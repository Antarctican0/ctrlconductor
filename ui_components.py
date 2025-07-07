"""
UI components module for Run8 Control Conductor

Handles all UI creation, management, and theming for the main application window.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import tkinter.ttk as ttk
from typing import Dict, List, Callable, Optional, Any
import logging

from config import ThemeConfig, FunctionMapping

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UIManager:
    """Manages the main UI components and theming"""
    
    def __init__(self, master: tk.Tk):
        """
        Initialize the UI manager
        
        Args:
            master: Main tkinter window
        """
        self.master = master
        self.theme = ThemeConfig()
        self.function_categories = FunctionMapping.CATEGORIES
        
        # UI element references
        self.ip_entry: Optional[tk.Entry] = None
        self.port_entry: Optional[tk.Entry] = None
        self.device_vars: List[tk.BooleanVar] = []
        self.device_checkboxes: List[tk.Checkbutton] = []
        self.reverse_axis_vars: Dict[str, tk.BooleanVar] = {}
        self.reverse_axis_checkboxes: Dict[str, tk.Checkbutton] = {}  # Store checkbox references
        self.mapping_labels: Dict[str, tk.Label] = {}
        self.mapping_buttons: Dict[str, tk.Button] = {}
        self.mapping_prompt: Optional[tk.StringVar] = None
        self.prompt_label: Optional[tk.Label] = None
        self.tabs: Optional[ttk.Notebook] = None
        self.category_frames: Dict[str, tk.Frame] = {}
        self.function_frames: List[tk.Frame] = []  # Add missing attribute
        
        # Button references
        self.start_button: Optional[tk.Button] = None
        self.stop_button: Optional[tk.Button] = None
        self.refresh_devices_button: Optional[tk.Button] = None
        self.load_mappings_button: Optional[tk.Button] = None
        self.save_mappings_button: Optional[tk.Button] = None
        self.clear_mappings_button: Optional[tk.Button] = None
        
        # Callback functions
        self.on_start_callback: Optional[Callable] = None
        self.on_stop_callback: Optional[Callable] = None
        self.on_refresh_devices_callback: Optional[Callable] = None
        self.on_load_mappings_callback: Optional[Callable] = None
        self.on_save_mappings_callback: Optional[Callable] = None
        self.on_clear_mappings_callback: Optional[Callable] = None
        self.on_device_toggle_callback: Optional[Callable] = None
        self.on_map_input_callback: Optional[Callable] = None
        self.on_clear_mapping_callback: Optional[Callable] = None
        self.reverser_mode_callback = None
        
        # Setup UI
        self._setup_ui_theme()
        self._setup_main_layout()
    
    def _setup_ui_theme(self) -> None:
        """Setup UI theme colors and styles"""
        self.master.configure(bg=self.theme.DARK_BG)
        
        # Setup TTK styles
        self._setup_ttk_style()
    
    def _setup_ttk_style(self) -> None:
        """Setup TTK notebook style for dark theme"""
        style = ttk.Style()
        try:
            style.theme_use('default')
            style.configure('TNotebook', background=self.theme.DARK_ACCENT)
            style.configure('TNotebook.Tab', background=self.theme.DARK_BUTTON_BG, 
                          foreground=self.theme.DARK_FG, padding=[10, 5])
            style.map('TNotebook.Tab', background=[('selected', self.theme.DARK_HIGHLIGHT)])
        except Exception as e:
            logger.warning(f"Failed to setup TTK style: {e}")
    
    def _setup_main_layout(self) -> None:
        """Setup the main window layout"""
        self.master.title("Run8 Control Conductor")
        self.master.geometry("800x600")
        
        # Create main sections
        self._create_connection_section()
        self._create_device_section()
        self._create_mapping_section()
        self._create_control_section()
    
    def _create_connection_section(self) -> None:
        """Create the connection configuration section"""
        connection_frame = tk.Frame(self.master, bg=self.theme.DARK_BG)
        connection_frame.pack(pady=5, fill="x")
        
        # IP configuration
        ip_frame = tk.Frame(connection_frame, bg=self.theme.DARK_BG)
        ip_frame.pack(side="left", padx=5)
        
        label = tk.Label(ip_frame, text="Simulator IP:", bg=self.theme.LIGHT_BG, fg=self.theme.DARK_FG)
        label.pack()
        self.ip_entry = tk.Entry(ip_frame, width=15, bg=self.theme.DARK_ENTRY_BG, fg=self.theme.DARK_ENTRY_FG, insertbackground=self.theme.DARK_ENTRY_FG)
        self.ip_entry.pack()
        
        # Port configuration
        port_frame = tk.Frame(connection_frame, bg=self.theme.DARK_BG)
        port_frame.pack(side="left", padx=5)
        
        tk.Label(port_frame, text="Simulator Port:", bg=self.theme.LIGHT_BG, fg=self.theme.DARK_FG).pack()
        self.port_entry = tk.Entry(port_frame, width=10, bg=self.theme.DARK_ENTRY_BG, fg=self.theme.DARK_ENTRY_FG, insertbackground=self.theme.DARK_ENTRY_FG)
        self.port_entry.pack()
    
    def _create_device_section(self) -> None:
        """Create the device selection section"""
        self.device_frame = tk.LabelFrame(
            self.master,
            text="Input Devices",
            bg=self.theme.LIGHT_BG,
            fg=self.theme.DARK_FG,
            bd=2,
            relief=tk.GROOVE,  # Use tk.GROOVE constant, not string
            labelanchor="nw"   # Use keyword argument
        )
        self.device_frame.pack(pady=10, fill="x")
        
        # Refresh devices button
        self.refresh_devices_button = tk.Button(
            self.device_frame,
            text="Refresh Devices",
            command=self._on_refresh_devices,
            bg=self.theme.DARK_BUTTON_BG,
            fg=self.theme.DARK_BUTTON_FG,
            activebackground=self.theme.DARK_HIGHLIGHT,
            activeforeground=self.theme.DARK_FG,
            relief=tk.FLAT,
            bd=1
        )
        self.refresh_devices_button.pack(anchor="w", pady=2)
        
        # Devices list frame
        self.devices_list_frame = tk.Frame(self.device_frame, bg=self.theme.LIGHT_BG)
        self.devices_list_frame.pack(anchor="w", fill="x", pady=5)
    
    def _create_mapping_section(self) -> None:
        """Create the input mapping section"""
        self.mapping_frame = tk.LabelFrame(
            self.master,
            text="Input Mapping",
            bg=self.theme.DARK_ACCENT,
            fg=self.theme.DARK_FG,
            bd=2,
            relief=tk.GROOVE,  # Use tk.GROOVE constant
            labelanchor="nw"
        )
        self.mapping_frame.pack(pady=10, fill="both", expand=True)
        
        # Mapping prompt
        self.mapping_prompt = tk.StringVar(value="Click 'Map Input' to assign a function.")
        self.prompt_label = tk.Label(
            self.mapping_frame,
            textvariable=self.mapping_prompt,
            fg="#7ecfff",
            bg=self.theme.DARK_ACCENT
        )
        self.prompt_label.pack(anchor=tk.W, pady=(0, 5))  # Use tk.W constant
        
        # Create tabbed interface
        self.tabs = ttk.Notebook(self.mapping_frame)
        self.tabs.pack(fill="both", expand=True)
        
        # Create category frames
        for category in self.function_categories:
            frame = tk.Frame(self.tabs, bg=self.theme.DARK_ACCENT)
            self.tabs.add(frame, text=category)
            self.category_frames[category] = frame
            
            # Create scrollable frame for this category
            self._create_scrollable_category_frame(category, frame)
        
        # Create reverser mode toggle
        self.reverser_mode_var = tk.BooleanVar(value=False)
        self.reverser_mode_callback = None
        self.reverser_mode_frame = None
        self.reverser_mode_checkbox = None
        
        # Create the reverser mode selection in the mapping section
        self._create_reverser_mode_selector()
    
    def _create_scrollable_category_frame(self, category: str, parent_frame: tk.Frame) -> None:
        """Create a scrollable frame for a function category"""
        # Create canvas and scrollbar
        canvas = tk.Canvas(parent_frame, bg=self.theme.DARK_ACCENT, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.DARK_ACCENT)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store reference to scrollable frame
        self.category_frames[category] = scrollable_frame
        
        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def _create_control_section(self) -> None:
        """Create the control buttons section"""
        control_frame = tk.Frame(self.master, bg=self.theme.DARK_BG)
        control_frame.pack(pady=10, fill="x")
        
        # Start/Stop buttons
        button_frame = tk.Frame(control_frame, bg=self.theme.DARK_BG)
        button_frame.pack(side="left")
        
        self.start_button = tk.Button(
            button_frame,
            text="Start",
            command=self._on_start,
            bg=self.theme.DARK_BUTTON_BG,
            fg=self.theme.DARK_BUTTON_FG,
            activebackground=self.theme.DARK_HIGHLIGHT,
            activeforeground=self.theme.DARK_FG,
            relief=tk.FLAT,
            bd=1
        )
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = tk.Button(
            button_frame,
            text="Stop",
            command=self._on_stop,
            state=tk.DISABLED,
            bg=self.theme.DARK_BUTTON_BG,
            fg=self.theme.DARK_BUTTON_FG,
            activebackground=self.theme.DARK_HIGHLIGHT,
            activeforeground=self.theme.DARK_FG,
            relief=tk.FLAT,
            bd=1
        )
        self.stop_button.pack(side="left", padx=5)
        
        # Mapping control buttons
        mapping_control_frame = tk.Frame(control_frame, bg=self.theme.DARK_BG)
        mapping_control_frame.pack(side="right")
        
        self.load_mappings_button = tk.Button(
            mapping_control_frame,
            text="Load Mappings",
            command=self._on_load_mappings,
            bg=self.theme.DARK_BUTTON_BG,
            fg=self.theme.DARK_BUTTON_FG,
            activebackground=self.theme.DARK_HIGHLIGHT,
            activeforeground=self.theme.DARK_FG,
            relief=tk.FLAT,
            bd=1
        )
        self.load_mappings_button.pack(side="left", padx=2)
        
        self.save_mappings_button = tk.Button(
            mapping_control_frame,
            text="Save Mappings",
            command=self._on_save_mappings,
            bg=self.theme.DARK_BUTTON_BG,
            fg=self.theme.DARK_BUTTON_FG,
            activebackground=self.theme.DARK_HIGHLIGHT,
            activeforeground=self.theme.DARK_FG,
            relief=tk.FLAT,
            bd=1
        )
        self.save_mappings_button.pack(side="left", padx=2)
        
        self.clear_mappings_button = tk.Button(
            mapping_control_frame,
            text="Clear All",
            command=self._on_clear_mappings,
            bg=self.theme.DARK_BUTTON_BG,
            fg=self.theme.DARK_BUTTON_FG,
            activebackground=self.theme.DARK_HIGHLIGHT,
            activeforeground=self.theme.DARK_FG,
            relief=tk.FLAT,
            bd=1
        )
        self.clear_mappings_button.pack(side="left", padx=2)
    
    def _create_reverser_mode_selector(self):
        """Create the reverser mode selection UI elements"""
        self.reverser_mode_frame = ttk.Frame(self.mapping_frame)
        self.reverser_mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(self.reverser_mode_frame, text="Reverser Control Mode:").pack(side=tk.LEFT)
        
        self.reverser_mode_checkbox = ttk.Checkbutton(
            self.reverser_mode_frame,
            text="Use 3-position switch (instead of axis/lever)",
            variable=self.reverser_mode_var,
            command=self._on_reverser_mode_change
        )
        self.reverser_mode_checkbox.pack(side=tk.LEFT, padx=10)
        
        # Add explanation label
        ttk.Label(
            self.reverser_mode_frame, 
            text="(Check this if you want to use buttons instead of a lever for the reverser)",
            font=("TkDefaultFont", 8)
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Separator(self.mapping_frame).pack(fill=tk.X, padx=5, pady=5)
    
    def _on_reverser_mode_change(self):
        """Handle reverser mode toggle change"""
        switch_mode = self.reverser_mode_var.get()
        
        # Show/hide the reverse checkbox for Reverser Lever based on mode
        if "Reverser Lever" in self.reverse_axis_checkboxes:
            reverse_checkbox = self.reverse_axis_checkboxes["Reverser Lever"]
            if switch_mode:
                # Hide reverse checkbox in switch mode
                reverse_checkbox.pack_forget()
            else:
                # Show reverse checkbox in axis mode
                reverse_checkbox.pack(side="left", padx=10)
        
        # Call the main application callback
        if self.reverser_mode_callback:
            self.reverser_mode_callback(switch_mode)
    
    def populate_device_list(self, devices: List[Any]) -> None:
        """
        Populate the device list with checkboxes
        
        Args:
            devices: List of InputDevice objects
        """
        # Clear existing devices
        for widget in self.devices_list_frame.winfo_children():
            widget.destroy()
        self.device_vars.clear()
        self.device_checkboxes.clear()
        
        # Add new devices
        for i, device in enumerate(devices):
            var = tk.BooleanVar()
            checkbox = tk.Checkbutton(
                self.devices_list_frame,
                text=f"{i}: {device.name}",
                variable=var,
                command=lambda idx=i: self._on_device_toggle(idx),
                bg=self.theme.DARK_BG,
                fg=self.theme.DARK_FG,
                activebackground=self.theme.DARK_BG,
                activeforeground=self.theme.DARK_FG,
                selectcolor=self.theme.DARK_ACCENT
            )
            checkbox.pack(anchor=tk.W)  # Use tk.W constant
            
            self.device_vars.append(var)
            self.device_checkboxes.append(checkbox)
    
    def populate_mapping_interface(self, functions: List[str]) -> None:
        """
        Populate the mapping interface with function controls
        
        Args:
            functions: List of function names to create controls for
        """
        # Clear existing mappings
        self.mapping_labels.clear()
        self.mapping_buttons.clear()
        self.reverse_axis_vars.clear()
        
        # Clear category frames
        for frame in self.category_frames.values():
            for widget in frame.winfo_children():
                widget.destroy()
        
        # Create controls for each function, organized by category order
        for category, category_functions in self.function_categories.items():
            if category not in self.category_frames:
                continue
                
            frame = self.category_frames[category]
            for function_name in category_functions:
                if function_name in functions:
                    self._create_function_controls(frame, function_name)
    
    def _get_function_category(self, function_name: str) -> str:
        """Get the category for a function name"""
        for category, functions in self.function_categories.items():
            if function_name in functions:
                return category
        return "Misc"  # Default category
    
    def _create_function_controls(self, parent_frame: tk.Frame, function_name: str) -> None:
        """Create controls for a single function"""
        func_frame = tk.Frame(parent_frame, bg=self.theme.DARK_ACCENT)
        func_frame.pack(fill="x", pady=2)

        name_label = tk.Label(
            func_frame,
            text=function_name,
            width=25,
            anchor=tk.W,
            bg=self.theme.LIGHT_BG,
            fg=self.theme.DARK_FG
        )
        name_label.pack(side="left", padx=5)

        status_label = tk.Label(
            func_frame,
            text="Not mapped",
            width=20,
            anchor=tk.W,  # Use tk.W constant
            bg=self.theme.DARK_ENTRY_BG,
            fg=self.theme.DARK_ENTRY_FG
        )
        status_label.pack(side="left", padx=5)
        self.mapping_labels[function_name] = status_label

        input_type = FunctionMapping.INPUT_TYPES.get(function_name, 'toggle')
        if input_type == 'lever':
            reverse_var = tk.BooleanVar()
            reverse_checkbox = tk.Checkbutton(
                func_frame,
                text="Reverse",
                variable=reverse_var,
                bg=self.theme.DARK_BG,
                fg=self.theme.DARK_FG,
                activebackground=self.theme.DARK_BG,
                activeforeground=self.theme.DARK_FG,
                selectcolor=self.theme.DARK_ACCENT
            )
            reverse_checkbox.pack(side="left", padx=10)
            self.reverse_axis_vars[function_name] = reverse_var
            self.reverse_axis_checkboxes[function_name] = reverse_checkbox
            
            # Hide reverse checkbox for Reverser Lever if in switch mode
            if function_name == "Reverser Lever" and self.reverser_mode_var.get():
                reverse_checkbox.pack_forget()

        buttons_frame = tk.Frame(func_frame, bg=self.theme.DARK_ACCENT)
        buttons_frame.pack(side="right", padx=5)

        map_button = tk.Button(
            buttons_frame,
            text="Map Input",
            command=lambda fn=function_name: self._on_map_input(fn),
            bg=self.theme.DARK_BUTTON_BG,
            fg=self.theme.DARK_BUTTON_FG,
            activebackground=self.theme.DARK_HIGHLIGHT,
            activeforeground=self.theme.DARK_FG,
            relief=tk.FLAT,
            bd=1
        )
        map_button.pack(side="left", padx=2)
        self.mapping_buttons[function_name] = map_button

        clear_button = tk.Button(
            buttons_frame,
            text="Clear",
            command=lambda fn=function_name: self._on_clear_mapping(fn),
            bg=self.theme.DARK_BUTTON_BG,
            fg=self.theme.DARK_BUTTON_FG,
            activebackground=self.theme.DARK_HIGHLIGHT,
            activeforeground=self.theme.DARK_FG,
            relief=tk.FLAT,
            bd=1
        )
        clear_button.pack(side="left", padx=2)

    def update_mapping_display(self, function_name: str, mapping_text: str) -> None:
        """Update the display text for a function mapping"""
        if function_name in self.mapping_labels:
            self.mapping_labels[function_name].config(text=mapping_text)
    
    def set_mapping_prompt(self, text: str) -> None:
        """Set the mapping prompt text"""
        if self.mapping_prompt:
            self.mapping_prompt.set(text)
    
    def get_ip_address(self) -> str:
        """Get the IP address from the entry field"""
        return self.ip_entry.get() if self.ip_entry else ""
    
    def get_port(self) -> int:
        """Get the port from the entry field"""
        try:
            return int(self.port_entry.get()) if self.port_entry else 0
        except ValueError:
            return 0
    
    def set_ip_address(self, ip: str) -> None:
        """Set the IP address in the entry field"""
        if self.ip_entry:
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, ip)
    
    def set_port(self, port: int) -> None:
        """Set the port in the entry field"""
        if self.port_entry:
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, str(port))
    
    def get_enabled_devices(self) -> List[int]:
        """Get list of enabled device indices"""
        return [i for i, var in enumerate(self.device_vars) if var.get()]
    
    def set_device_enabled(self, device_index: int, enabled: bool) -> None:
        """Set the enabled state of a device"""
        if 0 <= device_index < len(self.device_vars):
            self.device_vars[device_index].set(enabled)
    
    def get_reverse_axis_setting(self, function_name: str) -> bool:
        """Get the reverse axis setting for a function"""
        if function_name in self.reverse_axis_vars:
            return self.reverse_axis_vars[function_name].get()
        return False
    
    def set_reverse_axis_setting(self, function_name: str, reverse: bool) -> None:
        """Set the reverse axis setting for a function"""
        if function_name in self.reverse_axis_vars:
            self.reverse_axis_vars[function_name].set(reverse)
    
    def enable_start_button(self) -> None:
        """Enable the start button"""
        if self.start_button:
            self.start_button.config(state=tk.NORMAL)  # Use tk.NORMAL constant
    
    def disable_start_button(self) -> None:
        """Disable the start button"""
        if self.start_button:
            self.start_button.config(state=tk.DISABLED)  # Use tk.DISABLED constant
    
    def enable_stop_button(self) -> None:
        """Enable the stop button"""
        if self.stop_button:
            self.stop_button.config(state=tk.NORMAL)  # Use tk.NORMAL constant
    
    def disable_stop_button(self) -> None:
        """Disable the stop button"""
        if self.stop_button:
            self.stop_button.config(state=tk.DISABLED)  # Use tk.DISABLED constant
    
    def show_message(self, title: str, message: str, msg_type: str = "info") -> None:
        """Show a message dialog"""
        if msg_type == "error":
            messagebox.showerror(title, message)
        elif msg_type == "warning":
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)
    
    def ask_yes_no(self, title: str, message: str) -> bool:
        """Show a yes/no dialog"""
        return messagebox.askyesno(title, message)
    
    # Callback setter methods
    def set_start_callback(self, callback: Callable) -> None:
        """Set the start button callback"""
        self.on_start_callback = callback
    
    def set_stop_callback(self, callback: Callable) -> None:
        """Set the stop button callback"""
        self.on_stop_callback = callback
    
    def set_refresh_devices_callback(self, callback: Callable) -> None:
        """Set the refresh devices callback"""
        self.on_refresh_devices_callback = callback
    
    def set_load_mappings_callback(self, callback: Callable) -> None:
        """Set the load mappings callback"""
        self.on_load_mappings_callback = callback
    
    def set_save_mappings_callback(self, callback: Callable) -> None:
        """Set the save mappings callback"""
        self.on_save_mappings_callback = callback
    
    def set_clear_mappings_callback(self, callback: Callable) -> None:
        """Set the clear mappings callback"""
        self.on_clear_mappings_callback = callback
    
    def set_device_toggle_callback(self, callback: Callable) -> None:
        """Set the device toggle callback"""
        self.on_device_toggle_callback = callback
    
    def set_map_input_callback(self, callback: Callable) -> None:
        """Set the map input callback"""
        self.on_map_input_callback = callback
    
    def set_clear_mapping_callback(self, callback: Callable) -> None:
        """Set the clear mapping callback"""
        self.on_clear_mapping_callback = callback
    
    def set_reverser_mode_callback(self, callback: Callable) -> None:
        """Set the callback function for reverser mode changes"""
        self.reverser_mode_callback = callback
    
    def set_reverser_mode(self, switch_mode: bool):
        """Update the UI to reflect the current reverser mode"""
        self.reverser_mode_var.set(switch_mode)
        
        # Update the reverse checkbox visibility for Reverser Lever
        if "Reverser Lever" in self.reverse_axis_checkboxes:
            reverse_checkbox = self.reverse_axis_checkboxes["Reverser Lever"]
            if switch_mode:
                # Hide reverse checkbox in switch mode
                reverse_checkbox.pack_forget()
            else:
                # Show reverse checkbox in axis mode
                reverse_checkbox.pack(side="left", padx=10)
    
    # Internal callback methods
    def _on_start(self) -> None:
        """Handle start button click"""
        if self.on_start_callback:
            self.on_start_callback()
    
    def _on_stop(self) -> None:
        """Handle stop button click"""
        if self.on_stop_callback:
            self.on_stop_callback()
    
    def _on_refresh_devices(self) -> None:
        """Handle refresh devices button click"""
        if self.on_refresh_devices_callback:
            self.on_refresh_devices_callback()
    
    def _on_load_mappings(self) -> None:
        """Handle load mappings button click"""
        if self.on_load_mappings_callback:
            # Show file dialog to select mapping file to load
            file_path = filedialog.askopenfilename(
                title="Load Input Mappings",
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                self.on_load_mappings_callback(file_path)
    
    def _on_save_mappings(self) -> None:
        """Handle save mappings button click"""
        if self.on_save_mappings_callback:
            # Show file dialog to select where to save mapping file
            file_path = filedialog.asksaveasfilename(
                title="Save Input Mappings",
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                self.on_save_mappings_callback(file_path)
    
    def _on_clear_mappings(self) -> None:
        """Handle clear mappings button click"""
        if self.on_clear_mappings_callback:
            self.on_clear_mappings_callback()
    
    def _on_device_toggle(self, device_index: int) -> None:
        """Handle device checkbox toggle"""
        if self.on_device_toggle_callback:
            self.on_device_toggle_callback(device_index)
    
    def _on_map_input(self, function_name: str) -> None:
        """Handle map input button click"""
        if self.on_map_input_callback:
            self.on_map_input_callback(function_name)
    
    def _on_clear_mapping(self, function_name: str) -> None:
        """Handle clear mapping button click"""
        if self.on_clear_mapping_callback:
            self.on_clear_mapping_callback(function_name)
