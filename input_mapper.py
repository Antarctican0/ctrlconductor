"""
Run8 Control Conductor - Joystick/Gamepad Input Mapper

A GUI application that maps joystick/gamepad inputs to Run8 train simulator functions
and sends them via UDP packets. Features include:

- Support for multiple input devices (joysticks, gamepads)
- Configurable input mapping with persistent storage
- Dark theme UI with tabbed interface
- Support for various input types: momentary, toggle, lever, multi-way switches
- Real-time input detection and UDP transmission
- Axis reversal for lever controls

Author: Ethan
Version: 2.0
"""

import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
import pygame
import socket
import threading
import csv
import os
import time
import struct
from typing import Dict, List, Tuple, Optional, Union

# UDP settings
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 18888

# Input detection constants
DEADZONE = 0.7
RELEASE_TIMEOUT = 0.15
POLLING_INTERVAL = 20
UDP_SEND_INTERVAL = 50

# UI Theme Configuration
class ThemeConfig:
    DARK_BG = '#23272e'
    DARK_FG = '#e6e6e6'
    DARK_ACCENT = '#3a3f4b'
    DARK_HIGHLIGHT = '#4f5666'
    DARK_BUTTON_BG = '#353b45'
    DARK_BUTTON_FG = '#e6e6e6'
    DARK_ENTRY_BG = '#2c313a'
    DARK_ENTRY_FG = '#e6e6e6'
    LIGHT_BG = '#2c313a'  # lighter gray for label backgrounds

# Run8 Function Mappings
class FunctionMapping:
    FUNCTIONS = [
        ("Alerter", 1),
        ("Bell", 2),
        ("Distance Counter", 3),
        ("Dyn Brake Lever", 4),
        ("Headlight_Front", 5),
        ("Headlight_Rear", 6),
        ("Horn", 8),
        ("Independent Brake Lever", 9),
        ("Independent Bailoff", 10),
        ("Park-Brake Set", 12),
        ("Park-Brake Release", 13),
        ("Reverser Lever", 14),
        ("Sander", 15),
        ("Throttle Lever", 16),
        ("Train Brake Lever", 18),
        ("Wiper Switch", 19),
        ("Cab Light Switch", 41),
        ("Step Light Switch", 42),
        ("Gauge Light Switch", 43),
        ("EOT Emg Stop", 44),
        ("HEP Switch", 52),
        ("SlowSpeedOnOff", 55),
        ("Slow Speed Increment", 56),
        ("Slow Speed Decrement", 57),
        ("DPU Throttle Increase", 58),
        ("DPU Throttle Decrease", 59),
        ("DPU Dyn-Brake Setup", 60),
        ("DPU Fence Increase", 61),
        ("DPU Fence Decrease", 62),
    ]
    
    INPUT_TYPES = {
        'Horn': 'momentary',
        'Bell': 'momentary',
        'Alerter': 'momentary',
        'Independent Bailoff': 'momentary',
        'Sander': 'momentary',
        'EOT Emg Stop': 'momentary',
        'Throttle Lever': 'lever',
        'Dyn Brake Lever': 'lever',
        'Train Brake Lever': 'lever',
        'Reverser Lever': 'lever',
        'Distance Counter': '3way',  # 3-way toggle
        'Headlight_Front': '3way',   # 3-way toggle
        'Headlight_Rear': '3way',    # 3-way toggle
        'Wiper Switch': '4way',      # 4-way toggle
        'Park-Brake Set': 'momentary',
        'Park-Brake Release': 'momentary',
        'Cab Light Switch': 'toggle',
        'Step Light Switch': 'toggle',
        'Gauge Light Switch': 'toggle',
        'HEP Switch': 'toggle',
        'SlowSpeedOnOff': 'toggle',
        'Slow Speed Increment': 'momentary',
        'Slow Speed Decrement': 'momentary',
        'DPU Throttle Increase': 'momentary',
        'DPU Throttle Decrease': 'momentary',
        'DPU Dyn-Brake Setup': 'momentary',
        'DPU Fence Increase': 'momentary',
        'DPU Fence Decrease': 'momentary',
        'Independent Brake Lever': 'lever',
    }
    
    CATEGORIES = {
        "Main Controls": [
            "Throttle Lever", "Train Brake Lever", "Independent Brake Lever", 
            "Dyn Brake Lever", "Reverser Lever", "Sander", "Horn", "Bell", "Alerter"
        ],
        "Lights and Wipers": [
            "Headlight_Front", "Headlight_Rear", "Wiper Switch", 
            "Cab Light Switch", "Step Light Switch", "Gauge Light Switch"
        ],
        "DPU": [
            "DPU Throttle Increase", "DPU Throttle Decrease", "DPU Dyn-Brake Setup", 
            "DPU Fence Increase", "DPU Fence Decrease"
        ],
        "Misc": [
            "EOT Emg Stop", "HEP Switch", "SlowSpeedOnOff", "Slow Speed Increment", 
            "Slow Speed Decrement", "Independent Bailoff", "Distance Counter", 
            "Park-Brake Set", "Park-Brake Release"
        ]
    }

