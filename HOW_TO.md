# Kong AI Gateway — How To Guide

## What Is This?

A self-hosted AI router that lets you chat with four free LLM providers (Gemini, Groq, Mistral, Cohere) through a single endpoint. When one provider hits its rate limit, it automatically falls back to the next. Includes a web UI, persistent agents, and a streaming API.

**Two deployment modes:**
- **Flask app** — runs directly on Python, handles all routing itself
- **Kong Gateway** — sits in front as a production-grade API gateway (recommended for anything beyond local use)

---

## Prerequisites

- Python 3.10+
- Docker (for Kong mode)
- API keys for the providers you want to use (all have free tiers)

---

## Quick Start — Flask App

### 1. Copy and fill in your API keys

```bash
cp .env.example .env
# Edit .env and paste your keys
```

Get free keys from:
- Gemini: https://aistudio.google.com/app/apikey
- Groq: https://console.groq.com/keys
- Mistral: https://console.mistral.ai/api-keys
- Cohere: https://dashboard.cohere.com/api-keys

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Start the server

**Windows via WSL** (the venv was created in WSL, so use this):

Open your WSL terminal, then:

```bash
cd /mnt/c/Users/urfan/Desktop/Claude/kong-ai-gateway
source venv/bin/activate
python api/index.py
```

**Mac/Linux:**

```bash
source venv/bin/activate
python api/index.py
```

**Windows PowerShell (native):** requires recreating the venv in PowerShell — use WSL instead.

You'll see `* Running on http://0.0.0.0:5000` — open http://localhost:5000 in your browser.

To stop the server press `Ctrl+C`.

### 4. Test without the browser

**Windows PowerShell:**

```powershell
curl -X POST http://localhost:5000/api/chat `
  -H "Content-Type: application/json" `
  -d '{"messages":[{"role":"user","content":"say hi"}]}'
```

**Mac/Linux:**

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"say hi"}]}'
```

---

## Quick Start — Kong Gateway (Docker)

Kong is used as a production API gateway in front of the Flask app or as a standalone AI proxy.

### 1. Fill in your `.env` file (same as above)

### 2. Start Kong

```bash
docker compose up -d
```

Kong proxy is now available on port **8000**, admin API on **8001** (localhost only).

### 3. Test the AI route through Kong

```bash
curl -s -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello, who are you?"}]}'
```

### 4. Check Kong's admin API

```bash
# List all routes
curl http://localhost:8001/routes

# List all plugins
curl http://localhost:8001/plugins

# Kong health
curl http://localhost:8001/status
```

---

## Using the Web UI

1. Open http://localhost:5000
2. **Auto Fallback** mode tries providers in order: Gemini → Groq → Mistral → Cohere
3. Select a specific model from the dropdown to pin to one provider
4. The provider badge in the top bar shows which model answered

### Creating an Agent

Agents have a persistent system prompt that shapes every reply.

1. Click **+ New Agent** in the sidebar
2. Give it a name and a system prompt (e.g. "You are a concise code reviewer")
3. Choose a default model or leave it on Auto
4. Click the agent name to open its chat — history is saved between sessions

---

## CLI Client

```bash
# Basic usage
python client.py "Explain recursion in one sentence"

# The client streams responses live and prints token count at the end
```

The client always uses Auto Fallback mode.

---

## API Reference

All endpoints are served by the Flask app on port 5000.

### Chat

```
POST /api/chat
Content-Type: application/json

