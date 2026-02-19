# Appointment Agent

A full-stack appointment booking agent. External chatbots connect via webhook; a React dashboard manages settings.

## Quick Start

```bash
# 1. Copy .env.example and fill in values
cp .env.example .env

# 2. Generate required keys
openssl rand -hex 32               # → SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # → ENCRYPTION_KEY

# 3. Start with Docker
docker-compose up --build

# 4. Open http://localhost:8000 — login with admin/changeme
```

## Webhook Usage

```bash
curl -X POST http://localhost:8000/webhook/{your-webhook-path} \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "user-123", "message": "What times are free tomorrow?"}'
```

Response:
```json
{ "response": "Let me check availability...", "sessionId": "user-123" }
```

## Creating a New Website Instance

1. Click **New Instance** in the sidebar
2. Fill in **Configuration** tab: name, webhook path, business name, timezone, hours
3. Fill in **Calendar** tab: choose Google Calendar or Microsoft 365, paste credentials
4. Click **Create Instance**
5. Go to **Webhook** tab to copy the webhook URL → point your chatbot to it

## Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev  # proxies API to localhost:8000
```

## Supported LLM Providers

Configure in **Global Settings** panel:
- GitHub Models (GPT-4o) — default
- OpenAI
- Anthropic (Claude)
- Mistral
- Any OpenAI-compatible API

## Supported Calendar Providers (per instance)

- **Google Calendar** — Service Account credentials
- **Microsoft 365 / Outlook** — Azure AD App Registration
