
# ----------------------------------------------------------------------------
#  맵 만들기 : 직접 그린 길 + 장애물/나무/화산 기둥 배치 + 세부 설정  ->  솔로/아이템전/멀티에서 달리기
#  (폰/PC 공통 데이터 형식. 멀티에서는 방장이 맵 데이터를 그대로 보내서 모두 같은 트랙을 만든다)
# ----------------------------------------------------------------------------
CMAP_VER = 1
CMAP_WORLD = 1000.0          # 편집 가능한 땅: x, z 가 -1000 ~ +1000 m
CMAP_MAX_PTS = 400
CMAP_MAX_OBJS = 900
CMAP_MIN_LEN = 260.0         # 이보다 짧은 길은 만들 수 없음 (m)

# 놓을 수 있는 물건: (종류, 한글, 영문, 분류, 충돌 반지름(m, 크기 1), 기본 크기, 줄로 놓을 때 간격(m, 크기 1), 편집기 색)
#   분류: 'obs' 장애물 / 'deco' 장식(나무 등, 길 위에 놓으면 장애물이 됨) / 'road' 도로 기능(발판/상자)
OBJ_ROWS = [
    ('cone', '라바콘', 'Cone', 'obs', 0.42, 1.0, 2.4, (255, 128, 30)),
    ('drum', '드럼통', 'Oil drum', 'obs', 0.62, 1.0, 1.7, (40, 130, 230)),
    ('crate', '나무 상자', 'Crate', 'obs', 0.9, 1.0, 2.0, (196, 146, 82)),
    ('tires', '타이어 더미', 'Tire stack', 'obs', 0.95, 1.0, 2.0, (60, 60, 68)),
    ('block', '방호벽', 'Barrier', 'obs', 1.05, 1.0, 2.2, (228, 228, 232)),
    ('rock', '바위', 'Boulder', 'obs', 3.0, 0.6, 7.0, (138, 138, 148)),
    ('lavapillar', '화산 기둥', 'Lava pillar', 'obs', 1.35, 1.0, 4.5, (255, 92, 24)),
    ('pillar', '돌기둥', 'Stone pillar', 'obs', 1.15, 1.0, 4.0, (226, 220, 204)),
    ('icespike', '얼음 가시', 'Ice spike', 'obs', 1.3, 1.0, 4.0, (168, 222, 255)),
    ('crystal', '크리스탈', 'Crystal', 'obs', 1.2, 1.0, 4.0, (255, 60, 220)),
    ('pine', '소나무', 'Pine', 'deco', 0.75, 1.0, 7.5, (36, 118, 58)),
    ('roundtree', '둥근 나무', 'Round tree', 'deco', 0.8, 1.0, 8.0, (74, 164, 70)),
    ('palm', '야자수', 'Palm', 'deco', 0.6, 1.0, 9.0, (80, 190, 90)),
    ('acacia', '아카시아', 'Acacia', 'deco', 0.7, 1.0, 9.0, (120, 150, 50)),
    ('deadtree', '고목', 'Dead tree', 'deco', 0.6, 1.0, 6.0, (110, 80, 60)),
    ('bamboo', '대나무', 'Bamboo', 'deco', 0.9, 1.0, 3.2, (110, 190, 80)),
    ('cactus', '선인장', 'Cactus', 'deco', 0.9, 1.0, 5.0, (60, 140, 76)),
    ('bush', '덤불', 'Bush', 'deco', 1.4, 1.0, 3.2, (70, 140, 60)),
    ('flowers', '꽃밭', 'Flowers', 'deco', 0.0, 1.0, 4.0, (255, 120, 160)),
    ('mushroom', '버섯', 'Mushroom', 'deco', 2.0, 1.0, 6.0, (220, 60, 60)),
    ('sunflower', '해바라기', 'Sunflower', 'deco', 0.5, 1.0, 3.0, (255, 210, 40)),
    ('lollipop', '막대사탕', 'Lollipop', 'deco', 0.5, 1.0, 4.4, (255, 110, 190)),
    ('volcano', '화산', 'Volcano', 'deco', 13.0, 1.0, 36.0, (190, 60, 24)),
    ('building', '빌딩', 'Building', 'deco', 8.0, 1.0, 26.0, (90, 100, 150)),
    ('windmill', '풍차', 'Windmill', 'deco', 1.6, 1.0, 10.0, (240, 236, 220)),
    ('pyramid', '피라미드', 'Pyramid', 'deco', 6.0, 1.0, 15.0, (226, 196, 120)),
    ('lantern', '등불', 'Lantern', 'deco', 0.3, 1.0, 5.0, (255, 210, 120)),
    ('tombstone', '비석', 'Tombstone', 'deco', 0.6, 1.0, 2.2, (150, 150, 160)),
    ('pad', '부스트 발판', 'Boost pad', 'road', 0.0, 1.0, 12.0, (25, 230, 255)),
    ('jump', '점프대', 'Jump pad', 'road', 0.0, 1.0, 12.0, (255, 225, 60)),
    ('oil', '기름 웅덩이', 'Oil slick', 'road', 0.0, 1.0, 9.0, (40, 30, 60)),
    ('box', '아이템 상자', 'Item boxes', 'road', 0.0, 1.0, 30.0, (255, 170, 40)),
]
OBJ_INFO = {r[0]: dict(kind=r[0], ko=r[1], en=r[2], cat=r[3], rad=r[4], s=r[5], gap=r[6], col=r[7]) for r in OBJ_ROWS}
OBJ_ORDER = [r[0] for r in OBJ_ROWS]
OBJ_BY_CAT = {c: [r[0] for r in OBJ_ROWS if r[3] == c] for c in ('obs', 'deco', 'road')}
CMAP_WEATHERS = ['auto', 'none', 'rain', 'snow', 'leaf', 'petal', 'ember', 'ash', 'firefly', 'sparkle', 'bubble', 'dust', 'spore', 'sprinkle']
CMAP_WEATHER_KO = {'auto': '자동(바이옴)', 'none': '맑음', 'rain': '비', 'snow': '눈', 'leaf': '낙엽', 'petal': '꽃잎', 'ember': '불씨', 'ash': '화산재',
                   'firefly': '반딧불', 'sparkle': '반짝이', 'bubble': '거품', 'dust': '모래 먼지', 'spore': '포자', 'sprinkle': '스프링클'}
