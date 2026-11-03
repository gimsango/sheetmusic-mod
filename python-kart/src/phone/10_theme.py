
# ============================================================================
#  [폰] 바이옴별 색상표 / 안개 / 하늘(오로라) / 지평선 파노라마 / 장식물 스프라이트 (32종)
# ============================================================================
FOGN = 16


def fog_mix(c, fog, t):
    return (int(c[0] + (fog[0] - c[0]) * t), int(c[1] + (fog[1] - c[1]) * t), int(c[2] + (fog[2] - c[2]) * t))


# kind: (월드 폭 m, 월드 높이 m, 캔버스 폭 px, 캔버스 높이 px)
SPRITE_DIM = {
    'pine': (7.0, 11.0, 70, 110), 'roundtree': (7.5, 9.5, 75, 95), 'bush': (3.4, 2.2, 34, 22), 'cactus': (4.2, 6.5, 42, 65),
    'rock': (6.0, 3.6, 60, 36), 'mesa': (20.0, 24.0, 100, 120), 'palm': (9.0, 10.5, 90, 105), 'building': (1.0, 1.0, 64, 128),
    'crystal': (3.4, 8.0, 34, 80), 'lollipop': (4.4, 7.6, 44, 76), 'icecream': (3.4, 7.6, 34, 76),
    'acacia': (9.0, 7.0, 90, 70), 'deadtree': (6.0, 8.0, 60, 80), 'bamboo': (3.2, 12.0, 32, 120), 'mushroom': (6.0, 7.0, 60, 70),
    'coral': (4.0, 4.4, 40, 44), 'barrel': (3.2, 1.9, 48, 28), 'pillar': (2.6, 10.0, 26, 100), 'haystack': (4.0, 3.0, 40, 30),
    'windmill': (9.0, 14.0, 72, 112), 'flowers': (4.0, 1.4, 48, 17), 'tombstone': (1.6, 2.2, 32, 44), 'pumpkin': (1.9, 1.6, 38, 32),
    'chimney': (8.0, 22.0, 48, 132), 'pyramid': (14.0, 9.0, 112, 72), 'dome': (10.0, 5.6, 100, 56), 'icespike': (3.6, 6.0, 36, 60),
    'lantern': (1.4, 3.4, 20, 48), 'blocks': (4.0, 5.0, 40, 50), 'dish': (5.0, 6.0, 50, 60), 'sunflower': (3.0, 3.6, 36, 44),
    'cloud': (5.0, 3.0, 60, 36),
    # 맵 만들기 장애물/장식
    'cone': (0.75, 0.95, 24, 30), 'drum': (1.25, 1.5, 25, 30), 'crate': (1.8, 1.8, 36, 36), 'tires': (1.9, 1.7, 38, 34),
    'block': (2.3, 1.2, 46, 24), 'lavapillar': (2.8, 9.5, 28, 95), 'volcano': (44.0, 24.0, 132, 72),
}


