# Deploying elliotAI on free tiers

| Part | Where (free) | Why |
|---|---|---|
| Backend (FastAPI + audit engine + Chromium) | **Hugging Face Spaces**, Docker SDK, CPU basic | 16 GB RAM / 2 vCPU. Each audit runs headless Chromium (~0.5–1 GB); 512 MB tiers (Render/Koyeb free) OOM. |
| Frontend (Next.js) | **Vercel** Hobby | Native Next.js host. |
| Traces | **Phoenix Cloud** (free) or none | OTLP export is optional; local JSONL traces always work. |
| LLM | **NVIDIA NIM** free credits | OpenAI-compatible; models pinned in env. |

## 1. Backend → Hugging Face Space

```bash
# one-time: create a Docker Space at https://huggingface.co/new-space (SDK: Docker)
git clone https://huggingface.co/spaces/<you>/elliotai-backend hf-space
rsync -a --exclude-from=.dockerignore ./ hf-space/   # repo contents minus ignored files
cp deploy/huggingface/README.md hf-space/README.md   # Space card (sdk: docker, app_port: 7860)
cd hf-space && git add -A && git commit -m "deploy" && git push
```

Space → Settings → **Variables and secrets** (secrets are never baked into the image):

| Name | Type | Value |
|---|---|---|
| `NVIDIA_NIM_API_KEY` | secret | your NIM key |
| `NIM_VISION_MODEL` / `NIM_LLM_MODEL` | var | `nvidia/nemotron-3.5-super-vl-120b-a12b` |
| `NIM_VISION_FALLBACK` | var | `mistralai/mistral-large-4-1t-a52b` |
| `NIM_DISABLE_THINKING` | var | `true` |
| `ALLOWED_ORIGINS` | var | `https://<your-app>.vercel.app` |
| `AUDIT_RATE_LIMIT_PER_HOUR` | var | `5` (per client IP) |
| `MAX_CONCURRENT_AUDITS` | var | `2` (RAM bound) |
| `ALLOWED_TIERS` | var | `quick_scan,standard_audit` |
| `BLOCK_PRIVATE_TARGETS` | var | `true` (SSRF guard, default) |
| `PHOENIX_COLLECTOR_ENDPOINT` | var | optional, e.g. your Phoenix Cloud space URL |
| `PHOENIX_API_KEY` | secret | optional, Phoenix Cloud key (sent as `authorization: Bearer`) |

Health check: `GET https://<you>-elliotai-backend.hf.space/api/health`.

## 2. Frontend → Vercel

Import the GitHub repo in Vercel, **Root Directory = `frontend`**, then set:

| Name | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<you>-elliotai-backend.hf.space` |
| `NEXT_PUBLIC_WS_URL` | `wss://<you>-elliotai-backend.hf.space` |

## 3. Local (identical image)

```bash
docker build -t elliotai .
docker run -p 7860:7860 --env-file elliot/.env -e ALLOWED_ORIGINS=http://localhost:3000 elliotai
cd frontend && NEXT_PUBLIC_API_URL=http://localhost:7860 NEXT_PUBLIC_WS_URL=ws://localhost:7860 npm run dev
```

## Known limits of the free setup
- HF free Spaces sleep after inactivity (cold start ~1 min) and have ephemeral disk: audit history (SQLite) resets on restart.
- The rate limiter is in-memory (single instance). Multi-instance would need Redis.
- SSRF guard checks the submitted URL's resolved IPs; redirects / DNS rebinding to private IPs mid-crawl are not re-checked.
