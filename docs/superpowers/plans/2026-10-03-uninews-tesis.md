# Tesis de Ingeniería Civil Informática con UniNews — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Ejecutar secuencialmente; usar agentes y revisión delegada solo cuando esa modalidad esté autorizada.

**Goal:** Desarrollar una tesis de Ingeniería Civil Informática que diseñe, complete y evalúe UniNews, con comparación reproducible de extracción por reglas y asistida por LLM, pruebas operacionales y evaluación del mostrador.

**Architecture:** Reutilizar el sistema existente y completar sus pendientes mediante el plan del producto. Mantener corpus, anotaciones, experimentos y análisis separados de las bases operacionales; ejecutar A y B sobre capturas idénticas y congeladas. Vincular cada objetivo de tesis con pruebas, resultados y un capítulo de la memoria.

**Tech Stack:** Stack actual de UniNews; Python y pytest para evaluación, JSON/CSV para datos y manifiestos, Markdown para protocolo/borradores. El formato final de la memoria se ajustará al reglamento institucional; no se instala LaTeX ni se crea una memoria completa durante esta planificación.

**Spec:** [Propuesta académica y protocolo de tesis](../specs/2026-10-03-uninews-tesis.md), junto con la [especificación del producto](../specs/2026-09-06-uninews-python-openrouter.md), [roles](../specs/2026-09-06-agent-roles.md) y [AGENTS.md](../../../AGENTS.md).

Fecha: 2026-10-03, America/Santiago. Carrera confirmada: Ingeniería Civil Informática. Plazo, institución y plantilla no especificados. **Estado: plan listo para revisión; tareas pendientes.**

## Global Constraints

- U01: El scraper se implementará en Python y no utilizará ScrapeGraphAI ni servicios de scraping por créditos.
- U02: El único modelo del flujo de extracción será `minimax/minimax-m3:free` mediante OpenRouter; no habrá sustitución automática por modelos de pago ni ejecución de un LLM local.
- U03: El recolector se ejecutará en Windows, en una máquina diferente del servidor de la web, API y base de datos central.
- U04: Las universidades y sus enlaces serán configurados por el administrador; el recolector no incorporará universidades descubiertas por su cuenta.
- U05: Cada noticia publicable tendrá título, cuerpo original, categoría, fecha de publicación, nombre de universidad y URL de origen.
- U06: La fecha de extracción nunca se presentará como fecha de publicación; una fecha ausente o inválida impedirá la publicación automática.
- U07: Los artículos descargados y sus pendientes sobrevivirán a reinicios, falta de cuota de OpenRouter y desconexiones de la API central.
- U08: La comunicación entre recolector y servidor se realizará mediante una API autenticada por HTTPS; no se compartirá un archivo SQLite entre máquinas.
- U09: Astro consultará las noticias publicadas mediante FastAPI; ninguna clave de OpenRouter o del recolector se incluirá en el frontend.
- U10: Una entrega repetida del mismo artículo no creará noticias duplicadas ni sobrescribirá una edición humana con una revisión antigua.
- U11: El plan y su implementación conservarán los datos existentes; las migraciones y la restauración se verificarán sobre copias.
- U12: Las pruebas automatizadas habituales no realizarán llamadas a OpenRouter ni a universidades reales.
- U13: Se extraerá la imagen principal cuando exista, conservando su origen y metadatos; una imagen ausente o fallida no se reemplazará por una imagen generada.
- U14: El desarrollo y las pruebas de aplicación se completarán primero localmente, sin exigir recursos Google Cloud; la carga real de datos a BigQuery será una etapa posterior.
- U15: BigQuery almacenará datos analíticos versionados y consultables, con carga repetible y seguimiento de publicaciones, cambios y archivos; no sustituirá la base operacional de la web.
- U16: Los agentes tendrán roles, propiedad de archivos, contratos de entrega y reglas de coordinación explícitos en AGENTS.md y en la especificación de agentes.

Reglas académicas de ejecución: no inventar datos/referencias/participantes; no usar evaluación final para ajustar; conservar intentos fallidos; distinguir metas de resultados y evidencia local de producción. El protocolo enlazado define métricas, denominadores y límites de interpretación.

## 1. Ruta de tesis y alcance

**Título propuesto:** «Diseño, implementación y evaluación de un sistema trazable de recopilación y visualización de noticias universitarias chilenas mediante scraping en Python y extracción asistida por un modelo de lenguaje».

