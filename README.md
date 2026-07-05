# Living Workspace — template

Five empty folders, two documents, and an agent. Copy this repo, open Claude Code inside it,
and describe what you're working on. The application emerges from there.

```
OVERVIEW.md   what this system is — filled in first, by interview
CLAUDE.md     the operating manual the agent follows
data/         your persistent objects
schemas/      their structure and validity
tools/        deterministic operations on them
skills/       the rules and know-how for using the tools
views/        ways of seeing the data
```

The first thing that happens is not code: the agent interviews you and writes the answers
into `OVERVIEW.md`. Everything else traces back to it.
