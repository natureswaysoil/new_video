# Quick Start: Deploy to Google Cloud in 5 Minutes

Get your video automation system running on Google Cloud Platform in just a few steps.

## Prerequisites

- Google Cloud account with billing enabled
- Google Cloud SDK (gcloud) installed
- All API credentials ready (OpenAI, HeyGen, social media)

## Step-by-Step Deployment

### 1. Set Your Project ID

```bash
export GCP_PROJECT_ID=your-project-id
```

To find your project ID:
- Go to https://console.cloud.google.com
- Select or create a project
- Copy the Project ID

### 2. Run the Deployment Script

```bash
./deploy-gcp-all.sh
```

This single script will:
- ✅ Enable all required APIs
- ✅ Create service accounts with proper permissions
- ✅ Build your container image
- ✅ Deploy to Cloud Run
- ✅ Set up Cloud Scheduler for daily runs

**Time**: 5-10 minutes

### 3. Add Your Secrets

Create all required secrets in Google Secret Manager:

```bash
# Navigate to Secret Manager
https://console.cloud.google.com/security/secret-manager?project=YOUR_PROJECT_ID

# Or use gcloud commands:
gcloud secrets create openai_api_key --data-file=- <<< "your-api-key"
gcloud secrets create heygen_api_key --data-file=- <<< "your-api-key"
# ... add all other secrets
```

Required secrets:
- `google_sheets_credentials`
- `openai_api_key`
- `heygen_api_key`
- `youtube_credentials`
- `instagram_access_token`
- `instagram_account_id`
- `pinterest_access_token`
- `pinterest_board_id`
- `twitter_api_key`
- `twitter_api_secret`
- `twitter_access_token`
- `twitter_access_secret`

### 4. Test the Deployment

```bash
# Trigger a test run
gcloud scheduler jobs run video-automation-daily --location=us-central1

# Watch the logs
gcloud run services logs tail video-automation --region=us-central1
```

## That's It! 🎉

Your video automation system is now running on Google Cloud and will execute daily at 9:00 AM EST.

## What Happens Next?

- **Daily at 9:00 AM**: Cloud Scheduler triggers your automation
- **Video Processing**: Reads from Google Sheets, generates video, posts to social media
- **Automatic Scaling**: Cloud Run scales to zero when not in use (no cost)
- **Logs & Monitoring**: View everything in Cloud Console

## Viewing Logs

**Option 1: Command Line**
```bash
gcloud run services logs read video-automation --region=us-central1 --limit=50
```

**Option 2: Cloud Console**
```
https://console.cloud.google.com/run/detail/us-central1/video-automation/logs
```

## Cost

**Expected monthly cost**: $12-24/month
- Cloud Run: ~$1-2
- Secret Manager: ~$1
- Container Registry: ~$1
- Cloud Scheduler: $0.10
- OpenAI + HeyGen: ~$10-20

## Customization

### Change Schedule

Edit Cloud Scheduler job:
```bash
# Run every 4 hours instead of daily
gcloud scheduler jobs update http video-automation-daily \
    --location=us-central1 \
    --schedule="0 */4 * * *"
```

### Process More Products

```bash
# Process 3 products per run instead of 1
gcloud run services update video-automation \
    --region=us-central1 \
    --set-env-vars PRODUCTS_PER_RUN=3
```

### Adjust Resources

```bash
# Increase memory and CPU for faster processing
gcloud run services update video-automation \
    --region=us-central1 \
    --memory 4Gi \
    --cpu 4
```

## Troubleshooting

### Check Deployment Status
```bash
gcloud run services describe video-automation --region=us-central1
```

### View Recent Errors
```bash
gcloud run services logs read video-automation \
    --region=us-central1 \
    --limit=50 \
    --format="table(timestamp, severity, textPayload)"
```

### Test Manually
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe video-automation --region=us-central1 --format='value(status.url)')

# Trigger manually (requires authentication)
gcloud run services proxy video-automation --region=us-central1
```

## Common Issues

**"Permission denied"**
→ Run: `./setup-permissions.sh`

**"Secrets not found"**
→ Create all required secrets in Secret Manager

**"Timeout"**
→ Increase timeout: `gcloud run services update video-automation --region=us-central1 --timeout=3600`

**"Out of memory"**
→ Increase memory: `gcloud run services update video-automation --region=us-central1 --memory=4Gi`

## Next Steps

1. Monitor first few runs to ensure everything works
2. Set up billing alerts in Cloud Console
3. Customize video settings in `video_automation.py`
4. Add more scheduling times if needed

## Full Documentation

For complete details, see:
- **DEPLOY_TO_GCP.md** - Comprehensive deployment guide
- **README.md** - Application overview and setup
- **CUSTOMIZATION.md** - Customization options

## Support

Need help?
1. Check logs first: `gcloud run services logs tail video-automation --region=us-central1`
2. Review DEPLOY_TO_GCP.md troubleshooting section
3. Test each component separately

---

**Deployment time**: 5-10 minutes  
**Monthly cost**: $12-24  
**Maintenance**: Minimal (automated)
