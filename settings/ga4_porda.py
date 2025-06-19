"""
ga4_porda.py - Google Analytics 4 Tracking Module

This module handles user analytics and tracking for the Porda AI application
using Google Analytics 4. It collects user behavior data, system information,
and application usage statistics to help improve the application.

@author Abdullah
@version 1.0
@since 2024
"""

import requests
import uuid
import psutil
import logging
import threading
import winreg as reg
import time
import socket

from .SettingsValue import load_settings,save_settings

from dotenv import load_dotenv
import os
load_dotenv()

def is_connected():
    """
    Checks if the internet connection is available.
    
    This function attempts to connect to Google's DNS server to verify
    internet connectivity.
    
    @returns {bool} True if internet connection is available, False otherwise
    @throws {OSError} When connection attempt fails
    """
    try:
        # Connect to a reliable host (Google's DNS server) on port 53
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

MAX_RETRIES = 5
RETRY_DELAY = 5  # Delay in seconds between retries

# For main 
MEASUREMENT_ID = os.getenv("MEASUREMENT_ID")
API_SECRET = os.getenv("API_SECRET")
print("Measurement ID:", MEASUREMENT_ID)
print("API Secret:", API_SECRET)

def get_os_version():
    """
    Retrieves the Windows operating system version from the registry.
    
    This function reads the Windows registry to get the product name
    of the installed operating system.
    
    @returns {str} Operating system product name or "error" if failed
    @throws {Exception} When registry access fails
    """
    try:
        key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        product_name, _ = reg.QueryValueEx(key, "ProductName")
        reg.CloseKey(key)
        return product_name
    except Exception as e:
        return "error"

def get_or_create_uuid():
    """
    Generates or retrieves a unique user ID from the Windows registry.
    
    This function checks if a user UUID exists in the registry. If not,
    it creates a new one and stores it for future use.
    
    @returns {tuple} (user_uuid, status) where status is "got" or "created"
    @throws {FileNotFoundError} When registry key doesn't exist
    """
    registry_path = r"SOFTWARE\pordaai"
    uuid_key_name = "UserUUID"
    try:
        registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, registry_path, 0, reg.KEY_READ)
        user_uuid, _ = reg.QueryValueEx(registry_key, uuid_key_name)
        reg.CloseKey(registry_key)
        return user_uuid, "got"
    except FileNotFoundError:
        user_uuid = str(uuid.uuid4())
        registry_key = reg.CreateKey(reg.HKEY_CURRENT_USER, registry_path)
        reg.SetValueEx(registry_key, uuid_key_name, 0, reg.REG_SZ, user_uuid)
        reg.CloseKey(registry_key)
        return user_uuid, "created"
    
def get_or_created_client_uuid():
    """
    Generates or retrieves a client session ID from application settings.
    
    This function manages client session IDs for analytics tracking.
    It creates new sessions for first-time users or retrieves existing ones.
    
    @returns {tuple} (client_id, isNewSession) where isNewSession is boolean
    """
    settings = load_settings()
    clinet_id=""
    isNewSession=False
    if settings["initial_request_sent"]:
        clinet_id = settings["user_session"]
        isNewSession=False
        print("Getting old session")
        if not clinet_id:
            clinet_id = str(uuid.uuid4())
            isNewSession=True
            print("empty claint id")
            
    else:
        clinet_id = str(uuid.uuid4())
        isNewSession=True
        print("creating new cliinet id")
        settings["user_session"]=clinet_id
        save_settings(settings)
    return clinet_id,isNewSession
        
def get_system_type():
    """
    Determines if the system is a laptop or desktop based on battery presence.
    
    This function checks for the presence of a battery to determine
    the system type for analytics purposes.
    
    @returns {str} "Laptop" if battery is present, "Desktop" otherwise
    """
    if hasattr(psutil, "sensors_battery"):
        battery = psutil.sensors_battery()
        if battery is not None:
            return "Laptop"
    return "Desktop"