CMAP_WEATHER_EN = {'auto': 'Auto', 'none': 'Clear', 'rain': 'Rain', 'snow': 'Snow', 'leaf': 'Leaves', 'petal': 'Petals', 'ember': 'Embers', 'ash': 'Ash',
                   'firefly': 'Fireflies', 'sparkle': 'Sparkles', 'bubble': 'Bubbles', 'dust': 'Dust', 'spore': 'Spores', 'sprinkle': 'Sprinkles'}
CMAP_DECO_KO = ['없음', '조금', '보통', '많이']
CMAP_DECO_EN = ['None', 'Few', 'Normal', 'Lots']
CMAP_DECO_K = [0.0, 0.45, 1.0, 1.7]


def obj_name(kind, lang='ko'):
    o = OBJ_INFO.get(kind)
    if o is None:
        return kind
    return o['ko'] if lang == 'ko' else o['en']


def _fnv(text):
    h = 0x811c9dc5
    for ch in text.encode('utf-8'):
        h = ((h ^ ch) * 0x01000193) & 0xFFFFFFFF
    return h


def _num(v, lo, hi, nd=1, default=0.0):
    try:
        f = float(v)
    except Exception:
        return default
    if f != f or f in (float('inf'), float('-inf')):
        return default
    f = lo if f < lo else (hi if f > hi else f)
    return round(f, nd)


def _clean_name(v, default):
    t = ''.join(ch for ch in str(v if v is not None else '') if ch >= ' ' and ch not in '\x7f').strip()
    return t[:20] if t else default


