# Run8 Control Conductor

A modular GUI application that maps joystick/gamepad inputs to Run8 train simulator functions via UDP communication.

### Quick Download Links:
- **[📥 Download Latest Release](https://github.com/Antarctican0/ctrlconductor/releases/latest)** 
- **[📋 Quick Start Guide](release/QUICK_START_GUIDE.md)**

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
