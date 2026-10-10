---
name: retro
description: Look back at one agent session - this one, a past one, or the one behind a pull request - find where it struggled, trace each struggle to what in the repository let it happen, and propose ranked changes to the agent's environment. Writes nothing until the user picks. Use when asked for a retro or a retrospective of a session.
disable-model-invocation: true
argument-hint: '[session id | PR <number>]'
---

# Retro

A human-present skill. It reads one session and asks one question of every place the agent
struggled: **what in this repository let that happen?** The answer is a change to the agent's
environment — a check, a hook, a pointer, a line of the agent instructions, or the deletion of
one. Never a change to the product.

It proposes; the user picks; only then is anything written. A retro is not memory. "Be more careful
next time" is not a finding. A finding changes the repository so the next session cannot make the
same mistake, or does not have to search for the same fact again.

## Before anything: the project's bindings

Read `.quarterdeck.json` in the repository root once. It names:

- `docs_dir` — `<docs_dir>/workflow.md` is the rulebook this skill serves: section 1, *any rule
  that must hold is executable, or it does not hold*, and section 9, each rule on the cheapest
  surface that can actually enforce it. `<docs_dir>/board.md` is how to read a task on this
  project's board — read it before touching the board.
- `main_branch`, `task_prefix` — the owner's branch, and how a task branch is named.
- `domain_doc`, `adr_dir` — the owners of product rules and of architecture. Neither is this
  skill's to change.
- `commands.check`, `commands.mutation`, `core_dir` — the check chain a new check joins, and the
  mutation scope a retro never moves.
- `board.lists` — the only lists a task may be created in.

**Some files are not the project's.** Quarterdeck ships `<docs_dir>/workflow.md`,
`<docs_dir>/task-template.md`, the `refine`, `implement` and `retro` skills, `guard-main.py`, the
checks in `tools/quarterdeck/` and `.github/workflows/quarterdeck.yml`. `doctor` compares each with
the version installed, and an upgrade overwrites it. The block between `<!-- quarterdeck:begin -->`
and `<!-- quarterdeck:end -->` in the agent instructions is rendered, and a re-render replaces it.
A fix that belongs in any of these is never made in place — it is written up as a change to
Quarterdeck itself (section 5).

## 1. Pick the session

| Argument | Session |
|---|---|
| none | This one |
| a session id, or the start of one | That session |
| `PR <n>` | The session that opened pull request `n`, and the pull request's review |
| anything else | List the recent sessions and ask which |

The transcripts are read through a helper that prints one as a timeline:

```bash
python3 .claude/skills/retro/digest.py --list        # recent sessions: id, start, branch, title
python3 .claude/skills/retro/digest.py               # this session
python3 .claude/skills/retro/digest.py <id>          # a past session
python3 .claude/skills/retro/digest.py --pr <n>      # the session that opened pull request n
```

Run it for this session too: a moment is cited by its time, and only the transcript has the times.
Check the digest's first line — if another session has written since, the newest transcript is
that one's, and this one is picked from `--list`. Everything from the `/retro` turn on is the retro
itself, and is not reviewed. If `--pr` finds nothing, the pull request's branch names the session
in `--list`. If the helper finds no transcripts at all — an agent that keeps them elsewhere —
work from the conversation in context, and cite each moment by quoting it.

Write the digest to a scratch file and read it whole. If it is long, start from the `USER`,
`ERROR` and `BLOCKED` lines and read around them. A line that was cut and matters is read in full
from the `.jsonl`, whose path is the digest's second line.

Then gather what the transcript does not hold:

- **The task.** A `<task_prefix><id>-…` branch or an `/implement` or `/refine` argument names one.
  Read it, comments included, the way `<docs_dir>/board.md` says: a bounce to `refine`, and the
  reason given for it, is a moment in its own right.
- **The review.** The user is the reviewer; what they asked to change is the strongest signal
  there is. On GitHub: `gh pr view <n> --comments`, and the inline comments with
  `gh api repos/{owner}/{repo}/pulls/<n>/comments`. Place each request among the three shapes of
  workflow section 11 — trivially wrong, wrong approach, wrong specification.

## 2. Find the moments

A moment is a place in the session, cited by its time, where the session cost more than it should
have or produced something wrong. Look for:

- **Correction.** The user said no, interrupted, or redid something; a review asked for a change.
- **Refusal.** A `BLOCKED` line — a hook refused a tool call. The rule held; the question is why
  the agent tried.
- **The same failure again.** One error or assertion on repeat — the retry budget's territory,
  whether or not it reached three.
- **Search.** A run of reads, greps and finds before a file or a fact was found. A fact taken from
  a source the sources-of-truth table does not name for that domain, or the code taken as
  authority for intent.
- **A step skipped or out of order** against `/implement` or `/refine`: tests not first, the
  architecture record not checked, a status not moved, a tier-2 choice not logged, a tier-3 choice
  made instead of stopping.
- **A wrong number or word.** A constant or a rule not from the domain document; a term its
  lexicon bans.
- **A specification that let it through.** The task was in `todo` and still produced the wrong
  thing — section 11's third shape.
- **Expensive for little.** A call whose result came minutes later, or a result thousands of
  characters long, that the work did not need.
