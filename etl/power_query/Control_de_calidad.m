let
    T0 = fnHoja("glpi_tickets.xlsx", "tickets"),
    V0 = fnHoja("vulnerabilidades.xlsx", "hallazgos"),
    T = Table.Distinct(T0, {"id"}),
    Catalogo = List.Buffer(Dim_Categoria[categoria]),
    R1 = Table.RowCount(T0) - Table.RowCount(T),
    R2 = Table.RowCount(Table.SelectRows(T, each not List.Contains(Catalogo, [categoria]))),
    R3 = Table.RowCount(Table.SelectRows(T, each [tecnico_asignado] <> null
            and Text.From([tecnico_asignado]) <> Text.Proper(Text.Trim(Text.From([tecnico_asignado]))))),
    R7 = Table.RowCount(V0) - Table.RowCount(Table.Distinct(V0, {"hallazgo_id"})),
    Resultado = #table(
        type table [Regla = text, Descripción = text, Registros = Int64.Type],
        {
            {"R1", "Tickets duplicados eliminados", R1},
            {"R2", "Tickets con categoría distinta del catálogo", R2},
            {"R3", "Tickets con nombre de técnico corregido", R3},
            {"R7", "Hallazgos duplicados eliminados", R7}
        })
in
    Resultado
