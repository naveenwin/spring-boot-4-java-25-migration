# Stub — PostgreSQL TLS / EOF troubleshooting

> **Status:** stub (ops). Use when PG connections fail during SSL negotiation/auth with `EOFException`, `SSLHandshakeException`, or generic connect errors after a Java/Boot upgrade.

## Detect

Postgres JDBC failures at handshake; works locally but fails in container/k8s; appears only after Java 25 image change.

## Skeleton notes

1. EOF alone is not a root cause — host/port/proxy, server TLS off, cert/hostname/cipher mismatch, firewall/mesh, `pg_hba`, wrong/dupe driver, server pressure.  
2. Do **not** blame Java 25 without comparative evidence (same driver, trust store, URL, network path on both JREs).  
3. Diagnose in layers: resolved `org.postgresql:postgresql` → DNS/TCP → `psql` with same SSL mode → compare client/server/proxy logs.  
4. Use SSL modes deliberately (`disable` only as controlled diagnostic). Prefer `verify-full` (or platform standard) in production; fix trust/DNS/proxy rather than weakening TLS.  
5. Upgrade JDBC driver for the Java release before weakening TLS.

## Open questions for a future fill-in pass

- Cloud SQL / PgBouncer specific handshake notes (keep generic)  

## Handoff

`pgTlsStub=used|skipped`
