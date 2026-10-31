# -*- coding: utf-8 -*-
"""PC(Panda3D) 헤드리스 테스트 (tinydisplay 오프스크린): python tests/pc_probe.py <outdir> [map]"""
import os, sys, time, importlib.util, traceback
os.environ['KART3D_OFFSCREEN'] = '1'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
mid = int(sys.argv[2]) if len(sys.argv) > 2 else 1
os.makedirs('/tmp/kt_probe', exist_ok=True); sys.argv[0] = '/tmp/kt_probe/pc.py'
for f in ('/tmp/kt_probe/kart3d_profile.json',):
    if os.path.exists(f): os.remove(f)
spec = importlib.util.spec_from_file_location('kpc', os.path.join(ROOT, 'kart3d_pc.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kpc'] = K; spec.loader.exec_module(K)
g = K.Game({'window': (960, 540), 'lang': 'ko'})
g.profile['map'] = mid
print('font', g.font, 'lang', K.LANG)
def frames(n, dt=1 / 60.0):
    g.dt_override = dt
    for _ in range(n): g.taskMgr.step()
def shot(name):
    g.graphicsEngine.renderFrame()
    g.win.saveScreenshot(K.Filename(os.path.join(out, 'pc_%s.png' % name)))
try:
    t0 = time.time(); frames(5); print('menu ready in %.1fs' % (time.time() - t0)); frames(30); shot('menu')
    g.go('solo'); frames(10); shot('solo')
    g.go('garage'); frames(10); shot('garage')
    g.go('settings'); frames(5); shot('settings')
    g.go('multi'); frames(30); shot('multi')
    g.go('menu'); frames(3)
    g.profile['map'] = mid; g.profile['bots'] = 6; g.profile['laps'] = 2
    t0 = time.time(); g.start_solo(); print('race built in %.1fs' % (time.time() - t0))
    race = g.race; race.start_at = time.monotonic() + 0.4
    frames(40); shot('countdown')
    race.auto_local = True
    frames(60 * 8); shot('race')
    loc = race.local
    print('race: t=%.1f speed=%.0f pos=%d' % (race.t, loc.speed, race.ranking().index(loc) + 1))
    print('PC PROBE OK')
except Exception:
    traceback.print_exc(); shot('error')
