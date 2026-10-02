# -*- coding: utf-8 -*-
"""第二批图片（12张）复制、裁剪、放大。"""
import os, shutil
from PIL import Image

CLIP = (os.environ.get("KAIFENG_CLIP_DIR")
        or os.path.join(os.path.expanduser("~"), "clipboard-images"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "图片素材", "原图")
ZOOM = os.path.join(ROOT, "图片素材", "放大")
os.makedirs(SRC, exist_ok=True); os.makedirs(ZOOM, exist_ok=True)

batch2 = [
    "clipboard-2026-09-26T14-12-20-450Z-f1e094f5.jpg",
    "clipboard-2026-09-26T14-12-20-452Z-c9590a1f.jpg",
    "clipboard-2026-09-26T14-12-20-454Z-5f9744ef.jpg",
    "clipboard-2026-09-26T14-12-20-456Z-1bbc74e7.jpg",
    "clipboard-2026-09-26T14-12-20-458Z-d02bb9a3.jpg",
    "clipboard-2026-09-26T14-12-20-460Z-f6fcd0c0.jpg",
    "clipboard-2026-09-26T14-12-20-462Z-967cb295.jpg",
    "clipboard-2026-09-26T14-12-20-464Z-f0005454.jpg",
    "clipboard-2026-09-26T14-12-20-466Z-f1488c56.jpg",
    "clipboard-2026-09-26T14-12-20-468Z-f1842029.jpg",
    "clipboard-2026-09-26T14-12-20-469Z-ab26a2fa.jpg",
    "clipboard-2026-09-26T14-12-20-472Z-a9f5328c.jpg",
]
for k, n in enumerate(batch2):
    i = 51 + k
    p = os.path.join(CLIP, n)
    if not os.path.exists(p):
        print("MISSING", p); continue
    shutil.copy2(p, os.path.join(SRC, f"{i}.jpg"))
    im = Image.open(p).convert("RGB")
    w, h = im.size
    c = im.crop((int(w*0.575), int(h*0.02), int(w*0.875), int(h*0.985)))
    s = 2.2
    c = c.resize((int(c.width*s), int(c.height*s)), Image.LANCZOS)
    c.save(os.path.join(ZOOM, f"{i:02d}_right.jpg"), quality=95)
    print(i, f"{w}x{h}", n[-20:])