**Pregunta central:** ¿Qué calidad, trazabilidad y confiabilidad logra UniNews y qué cambia al incorporar selección de evidencia mediante LLM frente a reglas deterministas?

La tesis tiene dos entregas relacionadas: **artefacto de ingeniería** —scraper y mostrador— y **evidencia académica** —corpus, comparación, evaluación y memoria—. Una web funcionando no sustituye la evaluación; una comparación aislada no acredita operación del sistema.

La metodología propuesta es Design Science Research con evaluación experimental pareada y validación funcional/operacional; su fundamento y fuentes están en el protocolo. La selección del método se revisa con el profesor guía, sin atribuirla a un reglamento no proporcionado.

## 2. Estado inicial y precauciones de medición

Al comenzar, Git solo mostraba como archivo no seguido el plan anterior `docs/superpowers/plans/2026-10-03-uninews-scraper-y-mostrador.md`. Se conserva sin sobrescribirlo.

Ya existen `collector/`, `backend/`, `src/`, `evaluation/` y tests. El [plan del producto](2026-10-03-uninews-scraper-y-mostrador.md) describe pendientes de integridad, recuperación, imágenes y filtros; no se presume que estén implementados.

Hallazgos que impiden usar directamente el evaluador actual para la tesis:

1. `body_scores('becas', 'deportes')` devuelve `precision=0`, `recall=0`, **`f1=1`**. Se reprodujo con el intérprete local en esta planificación. Debe devolver F1=0.
2. `compare.py` promedia sobre predicciones recibidas: omitir artículos puede inflar el resultado. No controla todos los duplicados, faltantes y denominadores requeridos.
3. `baseline_extract` solo entrega título/cuerpo; comparar su ausencia de fecha/categoría contra B sería una comparación incompleta.
4. `annotate` genera campos gold nulos y `schema.json` solo enumera algunas claves; falta una validación suficiente de corpus final.

No se corrigió código en esta sesión ni se ejecutó la suite completa. Primero se planifica; P4–P5 fijan esos instrumentos antes de medir.

## 3. Archivos y responsabilidades

| Propiedad secuencial | Archivos a crear | Archivos existentes a modificar al ejecutar |
|---|---|---|
| Tesista + profesor guía | `thesis/brief.md`, `thesis/requirements.md`, `thesis/literature.csv`, `thesis/references.bib` | Protocolo académico si cambia una decisión |
| Corpus/anotación | `thesis/annotation-guide.md`, `thesis/corpus-decisions.csv`, `evaluation/corpus/manifest.json`, `evaluation/corpus/gold.json`, `evaluation/corpus/sources.json` | `evaluation/schema.json`, `evaluation/annotate.py`, `evaluation/README.md` |
| Instrumentos experimentales | `evaluation/validate.py`, `evaluation/run_experiment.py`, `evaluation/baseline.py`, `evaluation/baseline_rules.json`, `evaluation/statistics.py` | `evaluation/metrics.py`, `evaluation/compare.py` |
| QA de instrumentos | `tests/unit/test_evaluation_validation.py`, `tests/unit/test_evaluation_compare.py`, `tests/unit/test_experiment_runner.py`, `tests/unit/test_evaluation_statistics.py` | `tests/unit/test_evaluation_metrics.py` |
| Operación y uso | `thesis/operations-protocol.md`, `thesis/usability-protocol.md`, `thesis/acceptance.md` | Tests/API/UI del plan de producto bajo su propietario |
| Memoria y reproducción | `thesis/chapters/01-introduction.md` hasta `08-conclusions.md`, `thesis/reproduce.md`, `thesis/defense.md` | README con enlace a entregables finales |

Resultados no versionados: `artifacts/thesis/runs/`, `artifacts/thesis/reports/`, `artifacts/thesis/figures/`, `artifacts/thesis/usability/`. Ya están bajo patrones ignorados. Definir backup y acceso controlado; «ignorado por Git» no significa «respaldado».

No crear todos esos archivos vacíos ahora. Cada tarea crea únicamente lo que necesita. `evaluation/` es propiedad de este plan al ejecutarlo: coordinar su entrega con T10 del plan de producto para no implementar dos evaluadores ni editar el mismo archivo simultáneamente.

## 4. Hitos y secuencia

