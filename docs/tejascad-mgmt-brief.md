---
marp: true
theme: default
paginate: true
size: 16:9
header: 'Platform briefing · Directors'
footer: 'Confidential'
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

# A next-generation CAD platform

### Built in India. Licensed to the world.

**Directors' briefing**

*ITC figures are actual. Our projections are illustrative.*

---

## What we are proposing

- We are building **an engine we own** — and it is already running
- The same engine can carry **many brands, not just ours**
- That makes us **a platform business alongside a product business**

<div class="big" markdown="1">

**The proposal: build it platform-first from the outset.**

</div>

**Three things to work through together**

- **Corporate structure** · **Capital requirement** · **The team we build**

---

## Where the engineering stands

**Phase 0 — six weeks, ~207 commits, 13+ releases to the ActCAD team**

- **Customer DWG files open in the browser** — both WASM and ODA inWEB backends live
- **Full 14-mode osnap suite**, measurement, count, CSV and Excel export
- **250,000 entities at 61 fps** · regeneration 17× faster · instant zoom-extents
- **3D orbit, ViewCube, layouts and paper-space viewports**
- **DWG and PDF comparison**, colour plotting, batch print, markups
- **Windows MSI shipping** · macOS CI green · Android prototype
- **594 of 594 tests passing**

<div class="big" markdown="1">

**Benchmarking already puts it ahead of ActCAD on many customer files — and ahead of both IntelliCAD's viewer and ODA's own.**

</div>

---

## Architecture for the editor

**Certain ODA capabilities are not exposed through the web stack.**

- **To viewer launch** — continue on the current Rust/Tauri and WASM stack
- **After launch** — **migrate the full editor to Qt and C++ native**
  - opens the ODA surface unavailable on web
  - aligns with where the ActCAD team intends to work long term
- **The web viewer** — folds into the Qt stack, or remains separate
  - decided with data during migration

> **The platform capabilities — tenant configuration, licensing, marketplace, AI — live in the C++ core either way.**

---

## The opportunity

- **~40 IntelliCAD Consortium members** — regional CAD vendors on the foundation we are leaving
- **~200 vertical ISVs** — MEP, structural, electrical, survey, solar
- **BIM-lite startups** — needing a CAD foundation they cannot afford to build

**What they share**

- A foundation that **cannot deliver AI, cloud, web or mobile**
- **A million lines of source they must maintain themselves**
- **No practical alternative** short of a multi-year rebuild

<div class="big" markdown="1">

**Nobody is currently offering them a modern engine as a product. That is the opening.**

</div>

---

## What we pay IntelliCAD today

| | |
|---|---|
| Membership and extras | **~$100,000 per year** |
| Per-seat royalty to ITC | **None** |
| Component royalties (ACIS and others) | **$15–20 per sale** |
| AI module | **~$7–8,000 per year** — experimental |
| Android viewer | **~$8,000 per year** |
| **macOS** | **Not available at any price** |
| Web application and web editor | **Not available at any price** |
| Linux | **Not available at any price** |

> **The fee buys source code, not a product** — a codebase to staff, modify and re-merge at every version uptake.

**IntelliCAD is Windows-bound.** macOS, Linux and the browser are not options a member can buy — **they are doors that stay shut.**

---

## What we would offer instead

| | **IntelliCAD provides** | **We would provide** |
|---|---|---|
| Deliverable | ~1M lines of source | **A product they configure** |
| Engine maintenance | The member's problem | **Ours** |
| Engine defects | Member fixes; **work reaches rivals** | **We fix; member receives** |
| Member's own plugins | Entangled with engine changes | **Remain theirs** |
| Release cadence | Annual, coordinated | **Rolling** |
| Platform reach | **Windows only** | **Windows, macOS, Linux, web, Android** |
| AI | Paid add-on | **Included** |
| Licensing infrastructure | Member sources their own | **Included, and platform-blind** |

---

## Commercial model

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

- **Phased 50 / 75 / 100%** across each member's migration
- **Component royalties at cost** · **AI metered above an allowance**

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

**High-margin recurring revenue, earned on engineering we are funding anyway — and a second asset on the balance sheet.**

</div>

- Beyond this: **60–100 members**, direct distribution, or the **3D product on C3D** each open a materially larger business

---

## Investment required

