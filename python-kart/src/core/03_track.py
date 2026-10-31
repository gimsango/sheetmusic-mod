
# ----------------------------------------------------------------------------
#  트랙 생성: 맵 번호(1~1000) -> 고유한 코스 (중심선/고저차/뱅킹/장식물/부스트 패드)
# ----------------------------------------------------------------------------
def _mix3(a, b, wa, wb):
    return (a[0] * wa + b[0] * wb, a[1] * wa + b[1] * wb, a[2] * wa + b[2] * wb)


def catmull_closed(pts, per=40, alpha=0.5):
    """닫힌 centripetal Catmull-Rom 스플라인 (Barry-Goldman)"""
    n = len(pts)
    out = []

    def dist(a, b):
        return max(1e-3, math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2))
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        t0 = 0.0
        t1 = t0 + dist(p0, p1) ** alpha
        t2 = t1 + dist(p1, p2) ** alpha
        t3 = t2 + dist(p2, p3) ** alpha
        for s in range(per):
            t = t1 + (t2 - t1) * s / per
            a1 = _mix3(p0, p1, (t1 - t) / (t1 - t0), (t - t0) / (t1 - t0))
            a2 = _mix3(p1, p2, (t2 - t) / (t2 - t1), (t - t1) / (t2 - t1))
            a3 = _mix3(p2, p3, (t3 - t) / (t3 - t2), (t - t2) / (t3 - t2))
            b1 = _mix3(a1, a2, (t2 - t) / (t2 - t0), (t - t0) / (t2 - t0))
            b2 = _mix3(a2, a3, (t3 - t) / (t3 - t1), (t - t1) / (t3 - t1))
            out.append(_mix3(b1, b2, (t2 - t) / (t2 - t1), (t - t1) / (t2 - t1)))
    return out


def resample_closed(poly, spacing, min_n=220):
    """닫힌 폴리라인을 호 길이 기준 균일 간격으로 재샘플링"""
    m = len(poly)
    seg = []
    total = 0.0
    for i in range(m):
        a = poly[i]
        b = poly[(i + 1) % m]
        d = math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)
        seg.append(d)
        total += d
    n = max(min_n, int(round(total / spacing)))
    step = total / n
    out = []
    i = 0
    acc = 0.0
    for k in range(n):
        target = k * step
        while i < m - 1 and target > acc + seg[i]:
            acc += seg[i]
            i += 1
        f = (target - acc) / seg[i] if seg[i] > 1e-9 else 0.0
        f = 0.0 if f < 0 else (1.0 if f > 1 else f)
        a = poly[i]
        b = poly[(i + 1) % m]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f))
    return out


def max_turn_angle(poly):
    n = len(poly)
    worst = 0.0
    for i in range(n):
        a = poly[i - 1]
        b = poly[i]
        c = poly[(i + 1) % n]
        v1x = b[0] - a[0]
        v1z = b[2] - a[2]
        v2x = c[0] - b[0]
        v2z = c[2] - b[2]
        ang = abs(math.atan2(v1x * v2z - v1z * v2x, v1x * v2x + v1z * v2z))
        if ang > worst:
            worst = ang
    return worst


