# UniNews

UniNews es una plataforma local para recopilar, revisar y publicar noticias universitarias con trazabilidad. El recolector está implementado en Python y usa `minimax/minimax-m3:free` mediante OpenRouter cuando se ejecuta con credenciales configuradas. La aplicación web está construida con Astro y React; la API usa FastAPI y SQLite para desarrollo local.

## Estado

La implementación principal está avanzada y las pruebas actuales pasan, pero la aceptación final sigue pendiente de cerrar los entregables locales de retry/backup, evaluación AC10 y verificación de Scheduled Task en Windows. Consulta [docs/PROJECT_STATUS_2026-09-07.md](docs/PROJECT_STATUS_2026-09-07.md) para continuar el trabajo.

## Estructura

- `backend/`: API FastAPI, persistencia SQLite, autenticación, migraciones Alembic, media y outbox analítica.
- `collector/`: captura HTTP/Playwright restringida por configuración, robots, deduplicación, extracción y sincronización.
- `shared/`: contratos, validación, URLs y utilidades comunes.
- `analytics/`: preparación local de lotes NDJSON y manifiestos para BigQuery; no sube datos.
- `src/`: frontend Astro/React, portal público y panel administrativo.
- `scripts/windows/`: instalación y registro del recolector como tarea programada.
- `tests/`: pruebas unitarias e integración con fixtures y mocks.
- `evaluation/`: corpus y evaluación local.

## Requisitos locales

- Windows PowerShell.
- Python 3.14.7 x64 verificado en esta ejecución (el plan original pedía Python 3.12).
- Node.js/npm.
- OpenRouter solo para ejecuciones reales del recolector; las pruebas no consumen esa cuota.

Crear o reutilizar el entorno Python:

```powershell
& 'C:\Users\radst\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Instalar dependencias frontend:

```powershell
npm install
```

## Validación local

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit tests/integration -q
npm run typecheck
npm run lint
npm run build
```

Migraciones sobre una base SQLite temporal:

```powershell
$env:DATABASE_URL = 'sqlite:///./uninews-local.db'
.\.venv\Scripts\alembic.exe -c backend/alembic.ini upgrade head
.\.venv\Scripts\alembic.exe -c backend/alembic.ini downgrade base
```

## Ejecución

API:

```powershell
.\.venv\Scripts\uvicorn.exe backend.main:app --reload
```

Frontend:

```powershell
npm run dev
```

Recolector en modo local:

```powershell
.\.venv\Scripts\python.exe -m collector --help
```

Configura secretos fuera del repositorio. No ejecutes el recolector real sin revisar las universidades, hosts y enlaces permitidos.

## Reglas de seguridad y alcance

- No se usa ScrapeGraphAI.
- No se publican noticias ficticias cuando falla una fuente o el LLM.
- Las pruebas usan fixtures y mocks, sin universidades, OpenRouter ni Google Cloud productivos.
- BigQuery, despliegue cloud y push quedan fuera de esta fase.
