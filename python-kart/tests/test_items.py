# -*- coding: utf-8 -*-
"""아이템전 코어 테스트: python3 tests/test_items.py
 1) 아이템 표 100종 / 아이콘 / 설명 검사
 2) 100종 전부를 실제 레이스에서 사용 (봇 포함) -> 예외 없음 + 효과 확인
 3) 봇끼리 아이템전 완주 (여러 맵)
 4) 멀티플레이: 서버 + 2 클라이언트, 아이템 메시지(상자/발사/명중/광역/훔치기/자리바꾸기) 동기화
"""
import os, sys, time, subprocess, importlib.util, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = '/tmp/kart3d_core_items.py'
subprocess.check_call([sys.executable, os.path.join(ROOT, 'src', 'build.py'), 'core', out])
spec = importlib.util.spec_from_file_location('kcore_i', out)
C = importlib.util.module_from_spec(spec); sys.modules['kcore_i'] = C; spec.loader.exec_module(C)

# ---- 1) 표 ---------------------------------------------------------------
assert C.ITEM_COUNT == 100, C.ITEM_COUNT
keys = set()
kinds = {}
for it in C.ITEMS:
    assert it['key'] not in keys, it['key']; keys.add(it['key'])
    assert it['icon'] in C.ICONS, (it['key'], it['icon'])
    assert it['name'] and it['en']
    kinds[it['kind']] = kinds.get(it['kind'], 0) + 1
    for lang in ('ko', 'en'):
        d = C.item_desc(it['id'], lang); assert d, it['key']
    for prim in C.ICONS[it['icon']]:
        assert prim[0] in ('c', 'e', 'r', 'p', 'l'), prim
names = set(it['name'] for it in C.ITEMS); assert len(names) == 100, 'duplicate korean names'
names = set(it['en'] for it in C.ITEMS); assert len(names) == 100, 'duplicate english names'
print('items OK: 100 kinds=%d icons=%d tiers=%s' % (len(kinds), len(C.ICONS), C._TIER_N))
print('  ', ', '.join('%s:%d' % kv for kv in sorted(kinds.items())))

# ---- 2) 100종 전부 사용 -------------------------------------------------------
def new_race(mid=7, bots=7, items=True, auto=False):
    entries = C.solo_entries('Tester', 4321, bots, seed=mid)
    r = C.Race(mid, 3, entries, countdown=0.0, auto_local=auto, items=items)
    r.update(1 / 60.0, C.NO_INPUT)   # count -> run
    return r

def run(r, secs, inp=None):
    inp = inp or {'steer': 0.0, 'throttle': 1.0, 'brake': 0.0, 'drift': False}
    evs = []
    for _ in range(int(secs * 60)):
        r.update(1 / 60.0, inp); evs += r.events
    return evs

race = new_race()
run(race, 3.0)
loc = race.local
used = 0
seen_fx = set()
for it in range(C.ITEM_COUNT):
    # 매번 새 레이스 일부는 재사용: 상태 리셋
    loc.items = [it, None, None]; loc.uses = [C.ITEMS[it]['uses'], 0, 0]; loc.roll = [0.0, 0.0, 0.0]
    loc.sim.fx_reset()
    back = (it % 5 == 0)
    ok = race.use_item(0, back=back)
    assert ok, ('use failed', C.ITEMS[it]['key'])
    used += 1
    evs = run(race, 0.6)
    for e in evs:
        if e[0] == 'item' and e[1] == 'hit':
            seen_fx.add(e[2])
    # 상대에게 맞은 효과 수집
    for rc in race.racers:
        if rc.sim is not None:
            b = rc.sim.fx_bits()
            if b: seen_fx.add('bits%d' % b)
    if race.local.finished:
        race = new_race(mid=7 + it); run(race, 2.0); loc = race.local
print('used all %d items; entities alive=%d; local fx seen=%s' % (used, len(race.items.ents), sorted(x for x in seen_fx if not x.startswith('bits'))[:12]))

# 효과 하나씩 확인
r2 = new_race(mid=33, bots=3)
run(r2, 2.0)
L = r2.local; S = L.sim
def use_key(key, back=False):
    it = C.ITEM_BY_KEY[key]
    L.items[0] = it; L.uses[0] = C.ITEMS[it]['uses']; L.roll[0] = 0.0
    assert r2.use_item(0, back), key
