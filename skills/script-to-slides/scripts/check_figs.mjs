// スライドの図（SVG）を実際に描画して測る。ふつうは scripts/build_slides.py から呼ばれる。
//
//   MARP_NODE_MODULES=<marp-cli の node_modules/> node scripts/check_figs.mjs <図.svg> [...]
//
// このファイルは minorun365/minorun-marp-skill の tools/check-svg-box-fit.mjs（Apache License 2.0）をもとに、
// 見る項目（文字サイズ・ページ番号の位置・小見出しの色・濃い文字の数）を足して書き換えたもの。
// 元のライセンスは LICENSES/Apache-2.0.txt、出典は THIRD_PARTY_NOTICES.md。
//
// 見るもの（座標は viewBox の単位。図は等倍で貼るので、そのままスライド上の px）:
//   収まり   文字が、重なっている箱（rect）の内側に 14px 以上の余白で収まっているか
//   はみ出し 文字が viewBox の外に出ていないか
//   文字     19px 未満の文字がないか（注釈の下限）。28px 未満は「注釈サイズ」として、どの文字かを1行ずつ出す
//   右下     ページ番号が来る右下の隅（x>1060 かつ y>452）に文字がかかっていないか
// 候補（終了コードには入れない。人が見る）:
//   小見出しの色  箱の外の文字が、色のついた箱（紺・赤・緑。青は件数が多くなるので見ない）のすぐ上（すきま 30px まで・横に 40px 以上重なる）にあり、
//                 箱の塗りと色が違う（references/figures.md: 箱の上の小見出しは、箱と同じ色）。
//                 登場人物の名前や、箱の上に置いた別の要素も出る
//   濃い文字の数  図ごとの、薄くしていない <text> の数（かっこの中は、薄くした数）。目安は、初めて出す図で7個程度、
//                 積み上げた最終段で12個程度。2行の箱は2、ターミナルの行も1行ずつ数えるので、多めに出る（空の文字は数えない）。12個を超える図に「!」
// 文字の幅はソースからはわからないので、描画して getBBox() で測る。
// 文字を重ねるのが意図の矩形（差分のハイライトなど）は、rect に data-hl="1" を付けると対象外になる。
// puppeteer-core は marp-cli に同梱のものを借りる。
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';

const nm = process.env.MARP_NODE_MODULES;
if (!nm) { console.error('MARP_NODE_MODULES を指定する（scripts/build_slides.py 経由なら自動）'); process.exit(2); }
const require = createRequire(nm.endsWith('/') ? nm : nm + '/');
const puppeteer = require('puppeteer-core');
const CHROME = process.env.CHROME_PATH || (process.platform === 'darwin'
  ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : '/usr/bin/google-chrome');
const PAD = 14, MIN_NOTE = 19, MIN_LABEL = 28, HEAD_GAP = 30, HEAD_OVERLAP = 40, DARK_MAX = 12;
const STRONG = { '#1E3A5F': '紺', '#C0392B': '赤', '#1E8B4F': '緑' };
const COLOR = { ...STRONG, '#2E86C1': '青', '#1A1A2E': '黒', '#555555': '濃い灰', '#9AA5B1': '灰', '#FFFFFF': '白' };

