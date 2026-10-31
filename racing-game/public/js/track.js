// 절차적 트랙 생성: 맵 번호(1~1000) -> 고유한 코스/테마/배경
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export const MAP_COUNT = 1000;

export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const hash = (n) => { let h = (n + 1) * 2654435761 >>> 0; h ^= h >>> 15; h = Math.imul(h, 2246822519) >>> 0; h ^= h >>> 13; return h >>> 0; };

const ADJ = ['고요한', '질주하는', '폭풍의', '황금빛', '아득한', '불꽃', '은빛', '안개 낀', '번개', '전설의', '비밀',
  '끝없는', '반짝이는', '거친', '미지의', '새벽', '한밤', '정오의', '붉은', '푸른', '야생', '얼어붙은', '뜨거운', '꿈꾸는', '마지막'];

export const THEMES = [
  { key: 'forest', name: '숲', nouns: ['삼림 서킷', '계곡', '숲길', '피크닉 힐', '오솔길', '호숫가', '캠프 루트', '이끼 협곡'],
    skyTop: 0x2f7fd0, skyBot: 0xcfe6f5, fog: 0xbad4e8, fogD: 0.0012, ground: [0x3f7a35, 0x4f8f3f], far: 0x3a6b30, road: 0x3b3d42,
    wall: [0xdd2e2e, 0xf2f2f2], sun: 0xfff1d0, sunI: 2.6, sunDir: [0.5, 0.8, 0.3], hemi: [0xa8c8ff, 0x4a6b3a, 0.9],
    props: [['pine', 6], ['roundtree', 3], ['bush', 2], ['rock', 1]], weather: null, elev: 26, clouds: 1 },
  { key: 'desert', name: '사막', nouns: ['모래 폭풍길', '오아시스', '피라미드 로드', '선인장 계곡', '대상 루트', '낙타 고개', '신기루 서킷', '황금 사구'],
    skyTop: 0x3d86d6, skyBot: 0xf6e2b8, fog: 0xeed9b0, fogD: 0.0014, ground: [0xd9b36b, 0xc99f55], far: 0xd2aa62, road: 0x4a4743,
    wall: [0xc2552b, 0xf0e2c8], sun: 0xffe3b0, sunI: 2.9, sunDir: [0.4, 0.9, 0.2], hemi: [0xbfd8ff, 0xb08a4a, 0.9],
    props: [['cactus', 5], ['rock', 4], ['bush', 1]], weather: null, elev: 20, clouds: 0.3, rockColor: [0xb98c52, 0xa57a44] },
  { key: 'snow', name: '설원', nouns: ['빙하 서킷', '스키 슬로프', '오로라 길', '눈보라 고개', '얼음 호수', '설산 루트', '펭귄 마을', '크리스탈 동굴'],
    skyTop: 0x7aa6d6, skyBot: 0xe8f1fa, fog: 0xdfeaf5, fogD: 0.0022, ground: [0xf2f6fa, 0xdde7f0], far: 0xe6eef6, road: 0x44484f,
    wall: [0x2a6fd6, 0xf2f2f2], sun: 0xe6f0ff, sunI: 2.0, sunDir: [0.3, 0.6, 0.5], hemi: [0xc8dcff, 0xe8f0ff, 1.0],
    props: [['pine', 7], ['rock', 2]], snowy: true, weather: 'snow', elev: 28, clouds: 1.2, rockColor: [0xdfe6ee, 0xc8d2de] },
  { key: 'neon', name: '네온 시티', nouns: ['다운타운', '사이버 하이웨이', '루프탑 서킷', '야간 순환로', '네온 스트리트', '메가시티', '홀로그램 거리', '항구 야경'],
    skyTop: 0x05061a, skyBot: 0x2a0f4a, fog: 0x120a30, fogD: 0.0022, ground: [0x0b0b1c, 0x12122a], far: 0x08081a, road: 0x15151f,
    wall: [0xff2bd6, 0x19e6ff], glowWall: true, sun: 0x8fa8ff, sunI: 0.7, sunDir: [-0.4, 0.7, 0.5], hemi: [0x5566cc, 0x20104a, 1.0],
    props: [['building', 8], ['crystal', 1]], night: true, lamps: true, arches: 0xff2bd6, weather: null, elev: 14, clouds: 0 },
  { key: 'volcano', name: '화산', nouns: ['용암 서킷', '화염 협곡', '재의 평원', '마그마 터널', '불의 고개', '분화구 로드', '유황 계곡', '드래곤 둥지'],
    skyTop: 0x230b0b, skyBot: 0xb3401c, fog: 0x4a1a10, fogD: 0.0022, ground: [0x2a2220, 0x3a2a24], far: 0x8a2a0c, road: 0x2b2a2c,
    wall: [0xff5a1a, 0x222222], glowWall: true, sun: 0xff9a60, sunI: 1.8, sunDir: [0.5, 0.5, 0.2], hemi: [0xff8050, 0x3a1a10, 0.9],
    props: [['rock', 6], ['crystal', 3]], lava: true, weather: 'ember', elev: 30, clouds: 0, rockColor: [0x3a3030, 0x2a2222] },
  { key: 'tropic', name: '열대 해변', nouns: ['야자수 해안', '산호 만', '서핑 비치', '리조트 로드', '등대 섬', '파라다이스', '해적 항구', '석양 부두'],
    skyTop: 0x1e90e8, skyBot: 0xbfefff, fog: 0xbfe8f0, fogD: 0.0010, ground: [0xe8d49a, 0xf0dca8], far: 0x1aa6c4, road: 0x3f4147,
    wall: [0x00b7c9, 0xffffff], sun: 0xfff4d6, sunI: 3.0, sunDir: [0.3, 0.85, 0.4], hemi: [0xb8e4ff, 0xe8d49a, 1.0],
    props: [['palm', 7], ['bush', 2], ['rock', 1]], weather: null, elev: 12, clouds: 1, rockColor: [0xcbb88a, 0xb8a47a] },
  { key: 'autumn', name: '단풍', nouns: ['단풍길', '낙엽 고개', '수확 농장', '사과 과수원', '안개 마을', '호박 밭', '고성 언덕', '황금 들판'],
    skyTop: 0x5b8fcf, skyBot: 0xf5d9b0, fog: 0xe8cfa8, fogD: 0.0015, ground: [0x8a6a2f, 0x9b5d22], far: 0x7a5a28, road: 0x3d3a3a,
    wall: [0xb5451b, 0xf0e0c0], sun: 0xffd9a0, sunI: 2.4, sunDir: [0.6, 0.55, 0.2], hemi: [0xffe0b0, 0x7a4a20, 0.9],
    props: [['roundtree', 8], ['pine', 1], ['rock', 1]], autumn: true, weather: 'leaf', elev: 24, clouds: 1, rockColor: [0x8a7a68, 0x75675a] },
  { key: 'candy', name: '캔디 월드', nouns: ['사탕 왕국', '초코 강', '젤리 언덕', '마시멜로 길', '쿠키 서킷', '아이스크림 산', '솜사탕 하늘', '마카롱 파크'],
    skyTop: 0xff9bd8, skyBot: 0xfff0fa, fog: 0xffd7f0, fogD: 0.0016, ground: [0xffc2e6, 0xbdf0ff], far: 0xffb3dd, road: 0x5b4b7a,
    wall: [0xff5fa8, 0xffffff], sun: 0xfff0ff, sunI: 2.6, sunDir: [0.4, 0.8, 0.3], hemi: [0xffe0ff, 0xbde0ff, 1.1],
    props: [['lollipop', 7], ['icecream', 3]], arches: 0xff5fa8, weather: 'sprinkle', elev: 18, clouds: 1.5 },
  { key: 'space', name: '우주 기지', nouns: ['달 기지', '궤도 링', '운석 지대', '화성 기지', '은하 서킷', '위성 항로', '성운 고속도', '블랙홀 가장자리'],
    skyTop: 0x000008, skyBot: 0x0a0a22, fog: 0x05050f, fogD: 0.0009, ground: [0x8c8c94, 0x777780], far: 0x55555c, road: 0x2d2f36,
    wall: [0x19e6ff, 0xffffff], glowWall: true, sun: 0xffffff, sunI: 3.0, sunDir: [-0.6, 0.35, 0.4], hemi: [0x223355, 0x111118, 0.7],
    props: [['rock', 5], ['crystal', 3]], night: true, planet: true, arches: 0x19e6ff, weather: null, elev: 30, clouds: 0, rockColor: [0x8a8a92, 0x6a6a72] },
  { key: 'canyon', name: '석양 협곡', nouns: ['레드락 서킷', '메사 고원', '그랜드 캐년', '카우보이 길', '붉은 아치', '독수리 절벽', '황야 질주', '노을 루트'],
    skyTop: 0x2b3a7a, skyBot: 0xff9a4a, fog: 0xe0875a, fogD: 0.0016, ground: [0xb8532f, 0xa04426], far: 0x8a3a20, road: 0x3a3433,
    wall: [0xf0c040, 0x333333], sun: 0xff8a3a, sunI: 2.6, sunDir: [0.8, 0.28, 0.2], hemi: [0xffb080, 0x8a3a20, 0.9],
    props: [['mesa', 6], ['cactus', 2], ['rock', 2]], weather: null, elev: 34, clouds: 0.5, rockColor: [0xb04a28, 0x9a3f20] },
];

