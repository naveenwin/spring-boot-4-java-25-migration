# DEPENDENCY-CATALOG — Boot 4 / Java 25 pins

> **Status:** apply via the linked phase or phase 12. `migrate` rows change coordinates; they are not a version menu.  
> **Migrate** rows: vavr→[38](../phases/38-remove-vavr.md), shadow→[39](../phases/39-remove-or-migrate-shadow.md), resilience4j-boot3→[40](../phases/40-resilience4j-boot4.md), microutils kotlin-logging→oshai, javafaker/mockito-kotlin/hypersistence/LD client (linked phases).  
> **Targets:** stable releases on Maven Central or the Plugin Portal, constrained by the phase docs. Refresh from public metadata — see [AGENT.md](../AGENT.md). Do not copy a pin from another repository.  
> **Last reviewed:** 2026-11-01, for the Boot **4.1.1** / Java **25** line this file targets. When a current release note disagrees with a row, the release note wins. Change this date in the same edit that changes a pin.

## How migrate agents use this

1. In the Stage A dependency wave, each owning phase's A slice reads this file (phase 12 for plain bumps, [12-dependency-bump-queue.md](../phases/12-dependency-bump-queue.md)).
2. For each **explicit pin** in *this* service that appears below with `status=proposed` or `approved`, bump toward `proposedTarget` (or `approvedTarget` once approved).
3. Respect `risk` and the linked `phase`: the coordinate lands in that phase's Stage A commit. Platform rows normally use phase 01; GCP uses phase 01 for BOM alignment plus linked phase 34 for executable migration.
4. **Do not** open other repositories; **do not** invent versions missing from this catalog.
5. Apply `status=approved` without re-asking for a version target. If `phase` is a dedicated phase (not only 12), follow that phase — do not silent-bump. Phase docs may still `ASK_HUMAN` for behavior/API choices. For remaining `status=proposed`, ask before applying. Rows with `status=migrate` need a coordinate/module change via the linked phase — not a silent version bump.

## Rules

| Rule | Detail |
|------|--------|
| Explicit pins only | Literal versions / version variables / version catalog entries |
| BOM-managed | Prefer Boot / Cloud BOM when catalog says `Boot BOM` |
| Max stable | No alpha / beta / RC / milestone in `proposedTarget` |
| Phase caps | WireMock 4 deferred; Hypersistence line → phase 03; Cucumber 8 → phase 16; etc. |
| Internal | `status=internal` — never Maven-bump |
| Refresh | Enhance-agent only (see AGENT.md); migrate-agent reads frozen catalog |

## Status legend

| status | Meaning |
|--------|---------|
| `proposed` | Research recommendation; awaiting human approval |
| `approved` | Human locked — migrate agents apply target without re-asking (via linked phase or phase 12) |
| `deferred` | Newer line exists but blocked (beta / policy) |
| `migrate` | Coordinate / module-line change (not version-only) |
| `platform` | Owned by phase 01 |
| `internal` | Private artifact published by the organization. Do not bump it from Maven Central. |

## Platform trains (phase 01 plus linked executable phases)

| coordinate | proposedTarget | status | maxStableFound | risk | phase | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `org.springframework.boot (plugin)` | `4.1.1` | platform | `4.1.1` | — | 01 | Use [01-platform-baseline](../phases/01-platform-baseline.md); latest 4.1.x stable |
| `io.spring.dependency-management (plugin)` | `1.1.7` | platform | `1.1.7` | LOW | 01 | Align with Boot line |
| `Spring Cloud BOM train` | `2025.1.x` | platform | `2025.1.2+` | — | 01 | Boot 4 train only — never 2025.0.x |
| `com.google.cloud:spring-cloud-gcp-dependencies` | `8.2.4` | platform | `8.2.4` | MED | 34 | BOM alignment starts in 01; bootstrap/API/config is [34](../phases/34-spring-cloud-gcp.md); Pub/Sub lease, converter, and health are [43](../phases/43-pubsub.md). Do not use 8.0.0–8.0.3 (Jackson 2 BOM import). |

## Spring Kafka (phase 44)

| coordinate | proposedTarget | status | maxStableFound | risk | phase | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `org.springframework.kafka:spring-kafka` | Boot BOM | approved | Boot BOM | MED | 44 | Do not pin a version ahead of the Boot BOM. Steps: [44-spring-kafka-4](../phases/44-spring-kafka-4.md) |
| `org.springframework.kafka:spring-kafka-test` | `spring-boot-starter-kafka-test` (Boot BOM) | migrate | — | MED | 44 | Replace the test artifact. Do not version-bump `spring-kafka-test` |

