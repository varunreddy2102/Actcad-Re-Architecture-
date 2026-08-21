# TejasCAD — Encrypted, Platform-Blind Licensing Architecture

> *Working brand: TejasCAD, subject to TM clearance (`docs/brand-shortlist.md` §7). This document specifies the licensing subsystem in enough detail that legal, security, and prospective members can audit the promise. Cryptographic choices below are illustrative-but-defensible — final selections happen after the Phase 1 security review with an external crypto auditor.*

---

## 0. What this document is

The single hardest promise TejasCAD makes to its members is: **"Ship your licensing through our infrastructure. We give you a working license server, a license file format, an offline validator, revocation, renewals, floating seats, all of it. And we cannot see your customer list, your seat counts per customer, your pricing, your license contents, or any drawing data. Neither can anyone else who breaches us."**

This document specifies how that promise is kept — the threat model, the key hierarchy, the artifact structure, the flows for issuance / validation / renewal / revocation, what TejasCAD *does* see (aggregate counters and platform-royalty attestations, and nothing else), what safeguards keep us honest about that, and how a member proves the property to their own customers.

Companion to `docs/platform-strategy.md` §3 (which introduces the licensing seam) and `docs/tejascad-company-structure.md` §5 (which establishes IP ownership).

---

## 1. Requirements — in the words of each stakeholder

### 1.1 A member vendor's requirements

- **"I want a working license server on day one — perpetual, subscription, floating-seat, node-locked, all four modes."**
- **"Nobody at TejasCAD can see my customer list, my per-customer seat counts, my pricing, or which of my customers is renewing when."**
- **"I can prove to a customer under NDA that TejasCAD cannot see their license file contents."**
- **"If TejasCAD is breached, my license database and my customer data are not in the breach."**
- **"If TejasCAD terminates my membership, I can keep serving my existing customers under a survival clause — the license infrastructure keeps working for the seats already sold."**
- **"I control my own license keys. Not a shared secret. Not something TejasCAD can regenerate without my consent."**

### 1.2 An end customer's requirements (my member's customer)

- **"The license file on my laptop cannot be read by anyone but me."**
- **"When I renew, my company name and email are not visible to a third party (TejasCAD)."**
- **"When the software phones home, it doesn't send TejasCAD my drawing contents or my identity."**
- **"If my member vendor goes out of business, I have a documented failover — my perpetual seats keep working; my subscription seats have a grace period plus a defined process."**

### 1.3 TejasCAD's requirements (what we DO need to see, aggregated only)

- **Platform-royalty attestation for ACIS per-deployment counting.** ACIS master contract requires deployment counts. We need a defensible, auditable **number**, not identities.
- **License-server uptime / health metrics.** We host the infra; we monitor the infra. We see request rates, error rates, latency — never contents.
- **Aggregate telemetry with member consent.** Total active seats per member for billing (which is a number the member already tells us; we cross-check but never derive from customer identities).
- **Anti-piracy signal at the aggregate level.** We can tell a member "your license key is being used from 12 different countries in the last hour" as an anomaly signal, without seeing who those users are.

### 1.4 Regulators' requirements (GDPR, DPDPA India, CCPA)

- Personal data of end customers processed only by the member, not by TejasCAD. TejasCAD is not even a data processor for that layer.
- Cryptographic proof that platform architecture supports the "no access" claim — not just a policy assertion.
- Right to erasure at the member level; TejasCAD provides tooling but does not hold the data being erased.

---

## 2. Threat model — what we defend against

