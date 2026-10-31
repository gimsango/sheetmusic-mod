
# ============================================================================
#  [폰] 테마별 색상표 / 안개 / 하늘 / 배경 파노라마 / 장식물 스프라이트
# ============================================================================
FOGN = 16


def fog_mix(c, fog, t):
    return (int(c[0] + (fog[0] - c[0]) * t), int(c[1] + (fog[1] - c[1]) * t), int(c[2] + (fog[2] - c[2]) * t))


# kind: (월드 폭 m, 월드 높이 m, 캔버스 폭 px, 캔버스 높이 px)
SPRITE_DIM = {
    'pine': (7.0, 11.0, 70, 110), 'roundtree': (7.5, 9.5, 75, 95), 'bush': (3.4, 2.2, 34, 22), 'cactus': (4.2, 6.5, 42, 65),
    'rock': (6.0, 3.6, 60, 36), 'mesa': (20.0, 24.0, 100, 120), 'palm': (9.0, 10.5, 90, 105), 'building': (1.0, 1.0, 64, 128),
    'crystal': (3.4, 8.0, 34, 80), 'lollipop': (4.4, 7.6, 44, 76), 'icecream': (3.4, 7.6, 34, 76),
}


def _surf(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def _ell(s, c, cx, cy, rx, ry):
    pygame.draw.ellipse(s, c, (int(cx - rx), int(cy - ry), max(1, int(rx * 2)), max(1, int(ry * 2))))


def make_sprite(kind, th, var):
    cw, ch = SPRITE_DIM[kind][2], SPRITE_DIM[kind][3]
    s = _surf(cw, ch)
    cx = cw / 2.0
    if kind == 'pine':
        snowy = th.get('snowy')
        pygame.draw.rect(s, (90, 59, 34), (int(cx - 4), ch - 20, 8, 20))
        cols = [(31, 107, 53), (42, 125, 63), (53, 145, 74)] if not snowy else [(79, 127, 102), (109, 154, 132), (242, 247, 251)]
        for (by, hw_, h_), c in zip(((ch - 14, 34, 44), (ch - 40, 28, 38), (ch - 64, 21, 34)), cols):
            pygame.draw.polygon(s, c, [(cx - hw_, by), (cx + hw_, by), (cx, by - h_)])
            pygame.draw.polygon(s, shade_rgb(c, 0.7), [(cx, by - h_), (cx + hw_, by), (cx, by)])
    elif kind == 'roundtree':
        cols = [(217, 84, 30), (232, 163, 23), (184, 58, 26), (240, 192, 48)] if th.get('autumn') else [(58, 140, 58), (74, 160, 74), (47, 127, 53), (90, 170, 80)]
        c = cols[var % len(cols)]
        pygame.draw.rect(s, (90, 59, 34), (int(cx - 5), ch - 40, 10, 40))
        _ell(s, shade_rgb(c, 0.72), cx + 4, ch - 56, 33, 30)
        _ell(s, c, cx - 2, ch - 58, 31, 29)
        _ell(s, shade_rgb(c, 1.18), cx - 10, ch - 68, 16, 13)
    elif kind == 'bush':
        _ell(s, (40, 110, 48), cx + 2, ch - 8, 15, 9)
        _ell(s, (58, 140, 58), cx - 3, ch - 9, 14, 9)
        _ell(s, (88, 170, 80), cx - 6, ch - 12, 7, 4)
    elif kind == 'cactus':
        g = (59, 138, 74)
        pygame.draw.rect(s, g, (int(cx - 7), 6, 14, ch - 6), border_radius=6)
        pygame.draw.rect(s, shade_rgb(g, 0.72), (int(cx + 1), 8, 6, ch - 10), border_radius=3)
        pygame.draw.rect(s, g, (int(cx - 20), 28, 20, 8), border_radius=3)
        pygame.draw.rect(s, g, (int(cx - 22), 14, 8, 22), border_radius=4)
        pygame.draw.rect(s, g, (int(cx + 5), 36, 18, 8), border_radius=3)
        pygame.draw.rect(s, g, (int(cx + 15), 22, 8, 22), border_radius=4)
    elif kind == 'rock':
        c0, c1 = hex_rgb(th['rock'][0]), hex_rgb(th['rock'][1])
        pygame.draw.polygon(s, c0, [(2, ch), (8, 14), (24, 2), (44, 6), (58, 22), (58, ch)])
        pygame.draw.polygon(s, c1, [(30, 4), (44, 6), (58, 22), (58, ch), (32, ch), (34, 18)])
        pygame.draw.polygon(s, shade_rgb(c0, 1.2), [(8, 14), (24, 2), (30, 4), (20, 20)])
    elif kind == 'mesa':
        for c, pts in (((176, 74, 40), [(0, ch), (14, 46), (86, 46), (100, ch)]), ((199, 101, 58), [(12, 62), (18, 24), (82, 24), (90, 62)]),
                       ((168, 68, 36), [(22, 30), (26, 8), (74, 8), (78, 30)]), ((224, 160, 96), [(26, 10), (28, 4), (72, 4), (74, 10)])):
            pygame.draw.polygon(s, c, pts)
        pygame.draw.polygon(s, (120, 48, 26), [(60, 8), (100, ch), (70, ch)])
    elif kind == 'palm':
        pygame.draw.polygon(s, (138, 106, 64), [(cx - 5, ch), (cx + 3, ch), (cx + 8, 22), (cx + 2, 22)])
        for k, c in enumerate(((47, 143, 58), (58, 160, 70), (40, 125, 52), (70, 175, 80), (47, 143, 58), (58, 160, 70))):
            a = -2.7 + k * 0.54
            ex, ey = cx + 6 + math.cos(a) * 40, 22 + math.sin(a) * 22 + 12
            mx, my = cx + 6 + math.cos(a) * 20, 22 + math.sin(a) * 20 - 6
            pygame.draw.polygon(s, c, [(cx + 6, 22), (mx - 3, my - 5), (ex, ey), (mx + 3, my + 5)])
        pygame.draw.circle(s, (90, 59, 34), (int(cx + 6), 24), 4)
    elif kind == 'building':
        neon = th.get('night')
        cols = [(255, 43, 214), (25, 230, 255), (255, 225, 74), (120, 255, 150)]
        c = cols[var % 4]
        pygame.draw.rect(s, (22, 22, 44), (0, 0, cw, ch))
        pygame.draw.rect(s, (34, 34, 66), (cw - 14, 0, 14, ch))
        rnd = Rng(var * 977 + 13)
        for y in range(8, ch - 6, 10):
            for x in range(6, cw - 14, 10):
                if rnd() < 0.55:
                    wc = c if rnd() < 0.3 else ((255, 220, 140) if rnd() < 0.6 else (150, 190, 255))
                    pygame.draw.rect(s, wc, (x, y, 5, 5))
        pygame.draw.rect(s, c, (0, 0, cw, 3))
        pygame.draw.rect(s, c, (0, ch // 2, cw, 2))
        if not neon:
            pygame.draw.rect(s, (60, 60, 80), (0, 0, cw, ch), 2)
    elif kind == 'crystal':
        col = (255, 122, 26) if th.get('lava') else ((25, 230, 255) if th['key'] == 'space' else (255, 43, 214))
        pygame.draw.polygon(s, col, [(cx, 0), (cx + 12, ch * 0.45), (cx, ch), (cx - 12, ch * 0.45)])
        pygame.draw.polygon(s, shade_rgb(col, 0.62), [(cx, 0), (cx + 12, ch * 0.45), (cx, ch)])
        pygame.draw.polygon(s, shade_rgb(col, 1.35), [(cx, 4), (cx - 12, ch * 0.45), (cx - 3, ch * 0.45)])
    elif kind == 'lollipop':
        hue = [(255, 90, 140), (90, 200, 255), (255, 200, 60), (160, 110, 255), (110, 230, 150), (255, 140, 60)][var % 6]
        pygame.draw.rect(s, (245, 245, 245), (int(cx - 2), 30, 4, ch - 30))
        pygame.draw.circle(s, (255, 255, 255), (int(cx), 22), 21)
        pygame.draw.circle(s, hue, (int(cx), 22), 17)
        pygame.draw.circle(s, (255, 255, 255), (int(cx), 22), 11)
        pygame.draw.circle(s, hue, (int(cx), 22), 6)
    elif kind == 'icecream':
        pygame.draw.polygon(s, (224, 169, 106), [(cx - 13, 40), (cx + 13, 40), (cx, ch)])
        for k in range(3):
            pygame.draw.line(s, (190, 135, 80), (cx - 11 + k * 11, 42), (cx - 3 + k * 4, ch - 8), 1)
        sc = [(255, 158, 196), (255, 235, 160), (150, 220, 255)][var % 3]
        pygame.draw.circle(s, sc, (int(cx), 30), 15)
        pygame.draw.circle(s, shade_rgb(sc, 1.15), (int(cx - 4), 25), 6)
        pygame.draw.circle(s, (221, 34, 51), (int(cx), 12), 4)
    return s


class ThemeGfx(object):
    """하나의 맵 테마를 그리는 데 필요한 모든 캐시"""

    def __init__(self, th, seed, rw, rh, f, far):
        self.th = th
        self.rw, self.rh, self.f, self.far = rw, rh, f, far
        self.night = bool(th.get('night'))
        self.fog = hex_rgb(th['fog'])
        self.sky_top = hex_rgb(th['sky_top'])
        self.sky_bot = hex_rgb(th['sky_bot'])
        self.sprites = {}
        self.scaled = {}
        self._make_palette()
        self._make_fog_lut()
        self.sky = self._make_sky()
        self.pano = self._make_pano(seed)
        self.skyfx = self._make_skyfx(seed)
        self.glow = self._make_glow()
        self.sun_az = math.atan2(th['sun_dir'][0], th['sun_dir'][2])
        sd = th['sun_dir']
        self.sun_el = math.asin(sd[1] / math.sqrt(sd[0] ** 2 + sd[1] ** 2 + sd[2] ** 2))

    # ---- 색상표 -----------------------------------------------------------------
    def _make_palette(self):
        th = self.th
        amb = 0.86 if self.night else 1.0
        glow = bool(th.get('glow_wall'))
        road = hex_rgb(th['road'])
        g0, g1 = hex_rgb(th['ground'][0]), hex_rgb(th['ground'][1])
        w0, w1 = hex_rgb(th['wall'][0]), hex_rgb(th['wall'][1])
        wk = 1.0 if glow else amb
        base = {
            'road_a': shade_rgb(road, amb), 'road_b': shade_rgb(road, amb * 1.13),
            'grass_a': shade_rgb(g0, amb), 'grass_b': shade_rgb(g1, amb),
            'skirt_a': shade_rgb(g0, amb * 0.78), 'skirt_b': shade_rgb(g1, amb * 0.72),
            'kerb_r': shade_rgb((216, 35, 42), amb), 'kerb_w': shade_rgb((240, 240, 240), amb),
            'wall_a': shade_rgb(w0, wk * 0.95), 'wall_b': shade_rgb(w1, wk * 0.95),
            'wall_a2': shade_rgb(w0, wk * 0.74), 'wall_b2': shade_rgb(w1, wk * 0.74),
            'wall_top': shade_rgb((226, 226, 232), wk),
            'dash': (110, 220, 255) if self.night else (246, 246, 246),
            'line': (255, 255, 255),
            'far': hex_rgb(th['far']),
        }
        self.pal = {}
        for name, c in base.items():
            self.pal[name] = [fog_mix(c, self.fog, (i / (FOGN - 1.0)) * 0.94) for i in range(FOGN)]
        self.ground_far = fog_mix(shade_rgb(g0, amb * 0.9), self.fog, 0.55)

    def _make_fog_lut(self):
        far = self.far
        self.fog_lut = []
        for d in range(int(far) + 4):
            t = clamp((d - 0.12 * far) / (0.88 * far), 0.0, 1.0) ** 1.2
            self.fog_lut.append(min(FOGN - 1, int(t * FOGN)))

    # ---- 하늘 ----------------------------------------------------------------------
    def _make_sky(self):
        h = int(self.rh * 1.9)
        s = pygame.Surface((self.rw, h))
        for y in range(h):
            t = y / float(h - 1)          # 0 위 -> 1 지평선
            c = mix_rgb(self.sky_top, self.sky_bot, t ** 0.55)
            pygame.draw.line(s, c, (0, y), (self.rw, y))
        return s

    def _make_glow(self):
        r = max(24, int(self.rh * 0.22))
        s = _surf(r * 2, r * 2)
        sc = hex_rgb(self.th['sun'])
        for i in range(r, 0, -2):
            a = int(120 * (1 - i / float(r)) ** 2)
            pygame.draw.circle(s, (sc[0], sc[1], sc[2], a), (r, r), i)
        return s

    def _make_skyfx(self, seed):
        pw = max(64, int(TAU * self.f))
        ph = int(self.rh * 0.95)
        s = _surf(pw, ph)
        rnd = Rng(seed ^ 0x1234567)
        if self.night:
            for _ in range(260):
                x, y = int(rnd() * pw), int(rnd() * ph * 0.95)
                b = int(120 + rnd() * 135)
                s.set_at((x, y), (b, b, min(255, b + 20), 255))
                if rnd() < 0.18:
                    s.set_at((min(pw - 1, x + 1), y), (b, b, b, 200))
        n = int(7 * self.th.get('clouds', 0))
        if n:
            cc = (255, 240, 250, 205) if self.th['key'] == 'candy' else (255, 255, 255, 190)
            for _ in range(n):
                x = rnd() * pw
                y = ph * (0.18 + rnd() * 0.5)
                sz = (0.5 + rnd()) * self.rh * 0.12
                for j in range(5):
                    _ell(s, cc, (x + (j - 2) * sz * 0.7) % pw, y + (j % 2) * sz * 0.12, sz * (0.9 - 0.12 * abs(j - 2)), sz * 0.36)
        return s

    # ---- 파노라마 (360도 배경) ------------------------------------------------------
    def _make_pano(self, seed):
        th = self.th
        pw = max(64, int(TAU * self.f))
        ph = int(self.rh * 0.36)
        s = _surf(pw, ph)
        rnd = Rng(seed ^ 0x5bd1e995)
        skyb = self.sky_bot
        fog = self.fog
        key = th['key']

        def ridge(color, base, amp, harm=(1, 2, 3, 5, 8, 13), step=3):
            phs = [rnd() * TAU for _ in harm]
            pts = [(0, ph)]
            for x in range(0, pw + step, step):
                a = min(x, pw) / float(pw) * TAU
                h = base
                for k, p in zip(harm, phs):
                    h += amp / (k ** 0.8) * math.sin(k * a + p)
                pts.append((min(x, pw), ph - max(2, h)))
            pts.append((pw, ph))
            pygame.draw.polygon(s, color, pts)
            return pts

        far_c = mix_rgb(skyb, fog, 0.5)
        if key in ('forest', 'autumn'):
            col1 = (110, 140, 170) if key == 'forest' else (190, 150, 110)
            ridge(mix_rgb(col1, skyb, 0.5), ph * 0.55, ph * 0.28)
            c2 = (60, 110, 80) if key == 'forest' else (150, 95, 50)
            ridge(mix_rgb(c2, fog, 0.35), ph * 0.34, ph * 0.18)
            for _ in range(int(pw / 14)):
                x = rnd() * pw
                hh = 6 + rnd() * 10
                base_y = ph - ph * 0.30 + (rnd() - 0.5) * 8
                pygame.draw.polygon(s, mix_rgb(c2, fog, 0.15), [(x - 4, base_y + 6), (x + 4, base_y + 6), (x, base_y - hh)])
        elif key == 'desert':
            ridge(mix_rgb((200, 160, 100), skyb, 0.5), ph * 0.30, ph * 0.14, (1, 2, 3, 4))
            for _ in range(3):
                x = rnd() * pw
                b = 22 + rnd() * 18
                pygame.draw.polygon(s, mix_rgb((190, 150, 95), fog, 0.35), [(x - b, ph - 8), (x + b, ph - 8), (x, ph - 8 - b * 0.9)])
            ridge(mix_rgb((214, 176, 110), fog, 0.2), ph * 0.2, ph * 0.1, (1, 2, 4, 6))
        elif key == 'snow':
            snow = ridge((246, 250, 255), ph * 0.62, ph * 0.32)
            low = [(x, y + 15) for x, y in snow]
            low[0] = (0, ph)
            low[-1] = (pw, ph)
            pygame.draw.polygon(s, mix_rgb((120, 150, 190), skyb, 0.4), low)
            ridge(mix_rgb((95, 125, 105), fog, 0.45), ph * 0.26, ph * 0.12)
        elif key == 'neon':
            for layer, (col, hmax, wmax) in enumerate((((44, 22, 84), ph * 0.8, 26), ((22, 14, 52), ph * 0.55, 34))):
                x = 0
                while x < pw:
                    bw = 10 + rnd() * wmax
                    bh = 8 + rnd() * hmax
                    pygame.draw.rect(s, col, (x, ph - bh, bw, bh))
                    for wy in range(int(ph - bh + 4), ph - 3, 6):
                        for wx in range(int(x + 3), int(x + bw - 3), 5):
                            if rnd() < (0.25 if layer == 0 else 0.4):
                                pygame.draw.rect(s, [(255, 225, 120), (120, 220, 255), (255, 90, 220)][int(rnd() * 3)], (wx, wy, 2, 2))
                    if rnd() < 0.2:
                        pygame.draw.line(s, (255, 60, 90), (x + bw / 2, ph - bh), (x + bw / 2, ph - bh - 7), 1)
                    x += bw + rnd() * 4
        elif key == 'volcano':
            ridge((46, 22, 18), ph * 0.40, ph * 0.16)
            for _ in range(2):
                x = rnd() * pw
                b = 46 + rnd() * 30
                top = ph - ph * 0.88
                pygame.draw.polygon(s, (52, 26, 20), [(x - b, ph), (x + b, ph), (x + 10, top), (x - 10, top)])
                pygame.draw.polygon(s, (255, 110, 30), [(x - 10, top), (x + 10, top), (x + 5, top + 12), (x - 5, top + 9)])
                pygame.draw.line(s, (255, 130, 40), (x - 2, top + 8), (x - 8, ph), 2)
            ridge((34, 18, 16), ph * 0.2, ph * 0.1)
        elif key == 'tropic':
            sea = (30, 168, 200)
            pygame.draw.rect(s, mix_rgb(sea, skyb, 0.25), (0, ph - int(ph * 0.34), pw, int(ph * 0.34)))
            for _ in range(5):
                x = rnd() * pw
                w_ = 30 + rnd() * 50
                pygame.draw.ellipse(s, mix_rgb((70, 150, 100), fog, 0.35), (int(x - w_), ph - int(ph * 0.34) - 8, int(w_ * 2), 18))
            ridge(mix_rgb((235, 215, 160), fog, 0.2), ph * 0.14, ph * 0.04, (1, 3, 5))
        elif key == 'candy':
            ridge(mix_rgb((255, 190, 225), skyb, 0.35), ph * 0.48, ph * 0.22)
            ridge(mix_rgb((190, 240, 255), fog, 0.3), ph * 0.28, ph * 0.14)
            for _ in range(int(pw / 90)):
                x = rnd() * pw
                c = [(255, 90, 140), (90, 200, 255), (255, 200, 60)][int(rnd() * 3)]
                pygame.draw.line(s, (255, 255, 255), (x, ph), (x, ph - 34), 2)
                pygame.draw.circle(s, c, (int(x), ph - 38), 9)
                pygame.draw.circle(s, (255, 255, 255), (int(x), ph - 38), 4)
        elif key == 'space':
            ridge((70, 70, 80), ph * 0.34, ph * 0.18)
            px_ = rnd() * pw
            pygame.draw.circle(s, (58, 111, 208), (int(px_), int(ph * 0.45)), int(ph * 0.34))
            pygame.draw.circle(s, (30, 70, 150), (int(px_ + ph * 0.1), int(ph * 0.5)), int(ph * 0.26))
            pygame.draw.ellipse(s, (200, 184, 144), (int(px_ - ph * 0.6), int(ph * 0.4), int(ph * 1.2), int(ph * 0.14)), 2)
            ridge((92, 92, 104), ph * 0.18, ph * 0.1, (1, 2, 4, 7))
        elif key == 'canyon':
            for layer, (col, hmax) in enumerate((((150, 70, 50), ph * 0.8), ((120, 52, 36), ph * 0.55))):
                x = 0
                while x < pw:
                    bw = 30 + rnd() * 80
                    bh = hmax * (0.35 + rnd() * 0.65)
                    c = mix_rgb(col, fog, 0.3 - layer * 0.15)
                    pygame.draw.rect(s, c, (x, ph - bh, bw, bh))
                    pygame.draw.rect(s, shade_rgb(c, 1.2), (x, ph - bh, bw, 3))
                    pygame.draw.rect(s, shade_rgb(c, 0.8), (x + bw * 0.65, ph - bh, bw * 0.35, bh))
                    if rnd() < 0.5:
                        pygame.draw.rect(s, c, (x + bw * 0.2, ph - bh - 10, bw * 0.5, 10))
                    x += bw * (0.5 + rnd() * 0.6)
        return s

    # ---- 장식물 스프라이트 --------------------------------------------------------------
    def sprite(self, kind, var):
        k = (kind, var)
        sp = self.sprites.get(k)
        if sp is None:
            sp = self.sprites[k] = make_sprite(kind, self.th, var)
        return sp

    def scaled_sprite(self, kind, var, wpx, hpx):
        """월드 크기를 화면 픽셀 크기로 맞춘 스프라이트 (로그 간격 양자화 캐시: 크기가 연속으로 변해도 캐시 적중)"""
        qw = max(2, int(_QB ** round(math.log(max(wpx, 1.0)) / _QL)))
        qh = max(2, int(_QB ** round(math.log(max(hpx, 1.0)) / _QL)))
        key = (kind, var, qw, qh)
        sp = self.scaled.get(key)
        if sp is None:
            if len(self.scaled) > 1200:
                self.scaled.clear()
            sp = self.scaled[key] = pygame.transform.scale(self.sprite(kind, var), (qw, qh))
        return sp


_QB = 1.12
_QL = math.log(_QB)