export function mapInfo(id) {
  id = Math.min(MAP_COUNT, Math.max(1, id | 0));
  const n = id - 1, ti = n % 10, variant = Math.floor(n / 10), seed = hash(n * 7919 + 13);
  const th = THEMES[ti], r = rng(seed ^ 0x9e3779b9);
  const name = `${ADJ[Math.floor(r() * ADJ.length)]} ${th.nouns[Math.floor(r() * th.nouns.length)]}`;
  return { id, seed, theme: ti, variant, name, themeName: th.name };
}

// ---------- 텍스처 ----------
function canvasTex(w, h, draw, repeat = true) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  if (repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 8;
  return t;
}
const hex = (n) => '#' + n.toString(16).padStart(6, '0');
let _dot = null;
export function dotTex() {
  if (_dot) return _dot;
  const c = document.createElement('canvas'); c.width = c.height = 32; const x = c.getContext('2d');
  const g = x.createRadialGradient(16, 16, 0, 16, 16, 16); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.6, 'rgba(255,255,255,.9)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g; x.fillRect(0, 0, 32, 32); _dot = new THREE.CanvasTexture(c); return _dot;
}
function noise(ctx, w, h, count, alpha, size = 2) {
  for (let i = 0; i < count; i++) {
    ctx.fillStyle = Math.random() < 0.5 ? `rgba(255,255,255,${alpha})` : `rgba(0,0,0,${alpha})`;
    ctx.fillRect(Math.random() * w, Math.random() * h, size, size);
  }
}

// ---------- 지오메트리 도우미 ----------
function part(geo, color, x = 0, y = 0, z = 0, sx = 1, sy = 1, sz = 1, rx = 0, ry = 0, rz = 0) {
  const g = geo.index ? geo.toNonIndexed() : geo;
  g.applyMatrix4(new THREE.Matrix4().compose(new THREE.Vector3(x, y, z),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), new THREE.Vector3(sx, sy, sz)));
  const c = new THREE.Color(color), n = g.attributes.position.count, arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { arr[i * 3] = c.r; arr[i * 3 + 1] = c.g; arr[i * 3 + 2] = c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(arr, 3));
  if (!g.attributes.uv) g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(n * 2), 2));
  return g;
}
const merge = (list) => mergeGeometries(list, false);
const CYL = (a, b, h, s = 7) => new THREE.CylinderGeometry(a, b, h, s);
const CONE = (r, h, s = 7) => new THREE.ConeGeometry(r, h, s);
const ICO = (r, d = 0) => new THREE.IcosahedronGeometry(r, d);
const BOX = (x = 1, y = 1, z = 1) => new THREE.BoxGeometry(x, y, z);
const SPH = (r) => new THREE.SphereGeometry(r, 10, 8);

