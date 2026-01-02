# app_monetizada_completa.py
# App Agrícola con Monetización - FREE / BÁSICO / PREMIUM
# Compatible con Linux y Google Earth Engine

import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import io
from shapely.geometry import Polygon, LineString
import math
import warnings
import xml.etree.ElementTree as ET
import base64
import json
from io import BytesIO
from fpdf import FPDF
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import geojson
import requests
import contextily as ctx

# === MERCADO PAGO ===
try:
    import mercadopago
    MERCADO_PAGO_AVAILABLE = True
except ImportError:
    MERCADO_PAGO_AVAILABLE = False

warnings.filterwarnings('ignore')

# === CONFIGURACIÓN DE PLANES ===
PLANES = {
    'FREE': {
        'nombre': 'Gratuito',
        'precio': 0,
        'caracteristicas': [
            '✅ 3 análisis por mes',
            '✅ Cultivos básicos (Maíz, Soya)',
            '✅ Sentinel-2 (resolución limitada)',
            '✅ Exportación CSV',
            '❌ Sin datos NASA POWER',
            '❌ Sin curvas de nivel',
            '❌ Sin exportación PDF/DOCX',
            '❌ Sin análisis de textura',
            '❌ Soporte básico por email'
        ],
        'limite_analisis': 3,
        'cultivos_disponibles': ['MAÍZ', 'SOYA'],
        'satelites_disponibles': ['DATOS_SIMULADOS'],
        'exportaciones': ['CSV'],
        'nasa_power': False,
        'curvas_nivel': False,
        'analisis_textura': False
    },
    'BASICO': {
        'nombre': 'Básico',
        'precio': 29.99,
        'moneda': 'USD',
        'caracteristicas': [
            '✅ 20 análisis por mes',
            '✅ Todos los cultivos',
            '✅ Sentinel-2 + Landsat-8',
            '✅ Datos NASA POWER',
            '✅ Exportación CSV + PDF',
            '✅ Análisis de textura',
            '✅ Curvas de nivel básicas',
            '❌ Sin mapa base ESRI premium',
            '✅ Soporte prioritario'
        ],
        'limite_analisis': 20,
        'cultivos_disponibles': ['MAÍZ', 'SOYA', 'TRIGO', 'GIRASOL'],
        'satelites_disponibles': ['SENTINEL-2', 'LANDSAT-8', 'DATOS_SIMULADOS'],
        'exportaciones': ['CSV', 'PDF'],
        'nasa_power': True,
        'curvas_nivel': True,
        'analisis_textura': True,
        'intervalo_curvas_max': 10.0
    },
    'PREMIUM': {
        'nombre': 'Premium',
        'precio': 79.99,
        'moneda': 'USD',
        'caracteristicas': [
            '✅ Análisis ilimitados',
            '✅ Todos los cultivos + personalizados',
            '✅ Todos los satélites + datos históricos',
            '✅ Datos NASA POWER completos',
            '✅ Todas las exportaciones (CSV, PDF, DOCX, GeoJSON)',
            '✅ Curvas de nivel avanzadas',
            '✅ Mapa base ESRI premium',
            '✅ Análisis de textura detallado',
            '✅ Potencial de cosecha avanzado',
            '✅ Soporte 24/7 + asesoría agrícola'
        ],
        'limite_analisis': 99999,
        'cultivos_disponibles': ['MAÍZ', 'SOYA', 'TRIGO', 'GIRASOL'],
        'satelites_disponibles': ['SENTINEL-2', 'LANDSAT-8', 'DATOS_SIMULADOS'],
        'exportaciones': ['CSV', 'PDF', 'DOCX', 'GEOJSON'],
        'nasa_power': True,
        'curvas_nivel': True,
        'analisis_textura': True,
        'intervalo_curvas_max': 20.0,
        'esri_premium': True
    }
}

# === INICIALIZACIÓN DE SESIÓN ===
if 'plan_actual' not in st.session_state:
    st.session_state.plan_actual = 'FREE'
if 'analisis_realizados' not in st.session_state:
    st.session_state.analisis_realizados = 0
if 'usuario_id' not in st.session_state:
    st.session_state.usuario_id = f"user_{datetime.now().timestamp()}"
if 'fecha_reset' not in st.session_state:
    st.session_state.fecha_reset = datetime.now()

# === FUNCIONES DE MONETIZACIÓN ===
def verificar_limite_analisis():
    if (datetime.now() - st.session_state.fecha_reset).days >= 30:
        st.session_state.analisis_realizados = 0
        st.session_state.fecha_reset = datetime.now()
    plan = st.session_state.plan_actual
    limite = PLANES[plan]['limite_analisis']
    if st.session_state.analisis_realizados >= limite:
        return False, f"⚠️ Has alcanzado el límite de {limite} análisis mensuales de tu plan {PLANES[plan]['nombre']}."
    return True, ""

def registrar_analisis():
    st.session_state.analisis_realizados += 1

def verificar_funcionalidad(funcionalidad):
    plan = st.session_state.plan_actual
    if funcionalidad == 'nasa_power':
        return PLANES[plan]['nasa_power']
    elif funcionalidad == 'curvas_nivel':
        return PLANES[plan]['curvas_nivel']
    elif funcionalidad == 'analisis_textura':
        return PLANES[plan]['analisis_textura']
    elif funcionalidad == 'export_pdf':
        return 'PDF' in PLANES[plan]['exportaciones']
    elif funcionalidad == 'export_docx':
        return 'DOCX' in PLANES[plan]['exportaciones']
    elif funcionalidad == 'export_geojson':
        return 'GEOJSON' in PLANES[plan]['exportaciones']
    elif funcionalidad == 'esri_premium':
        return PLANES[plan].get('esri_premium', False)
    return True

def mostrar_modal_upgrade(funcionalidad=None):
    mensaje = "🔒 Esta funcionalidad está disponible solo en planes superiores."
    if funcionalidad:
        mensaje += f"\n\n**{funcionalidad}** requiere actualizar tu plan."
    
    with st.expander("💎 ACTUALIZAR PLAN", expanded=True):
        st.markdown(mensaje)
        st.markdown("### 🚀 Planes Disponibles")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="plan-card">', unsafe_allow_html=True)
            st.markdown('<div class="badge-plan free">GRATIS</div>', unsafe_allow_html=True)
            st.markdown("### 🆓 Gratuito")
            st.markdown("**$0 / mes**")
            for item in PLANES['FREE']['caracteristicas'][:5]:
                st.markdown(f"{item}")
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="plan-card">', unsafe_allow_html=True)
            st.markdown('<div class="badge-plan">BÁSICO</div>', unsafe_allow_html=True)
            st.markdown("### 🥈 Básico")
            st.markdown(f"**${PLANES['BASICO']['precio']} / mes**")
            for item in PLANES['BASICO']['caracteristicas'][:7]:
                st.markdown(f"{item}")
            if st.button("🚀 Actualizar a Básico", key="btn_basico", use_container_width=True):
                procesar_pago('BASICO')
            st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="plan-card featured">', unsafe_allow_html=True)
            st.markdown('<div class="badge-plan premium">POPULAR</div>', unsafe_allow_html=True)
            st.markdown("### 👑 Premium")
            st.markdown(f"**${PLANES['PREMIUM']['precio']} / mes**")
            for item in PLANES['PREMIUM']['caracteristicas'][:9]:
                st.markdown(f"{item}")
            if st.button("🔥 Obtener Premium", key="btn_premium", use_container_width=True, type="primary"):
                procesar_pago('PREMIUM')
            st.markdown("</div>", unsafe_allow_html=True)

