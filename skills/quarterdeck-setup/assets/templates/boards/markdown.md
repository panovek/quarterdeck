## The board: Markdown files

One file per task in `{{docs_dir}}/board/<id>.md`, where `<id>` is a short slug. Front matter
carries the state; the body carries the specification; a `## Log` section at the end carries
comments, newest last, each line dated. Status names:

{{status_map}}

```markdown
---
status: open
list: <milestone or list name>
waiting_on: [<id>, <id>]
---
<task name as a heading, then the filled template>

## Log
- YYYY-MM-DD · <who> · <what was said>
```

- **Read a task:** read the file, and the files of every id in `waiting_on`.
- **Move a task:** change `status:` in the front matter. Nothing else in the file changes.
- **Write the specification:** replace the body between the front matter and `## Log`.
- **Comment:** append one line to `## Log`.
- **Create a task** (only in {{lists}}): a new file with `list:` set to that name and
  `status: open`. Never with any other `list:` value.
- **Dependencies:** a task is blocked while any id in `waiting_on` has a status other than `done`.
- **The plan:** `list:` in the front matter is the task's milestone; the other files in
  `{{docs_dir}}/board/` with the same `list:` are its siblings; `waiting_on` is the ordering. There
  is no plan file — the board is the plan.
