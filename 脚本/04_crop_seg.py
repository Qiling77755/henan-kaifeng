# -*- coding: utf-8 -*-
"""表格/备忘录类图片：纵向切段放大，避免被压缩。"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "图片素材", "原图")
ZOOM = os.path.join(ROOT, "图片素材", "放大")

for i in [45, 46, 47, 49]:
    name = [f for f in os.listdir(SRC) if f.startswith(f"{i:02d}")][0]
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    w, h = im.size
    x0, x1 = int(w*0.295), int(w*0.615)
    y0, y1 = int(h*0.02), int(h*0.99)
    c = im.crop((x0, y0, x1, y1))
    H = c.height
    n = 4
    for k in range(n):
        seg = c.crop((0, k*H//n, c.width, min((k+1)*H//n + 14, H)))
        s = 2.6
        seg = seg.resize((int(seg.width*s), int(seg.height*s)), Image.LANCZOS)
        seg.save(os.path.join(ZOOM, f"{i:02d}_seg{k+1}.jpg"), quality=95)
    print(i, name, "->", n, "segments", seg.size)
