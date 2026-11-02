# Stub — Maven builds

> **Status:** partially filled. Gradle remains the primary worked example in phase docs; map each phase’s Gradle snippet to Maven plugins here.

## Detect

`pom.xml` present; no Gradle wrapper required.

## Skeleton steps

1. Bump `spring-boot-starter-parent` or imported `spring-boot-dependencies` to 4.x.  
2. Set `maven.compiler.release` / toolchain to **25**.  
3. Align Spring Cloud BOM to **2025.1.x** (Boot 4) — not 2025.0 ([01-platform-baseline.md](../phases/01-platform-baseline.md)).  
4. Add temporary `spring-boot-properties-migrator` (runtime) then remove ([18-config-properties.md](../phases/18-config-properties.md)).  
5. Map modular starters / classic bridge ([19-modular-starters.md](../phases/19-modular-starters.md)).  
6. Plugin equivalents:
   - OpenAPI → `openapi-generator-maven-plugin` (`useSpringBoot4`, `useJackson3`)  
   - Spotless → `spotless-maven-plugin` (indent DSL may differ — confirm Spotless 7 Maven docs)  
   - Protobuf → `protobuf-maven-plugin`  
   - Surefire/Failsafe — JUnit Platform provider on **3.x**. JUnit 6 does not run on Surefire 2. Delete a 2.x pin and use the Boot parent. Remove `junit:junit`, Vintage, and `surefire-junit47` ([36-junit-jupiter.md](../phases/36-junit-jupiter.md)). Re-check forks for Cucumber isolation ([16-cucumber-8.md](../phases/16-cucumber-8.md))  
7. Packaging: optional deps excluded from uber jar; classic loader removed; WAR may need `tomcat-runtime`.  
8. Same Jackson 3 / Hibernate 7 / Jakarta / Security rules as the main phase docs.

## Open questions for a future fill-in pass

- Recommended compiler plugin + toolchain XML snippet for JDK 25  
- Surefire/Failsafe flags commonly needed on Boot 4  
- How `spring-boot-maven-plugin` repackage differs (if at all) on 4.x  
- Maven twin for Gradle `copyWireMockStandalone`  

## Handoff

`mavenStub=used|skipped`
