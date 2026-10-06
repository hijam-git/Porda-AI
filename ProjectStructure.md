## Project Structure

```
Porda-AI/
├── main.py                    # Main application entry point
├── GetDataV2.py              # Screen capture and window management
├── SetupPordaApp.py          # Application setup and configuration
├── settings/
│   ├── SettingsValue.py      # Settings management
│   ├── message.py            # Message and notification system
│   ├── startup.py            # Startup configuration
│   ├── settingscss2.py       # UI styling
│   ├── doc.py                # Documentation content
│   ├── ga4_porda.py          # Google Analytics tracking
│   ├── EngineSetting.py      # Detection engine configuration
│   └── Settings.py           # Main settings interface
├── model/                    # Neural network model files
├── readme-assets/            # Documentation assets
└── context.md               # This documentation file
```

## Key Features Documented

### Core Functionality
- **Screen Capture**: Real-time screen capture with window filtering
- **Object Detection**: AI-powered object detection using YOLO models
- **Overlay System**: Dynamic overlay drawing for detected objects
- **Settings Management**: Comprehensive settings interface
- **System Tray Integration**: System tray icon with context menu
- **Keyboard Shortcuts**: Configurable hotkeys for various actions
- **CPU Monitoring**: Automatic detection stopping based on CPU usage

### Technical Components
- **PyQt5 GUI Framework**: Main application interface
- **OpenCV**: Computer vision and image processing
- **Windows API**: Screen capture and window management
- **Neural Networks**: YOLO-based object detection
- **OpenCL**: GPU acceleration support
- **Google Analytics**: Usage tracking and analytics