---
name: milestone-code-review
description: Review a whole repository, as it is on its main branch, for junk no tool can decide - an export nothing reaches that the dead-code tool cannot see, a parameter always passed one value, a field nothing reads, a rule worked out in a second place, a stale comment, a test that proves nothing, a word the project bans, an asset nothing uses. Junk, not bugs; the whole tree, not a diff. Proposes findings and files only what the user picks. Run by the owner at a milestone boundary.
disable-model-invocation: true
---

# Milestone code review

A human-present skill, run when a milestone ends. Linters, type checkers and dead-code tools answer
*is this reached*; this review asks *is this needed*. It reads the whole tree, because a change
orphans code in files it never touched, and an author does not grade its own change.

It looks for junk, not bugs, and it does not review a diff. It proposes; the user picks; only what
was picked is filed, as a task on the project's board. It changes no code.

## Before anything: the project's facts

This skill carries no project's paths, names or rules. It reads them.

If `.quarterdeck.json` is in the repository root, read it once:

- `main_branch` — the branch under review.
- `docs_dir` — `<docs_dir>/board.md` is how to read the board and create a task on it;
  `<docs_dir>/workflow.md` lists the rules already enforced, and by what.
- `domain_doc`, `adr_dir` — the product's rules and vocabulary, and its architecture.
- `board.lists` — the lists a finding may be filed in.
- `test_globs` — what is a test.
- `commands.check` — the checks already run; nothing they catch is proposed.

Without it, find the same facts, and note where each came from:

| Fact | Where to look |
|---|---|
| Main branch | `git symbolic-ref --short refs/remotes/origin/HEAD`; else whichever of `main` and `master` exists |
| Source | `git ls-files`, less documentation, generated and vendored files, lockfiles and binary assets. The build, test and lint configuration name the roots |
| Tests | The test runner's configuration — `include`, `testMatch`, `testpaths`, `*_test.go`, `spec/` |
| The rules | The agent instructions (`CLAUDE.md`, `AGENTS.md`) and what they point to: the architecture decision records, the design or domain document, its glossary |
| What is already checked | The check script or CI workflow, and the configuration of every tool it runs — linter, type checker, dead-code tool |
| The board | The tracker connector in this session, and the rule that says where an agent may file what it finds |

Ask the user for anything the repository does not answer. Never guess where a finding is filed.

Search with `git grep`: it reads only tracked files, and works the same in every shell.

## 1. Read the tree as it is on the main branch

```bash
git fetch origin
git diff --quiet origin/<main> -- <source roots>                       # exits 0
git status --porcelain --untracked-files=all -- <source roots>          # prints nothing
git rev-parse --short origin/<main>                                    # the SHA every finding names
```

If either check fails, stop and name the files that differ: the review is of what is merged, and a
finding must point at a line that exists on the main branch. Documentation is never reviewed. The
design document and the open tasks are read only to clear a candidate of check b, and for the
rules of checks c and f.

## 2. Read what is already filed

Read the open tasks of the list findings are filed in — every status short of done and closed. A
done or closed task is not read. A finding an open task already describes — by its
`**Review key:**` line, or as the same junk in the same place — is left out of the proposal.

## 3. The checks

The commands find candidates; judgement decides each one. A candidate the check's own exceptions
clear is dropped without a word, and so is anything an existing check already reports.

**a · An export nothing reaches, where the tooling cannot see.** A dead-code tool counts a module
taken whole as using every export it has. Find where the project takes modules whole, and check
each of their exports by hand:

- namespace and wildcard imports — `import * as m`, `from m import *`, `use m::*`;
- dynamic loading — `import()`, `require` of a computed path, reflection, string-keyed registries,
  dependency-injection containers;
- a module the tool's configuration marks as an entry, or whose exports it marks as used.

```bash
git grep -nE 'import (type )?\* as|from [A-Za-z_.]+ import \*|use [A-Za-z_:]+::\*'
```

An export is reached when a non-test file imports it by name or reads it through the whole module
(`m.name`). A module used whole on purpose — spread, iterated, serialised — has every export used.
A property or a local of the same name is not a use. Where a module re-exports another wholesale,
the wildcard is one export, reached while anything reads through it; its names are not weighed one
by one. The junk is the export, not what it exports, which its own module may well call.

