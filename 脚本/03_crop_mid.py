# -*- coding: utf-8 -*-
"""对「居中图片型」截图（表格、备忘录）裁剪中心文字区并放大。"""
import os
from PIL import Image

ROOT = r"E:\children‘s day file\开封美食地图"
SRC = os.path.join(ROOT, "图片素材", "原图")
ZOOM = os.path.join(ROOT, "图片素材", "放大")

for i in [42, 43, 44, 45, 46, 47, 49, 50]:
    name = [f for f in os.listdir(SRC) if f.startswith(f"{i:02d}")][0]
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    w, h = im.size
    c = im.crop((int(w*0.285), int(h*0.02), int(w*0.625), int(h*0.98)))
    s = 2.6
    c = c.resize((int(c.width*s), int(c.height*s)), Image.LANCZOS)
    c.save(os.path.join(ZOOM, f"{i:02d}_mid.jpg"), quality=95)
    print(i, name, im.size, "->", c.size)
