from event_lib import EventParser
from typing import Dict, List, Optional
import json


class EventManager:
    """Example class that uses the EventParser library to manage events."""
    
    def __init__(self, api_url: str = "http://192.168.1.185:8080/api"):
        """
        Initialize the EventManager.
        
        Args:
            api_url (str): The base URL for the API
        """
        self.parser = EventParser(api_url)
        self._cached_events: Dict[str, dict] = {}

    def parse_event_from_js(self, js_code: str) -> Optional[dict]:
        """
        Parse an event from JavaScript code and fetch its data.
        
        Args:
            js_code (str): The JavaScript code containing the event initialization
            
        Returns:
            Optional[dict]: The event data if found and fetched successfully, None otherwise
        """
        event_id = self.parser.extract_event_id(js_code)
        if not event_id:
            return None
            
        try:
            event_data = self.parser.get_event_data(event_id)
            self._cached_events[event_id] = event_data
            return event_data
        except Exception as e:
            print(f"Error fetching event data: {e}")
            return None

    def get_all_active_events(self) -> List[dict]:
        """
        Fetch all active events from the API.
        
        Returns:
            List[dict]: List of active events
        """
        try:
            events = self.parser.get_all_events()
            # Assuming the API returns a dictionary with an 'events' key
            active_events = [
                event for event in events.get('events', [])
                if event.get('status') == 'active'
            ]
            
            # Update cache
            for event in active_events:
                if 'id' in event:
                    self._cached_events[event['id']] = event
                    
            return active_events
        except Exception as e:
            print(f"Error fetching active events: {e}")
            return []

    def get_cached_event(self, event_id: str) -> Optional[dict]:
        """
        Get an event from the cache.
        
        Args:
            event_id (str): The ID of the event to retrieve
            
        Returns:
            Optional[dict]: The cached event data if found, None otherwise
        """
        return self._cached_events.get(event_id)

    def save_events_to_file(self, filename: str) -> bool:
        """
        Save all cached events to a JSON file.
        
        Args:
            filename (str): The name of the file to save to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(filename, 'w') as f:
                json.dump(self._cached_events, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving events to file: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Create an event manager instance
    manager = EventManager()
    
    # Example JavaScript code
    js_code = 'var eventManager = new EventManager("events/b69a294c-a074-4f4e-b949-4ae7de90c3e3", tooOld);'
    
    # Parse and fetch event data
    event_data = manager.parse_event_from_js(js_code)
    if event_data:
        print("Event data:", json.dumps(event_data, indent=2))
    
    # Get all active events
    active_events = manager.get_all_active_events()
    print(f"\nFound {len(active_events)} active events")
    
    # Save cached events to file
    if manager.save_events_to_file('events.json'):
        print("Events saved successfully") 