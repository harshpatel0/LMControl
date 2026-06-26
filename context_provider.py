import pygetwindow as gw
import platform
import os
import winapps
import pyautogui
import io
import base64
import pywinauto
import win32gui
from utils.logger import logger
import time
from settings.settings import settings
from utils.globals import (
    CONTEXT_PROVIDER_UI_DIFF_THRESHOLD_PERCENTAGE as THRESHOLD_PERCENTAGE,
    ALLOWED_CONTROL_TYPES,
    IS_RUNNING_WINDOWS,
)


def _get_active_provider() -> str:
    if settings.orchestrator.use_autonomy_mode:
        return getattr(settings.models.autonomy_actor, "provider", "ollama")
    return getattr(settings.models.actor, "provider", "ollama")


class ContextProvider:
    installed_apps = []
    WINDOWS_VERSION = (
        f"{platform.system()} {platform.release()} Build: {platform.version()}"
    )
    screen_width, screen_height = pyautogui.size()

    def __init__(self) -> None:
        pass

    def _get_elements_from_window(self, window):
        last_count = 0
        stable_ticks = 0
        skip_after_ticks = 0
        WAITING_PERIOD = settings.context_provider.waiting_period
        SKIP_TICKS = settings.context_provider.skip_after_ticks
        POLL_INTERVAL = 0.1

        # --- Stabilization phase ---
        while stable_ticks < WAITING_PERIOD:
            try:
                current_count = len(window.descendants())
            except:
                current_count = 0

            if current_count > 0 and current_count == last_count:
                stable_ticks += 1
            else:
                stable_ticks = 0
                last_count = current_count

            if stable_ticks < WAITING_PERIOD:
                skip_after_ticks += 1
                time.sleep(POLL_INTERVAL)

            if skip_after_ticks >= SKIP_TICKS:
                break

        logger.debug(f"UI Stabilized with {current_count} elements. Extracting data...")

        seen = set()
        elements = []

        # Window bounds
        try:
            win_rect = window.rectangle()
            bounds = (win_rect.left, win_rect.top, win_rect.right, win_rect.bottom)
        except:
            bounds = (0, 0, self.screen_width, self.screen_height)

        win_left, win_top, win_right, win_bottom = bounds

        for element in window.descendants():
            try:
                ctrl_type = element.element_info.control_type

                if ctrl_type not in ALLOWED_CONTROL_TYPES:
                    continue

                # --- Bounds check (fast reject) ---
                rect = element.rectangle()
                if rect.width() == 0 or rect.height() == 0:
                    continue

                target_x = int(rect.left + rect.width() / 2)
                target_y = int(rect.top + rect.height() / 2)

                if not (
                    win_left <= target_x <= win_right
                    and win_top <= target_y <= win_bottom
                ):
                    continue

                # --- Expand dropdowns (ComboBox) ---
                try:
                    expand = element.iface_expand_collapse_pattern
                    if expand and expand.CurrentExpandCollapseState == 0:  # Collapsed
                        expand.Expand()
                        time.sleep(0.05)
                except:
                    pass

                # --- Extract basic name ---
                try:
                    element_name = element.window_text().strip()
                except:
                    element_name = ""

                # --- Extract TextPattern ---
                text_content = None
                try:
                    text_pattern = element.iface_text_pattern
                    if text_pattern:
                        text_content = text_pattern.DocumentRange.GetText(-1)
                        if text_content:
                            text_content = text_content.strip()
                except:
                    pass

                # --- Extract ValuePattern ---
                value = None
                try:
                    value_pattern = element.iface_value_pattern
                    if value_pattern:
                        value = value_pattern.CurrentValue
                        if value:
                            value = value.strip()
                except:
                    pass

                # --- filtering ---
                if not (element_name or text_content or value):
                    continue

                # --- Deduplication key --- ---
                key = (ctrl_type, element_name, text_content, value, target_x, target_y)
                if key in seen:
                    continue

                seen.add(key)
                elements.append(
                    f"{ctrl_type} | name='{element_name}' | x={target_x} y={target_y}"
                )

            except Exception as e:
                logger.debug(f"Skipped element due to an exception: {e}")
                continue

        logger.debug(f"Final scan found {len(elements)} elements.")
        return elements

    def get_active_window(self) -> str:
        try:
            active_window = gw.getActiveWindow()
            return active_window.title if active_window else "Desktop"
        except Exception:
            return "Desktop"

    def get_screenshot(self, window_title: str | None = None):
        """
        Captures only the active window region.
        Falls back to full screenshot if window bounds can't be determined.
        """
        do_take_full_screen_screenshot = (
            settings.context_provider.take_full_screen_screenshot
        )

        if not do_take_full_screen_screenshot:
            try:
                if window_title is None:
                    win = gw.getActiveWindow()
                else:
                    wins = gw.getWindowsWithTitle(window_title)
                    win = wins[0] if wins else gw.getActiveWindow()

                if win is None:
                    raise ValueError("No window found")

                left = int(max(win.left, 0))
                top = int(max(win.top, 0))
                width = int(win.width)
                height = int(win.height)

                if width <= 0 or height <= 0:
                    raise ValueError("Window has zero size")

                screenshot = pyautogui.screenshot(region=(left, top, width, height))

            except Exception as e:
                logger.warning(
                    f"[ContextProvider] Window screenshot failed ({e}), falling back to full screen."
                )
                screenshot = pyautogui.screenshot()
        else:
            screenshot = pyautogui.screenshot()

        buffer = io.BytesIO()
        screenshot.save(
            buffer,
            format="JPEG",
            quality=int(settings.context_provider.screenshot_quality_percentage),
        )
        img_bytes = buffer.getvalue()
        return base64.b64encode(img_bytes).decode("utf-8")

    def get_taskbar_elements(self):
        try:
            app = pywinauto.Application(backend="uia").connect(
                title="Taskbar", timeout=3
            )
            elements = self._get_elements_from_window(app.top_window())
            return "\n".join(elements) if elements else "No taskbar elements found."
        except Exception as e:
            return f"Could not read taskbar: {str(e)}"

    def get_ui_tree(self) -> list:
        try:
            hwnd = win32gui.GetForegroundWindow()
            desktop = pywinauto.Desktop(backend="uia")

            window = desktop.window(handle=hwnd)
            elements = self._get_elements_from_window(window)

            logger.debug(elements)
            return elements
        except Exception as e:
            return []


