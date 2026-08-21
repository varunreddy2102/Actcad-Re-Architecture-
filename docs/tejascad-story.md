# TejasCAD — The Story

> *Working brand: TejasCAD. Subject to TM clearance per `docs/brand-shortlist.md` §7. Illustrative dates, figures, and market numbers throughout; the shape of the argument is locked, specifics get confirmed with the promoter group before external use.*

---

## 0. The one-paragraph version

For thirty years, the world of "AutoCAD-alternative" CAD has run on a single shared engine: **IntelliCAD**, licensed by a consortium of ~40 small vendors who pay to receive the same source, ship it under their own brand, and compete on the margins. That model built a generation of businesses — ActCAD included — but it is quietly ending. AI is a first-class layer inside CAD now, cloud co-editing is the default for new drafters entering the profession, BIM is moving down into the SMB base, and none of those things arrive through a consortium license fast enough. **TejasCAD** is what those consortium vendors, the vertical MEP / Electrical / Structural / Survey ISVs, and a new generation of BIM-lite startups will run on instead: a modern, ODA-direct, ACIS-kernel CAD engine, wrapped in a ready-to-ship white-label front end, extended by a plugin marketplace, and licensed to members by encrypted contracts we ourselves cannot read. **From India, for the world** — funded initially by the ActCAD promoters in personal capacity, structured for an eventual industry acquisition.

---

## 1. The moment

It is late 2026. Three things are true in CAD that were not true five years ago.

**AI is inside the editor, not next to it.** Autodesk shipped an MCP server in Revit 2027 and Fusion 2026. ARES Graebert shipped the A3 agent in ARES 2027. BricsCAD shipped AI Assistant V26. In three years, "no AI inside" reads the way "no undo" would read today. The lower half of the market — the AutoCAD-alternative segment ActCAD competes in — is structurally locked out of this shift because the shared IntelliCAD codebase can't be structurally modified without consortium coordination.

**Cloud co-editing is the default assumption of new drafters.** Anyone who learned drafting in the last three years learned it inside a Figma-shaped or Onshape-shaped multi-user environment. A single-user Windows-only DWG editor now reads to a fresh hire the way a floppy disk reads to a teenager. AutoCAD Web ships since 2018. ARES Kudo is a full browser DWG editor. Nothing in the IntelliCAD segment ships this credibly.

**BIM is moving into the SMB base.** The 14.7% CAGR of the BIM market plus the government mandates in Europe, the Gulf, Singapore, and increasingly India are pushing IFC import/export and lightweight parametric modeling down into the same SMB AEC shops that today buy ActCAD-tier products. Adding real BIM inside IntelliCAD is architecturally difficult because the shared engine wasn't designed for it.

Three curves are bending upward. The IntelliCAD-based products are on the wrong side of all three.

## 2. The problem, seen from three chairs

### 2.1 A CEO at a small IntelliCAD member vendor

They run a 40-person company doing $6–15M in ARR, mostly perpetual + light subscription, selling in one or two languages / regions. They pay the ITC royalty every year. They pass along consortium bug fixes to their customers. They ship a version behind AutoCAD's DWG format every year and a half. Their salespeople are being asked about AI, about web, about cloud co-edit, about IFC in every second demo. Their engineering team is 6–8 people; they can't build any of that on top of IntelliCAD without breaking the consortium license terms. They can't leave IntelliCAD because rebuilding a DWG-native engine from scratch is a 3-year, $15M project. **They are stuck.**

### 2.2 A founder building a vertical CAD tool

They're building an MEP design tool, or a solar-panel layout tool, or a curtain-wall detailer, or a shipbuilding drafter. They need a CAD engine that reads and writes DWG, has decent 2D drafting, has enough 3D to composite BIM elements, and lets them ship on Windows, browser, and increasingly Mac. Their options today are: **(a)** build on the AutoCAD SDK and pay Autodesk taxes forever, **(b)** build on BricsCAD's plugin API and accept the constraints, **(c)** try to license IntelliCAD (turned away most of the time — the consortium isn't set up for small-ticket verticals), **(d)** build their own engine (3 years, $15M, they don't have it), or **(e)** ship as a limited AutoCAD plugin and never own the customer relationship. **They have no clean option.**

