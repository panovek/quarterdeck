# Agent workflow

How a task travels from an idea to a merged commit when an agent does the writing.

This document is doctrine, not a suggestion. It exists to answer five specific failure modes of
handing implementation to an agent, and every rule below traces back to one of them:

1. **Building on undecided ground.** The task rests on a question nobody has answered — or the
   design documents carry two competing answers — and the agent picks one silently.
2. **Losing the thread.** After a few weeks nobody knows how the project works, what was decided,
   or why.
3. **Invented work.** Code that exists so that there is something to test or something to show: a
   settings module with fake settings, a helper nothing calls.
4. **Tests that prove nothing.** Tests that assert nothing, or assert whatever the implementation
   happened to do.
5. **Silent improvisation when blocked.** What an agent does when its task rests on a dependency
   that is not done or a question nobody has answered — and how anyone finds out.

The words *board*, *main branch*, *check command* and *domain document* below are bound to this
project's real names in `.quarterdeck.json`; the skills, the hook and the checks read that file.

## 1. The principle

**Any rule that must hold is executable, or it does not hold.**

A rule written in prose is a rule a model negotiates with. A rule that fails a command is a rule
it cannot get past. Every guardrail below is built to that pattern where it can be, and the few
that cannot be are named honestly in section 9.

## 2. Sources of truth

Authority is per domain, not a single ranking. Each domain has exactly one owner, and the owners
are listed in the *Sources of truth* table of `.quarterdeck.json` and repeated in the agent's
instructions. The shape is always the same:

| Domain | Owner | Notes |
|---|---|---|
| Architecture, layer boundaries, structural rules | The ADR folder | An ADR is amended, never contradicted in silence |
| Scope of the change being made right now | The task on the board | What we want, and how, *today* |
| The plan: milestones, ordering, dependencies, what is next | The board | Lists (or milestones or labels, per board kind) are the milestones, blocking links are the dependencies, statuses are the state. There is no plan file |
| Product rules, formulas, constants, lexicon | The domain document | The design intent — a PRD, a design document, a spec, an API contract |
| What currently exists | The code | Evidence of what *is* — never authority for what *should be* |

A project that has no domain document yet says so in the table. That is allowed, and it is
recorded so that everyone knows failure modes 1 and 2 are only half-answered until one exists.

The domain document is large and will not always keep pace with small changes. That is expected
and tolerated. What is not tolerated is inferring intent from an implementation: code that
contradicts the domain document is **a bug report**, not a source conflict.

**What an agent has in context when it starts.** The agent instruction file (`CLAUDE.md` or
`AGENTS.md`) and nothing else: the rules, the lexicon, and the one-line ADR digest. Everything else
is read on demand — the sections of the domain document a task cites, the full ADR whose area a
task touches, the code in the area, the task's neighbours on the board, this document when a
skill points at a section. The agent notes are never loaded; they are a log for a person.

**On contradiction, stop.** If two sources disagree within their own domains, or a task's
specification cannot be reconciled with an ADR or the domain document, the agent stops, reports
the contradiction and names both sides. It does not choose.

## 3. The task lifecycle

Statuses on the board, in order. A board that uses other names maps them in `.quarterdeck.json`;
the meaning does not change.

| Status | Meaning |
|---|---|
| `open` | An idea, or a description that has not been turned into a specification |
| `refine` | Under discussion — being grilled, or sent back because a question surfaced |
| `todo` | Specified, approved, and eligible for an agent |
| `in progress` | An agent (or the owner) is working on it |
| `in review` | A pull request exists and is waiting for the owner |
| `done` | Merged |
| `closed` | Dropped or cancelled — reachable from any status |

Who may move what:

| Transition | Decided by | Written by |
|---|---|---|
| `open → refine` | The owner — starting a grilling session is a human act | Either |
| `refine → todo` | **The owner. Approving a specification is the last gate before code** | An agent, on instruction: it writes the refined content into the task in the template's shape, then moves the status |
| `refine → open` | The owner, when refining is not finished | An agent, on instruction: it records what was settled and what remains open, then moves the status back |
| `todo → in progress` | Agent | Agent |
| `in progress → in review` | Agent, when the pull request is open and the evidence block is filled | Agent |
| `in progress → refine` | Agent, when a question it may not answer surfaces (section 6) | Agent |
| `in review → done` | The owner, on merge | The owner |
| anything `→ closed` | The owner only | The owner only |

**Deciding and writing are separate.** Every transition in the first three rows is the owner's
decision; the board write that carries it out is ordinary work an agent does when told to. An
agent moving a task because it was told to is not an agent deciding.

