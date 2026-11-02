# Contributing

This pack gets more useful when people add the stacks they actually migrated. Catalog pins, phases, stubs, and compile-error rules are the contribution that matters. A merged phase means the next service does not have to invent that step.

Use a pull request. Keep migration state out of it: `.joker/` stays in the service repo and is never committed here.

## What to add

| You hit this | Add this |
|--------------|----------|
| A library pin the catalog does not list | A row in [references/DEPENDENCY-CATALOG.md](references/DEPENDENCY-CATALOG.md): coordinate, stable target, risk, and the phase that applies it |
| A stack with no steps | A phase `phases/NN-short-name.md`, wired into [references/PHASE-CATALOG.md](references/PHASE-CATALOG.md). If the research is not finished, add `stubs/<topic>.md` instead |
| A stub you can now execute | Promote that stub to the next free phase id |
| A compile error no phase owns | A rule in [references/ownership.json](references/ownership.json), specific rules above broad ones |
| A failure that will hit the next service the same way | A version-bounded entry in [references/MIGRATION-EVIDENCE.md](references/MIGRATION-EVIDENCE.md), linked to the phase |
| A fix the pack should forbid | A row in [references/99-anti-patterns.md](references/99-anti-patterns.md). Do not renumber existing rows |

Point a chat at [AGENT.md](AGENT.md) when you want an agent to draft the pack change. That file is the template for a phase: Detect, Before → After, Steps, Do not, Risk, Rollback, Done when, Handoff. Do not point that chat at a service migration at the same time.

```text
Using <path-to-pack>/AGENT.md, add a phase for <topic>. Wire it into PHASE-CATALOG. Do not migrate any service.
```

## Rules

- One concern per change. A phase does not also bump unrelated libraries.
- Phase ids are stable. Pick the next free `NN`. Never renumber a phase that already exists.
- Examples are generic: "if the service has X", with before and after snippets. No service names, hostnames, ticket ids, registry paths, or private Maven coordinates.
- Versions come from a public release (Maven Central or the Plugin Portal), named in the catalog row. Do not paste a version observed only inside one company.
- Do not add CI base images, Docker registries, or private registry image tags.
- Do not edit `SKILL.md` unless the orchestration rules actually change.
- Agents that migrate a service must not read this file or [MANUAL.md](MANUAL.md).

## Checks

From the pack root, after a dashboard or snapshot change:

```bash
python3 -m unittest dashboard/test_snapshot.py
```

Describe in the pull request which phase or catalog row you added, which Boot and Java versions you verified it against, and what you left as a stub.
