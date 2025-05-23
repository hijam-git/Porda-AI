from ctypes import windll
def show_message(ms):
    
    user32 = windll.user32
    user32.MessageBeep(0x00000040)
    # Display a "Saved Done" notification as a system modal window with a check mark icon
    user32.MessageBoxW(0, ms, "Porda Ai Message", 0x40 | 0x1000)
def make_notification_sound():
    user32 = windll.user32
    user32.MessageBeep(0x00000040)
    
