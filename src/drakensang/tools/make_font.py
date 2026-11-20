# Noto Sans JP (可変) → 静的インスタンス化し、ゲームが要求するファミリ名 "DrakenFont" に改名。
# 半角スペースの送り幅を狭め、文節区切り用の「見えない改行候補」として使えるようにする。
# 使い方: python make_font.py <src.ttf> <dst> [wght=500] [space_em=0.12]
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
src, dst = sys.argv[1], sys.argv[2]
wght = float(sys.argv[3]) if len(sys.argv) > 3 else 500
space_em = float(sys.argv[4]) if len(sys.argv) > 4 else None  # 注: ゲーム(D3DX)はスペース幅を反映しない模様
f = instancer.instantiateVariableFont(TTFont(src), {"wght": wght})
name = f["name"]
# 日本語ロケール等の名前レコードが残るとGDIが別名で認識するため、ファミリ関連の名前は全言語分削除
for nid in (1, 2, 3, 4, 6, 16, 17, 21, 22, 25):
    name.removeNames(nameID=nid)
for nid, val in {1: "DrakenFont", 2: "Regular", 3: "DrakenFont-JP", 4: "DrakenFont", 6: "DrakenFont"}.items():
    name.setName(val, nid, 3, 1, 0x409)
    name.setName(val, nid, 1, 0, 0)
f["OS/2"].usWeightClass = 400
if space_em is not None:
    upm = f["head"].unitsPerEm
    g = f.getBestCmap()[0x20]
    adv, lsb = f["hmtx"][g]
    f["hmtx"][g] = (round(upm * space_em), 0)
    print(f"space glyph {g}: {adv} -> {f['hmtx'][g][0]} (upm {upm})")
f.save(dst)
print("saved", dst)
