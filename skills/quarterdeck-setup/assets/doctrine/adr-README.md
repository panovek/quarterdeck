# Architecture decision records

One file per decision, numbered, never deleted. A decision is amended by a new record that
supersedes it; the old record's status changes and nothing else in it does.

The one-line digest of every accepted record lives in the agent instructions (`CLAUDE.md` /
`AGENTS.md`), which is what an agent has in context at start. A full record is read only when a
task touches its area — never all of them, never at start. Keep the first line of each record
the rule itself, so the digest can be built from titles.

Start from [adr-template.md](adr-template.md).
