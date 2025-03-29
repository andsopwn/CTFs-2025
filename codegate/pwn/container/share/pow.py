import os
import subprocess
import socket
import time
import json
import base64
import sys
import hashlib
import uuid
import random
import fcntl
import errno
import re
import struct
import threading
import logging
import glob

# Configuration variables
BASE_IMAGE_NAME = "Windows11.qcow2"
BASE_IMAGE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), BASE_IMAGE_NAME
)
QEMU_PATH = "qemu-system-x86_64"
BOOT_TIMEOUT = 360
SEMAPHORE_FILE = "/tmp/qemu_vm_semaphore"
MAX_INSTANCES = 10
MAX_EXE_SIZE = 200 * 1024
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 1337
FLAG_PATH = "/flag" 

BIN_DIR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")

LOG_FILE = "vm_server.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def log_and_send(message, client_socket=None, client_address=None, vm_instance=None):
    """Log the message with client info and VM instance, and send it to the client if a socket is provided."""
    instance_info = f"[VM-{vm_instance}] " if vm_instance is not None else ""
    
    if client_address:
        log_message = f"[{client_address[0]}:{client_address[1]}] {instance_info}{message}"
    else:
        log_message = f"[SERVER] {instance_info}{message}"
    
    logger.info(log_message)

    if client_socket:
        try:
            client_socket.send(message.encode() + b"\n")
        except Exception as e:
            logger.error(f"Failed to send message to client: {str(e)}")

class Semaphore:
    def __init__(self, filename, max_instances):
        self.filename = filename
        self.max_instances = max_instances
        self.lockfd = None

    def acquire(self):
        while True:
            try:
                self.lockfd = open(self.filename, "r+")
                fcntl.flock(self.lockfd, fcntl.LOCK_EX)
                count = int(self.lockfd.read().strip() or "0")
                if count < self.max_instances:
                    self.lockfd.seek(0)
                    self.lockfd.write(str(count + 1))
                    self.lockfd.truncate()
                    fcntl.flock(self.lockfd, fcntl.LOCK_UN)
                    return True, count + 1
                fcntl.flock(self.lockfd, fcntl.LOCK_UN)
                self.lockfd.close()
                self.lockfd = None
                return False, count
            except IOError as e:
                if e.errno != errno.ENOENT:
                    raise
                try:
                    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
                    file_handle = os.open(self.filename, flags)
                    with os.fdopen(file_handle, "w") as f:
                        f.write("0")
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise
            time.sleep(1) 

    def release(self):
        if self.lockfd:
            fcntl.flock(self.lockfd, fcntl.LOCK_EX)
            self.lockfd.seek(0)
            count = int(self.lockfd.read().strip())
            self.lockfd.seek(0)
            self.lockfd.write(str(max(0, count - 1)))
            self.lockfd.truncate()
            fcntl.flock(self.lockfd, fcntl.LOCK_UN)
            self.lockfd.close()
            self.lockfd = None

    def get_current_count(self):
        try:
            with open(self.filename, "r") as f:
                return int(f.read().strip() or "0")
        except FileNotFoundError:
            return 0

def generate_pow():
    challenge = os.urandom(8)
    target = os.urandom(3)
    return challenge.hex(), target.hex()

def verify_pow(challenge, solution, target):
    full_challenge = bytes.fromhex(challenge + solution)
    hash_result = hashlib.sha256(full_challenge).hexdigest()
    return hash_result.startswith(target)

def generate_unique_path(prefix, suffix):
    return f"/tmp/{prefix}_{uuid.uuid4().hex}{suffix}"

def generate_mac_address():
    return "52:54:00:%02x:%02x:%02x" % (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )

def is_valid_exe(file_path):
    try:
        with open(file_path, "rb") as f:
            magic = f.read(2)
            return magic == b"MZ"
    except Exception:
        return False

def sanitize_command(command):
    return re.sub(r"[;&|`$()]", "", command)

def decode_and_save_exe(base64_input):
    try:
        decoded_data = base64.b64decode(base64_input)
        if len(decoded_data) > MAX_EXE_SIZE:
            raise ValueError(
                f"Decoded EXE size exceeds the limit of {MAX_EXE_SIZE} bytes"
            )

        temp_file_path = generate_unique_path("exe", ".exe")
        with open(temp_file_path, "wb") as f:
            f.write(decoded_data)

        if not is_valid_exe(temp_file_path):
            os.remove(temp_file_path)
            raise ValueError("Invalid EXE file format")

        return temp_file_path
    except base64.binascii.Error:
        raise ValueError("Invalid base64 input")
    except Exception as e:
        raise RuntimeError(f"Failed to decode and save EXE: {str(e)}")

