# -*- coding: utf-8 -*-
"""生成交互式 HTML 页面（数据内联，零外部依赖）。"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "data.json"), encoding="utf-8") as f:
    spots = json.load(f)

TPL = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>开封美食地图 · 清明上河园 / 鼓楼</title>
<style>
/* ---- Leaflet 1.9.4（内联，避免联网加载库；仅底图瓦片需联网） ---- */
__LEAFLET_CSS__
</style>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#f7f5f1;color:#22201d;font-family:"PingFang SC","Microsoft YaHei","Hiragino Sans GB","Source Han Sans SC",system-ui,-apple-system,"Segoe UI",sans-serif;font-size:14px;line-height:1.6}
.wrap{max-width:1500px;margin:0 auto;padding:14px 18px 14px;height:100vh;display:flex;flex-direction:column}
header{padding:2px 0 12px;border-bottom:1px solid rgba(0,0,0,.08);margin-bottom:10px;flex:0 0 auto}
h1{font-size:23px;font-weight:700;letter-spacing:.5px}
h1 span{color:#b5443a}
.sub{color:#75706a;font-size:13px;margin-top:6px}
.stats{display:flex;gap:18px;flex-wrap:wrap;margin-top:12px;font-size:12.5px;color:#5c5852}
.stats b{color:#22201d;font-weight:600}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 12px;background:#f7f5f1;padding:0;flex:0 0 auto;z-index:20}
input[type=text]{flex:1 1 200px;min-width:160px;padding:9px 12px;border:1px solid rgba(0,0,0,.14);border-radius:9px;background:#fff;font-size:13.5px;font-family:inherit;color:#22201d}
input[type=text]:focus{outline:none;border-color:#b5443a}
select{padding:9px 10px;border:1px solid rgba(0,0,0,.14);border-radius:9px;background:#fff;font-size:13px;font-family:inherit;color:#22201d;cursor:pointer}
.btn{padding:9px 15px;border-radius:9px;border:1px solid rgba(0,0,0,.14);background:#fff;font-size:13px;cursor:pointer;font-family:inherit;color:#22201d;transition:.15s;white-space:nowrap}
.btn:hover{border-color:#b5443a;color:#b5443a}
.btn.primary{background:#b5443a;color:#fff;border-color:#b5443a}
.btn.primary:hover{background:#9c382f;color:#fff}
main{flex:1 1 auto;min-height:0;display:block}
.grid2{height:100%;min-height:0;display:grid;grid-template-columns:minmax(0,1fr) 500px;gap:16px;align-items:stretch}
.grid2>aside{height:100%;min-height:0;display:flex;flex-direction:column;gap:10px}
/* 清单独立滚动区：地图常驻，清单自己滚 */
.pane{flex:1 1 auto;min-height:0;overflow-y:auto;overscroll-behavior:contain;padding-right:5px;display:flex;flex-direction:column;gap:9px}
.pane::-webkit-scrollbar{width:9px}
.pane::-webkit-scrollbar-track{background:rgba(0,0,0,.03);border-radius:5px}
.pane::-webkit-scrollbar-thumb{background:rgba(0,0,0,.17);border-radius:5px}
.pane::-webkit-scrollbar-thumb:hover{background:rgba(0,0,0,.3)}
.notes{flex:0 0 auto;display:flex;flex-direction:column;gap:7px}
.notes .sect{margin:0;font-size:12.5px}
.notes details.note{font-size:12px;padding:8px 10px}
.list{display:flex;flex-direction:column;gap:9px;max-height:none}
.card{background:#fff;border:1px solid rgba(0,0,0,.07);border-radius:12px;padding:12px 14px;cursor:pointer;transition:.15s;position:relative}
.card:hover{border-color:rgba(181,68,58,.45);box-shadow:0 3px 14px rgba(0,0,0,.055)}
.card.active{border-color:#b5443a;box-shadow:0 0 0 2px rgba(181,68,58,.14)}
.card .top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}
.card .nm{font-weight:600;font-size:14.5px;letter-spacing:.2px}
/* 店名一键复制按钮 */
.cp{margin-left:7px;padding:1px 7px;font-size:10.5px;line-height:1.6;border:1px solid rgba(0,0,0,.14);border-radius:6px;background:#fff;color:#8a857e;cursor:pointer;font-family:inherit;font-weight:500;vertical-align:1px;transition:.15s}
.cp:hover{border-color:#b5443a;color:#b5443a;background:rgba(181,68,58,.06)}
.cp:active{background:rgba(181,68,58,.13)}
.tag{display:inline-block;font-size:11px;padding:2px 8px;border-radius:20px;margin-top:5px;margin-right:5px;white-space:nowrap;border:1px solid transparent}
.card .ds{color:#4a4642;font-size:12.8px;margin-top:7px}
.card .rm{color:#8a857e;font-size:12.2px;margin-top:4px}
.card .ad{color:#8a857e;font-size:11.8px;margin-top:5px}
.dist{font-size:11.5px;color:#2f7d63;font-weight:600;white-space:nowrap;background:rgba(47,125,99,.09);padding:2px 8px;border-radius:20px}
.noloc{font-size:11.5px;color:#a09a92;background:rgba(0,0,0,.045);padding:2px 8px;border-radius:20px;white-space:nowrap}
.approx{font-size:11.5px;color:#8a6d3b;background:rgba(214,158,46,.13);padding:2px 8px;border-radius:20px;white-space:nowrap}
.mapbox{background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:14px;padding:12px;box-shadow:0 3px 16px rgba(0,0,0,.05)}
.map-main{position:relative;height:100%;min-height:0;display:flex;flex-direction:column}
#map{width:100%;flex:1 1 auto;height:auto;min-height:260px;border-radius:10px;background:#e9e5df;border:1px solid rgba(0,0,0,.08);z-index:1}
.leaflet-container{font-family:inherit;font-size:12.5px}
.leaflet-popup-content{margin:9px 12px;font-size:13px;line-height:1.6}
.mapfail{display:none;padding:16px;font-size:13px;color:#8a3c33;background:rgba(220,53,69,.06);border:1px solid rgba(220,53,69,.25);border-radius:9px}
.mapfail.on{display:block}
.legend{display:flex;flex-wrap:wrap;gap:9px;margin-top:11px;font-size:11.5px;color:#5c5852;flex:0 0 auto}
.legend i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px;vertical-align:middle}
.hint{font-size:11.5px;color:#8a857e;margin-top:8px;line-height:1.6;flex:0 0 auto}
.detail{background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:14px;padding:14px;margin-top:0;box-shadow:0 3px 16px rgba(0,0,0,.05);transition:box-shadow .25s,border-color .25s;flex:0 0 auto;max-height:44%;overflow-y:auto;overscroll-behavior:contain}
.detail::-webkit-scrollbar{width:8px}
.detail::-webkit-scrollbar-thumb{background:rgba(0,0,0,.15);border-radius:4px}
.detail.flash{border-color:#b5443a;box-shadow:0 0 0 3px rgba(181,68,58,.14),0 3px 16px rgba(0,0,0,.06)}
.detail h3{font-size:15px;margin-bottom:8px}
/* 详情头部：标题 + 关闭按钮（与「再次点击该地点」互为补充的显式关闭入口） */
.dhead{display:flex;align-items:flex-start;gap:8px}
.dhead h3{flex:1;min-width:0;margin-bottom:8px}
.dhead .dx{flex:0 0 auto;width:24px;height:24px;padding:0;line-height:1;border:1px solid rgba(0,0,0,.14);background:#fff;color:#6b6560;border-radius:8px;cursor:pointer;font-size:13px;font-family:inherit}
.dhead .dx:hover{background:#f2efec;color:#22201d;border-color:rgba(0,0,0,.26)}
/* 详情面板复制按钮组 */
.cps{display:flex;gap:6px;flex-wrap:wrap;margin:-2px 0 9px}
.cp2{font-size:11.5px;padding:4px 10px;border-radius:7px;border:1px solid rgba(0,0,0,.14);background:#fff;color:#4a4642;cursor:pointer;font-family:inherit}
.cp2:hover{border-color:#b5443a;color:#b5443a;background:rgba(181,68,58,.05)}
.cp2:active{background:rgba(181,68,58,.13)}
.detail .kv{font-size:12.8px;color:#4a4642;margin-top:5px}
.detail a{color:#b5443a;text-decoration:none;font-weight:600}
.detail a:hover{text-decoration:underline}
.shot{margin:9px 0 4px;border:1px solid rgba(0,0,0,.09);border-radius:10px;overflow:hidden;background:#fbfaf7}
.shot img{width:100%;max-height:168px;object-fit:contain;background:#fbfaf7;display:block;cursor:zoom-in}
.shot .shot-cap{font-size:11px;color:#8a857e;padding:5px 9px;border-top:1px solid rgba(0,0,0,.06);background:#fff}
.lb{position:fixed;inset:0;background:rgba(20,18,16,.86);display:none;align-items:center;justify-content:center;z-index:99;padding:24px;cursor:zoom-out}
.lb.on{display:flex}
.lb img{max-width:96vw;max-height:92vh;border-radius:8px;box-shadow:0 10px 50px rgba(0,0,0,.5)}
.sect{margin:26px 0 10px;font-size:15px;font-weight:700;display:flex;align-items:center;gap:9px}
.sect::after{content:"";flex:1;height:1px;background:rgba(0,0,0,.09)}
details.note{background:#fff;border:1px solid rgba(0,0,0,.07);border-radius:12px;padding:12px 14px;margin-top:12px;font-size:12.8px;color:#4a4642}
details.note summary{cursor:pointer;font-weight:600;color:#22201d}
details.note ul{margin:9px 0 0 18px}
details.note li{margin:3px 0}
.badge{display:inline-block;font-size:10.5px;padding:1px 6px;border-radius:4px;background:rgba(225,29,72,.1);color:#e11d48;font-weight:600;margin-left:6px}
.toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%) translateY(24px);max-width:600px;width:calc(100% - 32px);background:#fff;border:1px solid rgba(0,0,0,.12);border-left:4px solid #b5443a;border-radius:12px;padding:13px 17px;box-shadow:0 10px 40px rgba(0,0,0,.18);font-size:13px;line-height:1.7;color:#22201d;z-index:120;opacity:0;pointer-events:none;transition:opacity .22s,transform .22s}
.toast.on{opacity:1;transform:translateX(-50%) translateY(0);pointer-events:auto}
.toast .tt{font-weight:700;font-size:13.5px;display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:3px}
.toast .x{cursor:pointer;color:#8a857e;font-size:15px;line-height:1;padding:0 3px;flex:0 0 auto}
.toast .x:hover{color:#22201d}
.toast ul{margin:5px 0 0 17px}
.toast li{margin:2px 0}
.toast code{background:rgba(0,0,0,.06);padding:1px 5px;border-radius:4px;font-size:12px}
.toast .acts{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}
.toast .acts button{font-size:12.2px;padding:7px 12px;border-radius:8px;border:1px solid rgba(0,0,0,.14);background:#fff;cursor:pointer;font-family:inherit;color:#22201d}
.toast .acts button.p{background:#b5443a;color:#fff;border-color:#b5443a}
.toast.ok{border-left-color:#2f7d63}
@media(max-width:1080px){
  .wrap{height:100dvh;min-height:100vh;padding:10px 10px 8px}
  .sub{display:none}
  header{padding-bottom:8px;margin-bottom:8px}
  main{display:flex;flex-direction:column;flex:1 1 auto;min-height:0}
  .grid2{display:flex;flex-direction:column;gap:8px;height:100%;flex:1 1 auto;min-height:0}
  .hint{display:none}
  .map-main{flex:0 0 auto;height:auto;min-height:0;overflow:visible}
  #map{flex:0 0 auto;height:32vh;min-height:180px}
  .legend{margin-top:8px;font-size:11px;gap:7px}
  .grid2>aside{flex:1 1 auto;min-height:0;height:auto;display:block;overflow-y:auto;overscroll-behavior:contain;padding-bottom:14px}
  #detail{max-height:none;overflow:visible;margin-top:0}
  .pane{max-height:none;overflow:visible;padding-right:0}
}
@media(max-width:640px){
  .wrap{padding:8px 8px 6px}
  h1{font-size:18px}
  .hint{display:none}
  /* 图例压成一整行横向可滑，避免占用地图高度 */
  .legend{flex-wrap:nowrap;overflow-x:auto;white-space:nowrap;padding-bottom:3px}
  .legend span{flex:0 0 auto}
  .legend::-webkit-scrollbar{height:0}
  .stats{gap:6px 12px;font-size:11.5px;margin-top:8px}
  .toolbar{gap:6px;margin-bottom:8px}
  .toolbar>*{min-width:0;max-width:100%}
  input[type=text]{flex:1 1 100%;padding:8px 10px}
  select{flex:1 1 calc(50% - 3px);max-width:calc(50% - 3px);padding:8px}
  .btn{flex:1 1 calc(50% - 3px);white-space:normal;padding:9px 10px;font-size:12.5px}
  .detail{margin-top:0;padding:11px}
  .detail h3{font-size:14.5px;word-break:break-word}
  .card{padding:10px 11px}
  .card .top{flex-wrap:wrap;gap:6px}
  .card .top>div{min-width:0}
  .map-main{padding:8px}
}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>开封美食地图 <span>·</span> 清明上河园 / 鼓楼 / 老河大</h1>
  <div class="sub">来源：小红书帖子与评论区截图 62 张 · 坐标经腾讯地图逐条检索（实心点＝精确，空心虚线点＝区域近似）· 底图：高德 · 住宿：汉庭酒店(开封鼓楼火车站店)（<b>地图上唯一的红色五角星</b>）· <b>每条均可点开「来源截图」原图核对</b></div>
  <div class="stats">
    <span>条目总数 <b id="s1">0</b></span>
    <span>精确定位 <b id="s2">0</b></span>
    <span>区域近似 <b id="s5">0</b></span>
    <span>未定位 <b id="s3">0</b></span>
    <span id="s6wrap" style="display:none">其他酒店不标注 <b id="s6">0</b></span>
    <span>已合并重复 <b>9</b> 条</span>
    <span id="s4">距离：未获取定位</span>
  </div>
</header>

<div class="toolbar">
  <input type="text" id="q" placeholder="搜索店名 / 菜品 / 街区…">
  <select id="fArea"></select>
  <select id="fType"></select>
  <select id="fOrder">
    <option value="def">默认顺序</option>
    <option value="dist">距离最近</option>
    <option value="area">按区域</option>
  </select>
  <button class="btn primary" id="geo">📍 获取我的位置并算距离</button>
  <button class="btn" id="toHotel">🏨 以酒店为基准算距离</button>
  <button class="btn" id="resetDist" style="display:none">↺ 重置距离</button>
</div>

<main>
  <div class="grid2">
    <div class="mapbox map-main">
      <div id="map"></div>
      <div class="mapfail" id="mapfail">⚠️ 底图瓦片加载失败。真实地图需要联网（瓦片来自高德）。请检查网络后刷新；<b>圆点与店铺数据不受影响</b>，仍可在下方列表查看全部条目。</div>
      <div class="legend" id="legend"></div>
      <div class="hint"><b>地图操作</b>：双指捏合缩放 / 单指拖动平移（手机），滚轮缩放 / 按住拖动（电脑），左上角 ＋/－ 按钮亦可。<br><b>实心圆点</b>＝已精确定位的店铺（颜色区分类型）；<b>空心圆点</b>＝仅知大致区域（夜市摊位、园内摊位等，无独立地图POI）；<b>★ 红色五角星（全图唯一）</b>＝本次住宿「汉庭酒店(开封鼓楼火车站店)」。点击任意点即可查看详情。<br><b>复制</b>：清单每张卡片店名旁的「复制」按钮＝一键复制店名；点开详情后还可复制「名称 + 地址」，方便直接发给同行的人。</div>
    </div>
    <aside>
      <div class="detail" id="detail"><h3>点选一个地点</h3><div class="kv">在地图上点击圆点，或在右侧清单中选择，这里会显示详细信息、来源截图与导航入口。</div></div>
      <div class="pane" id="pane">
        <div class="notes">
          <details class="note">
  <summary>高频推荐速览（多图交叉印证）</summary>
  <ul>
    <li><b>清明上河园内</b>：孙记鸡血粉丝汤（东京食坊）、王婆粥铺铁板鸡架、孙羊正店烩面/筒子鸡、大宋切糕、虹桥杏仁茶</li>
    <li><b>清园周边</b>：逍遥奇永胡辣汤（早餐）、邢家锅贴老店（大梁门总店）、汴梁嘉宴灌汤包（龙亭店）、化三驴肉汤、宋都老黄记灌汤包</li>
    <li><b>灌汤包</b>：黄家老店（多分店）、第一楼、宋园、汴梁嘉宴、鼓楼饺子馆开封灌汤包老店</li>
    <li><b>本地人力荐夜市</b>：西司夜市（羊肉炕馍、烙饼卷面筋）、老河大夜市、东郊夜市；<b>鼓楼夜市被多位本地人劝退</b></li>
    <li><b>饮品甜品</b>：王大昌茶坊、元本有方、大台北、眷茶、嗒令甜品、吴记芋头饼、古法济公切糕</li>
  </ul>
        </details>
        </div>
        <section class="list" id="list"></section>
        <!-- 说明块置于清单末尾：不遮挡清单，滚到底即可查阅 -->
        <div class="notes">
          <div class="sect">数据说明与核验</div>
          <details class="note">
  <summary>位置校验方式 / 距离计算原理 / 已知局限</summary>
  <ul>
    <li><b>位置校验</b>：所有「已定位」条目均通过腾讯地图地点检索（placeSuggestion）逐条比对，坐标采用地图返回的 POI 经纬度；同品牌多分店时取与截图语境最匹配的分店。</li>
    <li><b>未定位条目</b>：多为夜市摊点、简称、帖主手写清单中的条目，腾讯地图未检索到唯一匹配结果，已标注「待核实」，需要现场或到当地后再确认。</li>
    <li><b>距离计算</b>：点击「获取我的位置」后，浏览器通过 Geolocation 取当前经纬度，再用 Haversine 公式计算与各店的<b>球面直线距离</b>（非驾车/步行路径距离，实际路程会更长）。</li>
    <li><b>前提条件</b>：定位需要浏览器授权，且 HTTPS/localhost 环境下才生效；若您不在开封（如嘉兴），显示的距离为跨城直线距离。</li>
    <li><b>未核实项</b>：评论区口语化内容存在个别错别字或歧义，凡无法从截图确证的字词均未纳入，避免误导。</li>
    <li><b>去重说明（本次修正）</b>：初版曾把同一家店的「泛称/占位条目」与「具体分店」分别计入，导致 <b>197 → 188</b>。已合并 9 条重复：邢家锅贴 3 条、第一楼 2 条、州桥日夜餐馆 1 条、田记米线 1 条、书店街 1 条、宋园 1 条（同一实体的不同写法）。</li>
    <li><b>待确认项</b>：① 化三驴肉汤馆「万岁山总店」与「首座时代总店」同名"总店"，疑为同一家被地图平台重复收录；② 部分条目为两家合记（如「马豫兴桶子鸡 / 存花桶子鸡」）已在备注标注。</li>
  </ul>
</details>
        </div>
      </div>
    </aside>
  </div>
</main>
</div>

<script>
/* ---- Leaflet 1.9.4 ---- */
__LEAFLET_JS__
</script>
<script>
const SPOTS = __DATA__;

const TYPE_COLOR = {
 "灌汤包":"#c0392b","锅贴·灌汤包":"#c0392b","锅贴":"#c0392b","豫菜":"#a93226","川菜":"#378add","川菜·灌汤包":"#378add",
 "驴肉汤":"#a0522d","鸡血汤":"#a0522d","羊肉汤":"#a0522d","牛肉汤":"#a0522d","汤馆":"#a0522d","羊双肠":"#a0522d",
 "火锅":"#d35400","烧烤":"#8e44ad","饮品甜品":"#2f7d63","糕点小吃":"#2f7d63",
 "夜市":"#e67e22","夜市小吃":"#e67e22","小吃":"#7f8c8d","园内小吃":"#e67e22","面食":"#7f8c8d","米线":"#7f8c8d",
 "早餐·胡辣汤":"#e67e22","西式快餐":"#378add","西餐":"#378add","农家菜":"#a93226","烩菜":"#a93226","熟食":"#7f8c8d",
 "特产":"#7f8c8d","清真小吃":"#7f8c8d","园内正餐":"#a93226","烤鸭·豫菜":"#a93226","景点":"#16a085","地标":"#16a085",
 "住宿":"#9b59b6","交通":"#7f8c8d","宵夜":"#e67e22","外卖":"#7f8c8d","其他":"#7f8c8d"};
const cOf = t => TYPE_COLOR[t] || "#7f8c8d";

const SORTS = ["街区顺序"];
const el = id => document.getElementById(id);
let myPos = null, myPosBase = null, current = null, filtered = SPOTS.slice();
/* 详情面板的初始占位内容：取消选中时原样还原（脚本位于 body 末尾，#detail 必然已存在） */
const DETAIL_HOME = el("detail") ? el("detail").innerHTML : "";

/* ---------- 地图投影（无需，改用 Leaflet 真实瓦片） ---------- */

function distKm(a,b,c,d){
  const R=6371, r=Math.PI/180;
  const dLat=(c-a)*r, dLng=(d-b)*r;
  const s=Math.sin(dLat/2)**2 + Math.cos(a*r)*Math.cos(c*r)*Math.sin(dLng/2)**2;
  return 2*R*Math.asin(Math.sqrt(s));
}

/* ---------- 筛选器 ---------- */
function buildFilters(){
  const areas = [...new Set(SPOTS.map(s=>s.ar))];
  const types = [...new Set(SPOTS.map(s=>s.ty))];
  el("fArea").innerHTML = '<option value="">全部区域</option>' + areas.map(a=>`<option value="${a}">${a}</option>`).join("");
  el("fType").innerHTML = '<option value="">全部类型</option>' + types.map(t=>`<option value="${t}">${t}</option>`).join("");
}

/* ---------- 地图绘制（Leaflet + 高德瓦片，GCJ-02 坐标天然对齐） ---------- */
let MAP=null, MLYR=null, FITTED=false;
function initMap(){
  MAP = L.map("map", {zoomControl:true, attributionControl:false}).setView([34.8025, 114.3450], 13);
  const url = "https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}";
  const tiles = L.tileLayer(url, {subdomains:["1","2","3","4"], maxZoom:18, minZoom:9});
  let okOnce=false;
  tiles.on("tileload", ()=>{ if(!okOnce){ okOnce=true; el("mapfail").classList.remove("on"); } });
  tiles.on("tileerror", ()=>{ if(!okOnce) el("mapfail").classList.add("on"); });
  tiles.addTo(MAP);
  MLYR = L.layerGroup().addTo(MAP);
  /* 点击地图空白处关闭详情。Leaflet 的 _findEventTargets 对 click/preclick 会先查 _draggableMoved()，
     拖动地图后不会触发 click；圆点点击已 stopPropagation，故此处只会在「真·点空白」时触发。 */
  MAP.on("click", ()=>{ if(current) deselect(); });
  setTimeout(()=>{ if(!okOnce) el("mapfail").classList.add("on"); MAP.invalidateSize(); }, 3500);
  window.addEventListener("resize", ()=>{ try{ MAP.invalidateSize(); }catch(_){} });
}
/* 红色五角星：仅用于本次住宿（唯一星标） */
function starIcon(sel){
  const s = sel?32:26;
  return L.divIcon({
    className:"", iconSize:[s,s], iconAnchor:[s/2,s/2],
    html:'<svg width="'+s+'" height="'+s+'" viewBox="0 0 24 24" style="filter:drop-shadow(0 1px 2px rgba(0,0,0,.35))"><polygon points="12,1.6 14.9,8.7 22.6,9.3 16.8,14.4 18.5,21.9 12,17.9 5.5,21.9 7.2,14.4 1.4,9.3 9.1,8.7" fill="#e11d48" stroke="#ffffff" stroke-width="1.9" stroke-linejoin="round"/></svg>'
  });
}
function renderMap(sel){
  if(!MAP) return;
  MLYR.clearLayers();
  /* 仅渲染「在地图上标注」的条目：offmap（其他酒店）不出点 */
  const pts = filtered.filter(s=>s.lat && !s.offmap);
  pts.forEach(s=>{
    const isHotel = !!s.star;
    const isSel = sel && sel.id===s.id;
    const approx = s.loc==="approx";
    let mk;
    if(isHotel){
      mk = L.marker([s.lat,s.lng], {icon:starIcon(isSel), zIndexOffset:1000});
    } else {
      mk = L.circleMarker([s.lat,s.lng], {
        radius: isSel?10:6.2,
        color: isSel? "#22201d" : (approx? cOf(s.ty) : "#ffffff"),
        weight: isSel?2.5:(approx?1.6:1.4),
        dashArray: approx? "3,2.6" : null,
        fillColor: cOf(s.ty),
        fillOpacity: approx? (isSel?.55:.3) : (isSel?1:.9)
      });
    }
    mk.bindTooltip((isHotel?"★ 本次住宿 · ":"") + s.n + (approx?" （区域近似）":""), {direction:"top", offset:[0,-6]});
    /* 再次点击同一个点 = 取消选中，让「打开 / 关闭」逻辑闭环 */
    mk.on("click", ev=>{ L.DomEvent.stopPropagation(ev); toggleSpot(s.id, true); });
    mk.addTo(MLYR);
  });
  if(!FITTED && pts.length){
    FITTED = true;
    try{ MAP.fitBounds(L.latLngBounds(pts.map(s=>[s.lat,s.lng])), {padding:[28,28], maxZoom:14}); }catch(_){}
  } else if(sel && sel.lat && !sel.offmap){
    MAP.panTo([sel.lat, sel.lng]);
  }
}

/* ---------- 列表渲染 ---------- */
function renderList(){
  const q=(el("q").value||"").trim().toLowerCase();
  const fa=el("fArea").value, ft=el("fType").value, ord=el("fOrder").value;
  filtered = SPOTS.filter(s=>{
    if(fa && s.ar!==fa) return false;
    if(ft && s.ty!==ft) return false;
    if(q){
      const hay=(s.n+s.ds+s.ad+s.rm+s.ar+s.ty).toLowerCase();
      if(!hay.includes(q)) return false;
    }
    return true;
  });
  if(ord==="dist" && myPos){
    filtered.sort((a,b)=>{
      const da=(a.lat&&!a.offmap)?distKm(myPos.lat,myPos.lng,a.lat,a.lng):1e9;
      const db=(b.lat&&!b.offmap)?distKm(myPos.lat,myPos.lng,b.lat,b.lng):1e9;
      return da-db;
    });
  } else if(ord==="area"){
    filtered.sort((a,b)=>a.ar.localeCompare(b.ar,"zh"));
  }
  el("list").innerHTML = filtered.map(s=>{
    let d = "";
    if(s.offmap){
      d = `<span class="noloc">不在地图标注</span>`;
    } else if(s.lat && myPos){
      const k=distKm(myPos.lat,myPos.lng,s.lat,s.lng);
      d = `<span class="dist">${k<1?(k*1000).toFixed(0)+" m":k.toFixed(1)+" km"}</span>`;
    } else if(s.loc==="approx"){
      d = `<span class="approx">区域近似</span>`;
    } else if(s.lat){
      d = `<span class="dist" style="color:#8a857e;background:rgba(0,0,0,.045)">未算距离</span>`;
    } else {
      d = `<span class="noloc">未定位</span>`;
    }
    const hotel = s.star ? '<span class="badge">★ 本次住宿</span>' : "";
    return `<div class="card${current&&current.id===s.id?" active":""}" data-id="${s.id}">
      <div class="top">
        <div><div class="nm">${s.n}${hotel}<button class="cp" title="复制店名" aria-label="复制店名">复制</button></div>
          <div><span class="tag" style="color:${cOf(s.ty)};border-color:${cOf(s.ty)}44;background:${cOf(s.ty)}12">${s.ty}</span><span class="tag" style="color:#75706a;border-color:rgba(0,0,0,.14)">${s.ar}</span></div>
        </div>
        <div>${d}</div>
      </div>
      ${s.ds?`<div class="ds">🍽 ${s.ds}</div>`:""}
      ${s.rm?`<div class="rm">💬 ${s.rm}</div>`:""}
      <div class="ad">📍 ${s.ad||"—"}${s.src?` · 来源 ${s.src}`:""}</div>
    </div>`;
  }).join("");
  el("list").querySelectorAll(".card").forEach(n=>{
    const id=+n.dataset.id;
    let dx=0,dy=0;
    n.addEventListener("mousedown",e=>{dx=e.clientX;dy=e.clientY;});
    n.addEventListener("click",e=>{
      /* 若指针位移>4px，视为「拖选文字」，不触发卡片选中（方便手动复制文本） */
      if(Math.abs(e.clientX-dx)>4||Math.abs(e.clientY-dy)>4) return;
      toggleSpot(id,false);
    });
    const cp=n.querySelector(".cp");
    if(cp) cp.addEventListener("click",e=>{ e.stopPropagation(); e.preventDefault(); copySpot(id,false); });
  });
  el("s1").textContent = SPOTS.length;
  el("s2").textContent = SPOTS.filter(s=>s.lat && s.loc!=="approx" && !s.offmap).length;
  el("s3").textContent = SPOTS.filter(s=>!s.lat).length;
  if(el("s5")) el("s5").textContent = SPOTS.filter(s=>s.loc==="approx").length;
  const nOff = SPOTS.filter(s=>s.offmap).length;
  if(el("s6")){
    el("s6").textContent = nOff;
    el("s6wrap").style.display = nOff ? "" : "none";
  }
  showReset();
  const legendTypes=[...new Set(SPOTS.map(s=>s.ty))].slice(0,14);
  el("legend").innerHTML = legendTypes.map(t=>`<span><i style="background:${cOf(t)}"></i>${t}</span>`).join("")
    + `<span style="margin-left:6px;color:#8a6d3b"><i style="background:#fff;border:1.5px dashed #8a6d3b;width:10px;height:10px"></i>区域近似</span>`
    + `<span style="margin-left:6px;color:#e11d48"><svg width="11" height="11" viewBox="0 0 24 24" style="vertical-align:-1px"><polygon points="12,1.6 14.9,8.7 22.6,9.3 16.8,14.4 18.5,21.9 12,17.9 5.5,21.9 7.2,14.4 1.4,9.3 9.1,8.7" fill="#e11d48" stroke="#fff" stroke-width="1.9" stroke-linejoin="round"/></svg>本次住宿</span>`;
}

/* ---------- 选中 / 取消选中 ---------- */
/* 同一个条目再点一次即关闭 —— 地图圆点与清单卡片共用同一套开关逻辑，保证「打开/关闭」闭环 */
function toggleSpot(id, fromMap){
  if(current && current.id===id){ deselect(); return; }
  select(id, fromMap);
}
/* 关闭详情：清空选中 → 面板还原初始占位态 → 地图大点与清单高亮随 renderMap(null) 复位。
   注意不触碰 FITTED，地图视野保持用户当前位置，不跳回初始范围。 */
function deselect(){
  current = null;
  const d = el("detail");
  if(d){ d.innerHTML = DETAIL_HOME; d.classList.remove("flash"); }
  renderList(); renderMap(null);
}

/* ---------- 选中 ---------- */
function select(id, fromMap){
  current = SPOTS.find(s=>s.id===id);
  renderList(); renderMap(current);
  if(current){
    const nav = current.lat
      ? `<a href="https://uri.amap.com/marker?position=${current.lng},${current.lat}&name=${encodeURIComponent(current.n)}&src=kaifeng-food-map&coordinate=gaode&callnative=1" target="_blank" rel="noopener">➤ 高德地图打开</a> ｜ <a href="https://apis.map.qq.com/uri/v1/marker?marker=coord:${current.lat},${current.lng};title:${encodeURIComponent(current.n)}&referer=kaifeng-food-map" target="_blank" rel="noopener">腾讯地图打开</a>`
      : "";
    let dd="";
    if(current.lat && myPos){
      const k=distKm(myPos.lat,myPos.lng,current.lat,current.lng);
      dd=`<div class="kv">📐 距当前位置直线距离：<b>${k<1?(k*1000).toFixed(0)+" 米":k.toFixed(2)+" 公里"}</b></div>`;
    }
    const shot = current.img
      ? `<div class="shot"><img src="${current.img}" alt="来源截图" loading="lazy"><div class="shot-cap">来源截图：${current.src||"—"}（点击可放大核对）</div></div>`
      : "";
    el("detail").innerHTML = `<div class="dhead"><h3>${current.n}</h3><button class="dx" id="dclose" title="关闭详情（也可再次点击该地点，或点地图空白处）" aria-label="关闭详情">✕</button></div>
      <div class="cps"><button class="cp2" data-kind="name">📋 复制店名</button><button class="cp2" data-kind="full">📋 复制名称 + 地址</button></div>
      <div class="kv">类型：${current.ty} ｜ 区域：${current.ar}</div>
      ${current.star?'<div class="kv" style="color:#e11d48">★ <b>本次行程住宿</b>（地图上唯一的红色五角星标记）</div>':""}
      ${current.offmap?'<div class="kv" style="color:#8a6d3b">ℹ️ <b>不在地图标注</b>：该处为推荐列表中提及的其他酒店，非本次行程住宿，故地图上不出点；数据与来源截图仍保留，便于回溯。</div>':""}
      ${current.loc==="approx"?'<div class="kv" style="color:#8a6d3b">⚠️ <b>区域近似</b>：该店在地图上无独立 POI（多为夜市/园内摊位），坐标按所属区域大致标注，供规划动线参考，<b>到店前请以实际为准</b>。</div>':""}
      ${shot}
      <div class="kv">地址：${current.ad||"—"}</div>
      ${current.lat?`<div class="kv">坐标：${current.lat.toFixed(6)}, ${current.lng.toFixed(6)}</div>`:'<div class="kv">坐标：未检索到</div>'}
      ${current.ds?`<div class="kv">推荐：${current.ds}</div>`:""}
      ${current.rm?`<div class="kv">点评：${current.rm}</div>`:""}
      ${dd}
      <div class="kv">来源截图：${current.src||"—"}</div>
      ${nav?`<div class="kv" style="margin-top:8px">${nav}</div>`:""}`;
    el("detail").querySelectorAll(".cp2").forEach(b=>b.addEventListener("click",e=>{
      e.preventDefault(); e.stopPropagation(); copySpot(current.id, b.dataset.kind==="full");
    }));
    const dc = el("dclose");
    if(dc) dc.addEventListener("click", e=>{ e.preventDefault(); e.stopPropagation(); deselect(); });
    if(!fromMap){
      /* 在清单里点选：若该卡片不在滚动区视野内，就把它滚到中间 */
      scrollCardIntoPane(document.querySelector(`.card[data-id="${id}"]`));
    } else {
      /* 从地图点选：详情固定在右栏顶部，只做高亮提示 */
      const d=el("detail");
      if(d){
        d.classList.add("flash");
        setTimeout(()=>d.classList.remove("flash"),900);
      }
    }
  }
}

/* 把卡片滚到清单滚动区中央；已完整可见则不动。
   注意：不用 behavior:"smooth" —— 部分环境（无头/禁用合成器）不会驱动平滑滚动动画，
   会导致"点了没反应"。这里用确定性赋值，保证一定滚到位。 */
function scrollCardIntoPane(card){
  const pane = el("pane");
  if(!pane || !card) return;
  const cr = card.getBoundingClientRect(), pr = pane.getBoundingClientRect();
  if(cr.top >= pr.top - 1 && cr.bottom <= pr.bottom + 1) return;   /* 已完整可见 */
  const want = pane.scrollTop + (cr.top - pr.top) - (pane.clientHeight - cr.height)/2;
  const max  = pane.scrollHeight - pane.clientHeight;
  pane.scrollTop = Math.max(0, Math.min(want, max));
}

/* ---------- 页内提示（替代 alert） ---------- */
let _toastT=null;
function toast(title,body,opt){
  opt=opt||{};
  const box=(function(){
    let b=el("toast");
    if(!b){ document.body.insertAdjacentHTML("beforeend",'<div class="toast" id="toast"></div>'); b=el("toast"); }
    return b;
  })();
  box.className="toast on"+(opt.ok?" ok":"");
  box.innerHTML='<div class="tt"><span>'+title+'</span><span class="x" id="tx">✕</span></div><div class="tb">'+body+'</div>'
    +(opt.hotel?'<div class="acts"><button class="p" id="toastHotel">🏨 改用酒店为基准算距离</button><button id="toastClose">知道了</button></div>':"");
  const close=()=>box.classList.remove("on");
  const x=el("tx"); if(x) x.onclick=close;
  const tc=el("toastClose"); if(tc) tc.onclick=close;
  const th=el("toastHotel"); if(th) th.onclick=()=>{ close(); useHotel(); };
  clearTimeout(_toastT);
  _toastT=setTimeout(close, opt.hotel?18000:6500);
}
/* ---------- 复制到剪贴板（优先 API，失败回退 execCommand，兼容 file:// 双击打开） ---------- */
const esc = s => String(s==null?"":s).replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function copyText(t, okMsg){
  const done = ()=>toast("复制成功", okMsg, {ok:true});
  const fail = ()=>toast("复制失败","浏览器未允许自动复制。请手动选中文字后按 <code>Ctrl + C</code>（Mac：<code>⌘ + C</code>）。");
  /* 通道一：同步 execCommand —— 桌面端（含 file:// 双击打开）必定同步返回结果，
     不会出现「点了没反应」。 */
  let okd=false;
  try{
    const ta=document.createElement("textarea");
    ta.value=t; ta.setAttribute("readonly","");
    ta.style.cssText="position:fixed;top:-1000px;left:0;opacity:0";
    document.body.appendChild(ta);
    ta.select(); ta.setSelectionRange(0, t.length);
    okd=document.execCommand("copy");
    document.body.removeChild(ta);
  }catch(err){ okd=false; }
  if(okd){ done(); return; }
  /* 通道二：异步 Clipboard API（iOS Safari 等），加 1.5s 超时兜底。
     无焦点窗口下该 Promise 可能永不 settle，超时后给明确提示而不是静默。 */
  const p = (navigator.clipboard && navigator.clipboard.writeText) ? navigator.clipboard.writeText(t) : null;
  if(!p){ fail(); return; }
  let settled=false;
  p.then(()=>{ if(!settled){ settled=true; done(); } })
   .catch(()=>{ if(!settled){ settled=true; fail(); } });
  setTimeout(()=>{ if(!settled){ settled=true; fail(); } }, 1500);
}
/* full=false 复制店名；full=true 复制「店名+地址」（便于直接发给同行的人） */
function copySpot(id, full){
  const s = SPOTS.find(x=>x.id===id);
  if(!s) return;
  if(full){
    const t = s.n + (s.ad ? "\n" + s.ad : "");
    copyText(t, "已复制名称与地址：<b>"+esc(s.n)+"</b><br>"+esc(s.ad||"—")
      +'<br><span style="color:#8a857e">可直接粘贴到微信 / 备忘录</span>');
  } else {
    copyText(s.n, "已复制店名：<b>"+esc(s.n)+"</b>");
  }
}

function useHotel(){
  const h=SPOTS.find(s=>s.lat && s.n.indexOf("汉庭")>=0);
  if(!h){ toast("未找到住宿坐标","数据中未检索到「汉庭酒店(开封鼓楼火车站店)」的坐标。"); return; }
  myPos={lat:h.lat,lng:h.lng}; myPosBase="hotel";
  el("geo").textContent="📍 获取我的位置并算距离";
  el("toHotel").textContent="🏨 已用酒店为基准";
  el("fOrder").value="dist";
  showReset();
  renderList(); renderMap(current);
  if(current) select(current.id,true);
  toast("已切换为酒店基准","所有条目的距离已改为「距汉庭酒店(开封鼓楼火车站店)的直线距离」，并按由近到远排序。",{ok:true});
}
function showReset(){
  const on = !!myPos;
  const b=el("resetDist"); if(b) b.style.display = on ? "" : "none";
  const s4=el("s4");
  if(s4) s4.innerHTML = on ? "距离基准：<b>"+(myPosBase==="hotel"?"汉庭酒店":"我的位置")+"</b>" : "距离：未获取定位";
}
el("resetDist").addEventListener("click",()=>{
  myPos=null; myPosBase=null;
  el("fOrder").value="def";
  el("geo").textContent="📍 获取我的位置并算距离";
  el("toHotel").textContent="🏨 以酒店为基准算距离";
  showReset();
  renderList(); renderMap(current);
  toast("已重置距离","已清除距离基准，列表恢复默认顺序、不再显示距离。可随时重新选择基准。",{ok:true});
});

/* ---------- 定位 ---------- */
el("geo").addEventListener("click",()=>{
  if(!navigator.geolocation){ toast("浏览器不支持定位","当前浏览器未提供定位接口。请改用「🏨 以酒店为基准算距离」。",{hotel:true}); return; }
  const host=location.hostname, proto=location.protocol;
  const secure = proto==="https:" || proto==="file:" || host==="localhost" || host==="127.0.0.1" || host==="[::1]" || host==="";
  if(!secure){
    toast("当前环境无法定位","浏览器只在 <b>HTTPS</b> 或 <b>localhost</b> 下允许网页定位。<br>当前地址：<code>"+proto+"//"+host+"</code><ul><li>改用本地服务器打开：在项目目录执行 <code>python -m http.server 8000</code>，再访问 <code>http://localhost:8000/</code></li><li>或直接点下方按钮，以酒店为基准算距离</li></ul>",{hotel:true});
    return;
  }
  const btn=el("geo"); const old=btn.textContent;
  btn.textContent="定位中…"; btn.disabled=true;
  navigator.geolocation.getCurrentPosition(p=>{
    btn.disabled=false; btn.textContent="📍 已获取定位";
    myPos={lat:p.coords.latitude,lng:p.coords.longitude}; myPosBase="me";
    el("fOrder").value="dist";
    showReset();
    renderList(); renderMap(current);
    if(current) select(current.id,true);
    toast("定位成功","已按你的当前位置计算直线距离，列表已切换为「距离最近」排序。点「↺ 重置距离」可随时清除。",{ok:true});
  },err=>{
    btn.disabled=false; btn.textContent=old;
    let t="定位失败", b="";
    if(err.code===1){
      t="定位权限被拒绝";
      b="浏览器拦截了本次定位授权（原始信息：<code>User denied Geolocation</code>），这是浏览器安全策略，并非页面故障。<ul>"
       +"<li>点地址栏左侧的 <b>🔒 / ⓘ</b> 图标 → 找到「位置信息」→ 改为「允许」→ 刷新页面后重试</li>"
       +"<li>若你是直接双击打开（地址以 <code>file://</code> 开头），部分浏览器会直接禁用定位，需改用本地服务器</li></ul>"
       +"不想设置也行——用下方按钮以酒店为基准算距离，效果一致。";
    } else if(err.code===2){ t="无法获取位置"; b="设备定位信号不可用（<i>"+err.message+"</i>）。请检查系统「定位服务 / 位置信息」是否已开启。"; }
    else if(err.code===3){ t="定位超时"; b="10 秒内未取到位置（<i>"+err.message+"</i>）。请重试，或改用酒店为基准。"; }
    else { t="定位失败"; b=(err.message||"未知错误"); }
    toast(t,b,{hotel:true});
  },{enableHighAccuracy:true,timeout:10000,maximumAge:60000});
});
el("toHotel").addEventListener("click",useHotel);
["q","fArea","fType","fOrder"].forEach(id=>{
  el(id).addEventListener("input",()=>{renderList();renderMap(current);});
  el(id).addEventListener("change",()=>{renderList();renderMap(current);});
});

buildFilters(); renderList(); initMap(); renderMap(null);

/* ---------- 来源截图放大预览 ---------- */
document.addEventListener("click",e=>{
  const img=e.target.closest(".shot img");
  if(img){ el("lbimg").src=img.src; el("lb").classList.add("on"); return; }
  if(e.target.id==="lb") e.target.classList.remove("on");
});
document.addEventListener("keydown",e=>{
  if(e.key!=="Escape") return;
  if(el("lb").classList.contains("on")){ el("lb").classList.remove("on"); return; }  /* 大图优先关闭 */
  if(current) deselect();
});
</script>
<div class="toast" id="toast"></div>
<div class="lb" id="lb"><img id="lbimg" alt="来源截图"></div>
</body>
</html>
'''

_vendor = os.path.join(ROOT, "脚本", "vendor")
_lcss = open(os.path.join(_vendor, "leaflet.css"), encoding="utf-8").read()
_ljs  = open(os.path.join(_vendor, "leaflet.js"),  encoding="utf-8").read()
html = (TPL.replace("__LEAFLET_CSS__", _lcss)
           .replace("__LEAFLET_JS__", _ljs)
           .replace("__DATA__", json.dumps(spots, ensure_ascii=False)))
out = os.path.join(ROOT, "开封美食地图.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("written", out, len(html), "chars")
