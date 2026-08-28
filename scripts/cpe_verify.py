#!/usr/bin/env python3
"""
Verificacion de CPE del inventario contra la API de NVD.

Uso:
    python3 cpe_verify.py                    # sin API key (6s entre peticiones)
    NVD_API_KEY=xxxx python3 cpe_verify.py   # con API key (0.6s entre peticiones)

Salida: tabla por consola + fichero resultado_cpes.csv

Interpretacion:
    OK          -> el CPE resuelve y devuelve CVEs. Usable tal cual.
    VACIO       -> el CPE es sintacticamente valido pero NVD no devuelve CVEs.
                   Puede ser ausencia legitima (SaaS, appliance) o error de string.
                   Revisar manualmente segun la columna 'esperado'.
    ERROR       -> fallo de peticion (revisar mensaje).
"""

import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
API_KEY = os.environ.get("NVD_API_KEY", "").strip()
DELAY = 0.7 if API_KEY else 6.5

# esperado: "cve"    -> deberia devolver CVEs; si sale VACIO hay que corregir el string
#           "ninguna" -> ausencia legitima documentada como punto ciego
INVENTARIO = [
    # (asset_id, software, cpe, esperado)
    ("WEB-01",   "Apache HTTP Server 2.4.49",
     "cpe:2.3:a:apache:http_server:2.4.49:*:*:*:*:*:*:*", "cve"),
    ("PROXY-01", "nginx 1.18.0",
     "cpe:2.3:a:f5:nginx:1.18.0:*:*:*:*:*:*:*", "cve"),
    ("MAIL-01",  "Exchange Server 2016 CU20",
     "cpe:2.3:a:microsoft:exchange_server:2016:cumulative_update_20:*:*:*:*:*:*", "cve"),
    ("APP-01",   "Apache Tomcat 9.0.30",
     "cpe:2.3:a:apache:tomcat:9.0.30:*:*:*:*:*:*:*", "cve"),
    ("PAY-01",   "Node.js 14.17.0",
     "cpe:2.3:a:nodejs:node.js:14.17.0:*:*:*:*:*:*:*", "cve"),
    ("DB-01",    "MySQL 8.0",
     "cpe:2.3:a:oracle:mysql:8.0:*:*:*:*:*:*:*", "cve"),
    ("DB-02",    "PostgreSQL 12.0",
     "cpe:2.3:a:postgresql:postgresql:12.0:*:*:*:*:*:*:*", "cve"),
    ("DB-03",    "MariaDB 10.5",
     "cpe:2.3:a:mariadb:mariadb:10.5:*:*:*:*:*:*:*", "cve"),
    ("DC-01",    "Windows Server 2019",
     "cpe:2.3:o:microsoft:windows_server_2019:*:*:*:*:*:*:*:*", "cve"),
    ("JMP-01",   "Windows Server 2019",
     "cpe:2.3:o:microsoft:windows_server_2019:*:*:*:*:*:*:*:*", "cve"),
    ("WKS-01",   "Windows 10 22H2",
     "cpe:2.3:o:microsoft:windows_10_22h2:*:*:*:*:*:*:*:*", "cve"),
    ("WKS-02",   "Windows 10 22H2",
     "cpe:2.3:o:microsoft:windows_10_22h2:*:*:*:*:*:*:*:*", "cve"),
    ("DEV-01",   "Ubuntu Linux 20.04",
     "cpe:2.3:o:canonical:ubuntu_linux:20.04:*:*:*:lts:*:*:*", "cve"),
    ("FW-01",    "Cisco Meraki MX",
     "cpe:2.3:h:cisco:meraki_mx:*:*:*:*:*:*:*:*", "ninguna"),
    ("FW-02",    "Cisco Meraki MX",
     "cpe:2.3:h:cisco:meraki_mx:*:*:*:*:*:*:*:*", "ninguna"),
    ("FW-03",    "Cisco Meraki MX",
     "cpe:2.3:h:cisco:meraki_mx:*:*:*:*:*:*:*:*", "ninguna"),
    ("SW-01",    "Conmutador de nucleo",
     "cpe:2.3:h:cisco:catalyst_switch:*:*:*:*:*:*:*:*", "ninguna"),
    ("SDN-01",   "Meraki Dashboard (cloud)",
     "cpe:2.3:a:cisco:meraki_dashboard:*:*:*:*:*:*:*:*", "ninguna"),
    ("M365-01",  "Exchange Online (SaaS)",
     "cpe:2.3:a:microsoft:exchange_online:*:*:*:*:*:*:*:*", "ninguna"),
]

