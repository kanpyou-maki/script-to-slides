#!/usr/bin/env python3
"""スライドの図（SVG）を描くための共通部品。

各デッキの図は、デッキの隣の `<デッキ名>_figs.py` に書き、このファイルの部品を使う。
書き出しは `python3 scripts/build_slides.py <デッキ.md>` が行う（単独で動かすなら
`python3 <デッキ名>_figs.py`）。出力先はデッキの隣の `figs/<デッキ名>-<図の名前>-<段階>.svg`。

図の規則は references/figures.md を参照。要点:
- 図のキャンバスは 1136x500（デッキには `![w:1136](./figs/...)` で等倍で貼る。文字サイズがそのまま実寸になる）
- 箱の中は大きめの1行ラベル（28px）。名前＋説明の2段組みにしない
- 強調はベタ塗り。主役以外は dim() で薄く落とす
- 基本の部品: 文字 text()、箱 box()、矢印 arrow()、折れ線の矢印 route()（破線も）、印 check()／cross()
- 人物 person()・パッケージ cube()・アプリ app()・AI robot()・データベース db()・コードのファイル doc()・鍵 key()・
  管理画面 panel()・入力欄 field()・家 house()・防犯カメラ camera()・警報 bell()・サーバー server()・フォルダ folder()・
  テーブル table()・通信経路 pipe()・Wi-Fi wifi()・錠前 lock() は、箱ではなく絵で描く。画面の枠は frame()、ブラウザの窓は window()、
  等幅の文字は mono()、ターミナルの画面は terminal()、
  矢じりのない実線は line()、くくる線は bracket()、破線は dashline()、実線の囲み枠は outline()、破線の枠（伏せた部品・表示されていないボタン）は ghost()
- 数えた項目の番号は num()（紺の丸に白い数字）、2行のラベルの箱は box2()、AIへの指示文の枠（右に AI）は ask()
- 枠の中・矢印の上に並べる高さ56の箱は chip()、設定の札（白地に紺の線）は plate()、文章の行（飾り）は bar()
- 番号つきの見出し（番号の丸と、その項目の中身）は head()
- 似た見た目をその場で作らず、足りなければ部品を足し、この一覧にも書く
- 右下（x>1040, y>440 のあたり）はページ番号が来るので空けておく
- 色は theme.css のトークンと同じ値。theme.css を変えたらここも合わせる
"""
import os
import pathlib

W, H = 1136, 500
NAVY, BLUE, BLUE_BG = "#1E3A5F", "#2E86C1", "#D6EAF8"
RED, RED_BG = "#C0392B", "#FDEDEC"
GREEN = "#1E8B4F"
TEXT, GRAY_DK, GRAY, PALE = "#1A1A2E", "#555555", "#9AA5B1", "#DDE5EE"
WHITE = "#FFFFFF"
FONT = "'Noto Sans JP','Hiragino Sans','Hiragino Kaku Gothic ProN','Yu Gothic',sans-serif"   # 幅の基準は Noto Sans JP
MONO = "'SF Mono',Menlo,monospace"
CUBE = {"green": ("#4CC38A", "#1E8B4F", "#176F3F"), "red": ("#E4695B", "#C0392B", "#9C2D22"),
        "gray": ("#C3CBD4", "#97A2AE", "#7C8794")}


def text(x, y, s, size=30, fill=TEXT, weight=700, anchor="middle", font=FONT):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" font-family="{font}">{s}</text>')


def box(x, y, w, h, label, fill=PALE, color=TEXT, size=30, stroke=None, rx=16, font=FONT):
    """箱（1行ラベル）。打ち込まれた文字列を入れるときは font=MONO。"""
    st = f' stroke="{stroke}" stroke-width="3"' if stroke else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{st}/>'
            + text(x + w / 2, y + h / 2 + size * 0.36, label, size, color, font=font))