| Hito | Tareas | Condición de salida |
|---|---|---|
| H1. Propuesta | P1–P2 | Problema, objetivos y metodología revisados |
| H2. Artefacto/corpus | P3 y trabajo técnico del producto | Versión evaluable, corpus anotado y split congelado |
| H3. Instrumentos | P4–P5 | Métricas y runner probados; baseline completo |
| H4. Evidencia | P6–P8 | Comparación, operación y uso con resultados o límites explícitos |
| H5. Memoria | P9–P10 | Conclusiones trazables y paquete de defensa reproducible |

Dependencias: P1 → P2 → P3; P4 puede avanzar con fixtures mientras se anota P3; P5 requiere P4 y los contratos del producto; P6 requiere P3–P5 y protocolo congelado. P7–P8 requieren artefacto integrado. P9 se redacta progresivamente y se completa después de P6–P8; P10 cierra.

### P1. Formalizar la propuesta y los objetivos

**Files:** crear `thesis/brief.md`, `thesis/requirements.md`.

**Entradas/salidas:** consumir PI1–PI4 y OE1–OE6 del protocolo; producir una propuesta breve y matriz `objetivo, requisito, evidencia, criterio, capítulo, estado`.

- [ ] Registrar fecha límite, plantilla, extensión, estilo de cita y condiciones de evaluación cuando se obtenga el reglamento. Hasta entonces indicar «no especificado» como dato de contexto, sin inventar exigencias.
- [ ] Redactar problema en una página, separando observaciones auditadas de supuestos. Describir quién consulta noticias y qué tareas realiza.
- [ ] Copiar y ajustar título, pregunta y objetivos del protocolo; excluir afirmaciones de superioridad o cobertura nacional que no se probarán.
- [ ] Definir la contribución: artefacto trazable, comparación controlada y evidencia de límites. Relacionar cada una con un objetivo y entregable.
- [ ] Revisar con el profesor guía el alcance académico y registrar fecha/acuerdos; no sustituir una revisión real por una afirmación de aprobación.
- [ ] Verificar que los seis objetivos tienen criterio observable y que BigQuery/cloud no bloquean los experimentos locales.
- [ ] Commit de ejecución: `docs: define thesis problem objectives and scope`, solo con las dos rutas de esta tarea.

**Cierre:** propuesta que distingue construcción, investigación y evaluación; ningún objetivo depende de demostrar un resultado favorable.

### P2. Construir antecedentes y justificar decisiones

**Files:** crear `thesis/literature.csv`, `thesis/references.bib`, `thesis/chapters/02-background.md`.

**Entradas/salidas:** consumir las cuatro referencias iniciales del protocolo; producir matriz con `id,title,authors,year,url,type,problem,method,data,metrics,limitations,relevance,read_status`.

- [ ] Ejecutar las búsquedas del protocolo en bibliotecas académicas y repositorios institucionales; registrar consultas y fecha. La lista inicial no es una revisión exhaustiva.
- [ ] Leer cada publicación antes de atribuir un resultado y completar la matriz; etiquetar explícitamente preprints y documentación técnica.
- [ ] Comparar reglas, extracción de contenido y selección asistida: qué extraen, sobre qué datos y cómo miden. No trasladar sus porcentajes a UniNews.
- [ ] Redactar la brecha acotada: evaluación de esta arquitectura y fuentes chilenas seleccionadas con evidencia y restricciones operacionales. No afirmar inexistencia universal de soluciones.
- [ ] Justificar Python propio, separación del recolector, evidencia por bloques, cola durable y revisión humana usando requisitos y alternativas.
- [ ] Revisar citas una a una: autor/año/título/DOI corresponden y cada afirmación enlaza su evidencia; generar BibTeX desde metadatos verificados.
- [ ] Commit: `docs: establish thesis related work and design rationale` con las tres rutas explícitas.

**Cierre:** antecedente → diferencia de UniNews → experimento que la examina; referencias verificables.

### P3. Construir y congelar corpus y anotación

**Files:** crear guía, decisiones y los tres archivos de corpus del mapa; modificar `evaluation/annotate.py`, `evaluation/schema.json`; crear `evaluation/validate.py`, `tests/unit/test_evaluation_validation.py`.

**Interfaces nuevas:** `validate_index(records: list[dict]) -> None` verifica identidades/particiones; `validate_corpus(records: list[dict], sources: dict) -> None` valida gold, evidencia, hashes y fuentes; `python -m evaluation.validate --corpus RUTA --sources RUTA` retorna 0 si es válido, 1 con errores identificados por artículo. Sin consultas de red.

