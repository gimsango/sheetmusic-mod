// 아케이드 카트 물리 + AI
import { kartStats } from './karts.js';

const wrapPi = (a) => { while (a > Math.PI) a -= Math.PI * 2; while (a < -Math.PI) a += Math.PI * 2; return a; };
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
export { wrapPi, clamp };

export class KartSim {
  constructor(track, kartId, slot = 0) {
    this.track = track; this.kartId = kartId; this.stats = kartStats(kartId);
    this.q = {};
    this.reset(track.spawnPose(slot));
  }

  reset(pose) {
    const t = this.track;
    this.x = pose.x; this.z = pose.z; this.heading = pose.heading; this.vx = 0; this.vz = 0;
    this.speed = 0; this.drifting = false; this.driftDir = 0; this.driftCharge = 0; this.driftTier = 0; this.boostT = 0;
    this.offroad = false; this.wallHit = 0; this.steerVis = 0; this.slip = 0; this.air = 0;
    t.query(this.x, this.z, -1, this.q);
    this.y = this.q.y; this.hint = this.q.idx;
    this.lastProg = this.q.prog; this.total = pose.prog != null ? pose.prog : 0;
    this.d = this.q.d; this.upx = 0; this.upy = 1; this.upz = 0;
    this.finished = false; this.finishTime = 0; this.events = [];
    this.wrongWay = false;
  }

  get lap() { return Math.max(1, Math.floor(this.total / this.track.N) + 1); }
  get progress() { return this.total; }

  // 트랙 위 가장 가까운 지점으로 리셋 (R 키)
  respawn() {
    const t = this.track, q = this.q, i = q.idx;
    this.x = t.px[i]; this.z = t.pz[i]; this.heading = Math.atan2(t.tx[i], t.tz[i]);
    this.vx = this.vz = this.speed = 0; this.drifting = false; this.driftCharge = 0; this.boostT = 0;
    t.query(this.x, this.z, -1, q); this.y = q.y; this.hint = q.idx; this.lastProg = q.prog;
  }

