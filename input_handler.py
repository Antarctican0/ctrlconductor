"""
Input handling module for Run8 Control Conductor

Handles joystick/gamepad device detection, management, and input processing.
"""

import pygame
import time
from typing import Dict, List, Tuple, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Input detection constants
DEADZONE = 0.7
RELEASE_TIMEOUT = 0.15


class InputDevice:
    """Represents a connected input device"""
    
    def __init__(self, device_id: int, name: str, joystick: pygame.joystick.JoystickType):
        """
        Initialize input device
        
        Args:
            device_id: Device ID
            name: Device name
            joystick: Pygame joystick object
        """
        self.device_id = device_id
        self.name = name
        self.joystick = joystick
        self.enabled = False
        
    def enable(self) -> bool:
        """Enable the device"""
        try:
            if not self.joystick.get_init():
                self.joystick.init()
            self.enabled = True
            logger.info(f"Enabled device: {self.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to enable device {self.name}: {e}")
            return False
    
    def disable(self) -> None:
        """Disable the device"""
        try:
            if self.joystick.get_init():
                self.joystick.quit()
            self.enabled = False
            logger.info(f"Disabled device: {self.name}")
        except Exception as e:
            logger.error(f"Failed to disable device {self.name}: {e}")
    
    def get_button_count(self) -> int:
        """Get number of buttons"""
        return self.joystick.get_numbuttons()
    
    def get_axis_count(self) -> int:
        """Get number of axes"""
        return self.joystick.get_numaxes()
    
    def get_hat_count(self) -> int:
        """Get number of hats"""
        return self.joystick.get_numhats()


