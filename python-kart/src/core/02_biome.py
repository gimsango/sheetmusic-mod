
# ----------------------------------------------------------------------------
#  바이옴 1000종 : 생태계 40가지 x 시간대 5가지 x 색감 5가지  ->  맵 번호(1~1000)마다 서로 다른 바이옴
#  (같은 맵 번호는 어느 기기에서든 같은 바이옴 -> 멀티플레이 OK)
# ----------------------------------------------------------------------------
BIOME_FAMILIES = 40
BIOME_COUNT = 1000

# 시간대: 하늘색(위/지평선), 해/달 색과 세기·고도, 장면 밝기, 색조, 밤 여부 ...
TIMES = {
    'dawn': dict(ko='새벽녘', en='Dawn', top=0x2b3a7a, bot=0xf3a6a0, sun=0xffc8a0, si=1.7, el=0.12, amb=0.86, tint=0xff9a8a, tk=0.10),
    'morning': dict(ko='아침', en='Morning', top=0x3f8ee0, bot=0xd6ecfb, sun=0xfff1d8, si=2.5, el=0.45, amb=1.0, tint=0xfff4e0, tk=0.04),
    'noon': dict(ko='한낮', en='Noon', top=0x2878d8, bot=0xcde6f8, sun=0xffffff, si=2.9, el=0.9, amb=1.05),
    'golden': dict(ko='황금빛 오후', en='Golden Hour', top=0x5b8fcf, bot=0xf8d9a0, sun=0xffd590, si=2.5, el=0.3, amb=1.0, tint=0xffc070, tk=0.10),
    'sunset': dict(ko='노을', en='Sunset', top=0x2b3a7a, bot=0xff9a4a, sun=0xff8a3a, si=2.2, el=0.08, amb=0.88, tint=0xff7a3a, tk=0.16),
    'dusk': dict(ko='황혼', en='Dusk', top=0x1c1f4a, bot=0xb05a8a, sun=0xff9ac0, si=1.3, el=0.05, amb=0.72, tint=0x8a4a9a, tk=0.18),
    'night': dict(ko='달밤', en='Moonlit Night', top=0x05061a, bot=0x1a2350, sun=0xbfd0ff, si=0.9, el=0.55, amb=0.52, tint=0x2a3a7a, tk=0.25, night=True, clouds=0.5),
    'aurora': dict(ko='오로라', en='Aurora Night', top=0x020814, bot=0x0f3a4a, sun=0xa0ffd8, si=0.9, el=0.5, amb=0.5, tint=0x1a6a5a, tk=0.25, night=True, aurora=True, clouds=0.3),
    'overcast': dict(ko='흐린 날', en='Overcast', top=0x7d8a99, bot=0xc9d1d9, sun=0xe8eef5, si=1.7, el=0.6, amb=0.9, tint=0x9aa4b0, tk=0.12, clouds=2.0),
    'storm': dict(ko='폭풍우', en='Storm', top=0x2a2f3a, bot=0x6b7280, sun=0xc8d0e0, si=1.2, el=0.5, amb=0.72, tint=0x4a5260, tk=0.2, clouds=2.4, weather='rain', fogk=1.4),
    'mist': dict(ko='안개', en='Mist', top=0x9aa8b5, bot=0xdfe6ea, sun=0xf0f0f0, si=1.8, el=0.5, amb=0.95, tint=0xc8d0d8, tk=0.12, fogk=2.3),
    'void': dict(ko='심우주', en='Deep Space', top=0x000004, bot=0x05050f, sun=0xffffff, si=3.0, el=0.35, amb=1.0, night=True),
    'nebula_v': dict(ko='보라 성운', en='Violet Nebula', top=0x0a0420, bot=0x3a1a5a, sun=0xe0c8ff, si=2.6, el=0.4, amb=1.0, tint=0x6a3a9a, tk=0.1, night=True),
    'nebula_b': dict(ko='푸른 성운', en='Blue Nebula', top=0x020818, bot=0x0a3a6a, sun=0xc8e8ff, si=2.6, el=0.3, amb=1.0, tint=0x2a5a9a, tk=0.1, night=True),
    'nebula_r': dict(ko='붉은 성운', en='Red Nebula', top=0x14020a, bot=0x5a1a2a, sun=0xffc8b0, si=2.6, el=0.45, amb=1.0, tint=0x9a3a3a, tk=0.1, night=True),
    'nebula_g': dict(ko='초록 성운', en='Green Nebula', top=0x02100a, bot=0x0a4a3a, sun=0xd0ffe0, si=2.6, el=0.25, amb=1.0, tint=0x2a8a5a, tk=0.1, night=True),
    'shallow': dict(ko='얕은 바다', en='Shallows', top=0x1aa0c8, bot=0x8ae0f0, sun=0xe8ffff, si=2.4, el=0.8, amb=0.95, tint=0x40c0d0, tk=0.15, fogk=1.6),
    'deep': dict(ko='깊은 바다', en='Deep Sea', top=0x02183a, bot=0x0a4a7a, sun=0x8ad0ff, si=1.4, el=0.7, amb=0.62, tint=0x1a5a9a, tk=0.25, fogk=2.0),
    'twilight_sea': dict(ko='해질녘 바다', en='Twilight Sea', top=0x1a2a6a, bot=0x3a8aa0, sun=0xffc8a0, si=1.6, el=0.3, amb=0.75, tint=0x3a6aa0, tk=0.2, fogk=1.8),
    'biolum': dict(ko='발광 심해', en='Glowing Abyss', top=0x000814, bot=0x04303a, sun=0x60ffe0, si=1.0, el=0.6, amb=0.52, tint=0x0a5a6a, tk=0.25, night=True, fogk=1.8),
    'sunbeam': dict(ko='햇살 드는 바다', en='Sunbeam Waters', top=0x2ab0d8, bot=0xc0f0f8, sun=0xffffff, si=2.8, el=0.85, amb=1.0, fogk=1.4),
    'glow': dict(ko='빛나는 밤', en='Glowing Night', top=0x04020e, bot=0x1a0a3a, sun=0xc0a0ff, si=1.0, el=0.5, amb=0.55, tint=0x3a1a6a, tk=0.22, night=True),
}

# 색감: (한글, 영문, 목표 색상각(도) 또는 None, 이동량, 채도 배율, 명도 배율)
MODS = {
    'base': ('', '', None, 0.0, 1.0, 1.0),
    'golden': ('황금빛', 'Golden', 45, 0.45, 1.1, 1.05),
    'crimson': ('붉은', 'Crimson', 0, 0.45, 1.15, 0.95),
    'azure': ('푸른', 'Azure', 205, 0.5, 1.05, 1.0),
    'violet': ('보랏빛', 'Violet', 275, 0.5, 1.05, 1.0),
    'emerald': ('에메랄드', 'Emerald', 150, 0.45, 1.1, 1.0),
    'frost': ('서리 내린', 'Frosted', 205, 0.15, 0.45, 1.22),
    'shadow': ('어둠의', 'Shadow', None, 0.0, 0.85, 0.62),
    'pastel': ('파스텔', 'Pastel', None, 0.0, 0.55, 1.2),
    'ashen': ('잿빛', 'Ashen', None, 0.0, 0.25, 0.9),
    'vivid': ('선명한', 'Vivid', None, 0.0, 1.4, 1.05),
    'rose': ('장밋빛', 'Rose', 335, 0.45, 1.05, 1.05),
    'amber': ('호박색', 'Amber', 30, 0.4, 1.2, 1.0),
    'jade': ('비취빛', 'Jade', 160, 0.35, 0.9, 1.05),
    'silver': ('은빛', 'Silver', 210, 0.2, 0.3, 1.15),
}

_G = (0x2f7f35, 0x3a8c3a, 0x4aa04a, 0x5aaa50)          # 기본 초록 잎
_DEF = dict(road=0x3b3d42, wall=(0xdd2e2e, 0xf2f2f2), kerb=(0xd8232a, 0xf0f0f0), leaf=_G, trunk=0x5a3b22, rock=(0x7d7f84, 0x6a6c70),
            flower=(0xffe040, 0xff6080, 0xffffff, 0xb07bff), crystal=0xff2bd6, accent=(0xff2bd6, 0x19e6ff, 0xffe14a, 0x78ff96),
            mesa=(0xb04a28, 0xc7653a, 0xa84424, 0xe0a060), cactus=0x3b8a4a, water=0x1ea8c4, planet=0x3a6fd0, elev=20, clouds=1.0,
            fog_d=0.0014, weather=(None,), light=1.0)

