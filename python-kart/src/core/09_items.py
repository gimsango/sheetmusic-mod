
# ----------------------------------------------------------------------------
#  아이템전: 아이템 100종 · 아이템 상자 · 슬롯 3칸(키 1/2/3) · 투사체/함정 · 봇 · 네트워크 동기화
#  등급 0 = 흔함/방어용(선두에게 잘 나옴) ... 3 = 강력함(꼴찌에게 잘 나옴)
# ----------------------------------------------------------------------------
ITEM_SLOTS = 3

_IT = [
    # (키, 한글, 영문, 종류, 등급, 사용 횟수, 아이콘, 색1, 색2, 매개변수)
    # ---- 가속 (10) ----
    ('booster', '부스터', 'Booster', 'boost', 0, 1, 'flame', 0xff8a1a, 0xffe066, {'dur': 1.6, 'pow': 1.0}),
    ('booster3', '트리플 부스터', 'Triple Booster', 'boost', 1, 3, 'flame', 0xff4a1a, 0xffd23a, {'dur': 1.4, 'pow': 1.0}),
    ('goldbooster', '황금 부스터', 'Golden Booster', 'boost', 2, 7, 'flame', 0xffcc00, 0xfff4b0, {'dur': 1.0, 'pow': 1.05}),
    ('nitro', '니트로', 'Nitro', 'boost', 1, 1, 'canister', 0x29a3ff, 0xe8f6ff, {'dur': 2.6, 'pow': 1.15}),
    ('supernitro', '슈퍼 니트로', 'Super Nitro', 'boost', 2, 2, 'canister', 0x9b5bff, 0xe4d8ff, {'dur': 2.6, 'pow': 1.25}),
    ('jetengine', '제트 엔진', 'Jet Engine', 'boost', 1, 1, 'flame', 0x3ad0ff, 0xd8f6ff, {'dur': 3.2, 'pow': 0.85}),
    ('turbocan', '터보 캔', 'Turbo Can', 'boost', 0, 2, 'canister', 0x2ecc71, 0xeafff0, {'dur': 1.0, 'pow': 0.9}),
    ('afterburner', '애프터버너', 'Afterburner', 'boost', 2, 1, 'flame', 0xff3d3d, 0xffb199, {'dur': 4.0, 'pow': 1.1}),
    ('sugarrush', '슈가 러시', 'Sugar Rush', 'boost', 1, 4, 'candy', 0xff5fa8, 0xffffff, {'dur': 0.8, 'pow': 1.0}),
    ('chili', '불꽃 고추', 'Fire Chili', 'boost', 1, 1, 'chili', 0xe8261c, 0x3db846, {'dur': 2.2, 'pow': 1.3}),
    # ---- 엔진 강화 (3) ----
    ('v8', 'V8 엔진', 'V8 Engine', 'engine', 1, 1, 'gear', 0xa8b2c4, 0xffb020, {'dur': 6.0, 'cap': 9.0, 'acc': 1.4}),
    ('slipstream', '슬립스트림', 'Slipstream', 'engine', 0, 1, 'wind', 0x8ee3ff, 0xffffff, {'dur': 5.0, 'cap': 6.0, 'acc': 1.25}),
    ('hyperdrive', '하이퍼드라이브', 'Hyperdrive', 'engine', 2, 1, 'gear', 0x19e6ff, 0x2a3c9b, {'dur': 7.0, 'cap': 13.0, 'acc': 1.6}),
    # ---- 무적 (3) ----
    ('star', '무적 스타', 'Super Star', 'star', 2, 1, 'star', 0xffd400, 0xfff6a0, {'dur': 7.0}),
    ('rainbowstar', '무지개 스타', 'Rainbow Star', 'star', 3, 1, 'star', 0xff4fd8, 0x6af0ff, {'dur': 10.0}),
    ('ministar', '미니 스타', 'Mini Star', 'star', 1, 1, 'star', 0xffa94d, 0xffffff, {'dur': 3.5}),
    # ---- 방어 (5) ----
    ('shield', '방패', 'Shield', 'shield', 0, 1, 'shield', 0x3d8bff, 0xd6e8ff, {'n': 1, 'dur': 15.0}),
    ('steelshield', '강철 방패', 'Steel Shield', 'shield', 1, 1, 'shield', 0x9aa4b6, 0xf0f3f8, {'n': 2, 'dur': 20.0}),
    ('bubble', '버블 쉴드', 'Bubble Shield', 'shield', 0, 1, 'bubble', 0x7fdcff, 0xe8fbff, {'n': 1, 'dur': 10.0}),
    ('bubble3', '트리플 버블', 'Triple Bubble', 'shield', 1, 1, 'bubble', 0xb08bff, 0xf0e8ff, {'n': 3, 'dur': 25.0}),
    ('aegis', '이지스', 'Aegis', 'shield', 2, 1, 'shield', 0xffcc33, 0xfff3c4, {'n': 4, 'dur': 30.0}),
    # ---- 유령 (2) ----
    ('ghost', '유령', 'Ghost', 'ghost', 2, 1, 'ghost', 0xe8ecff, 0x6b5bd6, {'dur': 5.0, 'steal': 1}),
    ('phantom', '팬텀', 'Phantom', 'ghost', 1, 1, 'ghost', 0xb7f5d8, 0x1f8f6a, {'dur': 3.5, 'steal': 0}),
    # ---- 자동 질주 (3) ----
    ('rocket', '로켓', 'Rocket', 'rocket', 3, 1, 'rocket', 0xe04040, 0xf2f2f2, {'dur': 5.5, 'spd': 1.45}),
    ('bullettrain', '탄환 열차', 'Bullet Train', 'rocket', 3, 1, 'rocket', 0x3a3f4c, 0xffd400, {'dur': 8.0, 'spd': 1.5}),
    ('comet', '혜성', 'Comet', 'rocket', 2, 1, 'rocket', 0x6ad7ff, 0xffffff, {'dur': 3.5, 'spd': 1.4}),
    # ---- 점프 (3) ----
    ('spring', '스프링', 'Spring', 'hop', 0, 1, 'spring', 0x4fd66b, 0xe6ffe9, {'air': 0.8, 'boost': 0.6}),
    ('spring3', '트리플 스프링', 'Triple Spring', 'hop', 0, 3, 'spring', 0xffa43a, 0xfff1e0, {'air': 0.7, 'boost': 0.5}),
    ('superjump', '슈퍼 점프', 'Super Jump', 'hop', 1, 1, 'spring', 0x3a7bff, 0xffffff, {'air': 1.5, 'boost': 1.6}),
    # ---- 자석 (2) ----
    ('magnet', '자석', 'Magnet', 'magnet', 1, 1, 'magnet', 0xe8261c, 0xdfe3ea, {'dur': 6.0, 'range': 80.0}),
    ('supermagnet', '슈퍼 자석', 'Super Magnet', 'magnet', 2, 1, 'magnet', 0x9b5bff, 0xdfe3ea, {'dur': 9.0, 'range': 140.0}),
    # ---- 회복 (2) ----
    ('repair', '수리 키트', 'Repair Kit', 'cleanse', 0, 1, 'wrench', 0xb4bccb, 0xff8a1a, {'immune': 1.5}),
    ('potion', '회복 물약', 'Potion', 'cleanse', 0, 1, 'potion', 0xff4f7a, 0xffd0dc, {'immune': 3.0}),
    # ---- 타이어 (2) ----
    ('offroad', '오프로드 타이어', 'Offroad Tires', 'grip', 0, 1, 'tire', 0x4a4e58, 0xffb020, {'dur': 8.0}),
    ('spiketires', '스파이크 타이어', 'Spiked Tires', 'grip', 1, 1, 'tire', 0x4a4e58, 0x19e6ff, {'dur': 12.0}),
    # ---- 워프 (3) ----
    ('warp', '워프', 'Warp', 'warp', 2, 1, 'portal', 0x9b5bff, 0x19e6ff, {'dist': 60.0}),
    ('hyperwarp', '하이퍼 워프', 'Hyper Warp', 'warp', 3, 1, 'portal', 0xff3dbb, 0xffd400, {'dist': 130.0}),
    ('blink', '순간이동', 'Blink', 'warp', 1, 1, 'portal', 0x2ee6a8, 0xffffff, {'dist': 30.0}),
    # ---- 거대화 (2) ----
    ('megamushroom', '거대 버섯', 'Mega Mushroom', 'giant', 2, 1, 'mushroom', 0xe8261c, 0xffffff, {'dur': 8.0}),
    ('titan', '타이탄 모드', 'Titan Mode', 'giant', 3, 1, 'mushroom', 0x7a5bff, 0xffd400, {'dur': 11.0}),
    # ---- 코인 (3) ----
    ('coin', '코인', 'Coin', 'coin', 0, 1, 'coin', 0xffcc00, 0xfff2a8, {'n': 1}),
    ('coinbag', '코인 주머니', 'Coin Bag', 'coin', 0, 1, 'bag', 0xc98a3a, 0xffcc00, {'n': 3}),
    ('treasure', '보물 상자', 'Treasure Chest', 'coin', 1, 1, 'chest', 0xa8642e, 0xffcc00, {'n': 6}),
    # ---- 행운 (2) ----
    ('dice', '행운의 주사위', 'Lucky Dice', 'lucky', 0, 1, 'dice', 0xffffff, 0xe8261c, {'min': 1}),
    ('clover', '네잎클로버', 'Four-Leaf Clover', 'lucky', 1, 1, 'clover', 0x2ecc71, 0xc8ffd8, {'min': 2}),
    # ---- 자리 교환 / 도둑 (3) ----
    ('swap', '자리 바꾸기', 'Position Swap', 'swap', 3, 1, 'swap', 0x19b6ff, 0xffd400, {'range': 160.0}),
    ('thief', '도둑 장갑', 'Thief Glove', 'steal', 1, 1, 'hand', 0x8a7bff, 0xffffff, {'n': 1}),
    ('superthief', '슈퍼 도둑 장갑', 'Super Thief Glove', 'steal', 2, 1, 'hand', 0xff8a1a, 0xfff1e0, {'n': 2}),
    # ---- 직선 발사 (12) ----  (브레이크를 누른 채 쓰면 뒤로 던짐)
    ('missile', '미사일', 'Missile', 'shot', 0, 1, 'missile', 0x36c24a, 0xffffff, {'spd': 60.0, 'life': 6.0, 'bounce': 4, 'n': 1, 'fx': 'spin', 'r': 1.2}),
    ('missile3', '트리플 미사일', 'Triple Missile', 'shot', 1, 3, 'missile', 0x1f9e3a, 0xffd400, {'spd': 60.0, 'life': 6.0, 'bounce': 4, 'n': 1, 'fx': 'spin', 'r': 1.2}),
    ('spread', '부채꼴 미사일', 'Spread Missiles', 'shot', 1, 1, 'missile', 0x2bd6c4, 0xffffff, {'spd': 55.0, 'life': 4.0, 'bounce': 1, 'n': 3, 'fx': 'spin', 'r': 1.1}),
    ('cannonball', '대포알', 'Cannonball', 'shot', 1, 1, 'ball', 0x3a3f4c, 0x9aa4b6, {'spd': 45.0, 'life': 5.0, 'bounce': 0, 'n': 1, 'fx': 'launch', 'r': 1.8}),
    ('snowball', '눈덩이', 'Snowball', 'shot', 0, 2, 'ball', 0xf2f8ff, 0x8ecbff, {'spd': 50.0, 'life': 4.0, 'bounce': 1, 'n': 1, 'fx': 'slow', 'fxd': 3.0, 'k': 0.6, 'r': 1.3}),
    ('icearrow', '얼음 화살', 'Ice Arrow', 'shot', 1, 1, 'arrow', 0x8ee3ff, 0xffffff, {'spd': 90.0, 'life': 3.0, 'bounce': 0, 'n': 1, 'fx': 'freeze', 'fxd': 1.6, 'r': 1.1}),
    ('laser', '레이저', 'Laser Beam', 'shot', 1, 1, 'laser', 0xff2bd6, 0xffffff, {'spd': 230.0, 'life': 0.8, 'bounce': 0, 'n': 1, 'fx': 'spin', 'r': 1.4}),
    ('plasma', '플라스마 볼', 'Plasma Ball', 'shot', 2, 1, 'ball', 0x19e6ff, 0xffffff, {'spd': 70.0, 'life': 6.0, 'bounce': 6, 'n': 1, 'fx': 'stun', 'fxd': 2.2, 'r': 1.6}),
    ('waterballoon', '물풍선', 'Water Balloon', 'shot', 0, 1, 'balloon', 0x3d8bff, 0xbfe0ff, {'spd': 40.0, 'life': 3.0, 'bounce': 0, 'n': 1, 'fx': 'slide', 'fxd': 2.0, 'r': 1.6}),
    ('pie', '크림 파이', 'Cream Pie', 'shot', 0, 1, 'pie', 0xf7e6c4, 0xff5fa8, {'spd': 45.0, 'life': 3.0, 'bounce': 0, 'n': 1, 'fx': 'blind', 'fxd': 3.5, 'r': 1.4}),
    ('boomerang', '부메랑', 'Boomerang', 'boomerang', 1, 3, 'boomerang', 0xffa43a, 0x8a4a1a, {'spd': 50.0, 'life': 4.0, 'out': 1.3, 'fx': 'spin', 'r': 1.4}),
    ('shuriken', '수리검', 'Shuriken', 'shot', 1, 3, 'shuriken', 0xb4bccb, 0x3a3f4c, {'spd': 95.0, 'life': 2.5, 'bounce': 2, 'n': 1, 'fx': 'spin', 'r': 1.0}),
    # ---- 유도 (5) ----
    ('homing', '유도 미사일', 'Homing Missile', 'homing', 1, 1, 'target', 0xe8261c, 0xffffff, {'spd': 128.0, 'life': 9.0, 'fx': 'spin', 'r': 1.3}),
    ('homing3', '트리플 유도 미사일', 'Triple Homing', 'homing', 2, 3, 'target', 0xc0141e, 0xffd400, {'spd': 124.0, 'life': 9.0, 'fx': 'spin', 'r': 1.3}),
    ('bees', '꿀벌 떼', 'Bee Swarm', 'homing', 2, 1, 'bee', 0xffcc00, 0x2b2f3a, {'spd': 112.0, 'life': 10.0, 'fx': 'slow', 'fxd': 3.0, 'k': 0.55, 'r': 1.8}),
    ('drone', '추적 드론', 'Hunter Drone', 'homing', 2, 1, 'drone', 0xa8b2c4, 0x19e6ff, {'spd': 132.0, 'life': 12.0, 'fx': 'stun', 'fxd': 2.0, 'r': 1.4}),
    ('firebird', '불새', 'Firebird', 'homing', 2, 1, 'bird', 0xff5a1a, 0xffd400, {'spd': 138.0, 'life': 10.0, 'fx': 'launch', 'r': 1.6}),
    # ---- 1등 추적 (2) ----
    ('seeker', '1등 추적 미사일', 'Leader Seeker', 'seeker', 3, 1, 'wing', 0x2b5bff, 0xffffff, {'spd': 150.0, 'life': 30.0, 'fx': 'launch', 'r': 9.0}),
    ('skyhammer', '스카이 해머', 'Sky Hammer', 'seeker', 3, 1, 'hammer', 0xa8b2c4, 0xffd400, {'spd': 140.0, 'life': 30.0, 'fx': 'flat', 'fxd': 4.0, 'r': 7.0}),
    # ---- 폭탄 (6) ----
    ('bomb', '폭탄', 'Bomb', 'bomb', 1, 1, 'bomb', 0x2b2f3a, 0xff5a1a, {'dist': 32.0, 'fuse': 1.2, 'n': 1, 'fx': 'launch', 'r': 8.0}),
    ('megabomb', '메가 폭탄', 'Mega Bomb', 'bomb', 2, 1, 'bomb', 0xb5121b, 0xffd400, {'dist': 40.0, 'fuse': 1.6, 'n': 1, 'fx': 'launch', 'r': 14.0}),
    ('stinkbomb', '방귀 폭탄', 'Stink Bomb', 'bomb', 0, 1, 'bomb', 0x7fbf3a, 0xd8ff9a, {'dist': 28.0, 'fuse': 1.0, 'n': 1, 'fx': 'slow', 'fxd': 3.5, 'k': 0.6, 'r': 9.0}),
    ('inkbomb', '먹물 폭탄', 'Ink Bomb', 'bomb', 1, 1, 'bomb', 0x1b1b2a, 0x9b5bff, {'dist': 30.0, 'fuse': 1.0, 'n': 1, 'fx': 'blind', 'fxd': 4.0, 'r': 10.0}),
    ('clusterbomb', '집속탄', 'Cluster Bomb', 'bomb', 2, 1, 'bomb', 0x5a6b3a, 0xffcc00, {'dist': 34.0, 'fuse': 1.3, 'n': 3, 'fx': 'launch', 'r': 7.0}),
    ('freezebomb', '냉동 폭탄', 'Freeze Bomb', 'bomb', 2, 1, 'bomb', 0x8ee3ff, 0xffffff, {'dist': 32.0, 'fuse': 1.2, 'n': 1, 'fx': 'freeze', 'fxd': 2.0, 'r': 10.0}),
    # ---- 회오리 (3) ----
    ('tornado', '토네이도', 'Tornado', 'tornado', 2, 1, 'tornado', 0xc8d0e0, 0xffffff, {'spd': 95.0, 'life': 9.0, 'fx': 'spin', 'r': 3.2}),
    ('sandstorm', '모래 폭풍', 'Sandstorm', 'tornado', 1, 1, 'tornado', 0xd9b36b, 0xfff1d0, {'spd': 90.0, 'life': 10.0, 'fx': 'blind', 'fxd': 2.5, 'r': 4.0}),
    ('blizzard', '눈보라', 'Blizzard', 'tornado', 2, 1, 'snow', 0xdff3ff, 0x6ab8ff, {'spd': 92.0, 'life': 9.0, 'fx': 'freeze', 'fxd': 1.4, 'r': 4.5}),
    # ---- 충격파: 내 주변 (4) ----
    ('emp', 'EMP', 'EMP Blast', 'wave', 1, 1, 'wave', 0x19e6ff, 0x2a3c9b, {'r': 22.0, 'fx': 'stun', 'fxd': 2.2}),
    ('shockwave', '충격파', 'Shockwave', 'wave', 1, 1, 'wave', 0xffcc33, 0xffffff, {'r': 16.0, 'fx': 'spin'}),
    ('frostnova', '서리 폭발', 'Frost Nova', 'wave', 2, 1, 'snow', 0x8ee3ff, 0xffffff, {'r': 20.0, 'fx': 'freeze', 'fxd': 1.8}),
    ('sonicboom', '소닉 붐', 'Sonic Boom', 'wave', 2, 1, 'wave', 0xff5fa8, 0xffffff, {'r': 28.0, 'fx': 'launch', 'boost': 1.0}),
    # ---- 광역 (8) ----
    ('lightning', '번개', 'Lightning', 'zap', 3, 1, 'bolt', 0xffd400, 0xffffff, {'scope': 'all', 'fx': 'shrink', 'fxd': 6.0}),
    ('thundercloud', '먹구름', 'Thundercloud', 'zap', 2, 1, 'cloud', 0x6a7488, 0xffd400, {'scope': 'ahead1', 'fx': 'shrink', 'fxd': 5.0}),
    ('chainlightning', '연쇄 번개', 'Chain Lightning', 'zap', 2, 1, 'bolt', 0x7fdcff, 0xffffff, {'scope': 'ahead3', 'fx': 'shrink', 'fxd': 3.5}),
    ('inksquid', '먹물 오징어', 'Ink Squid', 'zap', 1, 1, 'squid', 0x9097b4, 0xe8ecff, {'scope': 'ahead', 'fx': 'blind', 'fxd': 4.5}),
    ('confusion', '혼란의 주문', 'Confusion Spell', 'zap', 2, 1, 'swirl', 0xb04bff, 0xffffff, {'scope': 'ahead', 'fx': 'reverse', 'fxd': 4.0}),
    ('lullaby', '자장가', 'Lullaby', 'zap', 2, 1, 'note', 0x6ab8ff, 0xffffff, {'scope': 'top3', 'fx': 'stun', 'fxd': 2.5}),
    ('meteor', '메테오', 'Meteor Shower', 'meteor', 3, 1, 'meteor', 0xff5a1a, 0x6a4a3a, {'n': 3, 'fall': 1.6, 'fx': 'launch', 'r': 5.0}),
    ('gravity', '중력 장치', 'Gravity Well', 'zap', 2, 1, 'ball', 0x4a3b8b, 0xc07bff, {'scope': 'ahead', 'fx': 'slow', 'fxd': 4.0, 'k': 0.55}),
    # ---- 함정: 뒤에 설치 (12) ----
    ('banana', '바나나', 'Banana', 'trap', 0, 1, 'banana', 0xffd400, 0x6b4a1a, {'shape': 'banana', 'fx': 'spin', 'r': 1.2, 'life': 60.0}),
    ('banana3', '트리플 바나나', 'Triple Banana', 'trap', 0, 3, 'banana', 0xffe14d, 0x3db846, {'shape': 'banana', 'fx': 'spin', 'r': 1.2, 'life': 60.0}),
    ('giantbanana', '대왕 바나나', 'Giant Banana', 'trap', 1, 1, 'banana', 0xffb800, 0xffffff, {'shape': 'banana', 'fx': 'spin', 'fxd': 1.8, 'r': 2.6, 'life': 60.0, 'big': 1}),
    ('oil', '기름 웅덩이', 'Oil Slick', 'trap', 0, 1, 'drop', 0x5c5677, 0x9b5bff, {'shape': 'oil', 'fx': 'slide', 'fxd': 2.2, 'r': 3.0, 'life': 14.0, 'persist': 1}),
    ('fakebox', '가짜 아이템 상자', 'Fake Item Box', 'trap', 0, 1, 'box', 0xe8261c, 0xffd400, {'shape': 'fakebox', 'fx': 'launch', 'r': 1.4, 'life': 60.0}),
    ('tacks', '압정', 'Tack Strip', 'trap', 0, 1, 'spikes', 0xb4bccb, 0x3a3f4c, {'shape': 'spikes', 'fx': 'slow', 'fxd': 3.0, 'k': 0.55, 'r': 2.4, 'life': 40.0}),
    ('mine', '지뢰', 'Land Mine', 'trap', 1, 1, 'mine', 0x5a6b3a, 0xe8261c, {'shape': 'mine', 'fx': 'launch', 'r': 3.2, 'blast': 7.0, 'life': 60.0}),
    ('glue', '끈끈이', 'Glue Puddle', 'trap', 0, 1, 'glue', 0xb04bff, 0xead6ff, {'shape': 'glue', 'fx': 'slow', 'fxd': 0.8, 'k': 0.45, 'r': 3.4, 'life': 12.0, 'persist': 1}),
    ('icepatch', '빙판', 'Ice Patch', 'trap', 0, 1, 'ice', 0xbfefff, 0xffffff, {'shape': 'ice', 'fx': 'slide', 'fxd': 1.8, 'r': 3.6, 'life': 14.0, 'persist': 1}),
    ('barricade', '바리케이드', 'Barricade', 'trap', 1, 1, 'wall', 0xff8a1a, 0xffffff, {'shape': 'wall', 'fx': 'bump', 'r': 2.2, 'life': 40.0}),
    ('reverseportal', '역방향 포털', 'Reverse Portal', 'trap', 1, 1, 'portal', 0xff3d3d, 0x3a3f4c, {'shape': 'portal', 'fx': 'warpback', 'fxd': 45.0, 'r': 1.8, 'life': 40.0}),
    ('minefield', '지뢰밭', 'Minefield', 'trap', 2, 1, 'mine', 0x4a4e58, 0xffcc00, {'shape': 'mine', 'fx': 'launch', 'r': 3.0, 'blast': 6.0, 'life': 45.0, 'n': 5}),
]
ITEMS = [dict(id=i, key=a[0], name=a[1], en=a[2], kind=a[3], tier=a[4], uses=a[5], icon=a[6], c1=hex_rgb(a[7]), c2=hex_rgb(a[8]), p=a[9])
         for i, a in enumerate(_IT)]
