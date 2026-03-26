import urllib.request
import json
req = urllib.request.Request(
    'http://localhost:8000/api/audits/', 
    data=json.dumps({'type':'address','target':'test','audit_type':'standard','options':{}}).encode(), 
    headers={'Content-Type':'application/json'}
)
try:
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    print("GOT DATA:", data)
    open('last_audit.txt', 'w').write(data['audit_id'])
except Exception as e:
    print("FAILED:", e)
