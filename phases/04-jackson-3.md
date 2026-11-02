# 04 — Jackson 3

## Detect

Any of:

- `spring-boot-jackson2`
- `com.fasterxml.jackson.databind.ObjectMapper` (Jackson 2 package) in first-party code (services, Feign helpers, tests)
- `Jackson2ObjectMapperBuilderCustomizer` / FQCN under `org.springframework.boot.autoconfigure.jackson`
- `@JsonComponent` / `@JsonMixin` (Boot 3 Jackson annotations)
- `com.fasterxml.jackson.datatype:jackson-datatype-json-org` (Jackson 2 group)
- Boot 4 app still preferring Jackson 2 via `spring.http.converters.preferred-json-mapper=jackson2`
- Test/IT force-pins of `com.fasterxml.jackson.core:*` / `jackson-databind` to a 2.x version (common under older WireMock + Boot 2.7 BOM)

### Inventory before editing

```bash
rg -n 'com\.fasterxml\.jackson|tools\.jackson|ObjectMapper|JsonMapper|JsonComponent|JsonMixin|JacksonComponent|JacksonMixin' \
  --glob '*.java' --glob '*.kt' .
```

Classify each hit:

| Kind | Action |
|------|--------|
| HTTP serialization (MVC / WebFlux / Feign converters) | Own with Boot’s Jackson 3 `JsonMapper` |
| Application-injected mapper | Inject `JsonMapper` (or format-specific mapper) |
| Library-owned mapper | Upgrade/replace the library before the Boot 4 cutover; Jackson 2 is a blocker |
| Format-specific (XML, etc.) | Customize the **format-specific** mapper — a generic `ObjectMapper` bean does **not** necessarily replace Boot’s JSON/XML auto-config |
| Custom module / serializer / mixin / annotation | Align module major with the mapper that uses it |

### Mapper buckets (who builds the mapper)

Sort every mapper construction or injection into one bucket before editing. The bucket decides which defaults apply and whether Boot's `spring.jackson.*` / customizers reach it.

| Bucket | Typical signals | Defaults that apply | Migration |
|--------|-----------------|---------------------|-----------|
| **Bare** | `new ObjectMapper()`, `JsonMapper.builder().build()`, a static `MAPPER` field | Plain Jackson 3 defaults; Boot properties and customizers do **not** apply | Rebuild with `JsonMapper.builder()`; re-apply each feature the old code set; baseline it separately |
| **Kotlin helper** | `jacksonObjectMapper()`, `jsonMapper { }`, `ObjectMapper().registerKotlinModule()` | Jackson 3 defaults + Kotlin module; Boot settings do **not** apply | Move imports to `tools.jackson.module.kotlin`; use the builder form (`jsonMapper { addModule(kotlinModule()) }`) instead of registering on a built mapper |
| **Injected / shared** | Constructor-injected `ObjectMapper` / `JsonMapper`, a shared holder or test base exposing Boot's bean | Boot-configured `JsonMapper` (properties + customizers) | Inject `JsonMapper`; put feature changes in `JsonMapperBuilderCustomizer`, not at call sites |

A service often has all three. Do not "fix" a bare or helper mapper by making it inherit Boot's settings unless the baseline shows the outputs were already identical; that silently changes its wire output.

```bash
rg -n 'new ObjectMapper\(|JsonMapper\.builder\(|jacksonObjectMapper\(|jsonMapper \{|registerKotlinModule|ObjectMapper\(\)' \
  --glob '*.java' --glob '*.kt' src
```

### Immutable mappers and feature handling

Jackson 3 mappers are immutable once built. Code that changed a live mapper (`configure(...)`, `enable(...)`, `disable(...)`, `registerModule(...)`, `setSerializationInclusion(...)`) does not compile or has no effect. Move every such call onto the builder.

