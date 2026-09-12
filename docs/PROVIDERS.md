# Model providers

AI Platform talks to models only through `AuthorizedModelRuntime` → `ProviderRegistry` → adapters.

## Supported configurations

| Mode | `AI_PLATFORM_PROVIDER` | Base URL | API key |
|------|------------------------|----------|---------|
| OpenAI | `openai-compatible` (default) | `https://api.openai.com/v1` | `OPENAI_API_KEY` |
| xAI / Grok | `openai-compatible` | `https://api.x.ai/v1` | `XAI_API_KEY` or `OPENAI_API_KEY` |
| **Ollama (local)** | `ollama` | `http://127.0.0.1:11434/v1` | optional placeholder (`ollama`) |

Ollama uses the same OpenAI-compatible chat completions path.
**Ollama is loopback-only** in the host wiring (no remote arbitrary Ollama URL) to limit SSRF risk.

### Local Ollama example

```bash
# Terminal 1
ollama pull llama3.2
ollama serve

# Host env
export AI_PLATFORM_PROVIDER=ollama
export OPENAI_BASE_URL=http://127.0.0.1:11434/v1
export AI_PLATFORM_TRIAGE_MODEL=llama3.2
# No cloud provider key required
```

Authorization and capabilities are unchanged: denied requests never reach Ollama.

### Vercel note

Serverless Vercel cannot reach your laptop’s Ollama. Use Ollama on a machine/VPC where the API process runs, or keep cloud providers for Vercel Production.

## Adding another OpenAI-compatible host

Set `OPENAI_BASE_URL` + key. SSRF rules still apply (`validate_provider_base_url`).
