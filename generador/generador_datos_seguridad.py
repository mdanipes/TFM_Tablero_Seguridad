"""
Generador de datos SIMULADOS para el TFM: tablero de indicadores de seguridad
de la información en Power BI.

Produce tres fuentes, con la estructura pública del software GLPI (tickets)
y de un escáner de vulnerabilidades genérico:
  - glpi_tickets.xlsx         incidentes y solicitudes del área de seguridad
  - glpi_catalogos.xlsx       tablas de códigos (estado, prioridad, tipo, origen, categorías)
  - inventario_activos.xlsx   activos tecnológicos y su criticidad
  - vulnerabilidades.xlsx     hallazgos de escaneos mensuales

Los datos son ficticios. Se insertan a propósito problemas de calidad típicos
(duplicados, fechas incoherentes, textos escritos de formas distintas, valores
fuera de rango) para que el ETL en Power Query tenga que detectarlos y corregirlos.
Se guardan también la versión limpia y los indicadores de referencia, para
comprobar que Power BI calcula bien cada indicador.

Uso (escenario A, por defecto):  py generador_datos_seguridad.py
Uso (escenario B):  py generador_datos_seguridad.py --semilla 2027 --inicio 2026-01-01 --fin 2026-12-31 --escala 1.5 --factor-errores 2 --salida datos_seguridad_2026
Requisitos: numpy, pandas, openpyxl
Generado con apoyo de IA (Claude, Anthropic) y revisado por la autora.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEMILLA = 2026
INICIO, FIN = pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31 23:59")
CORTE = pd.Timestamp("2025-12-31 18:00")  # fecha de extracción de los datos
rng = np.random.default_rng(SEMILLA)
SALIDA = Path("datos_seguridad")
ESCALA = 1.0          # multiplica el volumen de tickets y de hallazgos
FACTOR_ERRORES = 1.0  # multiplica el número de problemas de calidad insertados


def n_err(base):
    """Número de registros afectados por un tipo de problema."""
    return int(round(base * FACTOR_ERRORES))

# ------------------------------------------------------------------ catálogos (códigos de GLPI)
ESTADOS = {1: "Nuevo", 2: "En curso (asignado)", 3: "En curso (planificado)", 4: "En espera", 5: "Resuelto", 6: "Cerrado"}
PRIORIDADES = {1: "Muy baja", 2: "Baja", 3: "Media", 4: "Alta", 5: "Muy alta", 6: "Mayor"}
NIVELES = {1: "Muy baja", 2: "Baja", 3: "Media", 4: "Alta", 5: "Muy alta"}  # urgencia e impacto
TIPOS = {1: "Incidente", 2: "Solicitud"}
ORIGENES = {1: "Helpdesk", 2: "Correo electrónico", 3: "Teléfono", 4: "Alerta SIEM", 5: "Directo"}
SLA_HORAS = {6: 4, 5: 8, 4: 24, 3: 72, 2: 120, 1: 240}  # tiempo máximo para resolver, por prioridad

# (id, nombre completo, tipo, peso relativo, grupo que atiende)
CATEGORIAS = [
    (11, "Seguridad > Incidente > Phishing o correo malicioso", 1, 30, "Seguridad - SOC"),
    (12, "Seguridad > Incidente > Malware", 1, 14, "Seguridad - SOC"),
    (13, "Seguridad > Incidente > Acceso no autorizado", 1, 8, "Seguridad - SOC"),
    (14, "Seguridad > Incidente > Fuga o pérdida de información", 1, 3, "Seguridad - SOC"),
    (15, "Seguridad > Incidente > Denegación de servicio", 1, 2, "Seguridad - Infraestructura"),
    (16, "Seguridad > Incidente > Explotación de vulnerabilidad", 1, 4, "Seguridad - Vulnerabilidades"),
    (17, "Seguridad > Incidente > Pérdida o robo de equipo", 1, 3, "Seguridad - Gestión de accesos"),
    (18, "Seguridad > Incidente > Uso indebido de recursos", 1, 5, "Seguridad - SOC"),
    (21, "Seguridad > Solicitud > Alta o baja de accesos", 2, 35, "Seguridad - Gestión de accesos"),
    (22, "Seguridad > Solicitud > Revisión de regla de firewall", 2, 15, "Seguridad - Infraestructura"),
    (23, "Seguridad > Solicitud > Acceso VPN", 2, 12, "Seguridad - Gestión de accesos"),
    (24, "Seguridad > Solicitud > Excepción de política", 2, 5, "Seguridad - Gestión de accesos"),
    (25, "Seguridad > Solicitud > Análisis de archivo sospechoso", 2, 10, "Seguridad - SOC"),
    (26, "Seguridad > Solicitud > Revisión de configuración segura", 2, 6, "Seguridad - Vulnerabilidades"),
]
TECNICOS = {"Seguridad - SOC": ["Analista 01", "Analista 02", "Analista 03"],
            "Seguridad - Gestión de accesos": ["Analista 04", "Analista 05"],
            "Seguridad - Infraestructura": ["Analista 06", "Analista 07"],
            "Seguridad - Vulnerabilidades": ["Analista 08"]}


def prioridad(urgencia, impacto):
    """Matriz de prioridad similar a la de GLPI: combina urgencia e impacto."""
    p = int(np.ceil((urgencia + impacto) / 2))
    if urgencia == 5 and impacto == 5:
        p = 6
    return max(1, min(6, p))


# ------------------------------------------------------------------ activos
def generar_activos():
    tipos = [("Servidor", "SRV", 45), ("Estación de trabajo", "PC", 40), ("Equipo de red", "RED", 15),
             ("Aplicación web", "APP", 12), ("Base de datos", "BD", 8)]
    areas = ["Operaciones", "Comercial", "Financiera", "Talento Humano", "Tecnología", "Gerencia"]
    so = {"Servidor": ["Windows Server 2019", "Windows Server 2022", "Linux Ubuntu 22.04", "Linux RHEL 8"],
          "Estación de trabajo": ["Windows 10", "Windows 11"], "Equipo de red": ["Firmware propietario"],
          "Aplicación web": ["Linux Ubuntu 22.04", "Windows Server 2019"], "Base de datos": ["Linux RHEL 8", "Windows Server 2022"]}
    filas = []
    for tipo, pref, n in tipos:
        for i in range(1, n + 1):
            crit = rng.choice(["Alta", "Media", "Baja"], p=[.5, .35, .15] if tipo in ("Servidor", "Base de datos", "Aplicación web")
                              else [.1, .4, .5])
            filas.append(dict(activo_id=f"{pref}-{i:03d}", tipo_activo=tipo, criticidad=crit,
                              area=rng.choice(areas), sistema_operativo=rng.choice(so[tipo]),
                              expuesto_internet=bool(tipo == "Aplicación web" or (tipo == "Servidor" and rng.random() < .15))))
    return pd.DataFrame(filas)


# ------------------------------------------------------------------ tickets
def generar_tickets(activos):
    dias = pd.date_range(INICIO, FIN.normalize(), freq="D")
    cat_ids = [c[0] for c in CATEGORIAS]
    pesos = np.array([c[3] for c in CATEGORIAS], float); pesos /= pesos.sum()
    # campañas de phishing: algunas semanas con muchos más casos
    campanas = set(rng.choice(len(dias), 8, replace=False))
    filas, tid = [], 1000
    for k, d in enumerate(dias):
        base = 3.2 if d.weekday() < 5 else 0.6
        base *= (1 + 0.15 * (d.year - 2024)) * ESCALA  # leve aumento anual
        n = rng.poisson(base)
        extra_phishing = rng.poisson(12) if any(0 <= k - c < 3 for c in campanas) else 0
        elegidos = list(rng.choice(cat_ids, n, p=pesos)) + [11] * extra_phishing
        for cat in elegidos:
            c = next(x for x in CATEGORIAS if x[0] == cat)
            hora = rng.uniform(7.5, 17.5) if d.weekday() < 5 and rng.random() < .85 else rng.uniform(0, 24)
            apertura = (d + pd.Timedelta(hours=float(hora))).floor("min")
            tipo = c[2]
            if tipo == 1:
                urg = int(rng.choice([2, 3, 4, 5], p=[.2, .4, .3, .1])); imp = int(rng.choice([2, 3, 4, 5], p=[.3, .4, .2, .1]))
                if cat in (14, 16): urg, imp = max(urg, 4), max(imp, 4)
            else:
                urg = int(rng.choice([1, 2, 3, 4], p=[.2, .4, .3, .1])); imp = int(rng.choice([1, 2, 3], p=[.4, .4, .2]))
            pri = prioridad(urg, imp)
            sla = SLA_HORAS[pri]
            # tiempo real de resolución: ~82 % dentro del SLA
            h = float(np.clip(rng.lognormal(np.log(sla * 0.45), 0.75), 0.1, sla * 8))
            resolucion = (apertura + pd.Timedelta(hours=h)).floor("min")
            cierre = (resolucion + pd.Timedelta(hours=float(rng.uniform(1, 96)))).floor("min")
            # parte de los tickets recientes sigue pendiente (backlog), p. ej. a la espera del usuario
            reciente = apertura > CORTE - pd.Timedelta(days=30)
            if resolucion > CORTE or (reciente and rng.random() < 0.08):
                estado = int(rng.choice([1, 2, 3, 4], p=[.2, .5, .1, .2])); resolucion = cierre = pd.NaT
            elif cierre > CORTE:
                estado = 5; cierre = pd.NaT
            else:
                estado = 6
            grupo = c[4]
            origen = 4 if (cat in (12, 13, 15, 16) and rng.random() < .6) else int(rng.choice([1, 2, 3, 5], p=[.5, .3, .1, .1]))
            activo = rng.choice(activos.activo_id) if tipo == 1 and cat not in (11,) and rng.random() < .8 else ""
            tid += 1
            filas.append({"id": tid, "titulo": c[1].split(" > ")[-1] + f" #{tid}", "tipo": tipo, "estado": estado,
                          "prioridad": pri, "urgencia": urg, "impacto": imp, "categoria": c[1],
                          "origen_solicitud": origen, "grupo_asignado": grupo, "tecnico_asignado": rng.choice(TECNICOS[grupo]),
                          "solicitante": f"usuario{int(rng.integers(1, 900)):04d}", "activo_relacionado": activo,
                          "fecha_apertura": apertura, "tiempo_para_resolver": apertura + pd.Timedelta(hours=sla),
                          "fecha_resolucion": resolucion, "fecha_cierre": cierre})
    return pd.DataFrame(filas)


# ------------------------------------------------------------------ vulnerabilidades
VULNS = [("Protocolo TLS 1.0/1.1 habilitado", 5.3), ("SMBv1 habilitado", 8.1), ("Certificado SSL caducado", 5.0),
         ("Servidor web con versión obsoleta", 7.5), ("Parche de seguridad de sistema operativo pendiente", 8.8),
         ("Contraseña por defecto en equipo de red", 9.8), ("Servicio Telnet expuesto", 7.4),
         ("Inyección SQL en formulario", 9.1), ("Cross-site scripting (XSS) reflejado", 6.1),
         ("Cabeceras de seguridad HTTP ausentes", 3.7), ("Listado de directorios habilitado", 5.3),
         ("Cifrados débiles en SSH", 4.3), ("Escritorio remoto sin autenticación de red", 7.5),
         ("Software antivirus desactualizado", 6.5), ("Navegador desactualizado", 6.8),
         ("Base de datos accesible sin cifrado", 7.2), ("Ejecución remota de código en servicio", 9.8),
         ("Divulgación de información en mensajes de error", 3.1), ("Cuenta de servicio con privilegios excesivos", 6.4),
         ("Puerto de administración expuesto", 5.8)]


def severidad(cvss):
    if cvss >= 9: return "Crítica"
    if cvss >= 7: return "Alta"
    if cvss >= 4: return "Media"
    return "Baja" if cvss > 0 else "Informativa"


def generar_vulnerabilidades(activos):
    """Escaneo mensual: cada hallazgo aparece al detectarse y se remedia con el tiempo."""
    filas, hid = [], 1
    meses = pd.date_range(INICIO, FIN, freq="MS")
    for _, a in activos.iterrows():
        n = rng.poisson((8 if a.tipo_activo in ("Servidor", "Aplicación web") else 5) * ESCALA)
        for _ in range(n):
            nombre, cvss = VULNS[int(rng.integers(len(VULNS)))]
            cvss = float(np.clip(round(cvss + rng.normal(0, .3), 1), 0.1, 10))
            det = meses[int(rng.integers(len(meses)))] + pd.Timedelta(days=int(rng.integers(0, 5)), hours=int(rng.integers(8, 18)))
            sev = severidad(cvss)
            objetivo = {"Crítica": 15, "Alta": 30, "Media": 90, "Baja": 180}[sev]  # días objetivo de remediación
            factor = 0.7 if a.criticidad == "Alta" else 1.2
            dias = float(rng.lognormal(np.log(objetivo * 0.6 * factor), 0.7))
            rem = det + pd.Timedelta(days=dias)
            if rng.random() < 0.05:
                estado, rem = "Riesgo aceptado", pd.NaT
            elif sev in ("Crítica", "Alta") and det > CORTE - pd.Timedelta(days=120) and rng.random() < 0.15:
                estado, rem = "Abierta", pd.NaT  # remediación vencida
            elif rem > CORTE:
                estado, rem = "Abierta", pd.NaT
            else:
                estado = "Remediada"
            filas.append(dict(hallazgo_id=f"H-{hid:05d}", activo_id=a.activo_id, vulnerabilidad=nombre, cvss=cvss,
                              severidad=sev, fecha_deteccion=det.floor("min"), estado=estado,
                              fecha_remediacion=rem.floor("min") if pd.notna(rem) else pd.NaT))
            hid += 1
    return pd.DataFrame(filas).sort_values("fecha_deteccion").reset_index(drop=True)


# ------------------------------------------------------------------ problemas de calidad (con registro)
def ensuciar(tk, vu):
    reg = []
    tk = tk.copy(); vu = vu.copy()
    tk["categoria"] = tk["categoria"].astype(object); tk["tecnico_asignado"] = tk["tecnico_asignado"].astype(object)

    def anotar(tabla, ids, problema, regla):
        for i in ids:
            reg.append(dict(tabla=tabla, id=i, problema=problema, regla_etl=regla))

    # 1. Categorías escritas de otra forma
    idx = rng.choice(tk.index, n_err(60), replace=False)
    for i in idx:
        c = tk.at[i, "categoria"]
        tk.at[i, "categoria"] = rng.choice([c.upper(), c.replace(" > ", ">"), c + " ", c.lower()])
    anotar("tickets", tk.loc[idx, "id"], "categoría escrita de forma distinta", "normalizar texto (recortar, mayúsculas, separador)")
    # 2. Técnicos con mayúsculas/espacios inconsistentes
    idx = rng.choice(tk.index, n_err(40), replace=False)
    tk.loc[idx, "tecnico_asignado"] = tk.loc[idx, "tecnico_asignado"].map(lambda s: rng.choice([s.upper(), " " + s, s.lower()]))
    anotar("tickets", tk.loc[idx, "id"], "nombre de técnico con formato inconsistente", "recortar espacios y usar formato de nombre propio")
    # 3. Resuelto/cerrado sin fecha de resolución
    cand = tk.index[tk.estado.isin([5, 6])]
    idx = rng.choice(cand, n_err(15), replace=False); tk.loc[idx, "fecha_resolucion"] = pd.NaT
    anotar("tickets", tk.loc[idx, "id"], "estado resuelto/cerrado sin fecha de resolución", "excluir del cálculo de tiempos y marcar como incompleto")
    # 4. Fecha de cierre anterior a la de apertura
    cand = tk.index[tk.estado == 6]
    idx = rng.choice(cand, n_err(10), replace=False)
    tk.loc[idx, "fecha_cierre"] = tk.loc[idx, "fecha_apertura"] - pd.Timedelta(days=2)
    anotar("tickets", tk.loc[idx, "id"], "fecha de cierre anterior a la apertura", "marcar como fecha inválida y excluir de tiempos de cierre")
    # 5. Prioridad vacía
    idx = rng.choice(tk.index, n_err(20), replace=False); tk.loc[idx, "prioridad"] = 0
    anotar("tickets", tk.loc[idx, "id"], "prioridad vacía (0)", "recalcular con la matriz urgencia x impacto")
    # 6. Tickets duplicados (exportación repetida)
    idx = rng.choice(tk.index, n_err(25), replace=False)
    tk = pd.concat([tk, tk.loc[idx]]).sort_values(["fecha_apertura", "id"]).reset_index(drop=True)
    reg.extend(dict(tabla="tickets", id=i, problema="ticket duplicado", regla_etl="eliminar duplicados por id") for i in
               tk[tk.duplicated("id")]["id"])
    # 7. Vulnerabilidades: CVSS fuera de rango, severidad incoherente, duplicados
    idx = rng.choice(vu.index, n_err(12), replace=False)
    vu["cvss"] = vu["cvss"].astype(float)
    vu.loc[idx, "cvss"] = rng.choice([-1.0, 11.0, 99.0], len(idx))
    anotar("vulnerabilidades", vu.loc[idx, "hallazgo_id"], "CVSS fuera de rango (0-10)", "marcar CVSS inválido; usar la severidad informada")
    idx = rng.choice(vu.index.difference(idx), n_err(20), replace=False)
    vu.loc[idx, "severidad"] = vu.loc[idx, "severidad"].map({"Crítica": "Media", "Alta": "Baja", "Media": "Alta", "Baja": "Crítica"}).fillna("Media")
    anotar("vulnerabilidades", vu.loc[idx, "hallazgo_id"], "severidad incoherente con el CVSS", "recalcular la severidad a partir del CVSS")
    idx = rng.choice(vu.index, n_err(18), replace=False)
    vu = pd.concat([vu, vu.loc[idx]]).sort_values("fecha_deteccion").reset_index(drop=True)
    reg.extend(dict(tabla="vulnerabilidades", id=i, problema="hallazgo duplicado", regla_etl="eliminar duplicados por hallazgo_id")
               for i in vu[vu.duplicated("hallazgo_id")]["hallazgo_id"])
    return tk, vu, pd.DataFrame(reg)


# ------------------------------------------------------------------ indicadores de referencia (sobre datos limpios)
def indicadores(tk, vu):
    t = tk.copy()
    t["mes"] = t.fecha_apertura.dt.to_period("M").astype(str)
    t["horas_resolucion"] = (t.fecha_resolucion - t.fecha_apertura).dt.total_seconds() / 3600
    t["sla_cumplido"] = t.fecha_resolucion <= t.tiempo_para_resolver
    res = t[t.fecha_resolucion.notna()]
    mensual = t.groupby("mes").agg(tickets=("id", "count"), incidentes=("tipo", lambda s: (s == 1).sum()),
                                   solicitudes=("tipo", lambda s: (s == 2).sum()),
                                   incidentes_prioridad_alta_o_mas=("prioridad", lambda s: ((s >= 4) & (t.loc[s.index, "tipo"] == 1)).sum()))
    mensual = mensual.join(res.groupby("mes").agg(mttr_horas=("horas_resolucion", "mean"),
                                                   pct_sla_cumplido=("sla_cumplido", lambda s: 100 * s.mean())))
    por_prioridad = res.groupby("prioridad").agg(tickets_resueltos=("id", "count"), mttr_horas=("horas_resolucion", "mean"),
                                                 pct_sla_cumplido=("sla_cumplido", lambda s: 100 * s.mean()))
    por_prioridad.index = por_prioridad.index.map(PRIORIDADES)
    por_categoria = t.groupby("categoria").agg(tickets=("id", "count")).sort_values("tickets", ascending=False)
    v = vu.copy()
    v["dias_remediacion"] = (v.fecha_remediacion - v.fecha_deteccion).dt.total_seconds() / 86400
    vuln_sev = v.groupby("severidad").agg(hallazgos=("hallazgo_id", "count"),
                                           abiertas_al_corte=("estado", lambda s: (s == "Abierta").sum()),
                                           dias_medios_remediacion=("dias_remediacion", "mean"))
    globales = pd.Series({
        "total_tickets": len(t), "total_incidentes": int((t.tipo == 1).sum()), "total_solicitudes": int((t.tipo == 2).sum()),
        "tickets_abiertos_al_corte": int(t.estado.isin([1, 2, 3, 4]).sum()),
        "mttr_horas_global": res.horas_resolucion.mean(), "pct_sla_cumplido_global": 100 * res.sla_cumplido.mean(),
        "total_hallazgos_vulnerabilidad": len(v), "vulnerabilidades_abiertas_al_corte": int((v.estado == "Abierta").sum()),
        "vulnerabilidades_criticas_abiertas": int(((v.estado == "Abierta") & (v.severidad == "Crítica")).sum())})
    return {k: x.round(2) for k, x in dict(globales=globales.to_frame("valor"), mensual=mensual, por_prioridad=por_prioridad,
                                           por_categoria=por_categoria, vulnerabilidades_por_severidad=vuln_sev).items()}


def main():
    global SEMILLA, INICIO, FIN, CORTE, rng, SALIDA, ESCALA, FACTOR_ERRORES
    ap = argparse.ArgumentParser(description="Generador de datos simulados del TFM")
    ap.add_argument("--semilla", type=int, default=SEMILLA)
    ap.add_argument("--inicio", default=str(INICIO.date()), help="primer día del periodo (AAAA-MM-DD)")
    ap.add_argument("--fin", default=str(FIN.date()), help="último día del periodo (AAAA-MM-DD); el corte es ese día a las 18:00")
    ap.add_argument("--escala", type=float, default=ESCALA)
    ap.add_argument("--factor-errores", type=float, default=FACTOR_ERRORES)
    ap.add_argument("--salida", default=str(SALIDA))
    a = ap.parse_args()
    SEMILLA, ESCALA, FACTOR_ERRORES, SALIDA = a.semilla, a.escala, a.factor_errores, Path(a.salida)
    INICIO = pd.Timestamp(a.inicio); FIN = pd.Timestamp(a.fin) + pd.Timedelta(hours=23, minutes=59)
    CORTE = pd.Timestamp(a.fin) + pd.Timedelta(hours=18)
    rng = np.random.default_rng(SEMILLA)
    SALIDA.mkdir(exist_ok=True)
    activos = generar_activos()
    tickets = generar_tickets(activos)
    vulns = generar_vulnerabilidades(activos)
    tk_sucio, vu_sucio, registro = ensuciar(tickets, vulns)

    tk_sucio.to_excel(SALIDA / "glpi_tickets.xlsx", index=False, sheet_name="tickets")
    with pd.ExcelWriter(SALIDA / "glpi_catalogos.xlsx") as w:
        for nombre, d in [("estados", ESTADOS), ("prioridades", PRIORIDADES), ("urgencia_impacto", NIVELES),
                          ("tipos", TIPOS), ("origenes", ORIGENES)]:
            pd.DataFrame(list(d.items()), columns=["codigo", "nombre"]).to_excel(w, sheet_name=nombre, index=False)
        pd.DataFrame([dict(categoria_id=c[0], categoria=c[1], tipo=TIPOS[c[2]], grupo_responsable=c[4]) for c in CATEGORIAS]) \
            .to_excel(w, sheet_name="categorias", index=False)
        pd.DataFrame([dict(prioridad=PRIORIDADES[k], codigo=k, horas_sla=v) for k, v in SLA_HORAS.items()]) \
            .to_excel(w, sheet_name="sla", index=False)
    activos.to_excel(SALIDA / "inventario_activos.xlsx", index=False, sheet_name="activos")
    vu_sucio.to_excel(SALIDA / "vulnerabilidades.xlsx", index=False, sheet_name="hallazgos")

    ref = SALIDA / "referencia_validacion"; ref.mkdir(exist_ok=True)
    tickets.to_excel(ref / "tickets_limpios.xlsx", index=False)
    vulns.to_excel(ref / "vulnerabilidades_limpias.xlsx", index=False)
    registro.to_excel(ref / "registro_problemas_calidad.xlsx", index=False)
    with pd.ExcelWriter(ref / "indicadores_referencia.xlsx") as w:
        for nombre, tabla in indicadores(tickets, vulns).items():
            tabla.to_excel(w, sheet_name=nombre)
    print(f"Tickets: {len(tickets)} (+{len(tk_sucio) - len(tickets)} duplicados) | Activos: {len(activos)} | "
          f"Hallazgos: {len(vulns)} (+{len(vu_sucio) - len(vulns)} duplicados)")
    print("Problemas de calidad insertados:\n", registro.groupby(["tabla", "problema"]).size().to_string())


if __name__ == "__main__":
    main()