def box2(x, y, w, l1, l2, fill, color):
    """2行のラベルの箱（高さ104）。"""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="104" rx="16" fill="{fill}"/>'
            + text(x + w / 2, y + 44, l1, 28, color) + text(x + w / 2, y + 82, l2, 28, color))


def num(cx, cy, n):
    """数えた項目の番号（紺の丸に白い数字）。同じ番号を、別の図・別のページでその項目を指すのにも使う。"""
    return f'<circle cx="{cx}" cy="{cy}" r="22" fill="{NAVY}"/>' + text(cx, cy + 10, str(n), 28, WHITE)


def head(n, s, color=NAVY):
    """番号つきの見出し（番号の丸と、その項目の中身）。対策は紺、攻撃のやり方・盗まれる経路は color=RED。"""
    return num(62, 62, n) + text(96, 72, s, 28, color, anchor="start")


def arrow(x1, y1, x2, y2, color=GRAY_DK, label=None, size=28, dy=-16):
    """label の中の | は改行。線の上に、下の行から積む。"""
    mid = "a" + color[1:]
    out = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="5" marker-end="url(#{mid})"/>'
    if label:
        lines = label.split("|")
        for i, ln in enumerate(lines):
            out += text((x1 + x2) / 2, (y1 + y2) / 2 + dy - (len(lines) - 1 - i) * (size + 8), ln, size, color)
    return out


def person(cx, cy, label, color=NAVY, mask=False):
    out = (f'<circle cx="{cx}" cy="{cy - 40}" r="27" fill="{color}"/>'
           f'<path d="M{cx - 46} {cy + 46} Q{cx - 46} {cy - 6} {cx} {cy - 6} Q{cx + 46} {cy - 6} {cx + 46} {cy + 46} Z" fill="{color}"/>')
    if mask:  # 攻撃者は目元を帯で隠す
        out += f'<rect x="{cx - 27}" y="{cy - 50}" width="54" height="13" fill="{TEXT}"/>'
    return out + text(cx, cy + 86, label, 28, color)


def cube(cx, cy, s, kind, label=None, lcolor=TEXT, lsize=28, ly=None):
    top, left, right = CUBE[kind]
    h = s / 2
    out = (f'<polygon points="{cx},{cy - s} {cx + s},{cy - h} {cx},{cy} {cx - s},{cy - h}" fill="{top}"/>'
           f'<polygon points="{cx - s},{cy - h} {cx},{cy} {cx},{cy + s} {cx - s},{cy + h}" fill="{left}"/>'
           f'<polygon points="{cx + s},{cy - h} {cx},{cy} {cx},{cy + s} {cx + s},{cy + h}" fill="{right}"/>')
    if label:
        out += text(cx, ly or cy + s + 44, label, lsize, lcolor)
    return out


def app(cx, cy, label, color=BLUE):
    return (f'<rect x="{cx - 62}" y="{cy - 46}" width="124" height="92" rx="12" fill="{color}"/>'
            f'<rect x="{cx - 50}" y="{cy - 18}" width="100" height="52" rx="4" fill="#FFFFFF"/>'
            f'<circle cx="{cx - 44}" cy="{cy - 32}" r="5" fill="#FFFFFF"/><circle cx="{cx - 28}" cy="{cy - 32}" r="5" fill="#FFFFFF"/>'
            + text(cx, cy + 86, label, 28, color))


def robot(cx, cy, label, color=NAVY):
    return (f'<line x1="{cx}" y1="{cy - 46}" x2="{cx}" y2="{cy - 66}" stroke="{color}" stroke-width="6"/>'
            f'<circle cx="{cx}" cy="{cy - 70}" r="8" fill="{color}"/>'
            f'<rect x="{cx - 56}" y="{cy - 46}" width="112" height="92" rx="20" fill="{color}"/>'
            f'<circle cx="{cx - 22}" cy="{cy - 6}" r="11" fill="#FFFFFF"/><circle cx="{cx + 22}" cy="{cy - 6}" r="11" fill="#FFFFFF"/>'
            f'<rect x="{cx - 22}" y="{cy + 18}" width="44" height="8" rx="4" fill="#FFFFFF"/>'
            + text(cx, cy + 86, label, 28, color))


