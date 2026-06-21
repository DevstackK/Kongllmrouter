"""
CLI client — streams responses from the LLM router with live output.
Usage: python client.py [prompt]
"""

import httpx
import json
import sys

SERVER_URL = "http://localhost:5000/api/chat"


def chat(prompt: str, provider: str = "auto") -> str:
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "provider": provider,
    }

    chunks = []
    with httpx.stream("POST", SERVER_URL, json=payload, timeout=60) as resp:
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")

        for line in resp.iter_lines():
            if not line.startswith("data: "):
                continue
            data = json.loads(line[6:])

            if data["type"] == "chunk":
                print(data["content"], end="", flush=True)
                chunks.append(data["content"])
            elif data["type"] == "done":
                usage = data.get("usage") or {}
                total = (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
                suffix = f" · {total} tokens" if total else ""
                print(f"\n\n[{data.get('provider', '')}]{suffix}")
            elif data["type"] == "error":
                raise RuntimeError(data.get("message", "Unknown error"))

    return "".join(chunks)


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello! Which model are you?"
    print(f"Prompt: {prompt}\n")
    chat(prompt)
