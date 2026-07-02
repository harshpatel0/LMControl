import pywinauto
from pywinauto.application import Application  # Use this exclusivly for types only.

from interactions.direct_app_control.types import *
import time

from utils.logger import logger

from utils.globals import ALLOWED_CONTROL_TYPES, STRUCTURAL_TYPES


class DirectAppController:
    def __init__(self) -> None:
        self.application: Application | None = None

    def _resolve_by_runtime_id(self, window, control_id: str):
        target = tuple(int(x) for x in control_id.split("-"))
        for element in window.descendants():
            if element.element_info.runtime_id == target:
                return element
        return None

    def _stringify_runtime_id(self, runtime_id: tuple) -> str:
        return "-".join(map(str, runtime_id))

    def connect(self, process_id: int) -> DirectAppConnectionResult:
        try:
            self.application = pywinauto.application.Application(backend="uia").connect(
                process=process_id
            )

            return DirectAppConnectionResult(success=True, message="Connected")
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
                if not w.is_visible():
                    continue
                pid = w.process_id()
                if pid in seen_pids:
                    continue
                seen_pids.add(pid)
                result.append(
                    Process(
                        pid=pid,
                        title=w.window_text(),
                        class_name=w.element_info.class_name,
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
                    try:
                        expand = element.iface_expand_collapse_pattern
                        if expand and expand.CurrentExpandCollapseState == 0:
                            expand.Expand()
                            time.sleep(0.05)
                    except:
                        pass

                try:
                    name = element.window_text().strip()
                except:
                    name = ""

                value = None
                try:
                    vp = element.iface_value_pattern
                    if vp:
                        value = (vp.CurrentValue or "").strip()
                except:
                    pass

                if not (name or value):
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

    def interact(self, control_id: str) -> DirectAppInteractionResult:
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
        try:
            inv = element.iface_invoke_pattern
            if inv:
                inv.Invoke()
                return DirectAppInteractionResult(
                    success=True, message="Invoked", method="invoke"
                )
        except Exception:
            pass
        try:
            tog = element.iface_toggle_pattern
            if tog:
                tog.Toggle()
                return DirectAppInteractionResult(
                    success=True, message="Toggled", method="toggle"
                )
        except Exception:
            pass
        try:
            sel = element.iface_selection_item_pattern
            if sel:
                sel.Select()
                return DirectAppInteractionResult(
                    success=True, message="Selected", method="select"
                )
        except Exception:
            pass
        return DirectAppInteractionResult(
            success=False, message="No supported pattern (invoke/toggle/select)"
        )

    def expand(self, control_id: str) -> DirectAppInteractionResult:
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
        try:
            exp = element.iface_expand_collapse_pattern
            if not exp:
                return DirectAppInteractionResult(
                    success=False, message="No expand/collapse pattern"
                )
            exp.Expand()
            return DirectAppInteractionResult(
                success=True, message="Expanded", method="expand"
            )
        except Exception as e:
            return DirectAppInteractionResult(
                success=False, message=f"Expand failed: {e}"
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
        try:
            exp = element.iface_expand_collapse_pattern
            if not exp:
                return DirectAppInteractionResult(
                    success=False, message="No expand/collapse pattern"
                )
            exp.Collapse()
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
        try:
            vp = element.iface_value_pattern
            if vp:
                vp.SetValue(value)
                return DirectAppInteractionResult(
                    success=True, message="Set value", method="value_pattern"
                )
        except Exception:
            pass
        try:
            legacy = element.iface_legacy_iaccessible_pattern
            if legacy:
                legacy.SetValue(value)
                return DirectAppInteractionResult(
                    success=True, message="Set value", method="legacy"
                )
        except Exception:
            pass
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
        try:
            element.scroll(direction, amount)
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
        try:
            rv = element.iface_range_value
            if not rv:
                return DirectAppInteractionResult(
                    success=False, message="No range value pattern"
                )
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
        try:
            if interaction == "close":
                element.close()
                return DirectAppInteractionResult(
                    success=True,
                    message=f"{interaction.title()}d Window",
                    method=interaction,
                )

            if interaction == "maximize":
                element.maximize()
                return DirectAppInteractionResult(
                    success=True,
                    message=f"{interaction.title()}d Window",
                    method=interaction,
                )

            if interaction == "minimize":
                element.minimize()
                return DirectAppInteractionResult(
                    success=True,
                    message=f"{interaction.title()}d Window",
                    method=interaction,
                )

            if interaction == "restore":
                element.restore()
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
        try:
            gp = element.iface_grid_pattern
            if not gp:
                return DirectAppInteractionResult(
                    success=False, message="No grid pattern available"
                )
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
