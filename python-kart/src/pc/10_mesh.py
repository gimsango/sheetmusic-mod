
# ============================================================================
#  [PC] 절차적 메시 / 텍스처 도우미  (코어 좌표 y-up  ->  Panda3D z-up : (x, y, z) -> (x, -z, y))
# ============================================================================
def PV(x, y, z):
    return (x, -z, y)


def rgbf(c, k=1.0, a=1.0):
    return (min(1.0, c[0] / 255.0 * k), min(1.0, c[1] / 255.0 * k), min(1.0, c[2] / 255.0 * k), a)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / l, v[1] / l, v[2] / l)


class Mesh(object):
    """정점색+법선(+UV) 메시를 모아서 한 번에 Geom 으로 만든다. 좌표는 모두 Panda(z-up)."""

    def __init__(self):
        self.v = []
        self.n = []
        self.c = []
        self.t = []
        self.idx = []

    def add(self, p, n, c, uv=(0.0, 0.0)):
        self.v.append(p)
        self.n.append(n)
        self.c.append(c)
        self.t.append(uv)
        return len(self.v) - 1

    def tri(self, a, b, c):
        self.idx.append((a, b, c))

    def quad(self, p0, p1, p2, p3, col, n=None, uv=None):
        """p0..p3 은 바깥에서 볼 때 반시계 방향"""
        if n is None:
            n = _norm(_cross((p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]), (p3[0] - p0[0], p3[1] - p0[1], p3[2] - p0[2])))
        u = uv or ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
        a = self.add(p0, n, col, u[0])
        b = self.add(p1, n, col, u[1])
        c = self.add(p2, n, col, u[2])
        d = self.add(p3, n, col, u[3])
        self.tri(a, b, c)
        self.tri(a, c, d)

    def box(self, c, h, col, taper=None, skip_bottom=False):
        cx, cy, cz = c
        hx, hy, hz = h
        tx, tz = taper if taper else (1.0, 1.0)
        # 앞(+y) 면만 테이퍼
        fx, fz = hx * tx, hz * tz
        P = lambda x, y, z: (cx + x, cy + y, cz + z)
        # +x
        self.quad(P(hx, -hy, -hz), P(fx, hy, -fz), P(fx, hy, fz), P(hx, -hy, hz), col)
        # -x
        self.quad(P(-fx, hy, -fz), P(-hx, -hy, -hz), P(-hx, -hy, hz), P(-fx, hy, fz), col)
        # +y (앞)
        self.quad(P(fx, hy, -fz), P(-fx, hy, -fz), P(-fx, hy, fz), P(fx, hy, fz), col)
        # -y (뒤)
        self.quad(P(-hx, -hy, -hz), P(hx, -hy, -hz), P(hx, -hy, hz), P(-hx, -hy, hz), col)
        # +z (위)
        self.quad(P(-hx, -hy, hz), P(hx, -hy, hz), P(fx, hy, fz), P(-fx, hy, fz), col)
        if not skip_bottom:
            self.quad(P(-fx, hy, -fz), P(fx, hy, -fz), P(hx, -hy, -hz), P(-hx, -hy, -hz), col)

    def frustum(self, c, r0, r1, length, col, axis='z', seg=10, caps=True, col_top=None):
        """축 방향 원기둥/원뿔대. axis 방향으로 -length/2 (반지름 r0) -> +length/2 (반지름 r1)"""
        cx, cy, cz = c
        h = length / 2.0
        ct = col_top or col

        def frame(a, b, w):
            # a,b = 원 평면 두 축 성분, w = 축 방향 성분  -> (x,y,z)
            if axis == 'z':
                return (cx + a, cy + b, cz + w)
            if axis == 'x':
                return (cx + w, cy + a, cz + b)
            return (cx + a, cy + w, cz + b)

        def vec(a, b, w):
            if axis == 'z':
                return (a, b, w)
            if axis == 'x':
                return (w, a, b)
            return (a, w, b)
        slope = (r0 - r1) / max(length, 1e-6)
        for i in range(seg):
            a0 = TAU * i / seg
            a1 = TAU * (i + 1) / seg
            ca0, sa0, ca1, sa1 = math.cos(a0), math.sin(a0), math.cos(a1), math.sin(a1)
            n0 = _norm(vec(ca0, sa0, slope))
            n1 = _norm(vec(ca1, sa1, slope))
            p0 = frame(ca0 * r0, sa0 * r0, -h)
            p1 = frame(ca1 * r0, sa1 * r0, -h)
            p2 = frame(ca1 * r1, sa1 * r1, h)
            p3 = frame(ca0 * r1, sa0 * r1, h)
            k0 = self.add(p0, n0, col)
            k1 = self.add(p1, n1, col)
            k2 = self.add(p2, n1, ct)
            k3 = self.add(p3, n0, ct)
            if axis == 'x':
                self.tri(k0, k2, k1)
                self.tri(k0, k3, k2)
            else:
                self.tri(k0, k1, k2)
                self.tri(k0, k2, k3)
        if caps:
            for sgn, rr, cc in ((-1, r0, col), (1, r1, ct)):
                if rr <= 1e-6:
                    continue
                nrm = vec(0, 0, sgn)
                ctr = self.add(frame(0, 0, sgn * h), nrm, cc)
                ring = [self.add(frame(math.cos(TAU * i / seg) * rr, math.sin(TAU * i / seg) * rr, sgn * h), nrm, cc) for i in range(seg)]
                for i in range(seg):
                    a, b = ring[i], ring[(i + 1) % seg]
                    if (sgn > 0) == (axis != 'x'):
                        self.tri(ctr, a, b)
                    else:
                        self.tri(ctr, b, a)

    def sphere(self, c, r, col, seg=10, rings=6, scale=(1.0, 1.0, 1.0)):
        cx, cy, cz = c
        sx, sy, sz = scale
        rows = []
        for j in range(rings + 1):
            phi = math.pi * j / rings
            row = []
            for i in range(seg):
                th = TAU * i / seg
                nx, ny, nz = math.sin(phi) * math.cos(th), math.sin(phi) * math.sin(th), math.cos(phi)
                row.append(self.add((cx + nx * r * sx, cy + ny * r * sy, cz + nz * r * sz), (nx, ny, nz), col))
            rows.append(row)
        for j in range(rings):
            for i in range(seg):
                a, b = rows[j][i], rows[j][(i + 1) % seg]
                c2, d = rows[j + 1][i], rows[j + 1][(i + 1) % seg]
                self.tri(a, c2, b)
                self.tri(b, c2, d)

    def octa(self, c, r, col, scale=(1.0, 1.0, 1.0)):
        cx, cy, cz = c
        sx, sy, sz = scale
        P = [(cx + r * sx, cy, cz), (cx - r * sx, cy, cz), (cx, cy + r * sy, cz), (cx, cy - r * sy, cz), (cx, cy, cz + r * sz), (cx, cy, cz - r * sz)]
        faces = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
        for a, b, d in faces:
            self.quad(P[a], P[b], P[d], P[d], col)

    def ring(self, c, r_in, r_out, col, axis='x', seg=14, width=0.02):
        """납작한 고리 (바퀴 림 등) - 두께 width"""
        self.frustum(c, r_out, r_out, width, col, axis, seg, False)
        self.frustum(c, r_in, r_in, width, col, axis, seg, False)

    def annulus(self, c, r_in, r_out, col, axis='x', seg=14):
        """평평한 고리(양면). axis 방향을 바라보는 면"""
        cx, cy, cz = c
        nrm = {'x': (1.0, 0.0, 0.0), 'y': (0.0, 1.0, 0.0), 'z': (0.0, 0.0, 1.0)}[axis]

        def pt(a, r):
            ca, sa = math.cos(a) * r, math.sin(a) * r
            if axis == 'x':
                return (cx, cy + ca, cz + sa)
            if axis == 'y':
                return (cx + ca, cy, cz + sa)
            return (cx + ca, cy + sa, cz)
        for i in range(seg):
            a0, a1 = TAU * i / seg, TAU * (i + 1) / seg
            p = [pt(a0, r_in), pt(a0, r_out), pt(a1, r_out), pt(a1, r_in)]
            self.quad(p[0], p[1], p[2], p[3], col, n=nrm)
            self.quad(p[3], p[2], p[1], p[0], col, n=(-nrm[0], -nrm[1], -nrm[2]))

    def disc(self, c, r, col, axis='x', seg=14):
        self.annulus(c, 0.0, r, col, axis, seg)

    def spoke(self, c, ang, r, width, col, axis='x'):
        """원판 면 위의 얇은 바(양면)"""
        cx, cy, cz = c
        ca, sa = math.cos(ang), math.sin(ang)
        pa, pb = -sa * width / 2, ca * width / 2

        def P(t, k):
            u, v = ca * t + pa * k, sa * t + pb * k
            return (cx, cy + u, cz + v) if axis == 'x' else (cx + u, cy, cz + v)
        nrm = (1.0, 0.0, 0.0) if axis == 'x' else (0.0, 1.0, 0.0)
        self.quad(P(0, -1), P(r, -1), P(r, 1), P(0, 1), col, n=nrm)
        self.quad(P(0, 1), P(r, 1), P(r, -1), P(0, -1), col, n=(-nrm[0], -nrm[1], -nrm[2]))

    def node(self, name, textured=False):
        fmt = GeomVertexFormat.getV3n3cpt2()
        vd = GeomVertexData(name, fmt, Geom.UHStatic)
        vd.setNumRows(len(self.v))
        vw = GeomVertexWriter(vd, 'vertex')
        nw = GeomVertexWriter(vd, 'normal')
        cw = GeomVertexWriter(vd, 'color')
        tw = GeomVertexWriter(vd, 'texcoord')
        for i in range(len(self.v)):
            p = self.v[i]
            vw.addData3(p[0], p[1], p[2])
            q = self.n[i]
            nw.addData3(q[0], q[1], q[2])
            c = self.c[i]
            cw.addData4(c[0], c[1], c[2], c[3])
            t = self.t[i]
            tw.addData2(t[0], t[1])
        prim = GeomTriangles(Geom.UHStatic)
        for a, b, c in self.idx:
            prim.addVertices(a, b, c)
        geom = Geom(vd)
        geom.addPrimitive(prim)
        gn = GeomNode(name)
        gn.addGeom(geom)
        return gn

    def attach(self, parent, name, textured=False):
        return parent.attachNewNode(self.node(name, textured))


