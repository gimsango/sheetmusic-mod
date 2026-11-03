# -*- coding: utf-8 -*-
"""크로스플레이 + 만든 맵: PC 손님 (cross_cmap_host.py 가 연 방에 접속)"""
import os, sys, time, importlib.util
os.environ['KART3D_OFFSCREEN'] = '1'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('/tmp/kt_probe/cg', exist_ok=True); sys.argv[0] = '/tmp/kt_probe/cg/pc.py'
if os.path.exists('/tmp/kt_probe/cg/kart3d_maps.json'):
    os.remove('/tmp/kt_probe/cg/kart3d_maps.json')
spec = importlib.util.spec_from_file_location('kpc', os.path.join(ROOT, 'kart3d_pc.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kpc'] = K; spec.loader.exec_module(K)
g = K.Game({'window': (640, 360), 'lang': 'ko'}); g.profile['name'] = 'PC-Guest'
def frames(n, dt=None):
    g.dt_override = dt
    for _ in range(n): g.taskMgr.step(); time.sleep(0.004)
frames(5)
time.sleep(1.5)
g.join_ip('127.0.0.1:5621')
saved = False
t0 = time.time()
while g.scene != 'race' and time.time() - t0 < 60:
    frames(3)
    cm = g.session.settings.get('cmap')
    if cm and not saved:
        saved = bool(g.store.add_copy(cm))
        print('[PC guest] lobby shows custom map:', cm['name'], '-> saved to my maps:', saved, len(g.store.maps), flush=True)
print('[PC guest] scene', g.scene, 'players', [p['name'] for p in g.session.players], flush=True)
race = g.race; race.auto_local = True
t = race.track
print('[PC guest] track sig: N=%d sum=%.3f obstacles=%d pads=%s name=%s' % (t.N, sum(t.px) + sum(t.pz), len(t.obstacles), sorted(p.get('kind', 'boost') for p in t.pads), t.info['name']), flush=True)
t_end = time.time() + 30
while time.time() < t_end:
    frames(60)
l = race.local
print('[PC guest] t=%.1f total=%.1f speed=%.1f scene=%s net=%s' % (race.t, l.total, l.speed, g.scene, g.session.net.status if g.session.net else None), flush=True)
print('[PC guest] racers:', [(r.name, r.kind, round(r.total), round(r.speed)) for r in race.racers], flush=True)
