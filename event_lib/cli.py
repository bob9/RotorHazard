#!/usr/bin/env python3
import argparse
import json
import requests
from event_lib import EventParser
from examples.event_manager import EventManager
from urllib.parse import urljoin


def fetch_from_url(url: str) -> dict:
    """Fetch data directly from a URL"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching from URL: {e}")
        return {}


def parse_js_code(args):
    """Handle parsing JavaScript code for event ID"""
    parser = EventParser(args.api_url)
    event_id = parser.extract_event_id(args.js_code)
    if event_id:
        print(f"Found event ID: {event_id}")
        if args.fetch:
            # Construct the full URL for the event
            url = f"http://{args.host}/events/{event_id}"
            print(f"Fetching from URL: {url}")
            event_data = fetch_from_url(url)
            if event_data:
                print("\nEvent data:")
                print(json.dumps(event_data, indent=2))
    else:
        print("No event ID found in the JavaScript code")


def list_events(args):
    """Handle listing all events"""
    # Construct the events URL
    url = f"http://{args.host}/events"
    print(f"Fetching events from: {url}")
    
    try:
        events = fetch_from_url(url)
        if args.active_only and isinstance(events, dict):
            # Filter active events if the response is a dictionary
            active_events = [
                event for event in events.get('events', [])
                if event.get('status') == 'active'
            ]
            print(f"\nFound {len(active_events)} active events:")
            print(json.dumps(active_events, indent=2))
        else:
            print("\nAll events:")
            print(json.dumps(events, indent=2))
        
        if args.save and events:
            try:
                with open(args.save, 'w') as f:
                    json.dump(events, f, indent=2)
                print(f"\nEvents saved to {args.save}")
            except Exception as e:
                print(f"\nError saving events to {args.save}: {e}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="RotorHazard Event Library CLI")
    parser.add_argument("--host", default="192.168.1.185:8080",
                      help="Host address (default: 192.168.1.185:8080)")
    parser.add_argument("--api-url", default="http://192.168.1.185:8080/api",
                      help="API base URL (default: http://192.168.1.185:8080/api)")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Parse JavaScript code command
    parse_parser = subparsers.add_parser("parse", help="Parse event ID from JavaScript code")
    parse_parser.add_argument("js_code", help="JavaScript code containing event initialization")
    parse_parser.add_argument("--fetch", action="store_true",
                           help="Fetch event data after parsing")
    
    # List events command
    list_parser = subparsers.add_parser("list", help="List events")
    list_parser.add_argument("--active-only", action="store_true",
                          help="Show only active events")
    list_parser.add_argument("--save", metavar="FILENAME",
                          help="Save events to JSON file")
    
    args = parser.parse_args()
    
    # Create parser instance
    event_parser = EventParser(args.api_url)
    
    # Download API data and find event ID
    event_id = event_parser.find_event_id()
    
    if event_id:
        print(f"Found event ID: {event_id}")
    else:
        print("No event ID found in API data")


if __name__ == "__main__":
    main() 