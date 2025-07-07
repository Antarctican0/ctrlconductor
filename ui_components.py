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
        # Can be tk.Label or tk.Entry (readonly)
        self.mapping_labels: Dict[str, Any] = {}
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
        self.on_cancel_mapping_callback: Optional[Callable] = None
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
        """Setup the main window layout using grid for better resizing"""
        self.master.title("Run8 Control Conductor")
        self.master.minsize(600, 650)
        self.master.geometry("700x650")

        # Configure grid weights for expansion
        self.master.grid_rowconfigure(0, weight=0)  # Connection
        self.master.grid_rowconfigure(1, weight=0)  # Devices
        self.master.grid_rowconfigure(2, weight=0)  # Reverser mode
        self.master.grid_rowconfigure(3, weight=1)  # Mapping (expand vertically)
        self.master.grid_rowconfigure(4, weight=0)  # Controls (bottom)
        self.master.grid_columnconfigure(0, weight=1)

        # Create main sections using grid
        self._create_connection_section()
        self._create_device_section()
        # Ensure reverser mode selector is created before layout so attribute exists
        self.reverser_mode_var = tk.BooleanVar(value=False)
        self.reverser_mode_callback = None
        self.reverser_mode_frame = None
        self.reverser_mode_checkbox = None
        self._create_reverser_mode_selector()  # Move reverser mode selector here
        self._create_mapping_section()
        self._create_control_section()

        # Place sections in grid
        self.connection_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
        self.device_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=2)
        if self.reverser_mode_frame is not None:
            self.reverser_mode_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=2)
        self.mapping_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=2)
        self.control_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(2, 8))
    
    def _create_connection_section(self) -> None:
        """Create the connection configuration section"""
        self.connection_frame = tk.Frame(self.master, bg=self.theme.DARK_BG)
        # IP configuration
        ip_frame = tk.Frame(self.connection_frame, bg=self.theme.DARK_BG)
        ip_frame.pack(side="left", padx=5)
        label = tk.Label(ip_frame, text="Simulator IP:", bg=self.theme.DARK_ACCENT, fg=self.theme.DARK_FG)
        label.pack()
        self.ip_entry = tk.Entry(
            ip_frame,
            width=15,
            bg=self.theme.DARK_ENTRY_BG,
            fg=self.theme.DARK_ENTRY_FG,
            insertbackground=self.theme.DARK_ENTRY_FG,
            highlightthickness=1,
            highlightbackground="#444444"
        )
        self.ip_entry.pack()
        # Port configuration
        port_frame = tk.Frame(self.connection_frame, bg=self.theme.DARK_BG)
        port_frame.pack(side="left", padx=5)
        tk.Label(port_frame, text="Simulator Port:", bg=self.theme.DARK_ACCENT, fg=self.theme.DARK_FG).pack()
        self.port_entry = tk.Entry(
            port_frame,
            width=10,
            bg=self.theme.DARK_ENTRY_BG,
            fg=self.theme.DARK_ENTRY_FG,
            insertbackground=self.theme.DARK_ENTRY_FG,
            highlightthickness=1,
            highlightbackground="#444444"
        )
        self.port_entry.pack()
    
    def _create_device_section(self) -> None:
        """Create the device selection section"""
        self.device_frame = tk.LabelFrame(
            self.master,
            text="Input Devices",
            bg=self.theme.DARK_ACCENT,
            fg=self.theme.DARK_FG,
            bd=2,
            relief=tk.GROOVE,  # Use tk.GROOVE constant, not string
            labelanchor="nw"   # Use keyword argument
        )
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
        self.devices_list_frame = tk.Frame(self.device_frame, bg=self.theme.DARK_ACCENT)
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
        # Mapping prompt
        self.mapping_prompt = tk.StringVar(value="Click 'Map Input' to assign a function.")
        
        # Prompt label and cancel button frame
        prompt_frame = tk.Frame(self.mapping_frame, bg=self.theme.DARK_ACCENT)
        prompt_frame.pack(fill="x", expand=False, anchor=tk.W, pady=(0, 5))
        
        self.prompt_label = tk.Label(
            prompt_frame,
            textvariable=self.mapping_prompt,
            fg="#7ecfff",
            bg=self.theme.DARK_ACCENT
        )
        self.prompt_label.pack(side=tk.LEFT, anchor=tk.W)
        
        # Cancel mapping button (initially hidden)
        self.cancel_mapping_button = tk.Button(
            prompt_frame,
            text="Cancel Mapping",
            command=self._on_cancel_mapping,
            bg=self.theme.DARK_BUTTON_BG,
            fg=self.theme.DARK_FG,
            activebackground=self.theme.DARK_HIGHLIGHT,
            activeforeground=self.theme.DARK_FG,
            relief=tk.RAISED
        )
        # Don't pack it yet - will show when mapping is in progress
        
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
        # (Reverser mode selector is now created and placed in main layout)
    
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
        self.control_frame = tk.Frame(self.master, bg=self.theme.DARK_BG)

        # Start/Stop buttons
        button_frame = tk.Frame(self.control_frame, bg=self.theme.DARK_BG)
        button_frame.pack(side="left", anchor="sw")

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
        mapping_control_frame = tk.Frame(self.control_frame, bg=self.theme.DARK_BG)
        mapping_control_frame.pack(side="right", anchor="se", padx=10, pady=5)

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
        self.reverser_mode_frame = tk.Frame(self.master, bg=self.theme.DARK_ACCENT)
        # Do not pack/grid here; handled in main layout
        label = tk.Label(
            self.reverser_mode_frame,
            text="Reverser Control Mode:",
            bg=self.theme.DARK_ACCENT,
            fg=self.theme.DARK_FG,
            font=("Segoe UI", 10, "bold")
        )
        label.pack(side=tk.LEFT)
        self.reverser_mode_checkbox = tk.Checkbutton(
            self.reverser_mode_frame,
            text="Use 3-position switch (instead of axis/lever)",
            variable=self.reverser_mode_var,
            command=self._on_reverser_mode_change,
            bg=self.theme.DARK_BUTTON_BG,
            fg=self.theme.DARK_BUTTON_FG,
            activebackground=self.theme.DARK_HIGHLIGHT,
            activeforeground=self.theme.DARK_FG,
            selectcolor=self.theme.DARK_ACCENT,
            relief=tk.RAISED,
            bd=2,
            font=("Segoe UI", 10, "bold")
        )
        self.reverser_mode_checkbox.pack(side=tk.LEFT, padx=10)
    
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

        # Refresh the mapping interface to show/hide 3-way rows
        if hasattr(self, '_last_functions_list'):
            self.populate_mapping_interface(self._last_functions_list)
    
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
                bg=self.theme.DARK_BUTTON_BG,
                fg=self.theme.DARK_BUTTON_FG,
                activebackground=self.theme.DARK_HIGHLIGHT,
                activeforeground=self.theme.DARK_FG,
                selectcolor=self.theme.DARK_ACCENT,
                relief=tk.RAISED,
                bd=2,
                font=("Segoe UI", 10, "bold")
            )
            checkbox.pack(anchor=tk.W, pady=2, padx=2)
            self.device_vars.append(var)
            self.device_checkboxes.append(checkbox)
    
    def populate_mapping_interface(self, functions: List[str], mapping_data: Optional[dict] = None) -> None:
        """
        Populate the mapping interface with function controls
        Args:
            functions: List of function names to create controls for
            mapping_data: Optional dict mapping function names to mapping text (for restoring UI)
        """
        # Store the last-used function list for UI refreshes
        self._last_functions_list = functions.copy()

        # Save current mapping display so we can restore it after UI refresh
        current_mapping_display = {}
        for fn, widget in self.mapping_labels.items():
            if isinstance(widget, tk.Entry):
                val = widget.get()
                current_mapping_display[fn] = val if val else "Not mapped"

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

        # Determine which mapping data to use for restoring display
        restore_map = mapping_data if mapping_data is not None else current_mapping_display
        for fn, widget in self.mapping_labels.items():
            # Always show "Not mapped" if no mapping exists
            text = restore_map.get(fn, "Not mapped")
            self.update_mapping_display(fn, text)
    
    def _get_function_category(self, function_name: str) -> str:
        """Get the category for a function name"""
        for category, functions in self.function_categories.items():
            if function_name in functions:
                return category
        return "Misc"  # Default category
    
    def _create_function_controls(self, parent_frame: tk.Frame, function_name: str) -> None:
        """Create controls for a single function"""
        # Always render the main Reverser Lever row
        if function_name == "Reverser Lever":
            # Main row: match font and padding to other controls
            func_frame = tk.Frame(parent_frame, bg=self.theme.DARK_ACCENT)
            func_frame.pack(fill="x", pady=2)

            name_label = tk.Label(
                func_frame,
                text="Reverser Lever",
                width=25,
                anchor=tk.W,
                bg=self.theme.DARK_ACCENT,
                fg=self.theme.DARK_FG
            )
            name_label.pack(side="left", padx=5)

            status_label = tk.Entry(
                func_frame,
                width=22,
                relief=tk.GROOVE,
                borderwidth=2,
                bg=self.theme.DARK_ENTRY_BG,
                fg=self.theme.DARK_ENTRY_FG,
                state="readonly",
                readonlybackground=self.theme.DARK_ENTRY_BG,
                highlightthickness=1,
                highlightbackground="#444444"
            )
            status_label.insert(0, "Not mapped")
            status_label.pack(side="left", padx=5)
            self.mapping_labels[function_name] = status_label

            input_type = FunctionMapping.INPUT_TYPES.get(function_name, 'toggle')
            reverse_var = None
            reverse_checkbox = None
            if input_type == 'lever':
                reverse_var = tk.BooleanVar()
                reverse_checkbox = tk.Checkbutton(
                    func_frame,
                    text="Reverse",
                    variable=reverse_var,
                    bg="#444444",
                    fg=self.theme.DARK_FG,
                    activebackground="#666666",
                    activeforeground=self.theme.DARK_FG,
                    selectcolor=self.theme.DARK_ACCENT,
                    relief=tk.RAISED,
                    bd=2
                )
                reverse_checkbox.pack(side="left", padx=10)
                self.reverse_axis_vars[function_name] = reverse_var
                self.reverse_axis_checkboxes[function_name] = reverse_checkbox
                # Hide reverse checkbox for Reverser Lever if in switch mode
                if self.reverser_mode_var.get():
                    reverse_checkbox.pack_forget()

            buttons_frame = tk.Frame(func_frame, bg=self.theme.DARK_ACCENT)
            buttons_frame.pack(side="right", padx=5)

            map_button = tk.Button(
                buttons_frame,
                text="Map Input",
                command=lambda fn=function_name: self._on_map_input(fn),
                bg="#444444",
                fg=self.theme.DARK_FG,
                activebackground="#666666",
                activeforeground=self.theme.DARK_FG,
                relief=tk.RAISED,
                bd=2
            )
            map_button.pack(side="left", padx=2)
            self.mapping_buttons[function_name] = map_button

            clear_button = tk.Button(
                buttons_frame,
                text="Clear",
                command=lambda fn=function_name: self._on_clear_mapping(fn),
                bg="#444444",
                fg=self.theme.DARK_FG,
                activebackground="#666666",
                activeforeground=self.theme.DARK_FG,
                relief=tk.RAISED,
                bd=2
            )
            clear_button.pack(side="left", padx=2)

            # If 3-way mode, disable main row's controls and add a single wide sub-frame with three rows
            if self.reverser_mode_var.get():
                map_button.config(state=tk.DISABLED)
                clear_button.config(state=tk.DISABLED)
                if reverse_checkbox:
                    reverse_checkbox.config(state=tk.DISABLED)

                # Create a single sub-frame for all three modes, each on its own line
                sub_frame = tk.Frame(parent_frame, bg="#23272b", highlightbackground="#444444", highlightthickness=1, bd=1, relief=tk.GROOVE)
                sub_frame.pack(fill="x", pady=(0, 8), padx=(0, 2))

                for idx, (pos, label) in enumerate(zip(["forward", "neutral", "reverse"], ["Forward", "Neutral", "Reverse"])):
                    row = tk.Frame(sub_frame, bg="#23272b")
                    row.pack(fill="x", pady=2)

                    name_label = tk.Label(
                        row,
                        text=label,
                        width=12,
                        anchor=tk.W,
                        bg="#23272b",
                        fg=self.theme.DARK_FG,
                        font=("Segoe UI", 10, "bold")
                    )
                    name_label.pack(side="left", padx=8)

                    status_label = tk.Entry(
                        row,
                        width=16,
                        relief=tk.GROOVE,
                        borderwidth=2,
                        bg=self.theme.DARK_ENTRY_BG,
                        fg=self.theme.DARK_ENTRY_FG,
                        state="readonly",
                        readonlybackground=self.theme.DARK_ENTRY_BG,
                        highlightthickness=1,
                        highlightbackground="#444444"
                    )
                    status_label.insert(0, "Not mapped")
                    status_label.pack(side="left", padx=5)
                    self.mapping_labels[f"Reverser 3way {pos}"] = status_label

                    buttons_frame = tk.Frame(row, bg="#23272b")
                    buttons_frame.pack(side="left", padx=5)

                    map_button = tk.Button(
                        buttons_frame,
                        text="Map Input",
                        command=lambda p=pos: self._on_map_input(f"Reverser 3way {p}"),
                        bg="#444444",
                        fg=self.theme.DARK_FG,
                        activebackground="#666666",
                        activeforeground=self.theme.DARK_FG,
                        relief=tk.RAISED,
                        bd=2,
                        width=10
                    )
                    map_button.pack(side="left", padx=2)
                    self.mapping_buttons[f"Reverser 3way {pos}"] = map_button

                    clear_button = tk.Button(
                        buttons_frame,
                        text="Clear",
                        command=lambda p=pos: self._on_clear_mapping(f"Reverser 3way {p}"),
                        bg="#444444",
                        fg=self.theme.DARK_FG,
                        activebackground="#666666",
                        activeforeground=self.theme.DARK_FG,
                        relief=tk.RAISED,
                        bd=2,
                        width=8
                    )
                    clear_button.pack(side="left", padx=2)
                # End of single sub-frame
            return

        # Default: lever/axis or button mapping
        func_frame = tk.Frame(parent_frame, bg=self.theme.DARK_ACCENT)
        func_frame.pack(fill="x", pady=2)

        name_label = tk.Label(
            func_frame,
            text=function_name,
            width=25,
            anchor=tk.W,
            bg=self.theme.DARK_ACCENT,
            fg=self.theme.DARK_FG
        )
        name_label.pack(side="left", padx=5)

        status_label = tk.Entry(
            func_frame,
            width=22,
            relief=tk.GROOVE,
            borderwidth=2,
            bg=self.theme.DARK_ENTRY_BG,
            fg=self.theme.DARK_ENTRY_FG,
            state="readonly",
            readonlybackground=self.theme.DARK_ENTRY_BG,
            highlightthickness=1,
            highlightbackground="#444444"
        )
        status_label.insert(0, "Not mapped")
        status_label.pack(side="left", padx=5)
        self.mapping_labels[function_name] = status_label

        input_type = FunctionMapping.INPUT_TYPES.get(function_name, 'toggle')
        if input_type == 'lever':
            reverse_var = tk.BooleanVar()
            reverse_checkbox = tk.Checkbutton(
                func_frame,
                text="Reverse",
                variable=reverse_var,
                bg="#444444",
                fg=self.theme.DARK_FG,
                activebackground="#666666",
                activeforeground=self.theme.DARK_FG,
                selectcolor=self.theme.DARK_ACCENT,
                relief=tk.RAISED,
                bd=2
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
            bg="#444444",
            fg=self.theme.DARK_FG,
            activebackground="#666666",
            activeforeground=self.theme.DARK_FG,
            relief=tk.RAISED,
            bd=2
        )
        map_button.pack(side="left", padx=2)
        self.mapping_buttons[function_name] = map_button

        clear_button = tk.Button(
            buttons_frame,
            text="Clear",
            command=lambda fn=function_name: self._on_clear_mapping(fn),
            bg="#444444",
            fg=self.theme.DARK_FG,
            activebackground="#666666",
            activeforeground=self.theme.DARK_FG,
            relief=tk.RAISED,
            bd=2
        )
        clear_button.pack(side="left", padx=2)

    def update_mapping_display(self, function_name: str, mapping_text: str) -> None:
        """Update the display text for a function mapping"""
        if function_name in self.mapping_labels:
            widget = self.mapping_labels[function_name]
            if isinstance(widget, tk.Entry):
                # 'readonly' is a valid state for tk.Entry, but not recognized by type checker
                widget.config(state="normal")
                widget.delete(0, tk.END)
                widget.insert(0, mapping_text)
                widget.config(state="readonly")  # type: ignore
            else:
                widget.config(text=mapping_text)
    
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
    
    def show_message(self, title: str, message: str, msg_type: str = "info") -> Any:
        """Show a message dialog. For 'question_with_options', returns 'cancel', 'clear', or 'keep'."""
        if msg_type == "error":
            messagebox.showerror(title, message)
            return None
        elif msg_type == "warning":
            messagebox.showwarning(title, message)
            return None
        elif msg_type == "question_with_options":
            # Custom dialog with three buttons
            dialog = tk.Toplevel(self.master)
            dialog.title(title)
            dialog.grab_set()
            dialog.resizable(False, False)
            tk.Label(dialog, text=message, wraplength=400, justify="left").pack(padx=20, pady=15)
            result = {"choice": "cancel"}
            def set_choice(val):
                result["choice"] = val
                dialog.destroy()
            btn_frame = tk.Frame(dialog)
            btn_frame.pack(pady=(0, 15))
            tk.Button(btn_frame, text="Cancel", width=10, command=lambda: set_choice("cancel")).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Clear Other Mapping", width=18, command=lambda: set_choice("clear")).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Keep Both", width=10, command=lambda: set_choice("keep")).pack(side="left", padx=5)
            dialog.wait_window()
            return result["choice"]
        else:
            messagebox.showinfo(title, message)
            return None
    
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
    
    def _on_cancel_mapping(self) -> None:
        """Handle cancel mapping button click"""
        if self.on_cancel_mapping_callback:
            self.on_cancel_mapping_callback()
            
    def set_cancel_mapping_callback(self, callback: Callable) -> None:
        """Set callback for cancel mapping button"""
        self.on_cancel_mapping_callback = callback
