# -*- coding: utf-8 -*-
"""폰 버전 아이템전 화면 확인용 스크린샷: python3 tests/item_shots.py <outdir> [W H]"""
import os, sys, time, importlib.util, traceback, math
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
W = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
H = int(sys.argv[3]) if len(sys.argv) > 3 else 520
os.makedirs('/tmp/kt_probe_i', exist_ok=True); sys.argv[0] = '/tmp/kt_probe_i/app.py'
if os.path.exists('/tmp/kt_probe_i/kart3d_profile.json'): os.remove('/tmp/kt_probe_i/kart3d_profile.json')
spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
pg = K.pygame
app = K.App({'window': (W, H), 'lang': 'ko'})
tag = '%dx%d' % (W, H)
def frames(n, dt=1 / 60.0):
    for _ in range(n): app.step(dt)
def shot(name): pg.image.save(app.screen, os.path.join(out, 'it_%s_%s.png' % (name, tag)))
try:
    # 아이콘 100종 갤러리
    app.screen.fill((14, 18, 34))
    cols = 20; sz = min(W // cols, H // 6) - 4
    for i in range(K.ITEM_COUNT):
        x = (i % cols) * (sz + 4) + 4; y = (i // cols) * (sz + 22) + 4
        app.screen.blit(app.icons.get(i, sz), (x, y))
        app.ui.text(app.screen, str(i + 1), x + 2, y + sz, 12, (200, 200, 220))
    shot('icons')
    app.go('solo'); frames(10); shot('solo')
    app.profile['map'] = 6; app.profile['bots'] = 7; app.profile['laps'] = 3
    app.start_solo(); race = app.race
    race.start_at = time.monotonic() + 0.2
    frames(30)
    L = race.local; S = L.sim
    IK = K.ITEM_BY_KEY
    L.items = [IK['homing3'], IK['banana3'], IK['star']]; L.uses = [3, 3, 1]; L.roll = [0, 0, 0.5]
    frames(10); shot('bar_roll')
    frames(40); shot('bar_ready')
    # 앞에 상자가 보이게: 상자 줄 바로 앞으로 이동
    b = race.items.boxes[0]
    x, y, z, h = race.track.pose_at((b['idx'] - 9) % race.track.N, 0)
    S.teleport(x, z, h); S.vx = math.sin(h) * 20; S.vz = math.cos(h) * 20
    frames(12); shot('boxes')
    # 함정 늘어놓기 + 투사체
    for key in ('banana', 'oil', 'tacks', 'mine', 'glue', 'icepatch', 'barricade', 'reverseportal', 'fakebox'):
        L.items[1] = IK[key]; L.uses[1] = 1; L.roll[1] = 0
        race.use_item(1)
        frames(9)
    # 뒤를 보도록 카메라: 카트를 반대로 돌리기 대신 함정 위치로 순간이동해서 앞쪽에 함정이 보이게
    tr = race.track
    x, y, z, h = tr.pose_at((S.q.prog - 50 / tr.ds) % tr.N, 0)
    S.teleport(x, z, h); S.vx = S.vz = 0
    for rc in race.racers:
        if rc is not L: rc.sim.vx = rc.sim.vz = 0
    frames(3); shot('traps')
    for key in ('missile', 'homing', 'bomb', 'tornado', 'laser', 'seeker'):
        L.items[0] = IK[key]; L.uses[0] = 1; L.roll[0] = 0
        race.use_item(0); frames(4)
    frames(6); shot('shots')
    # 상태 효과: 봇들에게 여러 효과 + 내 카트 무적
    bots = [rc for rc in race.racers if rc is not L]
    for i, (rc, fx) in enumerate(zip(bots, ('spin', 'shrink', 'freeze', 'launch'))):
        x, y, z, h = tr.pose_at((S.q.prog + (14 + i * 6) / tr.ds) % tr.N, (-1) ** i * 3.0)
        rc.sim.teleport(x, z, h); rc.sim.fx_reset(); rc.sim.vx = rc.sim.vz = 0
        rc.sim.hit(fx)
    x, y, z, h = tr.pose_at((S.q.prog + 38 / tr.ds) % tr.N, 0); bots[4].sim.teleport(x, z, h); bots[4].sim.fx_reset(); bots[4].sim.giant_t = 8
    x, y, z, h = tr.pose_at((S.q.prog + 26 / tr.ds) % tr.N, -4); bots[5].sim.teleport(x, z, h); bots[5].sim.fx_reset(); bots[5].sim.shield_n = 2; bots[5].sim.shield_t = 9
    S.star_t = 6
    frames(8); shot('effects')
    L.items = [IK['lightning'], None, None]; L.uses = [1, 0, 0]; L.roll = [0, 0, 0]
    race.use_item(0); frames(3); shot('lightning')
    S.fx_reset(); S.hit('blind', 3.0); frames(10); shot('ink')
    S.fx_reset(); S.hit('reverse', 3.0); S.shield_n = 2; S.shield_t = 5; S.coins = 4; frames(5); shot('status')
    race.auto_local = True
    n = 0
    while app.scene != 'results' and n < 60 * 200:
        frames(1, 1 / 30.0); n += 1
        if n == 300: shot('auto_mid')
    print('finished in %d frames' % n)
    frames(20); shot('results')
    print('ITEM SHOTS OK')
except Exception:
    traceback.print_exc(); shot('error')
