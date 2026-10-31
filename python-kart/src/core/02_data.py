
# ----------------------------------------------------------------------------
#  데이터: 맵 테마 10종 x 100 = 1000 맵 / 카트 20 x 20 x 25 x 10 = 100,000
# ----------------------------------------------------------------------------
ADJ = ['고요한', '질주하는', '폭풍의', '황금빛', '아득한', '불꽃', '은빛', '안개 낀', '번개', '전설의', '비밀',
       '끝없는', '반짝이는', '거친', '미지의', '새벽', '한밤', '정오의', '붉은', '푸른', '야생', '얼어붙은', '뜨거운', '꿈꾸는', '마지막']
ADJ_EN = ['Quiet', 'Racing', 'Stormy', 'Golden', 'Distant', 'Blazing', 'Silver', 'Foggy', 'Thunder', 'Legendary', 'Secret',
          'Endless', 'Sparkling', 'Rugged', 'Unknown', 'Dawn', 'Midnight', 'Noon', 'Crimson', 'Azure', 'Wild', 'Frozen', 'Scorching', 'Dreaming', 'Final']

THEMES = [
    dict(key='forest', name='숲', en='Forest',
         nouns=['삼림 서킷', '계곡', '숲길', '피크닉 힐', '오솔길', '호숫가', '캠프 루트', '이끼 협곡'],
         nouns_en=['Woodland Circuit', 'Valley', 'Forest Road', 'Picnic Hill', 'Trail', 'Lakeside', 'Camp Route', 'Mossy Gorge'],
         sky_top=0x2f7fd0, sky_bot=0xcfe6f5, fog=0xbad4e8, fog_d=0.0012, ground=(0x3f7a35, 0x4f8f3f), far=0x3a6b30, road=0x3b3d42,
         wall=(0xdd2e2e, 0xf2f2f2), sun=0xfff1d0, sun_i=2.6, sun_dir=(0.5, 0.8, 0.3), hemi=(0xa8c8ff, 0x4a6b3a, 0.9),
         props=(('pine', 6), ('roundtree', 3), ('bush', 2), ('rock', 1)), weather=None, elev=26, clouds=1.0, rock=(0x7d7f84, 0x6a6c70)),
    dict(key='desert', name='사막', en='Desert',
         nouns=['모래 폭풍길', '오아시스', '피라미드 로드', '선인장 계곡', '대상 루트', '낙타 고개', '신기루 서킷', '황금 사구'],
         nouns_en=['Sandstorm Road', 'Oasis', 'Pyramid Road', 'Cactus Valley', 'Caravan Route', 'Camel Pass', 'Mirage Circuit', 'Golden Dunes'],
         sky_top=0x3d86d6, sky_bot=0xf6e2b8, fog=0xeed9b0, fog_d=0.0014, ground=(0xd9b36b, 0xc99f55), far=0xd2aa62, road=0x4a4743,
         wall=(0xc2552b, 0xf0e2c8), sun=0xffe3b0, sun_i=2.9, sun_dir=(0.4, 0.9, 0.2), hemi=(0xbfd8ff, 0xb08a4a, 0.9),
         props=(('cactus', 5), ('rock', 4), ('bush', 1)), weather=None, elev=20, clouds=0.3, rock=(0xb98c52, 0xa57a44)),
    dict(key='snow', name='설원', en='Snowfield',
         nouns=['빙하 서킷', '스키 슬로프', '오로라 길', '눈보라 고개', '얼음 호수', '설산 루트', '펭귄 마을', '크리스탈 동굴'],
         nouns_en=['Glacier Circuit', 'Ski Slope', 'Aurora Road', 'Blizzard Pass', 'Ice Lake', 'Snow Peak Route', 'Penguin Village', 'Crystal Cave'],
         sky_top=0x7aa6d6, sky_bot=0xe8f1fa, fog=0xdfeaf5, fog_d=0.0022, ground=(0xf2f6fa, 0xdde7f0), far=0xe6eef6, road=0x44484f,
         wall=(0x2a6fd6, 0xf2f2f2), sun=0xe6f0ff, sun_i=2.0, sun_dir=(0.3, 0.6, 0.5), hemi=(0xc8dcff, 0xe8f0ff, 1.0),
         props=(('pine', 7), ('rock', 2)), snowy=True, weather='snow', elev=28, clouds=1.2, rock=(0xdfe6ee, 0xc8d2de)),
    dict(key='neon', name='네온 시티', en='Neon City',
         nouns=['다운타운', '사이버 하이웨이', '루프탑 서킷', '야간 순환로', '네온 스트리트', '메가시티', '홀로그램 거리', '항구 야경'],
         nouns_en=['Downtown', 'Cyber Highway', 'Rooftop Circuit', 'Night Loop', 'Neon Street', 'Megacity', 'Hologram Avenue', 'Harbor Nights'],
         sky_top=0x05061a, sky_bot=0x2a0f4a, fog=0x120a30, fog_d=0.0022, ground=(0x0b0b1c, 0x12122a), far=0x08081a, road=0x15151f,
         wall=(0xff2bd6, 0x19e6ff), glow_wall=True, sun=0x8fa8ff, sun_i=0.7, sun_dir=(-0.4, 0.7, 0.5), hemi=(0x5566cc, 0x20104a, 1.0),
         props=(('building', 8), ('crystal', 1)), night=True, lamps=True, arches=0xff2bd6, weather=None, elev=14, clouds=0.0, rock=(0x303048, 0x202038)),
    dict(key='volcano', name='화산', en='Volcano',
         nouns=['용암 서킷', '화염 협곡', '재의 평원', '마그마 터널', '불의 고개', '분화구 로드', '유황 계곡', '드래곤 둥지'],
         nouns_en=['Lava Circuit', 'Flame Canyon', 'Ash Plains', 'Magma Tunnel', 'Fire Pass', 'Crater Road', 'Sulfur Valley', "Dragon's Nest"],
         sky_top=0x230b0b, sky_bot=0xb3401c, fog=0x4a1a10, fog_d=0.0022, ground=(0x2a2220, 0x3a2a24), far=0x8a2a0c, road=0x2b2a2c,
         wall=(0xff5a1a, 0x222222), glow_wall=True, sun=0xff9a60, sun_i=1.8, sun_dir=(0.5, 0.5, 0.2), hemi=(0xff8050, 0x3a1a10, 0.9),
         props=(('rock', 6), ('crystal', 3)), lava=True, weather='ember', elev=30, clouds=0.0, rock=(0x3a3030, 0x2a2222)),
    dict(key='tropic', name='열대 해변', en='Tropical Beach',
         nouns=['야자수 해안', '산호 만', '서핑 비치', '리조트 로드', '등대 섬', '파라다이스', '해적 항구', '석양 부두'],
         nouns_en=['Palm Coast', 'Coral Bay', 'Surf Beach', 'Resort Road', 'Lighthouse Isle', 'Paradise', 'Pirate Harbor', 'Sunset Pier'],
         sky_top=0x1e90e8, sky_bot=0xbfefff, fog=0xbfe8f0, fog_d=0.0010, ground=(0xe8d49a, 0xf0dca8), far=0x1aa6c4, road=0x3f4147,
         wall=(0x00b7c9, 0xffffff), sun=0xfff4d6, sun_i=3.0, sun_dir=(0.3, 0.85, 0.4), hemi=(0xb8e4ff, 0xe8d49a, 1.0),
         props=(('palm', 7), ('bush', 2), ('rock', 1)), weather=None, elev=12, clouds=1.0, rock=(0xcbb88a, 0xb8a47a)),
    dict(key='autumn', name='단풍', en='Autumn',
         nouns=['단풍길', '낙엽 고개', '수확 농장', '사과 과수원', '안개 마을', '호박 밭', '고성 언덕', '황금 들판'],
         nouns_en=['Maple Road', 'Leaf Pass', 'Harvest Farm', 'Apple Orchard', 'Misty Village', 'Pumpkin Field', 'Castle Hill', 'Golden Meadow'],
         sky_top=0x5b8fcf, sky_bot=0xf5d9b0, fog=0xe8cfa8, fog_d=0.0015, ground=(0x8a6a2f, 0x9b5d22), far=0x7a5a28, road=0x3d3a3a,
         wall=(0xb5451b, 0xf0e0c0), sun=0xffd9a0, sun_i=2.4, sun_dir=(0.6, 0.55, 0.2), hemi=(0xffe0b0, 0x7a4a20, 0.9),
         props=(('roundtree', 8), ('pine', 1), ('rock', 1)), autumn=True, weather='leaf', elev=24, clouds=1.0, rock=(0x8a7a68, 0x75675a)),
    dict(key='candy', name='캔디 월드', en='Candy World',
         nouns=['사탕 왕국', '초코 강', '젤리 언덕', '마시멜로 길', '쿠키 서킷', '아이스크림 산', '솜사탕 하늘', '마카롱 파크'],
         nouns_en=['Candy Kingdom', 'Chocolate River', 'Jelly Hills', 'Marshmallow Road', 'Cookie Circuit', 'Ice Cream Mountain', 'Cotton Candy Sky', 'Macaron Park'],
         sky_top=0xff9bd8, sky_bot=0xfff0fa, fog=0xffd7f0, fog_d=0.0016, ground=(0xffc2e6, 0xbdf0ff), far=0xffb3dd, road=0x5b4b7a,
         wall=(0xff5fa8, 0xffffff), sun=0xfff0ff, sun_i=2.6, sun_dir=(0.4, 0.8, 0.3), hemi=(0xffe0ff, 0xbde0ff, 1.1),
         props=(('lollipop', 7), ('icecream', 3)), arches=0xff5fa8, weather='sprinkle', elev=18, clouds=1.5, rock=(0xe8a8d0, 0xd090b8)),
    dict(key='space', name='우주 기지', en='Space Base',
         nouns=['달 기지', '궤도 링', '운석 지대', '화성 기지', '은하 서킷', '위성 항로', '성운 고속도', '블랙홀 가장자리'],
         nouns_en=['Moon Base', 'Orbital Ring', 'Asteroid Field', 'Mars Outpost', 'Galaxy Circuit', 'Satellite Lane', 'Nebula Highway', 'Black Hole Rim'],
         sky_top=0x000008, sky_bot=0x0a0a22, fog=0x05050f, fog_d=0.0009, ground=(0x8c8c94, 0x777780), far=0x55555c, road=0x2d2f36,
         wall=(0x19e6ff, 0xffffff), glow_wall=True, sun=0xffffff, sun_i=3.0, sun_dir=(-0.6, 0.35, 0.4), hemi=(0x223355, 0x111118, 0.7),
         props=(('rock', 5), ('crystal', 3)), night=True, planet=True, arches=0x19e6ff, weather=None, elev=30, clouds=0.0, rock=(0x8a8a92, 0x6a6a72)),
    dict(key='canyon', name='석양 협곡', en='Sunset Canyon',
         nouns=['레드락 서킷', '메사 고원', '그랜드 캐년', '카우보이 길', '붉은 아치', '독수리 절벽', '황야 질주', '노을 루트'],
         nouns_en=['Red Rock Circuit', 'Mesa Plateau', 'Grand Canyon', 'Cowboy Trail', 'Red Arch', 'Eagle Cliffs', 'Wasteland Dash', 'Sundown Route'],
         sky_top=0x2b3a7a, sky_bot=0xff9a4a, fog=0xe0875a, fog_d=0.0016, ground=(0xb8532f, 0xa04426), far=0x8a3a20, road=0x3a3433,
         wall=(0xf0c040, 0x333333), sun=0xff8a3a, sun_i=2.6, sun_dir=(0.8, 0.28, 0.2), hemi=(0xffb080, 0x8a3a20, 0.9),
         props=(('mesa', 6), ('cactus', 2), ('rock', 2)), weather=None, elev=34, clouds=0.5, rock=(0xb04a28, 0x9a3f20)),
]


