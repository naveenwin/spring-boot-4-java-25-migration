# Phase catalog and planner order

**Migrate agents:** use this file with [SKILL.md](../SKILL.md). Do **not** read `MANUAL.md`.

Skip phases that intake marks **N/A**. The `NN` in `phases/NN-name.md` is a stable id, never renumbered. **Order** is the execution sequence. Stage A walks the table top to bottom applying build edits; Stage B walks it again applying source edits. Test-side phases come last in Stage B because test compilation only runs once main compiles.

Compile-error ownership for Stage B is [ownership.json](ownership.json).

## Conditional priority (the only place these rules live)

| Phase | `must` when | Otherwise |
|-------|-------------|-----------|
| [15-protobuf-protoc](../phases/15-protobuf-protoc.md) | Spring Cloud GCP Pub/Sub is present and the service has protobuf codegen or a direct protobuf / protoc **3.x** pin | `good` |
| [43-pubsub](../phases/43-pubsub.md) | `spring-cloud-gcp-starter-pubsub`, `spring-cloud-gcp-pubsub-stream-binder`, `PubSubTemplate`, or `spring.cloud.gcp.pubsub` | n/a |
| [28-okhttp-5](../phases/28-okhttp-5.md) | Legacy `com.squareup.okhttp3:mockwebserver` (4.x or 5.x) is present — phase 36 removes `junit:junit`, which that artifact needs | `good` for client-only OkHttp 4 |
| [36-junit-jupiter](../phases/36-junit-jupiter.md) | Any test source, Boot test starter, or JUnit coordinate. Already-Jupiter sources still run the JUnit 6 half | n/a only with no tests and no JUnit coordinates |
| [31-kotlin](../phases/31-kotlin.md) | `*.kt` sources or a Kotlin Gradle plugin | n/a |
| [37-gitlab-ci](../phases/37-gitlab-ci.md) | Legacy `sonarqube` extension, task, or `./gradlew sonarqube` | n/a |
| [38](../phases/38-remove-vavr.md), [39](../phases/39-remove-or-migrate-shadow.md), [40](../phases/40-resilience4j-boot4.md), [41](../phases/41-spring-retry-framework.md) | Detect hits | n/a |
| [44-spring-kafka-4](../phases/44-spring-kafka-4.md) | `spring-boot-starter-kafka`, `spring-kafka`, `spring-kafka-test`, `@KafkaListener`, or `@EmbeddedKafka` | n/a |
| [45-task-execution](../phases/45-task-execution.md) | `@Async`, `@Scheduled`, `AsyncConfigurer`, a `taskExecutor` / `applicationTaskExecutor` bean, or `spring.task.execution` / `spring.task.scheduling` | n/a |
| [23-over-engineer-gate](../phases/23-over-engineer-gate.md) | Never by default — the human asks, or the planner inserts it once after Stage B when the diff is large | `good` |

## Order

