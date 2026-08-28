# Plataforma

Implementación desplegable del sistema de priorización. Reúne la infraestructura,
la orquestación, el almacenamiento, la visualización y las utilidades de apoyo.

## Componentes

- **`infra/`** — despliegue con Docker Compose (Elasticsearch, Kibana, n8n, Caddy)
  y configuración del reverse proxy con PKI local.
- **`n8n/`** — workflows de orquestación:
  - `workflow-main.json`: pipeline principal de scoring.
  - `workflow-override.json`: override de criticidad (formulario, factor H).
  - `workflow-epss-ingest.json`: ingesta del dataset EPSS.
  - `workflow-kev-ingest.json`: ingesta del catálogo KEV de CISA.
- **`elasticsearch/`** — mappings de los cinco índices y consultas de referencia.
- **`kibana/`** — objetos guardados: dashboards y data views.
- **`scripts/`** — utilidades; `cpe_verify.py` verifica los CPE del inventario
  contra la API de NVD.

## Puesta en marcha

Las instrucciones completas de despliegue están en el
[README principal](../README.md). En resumen: levantar la infraestructura con
`docker compose up -d` desde `infra/`, crear los índices con los mappings de
`elasticsearch/mappings/`, importar los workflows en n8n y los objetos en Kibana.

## Nota sobre credenciales

Los workflows exportados contienen únicamente referencias a las credenciales
(identificador y nombre), no sus valores. Para reproducir el sistema es necesario
crear las credenciales correspondientes (Anthropic API y, opcionalmente, NVD API
key) dentro de la propia instancia de n8n.
