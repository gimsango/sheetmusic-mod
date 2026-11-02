#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
  TURBO KART 3D  -  폰 버전 (Pydroid 3)            [ kart3d_phone.py ]
==========================================================================
  * 맵 1000개 / 카트 100,000종 / 아이템전(아이템 100종) / WiFi(LAN) 멀티플레이 / 터치 조작
  * 아이템: 화면 위 아이템 칸 3개를 터치 (키보드는 1·2·3, ↓ 누른 채 쓰면 뒤로 던지기)
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


def _other_pythons():
    """설치된 다른 파이썬(3.10~3.14) 찾기 -> [(버전, 경로), ...] (선호 순서). 윈도우 'py' 런처와 PATH 를 이용."""
    import re
    import shutil
    pref = ['3.13', '3.12', '3.14', '3.11', '3.10']
    cur = os.path.normcase(os.path.abspath(sys.executable or ''))
    cands = []

    def add(p):
        try:
            p = os.path.abspath(p)
            if os.path.isfile(p) and os.path.normcase(p) != cur and p not in cands:
                cands.append(p)
        except Exception:
            pass

    def run(cmd):
        return subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True, timeout=25)
    try:
        r = run(['py', '-0p'])
        for m in re.finditer(r'[A-Za-z]:\\[^\r\n"]*?python\.exe', r.stdout or '', re.I):
            add(m.group(0))
    except Exception:
        pass
    for v in pref:
        w = shutil.which('python' + v)
        if w:
            add(w)
    if not cands:
        for v in pref:
            try:
                r = run(['py', '-' + v, '-c', 'import sys;print(sys.executable)'])
                if r.returncode == 0 and r.stdout.strip():
                    add(r.stdout.strip().splitlines()[-1])
            except Exception:
                pass
    out = []
    for p in cands:
        try:
            r = run([p, '-c', 'import sys;print("%d.%d" % sys.version_info[:2])'])
            v = r.stdout.strip()
            if r.returncode == 0 and v in pref:
                out.append((pref.index(v), v, p))
        except Exception:
            pass
    out.sort()
    return [(v, p) for _, v, p in out]


def _relaunch_with_other_python(imp, cands, install):
    """다른 파이썬이 이미 해당 패키지를 갖고 있으면(또는 install=True 면 설치해서) 그 파이썬으로 게임을 다시 시작한다."""
    if os.environ.get('KART3D_RELAUNCHED'):
        return False                      # 이미 한 번 재시작했으면 무한 반복 방지
    for v, exe2 in _other_pythons():
        ok = subprocess.call([exe2, '-c', 'import ' + imp], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        if not ok and install:
            for c in cands:
                print('>> Python %s 에 설치 시도 / installing into Python %s: %s' % (v, v, c))
                if subprocess.call([exe2, '-m', 'pip', 'install', '--only-binary=:all:', c]) == 0:
                    ok = True
                    break
        if ok:
            print('>> Python %s 로 게임을 시작합니다...  /  Restarting with Python %s' % (v, v))
            os.environ['KART3D_RELAUNCHED'] = '1'
            raise SystemExit(subprocess.call([exe2] + sys.argv))
    return False


def _ensure_pkg(pkg, alt_hint='', candidates=None, err=None):
    """필요한 패키지가 없을 때: 올바른 설치 명령을 보여주고, 동의하면 같은 파이썬으로 설치(미리 빌드된 것만)한 뒤 게임을 다시 시작한다."""
    exe = sys.executable or 'python'
    vi = sys.version_info
    ver = '%d.%d' % (vi[0], vi[1])
    cands = list(candidates or [pkg])
    imp = 'pygame' if pkg.startswith('pygame') else pkg
    if not _is_android():
        try:
            _relaunch_with_other_python(imp, cands, False)      # 다른 파이썬에 이미 설치돼 있으면 조용히 그걸로 실행
        except OSError:
            pass
    print('=' * 64)
    print('%s 패키지가 필요합니다  /  "%s" is required.   (Python %s)' % (pkg, pkg, ver))
    if err:
        print('(불러오기 오류 / import error: %s)' % err)
    if os.environ.get('KART3D_RELAUNCHED'):
        print('이미 한 번 설치/재시작을 했는데도 불러오지 못했습니다. 위의 오류 문구를 알려주세요.  /  Already retried once; please send the error text above.')
        print('=' * 64)
        _wait_key()
        return
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
                os.environ['KART3D_RELAUNCHED'] = '1'
                raise SystemExit(subprocess.call([exe] + sys.argv))
        print()
        print('이 파이썬(%s)에는 설치할 수 없었습니다.  /  Could not install into this Python.' % ver)
        print('>> 설치된 다른 파이썬을 찾는 중...  /  Looking for another Python...')
        try:
            _relaunch_with_other_python(imp, cands, True)
        except OSError:
            pass
        print('설치에 실패했습니다.  /  Install failed.')
        if vi >= (3, 14):
            script = os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else 'kart3d.py'
            qs = '"%s"' % script if (' ' in script or '(' in script) else script
            print('가장 흔한 원인: 파이썬 %s 은(는) 너무 새로워서 이 패키지의 설치 파일이 아직 없습니다.' % ver)
            print('  -> 해결: Python 3.13 을 추가로 설치하세요 (지금 파이썬은 그대로 둬도 됩니다). 새 명령 창에서 차례로:')
            print('       py install 3.13')
            print('       (위 명령이 안 되면 https://www.python.org/downloads/ 에서 3.13 설치, "Add python.exe to PATH" 체크)')
            print('       py -3.13 -m pip install %s' % cands[0])
            print('       py -3.13 %s' % qs)
            if qs != script:
                print('  (파일 이름에 공백/괄호가 있어서 따옴표로 감쌌습니다. 파일 이름을 kart3d.py 처럼 짧게 바꾸면 더 편해요)')
        else:
            print('위의 오류 문구를 그대로 알려주세요.  /  Please send the error text above.')
            print('(리눅스 "externally-managed-environment" 오류: python3 -m venv venv 로 가상환경을 만든 뒤 그 안에서 설치하세요)')
    print('=' * 64)
    _wait_key()

try:
    import pygame
except ImportError as _e:
    # 3.14+ 는 pygame 설치 파일이 없어서 호환 버전(pygame-ce)을 먼저 시도
    _ensure_pkg('pygame', candidates=(['pygame-ce', 'pygame'] if sys.version_info >= (3, 14) else ['pygame', 'pygame-ce']), err=str(_e))
    raise SystemExit(1)

# -*- coding: utf-8 -*-
# ============================================================================
#  TURBO KART 3D (Python)  -  공통 코어
#  맵 1000개 / 카트 100,000종 / 아이템 100종 / 아케이드 물리 / AI / WiFi(LAN) 멀티플레이
# ============================================================================
import math
import json
import socket
import threading
import time
import os
import sys
import queue

VERSION = '1.1'
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
                max_speed=52 + speed * 3.0, accel_rate=15 + accel * 1.7, turn_rate=1.62 + handling * 0.12, drift_grip=4.2 - drift * 0.18)


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
#  아케이드 카트 물리 + AI  (+ 아이템전 상태이상: 스핀/날아감/축소/감속/미끄럼/빙결/무적/방패/유령/거대화/로켓…)
# ----------------------------------------------------------------------------
DRIFT_BOOST = (0.0, 0.7, 1.2, 1.9)
STEER_RATES = ((6.0, 8.0), (10.0, 13.0), (16.0, 20.0))    # 조향 반응 설정별 (누를 때, 뗄 때) 속도
NO_INPUT = {'steer': 0.0, 'throttle': 0.0, 'brake': 0.0, 'drift': False}

# 다른 기기에 보내는 상태 비트 (원격 카트 표시용)
FX_SPIN, FX_AIR, FX_SHRINK, FX_STAR, FX_SHIELD, FX_GHOST, FX_GIANT, FX_FREEZE, FX_AUTO, FX_HOP, FX_SLIDE, FX_MAGNET = (
    1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048)
FX_RAM = FX_STAR | FX_GIANT | FX_AUTO          # 부딪히면 상대를 날려버리는 상태


