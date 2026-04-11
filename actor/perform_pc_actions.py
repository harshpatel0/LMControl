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
        self.click(button='left', position_x=position_x, position_y=position_y)
        time.sleep(interval * 10)
        pyautogui.write(text, interval=interval)
 
    def press_key(self, key):
        pyautogui.press(keys=key)
 
    def press_hotkey(self, hotkey):
        pyautogui.hotkey(*hotkey)
 