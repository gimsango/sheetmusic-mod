# -*- coding: utf-8 -*-
"""PC(Panda3D) 바이옴 확인: 맵마다 레이스 화면 스크린샷 -> 모음 이미지. python tests/pc_biome_shots.py <outdir> [첫 맵] [개수] [간격]"""
import os, sys, time, importlib.util, traceback, math
os.environ['KART3D_OFFSCREEN'] = '1'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
first = int(sys.argv[2]) if (len(sys.argv) > 2 and ',' not in sys.argv[2]) else 1
count = int(sys.argv[3]) if len(sys.argv) > 3 else 40
step = int(sys.argv[4]) if len(sys.argv) > 4 else 1
os.makedirs('/tmp/kt_pbs', exist_ok=True); sys.argv[0] = '/tmp/kt_pbs/pc.py'
if os.path.exists('/tmp/kt_pbs/kart3d_profile.json'): os.remove('/tmp/kt_pbs/kart3d_profile.json')
spec = importlib.util.spec_from_file_location('kpc', os.path.join(ROOT, 'kart3d_pc.py'))
K = importlib.util.module_from_spec(spec); sys.modules['kpc'] = K; spec.loader.exec_module(K)
g = K.Game({'window': (512, 288), 'lang': 'ko'})
g.profile['mode'] = 'speed'; g.profile['bots'] = 3; g.profile['laps'] = 1
def frames(n, dt=1 / 60.0):
    g.dt_override = dt
    for _ in range(n): g.taskMgr.step()
files = []
t0 = time.time()
maps = [int(v) for v in sys.argv[2].split(',')] if (len(sys.argv) > 2 and ',' in sys.argv[2]) else [first + i * step for i in range(count)]
try:
    frames(3)
    for mid in maps:
        g.profile['map'] = mid
        g.start_solo()
        race = g.race
        race.start_at = time.monotonic() - 1
        tr = race.track
        pf = (tr.N * 0.18 + mid * 7) % tr.N
        x, y, z, h = tr.pose_at(pf, 0.0)
        race.local.sim.teleport(x, z, h)
        g.chase = K.ChaseCam()
        frames(4)
        f = os.path.join(out, 'pcb_%04d.png' % mid)
        g.graphicsEngine.renderFrame()
        g.win.saveScreenshot(K.Filename(f))
        files.append((mid, f, tr.theme['name']))
        g.leave_race(); frames(1)
    print('rendered %d in %.1fs' % (len(files), time.time() - t0))
except Exception:
    traceback.print_exc()
# 모음 이미지 (pygame 으로 합치기)
try:
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    import pygame
    pygame.init(); pygame.display.set_mode((10, 10))
    font = pygame.font.Font(K.find_korean_font(), 13)
    cols = 5; tw, th_ = 320, 180
    rows = (len(files) + cols - 1) // cols
    sheet = pygame.Surface((cols * tw, rows * (th_ + 18))); sheet.fill((10, 12, 20))
    for k, (mid, f, nm) in enumerate(files):
        img = pygame.transform.smoothscale(pygame.image.load(f), (tw, th_))
        cx, cy = (k % cols) * tw, (k // cols) * (th_ + 18)
        sheet.blit(img, (cx, cy))
        sheet.blit(font.render('#%d %s' % (mid, nm), True, (255, 255, 255)), (cx + 4, cy + th_ + 1))
        os.remove(f)
    name = os.path.join(out, 'pc_biomes_%d_%d.png' % (maps[0], maps[-1]))
    pygame.image.save(sheet, name); print('saved', name)
except Exception:
    traceback.print_exc()
