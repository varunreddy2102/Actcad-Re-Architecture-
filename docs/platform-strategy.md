# White-Label Platform Strategy — Owning the Product, Membership + Rev-Share with Brand Partners

## 0. Status

**Concept stage. No partner signed beyond the anchor tenant.** This document proposes a strategic superset of the ActCAD re-architecture: instead of building a single-branded successor to ActCAD, build the same engine, tooling, and APIs as a **white-label CAD platform** that ActCAD ships under (as the anchor tenant) and that other CAD or vertical-tool vendors can license under their own brand for a membership fee plus a per-deployment royalty / revenue share.

Companion to — **not a replacement for** — `docs/rearchitecture-plan.md`. The engine, module decomposition, kernel choice (ACIS), feasibility spike, and three-phase delivery in that document all stand unchanged. What this document adds is the commercial and operational wrapper that turns the engine into a multi-tenant product, plus the architectural seams the wrapper needs.

**Decision rule for this document.** The pivot is worth doing only if §8 (the chicken-and-egg problem) can be closed with a credible partner pipeline by the end of Phase 1. If it cannot, fold the white-label optionality back into Phase 3 and ship ActCAD-branded first.

---

## 1. The pivot in one paragraph

Today's plan builds a first-party engine on ODA Drawings, the ACIS kernel, Qt 6 desktop, and a WASM browser shell, shipped as the next-generation ActCAD product. The same engine — same 10 modules, same Kernel Abstraction Layer, same `ui-bridge` C ABI, same command bus, same MCP server, same plugin host — can be made **tenant-aware** and licensed to other CAD-adjacent vendors who want a modern DWG-native foundation without building one. **Jytra (or a new subsidiary brand) owns the platform IP, the license servers, the signing keys, the plugin marketplace, and the ACIS OEM contract.** ActCAD becomes the anchor tenant: a brand-licensee of the platform that pays a member fee plus a royalty pass-through on its own seats. Other members — regional CAD vendors stuck on IntelliCAD, vertical AEC / MEP / structural / electrical tool vendors, BIM-lite startups — sign the same agreement and ship their own branded shell on the same engine.

---

## 2. What changes vs the existing plan, what doesn't

| Area | Existing plan | Under white-label | Delta |
|---|---|---|---|
| **Engine, modules, KAL, kernel** | ODA + ACIS, 10-module C++ core, MCP server | Identical | None |
| **Feasibility spike (§9)** | 7 pass/fail items including ACIS round-trip + Spike 1b commercial scoping | Identical, **but Spike 1b widens** to ask Spatial for a platform-level OEM contract covering multiple brand-licensees at one royalty schedule | Wider negotiation, same engineering risk |
| **Shell** | One ActCAD-branded shell, Qt + WASM | Generic platform shell with a **tenant profile** layer: theming, icons, splash, command-line prefix, doc strings, registry keys, installer brand, update channel, telemetry tenant | New: tenant-profile layer, ~3–6 engineer-months over baseline |
| **License server** | Per-product license keys | **Per-tenant license keys with platform-owned key authority.** Member tenants get their own license-server endpoint URL but share root validation | New: multi-tenant licensing service |
| **Code signing** | One Authenticode cert (ActCAD) | **Platform signs the engine binaries; tenants countersign their shell assets.** Verified-publisher chain trusts the platform root | New: dual-sign workflow |
| **Plugin marketplace** | 15% rev share over a $5K free tier, ActCAD-only catalog | **Platform-level catalog.** Plugins target the engine API; tenant shells choose which plugins are surfaced. Plugins built once, sold across all member brands. | Bigger: marketplace as a product line, not a side feature |
| **Pricing model** | ActCAD perpetual + AI/cloud subscription | ActCAD pricing unchanged. Members set their own end-user pricing. Platform takes membership fee + per-deployment royalty + marketplace cut. | New: B2B pricing for members |
| **Brand and legal** | Jytra builds, ActCAD sells | Jytra (or new subsidiary) owns the platform IP. ActCAD and other members sign membership + IP-license + rev-share agreements. | New: legal entity / contracts work |
| **Engineering org** | One product team | One **platform team**, plus a small ActCAD-tenant team that integrates and ships the anchor brand | Org change, not a headcount change |
| **Phasing** | P1 native Windows beta → P2 GA → P3 sunset old ActCAD | Identical for the engine. **White-label opens to outside members at the start of P3** when the product is GA and ACIS terms are proven. | New: a §9 partner-validation gate at end of P2 |

