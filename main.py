"""
Run8 Control Conductor - Main Application

A modular GUI application that maps joystick/gamepad inputs to Run8 train simulator 
functions and sends them via UDP packets.

This is the main application entry point that coordinates all the modules:
- networking: UDP communication
- input_handler: Input device management
- mapping_logic: Input mapping and processing
- ui_components: User interface
- config: Configuration and constants
- utils: Utility functions

Author: Ethan
Version: 3.0 (Modular)
"""

import tkinter as tk
import threading
import time
import logging
import os
import sys
import json
from typing import Optional, Dict, Any

from config import DEFAULT_IP, DEFAULT_PORT, POLLING_INTERVAL, UDP_SEND_INTERVAL, FunctionMapping
from networking import UDPClient
from input_handler import InputManager
from mapping_logic import InputMapper
from ui_components import UIManager
from utils import PeriodicTimer, StateTracker, format_input_display, setup_logging

# Setup logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)


class Run8ControlConductor:
    def toggle_throttle_mode(self, mode: str) -> None:
        """Toggle between throttle modes: separate, toggle, split"""
        self.throttle_mode = mode
        self.input_mapper.set_throttle_mode(mode)
        self.ui_manager.set_throttle_mode(mode)
    """Main application class that coordinates all modules"""
    
    def __init__(self):
        """Initialize the Run8 Control Conductor application"""
        logger.info("Initializing Run8 Control Conductor v3.0")

        # Initialize main window
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Initialize modules
        self.udp_client = UDPClient()
        self.input_manager = InputManager()
        self.input_mapper = InputMapper()
        self.ui_manager = UIManager(self.root)
        self.state_tracker = StateTracker()

        # Initialize application state
        self.running = False
        self.input_thread: Optional[threading.Thread] = None
        self.input_timer: Optional[PeriodicTimer] = None
        self.udp_timer: Optional[PeriodicTimer] = None

        # Input detection state
        self.waiting_for_input = False
        self.input_target_function: Optional[str] = None
        self.pending_commands: Dict[int, int] = {}  # function_id -> value

        # Reverser mode (default to axis)
        self.reverser_switch_mode = False

        # Combined throttle/dyn mode state
        self.combined_toggle_state = False  # False=Throttle, True=Dynamic
        self.last_toggle_button_state = False  # Track button state for edge detection

        # Auto-save settings
        self.auto_save_enabled = True
        self.auto_save_file = self._get_auto_save_file_path()

        # Setup UI callbacks
        self._setup_ui_callbacks()

        # Initialize with default values
        self.ui_manager.set_ip_address(DEFAULT_IP)
        self.ui_manager.set_port(DEFAULT_PORT)

        # Initialize throttle mode sync
        initial_throttle_mode = self.ui_manager.get_throttle_mode()
        self.input_mapper.set_throttle_mode(initial_throttle_mode)

        # Load persistent mappings automatically and refresh devices
        self._load_persistent_mappings()
        self.refresh_devices()

        logger.info("Run8 Control Conductor initialized successfully")
    
    def _setup_ui_callbacks(self) -> None:
        """Setup UI callback functions"""
        self.ui_manager.set_start_callback(self.start_application)
        self.ui_manager.set_stop_callback(self.stop_application)
        self.ui_manager.set_refresh_devices_callback(self.refresh_devices)
        self.ui_manager.set_load_mappings_callback(self.load_mappings)
        self.ui_manager.set_save_mappings_callback(self.save_mappings)
        self.ui_manager.set_clear_mappings_callback(self.clear_mappings)
        self.ui_manager.set_device_toggle_callback(self.on_device_toggle)
        self.ui_manager.set_map_input_callback(self.map_input)
        self.ui_manager.set_clear_mapping_callback(self.clear_mapping)
        self.ui_manager.set_reverser_mode_callback(self.toggle_reverser_mode)
        self.ui_manager.set_throttle_mode_callback(self.toggle_throttle_mode)
    
    def _get_auto_save_file_path(self) -> str:
        """Get the appropriate auto-save file path for persistent mappings"""
        try:
            # Try to use the application directory first (for portable installs)
            # Handle both script and executable environments
            if getattr(sys, 'frozen', False):
                # Running as executable
                app_dir = os.path.dirname(sys.executable)
                logger.debug(f"Running as executable, app directory: {app_dir}")
            else:
                # Running as script
                app_dir = os.path.dirname(os.path.abspath(__file__))
                logger.debug(f"Running as script, app directory: {app_dir}")
                
            auto_save_file = os.path.join(app_dir, 'auto_mappings.csv')
            
            # Test if we can write to the application directory
            test_file = os.path.join(app_dir, 'test_write.tmp')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                # If we can write to app directory, use it
                logger.info(f"Using app directory for auto-save: {auto_save_file}")
                return auto_save_file
            except (OSError, PermissionError):
                # Can't write to app directory, use user data directory
                logger.debug("App directory not writable, falling back to user data directory")
                pass
        except Exception as e:
            logger.debug(f"Error accessing app directory: {e}")
            pass
            pass
        
        # Fall back to user's AppData/Local directory
        try:
            import platform
            if platform.system() == 'Windows':
                appdata_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
                app_data_dir = os.path.join(appdata_dir, 'Run8ControlConductor')
            else:
                # For non-Windows systems
                app_data_dir = os.path.join(os.path.expanduser('~'), '.run8controlconductor')
            
            # Create directory if it doesn't exist
            os.makedirs(app_data_dir, exist_ok=True)
            auto_save_file = os.path.join(app_data_dir, 'auto_mappings.csv')
            logger.debug(f"Using user data directory for auto-save: {auto_save_file}")
            return auto_save_file
            
        except Exception as e:
            logger.warning(f"Failed to determine auto-save directory: {e}")
            # Last resort: use temp directory
            import tempfile
            auto_save_file = os.path.join(tempfile.gettempdir(), 'run8_auto_mappings.csv')
            logger.debug(f"Using temp directory for auto-save: {auto_save_file}")
            return auto_save_file
    
    def _load_persistent_mappings(self) -> None:
        """Load persistent mappings automatically"""
        try:
            if os.path.exists(self.auto_save_file):
                logger.info(f"Loading persistent mappings from: {self.auto_save_file}")
                self.load_mappings(self.auto_save_file)
                # Verify the mappings were loaded
                loaded_mappings = self.input_mapper.get_all_mappings()
                logger.info(f"Persistent mappings loaded successfully: {len(loaded_mappings)} mappings")
            else:
                logger.info(f"No persistent mappings file found at: {self.auto_save_file}")
                # Fall back to looking for legacy mappings file in multiple locations
                legacy_locations = [
                    # First try same directory as executable/script
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_mappings.csv"),
                    # Then try current working directory
                    os.path.join(os.getcwd(), "input_mappings.csv"),
                    # Then try the directory where the script was originally located
                    "input_mappings.csv"
                ]
                
                legacy_file_found = False
                for legacy_file in legacy_locations:
                    if os.path.exists(legacy_file):
                        logger.info(f"Importing legacy mappings from: {legacy_file}")
                        self.load_mappings(legacy_file)
                        # Auto-save the imported mappings for future use
                        self._auto_save_mappings()
                        legacy_file_found = True
                        break
                
                if not legacy_file_found:
                    logger.info("No persistent mappings found, starting with empty mappings")
                    self.load_mappings()
                    
        except Exception as e:
            logger.error(f"Error loading persistent mappings: {e}")
            # Fall back to default behavior
            self.load_mappings()
    
    def _auto_save_mappings(self) -> None:
        """Automatically save current mappings to the persistent file"""
        if not self.auto_save_enabled:
            return
            
        try:
            # Update reverse axis settings from UI before saving
            for function_name in self.input_mapper.get_mapped_functions():
                if function_name == "Reverser Lever" and self.reverser_switch_mode:
                    # Skip reverse axis setting for reverser in switch mode
                    continue
                    
                reverse_setting = self.ui_manager.get_reverse_axis_setting(function_name)
                self.input_mapper.set_axis_reverse(function_name, reverse_setting)
            
            # Ensure the input mapper has the correct reverser mode before saving
            if self.reverser_switch_mode:
                # Determine if it's 2way or 3way mode
                if getattr(self.input_mapper, 'reverser_two_input_mode', False):
                    mode = '2way'
                else:
                    mode = '3way'
            else:
                mode = 'axis'
            
            # Set the mode in the input mapper to ensure consistency
            self.input_mapper.set_reverser_switch_mode(mode)
            
            # Perform the auto-save
            if self.input_mapper.save_mappings(self.auto_save_file):
                logger.debug(f"Auto-saved mappings to: {self.auto_save_file}")
            else:
                logger.warning("Failed to auto-save mappings")
                
        except Exception as e:
            logger.error(f"Error during auto-save: {e}")
    
    def toggle_reverser_mode(self, mode: str) -> None:
        """Toggle between axis, 2-way, and 3-way switch mode for the reverser
        Args:
            mode: 'axis', '2way', or '3way'
        """
        self.reverser_switch_mode = (mode != 'axis')
        logger.info(f"Reverser mode set to: {mode}")
        # Update the input mapper with the new mode
        self.input_mapper.set_reverser_switch_mode(mode)
        # Update the UI to reflect the current mode
        self.ui_manager.set_reverser_mode(mode)
        # Auto-save the settings change
        self._auto_save_mappings()
    
    def start_application(self) -> None:
        """Start the input processing and UDP communication"""
        if self.running:
            logger.warning("Application already running")
            return
        
        # Validate connection settings
        ip = self.ui_manager.get_ip_address()
        port = self.ui_manager.get_port()
        
        if not ip or port <= 0:
            self.ui_manager.show_message("Error", "Please enter valid IP address and port", "error")
            return
        
        # Check if any devices are enabled
        enabled_devices = self.ui_manager.get_enabled_devices()
        if not enabled_devices:
            self.ui_manager.show_message("Error", "Please enable at least one input device", "error")
            return
        
        # Update connection settings
        self.udp_client.update_connection(ip, port)
        
        # Connect UDP client
        if not self.udp_client.connect():
            self.ui_manager.show_message("Error", "Failed to connect UDP client", "error")
            return
        
        # Start input processing
        self.running = True
        self.start_input_processing()
        
        # Update UI
        self.ui_manager.disable_start_button()
        self.ui_manager.enable_stop_button()
        self.ui_manager.set_mapping_prompt("Application running - inputs are being processed")
        
        logger.info(f"Application started - Connected to {ip}:{port}")
    
    def stop_application(self) -> None:
        """Stop the input processing and UDP communication"""
        if not self.running:
            return
        
        logger.info("Stopping application...")
        
        # Stop input processing
        self.running = False
        self.stop_input_processing()
        
        # Disconnect UDP client
        self.udp_client.disconnect()
        
        # Update UI
        self.ui_manager.enable_start_button()
        self.ui_manager.disable_stop_button()
        self.ui_manager.set_mapping_prompt("Application stopped - Click 'Start' to begin processing inputs")
        
        logger.info("Application stopped")
    
    def start_input_processing(self) -> None:
        """Start input processing timers"""
        try:
            # Start input polling timer
            self.input_timer = PeriodicTimer(
                POLLING_INTERVAL / 1000.0,  # Convert ms to seconds
                self.process_inputs
            )
            self.input_timer.start()
            
            # Start UDP send timer
            self.udp_timer = PeriodicTimer(
                UDP_SEND_INTERVAL / 1000.0,  # Convert ms to seconds
                self.send_pending_commands
            )
            self.udp_timer.start()
            
            logger.info("Input processing started")
        except Exception as e:
            logger.error(f"Failed to start input processing: {e}")
            self.running = False
            raise
    
    def stop_input_processing(self) -> None:
        """Stop input processing timers"""
        try:
            if self.input_timer:
                self.input_timer.stop()
                self.input_timer = None
            
            if self.udp_timer:
                self.udp_timer.stop()
                self.udp_timer = None
            
            # Clear pending commands
            self.pending_commands.clear()
            
            logger.info("Input processing stopped")
        except Exception as e:
            logger.error(f"Error stopping input processing: {e}")
    
    def process_inputs(self) -> None:
        """Process inputs from all enabled devices"""
        if not self.running:
            return

        try:
            # Process inputs from input manager first
            inputs = self.input_manager.process_inputs()
            if not inputs:
                return

            # --- 2-way/3-way reverser switch mode integration ---
            mode = self.ui_manager.get_reverser_mode() if hasattr(self, 'ui_manager') else 'axis'
            if mode in ("2way", "3way"):
                # Build input_state dict: (device_id, input_type, input_index) -> value
                input_state = {}
                for device_id, input_type, input_index, value in inputs:
                    input_state[(device_id, input_type, input_index)] = value
                # Update reverser state from mapped switch inputs
                changed = self.input_mapper.update_reverser_3way_state_from_inputs(input_state)
                # In 2-way mode, always send the packet if state changes or at interval
                send_interval = 0.25 if mode == "2way" else 0.5
                if changed or self.state_tracker.get_state('last_reverser_send_time', 0) < time.time() - send_interval:
                    function_id = self.input_mapper.function_dict.get("Reverser Lever")
                    if function_id:
                        state = getattr(self.input_mapper, 'reverser_state', None)
                        reverser_positions = getattr(self.input_mapper, 'reverser_positions', {
                            "forward": 255,
                            "neutral": 127,
                            "reverse": 0
                        })
                        value = reverser_positions.get(state, 127)
                        self.pending_commands[function_id] = value
                        self.state_tracker.states['last_reverser_send_time'] = time.time()
                        logger.info(f"Queued {mode} reverser command: state={state}, value={value}")

            # --- Combined Throttle/Dyn logic ---
            throttle_mode = self.ui_manager.get_throttle_mode() if hasattr(self, 'ui_manager') else 'separate'
            if throttle_mode in ("toggle", "split"):
                throttle_lever_value = None
                toggle_button_value = None
                # Use the mapping for "Throttle Lever" for all combined modes
                throttle_mapping = self.input_mapper.function_input_map.get("Throttle Lever")
                toggle_mapping = self.input_mapper.function_input_map.get("Throttle/Dyn Toggle")
                
                for device_id, input_type, input_index, value in inputs:
                    if throttle_mapping and (device_id, input_type, input_index) == throttle_mapping:
                        throttle_lever_value = value
                        logger.debug(f"Combined lever input: {value}")
                    if throttle_mode == "toggle" and toggle_mapping and (device_id, input_type, input_index) == toggle_mapping:
                        toggle_button_value = value
                        logger.debug(f"Toggle button input: {value}")
                
                # Update toggle state if needed (detect button press edge)
                if throttle_mode == "toggle" and toggle_button_value is not None:
                    # Convert to boolean for button state
                    current_button_pressed = bool(toggle_button_value)
                    # Toggle on button press (rising edge)
                    if current_button_pressed and not self.last_toggle_button_state:
                        self.combined_toggle_state = not self.combined_toggle_state
                        self.input_mapper.set_combined_toggle_state(self.combined_toggle_state)
                        mode_name = "Dynamic Brake" if self.combined_toggle_state else "Throttle"
                        logger.info(f"Toggle switched to: {mode_name}")
                    self.last_toggle_button_state = current_button_pressed
                
                # Process combined lever
                if throttle_lever_value is not None:
                    # Apply axis reverse setting if configured for "Throttle Lever"
                    reverse_setting = self.ui_manager.get_reverse_axis_setting("Throttle Lever")
                    if reverse_setting:
                        throttle_lever_value = -throttle_lever_value
                        logger.debug(f"Applied axis reverse: value now {throttle_lever_value}")
                    
                    if throttle_mode == "toggle":
                        results = self.input_mapper.process_combined_lever_input(throttle_lever_value, self.combined_toggle_state)
                    else:  # split mode
                        results = self.input_mapper.process_combined_lever_input(throttle_lever_value, False)
                    
                    logger.debug(f"Combined lever results: {results}")
                    for fid, val in results:
                        self.pending_commands[fid] = val
                        logger.debug(f"Queued command: function_id={fid}, value={val}")

            # --- Normal input processing for regular mappings ---
            regular_mappings = self.input_mapper.function_input_map.copy()
            if regular_mappings:
                for device_id, input_type, input_index, value in inputs:
                    for function_name, (mapped_device, mapped_type, mapped_index) in regular_mappings.items():
                        if (device_id == mapped_device and 
                            input_type == mapped_type and 
                            input_index == mapped_index):

                            if function_name == "Reverser Lever" and self.reverser_switch_mode:
                                continue

                            # Skip throttle lever processing if in combined mode (it's handled above)
                            if throttle_mode in ("toggle", "split") and function_name == "Throttle Lever":
                                continue

                            # Skip dyn brake lever processing if in combined mode AND it's the same mapping as throttle lever
                            if (throttle_mode in ("toggle", "split") and 
                                function_name == "Dyn Brake Lever" and 
                                self.input_mapper.function_input_map.get("Throttle Lever") == (mapped_device, mapped_type, mapped_index)):
                                continue

                            if function_name in ["Train Brake Lever", "Independent Brake Lever", "Dyn Brake Lever"] and input_type == "Axis":
                                function_id = self.input_mapper.function_dict.get(function_name)
                                if function_id:
                                    processed_value = self.input_mapper.process_brake_input(function_name, value)
                                    self.pending_commands[function_id] = processed_value
                                    continue

                            changed, processed_value = self.input_mapper.process_input_value(
                                function_name, device_id, input_type, input_index, value, 
                                self.state_tracker.states
                            )

                            if changed:
                                function_id = self.input_mapper.function_dict.get(function_name)
                                if function_id:
                                    self.pending_commands[function_id] = processed_value

                            if input_type == 'Axis' and function_name != "Reverser Lever" or (function_name == "Reverser Lever" and not self.reverser_switch_mode):
                                reverse_setting = self.ui_manager.get_reverse_axis_setting(function_name)
                                self.input_mapper.set_axis_reverse(function_name, reverse_setting)
        except Exception as e:
            logger.error(f"Error processing inputs: {e}")
    
    def send_pending_commands(self) -> None:
        """Send pending UDP commands"""
        if not self.running or not self.pending_commands:
            return
        
        try:
            # Send all pending commands
            for function_id, value in self.pending_commands.items():
                # Determine if audio flag should be used (default to True)
                # This could be customized based on function_id if needed
                use_audio = True

                if self.udp_client.send_command(function_id, value, audio=use_audio):
                    # Log reverser commands at info level for debugging
                    if function_id == self.input_mapper.function_dict.get("Reverser Lever"):
                        logger.info(f"Sent UDP reverser command: function={function_id}, value={value}")
                    else:
                        logger.debug(f"Sent UDP command: function={function_id}, value={value}")
                else:
                    logger.warning(f"Failed to send UDP command: function={function_id}, value={value}")
            
            # Clear pending commands
            self.pending_commands.clear()
            
        except Exception as e:
            logger.error(f"Error sending UDP commands: {e}")
    
    def refresh_devices(self) -> None:
        """Refresh the list of available input devices"""
        try:
            devices = self.input_manager.refresh_devices()
            self.ui_manager.populate_device_list(devices)
            
            # Populate mapping interface with all available functions
            all_functions = [name for name, _ in FunctionMapping.FUNCTIONS]
            self.ui_manager.populate_mapping_interface(all_functions)
            
            # Update mapping displays
            self.update_mapping_displays()
            
            # Log detailed device information
            if devices:
                logger.info(f"Refreshed devices - Found {len(devices)} devices")
                thrustmaster_count = sum(1 for device in devices if any(tm in device.name.lower() 
                                                                       for tm in ['thrustmaster', 'tm ', 't16000', 'twcs', 'hotas']))
                if thrustmaster_count > 0:
                    logger.info(f"Found {thrustmaster_count} Thrustmaster device(s)")
                else:
                    logger.info("No Thrustmaster devices detected")
            else:
                logger.warning("No devices detected after refresh")
                
        except Exception as e:
            logger.error(f"Error refreshing devices: {e}")
            self.ui_manager.show_message("Error", f"Failed to refresh devices: {e}", "error")
    
    def force_refresh_devices(self) -> None:
        """Force a complete device refresh (more aggressive)"""
        try:
            logger.info("Performing force device refresh...")
            devices = self.input_manager.force_device_refresh()
            self.ui_manager.populate_device_list(devices)
            
            # Populate mapping interface with all available functions
            all_functions = [name for name, _ in FunctionMapping.FUNCTIONS]
            self.ui_manager.populate_mapping_interface(all_functions)
            
            # Update mapping displays
            self.update_mapping_displays()
            
            # Show result message
            if devices:
                thrustmaster_devices = [device for device in devices if any(tm in device.name.lower() 
                                                                           for tm in ['thrustmaster', 'tm ', 't16000', 'twcs', 'hotas'])]
                if thrustmaster_devices:
                    self.ui_manager.show_message("Success", 
                                                f"Force refresh completed! Found {len(thrustmaster_devices)} Thrustmaster device(s):\n" +
                                                "\n".join(f"• {device.name}" for device in thrustmaster_devices),
                                                "info")
                else:
                    self.ui_manager.show_message("Info", 
                                                f"Force refresh completed. Found {len(devices)} device(s) but no Thrustmaster devices detected.",
                                                "info")
            else:
                self.ui_manager.show_message("Warning", 
                                            "Force refresh completed but no devices were detected.\n\n" +
                                            "Please check:\n" +
                                            "• Device is properly connected\n" +
                                            "• Device drivers are installed\n" +
                                            "• Device appears in Windows Device Manager",
                                            "warning")
                
            logger.info(f"Force refresh completed - Found {len(devices)} devices")
            
        except Exception as e:
            logger.error(f"Error during force refresh: {e}")
            self.ui_manager.show_message("Error", f"Force refresh failed: {e}", "error")
    
    def on_device_toggle(self, device_index: int) -> None:
        """Handle device enable/disable toggle"""
        try:
            enabled = self.ui_manager.get_enabled_devices()
            
            if device_index in enabled:
                if self.input_manager.enable_device(device_index):
                    logger.info(f"Enabled device {device_index}")
                else:
                    logger.warning(f"Failed to enable device {device_index}")
                    self.ui_manager.set_device_enabled(device_index, False)
            else:
                if self.input_manager.disable_device(device_index):
                    logger.info(f"Disabled device {device_index}")
                else:
                    logger.warning(f"Failed to disable device {device_index}")
                    
        except Exception as e:
            logger.error(f"Error toggling device {device_index}: {e}")
    
    def map_input(self, function_name: str) -> None:
        """Start input mapping for a specific function or reverser 3-way position"""
        if self.running:
            self.ui_manager.show_message("Info", "Please stop the application before mapping inputs", "info")
            return
        if self.waiting_for_input:
            self.ui_manager.show_message("Info", "Already waiting for input - please provide input or wait for timeout", "info")
            return
        enabled_devices = self.ui_manager.get_enabled_devices()
        if not enabled_devices:
            self.ui_manager.show_message("Error", "Please enable at least one input device", "error")
            return
        
        # Check if input detection is already active to prevent rapid successive mapping
        if hasattr(self.input_manager, 'detection_active') and self.input_manager.detection_active:
            self.ui_manager.show_message("Info", "Input detection already in progress. Please wait for it to complete.", "info")
            return
            
        self.waiting_for_input = True
        self.input_target_function = function_name
        # Special prompt for reverser 3-way
        if function_name.startswith("Reverser 3way "):
            pos = function_name.split(" ")[-1].capitalize()
            self.ui_manager.set_mapping_prompt(f"Press the button/switch for 'Reverser {pos}' (5 second timeout)...")
        elif function_name == "Reverser Lever" and self.reverser_switch_mode:
            self.ui_manager.set_mapping_prompt(f"Press the button/switch for '{function_name}' in 3-position switch mode (5 second timeout)...")
        else:
            self.ui_manager.set_mapping_prompt(f"Ready - now move/press the input for '{function_name}' (5 second timeout)...")
        detection_thread = threading.Thread(target=lambda: self._detect_input_thread_with_validation(function_name))
        detection_thread.daemon = True
        detection_thread.start()
    

    def _detect_input_thread_with_validation(self, function_name: str) -> None:
        """Thread function for input detection with input type validation"""
        try:
            detected_input = self.input_manager.detect_input(timeout=5.0)
            if detected_input and self.input_target_function:
                device_id, detected_input_type, input_index = detected_input
                # Determine required input type for this function
                from config import FunctionMapping
                required_type = FunctionMapping.INPUT_TYPES.get(function_name, 'toggle')
                # Normalize input types for comparison
                detected_type_norm = detected_input_type.lower()
                required_type_norm = required_type.lower()
                # Validation logic
                valid = True
                error_msg = None
                # For reverser 3way, only allow Button
                if function_name.startswith("Reverser 3way "):
                    if detected_type_norm != 'button':
                        valid = False
                        error_msg = "Reverser 3-way positions can only be mapped to buttons/switches. Please try again with a button input."
                # For lever/axis functions, only allow Axis
                elif required_type_norm == 'lever':
                    if detected_type_norm != 'axis':
                        valid = False
                        error_msg = f"'{function_name}' can only be mapped to an axis/lever input. Please try again with an axis input."
                # For momentary/toggle, only allow Button
                elif required_type_norm in ('momentary', 'toggle'):
                    if detected_type_norm != 'button':
                        valid = False
                        error_msg = f"'{function_name}' can only be mapped to a button/switch input. Please try again with a button input."
                # For 3way/4way, only allow Button
                elif required_type_norm in ('3way', '4way'):
                    if detected_type_norm != 'button':
                        valid = False
                        error_msg = f"'{function_name}' can only be mapped to a button/switch input. Please try again with a button input."
                if not valid:
                    self.ui_manager.show_message("Invalid Input Type", error_msg or "Incompatible input type.", "error")
                    self.ui_manager.set_mapping_prompt("Mapping cancelled: incompatible input type.")
                    return
                # --- Existing logic follows ---
                if function_name.startswith("Reverser 3way "):
                    pos = function_name.split(" ")[-1]
                    self.input_mapper.set_reverser_3way_mapping(pos, device_id, detected_input_type, input_index)
                    display_text = format_input_display(device_id, detected_input_type, input_index)
                    self.ui_manager.update_mapping_display(function_name, display_text)
                    self.ui_manager.set_mapping_prompt(f"Successfully mapped 'Reverser {pos.capitalize()}' to {display_text}")
                    logger.info(f"Mapped Reverser 3way {pos} to {display_text}")
                    # Auto-save the new mapping
                    self._auto_save_mappings()
                else:
                    existing_func = self.input_mapper.find_existing_mapping(device_id, detected_input_type, input_index)
                    if existing_func and existing_func != function_name:
                        msg = (f"This input is already mapped to '{existing_func}'.\n\n"
                               "Do you want to cancel, clear the other mapping, or keep both?")
                        choice = self.ui_manager.show_message(
                            "Input Already Mapped",
                            msg,
                            msg_type="question_with_options"
                        )
                        if choice == 'cancel':
                            self.ui_manager.set_mapping_prompt("Mapping cancelled by user.")
                            return
                        elif choice == 'clear':
                            self.input_mapper.remove_mapping(existing_func)
                            self.ui_manager.update_mapping_display(existing_func, "Not mapped")
                            logger.info(f"Cleared mapping for {existing_func} to allow remapping.")
                        # else: keep both (fall through)
                    if self.input_mapper.add_mapping(function_name, device_id, detected_input_type, input_index):
                        display_text = format_input_display(device_id, detected_input_type, input_index)
                        self.ui_manager.update_mapping_display(function_name, display_text)
                        self.ui_manager.set_mapping_prompt(f"Successfully mapped '{function_name}' to {display_text}")
                        logger.info(f"Mapped {function_name} to {display_text}")
                        # Auto-save the new mapping
                        self._auto_save_mappings()
                    else:
                        self.ui_manager.set_mapping_prompt(f"Failed to map '{function_name}'")
                        logger.error(f"Failed to map {function_name}")
            else:
                self.ui_manager.set_mapping_prompt("No input detected - timeout reached")
                logger.info("Input detection timed out")
        except Exception as e:
            logger.error(f"Error during input detection: {e}")
            self.ui_manager.set_mapping_prompt(f"Error during input detection: {e}")
        finally:
            self.waiting_for_input = False
            self.input_target_function = None
    
    def clear_mapping(self, function_name: str) -> None:
        """Clear mapping for a specific function"""
        if self.input_mapper.remove_mapping(function_name):
            self.ui_manager.update_mapping_display(function_name, "Not mapped")
            logger.info(f"Cleared mapping for {function_name}")
            # Auto-save the change
            self._auto_save_mappings()
        else:
            logger.warning(f"No mapping found for {function_name}")
    
    def load_mappings(self, file_path: Optional[str] = None) -> None:
        """Load mappings from file"""
        try:
            if self.input_mapper.load_mappings_from_csv(file_path):
                # Get the reverser mode from the input mapper after loading
                # The input mapper now loads the mode correctly from the CSV
                if self.input_mapper.reverser_switch_mode:
                    if getattr(self.input_mapper, 'reverser_two_input_mode', False):
                        mode = '2way'
                    else:
                        mode = '3way'
                else:
                    mode = 'axis'
                    
                # Sync the mode with main.py's state
                self.reverser_switch_mode = (mode != 'axis')
                
                # Update the UI to reflect the loaded mode
                self.ui_manager.set_reverser_mode(mode)
                
                # Update the input mapper to ensure consistency
                self.input_mapper.set_reverser_switch_mode(mode)
                
                # Update mapping displays
                self.update_mapping_displays()
                
                # Show success message
                if file_path == self.auto_save_file:
                    # This is loading persistent mappings
                    self.ui_manager.set_mapping_prompt("Persistent mappings loaded successfully")
                    logger.info(f"Persistent mappings loaded successfully (reverser mode: {mode})")
                elif file_path:
                    # This is a manual load from a specific file
                    self.ui_manager.set_mapping_prompt(f"Mappings loaded from {file_path}")
                    logger.info(f"Mappings loaded from {file_path} (reverser mode: {mode})")
                else:
                    # This is loading default/empty mappings
                    self.ui_manager.set_mapping_prompt("Default mappings loaded successfully")
                    logger.info(f"Default mappings loaded successfully (reverser mode: {mode})")
            else:
                if file_path:
                    self.ui_manager.set_mapping_prompt(f"No mappings found in {file_path}")
                    logger.info(f"No mappings found in {file_path}")
                else:
                    self.ui_manager.set_mapping_prompt("No saved mappings found")
                    logger.info("No saved mappings found")
        except Exception as e:
            logger.error(f"Error loading mappings: {e}")
            self.ui_manager.show_message("Error", f"Failed to load mappings: {e}", "error")
    
    def save_mappings(self, file_path: Optional[str] = None) -> None:
        """Save mappings to file (for manual save/load of different configurations)"""
        try:
            # Update reverse axis settings from UI
            for function_name in self.input_mapper.get_mapped_functions():
                if function_name == "Reverser Lever" and self.reverser_switch_mode:
                    # Skip reverse axis setting for reverser in switch mode
                    continue
                    
                reverse_setting = self.ui_manager.get_reverse_axis_setting(function_name)
                self.input_mapper.set_axis_reverse(function_name, reverse_setting)
            
            # Ensure the input mapper has the correct reverser mode before saving
            # Convert boolean reverser_switch_mode to proper string mode
            if self.reverser_switch_mode:
                # Determine if it's 2way or 3way mode
                if getattr(self.input_mapper, 'reverser_two_input_mode', False):
                    mode = '2way'
                else:
                    mode = '3way'
            else:
                mode = 'axis'
            
            # Set the mode in the input mapper to ensure consistency
            self.input_mapper.set_reverser_switch_mode(mode)
            
            # Validate mappings before saving
            if not self.input_mapper.validate_mappings():
                logger.warning("Mapping validation found issues, but proceeding with save")
            
            # Perform the save
            if self.input_mapper.save_mappings(file_path):
                if file_path:
                    self.ui_manager.set_mapping_prompt(f"Mappings saved to {file_path}")
                    logger.info(f"Mappings saved to {file_path} (reverser mode: {mode})")
                else:
                    # This is a save to the default location - also trigger auto-save
                    self.ui_manager.set_mapping_prompt("Mappings saved successfully")
                    logger.info(f"Mappings saved successfully (reverser mode: {mode})")
                    # Update the persistent mappings as well
                    self._auto_save_mappings()
            else:
                self.ui_manager.set_mapping_prompt("Failed to save mappings")
                logger.error("Failed to save mappings")
        except Exception as e:
            logger.error(f"Error saving mappings: {e}")
            self.ui_manager.show_message("Error", f"Failed to save mappings: {e}", "error")
    
    def clear_mappings(self) -> None:
        """Clear all mappings"""
        if self.ui_manager.ask_yes_no("Confirm", "Are you sure you want to clear all mappings?"):
            self.input_mapper.clear_all_mappings()
            self.update_mapping_displays()
            self.ui_manager.set_mapping_prompt("All mappings cleared")
            logger.info("All mappings cleared")
            # Auto-save the cleared state
            self._auto_save_mappings()
    
    def update_mapping_displays(self) -> None:
        """Update all mapping displays in the UI"""
        try:
            mappings = self.input_mapper.get_all_mappings()
            logger.info(f"Updating UI displays with {len(mappings)} mappings: {mappings}")
            
            # Update each function's display
            for function_name, _ in FunctionMapping.FUNCTIONS:
                if function_name in mappings:
                    device_id, input_type, input_index = mappings[function_name]
                    display_text = format_input_display(device_id, input_type, input_index)
                    self.ui_manager.update_mapping_display(function_name, display_text)
                    logger.debug(f"Updated display for {function_name}: {display_text}")
                    
                    # Update reverse axis setting
                    reverse_setting = self.input_mapper.get_axis_reverse(function_name)
                    self.ui_manager.set_reverse_axis_setting(function_name, reverse_setting)
                else:
                    self.ui_manager.update_mapping_display(function_name, "Not mapped")
            
            # Update reverser 3-way mappings if they exist
            if hasattr(self.input_mapper, 'reverser_3way_mappings') and self.input_mapper.reverser_3way_mappings:
                for pos in ['forward', 'neutral', 'reverse']:
                    reverser_function_name = f"Reverser 3way {pos}"
                    if pos in self.input_mapper.reverser_3way_mappings:
                        device_id, input_type, input_index = self.input_mapper.reverser_3way_mappings[pos]
                        display_text = format_input_display(device_id, input_type, input_index)
                        self.ui_manager.update_mapping_display(reverser_function_name, display_text)
                        logger.debug(f"Updated reverser 3-way display: {reverser_function_name} -> {display_text}")
                    else:
                        self.ui_manager.update_mapping_display(reverser_function_name, "Not mapped")
            else:
                # Clear reverser 3-way displays if no mappings exist
                for pos in ['forward', 'neutral', 'reverse']:
                    reverser_function_name = f"Reverser 3way {pos}"
                    self.ui_manager.update_mapping_display(reverser_function_name, "Not mapped")
                    
        except Exception as e:
            logger.error(f"Error updating mapping displays: {e}")
    
    def on_closing(self) -> None:
        """Handle application closing"""
        logger.info("Application closing...")
        
        # Stop application if running
        if self.running:
            self.stop_application()
        
        # Auto-save current mappings before closing
        self._auto_save_mappings()
        
        # Cleanup resources
        try:
            self.input_manager.cleanup()
            self.udp_client.disconnect()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        # Destroy the main window
        self.root.destroy()
        logger.info("Application closed")
    
    def run(self) -> None:
        """Run the main application loop"""
        try:
            logger.info("Starting main application loop")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise
        finally:
            logger.info("Main application loop ended")
    
    def cancel_input_mapping(self) -> None:
        """Cancel ongoing input mapping"""
        if self.waiting_for_input:
            if hasattr(self.input_manager, 'cancel_input_detection'):
                if self.input_manager.cancel_input_detection():
                    self.ui_manager.set_mapping_prompt("Input mapping cancelled by user")
                    self.waiting_for_input = False
                    self.input_target_function = None
                    logger.info("Input mapping cancelled by user")
                else:
                    self.ui_manager.set_mapping_prompt("No active input detection to cancel")
            else:
                # Fallback for older version
                self.waiting_for_input = False
                self.input_target_function = None
                self.ui_manager.set_mapping_prompt("Input mapping cancelled by user")
                logger.info("Input mapping cancelled by user (fallback)")
        else:
            self.ui_manager.set_mapping_prompt("No active input mapping to cancel")


def main():
    """Main entry point"""
    try:
        app = Run8ControlConductor()
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
