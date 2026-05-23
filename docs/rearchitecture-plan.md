# ActCAD Re-Architecture Plan

> **Status: Proposal, gated on the feasibility spike in §9.** Read alongside `docs/architecture-overview.md` (current stack and why it has to be replaced) and `docs/industry-outlook.md` (where the segment is going).

## 1. Goal

Replace the IntelliCAD engine with a first-party engine built directly on **ODA SDKs and the ACIS 3D kernel (Spatial / Dassault)**, over a 3-year horizon. By end of year 3, ActCAD on the new stack must equal or beat today's IntelliCAD-based ActCAD on every dimension that matters to customers (performance, platform reach, AI assistance, BIM, extensibility), while existing ActCAD continues to ship through Phase 2 to protect revenue.

The architecture must be **future-proof on three axes that the current stack is not**: cross-device (desktop + web + mobile), AI-native (first-party MCP/agent surface inside the engine), and ours to refactor (no consortium gating).

## 2. Key architectural decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 2.1 | Foundation libraries | ODA direct (Drawings, Visualize, IFC, BIM SDKs, MCAD, Civil, Scan-to-BIM, inWEB family). Drop ITC / IntelliCAD entirely. | One vendor relationship covering DWG + BIM + IFC + renderer + web. Royalty-free under ODA membership. Eliminates the consortium cadence problem. |
| 2.2 | 3D kernel | **ACIS (Spatial / Dassault) primary**, full commercial OEM contract. All kernel access goes through the KAL so the engine never depends on ACIS-specific types in public headers. **ODA MCAD is not the kernel — it's a translator** for reading and writing SolidWorks / Inventor / CATIA files (see §11). Gated on §9 spike item 1 (ACIS round-trip fidelity vs AutoCAD on customer DWGs) and spike item 1b (ACIS commercial scoping under NDA). | **AutoCAD's 3D solids are stored as ASM (Autodesk Shape Manager), which is a fork of ACIS that Autodesk took private around 2001.** A DWG with 3D solids contains ACIS/ASM SAT (Standard ACIS Text) blobs as `AcDb3dSolid` entities. For lossless round-trip of AutoCAD-origin 3D solids — the central value prop for AutoCAD migrators — ACIS is the natural kernel: same lineage, same topology model, same tolerance semantics. Translating ACIS → any-other-kernel → ACIS introduces drift on edges, fillets, and booleans that customers will see and reject. ActCAD already uses ACIS today through the IntelliCAD stack; this decision preserves geometric continuity for the existing customer base while putting the contract directly in our name. |
| 2.3 | Shell strategy | Shared C++ core compiled to native + WASM. **Qt 6 native shells** (Win / macOS / Linux) **on the commercial license** (not LGPL — see §15.4). **TypeScript + React + WebGPU** browser shell. Mobile deferred to Phase 3. | Web-only Tauri / Electron is rejected for the drawing window — CAD pros need native menus, drag-drop with the OS, accessibility APIs, and printer integration. Qt is what Autodesk Maya and most pro DCC apps use. Tauri stays as the right tool for a thin launcher / license app, not the editor. Qt commercial is required for static linking, modifications kept private, and iOS code-signing — all of which apply to a closed-source commercial product. |
| 2.4 | Engine language | **C++20** primary (interops directly with ODA's C++ SDKs — no FFI tax on inner-loop database calls). **Rust** selectively for `net`, `script` (host), `agent` (MCP), and new geometry algorithms where memory safety compounds. **No Rust in `db` or `render` hot paths.** | A CAD inner loop touches millions of entities per regen; the FFI tax of a Rust-primary core against a C++ SDK would be unacceptable. Rust earns its place where the boundary is narrow and the safety win compounds. |
| 2.5 | Extension APIs | **AutoLISP-compatible runtime** (migration story for the customer ecosystem). **Modern**: Python (embedded), TypeScript (in-app + browser), .NET 8+ (cross-platform via NativeAOT). **Dropped**: SDS, ADS, DIESEL, VBA, COM. **.NET surface is new — not ObjectARX-compatible** (set this expectation early). | LISP is the AutoCAD-ecosystem migration moat. The rest are legacy maintenance contracts with shrinking usage. The new .NET surface is opinionated and modern; pretending it's ObjectARX is a trap. |
| 2.6 | AI / agent surface | **MCP server inside the engine, wrapping the `cmd` module only** (never the `db` directly). Two MCP endpoints mirroring Autodesk Fusion 2026: a **local MCP** (requires ActCAD running, executes commands inside the host transaction) and a **remote MCP data server** (cloud, no host required, read-only DWG metadata + sheet / layer queries). **Public commitment: every MCP tool call resolves to exactly one transaction in the host undo stack.** No competitor (Autodesk Revit 2027, Fusion 2026, BricsCAD, ARES A3) has publicly documented this — it's a defensible differentiator. | The hard part of an agent surface for CAD is the *transactional command boundary*, not exposing the database. Revit 2027 MCP is Tech Preview without documented undo semantics; reviewers have already complained about half-finished features. Owning the transaction story publicly is both the right engineering and the right marketing. |
| 2.7 | Cloud / co-edit | **Two-tier server-authoritative model**. Tier 1 (geometry): serialized op-log over the engine's mutation stream, server-validated for referential integrity (door-to-wall, dim-to-entity), optimistic UI. Tier 2 (annotations, comments, markups, layer properties, sheet titles): Figma-style last-writer-wins per property with fractional indexing for ordering. Presence + selection locks at the UI layer. **Not a generic CRDT.** | The industry has converged here. Onshape uses serialized feature-level operations with branch-and-merge (USPTO 10,691,844). Figma explicitly rejected both OT and pure CRDT for LWW-per-property because each field updates independently and "merge text by character" isn't a real need. Yjs / Automerge OOM at the millions-of-entity scale of a real MEP DWG; recent academic work (geometry-aware CRDTs, MDPI 2025) confirms generic CRDTs lose intent on spatial documents. ARES Kudo ships closer to soft-lock + sync today — we can do better by going server-authoritative op-log on geometry from day 1. |
| 2.8 | License seam | The boundary between local-perpetual code and cloud-subscription code is a **build-time module boundary**, not a runtime feature flag. | Perpetual remains the moat; cloud / AI is an additive subscription. The architecture has to make this monetization model physically clean rather than glued on later. |
| 2.9 | Build system | CMake for C++ (industry standard, plays well with ODA's build pipeline). Emscripten for the WASM target. Cargo for the Rust crates, linked through a stable C ABI. | No exotic build tooling. The team will be onboarding from a C++ / IntelliCAD background. |

## 3. Module decomposition (C++ core)

Ten modules with strict contracts. The only module that mutates state is `db`; the only module the agent talks to is `cmd`.

1. **`db`** — drawing database. Canonical entity model, transactional mutation API, undo log, handle table, layer / block tables. Emits a typed op-stream on every commit. **Only mutator.**
2. **`geom`** — geometry primitives and the Kernel Abstraction Layer (KAL) over ACIS. Pure functions, no state. **No ACIS `ENTITY` type appears in any header outside this module** — opaque handles only. The KAL is what keeps a kernel swap technically possible (6–12 weeks of focused work) if business conditions ever require it; it is not a hedge against ACIS being the right call today.
3. **`render`** — view + render-abstraction over ODA Visualize and a future native backend. Read-only consumer of `db`; subscribes to the op-stream for invalidation.
4. **`cmd`** — command bus. Every user action, LISP call, .NET call, MCP call flows through here. Owns parsing, prompts, validation, transaction begin / commit, undo grouping. **The single seam the AI agent talks to.**
5. **`script`** — scripting host. Embeds CPython (native) / Pyodide (WASM), the LISP interpreter, and the JS bridge. All three reach `cmd`, never `db` directly.
6. **`plugin`** — plugin host. ABI versioning, capability negotiation, sandbox policy (stricter for WASM). API parity across native / WASM, **not** binary parity.
7. **`net`** — sync, document service client, auth, telemetry. Rust crate, exposed via stable C ABI.
8. **`agent`** — MCP server, tool catalog, permission scoping, dry-run / rate limiting. Wraps `cmd`. Rust crate.
9. **`platform`** — file I/O, fonts, clipboard, printer, GPU surface acquisition. **The only module with `#ifdef PLATFORM`.**
10. **`ui-bridge`** — thin C ABI / FlatBuffers boundary the Qt shell and the React / WASM shell both consume. **No UI code here.**

Communication: synchronous in-process calls within native; FlatBuffers over `postMessage` for WASM ↔ JS; the `db` op-stream is the universal invalidation / sync substrate (also fed to the co-edit network layer and the agent for context updates).

## 4. Stack at a glance

| Layer | Choice |
|---|---|
| DWG / DXF + database | ODA Drawings SDK |
| Rendering | ODA Visualize. Native backends: **DirectX 11 (Windows default), DirectX 12, Vulkan (cross-platform), Metal (macOS / iOS)**. Web: Visualize inWEB → WebGPU (WebGL2 fallback). All driven through our `render` module's abstraction layer so backends are swappable. |
| 3D Kernel | **ACIS (Spatial / Dassault)** primary, KAL-abstracted. Commercial OEM contract — initial fee + per-seat / per-deployment royalty + annual maintenance + component-module fees (see §15). |
| MCAD format I/O | ODA MCAD SDK (SolidWorks / Inventor / CATIA / NX / Creo translators) — read-only initially |
| BIM / IFC | ODA IFC SDK + BimRv / BimNw extensions |
| Engine language | C++20, selective Rust |
| Build | CMake + Emscripten + Cargo |
| Desktop shell | Qt 6 (commercial-vs-LGPL TBD per §10) |
| Browser shell | TypeScript + React + WebGPU (WebGL2 fallback) |
| Mobile shell | Native (Swift / Kotlin) over the C++ core via FFI — Phase 3 |
| Scripting | Python (CPython / Pyodide), TypeScript, .NET 8+ NativeAOT, AutoLISP shim |
| Agent surface | MCP server in `agent`, wrapping `cmd` |
| Cloud co-edit | Two-tier: server-authoritative op-log (geometry) + LWW per property (annotations / metadata) |
| Document service / auth / billing | TBD per §10 — leaning Clerk + Stripe + self-hosted document service |

## 5. Phasing — native-Windows-first, web in parallel

> **Important inversion from the obvious plan**: the obvious move is web-first because the industry is going there. For ActCAD's installed base specifically — Windows-desktop SMBs in India / SEA who pay perpetual and run on hardware where browser WebGPU is unreliable — a web-only beta would produce no useful signal. The Phase-1 daily-driver target is native Windows; web ships in parallel as viewer / markup first, then full editor.

### Phase 1 — Foundation (months 0–12)

- Engine skeleton on ODA Drawings + Visualize, with the module decomposition in §3.
- DWG open / edit / save with full ODA fidelity. Round-trip corpus exists and gates every PR.
- 2D drafting commands: line, polyline, circle, arc, hatch, dim, layer, block, OSnap.
- Native Windows Qt shell shipped to a willing-customer cohort by month 12.
- Parallel **viewer + markup** browser shell on the same engine, shipped at month 12.
- LISP runtime spike against a measured customer-script corpus; coverage target = top 80th percentile of customer scripts running.
- MCP server in `agent` exposing ~30 commands; AI assistant skeleton with dry-run + undo + permission scoping.
- IntelliCAD-based ActCAD continues to ship in parallel.

### Phase 2 — Production v1 (months 12–24)

- macOS and Linux Qt shells at parity with Windows.
- Browser shell promoted from viewer to full editor.
- LISP shim coverage extended to 95th percentile of measured corpus; migration tool ships for the long tail.
- Light 3D (basic solids, view, navigation) via ACIS through the KAL.
- Cloud document service with real-time co-edit on 2D drawings (op-log path, not CRDT).
- Plugin host stabilizes; Architecture vertical reshipped as the first plugin.
- AI assistant moves to GA: prompt-driven drafting, AI-generated blocks, command recommendations.
- New product GA at end of month 24. IntelliCAD ActCAD continues to ship in parallel.

### Phase 3 — Parity-or-better (months 24–36)

- Full 3D + BIM-lite (IFC import / export, parametric architectural objects).
- MEP and Electrical verticals reshipped as plugins; digital-twin / IoT extension hooks.
- Mobile (iOS / Android) shells over the same C++ core.
- End-to-end rendering pipeline tuning — now ours to own.
- IntelliCAD ActCAD enters sunset on a published timeline.

## 6. What we deliberately don't do

- Don't ship web-first to the existing installed base.
- Don't promise *binary* plugin parity across native and WASM — only API parity.
- Don't use a generic CRDT for DWG co-edit.
- Don't bundle SDS / ADS / DIESEL / VBA / COM.
- Don't try to be ObjectARX-compatible on the .NET surface.
- Don't let Rust into `db` or `render` hot paths.
- Don't sign the ACIS contract before §9 spike item 1 confirms round-trip fidelity on customer DWGs and spike item 1b returns a written term sheet from Spatial.
- Don't treat ODA MCAD as a B-rep modeling kernel — it's a translator for MCAD file formats only.
- Don't ship chat-in-canvas as the primary AI UX (Hypar pivoted away from text-to-BIM for this reason — see §14).
- Don't chase Bernini-style generative-CAD demos until editable, parametric round-tripping is proven.
- Don't use Yjs / Automerge for the geometry plane — confine generic CRDTs to non-spatial metadata only.
- **Don't let ACIS types leak past the KAL.** Every public header outside `geom` uses opaque handles. The KAL is what makes the engine survive kernel-vendor risk; bypassing it for "just this one feature" erodes the only insurance we have.
- **Don't ship to customers without royalty-reporting infrastructure in place.** The ACIS DELA requires accurate seat / deployment counts; building this after GA is a contractual exposure we don't take.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| **ACIS round-trip fidelity vs AutoCAD** — customer DWGs must open in new ActCAD, edit, save, and re-open in AutoCAD with no visible drift | §9 spike item 1 tests this on 50 real customer DWGs before signing the contract; KAL preserves a kernel-swap escape hatch if a regression is discovered post-GA |
| **ACIS commercial exposure** — opaque pricing, royalty per seat, change-of-control risk (Dassault owns SolidWorks, a competitor) | §9 spike item 1b returns a written term sheet under NDA; commercial / legal review of the DELA + change-of-control + business-continuation clauses; source escrow option negotiated; module list scoped before signing so component fees don't surprise |
| **ACIS WASM viability** — no public production WASM build of ACIS; if browser shell needs kernel-grade editing, this is a custom engineering conversation | §9 spike item 2 evaluates the inWEB + read-only-ACIS-translator path for the browser shell; full ACIS in WASM stays a Phase-2/3 question if customer demand requires it |
| **inWEB ≠ same binary as native** — likely two builds with shim parity, not one bundle | §9 spike item 2 measures the actual delta; messaging adjusted accordingly |
| **LISP compatibility is multi-person-year**, not a 12-month spike | Define "compatibility" as a measured percentile of a real customer-script corpus before kickoff; ship migration tool for the tail |
| **MCP without a transactional boundary** corrupts drawings | `agent` wraps `cmd` only; never `db`. Permission scoping, dry-run, rate limit from commit 1 |
| **Cadence trap re-emerges with ODA** | Renderer escape valve: `render` is an abstraction over Visualize, so a native Vulkan backend can be slotted in if Visualize stalls |
| **Qt licensing surprises** | Commercial license locked (§15.4); §9 spike item 6 negotiates the multi-year quote, not the licensing model |
| **Two parallel product lines for 24 months** is an org risk, not a tech risk | Support / engineering / marketing org plan written separately; clear customer messaging from day 1 |
| **`ui-bridge` ABI churn** breaks plugins and shells | Version the ABI from commit 1; never break, only extend |
| **DWG handle stability** across save / load (customer xdata uses handles) | Lock handle semantics before the save format is frozen in Phase 1 |
| **CRDT-vs-op-log** is decided on marketing, not on a DWG prototype | §9 spike item 7 prototypes 2-user co-edit on a real drawing before locking the design |

## 8. Migration story for existing customers

- IntelliCAD-based ActCAD continues to ship through Phase 2; sunset date is announced when new product reaches GA.
- LISP migration tool ships in Phase 2 with coverage of the measured customer-script corpus.
- Strategic customer .NET / IRX scripts are migrated by a **paid migration service** delivered by the same team that built the new APIs.
- File formats: full DWG round-trip parity from Phase 1, validated against a corpus that includes real customer drawings.
- Pricing: existing perpetual licenses get an upgrade path to the new product's perpetual tier; AI / cloud features are the new subscription line.

## 9. Feasibility spike — 4–6 weeks BEFORE committing to the 3-year plan

Seven validations, in priority order. **If items 1, 2, 3, or 5 fail, the plan changes before kickoff, not at the Phase-2 boundary.**

| # | What | Pass criterion |
|---|---|---|
| 1 | **ACIS round-trip fidelity test vs AutoCAD.** Take 50 customer DWGs containing ACIS / ASM B-rep solids. Open through ACIS, edit (move / boolean / fillet), save, re-open in AutoCAD. Measure geometric drift on volume / surface area / bounding box, boolean robustness, fillet survival, attribute preservation. | No visible drift, <0.001 unit tolerance on volume / area, identical entity handle set, booleans pass on ≥98% of customer solids. **If this passes, ACIS is locked for the 3-year plan and the contract is signed.** If it fails, the assumption that direct-ACIS gives lossless AutoCAD fidelity is wrong and we re-open the kernel decision. |
| 1b | **ACIS commercial scoping under NDA.** Procurement + legal track running parallel to spike item 1. Get written term sheet from Spatial naming: module list (Local Ops, Healing, Defeaturing, Polyhedral, etc.); **royalty model — per-deployment is the ask, per-seat is the documented fallback only** (see §15.1.1 for the comparison math, ~10× cost variance, and full negotiating sequence); WASM / Linux / macOS SKU availability; source-escrow option; DELA full text; change-of-control + business-continuation clauses; support-hour bundle. | Signed term sheet in hand before Phase-1 kickoff. Module list scoped to ActCAD's actual use case (no surprise component fees later). **Per-deployment royalty locked as the primary ask per §15.1.1**; per-seat accepted only if the 5-year amortized cost beats the per-deployment alternative Spatial would have offered. Volume tier breakpoints + annual minimum floor + carve-outs (trials / education / internal QA) all in writing. |
| 2 | Render the same 50 DWGs through native Visualize (Vulkan) *and* through Visualize inWEB (WebGPU); compare frame time on a 250k-entity drawing | inWEB ≤ 3× slower than native |
| 3 | Spike the `ui-bridge` C ABI / FlatBuffers seam: drive 10 commands from both a Qt shell and a React + WASM shell against a single `cmd` implementation | Seam is one source of truth; no shell-specific branching in `cmd` |
| 4 | Run a real customer LISP script (largest one a top-5 customer uses) through a minimal LISP interpreter on top of `cmd` | Script runs and produces visually identical output to current ActCAD |
| 5 | Stand up an MCP server exposing `cmd` to Claude / GPT; have it execute "draw a 3-bed apartment plan from this brief" | Command surface is agent-shaped, not human-shaped; no drawing corruption |
| 6 | Negotiate Qt 6 commercial multi-year quote at Jytra's actual revenue tier (Small Business almost certainly not eligible). Target 15–35% below first quote per Vendr-reported norm. | Signed quote in hand for App Dev Enterprise + mobile / WASM add-ons covering Phase-1 + Phase-2 headcount, with a price-protection clause for Phase-3 growth. |
| 7 | Reproduce 2-user co-edit on a 2D drawing with a stub op-log over WebSocket (not CRDT) | Op-stream design supports replication; conflict semantics on a real DWG operation are sane |

## 10. Open decisions for legal / commercial review

> ActCAD is a closed-source commercial product. Where a license has a free open-source path *and* a commercial / paid path, commit to the path that is unambiguously safe for closed-source distribution and standard commercial practice (static linking, code-signed binaries, modifications kept private). The locked / open status of each item below reflects that posture.

- **Qt 6 — LOCKED to commercial.** Static linking, code-signed iOS / macOS distribution, and keeping our Qt modifications private are all required; LGPL v3 does not support those. The remaining open work is *quote negotiation*, not the licensing model — see §9 spike item 6 and §15.4.
- **ACIS — LOCKED as the 3D kernel choice, commercial terms OPEN.** Spatial / Dassault commercial OEM contract. Decision rationale is locked (AutoCAD ASM ⊃ ACIS lineage → lossless DWG fidelity); commercial *terms* (initial fee, royalty model, module list, DELA specifics, change-of-control protection, source escrow) are open pending §9 spike item 1b. **Do not sign before the spike returns a term sheet.**
- **ODA — LOCKED to Sustaining from day 1**, Founding considered in Phase 3 for source / Git access. Limited Commercial's 100-seat cap is a footgun at our scale; Sustaining provides Web/SaaS (inWEB) redistribution rights without per-seat royalty.
- **Visual Studio — LOCKED to Enterprise** for C++ inner-loop devs (advanced profiling, IntelliTrace). Professional for the rest.
- **Document service / auth / billing stack** — recommended Clerk + Stripe + self-hosted document service. **Open** pending data-residency review for EU / India customers.
- **Customer-facing .NET API scope** — explicitly *not* ObjectARX-compatible. **Open** pending announcement / migration messaging review.
- **IntelliCAD-ActCAD sunset date** — **open**, driven by Phase 2 GA quality, not a date picked up front.
- **Alternative kernels — not chosen.** Other commercial / open-source B-rep kernels exist but don't share the ACIS / ASM heritage that gives us lossless fidelity on AutoCAD-origin DWG 3D solids — translating AutoCAD-origin SAT blobs through any non-ACIS kernel introduces drift on edges, fillets, and tolerances that our migration-focused customers will see and reject. The KAL keeps a kernel swap technically possible at ~6–12 weeks of focused work if business conditions ever require it; it is not a hedge against ACIS being the right call today.

## 11. Industry adoption — who else picked these and why

For each component of the planned stack: notable adopters, why they picked it, known pain points in shipped products, and the resulting verdict for ActCAD.

### 11.1 ODA SDKs (Drawings, Visualize, IFC, BIM, MCAD, inWEB) — direct membership

- **Adopters.** Bricsys / BricsCAD (founding ODA member, the deepest user — Drawings + Visualize + BIM + IFC SDK), GstarCAD, ZWCAD, NanoCAD (all direct on ODA Drawings). Graphisoft ARCHICAD and Vectorworks use ODA Drawings as their DWG import / export layer. Bentley MicroStation, Trimble, Dassault hold memberships for format interop. ARES Graebert wrote their own DWG library and uses ODA selectively. **IntelliCAD itself swapped its in-house DWG core for ODA technology under the hood years ago**, so all IntelliCAD-derived products (ActCAD, progeCAD, CMS IntelliCAD) inherit ODA indirectly today.
- **Why.** Format coverage no one else ships under a single C++ API (DWG back to R12, DGN, IFC 2x3/4/4.3, Revit, Navisworks); aggressive Autodesk-version tracking; one membership covers everything; Visualize lets members drop expensive third-party graphics middleware (HOOPS, etc.).
- **Known pain.** Annual membership fee is non-trivial (Sustaining tier required for MCAD). API surface is wide but uneven — Revit *read* is mature, Revit *write* is partial. Threading model is heavy C++. Riding ODA's release cadence whether your QA is ready or not. Visualize scene graph is its own world — interop with engine-side picking / snapping is your problem.
- **Cost (vendor-published).** Limited Commercial $3K first yr / $2.25K renewal (100-seat cap). **Pro / Sustaining $7.5K first yr / $4.5K renewal** — unlimited commercial seats + Web/SaaS (inWEB) redistribution rights, **no per-seat royalty**. Enterprise / Founding $37.5K first yr / $18K renewal — adds full source + Git access + board nomination. Extensions priced separately (BimRv / BimNw / MCAD / Civil typically $5K–$10K/yr each on top of the membership). See §15 for the rollup. ([ODA pricing](https://www.opendesign.com/pricing))
- **Verdict.** **Good fit, go direct.** ActCAD already pays ODA transitively; cutting to direct membership removes ITC as middleman and matches BricsCAD / GstarCAD / ZWCAD / NanoCAD.
- Sources: [ODA Members](https://www.opendesign.com/oda-membership), [Bricsys ODA showcase](https://www.opendesign.com/member-showcase/bricsys), [IntelliCAD on ODA](https://gfxspeak.com/featured/autocad-workalike-market/).

### 11.2 ACIS (Spatial / Dassault) — 3D kernel

- **Adopters.** Used by AutoCAD (via its ASM fork — see lineage note below), SpaceClaim (now ANSYS Discovery), Bentley MicroStation (uses both ACIS and Parasolid in different products), Hexagon products, BobCAD-CAM, IronCAD, CADopia, and **ActCAD itself today (via the IntelliCAD + ACIS stack)**. ACIS has been continuously productized since 1989 and is the second-most-deployed commercial B-rep kernel after Parasolid.
- **The AutoCAD lineage that matters.** AutoCAD shipped with ACIS for 3D solids starting with R13 (1994). Around 2001, Autodesk forked the ACIS source they had licensed and created **ASM (Autodesk Shape Manager)**, which is what AutoCAD, Inventor, Revit, and Fusion use today. The DWG format still stores 3D solids in the **ACIS SAT (Standard ACIS Text) blob format** as `AcDb3dSolid` entities — that's the on-disk representation. Reading a DWG with 3D solids gives you ACIS SAT. **Editing those solids with ACIS itself is the highest-fidelity path possible** outside of using ASM directly (which Autodesk does not license externally). Translating SAT into any non-ACIS kernel and back introduces drift on edges, fillets, tolerances, and history — drift that AutoCAD users see and reject.
- **Why this is the right choice for ActCAD.** Three reasons, in priority order: (1) **AutoCAD-fidelity migration story** — our customers are AutoCAD-DWG-native and that's our value prop; (2) **continuity** — ActCAD has been running on ACIS via IntelliCAD for years, so customer files, plugins, and workflows already assume ACIS semantics; (3) **maturity** — ACIS booleans, fillets, healing, and defeaturing are production-proven on the exact AEC + light-MCAD workloads ActCAD serves.
- **Known pain.** Largely single-threaded inside one body — concurrency happens across bodies, not within one operation. Module sprawl: base ACIS doesn't include robust booleans (Local Operations), import-healing (Healing), defeaturing (Defeaturing), or polyhedral / mesh (Polyhedral) — each is a separately-priced component. **No public production WASM build** — browser shell needs a separate path (ODA's read-only translator + viewer in Phase 1, full ACIS-in-WASM is a custom engineering conversation if needed in Phase 2/3). Memory model uses derivation from `ENTITY` with explicit `lose()` semantics; KAL must encapsulate this so it doesn't leak into the rest of the engine.
- **Cost.** Commercial OEM — opaque, procurement-gated. Industry-estimate shape: **six-figure initial license + 15–20% annual maintenance + per-seat or per-deployment royalty + per-module component fees + DELA distribution restrictions**. See §15.1 for the full structure and §9 spike item 1b for the procurement workstream that returns real numbers. **All ACIS line items in §15.2 envelopes are procurement placeholders pending the spike's term sheet.**
- **Verdict.** **Locked as the 3D kernel choice, contract terms gated on §9 spike items 1 and 1b.** The technical reasoning (AutoCAD ASM lineage → lossless DWG fidelity) is decision-forcing; only the commercial terms remain to be closed.
- Sources: [Spatial ACIS](https://www.spatial.com/solutions/3d-modeling/3d-acis-modeler), [ASM history](https://en.wikipedia.org/wiki/Autodesk_Shape_Manager), [AcDb3dSolid / ACIS in DWG](https://help.autodesk.com/view/OARX/2024/ENU/?guid=GUID-1B5BBE0E-44CA-4F2A-B8C3-3D2C7E8C0F8F), [ACIS components list](https://www.spatial.com/products/3d-acis-modeling).

### 11.3 ODA MCAD SDK — translator, not kernel

- **Adopters.** **Effectively none in production yet.** SolidWorks read opened June 2025; Inventor read followed; CATIA / NX / Creo / JT / Parasolid / Solid Edge are on the 2026–2027 roadmap. No shipped end-user CAD product is on it as a primary kernel.
- **Why members are interested.** Flat per-company pricing (no per-developer / per-seat), bundled into ODA membership extension — orders of magnitude cheaper than Parasolid (six-figures/yr + royalties) or ACIS. The only credible CATIA / SOLIDWORKS *write* path not controlled by Dassault.
- **Comparison.** ACIS (our chosen kernel, §11.2) is the production B-rep modeler; ODA MCAD is positioned as **translation / interop** — read SolidWorks / Inventor / CATIA, feed the resulting geometry into ACIS, edit there. The two complement each other and we use both.
- **Cost.** Bundled into ODA membership (Sustaining + extension, ~$5K–$10K/yr on top of the membership base). No per-seat royalty. **Parasolid for comparison: OEM only, fully opaque pricing, industry estimate six-figure upfront + per-seat royalty + annual maintenance** (Engineering.com / PROLIM analysts characterize CAD-component spend at 15–17% of ISV revenue once kernel + interop + visualization are stacked).
- **Verdict.** **Mismatch as a modeling kernel.** Use it as a **SolidWorks / Inventor / CATIA importer** in Phase 2-3 once it's mature. Do not stake the 3D pipeline on it.
- Sources: [ODA MCAD product](https://www.opendesign.com/products/mcad-sdk), [MCAD SDK for SolidWorks](https://www.opendesign.com/blog/2025/december/mcad-sdk-solidworks-files).

### 11.4 Qt 6 — desktop shell

- **Adopters in CAD / DCC.** Autodesk Maya (Qt since 2011), MotionBuilder, Mudbox, parts of 3ds Max; The Foundry Nuke / Mari / Katana; SideFX Houdini; Foundry Modo; CATIA V6 / 3DEXPERIENCE; Allplan / Nemetschek; FreeCAD (Qt 5 → 6 in progress); QCAD; OpenSCAD. **Counter-example.** Blender (custom OpenGL UI).
- **Why.** Cross-platform from a single codebase; mature OpenGL / Vulkan integration via QOpenGLWidget / QRhi; native theming; Qt Quick / QML for modern panels; signal-slot maps cleanly onto large C++ codebases.
- **Known pain.** **Commercial cost.** Qt for Application Development Professional / Enterprise is ~$4,000–$6,000 per developer per year for desktop; Small Business tier (rev-gated, caps at ~$250K) is €530/year/dev. Add ~30–60% for mobile / embedded / Qt-for-WebAssembly. LGPL requires dynamic linking — static-link needs the paid license. Qt 5 → 6 migration is painful at scale (FreeCAD's Qt 6 work has been 2+ years and still partial).
- **Cost (vendor-published, locked to commercial — see §10).** Standard Application Development Enterprise: **~$3,948–$4,660/yr/dev**, mobile / WebAssembly add-ons +30–60%. Small Business (€530/yr Pro, USD 618/yr Enterprise) **almost certainly not eligible at Jytra's revenue**; model standard pricing. LGPL is rejected: a closed-source commercial product can't static-link Qt under LGPL v3, can't ship a code-signed iOS app cleanly under it, and can't keep Qt modifications private. Vendr reports buyers commonly negotiate **15–35% below first quote** on multi-year contracts; §9 spike item 6 owns that conversation. ([Qt pricing](https://www.qt.io/pricing), [Vendr](https://www.vendr.com/marketplace/qt))
- **Verdict.** **Good fit, with a decision-forcing legal call.** Industry-standard for this product category. The LGPL-vs-commercial call gets made in §9 spike item 6.
- Sources: [Maya Qt SDK](https://help.autodesk.com/cloudhelp/2020/ENU/Maya-SDK-MERGED/developer/Working-with-Qt/Using-Qt-in-Plug-ins.html), [Qt pricing](https://www.qt.io/pricing), [Qt Small Business](https://www.qt.io/development/qt-for-small-business), [FreeCAD Qt 6 #6992](https://github.com/FreeCAD/FreeCAD/issues/6992).

### 11.5 C++ vs Rust for the engine core

- **Adopters (Rust).** **Fornjot** (Hanno Braun) — experimental B-rep kernel, explicitly "reliability over features," no shipped product on it. **Truck** (RICOS-JP) — Rust B-rep kernel, compiles to WASM; used by **CADmium** (Matt Ferraro). **Zoo.dev / KittyCAD** — the most serious commercial Rust CAD play; Rust geometry engine on the server (Vulkan / Nvidia), React frontend, app shipping. **Figma** — C++ canvas, Rust used for multiplayer sync server and hot-path tooling. Pattern: Rust at the edges, not the kernel.
- **Why.** Memory safety without GC, fearless concurrency, excellent WASM toolchain, cargo, no header / macro hell. For a from-scratch solver, type-checkable correctness.
- **Known pain.** Hiring depth in CAD geometry is in C++ not Rust. No mature commercial B-rep kernel ships a Rust binding (ACIS, Parasolid, and ODA SDKs are all C++ first). C++ FFI to ACIS / ODA is non-trivial — you pay it on every API boundary, which is why a Rust-primary core would be a tax on every inner-loop call.
- **Cost.** C++ and Rust toolchains are $0. **Primary IDE is VS Code (or Cursor) + clangd + CMake Tools + Qt extension pack + AI agent (Claude Code / Cursor / Copilot)** — that's where the AI-augmented dev workflow lives in 2026. **Visual Studio Enterprise reserved for 2-3 designated Windows-perf devs** (IntelliTrace, Concurrency Visualizer, advanced profiler) at $5,999 first / $2,569 renewal. JetBrains CLion (~€979/yr) available to taste as an alternative. AI dev tooling budgeted at **~$50/dev/mo blended** (Cursor Business $40/mo, Copilot Business $19/mo, Claude Code usage on top).
- **Verdict.** **Mismatch for the kernel; selective fit at the edges.** Confirms §2.4 — Rust earns its place in `net`, `script` host, `agent` (MCP), and new geometry algorithms. C++20 stays primary.
- Sources: [Fornjot](https://www.fornjot.app/), [Truck](https://github.com/ricosjp/truck), [CADmium](https://mattferraro.dev/posts/cadmium), [Zoo modeling-app](https://github.com/KittyCAD/modeling-app), [Figma WASM](https://www.figma.com/blog/webassembly-cut-figmas-load-time-by-3x/).

### 11.6 WebGPU + WebAssembly — browser CAD

- **Adopters.** **AutoCAD Web** — Autodesk transpiled a major part of AutoCAD's ~15M-line C++ via Emscripten to WASM; same engine as desktop. **Figma** — C++ → WASM via Emscripten, shipped WebGPU rendering in 2024. **Adobe Photoshop Web** — same pattern. **ODA Drawings inWEB / Visualize inWEB** — entire ODA C++ stack compiled to WASM. **CADmium** — Rust → WASM, three.js / WebGL today. **Tinkercad** — WebGL, JS-heavy. **Onshape** — NOT a WASM story: Parasolid runs native on AWS, browser only renders triangles via WebGL.
- **WebGPU baseline as of May 2026.** Chrome (since 113, 2023), Edge, Safari 26 (Sept 2025 — macOS Tahoe, iOS 26, visionOS), Firefox 141+ on Windows (July 2025), Firefox 145 on Apple Silicon. Firefox on Linux / Android still in progress. Babylon.js shows ~10× rendering speedup vs WebGL; WebGPU is the only path to in-browser compute shaders.
- **Known pain.** SharedArrayBuffer needs COOP / COEP headers — breaks embedding in customer intranets and some SaaS hosts. wasm32 caps at 4GB — large DWG / Revit forces wasm64 (narrower support). Filesystem assumptions need virtualizing via MEMFS / IDBFS. Binary size: stripped CAD WASM is tens of MB (need streaming compilation, dlopen-emulation code-splitting, `-Oz`). Debugging is dramatically worse than native.
- **Cost.** WebGPU / WebAssembly / WebGL2 are royalty-free W3C / Khronos browser APIs. **$0.** No conformance fee.
- **Verdict.** **Good fit for a Visualize-only browser companion now; the full-editor browser story is a multi-year program** matching AutoCAD Web's trajectory, not a Phase-1 launch deliverable.
- Sources: [AutoCAD WebAssembly InfoQ](https://www.infoq.com/presentations/autocad-webassembly/), [WebGPU baseline 2026](https://www.webgpu.com/news/webgpu-hits-critical-mass-all-major-browsers/), [Figma WebGPU](https://www.figma.com/blog/figma-rendering-powered-by-webgpu/), [Onshape architecture](https://www.onshape.com/en/blog/how-does-onshape-really-work).

### 11.7 ODA inWEB (Drawings inWEB, Visualize inWEB)

- **Adopters.** Drawings inWEB SDK opened to ODA members October 2024 — **no major shipping CAD product is publicly known to be on it for primary editing yet.** Members are building CDE / viewer apps. Visualize inWEB (`@inweb/viewer-visualize` on npm) is further along; several ODA members use it as a HOOPS / 3D-PDF viewer replacement. ODA's own *ODA Viewer* and the **VisualizeJS** demo viewer are the reference implementations.
- **Why.** Drawings inWEB is a **WASM transpilation of the C++ Drawings SDK** — file-format coverage is at parity with desktop Drawings SDK by construction.
- **Known pain.** Performance on large DWG (>200MB, dense annotation) lags desktop on initial-load and pan / zoom; browser-tab memory ceilings bite earlier than native. What's NOT at parity: full constraint engine, full LISP / .NET, plot / publish round-trip, certain custom-object proxies.
- **Cost.** Web/SaaS redistribution rights for inWEB begin at **ODA Sustaining ($7.5K first yr / $4.5K renewal)** — no per-deployment / per-seat royalty on top. Structurally cheaper than the Autodesk RealDWG path for a web product.
- **Verdict.** **Good fit for viewer / markup web companion in Phase 1; risky as the sole platform for full editing today.** Aligns with our native-Windows-first phasing in §5.
- Sources: [inWEB landing](https://www.opendesign.com/products/inweb), [Drawings inWEB SDK release](https://www.opendesign.com/blog/2024/october/drawings-inweb-sdk-oda), [@inweb/viewer-visualize npm](https://www.npmjs.com/package/@inweb/viewer-visualize).

### 11.8 CMake + Emscripten — C++ → WASM toolchain

- **Successful CAD-scale codebases on this exact toolchain.** AutoCAD Web (15M-line C++ → WASM via Emscripten — the headline case). Figma (3× initial load improvement when they moved off asm.js). Adobe Photoshop Web. ODA Drawings inWEB / Visualize inWEB. VTK / Kitware (ships documented Emscripten build with `VTK_WEBASSEMBLY_64_BIT` for >4GB models). CAD Exchanger Web.
- **Recurring failure modes.** Threading + SharedArrayBuffer requires COOP / COEP headers (breaks embeds, ads); 4GB pointer cap on wasm32 forces wasm64 for large models; filesystem virtualization (MEMFS / IDBFS) for every `fopen`; third-party C++ deps (Boost, ICU, OpenSSL) need patching for the Emscripten toolchain; binary size in the tens of MB needs streaming compilation + code-splitting; long compile / link cycles on kernel-sized code (hours for full rebuilds with LTO); GL / GLES → WebGL2 / WebGPU shader translation; debugging vastly worse than native.
- **Cost.** CMake (BSD-3), Emscripten (MIT / NCSA), Cargo (MIT / Apache-2.0), Vcpkg (MIT), Conan (MIT) — **all $0**. Kitware sells optional CMake support starting ~$2,500 pre-paid blocks; nice-to-have, not required.
- **Verdict.** **Good fit and well-trodden.** Every relevant precedent uses this toolchain; the failure modes are published and the playbook is public.
- Sources: [AutoCAD WebAssembly InfoQ](https://www.infoq.com/presentations/autocad-webassembly/), [Figma WebAssembly](https://www.figma.com/blog/webassembly-cut-figmas-load-time-by-3x/), [Emscripten pthreads](https://emscripten.org/docs/porting/pthreads.html), [VTK Emscripten](https://docs.vtk.org/en/latest/advanced/build_wasm_emscripten.html).

### 11.9 Summary verdict matrix

| Component | Verdict |
|---|---|
| 11.1 ODA SDKs (direct membership) | **Good fit** — matches BricsCAD / GstarCAD / ZWCAD / NanoCAD; removes ITC middleman |
| 11.2 ACIS B-rep kernel | **Locked** — AutoCAD ASM lineage = lossless DWG fidelity; commercial terms gated on §9 spike item 1b |
| 11.3 ODA MCAD SDK | **Not a kernel** — use as SolidWorks / Inventor / CATIA *importer* in Phase 2-3 |
| 11.4 Qt 6 desktop shell | **Good fit** — industry-standard; budget LGPL constraints or ~$5K/dev/yr commercial |
| 11.5 Rust selectively, not for kernel | **Confirmed** — Rust at the edges (`net`, `script`, `agent`); C++20 stays primary |
| 11.6 WebGPU + WASM browser | **Viewer now; full editor multi-year** — AutoCAD Web's trajectory, not a launch deliverable |
| 11.7 ODA inWEB | **Good fit for viewer; risky as sole platform** for full editing today |
| 11.8 CMake + Emscripten | **Good fit** — the exact playbook AutoCAD Web / Figma / ODA inWEB followed |

## 12. Collaboration architecture in detail

### 12.1 What the leaders actually shipped

- **Onshape (PTC)** — only mainstream parametric CAD with simultaneous multi-user editing of the same part. Built on an immutable, append-only operation history: every user action becomes a sequential change in the workspace, cloud is the single source of truth, no files. Branch-and-merge modeled on git (USPTO 10,691,844; also 10,002,150 and 10,503,721). Merge is feature-by-feature replay with conflict detection at the feature graph level. Works because parametric CAD has a semantic operation language (the feature tree).
- **ARES Kudo (Graebert)** — full DWG editor in browser + Automation server ("ARES Commander running remotely"). Public collaboration is View-Only Links, Comments, Markups, Version Compare — *not* concurrent co-editing in the Figma sense. "Multiple users in parallel by alternating editing and viewing sessions" with session handover. Closer to soft-locked session sharing with cloud sync on save. ARES 2027 (April 2026) adds the A3 AI agent.
- **AutoCAD Web** — fundamentally single-user, backed by Autodesk Docs. AutoCAD 2025.1 adds "Can Edit" share links + Activity Insights for audit + DWG comparison. Autodesk does *not* advertise concurrent geometry co-edit; they advertise serialized collaboration with rich audit and diff.
- **Vectorworks Cloud Services** — Cloud Document Reviewer (browser comment / measure / markup on shared sheet layers, returns to desktop). Concurrent geometry editing is via on-premises Project Sharing — file-based, not cloud-native.
- **Bricsys 24/7** — a CDE (document management + streaming viewer + workflow), not a co-editor.
- **Snaptrude** — AEC analog of Onshape, browser-based, real-time simultaneous editing without checkout. AI generation of LOD 300 models in 7–10 minutes (October 2025).
- **Figma** (canonical reference) — explicitly rejected both OT and pure CRDT. **Server-authoritative last-writer-wins per property.** Each document a tree-of-objects (HTML-DOM-like). Per-document server process over WebSockets. **Each field updates independently — concurrent edits to the same property produce A or B, never a merged value.** Fractional indexing (base-95 strings — average between siblings to insert) for ordering. Cycle-rejection for tree-reparent. Orphaned objects hidden client-side until reconciliation.

### 12.2 Why generic CRDTs lose on DWG

- DWG geometry is not a flat list — it's a spatially indexed graph with cross-references (block definitions, xrefs, layers, dimstyles, viewports).
- Tombstone GC blows up with millions of entities (Yjs scales to ~100k ops cleanly, OOMs at the millions-of-entity scale typical for an MEP riser DWG; Automerge OOMs on large transaction replay).
- Intent-preserving merge for "move this wall" requires understanding spatial constraints that generic CRDTs don't model.
- Recent academic work ("Geometry-Aware CRDTs", MDPI 2025) introduces geometric vector clocks + minimum bounding rectangles to capture spatial dependencies — still academic, not production.
- **The industry has converged on server-authoritative with domain-specific ordering, not generic CRDT.**

### 12.3 ActCAD's two-tier model — detailed

**Tier 1 (geometry edits): serialized op-log over the engine's mutation stream.**

- Every command (LINE, MOVE, ERASE, HATCH-modify, BLOCK-insert) is already an undoable transaction in the host today — that's the existing AcDb transaction. We promote that transaction to a network operation.
- Server linearizes all geometry ops. Optimistic UI on the client, server can reject ops that violate referential integrity (door-to-wall, dim-to-entity, hatch-boundary-to-geometry).
- The `db` op-stream defined in §3 is exactly the wire format — same stream serves invalidation, undo, replication, agent context, and audit.
- Presence + selection locks at the UI layer prevent dual edits before they become conflicts.
- Branch / version semantics (Onshape-style) deferred to Phase 3 — SMB drafters won't think in git branches; presence + soft-lock is the right Phase-2 UX.

**Tier 2 (annotations, comments, markups, layer properties, sheet titles, etc.): Figma-style LWW per property.**

- Each field updates independently; concurrent edits to the same field resolve to A-or-B, never a merge.
- Fractional indexing for any z-order / draw-order semantics.
- Cycle-rejection for reparenting tree ops (sheet → layout → viewport).
- This is also the right place for Yjs / Automerge if we ever want one — bounded scope, text-and-JSON shaped data, no spatial constraints.

### 12.4 What we copy, what we avoid

- **Copy** from Onshape: serialized op-log with cloud as single source of truth; explicit version model (snapshot-and-restore) even if we don't expose branch / merge initially.
- **Copy** from Figma: LWW per property; fractional indexing; cycle-rejection for tree ops; orphan-and-reconcile for clients out of sync.
- **Avoid** Onshape's "every user is a software engineer" branch model — SMB AEC users want soft-lock + presence + LWW on properties, not git workflows.
- **Avoid** ARES Kudo's soft-lock-only ceiling — go server-authoritative op-log on geometry from day 1 to leapfrog them.
- **Avoid** generic Yjs / Automerge for geometry — confine to non-spatial metadata where it's bounded.

### 12.5 Phasing for collaboration

- **Phase 1** — the `db` op-stream is the wire format from the first commit. No co-edit yet; the browser shell is viewer + markup; markups go through Tier 2 (LWW).
- **Phase 2** — Tier 1 turns on for 2D drawings with the cloud document service. Real-time co-edit ships with presence + soft-lock + LWW annotations.
- **Phase 3** — Tier 1 extends to 3D / BIM; explicit branch / snapshot exposed in the UI for what-if workflows.

Sources: [Figma multiplayer](https://www.figma.com/blog/how-figmas-multiplayer-technology-works/), [USPTO 10691844 (Onshape branch / merge)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10691844), [ARES 2027](https://architosh.com/2026/04/graebert-releases-ares-2027-ai-push-and-forma-integration/), [AutoCAD 2025.1 collaboration](https://www.autodesk.com/blogs/autocad/enhance-collaboration-and-save-time-with-autocad-2025-1/), [Vectorworks Cloud](https://www.vectorworks.net/en-US/newsroom/leveraging-vectorworks-cloud-services), [Bricsys 24/7](https://www.bricsys.com/247), [Geometry-aware CRDTs (MDPI 2025)](https://www.mdpi.com/2220-9964/14/12/468), [CRDTs go brrr (Joseph Gentle)](https://josephg.com/blog/crdts-go-brrr/).

## 13. Extensions and marketplace strategy

### 13.1 What the leaders actually shipped

- **Autodesk App Store + Autodesk Platform Services (APS, formerly Forge).** App Store accepts desktop add-ons (ObjectARX / .NET / LISP) *and* web apps using APS REST APIs. Initial review 24 hours, in-depth 2–3 days. Required artifacts: title, type, OS list, APS Client ID, screenshots, video, privacy policy URL (embedded in description AND inside the app itself). Monetization is publisher-controlled. **"Security review" is functional QA, not sandboxing-and-capabilities** — native plugins run with full process privileges.
- **Onshape App Store / Extensions.** The cleanest web-extension model in the industry because designed cloud-native from day one. **Two extension types only**: (1) UI extensions = an HTTPS page rendered in an iframe inside Onshape, (2) Action extensions = REST calls to the developer's server from Onshape's UI (context menu / toolbar). OAuth2 — Onshape is the client, the app is the server. Parameterized URLs inject documentId / workspaceId / userId / companyId. 180-second timeout on GET / POST actions. **No third-party code ever runs inside Onshape's process.**
- **BricsCAD Application Store + BRX.** BRX is BricsCAD Runtime eXtension — C / C++ and .NET API 100% source-compatible with AutoCAD ObjectARX. The value prop is "single code stream that runs on both BricsCAD and AutoCAD." SDK free, dev enrollment free. No web analog because BricsCAD has no web product to speak of.
- **SketchUp Extension Warehouse.** Ruby. Every extension shares the same Ruby VM. Sandboxing is by convention, enforced by RuboCop-SketchUp linting (no global variables, no monkey-patching, no `$LOAD_PATH` mutation, one root module per extension). Manual review + automated lint at submission. Encryption (.rbe) supports paid extensions.
- **Vectorworks Marketplace.** Binary trust model (partner vs unknown) with no code signing or sandboxing (per Vectorworks 2026 docs). Unknown-developer plugins disabled by default with a session warning. Security theater — users click "enable anyway" universally.
- **SolidWorks Solution Partner Program.** **No app store at all.** Mandatory 10% revenue share + sales disclosure to Dassault — publicly criticized by partners as imposing requirements without providing a storefront.
- **AutoCAD Web "extensions."** **LISP files only.** .lsp source uploaded to cloud profile. No .fas / .vlx compiled, no ARX, no .NET. ActiveX, 3D mesh / surface / solid creation, and most 3D-object modification are not available. Feature gap, not an architecture.

### 13.2 Architecture patterns

Two opposing models in production:

1. **In-process native plugins** (ObjectARX, BRX, Vectorworks SDK, SketchUp Ruby). Full power, no sandbox, distribution via store-as-shopfront. Security via developer reputation and manual review. Plugin-version-parity across host versions is the developer's problem.
2. **Out-of-process cloud apps** (Onshape, APS). iframe UI + OAuth REST. Sandboxed by the browser. Capability-scoped by OAuth scopes. No code runs inside the host process.

**Plugin parity across native and web does not exist in any shipped product.** AutoCAD Web is LISP-only with zero ARX / .NET. Onshape has no native at all. BricsCAD has BRX (native) and nothing web. The Onshape model gives you real security review + capability scoping, but it can only express what the REST API exposes — you cannot extend the geometry kernel from inside.

### 13.3 ActCAD's extension model

**Native desktop — keep BRX / ObjectARX compatibility.** SMB AEC switching from AutoCAD is ActCAD's value prop; native plugins are table stakes. Provide:

- **BRX-compatible API surface** — match BricsCAD's "single code stream that runs on AutoCAD" pledge.
- **AutoLISP compatibility shim** — covered in §2.5 and §5.
- **Authenticode-style code signing** + "verified publisher" badge in the store (Vectorworks-style binary trust is rejected).
- **Automated pre-publication scanning** (call-graph, suspicious API use, network egress detection) before manual review.

**Web — adopt the Onshape model.** Two extension types only:

- **UI extension** = an HTTPS page in an iframe inside the ActCAD web shell.
- **Action extension** = REST call to a developer-hosted server, OAuth2 scoped.

Define a stable extension manifest declaring capability scopes (read-drawing, write-drawing, network-egress, file-system, user-presence, plot, agent-tool-publish) — start with maybe six scopes, expand only when needed.

**Plugin parity = shared RPC surface, not shared binaries.** The `cmd` module in §3 defines an internal command / query API. Native plugins call it in-process (BRX / .NET). Web extensions call the same API via OAuth REST. Same scopes, same semantics, same audit trail. This is the only credible path to "write once, run on web and desktop" — and even then, only for plugins that don't need raw geometry-kernel access.

### 13.4 Marketplace policy

- Revenue share: tiered, not flat. Free for the first $5K/year of an extension's revenue, then 15% (Apple-equivalent for small business) to align with developer norms. Avoid the SolidWorks anti-pattern.
- Signing: required for both native and web.
- Categories: utilities, blocks / symbols, vertical packs (Architecture / MEP / Electrical / GIS), AI tools, integrations. AI-tool category needs a separate review track (see §14).
- Distribution: in-app store + web portal. Both list the same extensions.
- Agent-tool publishing: any extension that exposes MCP tools to the ActCAD agent runtime declares it in the manifest and goes through the AI-tool review track.

### 13.5 What to avoid (concrete anti-patterns)

- SolidWorks-style mandatory revenue share with no storefront.
- SketchUp's shared-VM-by-convention sandboxing — fine for SketchUp's installed base, dangerous for our new runtimes.
- Vectorworks-style binary trust — explicit capability scoping from day one, even if the initial buckets are coarse.
- Promising "write once, run everywhere" plugin parity — promise *API parity*, not *binary parity*.

Sources: [Autodesk App Store Getting Started](https://damassets.autodesk.net/content/dam/autodesk/www/pdfs/app-store-getting-started-guide.pdf), [Onshape Extensions](https://onshape-public.github.io/docs/app-dev/extensions/), [Onshape App Store](https://onshape-public.github.io/docs/app-store/), [BRX API](https://developer.bricsys.com/bricscad/help/en_US/CurVer/DevRef/source/BRX.htm), [SketchUp Extension Requirements](https://ruby.sketchup.com/file.extension_requirements.html), [RuboCop-SketchUp](https://github.com/SketchUp/rubocop-sketchup), [Vectorworks plug-in security](https://app-help.vectorworks.net/2026/eng/VW2026_Guide/Start/Third-party_plug-in_security.htm), [SolidWorks revenue share](https://www.fabbaloo.com/news/solidworks-partners-criticize-mandatory-revenue-share-and-sales-disclosure-requirements), [AutoCAD Web LISP](https://help.autodesk.com/view/ACADWEB/ENU/?guid=AutoCAD_Web_Help_File_Management_Lisp_html), [Figma plugin system](https://www.figma.com/blog/how-we-built-the-figma-plugin-system/).

## 14. AI and agent strategy in detail

### 14.1 What the leaders actually shipped

- **Autodesk** — "Autodesk AI" brand across products + public MCP servers as the agent substrate. Shipped:
  - **AutoCAD Smart Blocks** — Search-and-Convert (BCONVERT) finds geometry matching an existing block; 2026 adds text-to-block-attribute recognition. Detect-and-Convert (Tech Preview) scans the whole drawing and suggests block candidates.
  - **Markup Assist / Markup Import** — PDF / image markups → AI recognizes text commands (MOVE, COPY, DELETE) → proposes DWG edits.
  - **Activity Insights** — audit log + diff (not generative).
  - **Project Bernini → "Neural CAD"** — Bernini was the research model (10M shapes, ~3B params, text / sketch / image → 3D); now rebranded "Neural CAD" with the claim of editable CAD geometry in Forma / Fusion. No shipped product proves the editability claim yet.
  - **Forma (was Spacemaker)** — Site Automation: generative site design exploration with multi-objective evaluation.
  - **Autodesk Assistant + MCP** — **Revit 2027 ships a public MCP server (Tech Preview)** exposing six tool groups (model queries, sheet management, room management, schedules, exports, element ops): read everything, write a constrained set. **Fusion 2026 ships two MCP servers**: local Autodesk Fusion MCP (requires Fusion running, modeling + command execution) and remote Autodesk Fusion Data MCP (cloud, no Fusion required, data query). Both compatible with Claude Desktop / Cursor / VS Code / any MCP HTTP client.
- **BricsCAD AI** — AI Predict (ML-based ribbon command suggestion), AI Assistant (V26.2.03), Blockify (repetition detection for file-size reduction), Drawing Health (geometry cleanup), BIMIFY (AI classification of free-form 3D → IFC elements), auto-parametrize. **No public MCP server yet.**
- **Graebert ARES 2027** — A3 AI agent (built on OpenAI APIs) that selects / creates / modifies DWG entities; voice input in Kudo Professional; AI block generation; AI MText assistant. Deepest "agent in the inner loop" surface shipped on a DWG editor in 2026.
- **Adobe Firefly in Illustrator** — Generative Recolor (text-prompt palette generation across selected vector art) and Text-to-Vector Graphic (.svg output, then editable). Adjacent pattern: **AI outputs are first-class editable vector primitives, not raster overlays.** Trained on licensed Adobe Stock + public domain.
- **AI-native AEC startups.** Snaptrude — RFP → LOD 300 model in 7–10 min (adjacencies / zoning / codes / climate). Hypar — pivoted from text-to-BIM (Python / C# → IFC) to "suggestions" (Hypar 2.0, Jan 2025) focused on space planning, automatic editable masses / grids / columns / furniture from spatial programs. They publicly admitted text-to-BIM via chat alone was the wrong abstraction. Magicplan — mobile AR floor-plan capture.

### 14.2 The two architectural patterns

1. **AI as a tool** — inline, scoped, deterministic. Smart Blocks, Markup Assist, BIMIFY, AI Predict, Firefly Recolor. User invokes a specific AI-assisted command. AI suggests, user accepts. Undo is normal command undo. No persistent agent, no chat surface inside the canvas. **This is what's actually shipping and working.**
2. **AI in the inner loop** — agent + chat panel + MCP. Autodesk Assistant in Revit 2027, ARES A3, Fusion MCP. Chat panel converts NL → host command sequence. MCP is the architectural commitment — any LLM client can drive the host. Host exposes a curated tool surface. **Tech Preview status everywhere; no shipping CAD MCP server has documented transaction / undo semantics publicly.**

The closest validated pattern for "transactional, undoable, permission-scoped command surface" is actually **Figma plugins**: every plugin op is a Figma undo transaction; plugins must explicitly support undo; plugins run in QuickJS (compiled to WASM) inside an iframe sandbox; permissions declared in the manifest (currentuser, activeusers, fileusers, payments, teamlibrary). Not an MCP, but the cleanest shipped example of the contract.

### 14.3 Where the current generation goes wrong

- **Bernini-style generative CAD produces non-editable geometry.** That's why Hypar pivoted — chat-to-BIM gives a model that looks right but isn't tied to a parametric history a human can edit later. Autodesk's "Neural CAD" claim is unproven in product.
- **MCP without transactional semantics produces unfixable agent mistakes.** If an agent bulk-edits 5,000 wall parameters and corrupts the schedule, undo has to undo all 5,000 as one transaction.
- **Chat-as-primary-UI loses spatial context.** Hypar's lesson: "it's very hard to design anything real through a chat prompt." Spatial editing wants spatial UX.
- **Activity Insights is not AI.** Autodesk lumps audit logging into the AI brand — don't confuse marketing taxonomy with shipped intelligence.

### 14.4 ActCAD's three-step strategy

**Step 1 — Ship "AI as a tool" first (Phase 1).** Three commands that win adoption fast and have clear scope:

- **Markup Assist analog** — PDF redline → DWG edit proposals.
- **Smart Blocks analog** — block detection across drawings (BCONVERT-equivalent).
- **Drawing Health** — layer / standards cleanup, lineweight normalization, duplicate-entity removal.

Each command produces deterministic, undoable suggestions. No chat. No MCP yet. This is the floor every shipping competitor is already at; we have to match it before we can talk about anything more ambitious.

**Step 2 — Ship the MCP server as the integration surface, not the primary user UI (Phase 1–2).** Mirror Fusion 2026's split:

- **Local MCP server** — requires ActCAD running, executes commands inside the host transaction, full read + write.
- **Remote MCP data server** — cloud, no host required, read-only DWG metadata / sheet / layer / block queries.

Tool groups along Revit 2027 lines: entity queries, layer / style management, block ops, sheet / layout management, plot / export, drawing health. Compatible with Claude Desktop / Cursor / VS Code / any MCP HTTP client.

**The single most important architectural commitment: every MCP tool call is exactly one transaction in the host's existing undo stack.** No public CAD MCP has documented this. Making it explicit — in the docs, in marketing, in the developer portal — is the differentiator that compounds. Permission scoping at the tool level (read-only / write / plot / file-system-egress) is declared in the MCP server's tool descriptions.

**Step 3 — Conditional generative-CAD (Phase 3).** Only ship "from prompt to drawing" features when editable round-tripping through the parametric / feature system is proven. Until then, stay on AI-suggestions-as-editable-primitives (Firefly pattern: vectors out, editable). This is the lesson Hypar learned the expensive way; we should learn it for free.

### 14.5 Agent tool design rules

- Every tool maps to one `cmd` invocation in the host.
- Every tool call = one undo group.
- Every tool declares its scope (read / write / file-egress / network-egress) and its blast radius (single-entity / drawing-wide / cross-drawing).
- Dry-run is supported for every write tool — agent can preview without commit.
- Rate-limited per session and per scope.
- Audit log retained server-side for every tool call (input, output, transaction id, scopes used) — this is also the training data for the next iteration.
- Tool catalog is versioned; clients negotiate capabilities on connect.

### 14.6 What we avoid

- The Bernini hype path — don't promise generative CAD geometry until editable parametric round-tripping is proven.
- Chat-in-canvas as the primary AI UX (Hypar pivoted for this reason).
- Over-indexing on a single LLM vendor — MCP exists exactly to keep that open.
- Shipping an MCP server without the single-undo-transaction commitment.
- Confusing audit / diff features with "AI" in customer-facing positioning.

Sources: [AutoCAD AI features](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/What-are-the-AutoCAD-AI-driven-features.html), [AutoCAD 2026](https://www.autodesk.com/blogs/autocad/autocad-2026/), [Project Bernini](https://www.research.autodesk.com/projects/project-bernini/), [Autodesk MCP Servers](https://www.autodesk.com/solutions/autodesk-ai/autodesk-mcp-servers), [Fusion MCP announcement](https://www.engineering.com/autodesk-announces-fusion-mcp-servers-and-more-ai-updates/), [Revit 2027 MCP Tech Preview](https://help.autodesk.com/cloudhelp/2027/ENU/Revit-WhatsNew/files/GUID-68D8FE6D-C5B0-4503-AE27-02C715BAC25B.htm), [Revit 2027 MCP analysis](https://archbim.cloud/en/blog/revit-2027-ai-assistant-mcp-new-features), [ARES 2027 A3](https://architosh.com/2026/04/graebert-releases-ares-2027-ai-push-and-forma-integration/), [BricsCAD AI](https://www.bricsys.com/bricscad/features/ai-driven-tools), [Adobe Firefly Vector Recolor](https://blog.adobe.com/en/publish/2023/04/20/introducing-vector-recoloring-with-adobe-firefly), [Snaptrude AI](https://www.snaptrude.com/), [Hypar 2.0](https://aecmag.com/features/hypar-2-0/), [Hypar text-to-BIM lesson](https://aecmag.com/ai/hypar-text-to-bim-and-beyond/), [Snyk MCP CAD list](https://snyk.io/articles/9-mcp-servers-for-computer-aided-drafting-cad-with-ai/), [Figma plugin docs](https://developers.figma.com/docs/plugins/how-plugins-run/).

## 15. Cost of usage — third-party stack, shells, tools

Per-component cost data appears inline in each §11 subsection. This section rolls those up into a single reference table and three modeled annual budget envelopes at typical Phase-1 / Phase-2 / Phase-3 team sizes.

**All dollar figures are vendor-published or reported secondary-source estimates as of late 2025 / early 2026. Treat any opaque-OEM number as a directional placeholder — they need a live procurement conversation, not a guess.**

### 15.1 Unified pricing reference

| Component | License model | Public price | Per-seat / royalty | Source |
|---|---|---|---|---|
| **ODA — Limited Commercial** | Annual membership | $3K first yr / $2.25K renewal | None — but **100-seat cap** | [opendesign.com/pricing](https://www.opendesign.com/pricing) |
| **ODA — Pro / Sustaining** | Annual membership | **$7.5K first / $4.5K renewal** | **None** — unlimited + Web/SaaS rights | [opendesign.com/pricing](https://www.opendesign.com/pricing) |
| **ODA — Enterprise / Founding** | Annual membership | $37.5K first / $18K renewal | None — adds source code + Git | [opendesign.com/pricing](https://www.opendesign.com/pricing) |
| **ODA extensions** (BimRv / BimNw / MCAD / Civil / Scan-to-BIM) | Add-on, Sustaining+ | $5K–$10K/yr each (reported) | None | [ODA FAQ](https://www.opendesign.com/faq/membership) |
| **Spatial / Dassault ACIS — Initial OEM license** | One-time OEM fee | **Opaque — industry estimate $150K–$300K, procurement-gated** | One-time, gates access to headers + libs | [Spatial ACIS](https://www.spatial.com/solutions/3d-modeling/3d-acis-modeler) |
| **ACIS — Annual maintenance** | % of license fee | **15–20% of initial fee** (~$30K–$60K/yr typical) | Required for updates, hotfixes, CTC access | [Spatial support](https://www.spatial.com/support) |
| **ACIS — Per-deployment royalty** *(primary ask)* / **per-seat** *(fallback only)* | Volume-tiered | **Opaque, tiered** | **Per-deployment is the locked negotiating ask** — ~10× cheaper than per-seat over 3 years at ActCAD scale. Full comparison math, gotchas, and negotiating sequence in **§15.1.1**. | — |
| **ACIS — Component modules** (Local Ops, Healing, Defeaturing, Polyhedral, AGM, HLR, Lop) | Each priced separately on top of base | **Opaque, per-module** | A "complete" ACIS for our scope typically needs 3–5 modules; scope module list before signing | [ACIS components](https://www.spatial.com/products/3d-acis-modeling) |
| **ACIS — CTC support hours** | Bundled + overage | ~20–40 hr bundled; $300–$500/hr beyond (estimate) | Engineering-level support from Spatial's Corporate Technical Consulting | — |
| **ACIS — Source escrow** *(optional, recommended)* | Annual | ~$5K–$15K/yr typical | Business-continuation insurance if Spatial discontinues | — |
| **Siemens Parasolid** *(not chosen)* | OEM | Opaque | n/a | [Parasolid](https://plm.sw.siemens.com/en-US/plm-components/parasolid/) |
| **Qt for Small Business — App Dev** | Sub, per-dev | **€530/yr Pro, USD 618/yr Ent** | n/a — but **≤€1M revenue cap, max 3 licenses** | [Qt SBE](https://www.qt.io/development/qt-for-small-business) |
| **Qt — Application Development (standard)** | Sub, per-dev | ~$3,624/yr Pro, $3,948–$4,660/yr Ent | n/a | [Qt pricing](https://www.qt.io/pricing) |
| **Qt — Device Creation / Mobile / WASM add-ons** | Sub, per-dev | +30–60% over App Dev | n/a | [Qt pricing](https://www.qt.io/pricing) |
| **Qt LGPL** | LGPL v3 | $0 | n/a — **but no static linking, no signed iOS** | [Qt LGPL](https://www.qt.io/development/open-source-lgpl-obligations) |
| **CMake / Emscripten / Cargo / Vcpkg / Conan** | OSS | $0 | None | — |
| **Kitware CMake support (optional)** | Pre-paid | $2,500 / 12 mo | None | [Kitware support](https://www.kitware.com/commercial/support/) |
| **WebGPU / WebAssembly / WebGL2** | W3C / Khronos open | $0 | None | — |
| **Tauri** (if used for launcher app) | MIT / Apache-2.0 | $0 | None | — |
| **Electron** (rejected for editor) | MIT | $0 | None | — |
| **.NET 8 / NativeAOT** | MIT | $0 | None | [.NET free](https://dotnet.microsoft.com/en-us/platform/free) |
| **MCP protocol + SDKs** | MIT, donated to Linux Foundation | $0 | None | [MCP](https://www.anthropic.com/news/model-context-protocol) |
| **AutoLISP runtime** | **No commercial library exists** — build in-house | $0 (ECL embedded LGPL viable starting point) | None | [AutoLISP history](https://en.wikipedia.org/wiki/AutoLISP) |
| **Clerk Auth** | Per-MAU, vendor-published | Free ≤10K MAU; $25/mo base + $0.02/MAU | n/a | [Clerk pricing](https://clerk.com/pricing) |
| **Auth0** | Per-MAU | $150/mo for 500 MAU; escalates fast — enterprise $30K+/yr | n/a | [Auth0 pricing](https://auth0.com/pricing) |
| **Stripe Payments** | % of volume | **2.9% + $0.30** domestic card | n/a | [Stripe pricing](https://stripe.com/pricing) |
| **Stripe Billing** | % of volume | 0.7% of billing volume | n/a | [Stripe Billing](https://stripe.com/billing/pricing) |
| **AWS GPU — g4dn.xlarge (T4)** | On-demand | **$0.526/hr** ($4,608/yr 24×7) | n/a | [AWS GPU](https://handbook.vantage.sh/aws/reference/aws-gpu-instances/) |
| **AWS GPU — g5.xlarge (A10G)** | On-demand | **$0.916/hr** ($8,024/yr 24×7) | n/a | [AWS G5](https://aws.amazon.com/ec2/instance-types/g5/) |
| **JetBrains All Products Pack** | Sub, per-dev | **€979/yr (~$1,050)** | n/a — yr-2 ~20% off, yr-3 ~40% off | [JetBrains](https://www.jetbrains.com/store/) |
| **Visual Studio Enterprise** *(2-3 perf devs only)* | Sub, per-dev | $5,999 first / $2,569 renewal | n/a — reserved for Windows deep-profiling work | [VS pricing](https://visualstudio.microsoft.com/vs/pricing/) |
| **VS Code + clangd + Qt extensions** *(primary IDE)* | OSS | **$0** | n/a | [VS Code](https://code.visualstudio.com/) |
| **AI dev tooling** (Claude Code / Cursor / Copilot blended) | Per-dev sub | **~$50/dev/mo** ($600/yr); Cursor Business $40, Copilot Business $19, Claude Code usage on top | n/a | [Cursor pricing](https://cursor.com/pricing), [Copilot Business](https://github.com/features/copilot) |
| **GitHub Enterprise Cloud** | Sub, per-dev | $21/dev/mo ($252/yr) | n/a — 50-100 seat min on annual | [GitHub pricing](https://github.com/pricing) |
| **GitHub Advanced Security** | Sub, per-dev | +$19/dev/mo ($228/yr) | n/a | [GitHub pricing](https://github.com/pricing) |
| **GitHub Actions (standard)** | Per-minute | **$0.006/min** (2-core Linux, effective Jan 2026); 50K min/mo bundled in Enterprise Cloud | n/a | [Actions pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing) |

### 15.1.1 ACIS royalty model — per-deployment vs per-seat

The single largest variance in the ACIS commercial envelope is the **royalty model** (line item 3 in §15.1's cost-structure table). The two models can differ by ~10× over a 3-year window for an SMB-volume / low-price product like ActCAD. This subsection is the negotiating reference for Spike 1b.

**The two structures, plainly:**

| | Per-seat royalty | Per-deployment royalty |
|---|---|---|
| What triggers payment | Each active licensed user, recurring (annual) | Each unique install, typically one-time |
| Scales with | Total customer base × time | New installs per year |
| Risk shape | Linear forever; punishes long-lived perpetual customers | Front-loaded; amortizes over seat lifetime |
| Friendly to | Low-volume / high-price MCAD products (Plasticity, Shapr3D, KeyShot) | High-volume / low-price SMB CAD products (ActCAD, BricsCAD-class) |
| Reporting overhead | Per-customer active seat counts each quarter | Install events with unique deployment IDs |

**Illustrative math at ActCAD scale.** Hypothetical $50 royalty unit, 30,000 installed seats today, 3,000 new installs / year, 5-year average seat lifetime. Numbers are illustrative — actual rates come from Spatial's term sheet — but the relative shape holds:

| Year | Per-seat ($50/seat/yr) | Per-deployment ($50/install, one-time) |
|---|---|---|
| Y1 | 30,000 × $50 = **$1.50M** | 3,000 × $50 = **$150K** |
| Y2 | 33,000 × $50 = **$1.65M** | 3,000 × $50 = **$150K** |
| Y3 | 36,000 × $50 = **$1.80M** | 3,000 × $50 = **$150K** |
| **3-yr total** | **$4.95M** | **$450K** |

**~10× difference.** This is why the Phase 2 / 3 royalty placeholders in §15.2 assume per-deployment. If Spike 1b returns a per-seat-only offer at comparable headline rates, the Phase 3 envelope grows by roughly $1M+.

**When per-seat actually wins** (none of these describe ActCAD, but document them so the comparison is honest):
1. **High-price low-volume MCAD products.** Plasticity / Shapr3D / KeyShot — selling $500–$5K perpetuals at 5K–50K seats. A $50/seat royalty is 1–10% of revenue and reporting is simpler.
2. **Pure subscription with high churn.** 40%+ annual churn — per-seat self-terminates with the lapsed seat; per-deployment is sunk cost regardless.
3. **Single-customer enterprise / site license.** One customer, hundreds of seats — Spatial usually offers a flat site fee that beats both row-level models.

**Contract gotchas that change the actual cost** (must be in writing before signing):
- **Per-deployment "unique" definition.** Does reinstall on the same machine count? Hardware change? VM migration? OS reinstall? Vague language turns "one-time" into "recurring." Push for *machine-fingerprint or install-ID-based* with reinstalls on same machine excluded.
- **Per-seat "seat" definition.** Lapsed-subscription seats still counted for the quarter? Concurrent vs named users? Trial / evaluation seats counted? 30-day grace period for inactive seats?
- **Volume tier breakpoints.** A $50/seat headline might drop to $20 above 50K seats. Per-deployment might have no tiers, or steep tiers. **Tier shape matters more than the headline rate.**
- **Minimum annual royalty floor.** Most OEM contracts carry a minimum regardless of volume — sets the actual cost at low volumes. Push for $25K–$50K floor rather than $100K+.
- **Subscription vs perpetual treatment.** Some contracts charge differently for subscription vs perpetual customers. Ask explicitly.
- **Audit + true-up cadence.** Quarterly reporting + annual true-up is standard; some contracts allow annual reporting which reduces our internal overhead (line item 9 in §15.1).
- **Education / trial / internal-QA carve-outs.** Excluded from royalty count? Get it written.

**The negotiating ask sequence for Spike 1b** (ordered by priority):
1. **Per-deployment royalty, one-time**, with a precise unique-deployment definition (machine-fingerprint based, same-machine reinstalls excluded).
2. **Volume-tiered**, with breakpoints at 5K / 25K / 100K cumulative deployments and a meaningful tier decay (e.g., $50 → $30 → $15 → $5).
3. **Carve-outs**: trials, education, internal QA, evaluation copies all excluded from royalty count.
4. **Annual minimum floor** as low as possible — target $25K–$50K rather than $100K+.
5. **Per-seat as a fallback only** if per-deployment isn't on offer — and only with a steep volume curve (e.g., $50 → $5 above 50K seats) where 5-year amortized cost beats their per-deployment alternative.

**The decision rule.** Accept per-seat only if Spatial refuses per-deployment AND the 5-year amortized per-seat cost (using realistic seat-count + churn projections) is lower than the per-deployment alternative they would have offered. That comparison — both quotes side by side — is the negotiating leverage. **The plan locks in per-deployment as the default ask, with per-seat documented as an explicit fallback decision, not an accident.**

### 15.2 Modeled annual budget envelopes

Three scenarios sized to the engineering org in §5's phasing. **These are modeled rollups, not committed numbers.** Assumptions: ODA Sustaining from year 1 (Web/SaaS rights for inWEB), Qt commercial App Dev Enterprise standard tier (Small Business eligibility unlikely at Jytra's scale), **ACIS as the 3D kernel under a Spatial OEM contract** with the cost structure in §15.1 (initial fee + maintenance + royalty + module fees), **VS Code primary + Visual Studio Enterprise for 2-3 designated Windows-perf devs only**, AI dev tooling at ~$50/dev/mo blended.

> **ACIS line items are procurement placeholders** pending §9 spike item 1b's term sheet. Industry-estimate values are used as directional anchors only — the actual numbers come from the NDA conversation with Spatial. See §15.3 for modeled-vs-opaque split.

#### Phase 1 — 8 engineers (months 0–12)

| Line item | Year 1 |
|---|---|
| ODA Sustaining (incl. inWEB rights) | $7,500 |
| ODA Revit add-on (BimRv Standard) | $5,000 |
| Qt commercial — App Dev Enterprise (8 devs × $4,000) | $32,000 |
| **ACIS — initial OEM license** *(placeholder — opaque, §9 spike 1b)* | $200,000 |
| **ACIS — annual maintenance** *(placeholder — 17.5% of license)* | $35,000 |
| **ACIS — component modules** *(placeholder — Local Ops + Healing + Defeaturing)* | $50,000 |
| **ACIS — royalty** *(Phase 1 is internal beta — minimal seats, placeholder)* | $5,000 |
| **ACIS — source escrow** *(recommended)* | $10,000 |
| **Visual Studio Enterprise (2 perf devs × $5,999)** | $11,998 |
| VS Code + clangd + Qt extensions (rest of team) | $0 |
| **AI dev tooling (8 devs × ~$50/mo)** | $4,800 |
| JetBrains All Products Pack (4 devs to taste × $1,050) | $4,200 |
| GitHub Enterprise Cloud (8 × $252) | $2,016 |
| GitHub Advanced Security (8 × $228) | $1,824 |
| GitHub Actions large runners + cache | $5,000 |
| AWS dev infra (compute + storage + 1× g4dn dev box) | $8,000 |
| Auth / billing (nominal — Clerk free tier, Stripe test mode) | $1,000 |
| **Phase 1 yr 1 stack + tools + cloud total** | **~$383,300** (incl. ~$300K ACIS one-time + recurring) |

#### Phase 2 — 20 engineers (months 12–24, GA at month 24)

| Line item | Year 2 (renewal-mode where applicable) |
|---|---|
| ODA Sustaining renewal | $4,500 |
| ODA extensions (BimRv + MCAD + Civil) | $15,000 |
| Qt commercial — App Dev Enterprise (20 × $4,000) | $80,000 |
| Qt mobile / WASM add-ons (+40% on 5 web/mobile devs × $4,000) | $8,000 |
| **ACIS — annual maintenance** *(recurring)* | $35,000 |
| **ACIS — component modules renewal** | $50,000 |
| **ACIS — royalty** *(GA at month 24 — placeholder, assume 2,000 deployments × $50)* | $100,000 |
| **ACIS — source escrow** | $10,000 |
| **ACIS — CTC support hours overage** *(placeholder)* | $15,000 |
| **Visual Studio Enterprise (3 perf devs × $2,569 renewal)** | $7,707 |
| **AI dev tooling (20 devs × ~$50/mo)** | $12,000 |
| JetBrains All Products Pack (10 devs to taste × $840 yr-2 disc.) | $8,400 |
| GitHub Enterprise Cloud (20 × $252) | $5,040 |
| GitHub Advanced Security (20 × $228) | $4,560 |
| GitHub Actions + build infra | $15,000 |
| AWS production cloud (compute + 4× g5 streaming + storage + egress) | $60,000 |
| Auth (Clerk B2B, ~25K MAU) | $12,000 |
| Stripe Billing (assume $200K ARR × 0.7%) | $1,400 |
| Stripe Payments (assume $200K × 2.9%) | $5,800 |
| **Phase 2 stack + tools + cloud total** | **~$449,400** (incl. ~$210K ACIS recurring + royalty at GA) |

#### Phase 3 — 30 engineers (months 24–36)

| Line item | Year 3 |
|---|---|
| ODA — upgrade to Founding (source access) | $37,500 first / $18K renewal |
| ODA extensions (full extension set) | $30,000 |
| Qt commercial (30 × $4,000) | $120,000 |
| Qt mobile / iOS / Android / WASM add-ons (10 devs × $4,000 × 50%) | $20,000 |
| **ACIS — annual maintenance** | $35,000 |
| **ACIS — component modules renewal** *(may add Polyhedral + AGM for full 3D + BIM)* | $75,000 |
| **ACIS — royalty** *(at scale — placeholder, 10,000 deployments × $50)* | $500,000 |
| **ACIS — source escrow** | $10,000 |
| **ACIS — CTC support + WASM custom engineering** *(if mobile / web needs full ACIS)* | $40,000 |
| **Visual Studio Enterprise (3 perf devs renewal)** | $7,707 |
| **AI dev tooling (30 devs × ~$50/mo)** | $18,000 |
| JetBrains All Products Pack (12 devs to taste × $630 yr-3 disc.) | $7,560 |
| GitHub Enterprise Cloud (30 × $252) | $7,560 |
| GitHub Advanced Security (30 × $228) | $6,840 |
| GitHub Actions + build infra | $30,000 |
| AWS production (compute + 12× g5 streaming + CDN + egress at scale) | $200,000 |
| Auth (Clerk B2B, ~100K MAU) | $30,000 |
| Stripe Billing + Payments (assume $2M ARR) | $73,000 |
| **Phase 3 stack + tools + cloud total** | **~$1,255,700** (incl. ~$660K ACIS recurring + royalty at scale; royalty scales with deployments) |

### 15.3 What's modeled vs what's opaque

- **Modeled (vendor-published):** ODA, Qt, all OSS tooling, AWS GPU, Clerk, Stripe, JetBrains, Visual Studio, GitHub.
- **Opaque (needs procurement conversation — placeholders pending §9 spike item 1b):** ACIS initial license + maintenance + per-module fees + royalty model + DELA, Auth0 enterprise, Microsoft Unified Support. **All ACIS numbers in the rollup are industry-estimate placeholders, not vendor quotes.**
- **Variable with revenue / users:** Stripe (% of volume), Clerk (per-MAU), AWS (per-instance-hr × utilization).

### 15.4 Commercial commitments and cost-driven decisions

ActCAD is a closed-source commercial product. The license tier on every component is chosen accordingly — paid where standard commercial practice (static linking, code-signing, private modifications, unlimited seats) requires it, free where the OSS license cleanly permits it for closed-source use.

1. **ODA Sustaining from day 1 — LOCKED.** $7.5K first / $4.5K/yr renewal for unlimited commercial seats + inWEB Web/SaaS redistribution rights with **no per-seat royalty** is the single best-value line item in the entire stack. Limited Commercial's 100-seat cap is a footgun at our scale; Founding (~$37.5K) considered in Phase 3 for source + Git access + business-continuation rights.
2. **Qt 6 commercial — LOCKED.** Standard Application Development Enterprise per developer. LGPL is *not* viable for ActCAD: static linking is forbidden under LGPL v3, code-signed iOS distribution can't satisfy the user-relinking clause, and we need to keep our Qt modifications private. Small Business tier is almost certainly not available at Jytra's revenue. §9 spike item 6 negotiates the multi-year quote; target 15–35% below first quote per Vendr-reported norm.
3. **ACIS commercial OEM contract — LOCKED as the kernel choice; commercial terms OPEN pending Spike 1b.** Rationale: AutoCAD's 3D solids are stored as ASM (ACIS fork) SAT blobs in DWG; only ACIS round-trips them without drift. ActCAD already uses ACIS today through IntelliCAD; this decision puts the contract directly in our name and removes the IntelliCAD middleman. Cost shape is initial OEM license + 15–20% annual maintenance + royalty + per-module fees + DELA — see §15.1. **Royalty model — per-deployment is the LOCKED negotiating ask** (per-seat documented as fallback only; ~10× cost variance over 3 years at ActCAD scale — see §15.1.1 for the comparison math and full negotiating sequence). **All §15.2 ACIS line items are industry-estimate placeholders pending the term sheet from Spatial.** Once that lands, Phase-1 budget firms up to a real number.
4. **VS Code (or Cursor) primary, Visual Studio Enterprise reserved — LOCKED.** Primary IDE is **VS Code + clangd + CMake Tools + Qt extension pack + AI agent (Claude Code / Cursor / Copilot)** for the entire C++ team — that's where the AI-augmented dev workflow lives in 2026. Visual Studio Enterprise (~$6K first / $2.6K renewal) is **reserved for 2-3 designated Windows-perf devs** for IntelliTrace, Concurrency Visualizer, and advanced profiler work into ODA / Qt call stacks. JetBrains CLion available to taste as an alternative. Saves ~$12K Phase 1, ~$18K Phase 2, ~$30K Phase 3 versus the original plan of buying VS Enterprise for the whole C++ team.
5. **AI-augmented team math.** Qt's commercial license is per-human-developer; AI agents are tools, not licensees. AI doesn't reduce the per-seat *rate*, it reduces the per-seat *count* — a 12-dev AI-augmented Phase-2 team can ship what 20 devs shipped pre-AI, so Qt's line drops from $80K to ~$48K via headcount, not via license loophole. Same logic applies to ODA seats (unlimited under Sustaining — no effect), GitHub / Visual Studio / JetBrains (per-human, scale with headcount). Budget for AI dev tooling itself at **~$50/dev/mo blended** (Cursor Business $40, Copilot Business $19, Claude Code on top).
6. **All build / runtime tooling stays free.** CMake, Emscripten, Cargo, Vcpkg, Conan, WebGPU / WebAssembly, .NET 8 / NativeAOT, MCP, Tauri (launcher app only) are all permissive OSS — no commercial concern for our use.
7. **AutoLISP must be built in-house.** No commercial runtime exists to license; every IntelliCAD-class vendor rolls its own. Phase-1 LISP team is a real headcount commitment, not a vendor decision.
8. **Total stack + tools + cloud envelope** — roughly **~$383K Phase 1, ~$449K Phase 2, ~$1.26M Phase 3** (Phase-3 royalty scales with deployment volume). The ACIS line is the single largest cost driver and the single largest source of variance — locking the term sheet in Spike 1b is what converts these from placeholders to commitments. Salary still dwarfs the stack cost at every phase, but the kernel-commercial conversation is a real one that procurement / legal own from Spike 1b onward.

## 16. Memory architecture — designing for headroom from day 1

> **Executive summary.** Full engineering reference is in **`docs/memory-architecture.md`** (~900 lines: concurrency model, KAL contract, eviction protocol, failure modes, CI gates, anti-patterns, IntelliCAD-migration teaching, phase-by-phase rollout, glossary, references). Read this section for the strategic picture; read the companion document before writing code that touches `db`, `geom`, `render`, or any cache.

The CAD operating model is simple to state and hard to make fast: **open the drawing once, hold it entirely in memory, do all reads and writes against that in-memory state, write back to disk on save.** This is what AutoCAD has done since 1982 and what every serious DWG editor still does today. The model itself is correct and not up for debate. What turns it into a bottleneck is that "in memory" is doing more work than people think — a 250MB DWG can expand to several GB of working set once you add the kernel's body graph, the tessellation cache, spatial indexes, the undo log, and the renderer's GPU buffers. If the architecture doesn't budget that memory and police access patterns from commit 1, you ship a product whose user reviews say *"moderately large drawings frequently get stuck"* — the exact reputation the current ActCAD inherited from IntelliCAD and the exact reputation this re-architecture exists to escape.

This section is the architectural commitment for how we avoid that. It is written in plain language by design: every engineer joining the team should be able to read it once and know what the rules are.

### 16.1 The five layers of memory in a live CAD session

People talk about "the drawing in memory" as if it were one thing. It's really five layers, each with its own size, owner, and eviction policy. Get this picture in your head and the rest of this section follows.

| Layer | What lives here | Typical size (250MB DWG with 3D solids) | Owner module | Evictable under pressure? |
|---|---|---|---|---|
| **1. DWG database** | Entities, handles, layers, blocks, xrefs, dimstyles, attributes — the user's actual work | 400–800 MB | `db` | **Never** — single source of truth |
| **2. ACIS kernel bodies** | The `ENTITY` graph for every 3D solid the user has touched | 200 MB – 2 GB | `geom` via KAL | **Partial** — lazy-loaded on first touch; attributes lazy beyond that |
| **3. Tessellation cache** | Triangles + GPU buffers for everything currently being drawn | 500 MB – 4 GB | `render` | **Yes** — LRU evict; regenerate on demand |
| **4. Spatial indexes** | R-tree / BVH for hit-test, snap, frustum-cull, selection-window | 50–200 MB | `db` + `render` | **Rebuildable** — recompute from `db` |
| **5. Undo / op-log** | Delta records for reversal + co-edit replication + agent context + audit | 100–500 MB over a long session | `db` | **Truncatable** — drop oldest beyond threshold |

**The one rule:** Layer 1 (`db`) is sacred and never evicted. Everything above it is a cache or a derived view, and the budget says how much memory we'll spend on each. When pressure hits, the eviction order is fixed: tessellation (3) first → spatial indexes (4) → lazy-loaded ACIS attributes (2). Layer 1 stays put. The user's work is never at risk from a memory-management decision.

### 16.2 Eight architectural commitments that keep responsiveness flat as drawings grow

These are the design rules, in priority order. Each prevents a specific class of bottleneck that other CAD products live with.

#### 1. The `db` is the only owner of drawing state. Everything else is a cache.

If `render` needs triangles, `render` owns the triangle cache and `db` doesn't know about it. If snap needs an acceleration structure, snap rebuilds it from `db` and discards it. This is what makes Layer 1 / Layer 3–5 separation real instead of theoretical. The reason it matters in practice: when something is wrong in memory, you always know who to ask, and you can blow away every cache without losing the user's work. Single-source-of-truth is not a slogan; it's a recovery strategy.

#### 2. One write path, many read paths, never blocked by each other.

`db` mutations are serialized through one transaction queue on a worker thread. Reads — render, hover, snap, selection, agent query, property panel — go against the committed state via a **copy-on-write snapshot**. **No reader ever waits on a writer.** This is the single most important commitment in this section. It's what makes the UI stay at 60fps while a long ACIS boolean is running, what makes the AI agent able to query state during an edit without deadlocking, what makes co-edit possible without lock storms. Database people call this MVCC (multi-version concurrency control). It's the same pattern PostgreSQL uses. A CAD database is a database, and the rules that make databases fast apply here.

#### 3. Spatial index on load, not on demand.

The moment a drawing finishes loading, the R-tree / BVH is built. Every "what's at point X" query — pick, hover, OSnap, frustum cull, selection window, agent "find all entities in this room" — goes through the index. **Linear scan over entities is not a public API.** This is the single decision that separates snappy from unusable on a 250k-entity drawing. ODA's spatial filter can be wrapped here; we don't reinvent it. If we ever profile a hot path and find a linear scan, that's a bug fix, not an optimization.

#### 4. Lazy materialization of ACIS bodies.

ACIS bodies stay as opaque SAT blobs in `db` until the first geometric operation on that body. A drawing with 500 3D solids the user never queries shouldn't materialize 500 solids on open. ACIS supports this natively — we plumb it through the KAL. **Open time should be bounded by parse + index, not by kernel materialization.** When a user opens a 250MB DWG with 500 solids and clicks one of them, they wait for *one* solid to materialize, not 500.

#### 5. Tessellation lives on the GPU and is evictable.

Once a body is tessellated, the triangles go to GPU memory and stay there for the render loop. Under CPU memory pressure, the LRU tessellation is evicted; on next view it's regenerated from the cached B-rep. The tessellation cache has a **hard cap** (default: 30% of process working set) so it can never starve `db`. This is what `render` exists to do, and it's why `render` is a separate module from `geom` — different concerns, different eviction policies, different owners.

#### 6. Undo is a delta log, not a state snapshot.

Every undoable operation stores its inverse, not a copy of the world. Reversing `move(handle, dx, dy)` is `move(handle, -dx, -dy)` — bytes, not megabytes. Full-state snapshots are what blow heap in long sessions; deltas are what let AutoCAD survive an 8-hour edit session without the user noticing memory growth. This delta log is **the same op-stream** that drives sync, replication, agent context, and audit. One stream, five consumers (§3, §12). Building it any other way means writing the same plumbing five times.

#### 7. The memory budget is declared, enforced, and visible.

The engine boots with a declared memory budget — e.g., *"2× the loaded DWG size, capped at process working set minus 1 GB headroom for the OS."* Each cache layer has a sub-budget. When a sub-budget is exceeded, the layer evicts according to its policy. When the total is exceeded after eviction, the engine **fails loudly to the user** — *"this drawing exceeds your memory budget; please close other drawings or raise the limit in Preferences"* — instead of silently swapping to disk. **Silent swap is the worst possible failure mode**: the user thinks the app is frozen, force-quits, and loses work. Loud failure is recoverable; silent swap is a support ticket and a churn risk.

#### 8. Long operations run on workers; the UI thread does input + render only.

Open, save, regen, plot, index build, ACIS boolean, fillet, hatch boundary — all on worker threads with progress + cancel. Main-thread budget per frame is **8 ms** (target 16 ms for 60fps with headroom). Frame budget asserts in debug builds: any UI-thread work over 8 ms triggers a debug break, caught at write time by the engineer, not by a customer support ticket. This is how you guarantee responsiveness — by making "slow on the UI thread" a build-breaking error from commit 1.

### 16.3 Where bottlenecks actually appear in shipping CAD products, and the architectural answer to each

Plain-language version of what *"moderately large drawings get stuck"* usually means in practice, and how the rules above address each symptom.

| Symptom the user sees | What's really happening | Architectural answer |
|---|---|---|
| "Opens slowly on big files" | Eager ACIS materialization; spatial index built lazily on first pick | Rule 4 (lazy ACIS) + Rule 3 (index on load) — open time bounded by parse + index, not kernel work |
| "Stutters when I pan / zoom" | UI thread doing render + invalidation + new tessellation in one frame | Rule 5 (GPU-resident, evictable tess) + Rule 8 (8 ms UI budget) |
| "Hover lags on dense drawings" | Linear scan for hit-test | Rule 3 — spatial index is mandatory, scan-over-entities is forbidden |
| "Hangs for a few seconds when I save" | Save serializes the whole DWG on the UI thread | Rule 8 — save is a worker task with progress bar |
| "Editing a big solid freezes the app" | ACIS boolean on the UI thread, no copy-on-write snapshot | Rule 2 (MVCC reads) + Rule 8 (worker) — view keeps rendering against the pre-edit snapshot while the worker computes |
| "Crashes after a long session" | Undo log grew unbounded; or tessellation cache grew unbounded | Rule 6 (delta log + truncation) + Rule 5 (cache cap) + Rule 7 (budget enforcement) |
| "Force-quit because it 'froze' (but it was paging)" | Silent swap to disk under memory pressure | Rule 7 — fail loudly, never silently swap |
| "Property panel takes a second to update" | Eager load of all entity attributes on selection | Rule 4 (lazy attributes) — narrow query, on-demand |
| "Plugins make the app slow" | Plugin code running on the UI thread with full `db` access | `cmd` is the only seam; plugins go through it; long-running tool calls forced to worker (§13, §14.5) |

### 16.4 What to measure, and how to keep it from regressing

Plain rule: **the architecture above doesn't survive contact with the codebase unless CI measures it on every PR.** Specific gates we add at Phase-1 start:

1. **Open-time budget.** Corpus of 50 DWGs (small / medium / large / huge / pathological). PR fails if median open time regresses > 10%. Each drawing has a documented expected time.
2. **Frame-time P99 budget.** Synthetic *"pan-zoom-rotate-hover"* loop over each corpus drawing. P99 frame time logged per PR; regression past 16 ms = fail.
3. **Memory ceiling per drawing class.** Peak RSS during the synthetic loop. Hard ceiling per class; PR exceeding it fails.
4. **Allocation count regression.** Total `malloc` count in the open-edit-save loop. A sudden 2× spike usually means a new code path forgot to use the entity pool.
5. **Leak gate.** AddressSanitizer + LeakSanitizer enabled on all debug-build CI runs. Zero leaks tolerated.
6. **Long-session soak.** Overnight CI job: open big drawing, perform 10,000 edits with undo, save, close. RSS at the end must be within 5% of RSS at the start.
7. **Tracy profiler integration.** Every engineer's local build wires up Tracy. Frame time, allocation rate, GPU timing visible at all times. Performance work is done with measurement, not intuition.

### 16.5 Tools and people to bring in

- **Profilers:** Tracy (primary, every build), Intel VTune (deep CPU work), Heaptrack + Valgrind Massif (Linux memory), Visual Studio Diagnostics + WPA (Windows), AddressSanitizer + LeakSanitizer (CI gates).
- **Allocators:** mimalloc or jemalloc as a drop-in replacement for system `malloc` — 10–30% wins on allocation-heavy CAD workloads, near-zero integration cost.
- **Custom pools:** small-object pool for entity handles; arena allocator for transient command state (frees in one shot on transaction commit or abort).
- **Spatial indexes:** ODA's spatial filter for the database tier; embree BVH for the render tier if we want a ground-up alternative; both well-known, both proven.
- **Expertise sources:** Spatial CTC consultants (official ACIS memory-model guidance, bundled with the OEM contract); ex-AutoCAD / ex-Revit / ex-SolidWorks performance engineers via Toptal, Round Table Group, Guidepoint, GLG (~$300–$800/hr); back-channel with peer architects at Bentley / Hexagon / ANSYS SpaceClaim (other ACIS OEMs). **One day of an ex-AutoCAD perf engineer is worth a month of internal trial-and-error.** Budget for 40–80 expert-hours in Phase 1 specifically for the memory architecture.

### 16.6 What we deliberately don't do

- **No silent swap reliance.** If a drawing doesn't fit in budget, fail loudly. Pretending it works by paging is the worst possible customer experience.
- **No GC-based memory management for the kernel.** RAII + opaque handles. GC introduces unpredictable pauses; pauses kill responsiveness; responsiveness is the product.
- **No shared mutable state across threads without MVCC.** Every cross-thread read goes against a snapshot, never against live writable state. Locks on read paths are an outage waiting to happen at customer scale.
- **No "we'll profile later."** Profiling is wired in from commit 1 (Tracy + sanitizers + CI gates). Bolting performance work on after GA is what produces the *"moderately large drawings get stuck"* reputation we're escaping.
- **No premature out-of-core / streaming database.** AutoCAD has it. Revit has it. Both are huge engineering investments — multi-person-year. We commit to **in-RAM-only** for the 3-year plan, with the budget + eviction rules that make in-RAM viable for ActCAD's drawing-size distribution. Out-of-core is a Phase-4+ option if the customer base ever needs it; until then, the budget enforcement in Rule 7 is the right answer to *"my drawing doesn't fit."*
- **No giving plugins direct access to `db`.** Plugins go through `cmd` (§3, §13). Direct-access plugins are how every previous CAD product lost the ability to enforce these rules — once you let third-party code touch the database without a transaction boundary, every memory rule above becomes optional.

### 16.7 Bottom line in one paragraph

Hold the drawing in memory; that's correct and unchanged from how every serious CAD product works. **Treat memory as a budgeted resource with a declared cap, separate the one writable layer (`db`) from the four cacheable layers above it, use MVCC so reads never block writes, build the spatial index at load time, materialize ACIS bodies lazily, evict tessellation under pressure, store undo as deltas not snapshots, put every operation over 8 ms on a worker thread, and fail loudly rather than silently swap.** Wire profilers and CI gates in from commit 1 so the architecture is measured, not hoped for. Do this and a 250MB DWG with 3D solids stays responsive on a $500 laptop — the architecture is what makes it possible, not the hardware. Skip this and you ship the same *"gets stuck on big drawings"* reputation we're escaping, just with our name on it.

## 17. Render frame time — gaps and design decisions

> **Context.** §16 covers the memory architecture that keeps the working set bounded. This section covers the render-specific architecture decisions that determine whether the `render` module actually hits the P99 ≤ 16 ms frame-time CI gate (§16.4) once drawings grow to 100K+ entities. Read alongside `docs/memory-architecture.md` §9.1 (render integration).

### 17.1 What the current plan already has right

| Mechanism | Why it helps frame time |
|---|---|
| MVCC snapshots | Render thread never waits on a write — no stall from an ACIS boolean mid-frame |
| GPU-resident tessellation | Triangles live on the GPU; no re-upload every frame |
| LRU hard cap on tessellation cache | Cache cannot grow until it starves the rest of the pipeline |
| BVH frustum cull | Only submits draw calls for what's on screen |
| Worker-thread tessellation regeneration | Missing tessellation regenerates on a worker; render submits a placeholder, frame doesn't stall |
| Op-stream invalidation | Only the changed entity's tessellation is dirtied, not the whole scene |
| 8 ms UI-thread debug assert + CI P99 gate | Regressions caught at write time, not at GA |

These are the correct foundations. The gaps below are not contradictions of the plan — they are decisions the plan leaves open that must be closed before the `render` module header is written, because they change the shape of the tessellation cache key and the draw-call submission loop.

### 17.2 Gap 1 — Block instancing (highest impact)

**The problem.** A typical AEC or mechanical DWG has the same block (door, bolt, tree, fixture) inserted thousands of times. The tessellation cache as currently described is keyed on `(BodyHandle, detail_level)` and submits one draw call per visible entity. A drawing with 8,000 door inserts would submit up to 8,000 draw calls for identical geometry. The GPU is not the bottleneck — **CPU draw-call submission overhead is**. At scale, this alone can push frame time past 16 ms.

**The fix.** Geometry instancing: tessellate the block *definition* once, upload one vertex buffer, and draw it N times with an instance buffer of N transforms — one draw call regardless of insert count. DirectX 11/12 and Vulkan both expose this as `DrawInstanced` / `vkCmdDrawIndexedIndirect`. ODA Visualize has instancing in its scene graph; using it correctly makes this free for Phase 1. A custom backend must design for it explicitly.

**What must be decided before writing the module.** The tessellation cache key and invalidation logic are different for instanced geometry:

- Invalidation on **block definition change** → re-tessellate the definition, update the shared vertex buffer
- Invalidation on **insert transform change** → update the instance buffer only, no re-tessellation
- Invalidation on **one insert's attributes** (colour override, layer visibility) → partial instance buffer update

If the cache is designed flat `(entity_handle → mesh)` today, adding instancing later requires a significant refactor. Design it as `(definition_handle → mesh, [insert_handle → transform])` from commit 1.

### 17.3 Gap 2 — LOD tier calculation (named but not designed)

**The problem.** The tessellation cache key includes `detail_level` but the plan never defines how `detail_level` is computed. Without it:

- An arc occupying 3 screen pixels gets tessellated at the same segment count as one filling the viewport
- A circle at full zoom-out with 1,000 segments wastes GPU vertex throughput on geometry that contributes nothing to the pixel
- On a full zoom-out of a 100K-entity drawing, every entity submits fully tessellated geometry regardless of screen contribution

**The fix.** Compute the **pixel-projected size of the entity's AABB** from the camera transform during the BVH cull pass (which already has this information). Map projected size to a discrete detail tier:

| Projected AABB diagonal | Tier | Policy |
|---|---|---|
| < 2 px | `NONE` | Skip draw call entirely |
| 2–10 px | `DOT` | Single point or bounding box |
| 10–50 px | `LOW` | 6-segment arcs, simplified polylines |
| 50–200 px | `MED` | 24-segment arcs, normal polylines |
| > 200 px | `HIGH` | Full tessellation |

The BVH cull pass already computes projected bounds to decide visibility — the LOD tier comes out of that pass at zero extra cost. This is the change that keeps draw-call count sub-linear as the user zooms out.

### 17.4 Gap 3 — Text rendering (completely unaddressed)

**The problem.** Technical drawings carry enormous quantities of text: dimensions, annotations, leaders, attribute blocks, mtext. In a dense AEC drawing, text rendering is routinely 20–40% of total frame time if done naively. Re-rasterizing glyphs per frame on the CPU is catastrophically slow.

**The correct approach.**

- **SDF (Signed Distance Field) font atlas** on the GPU — one texture per font face, renders sharply at any size without per-frame CPU rasterization
- GPU-resident glyph atlas keyed on `(font_face, codepoint)`; atlas is built once on first use, updated only on new codepoints
- Text strings batched into a single draw call per font atlas per frame

ODA Visualize handles text internally; for Phase 1 using Visualize as the backend this is their problem. **The `render` module abstraction must define a text-rendering seam** (`render_text(string, transform, style)`) so that the Visualize backend delegates to Visualize and a custom native backend can implement SDF independently without changing the rest of the engine.

### 17.5 Gap 4 — GPU buffer upload strategy (not specified)

**The problem.** When the render worker finishes tessellating an entity on a background thread, the mesh needs to reach the GPU. How this crossing happens determines whether frames stall:

| Strategy | Behaviour | Verdict |
|---|---|---|
| Synchronous `Map/Unmap` on the render thread | Simple; causes a GPU pipeline bubble if the frame is mid-draw | Wrong |
| Upload heap + drain at frame start (DX12 / Vulkan) | Worker writes to a CPU-visible upload heap; frame loop drains at the start of the next frame before any draw calls | **Correct for DX12 / Vulkan** |
| DMA transfer queue (Vulkan) | Upload happens on a dedicated GPU transfer queue in parallel with rendering; zero frame time cost | **Best on Vulkan** |
| `UpdateSubresource` (DX11) | DX11's synchronous path; acceptable on DX11 since there is no explicit transfer queue | Acceptable for DX11 only |

The `render` module abstraction needs a `submit_tessellation(entity, mesh)` path whose backends implement the correct upload strategy for their API. This is a backend-specific concern but the seam must be in the abstraction from commit 1.

### 17.6 Gap 5 — Dirty region / incremental redraw (deferred, document the deferral)

**The problem.** The plan says the op-stream tells `render` which spatial regions need redraw, but does not say whether the engine redraws the full frame every frame or only redraws dirty tiles. Full-frame redraws at 60fps on a 4K display are roughly 2 GB/s of framebuffer write — modern GPUs handle this, but for the edit interaction loop (move one wall → only two dirty rectangles need to change) full redraws are wasted work.

**Decision: full-frame redraws for Phase 1; dirty tiles deferred to Phase 2.** This is the correct trade-off — dirty-tile invalidation is a meaningful engineering investment and is premature before the basic render pipeline is working and measured. ODA Visualize has tile-based invalidation built in; use it when Visualize is the backend.

**What must not be closed off.** The `render` module abstraction must not permanently hardcode full-frame semantics. The op-stream's spatial region invalidation (already in the plan) is the correct substrate for dirty-tile updates — preserve it so Phase 2 can layer dirty-tile redraws onto the same invalidation signal without changing the module interface.

### 17.7 Design decisions before writing the `render` module header

| Decision | When required | Impact if deferred |
|---|---|---|
| **Instanced tessellation cache** — `(definition_handle → mesh, [insert → transform])` structure, separate invalidation paths for definition vs instance transform | Before writing the `render` module header | Flat cache requires significant refactor to add instancing later |
| **LOD tier calculation** — pixel-projected AABB size maps to `{NONE, DOT, LOW, MED, HIGH}` tiers, computed in the BVH cull pass | Before writing the `render` module header | Adding LOD later changes the cache key and the frustum-cull loop |
| **`submit_tessellation()` upload-heap path** — backend-specific seam in the render abstraction | Before writing the `render` module header | Synchronous upload is sticky once code depends on it |
| **Text rendering seam** — `render_text(string, transform, style)` in the backend interface | Phase 1 design | Hard to add cleanly to the backend abstraction after backends are written |
| **Full-frame redraws confirmed for Phase 1** — dirty tile deferral explicitly documented | Phase 1 design | Not a code risk; a communication risk if engineers assume dirty tiles from day 1 |

### 17.8 What we deliberately don't do

- Don't design LOD tiers before measuring projected-AABB distribution on the real customer DWG corpus — the tier breakpoints above are starting points, not locked values.
- Don't implement GPU-driven culling (compute-shader cull pass) for Phase 1 — the CPU BVH is correct and sufficient; GPU-driven culling is a Phase-3 optimisation if the corpus grows to millions of entities.
- Don't add deferred / tiled rendering — this is 3D game engine complexity that is not warranted for ActCAD's 2D-primary use case in the 3-year plan.
- Don't build the SDF text atlas in Phase 1 if ODA Visualize is handling text rendering — build the seam, not the implementation; implement SDF only if / when a custom backend is needed.

## 18. Next steps

1. Review and approve this plan, or push back on specific decisions in §2, §12, §13, §14, or §15.
2. Run the feasibility spike (§9) — 4–6 weeks, small senior team, dedicated.
3. Convert each locked decision in §2 into an ADR under `docs/decisions/`.
4. Stand up the engineering org for Phase 1 (engine team, shell team, agent team, LISP-shim team, infra team).
5. Lock the Phase 1 milestone definitions and the willing-customer cohort for the month-12 native Windows beta.
6. Open commercial conversations (commitments locked per §10 and §15.4 — these are execution, not decisions): **ODA Sustaining membership signup; Qt Commercial Application Development Enterprise multi-year quote (target 15–35% below first quote, with mobile / WASM add-ons and Phase-3 price protection); 2-3 Visual Studio Enterprise seats for designated Windows-perf devs; AI dev tooling subscriptions (Cursor Business / Copilot Business / Claude Code) for the whole team; Clerk + Stripe accounts.**
7. **Open the ACIS commercial conversation with Spatial under NDA (Spike 1b workstream)** — request a term sheet covering: module list scoped to ActCAD use case (Local Ops + Healing + Defeaturing as floor; Polyhedral + AGM if Phase-3 BIM needs them); **royalty model — per-deployment is the primary ask, per-seat the documented fallback only** (see §15.1.1: ~10× cost variance at SMB scale, full negotiating sequence with tier breakpoints, minimum floor, and carve-outs); WASM / Linux / macOS SKU availability; source-escrow option; full DELA text; change-of-control + business-continuation clauses; CTC support-hour bundle. Legal review of the DELA before signing.
