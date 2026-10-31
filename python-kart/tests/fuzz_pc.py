# -*- coding: utf-8 -*-
"""PC 앱 퍼징: 모든 화면에 무작위 키 입력"""
import os, sys, time, random, importlib.util, traceback
os.environ['KART3D_OFFSCREEN'] = '1'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('/tmp/kt_probe/pf', exist_ok=True); sys.argv[0] = '/tmp/kt_probe/pf/pc.py'
spec = importlib.util.spec_from_file_location('kpc', os.path.join(ROOT, 'kart3d_pc.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kpc'] = K; spec.loader.exec_module(K)
g = K.Game({'window': (640, 360), 'lang': 'ko', 'port': 5631})
rnd = random.Random(11)
g.userExit = lambda: None
KEYS = ['arrow_up', 'arrow_down', 'arrow_left', 'arrow_right', 'enter', 'escape', 'r', 't', 'space', 'w', 'a', 's', 'd', 'lshift', 'backspace']
bad = []
def frames(n, dt=1 / 30.0):
    g.dt_override = dt
    for _ in range(n): g.taskMgr.step()
frames(3)
for scene in ('menu', 'solo', 'garage', 'settings', 'multi', 'lobby', 'race'):
    try:
        if scene == 'lobby':
            g.session.leave(); g.session.host_game(5631); g.go('lobby')
        elif scene == 'race':
            g.session.leave(); g.profile['map'] = rnd.randint(1, 1000); g.profile['bots'] = 4; g.start_solo(); g.race.start_at = time.monotonic() + 0.2
        else:
            g.go(scene)
        for f in range(120):
            k = rnd.choice(KEYS)
            if rnd.random() < 0.4:
                g._kdown(k)
                if rnd.random() < 0.7: g._kup(k)
            if g.input.active and rnd.random() < 0.3:
                g._keystroke(rnd.choice('0123456789abc.:'))
            if g.scene == 'menu' and rnd.random() < 0.05:
                g.go(rnd.choice(['solo', 'garage', 'settings', 'multi']))
            frames(1)
        g.keys.clear()
        if g.input.active: g.input.finish(False)
        if g.race: g.leave_race(); frames(2)
    except Exception:
        traceback.print_exc(); bad.append(scene)
g.session.leave()
print('PC FUZZ DONE, problems:', bad)
