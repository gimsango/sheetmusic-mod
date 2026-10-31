
# ============================================================================
#  [폰] 언어 / 폰트 / 포인터(터치) / 즉시모드 UI 위젯 / 온스크린 키보드
# ============================================================================
LANG = 'ko'


def T(ko, en):
    return ko if LANG == 'ko' else en


FONT_DIRS = ['/system/fonts', '/system/font', '/product/fonts', '/data/fonts', '/usr/share/fonts', '/System/Library/Fonts',
             'C:/Windows/Fonts', '/Library/Fonts']
FONT_HINTS = ('cjk', 'korean', 'nanum', 'malgun', 'gothic', 'hangul', 'notosanskr', 'sansfallback', 'applesd', 'wqy', 'unifont', 'seckorean')
FONT_FIRST = ['kart3d_font.ttf', 'kart3d_font.otf', 'kart3d_font.ttc',
              '/system/fonts/NotoSansCJK-Regular.ttc', '/system/fonts/NotoSansCJKkr-Regular.otf', '/system/fonts/NotoSansKR-Regular.otf',
              '/system/fonts/NotoSansKR-Regular.ttf', '/system/fonts/NanumGothic.ttf', '/system/fonts/DroidSansFallback.ttf',
              'C:/Windows/Fonts/malgun.ttf', '/System/Library/Fonts/AppleSDGothicNeo.ttc', '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
              '/usr/share/fonts/truetype/nanum/NanumGothic.ttf', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
              '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc']


def has_hangul(path):
    try:
        f = pygame.font.Font(path, 24)
        a = f.render('\ud55c\uae00', False, (255, 255, 255))
        b = f.render('\uffff\uffff', False, (255, 255, 255))
        return a.get_width() > 8 and pygame.image.tostring(a, 'RGBA') != pygame.image.tostring(b, 'RGBA')
    except Exception:
        return False


def find_korean_font():
    tried = set()

    def ok(p):
        if p in tried:
            return False
        tried.add(p)
        return os.path.isfile(p) and has_hangul(p)
    try:
        here = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv and sys.argv[0] else '.'
    except Exception:
        here = '.'
    for p in FONT_FIRST:
        if not os.path.isabs(p):
            p = os.path.join(here, p)
        if ok(p):
            return p
    for d in FONT_DIRS:
        try:
            names = []
            for root, _dirs, files in os.walk(d):
                for fn in files:
                    low = fn.lower()
                    if low.endswith(('.ttf', '.otf', '.ttc')) and any(h in low for h in FONT_HINTS):
                        names.append(os.path.join(root, fn))
                if len(names) > 60:
                    break
            for p in sorted(names):
                if ok(p):
                    return p
        except Exception:
            continue
    return None


def rrect(surf, color, rect, r):
    try:
        pygame.draw.rect(surf, color, rect, border_radius=int(r))
    except TypeError:
        pygame.draw.rect(surf, color, rect)


class Pointers(object):
    """터치/마우스 입력 통합. 손가락 여러 개를 동시에 추적한다."""

    def __init__(self):
        self.fingers = {}
        self.mouse = None
        self.taps = []
        self._last_tap = (0.0, -999, -999)
        self.has_touch = False

    def _tap(self, x, y):
        t = time.time()
        lt = self._last_tap
        if t - lt[0] < 0.18 and abs(x - lt[1]) < 40 and abs(y - lt[2]) < 40:
            return                      # 터치 + 에뮬레이트된 마우스 이벤트 중복 제거
        self._last_tap = (t, x, y)
        self.taps.append((x, y))

    def handle(self, e, sw, sh):
        et = e.type
        if hasattr(pygame, 'FINGERDOWN') and et in (pygame.FINGERDOWN, pygame.FINGERMOTION):
            self.has_touch = True
            self.fingers[e.finger_id] = (e.x * sw, e.y * sh)
        elif hasattr(pygame, 'FINGERUP') and et == pygame.FINGERUP:
            self.has_touch = True
            p = self.fingers.pop(e.finger_id, (e.x * sw, e.y * sh))
            self._tap(p[0], p[1])
        elif et == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.mouse = e.pos
        elif et == pygame.MOUSEMOTION and self.mouse is not None:
            self.mouse = e.pos
        elif et == pygame.MOUSEBUTTONUP and e.button == 1:
            self.mouse = None
            self._tap(e.pos[0], e.pos[1])

    def down(self):
        pts = list(self.fingers.values())
        if self.mouse is not None:
            pts.append(self.mouse)
        return pts

    def take_taps(self):
        t = self.taps
        self.taps = []
        return t


