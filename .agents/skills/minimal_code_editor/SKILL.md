---
trigger: always_on
---

# Skill: minimal_code_editor

## Objective
Modify Python projects with direct, minimal, and review-friendly changes.  
Return only what is necessary for quick manual review.

---

## Response Rules

- Always respond with:
  - a `unified diff`, OR
  - the full file (only if small)
- Do not explain changes
- Do not justify decisions
- No unnecessary text
- At most: one optional line of context

---

## Code Standards (Python)

Strictly follow:

- PEP 8
- Compatible with Flake8:
  - `max-line-length = 88`
  - Proper import ordering
  - No unused variables or imports
  - No trailing whitespace
  - Ensure newline at end of file
- Use type hints where applicable (`typing`)
- Keep functions small and focused

---

## Editing Rules

- Preserve existing structure
- Do not rename symbols unless required
- Do not refactor beyond the requested scope
- Apply minimal and surgical changes
- Avoid adding new dependencies

---

## Output Formats

- Return only changed hunks (no full file unless necessary)
- Do not repeat unchanged context
- Do not restate filenames outside diff headers
- No headers, titles, or markdown outside code blocks
- No IDs in code blocks
- Documentation should be in reStructuredText format or numpy style (docstrings)

## Forbidden

- Long explanations
- Unnecessary code comments
- Debug logs or prints (unless requested)
- Out-of-context example code

## Behavior

- Assume the user will manually review all changes
- Prioritize visual clarity in diffs
- Avoid implicit or hidden modifications
- Prefer consistency over cleverness
- Do not introduce breaking changes unless explicitly required

## Validation Expectations

Before responding, ensure:

- Code passes Flake8 checks
- No syntax errors
- Imports are valid and used
- Changes are minimal and scoped
- Output is clean and copy-paste ready

## User Profile

- User is an experienced developer
- Be concise and technical
- No hand-holding
- No explanations unless explicitly requested