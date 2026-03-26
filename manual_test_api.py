import urllib.request
import json
import time

def main():
    print("Starting automated audit...")
    req = urllib.request.Request(
        'http://localhost:8000/api/audit/start',
        data=json.dumps({'url': 'http://example.com', 'tier': 'standard_audit', 'verdict_mode': 'expert'}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    audit_id = data['audit_id']
    print(f"Audit started: {audit_id}")
    
    while True:
        try:
            status_res = urllib.request.urlopen(f'http://localhost:8000/api/audit/{audit_id}/status')
            status_data = json.loads(status_res.read())
            st = status_data.get('status')
            res_data = status_data.get('result')
            print(f"Status: {st}")
            
            if st in ['completed', 'failed']:
                print("\nAudit Final Status:", st)
                if res_data:
                    print("Result Keys:", res_data.keys())
                    for k, v in res_data.items():
                        if isinstance(v, list):
                            print(f"Array '{k}': size={len(v)}")
                        elif isinstance(v, dict):
                            for subk, subv in v.items():
                                if isinstance(subv, list):
                                    print(f"Array '{k}.{subk}': size={len(subv)}")
                break
        except Exception as e:
            print("Poll Error:", e)
        time.sleep(5)

if __name__ == '__main__':
    main()
