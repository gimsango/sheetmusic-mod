
# ============================================================================
#  [PC] 월드 생성: 하늘/조명/안개/트랙/연석/벽/갓길/장식물/패드/가로등/게이트
# ============================================================================
def mesh_tube(m, path, radius, col, seg=6):
    """3D 경로를 따라가는 튜브 (아치 등)"""
    rings = []
    n = len(path)
    for k in range(n):
        p = path[k]
        a = path[max(0, k - 1)]
        b = path[min(n - 1, k + 1)]
        t = _norm((b[0] - a[0], b[1] - a[1], b[2] - a[2]))
        ref = (0.0, 0.0, 1.0) if abs(t[2]) < 0.9 else (1.0, 0.0, 0.0)
        u = _norm(_cross(t, ref))
        v = _cross(t, u)
        ring = []
        for i in range(seg):
            ang = TAU * i / seg
            nx = u[0] * math.cos(ang) + v[0] * math.sin(ang)
            ny = u[1] * math.cos(ang) + v[1] * math.sin(ang)
            nz = u[2] * math.cos(ang) + v[2] * math.sin(ang)
            ring.append(m.add((p[0] + nx * radius, p[1] + ny * radius, p[2] + nz * radius), (nx, ny, nz), col))
        rings.append(ring)
    for k in range(n - 1):
        for i in range(seg):
            a, b = rings[k][i], rings[k][(i + 1) % seg]
            c, d = rings[k + 1][i], rings[k + 1][(i + 1) % seg]
            m.tri(a, b, c)
            m.tri(b, d, c)


def blade(m, base, tip, width, col, droop=0.0):
    """야자수 잎: 밑동 -> 끝 으로 뻗은 마름모 (양면)"""
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    l = math.hypot(dx, dy) or 1.0
    sx, sy = -dy / l * width, dx / l * width
    mid = (base[0] + dx * 0.45, base[1] + dy * 0.45, base[2] + (tip[2] - base[2]) * 0.3 + 0.25)
    pts = [(base[0], base[1], base[2]), (mid[0] + sx, mid[1] + sy, mid[2]), (tip[0], tip[1], tip[2]), (mid[0] - sx, mid[1] - sy, mid[2])]
    m.quad(pts[0], pts[1], pts[2], pts[3], col)
    m.quad(pts[3], pts[2], pts[1], pts[0], col)


