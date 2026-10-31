# a tiny MQTT 3.1.1-over-WebSocket broker for tests: CONNECT/CONNACK, SUBSCRIBE/SUBACK (exact topics and the '+' wildcard), PUBLISH QoS 0 fan-out,
# retained messages (the last one per topic, sent to a new subscriber; an empty one clears it), PINGREQ/PINGRESP, DISCONNECT
import asyncio, sys, websockets
subs = {}  # topic filter -> set(ws)
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
async def handler(ws):
    buf = b''; mine = set()
    try:
        async for msg in ws:
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
                        for w in list(ws_set):
                            try: await w.send(bytes([0x30]) + rlen(len(body)) + body)
                            except Exception: pass
                elif ty == 12: await ws.send(bytes([0xd0, 0]))
                elif ty == 14: await ws.close(); return
    finally:
        for t in mine: subs.get(t, set()).discard(ws)
async def main():
    async with websockets.serve(handler, 'localhost', int(sys.argv[1]), subprotocols=['mqtt']): await asyncio.Future()
asyncio.run(main())
