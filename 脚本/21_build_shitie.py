# -*- coding: utf-8 -*-
"""《汴京食帖》构建脚本 —— 第二版独立前端体验。

设计前提（决定实现方式的四个硬约束）：
  1) 不联网：原版底图走在线瓦片，断网即失效。本版自绘墨图，经纬投影 + 数据生成墨晕。
  2) 不造假：所有视觉变量必须能追溯到 data.json 的真实字段。
     墨分三色 = loc 字段三态（exact / approx / 未标）；城的轮廓 = 183 个落墨点的密度洇开。
  3) 不改旧版：只新增输出 汴京食帖.html，不动 开封美食地图.html 及其备份。
  4) 三色定调：宣纸 #F5F1E8 / 墨 #1F1B16 / 朱砂 #B03A2E。朱砂仅用于落印与选中。

输出：E:\\children‘s day file\\开封美食地图\\汴京食帖.html（单文件，数据内联）
"""
import json, os, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data.json")
OUT = os.path.join(ROOT, "汴京食帖.html")

data = json.load(open(SRC, encoding="utf-8"))

# ---------- 1. 派生：品类分组（覆盖 ty 全部 45 个取值，逐一断言） ----------
CAT_GROUPS = [
    ("汤", "汤羹", ["驴肉汤", "鸡血汤", "汤馆", "羊肉汤", "牛肉汤", "四味菜", "羊双肠", "早餐·胡辣汤", "早餐"]),
    ("包", "包子锅贴", ["灌汤包", "灌汤包·豫菜", "川菜·灌汤包", "锅贴·灌汤包", "锅贴"]),
    ("面", "面饭", ["面食", "米线", "烩菜", "砂锅"]),
    ("炙", "烧烤熟食", ["烧烤", "熟食", "熟食小吃", "牛羊肉"]),
    ("甜", "糕点甜饮", ["糕点小吃", "甜品", "饮品甜品"]),
    ("夜", "夜市", ["夜市", "夜市小吃", "宵夜", "外卖"]),
    ("正", "正餐", ["豫菜", "川菜", "烤鸭·豫菜", "火锅", "农家菜", "清真小吃", "西餐", "西式快餐", "简餐"]),
    ("杂", "杂项小食", ["小吃", "园内小吃", "园内正餐", "特产"]),
    ("处", "处所", ["景点", "地标", "住宿", "交通"]),
]
ALL_TY = sorted({x["ty"] for x in data})
CATMAP = {}
for k, _full, tys in CAT_GROUPS:
    for t in tys:
        CATMAP[t] = k
_missing = [t for t in ALL_TY if t not in CATMAP]
_ghost = [t for t in CATMAP if t not in ALL_TY]
assert not _missing, "未归组的 ty：%s" % _missing
assert not _ghost, "不存在的 ty：%s" % _ghost

# ---------- 2. 派生：市井（区域）分组，计数须与总数一致 ----------
AREA_GROUPS = [
    {"k": "qy",  "label": "清园",   "full": "清园内 · 清园周边", "core": "清明上河园", "ars": ["清园内", "清园周边"]},
    {"k": "gl",  "label": "鼓楼",   "full": "鼓楼书店街",        "core": "鼓楼·书店街", "ars": ["鼓楼书店街"]},
    {"k": "hd",  "label": "河大",   "full": "老河大",            "core": "老河大", "ars": ["老河大"]},
    {"k": "xg",  "label": "星光",   "full": "星光天地",          "core": "星光天地", "ars": ["星光天地"]},
    {"k": "dds", "label": "东大寺", "full": "东大寺",            "core": "东大寺", "ars": ["东大寺"]},
    {"k": "cy",  "label": "翠园",   "full": "翠园",              "core": "翠园", "ars": ["翠园"]},
    {"k": "xs",  "label": "西司",   "full": "西司",              "core": "西司夜市", "ars": ["西司"]},
    {"k": "dj",  "label": "东郊",   "full": "东郊夜市",          "core": "东郊夜市", "ars": ["东郊夜市"]},
    {"k": "bjy", "label": "汴京园", "full": "汴京公园",          "core": "汴京公园", "ars": ["汴京公园"]},
    {"k": "sj",  "label": "散记",   "full": "未定位 · 其他 · 零星", "core": None,
     "ars": ["未定位", "其他", "住宿", "交通", "苹果园", "集英花园", "东陈庄"]},
]
_ars_of = {a for g in AREA_GROUPS for a in g["ars"]}
_left = sorted({x["ar"] for x in data} - _ars_of)
assert not _left, "未归区的 ar：%s" % _left
_sum = sum(1 for x in data if any(x["ar"] in g["ars"] for g in AREA_GROUPS))
assert _sum == len(data), "区域分组漏 %d 条" % (len(data) - _sum)
for g in AREA_GROUPS:
    g["n"] = sum(1 for x in data if x["ar"] in g["ars"])

# ---------- 3. 派生：真实性统计（卷首实况句用） ----------
# 住处（星标）的归类要与 JS 端完全同源，否则墨样柱的计数会与图上实际差 1。
# 该记录没有 loc 字段，按缺省会并入「未标」，帖注便会对柒总的酒店说
# 「早期批次录入、数据集未标注精度来源」—— 与事实不符（src="柒总提供"、地址到门牌）。
# 它本不属于「网友帖子的坐标来源精度」这套统计，但坐标确实是确址，故显式归为确址。
def INK_OF(x):
    if x.get("star"):
        return 1
    return 1 if x.get("loc") == "exact" else (2 if x.get("loc") == "approx" else 3)


N_ALL = len(data)
N_MAP = sum(1 for x in data if isinstance(x.get("lat"), (int, float)) and isinstance(x.get("lng"), (int, float)))
N_EX = sum(1 for x in data if INK_OF(x) == 1)
N_AP = sum(1 for x in data if INK_OF(x) == 2)
N_NL = N_MAP - N_EX - N_AP
N_NO = N_ALL - N_MAP
assert N_MAP + N_NO == N_ALL
hotel = next(x for x in data if x.get("star"))

DATA_JS = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
CATMAP_JS = json.dumps(CATMAP, ensure_ascii=False, separators=(",", ":"))
AREA_JS = json.dumps(AREA_GROUPS, ensure_ascii=False, separators=(",", ":"))
META_JS = json.dumps({
    "nAll": N_ALL, "nMap": N_MAP, "nExact": N_EX, "nApprox": N_AP,
    "nUnmarked": N_NL, "nNomap": N_NO,
    "hotel": {"n": hotel["n"], "lat": hotel["lat"], "lng": hotel["lng"]},
}, ensure_ascii=False, separators=(",", ":"))

# ---------- 4. 样式 ----------
CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  background:#F5F1E8;color:#1F1B16;
  font-family:"Songti SC","STZhongsong","STSong","SimSun","Noto Serif SC",serif;
  font-size:15px;line-height:1.85;overflow:hidden;
  -webkit-font-smoothing:antialiased;
}
button,input{font-family:inherit;color:inherit}
button{background:none;border:none;cursor:pointer}
.mono{font-family:"JetBrains Mono","Cascadia Mono",Consolas,"Courier New",monospace;font-variant-numeric:tabular-nums}
#app{height:100vh;height:100dvh;display:flex;flex-direction:column;overflow:hidden}

