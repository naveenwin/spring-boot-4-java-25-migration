# 12 — Risk-ordered dependency bumps

## Detect

Bump **explicitly pinned** libraries that lag the shared catalog, as part of the Stage A dependency wave with every other phase's coordinates. Source fallout from a bump is owned by the linked phase or, for a plain bump, by this phase in Stage B.

**Version source of truth (in order):**

1. [DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md) `approvedTarget`  
2. This migration’s `.joker/java-spring-migration/catalog-approvals.yaml` ([CATALOG-GAP.md](../references/CATALOG-GAP.md))  
3. Otherwise skip / ask — do not invent  

- Load the catalog and `catalog-approvals.yaml` once for this migration (preflight must already be `ready`).  
- Diff *this* service’s explicit pins (Gradle / version catalog / properties) against those targets.  
- Skip coordinates not present in this service.  
- Skip `internal`, `platform` (use [01-platform-baseline.md](01-platform-baseline.md) and any linked executable phase such as [34-spring-cloud-gcp.md](34-spring-cloud-gcp.md)), and `deferred` unless the human opts in.  
- For `migrate` rows, follow the linked phase (do not treat as a silent version bump).

## Order (lowest risk first)

This phase's bumps land as **one** Stage A commit (`12-dependency-bump-queue A: …`) whose body lists each coordinate and version. The table is the review order and the order to back out a coordinate if resolution fails. Coordinates owned by a dedicated phase land in that phase's commit, not here.

| Priority | Examples | Notes |
|---------|----------|--------|
| 1 LOW | WireMock **3.x** patch + align CI/docker | Prefer `org.wiremock:wiremock-standalone` when CI/docker copy the standalone JAR (switch from `org.wiremock:wiremock` if needed). Same version everywhere; see [16-cucumber-8.md](16-cucumber-8.md). **Defer 4.x beta** — catalog caps at 3.13.x |
| 2 LOW | commons-lang3 / text / collections4 | Catalog targets; stay on same major unless catalog says otherwise |
| 3 LOW | datafaker 2.x | Only if already on `net.datafaker:datafaker`. If still on `javafaker`, do [09-testing.md](09-testing.md) first |
| 4 LOW–MED | Cucumber **7.x** latest *or* **8.0.x** modernization | 8.x needs idioms — see [16-cucumber-8.md](16-cucumber-8.md); catalog lists 8.0.x as max bump |
| 4b LOW–MED | MapStruct 1.5 → 1.6 (API + processor + SPI) | Dedicated phase [17-mapstruct.md](17-mapstruct.md); target from catalog |
| 5 LOW–MED | Hypersistence hibernate-73 latest | Queue is **patch/minor on `*-hibernate-73` only**. Artifact line `55`/`63` → `73` belongs in [03-hibernate-7.md](03-hibernate-7.md) |
| 6 MED | swagger-core 2.2.x | Bump `swagger-annotations` + `swagger-models` + `swagger-core` **same version, one commit** (catalog version). springdoc **2→3** / Knife4j Boot4 → [32-springdoc-openapi.md](32-springdoc-openapi.md), not this queue |
| 7 MED | protobuf Gradle plugin | Not protoc major — see [15-protobuf-protoc.md](15-protobuf-protoc.md) |
| 8 MED | jsonschema2pojo 1.2 → 1.3 | Dedicated phase [14-jsonschema2pojo.md](14-jsonschema2pojo.md) |
| 9 HIGH | protoc 4.x | Dedicated phase [15-protobuf-protoc.md](15-protobuf-protoc.md) — `SPIKE_FIRST` |
| 10 HIGH | distributed-lock | Prefer Boot 4 major of the **same** lib — see [11-distributed-lock.md](11-distributed-lock.md) |
| 11 HIGH | Cucumber 8 + WireMock 3 align | Dedicated phase [16-cucumber-8.md](16-cucumber-8.md); **WireMock 4 deferred** while beta |
| 12 HIGH | Other catalog `risk=HIGH` / major MED | Prefer dedicated phases: [24](24-tomcat-boot-managed.md) Tomcat, [25](25-testcontainers-2.md) TC, [26](26-rest-assured-6.md) RestAssured, [27](27-mockserver-9.md) MockServer, [28](28-okhttp-5.md) OkHttp, [29](29-nimbus-jose-jwt-10.md) Nimbus, [30](30-launchdarkly-7.md) LaunchDarkly; Flyway → [08](08-flyway-db.md); protoc → [15](15-protobuf-protoc.md); removals → [38](38-remove-vavr.md) / [39](39-remove-or-migrate-shadow.md) |

Optional LOW (same-major patch only, if pinned and in catalog): awaitility, other test utilities — one commit each.

