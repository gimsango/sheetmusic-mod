# -*- coding: utf-8 -*-
"""폰 앱 퍼징: 모든 화면에 무작위 터치/키 입력 -> 예외가 없어야 한다"""
import os, sys, time, random, importlib.util
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('/tmp/kt_probe/f', exist_ok=True); sys.argv[0] = '/tmp/kt_probe/f/app.py'
spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
pg = K.pygame
rnd = random.Random(7)
bad = []
for (W, H) in ((960, 480), (480, 960), (1280, 720)):
    app = K.App({'window': (W, H), 'lang': rnd.choice(['ko', 'en'])})
    app.profile['port'] = 5630
    for scene in ('menu', 'solo', 'garage', 'settings', 'settings_sound', 'settings_game', 'multi', 'lobby_host', 'race', 'results', 'maps', 'editor',
                  'custom_solo', 'custom_race', 'lobby_custom', 'time_attack', 'time_results'):
        try:
            app.err = ''
            if scene in ('settings_sound', 'settings_game'):
                app.go('settings'); app.set_tab = scene.split('_')[1]
            elif scene == 'time_attack':
                if app.race: app.leave_race()
                app.session.leave(); app.profile['map_src'] = 'builtin'; app.profile['mode'] = 'time'; app.profile['laps'] = 1
                app.start_solo(); app.race.start_at = time.monotonic() + 0.3
            elif scene == 'time_results':
                app.race.auto_local = True; app.scene = 'results'
            elif scene == 'lobby_host':
                app.session.leave(); app.session.host_game(5630); app.scene = 'lobby'
            elif scene == 'editor':
                app.maker.open(K.cmap_new('fuzz', rnd.randint(1, 1000)), None)
            elif scene == 'custom_solo':
                if not app.store.maps:
                    app.store.put(K.cmap_new('fuzz map', 33))
                app.profile['map_src'] = 'custom'; app.profile['cmap'] = app.store.maps[0]['uid']; app.go('solo')
            elif scene == 'custom_race':
                app.session.leave(); app.profile['map_src'] = 'custom'; app.profile['bots'] = 4; app.start_solo(); app.race.start_at = time.monotonic() + 0.3
            elif scene == 'lobby_custom':
                if app.race: app.leave_race()
                app.session.leave(); app.session.host_game(5630, app.store.maps[0] if app.store.maps else None); app.scene = 'lobby'; app.lobby_src = 'custom'
            elif scene == 'race':
                app.session.leave(); app.profile['map'] = rnd.randint(1, 1000); app.profile['bots'] = 5; app.start_solo(); app.race.start_at = time.monotonic() + 0.3
            elif scene == 'results':
                app.race.auto_local = True; app.scene = 'results'
            else:
                app.go(scene)
            for f in range(150 if scene != 'editor' else 400):
                if scene == 'editor' and app.maker.ed is not None and rnd.random() < 0.08:
                    app.maker.tab = rnd.choice(['road', 'obs', 'deco', 'pad', 'set'])
                    app.maker.tool = rnd.choice(['draw', 'move', 'add', 'del', 'up', 'down', 'start', 'pan'])
                    app.maker.line = rnd.random() < 0.5; app.maker.erase = rnd.random() < 0.2
                    if rnd.random() < 0.3: app.maker.wheel += rnd.choice([-1, 1])
                if rnd.random() < 0.35:
                    app.ptr.taps.append((rnd.uniform(0, W), rnd.uniform(0, H)))
                if rnd.random() < 0.2:
                    app.ptr.fingers[rnd.randint(0, 3)] = (rnd.uniform(0, W), rnd.uniform(0, H))
                if rnd.random() < 0.1:
                    app.ptr.fingers.pop(rnd.randint(0, 3), None)
                app.step(1 / 30.0)
                if app.err == 'error':
                    bad.append((W, H, scene, f)); break
            app.ptr.fingers.clear()
            if app.kb: app.close_kb('cancel')
            if scene in ('results', 'custom_race', 'time_results') and app.race: app.leave_race()
            if scene == 'editor' and app.maker.ed is not None:
                app.maker.save(); app.maker.leave()
        except Exception as e:
            import traceback; traceback.print_exc(); bad.append((W, H, scene, repr(e)))
    app.session.leave()
# 손상된 설정 파일이어도 켜져야 한다 (형식이 틀린 값은 무시)
import json
with open('/tmp/kt_probe/f/kart3d_profile.json', 'w') as f:
    json.dump({'vol_master': 'loud', 'laps': 2.7, 'kart': -5, 'records': [1, 2], 'music': 'yes', 'units': 7, 'cam_dist': 9, 'bots': None, 'name': 12}, f)
try:
    app = K.App({'window': (800, 400), 'lang': 'ko'})
    for _ in range(30): app.step(1 / 30.0)
    assert app.profile['laps'] == 2 and app.profile['vol_master'] == 1.0 and isinstance(app.profile['records'], dict), app.profile
    assert 0 <= app.profile['kart'] < K.KART_COUNT and app.err != 'error'
    print('corrupt profile OK:', {k: app.profile[k] for k in ('laps', 'kart', 'vol_master', 'music', 'units', 'cam_dist', 'bots', 'name')})
except Exception as e:
    import traceback; traceback.print_exc(); bad.append(('corrupt profile', repr(e)))
os.remove('/tmp/kt_probe/f/kart3d_profile.json')
print('FUZZ DONE, problems:', bad)
