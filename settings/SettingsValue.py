"""
SettingsValue.py - Settings Management and Configuration Module

This module handles the loading, saving, and management of application settings
for the Porda AI application. It provides default settings, configuration options,
and utility functions for managing user preferences and application behavior.

@author Abdullah
@version 1.0
@since 2024
"""

import json
import os
from SetupPordaApp import PordaAppDir
from . EngineSetting import get_engines
from datetime import datetime,date

default_settings = {
    "accuracy": 25,
    "network_width":17,
    "network_height":10,
    "active_timeout": 65,
    "sleep_timeout": 500,
    "keep_running_timeout": 10,
    "engine":"CPU Engine",
    "hardware_accelerated":True,
    "is_priority_realtime":False,
    

    "cover":"Bg Color",
    "is_blur":True,
    "is_bg_color":False,
    "is_color":False,
    "rgb_color_value":"(0,0,255)",
    
    "object":"Female",
    "is_detect_male":False,
    "is_detect_female":True,
    "cover_index":0,
    "blur_kernel":140,
    "obj_list":[1],
    "activity_status":True,
    "auto_startup":True,
    "startup_lagacy":True,
    "shortcut_key":"f2",
    "capture_screenshot":"f1",
    "dataset_path":os.path.join(PordaAppDir(), "PordaAi","Dataset"),
    "initial_request_sent":False,
    "user_session":"",
    
    "is_all_window":False,
    "is_include_window":True,
    "is_exclude_window":False,
    "include_windows":"chrome.exe, msedge.exe, brave.exe, firefox.exe, opera.exe, PotPlayerMini64.exe, vlc.exe,",
    "exclude_windows":"explorer.exe, cmd.exe, winword.exe, pordaai.exe",
    "always_skip_windows":[("explorer.exe","Progman"),
                              ("explorer.exe","WorkerW"),
                              ("explorer.exe","Shell_TrayWnd"),
                              ("explorer.exe","LauncherTipWnd"),
                              ("explorer.exe","SystemTray_Main"),
                              ("explorer.exe","NotifyIconOverflowWindow"),
                              ("ShellExperienceHost.exe","Shell_TrayWnd"),
                              ("ShellExperienceHost.exe","Windows.UI.Core.CoreWindow"),
                              ("SearchApp.exe","Windows.UI.Core.CoreWindow"),
                              ],

    "is_gpu_setup_properly":False,

    "is_allow_max_cpu_limit":False,
    "max_cpu_limit":90,
    "average_reading_interval":30,
    "last_message_shown": datetime.now().strftime("%Y-%m-%d"),
}

def cover_list():
    """
    Returns the list of available cover options for detected objects.
    
    @returns {list} List of cover option strings
    """
    values = ["Black", "White", "Bg Color","Blur","Mosaic"]
    return values

def object_list():
    """
    Returns the list of available object detection options.
    
    @returns {list} List of object detection option strings
    """
    values = ["Male", "Female","Female without Hijab","Female without Borka","Only NSFW","All Human",]
    return values

def engine_list():
    """
    Returns the list of available detection engines.
    
    @returns {list} List of available engine names
    """
    #"Dedicated GPU","Integrated GPU",
    values = get_engines()#["CPU Engine","Hp Elitbook G3"] + get_gpu_list()
    return values

def get_gpu_list():
    """
    Retrieves the list of available GPU devices using OpenCL.
    
    This function attempts to detect available GPU devices that can be used
    for hardware acceleration of the detection process.
    
    @returns {list} List of GPU device names, or ["Got Error"] if detection fails
    @throws {Exception} When OpenCL is not available or GPU detection fails
    """
    li = []
    try:
        import pyopencl as cl
        platforms = cl.get_platforms()
        for i, platform in enumerate(platforms):
            devices = platform.get_devices()
            for j, device in enumerate(devices):
                li.append(device.name)
    except Exception as e:
        print("Got error when finding gpu",e)
        li=["Got Error"]
    return li

def load_settings():
    """
    Loads application settings from the settings file.
    
    This function attempts to load settings from the JSON file. If the file
    doesn't exist or is corrupted, it creates a new file with default settings.
    It also ensures all required settings keys are present by merging with defaults.
    
    @returns {dict} Dictionary containing the loaded settings
    @throws {FileNotFoundError} When settings file doesn't exist
    @throws {json.JSONDecodeError} When settings file is corrupted
    @throws {PermissionError} When file access is denied
    """
    #As I already created pordaAi folder, if i use base_path then the programme will look for pyinstaller temp folder
    porda_app_dir = PordaAppDir()

    settings_file_path = os.path.join(porda_app_dir,"pordaAi","settings.json")

    try:
        with open(settings_file_path, 'r') as f:
            settings = json.load(f)
            
            
    except (FileNotFoundError, json.JSONDecodeError):
        settings = default_settings
        save_settings(settings)  # Save the default settings if the file is missing or invalid
    except PermissionError as e:
        print(f"Permission Denied while loading settings: {e}")
        settings = default_settings
    except Exception as e:
        print(f"An error occurred while loading settings: {e}")
        settings = default_settings

    # Update settings with defaults for missing keys
    for key, value in default_settings.items():
        settings.setdefault(key, value)

    return settings

def save_settings(settings):
    """
    Saves application settings to the settings file.
    
    This function writes the current settings to a JSON file. If the operation
    fails due to permissions or other issues, it handles the error gracefully.
    
    @param {dict} settings - Dictionary containing the settings to save
    @throws {PermissionError} When file write access is denied
    @throws {Exception} When file write operation fails
    """
    porda_app_dir = PordaAppDir()
    try:
        settings_file_path = os.path.join(porda_app_dir,"pordaAi","settings.json")

        with open(settings_file_path, 'w') as f:
            json.dump(settings, f)
           

    except PermissionError as e:
        print(f"Permission Denied while saving settings: {e}")
        # Optionally, you can choose to use default settings or take other actions here
        # For example, you can set settings to default_settings
        settings = default_settings
    except Exception as e:
        print(f"An error occurred while saving settings: {e}")