FAMILIES = [
    dict(key='forest', ko='숲', en='Forest', nouns=['삼림 서킷', '계곡', '숲길', '피크닉 힐', '오솔길', '호숫가'],
         nouns_en=['Woodland Circuit', 'Valley', 'Forest Road', 'Picnic Hill', 'Trail', 'Lakeside'],
         ground=(0x3f7a35, 0x4f8f3f), mtn=0x6e8cab, props=(('pine', 6), ('roundtree', 3), ('bush', 2), ('rock', 1)),
         style='mountains', elev=26, fog_d=0.0012, weather=(None, None, 'leaf', 'firefly'),
         times=('morning', 'noon', 'golden', 'sunset', 'night'), mods=('base', 'emerald', 'golden', 'frost', 'shadow')),
    dict(key='desert', ko='사막', en='Desert', nouns=['모래 폭풍길', '오아시스', '선인장 계곡', '대상 루트', '신기루 서킷', '황금 사구'],
         nouns_en=['Sandstorm Road', 'Oasis', 'Cactus Valley', 'Caravan Route', 'Mirage Circuit', 'Golden Dunes'],
         ground=(0xd9b36b, 0xc99f55), road=0x4a4743, wall=(0xc2552b, 0xf0e2c8), leaf=(0x3b8a4a, 0x4a9a52, 0x6a8a3a, 0x8a9a4a),
         trunk=0x7a5a32, rock=(0xb98c52, 0xa57a44), mtn=0xc8a064, props=(('cactus', 5), ('rock', 4), ('bush', 1), ('deadtree', 1)),
         style='dunes', elev=20, clouds=0.3, weather=(None, None, 'dust'),
         times=('dawn', 'noon', 'golden', 'sunset', 'night'), mods=('base', 'crimson', 'pastel', 'rose', 'ashen')),
    dict(key='snow', ko='설원', en='Snowfield', nouns=['빙하 서킷', '스키 슬로프', '눈보라 고개', '얼음 호수', '설산 루트', '펭귄 마을'],
         nouns_en=['Glacier Circuit', 'Ski Slope', 'Blizzard Pass', 'Ice Lake', 'Snow Peak Route', 'Penguin Village'],
         ground=(0xf2f6fa, 0xdde7f0), road=0x44484f, wall=(0x2a6fd6, 0xf2f2f2), kerb=(0x2a6fd6, 0xf2f2f2),
         leaf=(0x4f7f66, 0x6d9a84, 0x5a8a70, 0x7aa890), rock=(0xdfe6ee, 0xc8d2de), mtn=0xa8c0dc,
         props=(('pine', 7), ('rock', 2), ('icespike', 1)), style='snowpeaks', elev=28, clouds=1.2, fog_d=0.0022, snowy=True,
         weather=('snow', 'snow', None), times=('morning', 'noon', 'sunset', 'night', 'aurora'), mods=('base', 'azure', 'silver', 'violet', 'rose')),
    dict(key='neon', ko='네온 시티', en='Neon City', nouns=['다운타운', '사이버 하이웨이', '루프탑 서킷', '야간 순환로', '홀로그램 거리', '항구 야경'],
         nouns_en=['Downtown', 'Cyber Highway', 'Rooftop Circuit', 'Night Loop', 'Hologram Avenue', 'Harbor Nights'],
         ground=(0x0b0b1c, 0x12122a), road=0x15151f, wall=(0xff2bd6, 0x19e6ff), rock=(0x303048, 0x202038), crystal=0xff2bd6,
         props=(('building', 8), ('crystal', 1)), style='city', elev=14, clouds=0.0, fog_d=0.0022, night=True, lamps=True, glow=True, arches=True,
         weather=(None, 'rain', None), times=('dusk', 'night', 'storm', 'aurora', 'dawn'), mods=('base', 'azure', 'violet', 'emerald', 'golden')),
    dict(key='volcano', ko='화산', en='Volcano', nouns=['용암 서킷', '화염 협곡', '재의 평원', '마그마 터널', '분화구 로드', '드래곤 둥지'],
         nouns_en=['Lava Circuit', 'Flame Canyon', 'Ash Plains', 'Magma Tunnel', 'Crater Road', "Dragon's Nest"],
         ground=(0x2a2220, 0x3a2a24), road=0x2b2a2c, wall=(0xff5a1a, 0x222222), leaf=(0x4a3a30, 0x5a4434, 0x3a2e28, 0x6a5040),
         trunk=0x2a201c, rock=(0x3a3030, 0x2a2222), crystal=0xff7a1a, mtn=0x3a2018, props=(('rock', 6), ('crystal', 3), ('deadtree', 2)),
         style='volcano', elev=30, clouds=0.0, fog_d=0.0022, glow=True, sky=(0xb3401c, 0.55), weather=('ember', 'ember', 'ash'),
         times=('dusk', 'night', 'sunset', 'storm', 'noon'), mods=('base', 'crimson', 'amber', 'violet', 'ashen')),
    dict(key='tropic', ko='열대 해변', en='Tropical Beach', nouns=['야자수 해안', '산호 만', '서핑 비치', '리조트 로드', '등대 섬', '해적 항구'],
         nouns_en=['Palm Coast', 'Coral Bay', 'Surf Beach', 'Resort Road', 'Lighthouse Isle', 'Pirate Harbor'],
         ground=(0xe8d49a, 0xf0dca8), road=0x3f4147, wall=(0x00b7c9, 0xffffff), leaf=(0x2f8f3a, 0x3aa046, 0x288040, 0x46af50),
         trunk=0x8a6a40, rock=(0xcbb88a, 0xb8a47a), mtn=0x46a064, props=(('palm', 7), ('bush', 2), ('rock', 1)),
         style='sea', elev=12, fog_d=0.0010, weather=(None, None, 'rain'),
         times=('morning', 'noon', 'golden', 'sunset', 'night'), mods=('base', 'emerald', 'golden', 'rose', 'vivid')),
    dict(key='autumn', ko='단풍', en='Autumn', nouns=['단풍길', '낙엽 고개', '수확 농장', '사과 과수원', '안개 마을', '고성 언덕'],
         nouns_en=['Maple Road', 'Leaf Pass', 'Harvest Farm', 'Apple Orchard', 'Misty Village', 'Castle Hill'],
         ground=(0x8a6a2f, 0x9b5d22), road=0x3d3a3a, wall=(0xb5451b, 0xf0e0c0), leaf=(0xd9541e, 0xe8a317, 0xb83a1a, 0xf0c030),
         rock=(0x8a7a68, 0x75675a), mtn=0xb4966e, props=(('roundtree', 8), ('pine', 1), ('rock', 1), ('pumpkin', 1), ('haystack', 1)),
         style='hills', elev=24, fog_d=0.0015, weather=('leaf', 'leaf', None),
         times=('morning', 'golden', 'sunset', 'dusk', 'mist'), mods=('base', 'crimson', 'golden', 'amber', 'rose')),
    dict(key='candy', ko='캔디 월드', en='Candy World', nouns=['사탕 왕국', '초코 강', '젤리 언덕', '마시멜로 길', '쿠키 서킷', '솜사탕 하늘'],
         nouns_en=['Candy Kingdom', 'Chocolate River', 'Jelly Hills', 'Marshmallow Road', 'Cookie Circuit', 'Cotton Candy Sky'],
         ground=(0xffc2e6, 0xbdf0ff), road=0x5b4b7a, wall=(0xff5fa8, 0xffffff), leaf=(0xff8ac8, 0x8ad8ff, 0xffd870, 0xb08aff),
         accent=(0xff5a8c, 0x5ac8ff, 0xffc83c, 0xa06eff, 0x6ee696, 0xff8c3c), rock=(0xe8a8d0, 0xd090b8), mtn=0xffb4dc,
         props=(('lollipop', 7), ('icecream', 3)), style='candy', elev=18, clouds=1.5, fog_d=0.0016, arches=True, sky=(0xff9bd8, 0.5),
         weather=('sprinkle', 'sprinkle', None), times=('morning', 'noon', 'golden', 'sunset', 'night'), mods=('base', 'azure', 'violet', 'emerald', 'golden')),
    dict(key='space', ko='우주 기지', en='Space Base', nouns=['궤도 링', '운석 지대', '은하 서킷', '위성 항로', '성운 고속도', '블랙홀 가장자리'],
         nouns_en=['Orbital Ring', 'Asteroid Field', 'Galaxy Circuit', 'Satellite Lane', 'Nebula Highway', 'Black Hole Rim'],
         ground=(0x8c8c94, 0x777780), road=0x2d2f36, wall=(0x19e6ff, 0xffffff), rock=(0x8a8a92, 0x6a6a72), crystal=0x19e6ff, planet=0x3a6fd0,
         props=(('rock', 5), ('crystal', 3), ('dish', 2)), style='planet', elev=30, clouds=0.0, fog_d=0.0009, night=True, glow=True, lamps=True,
         weather=(None, 'sparkle'), times=('void', 'nebula_v', 'nebula_b', 'nebula_r', 'nebula_g'), mods=('base', 'azure', 'violet', 'crimson', 'silver')),
    dict(key='canyon', ko='석양 협곡', en='Sunset Canyon', nouns=['레드락 서킷', '메사 고원', '그랜드 캐년', '카우보이 길', '독수리 절벽', '황야 질주'],
         nouns_en=['Red Rock Circuit', 'Mesa Plateau', 'Grand Canyon', 'Cowboy Trail', 'Eagle Cliffs', 'Wasteland Dash'],
         ground=(0xb8532f, 0xa04426), road=0x3a3433, wall=(0xf0c040, 0x333333), rock=(0xb04a28, 0x9a3f20),
         props=(('mesa', 6), ('cactus', 2), ('rock', 2)), style='mesas', elev=34, clouds=0.5, fog_d=0.0016, weather=(None, 'dust', None),
         times=('golden', 'sunset', 'dusk', 'noon', 'night'), mods=('base', 'crimson', 'amber', 'rose', 'violet')),
    dict(key='jungle', ko='정글', en='Jungle', nouns=['밀림 루트', '폭포 계곡', '덩굴길', '앵무새 숲', '원시림 서킷', '강변 습지'],
         nouns_en=['Jungle Route', 'Waterfall Valley', 'Vine Trail', 'Parrot Woods', 'Primeval Circuit', 'Riverbank'],
         ground=(0x2f6a2a, 0x3a7a30), road=0x3a3a34, wall=(0xe0a020, 0x2a5a2a), leaf=(0x1f6a2a, 0x2a8a35, 0x1a5a28, 0x3a9a40),
         trunk=0x4a3420, rock=(0x6a6a5a, 0x585848), mtn=0x3a6a4a, props=(('palm', 4), ('roundtree', 4), ('bush', 4), ('rock', 1)),
         style='forestline', elev=22, clouds=1.4, fog_d=0.0019, weather=('rain', 'firefly', None),
         times=('morning', 'noon', 'mist', 'storm', 'night'), mods=('base', 'emerald', 'jade', 'vivid', 'shadow')),
    dict(key='savanna', ko='사바나', en='Savanna', nouns=['사파리 루트', '아카시아 평원', '사자 언덕', '마른 강바닥', '코끼리 길', '노을 초원'],
         nouns_en=['Safari Route', 'Acacia Plains', 'Lion Hill', 'Dry Riverbed', 'Elephant Trail', 'Sundown Grassland'],
         ground=(0xc9a64a, 0xb8943e), road=0x4a4238, wall=(0xd0602a, 0xf0e0b0), leaf=(0x6a8a2a, 0x7a9a32, 0x5a7a24, 0x8aa040),
         trunk=0x5a4028, rock=(0xa08a6a, 0x8a765a), mtn=0xa08c64, props=(('acacia', 6), ('bush', 3), ('rock', 2)),
         style='flat', elev=12, clouds=0.6, fog_d=0.0012, weather=(None, 'dust', None),
         times=('morning', 'noon', 'golden', 'sunset', 'night'), mods=('base', 'amber', 'golden', 'crimson', 'ashen')),
    dict(key='swamp', ko='늪지', en='Swamp', nouns=['안개 늪', '이끼 다리', '개구리 연못', '맹그로브 수로', '버려진 오두막', '반딧불 습지'],
         nouns_en=['Misty Bog', 'Moss Bridge', 'Frog Pond', 'Mangrove Channel', 'Old Shack', 'Firefly Marsh'],
         ground=(0x3e4a2a, 0x4a5530), road=0x34362e, wall=(0x6a8a3a, 0xc0c8a0), leaf=(0x3a5a2a, 0x4a6a30, 0x2e4a24, 0x5a7a3a),
         trunk=0x3a3020, rock=(0x5a5a48, 0x4a4a3a), mtn=0x4a5a44, accent=(0x9ad04a, 0xd0c04a, 0x6ab0a0, 0xc08ad0),
         props=(('deadtree', 5), ('mushroom', 2), ('bush', 3), ('roundtree', 2)), style='forestline', elev=10, clouds=1.2, fog_d=0.0028,
         weather=('firefly', 'spore', None), times=('mist', 'dusk', 'night', 'overcast', 'morning'), mods=('base', 'jade', 'shadow', 'violet', 'ashen')),
    dict(key='tundra', ko='툰드라', en='Tundra', nouns=['동토 서킷', '순록 평원', '얼음 바람길', '북극 기지', '서리 언덕', '빙원'],
         nouns_en=['Permafrost Circuit', 'Reindeer Plain', 'Icewind Road', 'Arctic Post', 'Frost Hill', 'Ice Field'],
         ground=(0xa8b0a0, 0xc0c8c0), road=0x40444a, wall=(0x4a6a8a, 0xe0e8f0), leaf=(0x5a6a50, 0x6a7a5a, 0x4a5a44, 0x7a8a6a),
         trunk=0x5a4a3a, rock=(0x8a909a, 0x747a84), mtn=0x9aa8b8, props=(('rock', 4), ('bush', 3), ('pine', 2), ('icespike', 1)),
         style='hills', elev=16, fog_d=0.0018, weather=('snow', None, 'snow'), snowcaps=True,
         times=('morning', 'noon', 'overcast', 'aurora', 'night'), mods=('base', 'silver', 'frost', 'azure', 'ashen')),
    dict(key='sakura', ko='벚꽃 동산', en='Cherry Blossom Hills', nouns=['벚꽃길', '사찰 언덕', '연못 정원', '등불 거리', '꽃잎 고개', '봄의 정원'],
         nouns_en=['Blossom Road', 'Temple Hill', 'Pond Garden', 'Lantern Street', 'Petal Pass', 'Spring Garden'],
         ground=(0x7aa85a, 0x8ab868), road=0x4a4448, wall=(0xd03040, 0xf8f0f0), leaf=(0xffb7d0, 0xff9ec0, 0xffc8dc, 0xf08ab0),
         trunk=0x4a3030, rock=(0x8a8a8a, 0x747474), accent=(0xff6040, 0xffd060, 0xff8ab0, 0xffffff), mtn=0x8aa0c0, snowcaps=True,
         props=(('roundtree', 7), ('lantern', 2), ('rock', 1), ('bush', 1)), style='mountains', elev=20, fog_d=0.0013,
         weather=('petal', 'petal', None), times=('morning', 'noon', 'golden', 'dusk', 'night'), mods=('base', 'rose', 'violet', 'pastel', 'crimson')),
    dict(key='bamboo', ko='대나무 숲', en='Bamboo Forest', nouns=['대숲길', '죽림 계곡', '판다 언덕', '바람 소리길', '이슬 정원', '비밀 사원'],
         nouns_en=['Bamboo Path', 'Bamboo Gorge', 'Panda Hill', 'Whispering Way', 'Dew Garden', 'Hidden Shrine'],
         ground=(0x4a7a3a, 0x5a8a42), road=0x3a3c38, wall=(0x2a7a4a, 0xe0e8c0), leaf=(0x4a9a3a, 0x5aaa44, 0x3a8a32, 0x6aba50),
         trunk=0x8aa050, rock=(0x7a7a70, 0x66665e), accent=(0xff5a3a, 0xffd060, 0xff9a5a, 0xffffff), mtn=0x6a8a7a,
         props=(('bamboo', 8), ('rock', 1), ('lantern', 1)), style='bamboo', elev=18, fog_d=0.0020, weather=('leaf', None, 'rain'),
         times=('morning', 'mist', 'noon', 'dusk', 'night'), mods=('base', 'emerald', 'jade', 'golden', 'shadow')),
    dict(key='mushroom', ko='버섯 숲', en='Mushroom Forest', nouns=['버섯 마을', '포자 계곡', '요정 숲길', '독버섯 언덕', '이끼 동굴', '빛나는 숲'],
         nouns_en=['Shroom Village', 'Spore Valley', 'Fairy Trail', 'Toadstool Hill', 'Moss Grotto', 'Glowing Woods'],
         ground=(0x4a5a3a, 0x5a6a42), road=0x3a3640, wall=(0xe04040, 0xf0f0f0), leaf=(0x5a7a3a, 0x6a8a44, 0x4a6a34, 0x7a9a4a),
         trunk=0xf0e8d8, rock=(0x6a6a5a, 0x585848), accent=(0xe03a3a, 0xff8a3a, 0x9a5aff, 0x3ab0ff), mtn=0x5a6a5a,
         props=(('mushroom', 7), ('bush', 3), ('roundtree', 1)), style='mushrooms', elev=16, clouds=0.8, fog_d=0.0021,
         weather=('spore', 'firefly', None), times=('morning', 'mist', 'dusk', 'night', 'golden'), mods=('base', 'violet', 'azure', 'crimson', 'vivid')),
    dict(key='crystal', ko='수정 동굴', en='Crystal Caverns', nouns=['수정 광산', '반짝이 동굴', '자수정 홀', '지하 호수', '보석 터널', '메아리 협곡'],
         nouns_en=['Crystal Mine', 'Glimmer Cave', 'Amethyst Hall', 'Underground Lake', 'Gem Tunnel', 'Echo Gorge'],
         ground=(0x2a2a3a, 0x34344a), road=0x22222c, wall=(0x8a5aff, 0x2a2a3a), rock=(0x4a4a5a, 0x3a3a4a), crystal=0xb07bff,
         props=(('crystal', 6), ('rock', 4), ('icespike', 1)), style='spires', elev=22, clouds=0.0, fog_d=0.0026, night=True, glow=True,
         weather=('sparkle', None), times=('night', 'glow', 'dusk', 'aurora', 'void'), mods=('base', 'azure', 'rose', 'emerald', 'golden')),
    dict(key='coral', ko='산호초 해저', en='Coral Reef', nouns=['산호 정원', '해저 협곡', '거북이 길', '진주 동굴', '해파리 숲', '침몰선'],
         nouns_en=['Coral Garden', 'Abyss Canyon', 'Turtle Way', 'Pearl Cave', 'Jellyfish Forest', 'Shipwreck'],
         ground=(0xd8c89a, 0xc8b888), road=0x3a4a5a, wall=(0xff7a5a, 0xf0f0f0), leaf=(0x2a8a5a, 0x3a9a6a, 0x1a7a4a, 0x4aaa7a),
         rock=(0x8a9aa0, 0x768690), accent=(0xff6a5a, 0xff9ac0, 0xffb040, 0x9a6aff), mtn=0x2a7a9a,
         props=(('coral', 7), ('rock', 2), ('bush', 2)), style='spires', elev=18, clouds=0.0, fog_d=0.0030, sky=(0x1aa0c0, 0.35),
         weather=('bubble', 'bubble', None), times=('shallow', 'deep', 'twilight_sea', 'biolum', 'sunbeam'), mods=('base', 'azure', 'emerald', 'violet', 'golden')),
    dict(key='toxic', ko='독성 황무지', en='Toxic Wasteland', nouns=['오염 구역', '방사능 계곡', '폐기물 처리장', '녹색 늪', '버려진 공장', '경고 구역'],
         nouns_en=['Hazard Zone', 'Fallout Valley', 'Waste Plant', 'Green Sludge', 'Abandoned Works', 'Warning Sector'],
         ground=(0x4a5030, 0x5a5a34), road=0x2e2e2a, wall=(0xf0d020, 0x222222), kerb=(0xf0d020, 0x222222), leaf=(0x4a4a30, 0x5a5a38, 0x3a3a28, 0x6a6a40),
         trunk=0x2a2a20, rock=(0x5a5a4a, 0x4a4a3a), crystal=0x7aff3a, accent=(0x7aff3a, 0xf0d020, 0x3a3a3a, 0xff7a20), mtn=0x5a5a3a,
         props=(('barrel', 4), ('deadtree', 3), ('rock', 3), ('crystal', 2)), style='factory', elev=14, clouds=1.4, fog_d=0.0024,
         sky=(0x8aa030, 0.4), weather=('ash', 'spore', None), times=('overcast', 'dusk', 'night', 'storm', 'noon'),
         mods=('base', 'emerald', 'amber', 'ashen', 'violet')),
    dict(key='ruins', ko='고대 유적', en='Ancient Ruins', nouns=['잊힌 신전', '돌기둥 광장', '왕의 무덤', '정글 사원', '고대 수로', '태양의 제단'],
         nouns_en=['Forgotten Temple', 'Pillar Plaza', "King's Tomb", 'Jungle Shrine', 'Ancient Aqueduct', 'Sun Altar'],
         ground=(0x9a8a5a, 0xa8986a), road=0x5a5248, wall=(0xc8b080, 0x7a6a4a), leaf=(0x4a7a3a, 0x5a8a42, 0x3a6a32, 0x6a9a4a),
         rock=(0xb0a080, 0x9a8a6a), mtn=0x9a906a, props=(('pillar', 6), ('rock', 3), ('bush', 2), ('palm', 1)),
         style='ruins', elev=20, clouds=0.8, fog_d=0.0015, weather=(None, 'dust', None),
         times=('morning', 'noon', 'golden', 'sunset', 'night'), mods=('base', 'golden', 'jade', 'ashen', 'amber')),
    dict(key='farm', ko='전원 마을', en='Countryside', nouns=['풍차 마을', '밀밭 길', '목장 언덕', '사과 농장', '시골 장터', '개울가'],
         nouns_en=['Windmill Village', 'Wheatfield Road', 'Ranch Hill', 'Apple Farm', 'Country Fair', 'Creekside'],
         ground=(0x6aa040, 0x7ab048), road=0x4a4440, wall=(0xc04030, 0xf8f8f0), rock=(0x8a8a80, 0x76766c), mtn=0x7a9ab4,
         props=(('roundtree', 4), ('haystack', 3), ('windmill', 1), ('bush', 2), ('flowers', 2)), style='hills', elev=18, clouds=1.2, fog_d=0.0012,
         lamps=True, weather=(None, None, 'rain'), times=('morning', 'noon', 'golden', 'sunset', 'night'), mods=('base', 'golden', 'emerald', 'amber', 'pastel')),
    dict(key='prairie', ko='초원', en='Prairie', nouns=['대평원', '바람의 들판', '야생마 길', '꽃길', '언덕 너머', '푸른 지평선'],
         nouns_en=['Great Plains', 'Windy Field', 'Mustang Trail', 'Flower Road', 'Over the Hill', 'Blue Horizon'],
         ground=(0x7ab050, 0x8ac058), road=0x45423e, wall=(0x3a7ad0, 0xf0f0f0), flower=(0xff7ab0, 0xffe040, 0xb07bff, 0xffffff), mtn=0x8aa8c8,
         props=(('flowers', 6), ('bush', 3), ('roundtree', 1), ('rock', 1)), style='flat', elev=10, clouds=1.3, fog_d=0.0010,
         weather=(None, 'petal', None), times=('dawn', 'morning', 'noon', 'golden', 'sunset'), mods=('base', 'golden', 'emerald', 'rose', 'frost')),
    dict(key='alien', ko='외계 행성', en='Alien Planet', nouns=['크레이터 루트', '촉수 숲', '이상한 평원', '산성 호수', '외계 신전', '쌍둥이 달'],
         nouns_en=['Crater Route', 'Tentacle Woods', 'Strange Plains', 'Acid Lake', 'Alien Temple', 'Twin Moons'],
         ground=(0x5a2a6a, 0x6a3a7a), road=0x2a2234, wall=(0x3aff9a, 0x2a1a3a), leaf=(0x3aff9a, 0x2ae0c0, 0xff3ad0, 0x9aff3a),
         trunk=0xc0a0ff, rock=(0x6a4a7a, 0x5a3a6a), crystal=0x3affd0, accent=(0xff3ad0, 0x3affd0, 0xffe03a, 0x9a5aff), planet=0xff6ad0, mtn=0x6a3a8a,
         props=(('mushroom', 4), ('crystal', 3), ('rock', 3), ('coral', 2)), style='planet', elev=26, clouds=0.6, fog_d=0.0018, glow=True,
         sky=(0x6a2a8a, 0.5), weather=('spore', 'sparkle', None), times=('dawn', 'noon', 'dusk', 'night', 'aurora'),
         mods=('base', 'emerald', 'crimson', 'azure', 'golden')),
    dict(key='cloud', ko='구름 왕국', en='Cloud Kingdom', nouns=['하늘 궁전', '무지개 다리', '천공의 섬', '바람의 성', '은하수 길', '새벽 정원'],
         nouns_en=['Sky Palace', 'Rainbow Bridge', 'Floating Isle', 'Castle of Winds', 'Milky Way', 'Dawn Garden'],
         ground=(0xf4f6ff, 0xe4e8fa), road=0x8a90b0, wall=(0xffd040, 0xffffff), leaf=(0xffffff, 0xf0f4ff, 0xe0e8ff, 0xfafaff),
         rock=(0xe8ecf8, 0xd0d8ec), crystal=0xffe070, mtn=0xd0dcff, props=(('cloud', 6), ('pillar', 3), ('crystal', 1)),
         style='clouds', elev=30, clouds=2.0, fog_d=0.0012, arches=True, sky=(0x9ac8ff, 0.3), weather=('sparkle', None, None),
         times=('dawn', 'morning', 'noon', 'sunset', 'aurora'), mods=('base', 'rose', 'golden', 'azure', 'violet')),
    dict(key='glacier', ko='빙하', en='Glacier', nouns=['얼음 협곡', '빙산 해협', '크레바스 길', '푸른 얼음 동굴', '북극광 서킷', '빙벽 루트'],
         nouns_en=['Ice Gorge', 'Iceberg Strait', 'Crevasse Run', 'Blue Ice Cave', 'Polar Light Circuit', 'Ice Wall Route'],
         ground=(0xd8ecf8, 0xc0dcf0), road=0x3a4250, wall=(0x40a0ff, 0xf0f8ff), kerb=(0x40a0ff, 0xf0f8ff), rock=(0xc8e0f0, 0xa8c8e0),
         crystal=0x9ad8ff, mtn=0xb4d4f0, props=(('icespike', 5), ('crystal', 3), ('rock', 2)), style='snowpeaks', elev=30, clouds=0.8, fog_d=0.0020,
         snowy=True, weather=('snow', 'sparkle', None), times=('morning', 'noon', 'sunset', 'night', 'aurora'), mods=('base', 'azure', 'silver', 'violet', 'emerald')),
    dict(key='lavender', ko='라벤더 들판', en='Lavender Fields', nouns=['보랏빛 들판', '향기로운 언덕', '풍차 고개', '꿀벌 길', '프로방스 로드', '꽃향기 마을'],
         nouns_en=['Purple Fields', 'Fragrant Hill', 'Windmill Pass', 'Honeybee Lane', 'Provence Road', 'Scented Village'],
         ground=(0x6a8a4a, 0x7a9a52), road=0x4a4448, wall=(0x8a5ad0, 0xf8f0ff), flower=(0x9a6ad8, 0xb08ae8, 0x7a4ac0, 0xc8a8f0), mtn=0x9a9ac8,
         props=(('flowers', 7), ('windmill', 1), ('roundtree', 2), ('bush', 1)), style='hills', elev=14, fog_d=0.0012,
         weather=('petal', None, None), times=('morning', 'noon', 'golden', 'sunset', 'dusk'), mods=('base', 'violet', 'rose', 'azure', 'pastel')),
    dict(key='saltflat', ko='소금 사막', en='Salt Flats', nouns=['소금 평원', '거울 호수', '하얀 사막', '결정 지대', '신기루 직선로', '소금 광산'],
         nouns_en=['Salt Plain', 'Mirror Lake', 'White Desert', 'Crystal Zone', 'Mirage Straight', 'Salt Mine'],
         ground=(0xf0f0ec, 0xe4e4dc), road=0x5a5a60, wall=(0x3a8ad0, 0xffffff), rock=(0xe0e0d8, 0xc8c8c0), crystal=0xf0f4ff, mtn=0xb0b4c0,
         props=(('rock', 3), ('crystal', 3), ('icespike', 1)), style='flat', elev=6, clouds=0.8, fog_d=0.0010, weather=(None, 'dust', None),
         times=('dawn', 'noon', 'golden', 'sunset', 'night'), mods=('base', 'rose', 'azure', 'golden', 'silver')),
    dict(key='badlands', ko='황무지', en='Badlands', nouns=['붉은 황무지', '해골 계곡', '바람 깎인 언덕', '무법자 길', '화석 지대', '먼지 폭풍로'],
         nouns_en=['Red Badlands', 'Skull Valley', 'Wind-Carved Hills', 'Outlaw Trail', 'Fossil Beds', 'Duststorm Road'],
         ground=(0x9a6a5a, 0x8a5a4a), road=0x3e3836, wall=(0xd09040, 0x3a3030), rock=(0x8a5a4a, 0x7a4a3a),
         mesa=(0x8a5a4a, 0xa06a5a, 0x7a4a3a, 0xc09080), leaf=(0x6a6a3a, 0x7a7a44, 0x5a5a34, 0x8a8a4a), trunk=0x4a3a2a,
         props=(('mesa', 4), ('rock', 3), ('deadtree', 2), ('cactus', 1)), style='mesas', elev=28, clouds=0.4, fog_d=0.0017,
         weather=('dust', None, None), times=('noon', 'golden', 'sunset', 'dusk', 'storm'), mods=('base', 'violet', 'ashen', 'amber', 'crimson')),
    dict(key='highland', ko='고원 지대', en='Highland Moors', nouns=['바람의 고원', '돌무덤 언덕', '이끼 황야', '양치기 길', '고성 폐허', '안개 호수'],
         nouns_en=['Windy Highland', 'Cairn Hill', 'Mossy Moor', "Shepherd's Path", 'Castle Ruins', 'Misty Loch'],
         ground=(0x6a7a4a, 0x7a8a52), road=0x40403c, wall=(0x5a6a8a, 0xe0e0d8), leaf=(0x5a7a3a, 0x6a8a44, 0x4a6a34, 0x7a9a4a),
         rock=(0x8a8a84, 0x74746e), mtn=0x7a8494, props=(('rock', 4), ('bush', 3), ('pillar', 2), ('pine', 1)),
         style='mountains', elev=30, clouds=1.6, fog_d=0.0019, weather=(None, 'rain', None),
         times=('morning', 'overcast', 'mist', 'sunset', 'storm'), mods=('base', 'jade', 'golden', 'ashen', 'frost')),
    dict(key='haunted', ko='유령 묘지', en='Haunted Graveyard', nouns=['유령의 언덕', '저주받은 저택', '해골 다리', '마녀의 숲', '박쥐 동굴', '달빛 묘지'],
         nouns_en=['Ghost Hill', 'Cursed Manor', 'Skull Bridge', 'Witch Woods', 'Bat Cave', 'Moonlit Cemetery'],
         ground=(0x2a3028, 0x343a30), road=0x26262a, wall=(0x8a5aff, 0x3a3a44), leaf=(0x3a3a2a, 0x44442e, 0x2e2e24, 0x4a4a34),
         trunk=0x2a2420, rock=(0x6a6a6e, 0x58585c), accent=(0xff8a20, 0x9a5aff, 0x6aff6a, 0xffd040), mtn=0x3a3a4a,
         props=(('deadtree', 4), ('tombstone', 4), ('pumpkin', 2), ('lantern', 1)), style='forestline', elev=14, fog_d=0.0026,
         sky=(0x3a1a5a, 0.3), weather=('firefly', None), times=('dusk', 'night', 'mist', 'storm', 'aurora'),
         mods=('base', 'violet', 'emerald', 'crimson', 'ashen')),
    dict(key='factory', ko='증기 공장', en='Steampunk Factory', nouns=['톱니바퀴 공장', '증기 기관실', '구리 파이프길', '시계탑 광장', '석탄 항구', '용광로'],
         nouns_en=['Cog Works', 'Steam Engine Hall', 'Copper Pipeway', 'Clocktower Square', 'Coal Harbor', 'Blast Furnace'],
         ground=(0x5a4a3a, 0x6a5a44), road=0x34302c, wall=(0xc08040, 0x3a2a20), rock=(0x6a5a4a, 0x5a4a3a), crystal=0xff9a3a,
         accent=(0xffb040, 0xc08040, 0x8a6a4a, 0xff7a3a), mtn=0x6a5a4a, props=(('chimney', 5), ('barrel', 3), ('rock', 1)),
         style='factory', elev=16, fog_d=0.0022, lamps=True, sky=(0x8a6a4a, 0.35), weather=('ash', None, 'ember'),
         times=('overcast', 'golden', 'sunset', 'dusk', 'night'), mods=('base', 'amber', 'crimson', 'ashen', 'golden')),
    dict(key='retro', ko='신스웨이브', en='Synthwave', nouns=['네온 그리드', '레트로 하이웨이', '크롬 일몰', '아케이드 시티', '레이저 계곡', '카세트 해변'],
         nouns_en=['Neon Grid', 'Retro Highway', 'Chrome Sunset', 'Arcade City', 'Laser Valley', 'Cassette Beach'],
         ground=(0x1a0a2a, 0x24103a), road=0x14101e, wall=(0xff3ad0, 0x3ad0ff), kerb=(0xff3ad0, 0x3ad0ff), leaf=(0xff3ad0, 0xc83aff, 0x3ad0ff, 0xff6ab0),
         trunk=0x3a1a5a, rock=(0x3a2a5a, 0x2a1a4a), crystal=0x3ad0ff, accent=(0xff3ad0, 0x3ad0ff, 0xffd03a, 0xff6a3a),
         props=(('palm', 5), ('pyramid', 2), ('crystal', 2)), style='retro', elev=10, clouds=0.0, fog_d=0.0016, night=True, glow=True, lamps=True, arches=True,
         weather=(None, 'sparkle'), times=('dusk', 'night', 'sunset', 'dawn', 'aurora'), mods=('base', 'azure', 'violet', 'golden', 'crimson')),
    dict(key='pyramid', ko='피라미드 사구', en='Pyramid Dunes', nouns=['파라오의 길', '스핑크스 광장', '나일 강변', '황금 무덤', '사막 오아시스', '왕가의 계곡'],
         nouns_en=["Pharaoh's Road", 'Sphinx Square', 'Nile Bank', 'Golden Tomb', 'Desert Oasis', 'Valley of Kings'],
         ground=(0xe0c078, 0xd0b068), road=0x5a5040, wall=(0x2a5ad0, 0xf0d890), leaf=(0x3a8a3a, 0x4a9a42, 0x2f7a32, 0x5aaa4a), trunk=0x8a6a40,
         rock=(0xc8a868, 0xb4945a), mtn=0xd4b478, props=(('pyramid', 3), ('palm', 3), ('rock', 2), ('pillar', 2)), style='dunes', elev=16, clouds=0.3,
         fog_d=0.0013, pyramids=True, weather=(None, 'dust'), times=('dawn', 'noon', 'golden', 'sunset', 'night'), mods=('base', 'golden', 'crimson', 'pastel', 'amber')),
    dict(key='sunflower', ko='해바라기 언덕', en='Sunflower Hills', nouns=['해바라기 밭', '태양의 언덕', '노란 물결길', '꿀벌 정원', '여름 오솔길', '농장 고개'],
         nouns_en=['Sunflower Field', 'Sun Hill', 'Yellow Wave Road', 'Bee Garden', 'Summer Trail', 'Farm Pass'],
         ground=(0x6a9a3a, 0x7aaa42), road=0x44403a, wall=(0xf0b020, 0x3a6a2a), flower=(0xffd020, 0xffb010, 0xffe050, 0xff9a20), mtn=0x8ab0c8,
         props=(('sunflower', 7), ('roundtree', 2), ('haystack', 1)), style='hills', elev=14, fog_d=0.0011, weather=(None, 'petal', None),
         times=('morning', 'noon', 'golden', 'sunset', 'dusk'), mods=('base', 'golden', 'amber', 'crimson', 'pastel')),
    dict(key='fjord', ko='피오르드', en='Fjord', nouns=['바이킹 해안', '빙하 폭포', '절벽 길', '등대 곶', '북해 루트', '고래 만'],
         nouns_en=['Viking Coast', 'Glacier Falls', 'Cliffside Road', 'Lighthouse Cape', 'North Sea Route', 'Whale Bay'],
         ground=(0x4a6a4a, 0x5a7a54), road=0x3a3e44, wall=(0x2a5a8a, 0xf0f0f0), leaf=(0x2a5a3a, 0x346a44, 0x224a32, 0x3e7a4e),
         rock=(0x6a7078, 0x585e66), water=0x2a5a7a, mtn=0x6a7888, snowcaps=True, props=(('pine', 5), ('rock', 4), ('bush', 1)),
         style='cliffs', elev=28, clouds=1.4, fog_d=0.0018, weather=(None, 'rain', 'snow'),
         times=('morning', 'overcast', 'sunset', 'night', 'aurora'), mods=('base', 'azure', 'frost', 'jade', 'shadow')),
    dict(key='moon', ko='달 기지', en='Lunar Base', nouns=['고요의 바다', '크레이터 기지', '월면 도로', '지구돋이 언덕', '착륙장', '달의 뒷면'],
         nouns_en=['Sea of Tranquility', 'Crater Base', 'Lunar Road', 'Earthrise Hill', 'Landing Pad', 'Far Side'],
         ground=(0xa0a0a4, 0x909094), road=0x3a3c42, wall=(0xf0f0f0, 0x3a3c42), kerb=(0xf0a020, 0xf0f0f0), rock=(0xb0b0b4, 0x8c8c90),
         crystal=0xe0e8ff, planet=0x3a8ad0, props=(('rock', 6), ('dish', 2), ('dome', 2)), style='planet', elev=18, clouds=0.0, fog_d=0.0007,
         night=True, lamps=True, weather=(None,), times=('void', 'nebula_b', 'nebula_v', 'nebula_g', 'nebula_r'), mods=('base', 'silver', 'azure', 'golden', 'rose')),
    dict(key='mars', ko='화성 개척지', en='Mars Colony', nouns=['붉은 평원', '올림푸스 루트', '개척 돔', '먼지 협곡', '탐사선 길', '극지 기지'],
         nouns_en=['Red Plains', 'Olympus Route', 'Colony Dome', 'Dust Canyon', 'Rover Trail', 'Polar Station'],
         ground=(0xb85a34, 0xa84e2c), road=0x3a2e2a, wall=(0xf0f0f0, 0xd06030), rock=(0x9a4a2a, 0x8a3e24), crystal=0xffa060,
         mesa=(0x9a4a2a, 0xb85a34, 0x8a3e24, 0xd08a60), mtn=0xa05030, props=(('rock', 5), ('dome', 2), ('dish', 1), ('mesa', 2)),
         style='mesas', elev=24, clouds=0.2, fog_d=0.0016, lamps=True, sky=(0xd09060, 0.6), weather=('dust', None),
         times=('dawn', 'noon', 'sunset', 'dusk', 'night'), mods=('base', 'crimson', 'amber', 'ashen', 'rose')),
    dict(key='toy', ko='장난감 나라', en='Toy Land', nouns=['블록 마을', '장난감 상자', '기차 선로', '인형의 집', '블록 성', '태엽 공원'],
         nouns_en=['Block Town', 'Toy Box', 'Train Tracks', 'Dollhouse', 'Brick Castle', 'Wind-up Park'],
         ground=(0x5ac85a, 0x4ab84a), road=0x5a5a6a, wall=(0xff4a4a, 0x4a8aff), kerb=(0xffd03a, 0x4a8aff), leaf=(0x3ad05a, 0xffd03a, 0xff6a3a, 0x3ab0ff),
         accent=(0xff4a4a, 0x4a8aff, 0xffd03a, 0x4ac85a, 0xff8a3a, 0xb05aff), rock=(0xb0b0c0, 0x9a9aaa), mtn=0x9ad0ff,
         props=(('blocks', 6), ('roundtree', 2)), style='toyblocks', elev=16, clouds=1.2, fog_d=0.0012, arches=True, weather=(None, 'sprinkle'),
         times=('morning', 'noon', 'golden', 'sunset', 'night'), mods=('base', 'vivid', 'pastel', 'azure', 'rose')),
    dict(key='alpine', ko='알프스 초원', en='Alpine Meadows', nouns=['알프스 고개', '목초지 길', '산장 마을', '에델바이스 언덕', '빙하 호수', '케이블카 루트'],
         nouns_en=['Alpine Pass', 'Meadow Road', 'Chalet Village', 'Edelweiss Hill', 'Glacier Lake', 'Cable Car Route'],
         ground=(0x6aa04a, 0x5a9040), road=0x40404a, wall=(0xd02a2a, 0xffffff), flower=(0xffffff, 0xffe040, 0xc060ff, 0xff8ab0), mtn=0x8a9ab4,
         props=(('pine', 5), ('flowers', 3), ('rock', 2), ('roundtree', 1)), style='snowpeaks', elev=34, clouds=1.2, fog_d=0.0012,
         weather=(None, None, 'snow'), times=('morning', 'noon', 'golden', 'sunset', 'night'), mods=('base', 'emerald', 'golden', 'frost', 'azure')),
]

