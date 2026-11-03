
# ============================================================================
#  [PC] 맵 만들기 편집기 (마우스): 왼쪽 = 지도(그리기/옮기기/놓기), 오른쪽 = 도구판
#   왼쪽 버튼 = 도구 사용, 오른쪽 버튼 끌기 = 화면 이동, 휠 = 확대/축소, Ctrl+Z = 되돌리기, F = 전체 보기, Esc = 나가기
# ============================================================================
PC_ED_TABS = [('road', '길', 'Road'), ('obs', '장애물', 'Obstacles'), ('deco', '나무·장식', 'Nature'), ('pad', '발판·상자', 'Pads'),
              ('set', '설정', 'Settings')]
PC_ED_ROAD = [('draw', '길 그리기', 'Draw road'), ('move', '점 옮기기', 'Move point'), ('add', '점 추가', 'Add point'),
              ('del', '점 지우기', 'Delete point'), ('up', '높이기', 'Raise'), ('down', '낮추기', 'Lower'), ('start', '출발점', 'Start line'),
              ('pan', '화면 이동', 'Pan view')]
PC_ED_HINT = {
    'draw': ('왼쪽 버튼을 누른 채 코스를 한 바퀴 그리세요 (끝은 처음과 이어져요)', 'Hold the left button and draw one lap'),
    'move': ('점을 끌어서 옮기기 (빈 곳을 끌면 화면 이동)', 'Drag a point to move it (drag empty space to pan)'),
    'add': ('길 근처를 클릭하면 점 추가', 'Click near the road to add a point'),
    'del': ('지울 점을 클릭', 'Click a point to delete it'),
    'up': ('점을 클릭하면 그 부근 길이 4m 높아짐', 'Click a point to raise the road 4 m'),
    'down': ('점을 클릭하면 그 부근 길이 4m 낮아짐', 'Click a point to lower the road 4 m'),
    'start': ('출발선이 될 점을 클릭', 'Click the point for the start line'),
    'pan': ('끌어서 화면 이동 · 휠로 확대/축소', 'Drag to pan · wheel to zoom'),
    'erase': ('클릭하거나 끌어서 물건 지우기', 'Click or drag to erase objects'),
    'place': ('클릭해서 놓기 · 오른쪽 버튼 끌기로 화면 이동', 'Click to place · right-drag to pan'),
    'line': ('끌어서 선을 따라 줄지어 놓기', 'Drag to place a row along your line'),
}


class Draw2D(object):
    """aspect2d 위에 그릴 색 삼각형 묶음 (GeomNode 하나)"""

    def __init__(self):
        self.vd = GeomVertexData('d2', GeomVertexFormat.getV3c4(), Geom.UHStatic)
        self.vw = GeomVertexWriter(self.vd, 'vertex')
        self.cw = GeomVertexWriter(self.vd, 'color')
        self.pr = GeomTriangles(Geom.UHStatic)
        self.n = 0

    def tri(self, a, b, c, col):
        vw, cw = self.vw, self.cw
        for p in (a, b, c):
            vw.addData3(p[0], 0.0, p[1])
            cw.addData4(col[0], col[1], col[2], col[3] if len(col) > 3 else 1.0)
        self.pr.addVertices(self.n, self.n + 1, self.n + 2)
        self.n += 3

    def quad(self, a, b, c, d, col):
        self.tri(a, b, c, col)
        self.tri(a, c, d, col)

    def rect(self, x0, z0, x1, z1, col):
        self.quad((x0, z0), (x1, z0), (x1, z1), (x0, z1), col)

    def circle(self, x, z, r, col, seg=12):
        for k in range(seg):
            a0 = TAU * k / seg
            a1 = TAU * (k + 1) / seg
            self.tri((x, z), (x + math.cos(a0) * r, z + math.sin(a0) * r), (x + math.cos(a1) * r, z + math.sin(a1) * r), col)

    def line(self, a, b, w, col):
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz)
        if L < 1e-9:
            return
        nx, nz = -dz / L * w * 0.5, dx / L * w * 0.5
        self.quad((a[0] + nx, a[1] + nz), (b[0] + nx, b[1] + nz), (b[0] - nx, b[1] - nz), (a[0] - nx, a[1] - nz), col)

    def node(self, name):
        g = Geom(self.vd)
        g.addPrimitive(self.pr)
        gn = GeomNode(name)
        gn.addGeom(g)
        return gn


def _cf(c, k=1.0, a=1.0):
    return (min(1.0, c[0] / 255.0 * k), min(1.0, c[1] / 255.0 * k), min(1.0, c[2] / 255.0 * k), a)


