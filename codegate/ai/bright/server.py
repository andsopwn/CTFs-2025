from pow import get_challenge, verify_challenge

challenge = get_challenge(133737)

print("PoW challenge! Run the following code:")
print()
print("    python3 pow.py solve", challenge)
print()
solution = input("Solution? >>> ")

if not verify_challenge(challenge, solution, False):
    print("PoW failed...")
    exit(1)

print("PoW succeeded!")

import os
import io
import base64
import numpy as np
from glob import glob
from PIL import Image

def extract_feature(image):
    with torch.no_grad():
        image = preprocess(image).unsqueeze(0)
        feature = model.encode_image(image)[0].numpy()
        return feature / np.linalg.norm(feature)

def validate(image):
    return np.array(image.convert('RGB')).mean() > 250 and image.height == image.width

def load_features():
    features = []
    for path in glob("images/*.png"):
        image = Image.open(path)
        feature = extract_feature(image)
        features.append(feature)
    return features

image = ""
while True:
    # I hate socat truncating the input
    part = input("Give me your base64-encoded image parts >>> ").strip()
    if part == "END":
        break
    image += part
    if len(image) > 2**24:
        print("Your image is too large...")
        exit(1)

try:
    image = base64.b64decode(image)
except:
    print("Failed to decode your image")
    exit(1)

image = Image.open(io.BytesIO(image), formats=["JPEG", "PNG"])

if not validate(image):
    print("I don't like that image...")
    exit(1)

print("Evaluating...")

import clip
import torch

model, preprocess = clip.load("ViT-B/32")

feature = extract_feature(image)
features = load_features()

found = False

for feature_ref in features:
    sim = np.dot(feature, feature_ref)
    print(sim)
    if sim > 0.9999:
        from flag import flag
        print(flag)
        exit(0)
