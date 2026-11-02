# 28 — OkHttp 4.x → 5.x

## Detect

Apply when:

- `com.squareup.okhttp3:okhttp` / `logging-interceptor` / `mockwebserver` at **4.9.x / 4.12.x** (or alphas of 5)
- Legacy `com.squareup.okhttp3:mockwebserver` at **5.x** (same artifact id; it still extends JUnit 4 `ExternalResource`)
- Code uses `okhttp3.internal.*`, custom `Dns` / TLS, or `Response.trailers()` peek-by-exception
- Boot 4 present — Boot **does not manage** OkHttp (since 3.4); version must be explicit / BOM

Skip when already on OkHttp BOM **5.5.x** with aligned modules and, when tests mock HTTP, `com.squareup.okhttp3:mockwebserver3` rather than legacy `mockwebserver`.

Catalog target: **5.5.0** ([DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md)).

## Why legacy MockWebServer matters

Legacy `com.squareup.okhttp3:mockwebserver` at 4.x and at 5.5.0 extends `org.junit.rules.ExternalResource`. The published **5.5.0** POM depends on `junit:junit:4.13.2`. Bumping that artifact and deleting a direct `junit:junit` line does not remove JUnit 4. Its presence makes this phase `must` ([PHASE-CATALOG.md](../references/PHASE-CATALOG.md#conditional-priority-the-only-place-these-rules-live)).

Move production OkHttp and the test server together: the Stage A slice swaps both coordinates in the same wave that removes `junit:junit` (phase 36); the Stage B slice moves the test sources. The test coordinate is `com.squareup.okhttp3:mockwebserver3` (BOM-managed, no JUnit dependency). Do not add `mockwebserver3-junit5` on Boot 4: it depends on `junit-jupiter-api` **5.13.4**, and Boot 4 manages JUnit 6. Tests that already call `start` / `close` use `mockwebserver3` alone.

## Before → After

```gradle
// BEFORE
implementation 'com.squareup.okhttp3:okhttp:4.12.0'
testImplementation 'com.squareup.okhttp3:mockwebserver:4.12.0'

// AFTER — Gradle: BOM + facade. mockwebserver3 is in the same BOM.
implementation platform('com.squareup.okhttp3:okhttp-bom:5.5.0')
implementation 'com.squareup.okhttp3:okhttp'
implementation 'com.squareup.okhttp3:logging-interceptor' // if used
testImplementation 'com.squareup.okhttp3:mockwebserver3'
```

```xml
<!-- Maven / no Gradle module metadata: use okhttp-jvm (root okhttp JAR is empty) -->
<dependency>
  <groupId>com.squareup.okhttp3</groupId>
  <artifactId>okhttp-jvm</artifactId>
  <version>5.5.0</version>
</dependency>
```

Typical `OkHttpClient.Builder` / `Request` call sites stay the same. Align Okio if directly pinned.

Test source moves (Stage B slice):

- `okhttp3.mockwebserver.*` → `mockwebserver3.*`
- Java `new MockResponse().setHeader(...).setBody(...).setResponseCode(...)` → `new MockResponse.Builder().addHeader(...).body(...).code(...).build()`
- Kotlin `MockResponse().setBody(x).setResponseCode(n)` → `MockResponse(code = n, body = x)`
- `shutdown()` → `close()`
- `RecordedRequest.path` → `RecordedRequest.target` (the request target, query string included). `url.encodedPath` drops the query.

## What breaks / how to fix

| Symptom | Cause | Fix |
|---------|--------|-----|
| `NoClassDefFoundError` for `OkHttpClient` (Maven) | Depended on empty `okhttp` facade | Use `okhttp-jvm` |
| Mixed 4.x + 5.x on classpath | Partial bump / transitive | Force BOM 5.5.0 everywhere |
| Flaky connect on dual-stack | Happy Eyeballs on by default | Smoke IPv4/IPv6; temp `.fastFallback(false)` + ticket |
| Trailer peek logic broken | `trailers()` now blocks | Use `peekTrailers()` (≥5.1) |
| Compile against `okhttp3.internal` | JPMS / internals not exported | Stop using internals |
| `junit:junit` still resolves after the BOM bump | Legacy `mockwebserver:5.5.0` depends on JUnit 4 | Replace with `mockwebserver3`; keep the phase 36 runtime exclude |
| `recordedRequest.path` or query assertion mismatch | `path` is gone; `url.encodedPath` omits the query | Compare `RecordedRequest.target` |
| Jupiter 5.13.4 vs Boot JUnit 6 | `mockwebserver3-junit5` pins Jupiter 5 | Use `mockwebserver3` only |

## Steps

1. Inventory direct + transitive OkHttp 4.x (Retrofit, Cloud, tests), including legacy `mockwebserver`.
2. Stage A: import `okhttp-bom:5.5.0`; align logging/tls. Gradle: `okhttp`. Maven: `okhttp-jvm`. Replace legacy `mockwebserver` with `mockwebserver3`.
3. Stage B: replace `okhttp3.internal` usage.
4. Stage B: apply the test-source moves above.
5. Dual-stack / trailer smoke if those paths exist.
6. HTTP client and MockWebServer tests are confirmed in the Stage C run.

### MockWebServer and BOM notes

- Legacy `mockwebserver:5.5.0` does **not** drop the JUnit 4 dependency. The JUnit exit is `mockwebserver3`.
- A `resolutionStrategy` force on `com.squareup.okhttp3` to the BOM patch covers Retrofit/GCP transitives when not every module is declared via the platform.
- Micrometer `OkHttpMetricsEventListener` and public `OkHttpClient` / `Request` adapter call sites often need no source edits on **5.5.0**; MockWebServer test sources still need the moves in the table above.

## Do not

- Mix OkHttp 4.x and 5.x.
- Depend on Maven `okhttp` alone.
- Assume Boot BOM manages OkHttp.
- Keep legacy `mockwebserver` at 5.5.0 as the way to delete `junit:junit`.
- Add `mockwebserver3-junit5` or `mockwebserver3-junit4` on Boot 4.
- Silent phase-12 bump when Detect finds internals / custom TLS / dual-stack pain — use this phase.

## Risk

`SPIKE_FIRST` when tests use MockWebServer: the server API changes in the same change as the client.

`SAFE_AUTO` only for a Gradle BOM bump of public client APIs when no mock server, internals, custom TLS, or trailers are present.

`ASK_HUMAN` for Maven coords, Happy Eyeballs flakes, trailers, custom TLS/DNS.

## Rollback

Revert the BOM, the `mockwebserver3` dependency, and the test-source edits together. Restoring legacy `mockwebserver` without `junit:junit` does not compile or run.

## Done when

- Classpath is OkHttp **5.5.0** (one version), including `mockwebserver3` when tests mock HTTP.
- No `com.squareup.okhttp3:mockwebserver` coordinate and no `okhttp3.mockwebserver` import.
- No direct or transitive `junit:junit` on a test runtime classpath.
- The latest compile shows no errors owned by this phase.

## Handoff

`okhttp=5.5.0; bom=yes; mockwebserver=mockwebserver3|n/a; junit4Jar=absent; fastFallback=default|disabled; tests=green|deferred`
