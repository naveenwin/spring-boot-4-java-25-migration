# 37 — Sonar Gradle plugin

## Detect

Apply when this repo still uses the legacy Sonar Gradle names:

- plugin `org.sonarqube` with a `sonarqube { }` extension
- task `sonarqube`, `tasks["sonarqube"]`, or `dependsOn("sonarqube")`
- a script in this repo that runs `./gradlew sonarqube`

Skip when Sonar is absent, and when the extension, the task, and the invocation already say `sonar`.

This phase does not edit CI job images, Dockerfiles, Jib base images, or registry tags.

## Before → After

Catalog `org.sonarqube` (example **7.5.x**) retires the legacy `sonarqube` names. Change all of them in one commit. [12-dependency-bump-queue.md](12-dependency-bump-queue.md) does not bump the plugin alone.

| Surface | Before | After |
|---------|--------|--------|
| Gradle extension | `sonarqube { properties { … } }` | `sonar { properties { … } }` |
| Task and `dependsOn` | `tasks["sonarqube"]`, `dependsOn("sonarqube")` | `tasks["sonar"]`, `dependsOn("sonar")` |
| CI script in this repo | `./gradlew sonarqube` | `./gradlew sonar` |

## Steps

1. Find the plugin, the extension, the task name, and every `sonarqube` invocation in this repo.
2. Move the plugin version, the `sonar { }` extension, the `sonar` task, and `./gradlew sonar` in one commit.
3. Leave `image:` lines, Docker `FROM`, and Jib `from.image` unchanged.
4. Ask the human to run the pipeline. The agent does not trigger CI.

## Do not

- Edit CI images, runtime images, or registry paths.
- Rename only one of the extension, the Gradle task, and the CI invocation.
- Edit a shared CI project in another repository.
- Embed hostnames or secrets.

## Risk

`SAFE_AUTO` when the extension, task, and invocation in this repo move together.  
`ASK_HUMAN` when the pipeline include lives in another repository.

## Rollback

Revert the commit.

## Done when

- Extension, task, and CI invocation all use `sonar` when the catalog plugin is applied.
- That commit does not change an image or a registry line.
- The human has a pipeline result. The agent does not run CI.

## Handoff

`sonar=renamed-together|deferred|n/a; images=untouched`
