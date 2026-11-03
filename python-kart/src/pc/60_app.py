
# ============================================================================
#  [PC] 게임 본체: 장면(메뉴/솔로/차고/설정/멀티/로비/레이스/결과) + 메인 루프
# ============================================================================
def wrap_map(m):
    return ((int(m) - 1) % MAP_COUNT) + 1


ITEM_KEYS_PC = {'1': 0, '2': 1, '3': 2, 'face_x': 0, 'face_y': 1, 'face_b': 2}


class Game(ShowBase):
    def __init__(self, args):
        global LANG
        self.args = args
        offscreen = bool(os.environ.get('KART3D_OFFSCREEN')) or bool(args.get('offscreen'))
        w, h = args.get('window', (1280, 720))
        cfg = ['window-title TURBO KART 3D', 'win-size %d %d' % (w, h), 'sync-video 1', 'framebuffer-multisample 1', 'multisamples 4']
        if args.get('fullscreen'):
            cfg.append('fullscreen 1')
        if offscreen:
            cfg += ['window-type offscreen', 'load-display p3tinydisplay', 'audio-library-name null']
        loadPrcFileData('', '\n'.join(cfg))
        ShowBase.__init__(self)
        self.offscreen = offscreen
        self.disableMouse()
        self.render.setAntialias(AntialiasAttrib.MAuto)
        self.camLens.setNearFar(0.4, 6000.0)
        self.profile = Profile()
        if args.get('port'):
            self.profile['port'] = args['port']
        path = find_korean_font()
        self.font = None
        self.font_en = None
        if path:
            try:
                self.font = self.loader.loadFont(Filename.fromOsSpecific(path).getFullpath())
                self.font.setPixelsPerUnit(64)
            except Exception:
                self.font = None
        lang = args.get('lang') or self.profile['lang']
        if lang == 'auto':
            lang = 'ko' if self.font else 'en'
        LANG = lang
        self.session = Session(self.profile)
        self.audio = Audio(self, self.profile['sound'])
        self.menu = MenuUI(self)
        self.input = TextInput(self)
        self.hud = HUD(self)
        self.hud.show(False)
        self.item_hud = ItemHUD(self)
        self.screen_fx = ScreenFxPC(self)
        self.item_world = None
        self.brake_held = False
        self.keys = set()
        self.steer = 0.0
        self.scene = 'menu'
        self.world = None
        self.world_map = None
        self.show_node = None
        self.show_rc = None
        self.race = None
        self.nodes = {}
        self.particles = None
        self.weather = None
        self.chase = ChaseCam()
        self.paused = False
        self.t = 0.0
        self.dt_override = None
        self.sel_map = int(self.profile['map'])
        self.scan = {'busy': False, 'rooms': [], 'done': False}
        self.err = ''
        self.finish_at = None
        self.shake = 0.0
        self.show_fps = bool(args.get('fps'))
        self.loading_txt = None
        self.store = MapStore()            # 내가 만든 맵 목록
        self.maker = PCMapMaker(self)      # 맵 만들기 편집기
        self.test_map = None               # 편집기 '시험 주행' 중인 맵
        self.sel_cmap = 0
        self.shown_scene = None
        self.pad = None
        try:
            devs = self.devices.getDevices(InputDevice.DeviceClass.gamepad)
            if devs:
                self.pad = devs[0]
                self.attachInputDevice(self.pad)
        except Exception:
            self.pad = None
        # 키 입력
        try:
            self.buttonThrowers[0].node().setModifierButtons(ModifierButtons())
            self.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
        except Exception:
            pass
        names = ['arrow_up', 'arrow_down', 'arrow_left', 'arrow_right', 'w', 'a', 's', 'd', 'space', 'lshift', 'rshift', 'lcontrol', 'rcontrol',
                 'r', 'm', 'enter', 'escape', 'f11', 'backspace', 't', '1', '2', '3', 'face_x', 'face_y', 'face_b', 'z', 'f']
        for k in names:
            self.accept(k, self._kdown, [k])
            self.accept(k + '-up', self._kup, [k])
            self.accept(k + '-repeat', self._krep, [k])
        self.accept('keystroke', self._keystroke)
        self.taskMgr.add(self.tick, 'tick')
        self.go('menu')

    # ------------------------------------------------------------------ 입력 처리
    def _kdown(self, k):
        self.keys.add(k)
        self.on_key(k)

    def _kup(self, k):
        self.keys.discard(k)

    def _krep(self, k):
        if k in ('arrow_up', 'arrow_down', 'arrow_left', 'arrow_right', 'backspace'):
            self.on_key(k)

    def _keystroke(self, ch):
        if self.input.active:
            self.input.char(ch)

    def mult(self):
        if 'lcontrol' in self.keys or 'rcontrol' in self.keys:
            return 100
        if 'lshift' in self.keys or 'rshift' in self.keys:
            return 10
        return 1

    def on_key(self, k):
        if self.input.active:
            if k == 'enter':
                self.input.finish(True)
            elif k == 'escape':
                self.input.finish(False)
            elif k == 'backspace':
                self.input.backspace()
            return
        if k == 'f11' and not self.offscreen:
            try:
                props = WindowProperties()
                props.setFullscreen(not self.win.isFullscreen())
                self.win.requestProperties(props)
            except Exception:
                pass
            return
        if self.scene == 'editor':
            self.maker.on_key(k)
            return
        if self.scene == 'race':
            if k in ITEM_KEYS_PC:
                self.use_item(ITEM_KEYS_PC[k])
            elif k == 'r' and self.race:
                self.race.respawn_local()
            elif k == 'escape':
                self.toggle_pause()
            elif k == 'm':
                self.audio.enabled = not self.audio.enabled
                self.hud.say(T('소리 켬', 'Sound on') if self.audio.enabled else T('소리 끔', 'Sound off'), 0.8)
                if not self.audio.enabled:
                    self.audio.silence()
            elif self.paused or self.scene == 'results':
                self.menu.key(k, 1)
            return
        if k == 'escape':
            self.back()
            return
        if self.scene == 'solo':
            if k == 'r':
                self.sel_map = 1 + int(_random.random() * MAP_COUNT)
                self.build_solo()
                return
            if k == 't':
                fa, ti_, mi_ = biome_parts(self.sel_map)
                self.sel_map = biome_map(fa + 1, ti_, mi_)
                self.build_solo()
                return
        self.menu.key(k, self.mult())

    def back(self):
        sc = self.scene
        if sc == 'menu':
            self.userExit()
        elif sc in ('solo', 'garage', 'settings', 'multi', 'maps'):
            self.profile.save()
            self.go('menu')
        elif sc == 'mapitem':
            self.go('maps')
        elif sc == 'editor':
            self.maker.try_exit()
        elif sc == 'lobby':
            self.session.leave()
            self.go('menu')
        elif sc == 'results':
            self.leave_race()

    def sfx_play(self, name, vol=1.0):
        self.audio.play(name, vol)

    def loading(self, msg):
        if self.loading_txt is not None:
            self.loading_txt.destroy()
        self.loading_txt = OnscreenText(text=msg, parent=self.aspect2d, pos=(0, 0), scale=0.11, fg=(1, 1, 1, 1), bg=(0, 0, 0, 0.85), font=self.font, mayChange=False)
        self.graphicsEngine.renderFrame()
        self.graphicsEngine.renderFrame()

    def loading_done(self):
        if self.loading_txt is not None:
            self.loading_txt.destroy()
            self.loading_txt = None

    # ------------------------------------------------------------------ 월드/쇼룸
    def destroy_world(self):
        for n in list(self.nodes.values()):
            n.destroy()
        self.nodes = {}
        if self.show_node is not None:
            self.show_node.destroy()
            self.show_node = None
        if self.particles is not None:
            self.particles.destroy()
            self.particles = None
        if self.weather is not None:
            self.weather.destroy()
            self.weather = None
        if self.item_world is not None:
            self.item_world.destroy()
            self.item_world = None
        if self.world is not None:
            self.world.destroy()
            self.world = None
        self.world_map = None

    def ensure_showroom(self):
        mid = int(self.profile['map'])
        if self.world is None or self.world_map != mid:
            self.destroy_world()
            self.loading(T('준비 중…', 'Preparing…'))
            tr = Track(mid)
            self.world = World(self, tr)
            self.world_map = mid
            self.loading_done()
            rc = Racer('show', '', int(self.profile['kart']), 0, 'bot')
            pf = tr.N - 9.0
            x, y, z, h = tr.pose_at(pf, 0.0)
            rc.x, rc.y, rc.z, rc.h = x, y, z, h
            rc.idx = int(pf) % tr.N
            rc.up = tr.surface_normal(rc.idx)
            rc.speed = 7.0
            self.show_rc = rc
            self.show_node = KartNode(self, rc, self.world.root)
        if self.show_node.rc.kart_id != int(self.profile['kart']):
            self.show_node.destroy()
            self.show_rc.kart_id = int(self.profile['kart'])
            self.show_node = KartNode(self, self.show_rc, self.world.root)

    def update_showroom(self, dt):
        self.ensure_showroom()
        rc = self.show_rc
        rc.total += dt * 2.0
        self.show_node.update(rc, dt, self.world.track.ds, 20.0)
        th = self.t * 0.45
        ctr = PV(rc.x, rc.y + 0.9, rc.z)
        dist = 8.2
        shift = 0.0
        if self.scene in ('menu', 'garage'):
            shift = -2.6
        # 카메라 오빗 (카트가 화면 오른쪽에 오도록 중심을 왼쪽으로 이동)
        cam = (ctr[0] + math.sin(th) * dist, ctr[1] + math.cos(th) * dist, ctr[2] + 1.5)
        self.camera.setPos(*cam)
        right = (-math.cos(th), math.sin(th), 0.0)
        self.camera.lookAt(Point3(ctr[0] + right[0] * shift, ctr[1] + right[1] * shift, ctr[2]), Vec3(0, 0, 1))
        self.camLens.setFov(56)
        self.world.update(cam)

    # ------------------------------------------------------------------ 장면 구성 (메뉴 행)
    def R(self, text, enter=None, left=None, right=None, kind='item', enabled=True, id=None):
        return dict(text=text, enter=enter, left=left, right=right, kind=kind, enabled=enabled, id=id)

    def I(self, text, color=None, scale=0.05):
        d = dict(text=text, kind='info', scale=scale)
        if color:
            d['color'] = color
        return d

    def go(self, scene):
        self.scene = scene
        self.err = ''
        self.menu.clear_extra()
        if scene != 'editor':
            self.maker.leave_ui()
        if scene != 'race':
            self.hud.show(False)
            self.item_hud.show(False)
            self.screen_fx.clear()
            self.menu.show(True)
        if scene == 'menu':
            self.build_main()
        elif scene == 'solo':
            self.sel_map = int(self.profile['map'])
            self.build_solo()
        elif scene == 'garage':
            self.build_garage()
        elif scene == 'settings':
            self.build_settings()
        elif scene == 'multi':
            self.scan_rooms()
            self.build_multi()
        elif scene == 'lobby':
            self.build_lobby()
        elif scene == 'maps':
            self.build_maps()
        elif scene == 'mapitem':
            self.build_mapitem()
        elif scene == 'editor':
            self.maker.enter()

    def build_main(self):
        self.menu.clear_extra()
        rows = [self.R(T('솔로 레이스', 'Solo race'), lambda: self.go('solo'), kind='primary', id='solo'),
                self.R(T('WiFi 멀티플레이', 'WiFi multiplayer'), lambda: self.go('multi'), kind='primary', id='multi'),
                self.R(T('맵 만들기 (내 맵 %d개)' % len(self.store.maps), 'Map maker (%d maps)' % len(self.store.maps)), lambda: self.go('maps'), id='maps'),
                self.R(T('차고 (카트 꾸미기)', 'Garage (customize)'), lambda: self.go('garage'), id='garage'),
                self.R(T('설정', 'Settings'), lambda: self.go('settings'), id='settings'),
                self.R(T('종료', 'Quit'), self.userExit, id='quit')]
        if self.err:
            rows.append(self.I(self.err, (1, 0.5, 0.5, 1)))
        rows.append(self.I('%s  #%d' % (kart_name(self.profile['kart'], LANG), int(self.profile['kart']) + 1), scale=0.045))
        self.menu.set('TURBO KART 3D', rows, T('맵·바이옴 1000종 · 카트 100,000종 · 아이템 100종 · WiFi 멀티', '1000 maps & biomes · 100,000 karts · 100 items · WiFi multiplayer'), T('↑↓ 선택   Enter 확인   F11 전체화면', 'Up/Down select   Enter OK   F11 fullscreen'))

    # ---- 솔로 ----
    def draw_outline(self, mid):
        self.menu.clear_extra()
        try:
            tr = Track(mid, True)
        except Exception:
            return
        b = tr.bounds
        span = max(b[1] - b[0], b[3] - b[2], 1.0)
        aspect = self.getAspectRatio()
        node = self.menu.extra.attachNewNode('outline')
        node.setPos(aspect - 0.78, 0, 0.12)
        cm = CardMaker('obg')
        cm.setFrame(-0.68, 0.68, -0.62, 0.62)
        bg = node.attachNewNode(cm.generate())
        bg.setColor(0.03, 0.05, 0.11, 0.78)
        bg.setTransparency(TransparencyAttrib.MAlpha)
        cx, cz = (b[0] + b[1]) / 2.0, (b[2] + b[3]) / 2.0
        s = 1.05 / span
        wc = hex_rgb(tr.theme['wall'][0])
        for thick, col in ((7, (0, 0, 0, 1)), (4, (wc[0] / 255.0, wc[1] / 255.0, wc[2] / 255.0, 1)), (2, (0.17, 0.18, 0.23, 1))):
            ls = LineSegs('o')
            ls.setThickness(thick)
            ls.setColor(*col)
            for i in range(0, tr.N + 1, 2):
                k = i % tr.N
                (ls.moveTo if i == 0 else ls.drawTo)((tr.px[k] - cx) * s, 0, -(tr.pz[k] - cz) * s)
            node.attachNewNode(ls.create())
        t = OnscreenText(text='%s · %.2f km' % (tr.theme['name'] if LANG == 'ko' else tr.theme['en'], tr.length / 1000.0), parent=node, pos=(0, -0.7), scale=0.05, fg=(0.85, 0.9, 1, 1),
                         font=self.font, mayChange=False, shadow=(0, 0, 0, 1))
        self.menu.nodes.append(t)
        self.outline_len = tr.length

    def custom_rows(self, editable=True):
        """'내가 만든 맵' 고르기 행 (←→ 로 바꾸기). 반환: (행 목록, 고른 맵 또는 None)"""
        maps = self.store.maps
        if not maps:
            return [self.I(T('아직 만든 맵이 없어요 -> 메뉴의 [맵 만들기]', 'No custom maps yet -> Map maker'), (1, 0.75, 0.5, 1)),
                    self.R(T('맵 만들기로 가기', 'Open map maker'), lambda: self.go('maps'), id='gomaps')], None
        i = max(0, self.store.index(self.profile['cmap']))
        d = maps[i]

        def cm(dd):
            def f(m=1):
                j = (self.store.index(self.profile['cmap']) + dd) % len(self.store.maps)
                self.profile['cmap'] = self.store.maps[j]['uid']
                self.profile.save()
                self.rebuild_scene()
            return f
        self.profile['cmap'] = d['uid']
        rows = [self.R(u'%s  < \u2605 %s  (%d/%d) >' % (T('내 맵', 'My map'), d['name'], i + 1, len(maps)), None, cm(-1), cm(1), id='cmap', enabled=editable)]
        return rows, d

    def rebuild_scene(self):
        if self.scene == 'solo':
            self.build_solo()
        elif self.scene == 'lobby':
            self._lobby_sig = None

    def build_solo(self):
        if self.profile['map_src'] == 'custom':
            return self.build_solo_custom()
        mid = self.sel_map = wrap_map(self.sel_map)
        info = map_info(mid)
        name = info['name'] if LANG == 'ko' else info['name_en']
        theme = info['theme_name'] if LANG == 'ko' else info['theme_en']

        def chg(d):
            def f(m=1):
                self.sel_map = wrap_map(self.sel_map + d * m)
                self.build_solo()
            return f

        def setpart(which, d):
            def f(m=1):
                fa, ti_, mi_ = biome_parts(self.sel_map)
                if which == 0:
                    fa += d
                elif which == 1:
                    ti_ += d
                else:
                    mi_ += d
                self.sel_map = biome_map(fa, ti_, mi_)
                self.build_solo()
            return f
        fam = biome_parts(mid)[0]
        fname, tname, moodname = biome_part_names(mid, LANG)

        def typemap():
            def done(t):
                try:
                    self.sel_map = wrap_map(int(t))
                except ValueError:
                    pass
                self.build_solo()
            self.input.begin(T('맵 번호 (1~1000)', 'Map number (1-1000)'), '', 4, 'num', done)

        def lap(d):
            def f(m=1):
                self.profile['laps'] = int(clamp(int(self.profile['laps']) + d, 1, 10))
                self.build_solo()
            return f

        def bots(d):
            def f(m=1):
                self.profile['bots'] = int(clamp(int(self.profile['bots']) + d, 0, 11))
                self.build_solo()
            return f

        def start():
            self.profile['map'] = self.sel_map
            self.profile.save()
            self.start_solo()

        def mode(m=1):
            self.profile['mode'] = 'speed' if self.profile['mode'] == 'item' else 'item'
            self.profile.save()
            self.build_solo()
        mname = T('아이템전 (아이템 100종)', 'Item battle (100 items)') if self.profile['mode'] == 'item' else T('스피드전', 'Speed race')

        def src(m=1):
            self.profile['map_src'] = 'custom'
            self.profile.save()
            self.build_solo()
        rows = [self.R('%s  < %s >' % (T('모드', 'Mode'), mname), mode, mode, mode, id='mode'),
                self.R('%s  < %s >' % (T('맵 종류', 'Maps'), T('기본 맵 1000개', 'Built-in 1000')), src, src, src, id='src'),
                self.R('%s  < #%d / %d >' % (T('맵', 'Map'), mid, MAP_COUNT), typemap, chg(-1), chg(1), id='map'),
                self.R('%s  < %s (%d/%d) >' % (T('바이옴', 'Biome'), fname, fam + 1, BIOME_FAMILIES), None, setpart(0, -1), setpart(0, 1), id='theme'),
                self.R('%s  < %s >' % (T('시간대', 'Time'), tname), None, setpart(1, -1), setpart(1, 1), id='time'),
                self.R('%s  < %s >' % (T('색감', 'Mood'), moodname), None, setpart(2, -1), setpart(2, 1), id='mood'),
                self.R('%s  < %d >' % (T('바퀴 수', 'Laps'), int(self.profile['laps'])), None, lap(-1), lap(1), id='laps'),
                self.R('%s  < %d >' % (T('AI 상대', 'AI rivals'), int(self.profile['bots'])), None, bots(-1), bots(1), id='bots'),
                self.R(T('출발!', 'START!'), start, kind='primary', id='start'),
                self.R(T('뒤로', 'Back'), lambda: self.back(), id='back')]
        self.menu.set(T('솔로 레이스', 'Solo race'), rows, '%s  ·  %s' % (name, theme),
                      T('←→ ±1   Shift ±10   Ctrl ±100   R 랜덤   T 바이옴   Enter(맵) 번호 입력', 'Left/Right ±1   Shift ±10   Ctrl ±100   R random   T biome   Enter on map: type number'))
        self.draw_outline(mid)

    def build_solo_custom(self):
        def mode(m=1):
            self.profile['mode'] = 'speed' if self.profile['mode'] == 'item' else 'item'
            self.profile.save()
            self.build_solo()

        def src(m=1):
            self.profile['map_src'] = 'builtin'
            self.profile.save()
            self.build_solo()

        def lap(dd):
            def f(m=1):
                self.profile['laps'] = int(clamp(int(self.profile['laps']) + dd, 1, 10))
                self.build_solo()
            return f

        def bots(dd):
            def f(m=1):
                self.profile['bots'] = int(clamp(int(self.profile['bots']) + dd, 0, 11))
                self.build_solo()
            return f

        def start():
            self.profile.save()
            self.start_solo()
        mname = T('아이템전 (아이템 100종)', 'Item battle (100 items)') if self.profile['mode'] == 'item' else T('스피드전', 'Speed race')
        crows, d = self.custom_rows()
        rows = [self.R('%s  < %s >' % (T('모드', 'Mode'), mname), mode, mode, mode, id='mode'),
                self.R('%s  < %s >' % (T('맵 종류', 'Maps'), T('내가 만든 맵 (%d)' % len(self.store.maps), 'My maps (%d)' % len(self.store.maps))), src, src, src, id='src')]
        rows += crows
        if d is not None:
            rows.append(self.R(T('이 맵 편집하기', 'Edit this map'), lambda: self.maker.open(d, d['uid']), id='edit'))
        rows += [self.R('%s  < %d >' % (T('바퀴 수', 'Laps'), int(self.profile['laps'])), None, lap(-1), lap(1), id='laps'),
                 self.R('%s  < %d >' % (T('AI 상대', 'AI rivals'), int(self.profile['bots'])), None, bots(-1), bots(1), id='bots')]
        if d is not None:
            rows.append(self.R(T('출발!', 'START!'), start, kind='primary', id='start'))
        rows.append(self.R(T('뒤로', 'Back'), lambda: self.back(), id='back'))
        sub = ''
        if d is not None:
            th = biome(d['look'])
            sub = u'\u2605 %s  ·  %s' % (d['name'], th['name'] if LANG == 'ko' else th['en'])
        self.menu.set(T('솔로 레이스', 'Solo race'), rows, sub, T('←→ 값 변경   Enter 확인', 'Left/Right change   Enter OK'))
        if d is not None:
            self.draw_outline(d)
        else:
            self.menu.clear_extra()

    # ---- 맵 만들기 (목록) ----
    def build_maps(self):
        def new():
            n = len(self.store.maps) + 1
            self.maker.open(cmap_new(T('나의 맵 %d' % n, 'My map %d' % n), int(self.profile['map'])), None)

        def imp_d(dd):
            def f(m=1):
                self.import_mid = wrap_map(getattr(self, 'import_mid', 1) + dd * m)
                self.build_maps()
            return f

        def imp():
            mid = getattr(self, 'import_mid', 1)
            self.maker.open(cmap_from_builtin(mid, map_info(mid)['name' if LANG == 'ko' else 'name_en']), None)
        rows = [self.R(T('+ 새 맵 만들기', '+ New map'), new, kind='primary', id='new'),
                self.R('%s  < #%d >' % (T('기본 맵 코스로 시작', 'Start from built-in map'), getattr(self, 'import_mid', 1)), imp, imp_d(-1), imp_d(1), id='imp')]
        for i, d in enumerate(self.store.maps[:14]):
            def pick(uid=d['uid']):
                self.sel_cmap_uid = uid
                self.go('mapitem')
            rows.append(self.R(u'\u2605 %s   (%d)' % (d['name'], len(d['objs'])), pick, id='m_' + d['uid']))
        if len(self.store.maps) > 14:
            rows.append(self.I(T('(맵이 많아서 14개까지만 보여요)', '(showing the first 14 maps)')))
        rows.append(self.R(T('뒤로', 'Back'), lambda: self.back(), id='back'))
        self.menu.set(T('맵 만들기', 'Map maker'), rows, T('내 맵 %d개 · 파일 kart3d_maps.json (폰과 같은 형식)', '%d maps · file kart3d_maps.json (same as phone)') % len(self.store.maps)
                      if LANG == 'ko' else 'Map maker', T('Enter = 열기   ←→ = 번호 바꾸기', 'Enter = open   Left/Right = change number'))
        self.menu.clear_extra()

    def build_mapitem(self):
        uid = getattr(self, 'sel_cmap_uid', '')
        d = self.store.get(uid)
        if d is None:
            self.go('maps')
            return

        def race():
            self.profile['map_src'] = 'custom'
            self.profile['cmap'] = uid
            self.profile.save()
            self.go('solo')

        def rename():
            def done(t):
                t = t.strip()
                if t:
                    dd = dict(d)
                    dd['name'] = t
                    self.store.put(dd)
                self.build_mapitem()
            self.input.begin(T('맵 이름 (Enter 확인)', 'Map name (Enter = OK)'), d['name'], 20, 'alpha', done)

        def delete():
            if getattr(self, '_del_armed', None) == uid:
                self.store.delete(uid)
                self._del_armed = None
                if self.profile['cmap'] == uid:
                    self.profile['cmap'] = ''
                    self.profile['map_src'] = 'builtin'
                self.go('maps')
            else:
                self._del_armed = uid
                self.build_mapitem()
        armed = getattr(self, '_del_armed', None) == uid
        th = biome(d['look'])
        rows = [self.R(T('편집하기', 'Edit'), lambda: self.maker.open(d, uid), kind='primary', id='edit'),
                self.R(T('이 맵으로 달리기 (솔로)', 'Race this map (solo)'), race, id='race'),
                self.R(T('이름 바꾸기', 'Rename'), rename, id='rename'),
                self.R(T('정말 삭제! (Enter 한 번 더)', 'Really delete! (Enter again)') if armed else T('삭제', 'Delete'), delete, id='del'),
                self.R(T('뒤로', 'Back'), lambda: self.go('maps'), id='back')]
        self.menu.set(u'\u2605 ' + d['name'], rows, '%s  ·  %s %d' % (th['name'] if LANG == 'ko' else th['en'], T('물건', 'objects'), len(d['objs'])), '')
        self.draw_outline(d)

    # ---- 차고 ----
    def build_garage(self):
        k = decode_kart(self.profile['kart'])

        def part(key, mod):
            def mk(d):
                def f(m=1):
                    k2 = decode_kart(self.profile['kart'])
                    k2[key] = (k2[key] + d) % mod
                    self.profile['kart'] = encode_kart(k2)
                    self.profile.save()
                    self.session.send_profile()
                    self.build_garage()
                return f
            return mk(-1), mk(1)

        def setname():
            def done(t):
                self.profile['name'] = t.strip()
                self.profile.save()
                self.session.send_profile()
                self.build_garage()
            self.input.begin(T('닉네임', 'Nickname'), self.profile['name'], 14, 'alpha', done)

        def num(d):
            def f(m=1):
                self.profile['kart'] = (int(self.profile['kart']) + d * m) % KART_COUNT
                self.profile.save()
                self.session.send_profile()
                self.build_garage()
            return f

        def typenum():
            def done(t):
                try:
                    self.profile['kart'] = int(clamp(int(t), 1, KART_COUNT)) - 1
                    self.profile.save()
                    self.session.send_profile()
                except ValueError:
                    pass
                self.build_garage()
            self.input.begin(T('카트 번호 (1~100000)', 'Kart number (1-100000)'), '', 6, 'num', done)

        def rnd():
            self.profile['kart'] = int(_random.random() * KART_COUNT)
            self.profile.save()
            self.session.send_profile()
            self.build_garage()
        kk = 'name' if LANG == 'ko' else 'en'
        bl, br = part('body', 20)
        pl, pr = part('paint', 20)
        wl, wr = part('wheel', 25)
        gl, gr = part('wing', 10)
        rows = [self.R('%s: %s' % (T('닉네임', 'Name'), self.profile.display_name()), setname, id='name'),
                self.R('%s  < %s >' % (T('차체', 'Body'), BODIES[k['body']][kk]), None, bl, br, id='body'),
                self.R('%s  < %s >' % (T('페인트', 'Paint'), PAINTS[k['paint']][kk]), None, pl, pr, id='paint'),
                self.R('%s  < %s >' % (T('휠', 'Wheels'), wheel_name(k['wheel'], LANG)), None, wl, wr, id='wheel'),
                self.R('%s  < %s >' % (T('윙/파츠', 'Wing'), WINGS[k['wing']][kk]), None, gl, gr, id='wing'),
                self.R('%s  < %d / %d >' % (T('카트 번호', 'Kart No.'), int(self.profile['kart']) + 1, KART_COUNT), typenum, num(-1), num(1), id='num'),
                self.R(T('랜덤 카트', 'Random kart'), rnd, kind='primary', id='rnd'),
                self.R(T('완료', 'Done'), lambda: self.back(), id='done')]
        self.menu.set(T('차고', 'Garage'), rows, kart_name(self.profile['kart'], LANG), T('←→ 파츠 변경   Shift/Ctrl 번호 ±10/±100', 'Left/Right change   Shift/Ctrl number ±10/±100'))
        self.menu.clear_extra()
        st = kart_stats(self.profile['kart'])
        aspect = self.getAspectRatio()
        for i, (lab, key) in enumerate(((T('최고속도', 'Speed'), 'speed'), (T('가속', 'Accel'), 'accel'), (T('핸들링', 'Handling'), 'handling'), (T('드리프트', 'Drift'), 'drift'))):
            z = -0.52 - i * 0.12
            x0 = aspect - 1.05
            self.menu.nodes.append(OnscreenText(text=lab, parent=self.menu.extra, pos=(x0, z + 0.9 + 0.0), scale=0.045, fg=(0.8, 0.86, 1, 1), align=TextNode.ALeft, font=self.font, mayChange=False, shadow=(0, 0, 0, 1)))
            Bar(self.menu.extra, x0 + 0.3, z + 0.9 - 0.005, 0.5, 0.035, (1, 0.69, 0.13, 1)).set(st[key] / 10.0)

    # ---- 설정 ----
    def build_settings(self):
        def lang():
            order = ['auto', 'ko', 'en']
            self.profile['lang'] = order[(order.index(self.profile['lang']) + 1) % 3]
            global LANG
            LANG = ('ko' if self.font else 'en') if self.profile['lang'] == 'auto' else self.profile['lang']
            self.profile.save()
            self.build_settings()

        def snd():
            self.profile['sound'] = not self.profile['sound']
            self.audio.enabled = bool(self.profile['sound'])
            self.profile.save()
            self.build_settings()

        def fps():
            self.show_fps = not self.show_fps
            self.build_settings()

        def steer_resp():
            self.profile['steer_resp'] = (int(self.profile['steer_resp']) + 1) % 3
            self.profile.save()
            self.build_settings()
        sn = [T('부드럽게', 'Smooth'), T('보통', 'Normal'), T('빠르게', 'Quick')]
        rows = [self.R('%s: %s' % (T('언어 / Language', 'Language'), self.profile['lang']), lang, id='lang'),
                self.R('%s: %s' % (T('소리', 'Sound'), 'ON' if self.profile['sound'] else 'OFF'), snd, id='snd'),
                self.R('%s: %s' % (T('조향 반응', 'Steering'), sn[int(self.profile['steer_resp']) % 3]), steer_resp, id='steer'),
                self.R('FPS: %s' % ('ON' if self.show_fps else 'OFF'), fps, id='fps'),
                self.R(T('완료', 'Done'), lambda: self.back(), id='done')]
        self.menu.set(T('설정', 'Settings'), rows, '', T('Enter 로 값 변경', 'Enter to change'))

    # ---- 멀티플레이 ----
    def scan_rooms(self):
        if not self.scan.get('busy'):
            self.scan = {'busy': True, 'rooms': self.scan.get('rooms', []), 'done': False}
            discover_async(self.scan)

    def join_ip(self, text):
        t = text.strip()
        if not t:
            return
        port = int(self.profile['port'])
        if ':' in t:
            t, p = t.split(':', 1)
            try:
                port = int(p)
            except ValueError:
                pass
        self.profile['last_ip'] = t
        self.profile.save()
        self.session.join_game(t, port)
        self.go('lobby')

    def build_multi(self):
        ips = local_ips()

        def host():
            cm = self.store.get(self.profile['cmap']) if self.profile['map_src'] == 'custom' else None
            if self.session.host_game(int(self.profile['port']), cm):
                self.go('lobby')
            else:
                self.err = self.session.error
                self.build_multi()

        def ipin():
            self.input.begin(T('호스트 IP (예: 192.168.0.5)', 'Host IP (e.g. 192.168.0.5)'), self.profile['last_ip'], 21, 'ip', self.join_ip)

        def rescan():
            self.scan_rooms()
            self.build_multi()
        rows = [self.I(T('내 IP: ', 'My IP: ') + (', '.join(ips) if ips else T('(WiFi 연결 확인)', '(check WiFi)'))),
                self.R(T('방 만들기 (호스트)', 'Host a game'), host, kind='primary', id='host'),
                self.R(T('IP 직접 입력해서 참가', 'Join by IP'), ipin, id='ip'),
                self.R(T('방 다시 검색', 'Rescan rooms'), rescan, id='rescan'),
                self.I(T('같은 WiFi 의 방:', 'Rooms on this WiFi:'), (1, 0.86, 0.47, 1))]
        rooms = self.scan.get('rooms', [])
        if self.scan.get('busy') and not rooms:
            rows.append(self.I(T('검색 중…', 'Searching…')))
        elif not rooms:
            rows.append(self.I(T('방이 없어요. 친구가 [방 만들기] 후 IP 로 접속하세요.', 'No rooms. Ask a friend to host, then join by IP.')))
        for i, rm in enumerate(rooms[:6]):
            def joiner(rm=rm):
                self.profile['last_ip'] = rm['ip']
                self.session.join_game(rm['ip'], rm.get('port', DEFAULT_PORT))
                self.go('lobby')
            mlab = (u'\u2605 ' + str(rm['cname'])) if rm.get('cname') else '#%s' % rm.get('map', '?')
            rows.append(self.R('%s  %s  %d/%d  %s' % (rm.get('name', 'room'), rm['ip'], rm.get('players', 0), RoomServer.MAX_PLAYERS, mlab), joiner,
                               enabled=rm.get('state') == 'lobby', id='room%d' % i))
        if self.err:
            rows.append(self.I(self.err, (1, 0.5, 0.5, 1)))
        rows.append(self.R(T('뒤로', 'Back'), lambda: self.back(), id='back'))
        self.menu.set(T('WiFi 멀티플레이', 'WiFi multiplayer'), rows, '', '')

    def build_lobby(self):
        ses = self.session
        st = ses.settings
        if ses.state == 'connecting':
            rows = [self.I(T('연결 중… ', 'Connecting… ') + ses.address), self.R(T('취소', 'Cancel'), lambda: (ses.leave(), self.go('multi')), id='cancel')]
            self.menu.set(T('로비', 'Lobby'), rows, '', '')
            self.menu.clear_extra()
            return
        rows = [self.I('%s %d/%d' % (T('플레이어', 'Players'), len(ses.players), RoomServer.MAX_PLAYERS), (1, 0.86, 0.47, 1), 0.055)]
        for p in ses.players[:8]:
            rows.append(self.I(('* ' if p['id'] == ses.host_id else '  ') + p['name'] + ('  (YOU)' if p['id'] == ses.my_id else ''), (1, 0.72, 0.15, 1) if p['id'] == ses.my_id else None, 0.05))
        info = map_info(st['map'])
        mname = '%s  ·  %s' % ((info['name'], info['theme_name']) if LANG == 'ko' else (info['name_en'], info['theme_en']))
        cmd = st.get('cmap')
        if cmd:
            mname = u'\u2605 %s  (%s)' % (cmd.get('name', '?'), T('직접 만든 맵', 'custom map'))
        if ses.is_host:
            def mp(d):
                def f(m=1):
                    ses.send_settings(map=wrap_map(int(st['map']) + d * m))
                return f

            def lp(d):
                def f(m=1):
                    ses.send_settings(laps=int(clamp(int(st['laps']) + d, 1, 10)))
                return f

            def bp(d):
                def f(m=1):
                    ses.send_settings(bots=int(clamp(int(st['bots']) + d, 0, 11)))
                return f

            def md(m=1):
                on = not bool(st.get('items'))
                ses.send_settings(items=on)
                self.profile['mode'] = 'item' if on else 'speed'

            def srcf(m=1):
                if cmd:
                    ses.send_settings(map=int(st['map']))
                    self.profile['map_src'] = 'builtin'
                else:
                    d = self.store.get(self.profile['cmap']) or (self.store.maps[0] if self.store.maps else None)
                    if d is not None:
                        self.profile['cmap'] = d['uid']
                        ses.send_settings(cmap=d)
                        self.profile['map_src'] = 'custom'

            def cmf(dd):
                def f(m=1):
                    maps = self.store.maps
                    if maps:
                        j = (self.store.index(self.profile['cmap']) + dd) % len(maps)
                        self.profile['cmap'] = maps[j]['uid']
                        ses.send_settings(cmap=maps[j])
                return f
            rows += [self.R('%s  < %s >' % (T('모드', 'Mode'), T('아이템전', 'Item battle') if st.get('items') else T('스피드전', 'Speed race')), md, md, md, id='mode'),
                     self.R('%s  < %s >' % (T('맵 종류', 'Maps'), T('내가 만든 맵', 'My maps') if cmd else T('기본 맵', 'Built-in')), srcf, srcf, srcf, id='src',
                            enabled=bool(cmd) or bool(self.store.maps))]
            if cmd:
                rows.append(self.R(u'%s  < \u2605 %s >' % (T('내 맵', 'My map'), cmd.get('name', '?')), None, cmf(-1), cmf(1), id='cmap'))
            else:
                rows.append(self.R('%s  < #%d >' % (T('맵', 'Map'), st['map']), None, mp(-1), mp(1), id='map'))
            rows += [
                     self.R('%s  < %d >' % (T('바퀴 수', 'Laps'), st['laps']), None, lp(-1), lp(1), id='laps'),
                     self.R('%s  < %d >' % (T('AI 봇', 'Bots'), st['bots']), None, bp(-1), bp(1), id='bots'),
                     self.R(T('레이스 시작!', 'START RACE!'), ses.start_race, kind='primary', id='start')]
            ips = local_ips()
            rows.append(self.I(T('친구에게 알려주세요: ', 'Tell your friends: ') + (ips[0] if ips else '?') + ':%d' % self.profile['port'], (1, 0.86, 0.47, 1)))
        else:
            mlab = (u'\u2605 ' + cmd.get('name', '?')) if cmd else '#%d' % st['map']
            rows.append(self.I('%s %s   %s %d   %s %d   %s' % (T('맵', 'Map'), mlab, T('바퀴', 'Laps'), st['laps'], T('봇', 'Bots'), st['bots'],
                                                             T('아이템전', 'Item battle') if st.get('items') else T('스피드전', 'Speed race'))))
            if cmd:
                def save_it(d=cmd):
                    if self.store.add_copy(d):
                        self.err = T('내 맵에 저장했어요', 'Saved to My maps')
                rows.append(self.R(T('이 맵을 내 맵에 저장', 'Save this map to My maps'), save_it, id='savemap'))
            rows.append(self.I(T('방장이 시작하기를 기다리는 중…', 'Waiting for the host…')))
        rows.append(self.R(T('나가기', 'Leave'), lambda: self.back(), id='leave'))
        self.menu.set(T('로비', 'Lobby'), rows, mname, T('←→ 값 변경 (Shift ±10, Ctrl ±100)', 'Left/Right change (Shift ±10, Ctrl ±100)'))
        key = (st['map'], cmap_key(cmd) if cmd else None)
        if getattr(self, '_lobby_map', None) != key or not self.menu.extra.getChildren():
            self.draw_outline(cmd if cmd else int(st['map']))
            self._lobby_map = key

    # ------------------------------------------------------------------ 레이스
    def solo_map(self):
        if self.test_map is not None:
            return self.test_map
        if self.profile['map_src'] == 'custom':
            d = self.store.get(self.profile['cmap'])
            if d is not None:
                return d
        return int(self.profile['map'])

    def start_solo(self):
        p = self.profile
        entries = solo_entries(p.display_name(), p['kart'], int(p['bots']))
        ref = self.solo_map()
        self.start_race(ref, int(p['laps']) if self.test_map is None else int(ref['laps']), entries, False, True,
                        5.0 if self.test_map is None else 3.0, p['mode'] == 'item')

    def use_item(self, slot):
        if self.race is not None and self.race.items is not None and not (self.paused and not self.race.multi):
            self.race.use_item(slot, self.brake_held)

    def start_race(self, map_id, laps, entries, multi, is_host, countdown, items=False):
        self.menu.show(False)
        self.menu.clear_extra()
        self.loading(T('맵 생성 중… ', 'Building map… ') + map_title(map_id, LANG))
        self.destroy_world()
        self.race = Race(map_id, laps, entries, multi=multi, is_host=is_host, countdown=countdown, net=self.session.net if multi else None, items=items)
        self.world = World(self, self.race.track)
        if items:
            self.item_world = ItemWorld(self, self.race, self.world.root)
        self.item_hud.reset()
        self.item_hud.show(items)
        self.hud.set_item_mode(items)
        self.screen_fx.clear()
        self.world_map = None
        self.nodes = {rc.id: KartNode(self, rc, self.world.root) for rc in self.race.racers}
        self.particles = Particles(self)
        wk = self.race.track.theme.get('weather')
        self.weather = Weather(self, wk, self.race.track.theme.get('wcol')) if wk else None
        self.hud.build_minimap(self.race.track)
        self.hud.mapname.setText(map_title(map_id, LANG))
        self.hud.show(True)
        self.chase = ChaseCam()
        self.steer = 0.0
        self.paused = False
        self.finish_at = None
        self.audio.silence()
        self.scene = 'race'
        self.loading_done()
        if items:
            self.hud.say(T('↑ 가속  ← → 조향  Space 드리프트  1·2·3 아이템 (↓ 누른 채 = 뒤로)  R 복귀',
                           'Up gas  Left/Right steer  Space drift  1·2·3 items (hold Down = throw back)  R reset'), 6.0, False, (1, 1, 1, 1))
        else:
            self.hud.say(T('↑ 가속   ← → 조향   Space 드리프트   R 복귀', 'Up gas   Left/Right steer   Space drift   R reset'), 6.0, False, (1, 1, 1, 1))

    def toggle_pause(self):
        if self.race is None or self.scene == 'results':
            return
        self.paused = not self.paused
        if self.paused:
            self.audio.silence()
            rows = [self.R(T('계속하기', 'Resume'), self.toggle_pause, kind='primary', id='resume')]
            if not self.race.multi:
                rows.append(self.R(T('다시 시작', 'Restart'), lambda: (setattr(self, 'paused', False), self.start_solo()), id='restart'))
            rows.append(self.R(T('나가기', 'Quit'), self.leave_race, id='quit'))
            self.menu.show(True)
            self.menu.set(T('일시정지', 'Paused'), rows, '', '')
        else:
            self.menu.show(False)

    def leave_race(self):
        multi = self.race is not None and self.race.multi
        self.race = None
        self.paused = False
        self.audio.silence()
        self.destroy_world()
        if multi:
            self.session.leave()
        if self.test_map is not None:
            self.test_map = None
            if self.maker.ed is not None:
                self.maker.need_cv = True
                self.go('editor')
                return
        self.go('menu')

    def read_input(self, dt):
        k = self.keys
        left = 'arrow_left' in k or 'a' in k
        right = 'arrow_right' in k or 'd' in k
        tgt = (1.0 if right else 0.0) - (1.0 if left else 0.0)
        thr = 1.0 if ('arrow_up' in k or 'w' in k) else 0.0
        brk = 1.0 if ('arrow_down' in k or 's' in k) else 0.0
        drift = 'space' in k or 'lshift' in k or 'rshift' in k
        pad = self.pad
        if pad is not None:
            try:
                ax = pad.findAxis(InputDevice.Axis.left_x).value
                if abs(ax) > 0.12:
                    tgt = ax
                thr = max(thr, pad.findAxis(InputDevice.Axis.right_trigger).value)
                brk = max(brk, pad.findAxis(InputDevice.Axis.left_trigger).value)
                from panda3d.core import GamepadButton
                drift = drift or pad.findButton(GamepadButton.face_a()).pressed or pad.findButton(GamepadButton.rshoulder()).pressed
            except Exception:
                pass
        self.brake_held = brk > 0.5
        self.steer = steer_step(self.steer, tgt, dt, self.profile['steer_resp'])
        return {'steer': self.steer, 'throttle': thr, 'brake': brk, 'drift': drift}

    def handle_events(self, race):
        for ev in race.events:
            kind = ev[0]
            if kind == 'count':
                if ev[1] <= 3:
                    self.audio.play('count')
            elif kind == 'go':
                self.audio.play('go')
                self.hud.say('GO!', 1.0, True)
            elif kind == 'lap':
                self.hud.say('FINAL LAP!' if ev[2] else 'LAP %d' % ev[1], 1.6)
                self.audio.play('lap')
            elif kind == 'finish':
                self.hud.say('FINISH!', 3.0, True)
                self.audio.play('finish')
                self.finish_at = time.time()
            elif kind == 'fin':
                self.hud.say(T('%s 결승!' % ev[1], '%s finished!' % ev[1]), 1.4, False, (0.8, 0.9, 1, 1))
            elif kind == 'left':
                self.hud.say(T('%s 퇴장' % ev[1], '%s left' % ev[1]), 1.4, False, (1, 0.6, 0.6, 1))
            elif kind == 'item':
                self.on_item_event(ev)
            elif kind == 'sim':
                e = ev[1]
                if e in ('pad', 'miniturbo'):
                    self.audio.play('boost')
                    if e == 'pad':
                        self.hud.say('BOOST!', 0.7, False, (0.3, 0.9, 1, 1))
                elif e in ('wall', 'bump'):
                    self.audio.play('bump')
                    self.shake = max(self.shake, 0.6)
                elif e == 'jump':
                    self.audio.play('lap', 0.7)
                    self.hud.say(T('점프!', 'JUMP!'), 0.7, False, (1, 0.88, 0.3, 1))
                elif e == 'oil':
                    self.audio.play('ihit', 0.6)
                    self.hud.say(T('미끌!', 'SLIPPERY!'), 0.8, False, (0.75, 0.6, 1, 1))
                elif e.startswith('tier'):
                    self.audio.play('tier')

    def on_item_event(self, ev):
        what = ev[1]
        if what == 'roll':
            self.audio.play('iroll', 0.5)
        elif what == 'get':
            self.audio.play('iget')
            self.hud.say('%s  ·  %s' % (item_name(ev[2], LANG), item_desc(ev[2], LANG)), 1.8, False, (0.78, 0.92, 1, 1))
        elif what == 'use':
            self.audio.play('iuse', 0.7)
        elif what == 'hit':
            self.audio.play('ihit')
            self.shake = max(self.shake, 0.9)
            self.hud.say(fx_name(ev[2], LANG) + '!', 1.2, True)
        elif what == 'block':
            self.audio.play('iblock')
            self.hud.say(T('방어!', 'BLOCKED!'), 1.0, True)
        elif what == 'score':
            self.hud.say(T('명중! ', 'HIT! ') + str(ev[2]), 1.2, False, (1, 0.86, 0.35, 1))
        elif what == 'stolen':
            self.hud.say(T('아이템을 도둑맞았어요: ', 'Item stolen: ') + item_name(ev[2], LANG), 1.6, False, (1, 0.6, 0.6, 1))

    def burst(self, x, y, z, n, cols, spd, size, life, up=4.0):
        pa = self.particles
        if pa is None:
            return
        for i in range(n):
            a = _random.random() * TAU
            v = spd * (0.4 + _random.random() * 0.6)
            c = cols[i % len(cols)]
            pa.emit(PV(x, y, z), PV(math.cos(a) * v, up * (0.3 + _random.random()), math.sin(a) * v), (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0),
                    size, life * (0.6 + _random.random() * 0.5))

    def item_vfx(self, race, lst):
        loc = race.local
        for v in lst:
            k = v[0]
            if k == 'box':
                self.burst(v[1], v[2], v[3], 14, [hue_rgb(i / 7.0) for i in range(7)], 7.0, 0.45, 0.6)
            elif k == 'boom':
                x, y, z, r, col = v[1], v[2], v[3], v[4], v[5]
                self.burst(x, y + 0.5, z, 36, [(255, 150, 40), (255, 230, 120), (255, 70, 40), col], r * 1.6, 1.0, 0.8, 7.0)
                d = math.hypot(loc.x - x, loc.z - z)
                if d < r * 3.0:
                    self.shake = max(self.shake, 1.0)
                if d < 150:
                    self.audio.play('iboom', clamp(1.0 - d / 160.0, 0.15, 1.0))
            elif k == 'ring':
                x, y, z, r, col = v[1], v[2], v[3], v[4], v[5]
                if self.particles is not None:
                    for i in range(28):
                        a = TAU * i / 28
                        self.particles.emit(PV(x + math.cos(a) * 1.5, y + 0.6, z + math.sin(a) * 1.5), PV(math.cos(a) * r * 2.2, 1.5, math.sin(a) * r * 2.2),
                                            (col[0] / 255.0, col[1] / 255.0, col[2] / 255.0), 0.9, 0.45)
            elif k == 'hit':
                self.burst(v[1], v[2] + 0.8, v[3], 12, [(255, 255, 255), (255, 220, 90)], 6.0, 0.5, 0.5)
            elif k == 'block':
                self.burst(v[1], v[2] + 0.8, v[3], 14, [(120, 220, 255), (255, 255, 255)], 7.0, 0.5, 0.5)
            elif k == 'warp':
                self.burst(v[1], v[2] + 0.8, v[3], 18, [(170, 90, 255), (60, 230, 255)], 5.0, 0.6, 0.7, 6.0)
            elif k == 'pop':
                self.burst(v[1], v[2], v[3], 8, [v[4], (255, 255, 255)], 5.0, 0.45, 0.4)
            elif k == 'area':
                it = ITEMS[v[1]]
                if it['kind'] == 'zap':
                    for rid in v[3]:
                        rc = race._find(rid)
                        if rc is not None and self.particles is not None:
                            c = it['c1']
                            for j in range(10):
                                cc = (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0) if j % 2 else (1, 1, 1)
                                self.particles.emit(PV(rc.x + (_random.random() - 0.5) * 1.2, rc.y + 1.0 + j * 1.4, rc.z + (_random.random() - 0.5) * 1.2),
                                                    (0, 0, 0), cc, 0.8, 0.35)
                    if loc.id in v[3] or it['p'].get('scope') == 'all' or v[2] == loc.id:
                        c = it['c1'] if it['icon'] in ('bolt', 'cloud') else (255, 255, 255)
                        self.screen_fx.flash = 0.32
                        self.screen_fx.flash_col = (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
                        self.audio.play('izap', 0.8)

    def emit_fx(self, race, dt):
        pa = self.particles
        if pa is None:
            return
        th = race.track.theme
        gc = hex_rgb(th['ground'][0])
        loc = race.local
        for rc in race.racers:
            if rc.speed < 4 or abs(rc.x - loc.x) + abs(rc.z - loc.z) > 90:
                continue
            node = self.nodes.get(rc.id)
            if node is None:
                continue
            m = node.model
            fx, fz = math.sin(rc.h), math.cos(rc.h)
            rx, rz = -fz, fx
            L, W = m.L, m.W
            if rc.drifting:
                col = [(0.67, 0.8, 1), (0.23, 0.67, 1), (1, 0.63, 0.16), (0.82, 0.31, 1)][min(3, rc.tier)]
                for s_ in (-1, 1):
                    if _random.random() < 0.8:
                        pa.emit(PV(rc.x - fx * L * 0.4 + rx * s_ * W * 0.5, rc.y + 0.25, rc.z - fz * L * 0.4 + rz * s_ * W * 0.5),
                                PV((_random.random() - 0.5) * 5 - fx * 3, 2 + _random.random() * 4, (_random.random() - 0.5) * 5 - fz * 3), col, 0.35, 0.4 + _random.random() * 0.25)
            if rc.boosting and _random.random() < 0.9:
                pa.emit(PV(rc.x - fx * (L * 0.5 + 0.6), rc.y + 0.6, rc.z - fz * (L * 0.5 + 0.6)),
                        PV(-fx * 9 + (_random.random() - 0.5) * 2, _random.random() * 2, -fz * 9 + (_random.random() - 0.5) * 2), (1, 0.6, 0.15), 0.6, 0.3)
            if rc.offroad and _random.random() < 0.5:
                pa.emit(PV(rc.x - fx * 1.2 + (_random.random() - 0.5) * 2, rc.y + 0.2, rc.z - fz * 1.2 + (_random.random() - 0.5) * 2),
                        PV((_random.random() - 0.5) * 3, 1 + _random.random() * 2, (_random.random() - 0.5) * 3), (gc[0] / 255.0, gc[1] / 255.0, gc[2] / 255.0), 0.9, 0.5)
            if rc.wall_hit > 0.6:
                side = 1.0 if (race.track.rx[rc.idx % race.track.N] * rx + race.track.rz[rc.idx % race.track.N] * rz) > 0 else -1.0
                for _ in range(2):
                    pa.emit(PV(rc.x + rx * side * 1.3, rc.y + 0.6, rc.z + rz * side * 1.3), PV((_random.random() - 0.5) * 8, 2 + _random.random() * 5, (_random.random() - 0.5) * 8), (1, 0.85, 0.35), 0.3, 0.4)

    def update_race(self, dt):
        race = self.race
        inp = self.read_input(dt)
        if race.multi:
            for m in self.session.pump():
                if m.get('t') == 'tolobby':
                    self.leave_to_lobby()
                    return
                race.handle_message(m)
            if self.session.state == 'idle':
                err = self.session.error
                self.race = None
                self.destroy_world()
                self.go('menu')
                self.err = err
                self.build_main()
                return
        if not self.paused or race.multi:
            race.update(dt, inp)
            self.handle_events(race)
            self.emit_fx(race, dt)
            if race.items is not None:
                self.item_vfx(race, race.items.take_vfx())
        loc = race.local
        sim = loc.sim
        # 카트 노드 동기화
        alive = set()
        for rc in race.racers:
            alive.add(rc.id)
            node = self.nodes.get(rc.id)
            if node is None:
                node = self.nodes[rc.id] = KartNode(self, rc, self.world.root)
            node.update(rc, dt, race.track.ds, math.hypot(rc.x - loc.x, rc.z - loc.z))
        for rid in [r for r in self.nodes if r not in alive]:
            self.nodes.pop(rid).destroy()
        # 카메라
        cp = self.chase.update(dt, loc, sim.stats['max_speed'])
        self.shake = max(0.0, self.shake - dt * 2.2)
        sh = self.shake * 0.25 + (0.05 if loc.boosting else 0.0)
        pos = PV(cp[0] + (_random.random() - 0.5) * sh, cp[1] + (_random.random() - 0.5) * sh, cp[2] + (_random.random() - 0.5) * sh)
        yaw, pitch = cp[3], cp[4]
        d = PV(math.sin(yaw) * math.cos(pitch), -math.sin(pitch), math.cos(yaw) * math.cos(pitch))
        self.camera.setPos(*pos)
        self.camera.lookAt(Point3(pos[0] + d[0] * 20, pos[1] + d[1] * 20, pos[2] + d[2] * 20), Vec3(0, 0, 1))
        self.cam_pos, self.cam_fwd = pos, d          # 카메라 뒤 물체 갱신 생략용
        ratio = loc.speed / sim.stats['max_speed']
        self.camLens.setFov(82 + clamp(ratio, 0, 1.2) * 8 + (6 if loc.boosting else 0))
        self.world.update(pos)
        if self.particles is not None:
            self.particles.update(dt if not self.paused else 0.0)
        if self.weather is not None:
            self.weather.update(dt, pos)
        self.hud.update(race, time.time())
        if race.items is not None:
            if self.item_world is not None:
                self.item_world.update(dt)
            self.item_hud.update(race, self.t)
            self.screen_fx.update(sim.blind_t, dt)
        self._fps_t = getattr(self, '_fps_t', 0.0) + dt
        if self._fps_t > 0.25:
            self._fps_t = 0.0
            self.hud._set(self.hud.fps, ('%d fps' % int(1.0 / max(dt, 1e-3))) if self.show_fps else '')
        if not self.paused:
            self.audio.engine(ratio, 1.0 if inp['throttle'] > 0 else 0.2, loc.drifting, loc.offroad)
        # 결과 화면
        if self.scene == 'race' and race.local_finished() and self.finish_at and time.time() - self.finish_at > 2.4:
            self.scene = 'results'
            self.build_results()
        elif self.scene == 'results':
            self._res_t = getattr(self, '_res_t', 0.0) + dt
            if self._res_t > 0.5:
                self._res_t = 0.0
                self.build_results()

    def build_results(self):
        race = self.race
        rows = []
        for i, rc in enumerate(race.ranking()):
            me = rc is race.local
            rows.append(self.I('%2d  %-14s %s' % (i + 1, rc.name, fmt_time(rc.finish_time) if rc.finished else T('주행 중…', 'racing…')), (1, 0.72, 0.15, 1) if me else (0.95, 0.97, 1, 1), 0.052))
        if race.multi:
            if self.session.is_host:
                rows.append(self.R(T('로비로 돌아가기', 'Back to lobby'), self.session.back_to_lobby, kind='primary', id='lobby'))
            else:
                rows.append(self.I(T('방장을 기다리는 중…', 'Waiting for the host…')))
        else:
            rows.append(self.R(T('다시 달리기', 'Race again'), self.start_solo, kind='primary', id='again'))
        rows.append(self.R(T('메뉴로', 'Menu'), self.leave_race, id='menu'))
        self.menu.show(True)
        self.menu.set(T('결과', 'Results'), rows, '', '')

    def leave_to_lobby(self):
        self.race = None
        self.paused = False
        self.audio.silence()
        self.destroy_world()
        self.go('lobby')

    # ------------------------------------------------------------------ 메인 틱
    def tick(self, task):
        dt = self.dt_override if self.dt_override is not None else min(ClockObject.getGlobalClock().getDt(), 0.1)
        self.t += dt
        self.input.tick(dt)
        sc = self.scene
        if sc in ('multi',) and self.scan.get('done'):
            self.scan['done'] = False
            self.build_multi()
        if sc == 'editor':
            self.maker.update(dt)
            return task.cont
        if sc in ('lobby', 'multi', 'menu', 'solo', 'garage', 'settings', 'maps', 'mapitem') or (sc == 'race' and self.race is None):
            if self.session.net is not None and sc == 'lobby':
                self.session.pump()
                if self.session.start_msg is not None:
                    msg = self.session.start_msg
                    self.session.start_msg = None
                    entries = self.session.entries_from_start(msg)
                    ref = msg.get('cmap') or int(msg['map'])
                    self.start_race(ref, int(msg['laps']), entries, True, self.session.is_host, float(msg.get('countdown', 5.0)), bool(msg.get('items')))
                    return task.cont
                if self.session.state == 'idle':
                    self.err = self.session.error or T('연결 실패', 'Connection failed')
                    self.go('multi')
                    self.build_multi()
                    return task.cont
                sig = (self.session.state, tuple((p['id'], p['name']) for p in self.session.players), self.session.host_id, tuple(sorted(self.session.settings.items())))
                if sig != getattr(self, '_lobby_sig', None):
                    self._lobby_sig = sig
                    self.build_lobby()
            self.update_showroom(dt)
        elif sc in ('race', 'results') and self.race is not None:
            self.update_race(dt)
        return task.cont
