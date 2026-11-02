# 34 — Spring Cloud GCP 8.x

## Detect

Apply when the service uses `com.google.cloud:spring-cloud-gcp-*` or any of:

- `spring-cloud-gcp-dependencies` below **8.x**
- Secret Manager: `spring-cloud-gcp-starter-secretmanager`, `spring.config.import=sm://…`, `${sm://…}`
- Pub/Sub: `spring-cloud-gcp-starter-pubsub`, `PubSubTemplate`, `PubSubAdmin`, `PubSubMessageConverter` — code, lease, converter, and health are [43-pubsub.md](43-pubsub.md). This phase only classifies the module and aligns the BOM.
- GCP logging, storage, SQL, Firestore, or core starters
- `ListenableFuture` / `.completable()` around GCP operations

Skip when no Spring Cloud GCP dependencies, imports, or configuration exist.

Catalog target: [DEPENDENCY-CATALOG.md](../references/DEPENDENCY-CATALOG.md) (`spring-cloud-gcp-dependencies` **8.2.4**, or the approved 8.x target current when the migration starts).

## Before → After

### BOM / dependencies

```gradle
// BEFORE — Boot 3-era train; mixed majors are also common
implementation platform("com.google.cloud:spring-cloud-gcp-dependencies:5.12.3")
implementation "com.google.cloud:spring-cloud-gcp-starter-secretmanager"

// AFTER — Boot 4-compatible train from the catalog
implementation platform("com.google.cloud:spring-cloud-gcp-dependencies:8.2.4")
implementation "com.google.cloud:spring-cloud-gcp-starter-secretmanager"
```

Keep all Spring Cloud GCP modules on one BOM train. Do not version logging, Secret Manager, and Pub/Sub independently.

### Classify each GCP module

Classify every `spring-cloud-gcp-*` module the service declares before editing. Each class sets the work to do and what counts as done.

| Class | Signals | Work | Done means |
|-------|---------|------|------------|
| **code-change** | First-party imports of changed APIs: `ListenableFuture` / `.completable()` around non-Pub/Sub GCP calls, custom credentials or client factories. Pub/Sub converters and subscriber code are phase 43 | Edit sources (main **and** test) per the sections below. Pub/Sub edits wait for phase 43 | Residual grep empty for this phase's sites; compiles |
| **dependency-only** | Starter on the classpath, used only through auto-config or properties, with no changed API in first-party code | BOM align only | Resolves on the 8.x train; context starts |
| **verification-only** | No source or dependency edit needed, but runtime behavior can still move (Secret Manager bootstrap, auth, emulator wiring) | Record the bootstrap, protocol, and real-auth layers below | Phase notes name which layer covered it, with a run id |

A module can be in two classes (for example, Secret Manager is often a config rename plus verification-only bootstrap). Record each class in the handoff `modules=[…]` list.

### Secret Manager ConfigData prefix

```yaml
# BEFORE — accepted by 8.x but deprecated
spring:
  config:
    import: "sm://db-password"
app:
  password: "${sm://db-password}"

# AFTER — canonical 8.x prefix
spring:
  config:
    import: "sm@db-password"
app:
  password: "${sm@db-password}"
```

The `sm@` swap keeps the path after the scheme. `sm@projects/<project-id>/secrets/<secret-id>` is valid and means the latest version. Do not shorten a full resource name to `sm@<secret-id>`.

A bare import, with no secret name, registers Secret Manager placeholder resolution. It maps the same way:

```yaml
# BEFORE — bare import
spring:
  config:
    import: "sm://"          # or "optional:sm://"

# AFTER
spring:
  config:
    import: "sm@"            # or "optional:sm@"
```

Inventory both the import and every placeholder, in `application*.yml` / `.properties`, profile files, test resources, and `@SpringBootTest(properties = …)` / `@TestPropertySource` strings. Keep an existing `optional:` prefix exactly as it is, and do not add or remove one. Changing missing-secret handling is an external behavior decision, not a mechanical rename.

### Pub/Sub

Pub/Sub call sites, the ack-lease default, the Jackson converter, and the health contributor are [43-pubsub.md](43-pubsub.md). `PubSubTemplate.publish` already returns `CompletableFuture` on GCP **4.8+**; deleting `.completable()` does not finish that phase.

Non-Pub/Sub GCP clients that still use Spring `ListenableFuture` / `.completable()` / `addCallback` are this phase. Map them the same way phase 43 maps Pub/Sub leftovers: the call returns `CompletableFuture`, test stubs use `completedFuture` / `failedFuture`, and callback swallow-vs-propagate stays. Residual grep for those non-Pub/Sub sites:

```bash
rg -n 'ListenableFuture|ListenableFutureCallback|SettableListenableFuture|AsyncResult|\.completable\(\)|addCallback\(|org\.springframework\.util\.concurrent' \
  --glob '*.java' --glob '*.kt' --glob '*.groovy' src
```

Pub/Sub hits belong to phase 43. Hits outside GCP belong to the owning phase. Record both; do not rewrite them here.

### Protobuf runtime (first-party codegen)

