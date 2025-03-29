# submit_image.py

import base64
from PIL import Image, ImageEnhance
import io
import numpy as np
import os

image_path = "images/stop-doing-math.png" 
chunk_size = 512
print_mode = True

img = Image.open(image_path).convert('RGB')

mean = np.mean(np.array(img))
if mean < 250:
    enhancer = ImageEnhance.Brightness(img)
    factor = 255.0 / mean
    img = enhancer.enhance(factor)

if img.width != img.height:
    size = max(img.width, img.height)
    img = img.resize((size, size))

buf = io.BytesIO()
img.save(buf, format='PNG')
byte_data = buf.getvalue()
b64 = base64.b64encode(byte_data).decode()

if print_mode:
    print("[*] Submit the following parts to the server:")
    for i in range(0, len(b64), chunk_size):
        print(b64[i:i+chunk_size])
    print("END")
else:
    parts = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
    parts.append("END")
    output = "\n".join(parts)
    with open("submission.txt", "w") as f:
        f.write(output)
    print("[*] Written to submission.txt")
