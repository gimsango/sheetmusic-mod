
# ============================================================================
#  [PC] 카트 노드(100,000종) / 그림자 / 파티클 / 날씨
# ============================================================================
_SHARED = {}


def shared_tex(name, fn):
    t = _SHARED.get(name)
    if t is None:
        t = _SHARED[name] = fn()
    return t


class KartNode(object):
    """Racer 하나를 3D 로 표시. KartModel(파츠 목록) -> Panda3D 지오메트리"""

    def __init__(self, app, racer, parent):
        self.app = app
        self.rc = racer
        m = self.model = KartModel(racer.kart_id)
        self.root = parent.attachNewNode('kart-' + str(racer.id))
        self.spinner = self.root.attachNewNode('spinner')      # 아이템 효과: 스핀/점프
        self.yaw = self.spinner.attachNewNode('yaw')
        self.chassis = self.yaw.attachNewNode('chassis')
        body = Mesh()
        glow = Mesh()
        for (cx, cy, cz, hx, hy, hz, col, tx, ty, g) in m.boxes:
            tgt = glow if g else body
            tgt.box((cx, cz, cy), (hx, hz, hy), rgbf(col, 1.0 if not g else 1.8), taper=(tx, ty) if (tx != 1 or ty != 1) else None)
        hp = m.helmet
        body.sphere((hp[0], hp[2], hp[1]), 0.27, rgbf(m.main), 10, 7)
        body.box((hp[0], hp[2] + 0.2, hp[1] - 0.02), (0.17, 0.07, 0.05), (0.03, 0.03, 0.04, 1))
        body.attach(self.chassis, 'body')
        glow.attach(self.chassis, 'glow').setLightOff()
        # 바퀴
        self.wheels = []
        R, ww = m.wheel_r, m.wheel_w
        for (lx, ly, lz, sgn, front) in m.wheels:
            pivot = self.chassis.attachNewNode('pivot')
            pivot.setPos(lx, lz, ly)
            spin = pivot.attachNewNode('spin')
            tm = Mesh()
            tm.frustum((0, 0, 0), R, R, ww, (0.13, 0.13, 0.15, 1), 'x', 14)
            tm.attach(spin, 'tire')
            rim = Mesh()
            rg = Mesh()
            face = sgn * (ww / 2 + 0.006)
            rc_ = rgbf(m.rim_color)
            if m.rim == 0:
                rim.disc((face, 0, 0), R * 0.66, rc_, 'x')
            elif m.rim in (1, 2):
                rim.disc((face, 0, 0), R * 0.62, (0.1, 0.1, 0.12, 1), 'x')
                n = 5 if m.rim == 1 else 8
                for k in range(n):
                    rim.spoke((face + sgn * 0.002, 0, 0), TAU * k / n, R * 0.62, 0.07 if m.rim == 1 else 0.045, rc_, 'x')
                rim.disc((face + sgn * 0.003, 0, 0), R * 0.14, rc_, 'x', 8)
            elif m.rim == 3:
                rim.disc((face, 0, 0), R * 0.62, (0.15, 0.15, 0.18, 1), 'x')
                rim.annulus((face + sgn * 0.002, 0, 0), R * 0.5, R * 0.64, rc_, 'x')
                rim.disc((face + sgn * 0.003, 0, 0), R * 0.14, rc_, 'x', 8)
            else:
                rim.disc((face, 0, 0), R * 0.62, (0.04, 0.04, 0.06, 1), 'x')
                rg.annulus((face + sgn * 0.002, 0, 0), R * 0.46, R * 0.62, rgbf(m.rim_color, 1.8), 'x')
            rim.attach(spin, 'rim').setTwoSided(True)
            if rg.v:
                rg.attach(spin, 'rimglow').setLightOff()
            self.wheels.append((pivot, spin, front))
        # 그림자 (blob)
        cm = CardMaker('shadow')
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        sh = self.root.attachNewNode(cm.generate())
        sh.setTexture(shared_tex('blob', lambda: tex_glow('blob', 64, 1.0)))
        sh.setColor(0, 0, 0, 0.62)
        sh.setTransparency(TransparencyAttrib.MAlpha)
        sh.setP(-90)
        sh.setPos(0, 0, 0.05)
        sh.setScale(m.W * 1.9, m.L * 1.7, 1)
        sh.setLightOff()
        sh.setDepthWrite(False)
        sh.setBin('fixed', 2)
        self.shadow = sh
        # 부스트 불꽃
        fm = Mesh()
        fm.frustum((0, 0, 0), 0.0, 0.22, 1.4, (3.0, 1.4, 0.4, 0.9), 'y', 8, False)
        self.flame = fm.attach(self.chassis, 'flame')
        self.flame.setPos(0, -m.L / 2 - 0.65, m.base + m.H * 0.3)
        self.flame.setLightOff()
        self.flame.setTransparency(TransparencyAttrib.MAlpha)
        self.flame.hide()
        # 이름표
        self.label = None
        if racer.kind != 'local' and racer.name:
            tn = TextNode('nm')
            tn.setText(racer.name)
            tn.setAlign(TextNode.ACenter)
            tn.setTextColor(1.0, 0.82, 0.47, 1) if racer.kind == 'bot' else tn.setTextColor(0.6, 0.91, 1.0, 1)
            tn.setShadow(0.06, 0.06)
            tn.setShadowColor(0, 0, 0, 1)
            if app.font is not None:
                tn.setFont(app.font)
            lb = self.root.attachNewNode(tn)
            lb.setPos(0, 0, 2.7)
            lb.setScale(0.85)
            lb.setBillboardPointEye()
            lb.setLightOff()
            lb.setFogOff()
            lb.setDepthTest(False)
            lb.setDepthWrite(False)
            lb.setBin('fixed', 40)
            self.label = lb
        self.spin = 0.0
        self.t = 0.0
        self.fx_state = None
        self.bubble = None

    def _effects(self, rc, dt):
        """아이템 상태이상 표시: 크기/점프/스핀/무지개(무적)/얼음/유령/방패"""
        self.t += dt
        fxb = rc.fx
        sc = rc.scale
        if abs(sc - 1.0) > 0.01 or self.fx_state is not None:
            self.root.setScale(sc)
        self.spinner.setZ(rc.air_y / max(sc, 0.3))
        self.spinner.setH(-math.degrees(rc.spin_ang))
        if fxb & FX_STAR:
            hc = hue_rgb(self.t * 2.2)
            cs = (0.6 + hc[0] / 255.0 * 0.9, 0.6 + hc[1] / 255.0 * 0.9, 0.6 + hc[2] / 255.0 * 0.9, 1.0)
        elif fxb & FX_FREEZE:
            cs = (0.7, 0.95, 1.6, 1.0)
        else:
            cs = None
        ghost = bool(fxb & FX_GHOST)
        state = (cs, ghost)
        if cs is not None or ghost or state != self.fx_state:
            if cs is None and not ghost:
                self.spinner.clearColorScale()
                self.spinner.clearTransparency()
            else:
                c = cs or (1.0, 1.0, 1.0, 1.0)
                self.spinner.setColorScale(c[0], c[1], c[2], 0.35 if ghost else 1.0)
                if ghost:
                    self.spinner.setTransparency(TransparencyAttrib.MAlpha)
                else:
                    self.spinner.clearTransparency()
            self.fx_state = state if (cs is not None or ghost) else None
        if fxb & FX_SHIELD:
            if self.bubble is None:
                m = self.model
                bm = Mesh()
                bm.sphere((0, 0, 0), 1.0, (0.55, 0.88, 1.0, 0.3), 14, 9)
                b = bm.attach(self.spinner, 'bubble')
                b.setTransparency(TransparencyAttrib.MAlpha)
                b.setLightOff()
                b.setTwoSided(True)
                b.setDepthWrite(False)
                b.setBin('fixed', 20)
                r = max(m.L, m.W * 1.4) * 0.72
                b.setScale(r * 0.85, r, r * 0.8)
                b.setPos(0, 0, m.base + m.H * 0.6)
                self.bubble = b
            self.bubble.show()
        elif self.bubble is not None:
            self.bubble.hide()

    def update(self, rc, dt, ds, cam_dist):
        m = self.model
        self._effects(rc, dt)
        pos = PV(rc.x, rc.y, rc.z)
        up = rc.up
        h = rc.h
        fx, fz = math.sin(h), math.cos(h)
        d = fx * up[0] + fz * up[2]
        F = (fx - up[0] * d, -up[1] * d, fz - up[2] * d)
        fp = PV(*F)
        upp = PV(*up)
        self.root.setPos(*pos)
        self.root.lookAt(Point3(pos[0] + fp[0], pos[1] + fp[1], pos[2] + fp[2]), Vec3(upp[0], upp[1], upp[2]))
        # 드리프트/미끄러짐: 차체만 회전 (코어: drift_dir>0 = 오른쪽 -> Panda H 음수)
        if rc.drifting:
            tgt = -rc.drift_dir * 17.0
        else:
            tgt = clamp(-rc.slip * 1.1, -14.0, 14.0)
        self.yaw.setH(self.yaw.getH() + (tgt - self.yaw.getH()) * min(1.0, dt * 9))
        self.chassis.setR(self.chassis.getR() + ((-rc.steer * 3.5) - self.chassis.getR()) * min(1.0, dt * 8))
        self.spin -= (rc.speed / m.wheel_r) * dt
        deg = math.degrees(self.spin)
        for pivot, spin, front in self.wheels:
            spin.setP(deg)
            if front:
                pivot.setH(-rc.steer * 24.0)
        if rc.boosting:
            self.flame.show()
            self.flame.setScale(1, 0.7 + _random.random() * 0.8, 1)
        else:
            self.flame.hide()
        if self.label is not None:
            self.label.setScale(0.85 * clamp(cam_dist / 16.0, 0.8, 4.0))
            if cam_dist < 11 or cam_dist > 220:
                self.label.hide()
            else:
                self.label.show()

    def destroy(self):
        self.root.removeNode()


