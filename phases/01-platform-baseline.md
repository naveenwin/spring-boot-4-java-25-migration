# 01 — Platform baseline (Java 25, Boot 4, build)

## Detect

Always applicable for this migration.

Optional signals:

- `io.spring.dependency-management` plugin version lagging Boot
- Included / composite builds still on toolchain Java 11/17
- SonarQube Gradle plugin majors that fail on Gradle 9 / JDK 25 (CI-local — note only)

## Before → After

| Before | After |
|--------|--------|
| `sourceCompatibility = 17` / `21` / `11` (target often omitted) | `sourceCompatibility` **and** `targetCompatibility` = `JavaVersion.VERSION_25` (or toolchain / `--release` 25) |
| `org.springframework.boot` `3.x` | Boot `4.x` (use team’s approved patch, e.g. 4.1.x) |
| Spring Cloud BOM for Boot 3 | Cloud train compatible with Boot 4 (e.g. `2025.1.x`) |
| Spring Cloud GCP / other Cloud BOM for Boot 3 | Boot 4–compatible GCP `8.x`; run [34-spring-cloud-gcp.md](34-spring-cloud-gcp.md) when detected, and [43-pubsub.md](43-pubsub.md) when Pub/Sub is detected |
| Gradle 8.x (example `8.7`) | Gradle **9.x** when required by Boot 4 plugin (example `9.7.x`) |
| `dependency-management` plugin for Boot 3 | Bump alongside Boot (example `1.1.7` class — match Boot docs) |
| Included build toolchain `languageVersion = 11` | Same Java **25** as root (`sourceCompatibility` / `targetCompatibility` or toolchain 25) |
| CI job image, Dockerfile, Jib base image | Leave them unchanged. This pack does not set image names. |
| Kotlin plugins on **2.2.x** or older, target Boot **4.1** + Java **25** | Same wave: [31-kotlin.md](31-kotlin.md) Kotlin **2.3.x** (Boot-managed **2.3.21**) |
| Undertow embedded | **Unsupported** on Boot 4 servlet stack — move to Tomcat/Jetty |
| WAR + embedded Tomcat | May need `spring-boot-starter-tomcat-runtime` |
| Classic loader / executable launch scripts | Removed or replaced — follow Boot 4 packaging notes |
| DevTools live reload on by default | Live reload **off** by default on Boot 4 |

### Spring Cloud train (do not confuse)

| Train | Boot line |
|-------|-----------|
| **2025.1.x** (e.g. Oakwood) | Boot **4.x** |
| **2025.0.x** (e.g. Northfields) | Boot **3.5.x** only — not a Boot 4 target |

Prefer landing on a current **3.5.x** before 4.0 when the official guide recommends it (clear Boot 3 deprecations first); then jump to Boot 4 + Cloud **2025.1.x**.

Boot 4 baseline: Spring Framework **7**, Jakarta EE **11**, Servlet **6.1** (Undertow removed).

This phase's build edits are the first commit of the Stage A dependency wave. Schedule [37-gitlab-ci.md](37-gitlab-ci.md) when the legacy Sonar Gradle names are still in use. Do not edit CI or runtime images. When Kotlin sources or Kotlin Gradle plugins are present and the target is Boot **4.1** + Java **25**, [31-kotlin.md](31-kotlin.md)'s A slice bumps Kotlin to **2.3.21** (Boot-managed) in the same wave. Kotlin **2.2.x** cannot emit JVM **25** bytecode; leaving it in place does not finish the Java **25** contract. [04-jackson-3.md](04-jackson-3.md), [18-config-properties.md](18-config-properties.md), and [19-modular-starters.md](19-modular-starters.md) follow in the wave and in Stage B order. If GCP is detected, schedule [34-spring-cloud-gcp.md](34-spring-cloud-gcp.md); if Pub/Sub is detected, schedule [43-pubsub.md](43-pubsub.md) as well. If the service pins `tomcat-embed-*`, schedule [24-tomcat-boot-managed.md](24-tomcat-boot-managed.md). The agent build JDK is `JAVA_HOME` on the pinned command. Do not edit CI or container images.

## Steps

1. Bump Java language level to **25** (source **and** target, or toolchain/`release`).  
2. Bump Spring Boot plugin / parent to **4.x** (from latest 3.5.x when practical). On Boot **4.1** + Java **25** with Kotlin detected, [31-kotlin.md](31-kotlin.md)'s A slice in this wave moves Kotlin to **2.3.21** — do not park the compiler bump on a **2.2.x** pin.  
3. Align Spring Cloud to **2025.1.x** (Boot 4) — never leave Cloud on 2025.0 while claiming Boot 4. Align the GCP BOM to the catalog 8.x target, then route GCP code/config/bootstrap work to phase 34.
4. Bump `io.spring.dependency-management` (Gradle) with the Boot line when present.  
5. Upgrade Gradle wrapper to a 9.x supported by the Boot plugin (Gradle builds).  
6. Align included/composite modules to Java 25 (do not leave toolchain 11).  
7. Replace Undertow; fix WAR/`tomcat-runtime` and packaging loader changes if used.  
8. Leave CI job images, Dockerfiles, and Jib base images unchanged. The agent build uses `JAVA_HOME` on the pinned command.  
9. Fix resolve failures attributed to this phase's commit (missing artifacts renamed in Boot 4). Compile errors are expected at this point and belong to Stage B.  
10. SonarQube Gradle plugin: if the legacy `sonarqube` names are still present, schedule [37-gitlab-ci.md](37-gitlab-ci.md) (extension, task, and CI rename together). Do not bump the plugin alone here.  
11. Schedule config migrator + modular starters phases next.

### Maven ([stubs/maven.md](../stubs/maven.md))

- Prefer `spring-boot-starter-parent` 4.x or import `spring-boot-dependencies` BOM.  
- Set compiler release 25.

## Do not

- Leave the service compiling on 21 while claiming “Java 25 migration complete.”  
- Treat Boot **4.1** + Java **25** as done while Kotlin plugins remain on **2.2.x**.  
- Pair Boot 4 with Spring Cloud **2025.0.x**.  
- Leave `includeBuild` / SPI modules on an older Java toolchain.  
- Keep Undertow on Boot 4.

## Risk

`SAFE_AUTO` for version bumps; `ASK_HUMAN` for CI/runtime image names if not already specified.

## Rollback

Revert build plugin versions + wrapper + BOM properties in one commit.

## Done when

Build definition shows Boot 4.x + Java 25; the wave's resolve run configures and shows no resolve failures attributed to this phase; included builds match Java 25 when present. When Kotlin is present on Boot **4.1** + Java **25**, phase 31's A slice in the same wave is at Kotlin **2.3.21**. Class-version compile errors (owner `01-platform-baseline`) are this phase's Stage B work.

## Handoff

`Boot=<version>; Java=25; BuildTool=<gradle|maven>; dependencyManagement=<ver|n/a>; kotlinWave=31-2.3.x|n/a; evaluates=yes|no`
