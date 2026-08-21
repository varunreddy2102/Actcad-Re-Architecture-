#!/usr/bin/env python3
"""Build a standalone, zero-dependency HTML slide deck from a Marp markdown file.

Usage:
    pip install markdown
    python3 scripts/build-deck.py docs/tejascad-mgmt-brief.md

Writes <name>-deck.html alongside the source.

Why hand-rolled rather than reveal.js: the existing exec deck pulls ~51 files
from CDNs, so it renders as a blank page without internet. This produces a
single self-contained file that works offline, on any laptop, forever.

Controls: arrows / space / PgUp / PgDn to move, O or Esc for the overview
grid, F for fullscreen, P to print (one slide per page).
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import markdown

FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
LEAD_RE = re.compile(r"<!--\s*_class:\s*lead\s*-->", re.I)
DIRECTIVE_RE = re.compile(r"<!--\s*_(?:class|paginate)\s*:.*?-->\s*", re.I)


def render(md_text: str) -> str:
    return markdown.Markdown(
        extensions=["extra", "sane_lists", "smarty", "md_in_html"]
    ).convert(md_text)


def title_of(chunk: str) -> str:
    m = re.search(r"^#{1,3}\s+(.+)$", chunk, re.M)
    if not m:
        return "—"
    return re.sub(r"[*`_]", "", m.group(1)).strip()


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
--primary:#1e3a5c; --deep:#102542; --accent:#c08847; --accent-lt:#e8d5b7;
--bg:#fff; --cream:#faf7f2; --slate:#f4f1ec; --text:#1a1a1a; --text2:#555;
--text3:#8a8378; --border:#e0d8cc; --danger:#b03c3c; --ok:#2d6f4b; --warn:#b88130;
}
html,body{height:100%;background:var(--deep);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
color:var(--text);-webkit-font-smoothing:antialiased}

.slide{position:fixed;inset:0;background:var(--bg);padding:5vh 6vw 9vh;
overflow-y:auto;display:none;flex-direction:column;
font-size:clamp(13px,1.42vw,21px);line-height:1.5}
.slide.on{display:flex}
.slide.lead{justify-content:center;align-items:flex-start;
background:linear-gradient(160deg,var(--deep) 0%,var(--primary) 100%);color:#fff;
padding:6vh 8vw}
.slide.lead h1{color:#fff;font-size:2.9em;line-height:1.08;border:0;margin-bottom:.35em;
letter-spacing:-.02em}
.slide.lead h3{color:var(--accent-lt);font-weight:500;font-size:1.15em;margin-bottom:1.1em}
.slide.lead p{color:#d8e2ee;max-width:52em}
.slide.lead strong{color:#fff}
.slide.lead code{background:rgba(255,255,255,.13);color:var(--accent-lt)}
.slide.lead a{color:var(--accent-lt)}

h1{font-size:2.05em;color:var(--primary);line-height:1.12;letter-spacing:-.015em;margin-bottom:.4em}
h2{font-size:1.5em;color:var(--primary);line-height:1.16;letter-spacing:-.012em;
border-bottom:3px solid var(--primary);padding-bottom:.28em;margin-bottom:.65em}
h3{font-size:1.12em;color:var(--deep);margin:.9em 0 .4em}
h4{font-size:.94em;color:var(--accent);text-transform:uppercase;letter-spacing:.08em;margin:.9em 0 .35em}
p{margin:.42em 0;max-width:62em}
strong{color:var(--primary);font-weight:640}
em{font-style:italic;color:var(--text2)}
a{color:var(--primary)}
ul,ol{margin:.42em 0 .42em 1.25em;max-width:62em}
li{margin:.26em 0}
li>ul,li>ol{margin:.2em 0 .2em 1em}
hr{border:0;border-top:1px solid var(--border);margin:1em 0}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
background:var(--slate);padding:.1em .38em;border-radius:3px;font-size:.86em;color:var(--deep)}

table{border-collapse:collapse;margin:.6em 0;width:100%;font-size:.85em;line-height:1.4}
th,td{border:1px solid var(--border);padding:.44em .6em;text-align:left;vertical-align:top}
th{background:var(--primary);color:#fff;font-weight:600;font-size:.95em;
text-transform:uppercase;letter-spacing:.03em}
tbody tr:nth-child(even){background:var(--cream)}
td strong{color:var(--deep)}

blockquote{border-left:4px solid var(--accent);background:var(--cream);
padding:.6em .95em;margin:.7em 0;border-radius:0 5px 5px 0;max-width:62em}
blockquote p{margin:.2em 0}
blockquote strong{color:var(--deep)}

.big{font-size:1.22em;line-height:1.34;color:var(--primary);font-weight:600;
background:var(--cream);border-left:4px solid var(--accent);padding:.7em .95em;
margin:.7em 0;border-radius:0 5px 5px 0;max-width:62em}
.big p{margin:0;max-width:none}
.big strong{color:var(--deep)}

/* chrome */
#bar{position:fixed;left:0;top:0;height:3px;background:var(--accent);width:0;
z-index:60;transition:width .18s ease}
#num{position:fixed;right:2vw;bottom:2.4vh;font-size:12px;color:var(--text3);
z-index:60;font-variant-numeric:tabular-nums;letter-spacing:.04em}
.lead #num,.slide.lead~#num{color:var(--accent-lt)}
#tag{position:fixed;left:6vw;bottom:2.4vh;font-size:10.5px;color:var(--text3);
z-index:60;text-transform:uppercase;letter-spacing:.11em}
#appx{position:fixed;right:2vw;top:2.2vh;font-size:10px;color:#fff;z-index:60;
background:var(--accent);padding:.28em .7em;border-radius:11px;
text-transform:uppercase;letter-spacing:.1em;display:none;font-weight:600}
body.in-appendix #appx{display:block}

/* overview */
#ov{position:fixed;inset:0;background:var(--deep);z-index:80;display:none;
overflow-y:auto;padding:3vh 3vw}
#ov.on{display:block}
#ov h2{color:#fff;border-color:var(--accent);font-size:1.3em;margin-bottom:.7em}
#ov .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:11px}
#ov .card{background:#fff;border-radius:6px;padding:11px 13px;cursor:pointer;
border:2px solid transparent;transition:transform .1s,border-color .1s;min-height:74px}
#ov .card:hover{transform:translateY(-2px);border-color:var(--accent)}
#ov .card .n{font-size:10px;color:var(--text3);font-variant-numeric:tabular-nums}
#ov .card .t{font-size:12.5px;color:var(--primary);font-weight:600;line-height:1.3;margin-top:3px}
#ov .card.ap{background:var(--cream)}
#ov .hint{color:#94a8c0;font-size:11.5px;margin-top:1.4em;letter-spacing:.03em}

@media print{
 /* A4 landscape - real paper, not 16:9 pixels. Height is auto with a
    min-height so a dense slide spills to a second sheet rather than
    silently clipping a table mid-row. Completeness beats tidiness in
    a handout. */
 @page{size:A4 landscape;margin:0}
 html,body{background:#fff}
 .slide{position:relative;display:block!important;inset:auto;
 width:297mm;min-height:206mm;height:auto;overflow:visible;
 page-break-after:always;break-after:page;
 font-size:10.5pt;line-height:1.42;padding:13mm 15mm 11mm}
 .slide:last-child{page-break-after:auto;break-after:auto}
 .slide.lead{min-height:206mm;-webkit-print-color-adjust:exact;print-color-adjust:exact}
 .slide.lead h1{font-size:2.3em}
 h2{font-size:1.34em;margin-bottom:.5em}
 table{font-size:.82em;page-break-inside:avoid;break-inside:avoid}
 th,td{padding:.34em .5em}
 blockquote,.big{page-break-inside:avoid;break-inside:avoid;margin:.5em 0}
 .big{font-size:1.1em}
 h2,h3,h4{page-break-after:avoid;break-after:avoid}
 th,tbody tr:nth-child(even),blockquote,.big,.slide.lead{
 -webkit-print-color-adjust:exact;print-color-adjust:exact}
 #bar,#num,#tag,#ov,#appx{display:none!important}
}
"""

