from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from . import SettingsValue

import os
import sys
import SetupPordaApp
from . import message
from PyQt5.QtCore import QSettings

from . settingscss2 import css
from . doc import document
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QApplication,QTabWidget,QColorDialog,QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QSpinBox,
                             QDoubleSpinBox, QComboBox, QCheckBox, QRadioButton, QPushButton,
                             QSplitter, QStackedWidget, QWidget,QTextBrowser,QScrollArea,QLineEdit,QButtonGroup,QSizePolicy,QTextEdit)


from ctypes.wintypes import HDC, HWND, RECT

title = "PordaAi1.3(a92)"
class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        parent_window_handle=131970

        # Ensure window is fully initialized before setting parent
        #win32gui.SetParent(int(widget.winId()), 131970)
        
        self.title = title
    
        self.setWindowTitle(self.title)

        self.setMinimumSize(650, 650)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        

        

        base_path = SetupPordaApp.PordaInternalFileDir() # it should from the directory where main.py
        self.setWindowIcon(QIcon(os.path.join(base_path, "static","favicon.png")))
        screen_rect = QApplication.desktop().screenGeometry()
        window_width = screen_rect.width() // 3
        window_height = screen_rect.height() * 6 // 10
        self.resize(window_width, window_height)

        self.setWindowFlags(self.windowFlags() | Qt.Tool)

        self.setStyleSheet(css)

        self.settings = SettingsValue.load_settings()
        self.parent = parent
        self.current_settings = self.parent.current_settings
        

        # Create a splitter to divide the window into two columns
        splitter = QSplitter()

        # Left column for groups
        left_column = QGroupBox("")
        left_layout = QVBoxLayout()

        # Add your group buttons here
        self.group_buttons = [
            QPushButton("Basic"),
            QPushButton("Network Size"),
            QPushButton("Timeout"),
            QPushButton("Additional Options"),
            QPushButton("In/Ex App"),
            QPushButton("Tracking"),
            QPushButton("Scalling"),
            QPushButton("About/Report"),
        ]

        for btn in self.group_buttons:
            btn.clicked.connect(self.show_group_properties)
            left_layout.addWidget(btn)

        left_column.setLayout(left_layout)

        # Right column for group properties
        right_column = QGroupBox("")

        right_layout = QVBoxLayout()
        right_column.setStyleSheet("QGroupBox { background-color:rgb(235, 236, 245);  }")

        # Create a stacked widget to hold the group property widgets
        self.stacked_widget = QStackedWidget()

        # Add widgets for each group's properties
        self.stacked_widget.addWidget(self.create_object_and_cover_properties())
        self.stacked_widget.addWidget(self.create_accuracy_properties())
        self.stacked_widget.addWidget(self.create_timeout_properties())
        self.stacked_widget.addWidget(self.create_additional_options_properties())
        
        self.stacked_widget.addWidget(self.window_specefy())
        self.stacked_widget.addWidget(self.tracking_settings())
        self.stacked_widget.addWidget(self.scalling_settings())
        self.stacked_widget.addWidget(self.contact_layout())

        right_layout.addWidget(self.stacked_widget)

        right_column.setLayout(right_layout)

        # Add both columns to the splitter
        splitter.addWidget(left_column)
        splitter.addWidget(right_column)

        # Set the splitter as the main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
       
        # Create button group
        button_group = QGroupBox()
        buttons_layout = QVBoxLayout()

        # Create horizontal layout for the first four buttons
        first_four_buttons_layout = QHBoxLayout()
        
        apply_button = QPushButton("Apply")
        apply_button.setObjectName("apply_button")
        apply_button.clicked.connect(self.update_setting)

        self.ok_button = QPushButton("OK")
        self.ok_button.setObjectName("ok_button")
        self.ok_button.clicked.connect(self.on_ok_button_clicked)

        save_value_button = QPushButton("Save")
        save_value_button.setObjectName("save_value_button")
        save_value_button.clicked.connect(self.save_settings_value)

        self.default_value_button = QPushButton("Default")
        self.default_value_button.setObjectName("default_value_button")
        self.default_value_button.clicked.connect(self.default_settings_value)


        first_four_buttons_layout.addWidget(save_value_button)
        first_four_buttons_layout.addWidget(self.default_value_button)
        first_four_buttons_layout.addWidget(self.ok_button)
        first_four_buttons_layout.addWidget(apply_button)

        # Add the first four buttons layout to the buttons layout
        buttons_layout.addLayout(first_four_buttons_layout)

        # Create horizontal layout for the last two buttons
        last_two_buttons_layout = QHBoxLayout()

        close_button = QPushButton("Terminate")
        close_button.clicked.connect(self.close_app)
        close_button.setObjectName("close_button")
        close_button.setStyleSheet('''QPushButton { background-color: rgb(200, 0, 0);color: #ffffff;
                                         padding: 10px 24px;
                                            margin-left: 14px;
                                            font-size: 16px;
                                            font-weight: bold; }
                                   
                                   QPushButton:hover { background-color: rgb(255, 0, 0);color: #ffffff;
                                          }
                                   ''')

        self.status_button = QPushButton("Enable/Disable")
        self.detection_status = self.settings["activity_status"]
        if self.detection_status:
            self.status_button.setText("Deativate")
            self.button_text = "deactive" # if true then set current index enable
        else:
            self.status_button.setText("Activate")
            self.button_text = "active"

        self.status_button.clicked.connect(self.change_status)
        close_button.setObjectName("status_button")
        self.status_button.setObjectName("status_button")
        self.status_button.setStyleSheet('''QPushButton { background-color: blue;color: #ffffff;
                                         padding: 10px 24px;
                                            margin-right: 14px;
                                            font-size: 16px;
                                            font-weight: bold;}
                                         QPushButton:hover { background-color: #2C3E50;color: #ffffff;
                                         }
                                         
                                         ''')

        last_two_buttons_layout.addWidget(close_button)
        last_two_buttons_layout.addWidget(self.status_button)

        # Add the last two buttons layout to the buttons layout
        buttons_layout.addLayout(last_two_buttons_layout)

        # Set the buttons layout for the button group
        
        button_group.setLayout(buttons_layout)

        # Add the button group to the main layout
        button_group.setStyleSheet("QGroupBox { border: none; }")

        main_layout.addWidget(button_group)
        #main_layout.addWidget(QLabel('''By using the app you acknowledge agreeing to the <a href='https://itholy.xyz/porda-ai'>Documentation</a>.'''))

        self.setLayout(main_layout)
        self.getStatus() #This shows Status in settings window

    def onTimeout(self):
        rect = RECT()
        hwnd = 0
        hdc = self.GetDC(hwnd)
       
        DT_SINGLELINE = 0x00000020
        DT_NOCLIP = 0x00000100
        self.DrawText(hdc, self._text, -1, rect, DT_SINGLELINE | DT_NOCLIP) 
        
        self.ReleaseDC(hwnd, hdc)


    def show_group_properties(self):
        sender_button = self.sender()
        index = sender_button.text()

        # Map group names to their respective indices
        group_mapping = {
            "Basic": 0,
            "Network Size": 1,
            "Timeout": 2,
            "Additional Options": 3,
            "In/Ex App":4,
            "Tracking":5,
            "Scalling":6,
            "About": 7,
        }

        # Show the corresponding properties for the selected group
        self.stacked_widget.setCurrentIndex(group_mapping[index])

        # Set a style for the active button
        for btn in self.group_buttons:
            if btn == sender_button:
                btn.setStyleSheet("QPushButton { background-color: #007acc; color: #ffffff; }")
            else:
                btn.setStyleSheet("")

    def contact_layout(self):
        contact_widget = QWidget()
        main_layout = QVBoxLayout()

        # Create a QScrollArea to make the text_browser scrollable
        scroll_area = QScrollArea()

        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(document)

        # Set the text_browser as the widget inside the scroll area
        scroll_area.setWidget(text_browser)
        scroll_area.setWidgetResizable(True)  # Ensures that the scroll area adjusts to its contents


        main_layout.addWidget(scroll_area)
        contact_widget.setLayout(main_layout)
        main_layout.setAlignment(Qt.AlignTop)
        return contact_widget
    
    def tracking_settings(self):
        tracking_widget = QWidget()
        main_layout = QVBoxLayout()
        label = QLabel("On Next Update")

        main_layout.addWidget(label)  # Add the label to the main layout

        tracking_widget.setLayout(main_layout)
        main_layout.setAlignment(Qt.AlignTop)
        
        return tracking_widget

    def scalling_settings(self):
        scalling_widget = QWidget()
        main_layout = QVBoxLayout()

        layout_cpu_limit_checkbox = QVBoxLayout()
        self.allow_max_cpu_limit_checkbox = QCheckBox("Allow Maximum CPU Limit")
        self.allow_max_cpu_limit_checkbox.setChecked(self.settings["is_allow_max_cpu_limit"])

        layout_cpu_limit_checkbox.addWidget(self.allow_max_cpu_limit_checkbox)


        layout_cpu_limit = QHBoxLayout()
        label_for_max_cpu_limit = QLabel("Max CPU Limit (%):")
        spin_box_for_max_cpu_limit = QSpinBox()
        spin_box_for_max_cpu_limit.setRange(50, 100)
        spin_box_for_max_cpu_limit.setSingleStep(5)
        spin_box_for_max_cpu_limit.setValue(self.settings["max_cpu_limit"])
        self.spin_box_for_max_cpu_limit=spin_box_for_max_cpu_limit

        layout_cpu_limit.addWidget(label_for_max_cpu_limit)
        layout_cpu_limit.addWidget(spin_box_for_max_cpu_limit)

        layout_average_interval = QHBoxLayout()
        label_for_average_interval = QLabel("Average Reading Interval (s):")
        spin_box_for_average_interval = QSpinBox()
        spin_box_for_average_interval.setRange(10, 150)
        spin_box_for_average_interval.setSingleStep(5)
        spin_box_for_average_interval.setValue(self.settings["average_reading_interval"])
        self.spin_box_for_average_interval=spin_box_for_average_interval

        layout_average_interval.addWidget(label_for_average_interval)
        layout_average_interval.addWidget(spin_box_for_average_interval)


         # Add spacing between layouts
        spacing_layout = QVBoxLayout()
        
        spacing_layout.addLayout(layout_cpu_limit_checkbox)
        spacing_layout.addSpacing(10) 
        spacing_layout.addLayout(layout_cpu_limit)
        spacing_layout.addSpacing(10) 
        spacing_layout.addLayout(layout_average_interval)
        
        # Align the spacing_layout to the left
        
        main_layout.addLayout(spacing_layout)
        main_layout.setAlignment(Qt.AlignTop)
        scalling_widget.setLayout(main_layout)

        return scalling_widget


    def window_specefy(self):
        window_widget = QWidget()
        main_layout = QVBoxLayout()

        all_windows_checkbox = QRadioButton("All Windows")
        all_windows_checkbox.setChecked(self.settings["is_all_window"])

        include_windows_checkbox = QRadioButton("Only Include Below Windows")
        include_windows_checkbox.setChecked(self.settings["is_include_window"])
        include_window_input = QTextEdit(self.settings["include_windows"])
        include_window_input.setFixedHeight(200)  # Set a minimum height for the input box

        exclude_windows_checkbox = QRadioButton("Only Exclude Below Windows")
        exclude_windows_checkbox.setChecked(self.settings["is_exclude_window"])
        exclude_window_input = QTextEdit(self.settings["exclude_windows"])
        exclude_window_input.setFixedHeight(100)  # Set a minimum height for the input box

        self.checkbox_specific_window = QRadioButton("Specific Window - Default is your working window")
        self.checkbox_specific_window.setEnabled(False)
        self.specific_window_name=QLineEdit()#self.settings["specific_window_name"])


        self.get_app_specific_windows_checkbox = QRadioButton("Auto Add Specific App")
        self.get_app_excluded_windows_checkbox = QRadioButton("Auto Add Excluded App")
        self.get_app_included_windows_checkbox = QRadioButton("Include an App")
        self.app_name_label = QLabel("Active Window App: ")
        
        
        self.all_windows_checkbox = all_windows_checkbox
        self.include_windows_checkbox = include_windows_checkbox
        self.exclude_windows_checkbox = exclude_windows_checkbox
        self.include_window_input = include_window_input
        self.exclude_window_input = exclude_window_input


        self.checkbox_specific_app = QCheckBox("Specific App - Default is your working window")
        
        
        spacing_layout = QVBoxLayout()
        spacing_layout.addWidget(all_windows_checkbox)
        spacing_layout.addSpacing(10)
        spacing_layout.addWidget(include_windows_checkbox)
        spacing_layout.addWidget(include_window_input)
        spacing_layout.addSpacing(10)
        # spacing_layout.addWidget(exclude_windows_checkbox)
        # spacing_layout.addWidget(exclude_window_input)
        spacing_layout.addSpacing(10)
        #spacing_layout.addWidget( self.checkbox_specific_app)
     
        # spacing_layout.addWidget(self.get_app_excluded_windows_checkbox)
        spacing_layout.addWidget(self.get_app_included_windows_checkbox)
        spacing_layout.addSpacing(10)
        spacing_layout.addWidget(self.checkbox_specific_window)
        spacing_layout.addWidget(self.app_name_label)

        
        main_layout.addLayout(spacing_layout)
        main_layout.setAlignment(Qt.AlignTop)

        window_widget.setLayout(main_layout)

        return window_widget


    def showDialog(self):
        # Create the QColorDialog with 'self' as the parent
        color_dialog = QColorDialog(self)

        # Execute the dialog modally and check the result
        result = color_dialog.exec_()

        # If the dialog was accepted (user clicked OK)
        if result == QColorDialog.Accepted:
            color = color_dialog.selectedColor()
            if color.isValid():
                self.color = color
                self.rgb_color_value=f"({color.red()}, {color.green()}, {color.blue()})"
                rgb_color=f"rgb({color.red()}, {color.green()}, {color.blue()})"
                self.lbl.setStyleSheet(f'background-color: {rgb_color}; color:{rgb_color}; padding: 5px')
        else:
            # Handle the case when the dialog was canceled or closed
            print("Color dialog was canceled or closed")

    def create_object_and_cover_properties(self):
        object_and_cover_widget = QWidget()
        main_layout = QVBoxLayout()

        layout_cover = QHBoxLayout()
        label_for_cover = QLabel("Cover:")
        
        self.blur_checkbox = QRadioButton("Blur")
        self.blur_checkbox.setChecked(self.settings["is_blur"])
        self.bg_color_checkbox = QRadioButton("Bg Color")
        self.bg_color_checkbox.setChecked(self.settings["is_bg_color"])
        self.color_checkbox = QRadioButton("Color")
        
        
        layout_cover.addWidget(label_for_cover)
        layout_cover.addWidget(self.blur_checkbox)
        layout_cover.addWidget(self.bg_color_checkbox)
        layout_cover.addWidget(self.color_checkbox)
       
        
        
        layout_cover_color = QHBoxLayout()
        
        self.color_checkbox.setChecked(self.settings["is_color"])
        self.rgb_color_value=self.settings["rgb_color_value"]
        
        
        
        solid_color_button = QRadioButton("Bg Color")
        solid_color_button.setChecked(self.settings["is_all_window"])
        
        self.color = QColor(0, 0, 0)  # Default color is black

        self.btn = QPushButton('Pick Color', self)
        self.btn.clicked.connect(self.showDialog)

        self.lbl = QLabel('____', self)
        rgb_color=f"rgb{self.rgb_color_value}"
        self.lbl.setStyleSheet(f'background-color: {rgb_color}; color: {rgb_color}; padding: 5px')

        layout_cover_color.addWidget(self.btn)
        layout_cover_color.addWidget(self.lbl)
        

        layout_object = QHBoxLayout()
        self.male_checkbox = QCheckBox("Male")
        self.male_checkbox.setChecked(self.settings["is_detect_male"])
        self.female_checkbox = QCheckBox("Female")
        self.female_checkbox.setChecked(self.settings["is_detect_female"])
        self.nsfw_checkbox = QCheckBox("NSFW")
        self.nsfw_checkbox.setEnabled(False)
        
        
        
        label_for_cover = QLabel("Object:")
        self.object_combobox = QComboBox()
        self.object_list = SettingsValue.object_list()
        self.object_combobox.addItems(self.object_list)
        self.object_combobox.setCurrentIndex(self.object_list.index(self.settings["object"]))
        
        self.object_combobox.setToolTipDuration(5)

        layout_object.addWidget(label_for_cover)
        # layout_object.addWidget(self.object_combobox)
        layout_object.addWidget(self.male_checkbox)
        layout_object.addWidget(self.female_checkbox)
        layout_object.addWidget(self.nsfw_checkbox)
        


        """
        layout_blur_kernel = QHBoxLayout()
        label_for_blur_kernel = QLabel("Blur kernel:")
        self.spin_box_for_blur_kernel = QSpinBox()
        self.spin_box_for_blur_kernel.setRange(10, 300)
        self.spin_box_for_blur_kernel.setSingleStep(5)
        self.spin_box_for_blur_kernel.setValue(self.settings["blur_kernel"])
        

        layout_blur_kernel.addWidget(label_for_blur_kernel)
        layout_blur_kernel.addWidget(self.spin_box_for_blur_kernel)

        """
        layout_activity = QHBoxLayout()
        label_for_status = QLabel("Status:")
        self.activity_status_combobox = QComboBox()
        self.activity_status_list = ["Enable Activity","Disable Activity"]
        self.activity_status_combobox.addItems(self.activity_status_list)
        self.activity_status_combobox.setEnabled(False)

        if self.settings["activity_status"] == True:
            self.activity_status_combobox.setCurrentIndex(0) # if true then set current index enable
            
        else:
            self.activity_status_combobox.setCurrentIndex(1)

        layout_activity.addWidget(label_for_status)
        layout_activity.addWidget(self.activity_status_combobox)
        

       
        layout_accuracy = QHBoxLayout()
        label_for_accuracy = QLabel("Accuracy:")
        spin_box_for_accuracy = QSpinBox()
        spin_box_for_accuracy.setRange(1, 99)
        spin_box_for_accuracy.setSingleStep(1)
        spin_box_for_accuracy.setValue(int(self.settings["accuracy"]))
        
        self.spinBoxForAccuracy=spin_box_for_accuracy

        layout_accuracy.addWidget(label_for_accuracy)
        layout_accuracy.addWidget(spin_box_for_accuracy)
        
        layout_engine = QHBoxLayout()
        self.engine_combobox = QComboBox()
        label_for_engine = QLabel("Engine:")
        self.engine_list = SettingsValue.engine_list()
        self.engine_combobox.addItems(self.engine_list)
        self.engine_combobox.setFixedHeight(60)
        
        
        print("startup settings")
        print(self.engine_list.index(self.settings["engine"]))
        self.engine_combobox.setCurrentIndex(self.engine_list.index(self.settings["engine"]))

        layout_engine.addWidget(label_for_engine)
        layout_engine.addWidget(self.engine_combobox)
        
        spacing_layout = QVBoxLayout()
        spacing_layout.addLayout(layout_cover)
        spacing_layout.addSpacing(10)  # Adjust the spacing value as needed
        spacing_layout.addLayout(layout_cover_color)
        spacing_layout.addSpacing(10)  # Adjust the spacing value as needed
        spacing_layout.addLayout(layout_object)
        spacing_layout.addSpacing(20)  
        spacing_layout.addLayout(layout_accuracy)
        spacing_layout.addSpacing(10)  
        spacing_layout.addLayout(layout_engine)
        spacing_layout.addSpacing(10)  
        # spacing_layout.addLayout(layout_activity)
        # spacing_layout.addSpacing(10)  
        # spacing_layout.addLayout(layout_blur_kernel)
        
        
        main_layout.addLayout(spacing_layout)
        main_layout.setAlignment(Qt.AlignTop)

        object_and_cover_widget.setLayout(main_layout)

        return object_and_cover_widget

    def create_accuracy_properties(self):
        accuracy_widget = QWidget()
        main_layout = QVBoxLayout()

        

        layout_network_width = QHBoxLayout()
        label_for_network_width = QLabel("Network Width:")
        spin_box_for_network_width = QSpinBox()
        spin_box_for_network_width.setRange(5, 19)
        spin_box_for_network_width.setSingleStep(1)
        spin_box_for_network_width.setValue(self.settings["network_width"])
        self.spinBoxForNetworkWidth=spin_box_for_network_width

        layout_network_width.addWidget(label_for_network_width)
        layout_network_width.addWidget(spin_box_for_network_width)

        layout_network_height = QHBoxLayout()
        label_for_network_height = QLabel("Network Height:")
        spin_box_for_network_height = QSpinBox()
        spin_box_for_network_height.setRange(5, 15)
        spin_box_for_network_height.setSingleStep(1)
        spin_box_for_network_height.setValue(self.settings["network_height"])
       
        self.spinBoxForNetworkHeight=spin_box_for_network_height

        layout_network_height.addWidget(label_for_network_height)
        layout_network_height.addWidget(spin_box_for_network_height)

        
        
        
        

         # Add spacing between layouts
        spacing_layout = QVBoxLayout()
        
        spacing_layout.addSpacing(10)  # Adjust the spacing value as needed
        spacing_layout.addLayout(layout_network_width)
        spacing_layout.addSpacing(10)  # Adjust the spacing value as needed
        spacing_layout.addLayout(layout_network_height)
        spacing_layout.addSpacing(10)  # Adjust the spacing value as needed
        


         # Align the spacing_layout to the left
        
        main_layout.addLayout(spacing_layout)
        main_layout.setAlignment(Qt.AlignTop)

        accuracy_widget.setLayout(main_layout)

        return accuracy_widget

    def create_timeout_properties(self):
        timeout_widget = QWidget()
        main_layout = QVBoxLayout()
        

        layout_active = QHBoxLayout()
        label_active_timeout = QLabel("Active (ms):")
        spin_box_active_timeout = QSpinBox()
        spin_box_active_timeout.setRange(10, 2000)
        spin_box_active_timeout.setSingleStep(5)
        spin_box_active_timeout.setValue(self.settings["active_timeout"])
        self.spinBoxActiveTimeout=spin_box_active_timeout

        layout_active.addWidget(label_active_timeout)
        layout_active.addWidget(spin_box_active_timeout)

        layout_sleep = QHBoxLayout()
        label_sleep_timeout = QLabel("Sleep (ms):")
        spin_box_sleep_timeout = QSpinBox()
        spin_box_sleep_timeout.setRange(300, 20000)
        spin_box_sleep_timeout.setSingleStep(100)
        spin_box_sleep_timeout.setValue(self.settings["sleep_timeout"])  # Defa
        self.spinBoxSleepTimeout=spin_box_sleep_timeout

        layout_sleep.addWidget(label_sleep_timeout)
        layout_sleep.addWidget(spin_box_sleep_timeout)


        layout_keep_running = QHBoxLayout()
        label_keep_active_time = QLabel("Keep running (s):")
        spin_box_keep_active_time = QSpinBox()
        spin_box_keep_active_time.setRange(5, 20000)
        spin_box_keep_active_time.setSingleStep(2)
        spin_box_keep_active_time.setValue(self.settings["keep_running_timeout"])
        self.spinBoxKeepActiveTime=spin_box_keep_active_time

        layout_keep_running.addWidget(label_keep_active_time)
        layout_keep_running.addWidget(spin_box_keep_active_time)



         # Add spacing between layouts
        spacing_layout = QVBoxLayout()
        spacing_layout.addLayout(layout_active)
        spacing_layout.addSpacing(10)  # Adjust the spacing value as needed
        spacing_layout.addLayout(layout_sleep)
        spacing_layout.addSpacing(10)  # Adjust the spacing value as needed
        spacing_layout.addLayout(layout_keep_running)


         # Align the spacing_layout to the left
        
        main_layout.addLayout(spacing_layout)
        main_layout.setAlignment(Qt.AlignTop)

        timeout_widget.setLayout(main_layout)
        return timeout_widget

    def create_additional_options_properties(self):
        
        additional_options_widget = QWidget()

        self.checkbox_hardware_acceleration = QCheckBox("Hardware Accelerated Window ")
        self.checkbox_hardware_acceleration.setChecked(self.settings["hardware_accelerated"])


        
        specific_window_label=QLabel("Write your specific window name")
        self.specific_window_name=QLineEdit()#self.settings["specific_window_name"])


        self.checkbox_static_cover = QCheckBox("Static Cover")
        self.checkbox_static_cover.setEnabled(False) #Making this deactivate, If needed then added later
        self.checkbox_auto_startup = QCheckBox("Auto Startup When Booting")
        self.checkbox_static_cover_for_specific_window = QCheckBox("Static Cover For Specific Window")
        self.make_priroty_realtime = QCheckBox("Make Priroty Normal to Realtime (Faster Response)")
        self.make_priroty_realtime.setChecked(self.settings["is_priority_realtime"])
        
        
        #self.checkbox_auto_startup.setChecked(self.settings["auto_startup"]) #As it automatically checks from regestry

        #================ The startup process ===========================================================
        RUN_PATH = "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        startup_settings = QSettings(RUN_PATH, QSettings.NativeFormat)
        # Check if the value exists
        if startup_settings.value("PordaAi", defaultValue=False, type=bool):
            # Get the value from the registry
            registry_value = startup_settings.value("PordaAi")

            if getattr(sys, 'frozen', False):
                value_should_be = f'"{sys.executable}" --startup_by_windows'
                if registry_value == value_should_be: # checking that the value is okey
                    self.checkbox_auto_startup.setChecked(True)
                else:
                    self.checkbox_auto_startup.setChecked(False)
            else:
                self.checkbox_auto_startup.setChecked(startup_settings.value("PordaAi", defaultValue=False, type=bool))

                print("not executable")
            
        else:
            self.checkbox_auto_startup.setChecked(False)

        hot_key_label=QLabel("Hotkey (ex:ctrl+p)")
        self.hot_key=QLineEdit(self.settings["shortcut_key"])

        hot_key_screenshot_label=QLabel("Hotkey For Dataset Enrichment (ex:ctrl+p)")
        self.hot_key_screenshot=QLineEdit(self.settings["capture_screenshot"])

        dataset_path_label=QLabel("Dataset Path")
        self.dataset_path=QLineEdit(self.settings["dataset_path"])

        # Create a QVBoxLayout for additional_options_widget
        layout = QVBoxLayout()

        # Add spacing between layouts
        # layout.addWidget(self.checkbox_hardware_acceleration)
        # layout.addSpacing(10)
        # layout.addWidget(self.checkbox_specific_window)
        # layout.addSpacing(10)
        #layout.addWidget(specific_window_label)
        #layout.addWidget(self.specific_window_name)

        # layout.addWidget(self.checkbox_static_cover)
        layout.addSpacing(10)
        layout.addWidget(self.checkbox_auto_startup)
        layout.addSpacing(10)
        layout.addWidget(self.make_priroty_realtime)
        layout.addSpacing(10)
        layout.addWidget(hot_key_label)
        layout.addWidget(self.hot_key)
        layout.addSpacing(10)
        layout.addWidget(hot_key_screenshot_label)
        layout.addWidget(self.hot_key_screenshot)
        layout.addSpacing(10)
        layout.addWidget(dataset_path_label)
        layout.addWidget(self.dataset_path)

        # Align the layout to the left
        layout.setAlignment(Qt.AlignTop)

        # Set the layout for additional_options_widget
        additional_options_widget.setLayout(layout)

        return additional_options_widget


    #===========================================================

    def save_settings_value(self):
        print(" enter insave method")

        self.settings["accuracy"] = self.spinBoxForAccuracy.value()
      
        self.settings["network_width"] = self.spinBoxForNetworkWidth.value()
        self.settings["network_height"] = self.spinBoxForNetworkHeight.value()

        self.settings["active_timeout"] = self.spinBoxActiveTimeout.value()
        self.settings["sleep_timeout"] = self.spinBoxSleepTimeout.value()
        self.settings["keep_running_timeout"] = self.spinBoxKeepActiveTime.value()

        self.settings["engine"] = self.engine_combobox.currentText()

        self.settings["is_blur"] = self.blur_checkbox.isChecked()
        self.settings["is_color"] = self.color_checkbox.isChecked()
        self.settings["is_bg_color"] = self.bg_color_checkbox.isChecked()
        self.settings["rgb_color_value"] = self.rgb_color_value
        

        self.settings["object"] = self.object_combobox.currentText()
        self.settings["is_detect_male"] = self.male_checkbox.isChecked()
        self.settings["is_detect_female"] = self.female_checkbox.isChecked()
        
        '''if self.activity_status_combobox.currentIndex() == 0:
            self.settings["activity_status"] = True
        else:
            self.settings["activity_status"] = False'''

        if self.button_text == "deactive":
            self.settings["activity_status"] = True
        else:
            self.settings["activity_status"] = False


        if self.checkbox_auto_startup.isChecked():
            self.settings["auto_startup"] = True
        else:
            self.settings["auto_startup"] = False
            
        #============ Save auto startup to regestry ====================================================
        RUN_PATH = "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        startup_settings = QSettings(RUN_PATH, QSettings.NativeFormat)
        try:
            if self.checkbox_auto_startup.isChecked():
                if getattr(sys, 'frozen', False):
                    print(" Frozen enter MEIPASS:", sys._MEIPASS)
                    startup_settings.setValue("PordaAi", f'"{sys.executable}" --startup_by_windows') #double quotation can be given
                    print("set auto startup Frozen enter sys.executable=",sys.executable)
                else:
                    #print("not frozen enter MEIPASS:", sys._MEIPASS)
                    startup_settings.setValue("PordaAi", f'"{sys.executable}" --startup_by_windows')
                    print("set auto startup sys.executable=",sys.executable)
            else:
                startup_settings.remove("PordaAi")
                print("removed")
        except:
            message.show_message("Getting error while saving auto start-up system. May be permission required, try run the app with permission.")
        #=================================================================================================

        self.settings["hardware_accelerated"] = False
        if self.checkbox_hardware_acceleration.isChecked():
            self.settings["hardware_accelerated"] = True
        if self.make_priroty_realtime.isChecked():
            self.settings["is_priority_realtime"] = True


        dataset_path=self.dataset_path.text()
        if dataset_path:
            if os.path.exists(dataset_path) and os.path.isdir(dataset_path):
                print("Directory exists.")
                dataset_path=os.path.join(dataset_path,"PordaAi-Dataset")
                self.settings["dataset_path"] = dataset_path
            else:
                print("Directory does not exist.")
                message.show_message("Your Dataset Path is invalid")
        else:
            default_settings = SettingsValue.default_settings
            self.settings["dataset_path"] = default_settings["dataset_path"]


        if self.hot_key.text()==self.hot_key_screenshot.text():
            message.show_message("Your Hot key can be same")
        else:
            hot_key_text = self.hot_key.text()
            if hot_key_text:
                import keyboard
                try:
                    keyboard.add_hotkey(self.hot_key.text(), lambda: None,suppress=True)
                    self.settings["shortcut_key"] = hot_key_text

                except Exception as e:
                    print(f"Your input is not valid please correct it {e}")
                    message.show_message("Your Hot key is not valid please correct it. Or it saves as default.")
            
            
            hot_key_screenshot_text = self.hot_key_screenshot.text()
            if hot_key_screenshot_text:
                import keyboard
                try:
                    keyboard.add_hotkey(self.hot_key_screenshot.text(), lambda: None,suppress=True)
                    self.settings["capture_screenshot"] = hot_key_screenshot_text

                except Exception as e:
                    print(f"Your input is not valid please correct it {e}")
                    message.show_message("Your Hot key for dataset enrichment is not valid please correct it. Or it saves as default.")

        
        #=========================================================
        self.settings["is_all_window"] =self.all_windows_checkbox.isChecked()
        self.settings["is_include_window"] = self.include_windows_checkbox.isChecked()
        self.settings["is_exclude_window"] = self.exclude_windows_checkbox.isChecked()
    

        #self.settings["exclude_windows"] = self.exclude_window_input.toPlainText().lower().replace('\n', '')
        #self.settings["include_windows"] = self.include_window_input.toPlainText().lower().replace('\n', '')
        self.settings["exclude_windows"] = self.exclude_window_input.toPlainText().replace('\n', '') 
        #Some app has its name capital latter, 
        #so if i use lower() then agian i have to make lowwer in get_datav2
        self.settings["include_windows"] = self.include_window_input.toPlainText().replace('\n', '')



        self.settings["is_allow_max_cpu_limit"] = False
        if self.allow_max_cpu_limit_checkbox.isChecked():
            self.settings["is_allow_max_cpu_limit"]=True

        self.settings["max_cpu_limit"] = self.spin_box_for_max_cpu_limit.value()
        

        #========================================================

        print(self.settings)
        try: # If any issue when saving file then get default for example: permission denied
            SettingsValue.save_settings(self.settings)
            message.show_message("Setting Was Saved")
        except Exception as e:
            self.default_settings_value()
            message.show_message(f"Error while saving settings Setting: {e}")

        
    def update_setting(self):
        self.current_settings["accuracy"] = self.spinBoxForAccuracy.value()
        self.current_settings["network_width"] = self.spinBoxForNetworkWidth.value()
        self.current_settings["network_height"] = self.spinBoxForNetworkHeight.value()
        self.current_settings["active_timeout"] = self.spinBoxActiveTimeout.value()
        self.current_settings["sleep_timeout"] = self.spinBoxSleepTimeout.value()
        self.current_settings["keep_running_timeout"] = self.spinBoxKeepActiveTime.value()
        self.current_settings["engine"] = self.engine_combobox.currentText()

        self.current_settings["is_blur"] = self.blur_checkbox.isChecked()
        self.current_settings["is_color"] = self.color_checkbox.isChecked()
        self.current_settings["is_bg_color"] = self.bg_color_checkbox.isChecked()
        self.current_settings["rgb_color_value"] = self.rgb_color_value
        
        
        # self.current_settings["blur_kernel"] = self.spin_box_for_blur_kernel.value()
        self.current_settings["object"] = self.object_combobox.currentText()
        self.current_settings["is_detect_male"] = self.male_checkbox.isChecked()
        self.current_settings["is_detect_female"] = self.female_checkbox.isChecked()
        self.current_settings["is_all_window"] = self.all_windows_checkbox.isChecked()
        self.current_settings["is_include_window"] = self.include_windows_checkbox.isChecked()
        self.current_settings["is_include_window"] = self.include_windows_checkbox.isChecked()
        self.current_settings["is_showing_included_app"] = self.get_app_included_windows_checkbox.isChecked()
        self.current_settings["exclude_windows"] = self.exclude_window_input.toPlainText().replace('\n', '') 
        self.current_settings["include_windows"] = self.include_window_input.toPlainText().replace('\n', '')
        
        self.current_settings["is_detect_specific_window"] = self.checkbox_specific_window.isChecked()
        self.current_settings["is_allow_max_cpu_limit"] = self.allow_max_cpu_limit_checkbox.isChecked()
        self.current_settings["max_cpu_limit"] = self.spin_box_for_max_cpu_limit.value()
        self.current_settings["is_now_active"] = self.getStatus()
        
        self.parent.update_settings(True)
        

    def default_settings_value(self):

        default_settings = SettingsValue.default_settings

        self.spinBoxForAccuracy.setValue(default_settings["accuracy"])
      
        self.spinBoxForNetworkWidth.setValue(default_settings["network_width"])
        self.spinBoxForNetworkHeight.setValue(default_settings["network_height"])

        self.spinBoxActiveTimeout.setValue(default_settings["active_timeout"])
        self.spinBoxSleepTimeout.setValue(default_settings["sleep_timeout"])
        self.spinBoxKeepActiveTime.setValue(default_settings["keep_running_timeout"])

        self.blur_checkbox.setChecked(default_settings["is_blur"])
        self.color_checkbox.setChecked(default_settings["is_color"])
        self.bg_color_checkbox.setChecked(default_settings["is_bg_color"])
        rgb_color=f"rgb{default_settings["rgb_color_value"]}"
        self.lbl.setStyleSheet(f'background-color: {rgb_color}; color:{rgb_color}; padding: 5px')
        
        
        self.object_combobox.setCurrentIndex(self.object_list.index(default_settings["object"]))
        self.male_checkbox.setChecked(default_settings["is_detect_male"])
        self.female_checkbox.isChecked(default_settings["is_detect_female"])


        self.checkbox_hardware_acceleration.setChecked(default_settings["hardware_accelerated"])


        self.all_windows_checkbox.setChecked(self.settings["is_all_window"])
        self.include_windows_checkbox.setChecked(self.settings["is_include_window"])
        self.exclude_windows_checkbox.setChecked(self.settings["is_exclude_window"])

        self.exclude_window_input.setText(default_settings["exclude_windows"])
        self.include_window_input.setText(default_settings["include_windows"])

    #===========================================================
    def get_window_to_detect(self):
        if self.all_windows_checkbox.isChecked():
            return "all"
        elif self.exclude_windows_checkbox.isChecked():
            return "excluded"
        elif self.include_windows_checkbox.isChecked():
            return "included"
        elif self.get_app_excluded_windows_checkbox.isChecked():
            return "get_app_for_excluded_windows"
        elif self.get_app_included_windows_checkbox.isChecked():
            print("======Included App===========")
            return "get_app_for_included_windows"
        
    def get_included_windows(self):
        windows = self.include_window_input.toPlainText()
        window_list = [item.strip() for item in windows.split(',') if item]
        print(f'Included window: {window_list}')
        return window_list
    def get_excluded_windows(self):

        windows = self.exclude_window_input.toPlainText()
        window_list = [item.strip() for item in windows.split(',') if item]
        print(f'Excluded window: {window_list}')
        return window_list
    #===========================================
    def change_status(self):
        print("change_status method in Setting")
        
        
        
        if self.button_text ==  "active":
            self.parent.status_button_state = True
            self.status_button.setText("Deactivate")
            self.button_text = "deactive"
            self.activity_status_combobox.setCurrentIndex(0)
            self.setWindowTitle(f"{self.title} - is Active")
           
            if self.parent.ready_to_start_detection:
                self.parent.detection_timer.start(self.spinBoxActiveTimeout.value())
                self.parent.isNow_Active_Mode = True
                self.parent.isNow_Sleep_Mode = False
                
        else:
           
            self.parent.status_button_state = False
            self.status_button.setText("Activate")
            self.button_text = "active"
            self.parent.detection_timer.stop()
            #self.parent.enable_disable_by_shortcut_key(True)
            self.activity_status_combobox.setCurrentIndex(1)
            self.setWindowTitle(f"{self.title} - is not Active")
        
    # ---------------------------------------------------------------------------
    def on_ok_button_clicked(self):
        # Update the attribute of the parent class
        # self.parent.update_settings(True)
        
        self.accept()
        
    def getDetectionAccuracy(self):
        return self.spinBoxForAccuracy.value()
    
   
    def getNetworkWidth(self):
        return int(self.spinBoxForNetworkWidth.value()*32)
    def getNetworkHeight(self):
        return int(self.spinBoxForNetworkHeight.value()*32)

    # ---------------------------------------------------------------------------

    # -------------TIMEOUT-------------------------------------------------------
    def getActiveTimeOut(self):
        return self.spinBoxActiveTimeout.value()
    
    def getSleepTimeOut(self):
        return self.spinBoxSleepTimeout.value()
    
    def getKeepActiveTime(self):
        return self.spinBoxKeepActiveTime.value()

    # --------------------------------------------------------------------------

    #========= Engine ============================================================
    def getEngine(self):
        return self.engine_combobox.currentText()

    #===========================================================================
    
    
    def getBlurKernel(self):
        return 0 #self.spin_box_for_blur_kernel.value()
    
    def getObjectCombobox(self):
        return self.object_combobox.currentText() #here i return the index number
    
    def getStatus(self):
        #if self.activity_status_combobox.currentIndex() == 0:
        if self.button_text == "deactive":
            self.setWindowTitle(f"{self.title} - is Active")
            return True
        else:
            self.setWindowTitle(f"{self.title} - is not Active")
            return False
    #=======================================================================

    
    # ----------------------------------------------------------------------
    def isHardwareAccelarationEnabled(self):
        return self.checkbox_hardware_acceleration.isChecked()

    def isSpecificWindowEnabled(self):
        return self.checkbox_specific_window.isChecked()
    def isSpecificAppEnabled(self):
        return self.checkbox_specific_app.isChecked()
    
    def SpecificWindowAppName(self):
        apps = self.specific_window_name.text()
        app_list = [item.strip() for item in apps.split(',') if item]
        if app_list:
            return app_list[0]
        else:
            return None

        


    def isStaticCoverEnabled(self):
        return self.checkbox_static_cover.isChecked()
    
    def isStaticCoverForSpecificWindow(self):
        return self.checkbox_static_cover_for_specific_window.isChecked()
    
    def isAutoStartup(self):
        return self.checkbox_auto_startup.isChecked()
    #===============================================================



    def closeEvent(self, event):
        self.application_is_about_to_close = True
        #self.accept()
        self.parent.closetheapp()

    def close_app(self):
        print("close print")
        self.application_is_about_to_close = True
        #self.accept()
        self.parent.closetheapp()
        print("close print")

        #QApplication.quit()
        #sys.exit()