> **The architecture is already 80% there.** The 10-module core, the `ui-bridge` C ABI, the API-parity plugin surface across native and web, the MCP server, the op-stream — these are exactly the seams a white-label platform exposes. The pivot is mostly a commercial layer plus a tenant-profile shell layer; it is not a rewrite.

---

## 3. White-label seams — what tenancy actually requires

Most of the new work lives **outside** the engine, in a new shell-layer abstraction and a new license / billing service. The engine itself remains tenant-agnostic.

### 3.1 Tenant profile — what each member configures

| Surface | What the tenant configures | Where it lives |
|---|---|---|
| **Brand identity** | Product name, icons (app, file, doc), splash, about-box copy, EULA text, support URLs | Tenant profile JSON, baked at installer build |
| **Command-line prefix** | LISP / script command namespace (e.g. `ACAD-` vs `BCAD-`), AutoCAD-compat command aliases on/off | Tenant profile, read by `cmd` module at startup |
| **File-format identity** | Custom DXF app-id, registered file extension, "open with" handler name | Installer + tenant profile |
| **Update channel** | Per-tenant update server URL, signed channel manifest | Platform-owned update service, per-tenant endpoints |
| **Telemetry tenant** | Tenant ID stamped on every telemetry event; tenant-scoped dashboard | Platform telemetry pipeline (Snowplow / similar) |
| **Feature flags** | Which plugins, kernels, AI tools are surfaced; which verticals are visible (MEP / Electrical / Civil / BIM-lite) | Tenant profile + entitlements service |
| **License endpoint** | Per-tenant license-server URL; tenants choose perpetual / subscription / hybrid; platform validates with root key | Multi-tenant license service |
| **Help and docs** | Per-tenant help URL; in-app help can be tenant-branded | Tenant profile, web-hosted |
| **AI agent identity** | Per-tenant assistant name, system prompt prefix, model routing | `agent` module reads tenant profile |
| **Pricing display** | Tenants set their own end-user pricing; platform never displays Jytra branding to end users | Tenant shell |

A tenant profile is a single JSON document plus an asset bundle (icons, EULA, splash). The platform's installer builder takes a tenant profile and produces a signed, branded MSI / DMG / DEB / WASM bundle in CI. **Adding a new tenant should be a build configuration, not a code change.**

### 3.2 What the engine never sees

To keep the engine clean and the per-tenant work cheap, the engine modules (`db`, `geom`, `render`, `cmd`, `script`, `plugin`, `net`, `agent`, `platform`, `ui-bridge`) **must not know which tenant they are running under.** Tenant identity is read once at startup by the shell, fed into the command-line prefix table, the update service, the license check, and the telemetry context, then forgotten. If a future engineer ever writes `if (tenant == "actcad")` inside an engine module, that is a bug.

This is the same discipline that keeps the engine portable across Qt + WASM: tenants are just another axis of the same configuration story.

### 3.3 What gets harder, honestly

- **QA matrix.** Today QA runs against one shell. Under white-label, QA runs against the engine plus N tenant profiles. The good news: tenant profiles are data, so smoke tests can iterate them in CI. The bad news: tenant-specific bug reports will look different ("crash in `XYZCAD`" vs "crash in the engine"), and triage will need a tenant-de-identification step that maps tenant reports back to engine repro cases.
- **Support boundary.** Members handle their own L1 / L2. The platform handles L3 (engine bugs, kernel bugs, plugin SDK). The contract has to spell this out so platform support doesn't get pulled into tenant-specific drafting questions.
- **Plugin compatibility.** Plugins are API-versioned against the engine. Tenants ship the engine version they qualified against; the marketplace shows which plugins work with which engine version. Same problem AutoCAD has solved many times; we copy that solution rather than invent.
- **Crash reports and PII.** Crash dumps from one tenant must never leak entity content or filenames to another tenant or to the platform without consent. Platform crash-report pipeline needs per-tenant key encryption at submission.

---

## 4. Member economics — membership + royalty pass-through + rev-share

The price stack a member pays the platform has three components. Each is illustrative; real numbers come out of the partner-pipeline conversations in §8.

### 4.1 Component A — Annual membership

A flat per-year fee that buys:

- Engine binaries and updates
- ODA + ACIS pass-through licensing under the platform's master contract
- Tenant-profile build pipeline and installer signing
- L3 engineering support, SLA defined
- Plugin SDK and marketplace listing rights
- Per-tenant license-server and update endpoints