def map_info(map_id):
    mid = int(min(MAP_COUNT, max(1, int(map_id))))
    n = mid - 1
    ti = n % 10
    variant = n // 10
    seed = hash32(n * 7919 + 13)
    th = THEMES[ti]
    r = Rng(seed ^ 0x9e3779b9)
    a = int(r() * len(ADJ))
    b = int(r() * len(th['nouns']))
    return dict(id=mid, seed=seed, theme=ti, variant=variant,
                name=ADJ[a] + ' ' + th['nouns'][b], name_en=ADJ_EN[a] + ' ' + th['nouns_en'][b],
                theme_name=th['name'], theme_en=th['en'])


# ----------------------------------------------------------------------------
#  카트 파츠
# ----------------------------------------------------------------------------
# (한글, 영문, 길이, 폭, 높이, 노즈 길이, 캐노피(0없음/1버블/2루프), 속도, 가속, 핸들링, 드리프트)
_BODY_ROWS = [
    ('스트리트 래퍼', 'Street Wrapper', 2.6, 1.5, 0.5, 0.6, 1, 6, 5, 6, 5), ('불독', 'Bulldog', 2.4, 1.8, 0.62, 0.3, 2, 5, 6, 5, 7),
    ('니들', 'Needle', 3.2, 1.3, 0.42, 1.2, 1, 8, 4, 4, 5), ('버블 팝', 'Bubble Pop', 2.2, 1.7, 0.7, 0.2, 1, 4, 7, 8, 6),
    ('웨지', 'Wedge', 3.0, 1.6, 0.4, 1.0, 0, 7, 5, 5, 6), ('탱크 미니', 'Tank Mini', 2.5, 2.0, 0.75, 0.2, 2, 4, 6, 4, 8),
    ('레이저', 'Laser', 3.1, 1.4, 0.44, 1.1, 1, 9, 3, 4, 4), ('머슬', 'Muscle', 2.9, 1.8, 0.58, 0.7, 2, 7, 6, 3, 6),
    ('스카우트', 'Scout', 2.4, 1.4, 0.55, 0.5, 0, 5, 7, 7, 6), ('포뮬러 제로', 'Formula Zero', 3.3, 1.5, 0.36, 1.4, 0, 8, 5, 6, 3),
    ('클래식 롱', 'Classic Long', 3.1, 1.5, 0.6, 0.9, 1, 6, 5, 5, 6), ('점프 큐브', 'Jump Cube', 2.0, 1.7, 0.8, 0.1, 2, 4, 8, 7, 7),
    ('스톰', 'Storm', 2.8, 1.7, 0.5, 0.8, 1, 7, 6, 5, 5), ('돌핀', 'Dolphin', 2.7, 1.5, 0.48, 0.9, 1, 6, 6, 7, 5),
    ('헤비 듀티', 'Heavy Duty', 2.8, 2.0, 0.7, 0.4, 2, 5, 4, 5, 8), ('고스트', 'Ghost', 3.0, 1.45, 0.4, 1.0, 1, 8, 5, 5, 5),
    ('핫로드', 'Hot Rod', 2.9, 1.6, 0.55, 1.0, 0, 7, 7, 4, 6), ('펄스', 'Pulse', 2.5, 1.55, 0.5, 0.6, 1, 6, 6, 6, 6),
    ('타이탄', 'Titan', 3.0, 1.9, 0.66, 0.6, 2, 8, 3, 3, 8), ('콤팩트 X', 'Compact X', 2.1, 1.4, 0.55, 0.3, 1, 5, 8, 8, 5),
]
BODIES = [dict(name=a[0], en=a[1], len=a[2], wid=a[3], hei=a[4], nose=a[5], canopy=a[6], spd=a[7], acc=a[8], han=a[9], dft=a[10]) for a in _BODY_ROWS]