# 날씨 입자: 색(없으면 테마에서), 떨어지는 속도(+아래/-위), 옆 흔들림, 크기
WEATHER = {
    'snow': ((255, 255, 255), 3.4, 1.2, 2), 'ember': ((255, 150, 50), -2.4, 1.2, 2), 'leaf': (None, 2.6, 2.4, 2), 'sprinkle': (None, 2.8, 1.0, 2),
    'rain': ((170, 200, 255), 26.0, 0.6, 1), 'petal': (None, 1.8, 2.8, 2), 'spore': ((210, 255, 140), -0.8, 1.6, 2), 'firefly': ((255, 236, 110), 0.0, 2.2, 2),
    'ash': ((160, 160, 166), 1.4, 1.0, 2), 'bubble': ((200, 240, 255), -2.2, 1.0, 2), 'sparkle': (None, 0.0, 0.3, 1), 'dust': (None, 0.4, 5.0, 1),
}

# 장식물 종류별 모양 변형 개수
PROP_VARS = {'roundtree': 4, 'lollipop': 6, 'icecream': 3, 'building': 4, 'mushroom': 4, 'coral': 4, 'flowers': 4, 'blocks': 6,
             'tombstone': 2, 'deadtree': 2, 'acacia': 2}

_BIOMES = {}


