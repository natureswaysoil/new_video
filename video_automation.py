#!/usr/bin/env python3
"""
Video Automation System
Reads products from Google Sheets, generates scripts with OpenAI,
creates videos with HeyGen, and posts to social media platforms.
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Third-party imports
import gspread
from google.cloud import secretmanager
from google.oauth2.service_account import Credentials
import openai
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SecretManager:
    """Handles retrieval of secrets from Google Secret Manager"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = secretmanager.SecretManagerServiceClient()
    
    def get_secret(self, secret_name: str) -> str:
        """Retrieve a secret value"""
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode('UTF-8')
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_name}: {e}")
            raise


class GoogleSheetsClient:
    """Handles Google Sheets operations"""
    
    def __init__(self, credentials_json: str, spreadsheet_id: str):
        creds = Credentials.from_service_account_info(
            json.loads(credentials_json),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.client = gspread.authorize(creds)
        self.spreadsheet_id = spreadsheet_id
        self.sheet = None
    
    def connect(self, worksheet_index: int = 0):
        """Connect to the spreadsheet"""
        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            self.sheet = spreadsheet.get_worksheet(worksheet_index)
            logger.info(f"Connected to Google Sheet: {spreadsheet.title}")
        except Exception as e:
            logger.error(f"Error connecting to Google Sheets: {e}")
            raise
    
    def get_all_products(self) -> List[Dict]:
        """Get all products from the sheet"""
        try:
            records = self.sheet.get_all_records()
            logger.info(f"Retrieved {len(records)} products from sheet")
            return records
        except Exception as e:
            logger.error(f"Error reading products: {e}")
            raise
    
    def get_last_processed_row(self) -> int:
        """Get the last processed row number from tracking column"""
        try:
            # Assuming there's a 'processed' or 'last_used' column
            # If not, this will be tracked in a separate state file
            return 0
        except Exception as e:
            logger.warning(f"Could not get last processed row: {e}")
            return 0
    
    def mark_row_processed(self, row_index: int, timestamp: str):
        """Mark a row as processed with timestamp"""
        try:
            # Update a 'Last Processed' column (adjust column letter as needed)
            self.sheet.update_cell(row_index + 2, self.sheet.col_count, timestamp)
        except Exception as e:
            logger.warning(f"Could not mark row {row_index} as processed: {e}")


class ScriptGenerator:
    """Generates video scripts using OpenAI"""
    
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
    
    def generate_script(self, product_data: Dict, platform: str = "general") -> str:
        """Generate a video script for a product"""
        try:
            prompt = self._create_prompt(product_data, platform)
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a creative video script writer specializing in engaging product marketing content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            script = response.choices[0].message.content
            logger.info(f"Generated script for product: {product_data.get('name', 'Unknown')}")
            return script
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            raise
    
    def _create_prompt(self, product_data: Dict, platform: str) -> str:
        """Create a prompt based on product data and platform"""
        product_name = product_data.get('name', product_data.get('Name', 'Product'))
        description = product_data.get('description', product_data.get('Description', ''))
        price = product_data.get('price', product_data.get('Price', ''))
        
        platform_specs = {
            "youtube": "Create a 60-90 second engaging video script",
            "instagram": "Create a 30-60 second captivating reel script",
            "pinterest": "Create a 15-30 second inspiring video script",
            "twitter": "Create a 15-30 second attention-grabbing video script"
        }
        
        spec = platform_specs.get(platform.lower(), "Create a 30-60 second video script")
        
        prompt = f"""
{spec} for this product:

Product Name: {product_name}
Description: {description}
Price: {price}

Requirements:
- Hook viewers in the first 3 seconds
- Highlight key benefits and features
- Include a clear call-to-action
- Keep it conversational and enthusiastic
- Make it suitable for text-to-speech narration

Format the script as natural spoken dialogue without stage directions.
"""
        return prompt


class HeyGenClient:
    """Handles video creation with HeyGen API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.heygen.com/v2"
        self.headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def create_video(self, script: str, product_data: Dict) -> Dict:
        """Create a video using HeyGen"""
        try:
            # HeyGen API endpoint for video generation
            url = f"{self.base_url}/video/generate"
            
            payload = {
                "video_inputs": [{
                    "character": {
                        "type": "avatar",
                        "avatar_id": "default_avatar",  # Configure your preferred avatar
                        "avatar_style": "normal"
                    },
                    "voice": {
                        "type": "text",
                        "input_text": script,
                        "voice_id": "en-US-JennyNeural",  # Configure your preferred voice
                        "speed": 1.0
                    },
                    "background": {
                        "type": "color",
                        "value": "#FFFFFF"  # Or use image URL
                    }
                }],
                "dimension": {
                    "width": 1920,
                    "height": 1080
                },
                "aspect_ratio": "16:9"
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            video_id = result.get('data', {}).get('video_id')
            
            if video_id:
                logger.info(f"Video creation initiated: {video_id}")
                return self._wait_for_video(video_id)
            else:
                raise Exception("No video_id returned from HeyGen")
                
        except Exception as e:
            logger.error(f"Error creating video with HeyGen: {e}")
            raise
    
    def _wait_for_video(self, video_id: str, max_wait: int = 600) -> Dict:
        """Poll for video completion"""
        url = f"{self.base_url}/video/{video_id}"
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                result = response.json()
                
                status = result.get('data', {}).get('status')
                
                if status == 'completed':
                    video_url = result.get('data', {}).get('video_url')
                    logger.info(f"Video completed: {video_url}")
                    return {
                        'video_id': video_id,
                        'video_url': video_url,
                        'status': 'completed'
                    }
                elif status == 'failed':
                    raise Exception(f"Video generation failed: {result}")
                
                logger.info(f"Video status: {status}, waiting...")
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error checking video status: {e}")
                raise
        
        raise TimeoutError(f"Video generation timed out after {max_wait} seconds")
    
    def download_video(self, video_url: str, output_path: str) -> str:
        """Download the generated video"""
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video downloaded to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            raise


class YouTubeUploader:
    """Handles YouTube video uploads"""
    
    def __init__(self, credentials_json: str):
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        self.credentials = Credentials.from_authorized_user_info(json.loads(credentials_json))
        self.youtube = build('youtube', 'v3', credentials=self.credentials)
        self.MediaFileUpload = MediaFileUpload
    
    def upload(self, video_path: str, title: str, description: str, tags: List[str]) -> str:
        """Upload video to YouTube"""
        try:
            body = {
                'snippet': {
                    'title': title[:100],  # YouTube title limit
                    'description': description[:5000],  # YouTube description limit
                    'tags': tags[:500],  # YouTube tags limit
                    'categoryId': '22'  # People & Blogs
                },
                'status': {
                    'privacyStatus': 'public',  # or 'private' or 'unlisted'
                    'selfDeclaredMadeForKids': False
                }
            }
            
            media = self.MediaFileUpload(video_path, chunksize=-1, resumable=True)
            
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = request.execute()
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"Uploaded to YouTube: {video_url}")
            return video_url
            
        except Exception as e:
            logger.error(f"Error uploading to YouTube: {e}")
            raise


class InstagramUploader:
    """Handles Instagram video uploads"""
    
    def __init__(self, access_token: str, instagram_account_id: str):
        self.access_token = access_token
        self.account_id = instagram_account_id
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def upload(self, video_url: str, caption: str) -> str:
        """Upload video to Instagram as Reel"""
        try:
            # Step 1: Create container
            container_url = f"{self.base_url}/{self.account_id}/media"
            container_params = {
                'media_type': 'REELS',
                'video_url': video_url,
                'caption': caption[:2200],  # Instagram caption limit
                'access_token': self.access_token
            }
            
            container_response = requests.post(container_url, params=container_params)
            container_response.raise_for_status()
            container_id = container_response.json()['id']
            
            # Step 2: Wait for processing
            time.sleep(30)  # Give Instagram time to process
            
            # Step 3: Publish
            publish_url = f"{self.base_url}/{self.account_id}/media_publish"
            publish_params = {
                'creation_id': container_id,
                'access_token': self.access_token
            }
            
            publish_response = requests.post(publish_url, params=publish_params)
            publish_response.raise_for_status()
            media_id = publish_response.json()['id']
            
            logger.info(f"Uploaded to Instagram: {media_id}")
            return media_id
            
        except Exception as e:
            logger.error(f"Error uploading to Instagram: {e}")
            raise


class PinterestUploader:
    """Handles Pinterest video uploads"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.pinterest.com/v5"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def upload(self, video_url: str, title: str, description: str, board_id: str) -> str:
        """Upload video to Pinterest"""
        try:
            url = f"{self.base_url}/pins"
            
            payload = {
                "title": title[:100],
                "description": description[:500],
                "board_id": board_id,
                "media_source": {
                    "source_type": "video_url",
                    "url": video_url
                }
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            pin_id = response.json()['id']
            pin_url = f"https://www.pinterest.com/pin/{pin_id}"
            
            logger.info(f"Uploaded to Pinterest: {pin_url}")
            return pin_url
            
        except Exception as e:
            logger.error(f"Error uploading to Pinterest: {e}")
            raise


class TwitterUploader:
    """Handles Twitter video uploads"""
    
    def __init__(self, api_key: str, api_secret: str, access_token: str, access_secret: str):
        import tweepy
        
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
        self.api = tweepy.API(auth)
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
    
    def upload(self, video_path: str, caption: str) -> str:
        """Upload video to Twitter"""
        try:
            # Upload media
            media = self.api.media_upload(video_path, media_category='tweet_video')
            
            # Wait for processing
            self._wait_for_media_processing(media.media_id)
            
            # Post tweet
            response = self.client.create_tweet(
                text=caption[:280],  # Twitter character limit
                media_ids=[media.media_id]
            )
            
            tweet_id = response.data['id']
            tweet_url = f"https://twitter.com/user/status/{tweet_id}"
            
            logger.info(f"Uploaded to Twitter: {tweet_url}")
            return tweet_url
            
        except Exception as e:
            logger.error(f"Error uploading to Twitter: {e}")
            raise
    
    def _wait_for_media_processing(self, media_id: str, max_wait: int = 120):
        """Wait for Twitter to process the video"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = self.api.get_media_upload_status(media_id)
            
            if status.processing_info['state'] == 'succeeded':
                return
            elif status.processing_info['state'] == 'failed':
                raise Exception("Twitter media processing failed")
            
            time.sleep(5)
        
        raise TimeoutError("Twitter media processing timed out")


class StateManager:
    """Manages automation state (current row, etc.)"""
    
    def __init__(self, state_file: str = "automation_state.json"):
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load state: {e}")
        
        return {'current_row': 0, 'last_run': None}
    
    def save_state(self):
        """Save state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def get_current_row(self) -> int:
        """Get current row index"""
        return self.state.get('current_row', 0)
    
    def set_current_row(self, row: int):
        """Set current row index"""
        self.state['current_row'] = row
        self.state['last_run'] = datetime.now().isoformat()
        self.save_state()
    
    def reset(self):
        """Reset to beginning"""
        self.state['current_row'] = 0
        self.save_state()


class VideoAutomation:
    """Main automation orchestrator"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.secret_manager = SecretManager(config['gcp_project_id'])
        self.state_manager = StateManager()
        
        # Initialize clients
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize all service clients"""
        logger.info("Initializing clients...")
        
        # Get secrets
        secrets = self._get_all_secrets()
        
        # Google Sheets
        self.sheets_client = GoogleSheetsClient(
            secrets['google_sheets_credentials'],
            self.config['spreadsheet_id']
        )
        self.sheets_client.connect()
        
        # OpenAI
        self.script_generator = ScriptGenerator(secrets['openai_api_key'])
        
        # HeyGen
        self.heygen_client = HeyGenClient(secrets['heygen_api_key'])
        
        # Social media
        self.youtube_uploader = YouTubeUploader(secrets['youtube_credentials'])
        self.instagram_uploader = InstagramUploader(
            secrets['instagram_access_token'],
            secrets['instagram_account_id']
        )
        self.pinterest_uploader = PinterestUploader(secrets['pinterest_access_token'])
        self.twitter_uploader = TwitterUploader(
            secrets['twitter_api_key'],
            secrets['twitter_api_secret'],
            secrets['twitter_access_token'],
            secrets['twitter_access_secret']
        )
        
        logger.info("All clients initialized successfully")
    
    def _get_all_secrets(self) -> Dict:
        """Retrieve all required secrets"""
        secret_names = [
            'google_sheets_credentials',
            'openai_api_key',
            'heygen_api_key',
            'youtube_credentials',
            'instagram_access_token',
            'instagram_account_id',
            'pinterest_access_token',
            'pinterest_board_id',
            'twitter_api_key',
            'twitter_api_secret',
            'twitter_access_token',
            'twitter_access_secret'
        ]
        
        secrets = {}
        for name in secret_names:
            try:
                secrets[name] = self.secret_manager.get_secret(name)
            except Exception as e:
                logger.error(f"Failed to get secret {name}: {e}")
                raise
        
        return secrets
    
    def process_product(self, product_data: Dict, row_index: int):
        """Process a single product: generate script, create video, post to platforms"""
        try:
            product_name = product_data.get('name', product_data.get('Name', f'Product {row_index}'))
            logger.info(f"Processing product: {product_name}")
            
            # Step 1: Generate script
            logger.info("Generating script...")
            script = self.script_generator.generate_script(product_data)
            
            # Step 2: Create video with HeyGen
            logger.info("Creating video with HeyGen...")
            video_result = self.heygen_client.create_video(script, product_data)
            
            # Step 3: Download video
            video_filename = f"video_{row_index}_{int(time.time())}.mp4"
            video_path = f"/home/claude/videos/{video_filename}"
            os.makedirs("/home/claude/videos", exist_ok=True)
            
            self.heygen_client.download_video(video_result['video_url'], video_path)
            
            # Step 4: Prepare content
            title = f"{product_name} - {product_data.get('tagline', 'Amazing Product')}"
            description = product_data.get('description', product_data.get('Description', ''))
            tags = product_data.get('tags', '').split(',') if product_data.get('tags') else [product_name]
            
            # Step 5: Upload to all platforms
            results = {}
            
            # YouTube
            try:
                logger.info("Uploading to YouTube...")
                results['youtube'] = self.youtube_uploader.upload(
                    video_path, title, description, tags
                )
            except Exception as e:
                logger.error(f"YouTube upload failed: {e}")
                results['youtube'] = f"Failed: {str(e)}"
            
            # Instagram (needs publicly accessible URL)
            try:
                logger.info("Uploading to Instagram...")
                results['instagram'] = self.instagram_uploader.upload(
                    video_result['video_url'], description[:2200]
                )
            except Exception as e:
                logger.error(f"Instagram upload failed: {e}")
                results['instagram'] = f"Failed: {str(e)}"
            
            # Pinterest
            try:
                logger.info("Uploading to Pinterest...")
                pinterest_board_id = self.secret_manager.get_secret('pinterest_board_id')
                results['pinterest'] = self.pinterest_uploader.upload(
                    video_result['video_url'], title, description, pinterest_board_id
                )
            except Exception as e:
                logger.error(f"Pinterest upload failed: {e}")
                results['pinterest'] = f"Failed: {str(e)}"
            
            # Twitter
            try:
                logger.info("Uploading to Twitter...")
                caption = f"{title}\n\n{description[:200]}..."
                results['twitter'] = self.twitter_uploader.upload(video_path, caption)
            except Exception as e:
                logger.error(f"Twitter upload failed: {e}")
                results['twitter'] = f"Failed: {str(e)}"
            
            logger.info(f"Product {product_name} processed successfully!")
            logger.info(f"Results: {json.dumps(results, indent=2)}")
            
            # Update state
            self.sheets_client.mark_row_processed(row_index, datetime.now().isoformat())
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing product {row_index}: {e}")
            raise
    
    def run(self, process_count: int = 1):
        """Run the automation for specified number of products"""
        try:
            # Get all products
            products = self.sheets_client.get_all_products()
            total_products = len(products)
            
            if total_products == 0:
                logger.warning("No products found in sheet")
                return
            
            # Get current position
            current_row = self.state_manager.get_current_row()
            
            logger.info(f"Starting from row {current_row + 1} of {total_products}")
            
            # Process products
            for i in range(process_count):
                # Get next product (loop back to start if at end)
                row_index = (current_row + i) % total_products
                product = products[row_index]
                
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing product {row_index + 1}/{total_products}")
                logger.info(f"{'='*60}\n")
                
                # Process the product
                self.process_product(product, row_index)
                
                # Update state
                next_row = (row_index + 1) % total_products
                self.state_manager.set_current_row(next_row)
                
                # Add delay between products
                if i < process_count - 1:
                    logger.info("Waiting before processing next product...")
                    time.sleep(60)  # 1 minute delay
            
            logger.info("\n" + "="*60)
            logger.info("Automation completed successfully!")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            raise


def main():
    """Main entry point"""
    # Configuration
    config = {
        'gcp_project_id': os.getenv('GCP_PROJECT_ID', 'your-project-id'),
        'spreadsheet_id': '1LU2ahpzMqLB5FLYqiyDbXOfjTxbdp8U8'  # From your URL
    }
    
    # Create and run automation
    automation = VideoAutomation(config)
    
    # Process one product at a time (adjust as needed)
    automation.run(process_count=1)


if __name__ == "__main__":
    main()
