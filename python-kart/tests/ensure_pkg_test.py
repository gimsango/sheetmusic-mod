# -*- coding: utf-8 -*-
"""_ensure_pkg 시나리오 (pip/프로세스 호출은 가짜)"""
import os, sys, importlib.util
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
K.input = lambda prompt='': 'y'
K._wait_key = lambda: None
cur = sys.executable

def make(fail_pkgs=(), other_import_ok=False, other_install_ok=True):
    log = []
    def fake(cmd, **kw):
        log.append(cmd)
        exe = cmd[0]
        if exe == '/fake/py313':
            if '-c' in cmd: return 0 if other_import_ok else 1
            if 'pip' in cmd: return 0 if other_install_ok else 1
            return 0                                   # 재시작
        if '-m' in cmd and 'pip' in cmd: return 1 if cmd[-1] in fail_pkgs else 0
        return 0                                       # 현재 파이썬 재시작
    return log, fake

# 시나리오 1: pygame 실패 -> pygame-ce 성공 -> 같은 파이썬으로 재시작
K._other_pythons = lambda: []
os.environ.pop('KART3D_RELAUNCHED', None)
log, K.subprocess.call = make(fail_pkgs={'pygame'})
try: K._ensure_pkg('pygame', candidates=['pygame', 'pygame-ce'])
except SystemExit as e: pass
seq = [c[-1] if '-m' in c else 'RESTART' for c in log]
print('시나리오1', seq); assert seq == ['pygame', 'pygame-ce', 'RESTART'], seq

# 시나리오 2: 현재 파이썬 설치 실패 -> 다른 파이썬(3.13)에 설치 -> 그 파이썬으로 재시작
K._other_pythons = lambda: [('3.13', '/fake/py313')]
os.environ.pop('KART3D_RELAUNCHED', None)
log, K.subprocess.call = make(fail_pkgs={'panda3d'})
try: K._ensure_pkg('panda3d')
except SystemExit as e: pass
kinds = []
for c in log:
    if c[0] == '/fake/py313': kinds.append('other-import' if '-c' in c else ('other-pip' if 'pip' in c else 'other-RESTART'))
    else: kinds.append('cur-pip' if 'pip' in c else 'cur-RESTART')
print('시나리오2', kinds); assert kinds == ['other-import', 'cur-pip', 'other-import', 'other-pip', 'other-RESTART'], kinds
assert os.environ.get('KART3D_RELAUNCHED') == '1'

# 시나리오 3: 이미 한 번 재시작했는데도 실패 -> 설치/재시작 반복 금지
log, K.subprocess.call = make(fail_pkgs={'panda3d'})
K._ensure_pkg('panda3d', err="DLL load failed")
print('시나리오3 (반복 금지) 호출 수:', len(log)); assert len(log) == 0
os.environ.pop('KART3D_RELAUNCHED', None)
print('ENSURE_PKG TESTS PASSED')
