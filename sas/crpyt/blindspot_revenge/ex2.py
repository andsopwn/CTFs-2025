from pwn import *
import json
from ecdsa.curves import NIST256p
from ecdsa.ellipticcurve import Point, PointJacobi

HOST, PORT = "tcp.sasc.tf", 10914     
curve = NIST256p

def get_R():
    io = remote(HOST, PORT)
    io.recvline()
    io.send(b"sign")
    pkt = json.loads(io.recvline().decode())
    R = pkt["R"]
    io.close()
    return tuple(R)

Rs = {get_R() for _ in range(8)}
print(f"[+] r diff : {len(Rs)} / 8")