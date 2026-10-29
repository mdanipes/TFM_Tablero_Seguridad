# Modelo de Power BI: tablas calculadas, columnas calculadas, medidas y relaciones

Extraído del archivo `powerbi/TFM_Tablero_v4.pbix`.

## Relaciones

| Desde (N) | Hacia (1) | Activa | Filtro |
|---|---|---|---|
| Tickets[categoria_id] | Dim_Categoria[categoria_id] | Sí | Único |
| Vulnerabilidades[activo_id] | Dim_Activo[activo_id] | Sí | Único |
| Tickets[estado] | Dim_Estado[codigo] | Sí | Único |
| Tickets[prioridad] | Dim_Prioridad[codigo] | Sí | Único |
| Tickets[tipo] | Dim_Tipo[codigo] | Sí | Único |
| Tickets[origen_solicitud] | Dim_Origen[codigo] | Sí | Único |
| Tickets[activo_relacionado] | Dim_Activo[activo_id] | Sí | Único |
| Tickets[fecha] | Calendario[Date] | Sí | Único |
| Vulnerabilidades[fecha] | Calendario[Date] | Sí | Único |

## Tablas calculadas

### Calendario

```dax
Calendario =
VAR Inicio = MIN ( MIN ( Tickets[fecha] ), MIN ( Vulnerabilidades[fecha] ) )
VAR Fin = MAX ( 'Parámetros'[Fecha de corte] )
RETURN
    ADDCOLUMNS (
        CALENDAR ( DATE ( YEAR ( Inicio ), 1, 1 ), DATE ( YEAR ( Fin ), 12, 31 ) ),
        "Año", YEAR ( [Date] ),
        "Mes", MONTH ( [Date] ),
        "Nombre mes", FORMAT ( [Date], "mmm" ),
        "Año-Mes", FORMAT ( [Date], "yyyy-mm" ),
        "Trimestre", "T" & QUARTER ( [Date] )
    )
```

### Tipos de problema

```dax
Tipos de problema =
DATATABLE (
    "Orden", INTEGER,
    "Problema", STRING,
    {
        { 1, "Resueltos sin fecha" },
        { 2, "Cierre antes de apertura" },
        { 3, "Prioridad recalculada" },
        { 4, "CVSS fuera de rango" },
        { 5, "Severidad corregida" }
    }
)
```

### Parámetros

```dax
Parámetros =
ROW ( "Fecha de corte", DATE ( 2025, 12, 31 ) + TIME ( 18, 0, 0 ) )
```

## Columnas calculadas

### Tickets[Días abierto]

```dax
VAR Corte = MAX ( 'Parámetros'[Fecha de corte] )
RETURN
    IF ( Tickets[estado] <= 4, DATEDIFF ( Tickets[fecha_apertura], Corte, DAY ) )
```

### Tickets[SLA vencido]

```dax
VAR Corte = MAX ( 'Parámetros'[Fecha de corte] )
RETURN
    IF ( Tickets[estado] <= 4, IF ( Tickets[tiempo_para_resolver] < Corte, 1, 0 ) )
```

### Dim_Activo[Expuesto a Internet]

```dax
IF ( Dim_Activo[expuesto_internet], "Sí", "No" )
```

## Medidas (26)

### Total tickets

```dax
Total tickets =
COUNTROWS ( Tickets )
```

### Incidentes

```dax
Incidentes =
CALCULATE ( [Total tickets], Tickets[tipo] = 1 )
```

### Solicitudes

```dax
Solicitudes =
CALCULATE ( [Total tickets], Tickets[tipo] = 2 )
```

### Tickets abiertos

```dax
Tickets abiertos =
CALCULATE ( [Total tickets], Tickets[estado] <= 4 )
```

### Incidentes prioridad alta o más

```dax
Incidentes prioridad alta o más =
CALCULATE ( [Incidentes], Tickets[prioridad] >= 4 )
```

### MTTR (horas)

```dax
MTTR (horas) =
AVERAGE ( Tickets[horas_resolucion] )
```

### % SLA cumplido

