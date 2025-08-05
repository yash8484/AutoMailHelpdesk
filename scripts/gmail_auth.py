#!/usr/bin/env python3
"""
Gmail OAuth2 Authentication Script

This script helps you authenticate with Gmail API and obtain refresh/access tokens.
Run this script to set up Gmail API authentication for the AutoMailHelpdesk.
"""

import os
import json
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes we need
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.labels'
]

def create_credentials_file():
    """Create the credentials.json file from the provided credentials."""
    credentials_data = {
        "installed": {
            "client_id": "24910683842-gm81kpcqgl42bvm0oa6u0qee3j7te27u.apps.googleusercontent.com",
            "project_id": "my-project-35035-ai-agent",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "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",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open('credentials.json', 'w') as f:
        json.dump(credentials_data, f, indent=2)
    
    print("✅ Created credentials.json file")

def authenticate_gmail():
    """Authenticate with Gmail API and return credentials."""
    creds = None
    
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def test_gmail_connection(creds):
    """Test the Gmail API connection."""
    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # Get user profile
        profile = service.users().getProfile(userId='me').execute()
        print(f"✅ Successfully connected to Gmail API")
        print(f"📧 Email: {profile['emailAddress']}")
        print(f"📊 Messages Total: {profile['messagesTotal']}")
        print(f"📥 Messages Unread: {profile['threadsUnread']}")
        
        return True
        
    except HttpError as error:
        print(f"❌ Error connecting to Gmail API: {error}")
        return False

def get_tokens_info(creds):
    """Get and display token information."""
    print("\n🔑 Token Information:")
    print(f"Refresh Token: {creds.refresh_token}")
    print(f"Access Token: {creds.token}")
    print(f"Token Expiry: {creds.expiry}")
    
    # Save tokens to a file for easy copying
    tokens_info = {
        "refresh_token": creds.refresh_token,
        "access_token": creds.token,
        "expiry": str(creds.expiry) if creds.expiry else None
    }
    
    with open('tokens.json', 'w') as f:
        json.dump(tokens_info, f, indent=2)
    
    print("\n💾 Token information saved to tokens.json")
    print("📝 Copy these values to your .env file or settings.py")

def main():
    """Main function to run the Gmail authentication process."""
    print("🚀 Gmail API Authentication Setup")
    print("=" * 50)
    
    # Create credentials file
    create_credentials_file()
    
    # Authenticate
    print("\n🔐 Starting Gmail authentication...")
    print("📱 A browser window will open for you to authenticate with Google")
    print("🔗 Please authorize the application to access your Gmail account")
    
    try:
        creds = authenticate_gmail()
        
        # Test connection
        print("\n🧪 Testing Gmail API connection...")
        if test_gmail_connection(creds):
            # Get token information
            get_tokens_info(creds)
            
            print("\n✅ Gmail API setup completed successfully!")
            print("\n📋 Next steps:")
            print("1. Copy the refresh_token and access_token from tokens.json")
            print("2. Update your .env file or settings.py with these values")
            print("3. Restart your AutoMailHelpdesk application")
            
        else:
            print("❌ Failed to connect to Gmail API")
            
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        print("💡 Make sure you have the correct credentials and internet connection")

if __name__ == '__main__':
    main() 