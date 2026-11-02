
# ----------------------------------------------------------------------------
#  WiFi(LAN) 멀티플레이: 방 서버 + 클라이언트 + 자동 탐색   (표준 라이브러리만 사용)
#  프로토콜: TCP, 줄 단위 JSON.  폰(Pydroid3) 버전과 PC 버전이 같은 방에서 함께 달릴 수 있다.
# ----------------------------------------------------------------------------
def local_ips():
    ips = []
    for target in (('10.255.255.255', 1), ('8.8.8.8', 80)):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(target)
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith('127.') and ip not in ips:
                ips.append(ip)
        except Exception:
            pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith('127.') and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips


def hard_close(sock):
    """다른 스레드가 recv 중이어도 즉시 연결을 끊는다 (shutdown 후 close)"""
    if sock is None:
        return
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass
    try:
        sock.close()
    except Exception:
        pass


class _Conn(object):
    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
        self.id = None
        self.name = ''
        self.kart = 0
        self.lock = threading.Lock()
        self.alive = True

    def send_raw(self, data):
        if not self.alive:
            return
        try:
            with self.lock:
                self.sock.sendall(data)
        except Exception:
            self.alive = False

    def send_obj(self, obj):
        self.send_raw((json.dumps(obj, separators=(',', ':')) + '\n').encode('utf-8'))


