# -*- coding: utf-8 -*-
"""《汴京食帖》视觉与交互验证：无头 Chrome 截图 + 控制台错误捕获。

用法：python 22_probe_shitie.py [stage]
  stage=init    仅看序幕
  stage=open    开卷后的全幅墨图
  stage=note    点开一条帖页
  stage=bag     行囊面板（拾 4 条后）
  stage=no      无处安放面板
  stage=gate    墨色闸门收到实墨
  stage=deep    拉近到单点
  stage=mobile  520x900 窄屏（见下）
  stage=scope   选中市井「鼓楼」（回读范围框与视野宽度）
  stage=scope2  选中品类「甜」
  stage=snd     配乐信号链状态
  stage=tl      时间线：flyTo 补间是否推进
  stage=tl2     rAF 是否推进
  stage=hotel   住处（原点）状态 + 真实命中测试（点哪家是哪家）
  stage=labels  拉近后点名层是否互压
  stage=hotelnote 点开住处的帖页

注入的 harness 会把 requestAnimationFrame 换成 16ms 定时器：无头 Chrome
不合成帧，原生 rAF 几乎不触发（实测 620ms 只跑 1 帧），补间与 rAF 节流的
重绘会整块僵住、验证失真。只影响验证环境，页面代码不动。
"""
import os, sys, subprocess, json, shutil

ROOT = r"E:\children‘s day file\开封美食地图"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SRC = os.path.join(ROOT, "汴京食帖.html")
TMP = os.path.join(ROOT, "_probe_shitie.html")

