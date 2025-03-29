# auto_bruteforce_submit.py

import base64
from PIL import Image, ImageEnhance
import io
import numpy as np
import subprocess

CHALLENGE = "s.Agpp.AABDqugu9uTpNMLez4wsCW/z"
IMAGE_LIST = [
    "images/absolute-cinema.png",
    "images/hackerman.png",
    "images/oiia.png",
    "images/stop-doing-math.png"
]

def solve_pow(challenge: str) -> str:
    result = subprocess.check_output(["python3", "pow.py", "solve", challenge])
    return result.decode().strip()

def preprocess_image(image_path: str) -> str:
    img = Image.open(image_path).convert('RGB')
    mean = np.mean(np.array(img))
    if mean < 250:
        img = ImageEnhance.Brightness(img).enhance(255.0 / mean)

    if img.width != img.height:
        size = max(img.width, img.height)
        img = img.resize((size, size))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def run_server(solution: str, b64_image: str) -> str:
    from subprocess import Popen, PIPE

    proc = Popen(["python3", "server.py"], stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)

    image_parts = [b64_image[i:i+512] for i in range(0, len(b64_image), 512)]
    image_parts.append("END")

    try:
        stdout, stderr = proc.communicate(
            input=f"{solution}\n" + "\n".join(image_parts) + "\n",
            timeout=10
        )
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()

    return stdout

def main():
    solution = solve_pow(CHALLENGE)
    print(f"[*] PoW Solved: {solution}")

    for img_path in IMAGE_LIST:
        print(f"\n[>] Trying image: {img_path}")
        b64_img = preprocess_image(img_path)
        output = run_server(solution, b64_img)
        print(output)

        if "flag" in output.lower():
            print("[✔] Flag found!")
            break
        else:
            print("[✘] No flag with this image.")

if __name__ == "__main__":
    main()