def min_separation(poly, ds):
    """경로상으로 멀리 떨어진 두 구간이 공간적으로 얼마나 가까운지"""
    n = len(poly)
    cell = 90.0
    grid = {}
    for i, p in enumerate(poly):
        grid.setdefault((int(p[0] // cell), int(p[2] // cell)), []).append(i)
    skip = int(140.0 / ds)
    best = 1e18
    for i, p in enumerate(poly):
        cx = int(p[0] // cell)
        cz = int(p[2] // cell)
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                lst = grid.get((cx + a, cz + b))
                if not lst:
                    continue
                for j in lst:
                    dj = abs(i - j)
                    if min(dj, n - dj) < skip:
                        continue
                    q = poly[j]
                    d = (p[0] - q[0]) ** 2 + (p[2] - q[2]) ** 2
                    if d < best:
                        best = d
    return math.sqrt(best)


def relax_corners(poly, max_ang=0.19, iters=60, spacing=4.0):
    n = len(poly)
    pts = [list(p) for p in poly]
    changed = False
    for _ in range(iters):
        bad = []
        for i in range(n):
            a = pts[i - 1]
            b = pts[i]
            c = pts[(i + 1) % n]
            v1x = b[0] - a[0]
            v1z = b[2] - a[2]
            v2x = c[0] - b[0]
            v2z = c[2] - b[2]
            if abs(math.atan2(v1x * v2z - v1z * v2x, v1x * v2x + v1z * v2z)) > max_ang:
                bad.append(i)
        if not bad:
            break
        changed = True
        mark = set()
        for i in bad:
            for k in range(-7, 8):
                mark.add((i + k) % n)
        new = [p[:] for p in pts]
        for i in mark:
            a = pts[i - 1]
            b = pts[i]
            c = pts[(i + 1) % n]
            new[i][0] = 0.5 * b[0] + 0.25 * (a[0] + c[0])
            new[i][2] = 0.5 * b[2] + 0.25 * (a[2] + c[2])
        pts = new
    if not changed:
        return poly
    return resample_closed([tuple(p) for p in pts], spacing)


class Q(object):
    """track.query() 결과 (재사용 객체)"""
    __slots__ = ('idx', 't', 'prog', 'd', 'rx', 'rz', 'tx', 'tz', 'ty', 'bank', 'cx', 'cy', 'cz', 'y')

    def __init__(self):
        self.idx = 0
        self.t = 0.0
        self.prog = 0.0
        self.d = 0.0
        self.rx = 0.0
        self.rz = 1.0
        self.tx = 0.0
        self.tz = 1.0
        self.ty = 0.0
        self.bank = 0.0
        self.cx = self.cy = self.cz = 0.0
        self.y = 0.0


class Track(object):
    SH = 12.0   # 갓길(잔디) 폭 - 그 바깥이 벽

    def __init__(self, map_id, outline_only=False):
        self.info = map_info(map_id)
        self.theme = THEMES[self.info['theme']]
        r = Rng(self.info['seed'])
        self.width = 15.0 + int(r() * 5)
        self.hw = self.width / 2.0
        hw, SH = self.hw, self.SH
        self.wall_off = hw + SH - 0.6
        # (가로 오프셋, 높이 변화): 도로 -> 연석 -> 갓길 -> 비탈
        self.rows = [(hw, 0.0), (hw + 0.7, -0.14), (hw + SH, -0.25), (hw + SH + 40.0, -2.5), (hw + SH + 200.0, -30.0)]
        self._centerline(r)
        self.props = []
        self.props_by_seg = {}
        self.pads = []
        self.lamps = []
        self.arches = []
        if not outline_only:
            self._decorate(r)

    # ---- 중심선 -----------------------------------------------------------
    def _centerline(self, r):
        th = self.theme
        K = 7 + int(r() * 8)
        R = 240 + r() * 240
        amp = 0.16 + r() * 0.24
        aspect = 1 + r() * 0.8
        rot = r() * TAU
        ph = (r() * TAU, r() * TAU, r() * TAU)
        elev = th['elev'] * (0.35 + r() * 0.65)
        jit = []
        noise = []
        for i in range(K):
            jit.append((r() - 0.5) * 0.55)
            noise.append(r() * 2 - 1)
        cr, sr = math.cos(rot), math.sin(rot)
        need_sep = 2 * (self.hw + self.SH) + 10.0
        poly = None
        for attempt in range(9):
            k = 0.8 ** attempt
            asp = 1 + (aspect - 1) * k
            pts = []
            for i in range(K):
                a = ((i + jit[i] * k) / K) * TAU
                rad = R * (1 + noise[i] * amp * k)
                x = math.cos(a) * rad * asp
                z = math.sin(a) * rad
                t = a / TAU
                y = elev * (math.sin(TAU * t + ph[0]) * 0.6 + math.sin(2 * TAU * t + ph[1]) * 0.3 + math.sin(3 * TAU * t + ph[2]) * 0.18)
                pts.append((x * cr - z * sr, y, x * sr + z * cr))
            poly = resample_closed(catmull_closed(pts, 40), 4.0)
            poly = relax_corners(poly)
            if max_turn_angle(poly) <= 0.21 and min_separation(poly, 4.0) >= need_sep:
                break
        n0 = len(poly)

        def tang(i):
            i %= n0
            a = poly[(i - 1) % n0]
            b = poly[(i + 1) % n0]
            dx, dz = b[0] - a[0], b[2] - a[2]
            l = math.hypot(dx, dz) or 1.0
            return dx / l, dz / l
        best_i, best_s = 0, 1e9
        for i in range(0, n0, 2):
            t0 = tang(i - 6)
            t1 = tang(i + 6)
            s = 1 - (t0[0] * t1[0] + t0[1] * t1[1])
            if s < best_s:
                best_s, best_i = s, i
        poly = poly[best_i:] + poly[:best_i]
        N = len(poly)
        self.N = N
        self.px = [p[0] for p in poly]
        self.py = [p[1] for p in poly]
        self.pz = [p[2] for p in poly]
        self.tx = [0.0] * N
        self.ty = [0.0] * N
        self.tz = [0.0] * N
        self.rx = [0.0] * N
        self.rz = [0.0] * N
        length = 0.0
        for i in range(N):
            a = (i - 1) % N
            b = (i + 1) % N
            dx = self.px[b] - self.px[a]
            dy = self.py[b] - self.py[a]
            dz = self.pz[b] - self.pz[a]
            l = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
            dx /= l
            dy /= l
            dz /= l
            self.tx[i], self.ty[i], self.tz[i] = dx, dy, dz
            h = math.hypot(dx, dz) or 1.0
            self.rx[i] = -dz / h
            self.rz[i] = dx / h
            length += math.sqrt((self.px[b] - self.px[i]) ** 2 + (self.py[b] - self.py[i]) ** 2 + (self.pz[b] - self.pz[i]) ** 2)
        self.length = length
        self.ds = length / N
        # 뱅킹: 코너 안쪽으로 기울임
        cur = [0.0] * N
        for i in range(N):
            a = (i - 3) % N
            b = (i + 3) % N
            cur[i] = self.tz[a] * self.tx[b] - self.tx[a] * self.tz[b]
        self.bank = [0.0] * N
        for i in range(N):
            s = 0.0
            for k in range(-10, 11):
                s += cur[(i + k) % N]
            self.bank[i] = clamp((-s / 21.0) * 2.4, -0.2, 0.2)
        # 앞쪽 커브 강도 (AI 속도 제어용)
        self.turn = [0.0] * N
        for i in range(N):
            m = 0.0
            for k in range(4, 35, 3):
                j = (i + k) % N
                c = self.tx[i] * self.tx[j] + self.tz[i] * self.tz[j]
                m = max(m, math.acos(clamp(c, -1.0, 1.0)))
            self.turn[i] = m
        self.min_y = min(self.py)
        self.max_y = max(self.py)
        self.bounds = (min(self.px), max(self.px), min(self.pz), max(self.pz))

    # ---- 장식물/패드 ---------------------------------------------------------
    def _decorate(self, r):
        th = self.theme
        N = self.N
        px, pz, py, rx, rz = self.px, self.pz, self.py, self.rx, self.rz
        # 부스트 패드
        count = 6 + int(r() * 5)
        for k in range(count):
            idx = int(((k + 0.5 + (r() - 0.5) * 0.4) / count) * N)
            d = (r() - 0.5) * self.width * 0.5
            if idx < 14 or idx > N - 8:
                continue
            self.pads.append(dict(idx=idx, d=d, half_len=4.5, half_w=2.8))
        # 장식물
        cell = 60.0
        grid = {}
        for i in range(0, N, 2):
            grid.setdefault((int(px[i] // cell), int(pz[i] // cell)), []).append(i)
        min2 = (self.hw + self.SH + 5.0) ** 2

        def free(x, z):
            cx = int(x // cell)
            cz = int(z // cell)
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    lst = grid.get((cx + a, cz + b))
                    if lst:
                        for i in lst:
                            dx = px[i] - x
                            dz = pz[i] - z
                            if dx * dx + dz * dz < min2:
                                return False
            return True
        total = sum(w for _, w in th['props'])
        want = int(round(N * 2.1))
        for _ in range(want):
            i = int(r() * N)
            side = 1 if r() < 0.5 else -1
            lat = self.wall_off + 4 + (r() ** 1.4) * 55
            x = px[i] + rx[i] * lat * side
            z = pz[i] + rz[i] * lat * side
            if not free(x, z):
                continue
            pick = r() * total
            kind = th['props'][0][0]
            for name, w in th['props']:
                pick -= w
                if pick <= 0:
                    kind = name
                    break
            y = py[i] + self.dy_at(lat) - 0.15
            rot = r() * 6.283
            s = 0.7 + r() * 0.9
            r1, r2, r3 = r(), r(), r()
            self.props.append(dict(kind=kind, x=x, y=y, z=z, rot=rot, s=s, r1=r1, r2=r2, r3=r3, seg=i))
        for p in self.props:
            self.props_by_seg.setdefault(p['seg'], []).append(p)
        if th.get('lamps'):
            k = 0
            for i in range(4, N, 7):
                self.lamps.append((i, 1 if k % 2 else -1))
                k += 1
        if th.get('arches'):
            for k in range(4):
                self.arches.append(int(((k + 0.5) / 4) * N + 20) % N)

    # ---- 질의 ---------------------------------------------------------------
    def dy_at(self, off):
        off = abs(off)
        rows = self.rows
        if off <= rows[0][0]:
            return 0.0
        for i in range(1, len(rows)):
            if off <= rows[i][0]:
                a = rows[i - 1]
                b = rows[i]
                return a[1] + (b[1] - a[1]) * ((off - a[0]) / (b[0] - a[0]))
        return rows[-1][1]

    def query(self, x, z, hint, o):
        N = self.N
        px = self.px
        pz = self.pz
        best = 0
        bd = 1e30
        if hint < 0:
            for i in range(N):
                dx = px[i] - x
                dz = pz[i] - z
                d = dx * dx + dz * dz
                if d < bd:
                    bd = d
                    best = i
        else:
            for k in range(-10, 11):
                i = (hint + k) % N
                dx = px[i] - x
                dz = pz[i] - z
                d = dx * dx + dz * dz
                if d < bd:
                    bd = d
                    best = i
        a = best
        b = (best + 1) % N
        ex = px[b] - px[a]
        ez = pz[b] - pz[a]
        t = ((x - px[a]) * ex + (z - pz[a]) * ez) / (ex * ex + ez * ez)
        if t < 0:
            a = (best - 1) % N
            b = best
            ex = px[b] - px[a]
            ez = pz[b] - pz[a]
            t = ((x - px[a]) * ex + (z - pz[a]) * ez) / (ex * ex + ez * ez)
        t = 0.0 if t < 0 else (1.0 if t > 1 else t)
        py, tx, ty, tz, rxs, rzs, bank = self.py, self.tx, self.ty, self.tz, self.rx, self.rz, self.bank
        cx = px[a] + (px[b] - px[a]) * t
        cz = pz[a] + (pz[b] - pz[a]) * t
        cy = py[a] + (py[b] - py[a]) * t
        rx = rxs[a] + (rxs[b] - rxs[a]) * t
        rz = rzs[a] + (rzs[b] - rzs[a]) * t
        rl = math.hypot(rx, rz) or 1.0
        rx /= rl
        rz /= rl
        ttx = tx[a] + (tx[b] - tx[a]) * t
        ttz = tz[a] + (tz[b] - tz[a]) * t
        tl = math.hypot(ttx, ttz) or 1.0
        bk = bank[a] + (bank[b] - bank[a]) * t
        d = (x - cx) * rx + (z - cz) * rz
        hw = self.hw
        o.idx = a
        o.t = t
        o.prog = a + t
        o.d = d
        o.rx = rx
        o.rz = rz
        o.tx = ttx / tl
        o.tz = ttz / tl
        o.ty = ty[a] + (ty[b] - ty[a]) * t
        o.bank = bk
        o.cx = cx
        o.cy = cy
        o.cz = cz
        o.y = cy - math.sin(bk) * (-hw if d < -hw else (hw if d > hw else d)) + self.dy_at(d)
        return o

    def pose_at(self, pf, d=0.0):
        """실수 인덱스 pf, 가로 오프셋 d 의 (x, y, z, heading)"""
        N = self.N
        i = int(math.floor(pf))
        t = pf - i
        a = i % N
        b = (a + 1) % N
        rx = self.rx[a] + (self.rx[b] - self.rx[a]) * t
        rz = self.rz[a] + (self.rz[b] - self.rz[a]) * t
        rl = math.hypot(rx, rz) or 1.0
        rx /= rl
        rz /= rl
        tx = self.tx[a] + (self.tx[b] - self.tx[a]) * t
        tz = self.tz[a] + (self.tz[b] - self.tz[a]) * t
        bk = self.bank[a] + (self.bank[b] - self.bank[a]) * t
        x = self.px[a] + (self.px[b] - self.px[a]) * t + rx * d
        z = self.pz[a] + (self.pz[b] - self.pz[a]) * t + rz * d
        y = self.py[a] + (self.py[b] - self.py[a]) * t - math.sin(bk) * clamp(d, -self.hw, self.hw)
        return x, y, z, math.atan2(tx, tz)

    def spawn_pose(self, slot):
        row = slot // 2
        col = slot % 2
        back = 3.0 + row * 4.6
        d = (1 if col else -1) * self.width * 0.2
        x, y, z, h = self.pose_at(self.N - back / self.ds, d)
        return dict(x=x, y=y, z=z, heading=h, prog=-back / self.ds)

    def surface_normal(self, i):
        """샘플 i 의 도로 법선 (월드 좌표계, 길이 1)"""
        i %= self.N
        cb = math.cos(self.bank[i])
        sb = math.sin(self.bank[i])
        rbx, rby, rbz = self.rx[i] * cb, -sb, self.rz[i] * cb
        tx, ty, tz = self.tx[i], self.ty[i], self.tz[i]
        nx = rby * tz - rbz * ty
        ny = rbz * tx - rbx * tz
        nz = rbx * ty - rby * tx
        l = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        return nx / l, ny / l, nz / l

    def edge_point(self, i, off):
        """샘플 i 에서 가로 오프셋 off(+오른쪽)의 지면 좌표 (x, y, z) - 비탈 포함"""
        i %= self.N
        hw = self.hw
        o = -hw if off < -hw else (hw if off > hw else off)
        return (self.px[i] + self.rx[i] * off,
                self.py[i] - math.sin(self.bank[i]) * o + self.dy_at(off),
                self.pz[i] + self.rz[i] * off)