def db(cx, cy, label, color=NAVY):
    """データベース（円柱）。高さは人物・アプリと同じ（cy±46）。"""
    top, bot = cy - 32, cy + 32
    out = (f'<path d="M{cx - 56} {top} V{bot} A56 14 0 0 0 {cx + 56} {bot} V{top} Z" fill="{color}"/>'
           f'<ellipse cx="{cx}" cy="{top}" rx="56" ry="14" fill="{color}" stroke="#FFFFFF" stroke-width="3"/>')
    for y in (cy - 8, cy + 14):
        out += f'<path d="M{cx - 56} {y} A56 14 0 0 0 {cx + 56} {y}" fill="none" stroke="#FFFFFF" stroke-width="3"/>'
    return out + text(cx, cy + 86, label, 28, color)


def doc(cx, cy, label, color=GRAY_DK, lines=True):
    """コードのファイル（角を折った紙）。lines=False なら中の行を描かない（鍵などを重ねるとき）。

    中の行は飾りの矩形。図の検査（文字と箱の余白）の対象から外すために data-hl="1" を付けている。
    """
    x, y = cx - 40, cy - 46
    out = (f'<path d="M{x} {y} H{x + 54} L{x + 80} {y + 26} V{y + 92} H{x} Z" fill="{color}"/>'
           f'<path d="M{x + 54} {y} V{y + 26} H{x + 80} Z" fill="#FFFFFF" opacity="0.55"/>')
    if lines:
        for i, w in enumerate((52, 52, 34)):
            out += f'<rect data-hl="1" x="{x + 14}" y="{y + 38 + i * 16}" width="{w}" height="6" rx="3" fill="#FFFFFF"/>'
    return out + text(cx, cy + 86, label, 28, color)


def key(cx, cy, color=TEXT, s=1.0):
    """鍵（APIキーなど）。持ち手の輪が左、歯が右下。"""
    return (f'<g transform="translate({cx} {cy}) scale({s})" fill="none" stroke="{color}" stroke-width="9" stroke-linecap="round">'
            f'<circle cx="-22" cy="0" r="15"/><path d="M-6 0 H38 M22 0 V14 M37 0 V14"/></g>')


def panel(cx, cy, label, color=NAVY):
    """サービスの管理画面（切り替えスイッチが並んだ画面）。スイッチは飾りの矩形なので data-hl="1" を付けている。"""
    out = f'<rect x="{cx - 62}" y="{cy - 46}" width="124" height="92" rx="12" fill="{color}"/>'
    for i, on in enumerate((True, False)):
        y = cy - 28 + i * 34
        out += (f'<rect data-hl="1" x="{cx - 44}" y="{y}" width="88" height="22" rx="11" fill="#FFFFFF"/>'
                f'<circle cx="{cx + 32 if on else cx - 32}" cy="{y + 11}" r="8" fill="{color}"/>')
    return out + text(cx, cy + 86, label, 28, color)


def house(cx, cy, label, color=NAVY):
    """家（屋根・壁・ドア）。高さは人物・アプリと同じくらい（cy-56〜cy+46）。"""
    return (f'<polygon points="{cx - 68},{cy - 8} {cx},{cy - 58} {cx + 68},{cy - 8}" fill="{color}"/>'
            f'<rect x="{cx - 50}" y="{cy - 8}" width="100" height="54" fill="{color}"/>'
            f'<rect data-hl="1" x="{cx - 13}" y="{cy + 8}" width="26" height="38" fill="#FFFFFF"/>'
            + text(cx, cy + 86, label, 28, color))