def steer_step(cur, tgt, dt, resp=1):
    """키보드/버튼 같은 켜고 끄는 입력을 부드럽게 -1..1 로 만든다. 반대 방향으로 급히 바꿀 때는 더 빠르게."""
    up, down = STEER_RATES[int(clamp(resp, 0, 2))]
    rate = down if tgt == 0 else up
    if tgt * cur < 0:
        rate = max(rate, down) * 1.3
    return cur + (tgt - cur) * min(1.0, dt * rate)


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
        self.fx_reset()

    # ---- 아이템 상태이상 ------------------------------------------------------------
    def fx_reset(self):
        self.spin_t = self.air_t = self.air_dur = 0.0
        self.shrink_t = self.slow_t = self.slide_t = self.freeze_t = self.stun_t = self.rev_t = self.blind_t = 0.0
        self.star_t = self.shield_t = self.ghost_t = self.giant_t = self.auto_t = self.grip_t = 0.0
        self.magnet_t = self.engine_t = self.hop_t = self.hop_dur = self.immune_t = self.ram_cool = 0.0
        self.shield_n = 0
        self.slow_k = 1.0
        self.engine_cap = 0.0
        self.engine_acc = 1.0
        self.auto_spd = 1.4
        self.magnet_range = 80.0
        self.boost_pow = 1.0
        self.coins = 0
        self.spin_ang = 0.0
        self.air_y = 0.0
        self.pull = None
        self.fx_time = 0.0

    def cure(self):
        """나쁜 상태이상 모두 해제"""
        self.spin_t = self.air_t = self.shrink_t = self.slow_t = self.slide_t = 0.0
        self.freeze_t = self.stun_t = self.rev_t = self.blind_t = 0.0
        self.slow_k = 1.0
        self.spin_ang = 0.0
        self.air_y = 0.0

    def debuffed(self):
        return (self.spin_t > 0 or self.shrink_t > 0 or self.slow_t > 0 or self.slide_t > 0 or self.freeze_t > 0
                or self.stun_t > 0 or self.rev_t > 0 or self.blind_t > 0)

    def invulnerable(self):
        return self.star_t > 0 or self.auto_t > 0 or self.ghost_t > 0 or self.immune_t > 0

    def hit(self, fx, dur=0.0, k=0.0):
        """공격 받기 -> 'ok' (맞음) / 'block' (방패로 막음) / 'immune' (무적/점프 등으로 무시)"""
        if self.finished or self.invulnerable():
            return 'immune'
        if self.giant_t > 0 and fx in ('spin', 'slide', 'slow', 'bump', 'flat', 'shrink', 'warpback'):
            return 'immune'
        if self.hop_t > 0 and fx in ('slide', 'slow'):          # 점프 중에는 바닥 함정이 안 통한다
            return 'immune'
        if self.shield_n > 0:
            self.shield_n -= 1
            if self.shield_n <= 0:
                self.shield_t = 0.0
            self.immune_t = max(self.immune_t, 0.5)
            return 'block'
        if fx in ('spin', 'launch', 'freeze', 'bump', 'flat'):
            self.drifting = False
            self.drift_charge = 0.0
            self.drift_tier = 0
            self.boost_t = 0.0
        if fx == 'spin':
            self.spin_t = max(self.spin_t, dur or 1.1)
        elif fx == 'launch':
            self.air_t = self.air_dur = dur or 1.25
            self.spin_t = max(self.spin_t, self.air_t + 0.25)
        elif fx == 'shrink':
            self.shrink_t = max(self.shrink_t, dur or 6.0)
            self.spin_t = max(self.spin_t, 0.5)
            self.giant_t = 0.0
        elif fx == 'flat':
            self.shrink_t = max(self.shrink_t, dur or 3.5)
            self.slow_t = max(self.slow_t, dur or 3.5)
            self.slow_k = 0.7
            self.spin_t = max(self.spin_t, 0.6)
        elif fx == 'slow':
            kk = clamp(k or 0.6, 0.2, 1.0)
            self.slow_k = min(self.slow_k, kk) if self.slow_t > 0 else kk
            self.slow_t = max(self.slow_t, dur or 3.0)
        elif fx == 'slide':
            self.slide_t = max(self.slide_t, dur or 2.0)
        elif fx == 'freeze':
            self.freeze_t = max(self.freeze_t, dur or 1.5)
        elif fx == 'stun':
            self.stun_t = max(self.stun_t, dur or 2.0)
        elif fx == 'reverse':
            self.rev_t = max(self.rev_t, dur or 4.0)
        elif fx == 'blind':
            self.blind_t = max(self.blind_t, dur or 4.0)
        elif fx == 'bump':
            self.vx *= 0.3
            self.vz *= 0.3
            self.speed = math.hypot(self.vx, self.vz)
            self.wall_hit = 1.0
            self.spin_t = max(self.spin_t, 0.4)
        return 'ok'

    def fx_bits(self):
        b = 0
        if self.spin_t > 0:
            b |= FX_SPIN
        if self.air_t > 0:
            b |= FX_AIR
        if self.shrink_t > 0:
            b |= FX_SHRINK
        if self.star_t > 0:
            b |= FX_STAR
        if self.shield_n > 0:
            b |= FX_SHIELD
        if self.ghost_t > 0:
            b |= FX_GHOST
        if self.giant_t > 0:
            b |= FX_GIANT
        if self.freeze_t > 0:
            b |= FX_FREEZE
        if self.auto_t > 0:
            b |= FX_AUTO
        if self.hop_t > 0:
            b |= FX_HOP
        if self.slide_t > 0:
            b |= FX_SLIDE
        if self.magnet_t > 0:
            b |= FX_MAGNET
        return b

    def _tick_fx(self, dt):
        self.fx_time += dt
        if self.spin_t > 0:
            self.spin_t -= dt
            self.spin_ang += dt * 14.0
            if self.spin_t <= 0:
                self.spin_t = 0.0
                self.spin_ang = 0.0
        if self.air_t > 0:
            self.air_t -= dt
            f = 1.0 - max(0.0, self.air_t) / max(self.air_dur, 0.05)
            self.air_y = math.sin(math.pi * f) * 3.4
            if self.air_t <= 0:
                self.air_t = 0.0
                self.air_y = 0.0
        elif self.hop_t > 0:
            self.hop_t -= dt
            f = 1.0 - max(0.0, self.hop_t) / max(self.hop_dur, 0.05)
            self.air_y = math.sin(math.pi * f) * (1.2 + self.hop_dur * 0.9)
            if self.hop_t <= 0:
                self.hop_t = 0.0
                self.air_y = 0.0
        else:
            self.air_y = 0.0
        if self.shrink_t > 0:
            self.shrink_t = max(0.0, self.shrink_t - dt)
        if self.slow_t > 0:
            self.slow_t -= dt
            if self.slow_t <= 0:
                self.slow_t = 0.0
                self.slow_k = 1.0
        if self.slide_t > 0:
            self.slide_t = max(0.0, self.slide_t - dt)
        if self.freeze_t > 0:
            self.freeze_t = max(0.0, self.freeze_t - dt)
        if self.stun_t > 0:
            self.stun_t = max(0.0, self.stun_t - dt)
        if self.rev_t > 0:
            self.rev_t = max(0.0, self.rev_t - dt)
        if self.blind_t > 0:
            self.blind_t = max(0.0, self.blind_t - dt)
        if self.star_t > 0:
            self.star_t = max(0.0, self.star_t - dt)
        if self.shield_t > 0:
            self.shield_t -= dt
            if self.shield_t <= 0:
                self.shield_t = 0.0
                self.shield_n = 0
        if self.ghost_t > 0:
            self.ghost_t = max(0.0, self.ghost_t - dt)
        if self.giant_t > 0:
            self.giant_t = max(0.0, self.giant_t - dt)
        if self.auto_t > 0:
            self.auto_t = max(0.0, self.auto_t - dt)
        if self.grip_t > 0:
            self.grip_t = max(0.0, self.grip_t - dt)
        if self.magnet_t > 0:
            self.magnet_t -= dt
            if self.magnet_t <= 0:
                self.magnet_t = 0.0
                self.pull = None
        if self.engine_t > 0:
            self.engine_t = max(0.0, self.engine_t - dt)
        if self.immune_t > 0:
            self.immune_t = max(0.0, self.immune_t - dt)
        if self.ram_cool > 0:
            self.ram_cool = max(0.0, self.ram_cool - dt)

    def _autopilot(self):
        """로켓 아이템: 트랙 중앙을 따라 자동으로 달린다"""
        t = self.track
        look = int(clamp((self.speed * 0.42 + 12.0) / t.ds, 5, 40))
        i = (self.q.idx + look) % t.N
        want = math.atan2(t.px[i] - self.x, t.pz[i] - self.z)
        return clamp(-wrap_pi(want - self.heading) * 2.6, -1.0, 1.0)

    def teleport(self, x, z, heading=None):
        """순간이동 (속력은 유지). 진행도는 다음 update 에서 자연스럽게 반영된다."""
        sp = max(0.0, self.vx * math.sin(self.heading) + self.vz * math.cos(self.heading))
        self.x, self.z = x, z
        if heading is not None:
            self.heading = heading
        self.vx = math.sin(self.heading) * sp
        self.vz = math.cos(self.heading) * sp
        self.track.query(x, z, -1, self.q)
        self.hint = self.q.idx
        self.y = self.q.y
        self.drifting = False
        self.drift_charge = 0.0
        self.drift_tier = 0

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
        self.cure()
        self.hop_t = 0.0
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
        self._tick_fx(dt)
        fx = sin(self.heading)
        fz = cos(self.heading)
        rx = -fz
        rz = fx
        vf = self.vx * fx + self.vz * fz
        vl = self.vx * rx + self.vz * rz
        # 입력 (상태이상이 있으면 바뀐다)
        lost = self.spin_t > 0 or self.air_t > 0 or self.freeze_t > 0
        if lost:
            thr, brk, steer, dbtn = 0.0, 0.0, 0.0, False
        elif self.auto_t > 0:
            thr, brk, steer, dbtn = 1.0, 0.0, self._autopilot(), False
        else:
            thr, brk, steer, dbtn = inp['throttle'], inp['brake'], inp['steer'], inp['drift']
            if self.rev_t > 0:
                steer = -steer
            if self.slide_t > 0:
                steer = clamp(steer + sin(self.fx_time * 7.0) * 0.55, -1.0, 1.0)
            if self.stun_t > 0:
                thr = 0.0
                dbtn = False
        boosting = self.boost_t > 0
        if boosting:
            self.boost_t -= dt
            if self.boost_t <= 0:
                self.boost_pow = 1.0
        maxs = s['max_speed']
        air = self.air_y > 0.3
        slow_off = self.offroad and not (self.grip_t > 0 or self.star_t > 0 or self.auto_t > 0 or air)
        cap = maxs * (0.55 if slow_off else 1.0) + (24.0 * self.boost_pow if boosting else 0.0) + self.coins * 0.55
        acc_k = 2.6 if boosting else 1.0
        if self.engine_t > 0:
            cap += self.engine_cap
            acc_k *= self.engine_acc
        if self.star_t > 0:
            cap += 14.0
            acc_k *= 1.6
        if self.giant_t > 0:
            cap += 5.0
        if self.magnet_t > 0 and self.pull is not None:
            cap += 9.0
        if self.shrink_t > 0:
            cap *= 0.72
            acc_k *= 0.8
        if self.slow_t > 0:
            cap *= self.slow_k
        if self.auto_t > 0:
            cap = max(cap, maxs * self.auto_spd)
            acc_k *= 3.0
        if thr > 0.01:
            if vf < cap:
                vf += s['accel_rate'] * acc_k * thr * (1 - 0.75 * max(0.0, vf) / cap) * dt
            else:
                vf -= 26 * dt
        if brk > 0.01:
            if vf > 1:
                vf -= 44 * brk * dt
            else:
                vf = max(-16.0, vf - 16 * brk * dt)
        elif thr < 0.01:
            vf -= sign(vf) * min(abs(vf), 7 * dt)
            if vf > cap + 1.0:
                vf -= 26 * dt
        vf *= exp(-(0.9 if slow_off else 0.04) * dt)
        if lost:
            if self.air_t > 0:
                vf *= exp(-0.8 * dt)
            elif self.freeze_t > 0:
                vf *= exp(-0.35 * dt)
            else:
                vf *= exp(-2.6 * dt)
        along = self.vx * q.tx + self.vz * q.tz
        vf -= 4.4 * q.ty * (1.0 if along >= 0 else -1.0) * dt     # 오르막은 느려지고 내리막은 빨라짐

        # 드리프트
        want = dbtn and abs(steer) > 0.25 and vf > 22 and not self.offroad
        if not dbtn:
            self.armed = True
        if not self.drifting and want and self.armed:
            self.armed = False
            self.drifting = True
            self.drift_dir = sign(steer)
            self.drift_charge = 0.0
            ev.append('driftStart')
        if self.drifting:
            if (not dbtn) or vf < 16:
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

        # 조향 (고속에서도 너무 둔해지지 않게)
        turn = s['turn_rate'] * (1.2 if self.grip_t > 0 else 1.0) * (0.9 if self.giant_t > 0 else 1.0)
        speed_f = clamp(abs(vf) / 14.0, 0.0, 1.0) * (1 - 0.22 * clamp(abs(vf) / maxs, 0.0, 1.0))
        if self.drifting:
            yaw = turn * (0.55 * self.drift_dir + 0.6 * steer * (0.75 if steer * self.drift_dir > 0 else 1.0)) * 1.15
        else:
            yaw = turn * steer
        self.heading -= yaw * speed_f * (1.0 if vf >= 0 else -1.0) * dt
        self.steer_vis += (steer - self.steer_vis) * min(1.0, dt * 12)
        grip = s['drift_grip'] if self.drifting else (9.5 if boosting else 12.0)
        if self.freeze_t > 0:
            grip = 0.5
        elif self.slide_t > 0:
            grip *= 0.22
        elif self.grip_t > 0:
            grip *= 1.25
        vl *= exp(-grip * dt)
        self.slip = vl
        nfx = sin(self.heading)
        nfz = cos(self.heading)
        self.vx = nfx * vf + (-nfz) * vl
        self.vz = nfz * vf + nfx * vl
        self.x += self.vx * dt
        self.z += self.vz * dt
        if self.magnet_t > 0 and self.pull is not None:
            self.x += self.pull[0] * 7.0 * dt
            self.z += self.pull[1] * 7.0 * dt

        # 다른 카트와 충돌 (원) - 유령 상태면 통과
        if self.ghost_t <= 0:
            rad = 2.5 * (1.5 if self.giant_t > 0 else (0.7 if self.shrink_t > 0 else 1.0))
            for o in others:
                dx = self.x - o[0]
                dz = self.z - o[1]
                dist = math.hypot(dx, dz)
                if 0.001 < dist < rad:
                    push = (rad - dist) / dist * (0.25 if self.giant_t > 0 else 0.55)
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
        elif t.pads and not air:
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
        self.react = 0.5 + rand() * 1.2       # 아이템을 받고 쓰기까지 머뭇거리는 시간

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
        if kart.blind_t > 0:                       # 시야가 가려지면 비틀거림
            steer = clamp(steer + math.sin(self.t * 2.3 + self.phase) * 0.5, -1.0, 1.0)
        rb = 1.0
        if rubber and player_total is not None:
            gap = (kart.total - player_total) * tr.ds
            rb = clamp(1 - gap / 900.0, 0.9, 1.08)
        curve = tr.turn[q.idx]
        target = kart.stats['max_speed'] * self.skill * rb * (1 - clamp(curve * 0.55 - 0.08, 0.0, 0.5))
        sp = kart.speed
        if kart.boost_t > 0 or kart.star_t > 0 or kart.engine_t > 0 or kart.auto_t > 0:
            target += 30.0                          # 가속 아이템을 쓰는 중이면 감속하지 않음
        inp = {'steer': steer, 'throttle': 1.0 if sp < target else 0.15, 'brake': 0.7 if sp > target + 7 else 0.0, 'drift': False}
        if curve > 0.55 and sp > 36 and self.skill > 0.9 and abs(steer) > 0.45:
            inp['drift'] = True
        if sp < 2 and kart.spin_t <= 0 and kart.freeze_t <= 0 and kart.air_t <= 0:
            self.stuck += dt
            if self.stuck > 2.5:
                kart.respawn()
                self.stuck = 0.0
        else:
            self.stuck = 0.0
        return inp


