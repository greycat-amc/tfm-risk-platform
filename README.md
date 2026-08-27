# tfm-risk-platform

**Evaluación de la superficie de exposición: un modelo de priorización de vulnerabilidades sensible al contexto del activo**

Trabajo Fin de Máster — Máster en Ciberseguridad.

Plataforma de evaluación de riesgo que integra fuentes de vulnerabilidad (NVD, EPSS, KEV) con el contexto de los activos y reordena la prioridad de remediación **a nivel de activo**, no de vulnerabilidad. El modelo es explícito, trazable y reproducible.

> **Aviso**: todos los datos de inventario, topología y escenario son **ficticios** (PYME de e-commerce en migración a la nube) y se emplean con fines exclusivamente académicos. No representan infraestructura real.

## Pregunta de investigación

Los escáneres comerciales tienden a priorizar puntuando **vulnerabilidades** en lugar de **activos**. Dos activos que comparten el mismo CVE —y por tanto el mismo riesgo técnico— reciben la misma prioridad, aunque su relevancia para el negocio y su radio de impacto sean distintos.

Este trabajo propone un modelo de priorización **sensible al contexto del activo**: un modelo auditable que reordena el riesgo a nivel de activo y produce rankings distintos para activos que comparten CVE idénticos y una misma puntuación de riesgo técnico. La contribución no reside en la novedad de incorporar contexto —las plataformas comerciales ya lo hacen de forma opaca— sino en su **auditabilidad y explicitud**.

## Arquitectura

El sistema se despliega con Docker Compose e integra cuatro servicios sobre una red interna:

- **Elasticsearch 8.15.3** — almacenamiento e indexación de inventario y riesgo.
- **Kibana 8.15.3** — visualización (dashboards, slopegraph, tablas comparativas).
- **n8n** — orquestación del pipeline de scoring.
- **Caddy 2** — reverse proxy con PKI local (HTTPS para n8n y Kibana).

El pipeline recupera el inventario, consulta NVD por CPE, enriquece cada CVE con EPSS y KEV, calcula el riesgo técnico por CVE, aplica el factor de contexto por activo y persiste el resultado. Un nodo de IA (Anthropic) genera la técnica MITRE ATT&CK asociada, la remediación y el `priority_rationale`.

El detalle completo del pipeline nodo a nodo está en [`docs/arquitectura.md`](docs/arquitectura.md).

## Modelo de scoring

**Riesgo técnico (por CVE):**

```
TR = 0.40 * CVSS_norm + 0.35 * EPSS_norm + 0.25 * KEV_norm
```

**Factor de contexto (por activo):**

```
CF = 0.30 * Exposure_norm
   + 0.20 * (1 + H) * Criticality_norm
   + 0.20 * (1 - H) * ModuleSensitivity_norm
   + 0.30 * BlastRadius_norm
```

**Riesgo final:**

```
FinalRisk = TR_top * (1 + CF) / 2      (rango [0, 1])
```

El factor **H** es binario: con `criticality_overridden = true` (H = 1) la criticidad duplica su peso y la sensibilidad del módulo se anula. El override se declara mediante un formulario (n8n Form Trigger).

**Umbrales de clasificación:**

| Nivel   | Rango            |
|---------|------------------|
| CRÍTICO | FinalRisk ≥ 0.80 |
| ALTO    | FinalRisk ≥ 0.60 |
| MEDIO   | FinalRisk ≥ 0.40 |
| BAJO    | FinalRisk < 0.40 |

El desarrollo completo del modelo está en [`docs/formula-scoring.md`](docs/formula-scoring.md).

### Diferenciación contextual (resultado central)

DC-01 y JMP-01 comparten CVE (CVE-2025-59287) y riesgo técnico (TR = 0.9918), pero producen FinalRisk distintos (0.883 vs 0.846) por el diferente radio de impacto de sus módulos. Un escáner que puntúa vulnerabilidades asignaría idéntica prioridad; el modelo contextual los diferencia de forma auditable.

## Puesta en marcha

### Requisitos

- Docker y Docker Compose.
- Al menos 4 GB de RAM disponibles para Elasticsearch.
- Entradas en `/etc/hosts` para `n8n.local` y `kibana.local` apuntando al host de Docker.

### Pasos

1. Clonar el repositorio:

   ```
   git clone https://github.com/greycat-amc/tfm-risk-platform.git
   cd tfm-risk-platform
   ```

2. Copiar la plantilla de entorno y revisar los valores:

   ```
   cp .env.example .env
   ```

3. Levantar la infraestructura:

   ```
   cd infra
   docker compose up -d
   ```

4. Crear los índices en Elasticsearch aplicando los mappings de [`elasticsearch/mappings/`](elasticsearch/mappings/).

5. Cargar el inventario de activos ([`data/inventario-21-activos.json`](data/)) en el índice `asset-inventory-v1`.

6. Ingerir el dataset EPSS ejecutando el flujo `workflow-epss-ingest` en n8n.

7. Importar los workflows de [`n8n/`](n8n/) en n8n y configurar la credencial de Anthropic.

8. Ejecutar `workflow-main`. El riesgo final quedará indexado en `asset-final-risk`.

9. Importar los dashboards de Kibana desde [`kibana/dashboards-export.ndjson`](kibana/).

> **Seguridad**: en este laboratorio Elasticsearch se ejecuta sin la capa de seguridad de X-Pack por tratarse de un entorno aislado. No debe exponerse así en producción. Las claves de API se configuran como credenciales **dentro de n8n**, nunca en el repositorio.

## Validación ofensiva

La cadena de explotación se valida con MITRE CALDERA sobre un laboratorio aislado (red host-only), empleando **CVE-2021-41773** (path traversal / RCE en Apache httpd 2.4.49) contra un activo objetivo pasivo. Las capturas before/after ([`caldera/results/`](caldera/results/)) documentan la ejecución de las abilities antes y después de la mitigación (actualización a httpd 2.4.51). El perfil de adversario está en [`caldera/adversary-T1190.json`](caldera/).

## Estructura del repositorio

Ver [`ESTRUCTURA.md`](ESTRUCTURA.md) para el árbol completo y la descripción de cada carpeta.
