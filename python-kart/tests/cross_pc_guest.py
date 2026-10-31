import os, sys, time, importlib.util
os.environ['KART3D_OFFSCREEN'] = '1'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('/tmp/kt_probe/g', exist_ok=True); sys.argv[0] = '/tmp/kt_probe/g/pc.py'
spec = importlib.util.spec_from_file_location('kpc', os.path.join(ROOT, 'kart3d_pc.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kpc'] = K; spec.loader.exec_module(K)
g = K.Game({'window': (640, 360), 'lang': 'ko'}); g.profile['name'] = 'PC-Guest'
def frames(n, dt=None):
    g.dt_override = dt
    for _ in range(n): g.taskMgr.step(); time.sleep(0.004)
frames(5)
time.sleep(1.5)
g.join_ip('127.0.0.1:5620')
t0 = time.time()
while g.scene != 'race' and time.time() - t0 < 60: frames(3)
print('[PC guest] scene', g.scene, 'players', [p['name'] for p in g.session.players], flush=True)
race = g.race; race.auto_local = True
t_end = time.time() + 36
while time.time() < t_end:
    frames(60)
    l = race.local
    print('[PC guest] t=%.1f phase=%s total=%.1f speed=%.1f scene=%s ses=%s err=%r net=%s' % (race.t, race.phase, l.total, l.speed, g.scene, g.session.state, g.session.error, g.session.net.status if g.session.net else None), flush=True)
print('[PC guest] racers:', [(r.name, r.kind, round(r.total), round(r.speed)) for r in race.racers], flush=True)