// 장식물 정의: parts = [{ geo, glow }]  (glow=true 이면 발광 재질)
function propParts(kind, th) {
  const rc = th.rockColor || [0x7d7f84, 0x6a6c70];
  switch (kind) {
    case 'pine': {
      const s = th.snowy;
      return [{ geo: merge([part(CYL(0.35, 0.5, 3, 6), 0x5a3b22, 0, 1.5, 0),
        part(CONE(3.4, 5), s ? 0x4f7f66 : 0x1f6b35, 0, 5), part(CONE(2.7, 4.6), s ? 0x6d9a84 : 0x2a7d3f, 0, 7.6),
        part(CONE(1.9, 4), s ? 0xf2f7fb : 0x35914a, 0, 10)]) }];
    }
    case 'roundtree': {
      const cols = th.autumn ? [0xd9541e, 0xe8a317, 0xb83a1a, 0xf0c030] : [0x3a8c3a, 0x4aa04a, 0x2f7f35];
      const c = cols[Math.floor(Math.random() * cols.length)];
      return [{ geo: merge([part(CYL(0.45, 0.65, 4, 6), 0x5a3b22, 0, 2, 0), part(ICO(3.4, 1), c, 0, 6.5, 0, 1, 0.9, 1),
        part(ICO(2.2, 1), c, 1.6, 5.3, 0.8)]) }];
    }
    case 'bush': return [{ geo: merge([part(ICO(1.6, 1), 0x2f7f35, 0, 0.8, 0, 1.2, 0.7, 1.1), part(ICO(1.1, 1), 0x3a8c3a, 1.3, 0.5, 0.5)]) }];
    case 'cactus': return [{ geo: merge([part(CYL(0.7, 0.8, 6, 8), 0x3b8a4a, 0, 3, 0), part(CYL(0.4, 0.4, 1.4, 6), 0x3b8a4a, 1.0, 2.4, 0, 1, 1, 1, 0, 0, Math.PI / 2),
      part(CYL(0.4, 0.4, 2.4, 6), 0x3b8a4a, 1.7, 3.5, 0), part(CYL(0.4, 0.4, 1.2, 6), 0x3b8a4a, -0.9, 3.6, 0, 1, 1, 1, 0, 0, Math.PI / 2),
      part(CYL(0.4, 0.4, 1.8, 6), 0x3b8a4a, -1.5, 4.4, 0)]) }];
    case 'rock': return [{ geo: merge([part(ICO(2.2, 0), rc[0], 0, 0.9, 0, 1.3, 0.9, 1.1), part(ICO(1.3, 0), rc[1], 2.3, 0.5, 0.7)]) }];
    case 'mesa': return [{ geo: merge([part(CYL(7, 9, 12, 7), 0xb04a28, 0, 6, 0), part(CYL(6.2, 7, 6, 7), 0xc7653a, 0, 15, 0),
      part(CYL(5.4, 6.2, 5, 7), 0xa84424, 0, 20.5, 0), part(CYL(5.6, 5.6, 1.2, 7), 0xe0a060, 0, 23.6, 0)]) }];
    case 'palm': {
      const leaves = [];
      for (let k = 0; k < 7; k++) leaves.push(part(BOX(4.5, 0.12, 1.3), k % 2 ? 0x2f8f3a : 0x3aa046, Math.cos(k * 0.898) * 2, 8.6, Math.sin(k * 0.898) * 2, 1, 1, 1, 0, -k * 0.898, -0.45));
      return [{ geo: merge([part(CYL(0.28, 0.5, 8.4, 6), 0x8a6a40, 0.3, 4.2, 0, 1, 1, 1, 0, 0, -0.06), ...leaves, part(SPH(0.45), 0x5a3b22, 0.2, 8.2, 0.3)]) }];
    }
    case 'building': return [
      { geo: merge([part(BOX(1, 1, 1), 0x161628, 0, 0.5, 0)]) },
      { geo: merge([part(BOX(1.02, 0.012, 1.02), 0xff2bd6, 0, 0.9, 0), part(BOX(1.02, 0.012, 1.02), 0x19e6ff, 0, 0.62, 0),
        part(BOX(1.02, 0.012, 1.02), 0xffe14a, 0, 0.34, 0), part(BOX(1.02, 0.01, 1.02), 0xff2bd6, 0, 1.0, 0)]), glow: 2.4 }];
    case 'crystal': {
      const col = th.lava ? 0xff7a1a : th.key === 'space' ? 0x19e6ff : 0xff2bd6;
      return [{ geo: merge([part(new THREE.OctahedronGeometry(1.2), col, 0, 3, 0, 1, 2.6, 1), part(new THREE.OctahedronGeometry(0.8), col, 1.6, 1.8, 0.4, 1, 2.2, 1, 0, 0, 0.3)]), glow: 1.8 }];
    }
    case 'lollipop': return [{ geo: merge([part(CYL(0.16, 0.16, 5.2, 6), 0xffffff, 0, 2.6, 0), part(CYL(2.2, 2.2, 0.6, 14), 0xffffff, 0, 6.2, 0, 1, 1, 1, Math.PI / 2, 0, 0),
      part(CYL(1.2, 1.2, 0.7, 14), 0xff77aa, 0, 6.2, 0, 1, 1, 1, Math.PI / 2, 0, 0)]), tint: true }];
    case 'icecream': return [{ geo: merge([part(CONE(1.4, 3.6, 8), 0xe0a96a, 0, 1.8, 0, 1, 1, 1, Math.PI, 0, 0), part(SPH(1.7), 0xff9ec4, 0, 4.3, 0),
      part(SPH(0.4), 0xdd2233, 0, 6.1, 0)]), tint: true }];
  }
  return [];
}

