---
marp: true
theme: default
paginate: true
size: 16:9
header: 'TejasCAD · Directors briefing · Concept approval in principle'
footer: 'Confidential · Working brand pending TM clearance · Illustrative numbers'
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

*Working brand TejasCAD pending TM clearance. Numbers illustrative — this briefing asks for concept approval, not a spend commitment.*

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

Six weeks in, ~207 commits, versioning aligned to ActCAD's own (26.1 → 26.3.7 delivered today, fixing 5 team-reported bugs).

| Area | Status |
|---|---|
| **DWG/DXF open** | Real customer files open in the browser on WASM + ODA inWEB. Both backends live. |
| **Measurement + snap + count** | Full 14-mode AutoCAD/ActCAD osnap suite; count + CSV/Excel export; quick calc. |
| **Rendering perf** | 250K entities at 61 fps via region rendering + culling; regen 17× faster; instant zoom-extents. |
| **3D** | Visualize camera bound — orbit, standard views, live 3D ViewCube shipping. Layouts + paper space viewports work end-to-end. |
| **Beyond scope** | DWG↔DWG + PDF revision comparison, color plotting, batch print, print-to-PDF, sidecar markup overlays. |
| **Distribution** | Tauri Windows MSI + `setup.exe` shipping today. macOS CI build green. Android Tauri prototype exists. |
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

**They already pay six-figure sums per year for a foundation they don't love.** We can offer them a better one.

---

## Building for ActCAD vs building for the world — the two paths, side by side

| Dimension | Build for ActCAD only | Build as a platform (ActCAD = anchor tenant) |
|---|---|---|
| Engine work | Same | Same |
| Ship date | ~24 months to GA | Same 24 months to GA + tenant-profile discipline in P1 |
| Extra P1 engineering cost | Baseline | **~3–6 engineer-months** for the tenant layer done properly |
| Revenue model | ActCAD license + AI/cloud subs | Same for ActCAD **plus** member fees + royalty pass-through + marketplace share + vertical co-development royalties |
| Passive-revenue upside | Zero | **Real** — every member added is annuity income from work we already did |
| Exit optionality | ActCAD sold as a product | TejasCAD platform sold as a category — a materially bigger valuation multiple |
| Risk if platform play fails | — | We still shipped a great ActCAD. Nothing wasted. |

> **The platform path costs a small P1 discipline premium and unlocks a much larger long-term option.** If members don't come, we've still shipped ActCAD. If they do, we own a category.

---

## What a member actually pays today — our own bill as the benchmark

We are an IntelliCAD member. **We know exactly what this market pays, because we pay it.**

| What ActCAD pays today | Amount |
|---|---|
| ITC membership + extras | **~$100K / year** |
| Per-seat royalty to ITC | **$0** — membership is royalty-free at the ITC level |
| Component royalties (ACIS and a few others) | **$15–20 per sale** |

**This is the number that disciplines our entire pricing model.** No ITC-tier vendor is going to pay us $250K/year for an engine when they pay ~$100K today — however much better ours is. Our fee has to land in the same neighbourhood and win on what it includes, not on price.

**So the model is:**

- **Platform fee $100–150K/year** — comparable to what they pay ITC now, but it includes AI, cloud, web, mobile, the marketplace, and the encrypted licensing stack, none of which ITC can deliver at any price
- **Component royalties passed straight through at cost** — the same $15–20/sale they already pay, no markup, no margin for us
- **Marketplace and vertical royalties on top** — these grow slowly and only become material once the ecosystem is real

> **We are not trying to extract more per member than ITC does. We're trying to be worth the same money and deliver a product they cannot otherwise get.** That's a much easier sale, and it's the honest one.

---

## The passive-revenue picture — realistic

Per-member economics at maturity, priced against the benchmark above:

| Line | Per member / year |
|---|---|
| Platform fee (blended: ~$60K small ISV → ~$200K large vendor) | ~$120K |
| Component royalties (ACIS etc.) | **$0 to us** — passed through at cost |
| Marketplace share (15% of ~$230K GMV, once mature) | ~$35K |
| Vertical co-development royalty (variable, when applicable) | ~$15K |
| **Recurring revenue per member** | **~$170K** |
| Platform cost to serve one additional member | ~$50K |
| **Gross margin per additional member** | **~70%** |

**What that compounds to:**

| Members (incl. ActCAD) | Recurring platform revenue | Contribution at ~70% margin |
|---|---|---|
| 3 | ~$450K/yr | ~$315K/yr |
| 6 | ~$1.0M/yr | ~$700K/yr |
| 12 | ~$2.0M/yr | ~$1.4M/yr |
| 20 | ~$3.4M/yr | ~$2.4M/yr |

