## The board: GitHub Issues

Through the `gh` CLI. Statuses are labels named `status:<name>`, one per issue; lists are labels
named `list:<name>`. Status names:

{{status_map}}

- **Read a task:** `gh issue view <n> --json title,body,labels,comments`. The task id is the issue
  number, written `#<n>`.
- **Move a task:** `gh issue edit <n> --remove-label status:<old> --add-label status:<new>`.
- **Write the specification:** `gh issue edit <n> --body-file <file>` — the filled template
  becomes the issue body.
- **Comment:** `gh issue comment <n> --body <text>`.
- **Create a task** (only in {{lists}}): `gh issue create --label list:<name> --label status:open
  --title <t> --body-file <file>`. Never with any other `list:` label.
- **Dependencies:** lines of the form `waiting_on: #<n>` in the issue body. A task is blocked while
  any of those issues is not labelled `status:done`.
- **The plan:** the `list:<name>` label (or the GitHub milestone, where the project uses them) is
  the task's milestone; `gh issue list --label list:<name>` shows its siblings; the `waiting_on:`
  lines are the ordering. There is no plan file — the board is the plan.
