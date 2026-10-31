// 카트 10만 종: 차체(20) x 페인트(20) x 휠(25) x 윙(10) = 100,000
import * as THREE from 'three';

export const KART_COUNT = 100000;

// [이름, 길이, 폭, 높이, 노즈 길이, 캐노피(0없음/1버블/2루프), 스탯: 속도, 가속, 핸들링, 드리프트]
export const BODIES = [
  ['스트리트 래퍼', 2.6, 1.5, 0.5, 0.6, 1, 6, 5, 6, 5], ['불독', 2.4, 1.8, 0.62, 0.3, 2, 5, 6, 5, 7], ['니들', 3.2, 1.3, 0.42, 1.2, 1, 8, 4, 4, 5],
  ['버블 팝', 2.2, 1.7, 0.7, 0.2, 1, 4, 7, 8, 6], ['웨지', 3.0, 1.6, 0.4, 1.0, 0, 7, 5, 5, 6], ['탱크 미니', 2.5, 2.0, 0.75, 0.2, 2, 4, 6, 4, 8],
  ['레이저', 3.1, 1.4, 0.44, 1.1, 1, 9, 3, 4, 4], ['머슬', 2.9, 1.8, 0.58, 0.7, 2, 7, 6, 3, 6], ['스카우트', 2.4, 1.4, 0.55, 0.5, 0, 5, 7, 7, 6],
  ['포뮬러 제로', 3.3, 1.5, 0.36, 1.4, 0, 8, 5, 6, 3], ['클래식 롱', 3.1, 1.5, 0.6, 0.9, 1, 6, 5, 5, 6], ['점프 큐브', 2.0, 1.7, 0.8, 0.1, 2, 4, 8, 7, 7],
  ['스톰', 2.8, 1.7, 0.5, 0.8, 1, 7, 6, 5, 5], ['돌핀', 2.7, 1.5, 0.48, 0.9, 1, 6, 6, 7, 5], ['헤비 듀티', 2.8, 2.0, 0.7, 0.4, 2, 5, 4, 5, 8],
  ['고스트', 3.0, 1.45, 0.4, 1.0, 1, 8, 5, 5, 5], ['핫로드', 2.9, 1.6, 0.55, 1.0, 0, 7, 7, 4, 6], ['펄스', 2.5, 1.55, 0.5, 0.6, 1, 6, 6, 6, 6],
  ['타이탄', 3.0, 1.9, 0.66, 0.6, 2, 8, 3, 3, 8], ['콤팩트 X', 2.1, 1.4, 0.55, 0.3, 1, 5, 8, 8, 5],
].map((a) => ({ name: a[0], len: a[1], wid: a[2], hei: a[3], nose: a[4], canopy: a[5], spd: a[6], acc: a[7], han: a[8], dft: a[9] }));

// [이름, 메인색, 보조색, 금속질감, 패턴(0단색/1레이싱 스트라이프/2투톤)]
export const PAINTS = [
  ['레이싱 레드', 0xd8232a, 0xffffff, 0.3, 1], ['코발트 블루', 0x1f5fd6, 0xffd23a, 0.4, 1], ['라임 그린', 0x58c418, 0x111111, 0.2, 2], ['선셋 오렌지', 0xff7a1a, 0x1b1b1b, 0.3, 1],
  ['로열 퍼플', 0x7a3cd6, 0xff6adf, 0.5, 2], ['핑크 팝', 0xff5fa8, 0xffffff, 0.2, 0], ['미드나잇 블랙', 0x15161c, 0xff2a2a, 0.8, 1], ['펄 화이트', 0xf2f4f8, 0x2a6fd6, 0.5, 1],
  ['골드', 0xe0b020, 0x222222, 1.0, 0], ['크롬 실버', 0xc4cad4, 0x2a2f3a, 1.0, 2], ['터콰이즈', 0x10b8b0, 0xffffff, 0.5, 2], ['버건디', 0x7a1230, 0xf0c060, 0.6, 1],
  ['옐로 택시', 0xffd400, 0x111111, 0.2, 2], ['아이스 블루', 0x7ad4ff, 0xffffff, 0.6, 1], ['포레스트', 0x1f6b35, 0xe8d8a0, 0.2, 2], ['네온 마젠타', 0xff1fd0, 0x19e6ff, 0.4, 1],
  ['건메탈', 0x4a5160, 0xff7a1a, 0.9, 1], ['민트', 0x7af0c0, 0x1b1b1b, 0.3, 0], ['코랄', 0xff6b5a, 0xfff2d0, 0.3, 2], ['사이버 옐로', 0xd6ff1a, 0x7a1fff, 0.5, 1],
].map((a) => ({ name: a[0], main: a[1], accent: a[2], metal: a[3], pattern: a[4] }));