- [ ] Asignar fuentes con el usuario; auditar estructura, fechas, navegación e imágenes. Conservar URLs descartadas y motivo antes de observar resultados A/B.
- [ ] Completar guía: cuerpo editorial, subtítulos/listas/citas, pies de foto, categoría, fecha ausente y contenido repetido. Probarla con seis artículos de desarrollo y corregir ambigüedades antes de anotar el final.
- [ ] Crear prueba para impedir fuga de un documento entre particiones:

```python
import pytest
from evaluation.validate import validate_index

def test_duplicate_document_cannot_cross_splits():
    rows = [
        {"article_id": "u1-01", "group_id": "story-1", "split": "development"},
        {"article_id": "u1-02", "group_id": "story-1", "split": "test"},
    ]
    with pytest.raises(ValueError, match="group_crosses_splits"):
        validate_index(rows)
```

- [ ] Ejecutar `python -m pytest tests/unit/test_evaluation_validation.py -q`; inicialmente falla porque el validador no existe. Implementar el núcleo:

```python
def validate_index(records: list[dict]) -> None:
    seen, groups = set(), {}
    for row in records:
        ident, group, split = row["article_id"], row["group_id"], row["split"]
        if ident in seen:
            raise ValueError("duplicate_article_id")
        if split not in {"development", "test"}:
            raise ValueError("invalid_split")
        if group in groups and groups[group] != split:
            raise ValueError("group_crosses_splits")
        seen.add(ident)
        groups[group] = split
```

- [ ] Ampliar esquema/validador para `article_id`, `group_id`, `university_id`, `source_id`, `source_url`, `captured_at`, `html_sha256`, `document_hash`, `split`, `gold`, `annotation_notes`; gold incluye título/cuerpo/categoría/fecha/precisión e institución. Verificar identidad en fuentes, hash del archivo original, fecha ISO o nula razonada, categoría del catálogo y cuerpo no vacío. Agregar tests específicos de cada rechazo.
- [ ] Capturar 60 documentos elegibles, dividir 30/30 con 10 por universidad en cada partición cuando sea posible; registrar manifiesto exacto, semilla y hashes. Congelar configuración de fuente y HTML/render capturado.
- [ ] Anotar sin predicciones; revisar 12 documentos con segundo anotador según protocolo y registrar desacuerdos/conciliación. No usar la salida nula de `annotate` como gold.
- [ ] Reejecutar pruebas y CLI de validación; respaldar corpus fuera de Git y registrar ubicación de acceso. Commit solo de guía, decisiones sanitizadas, esquema, validador y tests, nunca secretos o contenido restringido.

**Cierre:** corpus válido, particiones inmutables y anotaciones trazables; si falta acceso a fuentes/anotador, el límite queda explícito.

### P4. Reparar y probar el evaluador antes de medir

**Files:** modificar `evaluation/metrics.py`, `evaluation/compare.py`, `tests/unit/test_evaluation_metrics.py`; crear `tests/unit/test_evaluation_compare.py`.

**Interfaces:** conservar `body_scores(expected: str, actual: str) -> dict[str,float]`; extender `compare(corpus: Path, predictions: Path, *, split: str = "test") -> dict`. La CLI agrega `--split development|test`, por defecto `test`; no mezcla ajuste/evaluación.

- [ ] Añadir y ejecutar regresiones reales:

```python
import pytest
from evaluation.metrics import body_scores

@pytest.mark.parametrize("gold,predicted", [
    ("becas", "deportes"), ("becas", ""), ("", "deportes"),
])
def test_zero_overlap_is_never_perfect(gold, predicted):
    assert body_scores(gold, predicted)["f1"] == 0.0

def test_repeated_words_count_and_order_is_not_claimed():
    assert body_scores("becas becas", "becas")["recall"] == 0.5
    assert body_scores("becas campus", "campus becas")["f1"] == 1.0
```

