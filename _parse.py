import json

try:
    with open('ws_out.txt', 'r', encoding='utf-16', errors='ignore') as f:
        events = []
        for line in f:
            idx = line.find('{')
            if idx != -1:
                try:
                    events.append(json.loads(line[idx:].strip()))
                except Exception:
                    pass

    with open('events.json', 'w') as f:
        json.dump([e.get('type') for e in events], f, indent=2)

    cvss_list = [e for e in events if e.get('type') == 'cvss_metrics']
    with open('cvss.json', 'w') as f:
        json.dump(cvss_list, f, indent=2)

    print(f"Parsed {len(events)} events. cvss_list len: {len(cvss_list)}")
except Exception as e:
    print(f"err: {e}")