ITEM_COUNT = len(ITEMS)
ITEM_BY_KEY = dict((it['key'], it['id']) for it in ITEMS)
_TIER_N = [sum(1 for it in ITEMS if it['tier'] == t) for t in range(4)]

FX_NAMES = {'spin': ('스핀', 'spin'), 'launch': ('날려버림', 'launch'), 'shrink': ('축소', 'shrink'), 'flat': ('납작', 'flatten'),
            'slow': ('감속', 'slow'), 'slide': ('미끄러짐', 'slide'), 'freeze': ('빙결', 'freeze'), 'stun': ('엔진 정지', 'stun'),
            'reverse': ('조작 반전', 'reverse'), 'blind': ('시야 가림', 'blind'), 'bump': ('충돌', 'bump'), 'warpback': ('뒤로 이동', 'warp back'),
            'swap': ('자리 바뀜', 'swapped')}
_SCOPE = {'all': ('모든 상대', 'everyone'), 'ahead': ('앞의 모든 카트', 'all karts ahead'), 'ahead1': ('바로 앞 카트', 'the kart ahead'),
          'ahead3': ('앞의 3대', '3 karts ahead'), 'top3': ('1~3등', 'the top 3')}


def item_name(it, lang='ko'):
    i = ITEMS[it]
    return i['name'] if lang == 'ko' else i['en']


