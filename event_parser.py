import re
import requests
from typing import Optional, Dict, Any
from urllib.parse import urljoin

class EventParser:
    """A class to parse event IDs from JavaScript EventManager initialization code and fetch from API."""
    
    def __init__(self, base_url: str):
        """
        Initialize the EventParser with the API base URL.
        
        Args:
            base_url (str): The base URL for the API
        """
        self.base_url = base_url.rstrip('/')

    @staticmethod
    def extract_event_id(js_code: str) -> Optional[str]:
        """
        Extract the event ID from JavaScript EventManager initialization code.
        
        Args:
            js_code (str): The JavaScript code containing the EventManager initialization
            
        Returns:
            Optional[str]: The extracted UUID if found, None otherwise
        """
        # Pattern to match: "events/UUID"
        pattern = r'events/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
        match = re.search(pattern, js_code)
        
        if match:
            return match.group(1)  # Return just the UUID part
        return None

    @staticmethod
    def extract_event_path(js_code: str) -> Optional[str]:
        """
        Extract the complete event path from JavaScript EventManager initialization code.
        
        Args:
            js_code (str): The JavaScript code containing the EventManager initialization
            
        Returns:
            Optional[str]: The complete event path if found, None otherwise
        """
        pattern = r'(events/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
        match = re.search(pattern, js_code)
        
        if match:
            return match.group(1)  # Return the full events/UUID path
        return None


    def get_race_data(self, event_id: str, race_id: str) -> Dict[str, Any]:
        """
        Fetch event data from the API for a given event ID.
        
        Args:
            event_id (str): The UUID of the event to fetch
            
        Returns:
            Dict[str, Any]: The event data from the API
            
        Raises:
            requests.RequestException: If the API request fails
        """
        endpoint = f"/events/{event_id}/{race_id}/Race.json"
        url = urljoin(self.base_url, endpoint)
        
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        return response.json()

    def get_event_data(self, event_id: str) -> Dict[str, Any]:
        """
        Fetch event data from the API for a given event ID.
        
        Args:
            event_id (str): The UUID of the event to fetch
            
        Returns:
            Dict[str, Any]: The event data from the API
            
        Raises:
            requests.RequestException: If the API request fails
        """
        endpoint = f"/events/{event_id}"
        url = urljoin(self.base_url, endpoint)
        
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        return response.json()

    def get_all_events(self) -> Dict[str, Any]:
        """
        Fetch all events from the API.
        
        Returns:
            Dict[str, Any]: All events data from the API
            
        Raises:
            requests.RequestException: If the API request fails
        """
        endpoint = "/events"
        url = urljoin(self.base_url, endpoint)
        
        response = requests.get(url)
        response.raise_for_status()
        
        return response.json()

# Example usage:
if __name__ == "__main__":
    parser = EventParser()
    
    # Example JavaScript code
    js_code = 'var eventManager = new EventManager("events/b69a294c-a074-4f4e-b949-4ae7de90c3e3", tooOld);'
    
    # Extract event ID from JavaScript code
    event_id = parser.extract_event_id(js_code)
    if event_id:
        try:
            # Fetch event data from API
            event_data = parser.get_event_data(event_id)
            print(f"Event data for {event_id}:")
            print(event_data)
            
            # Fetch all events
            all_events = parser.get_all_events()
            print("\nAll events:")
            print(all_events)
        except requests.RequestException as e:
            print(f"Error fetching data from API: {e}") 