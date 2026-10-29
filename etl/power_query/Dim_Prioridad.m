let
    Origen = fnHoja("glpi_catalogos.xlsx", "sla"),
    Tipos = Table.TransformColumnTypes(Origen, {{"prioridad", type text}, {"codigo", Int64.Type}, {"horas_sla", Int64.Type}}),
    Renombrar = Table.RenameColumns(Tipos, {{"prioridad", "Prioridad"}, {"horas_sla", "Horas SLA"}})
in
    Renombrar
