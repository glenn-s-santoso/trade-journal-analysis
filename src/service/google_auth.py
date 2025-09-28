"""Google OAuth authentication service for Drive and Gmail APIs."""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import GoogleAuthError

from src.constants.env import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_PROJECT_ID, GOOGLE_REFRESH_TOKEN

# Define the scopes required for both Drive and Gmail
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.file']
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
ALL_SCOPES = DRIVE_SCOPES + GMAIL_SCOPES

# Paths for credential storage
CREDENTIALS_DIR = Path("credentials")
TOKEN_PATH = CREDENTIALS_DIR / "token.json"
CLIENT_SECRETS_PATH = CREDENTIALS_DIR / "client_secrets.json"


class GoogleAuthService:
    """Service for handling Google OAuth authentication."""

    def __init__(self, scopes: Optional[List[str]] = None):
        """Initialize the Google Auth Service.
        
        Args:
            scopes: List of OAuth scopes to request. If None, uses all scopes.
        """
        self.scopes = scopes or ALL_SCOPES
        
        # Create credentials directory if it doesn't exist
        if not CREDENTIALS_DIR.exists():
            CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

    def get_credentials(self) -> Optional[Credentials]:
        """Get valid user credentials from storage or environment variables.
        
        If no valid credentials are found, the user will be prompted to log in.
        
        Returns:
            Credentials or None if couldn't authenticate
        """
        creds = None

        # First try to load from token.json
        if TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), self.scopes)
            
            # If credentials are valid and not expired, return them
            if creds and creds.valid and not creds.expired:
                return creds
            
            # If credentials are expired but have a refresh token, try to refresh
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self._save_credentials(creds)
                    return creds
                except GoogleAuthError:
                    print("Failed to refresh credentials from token file.")
                    creds = None

        # Try to load from environment variables
        creds = self._get_credentials_from_env()
        if creds:
            return creds

        # If no valid credentials, try to get new ones
        return self._get_new_credentials()

    def _get_credentials_from_env(self) -> Optional[Credentials]:
        """Try to load credentials from environment variables."""
        
        if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REFRESH_TOKEN:
            creds = Credentials(
                token=None,
                refresh_token=GOOGLE_REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                scopes=self.scopes,
            )
            
            try:
                creds.refresh(Request())
                self._save_credentials(creds)
                print("Successfully refreshed credentials from environment variables")
                return creds
            except GoogleAuthError:
                print("Failed to refresh credentials from environment variables")
                # Fall back to user refresh flow if env variables don't work
                return self.refresh_user_credentials()
        
        return None

    def refresh_user_credentials(self) -> Optional[Credentials]:
        """Refresh user credentials using interactive flow with provided client ID and secret.
        
        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            
        Returns:
            Credentials object or None if the refresh fails
        """
        try:
            # Create client config dict from provided credentials
            client_config = {
                "installed": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "project_id": GOOGLE_PROJECT_ID,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": ["http://localhost"]
                }
            }
            
            # Create flow from client config dict
            flow = InstalledAppFlow.from_client_config(
                client_config,
                self.scopes
            )
            
            # Run the flow to get credentials
            creds = flow.run_local_server(
                port=0,
                access_type="offline",
                prompt="consent",
                include_granted_scopes="true"
            )
            
            # Save the credentials
            self._save_credentials(creds)
            print("Successfully refreshed user credentials via interactive flow")
            return creds
            
        except Exception as e:
            print(f"Error during interactive authentication flow: {e}")
            return None
    
    def _get_new_credentials(self) -> Optional[Credentials]:
        """Get new credentials via OAuth flow."""
        if CLIENT_SECRETS_PATH.exists():
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CLIENT_SECRETS_PATH), 
                    self.scopes
                )
                creds = flow.run_local_server(
                    port=0,
                    access_type="offline",
                    prompt="consent",
                    include_granted_scopes="true"
                )
                self._save_credentials(creds)
                return creds
            except Exception as e:
                print(f"Error during authentication flow: {e}")
        else:
            print(f"Client secrets file not found at {CLIENT_SECRETS_PATH}")
            
            # Try with environment variables
            if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
                return self.refresh_user_credentials()
            
        return None

    def _save_credentials(self, creds: Credentials) -> None:
        """Save credentials to token.json file."""
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    def create_client_secrets(self) -> None:
        """Create a client_secrets.json file from provided credentials."""
        client_config = {
            "installed": {
                "client_id": GOOGLE_CLIENT_ID,
                "project_id": GOOGLE_PROJECT_ID,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
            }
        }
        
        with open(CLIENT_SECRETS_PATH, 'w') as f:
            json.dump(client_config, f)
