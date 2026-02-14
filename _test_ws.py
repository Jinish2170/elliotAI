"""Quick end-to-end test: REST start + WebSocket stream."""
import asyncio, json, websockets, urllib.request

# Step 1: Start audit via REST
req = urllib.request.Request(
    "http://localhost:8000/api/audit/start",
    data=json.dumps({"url": "https://www.example.com", "tier": "quick_scan"}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req).read())
print(f"Audit started: {resp}")
audit_id = resp["audit_id"]


# Step 2: Connect WebSocket and read events
async def stream():
    async with websockets.connect(
        f"ws://localhost:8000/api/audit/stream/{audit_id}"
    ) as ws:
        count = 0
        async for msg in ws:
            data = json.loads(msg)
            t = data.get("type", "?")
            summary = json.dumps(data)[:150]
            print(f"  [{count:>3}] {t:<20} {summary}")
            count += 1
            if t in ("audit_complete", "audit_error"):
                break
    print(f"\nDone - received {count} events total")


asyncio.run(stream())
