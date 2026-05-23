# ActCAD Memory Architecture

> **Status:** Architecture document. Companion to `docs/rearchitecture-plan.md` §16 (executive summary). This document is the engineering reference — read it before writing code that touches `db`, `geom`, `render`, or any cache.

## Table of contents

1. [Why this document exists](#1-why-this-document-exists)
2. [Goals and non-goals](#2-goals-and-non-goals)
3. [The CAD memory model in plain terms](#3-the-cad-memory-model-in-plain-terms)
4. [The five-layer model](#4-the-five-layer-model)
5. [The eight commitments — full detail](#5-the-eight-commitments--full-detail)
6. [Concurrency model in depth](#6-concurrency-model-in-depth)
7. [The memory-budget machinery](#7-the-memory-budget-machinery)
8. [The Kernel Abstraction Layer (KAL)](#8-the-kernel-abstraction-layer-kal)
9. [Integration with other modules](#9-integration-with-other-modules)
10. [WASM and the browser shell](#10-wasm-and-the-browser-shell)
11. [Mobile implications (Phase 3)](#11-mobile-implications-phase-3)
12. [Failure modes and recovery](#12-failure-modes-and-recovery)
13. [Telemetry and observability](#13-telemetry-and-observability)
14. [Testing strategy](#14-testing-strategy)
15. [CI gates — exact specifications](#15-ci-gates--exact-specifications)
16. [Tools](#16-tools)
17. [Expertise sourcing](#17-expertise-sourcing)
18. [Anti-patterns — what we will not allow](#18-anti-patterns--what-we-will-not-allow)
19. [Migration from IntelliCAD patterns](#19-migration-from-intellicad-patterns)
20. [Phase-by-phase rollout](#20-phase-by-phase-rollout)
21. [Open questions](#21-open-questions)
22. [Glossary](#22-glossary)
23. [References](#23-references)

---

## 1. Why this document exists

The single most consistent complaint in public reviews of ActCAD today is some variation of: *"moderately large drawings frequently get stuck"*, *"freezes on opening big files"*, *"hangs when saving"*, *"crashes after a long session"*. That reputation is inherited from the IntelliCAD shell — synchronous main-thread command + render loop, no enforced memory budget, eager kernel materialization, linear-scan hit-testing in places where indexes should exist.

**The re-architecture exists in significant part to escape that reputation.** Memory architecture is the place where this is either won or lost. Geometry kernels are fast; renderers are fast; the bottleneck is almost always how the application manages the working set of an active edit session.

This document is the engineering commitment for how the new ActCAD engine manages that working set. It is not a roadmap, not a feature list, and not a survey of options. **It is the rules.** Every engineer joining the team should read this once and know what is allowed, what is forbidden, and which symptoms in the code or in customer reports map to which architectural commitment.

The executive summary lives in `docs/rearchitecture-plan.md` §16. Strategic and budget framing lives in `docs/exec-presentation.md`. This document is the depth.

---

## 2. Goals and non-goals

### 2.1 Goals

1. **Predictable responsiveness across drawing-size distribution.** A 250 MB DWG with 500 3D solids opens, edits, and saves at the same UI fluidity as a 5 MB DWG with 50 entities. Performance degrades gracefully, not in a cliff.
2. **Bounded memory footprint with declared, enforced limits.** Working set is a budget, not an emergent property. Exceeding the budget triggers loud, recoverable failure, never silent paging.
3. **Concurrent edit + render + agent query, with no readers blocked by writers.** The UI stays responsive during a long ACIS boolean. The AI agent can query state during an edit. Co-edit peers replicate without lock storms.
4. **Crash-resilient long sessions.** 8-hour edit sessions don't accumulate heap. Undo storage is bounded. Tessellation cache cannot starve the database.
5. **Measured, not hoped for.** Every commitment in §5 is enforced by CI gates from commit 1, not retrofitted after GA.

### 2.2 Non-goals

1. **Out-of-core / streaming database.** AutoCAD has one. Revit has one. They are multi-person-year investments. We commit to in-RAM-only for the 3-year plan with the budget enforcement that makes in-RAM viable for ActCAD's drawing-size distribution. Out-of-core is a Phase-4+ option only.
2. **Lock-free everything.** We use locks where they're the right tool. The rule is *no reader blocks on a writer*, not *no thread ever waits*.
3. **GPU-resident `db`.** Tessellation lives on the GPU. The drawing database does not. ResizeBAR / GPU-direct-storage are not in scope.
4. **Custom OS-level memory manager.** We use the OS allocator (or mimalloc as a drop-in) plus targeted object pools and arenas. We do not write a slab allocator from scratch.
5. **Pluggable kernels in v1.** The KAL keeps a kernel swap technically possible at ~6–12 weeks of focused work. It is not a runtime-swappable abstraction. ACIS is the only kernel that ships.

### 2.3 Success criteria

A 250 MB DWG with 500 3D solids, opened on a 16 GB / 8-core developer laptop:

- **Open time** ≤ 8 seconds, of which ≥ 80% is disk I/O + DWG parse, ≤ 20% is index build, 0% is eager kernel materialization
- **Steady-state RSS** ≤ 3× the on-disk DWG size (target ≤ 2× for AEC drawings without dense 3D)
- **Pan / zoom / hover P99 frame time** ≤ 16 ms during normal interaction; ≤ 33 ms during background regen
- **Save time** ≤ 4 seconds with a progress bar; UI remains interactive
- **Long-session test** (10,000 edits + undos across 8 hours) ends with RSS within 5% of the post-load baseline
- **Out-of-budget drawing** produces a clear modal: *"This drawing requires X GB; your current budget is Y GB. Close other drawings or raise the limit in Preferences."* — never a force-quit-and-lose-work situation

---

## 3. The CAD memory model in plain terms

### 3.1 Open-once, edit-in-memory, save-back

Every serious CAD product since AutoCAD R1 (1982) follows the same shape: open the drawing once, hold it entirely in memory, do all reads and writes against that in-memory state, write back to disk on save. This is not negotiable and not up for redesign. Out-of-core databases exist (Bentley MicroStation has one, Revit has one) but each represents many engineer-years of investment we do not take on.

What this model gives us:

- **O(1) random access** to any entity by handle
- **Transactional semantics** — a single user gesture maps to a single durable mutation
- **Single source of truth** for renderers, agents, plugins, and the network layer
- **No I/O on the read path** — every query is in-RAM

What this model demands of us:

- The entire working set fits in process memory, or we refuse to open
- Every cache or derived structure must declare its budget and respect a global cap
- Every consumer that holds a reference to a long-lived entity participates in the lifecycle protocol

### 3.2 Why naive in-memory blows up

The naive implementation of "open and hold in memory" loads a 250 MB DWG and assumes the process will use ~250 MB. In practice:

- The DWG **parses to ~2–3×** its on-disk size due to handle tables, attribute dictionaries, xref expansion
- Every 3D solid touched by the user **materializes a kernel `ENTITY` graph** that can be 5–50× the SAT blob size
- Every rendered entity has **GPU-resident tessellation** that scales with view detail
- Every edit appends to an **undo log** that, if implemented as snapshots, can grow unbounded over a long session
- The **renderer caches** invalidation regions, frustum-cull results, and material binds independently
- **Spatial indexes** add 5–10% on top of the entity model
- **Plugins** allocate against the same heap with no accounting

Result: a 250 MB DWG can occupy 4–6 GB of working set, then page when the OS notices, then appear *"frozen"* to the user, then get force-quit. **Every one of these failure modes is preventable. None is prevented by the IntelliCAD shell pattern we are leaving behind.**

### 3.3 What "the drawing in memory" actually contains

The phrase "the drawing in memory" is misleading. There is no single object. There are five distinct things, each with its own size, owner, lifecycle, and pressure-response policy. The architecture in §4 makes this separation explicit so that under pressure, the eviction story is mechanical rather than emergent.

---

## 4. The five-layer model

| Layer | Name | What lives here | Typical size on a 250 MB DWG with 3D solids | Owner module | Pressure response |
|---|---|---|---|---|---|
| **1** | DWG database | Entities, handles, layers, blocks, xrefs, dimstyles, attribute dictionaries, the on-disk SAT blob for every 3D solid (before kernel materialization) | 400–800 MB | `db` | **Never evicted** — single source of truth |
| **2** | ACIS kernel bodies | The materialized `ENTITY` graph for every 3D solid the user has touched since open | 200 MB – 2 GB | `geom` via KAL | **Partial** — body graphs are lazy-loaded on first geometric operation; non-essential attributes can be discarded |
| **3** | Tessellation cache | Triangle meshes + GPU vertex / index buffers for everything currently or recently in view | 500 MB – 4 GB | `render` | **Yes** — LRU evict on pressure; regenerate from B-rep on next view |
| **4** | Spatial indexes | R-tree / BVH for hit-test, snap, frustum cull, selection-window, agent spatial queries | 50–200 MB | `db` (entity index) + `render` (view index) | **Rebuildable** — can be discarded and recomputed from Layer 1 |
| **5** | Undo / op-log | Delta records: every committed transaction's inverse, plus replication and audit fan-out | 100–500 MB over a long session | `db` | **Truncatable** — drop oldest beyond a configurable threshold; warn before truncation |

### 4.1 Layer 1 — DWG database (`db`)

The canonical entity model. Held in process memory for the lifetime of the open document. Mutations go through one transaction queue; reads go through MVCC snapshots (§6). Layer 1 is the **only writable layer** — every other layer is a cache or derived view.

Layer 1 includes the on-disk SAT blob for each 3D solid, **kept in its parsed-but-not-materialized form** until first geometric operation. This is the lazy boundary between Layer 1 and Layer 2.

**Eviction policy: none.** Layer 1 is never evicted. If pressure forces a choice between Layer 1 and any other layer, every other layer evicts first.

**Size discipline:** Layer 1 is bounded by the DWG file content itself. Growth during a session is bounded by user edits (which append to Layer 5 as deltas, not by inflating Layer 1).

### 4.2 Layer 2 — ACIS kernel bodies (`geom` via KAL)

The materialized `ENTITY` graph for each 3D solid the user has performed a geometric operation on. ACIS supports lazy attribute loading natively; we plumb this through the KAL (§8.3) so the engine never materializes 500 solids on file open just because the file contains 500.

**Eviction policy: partial.** When pressure hits, the KAL can drop derived attributes (tessellation hints, healing metadata) but **not the body graph itself** if any consumer holds a reference. Bodies with no active references can be fully unloaded back to SAT-blob form in Layer 1.

**Reference counting** is enforced at the KAL boundary. The KAL holds the only `ENTITY*` pointers; the rest of the engine only sees opaque handles. This is what makes pressure-driven unload safe.

### 4.3 Layer 3 — Tessellation cache (`render`)

Triangle meshes + GPU vertex / index buffers for everything in or near view. Backed by the render backend's native GPU memory (DirectX / Vulkan / Metal / WebGPU).

**Eviction policy: LRU with a hard cap.** Default cap: 30% of process working set, or 1.5 GB, whichever is smaller. The cap is enforced *before* any allocation that would exceed it — evict-then-allocate, never allocate-then-evict.

**Regeneration:** any evicted tessellation can be regenerated from the cached B-rep in Layer 2 (or from Layer 1's SAT blob if Layer 2 was also evicted). Regeneration is a worker-thread task with a progress signal to the render frame loop.

### 4.4 Layer 4 — Spatial indexes (`db` + `render`)

Two kinds:

- **Entity spatial index** in `db` — R-tree over entity bounding boxes; serves hit-test, snap, selection-window, agent "find entities in region" queries. Built at file load (§5.3).
- **View spatial index** in `render` — BVH over visible tessellation; serves frustum cull and ray-cast for picking under the cursor. Rebuilt on view change.

**Eviction policy: rebuildable.** Either index can be discarded and recomputed. The entity index rebuild cost is proportional to entity count (single-digit milliseconds for 100K entities); the view index rebuilds incrementally as the camera moves.

### 4.5 Layer 5 — Undo / op-log (`db`)

A delta record for every committed transaction. The same op-stream that drives:

- **Local undo / redo** — apply the inverse delta
- **Co-edit replication** — ship the delta to the server for fan-out (`docs/rearchitecture-plan.md` §12)
- **AI agent context** — the agent observes the op-stream to track what changed since its last query
- **Audit** — security-relevant operations log to the audit sink

One stream, five consumers. Building it any other way means writing the same plumbing five times.

**Eviction policy: truncate-oldest.** Configurable threshold (default: 10,000 operations or 200 MB, whichever first). When approaching the threshold, the user is warned that further undo will lose history. Replication and audit consumers checkpoint independently and are not affected by local truncation.

### 4.6 Ownership matrix

| Concern | `db` | `geom` (KAL) | `render` | `cmd` | `agent` | `net` | `script` / `plugin` |
|---|---|---|---|---|---|---|---|
| Mutate entity state | ✅ (only) | ❌ | ❌ | ❌ (mediates) | ❌ | ❌ | ❌ |
| Read entity state | ✅ (live) | ✅ (snapshot) | ✅ (snapshot) | ✅ (snapshot) | ✅ (snapshot) | ✅ (snapshot) | ✅ (snapshot via `cmd`) |
| Hold kernel `ENTITY*` | ❌ | ✅ (only) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Own tessellation cache | ❌ | ❌ | ✅ (only) | ❌ | ❌ | ❌ | ❌ |
| Own undo log | ✅ (only) | ❌ | ❌ | ❌ (appends via txn) | ❌ | ❌ | ❌ |
| Open spatial-index queries | ✅ | ❌ | ✅ (view index) | ✅ | ✅ | ❌ | ✅ (via `cmd`) |
| Trigger eviction | ❌ | ✅ (kernel bodies) | ✅ (tess) | ❌ | ❌ | ❌ | ❌ |

### 4.7 Eviction order under pressure

Fixed. Not configurable per-customer because mistakes here cost data integrity.

```
Pressure detected
  ↓
1. Evict LRU tessellation (Layer 3) until below 70% of layer cap
  ↓ still under pressure?
2. Drop view spatial index (Layer 4 render) — will rebuild on next camera change
  ↓ still under pressure?
3. Unload ACIS bodies with no active references (Layer 2 → Layer 1)
  ↓ still under pressure?
4. Truncate oldest entries from undo log (Layer 5), warning the user
  ↓ still under pressure?
5. Drop entity spatial index (Layer 4 db) — will rebuild on next query
  ↓ still under pressure?
6. **Fail loudly to the user** (§7.5) — Layer 1 is never evicted
```

Layer 1 stays put. The user's work is never at risk from a memory-management decision.

---

## 5. The eight commitments — full detail

### 5.1 Single mutator: `db` owns all drawing state

**Rule.** `db` is the only module that holds writable drawing state. Every other module's view of the document is either (a) read-only against a snapshot, or (b) a derived cache that can be discarded.

**Why.** When something is wrong in memory, you always know who to ask. When you want to invalidate everything and start fresh, you blow away every cache and Layer 1 is intact. When two modules need to agree on what the document says, they look at the same source.

**Enforcement.** Public mutation API on `db` is a small surface (`begin_transaction`, `add_entity`, `remove_entity`, `modify_entity`, `commit_transaction`, `abort_transaction`). No other module exports a function that returns a writable handle to a `db` entity. Code review rejects any PR that introduces one. CI rule (clang-tidy custom check) flags non-`db` modules that return non-`const` references to entity types.

**Tradeoff accepted.** Every cross-module change to the document costs a transaction round-trip. This is the price of integrity and we pay it cheerfully.

### 5.2 MVCC: reads never block writes (and writes never block reads)

**Rule.** Mutations on `db` happen on one worker thread, serialized through a transaction queue. Reads happen on any thread, against a **copy-on-write snapshot** of the committed state.

**Why.** This is the single most important commitment in the architecture. It is what makes the UI stay at 60fps while a long ACIS boolean runs, what makes the AI agent able to query state during an edit, what makes co-edit possible without lock storms. The pattern is decades-old (PostgreSQL, every modern RDBMS); the CAD industry has been slow to adopt it because CAD databases were historically single-threaded.

**Mechanics (§6 has the full detail).** Every entity is internally versioned. A snapshot is a (lightweight) reference to a version vector. Mutations write new versions; old versions are reclaimed once no snapshot references them. Snapshots are cheap to acquire (`O(1)`) and cheap to release (`O(1)` amortized).

**What this is not.** It is not optimistic concurrency control — there are no merge conflicts in this layer because mutations are serialized. It is not lock-free — there are locks, but they're short and on the write path. It is not generic CRDTs — see §6.4.

**Enforcement.** Every public read API on `db` takes a `Snapshot` parameter. No public read API operates on "current state." Code that wants "current" calls `db.snapshot()` to acquire one. CI rule rejects any read API that omits the snapshot parameter.

### 5.3 Spatial index built at load time

**Rule.** The moment a drawing finishes parsing, the entity R-tree is built. Hit-test, snap, frustum cull, selection-window, and agent spatial queries all go through the index. **Linear scan over entities is not a public API on `db`.**

**Why.** This is the single decision that separates snappy from unusable on a 250K-entity drawing. The index build is a one-time cost at load (single-digit milliseconds per 10K entities); without it, every hover, every pick, every snap is `O(N)`.

**Mechanics.** R-tree built bottom-up from entity AABBs. Updates on commit: each transaction's modified-entity list drives `O(k log N)` index updates where `k` is the modified count.

**Enforcement.** `db` does not export `for_each_entity()`. Spatial queries are `db.query(region, filter)`. Code review rejects any traversal that bypasses the index for performance-sensitive paths. CI gate measures hit-test P99 on the synthetic drawing corpus.

### 5.4 Lazy materialization of ACIS bodies

**Rule.** ACIS bodies stay as opaque SAT blobs in `db` until the first geometric operation on that body. Open time is bounded by parse + index, **not** by kernel materialization.

**Why.** A drawing with 500 3D solids that the user never touches should not pay 500× the kernel-materialization cost on open. The user clicks one solid; we materialize one solid.

**Mechanics.** The KAL `Body::ensure_materialized()` is called by every geometric operation. If the body is already a kernel `ENTITY`, no-op. If it's still a SAT blob, parse + materialize on the calling thread (typically a worker), record the materialization in the KAL's reference map.

**Eviction.** Materialized bodies with no active references can be unloaded back to SAT-blob form under pressure (Layer 2 → Layer 1). The KAL tracks references via opaque handle counts.

**Enforcement.** KAL is the only module that calls into ACIS. No `ENTITY*` appears in any public header outside the KAL. CI rule (header grep) fails if `ENTITY` or any ACIS type appears in a non-`geom` header.

### 5.5 GPU-resident, evictable tessellation

**Rule.** Once a body is tessellated, the triangles go to GPU memory (vertex + index buffers in the active render backend) and stay there for the render loop. Under CPU memory pressure, LRU tessellation is evicted; on next view, it's regenerated from the cached B-rep.

**Why.** GPU-resident tessellation is what makes the render loop run at GPU speed instead of bus speed. Eviction policy keeps Layer 3 bounded so it can never starve Layer 1.

**Mechanics.** Render backend abstraction (`docs/rearchitecture-plan.md` §4) presents a uniform vertex buffer API across DirectX 11/12, Vulkan, Metal, WebGPU. Tessellation cache is keyed on (body handle, view-detail level). LRU tracks last-frame-used.

**Hard cap.** Default 30% of process working set, or 1.5 GB, whichever is smaller. Tunable per-platform (mobile defaults are lower; see §11). Allocation that would exceed the cap evicts first.

**Regeneration.** Worker-thread task. The render loop draws a placeholder (wireframe, low-LOD proxy) while regeneration is in flight. Frame time stays under 16 ms even during a regeneration burst.

### 5.6 Delta-based undo

**Rule.** Every undoable operation stores its inverse, not a snapshot of the world. Reversing `move(handle, dx, dy)` is `move(handle, -dx, -dy)` — bytes, not megabytes.

**Why.** Full-state snapshots are what blow heap in long sessions. AutoCAD survives 8-hour edit sessions because undo is incremental. We do the same.

**The op-stream is the universal substrate.** The same delta record drives:

1. **Local undo / redo**
2. **Co-edit replication** (`docs/rearchitecture-plan.md` §12)
3. **AI agent context** (`docs/rearchitecture-plan.md` §14)
4. **Audit log** (security-relevant ops only)
5. **Render invalidation** (which regions need redraw)

**Mechanics.** Each delta is `(op_id, timestamp, txn_handle, inverse_payload, forward_payload)`. The forward payload is what was applied (for replication); the inverse is what undo applies. Both are typed FlatBuffers messages.

**Truncation.** When the op-log exceeds threshold, oldest entries are dropped. User sees a warning before truncation. Replication and audit consumers checkpoint independently — local truncation doesn't lose their state.

### 5.7 Declared memory budget; fail loudly, never silently swap

**Rule.** The engine boots with a declared memory budget. Each cache layer has a sub-budget. When a sub-budget is exceeded, the layer evicts per §4.7. When the total budget is exceeded after eviction, **the engine fails loudly to the user** with a clear modal — never silently swaps to disk.

**Why.** Silent swap is the worst possible failure mode. The user thinks the app is frozen, force-quits, and loses work. Loud failure is recoverable; silent swap is a support ticket and a churn risk. *"The app is slow"* is a 1-star review. *"The app told me I needed more RAM and pointed me to the setting"* is a question we can answer.

**Budget formula (default).**

```
budget = min(
    2 × loaded_DWG_size_on_disk,
    process_working_set_limit − OS_headroom
)
```

Where `OS_headroom = 1 GB` on desktop, `512 MB` on mobile, `256 MB` in WASM. User can raise the cap in Preferences up to the OS limit; reducing below the working-set requirement triggers a refusal to open.

**Sub-budgets.** Layer 1 has no sub-budget (it's whatever the document needs). Layer 2 capped at 50% of remaining budget. Layer 3 capped at 30%. Layers 4 + 5 each capped at 10%.

**Loud-failure UX.** Modal dialog:

> *"This drawing requires X.X GB of memory. Your current budget is Y.Y GB. Options:*
> - *Close other open drawings (currently using Z.Z GB)*
> - *Raise the memory budget in Preferences → Performance*
> - *Open this drawing in a separate ActCAD process (uses fresh budget)*
> - *Open in read-only mode (uses 60% less memory)"*

No silent failures. No vague *"out of memory"* errors. Always a recoverable action.

### 5.8 8 ms UI-thread budget

**Rule.** The UI thread does input + render only. Every operation that could take more than 8 ms goes to a worker. Frame budget asserts in debug builds: any UI-thread work over 8 ms triggers a debug break.

**Why.** *"Slow on the UI thread"* is a build-breaking error from commit 1. Customers don't file tickets for *"the cursor lagged for 30 ms"* — they just churn. Profilers in CI catch this; debug-build asserts catch it locally before commit.

**What goes to a worker.**

- File I/O of any kind (open, save, plot)
- ACIS operations (boolean, fillet, sweep, blend)
- Regen (full or partial)
- Index build / rebuild
- Tessellation generation
- Network round-trips (sync, agent, telemetry)
- Plugin operations longer than 1 ms (enforced at the `cmd` boundary)

**What stays on the UI thread.**

- Mouse / keyboard input parsing
- Snapshot acquisition (`O(1)`)
- Spatial index queries (sub-millisecond on a 100K-entity drawing)
- Render command submission (GPU-resident; CPU work is bounded)
- Cursor / selection-marquee updates
- Property panel redraws against the current snapshot

**Frame budget assertion.** Debug builds wrap each main-loop iteration with a timer; if the iteration exceeds 8 ms, the assertion logs the call stack and breaks into the debugger. Release builds log to telemetry without breaking. CI gates on P99 frame time prevent regression.

---

## 6. Concurrency model in depth

### 6.1 Threads we use

| Thread | Count | Responsibility |
|---|---|---|
| **UI** | 1 | Input parsing, render-command submission, snapshot acquisition, fast read-only queries |
| **Mutation worker** | 1 | All `db` mutations, serialized through the transaction queue |
| **Render worker** | 1 | Tessellation regeneration, GPU buffer uploads, view-index incremental updates |
| **Kernel worker pool** | 2–8 (CPU-count dependent) | ACIS operations (booleans, fillets), heavy geometric computation |
| **I/O worker** | 1 | File open, save, plot, telemetry flush |
| **Net worker** | 1 | Sync, agent, MCP, document service |
| **Agent worker** | 1 | MCP request handling, tool dispatch |

Total at idle: 8–14 threads, of which most are blocked on a condition variable. Active threads at any moment in a typical edit session: 2–4.

### 6.2 The transaction queue

The mutation worker pulls one transaction at a time from a single-producer-multi-consumer queue. Every command (from `cmd`) that mutates state enqueues a transaction; the worker dequeues, executes, validates, and commits.

```
        cmd (UI thread or worker)
              ↓ enqueue
        transaction queue
              ↓ dequeue (serialized)
        mutation worker
          1. begin_transaction()  → working_copy
          2. apply ops              → working_copy
          3. validate              (referential integrity, kernel checks)
          4. commit_transaction()  → publish new snapshot version
          5. emit op-stream record → consumers (undo, sync, agent, audit, render)
```

**Why a single mutation thread instead of fine-grained locking.**

- Serialization eliminates an entire class of race conditions
- The mutation worker is throughput-bound, not latency-bound — adding more threads doesn't help when the bottleneck is `O(log N)` index updates
- Validation logic is simpler when mutations are serial
- ACIS itself is largely single-threaded within one body — multi-threading the mutation worker would not help kernel operations

### 6.3 Snapshot mechanics (copy-on-write)

Every entity carries an internal version counter. When a transaction commits, modified entities get incremented versions; the previous versions stick around in a per-entity version chain.

A `Snapshot` is a (lightweight) timestamp plus a reference count. Acquiring a snapshot is `O(1)`. Reads through a snapshot walk the version chain to find the largest version ≤ snapshot timestamp.

Old versions are reclaimed when no live snapshot references them (reference-counted GC at the snapshot level, not the entity level). The reclamation happens on the mutation worker after commit; it does not block readers.

**Snapshot lifetimes.**

- **Frame snapshot** — render thread acquires at the start of each frame, releases at frame end. Lifetime: ~16 ms.
- **Query snapshot** — hit-test, snap, agent query. Lifetime: < 1 ms typically.
- **Long-running snapshot** — agent that wants a stable view during a multi-step plan; co-edit peer that's applying a remote op-stream. Lifetime: seconds to minutes. Bounded by a maximum snapshot age (default: 30 seconds) after which the snapshot is forcibly released and re-acquired.

**Memory cost.** Version chains are bounded by the snapshot horizon. Typical overhead: 1.05–1.15× the base entity size. Under sustained edit load with no long-running snapshots, overhead converges to ~1.02×.

### 6.4 The op-stream as the universal substrate

The op-stream emitted by `db` on every commit serves five consumers:

1. **Undo** — stores the inverse delta in Layer 5
2. **Co-edit replication** — `net` ships the forward delta to the server (`docs/rearchitecture-plan.md` §12)
3. **AI agent context** — `agent` observes the stream to track changes between queries (`docs/rearchitecture-plan.md` §14)
4. **Render invalidation** — `render` reads the stream to know which spatial regions need redraw
5. **Audit** — security-sensitive operations (signed save, license validation) log to the audit sink

**Stream guarantees.**

- **Ordered** — strictly in commit order
- **Lossless to subscribers** — each consumer has a checkpoint; if a consumer falls behind, the stream backpressures (rare; mutation throughput is bounded)
- **Typed** — FlatBuffers schema with versioning
- **Replayable** — given a checkpoint, the stream can be replayed to rebuild downstream state

**What this is NOT.**

- Not a generic CRDT — see `docs/rearchitecture-plan.md` §2.7 for the co-edit model
- Not eventual-consistency — the stream is server-authoritative at the network boundary
- Not append-only forever — Layer 5 truncates oldest entries past threshold

---

## 7. The memory-budget machinery

### 7.1 Budget declaration and discovery

On engine boot, the runtime queries:

- **Process working set limit** — OS-specific (Windows: `GetProcessMemoryInfo`; macOS / Linux: `getrlimit(RLIMIT_AS)`; WASM: `wasm_memory_max`)
- **Available physical RAM** — for the loud-failure UX hint
- **User Preferences override** — defaults to *"computed"*, can be raised to a hard cap

Budget formula (default):

```
hard_cap = min(
    user_preference_cap (if set),
    OS_working_set_limit − OS_headroom
)

soft_target = min(
    2 × sum(open_DWG_sizes_on_disk),
    hard_cap
)
```

`soft_target` drives eviction. `hard_cap` drives loud failure.

### 7.2 Sub-budgets per layer

Defaults, expressed as fractions of `(hard_cap − Layer_1_actual)`:

| Layer | Default sub-budget |
|---|---|
| Layer 2 (ACIS bodies) | 50% |
| Layer 3 (tessellation) | 30% |
| Layer 4 (indexes) | 10% |
| Layer 5 (undo log) | 10% |

Sub-budgets are advisory in the sense that any layer can briefly exceed its share if others are below theirs. They are enforcing in the sense that `total ≤ hard_cap` is hard.

### 7.3 Eviction protocol

When a layer is asked to allocate and would exceed its sub-budget:

1. Layer attempts internal eviction (LRU or layer-specific policy)
2. If still over: layer requests budget extension from the engine's memory broker
3. Memory broker checks global state; if other layers are under their sub-budget, extension granted
4. If no slack available globally: broker triggers pressure-cascade per §4.7

The broker is a single small module (`mem_broker`) owned by `platform`. It is the single point of truth for budget state. All allocations go through it for accounting (it doesn't replace `malloc`; it tracks).

### 7.4 Pressure signals and OS APIs

The engine subscribes to OS memory pressure notifications:

- **Windows:** `CreateMemoryResourceNotification` + WM_COMPACTING
- **macOS:** `dispatch_source_create(DISPATCH_SOURCE_TYPE_MEMORYPRESSURE)`
- **Linux:** `cgroup memory.pressure_level` (where available); fallback to RSS polling
- **iOS / Android:** OS lifecycle callbacks (`didReceiveMemoryWarning`, `onTrimMemory`)
- **WASM:** allocator failure (no OS signal; we react to `malloc` returning null)

On any pressure signal, the broker triggers a level-appropriate eviction cascade before the OS starts paging.

### 7.5 Loud-failure UX

When the engine cannot satisfy a memory request after exhausting eviction:

1. The operation that triggered the allocation is **aborted cleanly** (transactional — no partial state)
2. The UI surfaces a modal with **concrete options** (close other drawings, raise budget, separate process, read-only mode)
3. The current document state is **untouched** — Layer 1 is intact, all committed work is preserved
4. Auto-save fires (if enabled) before the modal appears, as a belt-and-braces measure

What we never do:

- Display *"Out of memory"* with no actionable guidance
- Silently degrade to disk-backed mode without telling the user
- Force-quit
- Lose any committed mutation

---

## 8. The Kernel Abstraction Layer (KAL)

### 8.1 What the KAL hides

The KAL is the only module that imports ACIS headers. Its purpose:

1. **Hide ACIS-specific types** so they never appear in non-`geom` headers
2. **Encapsulate ACIS memory semantics** (`ENTITY` derivation, `lose()` lifecycle, attribute attachment) behind a clean RAII surface
3. **Make lazy materialization (§5.4) a property of the layer**, not a discipline of every caller
4. **Preserve the kernel-swap escape hatch** at ~6–12 weeks of focused work if business conditions ever require it

### 8.2 Opaque handle convention

Public types in `geom`:

- `BodyHandle` — opaque 64-bit identifier; valid for the lifetime of the document
- `FaceHandle`, `EdgeHandle`, `VertexHandle` — opaque 64-bit identifiers; valid for the lifetime of their parent body
- `BodyRef` — RAII guard that holds a body materialized while the ref is alive

No public type exposes an ACIS `ENTITY*`, `BODY*`, `FACE*`, or any kernel-specific structure.

### 8.3 Lazy materialization contract

```
BodyRef KAL::acquire(BodyHandle h)
    // If h refers to an already-materialized body: returns immediately, increments ref count
    // If h is still SAT-only: parses SAT, materializes, increments ref count
    // BodyRef destructor decrements; if count reaches zero AND under pressure, body
    //   is unloaded back to SAT form on a worker thread

template<typename Op>
auto KAL::with_body(BodyHandle h, Op op)
    // Scoped acquire+execute+release
    // Preferred API for callers that don't need long-lived refs
```

Callers in `cmd` and `script` use `with_body` for one-shot operations. The render module holds `BodyRef`s for currently-visible bodies, releasing them as bodies move out of view.

### 8.4 Memory ownership rules across the KAL boundary

- The KAL **owns** every materialized kernel object
- `BodyHandle` etc. are values that callers can store freely; they do not own memory
- `BodyRef` is a refcount guard; callers must release (RAII handles this)
- No caller may `delete` a kernel object — there is no public API that returns one
- The KAL is single-threaded internally for kernel operations on a given body; cross-body parallelism is delegated to the kernel-worker pool

---

## 9. Integration with other modules

### 9.1 `render` and the tessellation cache

`render` subscribes to the op-stream and invalidates affected tessellation entries on each commit. The tessellation cache is keyed on `(BodyHandle, detail_level)`; invalidation drops all detail levels for the affected body.

Render frames operate against a `Snapshot` acquired at frame start. The frame loop:

```
1. snapshot = db.snapshot()
2. visible = view_index.query(camera_frustum, snapshot)
3. for each entity in visible:
       if tessellation_cache.has(entity): submit_draw_call(entity)
       else: enqueue_tessellation(entity); submit_placeholder(entity)
4. snapshot release (automatic at scope exit)
```

The frame loop never blocks on a missing tessellation; it submits a placeholder (wireframe or low-LOD) and renders the real version on a subsequent frame.

### 9.2 `cmd` and transaction boundaries

Every `cmd` invocation (LISP call, .NET call, MCP tool call, UI command) maps to **exactly one** `db` transaction:

```
cmd.execute(command, args):
  1. parse + validate args
  2. txn = db.begin_transaction()
  3. try:
       run command logic; mutations go through txn
       db.commit_transaction(txn)
     except:
       db.abort_transaction(txn)
       re-raise
  4. emit op-stream record (on successful commit)
  5. surface UI feedback / return value
```

**Public commitment.** Every MCP tool call resolves to exactly one transaction in the host undo stack (`docs/rearchitecture-plan.md` §2.6). This commitment is enforced at the `cmd` boundary; no module bypasses it.

### 9.3 `agent` and read-only snapshots

The MCP agent operates against snapshots for read queries, and through `cmd` for mutations. The agent **never holds a snapshot for longer than 30 seconds** without re-acquiring; long-running plans re-query as they go.

The agent observes the op-stream to update its working context between queries; this is how it tracks *"what changed since I last looked"* without holding a stale snapshot indefinitely.

### 9.4 `net` and op-stream replication

`net` subscribes to the op-stream, batches deltas, and ships them to the document service for fan-out to co-edit peers. The local engine does not wait for ack before considering the local commit final — server authority resolves any conflicts at the geometry plane (`docs/rearchitecture-plan.md` §12).

`net` maintains its own checkpoint into the op-stream; local truncation of Layer 5 does not affect replication state.

### 9.5 `script` and `plugin` — sandboxed access patterns

Scripts (LISP, Python, JS bridge) and plugins (.NET, native) reach `db` only through `cmd`. There is no public read API on `db` exposed to plugins — they go through `cmd.query(...)` which acquires a snapshot per call.

**Long-running plugin operations** (more than ~1 ms estimated, or any I/O) are dispatched to a worker by `cmd`. The UI thread is never held by plugin code longer than the budget allows.

**Plugin memory accounting.** All plugin allocations route through the memory broker (`platform.mem_broker`) so the budget includes plugin overhead. A plugin that blows the budget is killed cleanly with a user notification — it does not bring down the engine.

---

## 10. WASM and the browser shell

### 10.1 The 4 GB browser memory ceiling

WebAssembly currently caps process memory at 4 GB (32-bit address space, even on 64-bit hosts). The browser shell budget defaults are correspondingly tighter:

| Layer | Default native cap | Default WASM cap |
|---|---|---|
| Layer 2 (ACIS bodies) | 50% of available | **Layer 2 not active in browser** — ACIS not in WASM (Phase 1–2) |
| Layer 3 (tessellation) | 30% / 1.5 GB | 25% / 800 MB |
| Layer 4 (indexes) | 10% | 10% |
| Layer 5 (undo log) | 10% / 200 MB | 10% / 100 MB |

### 10.2 Allocator implications

We do not use mimalloc or jemalloc in WASM — Emscripten's bundled allocator is what we ship. The memory broker accounts in the same way; only the underlying `malloc` differs.

### 10.3 Tessellation differences (WebGPU vs native)

WebGPU has stricter buffer size limits than native APIs (typically 256 MB per buffer, vs 4 GB on Vulkan). Large meshes are chunked. The chunking is handled in `render`'s WebGPU backend; the rest of the engine is unaware.

### 10.4 ACIS in the browser — translator path only

No public production WASM build of ACIS exists as of writing. For the 3-year plan:

- **Phase 1–2 browser shell:** ODA's read-only translators present geometry to the browser as static meshes. No browser-side ACIS editing. The browser is a viewer + 2D editor + markup tool.
- **Phase 3 (open question):** if customer demand for browser-side 3D editing materializes, the path is either (a) bespoke ACIS WASM engineering with Spatial, or (b) server-side ACIS with the browser shipping ops to a kernel server. Decision deferred to Phase-3 planning with customer data.

---

## 11. Mobile implications (Phase 3)

### 11.1 iOS app memory limits

iOS imposes per-app memory limits that vary by device generation: typically 1.5–4 GB available before the OS kills the app. Memory pressure signals (`didReceiveMemoryWarning`) fire well before the kill threshold; the engine treats these as immediate eviction triggers.

### 11.2 Android Vulkan considerations

Android memory limits are looser but Vulkan driver overhead varies wildly by vendor. The render backend keeps GPU memory tracked separately from CPU RSS in the budget formula.

### 11.3 When to refuse to open

On mobile, drawings that would exceed 80% of available budget after eviction trigger a refuse-to-open with a clear explanation:

> *"This drawing is too large to open on this device (requires X GB; this device has Y GB available to apps). Open on desktop, or use the Lightweight View mode."*

Lightweight View mode is a read-only tessellation-only mode that skips Layer 2 entirely.

---

## 12. Failure modes and recovery

| Failure mode | Detection | Recovery |
|---|---|---|
| OOM during long ACIS operation | Memory broker returns null on allocation | Transaction aborts cleanly; pre-edit snapshot remains; user sees the loud-failure modal (§7.5) |
| Tessellation cache thrash (LRU churn under tight budget) | Frame time P99 exceeds 33 ms for >5 consecutive frames | Render downshifts to a lower default detail level; user notified once per session |
| Worker thread crash | Worker watchdog (heartbeat-based) | Crashed worker restarted; in-flight transaction rolled back; user notified with crash report option |
| Plugin-induced memory pressure | Broker accounting attributes growth to a plugin | Plugin sandbox kills the plugin; engine intact; user sees plugin-killed notification |
| Corrupted op-stream record | Consumer-side schema validation | Replication and audit consumers checkpoint roll back; local undo continues; corruption logged for post-mortem |
| ACIS internal error (kernel-side exception) | KAL exception handler | Transaction aborts; KAL state cleaned via `lose()` discipline; user sees operation-failed message; bug filed with CTC |
| Document larger than budget on open | Pre-open size estimate | Loud-failure modal before any work is done; no partial open state to clean up |
| Snapshot horizon exceeded | Snapshot age tracker | Forced release; consumer re-acquires; query restarts from new snapshot |

---

## 13. Telemetry and observability

### 13.1 What we log

Counters and histograms shipped to telemetry (per-session, aggregated):

- Open time per drawing size bucket
- Frame time P50 / P95 / P99 per session
- Peak RSS per session
- Eviction event count per layer per session
- Transaction count, commit success rate, abort rate
- Snapshot count, snapshot lifetime distribution
- Loud-failure modal count + which option the user chose
- Worker crashes (rare; high-signal)
- ACIS operation latency P99 by operation type

### 13.2 What we never log (PII)

- Drawing content
- Entity coordinates
- File names or paths
- Customer identifiers in raw form (hashed only)
- Plugin code or plugin-supplied data

Telemetry is opt-in by default for new installs, with a clear settings toggle. Enterprise customers may disable entirely.

### 13.3 The "performance health" customer-visible badge

A small status indicator in the bottom-right corner shows real-time engine health:

- **Green** — frame time on budget, memory comfortable
- **Yellow** — sustained pressure (frame P99 > 16 ms, or memory > 80% of budget)
- **Red** — pressure with active eviction; suggests user action

Clicking the badge opens a diagnostic panel with the current state of all five layers, budget usage, and eviction recent history. This is what support tickets reference instead of *"the app is slow."*

---

## 14. Testing strategy

### 14.1 The DWG corpus

Fifty curated DWGs across five size / complexity buckets:

| Bucket | Size on disk | Entity count | 3D solid count | Count in corpus |
|---|---|---|---|---|
| Small | 1–10 MB | 1K–10K | 0–10 | 10 |
| Medium | 10–50 MB | 10K–50K | 10–100 | 15 |
| Large | 50–150 MB | 50K–200K | 100–500 | 15 |
| Huge | 150–500 MB | 200K–1M | 500–2000 | 5 |
| Pathological | varies | varies | varies | 5 (deliberately hard) |

The corpus lives in a separate licensed repository (size + licensing prevents inlining). CI pulls a curated subset for PR runs; nightly runs cover all 50.

### 14.2 Synthetic loops

For each corpus drawing:

- **Open-loop** — open, hold for 5s, close. Measures open time, peak RSS during open, RSS after close.
- **Interact-loop** — open, run a scripted pan-zoom-rotate-hover sequence for 60s. Measures frame time histogram, peak RSS, GPU memory usage.
- **Edit-loop** — open, run a scripted move-rotate-fillet sequence (50 operations), save, close. Measures transaction throughput, undo log growth, save time.
- **Pressure-loop** — open with budget set to 80% of the drawing's natural working set. Verifies eviction cascade triggers cleanly and the loud-failure modal appears at the right point.

### 14.3 Long-session soak

Nightly job: open the largest non-pathological drawing, perform 10,000 randomized edits with periodic saves, close. RSS at end must be within 5% of post-load baseline. Any growth beyond 5% is a leak and the job fails.

### 14.4 Sanitizers in CI

Debug-build CI runs with AddressSanitizer + LeakSanitizer enabled. Zero leaks tolerated. ThreadSanitizer enabled on a subset of tests (the MVCC machinery, the transaction queue) — too expensive for full coverage.

---

## 15. CI gates — exact specifications

### 15.1 Open-time gate

For each corpus drawing, open time must be ≤ the documented baseline × 1.10 (10% regression budget). New PR fails if median across 5 runs exceeds threshold.

### 15.2 Frame-time gate

For each interact-loop, P99 frame time must be ≤ 16 ms steady state, ≤ 33 ms during background regen bursts. Regression beyond these = fail.

### 15.3 Memory ceiling gate

Per drawing class, hard RSS ceiling:

| Class | Steady-state RSS ceiling |
|---|---|
| Small | 500 MB |
| Medium | 1.5 GB |
| Large | 4 GB |
| Huge | 8 GB |
| Pathological | drawing-specific |

PR exceeding any ceiling = fail.

### 15.4 Allocation count gate

Open-edit-save loop allocation count tracked per build. A 2× increase from baseline (single PR) is suspicious — flagged for review. A 5× increase is a hard fail. This catches accidental allocator-bypass (someone forgot to use the entity pool).

### 15.5 Leak gate

AddressSanitizer + LeakSanitizer on every debug CI run. Any leak = fail. No suppression list except for documented third-party leaks (with reference to upstream bug).

### 15.6 Soak gate

Nightly. Final RSS within 5% of post-load baseline = pass. PR-level approximation: a 1000-edit shortened version of the soak that completes in ~5 minutes, with a looser 10% threshold.

### 15.7 Failure handling — what counts as a flake

CI gates can flake. Policy:

- **Open-time / frame-time** — flake threshold is 1 failure in 3 retries; if 2 of 3 fail, that's a real regression
- **Memory ceiling / leak / allocation count** — zero tolerance; any failure is real
- **Soak** — single-fail allowed if reproducible only at large scale; re-run on a dedicated bare-metal runner for verification

---

## 16. Tools

### 16.1 Tracy (always-on)

[Tracy](https://github.com/wolfpld/tracy) is the primary profiler. Every developer build links Tracy; running the engine attaches Tracy automatically on localhost. Frame time, allocation rate, GPU timing, and zone-based CPU profiling are visible in real time.

### 16.2 Intel VTune (deep dives)

For CPU-heavy investigations (kernel operation profiling, allocator hot paths). Used by the perf team during dedicated investigations, not in every build.

### 16.3 Heaptrack and Massif

Linux-only deep memory analysis. Used when the soak gate fails and we need to find the leak.

### 16.4 Visual Studio Diagnostics + WPA

Windows-specific. Visual Studio Diagnostics for CPU + memory in development; Windows Performance Analyzer for system-level traces when investigating customer-reported issues.

### 16.5 AddressSanitizer + LeakSanitizer

CI-enabled on every debug build. Local builds can enable via a CMake flag. ThreadSanitizer enabled on the MVCC test subset.

### 16.6 mimalloc / jemalloc as system `malloc`

`mimalloc` is the default native allocator (drop-in `malloc` replacement). 10–30% wins on allocation-heavy CAD workloads with near-zero integration cost. `jemalloc` is the backup if mimalloc surfaces issues. Neither is used in WASM (Emscripten heap only).

---

## 17. Expertise sourcing

### 17.1 Spatial CTC

The ACIS OEM contract bundles Corporate Technical Consulting hours (typically 20–40 hours per year). These are engineering-level consultations, not sales support. **First conversation in Phase 1: get the ACIS team to review the KAL design before we commit to it.** Worth a half-day of their time and saves quarters of trial-and-error.

### 17.2 External performance engineers

Toptal, Round Table Group, Guidepoint, GLG all have networks of ex-AutoCAD, ex-Revit, ex-SolidWorks, ex-Fusion performance engineers available for hourly consultations ($300–$800/hr). **Budget 40–80 hours in Phase 1 specifically for memory architecture review.** One day of an ex-AutoCAD perf engineer is worth a month of internal trial-and-error.

### 17.3 Peer back-channels

Other ACIS OEMs (Bentley, Hexagon, ANSYS SpaceClaim, BobCAD) face the same challenges. Architects at these companies are often willing to talk informally at conferences (DevCon, Spatial Summit) about KAL design and memory architecture. Not a substitute for paid consultation, but valuable for sanity-checking decisions.

---

## 18. Anti-patterns — what we will not allow

### 18.1 Snapshot-based undo

Storing a full document snapshot per undo entry is the simplest implementation and the wrong choice. Memory growth is catastrophic over long sessions. Delta-based undo (§5.6) is the rule.

### 18.2 Eager attribute loading

Loading all entity attributes when an entity is read into memory wastes work and memory. Attributes load on first access. Property panel queries one entity's attributes at a time, not all of them.

### 18.3 Linear-scan hit-testing

Iterating over all entities for hit-test is `O(N)` and unusable at scale. The spatial index is mandatory. PRs that introduce a scan over entities for picking, snap, or selection are rejected.

### 18.4 Synchronous file I/O on the UI thread

Open, save, plot, autosave — all on workers. The UI thread does not block on disk. Ever.

### 18.5 Allocator-of-the-week thrash

We pick one allocator (mimalloc) and stay with it. We don't introduce per-module allocator overrides. The exception is targeted object pools for hot small-object allocation (entity handles, transient command state); those are bounded, documented, and reviewed.

### 18.6 Plugin direct-`db` access

Plugins go through `cmd`. There is no plugin API that returns a writable handle to a `db` entity. This is the line that, once crossed, makes every commitment above optional — so we don't cross it.

### 18.7 GC-based memory management in the engine hot path

RAII + opaque handles. GC introduces unpredictable pauses; pauses kill responsiveness. The Rust crates (`net`, `agent`) use Rust's ownership model, not GC; the C++ core uses RAII.

### 18.8 Hidden caches

Every cache declares itself to the memory broker. There are no per-function `static` caches, no thread-local growable maps, no *"oh and also we cache this little thing"*. If it's a cache, it's a registered, bounded, evictable cache.

---

## 19. Migration from IntelliCAD patterns

### 19.1 What we inherit (nothing)

The new engine is a clean break. We do not port IntelliCAD code. We do not port IntelliCAD patterns. We do not port IntelliCAD memory assumptions.

### 19.2 Patterns we deliberately don't copy

- **Single global state object accessible from anywhere** — replaced by `db` as a module with a defined public API
- **Synchronous main-loop command dispatch** — replaced by `cmd` with worker dispatch for anything long-running
- **Eager full-document load** — replaced by lazy materialization (§5.4)
- **Per-feature renderer tuning** — replaced by a single render abstraction with backend-specific implementations
- **Plugin direct database access** — replaced by `cmd`-mediated access only

### 19.3 What to teach engineers coming from IntelliCAD

Engineers joining from an IntelliCAD background should be onboarded with explicit teaching that:

1. There is no global "current drawing" object — you ask `cmd` for a snapshot
2. You do not modify entities directly — you submit a transaction
3. You do not iterate over all entities — you query the spatial index
4. You do not load a kernel body unless you're about to operate on it
5. You do not allocate freely — your allocation may trigger eviction, and that's the design
6. You do not block the UI thread for anything, ever

The first month for any new engineer includes a code-review pass on this document and a paired implementation of a small command end-to-end (parse args → snapshot → query → transaction → commit → op-stream emit) to internalize the pattern.

---

## 20. Phase-by-phase rollout

### 20.1 Phase 1 (months 0–12) — foundations

- The five-layer model is in place from commit 1
- All eight commitments enforced from commit 1
- CI gates 1–6 (open-time, frame-time, memory ceiling, allocation count, leak, soak) active by month 3
- Tracy + sanitizers wired in from commit 1
- KAL surface complete; ACIS integration complete
- The Phase-1 Windows beta to willing customers ships with the loud-failure UX in place

### 20.2 Phase 2 (months 12–24) — co-edit + AI integration

- The op-stream gains its replication and agent-context consumers
- Long-running snapshot patterns validated for the agent's multi-step plans
- WASM browser shell shipped with the tighter mobile-class budgets
- Lightweight View mode shipped for browser + mobile
- Performance health badge shipped to users

### 20.3 Phase 3 (months 24–36) — mobile + scale-out

- iOS + Android shells with mobile-class budgets
- Refuse-to-open UX validated on mobile-class devices
- Telemetry maturity — customer-reported issues triaged from the performance health badge in 80%+ of cases
- Out-of-core threshold re-evaluation: if customer drawings routinely exceed budget, scope the Phase-4 out-of-core work

---

## 21. Open questions

These are decisions deferred to specific points in the plan, not gaps in the architecture:

1. **Out-of-core / streaming database trigger.** What customer signal (P95 drawing size, frequency of loud-failure modals) tells us we need to take on out-of-core for Phase 4? Decision point: end of Phase 2, based on telemetry.

2. **Browser ACIS WASM viability.** Is full kernel editing in the browser worth the bespoke engineering with Spatial? Decision point: mid-Phase 3, based on browser-shell usage data and customer requests.

3. **Agent context window vs op-stream truncation.** Long agent sessions can exceed the agent's context window; do we summarize op-stream chunks, or rely on the agent to checkpoint? Decision point: Phase-2 agent GA planning.

4. **Snapshot horizon tuning.** Default 30s for long-running snapshots — is that too aggressive for the agent's multi-step plans? Tunable; data-driven decision in Phase 2.

5. **Memory broker accuracy on Linux cgroups v2.** Pressure signals on Linux are less reliable than other platforms — do we need a custom RSS-polling fallback? Decision point: Phase-2 Linux shell QA.

6. **ODA Visualize scene graph synchronisation.** The `render` module wraps ODA Visualize, which has its own scene graph. The plan does not describe how that scene graph is kept in sync with `db` changes from the op-stream — whether Visualize entities are updated in-place on the mutation worker, rebuilt from scratch per frame, or maintained as a parallel representation. This is the most concrete open question for the render module's Phase-1 implementation. Decision point: render module design spike, Phase-1 month 1–2.

7. **Multi-document (MDI) memory partitioning.** The loud-failure UX references "close other open drawings," implying multiple DWGs open simultaneously. The memory budget formula (`2 × loaded_DWG_size`) applies to a single document. Questions that need answers before MDI ships: does each document own an independent tessellation cache sub-budget, or do they share one pool? Does the tile cache (§17.6 in the plan) partition per-document or per-viewport? How does the broker attribute pressure to the correct document? Decision point: Phase-2 cloud document service design.

8. **Xref loading strategy.** External references (xrefs) are separate DWG files embedded by reference. The plan treats entities as a flat namespace but xrefs are a tree of separately-loaded documents. Open questions: are xref DWGs loaded eagerly on parent open or lazily on first viewport intersection? Does each xref contribute to the parent document's budget or carry its own sub-budget? How are xref handle namespaces isolated so they don't collide with the host document's handle table? This is a Phase-1 DWG fidelity requirement — the round-trip corpus will contain xrefs. Decision point: `db` module design, Phase-1 month 1.

9. **Undo grouping for compound operations.** The delta log stores one record per atomic mutation. A command like `ARRAY` creating 1,000 entity copies produces 1,000 delta records. Pressing Ctrl-Z must undo all 1,000 as one user-visible step. The plan says "every MCP tool call = one undo group" but the grouping mechanism — how `cmd` opens and closes a named group across multiple `db` transactions — is not specified. Without explicit undo grouping, complex commands either undo atomically (requiring a group protocol) or require the user to press Ctrl-Z 1,000 times. Decision point: `cmd` + `db` module design, Phase-1 month 1.

10. **Proxy entity handling.** DWG files produced by third-party applications (custom ObjectARX objects, vertical products) contain proxy entities — entity types for which we have no definition. The plan does not state whether these are: (a) preserved as opaque blobs and round-tripped faithfully, (b) shown as bounding-box placeholders, or (c) silently dropped. Silent drop breaks DWG round-trip fidelity for the vertical-product customers in our target market. Faithful preservation is the correct default; it requires the `db` entity model to carry an opaque-blob slot. Decision point: `db` entity model design, Phase-1 month 1.

11. **OSnap (object snap) geometric pipeline.** The plan assigns snap queries to the entity R-tree index. The R-tree returns candidates; the precise snap computation (nearest endpoint, midpoint, intersection of two curves, tangent, perpendicular) is a separate geometric operation. Intersection snap in particular requires solving for curve–curve intersection, which is a non-trivial computation that belongs in `geom`, not `db`. The module that owns the OSnap pipeline — the query sequencing, candidate ranking, aperture filtering, and snap-point computation — is not specified. If this ends up scattered across `cmd`, `db`, and `geom` without a clear owner, it becomes a maintenance and performance problem. Decision point: module design, Phase-1 month 2.

12. **DPI and display scaling.** High-DPI displays (Retina, 4K, 200% Windows scaling) require the render pipeline to distinguish between logical pixels (what the UI layout uses) and physical pixels (what the GPU renders). The tile cache tile size (512×512 px in §17.6) is ambiguous without this distinction — on a 2× Retina display, 512 logical pixels is 1024 physical pixels, 4× the GPU work. The LOD tier breakpoints (§17.3) are stated in pixels and are similarly ambiguous. The coordinate system that the `render` module works in — physical or logical — must be declared in the module contract. Decision point: render module design, Phase-1 month 1.

---

## 22. Glossary

- **AABB** — Axis-Aligned Bounding Box. Used for entity-level spatial indexing.
- **ACIS** — The 3D B-rep kernel from Spatial (Dassault). Our chosen kernel; see `docs/rearchitecture-plan.md` §11.2.
- **ASM** — Autodesk Shape Manager. A fork of ACIS Autodesk took private around 2001. AutoCAD's 3D solids use ASM internally; DWG persists them as ACIS-compatible SAT blobs.
- **BVH** — Bounding Volume Hierarchy. Used for view-level spatial indexing.
- **CRDT** — Conflict-free Replicated Data Type. The co-edit architecture uses CRDTs for annotations only (Layer 5 metadata plane), not for geometry. See `docs/rearchitecture-plan.md` §2.7.
- **DELA** — Distribution License Agreement. Spatial's contract terms beyond pricing.
- **DWG** — Drawing format. The canonical on-disk representation.
- **KAL** — Kernel Abstraction Layer. The `geom` module's encapsulation of ACIS.
- **LRU** — Least Recently Used. Default eviction policy for the tessellation cache.
- **MVCC** — Multi-Version Concurrency Control. The pattern that lets readers not block writers. PostgreSQL uses this.
- **op-stream** — The typed stream of committed transactions emitted by `db`. Universal substrate for undo, replication, agent, render invalidation, audit.
- **R-tree** — Spatial index data structure. Used for the entity index in `db`.
- **RAII** — Resource Acquisition Is Initialization. C++ pattern for lifetime-bound resource management. We use RAII heavily for kernel body refs, snapshots, transactions.
- **SAT** — Standard ACIS Text. The on-disk text serialization of an ACIS body. DWG stores 3D solids as SAT blobs.
- **Snapshot** — An immutable view of `db` state as of a point in time. Acquired in `O(1)`; held by every read-side consumer.
- **Working set** — The portion of process memory actively in use. What we budget against.

---

## 23. References

### ODA SDKs

- [ODA Drawings SDK](https://docs.opendesign.com/td/) — entity model, transaction API, spatial filter
- [ODA Visualize](https://docs.opendesign.com/tv/) — render abstraction, GPU buffer management
- [ODA inWEB](https://www.opendesign.com/products/web) — WASM compilation path for browser shell

### ACIS

- [Spatial ACIS](https://www.spatial.com/solutions/3d-modeling/3d-acis-modeler) — base kernel
- [ACIS components](https://www.spatial.com/products/3d-acis-modeling) — module list (Local Operations, Healing, Defeaturing, Polyhedral, AGM, HLR, Lop, ASM)
- Spatial CTC consultation (bundled with OEM contract; first session in Phase 1 reviews the KAL design)

### MVCC and database concurrency

- [PostgreSQL MVCC documentation](https://www.postgresql.org/docs/current/mvcc.html) — the canonical implementation
- [SQLite WAL mode](https://www.sqlite.org/wal.html) — a simpler MVCC variant; useful conceptual reference

### Tooling

- [Tracy profiler](https://github.com/wolfpld/tracy)
- [mimalloc paper](https://www.microsoft.com/en-us/research/uploads/prod/2019/06/mimalloc-tr-v1.pdf)
- [Heaptrack](https://github.com/KDE/heaptrack)
- [AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)

### Companion documents

- `docs/rearchitecture-plan.md` §16 — executive summary of this document
- `docs/rearchitecture-plan.md` §3 — module decomposition (which this document elaborates on for memory)
- `docs/rearchitecture-plan.md` §12 — collaboration architecture (Layer 5 op-stream consumer)
- `docs/rearchitecture-plan.md` §14 — AI agent strategy (Layer 5 op-stream consumer)
- `docs/architecture-overview.md` — current-state pain points that this document's commitments address
