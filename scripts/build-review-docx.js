#!/usr/bin/env node
/**
 * Build a comment-friendly Word review copy of the directors deck.
 *
 *   node scripts/build-review-docx.js docs/tejascad-mgmt-brief.md
 *
 * Each slide becomes one numbered Heading1 section, so Word's navigation pane
 * lists the slides and a reviewer can anchor a comment to a specific one. Slide
 * numbers match the deck exactly, so "comment on slide 12" is unambiguous
 * across the .docx, the .html deck and the .pdf handout.
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, PageBreak,
} = require("docx");

const NAVY = "1E3A5C";
const DEEP = "102542";
const ACCENT = "9A6B2F";
const GREY = "5A5A5A";
const CREAM = "FAF7F2";
const RULE = "D8D0C4";

const PAGE_W = 9026; // usable DXA width inside 1" margins on A4 portrait

/* ---------- inline markdown -> TextRuns ---------- */
function runs(md, base = {}) {
  const out = [];
  // **bold**, *italic*, `code`
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0, m;
  const push = (t, o) => { if (t) out.push(new TextRun({ text: t, ...base, ...o })); };
  while ((m = re.exec(md))) {
    push(md.slice(last, m.index), {});
    const tok = m[0];
    if (tok.startsWith("**")) push(tok.slice(2, -2), { bold: true, color: base.color || NAVY });
    else if (tok.startsWith("`")) push(tok.slice(1, -1), { font: "Consolas", size: 18 });
    else push(tok.slice(1, -1), { italics: true });
    last = m.index + tok.length;
  }
  push(md.slice(last), {});
  return out.length ? out : [new TextRun({ text: "", ...base })];
}

