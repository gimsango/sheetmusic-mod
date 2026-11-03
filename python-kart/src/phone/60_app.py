
# ============================================================================
#  [폰] 앱: 화면(메뉴/솔로/차고/설정/멀티/로비/레이스/결과) + 메인 루프
# ============================================================================
def R(x, y, w, h):
    return pygame.Rect(int(x), int(y), int(w), int(h))


ITEM_KEYS = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
for _n, _slot in (('K_KP1', 0), ('K_KP2', 1), ('K_KP3', 2), ('K_KP_1', 0), ('K_KP_2', 1), ('K_KP_3', 2)):
    if hasattr(pygame, _n):
        ITEM_KEYS[getattr(pygame, _n)] = _slot


class ShowKart(object):
    """쇼룸(메뉴/차고 배경)에서 돌아가는 카트용 가짜 Racer + 가짜 Race"""

    def __init__(self, track, kart_id):
        rc = Racer('show', '', kart_id, 0, 'bot')
        pf = track.N - 9.0
        x, y, z, h = track.pose_at(pf, 0.0)
        rc.x, rc.y, rc.z, rc.h = x, y, z, h
        rc.idx = int(pf) % track.N
        rc.up = track.surface_normal(rc.idx)
        rc.total = 0.0
        self.rc = rc
        self.racers = [rc]
        self.local = None


