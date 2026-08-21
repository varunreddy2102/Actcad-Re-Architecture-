# TejasCAD vs. IntelliCAD — The Case for Switching

> *Working brand: TejasCAD, subject to TM clearance (`docs/brand-shortlist.md` §7). This document is designed to be read by an existing IntelliCAD Consortium (ITC) member vendor's leadership team when deciding whether to migrate. It is intentionally honest about where switching is easy, where it is hard, and where a rational vendor might choose not to switch. Numbers illustrative; specifics reflect public ITC and industry pricing at time of writing.*

---

## 0. Who this is for

- **CEOs / founders of the ~40 ITC member vendors** — progeCAD, CADian (IntelliKorea), CMS IntelliCAD, DoubleCAD, and the long tail of regional / vertical ITC-based products. **Note:** BricsCAD, ZWCAD, and GstarCAD are *not* in this group — each already left IntelliCAD and built their own engine on ODA. They are peers who made this same move, not migration prospects.
- **Vertical ISVs building on IntelliCAD** — MEP, structural, survey, GIS specialists whose product is a shell over IntelliCAD's DWG core.
- **Investors and acquirers evaluating IntelliCAD-based businesses** — anyone doing due diligence needs the honest comparison, not the ITC marketing story.

---

## 1. What the IntelliCAD Consortium is, in one page

The **IntelliCAD Technology Consortium (ITC)**, founded in 1997, is a member-based organization that licenses a shared C++ DWG-native CAD codebase to its ~40 member vendors. Each member pays annual dues (illustrative: $30–100K/year sliding by seat volume) plus per-seat royalties (illustrative: $10–30/seat on a sliding scale), receives the shared source, ships it under their own brand, contributes bug fixes back to the consortium pool, and commits their engineering resources under the consortium license terms.

**What the ITC has done well for thirty years.**

