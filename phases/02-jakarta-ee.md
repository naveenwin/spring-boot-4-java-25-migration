# 02 — Jakarta EE namespace

## Detect

Any `javax.persistence`, `javax.validation`, `javax.servlet`, or non-JDK `javax.annotation` imports remain in first-party sources **or** path is Boot 2.7→4.

Skip if intake confirms clean `jakarta.*` already (typical Boot 3→4).

Order when several phases apply: this namespace commit first, Hibernate mappings in [03-hibernate-7.md](03-hibernate-7.md) second, Spring Data and native queries in [33-jpa-spring-data.md](33-jpa-spring-data.md) third.

## Before → After

```java
// Before
import javax.persistence.Entity;
import javax.validation.Valid;
import javax.servlet.http.HttpServletRequest;

// After
import jakarta.persistence.Entity;
import jakarta.validation.Valid;
import jakarta.servlet.http.HttpServletRequest;
```

## Residual grep (source-limited)

Count and rewrite only first-party sources plus explicit build coordinates. A repository-wide search will hit generated output and is not a migration miss.

```text
rg -n 'import javax\.(persistence|validation|servlet|annotation)\b' src/main src/test
rg -n 'javax\.(persistence|validation|servlet)[:.]' build.gradle* pom.xml settings.gradle* libs.versions.toml
```

Limit the source search to `src/main` and `src/test`. Do not edit the build when that second search finds no EE coordinate or processor path.

### JDK `javax` exclusions

These stay `javax`. They are JDK APIs, not Jakarta EE:

| Package | Examples |
|---------|----------|
| `javax.sql` | `DataSource` |
| `javax.crypto` | cipher / key APIs |
| `javax.lang.model` | annotation-processing model |
| `javax.annotation.processing` | JDK processor API (do not treat as EE `javax.annotation`) |
| `javax.net` | sockets, SSL |
| `javax.xml` | parsers, transform |

Also leave other JDK roots (`javax.naming`, `javax.security`, `javax.imageio`, `javax.tools`) when the import is not an EE API. The rewrite set is `javax.persistence`, `javax.validation`, `javax.servlet`, and non-JDK `javax.annotation` (`Generated`, `PostConstruct`, `Resource`, and the same family).

### Generated exclusions

Do not rewrite, and do not fail the residual grep on:

- `build/`, `target/`, `out/`, `.gradle/`
- generator output (`build/generated*`, `target/generated*`, checked-in sources a later phase regenerates)
- architecture or knowledge-graph snapshots (for example `.stratum/`) that still name old `javax` types

Those files are stale generated descriptions, not first-party source. Leave them for whatever regenerates them.

## Import-only diff

Every source hunk in this phase is an import line. A build hunk is allowed only when the inventory found an explicit EE coordinate or processor configuration.

Hibernate annotations (`@TypeDef`, `@Where`, Session `save` / `update` / `delete` / `load`) and Spring Data repository APIs stay in the file even when they sit next to a `javax.persistence` import. Behavior changes belong to [03](03-hibernate-7.md) or [33](33-jpa-spring-data.md).

Phase notes use one residual-search claim: changed-file count, JDK `javax` packages intentionally retained, generated paths excluded, and compile left unverified. Do not record one claim per import line.

## Steps

1. Inventory EE imports under `src/main` and `src/test` only (`javax.persistence`, `javax.validation`, `javax.servlet`, non-JDK `javax.annotation`).  
2. Search build files for explicit EE coordinates. Skip the build edit when none exist.  
3. Rewrite those imports to `jakarta.*`. Leave the JDK packages in the table above unchanged.  
4. Check annotation processors / MapStruct / generated code only when this phase owns that processor path (MapStruct version + SPI Java level → [17-mapstruct.md](17-mapstruct.md)). Do not hand-edit generated trees.  
5. Diff check: source hunks are import lines only. Move any other hunk to the owning phase.  
6. Re-run the source-limited residual grep. Ignore generated, build, and graph artifacts.

## Do not

- “Fix” `javax.sql`, `javax.crypto`, `javax.lang.model`, `javax.annotation.processing`, `javax.net`, or `javax.xml`.  
- Mix `javax.persistence` and `jakarta.persistence` on the classpath.  
- Treat generated or graph snapshots as leftover EE imports.  
- Change Hibernate mappings, Session calls, or repository method names in the namespace commit.  
- Widen the diff beyond imports (and explicit EE coordinates when they exist).

## Risk

`SAFE_AUTO` when the diff is import-only (plus explicit EE coordinates) and the JDK / generated exclusions above were applied. Large diff; prefer one commit.

## Rollback

Revert the Jakarta commit.

## Done when

No EE `javax.*` imports in first-party `src/main` and `src/test`. Residual grep excluded generated, build, and graph output. JDK `javax` packages listed above are unchanged. The source diff is import-only. Compile stays unverified until the human gate.

## Handoff

`jakarta=clean|partial; filesTouched=<n>; diff=import-only|coords+imports; jdkJavax=retained; generatedExcluded=yes`