PROBES = {
 "open": "try{localStorage.setItem('shitie.seen','1');}catch(e){}S.openScroll();",
 # 帖页：四枚按钮（图上寻它／拾入行囊／抄店名／抄坐标）必须在行内排得下、且不被挤出视口。
 # 桌面与窄屏（mobile 档）各跑一次，用同一段自报几何。
 "note": "S.openScroll();setTimeout(function(){"
         "S.openNote(S.DATA.filter(function(x){return x.ar==='鼓楼书店街';})[0]);"
         "setTimeout(function(){var r=document.querySelector('#note .nf').getBoundingClientRect();"
         "window.__DIAG={nf:[Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height)],"
         "btns:document.querySelectorAll('#note .nf .k').length,"
         "vw:window.innerWidth,vh:window.innerHeight,"
         "noteH:Math.round(document.querySelector('#note').getBoundingClientRect().height),"
         "sheetH:Math.round(document.querySelector('#sheet').getBoundingClientRect().height),"
         "btnTxt:[].map.call(document.querySelectorAll('#note .nf .k'),function(b){return b.textContent.trim();})};"
         "},140);},400);",
 "bag":  "S.openScroll();setTimeout(function(){[30,33,47,136].forEach(function(i){"
         "S.togglePick(S.DATA.filter(function(x){return x.id===i;})[0]);});"
         "document.querySelector('#btnBag').click();},400);",
 "no":   "S.openScroll();setTimeout(function(){document.querySelector('#btnNo').click();},400);",
 "gate": "S.openScroll();setTimeout(function(){S.setInk(1);},400);",
 # 必须先屏蔽 firstLook：它会自己开一帖并飞过去，把这里设好的视野整块覆盖掉
 # （此前一直如此，所谓「拉近到单点」实际是 11km 的全城视野）。
 "deep": "try{localStorage.setItem('shitie.seen','1');}catch(e){}S.openScroll();"
         "setTimeout(function(){var d=S.PTS.filter(function(x){return x._ink===1;})[0];"
         "S.openNote(d);S.VB.w=0.9;S.VB.cx=d._x;S.VB.cy=d._y;S.apply();},500);",
 # 选中市井 / 品类：视野应落到该片范围上，并画出朱砂范围框。
 # flyTo 补间 560ms，DIAG 必须等动画落定再读（harness 的窗口只有 650ms）。
 "scope":  "try{localStorage.setItem('shitie.seen','1');}catch(e){}S.openScroll();"
           "setTimeout(function(){"
           "var el=document.querySelector('#rail .rl[data-k=\"gl\"]');if(el)el.click();},30);"
           "setTimeout(function(){window.__DIAG=DIAG();},600);",
 "scope2": "try{localStorage.setItem('shitie.seen','1');}catch(e){}S.openScroll();"
           "setTimeout(function(){"
           "var el=document.querySelector('#cats .chip[data-k=\"甜\"]');if(el)el.click();},30);"
           "setTimeout(function(){window.__DIAG=DIAG();},600);",
 # 时间线：确认 flyTo 补间究竟跑没跑、补间期间 VB 怎么走
 "tl":     "try{localStorage.setItem('shitie.seen','1');}catch(e){}"
           "window.__TL=[];S.openScroll();"
           "setTimeout(function(){var el=document.querySelector('#rail .rl[data-k=\"gl\"]');"
           "window.__TL.push('find:'+(el?'ok':'null'));if(el){el.click();window.__TL.push('clicked');}},30);"
           "[100,250,400,550].forEach(function(t){setTimeout(function(){"
           "window.__TL.push(t+':w='+S.VB.w.toFixed(2)+' cx='+S.VB.cx.toFixed(2));},t);});"
           "setTimeout(function(){window.__DIAG={tl:window.__TL};},620);",
 # rAF 是否在 headless 里推进：直接数帧
 "tl2":    "window.__N=0;(function loop(){window.__N++;if(window.__N<999)requestAnimationFrame(loop);})();"
           "setTimeout(function(){window.__DIAG={raf:window.__N};},620);",
 # 点开住处的帖页：坐标、地址、「此处即住处」、信度文案都要经得起看
 "hotelnote": "try{localStorage.setItem('shitie.seen','1');}catch(e){}S.openScroll();"
              "setTimeout(function(){var h=null;S.PTS.forEach(function(d){if(d.star)h=d;});"
              "S.openNote(h);S.VB.w=1.6;S.VB.cx=h._x;S.VB.cy=h._y;S.apply();},500);",
 # 「图上寻它」：点一枚墨点只该开帖页（视野原地不动、不连线），
 # 朱砂直线与视野由帖页里那个按钮触发。这一档把两个状态都截出来。
 "locate": "try{localStorage.setItem('shitie.seen','1');}catch(e){}S.openScroll();"
           "setTimeout(function(){var d=null;S.PTS.forEach(function(x){"
           "if(!d&&!x._hood&&x._ink===1&&!x.star&&x._x>6&&x._x<8)d=x;});"
           "var r=document.querySelector('#ink').getBoundingClientRect(),"
           "vb=document.querySelector('#ink').getAttribute('viewBox').split(' ').map(Number);"
           "var cx=r.left+(d._x-vb[0])/vb[2]*r.width, cy=r.top+(d._y-vb[1])/vb[3]*r.height;"
           "var t=document.elementFromPoint(Math.round(cx),Math.round(cy));"
           "if(t)t.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,"
           "clientX:Math.round(cx),clientY:Math.round(cy),view:window}));"
           "window.__DIAG={sel:S.st.sel?S.st.sel.id:null,locate:!!S.st.locate,"
           "lines:document.querySelectorAll('#gRoute line').length,vbW:+S.VB.w.toFixed(3),"
           "btn:document.querySelector('#nLocate').textContent.trim(),"
           "btns:document.querySelectorAll('#note .nf .k').length};"
           "setTimeout(function(){document.querySelector('#nLocate').click();"
           "window.__DIAG.after={locate:!!S.st.locate,"
           "lines:document.querySelectorAll('#gRoute line').length,"
           "btn:document.querySelector('#nLocate').textContent.trim()};},1500);},600);",
 # 住处与点选：两处都曾是真实缺陷 —— 住处被降级成「未标」而在全景下隐形；
 # 分级显示把 pointer-events 一并关掉，全景下点淡影毫无反应。
 # 用真实命中测试（在目标正中心派发 click）判定，不靠肉眼。
 "hotel":  "try{localStorage.setItem('shitie.seen','1');}catch(e){}S.openScroll();"
           "setTimeout(function(){window.__DIAG=HIT();},320);",
 # 点名层此前因「表现属性优先级低于内联」而从未渲染出一个字，须防其复现与互压
 "labels": "try{localStorage.setItem('shitie.seen','1');}catch(e){}S.openScroll();"
           "setTimeout(function(){S.VB.w=3.2;S.VB.cx=6.4;S.VB.cy=4.6;S.apply();},200);"
           "setTimeout(function(){window.__DIAG=LBLS();},440);",
 # 配乐：信号链是否真的立起来（headless 无声，只看状态与不报错）
 "snd":    "try{localStorage.setItem('shitie.seen','1');}catch(e){}S.openScroll();"
           "setTimeout(function(){S.setSound(true);"
           "S.voiceOf(S.PTS[0]);S.voiceOf(S.PTS[40]);S.voiceOf(S.PTS[120]);"
           "S.chime(523.25,0.2,3.0);},200);"
           "setTimeout(function(){window.__DIAG={snd:S.sndState()};},600);",
}

