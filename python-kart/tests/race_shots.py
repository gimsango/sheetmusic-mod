# -*- coding: utf-8 -*-
"""레이스 장면 스크린샷 (자동 주행): python3 tests/race_shots.py <outdir> <map> [W H]"""
import os, sys, time, importlib.util
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]; mid = int(sys.argv[2]); W = int(sys.argv[3]) if len(sys.argv) > 3 else 1000; H = int(sys.argv[4]) if len(sys.argv) > 4 else 500
os.makedirs('/tmp/kt_probe', exist_ok=True); sys.argv[0] = '/tmp/kt_probe/app.py'
spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
pg = K.pygame
app = K.App({'window': (W, H), 'lang': 'ko'})
app.profile['map'] = mid; app.profile['bots'] = 9; app.profile['laps'] = 3; app.profile['quality'] = 1
app.start_solo(); race = app.race; race.auto_local = True
race.start_at = time.monotonic() + 3600
def frames(n, dt=1/60.): 
    for _ in range(n): app.step(dt)
# 카운트다운 중 (그리드)
race.count_left = 3.0; frames(30)
pg.image.save(app.screen, os.path.join(out, 'rs_%d_grid.png' % mid))
race.start_at = time.monotonic() - 1
frames(60 * 6); pg.image.save(app.screen, os.path.join(out, 'rs_%d_a.png' % mid))
# AI 조향 + 강제 드리프트 (조향이 클 때 드리프트 버튼 누름)
orig = race.local.brain.drive
hold = [False]
stat = {'maxsteer': 0.0, 'drift_frames': 0, 'maxtier': 0}
def drv(kart, dt, pt, rubber=True):
    inp = orig(kart, dt, pt, rubber)
    st = abs(inp['steer']); stat['maxsteer'] = max(stat['maxsteer'], st)
    if st > 0.3 and kart.speed > 25: hold[0] = True
    elif st < 0.06: hold[0] = False
    inp['drift'] = hold[0]
    if kart.drifting: kart.drift_charge += dt * 2.5     # (테스트용) 빨리 충전
    return inp
race.local.brain.drive = drv
shots = 0; n = 0
while shots < 2 and n < 60 * 120:
    frames(1); n += 1
    loc = race.local
    stat['drift_frames'] += 1 if loc.drifting else 0; stat['maxtier'] = max(stat['maxtier'], loc.tier if loc.drifting else 0)
    if shots == 0 and loc.drifting and loc.tier >= 1:
        frames(6); pg.image.save(app.screen, os.path.join(out, 'rs_%d_drift.png' % mid)); shots += 1
    elif shots == 1 and loc.boosting and loc.sim.boost_t > 0.3:
        frames(8); pg.image.save(app.screen, os.path.join(out, 'rs_%d_boost.png' % mid)); shots += 1
print(stat); print('map', mid, 'shots', shots, 'after', n, 'frames; speed %.0f' % race.local.speed, 'fps_ema %.0f' % app.fps_ema)
