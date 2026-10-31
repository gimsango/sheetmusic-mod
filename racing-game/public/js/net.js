// WebSocket 클라이언트 (같은 서버에서 서빙 -> 같은 WiFi 기기들이 접속)
export class Net {
  constructor() { this.ws = null; this.h = {}; this.id = null; this.connected = false; }
  on(t, fn) { this.h[t] = fn; return this; }
  connect() {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === 1) return resolve();
      const proto = location.protocol === 'https:' ? 'wss' : 'ws';
      let ws;
      try { ws = new WebSocket(`${proto}://${location.host}/ws`); } catch (e) { return reject(e); }
      this.ws = ws;
      ws.onopen = () => { this.connected = true; resolve(); };
      ws.onerror = () => reject(new Error('서버에 연결할 수 없습니다'));
      ws.onclose = () => { this.connected = false; this.h.close && this.h.close(); };
      ws.onmessage = (ev) => {
        let m; try { m = JSON.parse(ev.data); } catch { return; }
        if (m.t === 'welcome') this.id = m.id;
        const fn = this.h[m.t]; if (fn) fn(m);
      };
    });
  }
  send(o) { if (this.ws && this.ws.readyState === 1) this.ws.send(JSON.stringify(o)); }
  close() { if (this.ws) { this.ws.onclose = null; this.ws.close(); } this.ws = null; this.connected = false; this.id = null; }
}
