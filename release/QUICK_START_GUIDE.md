# Run8 Control Conductor - Quick Start Guide

## 🚀 Quick Start for New Users

### Step 1: Download and Run
1. Download `Run8ControlConductor.exe` from the releases section
2. Double-click to run the executable (no installation required)
3. If Windows shows a security warning, click "More info" then "Run anyway"

### Step 2: First Time Setup
1. **Connect your controller**: Plug in your joystick/gamepad to your computer
2. **Start Run8**: Make sure Run8 Train Simulator is running
3. **Detect your controller**: In the application, click "Refresh Devices" to detect your controller
4. **Enable your controller**: Check the box next to your controller to enable it

### Step 3: Map Your Controls
1. **Navigate tabs**: Use the tabs at the top (Main Controls, Lights & Wipers, DPU, Misc)
2. **Map functions**: Click "Map Input" next to any function you want to control
3. **Move/press control**: Within 5 seconds, move/press the desired control on your joystick
4. **Repeat**: Map all the functions you want to use
5. **For lever controls**: Check "Reverse" if the direction feels wrong

### Step 4: Start Using
1. **Click "Start"** to begin processing inputs
2. **Control Run8**: Your joystick inputs will now control Run8 functions
3. **Save mappings**: Click "Save Mappings" to save your controller setup for next time

## 💡 Tips
- **Save Your Setup**: Always click "Save Mappings" when you're happy with your controller setup
- **Load Previous Setup**: Click "Load Mappings" to restore previously saved settings
- **Multiple Controllers**: You can enable and use multiple controllers at the same time
- **Reverse Controls**: For throttle/brake levers, use the "Reverse" checkbox if they feel backwards

## 🔧 Troubleshooting
- **Controller not detected**: Make sure it's connected and working in Windows Game Controllers
- **No response in Run8**: Check that Run8 is running and the IP/port settings are correct (usually 127.0.0.1:18888)
- **Wrong direction**: Use the "Reverse" checkbox for lever controls that feel backwards

## 📋 System Requirements
- Windows 10/11 (64-bit)
- Run8 Train Simulator
- USB joystick/gamepad

## 🏗️ For Developers
If you want to modify the source code or contribute:
1. Clone the repository: `git clone https://github.com/your-username/ctrlconductor.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run from source: `python main.py`
4. Build executable: `python build_executable.py`

For support and updates, visit: https://github.com/your-username/ctrlconductor
