#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
  TURBO KART 3D  -  폰 버전 (Pydroid 3)            [ kart3d_phone.py ]
==========================================================================
  * 맵 1000개 / 카트 100,000종 / WiFi(LAN) 멀티플레이 / 터치 조작
  * 파일 하나로 실행됩니다. Pydroid 3 에서 이 파일을 열고 ▶ 를 누르세요.
  * 필요한 것: pygame  (Pydroid 3 > 메뉴 > Pip > "pygame" 설치)
    (PC 파이썬 3.14+ 는 `pip install pygame-ce` — 게임이 알아서 시도합니다)
  * PC 에서도 그대로 실행됩니다:  python kart3d_phone.py   (키보드 조작)

  [멀티플레이]  같은 WiFi 에 연결된 기기끼리 (폰 + 폰, 폰 + PC 가능)
     - 한 명이 [멀티플레이 > 방 만들기] 후 화면에 나온 IP 를 친구에게 알려주기
     - 친구는 [멀티플레이 > 방 찾기] (자동 검색) 또는 IP 직접 입력
     - 전용 서버:  python kart3d_phone.py --serve
  [옵션]  --window 960x540   창 크기 (PC)     --fps   FPS 표시    --lang en|ko
==========================================================================
"""
import os
import sys
import math
import time
import json
import array
import subprocess
import random as _random


def _is_android():
    return ('ANDROID_ARGUMENT' in os.environ) or ('ANDROID_ROOT' in os.environ and os.path.exists('/system/build.prop'))


def _wait_key():
    """더블클릭으로 실행했을 때 창이 바로 닫혀 오류를 못 보는 문제 방지"""
    try:
        if sys.stdin is not None and not _is_android():
            input('\nEnter 키를 누르면 창이 닫힙니다  /  Press Enter to close...')
    except Exception:
        pass


def _crash_log(text):
    """오류 내용을 화면 + kart3d_error.txt 파일로 남긴다 (파일은 게임 파일과 같은 폴더)"""
    info = 'Python %s | %s | %s' % (sys.version.split()[0], sys.platform, sys.executable)
    try:
        base = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv and sys.argv[0] else '.'
    except Exception:
        base = '.'
    for d in (base, os.path.expanduser('~'), '.'):
        try:
            path = os.path.join(d, 'kart3d_error.txt')
            with open(path, 'a', encoding='utf-8') as f:
                f.write(time.strftime('%Y-%m-%d %H:%M:%S') + '  ' + info + '\n' + text + '\n' + '-' * 60 + '\n')
            return path
        except Exception:
            continue
    return None


def _ensure_pkg(pkg, alt_hint='', candidates=None):
    """필요한 패키지가 없을 때: 올바른 설치 명령을 보여주고, 동의하면 같은 파이썬으로 설치(미리 빌드된 것만)한 뒤 게임을 다시 시작한다."""
    exe = sys.executable or 'python'
    vi = sys.version_info
    ver = '%d.%d' % (vi[0], vi[1])
    cands = list(candidates or [pkg])
    print('=' * 64)
    print('%s 패키지가 필요합니다  /  "%s" is required.   (Python %s)' % (pkg, pkg, ver))
    if _is_android():
        print('Pydroid 3:  왼쪽 위 메뉴(=) > Pip > "%s" 검색 > INSTALL  (설치 후 다시 실행)' % cands[0])
        if alt_hint:
            print(alt_hint)
        print('=' * 64)
        return
    print('이 게임을 실행하는 파이썬에 설치하는 명령 (그대로 복사해서 실행):')
    print()
    print('    "%s" -m pip install --only-binary=:all: %s' % (exe, cands[0]))
    print()
    if alt_hint:
        print(alt_hint)
    try:
        ans = input('지금 자동으로 설치할까요? / Install now? (y/n) [y]: ').strip().lower()
    except Exception:
        ans = 'n'
    if ans in ('', 'y', 'yes', 'ㅛ', '네', '예', 'ㅇ'):
        for c in cands:
            print('>> 설치 시도 / installing: %s' % c)
            rc = subprocess.call([exe, '-m', 'pip', 'install', '--only-binary=:all:', c])
            if rc == 0:
                print('설치 완료! 게임을 다시 시작합니다...  /  Installed. Restarting...')
                raise SystemExit(subprocess.call([exe] + sys.argv))
        print()
        print('설치에 실패했습니다.  /  Install failed.')
        if vi >= (3, 14):
            print('가장 흔한 원인: 파이썬 %s 은(는) 너무 새로워서 이 패키지의 설치 파일이 아직 없습니다.' % ver)
            print('  -> Python 3.13 을 설치하세요 (https://www.python.org/downloads/ , 설치 화면에서 "Add python.exe to PATH" 체크)')
            print('  -> 그 다음 새 명령 창에서:   py -3.13 -m pip install %s    그리고    py -3.13 %s' % (cands[0], os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else 'kart3d.py'))
        else:
            print('위의 오류 문구를 그대로 알려주세요.  /  Please send the error text above.')
            print('(리눅스 "externally-managed-environment" 오류: python3 -m venv venv 로 가상환경을 만든 뒤 그 안에서 설치하세요)')
    print('=' * 64)
    _wait_key()

try:
    import pygame
except ImportError:
    # 3.14+ 는 pygame 설치 파일이 없어서 호환 버전(pygame-ce)을 먼저 시도
    _ensure_pkg('pygame', candidates=(['pygame-ce', 'pygame'] if sys.version_info >= (3, 14) else ['pygame', 'pygame-ce']))
    raise SystemExit(1)

# -*- coding: utf-8 -*-
# ============================================================================
#  TURBO KART 3D (Python)  -  공통 코어
#  맵 1000개 / 카트 100,000종 / 아케이드 물리 / AI / WiFi(LAN) 멀티플레이
# ============================================================================
import math
import json
import socket
import threading
import time
import os
import sys
import queue

VERSION = '1.0'
MAP_COUNT = 1000
KART_COUNT = 100000
DEFAULT_PORT = 5555
DISC_PORT = 5556
TAU = math.pi * 2.0
STEP = 1.0 / 60.0          # 물리 고정 시간 간격


def clamp(v, a, b):
    return a if v < a else (b if v > b else v)


def sign(v):
    return 1.0 if v > 0 else (-1.0 if v < 0 else 0.0)


def wrap_pi(a):
    return (a + math.pi) % TAU - math.pi


def lerp(a, b, t):
    return a + (b - a) * t


def hex_rgb(v):
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


def mix_rgb(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))


def shade_rgb(c, k):
    return (int(clamp(c[0] * k, 0, 255)), int(clamp(c[1] * k, 0, 255)), int(clamp(c[2] * k, 0, 255)))


class Rng(object):
    """mulberry32 - 모든 기기/파이썬 버전에서 동일한 난수열"""
    __slots__ = ('a',)

    def __init__(self, seed):
        self.a = int(seed) & 0xFFFFFFFF

    def __call__(self):
        a = self.a = (self.a + 0x6D2B79F5) & 0xFFFFFFFF
        t = ((a ^ (a >> 15)) * (1 | a)) & 0xFFFFFFFF
        t = (((t + (((t ^ (t >> 7)) * (61 | t)) & 0xFFFFFFFF)) & 0xFFFFFFFF) ^ t) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0


def hash32(n):
    h = int(float(n + 1) * 2654435761.0) & 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 2246822519) & 0xFFFFFFFF
    h ^= h >> 13
    return h & 0xFFFFFFFF


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


# ----------------------------------------------------------------------------
#  트랙 생성: 맵 번호(1~1000) -> 고유한 코스 (중심선/고저차/뱅킹/장식물/부스트 패드)
# ----------------------------------------------------------------------------
def _mix3(a, b, wa, wb):
    return (a[0] * wa + b[0] * wb, a[1] * wa + b[1] * wb, a[2] * wa + b[2] * wb)


def catmull_closed(pts, per=40, alpha=0.5):
    """닫힌 centripetal Catmull-Rom 스플라인 (Barry-Goldman)"""
    n = len(pts)
    out = []

    def dist(a, b):
        return max(1e-3, math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2))
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        t0 = 0.0
        t1 = t0 + dist(p0, p1) ** alpha
        t2 = t1 + dist(p1, p2) ** alpha
        t3 = t2 + dist(p2, p3) ** alpha
        for s in range(per):
            t = t1 + (t2 - t1) * s / per
            a1 = _mix3(p0, p1, (t1 - t) / (t1 - t0), (t - t0) / (t1 - t0))
            a2 = _mix3(p1, p2, (t2 - t) / (t2 - t1), (t - t1) / (t2 - t1))
            a3 = _mix3(p2, p3, (t3 - t) / (t3 - t2), (t - t2) / (t3 - t2))
            b1 = _mix3(a1, a2, (t2 - t) / (t2 - t0), (t - t0) / (t2 - t0))
            b2 = _mix3(a2, a3, (t3 - t) / (t3 - t1), (t - t1) / (t3 - t1))
            out.append(_mix3(b1, b2, (t2 - t) / (t2 - t1), (t - t1) / (t2 - t1)))
    return out


def resample_closed(poly, spacing, min_n=220):
    """닫힌 폴리라인을 호 길이 기준 균일 간격으로 재샘플링"""
    m = len(poly)
    seg = []
    total = 0.0
    for i in range(m):
        a = poly[i]
        b = poly[(i + 1) % m]
        d = math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)
        seg.append(d)
        total += d
    n = max(min_n, int(round(total / spacing)))
    step = total / n
    out = []
    i = 0
    acc = 0.0
    for k in range(n):
        target = k * step
        while i < m - 1 and target > acc + seg[i]:
            acc += seg[i]
            i += 1
        f = (target - acc) / seg[i] if seg[i] > 1e-9 else 0.0
        f = 0.0 if f < 0 else (1.0 if f > 1 else f)
        a = poly[i]
        b = poly[(i + 1) % m]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f))
    return out


def max_turn_angle(poly):
    n = len(poly)
    worst = 0.0
    for i in range(n):
        a = poly[i - 1]
        b = poly[i]
        c = poly[(i + 1) % n]
        v1x = b[0] - a[0]
        v1z = b[2] - a[2]
        v2x = c[0] - b[0]
        v2z = c[2] - b[2]
        ang = abs(math.atan2(v1x * v2z - v1z * v2x, v1x * v2x + v1z * v2z))
        if ang > worst:
            worst = ang
    return worst


def min_separation(poly, ds):
    """경로상으로 멀리 떨어진 두 구간이 공간적으로 얼마나 가까운지"""
    n = len(poly)
    cell = 90.0
    grid = {}
    for i, p in enumerate(poly):
        grid.setdefault((int(p[0] // cell), int(p[2] // cell)), []).append(i)
    skip = int(140.0 / ds)
    best = 1e18
    for i, p in enumerate(poly):
        cx = int(p[0] // cell)
        cz = int(p[2] // cell)
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                lst = grid.get((cx + a, cz + b))
                if not lst:
                    continue
                for j in lst:
                    dj = abs(i - j)
                    if min(dj, n - dj) < skip:
                        continue
                    q = poly[j]
                    d = (p[0] - q[0]) ** 2 + (p[2] - q[2]) ** 2
                    if d < best:
                        best = d
    return math.sqrt(best)


def relax_corners(poly, max_ang=0.19, iters=60, spacing=4.0):
    n = len(poly)
    pts = [list(p) for p in poly]
    changed = False
    for _ in range(iters):
        bad = []
        for i in range(n):
            a = pts[i - 1]
            b = pts[i]
            c = pts[(i + 1) % n]
            v1x = b[0] - a[0]
            v1z = b[2] - a[2]
            v2x = c[0] - b[0]
            v2z = c[2] - b[2]
            if abs(math.atan2(v1x * v2z - v1z * v2x, v1x * v2x + v1z * v2z)) > max_ang:
                bad.append(i)
        if not bad:
            break
        changed = True
        mark = set()
        for i in bad:
            for k in range(-7, 8):
                mark.add((i + k) % n)
        new = [p[:] for p in pts]
        for i in mark:
            a = pts[i - 1]
            b = pts[i]
            c = pts[(i + 1) % n]
            new[i][0] = 0.5 * b[0] + 0.25 * (a[0] + c[0])
            new[i][2] = 0.5 * b[2] + 0.25 * (a[2] + c[2])
        pts = new
    if not changed:
        return poly
    return resample_closed([tuple(p) for p in pts], spacing)


class Q(object):
    """track.query() 결과 (재사용 객체)"""
    __slots__ = ('idx', 't', 'prog', 'd', 'rx', 'rz', 'tx', 'tz', 'ty', 'bank', 'cx', 'cy', 'cz', 'y')

    def __init__(self):
        self.idx = 0
        self.t = 0.0
        self.prog = 0.0
        self.d = 0.0
        self.rx = 0.0
        self.rz = 1.0
        self.tx = 0.0
        self.tz = 1.0
        self.ty = 0.0
        self.bank = 0.0
        self.cx = self.cy = self.cz = 0.0
        self.y = 0.0


class Track(object):
    SH = 12.0   # 갓길(잔디) 폭 - 그 바깥이 벽

    def __init__(self, map_id, outline_only=False):
        self.info = map_info(map_id)
        self.theme = THEMES[self.info['theme']]
        r = Rng(self.info['seed'])
        self.width = 15.0 + int(r() * 5)
        self.hw = self.width / 2.0
        hw, SH = self.hw, self.SH
        self.wall_off = hw + SH - 0.6
        # (가로 오프셋, 높이 변화): 도로 -> 연석 -> 갓길 -> 비탈
        self.rows = [(hw, 0.0), (hw + 0.7, -0.14), (hw + SH, -0.25), (hw + SH + 40.0, -2.5), (hw + SH + 200.0, -30.0)]
        self._centerline(r)
        self.props = []
        self.props_by_seg = {}
        self.pads = []
        self.lamps = []
        self.arches = []
        if not outline_only:
            self._decorate(r)

    # ---- 중심선 -----------------------------------------------------------
    def _centerline(self, r):
        th = self.theme
        K = 7 + int(r() * 8)
        R = 240 + r() * 240
        amp = 0.16 + r() * 0.24
        aspect = 1 + r() * 0.8
        rot = r() * TAU
        ph = (r() * TAU, r() * TAU, r() * TAU)
        elev = th['elev'] * (0.35 + r() * 0.65)
        jit = []
        noise = []
        for i in range(K):
            jit.append((r() - 0.5) * 0.55)
            noise.append(r() * 2 - 1)
        cr, sr = math.cos(rot), math.sin(rot)
        need_sep = 2 * (self.hw + self.SH) + 10.0
        poly = None
        for attempt in range(9):
            k = 0.8 ** attempt
            asp = 1 + (aspect - 1) * k
            pts = []
            for i in range(K):
                a = ((i + jit[i] * k) / K) * TAU
                rad = R * (1 + noise[i] * amp * k)
                x = math.cos(a) * rad * asp
                z = math.sin(a) * rad
                t = a / TAU
                y = elev * (math.sin(TAU * t + ph[0]) * 0.6 + math.sin(2 * TAU * t + ph[1]) * 0.3 + math.sin(3 * TAU * t + ph[2]) * 0.18)
                pts.append((x * cr - z * sr, y, x * sr + z * cr))
            poly = resample_closed(catmull_closed(pts, 40), 4.0)
            poly = relax_corners(poly)
            if max_turn_angle(poly) <= 0.21 and min_separation(poly, 4.0) >= need_sep:
                break
        n0 = len(poly)

        def tang(i):
            i %= n0
            a = poly[(i - 1) % n0]
            b = poly[(i + 1) % n0]
            dx, dz = b[0] - a[0], b[2] - a[2]
            l = math.hypot(dx, dz) or 1.0
            return dx / l, dz / l
        best_i, best_s = 0, 1e9
        for i in range(0, n0, 2):
            t0 = tang(i - 6)
            t1 = tang(i + 6)
            s = 1 - (t0[0] * t1[0] + t0[1] * t1[1])
            if s < best_s:
                best_s, best_i = s, i
        poly = poly[best_i:] + poly[:best_i]
        N = len(poly)
        self.N = N
        self.px = [p[0] for p in poly]
        self.py = [p[1] for p in poly]
        self.pz = [p[2] for p in poly]
        self.tx = [0.0] * N
        self.ty = [0.0] * N
        self.tz = [0.0] * N
        self.rx = [0.0] * N
        self.rz = [0.0] * N
        length = 0.0
        for i in range(N):
            a = (i - 1) % N
            b = (i + 1) % N
            dx = self.px[b] - self.px[a]
            dy = self.py[b] - self.py[a]
            dz = self.pz[b] - self.pz[a]
            l = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
            dx /= l
            dy /= l
            dz /= l
            self.tx[i], self.ty[i], self.tz[i] = dx, dy, dz
            h = math.hypot(dx, dz) or 1.0
            self.rx[i] = -dz / h
            self.rz[i] = dx / h
            length += math.sqrt((self.px[b] - self.px[i]) ** 2 + (self.py[b] - self.py[i]) ** 2 + (self.pz[b] - self.pz[i]) ** 2)
        self.length = length
        self.ds = length / N
        # 뱅킹: 코너 안쪽으로 기울임
        cur = [0.0] * N
        for i in range(N):
            a = (i - 3) % N
            b = (i + 3) % N
            cur[i] = self.tz[a] * self.tx[b] - self.tx[a] * self.tz[b]
        self.bank = [0.0] * N
        for i in range(N):
            s = 0.0
            for k in range(-10, 11):
                s += cur[(i + k) % N]
            self.bank[i] = clamp((-s / 21.0) * 2.4, -0.2, 0.2)
        # 앞쪽 커브 강도 (AI 속도 제어용)
        self.turn = [0.0] * N
        for i in range(N):
            m = 0.0
            for k in range(4, 35, 3):
                j = (i + k) % N
                c = self.tx[i] * self.tx[j] + self.tz[i] * self.tz[j]
                m = max(m, math.acos(clamp(c, -1.0, 1.0)))
            self.turn[i] = m
        self.min_y = min(self.py)
        self.max_y = max(self.py)
        self.bounds = (min(self.px), max(self.px), min(self.pz), max(self.pz))

    # ---- 장식물/패드 ---------------------------------------------------------
    def _decorate(self, r):
        th = self.theme
        N = self.N
        px, pz, py, rx, rz = self.px, self.pz, self.py, self.rx, self.rz
        # 부스트 패드
        count = 6 + int(r() * 5)
        for k in range(count):
            idx = int(((k + 0.5 + (r() - 0.5) * 0.4) / count) * N)
            d = (r() - 0.5) * self.width * 0.5
            if idx < 14 or idx > N - 8:
                continue
            self.pads.append(dict(idx=idx, d=d, half_len=4.5, half_w=2.8))
        # 장식물
        cell = 60.0
        grid = {}
        for i in range(0, N, 2):
            grid.setdefault((int(px[i] // cell), int(pz[i] // cell)), []).append(i)
        min2 = (self.hw + self.SH + 5.0) ** 2

        def free(x, z):
            cx = int(x // cell)
            cz = int(z // cell)
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    lst = grid.get((cx + a, cz + b))
                    if lst:
                        for i in lst:
                            dx = px[i] - x
                            dz = pz[i] - z
                            if dx * dx + dz * dz < min2:
                                return False
            return True
        total = sum(w for _, w in th['props'])
        want = int(round(N * 2.1))
        for _ in range(want):
            i = int(r() * N)
            side = 1 if r() < 0.5 else -1
            lat = self.wall_off + 4 + (r() ** 1.4) * 55
            x = px[i] + rx[i] * lat * side
            z = pz[i] + rz[i] * lat * side
            if not free(x, z):
                continue
            pick = r() * total
            kind = th['props'][0][0]
            for name, w in th['props']:
                pick -= w
                if pick <= 0:
                    kind = name
                    break
            y = py[i] + self.dy_at(lat) - 0.15
            rot = r() * 6.283
            s = 0.7 + r() * 0.9
            r1, r2, r3 = r(), r(), r()
            self.props.append(dict(kind=kind, x=x, y=y, z=z, rot=rot, s=s, r1=r1, r2=r2, r3=r3, seg=i))
        for p in self.props:
            self.props_by_seg.setdefault(p['seg'], []).append(p)
        if th.get('lamps'):
            k = 0
            for i in range(4, N, 7):
                self.lamps.append((i, 1 if k % 2 else -1))
                k += 1
        if th.get('arches'):
            for k in range(4):
                self.arches.append(int(((k + 0.5) / 4) * N + 20) % N)

    # ---- 질의 ---------------------------------------------------------------
    def dy_at(self, off):
        off = abs(off)
        rows = self.rows
        if off <= rows[0][0]:
            return 0.0
        for i in range(1, len(rows)):
            if off <= rows[i][0]:
                a = rows[i - 1]
                b = rows[i]
                return a[1] + (b[1] - a[1]) * ((off - a[0]) / (b[0] - a[0]))
        return rows[-1][1]

    def query(self, x, z, hint, o):
        N = self.N
        px = self.px
        pz = self.pz
        best = 0
        bd = 1e30
        if hint < 0:
            for i in range(N):
                dx = px[i] - x
                dz = pz[i] - z
                d = dx * dx + dz * dz
                if d < bd:
                    bd = d
                    best = i
        else:
            for k in range(-10, 11):
                i = (hint + k) % N
                dx = px[i] - x
                dz = pz[i] - z
                d = dx * dx + dz * dz
                if d < bd:
                    bd = d
                    best = i
        a = best
        b = (best + 1) % N
        ex = px[b] - px[a]
        ez = pz[b] - pz[a]
        t = ((x - px[a]) * ex + (z - pz[a]) * ez) / (ex * ex + ez * ez)
        if t < 0:
            a = (best - 1) % N
            b = best
            ex = px[b] - px[a]
            ez = pz[b] - pz[a]
            t = ((x - px[a]) * ex + (z - pz[a]) * ez) / (ex * ex + ez * ez)
        t = 0.0 if t < 0 else (1.0 if t > 1 else t)
        py, tx, ty, tz, rxs, rzs, bank = self.py, self.tx, self.ty, self.tz, self.rx, self.rz, self.bank
        cx = px[a] + (px[b] - px[a]) * t
        cz = pz[a] + (pz[b] - pz[a]) * t
        cy = py[a] + (py[b] - py[a]) * t
        rx = rxs[a] + (rxs[b] - rxs[a]) * t
        rz = rzs[a] + (rzs[b] - rzs[a]) * t
        rl = math.hypot(rx, rz) or 1.0
        rx /= rl
        rz /= rl
        ttx = tx[a] + (tx[b] - tx[a]) * t
        ttz = tz[a] + (tz[b] - tz[a]) * t
        tl = math.hypot(ttx, ttz) or 1.0
        bk = bank[a] + (bank[b] - bank[a]) * t
        d = (x - cx) * rx + (z - cz) * rz
        hw = self.hw
        o.idx = a
        o.t = t
        o.prog = a + t
        o.d = d
        o.rx = rx
        o.rz = rz
        o.tx = ttx / tl
        o.tz = ttz / tl
        o.ty = ty[a] + (ty[b] - ty[a]) * t
        o.bank = bk
        o.cx = cx
        o.cy = cy
        o.cz = cz
        o.y = cy - math.sin(bk) * (-hw if d < -hw else (hw if d > hw else d)) + self.dy_at(d)
        return o

    def pose_at(self, pf, d=0.0):
        """실수 인덱스 pf, 가로 오프셋 d 의 (x, y, z, heading)"""
        N = self.N
        i = int(math.floor(pf))
        t = pf - i
        a = i % N
        b = (a + 1) % N
        rx = self.rx[a] + (self.rx[b] - self.rx[a]) * t
        rz = self.rz[a] + (self.rz[b] - self.rz[a]) * t
        rl = math.hypot(rx, rz) or 1.0
        rx /= rl
        rz /= rl
        tx = self.tx[a] + (self.tx[b] - self.tx[a]) * t
        tz = self.tz[a] + (self.tz[b] - self.tz[a]) * t
        bk = self.bank[a] + (self.bank[b] - self.bank[a]) * t
        x = self.px[a] + (self.px[b] - self.px[a]) * t + rx * d
        z = self.pz[a] + (self.pz[b] - self.pz[a]) * t + rz * d
        y = self.py[a] + (self.py[b] - self.py[a]) * t - math.sin(bk) * clamp(d, -self.hw, self.hw)
        return x, y, z, math.atan2(tx, tz)

    def spawn_pose(self, slot):
        row = slot // 2
        col = slot % 2
        back = 3.0 + row * 4.6
        d = (1 if col else -1) * self.width * 0.2
        x, y, z, h = self.pose_at(self.N - back / self.ds, d)
        return dict(x=x, y=y, z=z, heading=h, prog=-back / self.ds)

    def surface_normal(self, i):
        """샘플 i 의 도로 법선 (월드 좌표계, 길이 1)"""
        i %= self.N
        cb = math.cos(self.bank[i])
        sb = math.sin(self.bank[i])
        rbx, rby, rbz = self.rx[i] * cb, -sb, self.rz[i] * cb
        tx, ty, tz = self.tx[i], self.ty[i], self.tz[i]
        nx = rby * tz - rbz * ty
        ny = rbz * tx - rbx * tz
        nz = rbx * ty - rby * tx
        l = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        return nx / l, ny / l, nz / l

    def edge_point(self, i, off):
        """샘플 i 에서 가로 오프셋 off(+오른쪽)의 지면 좌표 (x, y, z) - 비탈 포함"""
        i %= self.N
        hw = self.hw
        o = -hw if off < -hw else (hw if off > hw else off)
        return (self.px[i] + self.rx[i] * off,
                self.py[i] - math.sin(self.bank[i]) * o + self.dy_at(off),
                self.pz[i] + self.rz[i] * off)


# ----------------------------------------------------------------------------
#  아케이드 카트 물리 + AI
# ----------------------------------------------------------------------------
DRIFT_BOOST = (0.0, 0.7, 1.2, 1.9)


class KartSim(object):
    def __init__(self, track, kart_id, slot=0):
        self.track = track
        self.kart_id = kart_id
        self.stats = kart_stats(kart_id)
        self.q = Q()
        self.reset(track.spawn_pose(slot))

    def reset(self, pose):
        t = self.track
        self.x = pose['x']
        self.z = pose['z']
        self.heading = pose['heading']
        self.vx = 0.0
        self.vz = 0.0
        self.speed = 0.0
        self.drifting = False
        self.drift_dir = 0.0
        self.drift_charge = 0.0
        self.drift_tier = 0
        self.boost_t = 0.0
        self.offroad = False
        self.wall_hit = 0.0
        self.steer_vis = 0.0
        self.slip = 0.0
        self.armed = True
        self.pad_cool = 0.0
        t.query(self.x, self.z, -1, self.q)
        self.y = self.q.y
        self.hint = self.q.idx
        self.last_prog = self.q.prog
        self.total = pose.get('prog', 0.0)
        self.d = self.q.d
        self.upx, self.upy, self.upz = 0.0, 1.0, 0.0
        self.finished = False
        self.events = []
        self.wrong_way = False

    @property
    def lap(self):
        return max(1, int(math.floor(self.total / self.track.N)) + 1)

    def respawn(self):
        t = self.track
        q = self.q
        i = q.idx
        self.x = t.px[i]
        self.z = t.pz[i]
        self.heading = math.atan2(t.tx[i], t.tz[i])
        self.vx = self.vz = self.speed = 0.0
        self.drifting = False
        self.drift_charge = 0.0
        self.drift_tier = 0
        self.boost_t = 0.0
        t.query(self.x, self.z, -1, q)
        self.y = q.y
        self.hint = q.idx
        self.last_prog = q.prog

    def update(self, dt, inp, others):
        s = self.stats
        t = self.track
        q = self.q
        ev = self.events
        del ev[:]
        sin, cos, exp = math.sin, math.cos, math.exp
        fx = sin(self.heading)
        fz = cos(self.heading)
        rx = -fz
        rz = fx
        vf = self.vx * fx + self.vz * fz
        vl = self.vx * rx + self.vz * rz
        boosting = self.boost_t > 0
        if boosting:
            self.boost_t -= dt
        maxs = s['max_speed']
        cap = maxs * (0.55 if self.offroad else 1.0) + (24.0 if boosting else 0.0)
        thr = inp['throttle']
        brk = inp['brake']
        steer = inp['steer']
        if thr > 0.01:
            if vf < cap:
                vf += s['accel_rate'] * (2.6 if boosting else 1.0) * thr * (1 - 0.75 * max(0.0, vf) / cap) * dt
            else:
                vf -= 26 * dt
        if brk > 0.01:
            if vf > 1:
                vf -= 44 * brk * dt
            else:
                vf = max(-16.0, vf - 16 * brk * dt)
        elif thr < 0.01:
            vf -= sign(vf) * min(abs(vf), 7 * dt)
        vf *= exp(-(0.9 if self.offroad else 0.04) * dt)
        along = self.vx * q.tx + self.vz * q.tz
        vf -= 4.4 * q.ty * (1.0 if along >= 0 else -1.0) * dt     # 오르막은 느려지고 내리막은 빨라짐

        # 드리프트
        want = inp['drift'] and abs(steer) > 0.25 and vf > 22 and not self.offroad
        if not inp['drift']:
            self.armed = True
        if not self.drifting and want and self.armed:
            self.armed = False
            self.drifting = True
            self.drift_dir = sign(steer)
            self.drift_charge = 0.0
            ev.append('driftStart')
        if self.drifting:
            if (not inp['drift']) or vf < 16:
                tier = self.drift_tier
                if tier > 0:
                    self.boost_t = max(self.boost_t, DRIFT_BOOST[tier])
                    ev.append('miniturbo')
                self.drifting = False
                self.drift_charge = 0.0
                self.drift_tier = 0
            else:
                self.drift_charge += dt * (0.75 + 0.5 * (1.0 if steer * self.drift_dir > 0 else 0.4))
                c = self.drift_charge
                tier = 3 if c > 3.2 else (2 if c > 1.9 else (1 if c > 0.9 else 0))
                if tier > self.drift_tier:
                    ev.append('tier%d' % tier)
                self.drift_tier = tier

        # 조향
        speed_f = clamp(abs(vf) / 14.0, 0.0, 1.0) * (1 - 0.3 * clamp(abs(vf) / maxs, 0.0, 1.0))
        if self.drifting:
            yaw = s['turn_rate'] * (0.55 * self.drift_dir + 0.6 * steer * (0.75 if steer * self.drift_dir > 0 else 1.0)) * 1.15
        else:
            yaw = s['turn_rate'] * steer
        self.heading -= yaw * speed_f * (1.0 if vf >= 0 else -1.0) * dt
        self.steer_vis += (steer - self.steer_vis) * min(1.0, dt * 10)
        grip = s['drift_grip'] if self.drifting else (7.0 if boosting else 9.5)
        vl *= exp(-grip * dt)
        self.slip = vl
        nfx = sin(self.heading)
        nfz = cos(self.heading)
        self.vx = nfx * vf + (-nfz) * vl
        self.vz = nfz * vf + nfx * vl
        self.x += self.vx * dt
        self.z += self.vz * dt

        # 다른 카트와 충돌 (원)
        for o in others:
            dx = self.x - o[0]
            dz = self.z - o[1]
            dist = math.hypot(dx, dz)
            if 0.001 < dist < 2.5:
                push = (2.5 - dist) / dist * 0.55
                self.x += dx * push
                self.z += dz * push
                rel = (self.vx - o[2]) * dx / dist + (self.vz - o[3]) * dz / dist
                if rel < 0:
                    self.vx -= dx / dist * rel * 0.9
                    self.vz -= dz / dist * rel * 0.9
                    ev.append('bump')

        # 트랙 질의 + 벽
        t.query(self.x, self.z, self.hint, q)
        self.hint = q.idx
        lim = t.wall_off - 1.0
        if abs(q.d) > lim:
            sg = sign(q.d)
            over = abs(q.d) - lim
            self.x -= q.rx * over * sg
            self.z -= q.rz * over * sg
            vn = (self.vx * q.rx + self.vz * q.rz) * sg
            if vn > 0:
                self.vx -= q.rx * sg * vn * 1.35
                self.vz -= q.rz * sg * vn * 1.35
                k = 1 - clamp(vn / 80.0, 0.04, 0.2)
                self.vx *= k
                self.vz *= k
                if vn > 6:
                    self.wall_hit = 1.0
                    ev.append('wall')
                if self.drifting:
                    self.drifting = False
                    self.drift_charge = 0.0
                    self.drift_tier = 0
            t.query(self.x, self.z, self.hint, q)
        self.d = q.d
        self.offroad = abs(q.d) > t.hw + 0.4
        self.wall_hit = max(0.0, self.wall_hit - dt * 4)

        # 부스트 패드
        if self.pad_cool > 0:
            self.pad_cool -= dt
        elif t.pads:
            N = t.N
            for p in t.pads:
                di = q.prog - p['idx']
                if di > N / 2:
                    di -= N
                elif di < -N / 2:
                    di += N
                if abs(di * t.ds) < p['half_len'] and abs(q.d - p['d']) < p['half_w']:
                    self.boost_t = max(self.boost_t, 1.5)
                    ev.append('pad')
                    f = math.hypot(self.vx, self.vz)
                    if f < maxs:
                        k = 0.5 * maxs / max(f, 1.0) + 0.5
                        self.vx *= k
                        self.vz *= k
                    self.pad_cool = 0.6
                    break

        # 지면 높이/방향
        self.y = q.y
        cb = cos(q.bank)
        sb = sin(q.bank)
        rbx, rby, rbz = q.rx * cb, -sb, q.rz * cb
        tyy = q.ty
        ux = rby * q.tz - rbz * tyy
        uy = rbz * q.tx - rbx * q.tz
        uz = rbx * tyy - rby * q.tx
        ul = math.sqrt(ux * ux + uy * uy + uz * uz) or 1.0
        k = min(1.0, dt * 8)
        self.upx += (ux / ul - self.upx) * k
        self.upy += (uy / ul - self.upy) * k
        self.upz += (uz / ul - self.upz) * k

        # 진행도
        delta = q.prog - self.last_prog
        N = t.N
        if delta > N / 2:
            delta -= N
        elif delta < -N / 2:
            delta += N
        self.total += delta
        self.last_prog = q.prog
        self.speed = math.hypot(self.vx, self.vz)
        fwd = self.vx * q.tx + self.vz * q.tz
        self.wrong_way = self.speed > 8 and fwd < -4 and cos(wrap_pi(self.heading - math.atan2(q.tx, q.tz))) < -0.3


class BotBrain(object):
    def __init__(self, rand):
        self.skill = 0.82 + rand() * 0.2
        self.lane = (rand() - 0.5) * 0.7
        self.phase = rand() * 6.28
        self.t = 0.0
        self.stuck = 0.0

    def drive(self, kart, dt, player_total, rubber=True):
        tr = kart.track
        q = kart.q
        N = tr.N
        self.t += dt
        look = int(clamp(round((kart.speed * 0.5 + 12) / tr.ds), 5, 34))
        lane = (self.lane + math.sin(self.t * 0.35 + self.phase) * 0.12) * tr.width * 0.5
        i = (q.idx + look) % N
        tx = tr.px[i] + tr.rx[i] * lane
        tz = tr.pz[i] + tr.rz[i] * lane
        want = math.atan2(tx - kart.x, tz - kart.z)
        diff = wrap_pi(want - kart.heading)
        steer = clamp(-diff * 2.2, -1.0, 1.0)
        rb = 1.0
        if rubber and player_total is not None:
            gap = (kart.total - player_total) * tr.ds
            rb = clamp(1 - gap / 900.0, 0.9, 1.08)
        curve = tr.turn[q.idx]
        target = kart.stats['max_speed'] * self.skill * rb * (1 - clamp(curve * 0.55 - 0.08, 0.0, 0.5))
        sp = kart.speed
        inp = {'steer': steer, 'throttle': 1.0 if sp < target else 0.15, 'brake': 0.7 if sp > target + 7 else 0.0, 'drift': False}
        if curve > 0.55 and sp > 36 and self.skill > 0.9 and abs(steer) > 0.45:
            inp['drift'] = True
        if sp < 2:
            self.stuck += dt
            if self.stuck > 2.5:
                kart.respawn()
                self.stuck = 0.0
        else:
            self.stuck = 0.0
        return inp


# ----------------------------------------------------------------------------
#  레이스 진행 (솔로/멀티 공통): 카운트다운, 시뮬레이션, 순위, 네트워크 동기화
# ----------------------------------------------------------------------------
class Racer(object):
    """레이스 참가자 한 명 (플레이어/봇/원격 플레이어). 렌더러는 이 객체의 값만 읽으면 된다."""

    def __init__(self, rid, name, kart_id, slot, kind):
        self.id = rid
        self.name = name
        self.kart_id = kart_id
        self.slot = slot
        self.kind = kind            # 'local' | 'bot' | 'remote'
        self.sim = None
        self.brain = None
        self.finished = False
        self.finish_time = 0.0
        self.cur = None
        self.tgt = None
        # ---- 렌더링용 상태 ----
        self.x = self.y = self.z = 0.0
        self.h = 0.0
        self.speed = 0.0
        self.total = 0.0
        self.vx = self.vz = 0.0
        self.drifting = False
        self.tier = 0
        self.drift_dir = 0.0
        self.boosting = False
        self.steer = 0.0
        self.slip = 0.0
        self.up = (0.0, 1.0, 0.0)
        self.idx = 0
        self.offroad = False
        self.wall_hit = 0.0

    def sync_visual(self, track, dt):
        s = self.sim
        if s is not None:
            self.x, self.y, self.z, self.h = s.x, s.y, s.z, s.heading
            self.speed = s.speed
            self.total = s.total
            self.vx, self.vz = s.vx, s.vz
            self.drifting = s.drifting
            self.tier = s.drift_tier
            self.drift_dir = s.drift_dir
            self.boosting = s.boost_t > 0
            self.steer = s.steer_vis
            self.slip = s.slip
            self.up = (s.upx, s.upy, s.upz)
            self.idx = s.q.idx
            self.offroad = s.offroad
            self.wall_hit = s.wall_hit
            return
        c, t = self.cur, self.tgt
        f = 1.0 - math.exp(-14.0 * dt)
        c['x'] += (t['x'] - c['x']) * f
        c['y'] += (t['y'] - c['y']) * f
        c['z'] += (t['z'] - c['z']) * f
        dh = wrap_pi(t['h'] - c['h'])
        c['h'] += dh * f
        c['sp'] += (t['sp'] - c['sp']) * f
        c['total'] += (t['total'] - c['total']) * f
        self.x, self.y, self.z, self.h = c['x'], c['y'], c['z'], c['h']
        self.speed = c['sp']
        self.total = c['total']
        self.vx = math.sin(self.h) * self.speed
        self.vz = math.cos(self.h) * self.speed
        self.drifting = t['dr'] > 0
        self.tier = max(0, t['dr'] - 1)
        self.boosting = t['bo'] > 0
        self.steer = clamp(-dh * 2.0, -1.0, 1.0)
        if self.drifting:
            self.drift_dir = sign(self.steer) or self.drift_dir
        self.slip = 0.0
        self.idx = int(round(self.total)) % track.N
        self.up = track.surface_normal(self.idx)


class Race(object):
    def __init__(self, map_id, laps, entries, multi=False, is_host=True, countdown=5.0, net=None, auto_local=False):
        self.map_id = map_id
        self.track = Track(map_id)
        self.laps = laps
        self.multi = multi
        self.is_host = is_host
        self.net = net
        self.racers = []
        self.local = None
        rnd = Rng(map_id * 31 + 7)
        for e in entries:
            rc = Racer(e['id'], e['name'], e['kart'], e['slot'], e['kind'])
            if rc.kind != 'remote':
                rc.sim = KartSim(self.track, rc.kart_id, rc.slot)
                rc.total = rc.sim.total
            else:
                p = self.track.spawn_pose(rc.slot)
                rc.cur = dict(x=p['x'], y=p['y'], z=p['z'], h=p['heading'], sp=0.0, total=p['prog'])
                rc.tgt = dict(rc.cur, dr=0, bo=0)
            if rc.kind == 'bot':
                rc.brain = BotBrain(rnd)
            if rc.kind == 'local':
                self.local = rc
                if auto_local:
                    rc.brain = BotBrain(rnd)
            rc.sync_visual(self.track, 0.0)
            self.racers.append(rc)
        self.start_at = time.monotonic() + countdown
        self.countdown = countdown
        self.phase = 'count'          # count -> run
        self.t = 0.0
        self.acc = 0.0
        self.last_count = 99
        self.last_lap = 1
        self.events = []
        self.finish_order = []
        self.send_t = 0.0
        self.auto_local = auto_local
        self.count_left = countdown

    # ---- 진행 --------------------------------------------------------------
    def update(self, dt, inp):
        """프레임마다 호출. inp = {'steer','throttle','brake','drift'} (로컬 플레이어 입력)"""
        self.events = []
        dt = min(dt, 0.1)
        if self.phase == 'count':
            left = self.start_at - time.monotonic()
            self.count_left = left
            if left <= 0:
                self.phase = 'run'
                self.t = 0.0
                self.events.append(('go',))
            else:
                n = int(math.ceil(left))
                if n != self.last_count:
                    self.last_count = n
                    self.events.append(('count', n))
        self.acc += dt
        steps = 0
        while self.acc >= STEP and steps < 6:
            self._step(STEP, inp)
            self.acc -= STEP
            steps += 1
        if steps >= 6:
            self.acc = 0.0
        for rc in self.racers:
            rc.sync_visual(self.track, dt)
        self._net_tick(dt)

    def _step(self, dt, inp):
        running = self.phase == 'run'
        racers = self.racers
        N = self.track.N
        others_all = [(r.x, r.z, r.vx, r.vz) for r in racers]
        zero = {'steer': 0.0, 'throttle': 0.0, 'brake': 0.0, 'drift': False}
        for k, rc in enumerate(racers):
            sim = rc.sim
            if sim is None:
                continue
            if not running:
                use = zero
            elif rc.kind == 'local' and not rc.finished and not self.auto_local:
                use = inp
            else:
                if rc.brain is None:
                    rc.brain = BotBrain(Rng(5))
                loc = self.local
                use = rc.brain.drive(sim, dt, loc.total if loc is not None else None, not self.multi)
            if not running:
                sim.vx *= 0.9
                sim.vz *= 0.9
            others = others_all[:k] + others_all[k + 1:]
            sim.update(dt, use, others)
            # 다음 서브스텝에서 쓸 위치 갱신
            others_all[k] = (sim.x, sim.z, sim.vx, sim.vz)
            rc.total = sim.total
            if running:
                if not rc.finished and sim.total >= self.laps * N:
                    rc.finished = True
                    rc.finish_time = self.t
                    sim.finished = True
                    self.finish_order.append(rc)
                    if rc.kind == 'local':
                        self.events.append(('finish',))
                        if self.net is not None and self.multi:
                            self.net.send({'t': 'fin', 'time': round(rc.finish_time, 2)})
            if rc.kind == 'local':
                for e in sim.events:
                    self.events.append(('sim', e))
                lap = min(self.laps, sim.lap)
                if lap > self.last_lap and running:
                    self.events.append(('lap', lap, lap == self.laps))
                    self.last_lap = lap
        if running:
            self.t += dt

    def respawn_local(self):
        if self.local is not None and self.local.sim is not None and self.phase == 'run':
            self.local.sim.respawn()

    def ranking(self):
        def key(r):
            return (1e9 - r.finish_time) if r.finished else r.total
        return sorted(self.racers, key=key, reverse=True)

    def local_finished(self):
        return self.local is not None and self.local.finished

    # ---- 네트워크 -----------------------------------------------------------
    def _net_tick(self, dt):
        net = self.net
        if not self.multi or net is None or not net.connected or self.local is None:
            return
        self.send_t += dt
        if self.send_t < 0.05:
            return
        self.send_t = 0.0
        s = self.local.sim
        net.send({'t': 's', 'x': round(s.x, 2), 'y': round(s.y, 2), 'z': round(s.z, 2), 'h': round(s.heading, 3), 'sp': round(s.speed, 1),
                  'tp': round(s.total, 2), 'dr': (s.drift_tier + 1) if s.drifting else 0, 'bo': 1 if s.boost_t > 0 else 0})
        if self.is_host:
            bots = []
            for rc in self.racers:
                if rc.kind == 'bot':
                    b = rc.sim
                    bots.append([rc.id, round(b.x, 2), round(b.y, 2), round(b.z, 2), round(b.heading, 3), round(b.speed, 1), round(b.total, 2),
                                 (b.drift_tier + 1) if b.drifting else 0, 1 if b.boost_t > 0 else 0, round(rc.finish_time, 2) if rc.finished else 0])
            if bots:
                net.send({'t': 'b', 'b': bots})

    def _find(self, rid):
        for rc in self.racers:
            if rc.id == rid:
                return rc
        return None

    def handle_message(self, m):
        t = m.get('t')
        if t == 's':
            rc = self._find(m.get('id'))
            if rc is not None and rc.tgt is not None:
                rc.tgt.update(x=m['x'], y=m['y'], z=m['z'], h=m['h'], sp=m['sp'], total=m['tp'], dr=m['dr'], bo=m['bo'])
        elif t == 'b':
            for a in m.get('b', []):
                rc = self._find(a[0])
                if rc is not None and rc.tgt is not None:
                    rc.tgt.update(x=a[1], y=a[2], z=a[3], h=a[4], sp=a[5], total=a[6], dr=a[7], bo=a[8])
                    if a[9] and not rc.finished:
                        rc.finished = True
                        rc.finish_time = a[9]
        elif t == 'fin':
            rc = self._find(m.get('id'))
            if rc is not None and not rc.finished:
                rc.finished = True
                rc.finish_time = float(m.get('time', self.t))
                self.events.append(('fin', rc.name))
        elif t == 'left':
            rc = self._find(m.get('id'))
            if rc is not None:
                self.racers.remove(rc)
                self.events.append(('left', rc.name))


def solo_entries(name, kart_id, bots, seed=None):
    rnd = Rng(seed if seed is not None else (int(time.time() * 1000) & 0xFFFFFFFF))
    me = int(bots * 0.6)
    entries = []
    n = 0
    for i in range(bots + 1):
        if i == me:
            entries.append(dict(id='me', name=name, kart=kart_id, slot=i, kind='local'))
        else:
            n += 1
            entries.append(dict(id='b%d' % i, name='BOT %d' % n, kart=int(rnd() * KART_COUNT), slot=i, kind='bot'))
    return entries


# ----------------------------------------------------------------------------
#  WiFi(LAN) 멀티플레이: 방 서버 + 클라이언트 + 자동 탐색   (표준 라이브러리만 사용)
#  프로토콜: TCP, 줄 단위 JSON.  폰(Pydroid3) 버전과 PC 버전이 같은 방에서 함께 달릴 수 있다.
# ----------------------------------------------------------------------------
def local_ips():
    ips = []
    for target in (('10.255.255.255', 1), ('8.8.8.8', 80)):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(target)
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith('127.') and ip not in ips:
                ips.append(ip)
        except Exception:
            pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith('127.') and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips


def hard_close(sock):
    """다른 스레드가 recv 중이어도 즉시 연결을 끊는다 (shutdown 후 close)"""
    if sock is None:
        return
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass
    try:
        sock.close()
    except Exception:
        pass


class _Conn(object):
    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
        self.id = None
        self.name = ''
        self.kart = 0
        self.lock = threading.Lock()
        self.alive = True

    def send_raw(self, data):
        if not self.alive:
            return
        try:
            with self.lock:
                self.sock.sendall(data)
        except Exception:
            self.alive = False

    def send_obj(self, obj):
        self.send_raw((json.dumps(obj, separators=(',', ':')) + '\n').encode('utf-8'))


class RoomServer(object):
    """방 하나를 관리하는 서버. 호스트 플레이어의 앱 안에서 돌거나 `--serve` 로 단독 실행."""
    MAX_PLAYERS = 12

    def __init__(self, port=DEFAULT_PORT, name='KART3D'):
        self.port = port
        self.name = name
        self.conns = {}
        self.lock = threading.RLock()
        self.host_id = None
        self.map = 1
        self.laps = 3
        self.bots = 0
        self.state = 'lobby'
        self.next_id = 1
        self.running = False
        self.srv = None
        self.udp = None

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.port))
        s.listen(16)
        self.srv = s
        self.running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()
        self._start_discovery()
        return self

    def stop(self):
        self.running = False
        for sock in (self.srv, self.udp):
            try:
                if sock is not None:
                    sock.close()
            except Exception:
                pass
        with self.lock:
            conns = list(self.conns.values())
        for c in conns:
            c.alive = False
            hard_close(c.sock)

    # ---- LAN 탐색 응답 --------------------------------------------------------
    def _start_discovery(self):
        try:
            u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            u.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            u.bind(('', DISC_PORT))
            self.udp = u
            threading.Thread(target=self._disc_loop, daemon=True).start()
        except Exception:
            self.udp = None

    def _disc_loop(self):
        while self.running:
            try:
                data, addr = self.udp.recvfrom(512)
            except Exception:
                break
            if data.startswith(b'KART3D?'):
                with self.lock:
                    info = {'game': 'kart3d', 'name': self.name, 'port': self.port, 'map': self.map,
                            'players': len(self.conns), 'state': self.state}
                try:
                    self.udp.sendto(json.dumps(info).encode('utf-8'), addr)
                except Exception:
                    pass

    # ---- 접속 처리 ------------------------------------------------------------
    def _accept_loop(self):
        while self.running:
            try:
                sock, addr = self.srv.accept()
            except Exception:
                break
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(5.0)
            except Exception:
                pass
            threading.Thread(target=self._client_loop, args=(_Conn(sock, addr),), daemon=True).start()

    def _client_loop(self, c):
        buf = b''
        try:
            while self.running and c.alive:
                try:
                    data = c.sock.recv(8192)
                except socket.timeout:
                    continue
                if not data:
                    break
                buf += data
                while True:
                    k = buf.find(b'\n')
                    if k < 0:
                        break
                    line = buf[:k]
                    buf = buf[k + 1:]
                    if not line.strip():
                        continue
                    try:
                        m = json.loads(line.decode('utf-8'))
                    except Exception:
                        continue
                    if isinstance(m, dict):
                        self._handle(c, m)
        except Exception:
            pass
        finally:
            self._drop(c)

    def _room_msg(self):
        with self.lock:
            return {'t': 'room', 'host': self.host_id, 'map': self.map, 'laps': self.laps, 'bots': self.bots, 'state': self.state,
                    'players': [{'id': c.id, 'name': c.name, 'kart': c.kart} for c in self.conns.values()]}

    def _broadcast(self, obj, exclude=None):
        data = (json.dumps(obj, separators=(',', ':')) + '\n').encode('utf-8')
        with self.lock:
            targets = [c for c in self.conns.values() if c.id != exclude]
        for c in targets:
            c.send_raw(data)

    def _drop(self, c):
        hard_close(c.sock)
        c.alive = False
        with self.lock:
            if c.id is None or c.id not in self.conns:
                return
            del self.conns[c.id]
            if self.host_id == c.id:
                self.host_id = next(iter(self.conns), None)
            if not self.conns:
                self.state = 'lobby'
        self._broadcast({'t': 'left', 'id': c.id})
        self._broadcast(self._room_msg())

    def _handle(self, c, m):
        t = m.get('t')
        if t == 'join':
            with self.lock:
                if c.id is not None:
                    return
                if self.state != 'lobby':
                    c.send_obj({'t': 'error', 'msg': 'race in progress'})
                    return
                if len(self.conns) >= self.MAX_PLAYERS:
                    c.send_obj({'t': 'error', 'msg': 'room full'})
                    return
                c.id = 'p%d' % self.next_id
                self.next_id += 1
                c.name = str(m.get('name') or 'Racer')[:14]
                c.kart = int(m.get('kart', 0)) % KART_COUNT
                self.conns[c.id] = c
                if self.host_id is None:
                    self.host_id = c.id
            c.send_obj({'t': 'welcome', 'id': c.id})
            self._broadcast(self._room_msg())
            return
        if c.id is None:
            return
        if t in ('s', 'b', 'fin'):
            m['id'] = c.id
            self._broadcast(m, exclude=c.id)
        elif t == 'profile':
            c.name = str(m.get('name') or c.name)[:14]
            c.kart = int(m.get('kart', c.kart)) % KART_COUNT
            self._broadcast(self._room_msg())
        elif t == 'settings':
            if self.host_id == c.id and self.state == 'lobby':
                if 'map' in m:
                    self.map = int(clamp(int(m['map']), 1, MAP_COUNT))
                if 'laps' in m:
                    self.laps = int(clamp(int(m['laps']), 1, 10))
                if 'bots' in m:
                    self.bots = int(clamp(int(m['bots']), 0, self.MAX_PLAYERS - 1))
                self._broadcast(self._room_msg())
        elif t == 'start':
            if self.host_id == c.id and self.state == 'lobby':
                import random
                with self.lock:
                    self.state = 'racing'
                    order = [{'id': p.id, 'name': p.name, 'kart': p.kart} for p in self.conns.values()]
                    random.shuffle(order)
                    for i, p in enumerate(order):
                        p['slot'] = i
                    bots = []
                    for i in range(min(self.bots, self.MAX_PLAYERS - len(order))):
                        bots.append({'id': 'b%d' % (i + 1), 'name': 'BOT %d' % (i + 1), 'kart': random.randrange(KART_COUNT), 'slot': len(order) + i})
                    msg = {'t': 'start', 'map': self.map, 'laps': self.laps, 'countdown': 5.0, 'players': order, 'bots': bots}
                self._broadcast(msg)
        elif t == 'lobby':
            if self.host_id == c.id:
                with self.lock:
                    self.state = 'lobby'
                self._broadcast(self._room_msg())
                self._broadcast({'t': 'tolobby'})


class NetClient(object):
    def __init__(self):
        self.sock = None
        self.q = queue.Queue()
        self.connected = False
        self.status = 'idle'      # idle | connecting | connected | failed | closed
        self.error = ''
        self.id = None
        self._lock = threading.Lock()
        self._closing = False

    def connect_async(self, host, port, timeout=4.0):
        self.status = 'connecting'
        threading.Thread(target=self._connect, args=(host, port, timeout), daemon=True).start()

    def _connect(self, host, port, timeout):
        try:
            s = socket.create_connection((host, int(port)), timeout=timeout)
            try:
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except Exception:
                pass
            s.settimeout(2.0)
        except Exception as e:
            self.status = 'failed'
            self.error = str(e)
            return
        self.sock = s
        self.connected = True
        self.status = 'connected'
        self._read_loop()

    def _read_loop(self):
        buf = b''
        try:
            while self.connected:
                try:
                    data = self.sock.recv(8192)
                except socket.timeout:
                    continue
                if not data:
                    break
                buf += data
                while True:
                    k = buf.find(b'\n')
                    if k < 0:
                        break
                    line = buf[:k]
                    buf = buf[k + 1:]
                    if not line.strip():
                        continue
                    try:
                        self.q.put(json.loads(line.decode('utf-8')))
                    except Exception:
                        pass
        except Exception:
            pass
        finally:
            was = self.connected
            self.connected = False
            if was and not self._closing:
                self.status = 'closed'
                self.q.put({'t': 'close'})

    def send(self, obj):
        if not self.connected or self.sock is None:
            return
        data = (json.dumps(obj, separators=(',', ':')) + '\n').encode('utf-8')
        try:
            with self._lock:
                self.sock.sendall(data)
        except Exception:
            self.connected = False

    def poll(self):
        out = []
        while True:
            try:
                out.append(self.q.get_nowait())
            except queue.Empty:
                break
        return out

    def close(self):
        self._closing = True
        self.connected = False
        hard_close(self.sock)


def discover(timeout=1.3):
    """같은 WiFi 안에서 열려 있는 방을 UDP 브로드캐스트로 찾는다."""
    found = {}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(0.2)
        targets = ['255.255.255.255']
        for ip in local_ips():
            parts = ip.split('.')
            if len(parts) == 4:
                bc = '.'.join(parts[:3] + ['255'])
                if bc not in targets:
                    targets.append(bc)
        end = time.time() + timeout
        last = 0.0
        while time.time() < end:
            if time.time() - last > 0.4:
                for tg in targets:
                    try:
                        s.sendto(b'KART3D?', (tg, DISC_PORT))
                    except Exception:
                        pass
                last = time.time()
            try:
                data, addr = s.recvfrom(1024)
            except socket.timeout:
                continue
            except Exception:
                break
            try:
                info = json.loads(data.decode('utf-8'))
            except Exception:
                continue
            if isinstance(info, dict) and info.get('game') == 'kart3d':
                d = dict(info)
                d['ip'] = addr[0]
                found[(addr[0], d.get('port', DEFAULT_PORT))] = d
        s.close()
    except Exception:
        pass
    return list(found.values())


def discover_async(result):
    """result 는 dict. result['busy'], result['rooms'] 를 UI 가 읽는다."""
    def run():
        result['busy'] = True
        result['rooms'] = discover()
        result['busy'] = False
        result['done'] = True
    result['busy'] = True
    result['done'] = False
    threading.Thread(target=run, daemon=True).start()


class Session(object):
    """로비/접속 상태를 관리하는 얇은 계층. UI 는 이 객체의 필드만 읽고 메서드만 부른다."""

    def __init__(self, profile):
        self.profile = profile
        self.reset()

    def reset(self):
        self.net = None
        self.server = None
        self.state = 'idle'       # idle | connecting | lobby | racing
        self.error = ''
        self.my_id = None
        self.host_id = None
        self.players = []
        self.settings = {'map': 1, 'laps': 3, 'bots': 0}
        self.start_msg = None
        self.address = ''
        self._joined = False

    @property
    def is_host(self):
        return self.my_id is not None and self.my_id == self.host_id

    def host_game(self, port=DEFAULT_PORT):
        self.leave()
        try:
            self.server = RoomServer(port, name=self.profile.display_name()).start()
            self.server.map = int(self.profile['map'])
            self.server.laps = int(self.profile['laps'])
        except Exception as e:
            self.server = None
            self.error = 'server: %s' % e
            return False
        self._connect('127.0.0.1', port)
        return True

    def join_game(self, ip, port=DEFAULT_PORT):
        self.leave()
        self._connect(ip, port)

    def _connect(self, ip, port):
        self.net = NetClient()
        self.net.connect_async(ip, port)
        self.state = 'connecting'
        self.address = ip
        self.error = ''
        self._joined = False

    def pump(self):
        """매 프레임 호출. 레이스 중 메시지(s/b/fin/left/tolobby)를 돌려준다."""
        out = []
        net = self.net
        if net is None:
            return out
        if self.state == 'connecting':
            if net.status == 'connected' and not self._joined:
                self._joined = True
                net.send({'t': 'join', 'name': self.profile.display_name(), 'kart': self.profile['kart']})
            elif net.status == 'failed':
                self.error = net.error or 'connect failed'
                self.leave()
                return out
        for m in net.poll():
            t = m.get('t')
            if t == 'welcome':
                self.my_id = m.get('id')
            elif t == 'room':
                self.host_id = m.get('host')
                self.players = m.get('players', [])
                self.settings = {'map': m.get('map', 1), 'laps': m.get('laps', 3), 'bots': m.get('bots', 0)}
                if self.state in ('connecting', 'idle'):
                    self.state = 'lobby'
            elif t == 'start':
                self.start_msg = m
                self.state = 'racing'
            elif t == 'tolobby':
                self.state = 'lobby'
                out.append(m)
            elif t == 'error':
                self.error = str(m.get('msg', 'error'))
                self.leave()
                return out
            elif t == 'close':
                self.error = 'disconnected'
                self.leave()
                return out
            else:
                out.append(m)
        return out

    def send_settings(self, **kw):
        if self.net is not None and self.is_host:
            msg = {'t': 'settings'}
            msg.update(kw)
            self.net.send(msg)

    def send_profile(self):
        if self.net is not None and self.state in ('lobby',):
            self.net.send({'t': 'profile', 'name': self.profile.display_name(), 'kart': self.profile['kart']})

    def start_race(self):
        if self.net is not None and self.is_host:
            self.net.send({'t': 'start'})

    def back_to_lobby(self):
        if self.net is not None and self.is_host:
            self.net.send({'t': 'lobby'})

    def entries_from_start(self, m):
        is_host = self.is_host
        entries = []
        for p in m.get('players', []):
            entries.append(dict(id=p['id'], name=p['name'], kart=p['kart'], slot=p['slot'], kind='local' if p['id'] == self.my_id else 'remote'))
        for b in m.get('bots', []):
            entries.append(dict(id=b['id'], name=b['name'], kart=b['kart'], slot=b['slot'], kind='bot' if is_host else 'remote'))
        return entries

    def leave(self):
        try:
            if self.net is not None:
                self.net.close()
        except Exception:
            pass
        try:
            if self.server is not None:
                self.server.stop()
        except Exception:
            pass
        err = self.error
        self.reset()
        self.error = err


def serve_forever(port=DEFAULT_PORT):
    """`python 파일.py --serve` : 전용 서버 (폰/PC 어디서든 접속 가능)"""
    srv = RoomServer(port, name='KART3D Server').start()
    print('KART3D 서버 시작 / server started  (port %d)' % port)
    for ip in local_ips():
        print('  접속 주소 / connect to:  %s  (포트 %d)' % (ip, port))
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        srv.stop()


# ----------------------------------------------------------------------------
#  설정/프로필 저장 (JSON 파일, 실패해도 게임은 계속 동작)
# ----------------------------------------------------------------------------
class Profile(dict):
    DEFAULTS = {'name': '', 'kart': None, 'map': 1, 'laps': 3, 'bots': 7, 'quality': 1, 'auto_gas': True, 'sound': True,
                'lang': 'auto', 'last_ip': '', 'port': DEFAULT_PORT, 'steer_mode': 'buttons'}

    def __init__(self, filename='kart3d_profile.json'):
        dict.__init__(self)
        self.filename = filename
        self.path = None
        self.update(self.DEFAULTS)
        self.load()
        if self['kart'] is None:
            self['kart'] = int(time.time() * 1000) % KART_COUNT

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
                    if isinstance(data, dict):
                        for k, v in data.items():
                            if k in self.DEFAULTS:
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


# ----------------------------------------------------------------------------
#  카트 3D 모델(파츠 목록) + 추격 카메라  — 두 프론트엔드(폰/PC)가 공유
#  좌표계(로컬): x = 오른쪽, y = 위, z = 앞.  박스: (cx, cy, cz, hx, hy, hz, 색, 앞면 테이퍼 x, y, 발광)
# ----------------------------------------------------------------------------
class KartModel(object):
    """카트 번호 -> 3D 파츠 목록"""

    def __init__(self, kid):
        k = decode_kart(kid)
        b = BODIES[k['body']]
        p = PAINTS[k['paint']]
        self.kid = kid
        self.k = k
        self.main = p['main']
        self.accent = p['accent']
        self.metal = p['metal']
        L, W, H = b['len'], b['wid'], b['hei']
        self.L, self.W, self.H = L, W, H
        R = WHEEL_R[k['wheel'] % 5]
        ww = WHEEL_W[k['wheel'] % 5]
        self.wheel_r, self.wheel_w, self.rim = R, ww, k['wheel'] // 5
        base = R * 0.75
        self.base = base
        main, acc = self.main, self.accent
        dark = (28, 30, 38)
        nose = b['nose']
        boxes = []
        # (cx, cy, cz, hx, hy, hz, color, tx, ty, glow)
        boxes.append((0, base + H * 0.35, 0, W / 2, H * 0.35, L / 2, main, 1, 1, False))
        boxes.append((0, base + H * 0.28, L / 2 + nose * 0.3, W * 0.33, H * 0.24, max(0.12, nose * 0.55), acc if p['pattern'] == 2 else main, 0.5, 0.6, False))
        if p['pattern'] == 1:
            boxes.append((0, base + H * 0.71, nose * 0.3, W * 0.08, 0.02, (L + nose * 0.9) / 2, acc, 1, 1, False))
        if p['pattern'] == 2:
            boxes.append((0, base + H * 0.3, -L * 0.2, W * 0.51, H * 0.08, L * 0.2, acc, 1, 1, False))
        for s in (-1, 1):
            boxes.append((s * (W / 2 + 0.08), base + H * 0.3, -L * 0.05, W * 0.1, H * 0.27, L * 0.25, acc, 1, 1, False))
            boxes.append((s * W * 0.32, base + H * 0.42, L / 2 + 0.03, 0.11, 0.06, 0.05, (255, 246, 208), 1, 1, True))
            boxes.append((s * W * 0.25, base + H * 0.25, -L / 2 - 0.1, 0.07, 0.07, 0.2, (150, 156, 168), 1, 1, False))
            boxes.append((s * W * 0.36, base + H * 0.5, -L / 2 - 0.02, 0.12, 0.05, 0.03, (255, 40, 50), 1, 1, True))
        boxes.append((0, base + H * 0.12, L / 2 + nose * 0.55 + 0.05, W * 0.47, H * 0.07, 0.1, dark, 1, 1, False))
        seat = -L * 0.08
        self.seat = (0.0, base + H * 0.7, seat)
        if b['canopy'] == 1:
            boxes.append((0, base + H * 0.7 + 0.26, seat, W * 0.34, 0.26, 0.6, (150, 205, 245), 0.8, 0.85, False))
        elif b['canopy'] == 2:
            boxes.append((0, base + H * 0.7 + 0.17, seat - 0.15, W * 0.36, 0.17, L * 0.19, main, 1, 1, False))
            boxes.append((0, base + H * 0.7 + 0.2, seat + L * 0.19 + 0.02, W * 0.31, 0.1, 0.04, (32, 48, 64), 1, 1, False))
        # 드라이버 몸통
        boxes.append((0, base + H * 0.7 + 0.28, seat, 0.2, 0.28, 0.17, acc, 1, 1, False))
        self.helmet = (0.0, base + H * 0.7 + 0.72, seat + 0.02)
        # 윙/파츠
        top = base + H + 0.0
        bz = -L / 2
        w = k['wing']
        if w == 1:
            boxes.append((0, top - 0.05, bz + 0.1, W * 0.45, 0.03, 0.2, main, 1, 1, False))
        elif w == 2:
            for s in (-1, 1):
                boxes.append((s * W * 0.3, top + 0.25, bz + 0.1, 0.035, 0.28, 0.06, dark, 1, 1, False))
            boxes.append((0, top + 0.55, bz, W * 0.53, 0.035, 0.28, main, 1, 1, False))
        elif w == 3:
            for s in (-1, 1):
                boxes.append((s * W * 0.32, top + 0.28, bz + 0.1, 0.035, 0.3, 0.06, dark, 1, 1, False))
            boxes.append((0, top + 0.4, bz, W * 0.53, 0.03, 0.22, main, 1, 1, False))
            boxes.append((0, top + 0.68, bz - 0.12, W * 0.53, 0.03, 0.22, acc, 1, 1, False))
        elif w == 4:
            for s in (-1, 1):
                boxes.append((s * (W / 2 + 0.03), top - 0.05, bz + 0.3, 0.025, 0.25, 0.45, acc, 1, 1, False))
        elif w == 5:
            boxes.append((0, top + 0.5, bz - 0.1, W * 0.6, 0.04, 0.3, acc, 1, 1, False))
            for s in (-1, 1):
                boxes.append((s * W * 0.25, top + 0.25, bz + 0.05, 0.035, 0.28, 0.06, dark, 1, 1, False))
                boxes.append((s * W * 0.6, top + 0.5, bz - 0.1, 0.03, 0.14, 0.35, main, 1, 1, False))
        elif w == 6:
            boxes.append((0, top - 0.02, bz + 0.05, W * 0.4, 0.035, 0.27, main, 1, 1, False))
        elif w == 7:
            boxes.append((0, top + 0.12, -0.1, 0.18, 0.18, 0.25, dark, 0.5, 0.5, False))
        elif w == 8:
            for s in (-1, 1):
                boxes.append((s * 0.35, base + H * 0.6 + 0.3, bz - 0.2, 0.2, 0.2, 0.45, dark, 1, 1, False))
                boxes.append((s * 0.35, base + H * 0.6 + 0.3, bz - 0.66, 0.14, 0.14, 0.03, acc, 1, 1, True))
        elif w == 9:
            boxes.append((0, base + H + 0.55, bz - 0.1, 0.28, 0.28, 0.55, acc, 1, 1, False))
            boxes.append((0, base + H + 0.55, bz - 0.68, 0.18, 0.18, 0.05, (255, 150, 60), 1, 1, True))
            for s in (-1, 1):
                boxes.append((s * 0.4, base + H + 0.55, bz - 0.2, 0.25, 0.025, 0.2, dark, 1, 1, False))
        self.boxes = boxes
        # LOD1 용 단순 박스 (차체+포드+캐노피+윙 일부)
        self.boxes_lod1 = boxes[:2] + [bx for bx in boxes[2:] if bx[6] != (150, 156, 168) and bx[5] > 0.1 and not bx[9]][:7]
        # 바퀴 위치
        wz = L * 0.34
        self.wheels = []
        for sx, sz, front in ((-1, 1, True), (1, 1, True), (-1, -1, False), (1, -1, False)):
            self.wheels.append((sx * (W / 2 + ww * 0.35), R, sz * wz, sx, front))
        if self.rim == 3:
            self.rim_color = (224, 176, 32)
        elif self.rim == 4:
            self.rim_color = shade_rgb(acc, 1.3)
        else:
            self.rim_color = acc
        self.spin = 0.0


class ChaseCam(object):
    """추격 카메라: 카트 뒤쪽 위에서 부드럽게 따라간다"""

    def __init__(self):
        self.h = None
        self.y = 0.0

    def reset(self):
        self.h = None

    def update(self, dt, rc, max_speed):
        sr = clamp(rc.speed / max_speed, 0.0, 1.3)
        target = rc.h + (-rc.drift_dir * 0.2 if rc.drifting else 0.0)
        if self.h is None:
            self.h = rc.h
            self.y = rc.y
        self.h += wrap_pi(target - self.h) * (1 - math.exp(-5.5 * dt))
        self.y += (rc.y - self.y) * (1 - math.exp(-9.0 * dt))
        dist = 8.3 + sr * 2.2 + (1.6 if rc.boosting else 0.0)
        hgt = 3.5 + sr * 0.4
        fx, fz = math.sin(self.h), math.cos(self.h)
        x, y, z = rc.x - fx * dist, self.y + hgt, rc.z - fz * dist
        lx, ly, lz = rc.x + fx * 8.0, self.y + 1.2, rc.z + fz * 8.0
        yaw = math.atan2(lx - x, lz - z)
        pitch = math.atan2(y - ly, math.hypot(lx - x, lz - z))
        return x, y, z, yaw, pitch



# ============================================================================
#  [폰] 테마별 색상표 / 안개 / 하늘 / 배경 파노라마 / 장식물 스프라이트
# ============================================================================
FOGN = 16


def fog_mix(c, fog, t):
    return (int(c[0] + (fog[0] - c[0]) * t), int(c[1] + (fog[1] - c[1]) * t), int(c[2] + (fog[2] - c[2]) * t))


# kind: (월드 폭 m, 월드 높이 m, 캔버스 폭 px, 캔버스 높이 px)
SPRITE_DIM = {
    'pine': (7.0, 11.0, 70, 110), 'roundtree': (7.5, 9.5, 75, 95), 'bush': (3.4, 2.2, 34, 22), 'cactus': (4.2, 6.5, 42, 65),
    'rock': (6.0, 3.6, 60, 36), 'mesa': (20.0, 24.0, 100, 120), 'palm': (9.0, 10.5, 90, 105), 'building': (1.0, 1.0, 64, 128),
    'crystal': (3.4, 8.0, 34, 80), 'lollipop': (4.4, 7.6, 44, 76), 'icecream': (3.4, 7.6, 34, 76),
}


def _surf(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def _ell(s, c, cx, cy, rx, ry):
    pygame.draw.ellipse(s, c, (int(cx - rx), int(cy - ry), max(1, int(rx * 2)), max(1, int(ry * 2))))


def make_sprite(kind, th, var):
    cw, ch = SPRITE_DIM[kind][2], SPRITE_DIM[kind][3]
    s = _surf(cw, ch)
    cx = cw / 2.0
    if kind == 'pine':
        snowy = th.get('snowy')
        pygame.draw.rect(s, (90, 59, 34), (int(cx - 4), ch - 20, 8, 20))
        cols = [(31, 107, 53), (42, 125, 63), (53, 145, 74)] if not snowy else [(79, 127, 102), (109, 154, 132), (242, 247, 251)]
        for (by, hw_, h_), c in zip(((ch - 14, 34, 44), (ch - 40, 28, 38), (ch - 64, 21, 34)), cols):
            pygame.draw.polygon(s, c, [(cx - hw_, by), (cx + hw_, by), (cx, by - h_)])
            pygame.draw.polygon(s, shade_rgb(c, 0.7), [(cx, by - h_), (cx + hw_, by), (cx, by)])
    elif kind == 'roundtree':
        cols = [(217, 84, 30), (232, 163, 23), (184, 58, 26), (240, 192, 48)] if th.get('autumn') else [(58, 140, 58), (74, 160, 74), (47, 127, 53), (90, 170, 80)]
        c = cols[var % len(cols)]
        pygame.draw.rect(s, (90, 59, 34), (int(cx - 5), ch - 40, 10, 40))
        _ell(s, shade_rgb(c, 0.72), cx + 4, ch - 56, 33, 30)
        _ell(s, c, cx - 2, ch - 58, 31, 29)
        _ell(s, shade_rgb(c, 1.18), cx - 10, ch - 68, 16, 13)
    elif kind == 'bush':
        _ell(s, (40, 110, 48), cx + 2, ch - 8, 15, 9)
        _ell(s, (58, 140, 58), cx - 3, ch - 9, 14, 9)
        _ell(s, (88, 170, 80), cx - 6, ch - 12, 7, 4)
    elif kind == 'cactus':
        g = (59, 138, 74)
        pygame.draw.rect(s, g, (int(cx - 7), 6, 14, ch - 6), border_radius=6)
        pygame.draw.rect(s, shade_rgb(g, 0.72), (int(cx + 1), 8, 6, ch - 10), border_radius=3)
        pygame.draw.rect(s, g, (int(cx - 20), 28, 20, 8), border_radius=3)
        pygame.draw.rect(s, g, (int(cx - 22), 14, 8, 22), border_radius=4)
        pygame.draw.rect(s, g, (int(cx + 5), 36, 18, 8), border_radius=3)
        pygame.draw.rect(s, g, (int(cx + 15), 22, 8, 22), border_radius=4)
    elif kind == 'rock':
        c0, c1 = hex_rgb(th['rock'][0]), hex_rgb(th['rock'][1])
        pygame.draw.polygon(s, c0, [(2, ch), (8, 14), (24, 2), (44, 6), (58, 22), (58, ch)])
        pygame.draw.polygon(s, c1, [(30, 4), (44, 6), (58, 22), (58, ch), (32, ch), (34, 18)])
        pygame.draw.polygon(s, shade_rgb(c0, 1.2), [(8, 14), (24, 2), (30, 4), (20, 20)])
    elif kind == 'mesa':
        for c, pts in (((176, 74, 40), [(0, ch), (14, 46), (86, 46), (100, ch)]), ((199, 101, 58), [(12, 62), (18, 24), (82, 24), (90, 62)]),
                       ((168, 68, 36), [(22, 30), (26, 8), (74, 8), (78, 30)]), ((224, 160, 96), [(26, 10), (28, 4), (72, 4), (74, 10)])):
            pygame.draw.polygon(s, c, pts)
        pygame.draw.polygon(s, (120, 48, 26), [(60, 8), (100, ch), (70, ch)])
    elif kind == 'palm':
        pygame.draw.polygon(s, (138, 106, 64), [(cx - 5, ch), (cx + 3, ch), (cx + 8, 22), (cx + 2, 22)])
        for k, c in enumerate(((47, 143, 58), (58, 160, 70), (40, 125, 52), (70, 175, 80), (47, 143, 58), (58, 160, 70))):
            a = -2.7 + k * 0.54
            ex, ey = cx + 6 + math.cos(a) * 40, 22 + math.sin(a) * 22 + 12
            mx, my = cx + 6 + math.cos(a) * 20, 22 + math.sin(a) * 20 - 6
            pygame.draw.polygon(s, c, [(cx + 6, 22), (mx - 3, my - 5), (ex, ey), (mx + 3, my + 5)])
        pygame.draw.circle(s, (90, 59, 34), (int(cx + 6), 24), 4)
    elif kind == 'building':
        neon = th.get('night')
        cols = [(255, 43, 214), (25, 230, 255), (255, 225, 74), (120, 255, 150)]
        c = cols[var % 4]
        pygame.draw.rect(s, (22, 22, 44), (0, 0, cw, ch))
        pygame.draw.rect(s, (34, 34, 66), (cw - 14, 0, 14, ch))
        rnd = Rng(var * 977 + 13)
        for y in range(8, ch - 6, 10):
            for x in range(6, cw - 14, 10):
                if rnd() < 0.55:
                    wc = c if rnd() < 0.3 else ((255, 220, 140) if rnd() < 0.6 else (150, 190, 255))
                    pygame.draw.rect(s, wc, (x, y, 5, 5))
        pygame.draw.rect(s, c, (0, 0, cw, 3))
        pygame.draw.rect(s, c, (0, ch // 2, cw, 2))
        if not neon:
            pygame.draw.rect(s, (60, 60, 80), (0, 0, cw, ch), 2)
    elif kind == 'crystal':
        col = (255, 122, 26) if th.get('lava') else ((25, 230, 255) if th['key'] == 'space' else (255, 43, 214))
        pygame.draw.polygon(s, col, [(cx, 0), (cx + 12, ch * 0.45), (cx, ch), (cx - 12, ch * 0.45)])
        pygame.draw.polygon(s, shade_rgb(col, 0.62), [(cx, 0), (cx + 12, ch * 0.45), (cx, ch)])
        pygame.draw.polygon(s, shade_rgb(col, 1.35), [(cx, 4), (cx - 12, ch * 0.45), (cx - 3, ch * 0.45)])
    elif kind == 'lollipop':
        hue = [(255, 90, 140), (90, 200, 255), (255, 200, 60), (160, 110, 255), (110, 230, 150), (255, 140, 60)][var % 6]
        pygame.draw.rect(s, (245, 245, 245), (int(cx - 2), 30, 4, ch - 30))
        pygame.draw.circle(s, (255, 255, 255), (int(cx), 22), 21)
        pygame.draw.circle(s, hue, (int(cx), 22), 17)
        pygame.draw.circle(s, (255, 255, 255), (int(cx), 22), 11)
        pygame.draw.circle(s, hue, (int(cx), 22), 6)
    elif kind == 'icecream':
        pygame.draw.polygon(s, (224, 169, 106), [(cx - 13, 40), (cx + 13, 40), (cx, ch)])
        for k in range(3):
            pygame.draw.line(s, (190, 135, 80), (cx - 11 + k * 11, 42), (cx - 3 + k * 4, ch - 8), 1)
        sc = [(255, 158, 196), (255, 235, 160), (150, 220, 255)][var % 3]
        pygame.draw.circle(s, sc, (int(cx), 30), 15)
        pygame.draw.circle(s, shade_rgb(sc, 1.15), (int(cx - 4), 25), 6)
        pygame.draw.circle(s, (221, 34, 51), (int(cx), 12), 4)
    return s


class ThemeGfx(object):
    """하나의 맵 테마를 그리는 데 필요한 모든 캐시"""

    def __init__(self, th, seed, rw, rh, f, far):
        self.th = th
        self.rw, self.rh, self.f, self.far = rw, rh, f, far
        self.night = bool(th.get('night'))
        self.fog = hex_rgb(th['fog'])
        self.sky_top = hex_rgb(th['sky_top'])
        self.sky_bot = hex_rgb(th['sky_bot'])
        self.sprites = {}
        self.scaled = {}
        self._make_palette()
        self._make_fog_lut()
        self.sky = self._make_sky()
        self.pano = self._make_pano(seed)
        self.skyfx = self._make_skyfx(seed)
        self.glow = self._make_glow()
        self.sun_az = math.atan2(th['sun_dir'][0], th['sun_dir'][2])
        sd = th['sun_dir']
        self.sun_el = math.asin(sd[1] / math.sqrt(sd[0] ** 2 + sd[1] ** 2 + sd[2] ** 2))

    # ---- 색상표 -----------------------------------------------------------------
    def _make_palette(self):
        th = self.th
        amb = 0.86 if self.night else 1.0
        glow = bool(th.get('glow_wall'))
        road = hex_rgb(th['road'])
        g0, g1 = hex_rgb(th['ground'][0]), hex_rgb(th['ground'][1])
        w0, w1 = hex_rgb(th['wall'][0]), hex_rgb(th['wall'][1])
        wk = 1.0 if glow else amb
        base = {
            'road_a': shade_rgb(road, amb), 'road_b': shade_rgb(road, amb * 1.13),
            'grass_a': shade_rgb(g0, amb), 'grass_b': shade_rgb(g1, amb),
            'skirt_a': shade_rgb(g0, amb * 0.78), 'skirt_b': shade_rgb(g1, amb * 0.72),
            'kerb_r': shade_rgb((216, 35, 42), amb), 'kerb_w': shade_rgb((240, 240, 240), amb),
            'wall_a': shade_rgb(w0, wk * 0.95), 'wall_b': shade_rgb(w1, wk * 0.95),
            'wall_a2': shade_rgb(w0, wk * 0.74), 'wall_b2': shade_rgb(w1, wk * 0.74),
            'wall_top': shade_rgb((226, 226, 232), wk),
            'dash': (110, 220, 255) if self.night else (246, 246, 246),
            'line': (255, 255, 255),
            'far': hex_rgb(th['far']),
        }
        self.pal = {}
        for name, c in base.items():
            self.pal[name] = [fog_mix(c, self.fog, (i / (FOGN - 1.0)) * 0.94) for i in range(FOGN)]
        self.ground_far = fog_mix(shade_rgb(g0, amb * 0.9), self.fog, 0.55)

    def _make_fog_lut(self):
        far = self.far
        self.fog_lut = []
        for d in range(int(far) + 4):
            t = clamp((d - 0.12 * far) / (0.88 * far), 0.0, 1.0) ** 1.2
            self.fog_lut.append(min(FOGN - 1, int(t * FOGN)))

    # ---- 하늘 ----------------------------------------------------------------------
    def _make_sky(self):
        h = int(self.rh * 1.9)
        s = pygame.Surface((self.rw, h))
        for y in range(h):
            t = y / float(h - 1)          # 0 위 -> 1 지평선
            c = mix_rgb(self.sky_top, self.sky_bot, t ** 0.55)
            pygame.draw.line(s, c, (0, y), (self.rw, y))
        return s

    def _make_glow(self):
        r = max(24, int(self.rh * 0.22))
        s = _surf(r * 2, r * 2)
        sc = hex_rgb(self.th['sun'])
        for i in range(r, 0, -2):
            a = int(120 * (1 - i / float(r)) ** 2)
            pygame.draw.circle(s, (sc[0], sc[1], sc[2], a), (r, r), i)
        return s

    def _make_skyfx(self, seed):
        pw = max(64, int(TAU * self.f))
        ph = int(self.rh * 0.95)
        s = _surf(pw, ph)
        rnd = Rng(seed ^ 0x1234567)
        if self.night:
            for _ in range(260):
                x, y = int(rnd() * pw), int(rnd() * ph * 0.95)
                b = int(120 + rnd() * 135)
                s.set_at((x, y), (b, b, min(255, b + 20), 255))
                if rnd() < 0.18:
                    s.set_at((min(pw - 1, x + 1), y), (b, b, b, 200))
        n = int(7 * self.th.get('clouds', 0))
        if n:
            cc = (255, 240, 250, 205) if self.th['key'] == 'candy' else (255, 255, 255, 190)
            for _ in range(n):
                x = rnd() * pw
                y = ph * (0.18 + rnd() * 0.5)
                sz = (0.5 + rnd()) * self.rh * 0.12
                for j in range(5):
                    _ell(s, cc, (x + (j - 2) * sz * 0.7) % pw, y + (j % 2) * sz * 0.12, sz * (0.9 - 0.12 * abs(j - 2)), sz * 0.36)
        return s

    # ---- 파노라마 (360도 배경) ------------------------------------------------------
    def _make_pano(self, seed):
        th = self.th
        pw = max(64, int(TAU * self.f))
        ph = int(self.rh * 0.36)
        s = _surf(pw, ph)
        rnd = Rng(seed ^ 0x5bd1e995)
        skyb = self.sky_bot
        fog = self.fog
        key = th['key']

        def ridge(color, base, amp, harm=(1, 2, 3, 5, 8, 13), step=3):
            phs = [rnd() * TAU for _ in harm]
            pts = [(0, ph)]
            for x in range(0, pw + step, step):
                a = min(x, pw) / float(pw) * TAU
                h = base
                for k, p in zip(harm, phs):
                    h += amp / (k ** 0.8) * math.sin(k * a + p)
                pts.append((min(x, pw), ph - max(2, h)))
            pts.append((pw, ph))
            pygame.draw.polygon(s, color, pts)
            return pts

        far_c = mix_rgb(skyb, fog, 0.5)
        if key in ('forest', 'autumn'):
            col1 = (110, 140, 170) if key == 'forest' else (190, 150, 110)
            ridge(mix_rgb(col1, skyb, 0.5), ph * 0.55, ph * 0.28)
            c2 = (60, 110, 80) if key == 'forest' else (150, 95, 50)
            ridge(mix_rgb(c2, fog, 0.35), ph * 0.34, ph * 0.18)
            for _ in range(int(pw / 14)):
                x = rnd() * pw
                hh = 6 + rnd() * 10
                base_y = ph - ph * 0.30 + (rnd() - 0.5) * 8
                pygame.draw.polygon(s, mix_rgb(c2, fog, 0.15), [(x - 4, base_y + 6), (x + 4, base_y + 6), (x, base_y - hh)])
        elif key == 'desert':
            ridge(mix_rgb((200, 160, 100), skyb, 0.5), ph * 0.30, ph * 0.14, (1, 2, 3, 4))
            for _ in range(3):
                x = rnd() * pw
                b = 22 + rnd() * 18
                pygame.draw.polygon(s, mix_rgb((190, 150, 95), fog, 0.35), [(x - b, ph - 8), (x + b, ph - 8), (x, ph - 8 - b * 0.9)])
            ridge(mix_rgb((214, 176, 110), fog, 0.2), ph * 0.2, ph * 0.1, (1, 2, 4, 6))
        elif key == 'snow':
            snow = ridge((246, 250, 255), ph * 0.62, ph * 0.32)
            low = [(x, y + 15) for x, y in snow]
            low[0] = (0, ph)
            low[-1] = (pw, ph)
            pygame.draw.polygon(s, mix_rgb((120, 150, 190), skyb, 0.4), low)
            ridge(mix_rgb((95, 125, 105), fog, 0.45), ph * 0.26, ph * 0.12)
        elif key == 'neon':
            for layer, (col, hmax, wmax) in enumerate((((44, 22, 84), ph * 0.8, 26), ((22, 14, 52), ph * 0.55, 34))):
                x = 0
                while x < pw:
                    bw = 10 + rnd() * wmax
                    bh = 8 + rnd() * hmax
                    pygame.draw.rect(s, col, (x, ph - bh, bw, bh))
                    for wy in range(int(ph - bh + 4), ph - 3, 6):
                        for wx in range(int(x + 3), int(x + bw - 3), 5):
                            if rnd() < (0.25 if layer == 0 else 0.4):
                                pygame.draw.rect(s, [(255, 225, 120), (120, 220, 255), (255, 90, 220)][int(rnd() * 3)], (wx, wy, 2, 2))
                    if rnd() < 0.2:
                        pygame.draw.line(s, (255, 60, 90), (x + bw / 2, ph - bh), (x + bw / 2, ph - bh - 7), 1)
                    x += bw + rnd() * 4
        elif key == 'volcano':
            ridge((46, 22, 18), ph * 0.40, ph * 0.16)
            for _ in range(2):
                x = rnd() * pw
                b = 46 + rnd() * 30
                top = ph - ph * 0.88
                pygame.draw.polygon(s, (52, 26, 20), [(x - b, ph), (x + b, ph), (x + 10, top), (x - 10, top)])
                pygame.draw.polygon(s, (255, 110, 30), [(x - 10, top), (x + 10, top), (x + 5, top + 12), (x - 5, top + 9)])
                pygame.draw.line(s, (255, 130, 40), (x - 2, top + 8), (x - 8, ph), 2)
            ridge((34, 18, 16), ph * 0.2, ph * 0.1)
        elif key == 'tropic':
            sea = (30, 168, 200)
            pygame.draw.rect(s, mix_rgb(sea, skyb, 0.25), (0, ph - int(ph * 0.34), pw, int(ph * 0.34)))
            for _ in range(5):
                x = rnd() * pw
                w_ = 30 + rnd() * 50
                pygame.draw.ellipse(s, mix_rgb((70, 150, 100), fog, 0.35), (int(x - w_), ph - int(ph * 0.34) - 8, int(w_ * 2), 18))
            ridge(mix_rgb((235, 215, 160), fog, 0.2), ph * 0.14, ph * 0.04, (1, 3, 5))
        elif key == 'candy':
            ridge(mix_rgb((255, 190, 225), skyb, 0.35), ph * 0.48, ph * 0.22)
            ridge(mix_rgb((190, 240, 255), fog, 0.3), ph * 0.28, ph * 0.14)
            for _ in range(int(pw / 90)):
                x = rnd() * pw
                c = [(255, 90, 140), (90, 200, 255), (255, 200, 60)][int(rnd() * 3)]
                pygame.draw.line(s, (255, 255, 255), (x, ph), (x, ph - 34), 2)
                pygame.draw.circle(s, c, (int(x), ph - 38), 9)
                pygame.draw.circle(s, (255, 255, 255), (int(x), ph - 38), 4)
        elif key == 'space':
            ridge((70, 70, 80), ph * 0.34, ph * 0.18)
            px_ = rnd() * pw
            pygame.draw.circle(s, (58, 111, 208), (int(px_), int(ph * 0.45)), int(ph * 0.34))
            pygame.draw.circle(s, (30, 70, 150), (int(px_ + ph * 0.1), int(ph * 0.5)), int(ph * 0.26))
            pygame.draw.ellipse(s, (200, 184, 144), (int(px_ - ph * 0.6), int(ph * 0.4), int(ph * 1.2), int(ph * 0.14)), 2)
            ridge((92, 92, 104), ph * 0.18, ph * 0.1, (1, 2, 4, 7))
        elif key == 'canyon':
            for layer, (col, hmax) in enumerate((((150, 70, 50), ph * 0.8), ((120, 52, 36), ph * 0.55))):
                x = 0
                while x < pw:
                    bw = 30 + rnd() * 80
                    bh = hmax * (0.35 + rnd() * 0.65)
                    c = mix_rgb(col, fog, 0.3 - layer * 0.15)
                    pygame.draw.rect(s, c, (x, ph - bh, bw, bh))
                    pygame.draw.rect(s, shade_rgb(c, 1.2), (x, ph - bh, bw, 3))
                    pygame.draw.rect(s, shade_rgb(c, 0.8), (x + bw * 0.65, ph - bh, bw * 0.35, bh))
                    if rnd() < 0.5:
                        pygame.draw.rect(s, c, (x + bw * 0.2, ph - bh - 10, bw * 0.5, 10))
                    x += bw * (0.5 + rnd() * 0.6)
        return s

    # ---- 장식물 스프라이트 --------------------------------------------------------------
    def sprite(self, kind, var):
        k = (kind, var)
        sp = self.sprites.get(k)
        if sp is None:
            sp = self.sprites[k] = make_sprite(kind, self.th, var)
        return sp

    def scaled_sprite(self, kind, var, wpx, hpx):
        """월드 크기를 화면 픽셀 크기로 맞춘 스프라이트 (로그 간격 양자화 캐시: 크기가 연속으로 변해도 캐시 적중)"""
        qw = max(2, int(_QB ** round(math.log(max(wpx, 1.0)) / _QL)))
        qh = max(2, int(_QB ** round(math.log(max(hpx, 1.0)) / _QL)))
        key = (kind, var, qw, qh)
        sp = self.scaled.get(key)
        if sp is None:
            if len(self.scaled) > 1200:
                self.scaled.clear()
            sp = self.scaled[key] = pygame.transform.scale(self.sprite(kind, var), (qw, qh))
        return sp


_QB = 1.12
_QL = math.log(_QB)


# ============================================================================
#  [폰] 소프트웨어 3D 렌더러 (pygame 폴리곤 + 페인터 알고리즘)
#   - 트랙은 실제 3D 좌표(고저차/뱅킹 포함)를 카메라로 변환해 먼 곳부터 칠한다.
#   - 카트는 파츠(박스/바퀴/윙/드라이버)로 이루어진 3D 모델 (100,000종 파라미터 조합)
# ============================================================================
class Cam(object):
    def __init__(self):
        self.set(0.0, 0.0, 0.0, 0.0, 0.0)

    def set(self, x, y, z, yaw, pitch):
        self.x, self.y, self.z, self.yaw, self.pitch = x, y, z, yaw, pitch
        self.sy, self.cy = math.sin(yaw), math.cos(yaw)
        self.sp, self.cp = math.sin(pitch), math.cos(pitch)


QUALITY = [  # 내부 해상도 폭, near/mid/far 구간(샘플), 카트 LOD 거리(m)
    dict(w=336, near=16, mid=30, far=60, lod0=11.0, lod1=60.0, props=70, parts=True),
    dict(w=440, near=22, mid=44, far=90, lod0=17.0, lod1=90.0, props=140, parts=True),
    dict(w=580, near=26, mid=54, far=120, lod0=26.0, lod1=120.0, props=220, parts=True),
]

OFFS = None   # 단면 정점 배치 (Track 마다 hw 가 달라서 set_track 에서 채움)
K = 12        # 단면당 정점 수

# 박스 면 (코너 인덱스 = (sx>0)<<2 | (sy>0)<<1 | (sz>0))
FACES = (
    ('z+', (1, 5, 7, 3), 0.98), ('z-', (4, 0, 2, 6), 0.86), ('x+', (4, 5, 7, 6), 0.76), ('x-', (1, 0, 2, 3), 0.90), ('y+', (2, 3, 7, 6), 1.12),
)


class Renderer(object):
    def __init__(self, sw, sh, quality=1):
        self.sw, self.sh = sw, sh
        self.track = None
        self.tg = None
        self.models = {}
        self.parts = []
        self.weather = []
        self.labels = []
        self.shake = 0.0
        self.cam = Cam()
        self.set_quality(quality, sw, sh)

    # ---- 해상도/품질 -------------------------------------------------------------------
    def set_quality(self, q, sw, sh):
        self.q = int(clamp(q, 0, 2))
        Q_ = QUALITY[self.q]
        self.qp = Q_
        self.sw, self.sh = sw, sh
        rw = min(Q_['w'], sw)
        rh = max(120, int(rw * sh / float(sw)))
        self.rw, self.rh = rw, rh
        self.hx, self.hy = rw / 2.0, rh / 2.0
        self.f = min(rh * 0.92, rw * 0.62)
        self.near = 0.55
        try:
            self.surf = pygame.Surface((rw, rh), 0, pygame.display.get_surface())
        except Exception:
            self.surf = pygame.Surface((rw, rh))
        near_n, mid_n, far_n = Q_['near'], Q_['mid'], Q_['far']
        back = 5
        offs = list(range(-back, near_n + 1))
        k = near_n + 2
        while k <= mid_n:
            offs.append(k)
            k += 2
        while k <= far_n:
            offs.append(k)
            k += 4
        self.offs = offs
        self.slot_map = {}
        for i in range(len(offs) - 1):
            for o in range(offs[i] + 1, offs[i + 1] + 1):
                self.slot_map[o] = i
        self.far_m = far_n * 4.0
        if self.track is not None:
            self.set_track(self.track)

    # ---- 트랙 지오메트리 -------------------------------------------------------------------
    def set_track(self, track):
        self.track = track
        th = track.theme
        self.tg = ThemeGfx(th, track.info['seed'], self.rw, self.rh, self.f, self.far_m)
        N = track.N
        hw, wo, sk = track.hw, track.wall_off, track.rows[3][0]
        offs = [(-hw, 0.0), (hw, 0.0), (-(hw + 1.4), 0.0), (hw + 1.4, 0.0), (-wo, 0.0), (wo, 0.0), (-sk, 0.0), (sk, 0.0),
                (-wo, 1.3), (wo, 1.3), (-0.28, 0.0), (0.28, 0.0)]
        GX = [0.0] * (N * K)
        GY = [0.0] * (N * K)
        GZ = [0.0] * (N * K)
        for i in range(N):
            for j in range(K):
                x, y, z = track.edge_point(i, offs[j][0])
                GX[i * K + j] = x
                GY[i * K + j] = y + offs[j][1] + (0.04 if j >= 10 else 0.0)
                GZ[i * K + j] = z
        self.GX, self.GY, self.GZ = GX, GY, GZ
        self.weather = []
        wtype = th.get('weather')
        if wtype:
            rnd = Rng(track.info['seed'] ^ 77)
            for _ in range(70):
                self.weather.append([rnd() * self.rw, rnd() * self.rh, 14 + rnd() * 26, (rnd() - 0.5) * 8, 1 + int(rnd() * 2)])
        self.wtype = wtype
        self.parts = []
        # 시작 게이트 박스 (트랙 로컬: x=오른쪽, y=위, z=진행방향)
        hwg = hw + 1.6
        self.gate_boxes = [(-hwg, 5, 0, 0.7, 5, 0.7, (43, 47, 58), 1, 1, False), (hwg, 5, 0, 0.7, 5, 0.7, (43, 47, 58), 1, 1, False),
                           (0, 9.6, 0, hw + 2.2, 1.2, 0.4, (200, 40, 50), 1, 1, False), (0, 9.6, 0.42, hw + 2.0, 1.0, 0.03, (245, 245, 245), 1, 1, True)]

    def model(self, kid):
        m = self.models.get(kid)
        if m is None:
            if len(self.models) > 40:
                self.models.clear()
            m = self.models[kid] = KartModel(kid)
        return m

    # ---- 파티클 ----------------------------------------------------------------------------
    def emit(self, x, y, z, vx, vy, vz, color, size, life):
        if len(self.parts) < 260:
            self.parts.append([x, y, z, vx, vy, vz, life, life, color, size])

    def update_particles(self, dt):
        out = []
        for p in self.parts:
            p[6] -= dt
            if p[6] > 0:
                p[0] += p[3] * dt
                p[1] += p[4] * dt
                p[2] += p[5] * dt
                p[4] -= 9.0 * dt
                out.append(p)
        self.parts = out
        for w in self.weather:
            w[1] += w[2] * dt * (-0.5 if self.wtype == 'ember' else 1.0)
            w[0] += w[3] * dt
            if w[1] > self.rh + 4:
                w[1] = -4
            elif w[1] < -4:
                w[1] = self.rh + 4
            if w[0] < -4:
                w[0] = self.rw + 4
            elif w[0] > self.rw + 4:
                w[0] = -4

    # ---- 투영 도우미 --------------------------------------------------------------------------
    def proj(self, x, y, z):
        c = self.cam
        dx, dy, dz = x - c.x, y - c.y, z - c.z
        xr = -dx * c.cy + dz * c.sy
        zr = dx * c.sy + dz * c.cy
        dp = zr * c.cp - dy * c.sp
        yc = dy * c.cp + zr * c.sp
        if dp > self.near:
            inv = self.f / dp
            return (self.hx + xr * inv, self.hy - yc * inv, dp, xr, yc)
        return (0.0, 0.0, dp, xr, yc)

    def poly(self, color, pts):
        """pts: proj() 튜플들. near 평면 클리핑 + 화면 밖 컬링"""
        near = self.near
        allin = True
        anyin = False
        for p in pts:
            if p[2] > near:
                anyin = True
            else:
                allin = False
        if not anyin:
            return
        if not allin:
            pts = self._clip_near(pts)
            if len(pts) < 3:
                return
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        mxx = max(xs)
        mnx = min(xs)
        mxy = max(ys)
        mny = min(ys)
        if mxx < 0 or mnx > self.rw or mxy < 0 or mny > self.rh:
            return
        if mxx > 2400 or mnx < -2400 or mxy > 2400 or mny < -2400:
            pts = self._clip_screen([(p[0], p[1]) for p in pts])
            if len(pts) < 3:
                return
            pygame.draw.polygon(self.surf, color, pts)
            return
        pygame.draw.polygon(self.surf, color, list(zip(xs, ys)))

    def _clip_near(self, pts):
        near = self.near
        f, hx, hy = self.f, self.hx, self.hy
        out = []
        n = len(pts)
        for i in range(n):
            a = pts[i]
            b = pts[(i + 1) % n]
            ain = a[2] > near
            bin_ = b[2] > near
            if ain:
                out.append(a)
            if ain != bin_:
                t = (near - a[2]) / (b[2] - a[2])
                xr = a[3] + (b[3] - a[3]) * t
                yc = a[4] + (b[4] - a[4]) * t
                inv = f / near
                out.append((hx + xr * inv, hy - yc * inv, near, xr, yc))
        return out

    def _clip_screen(self, pts):
        W, H = self.rw + 2, self.rh + 2
        for axis, lo, hi in ((0, -2, W), (1, -2, H)):
            for bound, keep_ge in ((lo, True), (hi, False)):
                out = []
                n = len(pts)
                for i in range(n):
                    a = pts[i]
                    b = pts[(i + 1) % n]
                    ain = (a[axis] >= bound) if keep_ge else (a[axis] <= bound)
                    bin_ = (b[axis] >= bound) if keep_ge else (b[axis] <= bound)
                    if ain:
                        out.append(a)
                    if ain != bin_:
                        t = (bound - a[axis]) / (b[axis] - a[axis])
                        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
                pts = out
                if not pts:
                    return pts
        return pts

    # ============================================================================
    #  프레임 그리기
    # ============================================================================
    def draw_background(self):
        c = self.cam
        tg = self.tg
        s = self.surf
        f, hx, hy = self.f, self.hx, self.hy
        hor = hy - f * math.tan(c.pitch)
        hori = int(hor)
        sky = tg.sky
        s.blit(sky, (0, hori - sky.get_height()))
        if hori < self.rh:
            s.fill(tg.ground_far, (0, max(0, hori), self.rw, self.rh - max(0, hori)))
        # 태양/달
        da = wrap_pi(c.yaw - tg.sun_az)
        if abs(da) < 1.1:
            sx = hx + f * da
            sy = hor - f * math.tan(tg.sun_el)
            g = tg.glow
            s.blit(g, (int(sx - g.get_width() / 2), int(sy - g.get_height() / 2)))
            r = max(3, int(self.rh * (0.028 if not tg.night else 0.04)))
            sc = hex_rgb(tg.th['sun'])
            pygame.draw.circle(s, mix_rgb(sc, (255, 255, 255), 0.6), (int(sx), int(sy)), r)
        # 별/구름 + 파노라마
        pw = tg.pano.get_width()
        x0 = int((hx + f * c.yaw) % pw) - pw
        fx_ = tg.skyfx
        for xx in (x0, x0 + pw):
            s.blit(fx_, (xx, hori - fx_.get_height() + 2))
        pano = tg.pano
        for xx in (x0, x0 + pw):
            s.blit(pano, (xx, hori - pano.get_height() + 3))

    def draw_world(self, race, focus_idx, dirn):
        tr = self.track
        tg = self.tg
        N = tr.N
        c = self.cam
        surf = self.surf
        f, hx, hy, near = self.f, self.hx, self.hy, self.near
        cx, cy, cz = c.x, c.y, c.z
        csy, ccy, csp, ccp = c.sy, c.cy, c.sp, c.cp
        GX, GY, GZ = self.GX, self.GY, self.GZ
        offs = self.offs
        lut = tg.fog_lut
        lutmax = len(lut) - 1
        pal = tg.pal
        slot_map = self.slot_map
        items = [[] for _ in offs]
        half = N // 2
        # --- 슬롯에 오브젝트 배치 (장식물, 카트, 패드, 가로등, 게이트)
        pbs = tr.props_by_seg
        o_lo, o_hi = offs[0] + 1, offs[-1]
        for o in range(o_lo, o_hi + 1):
            i = (focus_idx + dirn * o) % N
            lst = pbs.get(i)
            if lst:
                sl = items[slot_map[o]]
                for p in lst:
                    dx, dz = p['x'] - cx, p['z'] - cz
                    dpp = (dx * csy + dz * ccy) * ccp - (p['y'] - cy) * csp
                    if dpp > 3.0:
                        sl.append((dpp, 0, p))
        for rc in race.racers:
            o = ((rc.idx - focus_idx) * dirn + half) % N - half
            sl_i = slot_map.get(o)
            if sl_i is not None:
                dx, dz = rc.x - cx, rc.z - cz
                items[sl_i].append(((dx * csy + dz * ccy) * ccp - (rc.y - cy) * csp, 1, rc))
        for p in tr.pads:
            o = ((p['idx'] - focus_idx) * dirn + half) % N - half
            sl_i = slot_map.get(o)
            if sl_i is not None:
                items[sl_i].append((1e6, 2, p))      # 패드는 도로 위에 깔리므로 가장 먼저
        if tr.lamps:
            for (li, side) in tr.lamps:
                o = ((li - focus_idx) * dirn + half) % N - half
                sl_i = slot_map.get(o)
                if sl_i is not None:
                    items[sl_i].append((self._dp_of(GX[li * K + 5], GY[li * K + 5], GZ[li * K + 5]) + 0.5, 3, (li, side)))
        o = ((0 - focus_idx) * dirn + half) % N - half
        sl_i = slot_map.get(o)
        if sl_i is not None:
            items[sl_i].append((self._dp_of(tr.px[0], tr.py[0], tr.pz[0]), 4, 0))
        for ai in tr.arches:
            o = ((ai - focus_idx) * dirn + half) % N - half
            sl_i = slot_map.get(o)
            if sl_i is not None:
                items[sl_i].append((self._dp_of(tr.px[ai], tr.py[ai], tr.pz[ai]), 5, ai))

        poly = self.poly
        prev = None
        prev_i = 0
        prev_k = 0
        nsec = len(offs)
        for k in range(nsec - 1, -1, -1):
            i = (focus_idx + dirn * offs[k]) % N
            base = i * K
            pts = []
            for j in range(K):
                dx = GX[base + j] - cx
                dy = GY[base + j] - cy
                dz = GZ[base + j] - cz
                xr = -dx * ccy + dz * csy
                zr = dx * csy + dz * ccy
                dp = zr * ccp - dy * csp
                yc = dy * ccp + zr * csp
                if dp > near:
                    inv = f / dp
                    pts.append((hx + xr * inv, hy - yc * inv, dp, xr, yc))
                else:
                    pts.append((0.0, 0.0, dp, xr, yc))
            if prev is not None:
                A, B = prev, pts
                stride = offs[k + 1] - offs[k]
                dpm = (A[0][2] + B[0][2]) * 0.5
                lv = lut[int(dpm) if dpm < lutmax else lutmax]
                ia = i if dirn > 0 else prev_i
                par = (min(i, prev_i) // 4) & 1 if stride == 1 else 0
                par2 = (min(i, prev_i) // 2) & 1 if stride <= 2 else 0
                grass = pal['grass_b' if par else 'grass_a'][lv]
                skirt = pal['skirt_b' if par else 'skirt_a'][lv]
                # 비탈 -> 갓길 -> 연석 -> 도로 순으로 칠함
                poly(skirt, (A[6], A[4], B[4], B[6]))
                poly(skirt, (A[5], A[7], B[7], B[5]))
                poly(grass, (A[4], A[2], B[2], B[4]))
                poly(grass, (A[3], A[5], B[5], B[3]))
                if dpm < 170:
                    kc = pal['kerb_r' if par2 else 'kerb_w'][lv]
                    poly(kc, (A[2], A[0], B[0], B[2]))
                    poly(kc, (A[1], A[3], B[3], B[1]))
                poly(pal['road_b' if par else 'road_a'][lv], (A[0], A[1], B[1], B[0]))
                if stride == 1 and dpm < 120 and ((min(i, prev_i) // 3) & 1) == 0:
                    poly(pal['dash'][lv], (A[10], A[11], B[11], B[10]))
                w_a = pal['wall_a' if par2 else 'wall_b'][lv]
                w_b = pal['wall_a2' if par2 else 'wall_b2'][lv]
                poly(w_a, (A[4], A[8], B[8], B[4]))
                poly(w_b, (A[9], A[5], B[5], B[9]))
                # 결승선 체커
                lo_i, hi_i = min(i, prev_i), max(i, prev_i)
                if stride == 1 and dpm < 100 and (lo_i == 0 or (lo_i == N - 1 and hi_i == 0)):
                    self._checker(A, B, lv)
                # 이 구간에 속한 오브젝트를 먼 것부터
                sl = items[k]
                if sl:
                    sl.sort(key=lambda t: -t[0])
                    for it in sl:
                        code = it[1]
                        if code == 0:
                            self._draw_prop(it[2], it[0])
                        elif code == 1:
                            self._draw_kart(it[2], it[0], lv)
                        elif code == 2:
                            self._draw_pad(it[2])
                        elif code == 3:
                            self._draw_lamp(it[2], lv)
                        elif code == 4:
                            self._draw_gate()
                        else:
                            self._draw_arch(it[2])
            prev = pts
            prev_i = i

    def _dp_of(self, x, y, z):
        c = self.cam
        dx, dy, dz = x - c.x, y - c.y, z - c.z
        return (dx * c.sy + dz * c.cy) * c.cp - dy * c.sp

    def _checker(self, A, B, lv):
        for r_ in range(2):
            for cidx in range(8):
                u0, u1 = cidx / 8.0, (cidx + 1) / 8.0
                v0, v1 = r_ * 0.5, (r_ + 1) * 0.5

                def pt(u, v):
                    # 도로 사각형 (A0,A1 먼쪽 / B0,B1 가까운쪽) 위의 쌍선형 보간
                    ax = A[0][0] + (A[1][0] - A[0][0]) * u
                    ay = A[0][1] + (A[1][1] - A[0][1]) * u
                    bx = B[0][0] + (B[1][0] - B[0][0]) * u
                    by = B[0][1] + (B[1][1] - B[0][1]) * u
                    return (ax + (bx - ax) * v, ay + (by - ay) * v, 1.0, 0, 0)
                if min(A[0][2], A[1][2], B[0][2], B[1][2]) <= self.near:
                    return
                col = (20, 20, 22) if (cidx + r_) % 2 else (245, 245, 245)
                self.poly(col, (pt(u0, v0), pt(u1, v0), pt(u1, v1), pt(u0, v1)))

    # ---- 장식물 --------------------------------------------------------------------------------
    def _draw_prop(self, p, dp):
        kind = p['kind']
        c = self.cam
        dx, dy, dz = p['x'] - c.x, p['y'] - c.y, p['z'] - c.z
        xr = -dx * c.cy + dz * c.sy
        zr = dx * c.sy + dz * c.cy
        d = zr * c.cp - dy * c.sp
        if d < 3.0:
            return
        yc = dy * c.cp + zr * c.sp
        inv = self.f / d
        sx = self.hx + xr * inv
        sy = self.hy - yc * inv
        wm, hm = SPRITE_DIM[kind][0], SPRITE_DIM[kind][1]
        s = p['s']
        var = 0
        if kind == 'building':
            wm = 14 + p['r1'] * 22
            hm = 30 + p['r3'] * p['r3'] * 150
            var = int(p['r2'] * 4)
        elif kind == 'mesa':
            wm, hm = wm * (1.2 + p['r1'] * 1.8), hm * (0.8 + p['r2'] * 1.6)
        elif kind == 'rock':
            wm, hm = wm * s * 1.3, hm * s * (1.0 + p['r1'] * 0.7)
        else:
            wm, hm = wm * s, hm * s
            if kind == 'roundtree':
                var = int(p['r1'] * 4)
            elif kind == 'lollipop':
                var = int(p['r1'] * 6)
            elif kind == 'icecream':
                var = int(p['r1'] * 3)
        hpx = inv * hm
        wpx = inv * wm
        if hpx < 2.5 or sy < 0 or sy - hpx > self.rh or sx + wpx * 0.5 < 0 or sx - wpx * 0.5 > self.rw:
            return
        if hpx > 1400:
            return
        tg = self.tg
        spr = tg.scaled_sprite(kind, var, wpx, hpx)
        lut = tg.fog_lut
        lv = lut[int(d) if d < len(lut) - 1 else len(lut) - 1]
        spr.set_alpha(255 - lv * 15 if lv else 255)
        self.surf.blit(spr, (int(sx - spr.get_width() / 2), int(sy - spr.get_height() + 1)))

    def _draw_lamp(self, data, lv):
        li, side = data
        tr = self.track
        x, y, z = self.GX[li * K + (5 if side > 0 else 4)], self.GY[li * K + 5], self.GZ[li * K + (5 if side > 0 else 4)]
        a = self.proj(x, y, z)
        b = self.proj(x, y + 9.5, z)
        if a[2] > self.near and b[2] > self.near:
            pygame.draw.line(self.surf, (60, 64, 80), (a[0], a[1]), (b[0], b[1]), 1)
            r = max(1, int(self.f * 0.7 / b[2]))
            pygame.draw.circle(self.surf, (255, 240, 190), (int(b[0]), int(b[1])), r)

    def _draw_arch(self, ai):
        tr = self.track
        col = hex_rgb(tr.theme['arches'])
        hw = tr.hw + 1.5
        prev = None
        for k in range(0, 13):
            a = math.pi * k / 12.0
            x, y, z = tr.edge_point(ai, -hw * math.cos(a))
            p = self.proj(x, y + hw * 0.0 + math.sin(a) * hw * 0.75 + 0.2, z)
            if prev is not None and prev[2] > self.near and p[2] > self.near:
                pygame.draw.line(self.surf, col, (prev[0], prev[1]), (p[0], p[1]), 2)
            prev = p

    def _draw_pad(self, pad):
        tr = self.track
        N = tr.N
        idx, d = pad['idx'], pad['d']
        hl, hw_ = pad['half_len'] / tr.ds, pad['half_w']

        def P(u, v):
            x, y, z, _h = tr.pose_at(idx + v * hl, d + u * hw_)
            return self.proj(x, y + 0.07, z)
        self.poly((10, 28, 70), (P(-1, -1), P(1, -1), P(1, 1), P(-1, 1)))
        for n, v0 in enumerate((-0.55, 0.0, 0.55)):
            col = (25, 230, 255) if n % 2 == 0 else (255, 225, 74)
            self.poly(col, (P(0, v0 + 0.32), P(0.9, v0 - 0.12), P(0.9, v0 - 0.34), P(0, v0 + 0.1), P(-0.9, v0 - 0.34), P(-0.9, v0 - 0.12)))

    def _draw_gate(self):
        tr = self.track
        T = (tr.tx[0], tr.ty[0], tr.tz[0])
        up = tr.surface_normal(0)
        Rv = (tr.rx[0], 0.0, tr.rz[0])
        org = (tr.px[0], tr.py[0], tr.pz[0])
        self.draw_boxes(org, Rv, up, T, self.gate_boxes, 1.0)

    # ---- 카트 -----------------------------------------------------------------------------------------
    def draw_boxes(self, org, Rv, Uv, Fv, boxes, shade, lod_fog=0):
        """박스 목록을 (org, R/U/F 기저)에서 3D 로 그린다. 각 박스: 보이는 면만 칠함."""
        c = self.cam
        f, hx, hy, near = self.f, self.hx, self.hy, self.near
        csy, ccy, csp, ccp = c.sy, c.cy, c.sp, c.cp
        ox, oy, oz = org[0] - c.x, org[1] - c.y, org[2] - c.z
        # 월드 벡터 -> 카메라 좌표 (x, y, depth)

        def cam_vec(v):
            xr = -v[0] * ccy + v[2] * csy
            zr = v[0] * csy + v[2] * ccy
            return (xr, v[1] * ccp + zr * csp, zr * ccp - v[1] * csp)
        O = cam_vec((ox, oy, oz))
        Rc, Uc, Fc = cam_vec(Rv), cam_vec(Uv), cam_vec(Fv)
        # 카메라의 로컬 좌표
        clx = -(ox * Rv[0] + oy * Rv[1] + oz * Rv[2])
        cly = -(ox * Uv[0] + oy * Uv[1] + oz * Uv[2])
        clz = -(ox * Fv[0] + oy * Fv[1] + oz * Fv[2])
        order = []
        for bx in boxes:
            dcen = O[2] + Rc[2] * bx[0] + Uc[2] * bx[1] + Fc[2] * bx[2]
            order.append((dcen, bx))
        order.sort(key=lambda t: -t[0])
        surf = self.surf
        rw, rh = self.rw, self.rh
        for dcen, bx in order:
            if dcen < -2.0:
                continue
            bcx, bcy, bcz, bhx, bhy, bhz, col, tx, ty, glow = bx
            vis = {'z+': clz > bcz + bhz, 'z-': clz < bcz - bhz, 'x+': clx > bcx + bhx, 'x-': clx < bcx - bhx, 'y+': cly > bcy + bhy}
            if not any(vis.values()):
                continue
            corners = []
            for idx in range(8):
                sx_ = 1 if idx & 4 else -1
                sy_ = 1 if idx & 2 else -1
                sz_ = 1 if idx & 1 else -1
                if sz_ > 0:
                    lx, ly = bcx + sx_ * bhx * tx, bcy + sy_ * bhy * ty
                else:
                    lx, ly = bcx + sx_ * bhx, bcy + sy_ * bhy
                lz = bcz + sz_ * bhz
                xr = O[0] + Rc[0] * lx + Uc[0] * ly + Fc[0] * lz
                yc = O[1] + Rc[1] * lx + Uc[1] * ly + Fc[1] * lz
                dp = O[2] + Rc[2] * lx + Uc[2] * ly + Fc[2] * lz
                if dp > near:
                    inv = f / dp
                    corners.append((hx + xr * inv, hy - yc * inv, dp, xr, yc))
                else:
                    corners.append((0.0, 0.0, dp, xr, yc))
            for name, ids, k in FACES:
                if not vis[name]:
                    continue
                cc = col if glow else shade_rgb(col, k * shade)
                self.poly(cc, [corners[i] for i in ids])

    def _draw_kart(self, rc, dp, lv):
        tg = self.tg
        qp = self.qp
        m = self.model(rc.kart_id)
        if dp < (1.0 if rc.kind == 'local' else 3.2):
            return
        h = rc.h
        up = rc.up
        fx, fz = math.sin(h), math.cos(h)
        # 도로면에 투영한 전방 벡터
        d = fx * up[0] + fz * up[2]
        Fv = (fx - up[0] * d, -up[1] * d, fz - up[2] * d)
        fl = math.sqrt(Fv[0] ** 2 + Fv[1] ** 2 + Fv[2] ** 2) or 1.0
        Fv = (Fv[0] / fl, Fv[1] / fl, Fv[2] / fl)
        Rv = (Fv[1] * up[2] - Fv[2] * up[1], Fv[2] * up[0] - Fv[0] * up[2], Fv[0] * up[1] - Fv[1] * up[0])   # F x U
        org = (rc.x, rc.y, rc.z)
        amb = 0.7 if tg.night else 1.0
        # 드리프트: 차체를 진행 방향에서 약간 틀어 보이게 (차체만 회전)
        yaw_off = 0.0
        if rc.drifting:
            yaw_off = -rc.drift_dir * 0.3
        elif abs(rc.slip) > 1.0:
            yaw_off = clamp(-rc.slip * 0.02, -0.25, 0.25)
        if yaw_off:
            cs, sn = math.cos(yaw_off), math.sin(yaw_off)
            Fn = tuple(Fv[i] * cs + Rv[i] * sn for i in range(3))
            Rn = tuple(Rv[i] * cs - Fv[i] * sn for i in range(3))
            Fv, Rv = Fn, Rn
        # 그림자
        if dp < qp['lod1']:
            L, W = m.L, m.W
            pts = []
            for a in range(8):
                t = a * TAU / 8
                lx, lz = math.cos(t) * W * 0.66, math.sin(t) * L * 0.62
                pts.append(self.proj(org[0] + Rv[0] * lx + Fv[0] * lz, org[1] + 0.05 + Rv[1] * lx + Fv[1] * lz, org[2] + Rv[2] * lx + Fv[2] * lz))
            base_col = tg.pal['grass_a' if rc.offroad else 'road_a'][lv]
            self.poly(shade_rgb(base_col, 0.5), pts)
        if dp > qp['lod1'] * 1.9:
            # 아주 먼 카트: 색 점
            p = self.proj(org[0], org[1] + 0.7, org[2])
            if p[2] > self.near:
                r = max(1, int(self.f * 1.0 / p[2]))
                pygame.draw.rect(self.surf, m.main, (int(p[0] - r), int(p[1] - r), r * 2 + 1, r + 1))
            return
        lod0 = dp < qp['lod0']
        # 부스트 불꽃
        if rc.boosting and dp < qp['lod1']:
            L = m.L
            ah = m.base + m.H * 0.3
            anc = (org[0] - Fv[0] * (L / 2) + up[0] * ah, org[1] - Fv[1] * (L / 2) + up[1] * ah, org[2] - Fv[2] * (L / 2) + up[2] * ah)
            for ln, col in ((1.9, (255, 140, 30)), (1.1, (255, 230, 120))):
                ln = ln * (0.8 + 0.4 * random_f())
                pa = self.proj(anc[0] + Rv[0] * 0.2, anc[1] + Rv[1] * 0.2, anc[2] + Rv[2] * 0.2)
                pb = self.proj(anc[0] - Rv[0] * 0.2, anc[1] - Rv[1] * 0.2, anc[2] - Rv[2] * 0.2)
                pt = self.proj(anc[0] - Fv[0] * ln, anc[1] - Fv[1] * ln, anc[2] - Fv[2] * ln)
                self.poly(col, (pa, pb, pt))
        boxes = m.boxes if lod0 else m.boxes_lod1
        # 바퀴 + 차체를 깊이순으로 섞어 그리기 위해: 뒤 바퀴 -> 차체 -> 앞 바퀴 (뒤에서 보는 시점에 적합)
        cam = self.cam
        cl = ((cam.x - org[0]) * Fv[0] + (cam.y - org[1]) * Fv[1] + (cam.z - org[2]) * Fv[2])
        wheels_back = [w for w in m.wheels if w[2] < 0]
        wheels_front = [w for w in m.wheels if w[2] > 0]
        first, second = (wheels_front, wheels_back) if cl < 0 else (wheels_back, wheels_front)
        for w in first:
            self._draw_wheel(m, w, org, Rv, up, Fv, rc, lod0, amb)
        self.draw_boxes(org, Rv, up, Fv, boxes, amb)
        # 드라이버 헬멧
        hp = m.helmet
        hxw = org[0] + Rv[0] * hp[0] + up[0] * hp[1] + Fv[0] * hp[2]
        hyw = org[1] + Rv[1] * hp[0] + up[1] * hp[1] + Fv[1] * hp[2]
        hzw = org[2] + Rv[2] * hp[0] + up[2] * hp[1] + Fv[2] * hp[2]
        hp_ = self.proj(hxw, hyw, hzw)
        if hp_[2] > self.near:
            r = max(2, int(self.f * 0.28 / hp_[2]))
            pygame.draw.circle(self.surf, shade_rgb(m.main, amb * 0.8), (int(hp_[0]), int(hp_[1])), r)
            pygame.draw.circle(self.surf, shade_rgb(m.main, amb * 1.3), (int(hp_[0] - r * 0.3), int(hp_[1] - r * 0.3)), max(1, r // 2))
            if cl > 0 and lod0:
                pygame.draw.rect(self.surf, (12, 12, 14), (int(hp_[0] - r * 0.7), int(hp_[1] - r * 0.15), max(2, int(r * 1.4)), max(1, int(r * 0.45))))
        for w in second:
            self._draw_wheel(m, w, org, Rv, up, Fv, rc, lod0, amb)
        # 이름표
        if rc.kind != 'local' and 14 < dp < 150:
            p = self.proj(org[0] + up[0] * 2.4, org[1] + up[1] * 2.4, org[2] + up[2] * 2.4)
            if p[2] > self.near:
                self.labels.append((p[0], p[1], rc.name, (255, 210, 120) if rc.kind == 'bot' else (150, 232, 255), dp))

    def _draw_wheel(self, m, w, org, Rv, Uv, Fv, rc, lod0, amb):
        lx, ly, lz, sgn, front = w
        R, ww = m.wheel_r, m.wheel_w
        if not lod0:
            self.draw_boxes(org, Rv, Uv, Fv, [(lx, ly, lz, ww / 2, R, R, (26, 26, 30), 1, 1, False)], amb)
            return
        cam = self.cam
        # 바퀴 중심(월드)
        ctr = (org[0] + Rv[0] * lx + Uv[0] * ly + Fv[0] * lz, org[1] + Rv[1] * lx + Uv[1] * ly + Fv[1] * lz, org[2] + Rv[2] * lx + Uv[2] * ly + Fv[2] * lz)
        spin = self._wheel_phase(rc)
        steer = -rc.steer * 0.45 if front else 0.0
        cs, sn = math.cos(steer), math.sin(steer)
        # 앞바퀴 조향: 회전축(로컬 x)을 y축 둘레로 돌림
        ax = (Rv[0] * cs + Fv[0] * sn, Rv[1] * cs + Fv[1] * sn, Rv[2] * cs + Fv[2] * sn)
        fw = (Fv[0] * cs - Rv[0] * sn, Fv[1] * cs - Rv[1] * sn, Fv[2] * cs - Rv[2] * sn)
        hxw = ww / 2.0
        ring = []
        for k in range(6):
            a = spin + k * math.pi / 3.0
            ca, sa = math.cos(a) * R, math.sin(a) * R
            ring.append((Uv[0] * ca + fw[0] * sa, Uv[1] * ca + fw[1] * sa, Uv[2] * ca + fw[2] * sa))
        capA = []
        capB = []
        for r_ in ring:
            capA.append(self.proj(ctr[0] + ax[0] * hxw + r_[0], ctr[1] + ax[1] * hxw + r_[1], ctr[2] + ax[2] * hxw + r_[2]))
            capB.append(self.proj(ctr[0] - ax[0] * hxw + r_[0], ctr[1] - ax[1] * hxw + r_[1], ctr[2] - ax[2] * hxw + r_[2]))
        # 카메라가 어느 캡 쪽에 있나
        v = (cam.x - ctr[0], cam.y - ctr[1], cam.z - ctr[2])
        side = v[0] * ax[0] + v[1] * ax[1] + v[2] * ax[2]
        tire = shade_rgb((34, 34, 40), amb)
        # 접지면(트레드) 먼저
        for k in range(6):
            a = spin + (k + 0.5) * math.pi / 3.0
            nx = Uv[0] * math.cos(a) + fw[0] * math.sin(a)
            ny = Uv[1] * math.cos(a) + fw[1] * math.sin(a)
            nz = Uv[2] * math.cos(a) + fw[2] * math.sin(a)
            if (v[0] * nx + v[1] * ny + v[2] * nz) > R * 0.866:
                shade = 0.7 + 0.3 * (0.5 + 0.5 * math.sin(a * 1.0))
                k2 = (k + 1) % 6
                self.poly(shade_rgb(tire, shade * (1.0 + (0.15 if k % 2 else 0.0))), (capA[k], capA[k2], capB[k2], capB[k]))
        if abs(side) > hxw:
            cap = capA if side > 0 else capB
            rim = m.rim_color
            self.poly(shade_rgb((26, 26, 30), amb), cap)
            # 림(안쪽 6각형)
            ctrp = self.proj(ctr[0] + ax[0] * (hxw + 0.01) * (1 if side > 0 else -1), ctr[1] + ax[1] * (hxw + 0.01) * (1 if side > 0 else -1), ctr[2] + ax[2] * (hxw + 0.01) * (1 if side > 0 else -1))
            if ctrp[2] > self.near:
                inner = []
                for p_ in cap:
                    inner.append((ctrp[0] + (p_[0] - ctrp[0]) * 0.68, ctrp[1] + (p_[1] - ctrp[1]) * 0.68, p_[2], p_[3], p_[4]))
                self.poly(rim if m.rim in (3, 4) else shade_rgb(rim, amb), inner)
                if m.rim in (1, 2):
                    for k in range(0, 6, 1 if m.rim == 2 else 2):
                        pygame.draw.line(self.surf, (30, 30, 36), (ctrp[0], ctrp[1]), (inner[k][0], inner[k][1]), 1)
                else:
                    hub = [(ctrp[0] + (p_[0] - ctrp[0]) * 0.28, ctrp[1] + (p_[1] - ctrp[1]) * 0.28, p_[2], p_[3], p_[4]) for p_ in cap]
                    self.poly((40, 40, 48), hub)

    def _wheel_phase(self, rc):
        return (rc.total * self.track.ds / 0.4) % TAU if self.track is not None else 0.0

    # ---- 프레임 ----------------------------------------------------------------------------------------
    def render(self, race, cam_pos, focus_idx, dirn, boost_fx=0.0, speed_ratio=0.0, t=0.0):
        self.labels = []
        self.cam.set(*cam_pos)
        self.draw_background()
        self.draw_world(race, focus_idx, dirn)
        self._draw_particles()
        self._draw_weather()
        if boost_fx > 0 or speed_ratio > 0.92:
            self._speed_lines(max(boost_fx, (speed_ratio - 0.9) * 4), t)
        return self.surf

    def _draw_particles(self):
        s = self.surf
        for p in self.parts:
            pr = self.proj(p[0], p[1], p[2])
            if pr[2] <= self.near:
                continue
            life = p[6] / p[7]
            r = max(1, int(p[9] * self.f / pr[2] * (0.4 + life)))
            col = p[8]
            col = (int(col[0] * (0.5 + 0.5 * life)), int(col[1] * (0.5 + 0.5 * life)), int(col[2] * (0.5 + 0.5 * life)))
            if 0 <= pr[0] < self.rw and 0 <= pr[1] < self.rh:
                pygame.draw.circle(s, col, (int(pr[0]), int(pr[1])), r)

    def _draw_weather(self):
        if not self.weather:
            return
        col = {'snow': (255, 255, 255), 'ember': (255, 150, 50), 'leaf': (217, 100, 40), 'sprinkle': (255, 120, 200)}.get(self.wtype, (255, 255, 255))
        s = self.surf
        for w in self.weather:
            if self.wtype == 'sprinkle':
                pygame.draw.rect(s, [(255, 120, 200), (120, 220, 255), (255, 230, 100)][int(w[0]) % 3], (int(w[0]), int(w[1]), 2, 3))
            elif w[4] > 1:
                pygame.draw.circle(s, col, (int(w[0]), int(w[1])), 1)
            else:
                s.set_at((int(w[0]) % self.rw, int(w[1]) % self.rh), col)

    def _speed_lines(self, amt, t):
        s = self.surf
        cx, cy = self.hx, self.hy * 1.05
        rnd = Rng(int(t * 24))
        n = int(10 + 14 * clamp(amt, 0, 1))
        for _ in range(n):
            a = rnd() * TAU
            r1 = self.rh * (0.42 + rnd() * 0.25)
            r2 = r1 + self.rh * (0.12 + rnd() * 0.2)
            c = int(150 + 100 * rnd())
            pygame.draw.line(s, (c, c, c), (cx + math.cos(a) * r1 * 1.4, cy + math.sin(a) * r1), (cx + math.cos(a) * r2 * 1.4, cy + math.sin(a) * r2), 1)


def random_f():
    return _random.random()


# ============================================================================
#  [폰] 언어 / 폰트 / 포인터(터치) / 즉시모드 UI 위젯 / 온스크린 키보드
# ============================================================================
LANG = 'ko'


def T(ko, en):
    return ko if LANG == 'ko' else en


FONT_DIRS = ['/system/fonts', '/system/font', '/product/fonts', '/data/fonts', '/usr/share/fonts', '/System/Library/Fonts',
             'C:/Windows/Fonts', '/Library/Fonts']
FONT_HINTS = ('cjk', 'korean', 'nanum', 'malgun', 'gothic', 'hangul', 'notosanskr', 'sansfallback', 'applesd', 'wqy', 'unifont', 'seckorean')
FONT_FIRST = ['kart3d_font.ttf', 'kart3d_font.otf', 'kart3d_font.ttc',
              '/system/fonts/NotoSansCJK-Regular.ttc', '/system/fonts/NotoSansCJKkr-Regular.otf', '/system/fonts/NotoSansKR-Regular.otf',
              '/system/fonts/NotoSansKR-Regular.ttf', '/system/fonts/NanumGothic.ttf', '/system/fonts/DroidSansFallback.ttf',
              'C:/Windows/Fonts/malgun.ttf', '/System/Library/Fonts/AppleSDGothicNeo.ttc', '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
              '/usr/share/fonts/truetype/nanum/NanumGothic.ttf', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
              '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc']


def has_hangul(path):
    try:
        f = pygame.font.Font(path, 24)
        a = f.render('\ud55c\uae00', False, (255, 255, 255))
        b = f.render('\uffff\uffff', False, (255, 255, 255))
        return a.get_width() > 8 and pygame.image.tostring(a, 'RGBA') != pygame.image.tostring(b, 'RGBA')
    except Exception:
        return False


def find_korean_font():
    tried = set()

    def ok(p):
        if p in tried:
            return False
        tried.add(p)
        return os.path.isfile(p) and has_hangul(p)
    try:
        here = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv and sys.argv[0] else '.'
    except Exception:
        here = '.'
    for p in FONT_FIRST:
        if not os.path.isabs(p):
            p = os.path.join(here, p)
        if ok(p):
            return p
    for d in FONT_DIRS:
        try:
            names = []
            for root, _dirs, files in os.walk(d):
                for fn in files:
                    low = fn.lower()
                    if low.endswith(('.ttf', '.otf', '.ttc')) and any(h in low for h in FONT_HINTS):
                        names.append(os.path.join(root, fn))
                if len(names) > 60:
                    break
            for p in sorted(names):
                if ok(p):
                    return p
        except Exception:
            continue
    return None


def rrect(surf, color, rect, r):
    try:
        pygame.draw.rect(surf, color, rect, border_radius=int(r))
    except TypeError:
        pygame.draw.rect(surf, color, rect)


class Pointers(object):
    """터치/마우스 입력 통합. 손가락 여러 개를 동시에 추적한다."""

    def __init__(self):
        self.fingers = {}
        self.mouse = None
        self.taps = []
        self._last_tap = (0.0, -999, -999)
        self.has_touch = False

    def _tap(self, x, y):
        t = time.time()
        lt = self._last_tap
        if t - lt[0] < 0.18 and abs(x - lt[1]) < 40 and abs(y - lt[2]) < 40:
            return                      # 터치 + 에뮬레이트된 마우스 이벤트 중복 제거
        self._last_tap = (t, x, y)
        self.taps.append((x, y))

    def handle(self, e, sw, sh):
        et = e.type
        if hasattr(pygame, 'FINGERDOWN') and et in (pygame.FINGERDOWN, pygame.FINGERMOTION):
            self.has_touch = True
            self.fingers[e.finger_id] = (e.x * sw, e.y * sh)
        elif hasattr(pygame, 'FINGERUP') and et == pygame.FINGERUP:
            self.has_touch = True
            p = self.fingers.pop(e.finger_id, (e.x * sw, e.y * sh))
            self._tap(p[0], p[1])
        elif et == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.mouse = e.pos
        elif et == pygame.MOUSEMOTION and self.mouse is not None:
            self.mouse = e.pos
        elif et == pygame.MOUSEBUTTONUP and e.button == 1:
            self.mouse = None
            self._tap(e.pos[0], e.pos[1])

    def down(self):
        pts = list(self.fingers.values())
        if self.mouse is not None:
            pts.append(self.mouse)
        return pts

    def take_taps(self):
        t = self.taps
        self.taps = []
        return t


class UI(object):
    """즉시모드 위젯: 그리면서 동시에 탭 여부를 돌려준다."""

    def __init__(self, font_path):
        self.font_path = font_path
        self.fonts = {}
        self.cache = {}
        self.panels = {}
        self.taps = []
        self.down = []
        self.u = 1.0

    def begin(self, taps, down, sw, sh):
        self.taps = taps
        self.down = down
        self.sw, self.sh = sw, sh
        self.u = min(sw, sh) / 540.0

    def font(self, size):
        size = max(8, int(size))
        f = self.fonts.get(size)
        if f is None:
            f = self.fonts[size] = pygame.font.Font(self.font_path, size)
        return f

    def render(self, text, size, color):
        key = (text, int(size), color)
        s = self.cache.get(key)
        if s is None:
            if len(self.cache) > 500:
                self.cache.clear()
            s = self.cache[key] = self.font(size).render(text, True, color)
        return s

    def text(self, surf, text, x, y, size, color=(255, 255, 255), anchor='l', shadow=True):
        s = self.render(text, size, color)
        w, h = s.get_size()
        if anchor == 'c':
            x -= w // 2
        elif anchor == 'r':
            x -= w
        if shadow:
            d = max(1, int(size) // 16)
            surf.blit(self.render(text, size, (0, 0, 0)), (x + d, y + d))
        surf.blit(s, (x, y))
        return w, h

    def panel(self, surf, rect, alpha=175, color=(8, 12, 28), radius=16):
        key = (rect.w, rect.h, alpha, color, radius)
        p = self.panels.get(key)
        if p is None:
            if len(self.panels) > 40:
                self.panels.clear()
            p = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            rrect(p, (color[0], color[1], color[2], alpha), p.get_rect(), radius)
            self.panels[key] = p
        surf.blit(p, rect.topleft)

    def tapped(self, rect):
        for t in self.taps:
            if rect.collidepoint(t):
                self.taps.remove(t)
                return True
        return False

    def pressed(self, rect):
        for p in self.down:
            if rect.collidepoint(p):
                return True
        return False

    def button(self, surf, rect, label, kind='normal', size=None, enabled=True):
        pr = enabled and self.pressed(rect)
        cols = {'normal': ((40, 48, 78), (62, 74, 118)), 'primary': ((236, 70, 70), (255, 120, 60)), 'ghost': ((22, 26, 44), (44, 52, 84)),
                'chip': ((34, 40, 66), (58, 68, 108)), 'chipon': ((25, 190, 225), (80, 225, 250)), 'danger': ((170, 40, 56), (220, 70, 80)),
                'good': ((40, 160, 90), (70, 205, 120))}
        base, hi = cols.get(kind, cols['normal'])
        if not enabled:
            base = hi = (50, 52, 62)
        c = hi if pr else base
        r = rect.inflate(-4, -4) if pr else rect
        rrect(surf, (0, 0, 0), r.move(0, max(2, int(r.h * 0.06))), r.h * 0.28)
        rrect(surf, c, r, r.h * 0.28)
        rrect(surf, shade_rgb(c, 1.25), pygame.Rect(r.x + 3, r.y + 2, r.w - 6, max(2, r.h // 8)), r.h * 0.1)
        if size is None:
            size = r.h * 0.46
        tc = (255, 255, 255) if enabled else (140, 140, 150)
        if kind == 'chipon':
            tc = (6, 20, 34)
        s = self.render(label, size, tc)
        if s.get_width() > r.w - 8:
            size = size * (r.w - 8) / float(s.get_width())
            s = self.render(label, size, tc)
        surf.blit(s, (r.centerx - s.get_width() // 2, r.centery - s.get_height() // 2))
        return enabled and self.tapped(rect)

    def stepper(self, surf, rect, label, value, lo=None, hi=None):
        """[라벨      ◀  값  ▶]  -> -1 / 0 / +1"""
        u = self.u
        self.text(surf, label, rect.x, rect.centery - 11 * u, 22 * u, (210, 220, 245))
        bw = rect.h
        res = 0
        lb = pygame.Rect(rect.right - bw * 3.4, rect.y, bw, rect.h)
        rb = pygame.Rect(rect.right - bw, rect.y, bw, rect.h)
        if self.button(surf, lb, '<', 'normal', enabled=(lo is None or value > lo)):
            res = -1
        if self.button(surf, rb, '>', 'normal', enabled=(hi is None or value < hi)):
            res = 1
        self.text(surf, str(value), (lb.right + rb.x) // 2, rect.centery - 13 * u, 26 * u, (255, 220, 120), 'c')
        return res


class OnScreenKeyboard(object):
    """텍스트/IP 입력용 화면 키보드 (모바일 소프트 키보드가 불안정해서 직접 그린다)"""

    def __init__(self, title, text, mode, maxlen, on_ok):
        self.title, self.text, self.mode, self.maxlen, self.on_ok = title, text, mode, maxlen, on_ok
        self.shift = False
        self.blink = 0.0

    def rows(self):
        if self.mode == 'ip':
            return ['123', '456', '789', '.0:']
        rs = ['1234567890', 'qwertyuiop', 'asdfghjkl-', 'zxcvbnm_.']
        return [r.upper() if self.shift else r for r in rs]

    def key(self, ch):
        if len(self.text) < self.maxlen:
            self.text += ch

    def handle_key_event(self, e):
        if e.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return 'ok'
        elif e.key == pygame.K_ESCAPE:
            return 'cancel'
        elif e.unicode and e.unicode.isprintable() and len(e.unicode) == 1:
            if self.mode != 'ip' or e.unicode in '0123456789.:':
                self.key(e.unicode)
        return None

    def draw(self, ui, surf, sw, sh, dt):
        u = ui.u
        self.blink += dt
        veil = pygame.Surface((sw, sh), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 170))
        surf.blit(veil, (0, 0))
        res = None
        if self.mode == 'ip':
            kw, kh = int(min(sw * 0.5, 120 * u * 3)), int(min(sh * 0.12, 62 * u))
            gx, gy = 4 * u * 2, 4 * u * 2
        else:
            kw, kh = int(min(sw / 11.0, 90 * u)), int(min(sh * 0.11, 60 * u))
            gx, gy = 6 * u, 6 * u
        rows = self.rows()
        ncol = max(len(r) for r in rows)
        total_w = ncol * kw + (ncol - 1) * gx
        total_h = (len(rows) + 1) * kh + len(rows) * gy
        x0 = (sw - total_w) // 2
        y0 = sh - total_h - int(14 * u)
        # 입력창
        box = pygame.Rect(x0, y0 - int(112 * u), total_w, int(92 * u))
        ui.panel(surf, box, 240, (14, 18, 36), 14)
        ui.text(surf, self.title, box.x + 14 * u, box.y + 6 * u, 20 * u, (190, 205, 240))
        shown = self.text + ('|' if int(self.blink * 2) % 2 == 0 else ' ')
        ui.text(surf, shown, box.x + 16 * u, box.y + 36 * u, 34 * u, (255, 255, 255))
        for ri, row in enumerate(rows):
            rw_ = len(row) * kw + (len(row) - 1) * gx
            rx = x0 + (total_w - rw_) // 2
            for ci, ch in enumerate(row):
                r = pygame.Rect(rx + ci * (kw + gx), y0 + ri * (kh + gy), kw, kh)
                if ui.button(surf, r, ch, 'normal', size=kh * 0.5):
                    self.key(ch)
        by = y0 + len(rows) * (kh + gy)
        bw3 = (total_w - 3 * gx) // 4
        specs = []
        if self.mode != 'ip':
            specs.append(('Aa', 'chipon' if self.shift else 'normal', 'shift'))
        else:
            specs.append(('', 'ghost', None))
        specs += [('<-', 'normal', 'bs'), (T('취소', 'Cancel'), 'ghost', 'cancel'), ('OK', 'primary', 'ok')]
        for i, (lab, kind, act) in enumerate(specs):
            r = pygame.Rect(x0 + i * (bw3 + gx), by, bw3, kh)
            if act is None:
                continue
            if ui.button(surf, r, lab, kind, size=kh * 0.46):
                if act == 'shift':
                    self.shift = not self.shift
                elif act == 'bs':
                    self.text = self.text[:-1]
                else:
                    res = act
        ui.taps[:] = []        # 키보드가 떠 있는 동안 다른 위젯이 탭을 받지 않게
        return res


# ============================================================================
#  [폰] 터치 조작 버튼 / HUD / 미니맵 / 사운드
# ============================================================================
class TouchControls(object):
    def __init__(self):
        self.btn = {}
        self.cache = {}

    def layout(self, sw, sh, auto_gas):
        r = int(min(sh * 0.125, sw * 0.085))
        self.r = r
        y = sh - int(r * 1.45)
        self.btn = {
            'left': (int(r * 1.3), y, r),
            'right': (int(r * 3.55), y, r),
            'drift': (sw - int(r * 1.5), y, int(r * 1.15)),
            'brake': (sw - int(r * 1.5), y - int(r * 2.35), int(r * 0.8)),
            'gas': (sw - int(r * 3.85), y + int(r * 0.15), int(r * 0.95)),
        }
        self.auto_gas = auto_gas

    def read(self, points):
        pressed = set()
        for (px, py) in points:
            for name, (cx, cy, rad) in self.btn.items():
                if name == 'gas' and self.auto_gas:
                    continue
                if (px - cx) ** 2 + (py - cy) ** 2 <= (rad * 1.3) ** 2:
                    pressed.add(name)
        return pressed

    def _disc(self, rad, on, color):
        key = (rad, on, color)
        s = self.cache.get(key)
        if s is None:
            s = pygame.Surface((rad * 2 + 4, rad * 2 + 4), pygame.SRCALPHA)
            a = 150 if on else 70
            pygame.draw.circle(s, (color[0], color[1], color[2], a), (rad + 2, rad + 2), rad)
            pygame.draw.circle(s, (255, 255, 255, 170 if on else 90), (rad + 2, rad + 2), rad, max(2, rad // 14))
            self.cache[key] = s
        return s

    def draw(self, surf, ui, pressed):
        u = ui.u
        for name, (cx, cy, rad) in self.btn.items():
            if name == 'gas' and self.auto_gas:
                continue
            on = name in pressed
            col = {'left': (120, 160, 255), 'right': (120, 160, 255), 'drift': (255, 150, 40), 'brake': (255, 80, 80), 'gas': (90, 220, 120)}[name]
            d = self._disc(rad, on, col)
            surf.blit(d, (cx - rad - 2, cy - rad - 2))
            wht = (255, 255, 255)
            if name in ('left', 'right'):
                s = 1 if name == 'right' else -1
                k = rad * 0.45
                pygame.draw.polygon(surf, wht, [(cx + s * k, cy), (cx - s * k * 0.6, cy - k), (cx - s * k * 0.6, cy + k)])
            else:
                lab = {'drift': 'DRIFT', 'brake': T('브레이크', 'BRAKE'), 'gas': 'GAS'}[name]
                ui.text(surf, lab, cx, cy - rad * 0.2, rad * 0.42, wht, 'c')


def build_minimap(track, size, theme_col):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    b = track.bounds
    span = max(b[1] - b[0], b[3] - b[2], 1.0)
    sc = (size - 16) / span
    ox = (size - (b[1] - b[0]) * sc) / 2
    oz = (size - (b[3] - b[2]) * sc) / 2
    pts = [(ox + (track.px[i] - b[0]) * sc, oz + (track.pz[i] - b[2]) * sc) for i in range(0, track.N, 2)]
    rrect(s, (0, 0, 0, 90), s.get_rect(), size * 0.12)
    pygame.draw.lines(s, (0, 0, 0, 255), True, pts, max(5, size // 22))
    pygame.draw.lines(s, (235, 238, 250, 255), True, pts, max(3, size // 36))
    s0 = pts[0]
    pygame.draw.circle(s, (255, 255, 255, 255), (int(s0[0]), int(s0[1])), max(3, size // 36))
    return s, (b[0], b[2], sc, ox, oz)


def draw_minimap(ui, surf, mini, tf, race, x, y):
    surf.blit(mini, (x, y))
    b0, b2, sc, ox, oz = tf
    for rc in race.racers:
        px = x + ox + (rc.x - b0) * sc
        py = y + oz + (rc.z - b2) * sc
        if rc is race.local:
            continue
        col = (255, 110, 110) if rc.kind == 'bot' else (90, 230, 255)
        pygame.draw.circle(surf, col, (int(px), int(py)), max(3, int(ui.u * 4)))
    rc = race.local
    px = x + ox + (rc.x - b0) * sc
    py = y + oz + (rc.z - b2) * sc
    pygame.draw.circle(surf, (255, 255, 255), (int(px), int(py)), max(5, int(ui.u * 7)))
    pygame.draw.circle(surf, (255, 176, 32), (int(px), int(py)), max(4, int(ui.u * 5)))


def fmt_time(t):
    m = int(t // 60)
    return '%d:%05.2f' % (m, t - m * 60)


def draw_hud(app, surf, race, dt):
    ui = app.ui
    u = ui.u
    sw, sh = app.W, app.H
    loc = race.local
    sim = loc.sim
    ranking = race.ranking()
    pos = ranking.index(loc) + 1
    # 순위
    ui.text(surf, str(pos), 18 * u, 8 * u, 84 * u, (255, 176, 32))
    nw = ui.render(str(pos), 84 * u, (255, 176, 32)).get_width()
    ui.text(surf, '/%d' % len(race.racers), 22 * u + nw, 44 * u, 34 * u, (255, 255, 255))
    ui.text(surf, 'LAP %d/%d' % (min(race.laps, sim.lap), race.laps), 20 * u, 98 * u, 28 * u)
    ui.text(surf, fmt_time(max(0.0, race.t)), 20 * u, 130 * u, 26 * u, (220, 230, 255))
    # 미니맵
    ms = int(min(sh * 0.34, 200 * u))
    if app.mini is None or app.mini[0].get_width() != ms:
        app.mini = build_minimap(race.track, ms, None)
    mx, my = sw - ms - 12 * u, 10 * u
    draw_minimap(ui, surf, app.mini[0], app.mini[1], race, int(mx), int(my))
    ui.text(surf, '#%d %s' % (race.map_id, race.track.info['name' if LANG == 'ko' else 'name_en']), sw - 14 * u, my + ms + 2 * u, 15 * u, (215, 225, 250), 'r')
    # 속도계
    kmh = int(sim.speed * 3.6)
    cx = int(sw * 0.70) if sw > sh else sw // 2 + int(sw * 0.18)
    by = sh - int(app.touch.r * 1.0) if app.touch.btn else sh - 90 * u
    ui.text(surf, str(kmh), cx, by - 64 * u, 70 * u, (255, 255, 255), 'r')
    ui.text(surf, 'km/h', cx + 6 * u, by - 36 * u, 24 * u, (200, 215, 245))
    bw = int(220 * u)
    pygame.draw.rect(surf, (0, 0, 0), (cx - bw, by + 4 * u, bw, 10 * u), border_radius=5)
    ratio = clamp(sim.speed / sim.stats['max_speed'], 0, 1.0)
    pygame.draw.rect(surf, (25, 230, 255) if sim.boost_t <= 0 else (255, 160, 40), (cx - bw, by + 4 * u, int(bw * ratio), 10 * u), border_radius=5)
    if sim.boost_t > 0:
        pygame.draw.rect(surf, (255, 255, 255), (cx - bw, by + 17 * u, int(bw * clamp(sim.boost_t / 1.9, 0, 1)), 6 * u), border_radius=3)
    if sim.drifting:
        tc = [(170, 200, 255), (60, 170, 255), (255, 160, 40), (210, 80, 255)][sim.drift_tier]
        pygame.draw.rect(surf, (0, 0, 0), (cx - bw, by + 26 * u, bw, 8 * u), border_radius=4)
        pygame.draw.rect(surf, tc, (cx - bw, by + 26 * u, int(bw * clamp(sim.drift_charge / 3.2, 0, 1)), 8 * u), border_radius=4)
    # 순위표
    if sh >= 380 and sw > sh:
        y = 170 * u
        for i, r in enumerate(ranking[:6]):
            me = r is loc
            row = pygame.Rect(int(12 * u), int(y), int(190 * u), int(24 * u))
            ui.panel(surf, row, 200 if me else 110, (255, 176, 32) if me else (0, 0, 0), 8)
            ui.text(surf, '%d' % (i + 1), row.x + 8 * u, row.y + 2 * u, 18 * u, (20, 20, 20) if me else (255, 255, 255), shadow=False)
            ui.text(surf, r.name, row.x + 30 * u, row.y + 2 * u, 18 * u, (20, 20, 20) if me else (235, 240, 255), shadow=False)
            y += 27 * u
    # 카운트다운 / 알림
    if race.phase == 'count':
        n = int(math.ceil(max(0.0, race.count_left)))
        if 1 <= n <= 3:
            frac = race.count_left - (n - 1)
            size = (150 + 60 * frac) * u
            ui.text(surf, str(n), sw // 2, int(sh * 0.2), size, (255, 255, 255), 'c')
    if sim.wrong_way and race.phase == 'run' and not loc.finished:
        ui.text(surf, T('역주행!', 'WRONG WAY!'), sw // 2, int(sh * 0.36), 50 * u, (255, 80, 90), 'c')
    now = time.time()
    app.toasts = [t for t in app.toasts if t[1] > now]
    ty = int(sh * 0.16)
    for text, until, color, big in app.toasts[-2:]:
        a = clamp((until - now) * 3.0, 0.0, 1.0)
        ui.text(surf, text, sw // 2, ty, (62 if big else 38) * u, color, 'c')
        ty += int((70 if big else 46) * u)


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


# ============================================================================
#  [폰] 앱: 화면(메뉴/솔로/차고/설정/멀티/로비/레이스/결과) + 메인 루프
# ============================================================================
def R(x, y, w, h):
    return pygame.Rect(int(x), int(y), int(w), int(h))


class ShowKart(object):
    """쇼룸(메뉴/차고 배경)에서 돌아가는 카트용 가짜 Racer + 가짜 Race"""

    def __init__(self, track, kart_id):
        rc = Racer('show', '', kart_id, 0, 'bot')
        pf = track.N - 9.0
        x, y, z, h = track.pose_at(pf, 0.0)
        rc.x, rc.y, rc.z, rc.h = x, y, z, h
        rc.idx = int(pf) % track.N
        rc.up = track.surface_normal(rc.idx)
        rc.total = 0.0
        self.rc = rc
        self.racers = [rc]
        self.local = None


class App(object):
    def __init__(self, args):
        global LANG
        self.args = args
        try:
            pygame.mixer.pre_init(22050, -16, 1, 512)
        except Exception:
            pass
        pygame.init()
        try:
            if args.get('window'):
                w, h = args['window']
                self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
            else:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        except Exception:
            self.screen = pygame.display.set_mode((960, 540))
        if self.screen.get_width() < 200 or self.screen.get_height() < 200:
            self.screen = pygame.display.set_mode((960, 540))
        pygame.display.set_caption('TURBO KART 3D')
        self.W, self.H = self.screen.get_size()
        self.profile = Profile()
        self.font_path = find_korean_font()
        lang = args.get('lang') or self.profile['lang']
        if lang == 'auto':
            lang = 'ko' if self.font_path else 'en'
        LANG = lang
        self.ui = UI(self.font_path)
        self.ptr = Pointers()
        self.sfx = Sfx(self.profile['sound'])
        self.session = Session(self.profile)
        self.renderer = Renderer(self.W, self.H, int(self.profile['quality']))
        self.cam = ChaseCam()
        self.touch = TouchControls()
        self.touch.layout(self.W, self.H, self.profile['auto_gas'])
        self.clock = pygame.time.Clock()
        self.scene = 'menu'
        self.race = None
        self.kb = None
        self.toasts = []
        self.mini = None
        self.keys = set()
        self.used_keyboard = False
        self.steer = 0.0
        self.dirn = 1
        self.paused = False
        self.running = True
        self.t = 0.0
        self.show = None
        self.show_map = None
        self.show_kart = None
        self.outline_cache = {}
        self.scan = {'busy': False, 'rooms': [], 'done': False}
        self.err = ''
        self.sel_map = int(self.profile['map'])
        self.slow_t = 0.0
        self.fps_ema = 60.0
        self.show_fps = bool(args.get('fps'))
        self.finish_at = None
        self.ping = 0.0

    # ------------------------------------------------------------------ 공통 도우미
    @property
    def landscape(self):
        return self.W >= self.H * 1.15

    def toast(self, text, dur=1.4, color=(255, 200, 70), big=False):
        self.toasts.append((text, time.time() + dur, color, big))

    def loading(self, msg):
        self.screen.fill((8, 12, 26))
        self.ui.text(self.screen, msg, self.W // 2, self.H // 2 - 20 * self.ui.u, 40 * self.ui.u, (255, 255, 255), 'c')
        pygame.display.flip()
        pygame.event.pump()

    def present(self, surf):
        try:
            if surf.get_size() == (self.W, self.H):
                self.screen.blit(surf, (0, 0))
            else:
                pygame.transform.scale(surf, (self.W, self.H), self.screen)
        except Exception:
            self.screen.blit(pygame.transform.scale(surf, (self.W, self.H)), (0, 0))

    def on_resize(self):
        self.W, self.H = self.screen.get_size()
        self.renderer.set_quality(self.renderer.q, self.W, self.H)
        self.touch.layout(self.W, self.H, self.profile['auto_gas'])
        self.mini = None
        self.show_map = None

    def set_quality(self, q):
        self.profile['quality'] = q
        self.profile.save()
        self.renderer.set_quality(q, self.W, self.H)

    def go(self, scene):
        self.scene = scene
        self.err = ''
        self.sfx.play('click', 0.6)
        if scene == 'solo':
            self.sel_map = int(self.profile['map'])
        if scene == 'multi':
            self.scan_rooms()

    def map_text(self, mid):
        i = map_info(mid)
        return (i['name'], i['theme_name']) if LANG == 'ko' else (i['name_en'], i['theme_en'])

    # ------------------------------------------------------------------ 쇼룸(3D 배경)
    def ensure_show(self, kart_id):
        mid = int(self.profile['map'])
        if self.show_map != mid or self.show is None:
            self.loading(T('준비 중…', 'Preparing…'))
            tr = Track(mid)
            self.renderer.set_track(tr)
            self.show_map = mid
            self.show = ShowKart(tr, kart_id)
            self.show_kart = kart_id
        if self.show_kart != kart_id:
            self.show.rc.kart_id = kart_id
            self.show_kart = kart_id

    def draw_show(self, dt, kart_id, shift=0.0, dist=6.3):
        self.ensure_show(kart_id)
        rc = self.show.rc
        tr = self.renderer.track
        rc.total += dt * 8.0
        th = self.t * 0.5
        cx, cy, cz = rc.x, rc.y + 0.9, rc.z
        camx, camz = cx + math.sin(th) * dist, cz + math.cos(th) * dist
        camy = cy + 1.5
        yaw = math.atan2(cx - camx, cz - camz) + shift
        pitch = math.atan2(camy - cy, math.hypot(cx - camx, cz - camz))
        dot = math.sin(yaw) * tr.tx[rc.idx] + math.cos(yaw) * tr.tz[rc.idx]
        dirn = 1 if dot >= 0 else -1
        surf = self.renderer.render(self.show, (camx, camy, camz, yaw, pitch), rc.idx, dirn, 0.0, 0.0, self.t)
        self.present(surf)

    # ------------------------------------------------------------------ 입력
    def pump_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if self.kb is not None:
                    r = self.kb.handle_key_event(e)
                    if r:
                        self.close_kb(r)
                    continue
                self.keys.add(e.key)
                if e.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE):
                    self.used_keyboard = True
                if e.key in (pygame.K_ESCAPE, getattr(pygame, 'K_AC_BACK', -999)):
                    self.on_back()
                elif self.scene == 'race':
                    if e.key == pygame.K_r and self.race:
                        self.race.respawn_local()
                    elif e.key == pygame.K_m:
                        self.sfx.enabled = not self.sfx.enabled
                        self.toast(T('소리 켬', 'Sound on') if self.sfx.enabled else T('소리 끔', 'Sound off'), 0.8)
                        if not self.sfx.enabled:
                            self.sfx.silence()
            elif e.type == pygame.KEYUP:
                self.keys.discard(e.key)
            elif e.type == getattr(pygame, 'VIDEORESIZE', -1):
                pass
            else:
                self.ptr.handle(e, self.W, self.H)
        if self.screen.get_size() != (self.W, self.H):
            self.on_resize()

    def on_back(self):
        if self.kb is not None:
            self.close_kb('cancel')
        elif self.scene == 'race':
            self.toggle_pause()
        elif self.scene == 'results':
            self.leave_race()
        elif self.scene in ('solo', 'garage', 'settings', 'multi'):
            self.profile.save()
            self.go('menu')
        elif self.scene == 'lobby':
            self.session.leave()
            self.go('menu')
        elif self.scene == 'menu':
            self.running = False

    def open_kb(self, title, text, mode, maxlen, cb):
        self.kb = OnScreenKeyboard(title, text, mode, maxlen, cb)

    def close_kb(self, result):
        kb = self.kb
        self.kb = None
        if result == 'ok' and kb is not None:
            kb.on_ok(kb.text)

    def read_input(self, dt):
        k = self.keys
        pressed = self.touch.read(self.ptr.down())
        left = pygame.K_LEFT in k or pygame.K_a in k or 'left' in pressed
        right = pygame.K_RIGHT in k or pygame.K_d in k or 'right' in pressed
        tgt = (1.0 if right else 0.0) - (1.0 if left else 0.0)
        brake = pygame.K_DOWN in k or pygame.K_s in k or 'brake' in pressed
        gas = pygame.K_UP in k or pygame.K_w in k or 'gas' in pressed
        auto = self.profile['auto_gas'] and not self.used_keyboard
        drift = pygame.K_SPACE in k or pygame.K_LSHIFT in k or pygame.K_RSHIFT in k or 'drift' in pressed
        rate = 7.0 if tgt == 0 else 5.5
        self.steer += (tgt - self.steer) * min(1.0, dt * rate)
        return {'steer': self.steer, 'throttle': 1.0 if (gas or (auto and not brake)) else 0.0, 'brake': 1.0 if brake else 0.0, 'drift': drift}, pressed

    # ------------------------------------------------------------------ 레이스
    def start_solo(self):
        p = self.profile
        entries = solo_entries(p.display_name(), p['kart'], int(p['bots']))
        self.start_race(int(p['map']), int(p['laps']), entries, False, True, 5.0)

    def start_race(self, map_id, laps, entries, multi, is_host, countdown):
        self.loading(T('맵 생성 중…', 'Building map…') + ' #%d' % map_id)
        self.race = Race(map_id, laps, entries, multi=multi, is_host=is_host, countdown=countdown, net=self.session.net if multi else None)
        self.renderer.set_track(self.race.track)
        self.show_map = None
        self.cam.reset()
        self.mini = None
        self.toasts = []
        self.paused = False
        self.finish_at = None
        self.touch.layout(self.W, self.H, self.profile['auto_gas'])
        self.sfx.silence()
        self.steer = 0.0
        self.dirn = 1
        self.scene = 'race'

    def toggle_pause(self):
        if self.race is None:
            return
        if self.race.multi:
            self.paused = not self.paused          # 멀티: 메뉴만 열리고 레이스는 계속
            return
        self.paused = not self.paused
        if self.paused:
            self.sfx.silence()

    def leave_race(self):
        multi = self.race is not None and self.race.multi
        self.race = None
        self.paused = False
        self.sfx.silence()
        self.show_map = None
        if multi:
            self.session.leave()
        self.go('menu')

    def handle_race_events(self, race):
        for ev in race.events:
            kind = ev[0]
            if kind == 'count':
                if ev[1] <= 3:
                    self.sfx.play('count')
            elif kind == 'go':
                self.sfx.play('go')
                self.toast('GO!', 1.0, (255, 255, 255), True)
            elif kind == 'lap':
                self.toast('FINAL LAP!' if ev[2] else 'LAP %d' % ev[1], 1.6, (255, 220, 90), True)
                self.sfx.play('lap')
            elif kind == 'finish':
                self.toast('FINISH!', 3.0, (255, 255, 255), True)
                self.sfx.play('finish')
                self.finish_at = time.time()
            elif kind == 'fin':
                self.toast(T('%s 결승!' % ev[1], '%s finished!' % ev[1]), 1.4, (200, 230, 255))
            elif kind == 'left':
                self.toast(T('%s 퇴장' % ev[1], '%s left' % ev[1]), 1.4, (255, 150, 150))
            elif kind == 'sim':
                e = ev[1]
                if e in ('pad', 'miniturbo'):
                    self.sfx.play('boost')
                    if e == 'pad':
                        self.toast('BOOST!', 0.7, (80, 230, 255))
                elif e in ('wall', 'bump'):
                    self.sfx.play('bump')
                    self.renderer.shake = max(self.renderer.shake, 0.6)
                elif e.startswith('tier'):
                    self.sfx.play('tier')

    def emit_fx(self, race, dt):
        rd = self.renderer
        th = race.track.theme
        gc = hex_rgb(th['ground'][0])
        loc = race.local
        for rc in race.racers:
            if rc.speed < 4:
                continue
            if abs(rc.x - loc.x) + abs(rc.z - loc.z) > 90:
                continue
            m = rd.model(rc.kart_id)
            fx, fz = math.sin(rc.h), math.cos(rc.h)
            rx, rz = -fz, fx
            L, W = m.L, m.W
            if rc.drifting:
                col = [(170, 200, 255), (60, 170, 255), (255, 160, 40), (210, 80, 255)][min(3, rc.tier)]
                for s_ in (-1, 1):
                    if _random.random() < 0.75:
                        rd.emit(rc.x - fx * L * 0.4 + rx * s_ * W * 0.5, rc.y + 0.25, rc.z - fz * L * 0.4 + rz * s_ * W * 0.5,
                                (_random.random() - 0.5) * 5 - fx * 3, 2 + _random.random() * 4, (_random.random() - 0.5) * 5 - fz * 3, col, 0.18, 0.35 + _random.random() * 0.25)
            if rc.boosting and _random.random() < 0.9:
                rd.emit(rc.x - fx * (L * 0.5 + 0.6), rc.y + 0.6, rc.z - fz * (L * 0.5 + 0.6), -fx * 9 + (_random.random() - 0.5) * 2, _random.random() * 2,
                        -fz * 9 + (_random.random() - 0.5) * 2, (255, 150, 40), 0.3, 0.3)
            if rc.offroad and _random.random() < 0.5:
                rd.emit(rc.x - fx * 1.2 + (_random.random() - 0.5) * 2, rc.y + 0.2, rc.z - fz * 1.2 + (_random.random() - 0.5) * 2,
                        (_random.random() - 0.5) * 3, 1 + _random.random() * 2, (_random.random() - 0.5) * 3, shade_rgb(gc, 1.2), 0.4, 0.5)
            if rc.wall_hit > 0.6:
                side = 1.0 if rc.idx is not None and race.track.rx[rc.idx % race.track.N] * rx + race.track.rz[rc.idx % race.track.N] * rz > 0 else -1.0
                for _ in range(2):
                    rd.emit(rc.x + rx * side * 1.3, rc.y + 0.6, rc.z + rz * side * 1.3, (_random.random() - 0.5) * 8, 2 + _random.random() * 5,
                            (_random.random() - 0.5) * 8, (255, 215, 90), 0.15, 0.4)

    def update_race(self, dt):
        race = self.race
        inp, pressed = self.read_input(dt)
        self.pressed = pressed
        if race.multi:
            for m in self.session.pump():
                if m.get('t') == 'tolobby':
                    self.race = None
                    self.show_map = None
                    self.go('lobby')
                    return
                race.handle_message(m)
            if self.session.state == 'idle':          # 서버 연결 끊김
                err = self.session.error
                self.race = None
                self.go('menu')
                self.err = err
                return
        if not self.paused or race.multi:
            race.update(dt, inp)
            self.handle_race_events(race)
            self.emit_fx(race, dt)
        loc = race.local
        sim = loc.sim
        self.renderer.update_particles(dt if not self.paused else 0.0)
        cp = self.cam.update(dt, loc, sim.stats['max_speed'])
        self.renderer.shake = max(0.0, self.renderer.shake - dt * 2.2)
        sh = self.renderer.shake * 0.25 + (0.05 if loc.boosting else 0.0)
        if sh > 0.01:
            cp = (cp[0] + (_random.random() - 0.5) * sh, cp[1] + (_random.random() - 0.5) * sh, cp[2] + (_random.random() - 0.5) * sh, cp[3], cp[4])
        tr = race.track
        i0 = loc.idx
        dot = math.sin(cp[3]) * tr.tx[i0] + math.cos(cp[3]) * tr.tz[i0]
        if dot < -0.35:
            self.dirn = -1
        elif dot > 0.35:
            self.dirn = 1
        ratio = loc.speed / sim.stats['max_speed']
        surf = self.renderer.render(race, cp, i0, self.dirn, 1.0 if loc.boosting else 0.0, ratio, self.t)
        self.present(surf)
        self.draw_labels()
        if not self.paused:
            self.sfx.engine(clamp(ratio, 0, 1.3), 1.0 if inp['throttle'] > 0 else 0.2, loc.boosting, loc.drifting, loc.offroad)
        # 성능 자동 조절
        self.fps_ema += (1.0 / max(dt, 1e-3) - self.fps_ema) * 0.05
        if self.fps_ema < 24 and self.renderer.q > 0 and race.phase == 'run':
            self.slow_t += dt
            if self.slow_t > 3.0:
                self.slow_t = 0.0
                self.set_quality(self.renderer.q - 1)
                self.toast(T('프레임 향상을 위해 그래픽 품질을 낮췄어요', 'Lowered graphics for smoother play'), 2.5, (255, 255, 255))
        else:
            self.slow_t = 0.0

    def draw_labels(self):
        rd = self.renderer
        sx = self.W / float(rd.rw)
        sy = self.H / float(rd.rh)
        for (x, y, text, color, dp) in rd.labels:
            size = clamp(260.0 / dp, 11, 26) * self.ui.u
            self.ui.text(self.screen, text, int(x * sx), int(y * sy), size, color, 'c')

    def draw_race_ui(self, dt):
        race = self.race
        ui = self.ui
        u = ui.u
        draw_hud(self, self.screen, race, dt)
        self.touch.draw(self.screen, ui, self.pressed)
        pb = R(self.W // 2 - 22 * u, 8 * u, 44 * u, 40 * u)
        if ui.button(self.screen, pb, 'II', 'ghost', size=22 * u):
            self.toggle_pause()
        if self.paused:
            self.draw_pause()
        elif race.local_finished() and self.finish_at and time.time() - self.finish_at > 2.4:
            self.scene = 'results'
        if self.show_fps:
            ui.text(self.screen, '%d fps  q%d  %dx%d' % (self.fps_ema, self.renderer.q, self.renderer.rw, self.renderer.rh), 8, self.H - 22 * u, 16 * u, (255, 255, 0))

    def draw_pause(self):
        ui = self.ui
        u = ui.u
        surf = self.screen
        veil = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 150))
        surf.blit(veil, (0, 0))
        pw, ph = int(min(self.W * 0.8, 460 * u)), int(300 * u)
        r = R((self.W - pw) // 2, (self.H - ph) // 2, pw, ph)
        ui.panel(surf, r, 235)
        ui.text(surf, T('일시정지', 'Paused'), r.centerx, r.y + 16 * u, 36 * u, (255, 255, 255), 'c')
        bh = 58 * u
        if ui.button(surf, R(r.x + 24 * u, r.y + 74 * u, r.w - 48 * u, bh), T('계속하기', 'Resume'), 'primary'):
            self.toggle_pause()
        if not self.race.multi:
            if ui.button(surf, R(r.x + 24 * u, r.y + 74 * u + (bh + 12 * u), r.w - 48 * u, bh), T('다시 시작', 'Restart'), 'normal'):
                self.paused = False
                self.start_solo()
                return
        if ui.button(surf, R(r.x + 24 * u, r.y + 74 * u + 2 * (bh + 12 * u), r.w - 48 * u, bh), T('나가기', 'Quit'), 'danger'):
            self.leave_race()

    def draw_results(self, dt):
        ui = self.ui
        u = ui.u
        surf = self.screen
        race = self.race
        veil = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 140))
        surf.blit(veil, (0, 0))
        pw = int(min(self.W * 0.92, 680 * u))
        ph = int(min(self.H * 0.94, 520 * u))
        r = R((self.W - pw) // 2, (self.H - ph) // 2, pw, ph)
        ui.panel(surf, r, 235)
        ui.text(surf, T('결과', 'Results'), r.centerx, r.y + 12 * u, 36 * u, (255, 215, 90), 'c')
        rank = race.ranking()
        rh = min(34 * u, (ph - 150 * u) / max(1, len(rank)))
        y = r.y + 62 * u
        for i, rc in enumerate(rank):
            row = R(r.x + 18 * u, y, r.w - 36 * u, rh - 3 * u)
            me = rc is race.local
            ui.panel(surf, row, 200 if me else 90, (255, 176, 32) if me else (255, 255, 255), 8)
            tc = (20, 20, 20) if me else (255, 255, 255)
            fs = rh * 0.62
            ui.text(surf, str(i + 1), row.x + 10 * u, row.y + rh * 0.08, fs, tc, shadow=False)
            ui.text(surf, '%s  (%s)' % (rc.name, kart_name(rc.kart_id, LANG)), row.x + 48 * u, row.y + rh * 0.08, fs, tc, shadow=False)
            ui.text(surf, fmt_time(rc.finish_time) if rc.finished else T('주행 중…', 'racing…'), row.right - 10 * u, row.y + rh * 0.08, fs, tc, 'r', shadow=False)
            y += rh
        by = r.bottom - 66 * u
        if ui.button(surf, R(r.x + 18 * u, by, r.w * 0.4, 52 * u), T('메뉴로', 'Menu'), 'ghost'):
            self.leave_race()
            return
        if race.multi:
            if self.session.is_host:
                if ui.button(surf, R(r.right - 18 * u - r.w * 0.5, by, r.w * 0.5, 52 * u), T('로비로 돌아가기', 'Back to lobby'), 'primary'):
                    self.session.back_to_lobby()
            else:
                ui.text(surf, T('방장을 기다리는 중…', 'Waiting for host…'), r.right - 18 * u, by + 12 * u, 22 * u, (190, 205, 240), 'r')
        else:
            if ui.button(surf, R(r.right - 18 * u - r.w * 0.5, by, r.w * 0.5, 52 * u), T('다시 달리기', 'Race again'), 'primary'):
                self.start_solo()

    # ------------------------------------------------------------------ 맵 선택기
    def outline(self, mid, w, h):
        key = (mid, w, h)
        hit = self.outline_cache.get(key)
        if hit is not None:
            return hit
        if len(self.outline_cache) > 24:
            self.outline_cache.clear()
        tr = Track(mid, True)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        b = tr.bounds
        span_x, span_z = max(b[1] - b[0], 1.0), max(b[3] - b[2], 1.0)
        sc = min((w - 24) / span_x, (h - 24) / span_z)
        ox = (w - span_x * sc) / 2
        oz = (h - span_z * sc) / 2
        pts = [(ox + (tr.px[i] - b[0]) * sc, oz + (tr.pz[i] - b[2]) * sc) for i in range(0, tr.N, 2)]
        wc = hex_rgb(tr.theme['wall'][0])
        pygame.draw.lines(s, (0, 0, 0, 200), True, pts, 9)
        pygame.draw.lines(s, wc, True, pts, 6)
        pygame.draw.lines(s, (40, 44, 58), True, pts, 3)
        pygame.draw.circle(s, (255, 255, 255), (int(pts[0][0]), int(pts[0][1])), 5)
        self.outline_cache[key] = (s, tr.length)
        return self.outline_cache[key]

    def map_picker(self, rect, mid, editable=True):
        ui = self.ui
        u = ui.u
        surf = self.screen
        ui.panel(surf, rect, 195)
        pad = int(12 * u)
        x, y, w = rect.x + pad, rect.y + pad, rect.w - 2 * pad
        name, theme = self.map_text(mid)
        ui.text(surf, '#%d / %d' % (mid, MAP_COUNT), x, y, 22 * u, (255, 200, 90))
        ui.text(surf, name, x, y + 24 * u, 30 * u)
        oh = int(rect.h * 0.34)
        out, length = self.outline(mid, int(w), oh)
        ui.text(surf, '%s · %.2f km' % (theme, length / 1000.0), x, y + 58 * u, 20 * u, (190, 205, 240))
        surf.blit(out, (x, y + 84 * u))
        ny = y + 88 * u + oh
        labels = ['-100', '-10', '-1', '+1', '+10', '+100', 'RND']
        deltas = [-100, -10, -1, 1, 10, 100, None]
        gap = 6 * u
        bw = (w - gap * 6) / 7.0
        bh = max(34 * u, min(48 * u, rect.h * 0.1))
        new = mid
        for i, (lab, d) in enumerate(zip(labels, deltas)):
            r = R(x + i * (bw + gap), ny, bw, bh)
            if ui.button(surf, r, lab, 'primary' if d is None else 'normal', size=bh * 0.4, enabled=editable):
                new = (1 + int(_random.random() * MAP_COUNT)) if d is None else ((mid - 1 + d) % MAP_COUNT) + 1
        cy_ = ny + bh + 8 * u
        ch = max(28 * u, min(40 * u, (rect.bottom - pad - cy_ - 6 * u) / 2.0))
        ti = map_info(mid)['theme']
        cw = (w - gap * 4) / 5.0
        for i, th in enumerate(THEMES):
            r = R(x + (i % 5) * (cw + gap), cy_ + (i // 5) * (ch + 6 * u), cw, ch)
            if ui.button(surf, r, th['name'] if LANG == 'ko' else th['en'], 'chipon' if i == ti else 'chip', size=ch * 0.44, enabled=editable):
                new = ((mid - 1) // 10) * 10 + i + 1
        return new

    # ------------------------------------------------------------------ 메뉴
    def scene_menu(self, dt):
        ui = self.ui
        u = ui.u
        surf = self.screen
        land = self.landscape
        self.draw_show(dt, self.profile['kart'], shift=0.34 if land else 0.0, dist=6.6)
        x = int(self.W * 0.06) if land else self.W // 2
        anc = 'l' if land else 'c'
        ui.text(surf, 'TURBO', x, int(self.H * 0.05), 96 * u, (255, 255, 255), anc)
        ui.text(surf, 'KART 3D', x, int(self.H * 0.05) + 86 * u, 70 * u, (255, 176, 32), anc)
        ui.text(surf, T('맵 1000개 · 카트 100,000종 · WiFi 멀티', '1000 maps · 100,000 karts · WiFi multiplayer'), x, int(self.H * 0.05) + 160 * u, 20 * u, (205, 220, 250), anc)
        bw = self.W * 0.40 if land else self.W * 0.82
        bx = int(self.W * 0.06) if land else (self.W - bw) / 2
        by = self.H * 0.43 if land else self.H * 0.40
        bh = min(self.H * 0.095, 60 * u)
        gap = bh * 0.2
        items = [(T('솔로 레이스', 'Solo race'), 'solo', 'primary'), (T('WiFi 멀티플레이', 'WiFi multiplayer'), 'multi', 'primary'),
                 (T('차고 (카트 꾸미기)', 'Garage (customize)'), 'garage', 'normal'), (T('설정', 'Settings'), 'settings', 'normal')]
        for i, (lab, tgt, kind) in enumerate(items):
            if ui.button(surf, R(bx, by + i * (bh + gap), bw, bh), lab, kind):
                self.go(tgt)
                return
        ui.text(surf, '%s #%d' % (kart_name(self.profile['kart'], LANG), self.profile['kart'] + 1), 14 * u, self.H - 30 * u, 18 * u, (200, 215, 245))
        if self.err:
            ui.text(surf, self.err, self.W // 2, self.H - 60 * u, 22 * u, (255, 120, 120), 'c')
        if ui.button(surf, R(self.W - 120 * u, self.H - 56 * u, 106 * u, 44 * u), T('종료', 'Quit'), 'ghost', size=20 * u):
            self.running = False

    # ------------------------------------------------------------------ 솔로
    def scene_solo(self, dt):
        ui = self.ui
        u = ui.u
        surf = self.screen
        self.draw_show(dt, self.profile['kart'], shift=0.0)
        land = self.landscape
        m = int(14 * u)
        if land:
            pr = R(m, m, self.W * 0.58 - m, self.H - 2 * m)
            rr = R(self.W * 0.58 + m / 2, m, self.W * 0.42 - m * 1.5, self.H - 2 * m)
        else:
            pr = R(m, m, self.W - 2 * m, self.H * 0.58)
            rr = R(m, self.H * 0.58 + 2 * m, self.W - 2 * m, self.H * 0.42 - 3 * m)
        self.sel_map = self.map_picker(pr, self.sel_map)
        ui.panel(surf, rr, 195)
        x, y, w = rr.x + 14 * u, rr.y + 14 * u, rr.w - 28 * u
        ui.text(surf, T('레이스 설정', 'Race settings'), x, y, 28 * u, (255, 255, 255))
        d = ui.stepper(surf, R(x, y + 52 * u, w, 44 * u), T('바퀴 수', 'Laps'), int(self.profile['laps']), 1, 10)
        if d:
            self.profile['laps'] = int(self.profile['laps']) + d
        d = ui.stepper(surf, R(x, y + 108 * u, w, 44 * u), T('AI 상대', 'AI rivals'), int(self.profile['bots']), 0, 11)
        if d:
            self.profile['bots'] = int(self.profile['bots']) + d
        ui.text(surf, '%s #%d' % (kart_name(self.profile['kart'], LANG), self.profile['kart'] + 1), x, y + 166 * u, 18 * u, (190, 205, 240))
        bh = min(70 * u, rr.h * 0.2)
        if ui.button(surf, R(x, rr.bottom - 14 * u - bh * 2 - 10 * u, w, bh), T('출발!', 'START!'), 'primary', size=bh * 0.5):
            self.profile['map'] = self.sel_map
            self.profile.save()
            self.start_solo()
            return
        if ui.button(surf, R(x, rr.bottom - 14 * u - bh, w, bh * 0.8), T('뒤로', 'Back'), 'ghost'):
            self.profile['map'] = self.sel_map
            self.profile.save()
            self.go('menu')

    # ------------------------------------------------------------------ 차고
    def scene_garage(self, dt):
        ui = self.ui
        u = ui.u
        surf = self.screen
        land = self.landscape
        self.draw_show(dt, self.profile['kart'], shift=0.42 if land else 0.0, dist=6.8)
        m = int(14 * u)
        if land:
            pr = R(m, m, min(self.W * 0.5, 480 * u), self.H - 2 * m)
        else:
            pr = R(m, self.H * 0.36, self.W - 2 * m, self.H * 0.62)
        ui.panel(surf, pr, 200)
        x, y, w = pr.x + 14 * u, pr.y + 12 * u, pr.w - 28 * u
        kk0 = clamp(pr.h / (560.0 * u), 0.72, 1.0)
        ui.text(surf, T('차고', 'Garage'), x, y, 32 * u * kk0)
        # 닉네임
        if ui.button(surf, R(x, y + 44 * u, w, 44 * u * kk0), (T('닉네임: ', 'Name: ') + self.profile.display_name()), 'normal', size=22 * u * kk0):
            def setname(t):
                self.profile['name'] = t.strip()
                self.profile.save()
                self.session.send_profile()
            self.open_kb(T('닉네임 (영문/숫자)', 'Nickname'), self.profile['name'], 'alpha', 14, setname)
        k = decode_kart(self.profile['kart'])
        rows = [('body', T('차체', 'Body'), BODIES[k['body']]['name' if LANG == 'ko' else 'en'], 20),
                ('paint', T('페인트', 'Paint'), PAINTS[k['paint']]['name' if LANG == 'ko' else 'en'], 20),
                ('wheel', T('휠', 'Wheels'), wheel_name(k['wheel'], LANG), 25),
                ('wing', T('윙/파츠', 'Wing'), WINGS[k['wing']]['name' if LANG == 'ko' else 'en'], 10)]
        kk = clamp(pr.h / (560.0 * u), 0.72, 1.0)
        ry = y + 100 * u * kk
        rh = 42 * u * kk
        for key, lab, val, mod in rows:
            ui.text(surf, lab, x, ry + 8 * u, 18 * u, (190, 205, 240))
            lb = R(x + 84 * u, ry, 44 * u, rh)
            rb = R(x + w - 44 * u, ry, 44 * u, rh)
            ui.text(surf, val, (lb.right + rb.x) // 2, ry + 8 * u, 20 * u, (255, 255, 255), 'c')
            d = 0
            if ui.button(surf, lb, '<', 'normal'):
                d = -1
            if ui.button(surf, rb, '>', 'normal'):
                d = 1
            if d:
                k[key] = (k[key] + d) % mod
                self.profile['kart'] = encode_kart(k)
                self.profile.save()
                self.session.send_profile()
                self.sfx.play('click', 0.5)
            ry += rh + 8 * u * kk
        # 번호/랜덤
        if ui.button(surf, R(x, ry, w * 0.62, 44 * u * kk), 'No. %d / %d' % (self.profile['kart'] + 1, KART_COUNT), 'normal', size=22 * u):
            def setnum(t):
                try:
                    n = int(float(t))
                    self.profile['kart'] = int(clamp(n, 1, KART_COUNT)) - 1
                    self.profile.save()
                    self.session.send_profile()
                except ValueError:
                    pass
            self.open_kb(T('카트 번호 (1~100000)', 'Kart number (1-100000)'), str(self.profile['kart'] + 1), 'ip', 6, setnum)
        if ui.button(surf, R(x + w * 0.65, ry, w * 0.35, 44 * u * kk), T('랜덤', 'Random'), 'primary', size=20 * u * kk):
            self.profile['kart'] = int(_random.random() * KART_COUNT)
            self.profile.save()
            self.session.send_profile()
        ry += 54 * u * kk
        st = kart_stats(self.profile['kart'])
        for lab, key in ((T('최고속도', 'Speed'), 'speed'), (T('가속', 'Accel'), 'accel'), (T('핸들링', 'Handling'), 'handling'), (T('드리프트', 'Drift'), 'drift')):
            ui.text(surf, lab, x, ry - 2 * u, 17 * u, (190, 205, 240))
            bx = x + 90 * u
            bw = w - 90 * u - 40 * u
            pygame.draw.rect(surf, (20, 24, 40), (bx, ry + 3 * u, bw, 12 * u), border_radius=6)
            pygame.draw.rect(surf, (255, 176, 32), (bx, ry + 3 * u, bw * st[key] / 10.0, 12 * u), border_radius=6)
            ui.text(surf, '%.1f' % st[key], bx + bw + 8 * u, ry - 3 * u, 17 * u, (255, 255, 255))
            ry += 24 * u * kk
        if ui.button(surf, R(x, pr.bottom - 52 * u * kk, w, 40 * u * kk), T('완료', 'Done'), 'primary', size=22 * u * kk):
            self.profile.save()
            self.go('menu')

    # ------------------------------------------------------------------ 설정
    def scene_settings(self, dt):
        global LANG
        ui = self.ui
        u = ui.u
        surf = self.screen
        self.draw_show(dt, self.profile['kart'], shift=0.0)
        pw = min(self.W - 28 * u, 620 * u)
        r = R((self.W - pw) / 2, 14 * u, pw, self.H - 28 * u)
        ui.panel(surf, r, 215)
        x, y, w = r.x + 18 * u, r.y + 14 * u, r.w - 36 * u
        ui.text(surf, T('설정', 'Settings'), x, y, 34 * u)
        y += 56 * u
        ui.text(surf, T('그래픽 품질', 'Graphics'), x, y, 22 * u, (210, 220, 245))
        y += 30 * u
        qn = [T('낮음', 'Low'), T('중간', 'Medium'), T('높음', 'High')]
        cw = (w - 20 * u) / 3.0
        for i in range(3):
            if ui.button(surf, R(x + i * (cw + 10 * u), y, cw, 46 * u), qn[i], 'chipon' if self.renderer.q == i else 'chip'):
                self.set_quality(i)
                self.show_map = None
        y += 62 * u
        for key, lab in (('auto_gas', T('자동 가속 (터치)', 'Auto gas (touch)')), ('sound', T('소리', 'Sound'))):
            on = bool(self.profile[key])
            if ui.button(surf, R(x, y, w, 46 * u), '%s :  %s' % (lab, 'ON' if on else 'OFF'), 'good' if on else 'normal'):
                self.profile[key] = not on
                if key == 'sound':
                    self.sfx.enabled = not on
                self.touch.layout(self.W, self.H, self.profile['auto_gas'])
                self.profile.save()
            y += 56 * u
        ui.text(surf, T('언어 / Language', 'Language'), x, y, 22 * u, (210, 220, 245))
        y += 30 * u
        for i, (code, lab) in enumerate((('auto', 'Auto'), ('ko', '한국어' if self.font_path else 'Korean'), ('en', 'English'))):
            cur = self.profile['lang']
            if ui.button(surf, R(x + i * (cw + 10 * u), y, cw, 46 * u), lab, 'chipon' if cur == code else 'chip'):
                self.profile['lang'] = code
                LANG = ('ko' if self.font_path else 'en') if code == 'auto' else code
                self.profile.save()
        y += 62 * u
        if ui.button(surf, R(x, y, w, 46 * u), 'FPS :  %s' % ('ON' if self.show_fps else 'OFF'), 'good' if self.show_fps else 'normal'):
            self.show_fps = not self.show_fps
        if ui.button(surf, R(x, r.bottom - 66 * u, w, 50 * u), T('완료', 'Done'), 'primary'):
            self.profile.save()
            self.go('menu')

    # ------------------------------------------------------------------ 멀티플레이
    def scan_rooms(self):
        if not self.scan.get('busy'):
            self.scan = {'busy': True, 'rooms': self.scan.get('rooms', []), 'done': False}
            discover_async(self.scan)

    def join_ip(self, text):
        t = text.strip()
        if not t:
            return
        port = int(self.profile['port'])
        if ':' in t:
            t, p = t.split(':', 1)
            try:
                port = int(p)
            except ValueError:
                pass
        self.profile['last_ip'] = t
        self.profile.save()
        self.session.join_game(t, port)
        self.scene = 'lobby'

    def scene_multi(self, dt):
        ui = self.ui
        u = ui.u
        surf = self.screen
        self.draw_show(dt, self.profile['kart'], shift=0.0)
        pw = min(self.W - 28 * u, 760 * u)
        r = R((self.W - pw) / 2, 14 * u, pw, self.H - 28 * u)
        ui.panel(surf, r, 215)
        x, y, w = r.x + 18 * u, r.y + 14 * u, r.w - 36 * u
        ui.text(surf, T('WiFi 멀티플레이', 'WiFi multiplayer'), x, y, 34 * u)
        y += 52 * u
        ips = local_ips()
        ui.text(surf, T('내 IP: ', 'My IP: ') + (', '.join(ips) if ips else T('(WiFi 연결 확인)', '(check WiFi)')), x, y, 19 * u, (190, 205, 240))
        y += 34 * u
        bh = 56 * u
        half = (w - 12 * u) / 2.0
        if ui.button(surf, R(x, y, half, bh), T('방 만들기 (호스트)', 'Host a game'), 'primary'):
            if self.session.host_game(int(self.profile['port'])):
                self.scene = 'lobby'
            else:
                self.err = self.session.error
        if ui.button(surf, R(x + half + 12 * u, y, half, bh), T('IP 직접 입력', 'Join by IP'), 'normal'):
            self.open_kb(T('호스트 IP (예: 192.168.0.5)', 'Host IP (e.g. 192.168.0.5)'), self.profile['last_ip'], 'ip', 21, self.join_ip)
        y += bh + 16 * u
        ui.text(surf, T('같은 WiFi 의 방', 'Rooms on this WiFi'), x, y, 22 * u, (255, 220, 120))
        if ui.button(surf, R(r.right - 18 * u - 150 * u, y - 6 * u, 150 * u, 40 * u), T('다시 검색', 'Rescan'), 'chip', size=18 * u, enabled=not self.scan.get('busy')):
            self.scan_rooms()
        y += 42 * u
        rooms = self.scan.get('rooms', [])
        if self.scan.get('busy') and not rooms:
            ui.text(surf, T('검색 중…', 'Searching…'), x, y, 20 * u, (190, 205, 240))
        elif not rooms:
            ui.text(surf, T('방을 찾지 못했어요. 친구가 [방 만들기] 후 IP 로 접속하세요.', 'No rooms found. Ask a friend to host, then use Join by IP.'), x, y, 18 * u, (190, 205, 240))
        for i, rm in enumerate(rooms[:5]):
            label = '%s  %s  ·  %d/%d  ·  #%s  ·  %s' % (rm.get('name', 'room'), rm['ip'], rm.get('players', 0), RoomServer.MAX_PLAYERS, rm.get('map', '?'), rm.get('state', ''))
            if ui.button(surf, R(x, y, w, 48 * u), label, 'normal', size=19 * u, enabled=rm.get('state') == 'lobby'):
                self.profile['last_ip'] = rm['ip']
                self.session.join_game(rm['ip'], rm.get('port', DEFAULT_PORT))
                self.scene = 'lobby'
            y += 54 * u
        if self.err:
            ui.text(surf, self.err, x, r.bottom - 112 * u, 20 * u, (255, 120, 120))
        if ui.button(surf, R(x, r.bottom - 60 * u, w, 46 * u), T('뒤로', 'Back'), 'ghost'):
            self.go('menu')

    # ------------------------------------------------------------------ 로비
    def scene_lobby(self, dt):
        ui = self.ui
        u = ui.u
        surf = self.screen
        ses = self.session
        self.draw_show(dt, self.profile['kart'], shift=0.0)
        # 서버에서 시작 신호가 오면 레이스 시작
        for m in ses.pump():
            pass
        if ses.start_msg is not None:
            msg = ses.start_msg
            ses.start_msg = None
            entries = ses.entries_from_start(msg)
            self.start_race(int(msg['map']), int(msg['laps']), entries, True, ses.is_host, float(msg.get('countdown', 5.0)))
            return
        if ses.state == 'idle':
            self.err = ses.error or T('연결이 끊어졌어요', 'Disconnected')
            self.go('multi')
            self.err = ses.error or T('연결 실패', 'Connection failed')
            return
        land = self.landscape
        m = int(14 * u)
        if ses.state == 'connecting':
            ui.text(surf, T('연결 중… ', 'Connecting… ') + ses.address, self.W // 2, self.H // 2 - 20 * u, 34 * u, (255, 255, 255), 'c')
            if ui.button(surf, R(self.W // 2 - 100 * u, self.H // 2 + 40 * u, 200 * u, 54 * u), T('취소', 'Cancel'), 'ghost'):
                ses.leave()
                self.go('multi')
            return
        if land:
            lr = R(m, m, self.W * 0.34, self.H - 2 * m)
            rr = R(self.W * 0.34 + 2 * m, m, self.W * 0.66 - 3 * m, self.H - 2 * m)
        else:
            lr = R(m, m, self.W - 2 * m, self.H * 0.3)
            rr = R(m, self.H * 0.3 + 2 * m, self.W - 2 * m, self.H * 0.7 - 3 * m)
        ui.panel(surf, lr, 205)
        x, y = lr.x + 14 * u, lr.y + 12 * u
        ui.text(surf, T('플레이어', 'Players') + ' %d/%d' % (len(ses.players), RoomServer.MAX_PLAYERS), x, y, 26 * u)
        y += 40 * u
        for p in ses.players[:8]:
            me = p['id'] == ses.my_id
            row = R(x, y, lr.w - 28 * u, 34 * u)
            ui.panel(surf, row, 200 if me else 110, (255, 176, 32) if me else (255, 255, 255), 8)
            tc = (20, 20, 20) if me else (255, 255, 255)
            ui.text(surf, ('* ' if p['id'] == ses.host_id else '') + p['name'], row.x + 8 * u, row.y + 4 * u, 20 * u, tc, shadow=False)
            y += 38 * u
        if ses.is_host:
            ips = local_ips()
            ui.text(surf, T('친구에게 알려주세요:', 'Tell your friends:'), x, lr.bottom - 120 * u, 16 * u, (190, 205, 240))
            ui.text(surf, (ips[0] if ips else '?') + ':%d' % self.profile['port'], x, lr.bottom - 96 * u, 24 * u, (255, 220, 120))
        if ui.button(surf, R(x, lr.bottom - 52 * u, lr.w - 28 * u, 42 * u), T('나가기', 'Leave'), 'danger', size=20 * u):
            ses.leave()
            self.go('menu')
            return
        # 오른쪽: 설정
        st = ses.settings
        mid = self.map_picker(R(rr.x, rr.y, rr.w, rr.h - 150 * u), int(st['map']), editable=ses.is_host)
        if ses.is_host and mid != st['map']:
            ses.send_settings(map=mid)
            self.profile['map'] = mid
        ui.panel(surf, R(rr.x, rr.bottom - 140 * u, rr.w, 140 * u), 205)
        sx, sy, sw_ = rr.x + 14 * u, rr.bottom - 134 * u, rr.w - 28 * u
        half = (sw_ - 12 * u) / 2.0
        d1 = ui.stepper(surf, R(sx, sy + 4 * u, half, 38 * u), T('바퀴', 'Laps'), int(st['laps']), 1, 10) if ses.is_host else 0
        d2 = ui.stepper(surf, R(sx + half + 12 * u, sy + 4 * u, half, 38 * u), T('봇', 'Bots'), int(st['bots']), 0, 11) if ses.is_host else 0
        if not ses.is_host:
            ui.text(surf, T('바퀴 %d · 봇 %d' % (st['laps'], st['bots']), 'Laps %d · Bots %d' % (st['laps'], st['bots'])), sx, sy + 8 * u, 22 * u, (230, 235, 255))
        if d1:
            ses.send_settings(laps=int(st['laps']) + d1)
        if d2:
            ses.send_settings(bots=int(st['bots']) + d2)
        if ses.is_host:
            if ui.button(surf, R(sx, sy + 56 * u, sw_, 64 * u), T('레이스 시작!', 'START RACE!'), 'primary', size=30 * u):
                ses.start_race()
        else:
            ui.text(surf, T('방장이 시작하기를 기다리는 중…', 'Waiting for the host to start…'), sx + sw_ / 2, sy + 70 * u, 22 * u, (190, 205, 240), 'c')

    # ------------------------------------------------------------------ 메인 루프
    def step(self, dt):
        """한 프레임: 이벤트 -> 장면 -> (키보드 오버레이) -> 화면 갱신"""
        self.t += dt
        self.pump_events()
        taps = self.ptr.take_taps()
        down = self.ptr.down()
        kb_active = self.kb is not None
        self.ui.begin([] if kb_active else taps, down, self.W, self.H)
        try:
            self.frame(dt)
        except Exception:
            import traceback
            traceback.print_exc()
            self.err = 'error'
            self.race = None
            self.scene = 'menu'
            self.show_map = None
        if self.kb is not None:
            self.ui.taps = taps if kb_active else []
            res = self.kb.draw(self.ui, self.screen, self.W, self.H, dt)
            if res:
                self.close_kb(res)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.step(min(self.clock.tick(60) / 1000.0, 0.1))
        try:
            self.profile.save()
            self.session.leave()
        except Exception:
            pass
        pygame.quit()

    def frame(self, dt):
        sc = self.scene
        if sc == 'race' and self.race is not None:
            self.update_race(dt)
            self.draw_race_ui(dt)
        elif sc == 'results' and self.race is not None:
            self.update_race(dt)
            self.draw_results(dt)
        elif sc == 'menu':
            self.scene_menu(dt)
        elif sc == 'solo':
            self.scene_solo(dt)
        elif sc == 'garage':
            self.scene_garage(dt)
        elif sc == 'settings':
            self.scene_settings(dt)
        elif sc == 'multi':
            self.scene_multi(dt)
        elif sc == 'lobby':
            self.scene_lobby(dt)
        else:
            self.scene = 'menu'



# ============================================================================
#  [폰] 진입점
# ============================================================================
def parse_args(argv):
    args = {}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == '--serve':
            args['serve'] = True
        elif a == '--fps':
            args['fps'] = True
        elif a == '--window' and i + 1 < len(argv):
            i += 1
            try:
                w, h = argv[i].lower().split('x')
                args['window'] = (int(w), int(h))
            except ValueError:
                pass
        elif a == '--lang' and i + 1 < len(argv):
            i += 1
            args['lang'] = argv[i]
        elif a == '--port' and i + 1 < len(argv):
            i += 1
            try:
                args['port'] = int(argv[i])
            except ValueError:
                pass
        i += 1
    return args


def main():
    try:
        args = parse_args(sys.argv)
        if args.get('serve'):
            serve_forever(args.get('port', DEFAULT_PORT))
            return
        app = App(args)
        app.run()
    except (SystemExit, KeyboardInterrupt):
        raise
    except BaseException:
        import traceback
        text = traceback.format_exc()
        print(text)
        path = _crash_log(text)
        print('=' * 64)
        print('오류가 발생했습니다. 위의 내용을 그대로 알려주세요.  /  An error occurred. Please send the text above.')
        if path:
            print('(같은 내용이 파일로도 저장되었습니다 / also saved to: %s)' % path)
        print('=' * 64)
        _wait_key()
        raise SystemExit(1)


if __name__ == '__main__':
    main()
