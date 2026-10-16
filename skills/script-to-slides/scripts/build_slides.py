#!/usr/bin/env python3
"""Marp デッキを書き出す（デッキの検査 → 図の書き出し → 図の検査 → テーマの結合 → PDF／ページ画像）。

使い方:
    python3 scripts/build_slides.py <デッキ.md> [...]            # PDF をデッキの隣に書き出す
    python3 scripts/build_slides.py <デッキ.md> --png <出力先>   # ページ画像（PNG）も書き出す
    python3 scripts/build_slides.py <デッキ.md> --no-pdf --png <出力先>   # 画像だけ
    python3 scripts/build_slides.py <デッキ.md> --verify [--png <ビルド済みの画像の場所>]
                                                              # 何も書き出さず、ビルド済みのものを確かめる（レビュー用）

やること（デッキ1本ごと）:
    0. `scripts/check_deck.py` のうち、デッキだけで決まる項目を見る（空のページ・まとめのページの幅と行数）。
       ビルドの前に結果が出る。NG があってもビルドは続け、終了コードを 1 にする
    1. デッキの隣に `<デッキ名>_figs.py` があれば実行して、`figs/` に SVG を書き出す
    2. `scripts/check_figs.mjs` で、その図の文字の収まりと文字サイズを実測する（NG があれば終了コード 1）。
       続けて、`_figs.py` のソースから「候補」を出す（終了コードには入れない。人が見る。下の「図の候補」）
    3. `theme.css` と `components.css` を結合して `.theme-build.css` を作る
       （Marp の @import はデッキのディレクトリ基準で解決されるので、結合して渡す）
    4. marp-cli で PDF（と PNG）を書き出す。`--no-stdin` を付け、標準入力も閉じる
       （付けないと、標準入力待ちで止まることがある）
    5. `.theme-build.css` を消す

`--verify`（デッキのある場所に何も書かない。marp も動かさない）:
    a. `scripts/check_deck.py` の全部（台本の 📊 注記とページの照合・まとめの一字一句・空のページ・まとめの幅と行数）。
       注記 ↔ ページの対応表も出す
    b. `<デッキ名>_figs.py` を一時フォルダへ書き出し、`figs/` の SVG と1枚ずつ比べる（古い図・余った図・足りない図）。
       デッキが貼っている図が `figs/` にあるかも見る
    c. `scripts/check_figs.mjs`（`figs/` の SVG を測る。28px 未満の文字の行も出る）と、図の候補
    d. PDF がデッキ・図・テーマより古くないか（古ければ「注意」。終了コードには入れない）
    e. `--png` を付けたとき: その場所のページ画像がページ数と同じ枚数あり、デッキ・図・テーマより新しいか

図の候補（`_figs.py` を実行せず、ソースを読む。references/figures.md「図の規則」）:
    ×と否定  `cross(` を呼ぶ図の関数の中の文字に、否定の語（ない・なく・拒否・ません・せず）がある
             （× を重ねた矢印の隣に、否定の語を置かない。× が否定を担うので、文字は「から」「へ」まで）。
             × から離れた場所の文字も出る（座標は見ない）。人が見て判断する
    色       このデッキの箱（`box(`・`box2(`）と、同じセクションの `_figs.py` の箱とで、塗りの色（紺・青・赤・緑）が違うのに、
             文言に COMMON_MIN 字以上の共通部分がある（同じものは同じ色。言い換えた同じ意味の語は拾えないので、
             デッキの中心の事実は、動詞の語幹で同じセクションの `_figs.py` を検索する）。危ない状態の赤と、決まりの紺のように、意味が違う組も出る

ページ画像の出力先は、デッキの場所の外（一時フォルダなど）にする。
"""
import argparse
import ast
import filecmp
import glob
import os
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_deck  # noqa: E402

MARP = ["npx", "--yes", "@marp-team/marp-cli@latest", "--no-stdin"]


