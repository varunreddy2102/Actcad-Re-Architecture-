---
marp: true
theme: default
paginate: true
size: 16:9
header: 'TejasCAD · Platform CAD, Built in India, For the World'
footer: 'Confidential · Working brand pending TM clearance'
style: |
  section { font-size: 22px; }
  h1 { color: #1a3a6c; }
  h2 { color: #2d5fa7; border-bottom: 2px solid #2d5fa7; padding-bottom: 4px; }
  table { font-size: 0.80em; }
  blockquote { border-left: 4px solid #2d5fa7; color: #444; }
  strong { color: #1a3a6c; }
---

<!-- _class: lead -->
<!-- _paginate: false -->

# TejasCAD

### The white-label CAD platform. Built in India. For the world.

**A strategic briefing for management, prospective members, and eventual investors.**

Working brand — TM clearance pending (`docs/brand-shortlist.md` §7). Numbers illustrative — locked before external use.

Companion documents: `docs/tejascad-story.md`, `docs/tejascad-company-structure.md`, `docs/tejascad-licensing-architecture.md`, `docs/tejascad-vs-intellicad.md`, `docs/rearchitecture-plan.md`, `docs/platform-strategy.md`.

---

## The one-slide version

We are building a **white-label CAD platform** — the same modern engine ActCAD-new will run on, licensed to other regional CAD vendors, vertical ISVs, and BIM-lite startups as their own branded product.

- **Engine on ODA + ACIS + Qt + WASM.** Modern, cross-platform, AI-native from day one, cloud co-edit at GA.
- **Ready-to-ship white-label front end.** A member goes from signed agreement to shipping their brand in **90 days**, not 3 years.
- **Encrypted, platform-blind licensing.** Members serve their customers through our infrastructure; we architecturally cannot see the data.
- **Plugin marketplace + verticalized-solutions program.** Cross-member revenue flows, not zero-sum competition.
- **From India, for the world.** Founded and initially funded by the current ActCAD promoters in personal capacity.
- **Five funding rounds over seven years** to a $1.5–2.5B acquisition envelope.

---

## Why now — three curves converging

1. **AI is inside the editor.** Autodesk Revit 2027 MCP. Fusion 2026 MCP. ARES A3 agent. BricsCAD AI. In three years, "no AI in CAD" reads the way "no undo" would read today. The IntelliCAD-based segment is structurally locked out.
2. **Cloud + web is the default assumption of every new drafter.** Onshape, AutoCAD Web, ARES Kudo. A Windows-only single-user DWG editor is being aged out one graduating class at a time.
3. **BIM is moving down into the SMB base.** IFC and lightweight parametric are being asked for by the same customers who buy ActCAD-tier products. IntelliCAD-based products cannot deliver at parity.

> **The lower half of the CAD market — the ~40 IntelliCAD-Consortium vendors, the vertical ISVs, the SMB long tail — is on the wrong side of all three curves.** That's the market we power.

---

## The market we serve (segmentation)

| Segment | Who they are | Count | Their problem |
|---|---|---|---|
| **Regional / national CAD vendors on IntelliCAD** | progeCAD, CADian, CMS IntelliCAD, DoubleCAD, + long tail of regional / vertical ITC products | ~40 vendors | Consortium ceiling on AI / cloud / web / mobile; fixes go to competitors |
| **Vertical ISVs building on shared CAD engines** | MEP, structural, electrical, survey, GIS, shipbuilding, curtain-wall specialists | ~200 globally in TAM | No clean engine license option; forced onto AutoCAD SDK or DIY |
| **BIM-lite startups** | New AEC-tech companies building lightweight BIM for SMBs | ~40 companies globally | Need CAD foundation + IFC + AI; can't afford to build |
| **SMB end customers** (indirect — reached via members) | Drafters in India / SEA / MEA / LATAM / EU SMBs | ~15M+ potential end seats | Under-served by AutoCAD-tier pricing; deserve modern features |

**Not on this list — peers, not prospects:** BricsCAD, ZWCAD, GstarCAD each already left IntelliCAD and went ODA-direct. ZWCAD and GstarCAD compete with ActCAD in India today. We do not white-label to them; that they made this move and won is validation of the direction, not a sales lead.

**TAM.** ~$1.2B in ITC-tier vendor revenue + $400M vertical ISV + $150M BIM-lite. **SAM (our member-reachable slice).** ~$500M-worth of member businesses could migrate over 5 years. **SOM (5-year target).** 10-15 members representing $60–120M of platform revenue.

---

## The insight — value has moved

For thirty years, the value in the CAD-alternative market was **owning the DWG parser**. That is no longer true — ODA is now a reliable, direct-license path. The value has moved to four layers, in this order:

1. **AI layer** — MCP servers, transactional agents, drawing-health tools
2. **Cloud / co-edit** — real-time multi-user editing, mobile/browser parity
3. **Plugin ecosystem** — marketplace of extensions that developers earn from
4. **White-label / brand-partner layer** — the same engine shipped under many brands

> **No one has built #4 as a first-class product.** Every CAD engine today is either single-brand (AutoCAD, BricsCAD, ARES) or consortium (IntelliCAD). The white-label-as-a-real-product model is the market gap. TejasCAD builds all four.

---

## Architecture in one picture

**10-module C++ core.** Engine is tenant-agnostic; tenant identity lives in the shell only.

| Module | Role |
|---|---|
| **`db`** | Drawing database. Only mutator. Emits typed op-stream. |
| **`geom`** | Kernel Abstraction Layer over ACIS. No ACIS types in public headers. |
| **`render`** | Visualize backends — DirectX 12 / Vulkan / Metal / WebGPU. |
| **`cmd`** | Command bus. The single seam AI + plugins + scripts talk to. |
| **`script`** | LISP, Python, JS. Everything routes through `cmd`, never `db`. |
| **`plugin`** | API-parity native + WASM plugin host. |
| **`net`** | Sync, document service, telemetry (Rust). |
| **`agent`** | MCP server, tool catalog, permission scoping (Rust). |
| **`platform`** | File I/O, fonts, printer, GPU surface. Only module with `#ifdef`. |
| **`ui-bridge`** | One C ABI. Qt shell + WASM shell + tenant shells all consume it. |

Full spec: `docs/rearchitecture-plan.md` §3.

---

## The three differentiators

**1. Modern — AI, cloud, web from day one.** MCP server inside the engine, transactional undo per agent tool call, browser editor in Phase 2, real-time co-edit at GA. Nothing in the IntelliCAD-based segment ships this credibly.

**2. Ready-to-ship white-label.** Tenant-profile-driven build pipeline. A member's brand, icons, EULA, command-line prefix, feature flags, and license-server configuration are captured in a single JSON + asset bundle. Signed, branded MSI / DMG / DEB / WASM bundles come out of CI. **New member goes from signed agreement to shipping their brand in 90 days.**

**3. Encrypted, platform-blind licensing.** Members serve their own customers through TejasCAD's licensing infrastructure — perpetual, subscription, floating, node-locked. **We architecturally cannot see the data.** Not a policy — a cryptographic property. Third-party audited annually.

> **These three, together, are what no competitor offers. Any one of them alone is a category-defining differentiator.**

---

## Differentiator #1 in detail — AI

**The commitment no competitor has made:** every AI tool call resolves to **exactly one transaction in the host undo stack.**

- **AI as a tool (Phase 1).** Markup Assist (PDF redline → DWG edits), Smart Blocks (block detection + conversion), Drawing Health (layer cleanup, dimstyle normalization). Inline, deterministic, undoable.
- **MCP server (Phase 1–2).** Local MCP (host running, agent commands inside host transaction) + remote MCP data server (cloud, read-only DWG queries). Mirrors Autodesk Fusion 2026 pattern. Works with Claude, Cursor, ChatGPT out of the box.
- **Generative CAD (Phase 3, conditional).** Only when editable parametric round-trip is proven. Hypar's lesson: text-to-BIM via chat alone was the wrong abstraction.

**Why this matters commercially:** every member's brand ships AI-inside-CAD on day one. This closes the #1 lost-deal reason for IntelliCAD-based competitors in the 2027–2029 window.

---

## Differentiator #2 in detail — white-label ready-to-ship

**Tenant profile = one JSON + one asset bundle → one signed, branded product.**

What a member configures:
- Brand identity (name, icons, splash, EULA, about-box copy)
- Command-line prefix (e.g. `ACAD-` → `MYCAD-`)
- File-format identity (custom DXF app-id, "open with" handler)
- Update channel (per-tenant signed manifest)
- Feature flags (which verticals / plugins / kernels / AI tools)
- License endpoint (per-tenant license-server URL)
- Help + docs URLs, AI assistant identity, marketplace-tenant-share percentage

**A new tenant is a build configuration, not a code change.** The engine never sees `if (tenant == ...)`. Full spec: `docs/platform-strategy.md` §3.

---

## Differentiator #3 in detail — encrypted, platform-blind licensing

Four-level cryptographic key hierarchy. **The critical property: TejasCAD does not hold the keys to see member customer data.**

- **Platform Root** — offline HSM; signs member LA public keys
- **Member License Authority (LA) key** — **held by the member.** TejasCAD generates on onboarding, transmits under one-time envelope crypto, deletes its copy. LA private key never lives in our infrastructure after handoff.
- **Per-license symmetric keys** — wrapped for end-user's specific machine; only that machine can decrypt
- **Aggregate attestation key** — member signs quarterly deployment counts for ACIS royalty; we see numbers, not identities

**What we can see:** aggregate deployment counters (per member, per quarter), infrastructure health metrics. **What we cannot see:** customer identities, seat counts per customer, pricing, license contents, drawing data. Not by policy. By math.

Third-party audit report published under CC-BY; members redistribute to their own customers as proof. Full spec: `docs/tejascad-licensing-architecture.md`.

---

## The plain-English trust story (for CEOs, lawyers, procurement)

**Q: Can TejasCAD read our customer list?** No. Customer identity never enters our systems. Members hold their own License Authority key.

**Q: Can TejasCAD read our customers' license files?** No. Payloads are encrypted with keys we don't hold.

**Q: If TejasCAD is breached, is our data in the breach?** No. Attacker gets ciphertext + aggregate counters. Ciphertext is useless without the member's key.

**Q: If TejasCAD gets a subpoena for our customer data, what happens?** We hand over what we hold — ciphertext. Which is useless. We cannot break the crypto for the government any more than for an attacker.

**Q: If TejasCAD terminates our membership, do our customers still work?** Yes. LA is yours. License artifacts are cryptographically valid independent of TejasCAD's continuity. Documented "TejasCAD-independent operations" playbook ships with the SDK.

**Q: Can we prove this to our customers?** Yes. Annual third-party crypto audit report, published under CC-BY for redistribution.

---

## Comparison — TejasCAD vs IntelliCAD

| Capability | IntelliCAD (via any member) | TejasCAD |
|---|---|---|
| AI-in-editor | Structurally blocked | MCP server + transactional undo |
| Real-time co-edit | None | Two-tier op-log + LWW at GA |
| Cross-platform | Windows-first | Windows + Mac + Linux + browser + mobile |
| BIM / IFC | Consortium-limited | ODA IFC + BIM native |
| Plugin marketplace | None | Platform-level cross-member catalog |
| Cloud file services | None | TejasCAD Cloud (optional) |
| Encrypted licensing | Third-party (Sentinel, Reprise) | Built-in, platform-blind, audited |
| Release cadence | Consortium-coordinated | Member-controlled off rolling engine |
| Bug fixes | Shared with competitors | Yours unless contributed |
| Verticalization | Member builds alone | Co-development + cross-member royalty |
| DWG fidelity | 6–18 mo behind AutoCAD | ODA direct, 0–6 mo behind |

Full analysis: `docs/tejascad-vs-intellicad.md`. Case study: `docs/tejascad-vs-intellicad.md` §10.

---

## Case study — "RegionCAD" (illustrative)

Composite ITC member: 18K seats across Southern Europe + MENA, €6.5M ARR, IntelliCAD-based.

**Year 1 delta (illustrative):**

| Cost line | Old | New | Delta |
|---|---|---|---|
| ITC dues + royalties | ~€450K | €0 | −€450K |
| Sentinel DRM | ~€180K | €0 (included) | −€180K |
| Mac port maintenance | ~€150K | €0 (included) | −€150K |
| TejasCAD platform fee | — | €200K | +€200K |
| ACIS pass-through (new sales only) | — | ~€30K | +€30K |
| Migration T&M (one-time) | — | €80K | +€80K |
| **Year 1 total** | | | **−€470K net saving** |

**Year 2 pro-forma with AI + web + cloud in market:** +€1.3M revenue uplift (10% pricing on perpetual, subscription tier growth, marketplace share + verticalization royalty). **Total Y2 improvement ~€1.77M annually.**

Full case study: `docs/tejascad-vs-intellicad.md` §10.

---

## Verticalised Solutions Program — cross-member royalties

Beyond horizontal engine + platform + marketplace, a **third revenue line**: verticals co-developed with a partner member, resold across other members' shells, with a **first-position royalty back to the co-developer whenever the vertical sells — even from another tenant.**

**Revenue split (illustrative):**
- Co-developing member (vertical IP owner): **40–50%**
- TejasCAD (engineering + platform): **30–40%**
- Selling member (tenant hosting the sale): **15–25%**

**Guardrails so this doesn't scare members off:**
- TejasCAD no-compete in the co-developer's named segment
- Co-developer holds 30-day right of first refusal on overlapping verticals
- Named-competitor exclusion (co-developer names up to 3 competitors who cannot buy)
- Royalty floor guarantee for 5 years
- Attribution across all tenant shells

**First four verticals to co-develop:** MEP, structural detailing, solar/PV layout, survey/civil. TejasCAD builds none on speculation — each waits for the right co-developer.

Full spec: `docs/tejascad-company-structure.md` §12.

---

## Business model — three revenue lines

**1. Annual membership fee.** ~$100–500K/member/year, sliding scale by tenant size. Funds platform engineering steady-state, tenant-profile pipeline, L3 support, marketplace listing rights.

**2. ACIS per-deployment royalty pass-through.** At cost. Members see a single line item; platform absorbs the master-contract negotiation. Zero platform margin — this is a pass-through, not a profit center.

**3. Marketplace + verticalization revenue.**
- Marketplace: 70% developer / 15% platform / 15% tenant on GMV
- Verticalization: platform takes 30–40% of vertical license revenue

**Illustrative per-member steady-state economics (Year 3+):**

| Line | ~$/year per member |
|---|---|
| Membership fee | $250K |
| ACIS pass-through | $75K (at cost) |
| Marketplace share (platform's 15%) | $75K on $500K GMV |
| Vertical royalty (variable) | ~$50K |
| **Revenue per member** | **~$450K** |
| Cost to serve | $85K |
| **Gross margin** | **~81%** |

---

## Company structure — Delaware C-Corp + Indian Op-Co

**Recommended entity:** TejasCAD Inc. (Delaware C-Corp holdco) with 100%-owned TejasCAD Technologies Pvt Ltd (India). Rationale: institutional Series A / B / growth-round investors overwhelmingly prefer Delaware; flipping later costs months of runway and 3–5% in legal + tax. India Op-Co employs the team, holds Indian contracts, assigns IP to the C-Corp.

**Founding cap table (illustrative, at incorporation):**

| Holder | % |
|---|---|
| Promoter Group (ActCAD founders, personal capacity) | 85.0% |
| Founding CTO / engineering lead | 5.0% |
| Founding CPO / product lead | 5.0% |
| Reserve for early operating hires | 5.0% |

**Founder-promoter allocation reflects that promoters are both (a) the seed capital source AND (b) the strategic underwriter of the anchor tenant (ActCAD).** No competitor can start a white-label CAD platform with a working revenue-generating brand as tenant zero.

Full detail: `docs/tejascad-company-structure.md` §2.

---

## ActCAD carve-out — how the anchor tenant relationship works

Both entities preserve independent optionality.

- **Jytra Technology Solutions** continues to own the ActCAD brand, customer relationships, perpetual license base, reseller channel, support org.
- **TejasCAD Inc.** owns the engine, platform, license infrastructure, marketplace, master ACIS / ODA / Qt contracts.
- **Master Platform License Agreement between Jytra and TejasCAD Inc.:** Jytra becomes a member tenant from day 1. Standard member terms, standard fees, standard royalty pass-through. **No preferential pricing — that keeps the cap table clean for later members and for exit diligence.**
- At TejasCAD exit, Jytra remains as-is: still a Jytra, still a member tenant, master agreement survives change-of-control. **Jytra shareholders (same promoter group) can sell Jytra separately, keep it, or merge it into the acquirer.**

Full detail: `docs/tejascad-company-structure.md` §7.

---

## Five-round funding waterfall over 7 years

Every round has a specific purpose. Numbers illustrative.

| Round | Timing | Size | Pre / Post ($M) | ARR at close | Purpose |
|---|---|---|---|---|---|
| **Promoter Seed** | Y0–Y1.5 | $4M | 12 / 16 (conv. cap) | pre-revenue | Spike + ACIS bilateral + P1 build |
| **Series A** | Y2–Y2.5 | $18M | 57 / 75 | $3–5M | Platform team + first 3 external members |
| **Series B** | Y4–Y4.5 | $50M + $10M secondary | 300 / 350 | $15–25M | International scale to 10–15 members |
| **Growth (pre-exit)** | Y5.5–Y6 | $100M | 1,100 / 1,200 | $40–60M | **Valuation floor + growth-into-multiple + optionality** |
| **Exit** | Y6.5–Y7 | Target $1.5–2.5B | acquisition or IPO | $75–150M | Return distribution |

**Total capital raised over 7 years:** ~$172M primary + $10M secondary = ~$182M.

Full detail: `docs/tejascad-company-structure.md` §3.

---

## Round 0 — Promoter Seed (illustrative $4M)

**Source: ActCAD promoter group, in personal capacity.**

- Structured as **founder equity + convertible notes with Series A valuation cap of $12M pre-money and 20% discount** — defers valuation to the Series A investor, which is exactly what a promoter friends-and-family round should do.
- **Two tranches:** $1.5M at incorporation (spike + M0–6 ramp); $2.5M at M6 (released against spike-pass + ACIS bilateral term sheet signed).
- **No institutional dilution before there is a shipping engine and locked ACIS terms.** This is the discipline that preserves 46% promoter ownership at Series A, versus ~25–30% if seed had been institutional.

**Uses (illustrative $4M):**
- Feasibility spike: $500K
- Engineering payroll (8 engineers, 12 months): $640K
- ACIS initial + ODA + Qt subscriptions: ~$350K
- Cloud + AI dev tooling: ~$150K
- Legal / contract work (ACIS, ODA, Qt): ~$200K
- Working capital + contingency: rest

---

## The pre-exit growth round — the specific move to lift acquisition value

**Timing:** Year 5.5–6, only if the acquisition conversation would otherwise arrive at $500–800M and the case for $1.5–2.5B is credible with 18–24 months more growth.

**Size (illustrative):** $100M at $1.2B post-money valuation.

**Three distinct mechanisms:**

1. **Price signal.** $1.2B post becomes the floor any acquirer must clear. Board and later-round investors reject sale below last-round-post except at extreme discount.
2. **Runway to grow into a higher multiple.** $100M funds 18–24 months of ARR growth. At platform / AI / marketplace forward multiples of 10–15×, every $10M ARR added = $100–150M enterprise value. A $50M → $100M ARR walk maps to $500M → $1.5B EV.
3. **Optionality signal.** Well-funded companies with strong momentum negotiate from optionality, not necessity. Acquirers pay reluctance premiums to founders who could credibly say no.

**Investors at this stage:** late-stage crossover (Coatue, T. Rowe, Fidelity, D1, DST) or strategic corporate acquirer taking a minority position as pre-M&A courtship (Autodesk Ventures, Hexagon corporate strategy, Dassault Ventures).

---

## Exit landscape — five acquirer archetypes

| Archetype | Candidates | Realistic multiple | Likelihood |
|---|---|---|---|
| **Large CAD incumbent** | Autodesk, Hexagon-Bricsys, Dassault, PTC, Bentley, Trimble | 8–12× forward ARR | High for Hexagon-Bricsys; medium-high for Autodesk |
| **ODA member consortium buyer** | ODA itself or coalition of large ODA members | 6–8× | Low but not zero |
| **PE roll-up** | Thoma Bravo, Vista, Insight, Providence | 6–9× | Medium-high |
| **Strategic industrial entering CAD** | Procore, SAP/Oracle industrial, ConTech incumbents | 8–12× | Medium |
| **Indian tech major** | TCS / Infosys / HCL / Wipro / L&T Tech / Cyient | 6–10× | Medium (new-for-2020s pattern) |

**Exit outcome scenarios (illustrative, at Y7):**

| Scenario | ARR | Multiple | Enterprise Value | Promoter proceeds (~36%) |
|---|---|---|---|---|
| Pessimistic | $80M | 7× | $560M | $200M |
| **Base** | $100M | 12× | $1.2B | $432M |
| **Strong (post-growth round)** | $130M | 15× | $1.95B | $700M |
| Optimistic (bidding war) | $150M | 18× | $2.7B | $970M |

---

## Product roadmap — 3 years to platform GA

| Phase | Months | Headline deliverables |
|---|---|---|
| **Phase 1: Foundation** | 0–12 | Engine on ODA. Full DWG fidelity. 2D drafting. Native Windows beta to willing-customer cohort. Browser viewer in parallel. LISP runtime. AI-as-tool features shipped. MCP server skeleton. **Tenant-profile layer built from day 1.** Encrypted licensing v1. |
| **Phase 2: Production v1** | 12–24 | Mac / Linux Qt at parity. Browser becomes full editor. Light 3D via ACIS through KAL. **Cloud co-edit on 2D.** LISP 95th percentile + migration tool. **AI assistant GA.** ActCAD-new GA at month 24. Soft outreach to 2–3 candidate members. |
| **Phase 2→3 gate** | Month 24 | **Partner-validation gate.** ≥2 members at LOI? → pursue platform amendment with Spatial + open marketplace + open to outside members. |
| **Phase 3: Parity-or-better + platform** | 24–36 | Full 3D + BIM-lite (IFC). MEP / Electrical / Structural verticals reshipped as plugins. Mobile shells. **First 3 external members onboarded. Marketplace opens.** IntelliCAD ActCAD sunset. |

Full detail: `docs/rearchitecture-plan.md` §5, `docs/platform-strategy.md` §9.

---

## Feasibility spike — 4–6 weeks before Phase 1 kickoff

**7 pass/fail items, decision-forcing.** Items 1, 2, 3, 5 are deal-breakers if they fail.

| # | What | Pass criterion |
|---|---|---|
| 1 | **ACIS round-trip vs AutoCAD** on 50 customer DWGs | <0.001 unit drift, booleans ≥98% pass, identical handle set |
| 1b | **ACIS commercial scoping under NDA** with Spatial | Term sheet: module list, royalty model, WASM/Linux/macOS SKUs, source escrow, DELA |
| 2 | inWEB perf vs native Visualize | inWEB ≤ 3× slower than native |
| 3 | `ui-bridge` C ABI driving Qt + WASM from one `cmd` | One source of truth, no shell-specific branching |
| 4 | Customer LISP script on minimal interpreter | Visually identical to current ActCAD |
| 5 | MCP-driven "draw a 3-bed apartment plan" | Agent-shaped commands, no corruption |
| 6 | Qt Commercial multi-year quote | Signed, target 15–35% below first quote |
| 7 | 2-user op-log co-edit on real drawing | Op-stream design supports replication |

**If 1, 2, 3, or 5 fail, the plan changes before kickoff — not at the Phase-2 boundary.**

---

## Modeled cost envelopes (salary excluded — full picture in `rearchitecture-plan.md` §15)

| Phase | Engineers | Stack + tools + cloud |
|---|---|---|
| **Phase 1** (0–12) | 8 | **~$383K** (incl. ~$300K ACIS initial + recurring) |
| **Phase 2** (12–24) | 20 | **~$449K** (incl. ~$210K ACIS recurring + royalty at GA) |
| **Phase 3** (24–36) | 30 | **~$1.26M** (incl. ~$660K ACIS recurring + royalty at scale) |

**In scope:** ODA Sustaining ($7.5K → $4.5K renewal, unlimited seats + Web/SaaS rights), Qt Commercial (~$4K/dev/yr), **ACIS commercial OEM** (initial + 15–20% maintenance + per-deployment royalty + module fees + DELA), VS Code primary + 2–3 VS Enterprise seats for perf devs, AI dev tooling (~$50/dev/mo), AWS infra, Clerk + Stripe.

**ACIS is the dominant line.** §15.1.1 per-deployment ask locks the model at SMB scale.

---

## Risk register (top 5 of 12; full list `company-structure.md` §13)

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| 1 | **Member pipeline stalls at ActCAD** — no external LOIs by month 24 | Kills platform business case | Soft outreach starts M12; ≥2 LOIs by M18 targeted; if not, defer platform → Phase 3 |
| 2 | **ACIS refuses platform-amendment** at Series A/B | Per-member economics break | Bilateral first, amendment from position of shipping success; fallback = per-member with platform-brokered terms |
| 3 | **ACIS round-trip fails on customer DWGs** | Anchor migration path breaks | Spike 1a; KAL preserves kernel-swap option |
| 4 | **Two product lines for 24 months** | Support / marketing bandwidth split | Dual-product operating plan in P1; explicit customer communication template |
| 5 | **Cadence trap re-emerges under TejasCAD** — we become the new slow consortium | Kills our own value prop | Rolling engine releases; tenant profile absorbs member-specific requests; formalized but non-blocking member input |

Full 12-risk register: `docs/tejascad-company-structure.md` §13.

---

## Go-to-market — the anchor-tenant-first sequence

Sales motion for member recruitment, phased against product maturity:

| Phase | GTM motion | Target output |
|---|---|---|
| **Spike + P1 M0-M6** | No outbound. Anchor-tenant-only. Build the product. | ActCAD engineering + platform build |
| **P1 M6–M12** | Founder / promoter-led warm intros to ~15 target member vendors from ActCAD's existing network in India / SEA / MEA. **Discovery conversations only.** | 15+ discovery meetings; 5–8 members intrigued |
| **P2 M12–M18** | **VP Partnerships hired.** Structured outreach to top 25 ITC-tier vendors + top 30 vertical ISVs. Sandboxed evaluation-build offer at zero cost. | 8+ evaluations running; 3–5 LOI-stage conversations |
| **P2 M18–M24** | Convert LOI conversations to signed Master License Agreements gated on ActCAD-new GA proof. | 2–3 signed members by month 24 (partner-validation gate) |
| **P3 M24–M36** | First 3 members onboard sequentially (one per quarter). Marketplace opens. **Second wave of 5–7 members** approached. | 5–8 shipping members by month 36 |
| **Y4+** | Land-and-expand: existing members co-develop verticals, new members added quarterly at steady 3–4/year | 12–15 members by Y5 |

---

## Team plan (headcount walk)

| Year | Headcount | Composition |
|---|---|---|
| Y0.5 | 8–10 | 2 promoter + senior spike engineers |
| Y1 | 15 | +engine team, +platform-shell engineer, +finance/legal contractor |
| Y2 | 25 | +VP Partnerships, +marketplace lead, +tenant-build engineer |
| **Y2.5 (Series A)** | 40 | +platform ops, +DevRel, +security/crypto, +3 partner-success engineers |
| Y4 (pre Series B) | 65 | +regional sales (SEA, EU, LATAM), +ML/AI, +vertical templates |
| **Y4.5 (Series B)** | 95 | +enterprise-tier GTM, +engineering scale, +customer success |
| Y5.5 | 130 | +Japan/MEA GTM, +M&A/corp dev, +ML platform |
| **Y6 (Growth)** | 170 | +growth-sprint hires across GTM + engineering |
| Y7 (Exit) | 200 | Steady state |

---

## Founders and team (placeholder — to be filled by promoter group)

- **[Founder 1]** — [role, ActCAD tenure, prior]. Leads platform strategy + investor relations.
- **[Founder 2]** — [role, tenure]. Leads product + member success.
- **CTO / engineering lead** — TBD (external hire vs internal promotion; decision at incorporation)
- **CPO / product lead** — TBD
- **VP Partnerships** — TBD (hired between M9 and M12)
- **Advisory board (post-incorporation targets):**
  - A former Bricsys / ARES / Onshape senior product / engineering leader
  - A CAD industry corp-dev veteran (M&A pattern-matching)
  - A crypto / security recognized expert (validation of the platform-blind licensing story)
  - A large-scale open ecosystem operator (Shopify, Atlassian, Autodesk App Store perspective)

**The credibility founding team gets from day 1:** working relationships with ODA, Spatial, Qt, and the ActCAD channel partners — not from a pitch, from history.

---

## The "from India, for the world" positioning

**Why this framing matters commercially, not just narratively:**

- Anchor tenant is Indian (ActCAD); founders and initial capital are Indian; founding engineering is India-anchored — the story is honest.
- The Atmanirbhar Bharat / Vishwa Guru moment gives Indian institutional capital + Indian tech-major acquirers a mission-aligned reason to engage.
- International member vendors and end customers read Indian engineering pedigree as *credibility* in 2026 (post-UPI, post-Chandrayaan-3, post-Jio) in a way that would have been harder in 2016.
- The name **Tejas** carries the story: HAL Tejas LCA is the living Atmanirbhar Bharat engineering symbol, and it is now being **exported** — Malaysia signed 2023, Argentina + Egypt in pipeline. "India-engineered, world-flown" is not a slogan; it's a track record we associate with.

Full brand rationale: `docs/brand-shortlist.md`.

---

## Milestones and value gates (what each round unlocks)

| Milestone | Value delivered | Round it enables |
|---|---|---|
| Feasibility spike passes | Engineering risk retired | Promoter capital tranche 2 |
| ACIS bilateral signed | Commercial exposure retired | ActCAD-new engineering start |
| Native beta ships | Product risk retired | Series A conversations open |
| GA + 2 member LOIs | Platform model validated | Series A closes |
| 3–5 members live + marketplace GMV | Platform model proven | Series B closes |
| 10+ members, $50M ARR, marketplace flywheel | Category leadership established | Growth round opens |
| Strategic conversations at IOI | Acquisition tension real | Growth round closes |
| Growth round closes | Valuation floor set | Acquisition from strength |
| 18–24 months of growth-round execution | ARR at $100–150M | Exit at $1.5–2.5B envelope |

---

## What we deliberately don't do

- **No IntelliCAD-compat drop-in replacement.** Different engine, real port work.
- **No consortium-model shared source.** Engine is licensed, not co-owned.
- **No preferential pricing for ActCAD-Jytra.** Standard-member terms, always.
- **No competing with our members** on their branded CAD sales.
- **No reading member customer data.** Architecturally, not by policy.
- **No SDS / DIESEL / VBA / COM / ADS** legacy compatibility.
- **No institutional funding before shipping engine + ACIS bilateral.**
- **No two products forever.** IntelliCAD-based ActCAD sunsets in Phase 3.
- **No chat-in-canvas as primary AI UX** — Hypar's lesson.
- **No selling to segments where we compete with a member** without member consent.

Each "don't" closes a door a competitor keeps open and pays for.

---

## What we're asking for today

**From the promoter group — decisions:**

1. Approve incorporation of TejasCAD Inc. (Delaware) + TejasCAD Technologies Pvt Ltd (India) per entity choice in `company-structure.md` §1
2. Commit Round-0 promoter capital envelope — illustrative $4M in two tranches
3. Approve founding execs (internal promotion vs external recruit)
4. Approve Master Platform License Agreement with Jytra at standard-member terms
5. Approve the feasibility spike (6 weeks, senior team) and the ACIS Spike 1b outreach to Spatial

**From this session — no external commitment.** Internal decisions, no press, no announcements. Feasibility spike runs first; go / no-go on the full plan after spike data.

**From prospective members — as engagements open (Y1+):**

- Sandboxed evaluation build with your brand pre-configured
- 8-week no-commitment technical evaluation
- Standard Master License Agreement + tenant profile onboarding

---

## Companion documents (reading order)

| Order | Document | Purpose |
|---|---|---|
| 1 | `docs/tejascad-story.md` | The narrative — why we exist, who we serve |
| 2 | This deck | Discussion-starter for management + investors + members |
| 3 | `docs/tejascad-vs-intellicad.md` | Head-to-head with the incumbent + case study |
| 4 | `docs/tejascad-company-structure.md` | Entity, cap table, funding waterfall, exit landscape, risk register, unit economics |
| 5 | `docs/tejascad-licensing-architecture.md` | Encrypted-licensing spec — the trust artifact |
| 6 | `docs/platform-strategy.md` | Platform seams, tenant-profile layer, marketplace |
| 7 | `docs/rearchitecture-plan.md` | Engineering plan (unchanged — 17 sections) |
| 8 | `docs/brand-shortlist.md` | Working brand rationale + TM path |

---

<!-- _class: lead -->
<!-- _paginate: false -->

# TejasCAD

### The CAD platform. Built in India. For the world.

**Questions?**

`docs/tejascad-story.md` · `docs/tejascad-pitch-deck.md`

Working brand — TM clearance pending.
