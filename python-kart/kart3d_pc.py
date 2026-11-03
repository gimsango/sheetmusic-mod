#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
  TURBO KART 3D  -  컴퓨터 버전 (Python + Panda3D)       [ kart3d_pc.py ]
==========================================================================
  * 맵 1000개 (맵마다 다른 바이옴 1000종) / 카트 100,000종 / 아이템전(아이템 100종) / WiFi 멀티 / GPU 3D
  * 파일 하나로 실행:     pip install panda3d       (한 번만)
                          python kart3d_pc.py
  * 폰(Pydroid 3) 버전과 같은 방에서 함께 달릴 수 있습니다.

  [조작]   ↑/W 가속   ↓/S 브레이크   ←→/AD 조향   Space/Shift 드리프트
           1·2·3 아이템 사용 (↓ 누른 채 = 뒤로 던지기)
           R 트랙 복귀   Esc 일시정지   M 소리   F11 전체화면
           게임패드: 왼쪽 스틱 + RT/LT + A(드리프트) + X/Y/B(아이템)
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
    from panda3d.core import (loadPrcFileData, Filename, WindowProperties, NodePath, Geom, GeomNode, GeomTriangles, GeomPoints, GeomLines,
                              GeomVertexData, GeomVertexFormat, GeomVertexWriter, Texture, TransparencyAttrib, ColorBlendAttrib,
                              AmbientLight, DirectionalLight, Fog, Vec3, Vec4, Point3, CardMaker, TextNode, LineSegs, AntialiasAttrib,
                              ModifierButtons, ClockObject, InputDevice, DepthOffsetAttrib, OmniBoundingVolume)
    from direct.showbase.ShowBase import ShowBase
    from direct.gui.OnscreenText import OnscreenText
except ImportError as _e:
    _ensure_pkg('panda3d', err=str(_e), alt_hint='(panda3d 가 계속 안 되면: pygame-ce 설치 후 kart3d_phone.py 를 PC 에서 실행해도 같은 게임입니다)')
    raise SystemExit(1)

# -*- coding: utf-8 -*-
# ============================================================================
#  TURBO KART 3D (Python)  -  공통 코어
#  맵 1000개(바이옴 1000종) / 카트 100,000종 / 아이템 100종 / 아케이드 물리 / AI / WiFi(LAN) 멀티플레이
# ============================================================================
import math
import json
import colorsys
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


# ----------------------------------------------------------------------------
#  데이터: 맵 1000개 (바이옴 1000종) / 카트 20 x 20 x 25 x 10 = 100,000
# ----------------------------------------------------------------------------
ADJ = ['고요한', '질주하는', '폭풍의', '황금빛', '아득한', '불꽃', '은빛', '안개 낀', '번개', '전설의', '비밀',
       '끝없는', '반짝이는', '거친', '미지의', '새벽', '한밤', '정오의', '붉은', '푸른', '야생', '얼어붙은', '뜨거운', '꿈꾸는', '마지막']
ADJ_EN = ['Quiet', 'Racing', 'Stormy', 'Golden', 'Distant', 'Blazing', 'Silver', 'Foggy', 'Thunder', 'Legendary', 'Secret',
          'Endless', 'Sparkling', 'Rugged', 'Unknown', 'Dawn', 'Midnight', 'Noon', 'Crimson', 'Azure', 'Wild', 'Frozen', 'Scorching', 'Dreaming', 'Final']

def map_info(map_id):
    """맵 번호 -> 이름/바이옴. theme = 생태계(0~39), theme_name = 그 맵만의 바이옴 이름"""
    mid = int(min(MAP_COUNT, max(1, int(map_id))))
    n = mid - 1
    bm = biome(mid)
    seed = hash32(n * 7919 + 13)
    r = Rng(seed ^ 0x9e3779b9)
    a = int(r() * len(ADJ))
    b = int(r() * len(bm['nouns']))
    return dict(id=mid, seed=seed, theme=bm['family'], variant=n // BIOME_FAMILIES,
                name=ADJ[a] + ' ' + bm['nouns'][b], name_en=ADJ_EN[a] + ' ' + bm['nouns_en'][b],
                theme_name=bm['name'], theme_en=bm['en'], family_name=bm['family_ko'], family_en=bm['family_en'])


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


def relax_corners(poly, max_ang=0.19, iters=60, spacing=4.0, min_n=220):
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
    return resample_closed([tuple(p) for p in pts], spacing, min_n)


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
        """map_id: 기본 맵 번호(1~1000) 또는 '맵 만들기'로 만든 맵 데이터(dict)"""
        self.props = []
        self.props_by_seg = {}
        self.pads = []
        self.lamps = []
        self.arches = []
        self.obstacles = []          # 길 위(벽 안쪽)에 놓인 단단한 물체 [(x, z, 반지름, 인덱스, 가로 오프셋)]
        self.obs_near = {}           # 트랙 인덱스 -> 그 근처 장애물 목록 (충돌/봇 회피용)
        self.box_rows = None         # 아이템 상자 줄 위치 (None = 자동)
        self.custom = None
        if isinstance(map_id, dict):
            self._init_custom(map_id, outline_only)
            return
        self.info = map_info(map_id)
        self.theme = biome(map_id)
        r = Rng(self.info['seed'])
        self._set_width(15.0 + int(r() * 5))
        self._centerline(r)
        if not outline_only:
            self._decorate(r)

    def _set_width(self, width):
        self.width = width
        self.hw = self.width / 2.0
        hw, SH = self.hw, self.SH
        self.wall_off = hw + SH - 0.6
        # (가로 오프셋, 높이 변화): 도로 -> 연석 -> 갓길 -> 비탈
        self.rows = [(hw, 0.0), (hw + 0.7, -0.14), (hw + SH, -0.25), (hw + SH + 40.0, -2.5), (hw + SH + 200.0, -30.0)]

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
        self._setup_poly(poly)

    # ---- 맵 만들기로 만든 맵 ------------------------------------------------------------
    def _init_custom(self, data, outline_only):
        d = cmap_clean(data) or cmap_new()
        self.custom = d
        seed = cmap_key(d)
        th = cmap_theme(d)
        self.theme = th
        self.info = dict(id=0, seed=seed, theme=th['family'], variant=0, name=d['name'], name_en=d['name'],
                         theme_name=th['name'], theme_en=th['en'], family_name=th['family_ko'], family_en=th['family_en'], custom=True)
        r = Rng(seed)
        self._set_width(float(d['width']))
        pts = d['pts']
        K = len(pts)
        amp = 30.0 * d['hills']
        ph = (r() * TAU, r() * TAU, r() * TAU)
        cps = []
        for i, p in enumerate(pts):
            t = i / float(K)
            y = p[2] + amp * (math.sin(TAU * t + ph[0]) * 0.6 + math.sin(2 * TAU * t + ph[1]) * 0.3 + math.sin(3 * TAU * t + ph[2]) * 0.18)
            cps.append((p[0], y, p[1]))
        poly = resample_closed(catmull_closed(cps, 24), 4.0, 60)
        # 너무 급한 꺾임은 달릴 수 있게 둥글게 (그린 모양은 최대한 유지)
        for _ in range(6):
            if max_turn_angle(poly) <= 0.21:
                break
            poly = relax_corners(poly, min_n=60)
        self._setup_poly(poly)
        if outline_only:
            return
        if d['pads']:
            self._auto_pads(r)
        dk = CMAP_DECO_K[d['deco']]
        if dk > 0:
            self._auto_props(r, dk)
        self._place_objs(d, seed)
        self._finish_props()
        if d['deco'] > 0:
            self._theme_extras()

    def _place_objs(self, d, seed):
        """직접 놓은 물건: 장식물/장애물(충돌) / 부스트·점프·기름 발판 / 아이템 상자 줄"""
        q = Q()
        N = self.N
        hw = self.hw
        boxes = []
        for n, o in enumerate(d['objs']):
            kind, x, z, s, rot = o[0], o[1], o[2], o[3], o[4]
            info = OBJ_INFO[kind]
            self.query(x, z, -1, q)
            idx = int(round(q.prog)) % N
            dd = q.d
            if info['cat'] == 'road':
                if abs(dd) > hw + 1.5:
                    continue                      # 길 밖의 발판/상자는 쓰지 않음
                if kind == 'box':
                    boxes.append(idx)
                    continue
                if kind == 'jump':
                    hl, hwp = 3.2 * s, 3.4 * s
                elif kind == 'oil':
                    hl, hwp = 3.4 * s, 2.6 * s
                else:
                    hl, hwp = 4.5 * s, 2.8 * s
                hwp = min(hwp, hw)
                pad = dict(idx=idx, d=clamp(dd, -hw + hwp, hw - hwp), half_len=hl, half_w=hwp)
                if kind != 'pad':
                    pad['kind'] = kind
                self.pads.append(pad)
                continue
            rr = Rng((seed ^ hash32(n * 7 + 3)) & 0xFFFFFFFF)
            r1, r2, r3 = rr(), rr(), rr()
            if kind == 'building':                # 빌딩은 크기 조절값으로 폭/높이를 정한다
                k = clamp((s - 0.3) / 2.7, 0.0, 1.0)
                r1 = r2 = k
                r3 = math.sqrt(k)
                rad = (14 + r1 * 22) * 0.45
            else:
                rad = info['rad'] * s
            y = q.y if abs(dd) <= hw + 0.7 else q.y - 0.15
            self.props.append(dict(kind=kind, x=x, y=y, z=z, rot=rot, s=s, r1=r1, r2=r2, r3=r3, seg=idx, user=True))
            if rad > 0 and abs(dd) - rad < self.wall_off:
                self.obstacles.append((x, z, rad, idx, dd))
        if boxes:
            rows = []
            for i in sorted(set(boxes)):
                if not rows or i - rows[-1] > 3:
                    rows.append(i)
            self.box_rows = rows
        for ob in self.obstacles:
            span = int(ob[2] / self.ds) + 4
            for k in range(-span, span + 1):
                self.obs_near.setdefault((ob[3] + k) % N, []).append(ob)

    def _setup_poly(self, poly):
        """재샘플된 닫힌 중심선(점 간격 약 4m) -> 방향/오른쪽 벡터/길이/뱅킹/커브 강도"""
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
        self._auto_pads(r)
        self._auto_props(r, 1.0)
        self._finish_props()
        self._theme_extras()

    def _auto_pads(self, r):
        N = self.N
        count = 6 + int(r() * 5)
        for k in range(count):
            idx = int(((k + 0.5 + (r() - 0.5) * 0.4) / count) * N)
            d = (r() - 0.5) * self.width * 0.5
            if idx < 14 or idx > N - 8:
                continue
            self.pads.append(dict(idx=idx, d=d, half_len=4.5, half_w=2.8))

    def _auto_props(self, r, density):
        """벽 바깥에 바이옴 장식물을 흩뿌린다 (density 1 = 기본 맵과 같은 양)"""
        th = self.theme
        N = self.N
        px, pz, py, rx, rz = self.px, self.pz, self.py, self.rx, self.rz
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
        want = int(round(N * 2.1 * density))
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

    def _finish_props(self):
        for p in self.props:
            self.props_by_seg.setdefault(p['seg'], []).append(p)

    def _theme_extras(self):
        th = self.theme
        N = self.N
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

        # 맵 만들기 장애물 (원 기둥과 충돌) - 높이 뛰어 있거나 유령이면 통과
        if t.obs_near and self.air_y < 0.9 and self.ghost_t <= 0:
            obs = t.obs_near.get(self.hint)
            if obs:
                kr = 1.15 * (1.5 if self.giant_t > 0 else (0.7 if self.shrink_t > 0 else 1.0))
                for ob in obs:
                    dx = self.x - ob[0]
                    dz = self.z - ob[1]
                    rr = ob[2] + kr
                    d2 = dx * dx + dz * dz
                    if d2 < rr * rr:
                        dist = math.sqrt(d2)
                        if dist < 1e-4:
                            nx, nz = -fx, -fz
                        else:
                            nx, nz = dx / dist, dz / dist
                        self.x = ob[0] + nx * rr
                        self.z = ob[1] + nz * rr
                        vn = self.vx * nx + self.vz * nz
                        if vn < 0:
                            self.vx -= nx * vn * 1.45
                            self.vz -= nz * vn * 1.45
                            k = 1 - clamp(-vn / 70.0, 0.05, 0.3)
                            self.vx *= k
                            self.vz *= k
                            if vn < -6:
                                self.wall_hit = 1.0
                                ev.append('wall')
                            if self.drifting:
                                self.drifting = False
                                self.drift_charge = 0.0
                                self.drift_tier = 0

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
                    pk = p.get('kind')
                    if pk == 'jump':
                        if self.hop_t <= 0 and self.air_t <= 0:
                            self.hop_t = self.hop_dur = 0.95
                            ev.append('jump')
                        self.pad_cool = 0.7
                        break
                    if pk == 'oil':
                        if self.star_t <= 0 and self.auto_t <= 0:
                            self.slide_t = max(self.slide_t, 1.4)
                            ev.append('oil')
                        self.pad_cool = 0.9
                        break
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
    def _avoid(self, tr, idx, lane):
        """앞쪽 장애물들이 막은 가로 구간을 모아서, 지금 차선에서 가장 가까운 빈 틈으로 비켜 간다 (길이 다 막혔으면 갓길로)"""
        N = tr.N
        hw = tr.hw
        lim = tr.wall_off - 2.0
        blocked = []
        seen = set()
        for k in (2, 5, 8, 11, 14, 17):
            lst = tr.obs_near.get((idx + k) % N)
            if not lst:
                continue
            for ob in lst:
                if id(ob) in seen:
                    continue
                seen.add(id(ob))
                ahead = (ob[3] - idx) % N
                if ahead < 1 or ahead > 18:
                    continue
                m = ob[2] + 1.8
                blocked.append((ob[4] - m, ob[4] + m))
        if not blocked:
            return lane
        if all(not (a < lane < b) for a, b in blocked):
            return lane
        best = None
        best_s = 1e9
        for a, b in blocked:
            for c in (a - 0.05, b + 0.05):
                if -lim <= c <= lim and all(not (a2 < c < b2) for a2, b2 in blocked):
                    sc = abs(c - lane) + (4.0 if abs(c) > hw - 0.8 else 0.0)
                    if sc < best_s:
                        best_s, best = sc, c
        return lane if best is None else best

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
        if tr.obs_near:
            lane = self._avoid(tr, q.idx, lane)
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
        self.map_id = map_id              # 기본 맵 번호 또는 만든 맵 데이터(dict)
        self.track = Track(map_id)
        self.custom = self.track.custom
        self.laps = laps
        self.multi = multi
        self.is_host = is_host
        self.net = net
        self.racers = []
        self.local = None
        rnd = Rng(map_id * 31 + 7) if self.custom is None else Rng((self.track.info['seed'] ^ 0x5151) & 0xFFFFFFFF)
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
        self.cmap = None              # 방장이 고른 '만든 맵' 데이터 (있으면 이 맵으로 달림)
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
                    if self.cmap:
                        info['cname'] = str(self.cmap.get('name', ''))[:20]
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
                    'cmap': self.cmap, 'players': [{'id': c.id, 'name': c.name, 'kart': c.kart} for c in self.conns.values()]}

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
                    if 'cmap' not in m:
                        self.cmap = None             # 기본 맵을 고르면 '만든 맵' 해제
                if 'cmap' in m:
                    self.cmap = cmap_clean(m['cmap']) if m['cmap'] else None
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
                    msg = {'t': 'start', 'map': self.map, 'laps': self.laps, 'countdown': 5.0, 'players': order, 'bots': bots, 'items': self.items,
                           'cmap': self.cmap}
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
        self.settings = {'map': 1, 'laps': 3, 'bots': 0, 'items': True, 'cmap': None}
        self.start_msg = None
        self.address = ''
        self._joined = False

    @property
    def is_host(self):
        return self.my_id is not None and self.my_id == self.host_id

    def host_game(self, port=DEFAULT_PORT, cmap=None):
        self.leave()
        try:
            self.server = RoomServer(port, name=self.profile.display_name()).start()
            self.server.map = int(self.profile['map'])
            self.server.cmap = cmap_clean(cmap) if cmap else None
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
                cm = m.get('cmap')
                self.settings = {'map': m.get('map', 1), 'laps': m.get('laps', 3), 'bots': m.get('bots', 0), 'items': bool(m.get('items', False)),
                                 'cmap': cmap_clean(cm) if cm else None}
                if self.state in ('connecting', 'idle'):
                    self.state = 'lobby'
            elif t == 'start':
                cm = m.get('cmap')
                m['cmap'] = cmap_clean(cm) if cm else None
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
                'mode': 'item',           # 'item' = 아이템전, 'speed' = 스피드전
                'map_src': 'builtin',     # 'builtin' = 기본 맵(1~1000), 'custom' = 내가 만든 맵
                'cmap': ''}               # 고른 '내 맵' 의 uid

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
        if tr.box_rows is not None:              # 맵 만들기에서 직접 놓은 상자 줄
            for idx in tr.box_rows:
                for j in range(4):
                    d = tr.hw * (-0.66 + 0.44 * j)
                    x, y, z, h = tr.pose_at(idx, d)
                    self.boxes.append({'x': x, 'y': y + 1.15, 'z': z, 'idx': idx, 't': 0.0, 'ph': r() * TAU, 'h': h})
            return
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


