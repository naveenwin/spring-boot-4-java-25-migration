# Stub — Spring Batch

> **Status:** stub.

## Detect

`spring-boot-starter-batch`, Job/Step beans.

## Skeleton notes

1. Boot 4 may default Batch to **in-memory** metadata — restore JDBC via `spring-boot-starter-batch-jdbc` (or equivalent) when jobs need a database.  
2. Align with modular starters ([19-modular-starters.md](../phases/19-modular-starters.md)).  
3. Risk: `ASK_HUMAN` if job repository storage changes.

## Open questions for a future fill-in pass

- Exact starter coordinates per Boot patch  
- Migration of existing Batch schema versions  

## Handoff

`batchStub=used|skipped`
