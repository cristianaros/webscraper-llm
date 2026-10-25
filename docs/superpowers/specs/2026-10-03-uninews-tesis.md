# UniNews: propuesta y protocolo de tesis de Ingeniería Civil Informática

Fecha: 2026-10-03, America/Santiago. Estado: propuesta para desarrollar y revisar con el profesor guía; no contiene resultados experimentales.

Carrera confirmada: **Ingeniería Civil Informática**. La institución, reglamento, formato de memoria, plazo y dedicación semanal no fueron especificados. El alcance y cronograma son propuestas; no se presentan como requisitos de una universidad particular.

## 1. Título y contribución

**Título propuesto:** «Diseño, implementación y evaluación de un sistema trazable de recopilación y visualización de noticias universitarias chilenas mediante scraping en Python y extracción asistida por un modelo de lenguaje».

**Nombre del artefacto:** UniNews.

La contribución propuesta reúne tres resultados comprobables:

1. Un sistema de ingeniería que integra fuentes heterogéneas, evidencia original, cola recuperable, revisión editorial y publicación web.
2. Una evaluación pareada de extracción mediante reglas frente a selección de evidencia asistida por LLM sobre un corpus universitario chileno delimitado.
3. Evidencia de sus límites: fidelidad, cobertura, esfuerzo de configuración, latencia, dependencia del proveedor y comportamiento ante fallos.

No se propone entrenar un nuevo modelo ni afirmar una innovación algorítmica que el proyecto no haya demostrado. Un resultado en que las reglas igualen o superen al LLM sigue siendo una conclusión válida. La novedad respecto de trabajos previos debe argumentarse después de la revisión bibliográfica, no afirmarse por usar IA.

## 2. Problema de investigación

Hipótesis de contexto por documentar: para consultar noticias de varias universidades, un lector debe navegar fuentes con distintas estructuras y mecanismos de consulta. La extracción automática puede incorporar navegación como contenido, omitir párrafos o confundir fechas; además, un proceso que depende de una API puede interrumpirse por cuota o conectividad.

No afirmar que «no existe ninguna plataforma similar», que todas las universidades comparten esos problemas o que el usuario ahorrará un porcentaje de tiempo sin medirlo. Documentar el problema con una auditoría de las fuentes elegidas y, cuando sea viable, tareas de consulta con usuarios.

**Pregunta principal:** ¿Qué calidad de extracción, trazabilidad y confiabilidad operacional alcanza UniNews al recopilar y presentar noticias de universidades chilenas seleccionadas, y qué diferencias produce incorporar selección de evidencia mediante un LLM frente a una alternativa determinista?

**Preguntas específicas:**

- PI1: ¿Cómo cambia la fidelidad de título, cuerpo, fecha y categoría entre ambos métodos sobre los mismos documentos?
- PI2: ¿Qué cobertura, latencia y carga de revisión manual se observan, incluyendo fallos y cuotas?
- PI3: ¿El sistema conserva noticias y ediciones, evita duplicados y mantiene recuperación verificable ante fallos?
- PI4: ¿El mostrador permite completar tareas de búsqueda y lectura con resultados correctos y trazables?

**Objetivo general:** Diseñar, completar y evaluar UniNews como sistema de recopilación y visualización de noticias universitarias chilenas, contrastando extracción determinista y asistida por LLM mediante evidencia reproducible de calidad y operación.

| Objetivo específico | Resultado verificable | Evidencia |
|---|---|---|
| OE1. Caracterizar fuentes y requisitos | Inventario de portales, restricciones y matriz de requisitos | Auditoría, literatura y trazabilidad |
| OE2. Completar arquitectura e implementación | Scraper, persistencia, API y mostrador integrados | Código, contratos, migraciones y tests |
| OE3. Construir corpus de referencia | Documentos capturados y anotaciones humanas independientes | Manifiesto, guía, partición y desacuerdos |
| OE4. Comparar los métodos de extracción | Métricas por método, artículo y universidad | Predicciones, intervalos y análisis de errores |
| OE5. Evaluar operación y uso del portal | Pruebas de recuperación y tareas de usuario | Logs, evidencias de UI y resultados desidentificados |
| OE6. Documentar aportes y limitaciones | Memoria y paquete reproducible | Capítulos, anexos, scripts y defensa |

