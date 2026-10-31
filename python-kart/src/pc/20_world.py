
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
                    m.sphere((math.cos(a) * d + (j - 1.5) * s * 0.9, math.sin(a) * d, z + (j % 2) * 8), s * 0.55, (1, 1, 1, 0.88) if th['key'] != 'candy' else (1, 0.94, 0.98, 0.88),
                             seg=8, rings=4, scale=(1.0, 0.7, 0.34))
            cl = m.attach(self.sky, 'clouds')
            cl.setTransparency(TransparencyAttrib.MAlpha)
            cl.setLightOff()
            cl.setFogOff()
            cl.setDepthWrite(False)
            cl.setBin('background', 4)
        self._horizon()

    def _horizon(self):
        """360도 먼 산/도시 실루엣 (안개색과 섞어 원근감)"""
        th = self.th
        key = th['key']
        fog = hex_rgb(th['fog'])
        skyb = hex_rgb(th['sky_bot'])
        rnd = Rng(self.track.info['seed'] ^ 0x77)
        m = Mesh()
        R = 2500.0

        def ridge(color, base, amp, harm=(1, 2, 3, 5, 8, 13), z0=-300.0, rad=R, snow=False):
            phs = [rnd() * TAU for _ in harm]
            segs = 200
            ang = [TAU * i / segs for i in range(segs + 1)]
            hs = []
            for a in ang:
                h = base
                for k, p in zip(harm, phs):
                    h += amp / (k ** 0.8) * math.sin(k * a + p)
                hs.append(max(10.0, h))
            low = []
            hi = []
            for i, a in enumerate(ang):
                ca, sa = math.cos(a) * rad, math.sin(a) * rad
                n = (-math.cos(a), -math.sin(a), 0.2)
                low.append(m.add((ca, sa, z0), n, rgbf(color, 0.82)))
                topc = rgbf(color, 1.12) if not snow else (0.96, 0.98, 1.0, 1.0)
                hi.append(m.add((ca, sa, hs[i]), n, topc))
            for i in range(segs):
                a, b, c, d = low[i], low[i + 1], hi[i + 1], hi[i]
                m.tri(a, b, c)
                m.tri(a, c, d)

        if key in ('forest', 'autumn'):
            c1 = (110, 140, 170) if key == 'forest' else (190, 150, 110)
            ridge(mix_rgb(c1, skyb, 0.5), 260, 150, rad=2600)
            c2 = (60, 110, 80) if key == 'forest' else (150, 95, 50)
            ridge(mix_rgb(c2, fog, 0.35), 150, 90, rad=2100)
        elif key == 'desert':
            ridge(mix_rgb((200, 160, 100), skyb, 0.5), 130, 70, (1, 2, 3, 4), rad=2500)
            for _ in range(3):
                a = rnd() * TAU
                b = 130 + rnd() * 90
                cx, cy = math.cos(a) * 2300, math.sin(a) * 2300
                m.frustum((cx, cy, b * 0.45), b, 0.0, b * 0.9, rgbf(mix_rgb((190, 150, 95), fog, 0.35)), 'z', 4, False)
            ridge(mix_rgb((214, 176, 110), fog, 0.2), 70, 45, (1, 2, 4, 6), rad=1900)
        elif key == 'snow':
            ridge((246, 250, 255), 330, 170, rad=2600, snow=True)
            ridge(mix_rgb((95, 125, 105), fog, 0.45), 120, 60, rad=2000)
        elif key == 'neon':
            for layer, (col, hmax, rad) in enumerate((((78, 40, 130), 520, 2500), ((30, 18, 66), 330, 2000))):
                n = 150
                for i in range(n):
                    a = TAU * i / n + rnd() * 0.02
                    w = 30 + rnd() * 55
                    h = 40 + rnd() * hmax
                    cx, cy = math.cos(a) * rad, math.sin(a) * rad
                    m.box((cx, cy, h / 2 - 50), (w / 2, w / 2, h / 2 + 25), rgbf(col))
                    if rnd() < 0.45:
                        gc = [(255, 43, 214), (25, 230, 255), (255, 225, 74)][int(rnd() * 3)]
                        m.box((cx, cy, h * (0.3 + 0.6 * rnd()) - 50), (w * 0.52, w * 0.52, 3), rgbf(gc, 1.6))
        elif key == 'volcano':
            ridge((46, 22, 18), 160, 90, rad=2400)
            for _ in range(2):
                a = rnd() * TAU
                b = 360 + rnd() * 180
                cx, cy = math.cos(a) * 2200, math.sin(a) * 2200
                m.frustum((cx, cy, b * 0.55), b, 40, b * 1.1, rgbf((52, 26, 20)), 'z', 9, False, rgbf((255, 120, 40), 1.5))
        elif key == 'tropic':
            ridge(mix_rgb((70, 150, 100), fog, 0.35), 60, 40, (1, 3, 5, 9), rad=2300)
            ridge(mix_rgb((235, 215, 160), fog, 0.2), 25, 15, (1, 3, 5), rad=1700)
        elif key == 'candy':
            ridge(mix_rgb((255, 190, 225), skyb, 0.35), 200, 120, rad=2500)
            ridge(mix_rgb((190, 240, 255), fog, 0.3), 110, 70, rad=2000)
        elif key == 'space':
            ridge((70, 70, 80), 150, 80, rad=2400)
            a = rnd() * TAU
            m.sphere((math.cos(a) * 2600, math.sin(a) * 2600, 900), 380, rgbf((58, 111, 208)), seg=18, rings=12)
            ridge((92, 92, 104), 80, 50, (1, 2, 4, 7), rad=1900)
        elif key == 'canyon':
            for layer, (col, hmax, rad) in enumerate((((150, 70, 50), 520, 2500), ((120, 52, 36), 330, 1900))):
                n = 40
                for i in range(n):
                    a = TAU * i / n + rnd() * 0.05
                    w = 120 + rnd() * 260
                    h = hmax * (0.35 + rnd() * 0.65)
                    cx, cy = math.cos(a) * rad, math.sin(a) * rad
                    cc = mix_rgb(col, fog, 0.3 - layer * 0.15)
                    m.box((cx, cy, h / 2 - 60), (w / 2, w / 3, h / 2 + 30), rgbf(cc))
        hz = m.attach(self.sky, 'horizon')
        hz.setTwoSided(True)
        hz.setLightOff()
        hz.setFogOff()

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
        red, white = (0.85, 0.14, 0.16, 1.0), (0.94, 0.94, 0.94, 1.0)
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
        th = self.th
        m = Mesh()
        glow = None
        rc = (hex_rgb(th['rock'][0]), hex_rgb(th['rock'][1]))
        if kind == 'pine':
            snowy = th.get('snowy')
            m.frustum((0, 0, 1.5), 0.5, 0.35, 3.0, rgbf((90, 59, 34)), 'z', 6)
            cols = [(31, 107, 53), (42, 125, 63), (53, 145, 74)] if not snowy else [(79, 127, 102), (109, 154, 132), (242, 247, 251)]
            for (z, r, ln), c in zip(((5.0, 3.4, 5.0), (7.6, 2.7, 4.6), (10.0, 1.9, 4.0)), cols):
                m.frustum((0, 0, z), r, 0.0, ln, rgbf(c), 'z', 7, True)
        elif kind == 'roundtree':
            cols = [(217, 84, 30), (232, 163, 23), (184, 58, 26), (240, 192, 48)] if th.get('autumn') else [(58, 140, 58), (74, 160, 74), (47, 127, 53), (90, 170, 80)]
            c = cols[var % 4]
            m.frustum((0, 0, 2.0), 0.65, 0.45, 4.0, rgbf((90, 59, 34)), 'z', 6)
            m.sphere((0, 0, 6.5), 3.4, rgbf(c), 9, 6, (1, 1, 0.9))
            m.sphere((1.6, 0.8, 5.3), 2.2, rgbf(c, 0.88), 8, 5)
        elif kind == 'bush':
            m.sphere((0, 0, 0.8), 1.6, rgbf((47, 127, 53)), 8, 5, (1.2, 1.1, 0.7))
            m.sphere((1.3, 0.5, 0.5), 1.1, rgbf((58, 140, 58)), 7, 4)
        elif kind == 'cactus':
            g = rgbf((59, 138, 74))
            m.frustum((0, 0, 3.0), 0.8, 0.7, 6.0, g, 'z', 8)
            m.frustum((0.9, 0, 2.4), 0.4, 0.4, 1.4, g, 'x', 6)
            m.frustum((1.7, 0, 3.5), 0.4, 0.4, 2.4, g, 'z', 6)
            m.frustum((-0.6, 0, 3.6), 0.4, 0.4, 1.2, g, 'x', 6)
            m.frustum((-1.3, 0, 4.4), 0.4, 0.4, 1.8, g, 'z', 6)
        elif kind == 'rock':
            m.sphere((0, 0, 0.9), 2.2, rgbf(rc[0]), 7, 4, (1.3, 1.1, 0.8))
            m.sphere((2.3, 0.7, 0.5), 1.3, rgbf(rc[1]), 6, 4, (1.0, 1.0, 0.8))
        elif kind == 'mesa':
            for (z, r0, r1, ln), c in zip(((6, 9, 7, 12), (15, 7, 6.2, 6), (20.5, 6.2, 5.4, 5), (23.6, 5.6, 5.6, 1.2)), ((176, 74, 40), (199, 101, 58), (168, 68, 36), (224, 160, 96))):
                m.frustum((0, 0, z), r0, r1, ln, rgbf(c), 'z', 7)
        elif kind == 'palm':
            m.frustum((0.3, 0, 4.2), 0.5, 0.28, 8.4, rgbf((138, 106, 64)), 'z', 6)
            for k in range(7):
                a = k * 0.898
                blade(m, (0.3, 0, 8.4), (0.3 + math.cos(a) * 4.6, math.sin(a) * 4.6, 6.7), 0.75, rgbf((47, 143, 58) if k % 2 else (58, 160, 70)))
            m.sphere((0.3, 0, 8.2), 0.45, rgbf((90, 59, 34)), 6, 4)
        elif kind == 'building':
            m.box((0, 0, 0.5), (0.5, 0.5, 0.5), rgbf((58, 56, 108)))
            g = Mesh()
            for z, c in ((0.9, (255, 43, 214)), (0.62, (25, 230, 255)), (0.34, (255, 225, 74)), (0.98, (255, 43, 214))):
                g.box((0, 0, z), (0.512, 0.512, 0.008), rgbf(c, 1.6))
            glow = g
        elif kind == 'crystal':
            col = (255, 122, 26) if th.get('lava') else ((25, 230, 255) if th['key'] == 'space' else (255, 43, 214))
            g = Mesh()
            g.octa((0, 0, 3.0), 1.2, rgbf(col, 1.5), (1, 1, 2.6))
            g.octa((1.6, 0.4, 1.8), 0.8, rgbf(col, 1.2), (1, 1, 2.2))
            glow = g
        elif kind == 'lollipop':
            hue = [(255, 90, 140), (90, 200, 255), (255, 200, 60), (160, 110, 255), (110, 230, 150), (255, 140, 60)][var % 6]
            m.frustum((0, 0, 2.6), 0.16, 0.16, 5.2, rgbf((245, 245, 245)), 'z', 6)
            m.frustum((0, 0, 6.2), 2.2, 2.2, 0.6, rgbf((255, 255, 255)), 'y', 14)
            m.frustum((0, -0.31, 6.2), 1.2, 1.2, 0.05, rgbf(hue), 'y', 14)
            m.frustum((0, 0.31, 6.2), 1.2, 1.2, 0.05, rgbf(hue), 'y', 14)
        elif kind == 'icecream':
            sc = [(255, 158, 196), (255, 235, 160), (150, 220, 255)][var % 3]
            m.frustum((0, 0, 1.8), 0.0, 1.4, 3.6, rgbf((224, 169, 106)), 'z', 8)
            m.sphere((0, 0, 4.3), 1.7, rgbf(sc), 9, 6)
            m.sphere((0, 0, 6.1), 0.4, rgbf((221, 34, 51)), 6, 4)
        return m, glow

    def _props(self):
        tr = self.track
        protos = {}
        chunks = {}
        rnd = Rng(tr.info['seed'] ^ 0x5151)
        VAR = {'roundtree': 4, 'lollipop': 6, 'icecream': 3}
        holder = NodePath('protos')
        for p in tr.props:
            kind = p['kind']
            if kind == 'roundtree':
                var = int(p['r1'] * 4)
            elif kind == 'lollipop':
                var = int(p['r1'] * 6)
            elif kind == 'icecream':
                var = int(p['r1'] * 3)
            else:
                var = 0
            key = (kind, var)
            pr = protos.get(key)
            if pr is None:
                m, glow = self._proto(kind, var)
                lit = m.attach(holder, 'p_%s_%d' % key)
                lit.setTwoSided(True)
                parts = [lit]
                if glow is not None:
                    g = glow.attach(holder, 'g_%s_%d' % key)
                    g.setLightOff()
                    parts.append(g)
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
            shade = 0.82 + p['r1'] * 0.3 if kind not in ('lollipop', 'icecream', 'building', 'crystal') else 1.0
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
