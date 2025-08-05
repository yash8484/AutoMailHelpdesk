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

### 1. Install Dependencies
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
# Run the setup script to create .env file
python scripts/setup_env.py

# This will create .env from env.example with your Gmail API credentials
```

### 3. Gmail API Authentication
```bash
# Run Gmail authentication to get tokens
python scripts/gmail_auth.py

# Follow the browser authentication flow
# Copy tokens from tokens.json to your .env file
```

### 4. Configure Required Services
Update your `.env` file with:
- **Gmail API**: Client ID and Secret (already configured)
- **Google AI**: API Key for Gemini
- **Database**: MySQL connection string
- **Redis**: Redis connection string
- **Odoo**: Helpdesk credentials
- **Langchain**: API key (optional)

### 5. Required Environment Variables
```bash
# Application
SECRET_KEY=your-secret-key
DEBUG=true

# Database
DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/db
REDIS_URL=redis://localhost:6379/0

# Gmail API (configured in env.example)
GMAIL_CLIENT_ID=24910683842-gm81kpcqgl42bvm0oa6u0qee3j7te27u.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=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
GMAIL_REFRESH_TOKEN=your-refresh-token
GMAIL_ACCESS_TOKEN=your-access-token

# Google AI
GOOGLE_API_KEY=your-google-ai-api-key
GOOGLE_PROJECT_ID=my-project-35035-ai-agent

# Odoo
ODOO_URL=https://your-odoo-instance.com
ODOO_DATABASE=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password

# Langchain (optional)
LANGCHAIN_API_KEY=your-langchain-key
```

## Local Development with Docker Compose

## Production Deployment via Helm

## Running Tests and Generating Coverage Reports
