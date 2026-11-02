# Stub — JVM and container verification

> **Status:** stub. Use when local build works but packaged app/container fails, or when changing the Java release with Boot 4.

## Detect

Dockerfile / CI image / `bootBuildImage` / different Java in shell vs CI vs runtime; attach/profiler failures; new `--add-opens` / unsafe flags proposed.

## Skeleton notes

1. Do not edit CI job images or base-image registries. This stub is for JVM flags and how the process starts when a container already exists. Agent builds set `JAVA_HOME` on the command ([COMPILE-GATES.md](../references/COMPILE-GATES.md)).  
2. Choose JRE vs JDK from actual needs (attach, agents, diagnostics) — not a blanket rule.  
3. Pin image digests (or controlled patch tags); match arch/libc; non-root; trust stores / fonts / native deps.  
4. Add JVM flags (`--add-opens`, unsafe memory, experimental) **only with evidence**: capture exception + library, confirm flag exists on that JDK, prefer a library upgrade that removes the need, document removal condition.  
5. Instrumentation/attach failures: confirm attach modules in image, permissions, temp dirs — do not globally inject `EnvironmentPostProcessor` hacks across services.  
6. Verify final image: entrypoint, user, memory under limits, TLS, graceful shutdown, health endpoints.
7. Audit JVM-option delivery. Shell-form commands may expand `$JAVA_OPTS`; exec-form `CMD ["java", "-jar", "/app.jar"]` does not. For exec-form images, use `JAVA_TOOL_OPTIONS` (read by the JVM) or put explicit arguments in the array. Verify the effective process command/environment rather than trusting deployment YAML.
8. For WebFlux/Netty 4.2, carry the measured allocator decision from [35-webflux.md](../phases/35-webflux.md). Set `-Dio.netty.allocator.type=…` before JVM startup, never from application code after Netty may initialize.
9. Capture a fair pre-migration performance baseline on the latest supported patch of the old Boot line. Compare the same JDK/container limits, traffic shape, tracing/sampling, connection pools, and warm-up; otherwise a platform change can mask or exaggerate a regression.
10. Record where each non-default JVM flag is owned (Dockerfile, Helm values, deployment env, buildpack) plus its removal condition.

## Open questions for a future fill-in pass

- Compact object headers / other JDK 25 experimental flags policy
- How to assert effective JVM options in a deployed container

## Handoff

`jvmContainersStub=used|skipped`
