import os, sys, time, importlib.util
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('/tmp/kt_probe/h', exist_ok=True); sys.argv[0] = '/tmp/kt_probe/h/app.py'
spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
app = K.App({'window': (800, 450), 'lang': 'ko'}); app.profile['port'] = 5620; app.profile['map'] = 11
def frames(n, dt=1 / 60.0):
    for _ in range(n):
        t1 = time.time(); app.step(dt); time.sleep(max(0.0, dt - (time.time() - t1)))
assert app.session.host_game(5620); app.scene = 'lobby'
t0 = time.time()
while len(app.session.players) < 2 and time.time() - t0 < 60: frames(5)
print('[PHONE host] players:', [p['name'] for p in app.session.players], flush=True)
app.session.send_settings(bots=2, laps=1); frames(30)
app.session.start_race(); t0 = time.time()
while app.scene != 'race' and time.time() - t0 < 20: frames(3)
race = app.race; race.auto_local = True
frames(60 * 42)
print('[PHONE host] racers:', [(r.name, r.kind, round(r.total), round(r.speed)) for r in race.racers], flush=True)