function skyDome(th, rand) {
  const g = new THREE.Group();
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { top: { value: new THREE.Color(th.skyTop) }, bot: { value: new THREE.Color(th.skyBot) } },
    vertexShader: 'varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
    fragmentShader: 'uniform vec3 top; uniform vec3 bot; varying vec3 vP; void main(){ float h = clamp(vP.y*1.6+0.12,0.0,1.0); gl_FragColor = vec4(mix(bot, top, pow(h,0.7)),1.0);\n#include <colorspace_fragment>\n}',
  });
  const dome = new THREE.Mesh(new THREE.SphereGeometry(4000, 24, 16), mat); dome.renderOrder = -10; g.add(dome);
  const dir = new THREE.Vector3(...th.sunDir).normalize();
  const sun = new THREE.Mesh(new THREE.SphereGeometry(th.night ? 120 : 160, 24, 16),
    new THREE.MeshBasicMaterial({ color: new THREE.Color(th.sun).multiplyScalar(th.night ? 1.4 : 2.2), fog: false, toneMapped: false }));
  sun.position.copy(dir).multiplyScalar(3400); g.add(sun);
  if (th.night) {
    const n = 1800, pos = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const u = rand() * 2 * Math.PI, v = Math.acos(rand() * 0.95 + 0.05), r = 3800;
      pos[i * 3] = r * Math.sin(v) * Math.cos(u); pos[i * 3 + 1] = r * Math.cos(v); pos[i * 3 + 2] = r * Math.sin(v) * Math.sin(u);
    }
    const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.add(new THREE.Points(sg, new THREE.PointsMaterial({ color: 0xffffff, size: 4.5, map: dotTex(), alphaTest: 0.1, sizeAttenuation: false, fog: false, transparent: true, opacity: 0.95, depthWrite: false })));
  }
  if (th.planet) {
    const p = new THREE.Mesh(new THREE.SphereGeometry(520, 32, 20), new THREE.MeshStandardMaterial({ color: 0x3a6fd0, roughness: 1, fog: false, emissive: 0x0a1a40 }));
    p.position.set(-1800, 1500, -2600); g.add(p);
    const ring = new THREE.Mesh(new THREE.RingGeometry(700, 980, 64), new THREE.MeshBasicMaterial({ color: 0xc8b890, side: THREE.DoubleSide, transparent: true, opacity: 0.55, fog: false }));
    ring.position.copy(p.position); ring.rotation.set(1.2, 0.2, 0.3); g.add(ring);
  }
  if (th.clouds > 0) {
    const cm = new THREE.MeshBasicMaterial({ color: th.key === 'candy' ? 0xfff0fa : 0xffffff, transparent: true, opacity: 0.85, fog: false, depthWrite: false });
    const count = Math.round(26 * th.clouds), im = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 10, 8), cm, count * 4), m = new THREE.Matrix4();
    let k = 0;
    for (let i = 0; i < count; i++) {
      const a = rand() * 6.283, d = 900 + rand() * 2200, y = 380 + rand() * 450, s = 80 + rand() * 120;
      for (let j = 0; j < 4; j++) {
        m.compose(new THREE.Vector3(Math.cos(a) * d + (j - 1.5) * s * 0.9, y + (j % 2) * 10, Math.sin(a) * d),
          new THREE.Quaternion(), new THREE.Vector3(s * (0.8 + rand() * 0.5), s * 0.34, s * 0.7));
        im.setMatrixAt(k++, m);
      }
    }
    g.add(im);
  }
  return g;
}

export class Weather {
  constructor(type, th) {
    this.type = type; if (!type) return;
    const n = type === 'snow' ? 1800 : 900;
    this.n = n; this.pos = new Float32Array(n * 3); this.ph = new Float32Array(n);
    for (let i = 0; i < n; i++) { this.pos[i * 3] = (Math.random() - 0.5) * 160; this.pos[i * 3 + 1] = Math.random() * 70; this.pos[i * 3 + 2] = (Math.random() - 0.5) * 160; this.ph[i] = Math.random() * 6.28; }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(this.pos.slice(), 3));
    this.g = g;
    const color = { snow: 0xffffff, ember: 0xff8a2a, leaf: 0xd9541e, sprinkle: 0xff77cc }[type];
    this.points = new THREE.Points(g, new THREE.PointsMaterial({ color, size: type === 'snow' ? 0.32 : 0.4, map: dotTex(), alphaTest: 0.05, transparent: true, opacity: 0.9, depthWrite: false, blending: type === 'ember' ? THREE.AdditiveBlending : THREE.NormalBlending }));
    this.points.frustumCulled = false;
    this.t = 0;
  }
  update(dt, cam) {
    if (!this.type) return;
    this.t += dt;
    const out = this.g.attributes.position.array, vy = this.type === 'ember' ? 2.5 : -3.2;
    for (let i = 0; i < this.n; i++) {
      this.pos[i * 3 + 1] += vy * dt * (0.6 + (i % 5) * 0.2);
      this.pos[i * 3] += Math.sin(this.t + this.ph[i]) * dt * 1.2;
      if (this.pos[i * 3 + 1] < 0) this.pos[i * 3 + 1] += 70; if (this.pos[i * 3 + 1] > 70) this.pos[i * 3 + 1] -= 70;
      out[i * 3] = ((this.pos[i * 3] - cam.x + 80) % 160 + 160) % 160 - 80 + cam.x;
      out[i * 3 + 1] = this.pos[i * 3 + 1] + cam.y - 25;
      out[i * 3 + 2] = ((this.pos[i * 3 + 2] - cam.z + 80) % 160 + 160) % 160 - 80 + cam.z;
    }
    this.g.attributes.position.needsUpdate = true;
  }
}

const UP = new THREE.Vector3(0, 1, 0);
function basisQuat(T, up) {
  const z = T.clone().normalize(), x = new THREE.Vector3().crossVectors(up, z).normalize(), y = new THREE.Vector3().crossVectors(z, x);
  return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z));
}

export class Track {
  constructor(mapId, outlineOnly = false) {
    this.info = mapInfo(mapId);
    const th = this.theme = THEMES[this.info.theme];
    const r = rng(this.info.seed);
    this.rand = r;
    this.width = 15 + Math.floor(r() * 5); this.hw = this.width / 2; this.SH = 12;
    this.wallOff = this.hw + this.SH - 0.6;
    this.rows = [{ off: this.hw, dy: 0 }, { off: this.hw + 0.7, dy: -0.14 }, { off: this.hw + this.SH, dy: -0.25 }, { off: this.hw + this.SH + 14, dy: -1.2 },
      { off: this.hw + this.SH + 60, dy: -6 }, { off: this.hw + this.SH + 160, dy: -34 }, { off: this.hw + this.SH + 260, dy: -80 }];
    this.makeCenterline(r);
    if (outlineOnly) return;
    this.group = new THREE.Group();
    this.buildMeshes(r);
    this.weather = new Weather(th.weather, th);
    if (this.weather.points) this.group.add(this.weather.points);
  }

