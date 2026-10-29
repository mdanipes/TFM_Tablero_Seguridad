# Metodología para diseñar y validar tableros de indicadores de seguridad de la información

Repositorio del Trabajo Fin de Máster de **María Daniela Pesántez Prado**, Máster Universitario en Análisis y Visualización de Datos Masivos (Visual Analytics and Big Data), Universidad Internacional de La Rioja (UNIR), 2026.

El repositorio contiene todo lo necesario para reproducir el caso de estudio de la memoria: el generador de datos simulados, los dos conjuntos de datos utilizados, las consultas de Power Query con las reglas de calidad R1 a R9, el modelo de Power BI con sus medidas DAX y el script que verifica la detección de los problemas de calidad y la exactitud de los indicadores.

> **Todos los datos son simulados.** No contienen información de ninguna organización ni persona real. «Empresa Delta EP» es un nombre ficticio.

## Estructura

```
├── generador/
│   └── generador_datos_seguridad.py   Genera los datos simulados (tickets de GLPI, activos y vulnerabilidades)
├── datos/
│   ├── escenario_A/                   Datos 2024–2025 (semilla 2026): caso de estudio principal
│   └── escenario_B/                   Datos 2026 (semilla 2027): prueba de reproducibilidad
│       ├── glpi_tickets.xlsx, glpi_catalogos.xlsx, inventario_activos.xlsx, vulnerabilidades.xlsx   (zona de origen)
│       └── referencia_validacion/     Datos limpios, registro de problemas insertados e indicadores de referencia
├── etl/power_query/                   Consultas M de Power Query (función fnHoja, parámetro RutaDatos y reglas R1–R9)
├── modelo/modelo_dax.md               Relaciones, tablas y columnas calculadas y las 26 medidas DAX
├── powerbi/
│   ├── TFM_Tablero_v4.pbix            Tablero con el escenario A
│   └── TFM_Tablero_v4_escenarioB.pbix Tablero con el escenario B
├── validacion/evaluar_reglas.py       Réplica en Python de las reglas R1–R9 y comparación con la referencia
└── resultados/                        Resultados de la validación de cada escenario (CSV)
```

## Flujo de los datos

Los datos se organizan en tres zonas (arquitectura por capas o medallón):

1. **Zona de origen (bronce):** los archivos Excel de `datos/escenario_X/`, tal como los produce el generador. Nunca se editan.
2. **Zona depurada (plata):** las consultas de `etl/power_query/`, que aplican las reglas de calidad:

   | Regla | Problema | Acción |
   |---|---|---|
   | R1 | Ticket duplicado | Eliminar la copia |
   | R2 | Categoría escrita de forma distinta al catálogo | Normalizar con una clave sin espacios y en mayúsculas |
   | R3 | Nombre de técnico con formato irregular | Recortar espacios y aplicar formato de nombre propio |
   | R4 | Prioridad vacía o igual a 0 | Recalcular con la matriz de urgencia e impacto y marcar |
   | R5 | Ticket resuelto sin fecha de resolución | Marcar y excluir del MTTR y del SLA |
   | R6 | Cierre anterior a la apertura | Marcar |
   | R7 | Hallazgo duplicado | Eliminar la copia |
   | R8 | CVSS vacío o fuera de 0–10 | Marcar y conservar la severidad informada |
   | R9 | Severidad incoherente con el CVSS | Recalcular según la escala del CVSS y marcar |

3. **Zona de modelo (oro):** el modelo en estrella de Power BI (2 tablas de hechos y 7 dimensiones) y las medidas de `modelo/modelo_dax.md`.

## Cómo reproducir los resultados

### 1. Generar los datos (opcional: ya están en `datos/`)

Requisitos: Python 3.10 o superior, `numpy`, `pandas` y `openpyxl` (`pip install -r requirements.txt`).

```bash
# Escenario A (caso de estudio): sin parámetros
python generador/generador_datos_seguridad.py --salida datos/escenario_A

# Escenario B (reproducibilidad): otra semilla, otro periodo, 1,5 veces el volumen y el doble de errores
python generador/generador_datos_seguridad.py --semilla 2027 --inicio 2026-01-01 --fin 2026-12-31 --escala 1.5 --factor-errores 2 --salida datos/escenario_B
```

Con la misma semilla y los mismos parámetros, el generador produce exactamente los mismos archivos.

### 2. Abrir el tablero

1. Abrir `powerbi/TFM_Tablero_v4.pbix` con Power BI Desktop.
2. En **Transformar datos › Administrar parámetros**, indicar en `RutaDatos` la carpeta de los datos, terminada en `\` (por ejemplo, `C:\TFM_Tablero_Seguridad\datos\escenario_A\`).
3. Para el escenario B, cambiar además la fecha de corte de la tabla calculada `Parámetros` a `DATE(2026,12,31) + TIME(18,0,0)`.
4. Pulsar **Actualizar**. Si aparece el error *Formula.Firewall*, seleccionar **Archivo › Opciones › Privacidad › Ignorar los niveles de privacidad**.

### 3. Verificar las reglas y los indicadores

```bash
python validacion/evaluar_reglas.py datos/escenario_A resultados/escenario_A
python validacion/evaluar_reglas.py datos/escenario_B resultados/escenario_B
```

El script compara, registro a registro, los problemas detectados con los insertados por el generador y los indicadores calculados con los de referencia.

## Resultados principales

| | Escenario A | Escenario B |
|---|---|---|
| Periodo | 2024–2025 | 2026 |
| Tickets / hallazgos cargados | 2 276 / 738 | 2 037 / 1 127 |
| Problemas de calidad insertados | 220 | 440 |
| Problemas detectados (falsos positivos) | 220 (0) | 440 (0) |
| Indicadores iguales a la referencia | 14 de 16 | 14 de 16 |

Las dos diferencias (tiempo medio de resolución y cumplimiento del SLA) se deben a los tickets sin fecha de resolución, que el tablero excluye del cálculo por la regla R5: −0,06 h y −0,04 puntos en el escenario A, y −0,13 h y −0,01 puntos en el escenario B.

## Uso de inteligencia artificial

El generador de datos, los scripts de validación y parte de las consultas se desarrollaron con apoyo de una herramienta de inteligencia artificial (Claude, de Anthropic) y fueron revisados por la autora. El detalle se recoge en el Anexo B de la memoria.

## Licencia

- Código (`generador/`, `etl/`, `validacion/`, `modelo/`): licencia MIT (ver `LICENSE`).
- Datos simulados (`datos/`, `resultados/`): Creative Commons Atribución 4.0 Internacional (CC BY 4.0).

## Cómo citar

Pesántez Prado, M. D. (2026). *Metodología para diseñar y validar tableros de indicadores de seguridad de la información* [Trabajo Fin de Máster, Universidad Internacional de La Rioja]. https://github.com/USUARIO/TFM_Tablero_Seguridad
