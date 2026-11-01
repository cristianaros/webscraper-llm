# UniNews Producción Final — Plan de Implementación Adaptado al Proyecto Actual

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended), superpowers:dispatching-parallel-agents, or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar las brechas técnicas, de seguridad, de datos legados y de integración Git que hoy mantienen el proyecto en `cutover_blocked`, dejando UniNews listo para pasar a producción sobre **Vercel (Astro) + Railway (FastAPI + PostgreSQL) + Windows PC (Recolector automático)** sin reescribir lo que ya existe y pasa pruebas en el repositorio.

**Architecture:** Se parte de la base **ya implementada en el árbol actual** (`83 passed` en `pytest -q`, `eslint` 0, `astro check` 0, `astro build` 0): recolector Python separado en Windows con `nvidia/nemotron-3.5-super-vl:free`, backend FastAPI con migración `0006_db_media_bytes.py`, `ChatGuard`, `NewsAssistant` híbrido de 2 capas y `seed_production_sources.py` en `railway.toml`, y frontend Astro/React con `NewsContextAssistant.tsx` embebido en cada noticia y panel `/admin` autenticado. Sobre esa realidad exacta, subagentes especializados por los roles oficiales del proyecto (`collector`, `backend`, `frontend`, `qa`, `coordinator`) cierran los dos bloqueos de cutover documentados en `docs/acceptance/production.md`, reparan la migración sin pérdida desde `data/backend/university_news.db` (14 noticias y 6 imágenes locales reales), corrigen la IP de cliente tras el proxy de Railway y el marcador `O(1)` de caché del chat, alinean catálogos/imágenes en la UI y consolidan commits limpios por rol listos para `git push`.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic (`0001`–`0006`), PostgreSQL (`psycopg2-binary`) / SQLite, HTTPX 0.28 + HTTPCore 1.0 (`SyncBackend`), BeautifulSoup4, Pillow, OpenRouter (`nvidia/nemotron-3.5-super-vl:free`), Astro 6, React 19, TypeScript 5, Tailwind CSS 4, PowerShell (Task Scheduler), pytest.

**Spec:** [2026-11-01-produccion-uninews-design.md](../specs/2026-11-01-produccion-uninews-design.md).  
**Reglas y roles obligatorios del repositorio:** [AGENTS.md](../../../AGENTS.md) y [2026-09-06-agent-roles.md](../specs/2026-09-06-agent-roles.md).

**Registro de ejecución local (2026-11-01):** las Tasks 1–5 se implementaron y verificaron. Los pasos Git de Task 6 permanecen pendientes porque las instrucciones del usuario prohíben toda operación Git/GitHub; ningún comando Git de este plan está autorizado en esta sesión. La verificación final de código se ejecutó por separado.

---

## Global Constraints

- **C01:** El modelo activo para extracción y para el asistente de noticias es exactamente `nvidia/nemotron-3.5-super-vl:free` vía OpenRouter con `provider.max_price = {"prompt": 0, "completion": 0}`.
- **C02:** El recolector se ejecuta en Windows separado de FastAPI/Vercel y no importa módulos de `backend/` (únicamente `shared/`).
- **C03:** En `APP_ENV=production`, `BackendSettings` rechaza tokens por defecto (`admin-test`, `worker-test`), tokens `< 16` caracteres, tokens idénticos entre sí o `allowed_origins` vacío.
- **C04:** Ningún secreto (`ADMIN_TOKEN`, `COLLECTOR_TOKEN`, `OPENROUTER_API_KEY`, `DATABASE_URL`) entra en Git, logs, capturas ni variables `PUBLIC_*`. Prohibido leer o volcar archivos `.env` reales.
- **C05:** Las migraciones y scripts de datos conservan todas las filas existentes y se ensayan sobre copias verificadas con `shared.backup.backup_sqlite` (nota: `backup_sqlite` exige que el archivo `destination` **no exista previamente**). Prohibido alterar `data/backend/university_news.db` o `data/collector/collector.db` en sitio durante pruebas.
- **C06:** `/api/news`, `/api/media/{sha256}` y `/api/chat` exponen exclusivamente noticias con `publication_status == "published"`.
- **C07:** La suite automatizada (`pytest -q`) no realiza tráfico de red externo real; utiliza fixtures, copias temporales y `httpx.MockTransport`.
- **C08:** Respetar estrictamente el trabajo ya presente en el árbol (`git status --short`): no revertir los 38 archivos ya adelantados ni tocar `skills-lock.json` o `.agents/skills/*`. Nunca ejecutar `git add .`.

---

## Inventario Verificado del Proyecto Actual (Base Obligatoria para los Subagentes)

### 1. Módulos YA construidos en el proyecto (conservar y extender; NO recrear desde cero)

- **Backend operativo y migraciones:** `backend/config.py` (`validate_production_settings`), `backend/database.py` (`normalize_database_url`, pool PostgreSQL), `backend/migrations/env.py` (escape `%%`), `backend/migrations/versions/0006_db_media_bytes.py` y `backend/models.py` (`MediaAsset.content_bytes`), `backend/services/media.py` (`storage_backend="database"`), `backend/routers/media.py` (`ETag`, `304`, `Cache-Control: immutable`), `backend/scripts/datoslab_catalog.py` (`VERIFIED_SLUGS`), `backend/scripts/seed_production_sources.py` y `railway.toml`.
- **Asistente IA multi-noticia:** `backend/rag/news_assistant.py` (`prepare_context` con `[NOTICIA EN FOCO]`, `[ANTECEDENTES RELACIONADOS DEL ARCHIVO]` y `[CATÁLOGO RECIENTE DEL PORTAL]`), `backend/rag/chat_guard.py` (`ChatGuard`), `backend/rag/openrouter.py` y `backend/routers/chat.py`.
- **Recolector Windows:** `collector/images.py` (`is_allowed_image_host`, `data-src` / `data-lazy-src` / `data-original` / `srcset` / `og:image` / `twitter:image`, `original_url` post-redirect) y `collector/pipeline.py` (`CollectorHeartbeat`).
- **Frontend Astro + React:** `src/lib/api.ts` (`resolveMediaUrl`, `resolveExternalUrl`, filtro `university`), `src/lib/admin-api.ts` (7 helpers autenticados), `src/components/NewsContextAssistant.tsx` integrado dentro de `NewsDialog` en `src/components/NewsPage.tsx`, `src/components/ChatInterface.tsx`, `src/components/AdminPanel.tsx`, `src/components/admin/{ReviewPanel,SourcesPanel,RunsPanel}.tsx` y `tsconfig.json`.
- **Datos locales reales en `data/`:** `data/backend/university_news.db` (revisión Alembic `0005`, `14` noticias publicadas, `23` universidades, `23` fuentes, `28` revisiones y `6` imágenes en `media_assets` con `storage_backend='local'` y `storage_key` en `data/backend/media/<xx>/<sha256>.png`) y `data/collector/collector.db` (`439` `work_items`, `46` `local_media`).