def fx_name(fx, lang='ko'):
    n = FX_NAMES.get(fx, (fx, fx))
    return n[0] if lang == 'ko' else n[1]


def item_desc(it, lang='ko'):
    i = ITEMS[it]
    k, p = i['kind'], i['p']
    ko = lang == 'ko'
    f = fx_name(p.get('fx', ''), lang)
    if k == 'boost':
        d = ('%g초 가속' % p['dur'], '%gs speed boost' % p['dur'])
    elif k == 'engine':
        d = ('%g초 엔진 강화 (최고속도 +%d)' % (p['dur'], p['cap']), '%gs engine power-up (+%d top speed)' % (p['dur'], p['cap']))
    elif k == 'star':
        d = ('%g초 무적 + 가속' % p['dur'], '%gs invincible + speed' % p['dur'])
    elif k == 'shield':
        d = ('공격 %d회 막기 (%g초)' % (p['n'], p['dur']), 'blocks %d hit(s) (%gs)' % (p['n'], p['dur']))
    elif k == 'ghost':
        d = ('%g초 투명' % p['dur'] + (' + 앞 차 아이템 훔치기' if p.get('steal') else ''), '%gs intangible' % p['dur'] + (' + steal' if p.get('steal') else ''))
    elif k == 'rocket':
        d = ('%g초 자동 질주 (무적, 속도 x%g)' % (p['dur'], p['spd']), '%gs autopilot (invincible, x%g speed)' % (p['dur'], p['spd']))
    elif k == 'hop':
        d = ('점프 %g초 (함정 회피) + 부스트' % p['air'], '%gs jump over traps + boost' % p['air'])
    elif k == 'magnet':
        d = ('%g초 동안 앞 차(%dm 안)에게 끌려감' % (p['dur'], p['range']), '%gs pull to the kart ahead (%dm)' % (p['dur'], p['range']))
    elif k == 'cleanse':
        d = ('상태이상 해제 + %g초 무적' % p['immune'], 'cure + %gs immunity' % p['immune'])
    elif k == 'grip':
        d = ('%g초 잔디 감속 없음 + 핸들링 향상' % p['dur'], '%gs no offroad slowdown + grip' % p['dur'])
    elif k == 'warp':
        d = ('%dm 앞으로 순간이동' % p['dist'], 'teleport %dm ahead' % p['dist'])
    elif k == 'giant':
        d = ('%g초 거대화 (부딪힌 차는 납작)' % p['dur'], '%gs giant (flattens karts)' % p['dur'])
    elif k == 'coin':
        d = ('코인 +%d (최고속도 상승)' % p['n'], '+%d coin(s), top speed up' % p['n'])
    elif k == 'lucky':
        d = ('더 좋은 아이템으로 변신', 'turns into a better item')
    elif k == 'swap':
        d = ('바로 앞 차와 자리 교환', 'swap places with the kart ahead')
    elif k == 'steal':
        d = ('앞 차 아이템 훔치기' + (' (%d대)' % p['n'] if p['n'] > 1 else ''), 'steal items ahead')
    elif k in ('shot', 'boomerang'):
        ko_, en_ = [], []
        if p.get('n', 1) > 1:
            ko_.append('%d갈래' % p['n'])
            en_.append('%d-way' % p['n'])
        if p['spd'] >= 200:
            ko_.append('초고속')
            en_.append('hyper-fast')
        if k == 'boomerang':
            ko_.append('던지면 돌아오는 부메랑')
            en_.append('returning throw')
        else:
            ko_.append('발사')
            en_.append('shot')
        if p.get('bounce'):
            ko_.append('(벽 %d번 튕김)' % p['bounce'])
            en_.append('(%d wall bounces)' % p['bounce'])
        d = (' '.join(ko_) + ' → ' + f, ' '.join(en_) + ' → ' + f)
    elif k == 'homing':
        wide = p['r'] >= 1.6
        d = ('앞 차를 끝까지 추적' + (' (넓은 범위)' if wide else '') + ' → ' + f, 'homes on the kart ahead' + (' (wide)' if wide else '') + ' → ' + f)
    elif k == 'seeker':
        d = ('1등을 추적해 반경 %dm 폭발 → %s' % (p['r'], f), 'hunts 1st place, %dm blast → %s' % (p['r'], f))
    elif k == 'bomb':
        many = ('%d개 ' % p['n']) if p.get('n', 1) > 1 else ''
        d = ('%s던지면 반경 %dm 폭발 → %s' % (many, p['r'], f), '%sthrow, %dm blast → %s' % (('%d x ' % p['n']) if many else '', p['r'], f))
    elif k == 'tornado':
        d = ('앞으로 달리는 회오리 → ' + f, 'roaming storm → ' + f)
    elif k == 'wave':
        d = ('내 주변 %dm → %s' % (p['r'], f), 'karts within %dm → %s' % (p['r'], f))
    elif k == 'zap':
        sc = _SCOPE.get(p['scope'], ('', ''))
        d = ('%s → %s' % (sc[0], f), '%s → %s' % (sc[1], f))
    elif k == 'meteor':
        d = ('1~%d등에게 메테오 → %s' % (p['n'], f), 'meteors on the top %d → %s' % (p['n'], f))
    elif k == 'trap':
        ko_, en_ = '뒤에 설치', 'drop behind'
        if p.get('n', 1) > 1:
            ko_, en_ = '뒤에 %d개 깔기' % p['n'], 'drop %d behind' % p['n']
        if p.get('big'):
            ko_, en_ = ko_ + ' (크기 2배)', en_ + ' (2x size)'
        if p.get('persist'):
            ko_, en_ = ko_ + ' (%d초 유지되는 웅덩이)' % p['life'], en_ + ' (%ds puddle)' % p['life']
        if p.get('shape') == 'mine':
            ko_, en_ = ko_ + ' (다가오면 반경 %dm 폭발)' % p.get('blast', 6), en_ + ' (proximity, %dm blast)' % p.get('blast', 6)
        if p.get('shape') == 'fakebox':
            ko_, en_ = '진짜처럼 보이는 상자 설치', 'drop a fake item box'
        d = (ko_ + ' → ' + f, en_ + ' → ' + f)
    else:
        d = ('', '')
    s = d[0] if ko else d[1]
    if i['uses'] > 1:
        s += ' (x%d)' % i['uses']
    return s


# ---------------------------------------------------------------------------
#  아이콘 (벡터): 좌표 -1..1, y 아래 방향.  두 프론트엔드가 같은 정의로 그린다.
#   ('c', x, y, r, 색)  원      ('e', x, y, rx, ry, 색)  타원      ('r', x, y, r, 두께, 색)  고리
#   ('p', ((x,y),...), 색)  다각형(중심에서 부채꼴로 채움 -> 별모양/볼록하게 작성)   ('l', ((x,y),...), 두께, 색)  굵은 선
#   색: 0 = 아이템 색1, 1 = 색2, 그 외 = ICON_COLS
# ---------------------------------------------------------------------------
ICON_COLS = {2: (255, 255, 255), 3: (28, 30, 40), 4: (255, 214, 40), 5: (232, 50, 40), 6: (120, 126, 140), 7: (205, 210, 220),
             8: (120, 72, 36), 9: (40, 150, 60), 10: (12, 12, 16), 11: (255, 140, 30)}


def _star_pts(n, ro, ri, rot=-math.pi / 2):
    return tuple((round(math.cos(rot + math.pi * i / n) * (ro if i % 2 == 0 else ri), 3),
                  round(math.sin(rot + math.pi * i / n) * (ro if i % 2 == 0 else ri), 3)) for i in range(n * 2))


def _ngon(n, r, rot=0.0, cx=0.0, cy=0.0):
    return tuple((round(cx + math.cos(rot + TAU * i / n) * r, 3), round(cy + math.sin(rot + TAU * i / n) * r, 3)) for i in range(n))


def _gear_teeth(n=8, r0=0.5, r1=0.92, hw=0.13, col=0):
    out = []
    for i in range(n):
        a = TAU * i / n
        c, s = math.cos(a), math.sin(a)
        out.append(('p', ((c * r0 - s * hw, s * r0 + c * hw), (c * r1 - s * hw, s * r1 + c * hw),
                          (c * r1 + s * hw, s * r1 - c * hw), (c * r0 + s * hw, s * r0 - c * hw)), col))
    return out


def _flake(col=0, col2=1):
    out = []
    for i in range(6):
        a = TAU * i / 6 - math.pi / 2
        c, s = math.cos(a), math.sin(a)
        out.append(('l', ((0.0, 0.0), (c * 0.9, s * 0.9)), 0.13, col))
        for sg in (-1, 1):
            b = a + sg * 0.75
            out.append(('l', ((c * 0.55, s * 0.55), (c * 0.55 + math.cos(b) * 0.28, s * 0.55 + math.sin(b) * 0.28)), 0.1, col))
    out.append(('c', 0.0, 0.0, 0.17, col2))
    return out


def _spiral(col=0):
    pts = []
    for i in range(26):
        t = i / 25.0
        a = t * 4.2 * math.pi
        r = 0.08 + 0.82 * t
        pts.append((round(math.cos(a) * r, 3), round(math.sin(a) * r, 3)))
    return [('l', tuple(pts), 0.15, col), ('c', 0.0, 0.0, 0.1, 1)]


