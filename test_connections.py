"""Quick connection test for all providers and the database."""
import os, json, sys
from dotenv import load_dotenv

load_dotenv()

results = {}

# ── Database ──────────────────────────────────────────────────────────────────
try:
    import psycopg2
    url = os.getenv("DATABASE_URL", "")
    conn = psycopg2.connect(url, connect_timeout=5)
    cur = conn.cursor()
    cur.execute("SELECT version()")
    ver = cur.fetchone()[0].split(",")[0]
    conn.close()
    results["database"] = f"OK  — {ver}"
except Exception as e:
    results["database"] = f"FAIL — {e}"

# ── Gemini ────────────────────────────────────────────────────────────────────
try:
    import httpx
    key = os.getenv("GEMINI_API_KEY", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    body = {"contents": [{"parts": [{"text": "Say OK"}]}], "generationConfig": {"maxOutputTokens": 5}}
    r = httpx.post(url, json=body, timeout=15)
    if r.status_code == 200:
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        results["gemini"] = f"OK  — reply: {text!r}"
    else:
        results["gemini"] = f"FAIL — HTTP {r.status_code}: {r.text[:120]}"
except Exception as e:
    results["gemini"] = f"FAIL — {e}"

# ── Groq ──────────────────────────────────────────────────────────────────────
try:
    key = os.getenv("GROQ_API_KEY", "")
    headers = {"Authorization": f"Bearer {key}"}
    body = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}
    r = httpx.post("https://api.groq.com/openai/v1/chat/completions", json=body, headers=headers, timeout=15)
    if r.status_code == 200:
        text = r.json()["choices"][0]["message"]["content"].strip()
        results["groq"] = f"OK  — reply: {text!r}"
    else:
        results["groq"] = f"FAIL — HTTP {r.status_code}: {r.text[:120]}"
except Exception as e:
    results["groq"] = f"FAIL — {e}"

# ── Mistral ───────────────────────────────────────────────────────────────────
try:
    key = os.getenv("MISTRAL_API_KEY", "")
    headers = {"Authorization": f"Bearer {key}"}
    body = {"model": "open-mistral-7b", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}
    r = httpx.post("https://api.mistral.ai/v1/chat/completions", json=body, headers=headers, timeout=15)
    if r.status_code == 200:
        text = r.json()["choices"][0]["message"]["content"].strip()
        results["mistral"] = f"OK  — reply: {text!r}"
    else:
        results["mistral"] = f"FAIL — HTTP {r.status_code}: {r.text[:120]}"
except Exception as e:
    results["mistral"] = f"FAIL — {e}"

# ── Cohere ────────────────────────────────────────────────────────────────────
try:
    key = os.getenv("COHERE_API_KEY", "")
    headers = {"Authorization": f"Bearer {key}"}
    body = {"model": "command-a-03-2025", "messages": [{"role": "user", "content": "Say OK"}]}
    r = httpx.post("https://api.cohere.com/v2/chat", json=body, headers=headers, timeout=15)
    if r.status_code == 200:
        text = r.json()["message"]["content"][0]["text"].strip()
        results["cohere"] = f"OK  — reply: {text!r}"
    else:
        results["cohere"] = f"FAIL — HTTP {r.status_code}: {r.text[:200]}"
except Exception as e:
    results["cohere"] = f"FAIL — {e}"

# ── Print ─────────────────────────────────────────────────────────────────────
print()
width = max(len(k) for k in results) + 2
for name, status in results.items():
    print(f"  {name:<{width}} {status}")
print()

any_fail = any("FAIL" in v for v in results.values())
sys.exit(1 if any_fail else 0)
