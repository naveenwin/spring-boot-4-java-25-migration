# Stub — R2DBC / Spring Data R2DBC

> **Status:** stub. Force-quoting and ID mapping need a SPIKE on real schemas.

## Detect

`spring-boot-starter-data-r2dbc`, `org.springframework.r2dbc.core.DatabaseClient`, R2DBC repositories, custom `ConnectionFactory` / `ConnectionPool`, `R2dbcTransactionManager`, `TransactionalOperator`.

## Skeleton notes

1. Align starter to Boot 4 focused name ([19-modular-starters.md](../phases/19-modular-starters.md)).  
2. First classify the surface. `DatabaseClient` and `TransactionalOperator` alone are Spring Framework APIs; they do not imply Spring Data repositories/entities. Do not schedule Spring Data migration work from the starter/POM alone—inspect imports or compiled classes.
3. Spring Data Relational 4.x may default to quoted identifiers — verify against existing schemas (`SPIKE_FIRST`) only when repositories/mapping are actually present.
4. Composite `@Id` / embeddables — confirm against Data 2025.1 notes.
5. If the service hand-builds `PostgresqlConnectionFactory`, `ConnectionPool`, routing, or transactions, Boot auto-configuration changes may be irrelevant; the driver/pool API and behavior are the risk. Inventory builder options and custom property prefixes before editing.
6. Ask the human for a real-Postgres integration smoke when custom pools exist: startup warmup/failure propagation, read/write routing, transaction rollback, prepared statements, acquire timeout/retry, pool saturation, and multi-host failover when configured.
7. Align `r2dbc-postgresql`, pool, and SPI through the Boot BOM/catalog; do not independently bump one component or mix an old driver with a new pool.
8. Use [25-testcontainers-2.md](../phases/25-testcontainers-2.md) for Postgres container coordinate/package migration; compile is not a driver-behavior test.
9. Jackson 3 codecs only if the service customizes R2DBC JSON — cross-link [04-jackson-3.md](../phases/04-jackson-3.md).

## Open questions for a future fill-in pass

- Exact quoting default per database  
- Migration path for composite IDs  
- Fleet-specific read/write routing and failover acceptance scenarios

## Handoff

`r2dbcStub=used|skipped; surface=framework|spring-data|custom-pool; postgresSmoke=green|deferred|n/a`