def slides_root(deck):
    """テーマ（theme.css と components.css）のある場所。デッキの場所から上へたどって、最初に theme.css がある場所。"""
    for parent in deck.resolve().parents:
        if (parent / "theme.css").is_file():
            return parent
    sys.exit(f"{deck}: 上の階層に theme.css がない（assets/theme.css と components.css を写す）")


def marp_node_modules():
    """check_figs.mjs が puppeteer-core を借りる先（marp-cli の node_modules）を探す。"""
    if os.environ.get("MARP_NODE_MODULES"):
        return os.environ["MARP_NODE_MODULES"]
    hits = glob.glob(os.path.expanduser("~/.npm/_npx/*/node_modules/puppeteer-core"))
    return str(pathlib.Path(hits[0]).parent) + "/" if hits else None


def run(cmd, **kw):
    return subprocess.run(cmd, stdin=subprocess.DEVNULL, **kw)


def fig_svgs(deck):
    return sorted(glob.glob(str(deck.parent / "figs" / f"{deck.stem}-*.svg")))


def check_figs(svgs):
    """図の検査。NG がなければ True。"""
    nm = marp_node_modules()
    if not svgs:
        return True
    if not nm:
        print("注意: marp-cli の node_modules が見つからないので、図の検査を飛ばした（1度 marp を実行すると入る）")
        return True
    return run(["node", str(HERE / "check_figs.mjs"), *svgs], env={**os.environ, "MARP_NODE_MODULES": nm}).returncode == 0


NEGATION = re.compile(r"ない|なく|拒否|ません|せず")
FILLS = {"NAVY": "紺", "BLUE": "青", "RED": "赤", "GREEN": "緑"}
COMMON_MIN = 6      # 5字にすると、セクション4だけで8件に増える


def _fig_funcs(figs_py):
    """_figs.py の（図の関数, 説明文, モジュールの文字列の定数）。"""
    tree = ast.parse(figs_py.read_text(encoding="utf-8"))
    consts = {t.id: n.value.value for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
              and isinstance(n.value.value, str) for t in n.targets if isinstance(t, ast.Name)}
    return [(fn, ast.get_docstring(fn), consts) for fn in tree.body if isinstance(fn, ast.FunctionDef)]


def _boxes(figs_py):
    """色のついた箱の（文言, 色の名前, 図の関数の名前）。文言が式のとき（f文字列など）は拾えない。"""
    out = []
    for fn, _, consts in _fig_funcs(figs_py):
        for c in ast.walk(fn):
            name = getattr(getattr(c, "func", None), "id", "")
            if not isinstance(c, ast.Call) or name not in ("box", "box2"):
                continue
            labels = c.args[4:5] if name == "box" else c.args[3:5]
            fill = next((k.value for k in c.keywords if k.arg == "fill"), c.args[5] if len(c.args) > 5 else None)
            label = "".join(a.value if isinstance(a, ast.Constant) and isinstance(a.value, str) else consts.get(getattr(a, "id", ""), "")
                            for a in labels)
            if label and getattr(fill, "id", "") in FILLS:
                out.append((label, FILLS[fill.id], fn.name))
    return out


def _common(a, b):
    """いちばん長い共通部分。"""
    best = ""
    for i in range(len(a)):
        for j in range(i + len(best) + 1, len(a) + 1):
            if a[i:j] not in b:
                break
            best = a[i:j]
    return best