def camera(cx, cy, label, color=NAVY):
    """防犯カメラ（本体・レンズ・支柱）。"""
    return (f'<rect x="{cx - 54}" y="{cy - 40}" width="76" height="52" rx="10" fill="{color}"/>'
            f'<polygon points="{cx + 28},{cy - 22} {cx + 56},{cy - 38} {cx + 56},{cy + 10} {cx + 28},{cy - 6}" fill="{color}"/>'
            f'<line x1="{cx - 16}" y1="{cy + 12}" x2="{cx - 16}" y2="{cy + 38}" stroke="{color}" stroke-width="8"/>'
            f'<rect data-hl="1" x="{cx - 44}" y="{cy + 36}" width="56" height="10" rx="5" fill="{color}"/>'
            + text(cx, cy + 86, label, 28, color))


def bell(cx, cy, label, color=NAVY):
    """警報（ベル）。"""
    return (f'<circle cx="{cx}" cy="{cy - 42}" r="8" fill="{color}"/>'
            f'<path d="M{cx - 38} {cy + 20} Q{cx - 38} {cy - 38} {cx} {cy - 38} Q{cx + 38} {cy - 38} {cx + 38} {cy + 20} '
            f'L{cx + 52} {cy + 32} H{cx - 52} Z" fill="{color}"/>'
            f'<circle cx="{cx}" cy="{cy + 40}" r="9" fill="{color}"/>'
            + text(cx, cy + 86, label, 28, color))


def server(cx, cy, label, color=NAVY):
    """サーバー（3段の機器）。高さは人物・アプリと同じ（cy±46）。ランプと溝は飾りなので data-hl="1" を付けている。"""
    out = ""
    for i in range(3):
        y = cy - 46 + i * 33
        out += (f'<rect x="{cx - 56}" y="{y}" width="112" height="26" rx="6" fill="{color}"/>'
                f'<circle cx="{cx - 40}" cy="{y + 13}" r="5" fill="#FFFFFF"/>'
                f'<rect data-hl="1" x="{cx - 8}" y="{y + 10}" width="50" height="6" rx="3" fill="#FFFFFF"/>')
    return out + text(cx, cy + 86, label, 28, color)


def folder(cx, cy, label, color=GRAY_DK):
    """フォルダ（見出しのつまみ付き）。"""
    return (f'<rect x="{cx - 56}" y="{cy - 46}" width="56" height="30" rx="8" fill="{color}"/>'
            f'<rect x="{cx - 56}" y="{cy - 30}" width="112" height="76" rx="8" fill="{color}"/>'
            + text(cx, cy + 86, label, 28, color))


def table(x, y, w, label, color=NAVY):
    """データベースのテーブル（見出しの行＋中身の行）。高さは100。中身の区切りは飾りなので data-hl="1" を付けている。"""
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="100" rx="10" fill="{PALE}"/>'
           f'<path d="M{x} {y + 60} V{y + 10} a10 10 0 0 1 10 -10 H{x + w - 10} a10 10 0 0 1 10 10 V{y + 60} Z" fill="{color}"/>')
    for i in (1, 2):
        out += f'<rect data-hl="1" x="{x + w * i / 3 - 2}" y="{y + 60}" width="4" height="40" fill="#FFFFFF"/>'
    return out + text(x + w / 2, y + 40, label, 28, "#FFFFFF")


def pipe(x1, y, x2, color=GRAY):
    """通信経路（太い横線）。流れの向きを持たないので、矢じりは付けない。"""
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="22" stroke-linecap="round"/>'


def wifi(cx, cy, color=RED, r=26):
    """Wi-Fi の印（白い丸の中に扇形の3本線）。通信経路 pipe() の上に重ねて置く。"""
    out = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="{color}" stroke-width="4"/>'
    for rho in (8, 15, 22):
        d = rho * 0.707
        out += (f'<path d="M{cx - d:.1f} {cy + 12 - d:.1f} A{rho} {rho} 0 0 1 {cx + d:.1f} {cy + 12 - d:.1f}" fill="none" '
                f'stroke="{color}" stroke-width="4" stroke-linecap="round"/>')
    return out + f'<circle cx="{cx}" cy="{cy + 13}" r="3.5" fill="{color}"/>'


