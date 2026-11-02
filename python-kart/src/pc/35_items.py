
# ============================================================================
#  [PC] 아이템전: 벡터 아이콘 -> 2D 메시 / HUD 슬롯 3칸(키 1·2·3) / 상자·투사체·함정 3D / 화면 효과
# ============================================================================
_ICON_PROTOS = {}


def _icon_mesh(it):
    """코어 ICONS 정의를 aspect2d 용 평면 메시로 (x 오른쪽, z 위). 그림자 한 번 + 본체 한 번."""
    item = ITEMS[it]
    m = Mesh()
    nrm = (0.0, -1.0, 0.0)

    def V(x, y):
        return (x, 0.0, -y)

    def col(ci):
        c = icon_color(item, ci)
        return (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, 1.0)

    def fan(cx, cy, pts, c):
        ctr = m.add(V(cx, cy), nrm, c)
        idx = [m.add(V(x, y), nrm, c) for x, y in pts]
        n = len(idx)
        for i in range(n):
            m.tri(ctr, idx[i], idx[(i + 1) % n])

    def ellipse(cx, cy, rx, ry, c, seg=22):
        fan(cx, cy, [(cx + math.cos(TAU * i / seg) * rx, cy + math.sin(TAU * i / seg) * ry) for i in range(seg)], c)

    def ring(cx, cy, r0, r1, c, seg=26):
        for i in range(seg):
            a0, a1 = TAU * i / seg, TAU * (i + 1) / seg
            p = [m.add(V(cx + math.cos(a) * r, cy + math.sin(a) * r), nrm, c) for a, r in ((a0, r0), (a0, r1), (a1, r1), (a1, r0))]
            m.tri(p[0], p[1], p[2])
            m.tri(p[0], p[2], p[3])

    def line(pts, w, c):
        h = w / 2.0
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            dx, dy = x1 - x0, y1 - y0
            l = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / l * h, dx / l * h
            p = [m.add(V(x, y), nrm, c) for x, y in ((x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny))]
            m.tri(p[0], p[1], p[2])
            m.tri(p[0], p[2], p[3])
        for x, y in pts:
            ellipse(x, y, h, h, c, 10)
    for shadow in (True, False):
        off = 0.07 if shadow else 0.0
        for prim in ICONS[item['icon']]:
            t = prim[0]
            c = (0.0, 0.0, 0.0, 0.45) if shadow else col(prim[-1])
            if t == 'c':
                ellipse(prim[1] + off, prim[2] + off, prim[3], prim[3], c)
            elif t == 'e':
                ellipse(prim[1] + off, prim[2] + off, prim[3], prim[4], c)
            elif t == 'r':
                ring(prim[1] + off, prim[2] + off, max(0.0, prim[3] - prim[4] / 2.0), prim[3] + prim[4] / 2.0, c)
            elif t == 'p':
                pts = prim[1]
                cx = sum(p[0] for p in pts) / len(pts)
                cy = sum(p[1] for p in pts) / len(pts)
                fan(cx + off, cy + off, [(x + off, y + off) for x, y in pts], c)
            elif t == 'l':
                line([(x + off, y + off) for x, y in prim[1]], prim[2], c)
    np_ = NodePath(m.node('icon%d' % it))
    np_.setTwoSided(True)
    np_.setTransparency(TransparencyAttrib.MAlpha)
    np_.setLightOff()
    return np_


def icon_node(parent, it, scale):
    proto = _ICON_PROTOS.get(it)
    if proto is None:
        proto = _ICON_PROTOS[it] = _icon_mesh(it)
    n = proto.copyTo(parent)
    n.setScale(scale)
    return n


