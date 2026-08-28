# Mappings de Elasticsearch

Cada archivo define el mapping de un índice en formato reutilizable. Para crear un
índice, se envía el mapping mediante una petición `PUT`:

```
curl -X PUT "http://localhost:9200/asset-inventory-v1" \
  -H "Content-Type: application/json" \
  --data-binary @asset-inventory-v1.json
```

Repetir para cada índice: `technical-risk-cve`, `asset-final-risk`, `epss-scores`
y `kev-catalog`.

## Notas

- **`technical-risk-cve`** emplea campos `text` con subcampo `.keyword`. Las
  agregaciones y las dimensiones en Kibana Lens sobre estos campos deben usar el
  sufijo `.keyword`.
- **`asset-inventory-v1`**, **`asset-final-risk`**, **`epss-scores`** y
  **`kev-catalog`** emplean mayoritariamente campos `keyword` directos.
- El mapping de `kev-catalog` refleja la estructura de documento que produce el
  flujo `workflow-kev-ingest` (un documento por CVE con `cve_id` como clave).
