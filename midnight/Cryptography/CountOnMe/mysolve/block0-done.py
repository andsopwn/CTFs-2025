from pwn import *
import sys
import time

context.log_level = 'debug'
HOST="chall3.midnightflag.fr"
PORT=11085
p=remote(HOST,PORT)
d=p.recv(1024).decode().splitlines()
a=d[0].strip()
b=a.split("=")[1]
ct=bytes.fromhex(b)
enc_line=d[1].strip()
iv=ct[:16]
enc=ct[16:]
n=16
blocks=[enc[i:i+n]for i in range(0,len(enc),n)]
q=0
def o(x):
    global q
    q+=1
    p.sendline(x.hex().encode())
    time.sleep(0.15)
    r=p.recvline().decode().strip()
    return("Look's good"in r)

block0=bytearray(n)
block0[15]=0x63
block0[14]=0x61
block0[13]=0x72
block0[12]=0x4f
block0[11]=0x67
block0[10]=0x6e
block0[9]=0x69
block0[8]=0x64
block0[7]=0x64
block0[6]=0x61
block0[5]=0x50
block0[4]=0x7b
block0[3]=0x46
block0[2]=0x54
block0[1]=0x43
block0[0]=0x01
out=[]
if len(blocks)>0:
    out.append(bytes(block0))

for i in range(1,len(blocks)):
    v=bytearray(n)
    # pos=15은 이미 0x01 패딩으로 'Look's good'가 뜸
    # 그 뒤 pos=14..0가 전부 추가 패딩인지 확인
    # PKCS7 규칙상 pos=14는 0x02, pos=13은 0x03... 순으로 맞는지 시험
    # 만약 어떤 지점에서 안 맞으면 실제 데이터가 있을 수 있으므로 brute force
    pad_candidate=2
    for pos in range(14,-1,-1):
        f=False
        # pos=14 => pad_candidate=2, pos=13 => pad_candidate=3...
        # pos=15=1은 이미 확정
        # 한번만 pad_candidate 값을 직접 넣고 테스트
        guess_val=pad_candidate
        pad_candidate+=1
        t=bytearray(blocks[i])
        for k in range(pos+1,n):
            t[k]^=v[k]^(guess_val)
        t[pos]^=guess_val
        c=iv+b"".join(blocks[:i])+bytes(t)
        print(f"[DEBUG] Query #{q+1}: block={i}, pos={pos}, forcedPad=0x{guess_val:02x}")
        if o(c):
            v[pos]=guess_val
            print(f"[DEBUG] FOUND block={i}, pos={pos}, byte=0x{guess_val:02x} (padding)")
            f=True
        else:
            # 안 맞으면 이 pos부터는 실제 데이터가 있을 수 있으니 brute force
            # 0x00..0xff 돌림
            print(f"[INFO] pos={pos}, forced pad=0x{guess_val:02x} not matched, brute forcing")
            real_found=False
            for g in range(256):
                t2=bytearray(blocks[i])
                for k2 in range(pos+1,n):
                    t2[k2]^=v[k2]^(n-pos) 
                t2[pos]^=g
                c2=iv+b"".join(blocks[:i])+bytes(t2)
                print(f"[DEBUG] Query #{q+1}: block={i}, pos={pos}, guess=0x{g:02x}")
                if o(c2):
                    val=g^(n-pos)
                    v[pos]=val
                    print(f"[DEBUG] FOUND block={i}, pos={pos}, byte=0x{val:02x} (data)")
                    real_found=True
                    break
            if not real_found:
                print(f"[-] block={i}, pos={pos} no valid guess found. Exiting.")
                sys.exit(1)
            f=True
        if not f:
            print(f"[-] block={i}, pos={pos} can't resolve. Exiting.")
            sys.exit(1)
    out.append(bytes(v))
res=b"".join(out)
print(res)
