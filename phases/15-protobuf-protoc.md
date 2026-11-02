# 15 — Protobuf Gradle/Maven plugin + protoc 4.x alignment

## Detect

`com.google.protobuf` Gradle plugin / `protobuf-maven-plugin`, a `protobuf { protoc { artifact = … } }` (or Maven protoc version), `.proto` sources, and/or generated Java under `generated/.../proto`. Search `src/main/proto/**` and included proto Gradle/Maven projects — “no `*.proto` under `src/main/java`” is not absent codegen. Also detect transitive `protobuf-java` (often from Google Cloud / gRPC) that may lag the compiler.

**Also detect (even when codegen is “done”):** an explicit `protobuf-java` / `protoc` pin still on **3.25.x** (or any 3.x) while **Spring Cloud GCP 8.x** / Pub/Sub clients are on the classpath. Match a **3.x value**, not the property name `protobufVersion`. A property named `protobufVersion` whose value is **4.x** is not a 3.x pin. Search Gradle scripts, version catalogs, `gradle.properties`, and Maven POMs:

```bash
rg -n -g '*.gradle*' -g '*.toml' -g 'gradle.properties' -g 'pom.xml' \
  -e 'protoc[^#\n]{0,80}[=:][[:space:]]*["'\'']?3\.' \
  -e 'protobuf(-java)?[^#\n]{0,80}[=:][[:space:]]*["'\'']?3\.' \
  -e 'protoc:3\.' \
  -e 'protobuf-java:3\.'
```

**Runtime symptom after GCP 8 without phase 15:** Spring context fails creating `topicAdminClient` / `pubSubAdmin` with `NoClassDefFoundError: com/google/protobuf/RuntimeVersion$RuntimeDomain` — gencode and Pub/Sub stubs expect **protobuf-java 4.x**; a leftover **direct 3.x** pin wins resolution until aligned.

