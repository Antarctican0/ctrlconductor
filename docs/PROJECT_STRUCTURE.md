# Project Structure

This document outlines the organization of the Run8 Control Conductor project.

## Root Directory

```
run8-control-conductor/
├── 📄 README.md              # Main project documentation
├── 📄 CHANGELOG.md           # Version history and changes
├── 📄 LICENSE                # MIT License
├── 📄 requirements.txt       # Python dependencies
├── 📄 .gitignore            # Git ignore rules
├── 📄 __init__.py           # Python package initialization
├── 📁 docs/                 # Documentation folder
│   └── 📄 REFACTORING_SUMMARY.md  # Detailed refactoring documentation
└── 📁 src/                  # Source code (main modules)
```

## Core Application Files

### Main Application
- **`main.py`** - Application entry point and coordinator
- **`run.py`** - Convenience launch script

### Core Modules
- **`networking.py`** - UDP communication with Run8 simulator
- **`input_handler.py`** - Input device management and processing
- **`mapping_logic.py`** - Input mapping and value processing logic
- **`ui_components.py`** - User interface components and theming
- **`config.py`** - Configuration constants and settings
- **`utils.py`** - Utility functions and helper classes

### Development & Testing
- **`test_modules.py`** - Module verification and testing script

### Legacy Files (for reference)
- **`input_mapper.py`** - Current working version (monolithic)
- **`input_mapper_original.py`** - Backup of original code

### Generated Files
- **`input_mappings.csv`** - User's saved input mappings (auto-generated)

## Module Responsibilities

### `main.py` (~400 lines)
- Application lifecycle management
- Module coordination and communication
- Error handling and logging setup
- User interaction flow control

### `networking.py` (~120 lines)
- UDP socket management
- Run8 protocol implementation
- Connection handling and error recovery

### `input_handler.py` (~250 lines)
- Pygame initialization and device detection
- Input device management (enable/disable)
- Real-time input processing and state tracking

### `mapping_logic.py` (~350 lines)
- Input-to-function mapping storage and retrieval
- Input value processing and transformation
- Different input type handling (momentary, toggle, lever, etc.)
- CSV file persistence

### `ui_components.py` (~400 lines)
- Tkinter GUI creation and management
- Dark theme implementation
- Tabbed interface and categorized controls
- User interaction callbacks

### `config.py` (~100 lines)
- Application constants and default values
- Run8 function definitions and mappings
- Theme configuration
- Input type classifications

### `utils.py` (~200 lines)
- Utility functions and helper classes
- Periodic timers and state tracking
- Common data transformations
- Error handling decorators

## Design Patterns Used

- **Facade Pattern**: `main.py` provides simplified interface to complex subsystems
- **Strategy Pattern**: Different input processing strategies in `mapping_logic.py`
- **Observer Pattern**: UI callbacks for event handling in `ui_components.py`
- **Factory Pattern**: Device creation and management in `input_handler.py`

## Data Flow

1. **Input Detection**: `input_handler.py` detects and processes raw input
2. **Mapping Resolution**: `mapping_logic.py` maps inputs to Run8 functions
3. **Value Processing**: `mapping_logic.py` transforms input values appropriately
4. **Network Transmission**: `networking.py` sends UDP packets to Run8
5. **UI Updates**: `ui_components.py` reflects current state to user

## Extension Points

- **New Input Types**: Extend `mapping_logic.py` with new processing strategies
- **Additional Protocols**: Extend `networking.py` with new communication methods
- **Custom Themes**: Modify `config.py` and `ui_components.py`
- **New Devices**: Extend `input_handler.py` with specialized device support
- **Additional Features**: Add new modules following the established patterns

## Development Workflow

1. **Setup**: `pip install -r requirements.txt`
2. **Test**: `python test_modules.py`
3. **Develop**: Modify appropriate module(s)
4. **Test**: Re-run module tests
5. **Run**: `python main.py` or `python run.py`
