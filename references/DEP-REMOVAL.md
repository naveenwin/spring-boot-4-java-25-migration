# Dependency removal — analysis & risk score

Shared protocol for **remove-and-replace** phases (e.g. [38-remove-vavr](../phases/38-remove-vavr.md), [39-remove-or-migrate-shadow](../phases/39-remove-or-migrate-shadow.md)).

Catalog rows with `proposedTarget` of `drop`, `drop (prefer)`, or notes that prefer removal **must not** be silent phase-12 bumps. Run the linked removal phase first.

---

## When to use

| Signal | Action |
|--------|--------|
| Catalog `status=migrate` + drop/prefer-remove | Schedule the dedicated removal phase |
| Detect finds the library/plugin in this service | Same |
| Human asks to delete a non-stdlib FP / legacy build tool | Same |

Coordinate **renames** (boot3→boot4, microutils→oshai, johnrengelman→gradleup when Shadow stays) are **migrate** phases, not this protocol — unless the phase explicitly offers a drop path (Shadow).

---

## Deep analysis (required before any delete)

Write under `.joker/java-spring-migration/phase-notes/<phase-id>.md` (never commit):

1. **Inventory** — dependency/plugin declaration sites; import / FQCN / Gradle id hits; test vs main split.  
2. **Surface map** — which APIs are used (e.g. `Option` vs `Either` vs collections; Shadow relocate/minimize vs plain fat JAR).  
3. **Boundary leak** — does the type appear on public REST/DTO/SPI signatures, or only inside private helpers?  
4. **Jackson / serialization** — companion modules (`vavr-jackson`, custom serializers).  
5. **Replace sketch** — JDK / Kotlin stdlib / Boot-native alternative per hot cluster (not a full rewrite yet).  
6. **Risk score** — compute below; record each factor.

Do not delete the dependency until the score and gate below are recorded.

---

## Risk score (0–100)

Sum weighted factors. Cap at 100. Higher = harder / riskier to remove in this migration.

| Factor | Weight | How to score (0–weight) |
|--------|-------:|-------------------------|
| **Call-site breadth** | 25 | 0: ≤3 files; 10: 4–15; 20: 16–40; 25: >40 or generated sources |
| **API surface depth** | 25 | 0: one shallow wrapper type; 12: few types, local only; 20: collections + Try/Either; 25: pervasive FP style / custom Vavr APIs |
| **Public contract leak** | 20 | 0: none; 10: internal module API; 20: REST/DTO/SPI/client library exports the type |
| **Serialization / modules** | 15 | 0: none; 8: test-only JSON; 15: prod Jackson module or wire shape depends on it |
| **Build / runtime coupling** | 15 | 0: unused; 8: build-only easy substitute; 15: packaging/CI/runtime depends on behavior (relocate, minimize, custom Shadow tasks) |

**Bands**

| Score | Band | Gate |
|------:|------|------|
| 0–29 | **LOW** | `SAFE_AUTO` — remove + replace in this phase |
| 30–59 | **MED** | `ASK_HUMAN` — present inventory + rewrite plan; remove only after OK (or interim catalog bump if human defers) |
| 60–100 | **HIGH** | `SPIKE_FIRST` — do not mass-replace; park removal, optional interim bump only, schedule follow-up epic |

---

## Replace rules

- Prefer **JDK** (`Optional`, `Stream`, `List`/`Map`, sealed types / records) and **Kotlin stdlib** (`Result`, nullable types, collections) over another third-party FP library.  
- One concern per commit: analysis note → removals/replacements → drop dependency.  
- Confidence ≥ 90% for mechanical replacements; stop and ask when public contracts or wire JSON would change.  
- Do not introduce a new FP framework to “replace” the old one.

---

## Handoff fields (common)

Removal phases should include in their handoff line:

`removalRisk=<0-100>; band=LOW|MED|HIGH; action=removed|deferred-bump|parked; replacedWith=<jdk|kotlin|bootJar|gradleup|n/a>`
