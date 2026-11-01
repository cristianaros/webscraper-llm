# Aceptación de cutover de producción

**Estado actual: `ready_for_cutover` (listo para iniciar el cutover manual; no autoriza tráfico ni operación productiva).** Las comprobaciones automatizadas locales pasan, incluida la configuración de resolución fijada antes de la navegación Chromium. Antes de abrir tráfico se deben completar los gates PostgreSQL y de red browser descritos abajo. No hay evidencia de despliegue en Railway/Vercel, tráfico productivo ni activación del recolector.

## Evidencia local automatizada

- [x] 2026-11-01: `pytest -q` completó con **103 passed, 3 deselected** tras añadir la prueba de migración directa de medios legados y prioridad de IP pública `X-Envoy-External-Address` / `X-Real-IP`.
- [x] 2026-11-01: `npm run lint`, `npm run typecheck` (0 errores) y `npm run build` finalizaron con código 0.
- [x] 2026-11-01: `tests/integration/test_production_readiness.py` pasó con los controles de cuota por `X-Real-IP`, rechazo de spoofing mediante `X-Forwarded-For` y invalidación del caché tras editar una noticia.
- [x] 2026-11-01: `tests/integration/test_legacy_db_cutover.py` copió la base local con `backup_sqlite`, elevó la copia de `0005` a `0006`, comprobó **14 noticias** y rellenó los bytes de **6 imágenes** verificando sus hashes. La base original permaneció sin cambios.
- [x] 2026-11-01: una segunda copia `0005` se migró directamente sin backfill previo; `migrate_to_postgres` incorporó bytes verificados y rechazó medios ausentes o corruptos con rollback.
- [x] 2026-11-01: las pruebas de `PublicOnlyNetworkBackend` verificaron que una respuesta DNS con una IP pública y otra link-local se rechaza antes de llamar a `connect_tcp`, y que el transporte HTTP predeterminado instala el backend de pinning.
- [x] 2026-11-01: `BrowserFetcher` resuelve todos los hosts permitidos, rechaza resultados no globales y pasa reglas `--host-resolver-rules` a Chromium antes de navegar; una prueba con Playwright simulado verifica la configuración antes de `page.goto`. La comprobación `server_addr()` posterior queda como defensa adicional.
- [x] 2026-11-01: `sync_postgres_sequences` fue comprobado con una conexión simulada; se generaron cinco llamadas `setval` para las tablas serializadas.
- [ ] **No verificado:** PostgreSQL 15+ vivo. La migración de datos legados se ensayó en SQLite; el destino SQLite confirmó conteos. La sincronización PostgreSQL solo se comprobó con conexión simulada, por lo que no demuestra una migración real ni la preservación de secuencias en PostgreSQL.
- [ ] **Límite de evidencia del navegador:** se comprobó con un lanzador Playwright simulado que Chromium recibe el mapeo antes de navegar, pero no se ejecutó Chromium real contra DNS controlado para observar el destino del socket. La aceptación local verifica la configuración de pinning; la verificación de red real queda pendiente en el entorno Windows antes de habilitar fuentes browser.

Las pruebas locales no verifican Railway, Vercel, DNS/TLS reales, cuotas OpenRouter, la red Windows ni Task Scheduler. La prueba HTTP de pinning es una prueba automatizada del backend de transporte, no una prueba de red productiva ni de TLS/SNI en una conexión real.

## Gates antes de abrir tráfico o activar la tarea automática

- [ ] Ejecutar `0001`–`0006` sobre una copia de PostgreSQL 15+ con las filas legadas requeridas; validar conteos, hashes de las 6 imágenes y secuencias después de la migración.
- [ ] En una máquina Windows autorizada con Chromium instalado, verificar el destino del socket browser contra DNS controlado y registrar que un rebinding a loopback/link-local se bloquea antes de enviar una solicitud. Mientras tanto, mantener fuentes `render_mode="browser"` deshabilitadas en producción.
- [ ] Ejecutar las comprobaciones de despliegue y operación de Railway, Vercel y Windows que siguen, registrando evidencia observada.

