# Stub — Spring Session

> **Status:** stub.

## Detect

Spring Session Redis/JDBC (or other stores), `spring.session.*` properties.

## Skeleton notes

1. Property prefix moves toward `spring.session.data.*` (e.g. Redis) — use [18-config-properties.md](../phases/18-config-properties.md).  
2. Boot 4 drops some Session store integrations (Hazelcast / Mongo session called out in Boot migration notes) — `ASK_HUMAN` if used.  
3. Risk: `SAFE_AUTO` for pure property renames; `ASK_HUMAN` for store replacement.

## Open questions for a future fill-in pass

- Full store support matrix on Boot 4  
- Reactive session  

## Handoff

`sessionStub=used|skipped`
