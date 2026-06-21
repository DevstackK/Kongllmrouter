#!/bin/bash
curl -s -X POST http://localhost:5000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"say hi and tell me your model name"}]}' | python3 -m json.tool
