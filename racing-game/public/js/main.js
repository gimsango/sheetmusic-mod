import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { Track, mapInfo, THEMES, MAP_COUNT, rng } from './track.js';
import { buildKart, decodeKart, encodeKart, kartStats, kartName, BODIES, PAINTS, WINGS, KART_COUNT, makeNameSprite } from './karts.js';
import { KartSim, BotBrain, wrapPi, clamp } from './physics.js';
import { Particles } from './fx.js';
import { Sound } from './audio.js';
import { Net } from './net.js';

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const ls = { get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} } };

// ================= 프로필 =================
const profile = { name: ls.get('tk.name', ''), kart: ls.get('tk.kart', Math.floor(Math.random() * KART_COUNT)), map: ls.get('tk.map', 1), laps: ls.get('tk.laps', 3), bots: ls.get('tk.bots', 7) };
const saveProfile = () => { ls.set('tk.name', profile.name); ls.set('tk.kart', profile.kart); ls.set('tk.map', profile.map); ls.set('tk.laps', profile.laps); ls.set('tk.bots', profile.bots); };
const myName = () => profile.name.trim() || '레이서' + (1 + (profile.kart % 99));

// ================= 렌더러 =================
const canvas = $('#c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const quality = { level: ls.get('tk.q', 2) }; // 0 낮음 1 중간 2 높음
const sound = new Sound();
const net = new Net();
const camera = new THREE.PerspectiveCamera(68, 1, 0.3, 6000);
let composer = null, bloom = null, renderPass = null;

function setupComposer(scene) {
  composer = new EffectComposer(renderer);
  renderPass = new RenderPass(scene, camera); composer.addPass(renderPass);
  bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.5, 0.65, 0.9); composer.addPass(bloom);
  composer.addPass(new OutputPass());
  resize();
}
function resize() {
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  if (composer) { composer.setSize(w, h); }
}
addEventListener('resize', resize);

// ================= 메뉴 프리뷰 씬 =================
const menu = { scene: new THREE.Scene(), kart: null, t: 0 };
{
  const s = menu.scene;
  s.add(new THREE.HemisphereLight(0xaac8ff, 0x1a1030, 1.2));
  const key = new THREE.DirectionalLight(0xffffff, 3.2); key.position.set(4, 6, 5); key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -6, right: 6, top: 6, bottom: -6, near: 1, far: 20 }); s.add(key);
  const rim = new THREE.DirectionalLight(0xff3d5a, 3); rim.position.set(-5, 3, -4); s.add(rim);
  const rim2 = new THREE.DirectionalLight(0x19e6ff, 2.2); rim2.position.set(5, 2, -5); s.add(rim2);
  const floor = new THREE.Mesh(new THREE.CylinderGeometry(3.4, 3.6, 0.25, 64), new THREE.MeshStandardMaterial({ color: 0x2a3454, metalness: 0.25, roughness: 0.55 }));
  floor.position.y = -0.13; floor.receiveShadow = true; s.add(floor);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(3.45, 0.06, 8, 96).rotateX(Math.PI / 2), new THREE.MeshBasicMaterial({ color: new THREE.Color(0x19e6ff).multiplyScalar(2.5), toneMapped: false }));
  s.add(ring);
}
function refreshMenuKart() {
  if (menu.kart) menu.scene.remove(menu.kart.root);
  menu.kart = buildKart(profile.kart);
  menu.kart.root.scale.setScalar(1.15); menu.scene.add(menu.kart.root);
}
function menuFrame(dt) {
  menu.t += dt;
  const k = menu.kart; if (!k) return;
  k.root.rotation.y = menu.t * 0.6;
  const garage = !$('#scGarage').classList.contains('off');
  const w = innerWidth, h = innerHeight, narrow = w < 760;
  camera.fov = 40; camera.aspect = w / h; camera.updateProjectionMatrix();
  const cx = garage && !narrow ? -1.7 : (!narrow ? -2.1 : 0);
  camera.position.set(cx + 0, garage ? 2.4 : 2.2, garage ? 8.6 : 8.4);
  if (garage && narrow) camera.position.set(0, 3.2, 8);
  camera.lookAt(cx, garage ? 0.6 : 1.0, 0);
  k.wheels.forEach((w2) => { w2.spin.rotation.x += dt * 3; });
  renderer.render(menu.scene, camera);
}

// ================= 화면 전환 =================
const screens = ['Main', 'Solo', 'Garage', 'Multi', 'Lobby', 'Help'];
function show(name) {
  screens.forEach((n) => $('#sc' + n).classList.toggle('off', n !== name));
  if (name === 'Garage') updateGarage();
  if (name === 'Main') $('#kartLabel').textContent = `내 카트 #${profile.kart + 1} · ${kartName(profile.kart)}`;
}
$$('[data-go]').forEach((b) => b.addEventListener('click', () => {
  sound.init();
  const g = b.dataset.go;
  if (g === 'main') { saveProfile(); show('Main'); }
  else if (g === 'solo') { show('Solo'); soloPicker.set(profile.map); }
  else if (g === 'garage') show('Garage');
  else if (g === 'multi') { $('#multiErr').textContent = ''; show('Multi'); }
  else if (g === 'help') show('Help');
}));

