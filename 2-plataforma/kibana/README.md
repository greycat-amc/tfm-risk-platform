# Dashboards de Kibana

`kibana-objects.ndjson` contiene los objetos guardados de Kibana (versión
8.15.3) que componen la capa de visualización del sistema.

## Contenido

Tres dashboards, con sus paneles embebidos (by value) y los data views que
utilizan:

- **Context-Prioritized Risk — Executive View**: vista ejecutiva del riesgo final
  por activo.
- **Context-Prioritized Risk — Technical Detail**: vista técnica con el detalle de
  riesgo por CVE, incluye el slopegraph (Vega) de reordenación de ranking.
- **WEB-01 — Empirical Validation (CVE-2021-41773)**: panel de la validación
  ofensiva sobre el activo WEB-01.

Data views incluidos (los cinco del sistema): `asset-final-risk`,
`technical-risk-cve`, `caldera-validation`, `epss-scores`, `asset-inventory-v1`.

## Importación

En Kibana: **Stack Management → Saved Objects → Import**, seleccionar el archivo
`kibana-objects.ndjson`. Los índices correspondientes deben existir
previamente (ver `../elasticsearch/mappings/`) y contener datos para que los
paneles muestren resultados.

## Nota

El slopegraph está implementado en Vega de forma estática. La interactividad
basada en `params` provoca errores de tipo *"Duplicate signal name"* en esta
versión, por lo que se mantiene la versión estática.
