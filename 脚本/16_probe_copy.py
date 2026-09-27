# -*- coding: utf-8 -*-
"""校验「一键复制」：mock 隔离两条分支（同步成功 / 失败兜底），不依赖 headless 剪贴板行为。"""
import os, re, json, subprocess

ROOT = r"E:\children‘s day file\开封美食地图"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
NODE   = r"C:\Users\17225\.workbuddy\binaries\node\versions\22.12.0\node.exe"
HTML   = os.path.join(ROOT, "开封美食地图.html")

src = open(HTML, encoding="utf-8").read()

# ---- 1. 内嵌 JS 语法检查 ----
blocks = re.findall(r"<script>(.*?)</script>", src, re.S)
tmp_js = os.path.join(ROOT, "_probe_tmp.js")
with open(tmp_js, "w", encoding="utf-8") as f:
    f.write(blocks[-1])
p = subprocess.run([NODE, "--check", tmp_js], capture_output=True, text=True, encoding="utf-8", errors="replace")
print("[1] 内嵌 JS 语法:", "OK" if p.returncode == 0 else "FAIL\n" + (p.stderr or "")[:400])
os.remove(tmp_js)

# ---- 2. 运行时探针 ----
PROBE = """
<script>
function mockClip(fn){
  try{ Object.defineProperty(navigator,'clipboard',{value:{writeText:fn},configurable:true}); }catch(e){}
}
window.addEventListener('load',function(){
 setTimeout(function(){
  var out={};
  out.cards=document.querySelectorAll('#list .card').length;
  out.cpPerCard=document.querySelectorAll('#list .card .cp').length;
  out.cp2BeforeSelect=document.querySelectorAll('#detail .cp2').length;

  /* 分支 A：模拟「同步复制成功」（真实浏览器中 execCommand 在用户手势内即返回 true） */
  document.execCommand=function(){ return true; };
  mockClip(function(){ return Promise.resolve(); });

  var card=document.querySelector('#list .card');
  card.querySelector('.cp').click();
  out.A_activeAfterCopyClick=document.querySelectorAll('#list .card.active').length;

  setTimeout(function(){
    out.A_toastVisible=!!(document.getElementById('toast')&&document.getElementById('toast').classList.contains('on'));
    out.A_toastTitle=((document.querySelector('#toast .tt span')||{}).textContent||'(none)');
    out.A_toastBody=((document.querySelector('#toast .tb')||{}).textContent||'').slice(0,40);
    out.A_leakedTa=document.querySelectorAll('textarea').length;

    /* 分支 B：模拟「同步复制失败 + Clipboard API 拒绝」 */
    document.execCommand=function(){ return false; };
    mockClip(function(){ return Promise.reject(new Error('denied')); });

    card.click();
    out.activeAfterCardClick=document.querySelectorAll('#list .card.active').length;
    out.activeId=document.querySelector('#list .card.active').dataset.id;
    out.detailHasCps=document.querySelectorAll('#detail .cp2').length;
    out.detailName=(document.querySelector('#detail h3')||{}).textContent;
    var b2=document.querySelector('#detail .cp2[data-kind="full"]');
    if(b2) b2.click();

    setTimeout(function(){
      out.B_toastTitle=((document.querySelector('#toast .tt span')||{}).textContent||'(none)');
      out.B_toastBody=((document.querySelector('#toast .tb')||{}).textContent||'').slice(0,60);
      out.B_leakedTa=document.querySelectorAll('textarea').length;

      /* 拖选保护：mousedown 与 click 位移 80px → 不应切换选中 */
      var card2=document.querySelectorAll('#list .card')[1];
      card2.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,clientX:100,clientY:100}));
      card2.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:180,clientY:120}));
      out.activeAfterDragSelect=document.querySelectorAll('#list .card.active').length;
      out.activeIdAfterDrag=document.querySelector('#list .card.active').dataset.id;

      document.title='PROBE'+JSON.stringify(out);
    },300);
  },300);
 },1600);
});
</script>
"""

tmp_html = os.path.join(ROOT, "_probe_tmp.html")
with open(tmp_html, "w", encoding="utf-8") as f:
    f.write(src.replace("</body>", PROBE + "</body>"))
cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--window-size=1440,900",
       "--virtual-time-budget=9000", "--dump-dom", "file:///" + tmp_html.replace("\\", "/")]
r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
os.remove(tmp_html)
m = re.search(r"<title>PROBE(.*?)</title>", r.stdout, re.S)
res = json.loads(m.group(1)) if m else {"error": "no probe", "stderr": (r.stderr or "")[-300:]}
print("[2] 运行时探针:")
print(json.dumps(res, ensure_ascii=False, indent=1))

# ---- 3. 断言 ----
ok = True
def chk(name, cond, extra=""):
    global ok
    print(("  OK   " if cond else "  FAIL ") + name + ("" if cond else "  " + str(extra)))
    ok &= bool(cond)

if "error" not in res:
    chk("卡片数 = 217", res["cards"] == 217, res["cards"])
    chk("每张卡片均有复制按钮 (217)", res["cpPerCard"] == 217, res["cpPerCard"])
    chk("[A] 点卡片「复制」不触发卡片选中", res["A_activeAfterCopyClick"] == 0, res["A_activeAfterCopyClick"])
    chk("[A] 同步成功 → 提示「复制成功」", res["A_toastVisible"] and res["A_toastTitle"] == "复制成功", res["A_toastTitle"])
    chk("[A] 提示含店名", "清明上河园" in res["A_toastBody"], res["A_toastBody"])
    chk("[A] 无残留临时 textarea", res["A_leakedTa"] == 0, res["A_leakedTa"])
    chk("正常点卡片可选中 (1)", res["activeAfterCardClick"] == 1, res["activeAfterCardClick"])
    chk("详情面板有 2 个复制按钮", res["detailHasCps"] == 2, res["detailHasCps"])
    chk("[B] 全部失败 → 提示「复制失败」+ 手动兜底指引", res["B_toastTitle"] == "复制失败" and "Ctrl + C" in res["B_toastBody"], (res["B_toastTitle"], res["B_toastBody"]))
    chk("[B] 无残留临时 textarea", res["B_leakedTa"] == 0, res["B_leakedTa"])
    chk("拖选(位移80px)不触发选中", res["activeAfterDragSelect"] == 1 and res["activeIdAfterDrag"] == res["activeId"], res)
else:
    ok = False

print("\nRESULT:", "PASS" if ok else "FAIL")
