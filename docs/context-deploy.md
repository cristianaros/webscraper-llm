# Contexto y runbook de despliegue UniNews

Actualizado: 2026-11-01. **Estado: `ready_for_cutover` para iniciar el checklist manual; no desplegado ni aprobado para servir tráfico.** Las pruebas locales de migración sobre copia SQLite y pinning HTTP/browser pasan. Antes de tráfico se requiere un ensayo de importación contra PostgreSQL 15+ y confirmar el pinning browser en el equipo Windows con Chromium real, o bloquear allí las fuentes `render_mode="browser"`. Consultar [el registro de aceptación](acceptance/production.md).

## Arquitectura

- Astro estático se publica en Vercel.
- FastAPI y PostgreSQL administrado se ejecutan en Railway. `railway.toml` aplica Alembic y luego el seed idempotente al liberar una versión.
- El recolector Python corre en una máquina Windows separada y envía datos por HTTPS. No ejecutar su scheduler en Railway/FastAPI.
- El modelo del recolector y del asistente es `nvidia/nemotron-3.5-super-vl:free`; las peticiones OpenRouter exigen precio máximo cero.
- Los bytes de imágenes se guardan en PostgreSQL; no depender del disco efímero de Railway.
- En producción la API usa el `X-Real-IP` validado para separar las cuotas por visitante. Ignora `X-Forwarded-For`, cuyo contenido/orden no se asume confiable. Esto presupone tráfico por el edge HTTP público de Railway, que define `X-Real-IP`; no asumir la misma confianza para ingreso privado/directo si no aplica controles equivalentes.

## Gates antes de abrir tráfico

1. En el equipo Windows con Chromium real, verificar que el modo browser bloquea DNS rebinding antes de enviar una solicitud; alternativamente, mantener deshabilitadas todas las fuentes `render_mode="browser"`. El test local confirma que el resolver rule se entrega antes de navegar, no el destino de un socket Chromium real.
2. Si se importan los datos legados, ensayar una copia en PostgreSQL 15+ y confirmar conteos, bytes/hashes de imagen y secuencias. La prueba disponible usó SQLite para comprobar la copia, Alembic, backfill y conteos; la función de sincronización de secuencias PostgreSQL se ejercitó con conexión simulada.
3. Completar y documentar las comprobaciones manuales de Railway, Vercel y Windows del registro de aceptación. No abrir tráfico ni activar Task Scheduler antes de cerrar los gates aplicables.

No activar Task Scheduler mientras un gate de seguridad siga abierto. No guardar la base operacional o cola definitiva en almacenamiento efímero.

## Migración de la base local

La prueba `tests/integration/test_legacy_db_cutover.py` trabaja sobre una copia temporal creada con `shared.backup.backup_sqlite`; no cambia `data/backend/university_news.db`. Para una migración operativa opcional, crear de nuevo una copia única y dirigir el comando a una instancia PostgreSQL 15+ vacía y respaldada:

```powershell
@'
from pathlib import Path
from shared.backup import backup_sqlite
source = Path("data/backend/university_news.db")
backup = Path("data/backend/university_news.pre-cutover.db")
backup_sqlite(source, backup)  # el destino debe no existir
print(f"Copia creada: {backup} ({backup.stat().st_size} bytes)")
'@ | .\.venv\Scripts\python.exe -
$env:DATABASE_URL = "<referencia local segura a PostgreSQL 15+>"
python -m scripts.migrate_to_postgres --source data/backend/university_news.pre-cutover.db --destination $env:DATABASE_URL --media-root data/backend/media
```

No reutilizar una copia destino ya existente ni apuntar a la base original para escribir. Mantener `DATABASE_URL` fuera de logs y capturas. Antes de abrir tráfico, verificar el informe de migración, las **14 noticias**, las **6 imágenes** con SHA-256 correcto y que las secuencias permitan inserciones nuevas. La migración compara conteos y aborta si no encuentra bytes de medios verificables; no sustituye un backup/restauración del destino PostgreSQL.

## Puesta en marcha en cuatro pasos

