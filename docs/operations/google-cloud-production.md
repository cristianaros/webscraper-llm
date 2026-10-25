# Operación en Producción: Google Cloud

Este documento describe la fase posterior de despliegue en Google Cloud Platform una vez completada y aceptada la operación local.

## 1. Requisitos Previos

- Proyecto GCP con facturación activa.
- Cuenta de servicio con permisos mínimos para Cloud Run, Cloud SQL y Cloud Storage.
- CLI de `gcloud` instalado y autenticado (`gcloud auth application-default login`).
- Secret Manager configurado con tokens de API y credenciales de base de datos.

## 2. Componentes

1. **Artifact Registry / Container Image**:
   - Construcción con `deploy/gcp/cloudbuild.yaml` o Docker.
   - Contenedor unificado: FastAPI para `/api` y archivos Astro preconstruidos en `/`.

2. **Cloud Run (`uninews-web`)**:
   - Servicio sin estado, TLS gestionado por Google Cloud.
   - Montaje de Cloud SQL Auth Proxy para conexión a PostgreSQL.

3. **Cloud SQL (PostgreSQL)**:
   - Base de datos operacional persistente.
   - Migración de datos SQLite usando `backend/scripts/migrate_to_postgres.py`.

4. **Cloud Storage**:
   - Bucket de medios privado para imágenes de noticias (`gs://uninews-media/`).

5. **BigQuery**:
   - Dataset analítico versionado `uninews` con tablas particionadas por fecha de evento.

## 3. Despliegue

Ejecutar el script PowerShell con los parámetros requeridos:

```powershell
.\scripts\gcp\deploy-platform.ps1 `
    -ProjectId "mi-proyecto" `
    -Region "us-central1" `
    -ImageDigest "us-central1-docker.pkg.dev/mi-proyecto/uninews/uninews-web:latest" `
    -SqlInstanceConnectionName "mi-proyecto:us-central1:uninews-db" `
    -MediaBucket "uninews-media" `
    -WebServiceAccount "uninews-web@mi-proyecto.iam.gserviceaccount.com" `
    -DatabaseSecretVersion "projects/mi-proyecto/secrets/db-url/versions/latest" `
    -AdminSecretVersion "projects/mi-proyecto/secrets/admin-token/versions/latest" `
    -CollectorSecretVersion "projects/mi-proyecto/secrets/collector-token/versions/latest"
```
