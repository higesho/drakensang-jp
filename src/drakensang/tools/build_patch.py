# 配布用の日本語化パッチを組み立てる（zip 内の export フォルダをゲームフォルダに上書きコピーする形式）
# 使い方: _jp/.venv/Scripts/python.exe -X utf8 build_patch.py [バージョン]
# 出力: _jp/dist/Drakensang_JP_Patch_<ver>/ と同名の .zip
import datetime, glob, hashlib, json, os, shutil, subprocess, sys, zipfile
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.dirname(ROOT)
VER = sys.argv[1] if len(sys.argv) > 1 else "v1.0"
NAME = f"Drakensang_JP_Patch_{VER}"
DIST = os.path.join(ROOT, "dist")
OUT = os.path.join(DIST, NAME)
TPL = os.path.join(ROOT, "patch_template")
TEX = os.path.join(ROOT, "textures")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest().upper()


def fourcc(dds):
    with open(dds, "rb") as f:
        f.seek(84)
        return f.read(4).decode("ascii", "replace")


def put_dds(png, orig_dds, rel):
    """元の DDS と同じ圧縮形式（DXT1/3/5）で書き出す"""
    dst = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    fmt = fourcc(orig_dds)
    if fmt not in ("DXT1", "DXT3", "DXT5"):
        raise SystemExit(f"unexpected format {fmt} in {orig_dds}")
    Image.open(png).convert("RGBA").save(dst, pixel_format=fmt)
    return rel


def write_text(dst, text, bom=False):
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    with open(dst, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
        f.write(text)


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    # 1) テキスト: 最新の訳を原本に反映した locale.db4
    subprocess.run([os.path.join(ROOT, ".venv", "Scripts", "python.exe"), "-X", "utf8",
                    os.path.join(ROOT, "tools", "merge.py")], check=True)
    files = []
    rel = r"export\db\locale.db4"
    os.makedirs(os.path.join(OUT, "export", "db"))
    shutil.copyfile(os.path.join(GAME, "export", "db", "locale.db4"), os.path.join(OUT, rel))
    files.append((rel, os.path.join(ROOT, "backup", "locale.db4.orig")))
    # 2) フォント
    rel = r"export\data\fonts\Drakensang"
    os.makedirs(os.path.join(OUT, "export", "data", "fonts"))
    shutil.copyfile(os.path.join(ROOT, "DrakenFont_NotoSansJP.ttf"), os.path.join(OUT, rel))
    files.append((rel, os.path.join(ROOT, "backup", "Drakensang.font.orig")))
    # 3) 画像（追加ファイル）
    orig_local = os.path.join(TEX, "orig", "export", "textures", "local")
    local = {"mainmenu": os.path.join(TEX, "mainmenu_ja.png"),
             "ingamemenu": os.path.join(TEX, "ingamemenu_ja.png"),
             "firsttime_ardo": os.path.join(TEX, "firsttime_ardo_ja.png")}
    for p in glob.glob(os.path.join(TEX, "signs", "ja", "*.png")):
        local[os.path.splitext(os.path.basename(p))[0]] = p
    for n, png in sorted(local.items()):
        files.append((put_dds(png, os.path.join(orig_local, n + ".dds"), rf"export\textures\local\{n}.dds"), None))
    for png in sorted(glob.glob(os.path.join(TEX, "maps", "ja", "*.png"))):
        n = os.path.splitext(os.path.basename(png))[0]
        orig = os.path.join(TEX, "maps", "loc", "export", "textures", "map", n + ".dds")
        files.append((put_dds(png, orig, rf"export\textures\map\{n}.dds"), None))
    # 5) スクリプト・説明書
    today = datetime.date.today().isoformat()
    # 上書きコピーで導入する形式（スクリプトは同梱しない）
    for fn, bom in [("README.txt", True), ("OFL.txt", False)]:
        t = open(os.path.join(TPL, fn), encoding="utf-8").read()
        t = t.replace("{VERSION}", VER).replace("{FOLDER}", NAME).replace("{DATE}", today)
        write_text(os.path.join(OUT, fn), t, bom)
    # 6) zip
    zpath = os.path.join(DIST, NAME + ".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dp, _, fns in os.walk(OUT):
            for fn in fns:
                full = os.path.join(dp, fn)
                z.write(full, os.path.relpath(full, DIST))
    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
    print(f"{len(files)} files, folder {total / 1e6:.1f} MB, zip {os.path.getsize(zpath) / 1e6:.1f} MB -> {zpath}")


if __name__ == "__main__":
    main()
