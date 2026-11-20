# run/raw/<fix名>.tsv の訳で、確定済み run/out/*.tsv の該当行を差し替える（検査に通った行のみ）
# 使い方: _jp/.venv/Scripts/python.exe apply_fix.py fix1 [fix2 ...]
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from postprocess import protected, enc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, "run")
src = {x["id"]: x for x in map(json.loads, open(os.path.join(ROOT, "work", "source.jsonl"), encoding="utf-8"))}

new, rejected = {}, []
for name in sys.argv[1:]:
    for line in open(os.path.join(RUN, "raw", name + ".tsv"), encoding="utf-8"):
        line = line.rstrip("\r\n")
        if "\t" not in line or line.startswith("#"):
            continue
        lid, ja = line.split("\t", 1)
        lid = lid.strip()
        if lid in src and protected(enc(src[lid]["en"])) == protected(ja.strip()):
            new[lid] = ja.strip()
        else:
            rejected.append(lid)

changed = 0
for p in glob.glob(os.path.join(RUN, "out", "*.tsv")):
    lines = open(p, encoding="utf-8").read().split("\n")
    hit = False
    for k, line in enumerate(lines):
        if "\t" in line and not line.startswith("#"):
            lid = line.split("\t", 1)[0]
            if lid in new:
                lines[k] = f"{lid}\t{new[lid]}"; hit = True; changed += 1
    if hit:
        open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print(f"差し替え {changed} 行, 不合格 {len(rejected)} 行: {rejected[:10]}")