## Apache Commons & small utilities

| coordinate | proposedTarget | status | maxStableFound | risk | phase | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `org.apache.commons:commons-lang3` | `3.21.0` | approved | `3.21.0` | LOW | 12 | Same-major patch/minor |
| `org.apache.commons:commons-text` | `1.15.0` | approved | `1.15.0` | LOW | 12 |  |
| `org.apache.commons:commons-collections4` | `4.6.0` | approved | `4.6.0` | LOW | 12 | Prefer GA 4.6.0 over 4.5.0-M2 milestone |
| `org.apache.commons:commons-csv` | `1.14.1` | approved | `1.14.1` | LOW | 12 |  |
| `org.apache.commons:commons-pool2` | `2.13.1` | approved | `2.13.1` | LOW | 12 |  |
| `org.apache.commons:commons-math3` | `3.6.1` | approved | `3.6.1` | LOW | 12 | Line frozen; math4 is different artifact |
| `commons-io:commons-io` | `2.22.0` | approved | `2.22.0` | LOW | 12 |  |
| `commons-fileupload:commons-fileupload` | `1.6.0` | approved | `1.6.0` | LOW | 12 | Legacy; prefer fileupload2 for new work |
| `com.google.code.gson:gson` | `2.14.0` | approved | `2.14.0` | LOW | 12 |  |
| `com.google.guava:guava` | `33.7.2-jre` | approved | `33.7.2-jre` | LOW | 12 | Use -jre classifier |
| `com.cronutils:cron-utils` | `9.2.1` | approved | `9.2.1` | LOW | 12 |  |
| `com.opencsv:opencsv` | `5.10` | approved | `5.10` | LOW | 12 |  |
| `org.apache.poi:poi-ooxml` | `5.5.1` | approved | `5.5.1` | MED | 12 | Keep poi + poi-ooxml aligned |
| `org.owasp:security-logging-logback` | `1.1.7` | approved | `1.1.7` | LOW | 12 |  |
| `org.owasp.encoder:encoder` | `1.3.1` | approved | `1.3.1` | LOW | 12 |  |
| `org.bouncycastle:bcprov-jdk18on` | `1.86` | approved | `1.86` | MED | 12 | Align other bc* jars |
| `joda-time:joda-time` | `2.15.0` | approved | `2.15.0` | LOW | 12 | Prefer java.time for new code |
| `io.vavr:vavr` | `drop (prefer)` | migrate | `1.0.1` | MED | 38 | Prefer remove via [38-remove-vavr](../phases/38-remove-vavr.md) (analysis + risk score). Interim `1.0.1` only if HIGH/parked |
| `com.jayway.jsonpath:json-path` | `3.0.0` | approved | `3.0.0` | MED | 12 | Jackson 3 providers; override Boot-managed 2.10.0 when wiring Jackson mapping |
| `org.skyscreamer:jsonassert` | `1.5.3` | approved | `1.5.3` | LOW | 12 |  |
| `net.java.dev.jna:jna` | `5.19.1` | approved | `5.19.1` | LOW | 12 |  |
| `org.locationtech.jts:jts-core` | `1.20.0` | approved | `1.20.0` | LOW | 12 |  |
| `io.pebbletemplates:pebble` | `4.1.2` | approved | `4.1.2` | MED | 12 | Boot 4 starter = `pebble-spring-boot-starter:4.1.2` (not legacy Boot 3 starter) |

## Testing, mocking, Cucumber, WireMock

