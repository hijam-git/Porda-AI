"""
GetDataV2.py - Screen Capture and Window Management Module

This module provides functionality for capturing screen data from Windows applications,
managing window handles, and retrieving process information. It's designed to work
with the Porda AI application for intelligent screen monitoring and object detection.

@author Abdullah
@version 2.0
@since 2024
"""

import win32gui
import win32ui
import win32con
from ctypes import windll
import numpy as np
import win32process
import win32api
import psutil
import time

def get_process_name(hwnd):
    """
    Retrieves the process name from a window handle using win32api.
    
    @param {int} hwnd - Window handle to get process name for
    @returns {str|None} Process name if successful, None if failed
    @throws {Exception} When unable to access process information
    """
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
        executable_path = win32process.GetModuleFileNameEx(handle, 0)
        process_name = executable_path.split("\\")[-1]

        return process_name
    except:
        return None


def get_process_name2(hwnd):
    """
    Retrieves the process name from a window handle using psutil.
    
    @param {int} hwnd - Window handle to get process name for
    @returns {str|None} Process name if successful, None if failed
    @throws {psutil.NoSuchProcess} When process no longer exists
    """
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        process_name = psutil.Process(pid).name()
        return process_name
    except: #psutil.NoSuchProcess:
        return None


def get_hwnds_for_pid(pid):
    """
    Gets all window handles associated with a specific process ID.
    
    @param {int} pid - Process ID to find windows for
    @returns {list} List of window handles for the given process ID
    """
    def callback(hwnd, hwnds):
        #if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
        if found_pid == pid:
            hwnds.append(hwnd)
        return True
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds

def get_hwnd_by_process_name(process_name):
    """
    Finds window handles by process name.
    
    @param {str} process_name - Name of the process to find windows for
    @returns {list} List of window handles for the given process name
    """
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            hwnds = get_hwnds_for_pid(proc.pid)
            if hwnds:
                return hwnds  # Return the list of HWNDs
    return []  # Return an empty list if process not found

class FoundWindow(Exception):
    """
    Custom exception raised when a window is found during enumeration.
    
    @extends {Exception}
    """
    pass

def get_hwnds_for_pid_first_hwnd(pid):
    """
    Gets the first visible and enabled window handle for a specific process ID.
    
    @param {int} pid - Process ID to find window for
    @returns {list} List containing the first found window handle
    @throws {FoundWindow} When a suitable window is found (caught internally)
    """
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            if win32gui.GetParent(hwnd) == 0:
                if win32gui.GetWindowPlacement(hwnd)[1] in (1,3):
                    _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if found_pid == pid:
                        hwnds.append(hwnd)
                        raise FoundWindow #this breaks when one wincow is found
                    
        return True
    
    hwnds = []
    try:
        win32gui.EnumWindows(callback, hwnds)
    except FoundWindow:
        pass  # We caught the exception, so just continue
    return hwnds

def get_hwnd_by_process_name_first_hwnd(process_name):
    """
    Finds the first window handle for a given process name.
    
    @param {str} process_name - Name of the process to find window for
    @returns {list} List containing the first found window handle
    """
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            hwnds = get_hwnds_for_pid_first_hwnd(proc.pid)
            if hwnds:
                return hwnds  # Return the list of HWNDs
    return []  # Return an empty list if process not found


