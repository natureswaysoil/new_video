#!/bin/bash
# Setup Cloud Scheduler to trigger video automation

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Cloud Scheduler Setup${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if PROJECT_ID is set
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID environment variable is not set${NC}"
    echo "Please set it with: export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

# Get the Cloud Run service URL
SERVICE_URL=$(gcloud run services describe video-automation --region us-central1 --format 'value(status.url)' 2>/dev/null)

if [ -z "$SERVICE_URL" ]; then
    echo -e "${RED}Error: Cloud Run service 'video-automation' not found${NC}"
    echo "Please deploy the service first with: ./deploy-cloudrun.sh"
    exit 1
fi

echo -e "${YELLOW}Cloud Run Service URL: $SERVICE_URL${NC}"
echo ""

# Get or create service account for scheduler
SA_EMAIL="video-automation-scheduler@$GCP_PROJECT_ID.iam.gserviceaccount.com"

echo -e "${YELLOW}Setting up service account for Cloud Scheduler...${NC}"
CREATE_SA_OUTPUT=$(gcloud iam service-accounts create video-automation-scheduler \
    --display-name="Video Automation Scheduler" \
    --project=$GCP_PROJECT_ID 2>&1) || {
    if [[ "$CREATE_SA_OUTPUT" == *"already exists"* ]]; then
        echo "Service account already exists"
    else
        echo -e "${RED}Error creating service account:${NC}"
        echo "$CREATE_SA_OUTPUT"
        exit 1
    fi
}

# Grant permission to invoke Cloud Run
echo -e "${YELLOW}Granting Cloud Run Invoker permission...${NC}"
gcloud run services add-iam-policy-binding video-automation \
    --region=us-central1 \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.invoker"

# Create Cloud Scheduler job
echo ""
echo -e "${YELLOW}Creating Cloud Scheduler job...${NC}"
CREATE_JOB_OUTPUT=$(gcloud scheduler jobs create http video-automation-daily \
    --location=us-central1 \
    --schedule="0 9 * * *" \
    --time-zone="America/New_York" \
    --uri="$SERVICE_URL" \
    --http-method=POST \
    --oidc-service-account-email="$SA_EMAIL" \
    --oidc-token-audience="$SERVICE_URL" \
    --headers="Content-Type=application/json" \
    --message-body='{"run_type": "scheduled"}' \
    --max-retry-attempts=3 \
    --max-retry-duration=600s \
    --min-backoff=60s \
    --max-backoff=3600s 2>&1) || {
        if [[ "$CREATE_JOB_OUTPUT" == *"already exists"* ]]; then
            echo -e "${YELLOW}Job already exists, updating...${NC}"
            gcloud scheduler jobs update http video-automation-daily \
                --location=us-central1 \
                --schedule="0 9 * * *" \
                --time-zone="America/New_York" \
                --uri="$SERVICE_URL"
        else
            echo -e "${RED}Error creating scheduler job:${NC}"
            echo "$CREATE_JOB_OUTPUT"
            exit 1
        fi
    }

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Cloud Scheduler Setup Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${YELLOW}Scheduled job: video-automation-daily${NC}"
echo "Schedule: Every day at 9:00 AM (America/New_York)"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "- List jobs: gcloud scheduler jobs list --location=us-central1"
echo "- Test job: gcloud scheduler jobs run video-automation-daily --location=us-central1"
echo "- View logs: gcloud scheduler jobs describe video-automation-daily --location=us-central1"
echo "- Delete job: gcloud scheduler jobs delete video-automation-daily --location=us-central1"
echo ""
echo -e "${YELLOW}To change the schedule, edit and run this script again${NC}"
