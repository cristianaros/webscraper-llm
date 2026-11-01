# Diseño de Puesta en Producción y Contexto IA Híbrido — UniNews (Adaptado al Estado Actual del Proyecto)

**Fecha:** 2026-11-01  
**Estado:** Aprobado y actualizado contra el árbol real del repositorio (`83 passed`, revisión local `0005` en `data/backend/university_news.db`).  
**Documentos base del repositorio:** [AGENTS.md](../../../AGENTS.md), [2026-09-06-uninews-python-openrouter.md](2026-09-06-uninews-python-openrouter.md) y [2026-09-06-agent-roles.md](2026-09-06-agent-roles.md).  
**Enmienda de alcance:** Sustituye el despliegue en Google Cloud/BigQuery para esta puesta en marcha por la topología **Vercel (Astro estático) + Railway (FastAPI + PostgreSQL administrado) + Windows PC (Recolector Python en Programador de Tareas)**, conservando intactos `analytics/` y `evaluation/` y manteniendo `nvidia/nemotron-3.5-super-vl:free` con costo cero.

---

## 1. Diagnóstico Verificado de lo que YA hay en el Proyecto

Tras inspeccionar el código y los datos actuales del repositorio:

1. **Base funcional ya implementada en el árbol de trabajo (verificada con `83 passed` en `pytest -q`, `eslint` 0, `astro check` 0 y `astro build` 0):**
   - **Backend (`backend/`):** `BackendSettings` valida secretos fuertes y `allowed_origins` en `APP_ENV=production` (`backend/config.py`); `normalize_database_url` y pool PostgreSQL en `backend/database.py`; escape de `%` en `backend/migrations/env.py`; migración `0006_db_media_bytes.py` y almacenamiento de bytes verificados en `MediaAsset.content_bytes` (`backend/services/media.py`, `backend/routers/media.py`); recuperación híbrida de 2 capas en `NewsAssistant` (`backend/rag/news_assistant.py`), caché y límites en `ChatGuard` (`backend/rag/chat_guard.py`, `backend/routers/chat.py`); catálogo `VERIFIED_SLUGS` y precarga idempotente en `backend/scripts/seed_production_sources.py` conectada a `railway.toml`.
   - **Recolector (`collector/`):** extracción de candidatos `data-src`, `data-lazy-src`, `data-original`, `srcset`, `og:image`, `twitter:image`, subdominios institucionales y `i0.wp.com`–`i2.wp.com` en `collector/images.py`, URL final post-redirección en `ImageAsset.original_url` y envío de `CollectorHeartbeat` en `collector/pipeline.py`.
   - **Frontend (`src/`):** `NewsContextAssistant.tsx` embebido dentro de `NewsDialog` en `NewsPage.tsx`, filtro por universidad, `resolveMediaUrl` / `resolveExternalUrl` en `src/lib/api.ts`, y cliente administrativo autenticado en `src/lib/admin-api.ts` con acciones en `ReviewPanel.tsx`, `SourcesPanel.tsx` y `RunsPanel.tsx`.
2. **Datos locales reales existentes en `data/`:**
   - `data/backend/university_news.db` está en la revisión Alembic `0005` y contiene **14 noticias publicadas**, **23 universidades**, **23 fuentes**, **28 revisiones** y **6 activos en `media_assets`** con `storage_backend='local'` y `storage_key` apuntando a archivos PNG reales en `data/backend/media/`.
   - `data/collector/collector.db` contiene **439 `work_items`** y **46 `local_media`**.
