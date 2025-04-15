from pwn import *
from Crypto.Util.Padding import unpad
from time import sleep

context.log_level = 'debug'
HOST = "chall4.midnightflag.fr"
PORT = 10105
p = remote(HOST, PORT)
data = p.recv(1024).decode().splitlines()
ctr_line = data[0].strip()
cipher_hex = ctr_line.split("=")[1]
ct = bytes.fromhex(cipher_hex)
enc_line = data[1].strip()
iv = ct[:16]
enc = ct[16:]
n = 16
blocks = [enc[i:i+n] for i in range(0, len(enc), n)]
query_count = 0

def query_oracle(x):
    global query_count
    query_count += 1
    p.sendline(x.hex().encode())
    sleep(0.15)
    r = p.recvline().decode().strip()
    return ("Look's good" in r)

out = []
for i in range(len(blocks)):
    v = bytearray(n)
    for j in range(1, n+1):
        pos = n-j
        for g in range(256):
            t = bytearray(blocks[i])
            for k in range(pos+1, n):
                t[k] ^= v[k] ^ j
            t[pos] ^= g
            d = iv + b"".join(blocks[:i]) + bytes(t)
            print(f"[DEBUG] Query #{query_count+1}: block={i}, pos={pos}, guess=0x{g:02x}")
            if query_oracle(d):
                val = g ^ j
                v[pos] = val
                print(f"[DEBUG] FOUND: block={i}, pos={pos}, byte=0x{val:02x}")
                break
    out.append(bytes(v))

res = b"".join(out)
try:
    res = unpad(res, n)
except:
    pass
print(res)

