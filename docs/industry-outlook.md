# CAD Industry Outlook — ActCAD's Segment, 2–5 Year Horizon

## Scope

This document looks forward 2–5 years (≈ 2026 → 2031) at the slice of the CAD market ActCAD competes in:

- **Product class**: DWG-native 2D drafting plus light/mid 3D; AutoCAD-alternative positioning.
- **Pricing class**: low perpetual / affordable subscription (typically <$500 / seat).
- **Verticals**: AEC SMBs, MEP, Electrical, Mechanical drafting, GIS, Civil/Survey.
- **Geographies**: India + SEA + LATAM + EU SMBs + NA cost-conscious.
- **Direct peers**: BricsCAD, ZWCAD, GstarCAD, progeCAD, ARES (Graebert), DraftSight, NanoCAD; plus free/open (LibreCAD, FreeCAD, NanoCAD Free).

It is paired with `docs/architecture-overview.md`. Every trend below ends with an implication that feeds §4 of that document.

---

## 1. Five forces reshaping the segment

### 1.1 AI assistance becomes table stakes (12–24 months)

- AutoCAD 2027 ships native integration with Anthropic's Model Context Protocol so the editor exposes drawing context to LLM agents.
- Graebert ARES 2027 ships **A3** (AI assistant) with multi-task prompting, AI-generated blocks, command recommendations, and voice interaction in Kudo.
- Industry estimates put AI handling 20–30 % of routine drafting work today, growing fast.
- By 2028, products without an in-editor AI assistant will read as legacy to evaluators.

**Implication for ActCAD re-arch**: AI is no longer a feature; it's a layer. The new architecture must expose a stable, structured representation of the drawing database to an LLM/agent runtime — an MCP-style server or equivalent — *before* anything else gets modernized. This is the single most consequential decision in §4.1 of the architecture doc, ahead of the "keep or replace the engine" question.

### 1.2 Cloud + web + mobile parity becomes baseline (24–36 months)

- AutoCAD 2027 introduced real-time multi-user editing of the same DWG plus Forma cloud integration.
- ARES delivers near-feature-parity desktop + web + mobile + Linux — the line industry analysts now use to define "modern" CAD.
- Onshape and Fusion's web app already define "cloud-native CAD" (app + database in cloud, microservices, multi-tenant co-edit) as the reference posture for new entrants.
- Quote that frames the period: *"In 2026, cloud-based CAD collaboration is no longer a nice-to-have — it is the standard."*

**Implication for ActCAD re-arch**: even if the primary deliverable stays a desktop binary, the *database and command model* must permit a server-side / multi-user mode. Decisions in §4.1 ("engine: keep or replace") and §4.4 ("Windows-only vs cross-platform / web") of the architecture doc become joined — the engine choice has to leave a path to web. The Graebert ARES + ARES Kudo pattern (shared engine, three UIs) is the most credible reference architecture for ActCAD's size.

### 1.3 BIM / CAD convergence moves downmarket (24–60 months)

- Global BIM market growing ~14.7 % CAGR through 2028.
- Mandated BIM adoption rising globally; estimates put adoption at ≈80 % by 2026 and ≈90 % by 2028 in mature regions.
- SMB BIM adoption is blocked by license + hardware cost (often >$50 k / firm) and by the trained-staff shortage (48 % of construction firms cite hiring difficulty).
- That gap — "BIM-light for SMBs" — is the largest underserved opportunity in this segment.

**Implication for ActCAD re-arch**: invest in ActCAD's BIM vertical at a multiple of investment in pure 2D drafting. The architecture must let BIM share a unified object model with 2D drawing entities (not a bolted-on side database), so SMB users can climb the BIM curve incrementally rather than buying a separate product. Revisit §3.2 of the architecture doc — "Vertical apps are loosely integrated" — this is the bullet that hurts most in the 5-year horizon.

### 1.4 Pricing models fragment, perpetual partially returns (ongoing)

- Subscriptions hit 68 % of new US CAD purchases in 2024.
- Counter-trend in 2026: notable customer-side migration *back* to perpetual where available, driven by subscription fatigue and Autodesk's named-user enforcement.
- Indian SME market, conversely, is moving *toward* subscription — low IT budgets favour opex.
- Net direction is hybrid: perpetual base license + optional cloud/AI subscription add-on.

**Implication for ActCAD re-arch**: ActCAD's perpetual model is an asset, not a liability — but only if the architecture cleanly separates the *local desktop core* (perpetual) from *cloud-delivered services* (AI assistant, co-edit, asset library, twin-data sync). The license boundary needs to be an architectural seam, not a business afterthought. This becomes a fifth bullet in §4.1's decisions.

### 1.5 Digital twin + IoT enters the SMB MEP conversation (36–60 months)

