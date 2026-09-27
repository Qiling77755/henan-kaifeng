# -*- coding: utf-8 -*-
"""运行时探针：在真实浏览器 DOM 中确认说明块位于清单末尾，且滚到清单底部可见。"""
import os, re, json, subprocess, sys

ROOT = r"E:\children‘s day file\开封美食地图"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

PROBE = """
<script>
window.addEventListener('load',function(){
 setTimeout(function(){
  var pane=document.getElementById('pane');
  var list=document.getElementById('list');
  var notes=[].slice.call(pane.children).filter(function(n){return n.className==='notes';});
  var tail=notes[notes.length-1];
  var det=tail.querySelector('details.note');
  var idx=[].map.call(pane.children,function(n){return n.id?('#'+n.id):(n.className||n.tagName);});
  var pr=pane.getBoundingClientRect();
  var beforeTop=Math.round(det.getBoundingClientRect().top-pr.top);
  pane.scrollTop=pane.scrollHeight;
  var tr=det.getBoundingClientRect();
  var r={
    cards:list.children.length,
    notesCount:notes.length,
    paneChildren:idx,
    tailSummary:det.querySelector('summary').textContent.trim(),
    tailTopBeforeScroll:beforeTop,
    tailTopAfterScrollToEnd:Math.round(tr.top-pr.top),
    tailVisibleAfterScrollToEnd:(tr.top>=pr.top-2 && tr.bottom<=pr.bottom+2),
    paneScrollable:pane.scrollHeight>pane.clientHeight+2,
    paneScrollTop:Math.round(pane.scrollTop),
    paneScrollHeight:pane.scrollHeight,
    paneClientHeight:pane.clientHeight
  };
  document.title='PROBE'+JSON.stringify(r);
 },1600);
});
</script>
"""

def run(w, h):
    src = open(os.path.join(ROOT, "开封美食地图.html"), encoding="utf-8").read()
    tmp = os.path.join(ROOT, "_probe_tmp.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(src.replace("</body>", PROBE + "</body>"))
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--window-size=%d,%d" % (w, h), "--virtual-time-budget=8000",
           "--dump-dom", "file:///" + tmp.replace("\\", "/")]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"<title>PROBE(.*?)</title>", p.stdout, re.S)
    os.remove(tmp)
    return json.loads(m.group(1)) if m else {"error": "no probe result", "stderr": (p.stderr or "")[-400:]}

for (w, h) in [(1440, 900), (430, 900)]:
    print("=== viewport %dx%d ===" % (w, h))
    print(json.dumps(run(w, h), ensure_ascii=False, indent=1))
