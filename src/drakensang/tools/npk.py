# Nebula2 の NPK アーカイブ（*.npk）の一覧・取り出し
# 使い方: python npk.py ls <npk> [部分一致...]
#         python npk.py x  <npk> <出力先> <部分一致,...>
import os, struct, sys


def entries(path):
    """(パス, オフセット, サイズ) を返す。オフセットはデータ部先頭からの相対値"""
    out = []
    with open(path, "rb") as f:
        magic, blocklen, dataoff = struct.unpack("<4sII", f.read(12))
        assert magic == b"0KPN", magic
        stack = []
        while True:
            tag = f.read(4)
            if not tag:
                break
            ln, = struct.unpack("<I", f.read(4))
            if tag == b"ATAD":
                break
            body = f.read(ln)
            if tag == b"_RID":
                nl, = struct.unpack("<H", body[:2]); stack.append(body[2:2 + nl].decode("latin1"))
            elif tag == b"ELIF":
                off, size, nl = struct.unpack("<IIH", body[:10])
                out.append(("/".join(stack + [body[10:10 + nl].decode("latin1")]), off, size))
            elif tag in (b"DNE_", b"DNED"):
                stack.pop()
    return out, dataoff


def read(path, name_off_size, dataoff):
    name, off, size = name_off_size
    with open(path, "rb") as f:
        f.seek(dataoff + 8 + off)        # "DATA" タグと長さの 8 バイトの後ろがデータ部
        return f.read(size)


if __name__ == "__main__":
    cmd, npk = sys.argv[1], sys.argv[2]
    ents, dataoff = entries(npk)
    if cmd == "ls":
        keys = sys.argv[3:]
        for e in ents:
            if not keys or any(k in e[0] for k in keys):
                print(e[0], e[2])
    elif cmd == "x":
        outdir, keys = sys.argv[3], sys.argv[4].split(",")
        for e in ents:
            if any(k in e[0] for k in keys):
                b = read(npk, e, dataoff)
                p = os.path.join(outdir, e[0]); os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, "wb").write(b)
                print(e[0], e[2], b[:4])
