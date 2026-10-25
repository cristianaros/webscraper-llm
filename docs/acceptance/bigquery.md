# Aceptación de BigQuery y Analítica

Estado: `not_executed` (preparación local completada, pendiente de carga real por decisión del operador).

## Resumen

- Contratos analíticos y esquema NDJSON: implementados y verificados con tests (`NEWS_COLUMNS`).
- Generador de lotes inmutables y manifiesto: implementado en `analytics/exporter.py`.
- Integración transaccional con eventos (`AnalyticsOutbox`): verificado en migraciones `0004_analytics.py`.
- Sink y adaptador BigQuery: `analytics/bigquery_sink.py` implementa `render_merge_sql` y verificación de precedencia por `record_version`.
- La carga real requiere recursos GCP activos (dataset BigQuery y bucket GCS) configurados por el administrador.
