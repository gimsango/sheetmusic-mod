
# ----------------------------------------------------------------------------
#  레이스 진행 (솔로/멀티 공통): 카운트다운, 시뮬레이션, 순위, 네트워크 동기화
# ----------------------------------------------------------------------------
class Racer(object):
    """레이스 참가자 한 명 (플레이어/봇/원격 플레이어). 렌더러는 이 객체의 값만 읽으면 된다."""

    def __init__(self, rid, name, kart_id, slot, kind):
        self.id = rid
        self.name = name
        self.kart_id = kart_id
        self.slot = slot
        self.kind = kind            # 'local' | 'bot' | 'remote'
        self.sim = None
        self.brain = None
        self.finished = False
        self.finish_time = 0.0
        self.cur = None
        self.tgt = None
        # ---- 렌더링용 상태 ----
        self.x = self.y = self.z = 0.0
        self.h = 0.0
        self.speed = 0.0
        self.total = 0.0
        self.vx = self.vz = 0.0
        self.drifting = False
        self.tier = 0
        self.drift_dir = 0.0
        self.boosting = False
        self.steer = 0.0
        self.slip = 0.0
        self.up = (0.0, 1.0, 0.0)
        self.idx = 0
        self.offroad = False
        self.wall_hit = 0.0

    def sync_visual(self, track, dt):
        s = self.sim
        if s is not None:
            self.x, self.y, self.z, self.h = s.x, s.y, s.z, s.heading
            self.speed = s.speed
            self.total = s.total
            self.vx, self.vz = s.vx, s.vz
            self.drifting = s.drifting
            self.tier = s.drift_tier
            self.drift_dir = s.drift_dir
            self.boosting = s.boost_t > 0
            self.steer = s.steer_vis
            self.slip = s.slip
            self.up = (s.upx, s.upy, s.upz)
            self.idx = s.q.idx
            self.offroad = s.offroad
            self.wall_hit = s.wall_hit
            return
        c, t = self.cur, self.tgt
        f = 1.0 - math.exp(-14.0 * dt)
        c['x'] += (t['x'] - c['x']) * f
        c['y'] += (t['y'] - c['y']) * f
        c['z'] += (t['z'] - c['z']) * f
        dh = wrap_pi(t['h'] - c['h'])
        c['h'] += dh * f
        c['sp'] += (t['sp'] - c['sp']) * f
        c['total'] += (t['total'] - c['total']) * f
        self.x, self.y, self.z, self.h = c['x'], c['y'], c['z'], c['h']
        self.speed = c['sp']
        self.total = c['total']
        self.vx = math.sin(self.h) * self.speed
        self.vz = math.cos(self.h) * self.speed
        self.drifting = t['dr'] > 0
        self.tier = max(0, t['dr'] - 1)
        self.boosting = t['bo'] > 0
        self.steer = clamp(-dh * 2.0, -1.0, 1.0)
        if self.drifting:
            self.drift_dir = sign(self.steer) or self.drift_dir
        self.slip = 0.0
        self.idx = int(round(self.total)) % track.N
        self.up = track.surface_normal(self.idx)


