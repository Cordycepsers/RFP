#!/bin/bash

# Media Procurement Platform - Deployment Script
# This script deploys the application to Google Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="media-procurement-backend"

echo -e "${BLUE}🚀 Starting deployment of Media Procurement Platform${NC}"
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Region: ${REGION}${NC}"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Not authenticated with gcloud. Please run 'gcloud auth login'${NC}"
    exit 1
fi

# Set the project
echo -e "${YELLOW}📋 Setting project to ${PROJECT_ID}${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable drive.googleapis.com
gcloud services enable sheets.googleapis.com

# Build and deploy using Cloud Build
echo -e "${YELLOW}🏗️ Building and deploying with Cloud Build...${NC}"
gcloud builds submit --config=cloudbuild.yaml ..

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}📊 Health check: ${SERVICE_URL}/health${NC}"

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
if curl -f -s "${SERVICE_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi

echo -e "${BLUE}📝 Next steps:${NC}"
echo -e "${BLUE}1. Configure environment variables in Cloud Run console${NC}"
echo -e "${BLUE}2. Set up Google Service Account credentials${NC}"
echo -e "${BLUE}3. Update Chrome extension with the service URL${NC}"
echo -e "${BLUE}4. Test the complete workflow${NC}"

echo -e "${GREEN}🎉 Deployment complete!${NC}"