| coordinate | proposedTarget | status | maxStableFound | risk | phase | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `org.awaitility:awaitility` | `omit pin / Boot BOM 4.3.0` | approved | `4.3.0` (Boot BOM) | LOW | 12 | Omit the pin; Boot BOM **4.3.0**. Never approve **4.3.1**. |
| `org.awaitility:awaitility-kotlin` | `omit pin / Boot BOM 4.3.0` | approved | `4.3.0` (Boot BOM) | LOW | 12 | Same as `awaitility`. Omit the pin; Boot BOM **4.3.0**. Never approved **4.3.1**. |
| `org.wiremock:wiremock` | `3.13.2` | approved | `4.0.0-beta.*` | LOW | 12/16 | Approved 3.13.2; WireMock 4 remains deferred (see policy). |
| `org.wiremock:wiremock-standalone` | `3.13.2` | approved | `4.0.0-beta.*` | LOW | 12/16 | Approved 3.13.2; prefer standalone when CI copies JAR; WireMock 4 remains deferred (see policy). |
| `net.datafaker:datafaker` | `2.7.0` | approved | `2.7.0` | LOW | 09/12 | Target if already on datafaker |
| `com.github.javafaker:javafaker` | `→ datafaker 2.7.0` | migrate | `1.0.2` | MED | 09 | Do not bump javafaker; migrate to net.datafaker:datafaker |
| `io.cucumber:cucumber-java` | `8.0.4` | approved | `8.0.4` | MED | 16 | Max bump = 8.0.4 (align cucumber-spring/junit*). Low-risk alt: 7.34.9 same-major |
| `io.cucumber:cucumber-spring` | `8.0.4` | approved | `8.0.4` | MED | 16 | Same version as cucumber-java |
| `io.cucumber:cucumber-junit` | `8.0.4` | approved | `8.0.4` | MED | 16 | Or junit-platform-engine on 8.x |
| `io.cucumber:cucumber-junit-platform-engine` | `8.0.4` | approved | `8.0.4` | MED | 16 |  |
| `org.mock-server:mockserver-junit-jupiter` | `9.0.0` | approved | `9.0.0` | HIGH | 27 | Apply via [27-mockserver-9](../phases/27-mockserver-9.md); use `*-no-dependencies` |
| `org.mock-server:mockserver-netty` | `9.0.0` | approved | `9.0.0` | HIGH | 27 | Align with junit-jupiter; phase 27 |
| `io.mockk:mockk` | `1.14.11` | approved | `1.14.11` | LOW | 12 |  |
| `org.mockito.kotlin:mockito-kotlin` | `6.4.0` | approved | `6.4.0` | MED | 12 | Replaces com.nhaarman.mockitokotlin2 |
| `com.nhaarman.mockitokotlin2:mockito-kotlin` | `→ org.mockito.kotlin:6.4.0` | migrate | `2.2.0` | MED | 09 | Migrate coordinate; do not bump 2.2.0 line |
| `org.mockito:mockito-inline` | `drop` | approved | `5.2.0` | LOW | 09 | Inline mocking in mockito-core 5.x — remove mockito-inline pin (migrate path approved) |
| `org.mockito:mockito-core` | `Boot BOM` | approved | `5.24.0` | LOW | 09 | Prefer Boot BOM; maxStable 5.24.0 if pin required |
| `org.assertj:assertj-core` | `Boot BOM` | approved | `3.27.7` | LOW | 09 | Prefer Boot BOM unless pin required |
| `com.ninja-squad:springmockk` | `4.0.2` | approved | `4.0.2` | LOW | 12 |  |
| `io.rest-assured:rest-assured` | `6.2.0` | approved | `6.2.0` | HIGH | 26 | Apply via [26-rest-assured-6](../phases/26-rest-assured-6.md); pin explicitly (Boot 4 BOM does not manage RA) |
| `org.testcontainers:testcontainers-bom` | `2.0.5` | approved | `2.0.5` | HIGH | 25 | Apply via [25-testcontainers-2](../phases/25-testcontainers-2.md); rename modules to `testcontainers-*` |
| `org.testcontainers:testcontainers` | `2.0.5` | approved | `2.0.5` | HIGH | 25 | Prefer BOM; phase 25 |
| `org.testcontainers:postgresql` | `testcontainers-postgresql` (BOM 2.0.5) | approved | `2.0.5` | HIGH | 25 | Artifact rename in 2.x — phase 25 |
| `io.github.serpro69:kotlin-faker` | `1.16.2` | approved | `1.16.2` | LOW | 12 | 2.0 still RC — stay 1.16.x |
| `com.willowtreeapps.assertk:assertk` | `0.28.1` | approved | `0.28.1` | LOW | 12 |  |
| `org.amshove.kluent:kluent` | `1.73` | approved | `1.73` | LOW | 12 |  |
| `io.kotest:kotest-runner-junit5` | `6.2.6` | approved | `6.2.6` | HIGH | 31 | Approved; co-migrate with [31-kotlin.md](../phases/31-kotlin.md) |
| `io.kotest:kotest-assertions-core` | `6.2.6` | approved | `6.2.6` | HIGH | 31 | Approved; align with kotest-runner — phase 31 |
| `com.tngtech.archunit:archunit-junit5` | `1.4.1` | approved | `1.4.1` | LOW | 12 |  |
| `com.atlassian.oai:swagger-request-validator-mockmvc` | `openapi-request-validator-mockmvc:3.0.0` | approved | `3.0.0` | HIGH | 12 | Approved. 3.0 renamed artifact to `openapi-request-validator-mockmvc:3.0.0` (Spring 7 / Boot 4). When every usage is a comment, change the coordinate only — do not uncomment matchers or rewrite assertions. Live call sites still need the import fix and a contract-test re-run. |
| `com.atlassian.oai:swagger-request-validator-restassured` | `openapi-request-validator-restassured:3.0.0` | approved | `3.0.0` | HIGH | 12 | Approved. 3.0 renamed artifact to `openapi-request-validator-restassured:3.0.0`. Same comment-only rule as mockmvc: coordinate only when usages are comments. Live call sites still need the import fix and a contract-test re-run. |
| `se.thinkcode.cucumber-runner` | `0.0.14` | approved | `0.0.14` | LOW | 12 |  |