### 2.3 An SMB drafter in Gurgaon, Manila, São Paulo, or Lagos

They spend eight hours a day inside a DWG editor. Their machine is a $600 laptop. Their internet is inconsistent. They want lower cost than AutoCAD, they want their existing DWGs to open without drift, they want their existing LISP scripts to keep working, they want to try AI features when their customers demand it, and they'd like to eventually share a file with a colleague without emailing back and forth. **They're a customer segment that grows every year and gets served worse every year.**

## 3. The insight

Everyone in the AutoCAD-alternative market has spent thirty years believing that **the value was in owning the DWG parser** and the drafting commands. That was true when the barrier to a working DWG engine was writing a million lines of C++ against a spec Autodesk actively obfuscated. It is not true anymore. ODA has been reliable for a decade; a small team can stand up a working DWG viewer on ODA in a quarter. **The value has moved.** It's now in four places:

1. **The AI layer** — MCP servers, transactional agents, drawing-health tools. Anyone building CAD in 2026 who is not building this first is building the wrong product.
2. **The cloud / co-edit layer** — real-time multi-user editing, cloud file management, mobile / browser parity. The reference architecture is well-known now (op-log for geometry, LWW for annotations); shipping it takes a year of engineering, not five.
3. **The plugin ecosystem** — a marketplace where vertical developers ship extensions and get paid. AutoCAD has this via ObjectARX and Autodesk App Store; nobody else does at scale.
4. **The white-label / brand-partner layer** — the ability to ship the same engine under many brands so that regional CAD vendors, vertical ISVs, and BIM-lite startups all run on it without building their own foundation.

**Nobody has built #4 as a real product.** Every CAD engine today is either single-brand (AutoCAD, BricsCAD, ARES, ZWCAD, GstarCAD) or shared-source-consortium (IntelliCAD). The white-label-as-a-first-class-product model is missing from the market. The four layers together — engine + AI + cloud + white-label + marketplace — is what TejasCAD builds.

## 4. The bet

**TejasCAD builds the platform the ActCAD-tier world will run on in 2030.**

We build the engine once, on ODA + ACIS + Qt + WASM, exactly as detailed in `docs/rearchitecture-plan.md`. We wrap it in a ready-to-ship white-label front end so that a member vendor can be shipping a branded product within weeks of signing, not years. We build an encrypted licensing layer that lets members serve their own customers without the platform seeing customer identities, seat counts, or license contents (§10 of this document; full spec in `docs/tejascad-licensing-architecture.md`). We open a plugin marketplace where vertical developers publish once and sell across every member's shell. We ship AI as first-class from day one. We ship cloud co-edit at GA. We take a membership fee, we pass through the ACIS per-deployment royalty at cost, we take a percentage of marketplace GMV. **We do not compete with our members. We power them.**

## 5. The promise, in the words of each audience

**To a member vendor:** "You keep your customer relationship, your brand, your pricing, your channel, your L1/L2 support. You lose the IntelliCAD royalty, the consortium bug-fix bottleneck, the six-month AutoCAD-DWG lag, and the strategic ceiling. You gain AI, cloud, web, mobile, and a marketplace, on day one."

**To a vertical ISV:** "Ship your vertical tool as a full branded CAD product in ninety days. We give you the drawing engine, the DWG file compatibility, the license server, the update channel, the crash-report pipeline, and the marketplace. You focus on the vertical logic that is actually your IP."

**To a member who wants to co-build a vertical with us:** "You bring the domain expertise; our engineering team co-develops the vertical solution with you. You retain attribution and a first-position royalty every time the vertical ships — including when *another* member sells it inside their shell. We provide the development effort at cost or on a shared-cost model, take a platform share, and never build a competing vertical in your named segment without your consent. Full mechanics in `docs/tejascad-company-structure.md` §12 — the Verticalised Solutions Program."