| Threat | Attacker capability | Defense |
|---|---|---|
| **Casual license theft** | End user copies license file to another machine | Node-lock via machine fingerprint; hardware-signature binding in the license artifact |
| **Sophisticated piracy** | Reverse-engineered validator, patched binaries | Not addressed here (addressed in `platform-strategy.md` platform-signing + tamper detection); licensing layer assumes binaries are trusted |
| **Compromise of TejasCAD infrastructure** | Attacker steals all data at TejasCAD's license service | Attacker gets ciphertext + aggregate counters only; no plaintext of license contents, no customer identities, no seat counts per customer |
| **Compromise of a member's license authority** | Attacker steals a member's signing key | Compromise is scoped to that member — other members unaffected; revocation path documented |
| **Compromise of an end-customer machine** | Attacker steals license file + local key material | License is bound to that machine (node-lock); moving to another machine invalidates it |
| **Malicious insider at TejasCAD** | An engineer with production access wants to read a member's data | Data at rest is encrypted with keys the insider does not hold (keys are held per member in a KMS the insider does not have console access to); data in transit uses per-member envelope encryption |
| **Legal compulsion on TejasCAD** | Government orders TejasCAD to hand over customer identities | We can hand over the ciphertext we hold, which is useless without the member's key. We cannot break the crypto for the government any more than we can for an attacker |

The last row is why this design is *architectural* rather than *policy*. A "we promise not to look" policy fails against subpoena. A "we don't hold the keys to look" architecture doesn't.

---

## 3. Cryptographic key hierarchy

Four levels of key material, each with a documented lifetime, rotation policy, and holder.

### 3.1 Platform Root (TejasCAD-held)

- **Purpose.** Signs the master platform certificate that all member License Authorities chain to. Establishes the "this is a legitimate TejasCAD platform member" trust root.
- **Algorithm.** Ed25519 (fast signature, small key, well-analyzed) with a fallback RSA-4096 root for legacy systems.
- **Storage.** Offline HSM in a physical vault; used only for annual re-issuance ceremonies.
- **Rotation.** 10-year lifetime with 2-year overlap for rotation.
- **What TejasCAD can decrypt with this key.** Nothing. This key only signs; it doesn't encrypt.

### 3.2 Member License Authority Key (member-held, TejasCAD-generated on member onboarding)

- **Purpose.** Each member gets their own License Authority (LA) key pair. All licenses that member issues are signed with the LA private key. The LA public key is signed by the Platform Root, so end-user validators can chain-verify the license → LA → Platform Root without contacting the network.
- **Algorithm.** Ed25519 for signing + X25519 for key agreement (or comparable NIST P-256 for compliance environments).
- **Storage.** **Held by the member.** TejasCAD generates the initial pair as a bootstrap convenience, transmits it under one-time envelope encryption, and immediately deletes its copy after signed member confirmation. Member is expected to store it in their own KMS / HSM / Vault. **This is the architectural key — the private LA key never lives in TejasCAD infrastructure after handoff.**
- **Rotation.** Member-driven. TejasCAD provides tooling to rotate (issue new LA, publish revocation for the old, migrate customers over 90-day overlap).
- **What TejasCAD can decrypt with this key.** **Nothing. We don't have it.** The member's licenses are signed by a key we do not hold and cannot regenerate.

### 3.3 Per-License Symmetric Keys (member-generated, license-scoped)

- **Purpose.** Each license artifact contains an encrypted payload (customer identity, seat count, feature entitlements, expiry, node-lock fingerprint) protected by a symmetric key. That symmetric key is wrapped for the specific end-customer's machine (client-side key derivation) so only that machine can decrypt the payload.
- **Algorithm.** AES-256-GCM for payload; the wrapping key is derived from an X25519 ECDH between the member's LA and a machine-generated end-user key pair.
- **Storage.** The wrapped key ships inside the license file. The unwrapping key lives on the end-user's machine, tied to hardware.
- **What TejasCAD can decrypt with this key.** **Nothing.** We don't have the member's LA private key, and we don't have the end-user machine's key. Even if we intercepted every license file in flight, we cannot open one.

### 3.4 Aggregate Attestation Key (member-held, TejasCAD-verified)

