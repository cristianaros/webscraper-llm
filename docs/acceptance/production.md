# Aceptación de Despliegue en Producción Cloud

Estado: `not_executed` (fase posterior opcional; no bloquea operación analítica ni desarrollo local).

## Resumen

- Despliegue preparado en `deploy/gcp/`:
  - `deploy/gcp/Dockerfile` para contenedor unificado FastAPI + Astro estático.
  - `deploy/gcp/cloudbuild.yaml` para construcción en Artifact Registry.
  - `scripts/gcp/deploy-platform.ps1` para aprovisionamiento y despliegue en Cloud Run.
  - `backend/scripts/migrate_to_postgres.py` para migración opcional de SQLite a Cloud SQL PostgreSQL.
  - `backend/services/gcs_media.py` para almacenamiento en Cloud Storage.
- La ejecución productiva en Google Cloud está reservada para la etapa posterior a la validación de operación local y carga analítica.