```java
// Before (Jackson 2 — mutate after construction)
ObjectMapper m = new ObjectMapper();
m.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
m.registerModule(new JavaTimeModule());

// After (Jackson 3 — configure the builder, then build once)
JsonMapper m = JsonMapper.builder()
    .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
    .build();

// Derive a variant from an existing mapper without mutating it
JsonMapper lenient = shared.rebuild()
    .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
    .build();
```

- Some feature enums moved in Jackson 3 (for example, date/time features have their own enum). Resolve each one against the Jackson 3 release notes for the target patch; do not guess the new type from the old name.
- Java time support is built into Jackson 3 databind; drop explicit `JavaTimeModule` registration unless the target patch documents otherwise.
- Several Jackson 3 defaults differ from Jackson 2. For each bucket, list the features the old code set **and** the ones it relied on by default, then confirm the Jackson 3 default for each. The wire baseline below is the evidence, not the feature list.
- For an injected mapper, change features in one `JsonMapperBuilderCustomizer`. Do not `rebuild()` Boot's bean at call sites to change global behavior.

## Before → After

### Dependencies

```gradle
// Before
implementation 'org.springframework.boot:spring-boot-jackson2'
implementation 'com.fasterxml.jackson.datatype:jackson-datatype-json-org'

// After
// rely on Boot's Jackson 3 via spring-boot-starter-json / web
implementation 'tools.jackson.datatype:jackson-datatype-json-org' // only if org.json types need it
```

```xml
<!-- Maven: remove spring-boot-jackson2; use tools.jackson.* modules as needed -->
```

There is no Boot 4 + Jackson 2 bridge in this workflow. If an upstream library requires Jackson 2 databind, upgrade/replace it or defer the Boot 4 migration. Do **not** invent a bean named `objectMapper` just to satisfy injection; identify the required Jackson major and fix the dependency.

### Config customizer + component annotations

Boot 4 customizer type lives under `org.springframework.boot.jackson.autoconfigure`.

```java
// Before
import org.springframework.boot.autoconfigure.jackson.Jackson2ObjectMapperBuilderCustomizer;
// often: builder.serializerByType(JSONObject.class, new JSONObjectSerializer())
//        + deserializerByType(JSONObject.class, new JSONObjectDeserializer())
@JsonComponent
@JsonMixin(MyType.class)

@Bean
Jackson2ObjectMapperBuilderCustomizer customizer() {
  return builder -> builder.serializerByType(JSONObject.class, new JSONObjectSerializer());
}

// After
import org.springframework.boot.jackson.autoconfigure.JsonMapperBuilderCustomizer;
import tools.jackson.datatype.jsonorg.JsonOrgModule;
@JacksonComponent
@JacksonMixin(MyType.class)

@Bean
JsonMapperBuilderCustomizer customizer() {
  return builder -> builder.addModule(new JsonOrgModule());
}
```

MapStruct helpers that convert `JSONObject` ↔ `Map` stay on the org.json side; pair them with `JsonOrgModule` for HTTP JSON — that is not a second Jackson stack.

### Injection type (all first-party call sites)

```java
// Before
import com.fasterxml.jackson.databind.ObjectMapper;
private final ObjectMapper objectMapper;

// After (recommended for JSON)
import tools.jackson.databind.json.JsonMapper;
private final JsonMapper jsonMapper;
// Jackson 3 also has tools.jackson.databind.ObjectMapper — prefer JsonMapper for HTTP JSON
```

`JsonMapper` is what Boot 4 auto-configures for JSON. Grep and rewrite injections in services, controllers, Feign helpers, **and** unit/IT bases — not only the `@Configuration` class.

### Exceptions / Lombok

```java
// Before
} catch (JsonProcessingException e) { ... }
@SneakyThrows(JsonProcessingException.class)
public String write(...) { return objectMapper.writeValueAsString(...); }

// After
} catch (JacksonException e) { ... }
// JacksonException is unchecked — remove unnecessary @SneakyThrows / throws clauses
public String write(...) { return jsonMapper.writeValueAsString(...); }
```

