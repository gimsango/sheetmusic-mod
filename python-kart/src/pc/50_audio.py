
# ============================================================================
#  [PC] 사운드: 코드로 WAV 를 합성해서 임시 폴더에 저장 -> Panda3D 오디오로 재생
# ============================================================================
def synth(freq, ms, vol=0.35, wave_='sine', slide=1.0, decay=True, rate=22050):
    n = int(rate * ms / 1000.0)
    buf = array.array('h')
    ph = 0.0
    for i in range(n):
        t = i / float(n)
        ph += freq * (1 + (slide - 1) * t) / rate
        f = ph % 1.0
        if wave_ == 'sine':
            x = math.sin(TAU * ph)
        elif wave_ == 'square':
            x = 1.0 if f < 0.5 else -1.0
        elif wave_ == 'saw':
            x = 2 * f - 1
        else:
            x = 4 * abs(f - 0.5) - 1
        env = (1 - t) ** 1.5 if decay else min(1.0, t * 25) * min(1.0, (1 - t) * 25)
        buf.append(int(x * env * vol * 32767))
    return buf


def synth_noise(ms, vol=0.3, rise=False, loop=False, rate=22050):
    n = int(rate * ms / 1000.0)
    buf = array.array('h')
    rnd = Rng(4242)
    lp = 0.0
    for i in range(n):
        t = i / float(n)
        lp += (rnd() * 2 - 1 - lp) * (0.25 + (0.5 * t if rise else 0.0))
        env = (min(1.0, t * 8) * (1 - t)) if not loop else 1.0
        buf.append(int(lp * env * vol * 32767))
    return buf


def synth_engine(rate=22050):
    dur = 0.4
    f = 90.0
    cycles = int(round(f * dur))
    n = int(rate * dur)
    buf = array.array('h')
    for k in range(n):
        ph = (k / float(n)) * cycles
        fr = ph % 1.0
        x = 0.5 * (2 * fr - 1) + 0.35 * (1.0 if fr < 0.4 else -1.0) + 0.25 * math.sin(TAU * ph * 2)
        buf.append(int(x * 0.3 * 32767))
    return buf