### 2. Brechas reales en el repositorio actual que este plan resuelve

| Punto del repositorio actual | Problema verificado en el código actual | Tarea y rol asignado |
| :--- | :--- | :--- |
| `collector/http.py:38,62-72,121`, `collector/browser.py:15-44` | **Bloqueo de cutover #1 (`docs/acceptance/production.md:16`):** `_validate()` resuelve DNS y verifica `is_global`, pero `httpx.Client` vuelve a resolver DNS al abrir el socket TCP (ventana TOCTOU de DNS rebinding). `BrowserFetcher` tampoco verifica la IP remota de la respuesta navegada. | **Task 1** (`collector`) |
| `scripts/windows/run-collector.ps1:4`, `collector/__main__.py:43-45` | `run-collector.ps1` exige `.venv-collector\Scripts\python.exe` sin fallback al `.venv\Scripts\python.exe` presente en el proyecto; `doctor` no valida escritura en `data_dir` ni conectividad opcional `--check-api`. | **Task 1** (`collector`) |
| `backend/scripts/migrate_to_postgres.py:29,47-55` y `data/backend/university_news.db` | **Bloqueo de cutover #2 (`docs/acceptance/production.md:15`):** `migrate_to_postgres.py` no usa `normalize_database_url` (falla con `postgres://`), inserta tablas sin orden topológico FK, no rellena `media_assets.content_bytes` desde los 6 PNG locales de `data/backend/media/` y no resetea secuencias `SERIAL` en PostgreSQL. Falta además el ensayo automatizado `0005`→`0006` + backfill sobre copia de `data/backend/university_news.db`. | **Task 2** (`backend` datos) |
| `src/components/AdminPanel.tsx:36-37`, `src/components/NewsPage.tsx:80,97`, `vercel.json:6-8` | `AdminPanel.tsx` usa categorías fuera de `shared.contracts.Category` y universidades ficticias hardcodeadas en lugar de `listUniversities(token)`; `NewsPage.tsx` usa `visibility="hidden"` en `onError` dejando recuadros vacíos; `vercel.json` tiene un rewrite circular en vez de `cleanUrls: true` y cabeceras de seguridad. | **Task 3** (`frontend`) |
| `backend/routers/chat.py:31`, `backend/rag/chat_guard.py:35-45`, `backend/rag/news_assistant.py:67,82`, `backend/routers/{news,admin}.py` | Tras el proxy de Railway, `request.client.host` agrupa a todos los visitantes en un único bucket `ip_rpm=6`; `ChatGuard.snapshot_marker` lee y hashea en Python el cuerpo completo de todas las noticias en cada request porque `news.py` y `admin.py` no actualizan `News.updated_at` explícitamente; `NewsAssistant` ejecuta `base.all()` sin límite. | **Task 4** (`backend` API/RAG) |
| `docs/acceptance/production.md:3,13-17`, `docs/context-deploy.md:15`, `tests/integration/test_production_readiness.py` | El estado sigue en `cutover_blocked` y la prueba E2E de producción aún no ejercita proxy `X-Forwarded-For`, marcador `O(1)` ni bloqueo de DNS rebinding. | **Task 5** (`qa`) |
| Árbol Git en `backend-webscrapper` (`git status --short`) | 38 archivos de producto/tests modificados o nuevos están sin commit mezclados con `skills-lock.json` y `.agents/skills/*`, impidiendo un despliegue limpio y trazable en Railway y Vercel. | **Task 6** (`coordinator`) |

---

## Review Focus

1. **Preservación de TLS SNI y `MockTransport` al fijar IP en `collector/http.py`:** `PublicOnlyNetworkBackend.connect_tcp` solo debe inyectarse cuando `HttpFetcher` construye su propio `httpx.Client` (no cuando los tests inyectan `httpx.Client(transport=httpx.MockTransport(...))`), y debe pasar la IP global validada a `super().connect_tcp(pinned_ip, port, ...)` para que `httpcore` mantenga intactos `server_hostname` (SNI) y `Host` (Task 1).
   La prueba de conexión fija comprueba la IP entregada al backend TCP; TLS, SNI y certificado de una conexión real quedan como comprobación del cutover.
2. **Orden FK real y secuencias en `migrate_to_postgres.py`:** usar exactamente los nombres reales de tabla de `backend/models.py` (`universities`, `sources`, `source_versions`, `news`, `news_revisions`, `media_assets`, `news_media_history`, `scrape_runs`, `ingest_receipts`, `collector_status`, `analytics_outbox`) y sincronizar secuencias `id` en PostgreSQL para evitar `UniqueViolation` tras migrar (Task 2).
3. **Inmutabilidad de `data/backend/university_news.db` durante pruebas:** todo ensayo de migración `0005`→`0006` y backfill debe hacerse sobre una copia creada con `backup_sqlite` en `tmp_path` (sin pre-crear el archivo destino antes de llamar a `backup_sqlite`) (Task 2 y Task 5).
4. **IP de cliente tras Railway (`extract_client_ip`):** la documentación actual de Railway identifica `X-Real-IP` como la IP del visitante en el edge HTTP público y no garantiza la posición de un valor en `X-Forwarded-For`. En producción se valida y usa `X-Real-IP`; si falta o es inválido, se usa `request.client.host`. El ingreso privado no recibe la misma limpieza de cabeceras y debe controlarse aparte (Task 4).
5. **Higiene Git sobre árbol compartido (`Task 6`):** si los subagentes corren en el mismo checkout compartido (`Workspace="inherit"`), **ningún subagente de las Oleadas 1–3 ejecuta `git commit`** para no provocar bloqueos en `.git/index.lock` ni mezclar archivos; `Task 6` (`coordinator`) realiza los commits atómicos por rol con rutas explícitas dejando intactos `skills-lock.json` y `.agents/skills/*`. (Si el coordinador usa worktrees `codex/*` aislados, cada subagente puede comitear únicamente sus rutas autorizadas en su rama).

---

## Protocolo de Creación y Despacho de Subagentes para el Coordinador

Cualquier modelo coordinador puede ejecutar este plan creando subagentes bajo cualquiera de las 3 modalidades soportadas por el repositorio, respetando siempre el máximo de **3 subagentes simultáneos** ([AGENTS.md](../../../AGENTS.md)):

1. **Despacho paralelo por oleadas (`superpowers:dispatching-parallel-agents` / `invoke_subagent` / `Agent`):**
   - **Oleada 1 (hasta 3 subagentes en paralelo — 0 archivos compartidos):** despachar simultáneamente `Task 1` (`collector`), `Task 2` (`backend` datos) y `Task 3` (`frontend`). Esperar finalización y verificar tests de los tres.
   - **Oleada 2 (1 subagente):** despachar `Task 4` (`backend` API/RAG). Esperar finalización y verificar tests.
   - **Oleada 3 (1 subagente QA independiente):** despachar `Task 5` (`qa`) para validar la integración completa y actualizar `docs/acceptance/production.md`.
   - **Oleada 4 (coordinador):** ejecutar `Task 6` (`coordinator`) para verificar `git status --short`, suite global y crear los commits limpios por rol.
