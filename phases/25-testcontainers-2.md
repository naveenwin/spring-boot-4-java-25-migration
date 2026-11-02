# 25 — Testcontainers 1.x → 2.x

## Detect

Apply when:

- `org.testcontainers:testcontainers-bom:1.x` or module pins `1.19–1.21.x`
- Artifact IDs **without** `testcontainers-` prefix (`postgresql`, `junit-jupiter`, `mysql`, …)
- Imports `org.testcontainers.containers.PostgreSQLContainer` (1.x package)
- JUnit 4 `@Rule` / `ClassRule` Testcontainers usage — [36-junit-jupiter.md](36-junit-jupiter.md) removes those before this phase. Start here from Jupiter `@Container`. If a `@Rule` container remains, finish 36 first.

Skip when already on `testcontainers-*` modules + BOM **2.0.5**.

Catalog target: [DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md) (`testcontainers-bom` **2.0.5**). On Boot **4.1.1**, apply that BOM explicitly. Do not substitute an older Boot-managed 2.0.2 line for the approved **2.0.5** pin.

**Declared-only (`sourceUsage=none`):** coordinates are on the build, and this grep is empty:

```bash
rg -n 'org\.testcontainers|PostgreSQLContainer|@Container' src/test
```

That branch is dependency-only: rename modules and set BOM **2.0.5**. No Docker spike, no OpenRewrite, no source edits, and no blockers. Handoff `sourceUsage=none`.

**Used:** the grep has hits. Follow the import and constructor migration below. Spike one IT only on that branch, before a mass rename.

## Before → After

### Gradle

```gradle
// BEFORE (1.x)
testImplementation platform('org.testcontainers:testcontainers-bom:1.20.4')
testImplementation 'org.testcontainers:junit-jupiter'
testImplementation 'org.testcontainers:postgresql'

// AFTER (2.x)
// Boot 4.1.1 — catalog BOM 2.0.5, not an older Boot-managed line
testImplementation platform('org.testcontainers:testcontainers-bom:2.0.5')
testImplementation 'org.testcontainers:testcontainers-junit-jupiter'
testImplementation 'org.testcontainers:testcontainers-postgresql'
```

### Java

```java
// BEFORE
import org.testcontainers.containers.PostgreSQLContainer;
@Container
static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

// AFTER
import org.testcontainers.postgresql.PostgreSQLContainer;
import org.testcontainers.utility.DockerImageName;
@Container
static PostgreSQLContainer postgres =
    new PostgreSQLContainer(DockerImageName.parse("postgres:16-alpine"));
```

| 1.x artifact | 2.x artifact |
|--------------|--------------|
| `postgresql` | `testcontainers-postgresql` |
| `junit-jupiter` | `testcontainers-junit-jupiter` |
| `mysql` / `kafka` / … | `testcontainers-<module>` |

| 1.x type | 2.x type |
|----------|----------|
| `org.testcontainers.containers.PostgreSQLContainer` | `org.testcontainers.postgresql.PostgreSQLContainer` |
| `getContainerIpAddress()` | `getHost()` |
| `DockerComposeContainer` | Prefer `ComposeContainer` |

## What breaks / how to fix

| Symptom | Cause | Fix |
|---------|--------|-----|
| `Could not find org.testcontainers:postgresql:2.0.x` | Version bump without rename | Use `testcontainers-postgresql` |
| Package `containers.PostgreSQLContainer` missing | Package move | New import; drop `<?>` |
| No no-arg constructor | Defaults removed | Pass explicit image / `DockerImageName` |
| JUnit 4 rule errors | JUnit 4 support removed | [36-junit-jupiter.md](36-junit-jupiter.md): `@Testcontainers` + `@Container` (1.x types). This phase does not reintroduce rules. |
| Mixed 1.x + 2.x on classpath | Partial migrate | One BOM; check transitive libs |
| CI can’t start containers | Docker/Ryuk/Podman | Ensure Docker; Podman often needs `TESTCONTAINERS_RYUK_DISABLED=true` |
| Image tag drift | Implicit defaults gone | Pin `postgres:MAJOR-alpine` (team standard) |

Optional automation: OpenRewrite `org.openrewrite.java.testing.testcontainers.Testcontainers2Migration`.

## Steps

1. Run `rg -n 'org\.testcontainers|PostgreSQLContainer|@Container' src/test`. Empty → **declared-only** / `sourceUsage=none`: do steps 2 and 7 only. Non-empty → **used**: continue through source edits, and spike one IT before renaming the rest.  
2. Inventory BOM vs per-module pins; list all `org.testcontainers` artifacts. On Boot **4.1.1**, set BOM **2.0.5** and rename modules to `testcontainers-*`.  
3. Used branch only: fix imports / constructors / `getHost()`. JUnit 4 `@Rule` containers belong to [36-junit-jupiter.md](36-junit-jupiter.md); if any remain, finish 36 before continuing.  
4. Used branch only: align Kafka/LocalStack/Compose separately if present (extra API renames).  
5. Used branch only: compile errors are Stage B work; ITs run in Stage C (the human runs them when Docker is not available to the orchestrator). Declared-only does not ask for a container spike.  
6. Skip OpenRewrite unless the used branch needs the import rewrite.  
7. One commit for this phase. Do not fold the BOM rename into another phase’s commit (phase **09** often shares `build.gradle.kts`). If they already landed together, record `sharedCommitWith=<phase-ids>` in both phase notes and this handoff.

## Do not

- Bump version only without renaming module artifacts.  
- Reintroduce JUnit 4 rules “temporarily.”  
- Rely on no-arg / default image constructors.  
- Stack an explicit 1.x BOM on Boot 4.  
- Treat Boot **4.1.1**’s managed Testcontainers line as a substitute for catalog BOM **2.0.5**.  
- Spike a PostgreSQL IT, or run OpenRewrite, when `sourceUsage=none`.  
- Hide this phase inside another phase’s commit without `sharedCommitWith`.  
- Treat this as a silent phase-12 version bump — use this phase.

## Risk

| Branch | Risk |
|--------|------|
| Declared-only (`sourceUsage=none`): BOM **2.0.5** + module rename, no test sources | `SAFE_AUTO` — no spike |
| Used, many IT modules or Kafka/LocalStack/Compose | `SPIKE_FIRST` |
| Used, first module otherwise | `ASK_HUMAN` after that module is green |

## Rollback

Revert BOM/artifact IDs/imports in one commit. Boot 4 does not manage TC 1.x — rollback stays on the previous 1.x pin set, not “Boot default 1.x.”

## Done when

All Testcontainers modules use 2.x artifact IDs on BOM **2.0.5** (Boot **4.1.1** included). Declared-only ends when the build coordinates are renamed and `sourceUsage=none` is recorded — no Docker smoke. Used path: imports compile, and the human reports Docker IT smoke green or deferred.

## Handoff

`testcontainers=2.x; bom=2.0.5; boot=4.1.1; modules=[…]; sourceUsage=none|used; dockerITs=n/a|green|deferred; sharedCommitWith=<phase-ids>|none`