ICONS = {
    'flame': [('p', ((0, -0.95), (0.45, -0.25), (0.62, 0.25), (0.4, 0.7), (0, 0.88), (-0.4, 0.7), (-0.62, 0.25), (-0.45, -0.25)), 0),
              ('p', ((0, -0.3), (0.28, 0.2), (0.25, 0.55), (0, 0.7), (-0.25, 0.55), (-0.28, 0.2)), 1)],
    'canister': [('p', ((-0.38, -0.45), (0.38, -0.45), (0.38, 0.85), (-0.38, 0.85)), 0), ('p', ((-0.2, -0.75), (0.2, -0.75), (0.2, -0.45), (-0.2, -0.45)), 6),
                 ('p', ((-0.28, -0.95), (0.28, -0.95), (0.28, -0.75), (-0.28, -0.75)), 1), ('p', ((-0.38, 0.05), (0.38, 0.05), (0.38, 0.3), (-0.38, 0.3)), 1),
                 ('l', ((-0.22, -0.3), (-0.22, -0.02)), 0.1, 2), ('l', ((-0.22, 0.4), (-0.22, 0.7)), 0.1, 2)],
    'candy': [('p', ((-0.42, 0), (-0.95, -0.42), (-0.95, 0.42)), 1), ('p', ((0.42, 0), (0.95, 0.42), (0.95, -0.42)), 1), ('c', 0, 0, 0.5, 0),
              ('l', ((-0.28, -0.3), (0.0, 0.42)), 0.12, 2), ('l', ((0.08, -0.45), (0.32, 0.2)), 0.12, 2)],
    'chili': [('l', ((-0.55, -0.4), (-0.25, 0.2), (0.2, 0.6), (0.72, 0.75)), 0.42, 0), ('p', ((-0.78, -0.58), (-0.36, -0.78), (-0.28, -0.46), (-0.62, -0.28)), 1),
              ('l', ((-0.57, -0.7), (-0.66, -0.97)), 0.11, 1), ('l', ((-0.45, -0.15), (-0.18, 0.28)), 0.08, 2)],
    'gear': [('c', 0, 0, 0.66, 0)] + _gear_teeth() + [('c', 0, 0, 0.27, 1)],
    'wind': [('l', ((-0.9, -0.35), (0.35, -0.35), (0.55, -0.5), (0.5, -0.72), (0.3, -0.75)), 0.15, 0),
             ('l', ((-0.9, 0.05), (0.65, 0.05), (0.85, -0.12), (0.8, -0.32)), 0.15, 1),
             ('l', ((-0.7, 0.45), (0.3, 0.45), (0.5, 0.6), (0.45, 0.8), (0.25, 0.82)), 0.15, 0)],
    'star': [('p', _star_pts(5, 0.98, 0.44), 0), ('p', _star_pts(5, 0.5, 0.22), 1), ('e', -0.15, -0.05, 0.06, 0.12, 3), ('e', 0.15, -0.05, 0.06, 0.12, 3)],
    'shield': [('p', ((0, -0.92), (0.76, -0.62), (0.68, 0.15), (0, 0.92), (-0.68, 0.15), (-0.76, -0.62)), 0),
               ('p', ((0, -0.62), (0.46, -0.42), (0.4, 0.1), (0, 0.6), (-0.4, 0.1), (-0.46, -0.42)), 1),
               ('l', ((0, -0.45), (0, 0.42)), 0.13, 0), ('l', ((-0.3, -0.1), (0.3, -0.1)), 0.13, 0)],
    'bubble': [('c', 0, 0, 0.8, 1), ('r', 0, 0, 0.8, 0.15, 0), ('e', -0.32, -0.38, 0.22, 0.11, 2), ('c', 0.36, 0.3, 0.08, 2)],
    'ghost': [('p', ((-0.62, 0.85), (-0.62, -0.2), (-0.45, -0.66), (0, -0.88), (0.45, -0.66), (0.62, -0.2), (0.62, 0.85), (0.31, 0.6), (0, 0.85), (-0.31, 0.6)), 0),
              ('e', -0.22, -0.2, 0.12, 0.18, 1), ('e', 0.22, -0.2, 0.12, 0.18, 1), ('e', 0, 0.25, 0.15, 0.1, 1)],
    'rocket': [('p', ((0, -0.95), (0.3, -0.55), (0.3, 0.45), (-0.3, 0.45), (-0.3, -0.55)), 0), ('p', ((0.3, 0.05), (0.64, 0.5), (0.64, 0.75), (0.3, 0.45)), 1),
               ('p', ((-0.3, 0.05), (-0.3, 0.45), (-0.64, 0.75), (-0.64, 0.5)), 1), ('c', 0, -0.25, 0.15, 2), ('c', 0, -0.25, 0.08, 3),
               ('p', ((-0.18, 0.45), (0.18, 0.45), (0, 0.97)), 4)],
    'spring': [('l', ((-0.55, 0.8), (0.55, 0.8)), 0.17, 1), ('l', ((-0.45, 0.58), (0.45, 0.38), (-0.45, 0.16), (0.45, -0.06), (-0.45, -0.28), (0.45, -0.48)), 0.14, 0),
               ('l', ((-0.55, -0.7), (0.55, -0.7)), 0.17, 1)],
    'magnet': [('l', ((-0.5, -0.66), (-0.5, 0.15), (-0.35, 0.55), (0, 0.7), (0.35, 0.55), (0.5, 0.15), (0.5, -0.66)), 0.34, 0),
               ('p', ((-0.68, -0.96), (-0.32, -0.96), (-0.32, -0.6), (-0.68, -0.6)), 1), ('p', ((0.32, -0.96), (0.68, -0.96), (0.68, -0.6), (0.32, -0.6)), 1)],
    'wrench': [('l', ((-0.58, 0.62), (0.28, -0.24)), 0.28, 0), ('c', 0.42, -0.42, 0.38, 0), ('c', 0.6, -0.6, 0.2, 3), ('c', -0.58, 0.62, 0.17, 1)],
    'potion': [('c', 0, 0.3, 0.62, 0), ('p', ((-0.18, -0.75), (0.18, -0.75), (0.18, -0.22), (-0.18, -0.22)), 7),
               ('p', ((-0.26, -0.96), (0.26, -0.96), (0.26, -0.74), (-0.26, -0.74)), 8), ('e', -0.22, 0.12, 0.12, 0.22, 2), ('c', 0.16, 0.48, 0.1, 1),
               ('c', -0.05, 0.62, 0.06, 1)],
    'tire': [('c', 0, 0, 0.92, 0), ('r', 0, 0, 0.8, 0.07, 6), ('c', 0, 0, 0.5, 1), ('c', 0, 0, 0.18, 3)],
    'portal': [('r', 0, 0, 0.8, 0.2, 0), ('r', 0, 0, 0.5, 0.15, 1), ('c', 0, 0, 0.24, 2)],
    'mushroom': [('p', ((-0.95, 0.05), (-0.8, -0.45), (-0.4, -0.82), (0, -0.92), (0.4, -0.82), (0.8, -0.45), (0.95, 0.05)), 0),
                 ('c', -0.45, -0.38, 0.18, 1), ('c', 0.42, -0.44, 0.15, 1), ('c', 0, -0.72, 0.13, 1),
                 ('p', ((-0.4, 0.05), (0.4, 0.05), (0.35, 0.86), (-0.35, 0.86)), 7), ('e', -0.14, 0.4, 0.06, 0.12, 3), ('e', 0.14, 0.4, 0.06, 0.12, 3)],
    'coin': [('c', 0, 0, 0.88, 0), ('r', 0, 0, 0.66, 0.1, 1), ('p', ((-0.13, -0.42), (0.13, -0.42), (0.13, 0.42), (-0.13, 0.42)), 1)],
    'bag': [('c', 0, 0.28, 0.64, 0), ('p', ((-0.24, -0.32), (0.24, -0.32), (0.42, -0.78), (-0.42, -0.78)), 0), ('l', ((-0.32, -0.32), (0.32, -0.32)), 0.11, 1),
            ('c', 0, 0.3, 0.27, 1), ('l', ((0, 0.12), (0, 0.48)), 0.08, 0)],
    'chest': [('p', ((-0.86, -0.1), (0.86, -0.1), (0.86, 0.76), (-0.86, 0.76)), 0),
              ('p', ((-0.86, -0.1), (-0.76, -0.55), (-0.4, -0.76), (0.4, -0.76), (0.76, -0.55), (0.86, -0.1)), 0),
              ('l', ((-0.86, -0.1), (0.86, -0.1)), 0.12, 1), ('l', ((-0.5, -0.7), (-0.5, 0.76)), 0.11, 1), ('l', ((0.5, -0.7), (0.5, 0.76)), 0.11, 1),
              ('p', ((-0.13, -0.26), (0.13, -0.26), (0.13, 0.2), (-0.13, 0.2)), 1)],
    'dice': [('p', ((-0.78, -0.78), (0.78, -0.78), (0.78, 0.78), (-0.78, 0.78)), 0), ('c', -0.4, -0.4, 0.14, 1), ('c', 0, 0, 0.14, 1),
             ('c', 0.4, 0.4, 0.14, 1), ('c', 0.4, -0.4, 0.14, 1), ('c', -0.4, 0.4, 0.14, 1)],
    'clover': [('l', ((0.05, 0.1), (0.42, 0.95)), 0.13, 9), ('c', -0.33, -0.33, 0.34, 0), ('c', 0.33, -0.33, 0.34, 0), ('c', -0.33, 0.33, 0.34, 0),
               ('c', 0.33, 0.33, 0.34, 0), ('c', 0, 0, 0.14, 1)],
    'swap': [('l', ((-0.72, -0.32), (0.5, -0.32)), 0.19, 0), ('p', ((0.38, -0.66), (0.94, -0.32), (0.38, 0.02)), 0),
             ('l', ((0.72, 0.36), (-0.5, 0.36)), 0.19, 1), ('p', ((-0.38, 0.02), (-0.94, 0.36), (-0.38, 0.7)), 1)],
    'hand': [('c', 0, 0.2, 0.55, 0), ('e', -0.42, -0.4, 0.14, 0.3, 0), ('e', -0.14, -0.54, 0.14, 0.33, 0), ('e', 0.14, -0.54, 0.14, 0.33, 0),
             ('e', 0.42, -0.4, 0.14, 0.3, 0), ('e', -0.62, 0.16, 0.3, 0.14, 0), ('p', ((-0.42, 0.62), (0.42, 0.62), (0.42, 0.96), (-0.42, 0.96)), 1)],
    'missile': [('p', ((0.95, 0), (0.5, -0.3), (-0.55, -0.3), (-0.55, 0.3), (0.5, 0.3)), 0), ('p', ((-0.25, -0.3), (-0.82, -0.64), (-0.6, -0.3)), 1),
                ('p', ((-0.25, 0.3), (-0.6, 0.3), (-0.82, 0.64)), 1), ('l', ((0.22, -0.3), (0.22, 0.3)), 0.11, 1), ('p', ((-0.55, -0.16), (-0.97, 0), (-0.55, 0.16)), 4)],
    'ball': [('c', 0, 0, 0.8, 0), ('r', 0, 0, 0.8, 0.09, 1), ('e', -0.28, -0.32, 0.24, 0.14, 2)],
    'arrow': [('l', ((-0.82, 0.82), (0.42, -0.42)), 0.14, 1), ('p', ((0.92, -0.92), (0.2, -0.64), (0.64, -0.2)), 0),
              ('l', ((-0.72, 0.72), (-0.95, 0.5)), 0.11, 0), ('l', ((-0.72, 0.72), (-0.5, 0.95)), 0.11, 0)],
    'laser': [('p', ((-0.96, 0.18), (-0.38, 0.18), (-0.38, 0.58), (-0.96, 0.58)), 6), ('l', ((-0.4, 0.3), (0.95, -0.62)), 0.26, 0),
              ('l', ((-0.4, 0.3), (0.95, -0.62)), 0.09, 2)],
    'balloon': [('l', ((0, 0.72), (0.1, 0.97)), 0.07, 7), ('c', 0, -0.1, 0.74, 0), ('p', ((-0.13, 0.6), (0.13, 0.6), (0, 0.78)), 0),
                ('e', -0.28, -0.38, 0.17, 0.11, 2)],
    'pie': [('p', ((-0.92, 0.08), (0.92, 0.08), (0.72, 0.6), (-0.72, 0.6)), 8), ('e', 0, 0.04, 0.92, 0.42, 0), ('c', 0, -0.2, 0.15, 1)],
    'boomerang': [('l', ((-0.76, 0.6), (-0.1, -0.56), (0.76, 0.6)), 0.31, 0), ('l', ((-0.76, 0.6), (-0.1, -0.56), (0.76, 0.6)), 0.08, 1)],
    'shuriken': [('p', _star_pts(4, 0.97, 0.3, -math.pi / 4), 0), ('c', 0, 0, 0.17, 1)],
    'target': [('r', 0, 0, 0.74, 0.15, 0), ('r', 0, 0, 0.38, 0.13, 0), ('l', ((0, -0.97), (0, -0.52)), 0.13, 1), ('l', ((0, 0.52), (0, 0.97)), 0.13, 1),
               ('l', ((-0.97, 0), (-0.52, 0)), 0.13, 1), ('l', ((0.52, 0), (0.97, 0)), 0.13, 1), ('c', 0, 0, 0.13, 1)],
    'bee': [('e', -0.26, -0.46, 0.26, 0.18, 2), ('e', 0.26, -0.46, 0.26, 0.18, 2), ('e', 0, 0.1, 0.58, 0.42, 0),
            ('l', ((-0.14, -0.26), (-0.14, 0.46)), 0.15, 1), ('l', ((0.2, -0.26), (0.2, 0.46)), 0.15, 1), ('p', ((0.55, 0.02), (0.92, 0.1), (0.55, 0.22)), 1)],
    'drone': [('l', ((-0.7, -0.6), (0.7, 0.6)), 0.11, 6), ('l', ((0.7, -0.6), (-0.7, 0.6)), 0.11, 6),
              ('p', ((-0.32, -0.22), (0.32, -0.22), (0.32, 0.26), (-0.32, 0.26)), 0),
              ('e', -0.7, -0.64, 0.26, 0.08, 1), ('e', 0.7, -0.64, 0.26, 0.08, 1), ('e', -0.7, 0.58, 0.26, 0.08, 1), ('e', 0.7, 0.58, 0.26, 0.08, 1),
              ('c', 0, 0.02, 0.11, 1)],
    'bird': [('p', ((-0.95, -0.55), (-0.05, 0.02), (-0.12, 0.32), (-0.55, 0.18)), 0), ('p', ((0.95, -0.55), (0.55, 0.18), (0.12, 0.32), (0.05, 0.02)), 0),
             ('e', 0, 0.2, 0.17, 0.42, 1), ('c', 0, -0.2, 0.15, 1), ('p', ((-0.2, 0.55), (0.2, 0.55), (0, 0.95)), 0)],
    'wing': [('p', ((-0.5, 0.02), (-0.96, -0.55), (-0.84, -0.1)), 1), ('p', ((-0.5, 0.1), (-0.86, -0.04), (-0.96, 0.3)), 1),
             ('p', ((0.5, 0.02), (0.84, -0.1), (0.96, -0.55)), 1), ('p', ((0.5, 0.1), (0.96, 0.3), (0.86, -0.04)), 1),
             ('c', 0, 0.12, 0.56, 0), ('r', 0, 0.12, 0.56, 0.1, 2), ('c', 0, 0.12, 0.2, 2)],
    'hammer': [('l', ((-0.62, 0.86), (0.22, -0.08)), 0.2, 8), ('p', ((-0.06, -0.76), (0.86, 0.14), (0.56, 0.46), (-0.36, -0.44)), 0),
               ('p', ((0.12, -0.6), (0.7, -0.02), (0.6, 0.08), (0.02, -0.5)), 1)],
    'bomb': [('c', 0, 0.16, 0.72, 0), ('e', -0.26, -0.08, 0.17, 0.11, 7), ('p', ((-0.15, -0.72), (0.15, -0.72), (0.15, -0.5), (-0.15, -0.5)), 6),
             ('l', ((0, -0.72), (0.2, -0.86), (0.45, -0.86)), 0.08, 8), ('c', 0.52, -0.86, 0.13, 1)],
    'tornado': [('e', 0, -0.66, 0.86, 0.18, 0), ('e', 0.1, -0.3, 0.62, 0.15, 0), ('e', -0.06, 0.05, 0.46, 0.13, 1), ('e', 0.08, 0.38, 0.3, 0.11, 0),
                ('e', 0, 0.68, 0.17, 0.09, 1)],
    'snow': _flake(),
    'wave': [('r', 0, 0, 0.84, 0.11, 0), ('r', 0, 0, 0.57, 0.12, 1), ('r', 0, 0, 0.3, 0.14, 0), ('c', 0, 0, 0.1, 2)],
    'bolt': [('l', ((0.45, -0.95), (-0.16, 0.0), (0.26, 0.0), (-0.36, 0.96)), 0.24, 0), ('l', ((0.42, -0.85), (-0.12, 0.0), (0.24, 0.0), (-0.3, 0.85)), 0.07, 1)],
    'cloud': [('l', ((0.12, 0.26), (-0.1, 0.6), (0.16, 0.6), (-0.06, 0.96)), 0.13, 1), ('c', -0.4, -0.1, 0.36, 0), ('c', 0.05, -0.32, 0.46, 0),
              ('c', 0.46, -0.06, 0.35, 0), ('p', ((-0.76, -0.06), (0.8, -0.06), (0.8, 0.26), (-0.76, 0.26)), 0)],
    'squid': [('l', ((-0.35, 0.25), (-0.46, 0.86)), 0.13, 0), ('l', ((-0.12, 0.25), (-0.15, 0.93)), 0.13, 0), ('l', ((0.12, 0.25), (0.15, 0.93)), 0.13, 0),
              ('l', ((0.35, 0.25), (0.46, 0.86)), 0.13, 0), ('p', ((0, -0.96), (0.43, -0.4), (0.43, 0.26), (-0.43, 0.26), (-0.43, -0.4)), 0),
              ('c', -0.17, -0.05, 0.12, 1), ('c', 0.17, -0.05, 0.12, 1), ('c', -0.15, -0.05, 0.055, 3), ('c', 0.19, -0.05, 0.055, 3)],
    'swirl': _spiral(),
    'note': [('e', -0.3, 0.6, 0.29, 0.21, 0), ('e', 0.45, 0.4, 0.29, 0.21, 0), ('l', ((-0.04, 0.6), (-0.04, -0.66)), 0.13, 0),
             ('l', ((0.71, 0.4), (0.71, -0.86)), 0.13, 0), ('p', ((-0.1, -0.7), (0.77, -0.92), (0.77, -0.6), (-0.1, -0.4)), 0)],
    'meteor': [('l', ((0.95, -0.95), (0.08, -0.08)), 0.5, 4), ('l', ((0.92, -0.6), (0.1, -0.1)), 0.2, 11), ('l', ((0.6, -0.92), (0.1, -0.1)), 0.2, 11),
               ('c', -0.2, 0.2, 0.56, 0), ('c', -0.36, 0.06, 0.13, 1), ('c', -0.04, 0.42, 0.1, 1), ('c', -0.38, 0.4, 0.07, 1)],
    'banana': [('l', ((-0.6, -0.68), (-0.62, -0.1), (-0.4, 0.4), (0.05, 0.72), (0.62, 0.76)), 0.34, 0), ('l', ((-0.6, -0.68), (-0.62, -0.88)), 0.14, 1),
               ('l', ((-0.45, -0.25), (-0.3, 0.26), (0.06, 0.5)), 0.07, 2)],
    'drop': [('p', ((0, -0.93), (0.5, -0.1), (0.6, 0.3), (0.42, 0.7), (0, 0.86), (-0.42, 0.7), (-0.6, 0.3), (-0.5, -0.1)), 0), ('e', -0.22, 0.2, 0.1, 0.18, 1)],
    'box': [('p', ((-0.82, -0.82), (0.82, -0.82), (0.82, 0.82), (-0.82, 0.82)), 0), ('p', ((-0.64, -0.64), (0.64, -0.64), (0.64, 0.64), (-0.64, 0.64)), 1),
            ('l', ((-0.26, -0.3), (-0.15, -0.5), (0.15, -0.5), (0.27, -0.3), (0.0, -0.04), (0.0, 0.16)), 0.15, 0), ('c', 0, 0.42, 0.1, 0)],
    'spikes': [('p', ((-0.92, 0.6), (0.92, 0.6), (0.92, 0.86), (-0.92, 0.86)), 1)] +
              [('p', ((-0.92 + k * 0.46, 0.6), (-0.46 + k * 0.46, 0.6), (-0.69 + k * 0.46, -0.52)), 0) for k in range(4)],
    'mine': [('e', 0, 0.3, 0.86, 0.4, 0), ('e', 0, 0.16, 0.6, 0.25, 6), ('c', 0, 0.04, 0.19, 1), ('e', -0.06, -0.02, 0.06, 0.04, 2)],
    'glue': [('c', -0.35, 0.25, 0.46, 0), ('c', 0.3, 0.3, 0.5, 0), ('c', 0, -0.1, 0.42, 0), ('c', 0.56, -0.26, 0.18, 0), ('c', -0.62, -0.32, 0.12, 0),
             ('e', -0.25, 0.0, 0.13, 0.08, 1)],
    'ice': [('p', _ngon(6, 0.9, -math.pi / 2), 0), ('p', _ngon(6, 0.52, -math.pi / 2), 1)] +
           [('l', ((0, 0), (round(math.cos(-math.pi / 2 + TAU * i / 6) * 0.86, 3), round(math.sin(-math.pi / 2 + TAU * i / 6) * 0.86, 3))), 0.06, 2) for i in range(6)],
    'wall': [('l', ((-0.6, 0.2), (-0.6, 0.92)), 0.15, 6), ('l', ((0.6, 0.2), (0.6, 0.92)), 0.15, 6),
             ('p', ((-0.92, -0.45), (0.92, -0.45), (0.92, 0.2), (-0.92, 0.2)), 0)] +
            [('p', ((-0.92 + k * 0.5, -0.45), (-0.7 + k * 0.5, -0.45), (-0.5 + k * 0.5, 0.2), (-0.72 + k * 0.5, 0.2)), 1) for k in range(4)] +
            [('c', -0.6, -0.62, 0.13, 4), ('c', 0.6, -0.62, 0.13, 4)],
}


