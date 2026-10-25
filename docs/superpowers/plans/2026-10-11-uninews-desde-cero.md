# UniNews desde cero — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. La existencia de roles no inicia agentes; delegar solo si el usuario lo autoriza.

**Goal:** Construir y comprobar desde un proyecto vacío una aplicación que recopile noticias de universidades configuradas, conserve su evidencia, permita revisión editorial y publique un mostrador web; después preparar su analítica y, en una fase distinta, desplegarla en la nube.

**Architecture:** Un proceso Python en Windows descubre y descarga solo fuentes configuradas, conserva documentos y entregas en SQLite local, y usa `minimax/minimax-m3:free` por OpenRouter para seleccionar evidencia y categoría. FastAPI recibe entregas idempotentes, guarda revisiones y medios originales en almacenamiento persistente, y Astro/React consulta noticias publicadas. Una outbox independiente alimenta BigQuery después de la aceptación local.

**Tech Stack:** Python 3.12 x64 objetivo; HTTPX, BeautifulSoup, feedparser, Pydantic 2, Playwright Python opcional, FastAPI, SQLAlchemy, Alembic, SQLite local; Astro 6, React 19, Node >=22.12.0; pytest, MockTransport y Playwright Test. En cloud posterior: Cloud SQL PostgreSQL, GCS, BigQuery y Cloud Run.

**Spec:** [Especificación funcional y técnica](../specs/2026-09-06-uninews-python-openrouter.md). Leer además [roles y contratos](../specs/2026-09-06-agent-roles.md), [reglas del repositorio](../../../AGENTS.md) y [protocolo de tesis](../specs/2026-10-03-uninews-tesis.md).

Fecha: 2026-10-11, America/Santiago. Estado: **plan nuevo, sin implementación ni aceptación atribuida a este documento**.

## Global Constraints

- U01: El scraper se implementará en Python y no utilizará ScrapeGraphAI ni servicios de scraping por créditos.
- U02: El único modelo del flujo de extracción será `minimax/minimax-m3:free` mediante OpenRouter; no habrá sustitución automática por modelos de pago ni ejecución de un LLM local.
- U03: El recolector se ejecutará en Windows, en una máquina diferente del servidor de la web, API y base de datos central.
- U04: Las universidades y sus enlaces serán configurados por el administrador; el recolector no incorporará universidades descubiertas por su cuenta.
- U05: Cada noticia publicable tendrá título, cuerpo original, categoría, fecha de publicación, nombre de universidad y URL de origen.
- U06: La fecha de extracción nunca se presentará como fecha de publicación; una fecha ausente o inválida impedirá la publicación automática.
- U07: Los artículos descargados y sus pendientes sobrevivirán a reinicios, falta de cuota de OpenRouter y desconexiones de la API central.
- U08: La comunicación entre recolector y servidor se realizará mediante una API autenticada por HTTPS; no se compartirá un archivo SQLite entre máquinas.
- U09: Astro consultará las noticias publicadas mediante FastAPI; ninguna clave de OpenRouter o del recolector se incluirá en el frontend.
- U10: Una entrega repetida del mismo artículo no creará noticias duplicadas ni sobrescribirá una edición humana con una revisión antigua.
- U11: El plan y su implementación conservarán los datos existentes; las migraciones y la restauración se verificarán sobre copias.
- U12: Las pruebas automatizadas habituales no realizarán llamadas a OpenRouter ni a universidades reales.
- U13: Se extraerá la imagen principal cuando exista, conservando su origen y metadatos; una imagen ausente o fallida no se reemplazará por una imagen generada.
- U14: El desarrollo y las pruebas de aplicación se completarán primero localmente, sin exigir recursos Google Cloud; la carga real de datos a BigQuery será una etapa posterior.
- U15: BigQuery almacenará datos analíticos versionados y consultables, con carga repetible y seguimiento de publicaciones, cambios y archivos; no sustituirá la base operacional de la web.
- U16: Los agentes tendrán roles, propiedad de archivos, contratos de entrega y reglas de coordinación explícitos en AGENTS.md y en la especificación de agentes.

