# Content Automation SaaS — Specification

## Overview

Full-stack AI-powered content automation SaaS with Next.js, Claude API, BullMQ, and pgvector.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 (App Router) |
| Backend | Python/Flask + Node.js |
| AI | Claude API (Anthropic) |
| Queue | BullMQ + Redis |
| Database | PostgreSQL + pgvector |
| Payments | Stripe |
| Auth | LinkedIn OAuth |

## Features

### Core Platform
- AI-powered content creation via Claude API
- BullMQ job queue for async task processing
- Redis-backed job status tracking
- pgvector for content embedding and semantic search
- Content scheduling and automation

### Payments & Auth
- Stripe integration for subscriptions
- LinkedIn OAuth for team authentication

### Modules
- **Content:** Create, schedule, publish content
- **Queue:** BullMQ dashboard for job monitoring
- **Search:** Semantic content search via pgvector
- **Billing:** Stripe subscription management

## API Structure

```
/api/content/*        Content creation and management
/api/queue/*         Job queue status
/api/search/*        Vector search
/api/auth/*          LinkedIn OAuth
/api/billing/*       Stripe webhooks + management
```

## Deployment

Docker + docker-compose. Redis and PostgreSQL via compose.
Stripe webhooks for billing events.