## MapStruct, Lombok, OpenAPI / Swagger, Protobuf, codegen

| coordinate | proposedTarget | status | maxStableFound | risk | phase | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `org.mapstruct:mapstruct` | `1.6.3` | approved | `1.6.3` | LOW | 17 | Skip 1.7 betas; align processor |
| `org.mapstruct:mapstruct-processor` | `1.6.3` | approved | `1.6.3` | LOW | 17 |  |
| `org.projectlombok:lombok` | `1.18.48` | approved | `1.18.48` | LOW | 12 | Confirm JDK 25 annotation processing |
| `org.projectlombok:lombok-mapstruct-binding` | `0.2.0` | approved | `0.2.0` | LOW | 12 |  |
| `org.springdoc:springdoc-openapi-starter-webmvc-ui` | `3.1.1` | approved | `3.1.1` | HIGH | 32 | Boot **4** requires springdoc **3.x**. Confirm current patch on springdoc.org before pin. WebFlux: `…-webflux-ui`. See [32-springdoc-openapi.md](../phases/32-springdoc-openapi.md) |
| `org.springdoc:springdoc-openapi-starter-webmvc-api` | `3.1.1` | approved | `3.1.1` | HIGH | 32 | API-only (no UI). Same major as UI starter |
| `com.baizhukui:knife4j-openapi3-boot4-spring-boot-starter` | `5.7.9` | approved | `5.7.9` | HIGH | 32 | Boot4 only; manages springdoc 3.0.3 in Knife4j Next matrix. Never use Jakarta Boot3 starter on Boot 4 |
| `io.swagger.core.v3:swagger-core` | `2.2.55` | approved | `2.2.55` | MED | 12/32 | Bump annotations+models+core same version; still Jackson-2 based until swagger-core Jackson 3 lands |
| `io.swagger.core.v3:swagger-annotations` | `2.2.55` | approved | `2.2.55` | MED | 12/32 |  |
| `io.swagger.core.v3:swagger-models` | `2.2.55` | approved | `2.2.55` | MED | 12/32 |  |
| `com.google.protobuf:protoc` | `4.36.2` | approved | `4.36.2` | HIGH | 15 | Align protobuf-java; skip 4.37 RC |
| `com.google.protobuf:protobuf-java` | `4.36.2` | approved | `4.36.2` | HIGH | 15 |  |
| `com.google.protobuf:protobuf-java-util` | `4.36.2` | approved | `4.36.2` | HIGH | 15 |  |
| `com.google.protobuf:protobuf-gradle-plugin` | `0.10.0` | approved | `0.10.0` | MED | 15 | Also via plugin id com.google.protobuf |
| `io.github.pseudomuto:protoc-gen-doc` | `1.5.1` | approved | `1.5.1` | LOW | 15 |  |
| `org.jsonschema2pojo (plugin)` | `1.3.3` | approved | `1.3.3` | MED | 14 | Fleet on 1.2.x |
| `org.openapi.generator (plugin)` | `7.26.0` | approved | `7.26.0` | MED | 05 | >=7.16 for Boot4/Jackson3 flags |

## Persistence helpers & DB drivers

