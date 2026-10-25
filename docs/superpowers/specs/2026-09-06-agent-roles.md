# Agentes del proyecto: responsabilidades y contratos

Estado: especificación de roles para la implementación. No se han iniciado agentes ni tareas productivas al crear este documento.

**Enmienda vigente (2026-10-25):** las menciones de MiniMax en el rol del recolector se sustituyen por el modelo gratuito de extracción `nvidia/nemotron-3.5-super-vl:free`, autorizado por el usuario.

## Coordinación y reglas comunes

Aplican [AGENTS.md](../../../AGENTS.md), la [especificación](2026-09-06-uninews-python-openrouter.md) y el [plan](../plans/2026-09-06-uninews-python-openrouter.md). Los roles son responsabilidades; pueden ejecutarse con herramientas multiagente o secuencialmente. No requieren modelos distintos ni otras suscripciones.

El coordinador asigna cada tarea con: objetivo observable, IDs de requisitos, archivos autorizados, contratos de entrada/salida, pruebas esperadas y punto de integración. Un agente que necesita otro contrato envía una propuesta concreta; no lo cambia silenciosamente. Un agente dependiente comienza cuando el contrato del anterior está integrado y comprobado.

Orden obligatorio: producto e imágenes locales → aceptación local → preparación y carga posterior a BigQuery → despliegue posterior de la plataforma cloud. El rol cloud puede implementar adaptadores y pruebas fake durante el desarrollo, pero no debe convertir un proyecto GCP real en requisito para los demás agentes.

## Roles

| Rol / nombre de tarea | Responsabilidad | Archivos de propiedad principal | Entrega obligatoria |
|---|---|---|---|
| Coordinador / `coordinator` | Arquitectura, contratos, orden de trabajo, conflictos e integración | `shared/`, `AGENTS.md`, planes/specs, configuración transversal de pruebas | Contratos coherentes, matriz de requisitos y síntesis de evidencias |
| Recolector / `collector` | Descubrimiento, HTML/RSS, browser Python, MiniMax, cola local, imágenes y Windows | `collector/`, `scripts/windows/`, fixtures/pruebas del recolector | CLI autónoma y recuperación demostrada sin consultas externas en tests |
| Backend / `backend` | Modelos, migraciones, fuentes, ingesta, publicación, revisiones, autorización y outbox analítica | `backend/`, pruebas API/migración | API con permisos, idempotencia y datos existentes conservados |
| Frontend / `frontend` | Panel de fuentes/revisión, noticias/imágenes, filtros, refresco y estados accesibles | `src/`, pruebas E2E de UI | UI usable con API real de pruebas, sin claves ni datos ficticios de respaldo |
| Cloud y analítica / `cloud_analytics` | Google Cloud, despliegue, GCS, IAM, BigQuery, jobs y consultas | `scripts/gcp/`, `analytics/`, `deploy/gcp/`, documentación cloud | Exportación local verificable primero; luego configuración cloud, carga recuperable y tablas/vistas analíticas |
| QA y tesis / `qa` | Revisión independiente, pruebas integrales, corpus y evaluación | `evaluation/`, pruebas de aceptación y reportes; lectura del resto | Hallazgos con evidencia, resultados reales y límites de generalización |

`shared/validation.py`, `shared/urls.py` y `shared/backup.py` pueden ser implementados por el rol técnico relacionado si el coordinador le cede explícitamente ese archivo durante la tarea. `backend/services/media.py` es del backend; el rol cloud define su adaptador GCS mediante contrato, sin editarlo simultáneamente. La outbox transaccional es del backend; su consumidor y el esquema BigQuery son del rol cloud. `package.json`, locks y migraciones tienen un solo propietario por turno.

## Especificación de cada agente

### Coordinador

- Entradas: requisitos del usuario, estado actual del árbol, resultados de cada rol.
- Decide: cambios de contrato, asignación de archivos y orden de integración; consulta al usuario solo cuando falta una decisión de producto necesaria que no pueda resolverse con los acuerdos existentes.
- Verifica: no se recupera ScrapeGraphAI, se mantiene MiniMax free, cola antes de red, campos/imágenes trazables y aplicación separada de analítica.
- No delega: responsabilidad de leer y reconciliar resultados ni la conclusión final de aceptación.

### Recolector

- Entradas: `SourceConfig`, contratos de documentos/imágenes, endpoints del servidor y entorno Windows.
- Produce: `Document`, `Selection`, `Delivery`, `ImageAsset`, `RunReport`; outbox local y scripts Windows.
- Límites: no escribe directamente en Cloud SQL/BigQuery; no guarda claves Google Cloud; no supone que una imagen externa/CDN está permitida si no consta en configuración.
- Pruebas: cuotas, reinicios, API caída, paginación, HTML dinámico, imagen inválida y deduplicación antes de llamadas repetidas.