class ItemHUD(object):
    """화면 위 가운데: 아이템 슬롯 3칸 + 이름 + 상태 + 미사일 경고"""

    def __init__(self, app):
        self.app = app
        a = app
        self.root = a.a2dTopCenter.attachNewNode('itemhud')
        self.slots = []
        self._txt = {}
        cm = CardMaker('slot')
        cm.setFrame(-0.1, 0.1, -0.1, 0.1)
        kw = dict(font=a.font, mayChange=True, shadow=(0, 0, 0, 1))
        for i in range(ITEM_SLOTS):
            fr = self.root.attachNewNode('slot%d' % i)
            fr.setPos((i - 1) * 0.25, 0, -0.135)
            border = fr.attachNewNode(cm.generate())
            border.setScale(1.08)
            border.setTransparency(TransparencyAttrib.MAlpha)
            bg = fr.attachNewNode(cm.generate())
            bg.setColor(0.06, 0.09, 0.19, 0.88)
            bg.setTransparency(TransparencyAttrib.MAlpha)
            holder = fr.attachNewNode('icon')
            key = OnscreenText(text=str(i + 1), parent=fr, pos=(-0.082, 0.06), scale=0.042, fg=(1, 0.86, 0.47, 1), align=TextNode.ALeft, **kw)
            uses = OnscreenText(text='', parent=fr, pos=(0.09, -0.088), scale=0.042, fg=(1, 1, 1, 1), align=TextNode.ARight, **kw)
            name = OnscreenText(text='', parent=fr, pos=(0, -0.152), scale=0.034, fg=(0.9, 0.93, 1, 1), align=TextNode.ACenter, **kw)
            self.slots.append({'fr': fr, 'border': border, 'icon': holder, 'key': key, 'uses': uses, 'name': name, 'cur': None})
        self.status = OnscreenText(text='', parent=self.root, pos=(0, -0.33), scale=0.046, fg=(1, 0.95, 0.75, 1), align=TextNode.ACenter, **kw)
        self.warn = OnscreenText(text='', parent=self.root, pos=(0, -0.4), scale=0.065, fg=(1, 0.3, 0.3, 1), align=TextNode.ACenter, **kw)
        self.root.hide()
        self.visible = False

    def _set(self, node, text):
        if self._txt.get(id(node)) != text:
            self._txt[id(node)] = text
            node.setText(text)

    def show(self, flag):
        self.visible = flag
        if flag:
            self.root.show()
        else:
            self.root.hide()

    def reset(self):
        for sl in self.slots:
            sl['cur'] = None
            for c in sl['icon'].getChildren():
                c.removeNode()

    def update(self, race, t):
        rc = race.local
        for i, sl in enumerate(self.slots):
            it = rc.items[i]
            roll = rc.roll[i]
            if it is None:
                want = None
            elif roll > 0:
                want = ('r', (int(t * 16) * 37 + i * 11) % ITEM_COUNT)
            else:
                want = ('i', it)
            if want != sl['cur']:
                sl['cur'] = want
                for c in sl['icon'].getChildren():
                    c.removeNode()
                if want is not None:
                    icon_node(sl['icon'], want[1], 0.082 if want[0] == 'i' else 0.066)
            ready = it is not None and roll <= 0
            if ready:
                k = 0.75 + 0.25 * math.sin(t * 6.0 + i)
                sl['border'].setColor(1.0 * k, 0.78 * k, 0.27, 0.95)
            else:
                sl['border'].setColor(0.32, 0.36, 0.5, 0.8)
            self._set(sl['uses'], ('x%d' % rc.uses[i]) if ready and rc.uses[i] > 1 else '')
            name = item_name(it, LANG) if ready else ''
            if self._txt.get(id(sl['name'])) != name:
                self._set(sl['name'], name)
                try:
                    w = sl['name'].textNode.calcWidth(name) if name else 0.0
                except Exception:
                    w = 0.0
                sl['name'].setScale(min(0.034, 0.235 / w) if w > 0 else 0.034)     # 칸 폭에 맞게 줄이기
        st = fx_status(rc.sim, LANG)
        self._set(self.status, '    '.join(s_[0] for s_ in st[:4]))
        thr = incoming_threat(race)
        self._set(self.warn, T('! 미사일 접근 !', '! INCOMING !') if (thr is not None and int(t * 6) % 2 == 0) else '')

    def destroy(self):
        self.root.removeNode()