| coordinate | proposedTarget | status | maxStableFound | risk | phase | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `io.hypersistence:hypersistence-utils-hibernate-73` | `3.16.0` | approved | `3.16.0` | LOW | 03/12 | Hibernate **7.3 and 7.4** target line (Boot 4.0→H7.2 / Boot 4.1→H7.4 via BOM; do not invent `*-74`) |
| `io.hypersistence:hypersistence-utils-hibernate-63` | `→ hibernate-73 3.16.0` | migrate | `3.8.3` | MED | 03 | Artifact line change in Hibernate 7 phase |
| `io.hypersistence:hypersistence-utils-hibernate-60` | `→ hibernate-73 3.16.0` | migrate | `3.5.0` | MED | 03 |  |
| `com.vladmihalcea:hibernate-types-60` | `→ hypersistence-utils-hibernate-73` | migrate | `2.21.1` | MED | 03 |  |
| `com.vladmihalcea:hibernate-types-52` | `→ hypersistence-utils-hibernate-73` | migrate | `2.9.13` | MED | 03 |  |
| `org.postgresql:postgresql` | `42.7.14` | approved | `42.7.14` | LOW | 12 | Prefer Boot BOM unless CVE pin needed |
| `org.flywaydb:flyway-core` | `13.10.3` | approved | `13.10.3` | HIGH | 08 | Ahead of Boot BOM (Boot 4.1.1 manages 12.4.0). Align plugin + core + vendor to this version. Production schema history stays unverified. |
| `org.flywaydb:flyway-database-postgresql` | `13.10.3` | approved | `13.10.3` | HIGH | 08 | Same version as plugin and `flyway-core` when the target is ahead of the Boot BOM. |
| `org.flywaydb:flyway-mysql` | `13.10.3` | approved | `13.10.3` | HIGH | 08 | Same version as plugin and `flyway-core` when the target is ahead of the Boot BOM. |
| `com.zaxxer:HikariCP` | `Boot BOM` | approved | `7.1.0` | LOW | 01 | Prefer Boot-managed; avoid override unless needed |
| `com.h2database:h2` | `2.5.252` | approved | `2.5.252` | MED | 12 |  |
| `com.mysql:mysql-connector-j` | `Boot BOM / 9.7.0` | approved | `26.7.0` | HIGH | 12 | Prefer Boot-managed **9.7.0** (omit version). `26.7.0` is real Oracle calver GA (ahead of Boot BOM) — see verification section below. |
| `com.oracle.database.jdbc:ojdbc8` | `23.3.0.23.09` | approved | `23.3.0.23.09` | MED | 12 | Confirm latest ojdbc on Maven for JDK 25 |
| `org.postgresql:r2dbc-postgresql` | `1.1.3.RELEASE` | approved | `1.1.3.RELEASE` | MED | stubs/r2dbc | Keep+bump; Boot 4.1 manages ~1.1.1 — 1.1.3 override OK |
| `org.apache.tomcat.embed:tomcat-embed-core` | `Boot BOM (remove pin)` | approved | `11.0.x` | HIGH | 24 | Apply via [24-tomcat-boot-managed](../phases/24-tomcat-boot-managed.md) — decommission pins |
| `org.hibernate.validator:hibernate-validator` | `Boot BOM` | approved | `9.1.5.Final` | LOW | 01 | Prefer Boot BOM |
| `jakarta.validation:jakarta.validation-api` | `Boot BOM` | approved | `3.1.1` | LOW | 01 | Prefer Boot BOM |

## HTTP clients, feature flags, security, gRPC, OTel