class InputManager:
    """Manages input devices and input detection"""
    
    def __init__(self):
        """Initialize the input manager"""
        self.devices: Dict[int, InputDevice] = {}
        self.enabled_devices: List[int] = []
        self.input_states: Dict[Tuple, Any] = {}
        self.last_input_time = 0
        self.waiting_for_input = False
        self.input_detected_callback = None
        
        # Initialize pygame
        try:
            pygame.init()
            pygame.joystick.init()
            logger.info("Pygame initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pygame: {e}")
    
    def refresh_devices(self) -> List[InputDevice]:
        """
        Refresh the list of available input devices
        
        Returns:
            List of available input devices
        """
        try:
            pygame.joystick.quit()
            pygame.joystick.init()
            
            # Clear existing devices
            for device in self.devices.values():
                device.disable()
            self.devices.clear()
            
            # Detect new devices
            device_count = pygame.joystick.get_count()
            logger.info(f"Found {device_count} input devices")
            
            for i in range(device_count):
                try:
                    joystick = pygame.joystick.Joystick(i)
                    device = InputDevice(i, joystick.get_name(), joystick)
                    self.devices[i] = device
                    logger.info(f"Detected device {i}: {device.name}")
                except Exception as e:
                    logger.error(f"Failed to initialize device {i}: {e}")
            
            return list(self.devices.values())
        except Exception as e:
            logger.error(f"Failed to refresh devices: {e}")
            return []
    
    def enable_device(self, device_id: int) -> bool:
        """Enable a specific device"""
        if device_id in self.devices:
            if self.devices[device_id].enable():
                if device_id not in self.enabled_devices:
                    self.enabled_devices.append(device_id)
                return True
        return False
    
    def disable_device(self, device_id: int) -> bool:
        """Disable a specific device"""
        if device_id in self.devices:
            self.devices[device_id].disable()
            if device_id in self.enabled_devices:
                self.enabled_devices.remove(device_id)
            return True
        return False
    
    def get_enabled_devices(self) -> List[InputDevice]:
        """Get list of enabled devices"""
        return [self.devices[device_id] for device_id in self.enabled_devices 
                if device_id in self.devices]
    
    def detect_input(self, timeout: float = 5.0) -> Optional[Tuple[int, str, int]]:
        """
        Detect input from enabled devices
        
        Args:
            timeout: Maximum time to wait for input (seconds)
            
        Returns:
            Tuple of (device_id, input_type, input_index) or None if no input
        """
        if not self.enabled_devices:
            return None
        
        self.waiting_for_input = True
        start_time = time.time()
        
        # Store initial states
        initial_states = {}
        for device_id in self.enabled_devices:
            if device_id not in self.devices:
                continue
            device = self.devices[device_id]
            if not device.enabled:
                continue
            
            initial_states[device_id] = {
                'buttons': [device.joystick.get_button(i) for i in range(device.get_button_count())],
                'axes': [device.joystick.get_axis(i) for i in range(device.get_axis_count())],
                'hats': [device.joystick.get_hat(i) for i in range(device.get_hat_count())]
            }
        
        try:
            # Store baseline states after a brief settling period
            baseline_states = {}
            movement_detected = {}
            
            # Initialize movement tracking
            for device_id in self.enabled_devices:
                if device_id not in self.devices:
                    continue
                device = self.devices[device_id]
                if not device.enabled:
                    continue
                
                movement_detected[device_id] = {}
                for i in range(device.get_axis_count()):
                    movement_detected[device_id][f'axis_{i}'] = False
            
            # Brief delay to let user prepare
            time.sleep(0.3)
            
            # Establish baseline after delay
            for device_id in self.enabled_devices:
                if device_id not in self.devices:
                    continue
                device = self.devices[device_id]
                if not device.enabled:
                    continue
                
                pygame.event.pump()
                baseline_states[device_id] = {
                    'buttons': [device.joystick.get_button(i) for i in range(device.get_button_count())],
                    'axes': [device.joystick.get_axis(i) for i in range(device.get_axis_count())],
                    'hats': [device.joystick.get_hat(i) for i in range(device.get_hat_count())]
                }
            
            detection_start = time.time()
            while time.time() - detection_start < (timeout - 0.3):  # Account for initial delay
                pygame.event.pump()
                
                for device_id in self.enabled_devices:
                    if device_id not in self.devices:
                        continue
                    device = self.devices[device_id]
                    if not device.enabled:
                        continue
                    
                    # Check buttons (immediate response)
                    for i in range(device.get_button_count()):
                        current = device.joystick.get_button(i)
                        baseline = baseline_states[device_id]['buttons'][i]
                        if current and not baseline:
                            return (device_id, 'Button', i)
                    
                    # Check axes with movement confirmation
                    for i in range(device.get_axis_count()):
                        current = device.joystick.get_axis(i)
                        baseline = baseline_states[device_id]['axes'][i]
                        movement_key = f'axis_{i}'
                        
                        # Detect significant movement
                        movement = abs(current - baseline)
                        if movement > DEADZONE:
                            if not movement_detected[device_id][movement_key]:
                                # First time detecting movement on this axis
                                movement_detected[device_id][movement_key] = True
                                # Wait a bit to confirm sustained movement
                                time.sleep(0.15)
                                pygame.event.pump()
                                confirmed = device.joystick.get_axis(i)
                                # Check if movement is still significant
                                if abs(confirmed - baseline) > DEADZONE * 0.7:  # Slightly lower threshold for confirmation
                                    return (device_id, 'Axis', i)
                                else:
                                    # False alarm, reset detection for this axis
                                    movement_detected[device_id][movement_key] = False
                        else:
                            # No significant movement, reset detection
                            movement_detected[device_id][movement_key] = False
                    
                    # Check hats (immediate response)
                    for i in range(device.get_hat_count()):
                        current = device.joystick.get_hat(i)
                        baseline = baseline_states[device_id]['hats'][i]
                        if current != baseline and current != (0, 0):
                            return (device_id, 'Hat', i)
                
                time.sleep(0.02)  # Small delay to prevent excessive CPU usage
                
        except Exception as e:
            logger.error(f"Error during input detection: {e}")
        finally:
            self.waiting_for_input = False
        
        return None
    
    def process_inputs(self) -> List[Tuple[int, str, int, Any]]:
        """
        Process all inputs from enabled devices
        
        Returns:
            List of (device_id, input_type, input_index, value) tuples
        """
        if not self.enabled_devices:
            return []
        
        inputs = []
        
        try:
            pygame.event.pump()
            
            for device_id in self.enabled_devices:
                if device_id not in self.devices:
                    continue
                device = self.devices[device_id]
                if not device.enabled:
                    continue
                
                # Process buttons
                for i in range(device.get_button_count()):
                    value = device.joystick.get_button(i)
                    key = (device_id, 'Button', i)
                    if key not in self.input_states or self.input_states[key] != value:
                        self.input_states[key] = value
                        inputs.append((device_id, 'Button', i, value))
                
                # Process axes
                for i in range(device.get_axis_count()):
                    value = device.joystick.get_axis(i)
                    key = (device_id, 'Axis', i)
                    if key not in self.input_states or abs(self.input_states[key] - value) > 0.01:
                        self.input_states[key] = value
                        inputs.append((device_id, 'Axis', i, value))
                
                # Process hats
                for i in range(device.get_hat_count()):
                    value = device.joystick.get_hat(i)
                    key = (device_id, 'Hat', i)
                    if key not in self.input_states or self.input_states[key] != value:
                        self.input_states[key] = value
                        inputs.append((device_id, 'Hat', i, value))
                        
        except Exception as e:
            logger.error(f"Error processing inputs: {e}")
        
        return inputs
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            for device in self.devices.values():
                device.disable()
            pygame.joystick.quit()
            pygame.quit()
            logger.info("Input manager cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
