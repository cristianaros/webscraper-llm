# QA local del recolector

Esta evidencia no usa red productiva.

## Recuperación y backup

```powershell
python -m collector --env C:\UniNews\collector\.env retry --item <UUID>
python -m collector --env C:\UniNews\collector\.env backup --output C:\UniNews\backups\collector-2026-09-07.db
```

`retry` reencola un elemento diferido; `backup` crea una copia SQLite mediante la API online, rechaza destinos existentes y comprueba `integrity_check`. `tests/integration/test_cli_recovery.py` cubre ambos casos localmente.

## Scheduled Task dry-run

La inspección no registra ni inicia tareas:

```powershell
Test-Path .\.venv-collector\Scripts\python.exe
Test-Path .\collector\.env
Get-Content .\scripts\windows\register-collector-task.ps1
```

Después, en una sesión autorizada, ejecutar `doctor` y revisar `Get-ScheduledTaskInfo -TaskName 'UniNews Collector'`. Esto no acredita aún la operación real de 72 horas.

## AC10

La evaluación offline reproducible está documentada en `evaluation/README.md` y no invoca OpenRouter. El corpus real y sus métricas quedan pendientes hasta contar con URLs consentidas y anotación humana; un piloto de menos de tres universidades no demuestra generalización.