| coordinate | proposedTarget | status | maxStableFound | risk | phase | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `com.squareup.okhttp3:okhttp` | `5.5.0` | approved | `5.5.0` | MED | 28 | Apply via [28-okhttp-5](../phases/28-okhttp-5.md); prefer okhttp-bom; Maven uses okhttp-jvm |
| `com.squareup.okhttp3:mockwebserver` | `replace with mockwebserver3 5.5.0` | approved | `5.5.0` | MED | 28 | Legacy artifact still depends on `junit:junit` at 5.5.0. Phase 28 is `must` while this coordinate remains and swaps it in the Stage A wave. Declare `mockwebserver3` under `okhttp-bom`. Do not add `mockwebserver3-junit5` on Boot 4 |
| `com.squareup.okhttp3:mockwebserver3` | `5.5.0` | approved | `5.5.0` | MED | 28 | JUnit-free MockWebServer. BOM-managed. Tests call `start` / `close`; `RecordedRequest.target` includes the query |
| `com.launchdarkly:launchdarkly-java-server-sdk` | `7.17.3` | approved | `7.17.3` | MED | 30 | Apply via [30-launchdarkly-7](../phases/30-launchdarkly-7.md); LDUser→LDContext; Relay≥8 |
| `com.launchdarkly:launchdarkly-client` | `→ server-sdk 7.17.3` | migrate | `4.6.3` | MED | 30 | Legacy artifact name; multi-hop via phase 30 (not a one-step bump) |
| `com.nimbusds:nimbus-jose-jwt` | `10.10` | approved | `10.10` | HIGH | 29 | Apply via [29-nimbus-jose-jwt-10](../phases/29-nimbus-jose-jwt-10.md); never 10.0–10.2; align with SS7 oauth2-jose |
| `io.jsonwebtoken:jjwt-api` | `0.13.0` | approved | `0.13.0` | MED | 12 | Keep jjwt-impl + jjwt-jackson same version |
| `io.jsonwebtoken:jjwt-impl` | `0.13.0` | approved | `0.13.0` | MED | 12 |  |
| `io.jsonwebtoken:jjwt-jackson` | `0.13.0` | approved | `0.13.0` | MED | 12 |  |
| `io.grpc:grpc-bom` | `1.85.0` | approved | `1.85.0` | MED | 12 | Align with protobuf 4.36.x |
| `io.grpc:grpc-protobuf` | `1.85.0` | approved | `1.85.0` | MED | 12 |  |
| `io.grpc:grpc-stub` | `1.85.0` | approved | `1.85.0` | MED | 12 |  |
| `io.grpc:grpc-netty-shaded` | `1.85.0` | approved | `1.85.0` | MED | 12 |  |
| `io.opentelemetry.javaagent:opentelemetry-javaagent` | `2.32.0` | approved | `2.32.0` | MED | 12 |  |
| `io.opentelemetry.instrumentation:opentelemetry-instrumentation-annotations` | `2.32.0` | approved | `2.32.0` | MED | 12 | Align with agent train where practical |
| `net.logstash.logback:logstash-logback-encoder` | `9.0` | approved | `9.0` | MED | 12 | Jackson 3 required on Boot 4; audit custom JsonFactoryDecorator → MapperBuilderDecorator |
| `io.github.resilience4j:resilience4j-bom` | `2.4.0` | approved | `2.4.0` | MED | 40 | Align with [40-resilience4j-boot4](../phases/40-resilience4j-boot4.md); BOM may omit boot4 |
| `io.github.resilience4j:resilience4j-spring-boot3` | `→ spring-boot4:2.4.0` | migrate | `2.2.0` | MED | 40 | Boot 4 hard-fails on boot3 — phase 40 |
| `io.github.resilience4j:resilience4j-spring-boot4` | `2.4.0` | approved | `2.4.0` | MED | 40 | Pin explicitly until BOM lists boot4 |
| `io.github.resilience4j:resilience4j-circuitbreaker` | `2.4.0` | approved | `2.4.0` | MED | 40 | Align with BOM 2.4.0 via phase 40 |
| `io.github.resilience4j:resilience4j-retry` | `2.4.0` | approved | `2.4.0` | MED | 40 | Align with BOM 2.4.0 via phase 40 |
| `org.springframework.retry:spring-retry` | `drop` | migrate | — | MED | 41 | Boot 4 / Framework 7 — remove; use [41-spring-retry-framework](../phases/41-spring-retry-framework.md) |
| `org.springframework.boot:spring-boot-starter-retry` | `drop` | migrate | — | MED | 41 | Remove with spring-retry; enable `@EnableResilientMethods` |
| `ch.qos.logback:logback-classic` | `Boot BOM` | approved | `1.6.5` | LOW | 01 | Prefer Boot BOM |
| `io.lettuce:lettuce-core` | `Boot BOM` | approved | `7.9.0.RELEASE` | LOW | 01 | Prefer Boot BOM |
| `io.projectreactor.addons:reactor-extra` | `Boot/Reactor BOM` | approved | `3.5.2` | MED | 12 | Align with reactor-core from Boot BOM |

## Kotlin ecosystem

| coordinate | proposedTarget | status | maxStableFound | risk | phase | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `org.jetbrains.kotlin.jvm` | `2.3.21` | approved | `2.3.21` | MED | 31 | Apply via [31-kotlin.md](../phases/31-kotlin.md); Boot **4.1** manages **2.3.21** (JVM **25** bytecode). Boot **4.0** used **2.2.21** (2.2.x caps at JVM **24**). |
| `org.jetbrains.kotlin.plugin.spring` | `same as kotlin.jvm` | approved | `2.3.21` | MED | 31 | Align version with kotlin.jvm — phase 31 |
| `org.jetbrains.kotlin.plugin.jpa` | `same as kotlin.jvm` | approved | `2.3.21` | MED | 31 | Align version with kotlin.jvm — phase 31 |
| `org.jetbrains.kotlinx:kotlinx-coroutines-core` | `Boot Coroutines BOM` | approved | `1.11.0` | MED | 31 | Prefer Boot kotlin-coroutines BOM; phase 31 |
| `org.jetbrains.kotlinx:kotlinx-coroutines-reactor` | `Boot Coroutines BOM` | approved | `1.11.0` | MED | 31 | Prefer Boot BOM; phase 31 |
| `io.github.oshai:kotlin-logging-jvm` | `8.0.4` | approved | `8.0.4` | MED | 12 | Target for microutils migrate; 8.x API cleanup (loggerFactory / lambda-only) |
| `io.github.microutils:kotlin-logging-jvm` | `→ oshai 8.0.4` | migrate | `3.0.5` | MED | 12 | Package moved to io.github.oshai |
| `org.jmailen.kotlinter` | `5.7.0` | approved | `5.7.0` | LOW | 12 |  |
| `com.ncorti.ktfmt.gradle` | `0.27.0` | approved | `0.27.0` | LOW | 12 |  |