  makeCenterline(r) {
    const th = this.theme;
    const K = 7 + Math.floor(r() * 8), R = 240 + r() * 240, amp = 0.16 + r() * 0.24, aspect = 1 + r() * 0.8, rot = r() * 6.283;
    const ph = [r() * 6.28, r() * 6.28, r() * 6.28], elev = th.elev * (0.35 + r() * 0.65);
    const pts = [];
    for (let i = 0; i < K; i++) {
      const a = ((i + (r() - 0.5) * 0.55) / K) * Math.PI * 2, rad = R * (1 + (r() * 2 - 1) * amp);
      const x = Math.cos(a) * rad * aspect, z = Math.sin(a) * rad, t = a / (Math.PI * 2);
      const y = elev * (Math.sin(Math.PI * 2 * t + ph[0]) * 0.6 + Math.sin(Math.PI * 4 * t + ph[1]) * 0.3 + Math.sin(Math.PI * 6 * t + ph[2]) * 0.18);
      pts.push(new THREE.Vector3(x * Math.cos(rot) - z * Math.sin(rot), y, x * Math.sin(rot) + z * Math.cos(rot)));
    }
    const curve = new THREE.CatmullRomCurve3(pts, true, 'centripetal');
    const N0 = Math.max(220, Math.round(curve.getLength() / 4));
    let sp = curve.getSpacedPoints(N0).slice(0, N0);
    // 가장 곧은 구간을 출발선으로
    const N = N0, tang = (i) => { i = ((i % N) + N) % N; const a = sp[(i - 1 + N) % N], b = sp[(i + 1) % N]; return new THREE.Vector3(b.x - a.x, 0, b.z - a.z).normalize(); };
    let bestI = 0, bestS = 1e9;
    for (let i = 0; i < N; i += 2) {
      const t0 = tang(i - 6), t1 = tang(i + 6), s = 1 - t0.dot(t1);
      if (s < bestS) { bestS = s; bestI = i; }
    }
    sp = sp.slice(bestI).concat(sp.slice(0, bestI));
    this.N = N;
    const A = (n) => new Float32Array(n);
    this.px = A(N); this.py = A(N); this.pz = A(N); this.tx = A(N); this.ty = A(N); this.tz = A(N);
    this.rx = A(N); this.rz = A(N); this.bank = A(N); this.turn = A(N);
    for (let i = 0; i < N; i++) { this.px[i] = sp[i].x; this.py[i] = sp[i].y; this.pz[i] = sp[i].z; }
    let len = 0;
    for (let i = 0; i < N; i++) {
      const a = (i - 1 + N) % N, b = (i + 1) % N;
      let dx = this.px[b] - this.px[a], dy = this.py[b] - this.py[a], dz = this.pz[b] - this.pz[a];
      const l = Math.hypot(dx, dy, dz); dx /= l; dy /= l; dz /= l;
      this.tx[i] = dx; this.ty[i] = dy; this.tz[i] = dz;
      const h = Math.hypot(dx, dz); this.rx[i] = -dz / h; this.rz[i] = dx / h; // right = T x up
      len += Math.hypot(this.px[b] - this.px[i], this.py[b] - this.py[i], this.pz[b] - this.pz[i]);
    }
    this.length = len; this.ds = len / N;
    // 뱅킹(곡률)
    const cur = A(N);
    for (let i = 0; i < N; i++) {
      const b = (i + 3) % N, a = (i - 3 + N) % N;
      // cross(Ta, Tb).y = tz_a*tx_b - tx_a*tz_b ... (y comp of a x b = az*bx - ax*bz)
      cur[i] = (this.tz[a] * this.tx[b] - this.tx[a] * this.tz[b]);
    }
    for (let i = 0; i < N; i++) {
      let s = 0; for (let k = -10; k <= 10; k++) s += cur[(i + k + N) % N];
      this.bank[i] = Math.max(-0.2, Math.min(0.2, (-s / 21) * 2.4));
    }
    // 앞으로 보이는 커브 강도 (AI 속도 제어용)
    for (let i = 0; i < N; i++) {
      let m = 0;
      for (let k = 4; k <= 34; k += 3) { const j = (i + k) % N; m = Math.max(m, Math.acos(Math.min(1, this.tx[i] * this.tx[j] + this.tz[i] * this.tz[j]))); }
      this.turn[i] = m;
    }
    let minY = 1e9, minX = 1e9, maxX = -1e9, minZ = 1e9, maxZ = -1e9;
    for (let i = 0; i < N; i++) { minY = Math.min(minY, this.py[i]); minX = Math.min(minX, this.px[i]); maxX = Math.max(maxX, this.px[i]); minZ = Math.min(minZ, this.pz[i]); maxZ = Math.max(maxZ, this.pz[i]); }
    this.minY = minY; this.bounds = { minX, maxX, minZ, maxZ };
  }

  dyAt(off) {
    off = Math.abs(off);
    const rows = this.rows;
    if (off <= rows[0].off) return 0;
    for (let i = 1; i < rows.length; i++) if (off <= rows[i].off) { const a = rows[i - 1], b = rows[i], t = (off - a.off) / (b.off - a.off); return a.dy + (b.dy - a.dy) * t; }
    return rows[rows.length - 1].dy;
  }

