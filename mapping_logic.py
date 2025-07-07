"""
Input mapping logic for Run8 Control Conductor

Handles the logic for mapping inputs to Run8 functions and processing input values.
"""

import csv
import os
from typing import Dict, List, Tuple, Optional, Any
import logging

from config import FunctionMapping

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Input detection constants
DEADZONE = 0.7


class InputMapper:
    def update_reverser_3way_state_from_inputs(self, input_state: Dict[Tuple[int, str, int], Any]) -> bool:
        """
        Poll all mapped 3-way reverser inputs and update the reverser state if any mapped input is active.
        Args:
            input_state: Dict mapping (device_id, input_type, input_index) to current value (e.g., 1 for button pressed)
        Returns:
            True if the reverser state changed, False otherwise
        """
        # Only use 3-way mappings if switch mode is enabled
        if not self.get_reverser_switch_mode():
            return False
        if not hasattr(self, 'reverser_3way_mappings') or not self.reverser_3way_mappings:
            return False

        prev_state = self.reverser_state
        # Priority: forward > neutral > reverse (if multiple pressed, forward wins, etc.)
        active_pos = None
        for pos in ("forward", "neutral", "reverse"):
            mapping = self.reverser_3way_mappings.get(pos)
            if not mapping:
                continue
            device_id, input_type, input_index = mapping
            value = input_state.get((device_id, input_type, input_index))
            if input_type == "Button":
                # Button is considered active if value == 1 (pressed)
                if value == 1:
                    active_pos = pos
                    break  # Highest priority found
            elif input_type == "Hat":
                # For hats, value should match direction
                if pos == "forward" and value == (0, 1):
                    active_pos = pos
                    break
                elif pos == "neutral" and value == (0, 0):
                    active_pos = pos
                    break
                elif pos == "reverse" and value == (0, -1):
                    active_pos = pos
                    break

        # Always set the reverser state to the currently active position (or keep previous if none pressed)
        if active_pos is not None:
            changed = (self.reverser_state != active_pos)
            self.reverser_state = active_pos
            if changed:
                logger.info(f"3-way reverser state changed to: {active_pos}")
            return changed
        # If no button/hat is pressed, do not change the state (latch last position)
        return False

    def find_existing_mapping(self, device_id: int, input_type: str, input_index: int) -> Optional[str]:
        """
        Find if an input is already mapped to a function.
        Returns the function name if found, else None.
        """
        for func, mapping in self.function_input_map.items():
            if mapping == (device_id, input_type, input_index):
                return func
        return None

    def __init__(self, mapping_file: Optional[str] = None):
        """
        Initialize the input mapper
        
        Args:
            mapping_file: Path to mapping CSV file
        """
        self.mapping_file = mapping_file or os.path.join(os.path.dirname(__file__), 'input_mappings.csv')
        self.function_input_map: Dict[str, Tuple[int, str, int]] = {}
        self.reverse_axis_settings: Dict[str, bool] = {}
        self.multiway_states: Dict[str, int] = {
            'Distance Counter': 0,
            'Headlight_Front': 0,
            'Headlight_Rear': 0,
            'Wiper Switch': 0
        }
        self.function_dict = {name: value for name, value in FunctionMapping.FUNCTIONS}
        
        # Reverser switch mode settings
        self.reverser_switch_mode = False
        self.reverser_state = "neutral"  # Current reverser position
        self.reverser_positions = {
            "forward": 255,     # Forward (uint16 max for Run8)
            "neutral": 127,    # Neutral (midpoint)
            "reverse": 0       # Reverse (uint16 min)
        }
        
        # 3-way reverser mappings
        self.reverser_3way_mappings = {}  # position -> (device_id, input_type, input_index)
    
    def load_mappings_from_csv(self, file_path: Optional[str] = None) -> bool:
        """
        Load input mappings from CSV file
        
        Args:
            file_path: Optional path to the CSV file. If None, uses default mapping file
        
        Returns:
            True if loaded successfully, False otherwise
        """
        mapping_file = file_path if file_path else self.mapping_file
        
        if not os.path.exists(mapping_file):
            logger.info(f"Mapping file {mapping_file} not found, starting with empty mappings")
            return False
        
        try:
            # Always clear 3-way mappings before loading
            self.reverser_3way_mappings = {}
            with open(mapping_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    function_name = row.get('Function')
                    device_id = row.get('Device')
                    input_type = row.get('Type')
                    input_index = row.get('Index')
                    reverse_axis = row.get('Reverse', 'False')

                    # Handle special reverser switch mode row
                    if function_name == '__REVERSER_SWITCH_MODE__':
                        self.reverser_switch_mode = str(reverse_axis).lower() == 'true'
                        logger.debug(f"Loaded reverser switch mode: {self.reverser_switch_mode}")
                        continue

                    # Handle reverser 3-way switch mappings
                    if function_name and function_name.startswith('__REVERSER_3WAY_'):
                        pos = function_name.replace('__REVERSER_3WAY_', '').lower().replace('__', '')
                        try:
                            if device_id is not None and input_index is not None and input_type is not None:
                                device_id_int = int(device_id)
                                input_index_int = int(input_index)
                                self.set_reverser_3way_mapping(pos, device_id_int, str(input_type), input_index_int)
                                logger.debug(f"Loaded reverser 3-way mapping: {pos} -> {device_id_int}:{input_type}:{input_index_int}")
                        except Exception as e:
                            logger.error(f"Invalid reverser 3-way mapping for {pos}: {e}")
                        continue

                    if all([function_name is not None, device_id is not None, input_type is not None, input_index is not None]):
                        try:
                            function_name_str = str(function_name)
                            input_type_str = str(input_type)
                            if input_index is None or device_id is None:
                                raise ValueError("Input index or device id is None")
                            input_index_int = int(input_index)
                            device_id_int = int(device_id)
                            self.function_input_map[function_name_str] = (
                                device_id_int, 
                                input_type_str, 
                                input_index_int
                            )
                            self.reverse_axis_settings[function_name_str] = str(reverse_axis).lower() == 'true'
                            logger.debug(f"Loaded mapping: {function_name_str} -> {device_id_int}:{input_type_str}:{input_index_int}")
                        except (ValueError, TypeError) as e:
                            logger.error(f"Invalid mapping data for {function_name}: {e}")

            logger.info(f"Loaded {len(self.function_input_map)} mappings from {mapping_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to load mappings from {mapping_file}: {e}")
            return False
    
    def save_mappings(self, file_path: Optional[str] = None) -> bool:
        """
        Save input mappings to CSV file
        
        Args:
            file_path: Optional path to the CSV file. If None, uses default mapping file
        
        Returns:
            True if saved successfully, False otherwise
        """
        mapping_file = file_path if file_path else self.mapping_file
        
        try:
            with open(mapping_file, 'w', newline='', encoding='utf-8') as file:
                fieldnames = ['Function', 'Device', 'Type', 'Index', 'Reverse']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                # Save regular mappings
                for function_name, (device_id, input_type, input_index) in self.function_input_map.items():
                    writer.writerow({
                        'Function': function_name,
                        'Device': device_id,
                        'Type': input_type,
                        'Index': input_index,
                        'Reverse': self.reverse_axis_settings.get(function_name, False)
                    })
                # Save reverser 3-way switch mappings if present
                if hasattr(self, 'reverser_3way_mappings'):
                    for pos, mapping in self.reverser_3way_mappings.items():
                        device_id, input_type, input_index = mapping
                        writer.writerow({
                            'Function': f'__REVERSER_3WAY_{pos.upper()}__',
                            'Device': device_id,
                            'Type': input_type,
                            'Index': input_index,
                            'Reverse': ''
                        })
                # Save reverser switch mode as a special row
                writer.writerow({
                    'Function': '__REVERSER_SWITCH_MODE__',
                    'Device': '',
                    'Type': '',
                    'Index': '',
                    'Reverse': self.reverser_switch_mode
                })
                    
            logger.info(f"Saved {len(self.function_input_map)} mappings to {mapping_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save mappings to {mapping_file}: {e}")
            return False
    
    def add_mapping(self, function_name: str, device_id: int, input_type: str, input_index: int) -> bool:
        """
        Add a new input mapping
        
        Args:
            function_name: Name of the Run8 function
            device_id: Input device ID
            input_type: Type of input (Button, Axis, Hat)
            input_index: Index of the input
            
        Returns:
            True if added successfully, False otherwise
        """
        if function_name not in self.function_dict:
            logger.error(f"Unknown function: {function_name}")
            return False
        
        self.function_input_map[function_name] = (device_id, input_type, input_index)
        logger.info(f"Added mapping: {function_name} -> {device_id}:{input_type}:{input_index}")
        return True
    
    def remove_mapping(self, function_name: str) -> bool:
        """
        Remove an input mapping
        
        Args:
            function_name: Name of the Run8 function
            
        Returns:
            True if removed successfully, False otherwise
        """
        if function_name in self.function_input_map:
            del self.function_input_map[function_name]
            if function_name in self.reverse_axis_settings:
                del self.reverse_axis_settings[function_name]
            logger.info(f"Removed mapping for {function_name}")
            return True
        return False
    
    def get_mapping(self, function_name: str) -> Optional[Tuple[int, str, int]]:
        """
        Get mapping for a specific function
        
        Args:
            function_name: Name of the Run8 function
            
        Returns:
            Tuple of (device_id, input_type, input_index) or None if not mapped
        """
        return self.function_input_map.get(function_name)
    
    def set_axis_reverse(self, function_name: str, reverse: bool) -> None:
        """
        Set axis reverse setting for a function
        
        Args:
            function_name: Name of the Run8 function
            reverse: Whether to reverse the axis
        """
        self.reverse_axis_settings[function_name] = reverse
        logger.debug(f"Set axis reverse for {function_name}: {reverse}")
    
    def get_axis_reverse(self, function_name: str) -> bool:
        """
        Get axis reverse setting for a function
        
        Args:
            function_name: Name of the Run8 function
            
        Returns:
            True if axis should be reversed, False otherwise
        """
        return self.reverse_axis_settings.get(function_name, False)
    
    def process_input_value(self, function_name: str, device_id: int, input_type: str, 
                           input_index: int, raw_value: Any, prev_states: Dict) -> Tuple[bool, int]:
        """
        Process raw input value to Run8 command value
        
        Args:
            function_name: Name of the Run8 function
            device_id: Input device ID
            input_type: Type of input (Button, Axis, Hat)
            input_index: Index of the input
            raw_value: Raw input value
            prev_states: Previous state tracking dictionary
            
        Returns:
            Tuple of (value_changed, processed_value)
        """
        mapping_key = (device_id, input_type, input_index)
        input_behavior = FunctionMapping.INPUT_TYPES.get(function_name, 'toggle')
        
        if input_behavior == 'lever':
            return self._process_lever_input(function_name, input_type, raw_value, mapping_key, prev_states)
        elif input_type == "Button":
            return self._process_button_input(function_name, raw_value, mapping_key, prev_states, input_behavior)
        elif input_type == "Axis" and input_behavior not in ('lever',):
            return self._process_axis_input(function_name, raw_value, mapping_key, prev_states, input_behavior)
        elif input_type == "Hat":
            return self._process_hat_input(function_name, raw_value, mapping_key, prev_states, input_behavior)
        
        return False, 0
    
    def _process_lever_input(self, function_name: str, input_type: str, raw_value: float, 
                            mapping_key: Tuple, prev_states: Dict) -> Tuple[bool, int]:
        """Process lever input (throttle, brake, reverser)"""
        if input_type != 'Axis':
            return False, 0
        
        axis_val = raw_value
        if self.get_axis_reverse(function_name):
            axis_val = -axis_val
        
        axis_val = max(-1.0, min(1.0, axis_val))
        
        if function_name == 'Throttle Lever':
            notch = int(round(((axis_val + 1.0) / 2.0) * 8))
            notch = max(0, min(8, notch))
            prev_notch = prev_states.get(mapping_key, -1)
            if notch != prev_notch:
                prev_states[mapping_key] = notch
                return True, notch
                
        elif function_name == 'Reverser Lever':
            # Get axis value (handle reverse setting)
            axis_val = -raw_value if self.reverse_axis_settings.get(function_name, False) else raw_value
            
            # Precise reverser control with clear regions for reverse/neutral/forward
            if axis_val < -0.8:  # Reverse position - more definitive threshold
                reverser_val = 0
                position = "reverse"
            elif axis_val > 0.8:  # Forward position - more definitive threshold
                reverser_val = 255
                position = "forward"
            else:  # Neutral position - wider center region for stability
                reverser_val = 127
                position = "neutral"
            
            # Check if value changed since last update
            prev_reverser = prev_states.get(mapping_key, None)
            if reverser_val != prev_reverser:
                prev_states[mapping_key] = reverser_val
                logger.info(f"Lever reverser: position={position}, value={reverser_val}, axis={axis_val:.2f}")
                return True, reverser_val
                
        elif function_name in ('Independent Brake Lever', 'Train Brake Lever', 'Dyn Brake Lever'):
            # Brake levers: Use full range from -1 to 1, mapping to 0-255.
            # Reverse axis setting is handled before this.
            # Map -1.0 to 1.0 -> 0 to 255
            brake_val = int(((axis_val + 1.0) / 2.0) * 255)
            brake_val = max(0, min(255, brake_val))

            prev_brake = prev_states.get(mapping_key, -1)
            if brake_val != prev_brake:
                prev_states[mapping_key] = brake_val
                logger.info(f"Brake {function_name} changed to: {brake_val} (axis: {axis_val:.3f})")
                return True, brake_val
        
        return False, 0
    
    def _process_button_input(self, function_name: str, raw_value: int, mapping_key: Tuple, 
                             prev_states: Dict, input_behavior: str) -> Tuple[bool, int]:
        """Process button input"""
        current_pressed = bool(raw_value)
        prev_pressed = prev_states.get(mapping_key, False)
        
        if function_name in self.multiway_states and input_behavior in ('3way', '4way'):
            num_states = 3 if input_behavior == '3way' else 4
            if current_pressed and not prev_pressed:
                self.multiway_states[function_name] = (self.multiway_states[function_name] + 1) % num_states
                value = self.multiway_states[function_name]
                prev_states[mapping_key] = current_pressed
                return True, value
                
        elif input_behavior == 'momentary':
            if current_pressed != prev_pressed:
                prev_states[mapping_key] = current_pressed
                return True, 1 if current_pressed else 0
                
        elif input_behavior == 'toggle':
            if current_pressed and not prev_pressed:
                prev_states[mapping_key] = current_pressed
                return True, 1
        
        prev_states[mapping_key] = current_pressed
        return False, 0
    
    def _process_axis_input(self, function_name: str, raw_value: float, mapping_key: Tuple, 
                           prev_states: Dict, input_behavior: str) -> Tuple[bool, int]:
        """Process axis input for non-lever functions"""
        prev_value = prev_states.get(mapping_key, 0.0)
        
        if input_behavior == 'momentary':
            current_active = abs(raw_value) > DEADZONE
            prev_active = abs(prev_value) > DEADZONE
            if current_active != prev_active:
                prev_states[mapping_key] = raw_value
                return True, 1 if current_active else 0
                
        elif input_behavior == 'toggle':
            current_active = abs(raw_value) > DEADZONE
            prev_active = abs(prev_value) > DEADZONE
            if current_active and not prev_active:
                prev_states[mapping_key] = raw_value
                return True, 1
        
        prev_states[mapping_key] = raw_value
        return False, 0
    
    def _process_hat_input(self, function_name: str, raw_value: Tuple[int, int], mapping_key: Tuple, 
                          prev_states: Dict, input_behavior: str) -> Tuple[bool, int]:
        """Process hat input"""
        prev_value = prev_states.get(mapping_key, (0, 0))
        
        if input_behavior == 'momentary':
            current_active = raw_value != (0, 0)
            prev_active = prev_value != (0, 0)
            if current_active != prev_active:
                prev_states[mapping_key] = raw_value
                return True, 1 if current_active else 0
                
        elif input_behavior == 'toggle':
            current_active = raw_value != (0, 0)
            prev_active = prev_value != (0, 0)
            if current_active and not prev_active:
                prev_states[mapping_key] = raw_value
                return True, 1
        
        prev_states[mapping_key] = raw_value
        return False, 0
    
    def process_reverser_switch_input(self, device_id, input_type, input_index, value, states):
        """
        Process reverser input in 3-position switch mode.
        
        Args:
            device_id: Input device ID
            input_type: Type of input (Button, Axis, Hat)
            input_index: Index of the input
            value: Current input value
            states: Dictionary of current states
            
        Returns:
            tuple: (changed, value) - Whether the state changed and the new value
        """
        changed = False
        
        if input_type == "Button":
            # Button pressed = 1, released = 0
            if value == 0:
                # Button released, ignore
                return False, self.reverser_positions[self.reverser_state]
            
            # Check if this button is mapped to a specific position
            forward_key = f"reverser_switch_forward_{device_id}_{input_index}"
            neutral_key = f"reverser_switch_neutral_{device_id}_{input_index}"
            reverse_key = f"reverser_switch_reverse_{device_id}_{input_index}"
            
            # First time setup for buttons if they don't exist in states
            if not any(k.startswith(f"reverser_switch_") for k in states):
                # This is the first button, map it to forward
                states[forward_key] = True
                self.reverser_state = "forward"
                return True, self.reverser_positions["forward"]
            elif forward_key not in states and neutral_key not in states and reverse_key not in states:
                # This is a new button, find a position that's not mapped yet
                if not any(k.startswith("reverser_switch_forward") for k in states):
                    states[forward_key] = True
                    self.reverser_state = "forward"
                    return True, self.reverser_positions["forward"]
                elif not any(k.startswith("reverser_switch_neutral") for k in states):
                    states[neutral_key] = True
                    self.reverser_state = "neutral"
                    return True, self.reverser_positions["neutral"]
                elif not any(k.startswith("reverser_switch_reverse") for k in states):
                    states[reverse_key] = True
                    self.reverser_state = "reverse"
                    return True, self.reverser_positions["reverse"]
            
            # Handle already mapped buttons
            if forward_key in states:
                if self.reverser_state != "forward":
                    self.reverser_state = "forward"
                    changed = True
            elif neutral_key in states:
                if self.reverser_state != "neutral":
                    self.reverser_state = "neutral"
                    changed = True
            elif reverse_key in states:
                if self.reverser_state != "reverse":
                    self.reverser_state = "reverse"
                    changed = True
                    
        elif input_type == "Hat":
            # For hat switches: up for forward, center for neutral, down for reverse
            if value[1] == 1:  # Up
                if self.reverser_state != "forward":
                    self.reverser_state = "forward"
                    changed = True
            elif value[1] == -1:  # Down
                if self.reverser_state != "reverse":
                    self.reverser_state = "reverse"
                    changed = True
            elif value == (0, 0):  # Center
                if self.reverser_state != "neutral":
                    self.reverser_state = "neutral"
                    changed = True
        
        return changed, self.reverser_positions[self.reverser_state]
    
    def set_reverser_switch_mode(self, switch_mode: bool):
        """Set the reverser switch mode"""
        self.reverser_switch_mode = switch_mode
    
    def get_reverser_switch_mode(self):
        """Get the current reverser switch mode"""
        return self.reverser_switch_mode
    
    # --- Reverser 3-way switch support ---
    def set_reverser_3way_mapping(self, position: str, device_id: int, input_type: str, input_index: int):
        """Set the mapping for a reverser 3-way switch position ('forward', 'neutral', 'reverse')."""
        if not hasattr(self, 'reverser_3way_mappings'):
            self.reverser_3way_mappings = {}
        self.reverser_3way_mappings[position] = (device_id, input_type, input_index)

    def get_reverser_3way_mapping(self, position: str):
        """Get the mapping for a reverser 3-way switch position."""
        if hasattr(self, 'reverser_3way_mappings'):
            return self.reverser_3way_mappings.get(position)
        return None

    def clear_reverser_3way_mapping(self, position: str):
        """Clear the mapping for a reverser 3-way switch position."""
        if hasattr(self, 'reverser_3way_mappings') and position in self.reverser_3way_mappings:
            del self.reverser_3way_mappings[position]

    def get_all_reverser_3way_mappings(self):
        """Return all 3-way switch mappings as a dict."""
        if hasattr(self, 'reverser_3way_mappings'):
            return dict(self.reverser_3way_mappings)
        return {}

    def process_reverser_3way_input(self, device_id: int, input_type: str, input_index: int, value: Any) -> Optional[str]:
        """Return 'forward', 'neutral', or 'reverse' if the input matches a mapped 3-way switch and is active."""
        if not hasattr(self, 'reverser_3way_mappings'):
            return None
        for pos, mapping in self.reverser_3way_mappings.items():
            if mapping == (device_id, input_type, input_index):
                # For buttons, value==1 means pressed
                if input_type == 'Button' and value:
                    return pos
                # For hats, value matches direction
                if input_type == 'Hat' and value:
                    return pos
        return None
    
    def get_all_mappings(self) -> Dict[str, Tuple[int, str, int]]:
        """Get all current mappings"""
        return self.function_input_map.copy()
    
    def clear_all_mappings(self) -> None:
        """Clear all mappings"""
        self.function_input_map.clear()
        self.reverse_axis_settings.clear()
        logger.info("Cleared all mappings")
    
    def get_mapped_functions(self) -> List[str]:
        """Get list of functions that have mappings"""
        return list(self.function_input_map.keys())
    
    def get_unmapped_functions(self) -> List[str]:
        """Get list of functions that don't have mappings"""
        all_functions = set(self.function_dict.keys())
        mapped_functions = set(self.function_input_map.keys())
        return list(all_functions - mapped_functions)
    
    def process_reverser_lever_axis(self, value: float) -> int:
        """
        Process reverser lever axis value to appropriate simulator value
        Args:
            value: Axis value from -1.0 to 1.0
        Returns:
            Simulator value (0-255)
        """
        # Add a small deadzone around center
        if -0.2 <= value <= 0.2:
            # Neutral zone
            reverser_val = 127
            state_name = "neutral"
        elif value > 0.2:
            # Forward
            # Scale from 0.2->1.0 to 128->255
            reverser_val = int(127 + (value - 0.2) * 160)
            reverser_val = min(255, max(128, reverser_val))
            state_name = "forward"
        else:
            # Reverse
            # Scale from -0.2->-1.0 to 126->0
            reverser_val = int(127 - (abs(value) - 0.2) * 160)
            reverser_val = min(126, max(0, reverser_val))
            state_name = "reverse"
        
        logger.info(f"Reverser lever: axis={value:.2f}, state={state_name}, value={reverser_val}")
        return reverser_val
    
    def process_brake_input(self, function_name: str, value: float) -> int:
        """
        Process brake input with direct mapping for better responsiveness
        """
        # Direct mapping from -1.0 to 1.0 to 0-255 range with minimal processing
        # This provides immediate response to control movements
        if function_name == "Train Brake Lever":
            # Slight bias toward release position for train brakes
            brake_val = int(((value + 1.05) / 2.1) * 255)
        elif function_name == "Independent Brake Lever":
            # Standard mapping for independent brake
            brake_val = int(((value + 1.0) / 2.0) * 255)
        elif function_name == "Dyn Brake Lever":
            # Dynamic brake is typically only active in positive range
            if value < -0.5:
                brake_val = 0  # Off position
            else:
                # Map from -0.5 to 1.0 to 0-255 for more control
                brake_val = int(((value + 0.5) / 1.5) * 255)
        else:
            # Default mapping for any other levers
            brake_val = int(((value + 1.0) / 2.0) * 255)
        
        # Ensure value stays in valid range
        brake_val = max(0, min(255, brake_val))
        
        # Log at INFO level for debugging
        logger.info(f"Brake {function_name}: axis={value:.2f}, value={brake_val}")
        
        return brake_val
