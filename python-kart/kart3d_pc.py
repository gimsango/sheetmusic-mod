#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
  TURBO KART 3D  -  컴퓨터 버전 (Python + Panda3D)       [ kart3d_pc.py ]
==========================================================================
  * 맵 1000개 / 카트 100,000종 / WiFi(LAN) 멀티플레이 / GPU 3D (조명·안개·그림자)
  * 파일 하나로 실행:     pip install panda3d       (한 번만)
                          python kart3d_pc.py
  * 폰(Pydroid 3) 버전과 같은 방에서 함께 달릴 수 있습니다.

  [조작]   ↑/W 가속   ↓/S 브레이크   ←→/AD 조향   Space/Shift 드리프트
           R 트랙 복귀   Esc 일시정지   M 소리   F11 전체화면
           게임패드: 왼쪽 스틱 + RT/LT + A(드리프트)
  [멀티]   한 명이 [멀티플레이 > 방 만들기], 나머지는 [방 찾기]/IP 입력
           전용 서버:  python kart3d_pc.py --serve
  [옵션]   --window 1280x720   --fullscreen   --lang en|ko   --port 5555
==========================================================================
"""
import os
import sys
import math
import time
import json
import array
import wave
import tempfile
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


def _ensure_pkg(pkg, alt_hint=''):
    """필요한 패키지가 없을 때: 올바른 설치 명령을 보여주고, 동의하면 같은 파이썬으로 설치한 뒤 게임을 다시 시작한다."""
    exe = sys.executable or 'python'
    is_android = _is_android()
    print('=' * 64)
    print('%s 패키지가 필요합니다  /  "%s" is required.' % (pkg, pkg))
    if is_android:
        print('Pydroid 3:  왼쪽 위 메뉴(=) > Pip > "%s" 검색 > INSTALL  (설치 후 다시 실행)' % pkg)
        if alt_hint:
            print(alt_hint)
        print('=' * 64)
        return
    print('이 게임을 실행하는 파이썬에 설치하는 명령 (그대로 복사해서 실행):')
    print()
    print('    "%s" -m pip install %s' % (exe, pkg))
    print()
    if alt_hint:
        print(alt_hint)
    try:
        ans = input('지금 자동으로 설치할까요? / Install now? (y/n) [y]: ').strip().lower()
    except Exception:
        ans = 'n'
    if ans in ('', 'y', 'yes', 'ㅛ', '네', '예', 'ㅇ'):
        rc = subprocess.call([exe, '-m', 'pip', 'install', pkg])
        if rc == 0:
            print('설치 완료! 게임을 다시 시작합니다...  /  Installed. Restarting...')
            raise SystemExit(subprocess.call([exe] + sys.argv))
        print()
        print('설치에 실패했습니다. 위의 오류 문구를 그대로 알려주세요.  /  Install failed. Please send the error text above.')
        print('(리눅스 "externally-managed-environment" 오류: python3 -m venv venv 로 가상환경을 만든 뒤 그 안에서 설치하세요)')
    print('=' * 64)
    _wait_key()

try:
    from panda3d.core import (loadPrcFileData, Filename, WindowProperties, NodePath, Geom, GeomNode, GeomTriangles, GeomPoints, GeomLines,
                              GeomVertexData, GeomVertexFormat, GeomVertexWriter, Texture, TransparencyAttrib, ColorBlendAttrib,
                              AmbientLight, DirectionalLight, Fog, Vec3, Vec4, Point3, CardMaker, TextNode, LineSegs, AntialiasAttrib,
                              ModifierButtons, ClockObject, InputDevice, DepthOffsetAttrib, OmniBoundingVolume)
    from direct.showbase.ShowBase import ShowBase
    from direct.gui.OnscreenText import OnscreenText
except ImportError:
    _ensure_pkg('panda3d', '(설치가 계속 안 되면: pip install pygame 후 kart3d_phone.py 를 PC 에서 실행해도 같은 게임입니다)')
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
#  [PC] 절차적 메시 / 텍스처 도우미  (코어 좌표 y-up  ->  Panda3D z-up : (x, y, z) -> (x, -z, y))
# ============================================================================
def PV(x, y, z):
    return (x, -z, y)


def rgbf(c, k=1.0, a=1.0):
    return (min(1.0, c[0] / 255.0 * k), min(1.0, c[1] / 255.0 * k), min(1.0, c[2] / 255.0 * k), a)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / l, v[1] / l, v[2] / l)


class Mesh(object):
    """정점색+법선(+UV) 메시를 모아서 한 번에 Geom 으로 만든다. 좌표는 모두 Panda(z-up)."""

    def __init__(self):
        self.v = []
        self.n = []
        self.c = []
        self.t = []
        self.idx = []

    def add(self, p, n, c, uv=(0.0, 0.0)):
        self.v.append(p)
        self.n.append(n)
        self.c.append(c)
        self.t.append(uv)
        return len(self.v) - 1

    def tri(self, a, b, c):
        self.idx.append((a, b, c))

    def quad(self, p0, p1, p2, p3, col, n=None, uv=None):
        """p0..p3 은 바깥에서 볼 때 반시계 방향"""
        if n is None:
            n = _norm(_cross((p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]), (p3[0] - p0[0], p3[1] - p0[1], p3[2] - p0[2])))
        u = uv or ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
        a = self.add(p0, n, col, u[0])
        b = self.add(p1, n, col, u[1])
        c = self.add(p2, n, col, u[2])
        d = self.add(p3, n, col, u[3])
        self.tri(a, b, c)
        self.tri(a, c, d)

    def box(self, c, h, col, taper=None, skip_bottom=False):
        cx, cy, cz = c
        hx, hy, hz = h
        tx, tz = taper if taper else (1.0, 1.0)
        # 앞(+y) 면만 테이퍼
        fx, fz = hx * tx, hz * tz
        P = lambda x, y, z: (cx + x, cy + y, cz + z)
        # +x
        self.quad(P(hx, -hy, -hz), P(fx, hy, -fz), P(fx, hy, fz), P(hx, -hy, hz), col)
        # -x
        self.quad(P(-fx, hy, -fz), P(-hx, -hy, -hz), P(-hx, -hy, hz), P(-fx, hy, fz), col)
        # +y (앞)
        self.quad(P(fx, hy, -fz), P(-fx, hy, -fz), P(-fx, hy, fz), P(fx, hy, fz), col)
        # -y (뒤)
        self.quad(P(-hx, -hy, -hz), P(hx, -hy, -hz), P(hx, -hy, hz), P(-hx, -hy, hz), col)
        # +z (위)
        self.quad(P(-hx, -hy, hz), P(hx, -hy, hz), P(fx, hy, fz), P(-fx, hy, fz), col)
        if not skip_bottom:
            self.quad(P(-fx, hy, -fz), P(fx, hy, -fz), P(hx, -hy, -hz), P(-hx, -hy, -hz), col)

    def frustum(self, c, r0, r1, length, col, axis='z', seg=10, caps=True, col_top=None):
        """축 방향 원기둥/원뿔대. axis 방향으로 -length/2 (반지름 r0) -> +length/2 (반지름 r1)"""
        cx, cy, cz = c
        h = length / 2.0
        ct = col_top or col

        def frame(a, b, w):
            # a,b = 원 평면 두 축 성분, w = 축 방향 성분  -> (x,y,z)
            if axis == 'z':
                return (cx + a, cy + b, cz + w)
            if axis == 'x':
                return (cx + w, cy + a, cz + b)
            return (cx + a, cy + w, cz + b)

        def vec(a, b, w):
            if axis == 'z':
                return (a, b, w)
            if axis == 'x':
                return (w, a, b)
            return (a, w, b)
        slope = (r0 - r1) / max(length, 1e-6)
        for i in range(seg):
            a0 = TAU * i / seg
            a1 = TAU * (i + 1) / seg
            ca0, sa0, ca1, sa1 = math.cos(a0), math.sin(a0), math.cos(a1), math.sin(a1)
            n0 = _norm(vec(ca0, sa0, slope))
            n1 = _norm(vec(ca1, sa1, slope))
            p0 = frame(ca0 * r0, sa0 * r0, -h)
            p1 = frame(ca1 * r0, sa1 * r0, -h)
            p2 = frame(ca1 * r1, sa1 * r1, h)
            p3 = frame(ca0 * r1, sa0 * r1, h)
            k0 = self.add(p0, n0, col)
            k1 = self.add(p1, n1, col)
            k2 = self.add(p2, n1, ct)
            k3 = self.add(p3, n0, ct)
            if axis == 'x':
                self.tri(k0, k2, k1)
                self.tri(k0, k3, k2)
            else:
                self.tri(k0, k1, k2)
                self.tri(k0, k2, k3)
        if caps:
            for sgn, rr, cc in ((-1, r0, col), (1, r1, ct)):
                if rr <= 1e-6:
                    continue
                nrm = vec(0, 0, sgn)
                ctr = self.add(frame(0, 0, sgn * h), nrm, cc)
                ring = [self.add(frame(math.cos(TAU * i / seg) * rr, math.sin(TAU * i / seg) * rr, sgn * h), nrm, cc) for i in range(seg)]
                for i in range(seg):
                    a, b = ring[i], ring[(i + 1) % seg]
                    if (sgn > 0) == (axis != 'x'):
                        self.tri(ctr, a, b)
                    else:
                        self.tri(ctr, b, a)

    def sphere(self, c, r, col, seg=10, rings=6, scale=(1.0, 1.0, 1.0)):
        cx, cy, cz = c
        sx, sy, sz = scale
        rows = []
        for j in range(rings + 1):
            phi = math.pi * j / rings
            row = []
            for i in range(seg):
                th = TAU * i / seg
                nx, ny, nz = math.sin(phi) * math.cos(th), math.sin(phi) * math.sin(th), math.cos(phi)
                row.append(self.add((cx + nx * r * sx, cy + ny * r * sy, cz + nz * r * sz), (nx, ny, nz), col))
            rows.append(row)
        for j in range(rings):
            for i in range(seg):
                a, b = rows[j][i], rows[j][(i + 1) % seg]
                c2, d = rows[j + 1][i], rows[j + 1][(i + 1) % seg]
                self.tri(a, c2, b)
                self.tri(b, c2, d)

    def octa(self, c, r, col, scale=(1.0, 1.0, 1.0)):
        cx, cy, cz = c
        sx, sy, sz = scale
        P = [(cx + r * sx, cy, cz), (cx - r * sx, cy, cz), (cx, cy + r * sy, cz), (cx, cy - r * sy, cz), (cx, cy, cz + r * sz), (cx, cy, cz - r * sz)]
        faces = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
        for a, b, d in faces:
            self.quad(P[a], P[b], P[d], P[d], col)

    def ring(self, c, r_in, r_out, col, axis='x', seg=14, width=0.02):
        """납작한 고리 (바퀴 림 등) - 두께 width"""
        self.frustum(c, r_out, r_out, width, col, axis, seg, False)
        self.frustum(c, r_in, r_in, width, col, axis, seg, False)

    def annulus(self, c, r_in, r_out, col, axis='x', seg=14):
        """평평한 고리(양면). axis 방향을 바라보는 면"""
        cx, cy, cz = c
        nrm = {'x': (1.0, 0.0, 0.0), 'y': (0.0, 1.0, 0.0), 'z': (0.0, 0.0, 1.0)}[axis]

        def pt(a, r):
            ca, sa = math.cos(a) * r, math.sin(a) * r
            if axis == 'x':
                return (cx, cy + ca, cz + sa)
            if axis == 'y':
                return (cx + ca, cy, cz + sa)
            return (cx + ca, cy + sa, cz)
        for i in range(seg):
            a0, a1 = TAU * i / seg, TAU * (i + 1) / seg
            p = [pt(a0, r_in), pt(a0, r_out), pt(a1, r_out), pt(a1, r_in)]
            self.quad(p[0], p[1], p[2], p[3], col, n=nrm)
            self.quad(p[3], p[2], p[1], p[0], col, n=(-nrm[0], -nrm[1], -nrm[2]))

    def disc(self, c, r, col, axis='x', seg=14):
        self.annulus(c, 0.0, r, col, axis, seg)

    def spoke(self, c, ang, r, width, col, axis='x'):
        """원판 면 위의 얇은 바(양면)"""
        cx, cy, cz = c
        ca, sa = math.cos(ang), math.sin(ang)
        pa, pb = -sa * width / 2, ca * width / 2

        def P(t, k):
            u, v = ca * t + pa * k, sa * t + pb * k
            return (cx, cy + u, cz + v) if axis == 'x' else (cx + u, cy, cz + v)
        nrm = (1.0, 0.0, 0.0) if axis == 'x' else (0.0, 1.0, 0.0)
        self.quad(P(0, -1), P(r, -1), P(r, 1), P(0, 1), col, n=nrm)
        self.quad(P(0, 1), P(r, 1), P(r, -1), P(0, -1), col, n=(-nrm[0], -nrm[1], -nrm[2]))

    def node(self, name, textured=False):
        fmt = GeomVertexFormat.getV3n3cpt2()
        vd = GeomVertexData(name, fmt, Geom.UHStatic)
        vd.setNumRows(len(self.v))
        vw = GeomVertexWriter(vd, 'vertex')
        nw = GeomVertexWriter(vd, 'normal')
        cw = GeomVertexWriter(vd, 'color')
        tw = GeomVertexWriter(vd, 'texcoord')
        for i in range(len(self.v)):
            p = self.v[i]
            vw.addData3(p[0], p[1], p[2])
            q = self.n[i]
            nw.addData3(q[0], q[1], q[2])
            c = self.c[i]
            cw.addData4(c[0], c[1], c[2], c[3])
            t = self.t[i]
            tw.addData2(t[0], t[1])
        prim = GeomTriangles(Geom.UHStatic)
        for a, b, c in self.idx:
            prim.addVertices(a, b, c)
        geom = Geom(vd)
        geom.addPrimitive(prim)
        gn = GeomNode(name)
        gn.addGeom(geom)
        return gn

    def attach(self, parent, name, textured=False):
        return parent.attachNewNode(self.node(name, textured))


# ---------------------------------------------------------------------------
#  텍스처 (코드로 생성)
# ---------------------------------------------------------------------------
def make_texture(name, w, h, data, fmt='RGB', repeat=True):
    t = Texture(name)
    t.setup2dTexture(w, h, Texture.T_unsigned_byte, Texture.F_rgba if fmt == 'RGBA' else Texture.F_rgb)
    t.setRamImageAs(bytes(data), fmt)
    if repeat:
        t.setWrapU(Texture.WM_repeat)
        t.setWrapV(Texture.WM_repeat)
    else:
        t.setWrapU(Texture.WM_clamp)
        t.setWrapV(Texture.WM_clamp)
    t.setMinfilter(Texture.FT_linear_mipmap_linear)
    t.setMagfilter(Texture.FT_linear)
    try:
        t.setAnisotropicDegree(4)
    except Exception:
        pass
    return t


def tex_asphalt(road_rgb, night, seed=1):
    w = h = 256
    rnd = Rng(seed)
    buf = bytearray(w * h * 3)
    for y in range(h):
        for x in range(w):
            n = (rnd() - 0.5) * 22
            r, g, b = road_rgb[0] + n, road_rgb[1] + n, road_rgb[2] + n
            u = x / float(w)
            v = y / float(h)
            line = None
            if u < 0.045 and u > 0.02 or u > 0.955 and u < 0.98:
                line = (240, 240, 240)
            elif 0.488 < u < 0.512 and v < 0.5:
                line = (120, 220, 255) if night else (245, 197, 24)
            if line:
                k = 0.88 + 0.12 * rnd()
                r, g, b = line[0] * k, line[1] * k, line[2] * k
            o = (y * w + x) * 3
            buf[o] = int(max(0, min(255, r)))
            buf[o + 1] = int(max(0, min(255, g)))
            buf[o + 2] = int(max(0, min(255, b)))
    return make_texture('asphalt', w, h, buf)


def tex_ground(c0, c1, seed=2):
    w = h = 128
    rnd = Rng(seed)
    low = [[rnd() for _ in range(8)] for _ in range(8)]
    buf = bytearray(w * h * 3)
    for y in range(h):
        fy = y / 16.0
        iy = int(fy) % 8
        iy1 = (iy + 1) % 8
        ty = fy - int(fy)
        for x in range(w):
            fx = x / 16.0
            ix = int(fx) % 8
            ix1 = (ix + 1) % 8
            tx = fx - int(fx)
            a = low[iy][ix] * (1 - tx) + low[iy][ix1] * tx
            b = low[iy1][ix] * (1 - tx) + low[iy1][ix1] * tx
            m = a * (1 - ty) + b * ty
            n = 1 + (rnd() - 0.5) * 0.12
            o = (y * w + x) * 3
            for k in range(3):
                buf[o + k] = int(max(0, min(255, (c0[k] + (c1[k] - c0[k]) * m) * n)))
    return make_texture('ground', w, h, buf)


def tex_glow(name='glow', size=64, soft=2.0):
    buf = bytearray(size * size * 4)
    c = (size - 1) / 2.0
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c) / c
            a = max(0.0, 1.0 - d) ** soft
            o = (y * size + x) * 4
            buf[o] = buf[o + 1] = buf[o + 2] = 255
            buf[o + 3] = int(a * 255)
    return make_texture(name, size, size, buf, 'RGBA', False)


def tex_pad():
    w, h = 64, 128
    buf = bytearray(w * h * 3)
    for y in range(h):
        for x in range(w):
            o = (y * w + x) * 3
            col = (8, 24, 60)
            for k in range(3):
                cy_ = 18 + k * 36
                # 위로 향한 화살표(셰브론)
                dy = (y - cy_)
                dx = abs(x - w / 2.0)
                if 0 <= dy - dx * 0.55 <= 11 and dx < 28:
                    col = (25, 230, 255) if k % 2 == 0 else (255, 225, 74)
            if x < 3 or x > w - 4 or y < 3 or y > h - 4:
                col = (25, 230, 255)
            buf[o], buf[o + 1], buf[o + 2] = col
    return make_texture('pad', w, h, buf, 'RGB', False)


# ============================================================================
#  [PC] 월드 생성: 하늘/조명/안개/트랙/연석/벽/갓길/장식물/패드/가로등/게이트
# ============================================================================
def mesh_tube(m, path, radius, col, seg=6):
    """3D 경로를 따라가는 튜브 (아치 등)"""
    rings = []
    n = len(path)
    for k in range(n):
        p = path[k]
        a = path[max(0, k - 1)]
        b = path[min(n - 1, k + 1)]
        t = _norm((b[0] - a[0], b[1] - a[1], b[2] - a[2]))
        ref = (0.0, 0.0, 1.0) if abs(t[2]) < 0.9 else (1.0, 0.0, 0.0)
        u = _norm(_cross(t, ref))
        v = _cross(t, u)
        ring = []
        for i in range(seg):
            ang = TAU * i / seg
            nx = u[0] * math.cos(ang) + v[0] * math.sin(ang)
            ny = u[1] * math.cos(ang) + v[1] * math.sin(ang)
            nz = u[2] * math.cos(ang) + v[2] * math.sin(ang)
            ring.append(m.add((p[0] + nx * radius, p[1] + ny * radius, p[2] + nz * radius), (nx, ny, nz), col))
        rings.append(ring)
    for k in range(n - 1):
        for i in range(seg):
            a, b = rings[k][i], rings[k][(i + 1) % seg]
            c, d = rings[k + 1][i], rings[k + 1][(i + 1) % seg]
            m.tri(a, b, c)
            m.tri(b, d, c)


def blade(m, base, tip, width, col, droop=0.0):
    """야자수 잎: 밑동 -> 끝 으로 뻗은 마름모 (양면)"""
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    l = math.hypot(dx, dy) or 1.0
    sx, sy = -dy / l * width, dx / l * width
    mid = (base[0] + dx * 0.45, base[1] + dy * 0.45, base[2] + (tip[2] - base[2]) * 0.3 + 0.25)
    pts = [(base[0], base[1], base[2]), (mid[0] + sx, mid[1] + sy, mid[2]), (tip[0], tip[1], tip[2]), (mid[0] - sx, mid[1] - sy, mid[2])]
    m.quad(pts[0], pts[1], pts[2], pts[3], col)
    m.quad(pts[3], pts[2], pts[1], pts[0], col)


class World(object):
    def __init__(self, app, track):
        self.app = app
        self.track = track
        self.th = track.theme
        self.night = bool(self.th.get('night'))
        self.root = app.render.attachNewNode('world')
        self.lights = []
        self.rnd = Rng(track.info['seed'] ^ 0xABCDEF)
        self._lighting()
        self._fog()
        self._sky()
        self._far_ground()
        self._road()
        self._kerbs()
        self._ground()
        self._walls()
        self._start()
        self._pads()
        self._props()
        if self.th.get('lamps'):
            self._lamps()
        if self.th.get('arches'):
            self._arches()

    # ---- 조명 / 안개 ---------------------------------------------------------------
    def _lighting(self):
        th = self.th
        hs = th['hemi']
        sky_c, gr_c = hex_rgb(hs[0]), hex_rgb(hs[1])
        mc = mix_rgb(sky_c, gr_c, 0.4)
        k = min(1.3, hs[2]) * (0.66 if not self.night else 1.25)
        amb = AmbientLight('amb')
        amb.setColor(Vec4(mc[0] / 255.0 * k, mc[1] / 255.0 * k, mc[2] / 255.0 * k, 1))
        sun = DirectionalLight('sun')
        sc = hex_rgb(th['sun'])
        si = th['sun_i'] * (0.34 if not self.night else 0.3)
        sun.setColor(Vec4(sc[0] / 255.0 * si, sc[1] / 255.0 * si, sc[2] / 255.0 * si, 1))
        sd = th['sun_dir']
        self.sun_dir = _norm(PV(*sd))
        a = self.root.attachNewNode(amb)
        s = self.root.attachNewNode(sun)
        s.lookAt(Point3(-self.sun_dir[0], -self.sun_dir[1], -self.sun_dir[2]))
        self.app.render.setLight(a)
        self.app.render.setLight(s)
        self.lights = [a, s]

    def _fog(self):
        th = self.th
        fc = hex_rgb(th['fog'])
        fog = Fog('fog')
        fog.setColor(fc[0] / 255.0, fc[1] / 255.0, fc[2] / 255.0)
        fog.setMode(Fog.MExponentialSquared)
        fog.setExpDensity(th['fog_d'])
        self.fog = fog
        self.app.render.setFog(fog)
        self.app.setBackgroundColor(fc[0] / 255.0, fc[1] / 255.0, fc[2] / 255.0)

    # ---- 하늘 ------------------------------------------------------------------------
    def _sky(self):
        th = self.th
        top, bot = hex_rgb(th['sky_top']), hex_rgb(th['sky_bot'])
        fog = hex_rgb(th['fog'])
        self.sky = self.root.attachNewNode('sky')
        m = Mesh()
        R = 3000.0
        seg, rings = 28, 16
        rows = []
        for j in range(rings + 1):
            phi = math.pi * j / rings            # 0 = 천정, pi = 천저
            row = []
            for i in range(seg):
                th_ = TAU * i / seg
                x, y, z = math.sin(phi) * math.cos(th_), math.sin(phi) * math.sin(th_), math.cos(phi)
                t = clamp(z * 1.6 + 0.12, 0.0, 1.0) ** 0.7
                c = mix_rgb(bot, top, t)
                row.append(m.add((x * R, y * R, z * R), (-x, -y, -z), rgbf(c)))
            rows.append(row)
        for j in range(rings):
            for i in range(seg):
                a, b = rows[j][i], rows[j][(i + 1) % seg]
                c, d = rows[j + 1][i], rows[j + 1][(i + 1) % seg]
                m.tri(a, b, c)
                m.tri(b, d, c)
        dome = m.attach(self.sky, 'dome')
        dome.setTwoSided(True)
        for np_ in (dome,):
            np_.setLightOff()
            np_.setFogOff()
            np_.setDepthWrite(False)
            np_.setDepthTest(False)
            np_.setBin('background', 0)
        # 태양/달
        glow = tex_glow('sunglow', 64, 1.5)
        cm = CardMaker('sun')
        cm.setFrame(-1, 1, -1, 1)
        sun = self.sky.attachNewNode(cm.generate())
        sun.setTexture(glow)
        sc = hex_rgb(th['sun'])
        sun.setColor(sc[0] / 255.0, sc[1] / 255.0, sc[2] / 255.0, 1)
        sun.setTransparency(TransparencyAttrib.MAlpha)
        sun.setBillboardPointEye()
        sun.setPos(self.sun_dir[0] * 2700, self.sun_dir[1] * 2700, self.sun_dir[2] * 2700)
        sun.setScale(260 if not self.night else 150)
        for n_ in (sun,):
            n_.setLightOff()
            n_.setFogOff()
            n_.setDepthWrite(False)
            n_.setBin('background', 2)
        core = self.sky.attachNewNode(cm.generate())
        core.setTexture(tex_glow('suncore', 32, 0.4))
        core.setColor(1, 1, 0.95, 1)
        core.setTransparency(TransparencyAttrib.MAlpha)
        core.setBillboardPointEye()
        core.setPos(self.sun_dir[0] * 2690, self.sun_dir[1] * 2690, self.sun_dir[2] * 2690)
        core.setScale(70 if not self.night else 60)
        core.setLightOff()
        core.setFogOff()
        core.setDepthWrite(False)
        core.setBin('background', 3)
        # 별
        if self.night:
            fmt = GeomVertexFormat.getV3cp()
            vd = GeomVertexData('stars', fmt, Geom.UHStatic)
            vw = GeomVertexWriter(vd, 'vertex')
            cw = GeomVertexWriter(vd, 'color')
            n = 1500
            for _ in range(n):
                u = self.rnd() * TAU
                v = math.acos(self.rnd() * 0.97 + 0.03)
                r = 2900.0
                vw.addData3(r * math.sin(v) * math.cos(u), r * math.sin(v) * math.sin(u), r * math.cos(v))
                b = 0.45 + self.rnd() * 0.55
                cw.addData4(b, b, min(1.0, b + 0.08), 1)
            prim = GeomPoints(Geom.UHStatic)
            prim.addNextVertices(n)
            geom = Geom(vd)
            geom.addPrimitive(prim)
            gn = GeomNode('starsgn')
            gn.addGeom(geom)
            st = self.sky.attachNewNode(gn)
            st.setRenderModeThickness(2.2)
            st.setLightOff()
            st.setFogOff()
            st.setDepthWrite(False)
            st.setBin('background', 1)
        # 구름
        nc = int(14 * th.get('clouds', 0))
        if nc:
            m = Mesh()
            for _ in range(nc):
                a = self.rnd() * TAU
                d = 1100 + self.rnd() * 1900
                z = 380 + self.rnd() * 420
                s = 70 + self.rnd() * 110
                for j in range(4):
                    m.sphere((math.cos(a) * d + (j - 1.5) * s * 0.9, math.sin(a) * d, z + (j % 2) * 8), s * 0.55, (1, 1, 1, 0.88) if th['key'] != 'candy' else (1, 0.94, 0.98, 0.88),
                             seg=8, rings=4, scale=(1.0, 0.7, 0.34))
            cl = m.attach(self.sky, 'clouds')
            cl.setTransparency(TransparencyAttrib.MAlpha)
            cl.setLightOff()
            cl.setFogOff()
            cl.setDepthWrite(False)
            cl.setBin('background', 4)
        self._horizon()

    def _horizon(self):
        """360도 먼 산/도시 실루엣 (안개색과 섞어 원근감)"""
        th = self.th
        key = th['key']
        fog = hex_rgb(th['fog'])
        skyb = hex_rgb(th['sky_bot'])
        rnd = Rng(self.track.info['seed'] ^ 0x77)
        m = Mesh()
        R = 2500.0

        def ridge(color, base, amp, harm=(1, 2, 3, 5, 8, 13), z0=-300.0, rad=R, snow=False):
            phs = [rnd() * TAU for _ in harm]
            segs = 200
            ang = [TAU * i / segs for i in range(segs + 1)]
            hs = []
            for a in ang:
                h = base
                for k, p in zip(harm, phs):
                    h += amp / (k ** 0.8) * math.sin(k * a + p)
                hs.append(max(10.0, h))
            low = []
            hi = []
            for i, a in enumerate(ang):
                ca, sa = math.cos(a) * rad, math.sin(a) * rad
                n = (-math.cos(a), -math.sin(a), 0.2)
                low.append(m.add((ca, sa, z0), n, rgbf(color, 0.82)))
                topc = rgbf(color, 1.12) if not snow else (0.96, 0.98, 1.0, 1.0)
                hi.append(m.add((ca, sa, hs[i]), n, topc))
            for i in range(segs):
                a, b, c, d = low[i], low[i + 1], hi[i + 1], hi[i]
                m.tri(a, b, c)
                m.tri(a, c, d)

        if key in ('forest', 'autumn'):
            c1 = (110, 140, 170) if key == 'forest' else (190, 150, 110)
            ridge(mix_rgb(c1, skyb, 0.5), 260, 150, rad=2600)
            c2 = (60, 110, 80) if key == 'forest' else (150, 95, 50)
            ridge(mix_rgb(c2, fog, 0.35), 150, 90, rad=2100)
        elif key == 'desert':
            ridge(mix_rgb((200, 160, 100), skyb, 0.5), 130, 70, (1, 2, 3, 4), rad=2500)
            for _ in range(3):
                a = rnd() * TAU
                b = 130 + rnd() * 90
                cx, cy = math.cos(a) * 2300, math.sin(a) * 2300
                m.frustum((cx, cy, b * 0.45), b, 0.0, b * 0.9, rgbf(mix_rgb((190, 150, 95), fog, 0.35)), 'z', 4, False)
            ridge(mix_rgb((214, 176, 110), fog, 0.2), 70, 45, (1, 2, 4, 6), rad=1900)
        elif key == 'snow':
            ridge((246, 250, 255), 330, 170, rad=2600, snow=True)
            ridge(mix_rgb((95, 125, 105), fog, 0.45), 120, 60, rad=2000)
        elif key == 'neon':
            for layer, (col, hmax, rad) in enumerate((((78, 40, 130), 520, 2500), ((30, 18, 66), 330, 2000))):
                n = 150
                for i in range(n):
                    a = TAU * i / n + rnd() * 0.02
                    w = 30 + rnd() * 55
                    h = 40 + rnd() * hmax
                    cx, cy = math.cos(a) * rad, math.sin(a) * rad
                    m.box((cx, cy, h / 2 - 50), (w / 2, w / 2, h / 2 + 25), rgbf(col))
                    if rnd() < 0.45:
                        gc = [(255, 43, 214), (25, 230, 255), (255, 225, 74)][int(rnd() * 3)]
                        m.box((cx, cy, h * (0.3 + 0.6 * rnd()) - 50), (w * 0.52, w * 0.52, 3), rgbf(gc, 1.6))
        elif key == 'volcano':
            ridge((46, 22, 18), 160, 90, rad=2400)
            for _ in range(2):
                a = rnd() * TAU
                b = 360 + rnd() * 180
                cx, cy = math.cos(a) * 2200, math.sin(a) * 2200
                m.frustum((cx, cy, b * 0.55), b, 40, b * 1.1, rgbf((52, 26, 20)), 'z', 9, False, rgbf((255, 120, 40), 1.5))
        elif key == 'tropic':
            ridge(mix_rgb((70, 150, 100), fog, 0.35), 60, 40, (1, 3, 5, 9), rad=2300)
            ridge(mix_rgb((235, 215, 160), fog, 0.2), 25, 15, (1, 3, 5), rad=1700)
        elif key == 'candy':
            ridge(mix_rgb((255, 190, 225), skyb, 0.35), 200, 120, rad=2500)
            ridge(mix_rgb((190, 240, 255), fog, 0.3), 110, 70, rad=2000)
        elif key == 'space':
            ridge((70, 70, 80), 150, 80, rad=2400)
            a = rnd() * TAU
            m.sphere((math.cos(a) * 2600, math.sin(a) * 2600, 900), 380, rgbf((58, 111, 208)), seg=18, rings=12)
            ridge((92, 92, 104), 80, 50, (1, 2, 4, 7), rad=1900)
        elif key == 'canyon':
            for layer, (col, hmax, rad) in enumerate((((150, 70, 50), 520, 2500), ((120, 52, 36), 330, 1900))):
                n = 40
                for i in range(n):
                    a = TAU * i / n + rnd() * 0.05
                    w = 120 + rnd() * 260
                    h = hmax * (0.35 + rnd() * 0.65)
                    cx, cy = math.cos(a) * rad, math.sin(a) * rad
                    cc = mix_rgb(col, fog, 0.3 - layer * 0.15)
                    m.box((cx, cy, h / 2 - 60), (w / 2, w / 3, h / 2 + 30), rgbf(cc))
        hz = m.attach(self.sky, 'horizon')
        hz.setTwoSided(True)
        hz.setLightOff()
        hz.setFogOff()

    def _far_ground(self):
        tr = self.track
        cm = CardMaker('far')
        cm.setFrame(-9000, 9000, -9000, 9000)
        far = self.root.attachNewNode(cm.generate())
        far.setP(-90)
        far.setZ(tr.min_y - 62)
        fc = hex_rgb(self.th['far'])
        far.setColor(fc[0] / 255.0, fc[1] / 255.0, fc[2] / 255.0, 1)
        far.setLightOff()

    # ---- 트랙 -------------------------------------------------------------------------
    def _up(self, k):
        n = self.track.surface_normal(k)
        return (n[0], -n[2], n[1])

    def _road(self):
        tr = self.track
        N, hw = tr.N, tr.hw
        m = Mesh()
        dist = 0.0
        for i in range(N + 1):
            k = i % N
            n = self._up(k)
            m.add(PV(*tr.edge_point(k, -hw)), n, (1, 1, 1, 1), (0.0, dist / 24.0))
            m.add(PV(*tr.edge_point(k, hw)), n, (1, 1, 1, 1), (1.0, dist / 24.0))
            dist += tr.ds
        for i in range(N):
            a = 2 * i
            m.tri(a, a + 1, a + 3)
            m.tri(a, a + 3, a + 2)
        np_ = m.attach(self.root, 'road')
        np_.setTexture(tex_asphalt(shade_rgb(hex_rgb(self.th['road']), 1.9 if self.night else 1.0), self.night, self.track.info['seed'] & 0xffff))
        np_.setTwoSided(True)
        self.road_np = np_

    def _kerbs(self):
        tr = self.track
        N, hw = tr.N, tr.hw
        m = Mesh()
        red, white = (0.85, 0.14, 0.16, 1.0), (0.94, 0.94, 0.94, 1.0)
        amb = 0.8 if self.night else 1.0
        for side in (-1, 1):
            for i in range(N):
                k0, k1 = i, (i + 1) % N
                col = red if (i // 2) & 1 else white
                col = (col[0] * amb, col[1] * amb, col[2] * amb, 1.0)
                p0 = PV(*tr.edge_point(k0, side * (hw - 0.1)))
                p1 = PV(*tr.edge_point(k0, side * (hw + 1.4)))
                p2 = PV(*tr.edge_point(k1, side * (hw + 1.4)))
                p3 = PV(*tr.edge_point(k1, side * (hw - 0.1)))
                lift = lambda p: (p[0], p[1], p[2] + 0.03)
                m.quad(lift(p0), lift(p1), lift(p2), lift(p3), col, n=self._up(k0))
        np_ = m.attach(self.root, 'kerbs')
        np_.setTwoSided(True)
        np_.setDepthOffset(1)

    def _ground(self):
        tr = self.track
        N, hw, SH = tr.N, tr.hw, tr.SH
        th = self.th
        g0, g1 = hex_rgb(th['ground'][0]), hex_rgb(th['ground'][1])
        amb = 1.9 if self.night else 1.0
        offs = [hw + 1.4, hw + SH, hw + SH + 40.0, hw + SH + 200.0]
        m = Mesh()
        dist = 0.0
        for i in range(N):
            k0, k1 = i, (i + 1) % N
            cA = rgbf(g0 if (i // 4) & 1 else g1, amb)
            for side in (-1, 1):
                for r in range(len(offs) - 1):
                    o0, o1 = offs[r], offs[r + 1]
                    a0 = PV(*tr.edge_point(k0, side * o0))
                    b0 = PV(*tr.edge_point(k0, side * o1))
                    b1 = PV(*tr.edge_point(k1, side * o1))
                    a1 = PV(*tr.edge_point(k1, side * o0))
                    uv = ((o0 / 12.0, dist / 12.0), (o1 / 12.0, dist / 12.0), (o1 / 12.0, (dist + tr.ds) / 12.0), (o0 / 12.0, (dist + tr.ds) / 12.0))
                    col = cA if r < 2 else (cA[0] * 0.8, cA[1] * 0.8, cA[2] * 0.8, 1.0)
                    m.quad(a0, b0, b1, a1, col, n=self._up(k0), uv=uv)
            dist += tr.ds
        np_ = m.attach(self.root, 'ground')
        np_.setTexture(tex_ground((255, 255, 255), (205, 205, 205), self.track.info['seed'] & 0xffff))
        np_.setTwoSided(True)

    def _walls(self):
        tr = self.track
        N, wo = tr.N, tr.wall_off
        th = self.th
        w0, w1 = hex_rgb(th['wall'][0]), hex_rgb(th['wall'][1])
        glow = bool(th.get('glow_wall'))
        m = Mesh()
        for side in (-1, 1):
            for i in range(N):
                k0, k1 = i, (i + 1) % N
                col = rgbf(w0 if (i // 2) & 1 else w1, 1.15 if glow else (0.8 if self.night else 1.0))
                b0 = PV(*tr.edge_point(k0, side * wo))
                b1 = PV(*tr.edge_point(k1, side * wo))
                t0 = (b0[0], b0[1], b0[2] + 1.3)
                t1 = (b1[0], b1[1], b1[2] + 1.3)
                nrm = (-tr.rx[k0] * side, tr.rz[k0] * side, 0.0)      # 도로 안쪽
                m.quad(b0, b1, t1, t0, col, n=nrm)
                # 윗면
                m.quad(t0, t1, (t1[0] - nrm[0] * 0.5, t1[1] - nrm[1] * 0.5, t1[2]), (t0[0] - nrm[0] * 0.5, t0[1] - nrm[1] * 0.5, t0[2]), rgbf((226, 226, 232), 1.0 if not self.night else 0.8), n=(0, 0, 1))
        np_ = m.attach(self.root, 'walls')
        np_.setTwoSided(True)
        if glow:
            np_.setLightOff()

    def _start(self):
        tr = self.track
        hw = tr.hw
        m = Mesh()
        cols = 8
        for r in range(2):
            for c in range(cols):
                f0, f1 = r * 0.5, (r + 1) * 0.5
                x, y, z, h = tr.pose_at(f0 - 0.0, 0)
                pts = []
                for (ff, cc) in ((f0, c), (f0, c + 1), (f1, c + 1), (f1, c)):
                    xx, yy, zz, _h = tr.pose_at(ff, -hw + 2 * hw * cc / cols)
                    pts.append(PV(xx, yy + 0.05, zz))
                col = (0.08, 0.08, 0.09, 1) if (r + c) % 2 else (0.96, 0.96, 0.96, 1)
                m.quad(pts[0], pts[1], pts[2], pts[3], col, n=self._up(0))
        np_ = m.attach(self.root, 'startline')
        np_.setTwoSided(True)
        np_.setDepthOffset(2)
        # 게이트
        gate = self.root.attachNewNode('gate')
        gm = Mesh()
        hwg = hw + 1.6
        for s in (-1, 1):
            gm.box((s * hwg, 0, 5), (0.7, 0.7, 5), (0.17, 0.18, 0.23, 1))
        gm.box((0, 0, 9.6), (hw + 2.2, 0.45, 1.2), (0.7, 0.14, 0.17, 1))
        gm.attach(gate, 'gatemesh')
        tn = TextNode('banner')
        tn.setText('START / FINISH')
        tn.setAlign(TextNode.ACenter)
        tn.setTextColor(1, 1, 1, 1)
        if self.app.font_en is not None:
            tn.setFont(self.app.font_en)
        t_np = gate.attachNewNode(tn)
        t_np.setPos(0, -0.5, 9.2)
        t_np.setScale(1.7)
        t_np.setLightOff()
        t2 = gate.attachNewNode(tn)
        t2.setPos(0, 0.5, 9.2)
        t2.setH(180)
        t2.setScale(1.7)
        t2.setLightOff()
        x, y, z, h = tr.pose_at(0.0, 0.0)
        gate.setPos(*PV(x, y, z))
        gate.setH(math.degrees(h) + 180)
        gate.setP(0)

    def _pads(self):
        tr = self.track
        tex = tex_pad()
        for p in tr.pads:
            idx, d = p['idx'], p['d']
            hl = p['half_len'] / tr.ds
            hwp = p['half_w']
            pts = []
            for (ff, uu) in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
                x, y, z, _h = tr.pose_at(idx + ff * hl, d + uu * hwp)
                pts.append(PV(x, y + 0.07, z))
            m = Mesh()
            m.quad(pts[0], pts[1], pts[2], pts[3], (1, 1, 1, 1), n=self._up(idx), uv=((0, 0), (1, 0), (1, 1), (0, 1)))
            np_ = m.attach(self.root, 'pad')
            np_.setTexture(tex)
            np_.setLightOff()
            np_.setTwoSided(True)
            np_.setDepthOffset(3)

    # ---- 장식물 -----------------------------------------------------------------------------
    def _proto(self, kind, var):
        th = self.th
        m = Mesh()
        glow = None
        rc = (hex_rgb(th['rock'][0]), hex_rgb(th['rock'][1]))
        if kind == 'pine':
            snowy = th.get('snowy')
            m.frustum((0, 0, 1.5), 0.5, 0.35, 3.0, rgbf((90, 59, 34)), 'z', 6)
            cols = [(31, 107, 53), (42, 125, 63), (53, 145, 74)] if not snowy else [(79, 127, 102), (109, 154, 132), (242, 247, 251)]
            for (z, r, ln), c in zip(((5.0, 3.4, 5.0), (7.6, 2.7, 4.6), (10.0, 1.9, 4.0)), cols):
                m.frustum((0, 0, z), r, 0.0, ln, rgbf(c), 'z', 7, True)
        elif kind == 'roundtree':
            cols = [(217, 84, 30), (232, 163, 23), (184, 58, 26), (240, 192, 48)] if th.get('autumn') else [(58, 140, 58), (74, 160, 74), (47, 127, 53), (90, 170, 80)]
            c = cols[var % 4]
            m.frustum((0, 0, 2.0), 0.65, 0.45, 4.0, rgbf((90, 59, 34)), 'z', 6)
            m.sphere((0, 0, 6.5), 3.4, rgbf(c), 9, 6, (1, 1, 0.9))
            m.sphere((1.6, 0.8, 5.3), 2.2, rgbf(c, 0.88), 8, 5)
        elif kind == 'bush':
            m.sphere((0, 0, 0.8), 1.6, rgbf((47, 127, 53)), 8, 5, (1.2, 1.1, 0.7))
            m.sphere((1.3, 0.5, 0.5), 1.1, rgbf((58, 140, 58)), 7, 4)
        elif kind == 'cactus':
            g = rgbf((59, 138, 74))
            m.frustum((0, 0, 3.0), 0.8, 0.7, 6.0, g, 'z', 8)
            m.frustum((0.9, 0, 2.4), 0.4, 0.4, 1.4, g, 'x', 6)
            m.frustum((1.7, 0, 3.5), 0.4, 0.4, 2.4, g, 'z', 6)
            m.frustum((-0.6, 0, 3.6), 0.4, 0.4, 1.2, g, 'x', 6)
            m.frustum((-1.3, 0, 4.4), 0.4, 0.4, 1.8, g, 'z', 6)
        elif kind == 'rock':
            m.sphere((0, 0, 0.9), 2.2, rgbf(rc[0]), 7, 4, (1.3, 1.1, 0.8))
            m.sphere((2.3, 0.7, 0.5), 1.3, rgbf(rc[1]), 6, 4, (1.0, 1.0, 0.8))
        elif kind == 'mesa':
            for (z, r0, r1, ln), c in zip(((6, 9, 7, 12), (15, 7, 6.2, 6), (20.5, 6.2, 5.4, 5), (23.6, 5.6, 5.6, 1.2)), ((176, 74, 40), (199, 101, 58), (168, 68, 36), (224, 160, 96))):
                m.frustum((0, 0, z), r0, r1, ln, rgbf(c), 'z', 7)
        elif kind == 'palm':
            m.frustum((0.3, 0, 4.2), 0.5, 0.28, 8.4, rgbf((138, 106, 64)), 'z', 6)
            for k in range(7):
                a = k * 0.898
                blade(m, (0.3, 0, 8.4), (0.3 + math.cos(a) * 4.6, math.sin(a) * 4.6, 6.7), 0.75, rgbf((47, 143, 58) if k % 2 else (58, 160, 70)))
            m.sphere((0.3, 0, 8.2), 0.45, rgbf((90, 59, 34)), 6, 4)
        elif kind == 'building':
            m.box((0, 0, 0.5), (0.5, 0.5, 0.5), rgbf((58, 56, 108)))
            g = Mesh()
            for z, c in ((0.9, (255, 43, 214)), (0.62, (25, 230, 255)), (0.34, (255, 225, 74)), (0.98, (255, 43, 214))):
                g.box((0, 0, z), (0.512, 0.512, 0.008), rgbf(c, 1.6))
            glow = g
        elif kind == 'crystal':
            col = (255, 122, 26) if th.get('lava') else ((25, 230, 255) if th['key'] == 'space' else (255, 43, 214))
            g = Mesh()
            g.octa((0, 0, 3.0), 1.2, rgbf(col, 1.5), (1, 1, 2.6))
            g.octa((1.6, 0.4, 1.8), 0.8, rgbf(col, 1.2), (1, 1, 2.2))
            glow = g
        elif kind == 'lollipop':
            hue = [(255, 90, 140), (90, 200, 255), (255, 200, 60), (160, 110, 255), (110, 230, 150), (255, 140, 60)][var % 6]
            m.frustum((0, 0, 2.6), 0.16, 0.16, 5.2, rgbf((245, 245, 245)), 'z', 6)
            m.frustum((0, 0, 6.2), 2.2, 2.2, 0.6, rgbf((255, 255, 255)), 'y', 14)
            m.frustum((0, -0.31, 6.2), 1.2, 1.2, 0.05, rgbf(hue), 'y', 14)
            m.frustum((0, 0.31, 6.2), 1.2, 1.2, 0.05, rgbf(hue), 'y', 14)
        elif kind == 'icecream':
            sc = [(255, 158, 196), (255, 235, 160), (150, 220, 255)][var % 3]
            m.frustum((0, 0, 1.8), 0.0, 1.4, 3.6, rgbf((224, 169, 106)), 'z', 8)
            m.sphere((0, 0, 4.3), 1.7, rgbf(sc), 9, 6)
            m.sphere((0, 0, 6.1), 0.4, rgbf((221, 34, 51)), 6, 4)
        return m, glow

    def _props(self):
        tr = self.track
        protos = {}
        chunks = {}
        rnd = Rng(tr.info['seed'] ^ 0x5151)
        VAR = {'roundtree': 4, 'lollipop': 6, 'icecream': 3}
        holder = NodePath('protos')
        for p in tr.props:
            kind = p['kind']
            if kind == 'roundtree':
                var = int(p['r1'] * 4)
            elif kind == 'lollipop':
                var = int(p['r1'] * 6)
            elif kind == 'icecream':
                var = int(p['r1'] * 3)
            else:
                var = 0
            key = (kind, var)
            pr = protos.get(key)
            if pr is None:
                m, glow = self._proto(kind, var)
                lit = m.attach(holder, 'p_%s_%d' % key)
                lit.setTwoSided(True)
                parts = [lit]
                if glow is not None:
                    g = glow.attach(holder, 'g_%s_%d' % key)
                    g.setLightOff()
                    parts.append(g)
                pr = protos[key] = parts
            ck = p['seg'] // 36
            chunk = chunks.get(ck)
            if chunk is None:
                chunk = chunks[ck] = self.root.attachNewNode('chunk%d' % ck)
            pos = PV(p['x'], p['y'], p['z'])
            s = p['s']
            if kind == 'building':
                sc = (14 + p['r1'] * 22, 14 + p['r2'] * 22, 30 + p['r3'] * p['r3'] * 150)
            elif kind == 'mesa':
                q = 1.2 + p['r1'] * 1.8
                sc = (q, q, 0.8 + p['r2'] * 1.6)
            elif kind == 'rock':
                sc = (s * 1.4, s * 1.4, s * (1.0 + p['r1'] * 0.8))
            else:
                sc = (s, s, s)
            shade = 0.82 + p['r1'] * 0.3 if kind not in ('lollipop', 'icecream', 'building', 'crystal') else 1.0
            for part in pr:
                inst = part.copyTo(chunk)
                inst.setPos(*pos)
                inst.setH(math.degrees(p['rot']))
                inst.setScale(*sc)
                if shade != 1.0:
                    inst.setColorScale(shade, shade, shade, 1)
        for chunk in chunks.values():
            chunk.flattenStrong()
        holder.removeNode()

    def _lamps(self):
        tr = self.track
        m = Mesh()
        g = Mesh()
        for (i, side) in tr.lamps:
            off = tr.wall_off + 1.2
            x, y, z = tr.edge_point(i, off * side)
            base = PV(x, y - 0.1, z)
            m.frustum((base[0], base[1], base[2] + 5.5), 0.22, 0.16, 11.0, rgbf((48, 52, 63)), 'z', 6)
            inward = (tr.rx[i] * -side * 1.6, -tr.rz[i] * -side * 1.6)
            m.box((base[0] + inward[0] * 0.5, base[1] + inward[1] * 0.5, base[2] + 11.0), (0.14 + abs(inward[0]) * 0.5, 0.14 + abs(inward[1]) * 0.5, 0.12), rgbf((48, 52, 63)))
            g.box((base[0] + inward[0], base[1] + inward[1], base[2] + 10.8), (0.5, 0.5, 0.1), (3.0, 2.8, 2.2, 1))
        m.attach(self.root, 'lamps')
        gn = g.attach(self.root, 'lamplights')
        gn.setLightOff()

    def _arches(self):
        tr = self.track
        col = rgbf(hex_rgb(self.th['arches']), 2.0)
        m = Mesh()
        for ai in tr.arches:
            pts = []
            for k in range(0, 25):
                a = math.pi * k / 24.0
                x, y, z = tr.edge_point(ai, -(tr.hw + 1.5) * math.cos(a))
                pts.append(PV(x, y + math.sin(a) * tr.hw * 0.8 + 0.2, z))
            mesh_tube(m, pts, 0.4, col, 6)
        n = m.attach(self.root, 'arches')
        n.setLightOff()

    # ---- 갱신/정리 ---------------------------------------------------------------------------
    def update(self, cam_pos):
        self.sky.setPos(*cam_pos)

    def destroy(self):
        for l in self.lights:
            try:
                self.app.render.clearLight(l)
            except Exception:
                pass
        try:
            self.app.render.clearFog()
        except Exception:
            pass
        self.root.removeNode()


# ============================================================================
#  [PC] 카트 노드(100,000종) / 그림자 / 파티클 / 날씨
# ============================================================================
_SHARED = {}


def shared_tex(name, fn):
    t = _SHARED.get(name)
    if t is None:
        t = _SHARED[name] = fn()
    return t


class KartNode(object):
    """Racer 하나를 3D 로 표시. KartModel(파츠 목록) -> Panda3D 지오메트리"""

    def __init__(self, app, racer, parent):
        self.app = app
        self.rc = racer
        m = self.model = KartModel(racer.kart_id)
        self.root = parent.attachNewNode('kart-' + str(racer.id))
        self.yaw = self.root.attachNewNode('yaw')
        self.chassis = self.yaw.attachNewNode('chassis')
        body = Mesh()
        glow = Mesh()
        for (cx, cy, cz, hx, hy, hz, col, tx, ty, g) in m.boxes:
            tgt = glow if g else body
            tgt.box((cx, cz, cy), (hx, hz, hy), rgbf(col, 1.0 if not g else 1.8), taper=(tx, ty) if (tx != 1 or ty != 1) else None)
        hp = m.helmet
        body.sphere((hp[0], hp[2], hp[1]), 0.27, rgbf(m.main), 10, 7)
        body.box((hp[0], hp[2] + 0.2, hp[1] - 0.02), (0.17, 0.07, 0.05), (0.03, 0.03, 0.04, 1))
        body.attach(self.chassis, 'body')
        glow.attach(self.chassis, 'glow').setLightOff()
        # 바퀴
        self.wheels = []
        R, ww = m.wheel_r, m.wheel_w
        for (lx, ly, lz, sgn, front) in m.wheels:
            pivot = self.chassis.attachNewNode('pivot')
            pivot.setPos(lx, lz, ly)
            spin = pivot.attachNewNode('spin')
            tm = Mesh()
            tm.frustum((0, 0, 0), R, R, ww, (0.13, 0.13, 0.15, 1), 'x', 14)
            tm.attach(spin, 'tire')
            rim = Mesh()
            rg = Mesh()
            face = sgn * (ww / 2 + 0.006)
            rc_ = rgbf(m.rim_color)
            if m.rim == 0:
                rim.disc((face, 0, 0), R * 0.66, rc_, 'x')
            elif m.rim in (1, 2):
                rim.disc((face, 0, 0), R * 0.62, (0.1, 0.1, 0.12, 1), 'x')
                n = 5 if m.rim == 1 else 8
                for k in range(n):
                    rim.spoke((face + sgn * 0.002, 0, 0), TAU * k / n, R * 0.62, 0.07 if m.rim == 1 else 0.045, rc_, 'x')
                rim.disc((face + sgn * 0.003, 0, 0), R * 0.14, rc_, 'x', 8)
            elif m.rim == 3:
                rim.disc((face, 0, 0), R * 0.62, (0.15, 0.15, 0.18, 1), 'x')
                rim.annulus((face + sgn * 0.002, 0, 0), R * 0.5, R * 0.64, rc_, 'x')
                rim.disc((face + sgn * 0.003, 0, 0), R * 0.14, rc_, 'x', 8)
            else:
                rim.disc((face, 0, 0), R * 0.62, (0.04, 0.04, 0.06, 1), 'x')
                rg.annulus((face + sgn * 0.002, 0, 0), R * 0.46, R * 0.62, rgbf(m.rim_color, 1.8), 'x')
            rim.attach(spin, 'rim').setTwoSided(True)
            if rg.v:
                rg.attach(spin, 'rimglow').setLightOff()
            self.wheels.append((pivot, spin, front))
        # 그림자 (blob)
        cm = CardMaker('shadow')
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        sh = self.root.attachNewNode(cm.generate())
        sh.setTexture(shared_tex('blob', lambda: tex_glow('blob', 64, 1.0)))
        sh.setColor(0, 0, 0, 0.62)
        sh.setTransparency(TransparencyAttrib.MAlpha)
        sh.setP(-90)
        sh.setPos(0, 0, 0.05)
        sh.setScale(m.W * 1.9, m.L * 1.7, 1)
        sh.setLightOff()
        sh.setDepthWrite(False)
        sh.setBin('fixed', 2)
        self.shadow = sh
        # 부스트 불꽃
        fm = Mesh()
        fm.frustum((0, 0, 0), 0.0, 0.22, 1.4, (3.0, 1.4, 0.4, 0.9), 'y', 8, False)
        self.flame = fm.attach(self.chassis, 'flame')
        self.flame.setPos(0, -m.L / 2 - 0.65, m.base + m.H * 0.3)
        self.flame.setLightOff()
        self.flame.setTransparency(TransparencyAttrib.MAlpha)
        self.flame.hide()
        # 이름표
        self.label = None
        if racer.kind != 'local' and racer.name:
            tn = TextNode('nm')
            tn.setText(racer.name)
            tn.setAlign(TextNode.ACenter)
            tn.setTextColor(1.0, 0.82, 0.47, 1) if racer.kind == 'bot' else tn.setTextColor(0.6, 0.91, 1.0, 1)
            tn.setShadow(0.06, 0.06)
            tn.setShadowColor(0, 0, 0, 1)
            if app.font is not None:
                tn.setFont(app.font)
            lb = self.root.attachNewNode(tn)
            lb.setPos(0, 0, 2.7)
            lb.setScale(0.85)
            lb.setBillboardPointEye()
            lb.setLightOff()
            lb.setFogOff()
            lb.setDepthTest(False)
            lb.setDepthWrite(False)
            lb.setBin('fixed', 40)
            self.label = lb
        self.spin = 0.0

    def update(self, rc, dt, ds, cam_dist):
        m = self.model
        pos = PV(rc.x, rc.y, rc.z)
        up = rc.up
        h = rc.h
        fx, fz = math.sin(h), math.cos(h)
        d = fx * up[0] + fz * up[2]
        F = (fx - up[0] * d, -up[1] * d, fz - up[2] * d)
        fp = PV(*F)
        upp = PV(*up)
        self.root.setPos(*pos)
        self.root.lookAt(Point3(pos[0] + fp[0], pos[1] + fp[1], pos[2] + fp[2]), Vec3(upp[0], upp[1], upp[2]))
        # 드리프트/미끄러짐: 차체만 회전 (코어: drift_dir>0 = 오른쪽 -> Panda H 음수)
        if rc.drifting:
            tgt = -rc.drift_dir * 17.0
        else:
            tgt = clamp(-rc.slip * 1.1, -14.0, 14.0)
        self.yaw.setH(self.yaw.getH() + (tgt - self.yaw.getH()) * min(1.0, dt * 9))
        self.chassis.setR(self.chassis.getR() + ((-rc.steer * 3.5) - self.chassis.getR()) * min(1.0, dt * 8))
        self.spin -= (rc.speed / m.wheel_r) * dt
        deg = math.degrees(self.spin)
        for pivot, spin, front in self.wheels:
            spin.setP(deg)
            if front:
                pivot.setH(-rc.steer * 24.0)
        if rc.boosting:
            self.flame.show()
            self.flame.setScale(1, 0.7 + _random.random() * 0.8, 1)
        else:
            self.flame.hide()
        if self.label is not None:
            self.label.setScale(0.85 * clamp(cam_dist / 16.0, 0.8, 4.0))
            if cam_dist < 11 or cam_dist > 220:
                self.label.hide()
            else:
                self.label.show()

    def destroy(self):
        self.root.removeNode()


class Particles(object):
    def __init__(self, app, n=150):
        self.app = app
        self.items = []
        cm = CardMaker('p')
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        tex = shared_tex('pglow', lambda: tex_glow('pglow', 32, 1.2))
        self.root = app.render.attachNewNode('particles')
        for _ in range(n):
            np_ = self.root.attachNewNode(cm.generate())
            np_.setTexture(tex)
            np_.setBillboardPointEye()
            np_.setLightOff()
            np_.setFogOff()
            np_.setDepthWrite(False)
            np_.setTransparency(TransparencyAttrib.MAlpha)
            np_.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
            np_.setBin('fixed', 30)
            np_.hide()
            self.items.append([np_, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, (1, 1, 1), 1.0])
        self.cursor = 0

    def emit(self, pos, vel, color, size, life):
        it = self.items[self.cursor]
        self.cursor = (self.cursor + 1) % len(self.items)
        it[1], it[2], it[3] = pos
        it[4], it[5], it[6] = vel
        it[7] = life
        it[8] = life
        it[9] = color
        it[10] = size
        it[0].show()

    def update(self, dt):
        for it in self.items:
            if it[7] <= 0:
                continue
            it[7] -= dt
            if it[7] <= 0:
                it[0].hide()
                continue
            it[1] += it[4] * dt
            it[2] += it[5] * dt
            it[3] += it[6] * dt
            it[6] -= 9.0 * dt
            f = it[7] / it[8]
            np_ = it[0]
            np_.setPos(it[1], it[2], it[3])
            np_.setScale(it[10] * (0.4 + f))
            c = it[9]
            np_.setColor(c[0], c[1], c[2], f)

    def destroy(self):
        self.root.removeNode()


class Weather(object):
    """카메라 주변을 도는 점 입자 (눈/불씨/낙엽/스프링클)"""

    def __init__(self, app, kind):
        self.app = app
        self.kind = kind
        self.n = 700 if kind == 'snow' else 380
        fmt = GeomVertexFormat.getV3()
        self.vd = GeomVertexData('weather', fmt, Geom.UHDynamic)
        self.vd.setNumRows(self.n)
        rnd = Rng(99)
        self.pos = [[(rnd() - 0.5) * 160, (rnd() - 0.5) * 160, rnd() * 70, rnd() * 6.28] for _ in range(self.n)]
        prim = GeomPoints(Geom.UHStatic)
        prim.addNextVertices(self.n)
        geom = Geom(self.vd)
        geom.addPrimitive(prim)
        gn = GeomNode('weather')
        gn.addGeom(geom)
        self.np = app.render.attachNewNode(gn)
        col = {'snow': (1, 1, 1, 1), 'ember': (1, 0.55, 0.18, 1), 'leaf': (0.85, 0.4, 0.15, 1), 'sprinkle': (1, 0.5, 0.8, 1)}[kind]
        self.np.setColor(*col)
        self.np.setRenderModeThickness(3.0 if kind == 'snow' else 4.0)
        self.np.setLightOff()
        self.np.setBin('fixed', 25)
        self.np.setDepthWrite(False)
        self.np.node().setBounds(OmniBoundingVolume())
        self.np.node().setFinal(True)
        self.t = 0.0

    def update(self, dt, cam):
        self.t += dt
        vw = GeomVertexWriter(self.vd, 'vertex')
        vy = 2.4 if self.kind == 'ember' else -3.4
        cx, cy, cz = cam
        for i, p in enumerate(self.pos):
            p[2] += vy * dt * (0.6 + (i % 5) * 0.2)
            p[0] += math.sin(self.t + p[3]) * dt * 1.2
            if p[2] < 0:
                p[2] += 70
            elif p[2] > 70:
                p[2] -= 70
            x = ((p[0] - cx + 80) % 160) - 80 + cx
            y = ((p[1] - cy + 80) % 160) - 80 + cy
            vw.setData3(x, y, p[2] + cz - 25)

    def destroy(self):
        self.np.removeNode()


# ============================================================================
#  [PC] 언어/폰트 + HUD + 키보드 메뉴 + 텍스트 입력
# ============================================================================
LANG = 'ko'


def T(ko, en):
    return ko if LANG == 'ko' else en


def find_korean_font():
    here = '.'
    try:
        here = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv and sys.argv[0] else '.'
    except Exception:
        pass
    cands = [os.path.join(here, n) for n in ('kart3d_font.ttf', 'kart3d_font.otf', 'kart3d_font.ttc')]
    cands += ['C:/Windows/Fonts/malgun.ttf', 'C:/Windows/Fonts/malgunbd.ttf', '/System/Library/Fonts/AppleSDGothicNeo.ttc',
              '/System/Library/Fonts/Supplemental/AppleGothic.ttf', '/Library/Fonts/AppleGothic.ttf',
              '/usr/share/fonts/truetype/nanum/NanumGothic.ttf', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
              '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc']
    for p in cands:
        if os.path.isfile(p):
            return p
    try:
        out = subprocess.check_output(['fc-list', ':lang=ko', 'file'], timeout=3).decode('utf-8', 'ignore')
        for line in out.splitlines():
            path = line.split(':')[0].strip()
            if path.lower().endswith(('.ttf', '.otf', '.ttc')) and os.path.isfile(path):
                return path
    except Exception:
        pass
    return None


def fmt_time(t):
    m = int(t // 60)
    return '%d:%05.2f' % (m, t - m * 60)


class Bar(object):
    """CardMaker 로 만든 가로 막대 (HUD/스탯)"""

    def __init__(self, parent, x, z, w, h, color, back=(0, 0, 0, 0.5)):
        cm = CardMaker('bar')
        cm.setFrame(0, 1, 0, 1)
        self.back = parent.attachNewNode(cm.generate())
        self.back.setPos(x, 0, z)
        self.back.setScale(w, 1, h)
        self.back.setColor(*back)
        self.back.setTransparency(TransparencyAttrib.MAlpha)
        self.fill = parent.attachNewNode(cm.generate())
        self.fill.setPos(x, 0, z)
        self.w, self.h = w, h
        self.fill.setColor(*color)
        self.set(0.0)

    def set(self, v, color=None):
        v = clamp(v, 0.0, 1.0)
        self.fill.setScale(max(0.0001, self.w * v), 1, self.h)
        if color:
            self.fill.setColor(*color)

    def show(self, flag=True):
        for n in (self.back, self.fill):
            n.show() if flag else n.hide()


class HUD(object):
    def __init__(self, app):
        self.app = app
        a = app
        self.root = a.aspect2d.attachNewNode('hud')
        kw = dict(font=a.font, mayChange=True, shadow=(0, 0, 0, 1))
        TL, TR, BR, TC = a.a2dTopLeft, a.a2dTopRight, a.a2dBottomRight, a.a2dTopCenter
        self.pos = OnscreenText(text='1', parent=TL, pos=(0.08, -0.2), scale=0.2, fg=(1, 0.69, 0.13, 1), align=TextNode.ALeft, **kw)
        self.tot = OnscreenText(text='/8', parent=TL, pos=(0.34, -0.2), scale=0.09, fg=(1, 1, 1, 1), align=TextNode.ALeft, **kw)
        self.lap = OnscreenText(text='LAP 1/3', parent=TL, pos=(0.08, -0.31), scale=0.062, fg=(1, 1, 1, 1), align=TextNode.ALeft, **kw)
        self.time = OnscreenText(text='0:00.00', parent=TL, pos=(0.08, -0.39), scale=0.055, fg=(0.85, 0.9, 1, 1), align=TextNode.ALeft, **kw)
        self.spd = OnscreenText(text='0', parent=BR, pos=(-0.45, 0.18), scale=0.2, fg=(1, 1, 1, 1), align=TextNode.ARight, **kw)
        self.kmh = OnscreenText(text='km/h', parent=BR, pos=(-0.43, 0.18), scale=0.06, fg=(0.8, 0.85, 0.96, 1), align=TextNode.ALeft, **kw)
        self.boost = Bar(BR, -0.88, 0.1, 0.78, 0.028, (0.1, 0.9, 1.0, 1))
        self.drift = Bar(BR, -0.88, 0.065, 0.78, 0.018, (1, 1, 1, 1))
        self.board = [OnscreenText(text='', parent=TL, pos=(0.08, -0.52 - i * 0.065), scale=0.045, fg=(1, 1, 1, 1), align=TextNode.ALeft, **kw) for i in range(6)]
        self.center = OnscreenText(text='', parent=a.aspect2d, pos=(0, 0.45), scale=0.3, fg=(1, 1, 1, 1), align=TextNode.ACenter, **kw)
        self.toast = OnscreenText(text='', parent=a.aspect2d, pos=(0, 0.62), scale=0.1, fg=(1, 0.8, 0.27, 1), align=TextNode.ACenter, **kw)
        self.wrong = OnscreenText(text='', parent=a.aspect2d, pos=(0, 0.2), scale=0.13, fg=(1, 0.3, 0.35, 1), align=TextNode.ACenter, **kw)
        self.fps = OnscreenText(text='', parent=a.a2dBottomLeft, pos=(0.03, 0.03), scale=0.04, fg=(1, 1, 0, 1), align=TextNode.ALeft, **kw)
        self.mapname = OnscreenText(text='', parent=TR, pos=(-0.04, -0.56), scale=0.04, fg=(0.85, 0.9, 1, 1), align=TextNode.ARight, **kw)
        self.mini_np = None
        self.dots = []
        self.toast_until = 0.0
        self.center_until = 0.0
        self.visible = True

    def build_minimap(self, track):
        if self.mini_np is not None:
            self.mini_np.removeNode()
        a = self.app
        self.mini_np = a.a2dTopRight.attachNewNode('mini')
        self.mini_np.setPos(-0.3, 0, -0.3)
        b = track.bounds
        span = max(b[1] - b[0], b[3] - b[2], 1.0)
        self.mm_span = span
        self.mm_c = ((b[0] + b[1]) / 2.0, (b[2] + b[3]) / 2.0)
        cm = CardMaker('mbg')
        cm.setFrame(-0.27, 0.27, -0.27, 0.27)
        bg = self.mini_np.attachNewNode(cm.generate())
        bg.setColor(0, 0, 0, 0.4)
        bg.setTransparency(TransparencyAttrib.MAlpha)
        for thick, col in ((6, (0, 0, 0, 1)), (3, (0.92, 0.94, 1, 1))):
            ls = LineSegs('trk')
            ls.setThickness(thick)
            ls.setColor(*col)
            for i in range(0, track.N + 1, 2):
                k = i % track.N
                x, z = self.mm_xy(track.px[k], track.pz[k])
                (ls.moveTo if i == 0 else ls.drawTo)(x, 0, z)
            self.mini_np.attachNewNode(ls.create())
        for d in self.dots:
            d.removeNode()
        self.dots = []
        for i in range(14):
            cmd = CardMaker('dot')
            cmd.setFrame(-0.011, 0.011, -0.011, 0.011)
            d = self.mini_np.attachNewNode(cmd.generate())
            d.hide()
            self.dots.append(d)

    def mm_xy(self, x, z):
        s = 0.5 / self.mm_span
        return ((x - self.mm_c[0]) * s, -(z - self.mm_c[1]) * s)

    def show(self, flag):
        self.visible = flag
        for n in (self.pos, self.tot, self.lap, self.time, self.spd, self.kmh, self.center, self.toast, self.wrong, self.fps, self.mapname, *self.board):
            n.show() if flag else n.hide()
        self.boost.show(flag)
        self.drift.show(flag)
        if self.mini_np is not None:
            self.mini_np.show() if flag else self.mini_np.hide()

    def update(self, race, now):
        loc = race.local
        sim = loc.sim
        rank = race.ranking()
        self.pos.setText(str(rank.index(loc) + 1))
        w = 0.1 * len(str(rank.index(loc) + 1))
        self.tot.setPos(0.28 + 0.12 * (len(str(rank.index(loc) + 1)) - 1), -0.2)
        self.tot.setText('/%d' % len(race.racers))
        self.lap.setText('LAP %d/%d' % (min(race.laps, sim.lap), race.laps))
        self.time.setText(fmt_time(max(0.0, race.t)))
        self.spd.setText(str(int(sim.speed * 3.6)))
        self.boost.set(sim.speed / sim.stats['max_speed'], (1.0, 0.63, 0.16, 1) if sim.boost_t > 0 else (0.1, 0.9, 1.0, 1))
        if sim.drifting:
            col = [(0.67, 0.8, 1, 1), (0.23, 0.67, 1, 1), (1, 0.63, 0.16, 1), (0.82, 0.31, 1, 1)][sim.drift_tier]
            self.drift.show(True)
            self.drift.set(sim.drift_charge / 3.2, col)
        else:
            self.drift.show(False)
        for i, t in enumerate(self.board):
            if i < len(rank):
                r = rank[i]
                t.setText('%d  %s' % (i + 1, r.name))
                t.setFg((1, 0.72, 0.15, 1) if r is loc else (1, 1, 1, 1))
            else:
                t.setText('')
        # 카운트다운 / 알림
        if race.phase == 'count':
            n = int(math.ceil(max(0.0, race.count_left)))
            self.center.setText(str(n) if 1 <= n <= 3 else '')
        elif now > self.center_until:
            self.center.setText('')
        if now > self.toast_until:
            self.toast.setText('')
        self.wrong.setText(T('역주행!', 'WRONG WAY!') if (sim.wrong_way and race.phase == 'run' and not loc.finished) else '')
        # 미니맵
        if self.mini_np is not None:
            for i, d in enumerate(self.dots):
                if i < len(race.racers):
                    rc = race.racers[i]
                    x, z = self.mm_xy(rc.x, rc.z)
                    d.setPos(x, 0, z)
                    d.setColor(*((1, 0.69, 0.13, 1) if rc is loc else ((1, 0.43, 0.43, 1) if rc.kind == 'bot' else (0.35, 0.9, 1, 1))))
                    d.setScale(1.7 if rc is loc else 1.0)
                    d.show()
                else:
                    d.hide()

    def say(self, text, secs=1.2, big=False, color=(1, 0.8, 0.27, 1)):
        if big:
            self.center.setText(text)
            self.center_until = time.time() + secs
        else:
            self.toast.setText(text)
            self.toast.setFg(color)
            self.toast_until = time.time() + secs

    def destroy(self):
        self.root.removeNode()
        for n in (self.pos, self.tot, self.lap, self.time, self.spd, self.kmh, self.center, self.toast, self.wrong, self.fps, self.mapname, *self.board):
            n.destroy()
        for b in (self.boost, self.drift):
            b.back.removeNode()
            b.fill.removeNode()
        if self.mini_np is not None:
            self.mini_np.removeNode()


class MenuUI(object):
    """키보드로 조작하는 텍스트 메뉴 (↑↓ 선택, ←→ 값 변경, Enter 실행, Esc 뒤로)"""

    def __init__(self, app):
        self.app = app
        self.root = app.a2dTopLeft.attachNewNode('menu')
        self.extra = app.aspect2d.attachNewNode('menu-extra')
        self.nodes = []
        self.rows = []
        self.sel = 0
        self.title = ''
        self.subtitle = ''
        self.hint = ''
        self.visible = True
        cm = CardMaker('panel')
        cm.setFrame(0.03, 1.72, -1.97, -0.04)
        self.panel = self.root.attachNewNode(cm.generate())
        self.panel.setColor(0.03, 0.05, 0.11, 0.78)
        self.panel.setTransparency(TransparencyAttrib.MAlpha)

    def set(self, title, rows, subtitle='', hint='', keep=True):
        sel_row = self.rows[self.sel].get('id') if (keep and self.rows and self.sel < len(self.rows)) else None
        self.title, self.rows, self.subtitle, self.hint = title, rows, subtitle, hint
        self.sel = 0
        if sel_row is not None:
            for i, r in enumerate(rows):
                if r.get('id') == sel_row:
                    self.sel = i
        if not self._selectable(self.sel):
            self.move(1)
        self.rebuild()

    def _selectable(self, i):
        return 0 <= i < len(self.rows) and self.rows[i].get('kind', 'item') != 'info' and self.rows[i].get('enabled', True)

    def clear(self):
        for n in self.nodes:
            n.destroy()
        self.nodes = []

    def rebuild(self):
        self.clear()
        a = self.app
        kw = dict(parent=self.root, font=a.font, mayChange=False, shadow=(0, 0, 0, 1), align=TextNode.ALeft)
        self.nodes.append(OnscreenText(text=self.title, pos=(0.12, -0.24), scale=0.13, fg=(1, 0.69, 0.13, 1), **kw))
        if self.subtitle:
            self.nodes.append(OnscreenText(text=self.subtitle, pos=(0.12, -0.34), scale=0.05, fg=(0.8, 0.86, 1, 1), **kw))
        z = -0.5
        for i, r in enumerate(self.rows):
            kind = r.get('kind', 'item')
            if kind == 'info':
                col = r.get('color', (0.78, 0.84, 0.98, 1))
                self.nodes.append(OnscreenText(text=r['text'], pos=(0.12, z), scale=r.get('scale', 0.05), fg=col, **kw))
                z -= r.get('gap', 0.075)
                continue
            sel = (i == self.sel)
            en = r.get('enabled', True)
            col = (1, 0.78, 0.22, 1) if sel else ((0.55, 0.57, 0.63, 1) if not en else ((1, 0.55, 0.45, 1) if kind == 'primary' else (0.95, 0.97, 1, 1)))
            txt = ('> ' if sel else '   ') + r['text']
            self.nodes.append(OnscreenText(text=txt, pos=(0.1, z), scale=0.074, fg=col, **kw))
            z -= 0.1
        if self.hint:
            self.nodes.append(OnscreenText(text=self.hint, pos=(0.12, -1.9), scale=0.04, fg=(0.7, 0.78, 0.95, 1), **kw))

    def move(self, d):
        n = len(self.rows)
        if n == 0:
            return
        for _ in range(n):
            self.sel = (self.sel + d) % n
            if self._selectable(self.sel):
                break
        self.rebuild()
        self.app.sfx_play('click', 0.4)

    def key(self, name, mult=1):
        if not self.rows:
            return False
        r = self.rows[self.sel] if self._selectable(self.sel) else None
        if name in ('arrow_down', 's'):
            self.move(1)
        elif name in ('arrow_up', 'w'):
            self.move(-1)
        elif name in ('arrow_left', 'a') and r and r.get('left'):
            r['left'](mult)
        elif name in ('arrow_right', 'd') and r and r.get('right'):
            r['right'](mult)
        elif name in ('enter', 'space') and r and r.get('enter'):
            self.app.sfx_play('click', 0.5)
            r['enter']()
        else:
            return False
        return True

    def show(self, flag):
        self.visible = flag
        if flag:
            self.root.show()
            self.extra.show()
        else:
            self.root.hide()
            self.extra.hide()

    def clear_extra(self):
        for c in list(self.extra.getChildren()):
            c.removeNode()


class TextInput(object):
    def __init__(self, app):
        self.app = app
        self.active = False
        self.text = ''
        self.title = ''
        self.maxlen = 14
        self.mode = 'alpha'
        self.cb = None
        self.node = None
        self.t = 0.0

    def begin(self, title, text, maxlen, mode, cb):
        self.active = True
        self.title, self.text, self.maxlen, self.mode, self.cb = title, str(text), maxlen, mode, cb
        self._draw()

    def _draw(self):
        if self.node is not None:
            self.node.destroy()
            self.node = None
        if not self.active:
            return
        cursor = '_' if int(self.t * 2) % 2 == 0 else ' '
        self.node = OnscreenText(text='%s\n\n%s%s\n\n[Enter] OK   [Esc] %s' % (self.title, self.text, cursor, T('취소', 'Cancel')), parent=self.app.aspect2d, pos=(0, 0.15), scale=0.085,
                                 fg=(1, 1, 1, 1), bg=(0, 0, 0, 0.88), shadow=(0, 0, 0, 1), align=TextNode.ACenter, font=self.app.font, mayChange=False)

    def tick(self, dt):
        if self.active:
            old = int(self.t * 2)
            self.t += dt
            if int(self.t * 2) != old:
                self._draw()

    def char(self, ch):
        if not self.active or len(ch) != 1 or not ch.isprintable():
            return
        if self.mode == 'num' and ch not in '0123456789':
            return
        if self.mode == 'ip' and ch not in '0123456789.:':
            return
        if len(self.text) < self.maxlen:
            self.text += ch
            self._draw()

    def backspace(self):
        if self.active:
            self.text = self.text[:-1]
            self._draw()

    def finish(self, ok):
        cb, text = self.cb, self.text
        self.active = False
        self._draw()
        if ok and cb:
            cb(text)


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


# ============================================================================
#  [PC] 게임 본체: 장면(메뉴/솔로/차고/설정/멀티/로비/레이스/결과) + 메인 루프
# ============================================================================
def wrap_map(m):
    return ((int(m) - 1) % MAP_COUNT) + 1


class Game(ShowBase):
    def __init__(self, args):
        global LANG
        self.args = args
        offscreen = bool(os.environ.get('KART3D_OFFSCREEN')) or bool(args.get('offscreen'))
        w, h = args.get('window', (1280, 720))
        cfg = ['window-title TURBO KART 3D', 'win-size %d %d' % (w, h), 'sync-video 1', 'framebuffer-multisample 1', 'multisamples 4']
        if args.get('fullscreen'):
            cfg.append('fullscreen 1')
        if offscreen:
            cfg += ['window-type offscreen', 'load-display p3tinydisplay', 'audio-library-name null']
        loadPrcFileData('', '\n'.join(cfg))
        ShowBase.__init__(self)
        self.offscreen = offscreen
        self.disableMouse()
        self.render.setAntialias(AntialiasAttrib.MAuto)
        self.camLens.setNearFar(0.4, 6000.0)
        self.profile = Profile()
        if args.get('port'):
            self.profile['port'] = args['port']
        path = find_korean_font()
        self.font = None
        self.font_en = None
        if path:
            try:
                self.font = self.loader.loadFont(Filename.fromOsSpecific(path).getFullpath())
                self.font.setPixelsPerUnit(64)
            except Exception:
                self.font = None
        lang = args.get('lang') or self.profile['lang']
        if lang == 'auto':
            lang = 'ko' if self.font else 'en'
        LANG = lang
        self.session = Session(self.profile)
        self.audio = Audio(self, self.profile['sound'])
        self.menu = MenuUI(self)
        self.input = TextInput(self)
        self.hud = HUD(self)
        self.hud.show(False)
        self.keys = set()
        self.steer = 0.0
        self.scene = 'menu'
        self.world = None
        self.world_map = None
        self.show_node = None
        self.show_rc = None
        self.race = None
        self.nodes = {}
        self.particles = None
        self.weather = None
        self.chase = ChaseCam()
        self.paused = False
        self.t = 0.0
        self.dt_override = None
        self.sel_map = int(self.profile['map'])
        self.scan = {'busy': False, 'rooms': [], 'done': False}
        self.err = ''
        self.finish_at = None
        self.shake = 0.0
        self.show_fps = bool(args.get('fps'))
        self.loading_txt = None
        self.shown_scene = None
        self.pad = None
        try:
            devs = self.devices.getDevices(InputDevice.DeviceClass.gamepad)
            if devs:
                self.pad = devs[0]
                self.attachInputDevice(self.pad)
        except Exception:
            self.pad = None
        # 키 입력
        try:
            self.buttonThrowers[0].node().setModifierButtons(ModifierButtons())
            self.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
        except Exception:
            pass
        names = ['arrow_up', 'arrow_down', 'arrow_left', 'arrow_right', 'w', 'a', 's', 'd', 'space', 'lshift', 'rshift', 'lcontrol', 'rcontrol',
                 'r', 'm', 'enter', 'escape', 'f11', 'backspace', 't']
        for k in names:
            self.accept(k, self._kdown, [k])
            self.accept(k + '-up', self._kup, [k])
            self.accept(k + '-repeat', self._krep, [k])
        self.accept('keystroke', self._keystroke)
        self.taskMgr.add(self.tick, 'tick')
        self.go('menu')

    # ------------------------------------------------------------------ 입력 처리
    def _kdown(self, k):
        self.keys.add(k)
        self.on_key(k)

    def _kup(self, k):
        self.keys.discard(k)

    def _krep(self, k):
        if k in ('arrow_up', 'arrow_down', 'arrow_left', 'arrow_right', 'backspace'):
            self.on_key(k)

    def _keystroke(self, ch):
        if self.input.active:
            self.input.char(ch)

    def mult(self):
        if 'lcontrol' in self.keys or 'rcontrol' in self.keys:
            return 100
        if 'lshift' in self.keys or 'rshift' in self.keys:
            return 10
        return 1

    def on_key(self, k):
        if self.input.active:
            if k == 'enter':
                self.input.finish(True)
            elif k == 'escape':
                self.input.finish(False)
            elif k == 'backspace':
                self.input.backspace()
            return
        if k == 'f11' and not self.offscreen:
            try:
                props = WindowProperties()
                props.setFullscreen(not self.win.isFullscreen())
                self.win.requestProperties(props)
            except Exception:
                pass
            return
        if self.scene == 'race':
            if k == 'r' and self.race:
                self.race.respawn_local()
            elif k == 'escape':
                self.toggle_pause()
            elif k == 'm':
                self.audio.enabled = not self.audio.enabled
                self.hud.say(T('소리 켬', 'Sound on') if self.audio.enabled else T('소리 끔', 'Sound off'), 0.8)
                if not self.audio.enabled:
                    self.audio.silence()
            elif self.paused or self.scene == 'results':
                self.menu.key(k, 1)
            return
        if k == 'escape':
            self.back()
            return
        if self.scene == 'solo':
            if k == 'r':
                self.sel_map = 1 + int(_random.random() * MAP_COUNT)
                self.build_solo()
                return
            if k == 't':
                self.sel_map = wrap_map(((self.sel_map - 1) // 10) * 10 + (map_info(self.sel_map)['theme'] + 1) % 10 + 1)
                self.build_solo()
                return
        self.menu.key(k, self.mult())

    def back(self):
        sc = self.scene
        if sc == 'menu':
            self.userExit()
        elif sc in ('solo', 'garage', 'settings', 'multi'):
            self.profile.save()
            self.go('menu')
        elif sc == 'lobby':
            self.session.leave()
            self.go('menu')
        elif sc == 'results':
            self.leave_race()

    def sfx_play(self, name, vol=1.0):
        self.audio.play(name, vol)

    def loading(self, msg):
        if self.loading_txt is not None:
            self.loading_txt.destroy()
        self.loading_txt = OnscreenText(text=msg, parent=self.aspect2d, pos=(0, 0), scale=0.11, fg=(1, 1, 1, 1), bg=(0, 0, 0, 0.85), font=self.font, mayChange=False)
        self.graphicsEngine.renderFrame()
        self.graphicsEngine.renderFrame()

    def loading_done(self):
        if self.loading_txt is not None:
            self.loading_txt.destroy()
            self.loading_txt = None

    # ------------------------------------------------------------------ 월드/쇼룸
    def destroy_world(self):
        for n in list(self.nodes.values()):
            n.destroy()
        self.nodes = {}
        if self.show_node is not None:
            self.show_node.destroy()
            self.show_node = None
        if self.particles is not None:
            self.particles.destroy()
            self.particles = None
        if self.weather is not None:
            self.weather.destroy()
            self.weather = None
        if self.world is not None:
            self.world.destroy()
            self.world = None
        self.world_map = None

    def ensure_showroom(self):
        mid = int(self.profile['map'])
        if self.world is None or self.world_map != mid:
            self.destroy_world()
            self.loading(T('준비 중…', 'Preparing…'))
            tr = Track(mid)
            self.world = World(self, tr)
            self.world_map = mid
            self.loading_done()
            rc = Racer('show', '', int(self.profile['kart']), 0, 'bot')
            pf = tr.N - 9.0
            x, y, z, h = tr.pose_at(pf, 0.0)
            rc.x, rc.y, rc.z, rc.h = x, y, z, h
            rc.idx = int(pf) % tr.N
            rc.up = tr.surface_normal(rc.idx)
            rc.speed = 7.0
            self.show_rc = rc
            self.show_node = KartNode(self, rc, self.world.root)
        if self.show_node.rc.kart_id != int(self.profile['kart']):
            self.show_node.destroy()
            self.show_rc.kart_id = int(self.profile['kart'])
            self.show_node = KartNode(self, self.show_rc, self.world.root)

    def update_showroom(self, dt):
        self.ensure_showroom()
        rc = self.show_rc
        rc.total += dt * 2.0
        self.show_node.update(rc, dt, self.world.track.ds, 20.0)
        th = self.t * 0.45
        ctr = PV(rc.x, rc.y + 0.9, rc.z)
        dist = 8.2
        shift = 0.0
        if self.scene in ('menu', 'garage'):
            shift = -2.6
        # 카메라 오빗 (카트가 화면 오른쪽에 오도록 중심을 왼쪽으로 이동)
        cam = (ctr[0] + math.sin(th) * dist, ctr[1] + math.cos(th) * dist, ctr[2] + 1.5)
        self.camera.setPos(*cam)
        right = (-math.cos(th), math.sin(th), 0.0)
        self.camera.lookAt(Point3(ctr[0] + right[0] * shift, ctr[1] + right[1] * shift, ctr[2]), Vec3(0, 0, 1))
        self.camLens.setFov(56)
        self.world.update(cam)

    # ------------------------------------------------------------------ 장면 구성 (메뉴 행)
    def R(self, text, enter=None, left=None, right=None, kind='item', enabled=True, id=None):
        return dict(text=text, enter=enter, left=left, right=right, kind=kind, enabled=enabled, id=id)

    def I(self, text, color=None, scale=0.05):
        d = dict(text=text, kind='info', scale=scale)
        if color:
            d['color'] = color
        return d

    def go(self, scene):
        self.scene = scene
        self.err = ''
        self.menu.clear_extra()
        if scene != 'race':
            self.hud.show(False)
            self.menu.show(True)
        if scene == 'menu':
            self.build_main()
        elif scene == 'solo':
            self.sel_map = int(self.profile['map'])
            self.build_solo()
        elif scene == 'garage':
            self.build_garage()
        elif scene == 'settings':
            self.build_settings()
        elif scene == 'multi':
            self.scan_rooms()
            self.build_multi()
        elif scene == 'lobby':
            self.build_lobby()

    def build_main(self):
        self.menu.clear_extra()
        rows = [self.R(T('솔로 레이스', 'Solo race'), lambda: self.go('solo'), kind='primary', id='solo'),
                self.R(T('WiFi 멀티플레이', 'WiFi multiplayer'), lambda: self.go('multi'), kind='primary', id='multi'),
                self.R(T('차고 (카트 꾸미기)', 'Garage (customize)'), lambda: self.go('garage'), id='garage'),
                self.R(T('설정', 'Settings'), lambda: self.go('settings'), id='settings'),
                self.R(T('종료', 'Quit'), self.userExit, id='quit')]
        if self.err:
            rows.append(self.I(self.err, (1, 0.5, 0.5, 1)))
        rows.append(self.I('%s  #%d' % (kart_name(self.profile['kart'], LANG), int(self.profile['kart']) + 1), scale=0.045))
        self.menu.set('TURBO KART 3D', rows, T('맵 1000개 · 카트 100,000종 · WiFi 멀티', '1000 maps · 100,000 karts · WiFi multiplayer'), T('↑↓ 선택   Enter 확인   F11 전체화면', 'Up/Down select   Enter OK   F11 fullscreen'))

    # ---- 솔로 ----
    def draw_outline(self, mid):
        self.menu.clear_extra()
        tr = Track(mid, True)
        b = tr.bounds
        span = max(b[1] - b[0], b[3] - b[2], 1.0)
        aspect = self.getAspectRatio()
        node = self.menu.extra.attachNewNode('outline')
        node.setPos(aspect - 0.78, 0, 0.12)
        cm = CardMaker('obg')
        cm.setFrame(-0.68, 0.68, -0.62, 0.62)
        bg = node.attachNewNode(cm.generate())
        bg.setColor(0.03, 0.05, 0.11, 0.78)
        bg.setTransparency(TransparencyAttrib.MAlpha)
        cx, cz = (b[0] + b[1]) / 2.0, (b[2] + b[3]) / 2.0
        s = 1.05 / span
        wc = hex_rgb(tr.theme['wall'][0])
        for thick, col in ((7, (0, 0, 0, 1)), (4, (wc[0] / 255.0, wc[1] / 255.0, wc[2] / 255.0, 1)), (2, (0.17, 0.18, 0.23, 1))):
            ls = LineSegs('o')
            ls.setThickness(thick)
            ls.setColor(*col)
            for i in range(0, tr.N + 1, 2):
                k = i % tr.N
                (ls.moveTo if i == 0 else ls.drawTo)((tr.px[k] - cx) * s, 0, -(tr.pz[k] - cz) * s)
            node.attachNewNode(ls.create())
        t = OnscreenText(text='%s · %.2f km' % (tr.theme['name'] if LANG == 'ko' else tr.theme['en'], tr.length / 1000.0), parent=node, pos=(0, -0.7), scale=0.05, fg=(0.85, 0.9, 1, 1),
                         font=self.font, mayChange=False, shadow=(0, 0, 0, 1))
        self.menu.nodes.append(t)
        self.outline_len = tr.length

    def build_solo(self):
        mid = self.sel_map = wrap_map(self.sel_map)
        info = map_info(mid)
        name = info['name'] if LANG == 'ko' else info['name_en']
        theme = info['theme_name'] if LANG == 'ko' else info['theme_en']

        def chg(d):
            def f(m=1):
                self.sel_map = wrap_map(self.sel_map + d * m)
                self.build_solo()
            return f

        def settheme(d):
            def f(m=1):
                th = (map_info(self.sel_map)['theme'] + d) % 10
                self.sel_map = wrap_map(((self.sel_map - 1) // 10) * 10 + th + 1)
                self.build_solo()
            return f

        def typemap():
            def done(t):
                try:
                    self.sel_map = wrap_map(int(t))
                except ValueError:
                    pass
                self.build_solo()
            self.input.begin(T('맵 번호 (1~1000)', 'Map number (1-1000)'), '', 4, 'num', done)

        def lap(d):
            def f(m=1):
                self.profile['laps'] = int(clamp(int(self.profile['laps']) + d, 1, 10))
                self.build_solo()
            return f

        def bots(d):
            def f(m=1):
                self.profile['bots'] = int(clamp(int(self.profile['bots']) + d, 0, 11))
                self.build_solo()
            return f

        def start():
            self.profile['map'] = self.sel_map
            self.profile.save()
            self.start_solo()
        rows = [self.R('%s  < #%d / %d >' % (T('맵', 'Map'), mid, MAP_COUNT), typemap, chg(-1), chg(1), id='map'),
                self.R('%s  < %s >' % (T('테마', 'Theme'), theme), None, settheme(-1), settheme(1), id='theme'),
                self.R('%s  < %d >' % (T('바퀴 수', 'Laps'), int(self.profile['laps'])), None, lap(-1), lap(1), id='laps'),
                self.R('%s  < %d >' % (T('AI 상대', 'AI rivals'), int(self.profile['bots'])), None, bots(-1), bots(1), id='bots'),
                self.R(T('출발!', 'START!'), start, kind='primary', id='start'),
                self.R(T('뒤로', 'Back'), lambda: self.back(), id='back')]
        self.menu.set(T('솔로 레이스', 'Solo race'), rows, name, T('←→ ±1   Shift ±10   Ctrl ±100   R 랜덤   T 테마   Enter(맵) 번호 입력', 'Left/Right ±1   Shift ±10   Ctrl ±100   R random   T theme   Enter on map: type number'))
        self.draw_outline(mid)

    # ---- 차고 ----
    def build_garage(self):
        k = decode_kart(self.profile['kart'])

        def part(key, mod):
            def mk(d):
                def f(m=1):
                    k2 = decode_kart(self.profile['kart'])
                    k2[key] = (k2[key] + d) % mod
                    self.profile['kart'] = encode_kart(k2)
                    self.profile.save()
                    self.session.send_profile()
                    self.build_garage()
                return f
            return mk(-1), mk(1)

        def setname():
            def done(t):
                self.profile['name'] = t.strip()
                self.profile.save()
                self.session.send_profile()
                self.build_garage()
            self.input.begin(T('닉네임', 'Nickname'), self.profile['name'], 14, 'alpha', done)

        def num(d):
            def f(m=1):
                self.profile['kart'] = (int(self.profile['kart']) + d * m) % KART_COUNT
                self.profile.save()
                self.session.send_profile()
                self.build_garage()
            return f

        def typenum():
            def done(t):
                try:
                    self.profile['kart'] = int(clamp(int(t), 1, KART_COUNT)) - 1
                    self.profile.save()
                    self.session.send_profile()
                except ValueError:
                    pass
                self.build_garage()
            self.input.begin(T('카트 번호 (1~100000)', 'Kart number (1-100000)'), '', 6, 'num', done)

        def rnd():
            self.profile['kart'] = int(_random.random() * KART_COUNT)
            self.profile.save()
            self.session.send_profile()
            self.build_garage()
        kk = 'name' if LANG == 'ko' else 'en'
        bl, br = part('body', 20)
        pl, pr = part('paint', 20)
        wl, wr = part('wheel', 25)
        gl, gr = part('wing', 10)
        rows = [self.R('%s: %s' % (T('닉네임', 'Name'), self.profile.display_name()), setname, id='name'),
                self.R('%s  < %s >' % (T('차체', 'Body'), BODIES[k['body']][kk]), None, bl, br, id='body'),
                self.R('%s  < %s >' % (T('페인트', 'Paint'), PAINTS[k['paint']][kk]), None, pl, pr, id='paint'),
                self.R('%s  < %s >' % (T('휠', 'Wheels'), wheel_name(k['wheel'], LANG)), None, wl, wr, id='wheel'),
                self.R('%s  < %s >' % (T('윙/파츠', 'Wing'), WINGS[k['wing']][kk]), None, gl, gr, id='wing'),
                self.R('%s  < %d / %d >' % (T('카트 번호', 'Kart No.'), int(self.profile['kart']) + 1, KART_COUNT), typenum, num(-1), num(1), id='num'),
                self.R(T('랜덤 카트', 'Random kart'), rnd, kind='primary', id='rnd'),
                self.R(T('완료', 'Done'), lambda: self.back(), id='done')]
        self.menu.set(T('차고', 'Garage'), rows, kart_name(self.profile['kart'], LANG), T('←→ 파츠 변경   Shift/Ctrl 번호 ±10/±100', 'Left/Right change   Shift/Ctrl number ±10/±100'))
        self.menu.clear_extra()
        st = kart_stats(self.profile['kart'])
        aspect = self.getAspectRatio()
        for i, (lab, key) in enumerate(((T('최고속도', 'Speed'), 'speed'), (T('가속', 'Accel'), 'accel'), (T('핸들링', 'Handling'), 'handling'), (T('드리프트', 'Drift'), 'drift'))):
            z = -0.52 - i * 0.12
            x0 = aspect - 1.05
            self.menu.nodes.append(OnscreenText(text=lab, parent=self.menu.extra, pos=(x0, z + 0.9 + 0.0), scale=0.045, fg=(0.8, 0.86, 1, 1), align=TextNode.ALeft, font=self.font, mayChange=False, shadow=(0, 0, 0, 1)))
            Bar(self.menu.extra, x0 + 0.3, z + 0.9 - 0.005, 0.5, 0.035, (1, 0.69, 0.13, 1)).set(st[key] / 10.0)

    # ---- 설정 ----
    def build_settings(self):
        def lang():
            order = ['auto', 'ko', 'en']
            self.profile['lang'] = order[(order.index(self.profile['lang']) + 1) % 3]
            global LANG
            LANG = ('ko' if self.font else 'en') if self.profile['lang'] == 'auto' else self.profile['lang']
            self.profile.save()
            self.build_settings()

        def snd():
            self.profile['sound'] = not self.profile['sound']
            self.audio.enabled = bool(self.profile['sound'])
            self.profile.save()
            self.build_settings()

        def fps():
            self.show_fps = not self.show_fps
            self.build_settings()
        rows = [self.R('%s: %s' % (T('언어 / Language', 'Language'), self.profile['lang']), lang, id='lang'),
                self.R('%s: %s' % (T('소리', 'Sound'), 'ON' if self.profile['sound'] else 'OFF'), snd, id='snd'),
                self.R('FPS: %s' % ('ON' if self.show_fps else 'OFF'), fps, id='fps'),
                self.R(T('완료', 'Done'), lambda: self.back(), id='done')]
        self.menu.set(T('설정', 'Settings'), rows, '', T('Enter 로 값 변경', 'Enter to change'))

    # ---- 멀티플레이 ----
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
        self.go('lobby')

    def build_multi(self):
        ips = local_ips()

        def host():
            if self.session.host_game(int(self.profile['port'])):
                self.go('lobby')
            else:
                self.err = self.session.error
                self.build_multi()

        def ipin():
            self.input.begin(T('호스트 IP (예: 192.168.0.5)', 'Host IP (e.g. 192.168.0.5)'), self.profile['last_ip'], 21, 'ip', self.join_ip)

        def rescan():
            self.scan_rooms()
            self.build_multi()
        rows = [self.I(T('내 IP: ', 'My IP: ') + (', '.join(ips) if ips else T('(WiFi 연결 확인)', '(check WiFi)'))),
                self.R(T('방 만들기 (호스트)', 'Host a game'), host, kind='primary', id='host'),
                self.R(T('IP 직접 입력해서 참가', 'Join by IP'), ipin, id='ip'),
                self.R(T('방 다시 검색', 'Rescan rooms'), rescan, id='rescan'),
                self.I(T('같은 WiFi 의 방:', 'Rooms on this WiFi:'), (1, 0.86, 0.47, 1))]
        rooms = self.scan.get('rooms', [])
        if self.scan.get('busy') and not rooms:
            rows.append(self.I(T('검색 중…', 'Searching…')))
        elif not rooms:
            rows.append(self.I(T('방이 없어요. 친구가 [방 만들기] 후 IP 로 접속하세요.', 'No rooms. Ask a friend to host, then join by IP.')))
        for i, rm in enumerate(rooms[:6]):
            def joiner(rm=rm):
                self.profile['last_ip'] = rm['ip']
                self.session.join_game(rm['ip'], rm.get('port', DEFAULT_PORT))
                self.go('lobby')
            rows.append(self.R('%s  %s  %d/%d  #%s' % (rm.get('name', 'room'), rm['ip'], rm.get('players', 0), RoomServer.MAX_PLAYERS, rm.get('map', '?')), joiner,
                               enabled=rm.get('state') == 'lobby', id='room%d' % i))
        if self.err:
            rows.append(self.I(self.err, (1, 0.5, 0.5, 1)))
        rows.append(self.R(T('뒤로', 'Back'), lambda: self.back(), id='back'))
        self.menu.set(T('WiFi 멀티플레이', 'WiFi multiplayer'), rows, '', '')

    def build_lobby(self):
        ses = self.session
        st = ses.settings
        if ses.state == 'connecting':
            rows = [self.I(T('연결 중… ', 'Connecting… ') + ses.address), self.R(T('취소', 'Cancel'), lambda: (ses.leave(), self.go('multi')), id='cancel')]
            self.menu.set(T('로비', 'Lobby'), rows, '', '')
            self.menu.clear_extra()
            return
        rows = [self.I('%s %d/%d' % (T('플레이어', 'Players'), len(ses.players), RoomServer.MAX_PLAYERS), (1, 0.86, 0.47, 1), 0.055)]
        for p in ses.players[:8]:
            rows.append(self.I(('* ' if p['id'] == ses.host_id else '  ') + p['name'] + ('  (YOU)' if p['id'] == ses.my_id else ''), (1, 0.72, 0.15, 1) if p['id'] == ses.my_id else None, 0.05))
        info = map_info(st['map'])
        mname = info['name'] if LANG == 'ko' else info['name_en']
        if ses.is_host:
            def mp(d):
                def f(m=1):
                    ses.send_settings(map=wrap_map(int(st['map']) + d * m))
                return f

            def lp(d):
                def f(m=1):
                    ses.send_settings(laps=int(clamp(int(st['laps']) + d, 1, 10)))
                return f

            def bp(d):
                def f(m=1):
                    ses.send_settings(bots=int(clamp(int(st['bots']) + d, 0, 11)))
                return f
            rows += [self.R('%s  < #%d >' % (T('맵', 'Map'), st['map']), None, mp(-1), mp(1), id='map'),
                     self.R('%s  < %d >' % (T('바퀴 수', 'Laps'), st['laps']), None, lp(-1), lp(1), id='laps'),
                     self.R('%s  < %d >' % (T('AI 봇', 'Bots'), st['bots']), None, bp(-1), bp(1), id='bots'),
                     self.R(T('레이스 시작!', 'START RACE!'), ses.start_race, kind='primary', id='start')]
            ips = local_ips()
            rows.append(self.I(T('친구에게 알려주세요: ', 'Tell your friends: ') + (ips[0] if ips else '?') + ':%d' % self.profile['port'], (1, 0.86, 0.47, 1)))
        else:
            rows.append(self.I('%s #%d   %s %d   %s %d' % (T('맵', 'Map'), st['map'], T('바퀴', 'Laps'), st['laps'], T('봇', 'Bots'), st['bots'])))
            rows.append(self.I(T('방장이 시작하기를 기다리는 중…', 'Waiting for the host…')))
        rows.append(self.R(T('나가기', 'Leave'), lambda: self.back(), id='leave'))
        self.menu.set(T('로비', 'Lobby'), rows, mname, T('←→ 값 변경 (Shift ±10, Ctrl ±100)', 'Left/Right change (Shift ±10, Ctrl ±100)'))
        key = (st['map'])
        if getattr(self, '_lobby_map', None) != key or not self.menu.extra.getChildren():
            self.draw_outline(int(st['map']))
            self._lobby_map = key

    # ------------------------------------------------------------------ 레이스
    def start_solo(self):
        p = self.profile
        entries = solo_entries(p.display_name(), p['kart'], int(p['bots']))
        self.start_race(int(p['map']), int(p['laps']), entries, False, True, 5.0)

    def start_race(self, map_id, laps, entries, multi, is_host, countdown):
        self.menu.show(False)
        self.menu.clear_extra()
        self.loading(T('맵 생성 중… #%d' % map_id, 'Building map… #%d' % map_id))
        self.destroy_world()
        self.race = Race(map_id, laps, entries, multi=multi, is_host=is_host, countdown=countdown, net=self.session.net if multi else None)
        self.world = World(self, self.race.track)
        self.world_map = None
        self.nodes = {rc.id: KartNode(self, rc, self.world.root) for rc in self.race.racers}
        self.particles = Particles(self)
        wk = self.race.track.theme.get('weather')
        self.weather = Weather(self, wk) if wk else None
        self.hud.build_minimap(self.race.track)
        nm = self.race.track.info['name' if LANG == 'ko' else 'name_en']
        self.hud.mapname.setText('#%d %s' % (map_id, nm))
        self.hud.show(True)
        self.chase = ChaseCam()
        self.steer = 0.0
        self.paused = False
        self.finish_at = None
        self.audio.silence()
        self.scene = 'race'
        self.loading_done()

    def toggle_pause(self):
        if self.race is None or self.scene == 'results':
            return
        self.paused = not self.paused
        if self.paused:
            self.audio.silence()
            rows = [self.R(T('계속하기', 'Resume'), self.toggle_pause, kind='primary', id='resume')]
            if not self.race.multi:
                rows.append(self.R(T('다시 시작', 'Restart'), lambda: (setattr(self, 'paused', False), self.start_solo()), id='restart'))
            rows.append(self.R(T('나가기', 'Quit'), self.leave_race, id='quit'))
            self.menu.show(True)
            self.menu.set(T('일시정지', 'Paused'), rows, '', '')
        else:
            self.menu.show(False)

    def leave_race(self):
        multi = self.race is not None and self.race.multi
        self.race = None
        self.paused = False
        self.audio.silence()
        self.destroy_world()
        if multi:
            self.session.leave()
        self.go('menu')

    def read_input(self, dt):
        k = self.keys
        left = 'arrow_left' in k or 'a' in k
        right = 'arrow_right' in k or 'd' in k
        tgt = (1.0 if right else 0.0) - (1.0 if left else 0.0)
        thr = 1.0 if ('arrow_up' in k or 'w' in k) else 0.0
        brk = 1.0 if ('arrow_down' in k or 's' in k) else 0.0
        drift = 'space' in k or 'lshift' in k or 'rshift' in k
        pad = self.pad
        if pad is not None:
            try:
                ax = pad.findAxis(InputDevice.Axis.left_x).value
                if abs(ax) > 0.12:
                    tgt = ax
                thr = max(thr, pad.findAxis(InputDevice.Axis.right_trigger).value)
                brk = max(brk, pad.findAxis(InputDevice.Axis.left_trigger).value)
                from panda3d.core import GamepadButton
                drift = drift or pad.findButton(GamepadButton.face_a()).pressed or pad.findButton(GamepadButton.rshoulder()).pressed
            except Exception:
                pass
        rate = 7.0 if tgt == 0 else 5.5
        self.steer += (tgt - self.steer) * min(1.0, dt * rate)
        return {'steer': self.steer, 'throttle': thr, 'brake': brk, 'drift': drift}

    def handle_events(self, race):
        for ev in race.events:
            kind = ev[0]
            if kind == 'count':
                if ev[1] <= 3:
                    self.audio.play('count')
            elif kind == 'go':
                self.audio.play('go')
                self.hud.say('GO!', 1.0, True)
            elif kind == 'lap':
                self.hud.say('FINAL LAP!' if ev[2] else 'LAP %d' % ev[1], 1.6)
                self.audio.play('lap')
            elif kind == 'finish':
                self.hud.say('FINISH!', 3.0, True)
                self.audio.play('finish')
                self.finish_at = time.time()
            elif kind == 'fin':
                self.hud.say(T('%s 결승!' % ev[1], '%s finished!' % ev[1]), 1.4, False, (0.8, 0.9, 1, 1))
            elif kind == 'left':
                self.hud.say(T('%s 퇴장' % ev[1], '%s left' % ev[1]), 1.4, False, (1, 0.6, 0.6, 1))
            elif kind == 'sim':
                e = ev[1]
                if e in ('pad', 'miniturbo'):
                    self.audio.play('boost')
                    if e == 'pad':
                        self.hud.say('BOOST!', 0.7, False, (0.3, 0.9, 1, 1))
                elif e in ('wall', 'bump'):
                    self.audio.play('bump')
                    self.shake = max(self.shake, 0.6)
                elif e.startswith('tier'):
                    self.audio.play('tier')

    def emit_fx(self, race, dt):
        pa = self.particles
        if pa is None:
            return
        th = race.track.theme
        gc = hex_rgb(th['ground'][0])
        loc = race.local
        for rc in race.racers:
            if rc.speed < 4 or abs(rc.x - loc.x) + abs(rc.z - loc.z) > 90:
                continue
            node = self.nodes.get(rc.id)
            if node is None:
                continue
            m = node.model
            fx, fz = math.sin(rc.h), math.cos(rc.h)
            rx, rz = -fz, fx
            L, W = m.L, m.W
            if rc.drifting:
                col = [(0.67, 0.8, 1), (0.23, 0.67, 1), (1, 0.63, 0.16), (0.82, 0.31, 1)][min(3, rc.tier)]
                for s_ in (-1, 1):
                    if _random.random() < 0.8:
                        pa.emit(PV(rc.x - fx * L * 0.4 + rx * s_ * W * 0.5, rc.y + 0.25, rc.z - fz * L * 0.4 + rz * s_ * W * 0.5),
                                PV((_random.random() - 0.5) * 5 - fx * 3, 2 + _random.random() * 4, (_random.random() - 0.5) * 5 - fz * 3), col, 0.35, 0.4 + _random.random() * 0.25)
            if rc.boosting and _random.random() < 0.9:
                pa.emit(PV(rc.x - fx * (L * 0.5 + 0.6), rc.y + 0.6, rc.z - fz * (L * 0.5 + 0.6)),
                        PV(-fx * 9 + (_random.random() - 0.5) * 2, _random.random() * 2, -fz * 9 + (_random.random() - 0.5) * 2), (1, 0.6, 0.15), 0.6, 0.3)
            if rc.offroad and _random.random() < 0.5:
                pa.emit(PV(rc.x - fx * 1.2 + (_random.random() - 0.5) * 2, rc.y + 0.2, rc.z - fz * 1.2 + (_random.random() - 0.5) * 2),
                        PV((_random.random() - 0.5) * 3, 1 + _random.random() * 2, (_random.random() - 0.5) * 3), (gc[0] / 255.0, gc[1] / 255.0, gc[2] / 255.0), 0.9, 0.5)
            if rc.wall_hit > 0.6:
                side = 1.0 if (race.track.rx[rc.idx % race.track.N] * rx + race.track.rz[rc.idx % race.track.N] * rz) > 0 else -1.0
                for _ in range(2):
                    pa.emit(PV(rc.x + rx * side * 1.3, rc.y + 0.6, rc.z + rz * side * 1.3), PV((_random.random() - 0.5) * 8, 2 + _random.random() * 5, (_random.random() - 0.5) * 8), (1, 0.85, 0.35), 0.3, 0.4)

    def update_race(self, dt):
        race = self.race
        inp = self.read_input(dt)
        if race.multi:
            for m in self.session.pump():
                if m.get('t') == 'tolobby':
                    self.leave_to_lobby()
                    return
                race.handle_message(m)
            if self.session.state == 'idle':
                err = self.session.error
                self.race = None
                self.destroy_world()
                self.go('menu')
                self.err = err
                self.build_main()
                return
        if not self.paused or race.multi:
            race.update(dt, inp)
            self.handle_events(race)
            self.emit_fx(race, dt)
        loc = race.local
        sim = loc.sim
        # 카트 노드 동기화
        alive = set()
        for rc in race.racers:
            alive.add(rc.id)
            node = self.nodes.get(rc.id)
            if node is None:
                node = self.nodes[rc.id] = KartNode(self, rc, self.world.root)
            node.update(rc, dt, race.track.ds, math.hypot(rc.x - loc.x, rc.z - loc.z))
        for rid in [r for r in self.nodes if r not in alive]:
            self.nodes.pop(rid).destroy()
        # 카메라
        cp = self.chase.update(dt, loc, sim.stats['max_speed'])
        self.shake = max(0.0, self.shake - dt * 2.2)
        sh = self.shake * 0.25 + (0.05 if loc.boosting else 0.0)
        pos = PV(cp[0] + (_random.random() - 0.5) * sh, cp[1] + (_random.random() - 0.5) * sh, cp[2] + (_random.random() - 0.5) * sh)
        yaw, pitch = cp[3], cp[4]
        d = PV(math.sin(yaw) * math.cos(pitch), -math.sin(pitch), math.cos(yaw) * math.cos(pitch))
        self.camera.setPos(*pos)
        self.camera.lookAt(Point3(pos[0] + d[0] * 20, pos[1] + d[1] * 20, pos[2] + d[2] * 20), Vec3(0, 0, 1))
        ratio = loc.speed / sim.stats['max_speed']
        self.camLens.setFov(84 + clamp(ratio, 0, 1.2) * 14 + (10 if loc.boosting else 0))
        self.world.update(pos)
        if self.particles is not None:
            self.particles.update(dt if not self.paused else 0.0)
        if self.weather is not None:
            self.weather.update(dt, pos)
        self.hud.update(race, time.time())
        self.hud.fps.setText(('%d fps' % int(1.0 / max(dt, 1e-3))) if self.show_fps else '')
        if not self.paused:
            self.audio.engine(ratio, 1.0 if inp['throttle'] > 0 else 0.2, loc.drifting, loc.offroad)
        # 결과 화면
        if self.scene == 'race' and race.local_finished() and self.finish_at and time.time() - self.finish_at > 2.4:
            self.scene = 'results'
            self.build_results()
        elif self.scene == 'results':
            self._res_t = getattr(self, '_res_t', 0.0) + dt
            if self._res_t > 0.5:
                self._res_t = 0.0
                self.build_results()

    def build_results(self):
        race = self.race
        rows = []
        for i, rc in enumerate(race.ranking()):
            me = rc is race.local
            rows.append(self.I('%2d  %-14s %s' % (i + 1, rc.name, fmt_time(rc.finish_time) if rc.finished else T('주행 중…', 'racing…')), (1, 0.72, 0.15, 1) if me else (0.95, 0.97, 1, 1), 0.052))
        if race.multi:
            if self.session.is_host:
                rows.append(self.R(T('로비로 돌아가기', 'Back to lobby'), self.session.back_to_lobby, kind='primary', id='lobby'))
            else:
                rows.append(self.I(T('방장을 기다리는 중…', 'Waiting for the host…')))
        else:
            rows.append(self.R(T('다시 달리기', 'Race again'), self.start_solo, kind='primary', id='again'))
        rows.append(self.R(T('메뉴로', 'Menu'), self.leave_race, id='menu'))
        self.menu.show(True)
        self.menu.set(T('결과', 'Results'), rows, '', '')

    def leave_to_lobby(self):
        self.race = None
        self.paused = False
        self.audio.silence()
        self.destroy_world()
        self.go('lobby')

    # ------------------------------------------------------------------ 메인 틱
    def tick(self, task):
        dt = self.dt_override if self.dt_override is not None else min(ClockObject.getGlobalClock().getDt(), 0.1)
        self.t += dt
        self.input.tick(dt)
        sc = self.scene
        if sc in ('multi',) and self.scan.get('done'):
            self.scan['done'] = False
            self.build_multi()
        if sc in ('lobby', 'multi', 'menu', 'solo', 'garage', 'settings') or (sc == 'race' and self.race is None):
            if self.session.net is not None and sc == 'lobby':
                self.session.pump()
                if self.session.start_msg is not None:
                    msg = self.session.start_msg
                    self.session.start_msg = None
                    entries = self.session.entries_from_start(msg)
                    self.start_race(int(msg['map']), int(msg['laps']), entries, True, self.session.is_host, float(msg.get('countdown', 5.0)))
                    return task.cont
                if self.session.state == 'idle':
                    self.err = self.session.error or T('연결 실패', 'Connection failed')
                    self.go('multi')
                    self.build_multi()
                    return task.cont
                sig = (self.session.state, tuple((p['id'], p['name']) for p in self.session.players), self.session.host_id, tuple(sorted(self.session.settings.items())))
                if sig != getattr(self, '_lobby_sig', None):
                    self._lobby_sig = sig
                    self.build_lobby()
            self.update_showroom(dt)
        elif sc in ('race', 'results') and self.race is not None:
            self.update_race(dt)
        return task.cont



# ============================================================================
#  [PC] 진입점
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
        elif a == '--fullscreen':
            args['fullscreen'] = True
        elif a == '--offscreen':
            args['offscreen'] = True
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
    game = None
    try:
        args = parse_args(sys.argv)
        if args.get('serve'):
            serve_forever(args.get('port', DEFAULT_PORT))
            return
        game = Game(args)
        game.run()
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
    finally:
        try:
            if game is not None:
                game.profile.save()
                game.session.leave()
        except Exception:
            pass


if __name__ == '__main__':
    main()
