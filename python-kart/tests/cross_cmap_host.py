# -*- coding: utf-8 -*-
"""크로스플레이 + 만든 맵: 폰 앱이 '내 맵'으로 방을 열고 PC 손님이 같은 맵으로 달린다 (cross_cmap_guest.py 와 같이 실행)"""
import os, sys, time, math, importlib.util
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('/tmp/kt_probe/ch', exist_ok=True); sys.argv[0] = '/tmp/kt_probe/ch/app.py'
for f in ('kart3d_maps.json', 'kart3d_profile.json'):
    if os.path.exists('/tmp/kt_probe/ch/' + f):
        os.remove('/tmp/kt_probe/ch/' + f)
spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
app = K.App({'window': (800, 450), 'lang': 'ko'}); app.profile['port'] = 5621
# 맵 만들기: 그린 코스 + 장애물 + 화산 기둥 + 발판
ed = K.MapEdit(K.cmap_new('크로스 테스트 맵', 205))
ed.set_stroke([(math.cos(a / 50.0 * K.TAU) * 240 * (1 + 0.15 * math.sin(a / 50.0 * 3 * K.TAU)), math.sin(a / 50.0 * K.TAU) * 160) for a in range(51)])
tr = ed.preview()
for k in range(1, 6):
    x, y, z, h = tr.pose_at(tr.N * k // 7, (-1) ** k * 3.5)
    ed.add_obj('lavapillar' if k % 2 else 'crate', x, z)
x, y, z, h = tr.pose_at(tr.N // 2, 0.0)
ed.add_obj('jump', x, z)
uid = app.store.put(ed.result())
app.profile['map_src'] = 'custom'; app.profile['cmap'] = uid
def frames(n, dt=1 / 60.0):
    for _ in range(n):
        t1 = time.time(); app.step(dt); time.sleep(max(0.0, dt - (time.time() - t1)))
cm = app.store.get(uid)
assert app.session.host_game(5621, cm); app.scene = 'lobby'; app.lobby_src = 'custom'
t0 = time.time()
while len(app.session.players) < 2 and time.time() - t0 < 60: frames(5)
print('[PHONE host] players:', [p['name'] for p in app.session.players], 'cmap:', (app.session.settings.get('cmap') or {}).get('name'), flush=True)
app.session.send_settings(bots=2, laps=1); frames(40)
app.session.start_race(); t0 = time.time()
while app.scene != 'race' and time.time() - t0 < 20: frames(3)
race = app.race; race.auto_local = True
t = race.track
print('[PHONE host] track sig: N=%d sum=%.3f obstacles=%d pads=%s name=%s' % (t.N, sum(t.px) + sum(t.pz), len(t.obstacles), sorted(p.get('kind', 'boost') for p in t.pads), t.info['name']), flush=True)
frames(60 * 40)
print('[PHONE host] racers:', [(r.name, r.kind, round(r.total), round(r.speed)) for r in race.racers], flush=True)
