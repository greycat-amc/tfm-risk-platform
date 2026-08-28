# Inventario de activos

## Escenario

El escenario corresponde a una **PYME de e-commerce ficticia** en proceso de
migración a la nube. Su infraestructura se distribuye en un centro de datos
propio (CPD), una sede principal (HQ) y un almacén, interconectados mediante una
red SD-WAN sobre equipos Meraki. El entorno integra activos tradicionales
(servidores web y de aplicación, bases de datos, correo on-premise), servicios
cloud (Microsoft 365, portal Meraki) y elementos OT/IoT (cámaras de
videovigilancia, PLC), lo que produce una superficie de exposición heterogénea.

El conjunto está compuesto por **21 activos** agrupados en **9 módulos
funcionales**. Cada activo declara su exposición, su criticidad y el módulo al que
pertenece; a partir de esa información y de la topología, el sistema calcula el
riesgo contextual de cada uno. Todos los datos son **ficticios** y se emplean con
fines exclusivamente académicos; no representan infraestructura real.

## Topología

![Topología de la organización — CPD, sedes y servicios cloud](img/topologia-escenario.png)

*Topología lógica del escenario: centro de datos (CPD), sede principal (HQ),
almacén y servicios cloud. Se indican los flujos de negocio, los túneles SD-WAN,
la identidad híbrida y los activos OT/IoT sujetos a override de criticidad.*

## Inventario

`inventario-21-activos.json` contiene los 21 activos exportados desde el índice
`asset-inventory-v1`. Cada activo es un objeto JSON con los campos que se
describen a continuación.

### Esquema

| Campo                        | Tipo    | Origen     | Descripción                                                        |
|------------------------------|---------|------------|--------------------------------------------------------------------|
| `asset_id`                   | keyword | declarado  | Identificador único del activo (p. ej. WEB-01)                     |
| `asset_name`                 | keyword | declarado  | Nombre descriptivo                                                 |
| `asset_type`                 | keyword | declarado  | Tipo de activo                                                     |
| `asset_version`              | keyword | declarado  | Versión del software                                               |
| `software`                   | keyword | declarado  | Producto de software                                               |
| `cpe_name`                   | keyword | declarado  | CPE 2.3 empleado para consultar NVD                                |
| `exposure`                   | keyword | declarado  | Grado de exposición (p. ej. internet, internal, restricted)        |
| `module_id`                  | keyword | declarado  | Módulo funcional al que pertenece el activo                        |
| `criticality`                | keyword | derivado   | Criticidad del activo                                              |
| `criticality_norm`           | float   | calculado  | Criticidad normalizada [0, 1]                                      |
| `blast_radius_norm`          | float   | calculado  | Radio de impacto normalizado del módulo                            |
| `blast_radius_status`        | keyword | calculado  | Estado del cálculo de blast radius                                 |
| `criticality_overridden`     | boolean | declarado  | Indica si la criticidad se ha declarado por override (factor H)    |
| `criticality_override_level` | keyword | declarado  | Nivel declarado en el override (null si no aplica)                 |
| `criticality_score`          | integer | derivado   | Puntuación de criticidad del override                              |
| `override_justification`     | text    | declarado  | Justificación del override (null si no aplica)                     |
| `override_timestamp`         | date    | declarado  | Momento del override (null si no aplica)                           |

### Marco de tres orígenes

El contexto de cada activo se parametriza según el origen de cada valor:

- **Declarado**: introducido directamente en el inventario por el responsable del activo.
- **Derivado**: obtenido a partir de otros campos o de tablas de referencia.
- **Calculado**: computado por el pipeline (normalizaciones, blast radius).

Los campos de override permanecen a `null` / `false` mientras no se declare una
criticidad explícita mediante el flujo `workflow-override`, que activa el factor H
del modelo de scoring.

Para el detalle del pipeline que consume este inventario, véase
[`../../1-modelo/`](../../1-modelo/).