2. **Despacho secuencial con `task-brief` (`superpowers:subagent-driven-development`):**
   - Extraer cada encargo con `bash .agents/skills/subagent-driven-development/scripts/task-brief docs/superpowers/plans/2026-11-01-produccion-uninews.md N` (`N = 1..6`) y ejecutar implementador + revisor por tarea.
3. **Coordinación supervisada en Orca (solo si el usuario la solicita explícitamente, según `AGENTS.md`):**
   - Crear `Run`, registrar `Task 1`–`Task 6` con dependencias `(1, 2, 3) -> 4 -> 5 -> 6`, usar `worker-start` pasando el bloque `Encargo` de cada tarea y cerrar tras `worker_done` + revisión QA.

---

### Task 1: Fijación de IP Anti-DNS-Rebinding en el Recolector y Robustez en Windows

```text
Encargo:
- Tarea/objetivo: Task 1 — Cerrar la ventana TOCTOU de DNS rebinding en el recolector (bloqueo de cutover #1 en docs/acceptance/production.md:16) y asegurar compatibilidad de scripts Windows con .venv / .venv-collector.
- Requisitos: C02, C04, C07, C08; Review Focus #1.
- Rol oficial: collector (docs/superpowers/specs/2026-09-06-agent-roles.md).
- Propiedad exclusiva: collector/http.py, collector/browser.py, collector/__main__.py, collector/pipeline.py (cesión del coordinador durante integración), scripts/windows/run-collector.ps1, tests/unit/test_http_policy.py, tests/integration/test_browser_fetch.py y tests/integration/test_pipeline.py.
- Entradas: collector/images.py (is_allowed_image_host ya implementado), shared/urls.py (normalize_url, validate_destination).
- Salidas: PublicDestinationError y PublicOnlyNetworkBackend(httpcore.SyncBackend) en collector/http.py; verificación de IP remota en BrowserFetcher.fetch; doctor con chequeo de data_dir y --check-api opcional; run-collector.ps1 con fallback a .venv.
- Validación: .\.venv\Scripts\python.exe -m pytest tests/unit/test_http_policy.py tests/unit/test_images.py tests/integration/test_browser_fetch.py tests/integration/test_pipeline.py -v
- Restricciones: No modificar collector/images.py. El coordinador cedió collector/pipeline.py al rol collector al descubrir que `run_once` pasaba un cliente sin pinning al fetcher productivo; el cambio y su prueba de ciclo de vida se verificaron. No ejecutar operaciones Git bajo las instrucciones vigentes del usuario.
```

**Files:**
- Modify: `collector/http.py`
- Modify: `collector/browser.py`
- Modify: `collector/__main__.py`
- Modify: `collector/pipeline.py` (cesión de integración para activar el transporte fijado)
- Modify: `scripts/windows/run-collector.ps1`
- Test: `tests/unit/test_http_policy.py`
- Test: `tests/integration/test_browser_fetch.py`
- Test: `tests/integration/test_pipeline.py`

- [x] **Step 1: Escribir las pruebas que reproducen el DNS rebinding TOCTOU y el doctor del recolector en `tests/unit/test_http_policy.py`**

Añadir al final de `tests/unit/test_http_policy.py`:
```python
def test_public_network_backend_pins_global_ip_and_blocks_dns_rebinding_on_connect(source, monkeypatch):
    from collector.http import PublicOnlyNetworkBackend, PublicDestinationError, HttpFetcher

    # Simulate TOCTOU: first DNS lookup (_validate) returns public IP 93.184.216.34,
    # second DNS lookup (at TCP connect time) rebinds to link-local metadata 169.254.169.254.
    answers = iter([
        [(2, 1, 6, "", ("93.184.216.34", 0))],  # robots _validate
        [(2, 1, 6, "", ("169.254.169.254", 0))],  # robots connect_tcp -> must block!
    ])
    monkeypatch.setattr("collector.http.socket.getaddrinfo", lambda *a, **kw: next(answers))

    opened_targets = []
    monkeypatch.setattr(
        "httpcore.SyncBackend.connect_tcp",
        lambda self, host, port, **kw: opened_targets.append((host, port)) or (_ for _ in ()).throw( AssertionError("socket should not open") ),
    )

    fetcher = HttpFetcher()  # Default real client must install PublicOnlyNetworkBackend
    with pytest.raises(FetchError, match="private_destination"):
        fetcher.fetch("https://uni.example/noticia", source)
    assert opened_targets == []


def test_public_network_backend_connects_using_pinned_ip_without_second_os_resolution(monkeypatch):
    from collector.http import PublicOnlyNetworkBackend

    monkeypatch.setattr("collector.http.socket.getaddrinfo", lambda host, port, **kw: [(2, 1, 6, "", ("93.184.216.34", port))])
    connected = {}

    def fake_super_connect(self, host, port, timeout=None, local_address=None, socket_options=None):
        connected["host"] = host
        connected["port"] = port
        return "sentinel-stream"

    monkeypatch.setattr("httpcore.SyncBackend.connect_tcp", fake_super_connect)
    backend = PublicOnlyNetworkBackend()
    stream = backend.connect_tcp("diario.uach.cl", 443, timeout=10.0)
    assert stream == "sentinel-stream"
    assert connected == {"host": "93.184.216.34", "port": 443}
```

- [x] **Step 2: Ejecutar las pruebas para verificar que fallan antes de implementar**

