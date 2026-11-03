
# ----------------------------------------------------------------------------
#  배경음악: 코드로 만드는 반복 곡 -> 16bit 모노 (파일 필요 없음, 폰/PC 같은 생성기)
#  16마디 = A 부분 8마디 + B 부분 8마디 (코드 진행/베이스/드럼/멜로디가 바뀜), 끝이 처음과 이어져서 끊김 없이 반복
#  악기: 패드(화음) + 베이스 + 아르페지오 + 멜로디(메아리) + 드럼(킥/스네어/하이햇/심벌)
#  메뉴 곡 1개 + 레이스 곡 16종 (맵마다 조/빠르기/진행/리듬이 다름)
#  같은 음은 한 번만 만들어서 재사용 -> PC 에서 한 곡 0.2~0.4초, 폰은 뒤에서 만들어서 렉 없음
# ----------------------------------------------------------------------------
MUSIC_RATE = 22050
MUSIC_STYLES = 16
_WT = 256


def _wave_tables():
    t = {}
    t['sine'] = [math.sin(TAU * i / _WT) for i in range(_WT)]
    t['tri'] = [4.0 * abs(i / float(_WT) - 0.5) - 1.0 for i in range(_WT)]
    t['saw'] = [2.0 * i / _WT - 1.0 for i in range(_WT)]
    t['sq'] = [1.0 if i < _WT // 2 else -1.0 for i in range(_WT)]
    t['pulse'] = [1.0 if i < _WT // 4 else -0.35 for i in range(_WT)]
    # 부드러운 톱니 (고조파 몇 개만) - 귀가 덜 아픈 베이스/리드
    t['soft'] = [sum(math.sin(TAU * k * i / _WT) / k for k in range(1, 6)) * 0.55 for i in range(_WT)]
    t['organ'] = [(math.sin(TAU * i / _WT) + 0.5 * math.sin(TAU * 2 * i / _WT) + 0.25 * math.sin(TAU * 4 * i / _WT)) * 0.6 for i in range(_WT)]
    # 종소리 비슷한 맑은 소리 (메뉴 멜로디)
    t['bell'] = [(math.sin(TAU * i / _WT) * 0.75 + math.sin(TAU * 3 * i / _WT) * 0.22 + math.sin(TAU * 5 * i / _WT) * 0.08) for i in range(_WT)]
    return t


_TABLES = None


def _midi_hz(n):
    return 440.0 * 2.0 ** ((n - 69) / 12.0)


def _note(table, freq, n, rate, vol, attack, release, sustain=1.0):
    """표를 훑어서 음 하나 (어택 -> 감쇠 -> 유지 -> 끝부분 페이드)"""
    n = int(n)
    if n <= 0:
        return []
    a = min(n, max(1, int(attack * rate)))
    r = max(1, int(release * rate))
    env = [vol * i / a for i in range(a)]
    d = min(r, n - a)
    if d > 0:
        k = (1.0 - sustain) / r
        env.extend([vol * (1.0 - k * j) for j in range(d)])
    if n - a - d > 0:
        env.extend([vol * sustain] * (n - a - d))
    t0 = max(0, n - r)
    inv = 1.0 / r
    env[t0:] = [e * (n - i) * inv for i, e in enumerate(env[t0:], t0)]
    stepf = freq * _WT / float(rate)
    return [table[int(i * stepf) & 255] * e for i, e in enumerate(env)]


def _add(mix, start, samples, gain=1.0):
    """곡 끝을 넘어가는 부분은 처음으로 이어 붙여서 이음새 없이 반복되게 (mix 는 array('d'))"""
    total = len(mix)
    ln = len(samples)
    if ln == 0 or total == 0:
        return
    start %= total
    pos = 0
    while pos < ln:
        k = min(total - start, ln - pos)
        seg = samples[pos:pos + k]
        if gain == 1.0:
            mix[start:start + k] = array.array('d', [a + b for a, b in zip(mix[start:start + k], seg)])
        else:
            mix[start:start + k] = array.array('d', [a + b * gain for a, b in zip(mix[start:start + k], seg)])
        pos += k
        start = 0


def _drums(rate, rnd):
    n = int(rate * 0.22)
    kick = []
    ph = 0.0
    for i in range(n):
        t = i / float(n)
        f = 150.0 * (1 - t) ** 2.2 + 42.0
        ph += f / rate
        kick.append(math.sin(TAU * ph) * (1 - t) ** 1.6 * 0.95)
    n = int(rate * 0.16)
    snare = []
    lp = 0.0
    for i in range(n):
        t = i / float(n)
        lp += (rnd() * 2 - 1 - lp) * 0.6
        snare.append((lp * 0.7 + math.sin(TAU * 190 * i / rate) * 0.35 * (1 - t)) * (1 - t) ** 2.0 * 0.6)
    n = int(rate * 0.05)
    hat = []
    prev = 0.0
    for i in range(n):
        t = i / float(n)
        x = rnd() * 2 - 1
        hat.append((x - prev) * (1 - t) ** 3 * 0.22)
        prev = x
    n = int(rate * 0.2)
    ohat = []
    prev = 0.0
    for i in range(n):
        t = i / float(n)
        x = rnd() * 2 - 1
        ohat.append((x - prev) * (1 - t) ** 1.5 * 0.16)
        prev = x
    n = int(rate * 1.3)
    crash = []
    prev = 0.0
    lp = 0.0
    for i in range(n):
        t = i / float(n)
        x = rnd() * 2 - 1
        lp += (x - lp) * 0.5
        crash.append((x - prev * 0.6 + lp * 0.3) * (1 - t) ** 2.4 * 0.2)
        prev = x
    return kick, snare, hat, ohat, crash


def make_music(style, seed, rate=MUSIC_RATE, bars=16):
    """style: 'menu' 또는 'race'. seed 로 조/빠르기/진행/리듬이 바뀐다. 반환: array('h') (모노, rate Hz)"""
    global _TABLES
    if _TABLES is None:
        _TABLES = _wave_tables()
    W = _TABLES
    menu = style == 'menu'
    r = Rng(hash32(int(seed) * 977 + (11 if menu else 29)))
    bpm = (90 + int(r() * 12)) if menu else (136 + int(r() * 20))
    minor = r() < (0.45 if menu else 0.62)
    scale = [0, 2, 3, 5, 7, 8, 10] if minor else [0, 2, 4, 5, 7, 9, 11]
    root = 45 + int(r() * 8)                       # A2 ~ E3
    if minor:
        progs = [[0, 5, 2, 6], [0, 3, 4, 4], [0, 5, 3, 4], [0, 6, 5, 4], [5, 6, 0, 0], [0, 2, 3, 4], [3, 4, 0, 5]]
    else:
        progs = [[0, 4, 5, 3], [0, 5, 3, 4], [0, 3, 0, 4], [5, 3, 0, 4], [0, 1, 4, 4], [3, 4, 2, 5], [0, 5, 1, 4]]
    ia = int(r() * len(progs))
    ib = (ia + 1 + int(r() * (len(progs) - 1))) % len(progs)
    prog = (progs[ia], progs[ib])
    spb = rate * 60.0 / bpm                        # 한 박의 샘플 수
    s16 = spb / 4.0
    bars = max(4, int(bars))
    half = bars // 2
    total = int(round(spb * 4 * bars))
    mix = array.array('d', bytes(8 * total))
    kick, snare, hat, ohat, crash = _drums(rate, r)
    snare_soft = [x * 0.55 for x in snare]
    cache = {}
    pads = {}

    def note(tname, midi, n, vol, attack, release, sustain):
        key = (tname, midi, int(n), vol, attack, release, sustain)
        s = cache.get(key)
        if s is None:
            s = cache[key] = _note(W[tname], _midi_hz(midi), n, rate, vol, attack, release, sustain)
        return s

    def tone(deg, octave, chord):
        o, d = divmod(deg, 7)
        m = root + scale[d] + 12 * (o + octave)
        if minor and chord % 7 == 4 and d == 6:    # 단조의 V 화음은 이끎음을 반음 올려서 (화성단음계) 끝맺음이 또렷하게
            m += 1
        return m

    # 리듬/음색 고르기 (A 와 B 가 다르게)
    bass_pats = [[1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0], [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1],
                 [1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1], [1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0]]
    ba = int(r() * len(bass_pats))
    bass_pat = (bass_pats[ba], bass_pats[(ba + 1 + int(r() * 3)) % len(bass_pats)])
    shapes = [[0, 1, 2, 1], [0, 2, 1, 2], [0, 1, 2, 3], [2, 1, 0, 1], [0, 2, 3, 2]]
    sa = int(r() * len(shapes))
    arp_shape = (shapes[sa], shapes[(sa + 2) % len(shapes)])
    lead_t = 'pulse' if r() < 0.5 else 'organ'
    bass_t = 'soft' if menu else ('saw' if r() < 0.5 else 'soft')
    mel_t = ('bell' if r() < 0.6 else 'sine') if menu else ('sq' if r() < 0.6 else 'pulse')

    # 멜로디: 강박은 화음 음, 약박은 이웃 음으로 걷기. 쉬는 칸이 있으면 앞 음을 늘인다 (A 는 8분음표, B 는 4분음표 위주)
    def make_motif(steps, rest_p):
        out = []
        cur = int(r() * 3) * 2
        for k in range(steps):
            if k > 0 and r() < rest_p:
                out.append(None)
                continue
            if k % 4 == 0 or r() < 0.3:
                cur = [0, 2, 4, 7][int(r() * 4)]
            else:
                cur = max(-1, min(9, cur + [-2, -1, 1, 2][int(r() * 4)]))
            out.append(cur)
        return out
    motif_a = make_motif(16, 0.36 if menu else 0.28)
    motif_b = make_motif(8, 0.2)
    # B 부분 드럼 변화
    kick_b = [0, 3, 8, 10] if r() < 0.5 else [0, 6, 8, 14]
    for bar in range(bars):
        sec = 0 if bar < half else 1
        bb = bar % half
        chord = prog[sec][bb % 4]
        b0 = int(bar * 4 * spb)
        # 화음(패드): 마디 전체를 부드럽게. B 부분은 7음을 살짝 더해서 풍성하게
        pad = pads.get((sec, chord))
        if pad is None:                                  # 같은 화음은 한 번만 합쳐 두고 재사용
            pv = 0.065 if menu else 0.048
            for j, dg in enumerate((0, 2, 4) if sec == 0 else (0, 2, 4, 6)):
                s = note('tri', tone(chord + dg, 1, chord), 4 * spb, pv * (0.6 if j == 3 else 1.0), 0.09, 0.5, 0.75)
                pad = list(s) if pad is None else [a + b for a, b in zip(pad, s)]
            pads[(sec, chord)] = pad
        _add(mix, b0, pad)
        # 베이스 (레이스: 8칸마다 한 옥타브 위로 튀기기)
        pat = bass_pat[sec]
        for k in range(16):
            if pat[k]:
                nb = tone(chord, -1, chord)
                if not menu and k % 8 == 6:
                    nb += 12
                elif sec == 1 and k % 8 == 4:
                    nb = tone(chord + 4, -1, chord)        # B 부분은 5음도 섞어서
                _add(mix, b0 + int(k * s16), note(bass_t, nb, s16 * (1.8 if menu else 1.4), 0.22, 0.004, 0.08, 0.6))
        # 아르페지오 (레이스는 16분, 메뉴는 8분)
        step = 2 if menu else 1
        shp = arp_shape[sec]
        for k in range(0, 16, step):
            dg = chord + [0, 2, 4, 7][shp[(k // step) % 4]]
            _add(mix, b0 + int(k * s16), note(lead_t, tone(dg, 1 + sec, chord), s16 * step * 0.9, 0.04 if menu else 0.045 - 0.008 * sec, 0.003, 0.05, 0.4))
        # 멜로디 + 메아리 (점8분 뒤에 작게 두 번)
        if sec == 0:
            phrase = bb // 2
            first = (bb % 2) * 8
            mot = motif_a[first:first + 8]
            if phrase % 2 == 1:                          # 대답 구절: 2도 위로 + 마지막은 으뜸음으로 맺기
                mot = [None if m is None else m + 2 for m in mot]
                if bb % 2 == 1:
                    mot[-2:] = [0, None]
            unit = 2
        else:
            mot = motif_b[(bb % 2) * 4:(bb % 2) * 4 + 4]
            unit = 4
        if not (sec == 0 and bb == half - 1 and not menu):   # A 부분 마지막 마디는 드럼 필을 위해 비워 둔다
            for k, m in enumerate(mot):
                if m is None:
                    continue
                ln = 1
                while k + ln < len(mot) and mot[k + ln] is None and ln < 3:
                    ln += 1
                n_len = s16 * unit * ln * 0.92
                mv = (0.062 if menu else 0.036) * (1.15 if unit == 4 else 1.0)
                s = note(mel_t, tone(chord + m, 2, chord), n_len, mv, 0.01, 0.12, 0.7)
                o = b0 + int(k * unit * s16)
                _add(mix, o, s)
                _add(mix, o + int(spb * 0.75), s, 0.3)
                _add(mix, o + int(spb * 1.5), s, 0.12)
        # 드럼
        fill = bb % 4 == 3
        if bb == 0 or (not menu and bb == 4):
            _add(mix, b0, crash, 1.0 if bb == 0 else 0.6)
        for k in range(16):
            o = b0 + int(k * s16)
            if menu:
                if k in (0, 10) or (sec == 1 and k == 7):
                    _add(mix, o, kick, 0.85)
                if k in (4, 12):
                    _add(mix, o, snare_soft)
                if k % 4 == 2:
                    _add(mix, o, hat)
                elif sec == 1 and k % 2 == 1:
                    _add(mix, o, hat, 0.45)
            else:
                if sec == 0:
                    if k % 4 == 0 or (fill and k in (14, 15)):
                        _add(mix, o, kick)
                else:
                    if k in kick_b or (fill and k in (14, 15)):
                        _add(mix, o, kick)
                if k in (4, 12) or (fill and k in (13, 14, 15)):
                    _add(mix, o, snare)
                elif fill and k in (10, 11):
                    _add(mix, o, snare, 0.5)
                if sec == 1 and k % 4 == 2:
                    _add(mix, o, ohat)
                elif k % 2 == 1:
                    _add(mix, o, hat)
                elif r() < 0.25:
                    _add(mix, o, hat, 0.7)
    # 정규화 + 부드러운 포화 (작은 소리를 조금 키워서 꽉 찬 느낌)
    peak = max(1e-6, max(mix), -min(mix))
    inv = 1.0 / peak
    c1 = 32767 * 0.9 * 1.5 * inv
    c3 = 32767 * 0.9 * 0.5 * inv * inv * inv
    return array.array('h', [int(x * (c1 - c3 * x * x)) for x in mix])


def music_seed(ref):
    """맵 -> 레이스 곡 번호 (같은 맵은 같은 곡)"""
    if isinstance(ref, dict):
        return cmap_key(ref) % MUSIC_STYLES
    return int(ref) % MUSIC_STYLES
