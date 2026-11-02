# 16 — Cucumber 7 → 8 (+ WireMock 3 align; WireMock 4 deferred)

## Detect

`io.cucumber:cucumber-java` / `cucumber-spring` / `cucumber-junit-platform-engine`, feature files, glue packages, and often WireMock (`org.wiremock:wiremock`, `org.wiremock:wiremock-standalone`, docker `wiremock/wiremock`, CI `wiremock.Run`). Skip if no Cucumber suite.

`io.cucumber:cucumber-junit` and `@RunWith(Cucumber.class)` are JUnit 4. [36-junit-jupiter.md](36-junit-jupiter.md) switches them to `cucumber-junit-platform-engine` on the current Cucumber line before this phase bumps to 8.

**WireMock-free suites:** If intake finds **no** `org.wiremock` dependency, `wiremock.Run`, or docker `wiremock/wiremock` (only **OkHttp MockWebServer** in step defs), skip the WireMock alignment checklist and `copyWireMockStandalone` — do not add WireMock solely to satisfy this phase.

## Goal

Land **Cucumber-JVM 8** so the suite **looks like Cucumber 8**, not Cucumber 5/7 glue that merely resolves on 8.x jars. Align WireMock on latest **stable 3.x**. **Do not** take WireMock **4.x** while it remains beta unless the human explicitly accepts beta.

## Before → After

### Dependencies

```gradle
// BEFORE
def cucumberVersion = "7.x"
integrationTestImplementation "io.cucumber:cucumber-java:${cucumberVersion}"
integrationTestImplementation "io.cucumber:cucumber-java8:${cucumberVersion}" // often unused
integrationTestImplementation "io.cucumber:cucumber-junit-platform-engine:${cucumberVersion}"
integrationTestImplementation "io.cucumber:cucumber-spring:${cucumberVersion}"
integrationTestImplementation "org.wiremock:wiremock:3.7.x" // or wiremock-standalone; client ahead of CI/docker
// often paired with forced com.fasterxml.jackson.*:2.x under Boot 2.7

// AFTER
def cucumberVersion = "8.0.x" // e.g. 8.0.4
integrationTestImplementation "io.cucumber:cucumber-java:${cucumberVersion}"
// no cucumber-java8
integrationTestImplementation "io.cucumber:cucumber-junit-platform-engine:${cucumberVersion}"
integrationTestImplementation "io.cucumber:cucumber-spring:${cucumberVersion}"
// Cucumber 8 formatters (html/usage) — Jackson is opt-in; prefer Jackson 3 if the app is on 3
integrationTestImplementation 'tools.jackson.core:jackson-databind'
// Prefer standalone when CI runs `wiremock.Run` from a copied JAR
integrationTestImplementation "org.wiremock:wiremock-standalone:3.13.x" // latest stable 3.x
// remove Jackson 2 force-overrides that existed only for plain wiremock
```

### Gradle task isolation

```gradle
tasks.register('cucumberTest', Test) {
  description = 'Cucumber suite'
  group = 'verification'
  testClassesDirs = sourceSets.integrationTest.output.classesDirs
  classpath = sourceSets.integrationTest.runtimeClasspath
  useJUnitPlatform()
  filter { includeTestsMatching '*CucumberRunner' }
  maxParallelForks = 1
  shouldRunAfter test
  // reports under build/test-results/cucumberTest (or project convention)
}
// unit `test` filtered to *UnitTest (or exclude *CucumberRunner)
// integrationTest may share sourceSets.test.output for shared TestConfig / helpers
// JaCoCo on unit tests only is fine — do not require Cucumber for coverage gates
```

### Runner / glue (Cucumber 8 idioms)

```java
// BEFORE — broad package select; unnamed hooks; static WireMock client init
@Suite
@IncludeEngines("cucumber")
@SelectPackages("com.example")           // scans too much
@SelectClasspathResource("features")
public class CucumberRunner {}

static { WireMock.configureFor(8484); }
@Before public void resetWireMock() { … }

// AFTER
@Suite
@IncludeEngines("cucumber")
@SelectClasspathResource("features")
@ConfigurationParameter(key = GLUE_PROPERTY_NAME, value = "com.example")
@ConfigurationParameter(
    key = "cucumber.glue.included-class-name-pattern",
    value = ".*(CucumberContext|TestConfig|.*StepDefinition|.*Hook|CustomType)")
public class CucumberRunner {} // suite class stays public for JUnit discovery

@BeforeAll(name = "configureWireMockClient")
static void configureWireMockClient() {
  WireMock.configureFor(WIREMOCK_PORT);
}
@Before(name = "resetWireMock")
void resetWireMock() { … }
```

Also: package-private step/hook/type classes are fine with `cucumber-spring`; keep `@CucumberContextConfiguration` discoverable.

**Suite class vs glue package:** The JUnit Platform `@Suite` entry (e.g. `CucumberConfiguration`) may live under `com.example.config` while `GLUE_PROPERTY_NAME` stays `stepDefinitions`. That is valid — do not move the suite into the glue package unless glue discovery fails.

**Glue class names:** When glue is only `stepDefinitions`, add `cucumber.glue.included-class-name-pattern` such as `.*(StepDefinition|Definition|Feature|Hook).*` so classes like `StoreFlipDefinition` and `GetByBarcodeFeature` are included without widening `@SelectPackages` to the whole app.

