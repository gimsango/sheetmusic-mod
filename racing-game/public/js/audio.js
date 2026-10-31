// WebAudio: 엔진음, 드리프트, 효과음 (외부 파일 없음)
export class Sound {
  constructor() { this.ctx = null; this.enabled = true; }
  init() {
    if (this.ctx) { this.ctx.resume(); return; }
    try {
      const C = window.AudioContext || window.webkitAudioContext; if (!C) return;
      const ctx = this.ctx = new C();
      this.master = ctx.createGain(); this.master.gain.value = 0.5; this.master.connect(ctx.destination);
      this.osc = ctx.createOscillator(); this.osc.type = 'sawtooth';
      this.osc2 = ctx.createOscillator(); this.osc2.type = 'square';
      this.lp = ctx.createBiquadFilter(); this.lp.type = 'lowpass'; this.lp.frequency.value = 600;
      this.eg = ctx.createGain(); this.eg.gain.value = 0;
      this.osc.connect(this.lp); this.osc2.connect(this.lp); this.lp.connect(this.eg); this.eg.connect(this.master);
      this.osc.start(); this.osc2.start();
      const buf = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate), d = buf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
      this.noise = ctx.createBufferSource(); this.noise.buffer = buf; this.noise.loop = true;
      this.nf = ctx.createBiquadFilter(); this.nf.type = 'bandpass'; this.nf.frequency.value = 1800; this.nf.Q.value = 1.2;
      this.ng = ctx.createGain(); this.ng.gain.value = 0;
      this.noise.connect(this.nf); this.nf.connect(this.ng); this.ng.connect(this.master); this.noise.start();
    } catch (e) { this.ctx = null; }
  }
  engine(speedRatio, throttle, drift, offroad, boost) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime, f = 55 + speedRatio * 150 + (boost ? 25 : 0);
    this.osc.frequency.setTargetAtTime(f, t, 0.05); this.osc2.frequency.setTargetAtTime(f * 0.5, t, 0.05);
    this.lp.frequency.setTargetAtTime(350 + speedRatio * 900 + throttle * 500, t, 0.08);
    this.eg.gain.setTargetAtTime(this.enabled ? 0.07 + throttle * 0.05 : 0, t, 0.1);
    this.ng.gain.setTargetAtTime(this.enabled ? (drift ? 0.12 : offroad ? 0.07 * speedRatio : 0.012 * speedRatio) : 0, t, 0.08);
    this.nf.frequency.setTargetAtTime(drift ? 2600 : 900, t, 0.1);
  }
  silence() { if (this.ctx) { const t = this.ctx.currentTime; this.eg.gain.setTargetAtTime(0, t, 0.1); this.ng.gain.setTargetAtTime(0, t, 0.1); } }
  beep(freq = 440, dur = 0.15, type = 'sine', vol = 0.3, slide = 0) {
    if (!this.ctx || !this.enabled) return;
    const t = this.ctx.currentTime, o = this.ctx.createOscillator(), g = this.ctx.createGain();
    o.type = type; o.frequency.setValueAtTime(freq, t); if (slide) o.frequency.exponentialRampToValueAtTime(freq * slide, t + dur);
    g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(0.001, t + dur);
    o.connect(g); g.connect(this.master); o.start(t); o.stop(t + dur + 0.02);
  }
  count(go) { go ? this.beep(880, 0.6, 'square', 0.25) : this.beep(440, 0.2, 'square', 0.2); }
  boost() { this.beep(300, 0.5, 'sawtooth', 0.2, 3); }
  bump() { this.beep(90, 0.15, 'square', 0.3, 0.5); }
  tier() { this.beep(1200, 0.08, 'triangle', 0.15); }
  lap() { this.beep(660, 0.12, 'triangle', 0.25); setTimeout(() => this.beep(990, 0.25, 'triangle', 0.25), 120); }
}
