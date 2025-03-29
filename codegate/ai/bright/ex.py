#!/usr/bin/env python3

import torch
import torch.nn.functional as F
import torchvision.transforms.functional as TF
from PIL import Image
import numpy as np
import clip

def resize_center_crop(tensor_img, size=224):
    """
    tensor_img: shape [C, H, W], float in [0..1]
    1) Resize the min dimension to `size` (keeping aspect ratio)
    2) Center-crop to (size, size)
    """
    C, H, W = tensor_img.shape
    # 1) resize shortest side to `size`
    #    PyTorch의 TF.resize()는 (H,W) 순으로 size를 넣어야 하며, antialias옵션 등은 1.12 이후 가능
    #    aspect 비율 맞춰야 하므로, scale factor 계산
    if H < W:
        newH = size
        newW = int(W * (size / H))
    else:
        newW = size
        newH = int(H * (size / W))
    resized = TF.resize(tensor_img, (newH, newW), antialias=True)

    # 2) center crop
    top = (newH - size) // 2
    left = (newW - size) // 2
    cropped = TF.crop(resized, top, left, size, size)
    return cropped

def clip_preprocess_tensor(tensor_img, device="cpu"):
    """
    tensor_img: shape [C, H, W], float in [0..1]
    Return shape [1, 3, 224, 224] normalized for CLIP
    """
    # 1) Resize & CenterCrop to 224
    out = resize_center_crop(tensor_img, size=224)
    # 2) Normalize to mean=[0.48145466, 0.4578275, 0.40821073], std=[0.26862954, 0.26130258, 0.27577711]
    #    (CLIP ViT-B/32 default)
    mean = torch.tensor([0.48145466, 0.4578275, 0.40821073], device=device).view(-1,1,1)
    std = torch.tensor([0.26862954, 0.26130258, 0.27577711], device=device).view(-1,1,1)
    out = (out - mean) / std
    # batch dimension
    return out.unsqueeze(0)

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Using device:", device)

    # 1) CLIP 로드
    model, _ = clip.load("ViT-B/32", device=device)
    model.eval()

    # 2) stop-doing-math.png 불러오고, 정사각형 패딩
    path_img = "images/stop-doing-math.png"
    pil_img = Image.open(path_img).convert("RGB")
    w, h = pil_img.size
    s = max(w, h)
    padded = Image.new("RGB", (s, s), (255,255,255))
    padded.paste(pil_img, ((s-w)//2, (s-h)//2))

    np_orig = np.array(padded, dtype=np.float32)  # shape [H, W, 3], range 0..255
    H, W, C = np_orig.shape
    print(f"Original shape: {H}x{W}, mean={np_orig.mean():.4f}")

    # 3) 원본 임베딩 (고정)
    #    텐서 변환: [3,H,W] in [0..1]
    base_torch = torch.tensor(np_orig.transpose(2,0,1) / 255.0, device=device, dtype=torch.float32)
    with torch.no_grad():
        # 원본 이미지에 대해 clip_preprocess_tensor
        in_orig = clip_preprocess_tensor(base_torch, device=device)
        feat_orig = model.encode_image(in_orig)
        feat_orig = feat_orig / feat_orig.norm(dim=-1, keepdim=True)  # normalize

    # 4) "학습 파라미터" (이미지 픽셀)
    #    deep copy해서 .requires_grad_(True)
    mod_torch = base_torch.clone().detach().requires_grad_(True)

    # 5) Hyperparameter
    lr = 1e-2           # 학습률 (필요시 조절)
    max_steps = 5000    # 반복 횟수
    lambda_bright = 2000.0  # 밝기 벌점 가중치(커질수록 mean 250을 빨리 만족)

    optimizer = torch.optim.Adam([mod_torch], lr=lr)

    for step in range(max_steps):
        # [0..1] 범위로 clamp
        with torch.no_grad():
            mod_torch.clamp_(0, 1)

        # CLIP 임베딩 계산
        # (grad 유지 위해, clip_preprocess_tensor에서 사용하는 연산들은 differentiable 함수여야 함)
        # mod_torch: [3,H,W] in [0..1]
        in_tensor = clip_preprocess_tensor(mod_torch, device=device)
        feat_cur = model.encode_image(in_tensor)
        feat_cur = feat_cur / feat_cur.norm(dim=-1, keepdim=True)
        sim = (feat_cur * feat_orig).sum()  # dot product

        # 픽셀 평균(8비트 스케일)
        mean_val = mod_torch.mean() * 255.0
        penalty = F.relu(250.0 - mean_val)  # mean<250면 양수, 아니면 0

        # 손실
        loss = (1.0 - sim) + lambda_bright * penalty

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if step % 100 == 0:
            print(f"Step {step}/{max_steps}, sim={sim.item():.6f}, mean={mean_val.item():.2f}, loss={loss.item():.6f}")

        # 조기 종료
        if mean_val.item() >= 250.0 and sim.item() >= 0.9999:
            print(f"[Success at step {step}] mean={mean_val.item():.2f}, sim={sim.item():.6f}")
            break

    # 최종 결과 clamp
    with torch.no_grad():
        mod_torch.clamp_(0, 1)

    # 6) 최종 이미지 저장
    final_np = (mod_torch.detach().cpu().numpy() * 255).astype(np.uint8)
    final_mean = final_np.mean()
    final_img = Image.fromarray(final_np.transpose(1,2,0), mode="RGB")
    out_path = "stop-doing-math_gradient.png"
    final_img.save(out_path)

    # 최종 유사도 재계산
    with torch.no_grad():
        final_in = clip_preprocess_tensor(torch.tensor(final_np.transpose(2,0,1)/255.0, device=device), device=device)
        final_feat = model.encode_image(final_in)
        final_feat = final_feat / final_feat.norm(dim=-1, keepdim=True)
        final_sim = (final_feat * feat_orig).sum().item()

    print(f"[Done] saved: {out_path}")
    print(f"Final mean={final_mean:.2f}, final sim={final_sim:.6f}")

    if final_mean >= 250.0 and final_sim >= 0.9999:
        print("[Result] 성공적으로 목표 달성!")
    else:
        print("[Result] mean>=250 and sim>=0.9999 달성 못 할 수도 있습니다.")

if __name__ == "__main__":
    main()