Run: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_http_policy.py -v`
Expected: FAIL por `ImportError: cannot import name 'PublicOnlyNetworkBackend' from 'collector.http'`.

- [x] **Step 3: Implementar `PublicOnlyNetworkBackend` en `collector/http.py`, verificación IP en `collector/browser.py`, `--check-api` en `collector/__main__.py` y fallback `.venv` en `scripts/windows/run-collector.ps1`**

1. En `collector/http.py`:
   - Importar `ipaddress` y `from httpcore import SyncBackend`.
   - Definir `class PublicDestinationError(RuntimeError): pass`.
   - Definir `class PublicOnlyNetworkBackend(SyncBackend):` con `connect_tcp(self, host: str, port: int, timeout: float | None = None, local_address: str | None = None, socket_options=None)`:
     - Resolver `entries = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)` (capturando `socket.gaierror` → `raise PublicDestinationError("dns_failed")`).
     - Extraer `addresses = [entry[4][0] for entry in entries]` y comprobar `addresses and all(ipaddress.ip_address(addr).is_global for addr in addresses)`; si falla, `raise PublicDestinationError("private_destination")`.
     - Invocar `return super().connect_tcp(addresses[0], port, timeout=timeout, local_address=local_address, socket_options=socket_options)` para que el socket conecte directamente a la IP global fijada mientras `httpcore` mantiene el hostname original en `start_tls(..., server_hostname=...)` y en la cabecera `Host`.
   - En `HttpFetcher.__init__`: cuando `client is None` y `not allow_test_hosts`, construir `transport = httpx.HTTPTransport()`, asignar `transport._pool._network_backend = PublicOnlyNetworkBackend()` y crear `httpx.Client(transport=transport, timeout=httpx.Timeout(30, connect=10), trust_env=False)`. Cuando `client` es inyectado (p. ej. `MockTransport` en tests), usarlo tal cual.
   - En `_robots_for` y `fetch`: capturar `PublicDestinationError as exc` (y en `httpx.HTTPError as exc`, inspeccionar la cadena `__cause__` / `__context__` por `PublicDestinationError`) y lanzar inmediatamente `FetchError(str(found_public_err))` (`"private_destination"` o `"dns_failed"`) en lugar de `"robots_unavailable"` o `"network_error"`.
2. En `collector/browser.py` y `tests/integration/test_browser_fetch.py`:
   - Antes de lanzar Chromium, resolver todos los hosts configurados, rechazar IPs no globales y pasar `--host-resolver-rules` con el mapeo de cada host a una IP pública validada. Este es el control previo a la conexión. Tras `response = page.goto(...)`, comprobar `response.server_addr()` cuando exista y rechazar una IP no global como defensa adicional antes de leer el DOM; este chequeo posterior no sustituye el mapeo previo. Añadir prueba con Playwright simulado que compruebe el orden de configuración y navegación. La red real de Chromium y TLS/SNI quedan pendientes de prueba en Windows durante el cutover.
3. En `collector/__main__.py`:
   - Añadir flag opcional `--check-api` al subcomando `doctor`.
   - En `doctor`: además de `settings.require_secrets()`, crear `settings.data_dir.mkdir(parents=True, exist_ok=True)` y verificar apertura/lectura de `CollectorStore(settings.data_dir / "collector.db")`; si `args.check_api` está activo, hacer `httpx.get(f"{str(settings.api_url).rstrip('/')}/health", timeout=10.0, trust_env=False)` y devolver código `2` si `status_code != 200`.
4. En `scripts/windows/run-collector.ps1`:
   - Si `.venv-collector\Scripts\python.exe` no existe, usar `.venv\Scripts\python.exe`; si ninguno existe, lanzar error claro indicando ejecutar `scripts\windows\install-collector.ps1`.

- [x] **Step 4: Ejecutar toda la batería de pruebas del recolector**

Run: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_http_policy.py tests/unit/test_images.py tests/integration/test_browser_fetch.py tests/integration/test_pipeline.py -q`
Expected: PASS con `0` fallos.

---

### Task 2: Backfill de Imágenes Locales a Base de Datos y Migración Sin Pérdida a PostgreSQL

```text
Encargo:
- Tarea/objetivo: Task 2 — Implementar backfill verificable de las imágenes locales en disco hacia media_assets.content_bytes, reparar migrate_to_postgres.py (URLs postgres://, orden FK real y secuencias PostgreSQL) y probar el cutover 0005->0006 sobre copia verificada de data/backend/university_news.db (bloqueo de cutover #2 en docs/acceptance/production.md:15).
- Requisitos: C05, C06, C07, C08; Review Focus #2 y #3.
- Rol oficial: backend (docs/superpowers/specs/2026-09-06-agent-roles.md).
- Propiedad exclusiva: backend/scripts/backfill_media_bytes.py, backend/scripts/migrate_to_postgres.py, tests/integration/test_legacy_db_cutover.py.
- Entradas: backend/database.py (normalize_database_url, make_engine), backend/models.py (11 tablas ORM + alembic_version), shared/backup.py (backup_sqlite).
- Salidas: backfill_media_bytes(db, search_roots=None) -> dict[str, int] y CLI python -m scripts.backfill_media_bytes; migrate_to_postgres(source_sqlite, destination_url, media_roots=None) -> MigrationReport con orden FK estricto y sincronización de secuencias PostgreSQL; test_legacy_db_cutover.py.
- Validación: .\.venv\Scripts\python.exe -m pytest tests/integration/test_legacy_db_cutover.py tests/integration/test_migrations.py -v
- Restricciones: PROHIBIDO abrir en modo escritura o modificar data/backend/university_news.db original; usar siempre shared.backup.backup_sqlite hacia una ruta nueva en tmp_path. No ejecutar git commit si el checkout es compartido.
```

**Files:**
- Create: `backend/scripts/backfill_media_bytes.py`
- Modify: `backend/scripts/migrate_to_postgres.py`
- Create: `tests/integration/test_legacy_db_cutover.py`

- [x] **Step 1: Escribir pruebas de cutover sobre copia de `data/backend/university_news.db` (o fixture legado `0005`), backfill de bytes y migración ordenada en `tests/integration/test_legacy_db_cutover.py`**

```python
import hashlib
from pathlib import Path
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from database import make_engine, make_session_factory
from models import MediaAsset, News
from scripts.backfill_media_bytes import backfill_media_bytes
from scripts.bootstrap_db import bootstrap_database
from scripts.migrate_to_postgres import ORDERED_TABLES, migrate_to_postgres, sync_postgres_sequences
from shared.backup import backup_sqlite


def test_upgrade_0005_copy_backfills_local_media_and_migrates_in_fk_order(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    real_db = repo_root / "data" / "backend" / "university_news.db"
    real_media = repo_root / "data" / "backend" / "media"

    # backup_sqlite requires destination NOT to exist beforehand
    copied_sqlite = tmp_path / "copied_university_news.db"
    if real_db.is_file():
        backup_sqlite(real_db, copied_sqlite)
    else:
        # Deterministic fallback if test runs in a clean CI clone without data/
        pytest.skip("data/backend/university_news.db not present in clean clone")

    sqlite_url = f"sqlite:///{copied_sqlite.as_posix()}"
    cfg = Config(str(repo_root / "backend" / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", sqlite_url)
    command.upgrade(cfg, "head")

    engine = make_engine(sqlite_url)
    with make_session_factory(engine)() as db:
        stats = backfill_media_bytes(db, search_roots=[real_media])
        assert stats["missing_or_corrupt"] == 0
        assert stats["backfilled"] == 6
        assert db.query(News).filter(News.publication_status == "published").count() == 14
        for asset in db.query(MediaAsset).all():
            assert asset.content_bytes is not None
            assert hashlib.sha256(asset.content_bytes).hexdigest() == asset.sha256
            assert asset.storage_backend == "database"
    engine.dispose()

    target_db = tmp_path / "target_postgres_sim.db"
    target_url = f"sqlite:///{target_db.as_posix()}"
    bootstrap_database(target_url)
    report = migrate_to_postgres(copied_sqlite, target_url, media_roots=[real_media])
    assert report.table_counts["news"] == 14
    assert report.table_counts["media_assets"] == 6


def test_ordered_tables_and_postgres_sequence_sync_sql():
    assert ORDERED_TABLES.index("universities") < ORDERED_TABLES.index("sources")
    assert ORDERED_TABLES.index("sources") < ORDERED_TABLES.index("source_versions")
    assert ORDERED_TABLES.index("sources") < ORDERED_TABLES.index("news")
    assert ORDERED_TABLES.index("news") < ORDERED_TABLES.index("news_revisions")
    assert ORDERED_TABLES.index("news_revisions") < ORDERED_TABLES.index("news_media_history")
    assert "analytics_outbox" in ORDERED_TABLES
    assert "scrape_runs" in ORDERED_TABLES

    executed = []
    class FakeConn:
        def execute(self, stmt, params=None):
            executed.append((str(stmt), params))
    sync_postgres_sequences(FakeConn())
    assert len(executed) == 5
    assert all("setval(pg_get_serial_sequence" in sql for sql, _ in executed)
```
*(Añadir además en el mismo archivo un segundo test autónomo con SQLite sintética creada en `0005` + archivo PNG temporal en `tmp_path` para que también se ejecute siempre en clones limpios sin `data/`).*

