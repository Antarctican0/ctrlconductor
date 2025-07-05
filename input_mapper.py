import tkinter as tk
from tkinter import messagebox
import pygame
import socket
import threading
import csv
import os

# UDP settings
default_ip = '127.0.0.1'
default_port = 18888

class InputMapperApp:
    def __init__(self, master):
        self.master = master
        master.title("Run8 Control Conductor")

        # --- DARK THEME COLORS ---
        self._DARK_BG = '#23272e'
        self._DARK_FG = '#e6e6e6'
        self._DARK_ACCENT = '#3a3f4b'
        self._DARK_HIGHLIGHT = '#4f5666'
        self._DARK_BUTTON_BG = '#353b45'
        self._DARK_BUTTON_FG = '#e6e6e6'
        self._DARK_ENTRY_BG = '#2c313a'
        self._DARK_ENTRY_FG = '#e6e6e6'
        # Set main window background
        master.configure(bg=self._DARK_BG)
        self._LIGHT_BG = '#2c313a'  # lighter gray for label backgrounds
        self._label_kwargs = {'bg': self._LIGHT_BG, 'fg': self._DARK_FG}
        self._entry_kwargs = {'bg': self._DARK_ENTRY_BG, 'fg': self._DARK_ENTRY_FG, 'insertbackground': self._DARK_ENTRY_FG, 'highlightbackground': self._DARK_HIGHLIGHT, 'highlightcolor': self._DARK_HIGHLIGHT}
        self._button_kwargs = {'bg': self._DARK_BUTTON_BG, 'fg': self._DARK_BUTTON_FG, 'activebackground': self._DARK_HIGHLIGHT, 'activeforeground': self._DARK_FG, 'relief': 'flat'}
        self._check_kwargs = {'bg': self._DARK_BG, 'fg': self._DARK_FG, 'activebackground': self._DARK_BG, 'activeforeground': self._DARK_FG, 'selectcolor': self._DARK_ACCENT}


        # Hard-coded function mappings from CSV
        self.function_list = [
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
        # Define expected input type for each function
        # 'momentary' = send both press (1) and release (0), 'toggle' = send on change, 'lever' = send on axis move
        self.function_input_type = {
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
            'EOT Emg Stop': 'toggle',
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
            # Add more as needed
        }
        # For multi-way toggle state tracking (function_name -> state)
        self.multiway_states = {'Distance Counter': 0, 'Headlight_Front': 0, 'Headlight_Rear': 0, 'Wiper Switch': 0}
        self.function_dict = {name: ushort for name, ushort in self.function_list}
        # self.load_function_csv()  # No longer needed


        self.ip_label = tk.Label(master, text="Simulator IP:", **self._label_kwargs)
        self.ip_label.pack()
        self.ip_entry = tk.Entry(master, **self._entry_kwargs)
        self.ip_entry.insert(0, default_ip)
        self.ip_entry.pack()

        self.port_label = tk.Label(master, text="Simulator Port:", **self._label_kwargs)
        self.port_label.pack()
        self.port_entry = tk.Entry(master, **self._entry_kwargs)
        self.port_entry.insert(0, str(default_port))
        self.port_entry.pack()

        # Device selection
        self.device_frame = tk.LabelFrame(master, text="Input Devices", bg=self._LIGHT_BG, fg=self._DARK_FG, bd=2, relief='groove', labelanchor='nw')
        self.device_frame.pack(pady=10, fill="x")
        self.device_vars = []
        self.device_checkboxes = []
        # Mapping frame and widgets must be defined before refresh_devices
        import tkinter.ttk as ttk
        self.mapping_frame = tk.LabelFrame(master, text="Input Mapping", bg=self._DARK_ACCENT, fg=self._DARK_FG, bd=2, relief='groove', labelanchor='nw')
        self.mapping_frame.pack(pady=10, fill="both", expand=True)

        # --- DARK THEME FOR TTK NOTEBOOK (tabs) ---
        style = ttk.Style()
        try:
            style.theme_use('default')
        except Exception:
            pass
        style.configure('TNotebook', background=self._DARK_ACCENT, borderwidth=0)
        style.configure('TNotebook.Tab', background=self._DARK_BG, foreground=self._DARK_FG, lightcolor=self._DARK_ACCENT, borderwidth=1, focusthickness=2, focuscolor=self._DARK_HIGHLIGHT)
        style.map('TNotebook.Tab', background=[('selected', self._DARK_ACCENT)], foreground=[('selected', self._DARK_FG)])
        self.mapping_widgets = []  # To clear/rebuild as needed
        self.mapping_labels = []   # For updating mapped input display
        self.mapping_buttons = []  # For enabling/disabling map buttons
        self.function_label_map = {}  # function_name -> label_widget
        # self.audio_vars = {}  # function_name -> tk.BooleanVar for audio flag (removed)
        self.function_input_map = {}  # function_name -> (device_idx, input_type, input_idx)
        self.mapping_save_path = os.path.join(os.path.dirname(__file__), 'input_mappings.csv')
        self.load_mappings()
        self.reverse_axis_vars = {}  # function_name -> tk.BooleanVar for axis reversal (lever only)
        self.mapping_prompt = tk.StringVar(value="Click 'Map Input' to assign a function.")
        self.prompt_label = tk.Label(self.mapping_frame, textvariable=self.mapping_prompt, fg="#7ecfff", bg=self._DARK_ACCENT)
        self.prompt_label.pack(anchor="w", pady=(0, 5))
        self.tabs = ttk.Notebook(self.mapping_frame)
        self.tabs.pack(fill="both", expand=True)
        # Define categories
        self.function_categories = {
            "Main Controls": [
                "Throttle Lever", "Train Brake Lever", "Independent Brake Lever", "Dyn Brake Lever", "Reverser Lever", "Sander", "Horn", "Bell", "Alerter"
            ],
            "Lights and Wipers": [
                "Headlight_Front", "Headlight_Rear", "Wiper Switch", "Cab Light Switch", "Step Light Switch", "Gauge Light Switch"
            ],
            "DPU": [
                "DPU Throttle Increase", "DPU Throttle Decrease", "DPU Dyn-Brake Setup", "DPU Fence Increase", "DPU Fence Decrease"
            ],
            "Misc": [
                "EOT Emg Stop", "HEP Switch", "SlowSpeedOnOff", "Slow Speed Increment", "Slow Speed Decrement", "Independent Bailoff", "Distance Counter", "Park-Brake Set", "Park-Brake Release"
            ]
        }
        self.category_frames = {}
        for cat in self.function_categories:
            frame = tk.Frame(self.tabs)
            self.tabs.add(frame, text=cat)
            self.category_frames[cat] = frame
        self.build_mapping_ui()
        self.refresh_devices_button = tk.Button(self.device_frame, text="Refresh Devices", command=self.refresh_devices, **self._button_kwargs)
        self.refresh_devices_button.pack(anchor="w")
        self.devices_list_frame = tk.Frame(self.device_frame, bg=self._LIGHT_BG)
        self.devices_list_frame.pack(anchor="w", fill="x")
        self.refresh_devices()



        self.start_button = tk.Button(master, text="Start UDP", command=self.start_mapping, **self._button_kwargs)
        self.start_button.pack(pady=10)

        self.status_label = tk.Label(master, text="Status: Waiting to start...", **self._label_kwargs)
        self.status_label.pack()


        self.running = False
        self.sock = None
        self.input_thread = None



    def refresh_devices(self):
        # Clear previous checkboxes
        for cb in self.device_checkboxes:
            cb.destroy()
        self.device_vars.clear()
        self.device_checkboxes.clear()
        # Detect devices
        pygame.init()
        pygame.joystick.init()
        num_devices = pygame.joystick.get_count()
        for i in range(num_devices):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(self.devices_list_frame, text=joy.get_name(), variable=var, **self._check_kwargs)
            cb.pack(anchor="w")
            self.device_vars.append(var)
            self.device_checkboxes.append(cb)
        # Rebuild mapping UI
        self.build_mapping_ui()

    def build_mapping_ui(self):
        # Clear previous widgets
        for widget in self.mapping_widgets:
            widget.destroy()
        self.mapping_widgets.clear()
        for label in self.mapping_labels:
            label.destroy()
        self.mapping_labels.clear()
        for btn in self.mapping_buttons:
            btn.destroy()
        self.mapping_buttons.clear()
        for frame in self.category_frames.values():
            for child in frame.winfo_children():
                child.destroy()
        # For each category, build a table
        for cat, funclist in self.function_categories.items():
            frame = self.category_frames[cat]
            frame.configure(bg=self._DARK_ACCENT)
            tk.Label(frame, text="Function", font=("Arial", 10, "bold"), **self._label_kwargs).grid(row=0, column=0, sticky="w", padx=4)
            tk.Label(frame, text="Mapped Input", font=("Arial", 10, "bold"), **self._label_kwargs).grid(row=0, column=1, sticky="w", padx=4)
            tk.Label(frame, text="Reverse Axis", font=("Arial", 10, "bold"), **self._label_kwargs).grid(row=0, column=2, sticky="w", padx=4)
            tk.Label(frame, text="", font=("Arial", 10, "bold"), **self._label_kwargs).grid(row=0, column=3, sticky="w", padx=4)
            for idx, fname in enumerate(funclist):
                ushort = self.function_dict[fname]
                row = idx + 1
                label = tk.Label(frame, text=fname, **self._label_kwargs)
                label.grid(row=row, column=0, sticky="w", padx=4, pady=2)
                mapped = tk.Label(frame, text="Not mapped", fg="#888", bg=self._LIGHT_BG)
                mapped.grid(row=row, column=1, sticky="w", padx=4, pady=2)
                self.function_label_map[fname] = mapped
                # Add reverse axis checkbox for levers only
                reverse_cb = None
                if self.function_input_type.get(fname) == 'lever':
                    rev_var = self.reverse_axis_vars.get(fname)
                    if not rev_var:
                        rev_var = tk.BooleanVar(value=False)
                        self.reverse_axis_vars[fname] = rev_var
                    reverse_cb = tk.Checkbutton(frame, variable=rev_var, **self._check_kwargs)
                    reverse_cb.grid(row=row, column=2, padx=4, pady=2)
                    self.mapping_widgets.append(reverse_cb)
                btn = tk.Button(frame, text="Map Input", command=lambda f=fname, l=mapped: self.start_input_mapping(f, l),
                                bg=self._DARK_BUTTON_BG, fg=self._DARK_BUTTON_FG, activebackground=self._DARK_HIGHLIGHT, activeforeground=self._DARK_FG,
                                relief='groove', bd=2, highlightbackground=self._DARK_HIGHLIGHT, highlightcolor=self._DARK_HIGHLIGHT)
                btn.grid(row=row, column=3, padx=4, pady=2)
                self.mapping_labels.append(mapped)
                self.mapping_buttons.append(btn)
                self.mapping_widgets.extend([label, mapped, btn])
                # Show current mapping if exists
                if fname in self.function_input_map:
                    mapping = self.function_input_map[fname]
                    if isinstance(mapping, tuple) and len(mapping) == 4 and mapping[1] == 'Hat':
                        dev, _, hat_idx, dir_name = mapping
                        mapped.config(text=f"Hat {hat_idx} {dir_name} (Device {dev})", fg=self._DARK_FG, bg=self._LIGHT_BG)
                    else:
                        dev, typ, idx = mapping
                        mapped.config(text=f"{typ} {idx} (Device {dev})", fg=self._DARK_FG, bg=self._LIGHT_BG)
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
        pygame.init()
        pygame.joystick.init()
        enabled_indices = [i for i, var in enumerate(self.device_vars) if var.get()]
        if not enabled_indices:
            self.mapping_prompt.set("No input devices enabled.")
            for btn in self.mapping_buttons:
                btn.config(state="normal")
            return
        joysticks = [pygame.joystick.Joystick(i) for i in enabled_indices]
        for joy in joysticks:
            joy.init()
        DEADZONE = 0.7
        # Remove this input from any other function before mapping
        def remove_input_from_others(mapping_tuple, target_function):
            to_remove = []
            for fname, mapping in self.function_input_map.items():
                if mapping == mapping_tuple and fname != target_function:
                    to_remove.append(fname)
            for fname in to_remove:
                del self.function_input_map[fname]
                if fname in self.function_label_map:
                    self.function_label_map[fname].config(text="Not mapped", fg="gray")

        import time
        release_timeout = 0.15  # seconds (was 1.0)
        release_start = time.time()
        while True:
            pygame.event.pump()
            all_released = True
            for j, joy in enumerate(joysticks):
                for a in range(joy.get_numaxes()):
                    if abs(joy.get_axis(a)) > DEADZONE:
                        all_released = False
                        break
                for b in range(joy.get_numbuttons()):
                    if joy.get_button(b):
                        all_released = False
                        break
                if not all_released:
                    break
            if all_released or (time.time() - release_start > release_timeout):
                break
            pygame.time.wait(2)
        # Record initial state after release phase
        pygame.event.pump()
        initial_axes = []
        initial_buttons = []
        initial_hats = []
        for joy in joysticks:
            initial_axes.append([joy.get_axis(a) for a in range(joy.get_numaxes())])
            initial_buttons.append([joy.get_button(b) for b in range(joy.get_numbuttons())])
            initial_hats.append([joy.get_hat(h) for h in range(joy.get_numhats())])
        # Now wait for a new axis/button movement (must cross deadzone or change from initial)
        found = False
        while not found:
            pygame.event.pump()
            for idx, (dev_idx, joy) in enumerate(zip(enabled_indices, joysticks)):
                # Check axes
                for axis in range(joy.get_numaxes()):
                    val = joy.get_axis(axis)
                    if abs(val) > DEADZONE and abs(val - initial_axes[idx][axis]) > 0.1:
                        mapping_tuple = (dev_idx, 'Axis', axis)
                        remove_input_from_others(mapping_tuple, self.input_map_target[0])
                        self.set_input_mapping(self.input_map_target[0], mapping_tuple, self.input_map_target[1])
                        found = True
                        break
                if found:
                    break
                # Check buttons
                for btn in range(joy.get_numbuttons()):
                    if joy.get_button(btn) and not initial_buttons[idx][btn]:
                        mapping_tuple = (dev_idx, 'Button', btn)
                        remove_input_from_others(mapping_tuple, self.input_map_target[0])
                        self.set_input_mapping(self.input_map_target[0], mapping_tuple, self.input_map_target[1])
                        found = True
                        break
                if found:
                    break
                # Check hats (D-Pad directions)
                for h in range(joy.get_numhats()):
                    hat_val = joy.get_hat(h)
                    prev_hat = initial_hats[idx][h]
                    directions = [(0,1), (0,-1), (1,0), (-1,0)]
                    dir_names = ['Up', 'Down', 'Right', 'Left']
                    for d, dname in zip(directions, dir_names):
                        if hat_val == d and prev_hat != d:
                            mapping_tuple = (dev_idx, 'Hat', h, dname)
                            remove_input_from_others(mapping_tuple, self.input_map_target[0])
                            self.set_input_mapping(self.input_map_target[0], mapping_tuple, self.input_map_target[1])
                            found = True
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                break
            pygame.time.wait(20)
        self.mapping_prompt.set("Click 'Map Input' to assign a function.")
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
        try:
            with open(self.mapping_save_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for fname, mapping in self.function_input_map.items():
                    # mapping can be (dev_idx, typ, idx) or (dev_idx, 'Hat', hat_idx, dir_name)
                    writer.writerow([fname] + list(mapping))
        except Exception as e:
            print(f"Error saving mappings: {e}")

    def load_mappings(self):
        if not os.path.exists(self.mapping_save_path):
            return
        try:
            with open(self.mapping_save_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4 and row[2] == 'Hat':
                        # (dev_idx, 'Hat', hat_idx, dir_name)
                        fname = row[0]
                        dev_idx = int(row[1])
                        typ = row[2]
                        hat_idx = int(row[3])
                        dir_name = row[4]
                        self.function_input_map[fname] = (dev_idx, typ, hat_idx, dir_name)
                    elif len(row) >= 3:
                        fname = row[0]
                        dev_idx = int(row[1])
                        typ = row[2]
                        idx = int(row[3]) if len(row) > 3 else 0
                        self.function_input_map[fname] = (dev_idx, typ, idx)
        except Exception as e:
            print(f"Error loading mappings: {e}")
        # After loading, update the UI if possible
        if hasattr(self, 'function_label_map'):
            for fname, mapping in self.function_input_map.items():
                label = self.function_label_map.get(fname)
                if label:
                    if isinstance(mapping, tuple) and len(mapping) == 4 and mapping[1] == 'Hat':
                        dev_idx, _, hat_idx, dir_name = mapping
                        label.config(text=f"Hat {hat_idx} {dir_name} (Device {dev_idx})", fg="black")
                    else:
                        dev_idx, typ, idx = mapping
                        label.config(text=f"{typ} {idx} (Device {dev_idx})", fg="black")

    def start_mapping(self):
    # Removed stop_mapping method
        ip = self.ip_entry.get()
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Port must be a number.")
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target = (ip, port)
        self.running = True
        self.status_label.config(text="Status: Mapping started!")
        # Get enabled device indices
        self.enabled_devices = [i for i, var in enumerate(self.device_vars) if var.get()]
        if not self.enabled_devices:
            messagebox.showerror("Error", "No input devices enabled.")
            self.running = False
            return
        self.input_thread = threading.Thread(target=self.input_loop, daemon=True)
        self.input_thread.start()

    def input_loop(self):
        import struct
        pygame.init()
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            self.status_label.config(text="No joystick/gamepad detected.")
            return
        # Use all enabled devices
        joysticks = []
        for idx in self.enabled_devices:
            joy = pygame.joystick.Joystick(idx)
            joy.init()
            joysticks.append(joy)
        self.status_label.config(text=f"Using: {', '.join(j.get_name() for j in joysticks)}")
        # Track previous state for each mapped input
        prev_states = {}

        while self.running:
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
                # mapping: (dev_idx, typ, idx) or (dev_idx, 'Hat', hat_idx, dir_name)
                send = False
                value = 0
                if isinstance(mapping, tuple) and len(mapping) == 4 and mapping[1] == 'Hat':
                    dev_idx, _, hat_idx, dir_name = mapping
                    if dev_idx >= len(joysticks):
                        continue
                    joy = joysticks[self.enabled_devices.index(dev_idx)]
                    hat_val = joy.get_hat(hat_idx)
                    # Map direction to value: Up=(0,1), Down=(0,-1), Right=(1,0), Left=(-1,0)
                    dir_map = {'Up': (0,1), 'Down': (0,-1), 'Right': (1,0), 'Left': (-1,0)}
                    dtuple = dir_map[dir_name]
                    curr = 1 if hat_val == dtuple else 0
                    prev = prev_states.get(mapping, 0)
                    input_type = self.function_input_type.get(fname, 'toggle')
                    # Support 3way/4way toggles for hats as well as buttons
                    if fname in self.multiway_states and input_type in ('3way', '4way'):
                        num_states = 3 if input_type == '3way' else 4
                        if curr and not prev:
                            self.multiway_states[fname] = (self.multiway_states.get(fname, 0) + 1) % num_states
                            value = self.multiway_states[fname]
                            send = True
                        prev_states[mapping] = curr
                    elif input_type == 'momentary':
                        if curr != prev:
                            value = curr
                            send = True
                        prev_states[mapping] = curr
                    else:
                        if curr and not prev:
                            value = 1
                            send = True
                        prev_states[mapping] = curr
                else:
                    dev_idx, typ, idx = mapping
                    if dev_idx >= len(joysticks):
                        continue
                    joy = joysticks[self.enabled_devices.index(dev_idx)]
                    input_type = self.function_input_type.get(fname, 'toggle')
                    # ...existing code for buttons/axes/levers...
                    # Special handling for multi-way toggles (3-way and 4-way)
                    if fname in self.multiway_states and input_type in ('3way', '4way') and typ == 'Button':
                        curr = 1 if joy.get_button(idx) else 0
                        prev = prev_states.get(mapping, 0)
                        num_states = 3 if input_type == '3way' else 4
                        if curr and not prev:
                            self.multiway_states[fname] = (self.multiway_states.get(fname, 0) + 1) % num_states
                            value = self.multiway_states[fname]
                            send = True
                        prev_states[mapping] = curr
                    elif fname == 'Throttle Lever' and typ == 'Axis':
                        axis_val = joy.get_axis(idx)
                        rev = self.reverse_axis_vars.get(fname, tk.BooleanVar(value=False)).get()
                        if rev:
                            axis_val = -axis_val
                        axis_val = max(-1.0, min(1.0, axis_val))
                        notch = int(round(((axis_val + 1.0) / 2.0) * 8))
                        notch = max(0, min(8, notch))
                        prev_notch = prev_states.get(mapping, -1)
                        if notch != prev_notch:
                            value = notch
                            send = True
                            prev_states[mapping] = notch
                    elif fname == 'Reverser Lever' and typ == 'Axis':
                        axis_val = joy.get_axis(idx)
                        rev = self.reverse_axis_vars.get(fname, tk.BooleanVar(value=False)).get()
                        if rev:
                            axis_val = -axis_val
                        axis_val = max(-1.0, min(1.0, axis_val))
                        if axis_val <= -0.33:
                            reverser_val = 0
                        elif axis_val >= 0.33:
                            reverser_val = 255
                        else:
                            reverser_val = 127
                        prev_reverser = prev_states.get(mapping, -1)
                        if reverser_val != prev_reverser:
                            value = reverser_val
                            send = True
                            prev_states[mapping] = reverser_val
                    elif fname in ('Independent Brake Lever', 'Train Brake Lever', 'Dyn Brake Lever') and typ == 'Axis':
                        axis_val = joy.get_axis(idx)
                        rev = self.reverse_axis_vars.get(fname, tk.BooleanVar(value=False)).get()
                        if rev:
                            axis_val = -axis_val
                        axis_val = max(-1.0, min(1.0, axis_val))
                        if fname == 'Dyn Brake Lever':
                            # Use threshold for "off" (axis <= -0.95)
                            if axis_val <= -0.95:
                                dyn_val = 0
                            else:
                                # Remap axis from (-0.95, 1.0) to (1, 255)
                                norm = (axis_val - (-0.95)) / (1.0 - (-0.95))
                                norm = max(0.0, min(1.0, norm))
                                dyn_val = int(round(norm * 254)) + 1  # 1–255
                            prev_dyn = prev_states.get(mapping, -1)
                            if dyn_val != prev_dyn:
                                value = dyn_val
                                send = True
                                prev_states[mapping] = dyn_val
                        else:
                            # Brake levers: 0-255
                            brake_val = int(round(((axis_val + 1.0) / 2.0) * 255))
                            brake_val = max(0, min(255, brake_val))
                            prev_brake = prev_states.get(mapping, -1)
                            if brake_val != prev_brake:
                                value = brake_val
                                send = True
                                prev_states[mapping] = brake_val
                    # Axis/button handling for non-lever/toggle functions (momentary/toggle, 3way/4way)
                    elif typ == 'Button':
                        curr = 1 if joy.get_button(idx) else 0
                        prev = prev_states.get(mapping, 0)
                        if input_type == 'momentary':
                            if curr != prev:
                                value = curr
                                send = True
                        elif input_type in ('toggle',):
                            if curr and not prev:
                                value = 1
                                send = True
                        prev_states[mapping] = curr
                    elif typ == 'Axis' and fname not in ('Throttle Lever', 'Dyn Brake Lever', 'Train Brake Lever', 'Independent Brake Lever', 'Reverser Lever'):
                        axis_val = joy.get_axis(idx)
                        prev = prev_states.get(mapping, 0)
                        if input_type == 'momentary':
                            curr = 1 if abs(axis_val) > 0.7 else 0
                            if curr != prev:
                                value = curr
                                send = True
                            prev_states[mapping] = curr
                        elif input_type in ('toggle',):
                            curr = 1 if abs(axis_val) > 0.7 else 0
                            if curr and not prev:
                                value = 1
                                send = True
                            prev_states[mapping] = curr
                    # 3way/4way toggles (button only)
                    if fname in self.multiway_states and input_type in ('3way', '4way') and typ == 'Button':
                        curr = 1 if joy.get_button(idx) else 0
                        prev = prev_states.get(mapping, 0)
                        num_states = 3 if input_type == '3way' else 4
                        if curr and not prev:
                            self.multiway_states[fname] = (self.multiway_states.get(fname, 0) + 1) % num_states
                            value = self.multiway_states[fname]
                            send = True
                        prev_states[mapping] = curr
                if send:
                    header = 0x60 | 0x80  # Always set audio flag (MSB)
                    ushort = self.function_dict[fname]
                    msg_bytes = bytearray()
                    msg_bytes.append(header)
                    msg_bytes.append((ushort >> 8) & 0xFF)
                    msg_bytes.append(ushort & 0xFF)
                    # Special handling for Throttle Lever: map axis to 0-8 (0=Notch 1, 8=Idle), with reverse option
                    if fname == "Throttle Lever" and ((isinstance(mapping, tuple) and len(mapping) == 3 and mapping[1] == 'Axis') or (len(mapping) == 4 and mapping[1] == 'Axis')):
                        axis_val = joy.get_axis(idx)
                        rev = self.reverse_axis_vars.get(fname, tk.BooleanVar(value=False)).get()
                        if rev:
                            axis_val = -axis_val
                        axis_val = max(-1.0, min(1.0, axis_val))
                        notch = int(round(((axis_val + 1.0) / 2.0) * 8))
                        notch = max(0, min(8, notch))
                        msg_bytes.append(notch)
                    elif fname == "Reverser Lever" and ((isinstance(mapping, tuple) and len(mapping) == 3 and mapping[1] == 'Axis') or (len(mapping) == 4 and mapping[1] == 'Axis')):
                        axis_val = joy.get_axis(idx)
                        rev = self.reverse_axis_vars.get(fname, tk.BooleanVar(value=False)).get()
                        if rev:
                            axis_val = -axis_val
                        axis_val = max(-1.0, min(1.0, axis_val))
                        if axis_val <= -0.33:
                            reverser_val = 0
                        elif axis_val >= 0.33:
                            reverser_val = 255
                        else:
                            reverser_val = 127
                        msg_bytes.append(reverser_val)
                    elif fname in ('Independent Brake Lever', 'Train Brake Lever', 'Dyn Brake Lever') and ((isinstance(mapping, tuple) and len(mapping) == 3 and mapping[1] == 'Axis') or (len(mapping) == 4 and mapping[1] == 'Axis')):
                        axis_val = joy.get_axis(idx)
                        rev = self.reverse_axis_vars.get(fname, tk.BooleanVar(value=False)).get()
                        if rev:
                            axis_val = -axis_val
                        axis_val = max(-1.0, min(1.0, axis_val))
                        if fname == 'Dyn Brake Lever':
                            # Use threshold for "off" (axis <= -0.95)
                            if axis_val <= -0.95:
                                dyn_val = 0
                            else:
                                norm = (axis_val - (-0.95)) / (1.0 - (-0.95))
                                norm = max(0.0, min(1.0, norm))
                                dyn_val = int(round(norm * 254)) + 1  # 1–255
                            msg_bytes.append(dyn_val)
                        else:
                            brake_val = int(round(((axis_val + 1.0) / 2.0) * 255))
                            brake_val = max(0, min(255, brake_val))
                            msg_bytes.append(brake_val)
                    else:
                        msg_bytes.append(value)
                    crc = msg_bytes[0] ^ msg_bytes[1] ^ msg_bytes[2] ^ msg_bytes[3]
                    msg_bytes.append(crc)
                    self.sock.sendto(msg_bytes, self.target)
            pygame.time.wait(50)  # 20 times per second

if __name__ == "__main__":
    root = tk.Tk()
    app = InputMapperApp(root)
    root.mainloop()
