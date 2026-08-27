# Estructura del repositorio

```
tfm-risk-platform/
├── README.md                  Portada: descripción, arquitectura, modelo y puesta en marcha
├── ESTRUCTURA.md              Este archivo
├── .env.example               Plantilla de variables de entorno (sin secretos)
├── .gitignore                 Exclusiones (secretos, volúmenes, datos pesados)
├── docs/
│   ├── arquitectura.md        Descripción técnica de la arquitectura del sistema
│   ├── formula-scoring.md     Modelo de scoring: TR, CF, FinalRisk y umbrales
│   └── img/                   Diagramas y capturas de la documentación
├── infra/
│   ├── docker-compose.yml     Definición de servicios (ES, Kibana, n8n, Caddy)
│   └── Caddyfile              Reverse proxy con PKI local
├── n8n/
│   ├── workflow-main.json         Pipeline principal de scoring
│   ├── workflow-override.json     Override de criticidad (Form Trigger)
│   └── workflow-epss-ingest.json  Ingesta del dataset EPSS
├── elasticsearch/
│   ├── mappings/              Mappings de los 5 índices
│   └── queries/               Consultas de agregación de referencia
├── data/
│   └── inventario-21-activos.json  Inventario de activos (datos simulados)
├── scripts/
│   └── cpe_verify.py          Verificación de CPE contra NVD
├── kibana/
│   └── dashboards-export.ndjson    Objetos guardados de Kibana
└── caldera/
    ├── adversary-T1190.json   Perfil de adversario (Exploit Public-Facing App.)
    └── results/               Capturas de validación (before / after)
```

## Aviso sobre los datos

Todos los datos de inventario, topología y escenario corresponden a un entorno **ficticio** (PYME de e-commerce en migración a la nube) construido con fines exclusivamente académicos. No representan infraestructura real.