const stripMd = (s) => s.replace(/\*\*/g, "").replace(/`/g, "").replace(/^\*|\*$/g, "").trim();

/* ---------- table ---------- */
function mdTable(lines) {
  const rows = lines
    .map((l) => l.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim()))
    .filter((cells) => !cells.every((c) => /^:?-{2,}:?$/.test(c) || c === ""));
  if (!rows.length) return null;
  const cols = Math.max(...rows.map((r) => r.length));
  const w = Math.floor(PAGE_W / cols);
  const widths = Array(cols).fill(w);

  return new Table({
    columnWidths: widths,
    width: { size: PAGE_W, type: WidthType.DXA },
    rows: rows.map((cells, ri) =>
      new TableRow({
        tableHeader: ri === 0,
        children: Array.from({ length: cols }, (_, ci) =>
          new TableCell({
            width: { size: widths[ci], type: WidthType.DXA },
            shading: {
              type: ShadingType.CLEAR,
              fill: ri === 0 ? NAVY : ri % 2 === 0 ? CREAM : "FFFFFF",
            },
            margins: { top: 60, bottom: 60, left: 90, right: 90 },
            children: [
              new Paragraph({
                spacing: { before: 0, after: 0 },
                children: runs(cells[ci] ?? "", {
                  size: 17,
                  bold: ri === 0,
                  color: ri === 0 ? "FFFFFF" : "1A1A1A",
                }),
              }),
            ],
          })
        ),
      })
    ),
  });
}

/* ---------- one slide body -> paragraphs ---------- */
function body(md) {
  const out = [];
  const lines = md.split("\n");
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) { i++; continue; }

    // table block
    if (line.trim().startsWith("|")) {
      const buf = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) buf.push(lines[i++]);
      const t = mdTable(buf);
      if (t) { out.push(t); out.push(new Paragraph({ spacing: { after: 140 }, children: [] })); }
      continue;
    }

    // callout / quote
    if (line.trim().startsWith(">")) {
      const buf = [];
      while (i < lines.length && (lines[i].trim().startsWith(">") || (buf.length && lines[i].trim() && !lines[i].trim().startsWith("|") && !/^[-*]\s|^\d+\.\s|^#{1,6}\s/.test(lines[i].trim())))) {
        buf.push(lines[i].trim().replace(/^>\s?/, ""));
        i++;
        if (i < lines.length && !lines[i].trim()) break;
      }
      out.push(new Paragraph({
        spacing: { before: 100, after: 140 },
        indent: { left: 260 },
        border: { left: { style: BorderStyle.SINGLE, size: 18, color: ACCENT, space: 10 } },
        shading: { type: ShadingType.CLEAR, fill: CREAM },
        children: runs(buf.join(" "), { size: 19 }),
      }));
      continue;
    }

    // headings inside a slide
    const h = line.match(/^(#{2,6})\s+(.*)$/);
    if (h) {
      out.push(new Paragraph({
        spacing: { before: 200, after: 80 },
        children: [new TextRun({ text: stripMd(h[2]), bold: true, size: 22, color: DEEP })],
      }));
      i++; continue;
    }

    // bullets / numbered
    const b = line.match(/^\s*[-*]\s+(.*)$/);
    const n = line.match(/^\s*(\d+)\.\s+(.*)$/);
    if (b || n) {
      out.push(new Paragraph({
        spacing: { before: 40, after: 40 },
        indent: { left: 360, hanging: 200 },
        children: [
          new TextRun({ text: b ? "•   " : `${n[1]}.  `, bold: true, color: ACCENT, size: 19 }),
          ...runs(b ? b[1] : n[2], { size: 19 }),
        ],
      }));
      i++; continue;
    }

    // raw html wrapper -> emphasised paragraph
    if (/^<\/?div/i.test(line.trim())) { i++; continue; }
    if (/^<!--/.test(line.trim())) { i++; continue; }

    out.push(new Paragraph({
      spacing: { before: 60, after: 100 },
      children: runs(line.trim(), { size: 19 }),
    }));
    i++;
  }
  return out;
}

/* ---------- main ---------- */
const src = process.argv[2] || "docs/tejascad-mgmt-brief.md";
let raw = fs.readFileSync(src, "utf8");
// Same guard as build-deck.py: if frontmatter's closing "---" is missing the
// match runs on and silently swallows slide 1. Real frontmatter is key/value
// lines only, so a heading or HTML comment inside the capture means over-match.
const fm = raw.match(/^---\n[\s\S]*?\n---\n/);
if (fm && /^#{1,3}\s|<!--/m.test(fm[0])) {
  console.error(`${src}: YAML frontmatter has no closing '---' — slide 1 would be swallowed.`);
  process.exit(1);
}
raw = raw.replace(/^---\n[\s\S]*?\n---\n/, "");
const slides = raw.split(/\n---\n/).map((s) => s.trim()).filter(Boolean);

const children = [];

// cover
children.push(
  new Paragraph({
    spacing: { before: 1400, after: 120 },
    children: [new TextRun({ text: "TejasCAD — Directors Briefing", bold: true, size: 48, color: NAVY })],
  }),
  new Paragraph({
    spacing: { after: 500 },
    children: [new TextRun({ text: "Review copy for comment", size: 26, color: ACCENT })],
  }),
  new Paragraph({
    spacing: { after: 160 },
    border: { top: { style: BorderStyle.SINGLE, size: 8, color: RULE, space: 12 } },
    children: [],
  }),
  new Paragraph({
    spacing: { after: 120 },
    children: [new TextRun({
      text: "This is the slide deck in document form so it can be marked up. Each slide is a numbered heading — the numbers match the presentation deck and the printed handout exactly, so a comment on \"Slide 12\" is unambiguous across all three.",
      size: 20, color: GREY,
    })],
  }),
  new Paragraph({
    spacing: { after: 120 },
    children: [
      new TextRun({ text: "To comment: ", bold: true, size: 20, color: NAVY }),
      new TextRun({ text: "select the text, then Review → New Comment (Ctrl+Alt+M). Turn on Track Changes if you want to edit wording directly.", size: 20, color: GREY }),
    ],
  }),
  new Paragraph({
    spacing: { after: 120 },
    children: [
      new TextRun({ text: "Please look hardest at: ", bold: true, size: 20, color: NAVY }),
      new TextRun({
        text: "the commitments made on the operator and division-of-labour slides (roadmap authority, separate support headcount, the competitive veto, founder-level equity), and every figure in the pricing and scenario tables. Competitor pricing is actual; our own projections are illustrative and should be challenged.",
        size: 20, color: GREY,
      }),
    ],
  }),
  new Paragraph({ children: [new PageBreak()] }),
);

let appendix = false;
slides.forEach((s, idx) => {
  const clean = s.replace(/<!--[\s\S]*?-->/g, "").trim();
  const m = clean.match(/^(#{1,3})\s+(.*)$/m);
  const title = m ? stripMd(m[2]) : "—";
  if (/^appendix/i.test(title)) appendix = true;
  const rest = m ? clean.replace(m[0], "").trim() : clean;

  children.push(new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: idx === 0 ? 0 : 320, after: 40 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 10, color: NAVY, space: 6 } },
    children: [
      new TextRun({ text: `Slide ${idx + 1}${appendix ? " (appendix)" : ""} — `, bold: true, size: 24, color: ACCENT }),
      new TextRun({ text: title, bold: true, size: 26, color: NAVY }),
    ],
  }));
  children.push(...body(rest));
});

const doc = new Document({
  creator: "TejasCAD",
  title: "TejasCAD Directors Briefing — review copy",
  description: "Slide deck in document form for comment and markup",
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 19, color: "1A1A1A" }, paragraph: { spacing: { line: 264 } } },
    },
  },
  sections: [{
    properties: { page: { margin: { top: 1000, bottom: 1000, left: 1080, right: 1080 } } },
    children,
  }],
});

const out = path.join(path.dirname(src), path.basename(src, ".md") + "-review.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  console.log(`  ${path.basename(src)} -> ${path.basename(out)}  (${Math.round(buf.length / 1024)} KB, ${slides.length} slide sections)`);
});
