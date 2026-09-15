---
name: grill-task
description: Refine one task on the board into an implementable specification through a relentless interview, then write it back to the board. Use when asked to grill, refine or specify a task, or when a task must be made ready for an agent.
---

# Grill a task

A human-present skill. It turns a conversation into a specification an agent can implement without
guessing. Nothing here is implemented; this skill produces prose only.

## Before anything: the project's bindings

Read `.quarterdeck.json` in the repository root once. It names:

- `docs_dir` — the workflow directory (default `docs/workflow`). The procedure is
  `<docs_dir>/workflow.md` sections 4 and 5; the form is `<docs_dir>/task-template.md`; the board
  procedures — how to read, move, comment on and create a task on *this* project's board — are
  `<docs_dir>/board.md`. Read the board file before touching the board.
- `adr_dir` — where decision records live.
- `domain_doc` — the document that owns product rules, formulas and constants, or `none yet`.
- `board.lists` — the only lists an agent may create tasks in.

The sources-of-truth table is in the agent instructions (`CLAUDE.md` / `AGENTS.md`), already in
context. Code is evidence of what *is*, never authority for what *should be*. Code that contradicts
the domain document is a bug report, not a source conflict. Two sources disagreeing is a thing to
report, naming both sides — never to resolve by choosing.

## 1. Gather, before asking anything

Facts are yours to find; only decisions belong to the user. Never ask what you can read.

- The task itself, including its subtasks, comments and dependencies.
- Every source the task touches: the sections of the domain document, and the code that already
  exists in the area. For ADRs, the digest in the agent instructions is already in context; open
  a full record in `<adr_dir>/` only when the task touches its area.
- Whether any task in the `Open decisions` list stands in the way.
- Whether every task this one waits on is `done`, and whether any of them left open questions
  behind.

Then move the task to `refine` and say what you found missing.

## 2. Interview in rounds

Map the task as a design tree; work the frontier — every decision whose prerequisites are already
settled. Ask the whole frontier in one round, numbered, each with your recommended answer. Wait.
Recompute the frontier from the answers. A question that depends on an answer you have not heard
belongs to a later round.

Put the trade-off, not just the choice. Where the domain document carries two competing ideas,
name both and say which you would keep and why.

## 3. Write the prose

Some answers are bigger than the task:

- An architectural choice becomes an ADR in `<adr_dir>/`, drafted here from
  `<adr_dir>/adr-template.md`, approved before any code exists. Name the alternatives rejected
  and why.
- A changed rule, constant or lexicon entry becomes an edit to the domain document. The domain
  document is the owner of those, so it is edited — not shadowed in the task. If the project has
  no domain document yet, say so, and record the rule in the task with *decision in this task* as
  its source.
- A decision that settles an `Open decisions` entry closes it there too, once the user agrees.

Leave these in the working tree. Committing them is the user's.

## 4. Finish, on the user's word only

Moving a task out of `refine` is the user's decision. You perform the write; you do not make the
call. Wait to be told which of these applies.

**Refining is finished.** Write the filled template into the task description, then set the status
to `todo`. Before you write it, check it yourself:

- Every field of the template is present.
- **Every line cites its source** — a section of the domain document, an ADR, a file and line,
  or a decision recorded in this task. An uncited line is an invention.
- Every acceptance line is a command to run or a number to assert. No opinions. If one cannot be
  written that way, it is not acceptance — either the task is not ready or the criterion is dropped
  and named under *Out of scope*.
- *Open questions* reads `none`.

**Refining is not finished.** Write what was settled and the questions still outstanding into the
task, and move it back to `open`. A task never sits in `refine` between sessions — `refine` means
a conversation is live.

## Never

- Never move a task to `todo` on your own judgement.
- Never mark a task `done`, and never close one.
- Never create a task outside the lists named in `board.lists`.
- Never fill a field by inference and leave it uncited. Escalate instead: a required field that
  cannot be quoted or directly derived from a named source is exactly what `refine` is for.
- Never start implementing. That is `/implement`, and it begins only after the user approves.
