import json

events = set()
with open('ws_out.txt') as f:
    for line in f:
        idx = line.find('{')
        if idx != -1:
            try:
                events.add(json.loads(line[idx:]).get('type', ''))
            except Exception:
                pass
print(events)