## Cómo usar este plan

Este es el orden para una construcción **desde cero**. El checkout actual ya contiene `collector/`, `backend/`, `src/`, `analytics/`, migraciones y pruebas; no se deben borrar ni recrear para seguirlo. Si se trabaja en este repositorio, tratar cada tarea como una lista de contratos y brechas: ejecutar la prueba indicada, leer los archivos actuales y aplicar solo lo que falte. El [plan original detallado](2026-09-06-uninews-python-openrouter.md) contiene ejemplos extensos de implementación; el [plan de cierre local](2026-10-03-uninews-scraper-y-mostrador.md) identifica brechas de la versión ya existente. Los tres documentos no son evidencia de ejecución.

Los datos reales de prueba necesitan URLs de instituciones asignadas por el administrador. UPLA figura como referencia inactiva; no agregar UV, PUCV u otras por suposición. Ninguna prueba habitual debe acceder a esos sitios, OpenRouter ni GCP. Los secretos viven en `.env` ignorados y fuera de logs/capturas. Antes de una migración, hacer copia consistente y probar sobre esa copia. Ejecutar `git status --short` al iniciar cada entrega y no agregar cambios ajenos al commit.

## Mapa de archivos y contratos

| Unidad | Archivos de responsabilidad única | Interfaz pública entre unidades |
|---|---|---|
| Contratos | `shared/contracts.py`, `shared/validation.py`, `shared/urls.py` | `SourceConfig`, `Document`, `Selection`, `ArticleFields`, `Delivery`, `Receipt`, `ImageAsset`, `RunReport` |
| API y datos | `backend/models.py`, `backend/migrations/versions/`, `backend/routers/{sources,collector,news,admin,media}.py`, `backend/services/{ingestion,media,analytics_events}.py` | API autenticada de fuentes/ingesta, API pública de noticias, recibos estables |
| Recolector | `collector/{config,http,discovery,browser,documents,store,openrouter,images,sync,pipeline,__main__}.py` | `run_once(...) -> RunSummary`; cola y outbox locales |
| Web | `src/lib/{api,admin-api}.ts`, `src/components/{NewsPage,AdminPanel}.tsx`, `src/components/admin/`, `src/components/news/` | Tipos TypeScript alineados con esquemas API; ninguna llamada al LLM |
| Operación | `scripts/windows/{install-collector,run-collector,register-collector-task}.ps1`, `shared/backup.py` | CLI `doctor`, `run-once`, `status`, `retry`, `backup` |
| Analítica | `analytics/{schema,storage,exporter,bigquery_sink}.py`, `analytics/sql/`, `docs/operations/bigquery.md` | Evento con `record_version`, lote NDJSON y manifiesto por hash |
| Evaluación | `evaluation/{annotate,compare,metrics}.py`, `evaluation/schema.json`, `tests/`, `docs/acceptance/` | Corpus anotado, predicciones, métricas y evidencia AC01–AC14 |

El coordinador posee `shared/`, dependencias, locks, migraciones transversales y configuración de pruebas. Recolector, backend, frontend, cloud/analítica y QA usan las propiedades de archivo definidas en la especificación de roles. Registrar y revisar cualquier cambio de contrato antes de editar consumidores. No hay dos propietarios activos del mismo archivo.

## Fase A — producto local

### T1. Entorno reproducible y contratos

**Files:** Crear `shared/__init__.py`, `shared/contracts.py`, `shared/validation.py`, `shared/urls.py`, `pytest.ini`, `tests/conftest.py`, `tests/unit/test_contracts.py`, `requirements-dev.in`, `requirements-dev.txt`, `collector/requirements.in`, `backend/requirements.txt`, `package.json`, `package-lock.json`, `.env.example`, `backend/.env.example`, `collector/.env.example`. El administrador de dependencias genera los locks desde versiones comprobadas; no copiarlos de un ejemplo.

