# Video Automation System - Setup Guide

Complete automation system that reads products from Google Sheets, generates scripts with OpenAI, creates videos with HeyGen, and posts to YouTube, Instagram, Pinterest, and Twitter.

## 🎯 Features

- ✅ Reads product data from Google Sheets
- ✅ Generates engaging video scripts with OpenAI GPT-4
- ✅ Creates professional videos with HeyGen AI avatars
- ✅ Automatically posts to YouTube, Instagram, Pinterest, and Twitter
- ✅ Tracks progress and loops through products
- ✅ Secure credential management with Google Secret Manager
- ✅ Comprehensive logging and error handling
- ✅ Flexible scheduling options
- ✅ **NEW:** Amazon PPC Optimizer with corrected API configuration

## 📊 Amazon PPC Optimizer

This repository now includes an Amazon PPC optimizer module for fetching campaign reports from the Amazon Advertising API. The implementation includes the properly configured payload with the required `adProduct` field.

📖 **See [AMAZON_PPC_README.md](AMAZON_PPC_README.md)** for complete Amazon PPC optimizer documentation and deployment instructions.

## 📋 Prerequisites

1. **Google Cloud Project** with billing enabled
2. **API Accounts** for:
   - OpenAI
   - HeyGen
   - YouTube
   - Instagram (via Facebook)
   - Pinterest
   - Twitter

## 🚀 Quick Deployment Options

### Option 1: Deploy to Google Cloud Platform (Recommended)

**Deploy in 5 minutes with a single command!**

```bash
export GCP_PROJECT_ID=your-project-id
./deploy-gcp-all.sh
```

This will deploy the entire system to Google Cloud Run with Cloud Scheduler for automated daily runs.

📖 **See [QUICKSTART_GCP.md](QUICKSTART_GCP.md)** for the 5-minute deployment guide  
📖 **See [DEPLOY_TO_GCP.md](DEPLOY_TO_GCP.md)** for comprehensive GCP deployment documentation

### Option 2: Local Installation

For local development or self-hosted deployment:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up Google Cloud SDK (if not already installed)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Set environment variables
export GCP_PROJECT_ID="your-gcp-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## 🔐 Google Secret Manager Setup

### Create Secrets

All credentials are stored securely in Google Secret Manager. Create the following secrets:

```bash
# Google Sheets Credentials (Service Account JSON)
gcloud secrets create google_sheets_credentials \
    --data-file=service-account.json

# OpenAI API Key
echo -n "sk-your-openai-api-key" | \
    gcloud secrets create openai_api_key --data-file=-

# HeyGen API Key
echo -n "your-heygen-api-key" | \
    gcloud secrets create heygen_api_key --data-file=-

# YouTube Credentials (OAuth2 JSON)
gcloud secrets create youtube_credentials \
    --data-file=youtube-oauth.json

# Instagram Access Token
echo -n "your-instagram-access-token" | \
    gcloud secrets create instagram_access_token --data-file=-

# Instagram Account ID
echo -n "your-instagram-account-id" | \
    gcloud secrets create instagram_account_id --data-file=-

# Pinterest Access Token
echo -n "your-pinterest-access-token" | \
    gcloud secrets create pinterest_access_token --data-file=-

# Pinterest Board ID
echo -n "your-pinterest-board-id" | \
    gcloud secrets create pinterest_board_id --data-file=-

# Twitter API Keys
echo -n "your-twitter-api-key" | \
    gcloud secrets create twitter_api_key --data-file=-

echo -n "your-twitter-api-secret" | \
    gcloud secrets create twitter_api_secret --data-file=-

echo -n "your-twitter-access-token" | \
    gcloud secrets create twitter_access_token --data-file=-

echo -n "your-twitter-access-secret" | \
    gcloud secrets create twitter_access_secret --data-file=-
```

## 📊 Google Sheets Setup

### 1. Sheet Structure

Your Google Sheet should have these columns (column names are flexible):

| Name | Description | Price | Tags | Image URL | (Optional columns) |
|------|-------------|-------|------|-----------|-------------------|

Example:
```
Column A: Product Name
Column B: Product Description
Column C: Price
Column D: Tags (comma-separated)
Column E: Image URL
Column F: Last Processed (auto-updated)
```