def procesar_pago(plan):
    # Modo demo: activar plan inmediatamente
    st.session_state.plan_actual = plan
    st.session_state.analisis_realizados = 0
    st.success(f"✅ ¡Plan {PLANES[plan]['nombre']} activado! (modo demo)")
    st.rerun()

# === ESTILOS ===
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important; color: #ffffff !important; font-family: 'Inter', sans-serif; }
.plan-banner { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important; color: white !important; padding: 15px 20px !important; border-radius: 12px !important; margin: 10px 0 !important; text-align: center !important; border: 2px solid rgba(255,255,255,0.2) !important; box-shadow: 0 4px 20px rgba(59,130,246,0.4) !important; }
.plan-banner.free { background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%) !important; box-shadow: 0 4px 20px rgba(107,114,128,0.4) !important; }
.plan-banner.premium { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important; box-shadow: 0 4px 20px rgba(245,158,11,0.4) !important; }
.plan-card { background: linear-gradient(135deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95)) !important; border-radius: 20px !important; padding: 25px !important; border: 2px solid rgba(59,130,246,0.2) !important; box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important; transition: all 0.3s ease !important; height: 100% !important; position: relative !important; }
.plan-card:hover { transform: translateY(-8px) !important; box-shadow: 0 20px 40px rgba(59,130,246,0.2) !important; border-color: rgba(59,130,246,0.4) !important; }
.plan-card.featured { border-color: #f59e0b !important; transform: scale(1.05) !important; }
.plan-card.featured:hover { transform: scale(1.05) translateY(-8px) !important; border-color: #fbbf24 !important; }
.badge-plan { position: absolute !important; top: -12px !important; right: 20px !important; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important; color: white !important; padding: 6px 15px !important; border-radius: 20px !important; font-weight: 700 !important; font-size: 0.8em !important; box-shadow: 0 4px 15px rgba(59,130,246,0.4) !important; }
.badge-plan.premium { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important; }
.badge-plan.free { background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%) !important; }
.btn-pago { background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; color: white !important; border: none !important; padding: 1em 2em !important; border-radius: 12px !important; font-weight: 700 !important; font-size: 1.1em !important; box-shadow: 0 4px 20px rgba(16,185,129,0.4) !important; transition: all 0.3s ease !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; width: 100% !important; margin-top: 20px !important; }
.btn-pago:hover { transform: translateY(-3px) !important; box-shadow: 0 8px 25px rgba(16,185,129,0.6) !important; background: linear-gradient(135deg, #34d399 0%, #10b981 100%) !important; }
[data-testid="stSidebar"] { background: #ffffff !important; border-right: 1px solid #e5e7eb !important; box-shadow: 5px 0 25px rgba(0,0,0,0.1) !important; }
[data-testid="stSidebar"] *, [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #000000 !important; }
.sidebar-title { font-size: 1.4em; font-weight: 800; margin: 1.5em 0 1em 0; text-align: center; padding: 14px; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); border-radius: 16px; color: #ffffff !important; box-shadow: 0 6px 20px rgba(59,130,246,0.3); border: 1px solid rgba(255,255,255,0.2); letter-spacing: 0.5px; }
</style>
""", unsafe_allow_html=True)

# === PARÁMETROS AGRÍCOLAS ===
PARAMETROS_CULTIVOS = {
    'MAÍZ': {'NITROGENO': {'min': 150, 'max': 200}, 'FOSFORO': {'min': 40, 'max': 60}, 'POTASIO': {'min': 120, 'max': 180}, 'MATERIA_ORGANICA_OPTIMA': 3.5, 'HUMEDAD_OPTIMA': 0.3, 'NDVI_OPTIMO': 0.85, 'NDRE_OPTIMO': 0.5},
    'SOYA': {'NITROGENO': {'min': 20, 'max': 40}, 'FOSFORO': {'min': 30, 'max': 50}, 'POTASIO': {'min': 80, 'max': 120}, 'MATERIA_ORGANICA_OPTIMA': 4.0, 'HUMEDAD_OPTIMA': 0.25, 'NDVI_OPTIMO': 0.8, 'NDRE_OPTIMO': 0.45},
    'TRIGO': {'NITROGENO': {'min': 120, 'max': 180}, 'FOSFORO': {'min': 40, 'max': 60}, 'POTASIO': {'min': 80, 'max': 120}, 'MATERIA_ORGANICA_OPTIMA': 3.0, 'HUMEDAD_OPTIMA': 0.28, 'NDVI_OPTIMO': 0.75, 'NDRE_OPTIMO': 0.4},
    'GIRASOL': {'NITROGENO': {'min': 80, 'max': 120}, 'FOSFORO': {'min': 35, 'max': 50}, 'POTASIO': {'min': 100, 'max': 150}, 'MATERIA_ORGANICA_OPTIMA': 3.2, 'HUMEDAD_OPTIMA': 0.22, 'NDVI_OPTIMO': 0.7, 'NDRE_OPTIMO': 0.35}
}

TEXTURA_SUELO_OPTIMA = {
    'MAÍZ': {'arena': 40, 'limo': 40, 'arcilla': 20},
    'SOYA': {'arena': 30, 'limo': 50, 'arcilla': 20},
    'TRIGO': {'arena': 50, 'limo': 30, 'arcilla': 20},
    'GIRASOL': {'arena': 60, 'limo': 25, 'arcilla': 15}
}

CLASIFICACION_PENDIENTES = [
    (0, 2, 'Plano', '#2ecc71'),
    (2, 5, 'Ligeramente inclinado', '#f1c40f'),
    (5, 8, 'Moderadamente inclinado', '#e67e22'),
    (8, 15, 'Fuertemente inclinado', '#e74c3c'),
    (15, 30, 'Muy fuertemente inclinado', '#c0392b'),
    (30, 100, 'Extremadamente inclinado', '#000000')
]

RECOMENDACIONES_TEXTURA = {
    'arena': 'Alto drenaje, baja retención de nutrientes. Aumentar materia orgánica.',
    'limo': 'Buena capacidad de retención de agua y nutrientes. Ideal para la mayoría de cultivos.',
    'arcilla': 'Alta capacidad de retención pero drenaje lento. Aireación limitada en suelos compactados.'
}

ICONOS_CULTIVOS = {'MAÍZ': '🌽', 'SOYA': '🫘', 'TRIGO': '🌾', 'GIRASOL': '🌻'}
COLORES_CULTIVOS = {'MAÍZ': '#f1c40f', 'SOYA': '#27ae60', 'TRIGO': '#d35400', 'GIRASOL': '#f39c12'}
PALETAS_GEE = {
    'NDVI': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850'],
    'NDRE': ['#d7191c', '#fdae61', '#ffffbf', '#abdda4', '#2b83ba'],
    'NDWI': ['#a50026', '#d73027', '#f46d43', '#fdae61', '#fee090', '#e0f3f8', '#abd9e9', '#74add1', '#4575b4', '#313695']
}
IMAGENES_CULTIVOS = {
    'MAÍZ': 'https://thumbs.dreamstime.com/b/cartoon-corn-field-background-agriculture-farm-crop-food-summer-ai-generated-illustration-depicting-vibrant-cornfield-386115880.jpg',
    'SOYA': 'https://img.freepik.com/premium-vector/views-plantations-farms-are-decorated-with-backdrop-hills-with-bright-clouds-summer_175103-1247.jpg',
    'TRIGO': 'https://thumbs.dreamstime.com/b/agricultural-crops-rye-rice-maize-wheat-soybean-plant-vector-illustration-secale-cereale-agriculture-cultivated-green-leaves-144102338.jpg',
    'GIRASOL': 'https://thumbs.dreamstime.com/b/cartoon-landscape-showcasing-vibrant-field-sunflowers-full-bloom-set-against-cheerful-blue-sky-fluffy-white-clouds-398818152.jpg'
}

# === FUNCIONES AUXILIARES ===
def validar_y_corregir_crs(gdf):
    if gdf.crs is None:
        gdf.crs = "EPSG:4326"
        st.warning("⚠️ CRS no detectado. Asignado por defecto: EPSG:4326 (WGS84)")
    elif gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    return gdf

def calcular_superficie(gdf):
    gdf_metrico = gdf.to_crs("EPSG:3857")
    area_total_m2 = gdf_metrico.geometry.area.sum()
    return area_total_m2 / 10000

def dividir_parcela_en_zonas(gdf, n_zonas):
    gdf = gdf.reset_index(drop=True)
    if len(gdf) == 1:
        poligono = gdf.geometry.iloc[0]
        minx, miny, maxx, maxy = poligono.bounds
        n = int(np.sqrt(n_zonas))
        paso_x = (maxx - minx) / n
        paso_y = (maxy - miny) / n
        zonas = []
        for i in range(n):
            for j in range(n):
                zona = Polygon([
                    (minx + i*paso_x, miny + j*paso_y),
                    (minx + (i+1)*paso_x, miny + j*paso_y),
                    (minx + (i+1)*paso_x, miny + (j+1)*paso_y),
                    (minx + i*paso_x, miny + (j+1)*paso_y)
                ])
                if poligono.intersects(zona):
                    zonas.append(poligono.intersection(zona))
        if zonas:
            gdf_zonas = gpd.GeoDataFrame(geometry=zonas, crs="EPSG:4326")
            gdf_zonas['id_zona'] = range(1, len(gdf_zonas) + 1)
            return gdf_zonas
    return gdf

def cargar_shapefile_desde_zip(zip_file):
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_file) as zip_ref:
            zip_ref.extractall(tmpdir)
        shapefiles = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
        if not shapefiles:
            raise ValueError("No se encontró archivo .shp en el ZIP")
        gdf = gpd.read_file(os.path.join(tmpdir, shapefiles[0]))
        return validar_y_corregir_crs(gdf)

def cargar_kml(kml_file):
    gdf_list = []
    tree = ET.parse(kml_file)
    root = tree.getroot()
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
    for placemark in root.findall('.//kml:Placemark', namespace):
        polygon = placemark.find('.//kml:Polygon', namespace)
        if polygon is not None:
            outer_ring = polygon.find('.//kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', namespace)
            if outer_ring is not None:
                coords_text = outer_ring.text.strip()
                coords = []
                for coord in coords_text.split():
                    lon_lat = coord.split(',')[:2]
                    if len(lon_lat) == 2:
                        try:
                            lon, lat = float(lon_lat[0]), float(lon_lat[1])
                            if -180 <= lon <= 180 and -90 <= lat <= 90:
                                coords.append((lon, lat))
                        except ValueError:
                            continue
                if len(coords) >= 3:
                    poly = Polygon(coords)
                    gdf_list.append(gpd.GeoDataFrame([1], geometry=[poly], crs="EPSG:4326"))
    if gdf_list:
        gdf = pd.concat(gdf_list, ignore_index=True)
        return validar_y_corregir_crs(gdf)
    raise ValueError("No se encontraron polígonos válidos en el KML")

def cargar_archivo_parcela(uploaded_file):
    extension = uploaded_file.name.split('.')[-1].lower()
    try:
        if extension == 'zip':
            return cargar_shapefile_desde_zip(uploaded_file)
        elif extension in ['kml', 'kmz']:
            return cargar_kml(uploaded_file)
        else:
            raise ValueError(f"Formato no soportado: {extension}")
    except Exception as e:
        st.error(f"Error al cargar archivo: {str(e)}")
        return None

# === DATOS SATELITALES SIMULADOS ===
def generar_datos_simulados(gdf, indice_seleccionado, cultivo, fecha_inicio, fecha_fin):
    np.random.seed(42)
    n = len(gdf)
    if indice_seleccionado == 'NDVI':
        opt = PARAMETROS_CULTIVOS[cultivo]['NDVI_OPTIMO']
        valores = np.random.normal(opt, 0.1, n).clip(0.1, 0.99)
    elif indice_seleccionado == 'NDRE':
        opt = PARAMETROS_CULTIVOS[cultivo]['NDRE_OPTIMO']
        valores = np.random.normal(opt, 0.08, n).clip(0.1, 0.7)
    else:
        valores = np.random.uniform(0.2, 0.8, n)
    gdf[indice_seleccionado.lower()] = valores
    gdf['ndwi'] = np.random.uniform(0.1, 0.5, n)
    gdf['materia_organica'] = np.random.normal(PARAMETROS_CULTIVOS[cultivo]['MATERIA_ORGANICA_OPTIMA'], 0.8, n).clip(0.5, 8.0)
    gdf['humedad_suelo'] = np.random.normal(PARAMETROS_CULTIVOS[cultivo]['HUMEDAD_OPTIMA'], 0.05, n).clip(0.05, 0.8)
    return gdf

# === NASA POWER (SIMULADO) ===
def obtener_datos_nasa_power(gdf, fecha_inicio, fecha_fin):
    if not verificar_funcionalidad('nasa_power'):
        return None
    dias = (fecha_fin - fecha_inicio).days + 1
    fechas = [fecha_inicio + timedelta(days=i) for i in range(dias)]
    np.random.seed(42)
    df = pd.DataFrame({
        'fecha': fechas,
        'radiacion_solar': np.random.uniform(4.0, 6.5, dias),
        'viento_2m': np.random.uniform(1.0, 4.0, dias),
        'precipitacion': np.random.exponential(2.0, dias).clip(0, 50),
        'temperatura': np.random.uniform(15, 35, dias)
    })
    return df

# === ANÁLISIS DE TEXTURA ===
def clasificar_textura_suelo(arena, limo, arcilla):
    textura_clave = max([('arena', arena), ('limo', limo), ('arcilla', arcilla)], key=lambda x: x[1])[0]
    return textura_clave

def analizar_textura_suelo(gdf, cultivo):
    if not verificar_funcionalidad('analisis_textura'):
        st.error("🔒 Análisis de textura no disponible")
        return gdf
    np.random.seed(42)
    arena_opt, limo_opt, arcilla_opt = TEXTURA_SUELO_OPTIMA[cultivo].values()
    gdf['arena'] = np.random.normal(arena_opt, 10, len(gdf)).clip(0, 100)
    gdf['limo'] = np.random.normal(limo_opt, 10, len(gdf)).clip(0, 100)
    gdf['arcilla'] = np.random.normal(arcilla_opt, 5, len(gdf)).clip(0, 100)
    gdf['textura_dominante'] = gdf.apply(lambda row: clasificar_textura_suelo(row['arena'], row['limo'], row['arcilla']), axis=1)
    return gdf

def mostrar_resultados_textura(gdf, cultivo, area_total):
    st.subheader(f"🪴 ANÁLISIS DE TEXTURA DEL SUELO - {cultivo}")
    st.write(f"**Área total analizada:** {area_total:.1f} ha")
    col1, col2 = st.columns(2)
    with col1:
        texto_dominante = gdf['textura_dominante'].mode()[0]
        st.metric("Textura Dominante", texto_dominante.upper())
        st.info(RECOMENDACIONES_TEXTURA[texto_dominante])
    with col2:
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')
        textura_counts = gdf['textura_dominante'].value_counts()
        ax.pie(textura_counts.values, labels=textura_counts.index, autopct='%1.1f%%', textprops={'color': 'white'})
        st.pyplot(fig)

# === CURVAS DE NIVEL (SIMULADO) ===
def generar_dem_sintetico(gdf, resolucion):
    poligono = gdf.unary_union
    minx, miny, maxx, maxy = poligono.bounds
    cols = int((maxx - minx) / (resolucion / 111000))
    rows = int((maxy - miny) / (resolucion / 111000))
    cols = max(cols, 10)
    rows = max(rows, 10)
    x = np.linspace(minx, maxx, cols)
    y = np.linspace(miny, maxy, rows)
    X, Y = np.meshgrid(x, y)
    centro_x = (minx + maxx) / 2
    centro_y = (miny + maxy) / 2
    distancia = np.sqrt((X - centro_x)**2 + (Y - centro_y)**2)
    Z = 100 + 50 * np.sin(distancia * 0.5) + 20 * np.random.random(X.shape)
    return X, Y, Z, poligono

def calcular_pendiente_simple(X, Y, Z, resolucion):
    grad_y, grad_x = np.gradient(Z, resolucion / 111000, resolucion / 111000)
    pendiente = np.arctan(np.sqrt(grad_x**2 + grad_y**2)) * (180 / np.pi)
    return pendiente

def generar_curvas_nivel_simple(X, Y, Z, intervalo, gdf):
    niveles = np.arange(np.floor(Z.min()), np.ceil(Z.max()) + intervalo, intervalo)
    curvas = []
    for nivel in niveles:
        cs = plt.contour(X, Y, Z, levels=[nivel])
        for collection in cs.collections:
            for path in collection.get_paths():
                if len(path.vertices) > 1:
                    coords = path.vertices
                    linea = LineString(coords)
                    if gdf.unary_union.intersects(linea):
                        curvas.append(linea)
    return curvas, niveles

def mostrar_resultados_curvas_nivel(X, Y, Z, pendiente_grid, curvas, elevaciones, gdf, cultivo, area_total):
    st.subheader(f"🏔️ ANÁLISIS DE CURVAS DE NIVEL - {cultivo}")
    st.write(f"**Área total analizada:** {area_total:.1f} ha")
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')
        im = ax.contourf(X, Y, Z, levels=20, cmap='terrain')
        ax.contour(X, Y, Z, levels=elevaciones, colors='white', linewidths=0.5)
        for curva in curvas[:50]:
            x, y = curva.xy
            ax.plot(x, y, 'white', linewidth=0.7)
        ax.set_title("Altitud (m.s.n.m.)", color='white')
        ax.tick_params(colors='white')
        plt.colorbar(im, ax=ax, label='Altitud (m)', pad=0.01)
        st.pyplot(fig)
    with col2:
        fig2, ax2 = plt.subplots(figsize=(8, 6))
        fig2.patch.set_facecolor('#0f172a')
        ax2.set_facecolor('#0f172a')
        im2 = ax2.contourf(X, Y, pendiente_grid, levels=np.linspace(0, 30, 20), cmap='RdYlGn_r')
        ax2.contour(X, Y, pendiente_grid, levels=[2, 5, 8, 15, 30], colors='black', linewidths=0.5)
        ax2.set_title("Pendiente (%)", color='white')
        ax2.tick_params(colors='white')
        plt.colorbar(im2, ax=ax2, label='Pendiente (%)', pad=0.01)
        st.pyplot(fig2)

# === MAPA CON ESRI ===
def crear_mapa_estatico_con_esri(gdf, titulo, columna_valor, analisis_tipo, nutriente, cultivo, satelite):
    if gdf.empty or columna_valor not in gdf.columns:
        return None
    try:
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')
        
        # Usar ESRI solo si el plan lo permite
        if verificar_funcionalidad('esri_premium'):
            try:
                gdf_wm = gdf.to_crs("EPSG:3857")
                ctx.add_basemap(ax, crs=gdf_wm.crs, source=ctx.providers.Esri.WorldImagery, alpha=1.0)
            except Exception as e:
                st.warning("⚠️ No se pudo cargar ESRI. Usando fondo oscuro.")
                ax.set_facecolor('#1e293b')
        else:
            # Fondo oscuro sin ESRI
            ax.set_facecolor('#1e293b')
        
        # Plot zonas
        gdf_plot = gdf.to_crs("EPSG:3857") if verificar_funcionalidad('esri_premium') else gdf
        vmin, vmax = gdf[columna_valor].min(), gdf[columna_valor].max()
        gdf_plot.plot(column=columna_valor, ax=ax, legend=True, vmin=vmin, vmax=vmax,
                      cmap='RdYlGn_r', edgecolor='white', linewidth=0.5, alpha=0.7,
                      legend_kwds={'shrink': 0.3, 'pad': 0.01})
        
        ax.set_title(f"{titulo} - {cultivo}", color='white', fontsize=14)
        ax.set_axis_off()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close(fig)
        return buf
    except Exception as e:
        st.error(f"Error creando mapa: {e}")
        return None

# === REPORTES ===
def generar_reporte_pdf(gdf, cultivo, analisis_tipo, area_total, nutriente=None, satelite=None, indice=None, mapa_buffer=None, estadisticas=None, recomendaciones=None):
    if not verificar_funcionalidad('export_pdf'):
        return None
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Reporte de Análisis Agrícola - {cultivo}", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Tipo de Análisis: {analisis_tipo}", ln=True)
        if nutriente:
            pdf.cell(0, 10, f"Nutriente: {nutriente}", ln=True)
        if satelite:
            pdf.cell(0, 10, f"Satélite: {satelite}", ln=True)
        if indice:
            pdf.cell(0, 10, f"Índice: {indice}", ln=True)
        pdf.cell(0, 10, f"Área Total: {area_total:.1f} ha", ln=True)
        pdf.ln(10)
        
        if mapa_buffer:
            mapa_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
            with open(mapa_path, "wb") as f:
                f.write(mapa_buffer.getbuffer())
            pdf.image(mapa_path, x=10, w=190)
            os.unlink(mapa_path)
            pdf.ln(5)
        
        if estadisticas:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Resumen Estadístico", ln=True)
            pdf.set_font("Arial", "", 12)
            for k, v in estadisticas.items():
                pdf.cell(0, 8, f"{k}: {v}", ln=True)
            pdf.ln(5)
        
        if recomendaciones:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Recomendaciones", ln=True)
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 8, recomendaciones)
        
        buf = BytesIO()
        pdf.output(buf)
        buf.seek(0)
        return buf
    except Exception as e:
        st.error(f"Error PDF: {e}")
        return None

def generar_reporte_docx(gdf, cultivo, analisis_tipo, area_total, nutriente=None, satelite=None, indice=None, mapa_buffer=None, estadisticas=None, recomendaciones=None):
    if not verificar_funcionalidad('export_docx'):
        return None
    try:
        doc = Document()
        doc.add_heading(f'Reporte de Análisis Agrícola - {cultivo}', 0)
        doc.add_paragraph(f'Tipo de Análisis: {analisis_tipo}')
        if nutriente:
            doc.add_paragraph(f'Nutriente: {nutriente}')
        if satelite:
            doc.add_paragraph(f'Satélite: {satelite}')
        if indice:
            doc.add_paragraph(f'Índice: {indice}')
        doc.add_paragraph(f'Área Total: {area_total:.1f} ha')
        doc.add_paragraph()
        
        if mapa_buffer:
            mapa_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
            with open(mapa_path, "wb") as f:
                f.write(mapa_buffer.getbuffer())
            doc.add_picture(mapa_path, width=Inches(6))
            os.unlink(mapa_path)
            doc.add_paragraph()
        
        if estadisticas:
            doc.add_heading('Resumen Estadístico', level=1)
            table = doc.add_table(rows=1, cols=2)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'Indicador'
            hdr_cells[1].text = 'Valor'
            for k, v in estadisticas.items():
                row_cells = table.add_row().cells
                row_cells[0].text = str(k)
                row_cells[1].text = str(v)
            doc.add_paragraph()
        
        if recomendaciones:
            doc.add_heading('Recomendaciones', level=1)
            doc.add_paragraph(recomendaciones)
        
        buf = BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf
    except Exception as e:
        st.error(f"Error DOCX: {e}")
        return None

def exportar_a_geojson(gdf, nombre_base="parcela"):
    if not verificar_funcionalidad('export_geojson'):
        return None, None
    try:
        gdf_export = gdf.copy()
        if 'geometry' not in gdf_export.columns:
            return None, None
        gdf_export = gdf_export.to_crs("EPSG:4326")
        geojson_str = gdf_export.to_json()
        nombre_archivo = f"{nombre_base}_{datetime.now().strftime('%Y%m%d_%H%M')}.geojson"
        return geojson_str, nombre_archivo
    except Exception as e:
        st.error(f"Error GeoJSON: {e}")
        return None, None

# === FUNCIONES DE APOYO ===
def crear_grafico_personalizado(serie, titulo, ylabel, color):
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#1e293b')
    ax.plot(serie.index, serie.values, color=color, linewidth=2.5)
    ax.set_title(titulo, color='white')
    ax.set_ylabel(ylabel, color='white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.grid(True, alpha=0.3, color='#475569')
    for spine in ax.spines.values():
        spine.set_color('#475569')
    return fig

def crear_grafico_barras_personalizado(serie, titulo, ylabel, color):
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#1e293b')
    ax.bar(serie.index, serie.values, color=color, alpha=0.7)
    ax.set_title(titulo, color='white')
    ax.set_ylabel(ylabel, color='white')
    ax.tick_params(axis='x', colors='white', rotation=45)
    ax.tick_params(axis='y', colors='white')
    ax.grid(True, alpha=0.3, color='#475569', axis='y')
    for spine in ax.spines.values():
        spine.set_color('#475569')
    return fig

def crear_mapa_potencial_cosecha_calor(gdf, cultivo):
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')
        gdf_plot = gdf.to_crs("EPSG:3857")
        gdf_plot.plot(column='potencial_cosecha', ax=ax, cmap='RdYlGn', legend=True,
                      legend_kwds={'shrink': 0.4, 'pad': 0.01})
        ax.set_title(f"Potencial de Cosecha Estimado - {cultivo}", color='white')
        ax.set_axis_off()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close(fig)
        return buf
    except:
        return None

def generar_resumen_estadisticas(gdf, analisis_tipo, cultivo, df_power=None):
    stats = {
        "Zonas Analizadas": len(gdf),
        "Área Total (ha)": calcular_superficie(gdf),
    }
    if 'npk_actual' in gdf.columns:
        stats["NPK Promedio"] = f"{gdf['npk_actual'].mean():.3f}"
    if 'valor_recomendado' in gdf.columns:
        stats["Recomendación Promedio"] = f"{gdf['valor_recomendado'].mean():.1f} kg/ha"
    if 'ndvi' in gdf.columns:
        stats["NDVI Promedio"] = f"{gdf['ndvi'].mean():.3f}"
    if df_power is not None:
        stats["Radiación Solar Promedio"] = f"{df_power['radiacion_solar'].mean():.1f} kWh/m²/día"
    return stats

def generar_recomendaciones_generales(gdf, analisis_tipo, cultivo):
    if analisis_tipo == "RECOMENDACIONES NPK":
        promedio = gdf['valor_recomendado'].mean()
        return f"Se recomienda aplicar un promedio de {promedio:.1f} kg/ha según el análisis por zonas. Consulte el mapa para aplicación variable."
    elif analisis_tipo == "FERTILIDAD ACTUAL":
        npk_prom = gdf['npk_actual'].mean()
        if npk_prom > 0.7:
            return "La fertilidad actual es alta. Monitoree para evitar excesos."
        elif npk_prom > 0.4:
            return "Fertilidad moderada. Considere aplicación de nutrientes según zonas."
        else:
            return "Baja fertilidad detectada. Recomendada aplicación de nutrientes balanceados."
    else:
        return "Análisis completado. Consulte los resultados detallados en las pestañas."

# === EJECUTAR ANÁLISIS ===
def ejecutar_analisis(gdf, nutriente, analisis_tipo, n_divisiones, cultivo, satelite_seleccionado=None,
                      indice_seleccionado=None, fecha_inicio=None, fecha_fin=None,
                      intervalo_curvas=None, resolucion_dem=None):
    try:
        gdf_zonas = dividir_parcela_en_zonas(gdf, n_divisiones)
        area_total = calcular_superficie(gdf)
        
        if analisis_tipo == "ANÁLISIS DE TEXTURA":
            gdf_resultado = analizar_textura_suelo(gdf_zonas, cultivo)
            return {'exitoso': True, 'gdf_analizado': gdf_resultado, 'area_total': area_total}
        
        elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
            return {'exitoso': True, 'gdf_analizado': gdf_zonas, 'area_total': area_total}
        
        else:  # Análisis GEE
            if satelite_seleccionado == 'DATOS_SIMULADOS':
                gdf_con_datos = generar_datos_simulados(gdf_zonas, indice_seleccionado, cultivo, fecha_inicio, fecha_fin)
            else:
                gdf_con_datos = generar_datos_simulados(gdf_zonas, indice_seleccionado, cultivo, fecha_inicio, fecha_fin)
            
            # Simular cálculo de NPK
            gdf_con_datos['npk_actual'] = (
                0.3 * gdf_con_datos[indice_seleccionado.lower()] +
                0.4 * (gdf_con_datos['materia_organica'] / 10) +
                0.3 * gdf_con_datos['humedad_suelo']
            ).clip(0, 1)
            
            if analisis_tipo == "RECOMENDACIONES NPK" and nutriente:
                rango = PARAMETROS_CULTIVOS[cultivo][nutriente]
                gdf_con_datos['valor_recomendado'] = (
                    rango['min'] + (1 - gdf_con_datos['npk_actual']) * (rango['max'] - rango['min'])
                ).clip(rango['min'], rango['max'])
            
            df_power = obtener_datos_nasa_power(gdf_con_datos, fecha_inicio, fecha_fin)
            
            return {
                'exitoso': True,
                'gdf_analizado': gdf_con_datos,
                'area_total': area_total,
                'df_power': df_power
            }
    except Exception as e:
        st.error(f"Error en análisis: {str(e)}")
        return {'exitoso': False}

# === INTERFAZ PRINCIPAL ===
st.markdown("""
<div class="hero-banner">
    <div class="hero-content">
        <h1 class="hero-title">ANALIZADOR MULTI-CULTIVO SATELITAL</h1>
        <p class="hero-subtitle">Potenciado con NASA POWER, GEE y tecnología avanzada para una agricultura de precisión</p>
    </div>
</div>
""", unsafe_allow_html=True)

plan_clase = "free" if st.session_state.plan_actual == "FREE" else "premium" if st.session_state.plan_actual == "PREMIUM" else ""
st.markdown(f"""
<div class="plan-banner {plan_clase}">
    <h4>📊 PLAN ACTUAL: <strong>{PLANES[st.session_state.plan_actual]['nombre']}</strong></h4>
    <p>Análisis realizados este mes: {st.session_state.analisis_realizados}/{PLANES[st.session_state.plan_actual]['limite_analisis']}</p>
</div>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.markdown('<div class="sidebar-title">💰 TU PLAN</div>', unsafe_allow_html=True)
    plan_info = PLANES[st.session_state.plan_actual]
    st.metric(f"Plan {plan_info['nombre']}", f"${plan_info['precio']}/mes" if plan_info['precio'] > 0 else "Gratis")
    porcentaje_uso = min(st.session_state.analisis_realizados / plan_info['limite_analisis'], 1.0)
    st.progress(porcentaje_uso)
    st.caption(f"📊 {st.session_state.analisis_realizados}/{plan_info['limite_analisis']} análisis usados")
    if st.button("⚡ Actualizar Plan", use_container_width=True):
        mostrar_modal_upgrade()
    
    st.markdown("---")
    st.markdown('<div class="sidebar-title">⚙️ CONFIGURACIÓN</div>', unsafe_allow_html=True)
    
    cultivos_disponibles = PLANES[st.session_state.plan_actual]['cultivos_disponibles']
    cultivo = st.selectbox("Cultivo:", cultivos_disponibles)
    if cultivo in IMAGENES_CULTIVOS:
        st.image(IMAGENES_CULTIVOS[cultivo], use_container_width=True)
    
    opciones_analisis = ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK", "POTENCIAL DE COSECHA (NPK)"]
    if verificar_funcionalidad('analisis_textura'):
        opciones_analisis.append("ANÁLISIS DE TEXTURA")
    if verificar_funcionalidad('curvas_nivel'):
        opciones_analisis.append("ANÁLISIS DE CURVAS DE NIVEL")
    
    analisis_tipo = st.selectbox("Tipo de Análisis:", opciones_analisis)
    
    if analisis_tipo == "ANÁLISIS DE TEXTURA" and not verificar_funcionalidad('analisis_textura'):
        st.warning("🔒 Requiere plan Básico+")
        mostrar_modal_upgrade("Análisis de Textura")
        analisis_tipo = "FERTILIDAD ACTUAL"
    if analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL" and not verificar_funcionalidad('curvas_nivel'):
        st.warning("🔒 Requiere plan Básico+")
        mostrar_modal_upgrade("Curvas de Nivel")
        analisis_tipo = "FERTILIDAD ACTUAL"
    
    nutriente = None
    if analisis_tipo in ["RECOMENDACIONES NPK", "POTENCIAL DE COSECHA (NPK)"]:
        nutriente = st.selectbox("Nutriente:", ["NITRÓGENO", "FÓSFORO", "POTASIO"])
    
    satelites_disponibles = PLANES[st.session_state.plan_actual]['satelites_disponibles']
    satelite_seleccionado = st.selectbox("Satélite:", satelites_disponibles)
    satelite_info = SATELITES_DISPONIBLES[satelite_seleccionado]
    st.info(f"""**{satelite_info['icono']} {satelite_info['nombre']}**
    - Resolución: {satelite_info['resolucion']}
    - Revisita: {satelite_info['revisita']}
    - Índices: {', '.join(satelite_info['indices'][:3])}""")
    
    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK", "POTENCIAL DE COSECHA (NPK)"]:
        indice_seleccionado = st.selectbox("Índice:", satelite_info['indices'])
        fecha_fin = st.date_input("Fecha fin", datetime.now())
        fecha_inicio = st.date_input("Fecha inicio", datetime.now() - timedelta(days=30))
    
    n_divisiones_max = 32 if st.session_state.plan_actual == 'FREE' else 50 if st.session_state.plan_actual == 'BASICO' else 200
    n_divisiones = st.slider("Número de zonas:", 16, n_divisiones_max, min(32, n_divisiones_max))
    
    intervalo_curvas = 5.0
    resolucion_dem = 10.0
    if analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL" and verificar_funcionalidad('curvas_nivel'):
        intervalo_max = PLANES[st.session_state.plan_actual].get('intervalo_curvas_max', 5.0)
        intervalo_curvas = st.slider("Intervalo (m):", 1.0, intervalo_max, 5.0, 1.0)
        resolucion_dem = st.slider("Resolución DEM (m):", 5.0, 50.0, 10.0, 5.0)
    
    uploaded_file = st.file_uploader("Subir parcela", type=['zip','kml','kmz'])

# === EJECUCIÓN ===
if uploaded_file:
    with st.spinner("Cargando parcela..."):
        try:
            gdf = cargar_archivo_parcela(uploaded_file)
            if gdf is not None:
                st.success(f"✅ **Parcela cargada exitosamente:** {len(gdf)} polígono(s)")
                area_total = calcular_superficie(gdf)
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**📊 INFORMACIÓN DE LA PARCELA:**")
                    st.write(f"- Polígonos: {len(gdf)}")
                    st.write(f"- Área total: {area_total:.1f} ha")
                    st.write(f"- CRS: {gdf.crs}")
                    st.write(f"- Formato: {uploaded_file.name.split('.')[-1].upper()}")
                    st.write("**📍 Vista Previa:**")
                    fig, ax = plt.subplots(figsize=(8, 6))
                    fig.patch.set_facecolor('#0f172a')
                    ax.set_facecolor('#0f172a')
                    gdf.plot(ax=ax, color='lightgreen', edgecolor='white', alpha=0.7)
                    ax.set_title(f"Parcela: {uploaded_file.name}", color='white')
                    ax.set_xlabel("Longitud", color='white')
                    ax.set_ylabel("Latitud", color='white')
                    ax.tick_params(colors='white')
                    ax.grid(True, alpha=0.3, color='#475569')
                    st.pyplot(fig)
                with col2:
                    st.write("**🎯 CONFIGURACIÓN GEE:**")
                    st.write(f"- Cultivo: {ICONOS_CULTIVOS[cultivo]} {cultivo}")
                    st.write(f"- Análisis: {analisis_tipo}")
                    st.write(f"- Zonas: {n_divisiones}")
                    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
                        st.write(f"- Satélite: {SATELITES_DISPONIBLES[satelite_seleccionado]['nombre']}")
                        st.write(f"- Índice: {indice_seleccionado}")
                        st.write(f"- Período: {fecha_inicio} a {fecha_fin}")
                    elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                        st.write(f"- Intervalo curvas: {intervalo_curvas} m")
                        st.write(f"- Resolución DEM: {resolucion_dem} m")

                if st.button("🚀 EJECUTAR ANÁLISIS COMPLETO", type="primary"):
                    limite_ok, mensaje_limite = verificar_limite_analisis()
                    if not limite_ok:
                        st.error(mensaje_limite)
                        mostrar_modal_upgrade()
                    else:
                        resultados = None
                        if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
                            if satelite_seleccionado != 'DATOS_SIMULADOS' and not verificar_funcionalidad('nasa_power'):
                                st.warning("⚠️ Datos de NASA POWER no disponibles en tu plan. Continuando sin ellos.")
                            resultados = ejecutar_analisis(
                                gdf, nutriente, analisis_tipo, n_divisiones,
                                cultivo, satelite_seleccionado, indice_seleccionado,
                                fecha_inicio, fecha_fin
                            )
                        elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                            if not verificar_funcionalidad('curvas_nivel'):
                                st.error("🔒 Las curvas de nivel requieren plan Básico o superior")
                                mostrar_modal_upgrade("Curvas de Nivel")
                            else:
                                resultados = ejecutar_analisis(
                                    gdf, None, analisis_tipo, n_divisiones,
                                    cultivo, None, None, None, None,
                                    intervalo_curvas, resolucion_dem
                                )
                        else:  # ANÁLISIS DE TEXTURA
                            if not verificar_funcionalidad('analisis_textura'):
                                st.error("🔒 El análisis de textura requiere plan Básico o superior")
                                mostrar_modal_upgrade("Análisis de Textura")
                            else:
                                resultados = ejecutar_analisis(
                                    gdf, None, analisis_tipo, n_divisiones,
                                    cultivo, None, None, None, None
                                )

                        if resultados and resultados['exitoso']:
                            registrar_analisis()
                            st.success(f"✅ Análisis completado. Usos restantes: {PLANES[st.session_state.plan_actual]['limite_analisis'] - st.session_state.analisis_realizados}")

                            res_guardar = {
                                'gdf_analizado': resultados['gdf_analizado'],
                                'analisis_tipo': analisis_tipo,
                                'cultivo': cultivo,
                                'area_total': resultados['area_total'],
                                'nutriente': nutriente,
                                'satelite_seleccionado': satelite_seleccionado,
                                'indice_seleccionado': indice_seleccionado,
                                'mapa_buffer': None,
                                'X': None,
                                'Y': None,
                                'Z': None,
                                'pendiente_grid': None,
                                'gdf_original': gdf if analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL" else None,
                                'df_power': resultados.get('df_power')
                            }

                            if analisis_tipo == "ANÁLISIS DE TEXTURA":
                                mostrar_resultados_textura(resultados['gdf_analizado'], cultivo, resultados['area_total'])
                            elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                                X, Y, Z, _ = generar_dem_sintetico(gdf, resolucion_dem)
                                pendiente_grid = calcular_pendiente_simple(X, Y, Z, resolucion_dem)
                                curvas, elevaciones = generar_curvas_nivel_simple(X, Y, Z, intervalo_curvas, gdf)
                                res_guardar.update({'X': X, 'Y': Y, 'Z': Z, 'pendiente_grid': pendiente_grid})
                                mostrar_resultados_curvas_nivel(X, Y, Z, pendiente_grid, curvas, elevaciones, gdf, cultivo, resultados['area_total'])
                            else:
                                gdf_analizado = resultados['gdf_analizado']
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Zonas Analizadas", len(gdf_analizado))
                                with col2:
                                    st.metric("Área Total", f"{resultados['area_total']:.1f} ha")
                                with col3:
                                    if analisis_tipo == "FERTILIDAD ACTUAL":
                                        valor_prom = gdf_analizado['npk_actual'].mean()
                                        st.metric("Índice NPK Promedio", f"{valor_prom:.3f}")
                                    else:
                                        valor_prom = gdf_analizado['valor_recomendado'].mean()
                                        st.metric(f"{nutriente} Promedio", f"{valor_prom:.1f} kg/ha")
                                with col4:
                                    if gdf_analizado['npk_actual'].mean() > 0:
                                        coef_var = (gdf_analizado['npk_actual'].std() / gdf_analizado['npk_actual'].mean() * 100)
                                        st.metric("Coef. Variación", f"{coef_var:.1f}%")

                                if resultados.get('df_power') is not None:
                                    df_power = resultados['df_power']
                                    st.subheader("🌤️ DATOS METEOROLÓGICOS (NASA POWER)")
                                    col5, col6, col7 = st.columns(3)
                                    with col5:
                                        st.metric("☀️ Radiación Solar", f"{df_power['radiacion_solar'].mean():.1f} kWh/m²/día")
                                    with col6:
                                        st.metric("💨 Viento a 2m", f"{df_power['viento_2m'].mean():.2f} m/s")
                                    with col7:
                                        st.metric("💧 NDWI Promedio", f"{gdf_analizado['ndwi'].mean():.3f}")

                                    tab_radiacion, tab_viento, tab_precip, tab_cosecha = st.tabs([
                                        "☀️ Radiación", "💨 Viento", "🌧️ Precip", "🔥 Cosecha"
                                    ])
                                    with tab_radiacion:
                                        serie_rad = df_power.set_index('fecha')['radiacion_solar']
                                        st.pyplot(crear_grafico_personalizado(serie_rad, "Radiación Solar", "kWh/m²/día", '#e67e22'))
                                    with tab_viento:
                                        serie_viento = df_power.set_index('fecha')['viento_2m']
                                        st.pyplot(crear_grafico_personalizado(serie_viento, "Viento", "m/s", '#3498db'))
                                    with tab_precip:
                                        serie_precip = df_power.set_index('fecha')['precipitacion']
                                        st.pyplot(crear_grafico_barras_personalizado(serie_precip, "Precipitación", "mm/día", '#2ecc71'))
                                    with tab_cosecha:
                                        rad_prom = df_power['radiacion_solar'].mean()
                                        viento_prom = df_power['viento_2m'].mean()
                                        gdf_analizado['radiacion_solar'] = rad_prom
                                        gdf_analizado['viento_2m'] = viento_prom
                                        gdf_analizado['solar_norm'] = gdf_analizado['radiacion_solar'].apply(lambda x: np.clip((x - 3.0)/(7.0-3.0), 0, 1))
                                        gdf_analizado['viento_norm'] = gdf_analizado['viento_2m'].apply(lambda x: np.clip(1 - (x - 1.0)/(5.0-1.0), 0, 1))
                                        gdf_analizado['humedad_norm'] = gdf_analizado['ndwi'].apply(lambda x: np.clip((x - 0.1)/(0.4-0.1), 0, 1))
                                        gdf_analizado['potencial_cosecha'] = (
                                            0.40 * gdf_analizado['npk_actual'] +
                                            0.25 * gdf_analizado['solar_norm'] +
                                            0.20 * gdf_analizado['humedad_norm'] +
                                            0.15 * gdf_analizado['viento_norm']
                                        ).clip(0, 1)
                                        mapa_calor = crear_mapa_potencial_cosecha_calor(gdf_analizado, cultivo)
                                        if mapa_calor:
                                            st.image(mapa_calor, use_container_width=True)

                                columna_valor = 'valor_recomendado' if analisis_tipo == "RECOMENDACIONES NPK" else 'npk_actual'
                                mapa_buffer = crear_mapa_estatico_con_esri(gdf_analizado,
                                    f"ANÁLISIS {analisis_tipo}",
                                    columna_valor,
                                    analisis_tipo,
                                    nutriente,
                                    cultivo,
                                    satelite_seleccionado
                                )
                                if mapa_buffer:
                                    res_guardar['mapa_buffer'] = mapa_buffer
                                    st.subheader(f"🗺️ MAPA CON ESRI SATELLITE - {analisis_tipo}")
                                    st.image(mapa_buffer, use_container_width=True)

                                st.subheader("🔬 ÍNDICES SATELITALES GEE POR ZONA")
                                columnas_indices = ['id_zona', 'npk_actual', 'materia_organica', 'ndvi', 'ndre', 'humedad_suelo', 'ndwi']
                                if analisis_tipo == "RECOMENDACIONES NPK":
                                    columnas_indices = ['id_zona', 'valor_recomendado', 'npk_actual', 'materia_organica', 'ndvi', 'ndre', 'humedad_suelo', 'ndwi']
                                columnas_indices = [col for col in columnas_indices if col in gdf_analizado.columns]
                                tabla_indices = gdf_analizado[columnas_indices].copy()
                                rename_dict = {'id_zona': 'Zona', 'npk_actual': 'NPK Actual', 'valor_recomendado': 'Recomendación', 'materia_organica': 'Materia Org (%)', 'ndvi': 'NDVI', 'ndre': 'NDRE', 'humedad_suelo': 'Humedad', 'ndwi': 'NDWI'}
                                tabla_indices = tabla_indices.rename(columns={k: v for k, v in rename_dict.items() if k in tabla_indices.columns})
                                st.dataframe(tabla_indices)

                            st.session_state['resultados_guardados'] = res_guardar
                        else:
                            st.error("❌ No se pudieron obtener resultados del análisis.")
            else:
                st.error("❌ No se pudo cargar la parcela.")
        except Exception as e:
            st.error(f"❌ Error procesando archivo: {str(e)}")
            import traceback
            st.error(f"Detalle: {traceback.format_exc()}")
else:
    st.info("📁 Sube un archivo de tu parcela para comenzar el análisis")

# === EXPORTACIÓN ===
if 'resultados_guardados' in st.session_state:
    res = st.session_state['resultados_guardados']
    st.markdown("---")
    st.subheader("📤 EXPORTAR RESULTADOS")

    col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)

    with col_exp1:
        if st.button("📊 Exportar CSV", key="export_csv"):
            if res['gdf_analizado'] is not None:
                df_export = res['gdf_analizado'].drop(columns=['geometry'], errors='ignore').copy()
                csv = df_export.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name=f"datos_{res['cultivo']}_{res['analisis_tipo'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="csv_download"
                )

    with col_exp2:
        if verificar_funcionalidad('export_pdf'):
            if st.button("📄 Generar PDF", key="export_pdf"):
                with st.spinner("Generando PDF..."):
                    estadisticas = generar_resumen_estadisticas(res['gdf_analizado'], res['analisis_tipo'], res['cultivo'], res.get('df_power'))
                    recomendaciones = generar_recomendaciones_generales(res['gdf_analizado'], res['analisis_tipo'], res['cultivo'])
                    pdf_buffer = generar_reporte_pdf(
                        res['gdf_analizado'], res['cultivo'], res['analisis_tipo'], res['area_total'],
                        res.get('nutriente'), res.get('satelite_seleccionado'), res.get('indice_seleccionado'),
                        res.get('mapa_buffer'), estadisticas, recomendaciones
                    )
                    if pdf_buffer:
                        st.download_button(
                            label="📥 Descargar PDF",
                            data=pdf_buffer,
                            file_name=f"reporte_{res['cultivo']}_{res['analisis_tipo'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf",
                            key="pdf_download"
                        )
        else:
            st.button("🔒 PDF (Requiere Básico+)", key="pdf_locked", disabled=True)
            st.caption("Plan Básico+")

    with col_exp3:
        if verificar_funcionalidad('export_docx'):
            if st.button("📝 Generar DOCX", key="export_docx"):
                with st.spinner("Generando DOCX..."):
                    estadisticas = generar_resumen_estadisticas(res['gdf_analizado'], res['analisis_tipo'], res['cultivo'], res.get('df_power'))
                    recomendaciones = generar_recomendaciones_generales(res['gdf_analizado'], res['analisis_tipo'], res['cultivo'])
                    docx_buffer = generar_reporte_docx(
                        res['gdf_analizado'], res['cultivo'], res['analisis_tipo'], res['area_total'],
                        res.get('nutriente'), res.get('satelite_seleccionado'), res.get('indice_seleccionado'),
                        res.get('mapa_buffer'), estadisticas, recomendaciones
                    )
                    if docx_buffer:
                        st.download_button(
                            label="📥 Descargar DOCX",
                            data=docx_buffer,
                            file_name=f"reporte_{res['cultivo']}_{res['analisis_tipo'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="docx_download"
                        )
        else:
            st.button("🔒 DOCX (Requiere Premium)", key="docx_locked", disabled=True)
            st.caption("Plan Premium")

    with col_exp4:
        if verificar_funcionalidad('export_geojson'):
            if st.button("🗺️ Exportar GeoJSON", key="export_geojson"):
                geojson_data, nombre_archivo = exportar_a_geojson(res['gdf_analizado'], f"parcela_{res['cultivo']}")
                if geojson_data:
                    st.download_button(
                        label="📥 Descargar GeoJSON",
                        data=geojson_data,
                        file_name=nombre_archivo,
                        mime="application/json",
                        key="geojson_download"
                    )
        else:
            st.button("🔒 GeoJSON (Requiere Premium)", key="geojson_locked", disabled=True)
            st.caption("Plan Premium")

# === PLANES ===
st.markdown("---")
st.subheader("💎 ELIGE EL PLAN PERFECTO PARA TI")

col_plan1, col_plan2, col_plan3 = st.columns(3)
for i, (key, plan) in enumerate(PLANES.items()):
    with [col_plan1, col_plan2, col_plan3][i]:
        badge_class = "free" if key == 'FREE' else "premium" if key == 'PREMIUM' else ""
        featured = "featured" if key == 'PREMIUM' else ""
        st.markdown(f'<div class="plan-card {featured}">', unsafe_allow_html=True)
        if key == 'PREMIUM':
            st.markdown('<div class="badge-plan premium">POPULAR</div>', unsafe_allow_html=True)
        elif key == 'FREE':
            st.markdown('<div class="badge-plan free">GRATIS</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="badge-plan">BÁSICO</div>', unsafe_allow_html=True)
        st.markdown(f"### {'👑' if key=='PREMIUM' else '🥈' if key=='BASICO' else '🆓'} {plan['nombre']}")
        st.markdown(f"**${plan['precio']} / mes**" if plan['precio'] > 0 else "**$0 / mes**")
        for item in plan['caracteristicas']:
            st.markdown(f"{item}")
        if st.session_state.plan_actual == key:
            st.success("✅ Plan actual")
        elif key == 'FREE':
            if st.button("Seleccionar Gratis", key=f"select_{key}", use_container_width=True):
                st.session_state.plan_actual = key
                st.session_state.analisis_realizados = 0
                st.rerun()
        else:
            if st.button(f"{'Obtener Premium' if key=='PREMIUM' else 'Actualizar a Básico'} - ${plan['precio']}/mes",
                        key=f"select_{key}", use_container_width=True, type="primary" if key=='PREMIUM' else "secondary"):
                procesar_pago(key)
        st.markdown("</div>", unsafe_allow_html=True)

with st.expander("❓ PREGUNTAS FRECUENTES SOBRE PRECIOS"):
    col_faq1, col_faq2 = st.columns(2)
    with col_faq1:
        st.markdown("**💳 ¿Cómo funcionan los pagos?**")
        st.markdown("- Pagos seguros mediante MercadoPago\n- Facturación mensual\n- Puedes cancelar en cualquier momento")
    with col_faq2:
        st.markdown("**🎯 ¿Hay prueba gratuita?**")
        st.markdown("- Sí, el plan Gratuito es siempre gratuito\n- Incluye 3 análisis mensuales\n- Perfecto para probar la plataforma")

st.info("💡 **Consejo**: Actualiza a Premium para desbloquear todas las funcionalidades avanzadas y exportaciones profesionales.")
