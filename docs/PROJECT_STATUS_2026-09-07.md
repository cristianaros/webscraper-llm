# Estado de UniNews para continuar

Fecha de corte: 2026-09-07 (America/Santiago)
Run de Orca: `run_62ee55b9897f`

## Situación actual

La implementación está funcional en local y la última QA ejecutada con GPT-5.6-Luna medium verificó:

- `pytest` completo: **37 passed**.
- `npm run typecheck`: sin errores.
- `npm run build`: correcto.
- `npm run lint`: sin errores; queda una advertencia de React Hook.
- Alembic `upgrade/downgrade` sobre SQLite temporal: correcto.
- CLI, scripts PowerShell y contratos de media, búsqueda y outbox: verificados.
- No quedan identificadores activos de ScrapeGraphAI, SGAI ni UPLA-client.

La QA dejó el estado como **BLOCKED**, porque faltan entregables del plan, no porque fallen las pruebas actuales.

## Trabajo pendiente en Orca

Está despachada la tarea `task_f52ba9295bd1` con `gpt-5.6-luna`, esfuerzo `medium`:

- añadir retry y backup explícitos al CLI del recolector;
- ampliar pruebas de recuperación con fixtures;
- incluir corpus/evaluación local AC10 reproducible;
- documentar y comprobar en modo dry-run la Scheduled Task de Windows.

Cuando entregue `worker_done`, hay que leer el informe, liberar el worker, reconocer la entrega y repetir QA independiente.

## Secuencia para el próximo día

1. Consultar Orca:

   ```powershell
   orca orchestration check --run run_62ee55b9897f --peek --json
   orca orchestration task-list --run run_62ee55b9897f --json
   ```

2. Si la tarea Luna terminó, ejecutar:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest tests/unit tests/integration -q
   npm run typecheck
   npm run lint
   npm run build
   ```

3. Revisar que existan pruebas y documentación para retry, backup, AC10 y Scheduled Task. No aceptar solo por `worker_done`.

4. Crear una nueva tarea QA independiente en Orca con `gpt-5.6-luna`, `medium`, sin editar archivos, para emitir `ACCEPTED` o `BLOCKED`.

5. Actualizar el plan y este informe únicamente con trabajo ejecutado y verificado.

## Cambios y límites

Se conservaron los cambios preexistentes del árbol Git. No se hizo push, merge, despliegue, creación de recursos Google Cloud ni carga a BigQuery. Python 3.14.7 x64 es el intérprete comprobado; la compatibilidad específica con Python 3.12 aún no está acreditada.

## Comandos útiles

```powershell
.\.venv\Scripts\python.exe -m collector --help
.\.venv\Scripts\alembic.exe -c backend/alembic.ini upgrade head
npm run dev
```