**Priority:** Spring Cloud GCP **8** (or `spring-cloud-gcp-starter-pubsub`) **and** protobuf codegen or a direct `protoc` / `protobuf-java` **3.x** pin makes this phase `must` ([PHASE-CATALOG.md](../references/PHASE-CATALOG.md#conditional-priority-the-only-place-these-rules-live)). Its Stage A slice bumps the pin in the same wave as phase 34's GCP 8 BOM, so the classpath never mixes protobuf 3.x gencode with 4.x runtime. Do not defer it because codegen looks finished. A green local context load is not production proof.

Skip only when the service has **no** protobuf codegen **and** no GCP/gRPC stack that pulls protobuf 4 gencode at runtime. Subscriber lease, JSON conversion, and the health contributor are [43-pubsub.md](43-pubsub.md).

## Before → After

Treat **plugin bump** and **protoc major** as separate changes.

### A) Protobuf Gradle plugin (low risk)

```gradle
// BEFORE
id 'com.google.protobuf' version '0.9.x'

// AFTER
id 'com.google.protobuf' version '0.10.x'
```

Keep `protoc` artifact unchanged in this commit.

### B) protoc 3.21.x → 4.x + matching protobuf-java (high risk — spike)

```gradle
// BEFORE — common lagging pin
protobuf {
  protoc {
    artifact = "com.google.protobuf:protoc:3.21.x"
  }
}
// Runtime may already be protobuf-java 4.33.x via Cloud GCP / gRPC — compiler/runtime skew

// AFTER — same 4.x.y for compiler and Java runtime
protobuf {
  protoc {
    artifact = "com.google.protobuf:protoc:4.36.x" // use current stable 4.x patch
  }
}
implementation 'com.google.protobuf:protobuf-java:4.36.x'
implementation 'com.google.protobuf:protobuf-java-util:4.36.x' // if JsonFormat / Struct helpers are used
```

Version rule (protobuf.dev): language runtimes share `minor.point` with a language-specific major — e.g. protoc **4.36.2** pairs with Java **`protobuf-java:4.36.2`**. Prefer exact match; do not leave GCP’s older transitive 4.33.x after bumping protoc to 4.36.x.

### Guarded same-major runtime alignment

Use a force only to keep group `com.google.protobuf` on the **one** catalog patch already chosen for `protoc` and direct `protobuf-java` (± util). Same-major skew (catalog **4.x.y** vs an older transitive **4.x**) is this path. A direct **3.x** pin is not same-major alignment — it is the **3 → 4** spike below, still scheduled before tests when GCP **8** is present.

```gradle
configurations.configureEach {
    resolutionStrategy.eachDependency { details ->
        if (details.requested.group == 'com.google.protobuf') {
            details.useVersion(protobufVersion) // same patch as protoc
            details.because('Align protobuf compiler and runtime to one patch')
        }
    }
}
```

Guards:

- Force only `com.google.protobuf`, only to that approved patch.  
- Set `protoc`, `protobuf-java`, and util (if used) to the same patch in the same commit as the force.  
- Do not force a different major than the compiler.  
- Do not treat a local `ApplicationContext` load as production Pub/Sub proof. Record it unverified until the human test gate.

### Generated code shape

| Era | Typical base |
|-----|----------------|
| Older protoc 3.x gencode | `GeneratedMessageV3` |
| protoc 4.x / Java 4.36 gencode | `GeneratedMessage` (+ runtime version validation) |

First-party code that only uses builders/getters/parsers usually needs **no** source edits. Grep for `GeneratedMessageV3` before the bump if anything extends or casts to it.

### protoc-gen-doc

`io.github.pseudomuto:protoc-gen-doc` (e.g. 1.5.1) is acceptable for **proto3** HTML/markdown docs. It does **not** reliably support protobuf **editions**. Keep proto3; do not block the protoc 4 bump solely on editions support.

### CI / OS note

`protoc` from Maven is a native binary (glibc). Alpine/musl CI images often fail `generateProto`; prefer a glibc-based (e.g. Debian) JDK image when the build runs protoc every job.

## Steps

1. Inventory: plugin version, `protoc` artifact, `protobuf-java` / `protobuf-java-util` on `compileClasspath` (who pulls them).  
2. Commit 1 (optional): bump protobuf **plugin** only; smoke generate + compile.  
3. Spike: confirm target `4.x.y` for both `protoc` and `protobuf-java` (+ util if needed).  
4. Commit 2: bump `protoc` + pin matching Java artifacts. On a **same-major** align, add the guarded `com.google.protobuf` force in that commit. A direct **3.x** pin moves to the catalog **4.x.y** in this commit as well — that major change stays `SPIKE_FIRST`.  
5. Smoke `generateProto` / `compileJava` (and tests that touch generated types if cheap).  
6. Confirm no accidental dual major of `protobuf-java` on the runtime classpath (`./gradlew dependencies --configuration runtimeClasspath | rg protobuf-java` or equivalent).
7. After a **3 → 4** compiler bump, the orchestrator's compile run includes `generateProto`; Stage C's context run then loads the full context. Context load checks the `RuntimeVersion` gap only. It does not prove production messaging.

## Do not

- Bump `protoc` 3 → 4 without aligning `protobuf-java` (± util) to the same `4.x.y`.  
- Force `com.google.protobuf` to a patch other than the `protoc` pin, or force any other group under this rule.  
- Call a same-major force a **3 → 4** migration, or skip the pre-test schedule when GCP **8** still sees a direct **3.x** pin.  
- Mix plugin-only and protoc-major in one mega-commit.  
- Assume `protoc-gen-doc` supports editions.  
- Run protoc on Alpine without verifying glibc compatibility.  
- Report production behavior from a local context load or generate/compile smoke.

## Risk

| Change | Risk |
|--------|------|
| protobuf plugin 0.9 → 0.10 | `SAFE_AUTO` |
| Same-major runtime align + guarded force onto the catalog patch already set on `protoc` | `SAFE_AUTO` when the guards above hold |
| Direct **3.x** → catalog **4.x** (`protoc` + `protobuf-java` + force), including GCP **8** scheduled before tests | `SPIKE_FIRST`. The plan item is also `priority: must` and `dependsOn: [34-spring-cloud-gcp]` |

## Rollback

Revert `protoc` / `protobuf-java` pins, the `com.google.protobuf` force, and the plugin version; regenerate; restore prior generated sources if checked in (prefer regenerate).

## Done when

Plugin at intended version; if protoc 4.x is adopted, compiler and `protobuf-java` share the same `4.x.y`, the guarded force (when used) matches that patch, and generate + compile succeed. GCP **8** + a former direct **3.x** pin is not left for test triage. Production Pub/Sub behavior stays **not claimed**.

## Handoff

`protobuf_plugin=<ver>; protoc=<kept|4.x.y>; protobuf_java=<aligned|skew>; force=guarded-same-patch|n/a; gcp8Direct3x=scheduled-before-tests|n/a; generate=ok|fail; production=not-claimed`
