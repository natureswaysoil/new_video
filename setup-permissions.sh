#!/bin/bash
# Setup service account and permissions for video automation

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Service Account & Permissions Setup${NC}"
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

SA_NAME="video-automation-sa"
SA_EMAIL="$SA_NAME@$GCP_PROJECT_ID.iam.gserviceaccount.com"

# Create service account
echo -e "${YELLOW}Creating service account...${NC}"
gcloud iam service-accounts create $SA_NAME \
    --display-name="Video Automation Service Account" \
    --project=$GCP_PROJECT_ID 2>/dev/null || echo "Service account already exists"

# Grant Secret Manager access
echo ""
echo -e "${YELLOW}Granting Secret Manager Secret Accessor role...${NC}"
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

# Grant Cloud Run service agent role
echo -e "${YELLOW}Granting Cloud Run Service Agent role...${NC}"
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.serviceAgent"

# Grant logging permissions
echo -e "${YELLOW}Granting Logging Write role...${NC}"
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/logging.logWriter"

# Grant monitoring permissions
echo -e "${YELLOW}Granting Monitoring Metric Writer role...${NC}"
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/monitoring.metricWriter"

# Optional: Grant storage permissions if saving videos to GCS
echo ""
echo -e "${YELLOW}Do you want to grant Cloud Storage permissions? (y/n)${NC}"
read -r storage_response
if [[ "$storage_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${YELLOW}Granting Storage Object Admin role...${NC}"
    gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/storage.objectAdmin"
fi

# Download service account key (optional)
echo ""
echo -e "${YELLOW}Do you want to download the service account key? (y/n)${NC}"
echo "(This is only needed for local development)"
read -r key_response
if [[ "$key_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    KEY_FILE="$SA_NAME-key.json"
    echo -e "${YELLOW}Downloading service account key to $KEY_FILE...${NC}"
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SA_EMAIL \
        --project=$GCP_PROJECT_ID
    
    echo ""
    echo -e "${RED}IMPORTANT: Keep this key file secure and never commit it to version control!${NC}"
    echo -e "${YELLOW}Set the environment variable:${NC}"
    echo "export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/$KEY_FILE"
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "Service Account Email: ${YELLOW}$SA_EMAIL${NC}"
echo ""
echo -e "${YELLOW}Granted Roles:${NC}"
echo "- secretmanager.secretAccessor"
echo "- run.serviceAgent"
echo "- logging.logWriter"
echo "- monitoring.metricWriter"
if [[ "$storage_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "- storage.objectAdmin (optional)"
fi
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Ensure all secrets are created in Secret Manager"
echo "2. Deploy the application with: ./deploy-cloudrun.sh"
echo "3. Set up Cloud Scheduler with: ./setup-scheduler.sh"
