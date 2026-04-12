import pyautogui
import time
class PCActions:
  def __init__(self, failsafe=True):
    pyautogui.FAILSAFE = failsafe

  def click(self, position_x, position_y, button='left'):
    pyautogui.click(button=button, x=position_x, y=position_y)

  def vscroll(self, scroll_amount, position_x, position_y):
    pyautogui.scroll(clicks=scroll_amount, x=position_x, y=position_y)

  def hscroll(self, scroll_amount, position_x, position_y):
    pyautogui.hscroll(clicks=scroll_amount, x=position_x, y=position_y)

  def type_text(self, text, position_x, position_y, interval=0.1):
    if position_x != None or position_y != None:
      self.click(button='left', position_x=position_x, position_y=position_y)

    time.sleep(interval * 5)
    pyautogui.write(text, interval=interval)

  def press_key(self, key):
    pyautogui.press(keys=key)

  def press_hotkey(self, hotkey):
    pyautogui.hotkey(*hotkey)

  def dismiss_taskbar_thumbnail_overlay(self):
    print("DEBUG: Inside dismiss_taskbar function now!") # Add this
    print("[PERFORM PC ACTIONS INTERNAL FUNCTION] Hopefully dismissing the popup")
    x_position, y_position = pyautogui.position()
    click_x_position = x_position - 70
    click_y_position = y_position - 96

    self.click(position_x=click_x_position, position_y=click_y_position)

if __name__ == "__main__":
  pc = PCActions()
  time.sleep(5)
  pc.dismiss_taskbar_thumbnail_overlay()