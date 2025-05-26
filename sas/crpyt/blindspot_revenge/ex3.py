from pwn import *
import json, hashlib, secrets, threading
from ecdsa.curves import NIST256p
from ecdsa.ellipticcurve import Point, PointJacobi

HOST, PORT = "tcp.sasc.tf", 10914
curve, G, p = NIST256p, NIST256p.generator, NIST256p.generator.order()

def pt2b(P): return P.to_bytes()
def H(R, m=b"x"): return int.from_bytes(hashlib.sha256(pt2b(R)+m).digest(), "big") % p
def jrecv(io): return json.loads(io.recvline().decode().strip())

def discover_valid_cmds():
    cmds = ["GETKEY", "REQKEY", "KEY", "PUBKEY", "INFO", "HELP"]
    for cmd in cmds:
        io = remote(HOST, PORT)
        io.recvline()
        io.send(json.dumps({"cmd": cmd}).encode() + b"\n")
        try:
            res = jrecv(io)
            print(f"[TRY] cmd={cmd} → {res}")
        except Exception as e:
            print(f"[ERROR] cmd={cmd} → Exception: {e}")
        io.close()

# discover_valid_cmds()
# exit(0)

io = remote(HOST, PORT)
io.recvline() 

io.send(json.dumps({"cmd": "KEY"}).encode() + b"\n")
resp = jrecv(io)
print(f"[DEBUG] KEY response: {resp}")

if "Q" not in resp:
    log.error("not support: {}".format(resp))
    io.close()
    exit(1)

Qx, Qy = resp["Q"]
Q = PointJacobi.from_affine(Point(curve.curve, Qx, Qy))

io.send(json.dumps({"cmd": "REQUEST"}).encode() + b"\n")
pkt = jrecv(io)
print(f"[DEBUG] REQUEST response: {pkt}")

Rx, Ry = pkt["R"]
R = PointJacobi.from_affine(Point(curve.curve, Rx, Ry))

sbox = {}

def ask(c):
    io.send(json.dumps({"cmd": "CHALLENGE", "c": c}).encode() + b"\n")
    sbox[c] = jrecv(io)["s"]

c1, c2 = 1, 2
t1 = threading.Thread(target=ask, args=(c1,))
t2 = threading.Thread(target=ask, args=(c2,))
t1.start(); t2.start(); t1.join(); t2.join()

s1, s2 = sbox[c1], sbox[c2]
d = ((s1 - s2) * pow((c1 - c2) % p, -1, p)) % p
log.success(f"[+] private d = {hex(d)}")

def forge(msg: str):
    k = secrets.randbelow(p - 1) + 1
    Rf = (G * k).to_affine()
    c = H(Rf, msg.encode())
    s = (k + c * d) % p
    return [[Rf.x(), Rf.y()], s]

io.close()

msgs = ["PWN0", "PWN1"]
for m in msgs:
    sg = forge(m)
    v = remote(HOST, PORT)
    v.recvline()
    v.send(json.dumps({"cmd": "VERIFY", "msg": m, "sig": sg}).encode() + b"\n")
    res = jrecv(v)
    print(f"[VERIFY] {m}: {res}")
    try:
        extra = jrecv(v)
        if "prize" in extra.get("msg", ""):
            print(extra["msg"])
            break
    except Exception:
        pass
    v.close()