### 2. Share Sheet with Service Account

1. Go to your Google Sheet
2. Click "Share"
3. Add the service account email (from your service-account.json)
4. Give "Editor" permissions

### 3. Get Sheet ID

From your sheet URL:
```
https://docs.google.com/spreadsheets/d/1LU2ahpzMqLB5FLYqiyDbXOfjTxbdp8U8/edit
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                    This is your Sheet ID
```

## 🔑 API Setup Instructions

### OpenAI API

1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy the key (starts with `sk-`)
4. Store in Google Secret Manager as shown above

### HeyGen API

1. Sign up at https://heygen.com
2. Go to API settings: https://app.heygen.com/settings/api
3. Generate API key
4. Store in Google Secret Manager

**Configure HeyGen Settings:**
- Choose your preferred avatar ID
- Choose your preferred voice ID
- Customize in the `create_video()` method

### YouTube API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable YouTube Data API v3
3. Create OAuth 2.0 credentials:
   - Application type: Desktop app
   - Download JSON file
4. Run OAuth flow once to get token:

```python
# First-time OAuth setup
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
credentials = flow.run_local_server(port=0)

# Save the credentials
import json
with open('youtube-oauth.json', 'w') as f:
    f.write(credentials.to_json())
```

### Instagram API (via Facebook)

1. Create a Facebook Developer account: https://developers.facebook.com
2. Create a new app (Business type)
3. Add Instagram Graph API product
4. Get your Instagram Business Account ID:
   ```
   GET https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_TOKEN
   ```
5. Get long-lived access token:
   ```
   GET https://graph.facebook.com/v18.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id=YOUR_APP_ID
     &client_secret=YOUR_APP_SECRET
     &fb_exchange_token=YOUR_SHORT_TOKEN
   ```

**Requirements:**
- Instagram Business or Creator account
- Connected to a Facebook Page
- Page access token with `instagram_basic`, `instagram_content_publish` permissions

### Pinterest API

1. Go to https://developers.pinterest.com/
2. Create a new app
3. Generate access token with scopes:
   - `boards:read`
   - `pins:read`
   - `pins:write`
4. Get your Board ID:
   ```
   GET https://api.pinterest.com/v5/boards
   Authorization: Bearer YOUR_ACCESS_TOKEN
   ```

### Twitter API

1. Apply for developer account: https://developer.twitter.com/
2. Create a new Project and App
3. Get API keys from "Keys and tokens" section:
   - API Key (Consumer Key)
   - API Key Secret (Consumer Secret)
   - Access Token
   - Access Token Secret
4. Enable read and write permissions
5. Enable OAuth 1.0a

## ⚙️ Configuration

### Environment Variables

Create a `.env` file:

```bash
# Required
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Scheduling (optional)
SCHEDULE_TYPE=daily          # Options: daily, hourly, every_n_hours, custom
SCHEDULE_TIME=09:00          # For daily schedule (24-hour format)
SCHEDULE_INTERVAL_HOURS=4    # For every_n_hours schedule
PRODUCTS_PER_RUN=1           # Number of products to process per run
RUN_ON_START=false           # Run immediately on startup
```

### Customize Video Settings

Edit `video_automation.py`:

```python
# In HeyGenClient.create_video() method:
payload = {
    "video_inputs": [{
        "character": {
            "type": "avatar",
            "avatar_id": "your_preferred_avatar_id",  # Change this
            "avatar_style": "normal"
        },
        "voice": {
            "type": "text",
            "input_text": script,
            "voice_id": "en-US-JennyNeural",  # Change this
            "speed": 1.0
        },
        "background": {
            "type": "color",
            "value": "#FFFFFF"  # Or use image URL
        }
    }],
    "dimension": {
        "width": 1920,  # Adjust resolution
        "height": 1080
    },
    "aspect_ratio": "16:9"  # Options: 16:9, 9:16, 1:1
}
```

## 🎬 Usage

### Cloud Deployment (Recommended)

After deploying to Google Cloud Platform:

```bash
# View logs
gcloud run services logs tail video-automation --region=us-central1

# Trigger manually
gcloud scheduler jobs run video-automation-daily --location=us-central1

# Update configuration
gcloud run services update video-automation --region=us-central1 \
    --set-env-vars PRODUCTS_PER_RUN=3
```

