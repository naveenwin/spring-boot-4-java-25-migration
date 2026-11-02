# Stub — MongoDB / Spring Data Mongo

> **Status:** stub from Boot 4 / Data 2025.1 research. Promote to a phase when a Mongo service is migrated.

## Detect

`spring-boot-starter-data-mongodb`, `MongoTemplate`, UUID/BigDecimal document fields, reactive Mongo.

## Skeleton notes

1. Property split: driver `spring.mongodb.*` vs Data `spring.data.mongodb.*` — use [18-config-properties.md](../phases/18-config-properties.md) + migrator.  
2. Explicit representation settings when upgrading existing data: `spring.mongodb.representation.uuid`, `spring.data.mongodb.representation.big-decimal` (confirm exact keys for the Boot patch).  
3. Starter naming: `mongodb` vs `data-mongodb` per Boot 4 modularization ([19-modular-starters.md](../phases/19-modular-starters.md)).  
4. Health/metrics property renames (`management.health.mongodb`, etc.).  
5. Risk: `ASK_HUMAN` / `SPIKE_FIRST` for BSON UUID subtype 3 / Decimal128 existing data.

## Open questions for a future fill-in pass

- Reactive Mongo / GridFS / vector search AOT  
- Full Before→After YAML matrix for UUID/BigDecimal  
- Interaction with Jackson 3 codecs for Mongo custom conversions  

## Handoff

`mongoStub=used|skipped`
