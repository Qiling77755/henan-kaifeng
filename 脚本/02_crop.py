# -*- coding: utf-8 -*-
"""对网页截图裁剪出「评论区 / 正文侧栏」并放大，便于逐字识别。"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "图片素材", "原图")
ZOOM = os.path.join(ROOT, "图片素材", "放大")
os.makedirs(ZOOM, exist_ok=True)

for name in sorted(os.listdir(SRC)):
    i = int(name[:2])
    p = os.path.join(SRC, name)
    im = Image.open(p).convert("RGB")
    w, h = im.size
    if w > 1500:  # 网页宽屏截图
        # 右侧：正文+评论区
        box = (int(w*0.575), int(h*0.02), int(w*0.875), int(h*0.985))
        c = im.crop(box)
        s = 2.2
        c = c.resize((int(c.width*s), int(c.height*s)), Image.LANCZOS)
        c.save(os.path.join(ZOOM, f"{i:02d}_right.jpg"), quality=95)
        # 左侧：封面/图片区（部分帖子标题在左）
        box2 = (int(w*0.19), int(h*0.02), int(w*0.59), int(h*0.985))
        c2 = im.crop(box2)
        c2 = c2.resize((int(c2.width*1.6), int(c2.height*1.6)), Image.LANCZOS)
        c2.save(os.path.join(ZOOM, f"{i:02d}_left.jpg"), quality=92)
    else:  # 竖屏截图
        s = 1.7
        c = im.resize((int(w*s), int(h*s)), Image.LANCZOS)
        top = c.crop((0, 0, c.width, c.height//2))
        bot = c.crop((0, c.height//2, c.width, c.height))
        top.save(os.path.join(ZOOM, f"{i:02d}_top.jpg"), quality=95)
        bot.save(os.path.join(ZOOM, f"{i:02d}_bot.jpg"), quality=95)

print("done")
print(sorted(os.listdir(ZOOM))[:8])
