// The rooms over MQTT (tkMq / mqHost / mqJoin), a room and two phones: each hello reaches the room, each phone gets only its own answer
// (20 KB, whole), a phone that went away is dropped after 25 s. Against the live public brokers (needs ports 8884 / 8084), or a local one:
//   python3 tests/mq_broker.py 8899 &  MQ="'ws://localhost:8899/mqtt'" node tests/mq_live.mjs
import fs from 'fs';
const s = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const a = s.slice(s.indexOf('const TK_MQ = ['), s.indexOf('const TKNET = {')), m = s.slice(s.indexOf('  mqHost(code, onConn'), s.indexOf('  async host(code, onConn'));
globalThis.document = { addEventListener() {}, removeEventListener() {}, visibilityState: 'visible' }; globalThis.addEventListener = () => {}; globalThis.removeEventListener = () => {};
const LOG = []; globalThis.tkDbg = (x) => LOG.push(x); globalThis.tkErrS = String;
const a2 = process.env.MQ ? a.replace(/const TK_MQ = \[[^\]]*\]/, 'const TK_MQ = [' + process.env.MQ + ']') : a; const T = new Function(a2 + '; return {' + m + '};')(), wait = (ms) => new Promise((r) => setTimeout(r, ms));
const code = 'Z' + Math.random().toString(36).slice(2, 5).toUpperCase(), got = { host: [], g1: [], g2: [] }; let fails = 0;
const check = (name, ok, info) => { console.log((ok ? 'PASS ' : 'FAIL ') + name + (ok ? '' : '  | ' + JSON.stringify(info))); if (!ok) fails++; };
const H = await T.mqHost(code, (c) => { c.on('close', () => got.host.push('closed:' + c.peer)); c.on('data', (d) => { got.host.push(d.t + ':' + c.peer); if (d.t === 'hello') c.send({ t: 'lobby', you: c.peer, big: 'x'.repeat(20000) }); }); });
await wait(4000); check('the room is on the brokers', H.p.open, LOG);
const g1 = await T.mqJoin(code, (d) => got.g1.push(d.you + ':' + (d.big || '').length)), g2 = await T.mqJoin(code, (d) => got.g2.push(d.you + ':' + (d.big || '').length));
g1.send({ t: 'hello' }); g2.send({ t: 'hello' }); await wait(3500);
const hellos = got.host.filter((x) => x.startsWith('hello:')).map((x) => x.slice(6));
check('both hellos reach the room', hellos.length === 2, got);
check('each phone gets only its own answer (20 KB, whole)', got.g1.length === 1 && got.g2.length === 1 && got.g1[0] !== got.g2[0] && got.g1[0].endsWith(':20000') && hellos.includes(got.g1[0].split(':')[0]), got);
g2.close(); await wait(32000);
check('a phone that went away is dropped by the room (25 s of silence)', got.host.includes('closed:' + got.g2[0].split(':')[0]) && !got.host.includes('closed:' + got.g1[0].split(':')[0]), got);
H.close(); g1.close(); console.log('FAILURES: ' + fails); setTimeout(() => process.exit(fails ? 1 : 0), 300);
