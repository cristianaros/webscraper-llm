# Optimización Radical UniNews Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar todo el código y componentes huérfanos del frontend y backend, optimizar la inferencia y latencia del extractor OpenRouter y compactar el contexto del asistente RAG para maximizar el rendimiento general del proyecto.

**Architecture:** Poda selectiva y quirúrgica de archivos muertos en `src/components/ui/` y `backend/`, acotamiento de parámetros de inferencia (`max_tokens: 512`, prompt cacheado en memoria) en `collector/openrouter.py` y optimización de ventanas de texto en `backend/rag/news_assistant.py`, manteniendo el modelo libre `nvidia/nemotron-3.5-super-vl:free` y pasando la suite completa de 104+ tests.

**Tech Stack:** Astro 6, React 19, FastAPI, PostgreSQL / SQLite, Python 3.14, OpenRouter HTTP client, Pytest.

**Spec:** `docs/superpowers/specs/2026-11-01-optimizacion-radical-uninews-design.md`

## Global Constraints

- Modelo LLM: exactamente `nvidia/nemotron-3.5-super-vl:free` con precio máximo cero (`{"prompt": 0, "completion": 0}`).
- Preservar los contratos públicos de API (`/api/news/`, `/api/collector/articles`, `/api/chat/`, `/api/admin/`).
- No modificar el archivo `.env` ni exponer ningún secreto en commits, logs o código.
- No alterar dependencias en `package.json` para no romper la compatibilidad con herramientas UI.

## Review Focus

1. **Astro typecheck post-poda de componentes:** Verificar que ningún archivo en `src/` mantenga imports huérfanos hacia `sidebar`, `navigation-menu`, `sheet`, `tooltip` o `use-mobile`.
2. **FastAPI startup sin el router scraper:** Verificar que `create_app()` inicializa limpiamente sin intentar registrar `routers.scraper`.
3. **Payload del Extractor:** Verificar que `extraction_payload(doc, prompt)` contiene `"max_tokens": 512` y que la selección de bloques es parseada íntegramente.
4. **Preservar marcadores del prompt RAG:** Verificar que `prepare_context()` mantiene intactas las secciones `[NOTICIA EN FOCO]`, `[ANTECEDENTES RELACIONADOS DEL ARCHIVO]` y `[CATÁLOGO RECIENTE DEL PORTAL]`.
5. **Retrocompatibilidad de importación:** Verificar que importar `MiniMaxExtractor` desde `collector.openrouter` sigue funcionando a través del alias hacia `OpenRouterExtractor`.

---

### Task 1: Poda de componentes huérfanos en Frontend

**Files:**
- Delete:
  - `src/components/ui/sidebar.tsx`
  - `src/components/ui/navigation-menu.tsx`
  - `src/components/ui/sheet.tsx`
  - `src/components/ui/tooltip.tsx`
  - `src/hooks/use-mobile.ts`

**Interfaces:**
- Consumes: Ninguna dependencia activa en `src/pages/` o `src/components/`.
- Produces: Árbol de código frontend limpio y compilable.

- [ ] **Step 1: Verificar que ningún componente activo importe los archivos a eliminar**

Ejecutar búsqueda para asegurar cero referencias:
```powershell
.\.venv\Scripts\python.exe -c "import pathlib; [print(p) for p in pathlib.Path('src').rglob('*') if p.suffix in ('.tsx', '.ts', '.astro') and any(k in p.read_text(encoding='utf-8') for k in ('ui/sidebar', 'ui/navigation-menu', 'use-mobile')) and p.name not in ('sidebar.tsx', 'navigation-menu.tsx', 'sheet.tsx', 'tooltip.tsx', 'use-mobile.ts')]"
```
Resultado esperado: Ningún archivo listado.

- [ ] **Step 2: Eliminar los 5 archivos huérfanos**