class App(object):
    def __init__(self, args):
        global LANG
        self.args = args
        try:
            pygame.mixer.pre_init(22050, -16, 1, 512)
        except Exception:
            pass
        pygame.init()
        try:
            if args.get('window'):
                w, h = args['window']
                self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
            else:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        except Exception:
            self.screen = pygame.display.set_mode((960, 540))
        if self.screen.get_width() < 200 or self.screen.get_height() < 200:
            self.screen = pygame.display.set_mode((960, 540))
        pygame.display.set_caption('TURBO KART 3D')
        self.W, self.H = self.screen.get_size()
        self.profile = Profile()
        self.font_path = find_korean_font()
        lang = args.get('lang') or self.profile['lang']
        if lang == 'auto':
            lang = 'ko' if self.font_path else 'en'
        LANG = lang
        self.ui = UI(self.font_path)
        self.ptr = Pointers()
        self.sfx = Sfx(self.profile['sound'])
        self.session = Session(self.profile)
        self.renderer = Renderer(self.W, self.H, int(self.profile['quality']))
        self.renderer.set_qmark_font(self.font_path)
        self.icons = ItemIcons()
        self.sfx_screen = ScreenFx()
        self.hud_top = 0
        self.brake_held = False
        self.item_rects = []
        self.cam = ChaseCam()
        self.touch = TouchControls()
        self.touch.layout(self.W, self.H, self.profile['auto_gas'])
        self.clock = pygame.time.Clock()
        self.scene = 'menu'
        self.race = None
        self.kb = None
        self.toasts = []
        self.mini = None
        self.keys = set()
        self.used_keyboard = False
        self.used_gas_key = False
        self.steer = 0.0
        self.dirn = 1
        self.paused = False
        self.running = True
        self.t = 0.0
        self.show = None
        self.show_map = None
        self.show_kart = None
        self.outline_cache = {}
        self.scan = {'busy': False, 'rooms': [], 'done': False}
        self.err = ''
        self.sel_map = int(self.profile['map'])
        self.fps_ema = 60.0
        self.show_fps = bool(args.get('fps'))
        self.finish_at = None
        self.ping = 0.0
        self.store = MapStore()           # 내가 만든 맵 목록
        self.maker = PhoneMapMaker(self)  # 맵 만들기 화면
        self.test_map = None              # 편집기에서 '시험 주행' 중인 맵

    # ------------------------------------------------------------------ 공통 도우미
    @property
    def landscape(self):
        return self.W >= self.H * 1.15

    def toast(self, text, dur=1.4, color=(255, 200, 70), big=False):
        self.toasts.append((text, time.time() + dur, color, big))

    def loading(self, msg):
        self.screen.fill((8, 12, 26))
        self.ui.text(self.screen, msg, self.W // 2, self.H // 2 - 20 * self.ui.u, 40 * self.ui.u, (255, 255, 255), 'c')
        pygame.display.flip()
        pygame.event.pump()

    def present(self, surf):
        try:
            if surf.get_size() == (self.W, self.H):
                self.screen.blit(surf, (0, 0))
            else:
                pygame.transform.scale(surf, (self.W, self.H), self.screen)
        except Exception:
            self.screen.blit(pygame.transform.scale(surf, (self.W, self.H)), (0, 0))

    def on_resize(self):
        self.W, self.H = self.screen.get_size()
        self.renderer.set_quality(self.renderer.q, self.W, self.H)
        self.touch.layout(self.W, self.H, self.profile['auto_gas'])
        self.mini = None
        self.show_map = None

    def set_quality(self, q):
        self.profile['quality'] = q
        self.profile.save()
        self.renderer.set_quality(q, self.W, self.H)

    def go(self, scene):
        self.scene = scene
        self.err = ''
        self.sfx.play('click', 0.6)
        if scene == 'solo':
            self.sel_map = int(self.profile['map'])
        if scene == 'multi':
            self.scan_rooms()

    def map_text(self, mid):
        i = map_info(mid)
        return (i['name'], i['theme_name']) if LANG == 'ko' else (i['name_en'], i['theme_en'])

    # ------------------------------------------------------------------ 쇼룸(3D 배경)
    def ensure_show(self, kart_id):
        mid = int(self.profile['map'])
        if self.show_map != mid or self.show is None:
            self.loading(T('준비 중…', 'Preparing…'))
            tr = Track(mid)
            self.renderer.set_track(tr)
            self.show_map = mid
            self.show = ShowKart(tr, kart_id)
            self.show_kart = kart_id
        if self.show_kart != kart_id:
            self.show.rc.kart_id = kart_id
            self.show_kart = kart_id

    def draw_show(self, dt, kart_id, shift=0.0, dist=6.3):
        self.ensure_show(kart_id)
        rc = self.show.rc
        tr = self.renderer.track
        rc.total += dt * 8.0
        th = self.t * 0.5
        cx, cy, cz = rc.x, rc.y + 0.9, rc.z
        camx, camz = cx + math.sin(th) * dist, cz + math.cos(th) * dist
        camy = cy + 1.5
        yaw = math.atan2(cx - camx, cz - camz) + shift
        pitch = math.atan2(camy - cy, math.hypot(cx - camx, cz - camz))
        dot = math.sin(yaw) * tr.tx[rc.idx] + math.cos(yaw) * tr.tz[rc.idx]
        dirn = 1 if dot >= 0 else -1
        surf = self.renderer.render(self.show, (camx, camy, camz, yaw, pitch), rc.idx, dirn, 0.0, 0.0, self.t)
        self.present(surf)

    # ------------------------------------------------------------------ 입력
    def pump_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if self.kb is not None:
                    r = self.kb.handle_key_event(e)
                    if r:
                        self.close_kb(r)
                    continue
                self.keys.add(e.key)
                if e.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE) or e.key in ITEM_KEYS:
                    self.used_keyboard = True
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.used_gas_key = True          # 가속 키를 눌러 본 뒤부터 '직접 가속' (조향 키만으로는 바뀌지 않음)
                if e.key in (pygame.K_ESCAPE, getattr(pygame, 'K_AC_BACK', -999)):
                    self.on_back()
                elif self.scene == 'race':
                    if e.key in ITEM_KEYS:
                        self.use_item(ITEM_KEYS[e.key])
                    elif e.key == pygame.K_r and self.race:
                        self.race.respawn_local()
                    elif e.key == pygame.K_m:
                        self.sfx.enabled = not self.sfx.enabled
                        self.toast(T('소리 켬', 'Sound on') if self.sfx.enabled else T('소리 끔', 'Sound off'), 0.8)
                        if not self.sfx.enabled:
                            self.sfx.silence()
            elif e.type == pygame.KEYUP:
                self.keys.discard(e.key)
            elif e.type == getattr(pygame, 'VIDEORESIZE', -1):
                pass
            elif self.scene == 'editor' and e.type == getattr(pygame, 'MOUSEWHEEL', -1):
                self.maker.wheel += e.y
            elif self.scene == 'editor' and e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and getattr(e, 'button', 1) in (2, 3, 4, 5):
                if e.button in (2, 3):
                    self.maker.rdrag = e.pos if e.type == pygame.MOUSEBUTTONDOWN else None
            elif self.scene == 'editor' and e.type == pygame.MOUSEMOTION and self.maker.rdrag is not None:
                a = self.maker.rdrag
                if self.maker.view is not None:
                    self.maker.pan(e.pos[0] - a[0], e.pos[1] - a[1])
                self.maker.rdrag = e.pos
            else:
                self.ptr.handle(e, self.W, self.H)
        if self.screen.get_size() != (self.W, self.H):
            self.on_resize()

    def on_back(self):
        if self.kb is not None:
            self.close_kb('cancel')
        elif self.scene == 'race':
            self.toggle_pause()
        elif self.scene == 'results':
            self.leave_race()
        elif self.scene in ('solo', 'garage', 'settings', 'multi', 'maps'):
            self.profile.save()
            self.go('menu')
        elif self.scene == 'editor':
            self.maker.on_back()
        elif self.scene == 'lobby':
            self.session.leave()
            self.go('menu')
        elif self.scene == 'menu':
            self.running = False

    def open_kb(self, title, text, mode, maxlen, cb):
        self.kb = OnScreenKeyboard(title, text, mode, maxlen, cb)

    def close_kb(self, result):
        kb = self.kb
        self.kb = None
        if result == 'ok' and kb is not None:
            kb.on_ok(kb.text)

    def touch_visible(self):
        """화면 버튼은 터치 기기(또는 키보드를 아직 안 쓴 경우)에서만 보인다"""
        return _is_android() or self.ptr.has_touch or not self.used_keyboard

    def read_input(self, dt):
        k = self.keys
        pressed = self.touch.read(self.ptr.down()) if self.touch_visible() else set()
        left = pygame.K_LEFT in k or pygame.K_a in k or 'left' in pressed
        right = pygame.K_RIGHT in k or pygame.K_d in k or 'right' in pressed
        tgt = (1.0 if right else 0.0) - (1.0 if left else 0.0)
        brake = pygame.K_DOWN in k or pygame.K_s in k or 'brake' in pressed
        gas = pygame.K_UP in k or pygame.K_w in k or 'gas' in pressed
        auto = self.profile['auto_gas'] and not self.used_gas_key
        drift = pygame.K_SPACE in k or pygame.K_LSHIFT in k or pygame.K_RSHIFT in k or 'drift' in pressed
        self.brake_held = brake
        self.steer = steer_step(self.steer, tgt, dt, self.profile['steer_resp'])
        return {'steer': self.steer, 'throttle': 1.0 if (gas or (auto and not brake)) else 0.0, 'brake': 1.0 if brake else 0.0, 'drift': drift}, pressed

    # ------------------------------------------------------------------ 레이스
    def solo_map(self):
        """솔로로 달릴 맵: 시험 주행 중이면 그 맵, '내 맵' 을 골랐으면 그 데이터, 아니면 기본 맵 번호"""
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
        self.loading(T('맵 생성 중…', 'Building map…') + ' ' + map_title(map_id, LANG))
        self.race = Race(map_id, laps, entries, multi=multi, is_host=is_host, countdown=countdown, net=self.session.net if multi else None, items=items)
        self.hud_top = 0
        self.renderer.set_track(self.race.track)
        self.show_map = None
        self.cam.reset()
        self.mini = None
        self.toasts = []
        self.paused = False
        self.finish_at = None
        self.touch.layout(self.W, self.H, self.profile['auto_gas'])
        self.sfx.silence()
        self.steer = 0.0
        self.dirn = 1
        self.scene = 'race'
        if not self.touch_visible() or not (_is_android() or self.ptr.has_touch):
            if items:
                self.toast(T('← → 조향  ↑ 가속  Space 드리프트  1·2·3 아이템 (↓ 누른 채 = 뒤로)  R 복귀',
                             'Steer ←→  Gas ↑  Drift Space  Items 1·2·3 (hold ↓ = throw back)  R reset'), 6.0, (255, 255, 255))
            else:
                self.toast(T('← → 조향   ↑ 가속   Space 드리프트   R 복귀', 'Left/Right steer   Up gas   Space drift   R reset'), 6.0, (255, 255, 255))
        elif items:
            self.toast(T('위쪽 아이템 칸을 눌러서 사용!', 'Tap the item slots at the top!'), 5.0, (255, 255, 255))

    def toggle_pause(self):
        if self.race is None:
            return
        if self.race.multi:
            self.paused = not self.paused          # 멀티: 메뉴만 열리고 레이스는 계속
            return
        self.paused = not self.paused
        if self.paused:
            self.sfx.silence()

    def leave_race(self):
        multi = self.race is not None and self.race.multi
        self.race = None
        self.paused = False
        self.sfx.silence()
        self.show_map = None
        if multi:
            self.session.leave()
        if self.test_map is not None:
            self.test_map = None
            if self.maker.ed is not None:
                self.maker.changed()
                self.go('editor')
                return
        self.go('menu')

    def handle_race_events(self, race):
        for ev in race.events:
            kind = ev[0]
            if kind == 'count':
                if ev[1] <= 3:
                    self.sfx.play('count')
            elif kind == 'go':
                self.sfx.play('go')
                self.toast('GO!', 1.0, (255, 255, 255), True)
            elif kind == 'lap':
                self.toast('FINAL LAP!' if ev[2] else 'LAP %d' % ev[1], 1.6, (255, 220, 90), True)
                self.sfx.play('lap')
            elif kind == 'finish':
                self.toast('FINISH!', 3.0, (255, 255, 255), True)
                self.sfx.play('finish')
                self.finish_at = time.time()
            elif kind == 'fin':
                self.toast(T('%s 결승!' % ev[1], '%s finished!' % ev[1]), 1.4, (200, 230, 255))
            elif kind == 'left':
                self.toast(T('%s 퇴장' % ev[1], '%s left' % ev[1]), 1.4, (255, 150, 150))
            elif kind == 'item':
                self.on_item_event(ev)
            elif kind == 'sim':
                e = ev[1]
                if e in ('pad', 'miniturbo'):
                    self.sfx.play('boost')
                    if e == 'pad':
                        self.toast('BOOST!', 0.7, (80, 230, 255))
                elif e in ('wall', 'bump'):
                    self.sfx.play('bump')
                    self.renderer.shake = max(self.renderer.shake, 0.6)
                elif e == 'jump':
                    self.sfx.play('lap', 0.7)
                    self.toast(T('점프!', 'JUMP!'), 0.7, (255, 225, 80))
                elif e == 'oil':
                    self.sfx.play('ihit', 0.6)
                    self.toast(T('미끌!', 'SLIPPERY!'), 0.8, (190, 150, 255))
                elif e.startswith('tier'):
                    self.sfx.play('tier')

    def on_item_event(self, ev):
        what = ev[1]
        if what == 'roll':
            self.sfx.play('iroll', 0.5)
        elif what == 'get':
            self.sfx.play('iget')
            self.toast('%s  ·  %s' % (item_name(ev[2], LANG), item_desc(ev[2], LANG)), 1.8, (200, 235, 255))
        elif what == 'use':
            self.sfx.play('iuse', 0.7)
        elif what == 'hit':
            self.sfx.play('ihit')
            self.renderer.shake = max(self.renderer.shake, 0.9)
            self.toast(fx_name(ev[2], LANG) + '!', 1.2, (255, 110, 110), True)
        elif what == 'block':
            self.sfx.play('iblock')
            self.toast(T('방어!', 'BLOCKED!'), 1.0, (120, 220, 255), True)
        elif what == 'score':
            self.toast(T('명중! ', 'HIT! ') + str(ev[2]), 1.2, (255, 220, 90))
        elif what == 'stolen':
            self.toast(T('아이템을 도둑맞았어요: ', 'Item stolen: ') + item_name(ev[2], LANG), 1.6, (255, 150, 150))

    def burst(self, x, y, z, n, cols, spd, size, life, up=4.0):
        rd = self.renderer
        for i in range(n):
            a = _random.random() * TAU
            v = spd * (0.4 + _random.random() * 0.6)
            rd.emit(x, y, z, math.cos(a) * v, up * (0.3 + _random.random()), math.sin(a) * v, cols[i % len(cols)], size, life * (0.6 + _random.random() * 0.5))

    def item_vfx(self, race, lst):
        loc = race.local
        for v in lst:
            k = v[0]
            if k == 'box':
                self.burst(v[1], v[2], v[3], 14, [hue_rgb(i / 7.0) for i in range(7)], 7.0, 0.22, 0.6)
            elif k == 'boom':
                x, y, z, r, col = v[1], v[2], v[3], v[4], v[5]
                self.burst(x, y + 0.5, z, 34, [(255, 150, 40), (255, 230, 120), (255, 70, 40), col], r * 1.6, 0.45, 0.8, 7.0)
                d = math.hypot(loc.x - x, loc.z - z)
                if d < r * 3.0:
                    self.renderer.shake = max(self.renderer.shake, 1.0)
                if d < 150:
                    self.sfx.play('iboom', clamp(1.0 - d / 160.0, 0.15, 1.0))
            elif k == 'ring':
                x, y, z, r, col = v[1], v[2], v[3], v[4], v[5]
                for i in range(26):
                    a = TAU * i / 26
                    self.renderer.emit(x + math.cos(a) * 1.5, y + 0.6, z + math.sin(a) * 1.5, math.cos(a) * r * 2.2, 1.5, math.sin(a) * r * 2.2, col, 0.4, 0.45)
            elif k == 'hit':
                self.burst(v[1], v[2] + 0.8, v[3], 12, [(255, 255, 255), (255, 220, 90)], 6.0, 0.22, 0.5)
            elif k == 'block':
                self.burst(v[1], v[2] + 0.8, v[3], 14, [(120, 220, 255), (255, 255, 255)], 7.0, 0.22, 0.5)
            elif k == 'warp':
                self.burst(v[1], v[2] + 0.8, v[3], 18, [(170, 90, 255), (60, 230, 255)], 5.0, 0.28, 0.7, 6.0)
            elif k == 'pop':
                self.burst(v[1], v[2], v[3], 8, [v[4], (255, 255, 255)], 5.0, 0.2, 0.4)
            elif k == 'area':
                it = ITEMS[v[1]]
                if it['kind'] == 'zap':
                    for rid in v[3]:
                        rc = race._find(rid)
                        if rc is not None:
                            for j in range(9):
                                self.renderer.emit(rc.x + (_random.random() - 0.5) * 1.2, rc.y + 1.0 + j * 1.4, rc.z + (_random.random() - 0.5) * 1.2,
                                                   0.0, 0.0, 0.0, it['c1'] if j % 2 else (255, 255, 255), 0.35, 0.35)
                    if loc.id in v[3] or it['p'].get('scope') == 'all' or v[2] == loc.id:
                        self.sfx_screen.flash = 0.32
                        self.sfx_screen.flash_col = it['c1'] if it['icon'] in ('bolt', 'cloud') else (255, 255, 255)
                        self.sfx.play('izap', 0.8)

    def emit_fx(self, race, dt):
        rd = self.renderer
        th = race.track.theme
        gc = hex_rgb(th['ground'][0])
        loc = race.local
        for rc in race.racers:
            if rc.speed < 4:
                continue
            if abs(rc.x - loc.x) + abs(rc.z - loc.z) > 90:
                continue
            m = rd.model(rc.kart_id)
            fx, fz = math.sin(rc.h), math.cos(rc.h)
            rx, rz = -fz, fx
            L, W = m.L, m.W
            if rc.drifting:
                col = [(170, 200, 255), (60, 170, 255), (255, 160, 40), (210, 80, 255)][min(3, rc.tier)]
                for s_ in (-1, 1):
                    if _random.random() < 0.75:
                        rd.emit(rc.x - fx * L * 0.4 + rx * s_ * W * 0.5, rc.y + 0.25, rc.z - fz * L * 0.4 + rz * s_ * W * 0.5,
                                (_random.random() - 0.5) * 5 - fx * 3, 2 + _random.random() * 4, (_random.random() - 0.5) * 5 - fz * 3, col, 0.18, 0.35 + _random.random() * 0.25)
            if rc.boosting and _random.random() < 0.9:
                rd.emit(rc.x - fx * (L * 0.5 + 0.6), rc.y + 0.6, rc.z - fz * (L * 0.5 + 0.6), -fx * 9 + (_random.random() - 0.5) * 2, _random.random() * 2,
                        -fz * 9 + (_random.random() - 0.5) * 2, (255, 150, 40), 0.3, 0.3)
            if rc.offroad and _random.random() < 0.5:
                rd.emit(rc.x - fx * 1.2 + (_random.random() - 0.5) * 2, rc.y + 0.2, rc.z - fz * 1.2 + (_random.random() - 0.5) * 2,
                        (_random.random() - 0.5) * 3, 1 + _random.random() * 2, (_random.random() - 0.5) * 3, shade_rgb(gc, 1.2), 0.4, 0.5)
            if rc.wall_hit > 0.6:
                side = 1.0 if rc.idx is not None and race.track.rx[rc.idx % race.track.N] * rx + race.track.rz[rc.idx % race.track.N] * rz > 0 else -1.0
                for _ in range(2):
                    rd.emit(rc.x + rx * side * 1.3, rc.y + 0.6, rc.z + rz * side * 1.3, (_random.random() - 0.5) * 8, 2 + _random.random() * 5,
                            (_random.random() - 0.5) * 8, (255, 215, 90), 0.15, 0.4)

    def update_race(self, dt):
        race = self.race
        inp, pressed = self.read_input(dt)
        self.pressed = pressed
        if race.multi:
            for m in self.session.pump():
                if m.get('t') == 'tolobby':
                    self.race = None
                    self.show_map = None
                    self.go('lobby')
                    return
                race.handle_message(m)
            if self.session.state == 'idle':          # 서버 연결 끊김
                err = self.session.error
                self.race = None
                self.go('menu')
                self.err = err
                return
        if not self.paused or race.multi:
            race.update(dt, inp)
            self.handle_race_events(race)
            self.emit_fx(race, dt)
            if race.items is not None:
                self.item_vfx(race, race.items.take_vfx())
        loc = race.local
        sim = loc.sim
        self.renderer.update_particles(dt if not self.paused else 0.0)
        cp = self.cam.update(dt, loc, sim.stats['max_speed'])
        self.renderer.shake = max(0.0, self.renderer.shake - dt * 2.2)
        sh = self.renderer.shake * 0.25 + (0.05 if loc.boosting else 0.0)
        if sh > 0.01:
            cp = (cp[0] + (_random.random() - 0.5) * sh, cp[1] + (_random.random() - 0.5) * sh, cp[2] + (_random.random() - 0.5) * sh, cp[3], cp[4])
        tr = race.track
        i0 = loc.idx
        dot = math.sin(cp[3]) * tr.tx[i0] + math.cos(cp[3]) * tr.tz[i0]
        if dot < -0.35:
            self.dirn = -1
        elif dot > 0.35:
            self.dirn = 1
        ratio = loc.speed / sim.stats['max_speed']
        surf = self.renderer.render(race, cp, i0, self.dirn, 1.0 if loc.boosting else 0.0, ratio, self.t)
        self.present(surf)
        self.draw_labels()
        if not self.paused:
            self.sfx.engine(clamp(ratio, 0, 1.3), 1.0 if inp['throttle'] > 0 else 0.2, loc.boosting, loc.drifting, loc.offroad)
        # 프레임 측정 (표시용 - 화질/해상도는 절대 자동으로 낮추지 않는다)
        self.fps_ema += (1.0 / max(dt, 1e-3) - self.fps_ema) * 0.05

    def draw_labels(self):
        rd = self.renderer
        sx = self.W / float(rd.rw)
        sy = self.H / float(rd.rh)
        for (x, y, text, color, dp) in rd.labels:
            size = clamp(260.0 / dp, 11, 26) * self.ui.u
            self.ui.text(self.screen, text, int(x * sx), int(y * sy), size, color, 'c')

    def draw_race_ui(self, dt):
        race = self.race
        ui = self.ui
        u = ui.u
        if race.local is not None and race.local.sim is not None:
            self.sfx_screen.draw(self.screen, self.W, self.H, race.local.sim.blind_t if race.items is not None else 0.0, dt)
        if race.items is not None:
            self.item_rects = draw_item_bar(self, self.screen, race)
            for i, r in enumerate(self.item_rects):
                if ui.tapped(r.inflate(int(10 * u), int(10 * u))):
                    self.use_item(i)
        else:
            self.hud_top = 0
        draw_hud(self, self.screen, race, dt)
        if self.touch_visible():
            self.touch.draw(self.screen, ui, self.pressed)
        if race.items is not None and self.landscape:
            r3 = self.item_rects[-1]
            pb = R(r3.right + 12 * u, 8 * u, 44 * u, 40 * u)
        else:
            pb = R(self.W // 2 - 22 * u, 8 * u, 44 * u, 40 * u)
        if ui.button(self.screen, pb, 'II', 'ghost', size=22 * u):
            self.toggle_pause()
        if self.paused:
            self.draw_pause()
        elif race.local_finished() and self.finish_at and time.time() - self.finish_at > 2.4:
            self.scene = 'results'
        if self.show_fps:
            ui.text(self.screen, '%d fps  q%d  %dx%d' % (self.fps_ema, self.renderer.q, self.renderer.rw, self.renderer.rh), 8, self.H - 22 * u, 16 * u, (255, 255, 0))

    def draw_pause(self):
        ui = self.ui
        u = ui.u
        surf = self.screen
        veil = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 150))
        surf.blit(veil, (0, 0))
        pw, ph = int(min(self.W * 0.8, 460 * u)), int(300 * u)
        r = R((self.W - pw) // 2, (self.H - ph) // 2, pw, ph)
        ui.panel(surf, r, 235)
        ui.text(surf, T('일시정지', 'Paused'), r.centerx, r.y + 16 * u, 36 * u, (255, 255, 255), 'c')
        bh = 58 * u
        if ui.button(surf, R(r.x + 24 * u, r.y + 74 * u, r.w - 48 * u, bh), T('계속하기', 'Resume'), 'primary'):
            self.toggle_pause()
        if not self.race.multi:
            if ui.button(surf, R(r.x + 24 * u, r.y + 74 * u + (bh + 12 * u), r.w - 48 * u, bh), T('다시 시작', 'Restart'), 'normal'):
                self.paused = False
                self.start_solo()
                return
        if ui.button(surf, R(r.x + 24 * u, r.y + 74 * u + 2 * (bh + 12 * u), r.w - 48 * u, bh), T('나가기', 'Quit'), 'danger'):
            self.leave_race()

    def draw_results(self, dt):
        ui = self.ui
        u = ui.u
        surf = self.screen
        race = self.race
        veil = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 140))
        surf.blit(veil, (0, 0))
        pw = int(min(self.W * 0.92, 680 * u))
        ph = int(min(self.H * 0.94, 520 * u))
        r = R((self.W - pw) // 2, (self.H - ph) // 2, pw, ph)
        ui.panel(surf, r, 235)
        ui.text(surf, T('결과', 'Results'), r.centerx, r.y + 12 * u, 36 * u, (255, 215, 90), 'c')
        rank = race.ranking()
        rh = min(34 * u, (ph - 150 * u) / max(1, len(rank)))
        y = r.y + 62 * u
        for i, rc in enumerate(rank):
            row = R(r.x + 18 * u, y, r.w - 36 * u, rh - 3 * u)
            me = rc is race.local
            ui.panel(surf, row, 200 if me else 90, (255, 176, 32) if me else (255, 255, 255), 8)
            tc = (20, 20, 20) if me else (255, 255, 255)
            fs = rh * 0.62
            ui.text(surf, str(i + 1), row.x + 10 * u, row.y + rh * 0.08, fs, tc, shadow=False)
            ui.text(surf, '%s  (%s)' % (rc.name, kart_name(rc.kart_id, LANG)), row.x + 48 * u, row.y + rh * 0.08, fs, tc, shadow=False)
            ui.text(surf, fmt_time(rc.finish_time) if rc.finished else T('주행 중…', 'racing…'), row.right - 10 * u, row.y + rh * 0.08, fs, tc, 'r', shadow=False)
            y += rh
        by = r.bottom - 66 * u
        if ui.button(surf, R(r.x + 18 * u, by, r.w * 0.4, 52 * u), T('메뉴로', 'Menu'), 'ghost'):
            self.leave_race()
            return
        if race.multi:
            if self.session.is_host:
                if ui.button(surf, R(r.right - 18 * u - r.w * 0.5, by, r.w * 0.5, 52 * u), T('로비로 돌아가기', 'Back to lobby'), 'primary'):
                    self.session.back_to_lobby()
            else:
                ui.text(surf, T('방장을 기다리는 중…', 'Waiting for host…'), r.right - 18 * u, by + 12 * u, 22 * u, (190, 205, 240), 'r')
        else:
            if ui.button(surf, R(r.right - 18 * u - r.w * 0.5, by, r.w * 0.5, 52 * u), T('다시 달리기', 'Race again'), 'primary'):
                self.start_solo()

    # ------------------------------------------------------------------ 맵 선택기
    def outline(self, mid, w, h):
        key = (mid if not isinstance(mid, dict) else ('c', cmap_key(mid)), w, h)
        hit = self.outline_cache.get(key)
        if hit is not None:
            return hit
        if len(self.outline_cache) > 24:
            self.outline_cache.clear()
        tr = Track(mid, True)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        b = tr.bounds
        span_x, span_z = max(b[1] - b[0], 1.0), max(b[3] - b[2], 1.0)
        sc = min((w - 24) / span_x, (h - 24) / span_z)
        ox = (w - span_x * sc) / 2
        oz = (h - span_z * sc) / 2
        pts = [(ox + (tr.px[i] - b[0]) * sc, oz + (tr.pz[i] - b[2]) * sc) for i in range(0, tr.N, 2)]
        wc = hex_rgb(tr.theme['wall'][0])
        pygame.draw.lines(s, (0, 0, 0, 200), True, pts, 9)
        pygame.draw.lines(s, wc, True, pts, 6)
        pygame.draw.lines(s, (40, 44, 58), True, pts, 3)
        pygame.draw.circle(s, (255, 255, 255), (int(pts[0][0]), int(pts[0][1])), 5)
        self.outline_cache[key] = (s, tr.length)
        return self.outline_cache[key]

    def map_picker(self, rect, mid, editable=True):
        ui = self.ui
        u = ui.u
        surf = self.screen
        ui.panel(surf, rect, 195)
        pad = int(12 * u)
        x, y, w = rect.x + pad, rect.y + pad, rect.w - 2 * pad
        name, theme = self.map_text(mid)
        ui.text(surf, '#%d / %d' % (mid, MAP_COUNT), x, y, 22 * u, (255, 200, 90))
        ui.text(surf, name, x, y + 24 * u, 30 * u)
        oh = int(rect.h * 0.34)
        out, length = self.outline(mid, int(w), oh)
        ui.text(surf, '%s · %.2f km' % (theme, length / 1000.0), x, y + 58 * u, 20 * u, (190, 205, 240))
        surf.blit(out, (x, y + 84 * u))
        ny = y + 88 * u + oh
        labels = ['-100', '-10', '-1', '+1', '+10', '+100', 'RND']
        deltas = [-100, -10, -1, 1, 10, 100, None]
        gap = 6 * u
        bw = (w - gap * 6) / 7.0
        bh = max(34 * u, min(48 * u, rect.h * 0.1))
        new = mid
        for i, (lab, d) in enumerate(zip(labels, deltas)):
            r = R(x + i * (bw + gap), ny, bw, bh)
            if ui.button(surf, r, lab, 'primary' if d is None else 'normal', size=bh * 0.4, enabled=editable):
                new = (1 + int(_random.random() * MAP_COUNT)) if d is None else ((mid - 1 + d) % MAP_COUNT) + 1
        # 바이옴 선택: 생태계(40) / 시간대(5) / 색감(5)  -> 1000가지
        cy_ = ny + bh + 8 * u
        ch = max(28 * u, min(40 * u, (rect.bottom - pad - cy_ - 6 * u) / 2.0))
        fam, ti, mi = biome_parts(mid)
        fname, tname, mname = biome_part_names(mid, LANG)
        sb = ch * 1.3

        def stepper(rx, ry, rw, label, on_d):
            res = None
            if ui.button(surf, R(rx, ry, sb, ch), '<', 'normal', size=ch * 0.5, enabled=editable):
                res = on_d(-1)
            if ui.button(surf, R(rx + rw - sb, ry, sb, ch), '>', 'normal', size=ch * 0.5, enabled=editable):
                res = on_d(1)
            mid_r = R(rx + sb + 3 * u, ry, rw - 2 * sb - 6 * u, ch)
            ui.panel(surf, mid_r, 150, (20, 28, 56), int(8 * u))
            size = ch * 0.44
            tw_ = ui.render(label, size, (235, 240, 255)).get_width()
            if tw_ > mid_r.w - 6 * u:
                size = size * (mid_r.w - 6 * u) / float(tw_)
            ui.text(surf, label, mid_r.centerx, mid_r.y + (ch - size * 1.15) / 2, size, (235, 240, 255), 'c', shadow=False)
            return res
        r1 = stepper(x, cy_, w, '%s  (%d/%d)' % (fname, fam + 1, BIOME_FAMILIES), lambda d: biome_map(fam + d, ti, mi))
        half = (w - gap) / 2.0
        r2 = stepper(x, cy_ + ch + 6 * u, half, tname, lambda d: biome_map(fam, ti + d, mi))
        r3 = stepper(x + half + gap, cy_ + ch + 6 * u, half, mname, lambda d: biome_map(fam, ti, mi + d))
        for rr_ in (r1, r2, r3):
            if rr_ is not None:
                new = rr_
        return new

    def source_tabs(self, rect, src, enabled=True):
        """[기본 맵 1000] [내가 만든 맵] 전환 -> 새 값"""
        ui = self.ui
        u = ui.u
        half = (rect.w - 8 * u) / 2.0
        if ui.button(self.screen, R(rect.x, rect.y, half, rect.h), T('기본 맵 1000개', 'Built-in maps'), 'chipon' if src != 'custom' else 'chip',
                     size=rect.h * 0.4, enabled=enabled):
            src = 'builtin'
        if ui.button(self.screen, R(rect.x + half + 8 * u, rect.y, half, rect.h), T('내가 만든 맵 (%d)' % len(self.store.maps), 'My maps (%d)' % len(self.store.maps)),
                     'chipon' if src == 'custom' else 'chip', size=rect.h * 0.4, enabled=enabled):
            src = 'custom'
        return src

    def custom_view(self, rect, d, title=None):
        """만든 맵 정보 + 코스 모양 (읽기 전용)"""
        ui = self.ui
        u = ui.u
        surf = self.screen
        ui.panel(surf, rect, 195)
        pad = int(12 * u)
        x, y, w = rect.x + pad, rect.y + pad, rect.w - 2 * pad
        ui.text(surf, title or T('내가 만든 맵', 'Custom map'), x, y, 20 * u, (255, 200, 90))
        ui.text(surf, map_title(d, LANG), x, y + 24 * u, 30 * u)
        oh = int(max(40 * u, rect.h - 150 * u))
        out, length = self.outline(d, int(w), oh)
        th = biome(d['look'])
        nobs = sum(1 for o in d['objs'] if OBJ_INFO[o[0]]['cat'] == 'obs')
        ui.text(surf, T('%s · %.2f km · 장애물 %d · 물건 %d', '%s · %.2f km · %d obstacles · %d objects') % (th['name'] if LANG == 'ko' else th['en'], length / 1000.0, nobs, len(d['objs'])),
                x, y + 58 * u, 18 * u, (190, 205, 240))
        surf.blit(out, (x, y + 84 * u))
        return y + 88 * u + oh

    def custom_picker(self, rect, editable=True, allow_edit=True):
        """'내 맵' 고르기 (◀ ▶ 로 바꾸기 + 편집). 반환: 고른 맵 데이터 또는 None"""
        ui = self.ui
        u = ui.u
        surf = self.screen
        maps = self.store.maps
        if not maps:
            ui.panel(surf, rect, 195)
            ui.text(surf, T('아직 만든 맵이 없어요', 'You have no custom maps yet'), rect.x + 16 * u, rect.y + 20 * u, 26 * u)
            if ui.button(surf, R(rect.x + 16 * u, rect.y + 70 * u, min(rect.w - 32 * u, 320 * u), 56 * u), T('맵 만들러 가기', 'Open map maker'), 'good', enabled=editable):
                self.go('maps')
            return None
        i = max(0, self.store.index(self.profile['cmap']))
        d = maps[i]
        bh = max(36 * u, min(50 * u, rect.h * 0.12))
        body = R(rect.x, rect.y, rect.w, rect.h - bh - 8 * u)
        self.custom_view(body, d)
        y = body.bottom + 8 * u
        bw = (rect.w - 16 * u) / (3.0 if allow_edit else 2.0)
        if ui.button(surf, R(rect.x, y, bw, bh), '<', 'normal', size=bh * 0.5, enabled=editable and len(maps) > 1):
            i = (i - 1) % len(maps)
        if ui.button(surf, R(rect.x + bw + 8 * u, y, bw, bh), '>  %d/%d' % (i + 1, len(maps)), 'normal', size=bh * 0.4, enabled=editable and len(maps) > 1):
            i = (i + 1) % len(maps)
        if allow_edit and ui.button(surf, R(rect.x + 2 * (bw + 8 * u), y, bw, bh), T('편집', 'Edit'), 'good', size=bh * 0.42, enabled=editable):
            self.maker.open(d, d['uid'])
            return d
        d = maps[i]
        if self.profile['cmap'] != d['uid']:
            self.profile['cmap'] = d['uid']
        return d

    # ------------------------------------------------------------------ 메뉴
    def scene_menu(self, dt):
        ui = self.ui
        u = ui.u
        surf = self.screen
        land = self.landscape
        self.draw_show(dt, self.profile['kart'], shift=0.34 if land else 0.0, dist=6.6)
        x = int(self.W * 0.06) if land else self.W // 2
        anc = 'l' if land else 'c'
        ui.text(surf, 'TURBO', x, int(self.H * 0.05), 96 * u, (255, 255, 255), anc)
        ui.text(surf, 'KART 3D', x, int(self.H * 0.05) + 86 * u, 70 * u, (255, 176, 32), anc)
        tag = T('맵·바이옴 1000종 · 카트 100,000종 · 아이템 100종 · WiFi 멀티', '1000 maps & biomes · 100,000 karts · 100 items · WiFi multiplayer')
        tsz = 20 * u
        tw_ = ui.render(tag, tsz, (205, 220, 250)).get_width()
        lim = (self.W * 0.9) if not land else (self.W * 0.52)
        if tw_ > lim:
            tsz = tsz * lim / float(tw_)
        ui.text(surf, tag, x, int(self.H * 0.05) + 160 * u, tsz, (205, 220, 250), anc)
        bw = self.W * 0.40 if land else self.W * 0.82
        bx = int(self.W * 0.06) if land else (self.W - bw) / 2
        by = self.H * 0.40 if land else self.H * 0.40
        bh = min(self.H * 0.085, 58 * u)
        gap = bh * 0.2
        items = [(T('솔로 레이스', 'Solo race'), 'solo', 'primary'), (T('WiFi 멀티플레이', 'WiFi multiplayer'), 'multi', 'primary'),
                 (T('맵 만들기', 'Map maker'), 'maps', 'good'),
                 (T('차고 (카트 꾸미기)', 'Garage (customize)'), 'garage', 'normal'), (T('설정', 'Settings'), 'settings', 'normal')]
        for i, (lab, tgt, kind) in enumerate(items):
            if ui.button(surf, R(bx, by + i * (bh + gap), bw, bh), lab, kind):
                self.go(tgt)
                return
        ui.text(surf, '%s #%d' % (kart_name(self.profile['kart'], LANG), self.profile['kart'] + 1), 14 * u, self.H - 30 * u, 18 * u, (200, 215, 245))
        if self.err:
            ui.text(surf, self.err, self.W // 2, self.H - 60 * u, 22 * u, (255, 120, 120), 'c')
        if ui.button(surf, R(self.W - 120 * u, self.H - 56 * u, 106 * u, 44 * u), T('종료', 'Quit'), 'ghost', size=20 * u):
            self.running = False

    # ------------------------------------------------------------------ 솔로
    def scene_solo(self, dt):
        ui = self.ui
        u = ui.u
        surf = self.screen
        self.draw_show(dt, self.profile['kart'], shift=0.0)
        land = self.landscape
        m = int(14 * u)
        if land:
            pr = R(m, m, self.W * 0.58 - m, self.H - 2 * m)
            rr = R(self.W * 0.58 + m / 2, m, self.W * 0.42 - m * 1.5, self.H - 2 * m)
        else:
            pr = R(m, m, self.W - 2 * m, self.H * 0.58)
            rr = R(m, self.H * 0.58 + 2 * m, self.W - 2 * m, self.H * 0.42 - 3 * m)
        tab_h = int(min(46 * u, pr.h * 0.1))
        src = self.source_tabs(R(pr.x, pr.y, pr.w, tab_h), self.profile['map_src'])
        if src != self.profile['map_src']:
            self.profile['map_src'] = src
            self.profile.save()
        body = R(pr.x, pr.y + tab_h + 8 * u, pr.w, pr.h - tab_h - 8 * u)
        if src == 'custom':
            self.custom_picker(body)
            if self.scene != 'solo':
                return
        else:
            self.sel_map = self.map_picker(body, self.sel_map)
        ui.panel(surf, rr, 195)
        x, y, w = rr.x + 14 * u, rr.y + 14 * u, rr.w - 28 * u
        ui.text(surf, T('레이스 설정', 'Race settings'), x, y, 28 * u, (255, 255, 255))
        d = ui.stepper(surf, R(x, y + 52 * u, w, 44 * u), T('바퀴 수', 'Laps'), int(self.profile['laps']), 1, 10)
        if d:
            self.profile['laps'] = int(self.profile['laps']) + d
        d = ui.stepper(surf, R(x, y + 108 * u, w, 44 * u), T('AI 상대', 'AI rivals'), int(self.profile['bots']), 0, 11)
        if d:
            self.profile['bots'] = int(self.profile['bots']) + d
        half = (w - 10 * u) / 2.0
        item_mode = self.profile['mode'] == 'item'
        if ui.button(surf, R(x, y + 160 * u, half, 40 * u), T('스피드전', 'Speed'), 'chip' if item_mode else 'chipon', size=19 * u):
            self.profile['mode'] = 'speed'
            self.profile.save()
        if ui.button(surf, R(x + half + 10 * u, y + 160 * u, half, 40 * u), T('아이템전', 'Items'), 'chipon' if item_mode else 'chip', size=19 * u):
            self.profile['mode'] = 'item'
            self.profile.save()
        ui.text(surf, '%s #%d' % (kart_name(self.profile['kart'], LANG), self.profile['kart'] + 1), x, y + 210 * u, 18 * u, (190, 205, 240))
        bh = min(70 * u, rr.h * 0.2)
        if ui.button(surf, R(x, rr.bottom - 14 * u - bh * 2 - 10 * u, w, bh), T('출발!', 'START!'), 'primary', size=bh * 0.5):
            self.profile['map'] = self.sel_map
            self.profile.save()
            self.start_solo()
            return
        if ui.button(surf, R(x, rr.bottom - 14 * u - bh, w, bh * 0.8), T('뒤로', 'Back'), 'ghost'):
            self.profile['map'] = self.sel_map
            self.profile.save()
            self.go('menu')

    # ------------------------------------------------------------------ 차고
    def scene_garage(self, dt):
        ui = self.ui
        u = ui.u
        surf = self.screen
        land = self.landscape
        self.draw_show(dt, self.profile['kart'], shift=0.42 if land else 0.0, dist=6.8)
        m = int(14 * u)
        if land:
            pr = R(m, m, min(self.W * 0.5, 480 * u), self.H - 2 * m)
        else:
            pr = R(m, self.H * 0.36, self.W - 2 * m, self.H * 0.62)
        ui.panel(surf, pr, 200)
        x, y, w = pr.x + 14 * u, pr.y + 12 * u, pr.w - 28 * u
        kk0 = clamp(pr.h / (560.0 * u), 0.72, 1.0)
        ui.text(surf, T('차고', 'Garage'), x, y, 32 * u * kk0)
        # 닉네임
        if ui.button(surf, R(x, y + 44 * u, w, 44 * u * kk0), (T('닉네임: ', 'Name: ') + self.profile.display_name()), 'normal', size=22 * u * kk0):
            def setname(t):
                self.profile['name'] = t.strip()
                self.profile.save()
                self.session.send_profile()
            self.open_kb(T('닉네임 (영문/숫자)', 'Nickname'), self.profile['name'], 'alpha', 14, setname)
        k = decode_kart(self.profile['kart'])
        rows = [('body', T('차체', 'Body'), BODIES[k['body']]['name' if LANG == 'ko' else 'en'], 20),
                ('paint', T('페인트', 'Paint'), PAINTS[k['paint']]['name' if LANG == 'ko' else 'en'], 20),
                ('wheel', T('휠', 'Wheels'), wheel_name(k['wheel'], LANG), 25),
                ('wing', T('윙/파츠', 'Wing'), WINGS[k['wing']]['name' if LANG == 'ko' else 'en'], 10)]
        kk = clamp(pr.h / (560.0 * u), 0.72, 1.0)
        ry = y + 100 * u * kk
        rh = 42 * u * kk
        for key, lab, val, mod in rows:
            ui.text(surf, lab, x, ry + 8 * u, 18 * u, (190, 205, 240))
            lb = R(x + 84 * u, ry, 44 * u, rh)
            rb = R(x + w - 44 * u, ry, 44 * u, rh)
            ui.text(surf, val, (lb.right + rb.x) // 2, ry + 8 * u, 20 * u, (255, 255, 255), 'c')
            d = 0
            if ui.button(surf, lb, '<', 'normal'):
                d = -1
            if ui.button(surf, rb, '>', 'normal'):
                d = 1
            if d:
                k[key] = (k[key] + d) % mod
                self.profile['kart'] = encode_kart(k)
                self.profile.save()
                self.session.send_profile()
                self.sfx.play('click', 0.5)
            ry += rh + 8 * u * kk
        # 번호/랜덤
        if ui.button(surf, R(x, ry, w * 0.62, 44 * u * kk), 'No. %d / %d' % (self.profile['kart'] + 1, KART_COUNT), 'normal', size=22 * u):
            def setnum(t):
                try:
                    n = int(float(t))
                    self.profile['kart'] = int(clamp(n, 1, KART_COUNT)) - 1
                    self.profile.save()
                    self.session.send_profile()
                except ValueError:
                    pass
            self.open_kb(T('카트 번호 (1~100000)', 'Kart number (1-100000)'), str(self.profile['kart'] + 1), 'ip', 6, setnum)
        if ui.button(surf, R(x + w * 0.65, ry, w * 0.35, 44 * u * kk), T('랜덤', 'Random'), 'primary', size=20 * u * kk):
            self.profile['kart'] = int(_random.random() * KART_COUNT)
            self.profile.save()
            self.session.send_profile()
        ry += 54 * u * kk
        st = kart_stats(self.profile['kart'])
        for lab, key in ((T('최고속도', 'Speed'), 'speed'), (T('가속', 'Accel'), 'accel'), (T('핸들링', 'Handling'), 'handling'), (T('드리프트', 'Drift'), 'drift')):
            ui.text(surf, lab, x, ry - 2 * u, 17 * u, (190, 205, 240))
            bx = x + 90 * u
            bw = w - 90 * u - 40 * u
            pygame.draw.rect(surf, (20, 24, 40), (bx, ry + 3 * u, bw, 12 * u), border_radius=6)
            pygame.draw.rect(surf, (255, 176, 32), (bx, ry + 3 * u, bw * st[key] / 10.0, 12 * u), border_radius=6)
            ui.text(surf, '%.1f' % st[key], bx + bw + 8 * u, ry - 3 * u, 17 * u, (255, 255, 255))
            ry += 24 * u * kk
        if ui.button(surf, R(x, pr.bottom - 52 * u * kk, w, 40 * u * kk), T('완료', 'Done'), 'primary', size=22 * u * kk):
            self.profile.save()
            self.go('menu')

    # ------------------------------------------------------------------ 설정
    def scene_settings(self, dt):
        global LANG
        ui = self.ui
        u = ui.u
        surf = self.screen
        self.draw_show(dt, self.profile['kart'], shift=0.0)
        pw = min(self.W - 28 * u, 620 * u)
        r = R((self.W - pw) / 2, 14 * u, pw, self.H - 28 * u)
        ui.panel(surf, r, 215)
        kk = clamp(r.h / (700.0 * u), 0.6, 1.0)          # 작은 화면에서는 세로 간격을 줄여 모두 들어가게
        x, y, w = r.x + 18 * u, r.y + 12 * u, r.w - 36 * u
        bh = 44 * u * kk
        cw = (w - 20 * u) / 3.0
        ui.text(surf, T('설정', 'Settings'), x, y, 32 * u * kk)
        y += 50 * u * kk

        def chips(label, names, cur, on_pick):
            nonlocal y
            ui.text(surf, label, x, y, 21 * u * kk, (210, 220, 245))
            y += 27 * u * kk
            for i, nm in enumerate(names):
                if ui.button(surf, R(x + i * (cw + 10 * u), y, cw, bh), nm, 'chipon' if cur == i else 'chip', size=bh * 0.42):
                    on_pick(i)
            y += bh + 12 * u * kk

        def pick_quality(i):
            self.set_quality(i)
            self.show_map = None

        def pick_steer(i):
            self.profile['steer_resp'] = i
            self.profile.save()
            self.toast(T('조향 반응을 바꿨어요', 'Steering changed'), 0.8)

        def pick_lang(i):
            global LANG
            code = ('auto', 'ko', 'en')[i]
            self.profile['lang'] = code
            LANG = ('ko' if self.font_path else 'en') if code == 'auto' else code
            self.profile.save()
        chips(T('그래픽 품질', 'Graphics'), [T('낮음', 'Low'), T('중간', 'Medium'), T('높음', 'High')], self.renderer.q, pick_quality)
        y -= 6 * u * kk
        ui.text(surf, T('높음 = 디테일을 줄이지 않는 원래 그래픽 · 낮음/중간 = 먼 곳 디테일을 줄여서 더 빠르게',
                        'High = full original detail · Low/Medium = less distant detail for speed'), x, y, 16 * u * kk, (170, 190, 230))
        y += 24 * u * kk
        chips(T('조향 반응 (키보드/버튼)', 'Steering response (keys/buttons)'), [T('부드럽게', 'Smooth'), T('보통', 'Normal'), T('빠르게', 'Quick')], int(self.profile['steer_resp']), pick_steer)
        for key, lab in (('auto_gas', T('자동 가속 (터치)', 'Auto gas (touch)')), ('sound', T('소리', 'Sound'))):
            on = bool(self.profile[key])
            if ui.button(surf, R(x, y, w, bh), '%s :  %s' % (lab, 'ON' if on else 'OFF'), 'good' if on else 'normal', size=bh * 0.42):
                self.profile[key] = not on
                if key == 'sound':
                    self.sfx.enabled = not on
                self.touch.layout(self.W, self.H, self.profile['auto_gas'])
                self.profile.save()
            y += bh + 10 * u * kk
        cur_lang = ('auto', 'ko', 'en').index(self.profile['lang']) if self.profile['lang'] in ('auto', 'ko', 'en') else 0
        chips(T('언어 / Language', 'Language'), ['Auto', '한국어' if self.font_path else 'Korean', 'English'], cur_lang, pick_lang)
        if ui.button(surf, R(x, y, w, bh), 'FPS :  %s' % ('ON' if self.show_fps else 'OFF'), 'good' if self.show_fps else 'normal', size=bh * 0.42):
            self.show_fps = not self.show_fps
        if ui.button(surf, R(x, r.bottom - 12 * u - 50 * u * kk, w, 50 * u * kk), T('완료', 'Done'), 'primary', size=22 * u * kk):
            self.profile.save()
            self.go('menu')

    # ------------------------------------------------------------------ 멀티플레이
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
        self.scene = 'lobby'

    def scene_multi(self, dt):
        ui = self.ui
        u = ui.u
        surf = self.screen
        self.draw_show(dt, self.profile['kart'], shift=0.0)
        pw = min(self.W - 28 * u, 760 * u)
        r = R((self.W - pw) / 2, 14 * u, pw, self.H - 28 * u)
        ui.panel(surf, r, 215)
        x, y, w = r.x + 18 * u, r.y + 14 * u, r.w - 36 * u
        ui.text(surf, T('WiFi 멀티플레이', 'WiFi multiplayer'), x, y, 34 * u)
        y += 52 * u
        ips = local_ips()
        ui.text(surf, T('내 IP: ', 'My IP: ') + (', '.join(ips) if ips else T('(WiFi 연결 확인)', '(check WiFi)')), x, y, 19 * u, (190, 205, 240))
        y += 34 * u
        bh = 56 * u
        half = (w - 12 * u) / 2.0
        if ui.button(surf, R(x, y, half, bh), T('방 만들기 (호스트)', 'Host a game'), 'primary'):
            cm = self.store.get(self.profile['cmap']) if self.profile['map_src'] == 'custom' else None
            self.lobby_src = 'custom' if cm else 'builtin'
            if self.session.host_game(int(self.profile['port']), cm):
                self.scene = 'lobby'
            else:
                self.err = self.session.error
        if ui.button(surf, R(x + half + 12 * u, y, half, bh), T('IP 직접 입력', 'Join by IP'), 'normal'):
            self.open_kb(T('호스트 IP (예: 192.168.0.5)', 'Host IP (e.g. 192.168.0.5)'), self.profile['last_ip'], 'ip', 21, self.join_ip)
        y += bh + 16 * u
        ui.text(surf, T('같은 WiFi 의 방', 'Rooms on this WiFi'), x, y, 22 * u, (255, 220, 120))
        if ui.button(surf, R(r.right - 18 * u - 150 * u, y - 6 * u, 150 * u, 40 * u), T('다시 검색', 'Rescan'), 'chip', size=18 * u, enabled=not self.scan.get('busy')):
            self.scan_rooms()
        y += 42 * u
        rooms = self.scan.get('rooms', [])
        if self.scan.get('busy') and not rooms:
            ui.text(surf, T('검색 중…', 'Searching…'), x, y, 20 * u, (190, 205, 240))
        elif not rooms:
            ui.text(surf, T('방을 찾지 못했어요. 친구가 [방 만들기] 후 IP 로 접속하세요.', 'No rooms found. Ask a friend to host, then use Join by IP.'), x, y, 18 * u, (190, 205, 240))
        for i, rm in enumerate(rooms[:5]):
            mlab = (u'\u2605 ' + str(rm['cname'])) if rm.get('cname') else '#%s' % rm.get('map', '?')
            label = '%s  %s  ·  %d/%d  ·  %s  ·  %s' % (rm.get('name', 'room'), rm['ip'], rm.get('players', 0), RoomServer.MAX_PLAYERS, mlab, rm.get('state', ''))
            if ui.button(surf, R(x, y, w, 48 * u), label, 'normal', size=19 * u, enabled=rm.get('state') == 'lobby'):
                self.profile['last_ip'] = rm['ip']
                self.session.join_game(rm['ip'], rm.get('port', DEFAULT_PORT))
                self.scene = 'lobby'
            y += 54 * u
        if self.err:
            ui.text(surf, self.err, x, r.bottom - 112 * u, 20 * u, (255, 120, 120))
        if ui.button(surf, R(x, r.bottom - 60 * u, w, 46 * u), T('뒤로', 'Back'), 'ghost'):
            self.go('menu')

    # ------------------------------------------------------------------ 로비
    def scene_lobby(self, dt):
        ui = self.ui
        u = ui.u
        surf = self.screen
        ses = self.session
        self.draw_show(dt, self.profile['kart'], shift=0.0)
        # 서버에서 시작 신호가 오면 레이스 시작
        for m in ses.pump():
            pass
        if ses.start_msg is not None:
            msg = ses.start_msg
            ses.start_msg = None
            entries = ses.entries_from_start(msg)
            ref = msg.get('cmap') or int(msg['map'])
            self.start_race(ref, int(msg['laps']), entries, True, ses.is_host, float(msg.get('countdown', 5.0)), bool(msg.get('items')))
            return
        if ses.state == 'idle':
            self.err = ses.error or T('연결이 끊어졌어요', 'Disconnected')
            self.go('multi')
            self.err = ses.error or T('연결 실패', 'Connection failed')
            return
        land = self.landscape
        m = int(14 * u)
        if ses.state == 'connecting':
            ui.text(surf, T('연결 중… ', 'Connecting… ') + ses.address, self.W // 2, self.H // 2 - 20 * u, 34 * u, (255, 255, 255), 'c')
            if ui.button(surf, R(self.W // 2 - 100 * u, self.H // 2 + 40 * u, 200 * u, 54 * u), T('취소', 'Cancel'), 'ghost'):
                ses.leave()
                self.go('multi')
            return
        if land:
            lr = R(m, m, self.W * 0.34, self.H - 2 * m)
            rr = R(self.W * 0.34 + 2 * m, m, self.W * 0.66 - 3 * m, self.H - 2 * m)
        else:
            lr = R(m, m, self.W - 2 * m, self.H * 0.3)
            rr = R(m, self.H * 0.3 + 2 * m, self.W - 2 * m, self.H * 0.7 - 3 * m)
        ui.panel(surf, lr, 205)
        x, y = lr.x + 14 * u, lr.y + 12 * u
        ui.text(surf, T('플레이어', 'Players') + ' %d/%d' % (len(ses.players), RoomServer.MAX_PLAYERS), x, y, 26 * u)
        y += 40 * u
        for p in ses.players[:8]:
            me = p['id'] == ses.my_id
            row = R(x, y, lr.w - 28 * u, 34 * u)
            ui.panel(surf, row, 200 if me else 110, (255, 176, 32) if me else (255, 255, 255), 8)
            tc = (20, 20, 20) if me else (255, 255, 255)
            ui.text(surf, ('* ' if p['id'] == ses.host_id else '') + p['name'], row.x + 8 * u, row.y + 4 * u, 20 * u, tc, shadow=False)
            y += 38 * u
        if ses.is_host:
            ips = local_ips()
            ui.text(surf, T('친구에게 알려주세요:', 'Tell your friends:'), x, lr.bottom - 120 * u, 16 * u, (190, 205, 240))
            ui.text(surf, (ips[0] if ips else '?') + ':%d' % self.profile['port'], x, lr.bottom - 96 * u, 24 * u, (255, 220, 120))
        if ui.button(surf, R(x, lr.bottom - 52 * u, lr.w - 28 * u, 42 * u), T('나가기', 'Leave'), 'danger', size=20 * u):
            ses.leave()
            self.go('menu')
            return
        # 오른쪽: 설정
        st = ses.settings
        prect = R(rr.x, rr.y, rr.w, rr.h - 196 * u)
        cm = st.get('cmap')
        if ses.is_host:
            tab_h = int(min(42 * u, prect.h * 0.1))
            if getattr(self, 'lobby_src', None) is None:
                self.lobby_src = 'custom' if cm else 'builtin'
            src = self.source_tabs(R(prect.x, prect.y, prect.w, tab_h), self.lobby_src)
            self.lobby_src = src
            body = R(prect.x, prect.y + tab_h + 6 * u, prect.w, prect.h - tab_h - 6 * u)
            if src == 'custom':
                d = self.custom_picker(body, editable=True, allow_edit=False)
                if self.scene != 'lobby':
                    return
                if d is not None and (cm is None or cmap_key(cm) != cmap_key(d) or cm.get('name') != d['name']):
                    if time.time() - getattr(self, '_cm_sent', 0.0) > 0.6:      # 서버가 되돌려줄 때까지 반복 전송 안 함
                        ses.send_settings(cmap=d)
                        self._cm_sent = time.time()
                    self.profile['map_src'] = 'custom'
            else:
                if cm is not None and time.time() - getattr(self, '_cm_sent', 0.0) > 0.6:
                    ses.send_settings(map=int(st['map']))
                    self._cm_sent = time.time()
                mid = self.map_picker(body, int(st['map']), editable=True)
                if mid != st['map']:
                    ses.send_settings(map=mid)
                    self.profile['map'] = mid
                self.profile['map_src'] = 'builtin'
        elif cm:
            bh = 46 * u
            self.custom_view(R(prect.x, prect.y, prect.w, prect.h - bh - 8 * u), cm, T('방장이 고른 맵 (직접 만든 맵)', "Host's custom map"))
            if ui.button(surf, R(prect.x, prect.bottom - bh, prect.w, bh), T('이 맵을 내 맵에 저장', 'Save this map to My maps'), 'good', size=bh * 0.4):
                if self.store.add_copy(cm):
                    self.toast(T('내 맵에 저장했어요', 'Saved to My maps'), 2.0)
        else:
            self.map_picker(prect, int(st['map']), editable=False)
        ui.panel(surf, R(rr.x, rr.bottom - 186 * u, rr.w, 186 * u), 205)
        sx, sy, sw_ = rr.x + 14 * u, rr.bottom - 180 * u, rr.w - 28 * u
        half = (sw_ - 12 * u) / 2.0
        d1 = ui.stepper(surf, R(sx, sy + 4 * u, half, 38 * u), T('바퀴', 'Laps'), int(st['laps']), 1, 10) if ses.is_host else 0
        d2 = ui.stepper(surf, R(sx + half + 12 * u, sy + 4 * u, half, 38 * u), T('봇', 'Bots'), int(st['bots']), 0, 11) if ses.is_host else 0
        im = bool(st.get('items'))
        if ses.is_host:
            if ui.button(surf, R(sx, sy + 50 * u, half, 38 * u), T('스피드전', 'Speed'), 'chip' if im else 'chipon', size=18 * u):
                ses.send_settings(items=False)
                self.profile['mode'] = 'speed'
            if ui.button(surf, R(sx + half + 12 * u, sy + 50 * u, half, 38 * u), T('아이템전', 'Items'), 'chipon' if im else 'chip', size=18 * u):
                ses.send_settings(items=True)
                self.profile['mode'] = 'item'
        else:
            mode = T('아이템전', 'Item battle') if im else T('스피드전', 'Speed race')
            ui.text(surf, T('바퀴 %d · 봇 %d · %s' % (st['laps'], st['bots'], mode), 'Laps %d · Bots %d · %s' % (st['laps'], st['bots'], mode)), sx, sy + 8 * u, 22 * u, (230, 235, 255))
        if d1:
            ses.send_settings(laps=int(st['laps']) + d1)
        if d2:
            ses.send_settings(bots=int(st['bots']) + d2)
        if ses.is_host:
            if ui.button(surf, R(sx, sy + 100 * u, sw_, 64 * u), T('레이스 시작!', 'START RACE!'), 'primary', size=30 * u):
                ses.start_race()
        else:
            ui.text(surf, T('방장이 시작하기를 기다리는 중…', 'Waiting for the host to start…'), sx + sw_ / 2, sy + 100 * u, 22 * u, (190, 205, 240), 'c')

    # ------------------------------------------------------------------ 메인 루프
    def step(self, dt):
        """한 프레임: 이벤트 -> 장면 -> (키보드 오버레이) -> 화면 갱신"""
        self.t += dt
        self.pump_events()
        taps = self.ptr.take_taps()
        down = self.ptr.down()
        kb_active = self.kb is not None
        self.ui.begin([] if kb_active else taps, down, self.W, self.H)
        try:
            self.frame(dt)
        except Exception:
            import traceback
            traceback.print_exc()
            self.err = 'error'
            self.race = None
            self.scene = 'menu'
            self.show_map = None
        if self.kb is not None:
            self.ui.taps = taps if kb_active else []
            res = self.kb.draw(self.ui, self.screen, self.W, self.H, dt)
            if res:
                self.close_kb(res)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.step(min(self.clock.tick(60) / 1000.0, 0.1))
        try:
            self.profile.save()
            self.session.leave()
        except Exception:
            pass
        pygame.quit()

    def frame(self, dt):
        sc = self.scene
        if sc == 'race' and self.race is not None:
            self.update_race(dt)
            self.draw_race_ui(dt)
        elif sc == 'results' and self.race is not None:
            self.update_race(dt)
            self.draw_results(dt)
        elif sc == 'menu':
            self.scene_menu(dt)
        elif sc == 'solo':
            self.scene_solo(dt)
        elif sc == 'garage':
            self.scene_garage(dt)
        elif sc == 'settings':
            self.scene_settings(dt)
        elif sc == 'multi':
            self.scene_multi(dt)
        elif sc == 'lobby':
            self.scene_lobby(dt)
        elif sc == 'maps':
            self.maker.scene_maps(dt)
        elif sc == 'editor':
            self.maker.scene_editor(dt)
        else:
            self.scene = 'menu'
