# Modelo de scoring

Este documento describe el modelo de priorización empleado por la plataforma.
El modelo separa el **riesgo técnico** de la vulnerabilidad (propio del CVE) del
**contexto del activo** que la presenta, y combina ambos en una puntuación final
acotada en el rango [0, 1].

La contribución del modelo no reside en la novedad de incorporar contexto —las
plataformas comerciales ya lo hacen de forma opaca— sino en su **auditabilidad**:
cada término es explícito, trazable y reproducible.

## 1. Riesgo técnico (TR)

El riesgo técnico se calcula por CVE a partir de tres fuentes normalizadas al
rango [0, 1]:

```
TR = 0.40 * CVSS_norm + 0.35 * EPSS_norm + 0.25 * KEV_norm
```

- **CVSS_norm**: severidad base del CVE (CVSS / 10).
- **EPSS_norm**: probabilidad de explotación en los próximos 30 días (valor EPSS directo, ya en [0, 1]).
- **KEV_norm**: pertenencia al catálogo KEV de CISA (1 si el CVE figura en KEV, 0 en caso contrario).

El TR se calcula para cada CVE asociado a un activo. Para el cálculo del riesgo
final se emplea el TR más alto del activo (TR_top).

## 2. Factor de contexto (CF)

El contexto pertenece al **activo**, no al CVE. El CF se aplica una sola vez por
activo, sobre su TR_top:

```
CF = 0.30 * Exposure_norm
   + 0.20 * (1 + H) * Criticality_norm
   + 0.20 * (1 - H) * ModuleSensitivity_norm
   + 0.30 * BlastRadius_norm
```

- **Exposure_norm**: grado de exposición del activo (declarado en el inventario).
- **Criticality_norm**: criticidad del activo para el negocio.
- **ModuleSensitivity_norm**: sensibilidad del módulo funcional al que pertenece el activo.
- **BlastRadius_norm**: radio de impacto del módulo, calculado sobre la topología (N = 9 módulos).

### Factor H (override de criticidad)

`H` es un factor binario que controla la ponderación entre criticidad y
sensibilidad del módulo:

- **H = 0** (por defecto): criticidad y sensibilidad del módulo pesan 0.20 cada una.
- **H = 1** (cuando `criticality_overridden = true`): la criticidad duplica su peso
  (0.20 -> 0.40) y la sensibilidad del módulo se anula (0.20 -> 0).

El override se activa mediante un formulario (n8n Form Trigger) cuando un
responsable declara explícitamente la criticidad de un activo, sustituyendo el
valor derivado del módulo por un juicio experto trazable.

## 3. Riesgo final (FinalRisk)

```
FinalRisk = TR_top * (1 + CF) / 2
```

El resultado queda acotado en el rango [0, 1]. El contexto actúa como
**modulador** del riesgo técnico: un mismo CVE con idéntico TR produce distintos
FinalRisk según el activo que lo presente.

## 4. Umbrales de clasificación

| Nivel   | Rango           |
|---------|-----------------|
| CRÍTICO | FinalRisk ≥ 0.80 |
| ALTO    | FinalRisk ≥ 0.60 |
| MEDIO   | FinalRisk ≥ 0.40 |
| BAJO    | FinalRisk < 0.40 |

## 5. Ejemplo de diferenciación contextual

DC-01 y JMP-01 comparten el mismo CVE (CVE-2025-59287) y el mismo riesgo técnico
(TR = 0.9918), pero producen puntuaciones finales distintas:

| Activo  | TR_top | FinalRisk | Nivel   |
|---------|--------|-----------|---------|
| DC-01   | 0.9918 | 0.883     | CRÍTICO |
| JMP-01  | 0.9918 | 0.846     | CRÍTICO |

La diferencia (0.883 vs 0.846) se debe al distinto radio de impacto (blast
radius) de los módulos a los que pertenecen. Un escáner comercial que puntúa
vulnerabilidades —y no activos— asignaría idéntica prioridad a ambos. El modelo
contextual los diferencia de forma auditable.
