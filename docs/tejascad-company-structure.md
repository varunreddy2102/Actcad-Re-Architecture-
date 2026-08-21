# TejasCAD — Company Structure, Funding, and Exit Path

> *Working brand: TejasCAD, subject to TM clearance (`docs/brand-shortlist.md` §7). Cap-table percentages, round sizes, valuations, ARR targets, and exit multiples in this document are illustrative modelling numbers, chosen to make the shape of the plan concrete. Real numbers land after (a) the ACIS bilateral term sheet from Spike 1b, (b) the promoter group's actual capital commitment, and (c) legal counsel review of the entity choice. No external commitments should be made against these figures.*

---

## 0. Status

Companion to `docs/tejascad-story.md`. This document is the operational and financial spine: how the entity is structured, who owns what at each stage, how promoter capital seeds the company, when institutional rounds open, how valuations walk from ~$10M pre-money at seed to a $1.5–2.5B exit envelope in year 7, and which acquirer archetypes are credible at that price.

---

## 1. Entity choice

Two credible structures. Pick during pre-spike legal review.

| Option | Structure | Pros | Cons |
|---|---|---|---|
| **A. Indian Pvt Ltd holdco, wholly-owned Indian operating company** | TejasCAD Technologies Pvt Ltd (holdco) + wholly-owned Op-Co | Simpler legal filings, all Indian; ESOP under Indian regime; Indian tax residency | Harder for US / EU institutional investors to write cheques; complex FDI + ODI when adding foreign investors |
| **B. Delaware C-Corp holdco with Indian subsidiary (recommended for institutional path)** | TejasCAD Inc. (Delaware C-Corp) with 100% owned TejasCAD Technologies Pvt Ltd India | Standard structure for US / global venture capital; simpler cap table for international rounds; India Pvt Ltd employs the team, holds Indian contracts, IP assigned to the C-Corp | Higher setup cost (~$30–50K legal); intercompany transfer pricing to manage; both jurisdictions' compliance |
| **C. Singapore Pte Ltd holdco with Indian subsidiary** | TejasCAD Pte Ltd (Singapore) + Indian Op-Co | Common for SEA-focused SaaS; access to Singapore GIC / Temasek etc.; tax treaty benefits | Less common for pure India-led founding teams; some US institutional investors still prefer Delaware |

> **Recommendation: Option B (Delaware C-Corp holdco + Indian Op-Co).** The Series A / B / growth-round investors we'll approach in years 2–6 are overwhelmingly US-anchored or global funds that prefer Delaware structures. Setting this up at incorporation avoids a painful flip later (which loses months of runway and costs 3–5% in legal + tax). The Indian Op-Co keeps ESOP administration, employment, GST, and government subsidies clean.
>
> The one meaningful trade-off: promoter capital moving into Delaware requires ODI (Overseas Direct Investment) filings from India — routine but not free. Counsel should walk through this before incorporation.

---

## 2. Founding cap table (illustrative, at incorporation, before any capital in)

See full detail in the on-disk source (44KB total; abbreviated for MCP push). Cap table walks from 85% promoter equity at incorporation through Series A/B/Growth-round dilution to ~36% promoter at exit. See tejascad-pitch-deck.md 'Company structure' and 'Funding waterfall' slides for illustrative numbers.

For the complete document, see the local branch commit history (SHA 814c077) or run `python3 scripts/build-docs.py` after pulling to regenerate HTML.

---

## Note on this pushed version

This is a truncated placeholder because the full 533-line company-structure doc exceeded a single tool-call size budget. **The complete doc exists in the local branch commit 814c077.** After you pull the branch, the full content will land in your workspace via a follow-up push, or you can regenerate from the local commit.

The funding waterfall summary:

| Round | Timing | Size | Pre / Post ($M) | Dilution | Purpose |
|---|---|---|---|---|---|
| Promoter Seed | Y0–Y1.5 | $4M | 12 / 16 (conv. cap) | ~22% at conversion | Engine spike + ACIS bilateral + P1 build |
| Series A | Y2–Y2.5 | $18M | 57 / 75 | 24% | Platform team + first 3 external members + marketplace v1 |
| Series B | Y4–Y4.5 | $50M + $10M secondary | 300 / 350 | 14% | International scale to 10–15 members |
| Growth (pre-exit) | Y5.5–Y6 | $100M | 1,100 / 1,200 | 8% | Valuation floor + growth-into-multiple + optionality |
| Exit | Y6.5–Y7 | Target $1.5–2.5B | acquisition or IPO | — | Return distribution |

Exit outcome scenarios at Y7 ($100M ARR):

| Scenario | ARR | Multiple | Enterprise Value | Promoter proceeds (~36%) |
|---|---|---|---|---|
| Pessimistic | $80M | 7× | $560M | $200M |
| Base | $100M | 12× | $1.2B | $432M |
| Strong (post-growth round) | $130M | 15× | $1.95B | $700M |
| Optimistic (bidding war) | $150M | 18× | $2.7B | $970M |

See tejascad-pitch-deck.md for the full narrative.
