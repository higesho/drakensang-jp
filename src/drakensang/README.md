# Drakensang 日本語化パッチの組み立ての道具

Steam 版 Drakensang: The Dark Eye（1.03）の日本語化パッチ（locale.db4・フォント・画像）を作る Python の道具です。

- `extract.py` … 原作の locale.db4 と static.db4 から訳す文章の一覧を作ります。
- `merge.py`（`postprocess.py` を使う）… 訳をまとめ、折り返し用のすき間を入れて locale.db4 に書き込みます。`apply_tsv.py`・`apply_fix.py` は訳の差し替え用です。
- `make_font.py` … Noto Sans JP からゲーム用のフォント「DrakenFont」を作ります。
- `make_menu_textures.py`・`map_relabel.py`・`map_sheet.py` … メニューと地図の文字の画像を描き直します。`npk.py` は npk の中身の一覧・取り出しです。
- `build_patch.py` … 配布用の zip を組み立てます。

必要なもの: Python 3（Pillow、fontTools、numpy、opencv-python、budoux）、Noto Sans JP、訳の表と地図の文字の定義（このリポジトリには入っていません）。
原作のファイル（locale.db4、static.db4、npk など）は各自で用意してください。
