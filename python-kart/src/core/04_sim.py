
# ----------------------------------------------------------------------------
#  아케이드 카트 물리 + AI
# ----------------------------------------------------------------------------
DRIFT_BOOST = (0.0, 0.7, 1.2, 1.9)


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
        fx = sin(self.heading)
        fz = cos(self.heading)
        rx = -fz
        rz = fx
        vf = self.vx * fx + self.vz * fz
        vl = self.vx * rx + self.vz * rz
        boosting = self.boost_t > 0
        if boosting:
            self.boost_t -= dt
        maxs = s['max_speed']
        cap = maxs * (0.55 if self.offroad else 1.0) + (24.0 if boosting else 0.0)
        thr = inp['throttle']
        brk = inp['brake']
        steer = inp['steer']
        if thr > 0.01:
            if vf < cap:
                vf += s['accel_rate'] * (2.6 if boosting else 1.0) * thr * (1 - 0.75 * max(0.0, vf) / cap) * dt
            else:
                vf -= 26 * dt
        if brk > 0.01:
            if vf > 1:
                vf -= 44 * brk * dt
            else:
                vf = max(-16.0, vf - 16 * brk * dt)
        elif thr < 0.01:
            vf -= sign(vf) * min(abs(vf), 7 * dt)
        vf *= exp(-(0.9 if self.offroad else 0.04) * dt)
        along = self.vx * q.tx + self.vz * q.tz
        vf -= 4.4 * q.ty * (1.0 if along >= 0 else -1.0) * dt     # 오르막은 느려지고 내리막은 빨라짐

        # 드리프트
        want = inp['drift'] and abs(steer) > 0.25 and vf > 22 and not self.offroad
        if not inp['drift']:
            self.armed = True
        if not self.drifting and want and self.armed:
            self.armed = False
            self.drifting = True
            self.drift_dir = sign(steer)
            self.drift_charge = 0.0
            ev.append('driftStart')
        if self.drifting:
            if (not inp['drift']) or vf < 16:
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

        # 조향
        speed_f = clamp(abs(vf) / 14.0, 0.0, 1.0) * (1 - 0.3 * clamp(abs(vf) / maxs, 0.0, 1.0))
        if self.drifting:
            yaw = s['turn_rate'] * (0.55 * self.drift_dir + 0.6 * steer * (0.75 if steer * self.drift_dir > 0 else 1.0)) * 1.15
        else:
            yaw = s['turn_rate'] * steer
        self.heading -= yaw * speed_f * (1.0 if vf >= 0 else -1.0) * dt
        self.steer_vis += (steer - self.steer_vis) * min(1.0, dt * 10)
        grip = s['drift_grip'] if self.drifting else (7.0 if boosting else 9.5)
        vl *= exp(-grip * dt)
        self.slip = vl
        nfx = sin(self.heading)
        nfz = cos(self.heading)
        self.vx = nfx * vf + (-nfz) * vl
        self.vz = nfz * vf + nfx * vl
        self.x += self.vx * dt
        self.z += self.vz * dt

        # 다른 카트와 충돌 (원)
        for o in others:
            dx = self.x - o[0]
            dz = self.z - o[1]
            dist = math.hypot(dx, dz)
            if 0.001 < dist < 2.5:
                push = (2.5 - dist) / dist * 0.55
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
        elif t.pads:
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
        rb = 1.0
        if rubber and player_total is not None:
            gap = (kart.total - player_total) * tr.ds
            rb = clamp(1 - gap / 900.0, 0.9, 1.08)
        curve = tr.turn[q.idx]
        target = kart.stats['max_speed'] * self.skill * rb * (1 - clamp(curve * 0.55 - 0.08, 0.0, 0.5))
        sp = kart.speed
        inp = {'steer': steer, 'throttle': 1.0 if sp < target else 0.15, 'brake': 0.7 if sp > target + 7 else 0.0, 'drift': False}
        if curve > 0.55 and sp > 36 and self.skill > 0.9 and abs(steer) > 0.45:
            inp['drift'] = True
        if sp < 2:
            self.stuck += dt
            if self.stuck > 2.5:
                kart.respawn()
                self.stuck = 0.0
        else:
            self.stuck = 0.0
        return inp