# (한글, 영문, 메인색, 보조색, 금속질감, 패턴 0단색/1스트라이프/2투톤)
_PAINT_ROWS = [
    ('레이싱 레드', 'Racing Red', 0xd8232a, 0xffffff, 0.3, 1), ('코발트 블루', 'Cobalt Blue', 0x1f5fd6, 0xffd23a, 0.4, 1),
    ('라임 그린', 'Lime Green', 0x58c418, 0x111111, 0.2, 2), ('선셋 오렌지', 'Sunset Orange', 0xff7a1a, 0x1b1b1b, 0.3, 1),
    ('로열 퍼플', 'Royal Purple', 0x7a3cd6, 0xff6adf, 0.5, 2), ('핑크 팝', 'Pink Pop', 0xff5fa8, 0xffffff, 0.2, 0),
    ('미드나잇 블랙', 'Midnight Black', 0x15161c, 0xff2a2a, 0.8, 1), ('펄 화이트', 'Pearl White', 0xf2f4f8, 0x2a6fd6, 0.5, 1),
    ('골드', 'Gold', 0xe0b020, 0x222222, 1.0, 0), ('크롬 실버', 'Chrome Silver', 0xc4cad4, 0x2a2f3a, 1.0, 2),
    ('터콰이즈', 'Turquoise', 0x10b8b0, 0xffffff, 0.5, 2), ('버건디', 'Burgundy', 0x7a1230, 0xf0c060, 0.6, 1),
    ('옐로 택시', 'Taxi Yellow', 0xffd400, 0x111111, 0.2, 2), ('아이스 블루', 'Ice Blue', 0x7ad4ff, 0xffffff, 0.6, 1),
    ('포레스트', 'Forest', 0x1f6b35, 0xe8d8a0, 0.2, 2), ('네온 마젠타', 'Neon Magenta', 0xff1fd0, 0x19e6ff, 0.4, 1),
    ('건메탈', 'Gunmetal', 0x4a5160, 0xff7a1a, 0.9, 1), ('민트', 'Mint', 0x7af0c0, 0x1b1b1b, 0.3, 0),
    ('코랄', 'Coral', 0xff6b5a, 0xfff2d0, 0.3, 2), ('사이버 옐로', 'Cyber Yellow', 0xd6ff1a, 0x7a1fff, 0.5, 1),
]
PAINTS = [dict(name=a[0], en=a[1], main=hex_rgb(a[2]), accent=hex_rgb(a[3]), metal=a[4], pattern=a[5]) for a in _PAINT_ROWS]