- [ ] Corregir la fórmula: `f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0`. Usar precisión/recobrado 0 cuando su denominador sea 0. Gold vacío de artículos se rechaza en el validador; el caso vacío/vacío no otorga 1 por defecto.
- [ ] Iterar sobre IDs gold de la partición, no sobre predicciones. Duplicado o ID desconocido es error; faltante produce estado `missing`, métricas de extracción 0 y permanece en cobertura. `None == None` nunca acredita una fecha extraída correctamente.
- [ ] Añadir prueba con dos artículos gold, una predicción perfecta y una ausente: `expected_articles=2`, `valid_predictions=1`, `coverage=0.5`, `title_accuracy=0.5`, `body.f1=0.5`. Añadir ambos ausentes, todos fallidos, fecha gold nula y predicción fabricada.
- [ ] Definir normalización NFC/espacios para título, tokens casefold para F1 y orden de bloques como control separado; no borrar tildes o puntuación del título para ocultar errores. Probar texto repetido, Unicode y omisión de párrafo.
- [ ] Calcular matriz/confusión y macro-F1 sobre las mismas etiquetas con soporte gold; validar longitudes antes de `zip`, reportar soporte por clase e instituciones. Devolver `null` para razón sin denominador, junto a sus conteos.
- [ ] Guardar por artículo: corrección de título/fecha/institución/categoría, P/R/F1 cuerpo, respaldo de evidencia y estado. Agregar total de llamadas, latencias disponibles, pendientes y revisión. No inferir costos monetarios si el proveedor no los informó.
- [ ] Ejecutar `python -m pytest tests/unit/test_evaluation_metrics.py tests/unit/test_evaluation_compare.py -q`. Commit: `fix: make thesis evaluation resistant to missing and invalid predictions` con rutas explícitas.

**Cierre:** casos límite comprobados y denominadores auditables; no se reutilizan resultados anteriores al arreglo como resultados finales.

### P5. Implementar runner reproducible y baseline completo

**Files:** crear `evaluation/run_experiment.py`, `evaluation/baseline.py`, `evaluation/baseline_rules.json`, `tests/unit/test_experiment_runner.py`; modificar `evaluation/README.md`.

**Interfaces:** `extract_baseline(doc: Document, source: SourceConfig, rules: dict) -> ArticleFields`; `run_experiment(corpus_path: Path, sources_path: Path, method: str, split: str, output_dir: Path, *, extractor=None) -> Path`. Devuelve ruta de predicciones; `extractor` inyectado permite fixtures. CLI con `--method rules|minimax`, `--split development|test`, `--corpus`, `--sources`, `--output`, `--mode replay|live` y `--env` solo para live.

- [ ] Definir predicción por artículo: `article_id`, `method`, `status` (`ok`, `failed`, `pending`, `review`), `title`, `body`, `category`, `published_on`, `date_precision`, `university_id`, `evidence_ids`, `error_code`, `attempts`, `llm_calls`, `latency_ms`, `tokens_input`, `tokens_output`. Nulos no medidos permanecen nulos, no 0 inventado.
- [ ] Guardar manifiesto por ejecución con versión Git, cambios locales/hash, hashes corpus/fuentes/reglas/prompt, método, split, modelo solicitado/devuelto, fecha, límites de reintento y modo. No incluir gold ni anotaciones dentro del payload enviado al extractor.
- [ ] Completar baseline: título/cuerpo desde bloques, fecha mediante funciones deterministas de `shared/validation.py` y reglas de categoría fijadas en JSON con orden de prioridad y fallback `General`. No modificar el baseline operacional si la extensión solo es experimental; usar adaptador en `evaluation/baseline.py`.
- [ ] Probar con un extractor fake cuyo `extract(doc)` contabiliza invocaciones y lanza un error controlado para un documento: el runner genera una fila fallida, no la omite, y no accede a gold. Probar que reanudar no repite una respuesta archivada ni cambia su intento principal.
- [ ] Construir `Document` desde la captura y configuración congeladas usando `build_document`; comprobar hash contra manifiesto. Pasar el mismo documento a A y B. Separar errores del parser de errores del modelo.
- [ ] Mantener replay como modo por defecto; live requiere invocación explícita, configuración y los límites del collector. Guardar respuesta antes de evaluarla y contar todos los intentos. No sustituir modelo ni publicar resultados experimentales en la API operacional.
- [ ] Ensayar en desarrollo; ejecutar `python -m pytest tests/unit/test_experiment_runner.py -q`. Commit: `feat: add paired reproducible thesis experiment runner` con archivos de esta tarea.

**Cierre:** ambos métodos producen el mismo contrato, la misma muestra y denominadores; el baseline no pierde por carecer de funciones que se pretende comparar.

### P6. Ejecutar comparación y analizar incertidumbre

