
# ============================================================================
#  [폰] 소프트웨어 3D 렌더러 (pygame 폴리곤 + 페인터 알고리즘)
#   - 트랙은 실제 3D 좌표(고저차/뱅킹 포함)를 카메라로 변환해 먼 곳부터 칠한다.
#   - 카트는 파츠(박스/바퀴/윙/드라이버)로 이루어진 3D 모델 (100,000종 파라미터 조합)
# ============================================================================
class Cam(object):
    def __init__(self):
        self.set(0.0, 0.0, 0.0, 0.0, 0.0)

    def set(self, x, y, z, yaw, pitch):
        self.x, self.y, self.z, self.yaw, self.pitch = x, y, z, yaw, pitch
        self.sy, self.cy = math.sin(yaw), math.cos(yaw)
        self.sp, self.cp = math.sin(pitch), math.cos(pitch)


QUALITY = [  # 내부 해상도 폭, near/mid/far 구간(샘플), 카트 LOD 거리(m)
    dict(w=336, near=16, mid=30, far=60, lod0=11.0, lod1=60.0, props=70, parts=True),
    dict(w=440, near=22, mid=44, far=90, lod0=17.0, lod1=90.0, props=140, parts=True),
    dict(w=580, near=26, mid=54, far=120, lod0=26.0, lod1=120.0, props=220, parts=True),
]

OFFS = None   # 단면 정점 배치 (Track 마다 hw 가 달라서 set_track 에서 채움)
K = 12        # 단면당 정점 수

# 박스 면 (코너 인덱스 = (sx>0)<<2 | (sy>0)<<1 | (sz>0))
FACES = (
    ('z+', (1, 5, 7, 3), 0.98), ('z-', (4, 0, 2, 6), 0.86), ('x+', (4, 5, 7, 6), 0.76), ('x-', (1, 0, 2, 3), 0.90), ('y+', (2, 3, 7, 6), 1.12),
)


