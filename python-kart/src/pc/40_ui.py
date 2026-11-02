
# ============================================================================
#  [PC] 언어/폰트 + HUD + 키보드 메뉴 + 텍스트 입력
# ============================================================================
LANG = 'ko'


def T(ko, en):
    return ko if LANG == 'ko' else en


def find_korean_font():
    here = '.'
    try:
        here = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv and sys.argv[0] else '.'
    except Exception:
        pass
    cands = [os.path.join(here, n) for n in ('kart3d_font.ttf', 'kart3d_font.otf', 'kart3d_font.ttc')]
    cands += ['C:/Windows/Fonts/malgun.ttf', 'C:/Windows/Fonts/malgunbd.ttf', '/System/Library/Fonts/AppleSDGothicNeo.ttc',
              '/System/Library/Fonts/Supplemental/AppleGothic.ttf', '/Library/Fonts/AppleGothic.ttf',
              '/usr/share/fonts/truetype/nanum/NanumGothic.ttf', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
              '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc']
    for p in cands:
        if os.path.isfile(p):
            return p
    try:
        out = subprocess.check_output(['fc-list', ':lang=ko', 'file'], timeout=3).decode('utf-8', 'ignore')
        for line in out.splitlines():
            path = line.split(':')[0].strip()
            if path.lower().endswith(('.ttf', '.otf', '.ttc')) and os.path.isfile(path):
                return path
    except Exception:
        pass
    return None


