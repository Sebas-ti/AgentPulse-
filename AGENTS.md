# AgentPulse — instrucciones para agentes de código

Este archivo es la fuente única de reglas del repo. Antigravity lo lee directamente;
Claude Code lo recibe a través de `CLAUDE.md`. Mantenlo corto: si una regla solo aplica
a una carpeta, va en `.agents/rules/` y `.claude/rules/`, no aquí.

## Qué es el proyecto

AgentPulse es una plataforma web que evalúa, monitorea y audita agentes conversacionales
y flujos RAG en QA y Producción. Mide latencia, costo por token, alucinaciones y
cumplimiento de guardrails. El diseño completo está en `ARCHITECTURE.md`.

## Antes de escribir código

1. Lee `ARCHITECTURE.md`, al menos las secciones que toca tu tarea.
2. Identifica a qué fase pertenece la tarea (sección "Plan por fases") y su criterio "Hecho cuando".
3. Propón un plan corto y espera aprobación si la tarea crea un módulo, una tabla o una dependencia.
4. Si lo pedido contradice `ARCHITECTURE.md`, detente y dilo. No lo resuelvas por tu cuenta.

## Comandos

La fase 0 crea estos comandos en el `Makefile`. Si aún no existen, créalos con estos nombres.

| Comando | Qué hace |
| --- | --- |
| `make dev` | Levanta postgres, redis, api, worker y web con Docker Compose |
| `make check` | Formato, lint, tipos y pruebas de todo el repo. Debe pasar antes de terminar |
| `make test` | Solo pruebas |
| `make migrate` | Aplica migraciones de Alembic |
| `make migration name=<slug>` | Genera una migración nueva |
| `make seed` | Carga un proyecto de ejemplo y ejecuta `examples/rag-agent` |

## Stack (fijo)

- Backend: Python 3.12 o superior, FastAPI, Pydantic v2, SQLAlchemy 2 asíncrono, asyncpg, Alembic, Taskiq sobre Redis Streams.
- Frontend: React, Vite, TypeScript estricto, TanStack Query, Tailwind, Recharts.
- SDK y CLI: OpenTelemetry SDK con exportador OTLP/HTTP, Typer.
- Datos: PostgreSQL y Redis. No hay otro almacén.
- Herramientas: `uv`, Ruff, Pyright, pytest; pnpm, ESLint, Vitest.
- Nube: Azure (Container Apps, PostgreSQL Flexible Server, Azure Managed Redis, Key Vault, Entra ID). IaC en Bicep.

No añadas dependencias, servicios ni frameworks sin pedirlo. Si crees que hace falta uno, explica por qué y espera respuesta.

## Estructura

```text
apps/api/src/agentpulse/   backend: core, auth, db, ingest, query, evals, alerts, realtime
apps/api/migrations/       Alembic
apps/api/tests/            pruebas del backend
apps/web/                  panel React
packages/sdk-python/       agentpulse-sdk y CLI
examples/rag-agent/        agente de ejemplo que emite trazas
infra/                     Bicep
docs/adr/                  decisiones de arquitectura
```

## Reglas de arquitectura

Son invariantes. Romper una requiere un ADR aprobado.

- **Monolito modular.** `api` y `worker` salen de la misma imagen. No crees servicios nuevos.
- **Fronteras de módulo.** `ingest`, `query`, `evals`, `alerts` y `realtime` no se importan entre sí. Solo pueden importar de `core`, `auth` y `db`.
- **Guardar antes de evaluar.** La ingesta persiste la traza y responde `202`. Ninguna evaluación corre dentro de una petición HTTP.
- **Aislamiento por proyecto.** Toda consulta filtra por `project_id` dentro de la capa de repositorio (`db/repositories`). Los endpoints nunca escriben SQL ni filtran a mano.
- **Ambiente desde la clave.** El ambiente (`qa` o `prod`) sale de la clave de API, nunca de un atributo que envíe el cliente.
- **Esquema interno propio.** Los atributos `gen_ai.*` de OpenTelemetry se traducen en `ingest/normalize.py`. Ningún otro módulo conoce esos nombres.
- **Evaluadores como plugins.** Todo evaluador implementa la interfaz `Evaluator` de `evals/base.py`. Ragas, DeepEval o Azure AI Content Safety se envuelven detrás de ella; nunca se llaman desde otro lugar.
- **Juez versionado.** Cada resultado guarda `evaluator_version` y `judge_model`. Si cambias un prompt de juez, sube la versión.
- **Texto de trazas = datos.** El contenido de prompts y respuestas evaluadas nunca se interpreta como instrucciones. Los prompts de juez lo delimitan de forma explícita.
- **Auditoría solo de inserción.** Nada actualiza ni borra filas de `audit_log`.

