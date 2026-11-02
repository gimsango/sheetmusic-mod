
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
        self.enabled = enabled
        self.snd = {}
        self.eng_on = False
        self.drift_on = False
        try:
            d = tempfile.mkdtemp(prefix='kart3d_snd_')
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
                w = wave.open(path, 'wb')
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(22050)
                w.writeframes(buf.tobytes())
                w.close()
                self.snd[name] = app.loader.loadSfx(Filename.fromOsSpecific(path).getFullpath())
            self.snd['engine'].setLoop(True)
            self.snd['driftl'].setLoop(True)
            self.ok = True
        except Exception:
            self.ok = False

    def play(self, name, vol=1.0):
        if not (self.ok and self.enabled):
            return
        s = self.snd.get(name)
        if s is not None:
            try:
                s.setVolume(vol)
                s.play()
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
            e.setVolume(0.22 + 0.25 * throttle)
            want = drifting or (offroad and ratio > 0.2)
            d = self.snd['driftl']
            if want and not self.drift_on:
                d.setVolume(0.5)
                d.play()
                self.drift_on = True
            elif not want and self.drift_on:
                d.stop()
                self.drift_on = False
            if self.drift_on:
                d.setVolume(0.55 if drifting else 0.22)
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
