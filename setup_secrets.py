#!/usr/bin/env python3
"""
Google Secret Manager Setup Helper
Interactive script to create all required secrets
"""

import os
import sys
import json
from google.cloud import secretmanager


class SecretSetup:
    """Helper class for setting up secrets"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = secretmanager.SecretManagerServiceClient()
    
    def create_secret(self, secret_id: str, secret_value: str):
        """Create or update a secret"""
        parent = f"projects/{self.project_id}"
        
        try:
            # Try to create the secret
            secret = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
            print(f"✓ Created secret: {secret_id}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"ℹ Secret {secret_id} already exists, will update version")
            else:
                print(f"✗ Error creating secret {secret_id}: {e}")
                return False
        
        # Add secret version
        try:
            parent = f"projects/{self.project_id}/secrets/{secret_id}"
            payload = secret_value.encode("UTF-8")
            
            self.client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {"data": payload}
                }
            )
            print(f"✓ Added value to secret: {secret_id}")
            return True
        except Exception as e:
            print(f"✗ Error adding secret version: {e}")
            return False
    
    def create_from_file(self, secret_id: str, file_path: str):
        """Create secret from file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return self.create_secret(secret_id, content)
        except Exception as e:
            print(f"✗ Error reading file {file_path}: {e}")
            return False


def get_input(prompt: str, required: bool = True, multiline: bool = False) -> str:
    """Get user input with validation"""
    while True:
        print(f"\n{prompt}")
        if multiline:
            print("(Enter 'EOF' on a new line when done)")
            lines = []
            while True:
                line = input()
                if line == 'EOF':
                    break
                lines.append(line)
            value = '\n'.join(lines)
        else:
            value = input("> ").strip()
        
        if value or not required:
            return value
        print("This field is required. Please enter a value.")


def get_file_input(prompt: str, required: bool = True) -> str:
    """Get file path input with validation"""
    while True:
        print(f"\n{prompt}")
        path = input("> ").strip()
        
        if not path and not required:
            return ""
        
        if os.path.exists(path):
            return path
        
        print(f"File not found: {path}")
        if not required:
            retry = input("Try again? (y/n): ").lower()
            if retry != 'y':
                return ""


def main():
    """Main setup flow"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║      GOOGLE SECRET MANAGER SETUP HELPER                   ║
║      This script will help you set up all required        ║
║      secrets for the video automation system              ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Get project ID
    project_id = os.getenv('GCP_PROJECT_ID')
    if not project_id:
        project_id = get_input("Enter your Google Cloud Project ID:")
    else:
        print(f"\nUsing project ID from environment: {project_id}")
    
    setup = SecretSetup(project_id)
    
    print("\n" + "="*60)
    print("GOOGLE SHEETS CREDENTIALS")
    print("="*60)
    
    creds_file = get_file_input(
        "Enter path to Google Sheets service account JSON file:"
    )
    setup.create_from_file('google_sheets_credentials', creds_file)
    
    print("\n" + "="*60)
    print("OPENAI API")
    print("="*60)
    print("Get your API key from: https://platform.openai.com/api-keys")
    
    openai_key = get_input("Enter your OpenAI API key (starts with 'sk-'):")
    setup.create_secret('openai_api_key', openai_key)
    
    print("\n" + "="*60)
    print("HEYGEN API")
    print("="*60)
    print("Get your API key from: https://app.heygen.com/settings/api")
    
    heygen_key = get_input("Enter your HeyGen API key:")
    setup.create_secret('heygen_api_key', heygen_key)
    
    print("\n" + "="*60)
    print("YOUTUBE API")
    print("="*60)
    
    use_file = input("Do you have a YouTube OAuth credentials JSON file? (y/n): ").lower()
    if use_file == 'y':
        youtube_file = get_file_input("Enter path to YouTube OAuth JSON file:")
        setup.create_from_file('youtube_credentials', youtube_file)
    else:
        print("\nYou'll need to set up YouTube OAuth later.")
        print("See README.md for instructions.")
        youtube_json = get_input("Or paste YouTube credentials JSON now (optional):", required=False, multiline=True)
        if youtube_json:
            setup.create_secret('youtube_credentials', youtube_json)
    
    print("\n" + "="*60)
    print("INSTAGRAM API")
    print("="*60)
    print("Get from: https://developers.facebook.com")
    
    insta_token = get_input("Enter Instagram access token:")
    setup.create_secret('instagram_access_token', insta_token)
    
    insta_id = get_input("Enter Instagram account ID:")
    setup.create_secret('instagram_account_id', insta_id)
    
    print("\n" + "="*60)
    print("PINTEREST API")
    print("="*60)
    print("Get from: https://developers.pinterest.com")
    
    pinterest_token = get_input("Enter Pinterest access token:")
    setup.create_secret('pinterest_access_token', pinterest_token)
    
    pinterest_board = get_input("Enter Pinterest board ID:")
    setup.create_secret('pinterest_board_id', pinterest_board)
    
    print("\n" + "="*60)
    print("TWITTER API")
    print("="*60)
    print("Get from: https://developer.twitter.com")
    
    twitter_api_key = get_input("Enter Twitter API key (consumer key):")
    setup.create_secret('twitter_api_key', twitter_api_key)
    
    twitter_api_secret = get_input("Enter Twitter API secret (consumer secret):")
    setup.create_secret('twitter_api_secret', twitter_api_secret)
    
    twitter_token = get_input("Enter Twitter access token:")
    setup.create_secret('twitter_access_token', twitter_token)
    
    twitter_token_secret = get_input("Enter Twitter access token secret:")
    setup.create_secret('twitter_access_secret', twitter_token_secret)
    
    print("\n" + "="*60)
    print("✓ SETUP COMPLETE!")
    print("="*60)
    print("\nAll secrets have been created in Google Secret Manager.")
    print("\nNext steps:")
    print("1. Verify secrets: gcloud secrets list")
    print("2. Test setup: python test_setup.py")
    print("3. Run automation: python video_automation.py")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