  // 위치 질의: hint 근처 구간에서 가장 가까운 점 -> {idx,t,d,y,...}
  query(x, z, hint, o) {
    const N = this.N, px = this.px, pz = this.pz;
    let best = 0, bd = 1e18;
    if (hint < 0) { for (let i = 0; i < N; i++) { const d = (px[i] - x) ** 2 + (pz[i] - z) ** 2; if (d < bd) { bd = d; best = i; } } }
    else { for (let k = -16; k <= 16; k++) { const i = (hint + k + N) % N, d = (px[i] - x) ** 2 + (pz[i] - z) ** 2; if (d < bd) { bd = d; best = i; } } }
    let a = best, b = (best + 1) % N;
    let ex = px[b] - px[a], ez = pz[b] - pz[a];
    let t = ((x - px[a]) * ex + (z - pz[a]) * ez) / (ex * ex + ez * ez);
    if (t < 0) { a = (best - 1 + N) % N; b = best; ex = px[b] - px[a]; ez = pz[b] - pz[a]; t = ((x - px[a]) * ex + (z - pz[a]) * ez) / (ex * ex + ez * ez); }
    t = Math.max(0, Math.min(1, t));
    const L = (arr) => arr[a] + (arr[b] - arr[a]) * t;
    const cx = L(px), cz = L(pz), cy = L(this.py);
    let rx = L(this.rx), rz = L(this.rz); const rl = Math.hypot(rx, rz); rx /= rl; rz /= rl;
    let tx = L(this.tx), tz = L(this.tz); const tl = Math.hypot(tx, tz); tx /= tl; tz /= tl;
    const bank = L(this.bank), d = (x - cx) * rx + (z - cz) * rz, hw = this.hw;
    o.idx = a; o.t = t; o.prog = a + t; o.d = d; o.rx = rx; o.rz = rz; o.tx = tx; o.tz = tz; o.ty = L(this.ty); o.bank = bank;
    o.cx = cx; o.cz = cz; o.cy = cy;
    o.y = cy - Math.sin(bank) * Math.max(-hw, Math.min(hw, d)) + this.dyAt(d);
    return o;
  }

  // 트랙 위의 점 (중심선 + 옆 오프셋)
  pointAt(i, d = 0, out = new THREE.Vector3()) {
    i = ((i % this.N) + this.N) % this.N;
    return out.set(this.px[i] + this.rx[i] * d, this.py[i] - Math.sin(this.bank[i]) * Math.max(-this.hw, Math.min(this.hw, d)), this.pz[i] + this.rz[i] * d);
  }
  normalAt(i, out = new THREE.Vector3()) {
    i = ((i % this.N) + this.N) % this.N;
    const cb = Math.cos(this.bank[i]), sb = Math.sin(this.bank[i]);
    const rb = new THREE.Vector3(this.rx[i] * cb, -sb, this.rz[i] * cb), T = new THREE.Vector3(this.tx[i], this.ty[i], this.tz[i]);
    return out.crossVectors(rb, T).normalize();
  }
  tangentAt(i, out = new THREE.Vector3()) { i = ((i % this.N) + this.N) % this.N; return out.set(this.tx[i], this.ty[i], this.tz[i]); }

