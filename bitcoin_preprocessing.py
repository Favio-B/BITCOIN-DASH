# -*- coding: utf-8 -*-
"""
Preprocesamiento de datos historicos de Bitcoin (2018-2026)
Metodologia CRISP-DM - Fase de Preparacion de Datos

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configuración visual global
plt.rcParams['figure.dpi'] = 120
plt.rcParams['font.size'] = 10
sns.set_theme(style="darkgrid")

# ==============================================================================
# 1. CARGA DEL DATASET
# ==============================================================================
print("=" * 60)

print("CARGA DEL DATASET")
print("=" * 60)

df = pd.read_excel("bitcoin.xlsx")

print(f"Registros cargados : {len(df)}")
print(f"Columnas           : {list(df.columns)}")
print(f"\nPrimeras filas:")
print(df.head(3))
print(f"\nTipos de datos:\n{df.dtypes}")

# ==============================================================================
# 2. CONVERSIÓN DE FECHAS (timestamps Unix en milisegundos → fechas legibles)
# ==============================================================================
print("\n" + "=" * 60)
print("CONVERSIÓN DE FECHAS")
print("=" * 60)

# Los timestamps están en milisegundos, dividimos entre 1000 para convertir a segundos
for col in ['timeOpen', 'timeClose', 'timeHigh', 'timeLow']:
    df[col] = pd.to_datetime(df[col], unit='ms')

# La fecha principal del registro es timeOpen (apertura del día)
df['fecha'] = df['timeOpen'].dt.date
df['fecha'] = pd.to_datetime(df['fecha'])

# Extracción de componentes temporales para análisis y Power BI
df['año']          = df['timeOpen'].dt.year
df['mes']          = df['timeOpen'].dt.month
df['dia']          = df['timeOpen'].dt.day
df['dia_semana']   = df['timeOpen'].dt.dayofweek          # 0=Lunes, 6=Domingo
df['nombre_dia']   = df['timeOpen'].dt.day_name()
df['nombre_mes']   = df['timeOpen'].dt.month_name()
df['trimestre']    = df['timeOpen'].dt.quarter
df['semana_año']   = df['timeOpen'].dt.isocalendar().week.astype(int)

# Ordenar por fecha ascendente (cronológico)
df = df.sort_values('fecha').reset_index(drop=True)

print(f"Rango temporal: {df['fecha'].min().date()} a {df['fecha'].max().date()}")
print(f"Total días    : {len(df)}")

# ==============================================================================
# 3. INGENIERÍA DE FEATURES
# ==============================================================================
print("\n" + "=" * 60)
print("INGENIERÍA DE FEATURES")
print("=" * 60)

# Rendimiento diario (%): mide cuánto subió o bajó el precio en el día
df['rendimiento_diario'] = (df['priceClose'] - df['priceOpen']) / df['priceOpen'] * 100

# Volatilidad diaria (%): amplitud del rango de precios relativa al precio de apertura
df['volatilidad_diaria'] = (df['priceHigh'] - df['priceLow']) / df['priceOpen'] * 100

# Rango del cuerpo (USD): diferencia absoluta entre cierre y apertura
df['rango_cuerpo'] = abs(df['priceClose'] - df['priceOpen'])

# Dirección: 1 = día alcista, 0 = día bajista (variable objetivo para clasificación)
df['direccion'] = (df['priceClose'] > df['priceOpen']).astype(int)

# Medias móviles del precio de cierre (útil para identificar tendencias)
df['media_movil_7d']  = df['priceClose'].rolling(window=7,  min_periods=1).mean()
df['media_movil_30d'] = df['priceClose'].rolling(window=30, min_periods=1).mean()

# Rendimiento respecto al día anterior (para análisis de series temporales)
df['rendimiento_vs_anterior'] = df['priceClose'].pct_change() * 100

print("Features creados:")
features_nuevos = ['rendimiento_diario','volatilidad_diaria','rango_cuerpo',
                   'direccion','media_movil_7d','media_movil_30d','rendimiento_vs_anterior']
for f in features_nuevos:
    print(f"  OK:{f}")

# ==============================================================================
# 4. LIMPIEZA Y VALIDACIÓN
# ==============================================================================
print("\n" + "=" * 60)
print("LIMPIEZA Y VALIDACIÓN")
print("=" * 60)

# --- Valores nulos ---
nulos = df.isnull().sum()
nulos_total = nulos[nulos > 0]
if len(nulos_total) == 0:
    print("Sin valores nulos detectados.")
else:
    print(f"Valores nulos encontrados:\n{nulos_total}")

# --- Duplicados ---
duplicados = df.duplicated(subset='fecha').sum()
print(f"Fechas duplicadas: {duplicados}")
if duplicados > 0:
    df = df.drop_duplicates(subset='fecha')
    print(f"  → Eliminados. Registros restantes: {len(df)}")

# --- Outliers con IQR en precio de cierre ---
print("\n[IQR] Outliers en priceClose:")
Q1 = df['priceClose'].quantile(0.25)
Q3 = df['priceClose'].quantile(0.75)
IQR = Q3 - Q1
outliers_iqr = df[(df['priceClose'] < Q1 - 1.5 * IQR) | (df['priceClose'] > Q3 + 1.5 * IQR)]
print(f"  Detectados: {len(outliers_iqr)} registros (precio extremo)")

# --- Outliers con Z-score en rendimiento diario ---
print("\n[Z-score] Outliers en rendimiento_diario (|z| > 3):")
df['z_rendimiento'] = np.abs(stats.zscore(df['rendimiento_diario'].dropna()))
outliers_z = df[df['z_rendimiento'] > 3]
print(f"  Detectados: {len(outliers_z)} días con rendimiento extremo")

# --- Outliers con Z-score en volumen ---
print("\n[Z-score] Outliers en volume (|z| > 3):")
df['z_volume'] = np.abs(stats.zscore(df['volume']))
outliers_vol = df[df['z_volume'] > 3]
print(f"  Detectados: {len(outliers_vol)} días con volumen extremo")

# --- Top 10 días más extremos ---
print("\n[TOP 10] Días con mayor rendimiento (RALLIES):")
top_rallies = df.nlargest(10, 'rendimiento_diario')[
    ['fecha', 'priceOpen', 'priceClose', 'rendimiento_diario', 'volume']
]
print(top_rallies.to_string(index=False))

print("\n[TOP 10] Días con menor rendimiento (CRASHES):")
top_crashes = df.nsmallest(10, 'rendimiento_diario')[
    ['fecha', 'priceOpen', 'priceClose', 'rendimiento_diario', 'volume']
]
print(top_crashes.to_string(index=False))

# ==============================================================================
# 5. ESTADÍSTICAS DESCRIPTIVAS
# ==============================================================================
print("\n" + "=" * 60)
print("ESTADÍSTICAS DESCRIPTIVAS")
print("=" * 60)

cols_numericas = ['priceOpen', 'priceHigh', 'priceLow', 'priceClose',
                  'volume', 'rendimiento_diario', 'volatilidad_diaria', 'rango_cuerpo']

print(df[cols_numericas].describe().round(2).to_string())

# Porcentaje de días alcistas vs bajistas
pct_alcistas = df['direccion'].mean() * 100
print(f"\nDías alcistas : {pct_alcistas:.1f}%")
print(f"Días bajistas : {100 - pct_alcistas:.1f}%")

# ==============================================================================
# 6. VISUALIZACIONES
# ==============================================================================
print("\n" + "=" * 60)
print("GENERANDO VISUALIZACIONES...")
print("=" * 60)

# --- 6.1 Heatmap de correlaciones ---
fig, ax = plt.subplots(figsize=(11, 8))
corr = df[cols_numericas].corr()
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap='coolwarm',
            center=0, linewidths=0.5, ax=ax, annot_kws={"size": 9})
ax.set_title("Correlación entre variables numéricas - Bitcoin (2018-2026)", fontsize=13, pad=12)
plt.tight_layout()
plt.savefig("correlacion_heatmap.png", bbox_inches='tight')
plt.show()
print("  OK:correlacion_heatmap.png")

# --- 6.2 Serie de tiempo del precio de cierre con medias móviles ---
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(df['fecha'], df['priceClose'],     color='steelblue',  lw=0.8, alpha=0.7, label='Precio Cierre')
ax.plot(df['fecha'], df['media_movil_7d'], color='orange',     lw=1.2, alpha=0.9, label='MA 7 días')
ax.plot(df['fecha'], df['media_movil_30d'],color='crimson',    lw=1.5, alpha=0.9, label='MA 30 días')
ax.set_title("Precio de Cierre Bitcoin 2018–2026", fontsize=13)
ax.set_xlabel("Fecha")
ax.set_ylabel("Precio (USD)")
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.legend()
plt.tight_layout()
plt.savefig("serie_tiempo_precio.png", bbox_inches='tight')
plt.show()
print("  OK:serie_tiempo_precio.png")

# --- 6.3 Distribución del rendimiento diario ---
fig, ax = plt.subplots(figsize=(10, 5))
rendimientos = df['rendimiento_diario'].dropna()
sns.histplot(rendimientos, bins=80, kde=True, color='steelblue', ax=ax,
             stat='density', alpha=0.6)
# Curva normal teórica superpuesta
mu, sigma = rendimientos.mean(), rendimientos.std()
x = np.linspace(rendimientos.min(), rendimientos.max(), 300)
ax.plot(x, stats.norm.pdf(x, mu, sigma), 'r--', lw=2, label=f'Normal (μ={mu:.2f}%, σ={sigma:.2f}%)')
ax.axvline(0, color='gray', linestyle=':', lw=1.5)
ax.set_title("Distribución del Rendimiento Diario - Bitcoin", fontsize=13)
ax.set_xlabel("Rendimiento diario (%)")
ax.set_ylabel("Densidad")
ax.legend()
plt.tight_layout()
plt.savefig("distribucion_rendimiento.png", bbox_inches='tight')
plt.show()
print("  OK:distribucion_rendimiento.png")

# --- 6.4 Boxplot de rendimientos por año ---
fig, ax = plt.subplots(figsize=(12, 5))
df_box = df.dropna(subset=['rendimiento_diario'])
sns.boxplot(data=df_box, x='año', y='rendimiento_diario', palette='Set2',
            flierprops=dict(marker='o', markersize=2), ax=ax)
ax.axhline(0, color='red', linestyle='--', lw=1.2)
ax.set_title("Distribución de Rendimientos Diarios por Año", fontsize=13)
ax.set_xlabel("Año")
ax.set_ylabel("Rendimiento diario (%)")
plt.tight_layout()
plt.savefig("boxplot_rendimiento_anual.png", bbox_inches='tight')
plt.show()
print("  OK:boxplot_rendimiento_anual.png")

# --- 6.5 Scatter: Volumen vs Volatilidad ---
fig, ax = plt.subplots(figsize=(9, 5))
sc = ax.scatter(df['volume'] / 1e9, df['volatilidad_diaria'],
                c=df['rendimiento_diario'], cmap='RdYlGn',
                alpha=0.4, s=10, vmin=-15, vmax=15)
plt.colorbar(sc, ax=ax, label='Rendimiento diario (%)')
ax.set_title("Volumen vs Volatilidad Diaria", fontsize=13)
ax.set_xlabel("Volumen (miles de millones USD)")
ax.set_ylabel("Volatilidad diaria (%)")
plt.tight_layout()
plt.savefig("scatter_volumen_volatilidad.png", bbox_inches='tight')
plt.show()
print("  OK:scatter_volumen_volatilidad.png")

# ==============================================================================
# 7. EXPORTAR DATASET LIMPIO PARA POWER BI
# ==============================================================================
print("\n" + "=" * 60)
print("EXPORTANDO bitcoin_clean.csv")
print("=" * 60)

# Columnas finales ordenadas de forma lógica para Power BI
columnas_finales = [
    # Temporal
    'fecha', 'año', 'trimestre', 'mes', 'nombre_mes', 'dia',
    'dia_semana', 'nombre_dia', 'semana_año',
    # Precios OHLC
    'priceOpen', 'priceHigh', 'priceLow', 'priceClose',
    # Volumen
    'volume',
    # Features calculados
    'rendimiento_diario', 'volatilidad_diaria', 'rango_cuerpo',
    'direccion', 'media_movil_7d', 'media_movil_30d', 'rendimiento_vs_anterior',
]

df_clean = df[columnas_finales].copy()

# Redondear columnas numéricas para legibilidad
round_cols = ['priceOpen','priceHigh','priceLow','priceClose',
              'rendimiento_diario','volatilidad_diaria','rango_cuerpo',
              'media_movil_7d','media_movil_30d','rendimiento_vs_anterior']
df_clean[round_cols] = df_clean[round_cols].round(4)

df_clean.to_csv("bitcoin_clean.csv", index=False, encoding='utf-8-sig')

print(f"Archivo guardado: bitcoin_clean.csv")
print(f"Registros       : {len(df_clean)}")
print(f"Columnas        : {len(df_clean.columns)}")
print(f"\nColumnas exportadas:\n{list(df_clean.columns)}")
print("\n¡Preprocesamiento completado exitosamente!")
#PROCESO FINALIZADO