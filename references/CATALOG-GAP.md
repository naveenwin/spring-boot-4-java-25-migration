# Catalog gap preflight

Mandatory gate **after intake**, **before plan approval and any migration code**.

Role split: migrate agent inventories and classifies; enhance agent updates the pack ([AGENT.md](../AGENT.md)).

---

## Scope

**Inventory:** declared dependencies and plugin version ids in **this** service only:

- Gradle: `build.gradle*`, `gradle.properties`, `libs.versions.toml`, plugin blocks  
- Maven: `pom.xml` dependency and plugin management that pins a version  

**Do not** walk the full resolved transitive tree. Transitive skew found later still uses [LOG-TRIAGE.md](LOG-TRIAGE.md) + [dependency-diagnosis](../stubs/dependency-diagnosis.md); those findings may **append** a gap row for the next enhance pass.

**Map each declared coordinate to:**

| Mapping | Meaning |
|---------|---------|
| `catalog_approved` | Row in [DEPENDENCY-CATALOG.md](DEPENDENCY-CATALOG.md) with `status=approved` — apply target (phase 12 or linked phase); **do not re-ask** |
| `catalog_proposed` | Rare remaining `proposed` rows — human gate once |
| `phase` | Linked full phase handles procedure (still use approved target without version menu) |
| `stub` | Stub exists; insufficient for a must item |
| `internal` | Private coordinate published inside the organization |
| `deferred` | Catalog or policy says defer (e.g. WireMock 4) |
| `missing` | Not in catalog, no phase, no stub |

---

## Roles

| Actor | May | Must not |
|-------|-----|----------|
| **Migrate parent** | Write `.joker` gap artifacts; spawn catalog-map subagent; give enhance prompts; block planning | Edit pack; invent fleet catalog rows; browse Maven for 40 coords itself |
| **Catalog-map subagent** | Read build files + catalog + README phase/stub index; research max stable for allowlisted missing LOWs; return classification only | Edit application code; edit pack; load transitive trees |
| **Enhance agent** | Update catalog, promote stubs → phases, create stubs/phases, wire README | Migrate the service unless explicitly asked |
| **Human** | Open enhance chat(s); approve MED/HIGH; sign deferrals; confirm gap re-check | Expect migrate to invent versions |

---

## Artifacts (`.joker`, never commit)

```text
.joker/java-spring-migration/
  catalog-map.yaml           # full declared inventory + mapping
  catalog-gaps.yaml          # open / resolved gaps only
  catalog-gaps.md            # short human table
  catalog-approvals.yaml     # migration-local auto / signed approvals
  enhance-prompts.md         # copy-paste prompts for pack chat(s)
```

### `catalog-map.yaml` (shape)

```yaml
generatedAt: "2026-10-20T21:00:00Z"
scope: declared-only
target:
  boot: "4.1.x"
  java: 25
  kotlin: "2.3.x"   # when *.kt present on Boot 4.1 + JDK 25; else null
entries:
  - coordinate: org.apache.commons:commons-lang3
    currentPin: "3.14.0"
    locations: ["gradle/libs.versions.toml:commonsLang3"]
    mapping: catalog_proposed
    risk: low
    action: auto_approve_migration_local
    suggestedTarget: "3.18.0"
  - coordinate: io.github.resilience4j:resilience4j-spring-boot3
    currentPin: "2.2.0"
    mapping: phase
    linkedPhase: phases/40-resilience4j-boot4.md
    risk: medium
    action: schedule_phase
    blocksPlan: false
  - coordinate: org.springframework.retry:spring-retry
    currentPin: "2.0.11"
    mapping: phase
    linkedPhase: phases/41-spring-retry-framework.md
    risk: medium
    action: schedule_phase
    blocksPlan: false
  - coordinate: org.springframework.kafka:spring-kafka
    currentPin: "3.2.0"
    mapping: phase
    linkedPhase: phases/44-spring-kafka-4.md
    risk: medium
    action: schedule_phase
    blocksPlan: false
```

### `catalog-gaps.yaml` (shape)

