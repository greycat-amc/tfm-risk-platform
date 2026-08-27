# Arquitectura del sistema

La plataforma implementa un pipeline de evaluación de riesgo que integra fuentes
de vulnerabilidad (NVD, EPSS, KEV) con el contexto de los activos, orquestado
sobre una infraestructura de contenedores. El diseño prioriza la **auditabilidad**:
cada transformación es un nodo explícito y trazable.

## 1. Componentes

El sistema se despliega mediante Docker Compose e integra cuatro servicios sobre
una red interna (`tfm_net`):

| Servicio       | Imagen                         | Rol                                                    |
|----------------|--------------------------------|--------------------------------------------------------|
| Elasticsearch  | elasticsearch:8.15.3           | Almacenamiento e indexación de inventario y riesgo     |
| Kibana         | kibana:8.15.3                  | Visualización (dashboards, slopegraph, tablas)         |
| n8n            | n8nio/n8n:latest               | Orquestación del pipeline de scoring                   |
| Caddy          | caddy:2                        | Reverse proxy con PKI local (HTTPS para n8n y Kibana)  |

Elasticsearch se expone únicamente en `127.0.0.1:9200` y se ejecuta sin la capa
de seguridad de X-Pack (`xpack.security.enabled=false`), decisión admisible por
tratarse de un entorno de laboratorio aislado. Caddy publica los puertos 80/443 y
enruta por nombre de host (`n8n.local`, `kibana.local`) hacia los servicios
internos.

## 2. Índices de Elasticsearch

| Índice                 | Contenido                                            | Clave de documento          |
|------------------------|------------------------------------------------------|-----------------------------|
| `asset-inventory-v1`   | Inventario de activos (fuente de verdad)             | asset_id                    |
| `technical-risk-cve`   | Riesgo técnico por par activo-CVE                    | asset_id + cve_id           |
| `asset-final-risk`     | Riesgo final por activo (21 documentos)              | asset_id (idempotente)      |
| `epss-scores`          | Dataset EPSS completo (~352.707 CVE, local)          | cve_id                      |
| `kev-catalog`          | Catálogo KEV de CISA (local)                         | cve_id                      |

Los índices emplean campos de tipo `keyword` (no `text` con subcampo `.keyword`),
lo que condiciona la forma de las agregaciones y de las dimensiones en Kibana Lens.

## 3. Pipeline principal (workflow-main)

El flujo se activa mediante un trigger de ejecución y recorre la siguiente
secuencia de nodos. La numeración corresponde a la del propio workflow.

| # Nodo | Nombre                              | Tipo         | Función                                                        |
|--------|-------------------------------------|--------------|----------------------------------------------------------------|
| —      | When Executed by Another Workflow   | Trigger      | Punto de entrada del pipeline                                  |
| 01a    | Fetch inventory                     | HTTP Request | Recupera el inventario desde `asset-inventory-v1`             |
| 01b    | Flatten hits                        | Code         | Aplana la respuesta de Elasticsearch                          |
| 01c    | Normalize assets                    | Code         | Normaliza los campos del activo                               |
| 02     | Query NVD by CPE                    | HTTP Request | Consulta la API de NVD por CPE (resultsPerPage=2000)          |
| 03     | Merge Asset + NVD Response          | Merge        | Une cada activo con sus CVE derivados del CPE                 |
| 04     | Asset-CVE Master Table              | Code         | Construye la tabla maestra activo-CVE                         |
| 05     | Query EPSS by CVE                   | Code         | Añade la probabilidad EPSS local a cada CVE                   |
| 06     | Query KEV by CVE                    | Code         | Marca la pertenencia al catálogo KEV                         |
| 07     | Calculate Technical Risk (CVE)      | Code         | Calcula TR por CVE (0.40·CVSS + 0.35·EPSS + 0.25·KEV)         |
| 07b    | Index Asset-CVE Risk                | HTTP Request | Indexa el TR por par activo-CVE en `technical-risk-cve`      |
| 08     | Final Risk Score (Asset)            | Code         | Aplica CF sobre el TR_top y calcula FinalRisk por activo      |
| —      | Basic LLM Chain (Anthropic)         | LangChain    | Genera técnica ATT&CK, remediación y rationale (JSON)         |
| 08b    | Parse + Merge Remediation           | Code         | Integra la salida del modelo en el documento del activo       |
| 08c    | Index Asset Risk                    | HTTP Request | Indexa el riesgo final en `asset-final-risk` (por asset_id)   |

### Detalle de la bifurcación de riesgo

El nodo **07** calcula el riesgo técnico **por cada CVE** del activo y bifurca:

- Una rama (**07b**) persiste el detalle activo-CVE en `technical-risk-cve`, lo que
  permite auditar el riesgo técnico de cada vulnerabilidad de forma independiente.
- La otra rama (**08**) selecciona el TR más alto del activo (TR_top), le aplica el
  factor de contexto (CF) una sola vez y obtiene el FinalRisk. El contexto pertenece
  al activo, no al CVE.

El nodo **Anthropic Chat Model** alimenta al **Basic LLM Chain**, que genera de
forma estructurada la técnica MITRE ATT&CK asociada, la remediación primaria, la
remediación compensatoria y el `priority_rationale`. El nodo **08b** integra esa
salida antes de la indexación final en **08c**.

## 4. Flujos auxiliares

- **workflow-override**: expone un formulario (n8n Form Trigger) mediante el cual un
  responsable declara explícitamente la criticidad de un activo. Activa el factor H
  del modelo (`criticality_overridden = true`), que duplica el peso de la criticidad
  y anula la sensibilidad del módulo.
- **workflow-epss-ingest**: descarga e indexa el dataset EPSS completo
  (`epss_scores-current.csv.gz`) en el índice `epss-scores`. Requiere habilitar el
  módulo `zlib` en n8n (`NODE_FUNCTION_ALLOW_BUILTIN=zlib`) para descomprimir el
  fichero.

## 5. Validación ofensiva

La cadena de explotación se valida en un entorno de laboratorio independiente
(red host-only 192.168.56.0/24) mediante MITRE CALDERA, empleando el
CVE-2021-41773 (path traversal / RCE en Apache httpd 2.4.49) sobre un activo
objetivo pasivo. Los resultados before/after documentan la ejecución de las
abilities antes y después de la mitigación (actualización a httpd 2.4.51).

## 6. Nota sobre credenciales

Los workflows exportados contienen únicamente **referencias** a las credenciales
(identificador y nombre), no sus valores. Para reproducir el sistema es necesario
crear las credenciales correspondientes (Anthropic API, y opcionalmente NVD API
key) dentro de la propia instancia de n8n.