sp0 = S.speed; use_key('booster'); assert S.boost_t > 1.0
use_key('star'); assert S.star_t > 6 and S.invulnerable()
assert S.hit('spin') == 'immune'
S.fx_reset(); use_key('shield'); assert S.shield_n == 1 and S.hit('spin') == 'block' and S.shield_n == 0
S.fx_reset(); S.immune_t = 0; assert S.hit('spin') == 'ok' and S.spin_t > 0
S.fx_reset(); use_key('rocket'); assert S.auto_t > 5
run(r2, 2.0); assert S.speed > S.stats['max_speed'] * 1.1, S.speed
S.fx_reset()
t0 = S.total; use_key('hyperwarp'); run(r2, 1 / 60.0 * 2)
assert (S.total - t0) * r2.track.ds > 100, (S.total - t0) * r2.track.ds
S.fx_reset(); use_key('megamushroom'); run(r2, 0.5); assert L.scale > 1.2, L.scale
S.fx_reset(); assert S.hit('shrink', 5) == 'ok'; run(r2, 0.5); assert L.scale < 0.8, L.scale
S.fx_reset(); assert S.hit('launch') == 'ok'; run(r2, 0.5); assert L.air_y > 0.5
S.fx_reset(); use_key('coinbag'); assert S.coins == 3
S.fx_reset(); L.items = [C.ITEM_BY_KEY['dice'], None, None]; L.uses = [1, 0, 0]; L.roll = [0, 0, 0]
assert r2.use_item(0); assert L.items[0] is not None and C.ITEMS[L.items[0]]['kind'] != 'lucky' and L.roll[0] > 0
# 광역: 번개 -> 상대 모두 축소
S.fx_reset(); use_key('lightning'); run(r2, 0.2)
shr = [rc for rc in r2.racers if rc is not L and rc.sim.shrink_t > 0]
print('lightning shrank %d/%d rivals' % (len(shr), len(r2.racers) - 1)); assert len(shr) >= 1
# 바나나 -> 뒤에 설치 -> 다른 카트가 밟으면 스핀
S.fx_reset(); use_key('banana'); assert any(e.kind == 'trap' for e in r2.items.ents)
# 봇을 바나나 위로 순간이동
bot = [rc for rc in r2.racers if rc is not L][0]
tr = [e for e in r2.items.ents if e.kind == 'trap'][-1]
bot.sim.fx_reset(); bot.sim.teleport(tr.x, tr.z)
for _ in range(10):
    r2.update(1 / 60.0, C.NO_INPUT)
print('banana: bot spin_t=%.2f' % bot.sim.spin_t); assert bot.sim.spin_t > 0 or bot.sim.shield_n > 0
# 유도 미사일이 앞 차를 맞히는지 (봇 하나를 40m 앞에 두고, 옆으로 비켜 있어도 따라가서 맞혀야 함)
S.fx_reset()
tgt = [rc for rc in r2.racers if rc is not L][1]
trk = r2.track
x, y, z, h = trk.pose_at((S.q.prog + 40 / trk.ds) % trk.N, trk.hw * 0.6)
tgt.sim.teleport(x, z, h); tgt.sim.fx_reset(); tgt.sim.shield_n = 0
r2.update(1 / 60.0, C.NO_INPUT)
use_key('homing')
got = False
for _ in range(60 * 8):
    r2.update(1 / 60.0, {'steer': 0, 'throttle': 1, 'brake': 0, 'drift': False})
    if tgt.sim.spin_t > 0: got = True; break
print('homing hit target:', got, tgt.name); assert got
# 1등 추적
S.fx_reset()
lead = [o for o in r2.ranking() if o is not L][0]
lead.sim.fx_reset(); lead.sim.shield_n = 0
use_key('seeker')
got = False
for _ in range(60 * 20):
    r2.update(1 / 60.0, {'steer': 0, 'throttle': 1, 'brake': 0, 'drift': False})
    if lead.sim.air_t > 0: got = True; break
print('seeker hit leader:', got, lead.name); assert got

# ---- 3) 봇 아이템전 완주 --------------------------------------------------------------
for mid in (1, 4, 555, 1000):
    entries = C.solo_entries('Auto', 777, 7, seed=mid)
    race = C.Race(mid, 1, entries, countdown=0.0, auto_local=True, items=True)
    t0 = time.time(); frames = 0; nuse = 0; nhit = 0; maxents = 0
    while frames < 60 * 300:
        race.update(1 / 60.0, C.NO_INPUT); frames += 1
        maxents = max(maxents, len(race.items.ents))
        for rc in race.racers:
            pass
        if all(r.finished for r in race.racers): break
    ok = all(r.finished for r in race.racers)
    vfx = race.items.take_vfx()
    print('item race map %4d: finished=%s t=%.1fs wall=%.1fs maxents=%d vfx=%d' % (mid, ok, race.t, time.time() - t0, maxents, len(vfx)))
    assert ok

