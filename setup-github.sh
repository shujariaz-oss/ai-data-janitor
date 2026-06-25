#!/bin/bash
# Quick setup script for AI Data Janitor deployment via GitHub Actions
# Run this after cloning the repo

set -e

echo "🚀 AI Data Janitor — GitHub Deployment Setup"
echo "=============================================="
echo ""

# Check if we're in the repo directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the ai-data-janitor repo root"
    exit 1
fi

echo "Step 1/4: Renaming github/ → .github/..."
if [ -d "github" ]; then
    git mv github .github
    git add .
    git commit -m "chore: move workflows to .github directory" || true
    echo "✅ Done"
else
    echo "✅ Already renamed (or .github exists)"
fi

echo ""
echo "Step 2/4: Pushing to GitHub..."
git push origin main || echo "⚠️  Push failed — you may need to pull first or set upstream"

echo ""
echo "=============================================="
echo "✅ GitHub repository is ready!"
echo ""
echo "Next steps:"
echo "1. Sign up for free services:"
echo "   • Neon (DB):      https://neon.tech"
echo "   • Upstash (Redis): https://upstash.com"
echo "   • Fly.io (API):    https://fly.io"
echo "   • Vercel (Frontend): https://vercel.com"
echo "   • Stripe (Billing):  https://stripe.com"
echo ""
echo "2. Add GitHub Secrets:"
echo "   Go to: https://github.com/shujariaz-oss/ai-data-janitor/settings/secrets/actions"
echo "   Add: FLY_API_TOKEN, VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID"
echo ""
echo "3. Run backend setup:"
echo "   cd backend"
echo "   fly deploy -a data-janitor-api --ha=false"
echo "   fly deploy -a data-janitor-worker --ha=false --config fly.worker.toml"
echo ""
echo "4. Deploy frontend:"
echo "   cd ../frontend"
echo "   vercel --prod"
echo ""
echo "📖 Full guide: DEPLOY.md"
