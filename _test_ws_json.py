import asyncio, json, websockets, urllib.request

req = urllib.request.Request(
    "http://localhost:8000/api/audit/start",
    data=json.dumps({"url": "https://avrut.com", "tier": "standard_audit", "verdict_mode": "expert"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
resp = json.loads(urllib.request.urlopen(req).read())
audit_id = resp["audit_id"]

events = []

async def stream():
    async with websockets.connect(f"ws://localhost:8000/api/audit/stream/{audit_id}") as ws:
        async for msg in ws:
            try:
                data = json.loads(msg)
                events.append(data)
                t = data.get("type")
                if t in ("audit_complete", "audit_error"):
                    break
            except Exception:
                pass
    with open('events_dump.json', 'w') as f:
        json.dump(events, f, indent=2)

asyncio.run(stream())
