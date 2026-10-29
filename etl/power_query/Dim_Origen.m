let
    Origen = fnHoja("glpi_catalogos.xlsx", "origenes"),
    Tipos = Table.TransformColumnTypes(Origen, {{"codigo", Int64.Type}, {"nombre", type text}}),
    Renombrar = Table.RenameColumns(Tipos, {{"nombre", "Origen"}})
in
    Renombrar
