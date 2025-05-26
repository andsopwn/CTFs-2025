#!/usr/bin/env python3
from pwn import *
import json, hashlib, secrets, threading
from ecdsa.curves import NIST256p
from ecdsa.ellipticcurve import Point, PointJacobi

HOST, PORT = "tcp.sasc.tf", 11800
curve, G, p = NIST256p, NIST256p.generator, NIST256p.generator.order()

def pt2b(P): return P.to_bytes()
def H(R,m=b"x"): return int.from_bytes(hashlib.sha256(pt2b(R)+m).digest(),"big")%p

io = remote(HOST, PORT)

io.recvline()
io.send(b"sign")

resp = json.loads(io.recvline().decode())
Rx,Ry = resp["R"]; Qx,Qy = resp["Q"]
R = PointJacobi.from_affine(Point(curve.curve, Rx, Ry))
Q = PointJacobi.from_affine(Point(curve.curve, Qx, Qy))

c1, c2 = 1, 2
s_recv = {}

def ask(c):
    io.send(json.dumps({"c": c}).encode()+b"\n")
    s = json.loads(io.recvline().decode())["s"]
    s_recv[c] = s

t1 = threading.Thread(target=ask, args=(c1,))
t2 = threading.Thread(target=ask, args=(c2,))
t1.start(); t2.start(); t1.join(); t2.join()

s1, s2 = s_recv[c1], s_recv[c2]
log.info(f"s1={s1}\ns2={s2}")

# extra d
d = ((s1 - s2) * pow(c1 - c2, -1, p)) % p
log.success(f"private d = {hex(d)}")

# 서명위조
def forge(msg: bytes):
    k = secrets.randbelow(p-1)+1
    Rf = (G * k).to_affine()
    c  = H(Rf, msg)
    s  = (k + c*d) % p
    return [[Rf.x(), Rf.y()], s]

sig = forge(b"seojun")
log.success(f"forged sig: {sig}")

v = remote(HOST, PORT); v.recvuntil(b':')
v.send(b"verify")
v.send(json.dumps({"sig": sig, "msg": "seojun"}).encode()+b"\n")

print(v.recvline().decode())
extra = v.recvline().decode()
print(extra)