This is the line that funds platform engineering steady-state. Order of magnitude — and this is illustrative until partner conversations close — **$100K–$500K per member per year**, tiered by tenant scale (small vertical-tool vendor vs regional CAD vendor with 50K+ seats). ActCAD-the-anchor would internally amortize this as a transfer cost.

### 4.2 Component B — Per-deployment royalty pass-through

ACIS is per-deployment under the §15.1.1 negotiating ask in the existing plan. Under white-label, the platform's master ACIS contract counts deployments across all member tenants. The platform passes that cost through to each member proportional to their tenant-stamped deployments. Members see a single line item; the platform absorbs the negotiation complexity.

ODA Sustaining is already unlimited seats; no per-deployment math there. Qt Commercial is per-developer-seat, paid by the platform once, not passed through.

### 4.3 Component C — Marketplace rev-share

Marketplace plugins are sold through the platform's storefront, in the platform's branded UI within each tenant shell (with tenant skinning for the chrome). Default split:

- **70% to developer**
- **15% to platform** (storefront, billing, hosting, certification, fraud)
- **15% to the tenant** in whose shell the plugin was sold

That last 15% is the line that gives tenants a real reason to surface marketplace plugins to their users. The existing plan's 15% / $5K-free-tier policy for marketplace plugins stands; under white-label, the 15% becomes 15%-platform + 15%-tenant, with the developer keeping 70%.

### 4.4 What the platform's P&L looks like at illustrative steady-state

Numbers are illustrative — partner pipeline closes them. The point is the shape, not the magnitude.

| Line | At 1 anchor (ActCAD only) | At 3 members | At 8 members |
|---|---|---|---|
| Memberships | $200K | $700K | $2.0M |
| Royalty pass-through (margin only) | ~$20K | ~$80K | ~$250K |
| Marketplace share (15% of $X plugin GMV) | low | medium | meaningful |
| **Platform gross contribution** | **~$220K** | **~$800K** | **~$2.3M+** |
| Platform team headcount needed | 12–15 | 18–22 | 25–30 |

> The platform business is **only viable at 3+ members.** With one anchor it is a cost center wearing a fancy abstraction; with eight it is a real software business. Sizing is in §8.

---

## 5. ACIS as a platform-level OEM contract

This is the single largest commercial dependency of the pivot. It widens, rather than replaces, the §9 Spike 1b conversation in the existing plan.

### 5.1 The asks that change

| §15.1.1 ask (existing plan, single-product) | §5 ask (this document, platform) |
|---|---|
| Per-deployment royalty, one-time, machine-fingerprint based, same-machine reinstalls excluded | **Same model**, but deployments aggregated across all member tenants under one master agreement |
| Volume tiers at 5K / 25K / 100K cumulative deployments with steep decay | Volume tiers at platform level: **aggregated deployments across all members count toward the next tier** — this is the key concession |
| Annual minimum floor target $25K–$50K | Annual minimum floor at the platform level, **not per member** — protects sub-scale members |
| Carve-outs: trials, education, internal QA excluded | Same carve-outs, plus: **sub-licensing rights to member tenants under the platform's master agreement** (DELA addendum required) |
| Source escrow, change-of-control protection | Same plus: **platform's sub-license to tenants survives change-of-control of Spatial / Dassault** |

### 5.2 Why Spatial should say yes (the pitch)

- ACIS volume grows faster under a platform model than under a single product. Spatial is upside-aligned, not exposed.
- Each member is independently underwriting deployments; platform aggregates risk and admin.
- One master contract, one set of audits, one DELA, one negotiation per renewal — lower transaction cost on Spatial's side too.
- Platform commits to a public "ACIS Inside" trust mark in member products (analogous to Intel Inside), giving Spatial brand reach into vertical CAD it would not otherwise touch.

### 5.3 Why Spatial might say no (and what we do then)

- **They price every member as a separate OEM.** This kills the economics. Mitigation: hold the negotiation as "platform-only" — walk away from a per-member contract structure. The §15.1.1 fallback (per-deployment for ActCAD only) remains available; the platform pivot then defers to Phase 3.
- **They demand a minimum committed royalty that only ActCAD volume can backstop.** Counter with a "ramp" — commit ActCAD-equivalent floor in year 1, escalating with member additions, gated on platform reaching N members by year 3.
- **They demand publicly disclosed member list / audit rights into member tenants.** Counter with platform-mediated audits and aggregated reporting; members are not parties to the Spatial contract.

