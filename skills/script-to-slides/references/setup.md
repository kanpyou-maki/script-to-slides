# 準備（最初に1回）

## 要るもの

| もの | 使う道具 | 入れ方の例 |
|------|---------|-----------|
| Python 3.9 以上 | すべて | OS の標準か、python.org |
| Pillow | `sheet_pages.py` | `pip install pillow` |
| Node.js 18 以上 | `build_slides.py`（marp-cli を `npx` で動かす）・`check_figs.mjs` | nodejs.org |
| Chrome か Chromium | PDF・ページ画像の書き出しと、図の検査 | ふつうに入れたものでよい。場所が既定と違えば `CHROME_PATH` で渡す |
| Noto Sans JP | 図とスライドの文字 | Google Fonts から入れる。図の文字幅はこのフォントを基準にしている |

- marp-cli は `build_slides.py` が `npx @marp-team/marp-cli` で呼ぶ（入れておかなくてよい。初回は取得に時間がかかる）
- 図の検査（`check_figs.mjs`）は、marp-cli に同梱の puppeteer-core を借りる。**一度 marp を動かしたあと**でないと、検査を飛ばしたと表示される
- Chrome の既定の場所: macOS は `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`、それ以外は `/usr/bin/google-chrome`

## フォントについて

文字の幅はフォントで変わる。図の検査（余白・はみ出し）は、そのマシンにあるフォントで測る。
Noto Sans JP を入れずに Hiragino（macOS）や Yu Gothic（Windows）で測ると、ほかの環境で余白が足りなくなることがある。
人に渡す・別のマシンで書き出すなら、Noto Sans JP で検査を通しておく。

## 置き方

デッキの置き場所の上の階層に、`assets/` の `theme.css`・`components.css`・`figlib.py` を写す。
`build_slides.py` は、デッキから上へたどって最初に `theme.css` がある場所をテーマの場所にする。

```
my-talk/
├── theme.css / components.css / figlib.py   # assets/ から写す
├── intro.md                # デッキ
├── intro.script.md         # 台本（デッキ名 + .script.md。--script で別の場所も渡せる）
├── intro_figs.py           # 図（examples/hand-drip/talk_figs.py を写して書き換える）
└── figs/                   # 書き出した SVG（自動）
```

デッキが多いときは `slides/` と `scripts/` に分けてもよい（`slides/part1/a.md` の台本は `scripts/part1/a.md`）。