**Interfaces:** `SourceConfig` contiene institución, URL y hosts permitidos, revisión y selectores; `Document` contiene URL canónica, hash, HTML/bloques y captura; `Selection` solo IDs de bloques y categoría; `Delivery` contiene `delivery_id` UUID y payload inmutable.

- [ ] Escribir `test_contracts.py`: rechazar host ajeno, timezone inválida, campos extra, fecha operativa sin zona, selección de ID inexistente y modelo distinto del literal requerido; aceptar un fixture completo con universidad configurada.
- [ ] Ejecutar `python -m pytest tests/unit/test_contracts.py -q`; esperar fallo por módulos/validadores ausentes.
- [ ] Implementar modelos Pydantic con `extra="forbid"`, `MODEL = "minimax/minimax-m3:free"`, catálogo de categorías compartido, validación de URL/host y serialización estable del payload. `Delivery.model_dump_json()` debe producir los mismos bytes para un reintento guardado.
- [ ] Repetir la prueba; crear ambientes Python/Node desde archivos de dependencia y correr `npm run typecheck`. En Windows, comprobar explícitamente Python 3.12 y Node >=22.12.0; registrar otra versión si es la disponible, sin afirmar compatibilidad no probada.
- [ ] Revisar diff y hacer commit solo de estas rutas: `feat: define UniNews contracts and reproducible setup`.

### T2. Base operacional y migración segura

**Files:** Crear `backend/{config,database,models,schemas,main,security}.py`, `backend/migrations/{env.py,versions/0001_legacy_news.py,versions/0002_collection.py,versions/0003_media.py,versions/0004_analytics.py}`, `backend/alembic.ini`, `tests/integration/test_migrations.py`.

**Interfaces:** `get_session()` entrega sesión transaccional; noticias tienen `publication_status`, `published_on: date | None`, `date_precision`, `canonical_url`, `editorial_lock` y `record_version: int`. Tablas separadas conservan `news_revisions`, `ingest_receipts`, `source_versions`, `media_assets` y `analytics_outbox`.

- [ ] Escribir prueba que parte de SQLite vacío y de una copia de una base heredada con dos noticias y IDs conocidos; tras `upgrade head` deben persistir filas, IDs, fechas y ediciones. Probar que un esquema desconocido aborta sin mutar datos.
- [ ] Ejecutar `python -m pytest tests/integration/test_migrations.py -q`; observar fallo previo a migraciones.
- [ ] Implementar Alembic con constraints: unicidad `(university_id, canonical_url)` cuando haya URL; `delivery_id` único; identidad de revisión `(source_id, canonical_url, document_hash, prompt_version, source_revision)`; outbox en la transacción de cada cambio. No correr migraciones automáticamente en cada arranque API.
- [ ] Repetir pruebas; ejecutar upgrade, downgrade cuando sea seguro, y restore sobre **copias temporales**. Registrar conteos antes/después y `PRAGMA integrity_check`; no ensayar restauración sobre una base abierta.
- [ ] Commit de modelos/migraciones/pruebas con rutas explícitas: `feat: add durable operational schema`.

### T3. API de fuentes, seguridad y control editorial

**Files:** Crear `backend/routers/{sources,admin,news}.py`, `backend/services/sources.py`, `tests/integration/{test_sources_api,test_public_visibility}.py`; modificar `backend/main.py`, `backend/security.py`, `backend/schemas.py`.

**Interfaces:** Admin crea universidad/fuente y valida una muestra por revisión; collector solo lee configuración y envía datos; público solo lee `published`. Rutas de configuración y escritura requieren token admin, distinto del token collector. Un cambio de selectores incrementa `revision` e invalida `validated_revision`.

