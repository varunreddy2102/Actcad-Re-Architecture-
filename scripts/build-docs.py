#!/usr/bin/env python3
"""Build standalone HTML versions of the project markdown documents.

Usage:
    pip install markdown
    python3 scripts/build-docs.py

Reads .md files from docs/ and writes a companion .html file alongside each
one. Excludes exec-presentation.md, which has its own hand-authored reveal.js
slide deck (docs/exec-presentation.html). Also writes docs/index.html that
links to every document on the site.
"""

from __future__ import annotations

import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
EXCLUDE_MD = {"exec-presentation.md"}

# Short descriptions used on the index page. One line each.
DESCRIPTIONS = {
    "rearchitecture-plan.md": (
        "Master plan: goals, architectural decisions, module decomposition, "
        "phasing, risks, feasibility spike, industry adoption, collaboration, "
        "AI strategy, cost envelopes, next steps."
    ),
    "architecture-overview.md": (
        "Current-state architecture (the IntelliCAD-based ActCAD) and why it "
        "has to be replaced."
    ),
    "industry-outlook.md": (
        "Where the CAD industry segment is going — peer products, AI, cloud, "
        "BIM, mobile."
    ),
    "memory-architecture.md": (
        "Engineering reference for how the new engine manages memory: "
        "five-layer model, eight commitments, MVCC concurrency, the KAL "
        "contract, eviction protocol, failure modes, CI gates, anti-patterns."
    ),
    "platform-strategy.md": (
        "White-label platform strategy: turning the new engine into a "
        "multi-tenant product, ActCAD as anchor tenant, membership + "
        "royalty + marketplace rev-share, ACIS platform-amendment, "
        "partner pipeline and the chicken-and-egg gate at month 24."
    ),
    "brand-shortlist.md": (
        "Working shortlist for the white-label platform's master brand: "
        "Indian-rooted, modern-SaaS, Atmanirbhar / Modi-era resonance, "
        "name ends in 'CAD'. Tiered candidates, sub-brand families, "
        "TM watch-outs, names set aside."
    ),
    "tejascad-story.md": (
        "The TejasCAD narrative — the moment, the problem seen from three "
        "chairs, the insight, the bet, the promise, who founds it and why "
        "they can, the three-act arc across seven years to acquisition."
    ),
    "tejascad-company-structure.md": (
        "Corporate spine — entity choice (Delaware C-Corp + India Op-Co), "
        "founding cap table, five-round funding waterfall (Seed → Series "
        "A → B → pre-exit Growth round → exit), IP ownership, ActCAD "
        "carve-out, exit landscape and acquirer archetypes, verticalised "
        "solutions program, risk register, unit economics."
    ),
    "tejascad-licensing-architecture.md": (
        "Encrypted, platform-blind licensing — cryptographic key "
        "hierarchy, license artifact structure, issuance and activation "
        "flows, what TejasCAD does and doesn't see, third-party audit "
        "artifact, GDPR/DPDPA compliance mapping."
    ),
    "tejascad-vs-intellicad.md": (
        "Head-to-head with the IntelliCAD Consortium — feature-by-feature "
        "and architectural comparison, commercial comparison, three "
        "differentiators, honest counter-cases, illustrative migration "
        "case study ('RegionCAD')."
    ),
    "tejascad-pitch-deck.md": (
        "Pitch deck (Marp-formatted) for management, prospective members, "
        "and investors — synthesizes story + structure + licensing + "
        "differentiation + funding waterfall + exit landscape. Also "
        "renders as a browsable HTML document."
    ),
    "exec-presentation.html": (
        "Slide deck for the management decision briefing (reveal.js)."
    ),
}

# Display titles for the index. Falls back to the H1 of the doc.
TITLE_OVERRIDES = {
    "exec-presentation.html": "Executive presentation",
}