def rgb_hex(c):
    return (int(c[0]) << 16) | (int(c[1]) << 8) | int(c[2])


def _c(v):
    return hex_rgb(v) if isinstance(v, int) else tuple(v)


def hsv_mod(c, mod):
    """색감 변형: 목표 색상 쪽으로 색상각 이동 + 채도/명도 배율"""
    tgt, amt, sm, vm = mod[2], mod[3], mod[4], mod[5]
    h, s, v = colorsys.rgb_to_hsv(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    if tgt is not None and amt > 0 and s > 0.06:
        d = ((tgt / 360.0 - h + 0.5) % 1.0) - 0.5
        h = (h + d * amt) % 1.0
    s = clamp(s * sm, 0.0, 1.0)
    v = clamp(v * vm, 0.0, 1.0)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5))


def biome_family(map_id):
    return (int(min(MAP_COUNT, max(1, int(map_id)))) - 1) % BIOME_FAMILIES


def family_map(map_id, family):
    """같은 변형(시간대/색감)을 유지한 채 다른 생태계의 맵 번호"""
    n = int(min(MAP_COUNT, max(1, int(map_id)))) - 1
    return (n // BIOME_FAMILIES) * BIOME_FAMILIES + (int(family) % BIOME_FAMILIES) + 1


def biome(map_id):
    """맵 번호 -> 바이옴(테마) 정보. 렌더러/트랙 생성기가 쓰는 모든 색/장식물/날씨/지형 스타일"""
    mid = int(min(MAP_COUNT, max(1, int(map_id))))
    b = _BIOMES.get(mid)
    if b is not None:
        return b
    n = mid - 1
    fi = n % BIOME_FAMILIES
    v = n // BIOME_FAMILIES
    F = dict(_DEF)
    F.update(FAMILIES[fi])
    tk = F['times'][v % 5]
    mk = F['mods'][(v // 5) % 5]
    T = TIMES[tk]
    M = MODS[mk]
    r = Rng(hash32(n * 104729 + 7))
    fam_night = bool(F.get('night'))
    night = bool(T.get('night')) or fam_night
    amb = 1.0 if fam_night else T['amb']
    tint = hex_rgb(T['tint']) if T.get('tint') is not None else None
    tkk = T.get('tk', 0.0)

    def scene(col, mod=True, light=True, tk_=1.0):
        c = _c(col)
        if mod:
            c = hsv_mod(c, M)
        if light:
            c = shade_rgb(c, amb)
        if tint is not None and tkk > 0:
            c = mix_rgb(c, tint, tkk * tk_)
        return c

    def glow(col):
        return hsv_mod(_c(col), M)
    g0, g1 = scene(F['ground'][0]), scene(F['ground'][1])
    leaf = [scene(x) for x in F['leaf']]
    rock = [scene(x) for x in F['rock']]
    trunk = scene(F['trunk'], mod=False)
    flower = [scene(x, light=False, tk_=0.4) for x in F['flower']]
    mesa = [scene(x) for x in F['mesa']]
    accent = [glow(x) for x in F['accent']]
    crystal = glow(F['crystal'])
    mtn = scene(F.get('mtn', F['rock'][0]))
    water = scene(F['water'])
    far = shade_rgb(mix_rgb(g0, mtn, 0.35), 0.85)
    road = shade_rgb(scene(F['road'], mod=False), 1.0)
    if F.get('glow'):
        w0, w1 = glow(F['wall'][0]), _c(F['wall'][1])
    else:
        w0, w1 = scene(F['wall'][0], tk_=0.5), scene(F['wall'][1], mod=False, tk_=0.5)
    kerb = (scene(F['kerb'][0], tk_=0.5), scene(F['kerb'][1], mod=False, tk_=0.5)) if not fam_night else (glow(F['kerb'][0]), _c(F['kerb'][1]))
    st = F.get('sky')
    top, bot = hex_rgb(T['top']), hex_rgb(T['bot'])
    if st:
        top = mix_rgb(top, hex_rgb(st[0]), st[1])
        bot = mix_rgb(bot, hex_rgb(st[0]), st[1] * 0.8)
    if mk not in ('base',):
        kk = 0.55 if M[2] is None else 0.35            # 명도/채도 계열 색감은 하늘에도 더 강하게
        bot = mix_rgb(bot, hsv_mod(bot, M), kk if not night else kk * 0.5)
        top = mix_rgb(top, hsv_mod(top, M), kk * 0.6 if not night else kk * 0.3)
    fog = mix_rgb(bot, far, 0.12)
    sun = hex_rgb(T['sun'])
    az = r() * TAU
    el = T['el']
    sun_dir = (round(math.cos(el) * math.sin(az), 3), round(max(0.05, math.sin(el)), 3), round(math.cos(el) * math.cos(az), 3))
    clouds = clamp(F['clouds'] * T.get('clouds', 1.0) if F['clouds'] > 0 else 0.0, 0.0, 2.6)
    cloud = mix_rgb((255, 255, 255), bot, 0.3) if not night else shade_rgb(mix_rgb(bot, (120, 130, 160), 0.5), 1.4)
    if tk in ('sunset', 'dusk', 'dawn'):
        cloud = mix_rgb(cloud, sun, 0.4)
    # 날씨
    wl = F['weather']
    w = wl[hash32(n * 31 + 17) % len(wl)]
    if T.get('weather') == 'rain' and w not in ('ember', 'ash', 'bubble'):
        w = 'snow' if (F.get('snowy') or mk == 'frost') else 'rain'
    if w == 'firefly' and not night and tk not in ('dusk', 'mist'):
        w = None if 'leaf' not in wl else 'leaf'
    fog_d = F['fog_d'] * T.get('fogk', 1.0) * (1.3 if w in ('rain', 'snow', 'dust', 'ash') else 1.0)
    wcol = None
    if w:
        base_c = WEATHER[w][0]
        if base_c is not None:
            wcol = base_c
        elif w == 'leaf':
            wcol = leaf[0]
        elif w == 'petal':
            wcol = mix_rgb(flower[0] if F['key'] not in ('sakura',) else leaf[0], (255, 255, 255), 0.25)
        elif w == 'sparkle':
            wcol = mix_rgb(crystal, (255, 255, 255), 0.5)
        elif w == 'dust':
            wcol = mix_rgb(g0, (255, 255, 255), 0.35)
        else:
            wcol = (255, 255, 255)
    # 장식물 비율은 맵마다 조금씩 다르게
    props = tuple((k, max(1, int(round(wt * (0.55 + r() * 0.9) * 10)))) for k, wt in F['props'])
    snowy = bool(F.get('snowy')) or mk == 'frost'
    if snowy and not F.get('snowy'):
        leaf = [mix_rgb(c, (235, 242, 250), 0.25) for c in leaf]
    arches = None
    if F.get('arches'):
        arches = rgb_hex(accent[0] if F['key'] in ('neon', 'retro', 'candy', 'toy') else w0)
    tko, ten = T['ko'], T['en']
    mko, men = M[0], M[1]
    name_ko = ('%s %s' % (mko, F['ko'])).strip() + ' (%s)' % tko
    name_en = ('%s %s' % (men, F['en'])).strip() + ' (%s)' % ten
    hemi_k = 0.95 if not night else 0.8
    b = dict(
        key=F['key'], family=fi, time=tk, mod=mk, name=name_ko, en=name_en, family_ko=F['ko'], family_en=F['en'],
        nouns=F['nouns'], nouns_en=F['nouns_en'], style=F['style'],
        sky_top=rgb_hex(top), sky_bot=rgb_hex(bot), fog=rgb_hex(fog), fog_d=round(fog_d, 5),
        ground=(rgb_hex(g0), rgb_hex(g1)), far=rgb_hex(far), road=rgb_hex(road), wall=(rgb_hex(w0), rgb_hex(w1)),
        sun=rgb_hex(sun), sun_i=T['si'] * F['light'], sun_dir=sun_dir,
        hemi=(rgb_hex(mix_rgb(top, (255, 255, 255), 0.45)), rgb_hex(g0), hemi_k),
        props=props, weather=w, wcol=wcol, elev=F['elev'], clouds=clouds, cloud=cloud,
        rock=(rgb_hex(rock[0]), rgb_hex(rock[1])), snowy=snowy, night=night, lamps=bool(F.get('lamps')) and night,
        glow_wall=bool(F.get('glow')), arches=arches, aurora=bool(T.get('aurora')), snowcaps=bool(F.get('snowcaps')) or snowy,
        pyramids=bool(F.get('pyramids')),
        leaf=leaf, trunk=trunk, flower=flower, crystal=crystal, accent=accent, mesa=mesa, cactus=scene(F['cactus']),
        water=water, planet=glow(F['planet']), mtn=mtn, kerb=kerb,
        rgb=dict(top=top, bot=bot, fog=fog, far=far, ground=g0, ground2=g1, mtn=mtn, hill=shade_rgb(leaf[0], 0.8), rock=rock[0],
                 rock2=rock[1], water=water, crystal=crystal, accent=accent, mesa=mesa, trunk=trunk, leaf=leaf, cloud=cloud,
                 planet=glow(F['planet']), sun=sun),
    )
    if len(_BIOMES) > 64:
        _BIOMES.clear()
    _BIOMES[mid] = b
    return b


# ---------------------------------------------------------------------------
#  지평선(360도 먼 배경) : 두 프론트엔드가 같은 정의로 그림
#   레이어 목록 [(반지름 m, [아이템...])]  (먼 것부터)
#   아이템: ('ridge', 색, 꼭대기색|None, 높이[201])  ('poly', 색, [(각 0..1, 높이 m), ...] 볼록)  ('disc', 색, 각, 높이, 반지름 m)
#           ('ring', 색, 각, 높이, 가로 반지름, 세로 반지름, 두께)  ('line', 색, [(각, 높이)...], 두께 m)
# ---------------------------------------------------------------------------
HZ_SEG = 200


def horizon_layers(th, seed):
    rnd = Rng((seed ^ 0x6a09e667) & 0xFFFFFFFF)
    C = th['rgb']
    fog, bot = C['fog'], C['bot']
    out = []

    def layer(rad):
        items = []
        out.append((rad, items))
        return items

    def heights(base, amp, harm=(1, 2, 3, 5, 8, 13), sharp=False):
        phs = [rnd() * TAU for _ in harm]
        hs = []
        for i in range(HZ_SEG + 1):
            a = TAU * i / HZ_SEG
            h = base
            for k, p in zip(harm, phs):
                s_ = math.sin(k * a + p)
                h += amp / (k ** 0.8) * ((1.0 - 2.0 * abs(s_)) * -1.0 if sharp else s_)
            hs.append(max(8.0, h))
        return hs

    def h_at(hs, a):
        f = (a % 1.0) * HZ_SEG
        i = int(f)
        t = f - i
        return hs[i] + (hs[min(HZ_SEG, i + 1)] - hs[i]) * t

    def ridge(items, col, hs, top=None):
        items.append(('ridge', col, top, hs))

    def poly(items, col, pts):
        items.append(('poly', col, pts))

    def rect(items, col, a, w, h0, h1, rad):
        da = w / (TAU * rad) / 2.0
        poly(items, col, [(a - da, h0), (a + da, h0), (a + da, h1), (a - da, h1)])

    def tri(items, col, a, w, h0, h1, rad):
        da = w / (TAU * rad) / 2.0
        poly(items, col, [(a - da, h0), (a + da, h0), (a, h1)])

    def disc(items, col, a, h, r):
        items.append(('disc', col, a % 1.0, h, r))

    def cap(items, col, a, w, h0, hh, rad, n=10):
        """반원 (버섯 갓 / 섬 / 구름)"""
        da = w / (TAU * rad) / 2.0
        pts = [(a + da * math.cos(math.pi * k / n), h0 + hh * math.sin(math.pi * k / n)) for k in range(n + 1)]
        poly(items, col, pts)

    st = th['style']
    acc = C['accent']
    hill = C['hill']
    mtn = C['mtn']
    snow_top = (250, 252, 255) if th.get('snowcaps') else None
    if st == 'mountains':
        L = layer(2600)
        ridge(L, mix_rgb(mtn, bot, 0.45), heights(260, 150), snow_top)
        L = layer(2100)
        hs = heights(150, 90)
        ridge(L, mix_rgb(hill, fog, 0.35), hs)
        for _ in range(110):
            a = rnd()
            h = h_at(hs, a)
            tri(L, mix_rgb(hill, fog, 0.25), a, 26 + rnd() * 18, h - 12, h + 22 + rnd() * 26, 2100)
    elif st == 'snowpeaks':
        L = layer(2600)
        ridge(L, mix_rgb(mix_rgb(mtn, (240, 246, 252), 0.4), bot, 0.2), heights(330, 170, sharp=True), (250, 252, 255))
        L = layer(2000)
        ridge(L, mix_rgb(hill, fog, 0.4), heights(120, 60))
    elif st == 'hills':
        L = layer(2500)
        ridge(L, mix_rgb(mtn, bot, 0.5), heights(150, 70, (1, 2, 3, 4)), snow_top)
        L = layer(2000)
        hs = heights(80, 40, (1, 2, 3, 5))
        ridge(L, mix_rgb(hill, fog, 0.3), hs)
        for _ in range(80):
            a = rnd()
            disc(L, mix_rgb(hill, fog, 0.2), a, h_at(hs, a) + 6, 12 + rnd() * 10)
    elif st == 'dunes':
        L = layer(2500)
        ridge(L, mix_rgb(C['ground'], bot, 0.5), heights(130, 70, (1, 2, 3, 4)))
        L = layer(2300)
        n = 4 if th.get('pyramids') else 3
        for _ in range(n):
            a = rnd()
            b_ = 160 + rnd() * 140
            if th.get('pyramids'):
                tri(L, mix_rgb(C['rock'], fog, 0.3), a, b_ * 1.9, 0, b_ * 1.2, 2300)
                tri(L, mix_rgb(shade_rgb(C['rock'], 0.78), fog, 0.3), a + b_ * 0.45 / (TAU * 2300), b_ * 0.95, 0, b_ * 1.2, 2300)
            else:
                tri(L, mix_rgb(C['rock'], fog, 0.35), a, b_, 0, b_ * 0.85, 2300)
        L = layer(1900)
        ridge(L, mix_rgb(C['ground2'], fog, 0.2), heights(70, 45, (1, 2, 4, 6)))
    elif st == 'city':
        dark1 = mix_rgb((44, 26, 84), acc[0], 0.12)
        dark2 = mix_rgb((22, 14, 52), acc[1], 0.1)
        for col, hmax, rad, n in ((mix_rgb(dark1, bot, 0.25), 520, 2500, 150), (dark2, 330, 2000, 120)):
            L = layer(rad)
            for i in range(n):
                a = i / float(n) + rnd() * 0.002
                w = 30 + rnd() * 55
                h = 40 + rnd() * hmax
                rect(L, col, a, w, -40, h, rad)
                if rnd() < 0.5:
                    rect(L, acc[int(rnd() * len(acc)) % len(acc)], a, w * 1.02, h * (0.3 + 0.6 * rnd()), h * (0.3 + 0.6 * rnd()) + 4, rad)
                for _ in range(int(h / 60)):
                    if rnd() < 0.55:
                        wa = a + (rnd() - 0.5) * w * 0.7 / (TAU * rad)
                        wh = rnd() * h
                        rect(L, (255, 225, 140) if rnd() < 0.6 else acc[1], wa, 5, wh, wh + 4, rad)
    elif st == 'volcano':
        L = layer(2400)
        ridge(L, mix_rgb(mtn, bot, 0.25), heights(160, 90))
        for _ in range(2):
            a = rnd()
            b_ = 360 + rnd() * 180
            da = b_ / (TAU * 2200)
            top_w = 40 / (TAU * 2200)
            hh = b_ * 1.1
            poly(L, shade_rgb(mtn, 1.15), [(a - da, 0), (a + da, 0), (a + top_w, hh), (a - top_w, hh)])
            poly(L, (255, 120, 40), [(a - top_w, hh), (a + top_w, hh), (a + top_w * 0.5, hh - 30), (a - top_w * 0.5, hh - 22)])
            poly(L, (255, 110, 30), [(a - top_w * 0.3, hh - 24), (a + top_w * 0.1, hh - 24), (a - da * 0.3, 40), (a - da * 0.36, 40)])
        L = layer(1900)
        ridge(L, shade_rgb(mtn, 0.8), heights(80, 50))
    elif st == 'sea':
        L = layer(2600)
        ridge(L, mix_rgb(C['water'], bot, 0.3), [24.0] * (HZ_SEG + 1))
        for _ in range(6):
            a = rnd()
            cap(L, mix_rgb(hill, fog, 0.35), a, 160 + rnd() * 260, 20, 30 + rnd() * 60, 2600)
        L = layer(1700)
        ridge(L, mix_rgb(C['ground'], fog, 0.2), heights(22, 12, (1, 3, 5)))
    elif st == 'candy':
        L = layer(2500)
        ridge(L, mix_rgb(mix_rgb(acc[0], (255, 255, 255), 0.55), bot, 0.35), heights(200, 120))
        L = layer(2000)
        hs = heights(110, 70)
        ridge(L, mix_rgb(mix_rgb(acc[1], (255, 255, 255), 0.5), fog, 0.3), hs)
        for i in range(32):
            a = rnd()
            h = h_at(hs, a)
            rect(L, (255, 255, 255), a, 6, h - 5, h + 60, 2000)
            disc(L, acc[i % len(acc)], a, h + 72, 18)
            disc(L, (255, 255, 255), a, h + 72, 8)
    elif st == 'planet':
        L = layer(2700)
        a = rnd()
        pc = C['planet']
        disc(L, mix_rgb(pc, bot, 0.15), a, 820, 380)
        disc(L, mix_rgb(shade_rgb(pc, 0.6), bot, 0.15), a + 120 / (TAU * 2700), 780, 300)
        L.append(('ring', mix_rgb((220, 200, 160), bot, 0.2), a, 820, 640, 110, 22))
        L = layer(2400)
        ridge(L, mix_rgb(C['rock'], bot, 0.35), heights(150, 80))
        L = layer(1900)
        ridge(L, mix_rgb(C['rock2'], fog, 0.2), heights(80, 50, (1, 2, 4, 7)))
    elif st == 'mesas':
        mcols = C['mesa']
        for li, (col, hmax, rad, n) in enumerate(((mcols[0], 520, 2500, 40), (mcols[2], 330, 1900, 40))):
            L = layer(rad)
            for i in range(n):
                a = i / float(n) + rnd() * 0.01
                w = 120 + rnd() * 260
                h = hmax * (0.35 + rnd() * 0.65)
                cc = mix_rgb(col, fog, 0.3 - li * 0.15)
                rect(L, cc, a, w, -40, h, rad)
                rect(L, shade_rgb(cc, 1.18), a, w, h - 8, h, rad)
                rect(L, shade_rgb(cc, 0.82), a + w * 0.32 / (TAU * rad), w * 0.36, -40, h - 8, rad)
    elif st == 'spires':
        L = layer(2500)
        ridge(L, mix_rgb(C['rock'], bot, 0.45), heights(120, 60))
        for _ in range(46):
            a = rnd()
            tri(L, mix_rgb(C['crystal'], fog, 0.45), a, 40 + rnd() * 60, 0, 200 + rnd() * 420, 2500)
        L = layer(1900)
        ridge(L, mix_rgb(C['rock2'], fog, 0.25), heights(60, 30))
        for _ in range(30):
            a = rnd()
            tri(L, mix_rgb(C['crystal'], fog, 0.25), a, 24 + rnd() * 30, 20, 90 + rnd() * 160, 1900)
    elif st == 'forestline':
        L = layer(2500)
        ridge(L, mix_rgb(mtn, bot, 0.55), heights(140, 60))
        L = layer(2000)
        hs = heights(60, 20)
        tc = mix_rgb(shade_rgb(hill, 0.8), fog, 0.3)
        ridge(L, tc, hs)
        for _ in range(240):
            a = rnd()
            h = h_at(hs, a)
            if rnd() < 0.6:
                tri(L, tc, a, 22 + rnd() * 16, h - 8, h + 30 + rnd() * 40, 2000)
            else:
                disc(L, tc, a, h + 14, 12 + rnd() * 12)
    elif st == 'flat':
        L = layer(2600)
        ridge(L, mix_rgb(mtn, bot, 0.6), heights(60, 25, (1, 2, 3, 5)))
        L = layer(2000)
        hs = heights(25, 10, (1, 3, 5, 7))
        ridge(L, mix_rgb(C['ground'], fog, 0.3), hs)
        if any(k == 'acacia' for k, _w in th['props']):
            tc = mix_rgb(shade_rgb(hill, 0.7), fog, 0.3)
            for _ in range(36):
                a = rnd()
                h = h_at(hs, a)
                rect(L, tc, a, 5, h - 4, h + 26, 2000)
                cap(L, tc, a, 70 + rnd() * 40, h + 24, 10, 2000, 6)
    elif st == 'clouds':
        L = layer(2600)
        cc = C['cloud']
        for i in range(170):
            a = i / 170.0 + rnd() * 0.004
            disc(L, mix_rgb(cc, bot, 0.35), a, 40 + rnd() * 110, 50 + rnd() * 80)
        for _ in range(7):
            a = rnd()
            h = 280 + rnd() * 320
            w = 120 + rnd() * 140
            tri(L, mix_rgb(shade_rgb(C['rock'], 0.8), bot, 0.3), a, w, h, h - w * 0.8, 2600)
            cap(L, mix_rgb(hill if hill[1] > hill[0] else (120, 200, 120), bot, 0.3), a, w, h, 16, 2600, 6)
        L = layer(2000)
        for i in range(120):
            a = i / 120.0 + rnd() * 0.005
            disc(L, mix_rgb(cc, fog, 0.15), a, 10 + rnd() * 50, 40 + rnd() * 50)
    elif st == 'ruins':
        L = layer(2500)
        ridge(L, mix_rgb(mtn, bot, 0.5), heights(120, 60))
        L = layer(2000)
        hs = heights(50, 25)
        ridge(L, mix_rgb(C['ground'], fog, 0.35), hs)
        cc = mix_rgb(C['rock'], fog, 0.3)
        for _ in range(26):
            a = rnd()
            h = h_at(hs, a)
            hh = 80 + rnd() * 120
            rect(L, cc, a, 18, h - 10, h + hh, 2000)
            if rnd() < 0.5:
                a2 = a + (40 + rnd() * 30) / (TAU * 2000)
                rect(L, cc, a2, 18, h - 10, h + hh, 2000)
                poly(L, cc, [(a - 12 / (TAU * 2000), h + hh), (a2 + 12 / (TAU * 2000), h + hh), (a2 + 12 / (TAU * 2000), h + hh + 14), (a - 12 / (TAU * 2000), h + hh + 14)])
    elif st == 'factory':
        L = layer(2500)
        ridge(L, mix_rgb(mtn, bot, 0.5), heights(100, 50))
        L = layer(2000)
        dc = mix_rgb(shade_rgb(mtn, 0.6), fog, 0.25)
        for _ in range(60):
            a = rnd()
            rect(L, dc, a, 80 + rnd() * 80, -30, 60 + rnd() * 140, 2000)
        smoke = mix_rgb((150, 145, 140), bot, 0.4)
        for _ in range(22):
            a = rnd()
            hh = 200 + rnd() * 250
            rect(L, shade_rgb(dc, 0.85), a, 20, 0, hh, 2000)
            rect(L, acc[0], a, 22, hh - 14, hh - 8, 2000)
            for j in range(3):
                disc(L, smoke, a + (j * 16 + rnd() * 10) / (TAU * 2000), hh + 20 + j * 26, 18 + j * 8)
    elif st == 'retro':
        L = layer(2800)
        a = rnd()
        disc(L, (255, 120, 70), a, 300, 300)
        disc(L, (255, 200, 90), a, 380, 220)
        for k in range(6):
            hb = 80 + k * 46
            rect(L, bot, a, 640, hb, hb + 10 + k * 2, 2800)
        L = layer(2400)
        hs = heights(170, 110, sharp=True)
        ridge(L, (40, 12, 64), hs)
        L.append(('line', acc[0], [(i / float(HZ_SEG), hs[i]) for i in range(HZ_SEG + 1)], 6))
        L = layer(1900)
        hs2 = heights(70, 40)
        ridge(L, (24, 8, 44), hs2)
        L.append(('line', acc[1], [(i / float(HZ_SEG), hs2[i]) for i in range(HZ_SEG + 1)], 5))
    elif st == 'bamboo':
        L = layer(2500)
        ridge(L, mix_rgb(mtn, bot, 0.5), heights(200, 100), snow_top)
        L = layer(2000)
        hs = heights(40, 15)
        tc = mix_rgb(shade_rgb(hill, 0.75), fog, 0.3)
        ridge(L, tc, hs)
        for _ in range(220):
            a = rnd()
            h = h_at(hs, a)
            hh = 200 + rnd() * 260
            rect(L, tc, a, 7, h - 6, h + hh, 2000)
            disc(L, tc, a + (rnd() - 0.5) * 0.004, h + hh - 10, 16 + rnd() * 14)
    elif st == 'mushrooms':
        L = layer(2500)
        ridge(L, mix_rgb(mtn, bot, 0.5), heights(120, 60))
        L = layer(2100)
        for i in range(28):
            a = rnd()
            hh = 120 + rnd() * 200
            w = 120 + rnd() * 120
            rect(L, mix_rgb(C['trunk'], fog, 0.3), a, w * 0.18, 0, hh, 2100)
            cap(L, mix_rgb(acc[i % len(acc)], fog, 0.3), a, w, hh - 6, w * 0.45, 2100)
        L = layer(1800)
        ridge(L, mix_rgb(hill, fog, 0.25), heights(40, 18))
    elif st == 'cliffs':
        L = layer(2500)
        ridge(L, mix_rgb(C['rock'], bot, 0.35), heights(380, 170, (1, 2, 3, 5, 8, 13, 21), sharp=True), snow_top)
        L = layer(1950)
        ridge(L, mix_rgb(C['water'], bot, 0.25), [18.0] * (HZ_SEG + 1))
        L = layer(1700)
        ridge(L, mix_rgb(C['rock2'], fog, 0.2), heights(30, 20, (1, 3, 7, 11)))
    elif st == 'toyblocks':
        L = layer(2500)
        ridge(L, mix_rgb(mtn, bot, 0.5), heights(140, 70, (1, 2, 3, 4)))
        L = layer(2000)
        for i in range(110):
            a = i / 110.0 + rnd() * 0.003
            w = 60 + rnd() * 70
            h = 40 + rnd() * 160
            c = mix_rgb(acc[int(rnd() * len(acc)) % len(acc)], fog, 0.25)
            rect(L, c, a, w, -20, h, 2000)
            if rnd() < 0.45:
                h2 = h + 30 + rnd() * 60
                rect(L, mix_rgb(acc[int(rnd() * len(acc)) % len(acc)], fog, 0.25), a, w * 0.6, h, h2, 2000)
    else:
        L = layer(2500)
        ridge(L, mix_rgb(mtn, bot, 0.5), heights(150, 80))
    return out


def biome_parts(map_id):
    """맵 번호 -> (생태계 0~39, 시간대 0~4, 색감 0~4)"""
    n = int(min(MAP_COUNT, max(1, int(map_id)))) - 1
    v = n // BIOME_FAMILIES
    return n % BIOME_FAMILIES, v % 5, (v // 5) % 5


def biome_map(family, ti, mi):
    """(생태계, 시간대, 색감) -> 맵 번호"""
    return ((int(ti) % 5) + 5 * (int(mi) % 5)) * BIOME_FAMILIES + (int(family) % BIOME_FAMILIES) + 1


def biome_part_names(map_id, lang='ko'):
    f, ti, mi = biome_parts(map_id)
    F = FAMILIES[f]
    T = TIMES[F['times'][ti]]
    M = MODS[F['mods'][mi]]
    if lang == 'ko':
        return F['ko'], T['ko'], (M[0] or '기본')
    return F['en'], T['en'], (M[1] or 'Classic')