- [ ] Escribir pruebas `TestClient`: token anónimo/collector no modifica fuente, edición concurrente devuelve 409, fuente nueva nace desactivada, fuente editada pierde validación y noticia draft/archived nunca sale en listado, detalle, estadísticas o chat.
- [ ] Ejecutar `python -m pytest tests/integration/test_sources_api.py tests/integration/test_public_visibility.py -q`; esperar 404/403 o fallos de aserción.
- [ ] Implementar rutas y comprobaciones de permiso en servidor. Configurar `allowed_hosts` explícitos y rechazo de URLs privadas/redirecciones fuera de alcance. Una prueba de fuente presenta hasta tres muestras y no publica.
- [ ] Repetir pruebas, incluidas 401, 403, 409 y 422. Inspeccionar OpenAPI y comprobar que los esquemas de lectura pública no exponen revisiones ni secretos.
- [ ] Commit: `feat: manage configured sources and editorial access`.

### T4. Descubrimiento y captura con Python

**Files:** Crear `collector/{config,http,discovery,browser,documents}.py`, `tests/unit/{test_urls,test_discovery,test_documents}.py`, fixtures HTML/RSS bajo `tests/fixtures/`.

**Interfaces:** `discover(source, transport, cursor) -> DiscoveryBatch`; `fetch_document(source, url, transport) -> Document`; `extract_candidates(document, source) -> list[EvidenceBlock]`. Cada bloque tiene ID estable, texto original y ubicación en el documento.

- [ ] Escribir fixtures de RSS, HTML paginado, contenido dinámico optativo, artículo con listas/citas, fecha ausente, `dateModified` sin `datePublished`, robots denegado, redirección externa y enlaces duplicados. Testear solo URLs/hosts configurados y preservación del orden editorial.
- [ ] Ejecutar `python -m pytest tests/unit/test_urls.py tests/unit/test_discovery.py tests/unit/test_documents.py -q`; observar fallos iniciales.
- [ ] Implementar HTTPX con timeouts, límites de bytes y redirects verificados; `feedparser` recibe bytes ya descargados; Playwright solo para `render_mode=browser`, con lista de hosts y sin evasión. Descubrir RSS configurado/declarado y HTML por selectores, guardar cursor al topar `max_pages`/`max_articles`.
- [ ] Extraer título/fecha/cuerpo desde el contenedor editorial validado, conservando párrafos, listas, subtítulos y citas. Si no hay fecha verificable, guardar `published_on=None` y motivo; `fetched_at` jamás rellena ese campo.
- [ ] Repetir pruebas; añadir 304, 429/503 con `Retry-After`, ciclos de paginación y cuerpo >40 000 caracteres. Commit: `feat: capture assigned sources and evidence`.

### T5. Cola local y extracción MiniMax recuperable

**Files:** Crear `collector/{store,openrouter,pipeline}.py`, `tests/integration/{test_collector_store,test_pipeline}.py`, `tests/unit/test_openrouter_extraction.py`.

**Interfaces:** Estados `discovered → fetched → llm_wait → ready → synced`, alternativas `review`, `failed`, `blocked`. `CollectorStore` confirma documento antes de llamar al LLM, y `Selection`/`Delivery` antes de enviar. `run_once(settings, *, clock, monotonic, http_transport) -> RunSummary` procesa outbox primero, luego descubrimiento y cuotas, luego outbox.

- [ ] Escribir test que reinicia SQLite después de guardar HTML y después de guardar Delivery; la segunda ejecución no vuelve a descargar/consultar el LLM si ya hay selección y conserva mismo UUID/payload. Dos reservas concurrentes de la última llamada dejan pasar exactamente una.
- [ ] Ejecutar `python -m pytest tests/integration/test_collector_store.py tests/unit/test_openrouter_extraction.py -q`; esperar fallo por cola/extractor ausentes.
- [ ] Implementar transiciones transaccionales, `attempts`, `next_attempt_at`, caché de fuente hasta 24 h, hash de documento/prompt/revisión/modelo, cuota persistente inicial 30/día UTC, 5/minuto y concurrencia 1. Bloqueos definitivos no vuelven a `pending()` por un `NULL` de reintento.
- [ ] Enviar a OpenRouter solo el modelo literal y precio máximo cero. Pedir IDs de evidencia y categoría; Python copia el texto original. Validar JSON, IDs y `finish_reason`; ante 429 dejar `llm_wait`, ante 401/402/403 o modelo no disponible pausar LLM sin fallback. Un JSON inválido admite un reintento máximo antes de revisión.
- [ ] Repetir pruebas con `httpx.MockTransport`; cubrir 429, error HTTP 200, respuesta truncada, precio no cero, reinicio y API desconectada. Commit: `feat: persist collection stages and grounded extraction`.

