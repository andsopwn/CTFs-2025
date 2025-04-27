#!/usr/bin/env python3
from pwn import *
context.log_level = 'error'

e   = ELF('./barcode')            # 대상 바이너리
lut = e.read( next(e.search(b' #')), 256 )  # 0x20=' ', 0x23='#' 패턴

def hex_to_qwords(s):
    s = s[2:] if s.startswith('0x') else s
    s = s.zfill((len(s)+15)//16*16)
    return [int(s[i:i+16],16) for i in range(0,len(s),16)]

def chain_decode(arr):
    for i in range(len(arr)-2, -1, -1):
        arr[i] = ~(arr[i] ^ arr[i+1]) & 0xFFFFFFFFFFFFFFFF
    return arr

def expand(qw):
    out = bytearray(64)
    for bit in range(64):
        out[bit] = lut[(qw>>bit)&1]
    return bytes(out)

if len(sys.argv)!=2:
    log.failure(f'usage: {sys.argv[0]} 0xHEX...')
    exit()

qws   = chain_decode( hex_to_qwords(sys.argv[1]) )
plain = b''.join( expand(q) for q in qws )

print( plain.decode() )
