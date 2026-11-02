# 33 — Jakarta Persistence 3.2 + Spring Data JPA 4

Covers the **JPA API** and **Spring Data repository** surface that arrives with Boot 4 — distinct from the Hibernate **ORM provider** work in [03-hibernate-7.md](03-hibernate-7.md).

| Layer | Version on Boot 4 | This phase |
|-------|-------------------|------------|
| `jakarta.persistence-api` | **3.2** (Jakarta EE 11) | Spec API: EntityManager, Criteria, EntityGraph, SchemaManager, QL |
| `spring-data-jpa` | **4.0.x** (Data train **2025.1**) | Repositories, derived queries, Specifications, metamodel processor coord |
| Hibernate ORM | **7.2** (Boot 4.0) / **7.4** (Boot 4.1) | Provider / annotations / Hypersistence → **[03](03-hibernate-7.md)** |
| `javax` → `jakarta` imports | — | **[02](02-jakarta-ee.md)** first |

Official references:

- [Jakarta Persistence 3.2](https://jakarta.ee/specifications/persistence/3.2/)
- [Spring Boot 4.0 Migration Guide](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide) (Hibernate `jpamodelgen` → `processor`)
- [Spring Data JPA 4.0.0 release notes](https://github.com/spring-projects/spring-data-jpa/releases/tag/4.0.0)
- [Spring Data JPA deprecated list (4.0)](https://docs.spring.io/spring-data/jpa/reference/4.0/api/java/deprecated-list.html)

**Order:** After [02](02-jakarta-ee.md). Prefer **after [03](03-hibernate-7.md)** when both apply (provider compile breaks first). If only repositories / Criteria / metamodel are broken, this phase alone is enough.

## Detect

Any of:

- `spring-boot-starter-data-jpa`, `JpaRepository`, `@EnableJpaRepositories`, `Specification`, `EntityManager` / `CriteriaBuilder` / `EntityGraph`
- Static metamodel usage (`Foo_`, `Bar_`) or annotation processor `hibernate-jpamodelgen` / `JPAMetaModelEntityProcessor`
- `getOne(`, `getById(`, `deleteInBatch(`
- `spring.data.jpa.query.native.parser`
- `@Temporal` / `java.util.Date` / `Calendar` on entities or `@org.springframework.data.jpa.repository.Temporal`
- `CriteriaQuery#multiselect`, EntityGraph `addSubclassSubgraph` / `addKeySubgraph`
- Direct `getSingleResult()` + `catch (NoResultException`
- `Byte[]` / `Character[]` basic attributes (prefer `byte[]` / `char[]`)
- Hand-rolled shared `EntityManager` / `EntityManagerBeanDefinitionRegistrarPostProcessor`
- Direct JSqlParser ownership for native-query rewrite → also [stubs/jsqlparser.md](../stubs/jsqlparser.md)
- Stale Boot 4 integration types (package-move slice, distinct from native-SQL behavior):
  - `org.springframework.boot.orm.jpa` (old `EntityManagerFactoryBuilder`)
  - `SpringImplicitNamingStrategy` / `SpringPhysicalNamingStrategy` in `application*` still on `org.springframework.boot.orm.jpa.hibernate`

Skip when the service has no JPA / Spring Data JPA. Phase [03](03-hibernate-7.md) leaves native queries and the custom `EntityManagerFactory` unchanged; this phase owns Boot 4 JPA integration types, not Hibernate ORM mappings.

Exclude build scripts when claiming a symbol is unused. A grep for `EntityManagerFactoryBuilder` or `spring-boot-starter-data-jpa` hits `build.gradle.kts` dependency lines; that hit is not an application type.

## Before → After

### Metamodel annotation processor (`jpamodelgen` → `processor`)

Boot 4 / Hibernate 7 no longer publish `hibernate-jpamodelgen`. Keeping an **old pinned** `jpamodelgen` can compile the module but generate **zero** `*_` classes → later `cannot find symbol: variable Foo_`.

```gradle
// Before
annotationProcessor 'org.hibernate.orm:hibernate-jpamodelgen'

// After — version from Boot BOM
annotationProcessor 'org.hibernate.orm:hibernate-processor'
```

```xml
<!-- Before -->
<path>
  <groupId>org.hibernate.orm</groupId>
  <artifactId>hibernate-jpamodelgen</artifactId>
</path>

<!-- After -->
<path>
  <groupId>org.hibernate.orm</groupId>
  <artifactId>hibernate-processor</artifactId>
</path>
```

If the processor class is named explicitly:

```text
Before: org.hibernate.jpamodelgen.JPAMetaModelEntityProcessor
After:  org.hibernate.processor.HibernateProcessor
```

After the swap, confirm generated sources contain `*_` types before debugging `Specification` code.

### Spring Data repository API renames

```java
// Before
entity = repo.getOne(id);       // deprecated
entity = repo.getById(id);      // deprecated
repo.deleteInBatch(entities);

// After
entity = repo.getReferenceById(id); // lazy reference — same idea as EM#getReference
repo.deleteAllInBatch(entities);
```

`getReferenceById` does **not** hit the DB until state is accessed — do not treat it as a loaded entity for validation that needs a flush/load.

`@org.springframework.data.jpa.repository.Temporal` is deprecated in SDJPA 4 — use `java.time` parameter / property types instead.

### Removed / silent config: native query parser

```yaml
# Before (Boot 3) — REMOVED in Spring Data JPA 4; silently ignored on Boot 4
spring.data.jpa.query.native.parser: jsqlparser
```

If the service depended on a specific enhancer/parser, configure a `QueryEnhancerSelector` on `@EnableJpaRepositories` (see SDJPA 4 javadoc). Direct JSqlParser ownership → [stubs/jsqlparser.md](../stubs/jsqlparser.md). Grep config trees/secrets for the old property — absence of an error does **not** mean behavior is unchanged.

### Derived queries: Criteria → JPQL (behavior)

Spring Data JPA 4 builds derived finder methods as **string JPQL** (cached) instead of `CriteriaQuery`. Signatures stay the same; edge cases to regression-check:

- Sort **nulls first/last** (now honored more consistently via JPA 3.2 null precedence)
- Exact ordering of multi-join derived methods
- Methods whose SQL shape was Criteria-specific

No mechanical rewrite required for happy-path finders. Prefer logging SQL once for high-risk derived methods (`ASK_HUMAN` if results differ).

### Single-result: `getSingleResultOrNull`

JPA 3.2 / SDJPA 4 prefer `Query.getSingleResultOrNull()`. Repository `Optional` / nullable returns stay observationally the same. First-party code that does:

```java
// Before — control flow via exception
try {
  return em.createQuery(...).getSingleResult();
} catch (NoResultException e) {
  return null;
}

// After
return em.createQuery(...).getSingleResultOrNull();
```

Leaving the old catch after switching to `getSingleResultOrNull()` leaves **dead** handlers; unguarded callers that assumed “never null” can NPE.

Note: Hibernate **7.3+** also makes `getSingleResult*` throw on **duplicate** rows more consistently — see [03](03-hibernate-7.md).

### Jakarta Persistence 3.2 — EntityGraph / Criteria

```java
// Before (deprecated for removal)
entityGraph.addSubclassSubgraph(SubType.class);
graph.addSubgraph(attr, SubType.class);
graph.addKeySubgraph(mapKeyAttr);

// After
entityGraph.addTreatedSubgraph(SubType.class);           // or Graph#addTreatedSubgraph
graph.addTreatedSubgraph(attr, SubType.class);
graph.addMapKeySubgraph(mapKeyAttr);
```

```java
// Before
criteriaQuery.multiselect(expr1, expr2);

// After (preferred)
criteriaQuery.select(cb.tuple(expr1, expr2));
// or cb.array(...)
```

Inheritance subtype attributes on Criteria paths still need explicit `cb.treat(...)` under Hibernate 7 — covered in [03](03-hibernate-7.md).

`Transaction#getTimeout()` is now `Integer` (nullable) in JPA 3.2 — avoid auto-unboxing into `int` comparisons (`NullPointerException` risk).

`EntityManagerFactory#getSchemaManager()` is the JPA 3.2 contract. Hibernate’s `SessionFactory#getSchemaManager()` return type now extends it (bytecode note if you compiled against older Hibernate SPI) — prefer the JPA type in application code.

`jakarta.persistence.spi.PersistenceUnitTransactionType` → `jakarta.persistence.PersistenceUnitTransactionType`.

### Temporal / array attribute deprecations (JPA 3.2)

```java
// Before (deprecated for new code)
@Temporal(TemporalType.TIMESTAMP)
private java.util.Date updatedAt;
private Byte[] payload;       // prefer primitive array
private Character[] code;

// After
private Instant updatedAt;    // or LocalDateTime / OffsetDateTime as appropriate
private byte[] payload;
private char[] code;          // or String
```

Do **not** rewrite production column types without Flyway approval ([08-flyway-db.md](08-flyway-db.md)). Mapping-only moves to `java.time` are usually `SAFE_AUTO` when JDBC types already match.

### Records as embeddables / projections (additive)

```java
// OK — value object
@Embeddable
public record Money(BigDecimal amount, String currency) {}

// OK — class-based projection / DTO
public record BookSummary(String title, BigDecimal amount) {}

// NOT OK — fails bootstrap
@Entity
public record Book(@Id Long id, String title) {}
```

Records may be `@Embeddable` or projection targets; they must **not** be `@Entity`.

### Specifications (additive — optional cleanup)

Existing `Specification<T>` read queries keep working. SDJPA 4 adds clearer types when you touch bulk/update paths:

- `PredicateSpecification` — reusable bare `Predicate`
- `UpdateSpecification` / `DeleteSpecification` — Criteria update/delete

`Specification.where(...)` / `unrestricted()` remain available. Prefer adopting new types only when editing the code — do not churn stable specs.

### Shared EntityManager / AOT

- Auto-registered shared `EntityManager` via `EntityManagerBeanDefinitionRegistrarPostProcessor` is deprecated — prefer EMF-backed shared EM or JPA 3.2 qualified injection; multi-datasource setups may need an explicit bean (`ASK_HUMAN`).
- AOT repository generation is **on by default** in SDJPA 4 — if native/AOT builds break on repositories, spike with [stubs/aot-native.md](../stubs/aot-native.md); do not disable AOT casually on non-native apps.

### Boot 4 package and naming-strategy names

These are compile-shaped renames. They are not a reason to rewrite SQL.

| Before | After (Boot 4) |
|--------|----------------|
| `org.springframework.boot.orm.jpa.EntityManagerFactoryBuilder` | `org.springframework.boot.jpa.EntityManagerFactoryBuilder` |
| `org.springframework.boot.orm.jpa.hibernate.SpringImplicitNamingStrategy` | `org.springframework.boot.hibernate.SpringImplicitNamingStrategy` |
| `org.springframework.boot.orm.jpa.hibernate.SpringPhysicalNamingStrategy` | `org.hibernate.boot.model.naming.CamelCaseToUnderscoresNamingStrategy` |

`DataSourceBuilder` stays `org.springframework.boot.jdbc`. `LocalContainerEntityManagerFactoryBean` and `JpaTransactionManager` stay on their existing packages. Confirm the FQCN against the target Boot patch if the line is not 4.1; do not invent a third package.

```yaml
spring.jpa.hibernate.naming.implicit-strategy: org.springframework.boot.hibernate.SpringImplicitNamingStrategy
spring.jpa.hibernate.naming.physical-strategy: org.hibernate.boot.model.naming.CamelCaseToUnderscoresNamingStrategy
```

**Preserve a custom `EntityManagerFactory`.** Qualifiers, a hand-rolled datasource configuration class, and native SQL stay. This slice changes Boot 4 type names and naming-strategy class names on that class. It does not replace the class with Boot autoconfiguration.

#### Package-move-only vs decision path

| Inventory (sources, not the build coordinate line) | Path |
|----------------------------------------------------|------|
| Only the three names in the table above | `SAFE_AUTO` package-move. `filesTouched` may be the EMF config class plus `application*` YAML. `repoApi=n/a`, `nativeParser=n/a` |
| `getOne` / `getById` / `deleteInBatch` | Repository API renames in this phase (`SAFE_AUTO` for the mechanical replacements in the repository section) |
| `hibernate-jpamodelgen` | Processor swap in this phase |
| Native `@Query` **and** `Pageable` or `Sort` on that method | `ASK_HUMAN` — sort/pagination rewrite, not a package move |
| `QueryEnhancerSelector`, or the service relied on `spring.data.jpa.query.native.parser` | `ASK_HUMAN` |
| App-owned `net.sf.jsqlparser` used to rewrite queries | `ASK_HUMAN` — [stubs/jsqlparser.md](../stubs/jsqlparser.md) |

`repoApi=n/a` means those repository methods were absent, not that they were migrated. `nativeParser=n/a` means the property was absent, not that it was deleted from YAML.

Fixed `@Query` strings with explicit `OFFSET` / `LIMIT` and **no** `Pageable` are a poor candidate for a mechanical SQL edit. JSqlParser on the classpath because Spring Data JPA brought it transitively does **not** by itself require a `QueryEnhancerSelector` when there is no dynamic sort and no `countQuery` derivation. An interface projection whose column aliases already match the getters needs no SQL change when sort and page are absent. Runtime query behavior stays unverified until Stage C.

### Modular Boot 4 starters (reminder)

Focus starters / test jars may use `spring-boot-data-jpa` / `spring-boot-data-jpa-test` naming — align with [19-modular-starters.md](19-modular-starters.md). Do not invent coordinates; follow Boot 4 BOM.

## Steps

1. Confirm Detect; ensure [02](02-jakarta-ee.md) imports are clean. Grep application sources, not build coordinates, and fill the package-move vs decision table.  
2. If the only required edits are `EntityManagerFactoryBuilder` and the naming-strategy class names, do that slice and stop. Preserve the custom `EntityManagerFactory`. Set `repoApi=n/a` and `nativeParser=n/a` when those signals are absent.  
3. Swap `hibernate-jpamodelgen` → `hibernate-processor` (+ processor class rename) when the old processor is present; verify `*_` metamodel generation.  
4. Replace `getOne` / `getById` → `getReferenceById`; `deleteInBatch` → `deleteAllInBatch` when those calls exist.  
5. Grep and remove `spring.data.jpa.query.native.parser` only when it is set. Wire `QueryEnhancerSelector` only if behavior depended on it (`ASK_HUMAN`). Do not add a selector because JSqlParser is transitive.  
6. Migrate EntityGraph / `multiselect` / `PersistenceUnitTransactionType` call sites; fix `getTimeout()` unboxing.  
7. Replace direct `getSingleResult` + `NoResultException` control flow with `getSingleResultOrNull` where appropriate.  
8. Prefer `java.time` over `@Temporal` / `Date` on touched entities; fix `Byte[]`/`Character[]` basics when compiling against 3.2 warnings-as-errors.  
9. Reject any `@Entity` record; keep records for embeddables/projections only.  
10. Spot-check high-risk derived queries (nulls sort, multi-join order) if tests exist. Native SQL with `Pageable` / `Sort` is the decision path, not a package move.  
11. Leave Hibernate Session / `@Where` / Hypersistence / Persistable UUID / sequence `allocationSize` work to [03](03-hibernate-7.md).

## Do not

- Pin Hibernate or Spring Data versions off the Boot BOM.  
- Leave `hibernate-jpamodelgen` on an old 6.x pin “because it still resolves.”  
- Treat `getReferenceById` as a fully loaded entity.  
- Rewrite Flyway DDL solely for JPA 3.2 deprecation warnings without approval.  
- Put `@Entity` on a Java record.  
- Disable AOT / invent QueryEnhancer hacks to hide unrelated Boot 4 failures.  
- Duplicate Persistable / Session `save|update|delete` fixes here — those belong in [03](03-hibernate-7.md).  
- Collapse a custom `EntityManagerFactory` or datasource configuration class to Boot autoconfiguration.  
- Add `QueryEnhancerSelector` when the application does not own JSqlParser and native methods have no dynamic sort.  
- Edit native SQL, including interface-projection queries whose aliases already match getters, on the package-move-only path.  
- Treat a Gradle coordinate line as proof that application code uses a type.

## Risk

`SAFE_AUTO` for the package-move-only slice (EMF builder import + naming-strategy class names, custom EMF preserved), the processor coordinate swap, `getOne`/`getById`/`deleteInBatch` renames, EntityGraph method renames, and `getSingleResultOrNull` with clear call sites.  
`ASK_HUMAN` for native paging (`Pageable` / `Sort` on a native method), parser / `QueryEnhancerSelector` behavior, query text rewrites, multi-datasource EntityManager wiring, temporal/column mapping that might touch stored data, and derived-query result differences.  
`SPIKE_FIRST` for custom Spring Data SPI (`QueryMethodEvaluationContextProvider`, SpEL query internals) or AOT repository failures.

## Rollback

Revert repository/API/processor commits independently of Hibernate provider commits when possible. Processor swap rollback restores metamodel generation on the previous Boot line only.

## Done when

- Package-move slice: `EntityManagerFactoryBuilder` and naming strategies use the Boot 4 names; custom EMF class still present; SQL unchanged. `filesTouched` may be config + YAML only, with `repoApi=n/a` and `nativeParser=n/a`.  
- Metamodel `*_` classes generate under Boot 4 (if used).  
- No first-party `getOne` / `getById` / `deleteInBatch` / `hibernate-jpamodelgen` (or those were absent).  
- No live dependency on `spring.data.jpa.query.native.parser` (absent counts as `n/a`, not “removed”).  
- EntityGraph / Criteria deprecations-for-removal fixed in first-party code (or explicitly deferred).  
- Compile progresses past JPA / Spring Data API errors; repository smoke tests green if present. Runtime native-query behavior stays unverified on a package-move-only slice.

## Handoff

`jpa32=ok; springDataJpa=4; slice=package-move-only|api|decision; metamodelProcessor=hibernate-processor|n/a; repoApi=migrated|partial|n/a; nativeParser=removed|n/a; customEmf=preserved|n/a; askedHuman=yes|no`
