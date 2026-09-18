## The board

Through the tracker connector available in this session. Status names on the board:

{{status_map}}

- **Read a task:** fetch it by id, including its comments, subtasks and dependency links.
- **Move a task:** set its status to the board's name from the table above.
- **Write the specification:** the filled template becomes the task description.
- **Comment:** add a comment to the task.
- **Create a task** (only in {{lists}}): create it in that list. Never in any other list.
- **Dependencies:** a task is blocked while any task it waits on is not `done`.
- **The plan:** the list, milestone or label a task sits in is its milestone; the other tasks in
  it are its siblings; its dependency links are the ordering. There is no plan file — the board is
  the plan.