class InputMapperApp:
    def __init__(self, master):
        self.master = master
        master.title("Run8 Control Conductor")

        # Initialize theme configuration
        self.theme = ThemeConfig()
        self._setup_ui_theme(master)
        
        # Initialize function mappings
        self.function_list = FunctionMapping.FUNCTIONS
        self.function_input_type = FunctionMapping.INPUT_TYPES
        self.function_categories = FunctionMapping.CATEGORIES
        
        # Initialize state tracking
        self.multiway_states = {
            'Distance Counter': 0, 
            'Headlight_Front': 0, 
            'Headlight_Rear': 0, 
            'Wiper Switch': 0
        }
        self.function_dict = {name: ushort for name, ushort in self.function_list}
        
        # Initialize application state
        self.running = False
        self.sock = None
        self.input_thread = None
        self.waiting_for_input = False
        self.input_map_target = None
        
        # Initialize data structures
        self.device_vars = []
        self.device_checkboxes = []
        self.mapping_widgets = []
        self.mapping_labels = []
        self.mapping_buttons = []
        self.function_label_map = {}
        self.function_input_map = {}
        self.reverse_axis_vars = {}
        
        # Setup UI
        self._setup_connection_ui()
        self._setup_device_ui()
        self._setup_mapping_ui()
        self._setup_control_ui()
        
        # Load saved mappings
        self.mapping_save_path = os.path.join(os.path.dirname(__file__), 'input_mappings.csv')
        self.load_mappings()
        
        # Initialize devices
        self.refresh_devices()

    def _setup_ui_theme(self, master):
        """Setup UI theme colors and styles"""
        master.configure(bg=self.theme.DARK_BG)
        
        self._label_kwargs = {
            'bg': self.theme.LIGHT_BG, 
            'fg': self.theme.DARK_FG
        }
        self._entry_kwargs = {
            'bg': self.theme.DARK_ENTRY_BG, 
            'fg': self.theme.DARK_ENTRY_FG, 
            'insertbackground': self.theme.DARK_ENTRY_FG, 
            'highlightbackground': self.theme.DARK_HIGHLIGHT, 
            'highlightcolor': self.theme.DARK_HIGHLIGHT
        }
        self._button_kwargs = {
            'bg': self.theme.DARK_BUTTON_BG, 
            'fg': self.theme.DARK_BUTTON_FG, 
            'activebackground': self.theme.DARK_HIGHLIGHT, 
            'activeforeground': self.theme.DARK_FG, 
            'relief': 'flat'
        }
        self._check_kwargs = {
            'bg': self.theme.DARK_BG, 
            'fg': self.theme.DARK_FG, 
            'activebackground': self.theme.DARK_BG, 
            'activeforeground': self.theme.DARK_FG, 
            'selectcolor': self.theme.DARK_ACCENT
        }

    def _setup_connection_ui(self):
        """Setup IP and port configuration UI"""
        self.ip_label = tk.Label(self.master, text="Simulator IP:", **self._label_kwargs)
        self.ip_label.pack()
        self.ip_entry = tk.Entry(self.master, **self._entry_kwargs)
        self.ip_entry.insert(0, DEFAULT_IP)
        self.ip_entry.pack()

        self.port_label = tk.Label(self.master, text="Simulator Port:", **self._label_kwargs)
        self.port_label.pack()
        self.port_entry = tk.Entry(self.master, **self._entry_kwargs)
        self.port_entry.insert(0, str(DEFAULT_PORT))
        self.port_entry.pack()

    def _setup_device_ui(self):
        """Setup device selection UI"""
        self.device_frame = tk.LabelFrame(
            self.master, 
            text="Input Devices", 
            bg=self.theme.LIGHT_BG, 
            fg=self.theme.DARK_FG, 
            bd=2, 
            relief='groove', 
            labelanchor='nw'
        )
        self.device_frame.pack(pady=10, fill="x")
        
        self.refresh_devices_button = tk.Button(
            self.device_frame, 
            text="Refresh Devices", 
            command=self.refresh_devices, 
            **self._button_kwargs
        )
        self.refresh_devices_button.pack(anchor="w")
        
        self.devices_list_frame = tk.Frame(self.device_frame, bg=self.theme.LIGHT_BG)
        self.devices_list_frame.pack(anchor="w", fill="x")

    def _setup_mapping_ui(self):
        """Setup input mapping UI"""
        self.mapping_frame = tk.LabelFrame(
            self.master, 
            text="Input Mapping", 
            bg=self.theme.DARK_ACCENT, 
            fg=self.theme.DARK_FG, 
            bd=2, 
            relief='groove', 
            labelanchor='nw'
        )
        self.mapping_frame.pack(pady=10, fill="both", expand=True)

        # Setup TTK style for tabs
        self._setup_ttk_style()
        
        self.mapping_prompt = tk.StringVar(value="Click 'Map Input' to assign a function.")
        self.prompt_label = tk.Label(
            self.mapping_frame, 
            textvariable=self.mapping_prompt, 
            fg="#7ecfff", 
            bg=self.theme.DARK_ACCENT
        )
        self.prompt_label.pack(anchor="w", pady=(0, 5))
        
        self.tabs = ttk.Notebook(self.mapping_frame)
        self.tabs.pack(fill="both", expand=True)
        
        # Create category frames
        self.category_frames = {}
        for cat in self.function_categories:
            frame = tk.Frame(self.tabs)
            self.tabs.add(frame, text=cat)
            self.category_frames[cat] = frame

    def _setup_ttk_style(self):
        """Setup TTK notebook style for dark theme"""
        style = ttk.Style()
        try:
            style.theme_use('default')
        except Exception:
            pass
        
        style.configure('TNotebook', background=self.theme.DARK_ACCENT, borderwidth=0)
        style.configure(
            'TNotebook.Tab', 
            background=self.theme.DARK_BG, 
            foreground=self.theme.DARK_FG, 
            lightcolor=self.theme.DARK_ACCENT, 
            borderwidth=1, 
            focusthickness=2, 
            focuscolor=self.theme.DARK_HIGHLIGHT
        )
        style.map(
            'TNotebook.Tab', 
            background=[('selected', self.theme.DARK_ACCENT)], 
            foreground=[('selected', self.theme.DARK_FG)]
        )

    def _setup_control_ui(self):
        """Setup control buttons and status display"""
        self.start_button = tk.Button(
            self.master, 
            text="Start UDP", 
            command=self.start_mapping, 
            **self._button_kwargs
        )
        self.start_button.pack(pady=10)

        self.status_label = tk.Label(
            self.master, 
            text="Status: Waiting to start...", 
            **self._label_kwargs
        )
        self.status_label.pack()



    def refresh_devices(self):
        """Refresh the list of available input devices"""
        # Clear previous checkboxes
        for cb in self.device_checkboxes:
            cb.destroy()
        self.device_vars.clear()
        self.device_checkboxes.clear()
        
        # Initialize pygame and detect devices
        pygame.init()
        pygame.joystick.init()
        num_devices = pygame.joystick.get_count()
        
        for i in range(num_devices):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(
                self.devices_list_frame, 
                text=joy.get_name(), 
                variable=var, 
                **self._check_kwargs
            )
            cb.pack(anchor="w")
            self.device_vars.append(var)
            self.device_checkboxes.append(cb)
        
        # Rebuild mapping UI
        self.build_mapping_ui()

    def build_mapping_ui(self):
        """Build the mapping interface for all function categories"""
        # Clear previous widgets
        for widget in self.mapping_widgets:
            widget.destroy()
        self.mapping_widgets.clear()
        self.mapping_labels.clear()
        self.mapping_buttons.clear()
        
        # Clear category frames
        for frame in self.category_frames.values():
            for child in frame.winfo_children():
                child.destroy()
        
        # Build UI for each category
        for cat, funclist in self.function_categories.items():
            frame = self.category_frames[cat]
            frame.configure(bg=self.theme.DARK_ACCENT)
            
            # Create headers
            headers = ["Function", "Mapped Input", "Reverse Axis", ""]
            for col, header in enumerate(headers):
                tk.Label(
                    frame, 
                    text=header, 
                    font=("Arial", 10, "bold"), 
                    **self._label_kwargs
                ).grid(row=0, column=col, sticky="w", padx=4)
            
            # Create function mapping rows
            for idx, fname in enumerate(funclist):
                row = idx + 1
                
                # Function name label
                label = tk.Label(frame, text=fname, **self._label_kwargs)
                label.grid(row=row, column=0, sticky="w", padx=4, pady=2)
                
                # Mapped input display
                mapped = tk.Label(
                    frame, 
                    text="Not mapped", 
                    fg="#888", 
                    bg=self.theme.LIGHT_BG
                )
                mapped.grid(row=row, column=1, sticky="w", padx=4, pady=2)
                self.function_label_map[fname] = mapped
                
                # Reverse axis checkbox (for levers only)
                if self.function_input_type.get(fname) == 'lever':
                    rev_var = self.reverse_axis_vars.get(fname)
                    if not rev_var:
                        rev_var = tk.BooleanVar(value=False)
                        self.reverse_axis_vars[fname] = rev_var
                    reverse_cb = tk.Checkbutton(frame, variable=rev_var, **self._check_kwargs)
                    reverse_cb.grid(row=row, column=2, padx=4, pady=2)
                    self.mapping_widgets.append(reverse_cb)
                
                # Map input button
                btn = tk.Button(
                    frame, 
                    text="Map Input", 
                    command=lambda f=fname, l=mapped: self.start_input_mapping(f, l),
                    bg=self.theme.DARK_BUTTON_BG, 
                    fg=self.theme.DARK_BUTTON_FG, 
                    activebackground=self.theme.DARK_HIGHLIGHT, 
                    activeforeground=self.theme.DARK_FG,
                    relief='groove', 
                    bd=2, 
                    highlightbackground=self.theme.DARK_HIGHLIGHT, 
                    highlightcolor=self.theme.DARK_HIGHLIGHT
                )
                btn.grid(row=row, column=3, padx=4, pady=2)
                
                self.mapping_labels.append(mapped)
                self.mapping_buttons.append(btn)
                self.mapping_widgets.extend([label, mapped, btn])
                
                # Show current mapping if exists
                self._update_mapping_display(fname, mapped)

    def _update_mapping_display(self, fname: str, mapped_label: tk.Label):
        """Update the display of a mapped input for a function"""
        if fname in self.function_input_map:
            mapping = self.function_input_map[fname]
            if isinstance(mapping, tuple) and len(mapping) == 4 and mapping[1] == 'Hat':
                dev, _, hat_idx, dir_name = mapping
                mapped_label.config(
                    text=f"Hat {hat_idx} {dir_name} (Device {dev})", 
                    fg=self.theme.DARK_FG, 
                    bg=self.theme.LIGHT_BG
                )
            else:
                dev, typ, idx = mapping
                mapped_label.config(
                    text=f"{typ} {idx} (Device {dev})", 
                    fg=self.theme.DARK_FG, 
                    bg=self.theme.LIGHT_BG
                )
    def start_input_mapping(self, function_name, label_widget):
        # Disable all map buttons while waiting for input
        for btn in self.mapping_buttons:
            btn.config(state="disabled")
        self.mapping_prompt.set(f"Press a button or move an axis for '{function_name}' on an enabled device...")
        self.waiting_for_input = True
        self.input_map_target = (function_name, label_widget)
        # Start a thread to listen for input
        threading.Thread(target=self.detect_input_for_mapping, daemon=True).start()

    def detect_input_for_mapping(self):
        """Detect input from enabled devices for mapping"""
        pygame.init()
        pygame.joystick.init()
        enabled_indices = [i for i, var in enumerate(self.device_vars) if var.get()]
        
        if not enabled_indices:
            self.mapping_prompt.set("No input devices enabled.")
            self._enable_mapping_buttons()
            return
        
        joysticks = [pygame.joystick.Joystick(i) for i in enabled_indices]
        for joy in joysticks:
            joy.init()
        
        # Wait for all inputs to be released
        self._wait_for_input_release(joysticks)
        
        # Record initial state
        initial_state = self._get_initial_input_state(joysticks)
        
        # Wait for new input
        self._wait_for_new_input(joysticks, initial_state, enabled_indices)
        
        # Reset UI
        self.mapping_prompt.set("Click 'Map Input' to assign a function.")
        self._enable_mapping_buttons()

    def _wait_for_input_release(self, joysticks: List):
        """Wait for all inputs to be released before mapping"""
        release_start = time.time()
        while True:
            pygame.event.pump()
            all_released = True
            
            for joy in joysticks:
                # Check axes
                for a in range(joy.get_numaxes()):
                    if abs(joy.get_axis(a)) > DEADZONE:
                        all_released = False
                        break
                
                # Check buttons
                for b in range(joy.get_numbuttons()):
                    if joy.get_button(b):
                        all_released = False
                        break
                
                if not all_released:
                    break
            
            if all_released or (time.time() - release_start > RELEASE_TIMEOUT):
                break
            
            pygame.time.wait(2)

    def _get_initial_input_state(self, joysticks: List) -> Dict:
        """Get the initial state of all inputs"""
        pygame.event.pump()
        initial_state = {
            'axes': [],
            'buttons': [],
            'hats': []
        }
        
        for joy in joysticks:
            initial_state['axes'].append([joy.get_axis(a) for a in range(joy.get_numaxes())])
            initial_state['buttons'].append([joy.get_button(b) for b in range(joy.get_numbuttons())])
            initial_state['hats'].append([joy.get_hat(h) for h in range(joy.get_numhats())])
        
        return initial_state

    def _wait_for_new_input(self, joysticks: List, initial_state: Dict, enabled_indices: List):
        """Wait for new input and map it"""
        while True:
            pygame.event.pump()
            
            for idx, (dev_idx, joy) in enumerate(zip(enabled_indices, joysticks)):
                # Check axes
                if self._check_axis_input(joy, idx, dev_idx, initial_state['axes']):
                    return
                
                # Check buttons
                if self._check_button_input(joy, idx, dev_idx, initial_state['buttons']):
                    return
                
                # Check hats (D-Pad)
                if self._check_hat_input(joy, idx, dev_idx, initial_state['hats']):
                    return
            
            pygame.time.wait(POLLING_INTERVAL)

    def _check_axis_input(self, joy, joy_idx: int, dev_idx: int, initial_axes: List) -> bool:
        """Check for axis input and map if detected"""
        for axis in range(joy.get_numaxes()):
            val = joy.get_axis(axis)
            if abs(val) > DEADZONE and abs(val - initial_axes[joy_idx][axis]) > 0.1:
                mapping_tuple = (dev_idx, 'Axis', axis)
                self._remove_input_from_others(mapping_tuple, self.input_map_target[0])
                self.set_input_mapping(self.input_map_target[0], mapping_tuple, self.input_map_target[1])
                return True
        return False

    def _check_button_input(self, joy, joy_idx: int, dev_idx: int, initial_buttons: List) -> bool:
        """Check for button input and map if detected"""
        for btn in range(joy.get_numbuttons()):
            if joy.get_button(btn) and not initial_buttons[joy_idx][btn]:
                mapping_tuple = (dev_idx, 'Button', btn)
                self._remove_input_from_others(mapping_tuple, self.input_map_target[0])
                self.set_input_mapping(self.input_map_target[0], mapping_tuple, self.input_map_target[1])
                return True
        return False

    def _check_hat_input(self, joy, joy_idx: int, dev_idx: int, initial_hats: List) -> bool:
        """Check for hat (D-Pad) input and map if detected"""
        for h in range(joy.get_numhats()):
            hat_val = joy.get_hat(h)
            prev_hat = initial_hats[joy_idx][h]
            
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            dir_names = ['Up', 'Down', 'Right', 'Left']
            
            for d, dname in zip(directions, dir_names):
                if hat_val == d and prev_hat != d:
                    mapping_tuple = (dev_idx, 'Hat', h, dname)
                    self._remove_input_from_others(mapping_tuple, self.input_map_target[0])
                    self.set_input_mapping(self.input_map_target[0], mapping_tuple, self.input_map_target[1])
                    return True
        return False

    def _remove_input_from_others(self, mapping_tuple: Tuple, target_function: str):
        """Remove input mapping from other functions"""
        to_remove = []
        for fname, mapping in self.function_input_map.items():
            if mapping == mapping_tuple and fname != target_function:
                to_remove.append(fname)
        
        for fname in to_remove:
            del self.function_input_map[fname]
            if fname in self.function_label_map:
                self.function_label_map[fname].config(text="Not mapped", fg="gray")

    def _enable_mapping_buttons(self):
        """Enable all mapping buttons"""
        for btn in self.mapping_buttons:
            btn.config(state="normal")

    def set_input_mapping(self, function_name, mapping_tuple, label_widget):
        # mapping_tuple: (dev_idx, typ, idx) or (dev_idx, 'Hat', hat_idx, dir_name)
        # Remove this input from any other function
        to_remove = []
        for fname, mapping in self.function_input_map.items():
            if mapping == mapping_tuple and fname != function_name:
                to_remove.append(fname)
        for fname in to_remove:
            del self.function_input_map[fname]
            # Update UI label for unmapped function
            if fname in self.function_label_map:
                self.function_label_map[fname].config(text="Not mapped", fg="gray")
        # Set the new mapping for this function
        self.function_input_map[function_name] = mapping_tuple
        # Label formatting
        if mapping_tuple[1] == 'Hat':
            dev_idx, _, hat_idx, dir_name = mapping_tuple
            label_widget.config(text=f"Hat {hat_idx} {dir_name} (Device {dev_idx})", fg="black")
        else:
            dev_idx, typ, idx = mapping_tuple
            label_widget.config(text=f"{typ} {idx} (Device {dev_idx})", fg="black")
        self.save_mappings()

    def save_mappings(self):
        """Save current input mappings to CSV file"""
        try:
            with open(self.mapping_save_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Function', 'Device', 'Type', 'Index', 'Direction'])  # Header
                
                for fname, mapping in self.function_input_map.items():
                    if isinstance(mapping, tuple) and len(mapping) == 4:
                        # Hat mapping: (dev_idx, 'Hat', hat_idx, dir_name)
                        writer.writerow([fname, mapping[0], mapping[1], mapping[2], mapping[3]])
                    else:
                        # Regular mapping: (dev_idx, typ, idx)
                        writer.writerow([fname, mapping[0], mapping[1], mapping[2], ''])
        except Exception as e:
            print(f"Error saving mappings: {e}")
            messagebox.showerror("Save Error", f"Could not save mappings: {e}")

    def load_mappings(self):
        """Load input mappings from CSV file"""
        if not os.path.exists(self.mapping_save_path):
            return
        
        try:
            with open(self.mapping_save_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header if present
                
                for row in reader:
                    if len(row) < 4:
                        continue
                    
                    fname = row[0]
                    if len(row) >= 5 and row[2] == 'Hat' and row[4]:
                        # Hat mapping: (dev_idx, 'Hat', hat_idx, dir_name)
                        dev_idx = int(row[1])
                        hat_idx = int(row[3])
                        dir_name = row[4]
                        self.function_input_map[fname] = (dev_idx, 'Hat', hat_idx, dir_name)
                    elif len(row) >= 4:
                        # Regular mapping: (dev_idx, typ, idx)
                        dev_idx = int(row[1])
                        typ = row[2]
                        idx = int(row[3])
                        self.function_input_map[fname] = (dev_idx, typ, idx)
        except Exception as e:
            print(f"Error loading mappings: {e}")
            messagebox.showerror("Load Error", f"Could not load mappings: {e}")
        
        # Update UI after loading
        self._update_all_mapping_displays()

    def _update_all_mapping_displays(self):
        """Update all mapping displays in the UI"""
        if hasattr(self, 'function_label_map'):
            for fname, mapping in self.function_input_map.items():
                label = self.function_label_map.get(fname)
                if label:
                    self._update_mapping_display(fname, label)

    def start_mapping(self):
        """Start the UDP mapping process"""
        if self.running:
            return
        
        # Validate IP and port
        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showerror("Error", "IP address cannot be empty.")
            return
        
        try:
            port = int(self.port_entry.get())
            if not (1 <= port <= 65535):
                raise ValueError("Port must be between 1 and 65535")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid port: {e}")
            return
        
        # Check for enabled devices
        self.enabled_devices = [i for i, var in enumerate(self.device_vars) if var.get()]
        if not self.enabled_devices:
            messagebox.showerror("Error", "No input devices enabled.")
            return
        
        # Check for any mapped functions
        if not self.function_input_map:
            if not messagebox.askyesno("Warning", "No functions are mapped. Continue anyway?"):
                return
        
        try:
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.target = (ip, port)
            
            # Start the mapping process
            self.running = True
            self.status_label.config(text="Status: Mapping started!")
            self.start_button.config(text="Stop UDP", command=self.stop_mapping)
            
            # Start input processing thread
            self.input_thread = threading.Thread(target=self.input_loop, daemon=True)
            self.input_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not start UDP mapping: {e}")
            self.running = False

    def stop_mapping(self):
        """Stop the UDP mapping process"""
        self.running = False
        if self.sock:
            self.sock.close()
            self.sock = None
        
        self.status_label.config(text="Status: Mapping stopped.")
        self.start_button.config(text="Start UDP", command=self.start_mapping)

    def input_loop(self):
        """Main input processing loop"""
        try:
            pygame.init()
            pygame.joystick.init()
            
            if pygame.joystick.get_count() == 0:
                self.status_label.config(text="No joystick/gamepad detected.")
                return
            
            # Initialize joysticks for enabled devices
            joysticks = []
            for idx in self.enabled_devices:
                if idx < pygame.joystick.get_count():
                    joy = pygame.joystick.Joystick(idx)
                    joy.init()
                    joysticks.append(joy)
            
            if not joysticks:
                self.status_label.config(text="No valid joysticks found.")
                return
            
            device_names = ', '.join(j.get_name() for j in joysticks)
            self.status_label.config(text=f"Using: {device_names}")
            
            # Track previous state for each mapped input
            prev_states = {}
            
            while self.running:
                try:
                    self._process_input_mappings(joysticks, prev_states)
                    pygame.time.wait(UDP_SEND_INTERVAL)
                except Exception as e:
                    print(f"Error in input processing: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in input loop: {e}")
            self.status_label.config(text=f"Error: {e}")
        finally:
            self.running = False

    def _process_input_mappings(self, joysticks: List, prev_states: Dict):
        """Process all input mappings and send UDP packets"""
        # Always rebuild input_to_function to reflect latest mappings
        input_to_function = {}
        for fname, mapping in self.function_input_map.items():
            input_to_function[mapping] = fname
            if mapping not in prev_states:
                prev_states[mapping] = 0
        
        # Remove any prev_states for unmapped inputs
        for mapping in list(prev_states.keys()):
            if mapping not in input_to_function:
                del prev_states[mapping]

        pygame.event.pump()
        
        for mapping, fname in input_to_function.items():
            try:
                send, value = self._process_single_mapping(mapping, fname, joysticks, prev_states)
                if send:
                    self._send_udp_packet(fname, value)
            except Exception as e:
                print(f"Error processing mapping {fname}: {e}")
                continue

    def _process_single_mapping(self, mapping: Tuple, fname: str, joysticks: List, prev_states: Dict) -> Tuple[bool, int]:
        """Process a single input mapping and return (should_send, value)"""
        send = False
        value = 0
        
        # Handle Hat (D-Pad) inputs
        if isinstance(mapping, tuple) and len(mapping) == 4 and mapping[1] == 'Hat':
            send, value = self._process_hat_input(mapping, fname, joysticks, prev_states)
        else:
            # Handle regular axis/button inputs
            send, value = self._process_regular_input(mapping, fname, joysticks, prev_states)
        
        return send, value

    def _send_udp_packet(self, fname: str, value: int):
        """Send UDP packet for a function with given value"""
        try:
            header = 0x60 | 0x80  # Always set audio flag (MSB)
            ushort = self.function_dict[fname]
            
            msg_bytes = bytearray()
            msg_bytes.append(header)
            msg_bytes.append((ushort >> 8) & 0xFF)
            msg_bytes.append(ushort & 0xFF)
            msg_bytes.append(value & 0xFF)
            
            # Calculate CRC
            crc = msg_bytes[0] ^ msg_bytes[1] ^ msg_bytes[2] ^ msg_bytes[3]
            msg_bytes.append(crc)
            
            self.sock.sendto(msg_bytes, self.target)
        except Exception as e:
            print(f"Error sending UDP packet for {fname}: {e}")

    def _process_hat_input(self, mapping: Tuple, fname: str, joysticks: List, prev_states: Dict) -> Tuple[bool, int]:
        """Process hat (D-Pad) input"""
        dev_idx, _, hat_idx, dir_name = mapping
        
        if dev_idx >= len(joysticks):
            return False, 0
        
        joy = joysticks[self.enabled_devices.index(dev_idx)]
        hat_val = joy.get_hat(hat_idx)
        
        # Map direction to value
        dir_map = {'Up': (0, 1), 'Down': (0, -1), 'Right': (1, 0), 'Left': (-1, 0)}
        dtuple = dir_map[dir_name]
        curr = 1 if hat_val == dtuple else 0
        prev = prev_states.get(mapping, 0)
        
        input_type = self.function_input_type.get(fname, 'toggle')
        
        if fname in self.multiway_states and input_type in ('3way', '4way'):
            num_states = 3 if input_type == '3way' else 4
            if curr and not prev:
                self.multiway_states[fname] = (self.multiway_states.get(fname, 0) + 1) % num_states
                value = self.multiway_states[fname]
                prev_states[mapping] = curr
                return True, value
        elif input_type == 'momentary':
            if curr != prev:
                prev_states[mapping] = curr
                return True, curr
        else:  # toggle
            if curr and not prev:
                prev_states[mapping] = curr
                return True, 1
        
        prev_states[mapping] = curr
        return False, 0

    def _process_regular_input(self, mapping: Tuple, fname: str, joysticks: List, prev_states: Dict) -> Tuple[bool, int]:
        """Process regular axis/button input"""
        dev_idx, typ, idx = mapping
        
        if dev_idx >= len(joysticks):
            return False, 0
        
        joy = joysticks[self.enabled_devices.index(dev_idx)]
        input_type = self.function_input_type.get(fname, 'toggle')
        
        # Handle different input types
        if input_type == 'lever':
            return self._process_lever_input(fname, typ, idx, joy, mapping, prev_states)
        elif typ == 'Button':
            return self._process_button_input(fname, idx, joy, mapping, prev_states, input_type)
        elif typ == 'Axis' and input_type not in ('lever',):
            return self._process_axis_input(fname, idx, joy, mapping, prev_states, input_type)
        
        return False, 0

    def _process_lever_input(self, fname: str, typ: str, idx: int, joy, mapping: Tuple, prev_states: Dict) -> Tuple[bool, int]:
        """Process lever input (throttle, brake, reverser)"""
        if typ != 'Axis':
            return False, 0
        
        axis_val = joy.get_axis(idx)
        rev = self.reverse_axis_vars.get(fname, tk.BooleanVar(value=False)).get()
        if rev:
            axis_val = -axis_val
        
        axis_val = max(-1.0, min(1.0, axis_val))
        
        if fname == 'Throttle Lever':
            notch = int(round(((axis_val + 1.0) / 2.0) * 8))
            notch = max(0, min(8, notch))
            prev_notch = prev_states.get(mapping, -1)
            if notch != prev_notch:
                prev_states[mapping] = notch
                return True, notch
        elif fname == 'Reverser Lever':
            if axis_val <= -0.33:
                reverser_val = 0
            elif axis_val >= 0.33:
                reverser_val = 255
            else:
                reverser_val = 127
            prev_reverser = prev_states.get(mapping, -1)
            if reverser_val != prev_reverser:
                prev_states[mapping] = reverser_val
                return True, reverser_val
        elif fname == 'Dyn Brake Lever':
            if axis_val <= -0.95:
                dyn_val = 0
            else:
                norm = (axis_val - (-0.95)) / (1.0 - (-0.95))
                norm = max(0.0, min(1.0, norm))
                dyn_val = int(round(norm * 254)) + 1
            prev_dyn = prev_states.get(mapping, -1)
            if dyn_val != prev_dyn:
                prev_states[mapping] = dyn_val
                return True, dyn_val
        elif fname in ('Independent Brake Lever', 'Train Brake Lever'):
            brake_val = int(round(((axis_val + 1.0) / 2.0) * 255))
            brake_val = max(0, min(255, brake_val))
            prev_brake = prev_states.get(mapping, -1)
            if brake_val != prev_brake:
                prev_states[mapping] = brake_val
                return True, brake_val
        
        return False, 0

    def _process_button_input(self, fname: str, idx: int, joy, mapping: Tuple, prev_states: Dict, input_type: str) -> Tuple[bool, int]:
        """Process button input"""
        curr = 1 if joy.get_button(idx) else 0
        prev = prev_states.get(mapping, 0)
        
        if fname in self.multiway_states and input_type in ('3way', '4way'):
            num_states = 3 if input_type == '3way' else 4
            if curr and not prev:
                self.multiway_states[fname] = (self.multiway_states.get(fname, 0) + 1) % num_states
                value = self.multiway_states[fname]
                prev_states[mapping] = curr
                return True, value
        elif input_type == 'momentary':
            if curr != prev:
                prev_states[mapping] = curr
                return True, curr
        elif input_type == 'toggle':
            if curr and not prev:
                prev_states[mapping] = curr
                return True, 1
        
        prev_states[mapping] = curr
        return False, 0

    def _process_axis_input(self, fname: str, idx: int, joy, mapping: Tuple, prev_states: Dict, input_type: str) -> Tuple[bool, int]:
        """Process axis input for non-lever functions"""
        axis_val = joy.get_axis(idx)
        prev = prev_states.get(mapping, 0)
        
        if input_type == 'momentary':
            curr = 1 if abs(axis_val) > DEADZONE else 0
            if curr != prev:
                prev_states[mapping] = curr
                return True, curr
        elif input_type == 'toggle':
            curr = 1 if abs(axis_val) > DEADZONE else 0
            if curr and not prev:
                prev_states[mapping] = curr
                return True, 1
        
        prev_states[mapping] = prev
        return False, 0

if __name__ == "__main__":
    root = tk.Tk()
    app = InputMapperApp(root)
    root.mainloop()