### T6. Ingesta idempotente, publicación y revisión

**Files:** Crear `backend/routers/collector.py`, `backend/services/ingestion.py`, `collector/sync.py`, `tests/integration/{test_ingestion,test_public_visibility}.py`; modificar `backend/models.py`, `backend/routers/admin.py`, `backend/routers/news.py` si el contrato lo exige.

**Interfaces:** `ingest(db, delivery, now) -> Receipt` guarda recibo y revisión en una transacción; `Receipt` repetido conserva el mismo `news_id`/estado. Público: `GET /api/news/`, `GET /api/news/{id}`, filtros por `university_id`, `category`, `date_from`, `date_to`, búsqueda y paginación estable por fecha editorial/ID.

- [ ] Escribir pruebas de 100 reenvíos del mismo payload: una noticia/una revisión; payload diferente con UUID reutilizado: 409; ACK perdido: mismo recibo; revisión antigua o bloqueo editorial: conserva texto editado y deja revisión pendiente.
- [ ] Ejecutar `python -m pytest tests/integration/test_ingestion.py tests/integration/test_public_visibility.py -q`; observar fallo inicial.
- [ ] Implementar validación central de host, hashes y evidencia; publicación automática solo para revisión de fuente validada, título 5–255, cuerpo >=200, categoría del catálogo, fecha original verificable y sin bloqueo editorial. Una revisión inválida queda almacenada y visible al admin, sin reemplazar publicación anterior.
- [ ] Implementar corrección/publicación/archivo con outbox transaccional y filtros públicos por `published_on` inclusivo; 422 si `date_from > date_to`. Fecha de día se serializa `YYYY-MM-DD`, sin zona ni hora inventada.
- [ ] Repetir pruebas de concurrencia, rollback, 100 reenvíos y aislamiento público. Commit: `feat: ingest revisions and publish validated news`.

### T7. Imagen principal original y llegada tardía

**Files:** Crear `collector/images.py`, `backend/services/media.py`, `backend/routers/media.py`, `tests/unit/test_images.py`, `tests/integration/test_media_delivery.py`; modificar `collector/store.py`, `collector/pipeline.py`, `backend/models.py` y crear migración de medios si no quedó en T2.

**Interfaces:** `ImageAsset(status, original_url, sha256, content_type, width, height, byte_size, alt, credit, error_code)`; `ImageDelivery` tiene UUID independiente y hash de documento esperado; `LocalMediaStore.put(sha256, bytes)` escribe por hash; `GET /api/media/{sha256}` sirve solo medios asociados a noticia pública.

- [ ] Crear pruebas con JPEG/PNG/WebP válidos, HTML disfrazado de imagen, SVG, pixel/logo, host CDN no autorizado, ausencia, fallo temporal y entrega tardía repetida.
- [ ] Ejecutar `python -m pytest tests/unit/test_images.py tests/integration/test_media_delivery.py -q`; observar fallo inicial.
- [ ] Descubrir figura editorial, `og:image`, `NewsArticle.image` y `srcset`; resolver URL relativa y validar host en cada redirect. Limitar a 5 MiB, 40 MP y mínimo inicial 300×160; decodificar firma real y guardar hash, origen, alt y crédito presentes.
- [ ] Guardar archivo primero en Windows, luego transferir por API autenticada a almacenamiento local persistente. Distinguir `not_found`, `pending`, `failed`, `ready`; la imagen tardía actualiza la misma noticia y genera evento, sin repetir LLM. El texto válido puede publicarse mientras la imagen está pendiente.
- [ ] Repetir pruebas y verificar acceso público/privado y deduplicación por hash. Commit: `feat: preserve original news imagery`.

### T8. Mostrador y panel administrativo

