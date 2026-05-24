"""
message.py - Message and Notification Module

This module provides functionality for displaying system messages and playing
notification sounds in the Porda AI application. It uses Windows API calls
to show message boxes and play system sounds.

@author Abdullah
@version 1.0
@since 2024
"""

from ctypes import windll

def show_message(ms):
    """
    Displays a message box with the specified text and plays a notification sound.
    
    This function shows a system modal message box with an information icon
    and plays a system notification sound to alert the user.
    
    @param {str} ms - Message text to display in the message box
    @returns {int} Return value from the MessageBoxW API call
    """
    user32 = windll.user32
    user32.MessageBeep(0x00000040)
    # Display a "Saved Done" notification as a system modal window with a check mark icon
    user32.MessageBoxW(0, ms, "Porda Ai Message", 0x40 | 0x1000)

def make_notification_sound():
    """
    Plays a system notification sound.
    
    This function plays the default system information sound to provide
    audio feedback to the user without displaying a message box.
    
    @returns {int} Return value from the MessageBeep API call
    """
    user32 = windll.user32
    user32.MessageBeep(0x00000040)
    
