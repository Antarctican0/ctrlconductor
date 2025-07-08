## Easy Controls for Run8 Train Simulator!
This program is meant to make using custom controls easier with Run8. It accomplishes this by taking mapped inputs of your devices and sending them in a format the simulator expects.

![image](https://github.com/user-attachments/assets/b4eab56a-b74f-4c32-bcc9-1d7a4d6a848b)

## Quick Start

### Option 1: Download Pre-built Release
1. **[📥 Download Latest Release](https://github.com/Antarctican0/ctrlconductor/releases/latest)**
2. Extract the zip file
3. Run `Run8ControlConductor.exe`

### Option 2: Run from Source
1. Clone this repository
2. Install Python 3.8+ and pip
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python main.py`

## Operations Manual
**Make sure that Run8 is set to use Custom USB Device and that the ports match!**

![image](https://github.com/user-attachments/assets/1bcd3f34-1a71-43f4-93f7-d7a109214ae2)

![image](https://github.com/user-attachments/assets/053f7f55-bde4-4bfd-82cd-0a353fa5b024)


### Throttle and Dynamic Braking
The Throttle and Dynamic Brakes can operate in one of three ways, based on your preference in control type. 
They can be mapped to two separate axis, and will appear individually to be mapped:

![image](https://github.com/user-attachments/assets/4b90cd6f-182e-4d39-8678-1cef9c636492)

They can be combined into one axis, with the upper half acting as the throttle, and the lower as the Dynamic Brake.

![image](https://github.com/user-attachments/assets/6aada74c-0747-4dd1-8463-b960d5a46e00)

Lastly, They can share the same axis, with a toggle switch being used to flip between the two functions. A new field will appear to assign this toggle.

![image](https://github.com/user-attachments/assets/b888bf47-d21e-4fa5-b13c-1c12cd89a5a0)

### Reverser
The Reverser can operate in two styles; controlled either by an axis input or controlled with buttons. When one of the button modes is selected, new fields will appear to assign either 2 or 3 inputs based off how your controls are configured in real life. 
- 2 Way Switch is recommended for two position rocker switches, as well as 3 position toggles that do not have a button mapped for the middle / neutral position.
- 3 Way Switch is recommended when you are utilizing a button box

![image](https://github.com/user-attachments/assets/7ba0500b-13e5-4004-878d-3853e480d784)

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Run8 Train Simulator for providing the UDP interface
- pygame community for excellent input handling
- Contributors and testers
- ChatGPT 4.1, Claude Sonnet 4 and 3.7 Thinking, Gemini 2.5 Pro Preview
