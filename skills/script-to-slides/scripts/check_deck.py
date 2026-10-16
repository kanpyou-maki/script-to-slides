#!/usr/bin/env python3
"""Marp デッキの機械チェック（台本の 📊 注記との照合・まとめのページ）。ビルドは要らない。

使い方:
    python3 scripts/check_deck.py <デッキ.md> [...]             # 照合する。NG があれば終了コード 1
    python3 scripts/check_deck.py <デッキ.md> --table           # 注記 ↔ ページの対応表（Markdown）も出す
    python3 scripts/check_deck.py <デッキ.md> --deck-only       # 台本との照合を飛ばす（デッキだけで決まる項目）

    対応する台本は、次の順に探す（最初に見つかったもの）:
      1. `--script <台本.md>` で渡したもの
      2. デッキと同じ場所の `<デッキ名>.script.md`（`talk.md` → `talk.script.md`）
      3. デッキのパスの `slides/` を `scripts/` に置き換えた場所
         （`slides/part1/talk.md` → `scripts/part1/talk.md`）
    台本がないデッキ（`00_表紙目次.md`）と、📊 を外してある台本は、デッキだけで決まる項目を見る。
    `scripts/build_slides.py` も、ビルドの前に `--deck-only` と同じ項目を見る（`--verify` は全部）。

見るもの（NG）:
    デッキだけで決まる項目
        空      見出しも中身もないページ（区切りの `---` が1つ多い）
        title   `title` のページが1枚目以外にある
        まとめ幅  まとめのページの1行（`<br>` で区切った1かたまり）が、1行の幅 SUMMARY_WIDTH を超える（折り返す）
        まとめ行  まとめのページの下端が SUMMARY_BOTTOM_MAX を超える（行が多すぎる）
    台本との照合
        注記    注記の数＝ページ数か、P1 から欠番なく昇順か、見出しが一致するか、
                （n/m）が「デッキの中で、同じ見出しの n 枚目／全 m 枚」と合うか（1枚だけの見出しには付けない。
                 同じ見出しが離れたページに出るときも、通して数える）
        まとめ   まとめのページの項目が、台本のまとめの項目と一字一句同じか
                （比べる前に、改行・`<br>`・空白・「、」「。」・`**`・バッククォートを除く。項目の数も比べる。
                 台本の項目は「Nつ目。」の行から、次の「Nつ目。」の行の手前まで。
                 最後の項目だけは、台本のほうが長くても NG にせず、余った文を「候補」として出す
                 （項目のあとの締めの言葉か、デッキから落ちた文かを、人が見る。終了コードには入れない））

見るもの（候補。終了コードには入れない）:
    含み    台本の本編が「代表的な／よくある／主な …Nつ」と数えて並べる文で、その語（「代表的」等）が、
            まとめ・橋渡し以外のページの文字にも、貼っている図（SVG）の文字にもない
            （地図・一覧の図が、並べたもので全部に読めないか。references/figures.md。
             その語がデッキのどこかにあれば出さないので、別の文脈で載っているだけのときは拾えない）

対応表（--table）:
    台本の注記・ページ・見出し・種類・図のファイル・その注記から次の注記までに読む字数を並べる。
    「新しく出る要素」は機械では出ない（図を見て書く）。

まとめのページの寸法（Chrome で描画して測った値。theme.css の `section.summary` を変えたら測り直す）:
    1行の幅   1,076px（1280 − 左右の余白 72×2 − 番号の丸のぶん 2em）。全角1字が 30px なので、全角だけなら35字まで
    文字の幅   全角 30px、半角カナ 15px、英数字と記号は下の表（Hiragino Sans の実測。平均は全角の0.6字ぶん）。
              約物が続くところ（「。）」等）は、前の約物が半角ぶんに詰まる。
              作り直しが済んだ24本の実測と比べて、計算は 0〜11px 広く出る（英字どうしの詰めを見ていないため。狭くは出ない）
    下端      136 ＋ 46.5×行数 ＋ 18×（項目数−1）。確かめてある最大は4項目・11行の 701.5（ページの高さは 720）。
              項目が2〜4つなら11行まで、5つなら10行まで
    `<code>`・太字を含む行は、幅が少し広く出る（この計算では測れない。まとめに入れたら1回ビルドして見る）
"""
import argparse
import math
import pathlib
import re
import sys