**Files:** Crear `src/pages/{index,admin}.astro`, `src/components/{NewsPage,AdminPanel}.tsx`, `src/components/news/{NewsFilters,NewsDialog}.tsx`, `src/components/admin/{SourcesPanel,RunsPanel,ReviewPanel}.tsx`, `src/lib/{api,admin-api,date}.ts`, `playwright.config.ts`, `tests/e2e/{news,admin}.spec.ts`; modificar `package.json`/lock mediante propietario único.

**Interfaces:** `News` incluye `published_on: string | null`, institución configurada, categoría, cuerpo, fuente e imagen/estado opcionales. `fetchNews`/`fetchUniversities` usan URL base y AbortSignal; admin envía token solo desde memoria.

- [ ] Escribir E2E con API interceptada: error 503 muestra error y reintento sin tarjetas ficticias; filtros combinados reinician `skip=0`; borradores no se muestran; diálogo tiene foco, Escape y enlace a fuente. Mock con imagen ausente y otro con imagen real.
- [ ] Ejecutar `npm run test:e2e -- tests/e2e/news.spec.ts tests/e2e/admin.spec.ts`; observar fallo inicial.
- [ ] Implementar estados carga/vacío/error; búsqueda, universidad, categoría, rango de fechas, paginación, actualización manual y cada 60 s solo con pestaña visible. Conservar filtros y artículo abierto durante el refresco; cancelar peticiones obsoletas.
- [ ] Implementar flujo admin probar fuente → revisar muestra → validar → activar, y revisar artículo → corregir/publicar/archivar. Mostrar causas 401/409/422 y estado de cuota/imagen; no persistir token en localStorage/sessionStorage ni renderizar HTML remoto sin escape.
- [ ] Ejecutar E2E, `npm run typecheck`, `npm run lint`, `npm run build`; comprobar móvil 390 px y teclado. Commit: `feat: browse and review university news`.

### T9. Instalación Windows, observabilidad y recuperación

**Files:** Crear `collector/__main__.py`, `scripts/windows/{install-collector,run-collector,register-collector-task,test-collector-task}.ps1`, `shared/backup.py`, `tests/integration/{test_cli_recovery,test_backup}.py`, `docs/operations/windows-collector.md`.

**Interfaces:** `python -m collector doctor|run-once|status|retry --item UUID|backup --output PATH`; `register-collector-task.ps1 -DryRun` devuelve definición JSON sin registrar tarea ni pedir credenciales.

- [ ] Escribir pruebas de CLI desde otro directorio, error de configuración sin secretos, backup SQLite con WAL y medios, restauración en directorio nuevo y UUID pendientes conservados. Dry-run no debe cambiar inventario de tareas.
- [ ] Ejecutar `python -m pytest tests/integration/test_cli_recovery.py tests/integration/test_backup.py -q` y `scripts/windows/test-collector-task.ps1`; observar fallos iniciales.
- [ ] Implementar tarea cada 15 min, `IgnoreNew`, máximo interno 12 min, externo 14 min, `StartWhenAvailable`, cuenta dedicada y ejecución sin sesión. Wrapper usa rutas absolutas, bloqueo de archivo y logs JSON rotatorios sin secretos/HTML.
- [ ] Implementar retry con backoff, `Retry-After`, circuito global LLM, pausa por disco <1 GiB o cola >2 GiB y envío de outbox aun durante pausa de descargas. Backups usan API consistente de SQLite y copia de medios; restaurar solo con procesos detenidos.
- [ ] Repetir pruebas, analizar sintaxis PowerShell y registrar ensayo real de 72 h con sesión cerrada/reinicio/red cortada cuando exista máquina Windows disponible. Dry-run y tests no acreditan AC02. Commit: `ops: run and recover unattended Windows collection`.

### T10. Aceptación local y evaluación de tesis

**Files:** Crear `tests/integration/test_local_pipeline.py`, `evaluation/{annotate,compare,metrics}.py`, `evaluation/schema.json`, `evaluation/README.md`, `tests/unit/test_evaluation_metrics.py`, `docs/acceptance/local.md`.

