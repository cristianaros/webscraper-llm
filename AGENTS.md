# Reglas de trabajo de UniNews

Estas instrucciones se aplican al repositorio completo. Las instrucciones explícitas del usuario y las reglas del entorno tienen prioridad. No sustituyen las instrucciones de nodeterm suministradas por el usuario cuando esa herramienta esté en uso.

## Documentos que deben leerse antes de implementar

- [Plan de implementación](docs/superpowers/plans/2026-09-06-uninews-python-openrouter.md).
- [Especificación funcional y técnica](docs/superpowers/specs/2026-09-06-uninews-python-openrouter.md).
- [Roles, contratos y coordinación de agentes](docs/superpowers/specs/2026-09-06-agent-roles.md).

## Reglas del producto

1. El scraping se realiza con Python propio. No introducir ScrapeGraphAI, servicios de scraping por créditos o mecanismos para eludir bloqueos.
2. El modelo de extracción activo es exactamente `nvidia/nemotron-3.5-super-vl:free` por OpenRouter, autorizado por el usuario el 25-10-2026 tras la baja de `minimax/minimax-m3:free`. No cambiarlo por otro modelo, un proveedor de pago o un LLM local sin nueva instrucción explícita.
3. El recolector funciona automáticamente en Windows, separado del servidor de la web y API. No poner su scheduler dentro de FastAPI o Astro.
4. Solo rastrear las universidades, hosts y enlaces configurados. El nombre institucional proviene de la configuración, nunca de una suposición del modelo.
5. Preservar título, cuerpo y fecha originales con evidencia. La categoría puede ser inferida por el LLM dentro del catálogo. No sustituir la fecha de publicación por la de extracción ni publicar datos ficticios si falla la API.
6. Extraer la imagen principal cuando exista, conservando origen, hash y metadatos; no generar una imagen para simular que fue extraída. Distinguir imagen ausente, pendiente y fallida.
7. Persistir el documento antes de llamar al LLM y el resultado antes de entregarlo. Los reintentos no deben duplicar artículos ni borrar una edición humana.
8. El almacenamiento operacional y BigQuery cumplen funciones distintas. BigQuery recibe datos analíticos versionados; una caída analítica no debe impedir publicar noticias.
9. En Google Cloud no guardar la base operacional ni la cola definitiva en el sistema de archivos efímero de Cloud Run. Usar el almacenamiento persistente previsto en la especificación.
10. Secretos fuera del código, frontend, capturas y logs. Tokens administrativos y del recolector son distintos; cuentas de servicio cloud con permisos mínimos por función.
11. Primero desarrollar y probar aplicación, datos, imágenes y preparación de lotes localmente. Subir datos a BigQuery después de validar esa etapa. El despliegue de la plataforma cloud es otra fase posterior; las pruebas locales no requieren proyecto, facturación o credenciales Google Cloud.

## Reglas de implementación y colaboración

1. Ejecutar `git status --short` al comenzar y registrar los cambios preexistentes. No revertir, formatear masivamente o sobrescribir trabajo de otra persona/agente.
2. Leer los archivos actuales antes de editar: los números de línea del plan son una referencia de la inspección, no una garantía de que el código permanezca inmóvil.
3. Implementar únicamente el alcance de la tarea asignada. Registrar una propuesta de cambio de contrato antes de modificar `shared`, migraciones compartidas, dependencias o infraestructura fuera de la propiedad asignada.
4. Un propietario activo por archivo. Para trabajo simultáneo, asignar módulos independientes o worktrees con ramas `codex/`; la coordinación integra cambios y resuelve conflictos leyendo ambas versiones.
5. Un rol definido no equivale a un agente ya ejecutándose. Despachar agentes solo para tareas concretas que puedan avanzar de forma independiente y cuando esa modalidad esté autorizada. Si no hay concurrencia disponible, ejecutar los mismos roles secuencialmente.
6. Mantener el modelo configurado por el usuario; no inventar asignaciones de modelos o presupuestos. Máximo recomendado: coordinador y tres trabajadores simultáneos, sujeto a capacidad real del entorno.
7. Escribir pruebas de comportamiento para integridad, recuperación, contratos y publicación. Usar fixtures/MockTransport; la suite habitual no consulta OpenRouter, universidades ni recursos cloud de producción.
8. Ejecutar las comprobaciones pertinentes a los archivos cambiados. Informar qué se ejecutó, qué pasó y qué no pudo verificarse. No llamar “probado” a un fragmento que solo fue leído.
9. Las migraciones conservan datos y se ensayan sobre copias. No eliminar volúmenes, recrear tablas con datos o restaurar sobre bases abiertas como atajo.
10. Usar commits pequeños con rutas explícitas; no hacer `git add .` sobre un árbol compartido con cambios ajenos. No hacer push, merge o despliegue por el mero hecho de terminar una tarea de planificación.
11. La creación de recursos Google Cloud y la activación de tareas productivas pertenecen a la ejecución, no a la redacción del plan. Respetar la autorización ya existente y las aprobaciones exigidas por las herramientas; no pedir otra autorización para una acción ya cubierta.
12. Toda entrega incluye: comportamiento conseguido, archivos propios modificados, pruebas/resultados, migraciones/configuración necesarias y riesgos concretos pendientes. No ocultar errores de extracción, límites de cuota o problemas de datos.

