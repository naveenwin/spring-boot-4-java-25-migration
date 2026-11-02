# Stub — Virtual threads (Java 21–25)

> **Status:** stub. Relevant when `spring.threads.virtual.enabled=true` or the upgrade proposes enabling virtual threads on Java 25.

## Detect

`spring.threads.virtual.enabled`, explicit virtual-thread executors, Java 21+ runtime with thread-per-request workload.

## Skeleton notes

1. Java **21–23**: blocking inside `synchronized` can pin carriers — investigate pinning on blocking paths.  
2. Java **24+** ([JEP 491](https://openjdk.org/jeps/491)): do **not** mechanically replace every `synchronized` with `ReentrantLock` “for pinning.” Change locking only when diagnostics show a problem.  
3. Virtual threads help blocking I/O wait; they do not speed CPU-bound work or remove DB/HTTP pool / rate-limit ceilings.  
4. `ThreadLocal` is per virtual thread (not carrier leak); still watch cost, inheritance, and lifecycle. Prefer scoped values where supported for immutable bounded context.  
5. Enable in non-prod first; load-test; check JFR/metrics for pinning, contention, pool saturation.  
6. Verify cancellation, timeouts, logging/security/observability context propagation.

## Open questions for a future fill-in pass

- Boot 4 property matrix for virtual threads per web stack  
- Interaction with `@Async` / messaging listeners  

## Handoff

`virtualThreadsStub=used|skipped; javaRelease=<n>`
