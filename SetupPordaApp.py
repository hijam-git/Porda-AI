import logging
import os
import sys
from datetime import datetime, timedelta,date
from settings.message  import show_message
import shutil
from settings.EngineSetting import set_graphics_preference
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

"""This file must be located in main directory"""

import ctypes
import os

# Define constants
HKEY_LOCAL_MACHINE = 0x80000002
KEY_SET_VALUE = 0x0002
REG_DWORD = 4
#"High": "00000003",
#"Above Normal": "00000006",
#"Normal": "00000002",

def set_priority_in_registry(exe_path, priority_hex):
    try:
        # Open the key for the specified application
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
        exe_name = os.path.basename(exe_path)
        subkey_path = os.path.join(key_path, exe_name)
        perf_subkey_path = os.path.join(subkey_path, "PerfOptions")

        # Create or open the subkey
        handle = ctypes.c_void_p()
        result = ctypes.windll.advapi32.RegCreateKeyExW(HKEY_LOCAL_MACHINE, perf_subkey_path, 0, None, 0, KEY_SET_VALUE, None, ctypes.byref(handle), None)
        if result != 0:
            raise OSError(f"Failed to create or open registry subkey. Error code: {result}")

        # Set the priority
        priority_value = ctypes.c_ulong(int(priority_hex, 16))
        result = ctypes.windll.advapi32.RegSetValueExW(handle, "CpuPriorityClass", 0, REG_DWORD, ctypes.byref(priority_value), ctypes.sizeof(priority_value))
        if result != 0:
            raise OSError(f"Failed to set registry value. Error code: {result}")

        print(f"Priority for {exe_name} set to {priority_hex} successfully.")
        return True

    except PermissionError as e:
        print("Got Permission Error, try open the app with addminstry permission")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if handle:
            ctypes.windll.advapi32.RegCloseKey(handle)

from settings import SettingsValue

FEEDBACK_MESSAGE = "Please Check The latest Version. Could You Please Give us a Feedback? Please Donate us 01823170383 (bkash/nagad/whatsapp). লেটেস্ট ভার্সন চেক করুন। অত্যান্ত ব্যয়বহুল এই প্রজেক্টটিকে এগিয়ে নিতে দয়া করে দান করুন"
FEEDBACK_URL = "https://forms.gle/yQk4yesWcuv65Ruw7"

DONATION_REMINDER = "Please Donate Us so that we can Improve it more, 01823170383 (bkash/nagad/whatsapp)"
def check_validity():
    now_time = date.today()
    settings = SettingsValue.load_settings()

    last_message_date_str = str(settings["last_message_shown"])
    print(last_message_date_str)

    # Manually split the string to extract the year, month, and day
    try:
        year, month, day = map(int, last_message_date_str.split('-'))
        last_message_date = date(year, month, day)
    except ValueError:
        # Handle cases where the date string is not properly formatted
        last_message_date = now_time  # Fallback or set to some default value

    # Calculate the difference in days
    days_since_last_message = (now_time - last_message_date).days

    if days_since_last_message > 15:
        show_message(FEEDBACK_MESSAGE)
        QDesktopServices.openUrl(QUrl(FEEDBACK_URL))

        # Update the last_message_shown date as a string
        settings["last_message_shown"] = now_time.strftime("%Y-%m-%d")
        SettingsValue.save_settings(settings)
        
        return False
    else:
        return True
    
import psutil
def isAppOpend():
    app_name = "PordaAi"
    app_count=0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # Check if the app name is in the process name
            #print(proc.info['name'].lower())
            if app_name.lower() in proc.info['name'].lower():
                app_count+=1
                print("count",app_count)
                if app_count>2:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

#==========================================================================================
def PordaAppDir():
    """It located exactly where the app (.exe) is located"""

    path = ""
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(os.path.abspath(__file__))

    return str(path)

def PordaInternalFileDir():
    """It locates the files which was integrated when executable in py installer, """
    
    dir_path = ""
    if getattr(sys, 'frozen', False):
        dir_path = sys._MEIPASS
    else:
        dir_path = os.path.dirname(os.path.abspath(__file__))
    
    return str(dir_path)

#============= ================ ========================= ====================== ================ =====

