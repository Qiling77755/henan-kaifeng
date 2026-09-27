# -*- coding: utf-8 -*-
"""运行时探针：验证「选中 / 取消选中」开关闭环。

覆盖的关闭路径：
  1) 清单卡片再点一次
  2) 地图圆点再点一次（用 stroke=#22201d 定位被选中的那个点）
  3) 点击地图空白处
  4) 详情面板 ✕ 按钮
  5) Esc 键（且大图预览优先关闭）
并做回归断言：卡片 217、星标 1、有坐标条目 183、统计栏账目不变。
"""
import os, re, json, subprocess

ROOT = r"E:\children‘s day file\开封美食地图"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

PROBE = r"""
<script>
window.addEventListener('load',function(){
 setTimeout(function(){
  var out=[], fail=0;
  function ok(name,cond,detail){ out.push({t:name,p:!!cond,d:detail}); if(!cond) fail++; }
  function clickAt(node,x,y){
    if(!node) return false;
    if(x==null){ var r=node.getBoundingClientRect(); x=r.left+r.width/2; y=r.top+r.height/2; }
    node.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,cancelable:true,clientX:x,clientY:y,view:window}));
    node.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,clientX:x,clientY:y,view:window}));
    return true;
  }
  function cards(){ return document.querySelectorAll('#list .card'); }
  function cardClick(i){
    var c=cards()[i]; if(!c) return false;
    var r=c.getBoundingClientRect();
    /* 点名称区域（左侧内边距内），避开右侧「复制」按钮 */
    return clickAt(c, r.left+20, r.top+14);
  }
  function st(){
    var d=document.getElementById('detail'), h3=d.querySelector('h3');
    return {
      cur: current? current.id : null,
      name: current? current.n : null,
      h3: h3? h3.textContent.trim() : null,
      close: !!document.getElementById('dclose'),
      active: document.querySelectorAll('#list .card.active').length,
      sel: document.querySelectorAll('#map path.leaflet-interactive[stroke="#22201d"]').length
    };
  }

  /* ---------- T0 基线 ---------- */
  var b=st();
  ok('T0 初始为占位态', b.cur===null && b.close===false && b.active===0 && b.sel===0,
     'h3='+b.h3+' close='+b.close+' active='+b.active+' sel='+b.sel);
  ok('T0 占位文案正确', b.h3==='点选一个地点', 'h3='+b.h3);

  /* ---------- T1/T2 卡片：打开 → 再点关闭 ---------- */
  cardClick(0);
  var a1=st();
  ok('T1 卡片点击=打开', a1.cur!==null && a1.close===true && a1.active===1 && a1.h3===a1.name,
     'cur='+a1.cur+' h3='+a1.h3+' active='+a1.active+' close='+a1.close);
  cardClick(0);
  var a2=st();
  ok('T2 卡片再点=关闭', a2.cur===null && a2.close===false && a2.active===0,
     'cur='+a2.cur+' h3='+a2.h3+' active='+a2.active+' close='+a2.close);

  /* ---------- T3 卡片：点 A 再点 B = 切换（不是关闭） ---------- */
  cardClick(0); cardClick(1);
  var a3=st();
  ok('T3 换一张卡=切换选中', a3.cur!==null && a3.active===1, 'cur='+a3.cur+' active='+a3.active);
  cardClick(1);

  /* ---------- T4/T5 地图圆点：打开 → 再点关闭 ---------- */
  var p0=document.querySelector('#map path.leaflet-interactive');
  clickAt(p0);
  var m1=st();
  ok('T4 圆点点击=打开', m1.cur!==null && m1.close===true && m1.sel===1 && m1.active===1,
     'cur='+m1.cur+' sel='+m1.sel+' active='+m1.active);
  var psel=document.querySelectorAll('#map path.leaflet-interactive[stroke="#22201d"]');
  ok('T4 选中点被高亮重绘', psel.length===1, 'selPaths='+psel.length);
  clickAt(psel[0]);
  var m2=st();
  ok('T5 圆点再点=关闭', m2.cur===null && m2.sel===0 && m2.active===0 && m2.close===false,
     'cur='+m2.cur+' sel='+m2.sel+' active='+m2.active);

  /* ---------- T6 点击地图空白处 ---------- */
  cardClick(0);
  var opened=st().cur!==null;
  var mm=document.getElementById('map'), mr=mm.getBoundingClientRect();
  var bx=mr.left+24, by=mr.bottom-24;
  var tgt=document.elementFromPoint(bx,by);
  ok('T6 定位到地图空白元素', !!tgt, 'tgt='+(tgt? tgt.tagName+'.'+tgt.className : 'null'));
  if(tgt) clickAt(tgt,bx,by);
  var b6=st();
  ok('T6 点空白=关闭详情', opened && b6.cur===null && b6.active===0,
     'opened='+opened+' cur='+b6.cur+' 点击目标='+(tgt? tgt.tagName+'.'+String(tgt.className).slice(0,40) : '-'));

  /* ---------- T7 ✕ 按钮 ---------- */
  cardClick(0);
  var hasBtn=!!document.getElementById('dclose');
  clickAt(document.getElementById('dclose'));
  var b7=st();
  ok('T7 ✕ 按钮=关闭详情', hasBtn && b7.cur===null && b7.close===false, 'hasBtn='+hasBtn+' cur='+b7.cur);

  /* ---------- T8 Esc 关闭详情 ---------- */
  cardClick(0);
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
  var b8=st();
  ok('T8 Esc=关闭详情', b8.cur===null, 'cur='+b8.cur);

  /* ---------- T9 Esc：大图预览优先于详情 ---------- */
  cardClick(0);
  var im=document.querySelector('#detail .shot img');
  var lbOn=false;
  if(im){ clickAt(im); lbOn=document.getElementById('lb').classList.contains('on'); }
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
  var b9=st();
  ok('T9 大图打开时 Esc 先关大图', lbOn===false ? true : (document.getElementById('lb').classList.contains('on')===false),
     '有截图='+!!im+' 点图后大图开='+lbOn+' Esc后大图开='+document.getElementById('lb').classList.contains('on'));
  ok('T9 详情未被误关', b9.cur!==null, 'cur='+b9.cur);
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
  ok('T9 再按 Esc 才关详情', st().cur===null, 'cur='+st().cur);

  /* ---------- T10 ✕ 按钮几何：可见、不越出面板、不压标题 ---------- */
  cardClick(0);
  var dxb=document.getElementById('dclose'), dhp=document.getElementById('detail');
  if(!dxb){ ok('T10 ✕ 按钮存在', false, '未找到 #dclose'); }
  else{
    var dr=dxb.getBoundingClientRect(), pr2=dhp.getBoundingClientRect();
    var h3r=dhp.querySelector('h3').getBoundingClientRect();
    ok('T10 ✕ 可见且尺寸正常', dr.width>16 && dr.height>16,
       'w='+dr.width.toFixed(1)+' h='+dr.height.toFixed(1));
    ok('T10 ✕ 不越出详情面板', dr.right<=pr2.right+1,
       'btn.right='+Math.round(dr.right)+' panel.right='+Math.round(pr2.right));
    ok('T10 ✕ 在视口内', dr.right<=window.innerWidth && dr.left>=0,
       'btn.right='+Math.round(dr.right)+' innerWidth='+window.innerWidth);
    ok('T10 ✕ 不与标题重叠', dr.left>=h3r.right-1,
       'btn.left='+Math.round(dr.left)+' h3.right='+Math.round(h3r.right));
    ok('T10 ✕ 未撑破面板高度', dhp.scrollWidth<=dhp.clientWidth+1,
       'scrollW='+dhp.scrollWidth+' clientW='+dhp.clientWidth);
  }
  cardClick(0);   /* 关掉，回到占位态 */

  /* ---------- T11 回归：数据与图层计数 ---------- */
  var r10=st();
  ok('T11 卡片数=217', cards().length===217, 'cards='+cards().length);
  ok('T11 统计栏一致', document.getElementById('s1').textContent==='217'
     && document.getElementById('s2').textContent==='113'
     && document.getElementById('s5').textContent==='70'
     && document.getElementById('s3').textContent==='34',
     's1='+document.getElementById('s1').textContent+' s2='+document.getElementById('s2').textContent
     +' s5='+document.getElementById('s5').textContent+' s3='+document.getElementById('s3').textContent);
  ok('T11 圆点=182 星标=1', document.querySelectorAll('#map path.leaflet-interactive').length===182
     && document.querySelectorAll('#map .leaflet-marker-icon').length===1,
     'paths='+document.querySelectorAll('#map path.leaflet-interactive').length
     +' stars='+document.querySelectorAll('#map .leaflet-marker-icon').length);
  ok('T11 结束时回到占位态', r10.cur===null && r10.active===0 && r10.close===false,
     'cur='+r10.cur+' active='+r10.active);

  document.title='PROBE'+JSON.stringify({fail:fail,total:out.length,res:out});
 },1800);
});
</script>
"""


