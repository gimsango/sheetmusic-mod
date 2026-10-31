# -*- coding: utf-8 -*-
"""폰 렌더러 헤드리스 스크린샷: python3 tests/render_probe.py <outdir> <map,map,...> [quality] [seconds]"""
import os, sys, time, importlib.util
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
pg = K.pygame
out = sys.argv[1]; maps = [int(x) for x in sys.argv[2].split(',')]
quality = int(sys.argv[3]) if len(sys.argv) > 3 else 1
secs = float(sys.argv[4]) if len(sys.argv) > 4 else 12
pg.init(); SW, SH = 960, 432
screen = pg.display.set_mode((SW, SH))
for mid in maps:
    race = K.Race(mid, 3, K.solo_entries('Me', 31337 + mid, 7, seed=mid), countdown=0.0, auto_local=True)
    R = K.Renderer(SW, SH, quality); R.set_track(race.track)
    cam = K.ChaseCam(); inp = {'steer': 0, 'throttle': 0, 'brake': 0, 'drift': False}
    n = int(secs * 60)
    for f in range(n):
        race.update(1 / 60.0, inp)
    loc = race.local
    times = []
    for f in range(30):
        race.update(1 / 60.0, inp)
        t0 = time.time()
        cp = cam.update(1 / 60.0, loc, loc.sim.stats['max_speed'])
        tr = race.track; i0 = loc.idx
        dirn = 1 if ((K.math.sin(cp[3]) * tr.tx[i0] + K.math.cos(cp[3]) * tr.tz[i0]) >= 0) else -1
        surf = R.render(race, cp, i0, dirn, 0.0, loc.speed / loc.sim.stats['max_speed'], f / 60.0)
        times.append(time.time() - t0)
    scaled = pg.transform.scale(surf, (SW, SH))
    pg.image.save(scaled, os.path.join(out, 'phone_%d_q%d.png' % (mid, quality)))
    times.sort()
    print('map %d  N=%d  render median %.1f ms  max %.1f ms  (internal %dx%d)' % (mid, race.track.N, times[len(times) // 2] * 1000, times[-1] * 1000, R.rw, R.rh))
