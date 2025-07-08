"""
Configuration settings and constants for Run8 Control Conductor.

This module contains all configuration constants, default values, and settings
used throughout the application.
"""

# Network configuration
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 18888

# Input detection constants
DEADZONE = 0.7
RELEASE_TIMEOUT = 0.15
POLLING_INTERVAL = 20  # ms (was likely 50 or higher)
UDP_SEND_INTERVAL = 20  # ms (was likely 50 or higher)

# UI Theme Configuration
class ThemeConfig:
    """Dark theme configuration for the UI"""
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
    """Run8 function mappings and input type definitions"""
    
    FUNCTIONS = [
        ("Alerter", 1),
        ("Bell", 2),
        ("Distance Counter", 3),
        ("Dyn Brake Lever", 4),
        ("Headlight Front", 5),
        ("Headlight Rear", 6),
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
        ("Circuit Breaker Control", 37),
        ("Circuit Breaker DynBrake", 38),
        ("Circuit Breaker EngRun", 39),
        ("Circuit Breaker GenField", 10),
        ("Cab Light Switch", 41),
        ("Step Light Switch", 42),
        ("Gauge Light Switch", 43),
        ("EOT Emg Stop", 44),
        ("HEP Switch", 52),
        ("Slow Speed Toggle", 55),
        ("Slow Speed Increment", 56),
        ("Slow Speed Decrement", 57),
        ("DPU Throttle Increase", 58),
        ("DPU Throttle Decrease", 59),
        ("DPU Dyn-Brake Setup", 60),
        ("DPU Fence Increase", 61),
        ("DPU Fence Decrease", 62),
        # --- Combined lever support ---
        ("Combined Throttle/Dyn", 100),
        ("Throttle/Dyn Toggle", 101),
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
        'Headlight Front': '3way',   # 3-way toggle
        'Headlight Rear': '3way',    # 3-way toggle
        'Wiper Switch': '4way',      # 4-way toggle
        'Park-Brake Set': 'momentary',
        'Park-Brake Release': 'momentary',
        'Circuit Breaker Control': 'toggle',
        'Circuit Breaker DynBrake': 'toggle',
        'Circuit Breaker EngRun': 'toggle',
        'Circuit Breaker GenField': 'toggle',
        'Cab Light Switch': 'toggle',
        'Step Light Switch': 'toggle',
        'Gauge Light Switch': 'toggle',
        'HEP Switch': 'toggle',
        'Slow Speed Toggle': 'toggle',
        'Slow Speed Increment': 'momentary',
        'Slow Speed Decrement': 'momentary',
        'DPU Throttle Increase': 'momentary',
        'DPU Throttle Decrease': 'momentary',
        'DPU Dyn-Brake Setup': 'momentary',
        'DPU Fence Increase': 'momentary',
        'DPU Fence Decrease': 'momentary',
        'Independent Brake Lever': 'lever',
        # --- Combined lever support ---
        'Combined Throttle/Dyn': 'lever',
        'Throttle/Dyn Toggle': 'button',
    }
    
    CATEGORIES = {
        "Main Controls": [
            # Lever controls with reverse options first
            "Throttle Lever", "Train Brake Lever", "Independent Brake Lever", 
            "Dyn Brake Lever", "Reverser Lever",
            # --- Combined lever support ---
            "Combined Throttle/Dyn", "Throttle/Dyn Toggle"
        ],
        "Cab Controls": [
            "Sander", "Horn", "Bell", "Alerter", "Independent Bailoff", "Distance Counter"
        ],
        "Lights and Wipers": [
            # No lever controls in this category, but keeping logical order
            "Headlight Front", "Headlight Rear", "Wiper Switch", 
            "Cab Light Switch", "Step Light Switch", "Gauge Light Switch"
        ],
        "Electrical": [
            # No lever controls in this category  
            "HEP Switch", "Circuit Breaker Control", "Circuit Breaker DynBrake", "Circuit Breaker EngRun", 
            "Circuit Breaker GenField",
        ],
        "DPU": [
            # No lever controls in this category
            "DPU Throttle Increase", "DPU Throttle Decrease", "DPU Dyn-Brake Setup", 
            "DPU Fence Increase", "DPU Fence Decrease"
        ],
        "Misc": [
            # No lever controls in this category  
            "EOT Emg Stop",  "Slow Speed Toggle", "Slow Speed Increment", 
            "Slow Speed Decrement", 
            "Park-Brake Set", "Park-Brake Release"
        ]
    }