3. **Brechas reales que mantienen el proyecto en `cutover_blocked` (`docs/acceptance/production.md`) o afectan operación productiva:**
   - **B1 — Ventana TOCTOU de DNS Rebinding en `collector/http.py` y `collector/browser.py`:** `HttpFetcher._validate()` resuelve DNS y verifica `ip.is_global`, pero `httpx.Client` vuelve a resolver DNS al conectar el socket sin fijar la IP validada (`docs/acceptance/production.md:16`). Además, `scripts/windows/run-collector.ps1` exige `.venv-collector` sin fallback al `.venv` existente en el proyecto.
   - **B2 — Migración de datos e imágenes locales a PostgreSQL (`backend/scripts/migrate_to_postgres.py`):** no normaliza `postgres://`, inserta tablas sin orden topológico de claves foráneas, no rellena `media_assets.content_bytes` a partir de las 6 imágenes locales de `data/backend/media/` (que fallarían en el contenedor Linux de Railway) y no sincroniza las secuencias `SERIAL` de PostgreSQL tras insertar IDs explícitos. Tampoco se ha ejecutado aún el ensayo automatizado `0005`→`0006` + backfill sobre copia verificada de `data/backend/university_news.db` (`docs/acceptance/production.md:15`).
   - **B3 — Proxy IP y escalabilidad en Railway (`backend/routers/chat.py`, `backend/rag/chat_guard.py`, `backend/rag/news_assistant.py`):** `request.client.host` detrás del balanceador de Railway devuelve la IP del proxy (compartiendo el rate-limit de `6 req/min` entre todos los usuarios); `ChatGuard.snapshot_marker` lee y hashea en Python el cuerpo completo de todas las noticias publicadas en cada consulta porque `routers/news.py` y `routers/admin.py` no sellan explícitamente `News.updated_at`; y `NewsAssistant.prepare_context` ejecuta `base.all()` sin cota sobre toda la tabla `news`.
   - **B4 — Desalineación residual en Frontend y `vercel.json`:** `src/components/AdminPanel.tsx` mantiene categorías fuera del contrato `shared.contracts.Category` y universidades ficticias hardcodeadas en vez de usar `/api/admin/universities`; `src/components/NewsPage.tsx` usa `visibility="hidden"` ante error de carga de imagen dejando huecos vacíos; y `vercel.json` contiene un rewrite circular sin `cleanUrls` ni cabeceras de seguridad.
   - **B5 — Integración Git pendiente:** hay 38 archivos de producto/pruebas modificados o sin seguimiento en el árbol de trabajo junto a archivos de herramientas (`.agents/skills/*`, `skills-lock.json`) que aún no han sido integrados en commits limpios por rol para poder hacer `git push` hacia Railway y Vercel.

---

## 2. Restricciones Globales (`Global Constraints`)

- **C01:** El único modelo activo para extracción y chat es `nvidia/nemotron-3.5-super-vl:free` por OpenRouter con `provider.max_price = {"prompt": 0, "completion": 0}`.
- **C02:** El recolector corre en Windows fuera de FastAPI/Vercel y no importa módulos de `backend/` (solo `shared/`).
- **C03:** En `APP_ENV=production`, `BackendSettings` rechaza tokens débiles/repetidos/por defecto (`< 16` chars, `admin-test`, `worker-test`) y `allowed_origins` vacío.
- **C04:** Ningún secreto (`ADMIN_TOKEN`, `COLLECTOR_TOKEN`, `OPENROUTER_API_KEY`, `DATABASE_URL`) entra en Git, logs, capturas ni variables `PUBLIC_*`.
- **C05:** Las migraciones y scripts de datos son aditivos y se prueban sobre copias verificadas (`backup_sqlite`); prohibido modificar `data/backend/university_news.db` o `data/collector/collector.db` sin respaldo previo.
- **C06:** `/api/news`, `/api/media/{sha256}` y `/api/chat` exponen exclusivamente filas con `publication_status == "published"`.
- **C07:** La suite automatizada (`pytest -q`) no realiza tráfico externo real; usa fixtures, copias temporales y `MockTransport`.
- **C08:** Coordinación multiagente sujeta a [AGENTS.md](../../../AGENTS.md) y [2026-09-06-agent-roles.md](2026-09-06-agent-roles.md): un solo propietario activo por archivo, máximo 3 subagentes simultáneos y prohibición absoluta de `git add .`.

---

## 3. Diseño Técnico de Cierre para Producción

