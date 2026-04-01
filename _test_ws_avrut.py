import asyncio, json, websockets, urllib.request

req = urllib.request.Request(
    "http://localhost:8000/api/audit/start",
    data=json.dumps({"url": "https://avrut.com", "tier": "standard_audit", "verdict_mode": "expert"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    resp = json.loads(urllib.request.urlopen(req).read())
    print(f"Audit started: {resp}")
    audit_id = resp["audit_id"]

    async def stream():
        async with websockets.connect(
            f"ws://localhost:8000/api/audit/stream/{audit_id}"
        ) as ws:
            count = 0
            async for msg in ws:
                data = json.loads(msg)
                t = data.get("type", "?")
                summary = json.dumps(data)
                print(f"  [{count:>3}] {t:<20} {summary}")
                count += 1
                if t in("audit_complete", "audit_error"):
                    break
        print(f"\nDone - received {count} events total")

    asyncio.run(stream())
except Exception as e:
    print(f"Error: {e}")
