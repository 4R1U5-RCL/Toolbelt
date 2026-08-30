# Skills

Reusable **skills** — each a self-contained working-method package with a README (working-method
guide + Known Issues), optional `templates/`, and a committed `tests/verify.sh`.

Two kinds live here, deliberately side by side:

| Kind | What it is | In this folder |
|------|------------|----------------|
| **Command** | An executable `/slash-command` — a procedure the assistant runs. | **Handoff** (`/handoff`) |
| **Discipline** | A cognitive practice — a format + habit the assistant follows; **not** a command. | **Memory**, **Scratch**, **Errors** |

A skill can be executable *or* cognitive; both are "skills" because both package a reusable method the
team adopts. Each folder says which it is up top. Verify any skill from its own directory:
`bash tests/verify.sh`.
