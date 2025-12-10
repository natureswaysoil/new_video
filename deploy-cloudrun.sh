#!/bin/bash
# Deployment script for Google Cloud Run

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Video Automation - Cloud Run Deployment${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if PROJECT_ID is set
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID environment variable is not set${NC}"
    echo "Please set it with: export GCP_PROJECT_ID=your-project-id"
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

# Set the project
echo -e "${YELLOW}Setting GCP project...${NC}"
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
echo ""
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    cloudscheduler.googleapis.com \
    containerregistry.googleapis.com

# Build the container image
echo ""
echo -e "${YELLOW}Building container image with Cloud Build...${NC}"
gcloud builds submit --config cloudbuild.yaml .

# Deploy to Cloud Run
echo ""
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy video-automation \
    --image gcr.io/$GCP_PROJECT_ID/video-automation:latest \
    --region us-central1 \
    --platform managed \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --no-allow-unauthenticated \
    --set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID,SCHEDULE_TYPE=daily,SCHEDULE_TIME=09:00,PRODUCTS_PER_RUN=1,RUN_ON_START=false

# Get the service URL
SERVICE_URL=$(gcloud run services describe video-automation --region us-central1 --format 'value(status.url)')

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "Service URL: ${YELLOW}$SERVICE_URL${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Set up Cloud Scheduler to trigger the service periodically"
echo "2. Ensure the service account has access to Secret Manager"
echo "3. Test the deployment with: curl -X POST $SERVICE_URL"
echo ""
echo -e "To set up Cloud Scheduler, run: ${YELLOW}./setup-scheduler.sh${NC}"
