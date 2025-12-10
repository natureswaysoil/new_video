#!/bin/bash
# Complete Google Cloud Platform deployment script
# This script performs a full deployment of the video automation system

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Video Automation - Complete GCP Deployment${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if PROJECT_ID is set
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID environment variable is not set${NC}"
    echo ""
    echo "Please set it with: export GCP_PROJECT_ID=your-project-id"
    echo "Then run this script again."
    echo ""
    echo "To find your project ID, visit: https://console.cloud.google.com"
    exit 1
fi

echo -e "${YELLOW}Project ID: $GCP_PROJECT_ID${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/install"
    exit 1
fi

echo -e "${GREEN}Found gcloud CLI${NC}"
echo ""

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}Not authenticated. Running gcloud auth login...${NC}"
    gcloud auth login
fi

echo -e "${GREEN}Authenticated${NC}"
echo ""

# Set the project
echo -e "${YELLOW}Setting GCP project...${NC}"
gcloud config set project $GCP_PROJECT_ID
echo ""

# Confirm with user
echo -e "${YELLOW}This script will:${NC}"
echo "1. Enable required GCP APIs"
echo "2. Create service account and grant permissions"
echo "3. Build container image with Cloud Build"
echo "4. Deploy to Cloud Run"
echo "5. Set up Cloud Scheduler for automation"
echo ""
echo -e "${YELLOW}Estimated time: 5-10 minutes${NC}"
echo ""
read -p "Continue? (y/n) " -r response
echo ""
if [[ ! $response =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Step 1: Enabling APIs${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    cloudscheduler.googleapis.com \
    containerregistry.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com

echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Step 2: Service Account Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

SA_NAME="video-automation-sa"
SA_EMAIL="$SA_NAME@$GCP_PROJECT_ID.iam.gserviceaccount.com"

# Create service account
echo -e "${YELLOW}Creating service account...${NC}"
CREATE_SA_OUTPUT=$(gcloud iam service-accounts create $SA_NAME \
    --display-name="Video Automation Service Account" \
    --project=$GCP_PROJECT_ID 2>&1) || {
    if echo "$CREATE_SA_OUTPUT" | grep -q "already exists"; then
        echo "Service account already exists"
    else
        echo -e "${RED}Error creating service account:${NC}"
        echo "$CREATE_SA_OUTPUT"
        exit 1
    fi
}

# Grant permissions
echo -e "${YELLOW}Granting permissions...${NC}"
for ROLE in roles/secretmanager.secretAccessor roles/logging.logWriter roles/monitoring.metricWriter; do
    gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$ROLE" --quiet
done

echo -e "${GREEN}✓ Service account configured${NC}"
echo ""

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Step 3: Building Container Image${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

echo -e "${YELLOW}Building with Cloud Build (this may take 2-3 minutes)...${NC}"
gcloud builds submit --config cloudbuild.yaml .

echo -e "${GREEN}✓ Container image built${NC}"
echo ""

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Step 4: Deploying to Cloud Run${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

echo -e "${YELLOW}Deploying service...${NC}"
gcloud run deploy video-automation \
    --image gcr.io/$GCP_PROJECT_ID/video-automation:latest \
    --region us-central1 \
    --platform managed \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --no-allow-unauthenticated \
    --service-account $SA_EMAIL \
    --set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID,SCHEDULE_TYPE=daily,SCHEDULE_TIME=09:00,PRODUCTS_PER_RUN=1,RUN_ON_START=false \
    --quiet

SERVICE_URL=$(gcloud run services describe video-automation --region us-central1 --format 'value(status.url)')

echo -e "${GREEN}✓ Deployed to Cloud Run${NC}"
echo -e "   URL: ${YELLOW}$SERVICE_URL${NC}"
echo ""

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Step 5: Setting up Cloud Scheduler${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Create scheduler service account
SCHEDULER_SA_EMAIL="video-automation-scheduler@$GCP_PROJECT_ID.iam.gserviceaccount.com"
echo -e "${YELLOW}Creating scheduler service account...${NC}"
CREATE_SCHEDULER_SA_OUTPUT=$(gcloud iam service-accounts create video-automation-scheduler \
    --display-name="Video Automation Scheduler" \
    --project=$GCP_PROJECT_ID 2>&1) || {
    if echo "$CREATE_SCHEDULER_SA_OUTPUT" | grep -q "already exists"; then
        echo "Scheduler service account already exists"
    else
        echo -e "${RED}Error creating scheduler service account:${NC}"
        echo "$CREATE_SCHEDULER_SA_OUTPUT"
        exit 1
    fi
}

# Grant Cloud Run invoker permission
echo -e "${YELLOW}Granting Cloud Run Invoker permission...${NC}"
gcloud run services add-iam-policy-binding video-automation \
    --region=us-central1 \
    --member="serviceAccount:$SCHEDULER_SA_EMAIL" \
    --role="roles/run.invoker" \
    --quiet

# Create Cloud Scheduler job
echo -e "${YELLOW}Creating Cloud Scheduler job...${NC}"
CREATE_JOB_OUTPUT=$(gcloud scheduler jobs create http video-automation-daily \
    --location=us-central1 \
    --schedule="0 9 * * *" \
    --time-zone="America/New_York" \
    --uri="$SERVICE_URL" \
    --http-method=POST \
    --oidc-service-account-email="$SCHEDULER_SA_EMAIL" \
    --oidc-token-audience="$SERVICE_URL" \
    --headers="Content-Type=application/json" \
    --message-body='{"run_type": "scheduled"}' \
    --max-retry-attempts=3 \
    --max-retry-duration=600s \
    --min-backoff=60s \
    --max-backoff=3600s \
    --quiet 2>&1) || {
        if echo "$CREATE_JOB_OUTPUT" | grep -q "already exists"; then
            echo -e "${YELLOW}Job already exists, updating...${NC}"
            gcloud scheduler jobs update http video-automation-daily \
                --location=us-central1 \
                --schedule="0 9 * * *" \
                --time-zone="America/New_York" \
                --uri="$SERVICE_URL" \
                --quiet
        else
            echo -e "${RED}Error creating scheduler job:${NC}"
            echo "$CREATE_JOB_OUTPUT"
            exit 1
        fi
    }

echo -e "${GREEN}✓ Cloud Scheduler configured${NC}"
echo ""

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🎉 Deployment Complete!${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

echo -e "${GREEN}✓ All components deployed successfully${NC}"
echo ""
echo -e "${YELLOW}Service Details:${NC}"
echo "  - Cloud Run URL: $SERVICE_URL"
echo "  - Region: us-central1"
echo "  - Service Account: $SA_EMAIL"
echo "  - Schedule: Daily at 9:00 AM (America/New_York)"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. ${BLUE}Ensure all secrets are created in Secret Manager${NC}"
echo "   Visit: https://console.cloud.google.com/security/secret-manager?project=$GCP_PROJECT_ID"
echo ""
echo "   Required secrets:"
echo "   - google_sheets_credentials"
echo "   - openai_api_key"
echo "   - heygen_api_key"
echo "   - youtube_credentials"
echo "   - instagram_access_token"
echo "   - instagram_account_id"
echo "   - pinterest_access_token"
echo "   - pinterest_board_id"
echo "   - twitter_api_key"
echo "   - twitter_api_secret"
echo "   - twitter_access_token"
echo "   - twitter_access_secret"
echo ""

echo "2. ${BLUE}Test the deployment${NC}"
echo "   Run: gcloud scheduler jobs run video-automation-daily --location=us-central1"
echo ""

echo "3. ${BLUE}View logs${NC}"
echo "   Run: gcloud run services logs tail video-automation --region=us-central1"
echo "   Or visit: https://console.cloud.google.com/run/detail/us-central1/video-automation/logs?project=$GCP_PROJECT_ID"
echo ""

echo "4. ${BLUE}Monitor costs${NC}"
echo "   Visit: https://console.cloud.google.com/billing?project=$GCP_PROJECT_ID"
echo ""

echo -e "${GREEN}For more information, see DEPLOY_TO_GCP.md${NC}"
echo ""