SLIDE_MARK = "📊"
EM = 30.0                   # まとめの文字（px）
SUMMARY_WIDTH = 1076.0      # まとめの1行の幅（px）
SUMMARY_TOP = 136.0         # まとめの1行目の上端
SUMMARY_LINE = 46.5         # 1行の高さ（30px × 1.55）
SUMMARY_GAP = 18.0          # 項目のあいだ（0.6em）
SUMMARY_BOTTOM_MAX = 702.0  # 下端の上限（4項目・11行の 701.5 まで）

# 英数字と記号の幅（30px のときの px。Chrome で10字並べて測った）
ASCII_W = dict(zip(
    " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~",
    [9.99, 9.33, 10.68, 19.71, 19.5, 26.37, 23.91, 5.85, 10.68, 10.68, 10.38, 19.68, 7.2, 10.74, 7.2, 14.22,
     19.71, 19.71, 19.71, 19.71, 19.83, 19.71, 19.71, 19.71, 19.71, 19.71, 7.2, 7.2, 15.36, 19.68, 15.36, 17.13, 27.15,
     22.5, 21.36, 22.68, 22.74, 19.29, 18.06, 22.62, 23.34, 7.47, 15.24, 21.21, 18.06, 28.35, 23.22, 23.85, 19.86, 23.85,
     21.78, 20.07, 19.47, 23.19, 21.51, 30.18, 21.66, 20.64, 20.07, 10.38, 14.22, 10.38, 15.99, 15.03, 15.0,
     17.25, 19.38, 17.34, 19.38, 17.64, 11.06, 19.23, 18.51, 7.14, 7.95, 17.25, 6.96, 27.93, 18.54, 18.75, 19.41, 19.38,
     12.9, 16.11, 11.76, 18.54, 16.32, 23.1, 16.08, 16.62, 14.94, 10.41, 11.25, 10.41, 16.29]))
OTHER_W = {"×": 19.68}
CLOSING = "、。，．」』）】〕｝〉》"
OPENING = "「『（【〔｛〈《"

RE_ANNOT = re.compile(rf"^{SLIDE_MARK}\s*P(\d+)\s*—\s*(.+?)\s*$")
RE_STEP = re.compile(r"（(\d+)/(\d+)）$")
RE_CLASS = re.compile(r"<!--\s*_class:\s*([\w-]+)\s*-->")
RE_COMMENT = re.compile(r"<!--.*?-->", re.S)
RE_HEADING = re.compile(r"^#{1,3}\s+(.+?)\s*$", re.M)
RE_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
RE_BR = re.compile(r"<br\s*/?>")
RE_ITEM = re.compile(r"^\d+\.\s+(.*)$")
RE_SUMMARY_HEAD = re.compile(r"^##\s*まとめ")
RE_SUMMARY_ITEM = re.compile(r"^\d+つ目(?:。|は、|、)")
RE_HEDGE = re.compile(r"(代表的|よくある|主な)[^。]*?[0-9０-９]つ")
RE_TAG = re.compile(r"<[^>]+>")


def text_width(s):
    """まとめの1行の幅（px）。"""
    w = 0.0
    for i, ch in enumerate(s):
        nxt = s[i + 1] if i + 1 < len(s) else ""
        if ch in ASCII_W:
            w += ASCII_W[ch]
        elif ch in OTHER_W:
            w += OTHER_W[ch]
        elif "｡" <= ch <= "ﾟ":
            w += EM / 2
        elif ch in CLOSING and nxt and (nxt in CLOSING or nxt in OPENING):
            w += EM / 2
        elif ch in OPENING and nxt and nxt in OPENING:
            w += EM / 2
        else:
            w += EM
    return w


def plain(s):
    """比べるための形（改行・<br>・空白・読点・句点・強調の記号を除く）。"""
    s = RE_BR.sub("", s)
    s = re.sub(r"</?(?:code|strong|b|em)>", "", s)
    return re.sub(r"[\s、。`*]", "", s)