**b · Something no one varies, sets or reads.** A parameter every caller passes the same value. An
option, a field of a data record, a configuration key or a feature flag that nothing sets or reads.
An abstraction with one implementation: an interface, a type parameter, a function taken as an
argument and always given the same one. Find the callers and readers with `git grep -nw`. Each is
junk **only when neither the design document nor an open task names its second use or its
consumer**: search both for the thing it stands for.

**c · A rule worked out in a second place.** The project's architecture gives some numbers and
rules one owner — a layer that computes them, a function every reader goes through, one source for
a constant. Read those rules where the project keeps them, then look for a second place doing the
owner's work: a view recomputing what the model reports, a formula written out again, a constant
repeated as a literal. Without such a rule, a formula written twice is still proposed when its two
copies could drift apart.

**d · A stale comment.** A task marker — `TODO`, `FIXME`, `XXX`, `HACK` — left behind. A task named
in a comment as still to come, when the board has it done or closed. Code commented out. A comment
that describes what the code beside it no longer does; these are met while reading for the other
checks.

```bash
git grep -nE '\b(TODO|FIXME|XXX|HACK)\b'
git grep -ohE '<the shape of a task id on this board>' | sort -u
```

The shape of a task id is read off the board's own tasks — `PROJ-123`, `#123`, `S2-07`. Look each
id up on its own: a board's search is fuzzy, so read the name it returns. A comment that names a
finished task as history is not stale, and nor is one whose task the board no longer has.

**e · A test that proves nothing.** A test that asserts a constant or a data table at a copy of
itself, through no code of the project. A test with no assertion, or one that asserts what its own
mock returns. Mutation testing, where the project runs it, sees some of these — only inside its
scope.

**f · A word the project bans.** If the glossary or the agent instructions name words not to use,
find them in identifiers, strings and comments. A word with an everyday meaning is read in context:
only the banned sense is a finding. A comment that echoes the design document's own prose is still
proposed, and says so: a fix in the code alone leaves the document as the one place the word
stands.

**g · An asset nothing uses.** What the dead-code tool does not read: stylesheet selectors,
templates, images, translation keys, configuration entries, scripts in the package manifest,
environment variables. For a stylesheet, read selectors with comments stripped — a comment often
cites a mockup's class name — and look each name up in the non-test source and the HTML; a name
built from parts is looked for by its stem.

```bash
git ls-files '*.css' '*.scss' '*.less' | xargs python3 -c 'import re, sys
for f in sys.argv[1:]:
    text = re.sub(r"/\*.*?\*/", "", open(f).read(), flags=re.S)
    for prelude in re.findall(r"([^{}]+)\{", text):
        for name in re.findall(r"[.#]([A-Za-z][\w-]*)", prelude):
            print(name)' | sort -u
```

## 4. Propose

One numbered list in the chat, in the order of the checks. Findings one fix removes are one item.

```markdown
### 1. <the junk, in one line>
**Key.** <check> · <file> · <symbol>
**Where.** `<file>:<line>` at `<sha>`
**Check.** <its letter, and the rule or document it rests on>
**Likely fix.** <one line>
```

After the list, one line for each finding left out because an open task describes it, with that
task's link. If nothing was found, say so and stop — a list padded to look useful is worse than no
list.

Ask which to file, by number. Wait. What is not picked is not recorded anywhere, and is proposed
again at the next review.

## 5. File what was picked

One task per picked number, in the list findings are filed in, at the board's first status:

- **Name** in the shape the list's own tasks have. If they are numbered, the number is one past
  the highest — done and closed tasks included; only their names are read.
- **Labels** the ones the board uses for the parts of the code the finding touches, if it has any.
- **Body:**

```markdown
**Where:** <the part of the code> · <the rule or document the check rests on>

<What it is and where: `file:line` at `<sha>`, the line quoted where it says it best.>

<Why it is junk: the check, in a sentence or two.>

**Likely fix.** <…>

**Review key:** <check> · <file> · <symbol>

**Related:** <task links, or none>
```

Finish with the links of the tasks filed.

## Never

- Never edit a file, and never commit. A finding is a task, not an edit.
- Never file without the user's pick, and never in a list an agent may not file in.
- Never close a task or mark one done, and never read a done or closed one beyond its name.
- Never review documentation.
