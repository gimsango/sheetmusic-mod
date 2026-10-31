// 터보 카트 3D - 정적 파일 + WebSocket 멀티플레이 서버
// 같은 WiFi(LAN)의 다른 기기에서 http://<이 PC의 IP>:3000 으로 접속하면 됩니다.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { WebSocketServer } from 'ws';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT) || 3000;
const PUBLIC = path.join(__dirname, 'public');
const THREE_DIR = path.join(__dirname, 'node_modules', 'three');
const MAX_PLAYERS = 12;

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.png': 'image/png',
  '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
};

function lanAddresses() {
  const out = [];
  for (const list of Object.values(os.networkInterfaces())) {
    for (const n of list || []) if (n.family === 'IPv4' && !n.internal) out.push(n.address);
  }
  return out;
}

function serveFile(res, file) {
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not found'); return; }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-cache' });
    res.end(data);
  });
}

const server = http.createServer((req, res) => {
  const url = decodeURIComponent((req.url || '/').split('?')[0]);
  if (url === '/info') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ port: PORT, addresses: lanAddresses().map((a) => `http://${a}:${PORT}`) }));
    return;
  }
  let base = PUBLIC, rel = url;
  if (url.startsWith('/vendor/three/')) { base = THREE_DIR; rel = url.slice('/vendor/three'.length); }
  const file = path.normalize(path.join(base, rel === '/' ? '/index.html' : rel));
  if (!file.startsWith(base)) { res.writeHead(403); res.end('Forbidden'); return; }
  serveFile(res, file);
});

// ---------- 방 / 멀티플레이 ----------
const rooms = new Map(); // code -> room
let nextId = 1;

function makeCode() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  for (;;) {
    let c = '';
    for (let i = 0; i < 4; i++) c += chars[Math.floor(Math.random() * chars.length)];
    if (!rooms.has(c)) return c;
  }
}
const send = (ws, obj) => { if (ws.readyState === 1) ws.send(JSON.stringify(obj)); };
const roomPlayers = (room) => [...room.players.values()].map((p) => ({ id: p.id, name: p.name, kart: p.kart }));
function broadcast(room, obj, exceptId) {
  const msg = JSON.stringify(obj);
  for (const p of room.players.values()) if (p.id !== exceptId && p.ws.readyState === 1) p.ws.send(msg);
}
function roomInfo(room) {
  return { t: 'room', code: room.code, host: room.host, map: room.map, laps: room.laps, bots: room.bots,
    state: room.state, players: roomPlayers(room) };
}
function leave(ws) {
  const room = ws.room; if (!room) return;
  room.players.delete(ws.pid);
  ws.room = null;
  if (room.players.size === 0) { rooms.delete(room.code); return; }
  if (room.host === ws.pid) room.host = room.players.keys().next().value;
  broadcast(room, { t: 'left', id: ws.pid });
  broadcast(room, roomInfo(room));
}

const wss = new WebSocketServer({ server, path: '/ws' });
wss.on('connection', (ws) => {
  ws.pid = 'p' + nextId++;
  ws.room = null;
  ws.isAlive = true;
  ws.on('pong', () => { ws.isAlive = true; });
  ws.on('message', (raw) => {
    let m; try { m = JSON.parse(raw); } catch { return; }
    const room = ws.room;
    switch (m.t) {
      case 'create': {
        leave(ws);
        const code = makeCode();
        const r = { code, host: ws.pid, map: 1, laps: 3, bots: 0, state: 'lobby', players: new Map() };
        rooms.set(code, r);
        r.players.set(ws.pid, { id: ws.pid, ws, name: String(m.name || '레이서').slice(0, 14), kart: m.kart | 0 });
        ws.room = r;
        send(ws, { t: 'welcome', id: ws.pid });
        send(ws, roomInfo(r));
        break;
      }
      case 'join': {
        const r = rooms.get(String(m.code || '').toUpperCase());
        if (!r) return send(ws, { t: 'error', msg: '방을 찾을 수 없습니다.' });
        if (r.state !== 'lobby') return send(ws, { t: 'error', msg: '이미 레이스가 진행 중입니다.' });
        if (r.players.size >= MAX_PLAYERS) return send(ws, { t: 'error', msg: '방이 가득 찼습니다.' });
        leave(ws);
        r.players.set(ws.pid, { id: ws.pid, ws, name: String(m.name || '레이서').slice(0, 14), kart: m.kart | 0 });
        ws.room = r;
        send(ws, { t: 'welcome', id: ws.pid });
        broadcast(r, roomInfo(r));
        break;
      }
      case 'profile': {
        if (!room) return;
        const p = room.players.get(ws.pid);
        if (p) { p.name = String(m.name || p.name).slice(0, 14); p.kart = m.kart | 0; }
        broadcast(room, roomInfo(room));
        break;
      }
      case 'settings': {
        if (!room || room.host !== ws.pid || room.state !== 'lobby') return;
        if (m.map) room.map = Math.min(1000, Math.max(1, m.map | 0));
        if (m.laps) room.laps = Math.min(10, Math.max(1, m.laps | 0));
        if (m.bots != null) room.bots = Math.min(MAX_PLAYERS - 1, Math.max(0, m.bots | 0));
        broadcast(room, roomInfo(room));
        break;
      }
      case 'start': {
        if (!room || room.host !== ws.pid || room.state !== 'lobby') return;
        room.state = 'racing';
        const order = roomPlayers(room).sort(() => Math.random() - 0.5);
        order.forEach((p, i) => { p.slot = i; });
        const bots = [];
        for (let i = 0; i < Math.min(room.bots, MAX_PLAYERS - order.length); i++) {
          bots.push({ id: 'b' + (i + 1), name: 'BOT ' + (i + 1), kart: Math.floor(Math.random() * 100000), slot: order.length + i });
        }
        broadcast(room, { t: 'start', map: room.map, laps: room.laps, countdown: 5000, players: order, bots });
        break;
      }
      case 'lobby': {
        if (!room || room.host !== ws.pid) return;
        room.state = 'lobby';
        broadcast(room, roomInfo(room));
        broadcast(room, { t: 'tolobby' });
        break;
      }
      case 's': // 위치 상태 (고빈도)
      case 'b': // 호스트가 시뮬레이션하는 봇 상태
      case 'fin': // 결승선 통과
        if (!room) return;
        m.id = ws.pid;
        broadcast(room, m, ws.pid);
        break;
      case 'chat':
        if (!room) return;
        broadcast(room, { t: 'chat', id: ws.pid, text: String(m.text || '').slice(0, 80) });
        break;
    }
  });
  ws.on('close', () => leave(ws));
  ws.on('error', () => {});
});

setInterval(() => {
  for (const ws of wss.clients) {
    if (!ws.isAlive) { ws.terminate(); continue; }
    ws.isAlive = false; ws.ping();
  }
}, 15000);

server.listen(PORT, '0.0.0.0', () => {
  console.log('\n🏁 터보 카트 3D 서버 시작!');
  console.log(`  이 PC       : http://localhost:${PORT}`);
  for (const a of lanAddresses()) console.log(`  WiFi/LAN    : http://${a}:${PORT}   ← 같은 WiFi의 친구들에게 알려주세요`);
  console.log('');
});
