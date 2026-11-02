# -*- coding: utf-8 -*-
"""폰 앱이 호스트, 헤드리스 게스트(코어 Session)가 접속: 로비 -> 시작 -> 원격 카트 렌더/동기화 확인"""
import os, sys, time, importlib.util, traceback
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
os.makedirs('/tmp/kt_probe', exist_ok=True); sys.argv[0] = '/tmp/kt_probe/app.py'
spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
pg = K.pygame
app = K.App({'window': (1000, 520), 'lang': 'ko'})
app.profile['port'] = 5613; app.profile['map'] = 4
def frames(n, dt=1 / 60.0):
    for _ in range(n): app.step(dt)
assert app.session.host_game(5613); app.scene = 'lobby'; frames(30)
P2 = K.Profile('/tmp/kt_probe/guest.json'); P2['name'] = 'GuestPC'; P2['kart'] = 77777
S2 = K.Session(P2); S2.join_game('127.0.0.1', 5613)
for _ in range(60): app.step(1 / 60.); S2.pump(); time.sleep(0.01)
print('players:', [p['name'] for p in app.session.players], '| guest state', S2.state)
assert len(app.session.players) == 2
app.session.send_settings(bots=2, laps=2); frames(20)
for _ in range(10): S2.pump(); time.sleep(0.01)
pg.image.save(app.screen, os.path.join(out, 'mp_lobby.png'))
app.session.start_race()
for _ in range(40): app.step(1 / 60.); S2.pump(); time.sleep(0.01)
assert app.scene == 'race' and S2.start_msg, (app.scene, S2.start_msg)
R2 = K.Race(4, 2, S2.entries_from_start(S2.start_msg), multi=True, is_host=S2.is_host, countdown=0.0, net=S2.net, auto_local=True, items=bool(S2.start_msg.get('items')))
race = app.race; race.auto_local = True; race.start_at = time.monotonic() - 1
for f in range(60 * 14):
    for m in S2.pump(): R2.handle_message(m)
    R2.update(1 / 60., {'steer': 0, 'throttle': 0, 'brake': 0, 'drift': False})
    app.step(1 / 60.)
    if f % 3 == 0: time.sleep(0.002)
pg.image.save(app.screen, os.path.join(out, 'mp_race.png'))
print('host racers:', [(r.name, r.kind, round(r.total, 1), round(r.speed)) for r in race.racers])
print('guest racers:', [(r.name, r.kind, round(r.total, 1), round(r.speed)) for r in R2.racers])
assert all(r.total > 30 for r in race.racers) and all(r.total > 30 for r in R2.racers)
S2.leave(); frames(30)
print('after guest left, host sees racers:', len(race.racers))
print('MULTI APP PROBE OK')
