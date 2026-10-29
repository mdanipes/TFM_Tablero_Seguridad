"""Uso: python validacion/evaluar_reglas.py datos/escenario_A resultados/escenario_A

Aplica en Python las reglas R1-R9 (réplica del ETL de Power Query) a un conjunto generado,
evalúa la detección frente al registro de problemas y compara los indicadores con la referencia."""
import os, sys, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
D = sys.argv[1].rstrip('/') + '/'; R = D + 'referencia_validacion/'
t = pd.read_excel(D + 'glpi_tickets.xlsx'); v = pd.read_excel(D + 'vulnerabilidades.xlsx')
cat = pd.read_excel(D + 'glpi_catalogos.xlsx', sheet_name='categorias')
reg = pd.read_excel(R + 'registro_problemas_calidad.xlsx')
g = lambda p: set(reg[reg.problema == p].id.astype(str))
out = []
def ev(n, iny, det):
    iny, det = set(iny), set(det); out.append(dict(regla=n, insertados=len(iny), detectados=len(det), VP=len(iny & det), FP=len(det - iny), FN=len(iny - det)))
# R1
ev('R1', g('ticket duplicado'), t[t.duplicated('id')].id.astype(str)); t = t.drop_duplicates('id').copy()
# R2 clave sin espacios y en mayúsculas
key = lambda s: str(s).replace(' ', '').upper()
cmap = {key(c): i for c, i in zip(cat.categoria, cat.categoria_id)}
t['categoria_id'] = t.categoria.map(lambda s: cmap.get(key(s)))
ev('R2', g('categoría escrita de forma distinta'), t[~t.categoria.isin(cat.categoria)].id.astype(str))
# R3
prop = lambda s: ' '.join(w.capitalize() for w in str(s).strip().split(' '))
ev('R3', g('nombre de técnico con formato inconsistente'), t[t.tecnico_asignado.astype(str) != t.tecnico_asignado.map(prop)].id.astype(str))
t['tecnico_asignado'] = t.tecnico_asignado.map(prop)
# R4 matriz urgencia x impacto
def pri(u, i):
    p = int(np.ceil((u + i) / 2)); p = 6 if (u == 5 and i == 5) else p; return max(1, min(6, p))
t['prioridad_recalculada'] = t.prioridad.isna() | (t.prioridad == 0)
t.loc[t.prioridad_recalculada, 'prioridad'] = [pri(u, i) for u, i in zip(t.loc[t.prioridad_recalculada, 'urgencia'], t.loc[t.prioridad_recalculada, 'impacto'])]
ev('R4', g('prioridad vacía (0)'), t[t.prioridad_recalculada].id.astype(str))
# R5, R6
for c in ['fecha_apertura', 'fecha_resolucion', 'fecha_cierre', 'tiempo_para_resolver']: t[c] = pd.to_datetime(t[c])
t['resolucion_incompleta'] = t.estado.isin([5, 6]) & t.fecha_resolucion.isna()
ev('R5', g('estado resuelto/cerrado sin fecha de resolución'), t[t.resolucion_incompleta].id.astype(str))
t['cierre_invalido'] = t.fecha_cierre < t.fecha_apertura
ev('R6', g('fecha de cierre anterior a la apertura'), t[t.cierre_invalido].id.astype(str))
# R7
ev('R7', g('hallazgo duplicado'), v[v.duplicated('hallazgo_id')].hallazgo_id); v = v.drop_duplicates('hallazgo_id').copy()
# R8, R9
v['cvss_valido'] = v.cvss.notna() & (v.cvss >= 0) & (v.cvss <= 10)
ev('R8', g('CVSS fuera de rango (0-10)'), v[~v.cvss_valido].hallazgo_id)
def sev(c):
    return 'Crítica' if c >= 9 else 'Alta' if c >= 7 else 'Media' if c >= 4 else 'Baja' if c > 0 else 'Informativa'
