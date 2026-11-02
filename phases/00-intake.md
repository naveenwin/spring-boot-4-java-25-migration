# 00 — Intake

## Detect

Always run first.

## Steps

1. Identify build tool: `build.gradle*` / `pom.xml`.  
2. Record the four pinned commands (`baseline`, `context`, `resolve`, `compile`) in `status.yaml` `commands`, using the defaults in [COMPILE-GATES.md](../references/COMPILE-GATES.md#commands-pinned-at-intake). For `baseline`, list every test task the service runs in CI or locally (`test`, `cucumberTest`, `integrationTest`, …), each with its `clean<Task>`. Override `compile` only when `testClasses` is absent or the boot module is not the root.  
3. Record current: Java level and the JDK path the service builds with today (`baselineJdk`), Spring Boot version, Spring Cloud BOM (if any).  
4. Classify path from the recorded Boot version: **Boot 3→4** when it is 3.x, **Boot 2.7→4** when it is 2.7.x. Boot 2.7 still needs the Jakarta and Sleuth inventory rows below.  
5. Inventory flags (yes/no):

| Signal | Looks for |
|--------|-----------|
| Target/compiler alignment | Boot minor, Java/toolchain level, Kotlin plugin, `JvmTarget`, `jvmToolchain`; Boot 4.1 + Java 25 + Kotlin 2.2.x is a mismatch → [31](31-kotlin.md) |
| Gradle task wiring | `dependsOn(tasks.findByPath(` returns nullable `Task?`; route every hit to [12](12-dependency-bump-queue.md), in the same commit as the plugin that registers the task. Phase 37 does not edit this call |
| JPA / Hibernate | `spring-boot-starter-data-jpa`, `@Entity` → ORM provider [03](03-hibernate-7.md); JPA 3.2 / Spring Data JPA 4 [33](33-jpa-spring-data.md) |
| JPA integration shape | custom `EntityManagerFactory`, `org.springframework.boot.orm.jpa`, old naming strategies, native `@Query` with `Pageable`/`Sort`, `QueryEnhancerSelector` → [33](33-jpa-spring-data.md) |
| Hypersistence line | `hypersistence-utils-hibernate-55` / `63` / `71` / `73` or `hibernate-types-*` (line change → [03](03-hibernate-7.md); patch on 73 → [12](12-dependency-bump-queue.md)) |
| Assigned UUID / Persistable | `@GenericGenerator` / custom `UUIDGenerator` / pre-set `@Id` without `Persistable` → [03](03-hibernate-7.md) |
| Hypersistence `update(` | `BaseJpaRepository.update` on managed/`@Version` entities → prefer `merge` in [03](03-hibernate-7.md) |
| Legacy Session / TypeDef | `session.save|update|delete|load`, `@TypeDef` / `@Where` / `@LazyCollection` → [03](03-hibernate-7.md) |
| Spring Data / JPA 3.2 | `getOne`/`getById`/`deleteInBatch`, `hibernate-jpamodelgen`, `Foo_` metamodel, `spring.data.jpa.query.native.parser`, EntityGraph `addSubclassSubgraph` → [33](33-jpa-spring-data.md) |
| Jackson 2 stack (must reach zero in phase 04) | `spring-boot-jackson2`, `spring.jackson2.*`, `preferred-json-mapper=jackson2`, injected mapper, bare `ObjectMapper()`, `jacksonObjectMapper()`; classify production and test call sites separately → [04](04-jackson-3.md) |
| OpenAPI generator | `org.openapi.generator` / `openapi-generator-*` |
| OpenFeign | `spring-cloud-starter-openfeign` |
| WebFlux / WebClient / Reactor Netty | `spring-boot-starter-webflux`, `WebClient`, `spring.http.codecs`, Reactor Netty → [35](35-webflux.md) |
| Spring Retry (legacy) | `spring-retry`, `spring-boot-starter-retry`, `org.springframework.retry.annotation` → [41](41-spring-retry-framework.md) (**must** when Detect; not Resilience4j) |
| Resilience4j | `resilience4j-spring-boot3` / `boot4`, `resilience4j-circuitbreaker` → [40](40-resilience4j-boot4.md) (**must** when Detect) |
| MVC | `spring-boot-starter-web` / `webmvc` |
| Classic vs focused starters | `starter-classic` / bare tech without Boot starter → [19](19-modular-starters.md) |
| Sleuth | `spring-cloud-sleuth` → [07](07-observability.md) |
| Spring Cloud GCP | For every `spring-cloud-gcp-*` starter, record app-owned imports/call sites; search main + test for `sm://`, `ListenableFuture`, `.completable()`, `addCallback`, `AsyncResult`, converters and logging APIs → [34](34-spring-cloud-gcp.md). Pub/Sub also records the pre-migration GCP version and whether `max-ack-extension-period` is set → [43](43-pubsub.md) |
| Actuator / custom endpoints | `starter-actuator`, `@Endpoint` → [22](22-actuator.md) |
| Security / OAuth2 | `starter-security`, OAuth2 → [20](20-spring-security-7.md) |
| Null-safety / Kotlin | NullAway, `org.springframework.lang`, `*.kt` → [21](21-null-safety-jspecify.md), [31-kotlin.md](31-kotlin.md) (**must** if Kotlin) |
| Flyway | Plugin version, starter vs core-only, production DB/vendor module, `spring.flyway.locations` in every profile/external path, and migration tree → [08](08-flyway-db.md) |
| MongoDB | `starter-data-mongodb` → [stubs/mongodb.md](../stubs/mongodb.md) |
| R2DBC | `starter-data-r2dbc` → [stubs/r2dbc.md](../stubs/r2dbc.md) |
| Kafka / AMQP / Batch | `spring-boot-starter-kafka`, `@KafkaListener`, `@EmbeddedKafka` → [44](44-spring-kafka-4.md); AMQP → [stubs/amqp.md](../stubs/amqp.md); Batch → [stubs/batch.md](../stubs/batch.md) |
| Spring Session | `spring.session` → [stubs/spring-session.md](../stubs/spring-session.md) |
| Native / AOT | GraalVM / `RuntimeHints` → [stubs/aot-native.md](../stubs/aot-native.md) |
| Distributed lock | `distributed-lock`, ShedLock, `@JdbcLocked` → [11](11-distributed-lock.md) |
| AOP starter | `starter-aop` / `starter-aspectj` / **missing** while annotation locks exist |
| Lock + messaging | lock deps + Pub/Sub / Kafka / similar → TaskScheduler risk ([11](11-distributed-lock.md)) |
| JUnit | `org.junit.Test` / `org.junit.Assert` / `@RunWith` / `@Rule`, `junit:junit`, Vintage, `cucumber-junit`, and any explicit `org.junit.jupiter` / `org.junit.platform` version or `junit-jupiter.version` → [36](36-junit-jupiter.md). Already-Jupiter sources still record the pin. Compare Cucumber runner package with step and `@CucumberContextConfiguration` packages. |
| OkHttp / MockWebServer | `com.squareup.okhttp3:okhttp` or `mockwebserver` → [28](28-okhttp-5.md) (priority rule in [PHASE-CATALOG.md](../references/PHASE-CATALOG.md#conditional-priority-the-only-place-these-rules-live)) |
| Faker | `javafaker` vs `datafaker` ([09](09-testing.md) / [12](12-dependency-bump-queue.md)) |
| Boot test surface | Count `@MockBean` / `@SpyBean`, old `AutoConfigureMockMvc` imports, RANDOM_PORT tests, Rest Assured scope and `.as(` call sites → [09](09-testing.md), [26](26-rest-assured-6.md) after 36 |
| Protobuf | Plugin / `protoc` / direct `protobuf-java`; also grep `src/main/proto/**` and included proto Gradle/Maven projects — “no `*.proto` under `src/main/java`” is not absent codegen → [15](15-protobuf-protoc.md) (priority rule in [PHASE-CATALOG.md](../references/PHASE-CATALOG.md#conditional-priority-the-only-place-these-rules-live)) |
| Testcontainers | Coordinates versus `org.testcontainers`, `PostgreSQLContainer`, `@Container` usage under `src/test`; declared-only is dependency-only → [25](25-testcontainers-2.md) |
| JsonSchema2Pojo | `jsonschema2pojo` → [14](14-jsonschema2pojo.md) |
| MapStruct | `mapstruct` / SPI → [17](17-mapstruct.md) |
| Cucumber / WireMock | → [16](16-cucumber-8.md); `wiremock` vs `wiremock-standalone` |
| Config property churn / routes | property renames plus `ant_path_matcher`, doubled `/` in mapping strings/constants, method mappings that repeat a class path containing `{var}`, and `server.error.*` / `server.servlet.encoding.*` including keys that live only in an external config store → [18](18-config-properties.md) |
| springdoc / Swagger UI | `org.springdoc`, Knife4j, Springfox → [32-springdoc-openapi.md](32-springdoc-openapi.md) |
| JSqlParser direct use | `net.sf.jsqlparser` → [stubs/jsqlparser.md](../stubs/jsqlparser.md) |
| Virtual threads | `spring.threads.virtual.enabled` → [stubs/virtual-threads.md](../stubs/virtual-threads.md) |
| `@Async` / `@Scheduled` | `taskExecutor` bean name, `AsyncConfigurer`, `spring.task.scheduling` → [stubs/task-execution.md](../stubs/task-execution.md) |
| Container / k8s rollout | Dockerfile / CrashLoop → [stubs/jvm-containers.md](../stubs/jvm-containers.md), [stubs/k8s-startup.md](../stubs/k8s-startup.md) |
| Metrics/tracing pins | Sleuth imports/config, direct Micrometer versions, actuator `micrometer-core` excludes, legacy Prometheus keys → [07](07-observability.md), [22](22-actuator.md) |
| Sonar Gradle plugin | Legacy `sonarqube` extension, task, or `./gradlew sonarqube` → [37](37-gitlab-ci.md). Do not inventory CI images. |

6. Emit **Applicable phases** plus a compact implementation-shape table. For each detected technology record `declared`, `sourceUsage` (`used` | `declared-only` | `none`), `phase`, and `decisionNeeded`. Each `decisionNeeded` becomes a blocker on that item in the plan. Include dedicated rows for Flyway layout/vendor, Testcontainers usage, GCP modules/call sites, Cucumber runner/glue packages, JPA native paging/package moves, and the context owner (the `@CucumberContextConfiguration` class or smallest `@SpringBootTest`, its test task, and any infrastructure it needs) for [42-baseline.md](42-baseline.md).
7. Flag anything `ASK_HUMAN` / `SPIKE_FIRST` for the human before work starts.  
8. Hand off to the **catalog gap preflight** ([CATALOG-GAP.md](../references/CATALOG-GAP.md)): declared pins/plugins vs catalog/phases/stubs. Intake itself does not approve versions or promote stubs.

If the human already named an upstream version this repository must wait for, record that gate in the plan. Do not open other repositories during intake.

## Do not

- Start code changes in intake.  
- Clone or open other services for comparison.

## Risk

`SAFE_AUTO`

## Rollback

N/A (read-only).

## Done when

Parent has a short markdown table: phase → applicable → risk, including which Detect hits are **stub-only** (must be promoted before plan per [CATALOG-GAP.md](../references/CATALOG-GAP.md)).

## Handoff

`Path=3to4|2to4; Build=Gradle|Maven; commands=default|custom; baselineJdk=<version>; contextOwner=<class>|none; Web=MVC|WebFlux|both; Phases=[...]; StubsRequired=[...]`
