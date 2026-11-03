# -*- coding: utf-8 -*-
"""맵 만들기(커스텀 맵) 코어 테스트: python3 tests/test_cmap.py
   데이터 정리 / 그린 선 -> 코스 / 같은 데이터 = 같은 트랙 / 장애물 충돌 / 발판 / 저장 / 방 서버로 전송"""
import os, sys, time, json, math, tempfile, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(tempfile.gettempdir(), 'kart3d_core_cmap_test.py')
os.system('%s "%s" core "%s" >/dev/null' % (sys.executable, os.path.join(ROOT, 'src', 'build.py'), OUT))
spec = importlib.util.spec_from_file_location('kcore', OUT)
K = importlib.util.module_from_spec(spec); sys.modules['kcore'] = K; spec.loader.exec_module(K)

# 1) 이상한 데이터 정리
bad = {'name': 'x' * 80 + '\x00', 'pts': [[1e9, -1e9, 999], [float('nan'), 0], [0, 0, 0], 'junk', [10, 20], [30, 40, 5]] * 3,
       'objs': [['cone', 5, 5], ['nope', 1, 1], ['rock', 1, 2, 99, 99], [1, 2]], 'width': 999, 'look': -5, 'deco': 9, 'weather': 'lava'}
c = K.cmap_clean(bad)
assert c is not None and len(c['name']) <= 20 and c['width'] == 30.0 and c['look'] == 1 and c['deco'] == 3 and c['weather'] == 'auto'
assert all(abs(p[0]) <= K.CMAP_WORLD and abs(p[1]) <= K.CMAP_WORLD and -40 <= p[2] <= 80 for p in c['pts'])
assert [o[0] for o in c['objs']] == ['cone', 'rock'] and c['objs'][1][3] == 3.0
assert K.cmap_clean({'pts': [[0, 0]]}) is None and K.cmap_clean('nope') is None
print('clean OK')

# 2) 손으로 그린 선 -> 코스 (너무 작으면 거절)
assert K.stroke_to_pts([(0, 0), (10, 0), (10, 10)]) is None
stroke = [(math.cos(a / 60.0 * K.TAU) * 260, math.sin(a / 60.0 * K.TAU) * 170) for a in range(61)]
pts = K.stroke_to_pts(stroke)
assert pts and len(pts) >= 20
ed = K.MapEdit(K.cmap_new('테스트', 77))
assert ed.set_stroke(stroke) and ed.preview() is not None and ed.preview().length > 900
tr = ed.preview()
assert abs(tr.ds - 4.0) < 0.3, tr.ds
print('stroke OK: %d points, %.0f m, ds %.2f' % (len(ed.data['pts']), tr.length, tr.ds))

