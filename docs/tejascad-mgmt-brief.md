---
marp: true
theme: default
paginate: true
size: 16:9
header: 'TejasCAD · Directors briefing'
footer: 'Confidential · Working brand pending TM clearance'
style: |
  section { font-size: 25px; padding: 60px 70px; }
  h1 { color: #1a3a6c; }
  h2 { color: #2d5fa7; border-bottom: 2px solid #2d5fa7; padding-bottom: 6px; }
  h3 { color: #2d5fa7; }
  table { font-size: 0.85em; }
  blockquote { border-left: 4px solid #2d5fa7; color: #333; background: #eef4fb; padding: 12px 18px; }
  strong { color: #1a3a6c; }
  .big { font-size: 1.3em; line-height: 1.35; color: #1a3a6c; }
---

<!-- _class: lead -->
<!-- _paginate: false -->

# Building for ActCAD, or building for the world?

### A directors briefing — for discussion

**Working brand TejasCAD, pending TM clearance.**

ITC pricing is what we actually pay. Our own projections are illustrative.

---

## The decision on the table

- We are **already** re-architecting ActCAD off IntelliCAD. **That continues either way.**
- The question is one level up: **do we build it only for ActCAD, or as a platform other CAD vendors license under their own brand?**
- Every seam we build for ActCAD — tenant profile, licensing, plugin host, AI — **is what a white-label platform needs anyway**
- The market is specific: **~40 ITC members**, **~200 vertical ISVs**, BIM-lite startups
- **"Can we build it" is settled** — Phase 0 ships today

---

## Phase 0 today — what already ships

Six weeks, ~207 commits, 13+ drops to the ActCAD team.

| Area | Status |
|---|---|
| **DWG/DXF** | Real customer files open in the browser. WASM + ODA inWEB, both live. |
| **Measure / snap / count** | Full 14-mode osnap suite, CSV + Excel export |
| **Performance** | 250K entities at 61 fps; regen 17× faster; instant zoom-extents |
| **3D** | Orbit, standard views, ViewCube. Layouts + paper space viewports. |
| **Beyond scope** | DWG↔DWG and PDF comparison, colour plotting, batch print, markups |
| **Distribution** | Windows MSI shipping. macOS CI green. Android prototype. |
| **Tests** | 594/594 green, plus a native gate harness |
| **The hard rule** | **Read-only guarantee holds. No `db` writes anywhere.** |

> **Faster than ActCAD on many customer files — and well ahead of IntelliCAD's viewer and ODA's own.** Before public launch.

**Still owed:** customer-hardware perf baseline · public launch and adoption signal.

---

## Architecture for the editor

Some ODA features are not exposed to the web stack. The full editor needs a **native** path.

- **Now → viewer launch** — continue on Rust/Tauri + WASM/inWEB. Ship it.
- **After launch** — **migrate the full product to Qt + C++ native.** This is where the missing ODA surface becomes available, and where the ActCAD team wants to be long term.
- **The web viewer** — either folds into the Qt stack as a second frontend on the same C++ engine, or stays on Rust/Tauri. **Decide with data during the migration.**

> **The platform seams — tenant profile, licensing, marketplace, AI agent — live in the C++ core regardless of which shell wraps them.**

---

## The case against — stated at full strength

1. **We are a CAD company, not a platform company.** Different sales motion, different support model, skills we have never had.
2. **It distracts from what matters.** ActCAD-new reaching GA is the priority. **The real cost is management attention.**
3. **The money is not transformational.** Partner obligations and a second entity for a few million a year.
4. **We would be arming competitors** — especially by licensing our verticals.
5. **Members will constrain our roadmap.** Once they pay, we are less free to choose.
6. **Nobody has asked for this.** Zero members, zero LOIs.
7. **ITC members are sticky.** Twenty years in, switching costs are large.
8. **We do not have the team.** A platform team has to be hired from scratch.

> **2, 3, 5, 6 and 8 are substantially correct.**

---

## Why we still think yes

| Objection | Answer |
|---|---|
| Not a platform company | **True.** But nothing before month 24 requires becoming one. |
| Distracts from ActCAD | **Partly conceded** — attention is the real cost |
| Money is modest | **Conceded.** Not why we would do it alone. |
| Arming competitors | Gated by named-competitor exclusion — **or we don't sell that tier** |
| Roadmap constraint | **Conceded — the one that worries us most.** Input, never veto. |
| No demand proven | **Fully conceded. Zero LOIs.** Hence a kill switch at month 24. |
| Members are sticky | **True** — base case is 12 members in seven years, not fifty |
| No team | **Conceded.** But **we need that team for ActCAD-new regardless.** |

<div class="big" markdown="1">

**Building multi-tenant makes ActCAD better even if no member ever signs.**

</div>

**The tenant seam touches six of ten modules.** Building it now forces no ActCAD-specific hacks in core, a real plugin API, configuration-driven behaviour. **Retrofitting later means reworking those six modules after they harden.**

---

## Who builds it

| Function | Who |
|---|---|
| Engine, multi-tenancy, licensing, deep systems | **TejasCAD — dev team to be hired** |
| QA, release engineering, corpus and regression | **TejasCAD — to be hired** |
| Dev support, SDK, docs, member L3 | **TejasCAD — to be hired** |
| Domain expertise, verticals, IRX, product judgement | **ActCAD's team** |
| Selling ActCAD to end customers | **ActCAD's sales — unchanged** |
| A member's own L1/L2 and end-customer sales | **The member** |

> **That team is the engine team.** The platform does not create the cost — ActCAD-new needs those people either way. **It decides who employs them and who else helps pay.**

---

## The kill switch

- **Month 12** — have 8–10 qualified member conversations happened? If not, **stop outbound**
- **Month 24, at ActCAD-new GA** — **≥2 members at signed LOI, or we stop.** No platform entity, no partner obligations
- **Before any Complete-tier sale** — does it threaten ActCAD in that territory? If so, **don't sell it**

<div class="big" markdown="1">

**If month 24 fails, we lose 3–6 engineer-months — spent on architecture we would defend on ActCAD's own merits anyway.**

</div>

- What we keep regardless: **cleanly separated engine, real plugin API, configuration-driven behaviour, proper licensing abstraction**

---

## The two paths

| | Build for ActCAD only | Build as a platform |
|---|---|---|
| Engine work | Same | Same |
| Ship date | ~24 months to GA | Same, + tenant discipline in P1 |
| Extra P1 cost | Baseline | **~3–6 engineer-months** |
| Revenue | ActCAD only | **+ member fees, marketplace, vertical royalties** |
| Exit | ActCAD as one product | **A second, separately saleable asset** |
| If it fails | — | **We still shipped a great ActCAD** |

> **A no forecloses one thing that is hard to reopen: the architecture.** Everything else can be revisited in three years.

---

## What we pay IntelliCAD today

| | |
|---|---|
| ITC membership + extras | **~$100K / year** |
| Per-seat royalty to ITC | **$0** — royalty-free at the ITC level |
| Component royalties (ACIS and others) | **$15–20 per sale** |
| AI | **~$7–8K/yr extra** — experimental |
| Android viewer | **~$8K/yr extra** — weak |
| Mac, web app, web editor | **Not available. Windows-tied.** |

> **And what we get for it is ~a million lines of source** — not a product. A codebase to staff, fork and re-merge on every uptake, before selling a single seat.

---

## IntelliCAD++ — what we give that ITC does not

| | **ITC gives** | **We give** |
|---|---|---|
| The deliverable | ~1M lines of source | **A shipping product you configure** |
| Engine maintenance | **Yours, forever** | **Ours.** You never touch engine code |
| Engine bugs | You fix them; **your work reaches competitors** | **We fix them.** You draw from the pool without funding it |
| Your own plugins & verticals | Intertwined with engine patches | **Stay entirely yours** |
| Release cadence | Coordinated, annual | **Rolling — ship when ready** |
| Platform reach | Windows | **Windows, Mac, Linux, web, Android** |
| AI | ~$8K experimental add-on | **Included** |
| Licensing / DRM | Buy your own | **Included, and platform-blind** |
| Direction | Member supermajority | Platform decides; **members have voice** |

> **The consortium gave members shared ownership of a codebase and sole responsibility for running it. We carry the responsibility instead.**

---

## What we deliver, and what we would charge

**Tiers gate on what they take:**

| Tier | Adds |
|---|---|
| **Core** | Engine, DWG fidelity, white-label shell, build pipeline, licensing, **AI** |
| **Plus** | + web app, **Mac, Android**, marketplace |
| **Complete** | + **the ActCAD-derived verticals** (Arch / Mech / Elec / BIM / GIS) |

**Priced by the member's own installed base:**

| Seat base | Core | Plus | Complete |
|---|---|---|---|
| Under 5,000 | $45K | $65K | $90K |
| 5,000–20,000 | $80K | $110K | $150K |
| 20,000–50,000 | $130K | **$170K** | $220K |
| 50,000+ | $190K | $240K | $300K |

- **Ramped 50% / 75% / 100%** over migration years 1–3
- **Component royalties pass through at cost** — no markup
- **AI metered above an allowance**, or bring your own key — inference is a real per-use cost
- **Complete tier is a decision, not just a price** — it arms vendors who may compete with ActCAD

---

## What this could become

| | Conservative | Base | Aggressive |
|---|---|---|---|
| Members by Y7 | 5 | 12 | 20 |
| Blended fee | ~$70K | ~$110K | ~$170K |
| + marketplace & royalties | ~$15K | ~$30K | ~$45K |
| **Platform ARR** | **~$425K** | **~$1.7M** | **~$4.3M** |
| Margin | ~68% | ~70% | ~72% |
| **Profit contribution** | **~$290K** | **~$1.2M** | **~$3.1M** |
| Enterprise value at 6–8× | not saleable | ~$10–13M | **~$26–34M** |

> **A profitable adjacent business line, not a venture-scale company.** Good return on a few engineer-months on an engine we are building anyway.

**Materially bigger needs ~60–100 members, direct-to-end-user, or the 3D product — later questions, not assumptions.**

---

## Funding

| Stage | When | Size |
|---|---|---|
| **Promoter seed** | Now → Y2 | **$1–2M** — the increment on an already-funded engine |
| **Strategic round** *(optional)* | Y4–5 | **$5–10M** — sets a floor, from a plausible acquirer |
| **Exit** | Y6–7 | Target **$30–50M** |

- A priced round's post-money **does** anchor expectations — but only if defensible
- **What forces price up is competition between buyers, not a prior round**
- At ~70% margins this **self-funds from year 3** — take the round for tension, not cash

---

## What we are asking

<div class="big" markdown="1">

**In-principle approval.**

</div>

**And to open three discussions:**

- **Corporate structure**
- **Capital requirement**
- **The team required to make this happen**

> **Nothing else is being decided today.** No capital commitment, no incorporation, no announcement, no change to how ActCAD is run.