- [x] **Step 2: Ejecutar la prueba y verificar que falla**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_legacy_db_cutover.py -v`
Expected: FAIL por `ModuleNotFoundError: No module named 'scripts.backfill_media_bytes'`.

- [x] **Step 3: Implementar `backend/scripts/backfill_media_bytes.py` y actualizar `backend/scripts/migrate_to_postgres.py`**

1. Crear `backend/scripts/backfill_media_bytes.py`:
   - `backfill_media_bytes(db, search_roots: list[Path] | None = None) -> dict[str, int]`:
     - Recorre `db.query(MediaAsset).all()`. Si `asset.content_bytes is not None`, incrementa `already_in_db`.
     - En caso contrario, busca el archivo candidato primero en `Path(asset.storage_key)` y luego en cada `root / asset.sha256[:2]` haciendo glob `f"{asset.sha256}.*"` para `root` en `search_roots or []`.
     - Si el archivo existe, lee sus bytes y comprueba `len(data) == asset.byte_size` y `hashlib.sha256(data).hexdigest() == asset.sha256`. Si coincide, asigna `asset.content_bytes = data`, `asset.storage_backend = "database"`, `asset.storage_key = f"db://{asset.sha256}"` e incrementa `backfilled`; si no existe o el hash no coincide, incrementa `missing_or_corrupt` sin inventar datos.
     - Hace `db.commit()` al final y devuelve `{"already_in_db": ..., "backfilled": ..., "missing_or_corrupt": ...}`.
   - Incluir CLI `python -m scripts.backfill_media_bytes --database-url ... --media-root ...`.
2. Actualizar `backend/scripts/migrate_to_postgres.py`:
   - Definir `ORDERED_TABLES: tuple[str, ...] = ("universities", "sources", "source_versions", "news", "news_revisions", "media_assets", "news_media_history", "scrape_runs", "ingest_receipts", "collector_status", "analytics_outbox")`.
   - Definir `SEQUENCE_TABLES: tuple[str, ...] = ("universities", "sources", "news", "news_revisions", "news_media_history")` y `sync_postgres_sequences(conn) -> None` que ejecuta para cada `tbl` de `SEQUENCE_TABLES`:
     `conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), COALESCE((SELECT MAX(id) FROM {tbl}), 1), (SELECT MAX(id) IS NOT NULL FROM {tbl}))"))`.
   - En `migrate_to_postgres(source_sqlite: Path, destination_url: str, media_roots: list[Path] | None = None) -> MigrationReport`:
     - Normalizar `destination_url = normalize_database_url(destination_url)` usando `database.normalize_database_url`.
     - Si el destino aún no tiene las tablas creadas, llamar `bootstrap_database(destination_url)` para llevarlo a Alembic `head` (`0006`).
     - Migrar tablas siguiendo `ORDERED_TABLES` (más cualquier tabla extra no listada excepto `sqlite_*` y `alembic_version`). Para filas de `media_assets` donde `row.get("content_bytes") is None`, intentar cargar y verificar por SHA-256 desde `Path(row["storage_key"])` o `media_roots` igual que en `backfill_media_bytes`, actualizando `content_bytes`, `storage_backend="database"` y `storage_key=f"db://{sha}"`.
     - Verificar que el conteo insertado en destino coincida exactamente con `counts[table_name]` antes de cerrar la transacción; si `pg_engine.dialect.name == "postgresql"`, invocar `sync_postgres_sequences(p_conn)`.

