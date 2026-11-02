# 35 — Spring WebFlux / Reactor Netty

## Detect

Apply when any of:

- `spring-boot-starter-webflux`, `WebClient`, `RouterFunction`, `WebFilter`
- Reactor Netty server/client configuration
- `spring.http.codecs.*`, custom `CodecCustomizer`, Jackson JSON encoders/decoders
- reactive Spring Security, WebSocket, RSocket, or `WebTestClient`

Skip when the service is MVC-only and has no `WebClient` or reactive infrastructure.

## Before → After

### Focused starters

```gradle
// BEFORE — WebFlux starter implicitly used for both server and outbound client
implementation "org.springframework.boot:spring-boot-starter-webflux"

// AFTER — keep WebFlux for a reactive server; add the focused client starter
// when the service creates WebClient without hosting a reactive server
implementation "org.springframework.boot:spring-boot-starter-webflux"
implementation "org.springframework.boot:spring-boot-starter-webclient" // client-only usage
```

Choose from actual usage. Do not add both starters automatically; coordinate starter selection with [19-modular-starters.md](19-modular-starters.md).

### Jackson 3 codecs

```yaml
# BEFORE — forbidden Boot 4 bridge
spring:
  http:
    codecs:
      preferred-json-mapper: jackson2

# AFTER
# delete the preference; Boot 4 uses Jackson 3 JsonMapper
```

Custom codec configuration must use `tools.jackson` / Boot's `JsonMapper` ([04-jackson-3.md](04-jackson-3.md)). Remove Jackson 2 encoder/decoder types; do not retain dual codecs.

### WebClient customizers

Prefer Boot-managed `WebClient.Builder` plus `WebClientCustomizer` over constructing unrelated builders in each service. Preserve existing connector, timeout, proxy, TLS, filter ordering, observation, and maximum-buffer behavior.

### WebTestClient

Align WebFlux test dependencies with Boot 4's focused test starters ([09-testing.md](09-testing.md), [19-modular-starters.md](19-modular-starters.md)). Keep tests on the same codec stack as production; a test-only Jackson 2 codec hides contract failures.

## Netty 4.2 allocator decision

Boot 4 / Reactor Netty can move services to Netty 4.2, whose default allocator differs from 4.1. This is a silent runtime characteristic, not a compile failure.

1. Read the pre-migration latency, throughput, CPU, direct-memory, and allocation baseline that [42-baseline.md](42-baseline.md) captured in Stage 0 on the Boot 3 commit.
2. Record the resolved Netty version and effective `ByteBufAllocator.DEFAULT`.
3. Ask the human to choose:
   - explicitly set `-Dio.netty.allocator.type=pooled` to preserve the former allocator while migrating; or
   - keep adaptive only after a representative comparison.
4. Put the flag in deployment JVM options, not application code: allocator selection can happen before a runtime setter executes.
5. Verify the final container actually delivers the option via [stubs/jvm-containers.md](../stubs/jvm-containers.md).

Do not claim one allocator is universally faster. The requirement is an explicit, measured decision instead of inheriting a new default unnoticed.

## Steps

1. Inventory reactive server, outbound-only `WebClient`, codecs, Reactor Netty customizers, Security, WebSocket/RSocket, and tests.
2. Select focused WebFlux/WebClient starters from actual usage.
3. Remove Jackson 2 preferred-mapper/config/codecs; use the phase-04 Jackson 3 mapper and wire-contract baseline.
4. Update `HttpHeaders` / client code through [06-http-clients.md](06-http-clients.md).
5. Align `WebTestClient` and focused test starters.
6. Record the Netty version and allocator against the Stage 0 baseline; record the human's pooled-vs-adaptive decision and where the JVM option is delivered.
7. Name the representative HTTP/WebClient, streaming/backpressure, and agreed performance smoke tests for Stage C. The human runs the performance smoke.
8. Route reactive Security changes to [20-spring-security-7.md](20-spring-security-7.md).

## Do not

- Leave `preferred-json-mapper=jackson2` or a test-only Jackson 2 codec.
- Add `spring-boot-starter-webflux` solely to obtain `WebClient` when the focused client starter is sufficient.
- Set `io.netty.allocator.type` from application code after Netty initialization.
- Adopt pooled or adaptive fleet-wide without representative measurements.
- Treat a green request/response smoke as proof that streaming, cancellation, backpressure, or memory behavior is unchanged.
- Introduce Undertow for reactive Boot 4.

## Risk

`SAFE_AUTO` for focused starter and Jackson 3 codec cleanup when behavior is covered.  
`ASK_HUMAN` for allocator/JVM options, TLS/proxy/timeouts, reactive Security, or production performance conclusions.  
`SPIKE_FIRST` for custom Netty pipelines, WebSocket/RSocket, large streaming bodies, or known memory/latency sensitivity.

## Rollback

Revert the WebFlux/starter/codec changes with the Boot migration. Remove any newly introduced allocator flag when rolling back to the old Netty line. Do not roll only JSON back to Jackson 2.

## Done when

- Reactive server/client starters match actual usage.
- Production and test codecs use Jackson 3 only.
- Context plus representative server/client/streaming checks are recorded.
- Netty version, allocator decision, baseline, and container option delivery are documented.

## Handoff

`webflux=server|client-only|both|n/a; codecs=jackson3; webTestClient=aligned|n/a; netty=<version>; allocator=pooled|adaptive|deferred; perfSmoke=green|deferred|n/a`