- **Blind.** The agent needed something it could not see: a log, a service, a device, a screen.

A smooth session has none. Say so and stop. A list padded to look useful is worse than no list.

## 3. Trace each moment to the environment

Do not fix the moment. Ask what let it happen, and what is the cheapest change that would have
prevented it. Take the first row that can carry the fix:

| What happened | Where the fix lives |
|---|---|
| A mistake a command could have caught | A check in the chain `commands.check` runs: a lint rule, the dead-code tool's configuration, a test that reads the source the way a boundary lint does, a CI step. Wire an existing tool before writing a new one |
| An action that must never happen was attempted | A hook of the project's own in `.claude/hooks/`, wired in `.claude/settings.json`, on the pattern of `guard-main.py` |
| A specification was approved and still wrong | One line in `<docs_dir>/agent-notes.md` (workflow section 11) — and, when the template or the refine checklist would have stopped it, that change written up for Quarterdeck |
| A step of `/implement` or `/refine` was missed or misordered | Written up for Quarterdeck: the skills are shipped |
| A slow search for a file or a fact | A pointer from where the agent already was: the agent instructions outside the Quarterdeck block, a document it had open, a skill of the project's own |
| Missing information | Wider access: a script, output written to a file, a connector |
| An expensive call | A cheaper one: a narrower command, a script, a smaller scope |
| A judgement rule every session needs, that no check can carry and no skill is loaded for | One line in the agent instructions, outside the Quarterdeck block |
| A line of the agent instructions or of a project skill misled, or the session shows it is carried elsewhere | Its deletion, or its move to the skill that runs at that moment |
| A gap in the domain document or an ADR, or two sources that disagree | Not this skill's. A task in one of `board.lists` on the user's word, or `/refine` |
| None of the above: a model error no environment change would prevent | Nothing. Name it and move on |

The agent instructions load into every session, a skill only when it runs, a document only when it
is read. A line belongs in the latest of these that is still early enough; a line added to the
instructions is paid for by every session after it. Where the instructions repeat a rule a hook
enforces, they do so on purpose — a rule you can read is easier to obey than a refusal you have to
discover — and the repetition is not a candidate for deletion.

## 4. Propose, ranked

Most severe first: wrong work that reached a pull request or the main branch; then a rule broken
and caught late, by the user or by CI; then a rule broken and caught by a check or a hook; then
time and context lost.

```markdown
### 1. <the fix, in one line>
**Moment.** [hh:mm:ss] <what happened — quoted, or one sentence>
**Why it could happen.** <what in the repository allowed it>
**Change.** <the file, and what is added, changed or deleted — or "for Quarterdeck">
**Cost.** <lines added to what every session loads; seconds added to the check chain>
**Proof.** <for a check or a hook: the case it must fail on, and one it must still let through>
```

After the candidates, one line for each moment that gets no proposal, and why.

**Every candidate cites a moment.** One without is generic advice, and is dropped — the citation
rule of workflow section 4, turned on the retro. Beware the session's subject: a retro of a session
about a dead-code tool is about the environment the agent worked in, not about the tool.

Ask which to apply, by number. Wait.

## 5. Apply what was picked

- **A gate is validated against a case with a known answer before it is believed** (workflow
  section 9): plant the case a new check exists to catch and watch it fail; take the plant out and
  watch `commands.check` pass. Show both runs. A check that cannot be made to fail is not finished.
- **A hook is run against the command from the moment, and against commands that must stay
  allowed** — the way `doctor` fires `guard-main.py`. A guard that breaks the session teaches
  people to remove it.
- **A new check joins the chain through the project's own script**, so `commands.check` keeps its
  value. If the command itself must change, that is a manifest edit and a re-rendered block: say
  so, and leave it to the setup skill.
- **A line of `agent-notes.md` is appended, not read** — the file is a log for a person and no skill
  loads it. Its format: `YYYY-MM-DD · <task-id> · what the rules failed to say`.
- **A change for Quarterdeck** — to a shipped skill, the doctrine, the template, the hook or a
  check — is written up as the file and the exact text, for the user to take upstream. The
  project's copy is left untouched: `doctor` would report the edit, and the next upgrade would
  drop it.
- **A fix too large to make now** — a new tool, a CI job — is written up in the shape of the task
  template for the user to put on the board. A defect in a check, hook or skill of the project's
  own may be filed in one of `board.lists`, on the user's word.

Leave every change in the working tree. Nothing is committed outside a task branch, and a retro
has no task. If the current branch is a task branch whose pull request is still open, say so
before the first edit: anything written now would ride in its next commit.

Finish with the files changed and, for each, the candidate it answers — then the write-ups for
Quarterdeck, if any.

## Never

- Never change the product: nothing in the source, the domain document, an ADR, or the ADR digest
  under the Quarterdeck block. A finding there is a task, not a retro edit.
- Never edit a file Quarterdeck ships, or the text inside the Quarterdeck block.
- Never weaken a check to quiet it. Never widen or narrow the mutation scope, and never lower its
  threshold.
- Never write before the user picks, and never commit.
- Never create a task on your own judgement, and never outside `board.lists`.
- Never read `<docs_dir>/agent-notes.md`.