**Interfaces:** `body_scores(gold: str, pred: str) -> dict[str,float]`; `baseline_extract(doc, source) -> ArticleFields`; `python -m evaluation.compare --corpus PATH --predictions PATH --output PATH`. La plantilla de `annotate` no es gold hasta que personas completen y validen campos.

- [ ] Escribir integración con `MockTransport`: fuente configurada → HTML guardado → selección simulada → ingesta → listado/detalle/imagen; ACK perdido, revisión nueva, edición humana y API caída. Testear métricas con dos artículos y uno omitido: cobertura 1/2, exactitud global de título 1/2.
- [ ] Ejecutar `python -m pytest tests/integration/test_local_pipeline.py tests/unit/test_evaluation_metrics.py -q`; observar fallo inicial.
- [ ] Implementar baseline determinista de título/cuerpo/fecha/categoría, anotación humana independiente, validación de IDs completos y predicciones ausentes con F1 de cuerpo cero. Registrar por artículo método, estado, versión Git, hashes, latencia, llamadas, modelo devuelto y motivo de fallo.
- [ ] Ejecutar suite Python, E2E, typecheck, lint, build y flujo real local sobre base temporal. Preparar lote NDJSON local sin GCP. Para el corpus: objetivo 60 artículos/3 universidades, 30 desarrollo/30 evaluación con semilla 20261003 y grupos duplicados juntos; congelar reglas/prompt antes del conjunto final. Un segundo anotador revisa al menos 12 cuando esté disponible.
- [ ] Documentar AC01–AC12 como `passed`, `failed` o `not_executed`, con evidencia y denominadores. Sin fuentes/URLs o anotadores reales, declarar el piloto limitado. QA independiente revisa integridad, fechas, borradores y métricas antes de cerrar aceptación. Commit: `test: document local product acceptance`.

## Fase B — datos analíticos en BigQuery, después de aceptar el producto local

### T11. Exportación local versionada y carga repetible

**Files:** Crear `analytics/{schema,storage,exporter,bigquery_sink}.py`, `analytics/sql/{news,queries}.sql`, `tests/integration/test_analytics_export.py`, `docs/operations/bigquery.md`; completar `backend/services/analytics_events.py` y migración correspondiente si no quedó en T2.

**Interfaces:** cada mutación emite `event_id`, `news_id`, `record_version` creciente, `event_at`, `operation`, `publication_status`, `is_deleted`, campos editoriales e imagen. `prepare` crea NDJSON+manifiesto con IDs/conteo/SHA-256 sin GCP; `upload` reutiliza ese lote y job ID persistido. `news_current` escoge la versión máxima por `news_id`.

- [ ] Escribir prueba fake de publicar → editar → cambiar imagen → archivar → eliminación lógica, seguida de lote entregado dos veces y ACK perdido. Esperar historial completo, una versión lógica actual y archivo fuera de `published_news`; publicación operacional sigue funcionando si la exportación falla.
- [ ] Ejecutar `python -m pytest tests/integration/test_analytics_export.py -q`; observar fallo inicial.
- [ ] Implementar outbox transaccional, manifiesto inmutable, carga GCS/BigQuery con esquema explícito y precedencia por `record_version`; parametrizar proyecto, dataset, bucket y región compatible. No escribir binarios en BigQuery ni confirmar outbox antes de verificar job.
- [ ] Repetir pruebas locales sin credenciales. Solo al pasar a esta fase, ejecutar primera carga real con credenciales de aplicación y presupuesto configurado; verificar `news_events`, `news_current` y `published_news` tras repetir lote. Registrar costes/errores reales, sin asumir gratuidad.
- [ ] Commit: `feat: export versioned news analytics`.

## Fase C — plataforma cloud, después de validar BigQuery

### T12. Persistencia cloud, despliegue y recuperación

