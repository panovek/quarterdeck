---
name: quarterdeck-setup
description: Install, upgrade or verify the Quarterdeck agent workflow in the current repository - detect the project, interview the owner about the decisions only they can make, write .quarterdeck.json, install the doctrine, skills, hook and checks, then prove the installation with doctor. Use when asked to set up, install, bootstrap, update, upgrade or check Quarterdeck.
---

# Set up Quarterdeck

You are the installer. Facts are yours to detect and to verify by running things; decisions belong
to the owner. Every step below has a **Validate** line that is a command with a known answer, and
the last step runs `doctor`, which re-checks all of it mechanically. Nothing is installed until
`doctor` reports zero failures.

Everything you install lives in `assets/` next to this file. Call that directory `$QD` below —
resolve it from this skill's own path before you start.

```
assets/
  VERSION                     the version you are installing
  doctrine/                   workflow.md, task-template.md, agent-notes.md, adr-README.md, adr-template.md
  skills/                     refine/, implement/, retro/, milestone-code-review/ — installed into the project's .claude/skills/
  hooks/guard-main.py         the PreToolUse guard; reads .quarterdeck.json at runtime
  tools/                      check-tests-first.py, check-pr-body.py, doctor.py
  templates/                  claude-block.md, boards/*.md, ci/quarterdeck.yml, pull_request_template.md,
                              ci/mutation.yml — a seed for the main-branch mutation run, offered in Step 9,
                              diagrams.md — a starter diagram registry, offered in Step 11, never installed by default
```

## Modes