def icon_color(item, ci):
    if ci == 0:
        return item['c1']
    if ci == 1:
        return item['c2']
    return ICON_COLS.get(ci, (255, 255, 255))


# ---------------------------------------------------------------------------
#  투사체/함정 하나
# ---------------------------------------------------------------------------
class Ent(object):
    __slots__ = ('eid', 'kind', 'item', 'owner', 'x', 'y', 'z', 'vx', 'vy', 'vz', 'h', 'hint', 'd', 'life', 'age', 'r',
                 'target', 'bounce', 'state', 'dead', 'hits', 'gy', 'prog')

    def __init__(self):
        self.hits = {}
        self.dead = False
        self.state = 0
        self.age = 0.0
        self.x = self.y = self.z = 0.0
        self.vx = self.vy = self.vz = 0.0
        self.target = None
        self.bounce = 0
        self.hint = -1
        self.h = 0.0
        self.d = 0.0
        self.gy = 0.0
        self.prog = 0.0
        self.life = 4.0
        self.r = 1.2


# 주인이 자기 투사체/함정에 바로 맞지 않는 시간
_ARM = {'shot': 0.45, 'boomerang': 99.0, 'homing': 99.0, 'tornado': 99.0, 'trap': 1.0, 'bomb': 99.0}


class ItemSystem(object):
    """아이템 상자 + 슬롯 + 사용 + 투사체/함정 + 봇 판단 + 네트워크.
    권한: 각 기기는 자기가 시뮬레이션하는 카트(내 카트 + 방장이면 봇)에 대해서만 맞았는지 판정하고, 그 결과를 알린다."""
    BOX_RESPAWN = 2.6
    ROLL_TIME = 0.9

    def __init__(self, race):
        self.race = race
        self.track = race.track
        self.q = Q()
        self.rng = Rng((int(time.time() * 1000) ^ (id(self) & 0xFFFF)) & 0xFFFFFFFF)
        self.ents = []
        self.seq = 0
        self.vfx = []
        self.boxes = []
        self.t = 0.0
        self._make_boxes()

    # ---- 상자 ----------------------------------------------------------------------
    def _make_boxes(self):
        tr = self.track
        N = tr.N
        rows = int(clamp(tr.length / 420.0, 4, 8))
        r = Rng(tr.info['seed'] ^ 0x1717)
        pads = [p['idx'] for p in tr.pads]
        for k in range(rows):
            idx = int(((k + 0.35 + r() * 0.3) / rows) * N)
            idx = max(20, min(N - 14, idx))
            for _ in range(4):
                if any(abs(idx - pi) < 7 for pi in pads):
                    idx = max(20, min(N - 14, idx + 9))
                else:
                    break
            for j in range(4):
                d = tr.hw * (-0.66 + 0.44 * j)
                x, y, z, h = tr.pose_at(idx, d)
                self.boxes.append({'x': x, 'y': y + 1.15, 'z': z, 'idx': idx, 't': 0.0, 'ph': r() * TAU, 'h': h})

    def _boxes_step(self, dt):
        for b in self.boxes:
            if b['t'] > 0:
                b['t'] = max(0.0, b['t'] - dt)
        race = self.race
        if race.phase != 'run':
            return
        N = self.track.N
        for rc in race.racers:
            if rc.sim is None or rc.finished:
                continue
            for i, b in enumerate(self.boxes):
                if b['t'] > 0:
                    continue
                di = (rc.idx - b['idx']) % N
                if 3 < di < N - 3:
                    continue
                dx = rc.x - b['x']
                dz = rc.z - b['z']
                if dx * dx + dz * dz < 4.4 * rc.scale:
                    b['t'] = self.BOX_RESPAWN
                    self.vfx.append(('box', b['x'], b['y'], b['z']))
                    self._send({'t': 'ib', 'b': i})
                    self.give(rc, self.roll_item(rc))

    def roll_item(self, rc, min_tier=0, lucky_ok=True):
        rank = self.race.ranking()
        n = len(rank)
        pos = rank.index(rc) if rc in rank else 0
        f = pos / float(n - 1) if n > 1 else 0.5
        tw = [1.25 - 0.95 * f, 0.75 + 0.35 * f, 0.08 + 0.95 * f, max(0.0, f - 0.4) * 1.5]
        for t in range(min_tier):
            tw[t] = 0.0
        if sum(tw) <= 0:
            tw[3] = 1.0
        total = 0.0
        ws = []
        for it in ITEMS:
            w = tw[it['tier']] / _TIER_N[it['tier']]
            if not lucky_ok and it['kind'] == 'lucky':
                w = 0.0
            ws.append(w)
            total += w
        x = self.rng() * total
        for i, w in enumerate(ws):
            x -= w
            if x <= 0 and w > 0:
                return i
        return ITEM_BY_KEY['booster']

    def give(self, rc, it, uses=None, roll=None):
        """빈 슬롯에 아이템 넣기 (가득 차 있으면 False)"""
        for s in range(ITEM_SLOTS):
            if rc.items[s] is None:
                rc.items[s] = it
                rc.uses[s] = ITEMS[it]['uses'] if uses is None else max(1, int(uses))
                rc.roll[s] = self.ROLL_TIME if roll is None else roll
                rc.hold[s] = 0.0
                if rc.kind == 'local':
                    self.race.ev(('item', 'roll', it, s))
                return True
        return False

    # ---- 사용 ----------------------------------------------------------------------
    def use(self, rc, slot, back=False):
        race = self.race
        if rc is None or rc.sim is None or race.phase != 'run' or rc.finished:
            return False
        if not (0 <= slot < ITEM_SLOTS):
            return False
        it = rc.items[slot]
        if it is None or rc.roll[slot] > 0:
            return False
        item = ITEMS[it]
        if item['kind'] == 'lucky':
            new = self.roll_item(rc, item['p']['min'], False)
            rc.items[slot] = new
            rc.uses[slot] = ITEMS[new]['uses']
            rc.roll[slot] = self.ROLL_TIME * 0.8
            rc.hold[slot] = 0.0
            self._ev(rc, ('item', 'use', it))
            self._ev(rc, ('item', 'roll', new, slot))
            return True
        self._activate(rc, it, back)
        rc.uses[slot] -= 1
        if rc.uses[slot] <= 0:
            rc.items[slot] = None
            rc.uses[slot] = 0
        self._ev(rc, ('item', 'use', it))
        return True

    def _ev(self, rc, ev):
        if rc is not None and rc.kind == 'local':
            self.race.ev(ev)

    def _send(self, msg):
        race = self.race
        if race.multi and race.net is not None:
            race.net.send(msg)

    def _ahead(self, rc, maxm=None):
        """진행 거리 기준으로 나보다 앞에 있는 카트들 (가까운 순)"""
        ds = self.track.ds
        out = []
        for o in self.race.racers:
            if o is rc or o.finished:
                continue
            gap = (o.total - rc.total) * ds
            if gap > 0 and (maxm is None or gap <= maxm):
                out.append((gap, o))
        out.sort(key=lambda t: t[0])
        return [o for _, o in out]

    def _activate(self, rc, it, back=False):
        item = ITEMS[it]
        k = item['kind']
        p = item['p']
        s = rc.sim
        if k == 'boost':
            s.boost_t = max(s.boost_t, p['dur'])
            s.boost_pow = p['pow']
            self.vfx.append(('boost', rc.id))
        elif k == 'engine':
            s.engine_t = p['dur']
            s.engine_cap = p['cap']
            s.engine_acc = p['acc']
        elif k == 'star':
            s.cure()
            s.star_t = max(s.star_t, p['dur'])
        elif k == 'shield':
            s.shield_n = max(s.shield_n, p['n'])
            s.shield_t = max(s.shield_t, p['dur'])
        elif k == 'ghost':
            s.ghost_t = p['dur']
            if p.get('steal'):
                self._steal(rc, 1, it)
        elif k == 'rocket':
            s.cure()
            s.auto_t = p['dur']
            s.auto_spd = p['spd']
        elif k == 'hop':
            s.hop_t = s.hop_dur = p['air']
            s.boost_t = max(s.boost_t, p['boost'])
            s.boost_pow = 0.8
        elif k == 'magnet':
            s.magnet_t = p['dur']
            s.magnet_range = p['range']
        elif k == 'cleanse':
            s.cure()
            s.immune_t = max(s.immune_t, p['immune'])
            s.boost_t = max(s.boost_t, 0.5)
        elif k == 'grip':
            s.grip_t = p['dur']
        elif k == 'warp':
            self._warp(rc, p['dist'])
            s.immune_t = max(s.immune_t, 0.8)
        elif k == 'giant':
            s.shrink_t = 0.0
            s.giant_t = p['dur']
        elif k == 'coin':
            s.coins = min(10, s.coins + p['n'])
            s.boost_t = max(s.boost_t, 0.4)
        elif k == 'swap':
            self._swap(rc, p['range'], it)
        elif k == 'steal':
            self._steal(rc, p['n'], it)
        elif k == 'wave':
            rr = p['r'] * p['r']
            tg = [o for o in self.race.racers if o is not rc and not o.finished and (o.x - rc.x) ** 2 + (o.z - rc.z) ** 2 < rr]
            if p.get('boost'):
                s.boost_t = max(s.boost_t, p['boost'])
            self._area(rc, it, tg)
        elif k == 'zap':
            sc = p['scope']
            if sc == 'all':
                tg = [o for o in self.race.racers if o is not rc and not o.finished]
            elif sc == 'top3':
                tg = [o for o in self.race.ranking() if o is not rc and not o.finished][:3]
            else:
                ah = self._ahead(rc)
                tg = ah[:1] if sc == 'ahead1' else (ah[:3] if sc == 'ahead3' else ah)
            self._area(rc, it, tg)
        else:
            self._throw(rc, it, back)

    def _warp(self, rc, dist):
        s = rc.sim
        tr = self.track
        pf = (s.q.prog + dist / tr.ds) % tr.N
        d = clamp(s.q.d, -tr.hw * 0.8, tr.hw * 0.8)
        x, y, z, h = tr.pose_at(pf, d)
        self.vfx.append(('warp', rc.x, rc.y, rc.z))
        s.teleport(x, z, h)
        self.vfx.append(('warp', x, y, z))

    def _swap(self, rc, rng, it):
        ah = self._ahead(rc, rng)
        if not ah:
            rc.sim.boost_t = max(rc.sim.boost_t, 1.0)        # 앞에 아무도 없으면 부스터로
            return
        o = ah[0]
        mine = (rc.x, rc.z, rc.h)
        self.vfx.append(('warp', rc.x, rc.y, rc.z))
        self.vfx.append(('warp', o.x, o.y, o.z))
        rc.sim.teleport(o.x, o.z, o.h)
        if o.sim is not None:
            o.sim.teleport(mine[0], mine[1], mine[2])
            self._ev(o, ('item', 'hit', 'swap', it))
        else:
            self._send({'t': 'ia', 'k': 'swap', 'o': rc.id, 'it': it, 'tg': [o.id], 'pos': [round(mine[0], 2), round(mine[1], 2), round(mine[2], 3)]})

    def _steal(self, rc, n, it):
        got = 0
        for o in self._ahead(rc):
            if got >= n:
                break
            if o.sim is not None:
                slots = [s for s in range(ITEM_SLOTS) if o.items[s] is not None and o.roll[s] <= 0]
                if slots:
                    s = slots[int(self.rng() * len(slots)) % len(slots)]
                    took, uses = o.items[s], o.uses[s]
                    o.items[s] = None
                    o.uses[s] = 0
                    self._ev(o, ('item', 'stolen', took))
                    if self.give(rc, took, uses, 0.4):
                        got += 1
            else:
                self._send({'t': 'ia', 'k': 'steal', 'o': rc.id, 'it': it, 'tg': [o.id]})
                got += 1

    def _area(self, owner, it, targets):
        ids = [o.id for o in targets]
        self._apply_area(owner.id, it, ids)
        self._send({'t': 'ia', 'o': owner.id, 'it': it, 'tg': ids})

    def _apply_area(self, owner_id, it, ids):
        if not (isinstance(it, int) and 0 <= it < ITEM_COUNT):
            return
        item = ITEMS[it]
        p = item['p']
        own = self.race._find(owner_id)
        if item['kind'] == 'wave' and own is not None:
            self.vfx.append(('ring', own.x, own.y, own.z, p['r'], item['c1']))
        self.vfx.append(('area', it, owner_id, list(ids)))
        for rid in ids:
            rc = self.race._find(rid)
            if rc is not None and rc.sim is not None:
                self.apply(rc, p['fx'], p.get('fxd'), p.get('k'), it, owner_id)

    def _throw(self, rc, it, back):
        item = ITEMS[it]
        k = item['kind']
        p = item['p']
        s = rc.sim
        tr = self.track
        specs = []
        sp_k = max(0.0, s.vx * math.sin(rc.h) + s.vz * math.cos(rc.h))
        if k in ('shot', 'boomerang'):
            n = p.get('n', 1)
            for j in range(n):
                h = rc.h + (j - (n - 1) / 2.0) * 0.2 + (math.pi if back else 0.0)
                fx, fz = math.sin(h), math.cos(h)
                v = p['spd'] + (sp_k if not back else 0.0)
                specs.append({'k': k, 'x': rc.x + fx * 2.8, 'y': rc.y + 0.6, 'z': rc.z + fz * 2.8, 'vx': fx * v, 'vz': fz * v})
        elif k == 'homing':
            ah = self._ahead(rc, 420.0)
            fx, fz = math.sin(rc.h), math.cos(rc.h)
            v = p['spd']
            specs.append({'k': k, 'x': rc.x + fx * 2.8, 'y': rc.y + 0.7, 'z': rc.z + fz * 2.8, 'vx': fx * v, 'vz': fz * v, 'tg': ah[0].id if ah else None})
        elif k == 'seeker':
            tg = None
            for o in self.race.ranking():
                if o is not rc and not o.finished:
                    tg = o.id
                    break
            specs.append({'k': k, 'x': rc.x, 'y': rc.y + 4.0, 'z': rc.z, 'tg': tg})
        elif k == 'bomb':
            n = p.get('n', 1)
            for j in range(n):
                h = rc.h + (j - (n - 1) / 2.0) * 0.3 + (math.pi if back else 0.0)
                fx, fz = math.sin(h), math.cos(h)
                hs = (sp_k if not back else 0.0) + p['dist'] / 0.7
                specs.append({'k': k, 'x': rc.x + fx * 2.2, 'y': rc.y + 1.2, 'z': rc.z + fz * 2.2, 'vx': fx * hs, 'vz': fz * hs, 'vy': 9.0})
        elif k == 'tornado':
            specs.append({'k': k, 'p': (s.q.prog + 14.0 / tr.ds) % tr.N, 'd': clamp(s.q.d, -tr.hw * 0.5, tr.hw * 0.5)})
        elif k == 'meteor':
            for o in [o for o in self.race.ranking() if o is not rc and not o.finished][:p['n']]:
                specs.append({'k': k, 'x': o.x, 'y': o.y + 40.0, 'z': o.z, 'tg': o.id})
        elif k == 'trap':
            n = p.get('n', 1)
            fx, fz = math.sin(rc.h), math.cos(rc.h)
            for j in range(n):
                if n == 1:
                    x, z = rc.x - fx * 3.2, rc.z - fz * 3.2
                else:
                    d = tr.hw * (-0.75 + 1.5 * j / (n - 1))
                    x, _y, z, _h = tr.pose_at((s.q.prog - (7.0 + (j % 2) * 5.0) / tr.ds) % tr.N, d)
                tr.query(x, z, s.hint, self.q)
                specs.append({'k': k, 'x': x, 'y': self.q.y + 0.05, 'z': z, 'h': rc.h})
        ents = [self._spawn(rc.id, it, sp) for sp in specs]
        if ents:
            self._send({'t': 'iu', 'o': rc.id, 'it': it, 'e': [self._wire(e, sp) for e, sp in zip(ents, specs)]})

    def _wire(self, e, sp):
        w = {'i': e.eid}
        for key in ('k', 'x', 'y', 'z', 'vx', 'vz', 'vy', 'h', 'p', 'd'):
            if key in sp:
                w[key] = round(sp[key], 3) if isinstance(sp[key], float) else sp[key]
        if sp.get('tg') is not None:
            w['tg'] = sp['tg']
        return w

    def _spawn(self, owner, it, sp, eid=None):
        if eid is None:
            self.seq += 1
            eid = '%s.%d' % (owner, self.seq)
        p = ITEMS[it]['p']
        tr = self.track
        e = Ent()
        e.eid = eid
        e.kind = sp.get('k', 'shot')
        e.item = it
        e.owner = owner
        e.x = float(sp.get('x', 0.0))
        e.y = float(sp.get('y', 0.0))
        e.z = float(sp.get('z', 0.0))
        e.vx = float(sp.get('vx', 0.0))
        e.vz = float(sp.get('vz', 0.0))
        e.vy = float(sp.get('vy', 0.0))
        e.h = float(sp.get('h', math.atan2(e.vx, e.vz) if (e.vx or e.vz) else 0.0))
        e.target = sp.get('tg')
        e.life = float(p.get('life', 4.0))
        e.r = float(p.get('r', 1.2))
        e.bounce = int(p.get('bounce', 0))
        if e.kind == 'tornado':
            e.prog = float(sp.get('p', 0.0))
            e.d = float(sp.get('d', 0.0))
            e.x, e.y, e.z, e.h = tr.pose_at(e.prog, e.d)
        elif e.kind == 'meteor':
            e.life = p.get('fall', 1.6) + 0.3
            e.gy = e.y - 40.0
        elif e.kind == 'bomb':
            e.life = 6.0
        elif e.kind == 'trap':
            e.gy = e.y
        tr.query(e.x, e.z, -1, self.q)
        e.hint = self.q.idx
        e.prog = self.q.prog if e.kind != 'tornado' else e.prog
        self.ents.append(e)
        if len(self.ents) > 140:                  # 너무 많으면 오래된 함정부터 정리
            for old in self.ents:
                if old.kind == 'trap' and not old.dead:
                    old.dead = True
                    break
        return e

    def _get(self, eid):
        for e in self.ents:
            if e.eid == eid:
                return e
        return None

    # ---- 맞음 처리 ----------------------------------------------------------------------
    def apply(self, rc, fx, dur=None, k=None, it=None, owner_id=None):
        """권한 있는 카트(rc.sim 존재)에 효과 적용"""
        s = rc.sim
        if s is None:
            return 'immune'
        res = s.hit(fx, dur or 0.0, k or 0.0)
        if res == 'ok':
            if fx == 'warpback':
                self._warp(rc, -float(dur or 40.0))
            self.vfx.append(('hit', rc.x, rc.y, rc.z, fx))
            self._ev(rc, ('item', 'hit', fx, it))
            loc = self.race.local
            if loc is not None and owner_id == loc.id and rc is not loc:
                self.race.ev(('item', 'score', rc.name, it))
        elif res == 'block':
            self.vfx.append(('block', rc.x, rc.y, rc.z))
            self._ev(rc, ('item', 'block', it))
        return res

    def _explode(self, e, notify=False):
        if e.dead:
            return
        e.dead = True
        p = ITEMS[e.item]['p']
        r = float(p.get('blast', p.get('r', 6.0)))
        self.vfx.append(('boom', e.x, e.y, e.z, r, ITEMS[e.item]['c1']))
        if notify:
            self._send({'t': 'ih', 'e': e.eid, 'boom': 1})
        rr = r * r
        for rc in self.race.racers:
            if rc.sim is None or rc.finished:
                continue
            if e.kind == 'bomb' and rc.id == e.owner:
                continue                           # 던진 사람은 자기 폭탄에 안 맞음
            if (rc.x - e.x) ** 2 + (rc.z - e.z) ** 2 < rr and abs(rc.y - e.y) < 8.0:
                self.apply(rc, p['fx'], p.get('fxd'), p.get('k'), e.item, e.owner)

    def _hit_by(self, e, rc):
        p = ITEMS[e.item]['p']
        if e.kind in ('bomb',) or (e.kind == 'trap' and p.get('shape') == 'mine'):
            self._explode(e, True)
            return True
        persist = bool(p.get('persist')) or e.kind == 'tornado'
        if persist:
            last = e.hits.get(rc.id, -99.0)
            cool = 0.3 if p.get('fx') == 'slow' else 1.2
            if self.t - last < cool:
                return False
            e.hits[rc.id] = self.t
        res = self.apply(rc, p['fx'], p.get('fxd'), p.get('k'), e.item, e.owner)
        if not persist:
            e.dead = True
            self.vfx.append(('pop', e.x, e.y, e.z, ITEMS[e.item]['c1']))
            self._send({'t': 'ih', 'e': e.eid, 'v': rc.id})
            return True
        return res == 'ok'

    def _collide(self, e):
        k = e.kind
        if k in ('seeker', 'meteor') or (k == 'bomb' and e.state == 0):
            return
        ground = k in ('trap', 'bomb')
        for rc in self.race.racers:
            s = rc.sim
            if s is None or rc.finished or e.dead:
                continue
            if rc.id == e.owner and e.age < _ARM.get(k, 0.5):
                continue
            if ground and rc.air_y > 0.6:
                continue                       # 점프/날아가는 중에는 바닥 함정 위를 지나감
            if k == 'bomb':
                rr = 2.6 + 1.1 * rc.scale       # 땅에 떨어진 폭탄: 가까이 오면 터짐
            else:
                rr = e.r + 1.1 * rc.scale
            dx = rc.x - e.x
            dz = rc.z - e.z
            if dx * dx + dz * dz < rr * rr and abs(rc.y + rc.air_y - e.y) < 3.5:
                if self._hit_by(e, rc) and e.dead:
                    return

    # ---- 매 스텝 ----------------------------------------------------------------------
    def step(self, dt):
        self.t += dt
        race = self.race
        self._boxes_step(dt)
        for rc in race.racers:
            s = rc.sim
            if s is None:
                continue
            for i in range(ITEM_SLOTS):
                if rc.roll[i] > 0:
                    rc.roll[i] -= dt
                    if rc.roll[i] <= 0:
                        rc.roll[i] = 0.0
                        if rc.items[i] is not None:
                            self._ev(rc, ('item', 'get', rc.items[i], i))
            if s.magnet_t > 0:
                ah = self._ahead(rc, s.magnet_range)
                s.pull = None
                if ah:
                    o = ah[0]
                    dx, dz = o.x - rc.x, o.z - rc.z
                    l = math.hypot(dx, dz)
                    if l > 3.0:
                        s.pull = (dx / l, dz / l)
        for e in self.ents:
            if not e.dead:
                self._step_ent(e, dt)
            if not e.dead:
                self._collide(e)
        self._ram(dt)
        if any(e.dead for e in self.ents):
            self.ents = [e for e in self.ents if not e.dead]

    def _ram(self, dt):
        """무적/거대화/로켓 카트에 부딪히면 날아간다 (피해자 쪽 기기가 판정)"""
        rs = self.race.racers
        for v in rs:
            s = v.sim
            if s is None or v.finished or s.ram_cool > 0 or (v.fx & (FX_RAM | FX_GHOST)):
                continue
            for o in rs:
                if o is v or not (o.fx & FX_RAM) or (o.fx & FX_GHOST):
                    continue
                rr = 2.4 + (1.4 if o.fx & FX_GIANT else 0.0)
                if (o.x - v.x) ** 2 + (o.z - v.z) ** 2 < rr * rr:
                    self.apply(v, 'flat' if o.fx & FX_GIANT else 'spin', None, None, None, o.id)
                    s.ram_cool = 1.2
                    break

    def _move_flat(self, e, dt, bounce):
        """지면을 따라 이동 + 벽 처리 (bounce: 반사, 아니면 미끄러짐)"""
        tr = self.track
        q = self.q
        sp = math.hypot(e.vx, e.vz)
        n = max(1, int(math.ceil(sp * dt / 1.5)))
        sdt = dt / n
        lim = tr.wall_off - 0.9
        for _ in range(n):
            e.x += e.vx * sdt
            e.z += e.vz * sdt
            tr.query(e.x, e.z, e.hint, q)
            e.hint = q.idx
            if abs(q.d) > lim:
                sg = sign(q.d)
                over = abs(q.d) - lim
                e.x -= q.rx * over * sg
                e.z -= q.rz * over * sg
                vn = (e.vx * q.rx + e.vz * q.rz) * sg
                if vn > 0:
                    if bounce:
                        e.vx -= 2 * vn * q.rx * sg
                        e.vz -= 2 * vn * q.rz * sg
                        e.bounce -= 1
                        if e.bounce < 0:
                            e.dead = True
                            self.vfx.append(('pop', e.x, e.y, e.z, ITEMS[e.item]['c1']))
                            return
                    else:
                        e.vx -= vn * q.rx * sg
                        e.vz -= vn * q.rz * sg
        e.prog = q.prog
        e.d = q.d
        return q.y

    def _steer_to(self, e, ax, az, spd, dt, turn=6.0):
        dx, dz = ax - e.x, az - e.z
        l = math.hypot(dx, dz) or 1.0
        cx, cz = e.vx / (math.hypot(e.vx, e.vz) or 1.0), e.vz / (math.hypot(e.vx, e.vz) or 1.0)
        k = min(1.0, dt * turn)
        nx, nz = cx + (dx / l - cx) * k, cz + (dz / l - cz) * k
        nl = math.hypot(nx, nz) or 1.0
        e.vx, e.vz = nx / nl * spd, nz / nl * spd

    def _step_ent(self, e, dt):
        item = ITEMS[e.item]
        p = item['p']
        k = e.kind
        tr = self.track
        e.age += dt
        if k in ('shot', 'boomerang'):
            if k == 'boomerang' and e.state == 0 and e.age > p.get('out', 1.3):
                e.state = 1
            if k == 'boomerang' and e.state == 1:
                own = self.race._find(e.owner)
                if own is None:
                    e.dead = True
                    return
                self._steer_to(e, own.x, own.z, p['spd'] + own.speed, dt, 5.0)
                if (own.x - e.x) ** 2 + (own.z - e.z) ** 2 < 6.0:
                    e.dead = True                       # 주인이 다시 잡음
                    return
            gy = self._move_flat(e, dt, k == 'shot')
            if e.dead:
                return
            e.y = gy + 0.6
            e.h = math.atan2(e.vx, e.vz)
        elif k == 'homing':
            tgt = self.race._find(e.target) if e.target is not None else None
            spd = p['spd']
            if tgt is not None and not tgt.finished and (tgt.x - e.x) ** 2 + (tgt.z - e.z) ** 2 < 45.0 ** 2:
                self._steer_to(e, tgt.x, tgt.z, spd, dt, 7.0)
            else:
                dd = e.d * 0.9
                if tgt is not None and not tgt.finished:
                    tr.query(tgt.x, tgt.z, tgt.idx, self.q)
                    dd = clamp(self.q.d, -tr.hw, tr.hw)
                x, _y, z, _h = tr.pose_at((e.prog + 10.0 / tr.ds) % tr.N, e.d + (dd - e.d) * 0.3)
                self._steer_to(e, x, z, spd, dt, 6.0)
            gy = self._move_flat(e, dt, False)
            e.y = gy + 0.7
            e.h = math.atan2(e.vx, e.vz)
        elif k == 'seeker':
            tgt = self.race._find(e.target) if e.target is not None else None
            if tgt is None or tgt.finished:
                self._explode(e)
                return
            spd = p['spd']
            tr.query(e.x, e.z, e.hint, self.q)
            e.hint = self.q.idx
            dist = math.hypot(tgt.x - e.x, tgt.z - e.z)
            if dist < 26.0:
                self._steer_to(e, tgt.x, tgt.z, spd, dt, 9.0)
                e.y += (tgt.y + 0.8 - e.y) * min(1.0, dt * 5.0)
            else:
                x, _y, z, _h = tr.pose_at((self.q.prog + 16.0 / tr.ds) % tr.N, 0.0)
                self._steer_to(e, x, z, spd, dt, 5.0)
                e.y += (self.q.y + 6.0 - e.y) * min(1.0, dt * 3.0)
            e.x += e.vx * dt
            e.z += e.vz * dt
            e.h = math.atan2(e.vx, e.vz)
            if dist < 2.6:
                self._explode(e)
                return
        elif k == 'bomb':
            if e.state == 0:
                e.vy -= 26.0 * dt
                e.y += e.vy * dt
                gy = self._move_flat(e, dt, False)
                if e.y <= gy + 0.45 and e.vy < 0:
                    e.y = gy + 0.45
                    e.state = 1
                    e.age = 0.0
                    e.vx *= 0.25                     # 떨어진 자리에 거의 멈춘다
                    e.vz *= 0.25
            else:
                e.vx *= math.exp(-6.0 * dt)
                e.vz *= math.exp(-6.0 * dt)
                e.y = self._move_flat(e, dt, False) + 0.45
                if e.age >= p['fuse']:
                    self._explode(e)
                    return
        elif k == 'tornado':
            e.prog = (e.prog + p['spd'] * dt / tr.ds) % tr.N
            dd = math.sin(e.age * 1.3) * tr.hw * 0.55
            e.d += (dd - e.d) * min(1.0, dt * 2.0)
            e.x, e.y, e.z, e.h = tr.pose_at(e.prog, e.d)
        elif k == 'meteor':
            fall = p.get('fall', 1.6)
            tgt = self.race._find(e.target) if e.target is not None else None
            if tgt is not None and e.age < fall - 0.35:
                e.x, e.z, e.gy = tgt.x, tgt.z, tgt.y
            e.y = e.gy + 40.0 * max(0.0, 1.0 - e.age / fall)
            if e.age >= fall:
                e.y = e.gy
                self._explode(e)
                return
        e.life -= dt
        if e.life <= 0:
            if k in ('bomb', 'seeker', 'meteor'):
                self._explode(e)
            else:
                e.dead = True

    # ---- 봇 ---------------------------------------------------------------------------
    def bot_think(self, rc, dt):
        if self.race.phase != 'run' or rc.finished or rc.sim is None:
            return
        react = rc.brain.react if rc.brain is not None else 1.0
        for slot in range(ITEM_SLOTS):
            it = rc.items[slot]
            if it is None or rc.roll[slot] > 0:
                continue
            rc.hold[slot] += dt
            if rc.hold[slot] < react:
                continue
            if self._bot_wants(rc, it, rc.hold[slot]):
                back = ITEMS[it]['kind'] in ('shot', 'bomb') and self._threat_behind(rc, 25.0) and not self._ahead(rc, 80.0)
                self.use(rc, slot, back)
                rc.hold[slot] = 0.0
                return

    def _threat_behind(self, rc, dist):
        ds = self.track.ds
        for o in self.race.racers:
            if o is not rc and not o.finished:
                gap = (rc.total - o.total) * ds
                if 0 < gap < dist:
                    return True
        return False

    def _bot_wants(self, rc, it, held):
        item = ITEMS[it]
        k = item['kind']
        p = item['p']
        s = rc.sim
        tr = self.track
        straight = tr.turn[s.q.idx] < 0.3
        if k in ('boost', 'engine', 'hop', 'coin', 'grip', 'lucky'):
            return straight or held > 6.0
        if k in ('star', 'rocket', 'giant', 'warp', 'magnet'):
            return straight or held > 4.0
        if k == 'shield':
            return held > 1.0
        if k == 'cleanse':
            return s.debuffed() or held > 8.0
        if k == 'ghost':
            return held > 2.5
        if k in ('shot', 'boomerang'):
            h = rc.h
            sh, ch = math.sin(h), math.cos(h)
            for o in self._ahead(rc, 70.0):
                dx, dz = o.x - rc.x, o.z - rc.z
                if dx * sh + dz * ch > 4.0 and abs(-dx * ch + dz * sh) < 3.5:
                    return True
            return held > 9.0 or self._threat_behind(rc, 20.0)
        if k in ('homing', 'steal'):
            return bool(self._ahead(rc, 160.0)) or held > 10.0
        if k == 'swap':
            return bool(self._ahead(rc, p['range'])) or held > 12.0
        if k == 'bomb':
            return bool(self._ahead(rc, 60.0)) or held > 8.0
        if k in ('seeker', 'zap', 'meteor', 'tornado'):
            return held > 2.0
        if k == 'wave':
            rr = (p['r'] * 0.8) ** 2
            return any(o is not rc and not o.finished and (o.x - rc.x) ** 2 + (o.z - rc.z) ** 2 < rr for o in self.race.racers) or held > 10.0
        if k == 'trap':
            return self._threat_behind(rc, 30.0) or held > 7.0
        return held > 5.0

    # ---- 네트워크 ---------------------------------------------------------------------
    def handle_message(self, m):
        t = m.get('t')
        race = self.race
        try:
            if t == 'ib':
                i = int(m.get('b', -1))
                if 0 <= i < len(self.boxes):
                    b = self.boxes[i]
                    if b['t'] <= 0:
                        self.vfx.append(('box', b['x'], b['y'], b['z']))
                    b['t'] = self.BOX_RESPAWN
            elif t == 'iu':
                it = m.get('it')
                if not (isinstance(it, int) and 0 <= it < ITEM_COUNT):
                    return
                o = m.get('o')
                for w in m.get('e', []):
                    if self._get(w.get('i')) is None:
                        sp = dict(w)
                        self._spawn(o, it, sp, w.get('i'))
                rc = race._find(o)
                if rc is not None and ITEMS[it]['kind'] in ('boost',):
                    self.vfx.append(('boost', o))
            elif t == 'ih':
                e = self._get(m.get('e'))
                if e is not None:
                    if m.get('boom'):
                        self._explode(e)
                    elif not ITEMS[e.item]['p'].get('persist'):
                        e.dead = True
                        self.vfx.append(('pop', e.x, e.y, e.z, ITEMS[e.item]['c1']))
                    loc = race.local
                    v = race._find(m.get('v'))
                    if loc is not None and e.owner == loc.id and v is not None and v is not loc:
                        race.ev(('item', 'score', v.name, e.item))
            elif t == 'ia':
                k = m.get('k')
                tg = m.get('tg', []) or []
                if k == 'swap':
                    pos = m.get('pos')
                    for rid in tg:
                        rc = race._find(rid)
                        if rc is not None and rc.sim is not None and pos:
                            self.vfx.append(('warp', rc.x, rc.y, rc.z))
                            rc.sim.teleport(float(pos[0]), float(pos[1]), float(pos[2]))
                            self._ev(rc, ('item', 'hit', 'swap', m.get('it')))
                elif k == 'steal':
                    for rid in tg:
                        rc = race._find(rid)
                        if rc is not None and rc.sim is not None:
                            slots = [s for s in range(ITEM_SLOTS) if rc.items[s] is not None and rc.roll[s] <= 0]
                            if slots:
                                s = slots[int(self.rng() * len(slots)) % len(slots)]
                                took, uses = rc.items[s], rc.uses[s]
                                rc.items[s] = None
                                rc.uses[s] = 0
                                self._ev(rc, ('item', 'stolen', took))
                                self._send({'t': 'ig', 'to': m.get('o'), 'it': took, 'u': uses})
                else:
                    self._apply_area(m.get('o'), m.get('it'), tg)
            elif t == 'ig':
                rc = race._find(m.get('to'))
                it = m.get('it')
                if rc is not None and rc.sim is not None and isinstance(it, int) and 0 <= it < ITEM_COUNT:
                    self.give(rc, it, m.get('u'), 0.4)
        except (TypeError, ValueError, KeyError):
            pass

    def take_vfx(self):
        v = self.vfx
        self.vfx = []
        return v


