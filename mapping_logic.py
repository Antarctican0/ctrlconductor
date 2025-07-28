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
    # --- Combined Throttle/Dynamic Brake support ---
    def set_throttle_mode(self, mode: str):
        """Set the throttle mode: 'separate', 'toggle', or 'split'"""
        self.throttle_mode = mode
        if mode == 'toggle':
            self.combined_toggle_state = False  # False=Throttle, True=Dynamic
        else:
            self.combined_toggle_state = None

    def get_throttle_mode(self) -> str:
        return getattr(self, 'throttle_mode', 'separate')

    def set_combined_toggle_state(self, state: bool):
        self.combined_toggle_state = state

    def process_combined_lever_input(self, value: float, toggle_state: bool = False) -> list:
        """
        Process a single lever for combined throttle/dynamic brake.
        Args:
            value: Axis value (-1.0 to 1.0 or 0.0 to 1.0 depending on mapping)
            toggle_state: If in toggle mode, True=Dynamic, False=Throttle (ignored in split mode)
        Returns:
            List of (function_id, value) tuples to send
        """
        results = []
        mode = self.get_throttle_mode()
        throttle_id = self.function_dict.get('Throttle Lever')
        dyn_id = self.function_dict.get('Dyn Brake Lever')
        
        # Ensure we have valid function IDs
        if throttle_id is None or dyn_id is None:
            logger.warning(f"Missing function IDs: Throttle={throttle_id}, Dyn={dyn_id}")
            return results
        
        # Apply deadzone to prevent jitter around center
        deadzone = 0.05
        if abs(value) < deadzone:
            value = 0.0
        
        logger.debug(f"Combined lever processing: mode={mode}, value={value:.3f}, toggle_state={toggle_state}")
        
        if mode == 'split':
            # Center = idle, positive = throttle, negative = dynamic brake
            if value > deadzone:
                # Throttle - Use notch system (0-8 notches) like normal throttle processing
                throttle_notch = int(round(value * 8))
                throttle_notch = max(0, min(8, throttle_notch))
                results.append((throttle_id, throttle_notch))
                results.append((dyn_id, 0))
                logger.debug(f"Split mode throttle: input={value:.3f} -> notch={throttle_notch}")
            elif value < -deadzone:
                # Dynamic brake - Use proper brake mapping (0-255)
                # Map negative values (-1 to 0) to brake range (0 to 255)
                dyn_val = int(abs(value) * 255)
                dyn_val = max(0, min(255, dyn_val))
                results.append((throttle_id, 0))
                results.append((dyn_id, dyn_val))
                logger.debug(f"Split mode dynamic: input={value:.3f} -> output={dyn_val}")
            else:
                # Idle position
                results.append((throttle_id, 0))
                results.append((dyn_id, 0))
                logger.debug("Split mode idle")
                
        elif mode == 'toggle':
            # Use toggle_state to select which function the lever controls
            # The lever should work in its full range for the selected function
            
            if toggle_state:
                # Dynamic Brake mode - use full axis range like other train brakes
                # Map full axis range (-1 to 1) to brake range (0 to 255)
                # Same formula as train brake: -1.0 = no braking (0), +1.0 = full braking (255)
                dyn_val = int(((value + 1.0) / 2.0) * 255)
                dyn_val = max(0, min(255, dyn_val))
                results.append((throttle_id, 0))
                results.append((dyn_id, dyn_val))
                logger.debug(f"Toggle mode dynamic: input={value:.3f} -> output={dyn_val} (full range)")
            else:
                # Throttle mode - use notch system like normal throttle
                # Convert full axis range (-1 to 1) to throttle notches (0 to 8)
                throttle_notch = int(round(((value + 1.0) / 2.0) * 8))
                throttle_notch = max(0, min(8, throttle_notch))
                results.append((throttle_id, throttle_notch))
                results.append((dyn_id, 0))
                logger.debug(f"Toggle mode throttle: input={value:.3f} -> notch={throttle_notch}")
        else:
            # Separate mode, do nothing here
            pass
            
        return results
    def get_reverser_command_value(self) -> int:
        """
        Get the current reverser value to send to the simulator (0=reverse, 127=neutral, 255=forward).
        Returns:
            int: Value for Run8 reverser lever (ushort 14)
        """
        if self.reverser_state == "forward":
            return 255
        elif self.reverser_state == "reverse":
            return 0
        else:
            return 127

    def get_reverser_command_packet(self) -> tuple:
        """
        Returns the (function_id, value) tuple for the current reverser state for UDP sending.
        """
        return (14, self.get_reverser_command_value())
    def update_reverser_3way_state_from_inputs(self, input_state: Dict[Tuple[int, str, int], Any]) -> bool:
        """
        Poll all mapped 3-way reverser inputs and update the reverser state if any mapped input is active.
        Supports both 3-input and 2-input (NOR logic) switch configurations.
        
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
        
        # Check which positions have mappings
        forward_mapping = self.reverser_3way_mappings.get("forward")
        neutral_mapping = self.reverser_3way_mappings.get("neutral")
        reverse_mapping = self.reverser_3way_mappings.get("reverse")
        
        # Determine if we're in 2-input mode (only forward and reverse mapped, or explicit setting)
        mapped_positions = [pos for pos in ["forward", "neutral", "reverse"] if self.reverser_3way_mappings.get(pos)]
        is_two_input_mode = (self.reverser_two_input_mode or 
                            (len(mapped_positions) == 2 and "neutral" not in mapped_positions))
        
        if is_two_input_mode:
            # 2-input mode: Only forward and reverse mapped
            # Only update if one of the mapped reverser inputs is actually in the input_state
            reverser_input_present = False
            forward_active = False
            reverse_active = False
            
            if forward_mapping:
                device_id, input_type, input_index = forward_mapping
                if (device_id, input_type, input_index) in input_state:
                    reverser_input_present = True
                    value = input_state.get((device_id, input_type, input_index))
                    if input_type == "Button" and value == 1:
                        forward_active = True
                    elif input_type == "Hat" and value == (0, 1):
                        forward_active = True
            
            if reverse_mapping:
                device_id, input_type, input_index = reverse_mapping
                if (device_id, input_type, input_index) in input_state:
                    reverser_input_present = True
                    value = input_state.get((device_id, input_type, input_index))
                    if input_type == "Button" and value == 1:
                        reverse_active = True
                    elif input_type == "Hat" and value == (0, -1):
                        reverse_active = True
            
            # Only update reverser state if a reverser input is actually present in this input cycle
            if not reverser_input_present:
                return False
            
            # Determine new state based on current button states
            if forward_active and not reverse_active:
                new_state = "forward"
            elif reverse_active and not forward_active:
                new_state = "reverse"
            elif not forward_active and not reverse_active:
                new_state = "neutral"
            else:
                # Both pressed: keep previous state (or prioritize forward)
                new_state = prev_state
            
            if new_state != prev_state:
                self.reverser_state = new_state
                logger.info(f"2-input reverser state changed to: {new_state} (forward={forward_active}, reverse={reverse_active})")
                return True
            return False
        else:
            # 3-input logic: Priority: forward > neutral > reverse (if multiple pressed, forward wins, etc.)
            # Only update if one of the mapped reverser inputs is actually in the input_state
            reverser_input_present = False
            active_pos = None
            
            for pos in ("forward", "neutral", "reverse"):
                mapping = self.reverser_3way_mappings.get(pos)
                if not mapping:
                    continue
                device_id, input_type, input_index = mapping
                
                # Check if this reverser input is present in the current input cycle
                if (device_id, input_type, input_index) in input_state:
                    reverser_input_present = True
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
            
            # Only update reverser state if a reverser input is actually present in this input cycle
            if not reverser_input_present:
                return False
            
            # Set the reverser state to the currently active position (or keep previous if none pressed)
            if active_pos is not None:
                changed = (self.reverser_state != active_pos)
                self.reverser_state = active_pos
                if changed:
                    logger.info(f"3-input reverser state changed to: {active_pos}")
                return changed
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
            'Headlight Front': 0,
            'Headlight Rear': 0,
            'Wiper Switch': 0
        }
        self.function_dict = {name: value for name, value in FunctionMapping.FUNCTIONS}
        
        # Reverser switch mode settings
        self.reverser_switch_mode = False
        self.reverser_two_input_mode = False  # New: Toggle for 2-input vs 3-input mode
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
            # Always clear existing data before loading
            self.function_input_map.clear()
            self.reverse_axis_settings.clear()
            self.reverser_3way_mappings = {}
            
            # Reset reverser mode to defaults
            self.reverser_switch_mode = False
            self.reverser_two_input_mode = False
            
            with open(mapping_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                loaded_mappings = 0
                loaded_reverser_mappings = 0
                loaded_new_reverser_mode = False  # Track if we found the new format
                
                for row in reader:
                    function_name = row.get('Function')
                    device_id = row.get('Device')
                    input_type = row.get('Type')
                    input_index = row.get('Index')
                    reverse_axis = row.get('Reverse', 'False')

                    # Handle new reverser mode format (preferred)
                    if function_name == '__REVERSER_MODE__':
                        mode_string = str(device_id).lower()  # Mode is stored in Device field
                        logger.debug(f"Loading reverser mode: {mode_string}")
                        try:
                            self.set_reverser_switch_mode(mode_string)
                            loaded_new_reverser_mode = True
                            logger.info(f"Loaded reverser mode: {mode_string}")
                        except ValueError as e:
                            logger.warning(f"Invalid reverser mode '{mode_string}', defaulting to axis: {e}")
                            self.set_reverser_switch_mode('axis')
                            loaded_new_reverser_mode = True
                        continue

                    # Handle legacy reverser switch mode row (for backward compatibility)
                    if function_name == '__REVERSER_SWITCH_MODE__':
                        legacy_switch_mode = str(reverse_axis).lower() == 'true'
                        logger.debug(f"Loading legacy reverser switch mode: {legacy_switch_mode}")
                        # Only use legacy format if new format wasn't found
                        if not loaded_new_reverser_mode:
                            if legacy_switch_mode:
                                # Default to 3way for legacy true values
                                self.set_reverser_switch_mode('3way')
                                logger.info("Loaded legacy reverser mode as 3way")
                            else:
                                self.set_reverser_switch_mode('axis')
                                logger.info("Loaded legacy reverser mode as axis")
                        else:
                            logger.debug("Skipping legacy reverser mode (new format already loaded)")
                        continue

                    # Handle reverser 3-way switch mappings
                    if function_name and function_name.startswith('__REVERSER_3WAY_'):
                        pos = function_name.replace('__REVERSER_3WAY_', '').lower().replace('__', '')
                        try:
                            if device_id and input_index and input_type:
                                device_id_int = int(device_id)
                                input_index_int = int(input_index)
                                self.set_reverser_3way_mapping(pos, device_id_int, str(input_type), input_index_int)
                                loaded_reverser_mappings += 1
                                logger.debug(f"Loaded reverser 3-way mapping: {pos} -> {device_id_int}:{input_type}:{input_index_int}")
                        except (ValueError, TypeError) as e:
                            logger.error(f"Invalid reverser 3-way mapping for {pos}: {e}")
                        continue

                    # Handle regular function mappings
                    if all([function_name, device_id is not None, input_type, input_index is not None]):
                        try:
                            function_name_str = str(function_name).strip()
                            input_type_str = str(input_type).strip()
                            input_index_int = int(input_index)
                            device_id_int = int(device_id)
                            
                            self.function_input_map[function_name_str] = (
                                device_id_int, 
                                input_type_str, 
                                input_index_int
                            )
                            self.reverse_axis_settings[function_name_str] = str(reverse_axis).lower() == 'true'
                            loaded_mappings += 1
                            logger.debug(f"Loaded mapping: {function_name_str} -> {device_id_int}:{input_type_str}:{input_index_int} (reverse: {self.reverse_axis_settings[function_name_str]})")
                        except (ValueError, TypeError) as e:
                            logger.error(f"Invalid mapping data for {function_name}: {e}")
                    elif function_name and not function_name.startswith('__'):
                        logger.warning(f"Skipping incomplete mapping for {function_name}: device={device_id}, type={input_type}, index={input_index}")

            logger.info(f"Loaded {loaded_mappings} regular mappings and {loaded_reverser_mappings} reverser 3-way mappings from {mapping_file}")
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
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
            
            with open(mapping_file, 'w', newline='', encoding='utf-8') as file:
                fieldnames = ['Function', 'Device', 'Type', 'Index', 'Reverse']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                saved_mappings = 0
                saved_reverser_mappings = 0
                
                # Save regular mappings
                for function_name, (device_id, input_type, input_index) in self.function_input_map.items():
                    try:
                        writer.writerow({
                            'Function': function_name,
                            'Device': device_id,
                            'Type': input_type,
                            'Index': input_index,
                            'Reverse': self.reverse_axis_settings.get(function_name, False)
                        })
                        saved_mappings += 1
                    except Exception as e:
                        logger.error(f"Failed to save mapping for {function_name}: {e}")
                        
                # Save reverser 3-way switch mappings if present
                if hasattr(self, 'reverser_3way_mappings') and self.reverser_3way_mappings:
                    for pos, mapping in self.reverser_3way_mappings.items():
                        try:
                            device_id, input_type, input_index = mapping
                            writer.writerow({
                                'Function': f'__REVERSER_3WAY_{pos.upper()}__',
                                'Device': device_id,
                                'Type': input_type,
                                'Index': input_index,
                                'Reverse': ''
                            })
                            saved_reverser_mappings += 1
                        except Exception as e:
                            logger.error(f"Failed to save reverser 3-way mapping for {pos}: {e}")
                        
                # Save reverser mode configuration as special rows
                # Determine the string mode to save
                try:
                    if self.reverser_switch_mode:
                        if getattr(self, 'reverser_two_input_mode', False):
                            mode_string = '2way'
                        else:
                            mode_string = '3way'
                    else:
                        mode_string = 'axis'
                        
                    writer.writerow({
                        'Function': '__REVERSER_MODE__',
                        'Device': mode_string,
                        'Type': '',
                        'Index': '',
                        'Reverse': ''
                    })
                    logger.debug(f"Saved reverser mode: {mode_string}")
                    
                    # Also save the legacy format for backward compatibility
                    writer.writerow({
                        'Function': '__REVERSER_SWITCH_MODE__',
                        'Device': '',
                        'Type': '',
                        'Index': '',
                        'Reverse': self.reverser_switch_mode
                    })
                    logger.debug(f"Saved legacy reverser switch mode: {self.reverser_switch_mode}")
                    
                except Exception as e:
                    logger.error(f"Failed to save reverser mode configuration: {e}")
                    
            logger.info(f"Saved {saved_mappings} regular mappings and {saved_reverser_mappings} reverser 3-way mappings to {mapping_file}")
            logger.info(f"Reverser mode: {'3way' if self.reverser_switch_mode and not getattr(self, 'reverser_two_input_mode', False) else '2way' if self.reverser_switch_mode else 'axis'}")
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
        Remove an input mapping, including reverser 3-way mappings if relevant.
        Args:
            function_name: Name of the Run8 function or special reverser 3way mapping
        Returns:
            True if removed successfully, False otherwise
        """
        removed = False
        # Remove from standard function mappings
        if function_name in self.function_input_map:
            del self.function_input_map[function_name]
            if function_name in self.reverse_axis_settings:
                del self.reverse_axis_settings[function_name]
            logger.info(f"Removed mapping for {function_name}")
            removed = True
        # Remove from reverser 3-way mappings if function_name matches
        if function_name.startswith("Reverser 3way"):
            # function_name is like 'Reverser 3way forward', 'Reverser 3way neutral', etc.
            parts = function_name.split()
            if len(parts) == 3:
                pos = parts[2].lower()
                if hasattr(self, 'reverser_3way_mappings') and pos in self.reverser_3way_mappings:
                    del self.reverser_3way_mappings[pos]
                    logger.info(f"Removed reverser 3-way mapping for {pos}")
                    removed = True
        return removed
    
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
        Process raw input value to Run8 command value.
        For the Reverser Lever (3-way switch mode), always return the correct value for function 14.
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

        # Reverser input mode selection: axis OR 3-way switch, never both
        if function_name == 'Reverser Lever':
            if self.get_reverser_switch_mode():
                # 3-way switch mode: always pass the current reverser value to the simulator
                # regardless of whether an axis is mapped or not
                return True, self.get_reverser_command_value()
            else:
                # Axis mode: only process axis, ignore buttons/hats
                if input_type == 'Axis':
                    return self._process_lever_input(function_name, input_type, raw_value, mapping_key, prev_states)
                else:
                    return False, 0

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
                
        elif input_behavior == '3way':
            # 3-way switch: Down=0, Center=1, Up=2
            # Hat values: (0, -1) = Down, (0, 0) = Center, (0, 1) = Up
            if raw_value == (0, -1):  # Down
                new_value = 0
            elif raw_value == (0, 0):  # Center
                new_value = 1
            elif raw_value == (0, 1):  # Up
                new_value = 2
            else:
                # Handle diagonal hat positions by using dominant direction
                if raw_value[1] > 0:  # Any upward component
                    new_value = 2
                elif raw_value[1] < 0:  # Any downward component
                    new_value = 0
                else:  # Horizontal or unknown
                    new_value = 1
            
            # Get previous 3-way value
            prev_3way_value = getattr(self, f'_last_3way_{function_name}', 1)  # Default to center
            if new_value != prev_3way_value:
                setattr(self, f'_last_3way_{function_name}', new_value)
                prev_states[mapping_key] = raw_value
                return True, new_value
                
        elif input_behavior == '4way':
            # 4-way switch: positions 0, 1, 2, 3
            # Hat values: (0, -1) = 0, (-1, 0) = 1, (0, 1) = 2, (1, 0) = 3, (0, 0) = center/default
            if raw_value == (0, -1):  # Down
                new_value = 0
            elif raw_value == (-1, 0):  # Left
                new_value = 1
            elif raw_value == (0, 1):  # Up
                new_value = 2
            elif raw_value == (1, 0):  # Right
                new_value = 3
            else:
                new_value = 0  # Default to first position
            
            # Get previous 4-way value
            prev_4way_value = getattr(self, f'_last_4way_{function_name}', 0)  # Default to first position
            if new_value != prev_4way_value:
                setattr(self, f'_last_4way_{function_name}', new_value)
                prev_states[mapping_key] = raw_value
                return True, new_value
        
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
    
    def set_reverser_switch_mode(self, mode):
        """Set the reverser switch mode. Accepts 'axis', '2way', or '3way'"""
        if mode == 'axis':
            self.reverser_switch_mode = False
            self.reverser_two_input_mode = False
        elif mode == '2way':
            self.reverser_switch_mode = True
            self.reverser_two_input_mode = True
        elif mode == '3way':
            self.reverser_switch_mode = True
            self.reverser_two_input_mode = False
        else:
            raise ValueError("Invalid reverser mode: {}".format(mode))
    
    def get_reverser_switch_mode(self):
        """Get the current reverser switch mode"""
        return self.reverser_switch_mode
    
    def get_current_mode_string(self) -> str:
        """Get the current reverser mode as a string for debugging"""
        if self.reverser_switch_mode:
            if getattr(self, 'reverser_two_input_mode', False):
                return '2way'
            else:
                return '3way'
        else:
            return 'axis'
    
    def validate_mappings(self) -> bool:
        """Validate the current mappings for consistency"""
        try:
            # Check if all mapped functions exist in the function dictionary
            for function_name in self.function_input_map:
                if function_name not in self.function_dict:
                    logger.warning(f"Mapping found for unknown function: {function_name}")
            
            # Check reverser 3-way mappings if in switch mode
            if self.reverser_switch_mode and hasattr(self, 'reverser_3way_mappings'):
                expected_positions = ['forward', 'neutral', 'reverse'] if not getattr(self, 'reverser_two_input_mode', False) else ['forward', 'reverse']
                for pos in expected_positions:
                    if pos not in self.reverser_3way_mappings:
                        logger.warning(f"Missing reverser 3-way mapping for position: {pos}")
                        
            logger.debug(f"Validation complete. Mode: {self.get_current_mode_string()}, Mappings: {len(self.function_input_map)}")
            return True
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False
    
    # --- Reverser 3-way switch support ---
    def set_reverser_3way_mapping(self, position: str, device_id: int, input_type: str, input_index: int):
        """Set the mapping for a reverser 3-way switch position ('forward', 'neutral', 'reverse')."""
        if not hasattr(self, 'reverser_3way_mappings'):
            self.reverser_3way_mappings = {}
        self.reverser_3way_mappings[position] = (device_id, input_type, input_index)
        logger.info(f"Set reverser 3-way mapping: {position} -> {device_id}:{input_type}:{input_index}")

    def get_reverser_3way_mapping(self, position: str):
        """Get the mapping for a reverser 3-way switch position."""
        if hasattr(self, 'reverser_3way_mappings'):
            mapping = self.reverser_3way_mappings.get(position)
            if mapping is None:
                logger.warning(f"No mapping found for Reverser 3way {position}")
            return mapping
        logger.warning(f"No mapping found for Reverser 3way {position}")
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
        """Get all current mappings, including reverser 3-way mappings"""
        all_mappings = self.function_input_map.copy()
        
        # Add reverser 3-way mappings with special naming
        if hasattr(self, 'reverser_3way_mappings'):
            for position, mapping in self.reverser_3way_mappings.items():
                all_mappings[f"Reverser 3way {position}"] = mapping
        
        return all_mappings
    
    def clear_all_mappings(self) -> None:
        """Clear all mappings, including reverser 3-way mappings"""
        self.function_input_map.clear()
        self.reverse_axis_settings.clear()
        if hasattr(self, 'reverser_3way_mappings'):
            self.reverser_3way_mappings.clear()
        logger.info("Cleared all mappings (including reverser 3-way)")
    
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
        # Store the original raw value for logging
        original_value = value
        
        # Apply axis reversal if configured
        if self.get_axis_reverse(function_name):
            value = -value
        
        # Account for joysticks that don't reach full range (common issue)
        # Many joysticks only reach ~0.95-0.98 instead of true 1.0
        # Expand the range slightly to ensure we can reach 0 and 255
        if value > 0.95:
            value = 1.0  # Force full range for values very close to 1.0
        elif value < -0.95:
            value = -1.0  # Force full range for values very close to -1.0
        
        # Direct mapping from -1.0 to 1.0 to 0-255 range with minimal processing
        # This provides immediate response to control movements
        if function_name == "Train Brake Lever":
            # Standard mapping for train brake lever: -1.0 = full release (0), +1.0 = full emergency (255)
            brake_val = int(((value + 1.0) / 2.0) * 255)
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
        
        # Enhanced logging to show raw input vs processed output
        logger.info(f"Brake {function_name}: raw_axis={original_value:.3f}, processed_axis={value:.3f}, final_value={brake_val} (range: 0=release, 255=emergency)")
        
        return brake_val