class Page:
    def __init__(self, n, raw):
        self.n = n
        m = RE_CLASS.search(raw)
        self.cls = m.group(1) if m else ""
        self.body = RE_COMMENT.sub("", raw).strip()
        m = RE_HEADING.search(self.body)
        self.heading = RE_BR.sub("", m.group(1)).strip() if m else ""
        self.images = [pathlib.PurePosixPath(p).name for p in RE_IMAGE.findall(self.body)]

    def items(self):
        """まとめのページの項目（`1. …` の行。<br> は残す）。"""
        return [m.group(1) for line in self.body.split("\n") if (m := RE_ITEM.match(line.strip()))]


def parse_deck(path):
    lines = path.read_text(encoding="utf-8").split("\n")
    if lines and lines[0].strip() == "---":                      # 先頭の設定
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), 0)
        lines = lines[end + 1:]
    chunks, cur, fenced = [], [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if line.strip() == "---" and not fenced:
            chunks.append("\n".join(cur))
            cur = []
        else:
            cur.append(line)
    chunks.append("\n".join(cur))
    return [Page(i, raw) for i, raw in enumerate(chunks, 1)]


def script_for(deck, script=None):
    if script:
        return pathlib.Path(script)
    side = deck.with_name(deck.stem + ".script.md")
    if side.is_file():
        return side
    parts = list(deck.resolve().parts)
    if "slides" not in parts:
        return None
    i = len(parts) - 1 - parts[::-1].index("slides")
    p = pathlib.Path(*parts[:i], "scripts", *parts[i + 1:])
    return p if p.is_file() else None


def parse_script(path):
    """(注記のリスト, まとめの項目のリスト)。注記は (P番号, 見出し, n, m, 行番号, 次の注記までに読む字数)。"""
    lines = path.read_text(encoding="utf-8").split("\n")
    annots, spoken = [], 0
    for no, line in enumerate(lines, 1):
        s = line.strip()
        m = RE_ANNOT.match(s)
        if m:
            if annots:
                annots[-1][5] = spoken
            title, step = m.group(2), None
            if (sm := RE_STEP.search(title)):
                title, step = title[:sm.start()], (int(sm.group(1)), int(sm.group(2)))
            title = re.sub(r"（タイトル）$", "", title).strip()
            annots.append([int(m.group(1)), title, step[0] if step else None, step[1] if step else None, no, 0])
            spoken = 0
        elif s and s != "---" and not s.startswith("#") and not s.startswith("**") and not s.startswith("[デモ"):
            spoken += len(re.sub(r"\s", "", s))
    if annots:
        annots[-1][5] = spoken
    start = next((i for i, line in enumerate(lines) if RE_SUMMARY_HEAD.match(line)), None)
    items = []
    if start is not None:
        end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == "---" or lines[i].startswith("## ")), len(lines))
        open_item = False
        for i in range(start + 1, end):
            s = lines[i].strip()
            if RE_SUMMARY_ITEM.match(s):
                items.append(RE_SUMMARY_ITEM.sub("", s))
                open_item = True
            elif s and open_item and not s.startswith(SLIDE_MARK):
                items[-1] += s
    return annots, items


def diff_at(a, b):
    """2つの文字列の、最初に違う位置の前後。"""
    i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return f"…{a[max(0, i - 8):i + 12]}… ／ …{b[max(0, i - 8):i + 12]}…"