def cmap_clean(d):
    """불러온/받은 맵 데이터를 안전한 형태로 고친다 (이상한 값은 범위 안으로, 모르는 물건은 버림). 못 쓰면 None"""
    if not isinstance(d, dict):
        return None
    try:
        W = CMAP_WORLD
        pts = []
        for p in list(d.get('pts') or [])[:CMAP_MAX_PTS]:
            if not isinstance(p, (list, tuple)) or len(p) < 2:
                continue
            pts.append([_num(p[0], -W, W), _num(p[1], -W, W), _num(p[2] if len(p) > 2 else 0.0, -40.0, 80.0)])
        if len(pts) < 4:
            return None
        objs = []
        for o in list(d.get('objs') or [])[:CMAP_MAX_OBJS]:
            if not isinstance(o, (list, tuple)) or len(o) < 3:
                continue
            k = str(o[0])
            if k not in OBJ_INFO:
                continue
            objs.append([k, _num(o[1], -W, W), _num(o[2], -W, W), _num(o[3] if len(o) > 3 else 1.0, 0.3, 3.0, 2, 1.0),
                         _num(o[4] if len(o) > 4 else 0.0, -7.0, 7.0, 2)])
        uid = ''.join(ch for ch in str(d.get('uid') or '') if ch.isalnum())[:16]
        weather = str(d.get('weather') or 'auto')
        if weather not in CMAP_WEATHERS:
            weather = 'auto'
        return dict(v=CMAP_VER, uid=uid, name=_clean_name(d.get('name'), 'My map'), pts=pts, objs=objs,
                    look=int(_num(d.get('look', 1), 1, MAP_COUNT, 0, 1)), width=_num(d.get('width', 16), 10.0, 30.0, 1, 16.0),
                    hills=_num(d.get('hills', 0.0), 0.0, 1.0, 2), deco=int(_num(d.get('deco', 2), 0, 3, 0, 2)),
                    pads=1 if d.get('pads', 1) else 0, weather=weather, laps=int(_num(d.get('laps', 3), 1, 10, 0, 3)))
    except Exception:
        return None


def cmap_key(d):
    """맵 내용(이름/uid 제외)으로 만든 고정 숫자 - 자동 장식 배치 등의 씨앗. 어느 기기에서든 같은 값"""
    body = dict(d)
    body.pop('uid', None)
    body.pop('name', None)
    return _fnv(json.dumps(body, sort_keys=True, separators=(',', ':')))


def map_title(ref, lang='ko'):
    """기본 맵 번호 / 만든 맵 데이터 -> 화면 표시용 짧은 이름"""
    if isinstance(ref, dict):
        return u'★ ' + str(ref.get('name', '?'))
    i = map_info(ref)
    return '#%d %s' % (i['id'], i['name'] if lang == 'ko' else i['name_en'])


def cmap_theme(d):
    """맵 데이터의 바이옴(색/하늘/장식물 팔레트) + 날씨 설정 반영"""
    th = biome(d['look'])
    w = d.get('weather', 'auto')
    if w == 'auto':
        return th
    th = dict(th)
    if w == 'none':
        th['weather'] = None
        th['wcol'] = None
        return th
    th['weather'] = w
    base_c = WEATHER[w][0]
    if base_c is not None:
        th['wcol'] = base_c
    elif w == 'leaf':
        th['wcol'] = th['leaf'][0]
    elif w == 'petal':
        th['wcol'] = mix_rgb(th['flower'][0], (255, 255, 255), 0.25)
    elif w == 'sparkle':
        th['wcol'] = mix_rgb(th['crystal'], (255, 255, 255), 0.5)
    elif w == 'dust':
        th['wcol'] = mix_rgb(hex_rgb(th['ground'][0]), (255, 255, 255), 0.35)
    else:
        th['wcol'] = (255, 255, 255)
    return th


