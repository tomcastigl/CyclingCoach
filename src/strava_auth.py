import requests
import json
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import time
import click

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
    click.echo("Opening Strava API settings page...")
    webbrowser.open("https://www.strava.com/settings/api")
    
    click.echo("\n=== STRAVA APP CREATION INSTRUCTIONS ===")
    click.echo("1. Log in to your Strava account if needed")
    click.echo("2. Fill out the 'My API Application' form:")
    click.echo("   - Application Name: CyclingCoach (or any name you prefer)")
    click.echo("   - Category: Training Analysis")
    click.echo("   - Website: http://localhost (for testing)")
    click.echo("   - Authorization Callback Domain: localhost")
    click.echo("3. Click 'Create' to create your application")
    click.echo("4. You'll see your Client ID and Client Secret on the next page")
    click.echo("===========================================\n")
    
    click.pause("Press any key once you've created your Strava application...")

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
    click.echo("Opening browser for Strava authorization...")
    webbrowser.open(auth_url)
    
    # Wait for the authorization code
    start_time = time.time()
    timeout = 120  # 2 minutes timeout
    
    with click.progressbar(
        length=timeout, 
        label='Waiting for authorization',
        show_eta=False
    ) as bar:
        for i in range(timeout):
            if AuthHandler.code is not None:
                break
            time.sleep(1)
            bar.update(1)
    
    if AuthHandler.code is None:
        click.echo("Authorization timed out. Please try again.")
        server.shutdown()
        return None
    
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
        click.echo(f"Error: {response.status_code}")
        click.echo(response.text)
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
    
    click.echo(f"Tokens saved to {file_path}")
    
    # Also set environment variables for current session
    os.environ['STRAVA_CLIENT_ID'] = str(tokens['client_id'])
    os.environ['STRAVA_CLIENT_SECRET'] = tokens['client_secret']
    os.environ['STRAVA_REFRESH_TOKEN'] = tokens['refresh_token']
    
    click.echo("Environment variables set for current session")

def main():
    """Main function to get and save Strava tokens"""
    click.echo(click.style("=== Strava Authentication Helper ===", fg="green", bold=True))
    click.echo("This script will help you set up Strava API authentication")
    click.echo("for the Cycling Coach application.")
    
    # Check if .env file already exists
    if os.path.exists('config/.env'):
        click.echo("\nFound existing configuration file.")
        use_existing = click.confirm("Would you like to use existing credentials?", default=True)
        if use_existing:
            click.echo("Using existing credentials.")
            return
    
    # Step 1: Create a Strava API application
    click.echo("\nStep 1: Create a Strava API application")
    create_app = click.confirm("Would you like to open the Strava API settings page to create an app?", default=True)
    if create_app:
        open_strava_api_settings()
    
    # Step 2: Get Client ID and Secret
    click.echo("\nStep 2: Enter your Strava API credentials")
    client_id = click.prompt("Client ID", type=str)
    client_secret = click.prompt("Client Secret", type=str, hide_input=True)
    
    # Step 3: Get authorization code
    click.echo("\nStep 3: Authorizing with Strava")
    auth_code = get_auth_code(client_id)
    
    if auth_code:
        click.echo(f"Authorization code received: {auth_code}")
        
        # Step 4: Exchange code for tokens
        click.echo("\nStep 4: Exchanging authorization code for tokens")
        tokens = exchange_code_for_tokens(client_id, client_secret, auth_code)
        
        if tokens:
            click.echo(click.style("Tokens received successfully!", fg="green"))
            
            # Update tokens with client_id and client_secret
            tokens['client_id'] = client_id
            tokens['client_secret'] = client_secret
            
            # Step 5: Save tokens
            click.echo("\nStep 5: Saving tokens to configuration file")
            save_tokens(tokens)
            
            click.echo(click.style("\n=== Authentication completed successfully! ===", fg="green", bold=True))
            click.echo("You can now use the Cycling Coach with your Strava account.")
            click.echo("Run 'coach fetch' to start fetching your activities.")
        else:
            click.echo(click.style("Failed to exchange code for tokens.", fg="red"))
    else:
        click.echo(click.style("Failed to get authorization code.", fg="red"))

if __name__ == "__main__":
    main() 