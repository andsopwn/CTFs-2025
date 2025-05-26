from pwn import *
import json, secrets, hashlib
from ecdsa.curves import NIST256p
from ecdsa.ellipticcurve import Point, PointJacobi

curve = NIST256p
G = curve.generator
p = G.order()

def point2bytes(P):
    return P.to_bytes()

def H(R, m):
    if isinstance(m, str):
        m = m.encode()
    return int.from_bytes(
        hashlib.sha256(point2bytes(R) + m).digest(), "big"
    ) % p

def recv_json(r):
    return json.loads(r.recvline().decode())

io = remote("tcp.sasc.tf", 11334)

io.sendline(json.dumps({"cmd": "GETKEY"}).encode())
Qx, Qy = recv_json(io)["Q"]
Q = PointJacobi.from_affine(Point(curve.curve, Qx, Qy))

io.sendline(json.dumps({"cmd": "REQUEST"}).encode())
Rx, Ry = recv_json(io)["R"]
R = PointJacobi.from_affine(Point(curve.curve, Rx, Ry))

c1 = secrets.randbelow(p - 1) + 1
io.sendline(json.dumps({"cmd": "CHALLENGE", "c": c1}).encode())
s1 = recv_json(io)["s"]

c2 = secrets.randbelow(p - 1) + 1
while c2 == c1:
    c2 = secrets.randbelow(p - 1) + 1
io.sendline(json.dumps({"cmd": "CHALLENGE", "c": c2}).encode())
s2 = recv_json(io)["s"]

d = ((s1 - s2) * pow((c1 - c2) % p, -1, p)) % p
log.success(f"recovered d = {hex(d)}")

for i in range(3):
    msg = f"FORGED-{i}"
    k = secrets.randbelow(p - 1) + 1
    Rf = (G * k).to_affine()
    c  = H(Rf, msg)
    s  = (k + c * d) % p
    sig = [[Rf.x(), Rf.y()], s]

    io.sendline(json.dumps({"cmd": "VERIFY", "msg": msg, "sig": sig}).encode())
    res = recv_json(io)
    log.info(res)

    if "msg" in res and "prize" in res["msg"]:
        print(res["msg"])
        break

io.interactive()

'''
pwned@CT100:~/CTFs-2025$ /usr/bin/env python3 "/home/pwned/CTFs-2025/sasctf/crpyt/blindspot/ex.py"
[+] Opening connection to tcp.sasc.tf on port 11334: Done
[+] recovered d = 0xc3aae1aea6900f15090425648662a531c8f729c8f7feb6a0b7a295f6905630e9
[*] {'status': 'ok', 'sign_cnt': 2, 'verify_cnt': 1}
[*] {'status': 'ok', 'sign_cnt': 2, 'verify_cnt': 2}
[*] {'status': 'ok', 'sign_cnt': 2, 'verify_cnt': 3}
[*] Switching to interactive mode
{"msg": "Wow, you can verify unsigned messages, here is your prize: SAS{r05_4t7ack_s3e5_7hr0u6h_7h3_bl1nd5p0t}"}
$ 
[*] Interrupted
[*] Closed connection to tcp.sasc.tf port 11334
$  
'''