def check_layout(pages):
    """デッキだけで決まる項目。(NG のリスト, まとめの要約) を返す。"""
    ng, info = [], ""
    for p in pages:
        if not p.body:
            ng.append(("空", f"P{p.n}: 見出しも中身もない（区切りの `---` が1つ多い）"))
        if p.cls == "title" and p.n != 1:
            ng.append(("title", f"P{p.n}: `title` は1枚目だけ"))
        if p.cls != "summary":
            continue
        items = p.items()
        if not items:
            continue
        rows, widest = 0, 0.0
        for k, item in enumerate(items, 1):
            for j, seg in enumerate(RE_BR.split(item), 1):
                seg = re.sub(r"</?\w+>|[`*]", "", seg).strip()
                w = text_width(seg)
                widest = max(widest, w)
                rows += max(1, math.ceil(w / SUMMARY_WIDTH))
                if w > SUMMARY_WIDTH:
                    over = w - SUMMARY_WIDTH
                    ng.append(("まとめ幅", f"P{p.n} の{k}つ目・{j}行目が {w:,.0f}px（上限 {SUMMARY_WIDTH:,.0f}px。全角{math.ceil(over / EM)}字ぶん超える）: {seg}"))
        bottom = SUMMARY_TOP + SUMMARY_LINE * rows + SUMMARY_GAP * (len(items) - 1)
        if bottom > SUMMARY_BOTTOM_MAX:
            cut = math.ceil((bottom - SUMMARY_BOTTOM_MAX) / SUMMARY_LINE)
            ng.append(("まとめ行", f"P{p.n}: {len(items)}項目・{rows}行で下端が {bottom:,.1f}（上限 {SUMMARY_BOTTOM_MAX:,.0f}）。{cut}行減らす"))
        info = f"まとめ {len(items)}項目・{rows}行（下端 {bottom:,.1f}／上限 {SUMMARY_BOTTOM_MAX:,.0f}）・最長 {widest:,.0f}px（上限 {SUMMARY_WIDTH:,.0f}）"
    return ng, info


def check_annotations(pages, annots):
    ng = []
    if len(annots) != len(pages):
        ng.append(("注記", f"注記 {len(annots)}件とページ {len(pages)}枚の数が合わない"))
    for i, a in enumerate(annots, 1):
        if a[0] != i:
            ng.append(("注記", f"台本 L{a[4]}: P{a[0]} は {i}番目の注記（P1 から欠番なく昇順にする）"))
            break
    total, seen, runs = {}, {}, {}       # runs: ページ番号 -> (同じ見出しの何枚目, 全部で何枚)
    for p in pages:
        total[p.heading] = total.get(p.heading, 0) + 1
    for p in pages:
        seen[p.heading] = seen.get(p.heading, 0) + 1
        runs[p.n] = (seen[p.heading], total[p.heading])
    for p, a in zip(pages, annots):
        if p.heading != a[1]:
            ng.append(("注記", f"P{p.n}（台本 L{a[4]}）: 見出しが違う。台本「{a[1]}」／デッキ「{p.heading}」"))
            continue
        n, m = runs[p.n]
        want = None if m == 1 else (n, m)
        have = (a[2], a[3]) if a[2] else None
        if want != have:
            fmt = lambda v: f"（{v[0]}/{v[1]}）" if v else "（n/m）なし"   # noqa: E731
            ng.append(("注記", f"P{p.n}（台本 L{a[4]}）「{a[1]}」: 台本は{fmt(have)}、デッキの並びでは{fmt(want)}"))
    if len(annots) != len(pages) and len(ng) > 4:      # 数が合わないと、ずれたページより後ろが全部出る
        ng = ng[:4] + [("注記", f"ほか {len(ng) - 4}件（先に、注記の数とページ数をそろえる）")]
    return ng


def check_summary(pages, script_items):
    """(NG のリスト, 候補のリスト)。"""
    ng, maybe = [], []
    page = next((p for p in pages if p.cls == "summary"), None)
    if page is None or not script_items:
        return ng, maybe
    deck_items = page.items()
    if len(deck_items) != len(script_items):
        ng.append(("まとめ", f"P{page.n}: 項目の数が違う。台本 {len(script_items)}／デッキ {len(deck_items)}"))
    for k, (d, s) in enumerate(zip(deck_items, script_items), 1):
        d, s = plain(d), plain(s)
        if d == s:
            continue
        if k == len(script_items) and s.startswith(d):
            maybe.append(("まとめ", f"P{page.n} の{k}つ目のあとに、台本にだけある文（締めの言葉でなければ、デッキに足す）: {s[len(d):]}"))
        else:
            ng.append(("まとめ", f"P{page.n} の{k}つ目が台本と違う（デッキ ／ 台本）: {diff_at(d, s)}"))
    return ng, maybe