- Shared engineering cost across ~40 vendors, each of whom could not have afforded to build the engine independently.
- Kept the ITC codebase reasonably competitive with AutoCAD on DWG file-format fidelity (usually 6–18 months behind Autodesk's format bumps).
- Enabled a diverse regional / vertical / language-localized ecosystem of AutoCAD alternatives that would not otherwise exist.
- Provided a legal / commercial framework that regional vendors can operate under.

**What the ITC structurally cannot do.**

- **Ship a modern AI layer inside the engine.** The consortium license restricts structural modifications; every member gets the same features at the same time; AI-inside-CAD requires architectural changes that touch the core.
- **Ship cloud-native / web-native versions.** IntelliCAD's C++ codebase and its Windows shell dependencies are not designed for WASM / server-side operation; the consortium has not funded a rewrite.
- **Ship real-time multi-user collaboration.** Requires an op-log architecture and server infrastructure the consortium's engineering model doesn't produce.
- **Move faster than the slowest member's release calendar.** Coordinated releases mean coordinated release schedules.
- **Prevent bug fixes from flowing to a member's direct competitors.** Every fix becomes consortium property.
- **Change fundamental architectural direction** (e.g., adopt a new 3D kernel, replace the render layer, add a plugin marketplace) without a consortium supermajority.

The list of what the ITC *cannot* do is now the list of what modern CAD *must* do. That's the whole problem.

---

## 2. Feature-by-feature comparison

Read this table as "on the day both products ship equivalent 2027 releases." TejasCAD's numbers assume the roadmap in `docs/rearchitecture-plan.md` executes.

| Capability | IntelliCAD (via any member) | TejasCAD |
|---|---|---|
| **DWG read/write fidelity** | ITC-maintained, generally 6–18 months behind Autodesk's format bumps | ODA Drawings SDK, direct membership; ODA typically 0–6 months behind Autodesk |
| **3D kernel** | ACIS, via ITC's consortium-scoped license | **ACIS, via TejasCAD's direct OEM contract** — same round-trip fidelity as AutoCAD (ASM is an ACIS fork); *your* deployment counted at platform level, not per-vendor |
| **Rendering** | ITC-provided, historically Windows-first, per-machine tuning required | ODA Visualize (DirectX 12 / Vulkan / Metal); WebGPU for browser; **no per-machine tuning** at customer sites |
| **Platform** | Windows-first; Mac / Linux ports exist for some members but at reduced parity | **Windows + Mac + Linux + browser + mobile** — same engine, same file formats, same behavior |
| **AI-in-editor** | Structurally blocked | MCP server inside the engine + agent tools + Markup Assist + Smart Blocks + Drawing Health, all with transactional undo |
| **Real-time co-edit** | None | Two-tier op-log + LWW; ships in Phase 2 |
| **BIM / IFC support** | Consortium-limited | ODA IFC + BIM SDKs; native |
| **MCAD file import** (SolidWorks, Inventor, CATIA) | Limited | ODA MCAD translator; direct read |
| **LISP compatibility** | Full (ITC codebase) | 95th percentile at GA; migration tool for the tail |
| **.NET / ObjectARX-compat extensions** | Consortium-approved surface | Opinionated modern surface (no legacy SDS / DIESEL / VBA / COM / ADS); ObjectARX-compatible plugin loader is opt-in |
| **Web extensions** | None | Iframe + OAuth REST, same command surface as native — write once |
| **Plugin marketplace** | None (member-by-member) | Platform-level marketplace, cross-member catalog |
| **Cloud file services** | None | TejasCAD Cloud (optional; member can bring their own) |
| **Encrypted licensing** | Member-built or third-party (Sentinel, Reprise) | Built-in, platform-blind, cryptographically-audited (§`tejascad-licensing-architecture.md`) |
| **Release cadence** | ITC coordinated — annually | Member controls their own release cadence off a rolling platform engine |
| **Bug-fix confidentiality** | Every fix shared with consortium (=competitors) | Fixes are yours unless you contribute them to platform commons |
| **Verticalization** | Member-built alone | Optional co-development with TejasCAD + cross-member royalty (see `tejascad-company-structure.md` §12) |

---

## 3. Architectural differences — why it matters even if features are similar today

At feature-parity in a given year, the *architecture* still tells you which product is on the right side of the trend in the next year. Three architectural differences drive most of the strategic gap:

### 3.1 Shared-source consortium vs first-party engine

**IntelliCAD:** Every member ships the same core. Your differentiation is on the shell, the vertical, the packaging, the channel, the price. Your engine improvements go to your competitors after one release cycle.

**TejasCAD:** You license the platform engine, but you own your shell, your tenant profile, your verticals, your customer relationships, your feature-flag configuration. Nothing you build on top flows back to other members unless you contribute it. **Your engineering investment stays yours.**

### 3.2 Windows-first monolith vs modular multi-platform engine

**IntelliCAD:** The codebase evolved under Windows-first assumptions. Cross-platform ports exist but at reduced parity. Web / mobile essentially not possible without a rewrite. The consortium has never funded that rewrite because the cost-share math is prohibitive.

**TejasCAD:** Modular from the start (10 C++ modules with one C ABI `ui-bridge`). Native shells (Qt 6) and WASM shell consume the same C ABI. Mobile roadmap is a shell over the same engine. **Cross-platform is a first-day property, not a retrofit.**

### 3.3 Command-bus with agent access vs command-dispatcher

**IntelliCAD:** Commands are dispatched to a monolithic engine; there's no clean seam an AI agent can talk to safely. Any AI integration is a bolt-on layer without transaction guarantees. This is why ITC members shipping "AI features" are shipping cloud-side sidecars, not in-engine agents.

**TejasCAD:** The `cmd` module is the **single seam** for command dispatch. Every AI tool call resolves to exactly one transaction in the undo stack. Every command is auditable, revertible, and testable. This is the architectural property that lets AI ship deep instead of shallow.

---

## 4. Commercial comparison

| Cost line | Typical IntelliCAD member | Equivalent for a TejasCAD member |
|---|---|---|
| **Annual consortium / platform fee** | ITC dues: illustrative $30–100K/year sliding by seat volume | TejasCAD member fee: illustrative $100–500K/year sliding by tenant scale (higher — but includes engine + platform + marketplace + licensing infra + AI infra + tenant-profile build pipeline; consortium dues buy only the engine license) |
| **Per-seat / per-deployment engine royalty** | ITC per-seat royalty: illustrative $10–30/seat/year | Platform ACIS pass-through: illustrative per-deployment one-time, at the master-contract rate; no per-seat annual escalation on perpetual base |
| **Kernel royalty (ACIS)** | Embedded in ITC costs; not directly negotiable | Pass-through at cost from TejasCAD's master contract; **the same rate as the platform's own tenants; leveraged buying power vs any single member's own contract** |
| **Feature engineering (AI, cloud, web, mobile)** | Not shipped by ITC — member funds independently at ~$3–8M/year for a modern-features roadmap they can't fully build | Included in the platform fee; member does not fund independently |
| **License / DRM infrastructure** | Third-party (Sentinel HASP, Reprise, etc.): $50–200K/year + integration | Included; encrypted, platform-blind |
| **Marketplace SDK + certification** | Not applicable; no marketplace | Included; 70% dev / 15% platform / 15% tenant split on marketplace sales |

**Rough take:** A regional CAD vendor doing $8M ARR pays ITC roughly $150–300K/year all-in (dues + royalties). A TejasCAD member fee at $250K/year is directly comparable on the engine-license line, and it *replaces* the $3–8M/year that member would need to fund independently to get AI + cloud + web + mobile + marketplace. **The line item that dominates is not the platform fee — it's the R&D the member no longer has to fund alone.**

The catch: TejasCAD ships that R&D as a **platform** — meaning your competitor members also get it. Your differentiation is now on shell, tenant configuration, vertical specialization, channel, and customer relationship. Not on the engine.

**For most ITC members, that trade is very favorable.** The R&D you couldn't fund alone is what's actually competitive-critical; the engine you paid ITC dues for is now a table-stakes commodity.

---

## 5. The three differentiators that matter most to a switching member

### 5.1 Modern engineering — AI, cloud, web from day one

The reason to switch is not that IntelliCAD is broken today. IntelliCAD is fine today. The reason to switch is that the *ceiling* on what IntelliCAD-based products can become is defined by the consortium's coordinated velocity, and every year that ceiling falls further behind AutoCAD / Bricsys / ARES / Onshape. **TejasCAD's ceiling is defined by your own product velocity plus the platform's platform-team output — much higher.**

### 5.2 Fully ready-to-use white-label — you ship a branded product in 90 days

TejasCAD ships a **tenant-profile-driven build pipeline**: a member's brand identity, icons, EULA, command-line prefix, help URLs, feature flags, and license service configuration are captured in a single tenant-profile document. Signed, branded MSI / DMG / DEB / WASM bundles come out of the pipeline. **A new member goes from signed agreement to shipping a branded, working CAD product in 90 days**, versus 18–36 months for an ITC member ramping up on a new codebase or 3–5 years for a brand starting from scratch.

Full engineering seam detail in `docs/platform-strategy.md` §3. The relevant point for a switching member: **you don't burn 18 months on integration.**

### 5.3 Encrypted licensing your customers can trust — architecturally, not by policy

Full spec in `docs/tejascad-licensing-architecture.md`. The one-sentence version: **your customer list, your seat counts, your pricing, your license contents are not visible to TejasCAD, not visible to other members, not visible to attackers who breach TejasCAD, and not producible under legal compulsion of TejasCAD — because the crypto is architected so we cannot see them, not because we promise not to look.** Third-party audited annually. Report published under CC-BY for you to redistribute to your customers.

For an ITC member migrating to TejasCAD, this replaces a third-party DRM vendor (Sentinel / Reprise / custom) with a first-party service that has **stronger** privacy properties than most third-party DRM.

---

## 6. Migration path — how a rational IntelliCAD-based vendor actually switches

The switch is real work. TejasCAD's success depends on making it as low-friction as possible. Standard migration package for an incoming member:

| Phase | Duration | What member does | What TejasCAD does |
|---|---|---|---|
| **0. Evaluate** | 4–6 weeks | Runs their top 20 customer DWGs through TejasCAD engine in a sandboxed build. Compares fidelity, performance, feature coverage. | Provides sandboxed evaluation build with the member's LOGO pre-configured; runs joint testing session |
| **1. Tenant setup** | 4–6 weeks | Finalizes brand assets (icons, EULA, splash, colors, command-line prefix, feature flags, license-server config). Reviews and signs Master License Agreement | Configures tenant profile; provisions license authority (member-held key per §3 of licensing arch); stands up the member's build pipeline |
| **2. Extension port** | 8–16 weeks | Ports member's existing verticalizations and .NET / IRX / LISP customizations to TejasCAD's plugin surface (95% of ITC LISP works unchanged; .NET requires the migration guide) | Provides plugin SDK, sample ports, dedicated migration engineer during this phase |
| **3. Beta rollout** | 4–8 weeks | Beta to 5–15 friendly customers under an NDA | Field-support engineer on standby; expedited engine-level fix path |
| **4. GA + parallel operation** | 6–12 months | Ships new product to new customers under the member's brand; keeps IntelliCAD-based product available to existing customers on the old contract | Standard member support tier |
| **5. IntelliCAD sunset** | 12–24 months later | Announces sunset of IntelliCAD-based product; migrates remaining perpetual customers to TejasCAD-based product on the same brand | Provides migration tools (LISP migration, DWG-check tool, etc.) |

Total elapsed calendar from "signed agreement" to "shipping GA under our brand": **9–18 months for most members**, faster for verticals with simple extension surfaces.

---

## 7. Why a rational IntelliCAD member switches

- The AI / cloud / web / mobile ceiling of the ITC codebase becomes commercially fatal within 24–36 months in most competitive segments.
- The R&D the member would need to fund independently to close that gap is 5–20× the TejasCAD member fee.
- The ITC governance model (coordinated releases, shared bug fixes with competitors, member supermajority for direction changes) becomes actively harmful the moment the member's competitive positioning depends on speed or exclusivity of a feature.
- The encrypted licensing story is a real, salable customer trust upgrade — enterprise / regulated / government customers actively ask for this.
- The verticalized-solutions program (`tejascad-company-structure.md` §12) turns the member's domain IP into a cross-tenant revenue stream, not just a shell-level differentiator.
- **The acquirer optionality is real.** An ITC-based vendor is a hard acquisition target for a strategic — the buyer inherits consortium license terms and a codebase they don't control. A TejasCAD-based vendor is a clean acquisition — the buyer inherits a defined platform license.

---

## 8. Why a rational IntelliCAD member does NOT switch (honest counter-cases)

- **The member's product is deeply forked from IntelliCAD** — significant proprietary modifications to the engine that would need to be re-implemented as TejasCAD plugins. Cost of migration exceeds cost of continuing.
- **The member's customer base is on perpetual-only, low-refresh, in a segment where AI / cloud / web don't matter** (e.g., a highly specialized detailing tool for a stable regulatory environment). "Modern" is not what the customer values.
- **The member is exiting the CAD business** and doesn't want to invest in a migration during runoff.
- **The member sees the IntelliCAD Consortium's shared engineering model as a philosophical fit** and does not want to enter a for-profit platform relationship.
- **The member's shell has irreducibly Windows-first design** that would need a full UI rewrite to run on the multi-platform TejasCAD shell — cost exceeds benefit for their customer base.
- **Trust — the member does not yet trust TejasCAD's operational stability**, licensing-crypto claims, or founder team. Legitimate; addressed only by track record and third-party audits over time.

**TejasCAD's outbound sales approach: acknowledge these counter-cases upfront, focus outreach on the members whose profile doesn't match them.** The ITC member pool is ~40; the switching-fit pool at any moment is probably 8–15. That's the pipeline.

---

## 9. What TejasCAD does NOT do vs IntelliCAD, deliberately

- **We do not offer an IntelliCAD-compatible drop-in replacement.** The engine is different (ODA-direct vs ITC-shared); porting is real work.
- **We do not preserve every ITC extension surface.** SDS / DIESEL / VBA / COM / ADS are not in scope; ObjectARX-compat is opt-in and modernized.
- **We do not commit to matching every ITC release feature-for-feature.** Our roadmap is defined by our platform and members, not by consortium coordination.
- **We do not offer consortium-model shared source.** The engine is licensed, not co-owned. The trade-off is R&D velocity for equity.
- **We do not compete with our members for their customers.** An ITC member typically competes with 40 other ITC members; a TejasCAD member competes only with peers in their same segment, and platform-provided verticalization revenues can align rather than oppose incentives.

---

## 10. Illustrative migration case study — "RegionCAD"

Illustrative composite based on typical ITC member profiles; not a real company. Numbers directional.

### 10.1 The company today

- **Product:** RegionCAD 2027 — an IntelliCAD-based DWG editor + MEP vertical add-on
- **Headquarters:** Barcelona; sales offices in Madrid, Milan, Warsaw, Istanbul
- **Team:** 45 people (12 engineering, 18 sales/support, 15 admin/operations)
- **Customers:** ~18,000 seats across Southern Europe + Turkey + MENA; 60% perpetual, 40% annual subscription
- **ARR:** ~€6.5M
- **Growth rate:** 4% YoY (declining from 12% five years ago)
- **Chief pain points reported by CEO:**
  - Cannot ship any credible AI feature (their #1 lost-deal reason in the last four quarters)
  - Web preview requested by 40% of new prospects, has no path to deliver it
  - MEP vertical increasingly asked for BIM/IFC interoperability, IntelliCAD BIM extension is not usable in production
  - ITC royalties + Sentinel HASP DRM fees + limited-parity Mac port maintenance = €780K/year of "keeping the lights on"

### 10.2 Migration decision timeline

| Month | Milestone | Investment |
|---|---|---|
| **M0** | RegionCAD leadership evaluates TejasCAD; runs top 20 customer DWGs through eval build | ~€25K (evaluation license + 4 weeks of 2 engineers' time) |
| **M2** | Signs Letter of Intent; TejasCAD engineering assigned as migration partner | LOI, no cash commitment |
| **M3** | Master Platform License Agreement signed | Year 1 platform fee €200K committed |
| **M4** | RegionCAD brand tenant profile finalized; License Authority key generated and held by RegionCAD | Included in platform fee |
| **M4-M8** | RegionCAD extension port (MEP vertical, custom LISP libraries, .NET plugins) with 2 TejasCAD migration engineers embedded | €80K in TejasCAD migration-support fees (T&M) |
| **M8-M10** | Closed beta with 12 friendly RegionCAD customers under NDA | RegionCAD field engineering |
| **M11** | **RegionCAD 2028 GA on TejasCAD engine** — sold to new customers under RegionCAD brand; runs alongside legacy RegionCAD 2027 for existing perpetual base | Marketing, packaging, launch |
| **M12** | AI-in-editor features (Markup Assist, Smart Blocks, Drawing Health) shipped as marketing headline for RegionCAD 2028 | Included in platform |
| **M14** | Web viewer + markup shipped to all RegionCAD 2028 customers | Included in platform |
| **M18** | Cloud co-edit shipped | Included in platform |
| **M24** | 60% of new sales are on RegionCAD 2028 (TejasCAD-based); IntelliCAD-based RegionCAD 2027 enters sunset with 24-month runoff plan for perpetual customers | — |
| **M42** | IntelliCAD-based RegionCAD 2027 fully sunset; ITC membership terminated | Savings begin |

### 10.3 Year 1 financial impact (illustrative)

**Costs.**

| Line | Old (IntelliCAD-based) | New (TejasCAD-based) | Delta |
|---|---|---|---|
| ITC dues + per-seat royalty (18K seats) | ~€450K | €0 | −€450K |
| Sentinel HASP DRM + integration | ~€180K | €0 (included) | −€180K |
| Mac port maintenance (external contractor) | ~€150K | €0 (included via TejasCAD Qt shell) | −€150K |
| TejasCAD platform annual fee | — | €200K | +€200K |
| ACIS per-deployment pass-through (new sales only in Y1) | — | ~€30K | +€30K |
| TejasCAD migration-support fees (one-time, Y1 only) | — | €80K | +€80K |
| **Total delta Y1** | | | **−€470K** |

**Revenue.**

| Line | Old | New (Y2 pro forma with AI + web + cloud in market) | Delta |
|---|---|---|---|
| Perpetual license revenue (SE Europe + Turkey + MENA) | €2.6M | €2.9M (10% uplift from AI-headline pricing power) | +€300K |
| Subscription revenue (existing base) | €2.6M | €3.4M (subscription tier + AI/cloud add-ons) | +€800K |
| **New:** Marketplace revenue share (RegionCAD hosts other vendors' MEP plugins in their shell) | €0 | €120K (15% tenant share of $800K GMV) | +€120K |
| **New:** Verticalization royalty (RegionCAD co-develops MEP-Southern-Europe vertical with TejasCAD, gets 45% royalty when TejasCAD Cloud sells it to other tenants' end customers) | €0 | €80K in Y2 | +€80K |
| **Total delta Y2 (steady state)** | | | **+€1.3M revenue + €470K cost savings = €1.77M annual improvement** |

### 10.4 Strategic outcomes over 3 years

- **Lost-deal rate down 60%** — the AI + web feature gap that lost deals in 2027 is closed by 2029
- **Enterprise & regulated customer wins** — the encrypted-licensing crypto-audit report becomes the deciding factor in 3 government-tender wins
- **RegionCAD 2028 becomes a marketplace hub** for European MEP plugins (attracts developers because it aggregates 18K seats + adjacent RegionCAD-family users)
- **RegionCAD's co-developed MEP vertical** ships in three other TejasCAD tenants' shells; the royalty flow becomes a €500K+/year line by Y3
- **Acquirer interest shifts** — where RegionCAD-on-IntelliCAD was a "hard to buy" asset (buyer inherits consortium terms), RegionCAD-on-TejasCAD is a "clean" acquisition candidate at higher multiple

### 10.5 What makes this case study realistic vs optimistic

**Realistic assumptions:**
- 60% conversion of new sales to the new product in Y2 (aggressive but achievable given AI/web/cloud gap they closed)
- 10% pricing uplift on perpetual (typical for feature-differentiating releases)
- €80K T&M migration cost (in line with TejasCAD's cost-recovery model)

**What could make it better than modeled:**
- Faster subscription mix shift as AI/cloud pull customers to subscription
- Winning strategic accounts on encrypted-licensing story (single deal could exceed €500K)
- Marketplace GMV grows faster than modeled if RegionCAD actively promotes plugins

**What could make it worse than modeled:**
- Migration slower than 8 weeks due to deeper .NET dependencies
- ACIS pass-through royalty higher than modeled if new customer volume outpaces
- Some IntelliCAD-era customers refuse to upgrade and remain on runoff longer

**Bottom line:** the illustrative case shows RegionCAD reaches €1.8M annual improvement by Y2 on a Y1 net cost of −€470K (i.e., saves money in year 1) and a one-time €80K migration fee. The switch is cash-flow positive from month 12 onward.

---

## 11. In one paragraph, for the ITC member CEO

If your product depends on AI, cloud, web, mobile, real-time co-edit, plugin ecosystem, or encrypted licensing being part of your value proposition in the next 24–36 months, you will need to invest $3–8M per year of engineering to build any of those on top of IntelliCAD, and the consortium license limits what you're allowed to build anyway. TejasCAD is the alternative to that spend — a platform on ODA + ACIS that ships all of those as first-class features, delivered on a member-license model that costs a fraction of what independent build-out would cost, run under an encrypted licensing infrastructure that is architecturally blind to your customer data. Your migration takes 9–18 months, your brand and customer relationships stay yours, your consortium royalty ends, and your acquirer optionality strengthens. **The question is not whether the modern-CAD wave arrives at your segment — it's whether you cross to it, or wait for it to arrive at your customers first.**
