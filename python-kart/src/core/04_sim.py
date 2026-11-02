
# ----------------------------------------------------------------------------
#  아케이드 카트 물리 + AI  (+ 아이템전 상태이상: 스핀/날아감/축소/감속/미끄럼/빙결/무적/방패/유령/거대화/로켓…)
# ----------------------------------------------------------------------------
DRIFT_BOOST = (0.0, 0.7, 1.2, 1.9)
STEER_RATES = ((6.0, 8.0), (10.0, 13.0), (16.0, 20.0))    # 조향 반응 설정별 (누를 때, 뗄 때) 속도
NO_INPUT = {'steer': 0.0, 'throttle': 0.0, 'brake': 0.0, 'drift': False}

# 다른 기기에 보내는 상태 비트 (원격 카트 표시용)
FX_SPIN, FX_AIR, FX_SHRINK, FX_STAR, FX_SHIELD, FX_GHOST, FX_GIANT, FX_FREEZE, FX_AUTO, FX_HOP, FX_SLIDE, FX_MAGNET = (
    1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048)
FX_RAM = FX_STAR | FX_GIANT | FX_AUTO          # 부딪히면 상대를 날려버리는 상태


def steer_step(cur, tgt, dt, resp=1):
    """키보드/버튼 같은 켜고 끄는 입력을 부드럽게 -1..1 로 만든다. 반대 방향으로 급히 바꿀 때는 더 빠르게."""
    up, down = STEER_RATES[int(clamp(resp, 0, 2))]
    rate = down if tgt == 0 else up
    if tgt * cur < 0:
        rate = max(rate, down) * 1.3
    return cur + (tgt - cur) * min(1.0, dt * rate)


