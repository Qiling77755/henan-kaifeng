# -*- coding: utf-8 -*-
"""
13_delete_offmap_hotels.py — 删除「无关酒店」
依据柒总 2026-09-27 指令：
  · 满庭芳（园内住宿餐饮）—— 保留
  · 全季酒店（开封市政府店）、松果酒店 —— 删除
删除后重排 id 使其连续（1..N），保持既有不变式。
"""
import json, shutil, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data.json")
BAK  = os.path.join(BASE, "data.before_delhotel.bak.json")

if not os.path.exists(BAK):
    shutil.copy(DATA, BAK)
    print("已备份 ->", os.path.basename(BAK))

d = json.load(open(DATA, encoding="utf-8"))
before = len(d)

DEL_KEYS = ["全季酒店", "松果酒店"]
kept, removed = [], []
for x in d:
    if any(k in x["n"] for k in DEL_KEYS) or x.get("offmap"):
        removed.append(f"#{x['id']} {x['n']}")
        continue
    x.pop("offmap", None)          # 字段已无意义，清掉
    kept.append(x)

# 重排 id
for i, x in enumerate(kept, 1):
    x["id"] = i

order = ["id","n","ty","ar","lat","lng","ad","ds","src","rm","img","loc","star"]
kept = [{k: x[k] for k in order if k in x} for x in kept]

json.dump(kept, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("已删除:", removed)
print(f"条目数: {before} -> {len(kept)}")
print("ID 连续:", [x["id"] for x in kept] == list(range(1, len(kept) + 1)))
print("星标条目:", [(x["id"], x["n"]) for x in kept if x.get("star")])
print("住宿类  :", [(x["id"], x["n"]) for x in kept if x["ty"] == "住宿"])
print("精确(非近似):", sum(1 for x in kept if x.get("lat") and x.get("loc") != "approx"))
print("区域近似    :", sum(1 for x in kept if x.get("loc") == "approx"))
print("未定位      :", sum(1 for x in kept if not x.get("lat")))