**Awaitility:** Prefer **no explicit version** — let the Boot BOM manage `org.awaitility:awaitility` on `testImplementation`. Before pinning a catalog `approvedTarget`, confirm the coordinate exists on Maven Central (catalog rows can lead the Central publish). If resolution fails (`Could not find org.awaitility:awaitility:x.y.z`), drop the pin and use the BOM (Boot **4.1.1** manages **4.3.0** as of this writing).

## Phase boundaries (do not mis-file work)

| Change | Phase | Not this queue as… |
|--------|-------|---------------------|
| `javafaker` → `net.datafaker:datafaker` | [09-testing.md](09-testing.md) | “datafaker 2.x bump” |
| Hypersistence `*-hibernate-55/63` → `*-hibernate-73` | [03-hibernate-7.md](03-hibernate-7.md) | Priority 5 |
| Boot / Cloud BOM / Gradle wrapper | [01-platform-baseline.md](01-platform-baseline.md) | Catalog “platform” rows |
| Spring Cloud GCP BOM + bootstrap/API/config migration | [34-spring-cloud-gcp.md](34-spring-cloud-gcp.md) (BOM begins in 01); Pub/Sub code is [43-pubsub.md](43-pubsub.md) | “GCP version-only bump” |
| Lock replace without checking Boot 4 major | — | Prefer [11-distributed-lock.md](11-distributed-lock.md) first |
| springdoc 2.x → 3.x / Knife4j Boot4 / Springfox removal | [32-springdoc-openapi.md](32-springdoc-openapi.md) | “swagger-core patch only” |
| Remove `junit:junit` / Vintage / JUnit 4 sources | [36-junit-jupiter.md](36-junit-jupiter.md) | A Jupiter 5.x pin or “keep Vintage” |
| Remove / replace `io.vavr:vavr` | [38-remove-vavr.md](38-remove-vavr.md) | Interim `1.0.1` bump without analysis |
| Drop or migrate `johnrengelman.shadow` | [39-remove-or-migrate-shadow.md](39-remove-or-migrate-shadow.md) | Bumping frozen `8.1.1` or silent gradleup swap |
| Resilience4j boot3 → boot4 | [40-resilience4j-boot4.md](40-resilience4j-boot4.md) | Leaving boot3 on Boot 4 or BOM-only bump |
| Remove `spring-retry` → Framework 7 resilience | [41-spring-retry-framework.md](41-spring-retry-framework.md) | Bumping `spring-retry` version on Boot 4 |
| Atlassian `swagger-request-validator-*` → `openapi-request-validator-*` when every usage is a comment | This queue, **coordinate only** | Uncommenting matchers or rewriting assertions |
| `org.openrewrite:rewrite-kotlin` with no approved catalog or `catalog-approvals.yaml` row | **Defer** | Inventing a Kotlin **2.3**-era version |
| `dependsOn(tasks.findByPath("jib"))` after a Jib plugin bump | Fix in that Jib commit (below) | Leaving nullable `Task?` in the Kotlin DSL |
| SonarQube Gradle plugin, extension, task, or CI task name | [37-gitlab-ci.md](37-gitlab-ci.md) | Plugin-only bump in this queue |

## Learnings from a full lagging-queue pass (generic)

These patterns held when clearing a Boot 4 / Jackson 3 lagging queue:

1. **Lowest risk first** — commons / faker / swagger before protoc / lock / Cucumber majors.  
2. **jsonschema2pojo 1.3** — see [14-jsonschema2pojo.md](14-jsonschema2pojo.md).  
3. **protoc 4.x** — see [15-protobuf-protoc.md](15-protobuf-protoc.md).  
4. **distributed-lock** — check for a Boot 4 major of the *same* library before planning ShedLock; Boot 4 needs `starter-aspectj` — see [11-distributed-lock.md](11-distributed-lock.md).  
5. **Cucumber 8 + WireMock 3** — see [16-cucumber-8.md](16-cucumber-8.md); leave WireMock 4 until GA.  
6. **Faker + async status tests** — pin amounts/statuses on success paths (phase 09).  
7. **Do not invent versions** — use the catalog; refresh the catalog via AGENT.md, not during migrate.

### OpenAPI request validator (comments only)

Catalog renames `com.atlassian.oai:swagger-request-validator-mockmvc` and `swagger-request-validator-restassured` to `openapi-request-validator-*:3.0.0`. When the only references are comments (for example `// OpenApiValidationMatchers…`), change the coordinate and stop. Do not uncomment assertions or update imports that are not compiled. Re-enable contract checks in a follow-up, not in this queue commit. Live call sites still need the import fix the catalog row describes — that is not the comment-only path.

### `rewrite-kotlin` without an approved row

Bump `org.openrewrite.rewrite` and `org.openrewrite.recipe:rewrite-migrate-java` only when those rows are approved, in one commit. Leave `org.openrewrite:rewrite-kotlin` **deferred** while [DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md) and this migration’s `catalog-approvals.yaml` have no approved target. A plugin bump does not imply a Kotlin **2.3**-era `rewrite-kotlin` version. Do not invent one.

