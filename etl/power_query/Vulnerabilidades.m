let
    Origen = fnHoja("vulnerabilidades.xlsx", "hallazgos"),
    Tipos = Table.TransformColumnTypes(Origen, {
        {"hallazgo_id", type text}, {"activo_id", type text}, {"vulnerabilidad", type text},
        {"cvss", type number}, {"severidad", type text}, {"fecha_deteccion", type datetime},
        {"estado", type text}, {"fecha_remediacion", type datetime}}),

    // R7: quitar hallazgos duplicados
    R7_SinDuplicados = Table.Distinct(Tipos, {"hallazgo_id"}),

    // R8: el CVSS solo es válido entre 0 y 10 (vacío = inválido)
    R8_CvssValido = Table.AddColumn(R7_SinDuplicados, "cvss_valido",
        each [cvss] <> null and [cvss] >= 0 and [cvss] <= 10, type logical),

    // R9: severidad calculada desde el CVSS (si el CVSS no es válido, se conserva la informada)
    R9_Severidad = Table.AddColumn(R8_CvssValido, "severidad_final",
        each if not [cvss_valido] then [severidad]
             else if [cvss] >= 9 then "Crítica"
             else if [cvss] >= 7 then "Alta"
             else if [cvss] >= 4 then "Media"
             else if [cvss] > 0 then "Baja"
             else "Ninguna", type text),
    R9_Marca = Table.AddColumn(R9_Severidad, "severidad_corregida", each [severidad_final] <> [severidad], type logical),

    // Columnas calculadas
    C1_Dias = Table.AddColumn(R9_Marca, "dias_remediacion",
        each if [fecha_remediacion] = null then null else Duration.TotalDays([fecha_remediacion] - [fecha_deteccion]), type number),
    C2_Fecha = Table.AddColumn(C1_Dias, "fecha", each DateTime.Date([fecha_deteccion]), type date),
    #"Personalizada agregada" = Table.AddColumn(C2_Fecha, "orden_severidad",
        each if [severidad_final] = "Crítica" then 1 else if [severidad_final] = "Alta" then 2
             else if [severidad_final] = "Media" then 3 else if [severidad_final] = "Baja" then 4 else 5),
    #"Tipo cambiado" = Table.TransformColumnTypes(#"Personalizada agregada", {{"orden_severidad", Int64.Type}})
in
    #"Tipo cambiado"
