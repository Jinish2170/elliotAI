const fs = require('fs');
const WebSocket = require('ws');
const id = fs.readFileSync('last_audit.txt', 'utf8').trim();
console.log("Listening for audit:", id);
const ws = new WebSocket(`ws://localhost:8000/api/audit/stream/${id}`);
ws.on('message', m => console.log(m.toString()));
ws.on('close', () => console.log('CLOSED'));
ws.on('error', e => console.error(e));
setTimeout(()=>process.exit(0), 15000); // listen for 15s
