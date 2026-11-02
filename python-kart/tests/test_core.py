# -*- coding: utf-8 -*-
"""코어 헤드리스 테스트: python3 tests/test_core.py"""
import os, sys, time, subprocess, importlib.util, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = '/tmp/kart3d_core_test.py'
subprocess.check_call([sys.executable, os.path.join(ROOT, 'src', 'build.py'), 'core', out])
spec = importlib.util.spec_from_file_location('kcore', out)
C = importlib.util.module_from_spec(spec); sys.modules['kcore'] = C; spec.loader.exec_module(C)

# 1) 카트 100,000종 인코딩/디코딩
seen = set()
for kid in range(0, C.KART_COUNT, 1):
    k = C.decode_kart(kid)
    assert C.encode_kart(k) == kid
    seen.add((k['body'], k['paint'], k['wheel'], k['wing']))
assert len(seen) == 100000, len(seen)
print('kart combos OK:', len(seen))
st = C.kart_stats(12345); print('stats', {k: round(v, 2) for k, v in st.items()})

# 2) 솔로 레이스 시뮬레이션 (자동 주행): 3개 맵, 완주해야 함
for mid in (1, 4, 777):
    entries = C.solo_entries('Tester', 54321, 5, seed=mid)
    race = C.Race(mid, 1, entries, countdown=0.0, auto_local=True)
    t0 = time.time(); frames = 0
    while frames < 60 * 400:
        race.update(1 / 60.0, {'steer': 0, 'throttle': 0, 'brake': 0, 'drift': False}); frames += 1
        if all(r.finished for r in race.racers): break
    ok = all(r.finished for r in race.racers)
    rk = race.ranking()
    print('map %4d  N=%d len=%dm  race time %.1fs  sim %.2fs wall  finished=%s  winner=%s %.1fs  last=%.1fs' % (
        mid, race.track.N, race.track.length, race.t, time.time() - t0, ok, rk[0].name, rk[0].finish_time, rk[-1].finish_time))
    assert ok

# 3) 멀티플레이: 서버 + 2 클라이언트(세션) + 호스트 봇
port = 5611
P1 = C.Profile('/tmp/kt_p1.json'); P1['name'] = 'Host'; P1['kart'] = 111
P2 = C.Profile('/tmp/kt_p2.json'); P2['name'] = 'Guest'; P2['kart'] = 222
S1, S2 = C.Session(P1), C.Session(P2)
assert S1.host_game(port)
def pump(*ss, secs=1.0):
    end = time.time() + secs; msgs = {id(s): [] for s in ss}
    while time.time() < end:
        for s in ss: msgs[id(s)] += s.pump()
        time.sleep(0.01)
    return msgs
pump(S1, secs=0.5)
S2.join_game('127.0.0.1', port); pump(S1, S2, secs=0.6)
print('lobby:', S1.state, S2.state, [p['name'] for p in S1.players], 'host?', S1.is_host, S2.is_host)
assert S1.state == 'lobby' and S2.state == 'lobby' and S1.is_host and not S2.is_host and len(S1.players) == 2
S1.send_settings(map=321, laps=2, bots=2); pump(S1, S2, secs=0.4)
assert {k: S2.settings[k] for k in ('map', 'laps', 'bots')} == {'map': 321, 'laps': 2, 'bots': 2}, S2.settings
found = []; r = {}
C.discover_async(r)
while r.get('busy'): time.sleep(0.05)
print('LAN discover:', [(x['ip'], x['port'], x['players']) for x in r['rooms']])
S1.start_race(); pump(S1, S2, secs=0.5)
assert S1.start_msg and S2.start_msg
e1 = S1.entries_from_start(S1.start_msg); e2 = S2.entries_from_start(S2.start_msg)
R1 = C.Race(321, 2, e1, multi=True, is_host=S1.is_host, countdown=0.0, net=S1.net, auto_local=True)
R2 = C.Race(321, 2, e2, multi=True, is_host=S2.is_host, countdown=0.0, net=S2.net, auto_local=True)
for f in range(60 * 12):
    for R, S in ((R1, S1), (R2, S2)):
        for m in S.pump(): R.handle_message(m)
        R.update(1 / 60.0, {'steer': 0, 'throttle': 0, 'brake': 0, 'drift': False})
    time.sleep(1 / 120.0)
for R, S in ((R1, S1), (R2, S2)):
    print(S.profile['name'], [(r.name, r.kind, round(r.total, 1), round(r.speed)) for r in R.racers])
# 각자 상대/봇이 앞으로 가고 있어야 한다
for R in (R1, R2):
    for r in R.racers: assert r.total > 5, (R is R1, r.name, r.total)
S2.leave(); pump(S1, secs=0.5); print('after guest left, players:', len(S1.players)); assert len(S1.players) == 1
S1.leave()
# 4) 바이옴 1000종: 맵마다 서로 다른 바이옴 (이름/조합 모두 고유), 생태계 40 x 25
names = set(); names_en = set(); combo = set(); fam = {}
for m in range(1, C.MAP_COUNT + 1):
    b = C.biome(m)
    names.add(b['name']); names_en.add(b['en']); combo.add((b['family'], b['time'], b['mod']))
    fam[b['family']] = fam.get(b['family'], 0) + 1
    assert C.biome_map(*C.biome_parts(m)) == m
    assert C.map_info(m)['theme_name'] == b['name']
assert len(names) == len(names_en) == len(combo) == 1000, (len(names), len(names_en), len(combo))
assert len(fam) == C.BIOME_FAMILIES == 40 and set(fam.values()) == {25}, fam
assert C.biome(77) is C.biome(77) and C.biome(77)['name'] == C.biome(77)['name']
for m in (1, 40, 163, 500, 999):
    assert C.horizon_layers(C.biome(m), C.map_info(m)['seed'])
print('biomes OK: 1000 unique (40 families x 5 times x 5 moods), e.g.', C.biome(1)['name'], '/', C.biome(999)['name'])
print('ALL CORE TESTS PASSED')