- **Purpose.** The one number TejasCAD needs — deployment count for ACIS royalty attribution — is produced by a **member-generated attestation**: a signed statement of the form "member M attests it has 12,847 active deployments this quarter." The attestation is signed by the member's LA and verified against a cryptographic accumulator that binds attestations to previous attestations (so a member cannot silently deflate a number without proof of decline).
- **Algorithm.** Signed count + Merkle-tree accumulator; optional zero-knowledge proof for advanced auditors to verify aggregate consistency without revealing per-license detail.
- **Verification.** TejasCAD verifies the signature and accumulator consistency. If a member's attestations are structurally inconsistent (e.g., a sudden 50% drop with no revocation events), that triggers an audit conversation, not automatic action.
- **What TejasCAD sees.** A number per quarter, per member. Nothing more.

---

## 4. License artifact structure

A single license file is a structured binary (recommended: Protocol Buffers or CBOR) with the following fields:

| Field | Encrypted? | Signed? | Who reads it |
|---|---|---|---|
| **Version** | No | Yes | Everyone |
| **Member LA public key + Platform Root signature chain** | No | (chain) | Validator |
| **License ID (opaque UUID)** | No | Yes | Everyone; TejasCAD sees this for aggregate attestation only |
| **Issued-at timestamp** | No | Yes | Everyone |
| **Wrapped symmetric key** (X25519-ECDH-derived, wrapped to end-user's machine key) | (it is itself a wrapper) | Yes | End-user machine only |
| **Encrypted payload** (customer name, org, email, seat count, features, node-lock fingerprint, expiry, tier) | **Yes** (AES-256-GCM) | Yes | End-user machine only after unwrap |
| **Feature-entitlement hash** | No | Yes | Validator uses this to check hasCapability(X) without decrypting the whole payload |
| **Revocation list URL + last-good timestamp** | No | Yes | Validator periodically checks; hard offline mode uses last-known-good |

**Key property.** The only unencrypted fields are: version, key chain, an opaque UUID, timestamps, entitlement hashes, and revocation-check URL. **No customer identity, no seat count, no pricing, no member customer-facing info is ever visible outside the end-user's machine.**

---

## 5. Issuance flow (what happens when a member sells a license)

1. Member's sales system captures customer info in the member's own systems.
2. Member's License Portal (either self-hosted or hosted by TejasCAD under the member's LA) generates the license artifact.
3. Payload is encrypted with a fresh symmetric key. Symmetric key is wrapped to the end-user's machine key at first-run (§6) or wrapped for offline delivery if the customer is provisioning air-gapped.
4. Artifact is signed with the member's LA private key.
5. Artifact is transmitted to the end user (email, download portal, whatever the member's business flow is).
6. **The License ID (opaque UUID)** is registered with TejasCAD's aggregate-attestation service — this is the only fact TejasCAD learns. Customer identity, seat count, and pricing never leave the member's systems.
7. Member's attestation Merkle-accumulator adds this License ID; next quarterly attestation includes it in the signed total.

**What TejasCAD's servers see during issuance:** an opaque UUID, a member ID, a timestamp. Nothing else.

---

## 6. Activation flow (end-user first-run)

1. User installs the member's branded CAD product. Enters license key or drops in license file.
2. Local validator checks signature chain (License → LA → Platform Root) with only public keys — **fully offline.**
3. First-run activation: local validator generates a fresh machine key pair from a Trusted Platform Module (TPM), Secure Enclave, or software equivalent bound to hardware fingerprint. Sends the machine public key to the **member's activation service** (not TejasCAD).
4. Member's activation service unwraps the license's wrapped symmetric key with the LA private key + re-wraps it with the machine public key. Returns to the end user.
5. Local validator now has the machine-scoped wrapped key; it can decrypt the payload and read seat count / features / expiry.
6. **TejasCAD sees:** nothing in this entire flow. Activation is a member ↔ end-user transaction.

**Optional online-check mode.** For subscription tier only, the local validator periodically checks a revocation list (fetched over HTTPS from the member's revocation endpoint, or from a mirror TejasCAD hosts for members who don't want to run their own). The check request contains only the opaque License ID and a signed "still alive" token; no customer data.

---

## 7. Renewal, revocation, and revocation-list distribution

- **Renewal.** Handled entirely inside the member's systems. A new license artifact is issued with a new expiry; the old artifact is optionally added to the revocation list. TejasCAD sees a UUID transition in aggregate attestation, nothing more.
- **Revocation.** Member publishes a signed revocation list at a URL the license artifact references. TejasCAD hosts a mirror of the revocation list for members that don't want to run their own — but the list is signed by the member's LA, and the contents are opaque UUIDs, so hosting the mirror gives TejasCAD zero additional information.
- **Cascade revocation.** If the member's LA is compromised, the Platform Root can revoke the LA. Validators reject any license whose LA is revoked. Member issues a new LA (§3.2) and migrates their active customers over a 90-day overlap window.
- **Offline hard mode.** Certain regulated / air-gapped environments cannot phone home. Validator supports a "last-known-good" mode: if the revocation list can't be reached, the license is honored for a member-configurable grace period (default 30 days for subscription; unlimited for perpetual with no revocation state) before entering a warning state.

---

## 8. What TejasCAD's licensing infrastructure DOES do

- **Hosts the platform PKI** — Platform Root signs Member LA public keys during onboarding. Publishes the LA public-key directory so end-user validators can verify chains.
- **Hosts the aggregate-attestation service** — receives quarterly signed attestations from members, verifies signatures and accumulator consistency, produces the ACIS royalty deployment count for the master contract.
- **Hosts mirrored infrastructure for members who want it** — license portal SaaS, revocation-list mirror, machine-activation service SaaS. Every one of these runs **as the member's agent under the member's LA**, meaning TejasCAD hosts the compute but cryptographically cannot read the data.
- **Provides SDKs, samples, integration guides, and reference implementations** so members can integrate quickly.
- **Runs the third-party crypto audit** and publishes the results — this is the artifact members show their own customers as proof.

## 9. What TejasCAD's licensing infrastructure DOES NOT do

- **Cannot decrypt license artifact payloads.** We don't have the keys.
- **Cannot see customer identities.** They never enter our systems.
- **Cannot see per-customer seat counts.** We see the member's aggregate quarterly attestation; that's it.
- **Cannot see pricing.** Prices are in the member's systems, never in ours.
- **Cannot see drawing data.** Drawing data doesn't touch the licensing infrastructure at all — it lives inside the member's cloud (if the member uses TejasCAD Cloud for co-edit) with per-tenant encryption, or on the end user's local machine.
- **Cannot re-issue a member's licenses without their LA key.** If the member's LA key is destroyed, TejasCAD cannot recover it. (Members are strongly advised to keep an offline backup under their own control.)
- **Cannot be legally compelled to produce plaintext of customer data.** We can be compelled to produce ciphertext we hold; the ciphertext is useless without the member's LA.

---

## 10. How a member proves the property to their end customer

The member's marketing / legal materials can include:

1. **A public statement of the architectural claim** ("our licensing infrastructure is architecturally blind to your data — this is not a policy promise, it is a cryptographic property").
2. **A pointer to this document** as the technical specification.
3. **The third-party crypto audit report** commissioned by TejasCAD and published under a permissive CC-BY license.
4. **A demonstration script** — a customer's technical team can run a tool that intercepts every network request the CAD product makes to member and TejasCAD infrastructure, and shows that no request contains any decrypted customer data.
5. **Legal boilerplate** in the master license agreement explicitly disclaiming TejasCAD's access to customer data, with contractual damages if the property is violated by architectural change.

---

## 11. Failure modes and their remediation

| Failure | Impact | Remediation |
|---|---|---|
| Member LA private key lost | Member cannot issue new licenses; existing licenses continue to validate against the LA public key | Member issues a new LA via TejasCAD (a signed request from a pre-registered recovery credential rotates their LA); 90-day migration window; existing customers migrated to newly signed licenses at renewal |
| Member LA private key compromised | Attacker can issue false licenses under the member's name | Member publishes revocation of the LA (via a break-glass workflow); Platform Root re-signs the new LA; validators reject old-LA-signed artifacts within the grace period |
| End-user machine loses TPM / machine key | User cannot decrypt their license payload | User's machine re-enrolls via member's activation service; member's LA re-wraps the symmetric key for the new machine key; old machine binding is invalidated |
| TejasCAD platform PKI Root compromised | All LA chains break | New Root; every member re-signs their LA against the new Root; documented rollover ceremony |
| TejasCAD as a company goes away | Member LA still works; member can keep issuing licenses; validators still work offline; revocation lists still verify | The whole point of the design. Member's infrastructure keeps functioning independent of TejasCAD's continuity. Documented "TejasCAD-independent operations" playbook shipped with member SDK |
| A member's business ends | Existing licenses continue to validate (they are cryptographically valid); revocation stops being updated | End users retain perpetual functionality; subscription tier enters grace-period per configured hard-offline mode |

---

## 12. Compliance mapping

| Regulation | How this design complies |
|---|---|
| **GDPR (EU)** | TejasCAD is not a controller or processor of end-customer personal data; the data does not enter our systems. Members are controllers of their own customer data; they use TejasCAD only for cryptographic and hosting services on ciphertext they own. Data Protection Impact Assessment for members made straightforward by the ciphertext-only architecture |
| **DPDPA (India)** | Data Fiduciary role sits with the member; TejasCAD is neither a Data Fiduciary nor a Data Processor for member customer data. Data localization requirements met at the member level (member chooses their region); TejasCAD platform infrastructure runs in configurable regions |
| **CCPA / CPRA (California)** | TejasCAD does not "sell" or "share" personal information — it never sees personal information |
| **SOC 2 Type II** | TejasCAD's own controls (over the ciphertext we hold, the aggregate attestation service, the platform PKI) audited annually and published |
| **ISO 27001** | Held by TejasCAD; per-member operations are the member's responsibility, framed as "customer of TejasCAD" in their own ISO scope |

---

## 13. Third-party crypto audit — the trust artifact

TejasCAD commissions an independent cryptographic audit by a firm of the community's choice (candidates: Trail of Bits, NCC Group, Kudelski Security, Cure53, IIT Bombay CSE), spending ~$150K per audit cycle. Audit deliverables:

- **Design review.** Crypto choices, key hierarchy, protocol correctness.
- **Implementation review.** Sample of the reference libraries, member SDK, activation service, license artifact parser.
- **Threat-model review.** Adequacy of the defense against each threat in §2.
- **Public report.** Published under CC-BY on `security.tejascad.com/audit-2027.pdf`, member permission to redistribute.
- **Cadence.** Annual for the first three years; biennial thereafter unless significant architectural changes.

The audit report is the single most important artifact for member-selling and for enterprise-customer trust. Budget for it goes in every year, ring-fenced.

---

## 14. What we deliberately don't do in v1

- **No zero-knowledge seat-count proofs to TejasCAD.** In v2 we may explore letting members prove their deployment count to us using a ZK protocol that reveals literally nothing beyond the number. For v1, signed attestation is trust-but-verify.
- **No hardware-token requirement.** The design supports TPM / Secure Enclave binding but does not require it — falls back to software machine fingerprinting. Members with high-security customers can require hardware.
- **No confidential-compute / TEE-based license service.** Overkill for v1; the architecture already achieves the property without TEEs.
- **No blockchain / smart-contract licensing.** Adds no useful property this design doesn't already have; adds complexity, latency, and audit surface. Not used.

---

## 15. Where each thread continues

| Thread | Full detail in |
|---|---|
| The tenant-profile layer that decides which encrypted-licensing configuration a member ships with | `docs/platform-strategy.md` §3 |
| How the platform PKI's Platform Root ownership sits inside the corporate structure | `docs/tejascad-company-structure.md` §5 (IP ownership) |
| How the encrypted-licensing story lands in the sales conversation with an IntelliCAD-dependent vendor | `docs/tejascad-vs-intellicad.md` §5 |
| The pitch-deck one-slide version of this design | `docs/tejascad-pitch-deck.md` slide 13 (illustrative index) |
