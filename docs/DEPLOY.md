# Deploying elliotAI

**Live demo:** https://elliotai.vercel.app (frontend on Vercel, backend self-hosted behind a Cloudflare tunnel).

## Sizing (measured)

| Requirement | Value | Why it matters |
|---|---|---|
| RAM per audit | **≥ 0.6 GB** peak (Python engine + headless Chromium), plus ~0.15 GB for the API | rules out every 256–512 MB free tier (Render, Koyeb, Railway free, SnapDeploy) |
| Recommended | 1 vCPU / 2 GB | one concurrent audit with headroom |
| Protocols | HTTPS + WebSocket, requests up to ~5 min | rules out short-timeout serverless functions |

## Hosting options (checked November 2026)

| Option | Cost | Fits | Notes |
|---|---|---|---|
| **Self-hosted + Cloudflare quick tunnel** *(current)* | free | ✅ | Any always-on machine. Setup: [`deploy/local/`](../deploy/local/README.md) |
| **Oracle Cloud Always Free** *(planned)* | free (card for verification) | ✅ 2 OCPU / 12 GB ARM | A VM you operate; free A1 capacity is often exhausted |
| Google Cloud Run | free tier (card required) | ✅ 2 GB | Scales to zero; WebSockets supported |
| Azure Container Apps | free grant (card required) | ✅ | Similar to Cloud Run |
| Railway Hobby | $5 / month | ✅ | Free plan capped at 0.5 GB |
| Hugging Face Spaces (Docker) | PRO subscription | ✅ | Free Docker Spaces were discontinued |

Any container host works with the repo [`Dockerfile`](../Dockerfile) (listens on `$PORT`, default 7860).

## Backend configuration

Non-secret settings (environment variables):

| Name | Production value | Purpose |
|---|---|---|
| `NIM_VISION_MODEL` / `NIM_LLM_MODEL` | `nvidia/nemotron-3.5-super-vl-120b-a12b` | pinned models |
| `NIM_VISION_FALLBACK` | `mistralai/mistral-large-4-1t-a52b` | fallback VLM |
| `NIM_DISABLE_THINKING` | `true` | reasoning models return empty answers otherwise |
| `ALLOWED_ORIGINS` | `https://<your-app>.vercel.app` | CORS |
| `BLOCK_PRIVATE_TARGETS` | `true` (default) | SSRF guard: refuse private / loopback / link-local targets |
| `AUDIT_RATE_LIMIT_PER_HOUR` | `5` | per client IP (`CF-Connecting-IP` behind Cloudflare) |
| `MAX_CONCURRENT_AUDITS` | `1`–`2` | RAM bound |
| `ALLOWED_TIERS` | `quick_scan,standard_audit` | keep long tiers off the public demo |
| `PHOENIX_COLLECTOR_ENDPOINT` | optional | export traces to Phoenix (local or Phoenix Cloud) |

Secrets: `NVIDIA_NIM_API_KEY` (and optional `PHOENIX_API_KEY`) go in the host's secret store or the gitignored `elliot/.env`, never into images or unit files.

Health check: `GET /api/health`.

## Frontend → Vercel

The repo's `frontend/vercel.json` pins the Next.js framework preset and `package.json` pins Node 24.x.

```bash
cd frontend
npx vercel link --yes --project <your-project>
printf 'https://<backend-host>' | npx vercel env add NEXT_PUBLIC_API_URL production
printf 'wss://<backend-host>'   | npx vercel env add NEXT_PUBLIC_WS_URL production
npx vercel deploy --prod
```

`NEXT_PUBLIC_*` values are inlined at build time: changing the backend URL requires a redeploy (automated by `deploy/local/elliotai-url-sync.sh` for the tunnel setup).

## Local (same image)

```bash
docker build -t elliotai .
docker run -p 7860:7860 --env-file elliot/.env -e ALLOWED_ORIGINS=http://localhost:3000 elliotai
cd frontend && NEXT_PUBLIC_API_URL=http://localhost:7860 NEXT_PUBLIC_WS_URL=ws://localhost:7860 npm run dev
```

## Known limits
- The rate limiter is in-memory (single instance); multiple instances would need Redis.
- The SSRF guard checks the submitted URL's resolved IPs; redirects or DNS rebinding to private IPs mid-crawl are not re-checked.
- Audit history (SQLite) lives on the host's disk; ephemeral container disks reset it on restart.
