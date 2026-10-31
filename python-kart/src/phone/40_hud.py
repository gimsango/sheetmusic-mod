
# ============================================================================
#  [폰] 터치 조작 버튼 / HUD / 미니맵 / 사운드
# ============================================================================
class TouchControls(object):
    def __init__(self):
        self.btn = {}
        self.cache = {}

    def layout(self, sw, sh, auto_gas):
        r = int(min(sh * 0.125, sw * 0.085))
        self.r = r
        y = sh - int(r * 1.45)
        self.btn = {
            'left': (int(r * 1.3), y, r),
            'right': (int(r * 3.55), y, r),
            'drift': (sw - int(r * 1.5), y, int(r * 1.15)),
            'brake': (sw - int(r * 1.5), y - int(r * 2.35), int(r * 0.8)),
            'gas': (sw - int(r * 3.85), y + int(r * 0.15), int(r * 0.95)),
        }
        self.auto_gas = auto_gas

    def read(self, points):
        pressed = set()
        for (px, py) in points:
            for name, (cx, cy, rad) in self.btn.items():
                if name == 'gas' and self.auto_gas:
                    continue
                if (px - cx) ** 2 + (py - cy) ** 2 <= (rad * 1.3) ** 2:
                    pressed.add(name)
        return pressed

    def _disc(self, rad, on, color):
        key = (rad, on, color)
        s = self.cache.get(key)
        if s is None:
            s = pygame.Surface((rad * 2 + 4, rad * 2 + 4), pygame.SRCALPHA)
            a = 150 if on else 70
            pygame.draw.circle(s, (color[0], color[1], color[2], a), (rad + 2, rad + 2), rad)
            pygame.draw.circle(s, (255, 255, 255, 170 if on else 90), (rad + 2, rad + 2), rad, max(2, rad // 14))
            self.cache[key] = s
        return s

    def draw(self, surf, ui, pressed):
        u = ui.u
        for name, (cx, cy, rad) in self.btn.items():
            if name == 'gas' and self.auto_gas:
                continue
            on = name in pressed
            col = {'left': (120, 160, 255), 'right': (120, 160, 255), 'drift': (255, 150, 40), 'brake': (255, 80, 80), 'gas': (90, 220, 120)}[name]
            d = self._disc(rad, on, col)
            surf.blit(d, (cx - rad - 2, cy - rad - 2))
            wht = (255, 255, 255)
            if name in ('left', 'right'):
                s = 1 if name == 'right' else -1
                k = rad * 0.45
                pygame.draw.polygon(surf, wht, [(cx + s * k, cy), (cx - s * k * 0.6, cy - k), (cx - s * k * 0.6, cy + k)])
            else:
                lab = {'drift': 'DRIFT', 'brake': T('브레이크', 'BRAKE'), 'gas': 'GAS'}[name]
                ui.text(surf, lab, cx, cy - rad * 0.2, rad * 0.42, wht, 'c')


def build_minimap(track, size, theme_col):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    b = track.bounds
    span = max(b[1] - b[0], b[3] - b[2], 1.0)
    sc = (size - 16) / span
    ox = (size - (b[1] - b[0]) * sc) / 2
    oz = (size - (b[3] - b[2]) * sc) / 2
    pts = [(ox + (track.px[i] - b[0]) * sc, oz + (track.pz[i] - b[2]) * sc) for i in range(0, track.N, 2)]
    rrect(s, (0, 0, 0, 90), s.get_rect(), size * 0.12)
    pygame.draw.lines(s, (0, 0, 0, 255), True, pts, max(5, size // 22))
    pygame.draw.lines(s, (235, 238, 250, 255), True, pts, max(3, size // 36))
    s0 = pts[0]
    pygame.draw.circle(s, (255, 255, 255, 255), (int(s0[0]), int(s0[1])), max(3, size // 36))
    return s, (b[0], b[2], sc, ox, oz)


def draw_minimap(ui, surf, mini, tf, race, x, y):
    surf.blit(mini, (x, y))
    b0, b2, sc, ox, oz = tf
    for rc in race.racers:
        px = x + ox + (rc.x - b0) * sc
        py = y + oz + (rc.z - b2) * sc
        if rc is race.local:
            continue
        col = (255, 110, 110) if rc.kind == 'bot' else (90, 230, 255)
        pygame.draw.circle(surf, col, (int(px), int(py)), max(3, int(ui.u * 4)))
    rc = race.local
    px = x + ox + (rc.x - b0) * sc
    py = y + oz + (rc.z - b2) * sc
    pygame.draw.circle(surf, (255, 255, 255), (int(px), int(py)), max(5, int(ui.u * 7)))
    pygame.draw.circle(surf, (255, 176, 32), (int(px), int(py)), max(4, int(ui.u * 5)))


def fmt_time(t):
    m = int(t // 60)
    return '%d:%05.2f' % (m, t - m * 60)


def draw_hud(app, surf, race, dt):
    ui = app.ui
    u = ui.u
    sw, sh = app.W, app.H
    loc = race.local
    sim = loc.sim
    ranking = race.ranking()
    pos = ranking.index(loc) + 1
    # 순위
    ui.text(surf, str(pos), 18 * u, 8 * u, 84 * u, (255, 176, 32))
    nw = ui.render(str(pos), 84 * u, (255, 176, 32)).get_width()
    ui.text(surf, '/%d' % len(race.racers), 22 * u + nw, 44 * u, 34 * u, (255, 255, 255))
    ui.text(surf, 'LAP %d/%d' % (min(race.laps, sim.lap), race.laps), 20 * u, 98 * u, 28 * u)
    ui.text(surf, fmt_time(max(0.0, race.t)), 20 * u, 130 * u, 26 * u, (220, 230, 255))
    # 미니맵
    ms = int(min(sh * 0.34, 200 * u))
    if app.mini is None or app.mini[0].get_width() != ms:
        app.mini = build_minimap(race.track, ms, None)
    mx, my = sw - ms - 12 * u, 10 * u
    draw_minimap(ui, surf, app.mini[0], app.mini[1], race, int(mx), int(my))
    ui.text(surf, '#%d %s' % (race.map_id, race.track.info['name' if LANG == 'ko' else 'name_en']), sw - 14 * u, my + ms + 2 * u, 15 * u, (215, 225, 250), 'r')
    # 속도계
    kmh = int(sim.speed * 3.6)
    cx = int(sw * 0.70) if sw > sh else sw // 2 + int(sw * 0.18)
    by = sh - int(app.touch.r * 1.0) if app.touch.btn else sh - 90 * u
    ui.text(surf, str(kmh), cx, by - 64 * u, 70 * u, (255, 255, 255), 'r')
    ui.text(surf, 'km/h', cx + 6 * u, by - 36 * u, 24 * u, (200, 215, 245))
    bw = int(220 * u)
    pygame.draw.rect(surf, (0, 0, 0), (cx - bw, by + 4 * u, bw, 10 * u), border_radius=5)
    ratio = clamp(sim.speed / sim.stats['max_speed'], 0, 1.0)
    pygame.draw.rect(surf, (25, 230, 255) if sim.boost_t <= 0 else (255, 160, 40), (cx - bw, by + 4 * u, int(bw * ratio), 10 * u), border_radius=5)
    if sim.boost_t > 0:
        pygame.draw.rect(surf, (255, 255, 255), (cx - bw, by + 17 * u, int(bw * clamp(sim.boost_t / 1.9, 0, 1)), 6 * u), border_radius=3)
    if sim.drifting:
        tc = [(170, 200, 255), (60, 170, 255), (255, 160, 40), (210, 80, 255)][sim.drift_tier]
        pygame.draw.rect(surf, (0, 0, 0), (cx - bw, by + 26 * u, bw, 8 * u), border_radius=4)
        pygame.draw.rect(surf, tc, (cx - bw, by + 26 * u, int(bw * clamp(sim.drift_charge / 3.2, 0, 1)), 8 * u), border_radius=4)
    # 순위표
    if sh >= 380 and sw > sh:
        y = 170 * u
        for i, r in enumerate(ranking[:6]):
            me = r is loc
            row = pygame.Rect(int(12 * u), int(y), int(190 * u), int(24 * u))
            ui.panel(surf, row, 200 if me else 110, (255, 176, 32) if me else (0, 0, 0), 8)
            ui.text(surf, '%d' % (i + 1), row.x + 8 * u, row.y + 2 * u, 18 * u, (20, 20, 20) if me else (255, 255, 255), shadow=False)
            ui.text(surf, r.name, row.x + 30 * u, row.y + 2 * u, 18 * u, (20, 20, 20) if me else (235, 240, 255), shadow=False)
            y += 27 * u
    # 카운트다운 / 알림
    if race.phase == 'count':
        n = int(math.ceil(max(0.0, race.count_left)))
        if 1 <= n <= 3:
            frac = race.count_left - (n - 1)
            size = (150 + 60 * frac) * u
            ui.text(surf, str(n), sw // 2, int(sh * 0.2), size, (255, 255, 255), 'c')
    if sim.wrong_way and race.phase == 'run' and not loc.finished:
        ui.text(surf, T('역주행!', 'WRONG WAY!'), sw // 2, int(sh * 0.36), 50 * u, (255, 80, 90), 'c')
    now = time.time()
    app.toasts = [t for t in app.toasts if t[1] > now]
    ty = int(sh * 0.16)
    for text, until, color, big in app.toasts[-2:]:
        a = clamp((until - now) * 3.0, 0.0, 1.0)
        ui.text(surf, text, sw // 2, ty, (62 if big else 38) * u, color, 'c')
        ty += int((70 if big else 46) * u)
