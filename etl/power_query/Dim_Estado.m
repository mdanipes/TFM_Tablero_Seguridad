let
    Origen = fnHoja("glpi_catalogos.xlsx", "estados"),
    Tipos = Table.TransformColumnTypes(Origen, {{"codigo", Int64.Type}, {"nombre", type text}}),
    Renombrar = Table.RenameColumns(Tipos, {{"nombre", "Estado"}}),
    // Agrupación útil para el tablero: abierto (1-4) o terminado (5-6)
    Situacion = Table.AddColumn(Renombrar, "Situación", each if [codigo] <= 4 then "Abierto" else "Terminado", type text)
in
    Situacion
