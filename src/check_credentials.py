import os
from dotenv import load_dotenv

def check_credentials():
    """Check and print the current Strava API credentials"""
    # Try to load from .env file
    env_path = os.path.join('config', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print("Found .env file in config directory.")
    else:
        print("No .env file found in config directory.")
    
    # Check environment variables
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
    
    print("\nStrava API Credentials:")
    print(f"STRAVA_CLIENT_ID: {'*****' + client_id[-4:] if client_id else 'Not set'}")
    print(f"STRAVA_CLIENT_SECRET: {'*' * 20 + client_secret[-4:] if client_secret else 'Not set'}")
    print(f"STRAVA_REFRESH_TOKEN: {'*' * 20 + refresh_token[-4:] if refresh_token else 'Not set'}")