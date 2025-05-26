from pwn import *
import numpy as np, os, re, sys

context.log_level = 'error'


def nullspace(A):
    A = A.copy() & 1; m, n = A.shape
    piv, r = [], 0
    for c in range(n):
        p = next((i for i in range(r, m) if A[i,c]), None)
        if p is None: continue
        A[[r,p]] = A[[p,r]]; piv.append(c)
        for i in range(m):
            if i != r and A[i,c]: A[i] ^= A[r]
        r += 1
    free = [c for c in range(n) if c not in piv]
    B = []
    for f in free:
        v = np.zeros(n, dtype=np.uint8); v[f] = 1
        for idx, p in enumerate(piv):
            if A[idx, f]: v[p] ^= 1
        B.append(v)
    return np.asarray(B, dtype=np.uint8)

def solve_kx63(G, c):
    A = np.concatenate([G.T.copy() & 1, c.reshape(-1,1)], 1)
    n, k1 = A.shape; k = k1-1; row = 0; piv = [-1]*k
    for col in range(k):
        p = next((i for i in range(row, n) if A[i,col]), None)
        if p is None: continue
        A[[row,p]] = A[[p,row]]
        for i in range(n):
            if i != row and A[i,col]: A[i] ^= A[row]
        piv[col] = row; row += 1
    x = np.zeros(k, dtype=np.uint8)
    for col in range(k-1, -1, -1):
        r = piv[col]
        if r == -1: continue
        val = A[r, -1]
        for j in range(col+1, k):
            val ^= A[r,j] & x[j]
        x[col] = val
    return x

def bits(h):
    return np.array(list(map(int, bin(int(h,16))[2:].rjust(len(h)*4,'0'))),
                    dtype=np.uint8)

def to_bytes(bs):
    return bytes(int(''.join(map(str, bs[i:i+8])),2)
                 for i in range(0,len(bs),8))

if len(sys.argv) != 3:
    log.error(f"usage: {sys.argv[0]} alice_pub.npy <cipher hex | file>")
G = np.load(sys.argv[1]).astype(np.uint8)
with open(sys.argv[2]) as f if os.path.isfile(sys.argv[2]) else \
     open(os.devnull) as f: pass
raw = open(sys.argv[2]).read() if os.path.isfile(sys.argv[2]) else sys.argv[2]
cipher_hex = ''.join(re.findall(r'[0-9a-fA-F]', raw)).lower()
c_bits = bits(cipher_hex)

H = nullspace(G)

# 0-62 bit bf
for sh in range(63):
    arr = c_bits[sh:]
    pad = (-len(arr)) % 63
    arr = np.concatenate([arr, np.zeros(pad, dtype=np.uint8)])
    k, n, blocks = 57, 63, len(arr)//63
    m_bits = []
    ok = True
    for i in range(blocks):
        c = arr[i*n:(i+1)*n].copy()
        s = (H @ c) & 1
        if s.any():
            pos = next((j for j in range(n)
                        if np.array_equal(H[:,j], s)), None)
            if pos is None: ok=False; break
            c[pos] ^= 1
            if (H @ c).any(): ok=False; break
        m_bits.extend(solve_kx63(G, c))
    if not ok or 1 not in m_bits: continue
    cut = len(m_bits) - 1 - m_bits[::-1].index(1)    # sentinel '1'
    if any(m_bits[cut+1:]): continue
    plain_bits = m_bits[:cut]
    if len(plain_bits)%8: continue
    pt = to_bytes(plain_bits)
    # printable
    if all(9<=b<128 for b in pt):
        print(pt.decode())
        break


'''
$ python3 ex.py alice_pub.npy output.txt
SAS{y0u_d0nt_r3ally_n33d_S_perm_t0_d3c0d3_Mc_3l1ec3_w1th_H4mm1ng_c0d3s}
'''