class UITreeHandler:
    context_provider: ContextProvider

    def __init__(self):
        self.context_provider = ContextProvider()
        self.current_tree = self.context_provider.get_ui_tree()
        self.previous_tree = self.current_tree
        self.initial_load = True
        self._cache_tree = []
        self._cache_time = 0.0
        self._cache_ttl = 0.15
        self._last_active_window = self.context_provider.get_active_window()

    def _get_cached_or_fresh_tree(self):
        now = time.time()
        if now - self._cache_time < self._cache_ttl and self._cache_tree:
            return self._cache_tree
        self._cache_tree = self.context_provider.get_ui_tree()
        self._cache_time = now
        return self._cache_tree

    def _get_tree(self):
        """Gathers added or removed trees as differences, rather than spitting the whole tree out"""

        self.previous_tree = self.current_tree
        self.current_tree = self._get_cached_or_fresh_tree()

        added_items = set(self.current_tree) - set(self.previous_tree)
        removed_items = set(self.previous_tree) - set(self.current_tree)

        return (added_items, removed_items)

    def request_tree_diffs(self):
        if not settings.context_provider.provide_uia_tree:
            return "UIA Tree has been disabled"

        if not IS_RUNNING_WINDOWS:
            return "UIA Tree is only enabled for Windows PCs"

        active_window = self.context_provider.get_active_window()
        window_changed = active_window != self._last_active_window
        self._last_active_window = active_window

        # Always send the full tree when the active window changes
        if window_changed or self.initial_load:
            self.initial_load = False
            self._cache_tree = []
            self.current_tree = self.context_provider.get_ui_tree()
            self.previous_tree = list(self.current_tree)
            ui_tree_elements = self.current_tree
            return_message = (
                "Here is the full UI tree\n" + "\n".join(ui_tree_elements)
                if ui_tree_elements
                else "No UI elements found."
            )
            logger.debug(f"Returning full UI Tree (window changed)\n{return_message}")
            return return_message

        # Always send the full tree if the provider is not Ollama

        if _get_active_provider() != "ollama":
            self.current_tree = self.context_provider.get_ui_tree()
            logger.debug(
                "Diffed UI Trees are unsupported for the current provider, only Ollama supports diffed trees, the full tree is being sent"
            )
            return "Here is the full UI tree\n" + "\n".join(self.current_tree)

        added_items, removed_items = self._get_tree()

        items_in_current_tree = len(self.current_tree)
        items_in_previous_tree = len(self.previous_tree)

        difference_in_items_from_trees = abs(
            items_in_current_tree - items_in_previous_tree
        )
        threshold_of_item_changes = (THRESHOLD_PERCENTAGE / 100) * items_in_current_tree

        if difference_in_items_from_trees >= threshold_of_item_changes:
            ui_tree_elements = self.current_tree
            return_message = (
                "Here is the full UI tree\n" + "\n".join(ui_tree_elements)
                if ui_tree_elements
                else "No UI elements found."
            )
            logger.debug(f"Returning full UI Tree\n{return_message}")
            return return_message

        added_items_as_text = (
            "Here are the added UI tree Items\n"
            + "\n".join(f"[+] {item}" for item in added_items)
            if added_items
            else "No additions to UI Tree were made"
        )
        removed_items_as_text = (
            "Here are the removed UI tree items\n"
            + "\n".join(f"[-] {item}" for item in removed_items)
            if removed_items
            else "No removals to UI Tree were made"
        )

        ui_tree = added_items_as_text + "\n" + removed_items_as_text
        logger.debug(f"Returning UI Tree Diff\n{ui_tree}")
        return ui_tree

    def force_reload_ui_tree(self):
        self._cache_tree = []
        self.current_tree = self.context_provider.get_ui_tree()
        self.previous_tree = list(self.current_tree)
        ui_tree_elements = self.current_tree
        return (
            "Here is the full UI tree" + "\n".join(ui_tree_elements)
            if ui_tree_elements
            else "No UI elements found."
        )
