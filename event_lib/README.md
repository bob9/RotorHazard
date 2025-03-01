# Event Library

A Python library for parsing and fetching event data from the RotorHazard API.

## Installation

```bash
pip install .
```

## Usage

### Basic Usage

```python
from event_lib import EventParser

# Create a parser instance
parser = EventParser("http://192.168.1.185:8080/api")

# Parse event ID from JavaScript code
js_code = 'var eventManager = new EventManager("events/b69a294c-a074-4f4e-b949-4ae7de90c3e3", tooOld);'
event_id = parser.extract_event_id(js_code)

# Fetch event data
if event_id:
    event_data = parser.get_event_data(event_id)
    print(event_data)

# Get all events
all_events = parser.get_all_events()
print(all_events)
```

### Using the EventManager Class

The `EventManager` class provides additional functionality like caching and filtering active events:

```python
from examples.event_manager import EventManager

# Create an event manager instance
manager = EventManager("http://192.168.1.185:8080/api")

# Parse and fetch event data
js_code = 'var eventManager = new EventManager("events/b69a294c-a074-4f4e-b949-4ae7de90c3e3", tooOld);'
event_data = manager.parse_event_from_js(js_code)

# Get all active events
active_events = manager.get_all_active_events()

# Get cached event
cached_event = manager.get_cached_event(event_id)

# Save events to file
manager.save_events_to_file('events.json')
```

## Features

- Parse event IDs from JavaScript code
- Fetch event data from RotorHazard API
- Cache event data
- Filter active events
- Save events to JSON file
- Type hints for better IDE support
- Error handling and logging

## Requirements

- Python 3.7+
- requests>=2.32.3 