import requests
import json
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import time

class AuthHandler(BaseHTTPRequestHandler):
    """Handle the OAuth callback from Strava"""
    code = None
    
    def do_GET(self):
        """Process the GET request with the authorization code"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Extract the authorization code from the URL
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params:
            AuthHandler.code = params['code'][0]
            
            # Send a success message to the browser
            response = f"""
            <html>
            <body>
                <h1>Authorization Successful!</h1>
                <p>You can now close this window and return to the application.</p>
            </body>
            </html>
            """
        else:
            # Send an error message to the browser
            response = f"""
            <html>
            <body>
                <h1>Authorization Failed!</h1>
                <p>Error: No authorization code received.</p>
                <p>Please try again.</p>
            </body>
            </html>
            """
        
        self.wfile.write(response.encode())

def open_strava_api_settings():
    """Open the Strava API settings page in a browser"""
    print("Opening Strava API settings page...")
    webbrowser.open("https://www.strava.com/settings/api")
    
    print("\n=== STRAVA APP CREATION INSTRUCTIONS ===")
    print("1. Log in to your Strava account if needed")
    print("2. Fill out the 'My API Application' form:")
    print("   - Application Name: CyclingCoach (or any name you prefer)")
    print("   - Category: Training Analysis")
    print("   - Website: http://localhost (for testing)")
    print("   - Authorization Callback Domain: localhost")
    print("3. Click 'Create' to create your application")
    print("4. You'll see your Client ID and Client Secret on the next page")
    print("===========================================\n")
    
    input("Press Enter once you've created your Strava application...")

def get_auth_code(client_id):
    """Get the authorization code by opening a browser window"""
    # Strava authorization URL
    auth_url = f"https://www.strava.com/oauth/authorize?client_id={client_id}&redirect_uri=http://localhost:8000&response_type=code&scope=activity:read_all"
    
    # Start a simple HTTP server to handle the callback
    server = HTTPServer(('localhost', 8000), AuthHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Open the browser for the user to authorize
    print("Opening browser for Strava authorization...")
    webbrowser.open(auth_url)
    
    # Wait for the authorization code
    start_time = time.time()
    timeout = 120  # 2 minutes timeout
    
    while AuthHandler.code is None:
        if time.time() - start_time > timeout:
            print("Authorization timed out. Please try again.")
            server.shutdown()
            return None
        time.sleep(1)
    
    # Shutdown the server
    server.shutdown()
    
    return AuthHandler.code

def exchange_code_for_tokens(client_id, client_secret, code):
    """Exchange the authorization code for tokens"""
    token_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(token_url, data=payload)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def save_tokens(tokens, file_path='config/.env'):
    """Save tokens to the .env file"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Create or update the .env file
    with open(file_path, 'w') as f:
        f.write(f"STRAVA_CLIENT_ID={tokens['client_id']}\n")
        f.write(f"STRAVA_CLIENT_SECRET={tokens['client_secret']}\n")
        f.write(f"STRAVA_REFRESH_TOKEN={tokens['refresh_token']}\n")
    
    print(f"Tokens saved to {file_path}")
    
    # Also set environment variables for current session
    os.environ['STRAVA_CLIENT_ID'] = str(tokens['client_id'])
    os.environ['STRAVA_CLIENT_SECRET'] = tokens['client_secret']
    os.environ['STRAVA_REFRESH_TOKEN'] = tokens['refresh_token']
    
    print("Environment variables set for current session")

def main():
    """Main function to get and save Strava tokens"""
    print("=== Strava Authentication Helper ===")
    print("This script will help you set up Strava API authentication")
    print("for the Cycling Coach application.")
    
    # Check if .env file already exists
    if os.path.exists('config/.env'):
        print("\nFound existing configuration file.")
        use_existing = input("Would you like to use existing credentials? (y/n): ").lower()
        if use_existing == 'y':
            print("Using existing credentials.")
            return
    
    # Step 1: Create a Strava API application
    print("\nStep 1: Create a Strava API application")
    create_app = input("Would you like to open the Strava API settings page to create an app? (y/n): ").lower()
    if create_app == 'y':
        open_strava_api_settings()
    
    # Step 2: Get Client ID and Secret
    print("\nStep 2: Enter your Strava API credentials")
    client_id = input("Client ID: ")
    client_secret = input("Client Secret: ")
    
    # Step 3: Get authorization code
    print("\nStep 3: Authorizing with Strava")
    auth_code = get_auth_code(client_id)
    
    if auth_code:
        print(f"Authorization code received: {auth_code}")
        
        # Step 4: Exchange code for tokens
        print("\nStep 4: Exchanging authorization code for tokens")
        tokens = exchange_code_for_tokens(client_id, client_secret, auth_code)
        
        if tokens:
            print("Tokens received successfully!")
            
            # Update tokens with client_id and client_secret
            tokens['client_id'] = client_id
            tokens['client_secret'] = client_secret
            
            # Step 5: Save tokens
            print("\nStep 5: Saving tokens to configuration file")
            save_tokens(tokens)
            
            print("\n=== Authentication completed successfully! ===")
            print("You can now use the Cycling Coach with your Strava account.")
            print("Run 'python src/main.py' to start using the application.")
        else:
            print("Failed to exchange code for tokens.")
    else:
        print("Failed to get authorization code.")

if __name__ == "__main__":
    main() 