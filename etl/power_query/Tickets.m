let
    Origen = fnHoja("glpi_tickets.xlsx", "tickets"),
    Tipos = Table.TransformColumnTypes(Origen, {
        {"id", Int64.Type}, {"titulo", type text}, {"tipo", Int64.Type}, {"estado", Int64.Type},
        {"prioridad", Int64.Type}, {"urgencia", Int64.Type}, {"impacto", Int64.Type},
        {"categoria", type text}, {"origen_solicitud", Int64.Type}, {"grupo_asignado", type text},
        {"tecnico_asignado", type text}, {"solicitante", type text}, {"activo_relacionado", type text},
        {"fecha_apertura", type datetime}, {"tiempo_para_resolver", type datetime},
        {"fecha_resolucion", type datetime}, {"fecha_cierre", type datetime}}),

    // R1: quitar tickets duplicados
    R1_SinDuplicados = Table.Distinct(Tipos, {"id"}),

    // R2: normalizar la categoría uniéndola con el catálogo por una clave sin espacios y en mayúsculas
    R2_Clave = Table.AddColumn(R1_SinDuplicados, "clave_categoria",
        each Text.Upper(Text.Replace(Text.Trim([categoria]), " ", "")), type text),
    R2_Unir = Table.NestedJoin(R2_Clave, {"clave_categoria"}, Dim_Categoria, {"clave_categoria"}, "cat", JoinKind.LeftOuter),
    R2_Expandir = Table.ExpandTableColumn(R2_Unir, "cat", {"categoria_id"}, {"categoria_id"}),
    R2_Final = Table.RemoveColumns(R2_Expandir, {"categoria", "clave_categoria"}),

    // R3: nombre del técnico sin espacios sobrantes y en formato de nombre propio
    R3_Tecnico = Table.TransformColumns(R2_Final, {{"tecnico_asignado", each Text.Proper(Text.Trim(_)), type text}}),

    // R4: si la prioridad está vacía (0), recalcularla con la matriz urgencia x impacto
    R4_Marca = Table.AddColumn(R3_Tecnico, "prioridad_recalculada",
        each [prioridad] = null or [prioridad] = 0, type logical),
    R4_Prioridad = Table.AddColumn(R4_Marca, "prioridad_final",
        each if [prioridad_recalculada]
             then (if [urgencia] = 5 and [impacto] = 5 then 6 else Number.RoundUp(([urgencia] + [impacto]) / 2))
             else [prioridad], Int64.Type),
    R4_Final = Table.RenameColumns(Table.RemoveColumns(R4_Prioridad, {"prioridad"}), {{"prioridad_final", "prioridad"}}),

    // R5: resuelto o cerrado sin fecha de resolución (queda fuera del MTTR y del SLA)
    R5_Incompleta = Table.AddColumn(R4_Final, "resolucion_incompleta",
        each List.Contains({5, 6}, [estado]) and [fecha_resolucion] = null, type logical),

    // R6: fecha de cierre anterior a la apertura
    R6_CierreInvalido = Table.AddColumn(R5_Incompleta, "cierre_invalido",
        each [fecha_cierre] <> null and [fecha_cierre] < [fecha_apertura], type logical),

    // Columnas calculadas para los indicadores
    C1_Horas = Table.AddColumn(R6_CierreInvalido, "horas_resolucion",
        each if [fecha_resolucion] = null then null else Duration.TotalHours([fecha_resolucion] - [fecha_apertura]), type number),
    C2_SLA = Table.AddColumn(C1_Horas, "sla_cumplido",
        each if [fecha_resolucion] = null then null else if [fecha_resolucion] <= [tiempo_para_resolver] then 1 else 0, Int64.Type),
    C3_Fecha = Table.AddColumn(C2_SLA, "fecha", each DateTime.Date([fecha_apertura]), type date),
    #"Filas filtradas" = Table.SelectRows(C3_Fecha, each true)
in
    #"Filas filtradas"
