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
        ("MU HL Switch", 7),
        ("Horn", 8),
        ("Independent Brake Lever", 9),
        ("Independent Bailoff", 10),
        ("Isolation Switch", 11),
        ("Park-Brake Set", 12),
        ("Park-Brake Release", 13),
        ("Reverser Lever", 14),
        ("Sander", 15),
        ("Throttle Lever", 16),
        ("Train Brake Lever", 18),
        ("Wiper Switch", 19),
        ("DTMF 0", 20),
        ("DTMF 1", 21),
        ("DTMF 2", 22),
        ("DTMF 3", 23),
        ("DTMF 4", 24),
        ("DTMF 5", 25),
        ("DTMF 6", 26),
        ("DTMF 7", 27),
        ("DTMF 8", 28),
        ("DTMF 9", 29),
        ("DTMF #", 30),
        ("DTMF *", 31),
        ("Radio Volume Increase", 32),
        ("Radio Volume Decrease", 33),
        ("Radio Mute", 34),
        ("Radio Channel Mode", 35),
        ("Radio DTMF Mode", 36),
        ("Circuit Breaker Control", 37),
        ("Circuit Breaker DynBrake", 38),
        ("Circuit Breaker EngRun", 39),
        ("Circuit Breaker GenField", 40),
        ("Cab Light Switch", 41),
        ("Step Light Switch", 42),
        ("Gauge Light Switch", 43),
        ("EOT Emg Stop", 44),
        ("Engine Start", 50),
        ("Engine Stop", 51),
        ("HEP Switch", 52),
        ("Slow Speed Toggle", 55),
        ("Slow Speed Increment", 56),
        ("Slow Speed Decrement", 57),
        ("DPU Throttle Increase", 58),
        ("DPU Throttle Decrease", 59),
        ("DPU Dyn-Brake Setup", 60),
        ("DPU Fence Increase", 61),
        ("DPU Fence Decrease", 62),
        ("Class Light Switch", 63),
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
        'Isolation Switch': '3way',  # 3-way toggle
        'Distance Counter': '3way',  # 3-way toggle
        'Headlight Front': '3way',   # 3-way toggle
        'Headlight Rear': '3way',    # 3-way toggle
        'Wiper Switch': '4way',      # 4-way toggle
        'MU HL Switch': '5way',    # 5-way toggle
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
        'DTMF 0': 'momentary',
        'DTMF 1': 'momentary',
        'DTMF 2': 'momentary',
        'DTMF 3': 'momentary',
        'DTMF 4': 'momentary',
        'DTMF 5': 'momentary',
        'DTMF 6': 'momentary',
        'DTMF 7': 'momentary',
        'DTMF 8': 'momentary',
        'DTMF 9': 'momentary',
        'DTMF #': 'momentary',
        'DTMF *': 'momentary',
        'Radio Volume Increase': 'momentary',
        'Radio Volume Decrease': 'momentary',
        'Radio Mute': 'toggle',
        'Radio Channel Mode': 'toggle',
        'Radio DTMF Mode': 'toggle',
        'Engine Start': 'momentary',
        'Engine Stop': 'momentary',
        'Class Light Switch': '4way',  # 4-way toggle
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
            "Cab Light Switch", "Step Light Switch", "Gauge Light Switch", "MU HL Switch",
            "Class Light Switch"
        ],
        "Electrical": [
            # No lever controls in this category  
            "HEP Switch", "Circuit Breaker Control", "Circuit Breaker DynBrake", "Circuit Breaker EngRun", 
            "Circuit Breaker GenField", "Isolation Switch"
        ],
        "DPU": [
            # No lever controls in this category
            "DPU Throttle Increase", "DPU Throttle Decrease", "DPU Dyn-Brake Setup", 
            "DPU Fence Increase", "DPU Fence Decrease"
        ],
        "Radios": [
            # No lever controls in this category  
            "DTMF 0", "DTMF 1", "DTMF 2", "DTMF 3", "DTMF 4", "DTMF 5", "DTMF 6", "DTMF 7", "DTMF 8", "DTMF 9",
            "DTMF #", "DTMF *", "Radio Volume Increase", "Radio Volume Decrease", "Radio Mute", "Radio Channel Mode",
            "Radio DTMF Mode"
        ],
        "Misc": [
            # No lever controls in this category  
            "EOT Emg Stop",  "Slow Speed Toggle", "Slow Speed Increment", 
            "Slow Speed Decrement", 
            "Park-Brake Set", "Park-Brake Release"
        ]
    }
