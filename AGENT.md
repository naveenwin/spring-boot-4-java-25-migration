# Agent instructions — maintain & extend this workflow pack

You are operating on the **`Java-boot4-migration/`** folder: a **generic, on-demand skill pack** for migrating Java/Kotlin Spring services to **Spring Boot 4 + Java 25**.

This file is **not** a migration phase. It tells you how to **improve the pack** when a human asks you to add, deepen, or fix workflow content.

---

## What this folder is for

| Role | Entry | Job |
|------|--------|-----|
| **Migrate a service** | **[SKILL.md](SKILL.md)** | Orchestrate intake → catalog-gap → plan → Stage 0 baseline → Stage A dependency wave → Stage B source phases → Stage C runtime vs baseline |
| **Phase catalog** | [PHASE-CATALOG.md](references/PHASE-CATALOG.md) | Planner order + stubs index (not the orchestrator) |
| **Extend the pack** | **This file (`AGENT.md`)** | Research a topic; add/update phase docs, stubs, the catalog, anti-patterns |

Humans pull this pack **on demand** by pointing a chat at **this folder’s root** (any checkout path) — it is **not** a global always-on Cursor skill. Patterns must stay **generic** (before → after on “the service under migration”). Never embed absolute host paths or one-off service names. Migration working files go under `.joker/java-spring-migration/` (never committed) — see SKILL.md.

---

## When the human asks you to enhance the workflow

Examples of enhancement requests (not exhaustive):

- “Add Firestore / NoSQL changes needed for Boot 4”
- “Deep-dive WebFlux codec migration and fill the stub”
- “Document R2DBC / Mongo / Cassandra / Elasticsearch for Boot 4”
- “Add a phase for Spring Security 7 breaking changes”
- “Expand the Maven stub into a real phase”

### Your job

1. **Understand the ask** as *workflow content*, not *migrate service X right now* (unless they also ask to migrate).  
2. **Research** using public Spring Boot 4 / Framework 7 / relevant driver docs + optional scan of the **current workspace only** if it helps illustrate patterns.  
3. **Produce or update markdown in this folder** following the conventions below.  
4. **Wire the new doc into** [PHASE-CATALOG.md](references/PHASE-CATALOG.md) (and [99-anti-patterns.md](references/99-anti-patterns.md) if needed). If orchestration behavior changes, update [SKILL.md](SKILL.md). Do not link agent docs to `MANUAL.md`.  
5. **Stop** when the pack is updated — do not start migrating an app unless explicitly asked.

### Not your job (unless explicitly requested)

- Migrating a live service end-to-end  
- Opening sibling repos for “how we did it”  
- Committing this folder if the human said it stays local / untracked  
- Overloading the session with unrelated dependency upgrades  

---

## Document types you may create

| Type | Naming | Use when |
|------|--------|----------|
| **Phase** | `NN-short-name.md` (two-digit stable id) | Actionable migration step placed by PHASE-CATALOG planner Order |
| **Stub** | `stubs/<topic>.md` | Topic known but not fully researched yet |
| **Catalog** | `DEPENDENCY-CATALOG.md` | Version trains and pin targets |
| **Evidence ledger** | `references/MIGRATION-EVIDENCE.md` | Generic symptom → cause → verified fix, version-bounded and linked to a phase |
| **Context control** | `references/CONTEXT-CONTROL.md` | Capsules, evidence labels, verifier, and chat-reset / new-chat handoffs |
| **Log triage** | `references/LOG-TRIAGE.md` | Stage C failure clustering and routing |
| **Build gates** | `references/COMPILE-GATES.md` | Pinned commands, run procedure, stage gates, bounded lookup |
| **Error ownership** | `references/ownership.json` | Ordered rules mapping a compile error to the phase that owns it |
| **Scripts** | `scripts/extract_run.py`, `scripts/migration.init.gradle` | Run extractor (summary, errors, tests, baseline delta) and the Gradle init script (resolve task, javac error cap) |
| **Catalog gap** | `references/CATALOG-GAP.md` | Protocol migrate follows; enhance resolves gaps from `enhance-prompts.md` |
| **Dep removal** | `references/DEP-REMOVAL.md` + `phases/NN-remove-*.md` | Drop-prefer catalog rows: analysis + risk score before delete/replace |
| **Anti-pattern** | update `99-anti-patterns.md` | “Never do this”. Put it under Cross-cutting only when it applies to every phase; otherwise under Phase-specific with the phase id, and in that phase's Do not. Never renumber |
| **Fill stub → phase** | promote `stubs/foo.md` → `NN-foo.md` | Stub is now complete enough to execute |

Pick the **next free `NN`** for the filename (stable id — **never renumber** existing phases when priorities change). Place the new row in the **PHASE-CATALOG planner Order** column where it belongs in the migration sequence. If unsure where it sits in that table, ask the human.

---

## Required phase doc template

Every new **phase** (and any stub you promote) must include these sections:

