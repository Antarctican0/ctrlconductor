# Run8 Control Conductor

A modular GUI application that maps joystick/gamepad inputs to Run8 train simulator functions via UDP communication.

## Features

- **Multiple Input Device Support**: Works with joysticks, gamepads, and other input devices
- **Configurable Mapping**: Easily map inputs to Run8 functions with persistent storage
- **Modern Dark Theme UI**: Clean, tabbed interface organized by function categories
- **Real-time Processing**: Live input detection and UDP transmission
- **Flexible Input Types**: Support for momentary, toggle, lever, and multi-way switch inputs
- **Axis Reversal**: Configurable axis reversal for lever controls
- **Modular Architecture**: Well-organized, maintainable code structure

## New in Version 3.0

- **Modular Design**: Code split into focused modules for better maintainability
- **Improved Error Handling**: Better error messages and logging
- **Enhanced Documentation**: Comprehensive docstrings and type hints
- **Developer-Friendly**: Easier to fork, modify, and contribute to

## Architecture

### Module Overview

- **`main.py`**: Main application entry point and coordinator
- **`networking.py`**: UDP communication with Run8 simulator
- **`input_handler.py`**: Input device management and processing
- **`mapping_logic.py`**: Input mapping and value processing logic
- **`ui_components.py`**: User interface creation and management
- **`config.py`**: Configuration constants and settings
- **`utils.py`**: Utility functions and helper classes

### Key Classes

- **`Run8ControlConductor`**: Main application class
- **`UDPClient`**: Handles UDP communication
- **`InputManager`**: Manages input devices
- **`InputMapper`**: Handles input mapping logic
- **`UIManager`**: Manages the user interface

## Installation

1. **Clone or Download**: Get the project files
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Application**:
   ```bash
   python main.py
   ```

## Usage

### Basic Setup

1. **Configure Connection**:
   - Set the simulator IP address (default: 127.0.0.1)
   - Set the simulator port (default: 18888)

2. **Enable Input Devices**:
   - Click "Refresh Devices" to detect connected controllers
   - Check the boxes for devices you want to use

3. **Map Inputs**:
   - Navigate through the function categories (Main Controls, Lights & Wipers, DPU, Misc)
   - Click "Map Input" next to any function
   - Move/press the desired input within 5 seconds
   - For lever controls, check "Reverse" if needed

4. **Start Processing**:
   - Click "Start" to begin processing inputs
   - The application will send UDP commands to Run8

### Input Types

- **Momentary**: Sends signal while pressed (Horn, Bell, Sander)
- **Toggle**: Toggles state on press (Light switches)
- **Lever**: Analog control with multiple positions (Throttle, Brakes)
- **Multi-way**: Cycles through states (3-way/4-way switches)

### Saving/Loading

- **Save Mappings**: Saves current input mappings to CSV file
- **Load Mappings**: Loads previously saved mappings
- **Clear All**: Removes all current mappings

## File Structure

```
run8inputpy/
├── main.py              # Main application entry point
├── networking.py        # UDP communication module
├── input_handler.py     # Input device management
├── mapping_logic.py     # Input mapping logic
├── ui_components.py     # User interface components
├── config.py           # Configuration and constants
├── utils.py            # Utility functions
├── __init__.py         # Package initialization
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── LICENSE            # MIT License
├── .gitignore         # Git ignore rules
└── input_mappings.csv # Saved mappings (created automatically)
```

## Development

### For Developers

The modular structure makes it easy to:

- **Add new input types**: Extend `mapping_logic.py`
- **Support new protocols**: Modify or extend `networking.py`
- **Customize UI**: Modify `ui_components.py` and `config.py`
- **Add new features**: Clean separation of concerns

### Code Organization

- **Separation of Concerns**: Each module has a specific responsibility
- **Type Hints**: Full type annotations for better IDE support
- **Comprehensive Logging**: Detailed logging for debugging
- **Error Handling**: Robust error handling throughout
- **Documentation**: Extensive docstrings and comments

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes in the appropriate module
4. Test thoroughly
5. Submit a pull request

## Run8 Functions

The application supports all major Run8 functions organized by category:

### Main Controls
- Throttle Lever, Train Brake Lever, Independent Brake Lever
- Dynamic Brake Lever, Reverser Lever
- Horn, Bell, Sander, Alerter

### Lights and Wipers
- Front/Rear Headlights, Wiper Switch
- Cab Light, Step Light, Gauge Light switches

### DPU (Distributed Power Unit)
- DPU Throttle Increase/Decrease
- DPU Dynamic Brake Setup
- DPU Fence Increase/Decrease

### Miscellaneous
- EOT Emergency Stop, HEP Switch
- Slow Speed controls, Park Brake
- Distance Counter, Independent Bailoff

## Requirements

- Python 3.7+
- pygame (for input handling)
- tkinter (usually included with Python)
- Run8 Train Simulator

## Troubleshooting

### Common Issues

1. **No devices detected**: 
   - Ensure controllers are connected and recognized by Windows
   - Click "Refresh Devices" after connecting new devices

2. **Input not responsive**:
   - Check if device is enabled (checkbox checked)
   - Verify the mapping is correct
   - Try re-mapping the input

3. **Connection issues**:
   - Verify Run8 is running and listening on the specified port
   - Check firewall settings
   - Ensure IP address and port are correct

### Debug Mode

The application includes comprehensive logging. Check the console output for detailed information about:
- Device detection and initialization
- Input processing and mapping
- UDP communication
- Error messages and warnings

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Run8 Train Simulator for providing the UDP interface
- pygame community for excellent input handling
- Contributors and testers

## Version History

- **v3.0**: Modular architecture, improved error handling, enhanced documentation
- **v2.0**: Enhanced UI, better input processing, configuration improvements
- **v1.0**: Initial release with basic functionality
