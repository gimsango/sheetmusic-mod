
# ----------------------------------------------------------------------------
#  설정/프로필 저장 (JSON 파일, 실패해도 게임은 계속 동작)
# ----------------------------------------------------------------------------
def user_data_dir():
    """설치판이 저장할 사용자 폴더 (Windows: %APPDATA%/TurboKart3D, macOS: Application Support, Linux: ~/.local/share)"""
    try:
        if sys.platform.startswith('win'):
            base = os.environ.get('APPDATA') or os.path.expanduser('~')
        elif sys.platform == 'darwin':
            base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
        else:
            base = os.environ.get('XDG_DATA_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'share')
        d = os.path.join(base, 'TurboKart3D')
        if not os.path.isdir(d):
            os.makedirs(d)
        return d
    except Exception:
        return None


def save_dirs():
    """저장 파일을 찾을/쓸 폴더 순서. 스크립트로 실행하면 게임 파일 옆이 먼저,
    설치판(스팀 등으로 묶은 실행 파일)은 프로그램 폴더가 쓰기 금지일 수 있어서 사용자 폴더가 먼저"""
    out = []
    if getattr(sys, 'frozen', False):
        d = user_data_dir()
        if d:
            out.append(d)
    try:
        out.append(os.path.dirname(os.path.abspath(sys.argv[0] if sys.argv and sys.argv[0] else __file__)))
    except Exception:
        pass
    try:
        out.append(os.path.expanduser('~'))
    except Exception:
        pass
    out.append('')
    seen = []
    for d in out:
        if d not in seen:
            seen.append(d)
    return seen


class Profile(dict):
    DEFAULTS = {'name': '', 'kart': None, 'map': 1, 'laps': 3, 'bots': 7, 'quality': 1, 'auto_gas': True, 'sound': True,
                'lang': 'auto', 'last_ip': '', 'port': DEFAULT_PORT, 'steer_mode': 'buttons', 'steer_resp': 1,
                'mode': 'item',           # 'item' = 아이템전, 'speed' = 스피드전, 'time' = 타임 어택(혼자, 기록 도전)
                'map_src': 'builtin',     # 'builtin' = 기본 맵(1~1000), 'custom' = 내가 만든 맵
                'cmap': '',               # 고른 '내 맵' 의 uid
                # 소리 (0~1)
                'vol_master': 1.0, 'vol_sfx': 1.0, 'vol_engine': 0.8, 'vol_music': 0.5, 'music': True,
                # 게임/카메라
                'units': 'kmh', 'shake': True, 'speed_fx': True, 'cam_dist': 1, 'records': {},
                # PC 그래픽/화면 (폰은 'quality' 를 씀)
                'gfx': 'high', 'msaa': 4, 'aniso': 8, 'view': 2, 'props_k': 1.0, 'fx_k': 1.0, 'weather_k': 1.0, 'shadows': True,
                'display': 'window', 'res': '', 'vsync': True, 'fps_cap': 0, 'fov': 82}

    def __init__(self, filename='kart3d_profile.json'):
        dict.__init__(self)
        self.filename = filename
        self.path = None
        self.update(self.DEFAULTS)
        self.load()
        if self['kart'] is None:
            self['kart'] = int(time.time() * 1000) % KART_COUNT
        self['kart'] = int(self['kart']) % KART_COUNT

    def _candidates(self):
        return [os.path.join(d, self.filename) if d else self.filename for d in save_dirs()]

    _BAD = object()

    @classmethod
    def _fix(cls, default, v):
        """저장 파일 값 검사: 기본값과 같은 종류면 (필요하면 고쳐서) 돌려주고, 아니면 _BAD (손으로 고친 파일 대비)"""
        num = isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and abs(v) < 1e9
        if default is None or (isinstance(default, int) and not isinstance(default, bool)):
            if default is None and v is None:
                return None
            return int(v) if num else cls._BAD
        if isinstance(default, float):
            return float(v) if num else cls._BAD
        if isinstance(default, bool):
            return v if isinstance(v, bool) else cls._BAD
        return v if isinstance(v, type(default)) else cls._BAD

    def load(self):
        for p in self._candidates():
            try:
                if os.path.isfile(p):
                    with open(p, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        for k, v in data.items():
                            if k in self.DEFAULTS:
                                v = self._fix(self.DEFAULTS[k], v)
                                if v is not self._BAD:
                                    self[k] = v
                        self.path = p
                        return
            except Exception:
                continue

    def save(self):
        paths = [self.path] if self.path else []
        paths += [p for p in self._candidates() if p not in paths]
        for p in paths:
            try:
                with open(p, 'w', encoding='utf-8') as f:
                    json.dump(dict(self), f, ensure_ascii=False)
                self.path = p
                return True
            except Exception:
                continue
        return False

    def display_name(self):
        n = str(self['name']).strip()
        return n if n else 'Racer%d' % (1 + int(self['kart']) % 99)


# ---- 기록 (맵마다 최고 랩 / 바퀴 수별 최고 완주 시간) ----
def rec_key(ref):
    if isinstance(ref, dict):
        return 'c%08x' % cmap_key(ref)
    return 'm%d' % int(ref)


def rec_get(profile, ref):
    recs = profile.get('records')
    r = recs.get(rec_key(ref)) if isinstance(recs, dict) else None
    return r if isinstance(r, dict) else {}


def rec_submit(profile, ref, laps, lap_times, race_time):
    """레이스 기록 저장. 반환 (새 최고 랩, 새 최고 완주) - 아이템전 기록은 넣지 않는다 (공정하게)"""
    recs = profile.get('records')
    if not isinstance(recs, dict):
        recs = {}
    key = rec_key(ref)
    r = recs.get(key)
    if not isinstance(r, dict):
        r = {}
    new_lap = new_race = False
    good = [t for t in (lap_times or []) if t > 2.0]
    if good:
        bl = min(good)
        if not isinstance(r.get('lap'), (int, float)) or bl < r['lap']:
            r['lap'] = round(bl, 3)
            new_lap = True
    if race_time is not None and race_time > 2.0:
        rk = 'race%d' % int(laps)
        if not isinstance(r.get(rk), (int, float)) or race_time < r[rk]:
            r[rk] = round(race_time, 3)
            new_race = True
    recs.pop(key, None)
    recs[key] = r                          # 최근에 달린 맵을 뒤로 (오래된 것부터 정리되게)
    if len(recs) > 4000:
        for k in list(recs.keys())[:500]:
            del recs[k]
    profile['records'] = recs
    profile.save()
    return new_lap, new_race

