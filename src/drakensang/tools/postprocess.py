# 訳文TSVの検査と、折り返し用スペースの挿入
# 使い方: _jp/.venv/Scripts/python.exe postprocess.py <訳.tsv> <出力.tsv>
#  - 入力: id<TAB>訳文（#NEW 行や空行は無視）
#  - 検査: 原文とのタグ・書式指定・\n の数の一致、未翻訳（英字だらけ）、未知のid
#  - 変換: 日本語部分に BudouX で文節区切りの半角スペースを入れる（タグや既存スペースの周辺は触らない）
import csv, json, os, re, sys
import budoux

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = re.compile(r"<[^<>]{1,60}>|\{\d+:[a-z]\}|\\n|\[NL\]|\*[^*\s]{1,20}\*")


def enc(en):
    """原文の実改行は翻訳時に [NL] として扱う"""
    return en.replace("\n", "[NL]")
parser = budoux.load_default_japanese_parser()


def tokens(s):
    return sorted(TOKEN.findall(s))


def protected(s):
    """性別切替タグ <A/B> は中身が訳されるので、形（<…/…>）だけを比較用に正規化"""
    # *hic* などの擬音は訳してよい（数も多少変わってよい）ので比較しない
    # 斜体 <i></i> は強調なので省略してよい（開きと閉じの数さえ揃っていればよい）
    toks = sorted(re.sub(r"^<[^<>/]+/[^<>/]+>$", "<X/Y>", t) if t.startswith("<") else t
                  for t in tokens(s) if not t.startswith("*") and t not in ("<i>", "</i>"))
    if s.count("<i>") != s.count("</i>"):
        toks.append("!unbalanced-italic")
    return toks


def space(text):
    text = text.replace("（仮）", "").replace("(仮)", "")
    out = []
    for part in re.split(r"(" + TOKEN.pattern + r"| +)", text):
        if not part:
            continue
        if TOKEN.fullmatch(part) or part.isspace() or not re.search(r"[぀-ヿ一-鿿]", part):
            out.append(part)
        else:
            out.append(" ".join(parser.parse(part)))
    s = "".join(out)
    s = re.sub(r" +", " ", s)
    s = re.sub(r" ([、。！？」』）…])", r"\1", s)   # 句読点・閉じ括弧の前には入れない
    return s


def main():
    inp, outp = sys.argv[1], sys.argv[2]
    src = {x["id"]: x for x in map(json.loads, open(os.path.join(ROOT, "work", "source.jsonl"), encoding="utf-8"))}
    rows, problems = [], []
    with open(inp, encoding="utf-8") as f:
        for n, row in enumerate(csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE), 1):
            if not row or not row[0].strip() or row[0].startswith("#"):
                continue
            if len(row) < 2:
                problems.append((n, row[0], "タブ区切りになっていない")); continue
            lid, ja = row[0].strip(), row[1]
            if lid not in src:
                problems.append((n, lid, "未知のid")); continue
            en = src[lid]["en"]
            if protected(en) != protected(ja):
                problems.append((n, lid, f"タグ不一致 en={tokens(en)} ja={tokens(ja)}"))
            letters = len(re.findall(r"[A-Za-z]", TOKEN.sub("", ja)))
            if letters > 0.5 * max(1, len(TOKEN.sub("", ja))):
                problems.append((n, lid, "英字が多い（未翻訳？）"))
            rows.append((lid, space(ja)))
    with open(outp, "w", encoding="utf-8", newline="\n") as f:
        for lid, ja in rows:
            f.write(f"{lid}\t{ja}\n")
    print(f"{len(rows)} rows -> {outp}; problems: {len(problems)}")
    for p in problems:
        print("  line %d %s: %s" % p)


if __name__ == "__main__":
    main()