**Files:** Crear `deploy/gcp/` (infraestructura declarativa y configuración), `tests/integration/test_postgres_migration.py`, `docs/operations/cloud.md`, `docs/acceptance/cloud.md`; adaptar `backend/database.py`, `backend/services/media.py` y configuración mediante interfaces ya probadas.

**Interfaces:** FastAPI usa Cloud SQL PostgreSQL persistente; medios en GCS privado servidos por API; recolector Windows conserva la misma API HTTPS con token collector distinto del admin. Exportador corre separado de la API. Cloud Run no conserva DB ni cola en su filesystem efímero.

- [ ] Escribir pruebas de adaptadores PostgreSQL/GCS con dobles locales y migración SQLite→PostgreSQL sobre copia: preservar IDs, revisiones, bloqueos y fechas. Probar reemplazo de instancia simulando reinicio de API sin perder datos.
- [ ] Ejecutar pruebas de adaptadores; observar fallos iniciales.
- [ ] Implementar infraestructura con secretos gestionados y cuentas de servicio de mínimo privilegio por API/exportador, conexión privada/persistente, migración explícita y rollback documentado. No poner clave JSON de servicio en repositorio ni permisos BigQuery en la API pública.
- [ ] Cuando se ejecute esta fase, aplicar en staging, migrar copia, comprobar conteos/IDs/medios y HTTPS desde Windows; luego validar instancia reemplazada y exportación repetida. Crear recursos y activar trabajos solo durante ejecución autorizada, no al redactar el plan.
- [ ] Registrar AC13–AC14 con evidencia o `not_executed`; QA independiente verifica recuperación y permisos. Commit: `ops: deploy persistent UniNews platform`.

## Puertas de salida y cobertura

| Puerta | Tareas | Evidencia mínima |
|---|---|---|
| Contratos y datos | T1–T3 | Validadores, migraciones sobre copias, tokens separados, borradores ocultos |
| Scraper y publicación | T4–T7 | Documento antes del LLM, entrega idempotente, imagen original y fecha verificable |
| Producto local | T8–T10 | Suite offline, UI integrada, backup/restore, Windows 72 h, evaluación real o límites explícitos |
| Analítica | T11 | Lote con hash y doble carga sin versión duplicada; archivos/tombstones correctos |
| Producción | T12 | Cloud SQL/GCS persistentes, HTTPS Windows→API, reemplazo de instancia y permisos mínimos |

AC01–AC12 pertenecen a la puerta local; AC13 a analítica; AC14 a coordinación y plataforma productiva. Las metas de extracción de la especificación son **metas propuestas**, no resultados: título/universidad >=95 %, fecha >=95 % donde sea verificable, F1 cuerpo >=0,95, macro-F1 categoría >=0,80 y cero hechos inventados publicados en el corpus. Informar resultados aunque no alcancen metas. No marcar un checkbox por existir código o por un informe histórico.

## Riesgos y decisiones pendientes al ejecutar

- **Fuentes y corpus:** sin lista de instituciones/URLs y revisión humana, se puede completar el producto con fixtures, pero no certificar cobertura ni AC10 multiuniversidad.
- **MiniMax gratuito:** disponibilidad, cuota y precio pueden cambiar; si no cumple el contrato, mantener documentos pendientes y mostrar causa. Cambiar modelo requiere instrucción explícita.
- **Windows:** sintaxis y dry-run no acreditan las 72 h sin sesión; reservar tiempo de observación con la máquina real.
- **Datos heredados:** el checkout actual ya contiene datos/esquemas potenciales; inventariar y copiar antes de cualquier migración o restauración.
- **Cloud:** BigQuery y despliegue tienen costes y credenciales propios; aceptación local no depende de ellos.

## Auto-revisión del plan

- [x] U01–U16 y AC01–AC14 tienen tarea y puerta de aceptación; producto local precede BigQuery y cloud.
- [x] Contratos entre recolector, API, web y analítica usan los mismos nombres y tipos principales.
- [x] Cada tarea tiene archivos, prueba inicial, implementación, comprobación y commit explícito.
- [x] No se marcaron tareas de implementación como ejecutadas ni se modificó código de aplicación.