### Packages

| Keep | Move |
|------|------|
| `com.fasterxml.jackson.annotation.*` | `com.fasterxml.jackson.core/databind` → `tools.jackson.*` |

### JsonPath (tests)

Boot 4.1 may still manage JsonPath 2.x. For Jackson 3 providers:

```gradle
ext { set('json-path.version', '3.0.0') } // or Maven property equivalent
```

```java
// Before
new JacksonJsonProvider(objectMapper, ...)
new JacksonMappingProvider(objectMapper)

// After
new Jackson3JsonProvider(jsonMapper)
new Jackson3MappingProvider(jsonMapper)
```

### Test classpath pins

```gradle
// Before (Boot 2.7-era — force Jackson 2 under WireMock / BOM)
configurations.testRuntimeClasspath {
  resolutionStrategy.force 'com.fasterxml.jackson.core:jackson-databind:2.17.1'
}

// After — remove force pins; let Boot 4 manage Jackson 3
```

### Properties / defaults

| Before | After |
|--------|--------|
| `spring.jackson.read.*` / `spring.jackson.write.*` | JSON-specific keys under `spring.jackson.json.*` (confirm via [18-config-properties.md](18-config-properties.md) / Boot changelog) |
| Need Boot 3-like defaults | `spring.jackson.use-jackson2-defaults=true` **only** if the Boot patch documents it and a human asks for parity |

Keep Jackson 3 defaults (including stricter trailing-token checks) unless wire-contract evidence requires compatibility. `use-jackson2-defaults` configures the Jackson 3 mapper; it is not permission to add Jackson 2.

### Wire-contract baseline (before → after)

Compilation finds package/API breaks; it does not find changed JSON. Before editing, capture representative request, response, message, and persisted-JSON fixtures on the current stack. After the direct cutover, serialize the same values with Boot's Jackson 3 `JsonMapper` and compare semantic values.

**Pre-edit baseline.** [42-baseline.md](42-baseline.md) captures it in Stage 0 on the unmodified pre-migration commit, before any Jackson or Boot edit, and stores it under `.joker/java-spring-migration/baseline/` (never committed). This phase reads it. Run one probe case per mapper bucket above, because a bare mapper and Boot's bean can already differ on the old stack. A baseline captured after edits begin is not a baseline; if that happens, recapture from the pre-migration commit.

**Unknown properties and enums.** Add probe cases that record what each mapper does today, then compare after the cutover:

- deserialize a payload carrying an extra, unknown property;
- deserialize an enum value the type does not declare, and the declared value in its wire form (name, `toString()`, or `@JsonValue`);
- serialize each enum through the same mapper the boundary uses.

Assert only the mapper outcome (parsed value, ignored field, or the Jackson exception type). Do not encode service behavior such as the HTTP status, error body, or retry/DLQ handling that follows; that belongs to the service's own tests and may legitimately differ by endpoint. A changed outcome is a wire diff to fix on the Jackson 3 mapper or to record as an approved diff.

Prioritize:

- enums that override `toString()` or use `@JsonValue`, including enum map keys;
- `Duration`, `Year`, `Month`, `Date`, and API-visible Java time values;
- custom serializers/deserializers and types imported from internal JARs;
- every hand-built mapper (`new ObjectMapper`, static JSON helpers, Pub/Sub/Feign converters), not only Boot's mapper;
- byte-sensitive consumers (signatures, hashes, snapshots) where property order matters.

Use literal JSON assertions for each risky value. A reusable probe may print `case-name<TAB>json` on the old and new classpaths for diffing. Source grep is insufficient for shared DTOs: inspect compiled classes or dependency JARs when risk can arrive through an internal artifact. Confirm that a flagged type actually reaches an HTTP/message/persistence boundary before changing global mapper features.

Restore compatibility on the Jackson 3 mapper with an explicit feature/customizer or a stable annotation such as `@JsonValue`; do not restore Jackson 2. Record intentional wire changes as a versioned API decision.