```markdown
# NN — <Title>

## Detect
When to apply / when to skip (concrete signals: deps, imports, config keys).

## Before → After
Generic code/config snippets. No service names. Show shape of current code → migrated code.

## Steps
Numbered, minimal, executable by a subagent.

## Do not
Hard constraints.

## Risk
One of: `SAFE_AUTO` | `ASK_HUMAN` | `SPIKE_FIRST`
Explain what needs human approval if not SAFE_AUTO.

## Rollback
How to undo this phase alone.

## Done when
Light exit criteria. Prefer "the latest compile shows no errors owned by this phase" and config validity; runtime outcomes belong to Stage C.

## Handoff
One short machine-readable line for the parent orchestrator.
```

Mark which steps are Stage A (build files only) and which are Stage B (source), when the phase has both. Do not put a confidence score in a phase doc; anything an implementer must not guess becomes a Detect signal that the planner turns into a blocker ([CONTEXT-CONTROL.md](references/CONTEXT-CONTROL.md#readiness)). Do not write "ask the human to compile": the orchestrator runs builds ([COMPILE-GATES.md](references/COMPILE-GATES.md)).

When a phase introduces new error signatures (packages, generated paths, message text), add or extend its rule in [references/ownership.json](references/ownership.json). Rules are first-match: put specific rules above broad ones, and keep test-side phases above main-side phases that share a package. Rerun `python3 scripts/extract_run.py --help` after editing scripts.

Commit subjects in a migration are `<phase-id> <A|B|fix>: <summary>`. The extractor git-blames build-file errors to that prefix, so a new phase id must match `NN-lowercase-words`.

Leave evidence claims out of the phase doc. The migrate agent writes them in `.joker/.../phase-notes/<id>.md` using [CONTEXT-CONTROL.md](references/CONTEXT-CONTROL.md). Do not add a per-phase human checkpoint for that labelling.

Stubs may use a shorter skeleton plus an **“Open questions for a future fill-in pass”** list (see existing `stubs/`).

---

## Quality bar for new content

1. **Generic** — never name a real service. Prefer “if the service has X…”.  
2. **Cohesive** — one concern per file (Firestore ≠ “all NoSQL”). Split Mongo / Firestore / Cassandra if steps diverge.  
3. **Detect-first** — orchestrators must be able to skip N/A phases.  
4. **Boot 3→4 primary** — call out Boot 2.7-only extras (Jakarta, Sleuth) only when the service is still on Boot 2.7.  
5. **Risk tags** — high-risk / irreversible / data-shape changes default to `ASK_HUMAN` or `SPIKE_FIRST`.  
6. **Light verification** — do not invent heavy per-phase test plans; point at [13-verification.md](phases/13-verification.md).  
7. **JDK 25 note** — builds use a per-command `JAVA_HOME` (do not mandate global SDK change).  
8. **Maven / WebFlux** — if the topic differs by build tool or web stack, add a short subsection or stub link rather than ignoring them.  
9. **Update the index** — PHASE-CATALOG phase table + any anti-patterns; keep orchestrator prompt accurate.
10. **Direct Jackson 3** — never document Boot 4 + `spring-boot-jackson2` as an intermediate path; Jackson 2 may appear only in historical Before snippets and pre-cutover contract evidence.
11. **No per-phase human gates** — do not add a “ask the human” step that the verifier or evidence handoff would repeat. Human stops stay the plan approval, open blockers that need a human, and a real decision.
12. **Human-facing names** — phase docs keep `# NN — <Title>` and filename ids. Chat and plan text use the title first ([SKILL.md Speak to humans](SKILL.md#speak-to-humans)). Do not rename Stage A/B/C or phase files to make the wording nicer.
13. **Breaking changes live in the phase** — when promoting a stub, write the starter renames, property keys, and removed APIs from the official guide into that phase. Do not add a second reference dump beside it. Bump **Last reviewed** on [DEPENDENCY-CATALOG.md](references/DEPENDENCY-CATALOG.md) in the same edit that changes a pin.

---

## Suggested workflow when asked to “deep analyze & add &lt;topic&gt;”

```
1. Restate the topic and proposed filename(s) + PHASE-CATALOG order slot → get human OK if ambiguous.
2. Research Boot 4 / related module migration notes (official docs first).
3. Optionally scan current workspace for Detect signals only (deps/imports) — do not turn that into a service-specific narrative.
4. Write the phase/stub using the template.
5. Patch PHASE-CATALOG.md (and 99-anti-patterns.md if needed).
6. Summarize for the human: what was added, risk level, when a migrate-orchestrator should run it.
```

---

## Refreshing the dependency catalog (fleet pins)

Shared pin table: [references/DEPENDENCY-CATALOG.md](references/DEPENDENCY-CATALOG.md).  
Migrate agents **read** it; they must **not** open other repositories to invent versions ([SKILL.md](SKILL.md) one-repo rule).

When a human asks to refresh or rebuild the catalog:

```
1. Scan the team’s service checkouts (paths the human provides) — Gradle files only
   (build.gradle*, gradle.properties, libs.versions.toml, plugin version pins).
   Union explicit group:artifact (+ plugin ids) with versions seen when refreshing from checkouts the human provides.
   Do not hard-code machine-local absolute paths into the catalog.
2. Classify: platform (phase 01) / third-party pin / migrate coordinate / private `internal` artifact / deferred by policy.
3. Research max stable per coordinate (Maven Central / Plugin Portal; exclude alpha/beta/RC).
   Apply phase-doc caps (WireMock 4 deferred, Hypersistence line via 03, Cucumber 8 via 16, etc.).
   Do not treat any single migrated service as the gold standard.
4. Write/update DEPENDENCY-CATALOG.md with status=proposed (or update maxStableFound notes).
   Set **Last reviewed** to the day of the edit.
5. Stop for human approval — flip accepted rows to approved (or set approvedTarget).
6. Point phase 12 / PHASE-CATALOG at the catalog if links changed.
```

**Enhance-agent** may scan multiple service checkouts for this maintenance task (paths from the human).  
**Migrate-agent** must not — it uses the frozen catalog, migration-local `catalog-approvals.yaml`, and phase 12 only ([CATALOG-GAP.md](references/CATALOG-GAP.md)). Hand each migrate chat only this repository's approved targets. An upstream version the human already named is a gate. The one-repo rule stays.

## Resolving migration catalog gaps (from a migrate preflight)

When a human pastes gaps from a service’s `.joker/java-spring-migration/catalog-gaps.yaml` / `enhance-prompts.md` (or the batch prompt migrate generated):

```
1. Work in the pack workspace — do not migrate the application service.
2. For each blocksPlan gap:
   - stub_only_required → promote stub to a full phase (template below); wire PHASE-CATALOG Order.
   - missing_needs_procedure → add catalog row (proposed) + stub or full phase; prefer phase if a must item needs steps.
   - internal_needs_owner_version → document owner/version expectations; do not invent Maven coords.
3. Research Boot 4 / Java 25 (+ Kotlin **2.3.x** on Boot **4.1** when noted) max stable — no alpha/beta/RC.
4. Update DEPENDENCY-CATALOG.md; leave status=proposed unless the human approves in this chat.
5. Summarize Detect signals and breaking changes for the migrate agent.
6. Stop. Human returns to the migrate chat and re-runs the catalog-gap preflight.
```

Also merge useful **migration-local** approvals from a finished migration’s `findings.md` / `catalog-approvals.yaml` into the fleet catalog when the human asks.

## Recording a learning

There is no inbox file. When a lesson should outlive one service, an enhance chat writes it straight into the phase, [MIGRATION-EVIDENCE.md](references/MIGRATION-EVIDENCE.md), `ownership.json`, an anti-pattern, or the catalog. Do not copy service names, commit SHAs, resume prompts, or unverified checklists into those files.

## Maintaining the evidence ledger

Add to [references/MIGRATION-EVIDENCE.md](references/MIGRATION-EVIDENCE.md) only when a finding is generic, version-bounded, and supported by docs/resolution/execution/deployment evidence. Reconcile contradictory findings before recording them. Do not include service names, internal coordinates, tickets, or environment secrets. Keep executable instructions in phase docs and dependency targets in the catalog.

### Example human prompts you should understand

```text
Using Java-boot4-migration/AGENT.md, resolve catalog gaps from this paste
(catalog-gaps.yaml / enhance-prompts.md). Promote required stubs to phases,
update DEPENDENCY-CATALOG.md. Do not migrate any application service.
```

```text
Using Java-boot4-migration/AGENT.md, research Spring Boot 4 changes for Firestore
and add a phase doc. Wire it into PHASE-CATALOG. Do not migrate any service yet.
```

```text
Deepen phases/35-webflux.md with RSocket guidance using AGENT.md conventions.
```

```text
Add NoSQL coverage: split Mongo and Firestore if needed; ASK_HUMAN on data
compatibility steps.
```

---

## Relationship to migrate-orchestrator agents

- **Migrate agent** reads `SKILL.md` + `PHASE-CATALOG.md` → runs phases → must not edit pack structure unless asked. Never read `MANUAL.md`.  
- **Enhance agent** (you, when given this file) edits the pack → must not migrate apps unless asked.  
- If a human asks for both (“add Firestore doc then migrate this repo”), do **pack update first**, then follow `SKILL.md` for migration.

---

## Do not

- Duplicate an existing phase under a new name — extend or link instead.  
- Embed secrets, internal hostnames, or one-off ticket IDs in phase docs.  
- Mark `SAFE_AUTO` for data migrations, index changes, or lock/replace decisions.  
- Leave README pointing at missing files.

---

## Done when (enhancement task)

- [ ] New/updated markdown exists under `Java-boot4-migration/`  
- [ ] Template sections present (for phases)  
- [ ] PHASE-CATALOG Order row (with Stage B side) and, when new error signatures exist, an `ownership.json` rule  
- [ ] Risk tags set  
- [ ] Human got a short summary of when to use the new doc  