# 回读选中状态：视野宽度 + 范围框几何 + 框上题名
DIAG_JS = """
function DIAG(){
  var S=window.__shitie, gs=document.querySelector('#gScope');
  var r=gs.querySelector('rect'), t=gs.querySelector('text');
  return {
    area:S.st.area, cat:S.st.cat, vbW:+S.VB.w.toFixed(3), wOut:+S.VB.wOut.toFixed(3),
    on:gs.classList.contains('on'),
    rect:r?[+r.getAttribute('x'),+r.getAttribute('y'),
            +r.getAttribute('width'),+r.getAttribute('height')].map(function(v){return +v.toFixed(3);}):null,
    lbl:t?t.textContent:''
  };
}

/* 真实命中测试：在目标正中心派发 click，看开出来的是不是它。
   此前点选靠 e.target，命中圈在密区互相压盖，点甲店开出乙店的帖。 */
function HIT(){
  var S=window.__shitie, out={}, h=null;
  S.PTS.forEach(function(d){ if(d.star) h=d; });
  var hr=h._el.getBoundingClientRect();
  out.hotel={ink:h._ink, op:getComputedStyle(h._el).opacity,
    pe:h._el.style.pointerEvents,
    pad:!!document.querySelector('#gDot circle.pad'),
    legend:!!document.querySelector('#inkcol .ik.origin'),
    lbl:h._lbl.textContent,
    lblShown:getComputedStyle(h._lbl).display!=='none',
    cx:Math.round(hr.left+hr.width/2), cy:Math.round(hr.top+hr.height/2)};
  var cl=0;
  S.PTS.forEach(function(d){ if(d._hit&&d._hit.style.pointerEvents==='all') cl++; });
  out.clickable=cl; out.pts=S.PTS.length;
  var C={cx:S.VB.cx, cy:S.VB.cy, w:S.VB.w};
  function home(){ S.closeNote(); S.VB.cx=C.cx; S.VB.cy=C.cy; S.VB.w=C.w; S.apply(); }
  function tap(x,y){
    var t=document.elementFromPoint(Math.round(x),Math.round(y));
    if(t) t.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,
      clientX:Math.round(x),clientY:Math.round(y),view:window}));
    return S.st.sel?S.st.sel.id:null;
  }
  home();
  out.tapHotel={want:70, got:tap(out.hotel.cx,out.hotel.cy)};
  home();
  var d3=null;
  S.PTS.forEach(function(x){ if(!d3&&!x._hood&&x._ink===3&&!x.star) d3=x; });
  var r3=d3._el.getBoundingClientRect();
  out.tapUnmarked={want:d3.id, got:tap(r3.left+r3.width/2, r3.top+r3.height/2)};
  /* 空白处：帖页应被收起，而不是毫无动静 */
  home(); S.openNote(h);
  var R=document.querySelector('#stage').getBoundingClientRect(), bx=null, by=null;
  for(var y=R.top+14;y<R.bottom-14&&bx===null;y+=19)
    for(var x=R.left+14;x<R.right-14;x+=19){
      if(S.pickAt(x,y)) continue;
      var el=document.elementFromPoint(x,y);
      if(el&&el.tagName==='svg'){ bx=x; by=y; break; }
    }
  var before=!document.querySelector('#note').hidden;
  if(bx!==null) tap(bx,by);
  out.blank={found:bx!==null, noteBefore:before,
    noteAfter:!document.querySelector('#note').hidden};
  return out;
}

/* 可见标签两两不得相交 —— 避让是几何问题，须用矩形实测，不能凭肉眼判读 */
function LBLS(){
  var S=window.__shitie, L=[], ov=[];
  document.querySelectorAll('#stage text').forEach(function(t){
    if(getComputedStyle(t).display==='none') return;
    var r=t.getBoundingClientRect();
    if(r.width<0.5||r.height<0.5) return;
    L.push({t:t.textContent.trim(),x:r.left,y:r.top,w:r.width,h:r.height});
  });
  for(var i=0;i<L.length;i++) for(var j=i+1;j<L.length;j++){
    var a=L[i],b=L[j];
    var ix=Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x);
    var iy=Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y);
    if(ix>0.5&&iy>0.5) ov.push(a.t+'／'+b.t);
  }
  var h=null; S.PTS.forEach(function(d){ if(d.star) h=d; });
  return {vbW:+S.VB.w.toFixed(3), shown:L.length, overlap:ov.length,
    pairs:ov.slice(0,6), hotelLblShown:getComputedStyle(h._lbl).display!=='none'};
}
"""