Eliminar:
- `src/components/ui/sidebar.tsx`
- `src/components/ui/navigation-menu.tsx`
- `src/components/ui/sheet.tsx`
- `src/components/ui/tooltip.tsx`
- `src/hooks/use-mobile.ts`

- [ ] **Step 3: Ejecutar verificación estática y compilación de Astro**

Run: `npm run lint; if ($LASTEXITCODE -eq 0) { npm run typecheck }; if ($LASTEXITCODE -eq 0) { npm run build }`
Resultado esperado: `0 errors, 0 warnings`, `3 page(s) built`, exit 0.

- [ ] **Step 4: Commit**

```bash
git add src/components/ui/sidebar.tsx src/components/ui/navigation-menu.tsx src/components/ui/sheet.tsx src/components/ui/tooltip.tsx src/hooks/use-mobile.ts
git commit -m "chore(web): remove unused shadcn ui components"
```

---

### Task 2: Poda de módulos y routers legados en Backend

**Files:**
- Delete:
  - `backend/sample_data.py`
  - `backend/rag/engine.py`
  - `backend/services/gcs_media.py`
  - `backend/scripts/seed_chilean_universities.py`
  - `backend/scripts/reindex_published.py`
  - `backend/routers/scraper.py`
  - `tests/integration/test_gcs_media.py`
- Modify:
  - `backend/main.py:10,20` (eliminar import y registro del router `scraper`)

**Interfaces:**
- Consumes: `backend/main.py`
- Produces: Inicialización de FastAPI sin endpoints 410 obsoletos ni dependencias de ChromaDB/GCS.

- [ ] **Step 1: Modificar `backend/main.py` para desregistrar el router `scraper`**

En `backend/main.py`:
- Línea 10: cambiar `from routers import news, sources, admin, collector, media, scraper, chat` por `from routers import news, sources, admin, collector, media, chat`.
- Línea 20: cambiar `for r in (news.router,sources.router,admin.router,collector.router,media.router,scraper.router,chat.router): app.include_router(r)` por `for r in (news.router,sources.router,admin.router,collector.router,media.router,chat.router): app.include_router(r)`.

- [ ] **Step 2: Eliminar los 7 archivos legados**

Eliminar:
- `backend/sample_data.py`
- `backend/rag/engine.py`
- `backend/services/gcs_media.py`
- `backend/scripts/seed_chilean_universities.py`
- `backend/scripts/reindex_published.py`
- `backend/routers/scraper.py`
- `tests/integration/test_gcs_media.py`

- [ ] **Step 3: Ejecutar suite de pruebas de backend para verificar estabilidad**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_news_search.py tests/integration/test_sources_api.py -v`
Resultado esperado: Todos los tests pasan con éxito.

- [ ] **Step 4: Commit**

```bash
git add backend/main.py backend/sample_data.py backend/rag/engine.py backend/services/gcs_media.py backend/scripts/seed_chilean_universities.py backend/scripts/reindex_published.py backend/routers/scraper.py tests/integration/test_gcs_media.py
git commit -m "chore(backend): remove legacy chroma, gcs, sample data, and retired scraper router"
```

---

### Task 3: Optimización del Extractor OpenRouter (Caching de Prompt y Reducción de Max Tokens)

**Files:**
- Modify:
  - `collector/openrouter.py:15-28`
  - `collector/pipeline.py:9,14`
- Test:
  - `tests/unit/test_openrouter_extraction.py`

**Interfaces:**
- Consumes: `collector/prompts/extract-v1.txt`
- Produces: `OpenRouterExtractor`, alias `MiniMaxExtractor = OpenRouterExtractor`, `extraction_payload` con `"max_tokens": 512`.

- [ ] **Step 1: Escribir test que verifique el payload optimizado y el alias de compatibilidad**

En `tests/unit/test_openrouter_extraction.py`, asegurar que se prueba:
1. `extraction_payload(doc, prompt)["max_tokens"] == 512`.
2. `OpenRouterExtractor` y `MiniMaxExtractor` son la misma clase y funcionan idénticamente.

- [ ] **Step 2: Ejecutar test para comprobar fallo o ausencia de `OpenRouterExtractor`**

Run: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_openrouter_extraction.py -v`
Resultado esperado: Falla por falta de `OpenRouterExtractor` o max_tokens == 2048.

