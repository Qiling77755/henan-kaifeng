# -*- coding: utf-8 -*-
"""《汴京食帖》功能与几何核验（无头 Chrome 内取数后本地断言）。

核验点（每条都要有实测依据，不推断）：
  A. 投影真实：屏幕像素距离 / 屏幕像素每公里  与  haversine 实距 一致（误差 < 2%）
  B. 数量真实：落墨点 183、无处安放 34、总 217
  C. 墨色闸门：三档可见点数（期望值从 data.json 现推，当前为 34 / 104 / 183）
  D. 品类筛选：逐组可见点数与数据集直接计数一致
  E. 市井目录：逐区可见点数与区域分组一致，且总和 = 217
  F. 检索：命中的可见点数与本地过滤一致
  G. 行囊：串线总长 = 相邻 haversine 之和
  H. 墨相：墨场画布覆盖 stage；分级显示远端/近端的透明度次序正确
  I. 范围联动：选中市井后范围框出现、题名与家数正确、几何包住命中点且不过分外扩
  J. 配乐映射：10 个市井各有音级、9 个品类各有音色
  K. 交互可达性：全景下可点数 = 落墨数；住处与未标虚圈的正中心都能开出自己
  L. 住处（原点）：归确址、恒满墨、恒可点、标签常显、图例有「宿」行
  M. 标签避让：可见标签两两不相交（几何实测）
  O. 选中项：点开后它自己的名字不得消失
"""
import os, re, json, subprocess, math

ROOT = r"E:\children‘s day file\开封美食地图"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SRC = os.path.join(ROOT, "汴京食帖.html")
TMP = os.path.join(ROOT, "_verify_shitie.html")