## Coordinación mediante Orca

Estas reglas se aplican cuando el usuario haya solicitado coordinación supervisada en Orca. Este archivo define el protocolo; no inicia agentes por sí mismo.

1. Leer las skills `orca-cli` y `orchestration` y obtener sus guías desde el ejecutable indicado por ellas. Seguir la sintaxis de la versión instalada. Comprobar que el runtime esté accesible y la función de orquestación habilitada antes de despachar; si no lo están, informar el bloqueo sin simular una ejecución ni sustituirla por agentes ajenos a Orca.
2. El coordinador crea o vincula un `Run`, registra las tareas y sus dependencias, y usa preferentemente `worker-start` para asignarlas. Verifica que existen las tareas y sus asignaciones (`Dispatch`). Abrir una terminal o enviar un prompt sin seguimiento no equivale a coordinar una tarea en Orca.
3. Cada encargo incluye objetivo, referencia al plan, contratos de entrada y salida, archivos de propiedad exclusiva, pruebas esperadas y entrega requerida. Reservar también archivos transversales como dependencias, locks, migraciones y configuración de pruebas. Un cambio de contrato se propone al coordinador antes de editarlo.
4. Iniciar los trabajos independientes antes de esperar resultados, respetando el máximo recomendado de concurrencia. El coordinador decide la secuencia: Orca no deduce conflictos ni decide por sí solo qué tareas ejecutar. Una tarea consumidora comienza cuando sus contratos y resultados previos están disponibles y comprobados; compartir una oleada en el documento de roles no elimina esas dependencias.
5. Usar el checkout requerido por la tarea y mantener un propietario activo por archivo. Crear worktrees separados cuando el usuario los solicite o exista un conflicto concreto que requiera aislamiento, explicando ese conflicto. Gestionarlos mediante Orca, con ramas `codex/`, siguiendo la política de setup del repositorio. Verificar la base Git y la presencia de planes, reglas y contratos antes de iniciar al trabajador: los cambios sin commit no se trasladan automáticamente a un nuevo worktree. No hacer commits indiscriminados para preparar esa base.
6. Los trabajadores siguen el preámbulo vigente de su asignación. Usan `ask` para bloqueos que requieren respuesta del coordinador y este responde mediante `reply`. Informan la finalización con `worker_done`, los identificadores de su asignación y un resultado explícito de éxito o fallo, incluyendo archivos y evidencia. No reutilizar identificadores de asignaciones terminadas.
7. El coordinador espera y procesa los mensajes mediante el mecanismo de orquestación, atiende preguntas y confirma la recepción después de procesar el lote completo. Un timeout, una terminal inactiva o un mensaje de progreso no demuestran finalización ni autorizan reiniciar o duplicar un trabajador.
8. Tras una finalización válida, el coordinador asigna inmediatamente otra tarea al mismo trabajador o ejecuta `worker-release` siguiendo la guía vigente. Mantener la sesión viva solo cuando el usuario lo solicite, registrándolo mediante `worker-retain`. No liberar trabajadores activos por un timeout ni sustituir una recuperación incierta por el cierre manual de terminales.
9. `worker_done` cierra una asignación, pero no acredita por sí solo la integración ni la aceptación del producto. El coordinador lee los cambios y resultados, integra dentro del alcance autorizado y comprueba los contratos; QA revisa independientemente la aceptación antes de cerrar la funcionalidad en el plan.

## Cierre de una tarea

El coordinador verifica el contrato y la evidencia antes de integrar. QA revisa independientemente la aceptación; no marca una función como terminada solo porque otro agente lo afirmó. Actualizar los checkboxes del plan únicamente por trabajo realmente ejecutado y comprobado.
