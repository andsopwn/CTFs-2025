#!/usr/bin/env python3
from pwn import *
import sys, binascii

def patch(fname, out, idx):
    buf = read(fname)
    assert buf.startswith(b'\x89PNG\r\n\x1a\n')
    off, outbuf = 8, buf[:8]
    while off < len(buf):
        ln  = u32(buf[off:off+4])
        typ = buf[off+4:off+8]
        dat = buf[off+8:off+8+ln]
        crc = buf[off+8+ln:off+12+ln]
        if typ == b'PLTE':
            assert ln % 3 == 0
            pal = bytearray(b'\x00\x00\x00' * (ln // 3))
            pal[idx*3:idx*3+3] = b'\xff\xff\xff'
            dat = bytes(pal)
            crc = p32(binascii.crc32(typ + dat) & 0xffffffff)
            ln  = len(dat)
        outbuf += p32(ln) + typ + dat + crc
        off += 12 + ln
    write(out, outbuf)

if __name__ == '__main__':
    patch(sys.argv[1], sys.argv[2], int(sys.argv[3]))
