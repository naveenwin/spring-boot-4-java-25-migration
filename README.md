# Spring Boot 4 and Java 25 migration

An agent workflow that plans and carries a Java or Kotlin Spring service from Boot 2 or Boot 3 onto **Spring Boot 4** and **Java 25**. You point a chat at this pack. The agent detects what the service actually uses, writes a plan, moves every library version, then fixes compile errors one topic at a time, and proves the result against a baseline it recorded before the first edit.

The mechanical work stays with the agent: intake, the version wave, source fixes, Gradle or Maven for resolve, compile, and the context-load test, local commits, and the handoff into the next chat. You approve the plan, answer the few product questions it cannot infer, run the full test suite twice, run CI, and open the merge request.

```text
Plan and migrate this service to Java 25 / Spring Boot 4 using <path-to-pack>/SKILL.md
```

Open that chat in the **service** repo. Pass the path to this pack. Operator detail is in [MANUAL.md](MANUAL.md).

## Why the plan is small on purpose

A Boot 4 jump touches Jakarta, Jackson 3, Hibernate 7, Security 7, the test stack, and whatever else that one service declared. Doing all of it in one green-at-every-step branch makes later phases patch around earlier breakage.

This pack refuses that shape.

1. **It inventories the service.** JPA, WebFlux, Kotlin, Flyway, GCP, Cucumber, and the rest are detected from the repo. Phases that do not apply are skipped. A Kafka stub does not run on a service that has no Kafka.
2. **It refuses to invent versions.** Pins come from [the catalog](references/DEPENDENCY-CATALOG.md) or from an approval recorded for this migration. A coordinate with no procedure blocks the plan until a phase or stub exists. The agent does not shop Maven Central again for a pin the catalog already set.
3. **It separates required work from optional work.** `must` is what Boot 4 and Java 25 need. `good` runs only after that tier passes. `bad` (a Jackson 2 bridge, WireMock 4 while it is still beta, disabling TLS to get green) runs only if you ask.
4. **It asks you before it guesses.** Each item is `SAFE_AUTO`, `ASK_HUMAN`, or `SPIKE_FIRST`. An open question stops that item. A worker that hits something new stops and reports it.

You see the plan as a table: what will change, why it applies to this service, and whether you need to decide anything. Nothing is edited until you approve it.

## Four stages, one closed loop

| Stage | What the agent changes | How it knows it is done |
|-------|------------------------|-------------------------|
| **Baseline** | Nothing, except a context-load test if the suite does not already load the Spring context | Full suite and context test recorded on the old JDK, before any migration commit |
| **Library versions** | Build files only, one commit per topic | The build configures and every classpath resolves. Compile is expected to fail |
| **Code fixes** | Source, resources, and tests, one topic at a time | That topic's compile errors are gone. The stage ends when compile is green |
| **Runtime check** | Fixes the new failures the run actually shows | Context loads. The full suite has no new failures against the baseline |

After every resolve, compile, or context run, the log stays on disk under `.joker/`. A small extractor prints **one line**: exit code, who owns the compile errors, and, at the runtime check, which tests newly fail. The orchestrator keeps that line. It does not paste the log into the chat, and a worker is not allowed to "clean up" another topic's errors to make the line look better.

That is the loop. Run, attribute, fix only what you own, run again. At the end, `newlyFailing` must be zero and every missing test must be explained (renamed, removed on purpose, or restored).

```text
baseline recorded
    → versions move, resolve is green
        → each phase clears the errors it owns
            → context loads
                → suite compared with the baseline
                    → a new failure goes back to the phase that owns it
```

## Isolation, so one fix cannot smear into the next

- **One repository.** The agent does not open a sibling service to copy a migration.
- **One owner per compile error.** [ownership.json](references/ownership.json) maps the compiler message to a phase. Jackson does not edit Hibernate files to get a green compile.
- **One phase per commit.** The subject is `<phase-id> <A|B|fix>: …`. The next run can blame a build-file failure back to the commit that introduced it.
- **A fresh worker per slice.** It receives one phase document and its own errors, then it is done. It does not keep a long memory of the rest of the migration.
- **No compatibility shims as a way out.** Boot 4 application JSON goes to Jackson 3. The pack will not add a Jackson 2 bridge, JUnit Vintage, a compile-only jar, or a disabled check to force a green build.

## Handoffs, so a long migration survives a new chat

Chats get dull after a few builds. The pack treats that as normal.

State lives in the service repo at `.joker/java-spring-migration/` (gitignored, never committed): the plan, blockers, the baseline, run ids, and a short handoff. After a stage boundary, or after four build runs in one chat, the agent writes the handoff and stops. You open a new chat and paste the resume prompt. The new chat reads `status.yaml` and the latest handoff. It does not need the old transcript.

You can watch the same state in a local board:

```bash
python3 <path-to-pack>/dashboard/server.py --root .
```

Then open `http://127.0.0.1:8765/`. The board only reads `.joker/`. It does not show build logs.

## What you still do

| You | The agent |
|-----|-----------|
| Approve the plan | Detect, select phases, write the plan |
| Answer product questions (wire format, a risky API choice) | Apply catalog versions, edit code, commit locally |
| Run the full test suite once before edits and once at the end | Run resolve, compile, and the single context-load test |
| Run CI and open the merge request | Compare the suite with the baseline and route new failures |
| Start a new chat when asked | Write the handoff the new chat resumes from |

If you already know the target line, put it in the first message and it will not ask:

```text
Plan and migrate this service to Java 25 / Spring Boot 4 using <path-to-pack>/SKILL.md
Target: Boot 4.1.x, Java 25, Spring Cloud 2025.1.x
Defer: WireMock 4, Cucumber 8 until after the must tier
```

## What a finished migration is aiming at

- Java **25** and Spring Boot **4.x**, with Spring Cloud **2025.1.x** when Cloud is in use.
- Jakarta EE, Jackson **3** with no application Jackson 2 bridge, Hibernate **7** and Spring Data JPA **4** where JPA is used.
- Security **7**, modular starters, and Boot-managed JUnit **6** where tests exist.
- Kotlin **2.3.x** when the repo has Kotlin, because Java 25 bytecode needs it on Boot 4.1.

The phase list and the order the planner uses are in [references/PHASE-CATALOG.md](references/PHASE-CATALOG.md). Intake classifies Boot 3.x and Boot 2.7.x from the version already in the build.

## This pack will not

- Redesign the domain while it migrates the platform.
- Edit CI images, Dockerfiles, or registry tags.
- Push to your remote, or commit `.joker/`.
- Keep a Boot 4 application on Jackson 2.

## Contributing

The catalog and the phase list grow when someone migrates a stack this pack has not seen yet. Add a public library pin, promote a stub, or write the next phase. [CONTRIBUTING.md](CONTRIBUTING.md).

## Layout

```text
README.md          this file
MANUAL.md          operator guide
CONTRIBUTING.md    how to add phases, catalog rows, and stubs
SKILL.md           rules the migration agent follows
AGENT.md           rules for extending the pack
phases/            one migration concern per file
references/        catalog, gates, error ownership
stubs/             topics that are not a phase yet
scripts/           log extractor and Gradle init script
dashboard/         local status board
```

## License

[Apache License 2.0](LICENSE).
