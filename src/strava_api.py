import os
import requests
import json
import time
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

class StravaAPI:
    def __init__(self, config_path='config'):
        # Load environment variables
        load_dotenv(os.path.join(config_path, '.env'))
        
        # Strava API credentials
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        self.refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
        
        # API endpoints
        self.auth_url = "https://www.strava.com/oauth/token"
        self.activities_url = "https://www.strava.com/api/v3/athlete/activities"
        
        # Get access token
        self.access_token = self._get_access_token()
    
    def _get_access_token(self):
        """Get a new access token using the refresh token"""
        if not self.refresh_token:
            print("Error: No refresh token available. Please run strava_auth.py first.")
            return None
            
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(self.auth_url, data=payload)
            response_json = response.json()
            
            if 'refresh_token' in response_json:
                # Save the new refresh token
                self.refresh_token = response_json['refresh_token']
                
                # Update the .env file
                env_path = os.path.join('config', '.env')
                if os.path.exists(env_path):
                    with open(env_path, 'r') as f:
                        lines = f.readlines()
                    
                    with open(env_path, 'w') as f:
                        for line in lines:
                            if line.startswith('STRAVA_REFRESH_TOKEN='):
                                f.write(f'STRAVA_REFRESH_TOKEN={self.refresh_token}\n')
                            else:
                                f.write(line)
                
                return response_json['access_token']
            else:
                print("Error: No refresh token in the response.")
                print(response_json)
                return None
        except Exception as e:
            print(f"Error getting access token: {e}")
            return None
    
    def get_activities(self, days=7):
        """Get activities from the past specified days"""
        if not self.access_token:
            print("Error: No access token available. Please run strava_auth.py first.")
            return None
            
        # Calculate time period
        after_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
        
        # Set up headers and parameters
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {'after': after_timestamp, 'per_page': 200}
        
        # Make the request
        try:
            response = requests.get(self.activities_url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(response.text)
                return None
            
            return response.json()
        except Exception as e:
            print(f"Error getting activities: {e}")
            return None
    
    def parse_activities(self, activities):
        """Parse activities data into a DataFrame"""
        if not activities:
            return None
        
        # Extract relevant fields
        parsed_activities = []
        for activity in activities:
            parsed_activity = {
                'id': activity.get('id'),
                'name': activity.get('name'),
                'type': activity.get('type'),
                'start_date_local': activity.get('start_date_local'),
                'distance': activity.get('distance'),  # in meters
                'moving_time': activity.get('moving_time'),  # in seconds
                'elapsed_time': activity.get('elapsed_time'),  # in seconds
                'total_elevation_gain': activity.get('total_elevation_gain'),  # in meters
                'average_speed': activity.get('average_speed'),  # in m/s
                'max_speed': activity.get('max_speed'),  # in m/s
                'average_heartrate': activity.get('average_heartrate'),
                'max_heartrate': activity.get('max_heartrate'),
                'average_watts': activity.get('average_watts'),
                'weighted_average_watts': activity.get('weighted_average_watts'),
                'kilojoules': activity.get('kilojoules'),
                'device_watts': activity.get('device_watts'),
                'max_watts': activity.get('max_watts'),
                'suffer_score': activity.get('suffer_score'),
                'has_heartrate': activity.get('has_heartrate'),
                'average_cadence': activity.get('average_cadence'),
                'average_temp': activity.get('average_temp'),
                'achievement_count': activity.get('achievement_count'),
                'kudos_count': activity.get('kudos_count'),
                'comment_count': activity.get('comment_count'),
                'athlete_count': activity.get('athlete_count'),
                'calories': activity.get('calories'),
            }
            parsed_activities.append(parsed_activity)
        
        # Convert to DataFrame
        df = pd.DataFrame(parsed_activities)
        
        # Convert date string to datetime
        if 'start_date_local' in df.columns:
            df['start_date_local'] = pd.to_datetime(df['start_date_local'])
        
        return df
    
    def save_activities(self, df, file_path='data/activities.csv'):
        """Save activities DataFrame to a CSV file"""
        if df is not None:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            df.to_csv(file_path, index=False)
            print(f"Activities saved to {file_path}")
        else:
            print("No activities to save")
    
    def get_activity_streams(self, activity_id):
        """Get detailed data streams for a specific activity"""
        streams_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {
            'keys': 'time,distance,latlng,altitude,velocity_smooth,heartrate,cadence,watts,temp,moving,grade_smooth',
            'key_by_type': True
        }
        
        response = requests.get(streams_url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return None
        
        return response.json()