### Kotlin DSL `findByPath` (`Task?`)

Intake routes every `dependsOn(tasks.findByPath(` hit to this phase. Phase 37 does not edit it. `tasks.findByPath("jib")` is `Task?`. `dependsOn(tasks.findByPath("jib"))` fails Kotlin DSL configure (`Task?` vs `Any`), often on the same build file as the plugin bump that registers the task. In that commit, use `dependsOn("jib")` or `tasks.named("jib")`. Grep `findByPath` before marking the bump done.

```kotlin
// BEFORE — configure fails: Task? is not a task dependency
dependsOn(tasks.findByPath("jib"))

// AFTER
dependsOn("jib")
// or: dependsOn(tasks.named("jib"))
```

### Sonar

Do not bump `org.sonarqube` in this queue. Plugin version, Gradle extension, task name, and the CI invocation move together in [37-gitlab-ci.md](37-gitlab-ci.md).

## Steps

1. Open [DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md). List this service’s explicit pins that appear there and are below target.  
2. Apply the bumps this phase owns (respect phase boundaries). Use catalog `approvedTarget` or `catalog-approvals.yaml` — do not re-query Maven for a different number during the queue.  
3. For MED (jsonschema2pojo): generate smoke then commit ([14](14-jsonschema2pojo.md)).  
4. For HIGH (protoc / lock / catalog HIGH): follow phases 15 / 11 / linked notes; stop and ask human if spike fails.  
5. For Cucumber 8 / WireMock 3 align: follow [16-cucumber-8.md](16-cucumber-8.md); ask before WireMock 4.  
6. OpenAPI validator: coordinate-only when usages are comments; defer `rewrite-kotlin` when no approved row exists.  
7. Jib plugin bump: replace `dependsOn(tasks.findByPath("jib"))` in that same commit.  
8. Sonar plugin / task / CI: do not bump here — schedule [37-gitlab-ci.md](37-gitlab-ci.md).  
9. Commit once. The wave's resolve run checks the coordinates; a `Could not find` attributed to this commit is fixed here (drop to the BOM, as for Awaitility, or ask).

## Do not

- Invent versions or “latest from Maven” when the catalog already pins a target.  
- Re-scan other repositories during migrate (the catalog is the pin list).  
- Put a coordinate owned by a dedicated phase into this phase's commit.  
- “While we’re here” upgrade Reactor / Feign / Cloud outside the BOM / catalog.  
- Take WireMock 4 beta “because Cucumber 8 landed.”  
- Bump Hypersistence `55`/`63` → `73` here instead of phase 03.  
- Maven-bump `status=internal` private coordinates.  
- Leave `org.wiremock:wiremock` while CI expects the standalone JAR.  
- Uncomment OpenAPI validator assertions while renaming the coordinate.  
- Bump `org.openrewrite:rewrite-kotlin` when no approved catalog or `catalog-approvals.yaml` row exists.  
- Leave `dependsOn(tasks.findByPath("…"))` in Kotlin DSL after the plugin that registers that task is bumped.  
- Bump `org.sonarqube` here instead of [37-gitlab-ci.md](37-gitlab-ci.md).

## Risk

`SAFE_AUTO` for catalog `approved` targets (and migration-local `catalog-approvals.yaml`) when the linked phase is 12 or the dedicated phase marks the version step SAFE_AUTO. A comment-only OpenAPI validator coordinate rename is `SAFE_AUTO` (no assertion edits). Follow the linked phase for HIGH trains (TC, RA, MockServer, protoc, Flyway, …) — do not re-ask for the catalog version. `SPIKE_FIRST` / `ASK_HUMAN` only when that **phase doc** requires a behavior decision, or the catalog row is still `proposed` / `deferred`. `rewrite-kotlin` with no approved row is deferred, not a version to invent. Sonar is phase 37.

## Rollback

Revert the bump commit, or back out one coordinate by editing its line in a `12-dependency-bump-queue fix:` commit.

## Done when

Catalog-applicable low/medium queue applied or explicitly deferred with reason; HIGH items either done per phases 11 / 14–16 (or human-approved catalog HIGH) or parked with reason (e.g. WireMock 4 = deferred beta). Comment-only OpenAPI validator coordinates changed without uncommenting assertions. `rewrite-kotlin` deferred when no approved row exists. Jib `findByPath` fixed or absent. Sonar left for phase 37.

## Handoff

`bumped=[…]; deferred=[…]; catalogStatus=draft|approved; migrationLocalApprovals=[…]; openapiValidator=coordinate-only|imports-fixed|n/a; rewriteKotlin=deferred|bumped|n/a; findByPath=fixed|n/a; sonar=phase37|n/a`
