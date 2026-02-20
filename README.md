# APIShield 🛡️

> Production-grade API rate limiting, abuse protection, and usage analytics — as a service.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)](https://fastapi.tiangolo.com)
[![Redis](https://img.shields.io/badge/Redis-7.x-red.svg)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://docker.com)

---

## The Problem

Every team building APIs eventually needs the same infrastructure:

- Rate limiting to prevent abuse
- API keys with scopes and per-key quotas
- IP blocking and anomaly detection
- Usage metrics and dashboards
- Usage-based billing

Most early-stage teams don't want to manage Nginx configs, maintain Redis Lua scripts, or wire up their own billing pipeline. **APIShield gives you all of that as a plug-and-play service.**

Think of it as a simplified, focused alternative to the relevant pieces of Cloudflare + Kong + Auth0 — without the complexity you don't need.

---

## Features

### 🔑 API Key Management

- Create, rotate, and revoke API keys
- Scope-based permissions (read, write, admin)
- Per-key rate limits and usage quotas
- Key expiration and audit logs

### ⚡ Rate Limiting Engine

- **Fixed window** — simple, low-overhead counting per time window
- **Sliding window** — smoother enforcement without boundary spikes
- **Token bucket** — bursts allowed up to a ceiling, refilled over time
- Distributed enforcement via atomic Redis operations
- Per-key, per-IP, and per-endpoint limit tiers

### 🚨 Abuse Detection

- IP burst detection with auto-blocking
- Geo anomaly detection (unusual origin patterns)
- Suspicious request pattern analysis (scanner signatures, credential stuffing)
- Configurable temporary vs. permanent blocks
- Webhook alerts for abuse events

### 📊 Usage Analytics Dashboard

- Requests per minute / hour / day
- Error rates and latency percentiles (p50, p95, p99)
- Top endpoints by volume and error rate
- Per-API-key usage breakdowns
- Real-time and historical views

### 💳 Usage-Based Billing

- Stripe integration for metered billing
- Configurable plans and overage pricing
- Automated invoice generation
- Usage export (CSV / JSON)

---

## Architecture

```
                        ┌─────────────────────────────────┐
                        │          Client Request          │
                        └────────────────┬────────────────┘
                                         │
                        ┌────────────────▼────────────────┐
                        │       Nginx / Envoy Gateway      │
                        └────────────────┬────────────────┘
                                         │
                   ┌─────────────────────▼──────────────────────┐
                   │              FastAPI Core Service            │
                   │                                              │
                   │  ┌────────────┐  ┌──────────┐  ┌────────┐  │
                   │  │  API Key   │  │   Rate   │  │ Abuse  │  │
                   │  │  Manager   │  │ Limiter  │  │ Engine │  │
                   │  └────────────┘  └──────────┘  └────────┘  │
                   └──────┬──────────────────┬────────────┬──────┘
                          │                  │            │
           ┌──────────────▼──┐    ┌──────────▼──┐   ┌───▼──────────────┐
           │   PostgreSQL     │    │    Redis     │   │  Kafka (async)   │
           │ Tenants, plans,  │    │ Rate counters│   │ Analytics events │
           │ billing, keys    │    │ IP blocklist │   │                  │
           └─────────────────┘    └─────────────┘   └──────────────────┘
                                                              │
                                                   ┌──────────▼──────────┐
                                                   │ Prometheus + Grafana │
                                                   │  Metrics & Dashboards│
                                                   └─────────────────────┘
```

**Tech Stack**

| Layer             | Technology             |
| ----------------- | ---------------------- |
| API Framework     | FastAPI (Python 3.11+) |
| Primary Database  | PostgreSQL 15          |
| Rate Limit Store  | Redis 7                |
| Event Streaming   | Apache Kafka           |
| Billing           | Stripe                 |
| Gateway           | Nginx / Envoy          |
| Observability     | Prometheus + Grafana   |
| Container Runtime | Docker + Kubernetes    |

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- A Stripe account (for billing features)

### Local Setup

```bash
# Clone the repository
git clone https://github.com/your-org/apishield.git
cd apishield

# Copy environment config
cp .env.example .env
# Edit .env with your Stripe keys, DB credentials, etc.

# Start all services
docker compose up -d

# Run database migrations
docker compose exec api alembic upgrade head

# Create your first tenant and API key
curl -X POST http://localhost:8000/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "My App", "plan": "starter"}'
```

The API will be available at `http://localhost:8000` and the Grafana dashboard at `http://localhost:3000`.

### Protecting Your API

Add APIShield to your stack by routing requests through the gateway:

```bash
# Option 1: Use the SDK (Python)
pip install apishield

# Option 2: Use the middleware directly in FastAPI
from apishield import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    apishield_url="https://your-apishield-instance.com",
    api_key="sk_live_...",
)

# Option 3: Point your Nginx upstream at the APIShield gateway
```

---

## API Reference

### Create an API Key

```http
POST /v1/keys
Authorization: Bearer <tenant_token>
Content-Type: application/json

{
  "name": "Production Key",
  "scopes": ["read", "write"],
  "rate_limit": {
    "strategy": "sliding_window",
    "requests": 1000,
    "window_seconds": 60
  },
  "quota": {
    "monthly_requests": 500000
  }
}
```

### Check Rate Limit Status

```http
GET /v1/keys/{key_id}/usage
Authorization: Bearer <tenant_token>
```

### Block an IP

```http
POST /v1/blocklist
Authorization: Bearer <tenant_token>
Content-Type: application/json

{
  "ip": "1.2.3.4",
  "reason": "scraping",
  "duration_seconds": 3600
}
```

Full API docs are available at `http://localhost:8000/docs` when running locally.

---

## Rate Limiting Strategies

### Fixed Window

Counts requests in discrete time buckets. Lowest overhead, but susceptible to boundary bursts (up to 2× the limit at window edges).

```
Window:    [--- 60s ---][--- 60s ---]
Limit:            1000          1000
Worst case: 1000 + 1000 = 2000 in 1 second at the boundary
```

### Sliding Window

Maintains a rolling count over the past N seconds. Eliminates boundary bursts at slightly higher memory cost.

```
At any moment: count of requests in the past 60s ≤ limit
```

### Token Bucket

Tokens accumulate at a steady refill rate up to a burst ceiling. Ideal for APIs that want to allow short bursts while enforcing an average throughput.

```
Refill rate:  100 tokens/second
Burst ceiling: 500 tokens
```

---

## Project Structure

```
apishield/
├── api/                  # FastAPI application
│   ├── routers/          # Endpoint handlers
│   ├── middleware/        # Rate limiting, auth
│   └── schemas/          # Pydantic models
├── core/
│   ├── rate_limiter/     # Fixed, sliding, token bucket implementations
│   ├── abuse_detector/   # IP burst, geo anomaly, pattern detection
│   └── key_manager/      # Key lifecycle management
├── workers/              # Kafka consumers, async analytics processors
├── billing/              # Stripe integration, usage metering
├── infra/
│   ├── docker/           # Dockerfiles
│   ├── k8s/              # Kubernetes manifests
│   └── terraform/        # Infrastructure as code
├── migrations/           # Alembic database migrations
├── tests/                # Unit and integration tests
└── grafana/              # Dashboard JSON definitions
```

---

## Configuration

Key environment variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/apishield

# Redis
REDIS_URL=redis://localhost:6379/0

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Kafka (optional, for async analytics)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Abuse detection thresholds
BURST_THRESHOLD_REQUESTS=100
BURST_THRESHOLD_WINDOW_SECONDS=5
GEO_ANOMALY_ENABLED=true
```

---

## Roadmap

**MVP (v0.1)**

- [x] API key CRUD with scope enforcement
- [x] Fixed window and sliding window rate limiting
- [x] Redis-backed distributed counters
- [x] Basic usage metrics API

**v0.2**

- [ ] Token bucket strategy
- [ ] IP burst detection and auto-blocking
- [ ] Grafana dashboard templates
- [ ] Stripe metered billing integration

**v0.3**

- [ ] Geo anomaly detection
- [ ] Request pattern analysis
- [ ] Multi-region Redis replication
- [ ] SDK packages (Python, Node.js, Go)

**v1.0**

- [ ] Self-serve onboarding portal
- [ ] Custom alert rules and webhooks
- [ ] SLA guarantees and HA deployment guide

---

## Contributing

Contributions are welcome. Please open an issue before submitting a large PR so we can discuss the approach.

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linting
ruff check . && mypy .
```

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<p align="center">Built for backend engineers who'd rather ship features than maintain rate-limit scripts.</p>