### 3.1 Fijación de IP Anti-DNS-Rebinding en el Recolector (`collector/http.py`, `collector/browser.py`)
- **`PublicOnlyNetworkBackend(httpcore.SyncBackend)`:** cuando `HttpFetcher` construye su `httpx.Client` real (es decir, cuando no recibe un cliente de prueba con `MockTransport` ni está en `allow_test_hosts=True`), inyecta un `HTTPTransport` cuyo `_pool._network_backend` resuelve `socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)` justo en `connect_tcp`:
  1. Comprueba que la lista no esté vacía y que **todas** las direcciones resueltas cumplan `ipaddress.ip_address(ip).is_global`. Si alguna es privada, loopback, link-local o reservada, lanza `PublicDestinationError("private_destination")` antes de abrir socket TCP.
  2. Conecta directamente a la primera IP global validada (`super().connect_tcp(pinned_ip, port, ...)`), evitando una segunda resolución DNS del sistema operativo, mientras `httpcore` conserva el `server_hostname` original para TLS SNI, validación de certificado X.509 y cabecera `Host`.
  3. `HttpFetcher.fetch` captura `PublicDestinationError` (o `httpx.ConnectError` envolviéndolo) y lanza `FetchError("private_destination")`.
- **`BrowserFetcher` (`collector/browser.py`):** además de validar cada request en `context.route`, inspecciona `response.server_addr()` tras `page.goto(...)`; si existe `ipAddress` y no es global (cuando `not self.http.allow_test_hosts`), aborta y lanza `FetchError("private_destination")`.
- **Operación Windows (`scripts/windows/run-collector.ps1`, `collector/__main__.py`):** `run-collector.ps1` usa `.venv-collector\Scripts\python.exe` si existe y cae automáticamente a `.venv\Scripts\python.exe`. `python -m collector --env <path> doctor` verifica además que `settings.data_dir` sea escribible y soporta `--check-api` opcional para validar `GET {api_url}/health`.

### 3.2 Backfill de Imágenes Locales y Migración Sin Pérdida a PostgreSQL (`backend/scripts/`)
- **`backfill_media_bytes(db, media_search_roots: list[Path] | None = None) -> dict[str, int]` en `backend/scripts/backfill_media_bytes.py`:**
  - Busca filas en `media_assets` con `content_bytes IS NULL`.
  - Localiza el archivo en `Path(asset.storage_key)` o bajo `<root>/<sha256[:2]>/<sha256>.*`, verifica `hashlib.sha256(data).hexdigest() == asset.sha256` y `len(data) == asset.byte_size`, y guarda `asset.content_bytes = data`, `asset.storage_backend = "database"`, `asset.storage_key = f"db://{asset.sha256}"`.
- **`migrate_to_postgres.py` reparado:**
  - Normaliza `destination_url` mediante `normalize_database_url` (acepta `postgres://` y `postgresql://` de Railway).
  - Verifica que el destino tenga el esquema Alembic en `0006` (o ejecuta `bootstrap_database(destination_url)` si está vacío).
  - Copia en orden topológico estricto de claves foráneas: `universities` → `sources` → `source_versions` → `news` → `news_revisions` → `media_assets` → `news_media_history` → `scrape_runs` → `ingest_receipts` → `collector_status` → `analytics_outbox`.
  - Si alguna fila de `media_assets` viene con `content_bytes IS NULL` y existe el archivo local verificable por SHA-256, incorpora sus bytes durante la migración.
  - En PostgreSQL (`pg_engine.dialect.name == "postgresql"`), sincroniza las secuencias de todas las tablas con clave primaria entera autoincremental (`universities`, `sources`, `news`, `news_revisions`, `news_media_history`) mediante `SELECT setval(pg_get_serial_sequence(:tbl, 'id'), COALESCE((SELECT MAX(id) FROM ...), 1), (SELECT MAX(id) IS NOT NULL FROM ...))`.
  - Verifica conteos exactos origen == destino en la misma transacción antes de confirmar.