# 3) 물건 놓기 + 줄로 놓기 + 지우기 + 되돌리기
i = tr.N // 4
x, y, z, h = tr.pose_at(i, 0.0)
assert ed.add_obj('lavapillar', x, z)
row = [tr.pose_at(tr.N // 2 + k, 0.0) for k in range(8)]
n = ed.add_line('cone', [(p[0], p[2]) for p in row])
assert n >= 10, n
for kind, f in (('pad', 0.6), ('jump', 0.7), ('oil', 0.8), ('box', 0.9)):
    x2, y2, z2, h2 = tr.pose_at(int(tr.N * f), 0.0)
    assert ed.add_obj(kind, x2, z2)
x3, y3, z3, h3 = tr.pose_at(int(tr.N * 0.1), 60.0)
assert ed.add_obj('volcano', x3, z3)
cnt = len(ed.data['objs'])
assert ed.erase_at(x, z, 3.0) == 1 and len(ed.data['objs']) == cnt - 1
assert ed.undo() and len(ed.data['objs']) == cnt
ed.raise_point(3, 8.0)
ed.set_start(5)
ed.reverse()
d = ed.result()
print('edit OK: %d objects' % len(d['objs']))

# 4) 같은 데이터(전송 후) -> 같은 트랙, 장애물/발판/상자
t1 = K.Track(d)
t2 = K.Track(json.loads(json.dumps(d)))
sig = lambda t: (t.N, round(sum(t.px), 6), round(sum(t.pz), 6), round(sum(t.py), 6), [sorted(p.items()) for p in t.props], t.pads, t.obstacles, t.box_rows)
assert sig(t1) == sig(t2)
kinds = sorted(set(p.get('kind', 'boost') for p in t1.pads))
assert 'jump' in kinds and 'oil' in kinds, kinds
assert len(t1.obstacles) >= 10 and t1.box_rows, (len(t1.obstacles), t1.box_rows)
assert t1.custom is not None and t1.info['name'] == '테스트' and K.map_title(d).endswith('테스트')
print('track OK: N=%d obstacles=%d pads=%s boxes=%s' % (t1.N, len(t1.obstacles), kinds, t1.box_rows))

# 5) 장애물에 부딪히면 튕겨 나온다 (통과하지 않음)
ox, oz, orad = t1.obstacles[0][0], t1.obstacles[0][1], t1.obstacles[0][2]
sim = K.KartSim(t1, 1, 0)
q = K.Q()
t1.query(ox, oz, -1, q)
back = 14.0
sim.x, sim.z = ox - q.tx * back, oz - q.tz * back
sim.heading = math.atan2(q.tx, q.tz)
t1.query(sim.x, sim.z, -1, sim.q)
sim.hint = sim.q.idx
sim.vx, sim.vz = q.tx * 30.0, q.tz * 30.0
closest = 1e9
for f in range(90):
    sim.update(1 / 60., {'steer': 0.0, 'throttle': 1.0, 'brake': 0.0, 'drift': False}, [])
    closest = min(closest, math.hypot(sim.x - ox, sim.z - oz))
assert closest >= orad + 1.0, (closest, orad)
print('collision OK: closest %.2f m (obstacle radius %.2f)' % (closest, orad))

# 6) 레이스: 봇 8대가 장애물 맵을 완주
race = K.Race(d, 2, K.solo_entries('Me', 1, 7, seed=4), countdown=0.0, items=True, auto_local=True)
race.start_at = time.monotonic() - 1
for f in range(60 * 150):
    race.update(1 / 60., K.NO_INPUT)
    if all(r.finished for r in race.racers):
        break
fin = sum(1 for r in race.racers if r.finished)
assert fin == len(race.racers), [round(r.total / race.track.N, 2) for r in race.racers]
print('race OK: all %d finished in %.1f s' % (fin, race.t))

# 7) 저장소 (파일)
tmpd = tempfile.mkdtemp()
st = K.MapStore(os.path.join(tmpd, 'maps.json'))
st._candidates = lambda: [os.path.join(tmpd, 'maps.json')]
uid = st.put(d)
assert uid and st.get(uid)['name'] == '테스트'
st2 = K.MapStore(os.path.join(tmpd, 'maps.json'))
st2._candidates = lambda: [os.path.join(tmpd, 'maps.json')]
st2.load()
assert len(st2.maps) == 1 and K.cmap_key(st2.maps[0]) == K.cmap_key(K.cmap_clean(d))
assert st2.add_copy(d) == st2.maps[0]['uid']           # 같은 내용은 중복 저장 안 함
st2.delete(uid)
assert not st2.maps
print('store OK')

# 8) 방 서버로 전송: 방장이 고른 맵을 손님이 그대로 받는다
port = 5791
srv = K.RoomServer(port).start()
prof_h = K.Profile('kart3d_cmap_test_h.json'); prof_g = K.Profile('kart3d_cmap_test_g.json')
host = K.Session(prof_h); guest = K.Session(prof_g)
host._connect('127.0.0.1', port); time.sleep(0.3)
for _ in range(50):
    host.pump(); time.sleep(0.02)
guest._connect('127.0.0.1', port)
for _ in range(80):
    host.pump(); guest.pump(); time.sleep(0.02)
assert host.is_host and guest.state == 'lobby'
host.send_settings(cmap=d)
for _ in range(60):
    host.pump(); guest.pump(); time.sleep(0.02)
gm = guest.settings.get('cmap')
assert gm is not None and K.cmap_key(gm) == K.cmap_key(K.cmap_clean(d)) and gm['name'] == '테스트'
host.start_race()
for _ in range(60):
    host.pump(); guest.pump(); time.sleep(0.02)
assert guest.start_msg is not None and guest.start_msg.get('cmap')
tg = K.Track(guest.start_msg['cmap'])
assert sig(tg) == sig(t1)
host.back_to_lobby()
for _ in range(40):
    host.pump(); guest.pump(); time.sleep(0.02)
host.send_settings(map=7)             # 로비에서 기본 맵을 고르면 만든 맵은 해제
for _ in range(40):
    host.pump(); guest.pump(); time.sleep(0.02)
assert guest.settings.get('cmap') is None and guest.settings['map'] == 7
host.leave(); guest.leave(); srv.stop()
print('network OK: guest built the identical track (%d bytes of map data)' % len(json.dumps(d, separators=(',', ':'))))
print('CMAP TESTS PASSED')