class World(object):
    def __init__(self, app, track):
        self.app = app
        self.track = track
        self.th = track.theme
        self.night = bool(self.th.get('night'))
        self.root = app.render.attachNewNode('world')
        self.lights = []
        self.rnd = Rng(track.info['seed'] ^ 0xABCDEF)
        self._lighting()
        self._fog()
        self._sky()
        self._far_ground()
        self._road()
        self._kerbs()
        self._ground()
        self._walls()
        self._start()
        self._pads()
        self._props()
        if self.th.get('lamps'):
            self._lamps()
        if self.th.get('arches'):
            self._arches()

    # ---- 조명 / 안개 ---------------------------------------------------------------
    def _lighting(self):
        th = self.th
        hs = th['hemi']
        sky_c, gr_c = hex_rgb(hs[0]), hex_rgb(hs[1])
        mc = mix_rgb(sky_c, gr_c, 0.4)
        k = min(1.3, hs[2]) * (0.66 if not self.night else 1.25)
        amb = AmbientLight('amb')
        amb.setColor(Vec4(mc[0] / 255.0 * k, mc[1] / 255.0 * k, mc[2] / 255.0 * k, 1))
        sun = DirectionalLight('sun')
        sc = hex_rgb(th['sun'])
        si = th['sun_i'] * (0.34 if not self.night else 0.3)
        sun.setColor(Vec4(sc[0] / 255.0 * si, sc[1] / 255.0 * si, sc[2] / 255.0 * si, 1))
        sd = th['sun_dir']
        self.sun_dir = _norm(PV(*sd))
        a = self.root.attachNewNode(amb)
        s = self.root.attachNewNode(sun)
        s.lookAt(Point3(-self.sun_dir[0], -self.sun_dir[1], -self.sun_dir[2]))
        self.app.render.setLight(a)
        self.app.render.setLight(s)
        self.lights = [a, s]

    def _fog(self):
        th = self.th
        fc = hex_rgb(th['fog'])
        fog = Fog('fog')
        fog.setColor(fc[0] / 255.0, fc[1] / 255.0, fc[2] / 255.0)
        fog.setMode(Fog.MExponentialSquared)
        fog.setExpDensity(th['fog_d'])
        self.fog = fog
        self.app.render.setFog(fog)
        self.app.setBackgroundColor(fc[0] / 255.0, fc[1] / 255.0, fc[2] / 255.0)

    # ---- 하늘 ------------------------------------------------------------------------
    def _sky(self):
        th = self.th
        top, bot = hex_rgb(th['sky_top']), hex_rgb(th['sky_bot'])
        fog = hex_rgb(th['fog'])
        self.sky = self.root.attachNewNode('sky')
        m = Mesh()
        R = 3000.0
        seg, rings = 28, 16
        rows = []
        for j in range(rings + 1):
            phi = math.pi * j / rings            # 0 = 천정, pi = 천저
            row = []
            for i in range(seg):
                th_ = TAU * i / seg
                x, y, z = math.sin(phi) * math.cos(th_), math.sin(phi) * math.sin(th_), math.cos(phi)
                t = clamp(z * 1.6 + 0.12, 0.0, 1.0) ** 0.7
                c = mix_rgb(bot, top, t)
                row.append(m.add((x * R, y * R, z * R), (-x, -y, -z), rgbf(c)))
            rows.append(row)
        for j in range(rings):
            for i in range(seg):
                a, b = rows[j][i], rows[j][(i + 1) % seg]
                c, d = rows[j + 1][i], rows[j + 1][(i + 1) % seg]
                m.tri(a, b, c)
                m.tri(b, d, c)
        dome = m.attach(self.sky, 'dome')
        dome.setTwoSided(True)
        for np_ in (dome,):
            np_.setLightOff()
            np_.setFogOff()
            np_.setDepthWrite(False)
            np_.setDepthTest(False)
            np_.setBin('background', 0)
        # 태양/달
        glow = tex_glow('sunglow', 64, 1.5)
        cm = CardMaker('sun')
        cm.setFrame(-1, 1, -1, 1)
        sun = self.sky.attachNewNode(cm.generate())
        sun.setTexture(glow)
        sc = hex_rgb(th['sun'])
        sun.setColor(sc[0] / 255.0, sc[1] / 255.0, sc[2] / 255.0, 1)
        sun.setTransparency(TransparencyAttrib.MAlpha)
        sun.setBillboardPointEye()
        sun.setPos(self.sun_dir[0] * 2700, self.sun_dir[1] * 2700, self.sun_dir[2] * 2700)
        sun.setScale(260 if not self.night else 150)
        for n_ in (sun,):
            n_.setLightOff()
            n_.setFogOff()
            n_.setDepthWrite(False)
            n_.setBin('background', 2)
        core = self.sky.attachNewNode(cm.generate())
        core.setTexture(tex_glow('suncore', 32, 0.4))
        core.setColor(1, 1, 0.95, 1)
        core.setTransparency(TransparencyAttrib.MAlpha)
        core.setBillboardPointEye()
        core.setPos(self.sun_dir[0] * 2690, self.sun_dir[1] * 2690, self.sun_dir[2] * 2690)
        core.setScale(70 if not self.night else 60)
        core.setLightOff()
        core.setFogOff()
        core.setDepthWrite(False)
        core.setBin('background', 3)
        # 별
        if self.night:
            fmt = GeomVertexFormat.getV3cp()
            vd = GeomVertexData('stars', fmt, Geom.UHStatic)
            vw = GeomVertexWriter(vd, 'vertex')
            cw = GeomVertexWriter(vd, 'color')
            n = 1500
            for _ in range(n):
                u = self.rnd() * TAU
                v = math.acos(self.rnd() * 0.97 + 0.03)
                r = 2900.0
                vw.addData3(r * math.sin(v) * math.cos(u), r * math.sin(v) * math.sin(u), r * math.cos(v))
                b = 0.45 + self.rnd() * 0.55
                cw.addData4(b, b, min(1.0, b + 0.08), 1)
            prim = GeomPoints(Geom.UHStatic)
            prim.addNextVertices(n)
            geom = Geom(vd)
            geom.addPrimitive(prim)
            gn = GeomNode('starsgn')
            gn.addGeom(geom)
            st = self.sky.attachNewNode(gn)
            st.setRenderModeThickness(2.2)
            st.setLightOff()
            st.setFogOff()
            st.setDepthWrite(False)
            st.setBin('background', 1)
        # 구름
        nc = int(14 * th.get('clouds', 0))
        if nc:
            m = Mesh()
            for _ in range(nc):
                a = self.rnd() * TAU
                d = 1100 + self.rnd() * 1900
                z = 380 + self.rnd() * 420
                s = 70 + self.rnd() * 110
                for j in range(4):
                    m.sphere((math.cos(a) * d + (j - 1.5) * s * 0.9, math.sin(a) * d, z + (j % 2) * 8), s * 0.55, rgbf(th.get('cloud') or (255, 255, 255), 1.0, 0.88),
                             seg=8, rings=4, scale=(1.0, 0.7, 0.34))
            cl = m.attach(self.sky, 'clouds')
            cl.setTransparency(TransparencyAttrib.MAlpha)
            cl.setLightOff()
            cl.setFogOff()
            cl.setDepthWrite(False)
            cl.setBin('background', 4)
        if th.get('aurora'):
            self._aurora()
        self._horizon()

    def _aurora(self):
        """오로라: 하늘에 반투명 띠 3줄"""
        m = Mesh()
        for band, col in enumerate(((0.3, 1.0, 0.68, 0.5), (0.36, 0.82, 1.0, 0.4), (0.75, 0.48, 1.0, 0.32))):
            ph, z0 = self.rnd() * TAU, 560 + band * 210
            seg = 90
            prev = None
            for i in range(seg + 1):
                a = TAU * i / seg
                r = 2800.0
                zz = z0 + math.sin(a * 3 + ph) * 90 + math.sin(a * 7 + ph * 2) * 35
                th_ = 230 + 80 * math.sin(a * 5 + ph)
                lo = m.add((math.cos(a) * r, math.sin(a) * r, zz), (-math.cos(a), -math.sin(a), 0), (col[0], col[1], col[2], col[3]))
                hi = m.add((math.cos(a) * r, math.sin(a) * r, zz + th_), (-math.cos(a), -math.sin(a), 0), (col[0], col[1], col[2], 0.0))
                if prev is not None:
                    m.tri(prev[0], lo, hi)
                    m.tri(prev[0], hi, prev[1])
                prev = (lo, hi)
        au = m.attach(self.sky, 'aurora')
        au.setTwoSided(True)
        au.setLightOff()
        au.setFogOff()
        au.setTransparency(TransparencyAttrib.MAlpha)
        au.setDepthWrite(False)
        au.setDepthTest(False)
        au.setBin('background', 1)

    def _horizon(self):
        """360도 지평선: 코어 horizon_layers 정의를 원통면에 그린다 (배경 칸에서 순서대로 -> 겹침 깜빡임 없음)"""
        th = self.th
        m = Mesh()

        def P(rad, a, h):
            t = a * TAU
            return (math.cos(t) * rad, math.sin(t) * rad, h)

        def N(a):
            t = a * TAU
            return (-math.cos(t), -math.sin(t), 0.2)

        def fan(rad, col, pts):
            c = rgbf(col)
            ca = sum(q[0] for q in pts) / len(pts)
            cz = sum(q[1] for q in pts) / len(pts)
            ctr = m.add(P(rad, ca, cz), N(ca), c)
            idx = [m.add(P(rad, a, h), N(a), c) for a, h in pts]
            for i in range(len(idx)):
                m.tri(ctr, idx[i], idx[(i + 1) % len(idx)])
        for rad, items in horizon_layers(th, self.track.info['seed']):
            for it in items:
                t = it[0]
                if t == 'ridge':
                    col, top, hs = it[1], it[2], it[3]
                    n = len(hs) - 1
                    rows = []
                    for i in range(n + 1):
                        a = i / float(n)
                        if top:
                            rows.append((m.add(P(rad, a, -300.0), N(a), rgbf(col, 0.82)), m.add(P(rad, a, hs[i] * 0.72), N(a), rgbf(col, 1.05)),
                                         m.add(P(rad, a, hs[i]), N(a), rgbf(top))))
                        else:
                            rows.append((m.add(P(rad, a, -300.0), N(a), rgbf(col, 0.82)), m.add(P(rad, a, hs[i]), N(a), rgbf(col, 1.12))))
                    for i in range(n):
                        r0, r1 = rows[i], rows[i + 1]
                        for k in range(len(r0) - 1):
                            m.tri(r0[k], r1[k], r1[k + 1])
                            m.tri(r0[k], r1[k + 1], r0[k + 1])
                elif t == 'poly':
                    fan(rad, it[1], it[2])
                elif t == 'disc':
                    col, a, h, r = it[1], it[2], it[3], it[4]
                    fan(rad, col, [(a + r * math.cos(TAU * k / 18) / (TAU * rad), h + r * math.sin(TAU * k / 18)) for k in range(18)])
                elif t == 'ring':
                    col, a, h, rx, ry, w = it[1], it[2], it[3], it[4], it[5], it[6]
                    c = rgbf(col)
                    seg = 40
                    outer = [m.add(P(rad, a + rx * math.cos(TAU * k / seg) / (TAU * rad), h + ry * math.sin(TAU * k / seg)), N(a), c) for k in range(seg)]
                    inner = [m.add(P(rad, a + (rx - w) * math.cos(TAU * k / seg) / (TAU * rad), h + (ry - w) * math.sin(TAU * k / seg)), N(a), c) for k in range(seg)]
                    for k in range(seg):
                        k2 = (k + 1) % seg
                        m.tri(outer[k], outer[k2], inner[k2])
                        m.tri(outer[k], inner[k2], inner[k])
                elif t == 'line':
                    col, pts, w = it[1], it[2], it[3]
                    c = rgbf(col, 1.3)
                    for i in range(len(pts) - 1):
                        (a0, h0), (a1, h1) = pts[i], pts[i + 1]
                        q = [m.add(P(rad - 1.0, a0, h0 - w / 2), N(a0), c), m.add(P(rad - 1.0, a1, h1 - w / 2), N(a1), c),
                             m.add(P(rad - 1.0, a1, h1 + w / 2), N(a1), c), m.add(P(rad - 1.0, a0, h0 + w / 2), N(a0), c)]
                        m.tri(q[0], q[1], q[2])
                        m.tri(q[0], q[2], q[3])
        hz = m.attach(self.sky, 'horizon')
        hz.setTwoSided(True)
        hz.setLightOff()
        hz.setFogOff()
        hz.setDepthWrite(False)
        hz.setDepthTest(False)
        hz.setBin('background', 6)

    def _far_ground(self):
        tr = self.track
        cm = CardMaker('far')
        cm.setFrame(-9000, 9000, -9000, 9000)
        far = self.root.attachNewNode(cm.generate())
        far.setP(-90)
        far.setZ(tr.min_y - 62)
        fc = hex_rgb(self.th['far'])
        far.setColor(fc[0] / 255.0, fc[1] / 255.0, fc[2] / 255.0, 1)
        far.setLightOff()

    # ---- 트랙 -------------------------------------------------------------------------
    def _up(self, k):
        n = self.track.surface_normal(k)
        return (n[0], -n[2], n[1])

    def _road(self):
        tr = self.track
        N, hw = tr.N, tr.hw
        m = Mesh()
        dist = 0.0
        for i in range(N + 1):
            k = i % N
            n = self._up(k)
            m.add(PV(*tr.edge_point(k, -hw)), n, (1, 1, 1, 1), (0.0, dist / 24.0))
            m.add(PV(*tr.edge_point(k, hw)), n, (1, 1, 1, 1), (1.0, dist / 24.0))
            dist += tr.ds
        for i in range(N):
            a = 2 * i
            m.tri(a, a + 1, a + 3)
            m.tri(a, a + 3, a + 2)
        np_ = m.attach(self.root, 'road')
        np_.setTexture(tex_asphalt(shade_rgb(hex_rgb(self.th['road']), 1.9 if self.night else 1.0), self.night, self.track.info['seed'] & 0xffff))
        np_.setTwoSided(True)
        self.road_np = np_

    def _kerbs(self):
        tr = self.track
        N, hw = tr.N, tr.hw
        m = Mesh()
        kb = self.th.get('kerb') or ((216, 35, 42), (240, 240, 240))
        red, white = rgbf(kb[0]), rgbf(kb[1])
        amb = 0.8 if self.night else 1.0
        for side in (-1, 1):
            for i in range(N):
                k0, k1 = i, (i + 1) % N
                col = red if (i // 2) & 1 else white
                col = (col[0] * amb, col[1] * amb, col[2] * amb, 1.0)
                p0 = PV(*tr.edge_point(k0, side * (hw - 0.1)))
                p1 = PV(*tr.edge_point(k0, side * (hw + 1.4)))
                p2 = PV(*tr.edge_point(k1, side * (hw + 1.4)))
                p3 = PV(*tr.edge_point(k1, side * (hw - 0.1)))
                lift = lambda p: (p[0], p[1], p[2] + 0.03)
                m.quad(lift(p0), lift(p1), lift(p2), lift(p3), col, n=self._up(k0))
        np_ = m.attach(self.root, 'kerbs')
        np_.setTwoSided(True)
        np_.setDepthOffset(1)

    def _ground(self):
        tr = self.track
        N, hw, SH = tr.N, tr.hw, tr.SH
        th = self.th
        g0, g1 = hex_rgb(th['ground'][0]), hex_rgb(th['ground'][1])
        amb = 1.9 if self.night else 1.0
        offs = [hw + 1.4, hw + SH, hw + SH + 40.0, hw + SH + 200.0]
        m = Mesh()
        dist = 0.0
        for i in range(N):
            k0, k1 = i, (i + 1) % N
            cA = rgbf(g0 if (i // 4) & 1 else g1, amb)
            for side in (-1, 1):
                for r in range(len(offs) - 1):
                    o0, o1 = offs[r], offs[r + 1]
                    a0 = PV(*tr.edge_point(k0, side * o0))
                    b0 = PV(*tr.edge_point(k0, side * o1))
                    b1 = PV(*tr.edge_point(k1, side * o1))
                    a1 = PV(*tr.edge_point(k1, side * o0))
                    uv = ((o0 / 12.0, dist / 12.0), (o1 / 12.0, dist / 12.0), (o1 / 12.0, (dist + tr.ds) / 12.0), (o0 / 12.0, (dist + tr.ds) / 12.0))
                    col = cA if r < 2 else (cA[0] * 0.8, cA[1] * 0.8, cA[2] * 0.8, 1.0)
                    m.quad(a0, b0, b1, a1, col, n=self._up(k0), uv=uv)
            dist += tr.ds
        np_ = m.attach(self.root, 'ground')
        np_.setTexture(tex_ground((255, 255, 255), (205, 205, 205), self.track.info['seed'] & 0xffff))
        np_.setTwoSided(True)

    def _walls(self):
        tr = self.track
        N, wo = tr.N, tr.wall_off
        th = self.th
        w0, w1 = hex_rgb(th['wall'][0]), hex_rgb(th['wall'][1])
        glow = bool(th.get('glow_wall'))
        m = Mesh()
        for side in (-1, 1):
            for i in range(N):
                k0, k1 = i, (i + 1) % N
                col = rgbf(w0 if (i // 2) & 1 else w1, 1.15 if glow else (0.8 if self.night else 1.0))
                b0 = PV(*tr.edge_point(k0, side * wo))
                b1 = PV(*tr.edge_point(k1, side * wo))
                t0 = (b0[0], b0[1], b0[2] + 1.3)
                t1 = (b1[0], b1[1], b1[2] + 1.3)
                nrm = (-tr.rx[k0] * side, tr.rz[k0] * side, 0.0)      # 도로 안쪽
                m.quad(b0, b1, t1, t0, col, n=nrm)
                # 윗면
                m.quad(t0, t1, (t1[0] - nrm[0] * 0.5, t1[1] - nrm[1] * 0.5, t1[2]), (t0[0] - nrm[0] * 0.5, t0[1] - nrm[1] * 0.5, t0[2]), rgbf((226, 226, 232), 1.0 if not self.night else 0.8), n=(0, 0, 1))
        np_ = m.attach(self.root, 'walls')
        np_.setTwoSided(True)
        if glow:
            np_.setLightOff()

    def _start(self):
        tr = self.track
        hw = tr.hw
        m = Mesh()
        cols = 8
        for r in range(2):
            for c in range(cols):
                f0, f1 = r * 0.5, (r + 1) * 0.5
                x, y, z, h = tr.pose_at(f0 - 0.0, 0)
                pts = []
                for (ff, cc) in ((f0, c), (f0, c + 1), (f1, c + 1), (f1, c)):
                    xx, yy, zz, _h = tr.pose_at(ff, -hw + 2 * hw * cc / cols)
                    pts.append(PV(xx, yy + 0.05, zz))
                col = (0.08, 0.08, 0.09, 1) if (r + c) % 2 else (0.96, 0.96, 0.96, 1)
                m.quad(pts[0], pts[1], pts[2], pts[3], col, n=self._up(0))
        np_ = m.attach(self.root, 'startline')
        np_.setTwoSided(True)
        np_.setDepthOffset(2)
        # 게이트
        gate = self.root.attachNewNode('gate')
        gm = Mesh()
        hwg = hw + 1.6
        for s in (-1, 1):
            gm.box((s * hwg, 0, 5), (0.7, 0.7, 5), (0.17, 0.18, 0.23, 1))
        gm.box((0, 0, 9.6), (hw + 2.2, 0.45, 1.2), (0.7, 0.14, 0.17, 1))
        gm.attach(gate, 'gatemesh')
        tn = TextNode('banner')
        tn.setText('START / FINISH')
        tn.setAlign(TextNode.ACenter)
        tn.setTextColor(1, 1, 1, 1)
        if self.app.font_en is not None:
            tn.setFont(self.app.font_en)
        t_np = gate.attachNewNode(tn)
        t_np.setPos(0, -0.5, 9.2)
        t_np.setScale(1.7)
        t_np.setLightOff()
        t2 = gate.attachNewNode(tn)
        t2.setPos(0, 0.5, 9.2)
        t2.setH(180)
        t2.setScale(1.7)
        t2.setLightOff()
        x, y, z, h = tr.pose_at(0.0, 0.0)
        gate.setPos(*PV(x, y, z))
        gate.setH(math.degrees(h) + 180)
        gate.setP(0)

    def _pads(self):
        tr = self.track
        tex = tex_pad()
        for p in tr.pads:
            idx, d = p['idx'], p['d']
            hl = p['half_len'] / tr.ds
            hwp = p['half_w']
            pts = []
            for (ff, uu) in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
                x, y, z, _h = tr.pose_at(idx + ff * hl, d + uu * hwp)
                pts.append(PV(x, y + 0.07, z))
            m = Mesh()
            m.quad(pts[0], pts[1], pts[2], pts[3], (1, 1, 1, 1), n=self._up(idx), uv=((0, 0), (1, 0), (1, 1), (0, 1)))
            np_ = m.attach(self.root, 'pad')
            np_.setTexture(tex)
            np_.setLightOff()
            np_.setTwoSided(True)
            np_.setDepthOffset(3)

    # ---- 장식물 -----------------------------------------------------------------------------
    def _proto(self, kind, var):
        """장식물 원형 메시 (바이옴 팔레트로 색칠). 반환: (빛 받는 메시, 발광 메시|None)"""
        th = self.th
        m = Mesh()
        g = Mesh()
        rc = (hex_rgb(th['rock'][0]), hex_rgb(th['rock'][1]))
        leaf = th.get('leaf') or [(47, 127, 53), (58, 140, 58), (74, 160, 74), (90, 170, 80)]
        trunk = th.get('trunk') or (90, 59, 34)
        acc = th.get('accent') or [(255, 43, 214), (25, 230, 255), (255, 225, 74), (120, 255, 150)]
        flower = th.get('flower') or [(255, 224, 64), (255, 96, 128), (255, 255, 255), (176, 123, 255)]
        night = self.night
        if kind == 'pine':
            m.frustum((0, 0, 1.5), 0.5, 0.35, 3.0, rgbf(trunk), 'z', 6)
            if th.get('snowy'):
                cols = [mix_rgb(leaf[0], (240, 246, 252), 0.15), mix_rgb(leaf[1], (240, 246, 252), 0.35), (242, 247, 251)]
            else:
                cols = [leaf[0], leaf[1], leaf[2]]
            for (z, r, ln), c in zip(((5.0, 3.4, 5.0), (7.6, 2.7, 4.6), (10.0, 1.9, 4.0)), cols):
                m.frustum((0, 0, z), r, 0.0, ln, rgbf(c), 'z', 7, True)
        elif kind == 'roundtree':
            c = leaf[var % len(leaf)]
            m.frustum((0, 0, 2.0), 0.65, 0.45, 4.0, rgbf(trunk), 'z', 6)
            m.sphere((0, 0, 6.5), 3.4, rgbf(c), 9, 6, (1, 1, 0.9))
            m.sphere((1.6, 0.8, 5.3), 2.2, rgbf(c, 0.88), 8, 5)
            if th.get('snowy'):
                m.sphere((0, 0, 8.6), 2.2, (0.94, 0.96, 0.99, 1), 8, 4, (1, 1, 0.45))
        elif kind == 'bush':
            m.sphere((0, 0, 0.8), 1.6, rgbf(leaf[0]), 8, 5, (1.2, 1.1, 0.7))
            m.sphere((1.3, 0.5, 0.5), 1.1, rgbf(leaf[1]), 7, 4)
        elif kind == 'cactus':
            gc = rgbf(th.get('cactus') or (59, 138, 74))
            m.frustum((0, 0, 3.0), 0.8, 0.7, 6.0, gc, 'z', 8)
            m.frustum((0.9, 0, 2.4), 0.4, 0.4, 1.4, gc, 'x', 6)
            m.frustum((1.7, 0, 3.5), 0.4, 0.4, 2.4, gc, 'z', 6)
            m.frustum((-0.6, 0, 3.6), 0.4, 0.4, 1.2, gc, 'x', 6)
            m.frustum((-1.3, 0, 4.4), 0.4, 0.4, 1.8, gc, 'z', 6)
        elif kind == 'rock':
            m.sphere((0, 0, 0.9), 2.2, rgbf(rc[0]), 7, 4, (1.3, 1.1, 0.8))
            m.sphere((2.3, 0.7, 0.5), 1.3, rgbf(rc[1]), 6, 4, (1.0, 1.0, 0.8))
        elif kind == 'mesa':
            mc = th.get('mesa') or [(176, 74, 40), (199, 101, 58), (168, 68, 36), (224, 160, 96)]
            for (z, r0, r1, ln), c in zip(((6, 9, 7, 12), (15, 7, 6.2, 6), (20.5, 6.2, 5.4, 5), (23.6, 5.6, 5.6, 1.2)), (mc[0], mc[1], mc[2], mc[3])):
                m.frustum((0, 0, z), r0, r1, ln, rgbf(c), 'z', 7)
        elif kind == 'palm':
            m.frustum((0.3, 0, 4.2), 0.5, 0.28, 8.4, rgbf(mix_rgb(trunk, (200, 170, 110), 0.45)), 'z', 6)
            for k in range(7):
                a = k * 0.898
                blade(m, (0.3, 0, 8.4), (0.3 + math.cos(a) * 4.6, math.sin(a) * 4.6, 6.7), 0.75, rgbf(leaf[k % len(leaf)]))
            m.sphere((0.3, 0, 8.2), 0.45, rgbf(shade_rgb(trunk, 0.9)), 6, 4)
        elif kind == 'building':
            m.box((0, 0, 0.5), (0.5, 0.5, 0.5), rgbf((58, 56, 108)))
            for z, c in ((0.9, acc[0]), (0.62, acc[1 % len(acc)]), (0.34, acc[2 % len(acc)]), (0.98, acc[0])):
                g.box((0, 0, z), (0.512, 0.512, 0.008), rgbf(c, 1.6))
        elif kind == 'crystal':
            col = th.get('crystal') or (255, 43, 214)
            g.octa((0, 0, 3.0), 1.2, rgbf(col, 1.5), (1, 1, 2.6))
            g.octa((1.6, 0.4, 1.8), 0.8, rgbf(col, 1.2), (1, 1, 2.2))
        elif kind == 'lollipop':
            hue = acc[var % len(acc)]
            m.frustum((0, 0, 2.6), 0.16, 0.16, 5.2, rgbf((245, 245, 245)), 'z', 6)
            m.frustum((0, 0, 6.2), 2.2, 2.2, 0.6, rgbf((255, 255, 255)), 'y', 14)
            m.frustum((0, -0.31, 6.2), 1.2, 1.2, 0.05, rgbf(hue), 'y', 14)
            m.frustum((0, 0.31, 6.2), 1.2, 1.2, 0.05, rgbf(hue), 'y', 14)
        elif kind == 'icecream':
            sc = mix_rgb(acc[(var + 1) % len(acc)], (255, 255, 255), 0.45)
            m.frustum((0, 0, 1.8), 0.0, 1.4, 3.6, rgbf((224, 169, 106)), 'z', 8)
            m.sphere((0, 0, 4.3), 1.7, rgbf(sc), 9, 6)
            m.sphere((0, 0, 6.1), 0.4, rgbf((221, 34, 51)), 6, 4)
        elif kind == 'acacia':
            c = leaf[var % len(leaf)]
            m.frustum((0, 0, 2.3), 0.32, 0.22, 4.6, rgbf(trunk), 'z', 6)
            m.frustum((-0.9, 0, 3.7), 0.14, 0.14, 2.0, rgbf(trunk), 'x', 5)
            m.sphere((0.3, 0, 4.9), 4.2, rgbf(c), 10, 5, (1, 1, 0.22))
            m.sphere((-1.4, 0.4, 4.2), 2.2, rgbf(c, 0.9), 8, 4, (1, 1, 0.26))
            if var:
                m.sphere((1.8, -0.6, 4.3), 1.8, rgbf(c, 1.08), 8, 4, (1, 1, 0.3))
        elif kind == 'deadtree':
            tc = rgbf(trunk)
            m.frustum((0, 0, 3.0), 0.42, 0.14, 6.0, tc, 'z', 6)
            sg = -1 if var else 1
            for path in (((0, 0, 2.8), (sg * 1.2, 0.2, 4.2), (sg * 1.9, 0.1, 5.4)), ((0, 0, 3.8), (-sg * 1.3, 0.3, 4.9), (-sg * 1.7, 0.0, 6.0)),
                         ((0, 0, 4.8), (0.3, sg * 1.1, 6.1), (0.5, sg * 1.3, 6.8))):
                mesh_tube(m, list(path), 0.13, tc, 5)
        elif kind == 'bamboo':
            rnd = Rng(17)
            for k in range(6):
                x, y = (rnd() - 0.5) * 2.2, (rnd() - 0.5) * 2.2
                h = 8.0 + rnd() * 4.5
                c = rgbf(shade_rgb(trunk, 0.85 + 0.3 * rnd()))
                m.frustum((x, y, h / 2), 0.12, 0.1, h, c, 'z', 6)
                for z in range(2, int(h), 2):
                    m.frustum((x, y, z), 0.15, 0.15, 0.1, rgbf(shade_rgb(trunk, 0.6)), 'z', 6, False)
                m.sphere((x, y, h), 0.9, rgbf(leaf[k % len(leaf)]), 7, 4, (1.4, 1.0, 0.45))
                m.sphere((x + 0.4, y, h - 2.2), 0.6, rgbf(leaf[(k + 1) % len(leaf)]), 6, 3, (1.4, 1.0, 0.45))
        elif kind == 'mushroom':
            cap = acc[var % len(acc)]
            m.frustum((0, 0, 1.7), 0.62, 0.5, 3.4, rgbf(trunk), 'z', 10)
            m.sphere((0, 0, 3.4), 2.7, rgbf(cap), 12, 6, (1, 1, 0.5))
            m.disc((0, 0, 3.32), 2.5, rgbf(shade_rgb(cap, 0.55)), 'z', 14)
            for (x, y, z) in ((1.2, 0.6, 4.55), (-1.0, 0.9, 4.5), (0.2, -1.3, 4.5), (-0.6, -0.4, 4.75), (1.6, -0.8, 4.1)):
                m.sphere((x, y, z), 0.28, (1, 1, 1, 1), 6, 3, (1, 1, 0.6))
        elif kind == 'coral':
            c = acc[var % len(acc)]
            rnd = Rng(var * 13 + 5)
            for k in range(6):
                x, y = (rnd() - 0.5) * 2.4, (rnd() - 0.5) * 2.4
                h = 1.5 + rnd() * 2.6
                cc = shade_rgb(c, 0.8 + rnd() * 0.4)
                m.frustum((x, y, h / 2), 0.3, 0.24, h, rgbf(cc), 'z', 7)
                m.sphere((x, y, h), 0.32, rgbf(shade_rgb(cc, 1.25)), 6, 4)
        elif kind == 'barrel':
            bc = acc[1] if len(acc) > 1 and acc[1][0] > 150 else (230, 200, 40)
            for (x, y) in ((-0.65, 0.0), (0.65, 0.1), (0.0, 1.0)):
                m.frustum((x, y, 0.8), 0.55, 0.55, 1.6, rgbf(bc), 'z', 10)
                m.frustum((x, y, 0.35), 0.57, 0.57, 0.12, rgbf((40, 40, 40)), 'z', 10)
                m.frustum((x, y, 1.25), 0.57, 0.57, 0.12, rgbf((40, 40, 40)), 'z', 10)
        elif kind == 'pillar':
            pc = rgbf(mix_rgb(rc[0], (235, 230, 215), 0.4))
            h = 8.0 if var == 0 else 4.8
            m.box((0, 0, 0.3), (1.1, 1.1, 0.3), rgbf(mix_rgb(rc[0], (235, 230, 215), 0.3)))
            m.frustum((0, 0, 0.6 + h / 2), 0.78, 0.68, h, pc, 'z', 12)
            if var == 0:
                m.box((0, 0, 0.6 + h + 0.3), (1.0, 1.0, 0.3), pc)
        elif kind == 'haystack':
            hc = (224, 186, 94)
            m.sphere((0, 0, 1.0), 2.0, rgbf(hc), 10, 6, (1, 1, 0.78))
            m.sphere((0.3, -0.2, 1.2), 1.5, rgbf(hc, 1.08), 8, 5, (1, 1, 0.9))
        elif kind == 'windmill':
            wc = rgbf((232, 226, 214))
            m.frustum((0, 0, 5.0), 2.2, 1.4, 10.0, wc, 'z', 10)
            m.frustum((0, 0, 10.8), 1.7, 0.0, 1.8, rgbf((150, 52, 40)), 'z', 10)
            m.box((0, -1.55, 0.9), (0.5, 0.1, 0.9), rgbf((90, 60, 40)))
            bc = rgbf((245, 240, 230))
            m.box((0, -1.6, 9.4), (5.6, 0.08, 0.45), bc)
            m.box((0, -1.6, 9.4), (0.45, 0.08, 5.6), bc)
            m.sphere((0, -1.7, 9.4), 0.35, rgbf((80, 60, 40)), 6, 4)
        elif kind == 'flowers':
            fc = flower[var % len(flower)]
            m.sphere((0, 0, 0.25), 1.9, rgbf(shade_rgb(leaf[1], 0.9)), 9, 4, (1, 1, 0.22))
            rnd = Rng(var * 7 + 3)
            for _ in range(11):
                m.sphere(((rnd() - 0.5) * 3.0, (rnd() - 0.5) * 3.0, 0.6 + rnd() * 0.25), 0.2, rgbf(fc), 5, 3)
        elif kind == 'tombstone':
            gc = rgbf(mix_rgb(rc[0], (150, 150, 155), 0.4))
            if var == 0:
                m.box((0, 0, 0.85), (0.6, 0.16, 0.85), gc)
                m.frustum((0, 0, 1.7), 0.6, 0.6, 0.32, gc, 'y', 10)
            else:
                m.box((0, 0, 1.1), (0.12, 0.12, 1.1), gc)
                m.box((0, 0, 1.5), (0.5, 0.12, 0.12), gc)
            m.box((0, 0.3, 0.05), (0.8, 0.9, 0.05), rgbf(shade_rgb(mix_rgb(rc[0], (150, 150, 155), 0.4), 0.7)))
        elif kind == 'pumpkin':
            pc = (236, 120, 24)
            m.sphere((-0.38, 0, 0.55), 0.55, rgbf(pc, 0.85), 8, 5)
            m.sphere((0.38, 0, 0.55), 0.55, rgbf(pc, 0.85), 8, 5)
            m.sphere((0, 0, 0.6), 0.62, rgbf(pc), 8, 5)
            m.box((0, 0, 1.25), (0.07, 0.07, 0.15), rgbf((70, 110, 40)))
            if night:
                for x in (-0.22, 0.22):
                    g.box((x, -0.6, 0.72), (0.09, 0.02, 0.07), (2.0, 1.7, 0.6, 1))
                g.box((0, -0.6, 0.45), (0.25, 0.02, 0.05), (2.0, 1.7, 0.6, 1))
        elif kind == 'chimney':
            bc = (122, 72, 52)
            m.box((0, 0, 2.5), (4.0, 3.0, 2.5), rgbf(bc))
            m.frustum((1.6, 0, 11.0), 1.0, 0.8, 18.0, rgbf(bc, 0.8), 'z', 10)
            g.frustum((1.6, 0, 19.4), 0.86, 0.86, 0.5, rgbf(acc[0], 1.4), 'z', 10)
            for x in (-2.6, -1.2, 0.2, 1.6, 3.0):
                (g if night else m).box((x, -3.02, 2.8), (0.45, 0.02, 0.6), (2.0, 1.6, 0.8, 1) if night else (0.2, 0.17, 0.15, 1))
        elif kind == 'pyramid':
            pc = mix_rgb(rc[0], (230, 200, 140), 0.35)
            m.frustum((0, 0, 4.5), 9.9, 0.0, 9.0, rgbf(pc), 'z', 4)
        elif kind == 'dome':
            m.sphere((0, 0, 0.2), 5.0, rgbf((170, 220, 255)), 14, 7, (1, 1, 0.58))
            m.frustum((0, 0, 0.25), 5.2, 5.2, 0.5, rgbf((150, 150, 160)), 'z', 16)
            g.box((0, -4.95, 1.0), (1.0, 0.05, 0.8), (2.0, 1.8, 1.0, 1) if night else rgbf((120, 200, 255), 1.4))
        elif kind == 'icespike':
            ic = mix_rgb(th.get('crystal') or (180, 225, 255), (230, 245, 255), 0.4)
            for (x, y, r, h) in ((-0.9, 0.1, 0.7, 4.2), (0.6, -0.3, 0.8, 5.4), (0.0, 0.6, 0.9, 6.0), (1.3, 0.5, 0.5, 3.0)):
                m.frustum((x, y, h / 2), r, 0.0, h, rgbf(ic), 'z', 5)
        elif kind == 'lantern':
            lc = acc[0] if acc else (255, 120, 60)
            m.frustum((0, 0, 1.1), 0.13, 0.13, 2.2, rgbf((110, 110, 112)), 'z', 6)
            m.box((0, 0, 0.1), (0.4, 0.4, 0.1), rgbf((110, 110, 112)))
            g.box((0, 0, 2.5), (0.35, 0.35, 0.35), rgbf(lc, 1.6 if night else 1.0))
            m.frustum((0, 0, 3.05), 0.62, 0.0, 0.5, rgbf((70, 60, 60)), 'z', 6)
        elif kind == 'blocks':
            rnd = Rng(var * 19 + 1)
            z = 0.0
            for k in range(3):
                hx = 1.6 - k * 0.35 + rnd() * 0.2
                hz = 0.55 + rnd() * 0.3
                c = acc[(var + k) % len(acc)]
                ox = (rnd() - 0.5) * 0.4
                m.box((ox, 0, z + hz), (hx, hx * 0.8, hz), rgbf(c))
                for sx in (-0.5, 0.5):
                    m.frustum((ox + sx * hx, 0, z + 2 * hz + 0.1), 0.25, 0.25, 0.2, rgbf(c, 1.15), 'z', 8)
                z += 2 * hz + 0.05
        elif kind == 'dish':
            lc = rgbf((150, 150, 158))
            m.frustum((0, 0, 1.8), 0.15, 0.12, 3.6, lc, 'z', 6)
            m.frustum((0, 0, 4.0), 0.3, 2.3, 1.0, rgbf((235, 238, 245)), 'z', 14, False)
            m.frustum((0, 0, 3.5), 0.3, 0.3, 0.3, lc, 'z', 6)
            m.frustum((0, 0, 4.9), 0.06, 0.06, 1.6, lc, 'z', 5)
            g.sphere((0, 0, 5.75), 0.14, (2.0, 0.4, 0.4, 1), 6, 3)
        elif kind == 'sunflower':
            fc = flower[0]
            for (x, y, h) in ((-0.8, 0.1, 2.8), (0.2, -0.3, 3.3), (0.9, 0.4, 2.5)):
                m.frustum((x, y, h / 2), 0.06, 0.05, h, rgbf((60, 130, 50)), 'z', 5)
                m.box((x + 0.2, y, h * 0.45), (0.25, 0.04, 0.1), rgbf((70, 150, 60)))
                m.disc((x, y - 0.06, h), 0.55, rgbf(fc), 'y', 12)
                m.disc((x, y - 0.08, h), 0.24, rgbf((100, 60, 30)), 'y', 10)
        elif kind == 'cloud':
            c0 = leaf[0] if leaf[0][0] > 200 else (250, 252, 255)
            for (x, y, z, r) in ((-1.0, 0, 1.0, 1.2), (0.6, 0.2, 1.3, 1.5), (0.0, -0.3, 1.9, 1.0), (1.5, -0.1, 0.8, 0.9)):
                m.sphere((x, y, z), r, rgbf(c0), 9, 5)
        return m, (g if g.v else None)

    def _props(self):
        tr = self.track
        protos = {}
        chunks = {}
        holder = NodePath('protos')
        for p in tr.props:
            kind = p['kind']
            nv = PROP_VARS.get(kind, 1)
            var = int(p['r1'] * nv) % nv if nv > 1 else 0
            key = (kind, var)
            pr = protos.get(key)
            if pr is None:
                m, glow = self._proto(kind, var)
                lit = m.attach(holder, 'p_%s_%d' % key)
                lit.setTwoSided(True)
                parts = [lit]
                if glow is not None:
                    gn = glow.attach(holder, 'g_%s_%d' % key)
                    gn.setLightOff()
                    parts.append(gn)
                pr = protos[key] = parts
            ck = p['seg'] // 36
            chunk = chunks.get(ck)
            if chunk is None:
                chunk = chunks[ck] = self.root.attachNewNode('chunk%d' % ck)
            pos = PV(p['x'], p['y'], p['z'])
            s = p['s']
            if kind == 'building':
                sc = (14 + p['r1'] * 22, 14 + p['r2'] * 22, 30 + p['r3'] * p['r3'] * 150)
            elif kind == 'mesa':
                q = 1.2 + p['r1'] * 1.8
                sc = (q, q, 0.8 + p['r2'] * 1.6)
            elif kind == 'rock':
                sc = (s * 1.4, s * 1.4, s * (1.0 + p['r1'] * 0.8))
            else:
                sc = (s, s, s)
            shade = 0.82 + p['r1'] * 0.3 if kind in ('pine', 'roundtree', 'bush', 'rock', 'cactus', 'palm', 'acacia', 'bamboo', 'deadtree', 'flowers') else 1.0
            for part in pr:
                inst = part.copyTo(chunk)
                inst.setPos(*pos)
                inst.setH(math.degrees(p['rot']))
                inst.setScale(*sc)
                if shade != 1.0:
                    inst.setColorScale(shade, shade, shade, 1)
        for chunk in chunks.values():
            chunk.flattenStrong()
        holder.removeNode()

    def _lamps(self):
        tr = self.track
        m = Mesh()
        g = Mesh()
        for (i, side) in tr.lamps:
            off = tr.wall_off + 1.2
            x, y, z = tr.edge_point(i, off * side)
            base = PV(x, y - 0.1, z)
            m.frustum((base[0], base[1], base[2] + 5.5), 0.22, 0.16, 11.0, rgbf((48, 52, 63)), 'z', 6)
            inward = (tr.rx[i] * -side * 1.6, -tr.rz[i] * -side * 1.6)
            m.box((base[0] + inward[0] * 0.5, base[1] + inward[1] * 0.5, base[2] + 11.0), (0.14 + abs(inward[0]) * 0.5, 0.14 + abs(inward[1]) * 0.5, 0.12), rgbf((48, 52, 63)))
            g.box((base[0] + inward[0], base[1] + inward[1], base[2] + 10.8), (0.5, 0.5, 0.1), (3.0, 2.8, 2.2, 1))
        m.attach(self.root, 'lamps')
        gn = g.attach(self.root, 'lamplights')
        gn.setLightOff()

    def _arches(self):
        tr = self.track
        col = rgbf(hex_rgb(self.th['arches']), 2.0)
        m = Mesh()
        for ai in tr.arches:
            pts = []
            for k in range(0, 25):
                a = math.pi * k / 24.0
                x, y, z = tr.edge_point(ai, -(tr.hw + 1.5) * math.cos(a))
                pts.append(PV(x, y + math.sin(a) * tr.hw * 0.8 + 0.2, z))
            mesh_tube(m, pts, 0.4, col, 6)
        n = m.attach(self.root, 'arches')
        n.setLightOff()

    # ---- 갱신/정리 ---------------------------------------------------------------------------
    def update(self, cam_pos):
        self.sky.setPos(*cam_pos)

    def destroy(self):
        for l in self.lights:
            try:
                self.app.render.clearLight(l)
            except Exception:
                pass
        try:
            self.app.render.clearFog()
        except Exception:
            pass
        self.root.removeNode()