**The system runs automatically on schedule - no manual intervention needed!**

### Local Execution

#### Run Once

Process one product:
```bash
python video_automation.py
```

#### Run with Scheduler

Continuous automation with scheduling:
```bash
python scheduler.py
```

#### Run as Background Service

Using systemd (Linux):

1. Create service file `/etc/systemd/system/video-automation.service`:

```ini
[Unit]
Description=Video Automation Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/video-automation
Environment="GCP_PROJECT_ID=your-project-id"
Environment="GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json"
ExecStart=/usr/bin/python3 scheduler.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl enable video-automation
sudo systemctl start video-automation
sudo systemctl status video-automation
```

### Run with Docker

1. Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "scheduler.py"]
```

2. Build and run:
```bash
docker build -t video-automation .
docker run -d \
  -e GCP_PROJECT_ID=your-project-id \
  -v /path/to/service-account.json:/app/credentials.json \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
  video-automation
```

## 📝 Logs

Logs are written to:
- `video_automation.log` - Main automation logs
- `scheduler.log` - Scheduler logs

View live logs:
```bash
tail -f video_automation.log
```

## 🔄 State Management

The system tracks progress in `automation_state.json`:
```json
{
  "current_row": 5,
  "last_run": "2024-01-15T14:30:00"
}
```

To reset and start from beginning:
```bash
rm automation_state.json
```

## 🐛 Troubleshooting

### Common Issues

**1. Google Sheets Permission Denied**
- Ensure service account has Editor access to the sheet
- Verify `google_sheets_credentials` secret is valid

**2. YouTube Upload Fails**
- Check OAuth token is valid and not expired
- Verify quota limits haven't been reached
- Ensure video meets YouTube requirements (format, size)

**3. Instagram Upload Fails**
- Instagram video must be publicly accessible (use HeyGen URL)
- Check video meets requirements: 3-60 seconds, MP4 format
- Verify access token has required permissions

**4. HeyGen Video Takes Too Long**
- Videos can take 2-10 minutes to generate
- Timeout is set to 10 minutes
- Check HeyGen account credit balance

**5. Secret Manager Access Denied**
- Ensure service account has `secretmanager.secretAccessor` role
- Verify project ID is correct

### Debug Mode

Add to the top of `video_automation.py`:
```python
logging.getLogger().setLevel(logging.DEBUG)
```

## 📈 Monitoring

### Check Status

```bash
# View recent logs
tail -n 50 video_automation.log

# Check current state
cat automation_state.json

# View scheduler status (if using systemd)
sudo systemctl status video-automation
```

### Metrics to Track

- Products processed per day
- Success rate per platform
- Video generation time
- Upload failures

## 🔒 Security Best Practices

1. **Never commit credentials** to version control
2. **Use Secret Manager** for all API keys
3. **Restrict service account permissions** to minimum required
4. **Rotate tokens** regularly
5. **Monitor API usage** for unusual activity
6. **Enable 2FA** on all accounts
7. **Review access logs** periodically

## 💰 Cost Considerations

Estimated costs per video:
- OpenAI GPT-4: ~$0.01-0.05 per script
- HeyGen: $0.15-0.50 per video (varies by plan)
- YouTube: Free
- Instagram: Free
- Pinterest: Free
- Twitter: Free
- Google Cloud (Secret Manager, Storage): ~$0.01

**Monthly estimate for 100 videos**: $16-55

## 🎨 Customization Ideas

1. **Custom Scripts per Platform**
   - Generate different scripts for each platform
   - Adjust length and style based on platform

2. **A/B Testing**
   - Create multiple versions
   - Track performance

3. **Thumbnails**
   - Generate custom thumbnails
   - Extract frames from video

4. **Analytics**
   - Track views, engagement
   - Store in database

5. **Webhooks**
   - Get notified on completion
   - Trigger follow-up actions

## 📞 Support

For issues or questions:
1. Check logs first
2. Review API documentation
3. Test each component separately
4. Verify credentials and permissions

## 📜 License

This project is provided as-is for personal or commercial use.

## 🙏 Credits

- OpenAI for GPT-4 API
- HeyGen for video generation
- Google Cloud Platform for infrastructure
- Social media platforms for APIs
