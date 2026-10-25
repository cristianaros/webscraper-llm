# Fuentes universitarias de DatosLab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans para ejecutar este plan por tareas. Esta ejecución se realiza en la sesión actual, sin despachar agentes.

**Goal:** Extraer noticias de las 21 universidades que figuran en `https://uninews.datoslab.cl/universidades/`, conservando la institución asignada, el texto y la fecha de la fuente original.

**Architecture:** La página de DatosLab define una lista fija y revisada de universidades. Cada perfil `/universidad/<sigla>` sirve para descubrir enlaces `/detalle/<id>`; estos redirigen al portal institucional. El recolector solo acepta los hosts configurados por universidad, descarga la noticia original y la entrega a la API existente. La cola nueva se aísla de la cola histórica porque sus IDs de fuente pertenecen a otra base operacional.

**Tech Stack:** Python, HTTPX, BeautifulSoup, SQLAlchemy, SQLite, pytest. Playwright solo para fuentes cuyo perfil requiera renderizado dinámico; la muestra actual entrega HTML estático.

**References:** [directorio](https://uninews.datoslab.cl/universidades/), [especificación funcional](../specs/2026-09-06-uninews-python-openrouter.md), [recuperación de extracción local](2026-10-25-recuperar-extraccion-local.md).

## Límites

- Los 21 nombres y siglas se congelan en un catálogo revisado; un cambio futuro del directorio no activa universidades automáticamente.
- La URL final de cada noticia debe permanecer en el host institucional configurado para esa universidad. Un desvío fuera de esa lista queda bloqueado.
- No se usa la fecha de descarga como fecha de publicación. La fecha debe estar en HTML original, por ejemplo en `time[datetime]` o `meta[property="article:published_time"]`.
- Las fuentes se registran de forma idempotente. Solo una muestra con título, cuerpo y fecha verificables se habilita; la publicación automática requiere validación explícita del perfil.
- Se conserva `data/collector/collector.db`. La nueva cola usa otra carpeta y se respalda la base operacional antes de registrar fuentes.
- Las pruebas habituales usan fixtures y MockTransport, sin OpenRouter ni universidades reales.

## Archivos

- Crear `backend/scripts/datoslab_catalog.py`: catálogo fijo de 21 universidades, perfiles y hosts institucionales.
- Crear `backend/scripts/register_datoslab_sources.py`: registro idempotente en la base operacional y resumen de cambios.
- Modificar `collector/documents.py`: aceptar evidencia de fecha de publicación en la etiqueta `meta`.
- Crear `tests/unit/test_datoslab_catalog.py`: catálogo cerrado, perfil único y host por universidad.
- Crear `tests/unit/test_documents_publication_meta.py`: evidencia y materialización de fecha sin fabricarla.
- Crear `docs/acceptance/datoslab-sources.md`: resultado por fuente del piloto real, con fallos visibles.
- Configurar solo archivos `.env` ignorados y datos locales para apuntar a la API actual y a una cola nueva.

## Tarea 1: catálogo cerrado y fuentes

- [x] Guardar los 21 pares nombre/sigla del directorio y los hosts de redirección observados. Cada `start_url` es `https://uninews.datoslab.cl/universidad/<sigla>` y el patrón de artículos limita `/detalle/<id>`.
- [x] Probar que no hay siglas duplicadas, que los hosts son específicos y que el catálogo contiene exactamente las 21 universidades del directorio.
- [x] Registrar universidades/fuentes sin duplicar los registros existentes; dejar inactivas las fuentes sin muestra verificada.
- [x] Ensayar el importador sobre una base temporal y volver a ejecutarlo para comprobar idempotencia.

## Tarea 2: fecha original y extracción segura

- [x] Escribir un test con HTML que contiene `meta[property="article:published_time"]` y párrafos de artículo: el bloque de fecha conserva el atributo `content` y la fecha resultante es la original.
- [x] Modificar `build_document` solo para leer fecha de la etiqueta meta si no existe `time` o un selector específico de fecha.
- [x] Ejecutar el test focalizado y la suite Python; verificar que el texto original y el hash siguen estables.

## Tarea 3: piloto local y conexión

- [x] Respaldar la base API y mantener intacta la cola histórica. Configurar `COLLECTOR_API_URL=http://127.0.0.1:8765` y un directorio de cola nuevo.
- [x] Muestrear cada perfil y su primer artículo usando el `HttpFetcher` real, con pausas, `robots.txt` y hosts permitidos. Registrar por universidad HTTP, título, fecha, longitud de cuerpo y causa concreta de fallo.
- [x] Habilitar las fuentes con muestra verificable; ejecutar `run-once` con presupuesto acotado y registrar entregas publicadas o pendientes. Comprobar al menos una noticia nueva en la API y la web.
- [x] Documentar en `docs/acceptance/datoslab-sources.md` qué fuentes funcionan, cuáles no y qué ajustes faltan, sin afirmar cobertura completa a partir de un solo artículo.
