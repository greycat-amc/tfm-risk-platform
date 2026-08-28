# tfm-risk-platform

**Evaluación de la superficie de exposición: un modelo de priorización de vulnerabilidades sensible al contexto del activo**

Trabajo Fin de Máster — Máster en Ciberseguridad.

Plataforma de evaluación de riesgo que integra fuentes de vulnerabilidad (NVD, EPSS, KEV) con el contexto de los activos y reordena la prioridad de remediación **a nivel de activo**, no de vulnerabilidad. El modelo es explícito, trazable y reproducible.

> **Aviso**: todos los datos de inventario, topología y escenario son **ficticios** (PYME de e-commerce en migración a la nube) y se emplean con fines exclusivamente académicos. No representan infraestructura real.

## Pregunta de investigación

La priorización del riesgo de vulnerabilidades reconoce el contexto del activo como
determinante, pero ese contexto se incorpora de forma heterogénea en los modelos y,
en las plataformas comerciales, con una ponderación que no siempre es completamente
auditable.

Este trabajo propone un modelo que separa dos planos habitualmente fundidos en una
única puntuación: el **riesgo técnico** de la vulnerabilidad (derivado de CVSS, EPSS
y KEV) y el **contexto del activo**, formalizado en un factor independiente y
explícito, el **ContextFactor**, con pesos declarados y cálculo trazable. La
priorización deja así de recaer sobre la vulnerabilidad para recaer sobre el activo
que la contiene, y el contexto pasa de ser un ajuste implícito a una componente
auditable del resultado.

La pregunta que articula el trabajo es: *¿en qué medida la incorporación sucesiva de
señales de explotación y del contexto arquitectónico del activo modifica la
priorización obtenida a partir de la severidad técnica de la vulnerabilidad?*

## Arquitectura

El sistema se despliega con Docker Compose e integra cuatro servicios sobre una red interna:

- **Elasticsearch 8.15.3** — almacenamiento e indexación de inventario y riesgo.
- **Kibana 8.15.3** — visualización (dashboards, slopegraph, tablas comparativas).
- **n8n** — orquestación del pipeline de scoring.
- **Caddy 2** — reverse proxy con PKI local (HTTPS para n8n y Kibana).

El pipeline recupera el inventario, consulta NVD por CPE, enriquece cada CVE con EPSS y KEV, calcula el riesgo técnico por CVE, aplica el factor de contexto por activo y persiste el resultado. Un nodo de IA (Anthropic) genera la técnica MITRE ATT&CK asociada, la remediación y el `priority_rationale`.

El detalle completo del pipeline nodo a nodo está en [`1-modelo/`](1-modelo/).

### Despliegue

![Arquitectura de contenedores sobre Docker](1-modelo/img/arquitectura-docker.png)

*Despliegue sobre una máquina virtual Ubuntu: los cuatro servicios se ejecutan como contenedores en una red bridge interna (`tfm_net`). Caddy actúa como proxy inverso con PKI local; Elasticsearch se expone únicamente en `127.0.0.1:9200`. Cada contenedor persiste sus datos en un volumen propio.*

### Pipeline de scoring

![Diagrama del pipeline de nodos](1-modelo/img/pipeline-nodos.png)

*Flujo del pipeline principal: recuperación del inventario, consulta a NVD por CPE, enriquecimiento con EPSS y KEV, cálculo del riesgo técnico por CVE, aplicación del factor de contexto por activo y persistencia del resultado.*

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

El desarrollo completo del modelo está en [`1-modelo/`](1-modelo/).

### Diferenciación contextual (resultado central)

DC-01 y JMP-01 comparten CVE (CVE-2025-59287) y riesgo técnico (TR = 0.9918), pero producen FinalRisk distintos (0.883 vs 0.846) por el diferente radio de impacto (blast radius) de sus módulos. El contexto, aplicado de forma explícita y con pesos declarados, reordena la prioridad entre dos activos que la severidad técnica igualaría.

## Organización del repositorio

El repositorio se estructura en tres bloques que siguen la secuencia del trabajo:

- **[`1-modelo/`](1-modelo/)** — la propuesta: formulación del modelo de scoring y arquitectura del sistema.
- **[`2-plataforma/`](2-plataforma/)** — la implementación: infraestructura, orquestación (n8n), índices (Elasticsearch), visualización (Kibana) y utilidades.
- **[`3-caso-estudio/`](3-caso-estudio/)** — la aplicación: inventario del escenario ficticio y validación ofensiva con CALDERA.

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

4. Crear los índices en Elasticsearch aplicando los mappings de [`2-plataforma/elasticsearch/mappings/`](2-plataforma/elasticsearch/mappings/).

5. Cargar el inventario de activos ([`3-caso-estudio/inventario/inventario-21-activos.json`](3-caso-estudio/inventario/)) en el índice `asset-inventory-v1`.

6. Ingerir las fuentes de datos ejecutando `workflow-epss-ingest` (dataset EPSS) y `workflow-kev-ingest` (catálogo KEV de CISA) en n8n.

7. Importar los workflows de [`2-plataforma/n8n/`](2-plataforma/n8n/) en n8n y configurar la credencial de Anthropic.

8. Ejecutar `workflow-main`. El riesgo final quedará indexado en `asset-final-risk`.

9. Importar los dashboards de Kibana desde [`2-plataforma/kibana/kibana-objects.ndjson`](2-plataforma/kibana/).

> **Seguridad**: en este laboratorio Elasticsearch se ejecuta sin la capa de seguridad de X-Pack por tratarse de un entorno aislado. No debe exponerse así en producción. Las claves de API se configuran como credenciales **dentro de n8n**, nunca en el repositorio.

## Validación ofensiva

La cadena de explotación se valida con MITRE CALDERA sobre un laboratorio aislado (red host-only), empleando **CVE-2021-41773** (path traversal / RCE en Apache httpd 2.4.49) contra un activo objetivo pasivo. Las capturas before/after ([`3-caso-estudio/validacion-caldera/results/`](3-caso-estudio/validacion-caldera/results/)) documentan la ejecución de las abilities antes y después de la mitigación (actualización a httpd 2.4.51). El perfil de adversario está en [`3-caso-estudio/validacion-caldera/adversary-T1190.yml`](3-caso-estudio/validacion-caldera/).

## Estructura del repositorio

Ver [`ESTRUCTURA.md`](ESTRUCTURA.md) para el árbol completo y la descripción de cada carpeta.