// ================= 스테퍼 =================
const vals = { soloLaps: profile.laps, soloBots: profile.bots, lobLaps: 3, lobBots: 0 };
const ranges = { soloLaps: [1, 10], soloBots: [0, 11], lobLaps: [1, 10], lobBots: [0, 11] };
function renderSteppers() { for (const k in vals) $('#' + k).textContent = vals[k]; }
$$('[data-step]').forEach((b) => b.addEventListener('click', () => {
  const [k, d] = b.dataset.step.split(':'); const [lo, hi] = ranges[k];
  vals[k] = clamp(vals[k] + Number(d), lo, hi); renderSteppers();
  if (k.startsWith('lob') && lobby.isHost) net.send({ t: 'settings', laps: vals.lobLaps, bots: vals.lobBots });
}));
renderSteppers();

// ================= 맵 선택기 =================
function drawOutline(cv, id) {
  const tr = new Track(id, true), c = cv.getContext('2d'), W = cv.width = 320, H = cv.height = 180;
  c.clearRect(0, 0, W, H);
  const b = tr.bounds, sx = (W - 30) / (b.maxX - b.minX), sz = (H - 30) / (b.maxZ - b.minZ), s = Math.min(sx, sz);
  const ox = (W - (b.maxX - b.minX) * s) / 2, oz = (H - (b.maxZ - b.minZ) * s) / 2;
  const P = (i) => [ox + (tr.px[i] - b.minX) * s, oz + (tr.pz[i] - b.minZ) * s];
  const th = THEMES[tr.info.theme];
  c.lineJoin = 'round'; c.lineCap = 'round';
  for (const [w, col] of [[9, 'rgba(0,0,0,.5)'], [6, '#' + th.wall[0].toString(16).padStart(6, '0')], [3.5, '#2b2f3a']]) {
    c.lineWidth = w; c.strokeStyle = col; c.beginPath();
    for (let i = 0; i <= tr.N; i++) { const [x, y] = P(i % tr.N); i ? c.lineTo(x, y) : c.moveTo(x, y); }
    c.stroke();
  }
  const [x0, y0] = P(0); c.fillStyle = '#fff'; c.beginPath(); c.arc(x0, y0, 5, 0, 7); c.fill();
  return Math.round(tr.length);
}
function makeMapPicker(el, onChange) {
  el.classList.add('mapPick');
  el.innerHTML = `<canvas></canvas><div class="name"></div><div class="sub"></div>
    <div class="nav"><button data-d="-10">«</button><button data-d="-1">‹</button><input type="number" min="1" max="${MAP_COUNT}"><button data-d="1">›</button><button data-d="10">»</button><button data-d="r">🎲</button></div>
    <div class="chips"></div>`;
  const cv = el.querySelector('canvas'), inp = el.querySelector('input'), chips = el.querySelector('.chips');
  THEMES.forEach((t, i) => { const b = document.createElement('button'); b.textContent = t.name; b.dataset.th = i; chips.appendChild(b); });
  let id = 1, timer = 0;
  const api = {
    set(v, emit = false) {
      id = ((Math.round(v) - 1 + MAP_COUNT) % MAP_COUNT) + 1; inp.value = id;
      const info = mapInfo(id); el.querySelector('.name').textContent = `#${id} ${info.name}`;
      clearTimeout(timer);
      timer = setTimeout(() => { const len = drawOutline(cv, id); el.querySelector('.sub').textContent = `${info.themeName} · 길이 ${(len / 1000).toFixed(2)} km`; }, 30);
      chips.querySelectorAll('button').forEach((b) => b.classList.toggle('on', Number(b.dataset.th) === info.theme));
      if (emit) onChange(id);
    },
    get: () => id,
    readonly(v) { el.classList.toggle('ro', v); },
  };
  el.querySelectorAll('.nav button').forEach((b) => b.addEventListener('click', () => api.set(b.dataset.d === 'r' ? 1 + Math.floor(Math.random() * MAP_COUNT) : id + Number(b.dataset.d), true)));
  inp.addEventListener('change', () => api.set(Number(inp.value) || 1, true));
  chips.addEventListener('click', (e) => { const t = e.target.dataset.th; if (t != null) api.set(Math.floor((id - 1) / 10) * 10 + Number(t) + 1, true); });
  return api;
}
const soloPicker = makeMapPicker($('#soloMap'), (id) => { profile.map = id; saveProfile(); });
const lobbyPicker = makeMapPicker($('#lobbyMap'), (id) => { if (lobby.isHost) net.send({ t: 'settings', map: id }); });

// ================= 차고 =================
function updateGarage() {
  const k = decodeKart(profile.kart);
  $('#pBody').textContent = BODIES[k.body].name; $('#pPaint').textContent = PAINTS[k.paint].name;
  $('#pWheel').textContent = `${['소', '중소', '중', '중대', '대'][k.wheel % 5]}형 ${['캡', '5스포크', '메쉬', '골드 링', '네온 링'][Math.floor(k.wheel / 5)]}`;
  $('#pWing').textContent = WINGS[k.wing].name;
  $('#kartNum').value = profile.kart + 1; $('#nameInput').value = profile.name;
  const st = kartStats(profile.kart);
  $('#stats').innerHTML = [['최고속도', st.speed], ['가속', st.accel], ['핸들링', st.handling], ['드리프트', st.drift]]
    .map(([n, v]) => `<div class="stat"><span>${n}</span><i style="--v:${v * 10}%"></i><b>${v.toFixed(1)}</b></div>`).join('');
  refreshMenuKart();
}
$$('[data-part]').forEach((b) => b.addEventListener('click', () => {
  const [p, d] = b.dataset.part.split(':'); const k = decodeKart(profile.kart), mod = { body: 20, paint: 20, wheel: 25, wing: 10 }[p];
  k[p] = (k[p] + Number(d) + mod) % mod; profile.kart = encodeKart(k); updateGarage(); saveProfile();
  if (net.connected) net.send({ t: 'profile', name: myName(), kart: profile.kart });
}));
$('#rndKart').addEventListener('click', () => { profile.kart = Math.floor(Math.random() * KART_COUNT); updateGarage(); saveProfile(); });
$('#kartNum').addEventListener('change', (e) => { profile.kart = clamp((Number(e.target.value) || 1) - 1, 0, KART_COUNT - 1) | 0; updateGarage(); saveProfile(); });
$('#nameInput').addEventListener('input', (e) => { profile.name = e.target.value; saveProfile(); });

