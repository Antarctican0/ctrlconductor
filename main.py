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
        
        # Setup UI callbacks
        self._setup_ui_callbacks()
        
        # Initialize with default values
        self.ui_manager.set_ip_address(DEFAULT_IP)
        self.ui_manager.set_port(DEFAULT_PORT)
        
        # Load saved mappings and refresh devices
        self.load_mappings()
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
    
    def toggle_reverser_mode(self, switch_mode: bool) -> None:
        """Toggle between axis and 3-position switch mode for the reverser
        
        Args:
            switch_mode: True for 3-position switch mode, False for axis mode
        """
        self.reverser_switch_mode = switch_mode
        logger.info(f"Reverser mode set to: {'3-position switch' if switch_mode else 'axis'}")
        
        # Update the input mapper with the new mode
        self.input_mapper.set_reverser_switch_mode(switch_mode)
        
        # Update the UI to reflect the current mode
        self.ui_manager.set_reverser_mode(switch_mode)
    
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
            # Get current mappings
            mappings = self.input_mapper.get_all_mappings()
            if not mappings:
                return
            
            # Process inputs from input manager
            inputs = self.input_manager.process_inputs()
            
            for device_id, input_type, input_index, value in inputs:
                # Find functions mapped to this input
                for function_name, (mapped_device, mapped_type, mapped_index) in mappings.items():
                    if (device_id == mapped_device and 
                        input_type == mapped_type and 
                        input_index == mapped_index):
                        
                        # Special handling for reverser in switch mode
                        if function_name == "Reverser Lever" and self.reverser_switch_mode and input_type == "Button":
                            # Handle reverser as a 3-position switch
                            # For buttons, use different buttons for forward/neutral/reverse
                            # or process a hat switch/POV hat directional input
                            changed, processed_value = self.input_mapper.process_reverser_switch_input(
                                device_id, input_type, input_index, value, 
                                self.state_tracker.states
                            )
                        else:
                            # Normal input processing for all other functions
                            changed, processed_value = self.input_mapper.process_input_value(
                                function_name, device_id, input_type, input_index, value, 
                                self.state_tracker.states
                            )
                        
                        if changed:
                            # Get the Run8 function ID
                            function_id = self.input_mapper.function_dict.get(function_name)
                            if function_id:
                                # Queue the command for sending
                                self.pending_commands[function_id] = processed_value
                                logger.debug(f"Queued command: {function_name} ({function_id}) = {processed_value}")
                        
                        # Update reverse axis settings from UI
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
                if self.udp_client.send_command(function_id, value):
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
            
            logger.info(f"Refreshed devices - Found {len(devices)} devices")
        except Exception as e:
            logger.error(f"Error refreshing devices: {e}")
            self.ui_manager.show_message("Error", f"Failed to refresh devices: {e}", "error")
    
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
        """Start input mapping for a specific function"""
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
        
        self.waiting_for_input = True
        self.input_target_function = function_name
        
        # Special prompt for reverser in switch mode
        if function_name == "Reverser Lever" and self.reverser_switch_mode:
            self.ui_manager.set_mapping_prompt(f"Press the button/switch for '{function_name}' in 3-position switch mode (5 second timeout)...")
        else:
            self.ui_manager.set_mapping_prompt(f"Ready - now move/press the input for '{function_name}' (5 second timeout)...")
        
        # Start input detection in a separate thread
        detection_thread = threading.Thread(target=self._detect_input_thread)
        detection_thread.daemon = True
        detection_thread.start()
    
    def _detect_input_thread(self) -> None:
        """Thread function for input detection"""
        try:
            detected_input = self.input_manager.detect_input(timeout=5.0)
            
            if detected_input and self.input_target_function:
                device_id, input_type, input_index = detected_input
                
                # Add the mapping
                if self.input_mapper.add_mapping(self.input_target_function, device_id, input_type, input_index):
                    # Update UI display
                    display_text = format_input_display(device_id, input_type, input_index)
                    self.ui_manager.update_mapping_display(self.input_target_function, display_text)
                    
                    self.ui_manager.set_mapping_prompt(f"Successfully mapped '{self.input_target_function}' to {display_text}")
                    logger.info(f"Mapped {self.input_target_function} to {display_text}")
                else:
                    self.ui_manager.set_mapping_prompt(f"Failed to map '{self.input_target_function}'")
                    logger.error(f"Failed to map {self.input_target_function}")
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
        else:
            logger.warning(f"No mapping found for {function_name}")
    
    def load_mappings(self, file_path: Optional[str] = None) -> None:
        """Load mappings from file"""
        try:
            if self.input_mapper.load_mappings_from_csv(file_path):
                # Get the reverser mode from the input mapper
                self.reverser_switch_mode = self.input_mapper.get_reverser_switch_mode()
                # Update UI with the loaded reverser mode
                self.ui_manager.set_reverser_mode(self.reverser_switch_mode)
                
                self.update_mapping_displays()
                if file_path:
                    self.ui_manager.set_mapping_prompt(f"Mappings loaded from {file_path}")
                    logger.info(f"Mappings loaded from {file_path}")
                else:
                    self.ui_manager.set_mapping_prompt("Default mappings loaded successfully")
                    logger.info("Default mappings loaded successfully")
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
        """Save mappings to file"""
        try:
            # Update reverse axis settings from UI
            for function_name in self.input_mapper.get_mapped_functions():
                if function_name == "Reverser Lever" and self.reverser_switch_mode:
                    # Skip reverse axis setting for reverser in switch mode
                    continue
                    
                reverse_setting = self.ui_manager.get_reverse_axis_setting(function_name)
                self.input_mapper.set_axis_reverse(function_name, reverse_setting)
            
            # Save the current reverser mode
            self.input_mapper.set_reverser_switch_mode(self.reverser_switch_mode)
            
            if self.input_mapper.save_mappings(file_path):
                if file_path:
                    self.ui_manager.set_mapping_prompt(f"Mappings saved to {file_path}")
                    logger.info(f"Mappings saved to {file_path}")
                else:
                    self.ui_manager.set_mapping_prompt("Mappings saved successfully")
                    logger.info("Mappings saved successfully")
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
    
    def update_mapping_displays(self) -> None:
        """Update all mapping displays in the UI"""
        try:
            mappings = self.input_mapper.get_all_mappings()
            
            # Update each function's display
            for function_name, _ in FunctionMapping.FUNCTIONS:
                if function_name in mappings:
                    device_id, input_type, input_index = mappings[function_name]
                    display_text = format_input_display(device_id, input_type, input_index)
                    self.ui_manager.update_mapping_display(function_name, display_text)
                    
                    # Update reverse axis setting
                    reverse_setting = self.input_mapper.get_axis_reverse(function_name)
                    self.ui_manager.set_reverse_axis_setting(function_name, reverse_setting)
                else:
                    self.ui_manager.update_mapping_display(function_name, "Not mapped")
                    
        except Exception as e:
            logger.error(f"Error updating mapping displays: {e}")
    
    def on_closing(self) -> None:
        """Handle application closing"""
        logger.info("Application closing...")
        
        # Stop application if running
        if self.running:
            self.stop_application()
        
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
