# ActCAD Re-Architecture Plan

> **Status: Proposal, gated on the feasibility spike in §9.** Read alongside `docs/architecture-overview.md` (current stack and why it has to be replaced) and `docs/industry-outlook.md` (where the segment is going).

## 1. Goal

Replace the IntelliCAD engine with a first-party engine built directly on ODA SDKs and Open CASCADE, over a 3-year horizon. By end of year 3, ActCAD on the new stack must equal or beat today's IntelliCAD-based ActCAD on every dimension that matters to customers (performance, platform reach, AI assistance, BIM, extensibility), while existing ActCAD continues to ship through Phase 2 to protect revenue.

The architecture must be **future-proof on three axes that the current stack is not**: cross-device (desktop + web + mobile), AI-native (first-party MCP/agent surface inside the engine), and ours to refactor (no consortium gating).

## 2. Key architectural decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 2.1 | Foundation libraries | ODA direct (Drawings, Visualize, IFC, BIM SDKs, MCAD, Civil, Scan-to-BIM, inWEB family). Drop ITC / IntelliCAD entirely. | One vendor relationship covering DWG + BIM + IFC + renderer + web. Royalty-free under ODA membership. Eliminates the consortium cadence problem. |
| 2.2 | 3D kernel | **Open CASCADE (OCCT) primary**, ODA MCAD as an abstracted fallback. Gated on §9 spike item 1. | OCCT has 25+ years in production, stronger B-rep robustness, mature STEP / IGES / IFC translators (which the BIM-downmarket bet leans on). MCAD is the youngest viable kernel and has known gaps on production parts. The decision-forcing test is whether OCCT can read existing customer ACIS B-rep blobs without geometric drift. |
| 2.3 | Shell strategy | Shared C++ core compiled to native + WASM. **Qt 6 native shells** (Win / macOS / Linux). **TypeScript + React + WebGPU** browser shell. Mobile deferred to Phase 3. | Web-only Tauri / Electron is rejected for the drawing window — CAD pros need native menus, drag-drop with the OS, accessibility APIs, and printer integration. Qt is what Autodesk Maya and most pro DCC apps use. Tauri stays as the right tool for a thin launcher / license app, not the editor. |
| 2.4 | Engine language | **C++20** primary (interops directly with ODA's C++ SDKs — no FFI tax on inner-loop database calls). **Rust** selectively for `net`, `script` (host), `agent` (MCP), and new geometry algorithms where memory safety compounds. **No Rust in `db` or `render` hot paths.** | A CAD inner loop touches millions of entities per regen; the FFI tax of a Rust-primary core against a C++ SDK would be unacceptable. Rust earns its place where the boundary is narrow and the safety win compounds. |
| 2.5 | Extension APIs | **AutoLISP-compatible runtime** (migration story for the customer ecosystem). **Modern**: Python (embedded), TypeScript (in-app + browser), .NET 8+ (cross-platform via NativeAOT). **Dropped**: SDS, ADS, DIESEL, VBA, COM. **.NET surface is new — not ObjectARX-compatible** (set this expectation early). | LISP is the AutoCAD-ecosystem migration moat. The rest are legacy maintenance contracts with shrinking usage. The new .NET surface is opinionated and modern; pretending it's ObjectARX is a trap. |
| 2.6 | AI / agent surface | **MCP server inside the engine, wrapping the `cmd` module only** (never the `db` directly). Transactional, undoable, permission-scoped, dry-run capable from day 1. | The hard part of an agent surface for CAD is the *transactional command boundary*, not exposing the database. Without this seam designed up front, the agent becomes a write-only firehose that corrupts drawings. |
| 2.7 | Cloud / co-edit | **Custom op-log** over the engine's mutation stream, replicated via the ODA collaboration substrate. **Not a generic CRDT.** | DWGs have cross-entity references (layers, blocks, xrefs, handles), spatial indices, and undo semantics where naive last-write-wins produces invalid drawings. Yjs / Automerge are for text and JSON, not CAD state. ARES Kudo solved this with an op log, and that's the proven path. |
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
| 3D Kernel | OCCT primary, MCAD fallback (KAL-abstracted) |
| BIM / IFC | ODA IFC SDK + BimRv / BimNw extensions |
| Engine language | C++20, selective Rust |
| Build | CMake + Emscripten + Cargo |
| Desktop shell | Qt 6 (commercial-vs-LGPL TBD per §10) |
| Browser shell | TypeScript + React + WebGPU (WebGL2 fallback) |
| Mobile shell | Native (Swift / Kotlin) over the C++ core via FFI — Phase 3 |
| Scripting | Python (CPython / Pyodide), TypeScript, .NET 8+ NativeAOT, AutoLISP shim |
| Agent surface | MCP server in `agent`, wrapping `cmd` |
| Cloud co-edit | Custom op-log on ODA collaboration substrate |
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
| 1 | Read 50 customer DWGs containing ACIS B-rep through OCCT *and* MCAD; measure geometric drift vs ACIS | No visible drift; <0.001 unit tolerance on volume / area for both. Decides 3D kernel. |
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

## 11. Next steps

1. Review and approve this plan, or push back on specific decisions in §2.
2. Run the feasibility spike (§9) — 4–6 weeks, small senior team, dedicated.
3. Convert each locked decision in §2 into an ADR under `docs/decisions/`.
4. Stand up the engineering org for Phase 1 (engine team, shell team, agent team, LISP-shim team, infra team).
5. Lock the Phase 1 milestone definitions and the willing-customer cohort for the month-12 native Windows beta.
