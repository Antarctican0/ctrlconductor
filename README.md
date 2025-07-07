# Run8 Control Conductor

A modular GUI application that maps joystick/gamepad inputs to Run8 train simulator functions via UDP communication.

## Features

- **Multi-device Support**: Connect and use multiple controllers simultaneously
- **Flexible Input Mapping**: Map buttons, axes, and hat switches to Run8 functions
- **Real-time Processing**: Low-latency input processing for responsive control
- **Modular Architecture**: Clean, maintainable code structure
- **User-friendly Interface**: Intuitive GUI with tabbed organization
- **Persistent Settings**: Save and load your controller configurations
- **Comprehensive Logging**: Built-in debugging and error reporting

## Quick Start

### Option 1: Download Pre-built Release
1. **[📥 Download Latest Release](https://github.com/Antarctican0/ctrlconductor/releases/latest)**
2. Extract the zip file
3. Run `Run8ControlConductor.exe`
4. See `USER_GUIDE.txt` for setup instructions

### Option 2: Run from Source
1. Clone this repository
2. Install Python 3.8+ and pip
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python main.py`

## Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed information about the codebase architecture.

## Building from Source

To create your own executable:

```bash
# Install build dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build the executable
python build_executable.py
```

The executable will be created in the `release/` directory.

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

### Debug Information

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
