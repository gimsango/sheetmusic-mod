
# ============================================================================
#  [PC] 설정 화면: 그래픽(품질 프리셋) / 화면 / 소리 / 조작·카메라 / 게임  - 마우스·키보드 모두 사용
# ============================================================================
GFX_PRESETS = {
    'low': dict(msaa=0, aniso=1, view=0, props_k=0.35, fx_k=0.5, weather_k=0.4, shadows=False),
    'medium': dict(msaa=2, aniso=4, view=1, props_k=0.65, fx_k=0.75, weather_k=0.7, shadows=True),
    'high': dict(msaa=4, aniso=8, view=2, props_k=1.0, fx_k=1.0, weather_k=1.0, shadows=True),
    'ultra': dict(msaa=8, aniso=16, view=3, props_k=1.0, fx_k=1.0, weather_k=1.0, shadows=True),
}
GFX_ORDER = ['low', 'medium', 'high', 'ultra', 'custom']
GFX_NAME = {'low': ('낮음', 'Low'), 'medium': ('중간', 'Medium'), 'high': ('높음', 'High'), 'ultra': ('최고', 'Ultra'), 'custom': ('사용자 지정', 'Custom')}
VIEW_LEVELS = [(380.0, 1.0), (650.0, 1.0), (0.0, 1.0), (0.0, 0.8)]       # (이보다 먼 장식물 숨김 m, 안개 배율)
VIEW_NAME = [('가까이', 'Near'), ('보통', 'Normal'), ('멀리', 'Far'), ('아주 멀리', 'Very far')]
PROPS_STEPS = [0.35, 0.5, 0.65, 0.8, 1.0]
FX_STEPS = [0.5, 0.75, 1.0]
WEATHER_STEPS = [0.0, 0.4, 0.7, 1.0]
MSAA_STEPS = [0, 2, 4, 8]
ANISO_STEPS = [1, 2, 4, 8, 16]
FPS_CAPS = [0, 30, 60, 120, 144, 165, 240]
RES_COMMON = [(1280, 720), (1366, 768), (1600, 900), (1920, 1080), (2560, 1080), (2560, 1440), (3440, 1440), (3840, 2160)]


def parse_res(v):
    try:
        w, h = str(v).lower().split('x')
        w, h = int(w), int(h)
        if 320 <= w <= 16384 and 240 <= h <= 16384:
            return (w, h)
    except Exception:
        pass
    return None


def gfx_sync(profile):
    """프로필의 그래픽 값 -> GFX (월드/카트/효과를 만들 때 읽음)"""
    v = int(clamp(int(profile['view']), 0, 3))
    cull, fogk = VIEW_LEVELS[v]
    GFX.update(aniso=int(profile['aniso']), props_k=float(profile['props_k']), fx_k=float(profile['fx_k']),
               weather_k=float(profile['weather_k']), shadows=bool(profile['shadows']), cull_m=cull, fog_k=fogk)


def startup_cfg(profile, args):
    """창을 만들기 전에 넣는 Panda3D 설정 (해상도/화면 모드/수직 동기화/안티에일리어싱)"""
    res = args.get('window') or parse_res(profile['res']) or (1280, 720)
    disp = 'fullscreen' if args.get('fullscreen') else str(profile['display'])
    if args.get('window'):
        disp = 'window'
    lines = ['win-size %d %d' % (res[0], res[1]), 'sync-video %d' % (1 if profile['vsync'] else 0)]
    if disp == 'fullscreen':
        lines.append('fullscreen 1')
    elif disp == 'borderless':
        lines += ['undecorated 1', 'win-origin 0 0']
    msaa = int(profile['msaa'])
    if msaa > 0:
        lines += ['framebuffer-multisample 1', 'multisamples %d' % msaa]
    return lines


def _cycle(lst, cur, d):
    try:
        i = lst.index(cur)
    except ValueError:
        i = min(range(len(lst)), key=lambda k: abs(lst[k] - cur)) if isinstance(cur, (int, float)) else 0
    return lst[(i + d) % len(lst)]


