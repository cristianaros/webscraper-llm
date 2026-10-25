# Fuentes del directorio DatosLab: piloto local del 2026-10-25

El [directorio de universidades](https://uninews.datoslab.cl/universidades/) se tomó como catálogo cerrado de 21 instituciones. Cada perfil de DatosLab sirve para descubrir enlaces; el cuerpo y la fecha se descargan del portal oficial al que redirige `/detalle/<id>`. El nombre de la universidad y los hosts admisibles están fijados en `backend/scripts/datoslab_catalog.py`.

## Resultado comprobado

- 21 fuentes nuevas registradas; 11 habilitadas con una muestra que contiene título, cuerpo y fecha originales. Cinco tienen publicación automática y seis requieren revisión editorial.
- La API local muestra 14 noticias publicadas. Trece se recogieron en este piloto: UPLA (5), UACH (2), UCT (2), UBIOBIO (2) y ULAGOS (2). La noticia restante de Universidad de Chile ya existía antes del piloto.
- En la cola nueva hay 28 artículos entregados, uno diferido por `http_404` y siete a la espera del presupuesto diario local del LLM. En la API hay 14 revisiones pendientes: siete con salida inválida del LLM y siete de revisión editorial. No se publicaron al faltar campos comprobados o una aprobación editorial.
- La suite Python terminó con `64 passed, 1 deselected, 4 warnings` después de los últimos ajustes. `GET /api/news/stats` devolvió `total_news: 14` y las cinco universidades publicadas en el piloto; la portada hidratada mostró 14 publicaciones.

Las muestras de las once fuentes habilitadas, con URL original, número de caracteres y fecha, están en `data/audits/datoslab-active-verified-2026-10-25.jsonl`, `data/audits/datoslab-archive-verified-2026-10-25.jsonl`, `data/audits/datoslab-udec-verified-2026-10-25.jsonl` y `data/audits/datoslab-utalca-verified-2026-10-25.jsonl`. Son archivos locales ignorados por Git. La auditoría inicial de todas las fuentes está en `data/audits/datoslab-2026-10-25.jsonl`; sus errores corregidos durante el piloto no representan el estado final de las once habilitadas.

## Estado por universidad

| Sigla | Universidad | Estado del piloto | Evidencia o impedimento |
|---|---|---|---|
| PUCV | Pontificia Universidad Católica de Valparaíso | Revisión editorial | El nuevo perfil aisló cuerpo y fecha originales; el enlace observado es de 2022 y hay 3 entregas pendientes. |
| UNAP | Universidad Arturo Prat | Revisión editorial | El nuevo perfil aisló cuerpo y fecha originales; el enlace observado es de 2022 y hay 1 entrega pendiente. |
| UACH | Universidad Austral de Chile | Publicación automática | Título, cuerpo y fecha originales verificados; 2 noticias publicadas. |
| UCT | Universidad Católica de Temuco | Publicación automática | Título, cuerpo y fecha originales verificados; 2 noticias publicadas. |
| UCSC | Universidad Católica de la Santísima Concepción | Revisión editorial | Extracción válida, pero el perfil enlaza una noticia de 2023; 2 entregas pendientes. |
| UCM | Universidad Católica del Maule | Inactiva | `robots_denied`. |
| UCN | Universidad Católica del Norte | Inactiva | `robots_unavailable`. |
| UTFSM | Universidad Técnica Federico Santa María | Inactiva | `robots_unavailable`. |
| UA | Universidad de Antofagasta | Inactiva | `robots_unavailable`. |
| UDA | Universidad de Atacama | Inactiva | El enlace llega a una página genérica sin título ni fecha de artículo verificables. |
| UAYSEN | Universidad de Aysén | Revisión editorial | Extracción válida, pero el perfil enlaza una noticia de 2025; 3 entregas pendientes. |
| UDEC | Universidad de Concepción | Revisión editorial | Los dos primeros enlaces carecen de fecha original; el tercero sí tiene título, cuerpo y fecha de 2026. Tres documentos esperan el presupuesto diario del LLM. |
| ULAGOS | Universidad de Los Lagos | Publicación automática | Título, cuerpo y fecha originales verificados; 2 noticias publicadas. |
| UMAG | Universidad de Magallanes | Inactiva | `dns_failed`. |
| UPLA | Universidad de Playa Ancha | Publicación automática | Título, cuerpo y fecha originales verificados; 5 noticias publicadas. |
| UTALCA | Universidad de Talca | Revisión editorial | El nuevo perfil aisló título, cuerpo y fecha original de 2025; tres documentos esperan el presupuesto diario del LLM. |
| UTA | Universidad de Tarapacá | Inactiva | Hay título y cuerpo, pero no fecha publicada en el artículo observado. |
| UV | Universidad de Valparaíso | Inactiva | Redirección a un host de validación fuera de la lista permitida. |
| UFRO | Universidad de la Frontera | Inactiva | `robots_denied`. |
| USERENA | Universidad de la Serena | Inactiva | Tras admitir el host institucional de redirección, `robots.txt` no estuvo disponible. |
| UBIOBIO | Universidad del Bío-Bío | Publicación automática | Título, cuerpo y fecha originales verificados; 2 noticias publicadas. |

Un perfil verificado prueba una muestra, no una cobertura completa del archivo de la universidad. La auditoría examina hasta tres enlaces y registra los candidatos rechazados. Se deberán volver a evaluar enlaces nuevos y cambios de HTML antes de prometer continuidad.

## Datos locales y reproducción

- Base operacional: `data/backend/university_news.db`. Respaldo previo: `data/backups/university_news-before-datoslab-2026-10-25.db` (integridad SQLite comprobada).
- Cola de este piloto: `data/collector-datoslab/collector.db`. Se conservó intacta la cola anterior `data/collector/collector.db`.
- `collector/.env`, ignorado por Git, apunta la API a `http://127.0.0.1:8765` y usa `data/collector-datoslab` como directorio de datos. Los secretos no se copiaron a archivos versionados.
- Los 21 registros pueden revisarse sin duplicados con `register_datoslab_sources.py`. `audit_datoslab_sources.py` respeta `robots.txt` y la lista de hosts; `activate_datoslab_sources.py` comprueba muestra, identidad y revisión de fuente antes de habilitarla.

Desde la raíz, con la API local en marcha:

```powershell
$env:PYTHONPATH='backend;.'
.\.venv\Scripts\python.exe backend/scripts/register_datoslab_sources.py
.\.venv\Scripts\python.exe backend/scripts/audit_datoslab_sources.py --output data/audits/nueva-auditoria.jsonl
.\.venv\Scripts\python.exe -m collector --env collector/.env doctor
.\.venv\Scripts\python.exe -m collector --env collector/.env run-once
```

Para cambiar un perfil, actualizar solo la fuente inactiva con `register_datoslab_sources.py --update-inactive`, repetir la auditoría y habilitar explícitamente las siglas cuya muestra sea válida. El script de activación rechaza auditorías que ya no coinciden con el ID o la revisión de la fuente.

## Pendientes operativos

- Los 10 perfiles inactivos requieren ajuste de selectores, reparación del portal o una fuente institucional accesible y autorizada. No se eludieron `robots.txt` ni validaciones de acceso, ni se inventaron fechas.
- Una noticia redirigida terminó en `http_404` y seguirá diferida hasta el reintento. Siete revisiones tienen salida inválida del modelo; conservan el documento original para reintento o revisión. Otros siete documentos esperan el próximo presupuesto diario local del LLM (30 solicitudes por día) y una nueva ejecución del recolector. OpenRouter devolvió temporalmente `provider_unavailable` durante el piloto de ULAGOS; un reintento posterior entregó los tres artículos.
- No se instaló una tarea programada de Windows y este piloto no acredita ejecución continua. Tampoco se desplegó en Azure. La API y la web locales deben seguir activas para que el recolector entregue artículos.
- Las imágenes no se comprobaron para todos los artículos; algunos se muestran sin imagen. No se reemplazaron por imágenes generadas.