def lock(cx, cy, color=GREEN, r=30):
    """錠前（白い丸の中）。暗号化した通信経路 pipe() の上に重ねて置く。本体は飾りの矩形なので data-hl="1" を付けている。"""
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="{color}" stroke-width="4"/>'
            f'<path d="M{cx - 8} {cy - 2} V{cy - 9} a8 8 0 0 1 16 0 V{cy - 2}" fill="none" stroke="{color}" stroke-width="5"/>'
            f'<rect data-hl="1" x="{cx - 14}" y="{cy - 3}" width="28" height="21" rx="4" fill="{color}"/>')


def field(x, y, w, s, color=GRAY_DK, fill="#FFFFFF", size=28, h=68, font=FONT):
    """入力欄（検索欄・フォーム）。s は入力されている文字。打ち込む文字列を見分けたいときは font=MONO。"""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{GRAY}" stroke-width="3"/>'
            + text(x + 22, y + h / 2 + size * 0.36, s, size, color, 700, "start", font))


def frame(x, y, w, h):
    """画面の枠（白地に灰色の線）。中に入力欄・ボタン・ファイルの中身を並べる。"""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#FFFFFF" stroke="{GRAY}" stroke-width="3"/>'


def ask(lead, lines, y, shown=None):
    """AIへの指示文（台本の一字一句。2行目からは1字下げる）。枠は x=40〜840、右に AI。

    枠の高さは全部の行で決める。shown は、そのうち何行目までを出すか（指示文をページをまたいで出すとき）。
    """
    h = 32 + 38 * len(lines)
    out = text(40, y - 14, lead, 28, TEXT, anchor="start") + frame(40, y, 800, h)
    for i, s in enumerate(lines[:shown]):
        out += text(62 if i == 0 else 90, y + 44 + i * 38, s, 28, TEXT, anchor="start")
    cy = min(y + h / 2, 396)
    return out + arrow(850, cy, 934, cy, BLUE) + robot(1000, cy, "AI")


def window(x, y, w, h, color=BLUE):
    """ブラウザの窓（アプリ app() を大きくしたもの）。上の帯に丸が2つ、その下の白いところに中身を並べる。"""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{color}"/>'
            f'<rect x="{x + 10}" y="{y + 44}" width="{w - 20}" height="{h - 54}" rx="6" fill="#FFFFFF"/>'
            f'<circle cx="{x + 26}" cy="{y + 22}" r="7" fill="#FFFFFF"/><circle cx="{x + 50}" cy="{y + 22}" r="7" fill="#FFFFFF"/>')


def chip(x, y, w, label, fill=NAVY, color=WHITE, font=FONT):
    """枠の中・矢印の上に並べる箱（高さ56）。打ち込まれた文字列は font=MONO。"""
    return box(x, y, w, 56, label, fill, color, 28, rx=12, font=font)


def plate(x, y, w, label, color=NAVY):
    """設定の札（白地に紺の線。高さ56）。Cookie の属性・有効期限のように、紺の箱に付ける設定。危ない設定は color=RED。"""
    return box(x, y, w, 56, label, WHITE, color, 28, stroke=color, rx=12)


def bar(x, y, w, fill=PALE):
    """文章の行（飾りの矩形）。y は上端。"""
    return f'<rect data-hl="1" x="{x}" y="{y}" width="{w}" height="14" rx="7" fill="{fill}"/>'





def mono(x, y, s, color=TEXT):
    """ファイルの中身の文字（等幅）。"""
    return text(x, y, s, 28, color, anchor="start", font=MONO)




def ghost(x, y, w, h, color=NAVY):
    """破線の枠（まだ伏せてある部品、表示されていないボタン、添えられていない・含まれていないもの）。中の文字は text() で重ねる。"""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="none" stroke="{color}" '
            f'stroke-width="4" stroke-dasharray="10 8"/>')


def line(x1, y1, x2, y2, color=GRAY, width=4):
    """矢じりのない実線（行や列の区切り、枝分かれのつなぎ）。破線は dashline()。"""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>'