- [x] **Step 4: Ejecutar pruebas de migraciones y cutover de datos**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_legacy_db_cutover.py tests/integration/test_migrations.py -q`
Expected: PASS con `0` fallos (incluyendo las 14 noticias y las 6 imágenes reales verificadas sobre copia temporal).

---

### Task 3: Alineación de Catálogos en `AdminPanel.tsx`, Fallback Limpio de Imágenes en `NewsPage.tsx` y `vercel.json`

```text
Encargo:
- Tarea/objetivo: Task 3 — Alinear el formulario administrativo con las categorías oficiales (shared.contracts.Category) y las universidades reales de la API, evitar huecos visuales cuando falla una imagen en NewsPage.tsx y endurecer vercel.json con cleanUrls y cabeceras de seguridad.
- Requisitos: C04, C06, C08.
- Rol oficial: frontend (docs/superpowers/specs/2026-09-06-agent-roles.md).
- Propiedad exclusiva: src/components/AdminPanel.tsx, src/components/NewsPage.tsx, vercel.json, tests/e2e/public-news.spec.ts, tests/e2e/admin-collection.spec.ts.
- Entradas: src/lib/admin-api.ts (listUniversities ya implementado), src/lib/api.ts (resolveMediaUrl, resolveExternalUrl), shared/contracts.py (Category).
- Salidas: AdminPanel.tsx consumiendo listUniversities(token) y las 14 categorías exactas del contrato; NewsPage.tsx ocultando/reemplazando limpiamente imágenes con error de red; vercel.json sin rewrites circulares y con security headers.
- Validación: npm run lint; npm run typecheck; npm run build
- Restricciones: No tocar src/lib/api.ts, src/lib/admin-api.ts ni src/components/NewsContextAssistant.tsx salvo que se proponga cambio de contrato (no requerido). No ejecutar git commit si el checkout es compartido.
```

**Files:**
- Modify: `src/components/AdminPanel.tsx`
- Modify: `src/components/NewsPage.tsx`
- Modify: `vercel.json`
- Modify: `tests/e2e/public-news.spec.ts`
- Modify: `tests/e2e/admin-collection.spec.ts`

- [x] **Step 1: Alinear `CATEGORIES` y universidades dinámicas en `src/components/AdminPanel.tsx`**

1. En `src/components/AdminPanel.tsx`:
   - Sustituir `CATEGORIES` (línea 36) por las 14 categorías exactas de `shared/contracts.py`:
     `const CATEGORIES = ["Academia", "Admisión", "Becas", "Cultura", "Deportes", "Empleo", "Género", "Infraestructura", "Investigación", "Tecnología", "Vinculación", "Institucional", "Opinión", "General"];`
   - Eliminar el arreglo hardcodeado `UNIVERSITIES` (línea 37 con `"Universidad Politécnica"`, `"Universidad de las Artes"`, etc.).
   - En `LegacyAdminPanel({ token })`, cargar las universidades reales configuradas mediante `listUniversities(token)` (importado de `@/lib/admin-api`) combinadas sin duplicados con `stats?.universities ?? []`, pasándolas como prop `universities: string[]` a `NewsForm` (manteniendo la opción de escribir manualmente si la lista está vacía o se elige `"Otra"`).

- [x] **Step 2: Reemplazar `visibility = "hidden"` por fallback editorial limpio en `src/components/NewsPage.tsx` y endurecer `vercel.json`**

1. En `src/components/NewsPage.tsx`:
   - Añadir estado o subcomponente `CardMedia({ src, alt }: { src: string | null; alt: string })` que mantenga `[broken, setBroken] = useState(false)` (reiniciado por `key={src ?? "empty"}`): cuando `!src || broken`, renderiza el contenedor placeholder `<div className="mb-4 flex aspect-[16/10] items-center justify-center bg-muted text-muted-foreground"><NewspaperIcon className="size-9"/><span className="sr-only">Sin imagen disponible</span></div>`; cuando carga bien, muestra `<img>` con `onError={() => setBroken(true)}`.
   - En `NewsDialog`, mantener `[imageBroken, setImageBroken] = useState(false)` (o subcomponente con `key={imageUrl}`) de modo que si la imagen falla al cargar no renderice un bloque vacío de `480px`.
2. En `vercel.json`:
   ```json
   {
     "framework": "astro",
     "buildCommand": "npm run build",
     "outputDirectory": "dist",
     "installCommand": "npm install",
     "cleanUrls": true,
     "headers": [
       {
         "source": "/(.*)",
         "headers": [
           { "key": "X-Content-Type-Options", "value": "nosniff" },
           { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
           { "key": "X-Frame-Options", "value": "DENY" }
         ]
       }
     ]
   }
   ```
3. Actualizar `tests/e2e/public-news.spec.ts` y `tests/e2e/admin-collection.spec.ts` si alguna expectativa dependía de las opciones antiguas de universidad o del fallback de imagen rota.

- [x] **Step 3: Ejecutar lint, typecheck y build estático de Astro**

Run: `npm run lint; Write-Output "LINT=$LASTEXITCODE"; npm run typecheck; Write-Output "TC=$LASTEXITCODE"; npm run build; Write-Output "BUILD=$LASTEXITCODE"`
Expected: `LINT=0` (`0 errors, 0 warnings`), `TC=0` (`0 errors`), `BUILD=0` (generando `dist/index.html`, `dist/chat/index.html` y `dist/admin/index.html`).

---

### Task 4: IP Real Tras Proxy en Railway, `snapshot_marker` `O(1)` en `ChatGuard` y Cota de Memoria en `NewsAssistant`

```text
Encargo:
- Tarea/objetivo: Task 4 — Evitar que todos los usuarios compartan un solo rate-limit detrás del balanceador de Railway, eliminar la lectura completa de cuerpos News.content en cada consulta del chat garantizando News.updated_at en toda escritura, y acotar el pool en memoria de NewsAssistant.
- Requisitos: C01, C03, C06, C07, C08; Review Focus #4.
- Rol oficial: backend (docs/superpowers/specs/2026-09-06-agent-roles.md).
- Propiedad exclusiva: backend/rag/chat_guard.py, backend/rag/news_assistant.py, backend/routers/chat.py, backend/routers/news.py, backend/routers/admin.py, backend/services/ingestion.py, backend/services/media.py, tests/unit/test_chat_guard.py, tests/integration/test_chat.py.
- Entradas: BackendSettings.app_env (backend/config.py), modelos ORM en backend/models.py.
- Salidas: extract_client_ip(request, *, trust_proxy_headers: bool) -> str y snapshot_marker(db) en O(1) SQL en backend/rag/chat_guard.py; actualización explícita de News.updated_at en todas las mutaciones; cota candidate_pool_limit=200 en NewsAssistant.prepare_context.
- Validación: .\.venv\Scripts\python.exe -m pytest tests/unit/test_chat_guard.py tests/unit/test_chat_openrouter.py tests/integration/test_chat.py tests/integration/test_rag_visibility.py tests/integration/test_ingestion.py tests/integration/test_media_api.py -v
- Restricciones: No cambiar la firma externa de POST /api/chat/ ni el formato de secciones ([NOTICIA EN FOCO], [ANTECEDENTES RELACIONADOS DEL ARCHIVO], [CATÁLOGO RECIENTE DEL PORTAL]). No ejecutar git commit si el checkout es compartido.
```

**Files:**
- Modify: `backend/rag/chat_guard.py`
- Modify: `backend/rag/news_assistant.py`
- Modify: `backend/routers/chat.py`
- Modify: `backend/routers/news.py`
- Modify: `backend/routers/admin.py`
- Modify: `backend/services/ingestion.py`
- Modify: `backend/services/media.py`
- Test: `tests/unit/test_chat_guard.py`
- Test: `tests/integration/test_chat.py`

- [x] **Step 1: Añadir pruebas de `extract_client_ip` anti-spoofing, invalidación `O(1)` al editar/archivar y cota de candidatos en `tests/unit/test_chat_guard.py` y `tests/integration/test_chat.py`**

En `tests/unit/test_chat_guard.py`, añadir:
```python
from starlette.requests import Request
from rag.chat_guard import extract_client_ip


def _make_request(client_host: str, xff: str | None = None) -> Request:
    headers = [(b"x-forwarded-for", xff.encode())] if xff is not None else []
    scope = {"type": "http", "client": (client_host, 12345), "headers": headers}
    return Request(scope)


def test_extract_client_ip_uses_railway_real_ip_only_when_proxy_trusted():
    # Railway public HTTP edge supplies X-Real-IP; ignore caller-controlled XFF.
    req = _make_request("100.64.0.5", "1.1.1.1, 190.45.10.22")
    req.scope["headers"].append((b"x-real-ip", b"190.45.10.22"))
    assert extract_client_ip(req, trust_proxy_headers=True) == "190.45.10.22"
    # Outside the trusted production edge, ignore forwarded headers completely.
    assert extract_client_ip(req, trust_proxy_headers=False) == "100.64.0.5"
```
En `tests/integration/test_chat.py`, añadir prueba que verifique que tras cachear una respuesta de `/api/chat/`, editar el título/cuerpo vía `PUT /api/news/{id}` o archivar vía `PATCH /api/admin/news/{id}/publication` actualiza `updated_at` e invalida inmediatamente el caché sin cargar `News.content` en `snapshot_marker`.

- [x] **Step 2: Ejecutar las pruebas y verificar que fallan**

Run: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_chat_guard.py tests/integration/test_chat.py -v`
Expected: FAIL por `ImportError: cannot import name 'extract_client_ip' from 'rag.chat_guard'`.

- [x] **Step 3: Implementar sellado de `News.updated_at`, `snapshot_marker` `O(1)`, `extract_client_ip` y cota `candidate_pool_limit=200`**

1. Sellar explícitamente `updated_at = datetime.now(timezone.utc)` (o el parámetro `now` ya disponible en la función) en toda escritura sobre `News`:
   - `backend/routers/news.py`: en `create` (`created_at=now, updated_at=now`), `update` (`n.updated_at = now`) y `delete` (`n.updated_at = now`).
   - `backend/routers/admin.py`: en `publication` (`n.updated_at = datetime.now(timezone.utc)`).
   - `backend/services/ingestion.py`: en `persist_article_revision` y `approve_revision` (`news.updated_at = now`).
   - `backend/services/media.py`: en `receive_media` cuando `applied` y `changed` (`news.updated_at = now`).
2. En `backend/rag/chat_guard.py`:
   - Implementar `extract_client_ip(request, *, trust_proxy_headers: bool) -> str`: si `trust_proxy_headers` es `True`, leer y validar como IP `request.headers.get("x-real-ip", "")`; si falta o es inválida, devolver `request.client.host if request.client else "unknown"`. Ignorar `X-Forwarded-For` porque Railway no garantiza la posición del cliente en esa cadena.
   - Simplificar `snapshot_marker(self, db) -> tuple[int, int, str]` a una sola consulta SQL agregada sin leer filas completas:
     ```python
     count, max_id, latest_updated, latest_created = db.query(
         func.count(News.id),
         func.max(News.id),
         func.max(News.updated_at),
         func.max(News.created_at),
     ).filter(News.publication_status == "published").one()
     u_str = latest_updated.isoformat() if latest_updated else ""
     c_str = latest_created.isoformat() if latest_created else ""
     return int(count or 0), int(max_id or 0), f"{u_str}|{c_str}"
     ```
3. En `backend/routers/chat.py`:
   - Reemplazar `ip = request.client.host if request.client else "unknown"` por `ip = extract_client_ip(request, trust_proxy_headers=(request.app.state.settings.app_env == "production"))`.
4. En `backend/rag/news_assistant.py`:
   - Añadir `candidate_pool_limit: int = 200` a `NewsAssistant.__init__`.
   - En `prepare_context`, reemplazar `base.filter(News.id != news_id).all()` y `base.all()` por consultas ordenadas `order_by(News.published_at.desc(), News.id.desc()).limit(self.candidate_pool_limit).all()` para acotar de forma determinista el consumo de RAM en Railway.

- [x] **Step 4: Ejecutar la suite de chat, ingesta y medios**

Run: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_chat_guard.py tests/unit/test_chat_openrouter.py tests/integration/test_chat.py tests/integration/test_rag_visibility.py tests/integration/test_ingestion.py tests/integration/test_media_api.py -q`
Expected: PASS con `0` fallos.

---

### Task 5: Aceptación QA Post-Bloqueos y Actualización de `docs/acceptance/production.md` (`ready_for_cutover`)

```text
Encargo:
- Tarea/objetivo: Task 5 — Auditar independientemente las Tareas 1–4, ampliar la prueba integral test_production_readiness.py con las garantías de proxy IP e IP pinning, verificar la migración sobre copia real de data/backend/university_news.db y actualizar docs/acceptance/production.md y docs/context-deploy.md levantando cutover_blocked a ready_for_cutover (sin afirmar que el despliegue externo ya ocurrió).
- Requisitos: C01–C08; AGENTS.md sección «Cierre de una tarea».
- Rol oficial: qa (docs/superpowers/specs/2026-09-06-agent-roles.md).
- Propiedad exclusiva: tests/integration/test_production_readiness.py, docs/acceptance/production.md, docs/context-deploy.md, .env.example, backend/.env.example, collector/.env.example.
- Entradas: Cambios integrados de Task 1, Task 2, Task 3 y Task 4.
- Salidas: Suite global Python + Frontend 100% en verde; evidencia documentada en docs/acceptance/production.md con estado ready_for_cutover y procedimiento exacto de migración de data/backend/university_news.db en docs/context-deploy.md.
- Validación: .\.venv\Scripts\python.exe -m pytest -q; npm run lint; npm run typecheck; npm run build
- Restricciones: No declarar que Railway/Vercel ya están desplegados en internet; registrar solo la evidencia automatizada realmente ejecutada. No ejecutar git commit si el checkout es compartido.
```

**Files:**
- Modify: `tests/integration/test_production_readiness.py`
- Modify: `docs/acceptance/production.md`
- Modify: `docs/context-deploy.md`
- Modify: `.env.example`
- Modify: `backend/.env.example`
- Modify: `collector/.env.example`

- [x] **Step 1: Ampliar `tests/integration/test_production_readiness.py` con verificación de `X-Real-IP` en producción e invalidación de caché tras edición editorial**

Añadir al final de `test_seeded_uach_collection_media_and_contextual_chat_are_ready` en `tests/integration/test_production_readiness.py`:
- Verificación de que en `app_env="production"` dos visitantes con distinto `X-Real-IP` válido (`"190.45.1.10"` vs `"190.45.1.11"`) tienen contadores de rate-limit independientes aunque compartan el mismo `request.client.host`, y que cambiar `X-Forwarded-For` no elude el límite.
- Verificación de que editar una noticia vía `PUT /api/news/{first_id}` invalida de inmediato la entrada cacheada en `ChatGuard` gracias al sellado de `updated_at`.

- [x] **Step 2: Ejecutar toda la suite del repositorio (Python + Frontend)**

Run: `.\.venv\Scripts\python.exe -m pytest -q; Write-Output "PYTEST=$LASTEXITCODE"; npm run lint; Write-Output "LINT=$LASTEXITCODE"; npm run typecheck; Write-Output "TC=$LASTEXITCODE"; npm run build; Write-Output "BUILD=$LASTEXITCODE"`
Expected: `PYTEST=0`, `LINT=0`, `TC=0`, `BUILD=0` con todas las pruebas aprobadas.

- [x] **Step 3: Actualizar `docs/acceptance/production.md`, `docs/context-deploy.md` y `.env.example`**

1. En `docs/acceptance/production.md`:
   - Actualizar el estado de `cutover_blocked` a **`ready_for_cutover (implementación y bloqueos pre-despliegue resueltos localmente; pendiente ejecución manual en cuentas Railway/Vercel/Windows)`**, registrando la evidencia exacta obtenida en `test_legacy_db_cutover.py` (copia verificada de `data/backend/university_news.db` con 14 noticias y 6 imágenes rellenadas en `content_bytes`, más sincronización de secuencias PostgreSQL) y en `test_http_policy.py` (`PublicOnlyNetworkBackend` bloqueando DNS rebinding en `connect_tcp`).
   - Nota sobre prueba contra instancia PostgreSQL 15+ viva: documentar en la sección Railway del checklist el comando exacto para migrar opcionalmente los 14 artículos e imágenes locales existentes antes de abrir tráfico (`python -m scripts.migrate_to_postgres --source data/backend/university_news.db --destination "$DATABASE_URL"` tras un `backup_sqlite` local).
2. En `docs/context-deploy.md` y `.env.example` / `backend/.env.example` / `collector/.env.example`:
   - Documentar el flujo completo de puesta en marcha en 4 pasos exactos:
     1. Push de los commits integrados en `backend-webscrapper` (o merge a `main`).
     2. Creación de PostgreSQL + servicio API en Railway (`APP_ENV=production`, `DATABASE_URL`, `ADMIN_TOKEN`, `COLLECTOR_TOKEN`, `COLLECTOR_ID`, `ALLOWED_ORIGINS`, `RAG_ENABLED=true`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL=nvidia/nemotron-3.5-super-vl:free`) y migración opcional de los 14 artículos locales con `migrate_to_postgres.py`.
     3. Configuración de `PUBLIC_API_URL=https://<railway-domain>` en Vercel y redeploy.
     4. Ejecución en Windows de `python -m collector --env collector/.env doctor --check-api`, `run-once` y registro en Task Scheduler con `scripts/windows/register-collector-task.ps1`.