def GetScreenData(self):
    """
    Captures screen data from the currently active window or specified windows.
    
    This function handles window detection, screen capture, and returns image data
    along with window position and size information. It supports various detection
    modes including all windows, included windows only, and specific window detection.
    
    @param {object} self - Main window instance containing detection settings
    @returns {tuple} (image, x, y, height, width, status) where:
        - image: numpy array of captured screen data
        - x, y: window position coordinates
        - height, width: window dimensions
        - status: 1 for success, None for failure
    @throws {Exception} When window capture fails
    """
    not_empt=False
    
    try:
        # i can chekck untill it not error
        self.hwnd = win32gui.GetForegroundWindow()
        self.rect = win32gui.GetWindowRect(self.hwnd)
            
    except Exception as e:
        not_empt=True
        
        if win32gui.GetWindowPlacement(self.last_stored_interested_hwnd)[1] in (1,3): #checking if last detecting window is available
            self.hwnd=self.last_stored_interested_hwnd
            self.rect = win32gui.GetWindowRect(self.hwnd)
        '''print("==============================")
        print(e)'''

    if not self.is_to_detect_all_windows:

        process_name = get_process_name(self.hwnd)
        #print(process_name)
        
        if not process_name:
            process_name="noprocess"
        
        #print(f'win32process :{process_name}')

        if self.is_detect_included_windows:

            if not process_name in self.included_window_list:
                
                    #checking current working window is okey to store in neglected windows
                    if win32gui.IsWindowVisible(self.hwnd) and win32gui.IsWindowEnabled(self.hwnd) and (win32gui.GetWindowPlacement(self.hwnd)[1] in (1,3)):
                        
                        window_class = win32gui.GetClassName(self.hwnd)
                      
                        if not (process_name,window_class) in self.skip_win: #Only add those window which is needed to add, for example task bar is not need to add
                            self.win_rects[self.hwnd]=win32gui.GetWindowRect(self.hwnd)
                   

                    # This Ensure the self.win_rects contains no inappropriet wins
                    for hw in list(self.win_rects.keys()):
                        try: #try if window is closed, then i rais error so, then delete the stored hwnd
                            win_place=win32gui.GetWindowPlacement(hw)[1]
                            if  win_place== 3: # If any window is covering full screen then No need to detect
                                img = np.zeros((300, 300, 3), dtype=int)
                                return img,0,0,0,0,None
                            
                            elif not (win_place in (1,3)): # if minimisied, then delete the key hwnd
                                del self.win_rects[hw]
                        except:
                            del self.win_rects[hw]

                        
                    if win32gui.GetWindowPlacement(self.last_stored_interested_hwnd)[1] in (1,3): #checking if last detecting window is available
                        self.hwnd=self.last_stored_interested_hwnd
                        self.rect = win32gui.GetWindowRect(self.hwnd)

            else:
                if not not_empt:
                    self.win_rects={}
                #self.last_stored_interested_hwnd=self.hwnd

        
        elif self.is_get_app_name_included_windows:
            window_class = win32gui.GetClassName(self.hwnd)

            self.settings_window.app_name_label.setText(f"Active Window App: {process_name} - {window_class}")
            included_list = self.settings_window.get_included_windows()
            print(included_list)
            print("===included list")
            if process_name not in included_list:
                self.settings_window.include_window_input.setText(' , '.join(included_list)+','+str(process_name))
                
            img = np.zeros((300, 300, 3), dtype=int)
            return img,0,0,0,0,None

    #process_name2 = get_process_name2(self.hwnd)
    #print(f'psutil :{process_name2}')
    
    
    left, top, right, bottom = win32gui.GetClientRect(self.hwnd) # get claint area excluding navigation bar
    width = right - left
    height = bottom - top
    if width<650 or height<400:
        self.win_rects[self.hwnd]=win32gui.GetWindowRect(self.hwnd)
        self.hwnd=self.last_stored_interested_hwnd
        self.rect = win32gui.GetWindowRect(self.hwnd)
        left, top, right, bottom = win32gui.GetClientRect(self.hwnd) # get claint area excluding navigation bar
        width = right - left
        height = bottom - top
    else:
        self.last_stored_interested_hwnd=self.hwnd

    x, y, _, _ = self.rect

    hwndDC = win32gui.GetWindowDC(self.hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)# nice accurate
    saveDC.SelectObject(saveBitMap)
    windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 3)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((int(bmpinfo['bmHeight']), bmpinfo['bmWidth'], 4))[:, :, [0, 1, 2]]
        
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(self.hwnd, hwndDC)
    
    return img,x,y,height,width, 1
    #return img,0,0,1