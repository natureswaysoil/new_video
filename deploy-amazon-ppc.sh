#!/bin/bash
# Deployment script for Amazon PPC Optimizer
# This script builds and deploys the Amazon PPC optimizer to Google Cloud

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Amazon PPC Optimizer Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if PROJECT_ID is set
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID environment variable is not set${NC}"
    echo "Usage: export GCP_PROJECT_ID=your-project-id && ./deploy-amazon-ppc.sh"
    exit 1
fi

PROJECT_ID=$GCP_PROJECT_ID
REGION="us-central1"
REPO_NAME="amazon-ppc-repo"
IMAGE_NAME="amazon-ppc-optimizer"
SERVICE_NAME="amazon-ppc-optimizer"

echo -e "${YELLOW}Project ID: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo ""

# Step 1: Create Artifact Registry repository if it doesn't exist
echo -e "${GREEN}[1/5] Creating Artifact Registry repository...${NC}"
if gcloud artifacts repositories describe $REPO_NAME --location=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "Repository '$REPO_NAME' already exists"
else
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Amazon PPC Optimizer Docker images" \
        --project=$PROJECT_ID
    echo -e "${GREEN}✓ Repository created${NC}"
fi

# Step 2: Configure Docker authentication
echo -e "${GREEN}[2/5] Configuring Docker authentication...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Step 3: Build the Docker image
echo -e "${GREEN}[3/5] Building Docker image...${NC}"
docker build -f Dockerfile.amazon-ppc \
    -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
    .

echo -e "${GREEN}✓ Image built successfully${NC}"

# Step 4: Push the Docker image
echo -e "${GREEN}[4/5] Pushing Docker image to Artifact Registry...${NC}"
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest

echo -e "${GREEN}✓ Image pushed successfully${NC}"

# Step 5: Deploy to Cloud Run (optional)
echo -e "${GREEN}[5/5] Deploying to Cloud Run...${NC}"

# Check if DEPLOY_TO_CLOUD_RUN is set to skip interactive prompt
if [ "${DEPLOY_TO_CLOUD_RUN}" == "yes" ] || [ "${DEPLOY_TO_CLOUD_RUN}" == "true" ]; then
    DEPLOY="yes"
elif [ "${DEPLOY_TO_CLOUD_RUN}" == "no" ] || [ "${DEPLOY_TO_CLOUD_RUN}" == "false" ]; then
    DEPLOY="no"
else
    read -p "Do you want to deploy to Cloud Run? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        DEPLOY="yes"
    else
        DEPLOY="no"
    fi
fi

if [ "$DEPLOY" == "yes" ]; then
    gcloud run deploy $SERVICE_NAME \
        --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
        --region=$REGION \
        --platform=managed \
        --allow-unauthenticated \
        --memory=1Gi \
        --cpu=1 \
        --timeout=900 \
        --set-env-vars=GCP_PROJECT_ID=$PROJECT_ID \
        --project=$PROJECT_ID
    
    echo -e "${GREEN}✓ Deployed to Cloud Run${NC}"
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --format='value(status.url)')
    echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
else
    echo "Skipping Cloud Run deployment"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Image: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"
echo ""
echo "To deploy using Cloud Build instead, run:"
echo "  gcloud builds submit --config=cloudbuild-amazon-ppc.yaml"