def tex_jump():
    """점프대: 노란 바탕 + 검은 사선 + 흰 화살표"""
    w, h = 64, 128
    buf = bytearray(w * h * 3)
    for y in range(h):
        for x in range(w):
            o = (y * w + x) * 3
            col = (250, 196, 28)
            if y < 40 and ((x + y) // 10) % 2 == 0:
                col = (30, 30, 34)
            dy = y - 64
            dx = abs(x - w / 2.0)
            if (0 <= dy - dx * 0.9 <= 14 and dx < 26) or (dx < 7 and 70 <= y <= 112):
                col = (255, 255, 255)
            if x < 3 or x > w - 4 or y < 3 or y > h - 4:
                col = (30, 30, 34)
            buf[o], buf[o + 1], buf[o + 2] = col
    return make_texture('jump', w, h, buf, 'RGB', False)


def tex_oil():
    """기름 웅덩이: 가장자리가 울퉁불퉁한 검은 얼룩 (밖은 투명)"""
    w, h = 64, 64
    buf = bytearray(w * h * 4)
    for y in range(h):
        for x in range(w):
            o = (y * w + x) * 4
            u, v = (x - 31.5) / 31.5, (y - 31.5) / 31.5
            a = math.atan2(v, u)
            r = math.hypot(u, v)
            edge = 0.86 + 0.12 * math.sin(a * 3.0 + 1.0)
            if r < edge:
                col = (20, 14, 28)
                if (u + 0.3) ** 2 / 0.09 + (v + 0.2) ** 2 / 0.04 < 1.0:
                    col = (64, 52, 108)
                elif (u - 0.3) ** 2 / 0.03 + (v - 0.3) ** 2 / 0.02 < 1.0:
                    col = (40, 92, 96)
                buf[o], buf[o + 1], buf[o + 2], buf[o + 3] = col[0], col[1], col[2], 235
            else:
                buf[o], buf[o + 1], buf[o + 2], buf[o + 3] = 0, 0, 0, 0
    return make_texture('oil', w, h, buf, 'RGBA', False)


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
                    m.sphere((math.cos(a) * d + (j - 1.5) * s * 0.9, math.sin(a) * d, z + (j % 2) * 8), s * 0.55, rgbf(th.get('cloud') or (255, 255, 255), 1.0, 0.88),
                             seg=8, rings=4, scale=(1.0, 0.7, 0.34))
            cl = m.attach(self.sky, 'clouds')
            cl.setTransparency(TransparencyAttrib.MAlpha)
            cl.setLightOff()
            cl.setFogOff()
            cl.setDepthWrite(False)
            cl.setBin('background', 4)
        if th.get('aurora'):
            self._aurora()
        self._horizon()

    def _aurora(self):
        """오로라: 하늘에 반투명 띠 3줄"""
        m = Mesh()
        for band, col in enumerate(((0.3, 1.0, 0.68, 0.5), (0.36, 0.82, 1.0, 0.4), (0.75, 0.48, 1.0, 0.32))):
            ph, z0 = self.rnd() * TAU, 560 + band * 210
            seg = 90
            prev = None
            for i in range(seg + 1):
                a = TAU * i / seg
                r = 2800.0
                zz = z0 + math.sin(a * 3 + ph) * 90 + math.sin(a * 7 + ph * 2) * 35
                th_ = 230 + 80 * math.sin(a * 5 + ph)
                lo = m.add((math.cos(a) * r, math.sin(a) * r, zz), (-math.cos(a), -math.sin(a), 0), (col[0], col[1], col[2], col[3]))
                hi = m.add((math.cos(a) * r, math.sin(a) * r, zz + th_), (-math.cos(a), -math.sin(a), 0), (col[0], col[1], col[2], 0.0))
                if prev is not None:
                    m.tri(prev[0], lo, hi)
                    m.tri(prev[0], hi, prev[1])
                prev = (lo, hi)
        au = m.attach(self.sky, 'aurora')
        au.setTwoSided(True)
        au.setLightOff()
        au.setFogOff()
        au.setTransparency(TransparencyAttrib.MAlpha)
        au.setDepthWrite(False)
        au.setDepthTest(False)
        au.setBin('background', 1)

    def _horizon(self):
        """360도 지평선: 코어 horizon_layers 정의를 원통면에 그린다 (배경 칸에서 순서대로 -> 겹침 깜빡임 없음)"""
        th = self.th
        m = Mesh()

        def P(rad, a, h):
            t = a * TAU
            return (math.cos(t) * rad, math.sin(t) * rad, h)

        def N(a):
            t = a * TAU
            return (-math.cos(t), -math.sin(t), 0.2)

        def fan(rad, col, pts):
            c = rgbf(col)
            ca = sum(q[0] for q in pts) / len(pts)
            cz = sum(q[1] for q in pts) / len(pts)
            ctr = m.add(P(rad, ca, cz), N(ca), c)
            idx = [m.add(P(rad, a, h), N(a), c) for a, h in pts]
            for i in range(len(idx)):
                m.tri(ctr, idx[i], idx[(i + 1) % len(idx)])
        for rad, items in horizon_layers(th, self.track.info['seed']):
            for it in items:
                t = it[0]
                if t == 'ridge':
                    col, top, hs = it[1], it[2], it[3]
                    n = len(hs) - 1
                    rows = []
                    for i in range(n + 1):
                        a = i / float(n)
                        if top:
                            rows.append((m.add(P(rad, a, -300.0), N(a), rgbf(col, 0.82)), m.add(P(rad, a, hs[i] * 0.72), N(a), rgbf(col, 1.05)),
                                         m.add(P(rad, a, hs[i]), N(a), rgbf(top))))
                        else:
                            rows.append((m.add(P(rad, a, -300.0), N(a), rgbf(col, 0.82)), m.add(P(rad, a, hs[i]), N(a), rgbf(col, 1.12))))
                    for i in range(n):
                        r0, r1 = rows[i], rows[i + 1]
                        for k in range(len(r0) - 1):
                            m.tri(r0[k], r1[k], r1[k + 1])
                            m.tri(r0[k], r1[k + 1], r0[k + 1])
                elif t == 'poly':
                    fan(rad, it[1], it[2])
                elif t == 'disc':
                    col, a, h, r = it[1], it[2], it[3], it[4]
                    fan(rad, col, [(a + r * math.cos(TAU * k / 18) / (TAU * rad), h + r * math.sin(TAU * k / 18)) for k in range(18)])
                elif t == 'ring':
                    col, a, h, rx, ry, w = it[1], it[2], it[3], it[4], it[5], it[6]
                    c = rgbf(col)
                    seg = 40
                    outer = [m.add(P(rad, a + rx * math.cos(TAU * k / seg) / (TAU * rad), h + ry * math.sin(TAU * k / seg)), N(a), c) for k in range(seg)]
                    inner = [m.add(P(rad, a + (rx - w) * math.cos(TAU * k / seg) / (TAU * rad), h + (ry - w) * math.sin(TAU * k / seg)), N(a), c) for k in range(seg)]
                    for k in range(seg):
                        k2 = (k + 1) % seg
                        m.tri(outer[k], outer[k2], inner[k2])
                        m.tri(outer[k], inner[k2], inner[k])
                elif t == 'line':
                    col, pts, w = it[1], it[2], it[3]
                    c = rgbf(col, 1.3)
                    for i in range(len(pts) - 1):
                        (a0, h0), (a1, h1) = pts[i], pts[i + 1]
                        q = [m.add(P(rad - 1.0, a0, h0 - w / 2), N(a0), c), m.add(P(rad - 1.0, a1, h1 - w / 2), N(a1), c),
                             m.add(P(rad - 1.0, a1, h1 + w / 2), N(a1), c), m.add(P(rad - 1.0, a0, h0 + w / 2), N(a0), c)]
                        m.tri(q[0], q[1], q[2])
                        m.tri(q[0], q[2], q[3])
        hz = m.attach(self.sky, 'horizon')
        hz.setTwoSided(True)
        hz.setLightOff()
        hz.setFogOff()
        hz.setDepthWrite(False)
        hz.setDepthTest(False)
        hz.setBin('background', 6)

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
        kb = self.th.get('kerb') or ((216, 35, 42), (240, 240, 240))
        red, white = rgbf(kb[0]), rgbf(kb[1])
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
        texs = {}
        for p in tr.pads:
            pk = p.get('kind') or 'boost'
            tex = texs.get(pk)
            if tex is None:
                tex = texs[pk] = tex_pad() if pk == 'boost' else (tex_jump() if pk == 'jump' else tex_oil())
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
            if pk == 'oil':
                np_.setTransparency(TransparencyAttrib.MAlpha)

    # ---- 장식물 -----------------------------------------------------------------------------
    def _proto(self, kind, var):
        """장식물 원형 메시 (바이옴 팔레트로 색칠). 반환: (빛 받는 메시, 발광 메시|None)"""
        th = self.th
        m = Mesh()
        g = Mesh()
        rc = (hex_rgb(th['rock'][0]), hex_rgb(th['rock'][1]))
        leaf = th.get('leaf') or [(47, 127, 53), (58, 140, 58), (74, 160, 74), (90, 170, 80)]
        trunk = th.get('trunk') or (90, 59, 34)
        acc = th.get('accent') or [(255, 43, 214), (25, 230, 255), (255, 225, 74), (120, 255, 150)]
        flower = th.get('flower') or [(255, 224, 64), (255, 96, 128), (255, 255, 255), (176, 123, 255)]
        night = self.night
        if kind == 'pine':
            m.frustum((0, 0, 1.5), 0.5, 0.35, 3.0, rgbf(trunk), 'z', 6)
            if th.get('snowy'):
                cols = [mix_rgb(leaf[0], (240, 246, 252), 0.15), mix_rgb(leaf[1], (240, 246, 252), 0.35), (242, 247, 251)]
            else:
                cols = [leaf[0], leaf[1], leaf[2]]
            for (z, r, ln), c in zip(((5.0, 3.4, 5.0), (7.6, 2.7, 4.6), (10.0, 1.9, 4.0)), cols):
                m.frustum((0, 0, z), r, 0.0, ln, rgbf(c), 'z', 7, True)
        elif kind == 'roundtree':
            c = leaf[var % len(leaf)]
            m.frustum((0, 0, 2.0), 0.65, 0.45, 4.0, rgbf(trunk), 'z', 6)
            m.sphere((0, 0, 6.5), 3.4, rgbf(c), 9, 6, (1, 1, 0.9))
            m.sphere((1.6, 0.8, 5.3), 2.2, rgbf(c, 0.88), 8, 5)
            if th.get('snowy'):
                m.sphere((0, 0, 8.6), 2.2, (0.94, 0.96, 0.99, 1), 8, 4, (1, 1, 0.45))
        elif kind == 'bush':
            m.sphere((0, 0, 0.8), 1.6, rgbf(leaf[0]), 8, 5, (1.2, 1.1, 0.7))
            m.sphere((1.3, 0.5, 0.5), 1.1, rgbf(leaf[1]), 7, 4)
        elif kind == 'cactus':
            gc = rgbf(th.get('cactus') or (59, 138, 74))
            m.frustum((0, 0, 3.0), 0.8, 0.7, 6.0, gc, 'z', 8)
            m.frustum((0.9, 0, 2.4), 0.4, 0.4, 1.4, gc, 'x', 6)
            m.frustum((1.7, 0, 3.5), 0.4, 0.4, 2.4, gc, 'z', 6)
            m.frustum((-0.6, 0, 3.6), 0.4, 0.4, 1.2, gc, 'x', 6)
            m.frustum((-1.3, 0, 4.4), 0.4, 0.4, 1.8, gc, 'z', 6)
        elif kind == 'rock':
            m.sphere((0, 0, 0.9), 2.2, rgbf(rc[0]), 7, 4, (1.3, 1.1, 0.8))
            m.sphere((2.3, 0.7, 0.5), 1.3, rgbf(rc[1]), 6, 4, (1.0, 1.0, 0.8))
        elif kind == 'mesa':
            mc = th.get('mesa') or [(176, 74, 40), (199, 101, 58), (168, 68, 36), (224, 160, 96)]
            for (z, r0, r1, ln), c in zip(((6, 9, 7, 12), (15, 7, 6.2, 6), (20.5, 6.2, 5.4, 5), (23.6, 5.6, 5.6, 1.2)), (mc[0], mc[1], mc[2], mc[3])):
                m.frustum((0, 0, z), r0, r1, ln, rgbf(c), 'z', 7)
        elif kind == 'palm':
            m.frustum((0.3, 0, 4.2), 0.5, 0.28, 8.4, rgbf(mix_rgb(trunk, (200, 170, 110), 0.45)), 'z', 6)
            for k in range(7):
                a = k * 0.898
                blade(m, (0.3, 0, 8.4), (0.3 + math.cos(a) * 4.6, math.sin(a) * 4.6, 6.7), 0.75, rgbf(leaf[k % len(leaf)]))
            m.sphere((0.3, 0, 8.2), 0.45, rgbf(shade_rgb(trunk, 0.9)), 6, 4)
        elif kind == 'building':
            m.box((0, 0, 0.5), (0.5, 0.5, 0.5), rgbf((58, 56, 108)))
            for z, c in ((0.9, acc[0]), (0.62, acc[1 % len(acc)]), (0.34, acc[2 % len(acc)]), (0.98, acc[0])):
                g.box((0, 0, z), (0.512, 0.512, 0.008), rgbf(c, 1.6))
        elif kind == 'crystal':
            col = th.get('crystal') or (255, 43, 214)
            g.octa((0, 0, 3.0), 1.2, rgbf(col, 1.5), (1, 1, 2.6))
            g.octa((1.6, 0.4, 1.8), 0.8, rgbf(col, 1.2), (1, 1, 2.2))
        elif kind == 'lollipop':
            hue = acc[var % len(acc)]
            m.frustum((0, 0, 2.6), 0.16, 0.16, 5.2, rgbf((245, 245, 245)), 'z', 6)
            m.frustum((0, 0, 6.2), 2.2, 2.2, 0.6, rgbf((255, 255, 255)), 'y', 14)
            m.frustum((0, -0.31, 6.2), 1.2, 1.2, 0.05, rgbf(hue), 'y', 14)
            m.frustum((0, 0.31, 6.2), 1.2, 1.2, 0.05, rgbf(hue), 'y', 14)
        elif kind == 'icecream':
            sc = mix_rgb(acc[(var + 1) % len(acc)], (255, 255, 255), 0.45)
            m.frustum((0, 0, 1.8), 0.0, 1.4, 3.6, rgbf((224, 169, 106)), 'z', 8)
            m.sphere((0, 0, 4.3), 1.7, rgbf(sc), 9, 6)
            m.sphere((0, 0, 6.1), 0.4, rgbf((221, 34, 51)), 6, 4)
        elif kind == 'acacia':
            c = leaf[var % len(leaf)]
            m.frustum((0, 0, 2.3), 0.32, 0.22, 4.6, rgbf(trunk), 'z', 6)
            m.frustum((-0.9, 0, 3.7), 0.14, 0.14, 2.0, rgbf(trunk), 'x', 5)
            m.sphere((0.3, 0, 4.9), 4.2, rgbf(c), 10, 5, (1, 1, 0.22))
            m.sphere((-1.4, 0.4, 4.2), 2.2, rgbf(c, 0.9), 8, 4, (1, 1, 0.26))
            if var:
                m.sphere((1.8, -0.6, 4.3), 1.8, rgbf(c, 1.08), 8, 4, (1, 1, 0.3))
        elif kind == 'deadtree':
            tc = rgbf(trunk)
            m.frustum((0, 0, 3.0), 0.42, 0.14, 6.0, tc, 'z', 6)
            sg = -1 if var else 1
            for path in (((0, 0, 2.8), (sg * 1.2, 0.2, 4.2), (sg * 1.9, 0.1, 5.4)), ((0, 0, 3.8), (-sg * 1.3, 0.3, 4.9), (-sg * 1.7, 0.0, 6.0)),
                         ((0, 0, 4.8), (0.3, sg * 1.1, 6.1), (0.5, sg * 1.3, 6.8))):
                mesh_tube(m, list(path), 0.13, tc, 5)
        elif kind == 'bamboo':
            rnd = Rng(17)
            for k in range(6):
                x, y = (rnd() - 0.5) * 2.2, (rnd() - 0.5) * 2.2
                h = 8.0 + rnd() * 4.5
                c = rgbf(shade_rgb(trunk, 0.85 + 0.3 * rnd()))
                m.frustum((x, y, h / 2), 0.12, 0.1, h, c, 'z', 6)
                for z in range(2, int(h), 2):
                    m.frustum((x, y, z), 0.15, 0.15, 0.1, rgbf(shade_rgb(trunk, 0.6)), 'z', 6, False)
                m.sphere((x, y, h), 0.9, rgbf(leaf[k % len(leaf)]), 7, 4, (1.4, 1.0, 0.45))
                m.sphere((x + 0.4, y, h - 2.2), 0.6, rgbf(leaf[(k + 1) % len(leaf)]), 6, 3, (1.4, 1.0, 0.45))
        elif kind == 'mushroom':
            cap = acc[var % len(acc)]
            m.frustum((0, 0, 1.7), 0.62, 0.5, 3.4, rgbf(trunk), 'z', 10)
            m.sphere((0, 0, 3.4), 2.7, rgbf(cap), 12, 6, (1, 1, 0.5))
            m.disc((0, 0, 3.32), 2.5, rgbf(shade_rgb(cap, 0.55)), 'z', 14)
            for (x, y, z) in ((1.2, 0.6, 4.55), (-1.0, 0.9, 4.5), (0.2, -1.3, 4.5), (-0.6, -0.4, 4.75), (1.6, -0.8, 4.1)):
                m.sphere((x, y, z), 0.28, (1, 1, 1, 1), 6, 3, (1, 1, 0.6))
        elif kind == 'coral':
            c = acc[var % len(acc)]
            rnd = Rng(var * 13 + 5)
            for k in range(6):
                x, y = (rnd() - 0.5) * 2.4, (rnd() - 0.5) * 2.4
                h = 1.5 + rnd() * 2.6
                cc = shade_rgb(c, 0.8 + rnd() * 0.4)
                m.frustum((x, y, h / 2), 0.3, 0.24, h, rgbf(cc), 'z', 7)
                m.sphere((x, y, h), 0.32, rgbf(shade_rgb(cc, 1.25)), 6, 4)
        elif kind == 'barrel':
            bc = acc[1] if len(acc) > 1 and acc[1][0] > 150 else (230, 200, 40)
            for (x, y) in ((-0.65, 0.0), (0.65, 0.1), (0.0, 1.0)):
                m.frustum((x, y, 0.8), 0.55, 0.55, 1.6, rgbf(bc), 'z', 10)
                m.frustum((x, y, 0.35), 0.57, 0.57, 0.12, rgbf((40, 40, 40)), 'z', 10)
                m.frustum((x, y, 1.25), 0.57, 0.57, 0.12, rgbf((40, 40, 40)), 'z', 10)
        elif kind == 'pillar':
            pc = rgbf(mix_rgb(rc[0], (235, 230, 215), 0.4))
            h = 8.0 if var == 0 else 4.8
            m.box((0, 0, 0.3), (1.1, 1.1, 0.3), rgbf(mix_rgb(rc[0], (235, 230, 215), 0.3)))
            m.frustum((0, 0, 0.6 + h / 2), 0.78, 0.68, h, pc, 'z', 12)
            if var == 0:
                m.box((0, 0, 0.6 + h + 0.3), (1.0, 1.0, 0.3), pc)
        elif kind == 'haystack':
            hc = (224, 186, 94)
            m.sphere((0, 0, 1.0), 2.0, rgbf(hc), 10, 6, (1, 1, 0.78))
            m.sphere((0.3, -0.2, 1.2), 1.5, rgbf(hc, 1.08), 8, 5, (1, 1, 0.9))
        elif kind == 'windmill':
            wc = rgbf((232, 226, 214))
            m.frustum((0, 0, 5.0), 2.2, 1.4, 10.0, wc, 'z', 10)
            m.frustum((0, 0, 10.8), 1.7, 0.0, 1.8, rgbf((150, 52, 40)), 'z', 10)
            m.box((0, -1.55, 0.9), (0.5, 0.1, 0.9), rgbf((90, 60, 40)))
            bc = rgbf((245, 240, 230))
            m.box((0, -1.6, 9.4), (5.6, 0.08, 0.45), bc)
            m.box((0, -1.6, 9.4), (0.45, 0.08, 5.6), bc)
            m.sphere((0, -1.7, 9.4), 0.35, rgbf((80, 60, 40)), 6, 4)
        elif kind == 'flowers':
            fc = flower[var % len(flower)]
            m.sphere((0, 0, 0.25), 1.9, rgbf(shade_rgb(leaf[1], 0.9)), 9, 4, (1, 1, 0.22))
            rnd = Rng(var * 7 + 3)
            for _ in range(11):
                m.sphere(((rnd() - 0.5) * 3.0, (rnd() - 0.5) * 3.0, 0.6 + rnd() * 0.25), 0.2, rgbf(fc), 5, 3)
        elif kind == 'tombstone':
            gc = rgbf(mix_rgb(rc[0], (150, 150, 155), 0.4))
            if var == 0:
                m.box((0, 0, 0.85), (0.6, 0.16, 0.85), gc)
                m.frustum((0, 0, 1.7), 0.6, 0.6, 0.32, gc, 'y', 10)
            else:
                m.box((0, 0, 1.1), (0.12, 0.12, 1.1), gc)
                m.box((0, 0, 1.5), (0.5, 0.12, 0.12), gc)
            m.box((0, 0.3, 0.05), (0.8, 0.9, 0.05), rgbf(shade_rgb(mix_rgb(rc[0], (150, 150, 155), 0.4), 0.7)))
        elif kind == 'pumpkin':
            pc = (236, 120, 24)
            m.sphere((-0.38, 0, 0.55), 0.55, rgbf(pc, 0.85), 8, 5)
            m.sphere((0.38, 0, 0.55), 0.55, rgbf(pc, 0.85), 8, 5)
            m.sphere((0, 0, 0.6), 0.62, rgbf(pc), 8, 5)
            m.box((0, 0, 1.25), (0.07, 0.07, 0.15), rgbf((70, 110, 40)))
            if night:
                for x in (-0.22, 0.22):
                    g.box((x, -0.6, 0.72), (0.09, 0.02, 0.07), (2.0, 1.7, 0.6, 1))
                g.box((0, -0.6, 0.45), (0.25, 0.02, 0.05), (2.0, 1.7, 0.6, 1))
        elif kind == 'chimney':
            bc = (122, 72, 52)
            m.box((0, 0, 2.5), (4.0, 3.0, 2.5), rgbf(bc))
            m.frustum((1.6, 0, 11.0), 1.0, 0.8, 18.0, rgbf(bc, 0.8), 'z', 10)
            g.frustum((1.6, 0, 19.4), 0.86, 0.86, 0.5, rgbf(acc[0], 1.4), 'z', 10)
            for x in (-2.6, -1.2, 0.2, 1.6, 3.0):
                (g if night else m).box((x, -3.02, 2.8), (0.45, 0.02, 0.6), (2.0, 1.6, 0.8, 1) if night else (0.2, 0.17, 0.15, 1))
        elif kind == 'pyramid':
            pc = mix_rgb(rc[0], (230, 200, 140), 0.35)
            m.frustum((0, 0, 4.5), 9.9, 0.0, 9.0, rgbf(pc), 'z', 4)
        elif kind == 'dome':
            m.sphere((0, 0, 0.2), 5.0, rgbf((170, 220, 255)), 14, 7, (1, 1, 0.58))
            m.frustum((0, 0, 0.25), 5.2, 5.2, 0.5, rgbf((150, 150, 160)), 'z', 16)
            g.box((0, -4.95, 1.0), (1.0, 0.05, 0.8), (2.0, 1.8, 1.0, 1) if night else rgbf((120, 200, 255), 1.4))
        elif kind == 'icespike':
            ic = mix_rgb(th.get('crystal') or (180, 225, 255), (230, 245, 255), 0.4)
            for (x, y, r, h) in ((-0.9, 0.1, 0.7, 4.2), (0.6, -0.3, 0.8, 5.4), (0.0, 0.6, 0.9, 6.0), (1.3, 0.5, 0.5, 3.0)):
                m.frustum((x, y, h / 2), r, 0.0, h, rgbf(ic), 'z', 5)
        elif kind == 'lantern':
            lc = acc[0] if acc else (255, 120, 60)
            m.frustum((0, 0, 1.1), 0.13, 0.13, 2.2, rgbf((110, 110, 112)), 'z', 6)
            m.box((0, 0, 0.1), (0.4, 0.4, 0.1), rgbf((110, 110, 112)))
            g.box((0, 0, 2.5), (0.35, 0.35, 0.35), rgbf(lc, 1.6 if night else 1.0))
            m.frustum((0, 0, 3.05), 0.62, 0.0, 0.5, rgbf((70, 60, 60)), 'z', 6)
        elif kind == 'blocks':
            rnd = Rng(var * 19 + 1)
            z = 0.0
            for k in range(3):
                hx = 1.6 - k * 0.35 + rnd() * 0.2
                hz = 0.55 + rnd() * 0.3
                c = acc[(var + k) % len(acc)]
                ox = (rnd() - 0.5) * 0.4
                m.box((ox, 0, z + hz), (hx, hx * 0.8, hz), rgbf(c))
                for sx in (-0.5, 0.5):
                    m.frustum((ox + sx * hx, 0, z + 2 * hz + 0.1), 0.25, 0.25, 0.2, rgbf(c, 1.15), 'z', 8)
                z += 2 * hz + 0.05
        elif kind == 'dish':
            lc = rgbf((150, 150, 158))
            m.frustum((0, 0, 1.8), 0.15, 0.12, 3.6, lc, 'z', 6)
            m.frustum((0, 0, 4.0), 0.3, 2.3, 1.0, rgbf((235, 238, 245)), 'z', 14, False)
            m.frustum((0, 0, 3.5), 0.3, 0.3, 0.3, lc, 'z', 6)
            m.frustum((0, 0, 4.9), 0.06, 0.06, 1.6, lc, 'z', 5)
            g.sphere((0, 0, 5.75), 0.14, (2.0, 0.4, 0.4, 1), 6, 3)
        elif kind == 'sunflower':
            fc = flower[0]
            for (x, y, h) in ((-0.8, 0.1, 2.8), (0.2, -0.3, 3.3), (0.9, 0.4, 2.5)):
                m.frustum((x, y, h / 2), 0.06, 0.05, h, rgbf((60, 130, 50)), 'z', 5)
                m.box((x + 0.2, y, h * 0.45), (0.25, 0.04, 0.1), rgbf((70, 150, 60)))
                m.disc((x, y - 0.06, h), 0.55, rgbf(fc), 'y', 12)
                m.disc((x, y - 0.08, h), 0.24, rgbf((100, 60, 30)), 'y', 10)
        elif kind == 'cloud':
            c0 = leaf[0] if leaf[0][0] > 200 else (250, 252, 255)
            for (x, y, z, r) in ((-1.0, 0, 1.0, 1.2), (0.6, 0.2, 1.3, 1.5), (0.0, -0.3, 1.9, 1.0), (1.5, -0.1, 0.8, 0.9)):
                m.sphere((x, y, z), r, rgbf(c0), 9, 5)
        # ---- 맵 만들기 장애물/장식 ----
        elif kind == 'cone':
            oc = rgbf((255, 118, 24))
            m.box((0, 0, 0.03), (0.42, 0.42, 0.03), rgbf((40, 40, 44)))
            m.frustum((0, 0, 0.5), 0.3, 0.05, 0.9, oc, 'z', 10)
            g.frustum((0, 0, 0.52), 0.215, 0.165, 0.14, (1.6, 1.6, 1.6, 1), 'z', 10)
            g.frustum((0, 0, 0.74), 0.13, 0.095, 0.1, (1.6, 1.6, 1.6, 1), 'z', 10)
        elif kind == 'drum':
            dc = (36, 120, 220)
            m.frustum((0, 0, 0.72), 0.58, 0.58, 1.44, rgbf(dc), 'z', 12)
            for z in (0.3, 0.72, 1.14):
                m.frustum((0, 0, z), 0.6, 0.6, 0.06, rgbf(dc, 0.6), 'z', 12)
            m.disc((0, 0, 1.445), 0.5, rgbf(dc, 1.2), 'z', 12)
        elif kind == 'crate':
            wc = (192, 140, 78)
            m.box((0, 0, 0.9), (0.9, 0.9, 0.9), rgbf(wc))
            for sx in (-1, 1):
                for sy in (-1, 1):
                    m.box((sx * 0.86, sy * 0.86, 0.9), (0.07, 0.07, 0.92), rgbf(wc, 0.65))
            for z in (0.06, 1.74):
                m.box((0, 0, z), (0.93, 0.93, 0.07), rgbf(wc, 0.7))
        elif kind == 'tires':
            for k in range(3):
                z = 0.28 + k * 0.5
                m.frustum((0, 0, z), 0.95, 0.95, 0.46, rgbf((30, 30, 34)), 'z', 14)
                m.frustum((0, 0, z + 0.235), 0.42, 0.42, 0.02, rgbf((12, 12, 14)), 'z', 10)
                m.frustum((0, 0, z), 0.97, 0.97, 0.08, rgbf((220, 40, 40) if k % 2 == 0 else (235, 235, 235)), 'z', 14)
        elif kind == 'block':
            bc = (226, 226, 230)
            m.box((0, 0, 0.35), (1.15, 0.45, 0.35), rgbf(bc))
            m.box((0, 0, 0.95), (1.15, 0.22, 0.27), rgbf(bc), taper=(1.0, 0.7))
            for x in (-0.8, -0.27, 0.27, 0.8):
                m.box((x, -0.46, 0.6), (0.1, 0.02, 0.45), rgbf((220, 40, 40)))
                m.box((x, 0.46, 0.6), (0.1, 0.02, 0.45), rgbf((220, 40, 40)))
        elif kind == 'lavapillar':
            bc = mix_rgb(rc[0], (34, 28, 30), 0.6)
            m.frustum((0, 0, 0.35), 1.5, 1.4, 0.7, rgbf(bc, 0.8), 'z', 6)
            m.frustum((0, 0, 4.9), 1.15, 0.95, 8.4, rgbf(bc), 'z', 6)
            for k in range(6):
                a = k * 1.047 + 0.3
                z = 1.6 + k * 1.15
                x, y = math.cos(a) * 1.06, math.sin(a) * 1.06
                g.box((x, y, z), (0.12, 0.12, 0.42), (2.4, 0.9, 0.2, 1))
            g.frustum((0, 0, 9.12), 0.88, 0.7, 0.16, (2.6, 1.0, 0.25, 1), 'z', 6)
            g.sphere((0, 0, 9.3), 0.45, (2.8, 1.5, 0.4, 1), 6, 3)
        elif kind == 'volcano':
            vc = mix_rgb(rc[0], (70, 44, 34), 0.55)
            m.frustum((0, 0, 11.0), 22.0, 5.5, 22.0, rgbf(vc), 'z', 14, False)
            m.frustum((0, 0, 21.5), 5.6, 4.2, 1.0, rgbf(vc, 0.7), 'z', 14)
            g.disc((0, 0, 21.9), 4.0, (2.6, 0.9, 0.2, 1), 'z', 14)
            for k in range(5):
                a = k * 1.26 + 0.4
                for j in range(6):
                    t = j / 6.0
                    r = 5.0 + t * 15.0
                    g.box((math.cos(a + t * 0.25) * r, math.sin(a + t * 0.25) * r, 21.2 - t * 20.0), (0.5, 0.5, 1.9), (2.4, 0.8, 0.15, 1))
        return m, (g if g.v else None)

    def _props(self):
        tr = self.track
        protos = {}
        chunks = {}
        holder = NodePath('protos')
        for p in tr.props:
            kind = p['kind']
            nv = PROP_VARS.get(kind, 1)
            var = int(p['r1'] * nv) % nv if nv > 1 else 0
            key = (kind, var)
            pr = protos.get(key)
            if pr is None:
                m, glow = self._proto(kind, var)
                lit = m.attach(holder, 'p_%s_%d' % key)
                lit.setTwoSided(True)
                parts = [lit]
                if glow is not None:
                    gn = glow.attach(holder, 'g_%s_%d' % key)
                    gn.setLightOff()
                    parts.append(gn)
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
            shade = 0.82 + p['r1'] * 0.3 if kind in ('pine', 'roundtree', 'bush', 'rock', 'cactus', 'palm', 'acacia', 'bamboo', 'deadtree', 'flowers') else 1.0
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
        self.spinner = self.root.attachNewNode('spinner')      # 아이템 효과: 스핀/점프
        self.yaw = self.spinner.attachNewNode('yaw')
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
        self.t = 0.0
        self.fx_state = None
        self.bubble = None
        # 마지막으로 노드에 넣은 값 (같으면 다시 넣지 않는다 - 보이는 건 같고 계산만 줄어듦)
        self._sz = self._sh = 0.0
        self._steer_h = 0.0
        self._flame_on = False
        self._label_vis = None
        self._label_sc = None

    def _effects(self, rc, dt):
        """아이템 상태이상 표시: 크기/점프/스핀/무지개(무적)/얼음/유령/방패"""
        self.t += dt
        fxb = rc.fx
        sc = rc.scale
        if abs(sc - 1.0) > 0.01 or self.fx_state is not None:
            self.root.setScale(sc)
        sz = rc.air_y / max(sc, 0.3)
        sh = -math.degrees(rc.spin_ang)
        if sz != self._sz or sh != self._sh:          # 값이 바뀔 때만 (대부분 0 그대로)
            self._sz, self._sh = sz, sh
            self.spinner.setZ(sz)
            self.spinner.setH(sh)
        if fxb & FX_STAR:
            hc = hue_rgb(self.t * 2.2)
            cs = (0.6 + hc[0] / 255.0 * 0.9, 0.6 + hc[1] / 255.0 * 0.9, 0.6 + hc[2] / 255.0 * 0.9, 1.0)
        elif fxb & FX_FREEZE:
            cs = (0.7, 0.95, 1.6, 1.0)
        else:
            cs = None
        ghost = bool(fxb & FX_GHOST)
        state = (cs, ghost)
        if cs is not None or ghost or state != self.fx_state:
            if cs is None and not ghost:
                self.spinner.clearColorScale()
                self.spinner.clearTransparency()
            else:
                c = cs or (1.0, 1.0, 1.0, 1.0)
                self.spinner.setColorScale(c[0], c[1], c[2], 0.35 if ghost else 1.0)
                if ghost:
                    self.spinner.setTransparency(TransparencyAttrib.MAlpha)
                else:
                    self.spinner.clearTransparency()
            self.fx_state = state if (cs is not None or ghost) else None
        if fxb & FX_SHIELD:
            if self.bubble is None:
                m = self.model
                bm = Mesh()
                bm.sphere((0, 0, 0), 1.0, (0.55, 0.88, 1.0, 0.3), 14, 9)
                b = bm.attach(self.spinner, 'bubble')
                b.setTransparency(TransparencyAttrib.MAlpha)
                b.setLightOff()
                b.setTwoSided(True)
                b.setDepthWrite(False)
                b.setBin('fixed', 20)
                r = max(m.L, m.W * 1.4) * 0.72
                b.setScale(r * 0.85, r, r * 0.8)
                b.setPos(0, 0, m.base + m.H * 0.6)
                self.bubble = b
            self.bubble.show()
        elif self.bubble is not None:
            self.bubble.hide()

    def update(self, rc, dt, ds, cam_dist):
        m = self.model
        self._effects(rc, dt)
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
        steer_h = -rc.steer * 24.0
        if steer_h != self._steer_h:
            self._steer_h = steer_h
            for pivot, spin, front in self.wheels:
                spin.setP(deg)
                if front:
                    pivot.setH(steer_h)
        else:
            for pivot, spin, front in self.wheels:
                spin.setP(deg)
        if rc.boosting:
            if not self._flame_on:
                self._flame_on = True
                self.flame.show()
            self.flame.setScale(1, 0.7 + _random.random() * 0.8, 1)
        elif self._flame_on:
            self._flame_on = False
            self.flame.hide()
        lb = self.label
        if lb is not None:
            vis = not (cam_dist < 11 or cam_dist > 220)
            if vis:
                lsc = 0.85 * clamp(cam_dist / 16.0, 0.8, 4.0)
                if lsc != self._label_sc:
                    self._label_sc = lsc
                    lb.setScale(lsc)
            if vis != self._label_vis:
                self._label_vis = vis
                if vis:
                    lb.show()
                else:
                    lb.hide()

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
    """카메라 주변을 도는 날씨 입자 (눈/비/불씨/낙엽/꽃잎/포자/반딧불/재/거품/반짝이/먼지/스프링클)"""

    def __init__(self, app, kind, color=None):
        self.app = app
        self.kind = kind
        spec = WEATHER.get(kind, ((255, 255, 255), 3.0, 1.0, 2))
        self.vy = -spec[1]
        self.drift = spec[2]
        self.n = {'snow': 520, 'rain': 700, 'firefly': 160, 'sparkle': 110, 'dust': 260}.get(kind, 320)
        self.lines = kind == 'rain'
        fmt = GeomVertexFormat.getV3()
        self.vd = GeomVertexData('weather', fmt, Geom.UHDynamic)
        self.vd.setNumRows(self.n * (2 if self.lines else 1))
        rnd = Rng(99)
        pos = [[(rnd() - 0.5) * 160, (rnd() - 0.5) * 160, rnd() * 70, rnd() * 6.28] for _ in range(self.n)]
        # 성분별 목록으로 들고 있다가 리스트 내포로 한꺼번에 계산 -> 정점 버퍼에 통째로 복사 (예전과 같은 좌표)
        self.px = [p[0] for p in pos]
        self.py = [p[1] for p in pos]
        self.pz = [p[2] for p in pos]
        self.ph = [p[3] for p in pos]
        self.kf = [0.6 + (i % 5) * 0.2 for i in range(self.n)]
        nv = self.n * (2 if self.lines else 1)
        try:
            ok = fmt.getArray(0).getStride() == 12           # float32 x 3 (보통의 Panda3D)
        except Exception:
            ok = False
        self.buf = array.array('f', bytes(12 * nv)) if ok else None
        if self.lines:
            prim = GeomLines(Geom.UHStatic)
            for i in range(self.n):
                prim.addVertices(2 * i, 2 * i + 1)
        else:
            prim = GeomPoints(Geom.UHStatic)
            prim.addNextVertices(self.n)
        geom = Geom(self.vd)
        geom.addPrimitive(prim)
        gn = GeomNode('weather')
        gn.addGeom(geom)
        self.np = app.render.attachNewNode(gn)
        c = color or spec[0] or (255, 255, 255)
        self.np.setColor(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, 1)
        self.np.setRenderModeThickness(1.5 if self.lines else (1.8 if kind == 'sparkle' else (3.0 if kind in ('snow', 'dust') else 4.0)))
        self.np.setLightOff()
        self.np.setBin('fixed', 25)
        self.np.setDepthWrite(False)
        self.np.node().setBounds(OmniBoundingVolume())
        self.np.node().setFinal(True)
        self.t = 0.0

    def update(self, dt, cam):
        self.t += dt
        t = self.t
        cx, cy, cz = cam
        sin = math.sin
        if self.kind == 'firefly':
            cos = math.cos
            px = self.px = [x + cos(t * 0.9 + p * 3.0) * dt * 2.0 for x, p in zip(self.px, self.ph)]
            py = self.py = [y + sin(t * 0.8 + p * 2.0) * dt * 2.0 for y, p in zip(self.py, self.ph)]
            pz = [z + sin(t * 0.7 + p * 2.0) * dt * 1.2 for z, p in zip(self.pz, self.ph)]
        else:
            vdt = self.vy * dt
            dr = self.drift
            pz = [z + vdt * k for z, k in zip(self.pz, self.kf)]
            px = self.px = [x + sin(t + p) * dt * dr for x, p in zip(self.px, self.ph)]
            py = self.py
        pz = self.pz = [z + 70 if z < 0 else (z - 70 if z > 70 else z) for z in pz]
        X = [((x - cx + 80) % 160) - 80 + cx for x in px]
        Y = [((y - cy + 80) % 160) - 80 + cy for y in py]
        Z = [z + cz - 25 for z in pz]
        buf = self.buf
        if buf is not None:
            A = array.array
            if self.lines:
                buf[0::6] = A('f', X)
                buf[1::6] = A('f', Y)
                buf[2::6] = A('f', Z)
                buf[3::6] = A('f', [x + 0.12 for x in X])
                buf[4::6] = A('f', Y)
                buf[5::6] = A('f', [z + 1.3 for z in Z])
            else:
                buf[0::3] = A('f', X)
                buf[1::3] = A('f', Y)
                buf[2::3] = A('f', Z)
            try:
                self.vd.modifyArrayHandle(0).copyDataFrom(buf)
                return
            except Exception:
                self.buf = None                  # 아주 오래된 Panda3D: 한 점씩 쓰는 방식으로
        vw = GeomVertexWriter(self.vd, 'vertex')
        lines = self.lines
        for x, y, z in zip(X, Y, Z):
            vw.setData3(x, y, z)
            if lines:
                vw.setData3(x + 0.12, y, z + 1.3)

    def destroy(self):
        self.np.removeNode()


# ============================================================================
#  [PC] 아이템전: 벡터 아이콘 -> 2D 메시 / HUD 슬롯 3칸(키 1·2·3) / 상자·투사체·함정 3D / 화면 효과
# ============================================================================
_ICON_PROTOS = {}


def _icon_mesh(it):
    """코어 ICONS 정의를 aspect2d 용 평면 메시로 (x 오른쪽, z 위). 그림자 한 번 + 본체 한 번."""
    item = ITEMS[it]
    m = Mesh()
    nrm = (0.0, -1.0, 0.0)

    def V(x, y):
        return (x, 0.0, -y)

    def col(ci):
        c = icon_color(item, ci)
        return (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, 1.0)

    def fan(cx, cy, pts, c):
        ctr = m.add(V(cx, cy), nrm, c)
        idx = [m.add(V(x, y), nrm, c) for x, y in pts]
        n = len(idx)
        for i in range(n):
            m.tri(ctr, idx[i], idx[(i + 1) % n])

    def ellipse(cx, cy, rx, ry, c, seg=22):
        fan(cx, cy, [(cx + math.cos(TAU * i / seg) * rx, cy + math.sin(TAU * i / seg) * ry) for i in range(seg)], c)

    def ring(cx, cy, r0, r1, c, seg=26):
        for i in range(seg):
            a0, a1 = TAU * i / seg, TAU * (i + 1) / seg
            p = [m.add(V(cx + math.cos(a) * r, cy + math.sin(a) * r), nrm, c) for a, r in ((a0, r0), (a0, r1), (a1, r1), (a1, r0))]
            m.tri(p[0], p[1], p[2])
            m.tri(p[0], p[2], p[3])

    def line(pts, w, c):
        h = w / 2.0
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            dx, dy = x1 - x0, y1 - y0
            l = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / l * h, dx / l * h
            p = [m.add(V(x, y), nrm, c) for x, y in ((x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny))]
            m.tri(p[0], p[1], p[2])
            m.tri(p[0], p[2], p[3])
        for x, y in pts:
            ellipse(x, y, h, h, c, 10)
    for shadow in (True, False):
        off = 0.07 if shadow else 0.0
        for prim in ICONS[item['icon']]:
            t = prim[0]
            c = (0.0, 0.0, 0.0, 0.45) if shadow else col(prim[-1])
            if t == 'c':
                ellipse(prim[1] + off, prim[2] + off, prim[3], prim[3], c)
            elif t == 'e':
                ellipse(prim[1] + off, prim[2] + off, prim[3], prim[4], c)
            elif t == 'r':
                ring(prim[1] + off, prim[2] + off, max(0.0, prim[3] - prim[4] / 2.0), prim[3] + prim[4] / 2.0, c)
            elif t == 'p':
                pts = prim[1]
                cx = sum(p[0] for p in pts) / len(pts)
                cy = sum(p[1] for p in pts) / len(pts)
                fan(cx + off, cy + off, [(x + off, y + off) for x, y in pts], c)
            elif t == 'l':
                line([(x + off, y + off) for x, y in prim[1]], prim[2], c)
    np_ = NodePath(m.node('icon%d' % it))
    np_.setTwoSided(True)
    np_.setTransparency(TransparencyAttrib.MAlpha)
    np_.setLightOff()
    return np_


def icon_node(parent, it, scale):
    proto = _ICON_PROTOS.get(it)
    if proto is None:
        proto = _ICON_PROTOS[it] = _icon_mesh(it)
    n = proto.copyTo(parent)
    n.setScale(scale)
    return n


class ItemHUD(object):
    """화면 위 가운데: 아이템 슬롯 3칸 + 이름 + 상태 + 미사일 경고"""

    def __init__(self, app):
        self.app = app
        a = app
        self.root = a.a2dTopCenter.attachNewNode('itemhud')
        self.slots = []
        self._txt = {}
        cm = CardMaker('slot')
        cm.setFrame(-0.1, 0.1, -0.1, 0.1)
        kw = dict(font=a.font, mayChange=True, shadow=(0, 0, 0, 1))
        for i in range(ITEM_SLOTS):
            fr = self.root.attachNewNode('slot%d' % i)
            fr.setPos((i - 1) * 0.25, 0, -0.135)
            border = fr.attachNewNode(cm.generate())
            border.setScale(1.08)
            border.setTransparency(TransparencyAttrib.MAlpha)
            bg = fr.attachNewNode(cm.generate())
            bg.setColor(0.06, 0.09, 0.19, 0.88)
            bg.setTransparency(TransparencyAttrib.MAlpha)
            holder = fr.attachNewNode('icon')
            key = OnscreenText(text=str(i + 1), parent=fr, pos=(-0.082, 0.06), scale=0.042, fg=(1, 0.86, 0.47, 1), align=TextNode.ALeft, **kw)
            uses = OnscreenText(text='', parent=fr, pos=(0.09, -0.088), scale=0.042, fg=(1, 1, 1, 1), align=TextNode.ARight, **kw)
            name = OnscreenText(text='', parent=fr, pos=(0, -0.152), scale=0.034, fg=(0.9, 0.93, 1, 1), align=TextNode.ACenter, **kw)
            self.slots.append({'fr': fr, 'border': border, 'icon': holder, 'key': key, 'uses': uses, 'name': name, 'cur': None})
        self.status = OnscreenText(text='', parent=self.root, pos=(0, -0.33), scale=0.046, fg=(1, 0.95, 0.75, 1), align=TextNode.ACenter, **kw)
        self.warn = OnscreenText(text='', parent=self.root, pos=(0, -0.4), scale=0.065, fg=(1, 0.3, 0.3, 1), align=TextNode.ACenter, **kw)
        self.root.hide()
        self.visible = False

    def _set(self, node, text):
        if self._txt.get(id(node)) != text:
            self._txt[id(node)] = text
            node.setText(text)

    def show(self, flag):
        self.visible = flag
        if flag:
            self.root.show()
        else:
            self.root.hide()

    def reset(self):
        for sl in self.slots:
            sl['cur'] = None
            for c in sl['icon'].getChildren():
                c.removeNode()

    def update(self, race, t):
        rc = race.local
        for i, sl in enumerate(self.slots):
            it = rc.items[i]
            roll = rc.roll[i]
            if it is None:
                want = None
            elif roll > 0:
                want = ('r', (int(t * 16) * 37 + i * 11) % ITEM_COUNT)
            else:
                want = ('i', it)
            if want != sl['cur']:
                sl['cur'] = want
                for c in sl['icon'].getChildren():
                    c.removeNode()
                if want is not None:
                    icon_node(sl['icon'], want[1], 0.082 if want[0] == 'i' else 0.066)
            ready = it is not None and roll <= 0
            if ready:
                k = 0.75 + 0.25 * math.sin(t * 6.0 + i)
                sl['border'].setColor(1.0 * k, 0.78 * k, 0.27, 0.95)
            else:
                sl['border'].setColor(0.32, 0.36, 0.5, 0.8)
            self._set(sl['uses'], ('x%d' % rc.uses[i]) if ready and rc.uses[i] > 1 else '')
            name = item_name(it, LANG) if ready else ''
            if self._txt.get(id(sl['name'])) != name:
                self._set(sl['name'], name)
                try:
                    w = sl['name'].textNode.calcWidth(name) if name else 0.0
                except Exception:
                    w = 0.0
                sl['name'].setScale(min(0.034, 0.235 / w) if w > 0 else 0.034)     # 칸 폭에 맞게 줄이기
        st = fx_status(rc.sim, LANG)
        self._set(self.status, '    '.join(s_[0] for s_ in st[:4]))
        thr = incoming_threat(race)
        self._set(self.warn, T('! 미사일 접근 !', '! INCOMING !') if (thr is not None and int(t * 6) % 2 == 0) else '')

    def destroy(self):
        self.root.removeNode()


class ItemWorld(object):
    """아이템 상자(무지개 큐브 + ?) / 투사체 / 함정 3D 표시"""

    def __init__(self, app, race, parent):
        self.app = app
        self.race = race
        self.items = race.items
        self.root = parent.attachNewNode('items3d')
        self.protos = {}
        self.ent_nodes = {}
        self.t = 0.0
        cube = Mesh()
        cube.box((0, 0, 0), (0.8, 0.8, 0.8), (1, 1, 1, 1))
        cube_np = NodePath(cube.node('ibox'))
        tn = TextNode('q')
        tn.setText('?')
        tn.setAlign(TextNode.ACenter)
        tn.setTextColor(1, 1, 1, 1)
        tn.setShadow(0.05, 0.05)
        tn.setShadowColor(0, 0, 0, 1)
        if app.font is not None:
            tn.setFont(app.font)
        self.qtext = tn
        self.boxes = []
        for b in self.items.boxes:
            n = self.root.attachNewNode('box')
            c = cube_np.copyTo(n)
            q = n.attachNewNode(tn.generate())
            q.setScale(1.3)
            q.setPos(0, 0, -0.45)
            q.setBillboardPointEye(1.3)          # 큐브 앞쪽(카메라 쪽)으로 띄워서 보이게
            q.setLightOff()
            n.setPos(*PV(b['x'], b['y'], b['z']))
            self.boxes.append((n, c))
        self.box_vis = [True] * len(self.boxes)

    def _proto(self, e):
        it = ITEMS[e.item]
        key = (e.kind, it['id'])
        p = self.protos.get(key)
        if p is not None:
            return p
        c1, c2 = rgbf(it['c1']), rgbf(it['c2'])
        m = Mesh()
        g = Mesh()
        icon = it['icon']
        k = e.kind
        prm = it['p']
        shape = prm.get('shape')
        ring = None
        alpha = False
        if k == 'trap':
            r = float(prm.get('r', 1.2))
            if shape == 'banana':
                b = 1.9 if prm.get('big') else 1.0
                for a in (-1.05, -0.35, 0.35, 1.05):
                    m.box((math.sin(a) * 0.5 * b, (math.cos(a) * 0.5 - 0.5) * b, 0.16 * b), (0.15 * b, 0.2 * b, 0.13 * b), c1)
                m.box((0, 0.05 * b, 0.2 * b), (0.06 * b, 0.12 * b, 0.06 * b), rgbf((110, 76, 30)))
            elif shape in ('oil', 'glue'):
                m.frustum((0, 0, 0.04), r, r * 0.95, 0.05, rgbf((22, 20, 30)) if shape == 'oil' else c1, 'z', 16)
                m.frustum((r * 0.3, r * 0.25, 0.08), r * 0.2, r * 0.18, 0.02, c2, 'z', 10)
            elif shape == 'ice':
                m.frustum((0, 0, 0.05), r, r, 0.06, c1, 'z', 6)
                m.frustum((0, 0, 0.09), r * 0.55, r * 0.55, 0.02, c2, 'z', 6)
            elif shape == 'spikes':
                m.box((0, 0, 0.04), (r, 0.4, 0.04), c2)
                for i in range(6):
                    m.frustum((-r + (i + 0.5) * 2 * r / 6.0, 0, 0.3), 0.16, 0.0, 0.45, c1, 'z', 4)
            elif shape == 'mine':
                m.frustum((0, 0, 0.1), 0.85, 0.7, 0.2, c1, 'z', 12)
                m.frustum((0, 0, 0.22), 0.5, 0.45, 0.06, rgbf((110, 116, 130)), 'z', 12)
                g.sphere((0, 0, 0.32), 0.17, (1.8, 0.2, 0.2, 1), 8, 5)
            elif shape == 'fakebox':
                m.box((0, 0, 0.85), (0.8, 0.8, 0.8), (1, 1, 1, 1))
            elif shape == 'wall':
                for (cx, cy, cz, hx, hy, hz, col, tx, ty, gl) in wall_boxes(it):
                    m.box((cx, cz, cy), (hx, hz, hy), rgbf(col))
            elif shape == 'portal':
                g.annulus((0, 0, 1.4), 1.0, 1.35, rgbf(it['c1'], 1.6), 'y', 22)
                g.annulus((0, 0, 1.4), 0.55, 0.75, rgbf(it['c2'], 1.3), 'y', 18)
        elif k == 'tornado':
            for i in range(5):
                m.frustum((0, 0, 0.55 + i * 1.12), 0.9 + i * 0.72, 1.25 + i * 0.75, 0.9, (c1 if i % 2 == 0 else c2)[:3] + (0.72,), 'z', 12, False)
            alpha = True
        elif k == 'meteor':
            g.sphere((0, 0, 0), 1.6, rgbf(it['c1'], 1.7), 10, 7)
            g.frustum((0, 0, 4.0), 1.1, 0.0, 7.0, (2.0, 1.4, 0.4, 0.8), 'z', 10, False)
            rm = Mesh()
            rr = float(prm.get('r', 5.0))
            rm.annulus((0, 0, 0), rr - 0.3, rr, (2.0, 0.4, 0.2, 1), 'z', 28)
            ring = rm
        elif k == 'seeker':
            m.sphere((0, 0, 0), 1.0, c1, 12, 8)
            m.box((1.45, 0, 0.3), (0.9, 0.35, 0.05), c2)
            m.box((-1.45, 0, 0.3), (0.9, 0.35, 0.05), c2)
        elif k == 'bomb':
            m.sphere((0, 0, 0), 0.8, c1, 12, 8)
            m.box((0, 0, 0.85), (0.12, 0.12, 0.15), rgbf((110, 116, 130)))
            g.sphere((0, 0, 1.08), 0.22, rgbf(it['c2'], 1.7), 8, 5)
        elif icon == 'laser':
            g.box((0, -3.5, 0), (0.14, 4.0, 0.14), rgbf(it['c1'], 1.8))
            g.box((0, -3.5, 0), (0.06, 4.05, 0.06), (2.0, 2.0, 2.0, 1))
        elif icon in ('missile', 'arrow', 'drone', 'bird', 'shuriken', 'boomerang'):
            for (cx, cy, cz, hx, hy, hz, col, tx, ty, gl) in ent_boxes(it):
                (g if gl else m).box((cx, cz, cy), (hx, hz, hy), rgbf(col, 1.6 if gl else 1.0), taper=(tx, ty) if (tx != 1 or ty != 1) else None)
        elif icon == 'bee':
            for i in range(5):
                a = TAU * i / 5
                m.sphere((math.cos(a) * 0.9, math.sin(a) * 0.9, math.sin(a * 2) * 0.3), 0.32, c1, 8, 5)
                m.box((math.cos(a) * 0.9, math.sin(a) * 0.9, math.sin(a * 2) * 0.3 + 0.28), (0.25, 0.05, 0.02), (1, 1, 1, 1))
        else:
            m.sphere((0, 0, 0), 0.75, c1, 12, 8)
            if icon == 'target':
                m.annulus((0, 0, 0), 0.76, 0.86, c2, 'z', 18)
            elif icon in ('ball', 'balloon', 'pie'):
                m.sphere((-0.25, -0.25, 0.35), 0.2, c2, 6, 4)
        p = NodePath('proto')
        if m.v:
            mn = m.attach(p, 'm')
            mn.setTwoSided(True)
        if g.v:
            gn = g.attach(p, 'g')
            gn.setLightOff()
            gn.setTwoSided(True)
        if ring is not None:
            rn = ring.attach(p, 'ring')
            rn.setLightOff()
            rn.setTwoSided(True)
        if alpha:
            p.setTransparency(TransparencyAttrib.MAlpha)
        self.protos[key] = p
        return p

    def update(self, dt):
        self.t += dt
        t = self.t
        vis = self.box_vis
        cp = getattr(self.app, 'cam_pos', None)
        cf = getattr(self.app, 'cam_fwd', None)
        for i, (b, (n, c)) in enumerate(zip(self.items.boxes, self.boxes)):
            on = not (b['t'] > 0)
            if on != vis[i]:                     # 보이기/숨기기는 바뀔 때만
                vis[i] = on
                if on:
                    n.show()
                else:
                    n.hide()
            if not on:
                continue
            # 카메라 뒤(3m 이상)에 있는 상자는 어차피 화면에 안 그려진다 -> 움직임 갱신을 건너뜀.
            # 다시 앞으로 오면 그 프레임에 바로 최신 위치/색으로 갱신되므로 보이는 그림은 같다.
            if cp is not None and (b['x'] - cp[0]) * cf[0] + (-b['z'] - cp[1]) * cf[1] + (b['y'] - cp[2]) * cf[2] < -3.0:
                continue
            n.setPos(*PV(b['x'], b['y'] + math.sin(t * 3.0 + b['ph']) * 0.18, b['z']))
            c.setH(math.degrees(b['ph'] + t * 1.8))
            hc = hue_rgb(t * 0.25 + b['ph'] / TAU)
            c.setColorScale(hc[0] / 255.0, hc[1] / 255.0, hc[2] / 255.0, 1)
        alive = set()
        for e in self.items.ents:
            if e.dead:
                continue
            alive.add(e.eid)
            n = self.ent_nodes.get(e.eid)
            if n is None:
                n = self.ent_nodes[e.eid] = self._proto(e).copyTo(self.root)
            self._place(e, n, t)
        for eid in [k for k in self.ent_nodes if k not in alive]:
            self.ent_nodes.pop(eid).removeNode()

    def _place(self, e, n, t):
        it = ITEMS[e.item]
        k = e.kind
        if k == 'trap':
            n.setPos(*PV(e.x, e.gy + 0.02, e.z))
            n.setH(math.degrees(e.h) + 180)
            if it['p'].get('shape') == 'fakebox':
                hc = hue_rgb(t * 0.25 + 0.5)
                n.setColorScale(hc[0] / 255.0, hc[1] / 255.0, hc[2] / 255.0, 1)
                n.setH(-t * 100.0)
            return
        n.setPos(*PV(e.x, e.y, e.z))
        icon = it['icon']
        if k == 'tornado' or icon in ('shuriken', 'boomerang', 'bee'):
            n.setH((t * 700.0) % 360.0)
        else:
            n.setH(math.degrees(e.h) + 180)
        if k == 'meteor':
            r = n.find('ring')
            if not r.isEmpty():
                r.setZ(e.gy - e.y + 0.15)
                r.setH(-n.getH())
        elif k == 'bomb' and e.state == 1:
            g = n.find('g')
            if not g.isEmpty():
                blink = int(t * (6 + e.age * 12)) % 2 == 0
                g.setColorScale((1.6, 0.2, 0.2, 1) if blink else (1, 1, 1, 1))

    def destroy(self):
        self.root.removeNode()
        self.ent_nodes = {}


class ScreenFxPC(object):
    """먹물(시야 가림) 얼룩 + 번개 번쩍임 (HUD 보다 아래 그려짐)"""

    def __init__(self, app):
        self.app = app
        self.root = app.aspect2d.attachNewNode('screenfx')
        self.root.setBin('background', 10)
        self.root.setDepthWrite(False)
        self.root.setDepthTest(False)
        tex = shared_tex('blob', lambda: tex_glow('blob', 64, 1.0))
        cm = CardMaker('ink')
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        self.ink = self.root.attachNewNode('ink')
        rnd = Rng(4321)
        for _ in range(9):
            c = self.ink.attachNewNode(cm.generate())
            c.setTexture(tex)
            c.setColor(0.05, 0.04, 0.1, 1)
            c.setPos((rnd() - 0.5) * 2.6, 0, (rnd() - 0.5) * 1.5)
            c.setScale(0.7 + rnd() * 0.8)
        self.ink.setTransparency(TransparencyAttrib.MAlpha)
        self.ink.hide()
        cf = CardMaker('flash')
        cf.setFrame(-3, 3, -2, 2)
        self.flash_np = self.root.attachNewNode(cf.generate())
        self.flash_np.setTransparency(TransparencyAttrib.MAlpha)
        self.flash_np.hide()
        self.flash = 0.0
        self.flash_col = (1, 1, 1)

    def update(self, blind_t, dt):
        if blind_t > 0:
            self.ink.show()
            self.ink.setAlphaScale(clamp(blind_t / 1.2, 0.0, 1.0) * 0.96)
        else:
            self.ink.hide()
        if self.flash > 0:
            self.flash_np.show()
            c = self.flash_col
            self.flash_np.setColor(c[0], c[1], c[2], clamp(self.flash * 1.6, 0.0, 0.66))
            self.flash = max(0.0, self.flash - dt)
        else:
            self.flash_np.hide()

    def clear(self):
        self.flash = 0.0
        self.ink.hide()
        self.flash_np.hide()


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
        self._v = None              # 마지막으로 넣은 값/색/표시 상태 (같으면 다시 넣지 않음)
        self._col = tuple(color)
        self._shown = True
        self.set(0.0)

    def set(self, v, color=None):
        v = clamp(v, 0.0, 1.0)
        if v != self._v:
            self._v = v
            self.fill.setScale(max(0.0001, self.w * v), 1, self.h)
        if color and color != self._col:
            self._col = color
            self.fill.setColor(*color)

    def show(self, flag=True):
        flag = bool(flag)
        if flag != self._shown:
            self._shown = flag
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
        self._txt = {}

    def _set(self, node, text):
        """글자가 바뀔 때만 setText (매 프레임 글자 메시를 다시 만들면 느려짐)"""
        if self._txt.get(id(node)) != text:
            self._txt[id(node)] = text
            node.setText(text)

    def set_item_mode(self, on):
        self.toast.setPos(0, 0.5 if on else 0.62)

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
        self._dot_st = [None] * len(self.dots)

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
        ps = str(rank.index(loc) + 1)
        if self._txt.get(id(self.pos)) != ps:
            self.tot.setPos(0.28 + 0.12 * (len(ps) - 1), -0.2)
        self._set(self.pos, ps)
        self._set(self.tot, '/%d' % len(race.racers))
        self._set(self.lap, 'LAP %d/%d' % (min(race.laps, sim.lap), race.laps))
        self._set(self.time, fmt_time(max(0.0, race.t)))
        self._set(self.spd, str(int(sim.speed * 3.6)))
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
                me = r is loc
                key = ('%d  %s' % (i + 1, r.name)) + ('\x01' if me else '')
                if self._txt.get(id(t)) != key:
                    self._txt[id(t)] = key
                    t.setText('%d  %s' % (i + 1, r.name))
                    t.setFg((1, 0.72, 0.15, 1) if me else (1, 1, 1, 1))
            else:
                self._set(t, '')
        # 카운트다운 / 알림
        if race.phase == 'count':
            n = int(math.ceil(max(0.0, race.count_left)))
            self._set(self.center, str(n) if 1 <= n <= 3 else '')
        elif now > self.center_until:
            self._set(self.center, '')
        if now > self.toast_until:
            self._set(self.toast, '')
        self._set(self.wrong, T('역주행!', 'WRONG WAY!') if (sim.wrong_way and race.phase == 'run' and not loc.finished) else '')
        # 미니맵
        if self.mini_np is not None:
            st = self._dot_st
            nr = len(race.racers)
            for i, d in enumerate(self.dots):
                if i < nr:
                    rc = race.racers[i]
                    x, z = self.mm_xy(rc.x, rc.z)
                    d.setPos(x, 0, z)
                    look = (rc is loc, rc.kind)
                    if st[i] != look:                # 색/크기/표시는 바뀔 때만
                        st[i] = look
                        d.setColor(*((1, 0.69, 0.13, 1) if rc is loc else ((1, 0.43, 0.43, 1) if rc.kind == 'bot' else (0.35, 0.9, 1, 1))))
                        d.setScale(1.7 if rc is loc else 1.0)
                        d.show()
                elif st[i] is not False:
                    st[i] = False
                    d.hide()

    def say(self, text, secs=1.2, big=False, color=(1, 0.8, 0.27, 1)):
        if big:
            self._set(self.center, text)
            self.center_until = time.time() + secs
        else:
            self._set(self.toast, text)
            self.toast.setFg(color)
            n = len(text)
            self.toast.setScale(0.1 if n <= 40 else max(0.05, 0.1 * 40.0 / n))      # 긴 문장은 글자를 줄여서 화면 안에
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
                'iroll': synth(1300, 30, 0.12, 'square'), 'iget': synth(880, 150, 0.26, 'tri', 1.5), 'iuse': synth_noise(220, 0.3, True),
                'ihit': synth(190, 280, 0.45, 'square', 0.4), 'iboom': synth_noise(650, 0.55), 'izap': synth(1500, 320, 0.25, 'square', 0.25),
                'iblock': synth(1250, 170, 0.26, 'tri', 1.2),
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


ITEM_KEYS_PC = {'1': 0, '2': 1, '3': 2, 'face_x': 0, 'face_y': 1, 'face_b': 2}


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
        self.item_hud = ItemHUD(self)
        self.screen_fx = ScreenFxPC(self)
        self.item_world = None
        self.brake_held = False
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
        self.store = MapStore()            # 내가 만든 맵 목록
        self.maker = PCMapMaker(self)      # 맵 만들기 편집기
        self.test_map = None               # 편집기 '시험 주행' 중인 맵
        self.sel_cmap = 0
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
                 'r', 'm', 'enter', 'escape', 'f11', 'backspace', 't', '1', '2', '3', 'face_x', 'face_y', 'face_b', 'z', 'f']
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
        if self.scene == 'editor':
            self.maker.on_key(k)
            return
        if self.scene == 'race':
            if k in ITEM_KEYS_PC:
                self.use_item(ITEM_KEYS_PC[k])
            elif k == 'r' and self.race:
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
                fa, ti_, mi_ = biome_parts(self.sel_map)
                self.sel_map = biome_map(fa + 1, ti_, mi_)
                self.build_solo()
                return
        self.menu.key(k, self.mult())

    def back(self):
        sc = self.scene
        if sc == 'menu':
            self.userExit()
        elif sc in ('solo', 'garage', 'settings', 'multi', 'maps'):
            self.profile.save()
            self.go('menu')
        elif sc == 'mapitem':
            self.go('maps')
        elif sc == 'editor':
            self.maker.try_exit()
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
        if self.item_world is not None:
            self.item_world.destroy()
            self.item_world = None
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
        if scene != 'editor':
            self.maker.leave_ui()
        if scene != 'race':
            self.hud.show(False)
            self.item_hud.show(False)
            self.screen_fx.clear()
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
        elif scene == 'maps':
            self.build_maps()
        elif scene == 'mapitem':
            self.build_mapitem()
        elif scene == 'editor':
            self.maker.enter()

    def build_main(self):
        self.menu.clear_extra()
        rows = [self.R(T('솔로 레이스', 'Solo race'), lambda: self.go('solo'), kind='primary', id='solo'),
                self.R(T('WiFi 멀티플레이', 'WiFi multiplayer'), lambda: self.go('multi'), kind='primary', id='multi'),
                self.R(T('맵 만들기 (내 맵 %d개)' % len(self.store.maps), 'Map maker (%d maps)' % len(self.store.maps)), lambda: self.go('maps'), id='maps'),
                self.R(T('차고 (카트 꾸미기)', 'Garage (customize)'), lambda: self.go('garage'), id='garage'),
                self.R(T('설정', 'Settings'), lambda: self.go('settings'), id='settings'),
                self.R(T('종료', 'Quit'), self.userExit, id='quit')]
        if self.err:
            rows.append(self.I(self.err, (1, 0.5, 0.5, 1)))
        rows.append(self.I('%s  #%d' % (kart_name(self.profile['kart'], LANG), int(self.profile['kart']) + 1), scale=0.045))
        self.menu.set('TURBO KART 3D', rows, T('맵·바이옴 1000종 · 카트 100,000종 · 아이템 100종 · WiFi 멀티', '1000 maps & biomes · 100,000 karts · 100 items · WiFi multiplayer'), T('↑↓ 선택   Enter 확인   F11 전체화면', 'Up/Down select   Enter OK   F11 fullscreen'))

    # ---- 솔로 ----
    def draw_outline(self, mid):
        self.menu.clear_extra()
        try:
            tr = Track(mid, True)
        except Exception:
            return
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

    def custom_rows(self, editable=True):
        """'내가 만든 맵' 고르기 행 (←→ 로 바꾸기). 반환: (행 목록, 고른 맵 또는 None)"""
        maps = self.store.maps
        if not maps:
            return [self.I(T('아직 만든 맵이 없어요 -> 메뉴의 [맵 만들기]', 'No custom maps yet -> Map maker'), (1, 0.75, 0.5, 1)),
                    self.R(T('맵 만들기로 가기', 'Open map maker'), lambda: self.go('maps'), id='gomaps')], None
        i = max(0, self.store.index(self.profile['cmap']))
        d = maps[i]

        def cm(dd):
            def f(m=1):
                j = (self.store.index(self.profile['cmap']) + dd) % len(self.store.maps)
                self.profile['cmap'] = self.store.maps[j]['uid']
                self.profile.save()
                self.rebuild_scene()
            return f
        self.profile['cmap'] = d['uid']
        rows = [self.R(u'%s  < \u2605 %s  (%d/%d) >' % (T('내 맵', 'My map'), d['name'], i + 1, len(maps)), None, cm(-1), cm(1), id='cmap', enabled=editable)]
        return rows, d

    def rebuild_scene(self):
        if self.scene == 'solo':
            self.build_solo()
        elif self.scene == 'lobby':
            self._lobby_sig = None

    def build_solo(self):
        if self.profile['map_src'] == 'custom':
            return self.build_solo_custom()
        mid = self.sel_map = wrap_map(self.sel_map)
        info = map_info(mid)
        name = info['name'] if LANG == 'ko' else info['name_en']
        theme = info['theme_name'] if LANG == 'ko' else info['theme_en']

        def chg(d):
            def f(m=1):
                self.sel_map = wrap_map(self.sel_map + d * m)
                self.build_solo()
            return f

        def setpart(which, d):
            def f(m=1):
                fa, ti_, mi_ = biome_parts(self.sel_map)
                if which == 0:
                    fa += d
                elif which == 1:
                    ti_ += d
                else:
                    mi_ += d
                self.sel_map = biome_map(fa, ti_, mi_)
                self.build_solo()
            return f
        fam = biome_parts(mid)[0]
        fname, tname, moodname = biome_part_names(mid, LANG)

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

        def mode(m=1):
            self.profile['mode'] = 'speed' if self.profile['mode'] == 'item' else 'item'
            self.profile.save()
            self.build_solo()
        mname = T('아이템전 (아이템 100종)', 'Item battle (100 items)') if self.profile['mode'] == 'item' else T('스피드전', 'Speed race')

        def src(m=1):
            self.profile['map_src'] = 'custom'
            self.profile.save()
            self.build_solo()
        rows = [self.R('%s  < %s >' % (T('모드', 'Mode'), mname), mode, mode, mode, id='mode'),
                self.R('%s  < %s >' % (T('맵 종류', 'Maps'), T('기본 맵 1000개', 'Built-in 1000')), src, src, src, id='src'),
                self.R('%s  < #%d / %d >' % (T('맵', 'Map'), mid, MAP_COUNT), typemap, chg(-1), chg(1), id='map'),
                self.R('%s  < %s (%d/%d) >' % (T('바이옴', 'Biome'), fname, fam + 1, BIOME_FAMILIES), None, setpart(0, -1), setpart(0, 1), id='theme'),
                self.R('%s  < %s >' % (T('시간대', 'Time'), tname), None, setpart(1, -1), setpart(1, 1), id='time'),
                self.R('%s  < %s >' % (T('색감', 'Mood'), moodname), None, setpart(2, -1), setpart(2, 1), id='mood'),
                self.R('%s  < %d >' % (T('바퀴 수', 'Laps'), int(self.profile['laps'])), None, lap(-1), lap(1), id='laps'),
                self.R('%s  < %d >' % (T('AI 상대', 'AI rivals'), int(self.profile['bots'])), None, bots(-1), bots(1), id='bots'),
                self.R(T('출발!', 'START!'), start, kind='primary', id='start'),
                self.R(T('뒤로', 'Back'), lambda: self.back(), id='back')]
        self.menu.set(T('솔로 레이스', 'Solo race'), rows, '%s  ·  %s' % (name, theme),
                      T('←→ ±1   Shift ±10   Ctrl ±100   R 랜덤   T 바이옴   Enter(맵) 번호 입력', 'Left/Right ±1   Shift ±10   Ctrl ±100   R random   T biome   Enter on map: type number'))
        self.draw_outline(mid)

    def build_solo_custom(self):
        def mode(m=1):
            self.profile['mode'] = 'speed' if self.profile['mode'] == 'item' else 'item'
            self.profile.save()
            self.build_solo()

        def src(m=1):
            self.profile['map_src'] = 'builtin'
            self.profile.save()
            self.build_solo()

        def lap(dd):
            def f(m=1):
                self.profile['laps'] = int(clamp(int(self.profile['laps']) + dd, 1, 10))
                self.build_solo()
            return f

        def bots(dd):
            def f(m=1):
                self.profile['bots'] = int(clamp(int(self.profile['bots']) + dd, 0, 11))
                self.build_solo()
            return f

        def start():
            self.profile.save()
            self.start_solo()
        mname = T('아이템전 (아이템 100종)', 'Item battle (100 items)') if self.profile['mode'] == 'item' else T('스피드전', 'Speed race')
        crows, d = self.custom_rows()
        rows = [self.R('%s  < %s >' % (T('모드', 'Mode'), mname), mode, mode, mode, id='mode'),
                self.R('%s  < %s >' % (T('맵 종류', 'Maps'), T('내가 만든 맵 (%d)' % len(self.store.maps), 'My maps (%d)' % len(self.store.maps))), src, src, src, id='src')]
        rows += crows
        if d is not None:
            rows.append(self.R(T('이 맵 편집하기', 'Edit this map'), lambda: self.maker.open(d, d['uid']), id='edit'))
        rows += [self.R('%s  < %d >' % (T('바퀴 수', 'Laps'), int(self.profile['laps'])), None, lap(-1), lap(1), id='laps'),
                 self.R('%s  < %d >' % (T('AI 상대', 'AI rivals'), int(self.profile['bots'])), None, bots(-1), bots(1), id='bots')]
        if d is not None:
            rows.append(self.R(T('출발!', 'START!'), start, kind='primary', id='start'))
        rows.append(self.R(T('뒤로', 'Back'), lambda: self.back(), id='back'))
        sub = ''
        if d is not None:
            th = biome(d['look'])
            sub = u'\u2605 %s  ·  %s' % (d['name'], th['name'] if LANG == 'ko' else th['en'])
        self.menu.set(T('솔로 레이스', 'Solo race'), rows, sub, T('←→ 값 변경   Enter 확인', 'Left/Right change   Enter OK'))
        if d is not None:
            self.draw_outline(d)
        else:
            self.menu.clear_extra()

    # ---- 맵 만들기 (목록) ----
    def build_maps(self):
        def new():
            n = len(self.store.maps) + 1
            self.maker.open(cmap_new(T('나의 맵 %d' % n, 'My map %d' % n), int(self.profile['map'])), None)

        def imp_d(dd):
            def f(m=1):
                self.import_mid = wrap_map(getattr(self, 'import_mid', 1) + dd * m)
                self.build_maps()
            return f

        def imp():
            mid = getattr(self, 'import_mid', 1)
            self.maker.open(cmap_from_builtin(mid, map_info(mid)['name' if LANG == 'ko' else 'name_en']), None)
        rows = [self.R(T('+ 새 맵 만들기', '+ New map'), new, kind='primary', id='new'),
                self.R('%s  < #%d >' % (T('기본 맵 코스로 시작', 'Start from built-in map'), getattr(self, 'import_mid', 1)), imp, imp_d(-1), imp_d(1), id='imp')]
        for i, d in enumerate(self.store.maps[:14]):
            def pick(uid=d['uid']):
                self.sel_cmap_uid = uid
                self.go('mapitem')
            rows.append(self.R(u'\u2605 %s   (%d)' % (d['name'], len(d['objs'])), pick, id='m_' + d['uid']))
        if len(self.store.maps) > 14:
            rows.append(self.I(T('(맵이 많아서 14개까지만 보여요)', '(showing the first 14 maps)')))
        rows.append(self.R(T('뒤로', 'Back'), lambda: self.back(), id='back'))
        self.menu.set(T('맵 만들기', 'Map maker'), rows, T('내 맵 %d개 · 파일 kart3d_maps.json (폰과 같은 형식)', '%d maps · file kart3d_maps.json (same as phone)') % len(self.store.maps)
                      if LANG == 'ko' else 'Map maker', T('Enter = 열기   ←→ = 번호 바꾸기', 'Enter = open   Left/Right = change number'))
        self.menu.clear_extra()

    def build_mapitem(self):
        uid = getattr(self, 'sel_cmap_uid', '')
        d = self.store.get(uid)
        if d is None:
            self.go('maps')
            return

        def race():
            self.profile['map_src'] = 'custom'
            self.profile['cmap'] = uid
            self.profile.save()
            self.go('solo')

        def rename():
            def done(t):
                t = t.strip()
                if t:
                    dd = dict(d)
                    dd['name'] = t
                    self.store.put(dd)
                self.build_mapitem()
            self.input.begin(T('맵 이름 (Enter 확인)', 'Map name (Enter = OK)'), d['name'], 20, 'alpha', done)

        def delete():
            if getattr(self, '_del_armed', None) == uid:
                self.store.delete(uid)
                self._del_armed = None
                if self.profile['cmap'] == uid:
                    self.profile['cmap'] = ''
                    self.profile['map_src'] = 'builtin'
                self.go('maps')
            else:
                self._del_armed = uid
                self.build_mapitem()
        armed = getattr(self, '_del_armed', None) == uid
        th = biome(d['look'])
        rows = [self.R(T('편집하기', 'Edit'), lambda: self.maker.open(d, uid), kind='primary', id='edit'),
                self.R(T('이 맵으로 달리기 (솔로)', 'Race this map (solo)'), race, id='race'),
                self.R(T('이름 바꾸기', 'Rename'), rename, id='rename'),
                self.R(T('정말 삭제! (Enter 한 번 더)', 'Really delete! (Enter again)') if armed else T('삭제', 'Delete'), delete, id='del'),
                self.R(T('뒤로', 'Back'), lambda: self.go('maps'), id='back')]
        self.menu.set(u'\u2605 ' + d['name'], rows, '%s  ·  %s %d' % (th['name'] if LANG == 'ko' else th['en'], T('물건', 'objects'), len(d['objs'])), '')
        self.draw_outline(d)

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

        def steer_resp():
            self.profile['steer_resp'] = (int(self.profile['steer_resp']) + 1) % 3
            self.profile.save()
            self.build_settings()
        sn = [T('부드럽게', 'Smooth'), T('보통', 'Normal'), T('빠르게', 'Quick')]
        rows = [self.R('%s: %s' % (T('언어 / Language', 'Language'), self.profile['lang']), lang, id='lang'),
                self.R('%s: %s' % (T('소리', 'Sound'), 'ON' if self.profile['sound'] else 'OFF'), snd, id='snd'),
                self.R('%s: %s' % (T('조향 반응', 'Steering'), sn[int(self.profile['steer_resp']) % 3]), steer_resp, id='steer'),
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
            cm = self.store.get(self.profile['cmap']) if self.profile['map_src'] == 'custom' else None
            if self.session.host_game(int(self.profile['port']), cm):
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
            mlab = (u'\u2605 ' + str(rm['cname'])) if rm.get('cname') else '#%s' % rm.get('map', '?')
            rows.append(self.R('%s  %s  %d/%d  %s' % (rm.get('name', 'room'), rm['ip'], rm.get('players', 0), RoomServer.MAX_PLAYERS, mlab), joiner,
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
        mname = '%s  ·  %s' % ((info['name'], info['theme_name']) if LANG == 'ko' else (info['name_en'], info['theme_en']))
        cmd = st.get('cmap')
        if cmd:
            mname = u'\u2605 %s  (%s)' % (cmd.get('name', '?'), T('직접 만든 맵', 'custom map'))
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

            def md(m=1):
                on = not bool(st.get('items'))
                ses.send_settings(items=on)
                self.profile['mode'] = 'item' if on else 'speed'

            def srcf(m=1):
                if cmd:
                    ses.send_settings(map=int(st['map']))
                    self.profile['map_src'] = 'builtin'
                else:
                    d = self.store.get(self.profile['cmap']) or (self.store.maps[0] if self.store.maps else None)
                    if d is not None:
                        self.profile['cmap'] = d['uid']
                        ses.send_settings(cmap=d)
                        self.profile['map_src'] = 'custom'

            def cmf(dd):
                def f(m=1):
                    maps = self.store.maps
                    if maps:
                        j = (self.store.index(self.profile['cmap']) + dd) % len(maps)
                        self.profile['cmap'] = maps[j]['uid']
                        ses.send_settings(cmap=maps[j])
                return f
            rows += [self.R('%s  < %s >' % (T('모드', 'Mode'), T('아이템전', 'Item battle') if st.get('items') else T('스피드전', 'Speed race')), md, md, md, id='mode'),
                     self.R('%s  < %s >' % (T('맵 종류', 'Maps'), T('내가 만든 맵', 'My maps') if cmd else T('기본 맵', 'Built-in')), srcf, srcf, srcf, id='src',
                            enabled=bool(cmd) or bool(self.store.maps))]
            if cmd:
                rows.append(self.R(u'%s  < \u2605 %s >' % (T('내 맵', 'My map'), cmd.get('name', '?')), None, cmf(-1), cmf(1), id='cmap'))
            else:
                rows.append(self.R('%s  < #%d >' % (T('맵', 'Map'), st['map']), None, mp(-1), mp(1), id='map'))
            rows += [
                     self.R('%s  < %d >' % (T('바퀴 수', 'Laps'), st['laps']), None, lp(-1), lp(1), id='laps'),
                     self.R('%s  < %d >' % (T('AI 봇', 'Bots'), st['bots']), None, bp(-1), bp(1), id='bots'),
                     self.R(T('레이스 시작!', 'START RACE!'), ses.start_race, kind='primary', id='start')]
            ips = local_ips()
            rows.append(self.I(T('친구에게 알려주세요: ', 'Tell your friends: ') + (ips[0] if ips else '?') + ':%d' % self.profile['port'], (1, 0.86, 0.47, 1)))
        else:
            mlab = (u'\u2605 ' + cmd.get('name', '?')) if cmd else '#%d' % st['map']
            rows.append(self.I('%s %s   %s %d   %s %d   %s' % (T('맵', 'Map'), mlab, T('바퀴', 'Laps'), st['laps'], T('봇', 'Bots'), st['bots'],
                                                             T('아이템전', 'Item battle') if st.get('items') else T('스피드전', 'Speed race'))))
            if cmd:
                def save_it(d=cmd):
                    if self.store.add_copy(d):
                        self.err = T('내 맵에 저장했어요', 'Saved to My maps')
                rows.append(self.R(T('이 맵을 내 맵에 저장', 'Save this map to My maps'), save_it, id='savemap'))
            rows.append(self.I(T('방장이 시작하기를 기다리는 중…', 'Waiting for the host…')))
        rows.append(self.R(T('나가기', 'Leave'), lambda: self.back(), id='leave'))
        self.menu.set(T('로비', 'Lobby'), rows, mname, T('←→ 값 변경 (Shift ±10, Ctrl ±100)', 'Left/Right change (Shift ±10, Ctrl ±100)'))
        key = (st['map'], cmap_key(cmd) if cmd else None)
        if getattr(self, '_lobby_map', None) != key or not self.menu.extra.getChildren():
            self.draw_outline(cmd if cmd else int(st['map']))
            self._lobby_map = key

    # ------------------------------------------------------------------ 레이스
    def solo_map(self):
        if self.test_map is not None:
            return self.test_map
        if self.profile['map_src'] == 'custom':
            d = self.store.get(self.profile['cmap'])
            if d is not None:
                return d
        return int(self.profile['map'])

    def start_solo(self):
        p = self.profile
        entries = solo_entries(p.display_name(), p['kart'], int(p['bots']))
        ref = self.solo_map()
        self.start_race(ref, int(p['laps']) if self.test_map is None else int(ref['laps']), entries, False, True,
                        5.0 if self.test_map is None else 3.0, p['mode'] == 'item')

    def use_item(self, slot):
        if self.race is not None and self.race.items is not None and not (self.paused and not self.race.multi):
            self.race.use_item(slot, self.brake_held)

    def start_race(self, map_id, laps, entries, multi, is_host, countdown, items=False):
        self.menu.show(False)
        self.menu.clear_extra()
        self.loading(T('맵 생성 중… ', 'Building map… ') + map_title(map_id, LANG))
        self.destroy_world()
        self.race = Race(map_id, laps, entries, multi=multi, is_host=is_host, countdown=countdown, net=self.session.net if multi else None, items=items)
        self.world = World(self, self.race.track)
        if items:
            self.item_world = ItemWorld(self, self.race, self.world.root)
        self.item_hud.reset()
        self.item_hud.show(items)
        self.hud.set_item_mode(items)
        self.screen_fx.clear()
        self.world_map = None
        self.nodes = {rc.id: KartNode(self, rc, self.world.root) for rc in self.race.racers}
        self.particles = Particles(self)
        wk = self.race.track.theme.get('weather')
        self.weather = Weather(self, wk, self.race.track.theme.get('wcol')) if wk else None
        self.hud.build_minimap(self.race.track)
        self.hud.mapname.setText(map_title(map_id, LANG))
        self.hud.show(True)
        self.chase = ChaseCam()
        self.steer = 0.0
        self.paused = False
        self.finish_at = None
        self.audio.silence()
        self.scene = 'race'
        self.loading_done()
        if items:
            self.hud.say(T('↑ 가속  ← → 조향  Space 드리프트  1·2·3 아이템 (↓ 누른 채 = 뒤로)  R 복귀',
                           'Up gas  Left/Right steer  Space drift  1·2·3 items (hold Down = throw back)  R reset'), 6.0, False, (1, 1, 1, 1))
        else:
            self.hud.say(T('↑ 가속   ← → 조향   Space 드리프트   R 복귀', 'Up gas   Left/Right steer   Space drift   R reset'), 6.0, False, (1, 1, 1, 1))

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
        if self.test_map is not None:
            self.test_map = None
            if self.maker.ed is not None:
                self.maker.need_cv = True
                self.go('editor')
                return
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
        self.brake_held = brk > 0.5
        self.steer = steer_step(self.steer, tgt, dt, self.profile['steer_resp'])
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
            elif kind == 'item':
                self.on_item_event(ev)
            elif kind == 'sim':
                e = ev[1]
                if e in ('pad', 'miniturbo'):
                    self.audio.play('boost')
                    if e == 'pad':
                        self.hud.say('BOOST!', 0.7, False, (0.3, 0.9, 1, 1))
                elif e in ('wall', 'bump'):
                    self.audio.play('bump')
                    self.shake = max(self.shake, 0.6)
                elif e == 'jump':
                    self.audio.play('lap', 0.7)
                    self.hud.say(T('점프!', 'JUMP!'), 0.7, False, (1, 0.88, 0.3, 1))
                elif e == 'oil':
                    self.audio.play('ihit', 0.6)
                    self.hud.say(T('미끌!', 'SLIPPERY!'), 0.8, False, (0.75, 0.6, 1, 1))
                elif e.startswith('tier'):
                    self.audio.play('tier')

    def on_item_event(self, ev):
        what = ev[1]
        if what == 'roll':
            self.audio.play('iroll', 0.5)
        elif what == 'get':
            self.audio.play('iget')
            self.hud.say('%s  ·  %s' % (item_name(ev[2], LANG), item_desc(ev[2], LANG)), 1.8, False, (0.78, 0.92, 1, 1))
        elif what == 'use':
            self.audio.play('iuse', 0.7)
        elif what == 'hit':
            self.audio.play('ihit')
            self.shake = max(self.shake, 0.9)
            self.hud.say(fx_name(ev[2], LANG) + '!', 1.2, True)
        elif what == 'block':
            self.audio.play('iblock')
            self.hud.say(T('방어!', 'BLOCKED!'), 1.0, True)
        elif what == 'score':
            self.hud.say(T('명중! ', 'HIT! ') + str(ev[2]), 1.2, False, (1, 0.86, 0.35, 1))
        elif what == 'stolen':
            self.hud.say(T('아이템을 도둑맞았어요: ', 'Item stolen: ') + item_name(ev[2], LANG), 1.6, False, (1, 0.6, 0.6, 1))

    def burst(self, x, y, z, n, cols, spd, size, life, up=4.0):
        pa = self.particles
        if pa is None:
            return
        for i in range(n):
            a = _random.random() * TAU
            v = spd * (0.4 + _random.random() * 0.6)
            c = cols[i % len(cols)]
            pa.emit(PV(x, y, z), PV(math.cos(a) * v, up * (0.3 + _random.random()), math.sin(a) * v), (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0),
                    size, life * (0.6 + _random.random() * 0.5))

    def item_vfx(self, race, lst):
        loc = race.local
        for v in lst:
            k = v[0]
            if k == 'box':
                self.burst(v[1], v[2], v[3], 14, [hue_rgb(i / 7.0) for i in range(7)], 7.0, 0.45, 0.6)
            elif k == 'boom':
                x, y, z, r, col = v[1], v[2], v[3], v[4], v[5]
                self.burst(x, y + 0.5, z, 36, [(255, 150, 40), (255, 230, 120), (255, 70, 40), col], r * 1.6, 1.0, 0.8, 7.0)
                d = math.hypot(loc.x - x, loc.z - z)
                if d < r * 3.0:
                    self.shake = max(self.shake, 1.0)
                if d < 150:
                    self.audio.play('iboom', clamp(1.0 - d / 160.0, 0.15, 1.0))
            elif k == 'ring':
                x, y, z, r, col = v[1], v[2], v[3], v[4], v[5]
                if self.particles is not None:
                    for i in range(28):
                        a = TAU * i / 28
                        self.particles.emit(PV(x + math.cos(a) * 1.5, y + 0.6, z + math.sin(a) * 1.5), PV(math.cos(a) * r * 2.2, 1.5, math.sin(a) * r * 2.2),
                                            (col[0] / 255.0, col[1] / 255.0, col[2] / 255.0), 0.9, 0.45)
            elif k == 'hit':
                self.burst(v[1], v[2] + 0.8, v[3], 12, [(255, 255, 255), (255, 220, 90)], 6.0, 0.5, 0.5)
            elif k == 'block':
                self.burst(v[1], v[2] + 0.8, v[3], 14, [(120, 220, 255), (255, 255, 255)], 7.0, 0.5, 0.5)
            elif k == 'warp':
                self.burst(v[1], v[2] + 0.8, v[3], 18, [(170, 90, 255), (60, 230, 255)], 5.0, 0.6, 0.7, 6.0)
            elif k == 'pop':
                self.burst(v[1], v[2], v[3], 8, [v[4], (255, 255, 255)], 5.0, 0.45, 0.4)
            elif k == 'area':
                it = ITEMS[v[1]]
                if it['kind'] == 'zap':
                    for rid in v[3]:
                        rc = race._find(rid)
                        if rc is not None and self.particles is not None:
                            c = it['c1']
                            for j in range(10):
                                cc = (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0) if j % 2 else (1, 1, 1)
                                self.particles.emit(PV(rc.x + (_random.random() - 0.5) * 1.2, rc.y + 1.0 + j * 1.4, rc.z + (_random.random() - 0.5) * 1.2),
                                                    (0, 0, 0), cc, 0.8, 0.35)
                    if loc.id in v[3] or it['p'].get('scope') == 'all' or v[2] == loc.id:
                        c = it['c1'] if it['icon'] in ('bolt', 'cloud') else (255, 255, 255)
                        self.screen_fx.flash = 0.32
                        self.screen_fx.flash_col = (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
                        self.audio.play('izap', 0.8)

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
            if race.items is not None:
                self.item_vfx(race, race.items.take_vfx())
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
        self.cam_pos, self.cam_fwd = pos, d          # 카메라 뒤 물체 갱신 생략용
        ratio = loc.speed / sim.stats['max_speed']
        self.camLens.setFov(82 + clamp(ratio, 0, 1.2) * 8 + (6 if loc.boosting else 0))
        self.world.update(pos)
        if self.particles is not None:
            self.particles.update(dt if not self.paused else 0.0)
        if self.weather is not None:
            self.weather.update(dt, pos)
        self.hud.update(race, time.time())
        if race.items is not None:
            if self.item_world is not None:
                self.item_world.update(dt)
            self.item_hud.update(race, self.t)
            self.screen_fx.update(sim.blind_t, dt)
        self._fps_t = getattr(self, '_fps_t', 0.0) + dt
        if self._fps_t > 0.25:
            self._fps_t = 0.0
            self.hud._set(self.hud.fps, ('%d fps' % int(1.0 / max(dt, 1e-3))) if self.show_fps else '')
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
        if sc == 'editor':
            self.maker.update(dt)
            return task.cont
        if sc in ('lobby', 'multi', 'menu', 'solo', 'garage', 'settings', 'maps', 'mapitem') or (sc == 'race' and self.race is None):
            if self.session.net is not None and sc == 'lobby':
                self.session.pump()
                if self.session.start_msg is not None:
                    msg = self.session.start_msg
                    self.session.start_msg = None
                    entries = self.session.entries_from_start(msg)
                    ref = msg.get('cmap') or int(msg['map'])
                    self.start_race(ref, int(msg['laps']), entries, True, self.session.is_host, float(msg.get('countdown', 5.0)), bool(msg.get('items')))
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
#  [PC] 맵 만들기 편집기 (마우스): 왼쪽 = 지도(그리기/옮기기/놓기), 오른쪽 = 도구판
#   왼쪽 버튼 = 도구 사용, 오른쪽 버튼 끌기 = 화면 이동, 휠 = 확대/축소, Ctrl+Z = 되돌리기, F = 전체 보기, Esc = 나가기
# ============================================================================
PC_ED_TABS = [('road', '길', 'Road'), ('obs', '장애물', 'Obstacles'), ('deco', '나무·장식', 'Nature'), ('pad', '발판·상자', 'Pads'),
              ('set', '설정', 'Settings')]
PC_ED_ROAD = [('draw', '길 그리기', 'Draw road'), ('move', '점 옮기기', 'Move point'), ('add', '점 추가', 'Add point'),
              ('del', '점 지우기', 'Delete point'), ('up', '높이기', 'Raise'), ('down', '낮추기', 'Lower'), ('start', '출발점', 'Start line'),
              ('pan', '화면 이동', 'Pan view')]
PC_ED_HINT = {
    'draw': ('왼쪽 버튼을 누른 채 코스를 한 바퀴 그리세요 (끝은 처음과 이어져요)', 'Hold the left button and draw one lap'),
    'move': ('점을 끌어서 옮기기 (빈 곳을 끌면 화면 이동)', 'Drag a point to move it (drag empty space to pan)'),
    'add': ('길 근처를 클릭하면 점 추가', 'Click near the road to add a point'),
    'del': ('지울 점을 클릭', 'Click a point to delete it'),
    'up': ('점을 클릭하면 그 부근 길이 4m 높아짐', 'Click a point to raise the road 4 m'),
    'down': ('점을 클릭하면 그 부근 길이 4m 낮아짐', 'Click a point to lower the road 4 m'),
    'start': ('출발선이 될 점을 클릭', 'Click the point for the start line'),
    'pan': ('끌어서 화면 이동 · 휠로 확대/축소', 'Drag to pan · wheel to zoom'),
    'erase': ('클릭하거나 끌어서 물건 지우기', 'Click or drag to erase objects'),
    'place': ('클릭해서 놓기 · 오른쪽 버튼 끌기로 화면 이동', 'Click to place · right-drag to pan'),
    'line': ('끌어서 선을 따라 줄지어 놓기', 'Drag to place a row along your line'),
}


class Draw2D(object):
    """aspect2d 위에 그릴 색 삼각형 묶음 (GeomNode 하나)"""

    def __init__(self):
        self.vd = GeomVertexData('d2', GeomVertexFormat.getV3c4(), Geom.UHStatic)
        self.vw = GeomVertexWriter(self.vd, 'vertex')
        self.cw = GeomVertexWriter(self.vd, 'color')
        self.pr = GeomTriangles(Geom.UHStatic)
        self.n = 0

    def tri(self, a, b, c, col):
        vw, cw = self.vw, self.cw
        for p in (a, b, c):
            vw.addData3(p[0], 0.0, p[1])
            cw.addData4(col[0], col[1], col[2], col[3] if len(col) > 3 else 1.0)
        self.pr.addVertices(self.n, self.n + 1, self.n + 2)
        self.n += 3

    def quad(self, a, b, c, d, col):
        self.tri(a, b, c, col)
        self.tri(a, c, d, col)

    def rect(self, x0, z0, x1, z1, col):
        self.quad((x0, z0), (x1, z0), (x1, z1), (x0, z1), col)

    def circle(self, x, z, r, col, seg=12):
        for k in range(seg):
            a0 = TAU * k / seg
            a1 = TAU * (k + 1) / seg
            self.tri((x, z), (x + math.cos(a0) * r, z + math.sin(a0) * r), (x + math.cos(a1) * r, z + math.sin(a1) * r), col)

    def line(self, a, b, w, col):
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz)
        if L < 1e-9:
            return
        nx, nz = -dz / L * w * 0.5, dx / L * w * 0.5
        self.quad((a[0] + nx, a[1] + nz), (b[0] + nx, b[1] + nz), (b[0] - nx, b[1] - nz), (a[0] - nx, a[1] - nz), col)

    def node(self, name):
        g = Geom(self.vd)
        g.addPrimitive(self.pr)
        gn = GeomNode(name)
        gn.addGeom(g)
        return gn


def _cf(c, k=1.0, a=1.0):
    return (min(1.0, c[0] / 255.0 * k), min(1.0, c[1] / 255.0 * k), min(1.0, c[2] / 255.0 * k), a)


class PCMapMaker(object):
    PANEL_W = 0.98

    def __init__(self, app):
        self.app = app
        self.ed = None
        self.uid = None
        self.tab = 'road'
        self.tool = 'draw'
        self.kinds = {'obs': 'cone', 'deco': 'pine', 'pad': 'pad'}
        self.line = False
        self.erase = False
        self.size = 1.0
        self.view = None
        self.root = None
        self.cv_np = None
        self.ov_np = None
        self.ui_np = None
        self.buttons = []
        self.texts = {}
        self.need_cv = True
        self.need_ui = True
        self.down = None           # 왼쪽 버튼 누른 위치 (aspect2d)
        self.moved = False
        self.stroke = None
        self.drag_pt = -1
        self.pan_last = None
        self.last_m = None
        self.msg = ''
        self.msg_t = 0.0
        self.confirm = None
        self.set_page = 0
        self.kind_page = 0
        self.import_mid = 1
        self.mouse_override = None  # 테스트용 (aspect2d 좌표)
        self.events = False

    # ------------------------------------------------------------------ 열기/닫기
    def say(self, ko, en, secs=2.2):
        self.msg = T(ko, en)
        self.msg_t = time.time() + secs
        self.need_ui = True

    def open(self, data, uid):
        self.ed = MapEdit(data)
        self.uid = uid
        self.view = None
        self.confirm = None
        self.stroke = None
        self.drag_pt = -1
        if not uid:
            self.tab, self.tool = 'road', 'draw'
            self.say('먼저 [길 그리기]로 코스를 그려 보세요 (기본 타원 코스로 바로 달릴 수도 있어요)',
                     'Draw your course with [Draw road] - or race the default oval right away', 5.0)
        self.app.go('editor')

    def enter(self):
        app = self.app
        app.menu.show(False)
        app.menu.clear_extra()
        self.leave_ui()
        self.root = app.aspect2d.attachNewNode('editor')
        self.cv_np = self.root.attachNewNode('canvas')
        self.ov_np = self.root.attachNewNode('overlay')
        self.ui_np = self.root.attachNewNode('editor-ui')
        for n in (self.cv_np, self.ov_np, self.ui_np):
            n.setTwoSided(True)
            n.setLightOff()
            n.setTransparency(TransparencyAttrib.MAlpha)
        self.need_cv = self.need_ui = True
        if not self.events:
            for ev, fn in (('mouse1', self.on_down), ('mouse1-up', self.on_up), ('mouse3', self.on_rdown), ('mouse3-up', self.on_rup),
                           ('wheel_up', lambda: self.on_wheel(1)), ('wheel_down', lambda: self.on_wheel(-1))):
                app.accept(ev, fn)
            self.events = True
        if self.view is None:
            self.fit()

    def leave_ui(self):
        if self.root is not None:
            self.root.removeNode()
        self.root = self.cv_np = self.ov_np = self.ui_np = None
        self.buttons = []
        self.texts = {}
        if self.events:
            for ev in ('mouse1', 'mouse1-up', 'mouse3', 'mouse3-up', 'wheel_up', 'wheel_down'):
                self.app.ignore(ev)
            self.events = False

    def save(self):
        d = self.ed.result()
        if d is None:
            self.say('저장할 수 없어요', 'Cannot save')
            return False
        d['uid'] = self.uid or ''
        uid = self.app.store.put(d)
        if uid is None:
            self.say('저장 실패', 'Save failed')
            return False
        self.uid = uid
        self.ed.data['uid'] = uid
        self.ed.dirty = False
        self.say('저장했어요', 'Saved')
        return True

    def try_exit(self):
        if self.ed is not None and self.ed.dirty:
            self.confirm = 'exit'
            self.need_ui = True
        else:
            self.leave()

    def leave(self):
        self.confirm = None
        self.leave_ui()
        self.ed = None
        self.app.go('maps')

    def test_drive(self):
        d = self.ed.result()
        if d is None:
            self.say('맵을 만들 수 없어요', 'Cannot build this map')
            return
        app = self.app
        p = app.profile
        entries = solo_entries(p.display_name(), p['kart'], int(p['bots']))
        app.test_map = d
        self.leave_ui()
        app.start_race(d, int(d['laps']), entries, False, True, 3.0, p['mode'] == 'item')

    # ------------------------------------------------------------------ 좌표
    def canvas_rect(self):
        a = self.app.getAspectRatio()
        return (-a + 0.02, a - self.PANEL_W - 0.03, -0.98, 0.98)

    def fit(self):
        d = self.ed.data
        xs = [p[0] for p in d['pts']] + [o[1] for o in d['objs']]
        zs = [p[1] for p in d['pts']] + [o[2] for o in d['objs']]
        x0, x1, z0, z1 = self.canvas_rect()
        w0, w1, v0, v1 = min(xs) - 40, max(xs) + 40, min(zs) - 40, max(zs) + 40
        sc = min((x1 - x0) / max(w1 - w0, 60.0), (z1 - z0) / max(v1 - v0, 60.0))
        self.view = [(w0 + w1) / 2.0, (v0 + v1) / 2.0, clamp(sc, 0.0002, 0.05)]
        self.need_cv = True

    def to_screen(self, x, z):
        cx, cz, sc = self.view
        x0, x1, z0, z1 = self.canvas_rect()
        return ((x0 + x1) / 2.0 + (x - cx) * sc, (z0 + z1) / 2.0 - (z - cz) * sc)

    def to_world(self, X, Z):
        cx, cz, sc = self.view
        x0, x1, z0, z1 = self.canvas_rect()
        return (cx + (X - (x0 + x1) / 2.0) / sc, cz - (Z - (z0 + z1) / 2.0) / sc)

    def in_canvas(self, m):
        x0, x1, z0, z1 = self.canvas_rect()
        return m is not None and x0 <= m[0] <= x1 and z0 <= m[1] <= z1

    def mouse(self):
        if self.mouse_override is not None:
            return self.mouse_override
        mw = self.app.mouseWatcherNode
        if mw is None or not mw.hasMouse():
            return None
        m = mw.getMouse()
        return (m.getX() * self.app.getAspectRatio(), m.getY())

    def zoom(self, k, at=None):
        if at is None:
            x0, x1, z0, z1 = self.canvas_rect()
            at = ((x0 + x1) / 2.0, (z0 + z1) / 2.0)
        wx, wz = self.to_world(*at)
        self.view[2] = clamp(self.view[2] * k, 0.0002, 0.05)
        nx, nz = self.to_world(*at)
        self.view[0] += wx - nx
        self.view[1] += wz - nz
        self.need_cv = True

    def pan(self, dX, dZ):
        sc = self.view[2]
        W = CMAP_WORLD + 200
        self.view[0] = clamp(self.view[0] - dX / sc, -W, W)
        self.view[1] = clamp(self.view[1] + dZ / sc, -W, W)
        self.need_cv = True

    def hit_m(self):
        return 0.035 / self.view[2]

    # ------------------------------------------------------------------ 입력
    def mode_of(self):
        if self.tab == 'road':
            return {'draw': 'stroke', 'move': 'point', 'pan': 'pan'}.get(self.tool, 'tap')
        if self.tab == 'set':
            return 'pan'
        if self.erase:
            return 'erase'
        return 'stroke' if self.line else 'tap'

    def busy(self):
        return self.ed is None or self.app.input.active or self.app.scene != 'editor'

    def on_down(self):
        if self.busy():
            return
        m = self.mouse()
        if m is None:
            return
        for (x0, x1, z0, z1, cb) in reversed(self.buttons):
            if x0 <= m[0] <= x1 and z0 <= m[1] <= z1:
                self.app.sfx_play('click', 0.4)
                cb()
                self.need_ui = True
                return
        if self.confirm is not None or not self.in_canvas(m):
            return
        self.down = m
        self.last_m = m
        self.moved = False
        mode = self.mode_of()
        wx, wz = self.to_world(*m)
        self.stroke = None
        self.drag_pt = -1
        if mode == 'stroke':
            self.stroke = [(wx, wz)]
        elif mode == 'point':
            i = self.ed.nearest_point(wx, wz, self.hit_m())
            if i >= 0:
                self.ed.snapshot()
                self.drag_pt = i
        elif mode == 'erase':
            if self.ed.erase_at(wx, wz, self.hit_m() * 0.7):
                self.need_cv = True

    def on_up(self):
        if self.down is None or self.busy():
            self.down = None
            return
        m = self.mouse() or self.last_m
        mode = self.mode_of()
        ed = self.ed
        wx, wz = self.to_world(*m)
        moved = self.moved
        self.down = None
        if mode == 'stroke' and self.stroke is not None:
            st = self.stroke
            self.stroke = None
            if self.tab == 'road':
                if len(st) > 4 and moved:
                    if ed.set_stroke(st):
                        self.say('길을 만들었어요! 점을 옮겨서 다듬을 수 있어요', 'Road created! Move points to fine-tune it')
                    else:
                        self.say('너무 짧아요. 화면을 크게 써서 한 바퀴 그려 주세요', 'Too short - draw a bigger loop')
            else:
                kind = self.kinds[self.tab]
                if not moved or len(st) < 2:
                    ed.add_obj(kind, wx, wz, OBJ_INFO[kind]['s'] * self.size)
                else:
                    n = ed.add_line(kind, st, OBJ_INFO[kind]['s'] * self.size)
                    if n:
                        self.say('%d개 놓았어요' % n, 'Placed %d' % n, 1.4)
                if ed.msg == 'full':
                    ed.msg = ''
                    self.say('물건이 너무 많아요 (최대 %d개)' % CMAP_MAX_OBJS, 'Too many objects (max %d)' % CMAP_MAX_OBJS)
            self.need_cv = True
        elif mode == 'point':
            if self.drag_pt >= 0:
                self.drag_pt = -1
                self.need_cv = True
        elif mode == 'tap' and not moved:
            self.tap(wx, wz)
        self.need_ui = True

    def tap(self, wx, wz):
        ed = self.ed
        if self.tab == 'road':
            tool = self.tool
            if tool == 'add':
                ed.insert_point(wx, wz)
            else:
                i = ed.nearest_point(wx, wz, self.hit_m())
                if i < 0:
                    self.say('점(동그라미)을 클릭해 주세요', 'Click on a point (circle)', 1.4)
                    return
                if tool == 'del':
                    if not ed.delete_point(i):
                        self.say('점이 4개보다 적을 수는 없어요', 'Need at least 4 points')
                elif tool in ('up', 'down'):
                    ed.raise_point(i, 4.0 if tool == 'up' else -4.0)
                elif tool == 'start':
                    ed.set_start(i)
                    self.say('출발선을 옮겼어요', 'Start line moved', 1.4)
        elif self.tab in ('obs', 'deco', 'pad'):
            kind = self.kinds[self.tab]
            if not ed.add_obj(kind, wx, wz, OBJ_INFO[kind]['s'] * self.size) and ed.msg == 'full':
                ed.msg = ''
                self.say('물건이 너무 많아요 (최대 %d개)' % CMAP_MAX_OBJS, 'Too many objects (max %d)' % CMAP_MAX_OBJS)
        self.need_cv = True

    def on_rdown(self):
        if self.busy():
            return
        m = self.mouse()
        if self.in_canvas(m):
            self.pan_last = m

    def on_rup(self):
        self.pan_last = None

    def on_wheel(self, d):
        if self.busy():
            return
        m = self.mouse()
        if self.in_canvas(m):
            self.zoom(1.2 ** d, m)

    def on_key(self, k):
        app = self.app
        if k == 'escape':
            if self.confirm is not None:
                self.confirm = None
                self.need_ui = True
            else:
                self.try_exit()
        elif k == 'z' and ('lcontrol' in app.keys or 'rcontrol' in app.keys):
            if self.ed.undo():
                self.need_cv = self.need_ui = True
        elif k == 'f':
            self.fit()

    def update(self, dt):
        if self.ed is None or self.root is None:
            return
        m = self.mouse()
        if m is not None and self.pan_last is not None:
            self.pan(m[0] - self.pan_last[0], m[1] - self.pan_last[1])
            self.pan_last = m
        if self.down is not None and m is not None and m != self.last_m:
            if not self.moved and math.hypot(m[0] - self.down[0], m[1] - self.down[1]) > 0.012:
                self.moved = True
            mode = self.mode_of()
            wx, wz = self.to_world(*m)
            if mode == 'stroke' and self.stroke is not None:
                lx, lz = self.stroke[-1]
                if math.hypot(wx - lx, wz - lz) * self.view[2] > 0.006:
                    self.stroke.append((wx, wz))
            elif mode == 'point' and self.drag_pt >= 0:
                self.ed.move_point(self.drag_pt, wx, wz, snap=False)
            elif mode == 'erase':
                objs = self.ed.data['objs']
                rad = self.hit_m() * 0.7
                keep = [o for o in objs if (o[1] - wx) ** 2 + (o[2] - wz) ** 2 >= (rad + OBJ_INFO[o[0]]['rad'] * o[3] * 0.5) ** 2]
                if len(keep) != len(objs):
                    self.ed.data['objs'] = keep
                    self.ed.dirty = True
                    self.need_cv = True
            elif self.moved:
                self.pan(m[0] - self.last_m[0], m[1] - self.last_m[1])
            self.last_m = m
        if self.need_cv:
            self.need_cv = False
            self.build_canvas()
            self.need_ui = True
        self.build_overlay()
        if self.need_ui or (self.msg and time.time() > self.msg_t):
            if self.msg and time.time() > self.msg_t:
                self.msg = ''
            self.need_ui = False
            self.build_ui()

    # ------------------------------------------------------------------ 지도 그리기
    def build_canvas(self):
        if self.cv_np is None:
            return
        for c in self.cv_np.getChildren():
            c.removeNode()
        D = Draw2D()
        x0, x1, z0, z1 = self.canvas_rect()
        d = self.ed.data
        th = biome(d['look'])
        g0 = hex_rgb(th['ground'][0])
        D.rect(x0, z0, x1, z1, _cf(g0, 0.42))
        sc = self.view[2]
        step = 50.0 if sc > 0.0012 else 200.0
        gcol = _cf(g0, 0.55)
        wa = self.to_world(x0, z1)
        wb = self.to_world(x1, z0)
        gx = math.floor(wa[0] / step) * step
        while gx <= wb[0]:
            X = self.to_screen(gx, 0)[0]
            D.line((X, z0), (X, z1), 0.002, gcol)
            gx += step
        gz = math.floor(wa[1] / step) * step
        while gz <= wb[1]:
            Z = self.to_screen(0, gz)[1]
            D.line((x0, Z), (x1, Z), 0.002, gcol)
            gz += step
        W = CMAP_WORLD
        corners = [self.to_screen(-W, -W), self.to_screen(W, -W), self.to_screen(W, W), self.to_screen(-W, W)]
        for k in range(4):
            D.line(corners[k], corners[(k + 1) % 4], 0.004, (0.8, 0.3, 0.3, 1))
        tr = self.ed.preview()
        if tr is not None:
            N = tr.N
            stp = 1 if sc > 0.004 else 2
            idxs = list(range(0, N, stp)) + [0]
            sh = tr.hw + tr.SH

            def edge(i, off):
                return self.to_screen(tr.px[i] + tr.rx[i] * off, tr.pz[i] + tr.rz[i] * off)
            L1 = [edge(i, -sh) for i in idxs]
            R1 = [edge(i, sh) for i in idxs]
            L0 = [edge(i, -tr.hw) for i in idxs]
            R0 = [edge(i, tr.hw) for i in idxs]
            grass = _cf(g0, 0.8)
            road = _cf(hex_rgb(th['road']), 1.5)
            wallc = _cf(hex_rgb(th['wall'][0]))
            for k in range(len(idxs) - 1):
                D.quad(L1[k], L1[k + 1], R1[k + 1], R1[k], grass)
            for k in range(len(idxs) - 1):
                D.quad(L0[k], L0[k + 1], R0[k + 1], R0[k], road)
            for k in range(len(idxs) - 1):
                D.line(L1[k], L1[k + 1], 0.003, wallc)
                D.line(R1[k], R1[k + 1], 0.003, wallc)
            if tr.max_y - tr.min_y > 1.0:
                for k in range(len(idxs) - 1):
                    f = (tr.py[idxs[k]] - tr.min_y) / (tr.max_y - tr.min_y)
                    c = mix_rgb((70, 90, 160), (255, 240, 160), f)
                    D.line(self.to_screen(tr.px[idxs[k]], tr.pz[idxs[k]]), self.to_screen(tr.px[idxs[k + 1]], tr.pz[idxs[k + 1]]), 0.003, _cf(c))
            a, b = edge(0, -tr.hw), edge(0, tr.hw)
            for k in range(8):
                p0 = (a[0] + (b[0] - a[0]) * k / 8.0, a[1] + (b[1] - a[1]) * k / 8.0)
                p1 = (a[0] + (b[0] - a[0]) * (k + 1) / 8.0, a[1] + (b[1] - a[1]) * (k + 1) / 8.0)
                D.line(p0, p1, 0.008, (1, 1, 1, 1) if k % 2 == 0 else (0.08, 0.08, 0.08, 1))
            j = min(N - 1, int(18 / tr.ds) + 1)
            c0 = self.to_screen(tr.px[0], tr.pz[0])
            c1 = self.to_screen(tr.px[j], tr.pz[j])
            ang = math.atan2(c1[1] - c0[1], c1[0] - c0[0])
            L = max(0.03, min(0.09, tr.width * sc * 1.2))
            tip = (c0[0] + math.cos(ang) * L, c0[1] + math.sin(ang) * L)
            D.line(c0, tip, 0.007, (1, 0.86, 0.24, 1))
            for da in (2.6, -2.6):
                D.line(tip, (tip[0] + math.cos(ang + da) * 0.022, tip[1] + math.sin(ang + da) * 0.022), 0.007, (1, 0.86, 0.24, 1))
        for o in d['objs']:
            info = OBJ_INFO[o[0]]
            p = self.to_screen(o[1], o[2])
            if not (x0 - 0.1 <= p[0] <= x1 + 0.1 and z0 - 0.1 <= p[1] <= z1 + 0.1):
                continue
            col = _cf(info['col'])
            cat = info['cat']
            if cat == 'road':
                hl = (4.5 if o[0] == 'pad' else 3.3) * o[3] * sc
                hwp = 2.8 * o[3] * sc
                if o[0] == 'box':
                    hl, hwp = 1.2 * sc, (tr.hw if tr is not None else 8.0) * sc
                hl, hwp = max(hl, 0.006), max(hwp, 0.005)
                fx_, fz_ = math.sin(o[4]), -math.cos(o[4])
                rx_, rz_ = -fz_, fx_
                pts = [(p[0] + fx_ * a_ * hl + rx_ * b_ * hwp, p[1] + fz_ * a_ * hl + rz_ * b_ * hwp) for (a_, b_) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                D.quad(pts[0], pts[1], pts[2], pts[3], col)
                continue
            rad = info['rad'] * o[3]
            if o[0] == 'building':
                rad = (14 + clamp((o[3] - 0.3) / 2.7, 0.0, 1.0) * 22) * 0.45
            if cat == 'obs':
                pr = max(0.006, rad * sc)
            else:
                pr = max(0.007, min(rad * sc * 2.2, 0.06))
            if o[0] in ('volcano', 'building'):
                pr = max(0.008, rad * sc)
            D.circle(p[0], p[1], pr * 1.18, (0, 0, 0, 1), 10)
            D.circle(p[0], p[1], pr, col, 10)
            if o[0] in ('lavapillar', 'volcano'):
                D.circle(p[0], p[1], pr * 0.42, (1, 0.85, 0.45, 1), 8)
        big = self.tab == 'road' and self.tool not in ('draw', 'pan')
        pr = 0.011 if big else 0.006
        for i, p in enumerate(d['pts']):
            q = self.to_screen(p[0], p[1])
            c = (1, 1, 1, 1)
            if p[2] > 0.5:
                c = (1, 0.78, 0.35, 1)
            elif p[2] < -0.5:
                c = (0.47, 0.67, 1, 1)
            if i == 0:
                D.circle(q[0], q[1], pr + 0.009, (0, 0, 0, 1), 12)
                D.circle(q[0], q[1], pr + 0.007, (0.3, 1, 0.47, 1), 12)
            D.circle(q[0], q[1], pr + 0.002, (0, 0, 0, 1), 10)
            D.circle(q[0], q[1], pr, c, 10)
        self.cv_np.attachNewNode(D.node('map2d'))

    def build_overlay(self):
        if self.ov_np is None:
            return
        for c in self.ov_np.getChildren():
            c.removeNode()
        D = Draw2D()
        any_ = False
        if self.stroke and len(self.stroke) > 1:
            pts = [self.to_screen(x, z) for x, z in self.stroke]
            col = (1, 0.9, 0.35, 1) if self.tab == 'road' else _cf(OBJ_INFO[self.kinds.get(self.tab, 'cone')]['col'])
            for a, b in zip(pts, pts[1:]):
                D.line(a, b, 0.012, (0, 0, 0, 1))
            for a, b in zip(pts, pts[1:]):
                D.line(a, b, 0.006, col)
            any_ = True
        if self.drag_pt >= 0:
            pts = [self.to_screen(p[0], p[1]) for p in self.ed.data['pts']]
            for k in range(len(pts)):
                D.line(pts[k], pts[(k + 1) % len(pts)], 0.004, (1, 0.9, 0.35, 1))
            q = pts[self.drag_pt]
            D.circle(q[0], q[1], 0.02, (1, 0.9, 0.35, 1), 14)
            any_ = True
        if any_:
            self.ov_np.attachNewNode(D.node('overlay'))

    # ------------------------------------------------------------------ 도구판
    def text(self, txt, x, z, scale, fg=(1, 1, 1, 1), align='l', maxw=None):
        tn_align = TextNode.ALeft if align == 'l' else (TextNode.ACenter if align == 'c' else TextNode.ARight)
        kw = dict(parent=self.ui_np, mayChange=False, shadow=(0, 0, 0, 1), align=tn_align)
        if self.app.font is not None:
            kw['font'] = self.app.font
        t = OnscreenText(text=txt, pos=(x, z), scale=scale, fg=fg, **kw)
        if maxw is not None:
            try:
                w = t.textNode.calcWidth(txt) * scale
                if w > maxw > 0:
                    t.setScale(scale * maxw / w)
            except Exception:
                pass
        return t

    def card(self, x0, z0, x1, z1, col):
        cm = CardMaker('c')
        cm.setFrame(x0, x1, z0, z1)
        n = self.ui_np.attachNewNode(cm.generate())
        n.setColor(*col)
        return n

    def button(self, x0, z0, x1, z1, label, cb, kind='normal', enabled=True, swatch=None):
        cols = {'normal': (0.16, 0.19, 0.31, 0.95), 'on': (0.1, 0.75, 0.88, 0.98), 'primary': (0.92, 0.27, 0.27, 0.98),
                'good': (0.16, 0.63, 0.35, 0.98), 'danger': (0.67, 0.16, 0.22, 0.98), 'ghost': (0.09, 0.1, 0.17, 0.95)}
        col = cols.get(kind, cols['normal']) if enabled else (0.2, 0.2, 0.24, 0.9)
        self.card(x0, z0, x1, z1, col)
        h = z1 - z0
        fg = (0.02, 0.08, 0.13, 1) if kind == 'on' else ((1, 1, 1, 1) if enabled else (0.55, 0.55, 0.6, 1))
        if swatch is not None:
            self.card(x0 + 0.008, z1 - 0.008 - h * 0.28, x0 + 0.008 + h * 0.28, z1 - 0.008, _cf(swatch))
        self.text(label, (x0 + x1) / 2.0, (z0 + z1) / 2.0 - h * 0.18, min(0.045, h * 0.5), fg, 'c', maxw=(x1 - x0) - 0.02)
        if enabled:
            self.buttons.append((x0, x1, z0, z1, cb))

    def stepper(self, x0, z, w, h, label, value, on_d):
        self.text(label, x0, z - h * 0.65, min(0.042, h * 0.5), (0.82, 0.86, 0.96, 1), maxw=w * 0.38)
        bw = h * 1.1
        lx = x0 + w * 0.4
        self.button(lx, z - h, lx + bw, z, '<', lambda: on_d(-1))
        self.button(x0 + w - bw, z - h, x0 + w, z, '>', lambda: on_d(1))
        self.text(str(value), (lx + bw + x0 + w - bw) / 2.0, z - h * 0.68, min(0.045, h * 0.52), (1, 0.86, 0.47, 1), 'c', maxw=(w - lx + x0 - 2 * bw) - 0.02)

    def build_ui(self):
        if self.ui_np is None:
            return
        for c in self.ui_np.getChildren():
            c.removeNode()
        self.buttons = []
        a = self.app.getAspectRatio()
        ed = self.ed
        d = ed.data
        x0, x1, z0, z1 = self.canvas_rect()
        # 지도 바깥으로 삐져나온 그림 가리기 (잘라내기 대신 불투명한 테두리)
        frame = (0.03, 0.04, 0.08, 1)
        self.card(-a - 0.2, -1.2, x0, 1.2, frame)
        self.card(x1, -1.2, a + 0.2, 1.2, frame)
        self.card(x0, z1, x1, 1.2, frame)
        self.card(x0, -1.2, x1, z0, frame)
        # 지도 위 글자
        tr = ed.preview()
        self.text(d['name'] + ('  *' if ed.dirty else ''), x0 + 0.03, z1 - 0.07, 0.06)
        if tr is not None:
            self.text(T('%.2f km · 폭 %dm · 조절점 %d · 물건 %d' % (tr.length / 1000.0, d['width'], len(d['pts']), len(d['objs'])),
                        '%.2f km · width %dm · %d points · %d objects' % (tr.length / 1000.0, d['width'], len(d['pts']), len(d['objs']))),
                      x0 + 0.03, z1 - 0.13, 0.038, (0.8, 0.86, 0.98, 1))
        wz = z1 - 0.19
        for wtxt in ed.warnings(LANG)[:2]:
            self.text('! ' + wtxt, x0 + 0.03, wz, 0.036, (1, 0.6, 0.45, 1))
            wz -= 0.05
        hint = self.msg if self.msg else self.hint()
        if hint:
            self.text(hint, x0 + 0.03, z0 + 0.03, 0.036, (1, 0.9, 0.6, 1), maxw=(x1 - x0) - 0.3)
        zb = 0.085
        for i, (lab, fn) in enumerate((('+', lambda: self.zoom(1.4)), ('-', lambda: self.zoom(1 / 1.4)), (T('전체', 'Fit'), self.fit))):
            self.button(x1 - zb - 0.02, z1 - 0.02 - (i + 1) * (zb + 0.012), x1 - 0.02, z1 - 0.02 - i * (zb + 0.012) - 0.012, lab, fn, 'ghost')
        # 오른쪽 도구판
        px0, px1 = a - self.PANEL_W, a - 0.02
        self.card(px0, -0.98, px1, 0.98, (0.06, 0.08, 0.16, 1))
        pw = px1 - px0 - 0.04
        x = px0 + 0.02
        z = 0.95
        tw = (pw - 4 * 0.01) / 5.0
        for i, (key, ko, en) in enumerate(PC_ED_TABS):
            def pick(k=key):
                self.tab = k
                self.erase = False
                self.need_cv = True
            self.button(x + i * (tw + 0.01), z - 0.08, x + i * (tw + 0.01) + tw, z, T(ko, en), pick, 'on' if self.tab == key else 'normal')
        z -= 0.1
        bz = -0.96
        bh = 0.09
        q = (pw - 3 * 0.01) / 4.0
        acts = [(T('되돌리기', 'Undo'), self.undo, 'normal', bool(ed.undo_stack)), (T('저장', 'Save'), self.save, 'good', True),
                (T('시험 주행', 'Test drive'), self.test_drive, 'primary', True), (T('나가기', 'Exit'), self.try_exit, 'ghost', True)]
        for i, (lab, fn, kind, en) in enumerate(acts):
            self.button(x + i * (q + 0.01), bz, x + i * (q + 0.01) + q, bz + bh, lab, fn, kind, en)
        top, bottom = z, bz + bh + 0.02
        if self.tab == 'road':
            self.ui_road(x, pw, top, bottom)
        elif self.tab in ('obs', 'deco', 'pad'):
            self.ui_objs(x, pw, top, bottom)
        else:
            self.ui_settings(x, pw, top, bottom)
        if self.confirm is not None:
            self.ui_confirm()

    def hint(self):
        if self.tab == 'set':
            return ''
        if self.tab == 'road':
            k = self.tool
        elif self.erase:
            k = 'erase'
        else:
            k = 'line' if self.line else 'place'
        h = PC_ED_HINT.get(k)
        return T(h[0], h[1]) if h else ''

    def undo(self):
        if self.ed.undo():
            self.need_cv = True

    def ui_road(self, x, pw, top, bottom):
        bw = (pw - 0.01) / 2.0
        bh = 0.085
        for i, (key, ko, en) in enumerate(PC_ED_ROAD):
            def pick(k=key):
                self.tool = k
                self.need_cv = True
            cx_ = x + (i % 2) * (bw + 0.01)
            cz = top - (i // 2) * (bh + 0.012)
            self.button(cx_, cz - bh, cx_ + bw, cz, T(ko, en), pick, 'on' if self.tool == key else 'normal')
        z = top - 4 * (bh + 0.012) - 0.02

        def rev():
            self.ed.reverse()
            self.need_cv = True
            self.say('달리는 방향을 바꿨어요', 'Direction reversed', 1.4)

        def center():
            d = self.ed.data
            xs = [p[0] for p in d['pts']]
            zs = [p[1] for p in d['pts']]
            self.ed.move_all(-(min(xs) + max(xs)) / 2.0, -(min(zs) + max(zs)) / 2.0)
            self.fit()
        self.button(x, z - bh, x + bw, z, T('방향 반대로', 'Reverse direction'), rev)
        self.button(x + bw + 0.01, z - bh, x + pw, z, T('가운데로 옮기기', 'Recenter'), center)
        z -= bh + 0.03
        self.text(T('조절점 색: 노랑 = 높음, 파랑 = 낮음, 초록 = 출발점', 'Point colors: yellow = high, blue = low, green = start'), x, z - 0.03, 0.032,
                  (0.7, 0.78, 0.95, 1), maxw=pw)
        self.text(T('마우스: 왼쪽 = 도구, 오른쪽 끌기 = 이동, 휠 = 확대', 'Mouse: left = tool, right-drag = pan, wheel = zoom'), x, z - 0.08, 0.032,
                  (0.7, 0.78, 0.95, 1), maxw=pw)
        self.text(T('Ctrl+Z 되돌리기 · F 전체 보기 · Esc 나가기', 'Ctrl+Z undo · F fit · Esc exit'), x, z - 0.13, 0.032, (0.7, 0.78, 0.95, 1), maxw=pw)

    def ui_objs(self, x, pw, top, bottom):
        cat = self.tab
        kinds = OBJ_BY_CAT['obs' if cat == 'obs' else ('deco' if cat == 'deco' else 'road')]
        cols = 3 if cat != 'pad' else 2
        bh = 0.08
        ctrl = 2 * (bh + 0.012) + 0.02
        avail = top - bottom - ctrl
        rows_fit = max(1, int((avail + 0.01) // (bh + 0.01)))
        per = len(kinds)
        if (len(kinds) + cols - 1) // cols > rows_fit:
            per = rows_fit * cols - 2
        npg = max(1, (len(kinds) + per - 1) // per)
        self.kind_page = int(clamp(self.kind_page, 0, npg - 1))
        shown = kinds[self.kind_page * per:(self.kind_page + 1) * per]
        bw = (pw - (cols - 1) * 0.01) / float(cols)
        cur = self.kinds[cat]
        cells = len(shown) + (2 if npg > 1 else 0)
        for i in range(cells):
            cx_ = x + (i % cols) * (bw + 0.01)
            cz = top - (i // cols) * (bh + 0.01)
            if i < len(shown):
                k = shown[i]

                def pick(k=k):
                    self.kinds[cat] = k
                    self.erase = False
                self.button(cx_, cz - bh, cx_ + bw, cz, obj_name(k, LANG), pick, 'on' if (k == cur and not self.erase) else 'normal', swatch=OBJ_INFO[k]['col'])
            elif i == len(shown):
                self.button(cx_, cz - bh, cx_ + bw, cz, '<', lambda: setattr(self, 'kind_page', self.kind_page - 1), enabled=self.kind_page > 0)
            else:
                self.button(cx_, cz - bh, cx_ + bw, cz, '>  %d/%d' % (self.kind_page + 1, npg), lambda: setattr(self, 'kind_page', self.kind_page + 1),
                            enabled=self.kind_page < npg - 1)
        z = bottom + ctrl
        third = (pw - 0.02) / 3.0

        def single():
            self.line = False
            self.erase = False

        def row():
            self.line = True
            self.erase = False

        def eraser():
            self.erase = not self.erase
        self.button(x, z - bh, x + third, z, T('한 개씩', 'Single'), single, 'on' if not self.line and not self.erase else 'normal')
        self.button(x + third + 0.01, z - bh, x + 2 * third + 0.01, z, T('줄로 놓기', 'Draw a row'), row, 'on' if self.line and not self.erase else 'normal')
        self.button(x + 2 * (third + 0.01), z - bh, x + pw, z, T('지우개', 'Eraser'), eraser, 'danger' if self.erase else 'normal')
        z -= bh + 0.012

        def size(dd):
            self.size = round(clamp(self.size + dd * 0.1, 0.4, 3.0), 2)
        self.stepper(x, z, pw, bh, T('크기', 'Size'), '%d%%' % int(round(self.size * 100)), size)

    def ui_settings(self, x, pw, top, bottom):
        ed = self.ed
        d = ed.data
        bh = 0.075
        gap = 0.012
        z = top

        def setv(key, val):
            ed.set(key, val)
            self.need_cv = True
        if self.set_page == 0:
            def rename():
                def done(t):
                    t = t.strip()
                    if t:
                        setv('name', t)
                    self.need_ui = True
                self.app.input.begin(T('맵 이름 (Enter 확인)', 'Map name (Enter = OK)'), d['name'], 20, 'alpha', done)
            self.button(x, z - bh, x + pw, z, T('이름: ', 'Name: ') + d['name'], rename)
            z -= bh + gap
            fam, ti, mi = biome_parts(d['look'])
            fname, tname, mname = biome_part_names(d['look'], LANG)
            self.stepper(x, z, pw, bh, T('바이옴', 'Biome'), fname, lambda k: setv('look', biome_map(fam + k, ti, mi)))
            z -= bh + gap
            self.stepper(x, z, pw, bh, T('시간대', 'Time'), tname, lambda k: setv('look', biome_map(fam, ti + k, mi)))
            z -= bh + gap
            self.stepper(x, z, pw, bh, T('색감', 'Mood'), mname, lambda k: setv('look', biome_map(fam, ti, mi + k)))
            z -= bh + gap
            wl = CMAP_WEATHERS
            self.stepper(x, z, pw, bh, T('날씨', 'Weather'), (CMAP_WEATHER_KO if LANG == 'ko' else CMAP_WEATHER_EN)[d['weather']],
                         lambda k: setv('weather', wl[(wl.index(d['weather']) + k) % len(wl)]))
            z -= bh + gap
            self.stepper(x, z, pw, bh, T('자동 장식', 'Auto scenery'), (CMAP_DECO_KO if LANG == 'ko' else CMAP_DECO_EN)[d['deco']],
                         lambda k: setv('deco', int(clamp(d['deco'] + k, 0, 3))))
            z -= bh + gap
        else:
            self.stepper(x, z, pw, bh, T('도로 폭', 'Road width'), '%dm' % d['width'], lambda k: setv('width', clamp(d['width'] + k * 2, 10, 30)))
            z -= bh + gap
            self.stepper(x, z, pw, bh, T('언덕', 'Hills'), '%d%%' % int(round(d['hills'] * 100)), lambda k: setv('hills', round(clamp(d['hills'] + k * 0.1, 0.0, 1.0), 2)))
            z -= bh + gap
            self.stepper(x, z, pw, bh, T('기본 바퀴 수', 'Default laps'), d['laps'], lambda k: setv('laps', int(clamp(d['laps'] + k, 1, 10))))
            z -= bh + gap
            half = (pw - 0.01) / 2.0
            self.button(x, z - bh, x + half, z, T('자동 부스트 발판: ', 'Auto boost pads: ') + (T('켬', 'On') if d['pads'] else T('끔', 'Off')),
                        lambda: setv('pads', 0 if d['pads'] else 1), 'on' if d['pads'] else 'normal')

            def ask_clear():
                self.confirm = 'clear'
            self.button(x + half + 0.01, z - bh, x + pw, z, T('물건 모두 지우기', 'Clear objects'), ask_clear, 'danger', bool(d['objs']))
            z -= bh + gap

            def imp(k):
                self.import_mid = ((self.import_mid - 1 + k) % MAP_COUNT) + 1

            def do_import():
                src = cmap_from_builtin(self.import_mid)
                ed.snapshot()
                ed.data['pts'] = src['pts']
                ed.data['width'] = src['width']
                self.fit()
                self.say('기본 맵 #%d 의 코스 모양을 가져왔어요' % self.import_mid, 'Copied the course of map #%d' % self.import_mid)
            self.stepper(x, z, pw * 0.64, bh, T('코스 가져오기', 'Copy course'), '#%d' % self.import_mid, imp)
            self.button(x + pw * 0.66, z - bh, x + pw, z, T('가져오기', 'Copy'), do_import)
            z -= bh + gap
        bz = bottom + 0.005
        self.button(x, bz, x + 0.16, bz + bh, '<', lambda: setattr(self, 'set_page', 0), enabled=self.set_page > 0)
        self.text('%d / 2' % (self.set_page + 1), x + pw / 2.0, bz + 0.025, 0.04, (0.9, 0.92, 1, 1), 'c')
        self.button(x + pw - 0.16, bz, x + pw, bz + bh, '>', lambda: setattr(self, 'set_page', 1), enabled=self.set_page < 1)

    def ui_confirm(self):
        a = self.app.getAspectRatio()
        self.card(-a, -1, a, 1, (0, 0, 0, 0.6))
        self.buttons = []        # 확인 창 밖은 클릭 안 됨
        self.card(-0.7, -0.25, 0.7, 0.3, (0.05, 0.07, 0.15, 0.97))
        if self.confirm == 'exit':
            self.text(T('저장하지 않은 변경이 있어요', 'You have unsaved changes'), 0, 0.15, 0.06, (1, 1, 1, 1), 'c')

            def save_exit():
                if self.save():
                    self.leave()
            self.button(-0.66, -0.2, -0.24, -0.06, T('저장 후 나가기', 'Save & exit'), save_exit, 'good')
            self.button(-0.21, -0.2, 0.21, -0.06, T('그냥 나가기', 'Discard'), self.leave, 'danger')
            self.button(0.24, -0.2, 0.66, -0.06, T('취소', 'Cancel'), lambda: setattr(self, 'confirm', None), 'ghost')
        else:
            self.text(T('놓은 물건을 모두 지울까요?', 'Remove all placed objects?'), 0, 0.15, 0.06, (1, 1, 1, 1), 'c')

            def clear():
                self.ed.clear_objs()
                self.confirm = None
                self.need_cv = True
            self.button(-0.6, -0.2, -0.04, -0.06, T('모두 지우기', 'Clear all'), clear, 'danger')
            self.button(0.04, -0.2, 0.6, -0.06, T('취소', 'Cancel'), lambda: setattr(self, 'confirm', None), 'ghost')



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
