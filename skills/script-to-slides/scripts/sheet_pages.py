#!/usr/bin/env python3
"""ページ画像を4枚ずつ並べた画像にする（目視とレビュー用。読む枚数を減らす）。

使い方:
    python3 scripts/sheet_pages.py <ページ画像のディレクトリ> <出力先のディレクトリ>

`build_slides.py --png` が出したページ画像（*.png）を、名前の順に4枚ずつ、左上 → 右上 → 左下 → 右下に並べて
`sheet-01.png` から書き出す。出力先は、デッキの場所の外（一時フォルダ）にする。

多くのページは、並べた画像だけで判定できる（細部が要るページだけ1枚ずつ見る）。
1枚ずつの画像が要ったのは、文字が詰まったページと、24px の注釈があるページ。
slide-reviewer には両方の場所を渡し、「まず並べた画像、細部を確かめたいページだけ1枚ずつ」と頼む。
"""
import pathlib
import sys

from PIL import Image

GAP = 12


def main(src, dst):
    src, dst = pathlib.Path(src), pathlib.Path(dst)
    dst.mkdir(parents=True, exist_ok=True)
    files = sorted(src.glob("*.png"))
    if not files:
        sys.exit(f"ページ画像がない: {src}")
    for i in range(0, len(files), 4):
        ims = [Image.open(p).convert("RGB") for p in files[i:i + 4]]
        w, h = ims[0].size
        sheet = Image.new("RGB", (w * 2 + GAP, h * 2 + GAP), "#888888")
        for k, im in enumerate(ims):
            sheet.paste(im, ((k % 2) * (w + GAP), (k // 2) * (h + GAP)))
        out = dst / f"sheet-{i // 4 + 1:02d}.png"
        sheet.save(out)
        print(out, " ".join(p.name for p in files[i:i + 4]))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