def cmap_new(name='My map', look=1):
    """새 맵: 바로 달릴 수 있는 기본 타원 코스"""
    pts = []
    K = 16
    for i in range(K):
        a = TAU * i / K
        pts.append([round(math.cos(a) * 300.0, 1), round(math.sin(a) * 190.0, 1), 0.0])
    return dict(v=CMAP_VER, uid='', name=name, pts=pts, objs=[], look=int(look), width=16.0, hills=0.0, deco=2, pads=1,
                weather='auto', laps=3)


def cmap_from_builtin(mid, name=None):
    """기본 맵 #mid 의 코스 모양을 가져와서 편집할 수 있는 맵으로 (조절점 약 30m 간격)"""
    tr = Track(mid, True)
    step = max(1, int(round(30.0 / tr.ds)))
    pts = []
    for i in range(0, tr.N, step):
        pts.append([round(tr.px[i], 1), round(tr.pz[i], 1), round(tr.py[i], 1)])
    # 가운데로 옮기기
    cx = (tr.bounds[0] + tr.bounds[1]) / 2.0
    cz = (tr.bounds[2] + tr.bounds[3]) / 2.0
    for p in pts:
        p[0] = round(clamp(p[0] - cx, -CMAP_WORLD, CMAP_WORLD), 1)
        p[1] = round(clamp(p[1] - cz, -CMAP_WORLD, CMAP_WORLD), 1)
    i = map_info(mid)
    d = cmap_new(name or i['name'], mid)
    d['pts'] = pts
    d['width'] = float(tr.width)
    return d


