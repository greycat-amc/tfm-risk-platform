# Estructura del repositorio

El repositorio se organiza en tres bloques que siguen la secuencia del trabajo:
**el modelo** propuesto, **la plataforma** que lo implementa y **el caso de
estudio** que lo aplica y valida.

```
tfm-risk-platform/
├── README.md                  Portada e índice del repositorio
├── ESTRUCTURA.md              Este archivo
├── .env.example               Plantilla de variables de entorno (sin secretos)
├── .gitignore                 Exclusiones (secretos, volúmenes, datos pesados)
│
├── 1-modelo/                  LA PROPUESTA: modelo de priorización
│   ├── README.md              Modelo de scoring y arquitectura del sistema
│   └── img/                   Diagramas (arquitectura de contenedores, pipeline)
│
├── 2-plataforma/              LA IMPLEMENTACIÓN: sistema desplegable
│   ├── infra/                 Docker Compose y reverse proxy (Caddy)
│   ├── n8n/                   Workflows de orquestación (scoring, ingestas, override)
│   ├── elasticsearch/         Mappings de los 5 índices y consultas de referencia
│   ├── kibana/                Objetos guardados (dashboards y data views)
│   └── scripts/               Utilidades (verificación de CPE contra NVD)
│
└── 3-caso-estudio/            EL CASO DE ESTUDIO: aplicación y validación
    ├── inventario/            Inventario de 21 activos y topología del escenario
    └── validacion-caldera/    Validación ofensiva de CVE-2021-41773 con CALDERA
```

## Correspondencia con la memoria

- **1-modelo** corresponde al diseño de la propuesta: la formulación del modelo de
  priorización contextual y la arquitectura del sistema.
- **2-plataforma** corresponde a la implementación: la infraestructura de
  contenedores, la orquestación en n8n, los índices de Elasticsearch, la
  visualización en Kibana y las utilidades de apoyo.
- **3-caso-estudio** corresponde a la aplicación sobre el escenario ficticio (PYME
  de e-commerce) y a la validación empírica de la explotabilidad.

## Aviso sobre los datos

Todos los datos de inventario, topología y escenario corresponden a un entorno
**ficticio** construido con fines exclusivamente académicos. No representan
infraestructura real.