class RoomServer(object):
    """방 하나를 관리하는 서버. 호스트 플레이어의 앱 안에서 돌거나 `--serve` 로 단독 실행."""
    MAX_PLAYERS = 12

    def __init__(self, port=DEFAULT_PORT, name='KART3D'):
        self.port = port
        self.name = name
        self.conns = {}
        self.lock = threading.RLock()
        self.host_id = None
        self.map = 1
        self.laps = 3
        self.bots = 0
        self.items = True             # 아이템전 여부
        self.state = 'lobby'
        self.next_id = 1
        self.running = False
        self.srv = None
        self.udp = None

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.port))
        s.listen(16)
        self.srv = s
        self.running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()
        self._start_discovery()
        return self

    def stop(self):
        self.running = False
        for sock in (self.srv, self.udp):
            try:
                if sock is not None:
                    sock.close()
            except Exception:
                pass
        with self.lock:
            conns = list(self.conns.values())
        for c in conns:
            c.alive = False
            hard_close(c.sock)

    # ---- LAN 탐색 응답 --------------------------------------------------------
    def _start_discovery(self):
        try:
            u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            u.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            u.bind(('', DISC_PORT))
            self.udp = u
            threading.Thread(target=self._disc_loop, daemon=True).start()
        except Exception:
            self.udp = None

    def _disc_loop(self):
        while self.running:
            try:
                data, addr = self.udp.recvfrom(512)
            except Exception:
                break
            if data.startswith(b'KART3D?'):
                with self.lock:
                    info = {'game': 'kart3d', 'name': self.name, 'port': self.port, 'map': self.map,
                            'players': len(self.conns), 'state': self.state}
                try:
                    self.udp.sendto(json.dumps(info).encode('utf-8'), addr)
                except Exception:
                    pass

    # ---- 접속 처리 ------------------------------------------------------------
    def _accept_loop(self):
        while self.running:
            try:
                sock, addr = self.srv.accept()
            except Exception:
                break
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(5.0)
            except Exception:
                pass
            threading.Thread(target=self._client_loop, args=(_Conn(sock, addr),), daemon=True).start()

    def _client_loop(self, c):
        buf = b''
        try:
            while self.running and c.alive:
                try:
                    data = c.sock.recv(8192)
                except socket.timeout:
                    continue
                if not data:
                    break
                buf += data
                while True:
                    k = buf.find(b'\n')
                    if k < 0:
                        break
                    line = buf[:k]
                    buf = buf[k + 1:]
                    if not line.strip():
                        continue
                    try:
                        m = json.loads(line.decode('utf-8'))
                    except Exception:
                        continue
                    if isinstance(m, dict):
                        self._handle(c, m)
        except Exception:
            pass
        finally:
            self._drop(c)

    def _room_msg(self):
        with self.lock:
            return {'t': 'room', 'host': self.host_id, 'map': self.map, 'laps': self.laps, 'bots': self.bots, 'items': self.items, 'state': self.state,
                    'players': [{'id': c.id, 'name': c.name, 'kart': c.kart} for c in self.conns.values()]}

    def _broadcast(self, obj, exclude=None):
        data = (json.dumps(obj, separators=(',', ':')) + '\n').encode('utf-8')
        with self.lock:
            targets = [c for c in self.conns.values() if c.id != exclude]
        for c in targets:
            c.send_raw(data)

    def _drop(self, c):
        hard_close(c.sock)
        c.alive = False
        with self.lock:
            if c.id is None or c.id not in self.conns:
                return
            del self.conns[c.id]
            if self.host_id == c.id:
                self.host_id = next(iter(self.conns), None)
            if not self.conns:
                self.state = 'lobby'
        self._broadcast({'t': 'left', 'id': c.id})
        self._broadcast(self._room_msg())

    def _handle(self, c, m):
        t = m.get('t')
        if t == 'join':
            with self.lock:
                if c.id is not None:
                    return
                if self.state != 'lobby':
                    c.send_obj({'t': 'error', 'msg': 'race in progress'})
                    return
                if len(self.conns) >= self.MAX_PLAYERS:
                    c.send_obj({'t': 'error', 'msg': 'room full'})
                    return
                c.id = 'p%d' % self.next_id
                self.next_id += 1
                c.name = str(m.get('name') or 'Racer')[:14]
                c.kart = int(m.get('kart', 0)) % KART_COUNT
                self.conns[c.id] = c
                if self.host_id is None:
                    self.host_id = c.id
            c.send_obj({'t': 'welcome', 'id': c.id})
            self._broadcast(self._room_msg())
            return
        if c.id is None:
            return
        if t in ('s', 'b', 'fin') or (isinstance(t, str) and t[:1] == 'i'):     # 'i*' = 아이템전 메시지
            m['id'] = c.id
            self._broadcast(m, exclude=c.id)
        elif t == 'profile':
            c.name = str(m.get('name') or c.name)[:14]
            c.kart = int(m.get('kart', c.kart)) % KART_COUNT
            self._broadcast(self._room_msg())
        elif t == 'settings':
            if self.host_id == c.id and self.state == 'lobby':
                if 'map' in m:
                    self.map = int(clamp(int(m['map']), 1, MAP_COUNT))
                if 'laps' in m:
                    self.laps = int(clamp(int(m['laps']), 1, 10))
                if 'bots' in m:
                    self.bots = int(clamp(int(m['bots']), 0, self.MAX_PLAYERS - 1))
                if 'items' in m:
                    self.items = bool(m['items'])
                self._broadcast(self._room_msg())
        elif t == 'start':
            if self.host_id == c.id and self.state == 'lobby':
                import random
                with self.lock:
                    self.state = 'racing'
                    order = [{'id': p.id, 'name': p.name, 'kart': p.kart} for p in self.conns.values()]
                    random.shuffle(order)
                    for i, p in enumerate(order):
                        p['slot'] = i
                    bots = []
                    for i in range(min(self.bots, self.MAX_PLAYERS - len(order))):
                        bots.append({'id': 'b%d' % (i + 1), 'name': 'BOT %d' % (i + 1), 'kart': random.randrange(KART_COUNT), 'slot': len(order) + i})
                    msg = {'t': 'start', 'map': self.map, 'laps': self.laps, 'countdown': 5.0, 'players': order, 'bots': bots, 'items': self.items}
                self._broadcast(msg)
        elif t == 'lobby':
            if self.host_id == c.id:
                with self.lock:
                    self.state = 'lobby'
                self._broadcast(self._room_msg())
                self._broadcast({'t': 'tolobby'})


