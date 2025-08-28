"""
Spotify Authentication Service for Nova

This module handles Spotify OAuth 2.0 authentication and token management.
It provides methods to authenticate users and refresh access tokens automatically.
"""
import os
import json
import time
import webbrowser
import requests
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode, parse_qs, urlparse

class SpotifyAuth:
    """Handles Spotify OAuth 2.0 authentication and token management"""
    
    def __init__(self):
        """Initialize Spotify authentication service"""
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:3000/callback')
        
        # Token storage
        self.tokens_file = os.path.expanduser('~/.nova/spotify/tokens.json')
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0
        
        # Ensure tokens directory exists
        os.makedirs(os.path.dirname(self.tokens_file), exist_ok=True)
        
        # Load existing tokens if available
        self._load_tokens()
    
    def _load_tokens(self) -> None:
        """Load tokens from file if they exist"""
        try:
            if os.path.exists(self.tokens_file):
                with open(self.tokens_file, 'r') as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get('access_token')
                    self.refresh_token = tokens.get('refresh_token')
                    self.token_expires_at = tokens.get('expires_at', 0)
                    print("✅ Spotify tokens loaded from file")
        except Exception as e:
            print(f"⚠️ Error loading Spotify tokens: {e}")
    
    def _save_tokens(self) -> None:
        """Save tokens to file"""
        try:
            tokens = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_at': self.token_expires_at
            }
            with open(self.tokens_file, 'w') as f:
                json.dump(tokens, f, indent=2)
            print("✅ Spotify tokens saved to file")
        except Exception as e:
            print(f"⚠️ Error saving Spotify tokens: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated and has valid tokens"""
        if not self.access_token or not self.refresh_token:
            return False
        
        # Check if token is expired (with 5 minute buffer)
        if time.time() >= self.token_expires_at - 300:
            return self._refresh_access_token()
        
        return True
    
    def authenticate(self) -> bool:
        """Perform OAuth 2.0 authentication flow"""
        if not self.client_id or not self.client_secret:
            print("❌ Spotify credentials not found in environment variables")
            return False
        
        try:
            # Step 1: Generate authorization URL
            auth_url = self._get_authorization_url()
            
            # Step 2: Open browser for user authorization
            print("🌐 Opening browser for Spotify authorization...")
            print(f"🔗 Authorization URL: {auth_url}")
            webbrowser.open(auth_url)
            
            # Step 3: Start local server to receive callback
            print("🔄 Waiting for authorization callback...")
            auth_code = self._receive_authorization_code()
            
            if not auth_code:
                print("❌ Failed to receive authorization code")
                return False
            
            # Step 4: Exchange authorization code for tokens
            print("🔄 Exchanging authorization code for tokens...")
            if self._exchange_code_for_tokens(auth_code):
                print("✅ Spotify authentication successful!")
                return True
            else:
                print("❌ Failed to exchange authorization code for tokens")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def _get_authorization_url(self) -> str:
        """Generate Spotify authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join([
                'user-read-playback-state',
                'user-modify-playback-state', 
                'user-read-currently-playing',
                'playlist-read-private',
                'playlist-read-collaborative'
            ])
        }
        
        return f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    
    def _receive_authorization_code(self) -> Optional[str]:
        """Start local server to receive authorization callback"""
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import threading
            
            auth_code = [None]  # Use list to store value from inner function
            
            class CallbackHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    """Handle the OAuth callback"""
                    # Parse query parameters
                    query = urlparse(self.path).query
                    params = parse_qs(query)
                    
                    # Extract authorization code
                    if 'code' in params:
                        auth_code[0] = params['code'][0]
                        
                        # Send success response
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        
                        response = """
                        <html>
                        <body>
                        <h1>✅ Spotify Authorization Successful!</h1>
                        <p>You can close this window and return to Nova.</p>
                        <script>setTimeout(() => window.close(), 3000);</script>
                        </body>
                        </html>
                        """
                        self.wfile.write(response.encode())
                    else:
                        # Send error response
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        
                        response = """
                        <html>
                        <body>
                        <h1>❌ Authorization Failed</h1>
                        <p>No authorization code received.</p>
                        </body>
                        </html>
                        """
                        self.wfile.write(response.encode())
                
                def log_message(self, format, *args):
                    # Suppress server logs
                    pass
            
            # Start local server on 127.0.0.1:3000
            server = HTTPServer(('127.0.0.1', 3000), CallbackHandler)
            server.timeout = 300  # 5 minute timeout
            
            # Run server in separate thread
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            # Wait for authorization code or timeout
            start_time = time.time()
            while not auth_code[0] and time.time() - start_time < 300:
                time.sleep(0.1)
            
            # Stop server
            server.shutdown()
            server.server_close()
            
            return auth_code[0]
            
        except Exception as e:
            print(f"❌ Error receiving authorization code: {e}")
            return None
    
    def _exchange_code_for_tokens(self, auth_code: str) -> bool:
        """Exchange authorization code for access and refresh tokens"""
        try:
            token_url = "https://accounts.spotify.com/api/token"
            
            data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                
                self.access_token = tokens['access_token']
                self.refresh_token = tokens['refresh_token']
                self.token_expires_at = time.time() + tokens['expires_in']
                
                # Save tokens
                self._save_tokens()
                return True
            else:
                print(f"❌ Token exchange failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error exchanging code for tokens: {e}")
            return False
    
    def _refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token"""
        if not self.refresh_token:
            return False
        
        try:
            token_url = "https://accounts.spotify.com/api/token"
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                
                self.access_token = tokens['access_token']
                if 'refresh_token' in tokens:
                    self.refresh_token = tokens['refresh_token']
                self.token_expires_at = time.time() + tokens['expires_in']
                
                # Save updated tokens
                self._save_tokens()
                print("✅ Spotify access token refreshed")
                return True
            else:
                print(f"❌ Token refresh failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error refreshing access token: {e}")
            return False
    
    def get_access_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary"""
        if self.is_authenticated():
            return self.access_token
        return None
    
    def logout(self) -> None:
        """Clear all authentication tokens"""
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0
        
        # Remove tokens file
        try:
            if os.path.exists(self.tokens_file):
                os.remove(self.tokens_file)
                print("✅ Spotify tokens cleared")
        except Exception as e:
            print(f"⚠️ Error removing tokens file: {e}")