JS = """
var S=[].slice.call(document.querySelectorAll('.slide')),i=0,N=S.length;
var bar=document.getElementById('bar'),num=document.getElementById('num'),
    ov=document.getElementById('ov'),body=document.body;
function go(n){
  i=Math.max(0,Math.min(N-1,n));
  S.forEach(function(s,k){s.classList.toggle('on',k===i)});
  bar.style.width=(N<2?100:(i/(N-1))*100)+'%';
  num.textContent=(i+1)+' / '+N;
  body.classList.toggle('in-appendix',S[i].dataset.ap==='1');
  S[i].scrollTop=0;
  try{location.hash=i+1}catch(e){}
}
function ovToggle(f){ov.classList.toggle('on',f===undefined?!ov.classList.contains('on'):f)}
document.addEventListener('keydown',function(e){
  var o=ov.classList.contains('on');
  if(e.key==='Escape'){ovToggle(!o);e.preventDefault();return}
  if(e.key==='o'||e.key==='O'){ovToggle();e.preventDefault();return}
  if(o){if(e.key==='Enter')ovToggle(false);return}
  switch(e.key){
    case 'ArrowRight':case 'ArrowDown':case ' ':case 'PageDown':go(i+1);e.preventDefault();break;
    case 'ArrowLeft':case 'ArrowUp':case 'PageUp':go(i-1);e.preventDefault();break;
    case 'Home':go(0);e.preventDefault();break;
    case 'End':go(N-1);e.preventDefault();break;
    case 'f':case 'F':
      if(document.fullscreenElement)document.exitFullscreen();
      else document.documentElement.requestFullscreen();e.preventDefault();break;
    case 'p':case 'P':window.print();e.preventDefault();break;
  }
});
document.querySelectorAll('#ov .card').forEach(function(c){
  c.addEventListener('click',function(){go(+c.dataset.i);ovToggle(false)})
});
var x=null;
document.addEventListener('touchstart',function(e){x=e.changedTouches[0].clientX},{passive:true});
document.addEventListener('touchend',function(e){
  if(x===null)return;var d=e.changedTouches[0].clientX-x;
  if(Math.abs(d)>55)go(i+(d<0?1:-1));x=null},{passive:true});
var h=parseInt((location.hash||'').replace('#',''),10);
go(isNaN(h)?0:h-1);
"""


