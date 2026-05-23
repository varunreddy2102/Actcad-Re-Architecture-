# ActCAD — Architecture, Pros/Cons, and Re-Architecture Implications

## Context

This repo is named `Actcad-Re-Architecture-` but currently contains only `.claude/` plugin configuration — no ActCAD source. Before any redesign work begins, we need a shared picture of:

1. What ActCAD actually *is* under the branding (the stack it's built on).
2. Where the strengths and weaknesses live in that stack.
3. Which architectural decisions the re-architecture must own.

This document is a research deliverable based on **public sources only**. The user will share internal ActCAD material (source, internal design docs, API usage telemetry, etc.) later; this write-up should be revisited and grounded against that material when it arrives.

---

## 1. What ActCAD Actually Is

ActCAD is a commercial DWG-compatible CAD product by **Jytra Technology Solutions Pvt. Ltd.** (East Godavari, India). It is **not** an independent CAD engine — it is an OEM build on top of the **IntelliCAD** engine, with Jytra applying customizations to the ITC source tree.

That single fact dictates almost everything about the architecture.

### 1.1 Layered Stack (bottom → top)

| Layer | Component | Owner | Role |
|---|---|---|---|
| L0 Foundation | **ODA Drawings SDK** (formerly Teigha) | Open Design Alliance | DWG/DXF read/write, drawing database, geometric primitives, rendering primitives |
| L0 Foundation | **ACIS 3D Kernel** | Spatial (Dassault) | Boundary-representation solid modeling for 3D |
| L0 Foundation | **Wintopo / pstoedit** | 3rd-party | Raster-to-vector, PostScript-to-vector helpers |
| L1 Engine | **IntelliCAD source** (currently v14.1 in ActCAD 2027) | ITC consortium | CAD shell on top of ODA: command system, entity model, UI shell, plotting, selection, snap, OSnap, LISP runtime, etc. ITC describes the IntelliCAD source as essentially "a set of examples of how to use the Teigha/IRX interface" |
| L2 Product | **ActCAD modifications** to ITC source | Jytra | Branding, UI tweaks, vertical-app surfaces (Architecture / Mechanical / Electrical / BIM / GIS), licensing, install/update |
| L3 Extension API | LISP, DCL, DIESEL, SDS/ADS (C), IRX (C++), DRX, COM, VBA, .NET, plus CUI/MNU customization | ITC + ActCAD | Customer-written extensions |

Jytra is a paying ITC member, so they receive full IntelliCAD source — that's how they can "make changes to match its requirements, which is not possible with any other OEM CAD engine."

### 1.2 How a Drawing Flows Through the Stack

1. **Open**: ODA Drawings parses the DWG and materializes objects into the in-memory drawing database.
2. **Display**: IntelliCAD's view/render layer walks the database and pushes draw primitives through ODA's GS (graphics system) to GDI/OpenGL/DirectX.
3. **Edit**: Commands (built-in C++ via IRX, or user-written LISP/.NET) mutate the database; the GS invalidates and redraws.
4. **3D ops**: Solid modeling commands hand off to ACIS; results are stored back as ACIS B-rep blobs inside the DWG.
5. **Save**: Database serialized back to DWG via ODA, preserving R2.5 → current compatibility.

---

## 2. Pros of the Current Architecture

- **Cheap to build, cheap to sell.** Buying into IntelliCAD source + ODA + ACIS replaces ~25 years of engine R&D. Retail starts around $199 perpetual.
- **DWG fidelity by construction.** ODA is the de facto non-Autodesk DWG implementation; format compatibility is essentially a solved problem.
- **Source-level access to the engine.** Unlike OEMs of closed engines, Jytra can patch the engine itself for ActCAD-specific behavior.
- **Mature ACIS-backed 3D.** Solid modeling, booleans, fillet/chamfer, etc. are industrial-grade and well-tested.
- **Broad extensibility surface.** LISP/DCL ports of legacy AutoCAD customizations work largely unchanged — a meaningful moat for migrating AutoCAD shops.
- **Multi-core / 64-bit native** per ITC's published platform notes.
- **Ecosystem leverage.** 25+ OEMs share the IntelliCAD platform — bug fixes and ODA upgrades flow downstream automatically.

---

## 3. Cons / Architectural Debt

### 3.1 Strategic (the expensive ones)

- **Cadence is not yours.** Engine major versions (IntelliCAD 14 → 14.1 → 15…) ship on ITC's timeline. Big architectural improvements ActCAD wants either wait for ITC, get carried as a vendor patch (merge pain on every uptake), or get built awkwardly above the engine.
- **Licensing stack is heavy and partly proprietary.** ACIS royalties + ODA membership + ITC fees compound per seat. Any move to undercut Autodesk on price is constrained by these floors.
- **OEM differentiation ceiling.** Most ITC OEMs ship a very similar product because they share the core; meaningful differentiation requires either deep engine forks (merge cost) or new layers above (where ActCAD's vertical apps sit today).

### 3.2 Technical

- **1990s C++ monolith DNA.** IntelliCAD descends from Visio/Softdesk's 1996-era "Phoenix" AutoCAD clone. The object model, command dispatch, and UI shell carry that lineage. Memory model and threading are bolted on rather than designed in.
- **API surface is huge and overlapping.** LISP + DCL + DIESEL + SDS (legacy C) + IRX (C++) + DRX + COM + VBA + .NET. Every API is a permanent maintenance contract with customers. SDS was already deprecated once (during the IntelliCAD 7 ODA transition) and still hasn't fully gone away.
- **Platform locked to Windows in practice.** ODA and ACIS are cross-platform, but the IntelliCAD shell, the .NET/COM/VBA APIs, MFC-style UI, and Jytra's product layer are Windows-centric. macOS/Linux/web are not first-class.
- **Performance ceiling on large drawings.** Public reviews repeatedly cite "moderately large drawings frequently get stuck" — symptomatic of the synchronous main-thread command/render loop typical of the IntelliCAD shell, combined with no enforced memory budget, eager kernel materialization, and linear-scan hit-testing. The re-architecture addresses this with a memory architecture committed up-front rather than retrofitted — see `docs/rearchitecture-plan.md` §16.
- **Vertical apps are loosely integrated.** Architecture / Mechanical / Electrical / BIM are layered as plug-in style modules, not deeply unified — meaning data flows between them are limited.
- **UI paradigm anchored to AutoCAD ~2010.** Ribbon + command line + modal dialogs. Touch, collaboration, and cloud are retrofits.

---

## 4. Implications for a Re-Architecture

The point of writing this document before touching code is to surface the *decisions* the re-architecture must own. Each of these is a fork in the road:

### 4.0 Why the engine decision is forced — three lived pains

The §3 cons are the abstract case for change. What follows is the *concrete* case, drawn from real operating experience running ActCAD on top of IntelliCAD. These three pains are not separate issues — they are three faces of one root cause: **the platform layer isn't ours, so the things that need to be deeply rebuilt can't be.**

#### 4.0.1 Rendering needs per-machine tuning and still isn't fast enough

- ActCAD's viewport renders through ODA's Graphics System (GS), historically OpenGL-based. ODA has been migrating toward Vulkan and ships a DirectX backend, but each step is on ODA's schedule, then ITC's schedule, then ours.
- Customers regularly need OpenGL driver tweaks, GPU-specific switches, and per-system tuning just to get usable performance. Even when tuned, performance ceiling is below what modern competitors deliver.
- Compare: AutoCAD 2027 shipped its own "Graphics System Framework" (GSF) — Autodesk owns the rendering pipeline end-to-end and tunes it as a single product. We cannot match that as a downstream consumer of someone else's renderer.

**What this rules out**: cosmetic fixes. The renderer can only be made truly fast if we own it.

#### 4.0.2 Non-Windows platforms are not within reach

- ODA Drawings and ACIS are cross-platform at the library level. The IntelliCAD shell technically has macOS and Linux ports through ITC, but the customer-facing surface (UI shell, installer, .NET/COM/VBA APIs, LISP/IRX ABI) is Windows-shaped.
- Graebert (ARES) is the one ITC OEM that committed to Linux + macOS + web parity, and they invested at a level most consortium members will not.
- The market has moved: customers expect at minimum macOS support, and increasingly Linux and web. We cannot deliver any of those credibly on the current stack within a reasonable horizon.

**What this rules out**: "we'll port the existing app." The shell is too Windows-shaped to port; it has to be rebuilt with portability in the bones.

#### 4.0.3 AI inside the codebase is structurally blocked

This is the deepest of the three, with two layers:

1. **Access.** ITC consortium license terms restrict sharing IntelliCAD source with third-party services (including AI assistants) and with outside contractors. For any non-employee engagement — code review, external development partner, AI-assisted refactor through a cloud LLM — the foundational engine is dark. We can put our patches and our product layer in front of an AI, but not the layer where the real work would be.

2. **Leverage.** Even setting access aside, we cannot land changes upstream on our own clock. Every AI-assisted refactor on the engine becomes a permanent vendor patch that we carry forever and re-merge on every ITC version uptake. The economics of AI-assisted engineering invert when you can't merge what the AI writes.

**What this rules out**: meaningfully accelerating engine-level work with modern tooling. AI assistance only pays off at the layers we own outright.

#### 4.0.4 Consequence for §4.1

The §3 cons could, in theory, be argued for or against. The §4.0 pains have all been *tried* and found to not be solvable inside the current arrangement. Together they collapse the §4.1 engine decision:

- **Keep IntelliCAD** is not viable as a strategic 5-year posture. It is viable only as a near-term ship vehicle while the replacement is built.
- **Replace, build on ODA directly** is the choice the operating reality is pushing us toward — own the engine, own the renderer, own the platform abstraction, own the codebase that AI can operate on.
- **Replace with non-ODA stack** stays a non-starter (DWG fidelity loss).

The decision below in §4.1 should be read as: *replace; sequencing and migration are what's open, not the direction.*

### 4.1 The four big decisions

1. **Engine: keep or replace IntelliCAD?**
   - *Keep*: lowest risk, preserves DWG fidelity, preserves the LISP/IRX ecosystem, but inherits the monolith and the ITC cadence.
   - *Replace (build above ODA directly)*: ODA Drawings + ODA Visualize + own command/UI layer. Drops the monolith, but you're rewriting ~25 years of CAD shell. Realistic only with a multi-year horizon.
   - *Replace (non-ODA engine)*: would forfeit DWG compatibility — likely non-starter for ActCAD's audience.

2. **3D kernel: stay on ACIS, direct OEM contract.**
   - **Decided: ACIS (Spatial / Dassault), direct OEM contract.** AutoCAD's 3D solids are stored as ASM (Autodesk Shape Manager) — a fork of ACIS that Autodesk took private around 2001 — and DWGs persist them as ACIS / ASM SAT blobs. For lossless round-trip of AutoCAD-origin 3D solids — the central value prop for AutoCAD migrators — ACIS is the only kernel that doesn't introduce translation drift.
   - ActCAD already uses ACIS today (via IntelliCAD); the re-architecture takes the contract direct, drops the IntelliCAD middleman, and keeps customer file fidelity unchanged.
   - All kernel access goes through a **Kernel Abstraction Layer (KAL)** so the engine never depends on ACIS-specific types in public headers; a kernel swap stays technically possible (~6–12 weeks of focused work) if business conditions ever require it.
   - Alternative kernels were considered and rejected on the same basis: anything that isn't ACIS introduces translation drift on AutoCAD-origin SAT blobs. See `docs/rearchitecture-plan.md` §11.2.
   - Commercial terms (initial OEM fee + maintenance + per-seat or per-deployment royalty + component module fees + DELA) are negotiated in Spike 1b under NDA — see `docs/rearchitecture-plan.md` §15.1 for the cost structure.

3. **API surface: which legacies survive?**
   - LISP almost certainly must survive — that's the migration story from AutoCAD.
   - SDS/ADS, DIESEL, VBA, COM are candidates for sunset.
   - A modern story (Python? TypeScript-in-browser? .NET 8+ cross-platform?) is the place to invest.

4. **Platform: Windows-only vs cross-platform / web.**
   - Web is where BIM / collaboration competition is moving (Autodesk Forma, Onshape, etc.).
   - Going web-native is a near-total rewrite of the UI shell — but the engine layers (ODA, ACIS) already have headless / server modes.

### 4.2 Risks to manage

- **DWG round-trip fidelity** — anything that touches the database layer must be measured against the existing DWG test corpus.
- **Customer extension breakage** — quantify which APIs are *actually* used in the wild before sunsetting any of them. (This is one of the first things to ask for from internal material: telemetry or estimate of LISP / IRX / .NET extension distribution among paying customers.)
- **Engine upgrade merge cost** if staying on ITC source — every ActCAD-side patch is a permanent rebase burden.
- **3D kernel migration** is irreversible in practice once shipped to customers — which is why we are *staying* on ACIS rather than migrating. The KAL preserves the technical option to swap, but the business intent is continuity.
- **ACIS commercial exposure** — opaque OEM pricing, royalty per seat or per deployment, change-of-control risk (Dassault owns SolidWorks, a competitor). Mitigated by source escrow + DELA review + business-continuation clauses in the OEM contract; see `docs/rearchitecture-plan.md` §7 and §10.

### 4.3 What to ask of the internal material (when it arrives)

To turn this from a public-info overview into a grounded re-architecture brief, the next pass needs:

- Where ActCAD diverges from stock ITC source (file list / patch volume).
- The build system and module boundaries inside the ActCAD codebase.
- The vertical-app architecture (are they DLL plug-ins? statically linked? sharing a common data model?).
- API-usage telemetry or customer-survey data on LISP / IRX / .NET / SDS.
- Performance hotspots already known internally (large-drawing slowdowns from §3.2 — is the bottleneck the regen, the GS, the DB, or the UI?).
- Licensing exposure: per-seat cost breakdown across ODA, ACIS, ITC.
- Roadmap commitments already made to customers (BIM, cloud, mobile).

---

## 5. Verification

This deliverable is research, not code, so there is nothing to run. The check is editorial:

- §1 (stack) matches what internal docs say about ActCAD's actual layering.
- §3 (cons) is reconciled against internal performance / support data — public reviews are directional but not authoritative.
- §4 decisions are the ones the engineering leadership actually has open. If a decision in §4 is already made internally, this doc should be updated to reflect it rather than re-litigate.

Once internal material lands, re-open this file and either confirm each section or annotate where reality differs.

---

## Sources

- [ActCAD case study — IntelliCAD.org](https://www.intellicad.org/actcad-case-study)
- [ActCAD 2026 released on IntelliCAD 14](https://www.intellicad.org/articles-and-press-releases/actcad-releases-actcad-2026-based-on-intellicad-14)
- [ActCAD 2027 released on IntelliCAD 14.1](https://www.intellicad.org/articles-and-press-releases/actcad-2027-released-built-on-intellicad-14.1)
- [IntelliCAD — Wikipedia](https://en.wikipedia.org/wiki/IntelliCAD)
- [IntelliCAD CAD Development Platform Framework](https://www.intellicad.org/cad-development-platform-framework)
- [Programming with IntelliCAD](https://www.intellicad.org/articles-and-press-releases/bid/204731/Programming-with-IntelliCAD)
- [ActCAD product site](https://actcad.com/)
- [Jytra Technology Solutions](https://www.jytra.com/)
- [BricsCAD vs ActCAD vs AutoCAD comparison — SpotSaaS](https://www.spotsaas.com/compare/bricscad-vs-actcad-vs-autocad)
- [ActCAD reviews — SourceForge](https://sourceforge.net/software/product/ACTCAD-Professional/)
