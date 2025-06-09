import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

def load_credentials():
    """Load Strava API credentials from .env file"""
    # Try to load from .env file
    env_path = os.path.join('config', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
    
    if not client_id or not client_secret or not refresh_token:
        print("Error: Strava API credentials not found.")
        print("Please run 'python src/strava_auth.py' to set up your credentials.")
        return None, None, None
    
    return client_id, client_secret, refresh_token

def get_access_token(client_id, client_secret, refresh_token):
    """Get a new access token using the refresh token"""
    auth_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    try:
        response = requests.post(auth_url, data=payload)
        response_json = response.json()
        
        if 'access_token' in response_json:
            return response_json['access_token']
        else:
            print("Error: No access token in the response.")
            print(response_json)
            return None
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None

def create_activity(access_token):
    """Create a sample test activity using Strava API"""
    if not access_token:
        return None
    
    activities_url = "https://www.strava.com/api/v3/activities"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Get user input for activity
    print("\nCreating a Sample Test Activity")
    print("==============================")
    print("This will create a manual activity on your Strava account.")
    
    # Default values
    name = input("Activity Name (default: 'Test Ride'): ") or "Test Ride"
    
    # Sport type
    print("\nSelect Sport Type:")
    print("1. Ride")
    print("2. Run")
    print("3. Swim")
    print("4. Walk")
    print("5. Hike")
    print("6. AlpineSki")
    print("7. BackcountrySki")
    print("8. Canoeing")
    print("9. Crossfit")
    print("10. EBikeRide")
    sport_choice = input("Enter choice (default: 1): ") or "1"
    
    sport_types = {
        "1": "Ride",
        "2": "Run",
        "3": "Swim",
        "4": "Walk",
        "5": "Hike",
        "6": "AlpineSki",
        "7": "BackcountrySki",
        "8": "Canoeing",
        "9": "Crossfit",
        "10": "EBikeRide"
    }
    
    sport_type = sport_types.get(sport_choice, "Ride")
    
    # Time and distance
    start_date_input = input(f"Start Date (default: today, format YYYY-MM-DD): ")
    if start_date_input:
        try:
            start_date = datetime.strptime(start_date_input, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Using today.")
            start_date = datetime.now()
    else:
        start_date = datetime.now()
    
    start_time_input = input(f"Start Time (default: {datetime.now().strftime('%H:%M')}, format HH:MM): ")
    if start_time_input:
        try:
            hour, minute = map(int, start_time_input.split(':'))
            start_date = start_date.replace(hour=hour, minute=minute)
        except (ValueError, IndexError):
            print("Invalid time format. Using current time.")
    
    start_date_local = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    elapsed_time_input = input("Duration in minutes (default: 60): ") or "60"
    elapsed_time = int(float(elapsed_time_input) * 60)  # Convert to seconds
    
    distance_input = input("Distance in kilometers (default: 20): ") or "20"
    distance = float(distance_input) * 1000  # Convert to meters
    
    description = input("Description (optional): ")
    
    # Create the payload
    payload = {
        'name': name,
        'type': sport_type,
        'sport_type': sport_type,
        'start_date_local': start_date_local,
        'elapsed_time': elapsed_time,
        'distance': distance
    }
    
    if description:
        payload['description'] = description
    
    # Ask if it's a trainer activity
    trainer_input = input("Is this a trainer activity? (y/n, default: n): ").lower()
    if trainer_input == 'y':
        payload['trainer'] = 1
    
    # Ask if it's a commute
    commute_input = input("Is this a commute? (y/n, default: n): ").lower()
    if commute_input == 'y':
        payload['commute'] = 1
    
    # Make the request
    try:
        response = requests.post(activities_url, headers=headers, json=payload)
        
        if response.status_code == 201:
            activity = response.json()
            print(f"\nActivity created successfully!")
            print(f"Name: {activity.get('name')}")
            print(f"Type: {activity.get('sport_type')}")
            print(f"Distance: {activity.get('distance')/1000:.2f} km")
            print(f"Duration: {activity.get('elapsed_time')/60:.2f} minutes")
            print(f"View on Strava: https://www.strava.com/activities/{activity.get('id')}")
            return activity
        else:
            print(f"Error creating activity: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error creating activity: {e}")
        return None