def create_vm(base_image_path, overlay_path, qga_sock_path):
    subprocess.run(
        [
            "qemu-img",
            "create",
            "-f",
            "qcow2",
            "-F",
            "qcow2",
            "-b",
            base_image_path,
            overlay_path,
        ],
        check=True,
    )

    mac_address = generate_mac_address()
    qemu_command = [
        QEMU_PATH,
        "-enable-kvm",
        "-cpu","host",
        "-m",
        "2G",
        "-smp",
        "2",
        "-drive",
        f"file={overlay_path},format=qcow2",
        "-netdev",
        f"user,id=net0,net=192.168.76.0/24,dhcpstart=192.168.76.9",
        "-device",
        f"e1000,netdev=net0,mac={mac_address}",
        "-chardev",
        f"socket,path={qga_sock_path},server,nowait,id=qga0",
        "-device",
        "virtio-serial",
        "-device",
        "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0",
        "-nographic",
    ]
    process = subprocess.Popen(
        qemu_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return process

def wait_for_vm_boot(qga_sock_path, client_socket, client_address, vm_instance):
    log_and_send("Waiting for VM to boot...", client_socket, client_address, vm_instance)
    start_time = time.time()
    while time.time() - start_time < BOOT_TIMEOUT:
        if os.path.exists(qga_sock_path):
            try:
                cmd = {"execute": "guest-ping"}
                response = qga_command(cmd, qga_sock_path)
                if response.get("return") is not None:
                    log_and_send(
                        "VM is booted and QGA is ready", client_socket, client_address, vm_instance
                    )
                    time.sleep(30)
                    return True
            except Exception as e:
                log_and_send(
                    f"QGA not ready yet: {str(e)}", client_socket, client_address, vm_instance
                )
        else:
            log_and_send("Waiting for QGA socket...", client_socket, client_address, vm_instance)
        time.sleep(10)
    return False

def qga_command(cmd, qga_sock_path):
    retries = 5
    while retries > 0:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(qga_sock_path)
            sock.sendall(json.dumps(cmd).encode() + b"\n")

            response = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
                if b"\n" in data:
                    break

            sock.close()
            return json.loads(response.decode())
        except (socket.error, json.JSONDecodeError) as e:
            print(f"QGA command failed, retrying... ({str(e)})")
            retries -= 1
            time.sleep(2)

    raise Exception("Failed to execute QGA command after multiple retries")

def transfer_file_to_guest(local_path, guest_path, qga_sock_path):
    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")

    cmd = {
        "execute": "guest-file-open",
        "arguments": {"path": guest_path, "mode": "w+"},
    }
    response = qga_command(cmd, qga_sock_path)
    handle = response["return"]

    cmd = {
        "execute": "guest-file-write",
        "arguments": {"handle": handle, "buf-b64": content},
    }
    qga_command(cmd, qga_sock_path)

    cmd = {"execute": "guest-file-close", "arguments": {"handle": handle}}
    qga_command(cmd, qga_sock_path)

def execute_in_guest(command, qga_sock_path):
    sanitized_command = sanitize_command(command)
    cmd = {
        "execute": "guest-exec",
        "arguments": {
            "path": "powershell.exe",
            "arg": ["-Command", sanitized_command],
            "capture-output": True,
        },
    }
    response = qga_command(cmd, qga_sock_path)
    pid = response["return"]["pid"]

    while True:
        cmd = {"execute": "guest-exec-status", "arguments": {"pid": pid}}
        status = qga_command(cmd, qga_sock_path)
        if status["return"]["exited"]:
            result = status["return"]
            output = ""
            if "out-data" in result:
                output += base64.b64decode(result["out-data"]).decode(
                    "utf-8", errors="ignore"
                )
            if "err-data" in result:
                output += base64.b64decode(result["err-data"]).decode(
                    "utf-8", errors="ignore"
                )
            return output
        time.sleep(1)

def create_system_only_file(content, path, qga_sock_path):
    create_file_cmd = f"Set-Content -Path {path} -Value '{content}' -NoNewline"
    execute_in_guest(create_file_cmd, qga_sock_path)

    set_acl_cmd = f"""
    icacls {path} /inheritance:r /grant:r System:(R)
    """
    execute_in_guest(set_acl_cmd, qga_sock_path)

def read_flag_from_file():
    try:
        with open(FLAG_PATH, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: Flag file not found at {FLAG_PATH}")
        return None
    except Exception as e:
        print(f"Error reading flag file: {str(e)}")
        return None

def cleanup_vm(process, overlay_path, qga_sock_path):
    if process:
        process.terminate()
    if os.path.exists(overlay_path):
        os.remove(overlay_path)
    if os.path.exists(qga_sock_path):
        os.remove(qga_sock_path)

def shutdown_vm(qga_sock_path):
    """Safely shutdown the VM through QGA"""
    try:
        cmd = {"execute": "guest-shutdown"}
        qga_command(cmd, qga_sock_path)
        return True
    except Exception as e:
        print(f"Failed to shutdown VM: {str(e)}")
        return False

def run_exe_in_vm(base64_exe, client_socket, client_address):
    semaphore = Semaphore(SEMAPHORE_FILE, MAX_INSTANCES)
    local_exe_path = None
    overlay_path = generate_unique_path("overlay", ".qcow2")
    qga_sock_path = generate_unique_path("qga", ".sock")
    process = None
    acquired = False
    vm_instance = None

    try:
        acquired, count = semaphore.acquire()
        vm_instance = count 

        if not acquired:
            log_and_send(
                f"Maximum number of instances ({MAX_INSTANCES}) reached.",
                client_socket,
                client_address,
                vm_instance
            )
            log_and_send(
                f"Currently running instances: {count}", 
                client_socket, 
                client_address,
                vm_instance
            )
            log_and_send(
                "Waiting for an available slot...", 
                client_socket, 
                client_address,
                vm_instance
            )

            while not acquired:
                time.sleep(5)
                acquired, count = semaphore.acquire()
                vm_instance = count
                if not acquired:
                    current_count = semaphore.get_current_count()
                    log_and_send(
                        f"Still waiting. Current instances: {current_count}/{MAX_INSTANCES}",
                        client_socket,
                        client_address,
                        vm_instance
                    )

        log_and_send(
            f"Slot available. Proceeding with VM creation. (Instance #{vm_instance})",
            client_socket,
            client_address,
            vm_instance
        )

        try:
            local_exe_path = decode_and_save_exe(base64_exe)
            process = create_vm(BASE_IMAGE_PATH, overlay_path, qga_sock_path)

            if not wait_for_vm_boot(qga_sock_path, client_socket, client_address, vm_instance):
                raise Exception("VM boot timeout or Windows not ready")

            log_and_send(
                "VM is ready. Proceeding with execution...", 
                client_socket, 
                client_address,
                vm_instance
            )

            flag_content = read_flag_from_file()
            if flag_content is None:
                raise Exception("Failed to read flag content")

            create_system_only_file(flag_content, "C:\\Windows\\system32\\flag.txt", qga_sock_path)

       
            log_and_send(
                "Creating destination directory structure", 
                client_socket, 
                client_address,
                vm_instance
            )
            destination_dir = "C:\\Users\\Codegate\\AppData\\Local\\ctf\\bin"
            mkdir_cmd = f'New-Item -Path "{destination_dir}" -ItemType Directory -Force'
            execute_in_guest(mkdir_cmd, qga_sock_path)
            log_and_send(
                "Transferring all bin files to VM", 
                client_socket, 
                client_address,
                vm_instance
            )
            bin_files = glob.glob(os.path.join(BIN_DIR_PATH, "*"))
            
            for local_file_path in bin_files:
                filename = os.path.basename(local_file_path)
                guest_file_path = f"{destination_dir}\\{filename}"
                log_and_send(
                    f"Transferring {filename} to VM", 
                    client_socket, 
                    client_address,
                    vm_instance
                )
                transfer_file_to_guest(local_file_path, guest_file_path, qga_sock_path)


            payload_filename = os.path.basename(local_exe_path)
            guest_payload_path = f"{destination_dir}\\{payload_filename}"
            log_and_send(
                f"Transferring payload {payload_filename} to VM", 
                client_socket, 
                client_address,
                vm_instance
            )
            transfer_file_to_guest(local_exe_path, guest_payload_path, qga_sock_path)

    
            log_and_send(
                "Loading the CodeGate.sys driver as a service", 
                client_socket, 
                client_address,
                vm_instance
            )
            driver_load_cmd = f'''
            # Create the service
            sc.exe create ctf type= kernel binpath=C:\\Users\\Codegate\\AppData\\Local\\ctf\\bin\\CodeGate.sys
            
            # Start the service
            sc.exe start ctf
            '''
            result = execute_in_guest(driver_load_cmd, qga_sock_path)
            log_and_send(
                f"Driver load result:\n{result}", 
                client_socket, 
                client_address,
                vm_instance
            )

         
            log_and_send(
                "Executing LaunchSandbox.bat with payload.exe", 
                client_socket, 
                client_address,
                vm_instance
            )
            execute_cmd = f'C:\\Users\\Codegate\\AppData\\Local\\ctf\\bin\\LaunchSandbox.bat C:\\Users\\Codegate\\AppData\\Local\\ctf\\bin\\{payload_filename}'
            result = execute_in_guest(execute_cmd, qga_sock_path)
            log_and_send(
                f"Execution result:\n{result}", 
                client_socket, 
                client_address,
                vm_instance
            )


            log_and_send(
                "Checking for running processes and waiting for completion...", 
                client_socket, 
                client_address,
                vm_instance
            )

            check_process_cmd = f'Get-Process -Name "{os.path.splitext(payload_filename)[0]}" -ErrorAction SilentlyContinue'
            max_wait = 180  
            wait_interval = 5
            total_waited = 0

            while total_waited < max_wait:
                process_check = execute_in_guest(check_process_cmd, qga_sock_path)
                if not process_check.strip():
                    log_and_send(
                        f"Process has terminated after waiting {total_waited} seconds", 
                        client_socket, 
                        client_address,
                        vm_instance
                    )
                    break
                
                log_and_send(
                    f"Process still running, waiting {wait_interval} more seconds...", 
                    client_socket, 
                    client_address,
                    vm_instance
                )
                time.sleep(wait_interval)
                total_waited += wait_interval

            if total_waited >= max_wait:
                log_and_send(
                    f"Process did not terminate within {max_wait} seconds, proceeding with shutdown", 
                    client_socket, 
                    client_address,
                    vm_instance
                )

            log_and_send(
                "Execution complete. Shutting down VM...", 
                client_socket, 
                client_address,
                vm_instance
            )
            shutdown_vm(qga_sock_path)
            time.sleep(10)

        except Exception as e:
            log_and_send(
                f"Error: {str(e)}", 
                client_socket, 
                client_address,
                vm_instance
            )
        finally:
            cleanup_vm(process, overlay_path, qga_sock_path)
            if local_exe_path and os.path.exists(local_exe_path):
                os.remove(local_exe_path)

    finally:
        if acquired:
            semaphore.release()
            log_and_send(
                f"Released instance slot #{vm_instance}. Current instances: {semaphore.get_current_count()}/{MAX_INSTANCES}",
                client_socket,
                client_address,
                vm_instance
            )

def handle_client(client_socket, client_address):
    client_socket.settimeout(300) 
    try:
        challenge, target = generate_pow()
        log_and_send("Proof of Work required", client_socket, client_address)
        log_and_send(f"Challenge: {challenge}", client_socket, client_address)
        log_and_send(f"Target: {target}", client_socket, client_address)
        log_and_send("Solution: ", client_socket, client_address)

        solution = client_socket.recv(1024).decode().strip()

        if not verify_pow(challenge, solution, target):
            log_and_send(
                "Error: Invalid Proof of Work solution.", client_socket, client_address
            )
            return

        log_and_send(
            "Proof of Work verified. Proceeding with execution.",
            client_socket,
            client_address
        )
        log_and_send(
            "Please enter the base64 encoded EXE file:", client_socket, client_address
        )

        base64_exe = b""
        try:
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    raise ConnectionResetError("Connection closed by the client")
                base64_exe += chunk
                if b"\n" in chunk:
                    break
        except socket.timeout:
            raise Exception("Timeout while receiving base64 encoded EXE")

        base64_exe = base64_exe.decode().strip()

        if not base64_exe:
            log_and_send("Error: No input provided.", client_socket, client_address)
            return

        try:
            run_exe_in_vm(base64_exe, client_socket, client_address)
        except Exception as e:
            log_and_send(
                f"An unexpected error occurred: {str(e)}", client_socket, client_address
            )
    except socket.timeout:
        log_and_send("Error: Connection timed out.", client_socket, client_address)
    except ConnectionResetError:
        log_and_send("Error: Connection was reset by the client.", client_socket, client_address)
    except Exception as e:
        log_and_send(f"An unexpected error occurred: {str(e)}", client_socket, client_address)
    finally:
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(5)
    log_and_send(f"Listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client, addr = server.accept()
        log_and_send(f"Accepted connection from {addr[0]}:{addr[1]}")
        client_handler = threading.Thread(target=handle_client, args=(client, addr))
        client_handler.start()

if __name__ == "__main__":
    start_server()