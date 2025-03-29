import torch
import torch.nn.functional as F
import torchvision.transforms as T
import clip
import numpy as np
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"

model, preprocess = clip.load("ViT-B/32", device=device)
model.eval()

# 1) 원본 이미지 로드 & float tensor [0..1]로 변환
orig_img = Image.open('images/stop-doing-math.png').convert('RGB')
raw = np.array(orig_img, dtype=np.float32) / 255.0
H, W, C = raw.shape  # C=3

# (주의) 단순히 torch.Tensor(raw).requires_grad_(True)로 하면
#   preprocess()와의 autograd 연결이 끊어지므로
#   아래 예시에서는 "최적화 대상" 이미지(tensor_img)를
#   직접 224x224로 리사이즈하는 과정을 만듭니다.
# 여기서는 간략화 위해 "원본 크기 그대로" CLIP에 넣는다고 가정(사실 실제 CLIP는 Resize 224 과정을 거침)
#   => gradient는 대략적인 개념만 시연.

tensor_img = torch.tensor(raw, requires_grad=True, device=device)

# 2) 원본 임베딩 (고정)
with torch.no_grad():
    # 실제로는 preprocess(orig_img)를 해야 하나, 여기선 "원본 크기 그대로 encode_image" 시연
    orig_feat = model.encode_image(
        T.ToTensor()(orig_img).unsqueeze(0).to(device)
    )
orig_feat = orig_feat / orig_feat.norm(dim=-1, keepdim=True)

optimizer = torch.optim.Adam([tensor_img], lr=0.01)
lambda_penalty = 1000.0  # 평균 밝기 부족시 penalty

for step in range(5000):
    # 2-1) clamp: 이미지 픽셀 [0..1] 범위
    with torch.no_grad():
        tensor_img.clamp_(0, 1)
    # 2-2) forward
    cur_feat = model.encode_image(
        tensor_img.permute(2,0,1).unsqueeze(0)  # [C,H,W] 모양
    )
    cur_feat = cur_feat / cur_feat.norm(dim=-1, keepdim=True)
    sim = (cur_feat * orig_feat).sum()

    # 2-3) 평균 픽셀 (8비트 스케일 => *255)
    mean_val_255 = tensor_img.mean() * 255.0
    # 250 이하이면 penalty
    penalty = F.relu(250.0 - mean_val_255)

    # 2-4) 최종 Loss
    loss = (1.0 - sim) + lambda_penalty * penalty
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if step % 500 == 0:
        print(f"Step {step}, sim={sim.item():.6f}, mean={mean_val_255.item():.2f}, loss={loss.item():.6f}")
    # 2-5) 조기 종료
    if sim.item() >= 0.9999 and mean_val_255.item() >= 250:
        print(f"Step {step} -> success!")
        break

# 최종 결과 확인
with torch.no_grad():
    tensor_img.clamp_(0,1)
final_np = (tensor_img.detach().cpu().numpy() * 255).astype(np.uint8)
final_img = Image.fromarray(final_np)
final_img.save("final.png")

print("Done.")