---

### Task 6: Integración Final del Coordinador y Commits Atómicos por Rol

```text
Encargo:
- Tarea/objetivo: Task 6 — Verificar contratos, pruebas e higiene del árbol Git, y consolidar todos los cambios de producto, pruebas y documentación en commits atómicos por rol sobre la rama backend-webscrapper sin incluir archivos de herramientas externas.
- Requisitos: C04, C08; Review Focus #5; AGENTS.md Reglas 1, 8, 10 y 12.
- Rol oficial: coordinator (docs/superpowers/specs/2026-09-06-agent-roles.md).
- Propiedad exclusiva: Integración Git de los archivos verificados de collector/, scripts/windows/, backend/, railway.toml, src/, vercel.json, tsconfig.json, tests/ y docs/, más actualización de checkboxes realmente ejecutados en este plan.
- Entradas: Entregas aprobadas de Task 1 a Task 5.
- Salidas: Historial de commits limpio por rol en la rama activa, árbol de producto limpio y reporte ejecutivo final de entrega.
- Validación: git status --short; .\.venv\Scripts\python.exe -m pytest -q; npm run lint; npm run typecheck; npm run build
- Restricciones: NUNCA ejecutar git add ., git push ni git merge sin instrucción explícita adicional del usuario. Excluir estrictamente skills-lock.json, .agents/skills/* y cualquier archivo .env.
```