class KartSim(object):
    def __init__(self, track, kart_id, slot=0):
        self.track = track
        self.kart_id = kart_id
        self.stats = kart_stats(kart_id)
        self.q = Q()
        self.reset(track.spawn_pose(slot))

    def reset(self, pose):
        t = self.track
        self.x = pose['x']
        self.z = pose['z']
        self.heading = pose['heading']
        self.vx = 0.0
        self.vz = 0.0
        self.speed = 0.0
        self.drifting = False
        self.drift_dir = 0.0
        self.drift_charge = 0.0
        self.drift_tier = 0
        self.boost_t = 0.0
        self.offroad = False
        self.wall_hit = 0.0
        self.steer_vis = 0.0
        self.slip = 0.0
        self.armed = True
        self.pad_cool = 0.0
        t.query(self.x, self.z, -1, self.q)
        self.y = self.q.y
        self.hint = self.q.idx
        self.last_prog = self.q.prog
        self.total = pose.get('prog', 0.0)
        self.d = self.q.d
        self.upx, self.upy, self.upz = 0.0, 1.0, 0.0
        self.finished = False
        self.events = []
        self.wrong_way = False
        self.fx_reset()

    # ---- 아이템 상태이상 ------------------------------------------------------------
    def fx_reset(self):
        self.spin_t = self.air_t = self.air_dur = 0.0
        self.shrink_t = self.slow_t = self.slide_t = self.freeze_t = self.stun_t = self.rev_t = self.blind_t = 0.0
        self.star_t = self.shield_t = self.ghost_t = self.giant_t = self.auto_t = self.grip_t = 0.0
        self.magnet_t = self.engine_t = self.hop_t = self.hop_dur = self.immune_t = self.ram_cool = 0.0
        self.shield_n = 0
        self.slow_k = 1.0
        self.engine_cap = 0.0
        self.engine_acc = 1.0
        self.auto_spd = 1.4
        self.magnet_range = 80.0
        self.boost_pow = 1.0
        self.coins = 0
        self.spin_ang = 0.0
        self.air_y = 0.0
        self.pull = None
        self.fx_time = 0.0

    def cure(self):
        """나쁜 상태이상 모두 해제"""
        self.spin_t = self.air_t = self.shrink_t = self.slow_t = self.slide_t = 0.0
        self.freeze_t = self.stun_t = self.rev_t = self.blind_t = 0.0
        self.slow_k = 1.0
        self.spin_ang = 0.0
        self.air_y = 0.0

    def debuffed(self):
        return (self.spin_t > 0 or self.shrink_t > 0 or self.slow_t > 0 or self.slide_t > 0 or self.freeze_t > 0
                or self.stun_t > 0 or self.rev_t > 0 or self.blind_t > 0)

    def invulnerable(self):
        return self.star_t > 0 or self.auto_t > 0 or self.ghost_t > 0 or self.immune_t > 0

    def hit(self, fx, dur=0.0, k=0.0):
        """공격 받기 -> 'ok' (맞음) / 'block' (방패로 막음) / 'immune' (무적/점프 등으로 무시)"""
        if self.finished or self.invulnerable():
            return 'immune'
        if self.giant_t > 0 and fx in ('spin', 'slide', 'slow', 'bump', 'flat', 'shrink', 'warpback'):
            return 'immune'
        if self.hop_t > 0 and fx in ('slide', 'slow'):          # 점프 중에는 바닥 함정이 안 통한다
            return 'immune'
        if self.shield_n > 0:
            self.shield_n -= 1
            if self.shield_n <= 0:
                self.shield_t = 0.0
            self.immune_t = max(self.immune_t, 0.5)
            return 'block'
        if fx in ('spin', 'launch', 'freeze', 'bump', 'flat'):
            self.drifting = False
            self.drift_charge = 0.0
            self.drift_tier = 0
            self.boost_t = 0.0
        if fx == 'spin':
            self.spin_t = max(self.spin_t, dur or 1.1)
        elif fx == 'launch':
            self.air_t = self.air_dur = dur or 1.25
            self.spin_t = max(self.spin_t, self.air_t + 0.25)
        elif fx == 'shrink':
            self.shrink_t = max(self.shrink_t, dur or 6.0)
            self.spin_t = max(self.spin_t, 0.5)
            self.giant_t = 0.0
        elif fx == 'flat':
            self.shrink_t = max(self.shrink_t, dur or 3.5)
            self.slow_t = max(self.slow_t, dur or 3.5)
            self.slow_k = 0.7
            self.spin_t = max(self.spin_t, 0.6)
        elif fx == 'slow':
            kk = clamp(k or 0.6, 0.2, 1.0)
            self.slow_k = min(self.slow_k, kk) if self.slow_t > 0 else kk
            self.slow_t = max(self.slow_t, dur or 3.0)
        elif fx == 'slide':
            self.slide_t = max(self.slide_t, dur or 2.0)
        elif fx == 'freeze':
            self.freeze_t = max(self.freeze_t, dur or 1.5)
        elif fx == 'stun':
            self.stun_t = max(self.stun_t, dur or 2.0)
        elif fx == 'reverse':
            self.rev_t = max(self.rev_t, dur or 4.0)
        elif fx == 'blind':
            self.blind_t = max(self.blind_t, dur or 4.0)
        elif fx == 'bump':
            self.vx *= 0.3
            self.vz *= 0.3
            self.speed = math.hypot(self.vx, self.vz)
            self.wall_hit = 1.0
            self.spin_t = max(self.spin_t, 0.4)
        return 'ok'

    def fx_bits(self):
        b = 0
        if self.spin_t > 0:
            b |= FX_SPIN
        if self.air_t > 0:
            b |= FX_AIR
        if self.shrink_t > 0:
            b |= FX_SHRINK
        if self.star_t > 0:
            b |= FX_STAR
        if self.shield_n > 0:
            b |= FX_SHIELD
        if self.ghost_t > 0:
            b |= FX_GHOST
        if self.giant_t > 0:
            b |= FX_GIANT
        if self.freeze_t > 0:
            b |= FX_FREEZE
        if self.auto_t > 0:
            b |= FX_AUTO
        if self.hop_t > 0:
            b |= FX_HOP
        if self.slide_t > 0:
            b |= FX_SLIDE
        if self.magnet_t > 0:
            b |= FX_MAGNET
        return b

    def _tick_fx(self, dt):
        self.fx_time += dt
        if self.spin_t > 0:
            self.spin_t -= dt
            self.spin_ang += dt * 14.0
            if self.spin_t <= 0:
                self.spin_t = 0.0
                self.spin_ang = 0.0
        if self.air_t > 0:
            self.air_t -= dt
            f = 1.0 - max(0.0, self.air_t) / max(self.air_dur, 0.05)
            self.air_y = math.sin(math.pi * f) * 3.4
            if self.air_t <= 0:
                self.air_t = 0.0
                self.air_y = 0.0
        elif self.hop_t > 0:
            self.hop_t -= dt
            f = 1.0 - max(0.0, self.hop_t) / max(self.hop_dur, 0.05)
            self.air_y = math.sin(math.pi * f) * (1.2 + self.hop_dur * 0.9)
            if self.hop_t <= 0:
                self.hop_t = 0.0
                self.air_y = 0.0
        else:
            self.air_y = 0.0
        if self.shrink_t > 0:
            self.shrink_t = max(0.0, self.shrink_t - dt)
        if self.slow_t > 0:
            self.slow_t -= dt
            if self.slow_t <= 0:
                self.slow_t = 0.0
                self.slow_k = 1.0
        if self.slide_t > 0:
            self.slide_t = max(0.0, self.slide_t - dt)
        if self.freeze_t > 0:
            self.freeze_t = max(0.0, self.freeze_t - dt)
        if self.stun_t > 0:
            self.stun_t = max(0.0, self.stun_t - dt)
        if self.rev_t > 0:
            self.rev_t = max(0.0, self.rev_t - dt)
        if self.blind_t > 0:
            self.blind_t = max(0.0, self.blind_t - dt)
        if self.star_t > 0:
            self.star_t = max(0.0, self.star_t - dt)
        if self.shield_t > 0:
            self.shield_t -= dt
            if self.shield_t <= 0:
                self.shield_t = 0.0
                self.shield_n = 0
        if self.ghost_t > 0:
            self.ghost_t = max(0.0, self.ghost_t - dt)
        if self.giant_t > 0:
            self.giant_t = max(0.0, self.giant_t - dt)
        if self.auto_t > 0:
            self.auto_t = max(0.0, self.auto_t - dt)
        if self.grip_t > 0:
            self.grip_t = max(0.0, self.grip_t - dt)
        if self.magnet_t > 0:
            self.magnet_t -= dt
            if self.magnet_t <= 0:
                self.magnet_t = 0.0
                self.pull = None
        if self.engine_t > 0:
            self.engine_t = max(0.0, self.engine_t - dt)
        if self.immune_t > 0:
            self.immune_t = max(0.0, self.immune_t - dt)
        if self.ram_cool > 0:
            self.ram_cool = max(0.0, self.ram_cool - dt)

    def _autopilot(self):
        """로켓 아이템: 트랙 중앙을 따라 자동으로 달린다"""
        t = self.track
        look = int(clamp((self.speed * 0.42 + 12.0) / t.ds, 5, 40))
        i = (self.q.idx + look) % t.N
        want = math.atan2(t.px[i] - self.x, t.pz[i] - self.z)
        return clamp(-wrap_pi(want - self.heading) * 2.6, -1.0, 1.0)

    def teleport(self, x, z, heading=None):
        """순간이동 (속력은 유지). 진행도는 다음 update 에서 자연스럽게 반영된다."""
        sp = max(0.0, self.vx * math.sin(self.heading) + self.vz * math.cos(self.heading))
        self.x, self.z = x, z
        if heading is not None:
            self.heading = heading
        self.vx = math.sin(self.heading) * sp
        self.vz = math.cos(self.heading) * sp
        self.track.query(x, z, -1, self.q)
        self.hint = self.q.idx
        self.y = self.q.y
        self.drifting = False
        self.drift_charge = 0.0
        self.drift_tier = 0

    @property
    def lap(self):
        return max(1, int(math.floor(self.total / self.track.N)) + 1)

    def respawn(self):
        t = self.track
        q = self.q
        i = q.idx
        self.x = t.px[i]
        self.z = t.pz[i]
        self.heading = math.atan2(t.tx[i], t.tz[i])
        self.vx = self.vz = self.speed = 0.0
        self.drifting = False
        self.drift_charge = 0.0
        self.drift_tier = 0
        self.boost_t = 0.0
        self.cure()
        self.hop_t = 0.0
        t.query(self.x, self.z, -1, q)
        self.y = q.y
        self.hint = q.idx
        self.last_prog = q.prog

    def update(self, dt, inp, others):
        s = self.stats
        t = self.track
        q = self.q
        ev = self.events
        del ev[:]
        sin, cos, exp = math.sin, math.cos, math.exp
        self._tick_fx(dt)
        fx = sin(self.heading)
        fz = cos(self.heading)
        rx = -fz
        rz = fx
        vf = self.vx * fx + self.vz * fz
        vl = self.vx * rx + self.vz * rz
        # 입력 (상태이상이 있으면 바뀐다)
        lost = self.spin_t > 0 or self.air_t > 0 or self.freeze_t > 0
        if lost:
            thr, brk, steer, dbtn = 0.0, 0.0, 0.0, False
        elif self.auto_t > 0:
            thr, brk, steer, dbtn = 1.0, 0.0, self._autopilot(), False
        else:
            thr, brk, steer, dbtn = inp['throttle'], inp['brake'], inp['steer'], inp['drift']
            if self.rev_t > 0:
                steer = -steer
            if self.slide_t > 0:
                steer = clamp(steer + sin(self.fx_time * 7.0) * 0.55, -1.0, 1.0)
            if self.stun_t > 0:
                thr = 0.0
                dbtn = False
        boosting = self.boost_t > 0
        if boosting:
            self.boost_t -= dt
            if self.boost_t <= 0:
                self.boost_pow = 1.0
        maxs = s['max_speed']
        air = self.air_y > 0.3
        slow_off = self.offroad and not (self.grip_t > 0 or self.star_t > 0 or self.auto_t > 0 or air)
        cap = maxs * (0.55 if slow_off else 1.0) + (24.0 * self.boost_pow if boosting else 0.0) + self.coins * 0.55
        acc_k = 2.6 if boosting else 1.0
        if self.engine_t > 0:
            cap += self.engine_cap
            acc_k *= self.engine_acc
        if self.star_t > 0:
            cap += 14.0
            acc_k *= 1.6
        if self.giant_t > 0:
            cap += 5.0
        if self.magnet_t > 0 and self.pull is not None:
            cap += 9.0
        if self.shrink_t > 0:
            cap *= 0.72
            acc_k *= 0.8
        if self.slow_t > 0:
            cap *= self.slow_k
        if self.auto_t > 0:
            cap = max(cap, maxs * self.auto_spd)
            acc_k *= 3.0
        if thr > 0.01:
            if vf < cap:
                vf += s['accel_rate'] * acc_k * thr * (1 - 0.75 * max(0.0, vf) / cap) * dt
            else:
                vf -= 26 * dt
        if brk > 0.01:
            if vf > 1:
                vf -= 44 * brk * dt
            else:
                vf = max(-16.0, vf - 16 * brk * dt)
        elif thr < 0.01:
            vf -= sign(vf) * min(abs(vf), 7 * dt)
            if vf > cap + 1.0:
                vf -= 26 * dt
        vf *= exp(-(0.9 if slow_off else 0.04) * dt)
        if lost:
            if self.air_t > 0:
                vf *= exp(-0.8 * dt)
            elif self.freeze_t > 0:
                vf *= exp(-0.35 * dt)
            else:
                vf *= exp(-2.6 * dt)
        along = self.vx * q.tx + self.vz * q.tz
        vf -= 4.4 * q.ty * (1.0 if along >= 0 else -1.0) * dt     # 오르막은 느려지고 내리막은 빨라짐

        # 드리프트
        want = dbtn and abs(steer) > 0.25 and vf > 22 and not self.offroad
        if not dbtn:
            self.armed = True
        if not self.drifting and want and self.armed:
            self.armed = False
            self.drifting = True
            self.drift_dir = sign(steer)
            self.drift_charge = 0.0
            ev.append('driftStart')
        if self.drifting:
            if (not dbtn) or vf < 16:
                tier = self.drift_tier
                if tier > 0:
                    self.boost_t = max(self.boost_t, DRIFT_BOOST[tier])
                    ev.append('miniturbo')
                self.drifting = False
                self.drift_charge = 0.0
                self.drift_tier = 0
            else:
                self.drift_charge += dt * (0.75 + 0.5 * (1.0 if steer * self.drift_dir > 0 else 0.4))
                c = self.drift_charge
                tier = 3 if c > 3.2 else (2 if c > 1.9 else (1 if c > 0.9 else 0))
                if tier > self.drift_tier:
                    ev.append('tier%d' % tier)
                self.drift_tier = tier

        # 조향 (고속에서도 너무 둔해지지 않게)
        turn = s['turn_rate'] * (1.2 if self.grip_t > 0 else 1.0) * (0.9 if self.giant_t > 0 else 1.0)
        speed_f = clamp(abs(vf) / 14.0, 0.0, 1.0) * (1 - 0.22 * clamp(abs(vf) / maxs, 0.0, 1.0))
        if self.drifting:
            yaw = turn * (0.55 * self.drift_dir + 0.6 * steer * (0.75 if steer * self.drift_dir > 0 else 1.0)) * 1.15
        else:
            yaw = turn * steer
        self.heading -= yaw * speed_f * (1.0 if vf >= 0 else -1.0) * dt
        self.steer_vis += (steer - self.steer_vis) * min(1.0, dt * 12)
        grip = s['drift_grip'] if self.drifting else (9.5 if boosting else 12.0)
        if self.freeze_t > 0:
            grip = 0.5
        elif self.slide_t > 0:
            grip *= 0.22
        elif self.grip_t > 0:
            grip *= 1.25
        vl *= exp(-grip * dt)
        self.slip = vl
        nfx = sin(self.heading)
        nfz = cos(self.heading)
        self.vx = nfx * vf + (-nfz) * vl
        self.vz = nfz * vf + nfx * vl
        self.x += self.vx * dt
        self.z += self.vz * dt
        if self.magnet_t > 0 and self.pull is not None:
            self.x += self.pull[0] * 7.0 * dt
            self.z += self.pull[1] * 7.0 * dt

        # 다른 카트와 충돌 (원) - 유령 상태면 통과
        if self.ghost_t <= 0:
            rad = 2.5 * (1.5 if self.giant_t > 0 else (0.7 if self.shrink_t > 0 else 1.0))
            for o in others:
                dx = self.x - o[0]
                dz = self.z - o[1]
                dist = math.hypot(dx, dz)
                if 0.001 < dist < rad:
                    push = (rad - dist) / dist * (0.25 if self.giant_t > 0 else 0.55)
                    self.x += dx * push
                    self.z += dz * push
                    rel = (self.vx - o[2]) * dx / dist + (self.vz - o[3]) * dz / dist
                    if rel < 0:
                        self.vx -= dx / dist * rel * 0.9
                        self.vz -= dz / dist * rel * 0.9
                        ev.append('bump')

        # 트랙 질의 + 벽
        t.query(self.x, self.z, self.hint, q)
        self.hint = q.idx
        lim = t.wall_off - 1.0
        if abs(q.d) > lim:
            sg = sign(q.d)
            over = abs(q.d) - lim
            self.x -= q.rx * over * sg
            self.z -= q.rz * over * sg
            vn = (self.vx * q.rx + self.vz * q.rz) * sg
            if vn > 0:
                self.vx -= q.rx * sg * vn * 1.35
                self.vz -= q.rz * sg * vn * 1.35
                k = 1 - clamp(vn / 80.0, 0.04, 0.2)
                self.vx *= k
                self.vz *= k
                if vn > 6:
                    self.wall_hit = 1.0
                    ev.append('wall')
                if self.drifting:
                    self.drifting = False
                    self.drift_charge = 0.0
                    self.drift_tier = 0
            t.query(self.x, self.z, self.hint, q)
        self.d = q.d
        self.offroad = abs(q.d) > t.hw + 0.4
        self.wall_hit = max(0.0, self.wall_hit - dt * 4)

        # 부스트 패드
        if self.pad_cool > 0:
            self.pad_cool -= dt
        elif t.pads and not air:
            N = t.N
            for p in t.pads:
                di = q.prog - p['idx']
                if di > N / 2:
                    di -= N
                elif di < -N / 2:
                    di += N
                if abs(di * t.ds) < p['half_len'] and abs(q.d - p['d']) < p['half_w']:
                    self.boost_t = max(self.boost_t, 1.5)
                    ev.append('pad')
                    f = math.hypot(self.vx, self.vz)
                    if f < maxs:
                        k = 0.5 * maxs / max(f, 1.0) + 0.5
                        self.vx *= k
                        self.vz *= k
                    self.pad_cool = 0.6
                    break

        # 지면 높이/방향
        self.y = q.y
        cb = cos(q.bank)
        sb = sin(q.bank)
        rbx, rby, rbz = q.rx * cb, -sb, q.rz * cb
        tyy = q.ty
        ux = rby * q.tz - rbz * tyy
        uy = rbz * q.tx - rbx * q.tz
        uz = rbx * tyy - rby * q.tx
        ul = math.sqrt(ux * ux + uy * uy + uz * uz) or 1.0
        k = min(1.0, dt * 8)
        self.upx += (ux / ul - self.upx) * k
        self.upy += (uy / ul - self.upy) * k
        self.upz += (uz / ul - self.upz) * k

        # 진행도
        delta = q.prog - self.last_prog
        N = t.N
        if delta > N / 2:
            delta -= N
        elif delta < -N / 2:
            delta += N
        self.total += delta
        self.last_prog = q.prog
        self.speed = math.hypot(self.vx, self.vz)
        fwd = self.vx * q.tx + self.vz * q.tz
        self.wrong_way = self.speed > 8 and fwd < -4 and cos(wrap_pi(self.heading - math.atan2(q.tx, q.tz))) < -0.3