class ItemWorld(object):
    """아이템 상자(무지개 큐브 + ?) / 투사체 / 함정 3D 표시"""

    def __init__(self, app, race, parent):
        self.app = app
        self.race = race
        self.items = race.items
        self.root = parent.attachNewNode('items3d')
        self.protos = {}
        self.ent_nodes = {}
        self.t = 0.0
        cube = Mesh()
        cube.box((0, 0, 0), (0.8, 0.8, 0.8), (1, 1, 1, 1))
        cube_np = NodePath(cube.node('ibox'))
        tn = TextNode('q')
        tn.setText('?')
        tn.setAlign(TextNode.ACenter)
        tn.setTextColor(1, 1, 1, 1)
        tn.setShadow(0.05, 0.05)
        tn.setShadowColor(0, 0, 0, 1)
        if app.font is not None:
            tn.setFont(app.font)
        self.qtext = tn
        self.boxes = []
        for b in self.items.boxes:
            n = self.root.attachNewNode('box')
            c = cube_np.copyTo(n)
            q = n.attachNewNode(tn.generate())
            q.setScale(1.3)
            q.setPos(0, 0, -0.45)
            q.setBillboardPointEye(1.3)          # 큐브 앞쪽(카메라 쪽)으로 띄워서 보이게
            q.setLightOff()
            n.setPos(*PV(b['x'], b['y'], b['z']))
            self.boxes.append((n, c))

    def _proto(self, e):
        it = ITEMS[e.item]
        key = (e.kind, it['id'])
        p = self.protos.get(key)
        if p is not None:
            return p
        c1, c2 = rgbf(it['c1']), rgbf(it['c2'])
        m = Mesh()
        g = Mesh()
        icon = it['icon']
        k = e.kind
        prm = it['p']
        shape = prm.get('shape')
        ring = None
        alpha = False
        if k == 'trap':
            r = float(prm.get('r', 1.2))
            if shape == 'banana':
                b = 1.9 if prm.get('big') else 1.0
                for a in (-1.05, -0.35, 0.35, 1.05):
                    m.box((math.sin(a) * 0.5 * b, (math.cos(a) * 0.5 - 0.5) * b, 0.16 * b), (0.15 * b, 0.2 * b, 0.13 * b), c1)
                m.box((0, 0.05 * b, 0.2 * b), (0.06 * b, 0.12 * b, 0.06 * b), rgbf((110, 76, 30)))
            elif shape in ('oil', 'glue'):
                m.frustum((0, 0, 0.04), r, r * 0.95, 0.05, rgbf((22, 20, 30)) if shape == 'oil' else c1, 'z', 16)
                m.frustum((r * 0.3, r * 0.25, 0.08), r * 0.2, r * 0.18, 0.02, c2, 'z', 10)
            elif shape == 'ice':
                m.frustum((0, 0, 0.05), r, r, 0.06, c1, 'z', 6)
                m.frustum((0, 0, 0.09), r * 0.55, r * 0.55, 0.02, c2, 'z', 6)
            elif shape == 'spikes':
                m.box((0, 0, 0.04), (r, 0.4, 0.04), c2)
                for i in range(6):
                    m.frustum((-r + (i + 0.5) * 2 * r / 6.0, 0, 0.3), 0.16, 0.0, 0.45, c1, 'z', 4)
            elif shape == 'mine':
                m.frustum((0, 0, 0.1), 0.85, 0.7, 0.2, c1, 'z', 12)
                m.frustum((0, 0, 0.22), 0.5, 0.45, 0.06, rgbf((110, 116, 130)), 'z', 12)
                g.sphere((0, 0, 0.32), 0.17, (1.8, 0.2, 0.2, 1), 8, 5)
            elif shape == 'fakebox':
                m.box((0, 0, 0.85), (0.8, 0.8, 0.8), (1, 1, 1, 1))
            elif shape == 'wall':
                for (cx, cy, cz, hx, hy, hz, col, tx, ty, gl) in wall_boxes(it):
                    m.box((cx, cz, cy), (hx, hz, hy), rgbf(col))
            elif shape == 'portal':
                g.annulus((0, 0, 1.4), 1.0, 1.35, rgbf(it['c1'], 1.6), 'y', 22)
                g.annulus((0, 0, 1.4), 0.55, 0.75, rgbf(it['c2'], 1.3), 'y', 18)
        elif k == 'tornado':
            for i in range(5):
                m.frustum((0, 0, 0.55 + i * 1.12), 0.9 + i * 0.72, 1.25 + i * 0.75, 0.9, (c1 if i % 2 == 0 else c2)[:3] + (0.72,), 'z', 12, False)
            alpha = True
        elif k == 'meteor':
            g.sphere((0, 0, 0), 1.6, rgbf(it['c1'], 1.7), 10, 7)
            g.frustum((0, 0, 4.0), 1.1, 0.0, 7.0, (2.0, 1.4, 0.4, 0.8), 'z', 10, False)
            rm = Mesh()
            rr = float(prm.get('r', 5.0))
            rm.annulus((0, 0, 0), rr - 0.3, rr, (2.0, 0.4, 0.2, 1), 'z', 28)
            ring = rm
        elif k == 'seeker':
            m.sphere((0, 0, 0), 1.0, c1, 12, 8)
            m.box((1.45, 0, 0.3), (0.9, 0.35, 0.05), c2)
            m.box((-1.45, 0, 0.3), (0.9, 0.35, 0.05), c2)
        elif k == 'bomb':
            m.sphere((0, 0, 0), 0.8, c1, 12, 8)
            m.box((0, 0, 0.85), (0.12, 0.12, 0.15), rgbf((110, 116, 130)))
            g.sphere((0, 0, 1.08), 0.22, rgbf(it['c2'], 1.7), 8, 5)
        elif icon == 'laser':
            g.box((0, -3.5, 0), (0.14, 4.0, 0.14), rgbf(it['c1'], 1.8))
            g.box((0, -3.5, 0), (0.06, 4.05, 0.06), (2.0, 2.0, 2.0, 1))
        elif icon in ('missile', 'arrow', 'drone', 'bird', 'shuriken', 'boomerang'):
            for (cx, cy, cz, hx, hy, hz, col, tx, ty, gl) in ent_boxes(it):
                (g if gl else m).box((cx, cz, cy), (hx, hz, hy), rgbf(col, 1.6 if gl else 1.0), taper=(tx, ty) if (tx != 1 or ty != 1) else None)
        elif icon == 'bee':
            for i in range(5):
                a = TAU * i / 5
                m.sphere((math.cos(a) * 0.9, math.sin(a) * 0.9, math.sin(a * 2) * 0.3), 0.32, c1, 8, 5)
                m.box((math.cos(a) * 0.9, math.sin(a) * 0.9, math.sin(a * 2) * 0.3 + 0.28), (0.25, 0.05, 0.02), (1, 1, 1, 1))
        else:
            m.sphere((0, 0, 0), 0.75, c1, 12, 8)
            if icon == 'target':
                m.annulus((0, 0, 0), 0.76, 0.86, c2, 'z', 18)
            elif icon in ('ball', 'balloon', 'pie'):
                m.sphere((-0.25, -0.25, 0.35), 0.2, c2, 6, 4)
        p = NodePath('proto')
        if m.v:
            mn = m.attach(p, 'm')
            mn.setTwoSided(True)
        if g.v:
            gn = g.attach(p, 'g')
            gn.setLightOff()
            gn.setTwoSided(True)
        if ring is not None:
            rn = ring.attach(p, 'ring')
            rn.setLightOff()
            rn.setTwoSided(True)
        if alpha:
            p.setTransparency(TransparencyAttrib.MAlpha)
        self.protos[key] = p
        return p

    def update(self, dt):
        self.t += dt
        t = self.t
        for b, (n, c) in zip(self.items.boxes, self.boxes):
            if b['t'] > 0:
                n.hide()
                continue
            n.show()
            n.setPos(*PV(b['x'], b['y'] + math.sin(t * 3.0 + b['ph']) * 0.18, b['z']))
            c.setH(math.degrees(b['ph'] + t * 1.8))
            hc = hue_rgb(t * 0.25 + b['ph'] / TAU)
            c.setColorScale(hc[0] / 255.0, hc[1] / 255.0, hc[2] / 255.0, 1)
        alive = set()
        for e in self.items.ents:
            if e.dead:
                continue
            alive.add(e.eid)
            n = self.ent_nodes.get(e.eid)
            if n is None:
                n = self.ent_nodes[e.eid] = self._proto(e).copyTo(self.root)
            self._place(e, n, t)
        for eid in [k for k in self.ent_nodes if k not in alive]:
            self.ent_nodes.pop(eid).removeNode()

    def _place(self, e, n, t):
        it = ITEMS[e.item]
        k = e.kind
        if k == 'trap':
            n.setPos(*PV(e.x, e.gy + 0.02, e.z))
            n.setH(math.degrees(e.h) + 180)
            if it['p'].get('shape') == 'fakebox':
                hc = hue_rgb(t * 0.25 + 0.5)
                n.setColorScale(hc[0] / 255.0, hc[1] / 255.0, hc[2] / 255.0, 1)
                n.setH(-t * 100.0)
            return
        n.setPos(*PV(e.x, e.y, e.z))
        icon = it['icon']
        if k == 'tornado' or icon in ('shuriken', 'boomerang', 'bee'):
            n.setH((t * 700.0) % 360.0)
        else:
            n.setH(math.degrees(e.h) + 180)
        if k == 'meteor':
            r = n.find('ring')
            if not r.isEmpty():
                r.setZ(e.gy - e.y + 0.15)
                r.setH(-n.getH())
        elif k == 'bomb' and e.state == 1:
            g = n.find('g')
            if not g.isEmpty():
                blink = int(t * (6 + e.age * 12)) % 2 == 0
                g.setColorScale((1.6, 0.2, 0.2, 1) if blink else (1, 1, 1, 1))

    def destroy(self):
        self.root.removeNode()
        self.ent_nodes = {}