# ----------------------------------------------------------------------------
#  레이스 진행 (솔로/멀티 공통): 카운트다운, 시뮬레이션, 순위, 아이템전, 네트워크 동기화
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
        # ---- 아이템전 ----
        self.items = [None, None, None]     # 슬롯 3칸 (키 1/2/3)
        self.uses = [0, 0, 0]
        self.roll = [0.0, 0.0, 0.0]         # 룰렛 남은 시간
        self.hold = [0.0, 0.0, 0.0]         # 봇: 들고 있던 시간
        self.fx = 0                         # 상태 비트 (FX_*)
        self.spin_ang = 0.0
        self.air_y = 0.0
        self.scale = 1.0

    def sync_visual(self, track, dt):
        s = self.sim
        k = min(1.0, dt * 7.0)
        if s is not None:
            self.x, self.y, self.z, self.h = s.x, s.y, s.z, s.heading
            self.speed = s.speed
            self.total = s.total
            self.vx, self.vz = s.vx, s.vz
            self.drifting = s.drifting
            self.tier = s.drift_tier
            self.drift_dir = s.drift_dir
            self.boosting = s.boost_t > 0 or s.auto_t > 0
            self.steer = s.steer_vis
            self.slip = s.slip
            self.up = (s.upx, s.upy, s.upz)
            self.idx = s.q.idx
            self.offroad = s.offroad
            self.wall_hit = s.wall_hit
            self.fx = s.fx_bits()
            self.spin_ang = s.spin_ang
            self.air_y = s.air_y
            ts = 0.55 if s.shrink_t > 0 else (1.6 if s.giant_t > 0 else 1.0)
            self.scale += (ts - self.scale) * k
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
        fx = int(t.get('fx', 0) or 0)
        self.fx = fx
        self.boosting = t['bo'] > 0 or bool(fx & FX_AUTO)
        self.steer = clamp(-dh * 2.0, -1.0, 1.0)
        if self.drifting:
            self.drift_dir = sign(self.steer) or self.drift_dir
        self.slip = 0.0
        self.idx = int(round(self.total)) % track.N
        self.up = track.surface_normal(self.idx)
        self.spin_ang = (self.spin_ang + dt * 14.0) if fx & FX_SPIN else 0.0
        ta = 3.0 if fx & FX_AIR else (1.4 if fx & FX_HOP else 0.0)
        self.air_y += (ta - self.air_y) * k
        ts = 0.55 if fx & FX_SHRINK else (1.6 if fx & FX_GIANT else 1.0)
        self.scale += (ts - self.scale) * k