WHEEL_R = [0.34, 0.38, 0.42, 0.46, 0.50]
WHEEL_W = [0.30, 0.36, 0.42, 0.48, 0.54]
WHEEL_SIZE_KO = ['소', '중소', '중', '중대', '대']
WHEEL_SIZE_EN = ['S', 'M-', 'M', 'M+', 'L']
RIM_KO = ['캡', '5스포크', '메쉬', '골드 링', '네온 링']
RIM_EN = ['Cap', '5-Spoke', 'Mesh', 'Gold Ring', 'Neon Ring']

# (한글, 영문, 속도, 가속, 핸들링)
_WING_ROWS = [('없음', 'None', 0, 1, 0), ('립 스포일러', 'Lip Spoiler', 0, 0, 1), ('하이 윙', 'High Wing', 1, -1, 0), ('트윈 플레인', 'Twin Plane', 1, -1, 1),
              ('사이드 핀', 'Side Fins', 0, 1, 0), ('GT 윙', 'GT Wing', 1, 0, 1), ('덕테일', 'Ducktail', 0, 0, 0), ('루프 스쿠프', 'Roof Scoop', 1, 0, -1),
              ('제트 부스터', 'Jet Booster', 2, -1, -1), ('로켓 팩', 'Rocket Pack', 2, -2, 0)]