HARNESS = """
<script>
/* 无头 Chrome 不合成帧，requestAnimationFrame 几乎不触发（实测 620ms 只跑 1 帧），
   补间动画与 rAF 节流的重绘会整块僵住。换成 16ms 定时器，让虚拟时间下动画仍能推进。
   只影响验证环境，页面代码不动。 */
(function(){
  window.requestAnimationFrame=function(cb){return setTimeout(function(){cb(performance.now());},16);};
  window.cancelAnimationFrame=function(id){clearTimeout(id);};
})();
window.__ERR=[];
window.addEventListener('error',function(e){window.__ERR.push('ERR '+e.message+' @line'+e.lineno);});
window.addEventListener('unhandledrejection',function(e){window.__ERR.push('REJ '+e.reason);});
(function(){var w=console.error;console.error=function(){window.__ERR.push('CE '+[].join.call(arguments,' '));w.apply(console,arguments);};})();
window.addEventListener('load',function(){setTimeout(function(){
  var S=window.__shitie||{};
  try{ %s }catch(e){ window.__ERR.push('THROW '+e.message); }
  setTimeout(function(){
    var box=document.createElement('div');
    box.id='__err';
    box.style.cssText='position:fixed;left:0;top:0;z-index:9999;font:12px monospace;color:#b03a2e;background:#fff;padding:4px 8px;max-width:100%%;white-space:pre-wrap';
    box.textContent='VW='+window.innerWidth+'x'+window.innerHeight+' ｜ '+
      (window.__DIAG?('DIAG '+JSON.stringify(window.__DIAG)+' ｜ '):'')+
      (window.__ERR.length?('JS 错误 '+window.__ERR.length+' 条：\\n'+window.__ERR.join('\\n')):'JS 错误 0 条');
    document.body.appendChild(box);
    window.__DONE=1;
  },650);
},600);});
</script>
"""


def build(stage, w, h, out, extra=""):
    src = open(SRC, encoding="utf-8").read()
    body = (DIAG_JS + PROBES.get(stage, "openScroll();")
            if stage != "init" else "/* 序幕保持 */") + extra
    with open(TMP, "w", encoding="utf-8") as f:
        f.write(src.replace("</body>", HARNESS % body + "</body>"))
    url = "file:///" + TMP.replace("\\", "/")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
           "--autoplay-policy=no-user-gesture-required",
           "--window-size=%d,%d" % (w, h), "--virtual-time-budget=9000",
           "--enable-logging=stderr", "--v=0",
           "--screenshot=" + out, url]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    # 从 DOM dump 里读错误框文本
    # 两次调用必须给同一组参数：是否带 --hide-scrollbars 会改变 innerWidth，
    # 两次渲染的 viewport 若不同，回读的坐标与截图就对不上。
    dump = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                           "--hide-scrollbars",
                           "--window-size=%d,%d" % (w, h), "--virtual-time-budget=9000",
                           "--dump-dom", url], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    err = "?"
    if 'id="__err"' in dump.stdout:
        seg = dump.stdout.split('id="__err"', 1)[1]
        seg = seg.split(">", 1)[1].split("</div>")[0]
        err = seg.strip()
    vw = 0
    if err.startswith("VW="):
        try: vw = int(err.split("=", 1)[1].split("x")[0])
        except Exception: vw = 0
    # 截图宽 < viewport ⇒ 右侧内容被静默裁掉（Chrome 窗口最小宽约 512）
    # 截图宽 > viewport ⇒ 仅右侧多出留白，无害
    warn = ""
    if vw and w < vw:
        warn = "  ⚠ 截图 %d < viewport %d，右侧 %dpx 内容被裁" % (w, vw, vw - w)
    elif vw and w > vw:
        warn = "  （截图 %d > viewport %d，右侧 %dpx 留白，无害）" % (w, vw, w - vw)
    print("[%s %dx%d] -> %s (%d bytes)%s\n     %s" % (
        stage, w, h, os.path.basename(out), os.path.getsize(out) if os.path.exists(out) else 0,
        warn, err.replace("\n", "\n     ")))
    for line in r.stderr.splitlines():
        if "SEVERE" in line or "ERROR:" in line:
            print("     CHROME:", line.strip()[:200])


if __name__ == "__main__":
    stages = sys.argv[1:] or ["open"]
    for s in stages:
        if s == "mobile":
            # Chrome 的 viewport 有最小宽度（约 500px），--window-size=430 时
            # innerWidth 仍为 512，而截图只有 430px 宽 → 右侧被静默裁掉、验证失真。
            # 故窄屏改用 520，并以截图宽 == innerWidth 作为前提。
            build("note", 520, 900, os.path.join(ROOT, "_probe_mobile.png"))
        else:
            build(s, 1600, 900, os.path.join(ROOT, "_probe_%s.png" % s))
    if os.path.exists(TMP):
        os.remove(TMP)