def app_initial_setup():
    try:
        app_dir = PordaAppDir()
        # creating dir for porda ai
        porda_app_dir_name = "PordaAi"
        os.makedirs(os.path.join(app_dir,porda_app_dir_name), exist_ok=True)
        os.makedirs(os.path.join(app_dir,porda_app_dir_name,"Extarnal-Model"), exist_ok=True)
        os.makedirs(os.path.join(app_dir,porda_app_dir_name,"Dataset"), exist_ok=True)
        settings_file = os.path.join(app_dir,porda_app_dir_name,"settings.json")
        
        if not os.path.exists(settings_file):
            print("settings not extst")
            QDesktopServices.openUrl(QUrl(FEEDBACK_URL))
            
        log_setup(app_dir,porda_app_dir_name)
        
        #  ===== copy the porda ai readme files ===================================
        # destination_file = os.path.join(app_dir,porda_app_dir_name,"ReadMe.pdf")
        # if not os.path.exists(destination_file):
        #     source_file = os.path.join(app_dir,"static","readme1.pdf")
        #     if os.path.exists(source_file):
        #         shutil.copy(source_file, destination_file)
        #     else:
        #         print("readme.pdf didn't found.")
        #=========================================================================

    except Exception as e:
        show_message(f"Getting error When Setup: {e}")
        logging.error(f"Getting Issuge when setup.")


    #set engine preference
    
    internal_dir = PordaInternalFileDir()


    extarnal_model = os.path.join(app_dir, porda_app_dir_name, "Extarnal-Model")

    #class_file_name = os.path.join(extarnal_model, "class-name")
    #with open(class_file_name, 'a') as file:
        #pass
    print(extarnal_model)

    all_files = os.listdir(extarnal_model)

    cfg_file_path=''
    weight_file_path=''


    # Check if there are any files in the directory
    if all_files and len(all_files) == 2:
        try:
            # Choose the first two files
            for file in all_files:
                print(file)
                if file.endswith(".cfg"):
                    cfg_file_path=os.path.join(extarnal_model,file)
                elif file.endswith(".weights"):
                    weight_file_path = os.path.join(extarnal_model,file)
                else:
                    print("model not found")

            if cfg_file_path and weight_file_path:
                CONFIG = cfg_file_path
                WEIGHTS = weight_file_path
                print("Model from Extarnal Dir")

            else:
                raise "Not found extarnal model files"
        except Exception as e:
            print(e)
    else:
        # No files found in the external model directory, use default internal model
        
        # CONFIG = os.path.join(internal_dir, "model", "porda-v3.cfg")
        # WEIGHTS = os.path.join(internal_dir, "model", "pordav3-10000.weights")
        CONFIG = os.path.join(internal_dir, "model", "pordav4x3.cfg")
        #WEIGHTS = os.path.join(internal_dir, "model", "v4x3-13500e-lr-0005.weights")
        #WEIGHTS = os.path.join(internal_dir, "model", "v4x3-14600e-889-lr-0005.weights")
        #WEIGHTS = os.path.join(internal_dir, "model", "16900-lr-001-895.weights") #better then 15700-lr-0005-906, 
        #WEIGHTS = os.path.join(internal_dir, "model", "20000-lr-0005.weights")
        #WEIGHTS = os.path.join(internal_dir, "model", "15700-lr-0005-906.weights") #less porformance then 19200
        WEIGHTS = os.path.join(internal_dir, "model", "porda-19200-lr-0005-909.weights")
        
        
        print("Model from Internal")
    #CONFIG = os.path.join(internal_dir, "model", "cfg_yolov4-tiny.cfg")
    #WEIGHTS = os.path.join(internal_dir,"model", "yolov4-tiny.weights")
    return CONFIG , WEIGHTS, internal_dir

def log_setup(app_dir, porda_app_dir_name):
    # Creating log folder if not exist
    log_folder_path = os.path.join(app_dir, porda_app_dir_name, "Error-log")
    os.makedirs(log_folder_path, exist_ok=True)

    # Create log file with the current date
    today_date = datetime.now().strftime("%Y-%m-%d")
    log_file_path = os.path.join(log_folder_path, f"Error_{today_date}.log")
  
  

    # Set up logging configuration
    logging.basicConfig(filename=log_file_path, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

    #delete_old_logs_based_on_date(log_folder_path, days_to_keep=7)

    delete_old_logs_based_on_file_count(log_folder_path, files_to_keep=7)

    # For printing unhandled errors
    def log_unhandled_exception(exc_type, exc_value, exc_traceback):
        # Specify the error messages to be excluded from logging
        excluded_error_messages = [
            
            "Error occurred when Detection : cannot reshape array of size 2 into shape (1,1,4)",
            "Error occurred when Detection : (1400, 'GetWindowRect', 'Invalid window handle.')"
        ]

        error_message = str(exc_value)

        if error_message not in excluded_error_messages:
            logging.error("Unhandled exception occurred:", exc_info=(exc_type, exc_value, exc_traceback))


    sys.excepthook = log_unhandled_exception


#This keep last 7  log files
def delete_old_logs_based_on_file_count(log_folder_path, files_to_keep):
    log_files = [f for f in os.listdir(log_folder_path) if f.startswith("Error_") and f.endswith(".log")]

    # Sort log files based on the date in the file name
    log_files.sort(key=lambda x: datetime.strptime(x.split("_")[1].split(".")[0], "%Y-%m-%d"), reverse=True)

    # Keep only the latest files_to_keep log files
    files_to_delete = log_files[files_to_keep:]

    for file_name in files_to_delete:
        file_path = os.path.join(log_folder_path, file_name)
        try:
            os.remove(file_path)
        except Exception as e:
            logging.error(f"Error while deleting old log file: {e}")

#This keeps last files based on date, Delete log files older than 7 days
def delete_old_logs_based_on_date(log_folder_path, days_to_keep):
    today_date = datetime.now()
    for file_name in os.listdir(log_folder_path):
        file_path = os.path.join(log_folder_path, file_name)
        if os.path.isfile(file_path):
            try:
                # Extract date from the file name
                date_str = file_name.split("_")[1].split(".")[0]
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                # Check if the file is older than the specified days_to_keep
                if (today_date - file_date) > timedelta(days=days_to_keep):
                    os.remove(file_path)
            except Exception as e:
                logging.error(f"Error while processing log file for deletion: {e}")
'''
# Truncate log file to keep the last 550 lines
if os.path.isfile(log_file_path):
    try:
        with open(log_file_path, 'r') as file:
            lines = file.readlines()
        
        lines = lines[-550:]
        
        with open(log_file_path, 'w') as file:
            file.writelines(lines)
    except Exception as e:
        logging.error(f"Error when opening log file: {e}")
    '''

    