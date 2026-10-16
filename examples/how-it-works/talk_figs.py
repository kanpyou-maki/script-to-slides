#!/usr/bin/env python3
"""見本「台本からスライドができるまで」の図。部品は figlib.py（上の階層にある最初のもの）。

図の関数は、デッキの見出しの順に並べる。step は「同じ図の何段階目か」。
座標はこのファイルにだけある。図を直すときはここを直して書き出し直す。

p2（台本が先）: 左から右へ、台本 → Claude → デッキと図のコード（上下に分かれる）→ 書き出し → PDF。段階ごとに右へ伸ばす。
p5（図を測る）: 上の段に、図のコード → 3枚に割った図 → ブラウザで測る。3枚目で、NG の戻り（下を通って左へ）と、OK の行き先（右下）を足す。
p8（照合）: 左に台本の注記の行、右にページ。行とページを線で結ぶ。2枚目は、まとめの組だけを残して薄くし、下に一字違いの例を足す。
p10（レビュー）: 書き手 → レビュアー → あなた。1枚目はレビュアーが見るもの（下に3つ）まで、2枚目で PASS と BLOCK の行き先を足す。
色: 聞き手（台本を書く人）と台本＝青、道具と Claude の働き＝紺、ファイル＝濃い灰、NG・BLOCK＝赤、OK・PASS＝緑。
図だけに足したもの: p8 の一字違いの例（「読み上げる」と「読みあげる」）、p8 のページの中の見出し。
"""
import pathlib
import sys

for _d in pathlib.Path(__file__).resolve().parents:   # 上の階層の figlib.py を使う
    if (_d / "figlib.py").is_file():
        sys.path.insert(0, str(_d))
        break
from figlib import *  # noqa: E402,F401,F403


# ---------- P2〜P4 台本が先、スライドはあと ----------
def p2(step):
    out = doc(90, 210, "台本", BLUE) + plate(10, 330, 160, "📊 注記", BLUE)
    if step >= 2:
        out += arrow(150, 210, 250, 210, label="読む")
        out += robot(330, 210, "Claude")
        out += route("M392 190 H430 V110 H548") + route("M392 230 H430 V330 H548")
        out += text(490, 96, "書く", 28, GRAY_DK) + text(490, 316, "書く", 28, GRAY_DK)
        out += doc(600, 110, "デッキ") + doc(600, 330, "図のコード")
    if step >= 3:
        out += route("M652 110 H830 V170") + route("M652 330 H830 V270")
        out += box(740, 178, 180, 84, "書き出し", NAVY, WHITE, 28)
        out += arrow(924, 220, 990, 220)
        out += doc(1040, 220, "PDF・画像")
        out += text(20, 470, "スライドの文字は、すべて台本から導く", 28, NAVY, anchor="start")
    return out


# ---------- P5〜P7 図はコードで描いて、測って確かめる ----------
def thumb(x, n):
    """3枚に割った図の1枚（白い枠の中に、n 個の箱）。箱は飾り。"""
    out = frame(x, 110, 130, 100)
    for i in range(n):
        out += f'<rect data-hl="1" x="{x + 14 + i * 36}" y="140" width="28" height="40" rx="6" fill="{NAVY}"/>'
    return out + text(x + 65, 250, f"{n}枚目", 28, GRAY_DK)


def p5(step):
    out = doc(80, 160, "図のコード") + arrow(130, 160, 192, 160)
    out += thumb(200, 1) + thumb(350, 2) + thumb(500, 3)
    if step >= 2:
        out += arrow(640, 160, 742, 160)
        out += text(930, 70, "描画して測る", 28, NAVY)
        out += window(750, 90, 360, 250, NAVY)
        for i, s in enumerate(("箱の縁までの余白", "はみ出し", "小さすぎる文字", "など")):
            out += text(784, 172 + i * 40, s, 28, TEXT if i < 3 else GRAY_DK, anchor="start")
    if step >= 3:
        out += route("M800 340 V420 H80 V300", RED)
        out += text(440, 404, "NG なら、コードを直す", 28, RED)
        out += arrow(1000, 340, 1000, 392, GREEN)
        out += text(960, 432, "デッキに貼る", 28, GREEN)
    return out


# ---------- P8〜P9 台本とページを機械で照合する ----------
def p8(step):
    rows = (("📊 P2 — 仕組み（1/2）", "P2 仕組み"), ("📊 P3 — 仕組み（2/2）", "P3 仕組み"), ("📊 P4 — まとめ", "P4 まとめ"))
    out = text(40, 40, "台本", 28, BLUE, anchor="start") + text(840, 40, "デッキのページ", 28, GRAY_DK, anchor="start")
    out += frame(30, 60, 560, 260)
    for i, (note, page) in enumerate(rows):
        y = 125 + i * 80
        g = (mono(60, y + 10, note) + line(560, y, 830, y, NAVY)
             + frame(840, y - 40, 250, 76) + text(965, y + 10, page, 28, TEXT))
        out += dim(g) if step == 2 and i < 2 else g
    out += text(700, 100, "照合する", 28, NAVY)
    if step == 1:
        out += text(30, 380, "注記の数とページ数・見出し・段階の番号", 28, NAVY, anchor="start")
    if step == 2:
        out += box(30, 370, 330, 64, "台本：読み上げる", PALE, TEXT, 28)
        out += text(400, 414, "≠", 40, RED)
        out += box(440, 370, 360, 64, "ページ：読みあげる", PALE, TEXT, 28)
        out += text(830, 414, "→ NG", 28, RED, anchor="start")
    return out


# ---------- P10〜P11 別のエージェントがレビューする ----------
def p10(step):
    out = robot(130, 190, "書き手") + arrow(200, 190, 380, 190, label="頼む")
    out += robot(460, 190, "レビュアー")
    out += line(460, 290, 460, 314, GRAY)
    for i, s in enumerate(("台本との整合", "図の規則", "描画した見た目")):
        out += chip(180 + i * 270, 320, 250, s)
    if step >= 2:
        out += route("M460 104 V50 H130 V96", RED)
        out += text(295, 90, "BLOCK なら直す", 28, RED)
        out += arrow(530, 190, 870, 190, GREEN, label="PASS なら渡す")
        out += person(960, 190, "あなた", BLUE)
    return out


if __name__ == "__main__":
    write_all(__file__, [(p2, 3), (p5, 3), (p8, 2), (p10, 2)])
