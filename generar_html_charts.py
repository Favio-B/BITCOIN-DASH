import csv, json, os, statistics
from collections import defaultdict

CSV_PATH = "bitcoin_clean.csv"
OUT_DIR = "html"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Leer CSV ──────────────────────────────────────────────────────────────────
rows = []
with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows.append(r)

def flt(v):
    try: return float(v)
    except: return None

fechas      = [r["fecha"] for r in rows]
closes      = [flt(r["priceClose"]) for r in rows]
highs       = [flt(r["priceHigh"]) for r in rows]
lows        = [flt(r["priceLow"]) for r in rows]
opens_      = [flt(r["priceOpen"]) for r in rows]
vols        = [flt(r["volume"]) for r in rows]
rend        = [flt(r["rendimiento_diario"]) for r in rows]
volatilidad = [flt(r["volatilidad_diaria"]) for r in rows]
ma7         = [flt(r["media_movil_7d"]) for r in rows]
ma30        = [flt(r["media_movil_30d"]) for r in rows]
AÑO_COL = "a\xf1o"
años    = [r[AÑO_COL] for r in rows]
meses       = [int(r["mes"]) for r in rows]
direccion   = [int(r["direccion"]) for r in rows]

# ── KPIs ──────────────────────────────────────────────────────────────────────
precio_actual = closes[-1]
precio_max    = max(highs)
precio_min    = min(lows)
rend_prom     = statistics.mean([x for x in rend if x is not None])
vol_prom      = statistics.mean([x for x in volatilidad if x is not None])
vol_total     = sum([x for x in vols if x is not None])
dias_alc      = sum(1 for d in direccion if d == 1)
dias_baj      = sum(1 for d in direccion if d == 0)
pct_alc       = dias_alc / len(direccion) * 100

# ── Heatmap: rendimiento mensual promedio por año ─────────────────────────────
heat = defaultdict(lambda: defaultdict(list))
for r in rows:
    heat[r[AÑO_COL]][int(r["mes"])].append(flt(r["rendimiento_diario"]) or 0)

años_unicos = sorted(set(años))
meses_nombres = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

heat_matrix = []
for a in años_unicos:
    row_data = []
    for m in range(1, 13):
        vals = heat[a][m]
        row_data.append(round(statistics.mean(vals), 4) if vals else None)
    heat_matrix.append(row_data)

# ── Volumen mensual (compacto) ─────────────────────────────────────────────────
vol_mensual = defaultdict(float)
for r in rows:
    key = r["fecha"][:7]
    vol_mensual[key] += flt(r["volume"]) or 0

vol_keys   = sorted(vol_mensual.keys())
vol_values = [round(vol_mensual[k]/1e9, 2) for k in vol_keys]

# ── Scatter: rendimiento vs volatilidad (muestra 1 de cada 3) ─────────────────
scatter_x, scatter_y, scatter_c = [], [], []
for i in range(0, len(rows), 3):
    x = flt(rows[i]["volatilidad_diaria"])
    y = flt(rows[i]["rendimiento_diario"])
    if x is not None and y is not None:
        scatter_x.append(round(x, 3))
        scatter_y.append(round(y, 3))
        scatter_c.append(int(rows[i]["direccion"]))

# ── Rendimiento por año ────────────────────────────────────────────────────────
rend_año = defaultdict(list)
for r in rows:
    v = flt(r["rendimiento_diario"])
    if v is not None:
        rend_año[r[AÑO_COL]].append(v)

rend_año_prom = {a: round(statistics.mean(v), 4) for a, v in rend_año.items()}

# ── Histograma rendimiento ────────────────────────────────────────────────────
rend_vals = [x for x in rend if x is not None]
hist_min, hist_max = -20, 20
bins = list(range(hist_min, hist_max+1, 2))
hist_counts = [0]*len(bins)
for v in rend_vals:
    for i, b in enumerate(bins):
        if b <= v < b+2:
            hist_counts[i] += 1
            break

