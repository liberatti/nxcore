---
trigger: always_on
---

## Context Control

- Ignore unrelated code
- Do not re-read entire file if diff is clear
- Focus only on modified lines

---

## Diff Minimization

- Use shortest valid diff
- Avoid context lines when possible
- Prefer single-hunk edits

---

## Determinism

- Do not provide alternatives
- Do not suggest improvements
- Do exactly what was requested