def fmt_time(t):
    m = int(t // 60)
    return '%d:%05.2f' % (m, t - m * 60)


class Bar(object):
    """CardMaker 로 만든 가로 막대 (HUD/스탯)"""

    def __init__(self, parent, x, z, w, h, color, back=(0, 0, 0, 0.5)):
        cm = CardMaker('bar')
        cm.setFrame(0, 1, 0, 1)
        self.back = parent.attachNewNode(cm.generate())
        self.back.setPos(x, 0, z)
        self.back.setScale(w, 1, h)
        self.back.setColor(*back)
        self.back.setTransparency(TransparencyAttrib.MAlpha)
        self.fill = parent.attachNewNode(cm.generate())
        self.fill.setPos(x, 0, z)
        self.w, self.h = w, h
        self.fill.setColor(*color)
        self.set(0.0)

    def set(self, v, color=None):
        v = clamp(v, 0.0, 1.0)
        self.fill.setScale(max(0.0001, self.w * v), 1, self.h)
        if color:
            self.fill.setColor(*color)

    def show(self, flag=True):
        for n in (self.back, self.fill):
            n.show() if flag else n.hide()


class HUD(object):
    def __init__(self, app):
        self.app = app
        a = app
        self.root = a.aspect2d.attachNewNode('hud')
        kw = dict(font=a.font, mayChange=True, shadow=(0, 0, 0, 1))
        TL, TR, BR, TC = a.a2dTopLeft, a.a2dTopRight, a.a2dBottomRight, a.a2dTopCenter
        self.pos = OnscreenText(text='1', parent=TL, pos=(0.08, -0.2), scale=0.2, fg=(1, 0.69, 0.13, 1), align=TextNode.ALeft, **kw)
        self.tot = OnscreenText(text='/8', parent=TL, pos=(0.34, -0.2), scale=0.09, fg=(1, 1, 1, 1), align=TextNode.ALeft, **kw)
        self.lap = OnscreenText(text='LAP 1/3', parent=TL, pos=(0.08, -0.31), scale=0.062, fg=(1, 1, 1, 1), align=TextNode.ALeft, **kw)
        self.time = OnscreenText(text='0:00.00', parent=TL, pos=(0.08, -0.39), scale=0.055, fg=(0.85, 0.9, 1, 1), align=TextNode.ALeft, **kw)
        self.spd = OnscreenText(text='0', parent=BR, pos=(-0.45, 0.18), scale=0.2, fg=(1, 1, 1, 1), align=TextNode.ARight, **kw)
        self.kmh = OnscreenText(text='km/h', parent=BR, pos=(-0.43, 0.18), scale=0.06, fg=(0.8, 0.85, 0.96, 1), align=TextNode.ALeft, **kw)
        self.boost = Bar(BR, -0.88, 0.1, 0.78, 0.028, (0.1, 0.9, 1.0, 1))
        self.drift = Bar(BR, -0.88, 0.065, 0.78, 0.018, (1, 1, 1, 1))
        self.board = [OnscreenText(text='', parent=TL, pos=(0.08, -0.52 - i * 0.065), scale=0.045, fg=(1, 1, 1, 1), align=TextNode.ALeft, **kw) for i in range(6)]
        self.center = OnscreenText(text='', parent=a.aspect2d, pos=(0, 0.45), scale=0.3, fg=(1, 1, 1, 1), align=TextNode.ACenter, **kw)
        self.toast = OnscreenText(text='', parent=a.aspect2d, pos=(0, 0.62), scale=0.1, fg=(1, 0.8, 0.27, 1), align=TextNode.ACenter, **kw)
        self.wrong = OnscreenText(text='', parent=a.aspect2d, pos=(0, 0.2), scale=0.13, fg=(1, 0.3, 0.35, 1), align=TextNode.ACenter, **kw)
        self.fps = OnscreenText(text='', parent=a.a2dBottomLeft, pos=(0.03, 0.03), scale=0.04, fg=(1, 1, 0, 1), align=TextNode.ALeft, **kw)
        self.mapname = OnscreenText(text='', parent=TR, pos=(-0.04, -0.56), scale=0.04, fg=(0.85, 0.9, 1, 1), align=TextNode.ARight, **kw)
        self.mini_np = None
        self.dots = []
        self.toast_until = 0.0
        self.center_until = 0.0
        self.visible = True
        self._txt = {}

    def _set(self, node, text):
        """글자가 바뀔 때만 setText (매 프레임 글자 메시를 다시 만들면 느려짐)"""
        if self._txt.get(id(node)) != text:
            self._txt[id(node)] = text
            node.setText(text)

    def set_item_mode(self, on):
        self.toast.setPos(0, 0.5 if on else 0.62)

    def build_minimap(self, track):
        if self.mini_np is not None:
            self.mini_np.removeNode()
        a = self.app
        self.mini_np = a.a2dTopRight.attachNewNode('mini')
        self.mini_np.setPos(-0.3, 0, -0.3)
        b = track.bounds
        span = max(b[1] - b[0], b[3] - b[2], 1.0)
        self.mm_span = span
        self.mm_c = ((b[0] + b[1]) / 2.0, (b[2] + b[3]) / 2.0)
        cm = CardMaker('mbg')
        cm.setFrame(-0.27, 0.27, -0.27, 0.27)
        bg = self.mini_np.attachNewNode(cm.generate())
        bg.setColor(0, 0, 0, 0.4)
        bg.setTransparency(TransparencyAttrib.MAlpha)
        for thick, col in ((6, (0, 0, 0, 1)), (3, (0.92, 0.94, 1, 1))):
            ls = LineSegs('trk')
            ls.setThickness(thick)
            ls.setColor(*col)
            for i in range(0, track.N + 1, 2):
                k = i % track.N
                x, z = self.mm_xy(track.px[k], track.pz[k])
                (ls.moveTo if i == 0 else ls.drawTo)(x, 0, z)
            self.mini_np.attachNewNode(ls.create())
        for d in self.dots:
            d.removeNode()
        self.dots = []
        for i in range(14):
            cmd = CardMaker('dot')
            cmd.setFrame(-0.011, 0.011, -0.011, 0.011)
            d = self.mini_np.attachNewNode(cmd.generate())
            d.hide()
            self.dots.append(d)

    def mm_xy(self, x, z):
        s = 0.5 / self.mm_span
        return ((x - self.mm_c[0]) * s, -(z - self.mm_c[1]) * s)

    def show(self, flag):
        self.visible = flag
        for n in (self.pos, self.tot, self.lap, self.time, self.spd, self.kmh, self.center, self.toast, self.wrong, self.fps, self.mapname, *self.board):
            n.show() if flag else n.hide()
        self.boost.show(flag)
        self.drift.show(flag)
        if self.mini_np is not None:
            self.mini_np.show() if flag else self.mini_np.hide()

    def update(self, race, now):
        loc = race.local
        sim = loc.sim
        rank = race.ranking()
        ps = str(rank.index(loc) + 1)
        if self._txt.get(id(self.pos)) != ps:
            self.tot.setPos(0.28 + 0.12 * (len(ps) - 1), -0.2)
        self._set(self.pos, ps)
        self._set(self.tot, '/%d' % len(race.racers))
        self._set(self.lap, 'LAP %d/%d' % (min(race.laps, sim.lap), race.laps))
        self._set(self.time, fmt_time(max(0.0, race.t)))
        self._set(self.spd, str(int(sim.speed * 3.6)))
        self.boost.set(sim.speed / sim.stats['max_speed'], (1.0, 0.63, 0.16, 1) if sim.boost_t > 0 else (0.1, 0.9, 1.0, 1))
        if sim.drifting:
            col = [(0.67, 0.8, 1, 1), (0.23, 0.67, 1, 1), (1, 0.63, 0.16, 1), (0.82, 0.31, 1, 1)][sim.drift_tier]
            self.drift.show(True)
            self.drift.set(sim.drift_charge / 3.2, col)
        else:
            self.drift.show(False)
        for i, t in enumerate(self.board):
            if i < len(rank):
                r = rank[i]
                me = r is loc
                key = ('%d  %s' % (i + 1, r.name)) + ('\x01' if me else '')
                if self._txt.get(id(t)) != key:
                    self._txt[id(t)] = key
                    t.setText('%d  %s' % (i + 1, r.name))
                    t.setFg((1, 0.72, 0.15, 1) if me else (1, 1, 1, 1))
            else:
                self._set(t, '')
        # 카운트다운 / 알림
        if race.phase == 'count':
            n = int(math.ceil(max(0.0, race.count_left)))
            self._set(self.center, str(n) if 1 <= n <= 3 else '')
        elif now > self.center_until:
            self._set(self.center, '')
        if now > self.toast_until:
            self._set(self.toast, '')
        self._set(self.wrong, T('역주행!', 'WRONG WAY!') if (sim.wrong_way and race.phase == 'run' and not loc.finished) else '')
        # 미니맵
        if self.mini_np is not None:
            for i, d in enumerate(self.dots):
                if i < len(race.racers):
                    rc = race.racers[i]
                    x, z = self.mm_xy(rc.x, rc.z)
                    d.setPos(x, 0, z)
                    d.setColor(*((1, 0.69, 0.13, 1) if rc is loc else ((1, 0.43, 0.43, 1) if rc.kind == 'bot' else (0.35, 0.9, 1, 1))))
                    d.setScale(1.7 if rc is loc else 1.0)
                    d.show()
                else:
                    d.hide()

    def say(self, text, secs=1.2, big=False, color=(1, 0.8, 0.27, 1)):
        if big:
            self._set(self.center, text)
            self.center_until = time.time() + secs
        else:
            self._set(self.toast, text)
            self.toast.setFg(color)
            n = len(text)
            self.toast.setScale(0.1 if n <= 40 else max(0.05, 0.1 * 40.0 / n))      # 긴 문장은 글자를 줄여서 화면 안에
            self.toast_until = time.time() + secs

    def destroy(self):
        self.root.removeNode()
        for n in (self.pos, self.tot, self.lap, self.time, self.spd, self.kmh, self.center, self.toast, self.wrong, self.fps, self.mapname, *self.board):
            n.destroy()
        for b in (self.boost, self.drift):
            b.back.removeNode()
            b.fill.removeNode()
        if self.mini_np is not None:
            self.mini_np.removeNode()


class MenuUI(object):
    """키보드로 조작하는 텍스트 메뉴 (↑↓ 선택, ←→ 값 변경, Enter 실행, Esc 뒤로)"""

    def __init__(self, app):
        self.app = app
        self.root = app.a2dTopLeft.attachNewNode('menu')
        self.extra = app.aspect2d.attachNewNode('menu-extra')
        self.nodes = []
        self.rows = []
        self.sel = 0
        self.title = ''
        self.subtitle = ''
        self.hint = ''
        self.visible = True
        cm = CardMaker('panel')
        cm.setFrame(0.03, 1.72, -1.97, -0.04)
        self.panel = self.root.attachNewNode(cm.generate())
        self.panel.setColor(0.03, 0.05, 0.11, 0.78)
        self.panel.setTransparency(TransparencyAttrib.MAlpha)

    def set(self, title, rows, subtitle='', hint='', keep=True):
        sel_row = self.rows[self.sel].get('id') if (keep and self.rows and self.sel < len(self.rows)) else None
        self.title, self.rows, self.subtitle, self.hint = title, rows, subtitle, hint
        self.sel = 0
        if sel_row is not None:
            for i, r in enumerate(rows):
                if r.get('id') == sel_row:
                    self.sel = i
        if not self._selectable(self.sel):
            self.move(1)
        self.rebuild()

    def _selectable(self, i):
        return 0 <= i < len(self.rows) and self.rows[i].get('kind', 'item') != 'info' and self.rows[i].get('enabled', True)

    def clear(self):
        for n in self.nodes:
            n.destroy()
        self.nodes = []

    def rebuild(self):
        self.clear()
        a = self.app
        kw = dict(parent=self.root, font=a.font, mayChange=False, shadow=(0, 0, 0, 1), align=TextNode.ALeft)
        self.nodes.append(OnscreenText(text=self.title, pos=(0.12, -0.24), scale=0.13, fg=(1, 0.69, 0.13, 1), **kw))
        if self.subtitle:
            self.nodes.append(OnscreenText(text=self.subtitle, pos=(0.12, -0.34), scale=0.05, fg=(0.8, 0.86, 1, 1), **kw))
        z = -0.5
        for i, r in enumerate(self.rows):
            kind = r.get('kind', 'item')
            if kind == 'info':
                col = r.get('color', (0.78, 0.84, 0.98, 1))
                self.nodes.append(OnscreenText(text=r['text'], pos=(0.12, z), scale=r.get('scale', 0.05), fg=col, **kw))
                z -= r.get('gap', 0.075)
                continue
            sel = (i == self.sel)
            en = r.get('enabled', True)
            col = (1, 0.78, 0.22, 1) if sel else ((0.55, 0.57, 0.63, 1) if not en else ((1, 0.55, 0.45, 1) if kind == 'primary' else (0.95, 0.97, 1, 1)))
            txt = ('> ' if sel else '   ') + r['text']
            self.nodes.append(OnscreenText(text=txt, pos=(0.1, z), scale=0.074, fg=col, **kw))
            z -= 0.1
        if self.hint:
            self.nodes.append(OnscreenText(text=self.hint, pos=(0.12, -1.9), scale=0.04, fg=(0.7, 0.78, 0.95, 1), **kw))

    def move(self, d):
        n = len(self.rows)
        if n == 0:
            return
        for _ in range(n):
            self.sel = (self.sel + d) % n
            if self._selectable(self.sel):
                break
        self.rebuild()
        self.app.sfx_play('click', 0.4)

    def key(self, name, mult=1):
        if not self.rows:
            return False
        r = self.rows[self.sel] if self._selectable(self.sel) else None
        if name in ('arrow_down', 's'):
            self.move(1)
        elif name in ('arrow_up', 'w'):
            self.move(-1)
        elif name in ('arrow_left', 'a') and r and r.get('left'):
            r['left'](mult)
        elif name in ('arrow_right', 'd') and r and r.get('right'):
            r['right'](mult)
        elif name in ('enter', 'space') and r and r.get('enter'):
            self.app.sfx_play('click', 0.5)
            r['enter']()
        else:
            return False
        return True

    def show(self, flag):
        self.visible = flag
        if flag:
            self.root.show()
            self.extra.show()
        else:
            self.root.hide()
            self.extra.hide()

    def clear_extra(self):
        for c in list(self.extra.getChildren()):
            c.removeNode()


class TextInput(object):
    def __init__(self, app):
        self.app = app
        self.active = False
        self.text = ''
        self.title = ''
        self.maxlen = 14
        self.mode = 'alpha'
        self.cb = None
        self.node = None
        self.t = 0.0

    def begin(self, title, text, maxlen, mode, cb):
        self.active = True
        self.title, self.text, self.maxlen, self.mode, self.cb = title, str(text), maxlen, mode, cb
        self._draw()

    def _draw(self):
        if self.node is not None:
            self.node.destroy()
            self.node = None
        if not self.active:
            return
        cursor = '_' if int(self.t * 2) % 2 == 0 else ' '
        self.node = OnscreenText(text='%s\n\n%s%s\n\n[Enter] OK   [Esc] %s' % (self.title, self.text, cursor, T('취소', 'Cancel')), parent=self.app.aspect2d, pos=(0, 0.15), scale=0.085,
                                 fg=(1, 1, 1, 1), bg=(0, 0, 0, 0.88), shadow=(0, 0, 0, 1), align=TextNode.ACenter, font=self.app.font, mayChange=False)

    def tick(self, dt):
        if self.active:
            old = int(self.t * 2)
            self.t += dt
            if int(self.t * 2) != old:
                self._draw()

    def char(self, ch):
        if not self.active or len(ch) != 1 or not ch.isprintable():
            return
        if self.mode == 'num' and ch not in '0123456789':
            return
        if self.mode == 'ip' and ch not in '0123456789.:':
            return
        if len(self.text) < self.maxlen:
            self.text += ch
            self._draw()

    def backspace(self):
        if self.active:
            self.text = self.text[:-1]
            self._draw()

    def finish(self, ok):
        cb, text = self.cb, self.text
        self.active = False
        self._draw()
        if ok and cb:
            cb(text)
