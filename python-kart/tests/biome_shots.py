# -*- coding: utf-8 -*-
"""바이옴 확인용 모음 이미지 (폰 렌더러): python3 tests/biome_shots.py <outdir> [첫 맵 번호] [개수] [간격]
   기본: 맵 1~40 (생태계 40가지 전부)"""
import os, sys, time, importlib.util, math
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
first = int(sys.argv[2]) if (len(sys.argv) > 2 and ',' not in sys.argv[2]) else 1
count = int(sys.argv[3]) if len(sys.argv) > 3 else 40
step = int(sys.argv[4]) if len(sys.argv) > 4 else 1
os.makedirs('/tmp/kt_bs', exist_ok=True); sys.argv[0] = '/tmp/kt_bs/app.py'
spec = importlib.util.spec_from_file_location('kp', os.path.join(ROOT, 'kart3d_phone.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kp'] = K; spec.loader.exec_module(K)
pg = K.pygame
pg.init(); screen = pg.display.set_mode((640, 360))
font = pg.font.Font(K.find_korean_font(), 13)
rd = K.Renderer(640, 360, 2)
cols = 5
tw, th_ = 320, 180
maps = [int(v) for v in sys.argv[2].split(',')] if (len(sys.argv) > 2 and ',' in sys.argv[2]) else [first + i * step for i in range(count)]
rows = (len(maps) + cols - 1) // cols
sheet = pg.Surface((cols * tw, rows * (th_ + 18)))
sheet.fill((10, 12, 20))
t0 = time.time()
for k, mid in enumerate(maps):
    entries = K.solo_entries('Me', 12345 + mid, 3, seed=mid)
    race = K.Race(mid, 1, entries, countdown=0.0)
    tr = race.track
    rd.set_track(tr)
    loc = race.local
    pf = (tr.N * 0.18 + mid * 7) % tr.N
    x, y, z, h = tr.pose_at(pf, 0.0)
    loc.sim.teleport(x, z, h)
    race.update(1 / 60.0, K.NO_INPUT)
    for rc in race.racers:
        rc.sync_visual(tr, 0.0)
    cam = K.ChaseCam()
    cp = cam.update(0.0, loc, 60.0)
    i0 = loc.idx
    dot = math.sin(cp[3]) * tr.tx[i0] + math.cos(cp[3]) * tr.tz[i0]
    for _ in range(3):
        rd.update_particles(1 / 30.0)
    surf = rd.render(race, cp, i0, 1 if dot >= 0 else -1, 0.0, 0.3, 1.0)
    thumb = pg.transform.smoothscale(surf, (tw, th_))
    cx, cy = (k % cols) * tw, (k // cols) * (th_ + 18)
    sheet.blit(thumb, (cx, cy))
    b = tr.theme
    sheet.blit(font.render('#%d %s' % (mid, b['name']), True, (255, 255, 255)), (cx + 4, cy + th_ + 1))
name = os.path.join(out, 'biomes_%d_%d.png' % (maps[0], maps[-1]))
pg.image.save(sheet, name)
print('saved', name, 'in %.1fs' % (time.time() - t0))
