# -*- coding: utf-8 -*-
"""_ensure_pkg 시나리오 (pip 호출은 가짜): 1) pygame 실패 -> pygame-ce 성공 -> 재시작   2) 모두 실패(Python 3.15 가정) -> 안내"""
import os, sys, importlib.util, io
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
calls = []
def fake_call_factory(fail):
    def fake(cmd):
        calls.append(cmd[-1] if '-m' in cmd else 'RESTART')
        if '-m' in cmd: return 1 if cmd[-1] in fail else 0
        return 0
    return fake
K.input = lambda prompt='': 'y'
K.subprocess.call = fake_call_factory({'pygame'})
try:
    K._ensure_pkg('pygame', candidates=['pygame', 'pygame-ce'])
except SystemExit as e:
    print('시나리오1 종료코드', e.code, '호출 순서:', calls)
assert calls == ['pygame', 'pygame-ce', 'RESTART'], calls
calls.clear()
K.subprocess.call = fake_call_factory({'pygame', 'pygame-ce'})
real_vi = sys.version_info
sys.version_info = (3, 15, 0, 'final', 0)
K._wait_key = lambda: None
print('--- 시나리오2 출력:')
K._ensure_pkg('pygame', candidates=['pygame-ce', 'pygame'])
sys.version_info = real_vi
print('호출:', calls)
