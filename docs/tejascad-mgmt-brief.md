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
  .big { font-size: 1.3em; line-height: 1.35; color: #1a3a6c; }
---

<!-- _class: lead -->
<!-- _paginate: false -->

# Building for ActCAD, or building for the world?

### A directors briefing — for discussion

**Working brand TejasCAD** · pending TM clearance

*ITC pricing is what we actually pay. Our own projections are illustrative.*

---

## The decision on the table

- We are **already** moving ActCAD off IntelliCAD — **that continues either way**

- The question is one level up:

<div class="big" markdown="1">

**Build it only for ActCAD — or as a platform other CAD vendors license under their own brand?**

</div>

- Every seam we build for ActCAD is **what a platform needs anyway**
- A specific market: **~40 ITC members** · **~200 vertical ISVs** · BIM-lite startups
- **"Can we build it" is settled** — Phase 0 ships today

---

## Phase 0 — what already ships

**Six weeks · ~207 commits · 13+ drops to the ActCAD team**

- **Real customer DWGs open in the browser** — WASM and ODA inWEB, both live
- **Full 14-mode osnap suite**, measure, count, CSV + Excel export
- **250K entities at 61 fps** · regen 17× faster · instant zoom-extents
- **3D orbit, ViewCube, layouts, paper-space viewports**
- **DWG↔DWG and PDF comparison**, colour plotting, batch print, markups
- **Windows MSI shipping** · macOS CI green · Android prototype
- **594/594 tests green** · read-only guarantee intact

> **Faster than ActCAD on many customer files — and well ahead of IntelliCAD's viewer and ODA's own.**

**Still owed:** customer-hardware perf baseline · public launch

---

## Architecture for the editor

**Some ODA features are not exposed to the web stack.**

- **Now → viewer launch** — stay on Rust/Tauri + WASM. Ship it.
- **After launch** — **migrate the full editor to Qt + C++ native**
  - where the missing ODA surface becomes available
  - where the ActCAD team wants to be long term
- **The web viewer** — folds into the Qt stack, or stays on Rust/Tauri
  - **decide with data during the migration**

> **The platform seams live in the C++ core** — whichever shell wraps them.

---

## The case against — at full strength

- **We are a CAD company, not a platform company**
- **It distracts from what matters** — the real cost is management attention
- **The money is not transformational**
- **We would be arming competitors**
- **Members will constrain our roadmap**
- **Nobody has asked for this** — zero members, zero LOIs
- **ITC members are sticky** — twenty years in
- **We do not have the team** — it has to be hired from scratch

<div class="big" markdown="1">

**Five of those eight are substantially correct.**

</div>

---

## Why we still think yes

- **Not a platform company** — nothing before month 24 requires becoming one
- **Distracts from ActCAD** — *partly conceded*, attention is the real cost
- **Money is modest** — *conceded*, not a reason on its own
- **Arming competitors** — gated, **or we simply don't sell that tier**
- **Roadmap constraint** — *conceded*, **the one that worries us most**
- **No demand proven** — *fully conceded*, hence the kill switch
- **No team** — *conceded*, but **we need that team for ActCAD anyway**

<div class="big" markdown="1">

**Building multi-tenant makes ActCAD better even if no member ever signs.**

</div>

- Forces a clean core, a real plugin API, configuration over hard-coding
- **Retrofitting later means reworking six of ten modules**

---

## Who builds it

- **TejasCAD hires** — dev · QA · dev support
- **ActCAD's team does what it is best at** — domain expertise, verticals, IRX, product judgement
- **ActCAD's sales is unchanged** — same team, same customers
- **Members support their own customers** — never us

<div class="big" markdown="1">

**That team is the engine team. ActCAD-new needs those people either way.**

</div>

- The platform doesn't create the cost — **it decides who employs them, and who else helps pay**

---

## The kill switch

- **Month 12** — 8–10 qualified member conversations, or **stop outbound**
- **Month 24, at ActCAD GA** — **2 signed LOIs, or we stop entirely**
  - no platform entity · no partner obligations · no second set of books
- **Before any vertical-tier sale** — if it threatens ActCAD, **don't sell it**

<div class="big" markdown="1">

**If month 24 fails we lose 3–6 engineer-months — on architecture we'd defend on ActCAD's own merits.**

</div>

- And we still keep a clean engine, a real plugin API, a proper licensing layer

---

## The two paths

| | **ActCAD only** | **As a platform** |
|---|---|---|
| Engine work | Same | Same |
| Ship date | ~24 months | Same |
| Extra cost | — | **3–6 engineer-months** |
| Revenue | ActCAD | **+ member fees, marketplace, royalties** |
| Exit | One product | **A second saleable asset** |
| If it fails | — | **We still shipped a great ActCAD** |

> **A no forecloses one thing that is hard to reopen — the architecture.** Everything else can wait three years.

---

## What we pay IntelliCAD today

- **~$100K a year** — membership and extras
- **No per-seat royalty to ITC**
- **$15–20 per sale** — component royalties, ACIS and others
- **AI: ~$7–8K extra** — experimental
- **Android viewer: ~$8K extra** — weak
- **Mac, web app, web editor: not available.** Windows-tied.

<div class="big" markdown="1">

**And what we get is ~a million lines of source — not a product.**

</div>

- A codebase to staff, fork and re-merge on every uptake, **before selling a seat**

---

## What we'd give that ITC does not

| | **ITC gives** | **We give** |
|---|---|---|
| Deliverable | ~1M lines of source | **A product you configure** |
| Engine upkeep | **Yours, forever** | **Ours** |
| Bug fixes | You fix — **work reaches rivals** | **We fix — you just receive** |
| Your plugins | Tangled with engine patches | **Stay entirely yours** |
| Releases | Annual, coordinated | **Rolling — ship when ready** |
| Reach | Windows | **Win · Mac · Linux · web · Android** |
| AI | $8K experiment | **Included** |
| Licensing | Buy your own | **Included, platform-blind** |

> **The consortium gave members shared ownership of a codebase and sole responsibility for running it. We carry the responsibility instead.**

---

## What we deliver, and what we'd charge

**Three tiers**

- **Core** — engine, DWG fidelity, white-label shell, licensing, **AI**
- **Plus** — **+ web app, Mac, Android**, marketplace
- **Complete** — **+ our verticals** (Arch · Mech · Elec · BIM · GIS)

| Member's seats | Core | Plus | Complete |
|---|---|---|---|
| Under 5,000 | $45K | $65K | $90K |
| 5,000–20,000 | $80K | $110K | $150K |
| 20,000–50,000 | $130K | **$170K** | $220K |
| 50,000+ | $190K | $240K | $300K |

- **Ramped 50 / 75 / 100%** over the migration years
- **Component royalties at cost** · **AI metered** above an allowance
- **The vertical tier is a decision, not a price** — it arms possible competitors

---

## What this could become

| | Conservative | Base | Aggressive |
|---|---|---|---|
| Members by Y7 | 5 | 12 | 20 |
| Blended fee | ~$70K | ~$110K | ~$170K |
| **Platform ARR** | **~$425K** | **~$1.7M** | **~$4.3M** |
| **Profit** | **~$290K** | **~$1.2M** | **~$3.1M** |
| Value at 6–8× | not saleable | ~$10–13M | **~$26–34M** |

<div class="big" markdown="1">

**A profitable adjacent business line — not a venture-scale company.**

</div>

- Materially bigger needs **60–100 members**, direct-to-end-user, or **the 3D product**
- **Later questions — not assumptions**

---

## Funding

- **Promoter seed, now → Y2 — $1–2M**
  - the increment on an engine already funded
- **Optional strategic round, Y4–5 — $5–10M**
  - from a plausible acquirer, **to set a floor**
- **Exit, Y6–7 — $30–50M**

<div class="big" markdown="1">

**What forces price up is competition between buyers — not a prior round.**

</div>

- At ~70% margins this **self-funds from year 3**
- **Take the round for tension, not for cash**

---

<!-- _class: lead -->

# What we are asking

<div class="big" markdown="1">

**In-principle approval**

</div>

### And to open three discussions

- **Corporate structure**
- **Capital requirement**
- **The team required to make this happen**

**Nothing else is decided today** — no capital commitment, no incorporation, no announcement, no change to how ActCAD runs.