v['sev_calc'] = [sev(c) if ok else None for c, ok in zip(v.cvss, v.cvss_valido)]
v['severidad_corregida'] = v.cvss_valido & (v.sev_calc != v.severidad)
v['severidad_final'] = np.where(v.severidad_corregida, v.sev_calc, v.severidad)
ev('R9', g('severidad incoherente con el CVSS'), v[v.severidad_corregida].hallazgo_id)
det = pd.DataFrame(out); print(det.to_string(index=False))
# conservación
print('filas tickets', len(t), 'hallazgos', len(v))
# restitución
cl = pd.read_excel(R + 'tickets_limpios.xlsx'); vl = pd.read_excel(R + 'vulnerabilidades_limpias.xlsx')
m = t.merge(cl[['id', 'prioridad']], on='id', suffixes=('', '_o')); x = m[m.prioridad_recalculada]
print('R4 restituye:', (x.prioridad == x.prioridad_o).sum(), '/', len(x))
mv = v.merge(vl[['hallazgo_id', 'severidad']], on='hallazgo_id', suffixes=('', '_o'))
print('Severidad final = original:', (mv.severidad_final == mv.severidad_o).sum(), '/', len(mv))
# indicadores (tablero) vs referencia
def ind(t, v, sevcol):
    rs = t[t.fecha_resolucion.notna()]
    h = (rs.fecha_resolucion - rs.fecha_apertura).dt.total_seconds() / 3600
    vv = v.copy(); vv['d'] = (pd.to_datetime(vv.fecha_remediacion) - pd.to_datetime(vv.fecha_deteccion)).dt.total_seconds() / 86400
    return {'I01 Tickets': len(t), 'I02 Incidentes': int((t.tipo == 1).sum()), 'I03 Solicitudes': int((t.tipo == 2).sum()),
            'I04 Abiertos': int(t.estado.isin([1, 2, 3, 4]).sum()), 'I05 Inc. prioridad alta o más': int(((t.tipo == 1) & (t.prioridad >= 4)).sum()),
            'I06 MTTR (h)': round(h.mean(), 2), 'I07 SLA (%)': round(100 * (rs.fecha_resolucion <= rs.tiempo_para_resolver).mean(), 2),
            'I08 Hallazgos': len(v), 'I09 Abiertas': int((v.estado == 'Abierta').sum()),
            'I10 Críticas abiertas': int(((v.estado == 'Abierta') & (v[sevcol] == 'Crítica')).sum()), 'I11 Días remediación': round(vv.d.mean(), 2)}
for c in ['fecha_apertura', 'fecha_resolucion', 'tiempo_para_resolver']: cl[c] = pd.to_datetime(cl[c])
a = ind(t, v, 'severidad_final'); b = ind(cl, vl, 'severidad')
q = {'Q12': int(t.resolucion_incompleta.sum()), 'Q13': int(t.cierre_invalido.sum()), 'Q14': int(t.prioridad_recalculada.sum()), 'Q15': int((~v.cvss_valido).sum()), 'Q16': int(v.severidad_corregida.sum())}
res = pd.DataFrame({'tablero_esperado': a, 'referencia': b}); res['diferencia'] = (res.tablero_esperado - res.referencia).round(2)
print(res.to_string()); print(q)
# meses SLA < 85
rs = t[t.fecha_resolucion.notna()].copy(); rs['m'] = rs.fecha_apertura.dt.to_period('M')
s = rs.groupby('m').apply(lambda d: round(100 * (d.fecha_resolucion <= d.tiempo_para_resolver).mean(), 1)); print('SLA mensual', s.to_dict())
os.makedirs(sys.argv[2], exist_ok=True)
det.to_csv(os.path.join(sys.argv[2], 'deteccion.csv'), index=False); res.to_csv(os.path.join(sys.argv[2], 'indicadores.csv')); pd.Series(q, name='valor').to_csv(os.path.join(sys.argv[2], 'indicadores_calidad.csv'))
