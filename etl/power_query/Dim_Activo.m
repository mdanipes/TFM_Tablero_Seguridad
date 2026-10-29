let
    Origen = fnHoja("inventario_activos.xlsx", "activos"),
    Tipos = Table.TransformColumnTypes(Origen, {{"activo_id", type text}, {"tipo_activo", type text},
        {"criticidad", type text}, {"area", type text}, {"sistema_operativo", type text}, {"expuesto_internet", type logical}})
in
    Tipos