  update(dt, inp, others = []) {
    const s = this.stats, t = this.track, q = this.q;
    this.events.length = 0;
    const fx = Math.sin(this.heading), fz = Math.cos(this.heading), rx = -fz, rz = fx;
    let vf = this.vx * fx + this.vz * fz, vl = this.vx * rx + this.vz * rz;
    const boosting = this.boostT > 0;
    if (boosting) this.boostT -= dt;
    const cap = s.maxSpeed * (this.offroad ? 0.55 : 1) + (boosting ? 24 : 0);

    // 가속/브레이크
    if (inp.throttle > 0.01) {
      if (vf < cap) vf += s.accelRate * (boosting ? 2.6 : 1) * inp.throttle * (1 - 0.75 * Math.max(0, vf) / cap) * dt;
      else vf -= 26 * dt;
    }
    if (inp.brake > 0.01) { if (vf > 1) vf -= 44 * inp.brake * dt; else vf = Math.max(-16, vf - 16 * inp.brake * dt); }
    else if (inp.throttle < 0.01) vf -= Math.sign(vf) * Math.min(Math.abs(vf), 7 * dt);
    vf *= Math.exp(-(this.offroad ? 0.9 : 0.04) * dt);
    // 경사 (오르막은 느려지고 내리막은 빨라짐)
    vf -= 4.4 * q.ty * Math.sign(this.vx * q.tx + this.vz * q.tz || 1) * dt;

    // 드리프트
    const wantDrift = inp.drift && Math.abs(inp.steer) > 0.25 && vf > 22 && !this.offroad;
    if (!inp.drift) this.armed = true;
    if (!this.drifting && wantDrift && this.armed) { this.armed = false; this.drifting = true; this.driftDir = Math.sign(inp.steer); this.driftCharge = 0; this.events.push('driftStart'); }
    if (this.drifting) {
      if (!inp.drift || vf < 16) {
        const tier = this.driftTier;
        if (tier > 0) { this.boostT = Math.max(this.boostT, [0, 0.7, 1.2, 1.9][tier]); this.events.push('miniturbo'); }
        this.drifting = false; this.driftCharge = 0; this.driftTier = 0;
      } else {
        this.driftCharge += dt * (0.75 + 0.5 * Math.abs(inp.steer * this.driftDir > 0 ? 1 : 0.4));
        const tier = this.driftCharge > 3.2 ? 3 : this.driftCharge > 1.9 ? 2 : this.driftCharge > 0.9 ? 1 : 0;
        if (tier > this.driftTier) this.events.push('tier' + tier);
        this.driftTier = tier;
      }
    }

    // 조향
    const speedF = clamp(Math.abs(vf) / 14, 0, 1) * (1 - 0.3 * clamp(Math.abs(vf) / s.maxSpeed, 0, 1));
    let yawRate;
    if (this.drifting) yawRate = s.turnRate * (0.55 * this.driftDir + 0.6 * inp.steer * (inp.steer * this.driftDir > 0 ? 0.75 : 1)) * 1.15;
    else yawRate = s.turnRate * inp.steer;
    this.heading -= yawRate * speedF * Math.sign(vf || 1) * dt;
    this.steerVis += (inp.steer - this.steerVis) * Math.min(1, dt * 10);

    // 횡 미끄러짐(그립)
    const grip = this.drifting ? s.driftGrip : (boosting ? 7 : 9.5);
    vl *= Math.exp(-grip * dt);
    this.slip = vl;

    // 새 헤딩 기준으로 속도 재구성
    const nfx = Math.sin(this.heading), nfz = Math.cos(this.heading), nrx = -nfz, nrz = nfx;
    this.vx = nfx * vf + nrx * vl; this.vz = nfz * vf + nrz * vl;
    // 속도가 헤딩과 어긋난 만큼은 위에서 vl 로 유지됨
    this.x += this.vx * dt; this.z += this.vz * dt;

    // 다른 카트와 충돌 (원 충돌)
    for (const o of others) {
      const dx = this.x - o.x, dz = this.z - o.z, dist = Math.hypot(dx, dz), min = 2.5;
      if (dist < min && dist > 0.001) {
        const push = (min - dist) / dist * 0.55;
        this.x += dx * push; this.z += dz * push;
        const rel = (this.vx - (o.vx || 0)) * dx / dist + (this.vz - (o.vz || 0)) * dz / dist;
        if (rel < 0) { this.vx -= dx / dist * rel * 0.9; this.vz -= dz / dist * rel * 0.9; this.events.push('bump'); }
        vf *= 0.995;
      }
    }

    // 트랙 질의 + 벽
    t.query(this.x, this.z, this.hint, q);
    this.hint = q.idx;
    if (Math.abs(q.d) > t.wallOff - 1.0) {
      const sgn = Math.sign(q.d), over = Math.abs(q.d) - (t.wallOff - 1.0);
      this.x -= q.rx * over * sgn; this.z -= q.rz * over * sgn;
      const vn = (this.vx * q.rx + this.vz * q.rz) * sgn;
      if (vn > 0) {
        this.vx -= q.rx * sgn * vn * 1.35; this.vz -= q.rz * sgn * vn * 1.35;
        const k = 1 - clamp(vn / 80, 0.04, 0.2); this.vx *= k; this.vz *= k;
        if (vn > 6) { this.wallHit = 1; this.events.push('wall'); }
        if (this.drifting) { this.drifting = false; this.driftCharge = 0; this.driftTier = 0; }
      }
      t.query(this.x, this.z, this.hint, q);
    }
    this.d = q.d;
    this.offroad = Math.abs(q.d) > t.hw + 0.4;
    this.wallHit = Math.max(0, this.wallHit - dt * 4);

    // 부스트 패드
    for (const p of t.pads) {
      let di = q.prog - p.idx; if (di > t.N / 2) di -= t.N; if (di < -t.N / 2) di += t.N;
      if (Math.abs(di * t.ds) < p.halfLen && Math.abs(q.d - p.d) < p.halfW) {
        if (this.padCool <= 0 || this.padCool == null) { this.boostT = Math.max(this.boostT, 1.5); this.events.push('pad'); const f = Math.hypot(this.vx, this.vz); if (f < s.maxSpeed) { this.vx *= (s.maxSpeed) / Math.max(f, 1) * 0.5 + 0.5; this.vz *= (s.maxSpeed) / Math.max(f, 1) * 0.5 + 0.5; } }
        this.padCool = 0.6;
      }
    }
    if (this.padCool > 0) this.padCool -= dt;

    // 높이 / 표면 방향
    this.y = q.y; // 트랙 표면에 스냅
    const cb = Math.cos(q.bank), sb = Math.sin(q.bank);
    let ux = -sb * q.rx * 1, uy = cb, uz = -sb * q.rz * 1;
    // 법선 = rightB x T
    const rbx = q.rx * cb, rby = -sb, rbz = q.rz * cb;
    ux = rby * q.tz - rbz * q.ty; uy = rbz * q.tx - rbx * q.tz; uz = rbx * q.ty - rby * q.tx;
    const ul = Math.hypot(ux, uy, uz) || 1;
    const k = Math.min(1, dt * 8);
    this.upx += (ux / ul - this.upx) * k; this.upy += (uy / ul - this.upy) * k; this.upz += (uz / ul - this.upz) * k;

    // 진행도
    let delta = q.prog - this.lastProg;
    if (delta > t.N / 2) delta -= t.N; else if (delta < -t.N / 2) delta += t.N;
    this.total += delta; this.lastProg = q.prog;
    this.speed = Math.hypot(this.vx, this.vz);
    const fwdDot = (this.vx * q.tx + this.vz * q.tz);
    this.wrongWay = this.speed > 8 && fwdDot < -4 && Math.cos(wrapPi(this.heading - Math.atan2(q.tx, q.tz))) < -0.3;
  }
}