class SettingsMixin(object):
    """Game 에 섞어 쓰는 설정 화면/적용 함수들"""

    # ---- 적용 ----------------------------------------------------------------------
    def desktop_size(self):
        try:
            w, h = self.pipe.getDisplayWidth(), self.pipe.getDisplayHeight()
            if w > 0 and h > 0:
                return (w, h)
        except Exception:
            pass
        return (1920, 1080)

    def res_list(self):
        dw, dh = self.desktop_size()
        out = set(r for r in RES_COMMON if r[0] <= dw and r[1] <= dh)
        out.add((dw, dh))
        try:
            di = self.pipe.getDisplayInformation()
            for i in range(di.getTotalDisplayModes()):
                w, h = di.getDisplayModeWidth(i), di.getDisplayModeHeight(i)
                if w >= 1024 and h >= 600 and w <= dw and h <= dh:
                    out.add((w, h))
        except Exception:
            pass
        return sorted(out)

    def cur_res(self):
        try:
            return (self.win.getXSize(), self.win.getYSize())
        except Exception:
            return parse_res(self.profile['res']) or (1280, 720)

    def apply_display(self):
        if self.offscreen:
            return
        p = self.profile
        props = WindowProperties()
        disp = p['display']
        if disp == 'borderless':
            w, h = self.desktop_size()
            props.setFullscreen(False)
            props.setUndecorated(True)
            props.setOrigin(0, 0)
            props.setSize(w, h)
        else:
            w, h = parse_res(p['res']) or self.cur_res()
            props.setUndecorated(False)
            props.setFullscreen(disp == 'fullscreen')
            props.setSize(w, h)
        try:
            self.win.requestProperties(props)
        except Exception:
            pass

    def apply_runtime(self):
        """바로 바꿀 수 있는 설정들 (안티에일리어싱 켬/끔, 프레임 제한, 카메라, 볼륨, 그래픽 값)"""
        p = self.profile
        gfx_sync(p)
        try:
            self.render.setAntialias(AntialiasAttrib.MAuto if int(p['msaa']) > 0 else AntialiasAttrib.MNone)
        except Exception:
            pass
        try:
            gc = ClockObject.getGlobalClock()
            cap = int(p['fps_cap'])
            if cap > 0:
                gc.setMode(ClockObject.MLimited)
                gc.setFrameRate(cap)
            else:
                gc.setMode(ClockObject.MNormal)
        except Exception:
            pass
        self.chase.k = CAM_K[int(clamp(int(p['cam_dist']), 0, 2))]
        self.audio.enabled = bool(p['sound'])
        self.audio.set_volumes(float(p['vol_master']), float(p['vol_sfx']), float(p['vol_engine']), float(p['vol_music']), bool(p['music']))
        # 그림자는 지금 보이는 카트에도 바로
        for n in list(getattr(self, 'nodes', {}).values()) + ([self.show_node] if getattr(self, 'show_node', None) is not None else []):
            try:
                n.shadow.show() if p['shadows'] else n.shadow.hide()
            except Exception:
                pass

    def set_preset(self, name):
        p = self.profile
        p['gfx'] = name
        if name in GFX_PRESETS:
            for k, v in GFX_PRESETS[name].items():
                p[k] = v
        p.save()
        self.apply_runtime()

    def set_opt(self, key, value):
        p = self.profile
        p[key] = value
        if key in ('msaa', 'aniso', 'view', 'props_k', 'fx_k', 'weather_k', 'shadows'):
            p['gfx'] = 'custom'
            for name, pre in GFX_PRESETS.items():
                if all(p[k] == v for k, v in pre.items()):
                    p['gfx'] = name
        p.save()
        self.apply_runtime()

    # ---- 화면 구성 -------------------------------------------------------------------
    def settings_back(self):
        """설정 화면에서 '뒤로'"""
        page = getattr(self, 'set_page', 'main')
        if page != 'main':
            self.set_page = 'main'
            self.build_settings()
        elif getattr(self, 'settings_from_pause', False):
            self.settings_from_pause = False
            self.paused = False
            self.toggle_pause()
        else:
            self.profile.save()
            self.go('menu')

    def open_settings(self, page='main', from_pause=False):
        self.set_page = page
        self.settings_from_pause = from_pause
        if not from_pause:
            self.go('settings')
        else:
            self.build_settings()

    def build_settings(self):
        page = getattr(self, 'set_page', 'main')
        fn = {'gfx': self.build_set_gfx, 'display': self.build_set_display, 'audio': self.build_set_audio,
              'controls': self.build_set_controls, 'game': self.build_set_game}.get(page)
        if fn is not None:
            fn()
            return

        def sub(pg):
            def f(m=1):
                self.set_page = pg
                self.build_settings()
            return f
        p = self.profile
        gn = GFX_NAME.get(p['gfx'], GFX_NAME['custom'])
        rows = [self.R('%s   [%s]' % (T('그래픽', 'Graphics'), T(gn[0], gn[1])), sub('gfx'), id='s_gfx', kind='primary'),
                self.R('%s   [%s · %dx%d]' % (T('화면', 'Display'), self.disp_name(), self.cur_res()[0], self.cur_res()[1]), sub('display'), id='s_disp'),
                self.R('%s   [%d%%]' % (T('소리', 'Audio'), int(round(float(p['vol_master']) * 100))), sub('audio'), id='s_audio'),
                self.R(T('조작 · 카메라', 'Controls & camera'), sub('controls'), id='s_ctl'),
                self.R(T('게임 (언어 · 단위)', 'Game (language · units)'), sub('game'), id='s_game'),
                self.R(T('뒤로', 'Back'), lambda: self.settings_back(), id='back')]
        self.menu.set(T('설정', 'Settings'), rows, T('마우스 클릭 · 휠, 또는 ↑↓ ←→ Enter', 'Mouse click / wheel, or arrows + Enter'),
                      T('Esc 뒤로', 'Esc back'))
        self.menu.clear_extra()

    def disp_name(self):
        d = self.profile['display']
        return {'window': T('창 모드', 'Windowed'), 'fullscreen': T('전체 화면', 'Fullscreen'), 'borderless': T('테두리 없는 창', 'Borderless')}.get(d, d)

    def _onoff(self, v):
        return T('켬', 'On') if v else T('끔', 'Off')

    def build_set_gfx(self):
        p = self.profile

        def preset(d):
            def f(m=1):
                order = GFX_ORDER[:-1]
                cur = p['gfx'] if p['gfx'] in order else 'high'
                self.set_preset(order[(order.index(cur) + d) % len(order)])
                self.build_settings()
            return f

        def opt(key, steps, d_default=1):
            def mk(d):
                def f(m=1):
                    self.set_opt(key, _cycle(steps, p[key], d))
                    self.build_settings()
                return f
            return mk

        def tog(key):
            def f(m=1):
                self.set_opt(key, not p[key])
                self.build_settings()
            return f
        gn = GFX_NAME.get(p['gfx'], GFX_NAME['custom'])
        msaa_note = ''
        if int(p['msaa']) != getattr(self, 'start_msaa', int(p['msaa'])):
            msaa_note = T('  (다시 시작 후 적용)', '  (after restart)')
        o_msaa, o_an, o_pr, o_fx, o_we = opt('msaa', MSAA_STEPS), opt('aniso', ANISO_STEPS), opt('props_k', PROPS_STEPS), opt('fx_k', FX_STEPS), opt('weather_k', WEATHER_STEPS)
        vn = VIEW_NAME[int(clamp(int(p['view']), 0, 3))]

        def view(d):
            def f(m=1):
                self.set_opt('view', (int(p['view']) + d) % 4)
                self.build_settings()
            return f
        rows = [self.R('%s  < %s >' % (T('품질 프리셋', 'Quality preset'), T(gn[0], gn[1])), preset(1), preset(-1), preset(1), id='g_preset', kind='primary'),
                self.R('%s  < %s >%s' % (T('안티에일리어싱', 'Anti-aliasing'), T('끄기', 'Off') if int(p['msaa']) == 0 else 'MSAA %dx' % int(p['msaa']), msaa_note),
                       o_msaa(1), o_msaa(-1), o_msaa(1), id='g_msaa'),
                self.R('%s  < %s >' % (T('텍스처 필터', 'Texture filtering'), '%dx' % int(p['aniso'])), o_an(1), o_an(-1), o_an(1), id='g_an'),
                self.R('%s  < %s >' % (T('시야 거리', 'View distance'), T(vn[0], vn[1])), view(1), view(-1), view(1), id='g_view'),
                self.R('%s  < %d%% >' % (T('장식물 밀도', 'Scenery density'), int(round(float(p['props_k']) * 100))), o_pr(1), o_pr(-1), o_pr(1), id='g_props'),
                self.R('%s  < %d%% >' % (T('효과 (파티클)', 'Effects (particles)'), int(round(float(p['fx_k']) * 100))), o_fx(1), o_fx(-1), o_fx(1), id='g_fx'),
                self.R('%s  < %s >' % (T('날씨 입자', 'Weather particles'), T('끄기', 'Off') if float(p['weather_k']) <= 0 else '%d%%' % int(round(float(p['weather_k']) * 100))),
                       o_we(1), o_we(-1), o_we(1), id='g_weather'),
                self.R('%s  < %s >' % (T('카트 그림자', 'Kart shadows'), self._onoff(p['shadows'])), tog('shadows'), tog('shadows'), tog('shadows'), id='g_shadow'),
                self.I(T('시야 거리·장식물·효과·날씨는 다음 레이스부터 적용돼요', 'View distance, scenery, effects and weather apply from the next race'), scale=0.042),
                self.R(T('뒤로', 'Back'), lambda: self.settings_back(), id='back')]
        self.menu.set(T('그래픽', 'Graphics'), rows, T('낮음 → 최고: 안티에일리어싱 · 텍스처 · 시야 거리 · 장식물 · 효과', 'Low → Ultra: AA · textures · view distance · scenery · effects'),
                      T('클릭/→ 다음 값 · 오른쪽 클릭/← 이전 값 · 휠', 'Click/→ next · right-click/← previous · wheel'))

    def build_set_display(self):
        p = self.profile

        def disp(d):
            def f(m=1):
                order = ['window', 'fullscreen', 'borderless']
                cur = p['display'] if p['display'] in order else 'window'
                p['display'] = order[(order.index(cur) + d) % 3]
                p.save()
                self.apply_display()
                self.build_settings()
            return f
        lst = self.res_list()

        def res(d):
            def f(m=1):
                cur = parse_res(p['res']) or self.cur_res()
                try:
                    i = lst.index(tuple(cur))
                except ValueError:
                    i = min(range(len(lst)), key=lambda k: abs(lst[k][0] - cur[0]) + abs(lst[k][1] - cur[1]))
                    i -= 1 if d > 0 else 0
                w, h = lst[(i + d) % len(lst)]
                p['res'] = '%dx%d' % (w, h)
                if p['display'] == 'borderless':
                    p['display'] = 'window'
                p.save()
                self.apply_display()
                self.build_settings()
            return f

        def vs(m=1):
            p['vsync'] = not p['vsync']
            p.save()
            self.build_settings()

        def cap(d):
            def f(m=1):
                p['fps_cap'] = _cycle(FPS_CAPS, int(p['fps_cap']), d)
                p.save()
                self.apply_runtime()
                self.build_settings()
            return f

        def fov(d):
            def f(m=1):
                p['fov'] = int(clamp(int(p['fov']) + d * (5 if m >= 10 else 1), 65, 110))
                p.save()
                self.build_settings()
            return f

        def fps(m=1):
            self.show_fps = not self.show_fps
            self.build_settings()
        rr = parse_res(p['res']) or self.cur_res()
        vs_note = T('  (다시 시작 후 적용)', '  (after restart)') if bool(p['vsync']) != getattr(self, 'start_vsync', bool(p['vsync'])) else ''
        rows = [self.R('%s  < %s >' % (T('화면 모드', 'Display mode'), self.disp_name()), disp(1), disp(-1), disp(1), id='d_mode'),
                self.R('%s  < %dx%d >' % (T('해상도', 'Resolution'), rr[0], rr[1]), res(1), res(-1), res(1), id='d_res', enabled=p['display'] != 'borderless'),
                self.R('%s  < %s >%s' % (T('수직 동기화 (VSync)', 'VSync'), self._onoff(p['vsync']), vs_note), vs, vs, vs, id='d_vsync'),
                self.R('%s  < %s >' % (T('프레임 제한', 'Frame rate limit'), T('무제한', 'Unlimited') if int(p['fps_cap']) == 0 else '%d fps' % int(p['fps_cap'])),
                       cap(1), cap(-1), cap(1), id='d_cap'),
                self.R('%s  < %d° >' % (T('시야각 (FOV)', 'Field of view'), int(p['fov'])), fov(1), fov(-1), fov(1), id='d_fov'),
                self.R('FPS %s  < %s >' % (T('표시', 'counter'), self._onoff(self.show_fps)), fps, fps, fps, id='d_fps'),
                self.R(T('뒤로', 'Back'), lambda: self.settings_back(), id='back')]
        dw, dh = self.desktop_size()
        self.menu.set(T('화면', 'Display'), rows, T('모니터 %dx%d · F11 = 전체 화면 전환', 'Monitor %dx%d · F11 toggles fullscreen') % (dw, dh) if LANG == 'ko'
                      else 'Monitor %dx%d · F11 toggles fullscreen' % (dw, dh), T('클릭/→ 다음 값 · 오른쪽 클릭/← 이전 값 · 휠', 'Click/→ next · right-click/← previous · wheel'))

    def build_set_audio(self):
        p = self.profile

        def vol(key):
            def mk(d):
                def f(m=1):
                    p[key] = round(clamp(float(p[key]) + d * 0.1, 0.0, 1.0), 2)
                    p.save()
                    self.apply_runtime()
                    self.build_settings()
                    self.sfx_play('click', 0.6)
                return f
            return mk

        def tog(key):
            def f(m=1):
                p[key] = not p[key]
                p.save()
                self.apply_runtime()
                self.build_settings()
            return f

        def bar(v):
            n = int(round(float(v) * 10))
            return '%3d%%  %s' % (int(round(float(v) * 100)), '|' * n + '.' * (10 - n))
        rows = []
        for key, ko, en in (('vol_master', '전체 볼륨', 'Master'), ('vol_sfx', '효과음', 'Effects'), ('vol_engine', '엔진 소리', 'Engine'), ('vol_music', '배경음악', 'Music')):
            v = vol(key)
            rows.append(self.R('%s  < %s >' % (T(ko, en), bar(p[key])), v(1), v(-1), v(1), id='a_' + key))
        rows += [self.R('%s  < %s >' % (T('소리', 'Sound'), self._onoff(p['sound'])), tog('sound'), tog('sound'), tog('sound'), id='a_sound'),
                 self.R('%s  < %s >' % (T('배경음악', 'Music'), self._onoff(p['music'])), tog('music'), tog('music'), tog('music'), id='a_music'),
                 self.R(T('뒤로', 'Back'), lambda: self.settings_back(), id='back')]
        self.menu.set(T('소리', 'Audio'), rows, T('M 키 = 레이스 중 소리 켜기/끄기', 'M = mute during a race'),
                      T('클릭/→ 크게 · 오른쪽 클릭/← 작게 · 휠', 'Click/→ louder · right-click/← quieter · wheel'))

    def build_set_controls(self):
        p = self.profile

        def steer(d):
            def f(m=1):
                p['steer_resp'] = (int(p['steer_resp']) + d) % 3
                p.save()
                self.build_settings()
            return f

        def cam(d):
            def f(m=1):
                p['cam_dist'] = (int(p['cam_dist']) + d) % 3
                p.save()
                self.apply_runtime()
                self.build_settings()
            return f

        def tog(key):
            def f(m=1):
                p[key] = not p[key]
                p.save()
                self.build_settings()
            return f
        sn = [T('부드럽게', 'Smooth'), T('보통', 'Normal'), T('빠르게', 'Quick')]
        cn = [T('가까이', 'Near'), T('보통', 'Normal'), T('멀리', 'Far')]
        rows = [self.R('%s  < %s >' % (T('조향 반응', 'Steering response'), sn[int(p['steer_resp']) % 3]), steer(1), steer(-1), steer(1), id='c_steer'),
                self.R('%s  < %s >' % (T('카메라 거리', 'Camera distance'), cn[int(p['cam_dist']) % 3]), cam(1), cam(-1), cam(1), id='c_cam'),
                self.R('%s  < %s >' % (T('화면 흔들림', 'Camera shake'), self._onoff(p['shake'])), tog('shake'), tog('shake'), tog('shake'), id='c_shake'),
                self.R('%s  < %s >' % (T('속도감 (속도에 따라 시야각 변화)', 'Speed effect (FOV with speed)'), self._onoff(p['speed_fx'])), tog('speed_fx'), tog('speed_fx'), tog('speed_fx'), id='c_sfx'),
                self.I(T('키보드: ↑ 가속 · ↓ 브레이크/후진 · ←→ 조향 · Space/Shift 드리프트 · 1·2·3 아이템 (↓ 누른 채 = 뒤로) · R 복귀 · Esc 일시정지',
                         'Keys: Up gas · Down brake · Left/Right steer · Space/Shift drift · 1·2·3 items (hold Down = back) · R reset · Esc pause'), scale=0.04),
                self.I(T('게임패드: 왼쪽 스틱 조향 · RT 가속 · LT 브레이크 · A/RB 드리프트 · X·Y·B 아이템',
                         'Gamepad: left stick steer · RT gas · LT brake · A/RB drift · X·Y·B items'), scale=0.04),
                self.R(T('뒤로', 'Back'), lambda: self.settings_back(), id='back')]
        self.menu.set(T('조작 · 카메라', 'Controls & camera'), rows, '', T('클릭/→ 다음 값 · 오른쪽 클릭/← 이전 값', 'Click/→ next · right-click/← previous'))

    def build_set_game(self):
        p = self.profile

        def lang(m=1):
            order = ['auto', 'ko', 'en']
            p['lang'] = order[(order.index(p['lang']) + 1) % 3] if p['lang'] in order else 'auto'
            global LANG
            LANG = ('ko' if self.font else 'en') if p['lang'] == 'auto' else p['lang']
            p.save()
            self.build_settings()

        def units(m=1):
            p['units'] = 'mph' if p['units'] == 'kmh' else 'kmh'
            p.save()
            self.build_settings()

        def clear_rec():
            if getattr(self, '_rec_armed', False):
                p['records'] = {}
                p.save()
                self._rec_armed = False
            else:
                self._rec_armed = True
            self.build_settings()
        ln = {'auto': T('자동', 'Auto'), 'ko': '한국어', 'en': 'English'}.get(p['lang'], p['lang'])
        nrec = len(p['records']) if isinstance(p['records'], dict) else 0
        rows = [self.R('%s  < %s >' % (T('언어 / Language', 'Language'), ln), lang, lang, lang, id='m_lang'),
                self.R('%s  < %s >' % (T('속도 단위', 'Speed units'), 'km/h' if p['units'] == 'kmh' else 'mph'), units, units, units, id='m_units'),
                self.R((T('정말 지울까요? (한 번 더)', 'Really clear? (again)') if getattr(self, '_rec_armed', False) else T('기록 모두 지우기', 'Clear all records')) + '  (%d)' % nrec,
                       clear_rec, id='m_rec', enabled=nrec > 0),
                self.R(T('뒤로', 'Back'), lambda: self.settings_back(), id='back')]
        self.menu.set(T('게임', 'Game'), rows, '', '')