def get_geo_country():
    """
    Retrieves the user's country based on IP address geolocation.
    
    This function uses the ipinfo.io service to determine the user's
    geographical location based on their IP address.
    
    @returns {str} Country code or "Unknown" if detection fails
    @throws {requests.RequestException} When geolocation service is unavailable
    """
    try:
        response = requests.get("https://ipinfo.io")
        data = response.json()
        return data.get("country", "Unknown")
    except requests.RequestException as e:
        logging.error(f"Error fetching geolocation data: {e}")
        return "Unknown"

def send_event(user_id, client_id, events, isNewSession):
    """
    Sends analytics events to Google Analytics 4.
    
    This function sends user events to Google Analytics with retry logic
    for reliability. It handles both new sessions and existing sessions.
    
    @param {str} user_id - Unique user identifier
    @param {str} client_id - Client session identifier
    @param {list} events - List of events to send
    @param {bool} isNewSession - Whether this is a new user session
    @throws {requests.RequestException} When network requests fail
    """
    url = f'https://www.google-analytics.com/mp/collect?measurement_id={MEASUREMENT_ID}&api_secret={API_SECRET}'

    payload = {
        'client_id': client_id,
        'user_id': user_id,
        'events': events
    }

    headers = {
        'Content-Type': 'application/json',
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 204:
                print(f'Event sent successfully on attempt {attempt}!')
                
                if isNewSession:
                    settings = load_settings()
                    settings["initial_request_sent"]=True
                    save_settings(settings)
                
                break
            else:
                print(f'Error sending event on attempt {attempt}: {response.status_code}, {response.text}')
        except requests.RequestException as e:
            print(f'Request failed on attempt {attempt}: {e}')
        
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
        else:
            print('Max retries reached. Failed to send event.')

def track_user(is_auto_startup):
    """
    Tracks user activity and sends analytics data to Google Analytics.
    
    This function collects system information, user behavior data, and
    sends appropriate events based on whether it's a new user or existing session.
    
    @param {bool} is_auto_startup - Whether the app was started automatically
    """
    # Initialize user ID and client ID
    user_id, user_status = get_or_create_uuid()
    client_id,isNewSession = get_or_created_client_uuid()#str(uuid.uuid4())
    geo_country = get_geo_country()

    # Common parameters for events
    common_parameter = {
        "app_version": "PordaAi-1.3-(a92)",
        "os_version": get_os_version(),
        'device_type': get_system_type(),
        "ram": round(psutil.virtual_memory().total / (1024 ** 3)),
        "country": geo_country,
    }
    
    events = []
    if not isNewSession:
        print("App Running Sending")
        events.append({"name": "app_running", "params": common_parameter})
    else:
        print("App Initial starting Sending")
        if user_status == "created":
            events.append({"name": "first_time_user", "params": common_parameter})
        # Determine the startup method
       
        startup_method = "auto_startup" if is_auto_startup else "by_clicking"
        
        # Add the App Starts event
        app_start_event = {
            "name": "app_starts",
            "params": {**common_parameter, "method": startup_method}
        }
        events.append(app_start_event)
        # Send all events in a single payload

    send_event(user_id, client_id, events,isNewSession)
        
def send_tracking_request(is_auto_startup):
    """
    Initiates the tracking request with internet connectivity check.
    
    This function checks for internet connectivity and attempts to send
    tracking data multiple times if needed.
    
    @param {bool} is_auto_startup - Whether the app was started automatically
    """
    # Create a thread for tracking
    try:
        for i in range(5):
            if is_connected():
                print("ga4 === connected internet")
                track_user(is_auto_startup)
                break
            else:
                print("no internet connection")
                
            time.sleep(5)
    except Exception as e:
        pass
    
if __name__ == "__main__":
    if send_tracking_request():
        print("request is sending")
    else:
        print("no internet connection")
        
    for i in range(10):
        print(i)
        time.sleep(1)
