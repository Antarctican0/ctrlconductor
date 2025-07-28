"""
Input handling module for Run8 Control Conductor

Handles joystick/gamepad device detection, management, and input processing.
"""

import pygame
import time
import threading
from typing import Dict, List, Tuple, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Input detection constants
DEADZONE = 0.7
RELEASE_TIMEOUT = 0.15


class InputDevice:
    """Represents a connected input device with enhanced Thrustmaster support"""
    
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
        self.is_thrustmaster = self._detect_thrustmaster()
        self._cached_info = None
        
    def _detect_thrustmaster(self) -> bool:
        """Detect if this is a Thrustmaster device"""
        name_lower = self.name.lower()
        thrustmaster_indicators = [
            'thrustmaster', 'tm ', 't16000', 'twcs', 'hotas', 
            'warthog', 'cougar', 'f16c', 'f18c', 'pendular'
        ]
        return any(indicator in name_lower for indicator in thrustmaster_indicators)
        
    def enable(self) -> bool:
        """Enable the device with enhanced error handling"""
        try:
            if self.enabled:
                logger.debug(f"Device {self.name} already enabled")
                return True
                
            if not self.joystick.get_init():
                logger.debug(f"Initializing joystick for {self.name}")
                self.joystick.init()
                
                # Cache device info after successful initialization
                self._cache_device_info()
                
            self.enabled = True
            
            # Special handling for Thrustmaster devices
            if self.is_thrustmaster:
                logger.info(f"✓ Enabled Thrustmaster device: {self.name}")
                logger.debug(f"  Buttons: {self.get_button_count()}, Axes: {self.get_axis_count()}, Hats: {self.get_hat_count()}")
            else:
                logger.info(f"✓ Enabled device: {self.name}")
                
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to enable device {self.name}: {e}")
            if self.is_thrustmaster:
                logger.error("Thrustmaster device enable failed - check drivers and USB connection")
            return False
    
    def disable(self) -> None:
        """Disable the device with enhanced error handling"""
        try:
            if not self.enabled:
                logger.debug(f"Device {self.name} already disabled")
                return
                
            if self.joystick.get_init():
                self.joystick.quit()
                
            self.enabled = False
            
            if self.is_thrustmaster:
                logger.info(f"✓ Disabled Thrustmaster device: {self.name}")
            else:
                logger.info(f"✓ Disabled device: {self.name}")
                
        except Exception as e:
            logger.error(f"✗ Failed to disable device {self.name}: {e}")
    
    def _cache_device_info(self) -> None:
        """Cache device information for performance"""
        try:
            if self.joystick.get_init():
                self._cached_info = {
                    'buttons': self.joystick.get_numbuttons(),
                    'axes': self.joystick.get_numaxes(),
                    'hats': self.joystick.get_numhats()
                }
        except Exception as e:
            logger.debug(f"Could not cache info for {self.name}: {e}")
            self._cached_info = None
    
    def get_button_count(self) -> int:
        """Get number of buttons"""
        try:
            if self._cached_info:
                return self._cached_info['buttons']
            return self.joystick.get_numbuttons()
        except Exception:
            return 0
    
    def get_axis_count(self) -> int:
        """Get number of axes"""
        try:
            if self._cached_info:
                return self._cached_info['axes']
            return self.joystick.get_numaxes()
        except Exception:
            return 0
    
    def get_hat_count(self) -> int:
        """Get number of hats"""
        try:
            if self._cached_info:
                return self._cached_info['hats']
            return self.joystick.get_numhats()
        except Exception:
            return 0


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
        self.detection_lock = threading.Lock()
        self.detection_active = False
        
        # Initialize pygame
        try:
            pygame.init()
            pygame.joystick.init()
            logger.info("Pygame initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pygame: {e}")
    
    def refresh_devices(self) -> List[InputDevice]:
        """
        Refresh the list of available input devices with enhanced debugging
        
        Returns:
            List of available input devices
        """
        try:
            # Reinitialize pygame joystick subsystem
            pygame.joystick.quit()
            time.sleep(0.1)  # Brief pause to allow cleanup
            pygame.joystick.init()
            
            # Clear existing devices
            for device in self.devices.values():
                device.disable()
            self.devices.clear()
            
            # Detect new devices with enhanced logging
            device_count = pygame.joystick.get_count()
            logger.info(f"Pygame detected {device_count} input device(s)")
            
            if device_count == 0:
                logger.warning("No input devices detected by pygame")
                logger.info("Troubleshooting tips:")
                logger.info("1. Ensure devices are properly connected")
                logger.info("2. Check Windows Device Manager for device status")
                logger.info("3. For Thrustmaster devices, ensure drivers are installed")
                logger.info("4. Try reconnecting the device")
                return []
            
            successful_devices = 0
            for i in range(device_count):
                try:
                    joystick = pygame.joystick.Joystick(i)
                    device_name = joystick.get_name()
                    
                    # Enhanced logging for device detection
                    logger.info(f"Processing device {i}: '{device_name}'")
                    
                    # Check if it's a Thrustmaster device and log accordingly
                    is_thrustmaster = any(tm_indicator in device_name.lower() 
                                        for tm_indicator in ['thrustmaster', 'tm ', 't16000', 'twcs', 'hotas'])
                    if is_thrustmaster:
                        logger.info(f"🎯 Thrustmaster device detected: {device_name}")
                    
                    # Try to get additional device info for debugging
                    try:
                        # Don't initialize yet, just get basic info
                        guid = joystick.get_guid()
                        instance_id = joystick.get_instance_id()
                        logger.debug(f"Device {i} - GUID: {guid}, Instance ID: {instance_id}")
                    except Exception as info_e:
                        logger.debug(f"Could not get additional info for device {i}: {info_e}")
                    
                    # Create device object
                    device = InputDevice(i, device_name, joystick)
                    self.devices[i] = device
                    successful_devices += 1
                    
                    logger.info(f"✓ Successfully registered device {i}: {device_name}")
                    
                except Exception as e:
                    logger.error(f"✗ Failed to process device {i}: {e}")
                    logger.debug(f"Device {i} error details:", exc_info=True)
            
            logger.info(f"Device scan complete: {successful_devices}/{device_count} devices successfully registered")
            
            # Log summary of detected devices
            if self.devices:
                logger.info("Registered devices summary:")
                for device_id, device in self.devices.items():
                    device_type = "Thrustmaster" if any(tm in device.name.lower() 
                                                      for tm in ['thrustmaster', 'tm ', 't16000', 'twcs', 'hotas']) else "Generic"
                    logger.info(f"  Device {device_id}: {device.name} ({device_type})")
            
            return list(self.devices.values())
            
        except Exception as e:
            logger.error(f"Critical error during device refresh: {e}")
            logger.debug("Device refresh error details:", exc_info=True)
            return []
    
    def enable_device(self, device_id: int) -> bool:
        """Enable a specific device with enhanced error handling"""
        if device_id not in self.devices:
            logger.error(f"Device {device_id} not found in device list")
            return False
            
        device = self.devices[device_id]
        logger.info(f"Attempting to enable device {device_id}: {device.name}")
        
        try:
            if device.enable():
                if device_id not in self.enabled_devices:
                    self.enabled_devices.append(device_id)
                logger.info(f"✓ Successfully enabled device {device_id}: {device.name}")
                return True
            else:
                logger.error(f"✗ Failed to enable device {device_id}: {device.name}")
                return False
        except Exception as e:
            logger.error(f"✗ Exception while enabling device {device_id} ({device.name}): {e}")
            return False
    
    def disable_device(self, device_id: int) -> bool:
        """Disable a specific device with enhanced error handling"""
        if device_id not in self.devices:
            logger.error(f"Device {device_id} not found in device list")
            return False
            
        device = self.devices[device_id]
        logger.info(f"Disabling device {device_id}: {device.name}")
        
        try:
            device.disable()
            if device_id in self.enabled_devices:
                self.enabled_devices.remove(device_id)
            logger.info(f"✓ Successfully disabled device {device_id}: {device.name}")
            return True
        except Exception as e:
            logger.error(f"✗ Exception while disabling device {device_id} ({device.name}): {e}")
            return False
    
    def get_enabled_devices(self) -> List[InputDevice]:
        """Get list of enabled devices"""
        return [self.devices[device_id] for device_id in self.enabled_devices 
                if device_id in self.devices]
    
    def detect_input(self, timeout: float = 5.0) -> Optional[Tuple[int, str, int]]:
        """
        Detect input from enabled devices with improved rapid succession handling
        
        Args:
            timeout: Maximum time to wait for input (seconds)
            
        Returns:
            Tuple of (device_id, input_type, input_index) or None if no input
        """
        # Check if detection is already in progress
        with self.detection_lock:
            if self.detection_active:
                logger.info("Input detection already in progress, skipping new request")
                return None
            self.detection_active = True
        
        try:
            if not self.enabled_devices:
                return None
            
            self.waiting_for_input = True
            start_time = time.time()
            
            # Store baseline states immediately (no initial delay)
            baseline_states = {}
            movement_detected = {}
            
            # Initialize movement tracking
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
                
                movement_detected[device_id] = {}
                for i in range(device.get_axis_count()):
                    movement_detected[device_id][f'axis_{i}'] = False
            
            # Small delay to let any residual input settle
            time.sleep(0.1)
            
            # Re-establish baseline after brief settling
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
            axis_confirmation_times = {}  # Track when axis movement was first detected
            
            while time.time() - detection_start < (timeout - 0.1):  # Account for initial delay
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
                            logger.info(f"Button {i} pressed on device {device_id}")
                            return (device_id, 'Button', i)
                    
                    # Check axes with improved movement detection
                    for i in range(device.get_axis_count()):
                        current = device.joystick.get_axis(i)
                        baseline = baseline_states[device_id]['axes'][i]
                        movement_key = f'axis_{i}'
                        axis_key = (device_id, i)
                        
                        # Detect significant movement
                        movement = abs(current - baseline)
                        if movement > DEADZONE:
                            current_time = time.time()
                            if not movement_detected[device_id][movement_key]:
                                # First time detecting movement on this axis
                                movement_detected[device_id][movement_key] = True
                                axis_confirmation_times[axis_key] = current_time
                                logger.info(f"Axis {i} movement detected on device {device_id}, confirming...")
                            else:
                                # Check if enough time has passed for confirmation
                                if current_time - axis_confirmation_times.get(axis_key, 0) >= 0.1:
                                    # Re-check movement to confirm it's sustained
                                    pygame.event.pump()
                                    confirmed = device.joystick.get_axis(i)
                                    confirmed_movement = abs(confirmed - baseline)
                                    if confirmed_movement > DEADZONE * 0.6:  # Lower threshold for confirmation
                                        logger.info(f"Axis {i} movement confirmed on device {device_id}")
                                        return (device_id, 'Axis', i)
                                    else:
                                        # Movement not sustained, reset
                                        movement_detected[device_id][movement_key] = False
                                        if axis_key in axis_confirmation_times:
                                            del axis_confirmation_times[axis_key]
                        else:
                            # No significant movement, reset detection
                            movement_detected[device_id][movement_key] = False
                            if axis_key in axis_confirmation_times:
                                del axis_confirmation_times[axis_key]
                    
                    # Check hats (immediate response)
                    for i in range(device.get_hat_count()):
                        current = device.joystick.get_hat(i)
                        baseline = baseline_states[device_id]['hats'][i]
                        if current != baseline and current != (0, 0):
                            logger.info(f"Hat {i} moved on device {device_id}")
                            return (device_id, 'Hat', i)
                
                time.sleep(0.01)  # Smaller delay for more responsive detection
                
        except Exception as e:
            logger.error(f"Error during input detection: {e}")
        finally:
            self.waiting_for_input = False
            with self.detection_lock:
                self.detection_active = False
        
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
    
    def cancel_input_detection(self) -> bool:
        """
        Cancel ongoing input detection
        
        Returns:
            True if detection was cancelled, False if no detection was active
        """
        with self.detection_lock:
            if self.detection_active:
                self.waiting_for_input = False
                logger.info("Input detection cancelled")
                return True
            return False
    
    def cleanup(self) -> None:
        """Cleanup resources with enhanced error handling"""
        logger.info("Starting input manager cleanup...")
        
        try:
            # Stop any ongoing input detection
            with self.detection_lock:
                if self.detection_active:
                    self.waiting_for_input = False
                    self.detection_active = False
                    logger.info("Stopped active input detection")
            
            # Disable all devices
            disabled_count = 0
            for device_id, device in self.devices.items():
                try:
                    if device.enabled:
                        device.disable()
                        disabled_count += 1
                except Exception as e:
                    logger.error(f"Error disabling device {device_id} ({device.name}): {e}")
            
            if disabled_count > 0:
                logger.info(f"Disabled {disabled_count} device(s)")
            
            # Clear device lists
            self.devices.clear()
            self.enabled_devices.clear()
            self.input_states.clear()
            
            # Cleanup pygame
            try:
                pygame.joystick.quit()
                logger.debug("Pygame joystick subsystem shut down")
            except Exception as e:
                logger.error(f"Error shutting down joystick subsystem: {e}")
            
            try:
                pygame.quit()
                logger.debug("Pygame shut down")
            except Exception as e:
                logger.error(f"Error shutting down pygame: {e}")
            
            logger.info("✓ Input manager cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"✗ Critical error during input manager cleanup: {e}")
    
    def get_device_info(self, device_id: int) -> dict:
        """Get detailed information about a specific device"""
        if device_id not in self.devices:
            return {}
        
        device = self.devices[device_id]
        info = {
            'id': device_id,
            'name': device.name,
            'enabled': device.enabled,
            'is_thrustmaster': device.is_thrustmaster,
            'buttons': device.get_button_count(),
            'axes': device.get_axis_count(),
            'hats': device.get_hat_count()
        }
        
        # Add additional info if device is initialized
        try:
            if device.joystick.get_init():
                info['guid'] = device.joystick.get_guid()
                info['instance_id'] = device.joystick.get_instance_id()
        except Exception:
            pass
        
        return info
    
    def force_device_refresh(self) -> List[InputDevice]:
        """Force a complete device refresh with cleanup"""
        logger.info("Forcing complete device refresh...")
        
        try:
            # More aggressive cleanup
            for device in self.devices.values():
                try:
                    device.disable()
                except Exception:
                    pass
            
            self.devices.clear()
            self.enabled_devices.clear()
            self.input_states.clear()
            
            # Complete pygame restart
            try:
                pygame.joystick.quit()
            except Exception:
                pass
            
            try:
                pygame.quit()
                time.sleep(0.2)  # Longer pause
                pygame.init()
                pygame.joystick.init()
            except Exception as e:
                logger.error(f"Error during pygame restart: {e}")
                return []
            
            # Regular refresh
            return self.refresh_devices()
            
        except Exception as e:
            logger.error(f"Error during force refresh: {e}")
            return []
