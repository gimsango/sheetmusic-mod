
# ----------------------------------------------------------------------------
#  카트 3D 모델(파츠 목록) + 추격 카메라  — 두 프론트엔드(폰/PC)가 공유
#  좌표계(로컬): x = 오른쪽, y = 위, z = 앞.  박스: (cx, cy, cz, hx, hy, hz, 색, 앞면 테이퍼 x, y, 발광)
# ----------------------------------------------------------------------------
class KartModel(object):
    """카트 번호 -> 3D 파츠 목록"""

    def __init__(self, kid):
        k = decode_kart(kid)
        b = BODIES[k['body']]
        p = PAINTS[k['paint']]
        self.kid = kid
        self.k = k
        self.main = p['main']
        self.accent = p['accent']
        self.metal = p['metal']
        L, W, H = b['len'], b['wid'], b['hei']
        self.L, self.W, self.H = L, W, H
        R = WHEEL_R[k['wheel'] % 5]
        ww = WHEEL_W[k['wheel'] % 5]
        self.wheel_r, self.wheel_w, self.rim = R, ww, k['wheel'] // 5
        base = R * 0.75
        self.base = base
        main, acc = self.main, self.accent
        dark = (28, 30, 38)
        nose = b['nose']
        boxes = []
        # (cx, cy, cz, hx, hy, hz, color, tx, ty, glow)
        boxes.append((0, base + H * 0.35, 0, W / 2, H * 0.35, L / 2, main, 1, 1, False))
        boxes.append((0, base + H * 0.28, L / 2 + nose * 0.3, W * 0.33, H * 0.24, max(0.12, nose * 0.55), acc if p['pattern'] == 2 else main, 0.5, 0.6, False))
        if p['pattern'] == 1:
            boxes.append((0, base + H * 0.71, nose * 0.3, W * 0.08, 0.02, (L + nose * 0.9) / 2, acc, 1, 1, False))
        if p['pattern'] == 2:
            boxes.append((0, base + H * 0.3, -L * 0.2, W * 0.51, H * 0.08, L * 0.2, acc, 1, 1, False))
        for s in (-1, 1):
            boxes.append((s * (W / 2 + 0.08), base + H * 0.3, -L * 0.05, W * 0.1, H * 0.27, L * 0.25, acc, 1, 1, False))
            boxes.append((s * W * 0.32, base + H * 0.42, L / 2 + 0.03, 0.11, 0.06, 0.05, (255, 246, 208), 1, 1, True))
            boxes.append((s * W * 0.25, base + H * 0.25, -L / 2 - 0.1, 0.07, 0.07, 0.2, (150, 156, 168), 1, 1, False))
            boxes.append((s * W * 0.36, base + H * 0.5, -L / 2 - 0.02, 0.12, 0.05, 0.03, (255, 40, 50), 1, 1, True))
        boxes.append((0, base + H * 0.12, L / 2 + nose * 0.55 + 0.05, W * 0.47, H * 0.07, 0.1, dark, 1, 1, False))
        seat = -L * 0.08
        self.seat = (0.0, base + H * 0.7, seat)
        if b['canopy'] == 1:
            boxes.append((0, base + H * 0.7 + 0.26, seat, W * 0.34, 0.26, 0.6, (150, 205, 245), 0.8, 0.85, False))
        elif b['canopy'] == 2:
            boxes.append((0, base + H * 0.7 + 0.17, seat - 0.15, W * 0.36, 0.17, L * 0.19, main, 1, 1, False))
            boxes.append((0, base + H * 0.7 + 0.2, seat + L * 0.19 + 0.02, W * 0.31, 0.1, 0.04, (32, 48, 64), 1, 1, False))
        # 드라이버 몸통
        boxes.append((0, base + H * 0.7 + 0.28, seat, 0.2, 0.28, 0.17, acc, 1, 1, False))
        self.helmet = (0.0, base + H * 0.7 + 0.72, seat + 0.02)
        # 윙/파츠
        top = base + H + 0.0
        bz = -L / 2
        w = k['wing']
        if w == 1:
            boxes.append((0, top - 0.05, bz + 0.1, W * 0.45, 0.03, 0.2, main, 1, 1, False))
        elif w == 2:
            for s in (-1, 1):
                boxes.append((s * W * 0.3, top + 0.25, bz + 0.1, 0.035, 0.28, 0.06, dark, 1, 1, False))
            boxes.append((0, top + 0.55, bz, W * 0.53, 0.035, 0.28, main, 1, 1, False))
        elif w == 3:
            for s in (-1, 1):
                boxes.append((s * W * 0.32, top + 0.28, bz + 0.1, 0.035, 0.3, 0.06, dark, 1, 1, False))
            boxes.append((0, top + 0.4, bz, W * 0.53, 0.03, 0.22, main, 1, 1, False))
            boxes.append((0, top + 0.68, bz - 0.12, W * 0.53, 0.03, 0.22, acc, 1, 1, False))
        elif w == 4:
            for s in (-1, 1):
                boxes.append((s * (W / 2 + 0.03), top - 0.05, bz + 0.3, 0.025, 0.25, 0.45, acc, 1, 1, False))
        elif w == 5:
            boxes.append((0, top + 0.5, bz - 0.1, W * 0.6, 0.04, 0.3, acc, 1, 1, False))
            for s in (-1, 1):
                boxes.append((s * W * 0.25, top + 0.25, bz + 0.05, 0.035, 0.28, 0.06, dark, 1, 1, False))
                boxes.append((s * W * 0.6, top + 0.5, bz - 0.1, 0.03, 0.14, 0.35, main, 1, 1, False))
        elif w == 6:
            boxes.append((0, top - 0.02, bz + 0.05, W * 0.4, 0.035, 0.27, main, 1, 1, False))
        elif w == 7:
            boxes.append((0, top + 0.12, -0.1, 0.18, 0.18, 0.25, dark, 0.5, 0.5, False))
        elif w == 8:
            for s in (-1, 1):
                boxes.append((s * 0.35, base + H * 0.6 + 0.3, bz - 0.2, 0.2, 0.2, 0.45, dark, 1, 1, False))
                boxes.append((s * 0.35, base + H * 0.6 + 0.3, bz - 0.66, 0.14, 0.14, 0.03, acc, 1, 1, True))
        elif w == 9:
            boxes.append((0, base + H + 0.55, bz - 0.1, 0.28, 0.28, 0.55, acc, 1, 1, False))
            boxes.append((0, base + H + 0.55, bz - 0.68, 0.18, 0.18, 0.05, (255, 150, 60), 1, 1, True))
            for s in (-1, 1):
                boxes.append((s * 0.4, base + H + 0.55, bz - 0.2, 0.25, 0.025, 0.2, dark, 1, 1, False))
        self.boxes = boxes
        # LOD1 용 단순 박스 (차체+포드+캐노피+윙 일부)
        self.boxes_lod1 = boxes[:2] + [bx for bx in boxes[2:] if bx[6] != (150, 156, 168) and bx[5] > 0.1 and not bx[9]][:7]
        # 바퀴 위치
        wz = L * 0.34
        self.wheels = []
        for sx, sz, front in ((-1, 1, True), (1, 1, True), (-1, -1, False), (1, -1, False)):
            self.wheels.append((sx * (W / 2 + ww * 0.35), R, sz * wz, sx, front))
        if self.rim == 3:
            self.rim_color = (224, 176, 32)
        elif self.rim == 4:
            self.rim_color = shade_rgb(acc, 1.3)
        else:
            self.rim_color = acc
        self.spin = 0.0