| Order | Phase | Stage B side | Default execution gate |
|------:|-------|--------------|------------------------|
| 0 | [00-intake](../phases/00-intake.md) | — | read-only |
| 0 | [42-baseline](../phases/42-baseline.md) | Stage 0 | SAFE_AUTO; ASK_HUMAN for missing infrastructure or baseline failures |
| 1 | [01-platform-baseline](../phases/01-platform-baseline.md) | build | SAFE_AUTO |
| 2 | [37-gitlab-ci](../phases/37-gitlab-ci.md) | build | SAFE_AUTO for the Sonar rename in this repo; do not edit images |
| 3 | [31-kotlin](../phases/31-kotlin.md) | main | ASK_HUMAN — Kotlin **2.3.21** (Boot 4.1) + JDK 25 |
| 4 | [04-jackson-3](../phases/04-jackson-3.md) | main | ASK_HUMAN for wire changes; Jackson 2 runtime need is `blocked` |
| 5 | [24-tomcat-boot-managed](../phases/24-tomcat-boot-managed.md) | main | ASK_HUMAN for WAR / Security pin; else SAFE_AUTO |
| 6 | [18-config-properties](../phases/18-config-properties.md) | main | SAFE_AUTO renames; ASK_HUMAN for route patterns or env contracts |
| 7 | [34-spring-cloud-gcp](../phases/34-spring-cloud-gcp.md) | main | SPIKE_FIRST bootstrap/auth |
| 8 | [15-protobuf-protoc](../phases/15-protobuf-protoc.md) | main | SPIKE_FIRST |
| 9 | [43-pubsub](../phases/43-pubsub.md) | main | SPIKE_FIRST lease/converter; SAFE_AUTO only when source GCP is ≥ 6 and there is no JSON converter |
| 10 | [19-modular-starters](../phases/19-modular-starters.md) | main | SAFE_AUTO classic bridge; ASK_HUMAN to exit classic |
| 11 | [02-jakarta-ee](../phases/02-jakarta-ee.md) | main | SAFE_AUTO |
| 12 | [03-hibernate-7](../phases/03-hibernate-7.md) | main | ASK_HUMAN for custom types / Persistable / merge / Session API / DDL |
| 13 | [33-jpa-spring-data](../phases/33-jpa-spring-data.md) | main | ASK_HUMAN for native parser / EM wiring / derived-query edges |
| 14 | [35-webflux](../phases/35-webflux.md) | main | SAFE_AUTO codecs/starters; ASK_HUMAN allocator/performance/security |
| 15 | [05-openapi-generator](../phases/05-openapi-generator.md) | main | SAFE_AUTO; ASK_HUMAN for regeneration surprises |
| 16 | [32-springdoc-openapi](../phases/32-springdoc-openapi.md) | main | ASK_HUMAN for Springfox/Knife4j swap |
| 17 | [06-http-clients](../phases/06-http-clients.md) | main | SAFE_AUTO converters; ASK_HUMAN Feign/codec |
| 18 | [41-spring-retry-framework](../phases/41-spring-retry-framework.md) | main | ASK_HUMAN for each `maxAttempts` → `maxRetries` and `@Recover`; SAFE_AUTO with zero call sites |
| 19 | [44-spring-kafka-4](../phases/44-spring-kafka-4.md) | main | SAFE_AUTO for the test starter and removed ZooKeeper attributes; ASK_HUMAN before `group.protocol=consumer` |
| 20 | [20-spring-security-7](../phases/20-spring-security-7.md) | main | SPIKE_FIRST / ASK_HUMAN |
| 21 | [07-observability](../phases/07-observability.md) | main | SAFE_AUTO when Sleuth present |
| 22 | [22-actuator](../phases/22-actuator.md) | main | SAFE_AUTO props; ASK_HUMAN exposure |
| 23 | [45-task-execution](../phases/45-task-execution.md) | main | SAFE_AUTO for the auto-config name and a null `getAsyncExecutor`; ASK_HUMAN for an alias, a pool size, or renaming a custom executor |
| 24 | [21-null-safety-jspecify](../phases/21-null-safety-jspecify.md) | main | ASK_HUMAN for NullAway / Kotlin cascade |
| 25 | [08-flyway-db](../phases/08-flyway-db.md) | main | SAFE_AUTO module/version align with SQL frozen; ASK_HUMAN for SQL or locations |
| 26 | [10-build-plugins](../phases/10-build-plugins.md) | build | SAFE_AUTO Spotless 7 / GJF |
| 27 | [14-jsonschema2pojo](../phases/14-jsonschema2pojo.md) | main | SAFE_AUTO after generate smoke |
| 28 | [17-mapstruct](../phases/17-mapstruct.md) | main | SAFE_AUTO |
| 29 | [29-nimbus-jose-jwt-10](../phases/29-nimbus-jose-jwt-10.md) | main | ASK_HUMAN |
| 30 | [30-launchdarkly-7](../phases/30-launchdarkly-7.md) | main | ASK_HUMAN — `LDUser` → `LDContext` |
| 31 | [11-distributed-lock](../phases/11-distributed-lock.md) | main | ASK_HUMAN if replace |
| 32 | [38-remove-vavr](../phases/38-remove-vavr.md) | main | analysis + risk score; remove/replace or park |
| 33 | [39-remove-or-migrate-shadow](../phases/39-remove-or-migrate-shadow.md) | build | prefer drop, else gradleup 9.6.x |
| 34 | [40-resilience4j-boot4](../phases/40-resilience4j-boot4.md) | main | boot3 → boot4 2.4.0 |
| 35 | [12-dependency-bump-queue](../phases/12-dependency-bump-queue.md) | main | SAFE_AUTO for approved catalog targets |
| 36 | [36-junit-jupiter](../phases/36-junit-jupiter.md) | test | SAFE_AUTO for Boot-managed JUnit 6; ASK_HUMAN for JUnit 4 rules / parameterized / message-first asserts |
| 37 | [28-okhttp-5](../phases/28-okhttp-5.md) | test | SPIKE_FIRST when tests use MockWebServer |
| 38 | [09-testing](../phases/09-testing.md) | test | SAFE_AUTO for the Boot test surface; ASK_HUMAN before a production error-body override |
| 39 | [25-testcontainers-2](../phases/25-testcontainers-2.md) | test | SAFE_AUTO when declared-only; SPIKE_FIRST when used |
| 40 | [26-rest-assured-6](../phases/26-rest-assured-6.md) | test | ASK_HUMAN |
| 41 | [27-mockserver-9](../phases/27-mockserver-9.md) | test | ASK_HUMAN |
| 42 | [16-cucumber-8](../phases/16-cucumber-8.md) | test | often `good` + medium |
| 43 | [13-verification](../phases/13-verification.md) | Stage C | context + suite vs baseline |

### Reference index (same folder)

| Doc | Role |
|-----|------|
| [DEPENDENCY-CATALOG.md](DEPENDENCY-CATALOG.md) | Third-party pin targets |
| [ownership.json](ownership.json) | Compile-error → owning phase rules |
| [DEP-REMOVAL.md](DEP-REMOVAL.md) | Remove-and-replace protocol |
| [MIGRATION-EVIDENCE.md](MIGRATION-EVIDENCE.md) | Symptom → verified fix |
| [CONTEXT-CONTROL.md](CONTEXT-CONTROL.md) | Capsules, readiness, verifier, chat reset |
| [COMPILE-GATES.md](COMPILE-GATES.md) | Commands, run procedure, stage gates, bounded lookup |
| [LOG-TRIAGE.md](LOG-TRIAGE.md) | Stage C failure clustering and routing |
| [CATALOG-GAP.md](CATALOG-GAP.md) | Post-intake declared-dependency map |
| [99-anti-patterns.md](99-anti-patterns.md) | Cross-cutting rules |

### Stubs (Detect → use or skip)

[maven](../stubs/maven.md) · [mongodb](../stubs/mongodb.md) · [r2dbc](../stubs/r2dbc.md) · [aot-native](../stubs/aot-native.md) · [amqp](../stubs/amqp.md) · [batch](../stubs/batch.md) · [spring-session](../stubs/spring-session.md) · [http-service-clients](../stubs/http-service-clients.md) · [dependency-diagnosis](../stubs/dependency-diagnosis.md) · [jsqlparser](../stubs/jsqlparser.md) · [virtual-threads](../stubs/virtual-threads.md) · [jvm-containers](../stubs/jvm-containers.md) · [postgresql-tls](../stubs/postgresql-tls.md) · [k8s-startup](../stubs/k8s-startup.md)