const files = process.argv.slice(2);
if (!files.length) { console.error('svg を指定'); process.exit(2); }
// コンテナなど root で動かすときは CHROME_NO_SANDBOX=1 にする（marp-cli と同じ変数）
const args = process.env.CHROME_NO_SANDBOX ? ['--no-sandbox', '--disable-gpu'] : [];
const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args });
const page = await browser.newPage();
let ng = 0, texts = 0, notes = 0;
const counts = [];
for (const f of files) {
  await page.setContent(`<html><body style="margin:0">${fs.readFileSync(f, 'utf8')}</body></html>`);
  await page.evaluate(() => document.fonts.ready);
  const res = await page.evaluate((HEAD_GAP, HEAD_OVERLAP) => {
    const svg = document.querySelector('svg'), vb = svg.viewBox.baseVal;
    const dim = e => { const g = e.closest('g[opacity]'); return !!g && +g.getAttribute('opacity') < 1; };
    const rects = [...svg.querySelectorAll('rect')].filter(r => r.dataset.hl !== '1')
      .map(r => ({ x: +r.getAttribute('x'), y: +r.getAttribute('y'), w: +r.getAttribute('width'), h: +r.getAttribute('height'),
        fill: (r.getAttribute('fill') || '').toUpperCase(), dim: dim(r) }));
    return [...svg.querySelectorAll('text')].map(t => {
      const b = t.getBBox(), cx = b.x + b.width / 2, cy = b.y + b.height / 2;
      // いちばん小さい箱（内側の箱）と比べる
      const box = rects.filter(r => cx >= r.x && cx <= r.x + r.w && cy >= r.y && cy <= r.y + r.h).sort((a, c) => a.w * a.h - c.w * c.h)[0];
      const fill = (t.getAttribute('fill') || '').toUpperCase();
      // すぐ下の箱（箱の外の文字だけ。いちばん近いもの）
      const below = box ? null : rects.filter(r => r.dim === dim(t) && r.y - (b.y + b.height) >= -4 && r.y - (b.y + b.height) <= HEAD_GAP
        && Math.min(b.x + b.width, r.x + r.w) - Math.max(b.x, r.x) >= HEAD_OVERLAP).sort((a, c) => a.y - c.y)[0];
      return { text: t.textContent.trim(), size: parseFloat(getComputedStyle(t).fontSize), fill, dim: dim(t), below: below ? below.fill : null,
        pad: box ? Math.round(Math.min(b.x - box.x, box.x + box.w - (b.x + b.width))) : null,
        out: b.x < 0 || b.y < 0 || b.x + b.width > vb.width || b.y + b.height > vb.height,
        corner: b.x + b.width > 1060 && b.y + b.height > 452 };
    });
  }, HEAD_GAP, HEAD_OVERLAP);
  const shown = res.filter(r => r.text);   // 名前のない人物（person(…, "")）の空の文字は数えない
  const dark = shown.filter(r => !r.dim).length;
  counts.push(`${path.basename(f, '.svg').replace(/^s\d+-\d+-/, '')} ${dark}${dark > DARK_MAX ? '!' : ''}${shown.length > dark ? `（${shown.length - dark}）` : ''}`);
  for (const r of res) {
    texts++;
    const bad = [];
    if (r.pad !== null && r.pad < PAD) bad.push(`箱の縁まで ${r.pad}px（最低 ${PAD}px）`);
    if (r.out) bad.push('viewBox の外');
    if (r.size < MIN_NOTE) bad.push(`文字が ${r.size}px（注釈の下限 ${MIN_NOTE}px）`);
    if (r.corner) bad.push('右下のページ番号の位置にかかる');
    if (r.size >= MIN_NOTE && r.size < MIN_LABEL) { notes++; console.log(`注釈 ${path.basename(f)} 「${r.text.slice(0, 24)}」 ${r.size}px`); }
    if (r.below && STRONG[r.below] && r.fill !== r.below)
      console.log(`候補 ${path.basename(f)} 「${r.text.slice(0, 24)}」（${COLOR[r.fill] || r.fill}）が、すぐ下の${STRONG[r.below]}の箱と違う色`);
    if (bad.length) { ng++; console.log(`NG ${path.basename(f)} 「${r.text.slice(0, 24)}」 ${bad.join(' / ')}`); }
  }
}
await browser.close();
if (counts.length) console.log(`濃い文字の数（かっこは薄くした数。${DARK_MAX}個を超える図に「!」）: ${counts.join(' / ')}`);
console.log(`図 ${files.length} 枚・文字 ${texts} 件を実測、NG ${ng} 件（${MIN_LABEL}px 未満の注釈サイズ ${notes} 件）`);
process.exit(ng ? 1 : 0);
