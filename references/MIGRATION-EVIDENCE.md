# Migration evidence ledger

Verified findings that are not yet written into a phase, the catalog, or [99-anti-patterns.md](99-anti-patterns.md). The migrate agent checks this file when a symptom matches. It is not a second copy of the phase docs.

Lessons from earlier migrations are already in those files. Do not paste them back here.

## Evidence levels

| Level | Meaning |
|-------|---------|
| `DOC` | Confirmed in official project documentation or release notes |
| `RESOLVE` | Confirmed from resolved artifacts, dependency metadata, or class inspection |
| `EXECUTED` | Reproduced with a focused build, test, or spike |
| `DEPLOYED` | Confirmed in a representative deployed environment |

An emulator can earn `EXECUTED` for bootstrap or protocol behavior. It never earns `DEPLOYED` for real credentials or IAM. Re-check the entry when the target version changes.

## Entry template

```text
ID:
Symptom:
Affected:
Cause:
Verified fix:
Evidence:
Verification level:
Phase:
Limits / re-check:
```

## Adding evidence

Add a row only when all of these hold:

- The same failure would hit the next Boot 4 service.
- The phase, the catalog, and the anti-pattern list do not already say what to do.
- The fix is generic and tied to a version. No service name, hostname, ticket, secret, or private coordinate.

Put the executable steps in the phase. Put the version in [DEPENDENCY-CATALOG.md](DEPENDENCY-CATALOG.md). This file keeps the symptom, the cause, and how the fix was proved. After an enhance chat copies the rule into the phase, delete the row.
