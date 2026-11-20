# run/out/*.tsv を統合 → 重複英文へ展開 → 文節スペース挿入 → locale.db4 に反映
# 使い方: _jp/.venv/Scripts/python.exe merge.py [--no-apply]
#  出力: run/translations.tsv（スペース挿入済み・最終形）, run/new_terms.tsv（新出語）
import argparse, glob, json, os, shutil, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from postprocess import space, protected, enc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.dirname(ROOT)
RUN = os.path.join(ROOT, "run")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-apply", action="store_true")
    a = ap.parse_args()
    src = {x["id"]: x for x in map(json.loads, open(os.path.join(ROOT, "work", "source.jsonl"), encoding="utf-8"))}
    dupes = json.load(open(os.path.join(RUN, "dupes.json"), encoding="utf-8"))
    tr, news = {}, set()
    for p in sorted(glob.glob(os.path.join(RUN, "out", "*.tsv"))):
        for line in open(p, encoding="utf-8"):
            line = line.rstrip("\n")
            if line.startswith("#NEW"):
                news.add(line); continue
            if "\t" in line:
                lid, ja = line.split("\t", 1)
                tr[lid] = ja
    for rep, others in dupes.items():
        if rep in tr:
            for o in others:
                tr.setdefault(o, tr[rep])
    final = {lid: space(ja) for lid, ja in tr.items() if lid in src}
    mism = [lid for lid, ja in final.items() if protected(enc(src[lid]["en"])) != protected(ja)]
    # 手動上書き（glossary/overrides.tsv）はスペース挿入後の最終形として適用
    ov = os.path.join(ROOT, "glossary", "overrides.tsv")
    if os.path.exists(ov):
        for line in open(ov, encoding="utf-8"):
            line = line.rstrip("\n")
            if line and not line.startswith("#") and "\t" in line:
                lid, ja = line.split("\t", 1)
                if lid in src:
                    final[lid] = ja
    final = {lid: ja.replace("[NL]", chr(10)) for lid, ja in final.items()}
    with open(os.path.join(RUN, "translations.tsv"), "w", encoding="utf-8", newline="\n") as f:
        for lid in src:
            if lid in final:
                f.write(f"{lid}\t{enc(final[lid])}\n")
    with open(os.path.join(RUN, "new_terms.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sorted(news)) + "\n")
    todo = [i for i, x in src.items() if not x.get("skip") and not x["en"].startswith("#")]
    print(f"訳あり {len(final)} / 対象 {len(todo)}  タグ不一致 {len(mism)}  新出語 {len(news)}")

    if a.no_apply:
        return
    db = os.path.join(GAME, "export", "db", "locale.db4")
    shutil.copyfile(os.path.join(ROOT, "backup", "locale.db4.orig"), db)
    c = sqlite3.connect(db)
    c.executemany("UPDATE _Locale SET LocaText=? WHERE LocaId=?", [(ja, lid) for lid, ja in final.items()])
    c.commit(); c.close()
    print("locale.db4 に反映しました:", db)


if __name__ == "__main__":
    main()