class Particles(object):
    def __init__(self, app, n=150):
        self.app = app
        self.items = []
        cm = CardMaker('p')
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        tex = shared_tex('pglow', lambda: tex_glow('pglow', 32, 1.2))
        self.root = app.render.attachNewNode('particles')
        for _ in range(n):
            np_ = self.root.attachNewNode(cm.generate())
            np_.setTexture(tex)
            np_.setBillboardPointEye()
            np_.setLightOff()
            np_.setFogOff()
            np_.setDepthWrite(False)
            np_.setTransparency(TransparencyAttrib.MAlpha)
            np_.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
            np_.setBin('fixed', 30)
            np_.hide()
            self.items.append([np_, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, (1, 1, 1), 1.0])
        self.cursor = 0

    def emit(self, pos, vel, color, size, life):
        it = self.items[self.cursor]
        self.cursor = (self.cursor + 1) % len(self.items)
        it[1], it[2], it[3] = pos
        it[4], it[5], it[6] = vel
        it[7] = life
        it[8] = life
        it[9] = color
        it[10] = size
        it[0].show()

    def update(self, dt):
        for it in self.items:
            if it[7] <= 0:
                continue
            it[7] -= dt
            if it[7] <= 0:
                it[0].hide()
                continue
            it[1] += it[4] * dt
            it[2] += it[5] * dt
            it[3] += it[6] * dt
            it[6] -= 9.0 * dt
            f = it[7] / it[8]
            np_ = it[0]
            np_.setPos(it[1], it[2], it[3])
            np_.setScale(it[10] * (0.4 + f))
            c = it[9]
            np_.setColor(c[0], c[1], c[2], f)

    def destroy(self):
        self.root.removeNode()


