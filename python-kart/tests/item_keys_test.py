# -*- coding: utf-8 -*-
"""키 1/2/3 으로 아이템 사용 (폰 버전: pygame 이벤트, PC 버전: Panda3D 이벤트) + 터치 슬롯 탭"""
import os, sys, time, importlib.util
which = sys.argv[1] if len(sys.argv) > 1 else 'phone'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if which == 'phone':
    os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
    os.makedirs('/tmp/kt_probe_k', exist_ok=True); sys.argv[0] = '/tmp/kt_probe_k/app.py'
    spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
    K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
    pg = K.pygame
    app = K.App({'window': (900, 500), 'lang': 'ko'})
    app.profile['mode'] = 'item'; app.profile['bots'] = 3
    app.start_solo(); race = app.race; race.start_at = time.monotonic() + 0.1
    for _ in range(30): app.step(1 / 60.)
    L = race.local; IK = K.ITEM_BY_KEY
    L.items = [IK['booster'], IK['shield'], IK['banana']]; L.uses = [1, 1, 1]; L.roll = [0, 0, 0]
    for key, slot in ((pg.K_1, 0), (pg.K_2, 1), (pg.K_3, 2)):
        pg.event.post(pg.event.Event(pg.KEYDOWN, key=key, mod=0, unicode=str(slot + 1), scancode=0))
        app.step(1 / 60.)
        pg.event.post(pg.event.Event(pg.KEYUP, key=key, mod=0, scancode=0))
        app.step(1 / 60.)
        assert L.items[slot] is None, ('key', slot, L.items)
    assert L.sim.shield_n == 1 and race.items.seq >= 1, (L.sim.shield_n, race.items.seq)   # 바나나는 바로 뒤 봇이 밟을 수도 있어서 생성 여부만 확인
    # 터치: 슬롯 탭
    L.items = [None, IK['coin'], None]; L.uses = [0, 1, 0]; L.roll = [0, 0, 0]
    app.step(1 / 60.)
    r = app.item_rects[1]
    app.ptr.taps.append(r.center); app.step(1 / 60.)
    assert L.items[1] is None and L.sim.coins == 1, (L.items, L.sim.coins)
    print('PHONE ITEM KEYS OK (pygame %s)' % pg.version.ver)
else:
    os.environ['KART3D_OFFSCREEN'] = '1'
    os.makedirs('/tmp/kt_probe_k2', exist_ok=True); sys.argv[0] = '/tmp/kt_probe_k2/pc.py'
    spec = importlib.util.spec_from_file_location('kpc', os.path.join(ROOT, 'kart3d_pc.py'))
    K = importlib.util.module_from_spec(spec); sys.modules['kpc'] = K; spec.loader.exec_module(K)
    g = K.Game({'window': (640, 360), 'lang': 'ko'})
    def frames(n):
        g.dt_override = 1 / 60.
        for _ in range(n): g.taskMgr.step()
    g.profile['mode'] = 'item'; g.profile['bots'] = 3
    frames(3); g.start_solo(); race = g.race; race.start_at = time.monotonic() + 0.1; frames(30)
    L = race.local; IK = K.ITEM_BY_KEY
    L.items = [IK['booster'], IK['shield'], IK['banana']]; L.uses = [1, 1, 1]; L.roll = [0, 0, 0]
    for k, slot in (('1', 0), ('2', 1), ('3', 2)):
        g.messenger.send(k); frames(1); g.messenger.send(k + '-up'); frames(1)
        assert L.items[slot] is None, ('key', slot, L.items)
    assert L.sim.shield_n == 1 and race.items.seq >= 1, (L.sim.shield_n, race.items.seq)   # 바나나는 바로 뒤 봇이 밟을 수도 있어서 생성 여부만 확인
    # ↓ 누른 채로 미사일 -> 뒤로 발사 (생성되는 순간을 기록: 바로 뒤 봇에 맞아 사라질 수 있으므로)
    spawned = []
    orig = race.items._spawn
    def rec(owner, it, sp, eid=None):
        e = orig(owner, it, sp, eid); spawned.append((e.kind, e.vx, e.vz)); return e
    race.items._spawn = rec
    L.items[0] = IK['missile']; L.uses[0] = 1; L.roll[0] = 0
    g.messenger.send('arrow_down'); frames(1); g.messenger.send('1'); frames(1); g.messenger.send('arrow_down-up'); frames(1)
    import math
    k, vx, vz = spawned[-1]
    fwd = math.sin(L.h) * vx + math.cos(L.h) * vz
    assert k == 'shot' and fwd < 0, (k, fwd)
    print('PC ITEM KEYS OK (backward shot ok)')
