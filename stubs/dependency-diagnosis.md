# Stub — Dependency / binary compatibility diagnosis

> **Status:** stub from Boot 4 upgrade reference practice. Use when compile succeeds but startup fails with missing class/method, or two modules resolve different versions of the same library.

## Detect

`ClassNotFoundException`, `NoClassDefFoundError`, `NoSuchMethodError`, `AbstractMethodError`, `ServiceConfigurationError` after Boot 4 bump; mixed Jackson / Micrometer / OpenAPI / Hibernate / HTTP-client versions in the tree.

## Skeleton notes

1. Capture the **first meaningful cause** (caller + missing target), not only the top Spring bean wrapper.  
2. Trace resolution:

```bash
./gradlew <module>:dependencies --configuration runtimeClasspath
./gradlew <module>:dependencyInsight --configuration runtimeClasspath --dependency <artifact>
# Maven: ./mvnw dependency:tree -Dverbose -Dincludes=group:artifact
```

3. Inspect the runtime JAR: `jar tf` / `javap -classpath … -p FullyQualifiedClass`.  
4. Check `META-INF/services`, `AutoConfiguration.imports`, `spring.factories`.  
5. Fix order: upgrade/replace library for Boot 4 → remove unnecessary pin → exclude stale transitive + add compatible → migrate custom code → isolate/postpone if no release exists.  
6. Frequent surfaces: JSqlParser ([jsqlparser.md](jsqlparser.md)), HTTP client TLS pins, Hibernate SPI extensions, Micrometer/tracing family, springdoc/Swagger ([../phases/32-springdoc-openapi.md](../phases/32-springdoc-openapi.md)), Flyway/Liquibase modules.

## Open questions for a future fill-in pass

- Promote to a full phase with Before→After examples per failure type  
- Scripting equivalents of class-reference scans (optional)

## Handoff

`depDiagnosis=used|skipped; rootCause=<short>`
