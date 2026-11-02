# 03 — Hibernate 7 (ORM provider)

Migrate the service onto the **Hibernate ORM** line shipped by **Boot 4** (do not pin Hibernate independently of the Boot BOM unless approved).

Jakarta Persistence **3.2** API + Spring Data JPA **4** repositories (metamodel processor, `getOne`→`getReferenceById`, derived-query engine, etc.) → **[33-jpa-spring-data.md](33-jpa-spring-data.md)**.

| Boot line | Hibernate (BOM) | Hypersistence artifact |
|-----------|-----------------|------------------------|
| Boot **4.0.x** | **7.2.x** | `hypersistence-utils-hibernate-73` (also covers 7.2) |
| Boot **4.1.x** (preferred fleet target) | **7.4.x** | `hypersistence-utils-hibernate-73` (covers **7.3 and 7.4**) |

Official guides (read when grepping fails to explain a break):

- [Hibernate 6.0 migration](https://docs.hibernate.org/orm/6.0/migration-guide/) (Boot 2.7 / H5 → Boot 3 / H6 path)
- [Hibernate 7.0](https://docs.hibernate.org/orm/7.0/migration-guide/) · [7.1](https://docs.hibernate.org/orm/7.1/migration-guide/) · [7.2](https://docs.hibernate.org/orm/7.2/migration-guide/) · [7.3](https://docs.hibernate.org/orm/7.3/migration-guide/) · [7.4](https://docs.hibernate.org/orm/7.4/migration-guide/)
- Hibernate ↔ Boot matrix: [hibernate.org/community/integrations](https://hibernate.org/community/integrations/)

**Path note:** Boot 2.7→4 always crosses Hibernate **5 → 6 → 7**. Finish [02-jakarta-ee.md](02-jakarta-ee.md) first. Boot 3→4 is mostly **6.x → 7.x** (plus fleet Hypersistence / Persistable work below).

## Detect

Any of:

- `spring-boot-starter-data-jpa`, `@Entity`, Hypersistence (`hypersistence-utils-hibernate-55` / `63` / `71` / `73`) or legacy `hibernate-types-52` / `60`
- `@Type` / `@TypeDef` / custom Hibernate `UserType` (including `PostgreSQLEnumType` subclasses, `MonetaryAmountType`, JSON types)
- Legacy Session API: `.save(`, `.update(`, `.saveOrUpdate(`, `.delete(`, `.load(` (not `getReference` / `find` / `persist` / `merge` / `remove`)
- Removed / renamed annotations: `@Where`, `@WhereJoinTable`, `@OrderBy` (Hibernate), `@Proxy`, `@LazyCollection`, `@LazyToOne`, `@SelectBeforeUpdate`, Hibernate `@Table` / `@Index` / `@ForeignKey` / `@IndexColumn`, `@Persister`, `@Loader`, `@Target` (Hibernate), `@Columns`
- Custom UUID generators: `@GenericGenerator`, `extends UUIDGenerator`, strategy pointing at a project `CustomUUIDGenerator`
- Assigned `@Id` UUID **without** `Persistable` (Spring Data may treat pre-set IDs as existing)
- `BaseJpaRepository.update(` call sites (Hypersistence) on managed / `@Version` graphs
- Entity/embeddable fields typed `org.json.JSONObject`
- `repositoryBaseClass = BaseJpaRepositoryImpl` (Hypersistence repos)
- Legacy Criteria (`org.hibernate.Criteria` / `createCriteria`), `Query#iterate`, callable `@NamedNativeQuery`, `hbm.xml`
- Versioned dialects (`PostgreSQL95Dialect`, etc.), `hibernate.multiTenancy` / `MultiTenancyStrategy`
- `StatelessSession` + second-level cache, or Hypersistence bulk APIs that use it
- Custom `Interceptor` / `Integrator` / `Configurable` ID generators / `UserType#nullSafeGet|Set`
- Native queries expecting `java.sql.Date` / `Timestamp` without `@SqlResultSetMapping`
- Bulk HQL/JPQL update/delete against `@Immutable` entities
- Criteria `Path#get("subtypeAttr")` without `CriteriaBuilder#treat`
- Maven enhance plugin under old coordinates (`hibernate-enhance-maven-plugin` / non-`org.hibernate.orm` group)

Skip only when intake proves no JPA / no Hibernate types / no Session-level API usage.

Repository renames (`getOne`), `hibernate-jpamodelgen` → `hibernate-processor`, EntityGraph JPA 3.2 methods, Boot 4 `EntityManagerFactoryBuilder` / naming-strategy packages, native SQL, and a custom `EntityManagerFactory` are **[33](33-jpa-spring-data.md)** — schedule that phase when Detect hits those signals (usually right after this one). Do not edit them here.

### Custom types — consumers first

Inventory field-level consumers before replacing `hibernate-types-*` or adding Hypersistence.

```text
hibernate-types / Hypersistence declared?
  no  -> continue with the other Detect signals
  yes -> find every first-party import, @TypeDef, @Type, UserType, and JSON entity field
          no field-level consumer -> remove the dead registration and the dependency
          consumer exists         -> classify the mapping; do not auto-add *-73
```

| Signal | Count in | Action |
|--------|----------|--------|
| `hibernate-types-*` / `hypersistence-utils-hibernate-*` coordinates | build files | **remove** when nothing consumes them; **migrate** to `hypersistence-utils-hibernate-73` only when a field still needs the type |
| `@TypeDef` / `@TypeDefs` whose name no field `@Type` uses | entities and mapped superclasses | delete the registration; do not keep the library to preserve it |
| Field `@Type`, `UserType`, `JsonBinaryType`, `JsonStringType`, `JSONObject` on an entity | first-party sources | stop and classify (the stop list below is not `SAFE_AUTO`) |
| Session `save` / `update` / `saveOrUpdate` / `delete` / `load` | see receiver-aware search | mechanical only when the receiver is a Hibernate `Session` |
| Repository API, native query, custom `EntityManagerFactory`, metamodel processor | — | leave unchanged for [33](33-jpa-spring-data.md) |
| DDL / Flyway | — | stop; [08-flyway-db.md](08-flyway-db.md) plus human |

Confidence can be ≥ 90 with no human question when the only hit is dead `@TypeDef` registrations and zero field consumers. Compile, and the resolved Hibernate patch, stay unverified. The Boot → Hibernate row at the top of this file is matrix inference until dependency resolution records the artifact.

**Stop** (not `SAFE_AUTO`) when first-party code has any of: a field-level custom type, a `UserType`, a `JSONObject` entity field, a Persistable / custom UUID strategy, a versioned `BaseJpaRepository.update`, a JSON/XML stored-shape change, a DDL or Flyway edit, or a compatibility property (`immutable_entity_update_query_handling_mode`, `xml_format_mapper.legacy_format`, native `prefer_jdbc_datetime_types`).

## Before → After

### Session / Em write API (H6 deprecated → **H7 removed**)

```java
// Before (Hibernate 5 / still compiling on 6)
session.save(entity);
session.update(entity);
session.saveOrUpdate(entity);
session.delete(entity);
session.load(MyEntity.class, id);   // proxy by id
T t = session.get(MyEntity.class, id);

// After
session.persist(entity);            // transient → managed
MyEntity managed = session.merge(entity); // detached → managed; USE THE RETURN VALUE
session.remove(entity);
MyEntity ref = session.getReference(MyEntity.class, id); // was load
T t = session.find(MyEntity.class, id);                  // prefer over get
```

| Old | Replacement |
|-----|-------------|
| `save` | `persist` |
| `update` / `saveOrUpdate` | `merge` (or `persist` if still transient) |
| `delete` | `remove` |
| `load` | `getReference` |
| `get` | prefer `find` (still present but deprecated toward JPA) |

### Receiver-aware Session search

Grep proposes candidates. Rewrite a hit only after the receiver is a Hibernate `Session` or `StatelessSession` (the declared type, not a name that happens to contain `session`).

```text
rg -n '\.(save|update|saveOrUpdate|delete|load)\(' src/main src/test
```

Leave these alone:

- `JpaRepository.save`, `saveAll`, `delete`, `deleteAll` (Spring Data — not `Session.save` / `Session.delete`)
- domain or service methods named `save`, `update`, `delete`, `merge`, or `load`
- `EntityManager.persist` / `merge` / `remove` (already JPA)

A method named `merge` on a repository or domain type is not the Hibernate `Session.merge` replacement and is not a signal to switch call sites.

Cascade enums (Hibernate `@Cascade` / `CascadeType` — fully deprecated in 7):

```java
// Before
CascadeType.SAVE_UPDATE
CascadeType.DELETE

// After
CascadeType.PERSIST and/or CascadeType.MERGE
CascadeType.REMOVE
```

**Detach + cascade trap (H7):** adding a **detached** child to a managed parent with `cascade = ALL|PERSIST` now throws `EntityExistsException` at flush. Merge the child first (or `getReference`), then associate the managed instance.

```java
// Before — often “worked” under SAVE_UPDATE semantics
parent.addChild(detachedChild);

// After
Child merged = session.merge(detachedChild);
parent.addChild(merged);
```

Refresh / lock on **detached** entities: no longer allowed (and `hibernate.allow_refresh_detached_entity` was removed). Reattach via `merge` / `find` first.

`@Id` / `@MapsId` associations no longer auto-cascade `PERSIST` — add `cascade = PERSIST` explicitly if the old implicit behavior was required.

### Removed / replaced mapping annotations (H7)

```java
// Before
@Where(clause = "deleted = false")
@WhereJoinTable(clause = "…")
@OrderBy("name asc")                 // org.hibernate.annotations.OrderBy
@Proxy(lazy = false)
@LazyCollection(LazyCollectionOption.EXTRA)
@LazyToOne(LazyToOneOption.NO_PROXY)
@SelectBeforeUpdate
org.hibernate.annotations.Table / @Index / @ForeignKey / @IndexColumn
@Target(SomeEmbeddableImpl.class)

// After
@SQLRestriction("deleted = false")
@SQLJoinTableRestriction("…")
@SQLOrder("name asc")                // or jakarta.persistence.OrderBy
// drop @Proxy — use find / FetchType / EntityGraph / @FetchProfile / bytecode laziness
// drop @LazyCollection / @LazyToOne — model fetch explicitly
// drop @SelectBeforeUpdate (tied to removed update semantics)
jakarta.persistence.Table / Index / ForeignKey / OrderColumn
@TargetEmbeddable(SomeEmbeddableImpl.class)  // only on @Embedded / @ElementCollection
```

### Lazy associations in `@SpringBootTest` / Cucumber (Hibernate 7)

After an HTTP request (MockMvc, Rest Assured, etc.), the server-side persistence context is closed. Tests or Cucumber steps that `repository.findBy…()` then read `@ManyToOne(fetch = LAZY)` (e.g. `entity.parent.child.getBarcode()`) often fail with `LazyInitializationException` where older Hibernate tolerated incidental loads.

**Pre-inventory, before any `@EntityGraph`:**

1. Grep `src/test` for the lazy association accessors tests actually call (the entity’s getter, plus generic shapes such as `getParent` and `.parent.`).  
2. For each hit, name the repository `findBy*` (or `@Query`) method that loaded the entity.  
3. That list is the edit set. Annotate every finder on it, including two-level paths. Do not annotate the first method that threw and leave the rest.

```text
rg -n 'getParent|\.parent\.' src/test
```

Use the service’s real accessor names in the same search. Then:

```kotlin
@EntityGraph(attributePaths = ["parent", "parent.parent"])
fun findByBusinessKey(key: String): Optional<ChildEntity>

@EntityGraph(attributePaths = ["parent", "parent.parent"])
fun findByLabel(label: String): List<ChildEntity>
```

`attributePaths` must be the entity’s real attribute names, not this sample. Annotating one finder while steps call another leaves latent `LazyInitializationException`s. Alternatives: `@Transactional(readOnly = true)` on a narrow test method, or assert on FK columns / DTOs — avoid global `EAGER` on production entities.

Also removed (delete or replace): `@Persister`, `@Loader`, `@GeneratorType`, `@Columns` (7.3), `CacheModeType` → `CacheMode`, `@Cache#include` → `@Cache#includeLazy`.

### TypeDef / custom enum type removal (H6 removed string `@TypeDef`; H7 still breaks leftover defs)

```java
// Before
@TypeDef(name = "jsonb", typeClass = JsonBinaryType.class)
@TypeDef(name = "pgsql_enum", typeClass = CustomPostgreSQLEnumType.class)
@TypeDef(typeClass = MonetaryAmountType.class, defaultForType = MonetaryAmount.class)

@Enumerated(EnumType.STRING)
@Type(type = "pgsql_enum")
private MyEnum status;

// After — delete CustomPostgreSQLEnumType / TypeDefs entirely (dead MonetaryAmountType defs still break on *-73)
@Enumerated(EnumType.STRING)
@JdbcTypeCode(SqlTypes.NAMED_ENUM) // or VARCHAR strategy used by the service
private MyEnum status;
```

Prefer `@JdbcTypeCode(SqlTypes.…)` over `@JdbcType(SomeInternalJdbcType.class)` — several PostgreSQL/Oracle JDBC type classes moved **internal** in H7.

Custom `UserType` / `CompositeUserType`: `nullSafeGet` / `nullSafeSet` signatures changed (session implementor no longer leaked the same way). Recompile against H7; prefer `@JdbcTypeCode` + converters when possible. Auto-applied `AttributeConverter` on `@Id` / `@Version` / `@Enumerated` / associations / `@Embedded` / `@Temporal` now **errors** (was ignored) — use `@Convert(disableConversion = true)` or remove the converter.

### JSON: Map *or* typed POJO

```java
// Before
@Type(type = "jsonb")
private JSONObject metadata;
@Type(type = "jsonb")
private SomeDto payload;

// After
@JdbcTypeCode(SqlTypes.JSON)
private Map<String, Object> metadata;
@JdbcTypeCode(SqlTypes.JSON)
private SomeDto payload; // POJO OK if the JSON stack can bind it
```

If DTOs/API still use `JSONObject` while entities use `Map`, add a small MapStruct `uses` helper at the edge (`JSONObject` ↔ `Map`) — pair with Jackson `JsonOrgModule` for HTTP JSON ([04-jackson-3.md](04-jackson-3.md)).

`hypersistence-utils-hibernate-73` **3.16.0** binds JSON with Jackson 3 (`tools.jackson`). Do not add `jackson-databind` 2.x for it, and do not treat that artifact as library-owned Jackson 2 in phase 04. Keeping `@Type(JsonBinaryType)` does not by itself require a Jackson 2 bridge or a switch to `@JdbcTypeCode`.

On Boot 4 + Jackson 3, if Hibernate JSON binding must use Jackson 3 explicitly:

```yaml
spring.jpa.properties.hibernate.type.json_format_mapper: jackson3
# or FQCN: org.hibernate.type.format.jackson.Jackson3JsonFormatMapper
```

XML `FormatMapper` portable format changed in H7 — if columns store XML collections/maps/byte[], either re-read/re-save data or set `hibernate.type.xml_format_mapper.legacy_format=true` temporarily (`ASK_HUMAN` for stored shape).

### Assigned UUID + Persistable (drop custom generator)

```java
// Before
@Id
@GeneratedValue(generator = "uuid")
@GenericGenerator(name = "uuid", strategy = "...CustomUUIDGenerator", /* params */)
private UUID id;

// After — delete the custom generator class
@Id
private UUID id; // assigned by app / mapper

// entity implements Persistable<UUID>:
@Transient
@Builder.Default
private boolean newEntity = true;

@Override
public boolean isNew() {
  return newEntity;
}

@PostLoad
@PostPersist
void markNotNew() {
  newEntity = false;
}
```

Required when Spring Data treats pre-set IDs as existing and skips insert. Do **not** invent a new generator or reintroduce `@UuidGenerator` / `@GeneratedValue` without a proven cascade/`isNew` story (`ASK_HUMAN`).

From H5/H6: UUID DDL default is `SqlTypes.UUID` (native `uuid` or `binary(16)`). Schema validation may fail on older `varchar` UUID columns — fix mapping or DDL with approval ([08-flyway-db.md](08-flyway-db.md)).

Custom `Configurable` generators: migrate `configure(…)` to the `GeneratorCreationContext` overload (or `@IdGeneratorType`). Mixing `GenerationType.SEQUENCE` with non-`@SequenceGenerator` (and TABLE vs `@TableGenerator`) is now a hard error.

### Hypersistence write API (`update` → `merge`)

On Hibernate 7, Hypersistence `update()` goes through **StatelessSession** and can fight managed graphs / `@Version` (optimistic-lock / double-write symptoms). Call sites that mutate already-managed entities (status writes, cascade saves) should use **`merge`**, not `update`.

```java
// Before
repo.update(entity);

// After — prefer the API your Spring Data / Hypersistence line provides
repo.merge(entity);
```

Do not invent a custom merge helper if `BaseJpaRepository` already exposes `merge`. Prefer repository APIs available on the Boot 4 / Spring Data line.

**StatelessSession (H7):** second-level cache is **on by default**. Restore old bypass with `setCacheMode(CacheMode.IGNORE)` (or `GET` / `jakarta.persistence.cache.storeMode=BYPASS` for bulk). `hibernate.jdbc.batch_size` no longer batches StatelessSession — use `setJdbcBatchSize` or `insertMultiple` / `updateMultiple` / `deleteMultiple`.

### Hypersistence coordinates

```text
Before: hypersistence-utils-hibernate-55 / 63 / 71 / …
        or com.vladmihalcea:hibernate-types-52 / 60
After:  io.hypersistence:hypersistence-utils-hibernate-73
        (catalog pin e.g. 3.16.0 — covers Hibernate 7.3 and 7.4)
```

Also rename packages if still on Hibernate Types 2.x: `com.vladmihalcea.hibernate` → `io.hypersistence.utils.hibernate` (and `com.vladmihalcea.spring` → `io.hypersistence.utils.spring`).

Patch bumps **after** the service is on `*-hibernate-73` go through [12-dependency-bump-queue.md](12-dependency-bump-queue.md).

### Queries, Criteria, native SQL

```java
// Before — ambiguous implicit select (rejected harder in H7)
session.createQuery("from X join y").getResultList();

// After
session.createQuery("from X join y", X.class).getResultList();
// or explicit select list / Object[].class / alias this
```

```java
// Before — Criteria path into inheritance subtype attribute (implicit treat)
path.get("subtypeOnlyAttribute");

// After
cb.treat(path, Subtype.class).get("subtypeOnlyAttribute");
```

```java
// Before — native query temporal columns → java.sql.Date / Timestamp
// After — default java.time (LocalDate / LocalTime / LocalDateTime)
// recover: hibernate.query.native.prefer_jdbc_datetime_types=true
```

```java
// Before — H5 update syntax
"update from MyEntity e set e.attr = null"

// After
"update MyEntity e set e.attr = null"
```

`getSingleResult()` / `getSingleResultOrNull()` (**H7.3+**): always throw when the list has **more than one** row (no silent dedupe). If duplicates are expected:

```java
query.setResultListTransformer(ResultListTransformer.uniqueResultTransformer());
```

Pagination / limit **with collection fetch** (**H7.4+**): limit is applied in SQL. Old in-memory limit: query hint `org.hibernate.limitInMemory`.

Immutable entities: bulk update/delete now **fail by default**. Temporary escape (prefer fixing the query):

```properties
hibernate.query.immutable_entity_update_query_handling_mode=allow
```

Read-only entities (**H7.3+**): collections are read-only too — mutating them errors.

Timeout when the DB marks the tx rollback-only (**H7.3+**): may surface as `PersistenceException` instead of `QueryTimeoutException` / `LockTimeoutException` — update catch blocks.

Locking: prefer `find`/`refresh`/`lock` options (`LockMode`, `Timeout`, …) over building `LockOptions` (deprecated; alias-specific lock modes removed in 7.1).

### Domain validation / access (stricter in H7)

Illegal now (examples):

- Multiple attribute types on one field (`@Basic` + `@ManyToOne`, `@Lob` + association, …)
- Property annotations under FIELD access (and the reverse) — previously often ignored
- JavaBean oddities such as `@Basic String isDefault()`
- Converters on incompatible attributes (see TypeDef section)

Misplaced annotations fail bootstrap — fix placement; do not silence with DDL tricks.

### Bootstrapping / settings / dialects (H5→H6 leftovers that still bite on H7)

| Signal | Action |
|--------|--------|
| `javax.persistence.*` settings / orm.xml | → `jakarta.persistence.*` ([02-jakarta-ee.md](02-jakarta-ee.md)) |
| `PostgreSQL95Dialect` / versioned dialects | → `PostgreSQLDialect` (let JDBC metadata pick version) |
| Community dialects on old artifact | Move to `hibernate-community-dialects` or new FQCN (e.g. Spanner PG dialect moved into core in 7.4) |
| `hibernate.multiTenancy` / `MultiTenancyStrategy` | Removed — drop; use current multi-tenant connection provider APIs |
| Implicit `@GeneratedValue` / shared `hibernate_sequence` | H6+ uses per-entity `*_seq` and allocation size **50** by default; set `hibernate.id.db_structure_naming_strategy=legacy` (or `single`) only with human OK + Flyway alignment |
| `@SequenceGenerator` only on one subclass of a `@MappedSuperclass` | Metadata does not cover siblings that share the sequence. See the mapped-superclass section below |
| Standalone entity scan | May need `hibernate-scan-jandex` |
| `ValidationMode.AUTO` + broken BV factory | Exception now **propagates** (was swallowed) |
| Accidental `import.sql` on classpath | H7.3+/7.4 run schema actions even with **zero** entities — remove stray import.sql |
| MySQL fetch depth | H7.4 removed dialect default `hibernate.max_fetch_depth=2` — set explicitly if relied on |

### Mapped superclass sequence metadata (`allocationSize` vs database increment)

Hibernate’s default `allocationSize` is **50** when generator metadata is missing. A `@SequenceGenerator` on **one subclass** does not apply to other entities that inherit the id from a `@MappedSuperclass` and share that database sequence. Those siblings allocate with the default 50 while the sequence advances by its own **INCREMENT**.

1. List every `@MappedSuperclass` and every subclass that uses the same `sequenceName`.  
2. Read the sequence **INCREMENT** from existing DDL / Flyway. Do not assume 50, and do not assume 1.  
3. Put one `@SequenceGenerator` on the mapped superclass. Remove the duplicate on the subclass.  
4. Set `allocationSize` to that database increment. The two values must match. A mismatch either collides with values the sequence will issue or opens large gaps.

```java
// Before — metadata only on one subclass; other subclasses of BaseEntity
// that share shared_seq keep Hibernate's default allocationSize (50)
@MappedSuperclass
public abstract class BaseEntity {
  @Id
  private Long id;
}

// After — one generator on the mapped superclass.
// allocationSize is the database sequence INCREMENT (read from DDL; not a default).
@MappedSuperclass
public abstract class BaseEntity {
  @Id
  @SequenceGenerator(name = "shared_seq", sequenceName = "shared_seq", allocationSize = /* DB INCREMENT */)
  @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "shared_seq")
  private Long id;
}
```

This is `ASK_HUMAN`. Do not change the sequence INCREMENT in Flyway to match Hibernate, and do not set `allocationSize = 50` because that is the provider default. Coordinate DDL with [08-flyway-db.md](08-flyway-db.md).

### DDL generation (only if schema is Hibernate-managed — usually **not** for fleet Flyway services)

Ask human before any DDL ([08-flyway-db.md](08-flyway-db.md)). Behavioral notes if `ddl-auto` / test schema export is used:

- Oracle / SQL Server default timestamp precision changed; Oracle `float`/`double` → `binary_float`/`binary_double` (`hibernate.dialect.oracle.use_binary_floats=false` to keep old)
- Basic arrays: XML/JSON array types on several dialects (escape: `hibernate.type.preferred_array_jdbc_type=VARBINARY`)
- `char`/`Character` → `varchar(1)` by default
- H7.1+: check constraints for `optional=false` subclass columns in SINGLE_TABLE
- H7.3+: `@Version` columns `not null` by default; H7.4+: `@CreationTimestamp`/`@UpdateTimestamp` and `@ElementCollection` set unique constraints tightened
- Oracle 23c+ value-based LOBs may need `hibernate.dialect.oracle.value_lob_enabled=false` if ORA-43853 / ORA-00600

### Bytecode enhancement / Maven plugin

```xml
<!-- After (Hibernate 7+) -->
<plugin>
  <groupId>org.hibernate.orm</groupId>
  <artifactId>hibernate-maven-plugin</artifactId>
  <!-- version from Boot BOM / Hibernate release -->
  <executions>
    <execution>
      <goals><goal>enhance</goal></goals>
    </execution>
  </executions>
</plugin>
```

Gradle: `hibernate { enhancement {} }` (empty block required in 7.1+ default setup). Do not re-enhance the same class with different options (`FeatureMismatchException`). Bidirectional association management / “extended” enhancement are deprecated — manage both sides in code.

### Interceptor / Integrator SPI

Remove calls to deleted `Interceptor` overloads that still used `Serializable` ids; implement `Interceptor` directly (`EmptyInterceptor` removed). `Integrator#integrate(Metadata, SessionFactoryImplementor, …)` → `integrate(Metadata, BootstrapContext, SessionFactoryImplementor)`.

## Steps

1. Confirm Boot line → Hibernate version from BOM (4.0→7.2, 4.1→7.4); do not override `hibernate-core` without approval. Record the matrix row as inference until resolution shows the artifact.  
2. Fill the consumer-first table. Zero field consumers → delete dead `@TypeDef` registrations and the unused type library. Consumers present → migrate to `hypersistence-utils-hibernate-73` (catalog pin) or stop on the conditions above. Do not add `*-73` to keep an unused registration.  
3. Replace Session `save`/`update`/`saveOrUpdate`/`delete`/`load` only after the receiver-aware search. Fix Hibernate cascade enums and detach+persist graphs. Leave `JpaRepository.save` / `delete` and domain `merge` methods unchanged.  
4. Rewrite removed annotations (`@Where`→`@SQLRestriction`, etc.); fix `@Target`→`@TargetEmbeddable`.  
5. Remove `@TypeDef` / custom enum UserTypes / dead `MonetaryAmountType` defs; annotate fields with `@JdbcTypeCode` only where a field still needs a type.  
6. Replace entity `JSONObject` with `Map` **or** keep typed POJO + `@JdbcTypeCode(JSON)`; add MapStruct edge helper if DTOs still use `JSONObject`; set Jackson 3 format mapper if needed ([04-jackson-3.md](04-jackson-3.md)).  
7. Grep `BaseJpaRepository.update(` → prefer `merge` for managed / `@Version` graphs; **ASK_HUMAN** if behavior is unclear. Review `StatelessSession` cache mode for bulk paths.  
8. For assigned UUIDs: drop custom `UUIDGenerator`; implement `Persistable` (do not restore `@GeneratedValue` without proof).  
9. Fix Criteria subtype paths (`treat`), ambiguous HQL `createQuery`, native temporal types, immutable bulk updates, and `getSingleResult` duplicate handling. Leave native query text, custom `EntityManagerFactory`, and repository API renames to [33](33-jpa-spring-data.md).  
10. Drop versioned dialects / dead multi-tenancy settings. For a shared sequence on a `@MappedSuperclass`, align `allocationSize` with the database INCREMENT (`ASK_HUMAN`, [08](08-flyway-db.md)).  
11. Update enhance plugin coordinates if used; fix custom `Interceptor` / `Integrator` / `UserType` compile breaks.  
12. If tests traverse lazy associations, run the pre-inventory and then add `@EntityGraph` on every listed finder. Do not start with the first failing method.  
13. Ask human before changing DB migration scripts ([08-flyway-db.md](08-flyway-db.md)).

## Do not

- Change DDL casually to “make Hibernate happy” without approval.  
- Keep `JSONObject` entity fields if the dialect rejects them — fix the type.  
- Leave `BaseJpaRepository.update` on versioned managed entities after the H7 cutover.  
- “Fix” assigned-UUID inserts by reintroducing `CustomUUIDGenerator` / `@GeneratedValue` without verifying `isNew` / cascades.  
- Bump Hypersistence `55`/`63`/`71` → `73` inside the lagging dependency queue instead of this phase.  
- Force a Hibernate version ahead of / behind the Boot BOM (e.g. forcing 7.3 on Boot 4.0) without a documented spike — Boot 4.0 historically hit introspect/StackOverflow issues on some 7.3 builds.  
- Re-enable detached `refresh`/`lock` via removed settings.  
- Blindly set `immutable_entity_update_query_handling_mode=allow` or `xml_format_mapper.legacy_format=true` as permanent fixes.  
- Add `hypersistence-utils-hibernate-73` when no field consumes the registered type — delete the dead registration and the old coordinate instead.  
- Rewrite `JpaRepository.save` / `delete`, or a domain method named `merge`, because a Session-method grep matched the name.  
- Set `allocationSize` without reading the database sequence INCREMENT, or leave generator metadata only on one subclass of a shared `@MappedSuperclass`.  
- Add `@EntityGraph` before the test-glue finder inventory is complete.  
- Edit native SQL, a custom `EntityManagerFactory`, the metamodel processor, or Spring Data repository APIs in this phase.

## Risk

`SAFE_AUTO` for deleting dead `@TypeDef` registrations with zero field consumers, an approved Hypersistence coordinate-only bump when the existing field mapping is unchanged and no custom `UserType` is involved, straightforward annotation renames, and Session API renames whose receiver is actually a `Session`.
`ASK_HUMAN` for Persistable cutover, `update`→`merge` on versioned graphs, native queries, JSON/XML column shape changes, sequence naming strategy, **`allocationSize` vs the database INCREMENT** on a mapped superclass, any Flyway/DDL, and exception-type changes in timeout handlers.
`SPIKE_FIRST` for a live custom `UserType`, a custom generator that will not compile, inventing a new ID strategy instead of Persistable, or Envers → core `@Audited` migration (optional in 7.4 — Envers still works; do not migrate unless requested).

## Rollback

Revert entity/type/Session-API commits; keep Boot 4 if platform phase already landed. Hypersistence coordinate can roll back with the same commit set if still binary-compatible with the previous Hibernate line (usually not after H7 — expect a paired revert).

## Done when

JPA entities compile against Boot-managed Hibernate 7.x; no leftover `@TypeDef` / removed annotations / receiver-confirmed `Session.save|update|delete|load` in first-party code; unused type libraries removed, or Hypersistence on `*-hibernate-73` when a field still needs it; shared sequences on a mapped superclass have `allocationSize` equal to the database INCREMENT when that shape exists; lazy finders were pre-inventoried before any `@EntityGraph`. Smoke repository tests (if present) pass or the compile-only gate is green. `bootHibernate=7.4` from the matrix is not an observed resolved version.

## Handoff

`hibernate7=ok; bootHibernate=7.2|7.4|other; bootHibernateSource=matrix|resolved; typeLibrary=removed-dead|migrated|n/a; jsonStrategy=Map|POJO|mixed|n/a; uuidStrategy=assigned+Persistable|generator|n/a; writeApi=merge|update|save; sessionApi=migrated|n/a; sequenceMetadata=superclass-aligned|n/a|asked; lazyFinders=pre-inventoried|n/a; askedHuman=yes|no`
