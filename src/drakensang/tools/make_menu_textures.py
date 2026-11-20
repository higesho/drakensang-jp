# メインメニュー/ゲーム内メニューの文字画像（mainmenu.dds / ingamemenu.dds）を日本語で作り直す
# 元画像: 1024x512、7行×3列（通常・ハイライト・無効）。行ピッチ 73px
# 出力: export/textures/local/*.dds（非圧縮 RGBA。npk より優先して読み込まれる）
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.dirname(ROOT)
FONT = r"C:\Windows\Fonts\yumindb.ttf"   # 游明朝 Demibold
SIZE = 38
ROW_CENTER = [34 + 73 * i for i in range(7)]

MENUS = {
    "mainmenu": dict(align="left", x=[22, 351, 695],
                     labels=["続きから", "新規ゲーム", "ゲームをロード", "オプション", "クレジット", "終了", "ゲームを保存"]),
    "ingamemenu": dict(align="center", x=[170, 507, 848],
                       labels=["再開", "新規ゲーム", "ゲームをロード", "オプション", "メインメニュー", "終了", "ゲームを保存"]),
}


def text_mask(text, font):
    l, t, r, b = font.getbbox(text)
    m = Image.new("L", (r - l + 16, b - t + 16), 0)
    ImageDraw.Draw(m).text((8 - l, 8 - t), text, font=font, fill=255)
    return m


def gradient(size, top, bottom):
    w, h = size
    g = Image.new("RGBA", size)
    d = ImageDraw.Draw(g)
    for y in range(h):
        f = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * f) for i in range(3)) + (255,))
    return g


def render(text, font, state):
    m = text_mask(text, font)
    pad = 14
    W, H = m.width + pad * 2, m.height + pad * 2
    mask = Image.new("L", (W, H), 0); mask.paste(m, (pad, pad))
    outline = mask.filter(ImageFilter.MaxFilter(3))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if state == "disabled":
        halo = Image.new("RGBA", (W, H), (200, 200, 200, 0)); halo.putalpha(outline.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.7)))
        body = Image.new("RGBA", (W, H), (45, 45, 45, 0)); body.putalpha(mask.filter(ImageFilter.GaussianBlur(2.2)))
        return Image.alpha_composite(Image.alpha_composite(img, halo), body)
    if state == "hover":
        glow_a = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(7)).point(lambda v: min(255, int(v * 1.6)))
        glow = Image.new("RGBA", (W, H), (255, 120, 0, 0)); glow.putalpha(glow_a)
        img = Image.alpha_composite(img, glow)
    # 影 → 暗い縁取り → 金色グラデーション
    shadow = Image.new("RGBA", (W, H), (40, 15, 0, 0)); shadow.putalpha(ImageChops.offset(outline, 2, 2).filter(ImageFilter.GaussianBlur(1.5)).point(lambda v: int(v * 0.8)))
    edge = Image.new("RGBA", (W, H), (120, 55, 10, 0)); edge.putalpha(outline)
    top, bottom = ((255, 248, 190), (235, 140, 30)) if state == "normal" else ((255, 252, 210), (250, 160, 40))
    fill = gradient((W, H), top, bottom); fill.putalpha(mask)
    for layer in (shadow, edge, fill):
        img = Image.alpha_composite(img, layer)
    return img


def main():
    font = ImageFont.truetype(FONT, SIZE)
    outdir = os.path.join(GAME, "export", "textures", "local")
    os.makedirs(outdir, exist_ok=True)
    for name, cfg in MENUS.items():
        canvas = Image.new("RGBA", (1024, 512), (0, 0, 0, 0))
        for row, label in enumerate(cfg["labels"]):
            for col, state in enumerate(("normal", "hover", "disabled")):
                im = render(label, font, state)
                x = cfg["x"][col] - 14 if cfg["align"] == "left" else cfg["x"][col] - im.width // 2
                y = ROW_CENTER[row] - im.height // 2
                canvas.alpha_composite(im, (max(0, x), max(0, y)))
        canvas.save(os.path.join(ROOT, "textures", name + "_ja.png"))
        canvas.save(os.path.join(outdir, name + ".dds"))
        print("saved", name)


if __name__ == "__main__":
    main()
