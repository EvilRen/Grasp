# a tiny MQTT 3.1.1-over-WebSocket broker for tests: CONNECT/CONNACK, SUBSCRIBE/SUBACK (exact topics and the '+' wildcard), PUBLISH QoS 0 fan-out,
# retained messages (the last one per topic, sent to a new subscriber; an empty one clears it), PINGREQ/PINGRESP, DISCONNECT
# Standard library only, on purpose: it used to import the third-party `websockets`, which is not in the test requirements. When that import
# failed the broker died at once, the test's stderr=DEVNULL hid it, and the MQTT suite failed 30 s later on a click that could not work
# because nothing was listening. The WebSocket handshake and framing below are the few lines needed to serve one subprotocol ('mqtt').
import asyncio, sys, base64, hashlib
WS_GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
subs = {}  # topic filter -> set(conn)
kept = {}  # topic -> the PUBLISH body of its retained message
def rlen(n):
    out = bytearray()
    while True:
        d = n % 128; n //= 128
        out.append(d | (128 if n else 0))
        if not n: return bytes(out)
def match(f, t):
    a, b = f.split('/'), t.split('/')
    return len(a) == len(b) and all(x == '+' or x == y for x, y in zip(a, b))

class Conn:  # one browser socket: WebSocket frames in and out, nothing else
    def __init__(self, r, w): self.r, self.w, self.closed = r, w, False
    async def handshake(self):
        head = await self.r.readuntil(b'\r\n\r\n')
        lines = head.decode('latin-1').split('\r\n')
        h = {}
        for ln in lines[1:]:
            if ': ' in ln: k, v = ln.split(': ', 1); h[k.lower()] = v
        key = h.get('sec-websocket-key')
        if not key: return False
        acc = base64.b64encode(hashlib.sha1((key + WS_GUID).encode()).digest()).decode()
        out = ['HTTP/1.1 101 Switching Protocols', 'Upgrade: websocket', 'Connection: Upgrade', 'Sec-WebSocket-Accept: ' + acc]
        if 'mqtt' in [p.strip() for p in h.get('sec-websocket-protocol', '').split(',')]: out.append('Sec-WebSocket-Protocol: mqtt')
        self.w.write(('\r\n'.join(out) + '\r\n\r\n').encode()); await self.w.drain(); return True
    async def recv(self):  # the next data message, or None when the socket goes
        buf = b''
        while True:
            try: h = await self.r.readexactly(2)
            except (asyncio.IncompleteReadError, ConnectionError): return None
            op, n = h[0] & 0x0f, h[1] & 0x7f
            masked = h[1] & 0x80
            try:
                if n == 126: n = int.from_bytes(await self.r.readexactly(2), 'big')
                elif n == 127: n = int.from_bytes(await self.r.readexactly(8), 'big')
                mask = await self.r.readexactly(4) if masked else b''
                pay = await self.r.readexactly(n) if n else b''
            except (asyncio.IncompleteReadError, ConnectionError): return None
            if masked: pay = bytes(c ^ mask[i % 4] for i, c in enumerate(pay))
            if op == 0x8: return None                                   # close
            if op == 0x9: await self.send(pay, 0xa); continue           # ping -> pong
            if op == 0xa: continue                                      # pong
            buf += pay
            if h[0] & 0x80: return buf                                 # FIN: the whole message
    async def send(self, pay, op=0x2):
        if self.closed: return
        n = len(pay)
        if n < 126: hdr = bytes([0x80 | op, n])
        elif n < 65536: hdr = bytes([0x80 | op, 126]) + n.to_bytes(2, 'big')
        else: hdr = bytes([0x80 | op, 127]) + n.to_bytes(8, 'big')
        try: self.w.write(hdr + pay); await self.w.drain()
        except (ConnectionError, RuntimeError): self.closed = True
    async def close(self):
        if self.closed: return
        self.closed = True
        try: await self.send(b'', 0x8)
        except Exception: pass
        try: self.w.close()
        except Exception: pass

async def handler(r, w):
    ws = Conn(r, w); buf = b''; mine = set()
    try:
        if not await ws.handshake(): return
        while True:
            msg = await ws.recv()
            if msg is None: return
            buf += msg
            while len(buf) >= 2:
                n, mul, i = 0, 1, 1
                while True:
                    if i >= len(buf): break
                    d = buf[i]; i += 1; n += (d & 127) * mul; mul *= 128
                    if not d & 128: break
                if len(buf) < i + n: break
                h, body, buf = buf[0], buf[i:i + n], buf[i + n:]; ty = h >> 4
                if ty == 1: await ws.send(bytes([0x20, 2, 0, 0]))
                elif ty == 8:
                    pid = body[:2]; p = 2; codes = b''; new = []
                    while p < len(body):
                        tl = body[p] << 8 | body[p + 1]; t = body[p + 2:p + 2 + tl].decode(); p += 3 + tl
                        subs.setdefault(t, set()).add(ws); mine.add(t); codes += b'\x00'; new.append(t)
                    await ws.send(bytes([0x90]) + rlen(2 + len(codes)) + pid + codes)
                    for t, kb in list(kept.items()):
                        if any(match(f, t) for f in new): await ws.send(bytes([0x31]) + rlen(len(kb)) + kb)
                elif ty == 3:
                    tl = body[0] << 8 | body[1]; t = body[2:2 + tl].decode()
                    if h & 1:
                        if len(body) > 2 + tl: kept[t] = body
                        else: kept.pop(t, None)
                    for f, ws_set in list(subs.items()):
                        if not match(f, t): continue
                        for c in list(ws_set):
                            try: await c.send(bytes([0x30]) + rlen(len(body)) + body)
                            except Exception: pass
                elif ty == 12: await ws.send(bytes([0xd0, 0]))
                elif ty == 14: await ws.close(); return
    except (ConnectionError, asyncio.IncompleteReadError): pass
    finally:
        for t in mine: subs.get(t, set()).discard(ws)
        await ws.close()

async def main():
    srv = await asyncio.start_server(handler, 'localhost', int(sys.argv[1]))
    async with srv: await asyncio.Future()
asyncio.run(main())