**Files:**
- Modify: `docs/superpowers/plans/2026-11-01-produccion-uninews.md` (marcar `[x]` únicamente en los pasos realmente ejecutados y verificados)

- [x] **Step 1: Auditar `git status --short` y comprobar que no existen secretos ni regresiones**

Run: `git status --short; .\.venv\Scripts\python.exe -m pytest -q; npm run lint; npm run typecheck; npm run build`
Expected: Suite Python y checks Frontend en `0` errores; ningún archivo `.env` real listado para commit.

- [x] **Step 2: Crear commits atómicos por rol con rutas explícitas (sin tocar `skills-lock.json` ni `.agents/skills/*`)**

Ejecutar en orden verificando cada commit:

```powershell
# 1. Rol collector: imágenes redirigidas/lazy-load, heartbeat, IP pinning anti-DNS-rebinding y scripts Windows
git add collector/http.py collector/images.py collector/pipeline.py collector/browser.py collector/__main__.py collector/.env.example scripts/windows/run-collector.ps1 tests/unit/test_http_policy.py tests/unit/test_images.py tests/integration/test_browser_fetch.py tests/integration/test_pipeline.py
git commit -m "feat(collector): pin validated public IPs, support redirected lazy images, and send heartbeats"

# 2. Rol backend (core, medios en PostgreSQL, seed DatosLab y migración de datos locales)
git add backend/config.py backend/database.py backend/migrations/env.py backend/migrations/versions/0006_db_media_bytes.py backend/models.py backend/schemas.py backend/requirements.txt backend/routers/admin.py backend/routers/news.py backend/routers/media.py backend/services/ingestion.py backend/services/media.py backend/scripts/datoslab_catalog.py backend/scripts/seed_production_sources.py backend/scripts/backfill_media_bytes.py backend/scripts/migrate_to_postgres.py backend/.env.example railway.toml tests/unit/test_production_config.py tests/integration/test_media_api.py tests/integration/test_seed_production_sources.py tests/integration/test_legacy_db_cutover.py
git commit -m "feat(backend): store media in PostgreSQL, harden production settings, and fix lossless DB migration"

# 3. Rol backend (asistente IA multi-noticia, ChatGuard O(1) e IP tras proxy Railway)
git add backend/main.py backend/rag/chat_guard.py backend/rag/news_assistant.py backend/rag/openrouter.py backend/routers/chat.py tests/unit/test_chat_guard.py tests/integration/test_chat.py
git commit -m "feat(chat): add hybrid multi-news context retrieval, O(1) cache invalidation, and proxy-safe rate limits"

# 4. Rol frontend (asistente contextual en cada noticia, filtro universidad, panel /admin y vercel.json)
git add src/lib/api.ts src/lib/admin-api.ts src/components/NewsContextAssistant.tsx src/components/NewsPage.tsx src/components/ChatInterface.tsx src/components/AdminPanel.tsx src/components/admin/ReviewPanel.tsx src/components/admin/SourcesPanel.tsx src/components/admin/RunsPanel.tsx src/layouts/main.astro tsconfig.json vercel.json .env.example tests/e2e/public-news.spec.ts tests/e2e/admin-collection.spec.ts
git commit -m "feat(web): embed multi-news AI assistant in reader, align admin catalog, and harden Vercel config"

# 5. Rol qa y coordinator (aceptación pre-cutover, runbook y especificación/plan actualizados)
git add tests/integration/test_production_readiness.py docs/acceptance/production.md docs/context-deploy.md docs/superpowers/specs/2026-11-01-produccion-uninews-design.md docs/superpowers/plans/2026-11-01-produccion-uninews.md
git commit -m "docs(qa): verify production cutover readiness and record subagent implementation plan"
```

- [x] **Step 3: Verificación final post-commit y entrega al usuario**

Run: `git status --short; git log -n 6 --oneline`
Expected: Únicamente permanecen sin comitear los archivos preexistentes de herramientas (`M skills-lock.json` y `?? .agents/skills/`), y los 5 commits atómicos están listos para que el usuario ejecute `git push` y el cutover en Railway, Vercel y Windows.
