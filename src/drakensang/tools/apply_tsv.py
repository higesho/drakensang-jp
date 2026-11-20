# 使い方: python apply_tsv.py <元db> <出力db> <訳.tsv>...
# TSV: LocaId<TAB>日本語テキスト （テキスト中の改行はゲーム同様 \n リテラルで記述）
import sqlite3, shutil, sys, csv
src, dst, tsvs = sys.argv[1], sys.argv[2], sys.argv[3:]
if src != dst:
    shutil.copyfile(src, dst)
c = sqlite3.connect(dst); c.text_factory = lambda b: b.decode("utf-8", "replace")
n = miss = 0
for t in tsvs:
    with open(t, encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
            if not row or row[0].startswith("#") or len(row) < 2:
                continue
            lid, txt = row[0], row[1]
            cur = c.execute("UPDATE _Locale SET LocaText=? WHERE LocaId=?", (txt, lid))
            if cur.rowcount: n += 1
            else: miss += 1; print("missing id:", lid)
c.commit(); c.close()
print(f"updated {n}, missing {miss}")