**Files:** crear `evaluation/statistics.py`, `tests/unit/test_evaluation_statistics.py`; resultados bajo `artifacts/thesis/`; borrador `thesis/chapters/06-results.md`.

**Interfaces:** `paired_body_interval(rows: list[dict], *, seed: int = 20261003, repeats: int = 2000) -> dict` consume `article_id,university_id,a,b`, donde a/b son F1 por documento; devuelve `delta,ci_low,ci_high,n`. CLI de estadísticas consume dos reportes de `compare`, alinea por ID y exige mismo conjunto gold/split/hash.

- [ ] Congelar manifiesto de experimento, código, prompt, criterios y plazo de cierre. Registrar cuáles metas y análisis son principales/secundarios antes de consultar el conjunto final.
- [ ] Añadir prueba con pares iguales: delta e intervalo exactamente 0; segunda prueba con B mayor en todos los pares y resultado reproducible con misma semilla.
- [ ] Implementar bootstrap estratificado pareado, después de exigir IDs únicos y eliminar duplicados editoriales en la construcción del corpus:

```python
from collections import defaultdict
from random import Random
from statistics import mean

def paired_body_interval(rows, *, seed=20261003, repeats=2000):
    if not rows or repeats < 100:
        raise ValueError("insufficient_bootstrap_input")
    if len({r["article_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate_article_id")
    groups = defaultdict(list)
    for row in sorted(rows, key=lambda r: r["article_id"]):
        groups[row["university_id"]].append(row["b"] - row["a"])
    rng, samples = Random(seed), []
    for _ in range(repeats):
        draw = []
        for key in sorted(groups):
            values = groups[key]
            draw.extend(rng.choice(values) for _ in values)
        samples.append(mean(draw))
    samples.sort()
    return {"delta": mean(r["b"] - r["a"] for r in rows),
            "ci_low": samples[int((repeats - 1) * .025)],
            "ci_high": samples[int((repeats - 1) * .975)], "n": len(rows)}
```

Si se retienen varias noticias del mismo grupo editorial, sustituir remuestreo de artículos por remuestreo de grupos completos antes del experimento; no aplicar el código anterior como si esos artículos fueran independientes.

- [ ] Ejecutar runner para A/B en desarrollo; revisar que artifacts/manifiestos/denominadores coinciden. Recién después ejecutar `--split test`, una sola corrida principal por documento/método; conservar errores y cuota.
- [ ] Ejecutar comparación offline desde cada archivo de predicciones, por ejemplo:

```powershell
.\.venv\Scripts\python.exe -m evaluation.compare --corpus evaluation/corpus/gold.json --predictions artifacts/thesis/runs/rules/predictions.json --split test --output artifacts/thesis/reports/rules.json
.\.venv\Scripts\python.exe -m evaluation.compare --corpus evaluation/corpus/gold.json --predictions artifacts/thesis/runs/minimax/predictions.json --split test --output artifacts/thesis/reports/minimax.json
```

- [ ] Generar tablas por método y universidad, diferencias pareadas y errores; revisar contra casos originales. No promediar desarrollo con evaluación final, ni contabilizar repeticiones como nuevos artículos.
- [ ] Informar métricas observadas, intervalos exploratorios y limitaciones; incluir B inferior, igual o inconcluso si eso muestran los datos. Separar validez del texto de decisión correcta de publicación.
- [ ] Ejecutar tests estadísticos locales; commit solo de código/tests/borrador con resultados derivados y sanitizados. Datos de runs permanecen respaldados fuera de Git conforme al protocolo.

**Cierre:** resultados verificables y discusión proporcional a la muestra, sin selección de mejores intentos o métricas.

### P7. Acreditar ingeniería y operación del sistema

**Files:** crear `thesis/operations-protocol.md`, `thesis/acceptance.md`; consumir pruebas/entregas T2–T10 del plan de producto.

**Entradas/salidas:** API/collector/web integrados; producir matriz `escenario,precondición,acción,esperado,observado,evidencia,estado` y trazabilidad OE2/OE5.

