# -*- coding: utf-8 -*-
"""回归校验：① 说明块确已移到清单末尾；② 文案零丢失（新旧 <li> 集合一致）。"""
import os, re, html as _h

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW = os.path.join(ROOT, "开封美食地图.html")
OLD = os.path.join(ROOT, "开封美食地图.before_notemove.bak.html")

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def li_texts(s):
    return sorted(_h.unescape(re.sub(r"<[^>]+>", "", x)).strip()
                  for x in re.findall(r"<li>(.*?)</li>", s, re.S))

new, old = read(NEW), read(OLD)
ok = True

# ---- 1. 文案零丢失 ----
ln, lo = li_texts(new), li_texts(old)
print(f"[1] <li> 条数  new={len(ln)}  old={len(lo)}  {'OK' if ln == lo else 'MISMATCH'}")
if ln != lo:
    ok = False
    only_new = [x for x in ln if x not in lo]
    only_old = [x for x in lo if x not in ln]
    print("   仅新有:", only_new[:5])
    print("   仅旧有:", only_old[:5])

# ---- 2. DOM 顺序：说明块在清单之后 ----
i_list   = new.index('<section class="list" id="list">')
i_note   = new.index("<summary>位置校验方式 / 距离计算原理 / 已知局限</summary>")
i_quick  = new.index("<summary>高频推荐速览（多图交叉印证）</summary>")
i_pane_e = new.index("</aside>")
print(f"[2] list@{i_list}  位置校验@{i_note}  高频推荐@{i_quick}  </aside>@{i_pane_e}")
c2 = i_pane_e > i_note > i_list and i_list > i_quick
print(f"    清单之前仅有『高频推荐速览』、『位置校验』位于清单末尾且在 aside 内 -> {'OK' if c2 else 'FAIL'}")
ok &= c2

# ---- 3. .notes 容器数量与结构 ----
n_notes = len(re.findall(r'<div class="notes">', new))
c3 = n_notes == 2
print(f"[3] .notes 容器数 = {n_notes}（预期 2）-> {'OK' if c3 else 'FAIL'}")
ok &= c3

# ---- 4. pane 内直接子元素顺序 ----
seg = new[new.index('<div class="pane" id="pane">'): i_pane_e]
order = re.findall(r'<div class="notes">|<section class="list" id="list"></section>', seg)
print("[4] #pane 直接子元素顺序:", order)
c4 = order == ['<div class="notes">', '<section class="list" id="list"></section>', '<div class="notes">']
print(f"    -> {'OK' if c4 else 'FAIL'}")
ok &= c4

print("\nRESULT:", "PASS" if ok else "FAIL")
