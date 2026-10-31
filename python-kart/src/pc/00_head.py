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

# @CORE@