class NetClient(object):
    def __init__(self):
        self.sock = None
        self.q = queue.Queue()
        self.connected = False
        self.status = 'idle'      # idle | connecting | connected | failed | closed
        self.error = ''
        self.id = None
        self._lock = threading.Lock()
        self._closing = False

    def connect_async(self, host, port, timeout=4.0):
        self.status = 'connecting'
        threading.Thread(target=self._connect, args=(host, port, timeout), daemon=True).start()

    def _connect(self, host, port, timeout):
        try:
            s = socket.create_connection((host, int(port)), timeout=timeout)
            try:
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except Exception:
                pass
            s.settimeout(2.0)
        except Exception as e:
            self.status = 'failed'
            self.error = str(e)
            return
        self.sock = s
        self.connected = True
        self.status = 'connected'
        self._read_loop()

    def _read_loop(self):
        buf = b''
        try:
            while self.connected:
                try:
                    data = self.sock.recv(8192)
                except socket.timeout:
                    continue
                if not data:
                    break
                buf += data
                while True:
                    k = buf.find(b'\n')
                    if k < 0:
                        break
                    line = buf[:k]
                    buf = buf[k + 1:]
                    if not line.strip():
                        continue
                    try:
                        self.q.put(json.loads(line.decode('utf-8')))
                    except Exception:
                        pass
        except Exception:
            pass
        finally:
            was = self.connected
            self.connected = False
            if was and not self._closing:
                self.status = 'closed'
                self.q.put({'t': 'close'})

    def send(self, obj):
        if not self.connected or self.sock is None:
            return
        data = (json.dumps(obj, separators=(',', ':')) + '\n').encode('utf-8')
        try:
            with self._lock:
                self.sock.sendall(data)
        except Exception:
            self.connected = False

    def poll(self):
        out = []
        while True:
            try:
                out.append(self.q.get_nowait())
            except queue.Empty:
                break
        return out

    def close(self):
        self._closing = True
        self.connected = False
        hard_close(self.sock)


def discover(timeout=1.3):
    """같은 WiFi 안에서 열려 있는 방을 UDP 브로드캐스트로 찾는다."""
    found = {}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(0.2)
        targets = ['255.255.255.255']
        for ip in local_ips():
            parts = ip.split('.')
            if len(parts) == 4:
                bc = '.'.join(parts[:3] + ['255'])
                if bc not in targets:
                    targets.append(bc)
        end = time.time() + timeout
        last = 0.0
        while time.time() < end:
            if time.time() - last > 0.4:
                for tg in targets:
                    try:
                        s.sendto(b'KART3D?', (tg, DISC_PORT))
                    except Exception:
                        pass
                last = time.time()
            try:
                data, addr = s.recvfrom(1024)
            except socket.timeout:
                continue
            except Exception:
                break
            try:
                info = json.loads(data.decode('utf-8'))
            except Exception:
                continue
            if isinstance(info, dict) and info.get('game') == 'kart3d':
                d = dict(info)
                d['ip'] = addr[0]
                found[(addr[0], d.get('port', DEFAULT_PORT))] = d
        s.close()
    except Exception:
        pass
    return list(found.values())


def discover_async(result):
    """result 는 dict. result['busy'], result['rooms'] 를 UI 가 읽는다."""
    def run():
        result['busy'] = True
        result['rooms'] = discover()
        result['busy'] = False
        result['done'] = True
    result['busy'] = True
    result['done'] = False
    threading.Thread(target=run, daemon=True).start()