| Mode | When | Go to |
|---|---|---|
| **Install** | No `.quarterdeck.json` in the repository root | Steps 0–11 |
| **Upgrade** | A manifest exists and its `quarterdeck` field differs from `$QD/VERSION`, or the owner asks to update | [Upgrade](#upgrade) |
| **Verify** | The owner asks to check, or you are unsure what state the project is in | [Verify](#verify) |

## Ground rules

- **Never ask what you can read.** Detect first; then put the decisions to the owner in one round,
  numbered, each with the detected default and the evidence for it.
- **Run what you are about to write down.** A test command or check command goes into the
  manifest only after you have run it and seen its exit code. If it fails, say so; the owner
  decides whether to record it anyway.
- **Never overwrite what the project owns.** Seeded files are written once. Anything outside the
  marked block in `CLAUDE.md` / `AGENTS.md` is untouched. Other keys in `.claude/settings.json`
  are preserved.
- **Never commit.** Leave everything in the working tree and list what was written. Committing is
  the owner's.
- **A failing validation stops the step.** Fix and re-validate. If you cannot, stop and report
  exactly which validation failed; do not continue to the next step "to see how far it gets".

## Install

### Step 0 — Preconditions

**Goal.** A git repository, and the assets found.

**Do.** `git rev-parse --show-toplevel` from the project root; `cat $QD/VERSION`.

**Validate.** Both succeed. Not a git repository → stop: the hook guards branches, so there must
be branches to guard. Everything below runs from the repository root.

### Step 1 — Detect the facts

**Goal.** Every default you will offer in Step 2 comes from evidence in the repository, not from
a guess.

**Do.** Find each of the following and note *where* you found it:

| Fact | Where to look |
|---|---|
| Ecosystem(s) | Marker files in the root: `tsconfig.json`, `package.json`, `pyproject.toml` / `setup.py` / `requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml` / `build.gradle(.kts)`, `*.sln` / `*.csproj`, `Gemfile`, `composer.json`, `Package.swift`, `mix.exs`. A monorepo may have several — note all and ask which one the workflow applies to first |
| Main branch | `git symbolic-ref --short refs/remotes/origin/HEAD`; else whichever of `main` / `master` exists |
| Test command | The runner's own entry: `package.json` scripts, `Makefile` / `justfile` targets, `mix.exs` aliases, `pyproject.toml` tool sections, `Cargo.toml`, `go.mod`. The [defaults table](#reference-ecosystem-defaults) is the fallback, never the first choice |
| Check command | An existing `check` / `ci` / `verify` script or target if there is one. Otherwise compose it: typecheck && lint && format-check && dead-code tool && the dead-code tool without the tests && tests, from the scripts that exist |
| Mutation command | Existing config: `stryker.config.*`, `mutmut` in `pyproject.toml`, `cargo-mutants`, `muzak` in `mix.exs`, … Empty if none |
| Test globs | The runner's config (`testMatch` / `include` for jest or vitest, `testpaths` for pytest, `test/` for ExUnit, `*_test.go`, `spec/` for RSpec). Then **check them**: they must match existing test files and must not match source files |
| Source directories | Where non-test code lives: `src`, `lib`, `app`, `Sources`, `.` for Go. What the test globs are checked against |
| ADR directory | Any of `docs/adr`, `docs/decisions`, `doc/adr`, `adr`, `docs/en/adr` |
| Domain document | Candidates only, never assumed: `PRD.md`, `docs/**/prd*.md`, `docs/design*.md`, `SPEC.md`, `docs/spec*.md`, an OpenAPI file, a `docs/gdd*.md`. Offer the best candidate as the default; `none yet` is a legitimate answer |
| Board | A ClickUp connector in this session → `clickup`; `gh` on PATH and a github.com remote → `github`; another tracker connector in the session → `generic`; otherwise `markdown` |
| CI | `.github/workflows/` → GitHub Actions; `.gitlab-ci.yml`, `.circleci/`, `bitbucket-pipelines.yml`, `azure-pipelines.yml` → note which |
| Agent instructions | Whether `CLAUDE.md` and/or `AGENTS.md` exist, and whether either already carries `<!-- quarterdeck:begin -->` |
| Hook settings | Whether `.claude/settings.json` exists and what it contains |

**Validate.**
- Run the detected test command and the detected check command; record the exit codes. If a
  command will plausibly take more than a couple of minutes, ask before running it.
- Test globs: a shell glob or `find` shows ≥ 1 match and no source file among the matches. A
  project with no tests yet is allowed — say so explicitly.
- Every path you will offer as a default exists.

### Step 2 — Interview the owner

**Goal.** The owner makes every decision; you make none of them. One round, numbered, each
question carrying the detected default and why it is the default.

Ask, in this order, skipping nothing:

1. **Main branch** and **task branch prefix** (default `task/`).
2. **Workflow documents directory** (default `docs/workflow`) and **ADR directory** (detected, or
   `docs/adr`).
3. **Domain document** — the single owner of product rules, formulas and constants: a PRD, a
   design document, a spec, an API contract. Path, or `none yet`. Say plainly that with `none yet`
   the citation rule has nothing to cite but ADRs and tasks, and that this is recorded, not hidden.
4. **Board**: kind (`clickup` / `github` / `markdown` / `generic`); the name the agent
   instructions should use for it; for `clickup` and `generic`, the board's own name for each of
   the seven statuses `open, refine, todo, in progress, in review, done, closed`; the **lists an
   agent may create tasks in** (default `Bugs, Open decisions`).
5. **Commands**: check, test, mutation (empty if none), architecture-record render (empty if
   none) — each with the exit code you observed.
6. **`core_dir`** — the pure, deterministic directory mutation testing is scoped to (empty if
   none yet).
7. **Test globs** — with the match counts from Step 1, and the source directories they were
   checked against.
8. **Agent signature** for `Co-Authored-By:` (default `Claude <noreply@anthropic.com>`).
9. **CI**: write the GitHub Actions workflow? (default yes when `.github/workflows/` exists; for
   another CI system, see Step 9). When there is a mutation command, also: seed the workflow that
   runs it on the main branch after a merge? (default yes on GitHub Actions). If the project's CI
   already runs mutation on pull requests, say so — that job is the project's, and moving it is
   the owner's call.
10. **Sources of truth** — confirm or edit the four default rows, and add any domain the
    project has that these do not cover (a data model document, a UI spec, a compliance
    document). The code row is added by you and is not up for discussion:

    | Domain | Owner | Notes |
    |---|---|---|
    | Architecture, layer boundaries, structural rules | `` `<adr_dir>/` `` | An ADR is amended, never contradicted in silence |
    | Scope of the change being made right now | The task on `<board name>` | What we want, and how, *today* |
    | The plan: milestones, ordering, dependencies, what is next | The `<board name>` board | Lists (or milestones or labels — `<docs_dir>/board.md` says which for this board) are the milestones, blocking links are the dependencies, statuses are the state. There is no plan file |
    | Product rules, formulas, constants, lexicon | `` `<domain_doc>` `` — or **none yet** — nothing owns intent; failure modes 1 and 2 are half-answered until something does | The design intent |

**Validate.** Every answer that is a path exists, or the owner has said it will. Every command
in the answers has been run (re-run any the owner changed). No question is left unanswered — an
answer of "whatever you think" means the default, and you say which default you took.

### Step 3 — Write the manifest

**Goal.** `.quarterdeck.json` in the repository root, with exactly the schema in the
[reference](#reference-the-manifest). It is the single binding between the doctrine and this
project: the hook, the two checks that need it, `doctor` and the skills read it.

**Do.** Write it with `quarterdeck` set to the contents of `$QD/VERSION`, two-space indentation,
keys in the reference order. Empty strings for commands that do not exist; never omit a key.

**Validate.** `python3 $QD/tools/doctor.py` — the **The manifest** section reports every key
`ok`. Everything below it will fail until the later steps run; that is expected at this point.

### Step 4 — Copy the shipped files

**Goal.** Byte-identical copies of everything Quarterdeck maintains. These files carry no
project-specific content — the hook and the checks read the manifest — so they are the same in
every project and `doctor` diffs them against `$QD`.

**Do.** `mkdir -p` the destinations, `cp` each, `chmod +x` the Python files.

| From `$QD/` | To |
|---|---|
| `doctrine/workflow.md` | `<docs_dir>/workflow.md` |
| `doctrine/task-template.md` | `<docs_dir>/task-template.md` |
| `skills/refine/SKILL.md` | `.claude/skills/refine/SKILL.md` |
| `skills/implement/SKILL.md` | `.claude/skills/implement/SKILL.md` |
| `skills/retro/SKILL.md` | `.claude/skills/retro/SKILL.md` |
| `skills/retro/digest.py` | `.claude/skills/retro/digest.py` |
| `skills/milestone-code-review/SKILL.md` | `.claude/skills/milestone-code-review/SKILL.md` |
| `hooks/guard-main.py` | `.claude/hooks/guard-main.py` |
| `tools/check-tests-first.py` | `tools/quarterdeck/check-tests-first.py` |
| `tools/check-pr-body.py` | `tools/quarterdeck/check-pr-body.py` |

If a destination already exists and differs, do not overwrite silently: show the owner the diff
and ask. (An existing identical copy is fine.)

**Validate.** `cmp` each pair — silent for all ten. Then `python3 $QD/tools/doctor.py` — the
**Shipped files** section is all `ok` (bar the CI workflow, which is Step 9).

### Step 5 — Seed the files the project will own

**Goal.** Logs and records that start from a template and then belong to the project. Written
once; never overwritten, by you or by any later upgrade.

| From `$QD/` | To | Skip when |
|---|---|---|
| `doctrine/agent-notes.md` | `<docs_dir>/agent-notes.md` | it exists |
| `doctrine/adr-README.md` | `<adr_dir>/README.md` | it exists |
| `doctrine/adr-template.md` | `<adr_dir>/adr-template.md` | it exists, or the folder already has its own template |
| `templates/pull_request_template.md` | `.github/pull_request_template.md` | it exists — then tell the owner the four sections it must carry |

**Validate.** Each destination exists. `doctor` — **Seeded files** all `ok`.

### Step 6 — Render the board procedures

**Goal.** `<docs_dir>/board.md`: how an agent reads, moves, comments on and creates a task on
*this* board. The installed skills read this file before touching the board.

**Do.** Start from `$QD/templates/boards/<kind>.md` and fill the placeholders:

| Placeholder | Value |
|---|---|
| `{{status_map}}` | A two-column Markdown table, header `Workflow status \| Board name`, one row per status in canonical order, both cells in backticks |
| `{{lists}}` | The agent-writable lists, each in backticks, joined with "and" for two, commas for more |
| `{{docs_dir}}` | The workflow documents directory, no trailing slash |

For a tracker none of the four templates covers — Linear, Jira, Notion, Trello through a connector
— start from `generic.md` and replace each bullet's verb with the actual tool call available in
this session (read, update status, update description, comment, create in list). Keep the seven
bullets: the skills rely on those six operations, and on the seventh — where the milestone, the
siblings and the ordering live, because the board is the plan — and nothing else.

**Validate.** `grep -c '{{' <docs_dir>/board.md` prints `0`. `doctor` — **Rendered files**: the
board file names every board status and every list.

### Step 7 — Render the agent-instruction block

**Goal.** The rules no tool can enforce, the sources-of-truth table, the check command and the
board — in the file the agent has in context at start.

**Do.** Render `$QD/templates/claude-block.md`:

| Placeholder | Value |
|---|---|
| `{{workflow_path}}`, `{{template_path}}` | `<docs_dir>/workflow.md`, `<docs_dir>/task-template.md` |
| `{{docs_dir}}`, `{{adr_dir}}` | Without trailing slash |
| `{{main_branch}}`, `{{task_prefix}}` | From the manifest |
| `{{sources_table}}` | A Markdown table, header `Domain \| Owner \| Notes`, one row per manifest `sources` entry, **and always, last:** `\| What currently exists \| The code \| Evidence of what *is* — never authority for what *should be* \|` |
| `{{lists}}` | As in Step 6 |
| `{{check}}`, `{{mutation}}`, `{{board_name}}` | From the manifest |
| `{{#mutation}}…{{/mutation}}` | Keep the text between the tags when the mutation command is non-empty; drop it and the tags otherwise |

Wrap the result in `<!-- quarterdeck:begin -->` and `<!-- quarterdeck:end -->` on their own
lines. Then splice it:

- If `CLAUDE.md` or `AGENTS.md` exists and already carries the markers, replace what is between
  them (markers included) and nothing else.
- Else if either file exists, append the block after one blank line. If both exist, do both.
- Else create `CLAUDE.md` with a one-line heading naming the project, a blank line, and the block.

**Validate.** In each carrier file, `grep -c 'quarterdeck:begin'` and `grep -c 'quarterdeck:end'`
both print `1`; `grep -c '{{'` prints `0`. `doctor` — **Rendered files**: every fact reported
`ok`. Then read the block back once as prose: a wrong path here is read by every future session.

### Step 8 — Wire the hook

**Goal.** `guard-main.py` runs before every Bash tool call and refuses the git operations that are
the owner's.

**Do.** Merge into `.claude/settings.json` (create it if absent; preserve every existing key and
hook):

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/guard-main.py\"" } ] }
    ]
  }
}
```

Do not add a second entry if one naming `guard-main.py` is already there.

**Validate.** `python3 -c 'import json; json.load(open(".claude/settings.json"))'` succeeds.
`doctor` — **The hook**: wired, and all ten fire cases `ok`. Those cases *are* the validation of
this step: a hook that is wired but never refuses anything is a rule that does not hold.

### Step 9 — CI

**Goal.** The two pull-request gates — first commit is tests only; the four sections present —
run on every pull request. When the project has a mutation command, its score runs on the main
branch after a merge, filtered to what the score depends on (workflow.md section 9).

**Do.**
- GitHub Actions and the owner said yes: copy `$QD/templates/ci/quarterdeck.yml` to
  `.github/workflows/quarterdeck.yml`; `ci` is `true` in the manifest.
- Another CI system: translate the two steps of that template into the project's CI
  configuration — both are one shell line each, with `fetch-depth: 0` (full history) as the only
  requirement — set `ci` to `false` in the manifest so `doctor` does not look for the workflow
  file, and tell the owner the job is theirs to maintain.
- No CI, or the owner said no: `ci` is `false`. Say what is *not* enforced as a result: the
  tests-first rule and the pull request body then rest on the prose in the skills.

**The mutation workflow** — only when `commands.mutation` is set, CI is GitHub Actions and the
owner said yes. Render `$QD/templates/ci/mutation.yml` to `.github/workflows/mutation.yml`. It is a
seed: skipped when the file exists, never touched by an upgrade, never checked by `doctor`.

| Placeholder | Value |
|---|---|
| `{{main_branch}}`, `{{core_dir}}`, `{{mutation}}` | From the manifest |
| `{{setup}}` | The steps that install the toolchain and the dependencies, indented as steps. Copy them from the project's existing CI job that runs the check command; with none, the ecosystem's official setup action and its lockfile install (`npm ci`, `pip install -r …`, `mix deps.get`, `go mod download`) |
| `{{paths}}` | One `      - '<glob>'` line each: `<core_dir>/**`; every directory `core_dir` imports from — read its imports, do not guess; every manifest test glob; the mutation tool's and the test runner's configuration files, the compiler configuration, the dependency manifest and lockfile, the toolchain version file; `.github/workflows/mutation.yml` |

For another CI system, translate it the same way — trigger on the main branch only, the same path
list — and tell the owner the job is theirs to maintain. Without a mutation command, skip this;
Step 11 brings it back.

**Validate.** GitHub: `cmp` the gates workflow against the template. Other CI: `grep` shows the CI
config referencing both `check-tests-first.py` and `check-pr-body.py`. Mutation workflow, when
written: `grep -c '{{' .github/workflows/mutation.yml` prints `0`, and every entry under `paths`
matches at least one tracked file — `git ls-files ':(glob)<entry>'` prints something for each, the
workflow file itself excepted until it is committed. A filter that matches nothing is a run that
never happens.

### Step 10 — Doctor

**Goal.** Zero failures.

**Do.** `python3 $QD/tools/doctor.py`. For each failure, go back to the step that owns it, fix,
and run `doctor` again. Warnings are reported to the owner verbatim; they are not yours to
silence.

**Validate.** Exit code `0`.

### Step 11 — Hand over

**Goal.** The owner knows exactly what was written and what is still theirs to do.

**Do.** Show `git status --short`. Then the by-hand list, with the project's real names:

1. Put the one-line digest of accepted ADRs directly under the block in `CLAUDE.md`. If
   `<adr_dir>` is empty, offer to draft ADR-0001 now — the one that names the layers and the
   import rule between them — from `<adr_dir>/adr-template.md`. Draft it only if asked; leave it
   uncommitted.
2. Configure the board: the seven statuses and the agent-writable lists (name them).
3. Add the language's dead-code tool to the check command twice — plainly, and a second time
   over the project without its tests, with every script the project runs that is not a test
   named as an entry of that run (workflow.md section 9) — and the boundary lint; add mutation
   testing on `core_dir`, and once it exists, set `commands.mutation` and seed its main-branch
   workflow (Step 9). Point at the README's *Tools by language* table for this ecosystem.
4. Validate every gate that reports a number against a case with a known answer: plant one
   test-only module — its import wrapped over several lines — one mutant, one boundary
   violation, and watch each fail.
5. Put one small task through `open → refine → todo → in progress → in review → done`. Nothing is
   installed until that has happened once.
6. Only when `commands.arch` is set: the recommended shape of the record is workflow.md section
   10 — a one-record registry, `diagrams.md` beside the record, with the folder's `README.md` as
   the authoring contract. Offer to copy `$QD/templates/diagrams.md` there as a starter, with the
   example record edited to the project's file name. It is a seed: written once if asked, never
   touched by an upgrade, never checked by `doctor`.

Do not commit anything.

## Upgrade

**Goal.** The project runs the version in `$QD/VERSION` without losing a single local decision.

This skill cannot update itself. If `$QD/VERSION` equals the manifest's `quarterdeck` field, tell
the owner to run `npx skills update quarterdeck-setup` first and stop; a newer `$QD` is the
precondition.

1. Read the manifest; note its `quarterdeck` version. Run `doctor` and collect the **Shipped
   files** failures — those are the files that changed upstream, or were edited locally, or are
   installed under a path this version no longer uses (reported as *stale*), or are new in this
   version (reported as *missing*).
2. **Renamed paths first.** `doctor` names each stale path and its replacement. Move it —
   `git mv .claude/skills/grill-task .claude/skills/refine` for the 0.3.0 rename, `git mv
   tools/quarterdeck/check-pr-evidence.py tools/quarterdeck/check-pr-body.py` for the gate
   renamed when the evidence block was dropped — so that a local edit travels with it, then treat
   the moved file as any other in the next step. Nothing may remain at the old path: two skills
   with one job is exactly the ambiguity the rename removes. A renamed tool is also referenced
   from the CI workflow; Step 9's validation catches the old name there.
3. For each: `diff` the project's copy against `$QD`'s. If the project copy carries a local edit
   (the owner will recognise it), **stop for that file** and propose moving the edit upstream —
   a local edit to a shipped file is lost at the next upgrade by design. Otherwise overwrite.
4. If `$QD/templates/claude-block.md` or the board template differs from what the project's
   rendered files reflect, re-run Steps 6 and 7 and show the owner the diff of the rendered
   result before writing it. Never touch text outside the block.
5. If the manifest schema gained a key (compare against the [reference](#reference-the-manifest)),
   ask for its value the way Step 2 would, and add it. If the default `sources` rows gained one
   — 0.3.0 added *The plan* — offer it the way Step 2 question 10 would; a row the owner accepts
   goes into the manifest and the block is re-rendered.
6. **0.3.2 moved mutation off the pull request.** When `commands.mutation` is set and no
   `.github/workflows/mutation.yml` exists, offer the mutation workflow the way Step 9 does. If
   the project's CI runs mutation on pull requests, point at workflow.md section 9 and leave that
   job alone: it is the project's.
7. **0.4.0 retired `test-only-modules.py`.** It read imports with a regular expression and could
   not see one the formatter wraps (workflow.md section 9); `doctor` reports it as retired.
   Delete `tools/quarterdeck/test-only-modules.py` and take it out of the check chain — the
   project's own script, and `commands.check` when it names the file, then re-render the block
   (Step 7) — and out of any CI configuration that names it. In its place, chain the project's
   dead-code tool a second time over the project without its tests (README, *Tools by
   language*), with every script the project runs that is not a test named as an entry of that
   run; run it and see it exit `0` before it goes in. Then plant one module imported only by its
   test through a wrapped import, see the run report it, and delete it. Where the ecosystem's
   tool has no such run, tell the owner the rule is theirs to write, as the
   [ecosystem defaults](#reference-ecosystem-defaults) say. Nothing reads `source_dirs` or
   `import_aliases` any more: delete both from the manifest.
8. **0.4.1 added `/retro`.** `doctor` reports `.claude/skills/retro/SKILL.md` and
   `.claude/skills/retro/digest.py` as missing; copy both as Step 4 does. Nothing else is to be
   done: the skill reads the manifest as it stands, and is run by hand — nothing in the workflow
   calls it.
9. **0.5.0 added `/milestone-code-review`.** `doctor` reports
   `.claude/skills/milestone-code-review/SKILL.md` as missing; copy it as Step 4 does. The same
   version changes `workflow.md` sections 9 and 11 and the `/retro` skill, which step 3 overwrites
   like any shipped file. Nothing else is to be done: the skill reads the manifest as it stands,
   files only into `board.lists` and only what the owner picks, and is run by hand at a milestone
   boundary — nothing in the workflow calls it.
10. Set `quarterdeck` in the manifest to `$QD/VERSION`.
11. `doctor` exits `0`. Show `git status --short`. Do not commit.

Seeded files are never touched by an upgrade. If a seed's template changed upstream, tell the
owner what changed and leave the merge to them.

## Verify

Run `python3 $QD/tools/doctor.py` and report it as it is: each failure with the step that fixes
it, each warning with what it means for the five failure modes (the **Readiness** section at the
end says which are answered mechanically and which only by prose). Change nothing unless asked.

## Reference: the manifest

```json
{
  "quarterdeck": "0.3.0",
  "main_branch": "main",
  "task_prefix": "task/",
  "docs_dir": "docs/workflow",
  "adr_dir": "docs/adr",
  "domain_doc": "docs/prd.md",
  "board": {
    "kind": "github",
    "name": "GitHub Issues",
    "statuses": {
      "open": "open", "refine": "refine", "todo": "todo", "in progress": "in progress",
      "in review": "in review", "done": "done", "closed": "closed"
    },
    "lists": ["Bugs", "Open decisions"]
  },
  "commands": {
    "check": "npm run typecheck && npm run lint && npx knip && npx knip --production && npm test",
    "test": "npm test",
    "mutation": "npm run test:mutation",
    "arch": ""
  },
  "core_dir": "src/core",
  "test_globs": ["**/*.test.ts", "**/__tests__/**"],
  "agent_signature": "Claude <noreply@anthropic.com>",
  "ci": true,
  "sources": [
    {"domain": "Architecture, layer boundaries, structural rules", "owner": "`docs/adr/`", "notes": "An ADR is amended, never contradicted in silence"},
    {"domain": "Scope of the change being made right now", "owner": "The task on GitHub Issues", "notes": "What we want, and how, *today*"},
    {"domain": "The plan: milestones, ordering, dependencies, what is next", "owner": "The GitHub Issues board", "notes": "`list:` labels are the milestones, `waiting_on:` lines are the dependencies, `status:` labels are the state. There is no plan file"},
    {"domain": "Product rules, formulas, constants, lexicon", "owner": "`docs/prd.md`", "notes": "The design intent"}
  ]
}
```

| Field | Read by |
|---|---|
| `main_branch`, `task_prefix` | the hook, `/implement`, `doctor`; `/milestone-code-review` reads `main_branch` |
| `docs_dir`, `adr_dir`, `domain_doc` | the skills, `doctor` |
| `board.*` | the skills (through `board.md`), `doctor` |
| `commands.*`, `core_dir`, `agent_signature` | `/implement`; `/retro` reads `commands.check`, `commands.mutation` and `core_dir`; `/milestone-code-review` reads `commands.check` |
| `test_globs` | `check-tests-first.py`, `/implement`, `/milestone-code-review`, `doctor` |
| `ci`, `sources`, `quarterdeck` | `doctor`; `sources` also renders the instruction block |

## Reference: ecosystem defaults

Fallbacks for Step 1 when the project's own configuration says nothing. Always prefer what the
repository actually declares.

| Marker | Test | Check | Test globs | Sources |
|---|---|---|---|---|
| `tsconfig.json` | `npm test` | `npm run check`, or compose from `typecheck`, `lint`, `format:check`, `knip` scripts | `**/*.test.ts`, `**/*.test.tsx`, `**/*.spec.ts`, `**/__tests__/**` | `src` |
| `package.json` | `npm test` | as above | `**/*.test.js`, `**/*.spec.js`, `**/__tests__/**` | `src` |
| `pyproject.toml`, `setup.py`, `requirements.txt` | `pytest` | `ruff check . && pytest` when ruff is configured, else `pytest` | `tests/**`, `**/test_*.py`, `**/*_test.py`, `**/conftest.py` | `src` |
| `mix.exs` | `mix test` | `mix format --check-formatted && mix compile --warnings-as-errors && mix test` (+ `mix credo --strict`, `mix dialyzer` when configured) | `test/**` | `lib` |
| `go.mod` | `go test ./...` | `go vet ./... && go test ./...` | `**/*_test.go` | `.` |
| `Cargo.toml` | `cargo test` | `cargo clippy --all-targets && cargo test` | `tests/**` | `src` |
| `pom.xml`, `build.gradle(.kts)` | `mvn test` / `gradle test` | `mvn verify` / `gradle check` | `**/src/test/**` | `src/main` |
| `*.sln`, `*.csproj` | `dotnet test` | `dotnet build && dotnet test` | `**/*.Tests/**`, `**/*Tests.cs` | `src` |
| `Gemfile` | `bundle exec rspec` | `bundle exec rubocop && bundle exec rspec` | `spec/**`, `test/**` | `lib`, `app` |
| `composer.json` | `vendor/bin/phpunit` | `vendor/bin/phpunit` | `tests/**` | `src` |
| `Package.swift` | `swift test` | `swift build && swift test` | `Tests/**` | `Sources` |

The test-only rule is the dead-code tool run a second time over the project without its tests;
the README's *Tools by language* table names that run where the ecosystem has one. Where it has
none, tell the owner the rule in one sentence — *a source file whose every importer is a test file
fails the build* — and that the equivalent is theirs to write into the check chain, reading the
import graph with the compiler or a parser, never with a regular expression.