/* ===== 卷首 ===== */
#head{
  flex:0 0 auto;height:58px;display:flex;align-items:center;gap:20px;
  padding:0 20px;border-bottom:1px solid #DCD3C0;position:relative;z-index:30;
}
.hd-t{display:flex;align-items:baseline;gap:12px;white-space:nowrap}
.hd-t h1{font-size:21px;font-weight:400;letter-spacing:5px}
.hd-t .zh{font-size:13px;color:#6E6353;letter-spacing:1px}
.hd-live{margin-left:auto;display:flex;align-items:center;gap:15px;font-size:12px;
  color:#6E6353;white-space:nowrap;overflow:hidden}
.hd-live b{font-weight:400;color:#1F1B16}
.hd-live .dot{display:inline-block;width:5px;height:5px;border-radius:50%;background:#B03A2E;
  vertical-align:2px;margin-right:5px}
#sndBtn{flex:0 0 auto;margin-left:16px;padding:5px 12px;border:1px solid #DCD3C0;border-radius:2px;
  background:#FBF8F1;font-size:12.5px;letter-spacing:2px;color:#6E6353;transition:all .2s;white-space:nowrap}
#sndBtn:hover{color:#1F1B16;border-color:#C9BFA9}
#sndBtn.on{color:#B03A2E;border-color:#DDB1A9;background:#FCF3F1}
#sndBtn.on::before{content:"♪ "}
.qw{position:relative;flex:0 0 auto}
#q{width:196px;padding:6px 10px 6px 27px;font-size:13.5px;border:1px solid #DCD3C0;
  border-radius:2px;background:#FBF8F1;color:#1F1B16}
#q:focus{outline:none;border-color:#B03A2E}
.qw::before{content:"寻";position:absolute;left:8px;top:50%;transform:translateY(-50%);
  font-size:12px;color:#A79B85;pointer-events:none}

/* ===== 三栏 ===== */
#mid{flex:1 1 auto;min-height:0;display:flex;position:relative}

#rail{
  flex:0 0 64px;border-right:1px solid #E2D9C6;writing-mode:vertical-rl;text-orientation:upright;
  display:flex;align-items:center;justify-content:flex-start;padding:10px 0;
  overflow-y:auto;overflow-x:hidden;z-index:10;
}
#rail::-webkit-scrollbar{width:0}
.rl{writing-mode:vertical-rl;text-orientation:upright;font-size:15.5px;letter-spacing:3px;
  color:#3A332B;padding:12px 0 12px 5px;margin:0;cursor:pointer;position:relative;
  transition:color .18s;white-space:nowrap}
.rl .c{font-size:10.5px;letter-spacing:0;color:#8A7C64;margin-right:3px;
  writing-mode:horizontal-tb;text-orientation:mixed;display:inline-block}
.rl:hover{color:#1F1B16}
.rl.on{color:#B03A2E}
.rl.on::before{content:"";position:absolute;right:-1px;top:9px;bottom:9px;width:2px;background:#B03A2E}
.rl.on .c{color:#C08A82}

#sheet{flex:1 1 auto;position:relative;min-width:0;overflow:hidden;display:flex}
#stage{flex:1 1 auto;position:relative;min-width:0;overflow:hidden}
/* 三层叠置：格线（底）→ 墨场（canvas）→ 墨点与标签（顶）。
   墨必须盖过格线，才像洇在纸上而不是画在格纸上。 */
.lyr{position:absolute;inset:0;display:block;width:100%;height:100%}
#inkBack{pointer-events:none}
/* 墨场是纯视觉层，不接任何输入 —— 它压在格线上、又被墨点压着，
   若还吃鼠标，空白处的点击就会落在一个「不属于墨图」的元素上，看上去像失灵。 */
#inkField{opacity:1;transition:opacity .5s linear;will-change:opacity;pointer-events:none}
#ink{cursor:grab;touch-action:none}
#ink.grab{cursor:grabbing}
#ink text{user-select:none;-webkit-user-select:none}
/* 层级未达的点退成影：不留描边、不留虚线圈，只余一层淡墨。
   否则全景下那些「白心虚圈」比实墨点还抢眼，反倒喧宾夺主。 */
#gDot .sh{fill:#7A6E5C;stroke:none;fill-opacity:.2}
/* 标签与范围框只做标注，不抢鼠标：抢了会让手型光标在字上消失，
   点选看上去就像失灵。点选本身已改为几何最近点，不依赖 e.target。 */
#gArea text,#gLbl text,#gScope{pointer-events:none}
/* 范围框：选中市井/品类时，把「这一片」圈出来 */
#gScope rect{fill:none;stroke:#B03A2E;stroke-width:1;stroke-dasharray:5 4;
  vector-effect:non-scaling-stroke;opacity:0;transition:opacity .34s ease}
#gScope.on rect{opacity:.62}
/* 字号/字距/描边一律不在这里写：SVG 里的裸数字是用户单位（公里），
   必须随缩放换算，交给 drawScope 与 apply 按 k 设。CSS 一旦写死，
   还会盖过 setAttribute，把题名撑到几公里宽。 */
#gScope text{fill:#B03A2E;paint-order:stroke;stroke:#F5F1E8;stroke-linejoin:round}

.ov{position:absolute;pointer-events:none;z-index:6;font-size:11.5px;color:#857A6C}
#north{left:16px;top:13px;display:flex;flex-direction:column;align-items:center;gap:1px}
#north .ar{font-size:15px;line-height:1;color:#4A423A}
#north .tx{font-size:10.5px}
#scale{left:16px;bottom:13px;display:flex;flex-direction:column;gap:4px}
#scale .bar{height:7px;border:1px solid #857A6C;border-top:none;position:relative}
#scale .bar span{position:absolute;left:50%;top:0;bottom:0;width:1px;background:#857A6C}
#foot-note{right:14px;bottom:13px;text-align:right;font-size:11.5px;color:#8A7C64;line-height:1.75}
#colophon{position:absolute;left:3%;top:50%;transform:translateY(-50%);z-index:6;
  pointer-events:none;writing-mode:vertical-rl;text-orientation:upright;
  font-size:13.5px;letter-spacing:4px;line-height:2.7;color:#5C5142;
  text-shadow:0 0 4px #F5F1E8,0 0 4px #F5F1E8,0 0 4px #F5F1E8;
  opacity:1;transition:opacity .55s ease}
#colophon.off{opacity:0}
#zoomctl{position:absolute;right:12px;top:11px;display:flex;flex-direction:column;z-index:8;
  align-items:center;gap:2px}
#zoomctl button{width:24px;height:22px;font-size:14px;color:#A79B85;transition:color .15s}
#zoomctl button:last-child{font-size:11.5px;letter-spacing:1px}
#zoomctl button:hover{color:#B03A2E}

#tip{position:fixed;z-index:60;pointer-events:none;opacity:0;transition:opacity .12s;
  background:#FBF8F1;color:#1F1B16;font-size:13.5px;padding:5px 11px;border-radius:2px;
  border:1px solid #B03A2E;box-shadow:0 3px 12px rgba(31,27,22,.2);
  white-space:nowrap;letter-spacing:.5px;max-width:62vw;overflow:hidden;text-overflow:ellipsis}
#tip.on{opacity:1}
#tip .m{font-size:11.5px;color:#857A6C;margin-left:7px}

/* ===== 帖页 ===== */
#note{flex:0 0 400px;width:400px;background:#FBF8F1;border-left:1px solid #DCD3C0;
  display:flex;flex-direction:column;z-index:12}
#note[hidden]{display:none}
.nh{flex:0 0 auto;display:flex;gap:12px;padding:17px 18px 13px;border-bottom:1px solid #E9E1D1}
.nh-l{flex:1 1 auto;min-width:0}
.nh h2{font-size:20px;font-weight:400;line-height:1.45;letter-spacing:.5px;word-break:break-word}
.nh .sub{margin-top:6px;font-size:12px;color:#857A6C;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.nh .sub i{font-style:normal}
.pill{border:1px solid #DCD3C0;border-radius:2px;padding:0 6px;font-size:11px;color:#6E6353;white-space:nowrap}
.pill.ex{border-color:#B03A2E;color:#B03A2E}
.pill.ap{border-color:#C08A5E;color:#9A6A38}
.seal{flex:0 0 auto;width:29px;background:#B03A2E;color:#FBF8F1;writing-mode:vertical-rl;
  text-orientation:upright;font-size:12.5px;letter-spacing:2px;display:flex;align-items:center;
  justify-content:center;padding:7px 0;line-height:1;max-height:112px;border-radius:1px}
#nClose{flex:0 0 auto;width:26px;height:26px;border:1px solid #DCD3C0;border-radius:2px;
  font-size:12px;color:#6E6353;transition:.15s}
#nClose:hover{border-color:#B03A2E;color:#B03A2E;background:#F6EDE9}
.nb{flex:1 1 auto;min-height:0;overflow-y:auto;padding:16px 19px 8px}
.nb::-webkit-scrollbar{width:8px}
.nb::-webkit-scrollbar-thumb{background:#DED5C3;border-radius:4px}
/* 帖心：一眼先读到的是别人的那句话，不是字段 */
.voice{position:relative;padding-left:24px;font-size:17.5px;line-height:2.05;
  color:#241F1A;letter-spacing:.4px;word-break:break-word}
.voice em{position:absolute;left:0;top:-1px;font-size:19px;font-style:normal;color:#B03A2E}
/* 闭引号必须回到行内，否则两个 em 都会被 absolute 拉到 left:0 叠在一起 */
.voice em.y{position:static;left:auto;top:auto;margin-left:1px}
.voice.none{font-size:15px;color:#B0A48D;padding-left:0;line-height:1.9}
.sig{margin-top:12px;text-align:right;font-size:11.5px;color:#A79B85;letter-spacing:1.5px}
.sig b{font-weight:400;color:#6E6353}
/* 校勘：数据集用「｜」把网友原话与编辑注记分开，这里正好分层 */
.hr{height:1px;background:#E9E1D1;margin:18px 0 12px;position:relative}
.hr i{position:absolute;left:0;top:-9px;background:#FBF8F1;padding-right:9px;
  font-style:normal;font-size:10.5px;color:#BEB3A0;letter-spacing:3px}
.anno{border-left:2px solid #E9E1D1;padding:1px 0 1px 11px;margin:7px 0;
  font-size:12.5px;line-height:1.85;color:#857A6C}
/* 帖注：事实写成小字夹注，不是表单项 */
.gl{display:flex;gap:12px;padding:4px 0;font-size:13.5px;line-height:1.8;color:#4A423A}
.gl>b{flex:0 0 44px;font-weight:400;font-size:11.5px;color:#A79B85;letter-spacing:1.5px;
  padding-top:3px;white-space:nowrap}
.gl>span{flex:1 1 auto;min-width:0;word-break:break-word}
.gl.soft{font-size:12.5px;color:#857A6C}
.gl.soft>b{color:#BEB3A0}
.thumb{margin-top:9px;display:block;width:100%;border:1px solid #E3DBC9;border-radius:1px;
  cursor:zoom-in;background:#EFE8D9;transition:border-color .18s}
.thumb:hover{border-color:#B03A2E}
.ph{color:#B0A48D}
.nf{flex:0 0 auto;display:flex;gap:7px;padding:11px 18px 13px;border-top:1px solid #E9E1D1}
.k{flex:1 1 0;padding:8px 4px;border:1px solid #DCD3C0;border-radius:2px;font-size:12.5px;
  color:#4A423A;transition:.15s;white-space:nowrap}
.k:hover:not([disabled]){border-color:#B03A2E;color:#B03A2E;background:#F6EDE9}
.k.on{background:#B03A2E;border-color:#B03A2E;color:#FBF8F1}
.k[disabled]{color:#C4B9A6;cursor:not-allowed}

/* ===== 卷尾 ===== */
#foot{flex:0 0 auto;height:46px;border-top:1px solid #DCD3C0;display:flex;align-items:center;
  padding:0 20px;position:relative;z-index:30;font-size:13.5px;overflow:hidden}
.fx{display:flex;align-items:baseline;gap:7px;white-space:nowrap}
.fx+.fx::before{content:"\00b7";color:#CBC0AC;margin:0 14px}
.fx.sp{margin-left:auto;color:#B9AE99;font-size:11.5px;letter-spacing:1px}
.fgl{font-size:11px;color:#A79B85;letter-spacing:1.5px}
.chip{font-size:13.5px;color:#4A423A;padding:3px 0;letter-spacing:1px;
  border-bottom:1px solid transparent;transition:.15s}
.chip:hover{color:#1F1B16}
.chip.on{color:#B03A2E;border-bottom-color:#B03A2E}
.chip .c{font-size:10.5px;color:#B9AE99;margin-left:3px;letter-spacing:0}
.chip.on .c{color:#C08A82}
.tx{font-size:13.5px;color:#4A423A;letter-spacing:1px;transition:.15s}
.tx:hover{color:#B03A2E}
.tx b{font-weight:400;color:#B03A2E;
  font-family:"JetBrains Mono",Consolas,monospace;font-size:12.5px}
.cnt{font-size:12px;color:#6E6353;font-family:"JetBrains Mono",Consolas,monospace}
/* 墨样柱：把「墨色三档」从页脚筛选器升为整幅图的脊柱，占满右缘 */
#inkcol{flex:0 0 56px;border-left:1px solid #E2D9C6;display:flex;flex-direction:column;
  justify-content:center;align-items:stretch;background:#F5F1E8;z-index:9}
.ik{display:flex;flex-direction:column;align-items:center;gap:6px;padding:17px 0;cursor:pointer;
  position:relative;transition:background .18s}
.ik:hover{background:#F0E9DA}
.ik .mk{display:block;transition:.2s}
.ik[data-v="1"] .mk{width:14px;height:14px;border-radius:50%;background:#1F1B16}
.ik[data-v="2"] .mk{width:14px;height:14px;border-radius:50%;background:#574D40}
.ik[data-v="3"] .mk{width:14px;height:14px;border-radius:50%;background:#F5F1E8;
  border:1px dashed #857A6C}
.ik .nm{writing-mode:vertical-rl;text-orientation:upright;font-size:13.5px;
  letter-spacing:3px;color:#3A332B}
.ik .ct{font-size:11.5px;color:#8A7C64;font-family:"JetBrains Mono",Consolas,monospace}
.ik.off .mk{opacity:.24}
.ik.off .nm,.ik.off .ct{opacity:.34}
.ik .mkinfo{position:absolute;right:100%;top:50%;transform:translateY(-50%);
  white-space:nowrap;background:#1F1B16;color:#F5F1E8;font-size:12px;padding:5px 10px;
  border-radius:2px;opacity:0;pointer-events:none;transition:opacity .16s;z-index:20;letter-spacing:.5px}
.ik:hover .mkinfo{opacity:1}
@media (max-width:900px){.ik .mkinfo{display:none}}
/* 「宿」不是墨色档，是原点：落一方朱印的样式，不可点，也不随闸门退影 */
.ik.origin{cursor:default}
.ik.origin:hover{background:transparent}
.ik.origin .mk{width:13px;height:13px;background:#B03A2E;
  box-shadow:0 0 0 3px #F5F1E8,0 0 0 4px #DDB1A9}
.ik.origin .nm{color:#B03A2E;letter-spacing:0}
.ikrule{height:1px;background:#E2D9C6;margin:0 14px}
.stamp{transform-box:view-box;animation:stamp .42s cubic-bezier(.2,1.4,.5,1) both}
@keyframes stamp{0%{transform:scale(1.55);opacity:0}60%{opacity:1}100%{transform:scale(1);opacity:1}}

/* ===== 浮层 ===== */
.pop{position:absolute;z-index:40;left:84px;bottom:62px;width:404px;max-width:calc(100vw - 104px);
  background:#FBF8F1;border:1px solid #DCD3C0;border-radius:2px;
  box-shadow:0 10px 34px rgba(31,27,22,.10);display:flex;flex-direction:column}
.pop[hidden]{display:none}
.pop-h{display:flex;align-items:center;gap:10px;padding:11px 14px;border-bottom:1px solid #E9E1D1}
.pop-h h3{font-size:14.5px;font-weight:400;letter-spacing:1.5px}
.pop-h .sub{font-size:11.5px;color:#A79B85;margin-left:auto}
.pop-b{overflow-y:auto;max-height:min(52vh,420px);padding:6px 0}
.pop-b::-webkit-scrollbar{width:8px}
.pop-b::-webkit-scrollbar-thumb{background:#DED5C3;border-radius:4px}
.pi{display:flex;align-items:center;gap:10px;padding:8px 14px;cursor:pointer;transition:background .15s}
.pi:hover{background:#F2ECDE}
.pi .no{flex:0 0 18px;text-align:center;font-size:11px;color:#B03A2E}
.pi .nm{flex:1 1 auto;min-width:0;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pi .ds{flex:0 0 auto;font-size:11.5px;color:#857A6C}
.pi .rm{flex:0 0 auto;font-size:12px;color:#B03A2E}
.pop-f{display:flex;gap:7px;align-items:center;padding:10px 14px;border-top:1px solid #E9E1D1}
.pop-f .k{flex:0 0 auto;padding:6px 12px}
.pop-f .sp{margin-left:auto;font-size:11.5px;color:#6E6353}
.wall{display:flex;flex-wrap:wrap;gap:9px;padding:14px;overflow-y:auto;max-height:min(46vh,340px)}
.wall b{width:15px;height:15px;border:1px dashed #B03A2E;border-radius:50%;cursor:pointer;
  transition:.15s;display:block}
.wall b:hover{background:rgba(176,58,46,.16);transform:scale(1.25)}

/* ===== 序幕 ===== */
#curtain{position:fixed;inset:0;z-index:200;background:#F5F1E8;display:flex;
  align-items:center;justify-content:center;transition:opacity .7s cubic-bezier(.4,0,.2,1)}
#curtain.gone{opacity:0;pointer-events:none}
.cu{text-align:center;padding:20px}
.seal4{width:96px;height:96px;margin:0 auto 30px;background:#B03A2E;border-radius:3px;
  display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;padding:9px;gap:2px;
  box-shadow:0 3px 16px rgba(176,58,46,.16);
  animation:land .7s cubic-bezier(.2,1.5,.5,1) both}
@keyframes land{0%{transform:scale(1.9) rotate(-7deg);opacity:0}55%{opacity:1}
  100%{transform:scale(1) rotate(0);opacity:1}}
.seal4 span{color:#FBF8F1;font-size:30px;line-height:1;display:flex;align-items:center;justify-content:center}
.cu h1{font-size:40px;font-weight:400;letter-spacing:14px;text-indent:14px;margin-bottom:13px}
.cu .cs{font-size:14.5px;color:#6E6353;letter-spacing:2px}
.cu .cstat{margin:20px auto 0;font-size:12px;color:#857A6C;line-height:2.1;max-width:540px}
.cu .cstat b{color:#B03A2E;font-weight:400}
.cu-btn{margin-top:28px;padding:11px 34px;border:1px solid #B03A2E;color:#B03A2E;font-size:15px;
  letter-spacing:6px;text-indent:6px;border-radius:2px;transition:.2s}
.cu-btn:hover{background:#B03A2E;color:#FBF8F1}
.cu-hint{margin-top:15px;font-size:11.5px;color:#B0A48D;letter-spacing:1px}

/* ===== 原图 ===== */
#light{position:fixed;inset:0;z-index:300;background:rgba(31,27,22,.9);display:flex;
  align-items:center;justify-content:center;padding:34px;cursor:zoom-out}
#light[hidden]{display:none}
#light img{max-width:100%;max-height:100%;border:1px solid rgba(245,241,232,.22);background:#F5F1E8}
#light .cap{position:absolute;left:0;right:0;bottom:18px;text-align:center;color:#C0B49C;font-size:12.5px}

@media (max-width:900px){
  #head{height:auto;padding:9px 13px;flex-wrap:wrap;gap:8px 12px}
  .hd-t h1{font-size:18px;letter-spacing:3px}
  .hd-t .zh,.hd-live{display:none}
  #sndBtn{margin-left:auto;padding:4px 9px;font-size:11.5px;letter-spacing:1px}
  .qw{flex:1 1 auto;width:100%;order:3}
  #q{width:100%}
  #mid{flex-direction:column}
  #rail{flex:0 0 46px;border-right:none;border-bottom:1px solid #E2D9C6;writing-mode:horizontal-tb;
    flex-direction:row;padding:0 8px;overflow-x:auto;overflow-y:hidden;align-items:center;
    justify-content:flex-start}
  .rl{writing-mode:horizontal-tb;padding:0 10px;margin:0;height:46px;display:flex;align-items:center;
    letter-spacing:1.5px;font-size:14px}
  .rl .c{margin:0 0 0 3px;transform:none}
  .rl.on::before{right:6px;left:6px;top:auto;bottom:6px;height:2px;width:auto}
  #sheet{min-height:104px}
  #note{position:static;flex:0 0 auto;width:100%;max-height:58%;border-left:none;
    border-top:1px solid #DCD3C0;box-shadow:none}
  #note .nh{padding:12px 14px 10px}
  #note .nh h2{font-size:17px}
  #note .nb{padding:13px 14px 6px}
  #note .nf{padding:9px 14px 11px}
  .voice{font-size:16px;padding-left:21px}
  .gl>b{flex:0 0 40px}
  #north,#scale,#foot-note,#colophon{display:none}
  #foot{height:auto;padding:7px 10px;flex-wrap:wrap;gap:3px 0;font-size:13px}
  .fx{white-space:normal;flex-wrap:wrap}
  .fx+.fx::before{margin:0 8px}
  .fx.sp{display:none}
  #cats{flex-wrap:wrap;gap:4px 11px}
  .chip{padding:1px 0;font-size:13px}
  .chip .c{font-size:10.5px}
  .fgl{font-size:10.5px}
  .pop{bottom:12px;max-height:70vh}
  #inkcol{flex:0 0 44px}
  .ik{padding:12px 0;gap:4px}
  .ik .nm{font-size:11.5px;letter-spacing:2px}
  .pop{left:12px;right:12px;width:auto;bottom:auto;top:12px}
  .cu h1{font-size:30px;letter-spacing:9px;text-indent:9px}
  .seal4{width:78px;height:78px;margin-bottom:22px}
  .seal4 span{font-size:24px}
}
"""

# ---------- 5. 脚本 ----------
JS = r"""
(function(){
"use strict";
var DATA=__DATA__, CATMAP=__CATMAP__, AREAS=__AREAS__, META=__META__;

/* ===== 1. 投影：等距圆柱 + 纬校。本城跨度 ~12km，误差可忽略 ===== */
var LAT0=34.80, KX=111.32*Math.cos(LAT0*Math.PI/180), KY=110.574;
var PTS=[], NO=[];
DATA.forEach(function(d){
  var ok=typeof d.lat==="number"&&isFinite(d.lat)&&typeof d.lng==="number"&&isFinite(d.lng);
  (ok?PTS:NO).push(d);
});
var LNG0=Infinity, LAT1=-Infinity;
PTS.forEach(function(d){ if(d.lng<LNG0)LNG0=d.lng; if(d.lat>LAT1)LAT1=d.lat; });
var XMAX=0, YMAX=0;
PTS.forEach(function(d){
  d._x=(d.lng-LNG0)*KX; d._y=(LAT1-d.lat)*KY;
  if(d._x>XMAX)XMAX=d._x; if(d._y>YMAX)YMAX=d._y;
});
var BX0=-0.65, BY0=-0.65, BX1=XMAX+0.65, BY1=YMAX+0.65, EX=1.05;

/* ===== 2. 归属：墨色（坐标来源精度）/ 品类 / 市井 / 是否处所 ===== */
var INKNAME={1:"确址",2:"约略",3:"未标"};
var INKDESC={
  1:"腾讯地图检索命中，坐标为 POI 实址。",
  2:"原帖未给独立 POI，按所属街区锚点落位，误差约 ±100 米。",
  3:"早期批次录入，数据集未标注精度来源，请按大致方位理解。"
};
function isHood(d){ return d.ty==="景点"||d.ty==="地标"||d.ty==="住宿"||d.ty==="交通"; }
PTS.forEach(function(d){
  /* 归类规则与构建脚本的 INK_OF 同源：住处（星标）是柒总给的门牌级实址，
     记录里没有 loc 字段，缺省并入「未标」会让帖注对它的信度说谎。 */
  d._ink=d.star?1:(d.loc==="exact"?1:d.loc==="approx"?2:3);
  d._cat=CATMAP[d.ty]||"杂";
  d._hood=isHood(d);
  d._anchor=d._hood;
  var g=AREAS.filter(function(x){return x.ars.indexOf(d.ar)>=0;});
  d._area=g.length?g[0].k:"sj";
});
NO.forEach(function(d){ d._ink=3; d._cat=CATMAP[d.ty]||"杂"; d._hood=isHood(d); });

/* ===== 3. DOM / 工具 ===== */
var $=function(s){ return document.querySelector(s); };
var sheet=$("#sheet"), stage=$("#stage"), svg=$("#ink"), tip=$("#tip"), note=$("#note");
var svgBack=$("#inkBack"), gGrid=$("#gGrid"), gWash=$("#gWash"), gArea=$("#gArea"),
    gRoute=$("#gRoute"), gDot=$("#gDot"), gLbl=$("#gLbl"), gScope=$("#gScope"), gHit=$("#gHit");
var HITPX=(window.matchMedia&&matchMedia("(pointer:coarse)").matches)?14:8.5;
var NS="http://www.w3.org/2000/svg";
function mk(tag,attrs,parent){
  var e=document.createElementNS(NS,tag),k;
  for(k in attrs) e.setAttribute(k,attrs[k]);
  if(parent) parent.appendChild(e);
  return e;
}
function esc(s){ return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;")
  .replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
var HOTEL=META.hotel;

/* ===== 4. 视图：cx,cy,w（h 由容器宽高比推出，保证 viewBox 与容器同比，无信箱边） ===== */
var VB={cx:(BX0+BX1)/2, cy:(BY0+BY1)/2, w:BX1-BX0, wOut:BX1-BX0, wIn:1};
function syncMax(){ VB.wIn=Math.max(0.55, VB.wOut/26); }
function W0(){ return stage.clientWidth||1; }
function H0(){ return stage.clientHeight||1; }
function stageRect(){ return stage.getBoundingClientRect(); }
function vbRect(){
  var h=VB.w*H0()/W0();
  return {x:VB.cx-VB.w/2, y:VB.cy-h/2, w:VB.w, h:h};
}
function pxPerKm(){ return W0()/VB.w; }
function clampVB(){
  /* 防御：任何一次 apply 都必须先有合法量纲，否则 NaN 会永久污染 cx/cy */
  if(!isFinite(VB.wOut)||VB.wOut<=0) VB.wOut=fitW();
  if(!isFinite(VB.wIn)||VB.wIn<=0) syncMax();
  if(!isFinite(VB.w)||VB.w<=0) VB.w=VB.wOut;
  if(!isFinite(VB.cx)) VB.cx=(BX0+BX1)/2;
  if(!isFinite(VB.cy)) VB.cy=(BY0+BY1)/2;
  VB.w=Math.min(VB.wOut,Math.max(VB.wIn,VB.w));
  var r=vbRect();
  if(r.w>=(BX1-BX0)+2*EX) VB.cx=(BX0+BX1)/2;
  else VB.cx=Math.min(BX1+EX-r.w/2, Math.max(BX0-EX+r.w/2, VB.cx));
  if(r.h>=(BY1-BY0)+2*EX) VB.cy=(BY0+BY1)/2;
  else VB.cy=Math.min(BY1+EX-r.h/2, Math.max(BY0-EX+r.h/2, VB.cy));
}
var sizedEls=[], gridEls=[], _raf=0, TIER=0;
function apply(){
  clampVB();
  var r=vbRect(), k=pxPerKm();
  var vb=r.x.toFixed(4)+" "+r.y.toFixed(4)+" "+r.w.toFixed(4)+" "+r.h.toFixed(4);
  svg.setAttribute("viewBox", vb);
  if(svgBack) svgBack.setAttribute("viewBox", vb);
  var i,e;
  for(i=0;i<dotEls.length;i++){
    e=dotEls[i]; var b=e.__b;
    if(b.t==="c") e.setAttribute("r",(b.px/k).toFixed(4));
    else { var s=b.px/k;
      e.setAttribute("x",(b.x-s/2).toFixed(4)); e.setAttribute("y",(b.y-s/2).toFixed(4));
      e.setAttribute("width",s.toFixed(4)); e.setAttribute("height",s.toFixed(4)); }
  }
  for(i=0;i<sizedEls.length;i++){
    e=sizedEls[i]; var q=e.__sz/k;
    if(e.__t==="c") e.setAttribute("r",q.toFixed(4));
    else { e.setAttribute("x",(e.__x-q/2).toFixed(4)); e.setAttribute("y",(e.__y-q/2).toFixed(4));
      e.setAttribute("width",q.toFixed(4)); e.setAttribute("height",q.toFixed(4)); }
  }
  for(i=0;i<PTS.length;i++) if(PTS[i]._wash) PTS[i]._wash.setAttribute("r",(WASH_R/k).toFixed(4));
  for(i=0;i<hitEls.length;i++) hitEls[i].setAttribute("r",(HITPX/k).toFixed(4));
  for(i=0;i<lblEls.length;i++){
    var t=lblEls[i];
    t.setAttribute("font-size",((t.__fs||13.5)/k).toFixed(4));
    t.setAttribute("stroke-width",((t.__fs?4.6:4)/k).toFixed(4));
    t.setAttribute("y",(t.__y-(t.__up||8)/k).toFixed(4));
  }
  /* 市井名是图上的骨架，字号与对比必须压过墨点，才起得到指位作用 */
  for(i=0;i<areaEls.length;i++){
    areaEls[i].setAttribute("font-size",(17.5/k).toFixed(4));
    areaEls[i].setAttribute("letter-spacing",(2.8/k).toFixed(4));
    areaEls[i].setAttribute("stroke-width",(6.5/k).toFixed(4));
    /* 重心恰好落在墨团正中时，名字会被墨点围住；把名字抬到墨团上沿，
       像标签悬在墨上，既保住指位又保可读。 */
    if(areaEls[i].__y!=null) areaEls[i].setAttribute("y",(areaEls[i].__y-9/k).toFixed(4));
  }
  for(i=0;i<gridEls.length;i++){
    var g=gridEls[i];
    g.el.setAttribute("font-size",(10.5/k).toFixed(4));
    if(g.ax==="x") g.el.setAttribute("x",(g.base+4/k).toFixed(4));
    else { g.el.setAttribute("x",(g.base+4/k).toFixed(4)); g.el.setAttribute("y",(g.baseY-2/k).toFixed(4)); }
  }
  if(gScope.__lbl){
    gScope.__lbl.setAttribute("font-size",(12/k).toFixed(4));
    gScope.__lbl.setAttribute("letter-spacing",(2.5/k).toFixed(4));
    gScope.__lbl.setAttribute("stroke-width",(4/k).toFixed(4));
    gScope.__lbl.setAttribute("y",(gScope.__by-7/k).toFixed(4));
  }
  var co=document.getElementById("colophon");
  if(co) co.classList.toggle("off", VB.w < VB.wOut*0.92);
  if(!_raf){ _raf=requestAnimationFrame(function(){
    _raf=0;
    drawField();
    var t=tierOf(), fo=t===1?1:(t===2?0.62:0.12);
    if(fieldEl&&fieldEl.__fo!==fo){ fieldEl.__fo=fo; fieldEl.style.opacity=fo; }
    if(t!==TIER){ TIER=t; refresh(); }
    drawScale(); declutter();
  }); }
}

/* ===== 5. 墨相：城由落墨点密度自己洇成 =====
   两重表达，随缩放交接：
     · 墨场（canvas）—— 核密度累加出的连续墨色。远看，这是「城」，
       浓淡由真实分布决定，不再是逐个点各画各的同心圆。
     · 墨晕（svg）—— 单点在纸上洇开的一小圈。近看，这是「店」。
   早先四层同心圆逐点铺，全景下必然裂成「黑饼」与「孤环」两极，密度传不出来。 */
/* 单点墨晕取屏幕恒定半径 —— 它是「这一家在纸上洇开的一小圈」。若用世界坐标，
   拉近时会胀成一张大饼，把整片街都糊住（0.10km 在 4km 视野下＝直径 46px）。 */
var WASH_R=15, WASH_A=0.13;
function buildWash(){
  var frag=document.createDocumentFragment();
  PTS.forEach(function(d){
    d._wash=mk("circle",{cx:d._x.toFixed(4),cy:d._y.toFixed(4),r:0.01,
      fill:"#1F1B16","fill-opacity":WASH_A},frag);
  });
  gWash.appendChild(frag);
}

/* 墨场：核密度场，在屏幕空间作画。
   固定核半径无解 —— 核小了每点各自成孤岛、连不成城，核大了整张纸糊成灰雾。
   所以核要随密度自适应（变带宽 KDE）：孤零零一家，核小而实，是一个清楚的墨点；
   挤成一片的地方，核大而淡，彼此交叠才洇成一整块墨。密度的差别于是自己显形。 */
var fieldEl=$("#inkField"), fctx=fieldEl?fieldEl.getContext("2d"):null, _fGrads=[], _fDimG=null;
/* 档位由「邻居数」决定：0 档是一粒实墨（孤零零一家），6 档是一片大而淡的底墨
   （彼此交叠才连成城）。两端的差别必须拉足，中间才谈得上层次。 */
var FIELD_LEV=[[10,0.17],[18,0.28],[26,0.250],[34,0.205],[43,0.165],[53,0.132],[64,0.105]];
var FIELD_BAND=58;   /* 邻居统计半径（屏幕像素） */
function fieldGrad(rad,a){
  var key=rad+"_"+a, i;
  for(i=0;i<_fGrads.length;i++) if(_fGrads[i].k===key) return _fGrads[i].g;
  var g=fctx.createRadialGradient(0,0,0,0,0,rad);
  /* 高斯型衰减：边缘要柔，否则每个核都成了一枚「圆盘」，满图皆是圆。
     浓淡靠核的叠加去挣，不靠单个核的强度。 */
  g.addColorStop(0,"rgba(31,27,22,"+a+")");
  g.addColorStop(0.32,"rgba(31,27,22,"+(a*0.70)+")");
  g.addColorStop(0.60,"rgba(31,27,22,"+(a*0.34)+")");
  g.addColorStop(0.84,"rgba(31,27,22,"+(a*0.09)+")");
  g.addColorStop(1,"rgba(31,27,22,0)");
  _fGrads.push({k:key,g:g});
  return g;
}
/* 邻居数决定核的档位。183² 次距离比较，只在重绘时算一遍。 */
function computeNeighbors(k){
  var b2=FIELD_BAND*FIELD_BAND, n=PTS.length, i, j, a, b, dx, dy;
  for(i=0;i<n;i++){
    a=PTS[i]; var c=0;
    for(j=0;j<n;j++){
      if(i===j) continue;
      b=PTS[j];
      dx=(a._x-b._x)*k; dy=(a._y-b._y)*k;
      if(dx*dx+dy*dy<b2) c++;
    }
    a._nb=c;
  }
}
function drawField(){
  if(!fctx) return;
  var R=stageRect();
  var dpr=Math.min(2, window.devicePixelRatio||1);
  var W=Math.max(1,Math.round(R.width*dpr)), H=Math.max(1,Math.round(R.height*dpr));
  if(fieldEl.width!==W||fieldEl.height!==H){ fieldEl.width=W; fieldEl.height=H; _fGrads.length=0; _fDimG=null; }
  fctx.setTransform(1,0,0,1,0,0);
  fctx.clearRect(0,0,W,H);
  var r=vbRect(), k=pxPerKm(), cw=R.width, ch=R.height, gs=[], j;
  for(j=0;j<FIELD_LEV.length;j++) gs.push(fieldGrad(FIELD_LEV[j][0],FIELD_LEV[j][1]));
  var maxR=FIELD_LEV[FIELD_LEV.length-1][0];
  if(!_fDimG) _fDimG=fieldGrad(16,0.10);
  computeNeighbors(k);
  for(var i=0;i<PTS.length;i++){
    var d=PTS[i];
    var sx=(d._x-r.x)*k, sy=(d._y-r.y)*k;
    if(sx<-maxR||sx>cw+maxR||sy<-maxR||sy>ch+maxR) continue;
    /* 筛选未命中的点也留在墨场里，只是极淡 ——「未知从不消失，只是变淡」
       这条不该只管墨点，也该管城的形状。 */
    var dim=!match(d);
    var lv=Math.min(FIELD_LEV.length-1, Math.floor(d._nb/3));
    var rad=dim?16:FIELD_LEV[lv][0];
    fctx.setTransform(dpr,0,0,dpr, sx*dpr, sy*dpr);
    fctx.fillStyle=dim?_fDimG:gs[lv];
    fctx.fillRect(-rad,-rad,rad*2,rad*2);
  }
  fctx.setTransform(1,0,0,1,0,0);
}

/* 三级显示：远看是城，近看是店。越确定越早现身，越不确定越要走近。
   反过来也是「承认不知道」——虚圈要走近才看得见，而它一直在。 */
function tierOf(){ var t=VB.w/VB.wOut; return t>0.62?1:(t>0.28?2:3); }
/* 层级未达的点不隐藏，只退成极淡的影，融进墨场。 */
function tierOpacity(d,T){
  /* 住处不受分级门控。它不在三态体系里 —— 那套统计的是网友帖子的坐标来源精度，
     而住处是柒总给的门牌级实址，且是全篇「距住处 X km」的原点，须恒在。 */
  if(d.star) return 1;
  if(d._ink===1) return T>=2?1:0.92;
  if(d._ink===2) return T>=2?0.82:0.24;
  return T>=3?1:0.07;
}

/* ===== 6. 经纬网：真实刻度（0.02°≈1.83km / 0.01°≈1.11km） ===== */
function buildGrid(){
  var k=pxPerKm(), i, lng, lat, t;
  for(i=0;i<14;i++){
    lng=Math.floor(LNG0*50)/50 + i*0.02;
    var x=(lng-LNG0)*KX;
    if(x>XMAX+0.3) break;
    mk("line",{x1:x.toFixed(3),y1:(BY0-1).toFixed(3),x2:x.toFixed(3),y2:(BY1+1).toFixed(3),
      stroke:"#DFD6C4","stroke-width":1,"vector-effect":"non-scaling-stroke"},gGrid);
    t=mk("text",{x:(x+4/k).toFixed(3),y:(BY1+0.30).toFixed(3),fill:"#A79B85",
      "font-family":"'JetBrains Mono',Consolas,monospace"},gGrid);
    t.textContent=lng.toFixed(2)+"E";
    gridEls.push({el:t,ax:"x",base:x,baseY:BY1+0.30});
  }
  for(i=0;i<10;i++){
    lat=Math.ceil((LAT1-0.005)*100)/100 - i*0.01;
    if(lat<LAT1-YMAX/KY) break;
    if(lat>LAT1) continue;
    var y=(LAT1-lat)*KY;
    mk("line",{x1:(BX0-1).toFixed(3),y1:y.toFixed(3),x2:(BX1+1).toFixed(3),y2:y.toFixed(3),
      stroke:"#DFD6C4","stroke-width":1,"vector-effect":"non-scaling-stroke"},gGrid);
    t=mk("text",{x:(BX0+4/k).toFixed(3),y:(y-2/k).toFixed(3),fill:"#A79B85",
      "font-family":"'JetBrains Mono',Consolas,monospace"},gGrid);
    t.textContent=lat.toFixed(2)+"N";
    gridEls.push({el:t,ax:"y",base:BX0,baseY:y});
  }
}

/* ===== 7. 市井名：取该区落墨点的真实重心 ===== */
var areaEls=[];
function buildAreaNames(){
  AREAS.forEach(function(g){
    if(!g.core) return;
    var pts=PTS.filter(function(d){return d._area===g.k;});
    if(pts.length<4) return;
    var cx=0,cy=0;
    pts.forEach(function(d){cx+=d._x;cy+=d._y;});
    cx/=pts.length; cy/=pts.length;
    var t=mk("text",{x:cx.toFixed(3),y:cy.toFixed(3),fill:"#5C5142","text-anchor":"middle",
      stroke:"#F5F1E8","paint-order":"stroke","stroke-linejoin":"round",
      "stroke-width":6.5,"stroke-opacity":"1"},gArea);
    t.textContent=g.core;
    t.__x=cx; t.__y=cy; t.__n=pts.length; t.__k=g.k;
    t.style.display="none";
    areaEls.push(t);
  });
}

/* ===== 8. 墨点 ===== */
var dotEls=[], byEl={};
var DOTPX={1:6.2,2:5.3,3:4.5};
function buildDots(){
  var frag=document.createDocumentFragment();
  PTS.forEach(function(d){
    var e,b;
    if(d._hood){
      /* 住处（星标）：先在身下铺一枚纸色圆垫，把鼓楼那片最密的墨团压出
         一小块干净纸面，再落印。它是全篇「距住处 X km」的原点，
         必须比任何一个墨点先被看见 —— 否则它就被自己周围的墨吃掉了。
         圆垫与墨点同走 dotEls 的尺寸通道（drawRoute 会清空 sizedEls）。 */
      if(d.star){
        var pad=mk("circle",{cx:d._x.toFixed(4),cy:d._y.toFixed(4),r:0.1,
          fill:"#F5F1E8","pointer-events":"none",class:"pad"},frag);
        pad.__b={t:"c",px:28,x:d._x,y:d._y};
        /* 走墨点的尺寸通道，但它不是墨点 —— 故带 .pad 类，
           核验统计落墨点数时须排除，否则 183 会被读成 184。 */
        dotEls.push(pad);
      }
      b={t:"r",px:d.star?13:7.6,x:d._x,y:d._y};
      e=mk("rect",{x:d._x,y:d._y,width:0.1,height:0.1,
        fill:d.star?"#B03A2E":"#F5F1E8",stroke:"#B03A2E",
        "stroke-width":d.star?0:1.6,"vector-effect":"non-scaling-stroke"},frag);
    } else {
      b={t:"c",px:DOTPX[d._ink],x:d._x,y:d._y};
      var att={cx:d._x.toFixed(4),cy:d._y.toFixed(4),r:0.04,
        "vector-effect":"non-scaling-stroke"};
      if(d._ink===3){ att.fill="#F5F1E8"; att.stroke="#7A6E5C";
        att["stroke-width"]=1.7; att["stroke-dasharray"]="2.6 2.4"; }
      else { att.fill=d._ink===1?"#1F1B16":"#574D40";
        att["fill-opacity"]=d._ink===1?1:0.8;
        att.stroke=d._ink===1?"#B03A2E":"#8C8070";
        att["stroke-width"]=d._ink===1?1.1:0.9; }
      e=mk("circle",att,frag);
    }
    e.__b=b;
    e.setAttribute("data-id",d.id);
    e.style.cursor="pointer";
    dotEls.push(e); byEl[d.id]=e; d._el=e;
  });
  gDot.appendChild(frag);
  var hf=document.createDocumentFragment();
  PTS.forEach(function(d){
    var h=mk("circle",{cx:d._x.toFixed(4),cy:d._y.toFixed(4),r:0.04,fill:"#000",
      "fill-opacity":"0","pointer-events":"all"},hf);
    h.setAttribute("data-id",d.id);
    h.style.cursor="pointer";
    h.__hit=d; hitEls.push(h); d._hit=h;
  });
  gHit.appendChild(hf);
}
var hitEls=[];

/* ===== 9. 地名标签 ===== */
var lblEls=[];
function buildLabels(){
  var frag=document.createDocumentFragment();
  PTS.forEach(function(d){
    var t=mk("text",{x:d._x.toFixed(4),y:d._y.toFixed(4),fill:"#241F1A","text-anchor":"middle",
      stroke:"#F5F1E8","paint-order":"stroke","stroke-linejoin":"round","stroke-width":4,
      "font-size":13.5},frag);
    /* 隐藏必须用内联样式，不能用表现属性。表现属性优先级低于内联，
       而显隐协议全靠 el.style.display="" 来「显示」——空字符串只移除内联声明，
       一遇表现属性 display="none" 就回落成隐藏。此前点名层因此从未画出过一字。 */
    t.style.display="none";
    /* 住处的名字以「宿」起头并去掉括号里的分店后缀：它是原点，不是一家长名店铺。
       字号与抬升也比普通点名大一分，保证它在任何视野下都读得出来。 */
    if(d.star){
      t.textContent="宿 · "+d.n.replace(/[（(][^）)]*[）)]?/g,"");
      t.__fs=15.5; t.__up=16;
    } else {
      t.textContent=d.n.length>14?d.n.slice(0,13)+"…":d.n;
      t.__fs=13.5; t.__up=8;
    }
    t.__d=d; t.__y=d._y; t.__star=!!d.star;
    lblEls.push(t); d._lbl=t;
  });
  gLbl.appendChild(frag);
}
var _dt=0, _ddirty=false;
/* 避让诊断日志：只记住处标签（图上唯一的「原点」）每次摆位的遭遇。
   用途是让无头核验能判定它偶发消失，究竟是「这一次 declutter 被合并吞掉」，
   还是「几何上真的被别的标签挡住了」——两者修法完全不同。
   默认关闭（每帧调用的东西不该在成品里常态分配对象），由探针经 debug.dbgLog(true) 打开。 */
var _dlog=[], _dlogOn=false, _draf=0;
function drec(tag,nb,blk){
  if(!_dlogOn) return;
  if(_dlog.length>=60) _dlog.shift();
  _dlog.push({ms:Math.round(performance.now()),tag:tag,
    w:+VB.w.toFixed(3),T:tierOf(),nb:nb,blk:blk||null,
    /* dt：此刻 rAF 是否已被占（=已有一次 declutter 在途）；raf：body 真正执行过的累计次数。
       两者一起看，即可分辨「请求被合并吞掉」与「body 跑了但几何上没摆上」。 */
    dt:_dt,raf:_draf});
}
/* 避让改用真实文字包围盒（getBBox，单位为投影公里），
   早先用半径估算会把「东大寺」这种确实存在、只是夹在两簇之间的市井误杀。 */
function declutter(){
  if(_dt){ _ddirty=true; drec("merge",-1); return; }
  _dt=requestAnimationFrame(function(){
    _dt=0; _draf++;
    var k=pxPerKm(), r=vbRect(), pad=3.2/k, boxes=[], i, d, T=tierOf();
    function live(x){ return match(x) && (!!x.star || x._ink<=T); }
    lblEls.forEach(function(t){ t.style.display="none"; });
    areaEls.forEach(function(t){ t.style.display="none"; });

    function place(el,p){
      /* 同一枚标签会被多条优先级规则先后点到（选中项往往同时是锚点，锚点又是普通点），
         第二次摆放时它必然撞上自己上一次推入的框，于是把自己藏掉 ——
         症状就是「点开的那个点，名字反而消失了」。已显示的就不再摆第二次。 */
      if(el.style.display!=="none"){ if(el.__star) drec("early",boxes.length); return true; }
      el.style.display="";
      var b;
      try{ b=el.getBBox(); }catch(e){ el.style.display="none";
        if(el.__star) drec("bboxerr",boxes.length); return false; }
      var q={x:b.x-p, y:b.y-p, w:b.width+2*p, h:b.height+2*p};
      if(q.w<=0||q.h<=0){ el.style.display="none";
        if(el.__star) drec("zero",boxes.length); return false; }
      for(var m=0;m<boxes.length;m++){
        var o=boxes[m];
        if(q.x<o.x+o.w && q.x+q.w>o.x && q.y<o.y+o.h && q.y+q.h>o.y){
          el.style.display="none";
          if(el.__star) drec("blocked",boxes.length,
            [+o.x.toFixed(3),+o.y.toFixed(3),+o.w.toFixed(3),+o.h.toFixed(3)]);
          return false;
        }
      }
      boxes.push(q);
      if(el.__star) drec("placed",boxes.length);
      return true;
    }

    /* 1 当前选中 */
    if(st.sel && st.sel._lbl) place(st.sel._lbl, pad);
    /* 2 市井名：按规模排序，先落大盘，城市的骨架先立起来 */
    areaEls.slice().sort(function(a,b){ return b.__n-a.__n; }).forEach(function(t){
      var first=true, ol=t.style.display;
      t.style.display="";
      var b;
      try{ b=t.getBBox(); }catch(e){ t.style.display="none"; return; }
      /* 市井名是骨架，间距收得比普通点名紧，尽量让每个区都留下名字 */
      var q={x:b.x-pad*0.55, y:b.y-pad*0.55, w:b.width+pad*1.1, h:b.height+pad*1.1};
      if(q.w<=0||q.h<=0){ t.style.display="none"; return; }
      for(var m=0;m<boxes.length;m++){
        var o=boxes[m];
        if(q.x<o.x+o.w && q.x+q.w>o.x && q.y<o.y+o.h && q.y+q.h>o.y){
          t.style.display="none"; return;
        }
      }
      boxes.push(q);
    });
    /* 3 处所锚点名：住处最先占位（它是原点，让位给谁都不合理），
       其余按 景点>地标>住宿>交通 排序，最要紧的先出 */
    var RANK={"景点":0,"地标":1,"住宿":2,"交通":3};
    PTS.filter(function(x){ return x._anchor && live(x); })
       .sort(function(a,b){ return (RANK[a.ty]||9)-(RANK[b.ty]||9); })
       .forEach(function(x){ place(x._lbl, pad); });
    /* 4 拉近后补齐普通墨点名 */
    if(VB.w<VB.wOut/1.7){
      PTS.filter(function(x){
        return !x._anchor && live(x) &&
          x._x>r.x-0.3 && x._x<r.x+r.w+0.3 && x._y>r.y-0.3 && x._y<r.y+r.h+0.3;
      }).sort(function(a,b){
        if(a._ink!==b._ink) return a._ink-b._ink;
        return (b.rm||"").length-(a.rm||"").length;
      }).forEach(function(x){ place(x._lbl, pad); });
    }
    /* 收尾：记下住处标签在这一帧结束时的最终可见性。
       与上面的 placed/blocked 对照，就能分辨「被合并」与「被挡」。 */
    for(i=0;i<lblEls.length;i++) if(lblEls[i].__star){
      drec(lblEls[i].style.display==="none"?"endHID":"endOK",boxes.length); break; }
    /* 本帧体内若又收到过被合并掉的请求（筛选、缩放、关帖都可能发生在本帧绘制之后），
       必须补跑一次：否则那一次请求会被永久吞掉，标签停在上一个视野的位置上。
       只补跑一次即可 —— 再来的请求会走 guard 分支，落进下一帧。 */
    if(_ddirty){ _ddirty=false; declutter(); }
  });
}

/* ===== 10. 状态与筛选 ===== */
var st={area:"all", cat:"all", ink:3, q:"", sel:null, bag:[], locate:false};
function match(d){
  if(st.area!=="all"&&d._area!==st.area) return false;
  if(st.cat!=="all"&&d._cat!==st.cat) return false;
  if(d._ink>st.ink) return false;
  if(st.q){
    var q=st.q.toLowerCase();
    if((d.n+" "+d.ty+" "+d.ar+" "+d.ad+" "+d.ds+" "+d.rm).toLowerCase().indexOf(q)<0) return false;
  }
  return true;
}
function refresh(){
  var vis=0, un=0, T=tierOf();
  PTS.forEach(function(d){
    /* 「能不能点」与「亮不亮」是两件事，此前被 `live` 合成了一条。
       后果：全景下 150 个半墨／虚圈退成淡影，看着仍是墨点，点下去却毫无反应
       —— 交互被视觉分级剥夺了。分级该管的只是谁浓、谁有名字。 */
    var ok=match(d), hit=ok, lit=ok&&(!!d.star||d._ink<=T),
        isSel=!!(st.sel&&st.sel.id===d.id);
    if(ok) vis++;
    d._el.style.display="";
    d._el.style.transition="opacity .22s linear";
    d._el.style.opacity = ok?tierOpacity(d,T):(d._hood?"0.16":"0.09");
    d._el.style.pointerEvents=hit?"all":"none";
    if(d._hit) d._hit.style.pointerEvents=hit?"all":"none";
    if(!d._hood) d._el.classList.toggle("sh", d._ink>T && !d.star && !isSel);
    if(d._wash) d._wash.style.opacity = lit?"":(d._hood?"0.22":"0.15");
    if(!lit){ if(d.star) drec("hidByRefresh",-3); d._lbl.style.display="none"; }
  });
  NO.forEach(function(d){
    var ok=match(d);
    if(ok) un++;
    if(d._wel) d._wel.style.opacity=ok?"1":"0.22";
  });
  /* 选中项一律升到满墨：即便它是层级未达的淡影，点它即等于「走近它」，
     该现身时就得现身。.sh 是 CSS 类，会压过 presentation attribute，必须摘掉。 */
  if(st.sel){ if(st.sel._el){st.sel._el.style.opacity="1"; st.sel._el.style.pointerEvents="all";
      st.sel._el.classList.remove("sh");}
    st.sel._lbl.style.display=""; }
  $("#cnt").innerHTML=vis+(un?'<span style="color:#B03A2E">＋'+un+'</span>':'')+
    (st.q?' <span style="color:#B9AE99;font-size:10.5px">命中</span>':'');
  $("#noSub").textContent=un===META.nNomap
    ? ("原帖未给位置 · 共 "+META.nNomap+" 家")
    : ("原帖未给位置 · 当前筛选命中 "+un+" / "+META.nNomap);
  drawField();   /* 墨场的浓淡也要跟着筛选走，否则「退墨成影」只影了墨点 */
  if(fieldEl) fieldEl.style.opacity = T===1?1:(T===2?0.62:0.12);
  syncScope();
  declutter();
}

/* ===== 11. 缩放/拖拽 ===== */
function zoomAt(cx,cy,f){
  var R=stageRect(), r=vbRect(), k=pxPerKm();
  var kx=r.x+(cx-R.left)/k, ky=r.y+(cy-R.top)/k;
  var nw=Math.min(VB.wOut,Math.max(VB.wIn,VB.w*f)), rt=nw/VB.w;
  VB.w=nw; VB.cx=kx+(VB.cx-kx)*rt; VB.cy=ky+(VB.cy-ky)*rt;
  apply();
}
function zoomBtn(f){
  var R=stageRect(); zoomAt(R.left+R.width/2,R.top+R.height/2,f);
}
var drag=null, lastDragMove=false;
svg.addEventListener("mousedown",function(e){
  if(e.button!==0) return;
  drag={x:e.clientX,y:e.clientY,cx:VB.cx,cy:VB.cy,moved:false};
  svg.classList.add("grab");
});
window.addEventListener("mousemove",function(e){
  if(!drag) return;
  var k=pxPerKm();
  if(Math.abs(e.clientX-drag.x)+Math.abs(e.clientY-drag.y)>3) drag.moved=true;
  VB.cx=drag.cx-(e.clientX-drag.x)/k; VB.cy=drag.cy-(e.clientY-drag.y)/k;
  apply();
});
window.addEventListener("mouseup",function(){
  lastDragMove=!!(drag&&drag.moved);
  drag=null; svg.classList.remove("grab");
});
svg.addEventListener("wheel",function(e){
  e.preventDefault();
  zoomAt(e.clientX,e.clientY,Math.exp(e.deltaY*0.0013));
},{passive:false});
svg.addEventListener("dblclick",function(e){
  zoomAt(e.clientX,e.clientY,e.shiftKey?2.1:1/2.1);
});
var tp=null;
svg.addEventListener("touchstart",function(e){
  if(e.touches.length===1){
    tp={m:"p",x:e.touches[0].clientX,y:e.touches[0].clientY,cx:VB.cx,cy:VB.cy};
  } else if(e.touches.length===2){
    var a=e.touches[0],b=e.touches[1];
    tp={m:"z",d:Math.max(1,Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY)),w:VB.w,
      mx:(a.clientX+b.clientX)/2,my:(a.clientY+b.clientY)/2,cx:VB.cx,cy:VB.cy};
  }
},{passive:true});
svg.addEventListener("touchmove",function(e){
  if(!tp) return;
  e.preventDefault();
  var R=stageRect(), r=vbRect(), k=pxPerKm();
  if(tp.m==="p"&&e.touches.length===1){
    VB.cx=tp.cx-(e.touches[0].clientX-tp.x)/k;
    VB.cy=tp.cy-(e.touches[0].clientY-tp.y)/k;
  } else if(tp.m==="z"&&e.touches.length===2){
    var a=e.touches[0],b=e.touches[1];
    var d=Math.max(1,Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY));
    var kx=r.x+(tp.mx-R.left)/k, ky=r.y+(tp.my-R.top)/k;
    var nw=Math.min(VB.wOut,Math.max(VB.wIn,tp.w*tp.d/d)), rt=nw/tp.w;
    VB.w=nw; VB.cx=kx+(tp.cx-kx)*rt; VB.cy=ky+(tp.cy-ky)*rt;
  }
  apply();
},{passive:false});
svg.addEventListener("touchend",function(){ tp=null; },{passive:true});

/* ===== 12. 平移补间 ===== */
var anim=0;
function flyTo(x,y,w){
  cancelAnimationFrame(anim);
  var t0=performance.now(), dur=560,
      c0=VB.cx, d0=VB.cy, w0=VB.w,
      c1=x, d1=y, w1=Math.max(VB.wIn,Math.min(VB.wOut,w==null?VB.w:w));
  (function step(t){
    var p=Math.min(1,(t-t0)/dur), e=1-Math.pow(1-p,3);
    VB.cx=c0+(c1-c0)*e; VB.cy=d0+(d1-d0)*e; VB.w=w0+(w1-w0)*e;
    apply();
    if(p<1) anim=requestAnimationFrame(step);
  })(t0);
}

/* ===== 12b. 范围：选择即视野 =====
   点一个市井或品类，地图直接落到「这一片」——视野与朱砂细框同步交代范围。
   宽度取自命中点的真实包围盒 + 留白，再按容器宽高比校正
   （扁的画幅要占更宽的范围才装得下同一片地方）。 */
function bboxOf(pts){
  var x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;
  pts.forEach(function(d){
    if(d._x<x0)x0=d._x; if(d._x>x1)x1=d._x;
    if(d._y<y0)y0=d._y; if(d._y>y1)y1=d._y;
  });
  return {x0:x0,x1:x1,y0:y0,y1:y1};
}
function focusOn(pts){
  if(!pts||!pts.length) return;
  var b=bboxOf(pts), w=b.x1-b.x0, h=b.y1-b.y0, AR=W0()/H0();
  var pad=Math.max(0.26, w*0.13);
  var need=Math.max(w+pad*2, (h+pad*2)*AR);
  flyTo((b.x0+b.x1)/2,(b.y0+b.y1)/2, Math.max(VB.wIn, Math.min(VB.wOut, need)));
}
function drawScope(pts,label){
  while(gScope.firstChild) gScope.removeChild(gScope.firstChild);
  gScope.__lbl=null;
  if(!pts||!pts.length){ gScope.classList.remove("on"); return; }
  var b=bboxOf(pts), pad=Math.max(0.16,(b.x1-b.x0)*0.09);
  var q={x:b.x0-pad, y:b.y0-pad, w:(b.x1-b.x0)+pad*2, h:(b.y1-b.y0)+pad*2};
  mk("rect",{x:q.x.toFixed(3),y:q.y.toFixed(3),width:q.w.toFixed(3),height:q.h.toFixed(3)},gScope);
  /* SVG 里的裸数字是「用户单位」＝公里，不是像素。题名的字号、字距、描边
     都必须按缩放换算，否则一个字能拉开几公里。 */
  var kk=pxPerKm();
  var t=mk("text",{x:q.x.toFixed(3),y:q.y.toFixed(3),fill:"#B03A2E",
    "font-size":(12/kk).toFixed(4),"letter-spacing":(2.5/kk).toFixed(4),
    "paint-order":"stroke",stroke:"#F5F1E8","stroke-width":(4/kk).toFixed(4),
    "stroke-linejoin":"round"},gScope);
  t.textContent=label||"";
  gScope.__lbl=t; gScope.__by=q.y;
  gScope.classList.add("on");
}
var _scopeKey="";
function syncScope(){
  var pts=null, label="";
  if(st.area!=="all"){
    pts=PTS.filter(function(d){return d._area===st.area;});
    var g=null;
    AREAS.forEach(function(a){ if(a.k===st.area) g=a; });
    label=(g?(g.core||g.full):"")+" · "+pts.length+" 家";
  } else if(st.cat!=="all"){
    pts=PTS.filter(function(d){return d._cat===st.cat;});
    label=st.cat+" · "+pts.length+" 家";
  }
  var key=st.area+"|"+st.cat+"#"+(pts?pts.length:"-");
  if(key===_scopeKey) return;
  _scopeKey=key;
  drawScope(pts,label);
}

/* ===== 13. 距离与朱砂线 ===== */
function dist(a,b){
  var la=(a.lat+b.lat)/2*Math.PI/180;
  return Math.hypot((a.lng-b.lng)*111.32*Math.cos(la),(a.lat-b.lat)*110.574);
}
function mapped(id){ return PTS.filter(function(d){return d.id===id;})[0]; }
function hotelXY(){ return {x:(HOTEL.lng-LNG0)*KX, y:(LAT1-HOTEL.lat)*KY}; }
function drawRoute(){
  while(gRoute.firstChild) gRoute.removeChild(gRoute.firstChild);
  sizedEls.length=0;
  var hp=hotelXY(), hx=hp.x, hy=hp.y;
  /* 朱砂线只在**用户主动要求**时才画（帖页里的「图上寻它」）。
     此前一开帖页就自动连线到住处 —— 那等于替用户把「这家离我多远」当成了他点开的意图，
     而他可能只是想知道这是家什么店。距离是问题，不是答案，得由他来问。 */
  if(st.locate&&st.sel&&st.sel._x!=null&&st.sel.id!==70){
    mk("line",{x1:hx.toFixed(3),y1:hy.toFixed(3),x2:st.sel._x.toFixed(3),y2:st.sel._y.toFixed(3),
      stroke:"#B03A2E","stroke-width":1.2,"stroke-dasharray":"5 4","stroke-opacity":".7",
      "vector-effect":"non-scaling-stroke"},gRoute);
    var c=mk("circle",{cx:hx.toFixed(3),cy:hy.toFixed(3),r:0.05,fill:"none",stroke:"#B03A2E",
      "stroke-width":1,"stroke-dasharray":"3 3","vector-effect":"non-scaling-stroke"},gRoute);
    c.__t="c"; c.__sz=5; c.__x=hx; c.__y=hy; sizedEls.push(c);
  }
  /* 落印：选中点加一圈朱砂方环（一次落印动画，非循环装饰） */
  if(st.sel&&st.sel._x!=null){
    var r=mk("rect",{x:0,y:0,width:0.1,height:0.1,fill:"none",stroke:"#B03A2E",
      "stroke-width":1.6,"vector-effect":"non-scaling-stroke"},gRoute);
    r.__t="r"; r.__sz=20; r.__x=st.sel._x; r.__y=st.sel._y;
    r.style.transformOrigin=st.sel._x.toFixed(3)+"px "+st.sel._y.toFixed(3)+"px";
    r.setAttribute("class","stamp");
    sizedEls.push(r);
  }
  var ids=st.bag.filter(function(id){ return !!mapped(id); });
  if(ids.length>1){
    var pts=ids.map(mapped), d="";
    pts.forEach(function(p,i){ d+=(i?" L":"M")+p._x.toFixed(3)+" "+p._y.toFixed(3); });
    mk("path",{d:d,fill:"none",stroke:"#B03A2E","stroke-width":1.5,"stroke-opacity":".82",
      "vector-effect":"non-scaling-stroke"},gRoute);
  }
  ids.forEach(function(id,i){
    var p=mapped(id);
    var r=mk("rect",{x:0,y:0,width:0.1,height:0.1,fill:"#B03A2E"},gRoute);
    r.__t="r"; r.__sz=11; r.__x=p._x; r.__y=p._y; sizedEls.push(r);
  });
  $("#bagN").textContent=st.bag.length;
  var bb=$("#btnBag"); bb.classList.toggle("on",st.bag.length>0);
  apply();
}

/* ===== 14. 帖页：帖心（人言）＋ 帖注（事实）＋ 校勘（meta） ===== */
function gl(k,v,soft){ return '<div class="gl'+(soft?" soft":"")+'"><b>'+k+'</b><span>'+v+'</span></div>'; }
function openNote(d){
  /* 每次翻开新的一帖，都回到「只读它的帖注」这一态 —— 不替用户连线、不替他走近。
     要不要在图上指出它的位置，是他接下来自己按的。 */
  st.sel=d; st.locate=false; note.hidden=false;
  voiceOf(d);   /* 翻开哪一家，就响哪一家的声 —— 市井定音高，品类定音色 */
  var has=d._x!=null, cls=d._ink===1?"ex":(d._ink===2?"ap":"");
  var seg=(d.rm||"").split("｜").map(function(t){return t.trim();}).filter(Boolean);
  var voice=seg[0]||"", meta=seg.slice(1);
  var h=[];

  /* 帖心 */
  if(voice) h.push('<p class="voice"><em>「</em>'+esc(voice)+'<em class="y">」</em></p>');
  else h.push('<p class="voice none">原帖未留评语。</p>');
  h.push('<div class="sig">'+esc(d.src||"—")+' · <b>'+INKNAME[d._ink]+'</b></div>');

  /* 校勘（仅当数据集确实分了层） */
  if(meta.length){
    h.push('<div class="hr"><i>校勘</i></div>');
    meta.forEach(function(t){ h.push('<p class="anno">'+esc(t)+'</p>'); });
  }

  /* 帖注 */
  h.push('<div class="hr"><i>帖注</i></div>');
  h.push(gl(d._hood?"所记":"吃食", (d.ds&&d.ds!=="——")?esc(d.ds):'<span class="ph">未记具体吃食</span>'));
  h.push(gl("品类", esc(d.ty)+(d._hood?'　<span style="color:#A79B85">处所</span>':"")+
    '　<span style="color:#A79B85">'+esc(d.ar)+'</span>'));
  if(has){
    h.push(gl("坐标",'<span class="mono" style="font-size:12.5px">'+d.lat.toFixed(6)+", "+
      d.lng.toFixed(6)+'</span>'));
    h.push(gl("地址", (d.ad?esc(d.ad):"—")));
    var km=dist(d,HOTEL);
    h.push(gl("距住处", km<0.005 ? '<span style="color:#857A6C">此处即住处</span>'
      : '<span class="mono" style="font-size:12.5px">'+km.toFixed(2)+' km</span>'+
        '<span style="color:#857A6C;font-size:12.5px"> 直线 · 自 '+esc(HOTEL.n)+'</span>'));
  } else {
    h.push(gl("坐标",'<span class="ph">原帖未给位置，本图未落墨</span>'));
  }
  /* 住处不在三态统计里：说它「腾讯地图检索命中」不实，说它「精度来源未标注」更不实。
     它自带一句准确的话。 */
  h.push(gl("信度", d.star ? "本次行程住处，坐标由行程主人提供，地址到门牌。" : INKDESC[d._ink], true));
  if(d.img){
    h.push('<div class="hr"><i>出处</i></div>');
    h.push('<p style="font-size:12.5px;color:#857A6C;margin-bottom:2px">原帖截图 '+esc(d.src)+'</p>'+
      "<img class='thumb' src='"+esc(d.img)+"' alt='原帖截图' loading='lazy' "+
      "data-src='"+esc(d.img)+"' data-cap='"+esc(d.n)+"'>");
  }

  note.querySelector(".nh").innerHTML=
    '<div class="nh-l"><h2>'+esc(d.n)+'</h2><div class="sub">'+
      '<span class="pill '+cls+'">'+INKNAME[d._ink]+'</span>'+
      '<i>'+esc(d.ar)+'</i><i>'+esc(d.ty)+'</i>'+
      '<i class="mono" style="font-size:11px;color:#A79B85">#'+d.id+'</i></div></div>'+
    '<div class="seal" title="所属市井">'+esc(d.ar.slice(0,6))+'</div>'+
    '<button id="nClose" title="合上（Esc）">合</button>';
  note.querySelector(".nb").innerHTML=h.join("");
  Array.prototype.forEach.call(note.querySelectorAll(".thumb"),function(im){
    im.onclick=function(){ showLight(im.dataset.src,im.dataset.cap); };
  });
  note.querySelector(".nb").scrollTop=0;
  $("#nClose").onclick=closeNote;
  var pb=$("#nPick"), inb=st.bag.indexOf(d.id)>=0;
  if(!has){ pb.disabled=true; pb.textContent="无处可落"; pb.classList.remove("on"); pb.onclick=null; }
  else{
    pb.disabled=false; pb.classList.toggle("on",inb);
    pb.textContent=inb?"已入行囊":"拾入行囊";
    pb.onclick=function(){ togglePick(d); };
  }
  $("#nCopyName").onclick=function(){ copy(d.n,"店名已抄"); };
  $("#nCopyPos").onclick=function(){
    if(!has){ toast("此家无坐标",true); return; }
    copy(d.lat.toFixed(6)+", "+d.lng.toFixed(6),"坐标已抄");
  };
  /* 「图上寻它」——把「在图上指出这家在哪」做成一个明确的手势，而不是开帖页的副作用。
     按下去才飞过去、才落那条朱砂直线；再按一次收回。无坐标者无处可指。 */
  var lb=$("#nLocate");
  lb.classList.remove("on");
  if(!has){ lb.disabled=true; lb.textContent="无处可指"; lb.onclick=null; }
  else{
    lb.disabled=false; lb.textContent="图上寻它";
    lb.onclick=function(){
      st.locate=!st.locate;
      lb.classList.toggle("on",st.locate);
      lb.textContent=st.locate?"收起朱线":"图上寻它";
      drawRoute();
      if(st.locate){
        snd("locate");
        /* 把「这家」与「住处」**同框** —— 朱砂线连着两端，只看得到一端就白连了。
           留白比 focusOn 宽一分（1.5×），因为这条线本身要看得出方向与长短；
           下限 wOut/9 是防呆：住在隔壁的店不该把视野怼到贴着门牌。 */
        var hp=hotelXY(), AR=W0()/H0(),
            dx=Math.abs(d._x-hp.x), dy=Math.abs(d._y-hp.y),
            need=Math.max(dx*1.5, dy*1.5*AR, VB.wOut/9);
        flyTo((d._x+hp.x)/2,(d._y+hp.y)/2, Math.max(VB.wIn, Math.min(VB.wOut, need)));
      }
      else snd("retract");
    };
  }
  drawRoute(); declutter();
}
function closeNote(){
  st.sel=null; st.locate=false; note.hidden=true;
  snd("fold");   /* 合上帖页：一声走开的短滑音，与「寻它」的落点相对 */
  /* 不再在这里「先把标签全藏一遍」。
     点名层的藏与摆是 declutter 一个人的事：它每帧先在体内全藏、再按优先级逐个占位。
     此前在此处抢先藏一次，就造出一个「已藏但尚未重摆」的空窗（约一帧），
     点空白处时满图名字会闪一下；更糟的是恢复全靠 declutter 的 requestAnimationFrame，
     一旦那次请求被合并吞掉，标签就永久停在隐藏态。 */
  drawRoute(); declutter();
}
function showLight(src,cap){
  var l=$("#light");
  l.querySelector("img").src=src;
  l.querySelector(".cap").textContent=cap+" · 原帖截图（点击任意处关闭）";
  l.hidden=false;
}
$("#light").onclick=function(){ this.hidden=true; };

/* ===== 15. 剪贴板 / 提示 ===== */
function copy(txt,msg){
  function fb(){
    try{
      var ta=document.createElement("textarea");
      ta.value=txt; ta.style.position="fixed"; ta.style.opacity="0";
      document.body.appendChild(ta); ta.select();
      document.execCommand("copy"); document.body.removeChild(ta); toast(msg);
    }catch(e){ toast("复制失败，请手动选取",true); }
  }
  try{
    if(navigator.clipboard&&navigator.clipboard.writeText)
      navigator.clipboard.writeText(txt).then(function(){toast(msg);},fb);
    else fb();
  }catch(e){ fb(); }
}
var tTimer=0;
/* 提示音：成事是四度上行的两记磬（确认），落空是一记钝梆。
   失败与成功必须听起来不一样 —— 否则「抄了」和「没抄到」是同一个声。 */
function toast(msg,miss){
  snd(miss?"miss":"copy");
  tip.innerHTML=msg;
  tip.classList.add("on");
  tip.style.left="50%"; tip.style.top="46%"; tip.style.transform="translate(-50%,-50%)";
  clearTimeout(tTimer);
  tTimer=setTimeout(function(){
    tTimer=0;
    if(tip.dataset.k==="t"){ tip.classList.remove("on"); tip.dataset.k=""; }
    tip.style.transform="";
  },1500);
  tip.dataset.k="t";
}

/* ===== 16. 行囊 ===== */
function saveBag(){ try{localStorage.setItem("shitie.bag",JSON.stringify(st.bag));}catch(e){} }
function loadBag(){
  try{ var s=localStorage.getItem("shitie.bag"); if(s) st.bag=JSON.parse(s)||[]; }catch(e){}
}
function togglePick(d){
  var i=st.bag.indexOf(d.id);
  if(i>=0) st.bag.splice(i,1); else st.bag.push(d.id);
  saveBag(); renderBag();
  snd(i>=0?"out":"into");   /* 「拾」是一记干脆的梆＋鼓，「取出」是一声走开的滑音 */
  if(st.sel&&st.sel.id===d.id){
    var pb=$("#nPick"), inb=st.bag.indexOf(d.id)>=0;
    pb.classList.toggle("on",inb); pb.textContent=inb?"已入行囊":"拾入行囊";
  }
  toast(i>=0?"已取出":"已入行囊");
}
function bagTotal(){
  var t=0, list=st.bag.filter(function(id){return !!mapped(id);});
  for(var i=1;i<list.length;i++) t+=dist(mapped(list[i-1]),mapped(list[i]));
  return t;
}
function renderBag(){
  var box=$("#bagList"),
      pts=st.bag.map(function(id){return DATA.filter(function(d){return d.id===id;})[0];}).filter(Boolean),
      lined=st.bag.filter(function(id){return !!mapped(id);});
  if(!pts.length){
    box.innerHTML='<div style="padding:22px 16px;color:#A79B85;font-size:13.5px">'+
      '行囊还是空的。<br>在墨图上点开任意一处，按「拾入行囊」，就能把它串成你自己的线。</div>';
  } else {
    var seq={};
    lined.forEach(function(id,i){ seq[id]=i+1; });
    box.innerHTML=pts.map(function(d){
      return '<div class="pi" data-id="'+d.id+'"><span class="no mono">'+
        (seq[d.id]?seq[d.id]:"·")+'</span><span class="nm">'+esc(d.n)+'</span>'+
        '<span class="ds">'+esc(d.ar)+'</span><span class="rm">取出</span></div>';
    }).join("");
    Array.prototype.forEach.call(box.querySelectorAll(".pi"),function(el){
      el.onclick=function(){
        var d=DATA.filter(function(x){return x.id===+el.dataset.id;})[0];
        togglePick(d);
      };
    });
  }
  $("#bagSum").innerHTML=pts.length
    ? (pts.length+" 处 · 连起来 "+bagTotal().toFixed(2)+" km")
    : "—";
  drawRoute();
}
$("#btnBag").onclick=function(){
  var p=$("#popBag");
  $("#popNo").hidden=true;
  p.hidden=!p.hidden;
  renderBag();
};
$("#bagClear").onclick=function(){ st.bag=[]; saveBag(); renderBag(); snd("out"); if(st.sel) openNote(st.sel); };
$("#bagCopy").onclick=function(){
  var pts=st.bag.map(function(id){return DATA.filter(function(d){return d.id===id;})[0];}).filter(Boolean);
  if(!pts.length){ toast("行囊是空的"); return; }
  var lines=pts.map(function(d,i){
    return (i+1)+"、"+d.n+"（"+d.ty+(d.rm?"，"+d.rm.slice(0,24):"")+"）";
  });
  lines.push("—");
  lines.push("直线首尾相连 "+bagTotal().toFixed(2)+" km；直线示意，非导航。");
  lines.push("数据来自《汴京食帖》，坐标精度不一，出行前请再核实。");
  copy(lines.join("\n"),"清单已抄");
};

/* ===== 17. 无处安放 ===== */
function renderNomap(){
  var w=$("#wall");
  w.innerHTML=NO.map(function(d){
    return "<b data-id='"+d.id+"' title='"+esc(d.n)+"'></b>";
  }).join("");
  Array.prototype.forEach.call(w.querySelectorAll("b"),function(el){
    var dd=NO.filter(function(x){return x.id===+el.dataset.id;})[0];
    if(dd) dd._wel=el;
    el.onclick=function(){
      var d=NO.filter(function(x){return x.id===+el.dataset.id;})[0];
      openNote(d);
      $("#popNo").hidden=true;
    };
  });
}
$("#btnNo").onclick=function(){
  var p=$("#popNo");
  $("#popBag").hidden=true;
  p.hidden=!p.hidden;
};

/* ===== 18. 目录 / 品类 / 墨色闸门 ===== */
function buildRail(){
  var r=$("#rail"),
      html='<div class="rl on" data-k="all">全<span class="c mono">'+META.nAll+'</span></div>';
  AREAS.forEach(function(g){
    html+='<div class="rl" data-k="'+g.k+'" title="'+esc(g.full)+'">'+g.label+
          '<span class="c mono">'+g.n+'</span></div>';
  });
  r.innerHTML=html;
  Array.prototype.forEach.call(r.querySelectorAll(".rl"),function(el){
    el.onclick=function(){ pickArea(el.dataset.k); };
  });
}
/* 选一片市井：目录上的高亮、视野落点、音级，都收在这一处 ——
   左侧目录与图上市井名共用它，同一个动作不会在两处说不一样的话。 */
function pickArea(k){
  var r=$("#rail");
  Array.prototype.forEach.call(r.querySelectorAll(".rl"),function(x){
    x.classList.toggle("on", x.dataset.k===k);
  });
  st.area=k;
  refresh();
  /* 换一片市井：长气定音区（听得出城在往哪边走），竹梆一记说明「换过了」 */
  if(sndOn&&AC){
    xiao(AREA_FREQ[k]?AREA_FREQ[k]*2:523.25, 0.055, 3.0);
    snd("area",{freq:AREA_FREQ[k]||261.63});
  }
  if(k==="all"){ flyTo((BX0+BX1)/2,(BY0+BY1)/2,VB.wOut); return; }
  /* 选定市井，视野即落到这一片 —— 不由用户再手动找 */
  focusOn(PTS.filter(function(d){return d._area===k;}));
}
var CATS=[["all","全"],["汤","汤"],["包","包"],["面","面"],["炙","炙"],
          ["甜","甜"],["夜","夜"],["正","正"],["杂","杂"],["处","处"]];
function catCount(k){
  return k==="all"?META.nAll:DATA.filter(function(d){return (CATMAP[d.ty]||"杂")===k;}).length;
}
function buildCats(){
  var box=$("#cats");
  box.innerHTML=CATS.map(function(c){
    return '<button class="chip'+(c[0]==="all"?" on":"")+'" data-k="'+c[0]+'">'+c[1]+
           '<span class="c">'+catCount(c[0])+'</span></button>';
  }).join("");
  Array.prototype.forEach.call(box.querySelectorAll(".chip"),function(el){
    el.onclick=function(){
      Array.prototype.forEach.call(box.querySelectorAll(".chip"),function(x){
        x.classList.remove("on"); x.querySelector(".c").style.display="none";
      });
      el.classList.add("on"); el.querySelector(".c").style.display="";
      st.cat=el.dataset.k; refresh();
      /* 音高与音色都取自该品类：汤沉而暗、炙亮而绵、甜清脆、处近钟。
         此前无论点哪一个，出来都是同一记 392Hz 的拨弦 —— 点遍九个 chip 听到的是一个音。 */
      var tn=CAT_TONE[el.dataset.k];
      if(sndOn&&AC){
        if(tn) pluck(329.63*tn[2], tn[0], 0.15, 1.6, tn[1]);
        else pluck(392.00,0.996,0.14,1.6,4000);   /* 「全」不带品类，返一个中性的音 */
      }
      /* 品类不带地理边界，就落在当前全部命中项的范围上 */
      focusOn(PTS.filter(match));
    };
    el.querySelector(".c").style.display="none";
  });
  box.querySelector('.chip[data-k="all"] .c').style.display="";
}
/* 墨样柱：三档墨色竖排在图右缘。收墨时未达档的墨点不退场，只退成影 ——
   未知从不消失，只是变淡。这是「墨分三色」落到交互上的关键一步。 */
var INKSEL=[
  {v:1,nm:"实墨",ct:META.nExact,tip:"确址 · 腾讯地图检索命中"},
  {v:2,nm:"半墨",ct:META.nApprox,tip:"约略 · 按街区锚点落位，±100 米"},
  {v:3,nm:"虚圈",ct:META.nUnmarked+"+"+META.nNomap,tip:"未标精度 · 80 家落墨 + 34 家无处安放"}
];
function buildGate(){
  var box=$("#inkcol"), html="";
  INKSEL.forEach(function(o,i){
    if(i) html+='<div class="ikrule"></div>';
    html+='<div class="ik" data-v="'+o.v+'" role="button" tabindex="0" title="'+esc(o.tip)+'">'+
      '<span class="mk"></span><span class="nm">'+o.nm+'</span>'+
      '<span class="ct">'+o.ct+'</span>'+
      '<span class="mkinfo">收墨至此 · '+esc(o.tip)+'</span></div>';
  });
  /* 末行是「宿」——它不是墨色档，而是原点。三档统计的是网友帖子的坐标来源精度，
     住处不在其列，却在全部「距住处 X km」里当原点，冷暖自知，须在图例里有一席之地。 */
  html+='<div class="ikrule"></div>'+
    '<div class="ik origin" title="本次行程住处 · 全部「距住处」以此为原点">'+
    '<span class="mk"></span><span class="nm">宿</span>'+
    '<span class="ct">原点</span>'+
    '<span class="mkinfo">本次行程住处 · 全部「距住处」以此为原点</span></div>';
  box.innerHTML=html;
  /* 只给墨色档绑闸门；「宿」不可点，它不是一道闸 */
  Array.prototype.forEach.call(box.querySelectorAll(".ik[data-v]"),function(el){
    var go=function(){ setInk(+el.dataset.v); };
    el.onclick=go;
    el.onkeydown=function(e){ if(e.key==="Enter"||e.key===" "){ e.preventDefault(); go(); } };
  });
  setInk(3);
}
function setInk(v){
  st.ink=v;
  Array.prototype.forEach.call(document.querySelectorAll(".ik[data-v]"),function(el){
    el.classList.toggle("off",(+el.dataset.v)>v);
  });
  refresh();
  /* 收墨一声。三档在**音高、时值、亮度**上同时分开：收到只剩确址时是一记干净利落的高磬，
     放到全显时是低而长的钟，中间那档居中并压一记低竹梆说明「又放了一格」。
     此前三档只有音高不同、时值一样，听着像同一口钟敲了三下。 */
  if(sndOn&&AC){
    var g=v===1?[1046.5,1.05,0.125]:(v===2?[784.0,1.85,0.14]:[523.25,3.0,0.155]);
    chime(g[0],g[2],g[1]);
    snd("ink",{freq:g[0]});
  }
}

/* 命中解析：取屏幕距离最近、且落在 HITPX 内的墨点。
   此前一律依赖 e.target —— 命中圈在密区互相压盖，谁在 DOM 里靠后谁赢，
   于是点甲店开出乙店的帖，连住处正中心都点不到自己（实测点到了 20 米外的邻居）。
   改成几何最近点：点哪家是哪家，悬停与点选共用同一口径，不会各说各话。
   #gHit 保留下来只做一件事 —— 让鼠标在这些点上变成手型（可点的先兆）。 */
function pickAt(cx,cy){
  var R=stageRect(), r=vbRect(), k=pxPerKm(), ox=R.left, oy=R.top,
      best=null, bd=HITPX*HITPX, i, d, dx, dy, q;
  for(i=0;i<PTS.length;i++){
    d=PTS[i];
    if(!match(d)) continue;
    dx=(d._x-r.x)*k-(cx-ox); dy=(d._y-r.y)*k-(cy-oy); q=dx*dx+dy*dy;
    if(q<=bd){ bd=q; best=d; }
  }
  return best;
}
/* 指下有没有「已经写出来的名字」。名字是图上最显眼的抓手，
   点它却毫无反应，最容易被当成整个页面坏了。
   避让已保证名字两两不相交，故至多命中一个 —— 不需要比远近。 */
function nameAt(cx,cy){
  var i, t, r;
  function inside(t){
    if(t.style.display==="none") return false;
    r=t.getBoundingClientRect();
    return cx>=r.left&&cx<=r.right&&cy>=r.top&&cy<=r.bottom;
  }
  for(i=0;i<lblEls.length;i++){ t=lblEls[i]; if(inside(t)) return {kind:"dot",d:t.__d}; }
  for(i=0;i<areaEls.length;i++){ t=areaEls[i]; if(inside(t)) return {kind:"area",k:t.__k}; }
  return null;
}

/* ===== 19. 悬停名牌 ===== */
document.addEventListener("mousemove",function(e){
  /* 只在指针确实落在图幅内时才解析，免得划过左侧目录也弹名牌 */
  var R=stageRect(), inMap=e.clientX>=R.left&&e.clientX<=R.right&&
                             e.clientY>=R.top&&e.clientY<=R.bottom;
  var d=inMap?pickAt(e.clientX,e.clientY):null, na=null;
  if(!d&&inMap){ na=nameAt(e.clientX,e.clientY); if(na&&na.kind==="dot") d=na.d; }
  if(d){
    tip.dataset.k="h";
    if(!tTimer){
      tip.classList.add("on");
      tip.style.left=(e.clientX+13)+"px";
      tip.style.top=(e.clientY-30)+"px";
      tip.style.transform="";
      tip.innerHTML=esc(d.n)+'<span class="m">'+INKNAME[d._ink]+" · "+esc(d.ar)+"</span>";
    }
  } else if(tip.dataset.k==="h"&&!tTimer){
    tip.classList.remove("on"); tip.dataset.k="";
  }
});
svg.addEventListener("mouseleave",function(){
  if(!tTimer&&tip.dataset.k==="h"){ tip.classList.remove("on"); tip.dataset.k=""; }
});

/* ===== 20. 点选 ===== */
svg.addEventListener("click",function(e){
  if(lastDragMove){ lastDragMove=false; return; }
  var d=pickAt(e.clientX,e.clientY);
  if(!d){
    /* 指下没有墨点，再看有没有名字：名字是最显眼的抓手，点它必须有着落 */
    var na=nameAt(e.clientX,e.clientY);
    if(na&&na.kind==="dot") d=na.d;
    else if(na){ pickArea(na.k); return; }   /* 点市井名＝选中这片市井，与左侧目录同一动作 */
    else { closeNote(); return; }            /* 点到空白＝收起帖页，不该毫无动静 */
  }
  if(st.sel&&st.sel.id===d.id){ closeNote(); return; }
  /* 点一枚墨点＝翻开这家的帖页，就这一件事。
     此前这里还顺带 flyTo 到 1.15km —— 于是「看一眼这是家什么店」被迫变成
     「凑近去看它离住处多远」，视野被夺走，想再看别处还得自己退回去。
     要不要走近，交给帖页里的「图上寻它」。 */
  openNote(d);
});

/* ===== 21. 比例尺 ===== */
var _sc=0;
function drawScale(){
  if(_sc) return; _sc=1;
  requestAnimationFrame(function(){
    _sc=0;
    var k=pxPerKm(), target=120, km=target/k,
        nice=[0.1,0.2,0.25,0.5,1,1.5,2,3,5,8], pick=nice[0];
    for(var i=0;i<nice.length;i++) if(nice[i]<=km) pick=nice[i];
    $("#scale .bar").style.width=Math.round(pick*k)+"px";
    $("#scale .tx").textContent=(pick<1?(pick*1000)+" 米":pick+" 公里");
  });
}

/* ===== 22. 键盘 ===== */
document.addEventListener("keydown",function(e){
  if(!opened){ openScroll(); }
  if(e.target.tagName==="INPUT"&&e.key!=="Escape") return;
  if(e.key==="Escape"){
    if(!$("#light").hidden){ $("#light").hidden=true; return; }
    if(!$("#popBag").hidden){ $("#popBag").hidden=true; return; }
    if(!$("#popNo").hidden){ $("#popNo").hidden=true; return; }
    if(!note.hidden){ closeNote(); }
    return;
  }
  if(e.key==="/"){ e.preventDefault(); $("#q").focus(); return; }
  if(e.key==="0"){ flyTo((BX0+BX1)/2,(BY0+BY1)/2,VB.wOut); return; }
  if(e.key==="+"||e.key==="="){ zoomBtn(1/1.6); return; }
  if(e.key==="-"||e.key==="_"){ zoomBtn(1.6); return; }
  if(e.key==="ArrowLeft"||e.key==="ArrowRight"){
    var list=PTS.filter(match);
    if(!list.length) return;
    var i=st.sel?list.indexOf(st.sel):-1;
    i=(e.key==="ArrowRight")?((i+1)%list.length):((i<=0)?list.length-1:i-1);
    var d=list[i];
    openNote(d);
    flyTo(d._x,d._y,Math.min(VB.w,1.2));
  }
});
$("#q").addEventListener("input",function(){ st.q=this.value.trim(); refresh(); });
$("#q").addEventListener("keydown",function(e){
  if(e.key==="Enter"){
    /* 搜出来的可能散在全城：先落到它们的范围上，再翻开最近的一条 */
    var list=PTS.filter(match), hit=list[0];
    if(hit){ focusOn(list); openNote(hit); }
    this.blur();
  }
  if(e.key==="Escape"){ st.q=""; this.value=""; refresh(); }
});
$("#zIn").onclick=function(){ zoomBtn(1/1.6); };
$("#zOut").onclick=function(){ zoomBtn(1.6); };
$("#zRe").onclick=function(){ flyTo((BX0+BX1)/2,(BY0+BY1)/2,VB.wOut); };
window.addEventListener("resize",function(){
  var old=VB.w;
  VB.wOut=fitW(); syncMax();
  VB.w=Math.max(VB.wIn,Math.min(VB.wOut,old));
  apply();
});

/* ===== 23. 浮层外点关闭 ===== */
document.addEventListener("mousedown",function(e){
  ["#popBag","#popNo"].forEach(function(id){
    var p=$(id);
    if(p.hidden) return;
    var t=e.target;
    if(p.contains(t)) return;
    if(t.closest&&(t.closest("#btnBag")||t.closest("#btnNo"))) return;
    p.hidden=true;
  });
});

/* ===== 24. 启动 ===== */
function fitW(){
  var pad=0.65, w=(BX1-BX0)+pad*2, h=(BY1-BY0)+pad*2;
  return Math.max(w, h*W0()/H0());
}
function start(){
  buildWash(); buildGrid(); buildAreaNames(); buildDots(); buildLabels();
  buildRail(); buildCats(); buildGate(); renderNomap(); loadBag(); renderBag();
  VB.wOut=fitW(); syncMax(); VB.w=VB.wOut;
  apply();
  $("#live").innerHTML=
    '<span><span class="dot"></span>共 <b>'+META.nAll+'</b> 家</span>'+
    '<span>确址 <b>'+META.nExact+'</b></span>'+
    '<span>约略 <b>'+META.nApprox+'</b></span>'+
    '<span>未标 <b>'+META.nUnmarked+'</b></span>'+
    '<span>无处安放 <b>'+META.nNomap+'</b></span>';
  $("#cuStat").innerHTML=
    "卷上 <b>"+META.nAll+"</b> 家 · 已落墨 <b>"+META.nMap+"</b> 家"+
    "（确址 <b>"+META.nExact+"</b> · 约略 <b>"+META.nApprox+"</b> · 未标 <b>"+META.nUnmarked+"</b>）<br>"+
    "<b>"+META.nNomap+"</b> 家原帖没给位置，只能悬在卷边 —— 这是这张图诚实的缺口。";
  gWash.style.opacity="0"; gWash.style.transition="opacity 1.15s ease-out";
  gArea.style.opacity="0"; gArea.style.transition="opacity 1s ease-out .45s";
  setTimeout(function(){ gWash.style.opacity="1"; gArea.style.opacity="1"; },160);
  var order=PTS.slice().sort(function(a,b){
    if(a._hood!==b._hood) return a._hood?-1:1;
    return a._ink-b._ink;
  });
  /* 逐点浮墨。落的终点不是「不透明」，而是这一档墨色在当前视图下该有的样子 ——
     否则开卷动画会把分级显示的透明度一并抹平。 */
  var T0=tierOf();
  order.forEach(function(d,i){
    var el=byEl[d.id], tgt=String(tierOpacity(d,T0));
    el.style.opacity="0"; el.style.transition="opacity .5s ease-out";
    setTimeout(function(){
      el.style.opacity=tgt;
      setTimeout(function(){ el.style.transition="opacity .22s linear"; },620);
    },110+i*2.2);
  });
  declutter();
}
var opened=false;
function openScroll(){
  if(opened) return; opened=true;
  var c=$("#curtain");
  c.classList.add("gone");
  setTimeout(function(){ c.style.display="none"; },760);
  setTimeout(function(){ apply(); },120);
  /* 展卷是这一程的第一次真手势，配乐由此起 —— 浏览器也只在手势里才准出声。
     此前若明说过不要（localStorage 记着），就不再自作主张。 */
  if(sndPref()!=="0"){
    setSound(true);
    setTimeout(function(){ chime(523.25,0.20,4.0); drum(0.20); },380);
  }
  firstLook();
}
/* 首次到访：不等用户猜，直接替他翻开一条帖 —— 而且是一条「确址」，
   让「墨色三档」第一次就落在实物上。此后不再打扰（localStorage 记忆）。 */
function firstLook(){
  var seen=false;
  try{ seen=localStorage.getItem("shitie.seen")==="1"; }catch(e){}
  if(seen) return;
  try{ localStorage.setItem("shitie.seen","1"); }catch(e){}
  setTimeout(function(){
    var d=PTS.filter(function(x){return x.id===47;})[0]||PTS[0];
    openNote(d);
    flyTo(d._x,d._y,Math.max(3.4,VB.wOut/2.4));
  },1160);
}
/* ===== 19. 市井有声 =====
   两层声音，都不是装饰，各自对应一件真事：
     · 一家店的声（voiceOf）—— 看的是"谁"。市井定音区、品类定音高与音色、墨色三态定虚实。
       汤沉而暗、炙亮而绵、甜清脆、处近钟；确址清亮，约略闷一分，未标只剩几不可闻的影。
       而三十四家无处安放本就没有位置，音也就飘着不落地。沉默也是信息。
     · 手势的声（snd）—— 看的是"你在做什么"。切换＝竹梆一击（不留尾），
       落点＝鼓，确认＝四度上行的两记磬，收回＝走开的滑音，落空＝一记钝梆。
   全部由 Web Audio 现场合成，不引一个音频文件 —— 作品仍是单文件、双击即开。 */
var AC=null, aMaster=null, sndOn=false, ambT=null, _plk={};
var PENTA=[261.63,293.66,329.63,392.00,440.00,523.25,587.33,659.25,783.99,880.00];
var AREA_FREQ={};
AREAS.slice().sort(function(a,b){ return b.n-a.n; }).forEach(function(g,i){
  AREA_FREQ[g.k]=PENTA[i%PENTA.length];
});
/* 品类 → 音色 [衰减, 低通, 音高乘数]。
   三项各管一件事：衰减＝余韵长短，低通＝明暗，乘数＝音高。
   乘数按「火候」排：汤最沉、炙最亮、甜最清脆、处最空 —— 同一个市井里
   卖汤与卖甜的店，出来的该是两个音，不是同一个音换个明暗。 */
var CAT_TONE={
  "汤":[0.9940,1900,0.86],"包":[0.9962,3900,0.94],"面":[0.9956,3200,0.90],
  "炙":[0.9974,6000,1.13],"甜":[0.9966,7000,1.19],"夜":[0.9980,2000,1.06],
  "正":[0.9960,3600,0.98],"杂":[0.9952,2800,1.02],"处":[0.9986,1400,1.25]
};
function sndPref(){ try{ return localStorage.getItem("shitie.snd"); }catch(e){ return null; } }
function makeIR(sec,decay){
  var sr=AC.sampleRate, len=Math.floor(sr*sec), b=AC.createBuffer(2,len,sr), c,i,d;
  for(c=0;c<2;c++){
    d=b.getChannelData(c);
    for(i=0;i<len;i++) d[i]=(Math.random()*2-1)*Math.pow(1-i/len,decay);
  }
  return b;
}
function audioInit(){
  if(AC) return AC;
  var C=window.AudioContext||window.webkitAudioContext;
  if(!C) return null;
  try{ AC=new C(); }catch(e){ return null; }
  aMaster=AC.createGain(); aMaster.gain.value=0;
  var lp=AC.createBiquadFilter(); lp.type="lowpass"; lp.frequency.value=5400;
  var conv=AC.createConvolver(); conv.buffer=makeIR(2.6,2.8);
  var wet=AC.createGain(); wet.gain.value=0.36;
  aMaster.connect(lp); lp.connect(AC.destination);
  lp.connect(conv); conv.connect(wet); wet.connect(AC.destination);
  return AC;
}
/* 拨弦：Karplus-Strong。一段噪声灌进延迟线，反复取平均衰减，
   出来的正是琴与筝的质地 —— 短促的起势，长长的余音。 */
function pluckBuf(freq,damp){
  var key=freq.toFixed(1)+"_"+damp.toFixed(4);
  if(_plk[key]) return _plk[key];
  var sr=AC.sampleRate, N=Math.max(2,Math.round(sr/freq)), len=Math.floor(sr*2.2);
  var buf=AC.createBuffer(1,len,sr), out=buf.getChannelData(0);
  var d=new Float32Array(N), i, n, i0, i1;
  for(i=0;i<N;i++) d[i]=Math.random()*2-1;
  for(n=0;n<len;n++){
    i0=n%N; i1=(n+1)%N;
    out[n]=d[i0];
    d[i0]=(d[i0]+d[i1])*0.5*damp;
  }
  var tail=Math.floor(sr*0.3);
  for(i=0;i<tail;i++) out[len-1-i]*=(tail-i)/tail;
  _plk[key]=buf;
  return buf;
}
function pluck(freq,damp,vol,dur,cut){
  if(!AC) return;
  var src=AC.createBufferSource();
  src.buffer=pluckBuf(freq,damp);
  var lp=AC.createBiquadFilter(); lp.type="lowpass"; lp.frequency.value=cut||4000;
  var g=AC.createGain(); g.gain.value=vol;
  src.connect(lp); lp.connect(g); g.connect(aMaster);
  src.start(); src.stop(AC.currentTime+dur);
}
/* 箫：气声长音，慢起慢落。这是这座城的底音，不是旋律。 */
function xiao(freq,vol,dur){
  if(!AC) return;
  var t=AC.currentTime;
  var g=AC.createGain();
  g.gain.setValueAtTime(0,t);
  g.gain.linearRampToValueAtTime(vol,t+dur*0.34);
  g.gain.linearRampToValueAtTime(vol*0.7,t+dur*0.66);
  g.gain.linearRampToValueAtTime(0.0001,t+dur);
  var lp=AC.createBiquadFilter(); lp.type="lowpass"; lp.frequency.value=freq*5;
  var o1=AC.createOscillator(), o2=AC.createOscillator(), g2=AC.createGain();
  var lfo=AC.createOscillator(), lg=AC.createGain();
  o1.type="sine"; o1.frequency.value=freq;
  o2.type="sine"; o2.frequency.value=freq*2;
  g2.gain.value=0.2;
  lfo.frequency.value=4.4; lg.gain.value=freq*0.007;
  lfo.connect(lg); lg.connect(o1.frequency);
  o1.connect(lp); o2.connect(g2); g2.connect(lp);
  lp.connect(g); g.connect(aMaster);
  [o1,o2,lfo].forEach(function(o){ o.start(t); o.stop(t+dur+0.1); });
}
/* 磬：钟的泛音比，起势短促，余韵极长。
   at 是相对现在的调度偏移（秒）—— 两声磬要叠成「确认音」时，必须落在采样时钟上，
   不能用 setTimeout 去凑：那是墙上时钟，会和音频时钟越走越偏。 */
function chime(freq,vol,dur,at){
  if(!AC) return;
  var t=AC.currentTime+(at||0), parts=[1,2.76,5.40,8.93];
  parts.forEach(function(p,i){
    var o=AC.createOscillator(), g=AC.createGain();
    o.type="sine"; o.frequency.value=freq*p;
    g.gain.setValueAtTime(0,t);
    g.gain.linearRampToValueAtTime(vol*Math.pow(0.40,i),t+0.008);
    g.gain.exponentialRampToValueAtTime(0.0001,t+dur*Math.pow(0.66,i));
    o.connect(g); g.connect(aMaster);
    o.start(t); o.stop(t+dur+0.1);
  });
}
/* 竹梆：带通噪声一击 ＋ 同频三角波点。木质、干脆、**不留尾**。
   专门给「切换」类手势用。切换必须一击即走：若带长余韵，连点几下时
   前一下的尾巴会叠在后一下上，听成一片糊 —— 那正是「切换音效听起来都一样」的来源。 */
function knock(freq,vol,dur){
  if(!AC) return;
  var t=AC.currentTime, sr=AC.sampleRate, d=dur||0.14,
      len=Math.max(8,Math.floor(sr*d)), i;
  var buf=AC.createBuffer(1,len,sr), a=buf.getChannelData(0);
  for(i=0;i<len;i++) a[i]=(Math.random()*2-1)*Math.pow(1-i/len,6);
  var src=AC.createBufferSource(); src.buffer=buf;
  var bp=AC.createBiquadFilter(); bp.type="bandpass";
  bp.frequency.value=freq; bp.Q.value=6.5;
  var hp=AC.createBiquadFilter(); hp.type="highpass"; hp.frequency.value=200;
  var g=AC.createGain(); g.gain.value=vol;
  src.connect(bp); bp.connect(hp); hp.connect(g); g.connect(aMaster);
  src.start(t); src.stop(t+d);
  var o=AC.createOscillator(), og=AC.createGain();
  o.type="triangle"; o.frequency.value=freq;
  og.gain.setValueAtTime(vol*0.45,t);
  og.gain.exponentialRampToValueAtTime(0.0001,t+d*0.85);
  o.connect(og); og.connect(aMaster);
  o.start(t); o.stop(t+d+0.05);
}
/* 滑音：音高由 f1 滑向 f2。用于「收回 / 放回」类手势 —— 与「落定」相对，
   声音自己走开，不再停在那儿。 */
function slide(f1,f2,vol,dur){
  if(!AC) return;
  var t=AC.currentTime, d=dur||0.6;
  var o=AC.createOscillator(), g=AC.createGain(), lp=AC.createBiquadFilter();
  o.type="sine";
  o.frequency.setValueAtTime(f1,t);
  o.frequency.exponentialRampToValueAtTime(Math.max(40,f2),t+d);
  lp.type="lowpass"; lp.frequency.value=Math.max(900,f1*4);
  g.gain.setValueAtTime(0.0001,t);
  g.gain.linearRampToValueAtTime(vol,t+d*0.16);
  g.gain.exponentialRampToValueAtTime(0.0001,t+d*1.3);
  o.connect(lp); lp.connect(g); g.connect(aMaster);
  o.start(t); o.stop(t+d*1.5);
}
/* 鼓：落印那一下 */
function drum(vol){
  if(!AC) return;
  var t=AC.currentTime;
  var o=AC.createOscillator(), g=AC.createGain();
  o.type="sine";
  o.frequency.setValueAtTime(150,t);
  o.frequency.exponentialRampToValueAtTime(44,t+0.3);
  g.gain.setValueAtTime(vol,t);
  g.gain.exponentialRampToValueAtTime(0.0001,t+0.46);
  o.connect(g); g.connect(aMaster);
  o.start(t); o.stop(t+0.6);
}
function ambStep(){
  if(!sndOn||!AC) return;
  var f=PENTA[Math.floor(Math.random()*PENTA.length)];
  if(Math.random()<0.3) f*=0.5;
  xiao(f,0.026+Math.random()*0.014,5.5+Math.random()*3.5);
  ambT=setTimeout(ambStep,6500+Math.random()*7500);
}
function setSound(on){
  sndOn=!!on;
  try{ localStorage.setItem("shitie.snd", sndOn?"1":"0"); }catch(e){}
  var b=$("#sndBtn");
  if(b){ b.classList.toggle("on",sndOn); b.setAttribute("aria-pressed",sndOn?"true":"false"); }
  if(sndOn){
    if(!audioInit()) return;
    if(AC.state==="suspended") AC.resume();
    aMaster.gain.cancelScheduledValues(AC.currentTime);
    aMaster.gain.setTargetAtTime(0.5,AC.currentTime,0.8);
    if(!ambT) ambT=setTimeout(ambStep,800);
  } else if(AC){
    aMaster.gain.cancelScheduledValues(AC.currentTime);
    aMaster.gain.setTargetAtTime(0,AC.currentTime,0.35);
    if(ambT){ clearTimeout(ambT); ambT=null; }
  }
}
/* 界面手势的声音。与「一家店的声音」分开：一个是你在做什么，一个是你在看谁。
   每个手势一个专属音色，且音高尽量取自这个动作真正涉及的数据 ——
   换一片市井，音高就是那片市井的音级；换一档墨，音高就是那一档的磬。
   此前拾入行囊、抄录、图上定位这些动作全都没有声音，而几处「切换」又都是同一记长音，
   连点几下分不出自己换了什么。 */
function snd(kind,arg){
  if(!sndOn||!AC) return;
  var f=(arg&&arg.freq)?arg.freq:329.63;
  switch(kind){
    case "area":    knock(f*2,0.075,0.16); break;        /* 换一片市井：竹梆一击，音高＝那片市井 */
    case "cat":     knock(f*2.6,0.07,0.13); break;        /* 换一类吃食：更高更薄，与换市井分开 */
    case "ink":     knock(f*0.5,0.055,0.10); break;       /* 收墨一档：低而钝，像把闸压下一格 */
    case "locate":  drum(0.13); pluck(f,0.9968,0.12,1.1,4400); break;   /* 在图上指出它：落点实 */
    case "retract": slide(f,f*0.62,0.062,0.5); break;     /* 收回朱线 */
    case "fold":    slide(f*0.8,f*0.5,0.055,0.42); break; /* 合上帖页 */
    case "into":    knock(659.3,0.085,0.12); drum(0.10); break;          /* 拾入行囊 */
    case "out":     slide(523.25,293.66,0.075,0.62); break;              /* 取出行囊 */
    case "copy":    chime(f,0.115,1.6); chime(f*1.4983,0.09,2.0,0.13); break;  /* 四度上行＝确认 */
    case "miss":    knock(174.6,0.055,0.10); break;       /* 落了空：一记钝梆，不是失望的装饰 */
    case "unmap":   xiao(f,0.05,4.2); break;              /* 无处安放：有声，但落不了地 */
    case "hood":    chime(f,0.10,2.8); drum(0.115); break;/* 处所：磬 ＋ 更实的落点 */
  }
}
/* 一家店的声音。市井定音级，品类定音色**并定音高**（九类九个音：汤沉、炙亮、甜清脆），
   墨色三态定虚实。品类乘数 CAT_MUL 之前不存在 —— 同一片市井里的店，
   无论卖汤还是卖甜，出来的是同一个音，只有音色略暗略亮之别。 */
function voiceOf(d){
  if(!sndOn||!AC||!d) return;
  /* 无处安放：原帖没给位置，也就没有市井归属 —— 给它一声飘着的低箫，不落定 */
  if(d._x==null){ snd("unmap",{freq:196}); return; }
  var f=AREA_FREQ[d._area]||PENTA[0];
  if(d._hood){ snd("hood",{freq:f*0.5}); return; }
  var tn=CAT_TONE[d._cat]||[0.996,3600,1];
  var vol=d._ink===1?0.30:(d._ink===2?0.19:0.10);
  pluck(f*tn[2],tn[0],vol,2.2,tn[1]);
}

start();

$("#cuBtn").onclick=openScroll;
$("#sndBtn").onclick=function(){ setSound(!sndOn); };
/* 记住上次的选择：关过的，这次不吵他 */
if(sndPref()==="1") $("#sndBtn").classList.add("on");
$("#curtain").addEventListener("click",function(e){ if(e.target===this) openScroll(); });
window.addEventListener("wheel",function(){ openScroll(); },{passive:true});
window.addEventListener("touchstart",function(){ openScroll(); },{passive:true});

/* 调试把手：仅供自动化探针调用，不参与界面逻辑 */
window.__shitie={VB:VB, st:st, PTS:PTS, NO:NO, DATA:DATA, AREAS:AREAS, CATS:CATS,
  openNote:openNote, closeNote:closeNote, togglePick:togglePick, renderBag:renderBag,
  openScroll:openScroll, apply:apply, match:match, setInk:setInk, refresh:refresh,
  byEl:byEl, setSound:setSound, voiceOf:voiceOf, chime:chime, snd:snd,
  knock:knock, slide:slide, flyTo:flyTo,
  pickAt:pickAt, nameAt:nameAt, pickArea:pickArea, HITPX:HITPX,
  declutter:declutter, drawRoute:drawRoute,
  dbgLog:function(on){ _dlogOn=!!on; if(!on) _dlog.length=0; return _dlogOn; },
  dlog:function(){ return _dlog; },
  META:META, INKNAME:INKNAME, tierOf:tierOf, focusOn:focusOn,
  AREA_FREQ:AREA_FREQ, CAT_TONE:CAT_TONE,
  sndState:function(){ return {on:sndOn, ctx:!!AC, state:AC?AC.state:null, amb:!!ambT}; }};
})();
"""

# ---------- 6. 骨架 ----------
HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>汴京食帖 · 开封 217 家吃食</title>
<meta name="description" content="开封吃食地图。墨分三色：确址、约略、未标。城的轮廓由 183 个落墨点自己洇开。">
<style>__CSS__</style>
</head>
<body>
<div id="app">

  <header id="head">
    <div class="hd-t">
      <h1>汴京食帖</h1>
      <span class="zh">开封 · 二百一十七家吃食</span>
    </div>
    <div class="qw"><input id="q" type="text" placeholder="寻店名 / 吃食 / 街巷　（/）" autocomplete="off" spellcheck="false"></div>
    <div class="hd-live" id="live"></div>
    <button id="sndBtn" aria-pressed="false"
      title="丝弦 · 图上落墨，耳边起音：市井定音高，品类定音色，墨色定虚实">丝弦</button>
  </header>

  <div id="mid">
    <nav id="rail" aria-label="市井目录"></nav>

    <section id="sheet">
      <div id="stage">
      <!-- 底：经纬格 -->
      <svg id="inkBack" class="lyr" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
        <g id="gGrid"></g>
      </svg>
      <!-- 中：墨场。核密度累加成的连续墨色，城的形状由此浮现 -->
      <canvas id="inkField" class="lyr"></canvas>
      <!-- 顶：墨点 · 标签 · 命中 -->
      <svg id="ink" class="lyr" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
        <g id="gWash"></g>
        <g id="gRoute"></g>
        <g id="gDot"></g>
        <!-- 市井名须在墨点之上：它是骨架，被墨盖住就失去了指位作用；
             但仍须在 gLbl 之下，免得压住选中点的标签。 -->
        <g id="gArea"></g>
        <g id="gLbl"></g>
        <g id="gScope"></g>
        <g id="gHit"></g>
      </svg>
      <div class="ov" id="north"><span class="ar">↑</span><span class="tx">北</span></div>
      <div class="ov" id="scale"><span class="tx"></span><span class="bar"><span></span></span></div>
      <div id="colophon">不设底图 · 城的轮廓由二百一十七家自己洇成<br>实墨确址 · 半墨约略 · 虚圈未标<br>三十四家无处安放，悬在卷边</div>
      <div class="ov" id="foot-note">远看是城 · 近看是店 · 拉近才见墨点<br>自绘墨图 · 等距圆柱投影 · 纬校 34.80°N<br>墨色三档 ＝ 坐标来源精度<br>丝弦 音区＝市井 · 音高音色＝品类 · 虚实＝墨色</div>
      <div id="zoomctl">
        <button id="zIn" title="放大（+）">＋</button>
        <button id="zOut" title="缩小（−）">－</button>
        <button id="zRe" title="复位（0）">复</button>
      </div>
      </div>
      <aside id="inkcol" aria-label="墨色三档"></aside>
    </section>

    <aside id="note" hidden aria-label="帖页">
      <div class="nh"></div>
      <div class="nb"></div>
      <div class="nf">
        <button class="k" id="nLocate" title="在图上把这家与住处同框 · 朱砂直线的长度即两地直线距离">图上寻它</button>
        <button class="k" id="nPick">拾入行囊</button>
        <button class="k" id="nCopyName">抄店名</button>
        <button class="k" id="nCopyPos">抄坐标</button>
      </div>
    </aside>

    <div class="pop" id="popBag" hidden>
      <div class="pop-h"><h3>行囊</h3><span class="sub" id="bagSum">—</span></div>
      <div class="pop-b" id="bagList"></div>
      <div class="pop-f">
        <button class="k" id="bagCopy">抄走清单</button>
        <button class="k" id="bagClear">清空</button>
        <span class="sp">朱砂细线 ＝ 你串的动线</span>
      </div>
    </div>

    <div class="pop" id="popNo" hidden>
      <div class="pop-h"><h3>无处安放</h3><span class="sub" id="noSub">原帖未给位置</span></div>
      <div class="wall" id="wall"></div>
      <div class="pop-f"><span class="sp">悬在卷边，等你亲自去过后再落墨</span></div>
    </div>
  </div>

  <footer id="foot">
    <span class="fx"><span class="fgl">品类</span><span id="cats" style="display:flex;gap:10px;align-items:baseline"></span></span>
    <span class="fx"><button class="tx" id="btnNo">无处安放 <b>__N_NO__</b></button></span>
    <span class="fx"><button class="tx" id="btnBag">行囊 <b id="bagN">0</b></button></span>
    <span class="fx"><span class="fgl">图上</span><span class="cnt" id="cnt">__N_MAP__</span></span>
    <span class="fx sp">自绘墨图 · 不设底图 · 朱砂线为直线示意</span>
  </footer>
</div>

<div id="curtain">
  <div class="cu">
    <div class="seal4"><span>食</span><span>汴</span><span>帖</span><span>京</span></div>
    <h1>汴京食帖</h1>
    <p class="cs">一张会承认自己不知道的地图</p>
    <p class="cstat" id="cuStat">—</p>
    <button class="cu-btn" id="cuBtn">展 卷</button>
    <p class="cu-hint">或按任意键 / 滚动 / 点空白处</p>
  </div>
</div>

<div id="light" hidden><img alt="原帖截图"><div class="cap"></div></div>
<div id="tip"></div>

<script>__JS__</script>
</body>
</html>
"""

HTML = (HTML.replace("__CSS__", CSS).replace("__JS__", JS)
            .replace("__N_NO__", str(N_NO)).replace("__N_ALL__", str(N_ALL)).replace("__N_MAP__", str(N_MAP))
            .replace("__DATA__", DATA_JS).replace("__CATMAP__", CATMAP_JS)
            .replace("__AREAS__", AREA_JS).replace("__META__", META_JS))

with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(HTML)

print("已输出 %s" % OUT)
print("字节 %d ｜ 总 %d ｜ 落墨 %d（确址 %d / 约略 %d / 未标 %d）｜ 无处安放 %d ｜ 品类 %d 组 ｜ 市井 %d 区"
      % (len(HTML.encode("utf-8")), N_ALL, N_MAP, N_EX, N_AP, N_NL, N_NO,
         len(CAT_GROUPS), len(AREA_GROUPS)))
