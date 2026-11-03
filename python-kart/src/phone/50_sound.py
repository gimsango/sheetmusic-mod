# ============================================================================
#  [폰] 사운드: 파일 없이 코드로 합성 (엔진/드리프트/효과음 + 배경음악)
#  채널 0 = 엔진, 1 = 드리프트, 2 = 배경음악 (예약해서 효과음이 뺏지 않게)
#  볼륨: 전체 x (효과음 / 엔진 / 음악) - 설정 화면에서 조절
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
        self.vol = dict(master=1.0, sfx=1.0, engine=0.8, music=0.5)
        self.music_on = True
        self.music_key = None          # 지금 들려줘야 할 곡
        self.cur_key = None            # 지금 채널에서 나오는 곡
        self.music_cache = {}          # 곡 -> Sound (최근 2곡만)
        self.raw_ready = {}            # 뒤에서 다 만든 곡 (아직 Sound 로 안 바꾼 것)
        self.gen_busy = False
        self.raw_ok = True
        self.stereo = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(self.RATE, -16, 1, 512)
            fmt = pygame.mixer.get_init()
            self.rate = fmt[0]
            self.stereo = fmt[2] >= 2
            self.raw_ok = fmt[1] == -16 and fmt[2] in (1, 2)   # 16bit 가 아니면 WAV 로 넘겨서 pygame 이 변환
            if pygame.mixer.get_num_channels() < 8:
                pygame.mixer.set_num_channels(8)
            pygame.mixer.set_reserved(3)
            self.eng_ch = pygame.mixer.Channel(0)
            self.drift_ch = pygame.mixer.Channel(1)
            self.mus_ch = pygame.mixer.Channel(2)
            self.ok = True
            self._build()
        except Exception:
            self.ok = False

    def _mk(self, samples, rate=None):
        """모노 16bit 샘플 -> Sound. 장치가 스테레오면 두 채널로 복사, 형식/빠르기가 다르면 WAV 로 넘겨서 변환"""
        rate = rate or self.rate
        if self.raw_ok and rate == self.rate:
            if self.stereo:
                st = array.array('h', bytes(4 * len(samples)))
                st[0::2] = samples
                st[1::2] = samples
                samples = st
            return pygame.mixer.Sound(buffer=samples.tobytes())
        import io
        import wave
        bio = io.BytesIO()
        w = wave.open(bio, 'wb')
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(rate))
        w.writeframes(samples.tobytes())
        w.close()
        return pygame.mixer.Sound(file=io.BytesIO(bio.getvalue()))

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
        S['iroll'] = self._tone(1300, 30, 0.12, 'square')
        S['iget'] = self._tone(880, 150, 0.26, 'tri', 1.5)
        S['iuse'] = self._noise(220, 0.3, True)
        S['ihit'] = self._tone(190, 280, 0.45, 'square', 0.4)
        S['iboom'] = self._noise(650, 0.55)
        S['izap'] = self._tone(1500, 320, 0.25, 'square', 0.25)
        S['iblock'] = self._tone(1250, 170, 0.26, 'tri', 1.2)
        for i, f0 in enumerate((58.0, 74.0, 95.0, 122.0, 156.0, 200.0)):
            dur = 0.2
            cycles = max(1, int(round(f0 * dur)))
            n = int(self.rate * dur)
            buf = array.array('h')
            for k in range(n):
                ph = (k / float(n)) * cycles
                fr = ph % 1.0
                x = 0.5 * (2 * fr - 1) + 0.35 * (1.0 if fr < 0.4 else -1.0) + 0.25 * math.sin(TAU * ph * 2)
                buf.append(int(x * 0.2 * 32767))
            self.eng.append(self._mk(buf))

    # ---- 볼륨 / 켜고 끄기 ----
    def set_volumes(self, master, sfx, engine, music, music_on=True):
        self.vol = dict(master=clamp(master, 0, 1), sfx=clamp(sfx, 0, 1), engine=clamp(engine, 0, 1), music=clamp(music, 0, 1))
        on = bool(music_on)
        if on != self.music_on:
            self.music_on = on
            if not on:
                self._stop_music()
        if self.ok:
            try:
                self.mus_ch.set_volume(self._mv())
            except Exception:
                pass

    def set_enabled(self, flag):
        self.enabled = bool(flag)
        if not self.enabled:
            self.silence()
            self._stop_music()

    def _mv(self):
        return 0.6 * self.vol['master'] * self.vol['music']

    def play(self, name, vol=1.0):
        if not (self.ok and self.enabled):
            return
        s = self.sounds.get(name)
        if s is not None:
            try:
                s.set_volume(clamp(vol * self.vol['master'] * self.vol['sfx'], 0.0, 1.0))
                s.play()
            except Exception:
                pass

    # ---- 배경음악: 처음 듣는 곡은 뒤에서 만들고(게임이 멈추지 않게), 다 되면 tick() 에서 틀기 ----
    def music(self, kind, seed=0):
        if not self.ok:
            return
        key = (kind, int(seed))
        if key == self.music_key:
            return
        self.music_key = key
        if self.cur_key is not None and self.cur_key != key:
            self._stop_music(300)

    def _stop_music(self, fade=0):
        self.cur_key = None
        if not self.ok:
            return
        try:
            if fade:
                self.mus_ch.fadeout(fade)
            else:
                self.mus_ch.stop()
        except Exception:
            pass

    def _gen(self):
        try:
            while True:
                key = self.music_key
                if key is None or key in self.music_cache or key in self.raw_ready:
                    break
                buf = make_music(key[0], key[1], MUSIC_RATE)
                self.raw_ready = {key: buf}           # 가장 최근에 원한 곡만 남긴다
        except Exception:
            pass
        self.gen_busy = False

    def tick(self):
        """매 프레임 (메인 스레드): 곡이 준비됐으면 틀기"""
        if not (self.ok and self.enabled and self.music_on):
            return
        key = self.music_key
        if key is None or key == self.cur_key:
            return
        snd = self.music_cache.get(key)
        if snd is None:
            buf = self.raw_ready.pop(key, None)
            if buf is None:
                if not self.gen_busy:
                    self.gen_busy = True
                    threading.Thread(target=self._gen, daemon=True).start()
                return
            try:
                snd = self._mk(buf, MUSIC_RATE)
            except Exception:
                self.music_key = None
                return
            for k in list(self.music_cache.keys()):
                if len(self.music_cache) < 2:
                    break
                del self.music_cache[k]
            self.music_cache[key] = snd
        try:
            self.mus_ch.set_volume(self._mv())
            self.mus_ch.play(snd, loops=-1, fade_ms=700)
            self.mus_ch.set_volume(self._mv())
            self.cur_key = key
        except Exception:
            self.cur_key = key

    def engine(self, ratio, throttle, boosting, drifting, offroad):
        if not (self.ok and self.enabled):
            return
        try:
            band = int(clamp(ratio * 5.4 + (0.6 if boosting else 0.0), 0, 5))
            if band != self.band:
                self.band = band
                self.eng_ch.play(self.eng[band], loops=-1)
            self.eng_ch.set_volume((0.22 + 0.2 * throttle) * self.vol['master'] * self.vol['engine'])
            want = (drifting or (offroad and ratio > 0.2))
            if want and not self.drift_on:
                self.drift_ch.play(self.sounds['drift'], loops=-1)
                self.drift_on = True
            elif not want and self.drift_on:
                self.drift_ch.stop()
                self.drift_on = False
            if self.drift_on:
                self.drift_ch.set_volume((0.6 if drifting else 0.25) * self.vol['master'] * self.vol['sfx'])
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