// ---------- AI ----------
export class BotBrain {
  constructor(rand) {
    this.skill = 0.82 + rand() * 0.2;       // 0.82 ~ 1.02
    this.lane = (rand() - 0.5) * 0.7;       // 선호 라인(-0.35~0.35 * 폭)
    this.phase = rand() * 6.28;
    this.t = 0; this.stuck = 0;
  }
  drive(kart, dt, playerProg, rubber = true) {
    const tr = kart.track, q = kart.q, N = tr.N;
    this.t += dt;
    const look = clamp(Math.round((kart.speed * 0.5 + 12) / tr.ds), 5, 34);
    const lane = (this.lane + Math.sin(this.t * 0.35 + this.phase) * 0.12) * tr.width * 0.5;
    const i = (q.idx + look) % N;
    // 코너 안쪽 라인: 다음 커브 방향으로 약간 치우침
    const tx = tr.px[i] + tr.rx[i] * lane, tz = tr.pz[i] + tr.rz[i] * lane;
    const want = Math.atan2(tx - kart.x, tz - kart.z), diff = wrapPi(want - kart.heading);
    const steer = clamp(-diff * 2.2, -1, 1);
    let rb = 1;
    if (rubber && playerProg != null) { const gap = (kart.total - playerProg) * tr.ds; rb = clamp(1 - gap / 900, 0.9, 1.08); }
    const curve = tr.turn[q.idx];
    const target = kart.stats.maxSpeed * this.skill * rb * (1 - clamp(curve * 0.55 - 0.08, 0, 0.5));
    const sp = kart.speed;
    const inp = { steer, throttle: sp < target ? 1 : 0.15, brake: sp > target + 7 ? 0.7 : 0, drift: false };
    if (curve > 0.55 && sp > 36 && this.skill > 0.9 && Math.abs(steer) > 0.45) { inp.drift = true; }
    if (sp < 2) { this.stuck += dt; if (this.stuck > 2.5) { kart.respawn(); this.stuck = 0; } } else this.stuck = 0;
    return inp;
  }
}