  ribbon(rows, side, uvFn, closed = true) {
    const N = this.N, R = rows.length, pos = new Float32Array((N + 1) * R * 3), uv = new Float32Array((N + 1) * R * 2), idx = [];
    let dist = 0;
    for (let i = 0; i <= N; i++) {
      const k = i % N;
      if (i > 0) dist += this.ds;
      for (let j = 0; j < R; j++) {
        const o = rows[j].off * side, p = (i * R + j);
        pos[p * 3] = this.px[k] + this.rx[k] * o;
        pos[p * 3 + 1] = this.py[k] - Math.sin(this.bank[k]) * Math.max(-this.hw, Math.min(this.hw, o)) + rows[j].dy;
        pos[p * 3 + 2] = this.pz[k] + this.rz[k] * o;
        const u = uvFn(rows[j], j, dist, o); uv[p * 2] = u[0]; uv[p * 2 + 1] = u[1];
      }
    }
    for (let i = 0; i < N; i++) for (let j = 0; j < R - 1; j++) {
      const a = i * R + j, b = a + 1, c = (i + 1) * R + j, d = c + 1;
      idx.push(a, b, c, c, b, d);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    g.setIndex(idx); g.computeVertexNormals();
    return g;
  }

  buildMeshes(r) {
    const th = this.theme, G = this.group, hw = this.hw, N = this.N;
    // --- 도로
    const roadTex = canvasTex(512, 512, (c, w, h) => {
      c.fillStyle = hex(th.road); c.fillRect(0, 0, w, h); noise(c, w, h, 9000, 0.05, 2);
      c.fillStyle = '#f2f2f2'; c.fillRect(w * 0.025, 0, w * 0.018, h); c.fillRect(w * 0.957, 0, w * 0.018, h);
      c.fillStyle = th.night ? '#7df' : '#f5c518'; c.fillRect(w * 0.492, 0, w * 0.016, h * 0.5);
      c.fillStyle = 'rgba(255,255,255,0.55)';
      for (const f of [0.25, 0.75]) c.fillRect(w * f - 3, 0, 6, h * 0.5);
    });
    const roadMat = new THREE.MeshStandardMaterial({ map: roadTex, roughness: th.key === 'snow' ? 0.55 : 0.86, metalness: 0.02 });
    const roadRows = [{ off: -hw, dy: 0 }, { off: hw, dy: 0 }];
    G.add(this.mesh(this.ribbon(roadRows, 1, (row, j, dist) => [j, dist / 24]), roadMat, true));
    // --- 연석
    const kerbTex = canvasTex(64, 128, (c, w, h) => { c.fillStyle = '#d8232a'; c.fillRect(0, 0, w, h / 2); c.fillStyle = '#f4f4f4'; c.fillRect(0, h / 2, w, h / 2); });
    const kerbMat = new THREE.MeshStandardMaterial({ map: kerbTex, roughness: 0.7 });
    for (const s of [1, -1]) {
      const g = this.ribbon([{ off: hw - 0.1, dy: 0.03 }, { off: hw + 1.4, dy: 0.03 }], s, (row, j, dist) => [j, dist / 8]);
      G.add(this.mesh(g, kerbMat, true));
    }
    // --- 갓길/지형
    const grassTex = canvasTex(256, 256, (c, w, h) => {
      c.fillStyle = hex(th.ground[0]); c.fillRect(0, 0, w, h);
      for (let i = 0; i < 160; i++) { c.fillStyle = hex(th.ground[1]) + 'cc'; c.beginPath(); c.arc(Math.random() * w, Math.random() * h, 6 + Math.random() * 22, 0, 6.283); c.fill(); }
      noise(c, w, h, 5000, 0.07, 2);
    });
    const groundMat = new THREE.MeshStandardMaterial({ map: grassTex, roughness: 1 });
    for (const s of [1, -1]) {
      G.add(this.mesh(this.ribbon(this.rows, s, (row, j, dist, o) => [Math.abs(o) / 14, dist / 14]), groundMat, true));
    }
    // 먼 바닥
    const far = new THREE.Mesh(new THREE.PlaneGeometry(9000, 9000), new THREE.MeshStandardMaterial({ color: th.far, roughness: th.key === 'tropic' ? 0.25 : 1, metalness: th.key === 'tropic' ? 0.3 : 0 }));
    far.rotation.x = -Math.PI / 2; far.position.set(0, this.minY - 95, 0); far.receiveShadow = false; G.add(far);
    // --- 가드레일 벽
    const wallTex = canvasTex(128, 64, (c, w, h) => {
      c.fillStyle = hex(th.wall[0]); c.fillRect(0, 0, w / 2, h); c.fillStyle = hex(th.wall[1]); c.fillRect(w / 2, 0, w / 2, h);
      c.fillStyle = 'rgba(0,0,0,0.18)'; c.fillRect(0, h * 0.72, w, h * 0.28);
    });
    const wallMat = new THREE.MeshStandardMaterial({ map: wallTex, roughness: 0.5, metalness: 0.15, side: THREE.DoubleSide });
    if (th.glowWall) { wallMat.emissive = new THREE.Color(0xffffff); wallMat.emissiveMap = wallTex; wallMat.emissiveIntensity = 0.9; }
    for (const s of [1, -1]) {
      const g = this.ribbon([{ off: this.wallOff, dy: 0 }, { off: this.wallOff, dy: 1.3 }], s, (row, j, dist) => [dist / 6, j]);
      G.add(this.mesh(g, wallMat, false));
      const cap = this.ribbon([{ off: this.wallOff - 0.3, dy: 1.3 }, { off: this.wallOff + 0.3, dy: 1.3 }], s, (row, j, dist) => [dist / 6, j]);
      G.add(this.mesh(cap, new THREE.MeshStandardMaterial({ color: 0xe8e8e8, roughness: 0.4, metalness: 0.4 }), false));
    }
    this.buildStartLine(G);
    this.buildPads(G, r);
    this.buildScenery(G, r);
    if (th.lamps) this.buildLamps(G);
    if (th.arches) this.buildArches(G, th.arches);
    G.add(skyDome(th, r));
  }

  mesh(geo, mat, receive) { const m = new THREE.Mesh(geo, mat); m.receiveShadow = receive; m.castShadow = false; return m; }

  buildStartLine(G) {
    const hw = this.hw, T = this.tangentAt(0), up = this.normalAt(0), q = basisQuat(T, up), P = this.pointAt(0);
    const chk = canvasTex(256, 64, (c, w, h) => {
      const s = 16; for (let x = 0; x < w / s; x++) for (let y = 0; y < h / s; y++) { c.fillStyle = (x + y) % 2 ? '#111' : '#f2f2f2'; c.fillRect(x * s, y * s, s, s); }
    });
    const line = new THREE.Mesh(new THREE.PlaneGeometry(this.width, 3.2), new THREE.MeshStandardMaterial({ map: chk, roughness: 0.7, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
    line.quaternion.copy(q); line.rotateX(-Math.PI / 2); line.position.copy(P).addScaledVector(up, 0.05); line.receiveShadow = true; G.add(line);
    const gate = new THREE.Group(); gate.quaternion.copy(q); gate.position.copy(P);
    const metal = new THREE.MeshStandardMaterial({ color: 0x2b2f3a, roughness: 0.4, metalness: 0.7 });
    for (const s of [-1, 1]) { const p = new THREE.Mesh(new THREE.BoxGeometry(1.4, 10, 1.4), metal); p.position.set(s * (hw + 1.6), 5, 0); p.castShadow = true; gate.add(p); }
    const banner = canvasTex(1024, 128, (c, w, h) => {
      const g = c.createLinearGradient(0, 0, w, 0); g.addColorStop(0, '#d8232a'); g.addColorStop(0.5, '#1b1f2a'); g.addColorStop(1, '#2a6fd6');
      c.fillStyle = g; c.fillRect(0, 0, w, h); c.fillStyle = '#fff'; c.font = 'bold 80px sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle';
      c.fillText('START / FINISH  🏁', w / 2, h / 2 + 4);
    }, false);
    const bm = new THREE.MeshStandardMaterial({ map: banner, emissive: 0xffffff, emissiveMap: banner, emissiveIntensity: 0.6, roughness: 0.5 });
    const bar = new THREE.Mesh(new THREE.BoxGeometry(this.width + 4.4, 2.4, 0.8), bm); bar.position.set(0, 9.6, 0); bar.castShadow = true; gate.add(bar);
    G.add(gate);
  }

  buildPads(G, r) {
    this.pads = [];
    const tex = canvasTex(128, 256, (c, w, h) => {
      c.fillStyle = 'rgba(0,10,30,0.85)'; c.fillRect(0, 0, w, h);
      for (let k = 0; k < 3; k++) {
        c.fillStyle = k % 2 ? '#ffe14a' : '#19e6ff'; c.beginPath();
        const y = 30 + k * 70; c.moveTo(w / 2, y); c.lineTo(w - 14, y + 44); c.lineTo(w - 38, y + 44); c.lineTo(w / 2, y + 16); c.lineTo(38, y + 44); c.lineTo(14, y + 44); c.closePath(); c.fill();
      }
      c.strokeStyle = '#19e6ff'; c.lineWidth = 6; c.strokeRect(3, 3, w - 6, h - 6);
    }, false);
    const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3, toneMapped: false, color: 0xffffff });
    const count = 6 + Math.floor(r() * 5);
    for (let k = 0; k < count; k++) {
      const idx = Math.floor(((k + 0.5 + (r() - 0.5) * 0.4) / count) * this.N), d = (r() - 0.5) * this.width * 0.5;
      if (idx < 14 || idx > this.N - 8) continue;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(5.2, 9), mat), up = this.normalAt(idx), P = this.pointAt(idx, d);
      m.quaternion.copy(basisQuat(this.tangentAt(idx), up)); m.rotateX(-Math.PI / 2);
      m.position.copy(P).addScaledVector(up, 0.07); G.add(m);
      this.pads.push({ idx, d, halfLen: 4.5, halfW: 2.8 });
    }
  }

  buildScenery(G, r) {
    const th = this.theme, N = this.N, cell = 60, grid = new Map();
    const key = (x, z) => Math.floor(x / cell) + ',' + Math.floor(z / cell);
    for (let i = 0; i < N; i += 2) { const k = key(this.px[i], this.pz[i]); (grid.get(k) || grid.set(k, []).get(k)).push(i); }
    const minDist = this.hw + this.SH + 5;
    const free = (x, z) => {
      const cx = Math.floor(x / cell), cz = Math.floor(z / cell);
      for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) {
        const l = grid.get((cx + a) + ',' + (cz + b)); if (!l) continue;
        for (const i of l) if ((this.px[i] - x) ** 2 + (this.pz[i] - z) ** 2 < minDist * minDist) return false;
      }
      return true;
    };
    const total = th.props.reduce((s, p) => s + p[1], 0);
    const buckets = {};
    const want = Math.round(N * 2.1);
    for (let n = 0; n < want; n++) {
      const i = Math.floor(r() * N), side = r() < 0.5 ? 1 : -1, lat = this.wallOff + 4 + Math.pow(r(), 1.4) * 55;
      const x = this.px[i] + this.rx[i] * lat * side, z = this.pz[i] + this.rz[i] * lat * side;
      if (!free(x, z)) continue;
      let pick = r() * total, kind = th.props[0][0];
      for (const p of th.props) { pick -= p[1]; if (pick <= 0) { kind = p[0]; break; } }
      (buckets[kind] = buckets[kind] || []).push({ x, y: this.py[i] + this.dyAt(lat) - 0.15, z, rot: r() * 6.283, s: 0.7 + r() * 0.9, r1: r(), r2: r(), r3: r() });
    }
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), col = new THREE.Color();
    for (const [kind, list] of Object.entries(buckets)) {
      const parts = propParts(kind, th);
      for (const p of parts) {
        const mat = p.glow ? new THREE.MeshBasicMaterial({ vertexColors: true, toneMapped: false, color: new THREE.Color().setScalar(p.glow) })
          : new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.85, flatShading: kind === 'rock' || kind === 'mesa' || kind === 'crystal' });
        const im = new THREE.InstancedMesh(p.geo, mat, list.length);
        list.forEach((it, k) => {
          let sx = it.s, sy = it.s, sz = it.s;
          if (kind === 'building') { sx = 14 + it.r1 * 22; sz = 14 + it.r2 * 22; sy = 30 + it.r3 * it.r3 * 150; }
          if (kind === 'mesa') { sx = sz = 1.2 + it.r1 * 1.8; sy = 0.8 + it.r2 * 1.6; }
          if (kind === 'rock' && th.key !== 'snow') { sx *= 1.4; sz *= 1.4; sy *= 1.2 + it.r1; }
          q.setFromAxisAngle(UP, it.rot);
          m.compose(new THREE.Vector3(it.x, it.y, it.z), q, new THREE.Vector3(sx, sy, sz));
          im.setMatrixAt(k, m);
          if (kind === 'lollipop' || kind === 'icecream') { col.setHSL(it.r1, 0.8, 0.6); im.setColorAt(k, col); }
          else if (!p.glow) { const v = 0.8 + it.r1 * 0.3; col.setRGB(v, v, v); im.setColorAt(k, col); }
        });
        im.castShadow = kind !== 'building' && !p.glow; im.receiveShadow = false; im.frustumCulled = false;
        G.add(im);
      }
    }
  }

  buildLamps(G) {
    const poles = [], heads = [], N = this.N;
    for (let i = 4, k = 0; i < N; i += 7, k++) {
      const s = k % 2 ? 1 : -1, lat = this.wallOff + 1.2, P = this.pointAt(i, lat * s);
      P.y = this.py[i] + this.dyAt(lat) - 0.2;
      const lookIn = -s * 3.2, rx = this.rx[i], rz = this.rz[i];
      poles.push(part(CYL(0.16, 0.22, 11, 6), 0x30343f, P.x, P.y + 5.5, P.z), part(BOX(0.25, 0.25, 3.6), 0x30343f, P.x + rx * lookIn * 0.5, P.y + 11, P.z + rz * lookIn * 0.5, 1, 1, 1, 0, Math.atan2(rx, rz), 0));
      heads.push(part(BOX(0.9, 0.18, 1.1), 0xfff0c0, P.x + rx * lookIn, P.y + 10.8, P.z + rz * lookIn, 1, 1, 1, 0, Math.atan2(rx, rz), 0));
    }
    G.add(new THREE.Mesh(merge(poles), new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.5, metalness: 0.5 })));
    G.add(new THREE.Mesh(merge(heads), new THREE.MeshBasicMaterial({ vertexColors: true, toneMapped: false, color: new THREE.Color().setScalar(3) })));
  }

  buildArches(G, color) {
    const N = this.N, count = 4, mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(2.2), toneMapped: false });
    for (let k = 0; k < count; k++) {
      const idx = Math.floor(((k + 0.5) / count) * N + 20) % N;
      const arch = new THREE.Mesh(new THREE.TorusGeometry(this.hw + 1.5, 0.45, 8, 40, Math.PI), mat), up = this.normalAt(idx);
      arch.quaternion.copy(basisQuat(this.tangentAt(idx), up)); arch.position.copy(this.pointAt(idx, 0)); G.add(arch);
    }
  }

  spawnPose(slot) {
    // 2열 그리드, 출발선 뒤쪽
    const row = Math.floor(slot / 2), col = slot % 2, back = 3 + row * 2.6;
    const i = ((-Math.round(back / this.ds)) % this.N + this.N) % this.N;
    const d = (col ? 1 : -1) * this.width * 0.2 + 0;
    const P = this.pointAt(i, d);
    return { x: P.x, z: P.z, heading: Math.atan2(this.tx[i], this.tz[i]), prog: -back / this.ds };
  }

  dispose() {
    this.group.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) { const ms = Array.isArray(o.material) ? o.material : [o.material]; ms.forEach((m) => { for (const k of ['map', 'emissiveMap']) if (m[k]) m[k].dispose(); m.dispose(); }); }
    });
  }
}
