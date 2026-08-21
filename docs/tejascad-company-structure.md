# TejasCAD — Company Structure, Funding, and Exit Path

> *Working brand: TejasCAD, subject to TM clearance (`docs/brand-shortlist.md` §7). Cap-table percentages, round sizes, valuations, ARR targets, and exit multiples in this document are illustrative modelling numbers, chosen to make the shape of the plan concrete. Real numbers land after (a) the ACIS bilateral term sheet from Spike 1b, (b) the promoter group's actual capital commitment, and (c) legal counsel review of the entity choice. No external commitments should be made against these figures.*

---

## 0. Status

> ⚠️ **SUPERSEDED IN PART — read `docs/tejascad-mgmt-brief.md` first.**
>
> This document was written before the commercial model was grounded in ActCAD's actual IntelliCAD costs and before the 50/50 ownership was confirmed. **§1 (Delaware C-Corp), §3 (the five-round, $172M funding waterfall), §8 (the $1.5–2.5B exit envelope) and §14 (the $100M ARR walk) do not survive that grounding** and are retained only as a record of the earlier thinking.
>
> **Current position:** ~$2.8M ARR base case at Y7, ~$47–54M aggressive enterprise value, a $1–2M promoter seed with an optional $5–10M strategic round, and an entity structure yet to be chosen. §2 (cap table), §5 (IP), §7 (ActCAD carve-out) and §12 (verticalised solutions) remain current.

---


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

Before promoter cash is contributed, the cap table is pure founder equity. This is the "who agreed to what" moment.

**TejasCAD mirrors ActCAD's existing ownership: 50 / 50.** This is not a new negotiation — it is the current partnership carried across.

| Holder | At incorporation | After a 15% ESOP pool |
|---|---|---|
| **ActCAD operating partner** | **50.0%** | **42.5%** |
| **Jytra promoter side** | **50.0%** | **42.5%** |
| ESOP pool (for the dev / QA / dev-support team being hired) | — | 15.0% |
| **Total** | **100.0%** | **100.0%** |

