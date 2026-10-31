# -*- coding: utf-8 -*-
"""폰 앱 헤드리스 UI 테스트: python3 tests/app_probe.py <outdir> [W H]"""
import os, sys, time, importlib.util, traceback
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
W = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
H = int(sys.argv[3]) if len(sys.argv) > 3 else 520
os.makedirs('/tmp/kt_probe', exist_ok=True)
for f in ('/tmp/kt_probe/kart3d_profile.json',):
    if os.path.exists(f): os.remove(f)
sys.argv[0] = '/tmp/kt_probe/app.py'
spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
pg = K.pygame
app = K.App({'window': (W, H), 'lang': 'ko'})
app.profile['port'] = 5612
print('font:', app.font_path, 'lang:', K.LANG)
tag = '%dx%d' % (W, H)

def frames(n, dt=1 / 60.0):
    for _ in range(n):
        app.step(dt)

def shot(name):
    pg.image.save(app.screen, os.path.join(out, 'ui_%s_%s.png' % (name, tag)))

def tap(x, y):
    app.ptr.taps.append((x, y)); frames(2)

def press(points, n):
    # 손가락 누름 시뮬레이션
    for i, p in enumerate(points):
        app.ptr.fingers[i] = p
    frames(n)
    app.ptr.fingers.clear()

try:
    frames(40); shot('menu')
    u = app.ui.u
    bw = W * 0.40; bx = W * 0.06; by = H * 0.40; bh = min(H * 0.1, 64 * u)
    tap(bx + bw / 2, by + bh / 2)           # 솔로 레이스
    assert app.scene == 'solo', app.scene
    frames(20); shot('solo')
    app.go('garage'); frames(20); shot('garage')
    app.open_kb('Nickname', 'Hi', 'alpha', 14, lambda t: None); frames(5); shot('keyboard')
    app.close_kb('cancel'); frames(2)
    app.go('settings'); frames(10); shot('settings')
    app.go('multi'); frames(60); shot('multi')
    # 호스트 시작 -> 로비
    assert app.session.host_game(5612)
    app.scene = 'lobby'; frames(40); shot('lobby')
    print('lobby state', app.session.state, 'host?', app.session.is_host, [p['name'] for p in app.session.players])
    app.session.leave(); app.go('menu'); frames(5)
    # 솔로 레이스 시작
    app.profile['map'] = 6; app.profile['bots'] = 6; app.profile['laps'] = 2
    app.start_solo()
    race = app.race
    race.start_at = time.monotonic() + 0.5
    frames(20); shot('countdown')
    frames(40)
    # 터치 조작: 오른쪽 아래 드리프트 버튼 + 오른쪽 조향 누르기
    btn = app.touch.btn
    for i in range(5):
        press([(btn['right'][0], btn['right'][1])], 20)
    press([(btn['right'][0], btn['right'][1]), (btn['drift'][0], btn['drift'][1])], 30)
    frames(60)
    shot('race')
    loc = race.local
    print('race: t=%.1f speed=%.0f lap=%d pos=%d idx=%d' % (race.t, loc.speed, loc.sim.lap, race.ranking().index(loc) + 1, loc.idx))
    # 일시정지
    app.toggle_pause(); frames(10); shot('pause'); app.toggle_pause(); frames(2)
    # 자동주행으로 결승까지
    race.auto_local = True
    n = 0
    while app.scene != 'results' and n < 60 * 240:
        frames(1, 1 / 30.0); n += 1
    print('results scene after %d frames (%.0fs of race time)' % (n, race.t))
    frames(30); shot('results')
    app.leave_race(); frames(5)
    print('FPS-ish ema', round(app.fps_ema, 1))
    print('APP PROBE OK')
except Exception:
    traceback.print_exc(); shot('error')
