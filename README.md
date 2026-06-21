# Kong AI Gateway

A self-hosted, multi-provider AI chat platform that routes prompts across five free LLM providers with automatic failover, JWT authentication, per-user token limits, and a daily featured models system powered by OpenRouter.

---

## Features

- **Multi-provider routing** — Gemini, Groq, Mistral, Cohere, and OpenRouter in one interface
- **Auto failover** — if one provider is rate-limited or down, the next picks up instantly
- **Free models only** — OpenRouter integration enforces `price == 0` at every level
- **Daily top-10 featured models** — cron job fetches the best free models from OpenRouter every day at 9am UTC
- **JWT authentication** — every endpoint is protected; first registered account becomes admin
- **Per-user token limits** — configurable daily cap, resets at midnight UTC
- **Agent system** — create named assistants with custom system prompts and persistent history
- **Admin dashboard** — user management, token usage stats, provider breakdown, activity log
- **Vercel ready** — deploys as a Python serverless function in one command
- **Supabase Postgres** — fully stateless server, all data in the cloud

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + Flask |
| Database | Supabase Postgres (psycopg2) |
| Auth | JWT (PyJWT) |
| Streaming | Server-Sent Events (SSE) |
| API Gateway | Kong (Docker, optional) |
| Hosting | Vercel (serverless) |
| Frontend | Vanilla JS + HTML (no build step) |

---

## Providers

| Provider | Model | Free Limit |
|----------|-------|-----------|
| Gemini | 2.5 Flash | 15 req/min, 1M tokens/day |
| Groq | Llama 3.3 70B | 30 req/min, 14,400 req/day |
| Mistral | Mistral 7B | 60 req/min |
| Cohere | Command-A | 20 req/min |
| OpenRouter | Top 10 free models (daily) | Varies per model |

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/DevstackK/Kongllmrouter.git
cd Kongllmrouter
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys and Supabase connection string. See [HOW_TO.md](HOW_TO.md) for where to get each key.

### 3. Set up Supabase

1. Create a free project at https://supabase.com
2. Go to **Project Settings → Database → Session pooler** and copy the connection URI
3. Paste it as `DATABASE_URL` in your `.env`

Tables are created automatically on first run.

### 4. Run

```bash
python api/index.py
```

Open **http://localhost:5001** — register an account (first account is admin).

---

## Deployment

### Vercel (recommended)

```bash
npm install -g vercel
vercel
```

Add all `.env` variables to your Vercel project dashboard, then:

```bash
vercel --prod
```

The cron job (`0 9 * * *`) runs automatically on Vercel Pro. On the free Hobby plan, trigger `/api/cron/refresh-models` manually or via an external scheduler.

### Docker + Kong

```bash
docker compose up -d
```

Kong proxy on **:8000**, admin API on **:8001**. See [HOW_TO.md](HOW_TO.md) for plugin configuration.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `GROQ_API_KEY` | Groq API key |
| `MISTRAL_API_KEY` | Mistral API key |
| `COHERE_API_KEY` | Cohere API key |
| `OPENROUTER_API_KEY` | OpenRouter API key (enables 5th provider + featured models) |
| `OPENROUTER_MODEL` | Default model — must end in `:free` |
| `JWT_SECRET` | Long random string for signing tokens |
| `RESET_SECRET` | Passphrase for the password reset endpoint |
| `MAX_USERS` | Maximum registered accounts |
| `DAILY_TOKEN_LIMIT` | Per-user token cap per day |
| `DATABASE_URL` | Supabase session pooler connection string |

---

## API

All endpoints require `Authorization: Bearer <token>` except register, login, and health.

```
POST /api/register          Register a new account
POST /api/login             Login and receive a JWT
GET  /api/health            Provider configuration status
GET  /api/providers         List available providers and featured models
POST /api/chat              Stream a chat response (SSE)
GET  /api/agents            List agents
POST /api/agents            Create an agent
DELETE /api/agents/:id      Delete an agent
GET  /api/agents/:id/messages   Message history
POST /api/agents/:id/messages   Save messages
GET  /api/cron/refresh-models   Trigger featured models refresh
```

Full request/response examples in [HOW_TO.md](HOW_TO.md).

---

## File Structure

```
├── api/
│   └── index.py           # Flask app — all routes, SSE, auth, DB
├── static/
│   ├── index.html         # Chat UI
│   └── admin.html         # Admin dashboard
├── vercel.json            # Vercel routing + cron
├── docker-compose.yml     # Kong container
├── kong.yml               # Kong declarative config
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
└── HOW_TO.md              # Full setup and deployment guide
```

---

## Full Documentation

See [HOW_TO.md](HOW_TO.md) for complete setup instructions including Supabase configuration, Docker + Kong plugin reference, Vercel deployment steps, and the full API reference.
