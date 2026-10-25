# Recuperar extracción local Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reprocesar documentos reales tras la baja del modelo gratuito original y mostrar una noticia revisada en la web local.

**Architecture:** El recolector mantiene un único modelo de extracción gratuito por OpenRouter. La cola conserva los documentos descargados y archiva las entregas fallidas antes de volver a la etapa LLM. El backend recibe una nueva revisión de extracción y el editor decide si publica una noticia con evidencia suficiente.

**Tech Stack:** Python, Pydantic, HTTPX, SQLite, FastAPI, Astro.

**Spec:** `docs/superpowers/specs/2026-09-06-uninews-python-openrouter.md` (U02 sustituido por autorización explícita del usuario del 25-10-2026).

## Global Constraints

- Único modelo activo: `nvidia/nemotron-3.5-super-vl:free` por OpenRouter; límite de precio cero para prompt y completion.
- Sin modelos de pago, datos ficticios, fechas inventadas ni lectura de fuentes fuera de la configuración.
- Persistir el documento y la selección antes de entregar; conservar las revisiones e impedir duplicados o pérdida de ediciones humanas.
- Los 30 payloads preparados con el modelo anterior se archivan antes de reprocesar, y la recuperación exige copia SQLite verificada.
- Una fuente con contenedor no validado pasa a revisión editorial; no se publica automáticamente.
- Pruebas habituales con MockTransport, sin llamadas a servicios externos.

## Propuesta de cambio de contrato

Autorización: el usuario eligió «Autorizar un cambio de modelo para la extracción» después de comprobar que `minimax/minimax-m3:free` responde 404. Cambiar `shared.contracts.FREE_MODEL` y la configuración del recolector al modelo gratuito comprobado. `Delivery.model` seguirá aceptando el identificador anterior únicamente para leer entregas históricas; la nueva extracción solo emitirá el modelo nuevo. Las nuevas entregas usan `prompt_version=extract-v2` para distinguir revisiones del mismo documento en el backend. El modelo RAG y las dependencias pertenecen a otro flujo.

Hallazgo durante la prueba real: `dateparser` interpreta `2026-10-09` como 10 de septiembre al forzar orden DMY. Se añade al alcance `shared/validation.py` para analizar fechas ISO de manera explícita antes del formato local y evitar publicaciones con fecha equivocada.

Hallazgo al mostrar la primera noticia: el esquema creado por Alembic no define un valor por defecto para `news.created_at`, por lo que una publicación editorial nueva causa error 500 en la API pública. Se añaden `backend/services/ingestion.py` y una migración aditiva `0005` que rellena únicamente los valores nulos en bases existentes. La migración se ensaya sobre copia.

## Archivos

- `shared/contracts.py`: modelo activo y lectura histórica de entregas.
- `shared/validation.py`: fechas ISO inequívocas.
- `collector/config.py` (consume el contrato), `collector/.env.example`, `collector/openrouter.py`, `collector/pipeline.py`: configuración, solicitud gratuita y nueva revisión.
- `collector/store.py`, `collector/__main__.py`: recuperación con archivo de payloads y copia obligatoria.
- `backend/services/ingestion.py`, `backend/migrations/versions/0005_news_created_at.py`: fecha de creación explícita y reparación de filas históricas nulas.
- `tests/unit/test_openrouter_extraction.py`, `tests/integration/test_collector_store.py`, pruebas de contratos: comportamiento del modelo y recuperación.

### Task 1: Modelo gratuito y revisiones

- [x] Añadir pruebas que comprueben modelo, precio cero, razonamiento desactivado y espera ante 404.
- [x] Actualizar contrato/configuración/pipeline sin cambiar datos históricos.
- [x] Ejecutar pruebas focalizadas y resolver fallos.

### Task 2: Recuperación de la cola

- [x] Añadir prueba de archivo y reencolado solo para entregas no confirmadas con error de modelo.
- [x] Implementar comando explícito que exige una copia SQLite verificada antes de cambiar la cola.
- [x] Ejecutar pruebas de cola e integración.

### Task 3: Verificación real local

- [x] Crear copia del SQLite del recolector y comprobar integridad.
- [x] Reprocesar un documento real con OpenRouter, conservar selección y entregar a la API local.
- [x] Revisar título, cuerpo, fecha y origen; publicar localmente solo si la evidencia lo respalda.
- [x] Corregir con prueba de comportamiento la interpretación de fechas ISO detectada en la prueba real.
- [x] Comprobar API pública tras aprobación y reparar `created_at` sin borrar noticias existentes.
- [x] Verificar API y Astro, registrar límites y configuración pendiente.

## Resultado local y límites

- Una noticia institucional de la Universidad de Chile aparece en la portada local con fecha 09-10-2026 y 10 bloques del cuerpo original.
- La cola original archivó 30 entregas fallidas y reencoló sus documentos; el backup verificado está en `data/collector/backups/`.
- La API de demostración usa una base SQLite temporal y dos fuentes locales; no sustituye la base operacional definitiva.
- Las otras fuentes aún requieren selectores de contenido validados. Una segunda llamada real al modelo devolvió selección inválida y quedó pendiente de revisión; los servicios gratuitos pueden imponer cuotas.
- La suite completa tuvo 50 pruebas aprobadas y una falla ajena a este cambio en `tests/integration/test_browser_fetch.py`, que construye una fuente de navegador sin `wait_selector` obligatorio.
