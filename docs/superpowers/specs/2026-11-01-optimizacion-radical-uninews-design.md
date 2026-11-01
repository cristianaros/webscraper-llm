# Diseño Técnico: Optimización Radical de UniNews (Página, Extractor y LLM)

- **Fecha:** 2026-11-01
- **Estado:** Propuesto (aprobación solicitada)
- **Autor:** Antigravity & Usuario
- **Ruta:** `docs/superpowers/specs/2026-11-01-optimizacion-radical-uninews-design.md`

---

## 1. Contexto e Intención

UniNews ha completado las fases de estabilización de su arquitectura de producción (Vercel para Astro estático, Railway para FastAPI y PostgreSQL con almacenamiento nativo de imágenes, y Windows Task Scheduler para el recolector independiente).

Con la arquitectura validada, el proyecto acumuló componentes huérfanos de UI (shadcn), módulos legados que fueron reemplazados en pasos previos (mock data, ChromaDB, GCS, seeders obsoletos) y márgenes de optimización en los pipelines de inferencia del LLM (`nvidia/nemotron-3.5-super-vl:free`), que ralentizan la respuesta o consumen cuotas innecesarias.

El objetivo de esta intervención es **optimizar el proyecto al máximo**, purgando código muerto y ajustando parámetros de inferencia, memoria y contexto para una respuesta instantánea y mínimo footprint de recursos.

---

## 2. Enfoques Considerados y Selección

### Enfoque 1: Poda Total de Código Muerto + Aceleración LLM/Extractor/Web (Seleccionado)
- Eliminar de raíz componentes huérfanos de UI en `src/components/ui/` (`sidebar.tsx`, `navigation-menu.tsx`, `sheet.tsx`, `tooltip.tsx`, `use-mobile.ts`).
- Eliminar archivos Python y tests muertos en backend: `backend/sample_data.py` (40 KB de datos falsos), `backend/rag/engine.py` (ChromaDB legado), `backend/services/gcs_media.py` (GCS reemplazado por PostgreSQL), `backend/scripts/seed_chilean_universities.py` y el router retirado `backend/routers/scraper.py`.
- Optimizar el extractor Windows: cachear en memoria el prompt de extracción para evitar I/O por artículo; reducir `max_tokens` de 2048 a 512 en `collector/openrouter.py`; renombrar la clase `MiniMaxExtractor` a `OpenRouterExtractor` (manteniendo alias de retrocompatibilidad).
- Optimizar el asistente RAG: compactar el contexto de noticias previas y catálogo para acelerar la generación de respuestas en Nemotron y evitar timeouts.
- **Razón de selección:** Maximiza la velocidad de ejecución y reduce la deuda técnica a cero sin alterar la integridad de `package.json` ni los lockfiles.

### Enfoque 2: Enfoque 1 + Purgado de Dependencias de Terceros
- Agrega a lo anterior la desinstalación de librerías en `package.json` asociadas a componentes no usados.
- **Razón de descarte:** Riesgo de fricción con herramientas CLI (`shadcn-ui`) si en el futuro se requieren componentes auxiliares, con ganancia marginal frente a la poda directa de archivos.

---

## 3. Metas, No-Metas y Anti-Metas

### Metas (Goals)
1. **Reducción de bundle y árbol de código frontend:** Eliminar más de 35 KB de código UI no utilizado que se instaló por defecto.
2. **Reducción de huella backend:** Eliminar más de 55 KB de código y scripts legados (`sample_data.py`, `engine.py`, `gcs_media.py`, `seed_chilean_universities.py`, `reindex_published.py`, `routers/scraper.py`).
3. **Aceleración del Extractor:**
   - Evitar lectura sincrónica de disco del archivo de prompt en cada llamada.
   - Reducir `max_tokens` de 2048 a 512 en `collector/openrouter.py`, recortando a la mitad el tiempo de espera por llamada en OpenRouter sin truncar la respuesta (el JSON de selección con summary < 500 caracteres ocupa < 350 tokens).
4. **Aceleración del Asistente de Noticias (RAG):**
   - Limitar el corte de texto del artículo principal en foco a 4.000 caracteres (suficiente para noticias universitarias) y el de noticias relacionadas a 1.500 caracteres.
   - Limitar el catálogo reciente en el prompt a las 15 noticias más recientes en vez de 30.
