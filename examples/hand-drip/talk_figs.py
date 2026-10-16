#!/usr/bin/env python3
"""見本「ハンドドリップの3つのコツ」の図。部品は figlib.py（上の階層にある最初のもの）。

図の関数は、デッキの見出しの順に並べる。step は「同じ図の何段階目か」。
座標はこのファイルにだけある。図を直すときはここを直して書き出し直す。

p2（味を決める3つのこと）: 左から右へ、番号つきの箱を1つずつ足す。前の箱は薄くせず、3枚目で並びがそろう。
p5（蒸らし）: 左に「少しだけ注ぐ」、右に「30秒ほど待つ」。2枚目で右の箱と結果（お湯が通りやすくなる）を足す。
色: 味を決める要素＝紺、聞き手がすること（注ぐ・待つ）＝青、結果＝紺の文字。
図だけに足したもの: p5 の矢印（順番を表す）。
"""
import pathlib
import sys

for _d in pathlib.Path(__file__).resolve().parents:   # 上の階層の figlib.py を使う
    if (_d / "figlib.py").is_file():
        sys.path.insert(0, str(_d))
        break
from figlib import *  # noqa: E402,F401,F403


# ---------- P2〜P4 味を決める3つのこと ----------
def p2(step):
    out = ""
    for i, label in enumerate(("豆の挽き方", "お湯の温度", "注ぐ速さ")[:step]):
        x = 60 + i * 352
        out += num(x + 150, 130, i + 1) + box(x, 180, 300, 110, label, NAVY, WHITE, 32)
    if step == 3:
        out += text(568, 400, "毎回そろえると、味のぶれが小さくなる", 30, NAVY)
    return out


# ---------- P5〜P6 最初に少しだけ注いで待つ ----------
def p5(step):
    out = box(60, 170, 380, 110, "少しだけ注ぐ", BLUE, WHITE, 32)
    out += text(250, 330, "粉全体を湿らせる", 28, GRAY_DK)
    if step >= 2:
        out += arrow(460, 225, 660, 225)
        out += box(680, 170, 380, 110, "30秒ほど待つ", BLUE, WHITE, 32)
        out += text(870, 330, "＝ 蒸らし", 28, GRAY_DK)
        out += text(568, 420, "ガスが抜けて、お湯が通りやすくなる", 30, NAVY)
    return out


if __name__ == "__main__":
    write_all(__file__, [(p2, 3), (p5, 2)])