| Stage | Timing | Amount |
|---|---|---|
| **Promoter seed** | Now to year 2 | **₹2 crore** |
| **Strategic round** *(optional)* | Years 4–5 | **$5–10M** |
| **Exit** | Years 6–7 | **$30–50M** target |

- The seed **funds the two-year build team** — next slide
- A strategic investor at years 4–5 **sets a valuation floor** ahead of any sale
- At ~70% margins the business **self-funds from year 3**

---

## Team required — the two-year build

| Role | Headcount | Cost |
|---|---|---|
| **CAD engine developers** | 2–4 | **₹100 lakh** |
| **Commands and UI developers** | 3–5 | **₹50 lakh** |
| **Marketing** | 1 | **₹25 lakh** |
| **Total** | **6–10 people** | **₹1.75 crore** |

<div class="big" markdown="1">

**₹2 crore seed against a ₹1.75 crore build — funded, with headroom.**

</div>

**A team this size is viable because of how we are building.** Phase 0 delivered ~207 commits and a shipping viewer in six weeks with AI-assisted development — the UI, commands, tests and tooling layers move several times faster than they used to.

- **AI carries the commands and UI layer** — that is where the leverage is real
- **Engine work still needs people** — ODA and ACIS integration, performance, vendor defects. Hire these deliberately.
- This is **the team the next ActCAD engine needs regardless** — the platform shares it, it does not create it

---

## Our approach

<div class="big" markdown="1">

**Build the platform capability now. Decide on commercialisation at month 24, with real data.**

</div>

- The multi-tenant architecture **makes ActCAD better in its own right** — clean core, real plugin API, configuration over hard-coding
- Building it now costs **3–6 engineer-months**. Retrofitting later means **reworking six of ten modules**
- We reach the month-24 decision **having lost nothing if we decline it**

| | **ActCAD only** | **Platform** |
|---|---|---|
| Engineering | Same | Same |
| Timeline to GA | ~24 months | Unchanged |
| Revenue | ActCAD alone | **Plus member fees and royalties** |
| Assets | One product | **Two separable assets** |

---

## What we need to get right

| Priority | How we address it |
|---|---|
| **ActCAD GA comes first** | Platform work is scoped and time-boxed around it |
| **Build the team well** | Needed for ActCAD regardless — the platform shares the cost |
| **Prove demand before committing** | Month-24 gate on two signed LOIs |
| **Keep control of the roadmap** | Members advise; **we decide** |
| **Protect our verticals** | Named-competitor exclusion; the tier stays optional |
| **Set a realistic pace** | Base case assumes 12 members over seven years |

<div class="big" markdown="1">

**Each of these is a decision we hold, not a dependency we carry.**

</div>

---

## Governance and review gates

| Point | Test | If not met |
|---|---|---|
| **Month 12** | 8–10 qualified member conversations held | Outbound pauses; engineering continues |
| **Month 24, at ActCAD GA** | **Two members at signed LOI** | Commercialisation does not proceed |
| **Before any vertical-tier sale** | No conflict with ActCAD's markets | Tier withheld from that member |

> **Every gate is a decision this board takes, on evidence, at the time.**

---

## The name

From Sanskrit **takṣ** — *to shape, to carve, to fashion*. The root of **Takshashila**.

| | Line | What a search turns up |
|---|---|---|
| **TAKSHON** | *Design Beyond Boundaries* | **Clear** — no Indian technology company trading on the name |
| **TAKSH** | *Precision in Every Dimension* | **Crowded** — four Indian software firms already use it |
| **TAKSHA** | *Design. Simulate. Build.* | **Conflict** — Taksha AI & Robotics Pvt Ltd, plus robotics and engineering firms |
| **VISTAAR** | *From Structures to Skylines* | Strong BIM story, but a common word in wide commercial use |

<div class="big" markdown="1">

**TAKSHON is the recommendation** — the only one of the four with room to own the category.

</div>

- Sub-brands follow naturally — **Engine · Cloud · Forge · SDK**
- These are web searches, **not register searches** — IP India Classes 9 and 42, plus USPTO and EUIPO, **before anything external**

---

<!-- _class: lead -->

# Let's build it

<div class="big" markdown="1">

**A next-generation CAD platform, engineered in India, licensed to the world.**

</div>

### Where we'd like to go from here

- **Build platform-first from the outset**
- **Work through structure, capital and team together**

**The engine is already running. The question is how far we take it.**