def hue_rgb(h):
    """0..1 색상환 -> 선명한 RGB (무적 스타 무지개 효과 등)"""
    h = (h % 1.0) * 6.0
    i = int(h)
    f = h - i
    q = int(255 * (1 - f))
    t = int(255 * f)
    return [(255, t, 0), (q, 255, 0), (0, 255, t), (0, q, 255), (t, 0, 255), (255, 0, q)][i % 6]


def fx_status(s, lang='ko'):
    """HUD 에 보여줄 내 카트 상태 목록 [(글자, 색), ...]"""
    ko = lang == 'ko'
    out = []

    def add(t, a, b, col):
        if t > 0:
            out.append(('%s %.1f' % (a if ko else b, t), col))
    add(s.star_t, '무적', 'STAR', (255, 220, 60))
    add(s.auto_t, '로켓', 'ROCKET', (255, 130, 90))
    add(s.ghost_t, '유령', 'GHOST', (225, 230, 255))
    add(s.giant_t, '거대화', 'GIANT', (255, 150, 150))
    if s.shield_n > 0:
        out.append((('방패 x%d' if ko else 'SHIELD x%d') % s.shield_n, (120, 210, 255)))
    add(s.engine_t, '엔진', 'ENGINE', (160, 230, 255))
    add(s.magnet_t, '자석', 'MAGNET', (255, 130, 130))
    add(s.grip_t, '타이어', 'TIRES', (255, 200, 90))
    add(s.immune_t, '보호', 'SAFE', (200, 255, 200))
    add(s.shrink_t, '축소', 'SHRUNK', (255, 255, 140))
    add(s.slow_t, '감속', 'SLOW', (255, 170, 90))
    add(s.slide_t, '미끄러짐', 'SLIPPERY', (170, 200, 255))
    add(s.freeze_t, '빙결', 'FROZEN', (175, 225, 255))
    add(s.stun_t, '엔진 정지', 'STUNNED', (255, 140, 60))
    add(s.rev_t, '조작 반전', 'REVERSED', (210, 140, 255))
    add(s.blind_t, '시야 가림', 'BLINDED', (190, 190, 200))
    if s.coins > 0:
        out.append((('코인 %d' if ko else 'COINS %d') % s.coins, (255, 214, 40)))
    return out


