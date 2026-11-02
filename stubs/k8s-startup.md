# Stub — Kubernetes startup triage

> **Status:** stub (ops). Use when an upgraded app hits `CrashLoopBackOff`, fails readiness, or flaps healthy then restarts.

## Detect

Post-deploy restart loops, probe failures, OOM (137), migration lock timeouts after Boot 4 / Java 25 rollout.

## Skeleton notes

1. Confirm image digest / revision actually rolled out (`rollout status`, pod `imageID`).  
2. `describe` + terminated state — distinguish app exit, OOM, probe fail, image/pull, permissions, eviction.  
3. Current and `--previous` logs; first cause + timestamps.  
4. Compare env deltas: Java/flags/memory, ConfigMaps/Secrets **presence** (never print secret values), DB/broker/DNS/TLS, probe paths/delays, migration startup duration.  
5. Map cause → focused doc: missing class → [dependency-diagnosis.md](dependency-diagnosis.md); props/starters → [18](../phases/18-config-properties.md)/[19](../phases/19-modular-starters.md); TLS EOF → [postgresql-tls.md](postgresql-tls.md); probes → [22-actuator.md](../phases/22-actuator.md).  
6. Prove stability: restart count flat, rollout complete, readiness holds, health/APIs OK — not a momentary `1/1 Running`.

## Open questions for a future fill-in pass

- Org-specific probe conventions (keep out of generic pack)  

## Handoff

`k8sStartupStub=used|skipped`