WINGS = [dict(name=a[0], en=a[1], spd=a[2], acc=a[3], han=a[4]) for a in _WING_ROWS]


def decode_kart(kid):
    kid = int(kid) % KART_COUNT
    return dict(id=kid, body=kid % 20, paint=(kid // 20) % 20, wheel=(kid // 400) % 25, wing=(kid // 10000) % 10)


def encode_kart(k):
    return k['body'] + 20 * k['paint'] + 400 * k['wheel'] + 10000 * k['wing']


def kart_name(kid, lang='ko'):
    k = decode_kart(kid)
    if lang == 'ko':
        return PAINTS[k['paint']]['name'] + ' ' + BODIES[k['body']]['name']
    return PAINTS[k['paint']]['en'] + ' ' + BODIES[k['body']]['en']


def wheel_name(wheel, lang='ko'):
    size, rim = wheel % 5, wheel // 5
    if lang == 'ko':
        return WHEEL_SIZE_KO[size] + '형 ' + RIM_KO[rim]
    return WHEEL_SIZE_EN[size] + ' ' + RIM_EN[rim]


def kart_stats(kid):
    k = decode_kart(kid)
    b = BODIES[k['body']]
    w = WINGS[k['wing']]
    size, rim = k['wheel'] % 5, k['wheel'] // 5

    def c(v):
        return max(1.0, min(10.0, v))
    speed = c(b['spd'] + w['spd'] + (size - 2) * 0.5 + (0.3 if rim == 3 else 0))
    accel = c(b['acc'] + w['acc'] - (size - 2) * 0.5)
    handling = c(b['han'] + w['han'] - (size - 2) * 0.2 + (0.4 if rim == 2 else 0))
    drift = c(b['dft'] + (0.8 if rim == 4 else 0) + (0.4 if size >= 3 else 0) - (0.2 if rim == 1 else 0))
    return dict(speed=speed, accel=accel, handling=handling, drift=drift,
                max_speed=52 + speed * 3.0, accel_rate=15 + accel * 1.7, turn_rate=1.5 + handling * 0.11, drift_grip=4.2 - drift * 0.18)