class BotBrain(object):
    def __init__(self, rand):
        self.skill = 0.82 + rand() * 0.2
        self.lane = (rand() - 0.5) * 0.7
        self.phase = rand() * 6.28
        self.t = 0.0
        self.stuck = 0.0
        self.react = 0.5 + rand() * 1.2       # 아이템을 받고 쓰기까지 머뭇거리는 시간

    def drive(self, kart, dt, player_total, rubber=True):
        tr = kart.track
        q = kart.q
        N = tr.N
        self.t += dt
        look = int(clamp(round((kart.speed * 0.5 + 12) / tr.ds), 5, 34))
        lane = (self.lane + math.sin(self.t * 0.35 + self.phase) * 0.12) * tr.width * 0.5
        i = (q.idx + look) % N
        tx = tr.px[i] + tr.rx[i] * lane
        tz = tr.pz[i] + tr.rz[i] * lane
        want = math.atan2(tx - kart.x, tz - kart.z)
        diff = wrap_pi(want - kart.heading)
        steer = clamp(-diff * 2.2, -1.0, 1.0)
        if kart.blind_t > 0:                       # 시야가 가려지면 비틀거림
            steer = clamp(steer + math.sin(self.t * 2.3 + self.phase) * 0.5, -1.0, 1.0)
        rb = 1.0
        if rubber and player_total is not None:
            gap = (kart.total - player_total) * tr.ds
            rb = clamp(1 - gap / 900.0, 0.9, 1.08)
        curve = tr.turn[q.idx]
        target = kart.stats['max_speed'] * self.skill * rb * (1 - clamp(curve * 0.55 - 0.08, 0.0, 0.5))
        sp = kart.speed
        if kart.boost_t > 0 or kart.star_t > 0 or kart.engine_t > 0 or kart.auto_t > 0:
            target += 30.0                          # 가속 아이템을 쓰는 중이면 감속하지 않음
        inp = {'steer': steer, 'throttle': 1.0 if sp < target else 0.15, 'brake': 0.7 if sp > target + 7 else 0.0, 'drift': False}
        if curve > 0.55 and sp > 36 and self.skill > 0.9 and abs(steer) > 0.45:
            inp['drift'] = True
        if sp < 2 and kart.spin_t <= 0 and kart.freeze_t <= 0 and kart.air_t <= 0:
            self.stuck += dt
            if self.stuck > 2.5:
                kart.respawn()
                self.stuck = 0.0
        else:
            self.stuck = 0.0
        return inp