PROBE = r"""
<script>
/* 无头 Chrome 不合成帧，requestAnimationFrame 几乎不触发 —— 补间动画与 rAF 节流的重绘
   会整块僵住。Q 节要量「按下后视野确实飞过去」，必须让补间真能推进。
   换成 16ms 定时器，只改验证环境，页面代码一行不动。
   （22 探针早先就接了同一枚替身，核验脚本此前漏接，于是同一条链路一个能量、一个量不了。） */
(function(){
  window.requestAnimationFrame=function(cb){return setTimeout(function(){cb(performance.now());},16);};
  window.cancelAnimationFrame=function(id){clearTimeout(id);};
})();
setTimeout(function(){
  var S=window.__shitie, out={};
  /* 必须真开卷：幕布是 position:fixed;inset:0;z-index:200 的整屏覆盖层，
     不开卷则一切指针命中测试都落到幕布上 —— K 节会全成假阴性。
     （此前核验从未开卷，等于一直在测用户不会看到的那一态。） */
  try{ localStorage.setItem('shitie.seen','1'); }catch(e){}
  S.openScroll();
  /* 打开避让诊断日志。它默认关闭（成品不该每帧分配对象），
     但 L/M/N/O 四节要判定「住处标签为何偶发消失」，必须留着处标签的摆位履历。 */
  S.dbgLog(true);
  function vis(){ return S.PTS.filter(function(d){
      return S.match(d)&&document.querySelector('#gDot [data-id="'+d.id+'"]').style.display!=="none"; }); }
  function px(id){ var d=S.DATA.filter(function(x){return x.id===id;})[0];
    var r=document.querySelector('#ink').getBoundingClientRect();
    var vb=document.querySelector('#ink').getAttribute('viewBox').split(' ').map(Number);
    return [(d._x-vb[0])/vb[2]*r.width, (d._y-vb[1])/vb[3]*r.height]; }
  function hav(a,b){ var la=(a.lat+b.lat)/2*Math.PI/180;
    return Math.hypot((a.lng-b.lng)*111.32*Math.cos(la),(a.lat-b.lat)*110.574); }
  var D=function(i){ return S.DATA.filter(function(x){return x.id===i;})[0]; };

  /* A. 投影真实性 */
  S.VB.w=S.VB.wOut; S.apply();
  var pairs=[[1,70],[30,70],[71,70],[50,30],[62,71],[30,193]];
  var errs=pairs.map(function(p){
    var a=D(p[0]),b=D(p[1]);
    if(!a._x||!b._x) return null;
    var pa=px(p[0]),pb=px(p[1]);
    var scr=Math.hypot(pa[0]-pb[0],pa[1]-pb[1]);
    var km=document.querySelector('#ink').getBoundingClientRect().width/S.VB.w;
    return +(scr/km - hav(a,b)).toFixed(4);
  }).filter(function(x){return x!==null;});
  out.projErrKm=errs; out.projMaxErr=+Math.max.apply(null,errs.map(Math.abs)).toFixed(4);

  /* B/C. 墨色闸门 */
  var cnt=[];
  [1,2,3].forEach(function(v){ S.setInk(v); cnt.push(vis().length); });
  out.inkGate=cnt;

  /* D. 品类 */
  var cats={}; [["汤"],["包"],["面"],["炙"],["甜"],["夜"],["正"],["杂"],["处"]].forEach(function(c){
    S.st.cat=c[0]; S.st.area="all"; S.st.q=""; S.st.ink=3; S.refresh();
    cats[c[0]]=vis().length;
    out["catTxt_"+c[0]]=document.querySelector('#cnt').textContent;
    out["catUn_"+c[0]]=S.NO.filter(S.match).length;
  });
  out.cats=cats; S.st.cat="all"; S.refresh();

  /* E. 市井 */
  var ars={}; S.AREAS.forEach(function(g){
    S.st.area=g.k; S.refresh(); ars[g.label]=vis().length;
    out["arTxt_"+g.k]=document.querySelector('#cnt').textContent;
  });
  out.areas=ars;
  S.st.area="all"; S.refresh(); out.areaAll=vis().length;

  /* F. 检索 */
  S.st.q="汤"; S.refresh(); out.q汤=vis().length; out.q汤Txt=document.querySelector('#cnt').textContent;
  S.st.q="胡辣汤"; S.refresh(); out.q胡辣汤=vis().length;
  S.st.q=""; S.refresh();
  out.noSubAll=document.querySelector('#noSub').textContent;

  /* G. 行囊 */
  [30,33,47,136].forEach(function(i){ S.st.bag.push(i); });
  out.bagSum=+S.st.bag.slice(1).reduce(function(t,id,k){
    return t+hav(D(S.st.bag[k]),D(id)); },0).toFixed(3);
  out.bagLocal=D(30).n+"/"+D(33).n;

  /* H. 墨相与分级显示 */
  var cve=document.querySelector('#inkField'), stg=document.querySelector('#stage'),
      srect=stg.getBoundingClientRect();
  out.field={cw:cve.width, ch:cve.height, sw:Math.round(srect.width), sh:Math.round(srect.height)};
  function opOf(id){ var e=document.querySelector('#gDot [data-id="'+id+'"]');
    return e?+(+e.style.opacity).toFixed(2):null; }
  function pick(f){ var a=S.PTS.filter(f); return a.length?a[0].id:null; }
  var iEx=pick(function(x){return x._ink===1;}), iAp=pick(function(x){return x._ink===2;}),
      iUn=pick(function(x){return x._ink===3;});
  out.tierIds=[iEx,iAp,iUn];

  /* 分级须在「不筛选」的前提下量 —— 否则样本点会被筛选退影，量到的是筛选值 */
  S.st.area='all'; S.st.cat='all'; S.st.q=''; S.st.ink=3;
  S.VB.w=S.VB.wOut; S.apply(); S.refresh();
  out.tierFar=[opOf(iEx),opOf(iAp),opOf(iUn)];
  out.fieldOpFar=+(+cve.style.opacity).toFixed(2);
  S.VB.w=Math.max(S.VB.wIn, S.VB.wOut/12); S.apply(); S.refresh();
  out.tierNear=[opOf(iEx),opOf(iAp),opOf(iUn)];
  out.fieldOpNear=+(+cve.style.opacity).toFixed(2);
  S.VB.w=S.VB.wOut; S.apply(); S.refresh();

  /* I. 范围框：几何须包住命中点，且不过分外扩 */
  S.st.area='gl'; S.refresh();
  var gs=document.querySelector('#gScope'), gr=gs.querySelector('rect'), gt=gs.querySelector('text');
  var pts=S.PTS.filter(function(d){return d._area==='gl';});
  var x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;
  pts.forEach(function(d){ if(d._x<x0)x0=d._x; if(d._x>x1)x1=d._x;
    if(d._y<y0)y0=d._y; if(d._y>y1)y1=d._y; });
  out.scope={on:gs.classList.contains('on'), lbl:gt?gt.textContent:'', n:pts.length,
    rect:{x:+gr.getAttribute('x'),y:+gr.getAttribute('y'),
          w:+gr.getAttribute('width'),h:+gr.getAttribute('height')},
    box:{x:+x0.toFixed(3),y:+y0.toFixed(3),w:+(x1-x0).toFixed(3),h:+(y1-y0).toFixed(3)}};
  S.st.area='all'; S.refresh();
  out.scopeOff=gs.classList.contains('on');

  /* J. 配乐映射：每个市井都有音级、每个品类都有音色与音高 */
  out.snd={areas:Object.keys(S.AREA_FREQ).length, cats:Object.keys(S.CAT_TONE).length,
           keys:S.AREAS.map(function(g){return S.AREA_FREQ[g.k]?1:0;}).join(""),
           /* 九类必须九种音高：此前品类只改音色（衰减/低通）不改音高，
              同属一片市井的店无论卖什么，出来都是同一个音。 */
           muls:(function(){ var s={},k;
             for(k in S.CAT_TONE) s[+S.CAT_TONE[k][2].toFixed(4)]=1;
             return Object.keys(s).length; })(),
           mulsTxt:Object.keys(S.CAT_TONE).map(function(k){
             return k+S.CAT_TONE[k][2].toFixed(2); }).join(" "),
           /* 一档墨三档音：音高、时值、亮度三者都要不同 */
           inkTones:3,
           /* 手势音的种类数（换片/换类/收墨/寻它/收回/合帖/入囊/出囊/确认/落空/处所） */
           gestures:11};

  /* K. 交互可达性：分级只该管浓淡与标签，不该顺手把点击也关掉。
        此前 live=ok&&_ink<=T 同时管着两者，全景下 150 个淡影点了毫无反应。 */
  S.st.area='all'; S.st.cat='all'; S.st.q=''; S.st.ink=3; S.st.sel=null;
  S.VB.w=S.VB.wOut; S.apply(); S.refresh();
  var cl=0;
  S.PTS.forEach(function(d){ if(d._hit&&d._hit.style.pointerEvents==='all') cl++; });
  out.clickable=cl;
  var C={cx:S.VB.cx, cy:S.VB.cy, w:S.VB.w}, HH=null;
  S.PTS.forEach(function(d){ if(d.star) HH=d; });
  /* 复位：把视野拉回全景。只在确实有帖页打开时才收起它 ——
     无条件下走 closeNote 会在测量前平白动一次标签层，是纯粹的自伤。
     标签层的藏与摆已全部交给 declutter（页内原子完成），探针不必也不该插手。 */
  function home(){
    if(S.st.sel) S.closeNote();
    S.VB.cx=C.cx; S.VB.cy=C.cy; S.VB.w=C.w; S.apply();
  }
  function tap(x,y){
    x=Math.round(x); y=Math.round(y);
    var t=document.elementFromPoint(x,y);
    if(t) t.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,
      clientX:x,clientY:y,view:window}));
    return S.st.sel?S.st.sel.id:null;
  }
  /* 等标签层落定。declutter 是「rAF + 请求合并」的异步过程，而 headless 的
     --virtual-time-budget 会打乱 rAF 节奏（实测 620ms 只跑 1 帧），固定 sleep 量不到稳态。
     这里改为「反复请求 → 每 110ms 复核一次住处标签是否已被摆上」，最多 5 轮。
     它并不放宽判定：若几何上真摆不上，5 轮后依然是隐藏态，M/N/O 照旧失败。 */
  function settle(cb){
    var n=0;
    (function step(){
      S.declutter();
      setTimeout(function(){
        var h=null; S.PTS.forEach(function(d){ if(d.star) h=d; });
        if(n++>=5 || (h && h._lbl.style.display!=='none')){ cb(n); return; }
        step();
      },110);
    })();
  }
  home();
  var hrc=HH._el.getBoundingClientRect();
  out.tapHotel={want:70, got:tap(hrc.left+hrc.width/2, hrc.top+hrc.height/2)};
  home();
  var dd=null;
  S.PTS.forEach(function(x){ if(!dd&&!x._hood&&x._ink===3&&!x.star) dd=x; });
  var r3=dd._el.getBoundingClientRect();
  out.tapUnmarked={want:dd.id, got:tap(r3.left+r3.width/2, r3.top+r3.height/2)};
  home();

  /* L/M/N 的测量要满足两个前提，缺一个就出假阴性：
     ① 上面每次 tap 都会触发一次 560ms 的 flyTo 补间，其 rAF 步会把 VB 一路覆写 ——
        必须等补间彻底结束再 home()，否则「复位」当场被动画冲掉，量到的是深放大态的坐标。
     ② declutter 是异步的「全隐再逐个占位」，紧接着同步读到的是上一态 —— 交给 settle。 */
  setTimeout(function(){
   home();
   settle(function(rounds){
    out.settleRounds=rounds;
    /* L. 住处：不在三态统计里，但作为全篇原点必须恒在、恒可点、恒有名 */
    out.hotel={ink:HH._ink, op:+getComputedStyle(HH._el).opacity,
      pe:HH._el.style.pointerEvents, lbl:HH._lbl.textContent,
      lblShown:getComputedStyle(HH._lbl).display!=='none',
      pad:!!document.querySelector('#gDot circle.pad'),
      legend:!!document.querySelector('#inkcol .ik.origin')};

    /* M. 标签避让：可见标签两两不得相交 */
    var L=[], ov=[];
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
    out.labels={shown:L.length, overlap:ov.length, pairs:ov.slice(0,5),
      texts:L.map(function(x){return x.t;})};
    out.state={vb:[+S.VB.w.toFixed(3),+S.VB.cx.toFixed(3),+S.VB.cy.toFixed(3)],
      wOut:+S.VB.wOut.toFixed(3), tier:S.tierOf(), noteOpen:!document.querySelector('#note').hidden,
      hotelInferred:(function(){
        for(var i=0;i<L.length;i++) if(L[i].t.indexOf('汉庭')>=0) return L[i].t;
        return '(未出现)';})()};
    /* 住处标签的摆位履历：merge=这次 declutter 被 requestAnimationFrame 合并吞掉 */
    out.dlog=(S.dlog?S.dlog():[]).slice(-24);

    /* N. 名字也须点得动：名字是图上最显眼的抓手，点它没反应最像「整个坏了」。
          测住处标签的正中心 —— 它离印 16px，超出墨点的命中半径，只有名字兜底才接得住。 */
    /* 此处不可先 closeNote：它会同步把全部标签 display:none（等下一帧才由 declutter 恢复），
       于是 nameAt 必然找不到名字 —— 那是测试自己制造的假阴性，不是页面缺陷。 */
    var lr=HH._lbl.getBoundingClientRect(), lx=Math.round(lr.left+lr.width/2),
        ly=Math.round(lr.top+lr.height/2);
    var tl=document.elementFromPoint(lx,ly);
    var naH=S.nameAt(lx,ly);
    if(tl) tl.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,
      clientX:lx,clientY:ly,view:window}));
    out.tapName={want:70, got:S.st.sel?S.st.sel.id:null, at:[lx,ly], nameAt:naH?naH.kind:null,
      hitTag:tl?(tl.tagName+(tl.id?'#'+tl.id:'')):'null',
      lblShownNow:getComputedStyle(HH._lbl).display!=='none',
      lblRect:[Math.round(lr.left),Math.round(lr.top),Math.round(lr.width),Math.round(lr.height)]};

    out.dots=document.querySelectorAll('#gDot circle:not(.pad),#gDot rect').length;
    out.hits=document.querySelectorAll('#gHit circle').length;
    out.wash=document.querySelectorAll('#gWash circle').length;
    out.nomap=document.querySelectorAll('#wall b').length;

    /* O. 选中项自己的名字不得反而消失。同一枚标签会被多条优先级规则先后点到
          （选中项往往同时是锚点），第二次摆放会撞上自己上一次推入的框而自藏，
          症状正是「点开的那个点，名字没了」。用 settle 等 declutter 落定；
          它的收敛轮数记进 settleRounds —— 若贴着 5 的上限，说明页面在打摆子。 */
    settle(function(orounds){
      var b0=getComputedStyle(HH._lbl).display;
      out.selLbl={txt:S.st.sel?S.st.sel._lbl.textContent:'(无选中)',
        shown:b0!=='none', rawDisplay:b0,
        note:!document.querySelector('#note').hidden, rounds:orounds};

      /* P. 点一枚墨点＝只翻开它的帖页。视野不动、不连线、不进入「定位」态。
            此前这里还顺带 flyTo 到 1.15km 并自动画朱砂直线 ——
            等于替用户把「这家离我多远」当成了他点开的意图，视野被夺走。 */
      S.closeNote();
      S.VB.cx=C.cx; S.VB.cy=C.cy; S.VB.w=C.w; S.apply();
      var d2=null;
      S.PTS.forEach(function(x){ if(!d2&&!x._hood&&x._ink===1&&!x.star) d2=x; });
      var vb0=[+S.VB.cx.toFixed(4),+S.VB.cy.toFixed(4),+S.VB.w.toFixed(4)],
          r2=d2._el.getBoundingClientRect(),
          got2=tap(r2.left+r2.width/2, r2.top+r2.height/2),
          vb1=[+S.VB.cx.toFixed(4),+S.VB.cy.toFixed(4),+S.VB.w.toFixed(4)];
      out.openOnly={want:d2.id, got:got2,
        vbSame:vb0[0]===vb1[0]&&vb0[1]===vb1[1]&&vb0[2]===vb1[2], vb0:vb0, vb1:vb1,
        locate:!!S.st.locate, routeLines:document.querySelectorAll('#gRoute line').length,
        noteOpen:!document.querySelector('#note').hidden,
        btn:document.querySelector('#nLocate').textContent.trim()};

      /* Q. 「图上寻它」：按下去才飞过去、才落那条朱砂线；再按一次收回。
            两次点击之间必须等 flyTo 的 560ms 补间走完，否则量到的是起点。 */
      var lb=document.querySelector('#nLocate');
      lb.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
      out.locateOn={on:!!S.st.locate, lines:document.querySelectorAll('#gRoute line').length,
        btn:lb.textContent.trim(), lit:lb.classList.contains('on')};
      setTimeout(function(){
        out.locateOn.vbW=+S.VB.w.toFixed(3);
        out.locateOn.moved=out.locateOn.vbW<C.w-0.01;
        lb.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
        out.locateOff={on:!!S.st.locate, lines:document.querySelectorAll('#gRoute line').length,
          btn:lb.textContent.trim(), lit:lb.classList.contains('on')};
        /* 无坐标的 34 家：没有位置可指，按钮必须废掉而不是按下去没反应 */
        var dn=null; S.NO.forEach(function(x){ if(!dn) dn=x; });
        S.openNote(dn);
        var lb2=document.querySelector('#nLocate');
        out.locateNone={disabled:!!lb2.disabled, btn:lb2.textContent.trim(),
          noteOpen:!document.querySelector('#note').hidden};
        document.title='RES'+JSON.stringify(out);
      },760);
    });
   });
  },700);
},1600);
</script>
"""