class Renderer(object):
    def __init__(self, sw, sh, quality=1):
        self.sw, self.sh = sw, sh
        self.track = None
        self.tg = None
        self.models = {}
        self.parts = []
        self.weather = []
        self.labels = []
        self.shake = 0.0
        self.cam = Cam()
        self.set_quality(quality, sw, sh)

    # ---- 해상도/품질 -------------------------------------------------------------------
    def set_quality(self, q, sw, sh):
        self.q = int(clamp(q, 0, 2))
        Q_ = QUALITY[self.q]
        self.qp = Q_
        self.sw, self.sh = sw, sh
        rw = min(Q_['w'], sw)
        rh = max(120, int(rw * sh / float(sw)))
        self.rw, self.rh = rw, rh
        self.hx, self.hy = rw / 2.0, rh / 2.0
        self.f = min(rh * 0.92, rw * 0.62)
        self.near = 0.55
        try:
            self.surf = pygame.Surface((rw, rh), 0, pygame.display.get_surface())
        except Exception:
            self.surf = pygame.Surface((rw, rh))
        near_n, mid_n, far_n = Q_['near'], Q_['mid'], Q_['far']
        back = 5
        offs = list(range(-back, near_n + 1))
        k = near_n + 2
        while k <= mid_n:
            offs.append(k)
            k += 2
        while k <= far_n:
            offs.append(k)
            k += 4
        self.offs = offs
        self.slot_map = {}
        for i in range(len(offs) - 1):
            for o in range(offs[i] + 1, offs[i + 1] + 1):
                self.slot_map[o] = i
        self.far_m = far_n * 4.0
        if self.track is not None:
            self.set_track(self.track)

    # ---- 트랙 지오메트리 -------------------------------------------------------------------
    def set_track(self, track):
        self.track = track
        th = track.theme
        self.tg = ThemeGfx(th, track.info['seed'], self.rw, self.rh, self.f, self.far_m)
        N = track.N
        hw, wo, sk = track.hw, track.wall_off, track.rows[3][0]
        offs = [(-hw, 0.0), (hw, 0.0), (-(hw + 1.4), 0.0), (hw + 1.4, 0.0), (-wo, 0.0), (wo, 0.0), (-sk, 0.0), (sk, 0.0),
                (-wo, 1.3), (wo, 1.3), (-0.28, 0.0), (0.28, 0.0)]
        GX = [0.0] * (N * K)
        GY = [0.0] * (N * K)
        GZ = [0.0] * (N * K)
        for i in range(N):
            for j in range(K):
                x, y, z = track.edge_point(i, offs[j][0])
                GX[i * K + j] = x
                GY[i * K + j] = y + offs[j][1] + (0.04 if j >= 10 else 0.0)
                GZ[i * K + j] = z
        self.GX, self.GY, self.GZ = GX, GY, GZ
        self.weather = []
        wtype = th.get('weather')
        if wtype:
            rnd = Rng(track.info['seed'] ^ 77)
            for _ in range(70):
                self.weather.append([rnd() * self.rw, rnd() * self.rh, 14 + rnd() * 26, (rnd() - 0.5) * 8, 1 + int(rnd() * 2)])
        self.wtype = wtype
        self.parts = []
        # 시작 게이트 박스 (트랙 로컬: x=오른쪽, y=위, z=진행방향)
        hwg = hw + 1.6
        self.gate_boxes = [(-hwg, 5, 0, 0.7, 5, 0.7, (43, 47, 58), 1, 1, False), (hwg, 5, 0, 0.7, 5, 0.7, (43, 47, 58), 1, 1, False),
                           (0, 9.6, 0, hw + 2.2, 1.2, 0.4, (200, 40, 50), 1, 1, False), (0, 9.6, 0.42, hw + 2.0, 1.0, 0.03, (245, 245, 245), 1, 1, True)]

    def model(self, kid):
        m = self.models.get(kid)
        if m is None:
            if len(self.models) > 40:
                self.models.clear()
            m = self.models[kid] = KartModel(kid)
        return m

    # ---- 파티클 ----------------------------------------------------------------------------
    def emit(self, x, y, z, vx, vy, vz, color, size, life):
        if len(self.parts) < 260:
            self.parts.append([x, y, z, vx, vy, vz, life, life, color, size])

    def update_particles(self, dt):
        out = []
        for p in self.parts:
            p[6] -= dt
            if p[6] > 0:
                p[0] += p[3] * dt
                p[1] += p[4] * dt
                p[2] += p[5] * dt
                p[4] -= 9.0 * dt
                out.append(p)
        self.parts = out
        for w in self.weather:
            w[1] += w[2] * dt * (-0.5 if self.wtype == 'ember' else 1.0)
            w[0] += w[3] * dt
            if w[1] > self.rh + 4:
                w[1] = -4
            elif w[1] < -4:
                w[1] = self.rh + 4
            if w[0] < -4:
                w[0] = self.rw + 4
            elif w[0] > self.rw + 4:
                w[0] = -4

    # ---- 투영 도우미 --------------------------------------------------------------------------
    def proj(self, x, y, z):
        c = self.cam
        dx, dy, dz = x - c.x, y - c.y, z - c.z
        xr = -dx * c.cy + dz * c.sy
        zr = dx * c.sy + dz * c.cy
        dp = zr * c.cp - dy * c.sp
        yc = dy * c.cp + zr * c.sp
        if dp > self.near:
            inv = self.f / dp
            return (self.hx + xr * inv, self.hy - yc * inv, dp, xr, yc)
        return (0.0, 0.0, dp, xr, yc)

    def poly(self, color, pts):
        """pts: proj() 튜플들. near 평면 클리핑 + 화면 밖 컬링"""
        near = self.near
        allin = True
        anyin = False
        for p in pts:
            if p[2] > near:
                anyin = True
            else:
                allin = False
        if not anyin:
            return
        if not allin:
            pts = self._clip_near(pts)
            if len(pts) < 3:
                return
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        mxx = max(xs)
        mnx = min(xs)
        mxy = max(ys)
        mny = min(ys)
        if mxx < 0 or mnx > self.rw or mxy < 0 or mny > self.rh:
            return
        if mxx > 2400 or mnx < -2400 or mxy > 2400 or mny < -2400:
            pts = self._clip_screen([(p[0], p[1]) for p in pts])
            if len(pts) < 3:
                return
            pygame.draw.polygon(self.surf, color, pts)
            return
        pygame.draw.polygon(self.surf, color, list(zip(xs, ys)))

    def _clip_near(self, pts):
        near = self.near
        f, hx, hy = self.f, self.hx, self.hy
        out = []
        n = len(pts)
        for i in range(n):
            a = pts[i]
            b = pts[(i + 1) % n]
            ain = a[2] > near
            bin_ = b[2] > near
            if ain:
                out.append(a)
            if ain != bin_:
                t = (near - a[2]) / (b[2] - a[2])
                xr = a[3] + (b[3] - a[3]) * t
                yc = a[4] + (b[4] - a[4]) * t
                inv = f / near
                out.append((hx + xr * inv, hy - yc * inv, near, xr, yc))
        return out

    def _clip_screen(self, pts):
        W, H = self.rw + 2, self.rh + 2
        for axis, lo, hi in ((0, -2, W), (1, -2, H)):
            for bound, keep_ge in ((lo, True), (hi, False)):
                out = []
                n = len(pts)
                for i in range(n):
                    a = pts[i]
                    b = pts[(i + 1) % n]
                    ain = (a[axis] >= bound) if keep_ge else (a[axis] <= bound)
                    bin_ = (b[axis] >= bound) if keep_ge else (b[axis] <= bound)
                    if ain:
                        out.append(a)
                    if ain != bin_:
                        t = (bound - a[axis]) / (b[axis] - a[axis])
                        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
                pts = out
                if not pts:
                    return pts
        return pts

    # ============================================================================
    #  프레임 그리기
    # ============================================================================
    def draw_background(self):
        c = self.cam
        tg = self.tg
        s = self.surf
        f, hx, hy = self.f, self.hx, self.hy
        hor = hy - f * math.tan(c.pitch)
        hori = int(hor)
        sky = tg.sky
        s.blit(sky, (0, hori - sky.get_height()))
        if hori < self.rh:
            s.fill(tg.ground_far, (0, max(0, hori), self.rw, self.rh - max(0, hori)))
        # 태양/달
        da = wrap_pi(c.yaw - tg.sun_az)
        if abs(da) < 1.1:
            sx = hx + f * da
            sy = hor - f * math.tan(tg.sun_el)
            g = tg.glow
            s.blit(g, (int(sx - g.get_width() / 2), int(sy - g.get_height() / 2)))
            r = max(3, int(self.rh * (0.028 if not tg.night else 0.04)))
            sc = hex_rgb(tg.th['sun'])
            pygame.draw.circle(s, mix_rgb(sc, (255, 255, 255), 0.6), (int(sx), int(sy)), r)
        # 별/구름 + 파노라마
        pw = tg.pano.get_width()
        x0 = int((hx + f * c.yaw) % pw) - pw
        fx_ = tg.skyfx
        for xx in (x0, x0 + pw):
            s.blit(fx_, (xx, hori - fx_.get_height() + 2))
        pano = tg.pano
        for xx in (x0, x0 + pw):
            s.blit(pano, (xx, hori - pano.get_height() + 3))

    def draw_world(self, race, focus_idx, dirn):
        tr = self.track
        tg = self.tg
        N = tr.N
        c = self.cam
        surf = self.surf
        f, hx, hy, near = self.f, self.hx, self.hy, self.near
        cx, cy, cz = c.x, c.y, c.z
        csy, ccy, csp, ccp = c.sy, c.cy, c.sp, c.cp
        GX, GY, GZ = self.GX, self.GY, self.GZ
        offs = self.offs
        lut = tg.fog_lut
        lutmax = len(lut) - 1
        pal = tg.pal
        slot_map = self.slot_map
        items = [[] for _ in offs]
        half = N // 2
        # --- 슬롯에 오브젝트 배치 (장식물, 카트, 패드, 가로등, 게이트)
        pbs = tr.props_by_seg
        o_lo, o_hi = offs[0] + 1, offs[-1]
        for o in range(o_lo, o_hi + 1):
            i = (focus_idx + dirn * o) % N
            lst = pbs.get(i)
            if lst:
                sl = items[slot_map[o]]
                for p in lst:
                    dx, dz = p['x'] - cx, p['z'] - cz
                    dpp = (dx * csy + dz * ccy) * ccp - (p['y'] - cy) * csp
                    if dpp > 3.0:
                        sl.append((dpp, 0, p))
        for rc in race.racers:
            o = ((rc.idx - focus_idx) * dirn + half) % N - half
            sl_i = slot_map.get(o)
            if sl_i is not None:
                dx, dz = rc.x - cx, rc.z - cz
                items[sl_i].append(((dx * csy + dz * ccy) * ccp - (rc.y - cy) * csp, 1, rc))
        for p in tr.pads:
            o = ((p['idx'] - focus_idx) * dirn + half) % N - half
            sl_i = slot_map.get(o)
            if sl_i is not None:
                items[sl_i].append((1e6, 2, p))      # 패드는 도로 위에 깔리므로 가장 먼저
        if tr.lamps:
            for (li, side) in tr.lamps:
                o = ((li - focus_idx) * dirn + half) % N - half
                sl_i = slot_map.get(o)
                if sl_i is not None:
                    items[sl_i].append((self._dp_of(GX[li * K + 5], GY[li * K + 5], GZ[li * K + 5]) + 0.5, 3, (li, side)))
        o = ((0 - focus_idx) * dirn + half) % N - half
        sl_i = slot_map.get(o)
        if sl_i is not None:
            items[sl_i].append((self._dp_of(tr.px[0], tr.py[0], tr.pz[0]), 4, 0))
        for ai in tr.arches:
            o = ((ai - focus_idx) * dirn + half) % N - half
            sl_i = slot_map.get(o)
            if sl_i is not None:
                items[sl_i].append((self._dp_of(tr.px[ai], tr.py[ai], tr.pz[ai]), 5, ai))

        poly = self.poly
        prev = None
        prev_i = 0
        prev_k = 0
        nsec = len(offs)
        for k in range(nsec - 1, -1, -1):
            i = (focus_idx + dirn * offs[k]) % N
            base = i * K
            pts = []
            for j in range(K):
                dx = GX[base + j] - cx
                dy = GY[base + j] - cy
                dz = GZ[base + j] - cz
                xr = -dx * ccy + dz * csy
                zr = dx * csy + dz * ccy
                dp = zr * ccp - dy * csp
                yc = dy * ccp + zr * csp
                if dp > near:
                    inv = f / dp
                    pts.append((hx + xr * inv, hy - yc * inv, dp, xr, yc))
                else:
                    pts.append((0.0, 0.0, dp, xr, yc))
            if prev is not None:
                A, B = prev, pts
                stride = offs[k + 1] - offs[k]
                dpm = (A[0][2] + B[0][2]) * 0.5
                lv = lut[int(dpm) if dpm < lutmax else lutmax]
                ia = i if dirn > 0 else prev_i
                par = (min(i, prev_i) // 4) & 1 if stride == 1 else 0
                par2 = (min(i, prev_i) // 2) & 1 if stride <= 2 else 0
                grass = pal['grass_b' if par else 'grass_a'][lv]
                skirt = pal['skirt_b' if par else 'skirt_a'][lv]
                # 비탈 -> 갓길 -> 연석 -> 도로 순으로 칠함
                poly(skirt, (A[6], A[4], B[4], B[6]))
                poly(skirt, (A[5], A[7], B[7], B[5]))
                poly(grass, (A[4], A[2], B[2], B[4]))
                poly(grass, (A[3], A[5], B[5], B[3]))
                if dpm < 170:
                    kc = pal['kerb_r' if par2 else 'kerb_w'][lv]
                    poly(kc, (A[2], A[0], B[0], B[2]))
                    poly(kc, (A[1], A[3], B[3], B[1]))
                poly(pal['road_b' if par else 'road_a'][lv], (A[0], A[1], B[1], B[0]))
                if stride == 1 and dpm < 120 and ((min(i, prev_i) // 3) & 1) == 0:
                    poly(pal['dash'][lv], (A[10], A[11], B[11], B[10]))
                w_a = pal['wall_a' if par2 else 'wall_b'][lv]
                w_b = pal['wall_a2' if par2 else 'wall_b2'][lv]
                poly(w_a, (A[4], A[8], B[8], B[4]))
                poly(w_b, (A[9], A[5], B[5], B[9]))
                # 결승선 체커
                lo_i, hi_i = min(i, prev_i), max(i, prev_i)
                if stride == 1 and dpm < 100 and (lo_i == 0 or (lo_i == N - 1 and hi_i == 0)):
                    self._checker(A, B, lv)
                # 이 구간에 속한 오브젝트를 먼 것부터
                sl = items[k]
                if sl:
                    sl.sort(key=lambda t: -t[0])
                    for it in sl:
                        code = it[1]
                        if code == 0:
                            self._draw_prop(it[2], it[0])
                        elif code == 1:
                            self._draw_kart(it[2], it[0], lv)
                        elif code == 2:
                            self._draw_pad(it[2])
                        elif code == 3:
                            self._draw_lamp(it[2], lv)
                        elif code == 4:
                            self._draw_gate()
                        else:
                            self._draw_arch(it[2])
            prev = pts
            prev_i = i

    def _dp_of(self, x, y, z):
        c = self.cam
        dx, dy, dz = x - c.x, y - c.y, z - c.z
        return (dx * c.sy + dz * c.cy) * c.cp - dy * c.sp

    def _checker(self, A, B, lv):
        for r_ in range(2):
            for cidx in range(8):
                u0, u1 = cidx / 8.0, (cidx + 1) / 8.0
                v0, v1 = r_ * 0.5, (r_ + 1) * 0.5

                def pt(u, v):
                    # 도로 사각형 (A0,A1 먼쪽 / B0,B1 가까운쪽) 위의 쌍선형 보간
                    ax = A[0][0] + (A[1][0] - A[0][0]) * u
                    ay = A[0][1] + (A[1][1] - A[0][1]) * u
                    bx = B[0][0] + (B[1][0] - B[0][0]) * u
                    by = B[0][1] + (B[1][1] - B[0][1]) * u
                    return (ax + (bx - ax) * v, ay + (by - ay) * v, 1.0, 0, 0)
                if min(A[0][2], A[1][2], B[0][2], B[1][2]) <= self.near:
                    return
                col = (20, 20, 22) if (cidx + r_) % 2 else (245, 245, 245)
                self.poly(col, (pt(u0, v0), pt(u1, v0), pt(u1, v1), pt(u0, v1)))

    # ---- 장식물 --------------------------------------------------------------------------------
    def _draw_prop(self, p, dp):
        kind = p['kind']
        c = self.cam
        dx, dy, dz = p['x'] - c.x, p['y'] - c.y, p['z'] - c.z
        xr = -dx * c.cy + dz * c.sy
        zr = dx * c.sy + dz * c.cy
        d = zr * c.cp - dy * c.sp
        if d < 3.0:
            return
        yc = dy * c.cp + zr * c.sp
        inv = self.f / d
        sx = self.hx + xr * inv
        sy = self.hy - yc * inv
        wm, hm = SPRITE_DIM[kind][0], SPRITE_DIM[kind][1]
        s = p['s']
        var = 0
        if kind == 'building':
            wm = 14 + p['r1'] * 22
            hm = 30 + p['r3'] * p['r3'] * 150
            var = int(p['r2'] * 4)
        elif kind == 'mesa':
            wm, hm = wm * (1.2 + p['r1'] * 1.8), hm * (0.8 + p['r2'] * 1.6)
        elif kind == 'rock':
            wm, hm = wm * s * 1.3, hm * s * (1.0 + p['r1'] * 0.7)
        else:
            wm, hm = wm * s, hm * s
            if kind == 'roundtree':
                var = int(p['r1'] * 4)
            elif kind == 'lollipop':
                var = int(p['r1'] * 6)
            elif kind == 'icecream':
                var = int(p['r1'] * 3)
        hpx = inv * hm
        wpx = inv * wm
        if hpx < 2.5 or sy < 0 or sy - hpx > self.rh or sx + wpx * 0.5 < 0 or sx - wpx * 0.5 > self.rw:
            return
        if hpx > 1400:
            return
        tg = self.tg
        spr = tg.scaled_sprite(kind, var, wpx, hpx)
        lut = tg.fog_lut
        lv = lut[int(d) if d < len(lut) - 1 else len(lut) - 1]
        spr.set_alpha(255 - lv * 15 if lv else 255)
        self.surf.blit(spr, (int(sx - spr.get_width() / 2), int(sy - spr.get_height() + 1)))

    def _draw_lamp(self, data, lv):
        li, side = data
        tr = self.track
        x, y, z = self.GX[li * K + (5 if side > 0 else 4)], self.GY[li * K + 5], self.GZ[li * K + (5 if side > 0 else 4)]
        a = self.proj(x, y, z)
        b = self.proj(x, y + 9.5, z)
        if a[2] > self.near and b[2] > self.near:
            pygame.draw.line(self.surf, (60, 64, 80), (a[0], a[1]), (b[0], b[1]), 1)
            r = max(1, int(self.f * 0.7 / b[2]))
            pygame.draw.circle(self.surf, (255, 240, 190), (int(b[0]), int(b[1])), r)

    def _draw_arch(self, ai):
        tr = self.track
        col = hex_rgb(tr.theme['arches'])
        hw = tr.hw + 1.5
        prev = None
        for k in range(0, 13):
            a = math.pi * k / 12.0
            x, y, z = tr.edge_point(ai, -hw * math.cos(a))
            p = self.proj(x, y + hw * 0.0 + math.sin(a) * hw * 0.75 + 0.2, z)
            if prev is not None and prev[2] > self.near and p[2] > self.near:
                pygame.draw.line(self.surf, col, (prev[0], prev[1]), (p[0], p[1]), 2)
            prev = p

    def _draw_pad(self, pad):
        tr = self.track
        N = tr.N
        idx, d = pad['idx'], pad['d']
        hl, hw_ = pad['half_len'] / tr.ds, pad['half_w']

        def P(u, v):
            x, y, z, _h = tr.pose_at(idx + v * hl, d + u * hw_)
            return self.proj(x, y + 0.07, z)
        self.poly((10, 28, 70), (P(-1, -1), P(1, -1), P(1, 1), P(-1, 1)))
        for n, v0 in enumerate((-0.55, 0.0, 0.55)):
            col = (25, 230, 255) if n % 2 == 0 else (255, 225, 74)
            self.poly(col, (P(0, v0 + 0.32), P(0.9, v0 - 0.12), P(0.9, v0 - 0.34), P(0, v0 + 0.1), P(-0.9, v0 - 0.34), P(-0.9, v0 - 0.12)))

    def _draw_gate(self):
        tr = self.track
        T = (tr.tx[0], tr.ty[0], tr.tz[0])
        up = tr.surface_normal(0)
        Rv = (tr.rx[0], 0.0, tr.rz[0])
        org = (tr.px[0], tr.py[0], tr.pz[0])
        self.draw_boxes(org, Rv, up, T, self.gate_boxes, 1.0)

    # ---- 카트 -----------------------------------------------------------------------------------------
    def draw_boxes(self, org, Rv, Uv, Fv, boxes, shade, lod_fog=0):
        """박스 목록을 (org, R/U/F 기저)에서 3D 로 그린다. 각 박스: 보이는 면만 칠함."""
        c = self.cam
        f, hx, hy, near = self.f, self.hx, self.hy, self.near
        csy, ccy, csp, ccp = c.sy, c.cy, c.sp, c.cp
        ox, oy, oz = org[0] - c.x, org[1] - c.y, org[2] - c.z
        # 월드 벡터 -> 카메라 좌표 (x, y, depth)

        def cam_vec(v):
            xr = -v[0] * ccy + v[2] * csy
            zr = v[0] * csy + v[2] * ccy
            return (xr, v[1] * ccp + zr * csp, zr * ccp - v[1] * csp)
        O = cam_vec((ox, oy, oz))
        Rc, Uc, Fc = cam_vec(Rv), cam_vec(Uv), cam_vec(Fv)
        # 카메라의 로컬 좌표
        clx = -(ox * Rv[0] + oy * Rv[1] + oz * Rv[2])
        cly = -(ox * Uv[0] + oy * Uv[1] + oz * Uv[2])
        clz = -(ox * Fv[0] + oy * Fv[1] + oz * Fv[2])
        order = []
        for bx in boxes:
            dcen = O[2] + Rc[2] * bx[0] + Uc[2] * bx[1] + Fc[2] * bx[2]
            order.append((dcen, bx))
        order.sort(key=lambda t: -t[0])
        surf = self.surf
        rw, rh = self.rw, self.rh
        for dcen, bx in order:
            if dcen < -2.0:
                continue
            bcx, bcy, bcz, bhx, bhy, bhz, col, tx, ty, glow = bx
            vis = {'z+': clz > bcz + bhz, 'z-': clz < bcz - bhz, 'x+': clx > bcx + bhx, 'x-': clx < bcx - bhx, 'y+': cly > bcy + bhy}
            if not any(vis.values()):
                continue
            corners = []
            for idx in range(8):
                sx_ = 1 if idx & 4 else -1
                sy_ = 1 if idx & 2 else -1
                sz_ = 1 if idx & 1 else -1
                if sz_ > 0:
                    lx, ly = bcx + sx_ * bhx * tx, bcy + sy_ * bhy * ty
                else:
                    lx, ly = bcx + sx_ * bhx, bcy + sy_ * bhy
                lz = bcz + sz_ * bhz
                xr = O[0] + Rc[0] * lx + Uc[0] * ly + Fc[0] * lz
                yc = O[1] + Rc[1] * lx + Uc[1] * ly + Fc[1] * lz
                dp = O[2] + Rc[2] * lx + Uc[2] * ly + Fc[2] * lz
                if dp > near:
                    inv = f / dp
                    corners.append((hx + xr * inv, hy - yc * inv, dp, xr, yc))
                else:
                    corners.append((0.0, 0.0, dp, xr, yc))
            for name, ids, k in FACES:
                if not vis[name]:
                    continue
                cc = col if glow else shade_rgb(col, k * shade)
                self.poly(cc, [corners[i] for i in ids])

    def _draw_kart(self, rc, dp, lv):
        tg = self.tg
        qp = self.qp
        m = self.model(rc.kart_id)
        if dp < (1.0 if rc.kind == 'local' else 3.2):
            return
        h = rc.h
        up = rc.up
        fx, fz = math.sin(h), math.cos(h)
        # 도로면에 투영한 전방 벡터
        d = fx * up[0] + fz * up[2]
        Fv = (fx - up[0] * d, -up[1] * d, fz - up[2] * d)
        fl = math.sqrt(Fv[0] ** 2 + Fv[1] ** 2 + Fv[2] ** 2) or 1.0
        Fv = (Fv[0] / fl, Fv[1] / fl, Fv[2] / fl)
        Rv = (Fv[1] * up[2] - Fv[2] * up[1], Fv[2] * up[0] - Fv[0] * up[2], Fv[0] * up[1] - Fv[1] * up[0])   # F x U
        org = (rc.x, rc.y, rc.z)
        amb = 0.7 if tg.night else 1.0
        # 드리프트: 차체를 진행 방향에서 약간 틀어 보이게 (차체만 회전)
        yaw_off = 0.0
        if rc.drifting:
            yaw_off = -rc.drift_dir * 0.3
        elif abs(rc.slip) > 1.0:
            yaw_off = clamp(-rc.slip * 0.02, -0.25, 0.25)
        if yaw_off:
            cs, sn = math.cos(yaw_off), math.sin(yaw_off)
            Fn = tuple(Fv[i] * cs + Rv[i] * sn for i in range(3))
            Rn = tuple(Rv[i] * cs - Fv[i] * sn for i in range(3))
            Fv, Rv = Fn, Rn
        # 그림자
        if dp < qp['lod1']:
            L, W = m.L, m.W
            pts = []
            for a in range(8):
                t = a * TAU / 8
                lx, lz = math.cos(t) * W * 0.66, math.sin(t) * L * 0.62
                pts.append(self.proj(org[0] + Rv[0] * lx + Fv[0] * lz, org[1] + 0.05 + Rv[1] * lx + Fv[1] * lz, org[2] + Rv[2] * lx + Fv[2] * lz))
            base_col = tg.pal['grass_a' if rc.offroad else 'road_a'][lv]
            self.poly(shade_rgb(base_col, 0.5), pts)
        if dp > qp['lod1'] * 1.9:
            # 아주 먼 카트: 색 점
            p = self.proj(org[0], org[1] + 0.7, org[2])
            if p[2] > self.near:
                r = max(1, int(self.f * 1.0 / p[2]))
                pygame.draw.rect(self.surf, m.main, (int(p[0] - r), int(p[1] - r), r * 2 + 1, r + 1))
            return
        lod0 = dp < qp['lod0']
        # 부스트 불꽃
        if rc.boosting and dp < qp['lod1']:
            L = m.L
            ah = m.base + m.H * 0.3
            anc = (org[0] - Fv[0] * (L / 2) + up[0] * ah, org[1] - Fv[1] * (L / 2) + up[1] * ah, org[2] - Fv[2] * (L / 2) + up[2] * ah)
            for ln, col in ((1.9, (255, 140, 30)), (1.1, (255, 230, 120))):
                ln = ln * (0.8 + 0.4 * random_f())
                pa = self.proj(anc[0] + Rv[0] * 0.2, anc[1] + Rv[1] * 0.2, anc[2] + Rv[2] * 0.2)
                pb = self.proj(anc[0] - Rv[0] * 0.2, anc[1] - Rv[1] * 0.2, anc[2] - Rv[2] * 0.2)
                pt = self.proj(anc[0] - Fv[0] * ln, anc[1] - Fv[1] * ln, anc[2] - Fv[2] * ln)
                self.poly(col, (pa, pb, pt))
        boxes = m.boxes if lod0 else m.boxes_lod1
        # 바퀴 + 차체를 깊이순으로 섞어 그리기 위해: 뒤 바퀴 -> 차체 -> 앞 바퀴 (뒤에서 보는 시점에 적합)
        cam = self.cam
        cl = ((cam.x - org[0]) * Fv[0] + (cam.y - org[1]) * Fv[1] + (cam.z - org[2]) * Fv[2])
        wheels_back = [w for w in m.wheels if w[2] < 0]
        wheels_front = [w for w in m.wheels if w[2] > 0]
        first, second = (wheels_front, wheels_back) if cl < 0 else (wheels_back, wheels_front)
        for w in first:
            self._draw_wheel(m, w, org, Rv, up, Fv, rc, lod0, amb)
        self.draw_boxes(org, Rv, up, Fv, boxes, amb)
        # 드라이버 헬멧
        hp = m.helmet
        hxw = org[0] + Rv[0] * hp[0] + up[0] * hp[1] + Fv[0] * hp[2]
        hyw = org[1] + Rv[1] * hp[0] + up[1] * hp[1] + Fv[1] * hp[2]
        hzw = org[2] + Rv[2] * hp[0] + up[2] * hp[1] + Fv[2] * hp[2]
        hp_ = self.proj(hxw, hyw, hzw)
        if hp_[2] > self.near:
            r = max(2, int(self.f * 0.28 / hp_[2]))
            pygame.draw.circle(self.surf, shade_rgb(m.main, amb * 0.8), (int(hp_[0]), int(hp_[1])), r)
            pygame.draw.circle(self.surf, shade_rgb(m.main, amb * 1.3), (int(hp_[0] - r * 0.3), int(hp_[1] - r * 0.3)), max(1, r // 2))
            if cl > 0 and lod0:
                pygame.draw.rect(self.surf, (12, 12, 14), (int(hp_[0] - r * 0.7), int(hp_[1] - r * 0.15), max(2, int(r * 1.4)), max(1, int(r * 0.45))))
        for w in second:
            self._draw_wheel(m, w, org, Rv, up, Fv, rc, lod0, amb)
        # 이름표
        if rc.kind != 'local' and 14 < dp < 150:
            p = self.proj(org[0] + up[0] * 2.4, org[1] + up[1] * 2.4, org[2] + up[2] * 2.4)
            if p[2] > self.near:
                self.labels.append((p[0], p[1], rc.name, (255, 210, 120) if rc.kind == 'bot' else (150, 232, 255), dp))

    def _draw_wheel(self, m, w, org, Rv, Uv, Fv, rc, lod0, amb):
        lx, ly, lz, sgn, front = w
        R, ww = m.wheel_r, m.wheel_w
        if not lod0:
            self.draw_boxes(org, Rv, Uv, Fv, [(lx, ly, lz, ww / 2, R, R, (26, 26, 30), 1, 1, False)], amb)
            return
        cam = self.cam
        # 바퀴 중심(월드)
        ctr = (org[0] + Rv[0] * lx + Uv[0] * ly + Fv[0] * lz, org[1] + Rv[1] * lx + Uv[1] * ly + Fv[1] * lz, org[2] + Rv[2] * lx + Uv[2] * ly + Fv[2] * lz)
        spin = self._wheel_phase(rc)
        steer = -rc.steer * 0.45 if front else 0.0
        cs, sn = math.cos(steer), math.sin(steer)
        # 앞바퀴 조향: 회전축(로컬 x)을 y축 둘레로 돌림
        ax = (Rv[0] * cs + Fv[0] * sn, Rv[1] * cs + Fv[1] * sn, Rv[2] * cs + Fv[2] * sn)
        fw = (Fv[0] * cs - Rv[0] * sn, Fv[1] * cs - Rv[1] * sn, Fv[2] * cs - Rv[2] * sn)
        hxw = ww / 2.0
        ring = []
        for k in range(6):
            a = spin + k * math.pi / 3.0
            ca, sa = math.cos(a) * R, math.sin(a) * R
            ring.append((Uv[0] * ca + fw[0] * sa, Uv[1] * ca + fw[1] * sa, Uv[2] * ca + fw[2] * sa))
        capA = []
        capB = []
        for r_ in ring:
            capA.append(self.proj(ctr[0] + ax[0] * hxw + r_[0], ctr[1] + ax[1] * hxw + r_[1], ctr[2] + ax[2] * hxw + r_[2]))
            capB.append(self.proj(ctr[0] - ax[0] * hxw + r_[0], ctr[1] - ax[1] * hxw + r_[1], ctr[2] - ax[2] * hxw + r_[2]))
        # 카메라가 어느 캡 쪽에 있나
        v = (cam.x - ctr[0], cam.y - ctr[1], cam.z - ctr[2])
        side = v[0] * ax[0] + v[1] * ax[1] + v[2] * ax[2]
        tire = shade_rgb((34, 34, 40), amb)
        # 접지면(트레드) 먼저
        for k in range(6):
            a = spin + (k + 0.5) * math.pi / 3.0
            nx = Uv[0] * math.cos(a) + fw[0] * math.sin(a)
            ny = Uv[1] * math.cos(a) + fw[1] * math.sin(a)
            nz = Uv[2] * math.cos(a) + fw[2] * math.sin(a)
            if (v[0] * nx + v[1] * ny + v[2] * nz) > R * 0.866:
                shade = 0.7 + 0.3 * (0.5 + 0.5 * math.sin(a * 1.0))
                k2 = (k + 1) % 6
                self.poly(shade_rgb(tire, shade * (1.0 + (0.15 if k % 2 else 0.0))), (capA[k], capA[k2], capB[k2], capB[k]))
        if abs(side) > hxw:
            cap = capA if side > 0 else capB
            rim = m.rim_color
            self.poly(shade_rgb((26, 26, 30), amb), cap)
            # 림(안쪽 6각형)
            ctrp = self.proj(ctr[0] + ax[0] * (hxw + 0.01) * (1 if side > 0 else -1), ctr[1] + ax[1] * (hxw + 0.01) * (1 if side > 0 else -1), ctr[2] + ax[2] * (hxw + 0.01) * (1 if side > 0 else -1))
            if ctrp[2] > self.near:
                inner = []
                for p_ in cap:
                    inner.append((ctrp[0] + (p_[0] - ctrp[0]) * 0.68, ctrp[1] + (p_[1] - ctrp[1]) * 0.68, p_[2], p_[3], p_[4]))
                self.poly(rim if m.rim in (3, 4) else shade_rgb(rim, amb), inner)
                if m.rim in (1, 2):
                    for k in range(0, 6, 1 if m.rim == 2 else 2):
                        pygame.draw.line(self.surf, (30, 30, 36), (ctrp[0], ctrp[1]), (inner[k][0], inner[k][1]), 1)
                else:
                    hub = [(ctrp[0] + (p_[0] - ctrp[0]) * 0.28, ctrp[1] + (p_[1] - ctrp[1]) * 0.28, p_[2], p_[3], p_[4]) for p_ in cap]
                    self.poly((40, 40, 48), hub)

    def _wheel_phase(self, rc):
        return (rc.total * self.track.ds / 0.4) % TAU if self.track is not None else 0.0

    # ---- 프레임 ----------------------------------------------------------------------------------------
    def render(self, race, cam_pos, focus_idx, dirn, boost_fx=0.0, speed_ratio=0.0, t=0.0):
        self.labels = []
        self.cam.set(*cam_pos)
        self.draw_background()
        self.draw_world(race, focus_idx, dirn)
        self._draw_particles()
        self._draw_weather()
        if boost_fx > 0 or speed_ratio > 0.92:
            self._speed_lines(max(boost_fx, (speed_ratio - 0.9) * 4), t)
        return self.surf

    def _draw_particles(self):
        s = self.surf
        for p in self.parts:
            pr = self.proj(p[0], p[1], p[2])
            if pr[2] <= self.near:
                continue
            life = p[6] / p[7]
            r = max(1, int(p[9] * self.f / pr[2] * (0.4 + life)))
            col = p[8]
            col = (int(col[0] * (0.5 + 0.5 * life)), int(col[1] * (0.5 + 0.5 * life)), int(col[2] * (0.5 + 0.5 * life)))
            if 0 <= pr[0] < self.rw and 0 <= pr[1] < self.rh:
                pygame.draw.circle(s, col, (int(pr[0]), int(pr[1])), r)

    def _draw_weather(self):
        if not self.weather:
            return
        col = {'snow': (255, 255, 255), 'ember': (255, 150, 50), 'leaf': (217, 100, 40), 'sprinkle': (255, 120, 200)}.get(self.wtype, (255, 255, 255))
        s = self.surf
        for w in self.weather:
            if self.wtype == 'sprinkle':
                pygame.draw.rect(s, [(255, 120, 200), (120, 220, 255), (255, 230, 100)][int(w[0]) % 3], (int(w[0]), int(w[1]), 2, 3))
            elif w[4] > 1:
                pygame.draw.circle(s, col, (int(w[0]), int(w[1])), 1)
            else:
                s.set_at((int(w[0]) % self.rw, int(w[1]) % self.rh), col)

    def _speed_lines(self, amt, t):
        s = self.surf
        cx, cy = self.hx, self.hy * 1.05
        rnd = Rng(int(t * 24))
        n = int(10 + 14 * clamp(amt, 0, 1))
        for _ in range(n):
            a = rnd() * TAU
            r1 = self.rh * (0.42 + rnd() * 0.25)
            r2 = r1 + self.rh * (0.12 + rnd() * 0.2)
            c = int(150 + 100 * rnd())
            pygame.draw.line(s, (c, c, c), (cx + math.cos(a) * r1 * 1.4, cy + math.sin(a) * r1), (cx + math.cos(a) * r2 * 1.4, cy + math.sin(a) * r2), 1)


def random_f():
    return _random.random()
