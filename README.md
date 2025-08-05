# AutoMailHelpdesk

## Project Goal
Build a **fully-automated**, production-grade email-to-ticket helpdesk assistant in Python that never goes down and always leaves every outgoing reply in Gmail drafts for human sign-off.

## Core Features
- Email Ingestion & Deduplication
- Email Parsing
- Ticket Management (Odoo Helpdesk)
- Intent Classification (Gemini + Langchain)
- Business Logic Modules (Bank Statement, Password Update, General Query, Urgent/Fallback)
- Chat History & Memory
- Observability & Monitoring
- Async Processing & Scalability
- Deployment & Reliability
- CI/CD & Quality

## Non-Functional Requirements
- Python 3.11, FastAPI (or Flask + Gunicorn + Uvicorn)
- Async I/O with `asyncio` and `aiohttp`/`google-aio`
- ORM and migrations via SQLAlchemy + Alembic
- Secrets management via `.env` (dotenv) and optional Vault/Secret Manager
- Configuration via Pydantic settings and YAML files in `config/`
- Rate-limiting logic to respect Gmail and Gemini API quotas
- Security practices: OAuth2 flows, encrypted credentials, and PII masking in logs

## Prerequisites and Environment Variable Setup

## Local Development with Docker Compose

## Production Deployment via Helm

## Running Tests and Generating Coverage Reports