### Backend

- Entradas: contratos congelados y base heredada.
- Produce: API pública/admin/collector, recibos transaccionales, historial, metadatos de imagen y eventos analíticos.
- Límites: no programa scraping en lifespan; no publica campos vacíos; no hace que un fallo de BigQuery revierta una noticia; no expone acceso administrativo por confiar solamente en la UI.
- Pruebas: duplicados/concurrencia, edición humana, rollback, visibilidad de borradores, migración SQLite→PostgreSQL y outbox con commit atómico.

### Frontend

- Entradas: OpenAPI, respuestas de ejemplo y componentes existentes.
- Produce: administración y portal público, incluido estado de imagen y actualización de datos.
- Límites: no instala otro diseño completo ni reemplaza cambios visuales concurrentes; no usa noticias ficticias al fallar la API; no llama a OpenRouter desde el navegador.
- Pruebas: teclado, móvil/escritorio, campos de error, filtros, fechas, imágenes ausentes/cargadas y token solo en memoria.

### Cloud y analítica

- Entradas: dominio/proyecto/región configurados, imagen de contenedor probada, contrato de evento analítico.
- Produce: infraestructura como código, Cloud Run/Cloud SQL/GCS, secretos/IAM, job exportador, esquema BigQuery, vistas y consultas.
- Límites: no usa claves JSON permanentes cuando puede usar identidad de servicio; no pone SQLite de producción en Cloud Run; no activa recursos ni facturación durante una tarea de planificación.
- Pruebas: plan de infraestructura, migración staging, permisos mínimos, carga repetida, evento de archivo/borrado y recuperación tras carga confirmada sin ACK local.

### QA y tesis

- Entradas: cambios integrados y criterios AC01–AC14.
- Produce: pruebas de aceptación, corpus anotado independientemente y métricas comparables.
- Límites: no altera código de producción para hacer pasar una prueba sin comunicar el defecto al propietario; no inventa una universidad de prueba como si fuera una fuente real; no publica métricas no medidas.
- Revisión: bloquea cierre por pérdida de datos, duplicados, filtración de secretos/borradores, fechas fabricadas, imágenes no trazables o eventos analíticos inconsistentes.

## Secuencia de trabajo

| Oleada | Trabajo autorizado por el plan | Condición para comenzar |
|---|---|---|
| 0 | Coordinador: contratos de tarea 1 y asignación de propiedad | Especificación y plan leídos |
| 1 | Backend: tareas 2–3; Recolector: tareas 4–7 | Contratos integrados; trabajos de archivos independientes |
| 2 | Backend: tarea 8; Recolector + coordinador: tarea 9 | Almacenamiento y evidencia disponibles |
| 3 | Frontend: 10–11; Recolector: 12; Backend: 13 | API de tareas 8–9 estable |
| 4 | Recolector y Backend por subpasos: 15 (imagen); QA: 14 | Sin editar simultáneamente contratos o endpoints compartidos |
| 5 | Backend: outbox de 16; Cloud: prepare/fakes de 16; QA: aceptación local de 18 | Imagen integrada y contratos de eventos definidos |
| 6 | Cloud: carga real BigQuery de 16, cuando se pase a esa fase | Aceptación local y manifiesto comprobados; usuario ha decidido subir datos |
| 7 | Cloud + Backend: plataforma cloud de 17, en fase posterior | Exportación comprobada y decisión de desplegar plataforma |
| 8 | Coordinador + QA: 18 y entrega final por ambiente | Evidencia real de fases ejecutadas; restantes marcadas not_executed |

La oleada 4 divide imagen por contratos: primero coordinador fija `ImageAsset`, luego recolector extrae y backend recibe, después frontend presenta. La oleada 5 no significa que dos agentes editen `models.py`: el backend posee la migración y cloud consume el contrato resultante.

## Formato de encargo y entrega

```text
Encargo:
- Tarea/objetivo: ID del plan y resultado observable.
- Requisitos: U/AC aplicables.
- Propiedad: lista exacta de archivos autorizados.
- Entradas: firmas y revisiones de contratos ya integradas.
- Salidas: firmas, artefactos y cambios que otro rol consumirá.
- Validación: comandos y resultados esperados.
- Restricciones: archivos compartidos reservados y acciones externas fuera del encargo.

Entrega:
- Resultado conseguido y diferencia de comportamiento.
- Archivos propios modificados.
- Comandos ejecutados, resultados y evidencia.
- Migraciones o configuración necesarias.
- Problemas concretos abiertos y contrato afectado.
```

Las revisiones de QA son independientes del implementador. El coordinador puede pedir una corrección al mismo agente y luego volver a verificar el comportamiento afectado. No se crean nuevos agentes únicamente para volver a leer un resultado que ya puede revisar el coordinador.