> **Operationally:** the Spike 1b conversation in the existing plan happens **first as a single-product ACIS contract.** Only after that closes do we open the platform-level conversation as an **amendment**, leveraging the now-existing relationship. Trying to negotiate platform terms before establishing the bilateral terms is a worse position.

---

## 6. Plugin marketplace as a first-class product line

Under the existing plan, the marketplace is a side-feature with a 15% rev share over a $5K free tier. Under white-label, the marketplace is **a product line of its own** — the largest source of platform revenue growth past year 3.

### 6.1 What changes

- **One catalog, many storefronts.** A plugin developer writes once against the engine API. Each tenant shell surfaces the catalog, skinned to the tenant brand. Tenants can promote / hide specific plugins (e.g. ActCAD hides a competing MEP vertical plugin if it conflicts with ActCAD's own MEP offering).
- **Certification is platform-level.** Plugins pass platform certification once, sell across all tenants. Tenants do not run their own certification — that would not scale.
- **Verified-publisher chain.** Platform issues publisher certs; tenants trust the platform root. Same trust model AutoCAD has for ObjectARX publishers, but cross-tenant.
- **API parity remains the engineering discipline.** The same internal command / query API plugins call in-process natively is what web extensions call over OAuth REST. White-label adds: the API is **also** the integration surface tenants use for their own first-party features, so we eat our own dogfood.

### 6.2 What this means for the §13 marketplace policy in the existing plan

The 15% rev share over a $5K/year free tier from §13.4 of the rearchitecture plan stays, but with a wrinkle: under white-label, the split becomes 70% developer / 15% platform / 15% tenant (the tenant in whose shell the sale happened). The free-tier protection for small developers is unchanged.

### 6.3 Vertical opportunity

The vertical-tool vendor segment (small MEP / Electrical / Structural / Survey / GIS software vendors) is the highest-leverage member archetype for the marketplace flywheel. These vendors don't want to build a CAD engine — they want to ship a vertical tool that runs inside one. White-label lets them ship as a tenant **and** publish their vertical IP as marketplace plugins. The platform gets a member fee, a per-deployment royalty, and a marketplace cut from the same partner.

---

## 7. Brand and legal structure

### 7.1 Entity

Two credible options. Choose during pre-spike legal review (§9 in the existing plan picks this up alongside the ACIS / DELA work).

| Option | Pros | Cons |
|---|---|---|
| **New Jytra subsidiary** owns the platform IP, ACIS contract, ODA contract, Qt contract. ActCAD becomes a member-licensee of the subsidiary. | Clean brand separation; member tenants are signing with a neutral platform entity, not a competitor's parent; cleanest path to outside investment if ever wanted | Subsidiary creation cost; intercompany transfer pricing; ActCAD-the-brand inside Jytra has to formally license from a sibling |
| **Jytra direct** owns the platform; ActCAD is one product line; other members license from Jytra. | Simpler legal structure; lower setup cost; no intercompany overhead | Members are signing with the parent of a competing tenant — a real objection from any second-tier CAD vendor we approach |

> Recommendation: **subsidiary**. The cost of standing one up is small relative to the credibility advantage when pitching the second and third member. A second-tier CAD vendor will not sign a master IP-license agreement with the parent company of ActCAD without significant friction.

### 7.2 Trademark and naming

The platform needs a name distinct from ActCAD. ActCAD continues as a product brand owned by Jytra; the platform brand is owned by the platform entity. Members surface their own brand to end users; the platform brand appears only on the developer / SDK / marketplace surfaces, plus an optional "Powered by [Platform]" trust mark.

### 7.3 IP and licensing posture

- **Engine source code:** platform entity owns. Members license under a perpetual + maintenance model. Source-escrow optional at member tier.
- **Plugin SDK:** released under a permissive license (members can build plugins without infecting their proprietary code).
- **Tenant profile assets** (icons, EULA text, brand colors): owned by the member tenant. Platform holds a build-time license to use them in installer signing.
- **Marketplace plugin IP:** developer-owned. Platform and tenant take rev share, not IP.
- **Audit and reporting rights:** platform audits members for deployment count under ACIS pass-through, no more invasive than ODA's existing audit rights.

### 7.4 Conflict resolution between members

The platform will sign members who compete with each other (e.g. two regional CAD vendors in adjacent markets). Anti-trust-aware contract drafting required from day 1:

- No exclusivity clauses to ActCAD (or any single member) on the platform itself
- Plugin developers can sell to any member tenant
- Marketplace ranking algorithms must be neutral and auditable
- Roadmap input from members is documented; the platform owns final prioritization

---

## 8. The chicken-and-egg problem

This is the single biggest reason the white-label pivot might not be worth doing right now. It deserves a section of its own because it is the dominant risk and the dominant gating decision.

### 8.1 The trap, stated plainly

- **Spatial wants volume commitments** before granting platform-level ACIS terms. Volume commitments require members.
- **Members want to see ACIS terms** before signing — the per-deployment royalty pass-through is a material part of their unit economics.
- **Members also want to see a working product** before signing, and a working developer ecosystem before believing the marketplace pitch.
- **Plugin developers want to see members** before investing in the SDK — one tenant's catalog is not a market.
- **Investors / management want to see the platform business model** before approving the headcount to build it.

Each cycle waits on the others. Without a sequencing plan that breaks one of these dependencies, the pivot stalls.

### 8.2 The anchor-tenant-first sequence that breaks it

The only sequence that actually works is **ship the engine ActCAD-first, build the tenancy seams in from day 1, open to members at GA.**

| Stage | What is shipped | What it unlocks |
|---|---|---|
| **Spike (months 0–1.5)** | Existing 7-item feasibility spike + ACIS bilateral commercial scoping (Spike 1b unchanged). **No platform conversation with Spatial yet.** | Phase 1 / no-go decision; ACIS bilateral terms locked |
| **Phase 1 (months 1.5–12)** | Engine + native Windows beta + ActCAD anchor tenant. **Tenant-profile layer built in from day 1**, even though only one tenant exists. Cost: ~3–6 engineer-months over baseline. | Platform-ready engine; ActCAD beta in customers' hands; demonstrable performance |
| **Phase 2 (months 12–24)** | ActCAD GA + browser editor + cloud co-edit + AI assistant GA. **Soft outreach to 2–3 candidate members during P2.** Conversations only — no contracts. | ActCAD shipping in production; ACIS volume real; member candidates evaluated on a working product |
| **Phase 2 → 3 gate (month 24)** | **Partner-validation gate.** Are at least 2 candidate members at LOI stage? If yes → open ACIS platform-amendment talks with Spatial, formal member onboarding starts. If no → defer white-label to Phase 3+; ActCAD continues single-product. | Decision point with real data, not a bet on a deck |
| **Phase 3 (months 24–36)** | First member tenants onboarded. Marketplace opens. Sunset of IntelliCAD-based ActCAD. | Platform business begins |

> **What this sequence costs:** about ~3–6 engineer-months of extra work during Phase 1 to build the tenant-profile layer (and the disciplines around it — "no `if (tenant == ...)` in engine code") rather than letting tenant-specific bits leak into the engine. That is cheap. **What it buys:** optionality. If the partner pipeline materializes, the platform is one quarter of work away. If it doesn't, we have shipped an excellent single-product ActCAD and lost only the marginal cost of disciplined boundaries we'd want anyway.

### 8.3 What would make us not pursue it

Three signals, any one of which would tell us to defer the platform pivot:

1. **No candidate member reaches LOI stage by month 24.** The pipeline is the proof. If two years of soft outreach to a segment of regional CAD vendors and vertical-tool ISVs has produced zero LOIs, the segment is not there.
2. **Spatial refuses platform-level ACIS terms even at month 24.** With ActCAD shipping, ACIS volume real, and bilateral relationship established, if Spatial still refuses platform amendment, the per-deployment economics break for second-tier members.
3. **ActCAD's own success swamps the optionality.** If ActCAD GA gets traction faster than expected and member outreach feels like a distraction from the anchor's growth, the right call is to stay single-product. This is a real and respectable outcome.

### 8.4 What would make us pursue it harder

Two signals that would change phasing — pull member onboarding into Phase 2:

1. **Two members at signed LOI before month 18.** Demand is real and faster than modeled.
2. **A specific vertical-tool vendor wants to be a member and brings real plugin / vertical IP.** This is the marketplace flywheel starting before GA — rare but possible.

---

## 9. Phasing — when does white-label show up in the roadmap?

| Phase | Engine work (unchanged from existing plan) | Platform work (new in this document) |
|---|---|---|
| **Spike (0–1.5 mo)** | 7-item feasibility spike per §9 | None — keep spike focused on bilateral ACIS + engine viability |
| **Phase 1 (1.5–12 mo)** | Engine on ODA, ACIS via KAL, MCP skeleton, native Windows beta, browser viewer in parallel | **Tenant-profile layer in shell from day 1.** Engineering discipline: no tenant identity in engine modules. Cost: ~3–6 engineer-months over baseline. |
| **Phase 2 (12–24 mo)** | Mac / Linux Qt at parity, browser full editor, 3D via ACIS, cloud co-edit, LISP coverage 95th percentile, AI GA, ActCAD-new GA at month 24 | **Soft outreach to candidate members** (no contracts). License-service and multi-tenant signing infrastructure stood up. Plugin marketplace certification process drafted. |
| **Month 24 gate** | ActCAD-new is GA | **Partner-validation gate.** Are ≥2 members at LOI? Decide: pursue platform amendment with Spatial / open marketplace, or defer indefinitely. |
| **Phase 3 (24–36 mo)** | Full 3D + BIM-lite (IFC), MEP / Electrical verticals as plugins, mobile, IntelliCAD ActCAD sunset | If gate passes: **first members onboarded, marketplace opens to outside developers, ACIS platform amendment signed.** Platform brand publicly launched. |

> **The phasing rule:** the platform business never blocks ActCAD's GA. ActCAD shipping is the proof point that recruits members; flipping that order recruits no one.

---

## 10. Open questions

Items that need management or legal decisions before the §9 partner-validation gate. None block the spike; all block the gate.

1. **Entity:** new Jytra subsidiary or Jytra-direct? (§7.1 — subsidiary recommended but not free.)
2. **Platform brand name:** distinct from ActCAD. Trademark availability to be cleared before any external conversation.
3. **Target member archetypes:** which segments do we approach? Regional CAD vendors stuck on IntelliCAD (BricsCAD, ZWCAD, GstarCAD are not these — they're peers; the targets are the *next tier down*: progeCAD, ARES re-sellers, regional vendors in India / SEA / LATAM / EU). Vertical-tool vendors (MEP / Electrical / Structural / Survey / GIS). BIM-lite startups. Pick 2 segments, not 5.
4. **ACIS platform-amendment negotiation strategy:** when to open, what to ask for, what to concede. Drafted alongside §15.1.1 in the existing plan.
5. **Anti-trust posture:** platform signing competing members. Counsel review needed on contract templates.
6. **Marketplace rev split:** 70/15/15 is illustrative. Comparable-market benchmarks: Apple 70/30, Steam 70/30, Atlassian 75/25 historically, ObjectARX no marketplace. The 15% tenant share is the line that recruits tenants to surface plugins; it has to be defended against tenants who'd rather see 80/20.
7. **Crash-report tenant isolation:** privacy and contract terms for cross-tenant L3 support.
8. **Member exit terms:** what happens to a member tenant's installed base if the member exits the platform? (Source escrow + run-out perpetual license is the standard answer; document it.)

---

## 11. Reading guide

| If you want | Read |
|---|---|
| The engineering plan | `docs/rearchitecture-plan.md` (unchanged) |
| The exec summary | `docs/exec-presentation.md` (unchanged) |
| Memory architecture detail | `docs/memory-architecture.md` (unchanged) |
| Industry trends framing | `docs/industry-outlook.md` (unchanged) |
| **The white-label business case** | this document |
| The ACIS commercial detail | `docs/rearchitecture-plan.md` §15.1.1, then §5 of this document for the platform-level amendment |

---

## 12. One-paragraph summary for the room

The architecture being built for ActCAD-new is also exactly the architecture a white-label CAD platform needs. Adding the tenant-profile layer, license service, and signing infrastructure during Phase 1 costs about ~3–6 engineer-months and gives us the option to open the engine to outside member brands at GA. The commercial dependency is an ACIS platform-amendment that aggregates deployments across members under one royalty schedule; Spatial is likely to grant this only after we have shipped ActCAD-new and proved bilateral volume. We should build the seams in P1, run soft member outreach in P2, and gate the platform decision at the month-24 GA: at least two members at LOI to proceed, otherwise defer to Phase 3 and ship single-product. The downside of building the seams is small; the downside of *not* building them and discovering at GA that we want the platform is large.