```yaml
status: open | waiting-enhance | ready
blocksPlan: true
gaps:
  - id: GAP-001
    coordinate: org.springframework.boot:spring-boot-starter-data-mongodb
    kind: stub_only_required
    linkedStub: stubs/mongodb.md
    blocksTier: must
    status: open
    enhanceAction: promote_stub_to_phase
  - id: GAP-002
    coordinate: com.example:legacy-client
    kind: missing_needs_procedure
    blocksTier: must
    status: open
    enhanceAction: create_stub_or_phase
```

### `catalog-approvals.yaml` (shape)

```yaml
# Migration-local only — not a second fleet catalog.
# Enhance may later merge stable rows into DEPENDENCY-CATALOG.md.
approvals:
  - coordinate: org.apache.commons:commons-lang3
    target: "3.18.0"
    source: auto_allowlist
    risk: low
    phase12Only: true
    signedBy: migrate-catalog-map
  - coordinate: com.example:foo
    target: "2.1.0"
    source: human
    signedBy: "<human>"
```

---

## Actions

### Fleet catalog `approved` (default path)

If the declared pin maps to `status=approved`, schedule the linked phase (or phase 12) and apply the catalog target. **Do not** present optional bump menus. Phase docs may still `ASK_HUMAN` for behavior (wire contracts, Security, allocator, etc.) — that is not a version cafeteria.

### Auto-approve (migration-local) — missing from fleet catalog only

Record in `catalog-approvals.yaml` for **this migration** when the pin is **not** in the fleet catalog. Do **not** edit [DEPENDENCY-CATALOG.md](DEPENDENCY-CATALOG.md) from migrate.

All of these must hold:

1. Declared pin or plugin id (not transitive)  
2. Not `internal`  
3. Not on deferred / bad / anti-pattern lists  
4. No Detect signal that maps to a stub or a phase that needs code/config migration  
5. Classified **phase-12-only** (version bump, no Before→After procedure)  
6. Risk **low**  
7. Suggested target is **stable** (no alpha/beta/RC), compatible with Boot 4 + Java 25, and Kotlin **2.3.x** (Boot **4.1** managed **2.3.21**) when the service has `*.kt`  

A fleet `status=migrate` row whose linked phase file exists is `mapping: phase`, `action: schedule_phase`, `blocksPlan: false`. Schedule that phase. Do not send it back to enhance. Resilience4j is phase 40 and Spring Retry is phase 41. Remaining fleet `catalog_proposed` rows, a `migrate` row with no phase file, internals, deferred items, and stub-only stacks go to the human / enhance gate (not a long optional list — only blockers).

### Promote stub (blocks plan)

When intake **Detects** a stub as applicable **and** that stack is **must-relevant** for this service:

1. Gap `stub_only_required`  
2. Write enhance prompt(s) in `enhance-prompts.md`  
3. Ask human to open a **new chat** on the **pack** workspace  
4. Status `waiting-catalog-gaps`  
5. **Do not** write the plan into `status.yaml` for approval until re-check is clean  

Irrelevant stubs (e.g. Mongo stub when Detect=no) do not block.

### Missing procedure (blocks plan when must-relevant)

No catalog, no phase, no stub, and not allowlisted phase-12-only → gap `missing_needs_procedure`. Enhance creates a stub or jumps to a full phase. Prefer a **phase** when a must item needs executable steps.

### Internal

Gap `internal_needs_owner_version`. Record the owner and the version they publish. Do not invent a Maven Central version, and do not open other repositories to find it.

### Deferred

Visible in gap report. Opt-in or document “stay on current line.” Does not block plan unless human marks it must-blocking.

---

## Orchestration

1. Intake finishes → `01-intake.md`  
2. Spawn **catalog-map** subagent (capsule below)  
3. Parent writes `catalog-map.yaml`, `catalog-gaps.yaml`, `catalog-gaps.md`, `catalog-approvals.yaml`, `enhance-prompts.md`  
4. If any gap has `blocksPlan: true`:  
   - Set `overallStatus: waiting-catalog-gaps`  
   - Stop. Give human the enhance prompt(s). Prefer **new chat** on pack root.  
   - Optional: write `handoffs/<timestamp>.md` with reason `waiting-catalog-gaps`  