**What `wireContracts=green` means.** Every probe case in the pre-edit inventory produced the same semantic JSON (and the same unknown-property/enum outcome) on the Jackson 3 classpath as in the baseline, for every mapper bucket. It is a static serialization statement about the cases inventoried. It does not claim that deployed consumers, unlisted DTOs, or runtime traffic were verified. Use `approved-diff` when a human accepted a recorded difference, and `blocked` when no pre-edit baseline exists or a diff is unresolved.

## Steps

1. Inventory and classify mapper usages (both tables above). Stage 0 already did this to capture the pre-edit wire baseline per mapper bucket, including unknown-property and enum cases; confirm every bucket has a baseline case and stop (`wireBaseline=missing`) if one does not.  
2. Remove `spring-boot-jackson2`, `spring.jackson2.*`, and any `preferred-json-mapper=jackson2` in the same cutover. Block on incompatible upstream libraries rather than bridging.
3. Rewrite first-party imports to `tools.jackson` (except annotations), including Feign helpers and tests.  
4. Switch `@JsonComponent`/`@JsonMixin` → `@JacksonComponent`/`@JacksonMixin`; customizers to `JsonMapperBuilderCustomizer` + `JsonOrgModule` when needed.  
5. Inject `JsonMapper`; rename fields/usages; drop `@SneakyThrows(JsonProcessingException)` / checked throws. Move post-construction `configure` / `enable` / `registerModule` calls onto builders (or `rebuild()`) per bucket.  
6. Align JsonPath to 3.x when tests use Jackson providers.  
7. Remove test/IT Jackson 2 force-aligns.  
8. Bump `jackson-databind-nullable` to a release that supports Jackson 3 (≥ 0.2.10) if OpenAPI nullable is used.  
9. Run the before/after wire probe and literal contract tests through HTTP/message paths plus directly constructed mappers; record reviewed diffs.

## Do not

- Ship a dual application JSON stack (Jackson 2 bridge + Jackson 3).
- Run Boot 4 application JSON through `spring-boot-jackson2`, even temporarily.
- Assume a Jackson 2 `ObjectMapper` bean replaces Boot’s Jackson 3 `JsonMapper` for HTTP.  
- Mutate a mapper instance after build (`registerModule` on a live immutable mapper) — use `JsonMapperBuilderCustomizer` or `mapper.rebuild()`.  
- Merge a bare or Kotlin-helper mapper into Boot's settings without a baseline showing identical output.  
- Capture the wire baseline after edits begin, or report `wireContracts=green` without one.  
- Assert HTTP status, error bodies, or retry handling in mapper probes.  
- Reintroduce WireMock/BOM Jackson 2 force-pins on a Jackson 3 app.  
- Add `feign-jackson3` blindly — see [06-http-clients.md](06-http-clients.md).

## Risk

`SAFE_AUTO` for import/customizer/injection cutover when contract evidence is unchanged.
`ASK_HUMAN` for intentional wire-format changes. Jackson 2 required by application runtime/test code is `blocked`, not a bridge option.

## Rollback

Revert the Boot 4/Jackson 3 migration commit or MR as a unit. Do not create a Boot 4 + Jackson 2 rollback state.

## Done when

No first-party `com.fasterxml.jackson.databind` usage; no `spring-boot-jackson2`, `spring.jackson2.*`, or Jackson 2 test force-pins; the latest compile shows no errors owned by this phase; no post-build mapper mutation; the pre-edit baseline exists for every mapper bucket and the wire-contract probe/tests were reviewed with every change accepted or corrected.

## Handoff

`jackson3=sole; jsonMapperInjected=yes; jsonOrgModule=yes|no; mapperBuckets=bare:N,kotlinHelper:N,injected:N; wireBaseline=pre-edit|missing; wireContracts=green|approved-diff|blocked; handBuiltMappers=[…]; wiremockJacksonPins=removed|n/a`
