
# ============================================================================
#  [폰] 앱: 화면(메뉴/솔로/차고/설정/멀티/로비/레이스/결과) + 메인 루프
# ============================================================================
def R(x, y, w, h):
    return pygame.Rect(int(x), int(y), int(w), int(h))


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
        self.slow_t = 0.0
        self.fps_ema = 60.0
        self.show_fps = bool(args.get('fps'))
        self.finish_at = None
        self.ping = 0.0

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
                if e.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE):
                    self.used_keyboard = True
                if e.key in (pygame.K_ESCAPE, getattr(pygame, 'K_AC_BACK', -999)):
                    self.on_back()
                elif self.scene == 'race':
                    if e.key == pygame.K_r and self.race:
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
        elif self.scene in ('solo', 'garage', 'settings', 'multi'):
            self.profile.save()
            self.go('menu')
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

    def read_input(self, dt):
        k = self.keys
        pressed = self.touch.read(self.ptr.down())
        left = pygame.K_LEFT in k or pygame.K_a in k or 'left' in pressed
        right = pygame.K_RIGHT in k or pygame.K_d in k or 'right' in pressed
        tgt = (1.0 if right else 0.0) - (1.0 if left else 0.0)
        brake = pygame.K_DOWN in k or pygame.K_s in k or 'brake' in pressed
        gas = pygame.K_UP in k or pygame.K_w in k or 'gas' in pressed
        auto = self.profile['auto_gas'] and not self.used_keyboard
        drift = pygame.K_SPACE in k or pygame.K_LSHIFT in k or pygame.K_RSHIFT in k or 'drift' in pressed
        rate = 7.0 if tgt == 0 else 5.5
        self.steer += (tgt - self.steer) * min(1.0, dt * rate)
        return {'steer': self.steer, 'throttle': 1.0 if (gas or (auto and not brake)) else 0.0, 'brake': 1.0 if brake else 0.0, 'drift': drift}, pressed

    # ------------------------------------------------------------------ 레이스
    def start_solo(self):
        p = self.profile
        entries = solo_entries(p.display_name(), p['kart'], int(p['bots']))
        self.start_race(int(p['map']), int(p['laps']), entries, False, True, 5.0)

    def start_race(self, map_id, laps, entries, multi, is_host, countdown):
        self.loading(T('맵 생성 중…', 'Building map…') + ' #%d' % map_id)
        self.race = Race(map_id, laps, entries, multi=multi, is_host=is_host, countdown=countdown, net=self.session.net if multi else None)
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
            elif kind == 'sim':
                e = ev[1]
                if e in ('pad', 'miniturbo'):
                    self.sfx.play('boost')
                    if e == 'pad':
                        self.toast('BOOST!', 0.7, (80, 230, 255))
                elif e in ('wall', 'bump'):
                    self.sfx.play('bump')
                    self.renderer.shake = max(self.renderer.shake, 0.6)
                elif e.startswith('tier'):
                    self.sfx.play('tier')

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
        # 성능 자동 조절
        self.fps_ema += (1.0 / max(dt, 1e-3) - self.fps_ema) * 0.05
        if self.fps_ema < 24 and self.renderer.q > 0 and race.phase == 'run':
            self.slow_t += dt
            if self.slow_t > 3.0:
                self.slow_t = 0.0
                self.set_quality(self.renderer.q - 1)
                self.toast(T('프레임 향상을 위해 그래픽 품질을 낮췄어요', 'Lowered graphics for smoother play'), 2.5, (255, 255, 255))
        else:
            self.slow_t = 0.0

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
        draw_hud(self, self.screen, race, dt)
        self.touch.draw(self.screen, ui, self.pressed)
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
        key = (mid, w, h)
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
        cy_ = ny + bh + 8 * u
        ch = max(28 * u, min(40 * u, (rect.bottom - pad - cy_ - 6 * u) / 2.0))
        ti = map_info(mid)['theme']
        cw = (w - gap * 4) / 5.0
        for i, th in enumerate(THEMES):
            r = R(x + (i % 5) * (cw + gap), cy_ + (i // 5) * (ch + 6 * u), cw, ch)
            if ui.button(surf, r, th['name'] if LANG == 'ko' else th['en'], 'chipon' if i == ti else 'chip', size=ch * 0.44, enabled=editable):
                new = ((mid - 1) // 10) * 10 + i + 1
        return new

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
        ui.text(surf, T('맵 1000개 · 카트 100,000종 · WiFi 멀티', '1000 maps · 100,000 karts · WiFi multiplayer'), x, int(self.H * 0.05) + 160 * u, 20 * u, (205, 220, 250), anc)
        bw = self.W * 0.40 if land else self.W * 0.82
        bx = int(self.W * 0.06) if land else (self.W - bw) / 2
        by = self.H * 0.43 if land else self.H * 0.40
        bh = min(self.H * 0.095, 60 * u)
        gap = bh * 0.2
        items = [(T('솔로 레이스', 'Solo race'), 'solo', 'primary'), (T('WiFi 멀티플레이', 'WiFi multiplayer'), 'multi', 'primary'),
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
        self.sel_map = self.map_picker(pr, self.sel_map)
        ui.panel(surf, rr, 195)
        x, y, w = rr.x + 14 * u, rr.y + 14 * u, rr.w - 28 * u
        ui.text(surf, T('레이스 설정', 'Race settings'), x, y, 28 * u, (255, 255, 255))
        d = ui.stepper(surf, R(x, y + 52 * u, w, 44 * u), T('바퀴 수', 'Laps'), int(self.profile['laps']), 1, 10)
        if d:
            self.profile['laps'] = int(self.profile['laps']) + d
        d = ui.stepper(surf, R(x, y + 108 * u, w, 44 * u), T('AI 상대', 'AI rivals'), int(self.profile['bots']), 0, 11)
        if d:
            self.profile['bots'] = int(self.profile['bots']) + d
        ui.text(surf, '%s #%d' % (kart_name(self.profile['kart'], LANG), self.profile['kart'] + 1), x, y + 166 * u, 18 * u, (190, 205, 240))
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
        x, y, w = r.x + 18 * u, r.y + 14 * u, r.w - 36 * u
        ui.text(surf, T('설정', 'Settings'), x, y, 34 * u)
        y += 56 * u
        ui.text(surf, T('그래픽 품질', 'Graphics'), x, y, 22 * u, (210, 220, 245))
        y += 30 * u
        qn = [T('낮음', 'Low'), T('중간', 'Medium'), T('높음', 'High')]
        cw = (w - 20 * u) / 3.0
        for i in range(3):
            if ui.button(surf, R(x + i * (cw + 10 * u), y, cw, 46 * u), qn[i], 'chipon' if self.renderer.q == i else 'chip'):
                self.set_quality(i)
                self.show_map = None
        y += 62 * u
        for key, lab in (('auto_gas', T('자동 가속 (터치)', 'Auto gas (touch)')), ('sound', T('소리', 'Sound'))):
            on = bool(self.profile[key])
            if ui.button(surf, R(x, y, w, 46 * u), '%s :  %s' % (lab, 'ON' if on else 'OFF'), 'good' if on else 'normal'):
                self.profile[key] = not on
                if key == 'sound':
                    self.sfx.enabled = not on
                self.touch.layout(self.W, self.H, self.profile['auto_gas'])
                self.profile.save()
            y += 56 * u
        ui.text(surf, T('언어 / Language', 'Language'), x, y, 22 * u, (210, 220, 245))
        y += 30 * u
        for i, (code, lab) in enumerate((('auto', 'Auto'), ('ko', '한국어' if self.font_path else 'Korean'), ('en', 'English'))):
            cur = self.profile['lang']
            if ui.button(surf, R(x + i * (cw + 10 * u), y, cw, 46 * u), lab, 'chipon' if cur == code else 'chip'):
                self.profile['lang'] = code
                LANG = ('ko' if self.font_path else 'en') if code == 'auto' else code
                self.profile.save()
        y += 62 * u
        if ui.button(surf, R(x, y, w, 46 * u), 'FPS :  %s' % ('ON' if self.show_fps else 'OFF'), 'good' if self.show_fps else 'normal'):
            self.show_fps = not self.show_fps
        if ui.button(surf, R(x, r.bottom - 66 * u, w, 50 * u), T('완료', 'Done'), 'primary'):
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
            if self.session.host_game(int(self.profile['port'])):
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
            label = '%s  %s  ·  %d/%d  ·  #%s  ·  %s' % (rm.get('name', 'room'), rm['ip'], rm.get('players', 0), RoomServer.MAX_PLAYERS, rm.get('map', '?'), rm.get('state', ''))
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
            self.start_race(int(msg['map']), int(msg['laps']), entries, True, ses.is_host, float(msg.get('countdown', 5.0)))
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
        mid = self.map_picker(R(rr.x, rr.y, rr.w, rr.h - 150 * u), int(st['map']), editable=ses.is_host)
        if ses.is_host and mid != st['map']:
            ses.send_settings(map=mid)
            self.profile['map'] = mid
        ui.panel(surf, R(rr.x, rr.bottom - 140 * u, rr.w, 140 * u), 205)
        sx, sy, sw_ = rr.x + 14 * u, rr.bottom - 134 * u, rr.w - 28 * u
        half = (sw_ - 12 * u) / 2.0
        d1 = ui.stepper(surf, R(sx, sy + 4 * u, half, 38 * u), T('바퀴', 'Laps'), int(st['laps']), 1, 10) if ses.is_host else 0
        d2 = ui.stepper(surf, R(sx + half + 12 * u, sy + 4 * u, half, 38 * u), T('봇', 'Bots'), int(st['bots']), 0, 11) if ses.is_host else 0
        if not ses.is_host:
            ui.text(surf, T('바퀴 %d · 봇 %d' % (st['laps'], st['bots']), 'Laps %d · Bots %d' % (st['laps'], st['bots'])), sx, sy + 8 * u, 22 * u, (230, 235, 255))
        if d1:
            ses.send_settings(laps=int(st['laps']) + d1)
        if d2:
            ses.send_settings(bots=int(st['bots']) + d2)
        if ses.is_host:
            if ui.button(surf, R(sx, sy + 56 * u, sw_, 64 * u), T('레이스 시작!', 'START RACE!'), 'primary', size=30 * u):
                ses.start_race()
        else:
            ui.text(surf, T('방장이 시작하기를 기다리는 중…', 'Waiting for the host to start…'), sx + sw_ / 2, sy + 70 * u, 22 * u, (190, 205, 240), 'c')

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
        else:
            self.scene = 'menu'