// ================= 입력 =================
const keys = {}, touch = {};
addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  keys[e.code] = true; sound.init();
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) e.preventDefault();
  if (!race) return;
  if (e.code === 'KeyR') race.local && race.local.sim.respawn();
  if (e.code === 'KeyM') { sound.enabled = !sound.enabled; toast(sound.enabled ? '소리 켬' : '소리 끔'); if (!sound.enabled) sound.silence(); }
  if (e.code === 'KeyQ') cycleQuality();
  if (e.code === 'Escape') togglePause();
});
addEventListener('keyup', (e) => { keys[e.code] = false; });
if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
  $('#touch').classList.remove('hidden');
  $$('#touch button').forEach((b) => {
    const k = b.dataset.k, set = (v) => (e) => { e.preventDefault(); touch[k] = v; b.classList.toggle('hold', v); sound.init(); };
    b.addEventListener('touchstart', set(true), { passive: false }); b.addEventListener('touchend', set(false)); b.addEventListener('touchcancel', set(false));
    b.addEventListener('mousedown', set(true)); b.addEventListener('mouseup', set(false)); b.addEventListener('mouseleave', set(false));
  });
}
let steerSmooth = 0;
function readInput(dt) {
  let tgt = (keys.ArrowLeft || keys.KeyA || touch.left ? -1 : 0) + (keys.ArrowRight || keys.KeyD || touch.right ? 1 : 0);
  let throttle = keys.ArrowUp || keys.KeyW || touch.gas ? 1 : 0, brake = keys.ArrowDown || keys.KeyS || touch.brake ? 1 : 0;
  let drift = !!(keys.Space || keys.ShiftLeft || keys.ShiftRight || touch.drift);
  const gp = navigator.getGamepads ? navigator.getGamepads()[0] : null;
  if (gp) {
    const ax = gp.axes[0]; if (Math.abs(ax) > 0.12) tgt = ax;
    throttle = Math.max(throttle, gp.buttons[7] ? gp.buttons[7].value : 0, gp.buttons[0] && gp.buttons[0].pressed ? 1 : 0);
    brake = Math.max(brake, gp.buttons[6] ? gp.buttons[6].value : 0, gp.buttons[1] && gp.buttons[1].pressed ? 1 : 0);
    drift = drift || !!(gp.buttons[5] && gp.buttons[5].pressed) || !!(gp.buttons[2] && gp.buttons[2].pressed);
  }
  const rate = tgt === 0 ? 7 : 5.5;
  steerSmooth += (tgt - steerSmooth) * Math.min(1, dt * rate);
  return { steer: steerSmooth, throttle, brake, drift };
}