class Race(object):
    def __init__(self, map_id, laps, entries, multi=False, is_host=True, countdown=5.0, net=None, auto_local=False, items=False):
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
                rc.tgt = dict(rc.cur, dr=0, bo=0, fx=0)
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
        self.events = []              # 지난 update 이후 일어난 일 (프론트엔드가 읽음)
        self._pend = []
        self.finish_order = []
        self.send_t = 0.0
        self.auto_local = auto_local
        self.count_left = countdown
        self.items = ItemSystem(self) if items else None

    def ev(self, e):
        self._pend.append(e)

    # ---- 진행 --------------------------------------------------------------
    def update(self, dt, inp):
        """프레임마다 호출. inp = {'steer','throttle','brake','drift'} (로컬 플레이어 입력)"""
        dt = min(dt, 0.1)
        if self.phase == 'count':
            left = self.start_at - time.monotonic()
            self.count_left = left
            if left <= 0:
                self.phase = 'run'
                self.t = 0.0
                self.ev(('go',))
            else:
                n = int(math.ceil(left))
                if n != self.last_count:
                    self.last_count = n
                    self.ev(('count', n))
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
        self.events, self._pend = self._pend, []

    def _step(self, dt, inp):
        running = self.phase == 'run'
        racers = self.racers
        N = self.track.N
        far = (1e9, 1e9, 0.0, 0.0)
        others_all = [far if (r.fx & FX_GHOST) else (r.x, r.z, r.vx, r.vz) for r in racers]
        items = self.items
        for k, rc in enumerate(racers):
            sim = rc.sim
            if sim is None:
                continue
            if not running:
                use = NO_INPUT
            elif rc.kind == 'local' and not rc.finished and not self.auto_local:
                use = inp
            else:
                if rc.brain is None:
                    rc.brain = BotBrain(Rng(5))
                loc = self.local
                use = rc.brain.drive(sim, dt, loc.total if loc is not None else None, not self.multi)
                if items is not None and running:
                    items.bot_think(rc, dt)
            if not running:
                sim.vx *= 0.9
                sim.vz *= 0.9
            others = others_all[:k] + others_all[k + 1:]
            sim.update(dt, use, others)
            # 다음 서브스텝/아이템 판정에서 쓸 위치 갱신
            if not (rc.fx & FX_GHOST):
                others_all[k] = (sim.x, sim.z, sim.vx, sim.vz)
            rc.x, rc.y, rc.z, rc.h, rc.idx = sim.x, sim.y, sim.z, sim.heading, sim.q.idx
            rc.vx, rc.vz, rc.speed, rc.air_y = sim.vx, sim.vz, sim.speed, sim.air_y
            rc.total = sim.total
            if running:
                if not rc.finished and sim.total >= self.laps * N:
                    rc.finished = True
                    rc.finish_time = self.t
                    sim.finished = True
                    self.finish_order.append(rc)
                    if rc.kind == 'local':
                        self.ev(('finish',))
                        if self.net is not None and self.multi:
                            self.net.send({'t': 'fin', 'time': round(rc.finish_time, 2)})
            if rc.kind == 'local':
                for e in sim.events:
                    self.ev(('sim', e))
                lap = min(self.laps, sim.lap)
                if lap > self.last_lap and running:
                    self.ev(('lap', lap, lap == self.laps))
                    self.last_lap = lap
        if items is not None:
            items.step(dt)
        if running:
            self.t += dt

    def respawn_local(self):
        if self.local is not None and self.local.sim is not None and self.phase == 'run':
            self.local.sim.respawn()

    def use_item(self, slot, back=False):
        """아이템전: 내 슬롯(0,1,2) 아이템 사용. back=True 면 (가능한 아이템은) 뒤로 던진다."""
        if self.items is None or self.local is None or self.auto_local:
            return False
        return self.items.use(self.local, slot, back)

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
                  'tp': round(s.total, 2), 'dr': (s.drift_tier + 1) if s.drifting else 0, 'bo': 1 if (s.boost_t > 0 or s.auto_t > 0) else 0,
                  'fx': s.fx_bits()})
        if self.is_host:
            bots = []
            for rc in self.racers:
                if rc.kind == 'bot':
                    b = rc.sim
                    bots.append([rc.id, round(b.x, 2), round(b.y, 2), round(b.z, 2), round(b.heading, 3), round(b.speed, 1), round(b.total, 2),
                                 (b.drift_tier + 1) if b.drifting else 0, 1 if (b.boost_t > 0 or b.auto_t > 0) else 0,
                                 round(rc.finish_time, 2) if rc.finished else 0, b.fx_bits()])
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
                rc.tgt.update(x=m['x'], y=m['y'], z=m['z'], h=m['h'], sp=m['sp'], total=m['tp'], dr=m['dr'], bo=m['bo'], fx=m.get('fx', 0))
        elif t == 'b':
            for a in m.get('b', []):
                rc = self._find(a[0])
                if rc is not None and rc.tgt is not None:
                    rc.tgt.update(x=a[1], y=a[2], z=a[3], h=a[4], sp=a[5], total=a[6], dr=a[7], bo=a[8], fx=a[10] if len(a) > 10 else 0)
                    if a[9] and not rc.finished:
                        rc.finished = True
                        rc.finish_time = a[9]
        elif t == 'fin':
            rc = self._find(m.get('id'))
            if rc is not None and not rc.finished:
                rc.finished = True
                rc.finish_time = float(m.get('time', self.t))
                self.ev(('fin', rc.name))
        elif t == 'left':
            rc = self._find(m.get('id'))
            if rc is not None:
                self.racers.remove(rc)
                self.ev(('left', rc.name))
        elif isinstance(t, str) and t[:1] == 'i' and self.items is not None:
            self.items.handle_message(m)


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
        self.items = True             # 아이템전 여부
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
            return {'t': 'room', 'host': self.host_id, 'map': self.map, 'laps': self.laps, 'bots': self.bots, 'items': self.items, 'state': self.state,
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
        if t in ('s', 'b', 'fin') or (isinstance(t, str) and t[:1] == 'i'):     # 'i*' = 아이템전 메시지
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
                if 'items' in m:
                    self.items = bool(m['items'])
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
                    msg = {'t': 'start', 'map': self.map, 'laps': self.laps, 'countdown': 5.0, 'players': order, 'bots': bots, 'items': self.items}
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
        self.settings = {'map': 1, 'laps': 3, 'bots': 0, 'items': True}
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
            self.server.items = self.profile['mode'] == 'item'
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
                self.settings = {'map': m.get('map', 1), 'laps': m.get('laps', 3), 'bots': m.get('bots', 0), 'items': bool(m.get('items', False))}
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
                'lang': 'auto', 'last_ip': '', 'port': DEFAULT_PORT, 'steer_mode': 'buttons', 'steer_resp': 1,
                'mode': 'item'}           # 'item' = 아이템전, 'speed' = 스피드전

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
        self.h += wrap_pi(target - self.h) * (1 - math.exp(-7.0 * dt))
        self.y += (rc.y - self.y) * (1 - math.exp(-9.0 * dt))
        dist = 8.3 + sr * 2.2 + (1.6 if rc.boosting else 0.0)
        hgt = 3.5 + sr * 0.4
        fx, fz = math.sin(self.h), math.cos(self.h)
        x, y, z = rc.x - fx * dist, self.y + hgt, rc.z - fz * dist
        lx, ly, lz = rc.x + fx * 8.0, self.y + 1.2, rc.z + fz * 8.0
        yaw = math.atan2(lx - x, lz - z)
        pitch = math.atan2(y - ly, math.hypot(lx - x, lz - z))
        return x, y, z, yaw, pitch


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
        self.frame_no = 0
        self.anim_t = 0.0
        self.qfont_path = None
        self.qcache = {}
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
        isys = getattr(race, 'items', None)
        if isys is not None:
            for b in isys.boxes:
                if b['t'] > 0.0:
                    continue
                o = ((b['idx'] - focus_idx) * dirn + half) % N - half
                sl_i = slot_map.get(o)
                if sl_i is not None:
                    dpb = self._dp_of(b['x'], b['y'], b['z'])
                    if dpb > 1.5:
                        items[sl_i].append((dpb, 6, b))
            for e in isys.ents:
                o = ((e.hint - focus_idx) * dirn + half) % N - half
                sl_i = slot_map.get(o)
                if sl_i is not None:
                    dpe = self._dp_of(e.x, e.y, e.z)
                    if dpe > 1.2:
                        items[sl_i].append((dpe + (0.0 if e.kind != 'trap' else 0.3), 7, e))

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
                        elif code == 5:
                            self._draw_arch(it[2])
                        elif code == 6:
                            self._draw_ibox(it[2], it[0])
                        else:
                            self._draw_ent(it[2], it[0])
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
    def draw_boxes(self, org, Rv, Uv, Fv, boxes, shade, lod_fog=0, scale=1.0, tint=None):
        """박스 목록을 (org, R/U/F 기저)에서 3D 로 그린다. 각 박스: 보이는 면만 칠함. scale = 크기 배율, tint = (색, 섞는 양)"""
        c = self.cam
        f, hx, hy, near = self.f, self.hx, self.hy, self.near
        csy, ccy, csp, ccp = c.sy, c.cy, c.sp, c.cp
        ox, oy, oz = org[0] - c.x, org[1] - c.y, org[2] - c.z
        # 월드 벡터 -> 카메라 좌표 (x, y, depth)

        def cam_vec(v, k=1.0):
            xr = -v[0] * ccy + v[2] * csy
            zr = v[0] * csy + v[2] * ccy
            return (xr * k, (v[1] * ccp + zr * csp) * k, (zr * ccp - v[1] * csp) * k)
        O = cam_vec((ox, oy, oz))
        Rc, Uc, Fc = cam_vec(Rv, scale), cam_vec(Uv, scale), cam_vec(Fv, scale)
        # 카메라의 로컬 좌표 (모델 단위)
        inv = 1.0 / scale
        clx = -(ox * Rv[0] + oy * Rv[1] + oz * Rv[2]) * inv
        cly = -(ox * Uv[0] + oy * Uv[1] + oz * Uv[2]) * inv
        clz = -(ox * Fv[0] + oy * Fv[1] + oz * Fv[2]) * inv
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
                if tint is not None:
                    cc = mix_rgb(cc, tint[0], tint[1])
                self.poly(cc, [corners[i] for i in ids])

    def _draw_kart(self, rc, dp, lv):
        tg = self.tg
        qp = self.qp
        m = self.model(rc.kart_id)
        if dp < (1.0 if rc.kind == 'local' else 3.2):
            return
        fxb = rc.fx
        sc = rc.scale
        h = rc.h
        up = rc.up
        fx, fz = math.sin(h), math.cos(h)
        # 도로면에 투영한 전방 벡터
        d = fx * up[0] + fz * up[2]
        Fv = (fx - up[0] * d, -up[1] * d, fz - up[2] * d)
        fl = math.sqrt(Fv[0] ** 2 + Fv[1] ** 2 + Fv[2] ** 2) or 1.0
        Fv = (Fv[0] / fl, Fv[1] / fl, Fv[2] / fl)
        Rv = (Fv[1] * up[2] - Fv[2] * up[1], Fv[2] * up[0] - Fv[0] * up[2], Fv[0] * up[1] - Fv[1] * up[0])   # F x U
        gnd = (rc.x, rc.y, rc.z)
        org = (rc.x, rc.y + rc.air_y, rc.z)
        amb = 0.7 if tg.night else 1.0
        tint = None
        if fxb & FX_STAR:
            tint = (hue_rgb(self.anim_t * 2.2), 0.5)
        elif fxb & FX_FREEZE:
            tint = ((175, 225, 255), 0.6)
        elif fxb & FX_SHRINK and fxb & FX_SPIN:
            tint = ((255, 255, 160), 0.35)
        # 드리프트/스핀: 차체를 진행 방향에서 틀어 보이게 (차체만 회전)
        yaw_off = rc.spin_ang
        if rc.drifting:
            yaw_off += -rc.drift_dir * 0.3
        elif abs(rc.slip) > 1.0:
            yaw_off += clamp(-rc.slip * 0.02, -0.25, 0.25)
        if yaw_off:
            cs, sn = math.cos(yaw_off), math.sin(yaw_off)
            Fn = tuple(Fv[i] * cs + Rv[i] * sn for i in range(3))
            Rn = tuple(Rv[i] * cs - Fv[i] * sn for i in range(3))
            Fv, Rv = Fn, Rn
        # 그림자 (공중이면 작아짐)
        if dp < qp['lod1']:
            L, W = m.L * sc, m.W * sc
            ks = 1.0 / (1.0 + rc.air_y * 0.25)
            pts = []
            for a in range(8):
                t = a * TAU / 8
                lx, lz = math.cos(t) * W * 0.66 * ks, math.sin(t) * L * 0.62 * ks
                pts.append(self.proj(gnd[0] + Rv[0] * lx + Fv[0] * lz, gnd[1] + 0.05 + Rv[1] * lx + Fv[1] * lz, gnd[2] + Rv[2] * lx + Fv[2] * lz))
            base_col = tg.pal['grass_a' if rc.offroad else 'road_a'][lv]
            self.poly(shade_rgb(base_col, 0.5), pts)
        if (fxb & FX_GHOST) and (self.frame_no // 3) % 2 == 0:
            return                                    # 유령: 깜빡임
        if dp > qp['lod1'] * 1.9:
            # 아주 먼 카트: 색 점
            p = self.proj(org[0], org[1] + 0.7, org[2])
            if p[2] > self.near:
                r = max(1, int(self.f * 1.0 * sc / p[2]))
                pygame.draw.rect(self.surf, m.main if tint is None else tint[0], (int(p[0] - r), int(p[1] - r), r * 2 + 1, r + 1))
            return
        lod0 = dp < qp['lod0']
        # 부스트 불꽃
        if rc.boosting and dp < qp['lod1']:
            L = m.L * sc
            ah = (m.base + m.H * 0.3) * sc
            anc = (org[0] - Fv[0] * (L / 2) + up[0] * ah, org[1] - Fv[1] * (L / 2) + up[1] * ah, org[2] - Fv[2] * (L / 2) + up[2] * ah)
            big = 1.6 if fxb & FX_AUTO else 1.0
            for ln, col in ((1.9, (255, 140, 30)), (1.1, (255, 230, 120))):
                ln = ln * (0.8 + 0.4 * random_f()) * sc * big
                w2 = 0.2 * sc * big
                pa = self.proj(anc[0] + Rv[0] * w2, anc[1] + Rv[1] * w2, anc[2] + Rv[2] * w2)
                pb = self.proj(anc[0] - Rv[0] * w2, anc[1] - Rv[1] * w2, anc[2] - Rv[2] * w2)
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
            self._draw_wheel(m, w, org, Rv, up, Fv, rc, lod0, amb, sc)
        self.draw_boxes(org, Rv, up, Fv, boxes, amb, 0, sc, tint)
        # 드라이버 헬멧
        hp = m.helmet
        hxw = org[0] + (Rv[0] * hp[0] + up[0] * hp[1] + Fv[0] * hp[2]) * sc
        hyw = org[1] + (Rv[1] * hp[0] + up[1] * hp[1] + Fv[1] * hp[2]) * sc
        hzw = org[2] + (Rv[2] * hp[0] + up[2] * hp[1] + Fv[2] * hp[2]) * sc
        hp_ = self.proj(hxw, hyw, hzw)
        if hp_[2] > self.near:
            hcol = m.main if tint is None else mix_rgb(m.main, tint[0], tint[1])
            r = max(2, int(self.f * 0.28 * sc / hp_[2]))
            pygame.draw.circle(self.surf, shade_rgb(hcol, amb * 0.8), (int(hp_[0]), int(hp_[1])), r)
            pygame.draw.circle(self.surf, shade_rgb(hcol, amb * 1.3), (int(hp_[0] - r * 0.3), int(hp_[1] - r * 0.3)), max(1, r // 2))
            if cl > 0 and lod0:
                pygame.draw.rect(self.surf, (12, 12, 14), (int(hp_[0] - r * 0.7), int(hp_[1] - r * 0.15), max(2, int(r * 1.4)), max(1, int(r * 0.45))))
        for w in second:
            self._draw_wheel(m, w, org, Rv, up, Fv, rc, lod0, amb, sc)
        # 방패: 카트를 감싸는 비눗방울
        if fxb & FX_SHIELD:
            ch = (m.base + m.H * 0.6) * sc
            cp_ = self.proj(org[0] + up[0] * ch, org[1] + up[1] * ch, org[2] + up[2] * ch)
            if cp_[2] > self.near:
                r = int(self.f * max(m.L, m.W * 1.4) * 0.72 * sc / cp_[2])
                if 3 < r < 900:
                    pygame.draw.circle(self.surf, (120, 220, 255), (int(cp_[0]), int(cp_[1])), r, max(1, r // 14))
                    pygame.draw.circle(self.surf, (235, 250, 255), (int(cp_[0] - r * 0.35), int(cp_[1] - r * 0.4)), max(1, r // 7))
        # 이름표
        if rc.kind != 'local' and 14 < dp < 150:
            k2 = 2.4 * sc
            p = self.proj(org[0] + up[0] * k2, org[1] + up[1] * k2, org[2] + up[2] * k2)
            if p[2] > self.near:
                self.labels.append((p[0], p[1], rc.name, (255, 210, 120) if rc.kind == 'bot' else (150, 232, 255), dp))

    def _draw_wheel(self, m, w, org, Rv, Uv, Fv, rc, lod0, amb, sc=1.0):
        lx, ly, lz, sgn, front = w
        lx, ly, lz = lx * sc, ly * sc, lz * sc
        R, ww = m.wheel_r * sc, m.wheel_w * sc
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

    # ---- 아이템전: 상자 / 투사체 / 함정 ------------------------------------------------------------------
    def set_qmark_font(self, path):
        self.qfont_path = path
        self.qcache = {}

    def _qmark(self, px):
        px = int(clamp(px, 6, 150))
        px -= px % 2
        if px in self.qcache:
            return self.qcache[px]
        try:
            g = pygame.font.Font(self.qfont_path, px).render('?', True, (255, 255, 255))
        except Exception:
            g = None
        if len(self.qcache) > 60:
            self.qcache.clear()
        self.qcache[px] = g
        return g

    @staticmethod
    def _yaw_basis(ang):
        c, s_ = math.cos(ang), math.sin(ang)
        return (-c, 0.0, s_), (0.0, 1.0, 0.0), (s_, 0.0, c)

    def _cube_box(self, x, y, z, ang, half, col, dp, qmark=True):
        Rv, Uv, Fv = self._yaw_basis(ang)
        self.draw_boxes((x, y, z), Rv, Uv, Fv, [(0, 0, 0, half, half, half, col, 1, 1, False)], 1.0)
        if qmark and dp < 80:
            p = self.proj(x, y, z)
            if p[2] > self.near:
                q = self._qmark(self.f * half * 1.7 / p[2])
                if q is not None:
                    self.surf.blit(q, (int(p[0] - q.get_width() / 2), int(p[1] - q.get_height() / 2)))

    def _draw_ibox(self, b, dp):
        t = self.anim_t
        bob = math.sin(t * 3.0 + b['ph']) * 0.18
        self._cube_box(b['x'], b['y'] + bob, b['z'], b['ph'] + t * 1.8, 0.8, hue_rgb(t * 0.25 + b['ph'] / TAU), dp)

    def _ground_poly(self, cx, cy, cz, pts, col, rot=0.0):
        """지면 위 평면 다각형. pts = (옆, 앞) 로컬 좌표"""
        c, s_ = math.cos(rot), math.sin(rot)
        self.poly(col, [self.proj(cx - lx * c + lz * s_, cy, cz + lx * s_ + lz * c) for (lx, lz) in pts])

    def _ground_ring(self, cx, cy, cz, r, col, n=18, width=2):
        pts = []
        for i in range(n):
            a = TAU * i / n
            p = self.proj(cx + math.cos(a) * r, cy, cz + math.sin(a) * r)
            if p[2] <= self.near:
                return
            pts.append((p[0], p[1]))
        pygame.draw.lines(self.surf, col, True, pts, width)

    def _ball(self, x, y, z, r, col, hl=None):
        p = self.proj(x, y, z)
        if p[2] <= self.near:
            return None
        rp = int(self.f * r / p[2])
        if rp > 700 or not (-rp <= p[0] <= self.rw + rp and -rp <= p[1] <= self.rh + rp):
            return p
        pygame.draw.circle(self.surf, col, (int(p[0]), int(p[1])), max(1, rp))
        if hl is not None and rp >= 3:
            pygame.draw.circle(self.surf, hl, (int(p[0] - rp * 0.35), int(p[1] - rp * 0.35)), max(1, rp // 3))
        return p

    _BLOB = (1.0, 0.85, 1.05, 0.9, 1.12, 0.8, 1.0, 0.92, 1.08, 0.86, 1.02, 0.9)

    def _ent_boxes(self, it):
        key = ('eb', it['id'])
        bx = self.models.get(key)
        if bx is None:
            bx = self.models[key] = ent_boxes(it)
        return bx

    def _draw_ent(self, e, dp):
        it = ITEMS[e.item]
        c1, c2 = it['c1'], it['c2']
        icon = it['icon']
        k = e.kind
        t = self.anim_t
        if k == 'trap':
            self._draw_trap(e, it, dp)
            return
        if k == 'tornado':
            for i in range(5):
                w = 1.0 + i * 0.75
                p = self.proj(e.x + math.sin(t * 9 + i) * 0.35 * i, e.y + 0.3 + i * 1.15, e.z + math.cos(t * 9 + i) * 0.35 * i)
                if p[2] > self.near:
                    rw = int(self.f * w / p[2])
                    rh = max(1, int(rw * 0.32))
                    if 1 < rw < 800:
                        pygame.draw.ellipse(self.surf, c1 if i % 2 == 0 else c2, (int(p[0] - rw), int(p[1] - rh), rw * 2, rh * 2), max(1, rh // 2))
            return
        if k == 'meteor':
            self._ground_ring(e.x, e.gy + 0.15, e.z, it['p'].get('r', 5.0), (255, 70, 40) if int(t * 8) % 2 else (255, 200, 60))
            p0 = self.proj(e.x, e.y + 7.0, e.z)
            p1 = self.proj(e.x, e.y, e.z)
            if p0[2] > self.near and p1[2] > self.near:
                pygame.draw.line(self.surf, (255, 190, 60), (p0[0], p0[1]), (p1[0], p1[1]), int(clamp(self.f * 0.9 / p1[2], 1, 40)))
            self._ball(e.x, e.y, e.z, 1.6, c1, (255, 230, 120))
            return
        if k == 'seeker':
            fx_, fz_ = math.sin(e.h), math.cos(e.h)
            rx_, rz_ = -fz_, fx_
            flap = math.sin(t * 22) * 0.45
            for sg in (-1, 1):
                a = self.proj(e.x + rx_ * sg * 0.6, e.y, e.z + rz_ * sg * 0.6)
                b = self.proj(e.x + rx_ * sg * 2.3, e.y + 0.6 + flap, e.z + rz_ * sg * 2.3)
                c = self.proj(e.x + rx_ * sg * 1.2 - fx_ * 0.9, e.y - 0.1, e.z + rz_ * sg * 1.2 - fz_ * 0.9)
                self.poly(c2, (a, b, c))
            self._ball(e.x, e.y, e.z, 1.0, c1, (255, 255, 255))
            return
        if k == 'bomb':
            p = self._ball(e.x, e.y, e.z, 0.8, c1, (100, 100, 112))
            if p is not None and p[2] > self.near:
                blink = e.state == 1 and int(t * (6 + e.age * 12)) % 2 == 0
                pygame.draw.circle(self.surf, (255, 50, 40) if blink else c2, (int(p[0]), int(p[1] - self.f * 0.85 / p[2])), max(1, int(self.f * 0.24 / p[2])))
            return
        if icon == 'laser':
            p0 = self.proj(e.x, e.y, e.z)
            sp = math.hypot(e.vx, e.vz) or 1.0
            p1 = self.proj(e.x - e.vx / sp * 8.0, e.y, e.z - e.vz / sp * 8.0)
            if p0[2] > self.near and p1[2] > self.near:
                wpx = int(clamp(self.f * 0.35 / p0[2], 1, 16))
                pygame.draw.line(self.surf, c1, (p0[0], p0[1]), (p1[0], p1[1]), wpx * 2)
                pygame.draw.line(self.surf, (255, 255, 255), (p0[0], p0[1]), (p1[0], p1[1]), wpx)
            return
        if icon in ('missile', 'arrow', 'drone', 'bird', 'shuriken', 'boomerang'):
            ang = (t * 20.0) if icon in ('shuriken', 'boomerang') else e.h
            Rv, Uv, Fv = self._yaw_basis(ang)
            self.draw_boxes((e.x, e.y, e.z), Rv, Uv, Fv, self._ent_boxes(it), 1.0)
            return
        if icon == 'bee':
            for i in range(5):
                a = t * 11 + i * 1.26
                self._ball(e.x + math.cos(a) * 0.9, e.y + math.sin(a * 1.7) * 0.4, e.z + math.sin(a) * 0.9, 0.32, c1, c2)
            return
        p = self._ball(e.x, e.y, e.z, 0.75, c1, (255, 255, 255) if icon != 'ball' else c2)
        if icon == 'target' and p is not None and p[2] > self.near:
            rp = int(self.f * 0.75 / p[2])
            if 3 < rp < 600:
                pygame.draw.circle(self.surf, c2, (int(p[0]), int(p[1])), rp, max(1, rp // 5))

    def _draw_trap(self, e, it, dp):
        p = it['p']
        shape = p.get('shape')
        c1, c2 = it['c1'], it['c2']
        y = e.gy + 0.08
        t = self.anim_t
        r = e.r
        if shape == 'banana':
            k = 1.9 if p.get('big') else 1.0
            arc = [-1.3 + 2.6 * i / 6.0 for i in range(7)]
            pts = [(math.sin(a) * 0.8 * k, (math.cos(a) * 0.8 - 0.45) * k) for a in arc] + \
                  [(math.sin(a) * 0.45 * k, (math.cos(a) * 0.45 - 0.45) * k) for a in reversed(arc)]
            self._ground_poly(e.x, y + 0.14, e.z, pts, c1, e.h)
            self._ground_poly(e.x, y + 0.15, e.z, [(-0.1 * k, 0.32 * k), (0.1 * k, 0.32 * k), (0.06 * k, 0.48 * k), (-0.06 * k, 0.48 * k)], (110, 76, 30), e.h)
        elif shape in ('oil', 'glue'):
            n = len(self._BLOB)
            pts = [(math.cos(TAU * i / n) * r * self._BLOB[i], math.sin(TAU * i / n) * r * self._BLOB[i]) for i in range(n)]
            self._ground_poly(e.x, y, e.z, pts, (22, 20, 30) if shape == 'oil' else c1, e.h)
            self._ground_poly(e.x, y + 0.01, e.z, [(math.cos(TAU * i / 8) * r * 0.22 + r * 0.3, math.sin(TAU * i / 8) * r * 0.14 - r * 0.25) for i in range(8)], c2, e.h)
        elif shape == 'ice':
            self._ground_poly(e.x, y, e.z, [(math.cos(TAU * i / 6) * r, math.sin(TAU * i / 6) * r) for i in range(6)], c1, e.h)
            self._ground_poly(e.x, y + 0.01, e.z, [(math.cos(TAU * i / 6) * r * 0.55, math.sin(TAU * i / 6) * r * 0.55) for i in range(6)], c2, e.h)
        elif shape == 'spikes':
            self._ground_poly(e.x, y, e.z, [(-r, -0.4), (r, -0.4), (r, 0.4), (-r, 0.4)], c2, e.h)
            if dp < 60:
                ch, sh_ = math.cos(e.h), math.sin(e.h)
                for i in range(6):
                    lx = -r + (i + 0.5) * 2 * r / 6.0
                    bx, bz = e.x - lx * ch, e.z + lx * sh_
                    a = self.proj(bx - 0.18 * ch, y, bz + 0.18 * sh_)
                    b = self.proj(bx + 0.18 * ch, y, bz - 0.18 * sh_)
                    c = self.proj(bx, y + 0.45, bz)
                    self.poly(c1, (a, b, c))
        elif shape == 'mine':
            self._ground_poly(e.x, y, e.z, [(math.cos(TAU * i / 10) * 0.85, math.sin(TAU * i / 10) * 0.85) for i in range(10)], c1)
            self._ground_poly(e.x, y + 0.12, e.z, [(math.cos(TAU * i / 10) * 0.5, math.sin(TAU * i / 10) * 0.5) for i in range(10)], (110, 116, 130))
            self._ball(e.x, y + 0.3, e.z, 0.17, (255, 40, 40) if int(t * 4) % 2 else (90, 20, 20))
        elif shape == 'fakebox':
            self._cube_box(e.x, e.gy + 0.85, e.z, -t * 1.8 + e.h, 0.8, hue_rgb(t * 0.25 + 0.5), dp)
        elif shape == 'wall':
            Rv, Uv, Fv = self._yaw_basis(e.h)
            self.draw_boxes((e.x, e.gy, e.z), Rv, Uv, Fv, wall_boxes(it), 1.0)
        elif shape == 'portal':
            ch, sh_ = math.cos(e.h), math.sin(e.h)
            pts = []
            for i in range(16):
                a = TAU * i / 16 + t * 2.0
                q = self.proj(e.x - math.cos(a) * 1.3 * ch, e.gy + 1.4 + math.sin(a) * 1.3, e.z + math.cos(a) * 1.3 * sh_)
                if q[2] <= self.near:
                    return
                pts.append((q[0], q[1]))
            w = int(clamp(self.f * 0.28 / max(dp, 1.0), 1, 20))
            pygame.draw.lines(self.surf, c1, True, pts, w)
            pygame.draw.lines(self.surf, c2, True, pts[::2], max(1, w // 2))

    # ---- 프레임 ----------------------------------------------------------------------------------------
    def render(self, race, cam_pos, focus_idx, dirn, boost_fx=0.0, speed_ratio=0.0, t=0.0):
        self.labels = []
        self.frame_no += 1
        self.anim_t = t
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
    ty = int(max(sh * 0.16, getattr(app, 'hud_top', 0) + 6 * u))
    for text, until, color, big in app.toasts[-2:]:
        size = (62 if big else 38) * u
        w = ui.render(text, size, color).get_width()
        if w > sw * 0.94:
            size = max(10, size * sw * 0.94 / float(w))      # 화면보다 길면 글자를 줄인다
        ui.text(surf, text, sw // 2, ty, size, color, 'c')
        ty += int((size + 8 * u) if not big else 70 * u)


# ============================================================================
#  [폰] 아이템전 UI: 벡터 아이콘 / 슬롯 3칸(키 1·2·3, 터치) / 룰렛 / 상태 표시 / 화면 효과(먹물·번쩍)
# ============================================================================
class ItemIcons(object):
    """코어의 벡터 아이콘 정의(ICONS) -> pygame Surface (2배로 그려서 부드럽게 축소, 크기별 캐시)"""

    def __init__(self):
        self.cache = {}

    def get(self, it, size):
        size = max(8, int(size))
        key = (it, size)
        s = self.cache.get(key)
        if s is None:
            if len(self.cache) > 320:
                self.cache.clear()
            s = self.cache[key] = self._make(ITEMS[it], size)
        return s

    @staticmethod
    def _draw(surf, item, prims, h, k, off, shadow):
        def P(x, y):
            return (h + x * k + off, h + y * k + off)
        for prim in prims:
            t = prim[0]
            if t == 'c':
                col = (0, 0, 0, 110) if shadow else icon_color(item, prim[4])
                pygame.draw.circle(surf, col, P(prim[1], prim[2]), max(1, int(prim[3] * k)))
            elif t == 'e':
                col = (0, 0, 0, 110) if shadow else icon_color(item, prim[5])
                cx, cy = P(prim[1], prim[2])
                rx, ry = max(1.0, prim[3] * k), max(1.0, prim[4] * k)
                pygame.draw.ellipse(surf, col, (cx - rx, cy - ry, rx * 2, ry * 2))
            elif t == 'r':
                col = (0, 0, 0, 110) if shadow else icon_color(item, prim[5])
                pygame.draw.circle(surf, col, P(prim[1], prim[2]), max(1, int(prim[3] * k + prim[4] * k / 2)), max(1, int(prim[4] * k)))
            elif t == 'p':
                col = (0, 0, 0, 110) if shadow else icon_color(item, prim[2])
                pygame.draw.polygon(surf, col, [P(x, y) for x, y in prim[1]])
            elif t == 'l':
                col = (0, 0, 0, 110) if shadow else icon_color(item, prim[3])
                w = max(1, int(prim[2] * k))
                pts = [P(x, y) for x, y in prim[1]]
                pygame.draw.lines(surf, col, False, pts, w)
                for p in pts:
                    pygame.draw.circle(surf, col, (int(p[0]), int(p[1])), max(1, w // 2))

    def _make(self, item, size):
        ss = size * 2
        surf = pygame.Surface((ss, ss), pygame.SRCALPHA)
        h = ss / 2.0
        k = h * 0.86
        prims = ICONS[item['icon']]
        self._draw(surf, item, prims, h, k, max(1, ss // 28), True)
        self._draw(surf, item, prims, h, k, 0, False)
        try:
            return pygame.transform.smoothscale(surf, (size, size))
        except Exception:
            return pygame.transform.scale(surf, (size, size))


def item_bar_rects(app):
    u = app.ui.u
    W, H = app.W, app.H
    S = int(64 * u)
    gap = int(9 * u)
    total = 3 * S + 2 * gap
    x0 = W // 2 - total // 2
    if app.landscape:
        y0 = int(8 * u)
    else:
        ms = int(min(H * 0.34, 200 * u))
        y0 = int(10 * u + ms + 34 * u)
    return [pygame.Rect(x0 + i * (S + gap), y0, S, S) for i in range(ITEM_SLOTS)]


def draw_item_bar(app, surf, race):
    ui = app.ui
    u = ui.u
    rc = race.local
    rects = item_bar_rects(app)
    t = app.t
    for i, r in enumerate(rects):
        it = rc.items[i]
        roll = rc.roll[i]
        ready = it is not None and roll <= 0
        ui.panel(surf, r, 215 if ready else 150, (18, 26, 52) if ready else (8, 12, 28), int(14 * u))
        if ready:
            pulse = 0.75 + 0.25 * math.sin(t * 6.0 + i)
            bc = (int(255 * pulse), int(200 * pulse), 70)
        else:
            bc = (80, 92, 125)
        rrect_outline(surf, bc, r, int(14 * u), max(2, int(3 * u)))
        if it is not None:
            if roll > 0:
                show = (int(t * 16) * 37 + i * 11) % ITEM_COUNT          # 룰렛
                ic = app.icons.get(show, r.w * 0.66)
            else:
                ic = app.icons.get(it, r.w * 0.8)
            surf.blit(ic, (r.centerx - ic.get_width() // 2, r.centery - ic.get_height() // 2))
            if ready and rc.uses[i] > 1:
                ui.text(surf, 'x%d' % rc.uses[i], r.right - 4 * u, r.bottom - 24 * u, 20 * u, (255, 255, 255), 'r')
            if ready:
                name = item_name(it, LANG)
                size = 14 * u
                w = ui.render(name, size, (230, 236, 255)).get_width()
                if w > r.w + 8 * u:
                    size = max(8, size * (r.w + 8 * u) / float(w))
                ui.text(surf, name, r.centerx, r.bottom + 2 * u, size, (230, 236, 255), 'c')
        ui.text(surf, str(i + 1), r.x + 6 * u, r.y + 2 * u, 17 * u, (255, 220, 120))
    app.hud_top = rects[0].bottom + 22 * u
    # 상태 표시 (무적/방패/축소…)
    st = fx_status(rc.sim, LANG)
    if st:
        x = rects[0].x
        y = rects[0].bottom + 20 * u
        for text, col in st[:4]:
            tw = ui.render(text, 15 * u, col).get_width()
            chip = pygame.Rect(int(x), int(y), int(tw + 14 * u), int(22 * u))
            ui.panel(surf, chip, 170, (0, 0, 0), int(10 * u))
            ui.text(surf, text, chip.x + 7 * u, chip.y + 2 * u, 15 * u, col, shadow=False)
            x += chip.w + 6 * u
        app.hud_top = y + 28 * u
    # 날아오는 미사일 경고
    thr = incoming_threat(race)
    if thr is not None and int(t * 6) % 2 == 0:
        ui.text(surf, T('! 미사일 접근 !', '! INCOMING !'), app.W // 2, int(app.hud_top), 30 * u, (255, 80, 80), 'c')
    return rects


def rrect_outline(surf, color, rect, r, width):
    try:
        pygame.draw.rect(surf, color, rect, width, border_radius=int(r))
    except TypeError:
        pygame.draw.rect(surf, color, rect, width)


class ScreenFx(object):
    """먹물(시야 가림)과 번개 번쩍임 - 큰 반투명 면은 미리 만들어 두고 투명도만 바꿔서 그린다"""

    def __init__(self):
        self.size = None
        self.ink = None
        self.veil = None
        self.flash = 0.0
        self.flash_col = (255, 255, 255)
        self.seed = 1

    def _ensure(self, W, H):
        if self.size != (W, H):
            self.size = (W, H)
            self.ink = None
            self.veil = pygame.Surface((W, H)).convert() if pygame.display.get_surface() is not None else pygame.Surface((W, H))

    def _make_ink(self, W, H):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        rnd = Rng(self.seed)
        base = min(W, H)
        for _ in range(7):
            cx, cy = W * (0.1 + rnd() * 0.8), H * (0.15 + rnd() * 0.75)
            r = base * (0.12 + rnd() * 0.16)
            pygame.draw.circle(s, (14, 12, 26, 245), (int(cx), int(cy)), int(r))
            for _k in range(6):
                a = rnd() * TAU
                d = r * (0.8 + rnd() * 0.6)
                pygame.draw.circle(s, (14, 12, 26, 245), (int(cx + math.cos(a) * d), int(cy + math.sin(a) * d)), int(r * (0.18 + rnd() * 0.25)))
            pygame.draw.circle(s, (60, 52, 90, 255), (int(cx - r * 0.35), int(cy - r * 0.35)), max(2, int(r * 0.12)))
        self.ink = s

    def draw(self, surf, W, H, blind_t, dt):
        self._ensure(W, H)
        if blind_t > 0:
            if self.ink is None:
                self.seed += 1
                self._make_ink(W, H)
            a = int(255 * clamp(blind_t / 1.2, 0.0, 1.0))
            self.ink.set_alpha(a)
            surf.blit(self.ink, (0, 0))
        elif self.ink is not None:
            self.ink = None
        if self.flash > 0:
            self.veil.fill(self.flash_col)
            self.veil.set_alpha(int(clamp(self.flash * 420, 0, 170)))
            surf.blit(self.veil, (0, 0))
            self.flash = max(0.0, self.flash - dt)


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


ITEM_KEYS = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
for _n, _slot in (('K_KP1', 0), ('K_KP2', 1), ('K_KP3', 2), ('K_KP_1', 0), ('K_KP_2', 1), ('K_KP_3', 2)):
    if hasattr(pygame, _n):
        ITEM_KEYS[getattr(pygame, _n)] = _slot


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
        self.renderer.set_qmark_font(self.font_path)
        self.icons = ItemIcons()
        self.sfx_screen = ScreenFx()
        self.hud_top = 0
        self.brake_held = False
        self.item_rects = []
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
        self.used_gas_key = False
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
                if e.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE) or e.key in ITEM_KEYS:
                    self.used_keyboard = True
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.used_gas_key = True          # 가속 키를 눌러 본 뒤부터 '직접 가속' (조향 키만으로는 바뀌지 않음)
                if e.key in (pygame.K_ESCAPE, getattr(pygame, 'K_AC_BACK', -999)):
                    self.on_back()
                elif self.scene == 'race':
                    if e.key in ITEM_KEYS:
                        self.use_item(ITEM_KEYS[e.key])
                    elif e.key == pygame.K_r and self.race:
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

    def touch_visible(self):
        """화면 버튼은 터치 기기(또는 키보드를 아직 안 쓴 경우)에서만 보인다"""
        return _is_android() or self.ptr.has_touch or not self.used_keyboard

    def read_input(self, dt):
        k = self.keys
        pressed = self.touch.read(self.ptr.down()) if self.touch_visible() else set()
        left = pygame.K_LEFT in k or pygame.K_a in k or 'left' in pressed
        right = pygame.K_RIGHT in k or pygame.K_d in k or 'right' in pressed
        tgt = (1.0 if right else 0.0) - (1.0 if left else 0.0)
        brake = pygame.K_DOWN in k or pygame.K_s in k or 'brake' in pressed
        gas = pygame.K_UP in k or pygame.K_w in k or 'gas' in pressed
        auto = self.profile['auto_gas'] and not self.used_gas_key
        drift = pygame.K_SPACE in k or pygame.K_LSHIFT in k or pygame.K_RSHIFT in k or 'drift' in pressed
        self.brake_held = brake
        self.steer = steer_step(self.steer, tgt, dt, self.profile['steer_resp'])
        return {'steer': self.steer, 'throttle': 1.0 if (gas or (auto and not brake)) else 0.0, 'brake': 1.0 if brake else 0.0, 'drift': drift}, pressed

    # ------------------------------------------------------------------ 레이스
    def start_solo(self):
        p = self.profile
        entries = solo_entries(p.display_name(), p['kart'], int(p['bots']))
        self.start_race(int(p['map']), int(p['laps']), entries, False, True, 5.0, p['mode'] == 'item')

    def use_item(self, slot):
        if self.race is not None and self.race.items is not None and not (self.paused and not self.race.multi):
            self.race.use_item(slot, self.brake_held)

    def start_race(self, map_id, laps, entries, multi, is_host, countdown, items=False):
        self.loading(T('맵 생성 중…', 'Building map…') + ' #%d' % map_id)
        self.race = Race(map_id, laps, entries, multi=multi, is_host=is_host, countdown=countdown, net=self.session.net if multi else None, items=items)
        self.hud_top = 0
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
        if not self.touch_visible() or not (_is_android() or self.ptr.has_touch):
            if items:
                self.toast(T('← → 조향  ↑ 가속  Space 드리프트  1·2·3 아이템 (↓ 누른 채 = 뒤로)  R 복귀',
                             'Steer ←→  Gas ↑  Drift Space  Items 1·2·3 (hold ↓ = throw back)  R reset'), 6.0, (255, 255, 255))
            else:
                self.toast(T('← → 조향   ↑ 가속   Space 드리프트   R 복귀', 'Left/Right steer   Up gas   Space drift   R reset'), 6.0, (255, 255, 255))
        elif items:
            self.toast(T('위쪽 아이템 칸을 눌러서 사용!', 'Tap the item slots at the top!'), 5.0, (255, 255, 255))

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
            elif kind == 'item':
                self.on_item_event(ev)
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

    def on_item_event(self, ev):
        what = ev[1]
        if what == 'roll':
            self.sfx.play('iroll', 0.5)
        elif what == 'get':
            self.sfx.play('iget')
            self.toast('%s  ·  %s' % (item_name(ev[2], LANG), item_desc(ev[2], LANG)), 1.8, (200, 235, 255))
        elif what == 'use':
            self.sfx.play('iuse', 0.7)
        elif what == 'hit':
            self.sfx.play('ihit')
            self.renderer.shake = max(self.renderer.shake, 0.9)
            self.toast(fx_name(ev[2], LANG) + '!', 1.2, (255, 110, 110), True)
        elif what == 'block':
            self.sfx.play('iblock')
            self.toast(T('방어!', 'BLOCKED!'), 1.0, (120, 220, 255), True)
        elif what == 'score':
            self.toast(T('명중! ', 'HIT! ') + str(ev[2]), 1.2, (255, 220, 90))
        elif what == 'stolen':
            self.toast(T('아이템을 도둑맞았어요: ', 'Item stolen: ') + item_name(ev[2], LANG), 1.6, (255, 150, 150))

    def burst(self, x, y, z, n, cols, spd, size, life, up=4.0):
        rd = self.renderer
        for i in range(n):
            a = _random.random() * TAU
            v = spd * (0.4 + _random.random() * 0.6)
            rd.emit(x, y, z, math.cos(a) * v, up * (0.3 + _random.random()), math.sin(a) * v, cols[i % len(cols)], size, life * (0.6 + _random.random() * 0.5))

    def item_vfx(self, race, lst):
        loc = race.local
        for v in lst:
            k = v[0]
            if k == 'box':
                self.burst(v[1], v[2], v[3], 14, [hue_rgb(i / 7.0) for i in range(7)], 7.0, 0.22, 0.6)
            elif k == 'boom':
                x, y, z, r, col = v[1], v[2], v[3], v[4], v[5]
                self.burst(x, y + 0.5, z, 34, [(255, 150, 40), (255, 230, 120), (255, 70, 40), col], r * 1.6, 0.45, 0.8, 7.0)
                d = math.hypot(loc.x - x, loc.z - z)
                if d < r * 3.0:
                    self.renderer.shake = max(self.renderer.shake, 1.0)
                if d < 150:
                    self.sfx.play('iboom', clamp(1.0 - d / 160.0, 0.15, 1.0))
            elif k == 'ring':
                x, y, z, r, col = v[1], v[2], v[3], v[4], v[5]
                for i in range(26):
                    a = TAU * i / 26
                    self.renderer.emit(x + math.cos(a) * 1.5, y + 0.6, z + math.sin(a) * 1.5, math.cos(a) * r * 2.2, 1.5, math.sin(a) * r * 2.2, col, 0.4, 0.45)
            elif k == 'hit':
                self.burst(v[1], v[2] + 0.8, v[3], 12, [(255, 255, 255), (255, 220, 90)], 6.0, 0.22, 0.5)
            elif k == 'block':
                self.burst(v[1], v[2] + 0.8, v[3], 14, [(120, 220, 255), (255, 255, 255)], 7.0, 0.22, 0.5)
            elif k == 'warp':
                self.burst(v[1], v[2] + 0.8, v[3], 18, [(170, 90, 255), (60, 230, 255)], 5.0, 0.28, 0.7, 6.0)
            elif k == 'pop':
                self.burst(v[1], v[2], v[3], 8, [v[4], (255, 255, 255)], 5.0, 0.2, 0.4)
            elif k == 'area':
                it = ITEMS[v[1]]
                if it['kind'] == 'zap':
                    for rid in v[3]:
                        rc = race._find(rid)
                        if rc is not None:
                            for j in range(9):
                                self.renderer.emit(rc.x + (_random.random() - 0.5) * 1.2, rc.y + 1.0 + j * 1.4, rc.z + (_random.random() - 0.5) * 1.2,
                                                   0.0, 0.0, 0.0, it['c1'] if j % 2 else (255, 255, 255), 0.35, 0.35)
                    if loc.id in v[3] or it['p'].get('scope') == 'all' or v[2] == loc.id:
                        self.sfx_screen.flash = 0.32
                        self.sfx_screen.flash_col = it['c1'] if it['icon'] in ('bolt', 'cloud') else (255, 255, 255)
                        self.sfx.play('izap', 0.8)

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
            if race.items is not None:
                self.item_vfx(race, race.items.take_vfx())
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
        if race.local is not None and race.local.sim is not None:
            self.sfx_screen.draw(self.screen, self.W, self.H, race.local.sim.blind_t if race.items is not None else 0.0, dt)
        if race.items is not None:
            self.item_rects = draw_item_bar(self, self.screen, race)
            for i, r in enumerate(self.item_rects):
                if ui.tapped(r.inflate(int(10 * u), int(10 * u))):
                    self.use_item(i)
        else:
            self.hud_top = 0
        draw_hud(self, self.screen, race, dt)
        if self.touch_visible():
            self.touch.draw(self.screen, ui, self.pressed)
        if race.items is not None and self.landscape:
            r3 = self.item_rects[-1]
            pb = R(r3.right + 12 * u, 8 * u, 44 * u, 40 * u)
        else:
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
        ui.text(surf, T('맵 1000개 · 카트 100,000종 · 아이템 100종 · WiFi 멀티', '1000 maps · 100,000 karts · 100 items · WiFi multiplayer'), x, int(self.H * 0.05) + 160 * u, 20 * u, (205, 220, 250), anc)
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
        half = (w - 10 * u) / 2.0
        item_mode = self.profile['mode'] == 'item'
        if ui.button(surf, R(x, y + 160 * u, half, 40 * u), T('스피드전', 'Speed'), 'chip' if item_mode else 'chipon', size=19 * u):
            self.profile['mode'] = 'speed'
            self.profile.save()
        if ui.button(surf, R(x + half + 10 * u, y + 160 * u, half, 40 * u), T('아이템전', 'Items'), 'chipon' if item_mode else 'chip', size=19 * u):
            self.profile['mode'] = 'item'
            self.profile.save()
        ui.text(surf, '%s #%d' % (kart_name(self.profile['kart'], LANG), self.profile['kart'] + 1), x, y + 210 * u, 18 * u, (190, 205, 240))
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
        kk = clamp(r.h / (700.0 * u), 0.6, 1.0)          # 작은 화면에서는 세로 간격을 줄여 모두 들어가게
        x, y, w = r.x + 18 * u, r.y + 12 * u, r.w - 36 * u
        bh = 44 * u * kk
        cw = (w - 20 * u) / 3.0
        ui.text(surf, T('설정', 'Settings'), x, y, 32 * u * kk)
        y += 50 * u * kk

        def chips(label, names, cur, on_pick):
            nonlocal y
            ui.text(surf, label, x, y, 21 * u * kk, (210, 220, 245))
            y += 27 * u * kk
            for i, nm in enumerate(names):
                if ui.button(surf, R(x + i * (cw + 10 * u), y, cw, bh), nm, 'chipon' if cur == i else 'chip', size=bh * 0.42):
                    on_pick(i)
            y += bh + 12 * u * kk

        def pick_quality(i):
            self.set_quality(i)
            self.show_map = None

        def pick_steer(i):
            self.profile['steer_resp'] = i
            self.profile.save()
            self.toast(T('조향 반응을 바꿨어요', 'Steering changed'), 0.8)

        def pick_lang(i):
            global LANG
            code = ('auto', 'ko', 'en')[i]
            self.profile['lang'] = code
            LANG = ('ko' if self.font_path else 'en') if code == 'auto' else code
            self.profile.save()
        chips(T('그래픽 품질', 'Graphics'), [T('낮음', 'Low'), T('중간', 'Medium'), T('높음', 'High')], self.renderer.q, pick_quality)
        chips(T('조향 반응 (키보드/버튼)', 'Steering response (keys/buttons)'), [T('부드럽게', 'Smooth'), T('보통', 'Normal'), T('빠르게', 'Quick')], int(self.profile['steer_resp']), pick_steer)
        for key, lab in (('auto_gas', T('자동 가속 (터치)', 'Auto gas (touch)')), ('sound', T('소리', 'Sound'))):
            on = bool(self.profile[key])
            if ui.button(surf, R(x, y, w, bh), '%s :  %s' % (lab, 'ON' if on else 'OFF'), 'good' if on else 'normal', size=bh * 0.42):
                self.profile[key] = not on
                if key == 'sound':
                    self.sfx.enabled = not on
                self.touch.layout(self.W, self.H, self.profile['auto_gas'])
                self.profile.save()
            y += bh + 10 * u * kk
        cur_lang = ('auto', 'ko', 'en').index(self.profile['lang']) if self.profile['lang'] in ('auto', 'ko', 'en') else 0
        chips(T('언어 / Language', 'Language'), ['Auto', '한국어' if self.font_path else 'Korean', 'English'], cur_lang, pick_lang)
        if ui.button(surf, R(x, y, w, bh), 'FPS :  %s' % ('ON' if self.show_fps else 'OFF'), 'good' if self.show_fps else 'normal', size=bh * 0.42):
            self.show_fps = not self.show_fps
        if ui.button(surf, R(x, r.bottom - 12 * u - 50 * u * kk, w, 50 * u * kk), T('완료', 'Done'), 'primary', size=22 * u * kk):
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
            self.start_race(int(msg['map']), int(msg['laps']), entries, True, ses.is_host, float(msg.get('countdown', 5.0)), bool(msg.get('items')))
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
        mid = self.map_picker(R(rr.x, rr.y, rr.w, rr.h - 196 * u), int(st['map']), editable=ses.is_host)
        if ses.is_host and mid != st['map']:
            ses.send_settings(map=mid)
            self.profile['map'] = mid
        ui.panel(surf, R(rr.x, rr.bottom - 186 * u, rr.w, 186 * u), 205)
        sx, sy, sw_ = rr.x + 14 * u, rr.bottom - 180 * u, rr.w - 28 * u
        half = (sw_ - 12 * u) / 2.0
        d1 = ui.stepper(surf, R(sx, sy + 4 * u, half, 38 * u), T('바퀴', 'Laps'), int(st['laps']), 1, 10) if ses.is_host else 0
        d2 = ui.stepper(surf, R(sx + half + 12 * u, sy + 4 * u, half, 38 * u), T('봇', 'Bots'), int(st['bots']), 0, 11) if ses.is_host else 0
        im = bool(st.get('items'))
        if ses.is_host:
            if ui.button(surf, R(sx, sy + 50 * u, half, 38 * u), T('스피드전', 'Speed'), 'chip' if im else 'chipon', size=18 * u):
                ses.send_settings(items=False)
                self.profile['mode'] = 'speed'
            if ui.button(surf, R(sx + half + 12 * u, sy + 50 * u, half, 38 * u), T('아이템전', 'Items'), 'chipon' if im else 'chip', size=18 * u):
                ses.send_settings(items=True)
                self.profile['mode'] = 'item'
        else:
            mode = T('아이템전', 'Item battle') if im else T('스피드전', 'Speed race')
            ui.text(surf, T('바퀴 %d · 봇 %d · %s' % (st['laps'], st['bots'], mode), 'Laps %d · Bots %d · %s' % (st['laps'], st['bots'], mode)), sx, sy + 8 * u, 22 * u, (230, 235, 255))
        if d1:
            ses.send_settings(laps=int(st['laps']) + d1)
        if d2:
            ses.send_settings(bots=int(st['bots']) + d2)
        if ses.is_host:
            if ui.button(surf, R(sx, sy + 100 * u, sw_, 64 * u), T('레이스 시작!', 'START RACE!'), 'primary', size=30 * u):
                ses.start_race()
        else:
            ui.text(surf, T('방장이 시작하기를 기다리는 중…', 'Waiting for the host to start…'), sx + sw_ / 2, sy + 100 * u, 22 * u, (190, 205, 240), 'c')

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