1. Publicar el código revisado mediante el proceso de release autorizado y confirmar que el release corresponde a los archivos aceptados. Este runbook no implica que ese release ya haya ocurrido.
2. Configurar PostgreSQL y el servicio API de Railway: `APP_ENV=production`, `DATABASE_URL`, `ADMIN_TOKEN`, `COLLECTOR_TOKEN`, `COLLECTOR_ID`, `ALLOWED_ORIGINS`, `RAG_ENABLED=true`, `OPENROUTER_API_KEY` y `OPENROUTER_MODEL=nvidia/nemotron-3.5-super-vl:free`. Usar referencias/secretos del servicio; no copiar valores sensibles a repositorio, frontend o logs. Aplicar Alembic y seed. Si se trasladan los datos locales, seguir el procedimiento de copia anterior antes de aceptar tráfico.
3. Configurar `PUBLIC_API_URL=https://<railway-domain>` en Vercel, publicar el frontend y verificar noticias, imágenes, chat, login/admin y CORS. No agregar secretos backend a variables `PUBLIC_*`.
4. En Windows, usar el archivo único `.env` en la raíz del proyecto fuera del control de versiones; ejecutar `python -m collector doctor --check-api` (o `python -m collector --env .env doctor --check-api`) y `python -m collector run-once`; revisar noticia, imagen, heartbeat y cola. Registrar Task Scheduler con `scripts/windows/register-collector-task.ps1` solo después de cerrar los gates de seguridad y migración.

## Railway: servicio API y PostgreSQL

1. Crear el servicio PostgreSQL y el servicio API en la cuenta autorizada. Conectar el repo mediante el release aprobado y comprobar `deploy/Dockerfile.api` y `railway.toml`.
2. Configurar `DATABASE_URL` con la referencia privada/variable ofrecida por Railway.
3. Generar dos secretos aleatorios distintos, cada uno de al menos 32 caracteres, para `ADMIN_TOKEN` y `COLLECTOR_TOKEN`. No reutilizar los valores de `.env.example`.
4. Configurar `APP_ENV=production`, `COLLECTOR_ID=windows-collector-1`, `ALLOWED_ORIGINS=["https://<dominio-vercel>"]`, `RAG_ENABLED=true`, `OPENROUTER_API_KEY` y `OPENROUTER_MODEL=nvidia/nemotron-3.5-super-vl:free`. `CHAT_DAILY_BUDGET=100` y `CHAT_IP_RPM=6` son valores iniciales ajustables.
5. Confirmar que la release ejecutó migraciones hasta `0006` y el seed; revisar `/health`, `/api/info` y ausencia de secretos en logs. Verificar persistencia tras restart controlado y que imágenes se sirvan desde DB.

## Vercel: frontend estático

1. Configurar `PUBLIC_API_URL=https://<dominio-railway>` en cada ambiente.
2. Configurar el dominio definitivo y agregar su origen HTTPS exacto a `ALLOWED_ORIGINS` en Railway.
3. Publicar el frontend y comprobar carga de noticias, imágenes API, rutas de chat/admin y errores esperados. Los tokens administrativos permanecen en memoria del navegador.

## Windows: recolector independiente

1. Instalar Python compatible con `collector/requirements.txt`, preparar el entorno y usar el archivo único `.env` en la raíz del proyecto (o copiar `.env.example` a `.env` en una máquina nueva).
2. Establecer `APP_ENV=production`, `COLLECTOR_API_URL=https://<dominio-railway>`, `COLLECTOR_ID`, `COLLECTOR_TOKEN`, una ruta persistente `COLLECTOR_DATA_DIR` y la clave OpenRouter. Mantener el modelo autorizado exacto.
3. Desde la raíz del checkout, ejecutar `python -m collector doctor --check-api`; resolver errores. Ejecutar `python -m collector run-once`, revisar resultado, heartbeat, cola/reintentos y publicación.
4. Antes de programar, asegurar que las fuentes en modo navegador están bloqueadas o que la protección preconexión ha sido aceptada. Luego revisar rutas/usuario de `scripts/windows/register-collector-task.ps1` y `scripts/windows/run-collector.ps1`, registrar la tarea y comprobar su historial tras una ejecución programada.

## Secuencia de cutover y rollback

1. Acordar ventana, dominios, cuenta de facturación, accesos y responsable de rollback.
2. Cerrar todos los gates de aceptación; provisionar/configurar Railway, migrar/sembrar y validar salud, CORS, persistencia, API administrativa y estado del recolector.
3. Configurar Vercel y verificar el portal público.
4. Configurar Windows, ejecutar `doctor` y `run-once`, inspeccionar noticias/revisiones/imágenes y solo entonces registrar la tarea periódica.
5. Vigilar logs de Railway, cuota OpenRouter, cola/heartbeat y resultados editoriales durante la ventana inicial. Deshabilitar la tarea o revertir el release si hay duplicados, errores de autenticación o datos inconsistentes.

El despliegue requiere acceso a cuentas externas y una decisión sobre ventana/responsable; estas acciones no se han ejecutado. No declarar producción activa antes de documentar cada comprobación.

## Referencias operativas

- `docs/operations/collector-windows.md`
- `docs/operations/server.md`
- `docs/operations/recovery.md`
- `.env.example` en la raíz (plantilla única sin secretos para `.env`)
- `docs/acceptance/production.md` (registro de evidencia del cutover)
