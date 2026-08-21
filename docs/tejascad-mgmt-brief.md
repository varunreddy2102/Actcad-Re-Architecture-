---
marp: true
theme: default
paginate: true
size: 16:9
header: 'TejasCAD · Directors briefing · Concept approval in principle'
footer: 'Confidential · Working brand pending TM clearance · Competitor pricing = actuals; our projections = illustrative'
style: |
  section { font-size: 24px; padding: 60px 70px; }
  h1 { color: #1a3a6c; }
  h2 { color: #2d5fa7; border-bottom: 2px solid #2d5fa7; padding-bottom: 6px; }
  h3 { color: #2d5fa7; }
  table { font-size: 0.85em; }
  blockquote { border-left: 4px solid #2d5fa7; color: #333; background: #eef4fb; padding: 12px 18px; }
  strong { color: #1a3a6c; }
  .big { font-size: 1.35em; line-height: 1.4; color: #1a3a6c; }
  .quiet { color: #666; font-size: 0.85em; }
---

<!-- _class: lead -->
<!-- _paginate: false -->

# Building for ActCAD, or building for the world?

### A directors briefing — concept approval in principle

**Companion documents already circulated:**
`docs/tejascad-story.md` · `docs/tejascad-company-structure.md` · `docs/tejascad-vs-intellicad.md` · `docs/tejascad-licensing-architecture.md`

*Working brand TejasCAD pending TM clearance. **ITC and ODA pricing are actuals we pay or can verify; our own projections are illustrative.** This briefing asks for concept approval, not a spend commitment.*

---

## The decision on the table today

We are already re-architecting ActCAD off IntelliCAD onto our own engine. That work continues either way.

**Today's question is one level higher:**

<div class="big" markdown="1">

**Do we build the new engine only for ActCAD — or do we build it as a platform that ActCAD is the anchor tenant of, and license the same platform to other CAD vendors under their own brand?**

</div>

The technical answer to "can we build this?" is now yes — with real evidence. Phase 0, six weeks in (~207 commits), already ships a working viewer that the ActCAD team is beta-testing daily. **This is no longer a feasibility conversation. It is a strategy conversation.** Detail on the next slide.

---

## Phase 0 today — what already ships

Six weeks in, ~207 commits, versioning aligned to ActCAD's own (26.1 → 26.3.7, the latest drop fixing 5 team-reported bugs).

| Area | Status |
|---|---|
| **DWG/DXF open** | Real customer files open in the browser on WASM + ODA inWEB. Both backends live. |
| **Measurement + snap + count** | Full 14-mode AutoCAD/ActCAD osnap suite; count + CSV/Excel export; quick calc. |
| **Rendering perf** | 250K entities at 61 fps via region rendering + culling; regen 17× faster; instant zoom-extents. |
| **3D** | Visualize camera bound — orbit, standard views, live 3D ViewCube shipping. Layouts + paper space viewports work end-to-end. |
| **Beyond scope** | DWG↔DWG + PDF revision comparison, color plotting, batch print, print-to-PDF, sidecar markup overlays. |
| **Distribution** | Tauri Windows MSI + `setup.exe` shipping. macOS CI build green. Android Tauri prototype exists. |
| **Test posture** | 594/594 web tests green; gate-5 native harness (22 cases, 223 assertions) exercises the ui-bridge with no shell-specific branching in core. |
| **Feedback loop** | **The ActCAD team is the de-facto closed beta** — filing numbered bugs against each drop, driving priorities. 13+ release drops delivered. |
| **The one hard rule** | **Read-only guarantee has held throughout.** No `db` writes anywhere in the codebase. Structurally intact. |

> **Competitive posture from live testing:** the new viewer is **faster than ActCAD's current product on many customer files, and significantly better than IntelliCAD's viewer and ODA's own web viewer.** The engineering work has already produced a best-in-class result — before we've even shipped it publicly.

**Still owed from the exit criteria:** customer-hardware perf gate measurement (2019-i5 baseline) and public web adoption signal (there is no public launch yet).

**Vendor blockers logged:** three ODA inWEB gaps (paper-space engine abort, TTF tessellation quality, unbound `appServices`) — all filed / worked around; none block the strategy.

---

## The Phase 1 architectural direction — what we already know

The viewer is proving something else: **some ODA features are not exposed through the web stack.** For those, the full-editor product needs a **native application** path, not just a browser.

**Plan (already consistent with the original re-architecture plan):**

- **Now → viewer launch:** continue on the current Rust/Tauri + WASM/inWEB stack. Ship the viewer.
- **After viewer launch:** **migrate the full-product to Qt + C++ native.** This is where the ODA features currently missing from the web stack become available, and where the ActCAD team wants to live long-term.
- **The web viewer:** either **folds into the Qt stack** as an alternate frontend on the same C++ engine, or **stays on Rust/Tauri** as an independent codebase. Open decision — settled with data during the migration.

**Why the directors should hear this now:**

- The Qt/C++ direction is not a change of plan; it is what the re-architecture always intended for the full product. The Rust/Tauri viewer is the entry point, not the destination.
- The "should the web viewer live in Qt or stay Rust/Tauri?" question is a **healthy** architectural choice we get to make after the viewer ships, not a fire we're fighting.
- **None of this changes the platform argument.** The platform seams (tenant profile, encrypted licensing, marketplace, MCP agent) live in the C++ core regardless of which shell wraps them.

---

## Where the platform idea came from — and why now

The re-architecture we approved earlier gave us **an engine we own** on ODA + ACIS + Qt + WASM, with a plugin surface, an MCP-based AI layer, and a modern shell.

Halfway through building it, one thing became obvious:

**Every seam we're building to serve ActCAD** — the tenant-profile layer, the license service, the plugin marketplace, the AI agent — **is exactly what a white-label CAD platform needs.** We're paying the cost. We might as well capture the value.

And a specific market opened at the same time:

- ~40 IntelliCAD Consortium members are stuck exactly where ActCAD was
- ~200 vertical ISVs have no clean CAD engine to license
- BIM-lite / AEC startup segment is looking for a foundation they don't have to build

**They already spend $700K–1.3M a year all-in on a foundation they don't love** — next slide. We can offer them a better one.

---

## Building for ActCAD vs building for the world — the two paths, side by side

| Dimension | Build for ActCAD only | Build as a platform (ActCAD = anchor tenant) |
|---|---|---|
| Engine work | Same | Same |
| Ship date | ~24 months to GA | Same 24 months to GA + tenant-profile discipline in P1 |
| Extra P1 engineering cost | Baseline | **~3–6 engineer-months** for the tenant layer done properly |
| Revenue model | ActCAD license + AI/cloud subs | Same for ActCAD **plus** member fees + royalty pass-through + marketplace share + vertical co-development royalties |
| Passive-revenue upside | Zero | **Real** — every member added is annuity income from work we already did |
| Exit optionality | ActCAD sold as a product | A second, separately saleable asset — modest on its own (~$14–54M, see scenarios), but it also makes ActCAD itself a cleaner acquisition |
| Risk if platform play fails | — | We still shipped a great ActCAD. Nothing wasted. |

> **The platform path costs a small P1 discipline premium and unlocks a real second revenue line.** If members don't come, we've still shipped ActCAD. If they do, we have a profitable business that cost us almost nothing to option.

---

## What a member pays IntelliCAD today — and what they actually get for it

We are an IntelliCAD member. **We know this market's economics because we live them.**

| ActCAD's ITC bill | Amount |
|---|---|
| ITC membership + extras | ~$100K / year |
| Per-seat royalty to ITC | $0 — royalty-free at the ITC level |
| Component royalties (ACIS and a few others) | $15–20 per sale |

**But the membership fee is the small part of the cost.** What ITC hands you is roughly **a million lines of source code**. That is not a product you can ship. It is a codebase you now have to staff, patch, fork, and re-merge on every ITC version uptake — **forever** — before you can sell a single seat.

**The real cost of being an IntelliCAD member:**

| Line | Typical mid-size member |
|---|---|
| ITC membership + extras | ~$100K |
| Component royalties (~3–4K sales/yr) | ~$60K |
| Third-party DRM (Sentinel / Reprise) + integration | $50–150K |
| 6–8 engineers maintaining the fork and building features | $500K–1M |
| **Realistic all-in cost of ownership** | **~$700K – $1.3M / year** |

**What ITC sells as paid add-ons — and what they actually are:**

| Add-on | ITC price | Reality |
|---|---|---|
| AI | ~$7–8K / yr | Experimental. Unclear how much is genuinely usable. |
| Android viewer | ~$8K / yr | Exists, but weak. |
| Mac / full web app / web editor | — | **Not available. IntelliCAD is Windows-tied.** |

> **The add-ons are cheap because they are not really products.** That matters for how we price: **we bundle, we do not itemize.** The moment we put a line item called "AI" on a quote, we get compared to an $8K experiment. Bundled into one platform fee that retires most of a $700K–1.3M stack, the comparison is the one we want.

---

## The lesson from ODA — cheap memberships won

ODA and IntelliCAD sell into **the same market**. Look at what they charge and what it got them.

| | **IntelliCAD (ITC)** | **ODA** |
|---|---|---|
| Entry price | ~$100K / year | **$3K first yr / $2.25K renewal** |
| Main commercial tier | ~$100K + paid add-ons | **$7.5K first yr / $4.5K renewal** — unlimited seats, no per-seat royalty |
| Top tier | — | $37.5K / $18K — full source, Git access, **board nomination** |
| Add-ons | AI ~$8K, Android ~$8K | Extensions $5–10K each |
| **Members** | **~40** | **~1,200+** |
| Who's on it | Regional CAD vendors | Bricsys, GstarCAD, ZWCAD, NanoCAD, Graphisoft, Vectorworks, Bentley, Trimble, Dassault |

**ODA charges roughly 1/20th of ITC and has ~30× the members.** That is not an accident — **low friction beat high extraction**, in exactly the market we are entering.

**But we cannot simply copy their price, and it's important to be clear why:** ODA ships *components*. The member does their own integration, and ODA's cost to serve each member is near zero. **We ship a turnkey white-labeled product with migration support** — our cost to serve is real (~$70K/member). Price below that and every member loses us money.

> **So we copy ODA's structure, not their number:** a genuinely cheap, genuinely self-serve bottom rung that costs us almost nothing to support — and paid rungs above it where we do real work. That is the next slide.

---

## Two speeds — a wide funnel and a paid core

| | **Developer tier** *(the ODA lesson)* | **Commercial tiers** *(where the revenue is)* |
|---|---|---|
| Price | **$6K first yr / $4K renewal** | $90K – $450K / yr |
| Who | Vertical ISVs, BIM-lite startups, individual devs, evaluators | Regional CAD vendors, funded ISVs shipping at scale |
| What they get | Engine + SDK + build pipeline, docs, community support, marketplace publishing | Full white-label, migration engineering, dedicated support, verticals, AI, multiplatform |
| Support model | **Self-serve. Near-zero cost to serve.** | Hands-on. ~$70K/member/yr |
| Seat cap | Capped (e.g. 500 seats) — outgrow it, move up | Uncapped |
| Why we do it | **Funnel + ecosystem + marketplace supply** | Pays for the platform |

**The developer tier is not a revenue line — it is the growth engine.** Sixty developer members at $4K is $240K, which is rounding error. What it actually buys:

- **Reach into the ~200 vertical ISVs and ~40 BIM-lite startups** who would never write a $90K cheque but might write a $6K one
- **A pipeline that graduates upward** — today's $6K ISV shipping 300 seats is tomorrow's $180K Growth-tier member
- **Marketplace supply** — plugins need developers, and developers need cheap access
- **The path past ~20 members.** Twenty commercial members is the realistic Y7 ceiling, and that caps the business near $50M. **A cheap bottom rung is how you get to 60–100.** ODA proved that in this exact market.

> **This is the one argument that the ceiling is higher than the base case suggests.** Twenty commercial members caps out around $50M — but an ODA-shaped funnel feeding those twenty, and graduating members into them over a decade, is a materially bigger business. It is a **Year 8–12 story, not a Year 7 one**, and it should not change today's decision.

---

## What each tier gates

**Two axes: how big they are, and how much of the platform they take.**

| Tier | What it unlocks |
|---|---|
| **Core** | Engine, DWG/DXF fidelity, white-label shell + build pipeline, encrypted licensing, **and AI** |
| **Plus** | + **web app, Mac, Android**, marketplace access, cloud AI |
| **Complete** | + **the ActCAD-derived vertical modules** (Arch / Mech / Elec / BIM / GIS), co-development priority |

> **AI ships in every tier, deliberately.** It is our sharpest edge over IntelliCAD — we want it in front of *every* member's end customers, not held back as an upsell. What we gate is the genuinely expensive-to-serve stuff: **extra platform shells, marketplace operations, and our verticals.**

**This is not a contradiction of "bundle, don't itemize."** A member buys *Plus*. They never see a line item called "AI — $40K" that invites comparison to ITC's $8K experiment.

---

## AI: bundle the capability, meter the consumption

**AI carries an ongoing marginal cost, and that has to be capped.** Bundling inference unmetered would put an **unbounded liability against a fixed fee** — a 10,000-seat member with 20% active AI use could plausibly burn more in inference than their entire platform fee. That single mistake would take the ~70% margin to nothing.

**So we treat AI inference exactly as we treat ACIS royalties: a pass-through cost, never a margin line.**

| Mechanism | How it works |
|---|---|
| **Per-seat allowance** | Each tier includes a modest monthly allowance — enough for normal drafting use |
| **Metered above it** | Beyond the allowance, billed at **cost plus a small ops margin**. Never subsidised. |
| **Bring your own key** | Member supplies their own model API key — **unlimited use, and it costs us nothing** |
| **They resell it** | Members price AI to their end customers however they like. **It becomes their revenue line, not our cost centre.** |

**And most calls should never hit a frontier model.** Routine work — command suggestion, drawing health, block detection — runs on **small or on-device models**. Frontier models are reserved for genuine agent tasks. That is the difference between a cost that scales with usage and one that doesn't.

> ⚠️ **Open item, stated honestly: we do not yet know our real inference cost per active user.** Sizing the allowance requires measuring it. **That is a Phase 1 task**, alongside the customer-hardware performance baseline — and until it is measured, the AI allowance numbers stay deliberately unset.

---

## The price matrix — and it ramps

**$300K on day one is steep for a vendor paying ITC $100K.** So we don't ask on day one, and we don't charge everyone the same.

| Member's seat base | **Core** | **Plus** | **Complete** |
|---|---|---|---|
| **Launch** — under 5,000 | $90K | $130K | $190K |
| **Growth** — 5,000–20,000 | $180K | $230K | $300K |
| **Scale** — 20,000–50,000 | $300K | $360K | $450K |
| **Enterprise** — 50,000+ | $450K | $520K | $620K+ |

*(ActCAD sits in **Scale / Plus — $360K**. The anchor tenant pays a real, arm's-length number. That discipline is what makes the model credible to everyone else.)*

**And it ramps, because their revenue on our platform ramps:**

| Migration year | They pay |
|---|---|
| Year 1 — porting, still paying ITC in parallel | **50%** |
| Year 2 — GA under their brand | **75%** |
| Year 3+ — fully migrated, ITC contract ended | **100%** |

> ⚠️ **Complete needs a decision, not just a price.** Licensing our verticals arms vendors who may compete with ActCAD in adjacent markets. The named-competitor exclusions and territory carve-outs in the Verticalised Solutions Program **stop being boilerplate the moment we sell that tier.**

---

## Membership + royalty, or membership only?

**Recommendation: no per-seat royalty to us. Tier by scale instead.**

| | Membership + per-sale royalty | **Tier by seat band (recommended)** |
|---|---|---|
| Revenue scales with member success | Yes | **Yes — same economics, via the band** |
| How it reads to an ITC member | A **downgrade** — ITC is royalty-free at the ITC level | Familiar; like any subscription |
| Reporting burden | Per-sale reporting, audits, friction | **One annual seat attestation** |
| Trust posture | We audit them | **They self-attest; we verify the signature** |
| Marketing line | — | **"No per-seat royalty to the platform."** Clean and quotable. |

**The elegant part: our licensing architecture already produces exactly the number we need.** The quarterly aggregate attestation — a signed count of active deployments, with no customer identities in it — is already in the design for ACIS royalty reporting. **The tier true-up rides on infrastructure we're building anyway, and it works without us ever seeing who their customers are.**

**Component royalties (ACIS etc.) still pass through at cost** — the same $15–20/sale they already pay. No markup. That's the one number they can compare directly, so it stays scrupulously clean.

---

## Founding status — earned by tier, not by showing up early

**Founding benefits cost us real money. They go to members who bring real reference value and take real risk — not to everyone who signs first.**

| | **Founding Partner** | **Founding Member** | **Early adopter** | **Developer tier** |
|---|---|---|---|---|
| Who qualifies | **Scale / Enterprise** (20K+ seats, $300K+) | **Growth** (5–20K seats, $180K) | **Launch** ($90K) | $6K self-serve |
| Slots available | **Max 3** | **Max 5** | uncapped | uncapped |
| Fee discount | **30%, locked 5 yrs** | **20%, locked 3 yrs** | 15%, 2 yrs | — *(already the cheap rung)* |
| **Warrants** | **Yes** — small equity stake, vests 3–4 yrs | No | No | No |
| Governance | **Technical advisory board seat** | Roadmap input, no seat | — | — |
| Vertical co-dev split | **50 / 30 / 20** | 45 / 35 / 20 | standard 40 / 40 / 20 | n/a |
| Marketplace fee holiday | 24 months | 12 months | — | — |
| Public designation | **"Founding Partner"** | "Founding Member" | — | — |

**Two conditions on all of it:**

1. **A deadline** — founding agreements must be signed **before platform GA**. After that the designation closes permanently, or it stops meaning anything.
2. **ActCAD does not take a founding slot.** It pays standard Scale-tier rates as the anchor tenant. **The arm's-length discipline matters more than the discount**, and it keeps all three Partner slots available for genuine external reference customers.

> **The warrants are the piece worth arguing about.** Giving equity to a customer is unusual — but a Founding Partner holding warrants stops being a licensee and becomes an ally who wants the platform **acquired well**. At three slots the dilution is negligible, and it is the strongest retention tool we have against a member drifting back to ITC or building their own.

---

## The passive-revenue picture

**The blended fee depends entirely on who actually signs, so here is the assumed mix — not a number pulled from the air.** A realistic 12-member book at Year 7:

| Count | Tier | Fee |
|---|---|---|
| 4 | Launch / Core | $90K |
| 3 | Launch / Plus | $130K |
| 2 | Growth / Plus | $230K |
| 2 | Growth / Complete | $300K |
| 1 | Scale / Plus *(ActCAD)* | $360K |
| **12** | | **$2.17M → ~$181K blended** |

**Per-member economics on that mix:**

| Line | Per member / year |
|---|---|
| Platform fee (blended, per above) | ~$181K |
| Component royalties (ACIS etc.) | **$0 to us** — passed through at cost |
| Marketplace share (15% of ~$230K GMV, once mature) | ~$35K |
| Vertical co-development royalty (variable) | ~$15K |
| **Recurring revenue per member** | **~$230K** |
| Platform cost to serve one additional member | ~$70K |
| **Gross margin per additional member** | **~70%** |

*Cost to serve excludes AI inference, which is metered and passed through — see the AI slide. That is what keeps this margin real rather than notional.*

**What that compounds to:**

| Members (incl. ActCAD) | Recurring platform revenue | Contribution at ~70% margin |
|---|---|---|
| 3 | ~$550K/yr | ~$385K/yr |
| 6 | ~$1.2M/yr | ~$840K/yr |
| 12 | ~$2.8M/yr | ~$2.0M/yr |
| 20 | ~$4.6M/yr | ~$3.2M/yr |

*Early members sit below the mature figure — the ramp means a year-1 member pays half. The 3- and 6-member rows reflect that.*

> **This is on top of ActCAD's own revenue** — which we keep, in full, inside Jytra. And it comes from engineering we are funding anyway.

---

## What this could become — conservative, base, aggressive

Two variables drive everything: **how many members we sign**, and **what mix of tiers they buy.**

| | **Conservative** | **Base** | **Aggressive** |
|---|---|---|---|
| **Commercial** members by Y7 (incl. ActCAD) | 5 | 12 | 20 |
| Developer-tier members (funnel) | ~10 | ~40 | ~80 |
| Tier mix | mostly Launch / Core | the mix on the previous slide | skews Growth+ / Plus & Complete |
| Blended fee per member | ~$105K | ~$181K | ~$285K |
| **+ marketplace & vertical royalties** | ~$25K | ~$50K | ~$50K |
| **Platform ARR at Y7** | **~$650K** | **~$2.8M** | **~$6.7M** |
| Gross margin | ~68% | ~70% | ~73% |
| **Annual profit contribution** | **~$440K** | **~$2.0M** | **~$4.9M** |
| Indicative exit multiple | — | 5–6× | 7–8× |
| **Indicative enterprise value** | not saleable at this scale | **~$14–17M** | **~$47–54M** |
| What we'd likely do | Don't sell. Run it — it pays for itself | Sell, or keep compounding | Competitive process; genuine strategic interest |

*Developer-tier revenue is excluded above — at $4K it is immaterial (~$320K even at 80 members). **Its value is the graduation pipeline into the commercial tiers**, which is what makes the Y8–12 picture bigger than the Y7 one.*

*Component royalties (ACIS etc.) are excluded throughout — they pass through at cost and earn us nothing.*

**The honest read: a strong adjacent business line, not a venture-scale company.** The aggressive case is a ~$7M ARR business worth ~$50M, throwing off ~$5M/year. That is an excellent return on a few engineer-months of incremental work on an engine we are funding anyway — and it is not a unicorn.

> **What would make it materially bigger?** Not this model. Twenty members at $340K caps out near $50M. Reaching $20M+ ARR needs **~60–100 members** (the global long tail, a decade of partner management) or selling **direct to end users** alongside our members — a bigger, more competitive, quite different business. **A question to open deliberately later, not to assume today.**

---

## Funding path — and what actually sets an acquisition floor

**Promoter-funded at the start, as intended.** But the ask is small, because the expensive part is already committed.

| Stage | When | Size | Purpose |
|---|---|---|---|
| **Promoter seed** | Now → Y2 | **$1–2M** | Platform layer + licensing infra + first member onboarding. **The engine is already funded and building — this is the increment on top.** |
| **Strategic round** *(optional)* | Y4–5 | **$5–10M at $40–60M pre** | **The floor-setter.** See below. |
| **Exit** | Y6–7 | Target $50–100M | Competitive process, if the strategic round created tension |

**On setting a floor — the honest mechanics:**

- A priced round's post-money **does** anchor board and shareholder expectations. That part is real.
- But it only holds **if the valuation was defensible.** An inflated round doesn't create a floor — it creates down-round risk and scares acquirers off.
- **What actually forces price up is competition between buyers, not a prior round.**

> **So the highest-leverage move is not a big financial round — it's a small strategic one.** $5–10M from a *plausible acquirer* (an ODA-ecosystem vendor, a CAD-adjacent strategic, an Indian engineering major) does three things a financial round cannot: it **sets a defensible floor**, it **puts a real buyer on the cap table**, and it **forces rival buyers to move** rather than wait.

**And a caution worth stating plainly:** at ~74% margins this business likely **self-funds from year 3**. Raising money we don't need is dilution without benefit. **Take the strategic round for the strategic reason — the floor and the tension — not for the cash.**

---

## Who our first members would be

Not competition. Segments where they'd rather share the platform cost than fund the R&D alone.

| Segment | What they are | Why they'd talk to us |
|---|---|---|
| **Regional ITC members** | progeCAD, CADian, CMS IntelliCAD, DoubleCAD, and the long tail of regional / vertical ITC-based products | Stuck on the IntelliCAD ceiling for AI / cloud / web / mobile. Consortium sends their fixes to competitors. |
| **Vertical ISVs** | MEP, structural, electrical, survey, solar, curtain-wall specialists | No clean engine option. Forced onto AutoCAD SDK or DIY. Would ship a full branded CAD in 90 days on us. |
| **BIM-lite startups** | New AEC-tech founders in Bengaluru, EU, ME, LATAM | Need CAD + IFC + AI foundation; can't afford to build it |

**To be clear about who is NOT on this list:** BricsCAD, ZWCAD, and GstarCAD are **peers, not prospects.** They each already left IntelliCAD and built their own engine direct on ODA — ZWCAD and GstarCAD are among ActCAD's most direct competitors in India today. **We do not white-label to them.**

> That they made this exact move — and won — is the strongest external validation of the direction. We're taking the same road they took, and adding the white-label layer none of them built.

**We approach the real prospects warmly, from ActCAD's existing network** — not cold outbound. The founder's own relationships across India / SEA / MEA / EU open the first 10–15 conversations without a sales team.

---

## How we bring a member on — the 90-day pattern

Members don't build. Members configure. That is the whole point.

| Week | What happens | Who does it |
|---|---|---|
| **W0** | LOI signed. Member gets sandboxed evaluation build with their brand pre-configured, and their 20 hardest customer DWGs test-loaded. | Member evaluates. TejasCAD supports. |
| **W1–4** | Tenant profile finalized: brand assets, EULA, command-prefix, feature flags, license-server endpoint, marketplace share %. **License Authority key generated and handed to the member — we never see it again.** | Joint. |
| **W5–10** | Existing extensions ported to our plugin SDK (95% of LISP works unchanged; .NET migration guide handles the rest). Dedicated migration engineer embedded. | Member engineering + TejasCAD migration lead. |
| **W11–13** | Closed beta with 5–15 of the member's own friendly customers under NDA. | Member. |
| **W14+** | **GA under the member's brand.** Signed installers roll out of our build pipeline. AI, cloud, web features go live with their name on them. | Member sells to their customers. |

**Full detail:** `docs/tejascad-vs-intellicad.md` §6 + `docs/tejascad-licensing-architecture.md` §5–6.

---

## How Jytra + ActCAD change (and how they don't)

<div class="big" markdown="1">

**Jytra keeps everything it has today. ActCAD keeps everything it has today. TejasCAD is a sibling entity built alongside.**

</div>

| Thing | What changes |
|---|---|
| **ActCAD brand, customers, channel, pricing** | No change |
| **Jytra ownership of ActCAD** | No change — Jytra remains the parent of ActCAD as a product |
| **Where the engine lives** | Owned by a new entity (TejasCAD Inc. + India Op-Co), licensed to Jytra for ActCAD on **standard-member terms** — same as every other member |
| **P&L reporting** | Two entities, two sets of books, arm's-length invoices between them |
| **Promoters' equity in ActCAD** | No change |
| **Promoters' equity in TejasCAD** | New — the founding cap table, capitalized in personal capacity |
| **Existing ActCAD customer commitments** | Fully honored. Migration plan is transparent, staged over 24 months. |

**The discipline that makes this work:** ActCAD pays TejasCAD the same rate as any external member. That is what makes the platform economics real for investors and clean for a future acquirer.

---

## Trust wedge — what we tell members that no one else can

**"Ship your licensing through our infrastructure. We architecturally cannot see your customer list, your seat counts, your prices, or your license contents. Not by policy — by cryptography. Third-party audited annually."**

- **Member holds their own License Authority key.** We generate it and destroy our copy at onboarding.
- **License payloads are encrypted with keys we don't have.** Even if we're breached, attackers get ciphertext + aggregate counters.
- **Subpoena-resistant by design.** We cannot break the crypto for a government any more than for an attacker.
- **Survives us.** If TejasCAD ever goes away, the member's licensing keeps working. Playbook shipped with the SDK.

Full technical spec: `docs/tejascad-licensing-architecture.md` (25 pages, external cryptographic audit planned before v1).

> This one property alone is worth a member conversation for every regulated-sector customer they're trying to close. **No competitor offers it. IntelliCAD structurally cannot.**

---

## What we're asking today — and what we're explicitly NOT asking

**We're asking for: concept approval in principle.** That's it.

That approval unlocks the following prep work — none of which commits capital or public communication:

- Draft Master Platform License Agreement template (Jytra ↔ TejasCAD)
- Open trademark clearance on TejasCAD + sub-brand family (TejasCAD Engine / Forge / Cloud / SDK)
- Corporate counsel scoping of the entity structure — **note the earlier Delaware C-Corp recommendation was premised on institutional VC rounds we are no longer planning; a simpler Indian structure may now be correct**
- Non-binding scoping conversation with 3–5 candidate member CEOs (all in ActCAD's existing warm network)
- Encrypted licensing v0 design review with an external crypto firm

**We are NOT asking today for:**

- Capital commitment (the $1–2M promoter seed is a separate, later decision)
- Public announcement of any kind
- Entity incorporation (that follows counsel review)
- ACIS platform-amendment negotiation with Spatial (that follows the bilateral first)
- Any change to how ActCAD is run today

---

## What "no" looks like — the honest counter

If we do not take the platform path, this is what happens:

- We still ship modern ActCAD in 24 months. **That is a great outcome.**
- We do not build the tenant / licensing / marketplace scaffolding — save ~3–6 engineer-months in P1.
- We keep all upside on ActCAD alone. No dilution risk from external investors later, no complexity of a two-entity structure, no partner-management overhead.
- We forgo the passive-revenue stream. If a competitor (Hexagon, ODA, an Indian tech major) decides in 2–3 years to build the same white-label platform, they own the category — not us.
- Our long-term exit is ActCAD as a product. The platform-multiplier is not available.

**Both paths are respectable.** The platform path adds a second revenue line and a second saleable asset. The single-product path is simpler, with no partner obligations and no second set of books.

---

## The three questions we'd like directors to sit with

1. **Is a ~$3–7M/year, ~75%-margin adjacent business worth the operational complexity** of running a second entity, managing partner relationships, and supporting other vendors' engineering teams? The revenue is real but it is not transformational — the honest question is whether the distraction cost is worth it.

2. **Are we willing to run Jytra + TejasCAD as two clean entities**, with ActCAD paying standard-member fees like any other member? That discipline is what makes the economics legible to members — but it also means real intercompany accounting for a business this size.

3. **Do we want to be the ones who build this** — the India-built CAD platform other vendors run on — accepting that on current numbers it is a **profitable business line, not a venture-scale outcome**, unless we later choose a much bigger distribution model?

**Concept approval today is a yes to exploring these rigorously, not a yes to answering them.**

> **What we are NOT asking you to fund today:** the engine. That is already committed and building. The platform layer is roughly **3–6 engineer-months incremental** on top of work in flight — the marginal cost of keeping this option open is small.

---

## What happens on Monday if the concept is approved

Week 1 (this coming week):
- Legal engagement: entity structure scoping (Delaware C-Corp vs simpler Indian structure — the funding path has changed)
- Trademark clearance opens on TejasCAD + sub-brand family
- Draft of Master Platform License Agreement between Jytra and TejasCAD
- **Phase 0 engineering continues at current pace** — no disruption, no scope change; the tenant-profile discipline gets folded into the build pipeline that already exists

Weeks 2–4:
- Draft of the $1–2M promoter seed structure (equity + convertible notes)
- First soft conversation with 2 candidate members from ActCAD's warm network — no LOI ask, just problem discovery. **We can show them the working viewer.**
- External crypto firm engaged to review encrypted licensing v0 design
- Customer-hardware perf baseline measurement (the exit criterion still owed from Phase 0)
- **Instrument AI inference cost per active user** — the number that sizes the allowance and protects the margin
- Public web-launch decision — first candidate-member conversations may benefit from a controlled public demo

By month 2, we come back to this room with:
- A confirmed entity plan
- A trademark status update
- Notes from the first 2 candidate-member conversations — **live product in hand for the demo, not slides**
- A firm number on the promoter seed
- Customer-hardware perf numbers to close the last Phase 0 exit criterion

**Nothing between now and month 2 is publicly visible. Nothing commits capital or brand until the promoter group approves the next step. Phase 0 engineering keeps shipping through all of it.**

---

<!-- _class: lead -->
<!-- _paginate: false -->

# The ask, in one line

<div class="big" markdown="1">

**Approve TejasCAD as a concept in principle — turn on the pre-work that lets us come back with real answers in eight weeks.**

</div>

`docs/tejascad-story.md` · `docs/tejascad-company-structure.md` · `docs/tejascad-vs-intellicad.md` · `docs/tejascad-licensing-architecture.md` · `docs/tejascad-pitch-deck.md`

Questions?
