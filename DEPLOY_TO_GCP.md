# Deploy Video Automation to Google Cloud Platform

Complete guide to deploying the video automation system to Google Cloud Platform (GCP). This system can run continuously on GCP with automated scheduling.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Deployment Options](#deployment-options)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Detailed Setup](#detailed-setup)
6. [Configuration](#configuration)
7. [Monitoring & Logs](#monitoring--logs)
8. [Troubleshooting](#troubleshooting)
9. [Cost Estimation](#cost-estimation)

---

## Overview

This deployment guide covers three GCP deployment options:

1. **Cloud Run** (Recommended) - Serverless, scales to zero, triggered by Cloud Scheduler
2. **App Engine** - Managed platform, always-on service
3. **Compute Engine** - Full VM control (manual setup required)

### Why Cloud Run?

- ✅ **Cost-effective**: Only pay when running
- ✅ **Serverless**: No infrastructure management
- ✅ **Scalable**: Auto-scales based on demand
- ✅ **Integrated**: Works with Cloud Scheduler for automation
- ✅ **Simple**: Deploy with a single command

---

## Deployment Options

### Option 1: Cloud Run (Recommended)

**Best for**: Scheduled automation, cost efficiency

```bash
./deploy-cloudrun.sh
./setup-scheduler.sh
```

**Pros**:
- Scales to zero when not in use
- Pay only for execution time
- Automatic HTTPS
- Simple deployment

**Cons**:
- Request timeout limit (60 minutes max)
- Cold start delay (1-3 seconds)

### Option 2: App Engine

**Best for**: Always-on services, simpler management

```bash
gcloud app deploy app.yaml
```

**Pros**:
- Always available
- Automatic scaling
- Built-in traffic splitting

**Cons**:
- Minimum instance costs
- Less flexible than Cloud Run
- Longer deployment time

### Option 3: Compute Engine

**Best for**: Full control, custom requirements

Requires manual VM setup, Docker installation, and configuration.

---

## Prerequisites

### 1. Google Cloud Project

Create a new GCP project or use an existing one:

```bash
# Create a new project
gcloud projects create your-project-id --name="Video Automation"

# Set as default project
gcloud config set project your-project-id

# Enable billing
# Go to: https://console.cloud.google.com/billing/linkedaccount?project=your-project-id
```

### 2. Install Google Cloud SDK

**macOS**:
```bash
brew install google-cloud-sdk
```

**Linux**:
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Windows**:
Download from: https://cloud.google.com/sdk/docs/install

### 3. Authenticate

```bash
# Login to GCP
gcloud auth login

# Set application default credentials
gcloud auth application-default login
```

### 4. Set Environment Variables

```bash
export GCP_PROJECT_ID=your-project-id
```

Add to your `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export GCP_PROJECT_ID=your-project-id' >> ~/.bashrc
source ~/.bashrc
```

---

## Quick Start

For the fastest deployment using Cloud Run:

```bash
# 1. Set your project ID
export GCP_PROJECT_ID=your-project-id

# 2. Set up service account and permissions
./setup-permissions.sh

# 3. Deploy to Cloud Run
./deploy-cloudrun.sh

# 4. Set up Cloud Scheduler for automation
./setup-scheduler.sh
```

That's it! Your system is now deployed and will run automatically.

---

## Detailed Setup

### Step 1: Enable Required APIs

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    cloudscheduler.googleapis.com \
    containerregistry.googleapis.com \
    compute.googleapis.com
```

### Step 2: Create Service Account

```bash
# Run the setup script
./setup-permissions.sh

# Or manually:
gcloud iam service-accounts create video-automation-sa \
    --display-name="Video Automation Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:video-automation-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:video-automation-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"
```

### Step 3: Create Secrets in Secret Manager

All API credentials must be stored in Google Secret Manager:

```bash
# Google Sheets credentials (service account JSON)
gcloud secrets create google_sheets_credentials \
    --data-file=path/to/service-account.json \
    --replication-policy="automatic"

# OpenAI API key
echo -n "sk-your-openai-api-key" | \
    gcloud secrets create openai_api_key --data-file=-

# HeyGen API key
echo -n "your-heygen-api-key" | \
    gcloud secrets create heygen_api_key --data-file=-

# YouTube credentials (OAuth2 JSON)
gcloud secrets create youtube_credentials \
    --data-file=path/to/youtube-oauth.json

# Instagram access token
echo -n "your-instagram-access-token" | \
    gcloud secrets create instagram_access_token --data-file=-

# Instagram account ID
echo -n "your-instagram-account-id" | \
    gcloud secrets create instagram_account_id --data-file=-

# Pinterest access token
echo -n "your-pinterest-access-token" | \
    gcloud secrets create pinterest_access_token --data-file=-

# Pinterest board ID
echo -n "your-pinterest-board-id" | \
    gcloud secrets create pinterest_board_id --data-file=-

# Twitter API keys
echo -n "your-twitter-api-key" | \
    gcloud secrets create twitter_api_key --data-file=-

echo -n "your-twitter-api-secret" | \
    gcloud secrets create twitter_api_secret --data-file=-

echo -n "your-twitter-access-token" | \
    gcloud secrets create twitter_access_token --data-file=-

echo -n "your-twitter-access-secret" | \
    gcloud secrets create twitter_access_secret --data-file=-
```

### Step 4: Build and Deploy to Cloud Run

```bash
# Option A: Use the deployment script
./deploy-cloudrun.sh

# Option B: Manual deployment
# Build the container
gcloud builds submit --config cloudbuild.yaml .

# Deploy to Cloud Run
gcloud run deploy video-automation \
    --image gcr.io/$GCP_PROJECT_ID/video-automation:latest \
    --region us-central1 \
    --platform managed \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --no-allow-unauthenticated \
    --service-account video-automation-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID,SCHEDULE_TYPE=daily,PRODUCTS_PER_RUN=1
```

### Step 5: Set Up Cloud Scheduler

```bash
# Option A: Use the setup script
./setup-scheduler.sh

# Option B: Manual setup
# Get the Cloud Run service URL
SERVICE_URL=$(gcloud run services describe video-automation \
    --region us-central1 --format 'value(status.url)')

# Create scheduler job
gcloud scheduler jobs create http video-automation-daily \
    --location=us-central1 \
    --schedule="0 9 * * *" \
    --time-zone="America/New_York" \
    --uri="$SERVICE_URL" \
    --http-method=POST \
    --oidc-service-account-email="video-automation-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --oidc-token-audience="$SERVICE_URL"
```

### Step 6: Test the Deployment

```bash
# Test the Cloud Scheduler job
gcloud scheduler jobs run video-automation-daily --location=us-central1

# View Cloud Run logs
gcloud run services logs read video-automation --region us-central1

# Check job status
gcloud scheduler jobs describe video-automation-daily --location=us-central1
```

---

## Configuration

### Environment Variables

Modify Cloud Run environment variables:

```bash
gcloud run services update video-automation \
    --region us-central1 \
    --set-env-vars SCHEDULE_TYPE=daily,SCHEDULE_TIME=09:00,PRODUCTS_PER_RUN=1
```

Available variables:
- `GCP_PROJECT_ID`: Your GCP project ID (required)
- `SCHEDULE_TYPE`: `daily`, `hourly`, `every_n_hours`, `custom`
- `SCHEDULE_TIME`: Time for daily runs (e.g., `09:00`)
- `SCHEDULE_INTERVAL_HOURS`: Interval for `every_n_hours`
- `PRODUCTS_PER_RUN`: Number of products to process per run
- `RUN_ON_START`: `true` or `false`
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`

### Adjust Resources

```bash
# Increase memory and CPU
gcloud run services update video-automation \
    --region us-central1 \
    --memory 4Gi \
    --cpu 4

# Adjust timeout (max 3600 seconds)
gcloud run services update video-automation \
    --region us-central1 \
    --timeout 3600
```

### Change Schedule

Edit the Cloud Scheduler job:

```bash
# Update schedule to run every 4 hours
gcloud scheduler jobs update http video-automation-daily \
    --location=us-central1 \
    --schedule="0 */4 * * *"

# Update to run twice daily (9 AM and 5 PM)
# Create additional jobs or modify the schedule
```

Common cron schedules:
- `0 9 * * *` - Daily at 9:00 AM
- `0 */4 * * *` - Every 4 hours
- `0 9,17 * * *` - Daily at 9 AM and 5 PM
- `0 9 * * 1-5` - Weekdays at 9 AM

### Multiple Schedules

Create additional scheduler jobs for different times:

```bash
# Morning run
gcloud scheduler jobs create http video-automation-morning \
    --location=us-central1 \
    --schedule="0 9 * * *" \
    --time-zone="America/New_York" \
    --uri="$SERVICE_URL" \
    --http-method=POST \
    --oidc-service-account-email="video-automation-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com"

# Afternoon run
gcloud scheduler jobs create http video-automation-afternoon \
    --location=us-central1 \
    --schedule="0 14 * * *" \
    --time-zone="America/New_York" \
    --uri="$SERVICE_URL" \
    --http-method=POST \
    --oidc-service-account-email="video-automation-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com"
```

---

## Monitoring & Logs

### View Logs

**Cloud Run logs**:
```bash
# Recent logs
gcloud run services logs read video-automation --region us-central1

# Follow logs in real-time
gcloud run services logs tail video-automation --region us-central1

# Logs from specific time
gcloud run services logs read video-automation \
    --region us-central1 \
    --since="2024-01-01T00:00:00Z"
```

**Cloud Scheduler logs**:
```bash
gcloud scheduler jobs describe video-automation-daily --location=us-central1
```

**Using Cloud Console**:
- Go to: https://console.cloud.google.com/run
- Select your service
- Click "LOGS" tab

### Cloud Logging

Advanced log queries:

```bash
# View logs in Cloud Logging
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=video-automation" \
    --limit 50 \
    --format json

# Filter for errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=video-automation AND severity>=ERROR" \
    --limit 50
```

### Monitoring Metrics

View metrics in Cloud Console:
- Go to: https://console.cloud.google.com/run/detail/us-central1/video-automation/metrics
- Monitor: Request count, latency, memory usage, CPU usage

### Set Up Alerts

Create alert policies for failures:

```bash
# Create alert for Cloud Run errors (via Cloud Console recommended)
# Go to: https://console.cloud.google.com/monitoring/alerting
```

---

## Troubleshooting

### Common Issues

#### 1. Permission Denied Errors

**Problem**: Service can't access Secret Manager

**Solution**:
```bash
# Re-run permissions setup
./setup-permissions.sh

# Or manually grant Secret Manager access
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:video-automation-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

#### 2. Timeout Errors

**Problem**: Cloud Run times out before video generation completes

**Solution**:
```bash
# Increase timeout to maximum (1 hour)
gcloud run services update video-automation \
    --region us-central1 \
    --timeout 3600
```

#### 3. Out of Memory

**Problem**: Container runs out of memory

**Solution**:
```bash
# Increase memory allocation
gcloud run services update video-automation \
    --region us-central1 \
    --memory 4Gi
```

#### 4. Cold Start Issues

**Problem**: First request takes too long

**Solution**:
```bash
# Set minimum instances (increases cost)
gcloud run services update video-automation \
    --region us-central1 \
    --min-instances 1
```

#### 5. Scheduler Not Triggering

**Problem**: Cloud Scheduler job not running

**Solution**:
```bash
# Check job status
gcloud scheduler jobs describe video-automation-daily --location=us-central1

# Manually trigger to test
gcloud scheduler jobs run video-automation-daily --location=us-central1

# Check service account permissions
gcloud run services get-iam-policy video-automation --region=us-central1
```

#### 6. Build Failures

**Problem**: Cloud Build fails

**Solution**:
```bash
# Check build logs
gcloud builds list --limit=5

# View specific build
gcloud builds log BUILD_ID

# Ensure Dockerfile is correct
docker build -t test .
```

### Debug Mode

Enable detailed logging:

```bash
gcloud run services update video-automation \
    --region us-central1 \
    --set-env-vars LOG_LEVEL=DEBUG
```

### Access Container Locally

Test the container locally before deploying:

```bash
# Build locally
docker build -t video-automation .

# Run locally
docker run -it \
    -e GCP_PROJECT_ID=$GCP_PROJECT_ID \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
    -v $HOME/.config/gcloud/application_default_credentials.json:/app/credentials.json \
    video-automation
```

---

## Cost Estimation

### Cloud Run Costs

**Pricing** (as of 2024):
- CPU: $0.00002400 per vCPU-second
- Memory: $0.00000250 per GiB-second
- Requests: $0.40 per million requests

**Example calculation** (1 video per day, 7 minutes per video):
- CPU: 2 vCPU × 420 seconds × 30 days × $0.000024 = $0.60/month
- Memory: 2 GiB × 420 seconds × 30 days × $0.0000025 = $0.06/month
- Requests: 30 requests × $0.0000004 = $0.00/month

**Total Cloud Run cost**: ~$0.66/month

### Additional GCP Services

- **Cloud Build**: $0.003 per build-minute (first 120 minutes free/day)
- **Container Registry**: $0.026 per GB-month storage
- **Cloud Scheduler**: $0.10 per job per month
- **Secret Manager**: $0.06 per secret per month (first 6 free)

**Estimated monthly GCP costs**:
- Low usage (1 video/day): $5-10/month
- Medium usage (5 videos/day): $10-20/month
- High usage (20 videos/day): $20-40/month

### Third-Party API Costs

See main README.md for OpenAI, HeyGen, and social media API costs.

### Total Cost Example

**Daily automation (1 video/day)**:
- Google Cloud: ~$7/month
- OpenAI + HeyGen: ~$5-17/month
- **Total**: ~$12-24/month

### Cost Optimization Tips

1. **Scale to zero**: Keep min-instances at 0
2. **Reduce memory**: Use 1Gi if videos are small
3. **Batch processing**: Process multiple products per run
4. **Use Cloud Storage**: Store videos in GCS instead of downloading
5. **Optimize images**: Use Artifact Registry instead of Container Registry
6. **Monitor usage**: Set up billing alerts

```bash
# Set up billing budget alert
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="Video Automation Budget" \
    --budget-amount=50.00 \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90
```

---

## Maintenance

### Update Deployment

```bash
# Re-deploy with latest code
./deploy-cloudrun.sh

# Or manually
gcloud builds submit --config cloudbuild.yaml .
gcloud run deploy video-automation \
    --image gcr.io/$GCP_PROJECT_ID/video-automation:latest \
    --region us-central1
```

### Rollback

```bash
# List revisions
gcloud run revisions list --service=video-automation --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic video-automation \
    --region=us-central1 \
    --to-revisions=REVISION_NAME=100
```

### Delete Resources

```bash
# Delete Cloud Run service
gcloud run services delete video-automation --region=us-central1

# Delete Cloud Scheduler job
gcloud scheduler jobs delete video-automation-daily --location=us-central1

# Delete service account
gcloud iam service-accounts delete video-automation-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com

# Delete container images
gcloud container images list-tags gcr.io/$GCP_PROJECT_ID/video-automation
gcloud container images delete gcr.io/$GCP_PROJECT_ID/video-automation:TAG
```

---

## Advanced Configurations

### Use Cloud Storage for Videos

Modify the application to store videos in GCS:

```python
from google.cloud import storage

# Upload video to GCS instead of local storage
def upload_to_gcs(local_path, bucket_name, blob_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    return blob.public_url
```

Grant storage permissions:
```bash
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:video-automation-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

### Multi-Region Deployment

Deploy to multiple regions for reliability:

```bash
# Deploy to multiple regions
for REGION in us-central1 europe-west1 asia-east1; do
    gcloud run deploy video-automation \
        --image gcr.io/$GCP_PROJECT_ID/video-automation:latest \
        --region $REGION \
        --platform managed
done
```

### CI/CD with GitHub Actions

See `DEPLOY_TO_GITHUB.md` for GitHub Actions integration.

### VPC Connector

For private network access:

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create video-automation-connector \
    --network default \
    --region us-central1 \
    --range 10.8.0.0/28

# Deploy with VPC connector
gcloud run deploy video-automation \
    --region us-central1 \
    --vpc-connector video-automation-connector
```

---

## Support & Resources

### Documentation
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)

### Useful Commands Reference

```bash
# Service management
gcloud run services list
gcloud run services describe video-automation --region=us-central1
gcloud run services delete video-automation --region=us-central1

# Logs
gcloud run services logs read video-automation --region=us-central1
gcloud run services logs tail video-automation --region=us-central1

# Scheduler
gcloud scheduler jobs list --location=us-central1
gcloud scheduler jobs run video-automation-daily --location=us-central1
gcloud scheduler jobs pause video-automation-daily --location=us-central1
gcloud scheduler jobs resume video-automation-daily --location=us-central1

# Secrets
gcloud secrets list
gcloud secrets versions access latest --secret=openai_api_key
gcloud secrets delete SECRET_NAME

# Builds
gcloud builds list
gcloud builds log BUILD_ID
```

---

## Next Steps

After successful deployment:

1. ✅ Monitor the first few scheduled runs
2. ✅ Set up billing alerts
3. ✅ Configure log retention policies
4. ✅ Set up monitoring dashboards
5. ✅ Document any customizations
6. ✅ Create backup strategy for state files
7. ✅ Test failure scenarios and recovery

---

**Last Updated**: December 2024  
**Version**: 1.0.0
