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

# @CORE@
