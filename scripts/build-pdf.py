#!/usr/bin/env python3
"""Build a single combined PDF from all project markdown documents.

Usage:
    pip install markdown weasyprint
    python3 scripts/build-pdf.py

Reads docs/ markdown files in canonical order, renders them into one HTML
document with a title page and auto-generated TOC, then converts to PDF via
weasyprint. Outputs docs/actcad-re-architecture.pdf.
"""

from __future__ import annotations

import re
from pathlib import Path

import markdown
from weasyprint import HTML, CSS

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT_PDF = DOCS / "actcad-re-architecture.pdf"

# Canonical document order (exec-presentation excluded — it's a slide deck)
DOC_ORDER = [
    "rearchitecture-plan.md",
    "architecture-overview.md",
    "industry-outlook.md",
    "memory-architecture.md",
]

DOC_SUBTITLES = {
    "rearchitecture-plan.md":    "Master Re-Architecture Plan",
    "architecture-overview.md":  "Architecture Overview & Implications",
    "industry-outlook.md":       "Industry Outlook",
    "memory-architecture.md":    "Memory Architecture — Engineering Reference",
}

CSS_SOURCE = """
/* ── Page setup ─────────────────────────────────────────────────────────── */
@page {
  size: A4;
  margin: 22mm 20mm 25mm 22mm;
  @bottom-center {
    content: counter(page);
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    font-size: 9pt;
    color: #888;
  }
  @top-right {
    content: string(doc-title);
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    font-size: 8pt;
    color: #aaa;
  }
}
@page :first { @bottom-center { content: none; } @top-right { content: none; } }
@page cover { margin: 0; @bottom-center { content: none; } @top-right { content: none; } }

/* ── Reset ───────────────────────────────────────────────────────────────── */
* { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --accent:   #1a3a6c;
  --accent-2: #2d5fa7;
  --muted:    #5b6675;
  --border:   #d0d5de;
  --code-bg:  #f3f5f7;
  --text:     #1a2332;
}

/* ── Cover page ──────────────────────────────────────────────────────────── */
.cover-page {
  page: cover;
  page-break-after: always;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  min-height: 100vh;
  padding: 60mm 22mm 30mm;
  background: var(--accent);
  color: white;
}
.cover-kicker {
  font-size: 9pt;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  opacity: 0.65;
  margin-bottom: 14mm;
}
.cover-title {
  font-size: 28pt;
  font-weight: 700;
  line-height: 1.15;
  margin-bottom: 6mm;
}
.cover-subtitle {
  font-size: 12pt;
  opacity: 0.8;
  margin-bottom: 20mm;
}
.cover-meta {
  font-size: 9pt;
  opacity: 0.6;
  line-height: 1.7;
}

/* ── TOC page ────────────────────────────────────────────────────────────── */
.toc-page {
  page-break-after: always;
  padding: 12mm 0 0;
}
.toc-title {
  font-size: 18pt;
  font-weight: 700;
  color: var(--accent);
  border-bottom: 2px solid var(--accent);
  padding-bottom: 4mm;
  margin-bottom: 6mm;
}
.toc-section { margin-bottom: 6mm; }
.toc-doc-name {
  font-size: 10pt;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 2mm;
  border-bottom: 1px solid var(--border);
  padding-bottom: 1.5mm;
}
.toc-entry {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 9.5pt;
  color: var(--text);
  line-height: 1.55;
  padding: 0.5mm 0 0.5mm 4mm;
}
.toc-entry.h1 { font-weight: 600; color: var(--accent-2); padding-left: 0; font-size: 10pt; }
.toc-entry.h2 { padding-left: 4mm; }
.toc-entry.h3 { padding-left: 10mm; color: var(--muted); font-size: 9pt; }
.toc-dots {
  flex: 1;
  border-bottom: 1px dotted var(--border);
  margin: 0 3mm;
  min-width: 8mm;
}
.toc-page-num { color: var(--muted); font-size: 9pt; }

/* ── Document chapters ───────────────────────────────────────────────────── */
body {
  font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
  font-size: 10pt;
  line-height: 1.6;
  color: var(--text);
}

.doc-chapter { page-break-before: always; }
.doc-chapter:first-of-type { page-break-before: auto; }

.chapter-banner {
  background: var(--accent);
  color: white;
  padding: 5mm 7mm;
  margin: -5mm -3mm 6mm;
  border-radius: 2mm;
  string-set: doc-title content();
}
.chapter-banner-kicker { font-size: 7.5pt; opacity: 0.65; text-transform: uppercase; letter-spacing: 0.1em; }
.chapter-banner-title  { font-size: 14pt; font-weight: 700; margin-top: 1mm; }

/* ── Headings ────────────────────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
  color: var(--accent);
  line-height: 1.3;
  margin-top: 5mm;
  margin-bottom: 2mm;
  page-break-after: avoid;
}
h1 { font-size: 16pt; border-bottom: 2px solid var(--accent); padding-bottom: 2mm; margin-top: 0; }
h2 { font-size: 12pt; border-bottom: 1px solid var(--border); padding-bottom: 1mm; color: var(--accent-2); }
h3 { font-size: 10.5pt; color: var(--accent-2); }
h4 { font-size: 10pt; }
h5 { font-size: 9.5pt; }
h6 { font-size: 9pt; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }

/* ── Body text ───────────────────────────────────────────────────────────── */
p { margin: 0 0 2.5mm; }
strong { color: var(--accent); }
a { color: var(--accent-2); text-decoration: none; }

ul, ol { margin: 0 0 2.5mm; padding-left: 5mm; }
li { margin: 0.8mm 0; }
li > ul, li > ol { margin: 0.5mm 0; }

blockquote {
  border-left: 3px solid var(--accent-2);
  margin: 2mm 0;
  padding: 2mm 4mm;
  background: #eef4fb;
  border-radius: 0 1.5mm 1.5mm 0;
  font-size: 9.5pt;
}
blockquote p:last-child { margin-bottom: 0; }

code {
  font-family: "SF Mono", Consolas, "Liberation Mono", monospace;
  font-size: 8.5pt;
  background: var(--code-bg);
  padding: 0.5mm 1.5mm;
  border-radius: 1mm;
}
pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 2mm;
  padding: 3mm 4mm;
  overflow-x: auto;
  font-size: 8pt;
  line-height: 1.45;
  margin: 2mm 0 3mm;
  page-break-inside: avoid;
}
pre code { background: none; padding: 0; font-size: inherit; }

table {
  border-collapse: collapse;
  width: 100%;
  font-size: 8.5pt;
  margin: 2mm 0 4mm;
  page-break-inside: avoid;
}
th, td {
  border: 1px solid var(--border);
  padding: 2mm 3mm;
  text-align: left;
  vertical-align: top;
}
th { background: #f0f4fa; color: var(--accent); font-weight: 600; }
tr:nth-child(even) td { background: #fafbfc; }

hr { border: 0; border-top: 1px solid var(--border); margin: 4mm 0; }

/* ── Orphan / widow control ──────────────────────────────────────────────── */
p, li { orphans: 3; widows: 3; }
"""


def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text)


def extract_headings(html: str, levels=(1, 2, 3)) -> list[dict]:
    """Return list of {level, text, slug} dicts from rendered HTML."""
    headings = []
    for m in re.finditer(r"<h([1-6])(?:[^>]*)>(.*?)</h\1>", html, re.DOTALL):
        level = int(m.group(1))
        if level not in levels:
            continue
        raw = m.group(2)
        text = re.sub(r"<[^>]+>", "", raw).strip()
        # Try to grab the id attribute for the anchor
        id_m = re.search(r'id=["\']([^"\']+)["\']', m.group(0))
        slug = id_m.group(1) if id_m else slugify(text)
        headings.append({"level": level, "text": text, "slug": slug})
    return headings


def convert_md(md_path: Path) -> tuple[str, list[dict]]:
    """Return (body_html, headings) for a markdown file."""
    text = md_path.read_text(encoding="utf-8")
    md = markdown.Markdown(
        extensions=["extra", "toc", "sane_lists", "smarty"],
        extension_configs={
            "toc": {
                "toc_depth": "1-3",
                "anchorlink": False,
                "permalink": False,
            },
        },
    )
    body = md.convert(text)
    headings = extract_headings(body, levels={1, 2, 3})
    return body, headings


def build_toc_html(doc_headings: list[tuple[str, str, list[dict]]]) -> str:
    """Build the TOC section HTML. doc_headings = [(filename, subtitle, headings)]."""
    parts = ['<div class="toc-page">', '<h1 class="toc-title">Contents</h1>']
    for _fname, subtitle, headings in doc_headings:
        parts.append(f'<div class="toc-section">')
        parts.append(f'<div class="toc-doc-name">{subtitle}</div>')
        for h in headings:
            cls = f"h{h['level']}"
            text = h["text"]
            # Use target anchor for weasyprint internal links
            parts.append(
                f'<div class="toc-entry {cls}">'
                f'<span>{text}</span>'
                f'<span class="toc-dots"></span>'
                f'<span class="toc-page-num"> </span>'
                f"</div>"
            )
        parts.append("</div>")
    parts.append("</div>")
    return "\n".join(parts)


def build_combined_html(doc_data: list[tuple[str, str, str, list[dict]]]) -> str:
    """Assemble full HTML. doc_data = [(filename, subtitle, body_html, headings)]."""
    toc_input = [(f, s, h) for f, s, _b, h in doc_data]
    toc_html = build_toc_html(toc_input)

    chapters = []
    for i, (fname, subtitle, body_html, _headings) in enumerate(doc_data):
        banner = (
            '<div class="chapter-banner">'
            '<div class="chapter-banner-kicker">ActCAD Re-Architecture · Jytra Technology Solutions · Confidential</div>'
            f'<div class="chapter-banner-title">{subtitle}</div>'
            "</div>"
        )
        cls = "doc-chapter"
        chapters.append(f'<div class="{cls}">{banner}{body_html}</div>')

    cover = """
<div class="cover-page">
  <div class="cover-kicker">Jytra Technology Solutions · Confidential · 2025–2028</div>
  <div class="cover-title">ActCAD<br>Re-Architecture</div>
  <div class="cover-subtitle">Strategic &amp; Engineering Documentation</div>
  <div class="cover-meta">
    3-year programme to replace the IntelliCAD engine<br>
    with a first-party engine on ODA SDKs and the ACIS 3D kernel.<br><br>
    Jytra Technology Solutions Pvt. Ltd.<br>
    East Godavari, India
  </div>
</div>
"""

    chapters_html = "\n\n".join(chapters)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ActCAD Re-Architecture — Full Documentation</title>
</head>
<body>
{cover}
{toc_html}
{chapters_html}
</body>
</html>
"""


def main() -> None:
    print("Loading markdown files...")
    doc_data = []
    for fname in DOC_ORDER:
        md_path = DOCS / fname
        if not md_path.exists():
            print(f"  SKIP (not found): {fname}")
            continue
        subtitle = DOC_SUBTITLES.get(fname, fname)
        print(f"  converting {fname} ...")
        body_html, headings = convert_md(md_path)
        doc_data.append((fname, subtitle, body_html, headings))

    print("Assembling combined HTML...")
    combined_html = build_combined_html(doc_data)

    print("Rendering PDF (this may take 15-30 seconds)...")
    html_obj = HTML(string=combined_html, base_url=str(DOCS))
    css_obj = CSS(string=CSS_SOURCE)
    html_obj.write_pdf(OUT_PDF, stylesheets=[css_obj])

    size_kb = OUT_PDF.stat().st_size // 1024
    print(f"Done → {OUT_PDF}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