CSS = """
:root {
  --bg: #fafbfc;
  --panel: #ffffff;
  --border: #d8dce1;
  --text: #1a2332;
  --muted: #5b6675;
  --accent: #1a3a6c;
  --accent-2: #2d5fa7;
  --code-bg: #f3f5f7;
  --hover: #eef2f8;
  --pill: #eef4fb;
}
* { box-sizing: border-box; }
html { font-size: 16px; -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 1rem;
  line-height: 1.6;
  color: var(--text);
  background: var(--bg);
}
a { color: var(--accent-2); text-decoration: none; }
a:hover { text-decoration: underline; }

.layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
}

.toc-sidebar {
  border-right: 1px solid var(--border);
  background: var(--panel);
  padding: 24px 20px 40px;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}
.toc-header { border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 12px; }
.toc-header .back-link { color: var(--accent-2); font-size: 0.85rem; }
.toc-header h2 {
  font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--muted); margin: 12px 0 0; font-weight: 600;
}
.toc-nav { font-size: 0.85rem; }
.toc-nav ul { list-style: none; padding-left: 12px; margin: 4px 0; }
.toc-nav > ul { padding-left: 0; }
.toc-nav li { margin: 3px 0; }
.toc-nav a {
  color: var(--text);
  display: block;
  padding: 2px 6px;
  border-radius: 3px;
  line-height: 1.35;
}
.toc-nav a:hover { background: var(--hover); color: var(--accent); text-decoration: none; }
.toc-nav > ul > li > a { font-weight: 600; color: var(--accent); }

.content {
  padding: 40px 60px 80px;
  max-width: 920px;
  width: 100%;
}
.doc-kicker {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--muted);
  margin: 0 0 24px;
}

h1, h2, h3, h4, h5, h6 {
  color: var(--accent);
  line-height: 1.3;
  margin-top: 1.8em;
  margin-bottom: 0.6em;
  scroll-margin-top: 1em;
}
h1 { font-size: 2.1rem; margin-top: 0; padding-bottom: 12px; border-bottom: 2px solid var(--accent); }
h2 { font-size: 1.55rem; padding-bottom: 6px; border-bottom: 1px solid var(--border); color: var(--accent-2); }
h3 { font-size: 1.2rem; color: var(--accent-2); }
h4 { font-size: 1.05rem; }
h5 { font-size: 0.95rem; color: var(--accent); }
h6 { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }

p { margin: 0.6em 0 1em; }

strong { color: var(--accent); }

ul, ol { margin: 0.6em 0 1em; padding-left: 1.6em; }
li { margin: 0.3em 0; }
li > ul, li > ol { margin: 0.3em 0; }

blockquote {
  border-left: 4px solid var(--accent-2);
  margin: 1em 0;
  padding: 0.5em 1.2em;
  color: var(--text);
  background: var(--pill);
  border-radius: 0 6px 6px 0;
}
blockquote p:first-child { margin-top: 0; }
blockquote p:last-child { margin-bottom: 0; }

code {
  font-family: "SF Mono", Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.88em;
  background: var(--code-bg);
  padding: 0.15em 0.4em;
  border-radius: 3px;
}
pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 14px 16px;
  overflow-x: auto;
  font-size: 0.86em;
  line-height: 1.5;
}
pre code { background: none; padding: 0; font-size: 1em; }

table {
  border-collapse: collapse;
  margin: 1em 0;
  width: 100%;
  font-size: 0.9em;
  display: block;
  overflow-x: auto;
}
@media (min-width: 700px) {
  table { display: table; }
}
th, td {
  border: 1px solid var(--border);
  padding: 8px 12px;
  text-align: left;
  vertical-align: top;
}
th { background: var(--panel); color: var(--accent); font-weight: 600; }
tr:nth-child(even) td { background: var(--panel); }

hr { border: 0; border-top: 1px solid var(--border); margin: 2em 0; }

.headerlink {
  opacity: 0;
  margin-left: 0.4em;
  color: var(--muted);
  font-weight: normal;
  text-decoration: none;
  font-size: 0.85em;
}
h1:hover .headerlink, h2:hover .headerlink, h3:hover .headerlink,
h4:hover .headerlink, h5:hover .headerlink, h6:hover .headerlink { opacity: 1; }

.doc-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 20px;
  flex-wrap: wrap;
}
.doc-meta { font-size: 0.78rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }

.doc-footer {
  margin-top: 4em;
  padding-top: 1.2em;
  border-top: 1px solid var(--border);
  font-size: 0.85rem;
  color: var(--muted);
}
.doc-footer a { color: var(--accent-2); }

/* Index page */
.index-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 18px;
  margin-top: 2em;
}
.index-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px 22px;
  transition: border-color 0.15s, transform 0.15s;
}
.index-card:hover { border-color: var(--accent-2); transform: translateY(-2px); }
.index-card h3 { margin: 0 0 8px; font-size: 1.15rem; border: 0; padding: 0; }
.index-card h3 a { color: var(--accent); }
.index-card p { margin: 0; color: var(--muted); font-size: 0.92rem; line-height: 1.45; }
.index-card .file-name {
  display: inline-block;
  font-family: "SF Mono", Monaco, Consolas, monospace;
  font-size: 0.75rem;
  color: var(--muted);
  background: var(--code-bg);
  padding: 2px 6px;
  border-radius: 3px;
  margin-top: 10px;
}

@media (max-width: 1024px) {
  .layout { grid-template-columns: 1fr; }
  .toc-sidebar { position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--border); }
  .content { padding: 30px 24px 60px; }
}

@media print {
  .toc-sidebar, .doc-footer { display: none; }
  .layout { grid-template-columns: 1fr; max-width: none; }
  .content { max-width: none; padding: 0; }
  body { background: white; font-size: 10.5pt; }
  pre, table { page-break-inside: avoid; }
  h1, h2, h3 { page-break-after: avoid; }
  a { color: inherit; text-decoration: none; }
}
"""

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — ActCAD Re-Architecture</title>
<style>{css}</style>
</head>
<body>
<div class="layout">
  <aside class="toc-sidebar">
    <div class="toc-header">
      <a href="index.html" class="back-link">← All documents</a>
      <h2>On this page</h2>
    </div>
    <nav class="toc-nav">{toc}</nav>
  </aside>
  <main class="content">
    <div class="doc-header">
      <p class="doc-kicker">ActCAD Re-Architecture · Jytra Technology Solutions · Confidential</p>
      <p class="doc-meta">{filename}</p>
    </div>
    {body}
    <footer class="doc-footer">
      <p>Companion documents:
        <a href="index.html">index</a> ·
        <a href="tejascad-story.html">TejasCAD story</a> ·
        <a href="tejascad-pitch-deck.html">TejasCAD deck</a> ·
        <a href="tejascad-vs-intellicad.html">vs IntelliCAD</a> ·
        <a href="tejascad-company-structure.html">company structure</a> ·
        <a href="tejascad-licensing-architecture.html">licensing</a> ·
        <a href="platform-strategy.html">platform strategy</a> ·
        <a href="rearchitecture-plan.html">engine plan</a> ·
        <a href="architecture-overview.html">overview</a> ·
        <a href="industry-outlook.html">industry</a> ·
        <a href="memory-architecture.html">memory</a> ·
        <a href="brand-shortlist.html">brand</a> ·
        <a href="exec-presentation.html">original exec deck</a>
      </p>
    </footer>
  </main>