# ---------------------------------------------------------------------------
#  텍스처 (코드로 생성)
# ---------------------------------------------------------------------------
def make_texture(name, w, h, data, fmt='RGB', repeat=True):
    t = Texture(name)
    t.setup2dTexture(w, h, Texture.T_unsigned_byte, Texture.F_rgba if fmt == 'RGBA' else Texture.F_rgb)
    t.setRamImageAs(bytes(data), fmt)
    if repeat:
        t.setWrapU(Texture.WM_repeat)
        t.setWrapV(Texture.WM_repeat)
    else:
        t.setWrapU(Texture.WM_clamp)
        t.setWrapV(Texture.WM_clamp)
    t.setMinfilter(Texture.FT_linear_mipmap_linear)
    t.setMagfilter(Texture.FT_linear)
    try:
        t.setAnisotropicDegree(4)
    except Exception:
        pass
    return t


def tex_asphalt(road_rgb, night, seed=1):
    w = h = 256
    rnd = Rng(seed)
    buf = bytearray(w * h * 3)
    for y in range(h):
        for x in range(w):
            n = (rnd() - 0.5) * 22
            r, g, b = road_rgb[0] + n, road_rgb[1] + n, road_rgb[2] + n
            u = x / float(w)
            v = y / float(h)
            line = None
            if u < 0.045 and u > 0.02 or u > 0.955 and u < 0.98:
                line = (240, 240, 240)
            elif 0.488 < u < 0.512 and v < 0.5:
                line = (120, 220, 255) if night else (245, 197, 24)
            if line:
                k = 0.88 + 0.12 * rnd()
                r, g, b = line[0] * k, line[1] * k, line[2] * k
            o = (y * w + x) * 3
            buf[o] = int(max(0, min(255, r)))
            buf[o + 1] = int(max(0, min(255, g)))
            buf[o + 2] = int(max(0, min(255, b)))
    return make_texture('asphalt', w, h, buf)


