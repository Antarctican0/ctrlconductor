"""
Utility functions and helpers for Run8 Control Conductor

Contains common utility functions, constants, and helper classes.
"""

import os
import time
import threading
from typing import Any, Callable, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PeriodicTimer:
    """A periodic timer that runs a function at regular intervals"""
    
    def __init__(self, interval: float, function: Callable, *args, **kwargs):
        """
        Initialize the periodic timer
        
        Args:
            interval: Time interval in seconds
            function: Function to call periodically
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.timer: Optional[threading.Timer] = None
        self.running = False
    
    def start(self) -> None:
        """Start the periodic timer"""
        if not self.running:
            self.running = True
            self._run()
            logger.debug(f"Started periodic timer with interval {self.interval}s")
    
    def stop(self) -> None:
        """Stop the periodic timer"""
        self.running = False
        if self.timer:
            self.timer.cancel()
            self.timer = None
            logger.debug("Stopped periodic timer")
    
    def _run(self) -> None:
        """Internal method to run the timer"""
        if self.running:
            try:
                self.function(*self.args, **self.kwargs)
            except Exception as e:
                logger.error(f"Error in periodic timer function: {e}")
            
            if self.running:
                self.timer = threading.Timer(self.interval, self._run)
                self.timer.start()
    
    def is_running(self) -> bool:
        """Check if the timer is running"""
        return self.running


class StateTracker:
    """Tracks state changes for input processing"""
    
    def __init__(self):
        """Initialize the state tracker"""
        self.states = {}
        self.last_change_time = {}
    
    def update_state(self, key: Any, value: Any) -> bool:
        """
        Update a state value
        
        Args:
            key: State key
            value: New state value
            
        Returns:
            True if state changed, False otherwise
        """
        current_time = time.time()
        old_value = self.states.get(key)
        
        if old_value != value:
            self.states[key] = value
            self.last_change_time[key] = current_time
            return True
        
        return False
    
    def get_state(self, key: Any, default: Any = None) -> Any:
        """Get current state value"""
        return self.states.get(key, default)
    
    def get_time_since_change(self, key: Any) -> float:
        """Get time since last state change"""
        if key in self.last_change_time:
            return time.time() - self.last_change_time[key]
        return float('inf')
    
    def clear_state(self, key: Any) -> None:
        """Clear a specific state"""
        if key in self.states:
            del self.states[key]
        if key in self.last_change_time:
            del self.last_change_time[key]
    
    def clear_all_states(self) -> None:
        """Clear all states"""
        self.states.clear()
        self.last_change_time.clear()


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between min and max
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def normalize_axis(value: float, deadzone: float = 0.0) -> float:
    """
    Normalize axis value to -1.0 to 1.0 range with deadzone
    
    Args:
        value: Raw axis value
        deadzone: Deadzone threshold (0.0 to 1.0)
        
    Returns:
        Normalized axis value
    """
    # Apply deadzone
    if abs(value) < deadzone:
        return 0.0
    
    # Normalize to -1.0 to 1.0 range
    if value > 0:
        return (value - deadzone) / (1.0 - deadzone)
    else:
        return (value + deadzone) / (1.0 - deadzone)


def map_range(value: float, from_min: float, from_max: float, 
              to_min: float, to_max: float) -> float:
    """
    Map a value from one range to another
    
    Args:
        value: Value to map
        from_min: Source range minimum
        from_max: Source range maximum
        to_min: Target range minimum
        to_max: Target range maximum
        
    Returns:
        Mapped value
    """
    # Normalize to 0-1 range
    normalized = (value - from_min) / (from_max - from_min)
    
    # Map to target range
    return to_min + (normalized * (to_max - to_min))


def get_application_dir() -> str:
    """Get the application directory"""
    return os.path.dirname(os.path.abspath(__file__))


def get_config_dir() -> str:
    """Get the configuration directory"""
    config_dir = os.path.join(get_application_dir(), 'config')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_log_dir() -> str:
    """Get the log directory"""
    log_dir = os.path.join(get_application_dir(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def format_input_display(device_id: int, input_type: str, input_index: int) -> str:
    """
    Format input mapping for display
    
    Args:
        device_id: Device ID
        input_type: Input type (Button, Axis, Hat)
        input_index: Input index
        
    Returns:
        Formatted display string
    """
    return f"Device {device_id}: {input_type} {input_index}"


def validate_ip_address(ip: str) -> bool:
    """
    Validate IP address format
    
    Args:
        ip: IP address string
        
    Returns:
        True if valid IP address, False otherwise
    """
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False
        
        return True
    except Exception:
        return False


def validate_port(port: int) -> bool:
    """
    Validate port number
    
    Args:
        port: Port number
        
    Returns:
        True if valid port, False otherwise
    """
    return 1 <= port <= 65535


def safe_int_convert(value: str, default: int = 0) -> int:
    """
    Safely convert string to int
    
    Args:
        value: String value to convert
        default: Default value if conversion fails
        
    Returns:
        Converted integer or default value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float_convert(value: str, default: float = 0.0) -> float:
    """
    Safely convert string to float
    
    Args:
        value: String value to convert
        default: Default value if conversion fails
        
    Returns:
        Converted float or default value
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Setup application logging
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Setup file handler if specified
    handlers = [console_handler]
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info(f"Logging setup complete - Level: {level}")


class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass


class InputError(Exception):
    """Custom exception for input-related errors"""
    pass


class NetworkError(Exception):
    """Custom exception for network-related errors"""
    pass


def handle_exception(func: Callable) -> Callable:
    """
    Decorator to handle exceptions in functions
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {e}")
            raise
    return wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """
    Decorator to retry function on failure
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    logger.warning(f"Function {func.__name__} failed on attempt {attempt + 1}: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator
