# -*- coding: utf-8 -*-
"""PC(Panda3D) 아이템전 화면 확인 (tinydisplay 오프스크린): python tests/pc_item_shots.py <outdir>"""
import os, sys, time, importlib.util, traceback, math
os.environ['KART3D_OFFSCREEN'] = '1'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
os.makedirs('/tmp/kt_probe_pi', exist_ok=True); sys.argv[0] = '/tmp/kt_probe_pi/pc.py'
if os.path.exists('/tmp/kt_probe_pi/kart3d_profile.json'): os.remove('/tmp/kt_probe_pi/kart3d_profile.json')
spec = importlib.util.spec_from_file_location('kpc', os.path.join(ROOT, 'kart3d_pc.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kpc'] = K; spec.loader.exec_module(K)
g = K.Game({'window': (1024, 576), 'lang': 'ko'})
def frames(n, dt=1 / 60.0):
    g.dt_override = dt
    for _ in range(n): g.taskMgr.step()
def shot(name):
    g.graphicsEngine.renderFrame()
    g.win.saveScreenshot(K.Filename(os.path.join(out, 'pci_%s.png' % name)))
try:
    frames(5); g.go('solo'); frames(5); shot('solo')
    g.profile['map'] = 6; g.profile['bots'] = 7; g.profile['laps'] = 3
    g.start_solo(); race = g.race; race.start_at = time.monotonic() + 0.2
    frames(30)
    L = race.local; S = L.sim; IK = K.ITEM_BY_KEY; tr = race.track
    L.items = [IK['homing3'], IK['banana3'], IK['star']]; L.uses = [3, 3, 1]; L.roll = [0, 0, 0.5]
    frames(8); shot('bar_roll'); frames(40); shot('bar_ready')
    b = race.items.boxes[0]
    x, y, z, h = tr.pose_at((b['idx'] - 9) % tr.N, 0)
    S.teleport(x, z, h); S.vx = math.sin(h) * 20; S.vz = math.cos(h) * 20
    frames(12); shot('boxes')
    for key in ('banana', 'oil', 'tacks', 'mine', 'glue', 'icepatch', 'barricade', 'reverseportal', 'fakebox'):
        L.items[1] = IK[key]; L.uses[1] = 1; L.roll[1] = 0
        race.use_item(1); frames(9)
    x, y, z, h = tr.pose_at((S.q.prog - 50 / tr.ds) % tr.N, 0)
    S.teleport(x, z, h); S.vx = S.vz = 0
    for rc in race.racers:
        if rc is not L: rc.sim.vx = rc.sim.vz = 0
    frames(3); shot('traps')
    for key in ('missile', 'homing', 'bomb', 'tornado', 'laser', 'seeker'):
        L.items[0] = IK[key]; L.uses[0] = 1; L.roll[0] = 0
        race.use_item(0); frames(4)
    frames(6); shot('shots')
    bots = [rc for rc in race.racers if rc is not L]
    for i, (rc, fx) in enumerate(zip(bots, ('spin', 'shrink', 'freeze', 'launch'))):
        x, y, z, h = tr.pose_at((S.q.prog + (14 + i * 6) / tr.ds) % tr.N, (-1) ** i * 3.0)
        rc.sim.teleport(x, z, h); rc.sim.fx_reset(); rc.sim.vx = rc.sim.vz = 0; rc.sim.hit(fx)
    x, y, z, h = tr.pose_at((S.q.prog + 38 / tr.ds) % tr.N, 0); bots[4].sim.teleport(x, z, h); bots[4].sim.fx_reset(); bots[4].sim.giant_t = 8
    x, y, z, h = tr.pose_at((S.q.prog + 26 / tr.ds) % tr.N, -4); bots[5].sim.teleport(x, z, h); bots[5].sim.fx_reset(); bots[5].sim.shield_n = 2; bots[5].sim.shield_t = 9
    S.star_t = 6
    frames(8); shot('effects')
    L.items = [IK['lightning'], None, None]; L.uses = [1, 0, 0]; L.roll = [0, 0, 0]
    race.use_item(0); frames(3); shot('lightning')
    S.fx_reset(); S.hit('blind', 3.0); frames(10); shot('ink')
    S.fx_reset(); S.hit('reverse', 3.0); S.shield_n = 2; S.shield_t = 5; S.coins = 4; frames(5); shot('status')
    race.auto_local = True
    t0 = time.time(); n = 0
    while g.scene != 'results' and n < 60 * 220:
        frames(1, 1 / 30.0); n += 1
    print('auto race done frames=%d wall=%.1fs ents_max?' % (n, time.time() - t0))
    frames(20); shot('results')
    g.leave_race(); frames(5); shot('menu_after')
    print('PC ITEM SHOTS OK')
except Exception:
    traceback.print_exc(); shot('error')
