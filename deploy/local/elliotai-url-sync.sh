#!/usr/bin/env bash
# Keep the Vercel frontend pointed at the current Cloudflare quick-tunnel URL.
# Quick tunnels get a new *.trycloudflare.com hostname whenever cloudflared
# restarts; this script detects a change, health-checks the new URL, updates the
# Vercel production env vars and redeploys. Run it periodically (systemd timer).
set -euo pipefail

METRICS="${METRICS:-127.0.0.1:20261}"           # cloudflared --metrics address
FRONTEND_DIR="${FRONTEND_DIR:?set FRONTEND_DIR to the linked frontend dir}"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/elliotai/tunnel_url"
VERCEL="${VERCEL:-npx -y vercel@66.6.0}"

host=$(curl -sf -m 5 "http://$METRICS/quicktunnel" \
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("hostname",""))' 2>/dev/null || true)
[ -n "$host" ] || { echo "tunnel not ready"; exit 0; }
url="https://$host"

mkdir -p "$(dirname "$STATE")"
[ "$(cat "$STATE" 2>/dev/null || true)" = "$url" ] && exit 0

# Only switch the frontend once the new tunnel actually serves the API.
curl -sf -m 20 "$url/api/health" >/dev/null || { echo "new tunnel not healthy yet: $url"; exit 0; }

cd "$FRONTEND_DIR"
for k in NEXT_PUBLIC_API_URL NEXT_PUBLIC_WS_URL; do
  $VERCEL env rm "$k" production -y >/dev/null 2>&1 || true
done
printf '%s' "$url"          | $VERCEL env add NEXT_PUBLIC_API_URL production >/dev/null
printf '%s' "wss://$host"   | $VERCEL env add NEXT_PUBLIC_WS_URL production >/dev/null
$VERCEL deploy --prod --yes >/dev/null
echo "$url" > "$STATE"
echo "frontend now points at $url"