> **This is on top of ActCAD's own revenue** — which we keep, in full, inside Jytra. And it comes from engineering we are funding anyway.

---

## What this could become — conservative, base, aggressive

Two variables drive everything: **how many members we sign**, and **what each is worth per year** (fee + marketplace + vertical royalties, maturing from ~$120K early to ~$220K for a large, long-tenured member).

| | **Conservative** | **Base** | **Aggressive** |
|---|---|---|---|
| Members by Y7 (incl. ActCAD) | 5 | 12 | 20 |
| Avg revenue per member at Y7 | ~$130K | ~$170K | ~$220K |
| **Platform ARR at Y7** | **~$650K** | **~$2.0M** | **~$4.4M** |
| Gross margin | ~65% | ~70% | ~72% |
| **Annual profit contribution** | **~$420K** | **~$1.4M** | **~$3.2M** |
| Indicative exit multiple | — | 5–6× | 7–8× |
| **Indicative enterprise value** | not saleable at this scale | **~$10–12M** | **~$30–35M** |
| What we'd likely do | Don't sell. Run it — it still pays for itself | Sell, or keep compounding | Competitive process; genuine strategic interest |

**Read this honestly: this is a profitable adjacent business line, not a venture-scale company.** Even the aggressive case is a ~$4M ARR business worth ~$35M. That is a very good outcome for a few engineer-months of incremental work on an engine we are building anyway — and a poor outcome for anyone expecting a unicorn.

> **What would it take to be materially bigger?** Not this model. Twenty members at $220K caps out around $35M. Getting to $20M+ ARR needs **~100 members** (the full global long tail, a decade of partner management) or selling **direct to end users** alongside our members — a bigger, more competitive, quite different business. **That is a question to open deliberately later, not something to assume today.**

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
- Corporate counsel scoping of the Delaware C-Corp + India Op-Co entity structure
- Non-binding scoping conversation with 3–5 candidate member CEOs (all in ActCAD's existing warm network)
- Encrypted licensing v0 design review with an external crypto firm

**We are NOT asking today for:**

- Capital commitment (that comes with the tranche-1 promoter seed decision, separately)
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

**Both paths are respectable.** The platform path has a bigger ceiling and a bigger canvas. The single-product path has less complexity and preserves optionality-of-scale for another day.

---

## The three questions we'd like directors to sit with

1. **Is a ~$2–4M/year, ~70%-margin adjacent business worth the operational complexity** of running a second entity, managing partner relationships, and supporting other vendors' engineering teams? The revenue is real but it is not transformational — the honest question is whether the distraction cost is worth it.

2. **Are we willing to run Jytra + TejasCAD as two clean entities**, with ActCAD paying standard-member fees like any other member? That discipline is what makes the economics legible to members — but it also means real intercompany accounting for a business this size.

3. **Do we want to be the ones who build this** — the India-built CAD platform other vendors run on — accepting that on current numbers it is a **profitable business line, not a venture-scale outcome**, unless we later choose a much bigger distribution model?

**Concept approval today is a yes to exploring these rigorously, not a yes to answering them.**

> **What we are NOT asking you to fund today:** the engine. That is already committed and building. The platform layer is roughly **3–6 engineer-months incremental** on top of work in flight — the marginal cost of keeping this option open is small.

---

## What happens on Monday if the concept is approved

Week 1 (this coming week):
- Legal engagement: Delaware C-Corp + India Op-Co scoping
- Trademark clearance opens on TejasCAD + sub-brand family
- Draft of Master Platform License Agreement between Jytra and TejasCAD
- **Phase 0 engineering continues at current pace** — no disruption, no scope change; the tenant-profile discipline gets folded into the build pipeline that already exists

Weeks 2–4:
- Draft of promoter capital tranche-1 structure (equity + convertible notes)
- First soft conversation with 2 candidate members from ActCAD's warm network — no LOI ask, just problem discovery. **We can show them the working viewer.**
- External crypto firm engaged to review encrypted licensing v0 design
- Customer-hardware perf baseline measurement (the exit criterion still owed from Phase 0)
- Public web-launch decision — first candidate-member conversations may benefit from a controlled public demo

By month 2, we come back to this room with:
- A confirmed entity plan
- A trademark status update
- Notes from the first 2 candidate-member conversations — **live product in hand for the demo, not slides**
- A firm number on tranche-1 promoter capital
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
