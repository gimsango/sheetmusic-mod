# -*- coding: utf-8 -*-
"""
TURBO KART 3D (PC) - 배포용 실행 파일 만들기 (Panda3D build_apps)
Build a standalone PC release (no Python needed on the player's computer).

    python -m pip install panda3d setuptools wheel
    python src/build.py                  # kart3d_pc.py 를 최신으로 (이미 있으면 생략 가능)
    python setup.py build_apps           # build/win_amd64/TurboKart3D.exe 등
    python setup.py build_apps -p manylinux2014_x86_64      # 리눅스(스팀 덱)용
    python setup.py bdist_apps           # 플랫폼별 압축 파일 (dist/)

결과 폴더(build/<플랫폼>/)를 그대로 Steam 업로드(SteamPipe) 콘텐츠 폴더로 쓰면 된다 (README 'Steam 출시' 참고).
설치판은 저장 파일을 사용자 폴더에 둔다: Windows %APPDATA%/TurboKart3D, Linux ~/.local/share/TurboKart3D,
macOS ~/Library/Application Support/TurboKart3D  (로그: 같은 폴더의 output.log)
"""
import os
import sys
import importlib.util

from setuptools import setup

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, 'kart3d_pc.py')
ICON_DIR = os.path.join(HERE, 'build_icons')


def _load_game():
    """게임 파일을 모듈로 불러온다 (main() 은 실행되지 않음) - 버전/아이콘 그림을 가져오려고"""
    spec = importlib.util.spec_from_file_location('kart3d_pc_setup', GAME)
    mod = importlib.util.module_from_spec(spec)
    argv = sys.argv
    try:
        sys.argv = [GAME]
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    return mod


def _make_icons(mod):
    if not os.path.isdir(ICON_DIR):
        os.makedirs(ICON_DIR)
    out = []
    for n in (256, 128, 64, 48, 32, 16):
        p = os.path.join(ICON_DIR, 'icon_%d.png' % n)
        mod.draw_icon(n, 3 if n >= 64 else 4).write(mod.Filename.fromOsSpecific(p))
        out.append(p)
    return out


_game = _load_game()
_icons = _make_icons(_game)

setup(
    name='TurboKart3D',
    version=_game.VERSION,
    description='TURBO KART 3D - kart racing with 1000 maps, 100 items, map maker and LAN multiplayer',
    options={
        'build_apps': {
            'gui_apps': {'TurboKart3D': 'kart3d_pc.py'},
            'icons': {'TurboKart3D': _icons},
            'plugins': ['pandagl', 'p3tinydisplay', 'p3openal_audio'],     # tinydisplay = OpenGL 이 안 될 때 예비 + --offscreen
            'log_filename': '$USER_APPDATA/TurboKart3D/output.log',
            'log_append': False,
            'include_patterns': ['README.md'],
            'exclude_modules': {'*': ['pygame', 'tkinter', 'numpy']},
            'platforms': ['win_amd64'],
        },
    },
)
