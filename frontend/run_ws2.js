
const fs = require('fs');
const WebSocket = require('ws');
async function start() {
    const res = await fetch('http://localhost:8000/api/audit/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({url: 'http://example.com', tier: 'standard_audit', verdict_mode: 'expert'})
    });
    const data = await res.json();
    console.log('AUDIT ID:', data.audit_id);
    const ws = new WebSocket('ws://localhost:8000/api/audit/stream/' + data.audit_id);
    ws.on('message', m => console.log(m.toString()));
    ws.on('close', () => console.log('WS CLOSED'));
    setTimeout(() => { ws.close(); console.log('DONE'); process.exit(0); }, 30000);
}
start();