{
  "messages": [{"role": "user", "content": "Hello"}],
  "provider": "auto",          // auto | gemini | groq | mistral | cohere
  "system_prompt": "..."       // optional, overrides agent system prompt
}
```

Returns a **Server-Sent Events** stream:

```
data: {"type": "provider", "name": "Gemini 2.5 Flash"}
data: {"type": "chunk", "content": "Hello"}
data: {"type": "chunk", "content": "!"}
data: {"type": "done", "provider": "Gemini 2.5 Flash", "usage": {"input_tokens": 5, "output_tokens": 3}}
```

### Providers

```
GET /api/providers
```

Returns the list of configured providers with their IDs and display names.

### Health Check

```
GET /api/health
```

Shows which providers have API keys configured.

### Agents

```
GET    /api/agents              # list all agents
POST   /api/agents              # create agent {name, system_prompt, model}
DELETE /api/agents/:id          # delete agent
GET    /api/agents/:id/messages # get message history (last 100)
POST   /api/agents/:id/messages # save messages [{role, content, provider, usage}]
```

---

## Kong Gateway — Features

Kong is built on **OpenResty**, which is **NGINX + Lua scripting**. This means Kong inherits all of NGINX's performance (event-driven, non-blocking, handles tens of thousands of concurrent connections) and adds a plugin system on top.

### What you get from the NGINX base

- Async, non-blocking request handling — no thread-per-request overhead
- Efficient SSL/TLS termination
- HTTP/1.1 and HTTP/2 support
- Load balancing across upstream servers
- Proxy buffering and connection pooling
- Static file serving

### Kong plugins you can enable for the AI gateway

**Security**
| Plugin | What it does |
|--------|-------------|
| `key-auth` | Require an API key on every request — so only your apps can call the gateway |
| `jwt` | Bearer token authentication |
| `oauth2` | Full OAuth2 flow |
| `ip-restriction` | Whitelist/blacklist IP ranges |
| `bot-detection` | Block known scrapers and bots |
| `cors` | Cross-origin request control |

**Rate Limiting**
| Plugin | What it does |
|--------|-------------|
| `rate-limiting` | Requests per second/minute/hour (already in `kong.yml` at 15 rpm) |
| `ai-rate-limiting-advanced` | Limit by token count instead of requests (Enterprise) |
| `request-size-limiting` | Cap payload size |

**Observability**
| Plugin | What it does |
|--------|-------------|
| `prometheus` | Exposes `/metrics` for Grafana dashboards |
| `file-log` | Log every request/response to a file |
| `http-log` | Forward logs to a webhook or logging service |
| `datadog` / `zipkin` | APM and distributed tracing |

**Transformations**
| Plugin | What it does |
|--------|-------------|
| `request-transformer` | Add/remove/rename headers and body fields before sending upstream |
| `response-transformer` | Modify the response before returning to the client |
| `ai-prompt-template` | Inject a fixed template around every prompt (Enterprise) |
| `ai-prompt-guard` | Block prompts matching patterns you define (Enterprise) |

**Reliability**
| Plugin | What it does |
|--------|-------------|
| `proxy-cache` | Cache identical responses — saves tokens on repeated questions |
| `ai-semantic-cache` | Cache by semantic similarity, not exact match (Enterprise) |
| `circuit-breaker` | Stop sending to a failing upstream automatically |
| `health-checks` | Active and passive health checks on upstream targets |

**AI-Specific** (built into Kong's `ai-proxy` plugin, already in `kong.yml`)
| Feature | What it does |
|---------|-------------|
| Provider abstraction | Single `/ai/chat` endpoint, Kong translates to Gemini/OpenAI/etc. format |
| Model routing | Route to different models based on headers or request content |
| Token tracking | Kong logs input/output token counts automatically |

### Adding a plugin via the Admin API (no restart needed)

```bash
# Add API key auth to the ai-llm-router service
curl -X POST http://localhost:8001/services/ai-llm-router/plugins \
  -d name=key-auth

# Create a consumer and give them a key
curl -X POST http://localhost:8001/consumers \
  -d username=myapp

curl -X POST http://localhost:8001/consumers/myapp/key-auth \
  -d key=my-secret-key-123

# Now requests need the header: apikey: my-secret-key-123
```

### Adding a plugin in `kong.yml` (declarative, requires restart)

```yaml
plugins:
  - name: key-auth
    service: ai-llm-router
    config:
      key_names: [apikey]

  - name: proxy-cache
    service: ai-llm-router
    config:
      response_code: [200]
      request_method: [POST]
      cache_ttl: 300
      strategy: memory
```

---

## File Structure

```
kong-ai-gateway/
├── api/
│   └── index.py        # Main Flask app — all routes, SSE streaming, SQLite
├── static/
│   └── index.html      # Web UI (single file, no build step)
├── client.py           # CLI streaming client
├── kong.yml            # Kong declarative config (database-off mode)
├── docker-compose.yml  # Kong + environment wiring
├── .env                # Your API keys (gitignored)
├── .env.example        # Template for new installs
├── requirements.txt    # Python dependencies
└── data.db             # SQLite database, created on first run (gitignored)
```

---

## Free Tier Limits (approximate)

| Provider | Model | Free Limit |
|----------|-------|-----------|
| Gemini | 2.5 Flash | 15 req/min, 1M tokens/day |
| Groq | Llama 3.3 70B | 30 req/min, 14,400 req/day |
| Mistral | 7B | 1 req/sec, varies |
| Cohere | Command-A | 20 req/min, 1,000 req/month |

With Auto Fallback, the router cycles through all four — the ~51M tokens/day figure in the UI assumes you hit each provider's daily max.
