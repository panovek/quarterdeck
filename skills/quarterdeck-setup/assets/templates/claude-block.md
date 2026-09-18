## How work is done

The full procedure is [{{workflow_path}}]({{workflow_path}}). The rules below are repeated here
because no tool can enforce them — they hold only if they are read.

- **`{{main_branch}}` is the owner's.** Agents commit and push only to their own `{{task_prefix}}*`
  branch. Never `git merge`, `git rebase`, `git push --force`, `git reset --hard` on
  `{{main_branch}}`, and never merge a pull request. A hook enforces this; the rule is here because
  a rule you can read is easier to obey than a refusal you have to discover.
- **Nothing is committed outside a task branch.** Work that has no task is left in the working
  tree for the owner.
- **Sources of truth are per domain.** Code is evidence of what *is*, never authority for what
  *should be*. Code that contradicts the domain document is a bug report, not a source conflict.

{{sources_table}}

- **On contradiction, stop.** Two sources disagreeing is a thing to report, naming both sides.
  Never resolve it by choosing.
- **Three tiers of decision.** Tier 1 — naming, file layout, private helpers, test arrangement:
  decide silently. Tier 2 — a real choice that changes neither architecture nor a product rule: decide,
  and record the choice *and the rejected alternative* in the pull request. Tier 3 — a rule or
  number in the domain document, a new dependency, a layer boundary, a public type other layers
  use, or a contradiction: **stop**, comment on the task, move it to `refine`. No pull request.
- **Three strikes on the same failure and stop.** Different errors in sequence are progress; the
  same assertion three times is being stuck. Comment on the task, move it to `refine`, open
  nothing.
- **Never weaken, skip or delete a test to make a suite pass.** Stop instead.
- **Coverage is never a reason to create a consumer.** If the only caller of a thing is its own
  test, the thing is deleted, not tested.
- **An agent never marks a task done and never closes one.** Those are the owner's.
- **An agent creates tasks only in {{lists}}.** Nowhere else.

The check chain is `{{check}}`{{#mutation}}; mutation testing is `{{mutation}}`{{/mutation}}.
The board is {{board_name}}; how to read, move and create tasks on it is
[{{docs_dir}}/board.md]({{docs_dir}}/board.md). **The board is also the plan** — milestones,
ordering, dependencies and what is next live there, and there is no plan file. The task template is
[{{template_path}}]({{template_path}}). Everything project-specific — branches, commands, test
globs, lists — is bound in `.quarterdeck.json`. Decisions are recorded in `{{adr_dir}}/`; their
one-line digest belongs directly below this block.