## Procedimiento para migrar los datos locales (opcional)

Antes de migrar la base `data/backend/university_news.db` a Railway, crear una copia nueva verificada y ejecutar la migración desde esa copia. No apuntar el comando a la base original para modificarla ni usar una base PostgreSQL con tablas/datos existentes como destino de importación.

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

Ejecutar primero en una base destino vacía y respaldada, restringir el acceso a la URL y no imprimirla en logs. La migración espera el esquema de destino y compara conteos; el comando de migración no crea una copia de seguridad PostgreSQL ni reemplaza las comprobaciones de restauración. Conservar el informe y verificar explícitamente 14 noticias, 6 imágenes servibles por hash y secuencias antes de abrir tráfico.

## Railway y PostgreSQL

- [ ] Proyecto/servicio y responsable: ____________________
- [ ] URL HTTPS API y fecha: ____________________
- [ ] PostgreSQL provisionado; `DATABASE_URL` referenciado desde Railway, no copiado a cliente/logs.
- [ ] `APP_ENV=production`; tokens admin/recolector únicos, distintos y de 32+ caracteres; secretos no registrados en este documento.
- [ ] `ALLOWED_ORIGINS` contiene el origen Vercel exacto; identificador collector coincide en ambos lados.
- [ ] Release completó Alembic hasta `0006` y seed idempotente (21 universidades y 11 fuentes verificadas habilitadas).
- [ ] `/health`, `/api/info`, login administrativo y autenticación del collector revisados.
- [ ] Persistencia PostgreSQL confirmada tras restart controlado; imágenes verificadas servidas desde DB.
- [ ] La migración PostgreSQL 15+ con datos legados fue ejecutada y verificada, si se trasladan los datos locales.
- [ ] Confirmar el comportamiento del proxy en Railway: la API confía en `X-Envoy-External-Address` / `X-Real-IP` (priorizando IP global validada) solo con `APP_ENV=production` y no usa `X-Forwarded-For`.
- Evidencia/run ID/fecha: ____________________

## Vercel

- [ ] `PUBLIC_API_URL=https://<dominio-api-railway>` en ambientes requeridos; ninguna clave privada configurada como `PUBLIC_*`.
- [ ] Build/deploy y dominio confirmados; origen incluido en CORS.
- [ ] Noticias y filtro por universidad cargan; imagen API carga; chat tiene respuesta/error esperado; admin opera con token en memoria.
- URL y fecha de deploy: ____________________

## Recolector Windows

- [ ] `.env` local fuera del control de versiones, `APP_ENV=production`, HTTPS Railway, `COLLECTOR_ID` y token coinciden.
- [ ] `python -m collector --env collector/.env doctor --check-api` pasa.
- [ ] `python -m collector --env collector/.env run-once` termina; heartbeat reciente y cola/reintentos revisados.
- [ ] Una noticia entregada se contrasta con fuente original: título, cuerpo, fecha, categoría; imagen/hash/origen cuando exista.
- [ ] Fuentes `render_mode="browser"` permanecen deshabilitadas hasta confirmar con Chromium real el mapeo de destino y el bloqueo previo al envío.
- [ ] Task Scheduler configurado con usuario, rutas y frecuencia revisados; una ejecución programada observada en historial.
- Evidencia/fecha: ____________________

## Decisión de activación y rollback

- Ventana y responsable: ____________________
- Aprobación de cutover: ____________________
- Señales de aceptación: no hay duplicados, los estados publicados/pending son correctos, datos persisten, cola avanza y no se filtran secretos.
- Rollback: deshabilitar tarea Windows; revertir release/configuración frontend según el procedimiento acordado; preservar DB y exportar evidencia antes de reparar datos.
- Resultado final y fecha: ____________________

`ready_for_cutover` permite comenzar el checklist manual y las validaciones en sus entornos reales; no significa que el cutover esté completo ni que el sistema esté aprobado para servir tráfico. Mantener cerrado el tráfico/Task Scheduler hasta completar los gates PostgreSQL y Chromium indicados.
