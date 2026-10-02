# -*- coding: utf-8 -*-
"""
12_hotel_fix.py — 住宿标注收敛
规则：
1. 只有【汉庭酒店(开封鼓楼火车站店)】带 star=true，地图上用红色五角星（唯一星标）。
2. 推荐列表里提及的其他酒店（全季市政府店、松果酒店）打 offmap=true：
   数据保留（含来源截图，便于回溯），但不在地图上出点。
3. 满庭芳（园内住宿餐饮）是清明上河园内的餐饮点，保留为普通圆点，不给星标。
"""
import json, shutil, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data.json")
BAK  = os.path.join(BASE, "data.before_hotelfix.bak.json")

if not os.path.exists(BAK):
    shutil.copy(DATA, BAK)
    print("已备份 ->", os.path.basename(BAK))

d = json.load(open(DATA, encoding="utf-8"))

STAR_NAME = "汉庭酒店(开封鼓楼火车站店)"
OFFMAP_KEYS = ["全季酒店", "松果酒店"]

star_hit, off_hit = [], []
for x in d:
    n = x["n"]
    if n == STAR_NAME:
        x["star"] = True
        star_hit.append(n)
    elif any(k in n for k in OFFMAP_KEYS):
        x["offmap"] = True
        # 明确说明为何不在地图上出点
        note = "推荐列表中提及的其他酒店，非本次住宿，不在地图上标注"
        x["rm"] = (x.get("rm") or "").strip()
        if note not in x["rm"]:
            x["rm"] = (x["rm"] + " ｜ " + note).strip(" ｜")
        off_hit.append(n)
    # 清理历史残留标记，保证幂等
    if n != STAR_NAME and "star" in x:
        x.pop("star", None)
    if not any(k in n for k in OFFMAP_KEYS) and "offmap" in x:
        x.pop("offmap", None)

# 统一字段顺序：把 star / offmap 放在末尾
order = ["id","n","ty","ar","lat","lng","ad","ds","src","rm","img","loc","star","offmap"]
d = [{k: x[k] for k in order if k in x} for x in d]

json.dump(d, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("星标条目 :", star_hit)
print("移出标注 :", off_hit)
print("总条目   :", len(d))
print("带星标的 :", [x['id'] for x in d if x.get('star')])
print("offmap的 :", [(x['id'], x['n']) for x in d if x.get('offmap')])
byc = {}
for x in d:
    byc[x["ty"]] = byc.get(x["ty"], 0) + 1
print("住宿类计数:", byc.get("住宿"))
print("住宿类明细:", [(x['id'], x['n']) for x in d if x['ty'] == "住宿"])