class ScreenFxPC(object):
    """먹물(시야 가림) 얼룩 + 번개 번쩍임 (HUD 보다 아래 그려짐)"""

    def __init__(self, app):
        self.app = app
        self.root = app.aspect2d.attachNewNode('screenfx')
        self.root.setBin('background', 10)
        self.root.setDepthWrite(False)
        self.root.setDepthTest(False)
        tex = shared_tex('blob', lambda: tex_glow('blob', 64, 1.0))
        cm = CardMaker('ink')
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        self.ink = self.root.attachNewNode('ink')
        rnd = Rng(4321)
        for _ in range(9):
            c = self.ink.attachNewNode(cm.generate())
            c.setTexture(tex)
            c.setColor(0.05, 0.04, 0.1, 1)
            c.setPos((rnd() - 0.5) * 2.6, 0, (rnd() - 0.5) * 1.5)
            c.setScale(0.7 + rnd() * 0.8)
        self.ink.setTransparency(TransparencyAttrib.MAlpha)
        self.ink.hide()
        cf = CardMaker('flash')
        cf.setFrame(-3, 3, -2, 2)
        self.flash_np = self.root.attachNewNode(cf.generate())
        self.flash_np.setTransparency(TransparencyAttrib.MAlpha)
        self.flash_np.hide()
        self.flash = 0.0
        self.flash_col = (1, 1, 1)

    def update(self, blind_t, dt):
        if blind_t > 0:
            self.ink.show()
            self.ink.setAlphaScale(clamp(blind_t / 1.2, 0.0, 1.0) * 0.96)
        else:
            self.ink.hide()
        if self.flash > 0:
            self.flash_np.show()
            c = self.flash_col
            self.flash_np.setColor(c[0], c[1], c[2], clamp(self.flash * 1.6, 0.0, 0.66))
            self.flash = max(0.0, self.flash - dt)
        else:
            self.flash_np.hide()

    def clear(self):
        self.flash = 0.0
        self.ink.hide()
        self.flash_np.hide()