An agent never closes a task and never marks one done. Closing is the owner's signal that the
work was reviewed; if an agent could do it, the board would become fiction.

An agent may **create** tasks in the agent-writable lists only — by default `Bugs` and
`Open decisions` — because "I found something I cannot answer" needs a cheap, honest destination,
and it belongs on the board rather than buried in a session transcript. It creates nothing in a
milestone or feature list.

## 4. Definition of ready

A task is eligible for an agent only when all of the following hold. This is the answer to
failure mode 1: the point is not that everything is known, but that *what is unknown is visible before
work starts.*

1. Every field of the task template is filled.
2. Every acceptance criterion is checkable by a command or is an asserted number — never an opinion.
3. No unresolved open decision (the `Open decisions` list) is referenced.
4. Every `waiting_on` task is `done`.
5. Every field cites its source.

**The citation rule is load-bearing.** Each line of a specification names where it came from — a
section of the domain document, an ADR, a file and line, a decision recorded in the task. An
uncited line is an invention, and can be spotted as one without checking anything. This is what
makes approving a specification a two-minute read rather than a second design session.

### The task template

Held canonically at `task-template.md` beside this file; the filled instance lives in the task's
description on the board.

| Field | Content |
|---|---|
| **Goal** | One sentence: why this task exists |
| **Scope** | What changes, in modules and files |
| **Out of scope** | Explicitly what is not built here |
| **Contract** | Formulas, constants, types, signatures — each with its source |
| **Acceptance** | Each line a command to run or a number to assert |
| **Verification** | The exact commands the agent runs before requesting review |
| **Open questions** | Must be empty for the task to leave `refine` |
| **Risk** | Optional. Reserved for a later rule about which tasks need closer review |

## 5. `/refine`

A human-present skill. It turns a conversation into a specification.

1. Read the task and its place on the board — its list or milestone, its blocking and blocked-by
   links, its siblings in the milestone — then the sections of the domain document it touches,
   relevant ADRs, and the code that already exists in the area.
2. Grill: put the unresolved decisions to the owner one round at a time, recommending an answer
   for each.
3. Where a decision is architectural, draft the ADR. Where it changes a rule or a constant, draft
   the domain-document delta. **Prose is approved before any code exists.**
4. On the owner's word that refining is finished: write the filled template into the task
   description, every field cited, and move the task to `todo`.
5. On the owner's word that it is *not* finished: write what was settled and the questions still
   outstanding into the task, and move it back to `open`. A task never sits in `refine` between
   sessions — `refine` means a conversation is live.

Escalation triggers — a specification cannot be completed and the task stays in `refine` — when a
required field cannot be filled by quoting or directly deriving from a named source; when an
unresolved open decision is in the way; when two sources disagree; or when an acceptance criterion
cannot be expressed as a command or a number.

## 6. `/implement`

The agent's loop, in order:

1. **Pre-flight.** Re-check the definition of ready (section 4). A task that fails it goes back to
   `refine` with a comment naming the missing field — never "I will assume and proceed".
2. Move the task to `in progress`. Create the branch (section 7). Work in the main tree while one
   task is in flight at a time.
3. **Tests first.** The first commit on the branch contains test files only, and they fail. The
   branch history is the evidence that the tests were written against the specification and not
   against the implementation. `tools/quarterdeck/check-tests-first.py` checks this on a pull
   request.
4. Implement.
5. Run the check command — typecheck, lint, format, dead code, tests, whatever the project chains.
6. Run the mutation command where the task touches the mutation-tested area (section 9).
7. **Architecture.** If the project keeps an architecture record, review it against the change
   and, through the project's diagram tool with the diagram's record from the registry, update it
   if the change warrants it. This step is unconditional; its *conclusion* may be "no change",
   which is then stated in the pull request. See section 10.
8. Open the pull request, fill the evidence block (section 8), comment the pull request link on
   the task, and move it to `in review`.

### What the agent may decide

| Tier | Examples | Behaviour |
|---|---|---|
| 1 — decide silently | Naming, file layout, private helpers, test arrangement | Just do it |
| 2 — decide and log | A real choice with a defensible answer that changes neither architecture nor a product rule | Proceed, and record the choice **and the rejected alternative** in the pull request |
| 3 — stop | Changes a rule or number in the domain document; adds a dependency; crosses a layer boundary; alters a public type other layers use; contradicts a source | Task back to `refine` with a comment. No pull request |

### The retry budget