def tex_ground(c0, c1, seed=2):
    w = h = 128
    rnd = Rng(seed)
    low = [[rnd() for _ in range(8)] for _ in range(8)]
    buf = bytearray(w * h * 3)
    for y in range(h):
        fy = y / 16.0
        iy = int(fy) % 8
        iy1 = (iy + 1) % 8
        ty = fy - int(fy)
        for x in range(w):
            fx = x / 16.0
            ix = int(fx) % 8
            ix1 = (ix + 1) % 8
            tx = fx - int(fx)
            a = low[iy][ix] * (1 - tx) + low[iy][ix1] * tx
            b = low[iy1][ix] * (1 - tx) + low[iy1][ix1] * tx
            m = a * (1 - ty) + b * ty
            n = 1 + (rnd() - 0.5) * 0.12
            o = (y * w + x) * 3
            for k in range(3):
                buf[o + k] = int(max(0, min(255, (c0[k] + (c1[k] - c0[k]) * m) * n)))
    return make_texture('ground', w, h, buf)


def tex_glow(name='glow', size=64, soft=2.0):
    buf = bytearray(size * size * 4)
    c = (size - 1) / 2.0
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c) / c
            a = max(0.0, 1.0 - d) ** soft
            o = (y * size + x) * 4
            buf[o] = buf[o + 1] = buf[o + 2] = 255
            buf[o + 3] = int(a * 255)
    return make_texture(name, size, size, buf, 'RGBA', False)


def tex_pad():
    w, h = 64, 128
    buf = bytearray(w * h * 3)
    for y in range(h):
        for x in range(w):
            o = (y * w + x) * 3
            col = (8, 24, 60)
            for k in range(3):
                cy_ = 18 + k * 36
                # 위로 향한 화살표(셰브론)
                dy = (y - cy_)
                dx = abs(x - w / 2.0)
                if 0 <= dy - dx * 0.55 <= 11 and dx < 28:
                    col = (25, 230, 255) if k % 2 == 0 else (255, 225, 74)
            if x < 3 or x > w - 4 or y < 3 or y > h - 4:
                col = (25, 230, 255)
            buf[o], buf[o + 1], buf[o + 2] = col
    return make_texture('pad', w, h, buf, 'RGB', False)
