import urllib.request
import json
import time

def main():
    print("Starting audit...")
    req = urllib.request.Request(
        'http://localhost:8000/api/audit/start',
        data=json.dumps({'url': 'http://example.com', 'tier': 'standard_audit', 'verdict_mode': 'expert'}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    audit_id = data['audit_id']
    print(f"Audit started: {audit_id}")
    
    # We will poll via DB directly to check status and result since we know we use DB
    import sys
    sys.path.append('.')
    import asyncio
    from veritas.db import init_database
    from veritas.db.repositories import AuditRepository
    
    async def poll():
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        engine = create_async_engine('sqlite+aiosqlite:///./data/veritas_audits.db')
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        while True:
            async with async_session() as session:
                repo = AuditRepository(session)
                audit = await repo.get_by_id(audit_id)
                if not audit:
                    print("Audit not found in DB yet...")
                else:
                    print(f"Status: {audit.status}")
                    if audit.status in ['completed', 'failed']:
                        return audit
            time.sleep(5)

    result = asyncio.run(poll())
    print("\nResult:", result.status)
    if result.result:
        try:
            res_data = json.loads(result.result)
            print("Result Keys:", res_data.keys())
            for k, v in res_data.items():
                if isinstance(v, list):
                    print(f"Array '{k}': size={len(v)}")
        except Exception as e:
            print("Could not parse result JSON:", e)

if __name__ == '__main__':
    main()
