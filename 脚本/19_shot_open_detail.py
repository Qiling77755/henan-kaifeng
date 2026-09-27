# -*- coding: utf-8 -*-
"""视觉确认：自动打开第一条详情，截图检查 ✕ 关闭按钮的排版（1440 / 430 两档）。"""
import os, subprocess

ROOT = r"E:\children‘s day file\开封美食地图"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

PROBE = """
<script>
window.addEventListener('load',function(){setTimeout(function(){
 var c=document.querySelectorAll('#list .card')[0];var r=c.getBoundingClientRect();
 var x=r.left+20, y=r.top+14;
 c.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,clientX:x,clientY:y}));
 c.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,clientX:x,clientY:y,view:window}));
},1500);});
</script>
"""

src = open(os.path.join(ROOT, "开封美食地图.html"), encoding="utf-8").read()
tmp = os.path.join(ROOT, "_shot_tmp.html")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(src.replace("</body>", PROBE + "</body>"))

url = "file:///" + tmp.replace("\\", "/")
for w, h, name in [(1440, 900, "_shot_open_1440.png"), (430, 900, "_shot_open_430.png")]:
    out = os.path.join(ROOT, name)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--window-size=%d,%d" % (w, h), "--virtual-time-budget=7000",
                    "--screenshot=" + out, url], capture_output=True)
    print(name, "->", os.path.exists(out), os.path.getsize(out) if os.path.exists(out) else 0)

os.remove(tmp)
print("临时文件已清理")