# ── Precio mensual (promedio close) ───────────────────────────────────────────
precio_mens = defaultdict(list)
for r in rows:
    key = r["fecha"][:7]
    v = flt(r["priceClose"])
    if v: precio_mens[key].append(v)

pm_keys   = sorted(precio_mens.keys())
pm_values = [round(statistics.mean(precio_mens[k]), 2) for k in pm_keys]
ma7_mens  = [round(statistics.mean([flt(rows[i]["media_movil_7d"]) for i in range(len(rows)) if rows[i]["fecha"][:7]==k and flt(rows[i]["media_movil_7d"])]), 2) for k in pm_keys]
ma30_mens = [round(statistics.mean([flt(rows[i]["media_movil_30d"]) for i in range(len(rows)) if rows[i]["fecha"][:7]==k and flt(rows[i]["media_movil_30d"])]), 2) for k in pm_keys]

CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"

# ══════════════════════════════════════════════════════════════════════════════
# 1. PRECIO HISTÓRICO + MEDIAS MÓVILES
# ══════════════════════════════════════════════════════════════════════════════
html1 = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Bitcoin – Precio Histórico</title>
<script src="{CDN}"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',sans-serif;padding:16px}}
h2{{color:#f7931a;font-size:1.1rem;margin-bottom:12px}}canvas{{background:#161b22;border-radius:8px}}</style></head>
<body>
<h2>&#8383; Bitcoin — Precio de Cierre &amp; Medias Móviles (mensual)</h2>
<canvas id="c" height="90"></canvas>
<script>
const labels={json.dumps(pm_keys)};
const close={json.dumps(pm_values)};
const ma7={json.dumps(ma7_mens)};
const ma30={json.dumps(ma30_mens)};
new Chart(document.getElementById('c'),{{
  type:'line',
  data:{{labels,datasets:[
    {{label:'Precio Cierre',data:close,borderColor:'#f7931a',borderWidth:2,pointRadius:0,fill:false,tension:0.3}},
    {{label:'MA 7d',data:ma7,borderColor:'#58a6ff',borderWidth:1.5,pointRadius:0,fill:false,tension:0.3,borderDash:[4,2]}},
    {{label:'MA 30d',data:ma30,borderColor:'#3fb950',borderWidth:1.5,pointRadius:0,fill:false,tension:0.3,borderDash:[8,4]}}
  ]}},
  options:{{responsive:true,interaction:{{mode:'index',intersect:false}},
    plugins:{{legend:{{labels:{{color:'#e6edf3'}}}},tooltip:{{callbacks:{{label:ctx=>'$'+ctx.parsed.y.toLocaleString()}}}}}},
    scales:{{x:{{ticks:{{color:'#8b949e',maxTicksLimit:24}},grid:{{color:'#21262d'}}}},
             y:{{ticks:{{color:'#8b949e',callback:v=>'$'+v.toLocaleString()}},grid:{{color:'#21262d'}}}}}}
  }}
}});
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
# 2. DISTRIBUCIÓN DE RENDIMIENTOS
# ══════════════════════════════════════════════════════════════════════════════
hist_labels = [f"{b}% a {b+2}%" for b in bins]
hist_colors = ['"#3fb950"' if b>=0 else '"#f85149"' for b in bins]

html2 = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Bitcoin – Distribución Rendimientos</title>
<script src="{CDN}"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',sans-serif;padding:16px}}
h2{{color:#f7931a;font-size:1.1rem;margin-bottom:12px}}canvas{{background:#161b22;border-radius:8px}}</style></head>
<body>
<h2>&#8383; Bitcoin — Distribución de Rendimientos Diarios</h2>
<canvas id="c" height="90"></canvas>
<script>
const labels={json.dumps(hist_labels)};
const counts={json.dumps(hist_counts)};
const colors=[{",".join(hist_colors)}];
new Chart(document.getElementById('c'),{{
  type:'bar',
  data:{{labels,datasets:[{{label:'Frecuencia',data:counts,backgroundColor:colors,borderWidth:0}}]}},
  options:{{responsive:true,
    plugins:{{legend:{{labels:{{color:'#e6edf3'}}}}}},
    scales:{{x:{{ticks:{{color:'#8b949e',maxRotation:45}},grid:{{color:'#21262d'}}}},
             y:{{ticks:{{color:'#8b949e'}},grid:{{color:'#21262d'}}}}}}
  }}
}});
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
# 3. VOLATILIDAD EN EL TIEMPO
# ══════════════════════════════════════════════════════════════════════════════
vol_mens2 = defaultdict(list)
for r in rows:
    v = flt(r["volatilidad_diaria"])
    if v: vol_mens2[r["fecha"][:7]].append(v)
vm_keys = sorted(vol_mens2.keys())
vm_vals = [round(statistics.mean(vol_mens2[k]), 3) for k in vm_keys]

html3 = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Bitcoin – Volatilidad</title>
<script src="{CDN}"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',sans-serif;padding:16px}}
h2{{color:#f7931a;font-size:1.1rem;margin-bottom:12px}}canvas{{background:#161b22;border-radius:8px}}</style></head>
<body>
<h2>&#8383; Bitcoin — Volatilidad Diaria Promedio Mensual (%)</h2>
<canvas id="c" height="90"></canvas>
<script>
const labels={json.dumps(vm_keys)};
const data={json.dumps(vm_vals)};
new Chart(document.getElementById('c'),{{
  type:'line',
  data:{{labels,datasets:[{{label:'Volatilidad %',data,borderColor:'#d29922',backgroundColor:'rgba(210,153,34,0.15)',
    borderWidth:2,pointRadius:0,fill:true,tension:0.4}}]}},
  options:{{responsive:true,interaction:{{mode:'index',intersect:false}},
    plugins:{{legend:{{labels:{{color:'#e6edf3'}}}}}},
    scales:{{x:{{ticks:{{color:'#8b949e',maxTicksLimit:24}},grid:{{color:'#21262d'}}}},
             y:{{ticks:{{color:'#8b949e',callback:v=>v+'%'}},grid:{{color:'#21262d'}}}}}}
  }}
}});
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
# 4. VOLUMEN MENSUAL
# ══════════════════════════════════════════════════════════════════════════════
html4 = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Bitcoin – Volumen</title>
<script src="{CDN}"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',sans-serif;padding:16px}}
h2{{color:#f7931a;font-size:1.1rem;margin-bottom:12px}}canvas{{background:#161b22;border-radius:8px}}</style></head>
<body>
<h2>&#8383; Bitcoin — Volumen Mensual Total (Miles de Millones USD)</h2>
<canvas id="c" height="90"></canvas>
<script>
const labels={json.dumps(vol_keys)};
const data={json.dumps(vol_values)};
new Chart(document.getElementById('c'),{{
  type:'bar',
  data:{{labels,datasets:[{{label:'Volumen (B$)',data,backgroundColor:'rgba(88,166,255,0.7)',borderColor:'#58a6ff',borderWidth:1}}]}},
  options:{{responsive:true,interaction:{{mode:'index',intersect:false}},
    plugins:{{legend:{{labels:{{color:'#e6edf3'}}}}}},
    scales:{{x:{{ticks:{{color:'#8b949e',maxTicksLimit:30}},grid:{{color:'#21262d'}}}},
             y:{{ticks:{{color:'#8b949e',callback:v=>v+'B'}},grid:{{color:'#21262d'}}}}}}
  }}
}});
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
# 5. HEATMAP RENDIMIENTO MENSUAL (sin Chart.js – puro HTML/CSS)
# ══════════════════════════════════════════════════════════════════════════════
def heat_color(v):
    if v is None: return "#21262d", "#8b949e"
    if v > 3:  return "#0d4429", "#3fb950"
    if v > 1:  return "#1b4721", "#56d364"
    if v > 0:  return "#1f3d1a", "#7ee787"
    if v > -1: return "#3d1a1a", "#f85149"
    if v > -3: return "#4d1010", "#da3633"
    return "#5c0000", "#ff7b7b"

cells = ""
for i, a in enumerate(años_unicos):
    cells += f"<tr><td style='padding:4px 8px;color:#8b949e;font-weight:600'>{a}</td>"
    for j, val in enumerate(heat_matrix[i]):
        bg, fg = heat_color(val)
        txt = f"{val:+.1f}%" if val is not None else "–"
        cells += f"<td style='background:{bg};color:{fg};padding:4px 6px;text-align:center;border-radius:4px;font-size:0.75rem'>{txt}</td>"
    cells += "</tr>"

meses_th = "".join(f"<th style='padding:4px 6px;color:#8b949e;font-size:0.75rem'>{m}</th>" for m in meses_nombres)

html5 = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Bitcoin – Heatmap Rendimientos</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',sans-serif;padding:16px}}
h2{{color:#f7931a;font-size:1.1rem;margin-bottom:12px}}
table{{border-collapse:separate;border-spacing:3px;width:100%}}
</style></head><body>
<h2>&#8383; Bitcoin — Heatmap Rendimiento Promedio Mensual (%)</h2>
<table>
<thead><tr><th></th>{meses_th}</tr></thead>
<tbody>{cells}</tbody>
</table>
</body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
# 6. SCATTER RENDIMIENTO vs VOLATILIDAD
# ══════════════════════════════════════════════════════════════════════════════
scatter_colors = ['"rgba(63,185,80,0.6)"' if c==1 else '"rgba(248,81,73,0.6)"' for c in scatter_c]

html6 = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Bitcoin – Rendimiento vs Volatilidad</title>
<script src="{CDN}"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',sans-serif;padding:16px}}
h2{{color:#f7931a;font-size:1.1rem;margin-bottom:12px}}canvas{{background:#161b22;border-radius:8px}}</style></head>
<body>
<h2>&#8383; Bitcoin — Rendimiento vs Volatilidad Diaria (verde=alcista, rojo=bajista)</h2>
<canvas id="c" height="90"></canvas>
<script>
const sx={json.dumps(scatter_x)};
const sy={json.dumps(scatter_y)};
const sc=[{",".join(scatter_colors)}];
const pts=sx.map((x,i)=>({{x,y:sy[i]}}));
new Chart(document.getElementById('c'),{{
  type:'scatter',
  data:{{datasets:[{{label:'Días',data:pts,backgroundColor:sc,pointRadius:3,pointHoverRadius:5}}]}},
  options:{{responsive:true,
    plugins:{{legend:{{labels:{{color:'#e6edf3'}}}},tooltip:{{callbacks:{{label:ctx=>`Vol: ${{ctx.parsed.x}}% | Rend: ${{ctx.parsed.y}}%`}}}}}},
    scales:{{x:{{title:{{display:true,text:'Volatilidad (%)',color:'#8b949e'}},ticks:{{color:'#8b949e'}},grid:{{color:'#21262d'}}}},
             y:{{title:{{display:true,text:'Rendimiento (%)',color:'#8b949e'}},ticks:{{color:'#8b949e',callback:v=>v+'%'}},grid:{{color:'#21262d'}}}}}}
  }}
}});
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
# 7. RENDIMIENTO PROMEDIO POR AÑO
# ══════════════════════════════════════════════════════════════════════════════
ra_keys = sorted(rend_año_prom.keys())
ra_vals = [rend_año_prom[k] for k in ra_keys]
ra_colors = ['"#3fb950"' if v>=0 else '"#f85149"' for v in ra_vals]

html7 = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Bitcoin – Rendimiento por Año</title>
<script src="{CDN}"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',sans-serif;padding:16px}}
h2{{color:#f7931a;font-size:1.1rem;margin-bottom:12px}}canvas{{background:#161b22;border-radius:8px}}</style></head>
<body>
<h2>&#8383; Bitcoin — Rendimiento Diario Promedio por Año (%)</h2>
<canvas id="c" height="90"></canvas>
<script>
const labels={json.dumps(ra_keys)};
const data={json.dumps(ra_vals)};
const colors=[{",".join(ra_colors)}];
new Chart(document.getElementById('c'),{{
  type:'bar',
  data:{{labels,datasets:[{{label:'Rendimiento Prom %',data,backgroundColor:colors,borderRadius:6,borderWidth:0}}]}},
  options:{{responsive:true,
    plugins:{{legend:{{labels:{{color:'#e6edf3'}}}}}},
    scales:{{x:{{ticks:{{color:'#8b949e'}},grid:{{color:'#21262d'}}}},
             y:{{ticks:{{color:'#8b949e',callback:v=>v+'%'}},grid:{{color:'#21262d'}}}}}}
  }}
}});
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
# 8. DASHBOARD KPIs (puro HTML)
# ══════════════════════════════════════════════════════════════════════════════
retorno_acum = (closes[-1] - closes[0]) / closes[0] * 100

kpis = [
    ("Precio Actual",      f"${precio_actual:,.2f}",  "#f7931a"),
    ("Precio Máximo",      f"${precio_max:,.2f}",     "#3fb950"),
    ("Precio Mínimo",      f"${precio_min:,.2f}",     "#f85149"),
    ("Rendimiento Prom",   f"{rend_prom:+.3f}%",      "#58a6ff"),
    ("Volatilidad Prom",   f"{vol_prom:.3f}%",        "#d29922"),
    ("% Días Alcistas",    f"{pct_alc:.1f}%",         "#3fb950"),
    ("% Días Bajistas",    f"{100-pct_alc:.1f}%",     "#f85149"),
    ("Retorno Acumulado",  f"{retorno_acum:+,.1f}%",  "#a371f7"),
    ("Total de Días",      f"{len(rows):,}",           "#8b949e"),
    ("Rango de Fechas",    f"{fechas[0]} → {fechas[-1]}", "#8b949e"),
]

kpi_cards = ""
for title, value, color in kpis:
    kpi_cards += f"""<div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px 20px;min-width:160px;flex:1">
    <div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;letter-spacing:.05em">{title}</div>
    <div style="color:{color};font-size:1.4rem;font-weight:700;margin-top:4px">{value}</div>
    </div>"""

html8 = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Bitcoin – Dashboard KPIs</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',sans-serif;padding:20px}}
h2{{color:#f7931a;font-size:1.2rem;margin-bottom:16px;border-bottom:1px solid #30363d;padding-bottom:8px}}
.grid{{display:flex;flex-wrap:wrap;gap:12px}}
footer{{margin-top:20px;color:#484f58;font-size:0.72rem;text-align:right}}
</style></head><body>
<h2>&#8383; Bitcoin Dashboard — Resumen General</h2>
<div class="grid">{kpi_cards}</div>
<footer>Datos: {fechas[0]} al {fechas[-1]} · {len(rows)} registros · Generado con Power BI MCP</footer>
</body></html>"""

# ── Escribir archivos ─────────────────────────────────────────────────────────
files = {
    "01_precio_historico.html":         html1,
    "02_distribucion_rendimiento.html": html2,
    "03_volatilidad_tiempo.html":       html3,
    "04_volumen_mensual.html":          html4,
    "05_heatmap_rendimiento.html":      html5,
    "06_scatter_rend_vs_vol.html":      html6,
    "07_rendimiento_por_año.html":      html7,
    "08_dashboard_kpis.html":           html8,
}

for fname, content in files.items():
    path = os.path.join(OUT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK: {path}")

print(f"\nLISTO: {len(files)} archivos HTML generados en ./{OUT_DIR}/")