# Alternativas a probar si el string principal falla
ALTERNATIVAS = {
    "PROXY-01": [
        "cpe:2.3:a:nginx:nginx:1.18.0:*:*:*:*:*:*:*",
        "cpe:2.3:a:f5:nginx:1.18.0:*:*:*:*:*:*:*",
    ],
    "MAIL-01": [
        "cpe:2.3:a:microsoft:exchange_server:2016:*:*:*:*:*:*:*",
        "cpe:2.3:a:microsoft:exchange_server:2016:cumulative_update_20:*:*:*:*:*:*",
    ],
    "WKS-01": [
        "cpe:2.3:o:microsoft:windows_10_22h2:*:*:*:*:*:*:*:*",
        "cpe:2.3:o:microsoft:windows_10:22h2:*:*:*:*:*:*:*",
        "cpe:2.3:o:microsoft:windows_10:-:*:*:*:*:*:*:*",
    ],
    "PAY-01": [
        "cpe:2.3:a:nodejs:node.js:14.17.0:*:*:*:*:*:*:*",
        "cpe:2.3:a:nodejs:nodejs:14.17.0:*:*:*:*:*:*:*",
    ],
    "SW-01": [
        "cpe:2.3:h:cisco:catalyst_switch:*:*:*:*:*:*:*:*",
        "cpe:2.3:o:cisco:ios:*:*:*:*:*:*:*:*",
    ],
}


def consultar(cpe, intentos=3):
    """Devuelve (total_cves, error). total_cves = -1 si hubo error."""
    params = urllib.parse.urlencode({"cpeName": cpe, "resultsPerPage": 1})
    url = f"{NVD_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "TFM-CPE-Check/1.0"})
    if API_KEY:
        req.add_header("apiKey", API_KEY)

    for intento in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode())
                return data.get("totalResults", 0), None
        except urllib.error.HTTPError as e:
            if e.code in (403, 503) and intento < intentos - 1:
                time.sleep(10 * (intento + 1))
                continue
            return -1, f"HTTP {e.code}"
        except Exception as e:
            if intento < intentos - 1:
                time.sleep(5)
                continue
            return -1, str(e)[:60]
    return -1, "agotados los reintentos"


def main():
    print(f"\nVerificacion de CPE contra NVD")
    print(f"API key: {'si' if API_KEY else 'NO (mas lento; considera pedir una en nvd.nist.gov)'}")
    print(f"Activos a comprobar: {len(INVENTARIO)}")
    print(f"Tiempo estimado: ~{int(len(INVENTARIO) * DELAY / 60) + 1} min\n")
    print(f"{'ASSET':<10} {'ESTADO':<8} {'CVEs':>6}  {'ESPERADO':<9} SOFTWARE")
    print("-" * 78)

    resultados = []
    cache = {}

    for asset_id, software, cpe, esperado in INVENTARIO:
        if cpe in cache:
            total, error = cache[cpe]
        else:
            total, error = consultar(cpe)
            cache[cpe] = (total, error)
            time.sleep(DELAY)

        if error:
            estado = "ERROR"
        elif total > 0:
            estado = "OK"
        else:
            estado = "VACIO"

        # Marca de discrepancia: esperabamos CVEs y no hay, o al reves
        alerta = ""
        if estado == "VACIO" and esperado == "cve":
            alerta = "  <-- REVISAR STRING"
        elif estado == "OK" and esperado == "ninguna":
            alerta = "  <-- inesperado, hay cobertura"

        print(f"{asset_id:<10} {estado:<8} {total if total >= 0 else '-':>6}  "
              f"{esperado:<9} {software}{alerta}")

        resultados.append({
            "asset_id": asset_id,
            "software": software,
            "cpe": cpe,
            "estado": estado,
            "total_cves": total,
            "esperado": esperado,
            "error": error or "",
        })

    # Probar alternativas para los que fallaron
    fallos = [r for r in resultados
              if r["estado"] != "OK" and r["esperado"] == "cve"
              and r["asset_id"] in ALTERNATIVAS]

    if fallos:
        print(f"\n{'='*78}")
        print("Probando strings alternativos para los que no resolvieron:\n")
        for r in fallos:
            print(f"  {r['asset_id']} ({r['software']}):")
            for alt in ALTERNATIVAS[r["asset_id"]]:
                if alt == r["cpe"]:
                    continue
                total, error = consultar(alt)
                time.sleep(DELAY)
                marca = "OK  " if total > 0 else ("ERR " if total < 0 else "vacio")
                print(f"    [{marca}] {total if total >= 0 else '-':>5} CVEs  {alt}")

    with open("resultado_cpes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(resultados[0].keys()))
        w.writeheader()
        w.writerows(resultados)

    ok = sum(1 for r in resultados if r["estado"] == "OK")
    revisar = sum(1 for r in resultados
                  if r["estado"] == "VACIO" and r["esperado"] == "cve")
    ciegos = sum(1 for r in resultados
                 if r["estado"] == "VACIO" and r["esperado"] == "ninguna")

    print(f"\n{'='*78}")
    print(f"Resultado: {ok} resuelven / {revisar} requieren correccion / "
          f"{ciegos} ausencia legitima")
    print(f"Detalle en resultado_cpes.csv\n")


if __name__ == "__main__":
    main()