def run(w, h):
    src = open(os.path.join(ROOT, "开封美食地图.html"), encoding="utf-8").read()
    tmp = os.path.join(ROOT, "_probe_toggle_tmp.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(src.replace("</body>", PROBE + "</body>"))
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--window-size=%d,%d" % (w, h), "--virtual-time-budget=9000",
           "--dump-dom", "file:///" + tmp.replace("\\", "/")]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"<title>PROBE(.*?)</title>", p.stdout, re.S)
    os.remove(tmp)
    if not m:
        return {"error": "no probe result", "stderr": (p.stderr or "")[-500:]}
    return json.loads(m.group(1))


TOTAL_FAIL = 0
for (w, h) in [(1440, 900), (430, 900)]:
    print("=== viewport %dx%d ===" % (w, h))
    r = run(w, h)
    if "error" in r:
        print("  ERROR:", r)
        TOTAL_FAIL += 1
        continue
    for it in r["res"]:
        print("  [%s] %s%s" % ("PASS" if it["p"] else "FAIL", it["t"],
                               "" if it["p"] else "\n        → " + it["d"]))
    print("  -- 失败 %d / 共 %d --" % (r["fail"], r["total"]))
    TOTAL_FAIL += r["fail"]
print()
print("TOTAL FAIL =", TOTAL_FAIL)
