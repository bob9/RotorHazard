import re
import requests
from typing import Optional, Dict, Any
from urllib.parse import urljoin


class EventParser:
    """A class to parse event IDs from JavaScript EventManager initialization code and fetch from API."""
    
    def __init__(self, base_url: str = "http://192.168.1.185:8080/api"):
        """
        Initialize the EventParser with the API base URL.
        
        Args:
            base_url (str): The base URL for the API
        """
        self.base_url = base_url.rstrip('/')

    def download_api_data(self) -> str:
        """
        Download data from the API.
        
        Returns:
            str: The API response text
        """
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error downloading from API: {e}")
            return ""

    def find_event_id(self) -> Optional[str]:
        """
        Download API data and find the event ID.
        
        Returns:
            Optional[str]: The event ID if found, None otherwise
        """
        api_data = self.download_api_data()
        if not api_data:
            return None

        # Pattern to match: "events/UUID"
        pattern = r'events/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
        match = re.search(pattern, api_data)
        
        if match:
            return match.group(1)  # Return just the UUID part
        return None

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
        response.raise_for_status()
        
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