# 08 — Flyway

## Detect

Any of:

- Gradle plugin `org.flywaydb.flyway` (record the version; flag when its major lags the catalog target or disagrees with `flyway-core`)
- Runtime coordinates: `spring-boot-starter-flyway`, `flyway-core`, and/or a vendor module (`flyway-database-postgresql`, `flyway-mysql`, other `flyway-database-*`)
- `flyway-core` **without** a vendor module while the production JDBC driver needs a Flyway 10+ database module
- `spring.flyway` keys — especially whether `spring.flyway.locations` appears in any `application*` file or documented external config path
- Scripts under `src/main/resources/db/migration` (default `classpath:db/migration`) or `db/migration/<vendor>`

Skip only when the service has no Flyway plugin, starter, core, vendor module, or migration tree.

**Default location is already valid.** Scripts at `db/migration/*.sql` with **no** `spring.flyway.locations` resolve as `classpath:db/migration`. That is not missing configuration. Do not add a `locations` key unless an external configtree or profile sets a conflicting path.

```text
org.flywaydb.flyway
flyway-core
flyway-database-
spring.flyway.locations
db/migration
```

## Before → After

```gradle
// Before — plugin lagging, core only, no vendor module
id 'org.flywaydb.flyway' version '5.x'
implementation 'org.flywaydb:flyway-core'

// After — plugin, core, and vendor module share one approved version
id 'org.flywaydb.flyway' version '13.10.3' // catalog approvedTarget
implementation 'org.springframework.boot:spring-boot-starter-flyway'
implementation 'org.flywaydb:flyway-core:13.10.3'
implementation 'org.flywaydb:flyway-database-postgresql:13.10.3' // vendor matching the production DB
```

When the approved target is **ahead of the Boot BOM**, pin **plugin + core + vendor** together. Example: Boot **4.1.1** manages Flyway **12.4.0** while the catalog approves **13.10.3**. `spring-boot-starter-flyway` alone stays on the older BOM line. Do not pin only one of the three.

Leave the starter unversioned. Use the vendor artifact that matches production (`flyway-database-postgresql`, `flyway-mysql`, or the matching `flyway-database-*`).

```yaml
# Scripts already under db/migration, and no profile sets locations:
# do not add spring.flyway.locations. Default is classpath:db/migration.

# Explicit locations only when the tree is not that default, or every
# profile already agrees on a non-default path:
# spring.flyway.locations: classpath:db/migration/<vendor>
```

Keep existing `baseline-on-migrate`, `baseline-version`, and `clean-disabled` keys as they are when this phase is version/module alignment only.

## Steps

1. Inventory plugin version, starter vs core-only, vendor module, production DB, every `spring.flyway.locations` hit, and the script directory.  
2. If scripts live under `db/migration` and no `locations` key exists, preserve `classpath:db/migration`. Do not add YAML to restate the default.  
3. Add the vendor module that matches the production DB.  
4. When catalog `approvedTarget` or migration-local `catalog-approvals.yaml` is ahead of the Boot BOM, set that **same** version on the Gradle plugin, `flyway-core`, and the vendor module in one change.  
5. When the approved target matches the Boot BOM, unversioned starter + vendor module is enough; any explicit pin must still keep plugin, core, and vendor on one version.  
6. Confirm locations still resolve for local and CI profiles. Writing `spring.flyway.locations` for the first time is `ASK_HUMAN` when external config may disagree — stop before adding the key.  
7. Do not rewrite historical SQL unless a Flyway check fails and a human approves the script edit.

## Do not

- Add `spring.flyway.locations` when default `classpath:db/migration` already matches the repo layout.  
- Pin plugin, core, or vendor module to different versions.  
- Rely on the starter alone when the approved target is ahead of the Boot BOM.  
- Edit applied production migrations.  
- Bump Flyway independently of an approved catalog or migration-local target.  
- Treat a build-file-only align as proof that migrate-on-startup succeeded.

## Risk

| Change | Risk |
|--------|------|
| Vendor module plus plugin + core + vendor aligned to an approved target, SQL frozen, locations left as they already resolve (including default `classpath:db/migration`) | `SAFE_AUTO` |
| Editing applied migration SQL, or first-time in-repo `locations` that may clash with external config | `ASK_HUMAN` |

Module alignment does not lower the schema-history risk of a later SQL edit. Score the SQL/location decision separately from the version pin.

## Rollback

Revert the plugin, core, vendor module, and any locations edit. The `SAFE_AUTO` path does not touch SQL, so rollback is the build change alone.

## Done when

- Vendor module matches the production DB.  
- If the approved target is ahead of the Boot BOM, plugin, core, and vendor share that version.  
- Default `classpath:db/migration` is unchanged when that layout already matched.  
- A build-file-only diff is a complete outcome; migrate-on-startup stays **unverified** until a human runs it.  
- No SQL rewrite when only module and version alignment changed.

## Handoff

`flywayModule=<artifact>|n/a; locations=default-classpath-db-migration|in-repo|external|n/a; pins=plugin+core+vendor|bom-aligned|n/a; sql=unchanged|edited; migrateOnStartup=unverified`
