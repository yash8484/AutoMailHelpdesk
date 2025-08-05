# AutoMailHelpdesk Architecture

## Overview
AutoMailHelpdesk is a fully-automated, production-grade email-to-ticket helpdesk assistant built in Python. It integrates with Gmail, Odoo, Google Gemini, Langchain, and ChromaDB to provide intelligent email processing, intent classification, and automated responses, while ensuring human oversight through Gmail drafts.

## Key Components

### 1. Email Ingestion & Deduplication
- **Gmail API (OAuth2)**: Used to poll for new emails on a configurable interval.
- **Deduplication**: Emails are deduplicated by Gmail message ID to prevent reprocessing.
- **Health Checks**: `/healthz` and `/readyz` endpoints are exposed for service monitoring.

### 2. Email Parsing
- Extracts sender, subject, body, attachments, and embedded Ticket IDs (via regex).
- Malformed emails are routed to an "error queue" for review.

### 3. Ticket Management (Odoo Helpdesk)
- Integrates with Odoo Helpdesk via its API.
- **Existing Tickets**: If a Ticket ID is present, the system fetches the ticket. If the last known intent matches the current intent, the message and metadata are appended. If intents differ, a new ticket is created.
- **New Tickets**: If no Ticket ID is present, a new ticket is always created.
- **Chat History**: Full chat history and per-message intent are persisted in Odoo custom fields or a related model.

### 4. Intent Classification (Gemini + Langchain)
- Uses a Langchain `LLMChain` wrapping Google Gemini to classify email intent into categories like `bank_statement`, `password_update`, `general_query`, `urgent_human`, or `fallback_human`.
- Extracts structured entities (e.g., `months`, `current_pw`, `new_pw`).

### 5. Business Logic Modules
- **Bank Statement Handler**: Queries MySQL for last-N months, generates a PDF (ReportLab/FPDF), and creates a Gmail draft with the PDF attached.
- **Password Update Handler**: Verifies `current_pw` using bcrypt, updates `new_pw` in the database, and drafts a success email or a request for missing/invalid passwords.
- **General Query Handler**: Generates embeddings via Google Embedding API, performs vector search against ChromaDB, runs a RAG chain with Gemini for answers and citations, and drafts the response email.
- **Urgent / Fallback Handler**: Notifies human support via Slack/email and drafts an acknowledgment email.

### 6. Chat History & Memory
- Stores every incoming/outgoing turn (timestamp, intent, ticket_id) in a database or Odoo model.
- Implements a Langchain `ConversationBufferMemory` subclass keyed by `ticket_id` and `email_id` to pass context into LLM calls.

### 7. Observability & Monitoring
- **Resilience**: All external API calls are wrapped with `tenacity` for retries and exponential backoff, and `aiobreaker` for circuit-breaking.
- **Logging**: Emits structured JSON logs to stdout, integrated with Sentry or Datadog.
- **LLM Tracing**: Records every LLM invocation and prompt variant in Langsmith; workflow visualized in Langraph.

### 8. Async Processing & Scalability
- Uses Celery with Redis or RabbitMQ as a broker for parallel email processing.
- State is stored in PostgreSQL or MySQL with indexes on `ticket_id` and `email_id` for sub-100ms lookups.

### 9. Deployment & Reliability
- **Containerization**: Services are Dockerized with multi-stage builds.
- **Orchestration**: Kubernetes (or Cloud Run) manifests/Helm charts include resource requests/limits, Horizontal Pod Autoscaling, liveness/readiness probes, and blue/green or canary deployment strategies.
- **Data Backup**: Automates daily backups of ChromaDB snapshots and Odoo database dumps.
- **Infrastructure (Optional)**: Terraform files for infrastructure provisioning.

### 10. CI/CD & Quality
- **GitHub Actions**: Workflows for linting (flake8), formatting (black), type checking (mypy), testing (pytest), and coverage reporting.
- **Dependency Management**: Dependabot configuration for automated dependency updates.
- **Pre-commit Hooks**: `isort`, `black`, and `safety` checks.

## Technology Stack
- **Language**: Python 3.11
- **Web Framework**: FastAPI (or Flask + Gunicorn + Uvicorn)
- **Async I/O**: `asyncio`, `aiohttp`/`google-aio`
- **ORM/Migrations**: SQLAlchemy + Alembic
- **Secrets Management**: `.env` (dotenv), optional Vault/Secret Manager
- **Configuration**: Pydantic settings, YAML files
- **Rate Limiting**: Custom logic for Gmail and Gemini APIs
- **Security**: OAuth2, encrypted credentials, PII masking

## Data Flow Diagram (Conceptual)

```mermaid
graph TD
    A[Incoming Email (Gmail)] --> B{Email Ingestion & Deduplication}
    B --> C{Email Parsing}
    C -- Malformed --> D[Error Queue]
    C -- Valid --> E{Ticket ID Check}
    E -- No Ticket ID --> F[Create New Odoo Ticket]
    E -- Ticket ID Present --> G{Fetch Odoo Ticket}
    G --> H{Intent Comparison}
    H -- Identical Intent --> I[Append to Odoo Ticket]
    H -- Different Intent --> F
    F --> J[Intent Classification (Gemini + Langchain)]
    I --> J
    J --> K{Business Logic Modules}
    K -- Bank Statement --> L[Query MySQL & Generate PDF]
    K -- Password Update --> M[Verify/Update DB & Draft Email]
    K -- General Query --> N[Embed, Vector Search ChromaDB, RAG]
    K -- Urgent/Fallback --> O[Notify Human Support]
    L --> P[Create Gmail Draft]
    M --> P
    N --> P
    O --> P
    P --> Q[Outgoing Reply (Gmail Drafts)]
    
    subgraph Observability
        J -- LLM Invocation --> R[Langsmith]
        K -- API Calls --> S[Tenacity & Aiobreaker]
        S --> T[Structured JSON Logs (Sentry/Datadog)]
    end
    
    subgraph Data Storage
        F -- Persist History --> U[PostgreSQL/MySQL]
        I -- Persist History --> U
        N -- Knowledge Base --> V[ChromaDB]
        U -- Memory --> W[Langchain ConversationBufferMemory]
    end
    
    subgraph Async Processing
        C -- Process Email --> X[Celery Queue (Redis/RabbitMQ)]
        X --> Y[Celery Workers]
        Y --> J
    end
```