const WHEEL_R = [0.34, 0.38, 0.42, 0.46, 0.5];
const WHEEL_W = [0.3, 0.36, 0.42, 0.48, 0.54];
const RIM_NAMES = ['캡', '5스포크', '메쉬', '골드 링', '네온 링'];
export const WINGS = [
  ['없음', 0, 1, 0], ['립 스포일러', 0, 0, 1], ['하이 윙', 1, -1, 0], ['트윈 플레인', 1, -1, 1], ['사이드 핀', 0, 1, 0],
  ['GT 윙', 1, 0, 1], ['덕테일', 0, 0, 0], ['루프 스쿠프', 1, 0, -1], ['제트 부스터', 2, -1, -1], ['로켓 팩', 2, -2, 0],
].map((a) => ({ name: a[0], spd: a[1], acc: a[2], han: a[3] }));

export function decodeKart(id) {
  id = ((id | 0) % KART_COUNT + KART_COUNT) % KART_COUNT;
  return { id, body: id % 20, paint: Math.floor(id / 20) % 20, wheel: Math.floor(id / 400) % 25, wing: Math.floor(id / 10000) % 10 };
}
export const encodeKart = (k) => k.body + 20 * k.paint + 400 * k.wheel + 10000 * k.wing;

export function kartName(id) {
  const k = decodeKart(id);
  return `${PAINTS[k.paint].name} ${BODIES[k.body].name}`;
}

// 1~10 스케일 스탯 + 실제 물리 파라미터
export function kartStats(id) {
  const k = decodeKart(id), b = BODIES[k.body], w = WINGS[k.wing], size = k.wheel % 5, rim = Math.floor(k.wheel / 5);
  const clamp = (v) => Math.max(1, Math.min(10, v));
  const speed = clamp(b.spd + w.spd + (size - 2) * 0.5 + (rim === 3 ? 0.3 : 0));
  const accel = clamp(b.acc + w.acc - (size - 2) * 0.5);
  const handling = clamp(b.han + w.han - (size - 2) * 0.2 + (rim === 2 ? 0.4 : 0));
  const drift = clamp(b.dft + (rim === 4 ? 0.8 : 0) + (size >= 3 ? 0.4 : 0) - (rim === 1 ? 0.2 : 0));
  return {
    speed, accel, handling, drift,
    maxSpeed: 52 + speed * 3.0, accelRate: 15 + accel * 1.7, turnRate: 1.5 + handling * 0.11, driftGrip: 4.2 - drift * 0.18,
  };
}