</div>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ActCAD Re-Architecture — Documentation</title>
<style>{css}</style>
</head>
<body>
<div class="layout">
  <aside class="toc-sidebar">
    <div class="toc-header">
      <h2>ActCAD Re-Architecture</h2>
    </div>
    <nav class="toc-nav">
      <ul>
        <li><a href="index.html"><strong>Index</strong></a></li>
        <li><a href="tejascad-story.html"><strong>TejasCAD story</strong></a></li>
        <li><a href="tejascad-pitch-deck.html">TejasCAD pitch deck</a></li>
        <li><a href="tejascad-vs-intellicad.html">TejasCAD vs IntelliCAD</a></li>
        <li><a href="tejascad-company-structure.html">Company structure & funding</a></li>
        <li><a href="tejascad-licensing-architecture.html">Licensing architecture</a></li>
        <li><a href="platform-strategy.html">Platform strategy</a></li>
        <li><a href="rearchitecture-plan.html">Engine master plan</a></li>
        <li><a href="architecture-overview.html">Current architecture</a></li>
        <li><a href="industry-outlook.html">Industry outlook</a></li>
        <li><a href="memory-architecture.html">Memory architecture</a></li>
        <li><a href="brand-shortlist.html">Brand shortlist</a></li>
        <li><a href="exec-presentation.html">Original exec deck</a></li>
      </ul>
    </nav>
  </aside>
  <main class="content">
    <p class="doc-kicker">ActCAD Re-Architecture · Jytra Technology Solutions · Confidential</p>
    <h1>Documentation</h1>
    <p>Strategic and engineering documentation for the 3-year re-architecture of ActCAD off the IntelliCAD engine onto a first-party engine built on ODA SDKs and the ACIS 3D kernel.</p>
    <p>The companion executive slide deck is hand-authored in reveal.js; all other documents are generated from the markdown sources in <code>docs/</code> via <code>scripts/build-docs.py</code>.</p>
    <div class="index-grid">
{cards}
    </div>
    <footer class="doc-footer">
      <p>Regenerate the HTML pages: <code>pip install markdown &amp;&amp; python3 scripts/build-docs.py</code></p>
    </footer>
  </main>
