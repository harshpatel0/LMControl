import pywinauto
from pywinauto.application import Application  # Use this exclusivly for types only.

from interactions.direct_app_control.types import *
import time

from utils.logger import logger

from utils.globals import ALLOWED_CONTROL_TYPES, STRUCTURAL_TYPES


class DirectAppController:
    def __init__(self) -> None:
        self.application: Application | None = None
        self.connected_pid: int | None = None

    def _resolve_by_runtime_id(self, window, control_id: str):
        target = tuple(int(x) for x in control_id.split("-"))
        for element in window.descendants():
            if element.element_info.runtime_id == target:
                return element
        return None

    def _get_pattern(self, element, pattern_name: str):
        """Safely access a UIA pattern, handling wrappers that lack the property."""
        if element is None:
            return None
        try:
            pattern = getattr(element, pattern_name, None)
            if pattern is not None:
                return pattern
        except Exception:
            pass

        try:
            from pywinauto.controls.uiawrapper import UIAWrapper

            uia_wrapper = UIAWrapper(element.element_info)
            return getattr(uia_wrapper, pattern_name, None)
        except Exception:
            return None

    def _stringify_runtime_id(self, runtime_id: tuple) -> str:
        return "-".join(map(str, runtime_id))

    def connect(self, process_id: int) -> DirectAppConnectionResult:
        try:
            self.application = pywinauto.application.Application(backend="uia").connect(
                process=process_id
            )
            self.connected_pid = process_id

            controls = self.list_controls()
            return DirectAppConnectionResult(
                success=True,
                message="Connected",
                controls_text=str(controls) if controls.controls else "",
            )
        except pywinauto.application.ProcessNotFoundError:
            return DirectAppConnectionResult(
                success=False, message=f"Process with ID {process_id} was not found"
            )
        except Exception as e:
            return DirectAppConnectionResult(
                success=False,
                message=f"Could not connect to process ({process_id}), {e}",
            )

    def list_processes(self) -> DirectAppProcessList:
        windows = pywinauto.Desktop(backend="uia").windows()
        seen_pids = set()
        result = []

        for w in windows:
            try:
                pid = w.process_id()
                if pid in seen_pids:
                    continue

                title = w.window_text()
                class_name = w.element_info.class_name
                rect = w.rectangle()

                # 1. Skip completely invisible service/background hosts
                # EXCEPT for the known UWP app shell wrapper class.
                if not w.is_visible() and class_name != "ApplicationFrameWindow":
                    continue

                # 2. Filter out windows without dimensions (0x0 background triggers)
                if (
                    rect.width() <= 0 or rect.height() <= 0
                ) and class_name != "ApplicationFrameWindow":
                    continue

                # 3. Filter out system/background artifacts that have empty titles
                # (Standard UWP apps like Settings will be caught via ApplicationFrameWindow)
                if not title and class_name != "ApplicationFrameWindow":
                    continue

                # 4. Skip common background background host components that aren't real apps
                if class_name in ["Windows.UI.Core.CoreWindow", "InputIndicatorWindow"]:
                    continue

                seen_pids.add(pid)
                result.append(
                    Process(
                        pid=pid,
                        title=title if title else "Windows Settings / UWP App",
                        class_name=class_name,
                    )
                )
            except Exception:
                continue

        return DirectAppProcessList(processes=result)

    def list_controls(
        self, expand_dropdowns: bool = True
    ) -> DirectAppControlListResult:
        if not self.application:
            return DirectAppControlListResult(error="Not connected")

        try:
            window = self.application.top_window()
        except Exception as e:
            return DirectAppControlListResult(error=f"Could not get window: {e}")

        seen = set()
        controls = []

        for element in window.descendants():
            try:
                ctrl_type = element.element_info.control_type
                if ctrl_type not in ALLOWED_CONTROL_TYPES:
                    continue

                if ctrl_type in STRUCTURAL_TYPES:
                    continue

                rect = element.rectangle()
                if rect.width() == 0 or rect.height() == 0:
                    continue

                if not element.is_visible():
                    continue

                if expand_dropdowns:
                    expand = self._get_pattern(element, "iface_expand_collapse")
                    if expand:
                        try:
                            if expand.CurrentExpandCollapseState == 0:
                                expand.Expand()
                                time.sleep(0.05)
                        except Exception:
                            pass

                try:
                    name = element.window_text().strip()
                except:
                    name = ""

                value = None
                vp = self._get_pattern(element, "iface_value")
                if vp:
                    try:
                        value = (vp.CurrentValue or "").strip()
                    except Exception:
                        pass

                if not (name or value) and ctrl_type not in {"Edit", "Document"}:
                    continue

                runtime_id = self._stringify_runtime_id(element.element_info.runtime_id)
                if runtime_id in seen:
                    continue
                seen.add(runtime_id)

                controls.append(
                    ProcessControl(
                        control_id=runtime_id,
                        type=ctrl_type,
                        name=name,
                        value=value or "",
                        enabled=element.is_enabled(),
                    )
                )
            except Exception as e:
                logger.debug(f"Skipped element: {e}")
                continue

        return DirectAppControlListResult(controls=controls)

    def interact(
        self, control_id: str, value: str | None = None
    ) -> DirectAppInteractionResult:
        if not self.application:
            return DirectAppInteractionResult(
                success=False,
                message="Not connected to a window, connect to the window to interact with it",
            )

        window = self.application.top_window()
        element = self._resolve_by_runtime_id(window, control_id)

        if element is None:
            return DirectAppInteractionResult(
                success=False, message="Control not found"
            )

        # Check for standard Invoke (Buttons)
        invoke = self._get_pattern(element, "iface_invoke")
        if invoke:
            try:
                invoke.Invoke()
                return DirectAppInteractionResult(
                    success=True, method="invoke", message="Invoked control"
                )
            except Exception as e:
                return DirectAppInteractionResult(
                    success=False, message=f"Invoke failed: {e}"
                )

        # Check for Toggle (Checkboxes/Switches)
        toggle = self._get_pattern(element, "iface_toggle")
        if toggle:
            try:
                toggle.Toggle()
                return DirectAppInteractionResult(
                    success=True, method="toggle", message="Toggled control"
                )
            except Exception as e:
                return DirectAppInteractionResult(
                    success=False, message=f"Toggle failed: {e}"
                )

        # Check for SelectionItem (ListItems/Radio buttons)
        select = self._get_pattern(element, "iface_selection_item")
        if select:
            try:
                select.Select()
                return DirectAppInteractionResult(
                    success=True, method="select", message="Selected control"
                )
            except Exception as e:
                return DirectAppInteractionResult(
                    success=False, message=f"Selection failed: {e}"
                )

        # Handle ComboBoxes by expanding them, or setting value directly
        if element.element_info.control_type == "ComboBox":
            expand_pattern = self._get_pattern(element, "iface_expand_collapse")
            if expand_pattern:
                try:
                    expand_pattern.Expand()
                    return DirectAppInteractionResult(
                        success=True,
                        method="expand_collapse",
                        message="Expanded ComboBox. Please run list_controls to see the new dropdown items.",
                    )
                except Exception as e:
                    return DirectAppInteractionResult(
                        success=False, message=f"Expand failed: {e}"
                    )

            if value is not None:
                vp = self._get_pattern(element, "iface_value")
                if vp:
                    try:
                        vp.SetValue(value)
                        return DirectAppInteractionResult(
                            success=True,
                            method="value_pattern",
                            message=f"Set ComboBox value to '{value}'",
                        )
                    except Exception as e:
                        return DirectAppInteractionResult(
                            success=False, message=f"Value pattern set failed: {e}"
                        )

            return DirectAppInteractionResult(
                success=False,
                message="ComboBox found but has no Expand or Value pattern",
            )

        # Last resort: try ValuePattern for controls that don't support invoke/toggle/select
        if value is not None:
            vp = self._get_pattern(element, "iface_value")
            if vp:
                try:
                    vp.SetValue(value)
                    return DirectAppInteractionResult(
                        success=True,
                        method="value_pattern",
                        message=f"Set value to '{value}'",
                    )
                except Exception as e:
                    return DirectAppInteractionResult(
                        success=False, message=f"Value pattern set failed: {e}"
                    )

    def expand(self, control_id: str) -> DirectAppInteractionResult:
        if not self.application:
            return DirectAppInteractionResult(
                success=False, message="Not connected to a window."
            )

        window = self.application.top_window()
        element = self._resolve_by_runtime_id(window, control_id)

        if element is None:
            return DirectAppInteractionResult(
                success=False, message="Control not found"
            )

        expand_pattern = self._get_pattern(element, "iface_expand_collapse")
        if not expand_pattern:
            return DirectAppInteractionResult(
                success=False,
                message=f"Control {element.element_info.control_type} does not support expanding.",
            )
        try:
            expand_pattern.Expand()
            return DirectAppInteractionResult(
                success=True,
                message="Successfully expanded control. Run list_controls to see new children.",
            )
        except Exception as e:
            return DirectAppInteractionResult(
                success=False, message=f"Expand failed: {str(e)}"
            )

    def collapse(self, control_id: str) -> DirectAppInteractionResult:
        if not self.application:
            return DirectAppInteractionResult(
                success=False,
                message="Not connected to a window, connect to the window to interact with it",
            )
        element = self._resolve_by_runtime_id(self.application.top_window(), control_id)
        if element is None:
            return DirectAppInteractionResult(
                success=False, message="Control not found"
            )
        expand_pattern = self._get_pattern(element, "iface_expand_collapse")
        if not expand_pattern:
            return DirectAppInteractionResult(
                success=False, message="No expand/collapse pattern"
            )
        try:
            expand_pattern.Collapse()
            return DirectAppInteractionResult(
                success=True, message="Collapse", method="collapse"
            )
        except Exception as e:
            return DirectAppInteractionResult(
                success=False, message=f"Collapse failed: {e}"
            )

    def set_value(self, control_id: str, value: str) -> DirectAppInteractionResult:
        if not self.application:
            return DirectAppInteractionResult(
                success=False,
                message="Not connected to a window, connect to the window to interact with it",
            )
        element = self._resolve_by_runtime_id(self.application.top_window(), control_id)
        if element is None:
            return DirectAppInteractionResult(
                success=False, message="Control not found"
            )
        vp = self._get_pattern(element, "iface_value")
        if vp:
            try:
                vp.SetValue(value)
                return DirectAppInteractionResult(
                    success=True, message="Set value", method="value_pattern"
                )
            except Exception as e:
                return DirectAppInteractionResult(
                    success=False, message=f"Value pattern set failed: {e}"
                )
        legacy = self._get_pattern(element, "iface_legacy_iaccessible")
        if legacy:
            try:
                legacy.SetValue(value)
                return DirectAppInteractionResult(
                    success=True, message="Set value", method="legacy"
                )
            except Exception as e:
                return DirectAppInteractionResult(
                    success=False, message=f"Legacy set failed: {e}"
                )
        return DirectAppInteractionResult(
            success=False, message="No non-focus-stealing pattern available"
        )

    def scroll(
        self,
        control_id: str,
        amount: Literal["line", "page"],
        direction: Literal["up", "down", "left", "right"],
    ) -> DirectAppInteractionResult:
        if not self.application:
            return DirectAppInteractionResult(
                success=False,
                message="Not connected to a window, connect to the window to interact with it",
            )

        window = self.application.top_window()
        element = self._resolve_by_runtime_id(window, control_id)
        if element is None:
            return DirectAppInteractionResult(
                success=False, message="Control not found"
            )
        scroll_fn = self._get_pattern(element, "scroll")
        if not scroll_fn:
            return DirectAppInteractionResult(
                success=False, message="Control does not support scroll"
            )
        try:
            scroll_fn(direction, amount)
            return DirectAppInteractionResult(
                success=True, message="Scrolled", method="scroll"
            )
        except Exception as e:
            return DirectAppInteractionResult(
                success=False, message=f"Scroll failed: {e}"
            )

    def set_range_value(
        self, control_id: str, value: float
    ) -> DirectAppInteractionResult:
        if not self.application:
            return DirectAppInteractionResult(
                success=False,
                message="Not connected to a window, connect to the window to interact with it",
            )

        element = self._resolve_by_runtime_id(self.application.top_window(), control_id)
        if element is None:
            return DirectAppInteractionResult(
                success=False, message="Control not found"
            )
        rv = self._get_pattern(element, "iface_range_value")
        if not rv:
            return DirectAppInteractionResult(
                success=False, message="No range value pattern"
            )
        try:
            rv.SetValue(value)
            return DirectAppInteractionResult(
                success=True, message="Value set", method="range_value"
            )
        except Exception as e:
            return DirectAppInteractionResult(
                success=False, message=f"Set range value failed: {e}"
            )

    def _execute_window_control(
        self,
        control_id: str,
        interaction: Literal["close", "maximize", "minimize", "restore"],
    ):
        if not self.application:
            return DirectAppInteractionResult(
                success=False,
                message="Not connected to a window, connect to the window to interact with it",
            )

        element = self._resolve_by_runtime_id(self.application.top_window(), control_id)

        if element is None:
            return DirectAppInteractionResult(
                success=False, message="Control not found"
            )

        method_name = {
            "close": "close",
            "maximize": "maximize",
            "minimize": "minimize",
            "restore": "restore",
        }.get(interaction)
        fn = self._get_pattern(element, method_name)
        if not fn:
            return DirectAppInteractionResult(
                success=False,
                message=f"Control does not support {interaction}",
            )
        try:
            fn()
            return DirectAppInteractionResult(
                success=True,
                message=f"{interaction.title()}d Window",
                method=interaction,
            )
        except Exception as e:
            return DirectAppInteractionResult(
                success=False, message=f"{interaction.title()} failed: {e}"
            )

    def minimize_window(self, control_id: str) -> DirectAppInteractionResult:
        return self._execute_window_control(control_id, "minimize")

    def maximize_window(self, control_id: str) -> DirectAppInteractionResult:
        return self._execute_window_control(control_id, "maximize")

    def restore_window(self, control_id: str) -> DirectAppInteractionResult:
        return self._execute_window_control(control_id, "restore")

    def close_window(self, control_id: str) -> DirectAppInteractionResult:
        return self._execute_window_control(control_id=control_id, interaction="close")

    def get_grid_item(
        self, control_id: str, row: int, col: int
    ) -> DirectAppInteractionResult:
        if not self.application:
            return DirectAppInteractionResult(
                success=False,
                message="Not connected to a window, connect to the window to interact with it",
            )

        window = self.application.top_window()
        element = self._resolve_by_runtime_id(window, control_id)
        if element is None:
            return DirectAppInteractionResult(
                success=False, message="Control not found"
            )
        gp = self._get_pattern(element, "iface_grid")
        if not gp:
            return DirectAppInteractionResult(
                success=False, message="No grid pattern available"
            )
        try:
            item = gp.GetItem(row, col)
            return DirectAppInteractionResult(
                success=True,
                message=f"Item at ({row},{col}) is {item}",
                method="grid_pattern",
            )
        except Exception as e:
            return DirectAppInteractionResult(
                success=False, message=f"Get grid item failed: {e}"
            )
