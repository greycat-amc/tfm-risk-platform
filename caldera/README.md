# Validación ofensiva con MITRE CALDERA

Esta carpeta contiene el perfil de adversario y las abilities empleados para
validar empíricamente la explotabilidad de **CVE-2021-41773** (path traversal y
ejecución remota de código en Apache HTTP Server 2.4.49) sobre el activo WEB-01.

## Entorno de laboratorio

- **WEB-01** (objetivo pasivo): Ubuntu 24.04 LTS, `192.168.56.105`, Apache httpd
  2.4.49 en contenedor Docker, puerto 80.
- **CALDERA** (atacante): Ubuntu 24.04 LTS, `192.168.56.106`, CALDERA 5.3.0,
  puerto 8888. El agente Sandcat se despliega sobre esta misma máquina.
- **Red**: host-only `192.168.56.0/24` (aislada) más NAT solo para paquetes.

## Cadena de ataque (T1190 — Exploit Public-Facing Application)

El adversario ejecuta tres abilities en orden atómico, cada una mapeada a la
técnica MITRE ATT&CK **T1190**:

| Orden | Ability                          | Táctica    | Acción                                                        |
|-------|----------------------------------|------------|--------------------------------------------------------------|
| 1     | Check Apache service WEB-01      | discovery  | Comprueba que el servicio responde antes de explotar         |
| 2     | Path traversal read passwd WEB-01| collection | Lee `/etc/passwd` mediante path traversal por `/icons/`      |
| 3     | RCE execute id WEB-01            | execution  | Ejecuta `id` mediante RCE por `/cgi-bin/` → `/bin/sh`        |

El vector de lectura emplea `/icons/`; el de ejecución emplea `/cgi-bin/`, ya que
`/cgi-bin/` devuelve error 500 para lecturas.

## Resultados: before / after

La validación se ejecuta en dos fases sobre la misma cadena:

- **before** (`results/before/`): con Apache 2.4.49, las tres abilities finalizan
  en estado **SUCCESS**. La vulnerabilidad es explotable.
- **after** (`results/after/`): tras aplicar la mitigación (actualización a Apache
  **2.4.51**), las abilities finalizan en estado **FAILED**. La vulnerabilidad
  queda cerrada.

Se actualiza a 2.4.51 y no a 2.4.50, ya que esta última introduce
CVE-2021-42013, una omisión incompleta de la corrección anterior.

## Reproducción

1. Copiar `adversary-T1190.yml` a `data/adversaries/` de la instancia de CALDERA.
2. Copiar los ficheros de `abilities/` a `data/abilities/` (una subcarpeta por
   táctica o directamente en el directorio de abilities).
3. Reiniciar CALDERA para que cargue los objetos.
4. Desplegar un agente Sandcat y crear una operación sobre el adversario
   **Apache 2.4.49 CVE-2021-41773 Validation** en modo autónomo, planificador
   atómico.

## Aviso

El entorno es un laboratorio aislado con fines exclusivamente académicos. La
dirección `192.168.56.105` pertenece a la red host-only privada de VirtualBox.
