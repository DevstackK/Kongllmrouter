import os
import json
import httpx
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)

AGENTS_FILE = "agents.json"

PROVIDERS = {
    "gemini": {
        "name": "Gemini 2.5 Flash",
        "url": f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}",
        "type": "gemini",
    },
    "groq": {
        "name": "Groq Llama 3.3 70B",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "type": "openai",
        "headers": {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
        "model": "llama-3.3-70b-versatile",
    },
    "mistral": {
        "name": "Mistral 7B",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "type": "openai",
        "headers": {"Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}"},
        "model": "open-mistral-7b",
    },
    "cohere": {
        "name": "Cohere Command-A",
        "url": "https://api.cohere.com/v2/chat",
        "type": "cohere",
        "headers": {"Authorization": f"Bearer {os.getenv('COHERE_API_KEY')}"},
        "model": "command-a-03-2025",
    },
}

AUTO_ORDER = ["gemini", "groq", "mistral", "cohere"]


def load_agents():
    if os.path.exists(AGENTS_FILE):
        with open(AGENTS_FILE) as f:
            return json.load(f)
    return {}


def save_agents(agents):
    with open(AGENTS_FILE, "w") as f:
        json.dump(agents, f, indent=2)


def call_gemini(provider, messages):
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"parts": [{"text": m["content"]}], "role": role})
    resp = httpx.post(provider["url"], json={"contents": contents}, timeout=30)
    if resp.status_code == 200:
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return {"choices": [{"message": {"role": "assistant", "content": text}}]}, 200
    return None, resp.status_code


def call_openai(provider, messages):
    body = {"model": provider["model"], "messages": messages, "max_tokens": 1024}
    resp = httpx.post(provider["url"], json=body, headers=provider["headers"], timeout=30)
    if resp.status_code == 200:
        return resp.json(), 200
    return None, resp.status_code


def call_cohere(provider, messages):
    body = {"model": provider["model"], "messages": messages}
    resp = httpx.post(provider["url"], json=body, headers=provider["headers"], timeout=30)
    if resp.status_code == 200:
        text = resp.json()["message"]["content"][0]["text"]
        return {"choices": [{"message": {"role": "assistant", "content": text}}]}, 200
    return None, resp.status_code


def call_provider(key, messages):
    provider = PROVIDERS[key]
    if provider["type"] == "gemini":
        return call_gemini(provider, messages)
    elif provider["type"] == "openai":
        return call_openai(provider, messages)
    elif provider["type"] == "cohere":
        return call_cohere(provider, messages)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/ai/chat", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages", [])
    provider_key = data.get("provider", "auto")
    agent_id = data.get("agent_id")

    # Inject system prompt if agent selected
    if agent_id:
        agents = load_agents()
        agent = agents.get(agent_id)
        if agent and agent.get("system_prompt"):
            messages = [{"role": "user", "content": f"[System: {agent['system_prompt']}]\n{messages[0]['content']}"}] + messages[1:]

    if provider_key != "auto":
        result, status = call_provider(provider_key, messages)
        if result:
            result["provider"] = PROVIDERS[provider_key]["name"]
            return jsonify(result)
        return jsonify({"error": f"Provider {provider_key} failed with {status}"}), status

    # Auto fallback
    for key in AUTO_ORDER:
        try:
            result, status = call_provider(key, messages)
            if result:
                result["provider"] = PROVIDERS[key]["name"]
                print(f"[OK] {PROVIDERS[key]['name']}")
                return jsonify(result)
            print(f"[SKIP] {key} → {status}")
        except Exception as e:
            print(f"[ERROR] {key}: {e}")

    return jsonify({"error": "All providers exhausted"}), 503


@app.route("/providers", methods=["GET"])
def get_providers():
    return jsonify([{"id": k, "name": v["name"]} for k, v in PROVIDERS.items()])


@app.route("/agents", methods=["GET"])
def list_agents():
    return jsonify(load_agents())


@app.route("/agents", methods=["POST"])
def create_agent():
    data = request.json
    agents = load_agents()
    agent_id = data["name"].lower().replace(" ", "-")
    agents[agent_id] = {"name": data["name"], "system_prompt": data.get("system_prompt", ""), "model": data.get("model", "auto")}
    save_agents(agents)
    return jsonify({"id": agent_id, **agents[agent_id]})


@app.route("/agents/<agent_id>", methods=["DELETE"])
def delete_agent(agent_id):
    agents = load_agents()
    agents.pop(agent_id, None)
    save_agents(agents)
    return jsonify({"ok": True})


if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=False)