Three consecutive failures **of the same failure** and the agent stops: it comments on the task
with what it tried and moves the task to `refine`. No draft pull request is opened.

"The same failure" is the point. An agent working through three different errors is making
progress. An agent hitting the same assertion three times is stuck — and the fourth attempt is
where it starts weakening the test to make the suite green.

**Never weaken, skip or delete a test to make a suite pass. Stop instead.**

## 7. Branch, commit and pull request conventions

- **Branch:** `<task prefix><task-id>-<slug>` — by default `task/<id>-<slug>`.
- **Commit subject:** verb first, imperative, as the existing history reads. No task identifier in
  the subject.
- **Commit trailers:** every agent commit carries `Task: <task-id>` and a `Co-Authored-By:` line
  naming the agent, so `git log` can separate agent work from the owner's forever.
- **Pull request title:** the task name verbatim.
- **Merging is the owner's**, followed by deleting the branch. An agent never merges, never
  pushes to the main branch, never rebases and never force-pushes.

## 8. The pull request evidence block

The body of every agent pull request, so that reviewing it requires running nothing.
`tools/quarterdeck/check-pr-evidence.py` fails a pull request whose body lacks a section.

```markdown
## Task
<task-id> · <task name> · <link>

## Acceptance
- [x] <criterion> — <the command output or number that proves it>
- [x] <criterion> — <...>

## Verification
- `<check command>` — pass
- mutation score — 84.2% (previous 83.1%)
- dead code — clean

## Architecture
No change. / Updated: `+ component <name>`, `+ relationship <a> → <b>` — see the image and the record diff.

## Decisions made (tier 2)
- <choice> — chose X over Y because <reason>.
- (or: none)

## Not done
- <anything deliberately left out, and why>
```

The tier-2 section is mandatory even when empty. An explicit "none" is information; a missing
section is ambiguity.

## 9. Guardrails

Each rule sits on the cheapest surface that can actually enforce it.

| Rule | Surface |
|---|---|
| No commits, pushes, merges or rebases on the main branch; no force-push; no merging a pull request | **Hook** — `.claude/hooks/guard-main.py`, a `PreToolUse` guard that refuses the tool call outright |
| A module that exists only to be tested | **Check command** — `tools/quarterdeck/test-only-modules.py`, or the project's own equivalent |
| Dead files, unused dependencies | **Check command** — the language's dead-code tool (README, *Tools by language*) |
| Tests that do not detect a wrong answer | **CI on pull requests** — mutation score on the pure area, threshold ratchets and never falls |
| Layer boundaries | **Check command** — the language's boundary lint, one rule per ADR |
| First commit on a branch is failing tests only | **CI on pull requests** — `tools/quarterdeck/check-tests-first.py` |
| Every evidence section present | **CI on pull requests** — `tools/quarterdeck/check-pr-evidence.py` |
| Source precedence, the three tiers, the retry budget, never weakening a test | **Agent instructions** — judgement, not mechanism |

**Invented work — and what actually catches it.** Dead-code tools are not enough: a module
imported by its own test is *used* as far as they are concerned, so the settings-module-with-fake-
settings passes them cleanly. What catches it is a check that fails when every importer of a source
file is a test file, naming the file and its tests. The companion rule lives in the agent
instructions because no tool can check it: *coverage is never a reason to create a consumer — if
the only caller of a thing is its own test, the thing is deleted, not tested.*

**Mutation testing.** Line coverage is exactly the metric a model games; mutation score is not,
because it asks the only question that matters — does this test fail when the answer is wrong?
Scope it to the part of the code that is pure and deterministic, so a full run takes seconds, and
record the scope in an ADR so that no agent helpfully widens it. The threshold ratchets upward and
never falls: a branch that lowers it weakened a test.

**A gate is validated against a case with a known answer before its number is believed.** A
mutation tool that cannot activate mutants under a new test-runner version reports survivors that
a manual edit proves are killed; a hook that never fires is a rule that does not hold.
Quarterdeck's `doctor` runs the hook against commands it must refuse. Do the same by hand for every
gate that reports a number — plant one mutant, one test-only module, one boundary violation, and
watch it fail.

**Two more test oracles.** Table assertions — a test asserts the number printed in the domain
document, never the number the implementation returned — and golden runs, where the same inputs
must produce the same committed hash. **New inline snapshots in the mutation-tested area are
banned**: a snapshot records whatever the implementation did, which is the machine-readable form
of a fake test.

## 10. The architecture record