// ================= 레이스 =================
let race = null;
const particles = new Particles(800);
const fmtTime = (t) => { const m = Math.floor(t / 60), s = t - m * 60; return `${m}:${s.toFixed(2).padStart(5, '0')}`; };
function toast(msg, ms = 1200) { const t = $('#toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove('show'), ms); }
function bigMsg(txt) { const b = $('#bigMsg'); b.textContent = txt; b.classList.remove('pop'); void b.offsetWidth; b.classList.add('pop'); }

async function startRace(cfg) {
  // cfg: { mapId, laps, entries:[{id,name,kart,slot,kind:'local'|'bot'|'remote'}], multi, host, countdown }
  endRace(true);
  $('#loading').classList.remove('hidden'); $('#loadTxt').textContent = `#${cfg.mapId} 맵 생성 중…`;
  await new Promise((r) => setTimeout(r, 60));
  screens.forEach((n) => $('#sc' + n).classList.add('off')); $('#results').classList.add('hidden'); $('#pause').classList.add('hidden');
  const scene = new THREE.Scene(), track = new Track(cfg.mapId), th = track.theme;
  scene.add(track.group);
  scene.fog = new THREE.FogExp2(th.fog, th.fogD);
  scene.add(new THREE.HemisphereLight(th.hemi[0], th.hemi[1], th.hemi[2] * 1.5));
  const sun = new THREE.DirectionalLight(th.sun, th.sunI * 1.3); const sunDir = new THREE.Vector3(...th.sunDir).normalize();
  sun.castShadow = quality.level > 0; sun.shadow.mapSize.set(quality.level > 1 ? 2048 : 1024, quality.level > 1 ? 2048 : 1024);
  Object.assign(sun.shadow.camera, { left: -60, right: 60, top: 60, bottom: -60, near: 10, far: 400 }); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.06;
  scene.add(sun, sun.target);
  let head = null;
  if (th.night) { head = new THREE.SpotLight(0xfff0d0, 1500, 120, 0.5, 0.7, 1.4); scene.add(head, head.target); }
  scene.add(particles.points);
  const rand = rng(cfg.mapId * 31 + 7);
  race = { cfg, scene, track, sun, sunDir, head, karts: [], laps: cfg.laps, N: track.N, phase: 'count', t: 0, startAt: performance.now() + cfg.countdown, last: performance.now(),
    local: null, finishedList: [], sendT: 0, shake: 0, camH: 0, camInit: false, lastCount: 99, resultsShown: false, paused: false, fps: 60, slow: 0, over: false };
  for (const e of cfg.entries) {
    const vis = buildKart(e.kart); scene.add(vis.root);
    const k = { id: e.id, name: e.name, kind: e.kind, slot: e.slot, vis, kartId: e.kart, finished: false, finishTime: 0, total: -e.slot, speed: 0 };
    if (e.kind !== 'remote') { k.sim = new KartSim(track, e.kart, e.slot); k.total = k.sim.total; }
    if (e.kind === 'bot' || (e.kind === 'local' && window.__tkAuto)) k.brain = new BotBrain(rand);
    if (e.kind === 'local') race.local = k;
    else { k.label = makeNameSprite(e.name, e.kind === 'bot' ? '#ffd27a' : '#9fe8ff'); k.label.position.set(0, 2.6, 0); vis.root.add(k.label); }
    if (e.kind === 'remote') { const p = track.spawnPose(e.slot); k.cur = { x: p.x, y: track.pointAt(0).y, z: p.z, h: p.heading, sp: 0, total: p.prog, drift: 0, boost: 0 }; k.tgt = { ...k.cur }; }
    race.karts.push(k);
  }
  drawMini();
  $('#mapName').textContent = `#${cfg.mapId} ${track.info.name}`;
  $('#lapT').textContent = cfg.laps; $('#posT').textContent = race.karts.length;
  $('#hud').classList.remove('hidden');
  setupComposer(scene); applyQuality();
  $('#loading').classList.add('hidden'); $('#wrong').classList.add('hidden');
  $('#bigMsg').textContent = ''; steerSmooth = 0;
  sound.init();
}

function applyQuality() {
  if (!race) return;
  const q = quality.level;
  renderer.shadowMap.enabled = q > 0; race.sun.castShadow = q > 0;
  bloom.enabled = q > 1; renderer.setPixelRatio(q === 0 ? 1 : Math.min(devicePixelRatio, 2));
  resize();
}
function cycleQuality() { quality.level = (quality.level + 1) % 3; ls.set('tk.q', quality.level); toast(['그래픽: 낮음', '그래픽: 중간', '그래픽: 높음'][quality.level]); if (race) { race.sun.shadow.map && race.sun.shadow.map.dispose(); race.sun.shadow.map = null; applyQuality(); } }

function endRace(silent) {
  if (!race) return;
  race.track.dispose(); race.scene.traverse((o) => { if (o.geometry && o.isMesh && !o.userData.keep) { /* karts share cached geometry; skip dispose */ } });
  race = null; composer = null; sound.silence();
  $('#hud').classList.add('hidden'); $('#results').classList.add('hidden'); $('#pause').classList.add('hidden');
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  if (!silent) { show(net.connected && lobby.code ? 'Lobby' : 'Main'); refreshMenuKart(); }
}

function drawMini() {
  const t = race.track, cv = $('#mini'), c = cv.getContext('2d'), W = cv.width, b = t.bounds;
  const s = (W - 24) / Math.max(b.maxX - b.minX, b.maxZ - b.minZ), ox = (W - (b.maxX - b.minX) * s) / 2, oz = (W - (b.maxZ - b.minZ) * s) / 2;
  race.mini = { s, ox, oz, base: document.createElement('canvas') };
  const bc = race.mini.base; bc.width = bc.height = W; const g = bc.getContext('2d'); g.lineJoin = g.lineCap = 'round';
  for (const [w, col] of [[10, 'rgba(0,0,0,.6)'], [6, '#e9edf7']]) { g.lineWidth = w; g.strokeStyle = col; g.beginPath(); for (let i = 0; i <= t.N; i++) { const k = i % t.N; const x = ox + (t.px[k] - b.minX) * s, y = oz + (t.pz[k] - b.minZ) * s; i ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); }
}
function drawMiniDots() {
  const cv = $('#mini'), c = cv.getContext('2d'), m = race.mini, b = race.track.bounds;
  c.clearRect(0, 0, cv.width, cv.height); c.drawImage(m.base, 0, 0);
  for (const k of race.karts) {
    const p = kartPos(k), x = m.ox + (p.x - b.minX) * m.s, y = m.oz + (p.z - b.minZ) * m.s;
    c.fillStyle = k === race.local ? '#ffb020' : k.kind === 'bot' ? '#ff6a6a' : '#19e6ff'; c.beginPath(); c.arc(x, y, k === race.local ? 6 : 4, 0, 7); c.fill();
    if (k === race.local) { c.strokeStyle = '#fff'; c.lineWidth = 2; c.stroke(); }
  }
}
const kartPos = (k) => (k.sim ? k.sim : k.cur);

function ranking() {
  const list = race.karts.slice();
  const key = (k) => (k.finished ? 1e9 - k.finishTime : k.total);
  list.sort((a, b) => key(b) - key(a));
  return list;
}

function togglePause() {
  if (!race || race.phase === 'count' && false) return;
  if (race.cfg.multi) { toast('멀티플레이에서는 일시정지가 없습니다'); return; }
  race.paused = !race.paused; $('#pause').classList.toggle('hidden', !race.paused); if (race.paused) sound.silence();
  race.last = performance.now();
}
$('#pauseBtn').addEventListener('click', togglePause);
$('#pResume').addEventListener('click', togglePause);
$('#pRestart').addEventListener('click', () => { const c = race.cfg; startRace({ ...c, countdown: 4000 }); });
$('#pQuit').addEventListener('click', () => quitRace());
function quitRace() {
  const multi = race && race.cfg.multi;
  endRace(true);
  if (multi) { net.close(); lobby.code = null; }
  show('Main'); refreshMenuKart();
}

// ---- 시뮬레이션 한 프레임 ----
const STEP = 1 / 120;
function simulate(dt) {
  const R = race, now = performance.now();
  if (R.phase === 'count') {
    const left = (R.startAt - now) / 1000, n = Math.ceil(left);
    if (left <= 0) { R.phase = 'run'; R.t = 0; bigMsg('GO!'); sound.count(true); setTimeout(() => { if (race === R && R.phase === 'run') $('#bigMsg').textContent = ''; }, 900); }
    else if (n !== R.lastCount) { R.lastCount = n; if (n <= 3) { bigMsg(String(n)); sound.count(false); } else $('#bigMsg').textContent = ''; }
  } else R.t += dt;
  const running = R.phase === 'run';
  const all = R.karts.map((k) => kartPos(k));
  for (const k of R.karts) {
    if (k.kind === 'remote') continue;
    const sim = k.sim;
    const others = []; for (const o of R.karts) if (o !== k) { const p = kartPos(o); others.push({ x: p.x, z: p.z, vx: p.vx || 0, vz: p.vz || 0 }); }
    let inp;
    if (!running) inp = { steer: 0, throttle: 0, brake: 0, drift: false };
    else if (k.kind === 'local' && !k.finished) inp = window.__tkAuto && k.brain ? k.brain.drive(sim, dt, null, false) : readInput(dt);
    else inp = k.brain ? k.brain.drive(sim, dt, R.local ? R.local.total : null, !R.cfg.multi) : { steer: 0, throttle: 0, brake: 1, drift: false };
    if (k.kind === 'local' && k.finished && !k.brain) { k.brain = new BotBrain(rng(5)); }
    if (k.finished && k.kind === 'local') inp = k.brain.drive(sim, dt, null, false);
    if (!running) { sim.vx *= 0.9; sim.vz *= 0.9; }
    // 로컬 카트와 봇은 호스트/솔로에서만 시뮬레이션
    sim.update(dt, inp, others);
    k.total = sim.total; k.speed = sim.speed;
    if (!k.finished && sim.total >= R.laps * R.N && running) {
      k.finished = true; k.finishTime = R.t; sim.finished = true; R.finishedList.push(k);
      if (k.kind === 'local') { bigMsg('FINISH!'); sound.lap(); net.connected && R.cfg.multi && net.send({ t: 'fin', time: k.finishTime }); }
    }
    if (k.kind === 'local') handleLocalEvents(k);
  }
}
let lastLap = 1;
function handleLocalEvents(k) {
  for (const e of k.sim.events) {
    if (e === 'pad') { sound.boost(); toast('BOOST!', 600); race.shake = Math.max(race.shake, 0.5); }
    else if (e === 'miniturbo') { sound.boost(); race.shake = Math.max(race.shake, 0.4); }
    else if (e === 'wall' || e === 'bump') { sound.bump(); race.shake = Math.max(race.shake, 0.6); }
    else if (e.startsWith('tier')) sound.tier();
  }
  const lap = Math.min(race.laps, k.sim.lap);
  if (lap !== lastLap && race.phase === 'run') { if (lap > lastLap) { toast(lap === race.laps ? 'FINAL LAP!' : `LAP ${lap}`, 1500); sound.lap(); } lastLap = lap; }
}

// ---- 시각 갱신 ----
const _m = new THREE.Matrix4(), _x = new THREE.Vector3(), _y = new THREE.Vector3(), _z = new THREE.Vector3(), _q = new THREE.Quaternion(), _tmp = {};
function updateVisuals(dt) {
  const R = race, track = R.track;
  for (const k of R.karts) {
    const v = k.vis;
    let x, y, z, h, up, sp, drifting = false, dTier = 0, steer = 0, boost = false, slip = 0, off = false;
    if (k.sim) {
      const s = k.sim; x = s.x; y = s.y; z = s.z; h = s.heading; up = _y.set(s.upx, s.upy, s.upz).normalize(); sp = s.speed;
      drifting = s.drifting; dTier = s.driftTier; steer = s.steerVis; boost = s.boostT > 0; slip = s.slip; off = s.offroad;
      k.vx = s.vx; k.vz = s.vz;
    } else {
      const c = k.cur, t = k.tgt, f = 1 - Math.exp(-14 * dt);
      c.x += (t.x - c.x) * f; c.y += (t.y - c.y) * f; c.z += (t.z - c.z) * f; c.h += wrapPi(t.h - c.h) * f; c.sp += (t.sp - c.sp) * f; c.total += (t.total - c.total) * f;
      c.drift = t.drift; c.boost = t.boost; x = c.x; y = c.y; z = c.z; h = c.h; sp = c.sp; drifting = !!c.drift; dTier = c.drift; boost = !!c.boost;
      const idx = Math.round(((c.total % track.N) + track.N) % track.N); up = track.normalAt(idx, _y);
      k.total = c.total; k.speed = sp; k.vx = Math.sin(h) * sp; k.vz = Math.cos(h) * sp;
      steer = clamp(wrapPi(t.h - c.h) * -2, -1, 1); k.cur.vx = k.vx; k.cur.vz = k.vz;
    }
    if (k.label) { const dd = Math.hypot(camera.position.x - x, camera.position.z - z); k.label.visible = dd > 14 && dd < 130; }
    // 방향: z=앞, y=법선
    _z.set(Math.sin(h), 0, Math.cos(h)); _z.addScaledVector(up, -_z.dot(up)).normalize();
    _x.crossVectors(up, _z).normalize(); _m.makeBasis(_x, up, _z); v.root.quaternion.setFromRotationMatrix(_m);
    v.root.position.set(x, y, z);
    v.yaw.rotation.y += ((drifting ? -Math.sign(k.sim ? k.sim.driftDir : steer) * 0.32 : clamp(-slip * 0.02, -0.25, 0.25)) - v.yaw.rotation.y) * Math.min(1, dt * 9);
    v.chassis.rotation.z += ((steer * 0.07 + (drifting ? 0.05 * (k.sim ? k.sim.driftDir : 0) : 0)) - v.chassis.rotation.z) * Math.min(1, dt * 8);
    v.chassis.rotation.x = -clamp(sp / 90, 0, 1) * 0.025;
    for (const w of v.wheels) { w.spin.rotation.x += (sp / w.radius) * dt; if (w.front) w.pivot.rotation.y = -steer * 0.5; }
    v.flame.visible = boost; if (boost) { v.flame.scale.set(1, 1, 0.8 + Math.random() * 0.8); }
    // 이펙트
    if (sp > 3) {
      const fx = Math.sin(h), fz = Math.cos(h), rx = -fz, rz = fx, L = v.info.length;
      if (drifting) {
        const col = [0xaaccff, 0x33aaff, 0xff9a22, 0xd04aff][dTier] || 0xaaccff;
        for (const s of [-1, 1]) if (Math.random() < 0.8) particles.emit(x - fx * L * 0.4 + rx * s * v.info.width * 0.5, y + 0.25, z - fz * L * 0.4 + rz * s * v.info.width * 0.5,
          (Math.random() - 0.5) * 5 - fx * 3, 2 + Math.random() * 4, (Math.random() - 0.5) * 5 - fz * 3, col, 0.5 + dTier * 0.15, 0.35 + Math.random() * 0.25);
      }
      if (boost && Math.random() < 0.9) particles.emit(x - fx * (L * 0.5 + 0.5), y + 0.55, z - fz * (L * 0.5 + 0.5), -fx * 10 + (Math.random() - 0.5) * 2, Math.random() * 2, -fz * 10 + (Math.random() - 0.5) * 2, 0xff8a22, 0.9, 0.35);
      if (off && Math.random() < 0.6) particles.emit(x - fx * 1.2 + (Math.random() - 0.5) * 2, y + 0.2, z - fz * 1.2 + (Math.random() - 0.5) * 2, (Math.random() - 0.5) * 3, 1 + Math.random() * 2, (Math.random() - 0.5) * 3, R.track.theme.ground[0], 1.2, 0.6);
      if (k.sim && k.sim.wallHit > 0.6) for (let i = 0; i < 3; i++) particles.emit(x + rx * (k.sim.d > 0 ? 1.3 : -1.3), y + 0.6, z + rz * (k.sim.d > 0 ? 1.3 : -1.3), (Math.random() - 0.5) * 8, 2 + Math.random() * 5, (Math.random() - 0.5) * 8, 0xffd060, 0.45, 0.4);
    }
  }
}

function updateCamera(dt) {
  const R = race, k = R.local, s = k.sim, tr = R.track;
  const spR = clamp(s.speed / s.stats.maxSpeed, 0, 1.3);
  const targetH = s.heading + (s.drifting ? -s.driftDir * 0.2 : 0);
  if (!R.camInit) { R.camH = s.heading; R.camInit = true; R.camY = s.y; }
  R.camH += wrapPi(targetH - R.camH) * (1 - Math.exp(-5.5 * dt));
  R.camY += (s.y - R.camY) * (1 - Math.exp(-9 * dt));
  const dist = 7.4 + spR * 2.2 + (s.boostT > 0 ? 1.6 : 0), hgt = 3.1 + spR * 0.4;
  const fx = Math.sin(R.camH), fz = Math.cos(R.camH);
  const pos = _tmp.p || (_tmp.p = new THREE.Vector3());
  pos.set(s.x - fx * dist, R.camY + hgt, s.z - fz * dist);
  R.shake = Math.max(0, R.shake - dt * 2.2);
  const sh = R.shake * 0.18 + (s.boostT > 0 ? 0.04 : 0) + spR * 0.012;
  camera.position.set(pos.x + (Math.random() - 0.5) * sh, pos.y + (Math.random() - 0.5) * sh, pos.z + (Math.random() - 0.5) * sh);
  camera.up.set(0, 1, 0);
  camera.lookAt(s.x + fx * 7, R.camY + 1.4, s.z + fz * 7);
  const fov = 66 + spR * 12 + (s.boostT > 0 ? 9 : 0);
  camera.fov += (fov - camera.fov) * Math.min(1, dt * 5); camera.updateProjectionMatrix();
  // 그림자/헤드라이트/날씨
  R.sun.position.set(s.x + R.sunDir.x * 160, s.y + R.sunDir.y * 160, s.z + R.sunDir.z * 160); R.sun.target.position.set(s.x, s.y, s.z);
  if (R.head) { R.head.position.set(s.x, s.y + 1.4, s.z); R.head.target.position.set(s.x + Math.sin(s.heading) * 30, s.y, s.z + Math.cos(s.heading) * 30); }
  tr.weather.update(dt, camera.position);
}

function updateHUD() {
  const R = race, k = R.local, s = k.sim, rank = ranking(), pos = rank.indexOf(k) + 1;
  $('#posN').textContent = pos; $('#lapN').textContent = Math.min(R.laps, s.lap);
  $('#hudTime').textContent = fmtTime(Math.max(0, R.t));
  $('#spd').textContent = Math.round(s.speed * 3.6);
  $('#boostBar').style.width = Math.min(100, (s.boostT / 1.9) * 100) + '%';
  $('#driftBar').style.width = s.drifting ? Math.min(100, (s.driftCharge / 3.2) * 100) + '%' : '0%';
  $('#driftBar').style.background = ['#aaccff', '#33aaff', '#ff9a22', '#d04aff'][s.driftTier];
  $('#wrong').classList.toggle('hidden', !s.wrongWay || R.phase !== 'run' || k.finished);
  $('#board').innerHTML = rank.slice(0, 8).map((o, i) => `<div class="${o === k ? 'me' : ''}"><span>${i + 1}</span><span>${o.name}</span></div>`).join('');
  drawMiniDots();
}

function showResults() {
  const R = race; R.resultsShown = true;
  const rank = ranking();
  const fill = () => {
    $('#resList').innerHTML = ranking().map((o, i) => `<li class="${o === R.local ? 'me' : ''}"><b>${i + 1}</b><span>${o.name} <small style="color:#9aa6c4">${kartName(o.kartId)}</small></span><span>${o.finished ? fmtTime(o.finishTime) : '주행 중…'}</span></li>`).join('');
  };
  fill(); R.resFill = fill; $('#results').classList.remove('hidden');
  $('#resAgain').textContent = R.cfg.multi ? (lobby.isHost ? '로비로 돌아가기' : '방장 대기…') : '다시 달리기';
  $('#resAgain').disabled = R.cfg.multi && !lobby.isHost;
}

// ---- 네트워크 상태 송수신 ----
function netTick(dt) {
  const R = race; if (!R.cfg.multi || !net.connected) return;
  R.sendT += dt; if (R.sendT < 0.05) return; R.sendT = 0;
  const s = R.local.sim;
  net.send({ t: 's', x: +s.x.toFixed(2), y: +s.y.toFixed(2), z: +s.z.toFixed(2), h: +s.heading.toFixed(3), sp: +s.speed.toFixed(1), tp: +s.total.toFixed(2), dr: s.drifting ? s.driftTier + 1 : 0, bo: s.boostT > 0 ? 1 : 0, fin: R.local.finished ? 1 : 0 });
  if (R.cfg.host) {
    const bots = R.karts.filter((k) => k.kind === 'bot').map((k) => { const b = k.sim; return [k.id, +b.x.toFixed(2), +b.y.toFixed(2), +b.z.toFixed(2), +b.heading.toFixed(3), +b.speed.toFixed(1), +b.total.toFixed(2), b.drifting ? b.driftTier + 1 : 0, b.boostT > 0 ? 1 : 0, k.finished ? +k.finishTime.toFixed(2) : 0]; });
    if (bots.length) net.send({ t: 'b', b: bots });
  }
}
function applyRemote(id, f) {
  if (!race) return; const k = race.karts.find((o) => o.id === id); if (!k || !k.tgt) return;
  Object.assign(k.tgt, f);
  if (f.fin === 1 && !k.finished) { /* 'fin' 메시지로 처리 */ }
}
net.on('s', (m) => applyRemote(m.id, { x: m.x, y: m.y, z: m.z, h: m.h, sp: m.sp, total: m.tp, drift: m.dr, boost: m.bo }));
net.on('b', (m) => { for (const a of m.b) { applyRemote(a[0], { x: a[1], y: a[2], z: a[3], h: a[4], sp: a[5], total: a[6], drift: a[7], boost: a[8] }); const k = race && race.karts.find((o) => o.id === a[0]); if (k && a[9] && !k.finished) { k.finished = true; k.finishTime = a[9]; } } });
net.on('fin', (m) => { const k = race && race.karts.find((o) => o.id === m.id); if (k && !k.finished) { k.finished = true; k.finishTime = m.time; toast(`${k.name} 결승!`, 1200); } });
net.on('left', (m) => { if (!race) return; const i = race.karts.findIndex((o) => o.id === m.id); if (i >= 0) { race.scene.remove(race.karts[i].vis.root); toast(`${race.karts[i].name} 퇴장`); race.karts.splice(i, 1); } });
net.on('chat', () => {});

// ---- 메인 루프 ----
let acc = 0;
function frame(nowMs) {
  requestAnimationFrame(frame);
  const R = race;
  if (!R) { const dt = Math.min(0.05, (nowMs - (frame.last || nowMs)) / 1000); frame.last = nowMs; menuFrame(dt); return; }
  const dtRaw = Math.min(0.1, (nowMs - R.last) / 1000) * (window.__tkTS || 1); R.last = nowMs; frame.last = nowMs;
  if (R.paused) { composer.render(); return; }
  // 성능 자동 조절
  R.fps += (1 / Math.max(dtRaw, 1e-3) - R.fps) * 0.05;
  if (R.fps < 28 && quality.level > 0 && !window.__tkNoAdapt) { R.slow += dtRaw; if (R.slow > 3) { quality.level--; R.slow = 0; applyQuality(); toast('프레임 향상을 위해 그래픽 품질을 낮췄어요'); } } else R.slow = 0;
  acc += dtRaw;
  while (acc >= STEP) { simulate(STEP); acc -= STEP; }
  netTick(dtRaw);
  updateVisuals(dtRaw);
  particles.update(dtRaw, innerHeight);
  updateCamera(dtRaw);
  updateHUD();
  const s = R.local.sim;
  sound.engine(clamp(s.speed / s.stats.maxSpeed, 0, 1.3), R.phase === 'run' && (keys.ArrowUp || keys.KeyW || touch.gas) ? 1 : 0.2, s.drifting, s.offroad, s.boostT > 0);
  // 결과 화면
  if (R.local.finished && !R.resultsShown && R.t - R.local.finishTime > 2.2) showResults();
  if (R.resultsShown) { R.resT = (R.resT || 0) + dtRaw; if (R.resT > 0.5) { R.resT = 0; R.resFill(); } }
  composer.render();
}
requestAnimationFrame(frame);

// ================= 솔로 시작 =================
$('#soloStart').addEventListener('click', () => {
  profile.map = soloPicker.get(); profile.laps = vals.soloLaps; profile.bots = vals.soloBots; saveProfile();
  startSolo();
});
function startSolo() {
  const rnd = rng((Date.now() >>> 0));
  const bots = vals.soloBots, entries = [], slotMe = Math.floor(bots * 0.6);
  let s = 0;
  for (let i = 0; i <= bots; i++) {
    if (i === slotMe) entries.push({ id: 'me', name: myName(), kart: profile.kart, slot: i, kind: 'local' });
    else entries.push({ id: 'b' + i, name: 'BOT ' + (++s), kart: Math.floor(rnd() * KART_COUNT), slot: i, kind: 'bot' });
  }
  lastLap = 1;
  startRace({ mapId: profile.map, laps: vals.soloLaps, entries, multi: false, host: true, countdown: 5000 });
}
$('#resAgain').addEventListener('click', () => {
  if (!race) return;
  if (race.cfg.multi) { if (lobby.isHost) net.send({ t: 'lobby' }); }
  else startSolo();
});
$('#resMenu').addEventListener('click', quitRace);

// ================= 멀티플레이 로비 =================
const lobby = { code: null, isHost: false, players: [], host: null };
async function connectNet() {
  try { await net.connect(); } catch (e) { $('#multiErr').textContent = '서버에 연결할 수 없습니다. 서버가 켜져 있는지 확인하세요.'; return false; }
  net.on('close', () => { if (lobby.code) { lobby.code = null; toast('서버와 연결이 끊어졌습니다', 2500); if (race) quitRace(); else show('Main'); } });
  return true;
}
$('#mkRoom').addEventListener('click', async () => { sound.init(); if (await connectNet()) net.send({ t: 'create', name: myName(), kart: profile.kart }); });
$('#joinRoom').addEventListener('click', async () => {
  sound.init(); const code = $('#joinCode').value.trim().toUpperCase(); if (code.length !== 4) { $('#multiErr').textContent = '4자리 방 코드를 입력하세요.'; return; }
  if (await connectNet()) net.send({ t: 'join', code, name: myName(), kart: profile.kart });
});
net.on('error', (m) => { $('#multiErr').textContent = m.msg; });
net.on('room', (m) => {
  lobby.code = m.code; lobby.host = m.host; lobby.players = m.players; lobby.isHost = m.host === net.id;
  $('#roomCode').textContent = m.code;
  if (!race && $('#scLobby').classList.contains('off')) { show('Lobby'); refreshMenuKart(); fetch('/info').then((r) => r.json()).then((j) => { $('#lanInfo').innerHTML = `같은 WiFi 친구들은 브라우저에서 <b>${j.addresses.join(' 또는 ') || location.host}</b> 으로 접속 후 방 코드 <b>${m.code}</b> 입력`; }).catch(() => {}); }
  $('#plist').innerHTML = m.players.map((p) => `<li class="${p.id === m.host ? 'host' : ''}"><span>${p.name}${p.id === net.id ? ' (나)' : ''}</span><small>${kartName(p.kart)}</small></li>`).join('');
  vals.lobLaps = m.laps; vals.lobBots = m.bots; renderSteppers(); lobbyPicker.set(m.map);
  lobbyPicker.readonly(!lobby.isHost);
  $$('#lobbySettings .stepper button').forEach((b) => { b.disabled = !lobby.isHost; });
  $('#startMulti').classList.toggle('hidden', !lobby.isHost); $('#waitHost').textContent = lobby.isHost ? '' : '방장이 시작하기를 기다리는 중…';
});
$('#startMulti').addEventListener('click', () => net.send({ t: 'start' }));
$('#leaveRoom').addEventListener('click', () => { net.close(); lobby.code = null; show('Main'); });
net.on('start', (m) => {
  lastLap = 1;
  const entries = [];
  for (const p of m.players) entries.push({ id: p.id, name: p.name, kart: p.kart, slot: p.slot, kind: p.id === net.id ? 'local' : 'remote' });
  const isHost = lobby.host === net.id;
  for (const b of m.bots) entries.push({ id: b.id, name: b.name, kart: b.kart, slot: b.slot, kind: isHost ? 'bot' : 'remote' });
  startRace({ mapId: m.map, laps: m.laps, entries, multi: true, host: isHost, countdown: m.countdown });
});
net.on('tolobby', () => { endRace(true); show('Lobby'); refreshMenuKart(); });

// ================= 시작 =================
show('Main'); refreshMenuKart(); resize();
// 디버그/자동 테스트용 훅
window.__tk = { startSolo: (map = 1, bots = 5, laps = 2) => { vals.soloBots = bots; vals.soloLaps = laps; profile.map = map; startSolo(); }, get race() { return race; }, keys, profile };