**Hipótesis de trabajo, si el reglamento exige hipótesis:** la selección asistida por LLM puede mejorar la fidelidad del cuerpo o la clasificación respecto de reglas, a cambio de latencia y dependencia de disponibilidad. Para PI1 se fija como variable primaria la diferencia media pareada de F1 del cuerpo, B−A; una mejora no está asumida. Las restantes métricas son secundarias. No cambiar la métrica primaria después de ver los resultados finales.

## 3. Metodología propuesta

Usar investigación aplicada con construcción y evaluación de un artefacto, organizada mediante Design Science Research. DSRM ofrece un proceso que vincula problema, objetivos, desarrollo, demostración, evaluación y comunicación. Su aplicación concreta a UniNews es una decisión de este protocolo. [Peffers et al., 2007](https://doi.org/10.2753/MIS0742-1222240302).

| Actividad | Aplicación a UniNews | Entregable |
|---|---|---|
| Problema | Auditar consulta y heterogeneidad de fuentes elegidas | Planteamiento y evidencia del contexto |
| Objetivos | Precisar fidelidad, operación y uso | Requisitos y protocolo congelado |
| Diseño/desarrollo | Completar el sistema existente | Versión evaluable y pruebas |
| Demostración | Ejecutar flujo fuente → publicación → lector | Piloto documentado |
| Evaluación | Comparación pareada, fallos y tareas de uso | Resultados y análisis |
| Comunicación | Argumentar conclusiones con evidencia | Memoria, anexos y defensa |

Scrum o Kanban pueden organizar el trabajo, pero no sustituyen el diseño de investigación ni la evaluación. No se requiere imponer una metodología ágil si una lista de tareas y entregas semanales basta.

## 4. Alcance técnico y académico

Se heredan íntegramente U01–U16 de la [especificación del producto](2026-09-06-uninews-python-openrouter.md), las reglas de [AGENTS.md](../../../AGENTS.md) y los [roles](2026-09-06-agent-roles.md).

La tesis utiliza Python propio; el único LLM autorizado es `minimax/minimax-m3:free` vía OpenRouter. El nombre de universidad procede de configuración, el cuerpo se reconstruye desde evidencia y las fechas no se inventan. La web conserva Astro/React y FastAPI. Windows ejecuta el recolector separado del servidor; durante desarrollo pueden correr como procesos separados en un mismo PC.

El [plan de implementación del producto](../plans/2026-10-03-uninews-scraper-y-mostrador.md) cubre las correcciones necesarias para disponer del artefacto evaluable. Este protocolo agrega investigación, corpus, medición, análisis y escritura; no autoriza duplicar módulos ni desarrollar una segunda plataforma.

**Núcleo de la tesis:** scraper, mostrador, persistencia, trazabilidad, comparación A/B, operación local y evaluación del uso. Imagen original y administración forman parte del sistema; no se atribuye su calidad al LLM si ambos métodos usan el mismo extractor de imágenes.

**Fases posteriores del producto:** carga real a BigQuery y despliegue cloud. No son requisitos de este experimento local salvo que el profesor guía los incorpore explícitamente al alcance académico. Su postergación no elimina los requisitos del producto; quedan como fases no ejecutadas.

**Fuera del núcleo:** entrenamiento/fine-tuning, GPU local, evasión de bloqueos, cobertura de todo Chile, múltiples LLM, PDF/OCR, extracción detrás de login y evaluación del chat RAG.

## 5. Diseño de la comparación

### 5.1 Unidades, tratamientos y control

- **Unidad primaria:** una noticia con documento capturado e identidad estable. Sus párrafos no se cuentan como observaciones independientes.
- **A — reglas:** selectores/metadata, reconstrucción determinista y clasificación por reglas documentadas. Completar fecha y categoría de esta alternativa antes de compararla: `baseline_extract` hoy solo devuelve título/cuerpo.
- **B — asistido:** mismo documento y candidatos; MiniMax selecciona identificadores de título/cuerpo/fecha y categoría; Python reconstruye desde evidencia.
- **Elementos compartidos:** captura, configuración de institución, parser de candidatos, normalización, validación, descarga de imagen, almacenamiento y presentación.
- **Clasificación A:** mapear categoría original del portal al catálogo cuando exista; en ausencia, reglas de palabras clave y desempate fijados usando solo desarrollo; si no hay señal, `General`. Guardar el mapeo/reglas exactos y su hash.
- **No confundir:** la universidad configurada es una verificación del sistema, no una capacidad inferida por el modelo. Diferencias de título/fecha pueden ser nulas si el parser solo produce un candidato.

Medir dos perspectivas separadas: (a) extracción sobre documentos congelados para comparar métodos bajo igual entrada; (b) flujo completo desde el inventario de URLs, incluyendo descarga fallida, página bloqueada, cuota, revisión y publicación. No excluir fallos para mejorar resultados del sistema.

Seleccionar evidencia tiene antecedentes próximos en evaluación de extracción web; NEXT-EVAL discute entradas congeladas y supervisión estructural para comparar reglas y LLM. Es un preprint sobre extracción de registros, no evidencia directa de rendimiento en noticias chilenas. [Kim, Kim y Jeong, 2025](https://arxiv.org/abs/2505.17125).

### 5.2 Corpus y partición

Mantener el objetivo del proyecto: **60 artículos de al menos tres universidades, 20 por universidad**. Se trata de una muestra exploratoria viable, no de una muestra nacional representativa ni de un cálculo de potencia estadística.

1. Elegir únicamente fuentes/URLs asignadas por el usuario; buscar variedad de estructura dentro de las disponibles. Registrar por qué se eligieron y sus limitaciones.
2. Definir una ventana de publicación antes de seleccionar artículos. Enumerar candidatos y registrar elegibilidad/exclusión, sin seleccionar por facilidad de extracción.
3. Identificar duplicados y versiones de una misma noticia antes de dividir. Todo grupo equivalente queda en una sola partición.
4. Formar 30 documentos de desarrollo y 30 de evaluación final, procurando 10/10 por universidad. Usar semilla `20261003` y guardar asignación explícita; la semilla sola no reproduce un inventario cambiante.
5. Ajustar perfiles/prompts/reglas solo con desarrollo. Congelar código, prompt, configuración y métricas antes de consultar resultados de la partición final.
6. Conservar casos difíciles: ausencia/ambigüedad de fecha, contenido extenso, listas, pies de foto e imágenes ausentes. Si no ocurren naturalmente, agregar fixtures sintéticos a las pruebas de robustez; no contarlos como noticias reales del corpus.

Si hay menos de tres universidades, declarar un piloto de menor alcance. Si hay menos de 60 documentos elegibles, documentar el inventario y acordar ampliación de ventana antes del experimento; no rellenar con noticias ficticias ni alterar el protocolo tras ver resultados.

HTML y anotaciones locales se guardan en `evaluation/corpus/`, actualmente ignorado por Git. Manifiestos sanitizados y documentación pueden versionarse; conservar contenido íntegro para evaluación solo según los permisos y reglas institucionales aplicables. No asumir que una URL pública autoriza redistribuir un corpus completo.

### 5.3 Anotación humana

La verdad de referencia se obtiene del artículo original, sin mostrar predicciones A/B al anotador:

- Título, cuerpo editorial completo y en orden, día/precisión de fecha, universidad, categoría y evidencia de cada campo.
- Conservar diferencias editoriales relevantes; definir tratamiento de subtítulos, listas, citas, pies de foto y textos repetidos en una guía previa.
- Fecha ausente: `null` y razón explícita; nunca tomar la fecha de captura.
- Capturar autoría de anotación mediante código de anotador y fecha, sin información personal innecesaria.
- Un segundo anotador revisa independientemente al menos 12 artículos, cuatro por universidad, seleccionados antes de ver resultados, además de los casos disputados. Reportar el conjunto aleatorio y los casos añadidos por separado.
- Reportar acuerdo previo a conciliación: coincidencia de título/fecha/categoría y F1 entre cuerpos; resolver desacuerdos con evidencia y conservar versiones originales. Si no hay segundo anotador, informar la limitación en vez de simular acuerdo.

`evaluation.annotate` genera una plantilla vacía. Sus campos nulos no son anotaciones completas ni se deben comparar como si fueran datos de referencia.

### 5.4 Ejecuciones y reproducibilidad

Por ejecución guardar `run_id`, `article_id`, método, estado, versión Git, hash del prompt/configuración/HTML, modelo devuelto, fecha UTC, latencia, llamadas, tokens reportados y motivo de fallo. No registrar API keys ni cabeceras de autorización.

Separar **replay offline** —respuestas archivadas, útil para reproducir evaluación— de **inferencia real** —necesaria para observar disponibilidad/latencia del proveedor—. Un replay no acredita rendimiento o cuota reales.

Hacer una ejecución principal por documento/método con el mismo límite fijado de reintentos. Conservar todos los intentos; no elegir la mejor respuesta. Como análisis de estabilidad, repetir tres veces diez documentos de desarrollo preseleccionados, sin tratarlos como 30 documentos independientes. Este ensayo no modifica el resultado primario de los 30 finales.

Planificar presupuesto de llamadas y ventana de cierre antes de empezar; los límites internos iniciales son 30/día y 5/minuto, no una garantía del proveedor. Al cierre, pendientes por cuota permanecen en el denominador de cobertura. Si el modelo no está disponible, mantener el experimento B no ejecutado y documentar la dependencia; no sustituirlo automáticamente.

## 6. Métricas y reglas de interpretación

| Dimensión | Definición y denominador | Interpretación |
|---|---|---|
| Cuerpo, primaria | Media de F1 por documento final; una predicción ausente vale 0 | Comparar B−A sobre pares idénticos |
| Título | Coincidencia exacta tras NFC y normalización de espacios / todos los documentos | No ocultar errores de tildes o reescritura |
| Fecha | Día/precisión correctos / documentos con fecha verificable | Informar también fecha fabricada cuando gold es nulo |
| Universidad | Identidad configurada correcta / todos los documentos | Integridad de configuración, no mejora atribuible al LLM |
| Categoría | Macro-F1 sobre etiquetas con soporte gold en la partición congelada; tabla por clase y soporte | Mantener clases/denominadores iguales entre métodos; no generalizar a categorías sin ejemplos |
| Cobertura | Predicciones válidas / documentos asignados | Reportar fallos, abstenciones y pendientes por separado |
| Evidencia | Bloques/campos seleccionados respaldados por el original / campos emitidos | Separar citas válidas de omisiones o selección editorial equivocada |
| Publicación segura | Noticias automáticamente publicadas correctas / todas las automáticamente publicadas | Si se publican 0: precisión indefinida, cobertura 0; nunca éxito perfecto |
| Cobertura de publicación | Noticias publicadas correctas / noticias elegibles según revisión humana | Evita un sistema que «acierta» absteniéndose siempre |
| Carga editorial | Pendientes de revisión / documentos asignados; tiempo humano por caso cuando se mida | Coste operacional del método |
| Latencia y consumo | Mediana/p95 de extracción y tiempo hasta entrega; llamadas/documento, tokens y cuota | Separar espera, caché y reintentos de tiempo de inferencia |
| Operación | Duplicados, pérdidas, conservación editorial y tiempo de recuperación por escenario | Cero pérdidas/duplicados en los escenarios ensayados, no garantía universal |
| Mostrador | Tareas completadas correctamente, tiempo, errores y necesidad de ayuda | Evaluación descriptiva de la muestra de usuarios |

F1 del cuerpo usa multiconjuntos de tokens normalizados: `O = suma(min(conteo_gold, conteo_pred))`, `P=O/tokens_pred`, `R=O/tokens_gold`, `F1=2PR/(P+R)` cuando el denominador es positivo. Si hay gold no vacío y no hay coincidencias, F1 es **0**. Gold vacío en un artículo supuestamente elegible es error de corpus; no se introduce como extracción perfecta.

El F1 de palabras no comprueba orden ni ausencia de párrafos omitidos. Complementarlo con exactitud de secuencia de bloques cuando haya gold de bloques y revisión de discrepancias contra texto original. No afirmar «cuerpo fiel» basándose solamente en bolsa de palabras.

Reportar diferencia media pareada y un intervalo exploratorio de 95% mediante bootstrap pareado de 2.000 remuestreos, semilla `20261003`, conservando pares A/B y estratos de universidad. Mantener juntos grupos duplicados si los hay. Esta es una elección del protocolo; interpretar incertidumbre condicionada a las fuentes elegidas. Tres universidades no bastan para inferir rendimiento de todas las plantillas del país. La elección de pruebas debe corresponder a métrica y diseño, como discuten [Dror et al., 2018](https://aclanthology.org/P18-1128/).

Si el intervalo cruza cero, comunicar evidencia inconclusa para la diferencia primaria, no equivalencia demostrada. Las métricas secundarias se reportan descriptivamente; no escoger a posteriori la única que favorezca B. Antes de una tesis confirmatoria más amplia, discutir tamaño muestral con el profesor guía usando variabilidad del piloto.

**Metas técnicas heredadas, no resultados:** título/universidad ≥95%, fecha ≥95% en casos verificables, F1 cuerpo ≥0,95, macro-F1 categoría ≥0,80 y cero hechos inventados publicados dentro del corpus. Estas metas son aceptación propuesta del proyecto, no prueba de superioridad ni condición de validez académica de una conclusión negativa. Con 30 noticias finales, un solo error cambia la proporción en 3,33 puntos porcentuales.

## 7. Evaluación operacional y del mostrador

**Operación:** ejecutar escenarios controlados con fixtures/MockTransport para reinicio tras guardar HTML, 429 del LLM, API caída, ACK perdido, 100 reenvíos, revisión antigua, bloqueo editorial, imagen tardía y archivo de noticia. Registrar entrada, acción, resultado esperado/observado y artefacto. Complementar con ensayo de Windows de 72 horas sin sesión; mocks y dry-run no sustituyen esa evidencia.

**Mostrador, funcional:** búsqueda, combinación de filtros, fecha editorial, paginación, actualización visible de 60 segundos, lectura abierta estable, acceso a fuente, imagen ausente y error de API. Borradores no son públicos y no hay noticias ficticias de respaldo.

**Mostrador, uso:** propuesta exploratoria de 6–8 personas adultas próximas al público objetivo, si hay acceso y conformidad con el procedimiento institucional. No se afirma suficiencia estadística. Cada persona realiza: encontrar una noticia de una universidad/categoría/periodo; identificar fecha y origen; leer el cuerpo y abrir la fuente. Límite propuesto: cinco minutos por tarea, fijado antes de medir; la ayuda del moderador queda registrada.

Usar el mismo conjunto controlado de noticias para todos, consentimiento, códigos de participante y resultados desidentificados. Registrar éxito correcto, tiempo, errores y comentarios; evitar recoger datos sensibles. Si se afirma ahorro frente a consultar portales, hace falta un comparador manual con tareas equivalentes y orden contrabalanceado; sin ese experimento solo se informa desempeño del mostrador.

Si no hay participantes, cerrar pruebas funcionales y declarar evaluación de uso no ejecutada; no reemplazar usuarios por agentes fingiendo que son personas. Verificar requisitos de comité/reglamento con el profesor guía antes de reclutar; este plan no presupone una norma institucional específica.

## 8. Amenazas a la validez

| Amenaza | Control y límite que se declara |
|---|---|
| Baseline incompleto | Implementar fecha/categoría deterministas y documentar esfuerzo de ajuste comparable |
| Fuga entre desarrollo/evaluación | Congelar splits por identidad/grupo; no ajustar tras mirar resultados finales |
| Sesgo de selección | Inventario y exclusiones trazables; universidades elegidas por alcance, no representación nacional |
| Referencia subjetiva | Guía, segundo anotador parcial, acuerdo y conciliación documentados |
| Métricas defectuosas | Tests de casos límite antes de cualquier informe; versión del evaluador congelada |
| Pérdida durante preprocesamiento | Gold desde original; distinguir fallo del parser de fallo de selección |
| Variación del proveedor | Registrar versión observada, fechas, reintentos y respuestas; no prometer determinismo remoto |
| Dependencia entre noticias | Agrupar duplicados; reportar resultados por fuente y alcance limitado del intervalo |
| Corpus pequeño/categorías escasas | Soporte por clase y universidad; no extrapolar a clases ausentes |
| Sesgo del desarrollador en usabilidad | Guion fijo, tareas objetivas, ayuda registrada y orden definido |
| Afirmación de originalidad excesiva | Contrastar literatura y atribuir módulos/librerías y trabajo previo |

## 9. Estructura propuesta de la memoria

| Capítulo | Contenido | Evidencia mínima |
|---|---|---|
| 1. Introducción | Problema, contexto chileno delimitado, preguntas, objetivos y alcance | Auditoría y referencias |
| 2. Marco teórico y trabajos relacionados | Scraping, extracción de contenido, LLM, evidencia, evaluación, sistemas recuperables | Matriz comparativa de literatura |
| 3. Metodología | DSR, corpus, variables, anotación, experimentos, métricas y amenazas | Protocolo previo a resultados |
| 4. Análisis y diseño | Requisitos, arquitectura, datos, estados, interfaces y decisiones | Diagramas, contratos y alternativas |
| 5. Implementación | Scraper, cola, API, imágenes, mostrador y administración | Versiones, fragmentos relevantes y pruebas |
| 6. Evaluación y resultados | A/B, fallos, operación y tareas de uso | Tablas/figuras generadas desde datos |
| 7. Discusión | Respuestas a PI1–PI4, compensaciones y comparación con literatura | Resultados, errores y límites |
| 8. Conclusiones y trabajo futuro | Cumplimiento de objetivos y mejoras justificadas | Matriz objetivo → evidencia → conclusión |
| Anexos | Guía de anotación, instrumentos, esquemas, manifiestos y reproducción | Material suficiente para auditoría |

La estructura se adapta al reglamento real cuando esté disponible. Escribir capítulos 1–5 mientras se desarrolla; escribir conclusiones y resumen final después de analizar resultados. No rellenar tablas con valores simulados sin marcarlos como ejemplos.

## 10. Literatura inicial verificada y búsqueda pendiente

Puntos de partida, no revisión exhaustiva:

- Peffers, Tuunanen, Rothenberger y Chatterjee (2007), *A Design Science Research Methodology for Information Systems Research*. Base para organizar construcción y evaluación del artefacto. [Publicación](https://doi.org/10.2753/MIS0742-1222240302).
- Barbaresi (2021), *Trafilatura: A Web Scraping Library and Command-Line Tool for Text Discovery and Extraction*. Antecedente de extracción de texto/metadata y evaluación comparativa; citarlo no implica sustituir el scraper propio. [ACL Anthology](https://aclanthology.org/2021.acl-demo.15/).
- Dror, Baumer, Shlomov y Reichart (2018), *The Hitchhiker’s Guide to Testing Statistical Significance in Natural Language Processing*. Apoya selección fundamentada de pruebas. [ACL Anthology](https://aclanthology.org/P18-1128/).
- Kim, Kim y Jeong (2025), *NEXT-EVAL: Next Evaluation of Traditional and LLM Web Data Record Extraction*. Preprint de referencia para comparación de extracción estructural. [arXiv](https://arxiv.org/abs/2505.17125).

Buscar literatura adicional con `web news content extraction evaluation`, `LLM evidence grounded extraction HTML`, `university news aggregation Chile` y `reliable web scraping data provenance`. Registrar biblioteca consultada, consulta, fecha, incluidos/excluidos y motivo. Incluir investigaciones con evaluación y documentos oficiales para tecnologías; distinguir artículos arbitrados, preprints y documentación.

Por trabajo registrar: problema, método, datos, métricas, limitaciones y relación concreta con UniNews. Verificar el texto completo antes de atribuir un hallazgo; las fichas/abstracts consultados para esta propuesta solo sustentan la descripción breve anterior. Buscar tesis comparables en repositorios institucionales cuando se conozca la universidad. No inventar autores, DOI o requisitos de citación.

## 11. Qué significa terminar la tesis

Una memoria defendible vincula cada objetivo con evidencia, explica decisiones de ingeniería y responde las preguntas con límites claros. No requiere que B gane ni que todas las metas propuestas se cumplan; sí requiere reportar fallos, justificar el alcance alcanzado y respetar los criterios institucionales que se confirmen.

Entregables: artefacto versionado, corpus/manifestación de acceso, protocolo, evaluador probado, resultados por artículo, análisis de errores, memoria, anexos reproducibles y demostración. Los datos restringidos pueden mantenerse fuera del repositorio público con instrucciones de acceso, sin afirmar reproducibilidad pública completa cuando no exista.