</div>
</body>
</html>
"""


FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
MARP_COMMENT_RE = re.compile(r"<!--\s*_class:.*?-->\s*|<!--\s*_paginate:.*?-->\s*", re.IGNORECASE)


def convert(md_path: Path) -> tuple[str, str, str]:
    """Return (title, toc_html, body_html) for a markdown source file."""
    text = md_path.read_text(encoding="utf-8")
    # Strip Marp YAML frontmatter and Marp-only directive comments so the
    # HTML preview reads as a document. The Marp source is unaffected on disk.
    text = FRONTMATTER_RE.sub("", text)
    text = MARP_COMMENT_RE.sub("", text)
    md = markdown.Markdown(
        extensions=["extra", "toc", "sane_lists", "smarty"],
        extension_configs={
            "toc": {
                "toc_depth": "2-3",
                "anchorlink": True,
                "permalink": False,
            },
        },
    )
    body = md.convert(text)

    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.DOTALL)
    if title_match:
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
    else:
        title = md_path.stem.replace("-", " ").title()

    return title, md.toc, body


def build_pages(md_files: list[Path]) -> list[tuple[Path, str]]:
    """Convert each markdown file to HTML. Return [(out_path, title), ...]."""
    written: list[tuple[Path, str]] = []
    for md_path in md_files:
        title, toc, body = convert(md_path)
        page = PAGE_TEMPLATE.format(
            title=title,
            css=CSS,
            toc=toc,
            body=body,
            filename=md_path.name,
        )
        out = DOCS / (md_path.stem + ".html")
        out.write_text(page, encoding="utf-8")
        written.append((out, title))
        print(f"  {md_path.name:35s} -> {out.name}")
    return written


def build_index(pages: list[tuple[Path, str]]) -> None:
    """Write docs/index.html linking to every document."""
    # Order: TejasCAD story first (the narrative front door), then TejasCAD
    # pack (structure, licensing, vs-intellicad, deck), then engine plan &
    # supporting docs, then brand shortlist, then original exec deck.
    order = [
        "tejascad-story.html",
        "tejascad-pitch-deck.html",
        "tejascad-vs-intellicad.html",
        "tejascad-company-structure.html",
        "tejascad-licensing-architecture.html",
        "platform-strategy.html",
        "rearchitecture-plan.html",
        "architecture-overview.html",
        "industry-outlook.html",
        "memory-architecture.html",
        "brand-shortlist.html",
        "exec-presentation.html",
    ]
    title_by_name = {p.name: t for p, t in pages}
    title_by_name.update({k: v for k, v in TITLE_OVERRIDES.items()})

    cards = []
    for name in order:
        title = title_by_name.get(name, name)
        # Look up description by markdown source name if applicable.
        md_name = name.replace(".html", ".md")
        desc = DESCRIPTIONS.get(md_name) or DESCRIPTIONS.get(name) or ""
        cards.append(
            "      <div class=\"index-card\">"
            f"<h3><a href=\"{name}\">{title}</a></h3>"
            f"<p>{desc}</p>"
            f"<span class=\"file-name\">{name}</span>"
            "</div>"
        )

    index_html = INDEX_TEMPLATE.format(css=CSS, cards="\n".join(cards))
    (DOCS / "index.html").write_text(index_html, encoding="utf-8")
    print(f"  index.html written ({len(cards)} cards)")


def main() -> None:
    md_files = sorted(p for p in DOCS.glob("*.md") if p.name not in EXCLUDE_MD)
    print(f"Converting {len(md_files)} markdown files in {DOCS}:")
    pages = build_pages(md_files)
    build_index(pages)
    print("Done.")


if __name__ == "__main__":
    main()
