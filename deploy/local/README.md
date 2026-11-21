# Self-hosting the backend from an always-on machine

Interim setup used for the live demo: the backend runs on a home machine and is
exposed through a free Cloudflare quick tunnel; the Vercel frontend is re-pointed
automatically when the tunnel URL changes.

```
Vercel (Next.js) ──HTTPS/WSS──► *.trycloudflare.com ──► cloudflared ──► 127.0.0.1:8010 (FastAPI + Chromium)
        ▲                                                   │
        └──── elliotai-url-sync (timer, every 2 min) ───────┘  detects a new tunnel URL → updates Vercel env → redeploys
```

| Unit | Role |
|---|---|
| `elliotai-backend.service` | uvicorn on 127.0.0.1 only; guards from `~/.config/elliotai/backend.env` |
| `elliotai-tunnel.service` | `cloudflared` quick tunnel (no account); `Wants=` (not `Requires=`) so backend restarts keep the same URL |
| `elliotai-url-sync.timer` / `.service` | runs `elliotai-url-sync.sh`: health-checks the new URL before switching the frontend |

## Install

```bash
sed -i "s#REPO_DIR#$PWD#g; s#NODE_BIN_DIR#$(dirname "$(which node)")#g" deploy/local/*.service
cp deploy/local/*.service deploy/local/*.timer ~/.config/systemd/user/
mkdir -p ~/.config/elliotai && cat > ~/.config/elliotai/backend.env <<'ENV'
BLOCK_PRIVATE_TARGETS=true          # SSRF guard: a public auditor must not reach your LAN
AUDIT_RATE_LIMIT_PER_HOUR=5
MAX_CONCURRENT_AUDITS=1
ALLOWED_TIERS=quick_scan,standard_audit
ALLOWED_ORIGINS=https://<your-app>.vercel.app
ENV
(cd frontend && npx vercel link --yes --project <your-project>)
systemctl --user daemon-reload
systemctl --user enable --now elliotai-backend elliotai-tunnel elliotai-url-sync.timer
sudo loginctl enable-linger "$USER"   # keep user services running without a login session
```

The NIM key stays in `elliot/.env` (gitignored); nothing secret goes into the units.

## Limits
- Quick-tunnel hostnames change when `cloudflared` restarts (reboot, crash); the frontend follows within ~2 minutes plus a Vercel build.
- Throughput is one audit at a time on the host's hardware. Move to a VM (e.g. Oracle Always Free) for a permanent setup.