class Race(object):
    def __init__(self, map_id, laps, entries, multi=False, is_host=True, countdown=5.0, net=None, auto_local=False):
        self.map_id = map_id
        self.track = Track(map_id)
        self.laps = laps
        self.multi = multi
        self.is_host = is_host
        self.net = net
        self.racers = []
        self.local = None
        rnd = Rng(map_id * 31 + 7)
        for e in entries:
            rc = Racer(e['id'], e['name'], e['kart'], e['slot'], e['kind'])
            if rc.kind != 'remote':
                rc.sim = KartSim(self.track, rc.kart_id, rc.slot)
                rc.total = rc.sim.total
            else:
                p = self.track.spawn_pose(rc.slot)
                rc.cur = dict(x=p['x'], y=p['y'], z=p['z'], h=p['heading'], sp=0.0, total=p['prog'])
                rc.tgt = dict(rc.cur, dr=0, bo=0)
            if rc.kind == 'bot':
                rc.brain = BotBrain(rnd)
            if rc.kind == 'local':
                self.local = rc
                if auto_local:
                    rc.brain = BotBrain(rnd)
            rc.sync_visual(self.track, 0.0)
            self.racers.append(rc)
        self.start_at = time.monotonic() + countdown
        self.countdown = countdown
        self.phase = 'count'          # count -> run
        self.t = 0.0
        self.acc = 0.0
        self.last_count = 99
        self.last_lap = 1
        self.events = []
        self.finish_order = []
        self.send_t = 0.0
        self.auto_local = auto_local
        self.count_left = countdown

    # ---- 진행 --------------------------------------------------------------
    def update(self, dt, inp):
        """프레임마다 호출. inp = {'steer','throttle','brake','drift'} (로컬 플레이어 입력)"""
        self.events = []
        dt = min(dt, 0.1)
        if self.phase == 'count':
            left = self.start_at - time.monotonic()
            self.count_left = left
            if left <= 0:
                self.phase = 'run'
                self.t = 0.0
                self.events.append(('go',))
            else:
                n = int(math.ceil(left))
                if n != self.last_count:
                    self.last_count = n
                    self.events.append(('count', n))
        self.acc += dt
        steps = 0
        while self.acc >= STEP and steps < 6:
            self._step(STEP, inp)
            self.acc -= STEP
            steps += 1
        if steps >= 6:
            self.acc = 0.0
        for rc in self.racers:
            rc.sync_visual(self.track, dt)
        self._net_tick(dt)

    def _step(self, dt, inp):
        running = self.phase == 'run'
        racers = self.racers
        N = self.track.N
        others_all = [(r.x, r.z, r.vx, r.vz) for r in racers]
        zero = {'steer': 0.0, 'throttle': 0.0, 'brake': 0.0, 'drift': False}
        for k, rc in enumerate(racers):
            sim = rc.sim
            if sim is None:
                continue
            if not running:
                use = zero
            elif rc.kind == 'local' and not rc.finished and not self.auto_local:
                use = inp
            else:
                if rc.brain is None:
                    rc.brain = BotBrain(Rng(5))
                loc = self.local
                use = rc.brain.drive(sim, dt, loc.total if loc is not None else None, not self.multi)
            if not running:
                sim.vx *= 0.9
                sim.vz *= 0.9
            others = others_all[:k] + others_all[k + 1:]
            sim.update(dt, use, others)
            # 다음 서브스텝에서 쓸 위치 갱신
            others_all[k] = (sim.x, sim.z, sim.vx, sim.vz)
            rc.total = sim.total
            if running:
                if not rc.finished and sim.total >= self.laps * N:
                    rc.finished = True
                    rc.finish_time = self.t
                    sim.finished = True
                    self.finish_order.append(rc)
                    if rc.kind == 'local':
                        self.events.append(('finish',))
                        if self.net is not None and self.multi:
                            self.net.send({'t': 'fin', 'time': round(rc.finish_time, 2)})
            if rc.kind == 'local':
                for e in sim.events:
                    self.events.append(('sim', e))
                lap = min(self.laps, sim.lap)
                if lap > self.last_lap and running:
                    self.events.append(('lap', lap, lap == self.laps))
                    self.last_lap = lap
        if running:
            self.t += dt

    def respawn_local(self):
        if self.local is not None and self.local.sim is not None and self.phase == 'run':
            self.local.sim.respawn()

    def ranking(self):
        def key(r):
            return (1e9 - r.finish_time) if r.finished else r.total
        return sorted(self.racers, key=key, reverse=True)

    def local_finished(self):
        return self.local is not None and self.local.finished

    # ---- 네트워크 -----------------------------------------------------------
    def _net_tick(self, dt):
        net = self.net
        if not self.multi or net is None or not net.connected or self.local is None:
            return
        self.send_t += dt
        if self.send_t < 0.05:
            return
        self.send_t = 0.0
        s = self.local.sim
        net.send({'t': 's', 'x': round(s.x, 2), 'y': round(s.y, 2), 'z': round(s.z, 2), 'h': round(s.heading, 3), 'sp': round(s.speed, 1),
                  'tp': round(s.total, 2), 'dr': (s.drift_tier + 1) if s.drifting else 0, 'bo': 1 if s.boost_t > 0 else 0})
        if self.is_host:
            bots = []
            for rc in self.racers:
                if rc.kind == 'bot':
                    b = rc.sim
                    bots.append([rc.id, round(b.x, 2), round(b.y, 2), round(b.z, 2), round(b.heading, 3), round(b.speed, 1), round(b.total, 2),
                                 (b.drift_tier + 1) if b.drifting else 0, 1 if b.boost_t > 0 else 0, round(rc.finish_time, 2) if rc.finished else 0])
            if bots:
                net.send({'t': 'b', 'b': bots})

    def _find(self, rid):
        for rc in self.racers:
            if rc.id == rid:
                return rc
        return None

    def handle_message(self, m):
        t = m.get('t')
        if t == 's':
            rc = self._find(m.get('id'))
            if rc is not None and rc.tgt is not None:
                rc.tgt.update(x=m['x'], y=m['y'], z=m['z'], h=m['h'], sp=m['sp'], total=m['tp'], dr=m['dr'], bo=m['bo'])
        elif t == 'b':
            for a in m.get('b', []):
                rc = self._find(a[0])
                if rc is not None and rc.tgt is not None:
                    rc.tgt.update(x=a[1], y=a[2], z=a[3], h=a[4], sp=a[5], total=a[6], dr=a[7], bo=a[8])
                    if a[9] and not rc.finished:
                        rc.finished = True
                        rc.finish_time = a[9]
        elif t == 'fin':
            rc = self._find(m.get('id'))
            if rc is not None and not rc.finished:
                rc.finished = True
                rc.finish_time = float(m.get('time', self.t))
                self.events.append(('fin', rc.name))
        elif t == 'left':
            rc = self._find(m.get('id'))
            if rc is not None:
                self.racers.remove(rc)
                self.events.append(('left', rc.name))


def solo_entries(name, kart_id, bots, seed=None):
    rnd = Rng(seed if seed is not None else (int(time.time() * 1000) & 0xFFFFFFFF))
    me = int(bots * 0.6)
    entries = []
    n = 0
    for i in range(bots + 1):
        if i == me:
            entries.append(dict(id='me', name=name, kart=kart_id, slot=i, kind='local'))
        else:
            n += 1
            entries.append(dict(id='b%d' % i, name='BOT %d' % n, kart=int(rnd() * KART_COUNT), slot=i, kind='bot'))
    return entries