### 3.3 IP Real Tras Proxy en Railway y `ChatGuard` / `NewsAssistant` en Tiempo `O(1)` (`backend/`)
- **`extract_client_ip(request: Request, *, trust_proxy_headers: bool) -> str` en `backend/rag/chat_guard.py`:**
  - Si `trust_proxy_headers` es `True` (`settings.app_env == "production"`) y existe `X-Real-IP` con sintaxis de IP válida, usa esa dirección. La [documentación de Railway](https://docs.railway.com/networking/public-networking/specs-and-limits) identifica `X-Real-IP` como IP remota del cliente en el edge HTTP público; no garantiza una posición estable del cliente en `X-Forwarded-For`. Si falta o es inválida, y en desarrollo/tests sin proxy confiable, usa `request.client.host`. El tráfico de red privada no pasa por la limpieza de cabeceras del edge público y requiere controles de ingreso propios.
- **Sellado consistente de `News.updated_at` y `snapshot_marker` `O(1)`:**
  - `backend/routers/news.py` (`create`, `update`, `delete`), `backend/routers/admin.py` (`publication`), `backend/services/ingestion.py` (`persist_article_revision`, `approve_revision`) y `backend/services/media.py` (`receive_media` al asociar imagen) asignan explícitamente `news.updated_at = now` (UTC).
  - Con `updated_at` garantizado en toda mutación, `ChatGuard.snapshot_marker(db)` ejecuta **una única consulta SQL agregada** sobre `News.publication_status == "published"` con `COUNT(id)`, `MAX(id)`, `MAX(updated_at)` y `MAX(created_at)`, eliminando la lectura completa de cuerpos `News.content` en cada request.
- **Cota de memoria en `NewsAssistant.prepare_context` (`backend/rag/news_assistant.py`):**
  - El pool de candidatos para antecedentes relacionados y búsqueda global se acota a las `200` noticias publicadas más recientes (`order_by(News.published_at.desc(), News.id.desc()).limit(200)`), evitando cargar miles de cuerpos completos en memoria de un contenedor Railway de 512 MB.

### 3.4 Alineación Editorial en Frontend y `vercel.json` (`src/`, `vercel.json`)
- **`src/components/AdminPanel.tsx`:** `CATEGORIES` se alinea exactamente con las 14 categorías de `shared/contracts.py:Category`; el formulario manual carga las universidades reales configuradas mediante `listUniversities(token)` (con entrada libre de respaldo si aún no hay universidades creadas), eliminando nombres ficticios hardcodeados.
- **`src/components/NewsPage.tsx`:** componente auxiliar `NewsImage` con estado `failed` reiniciado por `src` que, ante `onError`, renderiza el bloque placeholder `<NewspaperIcon />` en tarjetas y omite limpiamente la etiqueta `<img>` en `NewsDialog` sin dejar cajas vacías en blanco.
- **`vercel.json`:** reemplaza el rewrite circular por `"cleanUrls": true` y cabeceras HTTP de seguridad (`X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-Frame-Options: DENY`).

---

## 4. Mapa de Roles y Propiedad de Archivos por Oleada

Alineado con los roles oficiales de [2026-09-06-agent-roles.md](2026-09-06-agent-roles.md) (`collector`, `backend`, `frontend`, `qa`, `coordinator`) y el límite máximo de 3 trabajadores simultáneos de [AGENTS.md](../../../AGENTS.md):

| Oleada | Tarea | Rol oficial | Archivos de propiedad exclusiva |
| :--- | :--- | :--- | :--- |
| **Oleada 1** | `Task 1` | `collector` | `collector/http.py`, `collector/browser.py`, `collector/__main__.py`, `scripts/windows/run-collector.ps1`, `tests/unit/test_http_policy.py`, `tests/integration/test_browser_fetch.py` |
| **Oleada 1** | `Task 2` | `backend` *(datos)* | `backend/scripts/backfill_media_bytes.py`, `backend/scripts/migrate_to_postgres.py`, `tests/integration/test_legacy_db_cutover.py` |
| **Oleada 1** | `Task 3` | `frontend` | `src/components/AdminPanel.tsx`, `src/components/NewsPage.tsx`, `vercel.json`, `tests/e2e/public-news.spec.ts`, `tests/e2e/admin-collection.spec.ts` |
| **Oleada 2** | `Task 4` | `backend` *(API/RAG)* | `backend/rag/chat_guard.py`, `backend/rag/news_assistant.py`, `backend/routers/chat.py`, `backend/routers/news.py`, `backend/routers/admin.py`, `backend/services/ingestion.py`, `backend/services/media.py`, `tests/unit/test_chat_guard.py`, `tests/integration/test_chat.py` |
| **Oleada 3** | `Task 5` | `qa` | `tests/integration/test_production_readiness.py`, `docs/acceptance/production.md`, `docs/context-deploy.md`, `.env.example`, `backend/.env.example`, `collector/.env.example` |
| **Oleada 4** | `Task 6` | `coordinator` | Auditoría final de contratos, integración de commits atómicos por rol sobre `backend-webscrapper` (excluyendo `skills-lock.json` y `.agents/skills/*`) y verificación de paquete de cutover. |
