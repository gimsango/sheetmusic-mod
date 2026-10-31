#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
  TURBO KART 3D  -  폰 버전 (Pydroid 3)            [ kart3d_phone.py ]
==========================================================================
  * 맵 1000개 / 카트 100,000종 / WiFi(LAN) 멀티플레이 / 터치 조작
  * 파일 하나로 실행됩니다. Pydroid 3 에서 이 파일을 열고 ▶ 를 누르세요.
  * 필요한 것: pygame  (Pydroid 3 > 메뉴 > Pip > "pygame" 설치)
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


def _ensure_pkg(pkg, alt_hint=''):
    """필요한 패키지가 없을 때: 올바른 설치 명령을 보여주고, 동의하면 같은 파이썬으로 설치한 뒤 게임을 다시 시작한다."""
    exe = sys.executable or 'python'
    is_android = ('ANDROID_ARGUMENT' in os.environ) or ('ANDROID_ROOT' in os.environ and os.path.exists('/system/build.prop'))
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

try:
    import pygame
except ImportError:
    _ensure_pkg('pygame')
    raise SystemExit(1)

# @CORE@
