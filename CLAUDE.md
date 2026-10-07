@AGENTS.md

## Claude Code

- Al empezar una fase o una tarea que cree módulos o tablas, usa el modo plan y contrasta el plan con `ARCHITECTURE.md` antes de editar.
- `ARCHITECTURE.md` no se importa aquí a propósito, para no gastar contexto en cada sesión. Léelo con la herramienta de lectura cuando la tarea toque diseño.
- Las reglas por área viven en `.claude/rules/` con `paths` en el frontmatter. Reglas previstas:
  - `backend.md` → `apps/api/**/*.py`
  - `migrations.md` → `apps/api/migrations/**`
  - `web.md` → `apps/web/**/*.{ts,tsx}`
  - `infra.md` → `infra/**`
- Los procedimientos de varios pasos van como skills en `.claude/skills/`, no en este archivo. Skills previstas: `new-migration`, `new-evaluator`, `new-endpoint`.
- Si una regla de `.claude/rules/` o una skill tiene equivalente en `.agents/`, cambia las dos en el mismo commit para que Antigravity y Claude Code no diverjan.
- Para búsquedas amplias en el repo, delega en un subagente de exploración y trabaja con su resumen.
- Antes de cerrar una tarea, ejecuta `make check` y pega la salida relevante.
