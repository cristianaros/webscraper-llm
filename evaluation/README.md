# Evaluación local (AC10)

La evaluación es offline y no llama a OpenRouter. Conserve HTML capturado y anotaciones humanas; `gold` nunca se deriva de predicciones.

```powershell
python -m evaluation.annotate --documents corpus/documents.json --output corpus/annotations.json
python -m evaluation.compare --corpus corpus/annotations.json --predictions corpus/predictions.json --output artifacts/metrics.json
```

Reporte denominadores, versión de prompt/modelo, fuente, split, errores, tiempos y pendientes de cuota. Menos de tres universidades es solo un piloto y no demuestra generalización.
