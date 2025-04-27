#!/usr/bin/env python3
from pwn import *
import struct, zlib, re, pathlib, sys

# 대상 파일 지정 (기본: Hidden message.png)
fname = sys.argv[1] if len(sys.argv) > 1 else "Hidden message.png"
data  = pathlib.Path(fname).read_bytes()

# 1) 모든 IDAT 청크 이어붙이기
pos, raw = 8, b''                       # PNG 시그니처 건너뜀
while pos < len(data) - 12:
    ln   = struct.unpack(">I", data[pos:pos+4])[0]
    typ  = data[pos+4:pos+8]
    if typ == b"IDAT":
        raw += data[pos+8:pos+8+ln]
    pos += 8 + ln + 4                  # 길이 + 타입 + 데이터 + CRC

log.info(f"IDAT 합계 {len(raw):,} bytes")

# 2) zlib inflate
try:
    inflated = zlib.decompress(raw)     # zlib 헤더 O
except zlib.error:
    inflated = zlib.decompress(raw, -15)# raw deflate

log.info(f"inflate 후 {len(inflated):,} bytes")

# 3) 내부 PNG 시그니처 검색 및 추출
cnt = 0
for m in re.finditer(b'\x89PNG\r\n\x1a\n', inflated):
    out = f"inner_{cnt}.png"
    pathlib.Path(out).write_bytes(inflated[m.start():])
    log.success(f"{out} 추출 완료")
    cnt += 1

if not cnt:
    log.failure("숨은 PNG 시그니처를 찾지 못했음")
