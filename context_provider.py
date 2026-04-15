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

class ContextProvider:
  installed_apps = []
  WINDOWS_VERSION = f"{platform.system()} {platform.release()} Build: {platform.version()}"
  screen_width, screen_height = pyautogui.size()

  ALLOWED_CONTROL_TYPES = {
    "Button", "Edit", "ComboBox", "MenuItem", "MenuBar",
    "TabItem", "Hyperlink", "ListItem", "TreeItem", "CheckBox",
    "RadioButton", "Slider", "ToolBar", "SearchBox", "Text"
  }

  def _get_elements_from_window(self, window):
    last_count = 0
    stable_ticks = 0
    WAITING_PERIOD = settings.context_provider.waiting_period

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
        time.sleep(0.25)

    logger.info(f"UI Stabilized with {last_count} elements. Extracting data...")

    seen = set()
    elements = []
    
    try:
      win_rect = window.rectangle()
      bounds = (win_rect.left, win_rect.top, win_rect.right, win_rect.bottom)
    except:
      bounds = (0, 0, self.screen_width, self.screen_height)

    win_left, win_top, win_right, win_bottom = bounds

    # Single pass extraction
    for el in window.descendants():
      try:
        ctrl_type = el.element_info.control_type
        if ctrl_type not in self.ALLOWED_CONTROL_TYPES:
          continue

        # Check Rectangle (Fast)
        rect = el.rectangle()
        if rect.width() == 0 or rect.height() == 0:
          continue

        target_x = int(rect.left + rect.width() / 2)
        target_y = int(rect.top + rect.height() / 2)

        if not (win_left <= target_x <= win_right and win_top <= target_y <= win_bottom):
          continue

        # Check Text (SLOW - requires querying the other process)
        element_name = el.window_text().strip()
        if not element_name or len(element_name) > 100:
          continue

        if ctrl_type == "Text" and len(element_name) <= 1:
          continue

        key = (ctrl_type, element_name, target_x, target_y)
        if key not in seen:
          seen.add(key)
          elements.append(f"{ctrl_type} | name='{element_name}' | x={target_x} y={target_y}")
      except:
        continue

    logger.debug(f"Final scan found {len(elements)} elements.")
    return elements

  def get_active_window(self):
    active_window = gw.getActiveWindow()
    return active_window.title if active_window else "Desktop"

  def get_installed_apps(self):
    if not self.installed_apps:
      self.installed_apps = sorted(app.name for app in winapps.list_installed())
    
    return self.installed_apps

  def get_pinned_apps(self):
    path = os.path.expandvars(r'%AppData%\\Microsoft\\Internet Explorer\\Quick Launch\\User Pinned\\TaskBar')
    pinned_apps = [f.replace('.lnk', '') for f in os.listdir(path)]
    
    try:
      pinned_apps.remove('desktop.ini')
    except Exception:
      pass

    return pinned_apps
  
  def get_screenshot(self, window_title: str = None):
    """
    Captures only the active window region.
    Falls back to full screenshot if window bounds can't be determined.
    """
    try:
        if window_title is None:
          win = gw.getActiveWindow()
        else:
          wins = gw.getWindowsWithTitle(window_title)
          win = wins[0] if wins else gw.getActiveWindow()

        if win is None:
          raise ValueError("No window found")

        left   = max(win.left, 0)
        top    = max(win.top, 0)
        width  = win.width
        height = win.height

        if width <= 0 or height <= 0:
          raise ValueError("Window has zero size")

        screenshot = pyautogui.screenshot(region=(left, top, width, height))

    except Exception as e:
        logger.warning(f"[ContextProvider] Window screenshot failed ({e}), falling back to full screen.")
        screenshot = pyautogui.screenshot()

    buffer = io.BytesIO()
    screenshot.save(buffer, format="JPEG", quality=70)
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')
  
  def get_taskbar_elements(self):
    try:
      app = pywinauto.Application(backend="uia").connect(title="Taskbar", timeout=3)
      elements = self._get_elements_from_window(app.top_window())
      return "\n".join(elements) if elements else "No taskbar elements found."
    except Exception as e:
      return f"Could not read taskbar: {str(e)}"

  def get_ui_tree(self):
    try:
      hwnd = win32gui.GetForegroundWindow()
      desktop = pywinauto.Desktop(backend="uia")

      window = desktop.window(handle=hwnd)
      elements = self._get_elements_from_window(window)

      logger.debug(elements)
      return "\n".join(elements) if elements else "No UI elements found."
    except Exception as e:
      return f"Could not read UI tree: {str(e)}"
    

if __name__ == "__main__":
  import keyboard

  cp = ContextProvider()
  while True:
    if keyboard.is_pressed('k'):
      logger.info(cp.get_ui_tree(cp.get_active_window()))
    if keyboard.is_pressed('q'):
      quit()