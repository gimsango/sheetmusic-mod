# -*- coding: utf-8 -*-
"""입력 느낌 테스트: 조향 키로 자동가속이 꺼지지 않는지, 조향 반응 속도, 설정 화면"""
import os, sys, importlib.util
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1] if len(sys.argv) > 1 else '/tmp'
os.makedirs('/tmp/kt_probe/in', exist_ok=True); sys.argv[0] = '/tmp/kt_probe/in/app.py'
spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
pg = K.pygame

# 1) steer_step: 범위, 반응 시간
for resp, name in ((0, '부드럽게'), (1, '보통'), (2, '빠르게')):
    s = 0.0; t = 0.0
    while s < 0.9 and t < 3: s = K.steer_step(s, 1.0, 1 / 60.0, resp); t += 1 / 60.0
    r = 1.0; t2 = 0.0
    while r > 0.1 and t2 < 3: r = K.steer_step(r, 0.0, 1 / 60.0, resp); t2 += 1 / 60.0
    f = 1.0; t3 = 0.0
    while f > -0.9 and t3 < 3: f = K.steer_step(f, -1.0, 1 / 60.0, resp); t3 += 1 / 60.0
    print('조향 반응 %-6s  풀조향 90%% 까지 %.2fs / 놓았을 때 중앙까지 %.2fs / 반대로 급전환 %.2fs' % (name, t, t2, t3))
    assert -1.0 <= s <= 1.0
assert K.steer_step(0.0, 1.0, 1.0, 1) <= 1.0 and K.steer_step(0.0, -1.0, 1.0, 1) >= -1.0

# 2) 앱: 키보드로 조향만 눌러도 자동 가속 유지
app = K.App({'window': (900, 500), 'lang': 'ko'})
app.profile['auto_gas'] = True
def frames(n):
    for _ in range(n): app.step(1 / 60.0)
app.profile['bots'] = 3; app.start_solo(); app.race.start_at = K.time.monotonic() - 1; frames(5)
def key(k, down):
    pg.event.post(pg.event.Event(pg.KEYDOWN if down else pg.KEYUP, key=k, unicode='', mod=0, scancode=0))
    frames(1)
key(pg.K_LEFT, True)
inp, _ = app.read_input(1 / 60.0)
print('← 만 누름: throttle =', inp['throttle'], '(1.0 이어야 함: 자동 가속 유지)'); assert inp['throttle'] == 1.0
key(pg.K_LEFT, False)
key(pg.K_UP, True); inp, _ = app.read_input(1 / 60.0); assert inp['throttle'] == 1.0
key(pg.K_UP, False); inp, _ = app.read_input(1 / 60.0)
print('↑ 눌렀다 뗌: throttle =', inp['throttle'], '(0.0: 직접 가속 모드)'); assert inp['throttle'] == 0.0
key(pg.K_DOWN, True); inp, _ = app.read_input(1 / 60.0); print('↓: brake =', inp['brake']); assert inp['brake'] == 1.0
key(pg.K_DOWN, False)
print('터치 버튼 표시(키보드 사용 후):', app.touch_visible(), '(PC 에서 키보드를 쓰면 False)'); assert app.touch_visible() is False
app.leave_race(); frames(3)
# 3) 설정 화면 스크린샷
app.go('settings'); frames(6)
pg.image.save(app.screen, os.path.join(out, 'feel_settings_900x500.png'))
# 4) 설정 변경 반응
before = app.profile['steer_resp']
app.profile['steer_resp'] = 2; frames(3); assert app.profile['steer_resp'] == 2
print('INPUT FEEL TEST OK')