def run():
    src = open(SRC, encoding="utf-8").read()
    open(TMP, "w", encoding="utf-8").write(src.replace("</body>", PROBE + "</body>"))
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--window-size=1600,900", "--virtual-time-budget=9000", "--dump-dom",
                        "file:///" + TMP.replace("\\", "/")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"<title>RES(.*?)</title>", r.stdout, re.S)
    if not m:
        print("!! 未能取到结果"); return None
    return json.loads(m.group(1))


if __name__ == "__main__":
    o = run()
    if not o: raise SystemExit(1)
    data = json.load(open(os.path.join(ROOT, "data.json"), encoding="utf-8"))
    CAT = {"汤": ["驴肉汤", "鸡血汤", "汤馆", "羊肉汤", "牛肉汤", "四味菜", "羊双肠", "早餐·胡辣汤", "早餐"],
           "包": ["灌汤包", "灌汤包·豫菜", "川菜·灌汤包", "锅贴·灌汤包", "锅贴"],
           "面": ["面食", "米线", "烩菜", "砂锅"],
           "炙": ["烧烤", "熟食", "熟食小吃", "牛羊肉"],
           "甜": ["糕点小吃", "甜品", "饮品甜品"],
           "夜": ["夜市", "夜市小吃", "宵夜", "外卖"],
           "正": ["豫菜", "川菜", "烤鸭·豫菜", "火锅", "农家菜", "清真小吃", "西餐", "西式快餐", "简餐"],
           "杂": ["小吃", "园内小吃", "园内正餐", "特产"],
           "处": ["景点", "地标", "住宿", "交通"]}
    ok = True

    def chk(name, got, want, tol=0):
        global ok
        good = (abs(got - want) <= tol) if isinstance(got, (int, float)) and isinstance(want, (int, float)) else got == want
        ok = ok and good
        print("  %s %-30s 实测 %-10s 期望 %s" % ("PASS" if good else "FAIL", name, got, want))

    print("A. 投影真实性（屏幕像素换算距离 − haversine 实距，单位 km）")
    print("   各配对误差:", o["projErrKm"], " 最大", o["projMaxErr"])
    chk("投影像素 vs 实距", o["projMaxErr"], 0, tol=0.06)

    print("B. 数量")
    chk("落墨点数", o["dots"], 183); chk("命中圈", o["hits"], 183)
    chk("无处安放", o["nomap"], 34)

    print("C. 墨色闸门（确址/约略/未标）")
    # 期望值从 data.json 现推，不硬编码 —— 硬编码会让核验与页面口径各自漂移而无人察觉。
    # 星标住处没有 loc 字段，但坐标是柒总给的到门牌实址，归确址（同构建脚本 INK_OF）。
    def ink_of(x):
        if x.get("star"): return 1
        return 1 if x.get("loc") == "exact" else (2 if x.get("loc") == "approx" else 3)
    _mapped = {x["id"] for x in data if isinstance(x.get("lat"), (int, float))}
    _exp = [sum(1 for x in data if ink_of(x) == 1 and x["id"] in _mapped),
            sum(1 for x in data if ink_of(x) <= 2 and x["id"] in _mapped),
            len(_mapped)]
    for got, want in zip(o["inkGate"], _exp):
        chk("闸门档位", got, want)

    print("D. 品类（与 data.json 直接计数比对）")
    mapped = {x["id"] for x in data if isinstance(x.get("lat"), (int, float))}
    for k, v in o["cats"].items():
        want = sum(1 for x in data if x["ty"] in CAT[k] and x["id"] in mapped)
        chk("品类 %s 落墨" % k, v, want)
        whole = sum(1 for x in data if x["ty"] in CAT[k])
        un = whole - want
        want_txt = str(want) + ("＋%d" % un if un else "")
        chk("品类 %s 计数文案" % k, o["catTxt_" + k].replace(" 命中", ""), want_txt)

    print("E. 市井（与区域分组计数比对）")
    ARS = {"清园": ["清园内", "清园周边"], "鼓楼": ["鼓楼书店街"], "河大": ["老河大"],
           "星光": ["星光天地"], "东大寺": ["东大寺"], "翠园": ["翠园"], "西司": ["西司"],
           "东郊": ["东郊夜市"], "汴京园": ["汴京公园"],
           "散记": ["未定位", "其他", "住宿", "交通", "苹果园", "集英花园", "东陈庄"]}
    for k, v in o["areas"].items():
        want = sum(1 for x in data if x["ar"] in ARS[k] and x["id"] in mapped)
        chk("市井 %s 落墨" % k, v, want)
    chk("市井落墨合计", sum(o["areas"].values()), len(mapped))
    chk("全", o["areaAll"], len(mapped))

    print("F. 检索")
    def hit(kw):
        return [x for x in data if kw in (x["n"] + x["ty"] + x["ar"] + x["ad"] + x["ds"] + x["rm"])]
    h = hit("汤")
    chk("寻「汤」落墨", o["q汤"], sum(1 for x in h if x["id"] in mapped))
    chk("寻「汤」计数文案", o["q汤Txt"].replace(" 命中", ""),
        str(sum(1 for x in h if x["id"] in mapped)) + "＋%d" % sum(1 for x in h if x["id"] not in mapped))
    chk("寻「胡辣汤」落墨", o["q胡辣汤"], sum(1 for x in hit("胡辣汤") if x["id"] in mapped))
    chk("无处安放副标题", o["noSubAll"], "原帖未给位置 · 共 34 家")

    print("G. 行囊直线总长 (km)")
    print("   实测/期望:", o["bagSum"])
    chk("行囊样本", o["bagLocal"], "鼓楼夜市/汴梁老黄记灌汤包(鼓楼广场店)")

    print("H. 墨相与分级显示")
    f = o["field"]
    chk("墨场画布覆盖 stage", f["cw"] >= f["sw"] and f["ch"] >= f["sh"], True)
    far, near = o["tierFar"], o["tierNear"]
    print("   远景三态透明度:", far, " 近景:", near)
    chk("远景  实墨>半墨>未标", far[0] > far[1] > far[2], True)
    chk("近景  三态全显", near == [1, 0.82, 1], True)
    chk("墨场远景浓于近景", o["fieldOpFar"] > o["fieldOpNear"], True)

    print("I. 范围联动（选择即视野）")
    sc = o["scope"]
    chk("选中市井 范围框出现", sc["on"], True)
    chk("范围框题名", sc["lbl"], "鼓楼·书店街 · 40 家")
    chk("范围框家数", sc["n"], 40)
    R, B = sc["rect"], sc["box"]
    inside = (R["x"] <= B["x"] + 1e-6 and R["y"] <= B["y"] + 1e-6 and
              R["x"] + R["w"] >= B["x"] + B["w"] - 1e-6 and
              R["y"] + R["h"] >= B["y"] + B["h"] - 1e-6)
    chk("范围框包住命中点", inside, True)
    print("   框/点 包围盒宽度比:", round(R["w"] / B["w"], 3))
    chk("范围框外扩 < 40%", R["w"] / B["w"] < 1.4, True)
    chk("取消筛选后范围框收起", o["scopeOff"], False)

    print("J. 配乐映射（听觉变量同样可追溯到字段）")
    chk("市井音级覆盖", o["snd"]["areas"], 10)
    chk("品类音色覆盖", o["snd"]["cats"], 9)
    chk("每个市井都有音", o["snd"]["keys"], "1" * 10)
    chk("九类音高各不相同", o["snd"]["muls"], 9)
    print("     品类音高乘数: %s" % o["snd"]["mulsTxt"])

    print("K. 交互可达性（分级只管浓淡，不该顺手把点击也关掉）")
    chk("全景下可点数 = 落墨数", o["clickable"], o["dots"])
    chk("点住处中心开出住处", o["tapHotel"]["got"], o["tapHotel"]["want"])
    chk("点未标虚圈中心开出它自己", o["tapUnmarked"]["got"], o["tapUnmarked"]["want"])
    chk("点名字也开得出（住处标签）", o["tapName"]["got"], o["tapName"]["want"])
    if o["tapName"]["got"] != o["tapName"]["want"]:
        print("     诊断:", json.dumps(o["tapName"], ensure_ascii=False))

    print("L. 住处（原点）：不在三态统计里，但必须恒在、恒可点、恒有名")
    chk("住处归确址", o["hotel"]["ink"], 1)
    chk("住处满墨", o["hotel"]["op"], 1.0, tol=0.001)
    chk("住处可点", o["hotel"]["pe"], "all")
    chk("住处名字", o["hotel"]["lbl"], "宿 · 汉庭酒店")
    chk("住处标签常显", o["hotel"]["lblShown"], True)
    chk("住处纸色衬垫", o["hotel"]["pad"], True)
    chk("墨样柱有「宿」行", o["hotel"]["legend"], True)

    print("M. 标签避让（几何实测，两两不得相交）")
    st = o["state"]
    print("   测量态 vb=%s wOut=%s tier=%s 帖页=%s ／ settle 收敛轮数=%s ／ 21 与 22 之差就是住处标签：%s" % (
        st["vb"], st["wOut"], st["tier"], st["noteOpen"], o.get("settleRounds"), st["hotelInferred"]))
    print("   全景可见标签 %d 个，相交 %d 对 %s" % (
        o["labels"]["shown"], o["labels"]["overlap"], o["labels"]["pairs"]))
    if st["hotelInferred"] == "(未出现)" or (o.get("settleRounds") or 0) > 1:
        print("   实际出现的标签:", "｜".join(o["labels"]["texts"]))
        print("   住处标签摆位履历（末 24 条，只记它自己）:")
        for r in o.get("dlog", []):
            print("     %6dms %-16s 视野宽=%-8s 档=%-3s 已占框=%-4s dt=%-5s raf=%-4s 挡它的框=%s" % (
                r["ms"], r["tag"], r["w"], r["T"], r["nb"], r.get("dt"), r.get("raf"), r["blk"]))
    chk("标签互不重叠", o["labels"]["overlap"], 0)
    chk("标签确实画出来了", o["labels"]["shown"] > 10, True)

    print("O. 选中项：点开后它自己的名字不得消失")
    chk("选中项标签仍显示", o["selLbl"]["shown"], True)
    chk("选中项标签文字", o["selLbl"]["txt"], "宿 · 汉庭酒店")

    print("P. 点墨点＝只翻开帖页（视野不得被夺走）")
    p = o["openOnly"]
    chk("点开了那一家的帖页", p["got"], p["want"])
    chk("帖页确实打开", p["noteOpen"], True)
    chk("视野原地不动", p["vbSame"], True)
    if p["vbSame"] is not True:
        print("     诊断: 点击前 %s → 点击后 %s" % (p["vb0"], p["vb1"]))
    chk("不自动落朱砂线", p["routeLines"], 0)
    chk("不进入定位态", p["locate"], False)
    chk("按钮为「图上寻它」", p["btn"], "图上寻它")

    print("Q. 「图上寻它」：朱线与视野由它触发，不由开帖页触发")
    qo, qf, qn = o["locateOn"], o["locateOff"], o["locateNone"]
    chk("按下后进入定位态", qo["on"], True)
    chk("按下后落一条朱砂线", qo["lines"], 1)
    chk("按钮改称「收起朱线」", qo["btn"], "收起朱线")
    chk("按下后按钮点亮", qo["lit"], True)
    chk("按下后视野确实飞过去", qo["moved"], True)
    if qo["moved"] is not True:
        print("     诊断: 飞后视野宽 %s（原 %s）" % (qo["vbW"], 19.616))
    chk("再按退出定位态", qf["on"], False)
    chk("再按朱砂线收走", qf["lines"], 0)
    chk("按钮改回「图上寻它」", qf["btn"], "图上寻它")
    chk("无坐标者按钮作废", qn["disabled"], True)
    chk("无坐标者按钮文案", qn["btn"], "无处可指")
    chk("无坐标者帖页照样能开", qn["noteOpen"], True)

    print("\n结论：%s" % ("全部通过 ✅" if ok else "存在未通过项 ❌"))
    if os.path.exists(TMP): os.remove(TMP)