- [ ] Ejecutar las tareas técnicas del plan de producto necesarias para publicación íntegra, cola, cuota, imágenes, fuentes y mostrador. No marcar «implementado» por la existencia del plan.
- [ ] Ejecutar pruebas de fallos del protocolo con datos temporales: 429, reinicio, API caída, ACK perdido, reenvío, revisión antigua, edición humana e imagen tardía. Medir pendientes/IDs antes y después.
- [ ] Probar restauración de copia SQLite/medios y conservación de IDs; no restaurar sobre una base activa.
- [ ] Ejecutar checks del producto y pruebas de navegador. Vincular resultados específicos en la matriz de requisitos y guardar commit/ambiente.
- [ ] Completar ensayo real Windows de 72 horas con registro de tareas, interrupciones y recuperación. Un dry-run o test simulado queda reportado con su alcance limitado.
- [ ] Preparar lote analítico local sin GCP, solo para probar independencia del sistema; mantener carga BigQuery/despliegue como no ejecutados si no pertenecen al alcance acordado.
- [ ] Commit: `docs: record thesis operational evidence` con protocolo y aceptación, sin logs con secretos.

**Cierre:** el capítulo de ingeniería tiene evidencia de confiabilidad, no solo capturas de una web funcionando.

### P8. Evaluar tareas del mostrador con usuarios

**Files:** crear `thesis/usability-protocol.md`; datos desidentificados en `artifacts/thesis/usability/`; resultados en capítulo 6.

**Interfaces de evidencia:** CSV con `participant_id,task_id,condition,order,success,seconds,errors,assistance,notes`; una fila por tarea/persona. No incluir nombres, correos ni identificadores institucionales.

- [ ] Confirmar procedimiento institucional antes de reclutar; preparar consentimiento y guion con tareas y límite de cinco minutos del protocolo.
- [ ] Seleccionar 6–8 adultos próximos al público objetivo como muestra exploratoria; registrar criterio de inclusión y sin inferir representatividad.
- [ ] Ensayar el guion con una persona piloto, ajustar antes de la muestra final y mantener su resultado separado.
- [ ] Ejecutar búsqueda por universidad/categoría/fecha, identificación de origen y lectura. Registrar corrección, tiempo y ayuda; evitar enseñar la respuesta durante la tarea.
- [ ] Analizar conteos de éxito, mediana/rango temporal, errores frecuentes y comentarios. Con pocas personas, priorizar descripción e incidencias reproducibles.
- [ ] Si se mide ahorro frente a portales, usar conjuntos de tareas equivalentes, repartir orden A→B/B→A y registrar aprendizaje; de lo contrario eliminar afirmaciones de ahorro de tiempo de la memoria.
- [ ] Registrar evaluación no ejecutada si no hay participantes; no reemplazar personas por bots ni inventar encuestas. Commit del protocolo y síntesis anónima.

**Cierre:** evidencia de tareas reales o limitación explícita; los tests de interfaz no se presentan como satisfacción de usuarios.

### P9. Redactar memoria y discutir los hallazgos

**Files:** crear/completar `thesis/chapters/01-introduction.md`, `02-background.md`, `03-methodology.md`, `04-design.md`, `05-implementation.md`, `06-results.md`, `07-discussion.md`, `08-conclusions.md`.

**Entradas/salidas:** protocolo + literatura + evidencia; producir capítulos según estructura de la especificación, adaptados después a la plantilla real.

- [ ] Redactar introducción/antecedentes/metodología durante P1–P5 y distinguir sistema heredado de contribuciones de esta tesis.
- [ ] Documentar arquitectura, decisiones, estados, modelo de datos y contratos. Incluir alternativas descartadas con motivo medible, no una lista de tecnologías.
- [ ] Describir implementación mediante los cambios relevantes y su validación; citar librerías y reconocer colaboración/asistencia según las reglas académicas aplicables.
- [ ] Insertar tablas/figuras generadas desde reportes finales. Mantener valores y denominadores iguales entre texto, anexos y presentación.
- [ ] Responder PI1–PI4 explícitamente, explicar errores por etapa y confrontar la literatura sin comparar porcentajes de datasets incompatibles como si fueran el mismo experimento.
- [ ] Completar matriz OE1–OE6 con evidencia y grado de cumplimiento. Reportar objetivos parciales y restricciones de fuente/modelo/muestra.
- [ ] Escribir conclusiones y resumen al final; evitar «100% confiable», «cubre Chile» o «la IA mejora» si la evidencia no lo demuestra.
- [ ] Revisar con el profesor guía por capítulos; conservar observaciones/resolución y commits pequeños con rutas explícitas.

**Cierre:** cada conclusión tiene soporte y cada objetivo una respuesta, incluso cuando el resultado sea negativo.

### P10. Preparar reproducción y defensa

