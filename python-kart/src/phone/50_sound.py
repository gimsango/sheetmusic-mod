
# ============================================================================
#  [폰] 사운드: 파일 없이 코드로 합성 (엔진/드리프트/효과음)
# ============================================================================
class Sfx(object):
    RATE = 22050

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.ok = False
        self.sounds = {}
        self.eng = []
        self.band = -1
        self.drift_on = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(self.RATE, -16, 1, 512)
            self.rate = pygame.mixer.get_init()[0]
            self.ok = True
            self.eng_ch = pygame.mixer.Channel(0)
            self.drift_ch = pygame.mixer.Channel(1)
            self._build()
        except Exception:
            self.ok = False

    def _mk(self, samples):
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _tone(self, freq, ms, vol=0.35, wave='sine', slide=1.0, decay=True):
        n = int(self.rate * ms / 1000.0)
        buf = array.array('h')
        ph = 0.0
        for i in range(n):
            t = i / float(n)
            ph += freq * (1 + (slide - 1) * t) / self.rate
            f = ph % 1.0
            if wave == 'sine':
                x = math.sin(TAU * ph)
            elif wave == 'square':
                x = 1.0 if f < 0.5 else -1.0
            elif wave == 'saw':
                x = 2 * f - 1
            else:
                x = 4 * abs(f - 0.5) - 1
            env = (1 - t) ** 1.5 if decay else min(1.0, t * 25) * min(1.0, (1 - t) * 25)
            buf.append(int(x * env * vol * 32767))
        return self._mk(buf)

    def _noise(self, ms, vol=0.3, rise=False, loop=False):
        n = int(self.rate * ms / 1000.0)
        buf = array.array('h')
        rnd = Rng(4242)
        lp = 0.0
        for i in range(n):
            t = i / float(n)
            lp += (rnd() * 2 - 1 - lp) * (0.25 + (0.5 * t if rise else 0.0))
            env = (min(1.0, t * 8) * (1 - t)) if not loop else 1.0
            buf.append(int(lp * env * vol * 32767))
        return self._mk(buf)

    def _build(self):
        S = self.sounds
        S['count'] = self._tone(520, 160, 0.28, 'square')
        S['go'] = self._tone(1040, 520, 0.28, 'square')
        S['boost'] = self._noise(520, 0.38, True)
        S['bump'] = self._tone(110, 170, 0.5, 'sine', 0.45)
        S['tier'] = self._tone(1500, 70, 0.2, 'tri')
        S['lap'] = self._tone(740, 260, 0.28, 'tri', 1.34)
        S['finish'] = self._tone(520, 700, 0.3, 'tri', 2.0)
        S['click'] = self._tone(900, 40, 0.2, 'tri')
        S['drift'] = self._noise(260, 0.16, False, True)
        for i, f0 in enumerate((58.0, 74.0, 95.0, 122.0, 156.0, 200.0)):
            dur = 0.2
            cycles = max(1, int(round(f0 * dur)))
            f = cycles / dur
            n = int(self.rate * dur)
            buf = array.array('h')
            for k in range(n):
                ph = (k / float(n)) * cycles
                fr = ph % 1.0
                x = 0.5 * (2 * fr - 1) + 0.35 * (1.0 if fr < 0.4 else -1.0) + 0.25 * math.sin(TAU * ph * 2)
                buf.append(int(x * 0.2 * 32767))
            self.eng.append(self._mk(buf))

    def play(self, name, vol=1.0):
        if not (self.ok and self.enabled):
            return
        s = self.sounds.get(name)
        if s is not None:
            try:
                s.set_volume(vol)
                s.play()
            except Exception:
                pass

    def engine(self, ratio, throttle, boosting, drifting, offroad):
        if not (self.ok and self.enabled):
            return
        try:
            band = int(clamp(ratio * 5.4 + (0.6 if boosting else 0.0), 0, 5))
            if band != self.band:
                self.band = band
                self.eng_ch.play(self.eng[band], loops=-1)
            self.eng_ch.set_volume(0.22 + 0.2 * throttle)
            want = (drifting or (offroad and ratio > 0.2))
            if want and not self.drift_on:
                self.drift_ch.play(self.sounds['drift'], loops=-1)
                self.drift_on = True
            elif not want and self.drift_on:
                self.drift_ch.stop()
                self.drift_on = False
            if self.drift_on:
                self.drift_ch.set_volume(0.6 if drifting else 0.25)
        except Exception:
            pass

    def silence(self):
        if not self.ok:
            return
        try:
            self.eng_ch.stop()
            self.drift_ch.stop()
            self.band = -1
            self.drift_on = False
        except Exception:
            pass
