# locale.db4(原本) + static.db4(会話構造) から翻訳用 JSONL を作る
# 出力: _jp/work/source.jsonl  1行1エントリ {id, en, cat, dialog, speaker, type, order, parent}
import sqlite3, json, re, os, collections, uuid
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.dirname(ROOT)
dec = lambda b: b.decode("utf-8", "replace") if isinstance(b, bytes) else b
L = sqlite3.connect(f"file:{ROOT}/backup/locale.db4.orig?mode=ro", uri=True); L.text_factory = bytes
S = sqlite3.connect(f"file:{GAME}/export/db/static.db4?mode=ro", uri=True); S.text_factory = bytes

loc = {}
for i, t in L.execute("select LocaId, LocaText from _Locale"):
    i, t = dec(i), t
    try: t = t.decode("utf-8") if t is not None else ""
    except UnicodeDecodeError: t = t.decode("cp1252")
    loc[i] = t

# 会話: TakeGUID(blob) -> 情報
takes = {}
for g, did, tid, spk, typ, lid in S.execute("select TakeGUID, DialogId, TakeId, TakeSpeaker, TakeType, TakeLocaId from _Story_DialogTakes"):
    loca = str(uuid.UUID(bytes_le=lid)) if lid and len(lid) == 16 else None
    takes[g] = dict(dialog=dec(did), id=dec(tid), speaker=dec(spk), type=dec(typ), loca=loca)
byid = {v["loca"]: v for v in takes.values() if v["loca"]}   # LocaId -> take
take2loca = {v["id"]: v["loca"] for v in takes.values()}
# 会話ツリー: TakeGUID -> [(位置, 子TakeId)]。StartState から深さ優先でたどって通し番号(seq)を振る
children = {}
for g, child, pos, dg in S.execute("select TakeGUID, TakeChildId, TakeChildPosition, DialogGUID from _Story_DialogTakeChildMapping"):
    children.setdefault(g, []).append((pos, dec(child)))
tid2guid = {v["id"]: g for g, v in takes.items()}
parent = {}; order = {}
seq = 0
for g, v in takes.items():
    if v["type"] != "StartState":
        continue
    stack = [(g, None)]; seen = set()
    while stack:
        cur, ctx = stack.pop()
        if cur in seen: continue
        seen.add(cur)
        t = takes[cur]; lid = t["loca"]
        if t["type"] != "StartState" and lid:
            seq += 1; order.setdefault(lid, seq)
            if ctx: parent.setdefault(lid, ctx)
            if loc.get(lid, "") not in ("<Next>", "<Weiter>", "") : ctx = lid   # <Next> は文脈として飛ばす
        for pos, ch in sorted(children.get(cur, []), reverse=True):
            if ch in tid2guid: stack.append((tid2guid[ch], ctx))

GUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
def cat(i, t):
    if i in byid: return "dialog"
    if GUID.match(i): return "guid_other"
    m = re.match(r"^(lookat|infoid|archetype|tutorial|quest|journal|book|recipe|talent|spell|skill)[_]", i, re.I)
    if m: return m.group(1).lower()
    for suf in ("_name", "_Info", "_info", "_desc", "_short", "_long"):
        if i.endswith(suf): return "suffix" + suf.lower()
    return "misc"

os.makedirs(f"{ROOT}/work", exist_ok=True)
stats = collections.Counter(); chars = collections.Counter(); skip = collections.Counter()
with open(f"{ROOT}/work/source.jsonl", "w", encoding="utf-8") as out:
    for i, t in loc.items():
        c = cat(i, t)
        rec = dict(id=i, en=t, cat=c)
        if c == "dialog":
            d = byid[i]; rec.update(dialog=d["dialog"], speaker=d["speaker"], type=d["type"],
                                    parent=parent.get(i), order=order.get(i))
        if not t.strip() or t == "obsolete_entry_donottranslate" or t in ("<Next>", "<Weiter>", "<End>"):
            rec["skip"] = True; skip[c] += 1
        stats[c] += 1; chars[c] += len(t)
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(f"{'cat':20}{'rows':>8}{'chars':>10}{'skip':>7}")
for c, n in stats.most_common(): print(f"{c:20}{n:8}{chars[c]:10}{skip[c]:7}")
print("total", sum(stats.values()), sum(chars.values()))
print("dialog speakers:", collections.Counter(byid[i]["speaker"] for i in loc if i in byid).most_common(25))