Spring Cloud GCP **8.x** Pub/Sub and related clients use protobuf **4.x** gencode. If the service still pins `protobuf-java` / `protoc` **3.x** for its own `.proto` sources, context startup can fail before any test runs (`NoClassDefFoundError: com/google/protobuf/RuntimeVersion$RuntimeDomain` on `TopicAdminClient`). That pin is **not** a phase 34 edit. Phase [15-protobuf-protoc.md](15-protobuf-protoc.md) is `must` in that case and bumps it in the same Stage A wave. Errors on the pin or on generated sources are owned by 15 ([ownership.json](../references/ownership.json)).

## Bootstrap, emulator, and auth boundaries

Secret Manager ConfigData runs before the application context. A normal unit test or a green compile does not prove that `spring.config.import` can resolve.

Verify in layers:

1. **Bootstrap wiring** — a context test/fake service proves the 8.x ConfigData resolver and loader run on Boot 4.
2. **Service protocol** — Pub/Sub emulator or a controlled fake proves publish/pull/subscribe behavior.
3. **Real authentication** — a non-production cluster smoke with the real service account proves ADC, Workload Identity, TLS, and IAM.

Emulators normally bypass credentials and IAM. Record exactly which layer each test covers; never claim an emulator proves production authentication. Google provides no first-party Secret Manager emulator, so third-party images require security/supply-chain approval.

For Pub/Sub Testcontainers, follow [25-testcontainers-2.md](25-testcontainers-2.md): use Testcontainers 2 module names or a `GenericContainer`; do not mix 1.x and 2.x modules. Resolve mapped ports only after the container starts and prefer a listening-port wait strategy.

## Steps

1. Inventory the GCP BOM and every GCP starter; flag mixed train versions; classify each module as code-change / dependency-only / verification-only.
2. Align the BOM/modules to the approved 8.x catalog target.
3. Migrate `sm://` imports (including a bare `sm://`) and placeholders to `sm@` across main and test resources; keep each `optional:` prefix unchanged.
4. Update Secret Manager bootstrap configuration and remove obsolete package/SPI workarounds.
5. When Pub/Sub is present, classify that module and stop. Lease, converter, health contributor, and Pub/Sub futures are [43-pubsub.md](43-pubsub.md). Migrate `ListenableFuture` only on non-Pub/Sub GCP clients, then run the residual grep.
6. Name the smallest applicable bootstrap/protocol spike for Stage C. The orchestrator runs it when the environment allows; otherwise the human runs it. Record which layer it proves as a claim in phase notes. Pub/Sub delivery behavior is a phase 43 claim, not a substitute for the real-auth layer.
7. For services that read secrets in deployed environments, require a real lower-environment auth smoke before production readiness is claimed.

## Do not

- Downgrade Boot because Initializr omits a GCP entry; verify the actual 8.x compatibility matrix/artifacts.
- Keep mixed Spring Cloud GCP major versions.
- Treat a Pub/Sub/Secret Manager emulator as proof of ADC, Workload Identity, TLS, or IAM.
- Disable Secret Manager import or silently default required secrets merely to make startup green.
- Add a third-party Secret Manager emulator image without human security approval.
- Migrate Pub/Sub lease, converters, or health beans in this phase. Phase 43 owns them.
- Shorten `sm://projects/<project-id>/secrets/<secret-id>` to `sm@<secret-id>`. Keep the path after the scheme.
- Add or drop `optional:` on a Secret Manager import while renaming it.
- Change callback error semantics (swallow versus propagate) while converting to `CompletableFuture`.
- Hand off with `ListenableFuture` / `.completable()` residuals at non-Pub/Sub GCP call sites in test sources. Pub/Sub residuals belong to phase 43.
- Put project IDs, secret values, credentials, or tokens in this pack or migration notes.
- Bump `protoc` or `protobuf-java` in this phase. Phase 15 owns the pin.

## Risk

`SPIKE_FIRST` when Secret Manager is on the bootstrap path, custom credentials/client factories exist, or GCP spans multiple majors.  
`ASK_HUMAN` for missing-secret semantics, emulator supply chain, service-account/IAM changes, or real-cluster smoke.  
`SAFE_AUTO` only for a same-train patch align with no bootstrap/code API changes.

## Rollback

Revert the GCP BOM/config/code commit with the Boot migration. Do not leave Boot 4 paired with a Boot 3-era GCP train; if bootstrap cannot be made safe, roll back the Boot 4 migration rather than disabling secrets/auth.

## Done when

- All Spring Cloud GCP modules resolve from one approved 8.x BOM.
- No deprecated `sm://` import/placeholders remain in main or test resources when Secret Manager is used.
- The future residual grep is empty for non-Pub/Sub GCP call sites in main and test. Pub/Sub residuals are phase 43.
- Each module carries a class. A Pub/Sub module is handed to phase 43, not given a converter row here.
- Phase notes name the bootstrap/protocol spike and, when applicable, the lower-environment real-auth smoke; Stage C records their results.
- No secrets or credentials were committed or logged.
- The latest compile shows no errors owned by this phase.

## Handoff

`gcp=8.x|n/a; modules=[name:code-change|dependency-only|verification-only,…]; secretManager=sm@|n/a; pubsub=43|n/a; futureResidual=<n>; bootstrap=green|deferred|n/a; realAuth=green|deferred|n/a`

`pubsub=43` when any Pub/Sub detect signal exists. `futureResidual` counts non-Pub/Sub GCP sites only.