class Audio(object):
    def __init__(self, app, enabled=True):
        self.ok = False
        self.app = app
        self.enabled = enabled
        self.snd = {}
        self.eng_on = False
        self.drift_on = False
        self.vol = dict(master=1.0, sfx=1.0, engine=0.8, music=0.5)
        self.music_on = True
        self.music_snd = None
        self.music_key = None
        self.pending = None
        self.rate = 1.0
        self.dir = None
        try:
            _clean_old_temp('kart3d_snd_')
            d = self.dir = tempfile.mkdtemp(prefix='kart3d_snd_')
            import atexit
            import shutil
            atexit.register(shutil.rmtree, d, True)          # 끝날 때 임시 소리 파일 정리
            defs = {
                'count': synth(520, 160, 0.28, 'square'), 'go': synth(1040, 520, 0.28, 'square'), 'boost': synth_noise(520, 0.38, True),
                'bump': synth(110, 170, 0.5, 'sine', 0.45), 'tier': synth(1500, 70, 0.2, 'tri'), 'lap': synth(740, 260, 0.28, 'tri', 1.34),
                'finish': synth(520, 700, 0.3, 'tri', 2.0), 'click': synth(900, 40, 0.2, 'tri'),
                'engine': synth_engine(), 'driftl': synth_noise(500, 0.16, False, True),
                'iroll': synth(1300, 30, 0.12, 'square'), 'iget': synth(880, 150, 0.26, 'tri', 1.5), 'iuse': synth_noise(220, 0.3, True),
                'ihit': synth(190, 280, 0.45, 'square', 0.4), 'iboom': synth_noise(650, 0.55), 'izap': synth(1500, 320, 0.25, 'square', 0.25),
                'iblock': synth(1250, 170, 0.26, 'tri', 1.2),
            }
            for name, buf in defs.items():
                path = os.path.join(d, name + '.wav')
                _write_wav(path, buf, 22050)
                self.snd[name] = app.loader.loadSfx(Filename.fromOsSpecific(path).getFullpath())
            self.snd['engine'].setLoop(True)
            self.snd['driftl'].setLoop(True)
            self.ok = True
        except Exception:
            self.ok = False

    # ---- 볼륨 ----
    def set_volumes(self, master, sfx, engine, music, music_on=True):
        self.vol = dict(master=clamp(master, 0, 1), sfx=clamp(sfx, 0, 1), engine=clamp(engine, 0, 1), music=clamp(music, 0, 1))
        self.music_on = bool(music_on)
        if self.music_snd is not None:
            try:
                if self.music_on and self.enabled:
                    self.music_snd.setVolume(self._mv())
                    if self.music_snd.status() != self.music_snd.PLAYING:
                        self.music_snd.play()
                else:
                    self.music_snd.stop()
            except Exception:
                pass

    def _mv(self):
        return 0.55 * self.vol['master'] * self.vol['music']

    def play(self, name, vol=1.0):
        if not (self.ok and self.enabled):
            return
        s = self.snd.get(name)
        if s is not None:
            try:
                s.setVolume(vol * self.vol['master'] * self.vol['sfx'])
                s.play()
            except Exception:
                pass

    # ---- 배경음악: 처음 한 번 만들 때만 시간이 걸려서 뒤에서 만든다 ----
    def music(self, kind, seed=0):
        if not self.ok:
            return
        key = (kind, int(seed))
        if key == self.music_key:
            return
        self.music_key = key
        self.rate = 1.0
        if self.music_snd is not None:
            try:
                self.music_snd.stop()
            except Exception:
                pass
            self.music_snd = None
        path = os.path.join(self.dir, 'music_%s_%d.wav' % key)
        if os.path.isfile(path):
            self.pending = (key, path)
            return

        def work():
            try:
                buf = make_music(kind, seed, MUSIC_RATE)
                tmp = path + '.part'
                _write_wav(tmp, buf, MUSIC_RATE)
                os.replace(tmp, path)
                self.pending = (key, path)
            except Exception:
                pass
        threading.Thread(target=work, daemon=True).start()

    def tick(self):
        p = self.pending
        if p is None or p[0] != self.music_key:
            return
        self.pending = None
        try:
            m = self.app.loader.loadMusic(Filename.fromOsSpecific(p[1]).getFullpath())
            m.setLoop(True)
            m.setVolume(self._mv())
            m.setPlayRate(self.rate)
            self.music_snd = m
            if self.music_on and self.enabled:
                m.play()
        except Exception:
            self.music_snd = None

    def music_rate(self, rate):
        """마지막 바퀴에서 음악을 살짝 빠르게 (재생 속도 = 빠르기 + 음높이)"""
        self.rate = rate
        if self.music_snd is not None:
            try:
                self.music_snd.setPlayRate(rate)
            except Exception:
                pass

    def engine(self, ratio, throttle, drifting, offroad):
        if not (self.ok and self.enabled):
            return
        try:
            e = self.snd['engine']
            if not self.eng_on:
                e.setVolume(0.0)
                e.play()
                self.eng_on = True
            e.setPlayRate(0.55 + clamp(ratio, 0, 1.3) * 1.9)
            e.setVolume((0.22 + 0.25 * throttle) * self.vol['master'] * self.vol['engine'])
            want = drifting or (offroad and ratio > 0.2)
            d = self.snd['driftl']
            if want and not self.drift_on:
                d.setVolume(0.5 * self.vol['master'] * self.vol['sfx'])
                d.play()
                self.drift_on = True
            elif not want and self.drift_on:
                d.stop()
                self.drift_on = False
            if self.drift_on:
                d.setVolume((0.55 if drifting else 0.22) * self.vol['master'] * self.vol['sfx'])
        except Exception:
            pass

    def silence(self):
        if not self.ok:
            return
        try:
            self.snd['engine'].stop()
            self.snd['driftl'].stop()
        except Exception:
            pass
        self.eng_on = False
        self.drift_on = False


def _clean_old_temp(prefix, max_age=24 * 3600):
    """예전에 비정상 종료돼서 남은 임시 폴더 정리 (하루 넘은 것만)"""
    try:
        import shutil
        base = tempfile.gettempdir()
        now = time.time()
        for name in os.listdir(base):
            if name.startswith(prefix):
                p = os.path.join(base, name)
                if os.path.isdir(p) and now - os.path.getmtime(p) > max_age:
                    shutil.rmtree(p, True)
    except Exception:
        pass


def _write_wav(path, buf, rate):
    w = wave.open(path, 'wb')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(buf.tobytes())
    w.close()
