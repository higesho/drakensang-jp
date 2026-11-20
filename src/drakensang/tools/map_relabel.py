# 地図テクスチャの文字を日本語に描き替える
# 使い方（システムの Python。cv2 が必要）:
#   python -I -X utf8 map_relabel.py <ラベル定義.json> [--only 名前...] [--preview]
# ラベル定義 JSON: { "<地図名>": [ {"en": "...", "ja": "...", "box": [x0,y0,x1,y1],
#                                   "angle": 0, "keep": [[x0,y0,x1,y1], ...]}, ... ], ... }
#   box   : 英文を囲む軸平行の矩形（この中のインクを消す）。日本語もこの中に収める
#   angle : 文字列の傾き（度、反時計回りが正）。75〜105度で1行なら日本語の縦書きにする
#   keep  : 消してはいけない部分（矢印など）。省略可
#   ja    : 改行は "\n"。size を指定すると文字サイズを固定（省略時は自動、上限 MAX_FS）
# 出力: textures/maps/ja/<地図名>.png（確認用）と、--preview でなければ export/textures/map/<地図名>.dds
import json, math, os, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.dirname(ROOT)
MAPS = os.path.join(ROOT, "textures", "maps")
FONT = r"C:\Windows\Fonts\yumindb.ttf"   # 游明朝 Demibold（行書体は「ソ」と「リ」が紛らわしい）
MAX_FS = 30
NL = "\n"


def ink_mask(rgb, box, keeps):
    """box 内で、周囲より十分暗く絶対的にも暗い画素（墨のインク）を検出する。建物の茶色い線は残す"""
    h, w = rgb.shape[:2]
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0, x1, y1 = max(0, x0 - 4), max(0, y0 - 4), min(w, x1 + 4), min(h, y1 + 4)
    lum = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.int16)
    bg = cv2.medianBlur(lum.astype(np.uint8), 41).astype(np.int16)
    m = np.zeros((h, w), np.uint8)
    sl = (slice(y0, y1), slice(x0, x1))
    sub = ((bg[sl] - lum[sl]) > 28) & (lum[sl] < 105)
    m[sl][sub] = 255
    for kx0, ky0, kx1, ky1 in keeps:
        m[int(ky0):int(ky1), int(kx0):int(kx1)] = 0
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)


def ink_color(rgb, mask):
    core = cv2.erode(mask, np.ones((3, 3), np.uint8))
    px = rgb[core > 0]
    if len(px) < 20:
        return (40, 25, 10)
    dark = px[px.sum(1) <= np.percentile(px.sum(1), 15)]
    col = np.median(dark, 0)
    if col.mean() > 55:            # 薄すぎる場合は濃い墨色に寄せる
        col = col * (55 / col.mean())
    return tuple(int(v) for v in col)


def render_label(label, color):
    ja = label["ja"].replace("\\n", NL)
    en_lines = label.get("_en_lines", 1)
    if en_lines >= 2 and NL not in ja and len(ja) >= 4 and abs(float(label.get("angle", 0))) < 20:
        # 英文が2行なら日本語も2行に（「の」の後ろ、なければ中央で区切る）
        k = ja.find("の") + 1 if 0 < ja.find("の") < len(ja) - 1 else len(ja) // 2
        ja = ja[:k] + NL + ja[k:]
    lines = ja.split(NL)
    x0, y0, x1, y1 = label["box"]
    ang = float(label.get("angle", 0))
    bw, bh = x1 - x0, y1 - y0
    vertical = 75 <= abs(ang) <= 105 and len(lines) == 1
    if vertical:                   # 縦向きの文字は日本語の縦書きにする（文字は正立）
        lines = list(ja); ang = 0
    a = math.radians(abs(ang) % 180)
    c, s = abs(math.cos(a)), abs(math.sin(a))
    size = label.get("size")
    # 元の英文の高さ（ink_h: インク部分の縦幅）から目標の文字サイズを決める。水平に近い文字のみ
    start = MAX_FS
    ink_h = label.get("_ink_h")
    if ink_h and abs(ang) < 20 and not vertical:
        n = max(en_lines, len(lines))
        start = int(max(14, min(56, ink_h / n * 0.95)))
    sizes = [int(size)] if size else range(start, 7, -1)
    for fs in sizes:
        font = ImageFont.truetype(FONT, fs)
        tw = max(font.getbbox(l)[2] - font.getbbox(l)[0] for l in lines)
        lh = int(fs * (1.0 if vertical else 1.15))
        th = lh * len(lines)
        rw, rh = tw * c + th * s, tw * s + th * c
        if size or (rw <= bw * 0.98 and rh <= bh * 0.98):
            break
    pad = 6
    layer = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    top = font.getbbox("あ")[1]
    for i, l in enumerate(lines):
        bb = font.getbbox(l)
        lw = bb[2] - bb[0]
        d.text((pad + (tw - lw) // 2 - bb[0], pad + i * lh - top), l, font=font, fill=color + (255,))
    if ang:
        layer = layer.rotate(ang, resample=Image.BICUBIC, expand=True)
    return layer


def process(name, labels, preview=False):
    img = Image.open(os.path.join(MAPS, "src", name + ".png")).convert("RGBA")
    rgb = np.array(img.convert("RGB"))
    mask = np.zeros(rgb.shape[:2], np.uint8)
    colors = []
    for lb in labels:
        m = ink_mask(rgb, lb["box"], lb.get("keep", []))
        colors.append(ink_color(rgb, m))
        rows = m.any(1)
        ys = np.where(rows)[0]
        if len(ys):
            lb["_ink_h"] = int(ys.max() - ys.min()) - 4    # 膨張分を差し引いた縦幅
            # 英文の行数: インクのある行の連続区間（4px 以上）の数
            runs, cur = 0, 0
            for v in rows[ys.min():ys.max() + 1]:
                cur = cur + 1 if v else 0
                if cur == 4:
                    runs += 1
            lb["_en_lines"] = max(1, runs)
        mask |= m
    clean = cv2.inpaint(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), mask, 6, cv2.INPAINT_TELEA)
    out = Image.fromarray(cv2.cvtColor(clean, cv2.COLOR_BGR2RGB)).convert("RGBA")
    out.putalpha(img.split()[3])
    for lb, col in zip(labels, colors):
        if not lb.get("ja"):
            continue
        layer = render_label(lb, col)
        x0, y0, x1, y1 = lb["box"]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        out.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.5)),
                            (int(cx - layer.width / 2), int(cy - layer.height / 2)))
    os.makedirs(os.path.join(MAPS, "ja"), exist_ok=True)
    out.save(os.path.join(MAPS, "ja", name + ".png"))
    if not preview:
        dst = os.path.join(GAME, "export", "textures", "map"); os.makedirs(dst, exist_ok=True)
        out.save(os.path.join(dst, name + ".dds"))


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    only = sys.argv[sys.argv.index("--only") + 1:] if "--only" in sys.argv else None
    preview = "--preview" in sys.argv
    for name, labels in spec.items():
        if only and name not in only:
            continue
        process(name, labels, preview)
        print("done", name, len(labels))


if __name__ == "__main__":
    main()
