// Función: lee una hoja de un archivo Excel de la carpeta RutaDatos y usa la primera fila como encabezados
(archivo as text, hoja as text) as table =>
let
    Origen = Excel.Workbook(File.Contents(RutaDatos & archivo), null, true),
    Datos = Origen{[Item = hoja, Kind = "Sheet"]}[Data],
    Encabezados = Table.PromoteHeaders(Datos, [PromoteAllScalars = true])
in
    Encabezados
