import os
from PIL import Image, ImageDraw

def save_tearsheet(df, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    img_path = os.path.join(out_dir, "tearsheet.png")
    img = Image.new("RGB", (900, 500), (245, 248, 250))
    d = ImageDraw.Draw(img)
    d.text((20,20), "MM_SENTIMENT v11 — Tearsheet (placeholder)", fill=(0,0,0))
    img.save(img_path)
    return img_path