def fig_candidates(figs_py):
    """図の候補を出す（× と否定の語・色）。終了コードには入れない。"""
    lines = []
    for fn, doc, _ in _fig_funcs(figs_py):
        if not any(isinstance(c, ast.Call) and getattr(c.func, "id", "") == "cross" for c in ast.walk(fn)):
            continue
        for c in ast.walk(fn):
            if isinstance(c, ast.Constant) and isinstance(c.value, str) and c.value != doc and NEGATION.search(c.value):
                lines.append(f"候補 ×と否定 {figs_py.name}:{c.lineno} {fn.name}() は × を使う図で、文字に否定の語: 「{c.value}」")
    mine, seen = _boxes(figs_py), set()
    for other in sorted(figs_py.parent.glob("*_figs.py")):
        stem = other.stem.replace("_figs", "")
        for label, color, fn in mine:
            for label2, color2, fn2 in (_boxes(other) if other != figs_py else mine):
                key = (frozenset((label, label2)), frozenset((color, color2)))
                com = _common(label, label2)
                if color == color2 or len(com) < COMMON_MIN or key in seen:
                    continue
                seen.add(key)
                lines.append(f"候補 色 {figs_py.name} {fn}() の{color}の箱「{label}」と、{stem} {fn2}() の{color2}の箱「{label2}」に、共通の「{com}」")
    print("\n".join(lines) if lines else f"図の候補（× と否定の語・色）: {figs_py.name} はなし")


def build(deck, png_dir, pdf, check):
    deck = deck.resolve()
    root = slides_root(deck)
    ok = True
    if check:
        ok = check_deck.check(deck, deck_only=True)
    figs_py = deck.with_name(deck.stem + "_figs.py")
    if figs_py.exists():
        if run([sys.executable, str(figs_py)]).returncode:
            sys.exit(f"{figs_py.name}: 図の書き出しに失敗")
        if check:
            ok = check_figs(fig_svgs(deck)) and ok
            fig_candidates(figs_py)
    theme = root / ".theme-build.css"
    theme.write_text((root / "theme.css").read_text(encoding="utf-8") + "\n"
                     + (root / "components.css").read_text(encoding="utf-8"), encoding="utf-8")
    common = [str(deck), "--theme-set", str(theme), "--html", "--allow-local-files"]
    try:
        if pdf:
            r = run(MARP + common + ["-o", str(deck.with_suffix(".pdf"))], capture_output=True, text=True)
            print(f"{deck.name}: PDF " + ("OK" if r.returncode == 0 else "失敗\n" + r.stderr[-800:]))
            ok = ok and r.returncode == 0
        if png_dir:
            out = pathlib.Path(png_dir)
            out.mkdir(parents=True, exist_ok=True)
            for old in glob.glob(str(out / f"{deck.stem}.*.png")):      # ページが減ったときに、前の画像が残らないようにする
                os.remove(old)
            r = run(MARP + common + ["--images", "png", "-o", str(out / f"{deck.stem}.png")], capture_output=True, text=True)
            n = len(glob.glob(str(out / f"{deck.stem}.*.png")))
            pages = len(check_deck.parse_deck(deck))
            print(f"{deck.name}: ページ画像 {n} 枚 → {out}" if r.returncode == 0 else f"{deck.name}: 画像の書き出しに失敗\n" + r.stderr[-800:])
            if r.returncode == 0 and n != pages:
                print(f"NG {deck.name}: ページ画像 {n} 枚が、デッキの {pages} ページと合わない")
            ok = ok and r.returncode == 0 and n == pages
    finally:
        theme.unlink(missing_ok=True)
    return ok


