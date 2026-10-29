let
    Origen = fnHoja("glpi_catalogos.xlsx", "categorias"),
    Tipos = Table.TransformColumnTypes(Origen, {{"categoria_id", Int64.Type}, {"categoria", type text},
        {"tipo", type text}, {"grupo_responsable", type text}}),
    // Clave para comparar sin importar mayúsculas ni espacios (se usa en la regla R2 de Tickets)
    Clave = Table.AddColumn(Tipos, "clave_categoria", each Text.Upper(Text.Replace(Text.Trim([categoria]), " ", "")), type text),
    // Último nivel de la categoría, más corto para los gráficos (p. ej. "Malware")
    Subcategoria = Table.AddColumn(Clave, "Subcategoría", each List.Last(Text.Split([categoria], " > ")), type text)
in
    Subcategoria
