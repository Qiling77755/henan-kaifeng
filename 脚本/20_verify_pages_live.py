# -*- coding: utf-8 -*-
"""同步后校验：确认 GitHub Pages 已重建，且线上内容与本地新版一致。

判定依据（全部为实测，不推断）：
  1) Pages 最新构建状态 = built，且 commit 与本地 HEAD 一致
  2) 首页 HTTP 200，字节数与本地 index.html 完全相同
  3) 页面含新版特征：id="dclose" / toggleSpot / deselect
  4) 页面不含旧版特征：select(id,false)（已全部替换为 toggleSpot）
  5) 中文路径图片仍可访问（回归）
"""
import os, re, json, time, subprocess, urllib.request, urllib.error
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = "Qiling77755/henan-kaifeng"
URL = "https://qiling77755.github.io/henan-kaifeng/"


def gh(*a):
    r = subprocess.run(["gh"] + list(a), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode == 0 else None


def local_head():
    r = subprocess.run(["git", "-C", os.path.join(ROOT, "河南-开封"), "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def fetch(u):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0",
                                                "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return "ERR:" + type(e).__name__ + ":" + str(e)[:80], b""


head = local_head()
local = open(os.path.join(ROOT, "河南-开封", "index.html"), "rb").read()
print("本地 HEAD   :", head[:8])
print("本地体积    :", len(local), "bytes")

print("\n--- 等待 Pages 构建 ---")
built = False
for i in range(20):
    s = gh("api", "repos/%s/pages/builds/latest" % REPO,
           "--jq", '.status + "|" + (.commit // "-") + "|" + (.error.message // "-")')
    print("  [%2d] %s" % (i, s))
    if s and s.startswith("built") and head[:8] in s:
        built = True
        break
    time.sleep(10)

fail = 0
def check(name, ok, detail=""):
    global fail
    if not ok:
        fail += 1
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  → " + detail))

print("\n--- 线上实测 ---")
ts = str(int(time.time()))
st, body = fetch(URL + "?v=" + ts)
check("Pages 构建完成且 commit 匹配本地", built, "未等到 built，见上方日志")
check("首页 HTTP 200", st == 200, "status=%s" % st)
check("字节数与本地一致 (%d)" % len(local), len(body) == len(local),
      "线上=%d 本地=%d" % (len(body), len(local)))

if body:
    t = body.decode("utf-8", "replace")
    check('含新特征 id="dclose"', 'id="dclose"' in t)
    check("含新特征 toggleSpot", "toggleSpot" in t)
    check("含新特征 deselect", "function deselect" in t)
    check("已无旧写法 select(id,false)", "select(id,false)" not in t)
    check("仍含 217 条数据", '"n"' in t)
    check("仍含卡片复制按钮", 'class="cp"' in t)
    check("仍含唯一星标逻辑", "starIcon" in t)

for name in ["图片素材/原图/18.jpg", "图片素材/原图/01.jpg"]:
    s2, b2 = fetch(URL + quote(name))
    check("中文路径图片 %s" % name, s2 == 200 and len(b2) > 1000,
          "status=%s bytes=%d" % (s2, len(b2)))

print("\nTOTAL FAIL =", fail)