- MEP digital twins via IoT — sensors livestreaming into the BIM model — are normalizing for facilities operators.
- AI-driven segmentation of point clouds / reality-capture scans is collapsing the time to produce as-built MEP models.
- Currently big-firm / big-budget, but the tooling stack (ODA's ifc/point-cloud SDKs, AI segmentation libraries, MQTT/IoT brokers) commoditizes fast.

**Implication for ActCAD re-arch**: the MEP and Electrical verticals — the most loyal portion of ActCAD's user base — need a 3-year story for ingesting reality-capture data and a 5-year story for streaming IoT data into the model. The object model needs an extensible "non-CAD payload" hook from the start, not retrofitted.

---

## 2. Where ActCAD's user base is going

| User segment | 2–5 year direction | ActCAD posture |
|---|---|---|
| **AEC SMBs (architects)** | Pulled toward BIM, priced out of Revit; want Revit-lite | **Invest** — best fit for BIM-light bet (§1.3) |
| **Mechanical drafting / job-shop manufacturing** | Pulled toward Onshape / Fusion cloud-MCAD; desktop DWG share declines | **Defend, don't grow** — table-stakes MCAD, not a growth area |
| **Electrical / MEP contractors** | Most loyal to ActCAD-class tools; digital-twin overhang | **Invest** — verticalize hard; this is the moat |
| **Civil / survey** | Increasingly tied to Carlson, Civil 3D, OpenRoads | **Partner or exit** — not a defensible standalone position |
| **GIS** | Losing share to QGIS, ArcGIS Pro | **De-emphasize** — not where to put R&D dollars |

---

## 3. Geographic forecast

- **APAC ≈ 40 %** of new CAD-startup funding globally; the gravitational center of the SMB CAD market is moving east.
- **India** SMB market is shifting to subscription / cloud — ActCAD's home turf but actively contested by ZWCAD (China) and GstarCAD; home-field advantage is real but not durable without product differentiation.
- **EU** consolidating around Graebert (ARES) for mid-market DWG-CAD; perpetual licensing remains viable.
- **NA** subscription fatigue creates a window for low-cost perpetual, but evaluators now expect AI + cloud as baseline.

---

## 4. What this means for the re-architecture

Mapping each trend back to the decisions in `docs/architecture-overview.md` §4:

| Trend | Affects decision | New posture |
|---|---|---|
| §1.1 AI assistance | §4.1 engine choice; new "AI/agent surface" decision | AI/agent API is the **first** modernization layer, ahead of engine swap |
| §1.2 Cloud parity | §4.1 engine + §4.4 platform | Engine choice must preserve a server-side / multi-user path |
| §1.3 BIM downmarket | §3.2 vertical integration | Unified object model across 2D + BIM; vertical apps move from plug-ins to first-class |
| §1.4 Hybrid pricing | new decision: license seam | Architectural separation of local-perpetual core vs cloud-subscription services |
| §1.5 Digital twin / IoT | §4.2 3D kernel and object model | Object model must allow non-CAD payloads (sensor streams, reality-capture meta) without engine forks |

The bigger picture: a 2-year-out ActCAD that is just "cheaper AutoCAD with AI sprinkled in" is the losing position, because every peer (BricsCAD, ZWCAD, ARES, GstarCAD) will be there too and Autodesk will outspend everyone on AI. A defensible 5-year-out position is **"AI-assisted, cloud-collaborative, BIM-capable CAD for SMB AEC and MEP, priced perpetual + optional cloud subscription, India-first"**. The architecture work is what makes that position physically possible.

---

## Sources

- [Autodesk AutoCAD 2027 — Architosh](https://architosh.com/2026/04/autodesk-2027-adds-strong-new-features/)
- [ARES 2027 deep dive — Architosh](https://architosh.com/2026/05/ares-2027-deep-dive-ai-automation-and-bim-to-dwg-workflows/)
- [Graebert ARES 2027 + Forma — Architosh](https://architosh.com/2026/04/graebert-releases-ares-2027-ai-push-and-forma-integration/)
- [7 CAD design trends 2026 — Shalin Designs](https://shalindesigns.com/blog/cad-design-trends-2026-ai-cloud-digital-twin/)
- [CAD drafting trends 2026 — CADdrafter](https://caddrafter.us/cad-drafting-trends/)
- [AI in CAD 2026 — Fabrixon](https://fabrixon.com/ai-in-cad/)
- [5 BIM trends 2026 — United-BIM](https://www.united-bim.com/5-innovative-trends-shaping-the-future-of-bim-technology/)
- [BIM adoption worldwide 2026 — Novatr](https://www.novatr.com/blog/bim-adoption-around-the-world-global-overview)
- [BIM software market 2034 — Dataintelo](https://dataintelo.com/report/bim-software-market)
- [Cloud-native CAD features — Onshape](https://www.onshape.com/en/blog/features-defining-cloud-native-cad)
- [Cloud CAD collaboration 2026 — Orbit Training](https://orbittraining.ae/software/easily-collaborate-with-others-using-cloud-based-cad-tools/)
- [India CAD software market — PS Market Research](https://www.psmarketresearch.com/market-analysis/india-cad-software-market)
- [AutoCAD perpetual license 2026 — ZWSoft](https://www.zwsoft.com/blog/autocad-perpetual-license)
- [Perpetual vs subscription 2026 — DEV.to](https://dev.to/olivier_moussalli_e3492f5/perpetual-vs-subscription-licenses-which-business-model-wins-in-2026-19nb)
- [Digital twin for MEP — Autodesk University](https://www.autodesk.com/autodesk-university/article/Digital-Twin-Bringing-MEP-Models-Life-2021)
- [Electrical digital twin market — BRI](https://www.businessresearchinsights.com/market-reports/electrical-digital-twin-software-market-117162)
