# 地図ラベル: labels/*.json をまとめて描画し、確認用の一覧画像（英語→日本語の並び）を作る
# 使い方（システムの Python）: python -I -X utf8 map_sheet.py [--apply] [地図名...]
#  --apply を付けると export/textures/map/ に DDS も書き出す
import glob, json, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import map_relabel as mr

MAPS = mr.MAPS
apply = "--apply" in sys.argv
names = [a for a in sys.argv[1:] if not a.startswith("--")]
specs = {}
for p in sorted(glob.glob(os.path.join(MAPS, "labels", "*.json"))):
    specs.update(json.load(open(p, encoding="utf-8")))
if names:
    specs = {k: v for k, v in specs.items() if k in names}
done = []
for name, labels in specs.items():
    if labels:
        mr.process(name, labels, preview=not apply)
        done.append(name)
print("rendered", len(done), "of", len(specs), "(empty:", [k for k, v in specs.items() if not v], ")")
# 一覧: 1枚につき 4 地図、各地図は「元 | 日本語」を 384px 幅で
font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 14)
os.makedirs(os.path.join(MAPS, "sheets"), exist_ok=True)
for k in range(0, len(done), 4):
    group = done[k:k + 4]
    sheet = Image.new("RGB", (768, 384 * len(group)), (30, 30, 30))
    for i, n in enumerate(group):
        a = Image.open(os.path.join(MAPS, "src", n + ".png")).convert("RGB").resize((384, 384))
        b = Image.open(os.path.join(MAPS, "ja", n + ".png")).convert("RGB").resize((384, 384))
        sheet.paste(a, (0, i * 384)); sheet.paste(b, (384, i * 384))
        ImageDraw.Draw(sheet).text((4, i * 384 + 2), n, fill=(255, 255, 0), font=font)
    sheet.save(os.path.join(MAPS, "sheets", f"sheet_{k // 4:02d}.png"))
print("sheets:", (len(done) + 3) // 4)
