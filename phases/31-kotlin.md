# 31 — Kotlin (Boot 4 + JDK 25)

This phase is **must** when Detect finds Kotlin — not an optional stub.

**Sources:** [Spring Boot Kotlin support](https://docs.spring.io/spring-boot/reference/features/kotlin.html) (Boot 4 requires Kotlin **2.2.x+**); **Boot 4.1** manages Kotlin **2.3.21** and is the JDK **25** train. **Boot 4.0** managed **2.2.21** — Kotlin **2.2.x** bytecode tops out at **JVM 24**, so a **Java 25** migration on **Boot 4.1.x** must use **Kotlin 2.3.x** (prefer the Boot-managed **2.3.21** pin, not 2.3.0). Catalog [DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md).

## Detect

Apply when any of:

- `*.kt` sources
- Gradle: `kotlin("jvm")` / `org.jetbrains.kotlin.jvm`, `kotlin("plugin.spring")`, `kotlin("plugin.jpa")` / `plugin.noarg`, `kotlin("kapt")`
- Maven: `kotlin-maven-plugin`
- Deps: `kotlin-stdlib` / `kotlin-reflect`, `kotlinx-coroutines-*`, Kotest, MockK, SpringMockK, `kotlin-logging*`
- Serialization: `kotlinx.serialization` / `spring-boot-starter-kotlinx-serialization-json`

Skip only for pure-Java services with no Kotlin plugins or `.kt` files.

## Before → After

### Plugin + language level (Gradle Kotlin DSL)

```kotlin
// BEFORE — Kotlin 1.9 / 2.0 / 2.1 on JDK 21
plugins {
    kotlin("jvm") version "1.9.24"
    kotlin("plugin.spring") version "1.9.24"
    kotlin("plugin.jpa") version "1.9.24"
    // optionally: kotlin("kapt") version "1.9.24"
}
tasks.withType<KotlinCompile> {
    kotlinOptions {
        jvmTarget = "21"
        freeCompilerArgs = listOf("-Xjsr305=strict", "-Xjvm-default=all")
    }
}
implementation("org.jetbrains.kotlin:kotlin-stdlib-jdk8")

// AFTER — Boot 4.1 + JDK 25 (align ALL kotlin.* plugins to the same version)
plugins {
    kotlin("jvm") version "2.3.21"
    kotlin("plugin.spring") version "2.3.21"
    kotlin("plugin.jpa") version "2.3.21"   // or plugin.noarg if used that way
    // kotlin("kapt") version "2.3.21"      // if still on kapt
}
java {
    sourceCompatibility = JavaVersion.VERSION_25
    targetCompatibility = JavaVersion.VERSION_25
}
kotlin {
    jvmToolchain(25)
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_25)
        freeCompilerArgs.addAll(
            "-Xjsr305=strict",
            "-Xjvm-default=all",
            // Boot docs: avoid annotation-target warnings; future Kotlin default
            "-Xannotation-default-target=param-property",
        )
    }
}
// Prefer kotlin-stdlib (jdk8 artifact is legacy alias — Boot manages via Kotlin BOM)
implementation("org.jetbrains.kotlin:kotlin-stdlib")
implementation("org.jetbrains.kotlin:kotlin-reflect")
```

When the Spring Boot Gradle plugin is applied, prefer matching the **Boot-managed** Kotlin version (4.1 → **2.3.21**) on every `kotlin.*` plugin — do not leave stdlib on a different train.

### Groovy `build.gradle`

```gradle
plugins {
    id 'org.jetbrains.kotlin.jvm' version '2.3.21'
    id 'org.jetbrains.kotlin.plugin.spring' version '2.3.21'
    id 'org.jetbrains.kotlin.plugin.jpa' version '2.3.21'
}
kotlin {
    jvmToolchain(25)
}
tasks.withType(org.jetbrains.kotlin.gradle.tasks.KotlinCompile).configureEach {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_25)
        freeCompilerArgs.addAll([
            '-Xjsr305=strict',
            '-Xjvm-default=all',
            '-Xannotation-default-target=param-property',
        ])
    }
}
```

Spring Boot Gradle plugin **aligns** `kotlin.version` with the Kotlin plugin version when present — do not leave stdlib on a different train.

### Coroutines

```gradle
// Prefer Boot-managed Coroutines BOM (property kotlin-coroutines.version) — omit versions
implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core")
implementation("org.jetbrains.kotlinx:kotlinx-coroutines-reactor") // WebFlux / Reactor
implementation("org.jetbrains.kotlinx:kotlinx-coroutines-slf4j")
testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test")
```

Catalog floor if you must pin: **1.11.0** — still prefer BOM alignment with Boot **4.1** (Kotlin **2.3.21**).

### Testing stack (co-migrate)

| Library | Catalog / guidance |
|---------|-------------------|
| Kotest | **6.2.6** approved — `kotest-runner-junit5` **and** `kotest-assertions-core` at the same version; boolean matchers in `io.kotest.matchers.booleans` ([09-testing.md](09-testing.md)) |
| MockK | **1.14.11** approved |
| SpringMockK | **4.0.2** — `@MockkBean` / `@SpykBean` (Boot’s MockK analogue to `@MockitoBean`) |
| mockito-kotlin | Prefer `org.mockito.kotlin:6.4.0`; migrate off `com.nhaarman.mockitokotlin2` ([09-testing.md](09-testing.md)) |
| kotlin-logging | Prefer `io.github.oshai:kotlin-logging-jvm` (migrate from `io.github.microutils`) |

Boot recommends MockK + SpringMockK for Kotlin. JUnit 4 → Jupiter is [36-junit-jupiter.md](36-junit-jupiter.md), after this phase (JUnit 6 needs Kotlin 2.1+).

### Jackson 3

Jackson’s Kotlin module must be on the classpath for data classes — Boot auto-registers when found. Coordinate JSON cutover with [04-jackson-3.md](04-jackson-3.md). Do not leave a Jackson 2 Kotlin module while the app is on Jackson 3.

Optional: `spring-boot-starter-kotlinx-serialization-json` — only if the service already uses kotlinx.serialization; coexist carefully with Jackson 3 (ask human before enabling anew).

### Entry point

```kotlin
// Prefer Boot Kotlin idiom
fun main(args: Array<String>) {
    runApplication<MyApplication>(*args)
}
```

## What breaks / how to fix

| Symptom | Cause | Fix |
|---------|--------|-----|
| `Unknown Kotlin JVM target: 25` or `JvmTarget.JVM_25` unresolved on **2.2.x** | Kotlin **2.2.x** emits bytecode only through **24** | On **Boot 4.1** + JDK **25**, bump all Kotlin plugins to **2.3.x** (catalog / Boot: **2.3.21**). Use `JvmTarget.JVM_25` with `jvmToolchain(25)`. Do **not** cap Java/Kotlin at **24** as the end state for a Java **25** contract. |
| `JvmTarget.fromTarget("25")` on **2.2.x** still fails configure (“available targets … 24”) | `fromTarget` does not add JVM **25** to the **2.2** compiler. The script may accept the call; configure still rejects target **25** | Reject `fromTarget("25")` on **2.2.x**. Upgrade every Kotlin plugin to **2.3.x**, then set `JvmTarget.JVM_25`. |
| Boot 4 rejects Kotlin &lt; 2.2 | Hard requirement | Bump all `kotlin.*` plugins to **2.3.21** on Boot **4.1** (or Boot-managed equivalent). Boot **4.0** minimum was **2.2.x**. |
| Annotation / param-target warnings or wrong injection | Kotlin 2.2+ annotation defaulting | Add `-Xannotation-default-target=param-property` |
| Proxy / CGLIB fails on `@Service` / `@Configuration` | Class final by default | Ensure `kotlin("plugin.spring")` (all-open) applied |
| JPA entity / `val` issues | Final / no-arg | Keep `plugin.jpa` / `plugin.noarg`; entities need no-arg ctor story unchanged |
| Nullability compile errors vs Spring APIs | Kotlin 2.1+ strict **JSpecify** | Fix call sites; see [21-null-safety-jspecify.md](21-null-safety-jspecify.md) — do not disable null checks project-wide |
| `jvmTarget` 21/24 with Java 25 contract | Toolchain / compiler skew | Set Kotlin `jvmTarget` **25** and Java **25** with [01-platform-baseline.md](01-platform-baseline.md) on Kotlin **2.3+** |
| Mixed Kotlin plugin versions | jvm 2.3 + jpa 2.2 | **One** version for every Kotlin Gradle plugin |
| Kotest 5 + Kotlin 2.3 oddities | Train skew | Co-bump Kotest to **6.2.6** (approved) |
| `Unresolved reference 'boolean'` / `shouldBeTrue` on Kotest 6 | Wrong import path or missing `kotest-assertions-core` | Add `testImplementation("io.kotest:kotest-assertions-core:6.2.6")` with runner; import `io.kotest.matchers.booleans.shouldBeTrue` / `shouldBeFalse` (not `matchers.boolean` or bare `matchers.shouldBeTrue`) |
| kapt fails on JDK 25 | Old kapt / MapStruct | Align kapt to **2.3.21**; MapStruct **1.6.3** ([17-mapstruct.md](17-mapstruct.md)); consider KSP later (ASK_HUMAN) |
| `kotlin-stdlib-jdk8` resolution noise | Legacy artifact | Switch to `kotlin-stdlib`; Boot BOM manages |
| `KotlinCompile` decoration failure, or `FormattingOptions` unresolved | ktfmt **0.13.x** cannot configure on Kotlin Gradle plugin **2.3**, and ktfmt **0.27.0** drops `com.facebook.ktfmt.format.FormattingOptions` from the script classpath | Move `com.ncorti.ktfmt.gradle` to **0.27.0** in the same Stage A commit as the Kotlin plugin. Replace `FormattingOptions.DEFAULT_MAX_WIDTH` with the literal width |
| Coroutine context lost in tracing | Micrometer / Sleuth leftovers | [07-observability.md](07-observability.md); keep `coroutines-slf4j` / Reactor hooks |
| Serialization module clash | Jackson 2 kotlin + Jackson 3 | Single Jackson major; regenerate / fix DTO tests |

## Steps

1. **Inventory** — Kotlin plugin versions, toolchain/`jvmTarget`, kapt vs KSP, coroutines pins, Kotest/MockK/SpringMockK, serialization.  
2. **Bump Kotlin plugins** to **2.3.21** on Boot **4.1** (all of: jvm, spring, jpa/noarg, kapt, lombok-plugin if used) in one commit with JDK **25** toolchain and **`JvmTarget.JVM_25`**. In that same commit, move `com.ncorti.ktfmt.gradle` to **0.27.0** when the build uses it, and replace `FormattingOptions.DEFAULT_MAX_WIDTH` with a literal width. Do not “fix” a **2.2.x** script with `JvmTarget.fromTarget("25")`.  
3. Add **`-Xannotation-default-target=param-property`**; keep `-Xjsr305=strict` / `-Xjvm-default=all` unless the team standard differs.  
4. Align stdlib/reflect with Boot Kotlin BOM (drop conflicting direct pins).  
5. Align coroutines with Boot Coroutines BOM (remove stale `1.7.x` / `1.8.x` test pins).  
6. Co-migrate tests: Kotest **6.2.6**, MockK catalog target, SpringMockK; mockito-kotlin2 → `org.mockito.kotlin` if present.  
7. Fix JSpecify / nullability compile breaks at Framework boundaries ([21](21-null-safety-jspecify.md)).  
8. Confirm Jackson Kotlin module path with [04](04-jackson-3.md); do not introduce kotlinx.serialization without human OK.  
9. If MapStruct + kapt: bump processor/SPI with [17](17-mapstruct.md).  
10. Compile via the orchestrator; unit and IT outcomes are judged in Stage C against the baseline.

## Coordination with other phases

| Concern | Phase |
|---------|--------|
| Java 25 / Boot 4 plugins | [01-platform-baseline.md](01-platform-baseline.md) — do this first or with Kotlin bump |
| Jackson 3 / JsonMapper | [04-jackson-3.md](04-jackson-3.md) |
| JSpecify / NullAway | [21-null-safety-jspecify.md](21-null-safety-jspecify.md) |
| JUnit 4 removal | [36-junit-jupiter.md](36-junit-jupiter.md) — after this phase |
| Test starters / `@MockitoBean` | [09-testing.md](09-testing.md) |
| MapStruct + kapt | [17-mapstruct.md](17-mapstruct.md) |
| WebFlux codecs / Reactor Netty | [35-webflux.md](35-webflux.md) |
| LaunchDarkly `LDContext` | [30-launchdarkly-7.md](30-launchdarkly-7.md) |
| OkHttp 5 (often with Retrofit/Kotlin) | [28-okhttp-5.md](28-okhttp-5.md) |
| Pin versions | [DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md) |

## Do not

- Claim Boot **4.1** + JDK **25** migration complete on Kotlin **2.2.x** (bytecode cap **24**).  
- Use `JvmTarget.fromTarget("25")` on Kotlin **2.2.x**. Available targets still stop at **24**.  
- Cap `jvmTarget` / Java compatibility at **24** as the permanent fix on a **Java 25** contract — upgrade to **2.3.x** instead.  
- Write handoff `jvmTarget=25` while plugins are still **2.2.x**. The handoff reports **compiler capability**, not the contract you wanted.  
- Treat a DSL line `jvmTarget.set(JvmTarget.JVM_25)` on Kotlin **2.2.x** as Done-when. A verifier must REWORK that claim; the enum in the script is not compiler capability.  
- Mix Kotlin plugin versions across jvm / spring / jpa / kapt.  
- Leave `jvmTarget` on 17/21 while Java is 25.  
- Disable JSpecify / nullness globally to silence errors.  
- One-step Kotest 6 without Kotlin 2.3 (or the reverse) when both are far behind.  
- Add kotlinx.serialization as a “while we’re here” Jackson replacement.  
- Open sibling services for “how they did Kotlin” during migrate — use this phase + catalog.  
- Treat this as a silent phase-12 version bump when compiler flags / kapt / Kotest are involved.

## Risk

`ASK_HUMAN` when the bump crosses kapt/MapStruct, nullability cascades, Kotest 6, or a 2.2 → 2.3 compiler delta.  
`SAFE_AUTO` only when already on Kotlin **2.3.x** + JDK **25** toolchain/`JVM_25` and this phase is a patch align (e.g. 2.3.0 → 2.3.21) with no test-framework majors.  
`SPIKE_FIRST` for KSP migration, multiplatform, or first kotlinx.serialization + Jackson 3 coexistence.

## Rollback

Revert Kotlin plugin versions, toolchain/`jvmTarget`, compiler args, and co-bumped Kotest/coroutines pins in one commit (or revert MR). No data migration.

## Done when

- All Kotlin Gradle/Maven plugins on **2.3.21** (or Boot **4.1**-aligned **2.3.x**) when the target is JDK **25**  
- `jvmTarget` / toolchain **25** with Boot 4.1, set as `JvmTarget.JVM_25` on **2.3.x** — not `fromTarget("25")` on **2.2.x**  
- Handoff `compilerCapability` matches the applied plugin train (**2.3.x** → `jvm25`; **2.2.x** → `jvm24`, and this phase is **not** done for a Java **25** contract)  
- `-Xannotation-default-target=param-property` present (or documented team exception)  
- Coroutines / Kotest / MockK aligned per catalog or Boot BOM  
- Human compile (+ agreed tests) recorded green or deferred with reason  

## Handoff

`kotlin=<pluginVer>; jvmTarget=<25|unsupported>; compilerCapability=jvm25|jvm24|unknown; annotationDefaultTarget=param-property|exception; kapt=yes|no; kotest=6.2.6|n/a|deferred; coroutines=bom|pinned; compile=green|deferred`

`compilerCapability=jvm25` only when the applied compiler can emit JVM **25** (Kotlin **2.3.x** with `JvmTarget.JVM_25`). On **2.2.x**, emit `compilerCapability=jvm24` and `jvmTarget=unsupported` even if the migration contract says Java **25**.