**To a SMB drafter:** "The product you buy from your local vendor uses the same engine and file formats that a Fortune 500 firm's tools use. AI features are the same. Cloud co-edit is the same. It costs a fraction of AutoCAD. It runs on your $600 laptop."

**To an ActCAD customer today:** "Nothing changes for you until GA in year 2. Then your ActCAD gets faster, gets AI, gets cloud co-edit, gets web and mobile access, and your existing DWGs and LISP scripts keep working. In year 3, IntelliCAD-based ActCAD gets sunset and you're on the new engine — as a free upgrade for perpetual holders, as a subscription tier for new AI/cloud features."

**To an eventual acquirer:** "You are buying the CAD platform that powers thirty regional vendors, forty vertical ISVs, and 500,000 end seats across the SMB long tail of AEC / MEP / Electrical / GIS. The platform is ODA-native, ACIS-native, has a shipping AI layer, a shipping cloud, a working marketplace, and the encrypted licensing infrastructure that keeps members' data private from you and from us. It sits below and adjacent to your existing product lines, not on top."

## 6. Who founds this and why they can

The **current ActCAD promoters** — the same people who built ActCAD into one of the largest AutoCAD-alternative brands in India / SEA — capitalize TejasCAD in personal capacity as founder-promoters. They bring:

- **A shipping CAD product** (ActCAD) as the anchor tenant of the platform on day one. Nobody else in the market can capitalize a white-label CAD platform starting with a working, revenue-generating, tens-of-thousands-of-seats brand as tenant zero.
- **Twenty years of channel and customer knowledge** in exactly the segment TejasCAD serves — SMB AEC in India / SEA / MEA / LATAM / EU — which is where the second and third members will come from.
- **Direct experience of the IntelliCAD pain from the inside** — the release cadence, the consortium politics, the fix-goes-to-competitors problem, the AI-license-block. The founders know what to solve because they have lived with what is broken.
- **Personal capital sufficient for the promoter-seed round** — no external dilution before there is a shipping engine and an ACIS bilateral contract, so the equity story stays clean into Series A.

The founding team's day-one credibility with ODA, Spatial, Qt, and prospective member vendors is not a startup pitch — it is a working relationship those parties already have with the same people.

## 7. What we deliberately don't do

- **We don't build our own DWG parser.** ODA already does this; ownership of the DWG codec is not where the value is anymore.
- **We don't compete with our members on branded CAD sales.** ActCAD-the-product is a tenant of TejasCAD-the-platform. Other members are peers of ActCAD under the platform, not customers of ActCAD.
- **We don't ship a Jytra-branded consumer CAD product** in markets where we have members. The platform brand is developer-facing and partner-facing; end users see the member's brand.
- **We don't read member customer data.** The encrypted licensing layer (§10, full doc `tejascad-licensing-architecture.md`) is architecturally blind to license contents, seat counts, and end-customer identities. Members can prove this to their own customers with the same math.
- **We don't fork IntelliCAD, don't ship an IntelliCAD-compatible replacement, don't try to woo the consortium.** We build alongside and eventually past.
- **We don't chase enterprise AutoCAD replacement.** We serve the SMB long tail and the vertical ISV world — the segment the incumbents don't serve well.
- **We don't take institutional funding before the shipping engine.** Promoter capital carries the seed / Phase 1 spike (see `docs/tejascad-company-structure.md` §3); institutional Series A only opens after the ACIS bilateral is locked and the engine feasibility spike passes.

Each "don't" closes a door a competitor keeps open and pays for.

## 8. The three-act arc of the next 5–7 years

### Act I — The engine (year 0 → year 2)