5. Human / enhance promotes required stubs → phases, adds catalog rows, wires README  
6. Migrate resumes (same or new chat): **re-run catalog-map**  
7. When no `blocksPlan: true` gaps remain → stamp those prompts in `enhance-prompts.md` `do-not-rerun`, refresh the `catalog-gaps.md` header so it no longer says the plan is waiting, then proceed to **plan** (`status.yaml` items). Do not record CI or runtime images in `catalog-approvals.yaml`.
8. Preview planning notes are OK while waiting; **plan approval and Stage A edits are not**

### Catalog-map subagent capsule

```text
Service root: <this workspace>
Pack: DEPENDENCY-CATALOG.md, README phase table, stubs/, anti-patterns, this doc
Intake: 01-intake.md Detect flags
Target: Boot / Java / Kotlin from 00-target-contract.md
Scope: declared pins and plugins only — no full transitive tree
Output: catalog-map classifications only under .joker/
Constraint: no application edits; no pack edits; no compile/test
```

Parent reads the YAML summaries only — not Maven research noise.

---

## Enhance prompts

Put a **batch** prompt in `enhance-prompts.md` listing every open `blocksPlan` gap. Optionally add one prompt per GAP id when the human wants parallel enhance chats (max 2 writers on the pack).

Batch example:

```text
Using <path-to-pack>/AGENT.md, resolve catalog gaps for a Boot 4 migration preflight.

Read the gap list the human pastes (from the service's
.joker/java-spring-migration/catalog-gaps.yaml), or the summary below:
- GAP-001 (example): `stubs/mongodb.md` is still a stub → promote it to a phase. Kafka is already [44-spring-kafka-4.md](../phases/44-spring-kafka-4.md); schedule that phase, do not promote it again
- GAP-002: add catalog row + phase or stub for com.example:legacy-client

For each gap:
1. Research Boot 4 / Java 25 (Kotlin **2.3.x** on Boot **4.1** if noted) compatible max stable — no alpha/beta/RC.
2. Update DEPENDENCY-CATALOG.md (proposed → human can approve).
3. Promote stub to phase or add phase/stub per AGENT.md template; wire README planner Order.
4. Summarize Detect signals and breaking changes for migrate agents.

Do not migrate any application service in this chat unless I ask separately.
```

After enhance finishes, human returns to migrate:

```text
Resume the Boot 4 migration using <path-to-pack>/SKILL.md.
Re-run the catalog-gap preflight from .joker/java-spring-migration/catalog-gaps.yaml.
Proceed to plan only if no blocksPlan gaps remain.
```

---

## Phase 12 interaction

[12-dependency-bump-queue.md](../phases/12-dependency-bump-queue.md) may use, in order:

1. Catalog `approvedTarget`  
2. Matching row in `catalog-approvals.yaml` for this migration  
3. Otherwise skip / ask — never invent  

At closeout, note migration-local approvals in `findings.md` so enhance can merge useful rows into the fleet catalog later.

---

## Feedback from verification

When log triage yields `candidatePhases: []` for a dependency/resolution failure, append a gap to `catalog-gaps.yaml` (`kind: triage_unmapped`) with `blocksPlan: false` unless it blocks the current stage. A `Could not find` in a Stage A resolve run that the extractor cannot attribute is the same gap. Do not invent a version in the fix wave; route to enhance or human.

---

## Exit criteria (plan may begin)

- Every **must-relevant** Detected stub is promoted to a full phase (or human signed defer with reason — rare).  
- Every `blocksPlan` gap is `resolved` or explicitly deferred with sign-off.  
- Migration-local autos are recorded in `catalog-approvals.yaml`.  
- Catalog-map re-run is clean for blocking gaps.  
- Then — and only then — write the plan into `status.yaml` for human approval.
