# Stub — AOT / GraalVM native

> **Status:** stub. Always `SPIKE_FIRST` per repo.

## Detect

`native` Gradle/Maven profile, `RuntimeHints`, GraalVM CI images, `spring-boot-maven-plugin`/`bootBuildImage` native flags.

## Skeleton notes

1. Target GraalVM **25** with Boot 4 / Java 25.  
2. Unified reachability metadata; simplify reflection/resource hints where Boot AOT generates them.  
3. Management port / Actuator must be visible at **build** time when native-imaging management.  
4. Limitations: follow [Boot AOT packaging](https://docs.spring.io/spring-boot/reference/packaging/aot.html).

## Open questions for a future fill-in pass

- Per-repo hint inventory checklist  
- Interaction with Jackson 3 / Hibernate 7 native hints  

## Handoff

`aotStub=used|skipped`
