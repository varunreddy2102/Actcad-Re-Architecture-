---
marp: true
theme: default
paginate: true
size: 16:9
header: 'ActCAD Re-Architecture — Strategic Decision Briefing'
footer: 'Jytra Technology Solutions · Confidential'
style: |
  section { font-size: 22px; }
  h1 { color: #1a3a6c; }
  h2 { color: #2d5fa7; border-bottom: 2px solid #2d5fa7; padding-bottom: 4px; }
  table { font-size: 0.85em; }
  blockquote { border-left: 4px solid #2d5fa7; color: #444; }
  strong { color: #1a3a6c; }
---

<!-- _class: lead -->
<!-- _paginate: false -->

# ActCAD: Re-Architecting for the Next Decade

### A strategic decision briefing for management

**Jytra Technology Solutions** · Confidential

*Based on `docs/architecture-overview.md`, `docs/industry-outlook.md`, and `docs/rearchitecture-plan.md` (563 lines, 16 sections).*

---

## The ask in one slide

We propose a **3-year, phased re-architecture of ActCAD** that replaces the IntelliCAD engine with a **first-party engine built directly on ODA SDKs and Open CASCADE**.

- **Existing ActCAD continues to ship through Phase 2 — revenue is protected.**
- By end of year 3, the new product **equals or beats** today's ActCAD on every dimension that matters: performance, platform reach (web + native + mobile), AI assistance, BIM, extensibility.
- **Modeled stack + tooling + cloud budget:** ~$83K Phase 1 → ~$239K Phase 2 → ~$596K Phase 3 (salary excluded). No six-figure opaque OEM commitments.
- **Today's decision is narrow:** approve a **4–6 week feasibility spike**. After the spike, management gets a structured Go / No-Go on the full plan with measured data.

---

## Why now — three forces converging

1. **AI is becoming table stakes inside CAD.** Autodesk shipped MCP servers in Revit 2027 and Fusion 2026. ARES Graebert shipped the A3 AI agent in ARES 2027. BricsCAD shipped AI Assistant. **We are structurally blocked** from operating AI on our foundational codebase — IntelliCAD's consortium license forbids it.
2. **Cloud and web are no longer optional.** AutoCAD Web ships since 2018. Onshape has been cloud-native since founding. ARES Kudo ships a browser DWG editor. **We are Windows-only** because of how IntelliCAD's shell is structured.
3. **BIM is moving downmarket** into our customer base. SMB AEC customers in India / SEA / EU increasingly ask for IFC import / export and lightweight BIM. Adding that on top of IntelliCAD is a renderer-tuning treadmill we don't win.

> **If we are not on the new architecture by year 3, we will be selling against products that are.**

---

## The lived pain today

From `docs/architecture-overview.md` §4:

- **Renderer needs per-machine tuning** at customer sites and still underperforms versus AutoCAD / BricsCAD on the same hardware.
- **Non-Windows targets are out of reach** because IntelliCAD's shell is Windows-bound.
- **AI cannot operate on the foundational codebase** — consortium license blocks structural changes.
- **We ride IntelliCAD's release cadence**, which is gated on AutoCAD version-tracking and consortium QA, not on our customers' needs.
- **Every fix we ship into IntelliCAD is shared with our direct competitors** through the consortium.

---

## Where our direct peers are today

| Vendor | Engine | Web | AI | Co-edit |
|---|---|---|---|---|
| **BricsCAD** | ODA-direct, in-house engine | Limited | AI Assistant V26 | None |
| **ARES Graebert** | Own DWG + selective ODA | Kudo (full browser) | A3 agent (2027) | Soft-lock sync |
| **Onshape** | Cloud-native, Parasolid on AWS | Browser-only | Limited | Real-time + branch/merge |
| **Snaptrude** | Cloud-native AEC | Yes | RFP → LOD-300 gen | Real-time |
| **AutoCAD** | First-party (Autodesk) | WASM transpile | MCP, Markup Assist, Smart Blocks | Serialized + audit |
| **ActCAD today** | **IntelliCAD (downstream)** | **No** | **Blocked** | **None** |

The peer set is moving on three dimensions at once. We are not on any of them yet.

---

## The strategic bet

Replace IntelliCAD with a first-party engine on:

- **ODA SDKs direct** — the same foundation Bricsys, GstarCAD, ZWCAD, NanoCAD build on
- **Open CASCADE (OCCT)** — for AEC / drafting / light 3D / IFC
- **C++ core + Qt 6 native + WebAssembly browser** — Maya / Houdini / AutoCAD-Web pattern
- **AI-native from the foundation** — MCP server inside the engine, transactional undo, day one

Four differentiators we commit to publicly:

1. **Drop ITC — go ODA-direct** (same foundation BricsCAD is built on)
2. **Two-tier server-authoritative co-edit** (leapfrog ARES Kudo's soft-lock ceiling)
3. **MCP with documented transactional undo** (no competitor has done this)
4. **API-parity extension marketplace** across native + web (closer to "write once" than anyone shipping)

---

## Stack at a glance

| Layer | Choice |
|---|---|
| DWG / DXF + database | ODA Drawings SDK (direct membership) |
| Rendering | ODA Visualize — **DirectX 11 (Win default), DirectX 12, Vulkan, Metal**; web: Visualize inWEB → WebGPU |
| 3D kernel | **OCCT** (LGPL, free) — locked for the 3-year plan |
| MCAD format I/O | ODA MCAD translator (SolidWorks / Inventor / CATIA read) |
| BIM / IFC | ODA IFC + BimRv / BimNw |
| Engine language | **C++20 primary**, Rust selectively for net / agent / scripting |
| Desktop shell | **Qt 6 Commercial** (App Dev Enterprise) |
| Browser shell | TypeScript + React + WebGPU + WASM |
| Build | CMake + Emscripten + Cargo |
| Co-edit | Two-tier: op-log (geometry) + LWW (annotations) |
| Agent | MCP server in the engine, transactional |

---

## Architecture in one picture — 10-module C++ core

| Module | Role |
|---|---|
| **`db`** | Drawing database. **Only mutator.** Emits typed op-stream on every commit. |
| **`geom`** | Geometry + Kernel Abstraction Layer over OCCT. Pure functions, no state. |
| **`render`** | View / render-abstraction over Visualize. Swappable backends. |
| **`cmd`** | Command bus. **The single seam the AI agent talks to.** |
| **`script`** | Hosts Python, LISP, JS bridge. All reach `cmd`, never `db`. |
| **`plugin`** | Plugin host. API parity across native + WASM, not binary parity. |
| **`net`** | Sync, document service, auth, telemetry. (Rust crate) |
| **`agent`** | MCP server, tool catalog, permission scoping. (Rust crate) |
| **`platform`** | File I/O, fonts, clipboard, printer, GPU surface. Only module with `#ifdef`. |
| **`ui-bridge`** | One C ABI / FlatBuffers boundary. Qt shell + React/WASM shell both consume it. |

> One ABI; native + WASM both go through it. **Plugins and agents talk to one command bus.**

---

## Three phases, three years

| Phase | Months | Headline deliverables |
|---|---|---|
| **Phase 1: Foundation** | 0–12 | Engine skeleton on ODA. Full DWG fidelity. 2D drafting commands. **Native Windows beta** to willing-customer cohort. Browser viewer + markup in parallel. LISP runtime spike. **AI-as-tool features shipped** (Markup Assist, Smart Blocks, Drawing Health). MCP server skeleton. |
| **Phase 2: Production v1** | 12–24 | Mac / Linux Qt shells at parity. Browser becomes full editor. Light 3D via OCCT. **Cloud co-edit on 2D**. LISP coverage to 95th percentile + migration tool. AI assistant **GA**. **New product GA at month 24.** |
| **Phase 3: Parity-or-better** | 24–36 | Full 3D + BIM-lite (IFC). MEP / Electrical verticals reshipped as plugins. Mobile (iOS / Android) shells. End-to-end perf tuning. **IntelliCAD ActCAD sunset.** |

IntelliCAD-based ActCAD continues to ship in parallel through Phase 2 → revenue protected.

---

## Phasing inversion — why not web-first

The industry-default move is **web-first** because the future is in the cloud.

**For ActCAD specifically that would be wrong:**

- Installed base is **Windows desktop SMBs in India / SEA** on hardware where browser WebGPU is unreliable.
- A web-only beta would produce **zero useful signal** from existing customers.
- **Revenue protection** requires the desktop daily-driver to ship first.

The fix: **native Windows daily-driver first**, browser ships as viewer + markup in parallel, full browser editor in Phase 2.

> The *architectural* discipline that forces portability (the C ABI, the kernel layer, the op-stream) is preserved either way. What changes is which shell sees production first.

---

## Risk framework (top 5 of 10)

| Risk | Mitigation |
|---|---|
| **ACIS B-rep fidelity** in customer DWGs through OCCT | §16 spike item 1 is decision-forcing; KAL keeps the swap option open |
| **LISP compatibility is multi-person-year** | Define coverage as % of measured customer-script corpus (80% P1 → 95% P2); migration tool for the tail |
| **MCP without transactional undo corrupts drawings** | `agent` wraps `cmd` only; **every tool call = one host undo transaction** committed publicly |
| **Two parallel product lines for 24 months** | Org plan for support + marketing context-switching; clear customer messaging from day 1 |
| **Cadence trap re-emerges with ODA** | `render` module abstraction lets a native Vulkan / DirectX backend slot in if Visualize stalls |

Full risk register (10 items, each with named mitigation) in `docs/rearchitecture-plan.md` §7.

---

## Feasibility spike — 4–6 weeks before kickoff

**7 pass / fail items, decision-forcing.** Items 1, 2, 3, 5 are deal-breakers if they fail.

| # | What | Pass criterion |
|---|---|---|
| 1 | OCCT fidelity on customer ACIS B-rep parts | <0.001 unit drift, booleans pass on ≥95% — **locks 3D kernel** |
| 2 | inWEB perf vs native Visualize (Vulkan / DirectX) | inWEB ≤ 3× slower than native |
| 3 | `ui-bridge` C ABI driving Qt + WASM from one `cmd` | One source of truth; no shell-specific branching |
| 4 | Real customer LISP script on a minimal interpreter | Visually identical output to current ActCAD |
| 5 | MCP-driven "draw a 3-bed apartment plan" | Agent-shaped commands, no drawing corruption |
| 6 | Qt Commercial multi-year quote negotiated | Signed quote in hand (target 15–35% below first quote) |
| 7 | 2-user op-log co-edit on a real drawing | Op-stream design supports replication; sane conflict semantics |

> **If 1, 2, 3, or 5 fail, the plan changes before kickoff — not at the Phase-2 boundary.**

---

## Modeled cost envelopes (salary excluded)

| Phase | Engineers | Stack + tools + cloud |
|---|---|---|
| **Phase 1** (months 0–12) | 8 | **~$83,300** |
| **Phase 2** (months 12–24) | 20 | **~$239,400** |
| **Phase 3** (months 24–36) | 30 | **~$595,700** |

**What's in scope:** ODA Sustaining ($7.5K → $4.5K renewal, unlimited seats + Web/SaaS), Qt Commercial Enterprise (~$4K/dev/yr), OCCT (free under LGPL), VS Code primary + 2-3 VS Enterprise seats for perf devs, AI dev tooling (~$50/dev/mo), AWS infra (compute + GPU streaming), Clerk + Stripe.

**Not in scope** (deferred / hypothetical): Parasolid (~$200–500K/yr if it ever became necessary; not in 3-year plan), Open Cascade SAS support, ACIS commercial.

> **No six-figure-plus opaque-OEM item carried in any phase.** Every line item is bounded by a published price.

---

## Licensing posture — ActCAD is commercial closed-source

| Component | Choice | Why |
|---|---|---|
| **ODA** | Sustaining from day 1 | Unlimited commercial seats + inWEB Web/SaaS rights, **no per-seat royalty**. Best-value line item in the entire stack. |
| **Qt 6** | **Commercial App Dev Enterprise** | LGPL forbids static linking, can't satisfy iOS code-signing, can't keep modifications private — all required for closed-source product. |
| **OCCT** | **LGPL 2.1 + linking exception (free)** | Exception **explicitly permits closed-source commercial linking, including static.** No commercial contract needed. |
| **Visual Studio Enterprise** | 2-3 perf devs only | IntelliTrace + Concurrency Visualizer + advanced profiler earns its price on Windows deep-debug. Rest of team on VS Code. |
| **CMake / Emscripten / Cargo / .NET / MCP / Tauri** | OSS (free) | Permissive licenses; no commercial concern. |
| **Parasolid / ACIS** | **Deferred — year-4+ hypothetical only** | Not budgeted. KAL keeps the swap option without paying for it. |

---

## AI strategy — three steps, not a chat panel

| Step | What ships | When |
|---|---|---|
| **1. AI as a tool** | Markup Assist (PDF redline → DWG edits), Smart Blocks (block detection + conversion), Drawing Health (layer cleanup, dimstyle normalization). Inline commands, deterministic, undoable. | Phase 1 |
| **2. MCP server** | **Local MCP** (host running, commands inside host transaction) + **remote MCP data server** (cloud, read-only DWG queries). Mirrors Fusion 2026's split. Compatible with Claude, Cursor, ChatGPT. | Phase 1–2 |
| **3. Generative CAD** | Only when editable parametric round-tripping is proven. **Hypar's lesson:** text-to-BIM via chat alone was the wrong abstraction. | Phase 3, conditional |

> **The public commitment no competitor has made:** every MCP tool call resolves to **exactly one transaction in the host undo stack**. Revit 2027, Fusion 2026, ARES A3 all shipped agent surfaces without documenting this.

---

## Collaboration — two-tier server-authoritative

**Tier 1 — Geometry (the engine):** Serialized op-log over the engine's mutation stream. Server-validated for referential integrity (door-to-wall, dim-to-entity). Optimistic UI on the client. **The same op-stream serves undo, replication, agent context, and audit.**

**Tier 2 — Annotations, comments, markups, layer properties, sheet titles:** Figma-style **last-writer-wins per property** with fractional indexing for ordering.

What we **don't** do:

- **No generic CRDTs (Yjs / Automerge) on geometry** — they OOM at the millions-of-entity scale typical for an MEP riser DWG.
- **No git-style branch/merge in the UI** — Onshape's model assumes "every user is a software engineer." SMB drafters won't think that way.

Industry has converged here: Figma rejected pure CRDT for LWW; Onshape uses op-log + feature-tree merge; ARES Kudo ships closer to soft-lock + sync. **Our two-tier model leapfrogs ARES's ceiling.**

---

## Extensions — best of both worlds

**Native desktop:** **BRX / ObjectARX-compatible** plugins. Table-stakes for SMB AEC customers switching from AutoCAD. Authenticode signing + "verified publisher" badge.

**Web:** **Onshape-style iframe + OAuth REST.** Sandboxed, capability-scoped. No third-party code in the host process.

**The trick — plugin parity via shared RPC surface:** the same internal command / query API that native plugins call in-process is what web extensions call via OAuth REST. **Same scopes, same semantics, same audit trail.**

> No shipping CAD product has true "write once, run on web and desktop" plugins today. This is closer to it than anyone — and the right scope: API parity, not binary parity.

Marketplace policy: **15% revenue share over a $5K/year free tier** (Apple-equivalent for small developers) — avoid the SolidWorks anti-pattern of mandatory share with no storefront.

---

## What we deliberately don't do

- **No web-first to the installed base** — protects revenue, gets real customer feedback
- **No generic CRDTs for geometry** — confined to non-spatial metadata only
- **No SDS / DIESEL / VBA / COM / ADS** — legacy maintenance contracts with shrinking usage
- **No ObjectARX-compatible .NET surface** — opinionated and modern, set expectation early
- **No Rust in `db` or `render` hot paths** — C++20 stays primary; Rust at the edges
- **No Parasolid in the 3-year budget** — year-4+ hypothetical only
- **No chat-in-canvas as primary AI UX** — Hypar's lesson
- **No two products forever** — IntelliCAD ActCAD enters sunset in Phase 3

Each "don't" closes a door that competitors keep open and pay for.

---

## Migration story for existing customers

- **IntelliCAD-based ActCAD continues to ship through Phase 2.** Sunset date announced when new product reaches GA, not picked up front.
- **LISP migration tool** with measured-corpus coverage ships in Phase 2 for the long tail.
- **Strategic customer .NET / IRX scripts** migrated by a **paid migration service** delivered by the same team that built the new APIs.
- **File formats:** full DWG round-trip parity from Phase 1, validated against a corpus that includes real customer drawings.
- **Pricing:** existing perpetual licenses get an upgrade path to the new product's perpetual tier. AI / cloud features are the new subscription line.

> Two product lines coexist for 24 months. **This is an organizational risk, not a technical one** — and the support / marketing context-switching plan must be built alongside the engineering plan.

---

## What management is being asked to decide *today*

**Approve:**

1. The **4–6 week feasibility spike** — small senior team, dedicated.
2. **ODA Sustaining membership signup** ($7,500) — required for the spike itself.
3. **AI dev tooling subscriptions** (Cursor Business + Copilot Business + Claude Code) for the spike team — ~$400 for 6 weeks.
4. **Reaffirm strategic intent:** this is a 3-year program with revenue-protected migration, not a 12-month deliverable.

**Defer until after the spike:**

- Full 3-year program Go / No-Go (decided on spike data, not on this briefing).
- Qt Commercial multi-year quote negotiation.
- Engineering org standup for Phase 1.
- Phase 1 willing-customer cohort selection.

---

## Discussion — questions for the room

- Are the four differentiating bets (ODA-direct, two-tier co-edit, transactional MCP, API-parity marketplace) the right four? Which would we drop / add?
- Is the **native-Windows-first / web-in-parallel** phasing correct for our customer base, or should we revisit web-first?
- What's the willing-customer cohort look like — are there 5–10 strategic customers we'd commit to a Phase-1 Windows beta in month 12?
- Is the 24-month two-product-line plan operationally acceptable to support + marketing?
- What's our public position on **AI in CAD** going to be — leader, fast-follower, or quiet adopter?
- What's the **competitive intelligence** gap we want to close before the spike?

---

## Appendix — source documents

This briefing summarizes three repository documents (branch `claude/review-skills-plugins-B8xQd`):

| File | Lines | Scope |
|---|---|---|
| `docs/architecture-overview.md` | 183 | Current ActCAD stack, IntelliCAD dependency, lived operational pains |
| `docs/industry-outlook.md` | 119 | CAD segment outlook, 2–5 year horizon, AI / cloud / BIM / pricing trends |
| `docs/rearchitecture-plan.md` | **563** | **Full re-architecture plan — 16 sections covering goal, decisions, modules, stack, phasing, risks, migration, feasibility spike, industry adoption, collaboration, extensions, AI strategy, cost of usage, next steps** |

The plan document is the source of truth. This presentation is the discussion-starter, not the spec.

---

<!-- _class: lead -->
<!-- _paginate: false -->

# Thank you

### Questions?

`docs/rearchitecture-plan.md` · branch `claude/review-skills-plugins-B8xQd`
