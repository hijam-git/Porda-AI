import sys
from PyQt5.QtCore import (Qt, QPoint, QTimer,QCoreApplication,QEvent, 
                          QObject, pyqtSignal,QStandardPaths,QThread)
from PyQt5.QtGui import QPainter,QPixmap,QImage
from PyQt5.QtWidgets import (QApplication, QWidget,QLabel,QVBoxLayout,
                             QMenu, QAction, QSystemTrayIcon, QVBoxLayout, QLabel, QWidget)
from PyQt5.QtGui import QKeySequence
import numpy as np
import cv2
import time
import logging
import os
from settings.Settings import SettingsWindow

import signal
import psutil
import keyboard
#My modules

from GetDataV2 import GetScreenData 
from SetupPordaApp import app_initial_setup, isAppOpend, check_validity,PordaAppDir,set_priority_in_registry
from settings.SettingsValue import load_settings,save_settings, cover_list, engine_list
#from startup_image import StartupImage
from settings.message import show_message,make_notification_sound
from settings.EngineSetting import SetEngine,set_graphics_preference
from settings.ga4_porda import send_tracking_request

import SetupPordaApp
from PyQt5.QtGui import QIcon
import pstats
import cProfile
import tracemalloc
import functools

import win32gui
import win32ui
import win32con
import win32api
import win32process
import random
import threading
#from annotation.labelImg import AnnotationWindow
#from porda.get_data import GetScreenData
#from porda.detect import Detector
import multiprocessing


class KeyBoardManager(QObject):

    F2Signal = pyqtSignal()
    
    F1Signal = pyqtSignal()
    
       
    settings = load_settings()
    def show_settings_shortcut(self):
        #keyboard.add_hotkey("F1", self.F1Signal.emit, suppress=True)
       
        try:
            keyboard.add_hotkey(self.settings["capture_screenshot"], self.F1Signal.emit, suppress=True)
        except Exception as e:
            keyboard.add_hotkey("F1", self.F1Signal.emit, suppress=True)
            logging.error(f"Error setting up 'capture_screenshot' hotkey: {e}")
            

    def disable_enable_shortcut(self):
        try:
            keyboard.add_hotkey(self.settings["shortcut_key"], self.F2Signal.emit, suppress=True)
            
        except Exception as e:
            keyboard.add_hotkey("F2", self.F2Signal.emit, suppress=True)
            logging.error(f"Getting error of shortcut hot key: {e}")
        