```dax
% SLA cumplido =
DIVIDE ( SUM ( Tickets[sla_cumplido] ), COUNT ( Tickets[sla_cumplido] ) )
```

### Hallazgos

```dax
Hallazgos =
COUNTROWS ( Vulnerabilidades )
```

### Vulnerabilidades abiertas

```dax
Vulnerabilidades abiertas =
CALCULATE ( [Hallazgos], Vulnerabilidades[estado] = "Abierta" )
```

### Días medios de remediación

```dax
Días medios de remediación =
AVERAGE ( Vulnerabilidades[dias_remediacion] )
```

### Tickets con resolución incompleta

```dax
Tickets con resolución incompleta =
CALCULATE ( [Total tickets], Tickets[resolucion_incompleta] = TRUE () )
```

### Tickets con cierre inválido

```dax
Tickets con cierre inválido =
CALCULATE ( [Total tickets], Tickets[cierre_invalido] = TRUE () )
```

### Tickets con prioridad recalculada

```dax
Tickets con prioridad recalculada =
CALCULATE ( [Total tickets], Tickets[prioridad_recalculada] = TRUE () )
```

### Hallazgos con CVSS inválido

```dax
Hallazgos con CVSS inválido =
CALCULATE ( [Hallazgos], Vulnerabilidades[cvss_valido] = FALSE () )
```

### Hallazgos con severidad corregida

```dax
Hallazgos con severidad corregida =
CALCULATE ( [Hallazgos], Vulnerabilidades[severidad_corregida] = TRUE () )
```

### Críticas abiertas

```dax
Críticas abiertas =
CALCULATE ( [Vulnerabilidades abiertas], Vulnerabilidades[severidad_final] = "Crítica" )
```

### MTTR (días)

```dax
MTTR (días) =
DIVIDE ( [MTTR (horas)], 24 )
```

### Título origen

```dax
Título origen =
VAR TopOrigen =
    TOPN ( 1, VALUES ( Dim_Origen[Origen] ), [Total tickets], DESC )
VAR Nombre = MAXX ( TopOrigen, Dim_Origen[Origen] )
VAR Pct =
    DIVIDE (
        CALCULATE ( [Total tickets], Dim_Origen[Origen] = Nombre ),
        CALCULATE ( [Total tickets], ALL ( Dim_Origen ) )
    )
RETURN
    "Canal principal: " & Nombre & " (" & FORMAT ( Pct, "0 %" ) & " de los tickets)"
```

### Meta SLA

```dax
Meta SLA =
0.85
```

### Color críticas

```dax
Color críticas =
IF ( [Críticas abiertas] > 0, "#C0392B", "#333333" )
```

### Críticas abiertas (tarjeta)

```dax
Críticas abiertas (tarjeta) =
COALESCE ( [Críticas abiertas], 0 )
```

### Vulnerabilidades abiertas (tarjeta)

```dax
Vulnerabilidades abiertas (tarjeta) =
COALESCE ( [Vulnerabilidades abiertas], 0 )
```

### % Remediadas

```dax
% Remediadas =
DIVIDE (
    CALCULATE ( [Hallazgos], Vulnerabilidades[estado] = "Remediada" ),
    [Hallazgos]
)
```

### Tickets abiertos (tarjeta)

```dax
Tickets abiertos (tarjeta) =
COALESCE ( [Tickets abiertos], 0 )
```

### Color SLA

```dax
Color SLA =
IF ( [% SLA cumplido] < [Meta SLA], "#C0392B", "#333333" )
```

### Registros con problema

```dax
Registros con problema =
SWITCH (
    SELECTEDVALUE ( 'Tipos de problema'[Problema] ),
    "Resueltos sin fecha",       [Tickets con resolución incompleta],
    "Cierre antes de apertura",  [Tickets con cierre inválido],
    "Prioridad recalculada",     [Tickets con prioridad recalculada],
    "CVSS fuera de rango",       [Hallazgos con CVSS inválido],
    "Severidad corregida",       [Hallazgos con severidad corregida]
)
```

