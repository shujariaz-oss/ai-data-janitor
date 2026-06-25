#!/bin/bash
# AI Data Janitor - One-Command Deploy Script
# Prerequisites: flyctl, vercel CLI, git

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_APP="data-janitor-api"
WORKER_APP="data-janitor-worker"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AI DATA JANITOR - DEPLOY SCRIPT      ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

check_cmd() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}ERROR: $1 is not installed.${NC}"
        echo "Install from: $2"
        exit 1
    fi
}

check_cmd "fly" "https://fly.io/docs/hands-on/install-flyctl/"
check_cmd "vercel" "https://vercel.com/docs/cli"
check_cmd "git" "https://git-scm.com/downloads"

echo -e "${YELLOW}Checking Fly.io auth...${NC}"
fly auth whoami &> /dev/null || {
    echo -e "${YELLOW}Please login to Fly.io:${NC}"
    fly auth login
}

echo -e "${YELLOW}Checking Vercel auth...${NC}"
vercel whoami &> /dev/null || {
    echo -e "${YELLOW}Please login to Vercel:${NC}"
    vercel login
}

echo ""
echo -e "${BLUE}--- Step 1: Backend API ---${NC}"
if ! fly apps list | grep -q "$API_APP"; then
    echo -e "${YELLOW}Creating Fly app: $API_APP${NC}"
    fly apps create "$API_APP" || true
else
    echo -e "${GREEN}App $API_APP already exists.${NC}"
fi

echo -e "${YELLOW}Deploying backend API...${NC}"
cd backend
fly deploy -a "$API_APP" --ha=false
API_URL="https://$API_APP.fly.dev"
echo -e "${GREEN}API deployed: $API_URL${NC}"
cd ..

echo ""
echo -e "${BLUE}--- Step 2: Celery Worker ---${NC}"
if ! fly apps list | grep -q "$WORKER_APP"; then
    echo -e "${YELLOW}Creating Fly app: $WORKER_APP${NC}"
    fly apps create "$WORKER_APP" || true
else
    echo -e "${GREEN}App $WORKER_APP already exists.${NC}"
fi

echo -e "${YELLOW}Deploying worker...${NC}"
cd backend
fly deploy -a "$WORKER_APP" --ha=false --command "celery -A app.tasks.celery worker -l info -c 2"
echo -e "${GREEN}Worker deployed.${NC}"
cd ..

echo ""
echo -e "${BLUE}--- Step 3: Frontend (Vercel) ---${NC}"
cd frontend
vercel env rm NEXT_PUBLIC_API_URL production -y 2>/dev/null || true
vercel env add NEXT_PUBLIC_API_URL production <<< "$API_URL" 2>/dev/null || true

echo -e "${YELLOW}Deploying frontend...${NC}"
vercel --prod --yes
cd ..

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  DEPLOYMENT COMPLETE!                 ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Frontend:${NC}  https://your-app.vercel.app"
echo -e "${BLUE}API:${NC}       $API_URL"
echo -e "${BLUE}API Docs:${NC}  $API_URL/docs"
echo -e "${BLUE}Metrics:${NC}   $API_URL/metrics"
echo -e "${BLUE}Health:${NC}   $API_URL/health"