Promoter-seeded. Small senior team. Feasibility spike runs and passes; ACIS bilateral OEM contract signed. Engine standup on ODA. ActCAD as anchor tenant. Native Windows beta at month 12; ActCAD-new GA at month 24. AI as-a-tool and MCP server ship inside the engine from the start. Encrypted licensing spec goes public. Soft outreach to 2–3 candidate members during Phase 2 conversations, no contracts. **End of Act I: TejasCAD engine is real, ActCAD is a live tenant on it, and the platform seams are all built into the shell from day 1.**

### Act II — The platform (year 2 → year 4)

Partner-validation gate passes at month 24 (at least two members at LOI stage). ACIS platform-amendment negotiation opens with Spatial from a position of shipping success. First 2–3 external member tenants onboarded — target profile: one regional AutoCAD-alternative CAD vendor stuck on IntelliCAD, one vertical ISV in MEP / Electrical / Structural, and one BIM-lite startup. Plugin marketplace opens to outside developers. Cloud co-edit + web full editor ships. **Series A at month 30** (~$18M at ~$75M post-money illustrative), sized to observed member and marketplace demand. Series B at month 48–54 (~$50M at ~$350M post) once member count is 8–10 and marketplace GMV is meaningful. **End of Act II: TejasCAD is a platform business with 3–5 members, a working marketplace, and its first two institutional rounds.**

### Act III — The valuation walk to exit (year 4 → year 7)

Member count reaches 10–15. IntelliCAD-based ActCAD is fully sunset; the platform's own tenants are the only live CAD products in the Jytra family. AI / cloud become the majority of new revenue; perpetual base is the durable floor.

**Around month 60–66, the pre-exit growth round** — the specific move the founders make to *increase* the company's valuation ahead of acquisition rather than just cover runway. Sized around $75–150M at ~$1.0–1.5B post-money valuation. Purpose is threefold: **(a)** the post-money price becomes the floor any acquirer must clear, **(b)** the capital funds 18–24 months of ARR growth that — at 10–15× forward-revenue multiples for platform / AI / marketplace businesses — compounds into another billion of enterprise value, and **(c)** a well-funded company with strong momentum negotiates from optionality, not necessity. This round is not mandatory: it is the value-creation lever the founders pull if the M&A conversation would otherwise arrive at $500–800M and the case for $1.5–2.5B is credible.

**Month 78–84 — acquisition.** Target price envelope $1.5B–$3B depending on ARR trajectory, marketplace GMV, member count, and acquirer competition. Acquirer archetypes (full landscape in `docs/tejascad-company-structure.md` §8): a large CAD incumbent (Autodesk, Hexagon-Bricsys, Dassault, PTC, Bentley), an ODA member consortium buyer, a PE roll-up assembling a CAD portfolio, a strategic industrial vendor entering CAD, or an Indian tech major acquiring a global engineering platform. Founders exit or take secondary; members continue under the acquirer with survival clauses in the master license. **End of Act III: TejasCAD acquired in the $1.5–2.5B envelope, or continues as a standalone with the growth-round capital fueling an IPO track.**

## 9. The tagline

**TejasCAD. The CAD platform. Built in India, for the world.**

*Alternate phrasings under consideration: "The platform every CAD is built on." / "Your brand. Our engine. The world's CAD." / "The DWG platform of the next decade."*

## 10. Where each thread continues

| Thread introduced here | Full detail in |
|---|---|
| Company structure, promoter capital, cap table, funding path, acquisition | `docs/tejascad-company-structure.md` |
| Encrypted licensing that keeps member data private from the platform | `docs/tejascad-licensing-architecture.md` |
| Why the IntelliCAD-dependent world is the primary target and how we compare | `docs/tejascad-vs-intellicad.md` |
| The engineering plan (unchanged from the ActCAD re-arch) | `docs/rearchitecture-plan.md` |
| The white-label platform architecture superset | `docs/platform-strategy.md` |
| The pitch to members, investors, and acquirers | `docs/tejascad-pitch-deck.md` |