def outline(x, y, w, h, color=NAVY):
    """実線の囲み枠（いくつかの部品を囲んで、まとめた呼び名を付けるとき）。伏せた部品の破線の枠は ghost()。"""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="none" stroke="{color}" stroke-width="4"/>'


def bracket(x, y1, y2, color=GRAY, tick=18):
    """くくる線（「]」の形）。並べた箱の右に置き、そのうしろに含み（「ことがある」等）を書く。y1・y2 は上下の箱の中心。"""
    return line(x, y1, x, y2, color) + line(x - tick, y1, x, y1, color) + line(x - tick, y2, x, y2, color)


def terminal(x, y, w, lines):
    """ターミナルの画面（濃い地に等幅の文字 26px、行の間隔 40）。lines の要素は文字か (文字, 色)。"""
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{40 + 40 * len(lines)}" rx="14" fill="{TEXT}"/>'
    for i, ln in enumerate(lines):
        s, c = ln if isinstance(ln, tuple) else (ln, "#F0F4F8")
        out += text(x + 28, y + 50 + i * 40, s, 26, c, 400, "start", MONO)
    return out


def dashline(x1, y1, x2, y2, color=GRAY, width=4):
    """矢じりのない破線（境界線、まだ中身を見ていないつながり）。流れの向きがあるなら route(dash=True) を使う。"""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" stroke-dasharray="10 8"/>'


def check(cx, cy, color=NAVY, r=16):  # できる・確かめた
    return (f'<path d="M{cx - r} {cy} L{cx - r * 0.3} {cy + r * 0.7} L{cx + r} {cy - r * 0.7}" fill="none" '
            f'stroke="{color}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>')


def cross(cx, cy, color=TEXT, r=15):  # しない・できない
    return "".join(f'<line x1="{cx - r}" y1="{cy - r * s}" x2="{cx + r}" y2="{cy + r * s}" stroke="{color}" stroke-width="7"/>'
                   for s in (1, -1))


def route(d, color=GRAY_DK, dash=False):
    """折れ線の矢印。d は SVG の path（例: "M330 350 H920 V224"）。先端に矢じりが付く。"""
    da = ' stroke-dasharray="12 10"' if dash else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="5"{da} marker-end="url(#a{color[1:]})"/>'


def dim(inner):  # 主役以外を落とす
    return f'<g opacity="0.3">{inner}</g>'


def write_all(figs_file, figs):
    """figs_file: 呼び出し元の __file__。figs: [(図の関数, 段階の数), ...]"""
    src = pathlib.Path(figs_file).resolve()
    stem = src.stem.replace("_figs", "")
    out_dir = pathlib.Path(os.environ.get("FIGS_OUT_DIR") or src.parent / "figs")   # FIGS_OUT_DIR: build_slides.py --verify が比べるための出力先
    out_dir.mkdir(exist_ok=True)
    markers = "".join(
        f'<marker id="a{c[1:]}" markerUnits="userSpaceOnUse" markerWidth="20" markerHeight="20" refX="17" refY="10" orient="auto">'
        f'<path d="M0 0L20 10L0 20z" fill="{c}"/></marker>' for c in (GRAY_DK, RED, NAVY, GREEN, BLUE))
    n = changed = 0
    for fn, steps in figs:
        for step in range(1, steps + 1):
            path = out_dir / f"{stem}-{fn.__name__}-{step}.svg"
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"><defs>{markers}</defs>{fn(step)}</svg>\n'
            n += 1
            if path.exists() and path.read_text(encoding="utf-8") == svg:
                continue        # 中身が同じなら書き換えない（更新時刻を変えない。build_slides.py --verify が PDF・ページ画像の古さを時刻で見る）
            path.write_text(svg, encoding="utf-8")
            changed += 1
    print(f"{stem}: 図 {n} 枚を {out_dir} に書き出した（中身が変わったのは {changed} 枚）")
