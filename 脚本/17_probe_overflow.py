# -*- coding: utf-8 -*-
"""横向溢出对比：新 HTML（含复制按钮）vs 备份 HTML（无按钮），定位是否有元素被撑出视口。"""
import os, re, json, subprocess

ROOT = r"E:\children‘s day file\开封美食地图"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

PROBE = """
<script>
window.addEventListener('load',function(){
 setTimeout(function(){
  var vw=window.innerWidth;
  var over=[];
  document.querySelectorAll('body *').forEach(function(n){
    var r=n.getBoundingClientRect();
    if(r.width>0 && r.right>vw+1 && n.offsetParent!==null){
      over.push((n.className&&typeof n.className==='string'?n.className.split(' ')[0]:n.tagName)+'@'+Math.round(r.right));
    }
  });
  var de=document.documentElement;
  document.title='PROBE'+JSON.stringify({
    innerWidth:vw,
    scrollWidth:de.scrollWidth,
    horizOverflow:de.scrollWidth>vw+1,
    overCount:over.length,
    overFirst:over.slice(0,8)
  });
 },1500);
});
</script>
"""

def probe(path, w, h):
    src = open(path, encoding="utf-8").read()
    tmp = os.path.join(ROOT, "_ovf_tmp.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(src.replace("</body>", PROBE + "</body>"))
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--window-size=%d,%d" % (w, h), "--virtual-time-budget=8000",
           "--dump-dom", "file:///" + tmp.replace("\\", "/")]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    os.remove(tmp)
    m = re.search(r"<title>PROBE(.*?)</title>", r.stdout, re.S)
    return json.loads(m.group(1)) if m else {"error": (r.stderr or "")[-200:]}

NEW = os.path.join(ROOT, "开封美食地图.html")
OLD = os.path.join(ROOT, "开封美食地图.before_copybtn.bak.html")
for w in (430, 700, 1000, 1440):
    a = probe(NEW, w, 900)
    b = probe(OLD, w, 900)
    print("=== window-size %d ===" % w)
    print("  新版:", json.dumps(a, ensure_ascii=False))
    print("  旧版:", json.dumps(b, ensure_ascii=False))
