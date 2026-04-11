import pygetwindow as gw
import platform
import os
import winapps
import pyautogui
import io
import base64
import pywinauto

class ContextProvider:
  installed_apps = []
  WINDOWS_VERSION = f"{platform.system()} {platform.release()} Build: {platform.version()}"
  screen_width, screen_height = pyautogui.size()

  def _get_elements_from_window(self, window):
    elements = []
    for el in window.descendants():
      try:
        element_bounding_box = el.rectangle()
        element_name = el.window_text().strip()
        ctrl_type = el.element_info.control_type

        if not element_name or element_bounding_box.width() == 0 or element_bounding_box.height() == 0:
          continue

        target_x = int(element_bounding_box.left + element_bounding_box.width() / 2)
        target_y = int(element_bounding_box.top + element_bounding_box.height() / 2)
        
        elements.append(
          f"{ctrl_type} | name='{element_name}' | x={target_x} y={target_y}"
        )
      except:
          continue
        
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
  
  def get_screenshot(self):
    screenshot = pyautogui.screenshot()
    buffer = io.BytesIO()
    screenshot.save(buffer, format="JPEG", quality=70)
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return img_base64
  
  def get_taskbar_elements(self):
    try:
      app = pywinauto.Application(backend="uia").connect(title="Taskbar", timeout=3)
      elements = self._get_elements_from_window(app.top_window())
      return "\n".join(elements) if elements else "No taskbar elements found."
    except Exception as e:
      return f"Could not read taskbar: {str(e)}"

  def get_ui_tree(self, window_title: str):
    try:
      app = pywinauto.Application(backend="uia").connect(title_re=f".*{window_title}.*", timeout=5)
      elements = self._get_elements_from_window(app.top_window())
      return "\n".join(elements) if elements else "No UI elements found."
    except Exception as e:
      return f"Could not read UI tree: {str(e)}"
    

if __name__ == "__main__":
   cp = ContextProvider()
   print(cp.get_ui_tree(cp.get_active_window()))