Notes:
- **The 50/50 relationship is preserved through dilution** — an ESOP pool dilutes both sides proportionally, so parity survives.
- The ESOP pool exists because TejasCAD employs the engine team directly (dev, QA, dev support). Those hires need equity; the pool is sized at incorporation rather than negotiated later under pressure.
- **Both sides are principals in both entities.** That makes alignment easy and makes the arm's-length intercompany discipline in §5 and §7 more necessary, not less — nothing enforces it except the agreement itself.
- Vesting: standard 4-year, 1-year cliff for the CTO / CPO. Promoter shares fully vested at inception (they're capitalizing, not employed).
- ESOP pool is **separate** and gets created at the Series A round (§3.2), sized at 12–15%.

---

## 3. Funding waterfall — five rounds over seven years

The whole plan hinges on this walk. Each round's purpose, timing, size, valuation, dilution, and use of funds is spelled out below. Numbers illustrative.

### 3.1 Round 0 — Promoter Seed (year 0 → 1.5)

**Purpose.** Fund the feasibility spike, the ACIS bilateral term sheet, and Phase 1 initial engineering (8-engineer team, 12 months) as scoped in `docs/rearchitecture-plan.md`. Get to a working native Windows beta with ActCAD as the anchor tenant. **No institutional dilution before there is a shipping engine and locked ACIS terms.**

**Source.** The ActCAD promoter group, in personal capacity. Structured as a mix of:
- Founder equity subscription (paid-in against the 85% at par value)
- Interest-bearing promoter loan for the working-capital layer above equity (optional, keeps equity clean if the round is larger than the promoters want to fully equitize)
- Convertible notes with a Series A valuation cap and a 20% discount (**recommended**) — this defers valuation to the Series A investor, which is exactly what a promoter-friend-and-family round should do

**Size.** Illustrative **$4M USD (~₹35 Cr)** across two tranches:
- Tranche 1: $1.5M at incorporation, covers the 6-week feasibility spike (~$0.5M) and month 0–6 engineering ramp (~$1M)
- Tranche 2: $2.5M at month 6, released against spike-pass and ACIS bilateral term sheet signed, covers month 6–18 engineering + ACIS initial-fee + ODA + Qt subscriptions

**Valuation.** Deferred (convertible notes with **valuation cap at $12M pre-money**, 20% discount to Series A). This means a Series A at $75M post gets these notes converting at effectively $12M pre — a ~7× uplift for the promoter capital vs the Series A investor, which is the correct outcome for who took the earliest risk.

**Dilution at conversion.** Once converted at Series A, promoter capital converts to roughly 22–25% additional dilution on the pre-A cap table (numbers depend on exact conversion mechanics; see §3.2).

**Use of funds.**
- Feasibility spike (6 weeks, senior team): $500K
- Engineering payroll (8 engineers, 12 months, blended $80K/engr fully loaded): $640K
- ACIS initial + ODA Sustaining + Qt Commercial: ~$350K
- Cloud infra + AI dev tooling: ~$150K
- Legal (incorporation, ACIS contract, DELA, ODA membership, Qt commercial): ~$200K
- Working capital + contingency: rest

### 3.2 Round 1 — Series A (year 2 → 2.5, after ActCAD-new GA)

**Purpose.** Fund the transition from single-product engine to a **platform business** with 3–5 external member tenants and an opening plugin marketplace. Extend runway 24 months to Series B. Build the platform team (18–22 engineers), the go-to-market motion for member recruitment, the marketplace certification pipeline, and the encrypted licensing infrastructure at production scale.

**Trigger conditions (must be true for the round to open).**
- ACIS bilateral OEM contract signed and shipping in ActCAD-new
- ActCAD-new is in GA or within 3 months of it
- At least **2 candidate members at LOI stage** (per `docs/platform-strategy.md` §8's partner-validation gate)
- Encrypted licensing v1 shipping with third-party crypto audit
- Unit economics on the anchor tenant showing target ARR growth trajectory

**Size.** Illustrative **$18M USD** primary.

**Valuation.** **$57M pre-money / $75M post-money.** Rationale: the CAD-adjacent platform SaaS band at Series A with a shipping product, an anchor tenant of ~30K seats, ODA + ACIS locked in, and 2 external LOIs credibly supports a $60–100M post. Investors at this stage will be either a global venture fund with a deep-tech thesis (Lightspeed, Accel, Bessemer, Insight) or an India-anchored VC that can lead a $18M cheque (Peak XV / Sequoia India, Lightspeed India, Elevation, Nexus). A strategic corporate investor (an ODA member? a Hexagon subsidiary? Autodesk Ventures?) is a possibility but adds channel complexity — decide case by case.

**Dilution.** Series A investor takes **24%** (18/75). Promoter-note conversion adds another ~22% dilution to the pre-A cap table. Combined dilution on Round 0 cap table: ~46%. Post-Series-A cap table (illustrative):

| Holder | % post-A |
|---|---|
| Promoter Group | ~46% |
| Founding execs (CTO / CPO / early hires) | ~9% |
| ESOP pool (freshly created at 15%, unallocated) | ~15% |
| Promoter-note conversion (already in promoter %) | included |
| Series A investors | ~24% |
| Reserved / other | ~6% |
| **Total** | **100%** |

**Use of funds ($18M over 24 months).**
- Engineering team expansion from 12 → 22 headcount ($10.5M / 24mo fully loaded)
- Go-to-market team (VP Partnerships, 3 partner-success engineers, 2 marketing / evangelism): $2.5M
- Platform infrastructure at production scale (multi-tenant license service, marketplace, telemetry, crash-report pipeline, code-signing infra): $1.5M
- ACIS recurring + royalties + ODA + Qt: $1.5M
- Third-party audits (crypto, security, SOC 2): $500K
- Working capital + contingency: $1.5M

### 3.3 Round 2 — Series B (year 4 → 4.5, at 8–10 members)

**Purpose.** Scale internationally, expand member count from 3–5 to 10–15, mature the marketplace, potentially acquire a smaller CAD vendor for member roll-up. This is the "become the segment-leading platform" round.

**Trigger conditions.**
- 5+ external members shipping in production, plus ActCAD
- Marketplace GMV crossing $5M annualized
- ARR at $15–25M with 80%+ gross margin
- Multiple validated member archetypes (regional CAD vendor, vertical ISV, BIM-lite startup) — proves platform-model generality
- Two or more strategic conversations already happening informally with potential acquirers (early signals, not offers)

**Size.** Illustrative **$50M USD** primary + $10M secondary (allows founders and Series A investors to take partial liquidity).

**Valuation.** **$300M pre-money / $350M post-money.** Rationale: at $20M ARR growing 80–100% YoY, with a working marketplace, platform positioning, AI + cloud maturing, the industry comparable is 15–20× forward ARR at Series B for platform SaaS. Investors at this stage: growth funds (Iconiq, Coatue, GA, Meritech), sovereign wealth (GIC, Temasek), or a strategic corporate at a premium (rare — dilutes exit optionality; decline unless the strategic brings clear channel or tech).

**Dilution.** Series B primary takes **14.3%** (50/350). Secondary is a cap-table redistribution, not new dilution.

**Post-Series-B cap table (illustrative).**

| Holder | % post-B |
|---|---|
| Promoter Group | ~39% (after ~7% secondary sale) |
| Founding execs | ~7% (after minor secondary) |
| ESOP (allocated + unallocated) | ~14% |
| Series A investors | ~20% (net of secondary) |
| Series B investors | ~14% |
| Reserved | ~6% |
| **Total** | **100%** |

**Use of funds ($50M).**
- Engineering scale to 30 headcount + platform ops team: $22M / 24 months
- Go-to-market scale: regional sales in India / SEA / EU / LATAM, member success org: $8M
- Marketplace acceleration: developer relations, certification automation, revenue-share ops: $3M
- Optional bolt-on acquisition of a small IntelliCAD-dependent vendor to accelerate member count: $10M budget (may not deploy)
- Working capital, ACIS scale royalty, cloud infra scale: $7M

### 3.4 Round 3 — Pre-Exit Growth Round (year 5.5 → 6, the "valuation-pump" round)

**This is the round the founders make specifically to increase the acquisition price.** It's optional. It runs only if the Series B → M&A conversation is arriving at $500–800M and the case for $1.5–2.5B is credible with 18–24 months more growth.

**Purpose (three distinct mechanisms).**

1. **Price signal.** A $1.0–1.5B post-money round becomes the floor any acquirer must clear. Board and later-round investors would reject a sale below the last round's post-money except at extreme discount, which acquirers know. **The last round's price becomes the negotiating floor.**
2. **Runway to grow into a higher multiple.** The capital funds another 18–24 months of ARR growth. At platform / AI / marketplace forward multiples of 10–15×, every $10M of ARR added compounds into $100–150M of enterprise value. A $100M round at $1.2B post that lets the company grow ARR from $50M to $100M compounds directly into a $1.5–2B exit envelope.
3. **Optionality signal.** A well-funded company with strong momentum doesn't need to sell. Acquirers pay reluctance premiums to founders who could credibly say no. The round funds the option to say no, which is what makes the yes worth more.

**Trigger conditions.**
- ARR at $40–60M growing 60–80% YoY
- Member count at 10+ with strong retention (95%+ net retention)
- Marketplace GMV at $15–30M annualized with growing take-rate
- At least 2 strategic acquirer conversations at informal-offer or IOI stage
- Board consensus that acquiring at current valuation would leave $500M–1.5B on the table vs a 12–18 month growth window

**Size.** Illustrative **$100M USD** primary.

**Valuation.** **$1.1B pre-money / $1.2B post-money.** Rationale: at $50M ARR growing 60–80%, platform positioning, marketplace GMV attached, comparables at this stage justify 20–25× forward — the round underwrites growth to $100M ARR at 15× = $1.5B, giving investors a 25% target return within 24 months of the round closing.

**Dilution.** Growth round takes **8.3%** (100/1200).

**Post-growth-round cap table (illustrative).**

| Holder | % post-growth |
|---|---|
| Promoter Group | ~36% |
| Founding execs | ~6% |
| ESOP | ~13% |
| Series A | ~18% |
| Series B | ~13% |
| Growth round | ~8% |
| Reserved | ~6% |
| **Total** | **100%** |

**Investors at this stage.** Late-stage / crossover funds (Coatue, T. Rowe, Fidelity, D1, DST), or a strategic corporate acquirer taking a minority position as pre-M&A courtship (Autodesk Ventures, Hexagon corporate strategy, Dassault Ventures) — this last is common in industrial SaaS and often *does* signal a subsequent acquisition attempt.

**Use of funds ($100M over 18 months, not 24 — this is a growth sprint into acquisition, not runway).**
- Sales & marketing scale (double the GTM team, add enterprise-tier motion): $35M
- Engineering acceleration on differentiating features (AI, marketplace, mobile, vertical templates): $30M
- International expansion — Japan, Middle East, LATAM member pipelines: $10M
- Optional strategic bolt-on M&A (small vendor acquisitions to add members): $15M
- Working capital, ACIS scaled royalty, cloud: $10M

### 3.5 Round 4 — Exit (year 6.5 → 7)

Not a fundraise. The acquisition or IPO event. Detail in §7 and §8.

---

## 4. Funding waterfall in one table

| Round | Timing | Size | Pre / Post ($M) | Dilution | ARR at close | Purpose |
|---|---|---|---|---|---|---|
| **Promoter Seed** | Y0–Y1.5 | $4M | 12 / 16 (conv. cap) | ~22% at conversion | pre-revenue | Engine spike + ACIS bilateral + Phase 1 build |
| **Series A** | Y2–Y2.5 | $18M | 57 / 75 | 24% | $3–5M | Platform team + first 3 external members + marketplace v1 |
| **Series B** | Y4–Y4.5 | $50M + $10M secondary | 300 / 350 | 14% | $15–25M | International scale to 10–15 members + potentially bolt-on |
| **Growth** | Y5.5–Y6 | $100M | 1,100 / 1,200 | 8% | $40–60M | **Valuation floor + growth-into-multiple + optionality** |
| **Exit** | Y6.5–Y7 | Target $1.5–2.5B | acquisition or IPO | — | $75–150M | Return distribution |

**Total capital raised across the seven years:** ~$172M primary + $10M secondary = ~$182M.

**Founder / promoter ownership walk:** 85% → ~46% (post-A, incl. seed conversion) → ~39% (post-B, incl. minor secondary) → ~36% (post-growth) → ~36% at exit. At a $2B exit and 36% ownership, promoter group returns ~$720M gross before tax.

**Series A investor walk:** buys at $75M post, exits at $2B → 26× on paper, ~$470M gross on the $18M cheque.

**Series B investor walk:** buys at $350M post, exits at $2B → 5.7× on paper.

**Growth-round investor walk:** buys at $1.2B post, exits at $2B → 1.7×. Small return; the whole point of the growth round is to move the exit price up, not to make a big return for these investors. They're pricing in the acquisition premium, not further growth.

---

## 5. IP ownership and cross-entity IP flow

- All engine IP (the C++ core, Rust net/agent, KAL, MCP server, marketplace) is owned by **TejasCAD Inc. (Delaware C-Corp)**.
- Indian Op-Co licenses the IP from the C-Corp under an intercompany agreement at arm's-length rates (transfer pricing).
- Indian Op-Co employees assign all inventions to the Indian Op-Co, which sub-assigns to the C-Corp.
- **ActCAD-the-product IP** stays with Jytra Technology Solutions (existing entity). The new-engine ActCAD is built by TejasCAD Inc. under a **master license agreement between Jytra and TejasCAD Inc.**: Jytra pays TejasCAD's standard member fee + royalty pass-through, just like any other member. This keeps ActCAD's brand and customer relationships inside Jytra while giving it access to the new engine on identical commercial terms as future members.
- The critical clause: **ActCAD-Jytra receives no preferential platform pricing** vs future members. If it did, incoming members would (rightly) demand parity, or the ACIS master contract would treat ActCAD as a special case. Treating ActCAD as tenant zero on identical terms is the discipline that makes the platform business real.

---

## 6. Governance and board

**At incorporation.** Board of 3: two promoter representatives, one founding executive (CTO or CPO). All shareholders sign a shareholders' agreement establishing standard protective provisions.

**Post-Series A (5-person board).** 2 promoter, 1 founding exec, 1 Series A investor, 1 independent (industry veteran — target: former Bricsys / Autodesk / Onshape executive).

**Post-Series B (7-person board).** 2 promoter, 1 founding exec, 1 Series A, 1 Series B, 2 independents.

**Post-Growth round.** Board adds a Growth investor observer (not voting) unless the round is led by a strategic; strategic investors typically demand a board seat.

**Committees.** Audit + Compensation formed at Series A. Nominating & Governance at Series B.

**Founder protective provisions to preserve through Series A.** Board-level: super-majority approval required for sale of company below 2× last round's post-money; issuance of new shares senior to common; hiring/firing of CEO. Standard VC term sheets accept these when the promoter group retains 30%+ ownership and demonstrable operational control.

---

## 7. ActCAD carve-out — how the anchor tenant relationship works

This is the most contract-sensitive relationship in the whole structure and it needs to be right on day 1.

- **Jytra owns ActCAD**, the brand, the customer relationships, the perpetual license base, the reseller channel, the support organization.
- **TejasCAD Inc. owns the engine, the platform, the license infrastructure, the marketplace, the ACIS + ODA + Qt master contracts.**
- The two entities sign a **Master Platform License Agreement**:
  - Jytra becomes a member tenant of TejasCAD from day 1
  - Jytra pays the standard member annual fee and the per-deployment ACIS royalty pass-through, invoiced quarterly
  - Jytra's ActCAD tenant profile is built and signed by TejasCAD's tenant-build pipeline like any other member's
  - Jytra retains full customer and pricing sovereignty
  - Jytra has no board representation on TejasCAD (unless the promoter group is on both boards, which they can be — but Jytra as an entity doesn't get a seat)
  - Master agreement runs the same length and same survival clauses as external member agreements
- **Why this matters at acquisition:** an acquirer buying TejasCAD is buying a platform that has a proven customer in ActCAD-Jytra. If TejasCAD had preferential ActCAD pricing, the ARR would be artificially inflated / deflated depending on how it was structured, and diligence would find it. Arm's-length terms preserve deal cleanliness.
- **What happens to Jytra at TejasCAD exit:** Jytra remains a Jytra. It stays a member tenant of TejasCAD under the master agreement, which survives change-of-control of TejasCAD (standard survival clause). The Jytra shareholders (the same promoter group) can choose to sell Jytra separately, keep it, or merge it into the acquirer if the acquirer wants ActCAD as a brand too. **Both entities have independent exit optionality.**

---

## 8. Exit landscape — five acquirer archetypes

At the $1.5–2.5B valuation envelope and Year 6–7 timing, credible acquirer archetypes:

### 8.1 Large CAD incumbent

**Candidates.** Autodesk, Hexagon (owns Bricsys, Leica, MSC), Dassault Systèmes, PTC (owns Onshape), Bentley Systems, Trimble.

**Strategic rationale.** Buy the SMB / vertical-ISV segment they don't serve well. Absorb the marketplace and the encrypted licensing infrastructure as horizontal capabilities. Take the AI-in-CAD roadmap as a defensive move against each other.

**Realistic multiple.** 8–12× forward ARR for a strategic platform acquisition. At $100M ARR: $800M–$1.2B; at $150M ARR: $1.2–1.8B; premium possible for competitive process.

**Likelihood.** High for Hexagon-Bricsys (already has an SMB CAD line in BricsCAD; TejasCAD adds the SMB long-tail plus a platform play they can't build easily). Medium-high for Autodesk (segment they've ceded; buying it back is defensible). Medium for Dassault / PTC / Bentley.

### 8.2 ODA member consortium buyer

**Rationale.** ODA itself, or a coalition of large ODA members, might acquire TejasCAD to standardize the ODA-based downstream ecosystem. Less about revenue, more about strategic control of the format-alternative space.

**Realistic multiple.** Lower — 6–8× forward. This is a consolidation buyer, not a strategic premium buyer.

**Likelihood.** Low but not zero. Would require unusual coordination.

### 8.3 PE roll-up

**Rationale.** A PE firm building a CAD portfolio (Thoma Bravo, Vista, Insight, Providence). Roll TejasCAD together with 2–4 other engineering-software targets into a larger platform. Financial engineering + operational leverage exit to a strategic at higher multiple in 4–6 years.

**Realistic multiple.** 6–9× forward on a cash-flow-attractive business.

**Likelihood.** Medium-high — PE has been very active in engineering software post-2022.

### 8.4 Strategic industrial vendor entering CAD

**Rationale.** A large industrial or construction-tech vendor (Procore, Autodesk's competitors in ConTech, an SAP / Oracle industrial line) buys CAD as an entry into design tooling that complements their post-design workflows.

**Realistic multiple.** 8–12× — they need the strategic beachhead and will pay for it.

**Likelihood.** Medium. Depends on whether any of them has publicly stated a CAD ambition by year 5.

### 8.5 Indian tech major

**Rationale.** TCS / Infosys / HCL / Wipro / Tech Mahindra / L&T Technology Services / Cyient — one of them acquires TejasCAD as a **product IP asset** they can bundle with services delivery. India-out ambition + owning a global engineering-software platform is strategically consistent with the "India for the world" narrative TejasCAD carries.

**Realistic multiple.** 6–10× — Indian majors are more disciplined on multiples than US strategics but pay a premium for product-IP scarcity.

**Likelihood.** Medium — new-for-2020s pattern (TCS has been on this hunt; L&T Tech acquired Data Patterns' engineering unit; Tech Mahindra has done comparable moves).

### Exit outcome model

Modelling 4 scenarios at Year 7 with $100M ARR and different multiples / competitive dynamics:

| Scenario | ARR | Multiple | Enterprise Value | Promoter proceeds (36%) | Series A proceeds (18%) | Growth-round proceeds (8%) |
|---|---|---|---|---|---|---|
| **Pessimistic** — single acquirer, no auction, pre-growth-round price | $80M | 7× | $560M | $200M | $100M | — (round didn't happen) |
| **Base** — competitive process, one strategic wins | $100M | 12× | $1.2B | $432M | $216M | $96M (@0.8×) |
| **Strong** — growth-round done, competitive process, strategic premium | $130M | 15× | $1.95B | $700M | $350M | $156M (@1.3×) |
| **Optimistic** — bidding war between 2 strategics | $150M | 18× | $2.7B | $970M | $486M | $216M (@1.8×) |

The **growth round** is why "Base" and above are achievable. Without it, the pessimistic case is where 60–70% of platform-SaaS exits at this scale actually land.

---

## 9. Milestones and value gates (what each round unlocks)

| Milestone | Value delivered | Round it enables |
|---|---|---|
| Feasibility spike passes | Engineering risk retired | Continued promoter capital tranche 2 |
| ACIS bilateral signed | Commercial exposure retired | ActCAD-new engineering start |
| ActCAD-new native beta ships | Product risk retired | Series A conversations open |
| ActCAD-new GA + 2 member LOIs | Platform-model validated | Series A closes |
| 3–5 members live + marketplace GMV real | Platform-model proven | Series B closes |
| 10+ members, $50M ARR, marketplace flywheel | Category leadership established | Growth round opens |
| Strategic conversations at IOI | Acquisition tension real | Growth round closes |
| Growth round closes | Valuation floor set | Acquisition negotiation from strength |
| 18–24 months of growth-round execution | ARR at $100–150M | Exit at $1.5–2.5B envelope |

---

## 10. Team structure across the seven years

| Year | Headcount | Composition |
|---|---|---|
| **Y0.5** | 8–10 | 2 promoter + spike engineers (senior) |
| **Y1** | 15 | +engine team + 1 platform-shell engineer + finance/legal contractor |
| **Y2** | 25 | +GTM (VP Partnerships), +marketplace lead, +tenant-build engineer |
| **Y2.5 (post Series A)** | 40 | +Platform ops, +DevRel, +security/crypto, +3 partner-success engineers |
| **Y4 (pre Series B)** | 65 | +regional sales (SEA, EU, LATAM), +ML/AI team, +vertical-templates team |
| **Y4.5 (post Series B)** | 95 | +enterprise-tier GTM, +engineering scale, +customer success at member scale |
| **Y5.5 (pre-growth)** | 130 | +Japan/MEA GTM, +M&A / corp dev lead, +ML platform team |
| **Y6 (post-growth)** | 170 | +growth-sprint hires across GTM and engineering |
| **Y7 (exit)** | 200 | steady state at scale |

---

## 11. Governance discipline that preserves exit value

- **Never blend ActCAD-Jytra P&L with TejasCAD P&L.** Two entities, two sets of books, arm's-length invoices between them. An acquirer needs to see clean platform economics.
- **Never sell a discount to a member that isn't offered to all members.** ARR quality matters more than ARR magnitude at exit.
- **Never take strategic corporate money at Series A.** Locks doors. Series B is the earliest strategic money makes sense, and only from strategics that don't foreclose acquisition options.
- **Never let the ACIS deployment count drift from platform-level attribution.** Every member's deployments are attributed to the platform master contract; ActCAD deployments too. Acquirer diligence will pick this apart.
- **Never take on features that can't be built inside the tenant-agnostic engine.** "Just for ActCAD" features are a moral hazard that ruin the platform's exit multiple.

---

## 12. Verticalised Solutions Program — co-developed verticals, cross-member royalties

Beyond horizontal engine + platform + marketplace, TejasCAD offers a **third revenue line**: **verticalised solutions**, co-developed with a partner member, resold across other members' shells, with a **first-position royalty back to the co-development member every time the vertical is sold — even by a different tenant.**

### 12.1 Why this exists

A regional CAD vendor with two decades of MEP domain expertise, or a structural-engineering ISV with a specialised detailing engine, holds real vertical IP that would take TejasCAD years to build alone. Meanwhile, other members — a BIM-lite startup in a different region, a facilities-management platform, a construction-tech vendor — want to *offer* MEP or structural verticals to their end customers without building them from scratch. **The Verticalised Solutions Program is the marketplace between those two.** TejasCAD supplies the engineering effort and the platform reach; the vertical co-developer supplies the domain IP; the selling member supplies the customer relationship.

### 12.2 How the deal is structured (four-party revenue split, illustrative)

| Party | Contribution | Share of vertical license revenue |
|---|---|---|
| **Co-developing member (vertical IP owner)** | Domain expertise, requirements, testing, first customer proof, ongoing spec authority | **40–50%** |
| **TejasCAD (engineering + platform)** | Co-development engineering hours, integration with platform, certification, distribution across members, revenue-share ops | **30–40%** |
| **Selling member (tenant in whose shell the license was sold)** | Customer relationship, sales, L1/L2 support | **15–25%** |
| **End-customer support surface** | Handled by selling member; escalates to TejasCAD for engine issues, to co-developing member for vertical-logic issues | (built into shares) |

Splits negotiated per vertical. The **guiding principle: the co-developer never falls below 40% for the first three years of a vertical's life**, protecting the incentive to co-build.

### 12.3 Development-support commercial options

TejasCAD offers three co-development engagement models, chosen by the member:

1. **Time-and-materials.** Member pays TejasCAD's engineering rate for hours worked. Vertical IP shared per §13.4. Highest short-term cost to member, lowest ongoing royalty share to TejasCAD (25–30%).
2. **Shared-cost.** TejasCAD absorbs 50–70% of development cost against a higher ongoing royalty share (35–40%). Recommended default for members with a strong vertical thesis.
3. **TejasCAD-underwritten.** TejasCAD absorbs 100% of development cost when it wants a vertical in its catalog badly enough. Vertical IP structured as joint ownership, ongoing royalty share is highest (40–45%) and the co-developing member retains attribution + a **guaranteed minimum royalty floor** regardless of TejasCAD's platform share.

### 12.4 IP ownership

- **Vertical-specific domain IP** (rules, calculation engines, specialised UI, industry-specific data models): **owned by the co-developing member**, licensed exclusively to TejasCAD for redistribution to other members under the program terms.
- **Platform-side integration code** (adapters, plugin scaffolding, engine hooks): owned by TejasCAD, licensed to the vertical.
- **Joint-owned code** (created together, indivisible): joint ownership with mutual license.
- **Written IP schedule per vertical**, exhibit to the master agreement. No ambiguity at exit.

### 12.5 Guardrails so this doesn't scare members off

This is where the design has to be sharp. The obvious member fear: *"If I co-build a vertical with TejasCAD, will TejasCAD (a) start competing with me, (b) let a competitor of mine sell my vertical against my will, or (c) squeeze my royalty over time?"* Contractual answers to each:

1. **No-compete-in-segment for TejasCAD.** For every vertical a member co-develops with TejasCAD, TejasCAD contractually agrees **not to build a competing vertical in the same named segment** (e.g. "MEP-electrical for AEC SMBs in India / SEA") without the co-developing member's consent, for the term of the agreement + 24 months post-termination.
2. **Segment / territory first-refusal for the co-developer.** If a *third-party* co-developer wants to build a vertical in an overlapping segment, the original co-developer gets a 30-day right of first refusal to either extend their vertical's scope or veto (with veto capped — cannot indefinitely block the platform from adding a segment).
3. **Named-competitor exclusion.** The co-developing member can name **up to three specific competitors** in their master agreement. Those competitors are excluded from selling the vertical, no matter what tenant they are on the platform. If TejasCAD ever admits one of those competitors as a member (rare but possible), the vertical is not available in that tenant's shell.
4. **Royalty floor guarantee.** The co-developer's share cannot drop below the contracted percentage for a minimum of five years, regardless of platform economics changes.
5. **Attribution.** The vertical carries an "Original by [Member]" attribution in the About dialog and in the marketplace listing across all tenant shells. Removes only at co-developer's written request.
6. **Data pipeline transparency.** The co-developer sees, on a member portal, real-time counts of vertical deployments and royalty accrual by tenant, so they can audit their own income independently.

### 12.6 Why this makes the platform stronger, not weaker

- **Members contribute IP without losing it.** The co-developed vertical becomes a cross-member revenue stream that outlives any single tenant relationship.
- **The catalog grows without TejasCAD paying full development cost.** Verticals arrive as fast as members co-develop them.
- **Cross-member royalty flow creates a network effect.** A member earning royalties from another member's shell has a positive interest in seeing that member succeed — flips zero-sum competitor dynamics into positive-sum ecosystem dynamics.
- **At exit, the vertical program is a distinct valuation multiplier.** A CAD platform with 8 co-developed verticals and cross-member royalty flow reads as an ecosystem, not just a licensed engine. Comparables: Autodesk's App Store, Shopify's app ecosystem — both add materially to enterprise value.

### 12.7 Illustrative first four verticals to co-develop

Priority order for outbound conversations, based on the biggest gaps in the IntelliCAD-dependent world:

| Vertical | Target co-developer archetype | Why it's the right first four |
|---|---|---|
| **MEP (Mechanical / Electrical / Plumbing)** | Regional CAD vendor with 15+ years MEP focus | Largest AEC vertical demand; strong existing player pool |
| **Structural detailing** | Vertical ISV, likely EU or India | Highest willingness-to-pay per seat; existing tools are aging |
| **Solar / PV layout** | New-generation vertical startup, likely EU / India | Growing 30%+ per year; no dominant CAD platform yet |
| **Survey / civil / land development** | Regional vendor in geo where IntelliCAD is dominant (LATAM, SEA) | Cross-sells to existing IntelliCAD-migrating base |

TejasCAD's own engineering team builds none of these on speculation — they get built the moment a credible co-development member signs.

---

## 13. Risk register and mitigations

Every venture-scale investor will demand this. Ten risks, ranked by expected impact × probability. Each with a named owner (promoter group, board, or platform team) and a monitoring signal.

### 13.1 Category — commercial / go-to-market

| # | Risk | Impact | Prob. | Mitigation | Owner | Monitoring signal |
|---|---|---|---|---|---|---|
| 1 | **Member pipeline stalls at ActCAD** — no external LOIs by month 24 partner-validation gate | Kills the platform business case; company reverts to single-product | Medium | Soft outreach starts month 12, not 24; target 8–10 qualified conversations by month 18; if <2 LOIs, defer platform → Phase 3 and continue as single-product | Board | Number of stage-2+ member conversations tracked monthly |
| 2 | **ACIS refuses platform-amendment terms** at Series A / B stage | Per-member deployment economics break; platform gross margin thins | Medium | Bilateral ACIS contract signed first (§9 of rearch plan); platform amendment negotiated from position of shipping success; fallback = per-member ACIS contracts with platform brokering the terms | Board + Legal | Spike 1b + amendment negotiation status |
| 3 | **Member churn** — an early member leaves at year 2–3 | Reference-account loss; ARR hit; competitive fuel for ITC | Low-Med | Master agreement includes 3-year initial term with renewal; verticalized-solutions program creates cross-member revenue that raises switching cost; standard SaaS retention practices | GTM | Net revenue retention per member cohort |

### 13.2 Category — technical / product

| # | Risk | Impact | Prob. | Mitigation | Owner | Monitoring signal |
|---|---|---|---|---|---|---|
| 4 | **ACIS round-trip fidelity fails on customer DWGs** | Anchor-tenant migration path breaks; every downstream milestone slips | Low | Spike 1a (§9 of rearch plan) tests 50 real customer DWGs before contract; KAL preserves swap option to alternative kernel if needed | Engineering | Spike 1a pass/fail |
| 5 | **inWEB / WebGPU performance below 3× native** in Phase 2 | Web GA slips; competitive positioning weakens | Medium | Spike 2 (§9 of rearch plan); if fail, ship web viewer-only in P2 and defer full editor to P3; native + Qt shells cover the primary market either way | Engineering | Spike 2 result + browser-editor perf benchmarks |
| 6 | **Encrypted-licensing crypto audit finds a design flaw** in Phase 1 | Trust story delayed; member conversations lose the key differentiator | Low | External audit budgeted from day 1; iterate on design pre-GA; second audit at Phase 2 GA | Platform team + external auditor | Audit report cadence |

### 13.3 Category — organizational / execution

| # | Risk | Impact | Prob. | Mitigation | Owner | Monitoring signal |
|---|---|---|---|---|---|---|
| 7 | **Two product lines (IntelliCAD-ActCAD + TejasCAD-based ActCAD) for 24 months** | Support / marketing bandwidth split; customer confusion | Medium-High | Explicit dual-product operating plan in P1; clear customer communication template; sunset date announced only at GA, not up front | Jytra-ActCAD leadership | Support ticket volume, revenue trajectory |
| 8 | **Key-person risk in the founding team** | Company velocity depends on 3–5 specific people | Medium | Standard key-person insurance for promoters + founding execs; documented decision-authority matrix; deep bench at eng-lead level by year 3 | Board | Retention + KPI on-track |
| 9 | **Cadence trap** — TejasCAD becomes its own consortium-slow bottleneck | The exact problem we accuse IntelliCAD of; kills our own value prop | Medium | Rolling engine releases (no fixed member-alignment slots); tenant profile absorbs most member-specific requests without core changes; member roadmap input formalized but non-blocking | Board + Platform team | Engine release velocity vs member request queue |

### 13.4 Category — market / competitive

| # | Risk | Impact | Prob. | Mitigation | Owner | Monitoring signal |
|---|---|---|---|---|---|---|
| 10 | **A competitor announces a competing white-label CAD platform** — Bricsys / Hexagon spins one, or ODA itself does | Category defined by someone with more resources | Low-Medium | First-mover on encrypted licensing + verticalized-solutions program = differentiators competitor can't easily copy; ODA is a partner not competitor (they're a component vendor, not a competing platform); explicit IP + patent strategy on the tenant + licensing seams | Board | Competitive intel quarterly |
| 11 | **Autodesk ships a low-cost AutoCAD LT plus embedded AI** at price parity with SMB CAD | Compresses the SMB / ITC-tier market | Low | Historical Autodesk pattern is to leave SMB SEA / MEA / LATAM to the alternative CAD segment; even if they enter, our members' regional / vertical / language positioning is defensible | GTM | Autodesk SMB pricing / product moves |
| 12 | **Adverse global-macro or India-specific policy shift** (data localization, encryption regulation, ODI restrictions) | Structural friction on entity / operations | Low | Delaware C-Corp holdco + India Op-Co structure absorbs most policy shifts; encryption compliance is easier with our blind-licensing story than with typical DRM | Board + Legal | Policy tracking |

**Overall risk posture:** the platform play is **medium-risk / high-return**. The single largest risk is #1 (member pipeline stalls) — which is why the partner-validation gate at month 24 is a hard decision point in the story arc, not a soft aspiration.

---

## 14. Unit economics assumptions behind the valuation walk

Investor diligence will pressure-test these. Numbers illustrative; refined at Series A pitch.

### 14.1 Per-member economics (steady-state, ~year 3+)

| Line | Illustrative value | Note |
|---|---|---|
| **Average annual member fee** | $250K | Sliding scale: $100K small vertical ISV → $500K large regional CAD vendor |
| **ACIS royalty pass-through per member** | $75K/year | Depends on member's deployment volume; at cost, no margin |
| **Marketplace GMV per member (year 3+)** | $500K | Platform takes 15%, tenant takes 15%, developer takes 70% |
| **Marketplace share to platform per member** | $75K | 15% of $500K GMV |
| **Verticalized-solutions revenue attributed to platform** | $50K (variable) | 30–40% of vertical license revenue when applicable |
| **Total revenue per member (year 3+)** | $450K | Recurring + variable |
| **Platform cost to serve one member** | $85K | 15–20% of revenue; scales sub-linearly with member count |
| **Gross margin per member** | ~81% | Strong SaaS-comparable margin |

### 14.2 Member-count trajectory driving ARR walk

| Year | Members (incl. ActCAD) | ARR ($M) | ARR per member |
|---|---|---|---|
| Y2 (Series A) | 1 anchor + 2 LOI | $3.5 | ActCAD-heavy |
| Y3 | 3 shipping | $10 | $2–4M ActCAD + smaller external |
| Y4 (Series B) | 6–8 shipping | $22 | Mix stabilizing |
| Y5 | 10–12 shipping | $40 | Marketplace revenue material |
| Y6 (Growth) | 13–16 | $60 | Platform steady-state |
| Y7 (Exit) | 15–20 | $100 | Peak platform performance |

**ARR growth pattern:** 40% CAGR Y3→Y7 sustained. Below hypergrowth SaaS but well above typical enterprise-software CAGR — defensible at platform / marketplace multiples.

### 14.3 Sales and marketing efficiency

| Metric | Illustrative target | Comparable |
|---|---|---|
| **Payback period (member acquisition)** | 12–18 months | Typical B2B SaaS platform |
| **LTV / CAC (member)** | 5–8× | Strong; supported by low churn (multi-year master contracts) |
| **Net revenue retention (per member cohort)** | 115–130% | Growth in ACIS pass-through + marketplace share + vertical royalties |
| **Gross churn** | 5–8% annual | Low, given the switching cost after a member has migrated |

### 14.4 Sensitivity — what breaks the model

- **Member count below 6 by Y4:** ARR misses; Series B compressed valuation
- **Net revenue retention below 105%:** implies members not growing on the platform; long-term compounding weakens
- **Marketplace GMV growing < 40% YoY after Y4:** the marketplace flywheel isn't real; valuation multiple drops to pure-SaaS levels (10–12× vs 15–20×)
- **Gross margin below 70%:** cost-to-serve is too high; investor concerns on operating leverage

---

## 15. Open decisions for the promoter group

1. **Entity choice.** Delaware C-Corp holdco confirmed? (§1 recommendation.)
2. **Promoter capital envelope.** Is the illustrative $4M realistic given the promoter group's personal capacity? Larger = more runway before Series A + more retention; smaller = earlier Series A (harder valuation).
3. **Founding execs.** Recruit CTO / CPO externally, or promote from ActCAD-Jytra? Trade-off between institutional CAD knowledge (Jytra hires) and platform / venture-scaling experience (external).
4. **Board composition.** Which two promoters represent the group?
5. **ActCAD master agreement terms.** Standard-member terms or slight preferential? (§7 recommendation: standard, for cap-table cleanliness at exit.)
6. **Timing of Series A opening.** Immediately at ActCAD-new GA, or delay 6 months to get first member LOIs signed?
7. **Growth-round trigger.** What ARR / member-count / competitive-tension threshold triggers the growth round? Predefine so the decision isn't made under acquisition-approach pressure.
8. **Exit preferences.** Rank the five acquirer archetypes by promoter preference — some will care more about strategic buyer identity than pure price.
