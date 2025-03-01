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
            response = requests.get("http://192.168.1.185:8080/api")
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


    #//get round data
    # http://192.168.1.185:8080/events/b69a294c-a074-4f4e-b949-4ae7de90c3e3/Rounds.json
    def get_round_data(self, event_id: str, round_id: str) -> Dict[str, Any]:
        endpoint = f"/events/{event_id}/Rounds.json"
        url = urljoin("http://192.168.1.185:8080", endpoint)
        response = requests.get(url)
        response.raise_for_status()

        #find the round id in the response
        for round in response.json():
            if round['ID'] == round_id:
                return round
        return None


    def get_race_data(self, event_id: str, race_id: str) -> Dict[str, Any]:
        """
        Fetch event data from the API for a given event ID and race ID.
        
        Args:
            event_id (str): The UUID of the event to fetch
            race_id (str): The ID of the race to fetch
            
        Returns:
            Dict[str, Any]: The race data from the API
            
        Raises:
            requests.RequestException: If the API request fails
        """

        # /api/events/b69a294c-a074-4f4e-b949-4ae7de90c3e3/a853dde7-e1e6-46e9-b6e1-ef33e65baf96/Race.json
        endpoint = f"/events/{event_id}/{race_id}/Race.json"
        url = urljoin("http://192.168.1.185:8080", endpoint)
        

        # http://192.168.1.185:8080/events/b69a294c-a074-4f4e-b949-4ae7de90c3e3/d0dbab88-586d-476f-b5e8-429d06b7c909/Race.json

        response = requests.get(url)
        response.raise_for_status()
        
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
        response.raise_for_status()
        
        return response.json()
