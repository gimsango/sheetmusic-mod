
# ============================================================================
#  [폰] 맵 만들기: 내 맵 목록 + 편집기
#   길 그리기 / 점 옮기기·추가·삭제 / 높낮이 / 출발점 / 장애물 / 나무·화산 기둥 / 발판·상자 / 세부 설정
# ============================================================================
ED_TABS = [('road', '길', 'Road'), ('obs', '장애물', 'Obstacles'), ('deco', '나무·장식', 'Nature'), ('pad', '발판·상자', 'Pads'),
           ('set', '설정', 'Settings')]
ED_ROAD_TOOLS = [('draw', '길 그리기', 'Draw road'), ('move', '점 옮기기', 'Move point'), ('add', '점 추가', 'Add point'),
                 ('del', '점 지우기', 'Delete point'), ('up', '높이기', 'Raise'), ('down', '낮추기', 'Lower'),
                 ('start', '출발점', 'Start line'), ('pan', '화면 이동', 'Pan view')]
ED_HINT = {
    'draw': ('손가락으로 코스 모양을 한 바퀴 그리세요 (끝은 처음과 자동으로 이어져요)', 'Draw one lap of the course (the end joins the start)'),
    'move': ('점을 끌어서 옮기세요 (빈 곳을 끌면 화면 이동)', 'Drag a point to move it (drag empty space to pan)'),
    'add': ('길 근처를 누르면 그 자리에 점이 생겨요', 'Tap near the road to add a point'),
    'del': ('지울 점을 누르세요', 'Tap a point to delete it'),
    'up': ('누른 점 부근의 길이 4m 높아져요', 'Tap a point to raise the road 4 m'),
    'down': ('누른 점 부근의 길이 4m 낮아져요', 'Tap a point to lower the road 4 m'),
    'start': ('출발선이 될 점을 누르세요', 'Tap the point for the start line'),
    'pan': ('끌어서 화면 이동 · 두 손가락으로 확대/축소', 'Drag to pan · pinch to zoom'),
    'erase': ('누르거나 문질러서 물건 지우기', 'Tap or rub to erase objects'),
    'place': ('누르면 놓기 · 끌면 화면 이동', 'Tap to place · drag to pan'),
    'line': ('끌어서 선을 따라 줄지어 놓기', 'Drag to place a row along your line'),
}