def verify(deck, png_dir, script=None):
    """何も書き出さずに、ビルド済みのものを確かめる。NG がなければ True。"""
    deck = deck.resolve()
    root = slides_root(deck)
    ok = check_deck.check(deck, show_table=True, script=script)      # 注記 ↔ ページの対応表も出す
    pages = check_deck.parse_deck(deck)
    svgs = fig_svgs(deck)
    figs_dir = deck.parent / "figs"

    # b. 図が _figs.py の出力と同じか
    figs_py = deck.with_name(deck.stem + "_figs.py")
    if figs_py.exists():
        with tempfile.TemporaryDirectory() as tmp:
            r = run([sys.executable, "-B", str(figs_py)], env={**os.environ, "FIGS_OUT_DIR": tmp}, capture_output=True, text=True)
            if r.returncode:
                print(f"NG {figs_py.name}: 図の書き出しに失敗\n{r.stderr[-800:]}")
                ok = False
            else:
                fresh = {p.name for p in pathlib.Path(tmp).glob("*.svg")}
                have = {pathlib.Path(s).name for s in svgs}
                stale = sorted(n for n in fresh & have if not filecmp.cmp(pathlib.Path(tmp) / n, figs_dir / n, shallow=False))
                problems = ([f"古い図（_figs.py の出力と違う）: {'、'.join(stale)}"] if stale else []) \
                    + ([f"figs/ にない図: {'、'.join(sorted(fresh - have))}"] if fresh - have else []) \
                    + ([f"_figs.py が書き出さない図が figs/ に残っている: {'、'.join(sorted(have - fresh))}"] if have - fresh else [])
                for msg in problems:
                    print(f"NG {deck.name}: {msg}")
                if not problems:
                    print(f"OK {deck.name}: 図 {len(fresh)} 枚は _figs.py の出力と同じ")
                ok = ok and not problems
    used = [n for p in pages for n in p.images if n.endswith(".svg")]
    missing = sorted({n for n in used if not (figs_dir / n).exists()})
    if missing:
        print(f"NG {deck.name}: デッキが貼っている図が figs/ にない: {'、'.join(missing)}")
        ok = False
    unused = sorted({pathlib.Path(s).name for s in svgs} - set(used))
    if unused:
        print(f"注意 {deck.name}: どのページにも貼っていない図: {'、'.join(unused)}")

    # c. 図の検査と、図の候補
    ok = check_figs(svgs) and ok
    if figs_py.exists():
        fig_candidates(figs_py)

    # d・e. PDF とページ画像が、もとのファイルより古くないか
    sources = [deck, root / "theme.css", root / "components.css", *map(pathlib.Path, svgs)]
    newest = max(p.stat().st_mtime for p in sources if p.exists())
    pdf = deck.with_suffix(".pdf")
    if not pdf.exists():
        print(f"注意 {deck.name}: PDF がない")
    elif pdf.stat().st_mtime < newest:
        print(f"注意 {deck.name}: PDF が、デッキ・図・テーマより古い（書き出し直す）")
    else:
        print(f"OK {deck.name}: PDF はデッキ・図・テーマより新しい")
    if png_dir:
        pngs = glob.glob(str(pathlib.Path(png_dir) / f"{deck.stem}.*.png"))
        if len(pngs) != len(pages):
            print(f"NG {deck.name}: ページ画像 {len(pngs)} 枚が、デッキの {len(pages)} ページと合わない（{png_dir}）")
            ok = False
        elif min(os.stat(p).st_mtime for p in pngs) < newest:
            print(f"NG {deck.name}: ページ画像が、デッキ・図・テーマより古い（{png_dir}）")
            ok = False
        else:
            print(f"OK {deck.name}: ページ画像 {len(pngs)} 枚は、ページ数と同じで、デッキ・図・テーマより新しい")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("decks", nargs="+", type=pathlib.Path)
    ap.add_argument("--png", metavar="場所", help="ページ画像（PNG）の出力先。デッキの場所の外にする。--verify のときは、ビルド済みの画像の場所")
    ap.add_argument("--no-pdf", action="store_true", help="PDF を書き出さない")
    ap.add_argument("--no-check", action="store_true", help="デッキと図の検査を飛ばす")
    ap.add_argument("--verify", action="store_true", help="何も書き出さず、ビルド済みのもの（図・PDF・ページ画像）と台本の注記を確かめる")
    ap.add_argument("--script", metavar="台本", help="--verify で照合する台本（省くと決まった場所から探す。check_deck.py の説明）")
    a = ap.parse_args()
    sys.stdout.reconfigure(line_buffering=True)     # 図の検査（node）の出力と、順番が入れ替わらないようにする
    if a.verify:
        results = [verify(d, a.png, a.script) for d in a.decks]
    else:
        results = [build(d, a.png, not a.no_pdf, not a.no_check) for d in a.decks]
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