class CPUThread(QThread):
    cpu_usage_updated = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop_flag = False
        self.itr = 30 #Second
        self.l = 0
        self.cpu_usage_sum =0

    def run(self):
        while not self._stop_flag:
            self.cpu_usage_sum += psutil.cpu_percent(interval=1)
            self.l += 1
            if self.l == self.itr:
                self.l = 0
                avg_cpu_usage = self.cpu_usage_sum / self.itr
                self.cpu_usage_updated.emit(avg_cpu_usage)
                self.cpu_usage_sum = 0
            self.msleep(100)

    def stop(self):
        self._stop_flag = True
        self.wait()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        #self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |  Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
       
        #self.setWindowState(Qt.WindowFullScreen)
        screen_rect = QApplication.desktop().availableGeometry()
        
        #print(f"screen_rect{screen_rect}")
        self.setGeometry(screen_rect)
        self.setWindowFlags(self.windowFlags() | Qt.Tool)

        self.my_win_id = self.winId()
        #self.setParent(QWidget.find(hwnd_chrome))
     
    
 
        print("=====enter mainwindow class========")

        QCoreApplication.instance().installEventFilter(self)

        self.settings = load_settings() #loading porda ai settings
        self.current_settings = load_settings()
        self.current_settings["initial_request_sent"]=False
        save_settings(self.current_settings)
        
        

        
        #==================when developping===========

        if self.settings["is_allow_max_cpu_limit"]:
            self.enable_auto_stop_when_high_cpu = True
        else:
            self.enable_auto_stop_when_high_cpu = False


        #===============================================
        self.is_app_started_by_system = len(sys.argv) > 1 and sys.argv[1] == "--startup_by_windows"  #it was started during Windows startup.
        
        self.counting_for_sending=0
        tracking_thread = threading.Thread(target=send_tracking_request,args=(self.is_app_started_by_system,), daemon=True)
        tracking_thread.start()
        #send_tracking_request(True)
       
       
        self.first_sleep_when_auto_startup_by_windows = 5 #second
        CONFIG, WEIGHTS, self.internal_dir = app_initial_setup()
        self.app_extarnal_dir = PordaAppDir()


        #================================================================================
        val = check_validity()
       
        if isAppOpend():
            show_message("Porda Ai Already opened")
            self.triggerShutdown()
            sys.exit()
            
            
        '''if not val:
            print(val)
            self.triggerShutdown()
            sys.exit()'''

        # Other init variable
        print(QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation))


        self.is_taking_screenshot=0
        self.application_is_about_to_close = False
        #===================================================================================
        #net = cv2.dnn.readNet(CONFIG, WEIGHTS) #gave better than readNetFromDarknet 
        self.net = cv2.dnn.readNetFromDarknet(CONFIG, WEIGHTS)
        self.model = cv2.dnn_DetectionModel(self.net)

        #===============Checking Wheather windows open or not ==========================
        #self.net = cv2.dnn.readNetFromCaffe("model/deploy.prototxt", "model/res10_300x300_ssd_iter_140000.caffemodel")

        '''get_data_initial_attributes={
            "isSpecific_window_enable":self.isSpecific_window_enable,
            "is_to_detect_all_windows":False,
            "is_detect_included_windows":self.is_detect_included_windows,
            "included_window_list":self.included_window_list,
            "skip_win":self.skip_win,
            "is_to_detect_excluded_windows":False,
            "excluded_window_list": self.excluded_window_list,
            "isHardware_Accelaration_enable":self.isHardware_Accelaration_enable,
            "entire_window":self.entire_window,
            "isCustom_region_Enable":False,
            
            
        }
        '''
        
        #======== Initial Attributes ==============
        self.engine_set_properly = False
        self.ready_to_start_detection = False
        self.detection_timer_state = True
        self.status_button_state = self.settings["activity_status"]
        self.is_detect_specific_window = False
        self.specific_window_hwnd=0
        self.applied_active_timeout = 50
        self.cover_objects = []
        self.win_rects={}
        self.last_stored_interested_hwnd=0000
        self.last_object_found_time = 0
        self.isNow_Active_Mode = False
        self.isNow_Sleep_Mode = True
        self.last_making_win_topmost = time.time()
        self.timer_and_connect()
        self.apply_button_pressed = False
        self.update_settings(False)
        
        if not self.is_app_started_by_system:
            set_graphics_preference()
            if getattr(sys, 'frozen', False):
                if set_priority_in_registry(sys.executable,"00000003"): #making priority high
                    logging.error("Priority high set successfully")
                else:
                    logging.error("Getting error when seting priority high may be permission denied")

        if self.is_app_started_by_system: #Set Engine and start detection
            result = self.setup_engine()
            if result:
                if self.current_settings["activity_status"]: #If Activaty staus is true then start detecting
                    self.detection_timer.start(self.sleep_timeout)
                
            else:
                self.settings_window.show()
                show_message("Getting error when setting engine while startup")
                logging.error(f"Getting error when setting engine while startup: {result}")
        else:
            self.settings_window.show()
            
            
    def setup_engine(self):
        engine = self.current_settings["engine"]
        self.network_width=int(self.current_settings["network_width"])*32
        self.network_height=int(self.current_settings["network_height"])*32
        try:
            # self.ready_to_start_detection = False
            if SetEngine(self,engine,self.network_width,self.network_height):
                if not engine == "CPU Engine": # If cpu then it can be changed
                    self.settings_window.spinBoxForNetworkWidth.setEnabled(False)
                    self.settings_window.spinBoxForNetworkHeight.setEnabled(False)
                    self.settings_window.engine_combobox.setEnabled(False)
                    
                self.ready_to_start_detection = True #it ensure that all is ready for detection
                self.engine_set_properly = True
                return True
        except Exception as e:
            return e
            
            
    def update_settings(self,apply_button_clicked=False):
        
        self.apply_button_pressed = apply_button_clicked

        self.detection_accuracy = float(self.current_settings["accuracy"]/100)
        self.active_timeout = self.current_settings["active_timeout"]
        self.keep_active_time = self.current_settings["keep_running_timeout"] #in_seconds
        self.sleep_timeout = self.current_settings["sleep_timeout"]  # in ms
        self.is_to_detect_all_windows = self.current_settings["is_all_window"]
        self.is_detect_included_windows = self.current_settings["is_include_window"]
        self.included_window_list = self.current_settings["include_windows"]
        loaded_skip_win = self.current_settings["always_skip_windows"]
        self.skip_win = [tuple(item) for item in loaded_skip_win]

        
        self.is_blur = self.current_settings["is_blur"]
        self.is_bg_color = self.current_settings["is_bg_color"]
        self.is_color = self.current_settings["is_color"]
        self.rgb_color_value = self.current_settings["rgb_color_value"]
        import ast
        self.rgb_color_value = ast.literal_eval(self.rgb_color_value)
    
        self.object_list = []
        if self.current_settings["is_detect_male"]:
            self.object_list.append(0)
        if self.current_settings["is_detect_female"]:
            self.object_list.append(1)
            
        print(self.object_list)
            
        # self.current_settings["is_detect_female"]
        
        # obj = self.current_settings["object"] 
        # if obj == "All Human":
        #     self.object_list=[0,1]
        # elif obj == "Male":
        #     self.object_list=[0]
        # elif obj == "Female":
        #     self.object_list=[1]
        # else:
        #     self.object_list=[1]
            
        if (not self.engine_set_properly and apply_button_clicked ) or self.is_app_started_by_system:
            self.setup_engine()
            
        if apply_button_clicked:
            self.is_get_app_name_included_windows = self.current_settings["is_showing_included_app"]
            self.is_detect_specific_window = self.current_settings["is_detect_specific_window"]
            
        if apply_button_clicked and self.ready_to_start_detection and self.status_button_state and self.applied_active_timeout != self.active_timeout :
            
            self.set_detection_interval(self.active_timeout)
            self.isNow_Active_Mode = True
            self.isNow_Sleep_Mode = False
            self.last_object_found_time = time.time()
            self.applied_active_timeout = self.active_timeout
        
    def timer_and_connect(self):
        manager = KeyBoardManager(self)
        manager.F1Signal.connect(self.capture_screenshot)
        manager.show_settings_shortcut()

        manager2 = KeyBoardManager(self)
        manager2.F2Signal.connect(self.enable_disable_by_shortcut_key)
        manager2.disable_enable_shortcut()
        self.last_status_changed_shortcut_key_press = time.time()
        self.last_status_changed_shortcut_key_press_f1 = time.time()

        if self.enable_auto_stop_when_high_cpu:
            self.cpu_thread = CPUThread(parent=self)
            self.cpu_thread.cpu_usage_updated.connect(self.handle_cpu_usage_updated)
            self.cpu_thread.start()


        self.settings_window = SettingsWindow(parent=self)
        # self.settings_window.accepted.connect()

        self.detection_timer = QTimer(self)
        self.detection_timer.timeout.connect(self.UpdateCover)
        
        self.make_window_topmost_timer = QTimer(self)
        self.make_window_topmost_timer.timeout.connect(self.make_window_topmost)
        # self.make_window_topmost_timer.start(1000)

    def refresh_hotkey(self): #if hot key regestration is faild 
        print("refreshing Hot key")
        try:
            print("removing hot key")
            keyboard.remove_all_hotkeys()
            keyboard.clear_all_hotkeys()
        except Exception as e:
            print("no hot key found so adding hot key:",e)
       
        manager = KeyBoardManager(self)
        manager.F1Signal.connect(self.capture_screenshot)
        manager.show_settings_shortcut()

        manager2 = KeyBoardManager(self)
        manager2.F2Signal.connect(self.enable_disable_by_shortcut_key)
        manager2.disable_enable_shortcut()


    def eventFilter(self, obj, event):
        if event.type() == QEvent.WindowStateChange:
            # Check if the window is minimized, which may indicate sleep or hibernate
            if self.windowState() & Qt.WindowMinimized:
                print("PC Power State: Going to sleep")
                # Call your function here when the computer is going to sleep
                self.myFunction()
            else:
                print("PC Power State: Active")

        return super().eventFilter(obj, event)

    def myFunction(self):
        print("power called")

    def make_window_topmost(self):
        print("Making TOp")
        win32gui.SetWindowPos(int(self.winId()), win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

    def capture_screenshot(self):

        if (time.time() - self.last_status_changed_shortcut_key_press_f1) < 0.1: #second
            self.last_status_changed_shortcut_key_press_f1 = time.time()
            #self.make_window_topmost()
             
        else:
            self.last_status_changed_shortcut_key_press_f1 = time.time()
            print("initializing capturing screenshot")
            
            self.hide()  # Hide the window
            
            try:
                hdesktop = win32gui.GetDesktopWindow()

                # Get the size of the screen
                width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
                height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
                left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
                top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

                # Get the handle of the taskbar
                '''
                hTaskBar = win32gui.FindWindow("Shell_TrayWnd", None)
                rect = win32gui.GetWindowRect(hTaskBar)
                taskbar_height = rect[3] - rect[1]

                # Exclude taskbar from height
                height -= taskbar_height'''

                # Create a device context
                desktop_dc = win32gui.GetWindowDC(hdesktop)
                img_dc = win32ui.CreateDCFromHandle(desktop_dc)
                # Create a memory-based device context
                mem_dc = img_dc.CreateCompatibleDC()

                # Create a bitmap object
                screenshot = win32ui.CreateBitmap()
                screenshot.CreateCompatibleBitmap(img_dc, width, height)
                mem_dc.SelectObject(screenshot)

                # Copy the screen into our memory device context
                mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)

                # Convert the bitmap to a numpy array
                signed_ints_array = screenshot.GetBitmapBits(True)
                img = np.frombuffer(signed_ints_array, dtype='uint8')
                img.shape = (height, width, 4)

                # Free resources
                win32gui.DeleteObject(screenshot.GetHandle())
                mem_dc.DeleteDC()
                win32gui.ReleaseDC(hdesktop, desktop_dc)

                # Remove the alpha channel
                img = img[..., :3]

                #save_directory = os.path.join(self.app_extarnal_dir, "PordaAi","Dataset")
                save_directory = self.settings["dataset_path"]

                # Make sure the directory exists, if not, create it
                os.makedirs(save_directory, exist_ok=True)

                # Specify the filename for the screenshot
                filename = f"{str(time.time()).replace('.','')}.jpg"
                while os.path.exists(filename):
                    random_number = random.randint(1, 1000)
                    filename = f"{filename.split('.')[0]}{random_number}.jpg"

                # Save screenshot to the specified location
                cv2.imwrite(os.path.join(save_directory, filename), img)
                print("tkaing screen done")
                
                make_notification_sound()
                
                #file_path=os.path.join(save_directory, filename)
        
                #self.show_annotation_window(file_path)
                
            except Exception as e:
                print(f"Error while capturing Screenshot: {e}")
                logging.error(f"Error while capturing Screenshot: {e}")
            #self.detection_timer.start()
            self.show()


    def handle_cpu_usage_updated(self, cpu_usage):

        if cpu_usage > self.cpu_limit_threshold:  # Adjust the threshold as needed
            if self.detection_timer_state:
                print(f"As Current cpu usage {cpu_usage} is higher than {self.cpu_limit_threshold} to detection stop")
                self.detection_timer.stop()
                self.settings_window.activity_status_combobox.setCurrentIndex(1) #make disable

                self.settings_window.setWindowTitle(f"{self.settings_window.title} - is not Active")
                self.settings_window.status_button.setText("Activate")
                self.cover_objects = [] # This ensure that there is not rectangle in the screen
                self.update()
                self.detection_timer_state = False

        else:
            print(f"Current CPU Usage: {cpu_usage}%")
            if not self.detection_timer_state:
                if self.ready_to_start_detection: # Must have to check is timer ready for start
                    if self.status_button_state: # What user order, if he ordered stop, then dont start even when low cpu  
                        self.detection_timer.start()
                        self.isNow_Active_Mode = True
                        self.isNow_Sleep_Mode = False

                        self.settings_window.activity_status_combobox.setCurrentIndex(0)
                        self.settings_window.setWindowTitle(f"{self.settings_window.title} - is Active")
                        self.settings_window.status_button.setText("Deactivate")
                        
                        print("As Not CPU usages normal SO timer started")
                        self.detection_timer_state = True
            

  

    def UpdateCover(self):
        
        try:
            #t1=time.time()
            img,x,y,h,w,status = GetScreenData(self) #x y is position of window
            if status:
                self.draw_cover(img, x, y,h,w) # detect object and draw
                self.update()
                self.counting_for_sending+=1
            else:
                self.no_img_found()
                
            # if time.time()- self.last_making_win_topmost>1 and self.isNow_Active_Mode:
            #     self.last_making_win_topmost = time.time()
            #     self.make_window_topmost()
                
            #print((time.time()-t1)*1000)
            
            if self.counting_for_sending>15000:
                self.counting_for_sending=0
                try:
                    tracking_thread = threading.Thread(target=send_tracking_request,args=(self.is_app_started_by_system,), daemon=True)
                    tracking_thread.start()
                except Exception as e:
                    pass
                
                
        except Exception as e:
            print(e)
            self.no_img_found()
            logging.error(f"Error occurred when Detection : {str(e)}")


    #+==============================================================
    def no_img_found(self):
        if self.cover_objects:
            self.cover_objects=[]
            self.update()
        time_gone = time.time() - self.last_object_found_time
        if (time_gone > 1) and (not self.isNow_Sleep_Mode) : # if there is no required app then sleep with in 1 second
            print("sleep mode activate")
            self.set_detection_interval(self.sleep_timeout)
            self.isNow_Active_Mode = False
            self.isNow_Sleep_Mode = True

    def show_settings(self):
        print("show_settings")
        self.settings_window.show()

    def enable_disable_by_shortcut_key(self,is_clicked_settings_button=False):
        """Shorcut enable disable machanism"""
        
        self.status_button_state = self.settings_window.getStatus()
        print("Status change command by shortcut key")
        print(f"self.status_button_state:{self.status_button_state}")

        if not is_clicked_settings_button and (time.time() - self.last_status_changed_shortcut_key_press) < 0.1: #second
            self.last_status_changed_shortcut_key_press = time.time()
            print("frequently ")
            
        elif not is_clicked_settings_button and (time.time() - self.last_status_changed_shortcut_key_press) < 0.6: #second
            self.last_status_changed_shortcut_key_press = time.time()
            self.show_settings()
            
        else:
            self.last_status_changed_shortcut_key_press = time.time()
            if self.status_button_state:
                self.detection_timer.stop()
                self.detection_timer_state = False

                #self.settings_window.activity_status_combobox.setCurrentIndex(1) #make disable
                self.settings_window.status_button.setText("Activate")
                self.settings_window.button_text = "active"
                self.settings_window.setWindowTitle(f"{self.settings_window.title} - is not Active")
                
                print("Status Changing to timer stop")
                self.status_button_state = False
                self.cover_objects = [] # This ensure that there is not rectangle in the screen
                self.update() #This ensure cleaning all box
            else:
                if self.ready_to_start_detection: #It ensure that ready for detection
                    self.detection_timer.start()
                    self.isNow_Active_Mode = True
                    self.isNow_Sleep_Mode = False

                    self.status_button_state = True
                    self.detection_timer_state = True
                    #self.settings_window.activity_status_combobox.setCurrentIndex(0)
                    self.settings_window.status_button.setText("Deactivate")
                    self.settings_window.button_text = "deactive"
                    self.settings_window.setWindowTitle(f"{self.settings_window.title} - is Active")
        
                    print("Status Changing to timer start")
                    
    #=================================================================

    def set_detection_interval(self, interval):
        self.detection_timer.stop()
        self.detection_timer.setInterval(interval)
        self.detection_timer.start()


    def draw_cover(self,frame, screen_x, screen_y,h,w):

        cover_img = 0
        cover_objects = []
        #tp=time.time()
        padded_frame,x_ratio,y_ratio =self.add_padding(frame,h,w)
        #print(f"padding time {time.time()-tp}")
        
        classes, scores, boxes = self.model.detect(padded_frame, confThreshold = self.detection_accuracy, nmsThreshold=0.1)

        time_gone = time.time() - self.last_object_found_time
        
        #print(self.detection_timer.interval())

        #any(class_id in self.object_list for class_id in classes)

        #checking if there is any required object is founds
        # target_obj=[class_id for class_id in classes if class_id in self.object_list ]
      
        if set(classes) & set(self.object_list):
            self.last_object_found_time = time.time()
            
            #Here setting active timeout interval in qtimer not continiusly just for ones by using flag
            if (time_gone > self.keep_active_time) or (not self.isNow_Active_Mode):
                print("Active mode timeout active")
                if not self.apply_button_pressed: 
                    # When changing setting by clicking apply 
                    # button then making window top most cause problem
                    # so make sure when apply button is clicked then no need to make top most
                    self.make_window_topmost() #Trigger make topmost
                    self.apply_button_pressed = False
                    
                self.set_detection_interval(self.active_timeout)
                self.isNow_Active_Mode = True
                self.isNow_Sleep_Mode = False

        else:

            # if there is no object found then checking wheathe keep active time pass cause
            # it should not update sleep timeout untill a certain time continiusly detect
            # Afther certain time pass then it set sleep time out and flag helps not doing changing timeout interval continoiusly
            if (time_gone > self.keep_active_time) and (not self.isNow_Sleep_Mode) :
                print("sleep mode active")
                self.set_detection_interval(self.sleep_timeout)
                self.isNow_Active_Mode = False
                self.isNow_Sleep_Mode = True
        #------------------------------------------------------------------------------------
        #print(self.object_list)

        for class_id, box,score in zip(classes, boxes,scores):
            if class_id in self.object_list:

                x = int(box[0]*x_ratio)
                y = int(box[1]*y_ratio)
                w = int(box[2]*x_ratio)
                h = int(box[3]*y_ratio)
                
                if self.is_bg_color:
                    pixels = frame[y+20:y+80:3, x:x+50:3, ::-1].reshape(-1, 3)
                    unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
                    dominant_color = unique_colors[np.argmax(counts)]
                    cover_img=  np.full((h, w, 3), dominant_color, dtype=np.uint8)
                    
                elif self.is_color: 
                    cover_img=  np.full((h, w, 3), (self.rgb_color_value), dtype=np.uint8)
                    # cv2.putText(cover_img, str(score), (5, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                else :
                    image = frame[y:y+h, x:x+w]
                    image = image[:, :, [2, 1, 0]] # This make images real color
                    k=w//2#self.blur_kernel
                    cover_img = cv2.blur(image, (k,k))
                
                #cover_objects.append({"position": position, "w": w,"h":h,"color":color})
                #cover_objects.append({"position": position, "object_cover": cover_img})
                if self.win_rects:
                    box_x= x+screen_x
                    box_y= y+screen_y
                    box_w = w
                    box_h = h
                    box_rect = (box_x, box_y, box_x + box_w, box_y + box_h)
                    intersect = False
                    non_intersecting_parts = []

                    #print(self.win_rects)
                    for rect in self.win_rects.values():

                        win_x, win_y, win_bx, win_by = rect
                        win_w=win_bx-win_x-10 # a bit width reducing esure there is no gap
                        win_h=win_by-win_y-10

                        box_x,box_y,box_bx,box_by=box_rect

                        if win_x<box_x and win_y<box_y and box_bx<win_bx and box_by<win_by:
                            intersect = True
                            non_intersecting_parts = []
                            break
                        
                        if non_intersecting_parts:
                            for box in non_intersecting_parts:
                                '''x1,y1,w1,h1=box
                                # Calculating bottom-right coordinates for each box
                                x1_br = x1 + w1
                                y1_br = y1 + h1
                                x2_br = win_x + win_w
                                y2_br = win_y + win_h'''

                                x1_tl, y1_tl, box_w, box_h = box
                                x1_br = x1_tl + box_w
                                y1_br = y1_tl + box_h

                                x2_tl, y2_tl, x2_br, y2_br = rect

                                # Calculate overlap coordinates
                                overlap_x1 = max(x1_tl, x2_tl)
                                overlap_y1 = max(y1_tl, y2_tl)
                                overlap_x2 = min(x1_br, x2_br)
                                overlap_y2 = min(y1_br, y2_br)

                                # Calculate width and height of overlap
                                overlap_w = max(0, overlap_x2 - overlap_x1)
                                overlap_h = max(0, overlap_y2 - overlap_y1)

                                # Calculate area of overlap
                                overlap_area = overlap_w * overlap_h

                                
                                if overlap_area>10:
                                    print("remove")
                                    non_intersecting_parts=[]
                                    break
                                
                                '''box_rect=box
                                if not (box_rect[0]+box_rect[2] < win_x or box_rect[0] > win_x + win_w or box_rect[1]+box_rect[3] < win_y or box_rect[1] > win_y + win_h):
                                    non_intersecting_parts=[]
                                    break'''


                                #if (x1 < x2_br and x1_br >= win_x and y1 <= y2_br and y1_br >= win_y):
                                   
                             
                        else:
                            
                            
                            if not (box_rect[2] < win_x or box_rect[0] > win_x + win_w or box_rect[3] < win_y or box_rect[1] > win_y + win_h):
                                intersect = True
                                
                                # Calculate non-intersecting parts of the box
                                
                                # Top part
                                if box_y < win_y:
                                    non_intersecting_parts.append((box_x, box_y, box_w, min(win_y - box_y, box_h)))

                                # Bottom part
                                if box_y + box_h > win_y + win_h:
                                    # Calculate the non-intersecting part at the bottom
                                    non_intersecting_parts.append((box_x, max(box_y, win_y + win_h), box_w, box_y + box_h - win_y-win_h))

                                # Left part
                                if box_x < win_x:
                                    non_intersecting_parts.append((box_x, max(box_y, win_y), min(win_x - box_x, box_w)+10, (box_h - (win_y - box_y)) if box_y < win_y else (box_h - 0)))

                                # Right part
                                if box_x + box_w > win_x + win_w:
                                    non_intersecting_parts.append((win_x+win_w, max(box_y, win_y), max(box_x + box_w - win_x-win_w, 0), (box_h - (win_y - box_y)) if box_y < win_y else (box_h - 0)))

                    if intersect:
                        for part_x, part_y, part_w, part_h in non_intersecting_parts:
                            cover_img = np.full((part_h, part_w, 3), 0, dtype=np.uint8)
                            position = QPoint(part_x, part_y)
                            cover_objects.append((position, cover_img))

                            
                    if not intersect:
                        position = QPoint(x+screen_x, y+screen_y)
                        cover_objects.append((position,cover_img))
                    
                else:
                    position = QPoint(x+screen_x, y+screen_y)
                    cover_objects.append((position,cover_img))
                    
        self.cover_objects = cover_objects
       

    def add_padding(self,frame,h,w):
        #h, w = frame.shape[:2] # For faster get width height from getdata
        
        scale = min(self.network_height / h, self.network_width / w)
        new_w, new_h = int(w * scale), int(h * scale)
        # Calculate Button and right padding pixel
        bottom = self.network_height - new_h
        right = self.network_width - new_w
        
        if (bottom <55 and right==0) or (right <70 and bottom==0):
            return frame, 1,1
        
        #Resiged with network size aspect ratio
        resized_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        padded_frame = cv2.copyMakeBorder(resized_frame, 0, bottom, 0, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        
        x_ratio= w/new_w
        y_ratio= h/new_h
        return padded_frame, x_ratio,y_ratio
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        for position,object_cover in self.cover_objects:
            qimage = QImage(object_cover.data, object_cover.shape[1], object_cover.shape[0], object_cover.strides[0],QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            painter.drawPixmap(position, pixmap)


    def triggerShutdown(self):
        logging.error("Shutting Down")
        
        if self.enable_auto_stop_when_high_cpu:
            self.cpu_thread.stop()
            self.cpu_thread.wait()

        QCoreApplication.instance().quit()

    def closetheapp(self):
        #self.display_image_closing()
        if self.enable_auto_stop_when_high_cpu:
            self.cpu_thread.stop()
            self.cpu_thread.wait()
        #time.sleep(1)
        QApplication.quit()

import SetupPordaApp
class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self,main_window):
        super(SystemTrayIcon, self).__init__()

        base_path = SetupPordaApp.PordaInternalFileDir() # it should from the directory where main.py
        self.setIcon(QIcon(os.path.join(base_path, "static","pordaailogo.png")))

        self.setToolTip("Porda Ai - Developed by Abdullah")
        self.settings=main_window.settings_window

        self.menu = QMenu()
        self.settings_action = QAction("PordaAi Settings", self)
        self.settings_action.triggered.connect(self.settings.show)
        self.menu.addAction(self.settings_action)

        self.deactivate_action = QAction("Activate/Deactivate", self)
        self.deactivate_action.triggered.connect(main_window.enable_disable_by_shortcut_key)
        self.menu.addAction(self.deactivate_action)
        ''' self.settings_action = QAction("PordaAi Settings", self)
        self.settings_action.triggered.connect(self.settings.show)
        self.menu.addAction(self.settings_action)
        '''
        self.capture_screenshot = QAction("Make Dataset", self)
        self.capture_screenshot.triggered.connect(main_window.capture_screenshot)
        self.menu.addAction(self.capture_screenshot)

        self.refresh_hotkey_tray = QAction("Refresh HotKey", self)
        self.refresh_hotkey_tray.triggered.connect(main_window.refresh_hotkey)
        self.menu.addAction(self.refresh_hotkey_tray)

        self.refresh_cover_tray = QAction("Refresh Cover", self)
        self.refresh_cover_tray.triggered.connect(main_window.make_window_topmost)
        self.menu.addAction(self.refresh_cover_tray)
       
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(main_window.closetheapp)
        self.menu.addAction(self.exit_action)
        
        self.setContextMenu(self.menu)

        # Connect the activated signal to handle left-click events
        self.activated.connect(self.icon_activated)
        # Connect the messageClicked signal to handle tooltip change on hover
        #self.messageClicked.connect(self.change_tooltip)
        self.show()

    def icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            # Handle left-click event here
            self.settings.show()
           
    def change_tooltip(self):
        # Set a new tooltip when the messageClicked signal is emitted
        new_tooltip = "PordaAi - Currently Active"
        self.setToolTip(new_tooltip)

#======= to capture shutdown signal ===============
#We can check it by shut-down clicking button and not saving a text file,
#  then text file show worning for unsaved work and the pordaai will exit 
def sleep_handler(sig, frame):
    print("i sleep")
    sys.exit(0)

def signal_handler(sig, frame):
    sys.exit(0)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    #signal.signal(signal.SIGTERM, signal_handler)
    #signal.signal(signal.SIGINT, signal_handler)
    # Connect the aboutToQuit signal to a custom slot (function)
    mainwindow = MainWindow()
    app.aboutToQuit.connect(mainwindow.triggerShutdown)
    mainwindow.show()
    #mainwindow.showFullScreen()

    system_tray_icon = SystemTrayIcon(mainwindow)
    
    #profiler.print_stats()

   

   

    # Stop tracing memory allocations
    #tracemalloc.stop()
    sys.exit(app.exec_())



    

  