Optional, and narrow when present: see at a glance how the system fits together, and what a pull
request did to it. Nothing more is bought, and nothing more is paid for. A project that keeps one
sets `commands.arch` in `.quarterdeck.json` to the command that renders it; a project that keeps
none leaves it empty and section 6 step 7 reduces to the sentence in the pull request.

**The record is text.** A JSON or YAML map of components and relationships, or a C4 model —
committed, so that a diff reads as `+ component`, `+ relationship`, reviewable as text. If the
project renders images from it, one image per diagram is committed — the current picture — and
the renderer's HTML is not. **No per-pull-request delta image is produced.** The text diff of the
record says what changed and the reviewer's image diff of the committed picture shows it; a third
artefact saying the same thing is noise.

**The recommended shape is a one-record registry.** Beside the record lives a registry file —
`diagrams.md` — with one record per diagram: the file name and two or three plain sentences saying
what the owner wants to see on it. That record *is* the prompt: an agent hands it to the project's
diagram tool (Archify, for example — any renderer that takes a prompt and writes the record will
do) and authors the file under the contract in the folder's `README.md`, which holds every fixed
rule once — evidence first, one question per diagram, semantic labels, stable ids kept on refresh,
the project's lexicon, no subtitle, the node ceiling — so that no record has to repeat one. The
registry is the only list of diagrams there is: to sharpen a picture, edit its sentences; to add
one, add a record; to remove one, delete the record and its files. Nothing in the workflow or the
tooling enumerates the diagrams, so the list changes without anything else changing. A starter
registry ships with the setup skill as `templates/diagrams.md`.

**Only the architecture diagram is in the per-task loop.** Every other record in the registry —
behaviour drawn as a lifecycle, a sequence, a dataflow, a workflow — is refreshed deliberately, on
request, when the thing it draws changes. They change rarely; putting them under a per-task rule
buys nothing.

**What counts as a structural change** is read from the record's diff: a component or relationship
added or removed, a boundary moved, or a planned (dashed) relationship made real. A box that
merely moved is not one. When nothing changed, nothing is regenerated and the pull request says
"no architecture change" — an unchanged image committed on every pull request is noise. If the
record changed structurally and no ADR was added or amended, the pull request must say why not.

## 11. When a pull request is rejected

Three shapes, three responses:

- **Trivially wrong** — comment, the agent iterates on the same branch.
- **Wrong approach** — branch deleted, task back to `refine`, reason recorded in a comment on the
  task.
- **Wrong specification** — the specification was approved and still produced the wrong thing.
  This is a defect in the rules, not in the code.

For the third case, append one line to `agent-notes.md`. At each milestone boundary the notes are
read: anything that recurs is promoted into the agent instructions, the task template, or a lint
rule. Without this, the same class of rejection repeats forever and the conclusion slowly becomes
"the workflow does not work" — when what actually failed was a rule nobody wrote down.

## 12. Parked on purpose

Recorded so that they are not silently reopened.

- **Risk levels on tasks.** The field exists in the template; the rule that high-risk tasks need
  closer review is not written yet.
- **Autonomous specification drafting** for a legacy backlog. Deferred until hand-grilling a
  milestone shows whether it is needed.
- **Parallel agents.** One task at a time. With human review on every merge, N agents produce N
  pull requests queued on one reviewer, and every merge invalidates the others' base.
- **A plan file mirrored from the board.** Rejected shape: two mirrors drift, and the board is
  where statuses, dependencies and comments already live. The board is the plan — section 2.
- **A per-pull-request delta image of the architecture record.** Rejected shape: the text diff of
  the record and the image diff of the committed picture already say what changed — section 10.

## Appendix — which mechanism answers which failure mode

| Failure mode | Mechanism |
|---|---|
| 1 · Building on undecided ground | Definition of ready (4); `refine` as a real status (3); escalation triggers (5); tier 3 stops mid-task (6) |
| 2 · Losing the thread | Specification approved before code exists (5); ADR required for architectural choices (2, 10); the architecture record, redrawn from its registry record, and its per-pull-request verdict (10); the tier-2 decisions log (8) |
| 3 · Invented work | The test-only-module check (9); dead-code tools (9); the *Out of scope* field (4); "coverage is never a reason to create a consumer" (9) |
| 4 · Tests that prove nothing | Mutation score, not coverage (9); table assertions and golden runs (9); tests-first commit as branch evidence (6, 9); the ban on weakening a test (6) |
| 5 · Silent improvisation when blocked | `waiting_on` checked in pre-flight (4); the three tiers (6); the retry budget (6); agents may file into the agent-writable lists, and nowhere else (3) |
