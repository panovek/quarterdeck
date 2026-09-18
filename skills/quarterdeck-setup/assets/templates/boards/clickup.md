## The board: ClickUp

Through the ClickUp connector in this session. Status names on the board:

{{status_map}}

- **Read a task:** `mcp__clickup__getTaskById` — include subtasks, comments, and the `waiting_on`
  / `blocking` links. Subtasks and linked tasks are read the same way.
- **Move a task:** `mcp__clickup__updateTask` with the board's status name from the table above.
- **Write the specification:** `mcp__clickup__updateTask` — the filled template becomes the task
  description.
- **Comment:** `mcp__clickup__addComment`.
- **Create a task** (only in {{lists}}): `mcp__clickup__createTask` in that list. Never in any
  other list.
- **Dependencies:** a task is blocked while any task in its `waiting_on` links is not `done`.
- **The plan:** the list a task sits in is its milestone; the other tasks in that list
  (`mcp__clickup__searchTasks` filtered by list) are its siblings; its `waiting_on` / `blocking`
  links are the ordering. There is no plan file — the board is the plan.
