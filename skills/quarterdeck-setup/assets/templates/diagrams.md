# Diagrams

The list of diagrams, one record each: the file, and two or three plain sentences saying what the
owner wants to see on it. A record is the prompt — an agent hands its text to the project's diagram
tool and authors the file under the contract in [README.md](README.md), which holds every fixed
rule (evidence first, one question per diagram, semantic labels, stable ids kept on refresh, the
lexicon, no subtitle, the node ceiling) so that no record has to repeat one.

**To add a diagram**, add a record and author it. **To remove one**, delete the record, its source
file and its image. **To change one**, edit its sentences. Nothing else knows this list: the render
command draws whatever source files are in the folder, and the workflow names only the
architecture diagram.

---

**`system.architecture.json`** — Architecture diagram of the whole app: every layer, how the
layers communicate, the external dependencies, and the boundaries the lint enforces. Reviewed on
every task in `/implement`.
