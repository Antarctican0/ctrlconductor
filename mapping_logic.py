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
    """Handles input mapping and processing logic"""
    
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
        self.reverser_positions = {
            "forward": 65535,   # Full forward
            "neutral": 32767,   # Center position
            "reverse": 0        # Full reverse
        }
        
        # State tracking for reverser switch
        self.reverser_state = "neutral"  # Current state: forward, neutral, reverse
    
    def load_mappings_from_csv(self) -> bool:
        """
        Load input mappings from CSV file
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not os.path.exists(self.mapping_file):
            logger.info(f"Mapping file {self.mapping_file} not found, starting with empty mappings")
            return False
        
        try:
            with open(self.mapping_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    function_name = row.get('Function')
                    device_id = row.get('Device')
                    input_type = row.get('Type')
                    input_index = row.get('Index')
                    reverse_axis = row.get('Reverse', 'False')
                    
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
                            
            logger.info(f"Loaded {len(self.function_input_map)} mappings from {self.mapping_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load mappings from {self.mapping_file}: {e}")
            return False
    
    def save_mappings(self) -> bool:
        """
        Save input mappings to CSV file
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.mapping_file, 'w', newline='', encoding='utf-8') as file:
                fieldnames = ['Function', 'Device', 'Type', 'Index', 'Reverse']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for function_name, (device_id, input_type, input_index) in self.function_input_map.items():
                    writer.writerow({
                        'Function': function_name,
                        'Device': device_id,
                        'Type': input_type,
                        'Index': input_index,
                        'Reverse': self.reverse_axis_settings.get(function_name, False)
                    })
                    
            logger.info(f"Saved {len(self.function_input_map)} mappings to {self.mapping_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save mappings to {self.mapping_file}: {e}")
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
        elif input_type == 'Button':
            return self._process_button_input(function_name, raw_value, mapping_key, prev_states, input_behavior)
        elif input_type == 'Axis' and input_behavior not in ('lever',):
            return self._process_axis_input(function_name, raw_value, mapping_key, prev_states, input_behavior)
        elif input_type == 'Hat':
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
            if axis_val <= -0.33:
                reverser_val = 0
            elif axis_val >= 0.33:
                reverser_val = 255
            else:
                reverser_val = 127
            prev_reverser = prev_states.get(mapping_key, -1)
            if reverser_val != prev_reverser:
                prev_states[mapping_key] = reverser_val
                return True, reverser_val
                
        elif function_name == 'Dyn Brake Lever':
            if axis_val <= -0.95:
                dyn_val = 0
            else:
                norm = (axis_val - (-0.95)) / (1.0 - (-0.95))
                norm = max(0.0, min(1.0, norm))
                dyn_val = int(round(norm * 254)) + 1
            prev_dyn = prev_states.get(mapping_key, -1)
            if dyn_val != prev_dyn:
                prev_states[mapping_key] = dyn_val
                return True, dyn_val
                
        elif function_name in ('Independent Brake Lever', 'Train Brake Lever'):
            brake_val = int(round(((axis_val + 1.0) / 2.0) * 255))
            brake_val = max(0, min(255, brake_val))
            prev_brake = prev_states.get(mapping_key, -1)
            if brake_val != prev_brake:
                prev_states[mapping_key] = brake_val
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
    
    # (Duplicate methods removed. The original implementations above are retained.)
    
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