class Session(object):
    """로비/접속 상태를 관리하는 얇은 계층. UI 는 이 객체의 필드만 읽고 메서드만 부른다."""

    def __init__(self, profile):
        self.profile = profile
        self.reset()

    def reset(self):
        self.net = None
        self.server = None
        self.state = 'idle'       # idle | connecting | lobby | racing
        self.error = ''
        self.my_id = None
        self.host_id = None
        self.players = []
        self.settings = {'map': 1, 'laps': 3, 'bots': 0, 'items': True}
        self.start_msg = None
        self.address = ''
        self._joined = False

    @property
    def is_host(self):
        return self.my_id is not None and self.my_id == self.host_id

    def host_game(self, port=DEFAULT_PORT):
        self.leave()
        try:
            self.server = RoomServer(port, name=self.profile.display_name()).start()
            self.server.map = int(self.profile['map'])
            self.server.laps = int(self.profile['laps'])
            self.server.items = self.profile['mode'] == 'item'
        except Exception as e:
            self.server = None
            self.error = 'server: %s' % e
            return False
        self._connect('127.0.0.1', port)
        return True

    def join_game(self, ip, port=DEFAULT_PORT):
        self.leave()
        self._connect(ip, port)

    def _connect(self, ip, port):
        self.net = NetClient()
        self.net.connect_async(ip, port)
        self.state = 'connecting'
        self.address = ip
        self.error = ''
        self._joined = False

    def pump(self):
        """매 프레임 호출. 레이스 중 메시지(s/b/fin/left/tolobby)를 돌려준다."""
        out = []
        net = self.net
        if net is None:
            return out
        if self.state == 'connecting':
            if net.status == 'connected' and not self._joined:
                self._joined = True
                net.send({'t': 'join', 'name': self.profile.display_name(), 'kart': self.profile['kart']})
            elif net.status == 'failed':
                self.error = net.error or 'connect failed'
                self.leave()
                return out
        for m in net.poll():
            t = m.get('t')
            if t == 'welcome':
                self.my_id = m.get('id')
            elif t == 'room':
                self.host_id = m.get('host')
                self.players = m.get('players', [])
                self.settings = {'map': m.get('map', 1), 'laps': m.get('laps', 3), 'bots': m.get('bots', 0), 'items': bool(m.get('items', False))}
                if self.state in ('connecting', 'idle'):
                    self.state = 'lobby'
            elif t == 'start':
                self.start_msg = m
                self.state = 'racing'
            elif t == 'tolobby':
                self.state = 'lobby'
                out.append(m)
            elif t == 'error':
                self.error = str(m.get('msg', 'error'))
                self.leave()
                return out
            elif t == 'close':
                self.error = 'disconnected'
                self.leave()
                return out
            else:
                out.append(m)
        return out

    def send_settings(self, **kw):
        if self.net is not None and self.is_host:
            msg = {'t': 'settings'}
            msg.update(kw)
            self.net.send(msg)

    def send_profile(self):
        if self.net is not None and self.state in ('lobby',):
            self.net.send({'t': 'profile', 'name': self.profile.display_name(), 'kart': self.profile['kart']})

    def start_race(self):
        if self.net is not None and self.is_host:
            self.net.send({'t': 'start'})

    def back_to_lobby(self):
        if self.net is not None and self.is_host:
            self.net.send({'t': 'lobby'})

    def entries_from_start(self, m):
        is_host = self.is_host
        entries = []
        for p in m.get('players', []):
            entries.append(dict(id=p['id'], name=p['name'], kart=p['kart'], slot=p['slot'], kind='local' if p['id'] == self.my_id else 'remote'))
        for b in m.get('bots', []):
            entries.append(dict(id=b['id'], name=b['name'], kart=b['kart'], slot=b['slot'], kind='bot' if is_host else 'remote'))
        return entries

    def leave(self):
        try:
            if self.net is not None:
                self.net.close()
        except Exception:
            pass
        try:
            if self.server is not None:
                self.server.stop()
        except Exception:
            pass
        err = self.error
        self.reset()
        self.error = err


def serve_forever(port=DEFAULT_PORT):
    """`python 파일.py --serve` : 전용 서버 (폰/PC 어디서든 접속 가능)"""
    srv = RoomServer(port, name='KART3D Server').start()
    print('KART3D 서버 시작 / server started  (port %d)' % port)
    for ip in local_ips():
        print('  접속 주소 / connect to:  %s  (포트 %d)' % (ip, port))
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        srv.stop()