- [ ] **Step 3: Implementar optimizaciones en `collector/openrouter.py`**

- Cachear el contenido de `extract-v1.txt` en una variable de módulo `_EXTRACT_PROMPT` cargada una sola vez.
- En `extraction_payload`: cambiar `"max_tokens": 2048` a `"max_tokens": 512`.
- Renombrar `class MiniMaxExtractor:` a `class OpenRouterExtractor:`.
- Agregar al final del módulo el alias: `MiniMaxExtractor = OpenRouterExtractor`.
- En `collector/pipeline.py`: actualizar la importación para usar `OpenRouterExtractor`.

- [ ] **Step 4: Ejecutar tests del extractor y doctor CLI**

Run: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_openrouter_extraction.py -v; .\.venv\Scripts\python.exe -m collector doctor`
Resultado esperado: PASS y `doctor: configuration valid`.

- [ ] **Step 5: Commit**

```bash
git add collector/openrouter.py collector/pipeline.py tests/unit/test_openrouter_extraction.py
git commit -m "perf(collector): cache extraction prompt, tune max_tokens to 512, and rename extractor class"
```

---

### Task 4: Optimización del Asistente RAG (Ventanas de Contexto y Catálogo)

**Files:**
- Modify:
  - `backend/rag/news_assistant.py:58,75,78,91`
- Test:
  - `tests/integration/test_chat.py`
  - `tests/integration/test_production_readiness.py`

**Interfaces:**
- Consumes: `NewsAssistant`
- Produces: Contexto optimizado con menor consumo de tokens y generación más rápida.

- [ ] **Step 1: Ajustar parámetros de contexto en `backend/rag/news_assistant.py`**

- En `prepare_context`:
  - Línea 58: cambiar `.limit(30)` por `.limit(15)`.
  - Línea 75: cambiar `(selected.content or "")[:8000]` por `(selected.content or "")[:4000]`.
  - Línea 78: cambiar `(n.content or "")[:2500]` por `(n.content or "")[:1500]`.
  - Línea 91: cambiar `(n.content or "")[:4500]` por `(n.content or "")[:2500]`.

- [ ] **Step 2: Ejecutar tests de chat e integración para asegurar consistencia de contratos**

Run: `.\.venv\Scripts\python.exe -m pytest tests/integration/test_chat.py tests/integration/test_production_readiness.py -v`
Resultado esperado: Todos los tests pasan al 100%.

- [ ] **Step 3: Commit**

```bash
git add backend/rag/news_assistant.py
git commit -m "perf(chat): compact retrieval context and limit catalog size for lower LLM latency"
```

---

### Task 5: Verificación Integral de Regresión y Aceptación Final

**Files:**
- Verify: Todos los módulos del repositorio.

- [ ] **Step 1: Ejecutar la suite completa de tests de Python**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Resultado esperado: `104 passed, 3 deselected` (cero fallos).

- [ ] **Step 2: Ejecutar suite de frontend (lint, types, build)**

Run: `npm run lint; if ($LASTEXITCODE -eq 0) { npm run typecheck }; if ($LASTEXITCODE -eq 0) { npm run build }`
Resultado esperado: `0 errors, 0 warnings` y compilación estática completada en `dist/`.

- [ ] **Step 3: Ejecutar verificación de salud del recolector**

Run: `.\.venv\Scripts\python.exe -m collector doctor`
Resultado esperado: `doctor: configuration valid`.

- [ ] **Step 4: Comprobar estado limpio de Git**

Run: `git status --short`
Resultado esperado: Ningún archivo sin rastrear imprevisto y `.env` firmemente ignorado.