def _surf(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def _ell(s, c, cx, cy, rx, ry):
    pygame.draw.ellipse(s, c, (int(cx - rx), int(cy - ry), max(1, int(rx * 2)), max(1, int(ry * 2))))


def _rr(s, c, rect, r):
    try:
        pygame.draw.rect(s, c, rect, border_radius=int(r))
    except TypeError:
        pygame.draw.rect(s, c, rect)


def _pal(th, key, default):
    v = th.get(key)
    return v if v else default


def make_sprite(kind, th, var):
    cw, ch = SPRITE_DIM[kind][2], SPRITE_DIM[kind][3]
    s = _surf(cw, ch)
    cx = cw / 2.0
    leaf = _pal(th, 'leaf', [(47, 127, 53), (58, 140, 58), (74, 160, 74), (90, 170, 80)])
    trunk = _pal(th, 'trunk', (90, 59, 34))
    acc = _pal(th, 'accent', [(255, 43, 214), (25, 230, 255), (255, 225, 74), (120, 255, 150)])
    flower = _pal(th, 'flower', [(255, 224, 64), (255, 96, 128), (255, 255, 255), (176, 123, 255)])
    rk = (hex_rgb(th['rock'][0]), hex_rgb(th['rock'][1]))
    night = bool(th.get('night'))
    if kind == 'pine':
        pygame.draw.rect(s, trunk, (int(cx - 4), ch - 20, 8, 20))
        if th.get('snowy'):
            cols = [mix_rgb(leaf[0], (240, 246, 252), 0.15), mix_rgb(leaf[1], (240, 246, 252), 0.35), (242, 247, 251)]
        else:
            cols = [leaf[0], leaf[1], leaf[2]]
        for (by, hw_, h_), c in zip(((ch - 14, 34, 44), (ch - 40, 28, 38), (ch - 64, 21, 34)), cols):
            pygame.draw.polygon(s, c, [(cx - hw_, by), (cx + hw_, by), (cx, by - h_)])
            pygame.draw.polygon(s, shade_rgb(c, 0.7), [(cx, by - h_), (cx + hw_, by), (cx, by)])
    elif kind == 'roundtree':
        c = leaf[var % len(leaf)]
        pygame.draw.rect(s, trunk, (int(cx - 5), ch - 40, 10, 40))
        _ell(s, shade_rgb(c, 0.72), cx + 4, ch - 56, 33, 30)
        _ell(s, c, cx - 2, ch - 58, 31, 29)
        _ell(s, shade_rgb(c, 1.18), cx - 10, ch - 68, 16, 13)
        if th.get('snowy'):
            _ell(s, (240, 246, 252), cx - 4, ch - 80, 18, 7)
    elif kind == 'bush':
        _ell(s, shade_rgb(leaf[0], 0.85), cx + 2, ch - 8, 15, 9)
        _ell(s, leaf[1], cx - 3, ch - 9, 14, 9)
        _ell(s, shade_rgb(leaf[2], 1.1), cx - 6, ch - 12, 7, 4)
    elif kind == 'cactus':
        g = th.get('cactus') or (59, 138, 74)
        pygame.draw.rect(s, g, (int(cx - 7), 6, 14, ch - 6), border_radius=6)
        pygame.draw.rect(s, shade_rgb(g, 0.72), (int(cx + 1), 8, 6, ch - 10), border_radius=3)
        pygame.draw.rect(s, g, (int(cx - 20), 28, 20, 8), border_radius=3)
        pygame.draw.rect(s, g, (int(cx - 22), 14, 8, 22), border_radius=4)
        pygame.draw.rect(s, g, (int(cx + 5), 36, 18, 8), border_radius=3)
        pygame.draw.rect(s, g, (int(cx + 15), 22, 8, 22), border_radius=4)
    elif kind == 'rock':
        c0, c1 = rk
        pygame.draw.polygon(s, c0, [(2, ch), (8, 14), (24, 2), (44, 6), (58, 22), (58, ch)])
        pygame.draw.polygon(s, c1, [(30, 4), (44, 6), (58, 22), (58, ch), (32, ch), (34, 18)])
        pygame.draw.polygon(s, shade_rgb(c0, 1.2), [(8, 14), (24, 2), (30, 4), (20, 20)])
    elif kind == 'mesa':
        mc = _pal(th, 'mesa', [(176, 74, 40), (199, 101, 58), (168, 68, 36), (224, 160, 96)])
        for c, pts in ((mc[0], [(0, ch), (14, 46), (86, 46), (100, ch)]), (mc[1], [(12, 62), (18, 24), (82, 24), (90, 62)]),
                       (mc[2], [(22, 30), (26, 8), (74, 8), (78, 30)]), (mc[3], [(26, 10), (28, 4), (72, 4), (74, 10)])):
            pygame.draw.polygon(s, c, pts)
        pygame.draw.polygon(s, shade_rgb(mc[0], 0.68), [(60, 8), (100, ch), (70, ch)])
    elif kind == 'palm':
        tc = mix_rgb(trunk, (200, 170, 110), 0.45)
        pygame.draw.polygon(s, tc, [(cx - 5, ch), (cx + 3, ch), (cx + 8, 22), (cx + 2, 22)])
        for k in range(6):
            c = leaf[k % len(leaf)]
            a = -2.7 + k * 0.54
            ex, ey = cx + 6 + math.cos(a) * 40, 22 + math.sin(a) * 22 + 12
            mx, my = cx + 6 + math.cos(a) * 20, 22 + math.sin(a) * 20 - 6
            pygame.draw.polygon(s, c, [(cx + 6, 22), (mx - 3, my - 5), (ex, ey), (mx + 3, my + 5)])
        pygame.draw.circle(s, shade_rgb(trunk, 0.9), (int(cx + 6), 24), 4)
    elif kind == 'building':
        c = acc[var % len(acc)]
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
        if not night:
            pygame.draw.rect(s, (60, 60, 80), (0, 0, cw, ch), 2)
    elif kind == 'crystal':
        col = th.get('crystal') or (255, 43, 214)
        pygame.draw.polygon(s, col, [(cx, 0), (cx + 12, ch * 0.45), (cx, ch), (cx - 12, ch * 0.45)])
        pygame.draw.polygon(s, shade_rgb(col, 0.62), [(cx, 0), (cx + 12, ch * 0.45), (cx, ch)])
        pygame.draw.polygon(s, shade_rgb(col, 1.35), [(cx, 4), (cx - 12, ch * 0.45), (cx - 3, ch * 0.45)])
    elif kind == 'lollipop':
        hue = acc[var % len(acc)]
        pygame.draw.rect(s, (245, 245, 245), (int(cx - 2), 30, 4, ch - 30))
        pygame.draw.circle(s, (255, 255, 255), (int(cx), 22), 21)
        pygame.draw.circle(s, hue, (int(cx), 22), 17)
        pygame.draw.circle(s, (255, 255, 255), (int(cx), 22), 11)
        pygame.draw.circle(s, hue, (int(cx), 22), 6)
    elif kind == 'icecream':
        pygame.draw.polygon(s, (224, 169, 106), [(cx - 13, 40), (cx + 13, 40), (cx, ch)])
        for k in range(3):
            pygame.draw.line(s, (190, 135, 80), (cx - 11 + k * 11, 42), (cx - 3 + k * 4, ch - 8), 1)
        sc = mix_rgb(acc[(var + 1) % len(acc)], (255, 255, 255), 0.45)
        pygame.draw.circle(s, sc, (int(cx), 30), 15)
        pygame.draw.circle(s, shade_rgb(sc, 1.15), (int(cx - 4), 25), 6)
        pygame.draw.circle(s, (221, 34, 51), (int(cx), 12), 4)
    elif kind == 'acacia':
        pygame.draw.polygon(s, trunk, [(cx - 4, ch), (cx + 3, ch), (cx + 9, ch * 0.34), (cx + 4, ch * 0.34)])
        pygame.draw.line(s, trunk, (int(cx + 2), int(ch * 0.62)), (int(cx - 14), int(ch * 0.34)), 3)
        c = leaf[var % len(leaf)]
        _ell(s, shade_rgb(c, 0.7), cx + 4, ch * 0.33, 42, 9)
        _ell(s, c, cx + 2, ch * 0.27, 43, 10)
        _ell(s, shade_rgb(c, 1.18), cx - 8, ch * 0.22, 20, 6)
        if var:
            _ell(s, c, cx - 16, ch * 0.4, 18, 5)
    elif kind == 'deadtree':
        pygame.draw.polygon(s, trunk, [(cx - 5, ch), (cx + 5, ch), (cx + 2, ch * 0.3), (cx - 2, ch * 0.3)])
        rnd = Rng(var * 31 + 7)
        for k in range(5):
            y0 = ch * (0.35 + 0.1 * k)
            sgn = -1 if (k + var) % 2 else 1
            ex = cx + sgn * (12 + rnd() * 14)
            ey = y0 - 10 - rnd() * 16
            pygame.draw.line(s, trunk, (int(cx), int(y0)), (int(ex), int(ey)), max(1, 4 - k // 2))
            pygame.draw.line(s, trunk, (int(ex), int(ey)), (int(ex + sgn * 6), int(ey - 8)), 1)
    elif kind == 'bamboo':
        rnd = Rng(17)
        for k in range(5):
            x = 3 + k * 6 + int(rnd() * 3)
            top = int(4 + rnd() * 20)
            c = shade_rgb(trunk, 0.85 + 0.25 * rnd())
            pygame.draw.rect(s, c, (x, top, 4, ch - top))
            for y in range(top + 10, ch, 13):
                pygame.draw.line(s, shade_rgb(c, 0.6), (x, y), (x + 3, y), 1)
            _ell(s, leaf[k % len(leaf)], x + 2 + (k % 2) * 4 - 2, top + 3, 6, 3)
            _ell(s, leaf[(k + 1) % len(leaf)], x - 2, top + 16, 5, 2)
    elif kind == 'mushroom':
        cap = acc[var % len(acc)]
        _rr(s, trunk, (int(cx - 7), int(ch * 0.42), 14, int(ch * 0.58)), 5)
        _ell(s, shade_rgb(trunk, 0.8), cx + 3, ch * 0.75, 3, 12)
        _ell(s, shade_rgb(cap, 0.65), cx, ch * 0.42, 27, 9)
        pygame.draw.ellipse(s, cap, (int(cx - 28), 2, 56, int(ch * 0.8)))
        pygame.draw.rect(s, (0, 0, 0, 0), (0, int(ch * 0.42), cw, ch))
        _rr(s, trunk, (int(cx - 7), int(ch * 0.42), 14, int(ch * 0.58)), 5)
        _ell(s, shade_rgb(cap, 0.6), cx, ch * 0.42, 26, 4)
        for (dx, dy, r_) in ((-12, 0.2, 4), (6, 0.12, 5), (16, 0.3, 3), (-2, 0.32, 3)):
            pygame.draw.circle(s, (255, 255, 255), (int(cx + dx), int(ch * dy)), r_)
    elif kind == 'coral':
        c = acc[var % len(acc)]
        rnd = Rng(var * 13 + 5)
        for k in range(6):
            x = 4 + k * 6
            h = int(ch * (0.4 + rnd() * 0.55))
            cc = shade_rgb(c, 0.8 + rnd() * 0.4)
            _rr(s, cc, (x, ch - h, 6, h), 3)
            pygame.draw.circle(s, shade_rgb(cc, 1.25), (x + 3, ch - h + 2), 4)
    elif kind == 'barrel':
        bc = acc[1] if len(acc) > 1 and acc[1][0] > 150 else (230, 200, 40)
        for k in range(3):
            x = 2 + k * 15
            _rr(s, bc, (x, 4, 13, ch - 4), 3)
            pygame.draw.rect(s, (40, 40, 40), (x, 9, 13, 2))
            pygame.draw.rect(s, (40, 40, 40), (x, ch - 8, 13, 2))
            pygame.draw.circle(s, (30, 30, 30), (x + 6, ch // 2 + 2), 3)
    elif kind == 'pillar':
        pc = mix_rgb(rk[0], (235, 230, 215), 0.4)
        top = 8 if var == 0 else 26
        pygame.draw.rect(s, shade_rgb(pc, 0.85), (2, ch - 8, cw - 4, 8))
        pygame.draw.rect(s, pc, (5, top, cw - 10, ch - top - 8))
        for x in range(8, cw - 6, 4):
            pygame.draw.line(s, shade_rgb(pc, 0.78), (x, top + 2), (x, ch - 10), 1)
        if var == 0:
            pygame.draw.rect(s, shade_rgb(pc, 1.08), (1, 2, cw - 2, 7))
        else:
            pygame.draw.polygon(s, pc, [(5, top), (cw - 5, top), (cw - 8, top - 6), (10, top - 3)])
    elif kind == 'haystack':
        hc = (224, 186, 94)
        _ell(s, shade_rgb(hc, 0.8), cx + 2, ch - 12, 19, 13)
        _ell(s, hc, cx - 1, ch - 13, 18, 13)
        for k in range(4):
            pygame.draw.arc(s, shade_rgb(hc, 0.75), (int(cx - 15 + k * 3), int(ch - 24 + k * 3), 30 - k * 6, 22 - k * 4), 0.3, 2.8, 1)
    elif kind == 'windmill':
        wc = (232, 226, 214)
        pygame.draw.polygon(s, wc, [(cx - 14, ch), (cx + 14, ch), (cx + 8, ch * 0.32), (cx - 8, ch * 0.32)])
        pygame.draw.polygon(s, shade_rgb(wc, 0.8), [(cx + 2, ch), (cx + 14, ch), (cx + 8, ch * 0.32), (cx + 2, ch * 0.32)])
        pygame.draw.polygon(s, (150, 52, 40), [(cx - 11, ch * 0.33), (cx + 11, ch * 0.33), (cx, ch * 0.22)])
        pygame.draw.rect(s, (90, 60, 40), (int(cx - 4), ch - 14, 8, 14))
        hy = int(ch * 0.3)
        for a in (0.6, 2.17, 3.74, 5.31):
            ex, ey = cx + math.cos(a) * 32, hy + math.sin(a) * 32
            pygame.draw.line(s, (120, 90, 60), (int(cx), hy), (int(ex), int(ey)), 2)
            px_, py_ = -math.sin(a) * 5, math.cos(a) * 5
            pygame.draw.polygon(s, (245, 240, 230), [(cx + math.cos(a) * 8, hy + math.sin(a) * 8), (ex, ey), (ex + px_, ey + py_),
                                                    (cx + math.cos(a) * 8 + px_, hy + math.sin(a) * 8 + py_)])
        pygame.draw.circle(s, (80, 60, 40), (int(cx), hy), 3)
    elif kind == 'flowers':
        _ell(s, shade_rgb(leaf[1], 0.9), cx, ch - 5, 23, 6)
        rnd = Rng(var * 7 + 3)
        fc = flower[var % len(flower)]
        for _ in range(11):
            x = cx + (rnd() - 0.5) * 40
            y = ch - 6 - rnd() * 9
            pygame.draw.circle(s, fc, (int(x), int(y)), 3)
            pygame.draw.circle(s, mix_rgb(fc, (255, 255, 255), 0.6), (int(x), int(y)), 1)
    elif kind == 'tombstone':
        gc = mix_rgb(rk[0], (150, 150, 155), 0.4)
        if var == 0:
            _rr(s, gc, (6, 4, cw - 12, ch - 4), 10)
            pygame.draw.line(s, shade_rgb(gc, 0.6), (11, 18), (cw - 11, 18), 2)
            pygame.draw.line(s, shade_rgb(gc, 0.6), (11, 25), (cw - 13, 25), 2)
        else:
            pygame.draw.rect(s, gc, (int(cx - 4), 2, 8, ch - 2))
            pygame.draw.rect(s, gc, (int(cx - 12), 12, 24, 7))
        pygame.draw.rect(s, shade_rgb(gc, 0.7), (2, ch - 4, cw - 4, 4))
    elif kind == 'pumpkin':
        pc = (236, 120, 24)
        _ell(s, shade_rgb(pc, 0.8), cx - 9, ch - 12, 9, 11)
        _ell(s, shade_rgb(pc, 0.8), cx + 9, ch - 12, 9, 11)
        _ell(s, pc, cx, ch - 12, 11, 12)
        pygame.draw.rect(s, (70, 110, 40), (int(cx - 2), 2, 4, 7))
        if night:
            pygame.draw.polygon(s, (255, 220, 80), [(cx - 8, ch - 16), (cx - 3, ch - 16), (cx - 5, ch - 20)])
            pygame.draw.polygon(s, (255, 220, 80), [(cx + 3, ch - 16), (cx + 8, ch - 16), (cx + 5, ch - 20)])
            pygame.draw.rect(s, (255, 220, 80), (int(cx - 7), ch - 10, 14, 3))
    elif kind == 'chimney':
        bc = (122, 72, 52)
        pygame.draw.rect(s, bc, (0, int(ch * 0.62), cw, int(ch * 0.38)))
        pygame.draw.rect(s, shade_rgb(bc, 0.8), (int(cw * 0.55), 6, 14, ch))
        pygame.draw.rect(s, acc[0], (int(cw * 0.55) - 1, 10, 16, 4))
        rnd = Rng(11)
        for y in range(int(ch * 0.66), ch - 6, 9):
            for x in range(4, cw - 6, 9):
                if rnd() < 0.6:
                    pygame.draw.rect(s, (255, 200, 110) if night or rnd() < 0.3 else (50, 40, 36), (x, y, 5, 5))
    elif kind == 'pyramid':
        pc = mix_rgb(rk[0], (230, 200, 140), 0.35)
        pygame.draw.polygon(s, pc, [(0, ch), (cw, ch), (cx, 0)])
        pygame.draw.polygon(s, shade_rgb(pc, 0.72), [(cx, 0), (cw, ch), (cx + 18, ch)])
        for k in range(1, 8):
            y = ch * k / 8.0
            pygame.draw.line(s, shade_rgb(pc, 0.85), (cx - (cx * y / ch), y), (cx + (cx * y / ch), y), 1)
    elif kind == 'dome':
        gl = (170, 220, 255, 210)
        pygame.draw.ellipse(s, gl, (6, 4, cw - 12, (ch - 10) * 2))
        pygame.draw.rect(s, (0, 0, 0, 0), (0, ch - 8, cw, 8))
        pygame.draw.ellipse(s, (220, 240, 255), (6, 4, cw - 12, (ch - 10) * 2), 2)
        for k in range(1, 4):
            pygame.draw.line(s, (220, 240, 255), (6 + (cw - 12) * k / 4.0, 8 + abs(2 - k) * 6), (6 + (cw - 12) * k / 4.0, ch - 8), 1)
        pygame.draw.rect(s, (150, 150, 160), (2, ch - 8, cw - 4, 8))
        pygame.draw.rect(s, (255, 230, 140) if night else (120, 200, 255), (int(cx - 6), ch - 18, 12, 10))
    elif kind == 'icespike':
        ic = th.get('crystal') or (180, 225, 255)
        ic = mix_rgb(ic, (230, 245, 255), 0.4)
        for (x, w_, h_) in ((cx - 9, 7, 0.7), (cx + 6, 8, 0.9), (cx - 1, 9, 1.0), (cx + 13, 5, 0.5)):
            pygame.draw.polygon(s, ic, [(x - w_, ch), (x + w_, ch), (x, ch * (1 - h_))])
            pygame.draw.polygon(s, shade_rgb(ic, 0.78), [(x, ch * (1 - h_)), (x + w_, ch), (x, ch)])
    elif kind == 'lantern':
        lc = acc[0] if acc else (255, 120, 60)
        pygame.draw.rect(s, (110, 110, 112), (int(cx - 2), 18, 4, ch - 18))
        pygame.draw.rect(s, (110, 110, 112), (int(cx - 6), ch - 4, 12, 4))
        _rr(s, lc if night else shade_rgb(lc, 0.85), (int(cx - 6), 8, 12, 12), 3)
        pygame.draw.polygon(s, (70, 60, 60), [(cx - 9, 9), (cx + 9, 9), (cx, 2)])
    elif kind == 'blocks':
        rnd = Rng(var * 19 + 1)
        y = ch
        for k in range(3):
            w_ = int(34 - k * 7 + rnd() * 4)
            h_ = int(12 + rnd() * 6)
            x = int(cx - w_ / 2 + (rnd() - 0.5) * 6)
            c = acc[(var + k) % len(acc)]
            pygame.draw.rect(s, c, (x, y - h_, w_, h_))
            pygame.draw.rect(s, shade_rgb(c, 0.75), (x + w_ - 5, y - h_, 5, h_))
            for sx in range(x + 4, x + w_ - 4, 8):
                pygame.draw.rect(s, shade_rgb(c, 1.15), (sx, y - h_ - 3, 5, 3))
            y -= h_ + 3
    elif kind == 'dish':
        pygame.draw.line(s, (150, 150, 158), (int(cx), ch), (int(cx), int(ch * 0.45)), 3)
        pygame.draw.line(s, (150, 150, 158), (int(cx - 12), ch), (int(cx), int(ch * 0.6)), 2)
        pygame.draw.line(s, (150, 150, 158), (int(cx + 12), ch), (int(cx), int(ch * 0.6)), 2)
        pygame.draw.ellipse(s, (235, 238, 245), (int(cx - 22), int(ch * 0.12), 44, 30))
        pygame.draw.ellipse(s, (190, 195, 205), (int(cx - 16), int(ch * 0.18), 32, 20))
        pygame.draw.line(s, (120, 120, 128), (int(cx), int(ch * 0.36)), (int(cx + 4), int(ch * 0.05)), 2)
        pygame.draw.circle(s, (255, 80, 80), (int(cx + 4), int(ch * 0.05)), 2)
    elif kind == 'sunflower':
        fc = flower[0]
        for k, (x, top) in enumerate(((cx - 10, 10), (cx + 2, 4), (cx + 12, 14))):
            pygame.draw.line(s, (60, 130, 50), (int(x), ch), (int(x), top + 6), 2)
            _ell(s, (70, 150, 60), x - 4, ch - 12 - k * 3, 4, 2)
            for a in range(8):
                ang = a * TAU / 8
                pygame.draw.circle(s, fc, (int(x + math.cos(ang) * 5), int(top + 6 + math.sin(ang) * 5)), 3)
            pygame.draw.circle(s, (100, 60, 30), (int(x), top + 6), 3)
    elif kind == 'cloud':
        c0 = leaf[0] if leaf[0][0] > 200 else (250, 252, 255)
        _ell(s, shade_rgb(c0, 0.86), cx + 4, ch - 9, 26, 9)
        _ell(s, c0, cx - 10, ch - 14, 16, 12)
        _ell(s, c0, cx + 6, ch - 18, 18, 15)
        _ell(s, shade_rgb(c0, 1.05), cx - 2, ch - 22, 10, 8)
    elif kind == 'cone':
        oc = (255, 118, 24)
        pygame.draw.rect(s, (40, 40, 44), (2, ch - 4, cw - 4, 4))
        pygame.draw.polygon(s, oc, [(cx - 9, ch - 4), (cx + 9, ch - 4), (cx + 2, 1), (cx - 2, 1)])
        pygame.draw.polygon(s, shade_rgb(oc, 0.78), [(cx + 1, 1), (cx + 2, 1), (cx + 9, ch - 4), (cx + 3, ch - 4)])
        pygame.draw.polygon(s, (250, 250, 250), [(cx - 6.4, ch - 12), (cx + 6.4, ch - 12), (cx + 5.0, ch - 17), (cx - 5.0, ch - 17)])
        pygame.draw.polygon(s, (250, 250, 250), [(cx - 3.8, ch - 21), (cx + 3.8, ch - 21), (cx + 2.8, ch - 24), (cx - 2.8, ch - 24)])
    elif kind == 'drum':
        dc = (36, 120, 220)
        _rr(s, dc, (2, 3, cw - 4, ch - 3), 3)
        pygame.draw.rect(s, shade_rgb(dc, 0.72), (cw - 9, 4, 6, ch - 5))
        for y in (8, ch // 2, ch - 7):
            pygame.draw.rect(s, shade_rgb(dc, 0.6), (2, y, cw - 4, 2))
        _ell(s, shade_rgb(dc, 1.25), cx, 4, cw / 2 - 2, 3)
        pygame.draw.circle(s, (230, 230, 230), (int(cx - 3), 4), 2)
    elif kind == 'crate':
        wc = (192, 140, 78)
        pygame.draw.rect(s, wc, (1, 2, cw - 2, ch - 2))
        pygame.draw.rect(s, shade_rgb(wc, 0.68), (1, 2, cw - 2, ch - 2), 3)
        pygame.draw.line(s, shade_rgb(wc, 0.68), (3, 4), (cw - 4, ch - 3), 3)
        pygame.draw.line(s, shade_rgb(wc, 0.68), (cw - 4, 4), (3, ch - 3), 3)
        for y in (ch // 3, 2 * ch // 3):
            pygame.draw.line(s, shade_rgb(wc, 0.85), (3, y), (cw - 4, y), 1)
        pygame.draw.rect(s, shade_rgb(wc, 1.2), (1, 2, cw - 2, 3))
    elif kind == 'tires':
        for k in range(3):
            y = ch - 11 - k * 10
            _ell(s, (24, 24, 28), cx, y + 4, cw / 2 - 1, 7)
            _ell(s, (44, 44, 50), cx, y + 1, cw / 2 - 2, 6)
            _ell(s, (14, 14, 16), cx, y + 1, cw / 4, 3)
            pygame.draw.arc(s, (230, 40, 40) if k % 2 == 0 else (240, 240, 240), (2, y - 5, cw - 4, 12), 0.2, 2.9, 2)
    elif kind == 'block':
        bc = (226, 226, 230)
        pygame.draw.polygon(s, bc, [(1, ch), (cw - 1, ch), (cw - 5, ch - 9), (cw - 9, 1), (9, 1), (5, ch - 9)])
        pygame.draw.polygon(s, shade_rgb(bc, 0.8), [(1, ch), (cw - 1, ch), (cw - 5, ch - 9), (5, ch - 9)])
        for x in range(4, cw - 6, 10):
            pygame.draw.polygon(s, (220, 40, 40), [(x + 6, 3), (x + 10, 3), (x + 4, ch - 10), (x, ch - 10)])
    elif kind == 'lavapillar':
        bc = mix_rgb(rk[0], (34, 28, 30), 0.6)
        lava = (255, 120, 24)
        pygame.draw.rect(s, shade_rgb(bc, 0.8), (2, ch - 8, cw - 4, 8))
        pygame.draw.polygon(s, bc, [(5, ch - 6), (cw - 5, ch - 6), (cw - 7, 8), (7, 8)])
        pygame.draw.polygon(s, shade_rgb(bc, 0.7), [(cx + 2, ch - 6), (cw - 5, ch - 6), (cw - 7, 8), (cx + 2, 8)])
        for k, y in enumerate(range(16, ch - 12, 14)):
            x0 = 8 + (k * 5) % 9
            pygame.draw.line(s, lava, (x0, y), (x0 + 6, y + 5), 2)
            pygame.draw.line(s, (255, 220, 120), (x0 + 6, y + 5), (x0 + 3, y + 10), 1)
        _ell(s, (255, 90, 20), cx, 8, cw / 2 - 6, 4)
        _ell(s, (255, 220, 110), cx, 7, cw / 2 - 10, 2)
        for k in range(3):
            pygame.draw.circle(s, (255, 150, 40), (int(cx - 5 + k * 5), 4 - k % 2), 2)
    elif kind == 'volcano':
        vc = mix_rgb(rk[0], (70, 44, 34), 0.55)
        lava = (255, 110, 24)
        pygame.draw.polygon(s, vc, [(0, ch), (cw, ch), (cx + 16, 12), (cx - 16, 12)])
        pygame.draw.polygon(s, shade_rgb(vc, 0.75), [(cx + 2, ch), (cw, ch), (cx + 16, 12), (cx + 2, 12)])
        _ell(s, (60, 20, 14), cx, 12, 16, 4)
        _ell(s, lava, cx, 12, 12, 3)
        for k, (x1, x2) in enumerate(((cx - 6, cx - 30), (cx + 4, cx + 22), (cx - 1, cx - 8))):
            pts = [(x1, 14), (x1 + (x2 - x1) * 0.4 + 3, 30 + k * 6), (x2, ch - 6 - k * 8)]
            pygame.draw.lines(s, lava, False, pts, 3)
            pygame.draw.lines(s, (255, 210, 110), False, pts, 1)
        for k in range(4):
            pygame.draw.circle(s, (255, 160, 60), (int(cx - 9 + k * 6), 6 - (k % 2) * 3), 2)
    return s


class ThemeGfx(object):
    """하나의 맵(바이옴)을 그리는 데 필요한 모든 캐시"""

    def __init__(self, th, seed, rw, rh, f, far):
        self.th = th
        self.rw, self.rh, self.f, self.far = rw, rh, f, far
        self.night = bool(th.get('night'))
        self.fog = hex_rgb(th['fog'])
        self.sky_top = hex_rgb(th['sky_top'])
        self.sky_bot = hex_rgb(th['sky_bot'])
        self.sprites = {}
        self.scaled = {}          # 크기 맞춘 스프라이트 캐시 (이번 세대)
        self.scaled_old = {}      # 직전 세대: 다시 쓰이면 이번 세대로 옮겨 살린다
        self.scaled_px = 0        # 이번 세대가 차지한 픽셀 수 (메모리 상한용)
        self.fog_masks = {}       # 안개 단계별 알파 곱하기 판
        self._make_palette()
        self._make_fog_lut()
        self.sky = self._make_sky()
        self.pano = self._make_pano(seed)
        self.skyfx = self._make_skyfx(seed)
        self.glow = self._make_glow()
        self.sun_az = math.atan2(th['sun_dir'][0], th['sun_dir'][2])
        sd = th['sun_dir']
        self.sun_el = math.asin(sd[1] / math.sqrt(sd[0] ** 2 + sd[1] ** 2 + sd[2] ** 2))
        self._make_bg()

    def _make_bg(self):
        """하늘 + 별/구름/오로라 + 지평선을 미리 한 장(불투명)으로 합성해 둔다.
        매 프레임 반투명 그림 여러 장을 섞던 것을 '복사 두 번'으로 바꿔서 빠르다 (보이는 그림은 같음).
        해/달은 여기 넣지 않고 매 프레임 원래 위치 계산 그대로, 해 주변 사각형만 원래 순서로 다시 그린다."""
        pano, fx_, sky = self.pano, self.skyfx, self.sky
        pw = pano.get_width()
        sh = sky.get_height()
        extra = 3                                        # 구름(+2)/지평선(+3)이 지평선 아래로 내려오는 줄 수
        H = sh + extra
        try:
            bg = pygame.Surface((pw, H), 0, pygame.display.get_surface())
        except Exception:
            bg = pygame.Surface((pw, H))
        x = 0
        while x < pw:
            bg.blit(sky, (x, 0))
            x += sky.get_width()
        bg.fill(self.ground_far, (0, sh, pw, extra))
        bg.blit(fx_, (0, sh - fx_.get_height() + 2))
        bg.blit(pano, (0, sh - pano.get_height() + 3))
        self.bg = bg
        self.bg_sky_h = sh
        self.bg_extra = extra
        self.sun_r = max(3, int(self.rh * (0.028 if not self.night else 0.04)))
        self.sun_col = mix_rgb(hex_rgb(self.th['sun']), (255, 255, 255), 0.6)

    # ---- 색상표 -----------------------------------------------------------------
    def _make_palette(self):
        th = self.th
        amb = 0.86 if (self.night and not th.get('glow_wall')) else 1.0
        glow = bool(th.get('glow_wall'))
        road = hex_rgb(th['road'])
        g0, g1 = hex_rgb(th['ground'][0]), hex_rgb(th['ground'][1])
        w0, w1 = hex_rgb(th['wall'][0]), hex_rgb(th['wall'][1])
        kb = th.get('kerb') or ((216, 35, 42), (240, 240, 240))
        wk = 1.0 if glow else amb
        base = {
            'road_a': shade_rgb(road, amb), 'road_b': shade_rgb(road, amb * 1.13),
            'grass_a': shade_rgb(g0, amb), 'grass_b': shade_rgb(g1, amb),
            'skirt_a': shade_rgb(g0, amb * 0.78), 'skirt_b': shade_rgb(g1, amb * 0.72),
            'kerb_r': shade_rgb(kb[0], amb), 'kerb_w': shade_rgb(kb[1], amb),
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
        # 안개가 짙은 바이옴은 더 가까이부터 흐려진다
        dens = clamp(self.th.get('fog_d', 0.0015) / 0.0015, 0.6, 2.6)
        start = 0.12 / dens
        self.fog_lut = []
        for d in range(int(far) + 4):
            t = clamp((d - start * far) / ((1.0 - start) * far / min(dens, 1.6)), 0.0, 1.0) ** 1.2
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
        if self.th.get('aurora'):
            for band, col in enumerate(((70, 255, 170, 80), (90, 210, 255, 64), (190, 120, 255, 52))):
                ph1, amp = rnd() * TAU, ph * (0.03 + 0.015 * band)
                y0 = ph * (0.6 + band * 0.08)
                thick = ph * (0.09 - band * 0.015)
                top, low = [], []
                for i in range(0, 61):
                    x = pw * i / 60.0
                    a = TAU * i / 60.0
                    y = y0 + math.sin(a * 3 + ph1) * amp + math.sin(a * 7 + ph1 * 2) * amp * 0.4
                    top.append((x, y))
                    low.append((x, y + thick * (0.7 + 0.3 * math.sin(a * 5 + ph1))))
                pygame.draw.polygon(s, col, top + low[::-1])
        n = int(7 * self.th.get('clouds', 0))
        if n:
            c = self.th.get('cloud') or (255, 255, 255)
            cc = (c[0], c[1], c[2], 190)
            for _ in range(n):
                x = rnd() * pw
                y = ph * (0.18 + rnd() * 0.5)
                sz = (0.5 + rnd()) * self.rh * 0.12
                for j in range(5):
                    _ell(s, cc, (x + (j - 2) * sz * 0.7) % pw, y + (j % 2) * sz * 0.12, sz * (0.9 - 0.12 * abs(j - 2)), sz * 0.36)
        return s

    # ---- 지평선 파노라마 (코어의 horizon_layers 정의를 그대로 그림) --------------------------
    def _make_pano(self, seed):
        th = self.th
        pw = max(64, int(TAU * self.f))
        ph = int(self.rh * 0.62)
        s = _surf(pw, ph)
        k = self.f / 2500.0

        def X(a):
            return a * pw

        def Y(h):
            return ph - h * k

        def wrap(fn, xmin, xmax):
            fn(0)
            if xmin < 0:
                fn(pw)
            if xmax > pw:
                fn(-pw)
        for rad, items in horizon_layers(th, seed):
            for it in items:
                t = it[0]
                if t == 'ridge':
                    col, top, hs = it[1], it[2], it[3]
                    n = len(hs) - 1
                    pts = [(0, ph)] + [(pw * i / float(n), Y(hs[i])) for i in range(n + 1)] + [(pw, ph)]
                    if top:
                        pygame.draw.polygon(s, top, pts)
                        dy = max(2.0, ph * 0.03)
                        pts2 = [(0, ph)] + [(pw * i / float(n), Y(hs[i]) + dy + (ph - Y(hs[i])) * 0.2) for i in range(n + 1)] + [(pw, ph)]
                        pygame.draw.polygon(s, col, pts2)
                    else:
                        pygame.draw.polygon(s, col, pts)
                elif t == 'poly':
                    col = it[1]
                    pts = [(X(a), Y(h)) for a, h in it[2]]
                    xs = [p[0] for p in pts]
                    wrap(lambda dx: pygame.draw.polygon(s, col, [(x + dx, y) for x, y in pts]), min(xs), max(xs))
                elif t == 'disc':
                    col, a, h, r = it[1], it[2], it[3], it[4]
                    rp = max(1, int(r * k))
                    x, y = X(a), Y(h)
                    wrap(lambda dx: pygame.draw.circle(s, col, (int(x + dx), int(y)), rp), x - rp, x + rp)
                elif t == 'ring':
                    col, a, h, rx, ry, w = it[1], it[2], it[3], it[4], it[5], it[6]
                    x, y = X(a), Y(h)
                    rect = (int(x - rx * k), int(y - ry * k), max(2, int(rx * k * 2)), max(2, int(ry * k * 2)))
                    wrap(lambda dx: pygame.draw.ellipse(s, col, (rect[0] + dx, rect[1], rect[2], rect[3]), max(1, int(w * k))), rect[0], rect[0] + rect[2])
                elif t == 'line':
                    pts = [(X(a), Y(h)) for a, h in it[2]]
                    pygame.draw.lines(s, it[1], False, pts, max(1, int(it[3] * k)))
        return s

    # ---- 장식물 스프라이트 --------------------------------------------------------------
    def sprite(self, kind, var):
        k = (kind, var)
        sp = self.sprites.get(k)
        if sp is None:
            sp = self.sprites[k] = make_sprite(kind, self.th, var)
        return sp

    def scaled_sprite(self, kind, var, wpx, hpx, lv=0):
        """월드 크기를 화면 픽셀 크기로 맞춘 스프라이트 (로그 간격 양자화 캐시: 크기가 연속으로 변해도 캐시 적중)"""
        qw = max(2, int(_QB ** round(math.log(max(wpx, 1.0)) / _QL)))
        qh = max(2, int(_QB ** round(math.log(max(hpx, 1.0)) / _QL)))
        sp = self.scaled.get((kind, var, qw, qh, lv))
        if sp is None:
            sp = self.scaled_entry(kind, var, qw, qh, lv)
        return sp

    def scaled_entry(self, kind, var, qw, qh, lv):
        """캐시에 없는 크기의 스프라이트. 안개(lv)는 알파 채널에 미리 곱해 둔다 (같은 그림, 4배 빠른 그리기 경로)

        캐시는 두 세대로 관리한다: 이번 세대가 꽉 차면 통째로 '직전 세대'가 되고, 직전 세대에서 다시 쓰인 것만
        살아남는다. 화면에 보이는 스프라이트는 버려지지 않아서 끊김이 없고, 메모리도 픽셀 수로 묶인다."""
        key = (kind, var, qw, qh, lv)
        sp = self.scaled_old.pop(key, None)
        if sp is None:
            sp = pygame.transform.scale(self.sprite(kind, var), (qw, qh))
            if lv:
                self._fog_mult(sp, lv)
        sc = self.scaled
        if len(sc) >= _CACHE_N or self.scaled_px > _CACHE_PX:
            self.scaled_old = sc
            sc = self.scaled = {}
            self.scaled_px = 0
        sc[key] = sp
        self.scaled_px += qw * qh
        return sp

    def _fog_mult(self, sp, lv):
        """sp 의 알파에 (255 - lv*15)/255 를 곱한다. fill(BLEND_RGBA_MULT) 와 픽셀까지 같은 결과지만
        미리 칠해 둔 판을 블릿하는 쪽이 10배 이상 빠르다 (큰 건물 스프라이트에서 끊김의 원인이었음)"""
        w, h = sp.get_size()
        if w > 2048 or h > 2048:
            sp.fill((255, 255, 255, 255 - lv * 15), special_flags=pygame.BLEND_RGBA_MULT)
            return
        m = self.fog_masks.get(lv)
        if m is None or m.get_width() < w or m.get_height() < h:
            mw, mh = (m.get_width(), m.get_height()) if m is not None else (64, 64)
            while mw < w:
                mw *= 2
            while mh < h:
                mh *= 2
            m = pygame.Surface((mw, mh), pygame.SRCALPHA)
            m.fill((255, 255, 255, 255 - lv * 15))
            self.fog_masks[lv] = m
        sp.blit(m, (0, 0), (0, 0, w, h), special_flags=pygame.BLEND_RGBA_MULT)


_QB = 1.12
_CACHE_N = 1400            # 세대당 최대 장수
_CACHE_PX = 3000000        # 세대당 최대 픽셀 (약 12MB) - 두 세대 합쳐도 24MB 안팎 (크게 잡으면 오히려 느려짐)
_QL = math.log(_QB)
