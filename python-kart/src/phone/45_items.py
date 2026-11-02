
# ============================================================================
#  [폰] 아이템전 UI: 벡터 아이콘 / 슬롯 3칸(키 1·2·3, 터치) / 룰렛 / 상태 표시 / 화면 효과(먹물·번쩍)
# ============================================================================
class ItemIcons(object):
    """코어의 벡터 아이콘 정의(ICONS) -> pygame Surface (2배로 그려서 부드럽게 축소, 크기별 캐시)"""

    def __init__(self):
        self.cache = {}

    def get(self, it, size):
        size = max(8, int(size))
        key = (it, size)
        s = self.cache.get(key)
        if s is None:
            if len(self.cache) > 320:
                self.cache.clear()
            s = self.cache[key] = self._make(ITEMS[it], size)
        return s

    @staticmethod
    def _draw(surf, item, prims, h, k, off, shadow):
        def P(x, y):
            return (h + x * k + off, h + y * k + off)
        for prim in prims:
            t = prim[0]
            if t == 'c':
                col = (0, 0, 0, 110) if shadow else icon_color(item, prim[4])
                pygame.draw.circle(surf, col, P(prim[1], prim[2]), max(1, int(prim[3] * k)))
            elif t == 'e':
                col = (0, 0, 0, 110) if shadow else icon_color(item, prim[5])
                cx, cy = P(prim[1], prim[2])
                rx, ry = max(1.0, prim[3] * k), max(1.0, prim[4] * k)
                pygame.draw.ellipse(surf, col, (cx - rx, cy - ry, rx * 2, ry * 2))
            elif t == 'r':
                col = (0, 0, 0, 110) if shadow else icon_color(item, prim[5])
                pygame.draw.circle(surf, col, P(prim[1], prim[2]), max(1, int(prim[3] * k + prim[4] * k / 2)), max(1, int(prim[4] * k)))
            elif t == 'p':
                col = (0, 0, 0, 110) if shadow else icon_color(item, prim[2])
                pygame.draw.polygon(surf, col, [P(x, y) for x, y in prim[1]])
            elif t == 'l':
                col = (0, 0, 0, 110) if shadow else icon_color(item, prim[3])
                w = max(1, int(prim[2] * k))
                pts = [P(x, y) for x, y in prim[1]]
                pygame.draw.lines(surf, col, False, pts, w)
                for p in pts:
                    pygame.draw.circle(surf, col, (int(p[0]), int(p[1])), max(1, w // 2))

    def _make(self, item, size):
        ss = size * 2
        surf = pygame.Surface((ss, ss), pygame.SRCALPHA)
        h = ss / 2.0
        k = h * 0.86
        prims = ICONS[item['icon']]
        self._draw(surf, item, prims, h, k, max(1, ss // 28), True)
        self._draw(surf, item, prims, h, k, 0, False)
        try:
            return pygame.transform.smoothscale(surf, (size, size))
        except Exception:
            return pygame.transform.scale(surf, (size, size))


def item_bar_rects(app):
    u = app.ui.u
    W, H = app.W, app.H
    S = int(64 * u)
    gap = int(9 * u)
    total = 3 * S + 2 * gap
    x0 = W // 2 - total // 2
    if app.landscape:
        y0 = int(8 * u)
    else:
        ms = int(min(H * 0.34, 200 * u))
        y0 = int(10 * u + ms + 34 * u)
    return [pygame.Rect(x0 + i * (S + gap), y0, S, S) for i in range(ITEM_SLOTS)]


def draw_item_bar(app, surf, race):
    ui = app.ui
    u = ui.u
    rc = race.local
    rects = item_bar_rects(app)
    t = app.t
    for i, r in enumerate(rects):
        it = rc.items[i]
        roll = rc.roll[i]
        ready = it is not None and roll <= 0
        ui.panel(surf, r, 215 if ready else 150, (18, 26, 52) if ready else (8, 12, 28), int(14 * u))
        if ready:
            pulse = 0.75 + 0.25 * math.sin(t * 6.0 + i)
            bc = (int(255 * pulse), int(200 * pulse), 70)
        else:
            bc = (80, 92, 125)
        rrect_outline(surf, bc, r, int(14 * u), max(2, int(3 * u)))
        if it is not None:
            if roll > 0:
                show = (int(t * 16) * 37 + i * 11) % ITEM_COUNT          # 룰렛
                ic = app.icons.get(show, r.w * 0.66)
            else:
                ic = app.icons.get(it, r.w * 0.8)
            surf.blit(ic, (r.centerx - ic.get_width() // 2, r.centery - ic.get_height() // 2))
            if ready and rc.uses[i] > 1:
                ui.text(surf, 'x%d' % rc.uses[i], r.right - 4 * u, r.bottom - 24 * u, 20 * u, (255, 255, 255), 'r')
            if ready:
                name = item_name(it, LANG)
                size = 14 * u
                w = ui.render(name, size, (230, 236, 255)).get_width()
                if w > r.w + 8 * u:
                    size = max(8, size * (r.w + 8 * u) / float(w))
                ui.text(surf, name, r.centerx, r.bottom + 2 * u, size, (230, 236, 255), 'c')
        ui.text(surf, str(i + 1), r.x + 6 * u, r.y + 2 * u, 17 * u, (255, 220, 120))
    app.hud_top = rects[0].bottom + 22 * u
    # 상태 표시 (무적/방패/축소…)
    st = fx_status(rc.sim, LANG)
    if st:
        x = rects[0].x
        y = rects[0].bottom + 20 * u
        for text, col in st[:4]:
            tw = ui.render(text, 15 * u, col).get_width()
            chip = pygame.Rect(int(x), int(y), int(tw + 14 * u), int(22 * u))
            ui.panel(surf, chip, 170, (0, 0, 0), int(10 * u))
            ui.text(surf, text, chip.x + 7 * u, chip.y + 2 * u, 15 * u, col, shadow=False)
            x += chip.w + 6 * u
        app.hud_top = y + 28 * u
    # 날아오는 미사일 경고
    thr = incoming_threat(race)
    if thr is not None and int(t * 6) % 2 == 0:
        ui.text(surf, T('! 미사일 접근 !', '! INCOMING !'), app.W // 2, int(app.hud_top), 30 * u, (255, 80, 80), 'c')
    return rects


def rrect_outline(surf, color, rect, r, width):
    try:
        pygame.draw.rect(surf, color, rect, width, border_radius=int(r))
    except TypeError:
        pygame.draw.rect(surf, color, rect, width)


class ScreenFx(object):
    """먹물(시야 가림)과 번개 번쩍임 - 큰 반투명 면은 미리 만들어 두고 투명도만 바꿔서 그린다"""

    def __init__(self):
        self.size = None
        self.ink = None
        self.veil = None
        self.flash = 0.0
        self.flash_col = (255, 255, 255)
        self.seed = 1

    def _ensure(self, W, H):
        if self.size != (W, H):
            self.size = (W, H)
            self.ink = None
            self.veil = pygame.Surface((W, H)).convert() if pygame.display.get_surface() is not None else pygame.Surface((W, H))

    def _make_ink(self, W, H):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        rnd = Rng(self.seed)
        base = min(W, H)
        for _ in range(7):
            cx, cy = W * (0.1 + rnd() * 0.8), H * (0.15 + rnd() * 0.75)
            r = base * (0.12 + rnd() * 0.16)
            pygame.draw.circle(s, (14, 12, 26, 245), (int(cx), int(cy)), int(r))
            for _k in range(6):
                a = rnd() * TAU
                d = r * (0.8 + rnd() * 0.6)
                pygame.draw.circle(s, (14, 12, 26, 245), (int(cx + math.cos(a) * d), int(cy + math.sin(a) * d)), int(r * (0.18 + rnd() * 0.25)))
            pygame.draw.circle(s, (60, 52, 90, 255), (int(cx - r * 0.35), int(cy - r * 0.35)), max(2, int(r * 0.12)))
        self.ink = s

    def draw(self, surf, W, H, blind_t, dt):
        self._ensure(W, H)
        if blind_t > 0:
            if self.ink is None:
                self.seed += 1
                self._make_ink(W, H)
            a = int(255 * clamp(blind_t / 1.2, 0.0, 1.0))
            self.ink.set_alpha(a)
            surf.blit(self.ink, (0, 0))
        elif self.ink is not None:
            self.ink = None
        if self.flash > 0:
            self.veil.fill(self.flash_col)
            self.veil.set_alpha(int(clamp(self.flash * 420, 0, 170)))
            surf.blit(self.veil, (0, 0))
            self.flash = max(0.0, self.flash - dt)
