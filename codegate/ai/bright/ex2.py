#!/usr/bin/env python3

import base64
import io
import sys
import subprocess
from PIL import Image
import numpy as np
import clip
import torch

IMAGE_PATH = "images/stop-doing-math.png"

def solve_pow(challenge):
    result = subprocess.run(
        ["python3", "pow.py", "solve", challenge],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("PoW solving failed:", result.stderr)
        sys.exit(1)
    solution = result.stdout.strip()
    print(f"PoW Solution: {solution}")
    return solution

def prepare_image(image_path):
    model, preprocess = clip.load("ViT-B/32")
    orig_img = Image.open(image_path).convert("RGB")
    
    with torch.no_grad():
        orig_tensor = preprocess(orig_img).unsqueeze(0)
        orig_feature = model.encode_image(orig_tensor)[0].numpy()
        orig_feature = orig_feature / np.linalg.norm(orig_feature)
    
    width, height = orig_img.size
    size = max(width, height)
    new_img = Image.new("RGB", (size, size), (255, 255, 255))
    new_img.paste(orig_img, ((size - width) // 2, (size - height) // 2))
    
    img_array = np.array(new_img, dtype=np.float32)
    mean_rgb = img_array.mean()
    print(f"[{image_path}] Original RGB Mean: {mean_rgb}")
    
    if mean_rgb < 250:
        white_img = np.full_like(img_array, 255, dtype=np.float32)
        alpha = 0.0
        step = 1e-5  # ChatGPT와 동일한 초기 스텝
        
        # 1단계: ChatGPT 방식으로 선형 탐색 (0~1, step=1e-5)
        print(f"[{image_path}] [Phase 1] Searching alpha in [0..1] with step={step}, total steps ~ 100000")
        best_alpha = alpha
        best_sim = -1.0
        best_array = img_array.copy()
        total_steps = 100000
        
        for i in range(total_steps):
            alpha = i * step
            blended_array = img_array * (1 - alpha) + white_img * alpha
            mean_rgb = blended_array.mean()
            
            if mean_rgb >= 250:
                new_img = Image.fromarray(np.clip(blended_array, 0, 255).astype(np.uint8))
                with torch.no_grad():
                    new_tensor = preprocess(new_img).unsqueeze(0)
                    new_feature = model.encode_image(new_tensor)[0].numpy()
                    new_feature = new_feature / np.linalg.norm(new_feature)
                sim = np.dot(orig_feature, new_feature)
                
                if sim > best_sim:
                    best_sim = sim
                    best_alpha = alpha
                    best_array = blended_array.copy()
            
            if i % 10000 == 0:
                print(f"[{image_path}] Step {i}/{total_steps-1}, alpha={alpha:.5f}, cur_mean={mean_rgb:.2f}, best_sim={best_sim:.6f}")
            
            if mean_rgb > 250.1:  # 250.1 초과 시 중단
                break
        
        alpha = best_alpha
        blended_array = best_array
        mean_rgb = blended_array.mean()
        print(f"[{image_path}] [Phase 1 Result] Alpha {alpha:.5f}, RGB Mean: {mean_rgb}, Best Similarity: {best_sim}")
        
        # 2단계: 미세 조정으로 유사도 0.9999 목표
        if best_sim < 0.9999 and mean_rgb >= 250:
            print(f"[{image_path}] [Phase 2] Fine-tuning to reach Similarity > 0.9999")
            step = 1e-6  # 더 작은 스텝으로 정밀 조정
            max_attempts = 10000  # 추가 10,000번 시도
            direction = -1  # 초기 방향: 감소
            min_alpha = max(0.85, alpha - 0.05)  # 탐색 하한
            max_alpha = min(0.95, alpha + 0.05)  # 탐색 상한
            
            for attempt in range(max_attempts):
                blended_array = img_array * (1 - alpha) + white_img * alpha
                mean_rgb = blended_array.mean()
                
                new_img = Image.fromarray(np.clip(blended_array, 0, 255).astype(np.uint8))
                with torch.no_grad():
                    new_tensor = preprocess(new_img).unsqueeze(0)
                    new_feature = model.encode_image(new_tensor)[0].numpy()
                    new_feature = new_feature / np.linalg.norm(new_feature)
                sim = np.dot(orig_feature, new_feature)
                
                if sim > best_sim:
                    best_sim = sim
                    best_alpha = alpha
                    best_array = blended_array.copy()
                    print(f"[{image_path}] New best at Attempt {attempt}, Alpha {alpha:.6f}, RGB Mean: {mean_rgb}, Sim: {sim}")
                
                if attempt % 1000 == 0:
                    print(f"[{image_path}] Attempt {attempt}, Alpha {alpha:.6f}, RGB Mean: {mean_rgb}, Sim: {sim}, Step: {step:.6f}")
                
                if sim >= 0.9999 and mean_rgb >= 250:
                    print(f"[{image_path}] Success! Reached Similarity > 0.9999 at attempt {attempt}")
                    break
                
                # 방향 전환 및 스텝 조정
                if mean_rgb < 250:
                    direction = 1
                    alpha = best_alpha + step
                    step *= 0.5
                elif sim < best_sim - 0.0001:
                    direction *= -1
                    alpha = best_alpha
                    step *= 0.5
                elif alpha < min_alpha or alpha > max_alpha:
                    direction *= -1
                    alpha = best_alpha
                    step *= 0.5
                
                alpha += step * direction
                step = max(step, 1e-7)  # 최소 스텝 크기 제한
                
                if attempt == max_attempts - 1:
                    print(f"[{image_path}] Max attempts reached. Best Similarity {best_sim} at Alpha {best_alpha:.6f}")
                    blended_array = best_array
        
        img_array = np.clip(blended_array, 0, 255).astype(np.uint8)
    
    new_img = Image.fromarray(img_array)
    
    with torch.no_grad():
        new_tensor = preprocess(new_img).unsqueeze(0)
        new_feature = model.encode_image(new_tensor)[0].numpy()
        new_feature = new_feature / np.linalg.norm(new_feature)
    
    sim = np.dot(orig_feature, new_feature)
    mean_rgb = img_array.mean()
    print(f"[{image_path}] Final RGB Mean: {mean_rgb}")
    print(f"[{image_path}] Final Similarity with original: {sim}")
    
    if sim < 0.9999:
        print(f"[{image_path}] Warning: Similarity below 0.9999, flag may not be obtained.")
    
    img_buffer = io.BytesIO()
    new_img.save(img_buffer, format="PNG")
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
    return img_base64, sim

def interact_with_server(challenge, solution, img_base64):
    proc = subprocess.Popen(
        ["python3", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print(proc.stdout.readline())
    print(proc.stdout.readline())
    print(proc.stdout.readline())
    print(proc.stdout.readline())
    print(proc.stdout.readline())
    proc.stdin.write(solution + "\n")
    proc.stdin.flush()
    
    pow_result = proc.stdout.readline()
    print(pow_result)
    if "PoW succeeded!" not in pow_result:
        print("PoW verification failed.")
        sys.exit(1)
    
    part_size = len(img_base64) // 2
    part1 = img_base64[:part_size]
    part2 = img_base64[part_size:]
    
    print(proc.stdout.readline())
    proc.stdin.write(part1 + "\n")
    proc.stdin.flush()
    print(proc.stdout.readline())
    
    proc.stdin.write(part2 + "\n")
    proc.stdin.flush()
    print(proc.stdout.readline())
    
    proc.stdin.write("END\n")
    proc.stdin.flush()
    
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        print(line.strip())
        if "codegate2025" in line:
            print("Flag found:", line.strip())
            return True
    proc.wait()
    return False

def main():
    challenge = "s.Agpp.AAACOnD4tKmXgPwaySbExBhQ"
    solution = "s.AAA3e9t4YFJEVrnla1gyYHmCZ6Y0U5JSZ4gTT2RyB6YcVxwCLAnuU4tPjGFsodg9MJdyhFJDf0N4QEooNIoRg23P3pwgRvPDJ5PrLf881SfBrKup+eAEkrD1mSSh58ln8tN4kVbX39qKAI135Vp2E8JLRE9w40hOf05nVftQ8xulloadg+vAwnL7VOvneKKOFWi9yjNrxD4mJE+7v9jaNoGK"
    
    print(f"\nTrying image: {IMAGE_PATH}")
    try:
        img_base64, sim = prepare_image(IMAGE_PATH)
        if sim >= 0.9999:
            print(f"[{IMAGE_PATH}] Similarity is sufficient, submitting to server.")
        else:
            print(f"[{IMAGE_PATH}] Similarity insufficient, but submitting anyway.")
        
        flag_found = interact_with_server(challenge, solution, img_base64)
        if flag_found:
            print(f"Success with {IMAGE_PATH}!")
        else:
            print(f"Failed with {IMAGE_PATH}.")
    except FileNotFoundError:
        print(f"[{IMAGE_PATH}] not found.")

if __name__ == "__main__":
    main()