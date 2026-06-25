# AI Data Janitor — Autonomous CRM Data Cleaning Micro-SaaS

**AI Data Janitor** is a production-ready, usage-based micro-SaaS that autonomously connects to Salesforce and HubSpot via OAuth, normalizes fields, deduplicates records, enriches missing data from external APIs, and meters every cleaned record to Stripe at **$0.02 per record**.

## 🚀 Deploy Now

**[📖 See DEPLOY.md for complete deployment guide](DEPLOY.md)** — Zero-cost deployment using GitHub Actions + Fly.io + Vercel + Neon + Upstash.

## Quick Start (Local)

```bash
# Clone the repo
git clone https://github.com/shujariaz-oss/ai-data-janitor.git
cd ai-data-janitor

# Local development (Docker)
docker compose up -d --build

# Access points
# Dashboard:  http://localhost:3000
# API Docs:   http://localhost:8000/docs
# Metrics:    http://localhost:8000/metrics
```

---

## Architecture

```
Frontend (Next.js) → FastAPI → PostgreSQL 16
                           ↓
                    Celery + Redis
                           ↓
              Salesforce / HubSpot APIs
```

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Workers | Celery + Redis |
| Database | PostgreSQL 16 |
| Frontend | Next.js 14, React 18, Tailwind CSS |
| Auth | JWT, bcrypt, AES-256-GCM |
| Billing | Stripe Metered Billing |

---

## API Endpoints

All endpoints require JWT authentication.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | JWT login |
| GET | `/crm/connect/{crm_type}` | Initiate OAuth |
| GET | `/crm/callback` | OAuth callback |
| POST | `/cleaning/trigger` | Trigger cleaning |
| GET | `/cleaning/jobs` | List jobs |
| GET | `/billing/usage` | Usage & cost |
| GET | `/audit/changes` | Audit log |
| POST | `/audit/rollback/{id}` | Rollback change |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
SECRET_KEY=              # 256-bit random
ENCRYPTION_KEY=          # 32-byte AES key
DATABASE_URL=            # PostgreSQL async URL
REDIS_URL=               # Redis connection
STRIPE_SECRET_KEY=       # Stripe test/live key
STRIPE_PRICE_ID=         # Metered price ID
SALESFORCE_CLIENT_ID=    # Salesforce OAuth
HUBSPOT_CLIENT_ID=       # HubSpot OAuth
```

---

## Testing

```bash
make test       # Run pytest
make lint       # Run ruff/black
make test-cov   # Coverage report
```

---

## License

MIT License
