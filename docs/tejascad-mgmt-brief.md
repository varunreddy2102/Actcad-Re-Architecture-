---
marp: true
theme: default
paginate: true
size: 16:9
header: 'TejasCAD · Directors briefing'
footer: 'Confidential · Working brand pending TM clearance'
style: |
  section { font-size: 27px; padding: 62px 78px; }
  h1 { color: #1a3a6c; }
  h2 { color: #2d5fa7; border-bottom: 2px solid #2d5fa7; padding-bottom: 6px; }
  table { font-size: 0.82em; }
  blockquote { border-left: 4px solid #c08847; background: #faf7f2; padding: 12px 18px; }
  strong { color: #1a3a6c; }
  .big { font-size: 1.28em; line-height: 1.35; color: #1a3a6c; }
---

<!-- _class: lead -->
<!-- _paginate: false -->

# TejasCAD

### Licensing our new CAD engine to other vendors

**Directors' briefing**

*Working brand, pending trademark clearance. ITC figures are actual; our projections are illustrative.*

---

## Purpose of this briefing

- We are replacing ActCAD's IntelliCAD foundation with **an engine we own**
- The same engine could be **licensed to other CAD vendors** under their brands
- This briefing sets out **that opportunity, its economics, and its risks**

<div class="big" markdown="1">

**We are seeking in-principle approval to explore it — and to open three discussions.**

</div>

- **Corporate structure** · **Capital requirement** · **Team required**

---

## Where the engineering stands

**Phase 0 — six weeks, ~207 commits, 13+ releases to the ActCAD team**

- **Customer DWG files open in the browser** — both WASM and ODA inWEB backends live
- **Full 14-mode osnap suite**, measurement, count, CSV and Excel export
- **250,000 entities at 61 fps** · regeneration 17× faster · instant zoom-extents
- **3D orbit, ViewCube, layouts and paper-space viewports**
- **DWG and PDF comparison**, colour plotting, batch print, markups
- **Windows MSI shipping** · macOS CI green · Android prototype
- **594 of 594 tests passing** · read-only guarantee intact

> **Benchmarking shows it ahead of ActCAD on many customer files, and ahead of both IntelliCAD's viewer and ODA's own.**

**Outstanding:** customer-hardware performance baseline · public launch

---

## Architecture for the editor

**Certain ODA capabilities are not exposed through the web stack.**

- **To viewer launch** — continue on the current Rust/Tauri and WASM stack
- **After launch** — **migrate the full editor to Qt and C++ native**
  - provides access to the ODA surface unavailable on web
  - aligns with where the ActCAD team intends to work long term
- **The web viewer** — either folds into the Qt stack or remains separate
  - **to be determined with data during migration**

> **The platform capabilities — tenant configuration, licensing, marketplace, AI — reside in the C++ core in either case.**

---

## The opportunity

- **~40 IntelliCAD Consortium members** — regional CAD vendors on the same foundation we are leaving
- **~200 vertical ISVs** — MEP, structural, electrical, survey, solar
- **BIM-lite startups** — need a CAD foundation they cannot afford to build

**What they have in common**

- Paying for a foundation that **cannot deliver AI, cloud, web or mobile**
- Carrying **a million lines of source they must maintain themselves**
- **No practical alternative** short of a multi-year engine rebuild

---

## What we pay IntelliCAD today

| | |
|---|---|
| Membership and extras | **~$100,000 per year** |
| Per-seat royalty to ITC | **None** |
| Component royalties (ACIS and others) | **$15–20 per sale** |
| AI module | **~$7–8,000 per year** — experimental |
| Android viewer | **~$8,000 per year** |
| Mac, web application, web editor | **Not available** |

> **The fee purchases source code, not a product** — a codebase to staff, modify and re-merge at every version uptake.

---

## How our offer would compare

| | **IntelliCAD provides** | **TejasCAD would provide** |
|---|---|---|
| Deliverable | ~1M lines of source | **A product they configure** |
| Engine maintenance | The member's responsibility | **Ours** |
| Engine defects | Member fixes; **work reaches rivals** | **We fix; member receives** |
| Member's own plugins | Entangled with engine changes | **Remain theirs** |
| Release cadence | Annual, coordinated | **Rolling** |
| Platform reach | Windows | **Windows, Mac, Linux, web, Android** |
| AI | Paid add-on | **Included** |
| Licensing infrastructure | Member sources their own | **Included, and platform-blind** |

---

## Proposed commercial model

**Three tiers**

- **Core** — engine, DWG fidelity, white-label shell, licensing, AI
- **Plus** — adds web application, Mac, Android, marketplace
- **Complete** — adds our vertical modules (Arch, Mech, Elec, BIM, GIS)

| Member's installed base | Core | Plus | Complete |
|---|---|---|---|
| Under 5,000 seats | $45K | $65K | $90K |
| 5,000–20,000 | $80K | $110K | $150K |
| 20,000–50,000 | $130K | **$170K** | $220K |
| 50,000+ | $190K | $240K | $300K |

- **Phased at 50 / 75 / 100%** across the member's migration years
- **Component royalties passed through at cost** · **AI metered above an allowance**

---

## Financial outlook

| | Conservative | Base | Aggressive |
|---|---|---|---|
| Members by year 7 | 5 | 12 | 20 |
| Average fee | ~$70K | ~$110K | ~$170K |
| **Recurring revenue** | **~$425K** | **~$1.7M** | **~$4.3M** |
| **Contribution** | **~$290K** | **~$1.2M** | **~$3.1M** |
| Indicative value at 6–8× | — | ~$10–13M | **~$26–34M** |

<div class="big" markdown="1">

**A profitable adjacent business line. Not a venture-scale outcome.**

</div>

- Revenue accrues **in addition to ActCAD**, from engineering already funded
- Materially larger scale would require **60–100 members**, direct distribution, or the 3D product

---

## Investment required

| Stage | Timing | Amount |
|---|---|---|
| **Promoter seed** | Now to year 2 | **$1–2M** |
| **Strategic round** *(optional)* | Years 4–5 | **$5–10M** |
| **Exit** | Years 6–7 | **$30–50M** target |

- The seed is **the increment on an engine already funded** — not its full cost
- A strategic investor at years 4–5 would **establish a valuation floor** ahead of any sale
- At ~70% margins the business **self-funds from year 3**

---

## Two options

| | **ActCAD only** | **Platform** |
|---|---|---|
| Engineering | Same | Same |
| Timeline | ~24 months to GA | Unchanged |
| Additional cost | — | **3–6 engineer-months** |
| Revenue | ActCAD alone | **Plus member fees and royalties** |
| Asset at exit | One product | **Two separable assets** |
| Complexity | Lower | Second entity, partner obligations |

<div class="big" markdown="1">

**Recommendation: build the platform capability now, and decide on commercialisation at month 24.**

</div>

- The multi-tenant architecture **improves ActCAD in its own right**
- Retrofitting it later would mean **reworking six of ten modules**

---

## Principal risks

| Risk | How we would manage it |
|---|---|
| **Management attention diverted from ActCAD** | Platform work is scoped and time-boxed; ActCAD GA remains the priority |
| **Demand unproven** — no members, no LOIs | Month-24 gate; no entity or obligations before it |
| **Team must be recruited** | Required for ActCAD regardless; platform shares the cost |
| **Member roadmap influence** | Members advise; **they do not hold a vote** |
| **Licensing verticals to potential competitors** | Named-competitor exclusion, or the tier is simply not offered |
| **Consortium members are slow to move** | Base case assumes 12 members over seven years |
| **Returns are modest** | Presented as an adjacent line, not a growth story |

---

## Governance and review gates

| Point | Test | If not met |
|---|---|---|
| **Month 12** | 8–10 qualified member conversations held | Outbound stops; engineering continues |
| **Month 24, at ActCAD GA** | **Two members at signed LOI** | **Commercialisation does not proceed** |
| **Before any vertical-tier sale** | No conflict with ActCAD's own markets | Tier withheld from that member |

<div class="big" markdown="1">

**If the month-24 gate is not met, the exposure is 3–6 engineer-months of architecture we would adopt for ActCAD in any case.**

</div>

---

<!-- _class: lead -->

# Decisions requested

<div class="big" markdown="1">

**In-principle approval to proceed with exploration**

</div>

### And to open three discussions

- **Corporate structure**
- **Capital requirement**
- **Team required**

**No capital commitment, incorporation, external communication, or change to ActCAD's operations is sought today.**