class Weather(object):
    """카메라 주변을 도는 점 입자 (눈/불씨/낙엽/스프링클)"""

    def __init__(self, app, kind):
        self.app = app
        self.kind = kind
        self.n = 520 if kind == 'snow' else 320
        fmt = GeomVertexFormat.getV3()
        self.vd = GeomVertexData('weather', fmt, Geom.UHDynamic)
        self.vd.setNumRows(self.n)
        rnd = Rng(99)
        self.pos = [[(rnd() - 0.5) * 160, (rnd() - 0.5) * 160, rnd() * 70, rnd() * 6.28] for _ in range(self.n)]
        prim = GeomPoints(Geom.UHStatic)
        prim.addNextVertices(self.n)
        geom = Geom(self.vd)
        geom.addPrimitive(prim)
        gn = GeomNode('weather')
        gn.addGeom(geom)
        self.np = app.render.attachNewNode(gn)
        col = {'snow': (1, 1, 1, 1), 'ember': (1, 0.55, 0.18, 1), 'leaf': (0.85, 0.4, 0.15, 1), 'sprinkle': (1, 0.5, 0.8, 1)}[kind]
        self.np.setColor(*col)
        self.np.setRenderModeThickness(3.0 if kind == 'snow' else 4.0)
        self.np.setLightOff()
        self.np.setBin('fixed', 25)
        self.np.setDepthWrite(False)
        self.np.node().setBounds(OmniBoundingVolume())
        self.np.node().setFinal(True)
        self.t = 0.0

    def update(self, dt, cam):
        self.t += dt
        vw = GeomVertexWriter(self.vd, 'vertex')
        vy = 2.4 if self.kind == 'ember' else -3.4
        cx, cy, cz = cam
        for i, p in enumerate(self.pos):
            p[2] += vy * dt * (0.6 + (i % 5) * 0.2)
            p[0] += math.sin(self.t + p[3]) * dt * 1.2
            if p[2] < 0:
                p[2] += 70
            elif p[2] > 70:
                p[2] -= 70
            x = ((p[0] - cx + 80) % 160) - 80 + cx
            y = ((p[1] - cy + 80) % 160) - 80 + cy
            vw.setData3(x, y, p[2] + cz - 25)

    def destroy(self):
        self.np.removeNode()