## Build plugins & toolchains

| coordinate | proposedTarget | status | maxStableFound | risk | phase | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `com.diffplug.spotless` | `8.10.4` | approved | `8.10.4` | MED | 10 | Gradle 9; indent DSL changes in 7+ |
| `com.google.cloud.tools.jib` | `3.5.4` | approved | `3.5.4` | MED | 12 |  |
| `com.google.protobuf (plugin)` | `0.10.0` | approved | `0.10.0` | MED | 15 |  |
| `org.flywaydb.flyway` | `13.10.3` | approved | `13.10.3` | HIGH | 08 | Same version as `flyway-core` and the vendor module. Do not pin the plugin alone when ahead of the Boot BOM. |
| `org.sonarqube` | `7.5.0.8588` | approved | `7.5.0.8588` | MED | 37 | Task name is `sonar`, not `sonarqube`. Plugin, extension, task, and CI invocation move together in [37-gitlab-ci](../phases/37-gitlab-ci.md). Not a phase-12 bump. |
| `org.openrewrite.rewrite` | `7.4.1+` | approved | `7.4.1+` | MED | 12 | Align with recipe modules; verify portal latest stable |
| `org.openrewrite.recipe:rewrite-spring` | `6.37.1` | approved | `6.37.1` | MED | 12 |  |
| `org.openrewrite.recipe:rewrite-migrate-java` | `3.42.1` | approved | `3.42.1` | MED | 12 |  |
| `com.google.cloud.artifactregistry.gradle-plugin` | `2.2.5` | approved | `2.2.5` | LOW | 12 |  |
| `io.gatling.gradle` | `3.16.0` | approved | `3.16.0` | MED | 12 |  |
| `io.gatling:gatling-core` | `3.16.0` | approved | `3.16.0` | MED | 12 | Align Gatling Gradle plugin |
| `io.freefair.lombok` | `9.8.2` | approved | `9.8.2` | MED | 12 | Tie to Gradle major |
| `com.github.johnrengelman.shadow` | `→ drop or gradleup 9.6.x` | migrate | `8.1.1` | MED | 39 | [39-remove-or-migrate-shadow](../phases/39-remove-or-migrate-shadow.md) — prefer drop; never bump 8.1.1 |
| `com.gradleup.shadow` | `9.6.1` | approved | `9.6.1` | MED | 39 | Keep path only after 39 rejects drop; validate shaded JAR / DSL |
| `org.gradle.toolchains.foojay-resolver-convention` | `1.0.0` | approved | `1.0.0` | LOW | 12 |  |
| `com.avast.gradle.docker-compose` | `0.17.21` | approved | `0.17.21` | LOW | 12 | Upstream archived |
| `com.google.cloud:libraries-bom` | `26.90.0` | approved | `26.90.0` | MED | 12 | Import as BOM only |
| `com.github.java-json-tools:json-schema-validator` | `2.2.14` | approved | `2.2.14` | LOW | 12 | Effectively unmaintained |

## Private artifacts

A coordinate your organization publishes is `status=internal`. Record the owner and the version they publish. Do not invent a Maven Central version for it. Do not open other repositories to find that version.

## Deferred / policy caps (summary)

| Item | Cap | Why |
|------|-----|-----|
| WireMock 4.x | Stay on **3.13.2** (3.x bump **approved**) | 4.x still beta — phase 12 / 16 / anti-patterns |
| MapStruct 1.7 | Stay on **1.6.3** | 1.7 beta |
| Cucumber 8 | **8.0.4** after phase 16 | Not a silent version bump from 7.x |
| Hypersistence `*-60/63` / hibernate-types | Move via phase **03** | Artifact line change |
| javafaker | Migrate via phase **09** | Replace with datafaker |

## Catalog maintenance notes

