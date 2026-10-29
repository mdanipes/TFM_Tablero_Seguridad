let
    Origen = fnHoja("glpi_catalogos.xlsx", "tipos"),
    Tipos = Table.TransformColumnTypes(Origen, {{"codigo", Int64.Type}, {"nombre", type text}}),
    Renombrar = Table.RenameColumns(Tipos, {{"nombre", "Tipo de ticket"}})
in
    Renombrar