class ChaseCam(object):
    """추격 카메라: 카트 뒤쪽 위에서 부드럽게 따라간다"""

    def __init__(self):
        self.h = None
        self.y = 0.0

    def reset(self):
        self.h = None

    def update(self, dt, rc, max_speed):
        sr = clamp(rc.speed / max_speed, 0.0, 1.3)
        target = rc.h + (-rc.drift_dir * 0.2 if rc.drifting else 0.0)
        if self.h is None:
            self.h = rc.h
            self.y = rc.y
        self.h += wrap_pi(target - self.h) * (1 - math.exp(-7.0 * dt))
        self.y += (rc.y - self.y) * (1 - math.exp(-9.0 * dt))
        dist = 8.3 + sr * 2.2 + (1.6 if rc.boosting else 0.0)
        hgt = 3.5 + sr * 0.4
        fx, fz = math.sin(self.h), math.cos(self.h)
        x, y, z = rc.x - fx * dist, self.y + hgt, rc.z - fz * dist
        lx, ly, lz = rc.x + fx * 8.0, self.y + 1.2, rc.z + fz * 8.0
        yaw = math.atan2(lx - x, lz - z)
        pitch = math.atan2(y - ly, math.hypot(lx - x, lz - z))
        return x, y, z, yaw, pitch