5. **Verificación total:** Todos los tests de backend y de integración (105+ tests) deben continuar pasando (`pytest -q`), y la web debe compilar sin advertencias ni errores (`lint`, `typecheck`, `build`).

### No-Metas (Non-Goals)
- No cambiar el modelo LLM activo: se mantiene exactamente `nvidia/nemotron-3.5-super-vl:free` con precio máximo cero.
- No alterar los esquemas de bases de datos existentes ni generar migraciones destructivas.

### Anti-Metas (Anti-Goals)
- No alterar los contratos públicos de la API (`/api/news/`, `/api/collector/articles`, `/api/chat/`, `/api/admin/`).
- No tocar `.env` ni exponer secretos.
- No dejar imports rotos ni referencias colgantes tras borrar archivos huérfanos.

---

## 4. Plan de Cambios Detallado por Componente

### A. Frontend (`src/`)
- **Archivos a eliminar:**
  - `src/components/ui/sidebar.tsx` (22.3 KB)
  - `src/components/ui/navigation-menu.tsx` (7.5 KB)
  - `src/components/ui/sheet.tsx` (4.5 KB)
  - `src/components/ui/tooltip.tsx` (2.8 KB)
  - `src/hooks/use-mobile.ts` (0.6 KB)
- **Verificación:** Ejecutar `npm run typecheck`, `npm run lint` y `npm run build` para garantizar que ningún componente o página los requiera.

### B. Backend (`backend/`)
- **Archivos a eliminar:**
  - `backend/sample_data.py` (40 KB de mock)
  - `backend/rag/engine.py` (6.1 KB de ChromaDB legado)
  - `backend/services/gcs_media.py` (1.7 KB de Google Cloud Storage)
  - `backend/scripts/seed_chilean_universities.py` (3.7 KB de seeder legado)
  - `backend/scripts/reindex_published.py` (1.4 KB de reindexador de ChromaDB)
  - `backend/routers/scraper.py` (0.2 KB del endpoint obsoleto `/api/scrape/upla`)
  - `tests/integration/test_gcs_media.py` (test del módulo GCS eliminado)
- **Archivos a ajustar:**
  - `backend/main.py`: retirar la importación de `scraper.router` y su `app.include_router(scraper.router)`.

### C. Extractor de Noticias (`collector/`)
- **Archivos a ajustar:**
  - `collector/openrouter.py`:
    - Cachear el contenido de `extract-v1.txt` a nivel de módulo o método lazy thread-safe.
    - Cambiar `"max_tokens": 2048` por `"max_tokens": 512` en `extraction_payload`.
    - Renombrar la clase `MiniMaxExtractor` a `OpenRouterExtractor`, conservando un alias `MiniMaxExtractor = OpenRouterExtractor` para mantener retrocompatibilidad total con tests e invocaciones previas.
  - `collector/pipeline.py`: usar `OpenRouterExtractor`.

### D. Asistente RAG (`backend/rag/news_assistant.py`)
- **Ajustes:**
  - `prepare_context`:
    - Reducir el límite de catálogo reciente de 30 a 15 artículos.
    - Ajustar el corte de contenido de la noticia en foco de `[:8000]` a `[:4000]`.
    - Ajustar el corte de contenido de antecedentes relacionados de `[:2500]` a `[:1500]`.
    - Ajustar el corte de noticias relevantes generales de `[:4500]` a `[:2500]`.
  - Mantiene intacta la presencia de las etiquetas esperadas por los tests de producción: `[NOTICIA EN FOCO]`, `[ANTECEDENTES RELACIONADOS DEL ARCHIVO]`, `[CATÁLOGO RECIENTE DEL PORTAL]`.

---

## 5. Criterios de Aceptación y Verificación

1. `git status` muestra únicamente los archivos eliminados y los archivos optimizados.
2. `pytest -q` pasa con 100% de éxito (mínimo 104 tests activos tras retirar el test de GCS).
3. `python -m collector doctor` pasa con `configuration valid`.
4. `npm run lint` reporta 0 errores y 0 advertencias.
5. `npm run typecheck` reporta 0 errores.
6. `npm run build` completa la generación estática de las 3 rutas (`/`, `/chat`, `/admin`) en `dist/`.