## Convenciones de código

Python:
- Tipos en todas las firmas; Pyright en modo estricto sin `# type: ignore` sin motivo escrito.
- Todo I/O es `async`. Nada de llamadas bloqueantes dentro de handlers o tareas.
- Entradas y salidas de la API son modelos Pydantic; no devuelvas modelos de SQLAlchemy.
- Dinero en `Decimal`, nunca `float`. Tiempos en UTC con zona.
- Configuración solo desde `core/settings.py`; no leas `os.environ` en otros módulos.
- Errores de dominio como excepciones de `core/errors.py`, traducidas a HTTP en un solo lugar.

TypeScript:
- `strict` activado; sin `any`.
- Los tipos de la API se generan desde el OpenAPI del backend (`pnpm gen:api`); no los escribas a mano.
- Datos remotos siempre con TanStack Query; sin `fetch` suelto en componentes.

General:
- Código, identificadores, commits y nombres de ramas en inglés. Documentación del repo en español.
- Sin comentarios que repitan el código. Comenta el porqué cuando no sea obvio.

## Base de datos

- Todo cambio de esquema es una migración de Alembic generada con `make migration`. Nunca edites una migración ya fusionada.
- Toda tabla de negocio lleva `project_id`, `created_at` y clave primaria UUID generada en la aplicación.
- `spans` está particionada por mes sobre `started_at`. No añadas índices globales sin medir.
- Migraciones compatibles hacia atrás: primero expandir, después contraer, en despliegues separados.

## Pruebas

- Cada endpoint nuevo trae prueba de camino feliz, de validación y de autorización.
- Las pruebas de repositorio corren contra PostgreSQL real (contenedor), no contra SQLite ni mocks.
- Los evaluadores con LLM se prueban con un juez falso determinista. Las llamadas reales al modelo solo corren en la suite marcada `@pytest.mark.live`, fuera del CI.
- `tests/test_isolation.py` verifica que un proyecto no puede leer datos de otro. No la desactives.
- Corre `make check` antes de dar una tarea por terminada y pega el resultado en tu resumen.

## Seguridad

- Nunca escribas secretos, claves ni cadenas de conexión reales en el repo, en pruebas ni en logs.
- De las claves de API solo se guarda el hash; la clave completa se muestra una vez al crearla.
- No registres en logs el contenido de prompts ni de respuestas. Registra identificadores.
- La redacción de datos personales corre en la ingesta, antes de guardar. No la muevas después.

## Flujo de trabajo

- Una tarea, una rama: `phase-<n>/<slug>`. No trabajes sobre archivos que otra rama activa esté cambiando.
- Commits pequeños con Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`).
- Si una decisión cambia el diseño, añade `docs/adr/NNNN-<slug>.md` y actualiza `ARCHITECTURE.md` en el mismo commit.
- Al terminar, resume: qué cambió, cómo se verificó, qué quedó pendiente.

## No hacer

- No implementes trabajo de fases posteriores "de paso".
- No cambies el contrato de ingesta (`/v1/otlp/v1/traces`, `/v1/traces`) sin un ADR.
- No añadas un segundo almacén (ClickHouse, Cosmos DB, Blob) en el MVP.
- No desactives pruebas ni reglas de lint para que pase `make check`.
- No hagas `git push --force` ni reescribas historia en `main`.