def stroke_to_pts(stroke, spacing=26.0):
    """손가락/마우스로 그린 선 -> 닫힌 코스 조절점 (일정 간격으로 다시 찍고 살짝 다듬음). 너무 짧으면 None"""
    pts = []
    for p in stroke:
        x, z = float(p[0]), float(p[1])
        if not pts or (x - pts[-1][0]) ** 2 + (z - pts[-1][1]) ** 2 > 0.25:
            pts.append((x, z))
    if len(pts) < 3:
        return None
    seg = []
    total = 0.0
    for i in range(len(pts) - 1):
        d = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        seg.append(d)
        total += d
    close = math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])
    if total + close < CMAP_MIN_LEN:
        return None
    n = max(5, int(round(total / spacing)))
    out = []
    i = 0
    acc = 0.0
    for k in range(n):
        tgt = total * k / n
        while i < len(seg) - 1 and tgt > acc + seg[i]:
            acc += seg[i]
            i += 1
        f = (tgt - acc) / seg[i] if seg[i] > 1e-9 else 0.0
        f = 0.0 if f < 0 else (1.0 if f > 1 else f)
        a, b = pts[i], pts[i + 1]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    # 끝과 처음 사이가 멀면 중간 점을 채워서 부드럽게 닫기
    if close > spacing * 1.5:
        m = int(close // spacing)
        a, b = out[-1], out[0]
        for k in range(1, m):
            f = k / float(m)
            out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    # 손떨림 다듬기 (이웃 평균 한 번)
    nn = len(out)
    sm = []
    for k in range(nn):
        a, b, c = out[k - 1], out[k], out[(k + 1) % nn]
        sm.append([round(clamp(0.25 * a[0] + 0.5 * b[0] + 0.25 * c[0], -CMAP_WORLD, CMAP_WORLD), 1),
                   round(clamp(0.25 * a[1] + 0.5 * b[1] + 0.25 * c[1], -CMAP_WORLD, CMAP_WORLD), 1), 0.0])
    return sm


def stroke_points_every(stroke, gap):
    """그린 선을 따라 gap(m) 간격으로 물건 놓을 자리 [(x, z, 방향)]"""
    out = []
    if not stroke:
        return out
    px, pz = float(stroke[0][0]), float(stroke[0][1])
    out.append((px, pz, 0.0))
    acc = 0.0
    for p in stroke[1:]:
        x, z = float(p[0]), float(p[1])
        d = math.hypot(x - px, z - pz)
        if d < 1e-6:
            continue
        ang = math.atan2(x - px, z - pz)
        t = gap - acc
        while t <= d:
            out.append((px + (x - px) * t / d, pz + (z - pz) * t / d, ang))
            t += gap
        acc = d - (t - gap)
        px, pz = x, z
    if len(out) > 1:
        out[0] = (out[0][0], out[0][1], out[1][2])
    return out


class MapStore(object):
    """만든 맵 목록 (kart3d_maps.json, 게임 파일 옆 또는 홈 폴더)"""
    FILE = 'kart3d_maps.json'

    def __init__(self, filename=None):
        self.filename = filename or self.FILE
        self.path = None
        self.maps = []
        self.load()

    def _candidates(self):
        out = []
        try:
            out.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0] if sys.argv and sys.argv[0] else __file__)), self.filename))
        except Exception:
            pass
        try:
            out.append(os.path.join(os.path.expanduser('~'), self.filename))
        except Exception:
            pass
        out.append(self.filename)
        return out

    def load(self):
        for p in self._candidates():
            try:
                if os.path.isfile(p):
                    with open(p, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    lst = data.get('maps', []) if isinstance(data, dict) else data
                    maps = []
                    for d in lst if isinstance(lst, list) else []:
                        c = cmap_clean(d)
                        if c is not None:
                            if not c['uid'] or any(m['uid'] == c['uid'] for m in maps):
                                c['uid'] = self.new_uid(maps)
                            maps.append(c)
                    self.maps = maps
                    self.path = p
                    return
            except Exception:
                continue

    def save(self):
        paths = [self.path] if self.path else []
        paths += [p for p in self._candidates() if p not in paths]
        for p in paths:
            try:
                tmp = p + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as f:
                    json.dump({'v': CMAP_VER, 'maps': self.maps}, f, ensure_ascii=False, separators=(',', ':'))
                try:
                    os.replace(tmp, p)
                except Exception:
                    with open(p, 'w', encoding='utf-8') as f:
                        json.dump({'v': CMAP_VER, 'maps': self.maps}, f, ensure_ascii=False, separators=(',', ':'))
                self.path = p
                return True
            except Exception:
                continue
        return False

    def new_uid(self, maps=None):
        maps = self.maps if maps is None else maps
        used = set(m['uid'] for m in maps)
        n = int(time.time() * 1000) & 0xFFFFFFFF
        while True:
            u = 'm%08x' % (hash32(n) & 0xFFFFFFFF)
            if u not in used:
                return u
            n += 1

    def get(self, uid):
        for m in self.maps:
            if m['uid'] == uid:
                return m
        return None

    def index(self, uid):
        for i, m in enumerate(self.maps):
            if m['uid'] == uid:
                return i
        return -1

    def put(self, d):
        """저장 (uid 가 같으면 덮어쓰기). 반환: uid"""
        c = cmap_clean(d)
        if c is None:
            return None
        if not c['uid']:
            c['uid'] = self.new_uid()
        i = self.index(c['uid'])
        if i >= 0:
            self.maps[i] = c
        else:
            self.maps.append(c)
        self.save()
        return c['uid']

    def add_copy(self, d):
        """다른 사람 맵 저장: 같은 내용이 이미 있으면 그것을, 아니면 새 uid 로"""
        c = cmap_clean(d)
        if c is None:
            return None
        k = cmap_key(c)
        for m in self.maps:
            if cmap_key(m) == k:
                return m['uid']
        c['uid'] = self.new_uid()
        self.maps.append(c)
        self.save()
        return c['uid']

    def delete(self, uid):
        i = self.index(uid)
        if i >= 0:
            del self.maps[i]
            self.save()


class MapEdit(object):
    """편집 중인 맵 (도구 동작 + 되돌리기 + 미리보기 트랙). 폰/PC 편집기 화면이 같이 쓴다."""
    HIT = 14.0          # 점/물건을 집는 반경 (m) - 화면 배율에 맞춰 UI 가 바꿔 준다

    def __init__(self, data):
        self.data = cmap_clean(data) or cmap_new()
        self.undo_stack = []
        self.dirty = False            # 저장 안 한 변경
        self._prev = None
        self._prev_key = None
        self.msg = ''

    # ---- 되돌리기 ------------------------------------------------------------------
    def snapshot(self):
        self.undo_stack.append(json.dumps(self.data, separators=(',', ':')))
        if len(self.undo_stack) > 60:
            del self.undo_stack[0]
        self.dirty = True

    def undo(self):
        if not self.undo_stack:
            return False
        self.data = json.loads(self.undo_stack.pop())
        self.dirty = True
        return True

    # ---- 미리보기 트랙 (중심선만) --------------------------------------------------------
    def preview(self):
        key = json.dumps([self.data['pts'], self.data['width'], self.data['hills']], separators=(',', ':'))
        if key != self._prev_key:
            self._prev_key = key
            try:
                self._prev = Track(self.data, True)
            except Exception:
                self._prev = None
        return self._prev

    def warnings(self, lang='ko'):
        out = []
        tr = self.preview()
        if tr is None:
            return [T_(lang, '길을 만들 수 없어요. 다시 그려 보세요', 'Cannot build this road. Try drawing again')]
        if tr.length < CMAP_MIN_LEN:
            out.append(T_(lang, '길이 너무 짧아요', 'Road is too short'))
        sep = min_separation([(tr.px[i], tr.py[i], tr.pz[i]) for i in range(tr.N)], tr.ds)
        if sep < 2 * (tr.hw + tr.SH) + 4.0:
            out.append(T_(lang, '길이 서로 겹치거나 너무 가까워요', 'Parts of the road overlap or are too close'))
        return out

    # ---- 길 -----------------------------------------------------------------------
    def set_stroke(self, stroke):
        pts = stroke_to_pts(stroke)
        if pts is None:
            self.msg = 'short'
            return False
        self.snapshot()
        self.data['pts'] = pts
        return True

    def nearest_point(self, x, z, rad=None):
        rad = self.HIT if rad is None else rad
        best, bd = -1, rad * rad
        for i, p in enumerate(self.data['pts']):
            d = (p[0] - x) ** 2 + (p[1] - z) ** 2
            if d < bd:
                bd, best = d, i
        return best

    def move_point(self, i, x, z, snap=True):
        if snap:
            self.snapshot()
        p = self.data['pts'][i]
        p[0] = round(clamp(x, -CMAP_WORLD, CMAP_WORLD), 1)
        p[1] = round(clamp(z, -CMAP_WORLD, CMAP_WORLD), 1)
        self.dirty = True

    def insert_point(self, x, z):
        """가장 가까운 구간 사이에 조절점 추가"""
        pts = self.data['pts']
        if len(pts) >= CMAP_MAX_PTS:
            return -1
        n = len(pts)
        best, bd = 0, 1e30
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            ex, ez = b[0] - a[0], b[1] - a[1]
            L = ex * ex + ez * ez
            t = clamp(((x - a[0]) * ex + (z - a[1]) * ez) / L, 0.0, 1.0) if L > 1e-9 else 0.0
            d = (a[0] + ex * t - x) ** 2 + (a[1] + ez * t - z) ** 2
            if d < bd:
                bd, best = d, i
        self.snapshot()
        a, b = pts[best], pts[(best + 1) % n]
        h = round((a[2] + b[2]) / 2.0, 1)
        pts.insert(best + 1, [round(clamp(x, -CMAP_WORLD, CMAP_WORLD), 1), round(clamp(z, -CMAP_WORLD, CMAP_WORLD), 1), h])
        return best + 1

    def delete_point(self, i):
        if len(self.data['pts']) <= 4:
            self.msg = 'min'
            return False
        self.snapshot()
        del self.data['pts'][i]
        return True

    def raise_point(self, i, dh):
        self.snapshot()
        p = self.data['pts'][i]
        p[2] = round(clamp(p[2] + dh, -40.0, 80.0), 1)

    def set_start(self, i):
        pts = self.data['pts']
        if 0 < i < len(pts):
            self.snapshot()
            self.data['pts'] = pts[i:] + pts[:i]

    def reverse(self):
        self.snapshot()
        pts = self.data['pts']
        self.data['pts'] = [pts[0]] + pts[1:][::-1]

    def move_all(self, dx, dz):
        self.snapshot()
        W = CMAP_WORLD
        for p in self.data['pts']:
            p[0] = round(clamp(p[0] + dx, -W, W), 1)
            p[1] = round(clamp(p[1] + dz, -W, W), 1)
        for o in self.data['objs']:
            o[1] = round(clamp(o[1] + dx, -W, W), 1)
            o[2] = round(clamp(o[2] + dz, -W, W), 1)

    # ---- 물건 ----------------------------------------------------------------------
    def road_angle(self, x, z):
        """그 자리에서 길이 향하는 방향 (발판/방호벽을 길 방향으로 놓을 때)"""
        tr = self.preview()
        if tr is None:
            return 0.0
        q = Q()
        tr.query(x, z, -1, q)
        return math.atan2(q.tx, q.tz)

    def add_obj(self, kind, x, z, s=None, rot=None, snap=True):
        if kind not in OBJ_INFO or len(self.data['objs']) >= CMAP_MAX_OBJS:
            self.msg = 'full'
            return False
        if snap:
            self.snapshot()
        info = OBJ_INFO[kind]
        if s is None:
            s = info['s']
        if rot is None:
            rot = self.road_angle(x, z) if kind in ('block', 'pad', 'jump', 'oil', 'box', 'crate', 'tires') else (hash32(int(x * 7 + z * 13)) % 628) / 100.0
        W = CMAP_WORLD
        self.data['objs'].append([kind, round(clamp(x, -W, W), 1), round(clamp(z, -W, W), 1), round(clamp(s, 0.3, 3.0), 2), round(wrap_pi(rot), 2)])
        return True

    def add_line(self, kind, stroke, s=None):
        """그린 선을 따라 물건을 줄지어 놓기 (콘/방호벽 줄, 가로수 등)"""
        info = OBJ_INFO.get(kind)
        if info is None or len(stroke) < 2:
            return 0
        s = info['s'] if s is None else s
        spots = stroke_points_every(stroke, max(1.0, info['gap'] * s))
        if not spots:
            return 0
        self.snapshot()
        n = 0
        for (x, z, ang) in spots:
            if len(self.data['objs']) >= CMAP_MAX_OBJS:
                self.msg = 'full'
                break
            rot = ang if kind in ('block', 'crate', 'tires', 'drum') else None
            if kind in ('pad', 'jump', 'oil', 'box'):
                rot = None
            self.add_obj(kind, x, z, s, rot, snap=False)
            n += 1
        return n

    def erase_at(self, x, z, rad=None):
        rad = self.HIT if rad is None else rad
        objs = self.data['objs']
        hit = [i for i, o in enumerate(objs) if (o[1] - x) ** 2 + (o[2] - z) ** 2 < (rad + OBJ_INFO[o[0]]['rad'] * o[3] * 0.5) ** 2]
        if not hit:
            return 0
        self.snapshot()
        for i in reversed(hit):
            del objs[i]
        return len(hit)

    def scale_obj_at(self, x, z, k):
        objs = self.data['objs']
        best, bd = -1, (self.HIT * 1.5) ** 2
        for i, o in enumerate(objs):
            d = (o[1] - x) ** 2 + (o[2] - z) ** 2
            if d < bd:
                bd, best = d, i
        if best < 0:
            return False
        self.snapshot()
        objs[best][3] = round(clamp(objs[best][3] * k, 0.3, 3.0), 2)
        return True

    def clear_objs(self):
        if self.data['objs']:
            self.snapshot()
            self.data['objs'] = []

    # ---- 설정 ----------------------------------------------------------------------
    def set(self, key, value):
        if self.data.get(key) != value:
            self.snapshot()
            self.data[key] = value
            self.data = cmap_clean(self.data) or self.data

    def result(self):
        return cmap_clean(self.data)


def T_(lang, ko, en):
    return ko if lang == 'ko' else en