def build(src: Path) -> Path:
    raw = src.read_text(encoding="utf-8")

    # Guard: if the frontmatter's closing "---" is missing, the lazy match runs
    # on to the first slide separator and silently swallows slide 1. That failed
    # quietly twice. Detect it by what got captured: real frontmatter is only
    # key/value lines, so a heading or HTML comment inside it means over-match.
    m = FRONTMATTER_RE.match(raw)
    if m and re.search(r"^#{1,3}\s|<!--", m.group(0), re.M):
        raise SystemExit(
            f"{src}: YAML frontmatter has no closing '---', so slide 1 would be "
            "swallowed.\nAdd a '---' line after the style block."
        )
    raw = FRONTMATTER_RE.sub("", raw)

    chunks = [c.strip() for c in raw.split("\n---\n") if c.strip()]

    slides, cards = [], []
    in_appendix = False
    for n, ch in enumerate(chunks):
        lead = bool(LEAD_RE.search(ch))
        clean = DIRECTIVE_RE.sub("", ch).strip()
        t = title_of(clean)
        if t.lower().startswith("appendix"):
            in_appendix = True
        cls = "slide lead" if lead else "slide"
        slides.append(
            f'<section class="{cls}" data-ap="{"1" if in_appendix else "0"}">'
            f"{render(clean)}</section>"
        )
        cards.append(
            f'<div class="card{" ap" if in_appendix else ""}" data-i="{n}">'
            f'<div class="n">{n + 1}</div><div class="t">{html.escape(t)}</div></div>'
        )

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{html.escape(title_of(chunks[0]))}</title>
<style>{CSS}</style>
</head>
<body>
<div id="bar"></div><div id="appx">Appendix</div>
<div id="tag">TejasCAD · Confidential</div><div id="num"></div>
{chr(10).join(slides)}
<div id="ov"><h2>All slides</h2><div class="grid">
{chr(10).join(cards)}
</div><div class="hint">Click a slide to jump &nbsp;·&nbsp; ← → or space to move &nbsp;·&nbsp;
O / Esc for this view &nbsp;·&nbsp; F fullscreen &nbsp;·&nbsp; P print to PDF</div></div>
<script>{JS}</script>
</body></html>"""

    out = src.with_name(src.stem + "-deck.html")
    out.write_text(doc, encoding="utf-8")
    return out


CHROME_HINTS = [
    "/opt/pw-browsers/chromium-*/chrome-linux/chrome",
    "/opt/pw-browsers/chromium/chrome-linux/chrome",
]


def find_chrome() -> str | None:
    import glob
    import shutil

    for pat in CHROME_HINTS:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        if (w := shutil.which(name)):
            return w
    return None


def to_pdf(deck: Path) -> Path | None:
    """Render the deck to PDF via headless Chromium, one slide per sheet."""
    import subprocess

    chrome = find_chrome()
    if not chrome:
        print("  ! no chromium found - open the deck and press P instead")
        return None
    out = deck.with_suffix(".pdf")
    subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--no-sandbox",
         "--no-pdf-header-footer", "--virtual-time-budget=5000",
         f"--print-to-pdf={out}", deck.resolve().as_uri()],
        check=True, capture_output=True,
    )
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: build-deck.py <marp-markdown-file> [--pdf]")
    s = Path(sys.argv[1])
    o = build(s)
    print(f"  {s.name} -> {o.name}  ({o.stat().st_size // 1024} KB, self-contained)")
    if "--pdf" in sys.argv:
        if (pdf := to_pdf(o)):
            print(f"  {o.name} -> {pdf.name}  ({pdf.stat().st_size // 1024} KB, A4 landscape)")
