---
name: implement
description: Implement one approved task end to end - pre-flight readiness check, task branch, tests first, the check chain, mutation testing, the architecture record, and a pull request with its evidence block. Use when asked to implement a task that is in todo.
---

# Implement a task

This is the order of work. Do not reorder it; each step exists because something goes wrong
without it. The full rules are in the workflow document named below.

## Before anything: the project's bindings

Read `.quarterdeck.json` in the repository root once. Everything project-specific below comes
from it:

| Field | Used for |
|---|---|
| `main_branch`, `task_prefix` | The owner's branch, and how task branches are named |
| `docs_dir` | `<docs_dir>/workflow.md` is the rulebook; `<docs_dir>/task-template.md` the form; `<docs_dir>/board.md` **the board procedures — read it before touching the board** |
| `adr_dir` | Decision records |
| `domain_doc` | The owner of product rules, formulas and constants (`none yet` is possible) |
| `commands.check`, `commands.test`, `commands.mutation`, `commands.arch` | The check chain, the tests alone, mutation testing, the architecture-record renderer. Empty means the project has none |
| `core_dir` | The pure, deterministic area mutation testing is scoped to |
| `test_globs` | What counts as a test file — the tests-first check uses the same list |
| `agent_signature` | The `Co-Authored-By:` line on every commit |
| `board.lists` | The only lists an agent may create tasks in |

The sources-of-truth table is in the agent instructions, already in context. Code is evidence of
what *is*, never authority for what *should be*. Two sources disagreeing is a tier-3 stop (below),
never something to resolve by choosing.

## 1. Pre-flight — refuse an unready task

Read the task and check every line of the definition of ready:

- The status is `todo`. A task in any other status is not yours to start.
- Every field of the template is filled, and *Open questions* reads `none`.
- Every acceptance line is a command or an asserted number.
- Every task this one waits on is `done`.
- Nothing references an unresolved entry in the `Open decisions` list.

**If any of it fails: comment on the task naming exactly what is missing, move it to `refine`, and
stop.** Never assume, never fill the gap yourself, never proceed "to save a round trip".

Read the sources the specification cites before writing anything — the sections of the domain
document, the ADRs, the code in the area. The specification is the scope; the cited sources are
the substance.

## 2. Branch

Move the task to `in progress`, then:

```bash
git checkout <main_branch> && git pull --ff-only
git checkout -b <task_prefix><task-id>-<slug>
```

Work in the main tree while one task is in flight at a time.

## 3. Tests first, and let them fail

The **first commit on the branch contains test files only, and they fail.** That commit is the
evidence that the tests were written against the specification rather than against the
implementation — it is the whole defence against a test that asserts whatever the code happened to
do. `tools/quarterdeck/check-tests-first.py` checks it on the pull request; test files are the
paths matching `test_globs`.

Write them from the acceptance criteria and the contract:

- Assert **the number in the domain document**, never the number the implementation returns.
- Prefer a property or a table over an example where the contract is a formula.
- A golden run — committed inputs and a committed hash of the result — is the right shape for
  anything deterministic.
- **Never add an inline snapshot under `core_dir`.** A snapshot records whatever the code did,
  which is a fake test in machine-readable form.

Commit as `Add tests for <what>`, with the trailers `Task: <task-id>` and
`Co-Authored-By: <agent_signature>`.

## 4. Implement

Make them pass. Nothing more: the *Out of scope* field is binding, and code with no caller is
dead code.

## 5. Verify

Run what the specification's *Verification* field lists — at minimum `commands.check`, and
`commands.mutation` when the project has one and the task touches `core_dir`.

**Three consecutive failures of the same failure and you stop**: comment on the task with what you
tried, move it to `refine`, open nothing. Different errors in sequence are progress; the same
assertion three times is being stuck — and the next attempt is where a test gets weakened.

**Never weaken, skip or delete a test to make a suite pass.**

## 6. Architecture

Unconditional step, whatever the task was.

**The project keeps an architecture record** (`commands.arch` is set). Read the architecture
diagram's record and decide whether this change alters it: a component or relationship added or
removed, a boundary moved, or a planned (dashed) relationship the task just made real is a
**structural** change; a box that merely moved is not. The other diagrams in the folder, if any,
are refreshed only on request, never here.

*No:* say so in the pull request; regenerate nothing.

*Yes:* update the record through the project's diagram tool, never by hand. If the project keeps
a registry (`diagrams.md` beside the record — workflow section 10), take the architecture
diagram's record from it and add one sentence saying what this task added, removed or made real,
in the words of the specification's *Scope*; the folder's `README.md` is the contract the file is
authored under. Then run `commands.arch` and commit the record and the image it renders. Read the
record's diff before committing — the pull request states each structural change in the words of
that diff. **If the change is structural and no ADR was added or amended, the pull request must
say why not.**

**The project keeps no architecture record** (`commands.arch` is empty). If the change adds a
layer, a boundary or a relationship between layers that an ADR describes, the pull request says so
under *Architecture*; otherwise it says "no architecture change".

## 7. Pull request

```bash
git push -u origin <task_prefix><task-id>-<slug>
gh pr create --title "<the task name, verbatim>" --body-file <the evidence block>
```

The evidence block is specified in section 8 of the workflow, and `.github/pull_request_template.md`
carries its skeleton: task link · each acceptance criterion with the output or number that proves
it · verification results including the mutation score and its delta · the architecture verdict ·
**the tier-2 decisions log** · what was deliberately not done. The tier-2 section is mandatory even
when it reads `none`. `tools/quarterdeck/check-pr-evidence.py` fails the pull request when a
section is missing.

Then comment the pull request link on the task and move it to `in review`.

## The three tiers, while you work

| Tier | What | Do |
|---|---|---|
| 1 | Naming, file layout, private helpers, test arrangement | Decide silently |
| 2 | A real choice that changes neither architecture nor a product rule | Decide, and log the choice **and the rejected alternative** in the pull request |
| 3 | A number or rule in the domain document, a new dependency, a layer boundary, a public type other layers use, a contradiction between sources | **Stop.** Comment, move the task to `refine`, open nothing |

## Never

- Never commit on `main_branch`, never merge, never rebase, never force-push, never merge a pull
  request. A hook refuses these; the rule is here so you do not have to discover it.
- Never mark a task `done` and never close one.
- Never create a task outside the lists named in `board.lists`.