class PCMapMaker(object):
    PANEL_W = 0.98

    def __init__(self, app):
        self.app = app
        self.ed = None
        self.uid = None
        self.tab = 'road'
        self.tool = 'draw'
        self.kinds = {'obs': 'cone', 'deco': 'pine', 'pad': 'pad'}
        self.line = False
        self.erase = False
        self.size = 1.0
        self.view = None
        self.root = None
        self.cv_np = None
        self.ov_np = None
        self.ui_np = None
        self.buttons = []
        self.texts = {}
        self.need_cv = True
        self.need_ui = True
        self.down = None           # 왼쪽 버튼 누른 위치 (aspect2d)
        self.moved = False
        self.stroke = None
        self.drag_pt = -1
        self.pan_last = None
        self.last_m = None
        self.msg = ''
        self.msg_t = 0.0
        self.confirm = None
        self.set_page = 0
        self.kind_page = 0
        self.import_mid = 1
        self.mouse_override = None  # 테스트용 (aspect2d 좌표)
        self.events = False

    # ------------------------------------------------------------------ 열기/닫기
    def say(self, ko, en, secs=2.2):
        self.msg = T(ko, en)
        self.msg_t = time.time() + secs
        self.need_ui = True

    def open(self, data, uid):
        self.ed = MapEdit(data)
        self.uid = uid
        self.view = None
        self.confirm = None
        self.stroke = None
        self.drag_pt = -1
        if not uid:
            self.tab, self.tool = 'road', 'draw'
            self.say('먼저 [길 그리기]로 코스를 그려 보세요 (기본 타원 코스로 바로 달릴 수도 있어요)',
                     'Draw your course with [Draw road] - or race the default oval right away', 5.0)
        self.app.go('editor')

    def enter(self):
        app = self.app
        app.menu.show(False)
        app.menu.clear_extra()
        self.leave_ui()
        self.root = app.aspect2d.attachNewNode('editor')
        self.cv_np = self.root.attachNewNode('canvas')
        self.ov_np = self.root.attachNewNode('overlay')
        self.ui_np = self.root.attachNewNode('editor-ui')
        for n in (self.cv_np, self.ov_np, self.ui_np):
            n.setTwoSided(True)
            n.setLightOff()
            n.setTransparency(TransparencyAttrib.MAlpha)
        self.need_cv = self.need_ui = True
        if not self.events:
            for ev, fn in (('mouse1', self.on_down), ('mouse1-up', self.on_up), ('mouse3', self.on_rdown), ('mouse3-up', self.on_rup),
                           ('wheel_up', lambda: self.on_wheel(1)), ('wheel_down', lambda: self.on_wheel(-1))):
                app.accept(ev, fn)
            self.events = True
        if self.view is None:
            self.fit()

    def leave_ui(self):
        if self.root is not None:
            self.root.removeNode()
        self.root = self.cv_np = self.ov_np = self.ui_np = None
        self.buttons = []
        self.texts = {}
        if self.events:
            for ev in ('mouse1', 'mouse1-up', 'mouse3', 'mouse3-up', 'wheel_up', 'wheel_down'):
                self.app.ignore(ev)
            self.events = False

    def save(self):
        d = self.ed.result()
        if d is None:
            self.say('저장할 수 없어요', 'Cannot save')
            return False
        d['uid'] = self.uid or ''
        uid = self.app.store.put(d)
        if uid is None:
            self.say('저장 실패', 'Save failed')
            return False
        self.uid = uid
        self.ed.data['uid'] = uid
        self.ed.dirty = False
        self.say('저장했어요', 'Saved')
        return True

    def try_exit(self):
        if self.ed is not None and self.ed.dirty:
            self.confirm = 'exit'
            self.need_ui = True
        else:
            self.leave()

    def leave(self):
        self.confirm = None
        self.leave_ui()
        self.ed = None
        self.app.go('maps')

    def test_drive(self):
        d = self.ed.result()
        if d is None:
            self.say('맵을 만들 수 없어요', 'Cannot build this map')
            return
        app = self.app
        p = app.profile
        entries = solo_entries(p.display_name(), p['kart'], int(p['bots']))
        app.test_map = d
        self.leave_ui()
        app.start_race(d, int(d['laps']), entries, False, True, 3.0, p['mode'] == 'item')

    # ------------------------------------------------------------------ 좌표
    def canvas_rect(self):
        a = self.app.getAspectRatio()
        return (-a + 0.02, a - self.PANEL_W - 0.03, -0.98, 0.98)

    def fit(self):
        d = self.ed.data
        xs = [p[0] for p in d['pts']] + [o[1] for o in d['objs']]
        zs = [p[1] for p in d['pts']] + [o[2] for o in d['objs']]
        x0, x1, z0, z1 = self.canvas_rect()
        w0, w1, v0, v1 = min(xs) - 40, max(xs) + 40, min(zs) - 40, max(zs) + 40
        sc = min((x1 - x0) / max(w1 - w0, 60.0), (z1 - z0) / max(v1 - v0, 60.0))
        self.view = [(w0 + w1) / 2.0, (v0 + v1) / 2.0, clamp(sc, 0.0002, 0.05)]
        self.need_cv = True

    def to_screen(self, x, z):
        cx, cz, sc = self.view
        x0, x1, z0, z1 = self.canvas_rect()
        return ((x0 + x1) / 2.0 + (x - cx) * sc, (z0 + z1) / 2.0 - (z - cz) * sc)

    def to_world(self, X, Z):
        cx, cz, sc = self.view
        x0, x1, z0, z1 = self.canvas_rect()
        return (cx + (X - (x0 + x1) / 2.0) / sc, cz - (Z - (z0 + z1) / 2.0) / sc)

    def in_canvas(self, m):
        x0, x1, z0, z1 = self.canvas_rect()
        return m is not None and x0 <= m[0] <= x1 and z0 <= m[1] <= z1

    def mouse(self):
        if self.mouse_override is not None:
            return self.mouse_override
        mw = self.app.mouseWatcherNode
        if mw is None or not mw.hasMouse():
            return None
        m = mw.getMouse()
        return (m.getX() * self.app.getAspectRatio(), m.getY())

    def zoom(self, k, at=None):
        if at is None:
            x0, x1, z0, z1 = self.canvas_rect()
            at = ((x0 + x1) / 2.0, (z0 + z1) / 2.0)
        wx, wz = self.to_world(*at)
        self.view[2] = clamp(self.view[2] * k, 0.0002, 0.05)
        nx, nz = self.to_world(*at)
        self.view[0] += wx - nx
        self.view[1] += wz - nz
        self.need_cv = True

    def pan(self, dX, dZ):
        sc = self.view[2]
        W = CMAP_WORLD + 200
        self.view[0] = clamp(self.view[0] - dX / sc, -W, W)
        self.view[1] = clamp(self.view[1] + dZ / sc, -W, W)
        self.need_cv = True

    def hit_m(self):
        return 0.035 / self.view[2]

    # ------------------------------------------------------------------ 입력
    def mode_of(self):
        if self.tab == 'road':
            return {'draw': 'stroke', 'move': 'point', 'pan': 'pan'}.get(self.tool, 'tap')
        if self.tab == 'set':
            return 'pan'
        if self.erase:
            return 'erase'
        return 'stroke' if self.line else 'tap'

    def busy(self):
        return self.ed is None or self.app.input.active or self.app.scene != 'editor'

    def on_down(self):
        if self.busy():
            return
        m = self.mouse()
        if m is None:
            return
        for (x0, x1, z0, z1, cb) in reversed(self.buttons):
            if x0 <= m[0] <= x1 and z0 <= m[1] <= z1:
                self.app.sfx_play('click', 0.4)
                cb()
                self.need_ui = True
                return
        if self.confirm is not None or not self.in_canvas(m):
            return
        self.down = m
        self.last_m = m
        self.moved = False
        mode = self.mode_of()
        wx, wz = self.to_world(*m)
        self.stroke = None
        self.drag_pt = -1
        if mode == 'stroke':
            self.stroke = [(wx, wz)]
        elif mode == 'point':
            i = self.ed.nearest_point(wx, wz, self.hit_m())
            if i >= 0:
                self.ed.snapshot()
                self.drag_pt = i
        elif mode == 'erase':
            if self.ed.erase_at(wx, wz, self.hit_m() * 0.7):
                self.need_cv = True

    def on_up(self):
        if self.down is None or self.busy():
            self.down = None
            return
        m = self.mouse() or self.last_m
        mode = self.mode_of()
        ed = self.ed
        wx, wz = self.to_world(*m)
        moved = self.moved
        self.down = None
        if mode == 'stroke' and self.stroke is not None:
            st = self.stroke
            self.stroke = None
            if self.tab == 'road':
                if len(st) > 4 and moved:
                    if ed.set_stroke(st):
                        self.say('길을 만들었어요! 점을 옮겨서 다듬을 수 있어요', 'Road created! Move points to fine-tune it')
                    else:
                        self.say('너무 짧아요. 화면을 크게 써서 한 바퀴 그려 주세요', 'Too short - draw a bigger loop')
            else:
                kind = self.kinds[self.tab]
                if not moved or len(st) < 2:
                    ed.add_obj(kind, wx, wz, OBJ_INFO[kind]['s'] * self.size)
                else:
                    n = ed.add_line(kind, st, OBJ_INFO[kind]['s'] * self.size)
                    if n:
                        self.say('%d개 놓았어요' % n, 'Placed %d' % n, 1.4)
                if ed.msg == 'full':
                    ed.msg = ''
                    self.say('물건이 너무 많아요 (최대 %d개)' % CMAP_MAX_OBJS, 'Too many objects (max %d)' % CMAP_MAX_OBJS)
            self.need_cv = True
        elif mode == 'point':
            if self.drag_pt >= 0:
                self.drag_pt = -1
                self.need_cv = True
        elif mode == 'tap' and not moved:
            self.tap(wx, wz)
        self.need_ui = True

    def tap(self, wx, wz):
        ed = self.ed
        if self.tab == 'road':
            tool = self.tool
            if tool == 'add':
                ed.insert_point(wx, wz)
            else:
                i = ed.nearest_point(wx, wz, self.hit_m())
                if i < 0:
                    self.say('점(동그라미)을 클릭해 주세요', 'Click on a point (circle)', 1.4)
                    return
                if tool == 'del':
                    if not ed.delete_point(i):
                        self.say('점이 4개보다 적을 수는 없어요', 'Need at least 4 points')
                elif tool in ('up', 'down'):
                    ed.raise_point(i, 4.0 if tool == 'up' else -4.0)
                elif tool == 'start':
                    ed.set_start(i)
                    self.say('출발선을 옮겼어요', 'Start line moved', 1.4)
        elif self.tab in ('obs', 'deco', 'pad'):
            kind = self.kinds[self.tab]
            if not ed.add_obj(kind, wx, wz, OBJ_INFO[kind]['s'] * self.size) and ed.msg == 'full':
                ed.msg = ''
                self.say('물건이 너무 많아요 (최대 %d개)' % CMAP_MAX_OBJS, 'Too many objects (max %d)' % CMAP_MAX_OBJS)
        self.need_cv = True

    def on_rdown(self):
        if self.busy():
            return
        m = self.mouse()
        if self.in_canvas(m):
            self.pan_last = m

    def on_rup(self):
        self.pan_last = None

    def on_wheel(self, d):
        if self.busy():
            return
        m = self.mouse()
        if self.in_canvas(m):
            self.zoom(1.2 ** d, m)

    def on_key(self, k):
        app = self.app
        if k == 'escape':
            if self.confirm is not None:
                self.confirm = None
                self.need_ui = True
            else:
                self.try_exit()
        elif k == 'z' and ('lcontrol' in app.keys or 'rcontrol' in app.keys):
            if self.ed.undo():
                self.need_cv = self.need_ui = True
        elif k == 'f':
            self.fit()

    def update(self, dt):
        if self.ed is None or self.root is None:
            return
        m = self.mouse()
        if m is not None and self.pan_last is not None:
            self.pan(m[0] - self.pan_last[0], m[1] - self.pan_last[1])
            self.pan_last = m
        if self.down is not None and m is not None and m != self.last_m:
            if not self.moved and math.hypot(m[0] - self.down[0], m[1] - self.down[1]) > 0.012:
                self.moved = True
            mode = self.mode_of()
            wx, wz = self.to_world(*m)
            if mode == 'stroke' and self.stroke is not None:
                lx, lz = self.stroke[-1]
                if math.hypot(wx - lx, wz - lz) * self.view[2] > 0.006:
                    self.stroke.append((wx, wz))
            elif mode == 'point' and self.drag_pt >= 0:
                self.ed.move_point(self.drag_pt, wx, wz, snap=False)
            elif mode == 'erase':
                objs = self.ed.data['objs']
                rad = self.hit_m() * 0.7
                keep = [o for o in objs if (o[1] - wx) ** 2 + (o[2] - wz) ** 2 >= (rad + OBJ_INFO[o[0]]['rad'] * o[3] * 0.5) ** 2]
                if len(keep) != len(objs):
                    self.ed.data['objs'] = keep
                    self.ed.dirty = True
                    self.need_cv = True
            elif self.moved:
                self.pan(m[0] - self.last_m[0], m[1] - self.last_m[1])
            self.last_m = m
        if self.need_cv:
            self.need_cv = False
            self.build_canvas()
            self.need_ui = True
        self.build_overlay()
        if self.need_ui or (self.msg and time.time() > self.msg_t):
            if self.msg and time.time() > self.msg_t:
                self.msg = ''
            self.need_ui = False
            self.build_ui()

    # ------------------------------------------------------------------ 지도 그리기
    def build_canvas(self):
        if self.cv_np is None:
            return
        for c in self.cv_np.getChildren():
            c.removeNode()
        D = Draw2D()
        x0, x1, z0, z1 = self.canvas_rect()
        d = self.ed.data
        th = biome(d['look'])
        g0 = hex_rgb(th['ground'][0])
        D.rect(x0, z0, x1, z1, _cf(g0, 0.42))
        sc = self.view[2]
        step = 50.0 if sc > 0.0012 else 200.0
        gcol = _cf(g0, 0.55)
        wa = self.to_world(x0, z1)
        wb = self.to_world(x1, z0)
        gx = math.floor(wa[0] / step) * step
        while gx <= wb[0]:
            X = self.to_screen(gx, 0)[0]
            D.line((X, z0), (X, z1), 0.002, gcol)
            gx += step
        gz = math.floor(wa[1] / step) * step
        while gz <= wb[1]:
            Z = self.to_screen(0, gz)[1]
            D.line((x0, Z), (x1, Z), 0.002, gcol)
            gz += step
        W = CMAP_WORLD
        corners = [self.to_screen(-W, -W), self.to_screen(W, -W), self.to_screen(W, W), self.to_screen(-W, W)]
        for k in range(4):
            D.line(corners[k], corners[(k + 1) % 4], 0.004, (0.8, 0.3, 0.3, 1))
        tr = self.ed.preview()
        if tr is not None:
            N = tr.N
            stp = 1 if sc > 0.004 else 2
            idxs = list(range(0, N, stp)) + [0]
            sh = tr.hw + tr.SH

            def edge(i, off):
                return self.to_screen(tr.px[i] + tr.rx[i] * off, tr.pz[i] + tr.rz[i] * off)
            L1 = [edge(i, -sh) for i in idxs]
            R1 = [edge(i, sh) for i in idxs]
            L0 = [edge(i, -tr.hw) for i in idxs]
            R0 = [edge(i, tr.hw) for i in idxs]
            grass = _cf(g0, 0.8)
            road = _cf(hex_rgb(th['road']), 1.5)
            wallc = _cf(hex_rgb(th['wall'][0]))
            for k in range(len(idxs) - 1):
                D.quad(L1[k], L1[k + 1], R1[k + 1], R1[k], grass)
            for k in range(len(idxs) - 1):
                D.quad(L0[k], L0[k + 1], R0[k + 1], R0[k], road)
            for k in range(len(idxs) - 1):
                D.line(L1[k], L1[k + 1], 0.003, wallc)
                D.line(R1[k], R1[k + 1], 0.003, wallc)
            if tr.max_y - tr.min_y > 1.0:
                for k in range(len(idxs) - 1):
                    f = (tr.py[idxs[k]] - tr.min_y) / (tr.max_y - tr.min_y)
                    c = mix_rgb((70, 90, 160), (255, 240, 160), f)
                    D.line(self.to_screen(tr.px[idxs[k]], tr.pz[idxs[k]]), self.to_screen(tr.px[idxs[k + 1]], tr.pz[idxs[k + 1]]), 0.003, _cf(c))
            a, b = edge(0, -tr.hw), edge(0, tr.hw)
            for k in range(8):
                p0 = (a[0] + (b[0] - a[0]) * k / 8.0, a[1] + (b[1] - a[1]) * k / 8.0)
                p1 = (a[0] + (b[0] - a[0]) * (k + 1) / 8.0, a[1] + (b[1] - a[1]) * (k + 1) / 8.0)
                D.line(p0, p1, 0.008, (1, 1, 1, 1) if k % 2 == 0 else (0.08, 0.08, 0.08, 1))
            j = min(N - 1, int(18 / tr.ds) + 1)
            c0 = self.to_screen(tr.px[0], tr.pz[0])
            c1 = self.to_screen(tr.px[j], tr.pz[j])
            ang = math.atan2(c1[1] - c0[1], c1[0] - c0[0])
            L = max(0.03, min(0.09, tr.width * sc * 1.2))
            tip = (c0[0] + math.cos(ang) * L, c0[1] + math.sin(ang) * L)
            D.line(c0, tip, 0.007, (1, 0.86, 0.24, 1))
            for da in (2.6, -2.6):
                D.line(tip, (tip[0] + math.cos(ang + da) * 0.022, tip[1] + math.sin(ang + da) * 0.022), 0.007, (1, 0.86, 0.24, 1))
        for o in d['objs']:
            info = OBJ_INFO[o[0]]
            p = self.to_screen(o[1], o[2])
            if not (x0 - 0.1 <= p[0] <= x1 + 0.1 and z0 - 0.1 <= p[1] <= z1 + 0.1):
                continue
            col = _cf(info['col'])
            cat = info['cat']
            if cat == 'road':
                hl = (4.5 if o[0] == 'pad' else 3.3) * o[3] * sc
                hwp = 2.8 * o[3] * sc
                if o[0] == 'box':
                    hl, hwp = 1.2 * sc, (tr.hw if tr is not None else 8.0) * sc
                hl, hwp = max(hl, 0.006), max(hwp, 0.005)
                fx_, fz_ = math.sin(o[4]), -math.cos(o[4])
                rx_, rz_ = -fz_, fx_
                pts = [(p[0] + fx_ * a_ * hl + rx_ * b_ * hwp, p[1] + fz_ * a_ * hl + rz_ * b_ * hwp) for (a_, b_) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                D.quad(pts[0], pts[1], pts[2], pts[3], col)
                continue
            rad = info['rad'] * o[3]
            if o[0] == 'building':
                rad = (14 + clamp((o[3] - 0.3) / 2.7, 0.0, 1.0) * 22) * 0.45
            if cat == 'obs':
                pr = max(0.006, rad * sc)
            else:
                pr = max(0.007, min(rad * sc * 2.2, 0.06))
            if o[0] in ('volcano', 'building'):
                pr = max(0.008, rad * sc)
            D.circle(p[0], p[1], pr * 1.18, (0, 0, 0, 1), 10)
            D.circle(p[0], p[1], pr, col, 10)
            if o[0] in ('lavapillar', 'volcano'):
                D.circle(p[0], p[1], pr * 0.42, (1, 0.85, 0.45, 1), 8)
        big = self.tab == 'road' and self.tool not in ('draw', 'pan')
        pr = 0.011 if big else 0.006
        for i, p in enumerate(d['pts']):
            q = self.to_screen(p[0], p[1])
            c = (1, 1, 1, 1)
            if p[2] > 0.5:
                c = (1, 0.78, 0.35, 1)
            elif p[2] < -0.5:
                c = (0.47, 0.67, 1, 1)
            if i == 0:
                D.circle(q[0], q[1], pr + 0.009, (0, 0, 0, 1), 12)
                D.circle(q[0], q[1], pr + 0.007, (0.3, 1, 0.47, 1), 12)
            D.circle(q[0], q[1], pr + 0.002, (0, 0, 0, 1), 10)
            D.circle(q[0], q[1], pr, c, 10)
        self.cv_np.attachNewNode(D.node('map2d'))

    def build_overlay(self):
        if self.ov_np is None:
            return
        for c in self.ov_np.getChildren():
            c.removeNode()
        D = Draw2D()
        any_ = False
        if self.stroke and len(self.stroke) > 1:
            pts = [self.to_screen(x, z) for x, z in self.stroke]
            col = (1, 0.9, 0.35, 1) if self.tab == 'road' else _cf(OBJ_INFO[self.kinds.get(self.tab, 'cone')]['col'])
            for a, b in zip(pts, pts[1:]):
                D.line(a, b, 0.012, (0, 0, 0, 1))
            for a, b in zip(pts, pts[1:]):
                D.line(a, b, 0.006, col)
            any_ = True
        if self.drag_pt >= 0:
            pts = [self.to_screen(p[0], p[1]) for p in self.ed.data['pts']]
            for k in range(len(pts)):
                D.line(pts[k], pts[(k + 1) % len(pts)], 0.004, (1, 0.9, 0.35, 1))
            q = pts[self.drag_pt]
            D.circle(q[0], q[1], 0.02, (1, 0.9, 0.35, 1), 14)
            any_ = True
        if any_:
            self.ov_np.attachNewNode(D.node('overlay'))

    # ------------------------------------------------------------------ 도구판
    def text(self, txt, x, z, scale, fg=(1, 1, 1, 1), align='l', maxw=None):
        tn_align = TextNode.ALeft if align == 'l' else (TextNode.ACenter if align == 'c' else TextNode.ARight)
        kw = dict(parent=self.ui_np, mayChange=False, shadow=(0, 0, 0, 1), align=tn_align)
        if self.app.font is not None:
            kw['font'] = self.app.font
        t = OnscreenText(text=txt, pos=(x, z), scale=scale, fg=fg, **kw)
        if maxw is not None:
            try:
                w = t.textNode.calcWidth(txt) * scale
                if w > maxw > 0:
                    t.setScale(scale * maxw / w)
            except Exception:
                pass
        return t

    def card(self, x0, z0, x1, z1, col):
        cm = CardMaker('c')
        cm.setFrame(x0, x1, z0, z1)
        n = self.ui_np.attachNewNode(cm.generate())
        n.setColor(*col)
        return n

    def button(self, x0, z0, x1, z1, label, cb, kind='normal', enabled=True, swatch=None):
        cols = {'normal': (0.16, 0.19, 0.31, 0.95), 'on': (0.1, 0.75, 0.88, 0.98), 'primary': (0.92, 0.27, 0.27, 0.98),
                'good': (0.16, 0.63, 0.35, 0.98), 'danger': (0.67, 0.16, 0.22, 0.98), 'ghost': (0.09, 0.1, 0.17, 0.95)}
        col = cols.get(kind, cols['normal']) if enabled else (0.2, 0.2, 0.24, 0.9)
        self.card(x0, z0, x1, z1, col)
        h = z1 - z0
        fg = (0.02, 0.08, 0.13, 1) if kind == 'on' else ((1, 1, 1, 1) if enabled else (0.55, 0.55, 0.6, 1))
        if swatch is not None:
            self.card(x0 + 0.008, z1 - 0.008 - h * 0.28, x0 + 0.008 + h * 0.28, z1 - 0.008, _cf(swatch))
        self.text(label, (x0 + x1) / 2.0, (z0 + z1) / 2.0 - h * 0.18, min(0.045, h * 0.5), fg, 'c', maxw=(x1 - x0) - 0.02)
        if enabled:
            self.buttons.append((x0, x1, z0, z1, cb))

    def stepper(self, x0, z, w, h, label, value, on_d):
        self.text(label, x0, z - h * 0.65, min(0.042, h * 0.5), (0.82, 0.86, 0.96, 1), maxw=w * 0.38)
        bw = h * 1.1
        lx = x0 + w * 0.4
        self.button(lx, z - h, lx + bw, z, '<', lambda: on_d(-1))
        self.button(x0 + w - bw, z - h, x0 + w, z, '>', lambda: on_d(1))
        self.text(str(value), (lx + bw + x0 + w - bw) / 2.0, z - h * 0.68, min(0.045, h * 0.52), (1, 0.86, 0.47, 1), 'c', maxw=(w - lx + x0 - 2 * bw) - 0.02)

    def build_ui(self):
        if self.ui_np is None:
            return
        for c in self.ui_np.getChildren():
            c.removeNode()
        self.buttons = []
        a = self.app.getAspectRatio()
        ed = self.ed
        d = ed.data
        x0, x1, z0, z1 = self.canvas_rect()
        # 지도 바깥으로 삐져나온 그림 가리기 (잘라내기 대신 불투명한 테두리)
        frame = (0.03, 0.04, 0.08, 1)
        self.card(-a - 0.2, -1.2, x0, 1.2, frame)
        self.card(x1, -1.2, a + 0.2, 1.2, frame)
        self.card(x0, z1, x1, 1.2, frame)
        self.card(x0, -1.2, x1, z0, frame)
        # 지도 위 글자
        tr = ed.preview()
        self.text(d['name'] + ('  *' if ed.dirty else ''), x0 + 0.03, z1 - 0.07, 0.06)
        if tr is not None:
            self.text(T('%.2f km · 폭 %dm · 조절점 %d · 물건 %d' % (tr.length / 1000.0, d['width'], len(d['pts']), len(d['objs'])),
                        '%.2f km · width %dm · %d points · %d objects' % (tr.length / 1000.0, d['width'], len(d['pts']), len(d['objs']))),
                      x0 + 0.03, z1 - 0.13, 0.038, (0.8, 0.86, 0.98, 1))
        wz = z1 - 0.19
        for wtxt in ed.warnings(LANG)[:2]:
            self.text('! ' + wtxt, x0 + 0.03, wz, 0.036, (1, 0.6, 0.45, 1))
            wz -= 0.05
        hint = self.msg if self.msg else self.hint()
        if hint:
            self.text(hint, x0 + 0.03, z0 + 0.03, 0.036, (1, 0.9, 0.6, 1), maxw=(x1 - x0) - 0.3)
        zb = 0.085
        for i, (lab, fn) in enumerate((('+', lambda: self.zoom(1.4)), ('-', lambda: self.zoom(1 / 1.4)), (T('전체', 'Fit'), self.fit))):
            self.button(x1 - zb - 0.02, z1 - 0.02 - (i + 1) * (zb + 0.012), x1 - 0.02, z1 - 0.02 - i * (zb + 0.012) - 0.012, lab, fn, 'ghost')
        # 오른쪽 도구판
        px0, px1 = a - self.PANEL_W, a - 0.02
        self.card(px0, -0.98, px1, 0.98, (0.06, 0.08, 0.16, 1))
        pw = px1 - px0 - 0.04
        x = px0 + 0.02
        z = 0.95
        tw = (pw - 4 * 0.01) / 5.0
        for i, (key, ko, en) in enumerate(PC_ED_TABS):
            def pick(k=key):
                self.tab = k
                self.erase = False
                self.need_cv = True
            self.button(x + i * (tw + 0.01), z - 0.08, x + i * (tw + 0.01) + tw, z, T(ko, en), pick, 'on' if self.tab == key else 'normal')
        z -= 0.1
        bz = -0.96
        bh = 0.09
        q = (pw - 3 * 0.01) / 4.0
        acts = [(T('되돌리기', 'Undo'), self.undo, 'normal', bool(ed.undo_stack)), (T('저장', 'Save'), self.save, 'good', True),
                (T('시험 주행', 'Test drive'), self.test_drive, 'primary', True), (T('나가기', 'Exit'), self.try_exit, 'ghost', True)]
        for i, (lab, fn, kind, en) in enumerate(acts):
            self.button(x + i * (q + 0.01), bz, x + i * (q + 0.01) + q, bz + bh, lab, fn, kind, en)
        top, bottom = z, bz + bh + 0.02
        if self.tab == 'road':
            self.ui_road(x, pw, top, bottom)
        elif self.tab in ('obs', 'deco', 'pad'):
            self.ui_objs(x, pw, top, bottom)
        else:
            self.ui_settings(x, pw, top, bottom)
        if self.confirm is not None:
            self.ui_confirm()

    def hint(self):
        if self.tab == 'set':
            return ''
        if self.tab == 'road':
            k = self.tool
        elif self.erase:
            k = 'erase'
        else:
            k = 'line' if self.line else 'place'
        h = PC_ED_HINT.get(k)
        return T(h[0], h[1]) if h else ''

    def undo(self):
        if self.ed.undo():
            self.need_cv = True

    def ui_road(self, x, pw, top, bottom):
        bw = (pw - 0.01) / 2.0
        bh = 0.085
        for i, (key, ko, en) in enumerate(PC_ED_ROAD):
            def pick(k=key):
                self.tool = k
                self.need_cv = True
            cx_ = x + (i % 2) * (bw + 0.01)
            cz = top - (i // 2) * (bh + 0.012)
            self.button(cx_, cz - bh, cx_ + bw, cz, T(ko, en), pick, 'on' if self.tool == key else 'normal')
        z = top - 4 * (bh + 0.012) - 0.02

        def rev():
            self.ed.reverse()
            self.need_cv = True
            self.say('달리는 방향을 바꿨어요', 'Direction reversed', 1.4)

        def center():
            d = self.ed.data
            xs = [p[0] for p in d['pts']]
            zs = [p[1] for p in d['pts']]
            self.ed.move_all(-(min(xs) + max(xs)) / 2.0, -(min(zs) + max(zs)) / 2.0)
            self.fit()
        self.button(x, z - bh, x + bw, z, T('방향 반대로', 'Reverse direction'), rev)
        self.button(x + bw + 0.01, z - bh, x + pw, z, T('가운데로 옮기기', 'Recenter'), center)
        z -= bh + 0.03
        self.text(T('조절점 색: 노랑 = 높음, 파랑 = 낮음, 초록 = 출발점', 'Point colors: yellow = high, blue = low, green = start'), x, z - 0.03, 0.032,
                  (0.7, 0.78, 0.95, 1), maxw=pw)
        self.text(T('마우스: 왼쪽 = 도구, 오른쪽 끌기 = 이동, 휠 = 확대', 'Mouse: left = tool, right-drag = pan, wheel = zoom'), x, z - 0.08, 0.032,
                  (0.7, 0.78, 0.95, 1), maxw=pw)
        self.text(T('Ctrl+Z 되돌리기 · F 전체 보기 · Esc 나가기', 'Ctrl+Z undo · F fit · Esc exit'), x, z - 0.13, 0.032, (0.7, 0.78, 0.95, 1), maxw=pw)

    def ui_objs(self, x, pw, top, bottom):
        cat = self.tab
        kinds = OBJ_BY_CAT['obs' if cat == 'obs' else ('deco' if cat == 'deco' else 'road')]
        cols = 3 if cat != 'pad' else 2
        bh = 0.08
        ctrl = 2 * (bh + 0.012) + 0.02
        avail = top - bottom - ctrl
        rows_fit = max(1, int((avail + 0.01) // (bh + 0.01)))
        per = len(kinds)
        if (len(kinds) + cols - 1) // cols > rows_fit:
            per = rows_fit * cols - 2
        npg = max(1, (len(kinds) + per - 1) // per)
        self.kind_page = int(clamp(self.kind_page, 0, npg - 1))
        shown = kinds[self.kind_page * per:(self.kind_page + 1) * per]
        bw = (pw - (cols - 1) * 0.01) / float(cols)
        cur = self.kinds[cat]
        cells = len(shown) + (2 if npg > 1 else 0)
        for i in range(cells):
            cx_ = x + (i % cols) * (bw + 0.01)
            cz = top - (i // cols) * (bh + 0.01)
            if i < len(shown):
                k = shown[i]

                def pick(k=k):
                    self.kinds[cat] = k
                    self.erase = False
                self.button(cx_, cz - bh, cx_ + bw, cz, obj_name(k, LANG), pick, 'on' if (k == cur and not self.erase) else 'normal', swatch=OBJ_INFO[k]['col'])
            elif i == len(shown):
                self.button(cx_, cz - bh, cx_ + bw, cz, '<', lambda: setattr(self, 'kind_page', self.kind_page - 1), enabled=self.kind_page > 0)
            else:
                self.button(cx_, cz - bh, cx_ + bw, cz, '>  %d/%d' % (self.kind_page + 1, npg), lambda: setattr(self, 'kind_page', self.kind_page + 1),
                            enabled=self.kind_page < npg - 1)
        z = bottom + ctrl
        third = (pw - 0.02) / 3.0

        def single():
            self.line = False
            self.erase = False

        def row():
            self.line = True
            self.erase = False

        def eraser():
            self.erase = not self.erase
        self.button(x, z - bh, x + third, z, T('한 개씩', 'Single'), single, 'on' if not self.line and not self.erase else 'normal')
        self.button(x + third + 0.01, z - bh, x + 2 * third + 0.01, z, T('줄로 놓기', 'Draw a row'), row, 'on' if self.line and not self.erase else 'normal')
        self.button(x + 2 * (third + 0.01), z - bh, x + pw, z, T('지우개', 'Eraser'), eraser, 'danger' if self.erase else 'normal')
        z -= bh + 0.012

        def size(dd):
            self.size = round(clamp(self.size + dd * 0.1, 0.4, 3.0), 2)
        self.stepper(x, z, pw, bh, T('크기', 'Size'), '%d%%' % int(round(self.size * 100)), size)

    def ui_settings(self, x, pw, top, bottom):
        ed = self.ed
        d = ed.data
        bh = 0.075
        gap = 0.012
        z = top

        def setv(key, val):
            ed.set(key, val)
            self.need_cv = True
        if self.set_page == 0:
            def rename():
                def done(t):
                    t = t.strip()
                    if t:
                        setv('name', t)
                    self.need_ui = True
                self.app.input.begin(T('맵 이름 (Enter 확인)', 'Map name (Enter = OK)'), d['name'], 20, 'alpha', done)
            self.button(x, z - bh, x + pw, z, T('이름: ', 'Name: ') + d['name'], rename)
            z -= bh + gap
            fam, ti, mi = biome_parts(d['look'])
            fname, tname, mname = biome_part_names(d['look'], LANG)
            self.stepper(x, z, pw, bh, T('바이옴', 'Biome'), fname, lambda k: setv('look', biome_map(fam + k, ti, mi)))
            z -= bh + gap
            self.stepper(x, z, pw, bh, T('시간대', 'Time'), tname, lambda k: setv('look', biome_map(fam, ti + k, mi)))
            z -= bh + gap
            self.stepper(x, z, pw, bh, T('색감', 'Mood'), mname, lambda k: setv('look', biome_map(fam, ti, mi + k)))
            z -= bh + gap
            wl = CMAP_WEATHERS
            self.stepper(x, z, pw, bh, T('날씨', 'Weather'), (CMAP_WEATHER_KO if LANG == 'ko' else CMAP_WEATHER_EN)[d['weather']],
                         lambda k: setv('weather', wl[(wl.index(d['weather']) + k) % len(wl)]))
            z -= bh + gap
            self.stepper(x, z, pw, bh, T('자동 장식', 'Auto scenery'), (CMAP_DECO_KO if LANG == 'ko' else CMAP_DECO_EN)[d['deco']],
                         lambda k: setv('deco', int(clamp(d['deco'] + k, 0, 3))))
            z -= bh + gap
        else:
            self.stepper(x, z, pw, bh, T('도로 폭', 'Road width'), '%dm' % d['width'], lambda k: setv('width', clamp(d['width'] + k * 2, 10, 30)))
            z -= bh + gap
            self.stepper(x, z, pw, bh, T('언덕', 'Hills'), '%d%%' % int(round(d['hills'] * 100)), lambda k: setv('hills', round(clamp(d['hills'] + k * 0.1, 0.0, 1.0), 2)))
            z -= bh + gap
            self.stepper(x, z, pw, bh, T('기본 바퀴 수', 'Default laps'), d['laps'], lambda k: setv('laps', int(clamp(d['laps'] + k, 1, 10))))
            z -= bh + gap
            half = (pw - 0.01) / 2.0
            self.button(x, z - bh, x + half, z, T('자동 부스트 발판: ', 'Auto boost pads: ') + (T('켬', 'On') if d['pads'] else T('끔', 'Off')),
                        lambda: setv('pads', 0 if d['pads'] else 1), 'on' if d['pads'] else 'normal')

            def ask_clear():
                self.confirm = 'clear'
            self.button(x + half + 0.01, z - bh, x + pw, z, T('물건 모두 지우기', 'Clear objects'), ask_clear, 'danger', bool(d['objs']))
            z -= bh + gap

            def imp(k):
                self.import_mid = ((self.import_mid - 1 + k) % MAP_COUNT) + 1

            def do_import():
                src = cmap_from_builtin(self.import_mid)
                ed.snapshot()
                ed.data['pts'] = src['pts']
                ed.data['width'] = src['width']
                self.fit()
                self.say('기본 맵 #%d 의 코스 모양을 가져왔어요' % self.import_mid, 'Copied the course of map #%d' % self.import_mid)
            self.stepper(x, z, pw * 0.64, bh, T('코스 가져오기', 'Copy course'), '#%d' % self.import_mid, imp)
            self.button(x + pw * 0.66, z - bh, x + pw, z, T('가져오기', 'Copy'), do_import)
            z -= bh + gap
        bz = bottom + 0.005
        self.button(x, bz, x + 0.16, bz + bh, '<', lambda: setattr(self, 'set_page', 0), enabled=self.set_page > 0)
        self.text('%d / 2' % (self.set_page + 1), x + pw / 2.0, bz + 0.025, 0.04, (0.9, 0.92, 1, 1), 'c')
        self.button(x + pw - 0.16, bz, x + pw, bz + bh, '>', lambda: setattr(self, 'set_page', 1), enabled=self.set_page < 1)

    def ui_confirm(self):
        a = self.app.getAspectRatio()
        self.card(-a, -1, a, 1, (0, 0, 0, 0.6))
        self.buttons = []        # 확인 창 밖은 클릭 안 됨
        self.card(-0.7, -0.25, 0.7, 0.3, (0.05, 0.07, 0.15, 0.97))
        if self.confirm == 'exit':
            self.text(T('저장하지 않은 변경이 있어요', 'You have unsaved changes'), 0, 0.15, 0.06, (1, 1, 1, 1), 'c')

            def save_exit():
                if self.save():
                    self.leave()
            self.button(-0.66, -0.2, -0.24, -0.06, T('저장 후 나가기', 'Save & exit'), save_exit, 'good')
            self.button(-0.21, -0.2, 0.21, -0.06, T('그냥 나가기', 'Discard'), self.leave, 'danger')
            self.button(0.24, -0.2, 0.66, -0.06, T('취소', 'Cancel'), lambda: setattr(self, 'confirm', None), 'ghost')
        else:
            self.text(T('놓은 물건을 모두 지울까요?', 'Remove all placed objects?'), 0, 0.15, 0.06, (1, 1, 1, 1), 'c')

            def clear():
                self.ed.clear_objs()
                self.confirm = None
                self.need_cv = True
            self.button(-0.6, -0.2, -0.04, -0.06, T('모두 지우기', 'Clear all'), clear, 'danger')
            self.button(0.04, -0.2, 0.6, -0.06, T('취소', 'Cancel'), lambda: setattr(self, 'confirm', None), 'ghost')
