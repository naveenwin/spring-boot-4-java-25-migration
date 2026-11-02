# 27 — MockServer 5.x → 9.x

## Detect

Apply when:

- `org.mock-server:mockserver-junit-jupiter` / `mockserver-netty` / `mockserver-client-java` at **5.14–5.15.x**
- Optional `classifier: 'shaded'`
- `@ExtendWith(MockServerExtension.class)` and/or `@MockServerSettings`
- `ClientAndServer` / `MockServerClient` usage in tests
- JUnit 4 `org.mockserver.junit.MockServerRule` — [36-junit-jupiter.md](36-junit-jupiter.md) moves it to this major’s `mockserver-junit-jupiter` before the 9.x bump. If the rule is still present, finish 36 first.

Skip when already on `*-no-dependencies:9.0.x`.

Catalog target: **9.0.0** via [DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md).  
Requires **Java 17+** (satisfied by Java 25 migration).

## Before → After

```gradle
// BEFORE (5.15.x)
testImplementation 'org.mock-server:mockserver-junit-jupiter:5.15.0'
// or: mockserver-netty:5.15.0:shaded

// AFTER (9.x) — preferred coords
testImplementation 'org.mock-server:mockserver-junit-jupiter-no-dependencies:9.0.0'
// or: mockserver-netty-no-dependencies:9.0.0
// Optional: platform('org.mock-server:mockserver-bom:9.0.0')
```

```java
// BEFORE — dual annotation (risky in 9.x: double start / port clash)
@ExtendWith(MockServerExtension.class)
@MockServerSettings(ports = {1080})
class UpstreamContractTest { }

// AFTER — pick ONE (settings already meta-annotates the extension)
@MockServerSettings(ports = {1080}, resetBeforeEach = true)
class UpstreamContractTest {
  UpstreamContractTest(MockServerClient client) { this.client = client; }
}
```

`when` / `respond` / `verify` fluent API shape is largely stable; prefer `hasStarted()` over deprecated `isRunning()`.

## What breaks / how to fix

| Symptom | Cause | Fix |
|---------|--------|-----|
| Artifact / `:shaded` not found | Shaded classifier removed (6.0+) | Switch to `*-no-dependencies` |
| Port in use / starts twice | Both `@ExtendWith` and `@MockServerSettings` | Use only one |
| `verify` fails that used to pass (body) | Body matchers now applied | Fix matcher or SUT |
| Brittle assert on verify exception text | Over-count message reworded | Assert on new “found … but should…” wording |
| Verify misses older requests | JUnit extension default log cap (~1000) | Raise `mockserver.maxLogEntries` / expectations |
| Expectation rejected (`statusCode`) | Must be 100–999 | Fix JSON/code status codes |
| Template returns 500 | New default | Fix template or `templateFailureAsServerError=false` |
| Netty/Jackson clash | Unshaded + app stack | Prefer `-no-dependencies` |
| HTTP/3 / natives fail | No-deps can’t load HTTP/3 | Special http3 classifier/image only if needed |

Intervening majors (6–8) are included in the jump: Jakarta / Java 17 / packaging — treat as one packaging + behavior pass.

## Steps

1. Inventory all `org.mock-server` coords, shaded classifiers, Spring `@MockServerTest`, expectation JSON, `mockserver.*` props.  
2. Bump to **9.0.0** and rewrite to `*-no-dependencies` artifacts; do not mix unshaded + no-deps.  
3. Fix dual JUnit annotations; consider `resetBeforeEach = true`.  
4. Scan expectations for invalid `statusCode` / duplicate expectation `id`s (last wins).  
5. Re-run MockServer tests; triage via the table (verify matchers, message text, log caps, templates).  
6. Raise log/expectation caps if deep verify history flakes.  
7. Ask human to confirm suite green; one commit for coords, follow-ups for assertion/expectation fixes if large.

## Do not

- Keep `classifier = 'shaded'` on ≥6.0.  
- Combine `@ExtendWith(MockServerExtension)` and `@MockServerSettings` on one class.  
- Mix no-dependencies with matching unshaded modules.  
- Assume old verify body/OpenAPI checks that “always passed” are still correct.  
- Deploy MockServer to production (test/dev only).  
- Silent phase-12 bump — use this phase.

## Risk

`ASK_HUMAN` default. `SPIKE_FIRST` for templates, binary proxy, mTLS, HTTP/3, OpenAPI verify, or large suites with string-matched AssertionErrors. `SAFE_AUTO` only for trivial `when`/`respond` stubs with no verify-message asserts.

## Rollback

Revert to previous 5.15.x coords (and shaded if that was prior). Note: 5.15 is unsupported for security patches; rollback is temporary. Boot 4 still needs Java 17+ — MockServer-only rollback.

## Done when

Dependencies on 9.0.0 no-deps (or documented exception); dual-annotation fixed; human reports MockServer tests green or deferred with reason.

## Handoff

`mockServer=9.0.0; artifact=no-dependencies|unshaded; dualAnnotationFixed=yes|n/a; tests=green|deferred`
