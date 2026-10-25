# Asistente de noticias local Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir preguntas reales sobre noticias publicadas desde la página `/chat` de UniNews.

**Architecture:** FastAPI registra `/api/chat` y usa la base operacional como fuente de recuperación, filtrando siempre por `publication_status=published`. La respuesta se genera por OpenRouter con el modelo gratuito vigente. Consultar la base directamente evita un índice Chroma vacío o desactualizado y no requiere descargar modelos de embeddings para la prueba local.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite local, HTTPX, Astro/React, pytest MockTransport.

**Spec:** `docs/superpowers/specs/2026-09-06-uninews-python-openrouter.md` y enmienda del modelo en `docs/superpowers/plans/2026-10-25-recuperar-extraccion-local.md`.

## Global Constraints

- Consultar solo noticias publicadas, nunca borradores ni archivadas.
- Usar `nvidia/nemotron-3.5-super-vl:free` con precio máximo cero; no enviar claves al frontend.
- Limitar número y longitud de artículos enviados como contexto; indicar cuando no hay evidencia.
- Pruebas sin llamadas reales a OpenRouter; una prueba manual local puede usar la clave existente.
- No modificar la cola del recolector ni la base original para activar el chat.

## Archivos

- `backend/config.py`: leer configuración y secreto del backend desde `backend/.env` o variables de entorno.
- `backend/rag/openrouter.py`: cliente de chat configurado con el modelo gratuito y límites de precio.
- `backend/rag/news_assistant.py`: recuperación de noticias publicadas y construcción del contexto.
- `backend/routers/chat.py`, `backend/main.py`: rutas, estado y dependencia del asistente.
- `backend/schemas.py`: límite de longitud de la pregunta.
- `backend/.env.example`: configuración documentada.
- `src/components/ChatInterface.tsx`, `src/pages/chat.astro`: mensajes de estado acordes con el funcionamiento real.
- `tests/integration/test_chat.py`, `tests/unit/test_chat_openrouter.py`: comportamiento de visibilidad, rutas, contexto y llamadas al proveedor.

### Task 1: Rutas y recuperación

- [x] Escribir pruebas de rutas y de exclusión de noticias no publicadas.
- [x] Implementar consulta acotada y registro del router.
- [x] Ejecutar las pruebas focalizadas.

### Task 2: OpenRouter y configuración

- [x] Probar con MockTransport el modelo autorizado y el límite de precio cero.
- [x] Configurar el cliente desde `BackendSettings`, sin secretos en respuestas ni logs.
- [x] Ejecutar las pruebas focalizadas.

### Task 3: Prueba local visible

- [x] Activar el asistente en la API local con la clave ya configurada.
- [x] Verificar `/api/chat/status` y una pregunta sobre la noticia publicada.
- [x] Verificar el resultado en la página `/chat` y dejar documentadas las limitaciones.

## Resultado local

- API reiniciada desde cero: `/api/chat/status` devolvió `ok`, 1 noticia disponible y el modelo gratuito configurado; una pregunta real sobre la noticia publicada devolvió HTTP 200 y una fuente.
- La página `/chat` mostró la respuesta y el enlace a la noticia original.
- `pytest -q`: 54 aprobadas, 1 excluida por la configuración habitual; `npm run build`: correcto; `npm run lint`: sin errores, 1 advertencia preexistente.
- `npm run typecheck` sigue fallando en archivos E2E preexistentes porque faltan `@playwright/test` y `@types/node`.
- La recuperación actual puntúa coincidencias de palabras en noticias publicadas de la base operacional. No usa el índice Chroma legado. La base local contiene solo una noticia publicada y la continuidad del recolector requiere configurar su entrega a esta API y ejecutarlo por separado.