class PhoneMapMaker(object):
    def __init__(self, app):
        self.app = app
        self.ed = None
        self.uid = None
        self.tab = 'road'
        self.tool = 'draw'
        self.kinds = {'obs': 'cone', 'deco': 'pine', 'pad': 'pad'}
        self.erase = False
        self.line = False
        self.size = 1.0
        self.view = None
        self.canvas = None
        self.blocks = []
        self.g = None              # 진행 중인 손가락 동작
        self.stroke = None
        self.drag_pt = -1
        self.block_taps = False    # 이번 프레임의 탭은 끌기/두 손가락 동작의 끝이라 무시
        self.wheel = 0.0
        self.rdrag = None          # 마우스 오른쪽 끌기 (화면 이동)
        self.ver = 0
        self.cv_key = None
        self.cv_surf = None
        self.confirm = None
        self.page = 0
        self.set_page = 0
        self.deco_page = 0
        self.msg = ''
        self.msg_t = 0.0
        self.import_mid = 1
        self.info_cache = {}
        self.test_uid = None

    # ------------------------------------------------------------------ 공통
    def say(self, ko, en, secs=2.2):
        self.msg = T(ko, en)
        self.msg_t = time.time() + secs

    def open(self, data, uid):
        self.ed = MapEdit(data)
        self.uid = uid
        self.view = None
        self.g = None
        self.stroke = None
        self.drag_pt = -1
        self.confirm = None
        self.ver += 1
        if not uid:
            self.tab, self.tool = 'road', 'draw'
            self.say('먼저 [길 그리기]로 코스를 그려 보세요. 기본 타원 코스로 바로 달릴 수도 있어요',
                     'Draw your course with [Draw road] - or race the default oval right away', 5.0)
        self.app.go('editor')

    def changed(self):
        self.ver += 1

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
        self.info_cache.pop(uid, None)
        self.say('저장했어요', 'Saved')
        return True

    def map_info_of(self, d):
        key = d['uid'] + str(cmap_key(d))
        hit = self.info_cache.get(key)
        if hit is None:
            try:
                tr = Track(d, True)
                length = tr.length
            except Exception:
                length = 0.0
            nobs = sum(1 for o in d['objs'] if OBJ_INFO[o[0]]['cat'] == 'obs')
            ndeco = sum(1 for o in d['objs'] if OBJ_INFO[o[0]]['cat'] == 'deco')
            npad = len(d['objs']) - nobs - ndeco
            hit = self.info_cache[key] = (length, nobs, ndeco, npad)
            if len(self.info_cache) > 120:
                self.info_cache.clear()
        return hit

    # ------------------------------------------------------------------ 화면 좌표
    def fit(self):
        d = self.ed.data
        xs = [p[0] for p in d['pts']] + [o[1] for o in d['objs']]
        zs = [p[1] for p in d['pts']] + [o[2] for o in d['objs']]
        cv = self.canvas
        x0, x1, z0, z1 = min(xs) - 40, max(xs) + 40, min(zs) - 40, max(zs) + 40
        sc = min(cv.w / max(x1 - x0, 60.0), cv.h / max(z1 - z0, 60.0))
        self.view = [(x0 + x1) / 2.0, (z0 + z1) / 2.0, clamp(sc, 0.08, 12.0)]

    def to_screen(self, x, z):
        cx, cz, sc = self.view
        cv = self.canvas
        return (cv.centerx + (x - cx) * sc, cv.centery + (z - cz) * sc)

    def to_world(self, sx, sy):
        cx, cz, sc = self.view
        cv = self.canvas
        return (cx + (sx - cv.centerx) / sc, cz + (sy - cv.centery) / sc)

    def zoom(self, k, sx=None, sy=None):
        cv = self.canvas
        if sx is None:
            sx, sy = cv.centerx, cv.centery
        wx, wz = self.to_world(sx, sy)
        self.view[2] = clamp(self.view[2] * k, 0.08, 12.0)
        nx, nz = self.to_world(sx, sy)
        self.view[0] += wx - nx
        self.view[1] += wz - nz
        self.clamp_view()

    def pan(self, dx, dy):
        sc = self.view[2]
        self.view[0] -= dx / sc
        self.view[1] -= dy / sc
        self.clamp_view()

    def clamp_view(self):
        W = CMAP_WORLD + 200
        self.view[0] = clamp(self.view[0], -W, W)
        self.view[1] = clamp(self.view[1], -W, W)

    def hit_m(self):
        return 26.0 * self.app.ui.u / self.view[2]

    # ------------------------------------------------------------------ 목록 화면
    def scene_maps(self, dt):
        app = self.app
        ui = app.ui
        u = ui.u
        surf = app.screen
        app.draw_show(dt, app.profile['kart'], shift=0.0)
        store = app.store
        pw = min(app.W - 28 * u, 900 * u)
        r = R((app.W - pw) / 2, 14 * u, pw, app.H - 28 * u)
        ui.panel(surf, r, 222)
        x, y, w = r.x + 18 * u, r.y + 14 * u, r.w - 36 * u
        ui.text(surf, T('맵 만들기', 'Map maker'), x, y, 34 * u)
        ui.text(surf, T('내 맵 %d개' % len(store.maps), '%d maps' % len(store.maps)), r.right - 18 * u, y + 8 * u, 22 * u, (255, 220, 120), 'r')
        y += 52 * u
        bh = 52 * u
        third = (w - 2 * 10 * u) / 3.0
        if ui.button(surf, R(x, y, third, bh), T('+ 새 맵', '+ New map'), 'primary', size=22 * u):
            n = len(store.maps) + 1
            self.open(cmap_new(T('나의 맵 %d' % n, 'My map %d' % n), int(app.profile['map'])), None)
            return
        if ui.button(surf, R(x + third + 10 * u, y, third, bh), T('기본 맵 코스로 시작', 'Start from a map'), 'normal', size=19 * u):
            mid = int(self.import_mid)
            d = cmap_from_builtin(mid, map_info(mid)['name' if LANG == 'ko' else 'name_en'])
            self.open(d, None)
            return
        d_ = ui.stepper(surf, R(x + 2 * (third + 10 * u), y + 4 * u, third, bh - 8 * u), '', '#%d' % self.import_mid)
        if d_:
            self.import_mid = ((self.import_mid - 1 + d_) % MAP_COUNT) + 1
        y += bh + 14 * u
        rows_h = r.bottom - 76 * u - y
        per = max(1, int(rows_h // (74 * u)))
        npg = max(1, (len(store.maps) + per - 1) // per)
        self.page = int(clamp(self.page, 0, npg - 1))
        if not store.maps:
            ui.text(surf, T('아직 만든 맵이 없어요. [+ 새 맵]을 눌러 보세요!', 'No maps yet. Tap [+ New map]!'), x, y + 10 * u, 22 * u, (190, 205, 240))
        for i, d in enumerate(store.maps[self.page * per:(self.page + 1) * per]):
            row = R(x, y, w, 66 * u)
            ui.panel(surf, row, 120, (40, 54, 96), int(10 * u))
            length, nobs, ndeco, npad = self.map_info_of(d)
            ui.text(surf, d['name'], row.x + 12 * u, row.y + 6 * u, 26 * u)
            th = biome(d['look'])
            sub = T('%.2f km · 장애물 %d · 장식 %d · 발판/상자 %d · %s' % (length / 1000.0, nobs, ndeco, npad, th['name']),
                    '%.2f km · %d obstacles · %d deco · %d pads/boxes · %s' % (length / 1000.0, nobs, ndeco, npad, th['en']))
            ui.text(surf, sub, row.x + 12 * u, row.y + 38 * u, 16 * u, (190, 205, 240))
            bw = 92 * u
            bx = row.right - 3 * (bw + 8 * u)
            if ui.button(surf, R(bx, row.y + 10 * u, bw, 46 * u), T('편집', 'Edit'), 'normal', size=20 * u):
                self.open(d, d['uid'])
                return
            if ui.button(surf, R(bx + bw + 8 * u, row.y + 10 * u, bw, 46 * u), T('달리기', 'Race'), 'good', size=20 * u):
                app.profile['map_src'] = 'custom'
                app.profile['cmap'] = d['uid']
                app.profile.save()
                app.go('solo')
                return
            dk = 'danger' if self.confirm == ('del', d['uid']) else 'ghost'
            if ui.button(surf, R(bx + 2 * (bw + 8 * u), row.y + 10 * u, bw, 46 * u), T('정말?', 'Sure?') if dk == 'danger' else T('삭제', 'Delete'), dk, size=20 * u):
                if self.confirm == ('del', d['uid']):
                    store.delete(d['uid'])
                    self.confirm = None
                    if app.profile['cmap'] == d['uid']:
                        app.profile['cmap'] = ''
                        app.profile['map_src'] = 'builtin'
                else:
                    self.confirm = ('del', d['uid'])
            y += 74 * u
        if npg > 1:
            py_ = r.bottom - 124 * u
            if ui.button(surf, R(x, py_, 90 * u, 40 * u), '<', 'normal', enabled=self.page > 0):
                self.page -= 1
            ui.text(surf, '%d / %d' % (self.page + 1, npg), x + 130 * u, py_ + 6 * u, 22 * u, (230, 235, 255), 'c')
            if ui.button(surf, R(x + 170 * u, py_, 90 * u, 40 * u), '>', 'normal', enabled=self.page < npg - 1):
                self.page += 1
        ui.text(surf, T('파일: kart3d_maps.json (폰/PC 같은 형식)', 'File: kart3d_maps.json (same format on phone/PC)'), x + 220 * u, r.bottom - 40 * u, 15 * u, (150, 165, 200))
        if ui.button(surf, R(x, r.bottom - 46 * u - 8 * u, 200 * u, 46 * u), T('뒤로', 'Back'), 'ghost'):
            app.go('menu')

    # ------------------------------------------------------------------ 편집기
    def layout(self):
        app = self.app
        u = app.ui.u
        m = int(10 * u)
        if app.landscape:
            tw = int(min(max(app.W * 0.34, 330 * u), app.W * 0.46))
            canvas = R(m, m, app.W - tw - 3 * m, app.H - 2 * m)
            panel = R(canvas.right + m, m, tw, app.H - 2 * m)
        else:
            th = int(min(max(app.H * 0.42, 380 * u), app.H * 0.55))
            canvas = R(m, m, app.W - 2 * m, app.H - th - 3 * m)
            panel = R(m, canvas.bottom + m, app.W - 2 * m, th)
        return canvas, panel

    def scene_editor(self, dt):
        app = self.app
        ui = app.ui
        u = ui.u
        surf = app.screen
        ed = self.ed
        if ed is None:
            app.go('maps')
            return
        canvas, panel = self.layout()
        if self.canvas is None or self.canvas.size != canvas.size or self.canvas.topleft != canvas.topleft:
            self.canvas = canvas
            self.cv_key = None
            if self.view is None:
                self.fit()
        if self.view is None:
            self.fit()
        surf.fill((10, 14, 28))
        self.blocks = []
        # --- 화면 확대/축소 버튼 (캔버스 오른쪽 위)
        zb = int(46 * u)
        zr = [R(canvas.right - zb - 8 * u, canvas.y + 8 * u + i * (zb + 6 * u), zb, zb) for i in range(3)]
        self.blocks = list(zr)
        # --- 손가락 동작 처리 (그리기/옮기기/화면 이동/확대)
        self.handle_gestures()
        self.draw_canvas(surf)
        for i, (lab, fn) in enumerate((('+', lambda: self.zoom(1.4)), ('-', lambda: self.zoom(1 / 1.4)), (T('전체', 'Fit'), self.fit))):
            if ui.button(surf, zr[i], lab, 'ghost', size=zb * (0.5 if i < 2 else 0.32)):
                fn()
        # 위쪽 정보줄
        d = ed.data
        tr = ed.preview()
        info = d['name'] + ('  *' if ed.dirty else '')
        ui.text(surf, info, canvas.x + 12 * u, canvas.y + 8 * u, 26 * u, (255, 255, 255))
        if tr is not None:
            ui.text(surf, T('%.2f km · 폭 %dm · 조절점 %d · 물건 %d' % (tr.length / 1000.0, d['width'], len(d['pts']), len(d['objs'])),
                            '%.2f km · width %dm · %d points · %d objects' % (tr.length / 1000.0, d['width'], len(d['pts']), len(d['objs']))),
                    canvas.x + 12 * u, canvas.y + 40 * u, 17 * u, (200, 215, 245))
        warns = ed.warnings(LANG) if self.g is None else []
        wy = canvas.y + 64 * u
        for wtxt in warns[:2]:
            ui.text(surf, '! ' + wtxt, canvas.x + 12 * u, wy, 17 * u, (255, 150, 110))
            wy += 22 * u
        hint = self.current_hint()
        if self.msg and time.time() < self.msg_t:
            hint = self.msg
        if hint:
            ui.text(surf, hint, canvas.x + 12 * u, canvas.bottom - 30 * u, 17 * u, (255, 230, 150))
        self.draw_panel(surf, panel)
        self.handle_taps()
        if self.confirm is not None and self.confirm[0] in ('exit', 'clear'):
            self.draw_confirm(surf)

    def current_hint(self):
        if self.tab == 'set':
            return ''
        if self.tab == 'road':
            k = self.tool
        elif self.erase:
            k = 'erase'
        else:
            k = 'line' if self.line else 'place'
        h = ED_HINT.get(k)
        return T(h[0], h[1]) if h else ''

    # ---- 캔버스 그리기 ---------------------------------------------------------------
    def draw_canvas(self, surf):
        cv = self.canvas
        key = (self.ver, tuple(round(v, 4) for v in self.view), cv.size)
        if key != self.cv_key or self.cv_surf is None:
            self.cv_key = key
            self.cv_surf = self.render_canvas()
        surf.blit(self.cv_surf, cv.topleft)
        # 진행 중인 선 / 옮기는 점
        u = self.app.ui.u
        if self.stroke and len(self.stroke) > 1:
            pts = [self.to_screen(x, z) for x, z in self.stroke]
            col = (255, 230, 90) if self.tab == 'road' else OBJ_INFO[self.kinds.get(self.tab, 'cone')]['col']
            pygame.draw.lines(surf, (0, 0, 0), False, pts, max(3, int(7 * u)))
            pygame.draw.lines(surf, col, False, pts, max(2, int(4 * u)))
        if self.drag_pt >= 0:
            pts = [self.to_screen(p[0], p[1]) for p in self.ed.data['pts']]
            pygame.draw.lines(surf, (255, 230, 90), True, pts, max(1, int(2 * u)))
            p = pts[self.drag_pt]
            pygame.draw.circle(surf, (255, 230, 90), (int(p[0]), int(p[1])), int(12 * u), max(2, int(3 * u)))
        pygame.draw.rect(surf, (90, 110, 170), cv, max(1, int(2 * u)))

    def render_canvas(self):
        cv = self.canvas
        u = self.app.ui.u
        s = pygame.Surface(cv.size)
        d = self.ed.data
        th = biome(d['look'])
        g0 = hex_rgb(th['ground'][0])
        bgc = shade_rgb(g0, 0.42)
        s.fill(bgc)
        ox, oy = cv.x, cv.y
        sc = self.view[2]

        def P(x, z):
            sx, sy = self.to_screen(x, z)
            return (sx - ox, sy - oy)
        # 격자 (50m / 확대가 작으면 200m)
        step = 50.0 if sc > 0.5 else 200.0
        gc = shade_rgb(g0, 0.52)
        x0w, z0w = self.to_world(cv.x, cv.y)
        x1w, z1w = self.to_world(cv.right, cv.bottom)
        gx = math.floor(x0w / step) * step
        while gx <= x1w:
            a = P(gx, 0)[0]
            pygame.draw.line(s, gc, (a, 0), (a, cv.h))
            gx += step
        gz = math.floor(z0w / step) * step
        while gz <= z1w:
            b = P(0, gz)[1]
            pygame.draw.line(s, gc, (0, b), (cv.w, b))
            gz += step
        W = CMAP_WORLD
        pygame.draw.rect(s, (200, 80, 80), pygame.Rect(P(-W, -W), (2 * W * sc, 2 * W * sc)), max(1, int(2 * u)))
        tr = self.ed.preview()
        if tr is not None:
            N = tr.N
            stp = 1 if sc > 1.2 else 2
            idxs = list(range(0, N, stp)) + [0]
            sh = tr.hw + tr.SH
            road = shade_rgb(hex_rgb(th['road']), 1.5)
            grass = shade_rgb(g0, 0.8)
            wallc = hex_rgb(th['wall'][0])

            def edge(i, off):
                return P(tr.px[i] + tr.rx[i] * off, tr.pz[i] + tr.rz[i] * off)
            L1 = [edge(i, -sh) for i in idxs]
            R1 = [edge(i, sh) for i in idxs]
            L0 = [edge(i, -tr.hw) for i in idxs]
            R0 = [edge(i, tr.hw) for i in idxs]
            for k in range(len(idxs) - 1):
                pygame.draw.polygon(s, grass, (L1[k], L1[k + 1], R1[k + 1], R1[k]))
            for k in range(len(idxs) - 1):
                pygame.draw.polygon(s, road, (L0[k], L0[k + 1], R0[k + 1], R0[k]))
            lw = max(1, int(2 * u))
            pygame.draw.lines(s, wallc, False, L1, lw)
            pygame.draw.lines(s, wallc, False, R1, lw)
            # 높이 표시: 색이 밝을수록 높음 (가운데 선)
            if tr.max_y - tr.min_y > 1.0:
                cl = [P(tr.px[i], tr.pz[i]) for i in idxs]
                for k in range(len(idxs) - 1):
                    f = (tr.py[idxs[k]] - tr.min_y) / (tr.max_y - tr.min_y)
                    pygame.draw.line(s, mix_rgb((70, 90, 160), (255, 240, 160), f), cl[k], cl[k + 1], max(1, int(2 * u)))
            # 출발선 (체크무늬) + 방향 화살표
            a, b = edge(0, -tr.hw), edge(0, tr.hw)
            for k in range(8):
                p0 = (a[0] + (b[0] - a[0]) * k / 8.0, a[1] + (b[1] - a[1]) * k / 8.0)
                p1 = (a[0] + (b[0] - a[0]) * (k + 1) / 8.0, a[1] + (b[1] - a[1]) * (k + 1) / 8.0)
                pygame.draw.line(s, (255, 255, 255) if k % 2 == 0 else (20, 20, 20), p0, p1, max(3, int(5 * u)))
            j = min(N - 1, int(18 / tr.ds) + 1)
            c0 = P(tr.px[0], tr.pz[0])
            c1 = P(tr.px[j], tr.pz[j])
            ang = math.atan2(c1[1] - c0[1], c1[0] - c0[0])
            L = max(16 * u, min(60 * u, tr.width * sc * 1.2))
            tip = (c0[0] + math.cos(ang) * L, c0[1] + math.sin(ang) * L)
            pygame.draw.line(s, (255, 220, 60), c0, tip, max(2, int(4 * u)))
            for da in (2.6, -2.6):
                pygame.draw.line(s, (255, 220, 60), tip, (tip[0] + math.cos(ang + da) * 12 * u, tip[1] + math.sin(ang + da) * 12 * u), max(2, int(4 * u)))
        # 물건
        for o in d['objs']:
            info = OBJ_INFO[o[0]]
            p = P(o[1], o[2])
            if p[0] < -60 or p[1] < -60 or p[0] > cv.w + 60 or p[1] > cv.h + 60:
                continue
            col = info['col']
            cat = info['cat']
            if cat == 'road':
                hl = (4.5 if o[0] == 'pad' else 3.3) * o[3] * sc
                hwp = 2.8 * o[3] * sc
                if o[0] == 'box':
                    hl, hwp = 1.2 * sc, (tr.hw if tr is not None else 8.0) * sc
                hl, hwp = max(hl, 4 * u), max(hwp, 3 * u)
                ca, sa = math.cos(o[4]), math.sin(o[4])
                # rot = 길 방향(atan2(tx, tz)) -> 화면 (x 오른쪽, z 아래)
                fx_, fz_ = sa, ca
                rx_, rz_ = -fz_, fx_
                pts = [(p[0] + fx_ * a_ * hl + rx_ * b_ * hwp, p[1] + fz_ * a_ * hl + rz_ * b_ * hwp) for (a_, b_) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                pygame.draw.polygon(s, col, pts)
                pygame.draw.polygon(s, (0, 0, 0), pts, 1)
                if o[0] == 'box':
                    for k in range(4):
                        t_ = -0.66 + 0.44 * k
                        q_ = (p[0] + rx_ * t_ * hwp, p[1] + rz_ * t_ * hwp)
                        pygame.draw.rect(s, (255, 255, 255), (int(q_[0] - 3 * u), int(q_[1] - 3 * u), int(6 * u) + 1, int(6 * u) + 1))
                continue
            rad = info['rad'] * o[3]
            if o[0] == 'building':
                rad = (14 + clamp((o[3] - 0.3) / 2.7, 0.0, 1.0) * 22) * 0.45
            pr = max(4 * u, rad * sc) if cat == 'obs' else max(4.5 * u, min(rad * sc * 2.2, 40 * u))
            if o[0] == 'volcano' or o[0] == 'building':
                pr = max(5 * u, rad * sc)
            ip = (int(p[0]), int(p[1]))
            if cat == 'obs':
                if o[0] in ('block', 'crate', 'tires'):
                    ca, sa = math.cos(o[4]), math.sin(o[4])
                    hl = pr * (1.8 if o[0] == 'block' else 1.0)
                    pts = [(p[0] + sa * a_ * hl + (-ca) * b_ * pr * 0.7, p[1] + ca * a_ * hl + sa * b_ * pr * 0.7)
                           for (a_, b_) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                    pygame.draw.polygon(s, col, pts)
                    pygame.draw.polygon(s, (0, 0, 0), pts, 1)
                else:
                    pygame.draw.circle(s, (0, 0, 0), ip, int(pr) + 1)
                    pygame.draw.circle(s, col, ip, int(pr))
                    if o[0] == 'lavapillar':
                        pygame.draw.circle(s, (255, 220, 120), ip, max(1, int(pr * 0.45)))
            else:
                pygame.draw.circle(s, shade_rgb(col, 0.55), (ip[0] + 1, ip[1] + 1), int(pr))
                pygame.draw.circle(s, col, ip, int(pr))
                if o[0] == 'volcano':
                    pygame.draw.circle(s, (255, 120, 30), ip, max(2, int(pr * 0.3)))
        # 조절점
        pts = d['pts']
        big = self.tab == 'road' and self.tool not in ('draw', 'pan')
        pr = int((7 if big else 4) * u)
        for i, p in enumerate(pts):
            q_ = P(p[0], p[1])
            ip = (int(q_[0]), int(q_[1]))
            c = (255, 255, 255)
            if p[2] > 0.5:
                c = (255, 200, 90)
            elif p[2] < -0.5:
                c = (120, 170, 255)
            if i == 0:
                pygame.draw.circle(s, (0, 0, 0), ip, pr + int(4 * u))
                pygame.draw.circle(s, (80, 255, 120), ip, pr + int(3 * u))
            pygame.draw.circle(s, (0, 0, 0), ip, pr + 1)
            pygame.draw.circle(s, c, ip, pr)
            if big and abs(p[2]) > 0.5:
                self.app.ui.text(s, '%+d' % int(round(p[2])), ip[0] + pr + 2, ip[1] - pr - 14 * u, 14 * u, c)
        return s

    # ---- 손가락/마우스 동작 --------------------------------------------------------------
    def pointers(self):
        ptr = self.app.ptr
        if ptr.fingers:
            return list(ptr.fingers.items())
        if ptr.mouse is not None:
            return [('m', ptr.mouse)]
        return []

    def handle_gestures(self):
        cv = self.canvas
        if self.app.kb is not None or self.confirm is not None:
            self.g = None
            return
        if self.wheel:
            mp = pygame.mouse.get_pos()
            if cv.collidepoint(mp):
                self.zoom(1.18 ** self.wheel, mp[0], mp[1])
            self.wheel = 0.0
        self.block_taps = False
        pts = self.pointers()
        ids = dict(pts)
        g = self.g
        if g is None:
            inside = [(i, p) for i, p in pts if cv.collidepoint(p) and not any(b.collidepoint(p) for b in self.blocks)]
            if len(pts) == 1 and len(inside) == 1:
                i, p = inside[0]
                self.g = {'mode': 'one', 'id': i, 'start': p, 'last': p, 'moved': False}
                self.begin(p)
            elif len(inside) >= 2:
                self.g = self.two_start(inside[:2])
            return
        if g['mode'] == 'one':
            if len(pts) >= 2:
                self.cancel()
                inside = [(i, p) for i, p in pts if cv.collidepoint(p)]
                self.g = self.two_start(inside[:2]) if len(inside) >= 2 else {'mode': 'wait'}
                return
            p = ids.get(g['id'])
            if p is None:
                self.end(g['last'], g['moved'])
                if g['moved']:
                    self.block_taps = True
                self.g = None
                return
            if not g['moved'] and math.hypot(p[0] - g['start'][0], p[1] - g['start'][1]) > 10 * self.app.ui.u:
                g['moved'] = True
            if p != g['last']:
                self.drag(g['last'], p, g['moved'])
                g['last'] = p
        elif g['mode'] == 'two':
            a, b = ids.get(g['a']), ids.get(g['b'])
            if a is None or b is None:
                self.g = {'mode': 'wait'}
                self.block_taps = True
                return
            c = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            dist = max(10.0, math.hypot(a[0] - b[0], a[1] - b[1]))
            self.pan(c[0] - g['c'][0], c[1] - g['c'][1])
            self.zoom(dist / g['d'], c[0], c[1])
            g['c'], g['d'] = c, dist
        else:      # 'wait': 손가락을 모두 뗄 때까지 아무것도 안 함
            self.block_taps = True
            if not pts:
                self.g = None

    def two_start(self, two):
        (ia, a), (ib, b) = two
        return {'mode': 'two', 'a': ia, 'b': ib, 'c': ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0), 'd': max(10.0, math.hypot(a[0] - b[0], a[1] - b[1]))}

    def mode_of(self):
        """현재 도구의 손가락 동작 종류: 'stroke' (선 그리기) / 'point' (점 끌기) / 'erase' / 'pan' / 'tap'"""
        if self.tab == 'road':
            return {'draw': 'stroke', 'move': 'point', 'pan': 'pan'}.get(self.tool, 'tap')
        if self.tab == 'set':
            return 'pan'
        if self.erase:
            return 'erase'
        return 'stroke' if self.line else 'tap'

    def begin(self, p):
        m = self.mode_of()
        wx, wz = self.to_world(*p)
        self.stroke = None
        self.drag_pt = -1
        if m == 'stroke':
            self.stroke = [(wx, wz)]
        elif m == 'point':
            i = self.ed.nearest_point(wx, wz, self.hit_m())
            if i >= 0:
                self.ed.snapshot()
                self.drag_pt = i
        elif m == 'erase':
            if self.ed.erase_at(wx, wz, self.hit_m() * 0.7):
                self.changed()

    def drag(self, a, b, moved):
        m = self.mode_of()
        wx, wz = self.to_world(*b)
        if m == 'stroke' and self.stroke is not None:
            lx, lz = self.stroke[-1]
            if math.hypot(wx - lx, wz - lz) * self.view[2] > 3:
                self.stroke.append((wx, wz))
        elif m == 'point' and self.drag_pt >= 0:
            self.ed.move_point(self.drag_pt, wx, wz, snap=False)
        elif m == 'erase':
            ed = self.ed
            objs = ed.data['objs']
            rad = self.hit_m() * 0.7
            keep = [o for o in objs if (o[1] - wx) ** 2 + (o[2] - wz) ** 2 >= (rad + OBJ_INFO[o[0]]['rad'] * o[3] * 0.5) ** 2]
            if len(keep) != len(objs):
                ed.data['objs'] = keep
                ed.dirty = True
                self.changed()
        elif moved:
            self.pan(b[0] - a[0], b[1] - a[1])

    def end(self, p, moved):
        m = self.mode_of()
        ed = self.ed
        if m == 'stroke' and self.stroke is not None:
            st = self.stroke
            self.stroke = None
            if self.tab == 'road':
                if len(st) > 4:
                    if ed.set_stroke(st):
                        self.changed()
                        self.say('길을 만들었어요! 점을 옮겨서 다듬을 수 있어요', 'Road created! Move points to fine-tune it')
                    else:
                        self.say('너무 짧아요. 화면을 크게 써서 한 바퀴 그려 주세요', 'Too short - draw a bigger loop')
            else:
                kind = self.kinds[self.tab]
                if len(st) < 2 or not moved:
                    if ed.add_obj(kind, st[-1][0], st[-1][1], OBJ_INFO[kind]['s'] * self.size):
                        self.changed()
                else:
                    n = ed.add_line(kind, st, OBJ_INFO[kind]['s'] * self.size)
                    if n:
                        self.changed()
                        self.say('%d개 놓았어요' % n, 'Placed %d' % n, 1.4)
                if ed.msg == 'full':
                    self.say('물건이 너무 많아요 (최대 %d개)' % CMAP_MAX_OBJS, 'Too many objects (max %d)' % CMAP_MAX_OBJS)
                    ed.msg = ''
        elif m == 'point' and self.drag_pt >= 0:
            self.drag_pt = -1
            self.changed()

    def cancel(self):
        self.stroke = None
        if self.drag_pt >= 0:
            self.drag_pt = -1
            self.changed()

    def handle_taps(self):
        """캔버스를 짧게 누른 경우 (점 추가/삭제/높이/출발점/물건 하나 놓기)"""
        ui = self.app.ui
        cv = self.canvas
        taps = [t for t in ui.taps if cv.collidepoint(t) and not any(b.collidepoint(t) for b in self.blocks)]
        for t in taps:
            ui.taps.remove(t)
        if not taps or self.block_taps or self.confirm is not None:
            return
        m = self.mode_of()
        ed = self.ed
        for t in taps:
            wx, wz = self.to_world(*t)
            if self.tab == 'road':
                tool = self.tool
                if tool == 'add':
                    if ed.insert_point(wx, wz) >= 0:
                        self.changed()
                    continue
                i = ed.nearest_point(wx, wz, self.hit_m())
                if i < 0:
                    if tool in ('del', 'up', 'down', 'start'):
                        self.say('점(동그라미)을 눌러 주세요', 'Tap on a point (circle)', 1.4)
                    continue
                if tool == 'del':
                    if ed.delete_point(i):
                        self.changed()
                    else:
                        self.say('점이 4개보다 적을 수는 없어요', 'Need at least 4 points')
                elif tool in ('up', 'down'):
                    ed.raise_point(i, 4.0 if tool == 'up' else -4.0)
                    self.changed()
                elif tool == 'start':
                    ed.set_start(i)
                    self.changed()
                    self.say('출발선을 옮겼어요', 'Start line moved', 1.4)
            elif m == 'tap' and self.tab in ('obs', 'deco', 'pad'):
                kind = self.kinds[self.tab]
                if ed.add_obj(kind, wx, wz, OBJ_INFO[kind]['s'] * self.size):
                    self.changed()
                elif ed.msg == 'full':
                    self.say('물건이 너무 많아요 (최대 %d개)' % CMAP_MAX_OBJS, 'Too many objects (max %d)' % CMAP_MAX_OBJS)
                    ed.msg = ''
            elif m == 'erase':
                if ed.erase_at(wx, wz, self.hit_m() * 0.7):
                    self.changed()

    # ---- 오른쪽(아래) 도구판 -----------------------------------------------------------------
    def draw_panel(self, surf, r):
        app = self.app
        ui = app.ui
        u = ui.u
        ui.panel(surf, r, 225)
        pad = int(10 * u)
        x, y, w = r.x + pad, r.y + pad, r.w - 2 * pad
        # 탭
        th_ = int(min(44 * u, r.h * 0.1))
        tw = (w - 4 * 4 * u) / 5.0
        for i, (key, ko, en) in enumerate(ED_TABS):
            if ui.button(surf, R(x + i * (tw + 4 * u), y, tw, th_), T(ko, en), 'chipon' if self.tab == key else 'chip', size=th_ * 0.4):
                self.tab = key
                self.erase = False
                self.changed()
        y += th_ + 8 * u
        # 아래쪽 공통 버튼
        bh = int(min(50 * u, r.h * 0.11))
        by = r.bottom - pad - bh
        q = (w - 3 * 6 * u) / 4.0
        if ui.button(surf, R(x, by, q, bh), T('되돌리기', 'Undo'), 'normal', size=bh * 0.36, enabled=bool(self.ed.undo_stack)):
            if self.ed.undo():
                self.changed()
        if ui.button(surf, R(x + q + 6 * u, by, q, bh), T('저장', 'Save'), 'good', size=bh * 0.4):
            self.save()
        if ui.button(surf, R(x + 2 * (q + 6 * u), by, q, bh), T('시험 주행', 'Test drive'), 'primary', size=bh * 0.36):
            self.test_drive()
            return
        if ui.button(surf, R(x + 3 * (q + 6 * u), by, q, bh), T('나가기', 'Exit'), 'ghost', size=bh * 0.38):
            self.try_exit()
        area = R(x, y, w, by - 8 * u - y)
        if self.tab == 'road':
            self.panel_road(surf, area)
        elif self.tab in ('obs', 'deco', 'pad'):
            self.panel_objs(surf, area)
        else:
            self.panel_settings(surf, area)

    def grid(self, area, n, cols, rows_max=None, gap=None):
        u = self.app.ui.u
        gap = 6 * u if gap is None else gap
        rows = (n + cols - 1) // cols
        if rows_max:
            rows = min(rows, rows_max)
        bw = (area.w - (cols - 1) * gap) / float(cols)
        bh = min(52 * u, (area.h - (rows - 1) * gap) / float(max(1, rows)))
        return [R(area.x + (i % cols) * (bw + gap), area.y + (i // cols) * (bh + gap), bw, bh) for i in range(n)], bh

    def panel_road(self, surf, area):
        ui = self.app.ui
        u = ui.u
        top = R(area.x, area.y, area.w, area.h * 0.62)
        rects, bh = self.grid(top, len(ED_ROAD_TOOLS), 2)
        for (key, ko, en), rr in zip(ED_ROAD_TOOLS, rects):
            if ui.button(surf, rr, T(ko, en), 'chipon' if self.tool == key else 'chip', size=bh * 0.38):
                self.tool = key
                self.changed()
        y = rects[-1].bottom + 10 * u
        half = (area.w - 8 * u) / 2.0
        h2 = min(46 * u, (area.bottom - y - 8 * u) / 2.0)
        if h2 < 24 * u:
            return
        if ui.button(surf, R(area.x, y, half, h2), T('방향 반대로', 'Reverse direction'), 'normal', size=h2 * 0.38):
            self.ed.reverse()
            self.changed()
            self.say('달리는 방향을 바꿨어요', 'Direction reversed', 1.4)
        if ui.button(surf, R(area.x + half + 8 * u, y, half, h2), T('전체 옮기기 ↻', 'Recenter'), 'normal', size=h2 * 0.38):
            d = self.ed.data
            xs = [p[0] for p in d['pts']]
            zs = [p[1] for p in d['pts']]
            self.ed.move_all(-(min(xs) + max(xs)) / 2.0, -(min(zs) + max(zs)) / 2.0)
            self.changed()
            self.fit()
        y += h2 + 8 * u
        if ui.button(surf, R(area.x, y, area.w, h2), T('도로 폭 %dm  (설정 탭에서 더 많은 조절)' % self.ed.data['width'], 'Road width %dm (more in Settings)' % self.ed.data['width']),
                     'ghost', size=h2 * 0.34):
            self.tab = 'set'

    def panel_objs(self, surf, area):
        ui = self.app.ui
        u = ui.u
        cat = self.tab
        kinds = OBJ_BY_CAT['obs' if cat == 'obs' else ('deco' if cat == 'deco' else 'road')]
        cols = 3 if cat != 'pad' else 2
        # 아래: [한 개|줄] [크기 -/+] [지우개]
        ctrl_h = min(44 * u, area.h * 0.13)
        cy = area.bottom - ctrl_h * 2 - 6 * u
        grid_area = R(area.x, area.y, area.w, cy - 8 * u - area.y)
        per_page = len(kinds)
        maxrows = max(1, int((grid_area.h + 6 * u) // (40 * u + 6 * u)))
        if (len(kinds) + cols - 1) // cols > maxrows:
            per_page = maxrows * cols - 2
        npg = max(1, (len(kinds) + per_page - 1) // per_page)
        self.deco_page = int(clamp(self.deco_page, 0, npg - 1))
        shown = kinds[self.deco_page * per_page:(self.deco_page + 1) * per_page]
        n_btn = len(shown) + (2 if npg > 1 else 0)
        rects, bh = self.grid(grid_area, n_btn, cols)
        cur = self.kinds[cat]
        for k, rr in zip(shown, rects):
            on = (k == cur and not self.erase)
            if ui.button(surf, rr, obj_name(k, LANG), 'chipon' if on else 'chip', size=bh * 0.34):
                self.kinds[cat] = k
                self.erase = False
            sw_ = max(6, int(bh * 0.22))
            pygame.draw.rect(surf, OBJ_INFO[k]['col'], (rr.x + 5, rr.y + 5, sw_, sw_))
        if npg > 1:
            if ui.button(surf, rects[-2], '<', 'normal', size=bh * 0.4, enabled=self.deco_page > 0):
                self.deco_page -= 1
            if ui.button(surf, rects[-1], '>  %d/%d' % (self.deco_page + 1, npg), 'normal', size=bh * 0.36, enabled=self.deco_page < npg - 1):
                self.deco_page += 1
        third = (area.w - 12 * u) / 3.0
        if ui.button(surf, R(area.x, cy, third, ctrl_h), T('한 개씩', 'Single'), 'chipon' if not self.line and not self.erase else 'chip', size=ctrl_h * 0.36):
            self.line = False
            self.erase = False
        if ui.button(surf, R(area.x + third + 6 * u, cy, third, ctrl_h), T('줄로 놓기', 'Draw a row'), 'chipon' if self.line and not self.erase else 'chip', size=ctrl_h * 0.36):
            self.line = True
            self.erase = False
        if ui.button(surf, R(area.x + 2 * (third + 6 * u), cy, third, ctrl_h), T('지우개', 'Eraser'), 'danger' if self.erase else 'chip', size=ctrl_h * 0.36):
            self.erase = not self.erase
        y2 = cy + ctrl_h + 6 * u
        d_ = self.stepper(surf, R(area.x, y2, area.w, ctrl_h), T('크기', 'Size'), '%d%%' % int(round(self.size * 100)))
        if d_:
            self.size = round(clamp(self.size + d_ * 0.1, 0.4, 3.0), 2)

    def panel_settings(self, surf, area):
        app = self.app
        ui = app.ui
        u = ui.u
        ed = self.ed
        d = ed.data
        npg = 2
        rh = min(44 * u, (area.h - 50 * u) / 6.0)
        y = area.y
        if self.set_page == 0:
            if ui.button(surf, R(area.x, y, area.w, rh), T('이름: ', 'Name: ') + d['name'], 'normal', size=rh * 0.4):
                def setname(t):
                    t = t.strip()
                    if t:
                        ed.set('name', t)
                        self.changed()
                app.open_kb(T('맵 이름', 'Map name'), d['name'], 'text', 20, setname)
            y += rh + 6 * u
            fam, ti, mi = biome_parts(d['look'])
            fname, tname, mname = biome_part_names(d['look'], LANG)
            for label, val, fn in ((T('바이옴', 'Biome'), fname, lambda k: biome_map(fam + k, ti, mi)),
                                   (T('시간대', 'Time'), tname, lambda k: biome_map(fam, ti + k, mi)),
                                   (T('색감', 'Mood'), mname, lambda k: biome_map(fam, ti, mi + k))):
                k = self.stepper(surf, R(area.x, y, area.w, rh), label, val)
                if k:
                    ed.set('look', fn(k))
                    self.changed()
                y += rh + 6 * u
            wl = CMAP_WEATHERS
            k = self.stepper(surf, R(area.x, y, area.w, rh), T('날씨', 'Weather'), (CMAP_WEATHER_KO if LANG == 'ko' else CMAP_WEATHER_EN)[d['weather']])
            if k:
                ed.set('weather', wl[(wl.index(d['weather']) + k) % len(wl)])
                self.changed()
            y += rh + 6 * u
            k = self.stepper(surf, R(area.x, y, area.w, rh), T('자동 장식', 'Auto scenery'), (CMAP_DECO_KO if LANG == 'ko' else CMAP_DECO_EN)[d['deco']])
            if k and 0 <= d['deco'] + k <= 3:
                ed.set('deco', d['deco'] + k)
                self.changed()
        else:
            k = self.stepper(surf, R(area.x, y, area.w, rh), T('도로 폭', 'Road width'), '%dm' % d['width'])
            if k:
                ed.set('width', clamp(d['width'] + k * 2, 10, 30))
                self.changed()
            y += rh + 6 * u
            k = self.stepper(surf, R(area.x, y, area.w, rh), T('언덕', 'Hills'), '%d%%' % int(round(d['hills'] * 100)))
            if k:
                ed.set('hills', round(clamp(d['hills'] + k * 0.1, 0.0, 1.0), 2))
                self.changed()
            y += rh + 6 * u
            k = self.stepper(surf, R(area.x, y, area.w, rh), T('기본 바퀴 수', 'Default laps'), d['laps'])
            if k and 1 <= d['laps'] + k <= 10:
                ed.set('laps', d['laps'] + k)
            y += rh + 6 * u
            half = (area.w - 8 * u) / 2.0
            if ui.button(surf, R(area.x, y, half, rh), T('자동 부스트 발판: ', 'Auto boost pads: ') + (T('켬', 'On') if d['pads'] else T('끔', 'Off')),
                         'chipon' if d['pads'] else 'chip', size=rh * 0.34):
                ed.set('pads', 0 if d['pads'] else 1)
                self.changed()
            if ui.button(surf, R(area.x + half + 8 * u, y, half, rh), T('물건 모두 지우기', 'Clear objects'), 'danger', size=rh * 0.34, enabled=bool(d['objs'])):
                self.confirm = ('clear', None)
            y += rh + 6 * u
            k = self.stepper(surf, R(area.x, y, area.w * 0.62, rh), T('코스 가져오기', 'Copy course'), '#%d' % self.import_mid)
            if k:
                self.import_mid = ((self.import_mid - 1 + k) % MAP_COUNT) + 1
            if ui.button(surf, R(area.x + area.w * 0.64, y, area.w * 0.36, rh), T('가져오기', 'Copy'), 'normal', size=rh * 0.36):
                src = cmap_from_builtin(self.import_mid)
                ed.snapshot()
                ed.data['pts'] = src['pts']
                ed.data['width'] = src['width']
                self.changed()
                self.fit()
                self.say('기본 맵 #%d 의 코스 모양을 가져왔어요' % self.import_mid, 'Copied the course of map #%d' % self.import_mid)
        py_ = area.bottom - 40 * u
        if ui.button(surf, R(area.x, py_, 90 * u, 40 * u), '<', 'normal', enabled=self.set_page > 0):
            self.set_page -= 1
        ui.text(surf, '%d / %d' % (self.set_page + 1, npg), area.x + area.w / 2, py_ + 8 * u, 20 * u, (230, 235, 255), 'c')
        if ui.button(surf, R(area.right - 90 * u, py_, 90 * u, 40 * u), '>', 'normal', enabled=self.set_page < npg - 1):
            self.set_page += 1

    def stepper(self, surf, rect, label, value):
        """[라벨   < 값 >] - 값 글자가 길면 칸에 맞게 줄인다. 반환 -1/0/+1"""
        ui = self.app.ui
        u = ui.u
        lw = rect.w * 0.36
        ui.text(surf, label, rect.x, rect.centery - 11 * u, min(22 * u, rect.h * 0.48), (210, 220, 245))
        bw = rect.h * 1.05
        res = 0
        lb = R(rect.x + lw, rect.y, bw, rect.h)
        rb = R(rect.right - bw, rect.y, bw, rect.h)
        if ui.button(surf, lb, '<', 'normal', size=rect.h * 0.5):
            res = -1
        if ui.button(surf, rb, '>', 'normal', size=rect.h * 0.5):
            res = 1
        room = rb.x - lb.right - 8 * u
        size = min(24 * u, rect.h * 0.52)
        tw = ui.render(str(value), size, (255, 220, 120)).get_width()
        if tw > room:
            size = size * room / float(tw)
        ui.text(surf, str(value), (lb.right + rb.x) // 2, rect.centery - size * 0.55, size, (255, 220, 120), 'c')
        return res

    # ---- 확인 창 / 나가기 / 시험 주행 -------------------------------------------------------
    def draw_confirm(self, surf):
        app = self.app
        ui = app.ui
        u = ui.u
        veil = pygame.Surface((app.W, app.H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 160))
        surf.blit(veil, (0, 0))
        pw, ph = int(min(app.W * 0.86, 520 * u)), int(250 * u)
        r = R((app.W - pw) // 2, (app.H - ph) // 2, pw, ph)
        ui.panel(surf, r, 240)
        kind = self.confirm[0]
        bh = 54 * u
        if kind == 'exit':
            ui.text(surf, T('저장하지 않은 변경이 있어요', 'You have unsaved changes'), r.centerx, r.y + 22 * u, 26 * u, (255, 255, 255), 'c')
            third = (r.w - 4 * 14 * u) / 3.0
            if ui.button(surf, R(r.x + 14 * u, r.bottom - bh - 18 * u, third, bh), T('저장 후 나가기', 'Save & exit'), 'good', size=18 * u):
                if self.save():
                    self.confirm = None
                    self.leave()
            if ui.button(surf, R(r.x + 28 * u + third, r.bottom - bh - 18 * u, third, bh), T('그냥 나가기', 'Discard'), 'danger', size=18 * u):
                self.confirm = None
                self.leave()
            if ui.button(surf, R(r.x + 42 * u + 2 * third, r.bottom - bh - 18 * u, third, bh), T('취소', 'Cancel'), 'ghost', size=18 * u):
                self.confirm = None
        else:
            ui.text(surf, T('놓은 물건을 모두 지울까요?', 'Remove all placed objects?'), r.centerx, r.y + 22 * u, 26 * u, (255, 255, 255), 'c')
            half = (r.w - 3 * 14 * u) / 2.0
            if ui.button(surf, R(r.x + 14 * u, r.bottom - bh - 18 * u, half, bh), T('모두 지우기', 'Clear all'), 'danger', size=20 * u):
                self.ed.clear_objs()
                self.changed()
                self.confirm = None
            if ui.button(surf, R(r.x + 28 * u + half, r.bottom - bh - 18 * u, half, bh), T('취소', 'Cancel'), 'ghost', size=20 * u):
                self.confirm = None
        ui.taps[:] = []

    def try_exit(self):
        if self.ed is not None and self.ed.dirty:
            self.confirm = ('exit', None)
        else:
            self.leave()

    def leave(self):
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
        app.start_race(d, int(d['laps']), entries, False, True, 3.0, p['mode'] == 'item')

    def on_back(self):
        if self.confirm is not None:
            self.confirm = None
        else:
            self.try_exit()