let _glowTex = null;
function glowTex() {
  if (_glowTex) return _glowTex;
  const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d');
  const g = x.createRadialGradient(32, 32, 0, 32, 32, 32); g.addColorStop(0, 'rgba(255,255,255,.9)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g; x.fillRect(0, 0, 64, 64); _glowTex = new THREE.CanvasTexture(c); return _glowTex;
}
const geoCache = new Map();
const cached = (key, fn) => { if (!geoCache.has(key)) geoCache.set(key, fn()); return geoCache.get(key); };
const matCache = new Map();
const stdMat = (key, opts) => { if (!matCache.has(key)) matCache.set(key, new THREE.MeshStandardMaterial(opts)); return matCache.get(key); };

function add(parent, geo, mat, x = 0, y = 0, z = 0, cast = true) {
  const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = cast; parent.add(m); return m;
}

function buildWheel(k, p, rimMats) {
  const size = k.wheel % 5, rim = Math.floor(k.wheel / 5), R = WHEEL_R[size], W = WHEEL_W[size];
  const g = new THREE.Group(), spin = new THREE.Group(); g.add(spin);
  const tire = cached(`tire${size}`, () => new THREE.CylinderGeometry(R, R, W, 20).rotateZ(Math.PI / 2));
  add(spin, tire, stdMat('tire', { color: 0x15161a, roughness: 0.95 }));
  const face = W / 2 + 0.005;
  const rimMat = rim === 3 ? stdMat('gold', { color: 0xe0b020, metalness: 1, roughness: 0.25 }) : rim === 4 ? rimMats.glow : rimMats.accent;
  if (rim === 0) {
    const d = cached(`disc${size}`, () => new THREE.CylinderGeometry(R * 0.68, R * 0.68, W + 0.02, 18).rotateZ(Math.PI / 2));
    add(spin, d, rimMat, 0, 0, 0, false);
  } else if (rim === 1 || rim === 2) {
    const n = rim === 1 ? 5 : 8;
    const ring = cached(`ring${size}`, () => new THREE.TorusGeometry(R * 0.66, R * 0.07, 6, 18).rotateY(Math.PI / 2));
    const spoke = cached(`spoke${size}${n}`, () => new THREE.BoxGeometry(W + 0.03, R * 0.1, R * 0.62).translate(0, 0, R * 0.32));
    for (const s of [-1, 1]) add(spin, ring, rimMat, s * face, 0, 0, false);
    for (let i = 0; i < n; i++) { const sp = add(spin, spoke, rimMat, 0, 0, 0, false); sp.rotation.x = (i / n) * Math.PI * 2; }
  } else if (rim === 3) {
    const ring = cached(`gring${size}`, () => new THREE.TorusGeometry(R * 0.6, R * 0.1, 8, 20).rotateY(Math.PI / 2));
    for (const s of [-1, 1]) add(spin, ring, rimMat, s * face, 0, 0, false);
    add(spin, cached(`ghub${size}`, () => new THREE.CylinderGeometry(R * 0.5, R * 0.5, W + 0.02, 14).rotateZ(Math.PI / 2)), stdMat('chromeDark', { color: 0x30343c, metalness: 0.9, roughness: 0.3 }), 0, 0, 0, false);
  } else {
    const ring = cached(`nring${size}`, () => new THREE.TorusGeometry(R * 0.62, R * 0.1, 8, 24).rotateY(Math.PI / 2));
    for (const s of [-1, 1]) add(spin, ring, rimMat, s * face, 0, 0, false);
    add(spin, cached(`nhub${size}`, () => new THREE.CylinderGeometry(R * 0.55, R * 0.55, W + 0.01, 14).rotateZ(Math.PI / 2)), stdMat('hubdark', { color: 0x101218, roughness: 0.6 }), 0, 0, 0, false);
  }
  return { group: g, spin, radius: R, width: W };
}

function buildWing(k, p, mats, g, b) {
  const bz = -b.len / 2, top = b.hei + 0.38;
  const dark = stdMat('wdark', { color: 0x1c1e26, roughness: 0.5, metalness: 0.4 });
  const box = (w, h, d) => cached(`box${w},${h},${d}`, () => new THREE.BoxGeometry(w, h, d));
  const bodyW = b.wid;
  switch (k.wing) {
    case 1: add(g, box(bodyW * 0.9, 0.06, 0.4), mats.main, 0, top - 0.05, bz + 0.1); break;
    case 2: for (const s of [-1, 1]) add(g, box(0.07, 0.55, 0.12), dark, s * bodyW * 0.3, top + 0.25, bz + 0.1);
      add(g, box(bodyW * 1.05, 0.07, 0.55), mats.main, 0, top + 0.55, bz); break;
    case 3: for (const s of [-1, 1]) add(g, box(0.07, 0.6, 0.12), dark, s * bodyW * 0.32, top + 0.28, bz + 0.1);
      add(g, box(bodyW * 1.05, 0.06, 0.45), mats.main, 0, top + 0.4, bz); add(g, box(bodyW * 1.05, 0.06, 0.45), mats.accent, 0, top + 0.68, bz - 0.12); break;
    case 4: for (const s of [-1, 1]) { const f = add(g, box(0.05, 0.5, 0.9), mats.accent, s * (bodyW / 2 + 0.02), top - 0.1, bz + 0.3); f.rotation.x = -0.25; } break;
    case 5: add(g, box(bodyW * 1.2, 0.08, 0.6), mats.accent, 0, top + 0.5, bz - 0.1);
      for (const s of [-1, 1]) { add(g, box(0.07, 0.55, 0.12), dark, s * bodyW * 0.25, top + 0.25, bz + 0.05); add(g, box(0.06, 0.28, 0.7), mats.main, s * bodyW * 0.6, top + 0.5, bz - 0.1); } break;
    case 6: { const m = add(g, box(bodyW * 0.8, 0.07, 0.55), mats.main, 0, top - 0.02, bz + 0.05); m.rotation.x = 0.3; break; }
    case 7: add(g, cached('scoop', () => new THREE.ConeGeometry(0.2, 0.5, 8).rotateX(Math.PI / 2)), dark, 0, top + 0.1, -0.1); break;
    case 8: for (const s of [-1, 1]) { const c = add(g, cached('jet', () => new THREE.CylinderGeometry(0.2, 0.26, 0.9, 12).rotateX(Math.PI / 2)), dark, s * 0.35, b.hei * 0.6 + 0.3, bz - 0.2);
      add(g, cached('jetf', () => new THREE.CylinderGeometry(0.15, 0.15, 0.05, 12).rotateX(Math.PI / 2)), mats.glow, s * 0.35, b.hei * 0.6 + 0.3, bz - 0.68, false); } break;
    case 9: add(g, cached('rocket', () => new THREE.CapsuleGeometry(0.28, 1.0, 4, 10).rotateX(Math.PI / 2)), mats.accent, 0, b.hei + 0.55, bz - 0.1);
      add(g, cached('rocketf', () => new THREE.ConeGeometry(0.22, 0.5, 10).rotateX(-Math.PI / 2)), mats.glow, 0, b.hei + 0.55, bz - 0.95, false);
      for (const s of [-1, 1]) add(g, box(0.5, 0.05, 0.4), dark, s * 0.4, b.hei + 0.55, bz - 0.2); break;
  }
}

export function buildKart(id, opts = {}) {
  const k = decodeKart(id), b = BODIES[k.body], p = PAINTS[k.paint];
  const root = new THREE.Group(), yaw = new THREE.Group(), chassis = new THREE.Group();
  root.add(yaw); yaw.add(chassis);
  const mats = {
    main: stdMat(`main${k.paint}`, { color: p.main, metalness: p.metal * 0.85, roughness: 0.55 - p.metal * 0.3 }),
    accent: stdMat(`acc${k.paint}`, { color: p.accent, metalness: p.metal * 0.6, roughness: 0.45 }),
    glow: stdMat(`glow${k.paint}`, { color: 0x111111, emissive: p.accent, emissiveIntensity: 2.2 }),
  };
  const dark = stdMat('chdark', { color: 0x1a1c22, roughness: 0.6, metalness: 0.5 });
  const L = b.len, W = b.wid, H = b.hei, wheelZ = L * 0.34, wheelR = WHEEL_R[k.wheel % 5];
  const base = wheelR * 0.75; // 차체 바닥 높이
  const body = new THREE.Group(); body.position.y = base; chassis.add(body);
  const box = (w, h, d) => cached(`kb${w.toFixed(2)},${h.toFixed(2)},${d.toFixed(2)}`, () => new THREE.BoxGeometry(w, h, d));
  // 메인 섀시 + 노즈(쐐기) + 사이드 포드
  add(body, box(W, H * 0.7, L), mats.main, 0, H * 0.35, 0);
  const noseGeo = cached(`nose${b.nose}${W}${H}`, () => {
    const g = new THREE.CylinderGeometry(W * 0.12, W * 0.45, Math.max(0.2, b.nose + 0.5), 4, 1).rotateX(Math.PI / 2).rotateY(Math.PI / 4);
    g.scale(1, (H * 0.55) / (W * 0.45 * 1.0), 1); return g;
  });
  const nose = add(body, noseGeo, mats.main, 0, H * 0.28, L / 2 + b.nose * 0.3); nose.scale.set(1.5, 1, 1);
  if (p.pattern === 2) nose.material = mats.accent;
  if (p.pattern === 1) { add(body, box(W * 0.16, 0.02, L + b.nose * 0.9), mats.accent, 0, H * 0.71, b.nose * 0.3, false); }
  if (p.pattern === 2) add(body, box(W * 1.02, H * 0.16, L * 0.4), mats.accent, 0, H * 0.3, -L * 0.2, false);
  for (const s of [-1, 1]) add(body, box(W * 0.2, H * 0.55, L * 0.5), mats.accent, s * (W / 2 + 0.08), H * 0.3, -L * 0.05);
  // 앞 범퍼 / 라이트
  add(body, box(W * 0.95, H * 0.14, 0.2), dark, 0, H * 0.12, L / 2 + b.nose * 0.55 + 0.05);
  for (const s of [-1, 1]) add(body, box(0.22, 0.12, 0.08), stdMat('light', { color: 0xfff6d0, emissive: 0xfff0b0, emissiveIntensity: 3 }), s * W * 0.32, H * 0.42, L / 2 + 0.03, false);
  // 캐노피 / 운전석
  const seatZ = -L * 0.08;
  if (b.canopy === 1) {
    const dome = add(body, cached('dome', () => new THREE.SphereGeometry(0.55, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2)), stdMat('glass', { color: 0x9fd8ff, metalness: 0.9, roughness: 0.05, transparent: true, opacity: 0.45 }), 0, H * 0.7, seatZ, false);
    dome.scale.set(W * 0.75, 1, 1.2);
  } else if (b.canopy === 2) {
    add(body, box(W * 0.7, 0.34, L * 0.38), mats.main, 0, H * 0.7 + 0.17, seatZ - 0.15);
    add(body, box(W * 0.62, 0.2, 0.05), stdMat('glass2', { color: 0x203040, metalness: 0.9, roughness: 0.1 }), 0, H * 0.7 + 0.2, seatZ + L * 0.19 + 0.02, false);
  }
  // 드라이버
  const driver = new THREE.Group(); driver.position.set(0, H * 0.7, seatZ); body.add(driver);
  add(driver, cached('torso', () => new THREE.CapsuleGeometry(0.22, 0.25, 4, 8)), stdMat(`suit${k.paint}`, { color: p.accent, roughness: 0.7 }), 0, 0.28, 0);
  add(driver, cached('helmet', () => new THREE.SphereGeometry(0.26, 14, 12)), stdMat(`helm${k.paint}`, { color: p.main, metalness: 0.5, roughness: 0.25 }), 0, 0.68, 0.02);
  add(driver, box(0.34, 0.1, 0.12), stdMat('visor', { color: 0x0a0a0a, metalness: 1, roughness: 0.05 }), 0, 0.68, 0.22, false);
  // 핸들
  add(body, cached('wheelring', () => new THREE.TorusGeometry(0.14, 0.03, 6, 14)), dark, 0, H * 0.78, seatZ + 0.38, false).rotation.x = -0.9;
  // 배기구 + 윙
  for (const s of [-1, 1]) add(body, cached('pipe', () => new THREE.CylinderGeometry(0.07, 0.09, 0.4, 8).rotateX(Math.PI / 2)), stdMat('pipe', { color: 0x9aa0aa, metalness: 1, roughness: 0.2 }), s * W * 0.25, H * 0.25, -L / 2 - 0.1, false);
  buildWing(k, p, mats, body, b);
  // 언더글로우
  const glowPlane = add(chassis, cached('under', () => new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2)), new THREE.MeshBasicMaterial({ color: new THREE.Color(p.accent), map: glowTex(), transparent: true, opacity: 0.55, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }), 0, 0.06, 0, false);
  glowPlane.scale.set(W * 2.2, 1, L * 1.9);
  // 바퀴 4개
  const wheels = [];
  for (const [sx, sz, front] of [[-1, 1, true], [1, 1, true], [-1, -1, false], [1, -1, false]]) {
    const w = buildWheel(k, p, mats), pivot = new THREE.Group();
    pivot.position.set(sx * (W / 2 + w.width * 0.35), wheelR, sz * wheelZ); pivot.add(w.group);
    if (sx > 0) w.group.rotation.y = Math.PI; // 바깥쪽 림이 바깥으로 보이게
    chassis.add(pivot); wheels.push({ pivot, spin: w.spin, front, radius: wheelR, side: sx });
  }
  // 부스트 불꽃
  const flame = new THREE.Mesh(new THREE.ConeGeometry(0.18, 1.1, 10).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffa040).multiplyScalar(2.5), transparent: true, opacity: 0.9, toneMapped: false, depthWrite: false }));
  flame.position.set(0, H * 0.3 + base, -L / 2 - 0.65); flame.visible = false; chassis.add(flame);
  root.traverse((o) => { if (o.isMesh && o.castShadow) o.receiveShadow = false; });
  return { root, yaw, chassis, wheels, flame, driver, info: { ...k, bodyDef: b, paint: p, length: L, width: W, wheelRadius: wheelR } };
}

export function makeNameSprite(text, color = '#ffffff') {
  const c = document.createElement('canvas'); c.width = 256; c.height = 64;
  const x = c.getContext('2d'); x.font = 'bold 34px sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.lineWidth = 7; x.strokeStyle = 'rgba(0,0,0,0.75)'; x.strokeText(text, 128, 34); x.fillStyle = color; x.fillText(text, 128, 34);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthTest: false, transparent: true, fog: false }));
  s.scale.set(3.6, 0.9, 1); s.renderOrder = 10; return s;
}
