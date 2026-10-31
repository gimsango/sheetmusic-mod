# -*- coding: utf-8 -*-
"""PC 앱 호스트 + 헤드리스 게스트: 로비 -> 시작 -> 동기화 -> 일시정지 -> 결과"""
import os, sys, time, importlib.util, traceback
os.environ['KART3D_OFFSCREEN'] = '1'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
os.makedirs('/tmp/kt_probe', exist_ok=True); sys.argv[0] = '/tmp/kt_probe/pc.py'
spec = importlib.util.spec_from_file_location('kpc', os.path.join(ROOT, 'kart3d_pc.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kpc'] = K; spec.loader.exec_module(K)
g = K.Game({'window': (960, 540), 'lang': 'ko', 'port': 5614})
g.profile['map'] = 7
def frames(n, dt=1 / 60.0):
    g.dt_override = dt
    for _ in range(n): g.taskMgr.step()
def shot(name):
    g.graphicsEngine.renderFrame(); g.win.saveScreenshot(K.Filename(os.path.join(out, 'pcm_%s.png' % name)))
try:
    frames(10)
    g.go('multi'); frames(10)
    assert g.session.host_game(5614); g.go('lobby'); frames(20)
    P2 = K.Profile('/tmp/kt_probe/pcguest.json'); P2['name'] = 'GuestPhone'; P2['kart'] = 55555
    S2 = K.Session(P2); S2.join_game('127.0.0.1', 5614)
    for _ in range(60): frames(1); S2.pump(); time.sleep(0.01)
    print('players:', [p['name'] for p in g.session.players])
    assert len(g.session.players) == 2
    g.session.send_settings(bots=2, laps=2, map=8)
    for _ in range(20): frames(1); S2.pump(); time.sleep(0.01)
    shot('lobby')
    assert S2.settings['map'] == 8, S2.settings
    g.session.start_race()
    for _ in range(40): frames(1); S2.pump(); time.sleep(0.01)
    assert g.scene == 'race', g.scene
    R2 = K.Race(8, 2, S2.entries_from_start(S2.start_msg), multi=True, is_host=S2.is_host, countdown=0.0, net=S2.net, auto_local=True)
    race = g.race; race.auto_local = True; race.start_at = time.monotonic() - 1
    for f in range(60 * 12):
        for m in S2.pump(): R2.handle_message(m)
        R2.update(1 / 60., {'steer': 0, 'throttle': 0, 'brake': 0, 'drift': False})
        frames(1)
    shot('race')
    print('host:', [(r.name, r.kind, round(r.total), round(r.speed)) for r in race.racers])
    print('guest:', [(r.name, r.kind, round(r.total), round(r.speed)) for r in R2.racers])
    assert all(r.total > 30 for r in race.racers) and all(r.total > 30 for r in R2.racers)
    # 일시정지 (멀티에서는 메뉴만 뜨고 레이스 계속)
    g.on_key('escape'); frames(5); shot('pause'); assert g.paused
    g.on_key('escape'); frames(2); assert not g.paused
    # 결승까지
    n = 0
    while g.scene != 'results' and n < 60 * 200:
        for m in S2.pump(): R2.handle_message(m)
        R2.update(1 / 30., {'steer': 0, 'throttle': 0, 'brake': 0, 'drift': False}); frames(1, 1 / 30.); n += 1
    print('results after', n, 'frames, scene =', g.scene)
    frames(40); shot('results')
    assert g.scene == 'results'
    S2.leave(); frames(30)
    print('after guest left, racers:', len(race.racers))
    g.leave_race(); frames(5)
    print('PC MULTI PROBE OK')
except Exception:
    traceback.print_exc(); shot('error')
