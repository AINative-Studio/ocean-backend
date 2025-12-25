#!/bin/bash

# Ocean Backend - Railway Setup Script
# This script helps you set up the Railway project and environment variables

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================"
echo "Ocean Backend - Railway Setup"
echo "========================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}Error: Railway CLI not found${NC}"
    echo "Install with: npm install -g @railway/cli"
    exit 1
fi

echo -e "${GREEN}✓ Railway CLI found${NC}"
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "Please login to Railway:"
    railway login
fi

echo -e "${GREEN}✓ Logged in to Railway${NC}"
echo ""

# Prompt for environment variables
echo "========================================"
echo "Environment Configuration"
echo "========================================"
echo ""

read -p "Enter ZERODB_PROJECT_ID: " ZERODB_PROJECT_ID
read -p "Enter ZERODB_API_KEY: " ZERODB_API_KEY
read -p "Enter ZERODB_API_URL (default: https://api.ainative.studio): " ZERODB_API_URL
ZERODB_API_URL=${ZERODB_API_URL:-https://api.ainative.studio}

# Generate secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo ""
echo -e "${GREEN}Generated SECRET_KEY${NC}"

# Confirm environment
echo ""
echo "========================================"
echo "Configuration Summary"
echo "========================================"
echo "ZERODB_API_URL: $ZERODB_API_URL"
echo "ZERODB_PROJECT_ID: $ZERODB_PROJECT_ID"
echo "ZERODB_API_KEY: ****${ZERODB_API_KEY: -4}"
echo "SECRET_KEY: ****${SECRET_KEY: -4}"
echo ""

read -p "Deploy to which environment? (staging/production): " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-staging}

# Switch to environment
echo ""
echo "Switching to $ENVIRONMENT environment..."
railway environment create "$ENVIRONMENT" 2>/dev/null || echo "Environment already exists"
railway environment "$ENVIRONMENT"

echo ""
echo "Setting environment variables..."

# Set all required variables
railway variables set ZERODB_API_URL="$ZERODB_API_URL"
railway variables set ZERODB_PROJECT_ID="$ZERODB_PROJECT_ID"
railway variables set ZERODB_API_KEY="$ZERODB_API_KEY"
railway variables set SECRET_KEY="$SECRET_KEY"
railway variables set PROJECT_NAME="Ocean Backend"
railway variables set DEBUG="false"
railway variables set OCEAN_EMBEDDINGS_MODEL="BAAI/bge-base-en-v1.5"
railway variables set OCEAN_EMBEDDINGS_DIMENSIONS="768"
railway variables set API_V1_STR="/api/v1"

# Set CORS origins
if [ "$ENVIRONMENT" == "staging" ]; then
    CORS='["http://localhost:3000","http://localhost:5173"]'
else
    read -p "Enter production frontend URLs (comma-separated): " PROD_URLS
    CORS="[\"$PROD_URLS\"]"
fi

railway variables set BACKEND_CORS_ORIGINS="$CORS"

echo ""
echo -e "${GREEN}✓ Environment variables configured${NC}"

# Ask if they want to deploy now
echo ""
read -p "Deploy now? (y/n): " DEPLOY_NOW

if [ "$DEPLOY_NOW" == "y" ]; then
    echo ""
    echo "Deploying to Railway..."
    railway up

    echo ""
    echo "Waiting for deployment to complete (30s)..."
    sleep 30

    # Get the domain
    DOMAIN=$(railway domain 2>/dev/null || echo "")

    if [ -n "$DOMAIN" ]; then
        echo ""
        echo -e "${GREEN}Deployment complete!${NC}"
        echo ""
        echo "Service URL: https://$DOMAIN"
        echo "Health: https://$DOMAIN/health"
        echo "Docs: https://$DOMAIN/docs"
        echo ""

        # Ask if they want to run smoke tests
        read -p "Run smoke tests? (y/n): " RUN_TESTS

        if [ "$RUN_TESTS" == "y" ]; then
            export RAILWAY_STAGING_URL="https://$DOMAIN"
            ./scripts/smoke_tests.sh
        fi
    else
        echo ""
        echo -e "${YELLOW}Deployment initiated. Check Railway dashboard for status.${NC}"
        echo "Run 'railway logs' to view deployment logs."
    fi
else
    echo ""
    echo "Setup complete. Deploy later with: railway up"
fi

echo ""
echo "========================================"
echo "Next Steps"
echo "========================================"
echo "1. View logs: railway logs"
echo "2. Check status: railway status"
echo "3. Open dashboard: railway open"
echo "4. Run smoke tests: ./scripts/smoke_tests.sh"
echo ""