**Files:** crear `thesis/reproduce.md`, `thesis/defense.md`; completar `thesis/acceptance.md`.

**Entradas/salidas:** versión congelada, entorno y artifacts; producir instrucciones verificadas, guion de defensa y demostración estable.

- [ ] Documentar desde entorno limpio cómo instalar dependencias resueltas, validar corpus permitido, ejecutar replay y regenerar métricas. Aclarar qué datos requieren acceso privado y qué requiere OpenRouter real.
- [ ] Verificar que replay reproduce las tablas a partir de respuestas archivadas sin red; regeneración numérica no implica reproducción exacta de una API futura.
- [ ] Preparar demostración con datos identificados como muestra de evaluación, errores controlados y backend local; no depender de cuota en vivo para la defensa.
- [ ] Estructurar presentación: problema, pregunta, aporte, arquitectura, método, resultados, límites y conclusión. Duración se ajusta a la regla real de defensa.
- [ ] Ensayar preguntas: por qué LLM, por qué no basta reglas, cómo se evitó inventar fechas, cómo se midió fidelidad, qué ocurre con cuota, qué generaliza y qué no.
- [ ] Revisar referencias, permisos de anexos, ausencia de secretos y coherencia de números. No publicar corpus o datos de participantes por el solo hecho de terminar la tesis.
- [ ] Entregar inventario de versión/código, memoria, reportes, corpus o manifiesto de acceso, scripts, limitaciones y fases del producto pendientes.

**Cierre:** material defendible y reproducible dentro del acceso declarado. La calificación/aprobación corresponde al procedimiento institucional, no a una marca automática del plan.

## 5. Cronograma orientativo de doce semanas

Propuesta relativa, no fecha de entrega comprometida. Ajustar a plazo/dedicación real y disponibilidad de fuentes, anotador y participantes. Escritura y revisión acompañan el trabajo técnico; no se dejan completas para la última semana.

| Semana | Foco | Entrega |
|---|---|---|
| 1 | P1, auditoría inicial y acuerdos | Propuesta y objetivos |
| 2 | P2, fuentes y guía de anotación | Matriz bibliográfica y protocolo |
| 3–4 | P3 y correcciones del producto | Corpus anotado, manifiesto y artefacto avanzando |
| 5 | P4–P5 | Métricas, baseline y runner probados |
| 6 | Desarrollo, revisión de instrumentos | Protocolo/código congelados |
| 7 | P6 | Experimento final y resultados brutos |
| 8 | P7, incluyendo 72 horas reales | Evidencia de operación |
| 9 | P8 | Resultados de tareas del mostrador |
| 10 | P9 | Borrador integral y discusión |
| 11 | P9–P10 | Correcciones del guía y reproducción |
| 12 | P10 | Memoria final y ensayo de defensa |

Riesgos que desplazan el calendario: cambios de fuentes, cuota/modelo indisponible, acceso a segundo anotador, reclutamiento y observaciones del profesor guía. Recortar cloud/chat/extensiones antes que eliminar la calidad del corpus o manipular la evaluación.

## 6. Revisión y entrega de esta planificación

Cobertura: OE1→P1–P2; OE2→P7/plan de producto; OE3→P3; OE4→P4–P6; OE5→P7–P8; OE6→P9–P10. Protocolo §§5–6 define comparación y métricas; §7 define operación/uso; §8 amenazas; §9 capítulos; §10 literatura inicial.

Esta tarea crea únicamente el plan y la propuesta/protocolo. No corrige producción, no captura portales, no consulta OpenRouter, no recluta participantes ni fabrica resultados. La reproducción puntual del defecto F1 está documentada como diagnóstico, no como ejecución de la tesis.

Validación realizada el 2026-10-03: 16 restricciones U idénticas al documento de producto, diez tareas, enlaces locales resueltos, bloques Markdown cerrados, cuatro fragmentos Python analizados con AST y un bloque PowerShell analizado sin errores. Los ejemplos de partición y bootstrap se comprobaron en memoria, incluyendo fuga entre splits, pares iguales, mejora conocida y reproducibilidad frente al orden de entrada. No se ejecutó la suite de producto ni se midió ninguna noticia real.

Modalidades posteriores: ejecución por tareas en esta sesión con `executing-plans`, o delegación autorizada con propiedad de archivos y revisión entre entregas. Las decisiones académicas se revisan con el profesor guía; no se inicia esa ejecución automáticamente.
