# ActCAD Re-Architecture Plan

> **Status: Proposal, gated on the feasibility spike in §9.** Read alongside `docs/architecture-overview.md` (current stack and why it has to be replaced) and `docs/industry-outlook.md` (where the segment is going).

## 1. Goal

Replace the IntelliCAD engine with a first-party engine built directly on ODA SDKs and Open CASCADE, over a 3-year horizon. By end of year 3, ActCAD on the new stack must equal or beat today's IntelliCAD-based ActCAD on every dimension that matters to customers (performance, platform reach, AI assistance, BIM, extensibility), while existing ActCAD continues to ship through Phase 2 to protect revenue.

The architecture must be **future-proof on three axes that the current stack is not**: cross-device (desktop + web + mobile), AI-native (first-party MCP/agent surface inside the engine), and ours to refactor (no consortium gating).

## 2. Key architectural decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 2.1 | Foundation libraries | ODA direct (Drawings, Visualize, IFC, BIM SDKs, MCAD, Civil, Scan-to-BIM, inWEB family). Drop ITC / IntelliCAD entirely. | One vendor relationship covering DWG + BIM + IFC + renderer + web. Royalty-free under ODA membership. Eliminates the consortium cadence problem. |
| 2.2 | 3D kernel | **Open CASCADE (OCCT) primary** for the AEC / drafting / light-3D use case ActCAD actually serves. **Parasolid** held as a paid Phase-3+ option *only if* customers demand MCAD-grade parametric / fillet / boolean robustness. **ODA MCAD is not the kernel — it's a translator** for reading and writing SolidWorks / Inventor / CATIA files (see §11). All kernel access goes through the KAL. Gated on §9 spike item 1. | OCCT has 25+ years in production and ships in FreeCAD, KiCad, Salome, IfcOpenShell, BIM Vision. It has documented boolean-robustness gaps on degenerate topology and tight tolerances — **Shapr3D migrated OCCT → Parasolid in 2017 for exactly that reason** — but for AEC extrusions, IFC, and 2.5D operations it's sufficient. Parasolid is the gold standard but costs six-figures/yr + royalties and controls distribution. ODA MCAD opened SolidWorks read in June 2025 and is a translator SDK, not a B-rep modeling kernel. |
| 2.3 | Shell strategy | Shared C++ core compiled to native + WASM. **Qt 6 native shells** (Win / macOS / Linux). **TypeScript + React + WebGPU** browser shell. Mobile deferred to Phase 3. | Web-only Tauri / Electron is rejected for the drawing window — CAD pros need native menus, drag-drop with the OS, accessibility APIs, and printer integration. Qt is what Autodesk Maya and most pro DCC apps use. Tauri stays as the right tool for a thin launcher / license app, not the editor. |
| 2.4 | Engine language | **C++20** primary (interops directly with ODA's C++ SDKs — no FFI tax on inner-loop database calls). **Rust** selectively for `net`, `script` (host), `agent` (MCP), and new geometry algorithms where memory safety compounds. **No Rust in `db` or `render` hot paths.** | A CAD inner loop touches millions of entities per regen; the FFI tax of a Rust-primary core against a C++ SDK would be unacceptable. Rust earns its place where the boundary is narrow and the safety win compounds. |
| 2.5 | Extension APIs | **AutoLISP-compatible runtime** (migration story for the customer ecosystem). **Modern**: Python (embedded), TypeScript (in-app + browser), .NET 8+ (cross-platform via NativeAOT). **Dropped**: SDS, ADS, DIESEL, VBA, COM. **.NET surface is new — not ObjectARX-compatible** (set this expectation early). | LISP is the AutoCAD-ecosystem migration moat. The rest are legacy maintenance contracts with shrinking usage. The new .NET surface is opinionated and modern; pretending it's ObjectARX is a trap. |
| 2.6 | AI / agent surface | **MCP server inside the engine, wrapping the `cmd` module only** (never the `db` directly). Two MCP endpoints mirroring Autodesk Fusion 2026: a **local MCP** (requires ActCAD running, executes commands inside the host transaction) and a **remote MCP data server** (cloud, no host required, read-only DWG metadata + sheet / layer queries). **Public commitment: every MCP tool call resolves to exactly one transaction in the host undo stack.** No competitor (Autodesk Revit 2027, Fusion 2026, BricsCAD, ARES A3) has publicly documented this — it's a defensible differentiator. | The hard part of an agent surface for CAD is the *transactional command boundary*, not exposing the database. Revit 2027 MCP is Tech Preview without documented undo semantics; reviewers have already complained about half-finished features. Owning the transaction story publicly is both the right engineering and the right marketing. |
| 2.7 | Cloud / co-edit | **Two-tier server-authoritative model**. Tier 1 (geometry): serialized op-log over the engine's mutation stream, server-validated for referential integrity (door-to-wall, dim-to-entity), optimistic UI. Tier 2 (annotations, comments, markups, layer properties, sheet titles): Figma-style last-writer-wins per property with fractional indexing for ordering. Presence + selection locks at the UI layer. **Not a generic CRDT.** | The industry has converged here. Onshape uses serialized feature-level operations with branch-and-merge (USPTO 10,691,844). Figma explicitly rejected both OT and pure CRDT for LWW-per-property because each field updates independently and "merge text by character" isn't a real need. Yjs / Automerge OOM at the millions-of-entity scale of a real MEP DWG; recent academic work (geometry-aware CRDTs, MDPI 2025) confirms generic CRDTs lose intent on spatial documents. ARES Kudo ships closer to soft-lock + sync today — we can do better by going server-authoritative op-log on geometry from day 1. |
| 2.8 | License seam | The boundary between local-perpetual code and cloud-subscription code is a **build-time module boundary**, not a runtime feature flag. | Perpetual remains the moat; cloud / AI is an additive subscription. The architecture has to make this monetization model physically clean rather than glued on later. |
| 2.9 | Build system | CMake for C++ (industry standard, plays well with ODA's build pipeline). Emscripten for the WASM target. Cargo for the Rust crates, linked through a stable C ABI. | No exotic build tooling. The team will be onboarding from a C++ / IntelliCAD background. |

## 3. Module decomposition (C++ core)

Ten modules with strict contracts. The only module that mutates state is `db`; the only module the agent talks to is `cmd`.

1. **`db`** — drawing database. Canonical entity model, transactional mutation API, undo log, handle table, layer / block tables. Emits a typed op-stream on every commit. **Only mutator.**
2. **`geom`** — geometry primitives and the Kernel Abstraction Layer over OCCT (or MCAD). Pure functions, no state. The KAL prevents kernel types from leaking into public headers.
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
| Rendering | ODA Visualize (native: Vulkan / Metal / DirectX backends; web: Visualize inWEB → WebGPU) |
| 3D Kernel | OCCT primary (KAL-abstracted); Parasolid as paid Phase-3+ option for MCAD-grade workflows |
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
- Light 3D (basic solids, view, navigation) via OCCT through the KAL.
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
- Don't pick the 3D kernel before §9 spike item 1 measures it.
- Don't treat ODA MCAD as a B-rep modeling kernel — it's a translator for MCAD file formats only.
- Don't ship chat-in-canvas as the primary AI UX (Hypar pivoted away from text-to-BIM for this reason — see §14).
- Don't chase Bernini-style generative-CAD demos until editable, parametric round-tripping is proven.
- Don't use Yjs / Automerge for the geometry plane — confine generic CRDTs to non-spatial metadata only.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| **ACIS B-rep blob fidelity** when migrating customer DWGs to OCCT / MCAD | §9 spike item 1 is decision-forcing; KAL keeps the swap option open if either kernel underperforms |
| **inWEB ≠ same binary as native** — likely two builds with shim parity, not one bundle | §9 spike item 2 measures the actual delta; messaging adjusted accordingly |
| **LISP compatibility is multi-person-year**, not a 12-month spike | Define "compatibility" as a measured percentile of a real customer-script corpus before kickoff; ship migration tool for the tail |
| **MCP without a transactional boundary** corrupts drawings | `agent` wraps `cmd` only; never `db`. Permission scoping, dry-run, rate limit from commit 1 |
| **Cadence trap re-emerges with ODA** | Renderer escape valve: `render` is an abstraction over Visualize, so a native Vulkan backend can be slotted in if Visualize stalls |
| **Qt licensing surprises** | Decide commercial vs LGPL with legal review *before* tooling investment (§10) |
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
| 1 | Read 50 customer DWGs containing ACIS B-rep through OCCT; for the 3D-heavy subset, run a side-by-side Parasolid trial. Measure geometric drift, boolean robustness on degenerate topology, and fillet survival. | OCCT pass = no visible drift, <0.001 unit tolerance on volume / area, booleans pass on ≥95% of customer parts. If <95%, escalate to Parasolid commercial conversation. |
| 2 | Render the same 50 DWGs through native Visualize (Vulkan) *and* through Visualize inWEB (WebGPU); compare frame time on a 250k-entity drawing | inWEB ≤ 3× slower than native |
| 3 | Spike the `ui-bridge` C ABI / FlatBuffers seam: drive 10 commands from both a Qt shell and a React + WASM shell against a single `cmd` implementation | Seam is one source of truth; no shell-specific branching in `cmd` |
| 4 | Run a real customer LISP script (largest one a top-5 customer uses) through a minimal LISP interpreter on top of `cmd` | Script runs and produces visually identical output to current ActCAD |
| 5 | Stand up an MCP server exposing `cmd` to Claude / GPT; have it execute "draw a 3-bed apartment plan from this brief" | Command surface is agent-shaped, not human-shaped; no drawing corruption |
| 6 | Confirm Qt 6 commercial vs LGPL with legal and per-seat pricing | Decision made, not deferred |
| 7 | Reproduce 2-user co-edit on a 2D drawing with a stub op-log over WebSocket (not CRDT) | Op-stream design supports replication; conflict semantics on a real DWG operation are sane |

## 10. Open decisions for legal / commercial review

- **Qt 6 commercial vs LGPL** — affects static linking, code signing on macOS / iOS, and per-developer cost.
- **OCCT licensing path** — LGPL exception vs commercial support contract.
- **ODA membership tier** and inWEB redistribution terms — confirm against the "one engine, two targets" assumption.
- **Document service / auth / billing stack** — recommend Clerk + Stripe + self-hosted document service unless cost / data-residency rules say otherwise.
- **Customer-facing .NET API scope** — explicitly *not* ObjectARX-compatible; messaging needs to be clear from announcement.
- **IntelliCAD-ActCAD sunset date** — driven by Phase 2 GA quality, not a date picked up front.

## 11. Industry adoption — who else picked these and why

For each component of the planned stack: notable adopters, why they picked it, known pain points in shipped products, and the resulting verdict for ActCAD.

### 11.1 ODA SDKs (Drawings, Visualize, IFC, BIM, MCAD, inWEB) — direct membership

- **Adopters.** Bricsys / BricsCAD (founding ODA member, the deepest user — Drawings + Visualize + BIM + IFC SDK), GstarCAD, ZWCAD, NanoCAD (all direct on ODA Drawings). Graphisoft ARCHICAD and Vectorworks use ODA Drawings as their DWG import / export layer. Bentley MicroStation, Trimble, Dassault hold memberships for format interop. ARES Graebert wrote their own DWG library and uses ODA selectively. **IntelliCAD itself swapped its in-house DWG core for ODA technology under the hood years ago**, so all IntelliCAD-derived products (ActCAD, progeCAD, CMS IntelliCAD) inherit ODA indirectly today.
- **Why.** Format coverage no one else ships under a single C++ API (DWG back to R12, DGN, IFC 2x3/4/4.3, Revit, Navisworks); aggressive Autodesk-version tracking; one membership covers everything; Visualize lets members drop expensive third-party graphics middleware (HOOPS, etc.).
- **Known pain.** Annual membership fee is non-trivial (Sustaining tier required for MCAD). API surface is wide but uneven — Revit *read* is mature, Revit *write* is partial. Threading model is heavy C++. Riding ODA's release cadence whether your QA is ready or not. Visualize scene graph is its own world — interop with engine-side picking / snapping is your problem.
- **Verdict.** **Good fit, go direct.** ActCAD already pays ODA transitively; cutting to direct membership removes ITC as middleman and matches BricsCAD / GstarCAD / ZWCAD / NanoCAD.
- Sources: [ODA Members](https://www.opendesign.com/oda-membership), [Bricsys ODA showcase](https://www.opendesign.com/member-showcase/bricsys), [IntelliCAD on ODA](https://gfxspeak.com/featured/autocad-workalike-market/).

### 11.2 Open CASCADE (OCCT) — 3D kernel

- **Adopters (open source).** FreeCAD (entire Part / PartDesign workbench), KiCad (3D PCB viewer / STEP export), Salome (EDF simulation platform), Gmsh, CAD Assistant, BIM Vision, IfcOpenShell. **Commercial.** Open Cascade SAS sells support to Airbus, Bureau Veritas, EDF; CAD Exchanger uses it internally for translators.
- **Notably NOT on OCCT.** SolidWorks (Parasolid), NX (Parasolid), Solid Edge (Parasolid), Inventor / Fusion (ASM = Parasolid fork), Plasticity (Parasolid). **Shapr3D migrated OCCT → Parasolid in 2017** explicitly because OCCT's boolean robustness wasn't production-grade for MCAD workloads.
- **Why anyone picks OCCT.** Only open-source full-scale B-rep + STEP / IGES / BREP I/O; LGPL 2.1 with dynamic-linking exception allows commercial closed-source products; broad surface / curve / topology coverage; included tessellator + visualization.
- **Known pain.** Boolean robustness on degenerate topology (FreeCAD issues #5619, #5782, #15599, #17497, #17705, #26119 all document this — workaround is the "Fuzzy Boolean" tolerance hack). Tolerance model is global-ish, breaks when small geometry sits next to large. Performance on large assemblies (FreeCAD bypasses the OCCT viewer for Coin3D). Surface intersection edge cases on trimmed NURBS produce empty / invalid edges. Multi-threaded booleans are sometimes *slower* than single-threaded.
- **Verdict.** **Acceptable for ActCAD's AEC / drafting / light-3D scope.** Risky if customers ever want filleted assemblies — keep Parasolid as a paid Phase-3+ option. The §9 spike measures the boundary.
- Sources: [OCCT projects](https://dev.opencascade.org/about/projects_and_products), [FreeCAD #15599](https://github.com/FreeCAD/FreeCAD/issues/15599), [#5619](https://github.com/FreeCAD/FreeCAD/issues/5619), [Shapr3D migration](https://www.fabbaloo.com/2017/12/shapr3d-30-brings-parasolid-3d-modeling-to-ipad-pro).

### 11.3 ODA MCAD SDK — translator, not kernel

- **Adopters.** **Effectively none in production yet.** SolidWorks read opened June 2025; Inventor read followed; CATIA / NX / Creo / JT / Parasolid / Solid Edge are on the 2026–2027 roadmap. No shipped end-user CAD product is on it as a primary kernel.
- **Why members are interested.** Flat per-company pricing (no per-developer / per-seat), bundled into ODA membership extension — orders of magnitude cheaper than Parasolid (six-figures/yr + royalties) or ACIS. The only credible CATIA / SOLIDWORKS *write* path not controlled by Dassault.
- **Comparison.** Parasolid mature since 1988, gold standard for booleans / fillets, expensive, distribution-controlled. ACIS second-place commercial, better at faceted-import / defeaturing. OCCT open-source but B-rep robustness behind both. **ODA MCAD is positioned as translation / interop, not as a modeling kernel.**
- **Verdict.** **Mismatch as a modeling kernel.** Use it as a **SolidWorks / Inventor / CATIA importer** in Phase 2-3 once it's mature. Do not stake the 3D pipeline on it.
- Sources: [ODA MCAD product](https://www.opendesign.com/products/mcad-sdk), [MCAD SDK for SolidWorks](https://www.opendesign.com/blog/2025/december/mcad-sdk-solidworks-files).

### 11.4 Qt 6 — desktop shell

- **Adopters in CAD / DCC.** Autodesk Maya (Qt since 2011), MotionBuilder, Mudbox, parts of 3ds Max; The Foundry Nuke / Mari / Katana; SideFX Houdini; Foundry Modo; CATIA V6 / 3DEXPERIENCE; Allplan / Nemetschek; FreeCAD (Qt 5 → 6 in progress); QCAD; OpenSCAD. **Counter-example.** Blender (custom OpenGL UI).
- **Why.** Cross-platform from a single codebase; mature OpenGL / Vulkan integration via QOpenGLWidget / QRhi; native theming; Qt Quick / QML for modern panels; signal-slot maps cleanly onto large C++ codebases.
- **Known pain.** **Commercial cost.** Qt for Application Development Professional / Enterprise is ~$4,000–$6,000 per developer per year for desktop; Small Business tier (rev-gated, caps at ~$250K) is €530/year/dev. Add ~30–60% for mobile / embedded / Qt-for-WebAssembly. LGPL requires dynamic linking — static-link needs the paid license. Qt 5 → 6 migration is painful at scale (FreeCAD's Qt 6 work has been 2+ years and still partial).
- **Verdict.** **Good fit, with a decision-forcing legal call.** Industry-standard for this product category. The LGPL-vs-commercial call gets made in §9 spike item 6.
- Sources: [Maya Qt SDK](https://help.autodesk.com/cloudhelp/2020/ENU/Maya-SDK-MERGED/developer/Working-with-Qt/Using-Qt-in-Plug-ins.html), [Qt pricing](https://www.qt.io/pricing), [Qt Small Business](https://www.qt.io/development/qt-for-small-business), [FreeCAD Qt 6 #6992](https://github.com/FreeCAD/FreeCAD/issues/6992).

### 11.5 C++ vs Rust for the engine core

- **Adopters (Rust).** **Fornjot** (Hanno Braun) — experimental B-rep kernel, explicitly "reliability over features," no shipped product on it. **Truck** (RICOS-JP) — Rust B-rep kernel, compiles to WASM; used by **CADmium** (Matt Ferraro). **Zoo.dev / KittyCAD** — the most serious commercial Rust CAD play; Rust geometry engine on the server (Vulkan / Nvidia), React frontend, app shipping. **Figma** — C++ canvas, Rust used for multiplayer sync server and hot-path tooling. Pattern: Rust at the edges, not the kernel.
- **Why.** Memory safety without GC, fearless concurrency, excellent WASM toolchain, cargo, no header / macro hell. For a from-scratch solver, type-checkable correctness.
- **Known pain.** Hiring depth in CAD geometry is in C++ not Rust. No mature B-rep kernel in Rust (Truck / Fornjot are years behind OCCT, decades behind Parasolid). C++ FFI to ODA / OCCT / Parasolid is non-trivial — you pay it on every API boundary.
- **Verdict.** **Mismatch for the kernel; selective fit at the edges.** Confirms §2.4 — Rust earns its place in `net`, `script` host, `agent` (MCP), and new geometry algorithms. C++20 stays primary.
- Sources: [Fornjot](https://www.fornjot.app/), [Truck](https://github.com/ricosjp/truck), [CADmium](https://mattferraro.dev/posts/cadmium), [Zoo modeling-app](https://github.com/KittyCAD/modeling-app), [Figma WASM](https://www.figma.com/blog/webassembly-cut-figmas-load-time-by-3x/).

### 11.6 WebGPU + WebAssembly — browser CAD

- **Adopters.** **AutoCAD Web** — Autodesk transpiled a major part of AutoCAD's ~15M-line C++ via Emscripten to WASM; same engine as desktop. **Figma** — C++ → WASM via Emscripten, shipped WebGPU rendering in 2024. **Adobe Photoshop Web** — same pattern. **ODA Drawings inWEB / Visualize inWEB** — entire ODA C++ stack compiled to WASM. **CADmium** — Rust → WASM, three.js / WebGL today. **Tinkercad** — WebGL, JS-heavy. **Onshape** — NOT a WASM story: Parasolid runs native on AWS, browser only renders triangles via WebGL.
- **WebGPU baseline as of May 2026.** Chrome (since 113, 2023), Edge, Safari 26 (Sept 2025 — macOS Tahoe, iOS 26, visionOS), Firefox 141+ on Windows (July 2025), Firefox 145 on Apple Silicon. Firefox on Linux / Android still in progress. Babylon.js shows ~10× rendering speedup vs WebGL; WebGPU is the only path to in-browser compute shaders.
- **Known pain.** SharedArrayBuffer needs COOP / COEP headers — breaks embedding in customer intranets and some SaaS hosts. wasm32 caps at 4GB — large DWG / Revit forces wasm64 (narrower support). Filesystem assumptions need virtualizing via MEMFS / IDBFS. Binary size: stripped CAD WASM is tens of MB (need streaming compilation, dlopen-emulation code-splitting, `-Oz`). Debugging is dramatically worse than native.
- **Verdict.** **Good fit for a Visualize-only browser companion now; the full-editor browser story is a multi-year program** matching AutoCAD Web's trajectory, not a Phase-1 launch deliverable.
- Sources: [AutoCAD WebAssembly InfoQ](https://www.infoq.com/presentations/autocad-webassembly/), [WebGPU baseline 2026](https://www.webgpu.com/news/webgpu-hits-critical-mass-all-major-browsers/), [Figma WebGPU](https://www.figma.com/blog/figma-rendering-powered-by-webgpu/), [Onshape architecture](https://www.onshape.com/en/blog/how-does-onshape-really-work).

### 11.7 ODA inWEB (Drawings inWEB, Visualize inWEB)

- **Adopters.** Drawings inWEB SDK opened to ODA members October 2024 — **no major shipping CAD product is publicly known to be on it for primary editing yet.** Members are building CDE / viewer apps. Visualize inWEB (`@inweb/viewer-visualize` on npm) is further along; several ODA members use it as a HOOPS / 3D-PDF viewer replacement. ODA's own *ODA Viewer* and the **VisualizeJS** demo viewer are the reference implementations.
- **Why.** Drawings inWEB is a **WASM transpilation of the C++ Drawings SDK** — file-format coverage is at parity with desktop Drawings SDK by construction.
- **Known pain.** Performance on large DWG (>200MB, dense annotation) lags desktop on initial-load and pan / zoom; browser-tab memory ceilings bite earlier than native. What's NOT at parity: full constraint engine, full LISP / .NET, plot / publish round-trip, certain custom-object proxies.
- **Verdict.** **Good fit for viewer / markup web companion in Phase 1; risky as the sole platform for full editing today.** Aligns with our native-Windows-first phasing in §5.
- Sources: [inWEB landing](https://www.opendesign.com/products/inweb), [Drawings inWEB SDK release](https://www.opendesign.com/blog/2024/october/drawings-inweb-sdk-oda), [@inweb/viewer-visualize npm](https://www.npmjs.com/package/@inweb/viewer-visualize).

### 11.8 CMake + Emscripten — C++ → WASM toolchain

- **Successful CAD-scale codebases on this exact toolchain.** AutoCAD Web (15M-line C++ → WASM via Emscripten — the headline case). Figma (3× initial load improvement when they moved off asm.js). Adobe Photoshop Web. ODA Drawings inWEB / Visualize inWEB. VTK / Kitware (ships documented Emscripten build with `VTK_WEBASSEMBLY_64_BIT` for >4GB models). CAD Exchanger Web.
- **Recurring failure modes.** Threading + SharedArrayBuffer requires COOP / COEP headers (breaks embeds, ads); 4GB pointer cap on wasm32 forces wasm64 for large models; filesystem virtualization (MEMFS / IDBFS) for every `fopen`; third-party C++ deps (Boost, ICU, OpenSSL) need patching for the Emscripten toolchain; binary size in the tens of MB needs streaming compilation + code-splitting; long compile / link cycles on kernel-sized code (hours for full rebuilds with LTO); GL / GLES → WebGL2 / WebGPU shader translation; debugging vastly worse than native.
- **Verdict.** **Good fit and well-trodden.** Every relevant precedent uses this toolchain; the failure modes are published and the playbook is public.
- Sources: [AutoCAD WebAssembly InfoQ](https://www.infoq.com/presentations/autocad-webassembly/), [Figma WebAssembly](https://www.figma.com/blog/webassembly-cut-figmas-load-time-by-3x/), [Emscripten pthreads](https://emscripten.org/docs/porting/pthreads.html), [VTK Emscripten](https://docs.vtk.org/en/latest/advanced/build_wasm_emscripten.html).

### 11.9 Summary verdict matrix

| Component | Verdict |
|---|---|
| 11.1 ODA SDKs (direct membership) | **Good fit** — matches BricsCAD / GstarCAD / ZWCAD / NanoCAD; removes ITC middleman |
| 11.2 OCCT B-rep kernel | **Acceptable for AEC; risky for MCAD parametrics** (Shapr3D's exit is the cautionary tale) |
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

## 15. Next steps

1. Review and approve this plan, or push back on specific decisions in §2, §12, §13, or §14.
2. Run the feasibility spike (§9) — 4–6 weeks, small senior team, dedicated.
3. Convert each locked decision in §2 into an ADR under `docs/decisions/`.
4. Stand up the engineering org for Phase 1 (engine team, shell team, agent team, LISP-shim team, infra team).
5. Lock the Phase 1 milestone definitions and the willing-customer cohort for the month-12 native Windows beta.
6. Open commercial conversations: ODA membership tier upgrade, Parasolid evaluation license (gated on §9 spike item 1), Qt commercial-vs-LGPL decision.