**Legacy Gradle plugins:** `se.thinkcode.cucumber-runner` may remain applied; the real entry point is `@Suite` + `cucumber-junit-platform-engine`. Record in handoff whether the thinkcode plugin is redundant or still required for a custom task — do not assume removal without a compile/task graph check.

**CI:** If the pipeline runs `gradle -x test`, bumping Cucumber does not prove BDD in CI until a job runs `./gradlew cucumberTest` (or `test` + `cucumberTest`) with emulators/DB up. Call that out in handoff.

**Resolution strategy:** Pin only the **three** first-party modules you declare (`cucumber-java`, `cucumber-spring`, `cucumber-junit-platform-engine`) to the same **8.0.x** patch. **Do not** `resolutionStrategy.force` the entire `io.cucumber` group to that version — transitives such as `messages`, `gherkin`, and `tag-expressions` use **their own** release lines (e.g. not `8.0.4` on Central). A group-wide force breaks `testCompileProtoPath` / `extractIncludeTestProto` with “Could not find io.cucumber:messages:8.0.4”.

Parameter / DocString transformers that used Jackson 2 `ObjectMapper` should take Boot’s `JsonMapper` (`convertValue` / `constructType` / `readValue` with `tools.jackson` types).

Scenario hooks: named `@Before` for WireMock reset; if the suite shares a messaging emulator, drain/clear captures before DB cleanup when races appear.

### WireMock 3.x alignment (required); 4.x deferred

Align **Gradle client**, **CI process**, and **docker image** to the **same** 3.x patch.

CI images often lack `curl`. Resolve the standalone JAR via Gradle instead:

```gradle
tasks.register('copyWireMockStandalone') {
  doLast {
    def jar = configurations.integrationTestRuntimeClasspath.files.find {
      it.name.startsWith('wiremock-standalone-') && it.name.endsWith('.jar')
    }
    // copy to wiremock-standalone-ci.jar (gitignore this output)
  }
}
```

```yaml
# CI — separate job from unit tests; ensure java is on PATH when the image only sets JAVA_HOME
- export PATH="${JAVA_HOME}/bin:${PATH}"
- ./gradlew copyWireMockStandalone --no-daemon
- java -cp "wiremock-standalone-ci.jar:…/wiremock-faker-extension-….jar" wiremock.Run --port 8484 …
- ./gradlew cucumberTest --no-daemon
# gitignore wiremock-standalone-ci.jar — do not commit it
# unit job: ./gradlew test -x cucumberTest (or equivalent)
```

```yaml
# docker-compose
image: wiremock/wiremock:3.13.x   # same patch as Gradle
```

**WireMock 4:** park until GA (immutable domain types / `transform`, modular artifacts, Jetty 12.1) — separate spike.

## Steps

1. Spike: confirm Cucumber 8.0.x patch; confirm WireMock latest **3.x** (not 4 beta).  
2. Bump Cucumber modules; **remove** `cucumber-java8`; add Jackson for formatters if using html/usage.  
3. Apply glue/runner/hook idioms (named hooks, `@BeforeAll` for WireMock client, include-class pattern).  
4. Align WireMock 3.x on Gradle + docker + CI (`copyWireMockStandalone` if no curl).  
5. Compile integration tests; run `cucumberTest` with WireMock process up.  
6. Separate commits: Cucumber idioms vs WireMock process align preferred.

## Modernization checklist (Definition of Done)

```text
[ ] No io.cucumber:cucumber-java8
[ ] Cucumber modules == 8.0.x
[ ] WireMock on wiremock-standalone (if CI uses wiremock.Run); Gradle == CI == docker == same 3.x (not 4.x beta)
[ ] No Jackson 2 force-pins left “for WireMock”
[ ] Glue discovery narrowed (include pattern / explicit glue)
[ ] Hooks named; configureFor not in static {}
[ ] Package-private glue where Spring allows
[ ] Formatter / transformers on JsonMapper (Jackson 3 if app is on 3)
[ ] cucumberTest isolated (maxParallelForks=1; separate CI job); CI jar gitignored
[ ] cucumberTest green
```

## Do not

- Call the phase done on a version-only bump.
- Leave `io.cucumber:cucumber-junit` (the JUnit 4 runner) in place. That removal is [36-junit-jupiter.md](36-junit-jupiter.md).  
- Introduce WireMock 4 while beta without human OK.  
- Download the standalone JAR with `curl` on images that do not ship curl.  
- Leave client on 3.13.x and CI/docker on 3.7.x.  
- Stay on `org.wiremock:wiremock` while CI expects the standalone JAR.  
- Commit `wiremock-standalone-ci.jar`.  
- Run Cucumber in the same parallel Test JVM / CI job as unit tests that share DB/WireMock/emulator.

## Risk

| Change | Risk |
|--------|------|
| Cucumber 8 + idioms | `ASK_HUMAN` first time; then compile + cucumber smoke |
| WireMock 3.x align | `SAFE_AUTO` after process starts |
| WireMock 4.x | `SPIKE_FIRST` / **deferred** while beta |

## Rollback

Revert Cucumber to 7.x (still omit java8 if unused); restore prior WireMock 3.x tags/CI script.

## Done when

Checklist above is complete; WireMock remains on stable 3.x.

## Handoff

`cucumber=8.0.x; java8=removed; wiremock=3.x-aligned|4-deferred; cucumberTest=green|fail`
