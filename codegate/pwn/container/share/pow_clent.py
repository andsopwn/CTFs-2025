from pwn import *
import hashlib
import base64
import os
import argparse

context.log_level = "debug"

HOST = "localhost"
PORT = 1337


def solve_pow(challenge, target):
    log.info(f"Solving PoW: challenge = {challenge}, target = {target}")
    for i in range(2**32):
        solution = i.to_bytes(4, "big").hex()
        full_challenge = bytes.fromhex(challenge + solution)
        hash_result = hashlib.sha256(full_challenge).hexdigest()
        if hash_result.startswith(target):
            log.success(f"Solution found: {solution}")
            return solution
    raise Exception("PoW solution not found")


def read_exploit_file(filename):
    log.info(f"Reading exploit file: {filename}")
    with open(filename, "rb") as f:
        data = f.read()
    log.info(f"Exploit file size: {len(data)} bytes")
    return data


def main(exe_path):
    conn = remote(HOST, PORT)

    log.info("Connected to server. Waiting for initial output...")
    initial_output = conn.recvuntil(b"Challenge: ", drop=True)
    print(initial_output.decode())

    challenge = conn.recvline().strip().decode()
    log.info(f"Received challenge: {challenge}")

    conn.recvuntil(b"Target: ")
    target = conn.recvline().strip().decode()
    log.info(f"Received target: {target}")

    conn.recvuntil(b"Solution: ")

    try:
        solution = solve_pow(challenge, target)
        log.info(f"Sending solution: {solution}")
        conn.sendline(solution.encode())
    except Exception as e:
        log.failure(f"Failed to solve PoW: {str(e)}")
        conn.close()
        return

    log.info("Waiting for server response...")
    response = conn.recvuntil(b"Please enter the base64 encoded EXE file:", drop=True)
    print(response.decode())

    if b"Invalid Proof of Work solution" in response:
        log.failure("Failed to solve PoW. Exiting.")
        conn.close()
        return

    try:
        exploit_data = read_exploit_file(exe_path)
    except FileNotFoundError:
        log.failure(f"Error: {exe_path} file not found.")
        conn.close()
        return
    except IOError:
        log.failure(f"Error: Could not read {exe_path} file.")
        conn.close()
        return

    exploit_base64 = base64.b64encode(exploit_data).decode()

    log.info("Sending encoded exploit...")
    conn.sendline(exploit_base64.encode())

    log.info("Exploit sent. Switching to interactive mode...")
    conn.interactive()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PoW client for CTF challenge")
    parser.add_argument("exe_path", help="Path to the exploit EXE file")
    args = parser.parse_args()

    main(args.exe_path)