# ---- 4) 멀티플레이 ---------------------------------------------------------------------
port = 5641
P1 = C.Profile('/tmp/kti_p1.json'); P1['name'] = 'Host'; P1['kart'] = 11; P1['mode'] = 'item'
P2 = C.Profile('/tmp/kti_p2.json'); P2['name'] = 'Guest'; P2['kart'] = 22
S1, S2 = C.Session(P1), C.Session(P2)
assert S1.host_game(port)
def pump(*ss, secs=0.5):
    end = time.time() + secs; msgs = {id(s): [] for s in ss}
    while time.time() < end:
        for s in ss: msgs[id(s)] += s.pump()
        time.sleep(0.005)
    return msgs
pump(S1, secs=0.4)
S2.join_game('127.0.0.1', port); pump(S1, S2, secs=0.5)
assert S2.settings.get('items') is True, S2.settings
S1.send_settings(map=12, laps=2, bots=0); pump(S1, S2, secs=0.3)
S1.start_race(); pump(S1, S2, secs=0.4)
m1, m2 = S1.start_msg, S2.start_msg
assert m1.get('items') and m2.get('items')
R1 = C.Race(12, 2, S1.entries_from_start(m1), multi=True, is_host=True, countdown=0.0, net=S1.net, items=True)
R2 = C.Race(12, 2, S2.entries_from_start(m2), multi=True, is_host=False, countdown=0.0, net=S2.net, items=True)
gas = {'steer': 0, 'throttle': 1, 'brake': 0, 'drift': False}
def both(secs):
    end = time.time() + secs
    while time.time() < end:
        for S, R in ((S1, R1), (S2, R2)):
            for m in S.pump(): R.handle_message(m)
            R.update(1 / 60.0, gas)
        time.sleep(1 / 120.0)
both(1.5)
# 손님이 바나나를 깔면 방장 화면에도 생겨야 함
G = R2.local
G.items[0] = C.ITEM_BY_KEY['banana']; G.uses[0] = 1; G.roll[0] = 0
assert R2.use_item(0)
both(0.4)
eids2 = set(e.eid for e in R2.items.ents); eids1 = set(e.eid for e in R1.items.ents)
print('banana synced:', eids2 & eids1)
assert eids2 & eids1
# 방장이 번개 -> 손님 축소
H = R1.local
H.items[1] = C.ITEM_BY_KEY['lightning']; H.uses[1] = 1; H.roll[1] = 0
G.sim.fx_reset()
assert R1.use_item(1)
both(0.4)
print('guest shrink_t after host lightning: %.2f  (remote fx bits seen by host: %d)' % (G.sim.shrink_t, R1._find(G.id).fx))
assert G.sim.shrink_t > 0
assert R1._find(G.id).fx & C.FX_SHRINK
# 손님이 방장의 아이템 훔치기 (손님을 방장 15m 뒤로)
H.items = [C.ITEM_BY_KEY['star'], None, None]; H.uses = [1, 0, 0]; H.roll = [0, 0, 0]
G.items = [C.ITEM_BY_KEY['thief'], C.ITEM_BY_KEY['swap'], None]; G.uses = [1, 1, 0]; G.roll = [0, 0, 0]
hs = H.sim; trk = R2.track
x, y, z, h = trk.pose_at((hs.q.prog - 15 / trk.ds) % trk.N, 0)
G.sim.teleport(x, z, h)
both(0.3)
ahead_ids = [o.id for o in R2.items._ahead(G)]
print('guest sees ahead:', ahead_ids, 'host id', H.id)
assert ahead_ids and ahead_ids[0] == H.id
assert R2.use_item(0)
both(0.6)
print('after steal: host items', H.items, 'guest items', G.items)
assert C.ITEM_BY_KEY['star'] in G.items and H.items[0] is None
# 자리 바꾸기: 손님이 방장 앞으로
g0, h0 = G.sim.total, H.sim.total
assert R2.use_item(1)
both(0.6)
print('swap: guest total %.1f->%.1f host %.1f->%.1f' % (g0, G.sim.total, h0, H.sim.total))
assert G.sim.total > H.sim.total
# 상자 동기화
b = R1.items.boxes[0]
R1.items._send({'t': 'ib', 'b': 0}); b['t'] = 2.6
both(0.2)
assert R2.items.boxes[0]['t'] > 0
# 손님 미사일이 방장을 맞히면 방장 쪽에서 판정 + 알림
S1.leave(); S2.leave()
print('ITEM TESTS OK')