- Explicit pins only; many Spring starters are unversioned (BOM) and omitted on purpose.
- WireMock may appear only via a Gradle version variable — include when Detect finds WireMock.
- Services already on Boot 4.x plugin still align other explicit pins to this catalog after the platform phase.

## Approval checklist (human)

- [x] Accept `proposedTarget` for **LOW** rows → `approved`
- [x] OpenAPI request validator 3.0 rename (mockmvc + restassured) → `approved`
- [x] Kotest 6.x → `approved` (Kotlin co-migrate)
- [x] Dedicated phases for Tomcat / Testcontainers / RestAssured / MockServer (24–27)
- [ ] Approve applying HIGH catalog rows for phases 24–27 (or approve after first spike)
- [ ] Decide **MED** rows (OkHttp 5, Cucumber 8, LaunchDarkly 7, Spotless 8, etc.)
- [ ] MySQL: stay Boot-managed 9.7.x vs optional ahead-of-BOM 26.7.0 (see verification)
- [ ] Confirm Sonar / Spotless plugin targets vs team standards

## HIGH sensitivity — phases & verification

| Topic | Catalog | Phase | Notes |
|-------|---------|-------|-------|
| Tomcat embed pins | `Boot BOM (remove pin)` | [24-tomcat-boot-managed](../phases/24-tomcat-boot-managed.md) | Decommission pins; WAR → `tomcat-runtime` |
| Testcontainers 2.x | BOM `2.0.5` + module renames | [25-testcontainers-2](../phases/25-testcontainers-2.md) | `postgresql` → `testcontainers-postgresql` |
| Rest Assured 6.x | `6.2.0` explicit pin | [26-rest-assured-6](../phases/26-rest-assured-6.md) | Boot 4 does not manage RA; Jackson 3 + ORV |
| MockServer 9.x | `9.0.0` no-dependencies | [27-mockserver-9](../phases/27-mockserver-9.md) | Drop `:shaded`; fix dual annotations |
| Protobuf 4.36 | `4.36.2` | [15-protobuf-protoc](../phases/15-protobuf-protoc.md) | Existing |
| Flyway 13 | `13.10.3` | [08-flyway-db](../phases/08-flyway-db.md) | Ahead of the Boot BOM: plugin + core + vendor together; production schema history unverified |
| Nimbus JWT 10 | `10.10` | [29-nimbus-jose-jwt-10](../phases/29-nimbus-jose-jwt-10.md) | approved — apply via phase |
| OkHttp 5 | `5.5.0` | [28-okhttp-5](../phases/28-okhttp-5.md) | `must` when legacy `mockwebserver` remains; test artifact is `mockwebserver3` |
| LaunchDarkly 7 | `7.17.3` | [30-launchdarkly-7](../phases/30-launchdarkly-7.md) | approved — apply via phase |
| Kotest 6 | `6.2.6` | **approved** | Co-migrate with [31-kotlin](../phases/31-kotlin.md) |

### MySQL Connector/J — what “unverified” meant & how to verify

**`26.7.0` is real** — Oracle Calendar Versioning (`YY.M.P`, July 2026 GA), not a Solr/Maven glitch.  
**Why we did not default the catalog to it:** Spring Boot 4.x BOM still manages the **9.x** line (e.g. **9.7.0** on Boot 4.1.x). Jumping to 26.7.0 is **ahead-of-BOM**.

**Recommended target:** omit the version (Boot-managed) or pin **`9.7.0`** to match Boot 4.1.x.

**Verification checklist before approving `26.7.0` (or any ahead-of-BOM driver):**

1. **Maven Central** — open `com.mysql:mysql-connector-j:<version>`; confirm group `com.mysql`, packaging `jar`, GA publish date.  
2. **Oracle release notes** — [Connector/J relnotes](https://dev.mysql.com/doc/relnotes/connector-j/en/); note supported **MySQL Server** majors and auth/SSL changes.  
3. **Boot BOM** — check `mysql.version` for your Boot patch; prefer BOM unless Security forces override (`ext['mysql.version']` with expiry).  
4. **Run against the MySQL major this service actually uses** — Flyway/IT/CRUD smoke; fail closed on auth errors.  
5. **SSL / auth defaults** — `sslMode` / `caching_sha2_password` / Cloud SQL proxy path; do not assume `mysql_native_password`.  
6. **CVE scan** on the exact jar; ensure old `mysql:mysql-connector-java` coords are gone.

Until that checklist is done for **26.7.0**, migrate agents should land on **Boot-managed 9.7.x**.

---
