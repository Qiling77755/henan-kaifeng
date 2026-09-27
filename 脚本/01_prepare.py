# -*- coding: utf-8 -*-
"""按用户给定的顺序，把 50 张图片复制到工作区，并生成放大版便于文字识别。"""
import os, shutil
from PIL import Image

CLIP = r"C:\Users\17225\.workbuddy\clipboard-images"
GOOGLE = r"E:\Google download"
ROOT = r"E:\children‘s day file\开封美食地图"
SRC = os.path.join(ROOT, "图片素材", "原图")
ZOOM = os.path.join(ROOT, "图片素材", "放大")
os.makedirs(SRC, exist_ok=True)
os.makedirs(ZOOM, exist_ok=True)

clip_names = [
    "clipboard-2026-09-26T13-22-40-706Z-83d01475.jpg",
    "clipboard-2026-09-26T13-22-40-707Z-07a23735.jpg",
    "clipboard-2026-09-26T13-22-40-709Z-15510ecd.jpg",
    "clipboard-2026-09-26T13-22-40-711Z-b5421263.jpg",
    "clipboard-2026-09-26T13-22-40-714Z-ace89cea.jpg",
    "clipboard-2026-09-26T13-22-40-716Z-3338033b.jpg",
    "clipboard-2026-09-26T13-22-40-718Z-6ea0e849.jpg",
    "clipboard-2026-09-26T13-22-40-720Z-0775853d.jpg",
    "clipboard-2026-09-26T13-22-40-722Z-9944fc68.jpg",
    "clipboard-2026-09-26T13-22-40-724Z-23b3bb36.jpg",
    "clipboard-2026-09-26T13-22-40-726Z-fcc212f6.jpg",
    "clipboard-2026-09-26T13-22-40-727Z-feceae70.jpg",
    "clipboard-2026-09-26T13-22-40-729Z-e5f415da.jpg",
    "clipboard-2026-09-26T13-22-40-731Z-9839c010.jpg",
    "clipboard-2026-09-26T13-22-40-733Z-41449ace.jpg",
    "clipboard-2026-09-26T13-22-40-735Z-faf7ecb1.jpg",
    "clipboard-2026-09-26T13-22-40-736Z-c346801e.jpg",
    "clipboard-2026-09-26T13-22-40-738Z-4d14a903.jpg",
    "clipboard-2026-09-26T13-22-40-740Z-20d677ba.jpg",
    "clipboard-2026-09-26T13-22-40-742Z-9d7d6ca1.jpg",
    "clipboard-2026-09-26T13-22-40-745Z-6d051031.jpg",
    "clipboard-2026-09-26T13-22-40-747Z-872438c4.jpg",
    "clipboard-2026-09-26T13-22-40-749Z-a63558d8.jpg",
    "clipboard-2026-09-26T13-22-40-751Z-410b73e5.jpg",
]
google_names = [
    "和闺蜜一致认为开封好吃的美食店（夯到拉）_1_🍿爆米花_来自小红书网页版.jpg",
    "和闺蜜一致认为开封好吃的美食店（夯到拉）_2_🍿爆米花_来自小红书网页版.jpg",
    "和闺蜜一致认为开封好吃的美食店（夯到拉）_3_🍿爆米花_来自小红书网页版.jpg",
    "和闺蜜一致认为开封好吃的美食店（夯到拉）_4_🍿爆米花_来自小红书网页版.jpg",
    "和闺蜜一致认为开封好吃的美食店（夯到拉）_5_🍿爆米花_来自小红书网页版.jpg",
    "和闺蜜一致认为开封好吃的美食店（夯到拉）_6_🍿爆米花_来自小红书网页版.jpg",
    "和闺蜜一致认为开封好吃的美食店（夯到拉）_7_🍿爆米花_来自小红书网页版.jpg",
    "和闺蜜一致认为开封好吃的美食店（夯到拉）_8_🍿爆米花_来自小红书网页版.jpg",
    "和闺蜜一致认为开封好吃的美食店（夯到拉）_9_🍿爆米花_来自小红书网页版.jpg",
]
clip2_names = [
    "clipboard-2026-09-26T13-22-40-753Z-485f27ce.jpg",
    "clipboard-2026-09-26T13-22-40-755Z-b18ef5f5.jpg",
    "clipboard-2026-09-26T13-22-40-757Z-f9120fe0.jpg",
    "clipboard-2026-09-26T13-22-40-759Z-7d037d48.jpg",
    "clipboard-2026-09-26T13-22-40-761Z-8331c566.jpg",
    "clipboard-2026-09-26T13-22-40-763Z-1da9c121.jpg",
    "clipboard-2026-09-26T13-22-40-765Z-560d3724.jpg",
    "clipboard-2026-09-26T13-22-40-768Z-0aae7efa.jpg",
    "clipboard-2026-09-26T13-22-40-769Z-70440a2f.jpg",
    "clipboard-2026-09-26T13-22-40-772Z-4f72590d.jpg",
    "clipboard-2026-09-26T13-22-40-773Z-8b3fecba.jpg",
    "clipboard-2026-09-26T13-22-40-775Z-be92753e.jpg",
    "clipboard-2026-09-26T13-22-40-776Z-83f4fb1a.jpg",
    "clipboard-2026-09-26T13-22-40-779Z-38b9333a.jpg",
    "clipboard-2026-09-26T13-22-40-780Z-71589d1c.jpg",
    "clipboard-2026-09-26T13-22-40-782Z-6bb093d9.jpg",
    "clipboard-2026-09-26T13-22-40-784Z-a27209dc.jpg",
]

seq = []
for n in clip_names: seq.append(os.path.join(CLIP, n))
for n in google_names: seq.append(os.path.join(GOOGLE, n))
for n in clip2_names: seq.append(os.path.join(CLIP, n))

print("total", len(seq))
for i, p in enumerate(seq, 1):
    if not os.path.exists(p):
        print("MISSING", i, p); continue
    ext = os.path.splitext(p)[1]
    dst = os.path.join(SRC, f"{i:02d}{ext}")
    shutil.copy2(p, dst)
    im = Image.open(p).convert("RGB")
    w, h = im.size
    print(f"{i:02d} size={w}x{h}  {os.path.basename(p)[:50]}")
    # 放大版：整图 2 倍（长边上限 2000）
    scale = 2
    z = im.resize((w*scale, h*scale), Image.LANCZOS)
    z.save(os.path.join(ZOOM, f"{i:02d}_full.jpg"), quality=92)
