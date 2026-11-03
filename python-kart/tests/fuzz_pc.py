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
KEYS = ['arrow_up', 'arrow_down', 'arrow_left', 'arrow_right', 'enter', 'escape', 'r', 't', 'space', 'w', 'a', 's', 'd', 'lshift', 'backspace', 'z', 'f', 'lcontrol']
bad = []
def frames(n, dt=1 / 30.0):
    g.dt_override = dt
    for _ in range(n): g.taskMgr.step()
frames(3)
for scene in ('menu', 'solo', 'garage', 'settings', 'set_gfx', 'set_display', 'set_audio', 'set_controls', 'set_game', 'about', 'multi', 'lobby',
              'race', 'pause_settings', 'time_attack', 'time_results', 'maps', 'editor', 'custom_solo', 'custom_race', 'lobby_custom'):
    try:
        if scene.startswith('set_'):
            g.go('menu'); g.open_settings(scene[4:])
        elif scene == 'pause_settings':
            g.session.leave(); g.profile['map_src'] = 'builtin'; g.profile['mode'] = 'speed'; g.profile['bots'] = 2; g.start_solo()
            g.race.start_at = time.monotonic() + 0.2; frames(2); g.toggle_pause(); g.open_settings('main', True)
        elif scene == 'time_attack':
            g.session.leave(); g.profile['map_src'] = 'builtin'; g.profile['mode'] = 'time'; g.profile['laps'] = 1; g.start_solo()
            g.race.start_at = time.monotonic() + 0.2; g.race.auto_local = True
        elif scene == 'time_results':
            if g.race is None or g.scene != 'race':          # 앞 장면에서 무작위 입력으로 나갔으면 새로 시작
                g.profile['map_src'] = 'builtin'; g.profile['mode'] = 'time'; g.profile['laps'] = 1; g.start_solo()
                g.race.start_at = time.monotonic() + 0.2
            if g.paused: g.toggle_pause()
            g.race.auto_local = True
            for _ in range(2400):
                g.dt_override = 1 / 30.0; g.taskMgr.step()
                if g.scene == 'results': break
            print('time attack reached', g.scene, 'laps', g.race.lap_times if g.race else None)
        elif scene == 'lobby':
            g.session.leave(); g.session.host_game(5631); g.go('lobby')
        elif scene == 'editor':
            g.maker.open(K.cmap_new('fuzz', rnd.randint(1, 1000)), None)
        elif scene == 'custom_solo':
            if not g.store.maps:
                g.store.put(K.cmap_new('fuzz map', 44))
            g.profile['map_src'] = 'custom'; g.profile['cmap'] = g.store.maps[0]['uid']; g.go('solo')
        elif scene == 'custom_race':
            g.session.leave(); g.profile['map_src'] = 'custom'; g.profile['bots'] = 3; g.start_solo(); g.race.start_at = time.monotonic() + 0.2
        elif scene == 'lobby_custom':
            g.session.leave(); g.session.host_game(5631, g.store.maps[0] if g.store.maps else None); g.go('lobby')
        elif scene == 'race':
            g.session.leave(); g.profile['map'] = rnd.randint(1, 1000); g.profile['bots'] = 4; g.start_solo(); g.race.start_at = time.monotonic() + 0.2
        else:
            g.go(scene)
        for f in range(120 if scene != 'editor' else 400):
            if g.scene == 'editor' and g.maker.ed is not None:
                mk = g.maker
                mk.mouse_override = (rnd.uniform(-1.8, 1.8), rnd.uniform(-1, 1))
                r_ = rnd.random()
                if r_ < 0.15: mk.on_down()
                elif r_ < 0.3: mk.on_up()
                elif r_ < 0.35: mk.on_wheel(rnd.choice([-1, 1]))
                elif r_ < 0.38: mk.on_rdown()
                elif r_ < 0.41: mk.on_rup()
                if rnd.random() < 0.05:
                    mk.tab = rnd.choice(['road', 'obs', 'deco', 'pad', 'set']); mk.tool = rnd.choice(['draw', 'move', 'add', 'del', 'up', 'down', 'start', 'pan'])
                    mk.line = rnd.random() < 0.5; mk.erase = rnd.random() < 0.2; mk.need_ui = True
            k = rnd.choice(KEYS)
            if rnd.random() < 0.4:
                g._kdown(k)
                if rnd.random() < 0.7: g._kup(k)
            if g.input.active and rnd.random() < 0.3:
                g._keystroke(rnd.choice('0123456789abc.:'))
            if g.scene == 'menu' and rnd.random() < 0.05:
                g.go(rnd.choice(['solo', 'garage', 'settings', 'multi']))
            if g.scene not in ('editor', 'race') and rnd.random() < 0.15:         # 마우스로 메뉴 조작
                a = g.getAspectRatio()
                pos = (rnd.uniform(-a, a), rnd.uniform(-1, 1))
                g.last_mouse = pos
                g.menu.hover(pos)
                g.menu.mouse(rnd.choice(['l', 'l', 'r', 'wu', 'wd']), pos)
            frames(1)
        g.keys.clear()
        if g.input.active: g.input.finish(False)
        if g.race and scene != 'time_attack': g.leave_race(); frames(2)
        if g.scene == 'editor' and g.maker.ed is not None:
            g.maker.save(); g.maker.leave(); frames(2)
    except Exception:
        traceback.print_exc(); bad.append(scene)
g.session.leave()
print('PC FUZZ DONE, problems:', bad)