def incoming_threat(race):
    """내 카트를 노리는 유도/1등추적/메테오가 날아오는 중인가"""
    if race.items is None or race.local is None:
        return None
    lid = race.local.id
    for e in race.items.ents:
        if e.target == lid and e.kind in ('homing', 'seeker', 'meteor') and not e.dead:
            return e
    return None


def ent_boxes(it):
    """날아가는 아이템의 3D 박스 모델 (로컬: x 오른쪽, y 위, z 앞) - 두 프론트엔드 공용"""
    c1, c2 = it['c1'], it['c2']
    icon = it['icon']
    if icon == 'missile':
        return [(0, 0, 0, 0.28, 0.28, 0.75, c1, 1, 1, False), (0, 0, 0.92, 0.2, 0.2, 0.18, c2, 0.4, 0.4, False),
                (0, 0, -0.6, 0.62, 0.05, 0.16, c2, 1, 1, False), (0, 0, -0.86, 0.15, 0.15, 0.08, (255, 200, 60), 1, 1, True)]
    if icon == 'arrow':
        return [(0, 0, 0, 0.06, 0.06, 0.95, c2, 1, 1, False), (0, 0, 1.05, 0.24, 0.08, 0.24, c1, 0.15, 1, False),
                (0, 0, -0.9, 0.22, 0.04, 0.12, c1, 1, 1, False)]
    if icon == 'drone':
        return [(0, 0.1, 0, 1.0, 0.04, 0.08, (110, 116, 130), 1, 1, False), (0, 0.1, 0, 0.08, 0.04, 1.0, (110, 116, 130), 1, 1, False),
                (0, 0, 0, 0.45, 0.2, 0.45, c1, 1, 1, False), (0, 0.02, 0.46, 0.14, 0.08, 0.02, c2, 1, 1, True)]
    if icon == 'bird':
        return [(0, 0.1, -0.1, 1.4, 0.05, 0.36, c2, 1, 1, False), (0, 0, 0, 0.3, 0.26, 0.7, c1, 1, 1, False),
                (0, 0.16, 0.78, 0.2, 0.2, 0.2, c1, 1, 1, False)]
    if icon == 'shuriken':
        return [(0, 0, 0, 0.85, 0.05, 0.18, c1, 1, 1, False), (0, 0, 0, 0.18, 0.05, 0.85, c1, 1, 1, False),
                (0, 0.03, 0, 0.16, 0.06, 0.16, c2, 1, 1, False)]
    if icon == 'boomerang':
        return [(0.35, 0, 0, 0.62, 0.07, 0.16, c1, 1, 1, False), (0, 0, 0.35, 0.16, 0.07, 0.62, c1, 1, 1, False)]
    return [(0, 0, 0, 0.5, 0.5, 0.5, c1, 1, 1, False)]


def wall_boxes(it):
    c1, c2 = it['c1'], it['c2']
    return [(-1.3, 0.25, 0, 0.08, 0.25, 0.08, (120, 126, 140), 1, 1, False), (1.3, 0.25, 0, 0.08, 0.25, 0.08, (120, 126, 140), 1, 1, False),
            (0, 0.8, 0, 1.9, 0.42, 0.2, c1, 1, 1, False), (-1.05, 0.8, 0.21, 0.25, 0.38, 0.01, c2, 1, 1, False),
            (0, 0.8, 0.21, 0.25, 0.38, 0.01, c2, 1, 1, False), (1.05, 0.8, 0.21, 0.25, 0.38, 0.01, c2, 1, 1, False)]