def check_hedges(deck, pages, script):
    """台本が含みを付けて数えた文（「代表的なものを3つ」等）の語が、内容ページと図にあるか。候補のリストを返す。"""
    shown = ""
    for p in pages:
        if p.cls in ("summary", "bridge"):
            continue
        shown += p.body
        for rel in RE_IMAGE.findall(p.body):
            f = deck.parent / rel
            if f.suffix == ".svg" and f.is_file():
                shown += RE_TAG.sub(" ", f.read_text(encoding="utf-8"))
    maybe, buf, first, page = [], "", None, None
    for no, line in enumerate(script.read_text(encoding="utf-8").split("\n"), 1):
        s = line.strip()
        if RE_SUMMARY_HEAD.match(s):
            break
        if (m := RE_ANNOT.match(s)):
            if not buf:                      # 文の途中の注記は、文の頭のページのままにする
                page = int(m.group(1))
            continue
        if not s or s == "---" or s.startswith(("#", "**", "[デモ")):
            continue
        first = first or no
        buf += s
        if buf.endswith("。"):
            m = RE_HEDGE.search(buf)
            if m and m.group(1) not in shown:
                where = f"P{page}" if page else "注記の前"
                maybe.append(("含み", f"台本 L{first}（{where}）「{buf}」の「{m.group(1)}」が、ページの文字にも図にもない"
                                      "（地図・一覧の図があれば、小見出しに出す）"))
            buf, first = "", None
    return maybe


def table(pages, annots):
    out = ["| 台本の注記 | ページ | 見出し | 種類 | 図 | 読む字数 | 新しく出る要素 |", "|---|---|---|---|---|---|---|"]
    for i in range(max(len(pages), len(annots))):
        p = pages[i] if i < len(pages) else None
        a = annots[i] if i < len(annots) else None
        note = f"L{a[4]} P{a[0]} {a[1]}" + (f"（{a[2]}/{a[3]}）" if a[2] else "") if a else "（なし）"
        out.append(f"| {note} | {'P' + str(p.n) if p else '（なし）'} | {p.heading if p else ''} | {p.cls if p else ''} | "
                   f"{'、'.join(p.images) if p else ''} | {a[5] if a else ''} | |")
    return "\n".join(out)


def check(deck, deck_only=False, show_table=False, script=None):
    """1本を調べて結果を出す。NG がなければ True。"""
    pages = parse_deck(deck)
    ng, info = check_layout(pages)
    maybe, notes = [], [f"{len(pages)}ページ"]
    script = None if deck_only else script_for(deck, script)
    annots = []
    if script:
        annots, items = parse_script(script)
        if annots:
            ng += check_annotations(pages, annots)
            s_ng, maybe = check_summary(pages, items)
            ng += s_ng
            maybe += check_hedges(deck, pages, script)
            notes.append(f"注記 {len(annots)}件")
        else:
            notes.append("台本に 📊 がないので、照合は飛ばした")
    elif not deck_only:
        notes.append("対応する台本がないので、照合は飛ばした")
    if info:
        notes.append(info)
    print(f"{'NG' if ng else 'OK'} {deck}  " + "／".join(notes))
    for kind, text in ng:
        print(f"  [{kind}] {text}")
    for kind, text in maybe:
        print(f"  [候補] {kind}: {text}")
    if show_table and annots:
        print("\n" + table(pages, annots) + "\n")
    return not ng


def main():
    ap = argparse.ArgumentParser(description="Marp デッキの機械チェック（台本の 📊 注記との照合・まとめのページ）")
    ap.add_argument("decks", nargs="+", type=pathlib.Path)
    ap.add_argument("--table", action="store_true", help="注記 ↔ ページの対応表（Markdown）も出す")
    ap.add_argument("--deck-only", action="store_true", help="台本との照合を飛ばす")
    ap.add_argument("--script", metavar="台本", help="対応する台本（デッキ1本のときだけ。省くと決まった場所から探す）")
    a = ap.parse_args()
    results = [check(d, a.deck_only, a.table, a.script) for d in a.decks]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
