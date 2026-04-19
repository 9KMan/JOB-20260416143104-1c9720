# Content Automation SaaS Platform

AI-powered content automation platform with Next.js, Claude API, BullMQ, and pgvector.

## Tech Stack

- **Frontend:** Next.js 14 (App Router)
- **Backend:** Node.js + Express + BullMQ
- **AI:** Claude API (Anthropic)
- **Queue:** BullMQ + Redis
- **Database:** PostgreSQL + pgvector
- **Payments:** Stripe
- **Auth:** LinkedIn OAuth

## Features

| Feature | Description |
|---------|-------------|
| AI Content Creation | Claude API integration for automated content |
| Task Queue | BullMQ + Redis for async processing |
| Vector Search | pgvector for content embeddings |
| Scheduling | Automated content scheduling |
| Payments | Stripe subscription integration |
| Auth | LinkedIn OAuth |

## Quick Start

```bash
# Backend
pip install -r requirements.txt
python run.py

# Frontend
npm install
npm run dev

# Docker
docker-compose up --build
```

## Structure

```
app/
  models/        Data models
  modules/       Feature modules (auth, financial, procurement, production, sales, reporting)
  static/        Assets
  templates/     HTML templates
docker-compose.yml
requirements.txt
run.py
tests/
```