class UI(object):
    """즉시모드 위젯: 그리면서 동시에 탭 여부를 돌려준다."""

    def __init__(self, font_path):
        self.font_path = font_path
        self.fonts = {}
        self.cache = {}
        self.panels = {}
        self.taps = []
        self.down = []
        self.u = 1.0

    def begin(self, taps, down, sw, sh):
        self.taps = taps
        self.down = down
        self.sw, self.sh = sw, sh
        self.u = min(sw, sh) / 540.0

    def font(self, size):
        size = max(8, int(size))
        f = self.fonts.get(size)
        if f is None:
            f = self.fonts[size] = pygame.font.Font(self.font_path, size)
        return f

    def render(self, text, size, color):
        key = (text, int(size), color)
        s = self.cache.get(key)
        if s is None:
            if len(self.cache) > 500:
                self.cache.clear()
            s = self.cache[key] = self.font(size).render(text, True, color)
        return s

    def text(self, surf, text, x, y, size, color=(255, 255, 255), anchor='l', shadow=True):
        s = self.render(text, size, color)
        w, h = s.get_size()
        if anchor == 'c':
            x -= w // 2
        elif anchor == 'r':
            x -= w
        if shadow:
            d = max(1, int(size) // 16)
            surf.blit(self.render(text, size, (0, 0, 0)), (x + d, y + d))
        surf.blit(s, (x, y))
        return w, h

    def panel(self, surf, rect, alpha=175, color=(8, 12, 28), radius=16):
        key = (rect.w, rect.h, alpha, color, radius)
        p = self.panels.get(key)
        if p is None:
            if len(self.panels) > 40:
                self.panels.clear()
            p = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            rrect(p, (color[0], color[1], color[2], alpha), p.get_rect(), radius)
            self.panels[key] = p
        surf.blit(p, rect.topleft)

    def tapped(self, rect):
        for t in self.taps:
            if rect.collidepoint(t):
                self.taps.remove(t)
                return True
        return False

    def pressed(self, rect):
        for p in self.down:
            if rect.collidepoint(p):
                return True
        return False

    def button(self, surf, rect, label, kind='normal', size=None, enabled=True):
        pr = enabled and self.pressed(rect)
        cols = {'normal': ((40, 48, 78), (62, 74, 118)), 'primary': ((236, 70, 70), (255, 120, 60)), 'ghost': ((22, 26, 44), (44, 52, 84)),
                'chip': ((34, 40, 66), (58, 68, 108)), 'chipon': ((25, 190, 225), (80, 225, 250)), 'danger': ((170, 40, 56), (220, 70, 80)),
                'good': ((40, 160, 90), (70, 205, 120))}
        base, hi = cols.get(kind, cols['normal'])
        if not enabled:
            base = hi = (50, 52, 62)
        c = hi if pr else base
        r = rect.inflate(-4, -4) if pr else rect
        rrect(surf, (0, 0, 0), r.move(0, max(2, int(r.h * 0.06))), r.h * 0.28)
        rrect(surf, c, r, r.h * 0.28)
        rrect(surf, shade_rgb(c, 1.25), pygame.Rect(r.x + 3, r.y + 2, r.w - 6, max(2, r.h // 8)), r.h * 0.1)
        if size is None:
            size = r.h * 0.46
        tc = (255, 255, 255) if enabled else (140, 140, 150)
        if kind == 'chipon':
            tc = (6, 20, 34)
        s = self.render(label, size, tc)
        if s.get_width() > r.w - 8:
            size = size * (r.w - 8) / float(s.get_width())
            s = self.render(label, size, tc)
        surf.blit(s, (r.centerx - s.get_width() // 2, r.centery - s.get_height() // 2))
        return enabled and self.tapped(rect)

    def stepper(self, surf, rect, label, value, lo=None, hi=None):
        """[라벨      ◀  값  ▶]  -> -1 / 0 / +1"""
        u = self.u
        self.text(surf, label, rect.x, rect.centery - 11 * u, 22 * u, (210, 220, 245))
        bw = rect.h
        res = 0
        lb = pygame.Rect(rect.right - bw * 3.4, rect.y, bw, rect.h)
        rb = pygame.Rect(rect.right - bw, rect.y, bw, rect.h)
        if self.button(surf, lb, '<', 'normal', enabled=(lo is None or value > lo)):
            res = -1
        if self.button(surf, rb, '>', 'normal', enabled=(hi is None or value < hi)):
            res = 1
        self.text(surf, str(value), (lb.right + rb.x) // 2, rect.centery - 13 * u, 26 * u, (255, 220, 120), 'c')
        return res


class OnScreenKeyboard(object):
    """텍스트/IP 입력용 화면 키보드 (모바일 소프트 키보드가 불안정해서 직접 그린다)"""

    def __init__(self, title, text, mode, maxlen, on_ok):
        self.title, self.text, self.mode, self.maxlen, self.on_ok = title, text, mode, maxlen, on_ok
        self.shift = False
        self.blink = 0.0

    def rows(self):
        if self.mode == 'ip':
            return ['123', '456', '789', '.0:']
        rs = ['1234567890', 'qwertyuiop', 'asdfghjkl-', 'zxcvbnm_.']
        return [r.upper() if self.shift else r for r in rs]

    def key(self, ch):
        if len(self.text) < self.maxlen:
            self.text += ch

    def handle_key_event(self, e):
        if e.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return 'ok'
        elif e.key == pygame.K_ESCAPE:
            return 'cancel'
        elif e.unicode and e.unicode.isprintable() and len(e.unicode) == 1:
            if self.mode != 'ip' or e.unicode in '0123456789.:':
                self.key(e.unicode)
        return None

    def draw(self, ui, surf, sw, sh, dt):
        u = ui.u
        self.blink += dt
        veil = pygame.Surface((sw, sh), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 170))
        surf.blit(veil, (0, 0))
        res = None
        if self.mode == 'ip':
            kw, kh = int(min(sw * 0.5, 120 * u * 3)), int(min(sh * 0.12, 62 * u))
            gx, gy = 4 * u * 2, 4 * u * 2
        else:
            kw, kh = int(min(sw / 11.0, 90 * u)), int(min(sh * 0.11, 60 * u))
            gx, gy = 6 * u, 6 * u
        rows = self.rows()
        ncol = max(len(r) for r in rows)
        total_w = ncol * kw + (ncol - 1) * gx
        total_h = (len(rows) + 1) * kh + len(rows) * gy
        x0 = (sw - total_w) // 2
        y0 = sh - total_h - int(14 * u)
        # 입력창
        box = pygame.Rect(x0, y0 - int(112 * u), total_w, int(92 * u))
        ui.panel(surf, box, 240, (14, 18, 36), 14)
        ui.text(surf, self.title, box.x + 14 * u, box.y + 6 * u, 20 * u, (190, 205, 240))
        shown = self.text + ('|' if int(self.blink * 2) % 2 == 0 else ' ')
        ui.text(surf, shown, box.x + 16 * u, box.y + 36 * u, 34 * u, (255, 255, 255))
        for ri, row in enumerate(rows):
            rw_ = len(row) * kw + (len(row) - 1) * gx
            rx = x0 + (total_w - rw_) // 2
            for ci, ch in enumerate(row):
                r = pygame.Rect(rx + ci * (kw + gx), y0 + ri * (kh + gy), kw, kh)
                if ui.button(surf, r, ch, 'normal', size=kh * 0.5):
                    self.key(ch)
        by = y0 + len(rows) * (kh + gy)
        bw3 = (total_w - 3 * gx) // 4
        specs = []
        if self.mode != 'ip':
            specs.append(('Aa', 'chipon' if self.shift else 'normal', 'shift'))
        else:
            specs.append(('', 'ghost', None))
        specs += [('<-', 'normal', 'bs'), (T('취소', 'Cancel'), 'ghost', 'cancel'), ('OK', 'primary', 'ok')]
        for i, (lab, kind, act) in enumerate(specs):
            r = pygame.Rect(x0 + i * (bw3 + gx), by, bw3, kh)
            if act is None:
                continue
            if ui.button(surf, r, lab, kind, size=kh * 0.46):
                if act == 'shift':
                    self.shift = not self.shift
                elif act == 'bs':
                    self.text = self.text[:-1]
                else:
                    res = act
        ui.taps[:] = []        # 키보드가 떠 있는 동안 다른 위젯이 탭을 받지 않게
        return res
