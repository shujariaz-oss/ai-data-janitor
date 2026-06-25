# GitHub Deployment Guide — AI Data Janitor

> **Zero-cost deployment** using GitHub Actions + free cloud services.
> **Time to deploy:** ~15 minutes after you obtain API tokens.

---

## Step 1: Clone & Prepare (1 min)

```bash
git clone https://github.com/shujariaz-oss/ai-data-janitor.git
cd ai-data-janitor
```

---

## Step 2: Fix GitHub Actions Directory (1 min)

The workflows were pushed to `github/workflows/` instead of `.github/workflows/` (GitHub API limitation). Fix it:

```bash
# Rename the directory
git mv github .github
git add .
git commit -m "chore: move workflows to .github directory"
git push origin main
```

Or run the automated setup script:
```bash
bash setup-github.sh
```

---

## Step 3: Sign Up for Free Services (~5 min)

### 3.1 Neon — PostgreSQL Database
1. Go to [neon.tech](https://neon.tech) → Sign up (free)
2. Create a new project named `data-janitor`
3. Copy the **Connection string** (looks like: `postgresql://user:pass@host.neon.tech/db`)
4. Save it as `DATABASE_URL`

### 3.2 Upstash — Redis
1. Go to [upstash.com](https://upstash.com) → Sign up (free)
2. Create a new Redis database
3. Copy the **Endpoint** and **Password**
4. Build `REDIS_URL`: `redis://default:password@host:port`

### 3.3 Fly.io — Backend API + Worker
1. Go to [fly.io](https://fly.io) → Sign up (free, requires credit card for verification)
2. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
3. Login: `fly auth login`
4. Get your token: `fly auth token`
5. Save this as `FLY_API_TOKEN`

### 3.4 Vercel — Frontend
1. Go to [vercel.com](https://vercel.com) → Sign up with GitHub
2. Install Vercel CLI: `npm i -g vercel`
3. Login: `vercel login`
4. Create project: `vercel link` (follow prompts, choose your GitHub repo)
5. Get your tokens:
   - `vercel token` → save as `VERCEL_TOKEN`
   - Check `~/.local/share/com.vercel/cli/auth.json` for `orgId` and `projectId`

### 3.5 Stripe — Billing
1. Go to [stripe.com](https://stripe.com) → Sign up (free test mode)
2. Go to Developers → API Keys → Copy **Secret key** (test mode)
3. Go to Products → Create a product "Data Cleaning" with metered pricing at $0.02/record
4. Copy the **Price ID** (looks like `price_xxx`)

---

## Step 4: Add GitHub Secrets (2 min)

1. Go to your repo: `https://github.com/shujariaz-oss/ai-data-janitor`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

| Secret Name | Value From |
|-------------|-----------|
| `FLY_API_TOKEN` | `fly auth token` |
| `VERCEL_TOKEN` | `vercel token` |
| `VERCEL_ORG_ID` | From `vercel link` output |
| `VERCEL_PROJECT_ID` | From `vercel link` output |

---

## Step 5: Add Environment Variables to Fly.io (3 min)

The backend needs secrets to connect to Neon and Upstash:

```bash
cd backend

# Set secrets for the API app
fly secrets set -a data-janitor-api \
  DATABASE_URL="your-neon-connection-string" \
  REDIS_URL="your-upstash-redis-url" \
  CELERY_BROKER_URL="your-upstash-redis-url" \
  CELERY_RESULT_BACKEND="your-upstash-redis-url" \
  SECRET_KEY="$(openssl rand -hex 32)" \
  ENCRYPTION_KEY="$(openssl rand -hex 32)" \
  STRIPE_SECRET_KEY="sk_test_xxx" \
  STRIPE_PRICE_ID="price_xxx" \
  WEBHOOK_SECRET="whsec_$(openssl rand -hex 32)" \
  SALESFORCE_CLIENT_ID="your-salesforce-client-id" \
  SALESFORCE_CLIENT_SECRET="your-salesforce-secret" \
  HUBSPOT_CLIENT_ID="your-hubspot-client-id" \
  HUBSPOT_CLIENT_SECRET="your-hubspot-secret"

# Set secrets for the worker app
fly secrets set -a data-janitor-worker \
  DATABASE_URL="your-neon-connection-string" \
  REDIS_URL="your-upstash-redis-url" \
  CELERY_BROKER_URL="your-upstash-redis-url" \
  CELERY_RESULT_BACKEND="your-upstash-redis-url" \
  SECRET_KEY="same-as-api" \
  ENCRYPTION_KEY="same-as-api" \
  STRIPE_SECRET_KEY="sk_test_xxx" \
  STRIPE_PRICE_ID="price_xxx"
```

> **Note:** For production, use `STRIPE_SECRET_KEY` starting with `sk_live_` instead of `sk_test_`.

---

## Step 6: Deploy! (1 min)

### Option A: Automatic (via GitHub Actions)

Push any commit to `main` and GitHub Actions will auto-deploy:

```bash
# Make a small change to trigger deployment
echo "# Deployed via GitHub Actions" >> README.md
git add .
git commit -m "trigger: deploy via GitHub Actions"
git push origin main
```

Then go to **Actions** tab in your GitHub repo to watch the deployment.

### Option B: Manual (via CLI)

```bash
# Deploy backend API
cd backend
fly deploy -a data-janitor-api --ha=false

# Deploy worker
fly deploy -a data-janitor-worker --ha=false --config fly.worker.toml

# Deploy frontend
cd ../frontend
vercel --prod
```

---

## Step 7: Verify Deployment (2 min)

After deployment completes:

| Service | URL | Check |
|---------|-----|-------|
| API Docs | `https://data-janitor-api.fly.dev/docs` | FastAPI Swagger UI |
| Health | `https://data-janitor-api.fly.dev/health` | Should return `{"status":"ok"}` |
| Dashboard | `https://your-vercel-app.vercel.app` | Login page |
| API Metrics | `https://data-janitor-api.fly.dev/metrics` | Prometheus metrics |

---

## Troubleshooting

### Issue: `fly deploy` fails with "app not found"
```bash
fly apps create data-janitor-api
fly apps create data-janitor-worker
```

### Issue: Database connection fails
- Check Neon allows connections from Fly.io IPs
- Add `?sslmode=require` to the end of `DATABASE_URL`

### Issue: Redis connection fails
- Upstash uses TLS, so prefix with `rediss://` instead of `redis://`

### Issue: GitHub Actions deploy fails
- Check **Actions** tab for error logs
- Verify all secrets are set correctly
- Ensure `FLY_API_TOKEN` has not expired

---

## Architecture (Deployed)

```
User → Vercel (Next.js)
            ↓
    Fly.io (FastAPI API)
            ↓
    Neon (PostgreSQL) + Upstash (Redis)
            ↓
    Fly.io (Celery Worker)
            ↓
    Salesforce / HubSpot APIs
```

All services are on the **free tier** — zero cost for development and light usage.

---

## Next Steps

1. **Register your first account** at the deployed dashboard
2. **Connect Salesforce or HubSpot** via OAuth
3. **Trigger a cleaning job** and watch the audit log
4. **Check Stripe billing** — usage is tracked automatically

---

**Questions?** Open an issue at: https://github.com/shujariaz-oss/ai-data-janitor/issues
