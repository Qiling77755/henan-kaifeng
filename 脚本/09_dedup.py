# -*- coding: utf-8 -*-
"""数据去重：合并同一实体的重复录入条目。原文件备份为 data.raw.bak.json。"""
import json, os, shutil, collections

ROOT = r"E:\children‘s day file\开封美食地图"
SRC = os.path.join(ROOT, "data.json")
BAK = os.path.join(ROOT, "data.raw.bak.json")

if not os.path.exists(BAK):
    shutil.copy2(SRC, BAK)
    print("[备份] ->", BAK)

d = json.load(open(SRC, encoding="utf-8"))
before = len(d)
idx = {x["id"]: x for x in d}

# ── 硬重复：{保留ID: [被合并ID...] , 合并说明} ──────────────────
# 规律：无坐标的「模糊占位条目」与已定位的具体门店同属一家 → 重复
MERGES = [
    (17, [48, 98, 105], "邢家锅贴老店(大梁门总店) —— 另有书店街/鼓楼方向、多分店通用、宋记 等重复表述，已合并"),
    (25, [51],          "第一楼·灌汤包(森林半岛店) —— 另有「第一楼（灌汤包）」泛称重复，已合并"),
    (76, [136],         "第一楼·灌汤包(西湖店) —— 另有「第一楼（老字号，多店）」泛称重复，已合并"),
    (122, [134],        "州桥日夜餐馆 —— 另有「州桥日夜餐馆→孙记/宋门小建鸡血汤」混记条目重复，已合并"),
    (100, [104],        "田庆辉田记米线(三胜前街) —— 另有「田记米线」重复，已合并"),
    (31, [121],         "书店街（地标）—— 另有「书店街夜市」重复，已合并"),
    (16, [83],          "宋园灌汤小笼包(晋安路清明上河园店) —— 另有「宋园（吃土豆鸡翅的餐厅）」为同一家，已合并"),
]

drop = set()
report = []
for keep, dels, note in MERGES:
    if keep not in idx:
        print("!! 保留ID不存在:", keep); continue
    k = idx[keep]
    for j in dels:
        if j in idx:
            drop.add(j)
            # 合并补充信息（推荐菜、备注不丢失）
            o = idx[j]
            if o.get("ds") and o["ds"] not in (k.get("ds") or ""):
                k["ds"] = ((k.get("ds") or "") + "；" + o["ds"]).strip("；")
            report.append(f"  #{keep} {k['n']}  ←  合并 #{j} {o['n']}")
    k["rm"] = (k.get("rm") or "")
    k["rm"] = (k["rm"] + " ｜ " + note).strip(" ｜")

# ── 待核提示（不删，仅标注）──────────────────────────────────
FLAGS = {
    63: "⚠ 与 #24「万岁山总店」同名「总店」，疑同一家被地图平台重复收录，建议到店前电话确认",
    50: "⚠ 本条为两家合记（马豫兴桶子鸡 + 存花桶子鸡）",
    86: "⚠ 本条为两家合记（戴七煎包 + 清真速冻烧卖）",
    124: "⚠ 本条为两家合记（麦禾炉域 + 文敬轩酱爆鸡）",
    125: "⚠ 本条为两家合记（兴盛德 + 何记三刀）",
    139: "⚠ 店名待核实",
}
for i, note in FLAGS.items():
    if i in idx:
        idx[i]["rm"] = (idx[i].get("rm") or "") 
        idx[i]["rm"] = (idx[i]["rm"] + " ｜ " + note).strip(" ｜")

core = [x for x in d if x["id"] not in drop]
for n, x in enumerate(core, 1):
    x["id"] = n

json.dump(core, open(SRC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("\n=== 合并明细 ===")
for line in report:
    print(line)
print(f"\n去重前 {before} 条 → 去重后 {len(core)} 条（删除重复 {len(drop)} 条）")
print("已定位:", sum(1 for x in core if x.get("lat")))
print("未定位:", sum(1 for x in core if not x.get("lat")))
