# -*- coding: utf-8 -*-
"""PC 렌더 스크린샷 (여러 맵): python tests/pc_shots.py <outdir> <map,map,...> [secs]"""
import os, sys, time, importlib.util, traceback
os.environ['KART3D_OFFSCREEN'] = '1'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]; maps = [int(x) for x in sys.argv[2].split(',')]; secs = float(sys.argv[3]) if len(sys.argv) > 3 else 9
os.makedirs('/tmp/kt_probe', exist_ok=True); sys.argv[0] = '/tmp/kt_probe/pc.py'
spec = importlib.util.spec_from_file_location('kpc', os.path.join(ROOT, 'kart3d_pc.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kpc'] = K; spec.loader.exec_module(K)
g = K.Game({'window': (960, 540), 'lang': 'ko'})
def frames(n, dt=1 / 60.0):
    g.dt_override = dt
    for _ in range(n): g.taskMgr.step()
def shot(name):
    g.graphicsEngine.renderFrame(); g.win.saveScreenshot(K.Filename(os.path.join(out, 'pcs_%s.png' % name)))
for mid in maps:
    try:
        g.profile['map'] = mid; g.profile['bots'] = 7; g.profile['laps'] = 2
        t0 = time.time(); g.start_solo(); bt = time.time() - t0
        race = g.race; race.start_at = time.monotonic() + 0.2; race.auto_local = True
        frames(int(secs * 60))
        shot('%d' % mid)
        print('map %d (%s) built %.2fs  N=%d props=%d  speed %.0f' % (mid, race.track.theme['key'], bt, race.track.N, len(race.track.props), race.local.speed))
        g.leave_race()
        frames(2)
    except Exception:
        traceback.print_exc(); shot('err%d' % mid)
