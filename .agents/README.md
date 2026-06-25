# Agent Configurations

This directory contains localized rules and skills for agentic AI workflows in this repository.

## Structure

- **[/rules](rules/)**: Rules injected into the agent's context.
  - [context-control.md](rules/context-control.md): Context minimization and diff minimization rules.
  - [ui-ux.md](rules/ui-ux.md): Angular Material UI/UX rules, updated for the modern, light, and minimalist style.
- **[/skills](skills/)**: Custom skills.
  - [minimal_code_editor](skills/minimal_code_editor/SKILL.md): Directives for direct, surgical code editing with Flake8 compatibility.
