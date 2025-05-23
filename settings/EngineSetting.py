
import cv2
import time
import logging
from . import message
from PyQt5.QtCore import QSettings
from . import SettingsValue

def get_gpu_list():
    li = []
    try:
        import pyopencl as cl
        platforms = cl.get_platforms()

        for platform_idx, platform in enumerate(platforms):
            print(f"Platform {platform_idx}:", platform.get_info(cl.platform_info.NAME))
            print("  Vendor:", platform.get_info(cl.platform_info.VENDOR))
            devices = platform.get_devices()
            for device_idx, device in enumerate(devices):
                en= f"{platform_idx}:{platform.get_info(cl.platform_info.NAME)},\n{device_idx}:{device.get_info(cl.device_info.NAME)}" 
                li.append(en)

    except Exception as e:
        print(f"Got error when finding gpu: {e}")
        logging.error("Pordaai opencl error in your device")
    
    return li


def get_engines():
    val = ["CPU Engine"] + get_gpu_list()
    #val = ["CPU Engine","Hp Elitbook G3","Intregeted GPU"] + get_gpu_list()
    return val


def SetEngine(self,engine,network_width,network_height):
   
    engines = get_engines()
    self.engine_set_properly = False
    print("entering SetEngine Method")

    if engine == "CPU Engine":
        try:
            cv2.dnn.DNN_CLEAR_FORWARD = 1
            cv2.dnn.DNN_CLEAR_BACKWARD = 1
            self.model.setInputParams(size=(network_width,network_height), scale=1/255)
            
            self.engine_set_properly = True
            return True

        except:
            return False
               

    elif engine == "Integreted GPU":
        try:
            if cv2.ocl.haveOpenCL():
                if not settings["is_gpu_setup_properly"]:
                    message.show_message("Wait for first time GPU setup. It may take 10-40 seconds. Wait even if it no responding.")
                
                cv2.dnn.DNN_CLEAR_FORWARD = 1
                cv2.dnn.DNN_CLEAR_BACKWARD = 1
                cv2.ocl.setUseOpenCL(True)
                #self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
                self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL)
                
                self.model.setInputParams(size=(network_width,network_height), scale=1/255)
                self.engine_set_properly = True
                return True
                
            else:
                message.show_message("Getting Error, Please try CPU Engine.")
                self.engine_set_properly = False
                self.settings_window.engine_combobox.setCurrentIndex(engines.index("CPU Engine"))
                print("Can not getting your Built In GPU. Check CPU")
                
                return False

        except Exception as e:
            message.show_message("Getting Error, Please try CPU Engine.")
            self.engine_set_properly = False
            logging.error(f"Error occurred when setup oepncl: {str(e)}")
            self.settings_window.engine_combobox.setCurrentIndex(engines.index("CPU Engine"))
            print("Getting error when setting your integreged GPU.")
            return False
        

    else:
        print("===============================")
        print(engine.split(',\n'))
        platform = engine.split(',\n')[0]
        engine_device = engine.split(',\n')[1]

        if 'CUDA' in engine:
            message.show_message("This version don't support CUDA will be added cuda soon insaAllah!")
            return False
        
        if 'OpenCL' in platform:
            settings = SettingsValue.load_settings()
            v=settings["is_gpu_setup_properly"]
            print(f"settings[is_gpu_setup_properly]:{v}")
            
            if not settings["is_gpu_setup_properly"]:
                message.show_message("Wait for first time GPU setup. It may take 10-40 seconds. Wait even if it no responding.")
                
            selected_platform_index = int(platform[0])
            selected_device_index = int(engine_device[0])
            print(selected_platform_index)
            print(selected_device_index)
            try:
                
                set_opencl_device(selected_platform_index,selected_device_index)
                if cv2.ocl.haveOpenCL():
                    cv2.dnn.DNN_CLEAR_FORWARD = 1
                    cv2.dnn.DNN_CLEAR_BACKWARD = 1
                    cv2.ocl.setUseOpenCL(True)
                    #self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                    self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
                    self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL)
                    
                    self.model.setInputParams(size=(network_width,network_height), scale=1/255)
                
                    self.engine_set_properly = True
                    settings["is_gpu_setup_properly"] = True
                    SettingsValue.save_settings(settings)
                    print(f"====> img_size:{network_width,network_height} Engine: {engine}")

                    return True
                else:
                    self.engine_set_properly = False
                    self.settings_window.engine_combobox.setCurrentIndex(engines.index("CPU Engine"))
                    print("Can not getting your Built In GPU. Check CPU")
                    return False
                
            except Exception as e:
                self.engine_set_properly = False
                logging.error(f"Error occurred when setup oepncl: {str(e)}")
                self.settings_window.engine_combobox.setCurrentIndex(engines.index("CPU Engine"))
                print("Getting error when setting Built in GPU.")
                return False
        else:
            message.show_message(f"We only take OpenCL device.")

            self.engine_set_properly = False
            self.settings_window.engine_combobox.setCurrentIndex(engines.index("CPU Engine"))
            message.show_message(f"Not operate your {engine} in this version. Please check out next Update.")
            return False
    
def set_opencl_device(selected_platform_index,selected_device_index):
    try:
        print("entering set_opencl devidce function")
        import pyopencl as cl
        platforms = cl.get_platforms()

        # Get the selected platform and device
        selected_platform = platforms[selected_platform_index]
        selected_device = selected_platform.get_devices()[selected_device_index]

        # Create an OpenCL context with the selected device
        ctx = cl.Context([selected_device])

        # Now, you can use the 'ctx' object for OpenCL operations with the chosen device
        queue = cl.CommandQueue(ctx)
        print(queue)

    except Exception as e:
        print(f"Got error when setting opencl device: {e}")

#if there is not openl cl support then set here GpuPreference 1
#if there is cuda and opencl then set 1

def set_graphics_preference():
    import sys
    import winreg
    
    if True:#getattr(sys, 'frozen', False):
        value = "GpuPreference=1;"

        '''existing_value, _ = winreg.QueryValueEx(key, value_name)
        print(f"The value {existing_value} already exists at location {key_path}")'''
        
        # Specify the registry key path
        key_path = r"Software\Microsoft\DirectX\UserGpuPreferences"
        value_name = sys.executable #Here value name will be the app path and value will be gpu preference
        #value_name = "D:\Python-Zone\OpenCv\Porda Project\install\pordaapp\dist\PordaAi1.2_win10(alpha45).exe" #Here value name will be the app path and value will be gpu preference
        value_data = "GpuPreference=1;"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                existing_value, _ = winreg.QueryValueEx(key, value_name)
                winreg.CloseKey(key)
                if existing_value != value_data:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value_data)
                    print("Value set successfully.")
                    winreg.CloseKey(key)
                else:
                    print("Value already set in the registry.")

            except FileNotFoundError:
                print(f"The value with name '{value_name}' does not exist in the registry.")
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value_data)
                print("Value set successfully.")
                winreg.CloseKey(key)

        except FileNotFoundError:
            print("Key does not exist in the registry.")
        except Exception as e:
            print("An error occurred:", e)