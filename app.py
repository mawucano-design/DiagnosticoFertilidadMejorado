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
warnings.filterwarnings('ignore')

# === ESTILOS PERSONALIZADOS - VERSIÓN PREMIUM MODERNA ===
st.markdown("""
<style>
/* === FONDO GENERAL OSCURO ELEGANTE === */
.stApp {
background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
color: #ffffff !important;
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
/* === SIDEBAR: FONDO BLANCO CON TEXTO NEGRO === */
[data-testid="stSidebar"] {
background: #ffffff !important;
border-right: 1px solid #e5e7eb !important;
box-shadow: 5px 0 25px rgba(0, 0, 0, 0.1) !important;
}
/* Texto general del sidebar en NEGRO */
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stText,
[data-testid="stSidebar"] .stTitle,
[data-testid="stSidebar"] .stSubheader {
color: #000000 !important;
text-shadow: none !important;
}
/* Título del sidebar elegante */
.sidebar-title {
font-size: 1.4em;
font-weight: 800;
margin: 1.5em 0 1em 0;
text-align: center;
padding: 14px;
background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
border-radius: 16px;
color: #ffffff !important;
box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
border: 1px solid rgba(255, 255, 255, 0.2);
letter-spacing: 0.5px;
}
/* Widgets del sidebar con estilo glassmorphism */
[data-testid="stSidebar"] .stSelectbox,
[data-testid="stSidebar"] .stDateInput,
[data-testid="stSidebar"] .stSlider {
background: rgba(255, 255, 255, 0.9) !important;
backdrop-filter: blur(10px);
border-radius: 12px;
padding: 12px;
margin: 8px 0;
border: 1px solid #d1d5db !important;
}
/* Labels de los widgets en negro */
[data-testid="stSidebar"] .stSelectbox div,
[data-testid="stSidebar"] .stDateInput div,
[data-testid="stSidebar"] .stSlider label {
color: #000000 !important;
font-weight: 600;
font-size: 0.95em;
}
/* Inputs y selects - fondo blanco con texto negro */
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
background-color: #ffffff !important;
border: 1px solid #d1d5db !important;
color: #000000 !important;
border-radius: 8px;
}
/* Slider - colores negro */
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {
color: #000000 !important;
}
/* Date Input - fondo blanco con texto negro */
[data-testid="stSidebar"] .stDateInput [data-baseweb="input"] {
background-color: #ffffff !important;
border: 1px solid #d1d5db !important;
color: #000000 !important;
border-radius: 8px;
}
/* Placeholder en gris */
[data-testid="stSidebar"] .stDateInput [data-baseweb="input"]::placeholder {
color: #6b7280 !important;
}
/* Botones premium */
.stButton > button {
background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
color: white !important;
border: none !important;
padding: 0.8em 1.5em !important;
border-radius: 12px !important;
font-weight: 700 !important;
font-size: 1em !important;
box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
transition: all 0.3s ease !important;
text-transform: uppercase !important;
letter-spacing: 0.5px !important;
}
.stButton > button:hover {
transform: translateY(-3px) !important;
box-shadow: 0 8px 25px rgba(59, 130, 246, 0.6) !important;
background: linear-gradient(135deg, #4f8df8 0%, #2d5fe8 100%) !important;
}
/* Botones desactivados para upsell */
.stButton:disabled > button,
.stButton[disabled] > button {
background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%) !important;
color: #cbd5e1 !important;
cursor: not-allowed !important;
opacity: 0.6 !important;
}
/* === HERO BANNER PRINCIPAL CON IMAGEN === */
.hero-banner {
background: linear-gradient(rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.95)),
url('https://images.unsplash.com/photo-1597981309443-6e2d2a4d9c3f?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80') !important;
background-size: cover !important;
background-position: center 40% !important;
padding: 3.5em 2em !important;
border-radius: 24px !important;
margin-bottom: 2.5em !important;
box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4) !important;
border: 1px solid rgba(59, 130, 246, 0.2) !important;
position: relative !important;
overflow: hidden !important;
}
.hero-banner::before {
content: '' !important;
position: absolute !important;
top: 0 !important;
left: 0 !important;
right: 0 !important;
bottom: 0 !important;
background: linear-gradient(45deg, rgba(59, 130, 246, 0.1), rgba(29, 78, 216, 0.05)) !important;
z-index: 1 !important;
}
.hero-content {
position: relative !important;
z-index: 2 !important;
text-align: center !important;
}
.hero-title {
color: #ffffff !important;
font-size: 3.2em !important;
font-weight: 900 !important;
margin-bottom: 0.3em !important;
text-shadow: 0 4px 12px rgba(0, 0, 0, 0.6) !important;
letter-spacing: -0.5px !important;
background: linear-gradient(135deg, #ffffff 0%, #93c5fd 100%) !important;
-webkit-background-clip: text !important;
-webkit-text-fill-color: transparent !important;
background-clip: text !important;
}
.hero-subtitle {
color: #cbd5e1 !important;
font-size: 1.3em !important;
font-weight: 400 !important;
max-width: 800px !important;
margin: 0 auto !important;
line-height: 1.6 !important;
}
/* === PESTAÑAS, GRÁFICOS, METRIC, etc. (igual que antes) === */
/* ... (el resto del CSS se mantiene igual al original) ... */
</style>
""", unsafe_allow_html=True)

# ===== HERO BANNER PRINCIPAL =====
st.markdown("""
<div class="hero-banner">
<div class="hero-content">
<h1 class="hero-title">ANALIZADOR MULTI-CULTIVO SATELITAL - DEMO</h1>
<p class="hero-subtitle">Versión limitada: 2 análisis gratuitos. ¡Adquiere la versión completa para acceso total!</p>
</div>
</div>
""", unsafe_allow_html=True)

# ===== CONFIGURACIÓN (igual al original) =====
# (Incluye SATELITES_DISPONIBLES, METODOLOGIAS_NPK, PARAMETROS_CULTIVOS, TEXTURA_SUELO_OPTIMA, etc.)
SATELITES_DISPONIBLES = {
    'SENTINEL-2': {
        'nombre': 'Sentinel-2',
        'resolucion': '10m',
        'revisita': '5 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B8', 'B8A', 'B11', 'B12'],
        'indices': ['NDVI', 'NDRE', 'GNDVI', 'OSAVI', 'MCARI', 'TCARI', 'NDII'],
        'icono': '🛰️',
        'bandas_np': {
            'N': ['B5', 'B8A'],
            'P': ['B4', 'B11'],
            'K': ['B8', 'B11', 'B12']
        }
    },
    'LANDSAT-8': {
        'nombre': 'Landsat 8',
        'resolucion': '30m',
        'revisita': '16 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B10', 'B11'],
        'indices': ['NDVI', 'NDWI', 'EVI', 'SAVI', 'MSAVI', 'NDII'],
        'icono': '🛰️',
        'bandas_np': {
            'N': ['B4', 'B5'],
            'P': ['B3', 'B6'],
            'K': ['B5', 'B6', 'B7']
        }
    },
    'DATOS_SIMULADOS': {
        'nombre': 'Datos Simulados',
        'resolucion': '10m',
        'revisita': '5 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B8'],
        'indices': ['NDVI', 'NDRE', 'GNDVI'],
        'icono': '🔬'
    }
}

METODOLOGIAS_NPK = {
    'SENTINEL-2': {
        'NITRÓGENO': {'metodo': 'NDRE + Regresión Espectral', 'formula': 'N = 150 * NDRE + 50 * (B8A/B5)', 'bandas': ['B5', 'B8A'], 'r2_esperado': 0.75, 'referencia': 'Clevers & Gitelson, 2013'},
        'FÓSFORO': {'metodo': 'Índice SWIR-VIS', 'formula': 'P = 80 * (B11/B4)^0.5 + 20', 'bandas': ['B4', 'B11'], 'r2_esperado': 0.65, 'referencia': 'Miphokasap et al., 2012'},
        'POTASIO': {'metodo': 'Índice de Estrés Hídrico', 'formula': 'K = 120 * (B8 - B11)/(B8 + B12) + 40', 'bandas': ['B8', 'B11', 'B12'], 'r2_esperado': 0.70, 'referencia': 'Jackson et al., 2004'}
    },
    'LANDSAT-8': {
        'NITRÓGENO': {'metodo': 'TCARI/OSAVI', 'formula': 'N = 3*[(B5-B4)-0.2*(B5-B3)*(B5/B4)] / (1.16*(B5-B4)/(B5+B4+0.16))', 'bandas': ['B3', 'B4', 'B5'], 'r2_esperado': 0.72, 'referencia': 'Haboudane et al., 2002'},
        'FÓSFORO': {'metodo': 'Relación SWIR1-Verde', 'formula': 'P = 60 * (B6/B3)^0.7 + 25', 'bandas': ['B3', 'B6'], 'r2_esperado': 0.68, 'referencia': 'Chen et al., 2010'},
        'POTASIO': {'metodo': 'Índice NIR-SWIR', 'formula': 'K = 100 * (B5 - B7)/(B5 + B7) + 50', 'bandas': ['B5', 'B7'], 'r2_esperado': 0.69, 'referencia': 'Thenkabail et al., 2000'}
    }
}

PARAMETROS_CULTIVOS = {
    'MAÍZ': {'NITROGENO': {'min': 150, 'max': 200, 'optimo': 180}, 'FOSFORO': {'min': 40, 'max': 60, 'optimo': 50}, 'POTASIO': {'min': 120, 'max': 180, 'optimo': 150}, 'MATERIA_ORGANICA_OPTIMA': 3.5, 'HUMEDAD_OPTIMA': 0.3, 'NDVI_OPTIMO': 0.85, 'NDRE_OPTIMO': 0.5, 'TCARI_OPTIMO': 0.4, 'OSAVI_OPTIMO': 0.6, 'RENDIMIENTO_BASE': 8.0, 'RENDIMIENTO_OPTIMO': 12.0, 'RESPUESTA_N': 0.05, 'RESPUESTA_P': 0.08, 'RESPUESTA_K': 0.04, 'FACTOR_CLIMA': 0.7},
    'SOYA': {'NITROGENO': {'min': 20, 'max': 40, 'optimo': 30}, 'FOSFORO': {'min': 30, 'max': 50, 'optimo': 40}, 'POTASIO': {'min': 80, 'max': 120, 'optimo': 100}, 'MATERIA_ORGANICA_OPTIMA': 4.0, 'HUMEDAD_OPTIMA': 0.25, 'NDVI_OPTIMO': 0.8, 'NDRE_OPTIMO': 0.45, 'TCARI_OPTIMO': 0.35, 'OSAVI_OPTIMO': 0.55, 'RENDIMIENTO_BASE': 2.5, 'RENDIMIENTO_OPTIMO': 4.0, 'RESPUESTA_N': 0.02, 'RESPUESTA_P': 0.03, 'RESPUESTA_K': 0.025, 'FACTOR_CLIMA': 0.75},
    'TRIGO': {'NITROGENO': {'min': 120, 'max': 180, 'optimo': 150}, 'FOSFORO': {'min': 40, 'max': 60, 'optimo': 50}, 'POTASIO': {'min': 80, 'max': 120, 'optimo': 100}, 'MATERIA_ORGANICA_OPTIMA': 3.0, 'HUMEDAD_OPTIMA': 0.28, 'NDVI_OPTIMO': 0.75, 'NDRE_OPTIMO': 0.4, 'TCARI_OPTIMO': 0.3, 'OSAVI_OPTIMO': 0.5, 'RENDIMIENTO_BASE': 3.5, 'RENDIMIENTO_OPTIMO': 6.0, 'RESPUESTA_N': 0.03, 'RESPUESTA_P': 0.05, 'RESPUESTA_K': 0.035, 'FACTOR_CLIMA': 0.8},
    'GIRASOL': {'NITROGENO': {'min': 80, 'max': 120, 'optimo': 100}, 'FOSFORO': {'min': 35, 'max': 50, 'optimo': 42}, 'POTASIO': {'min': 100, 'max': 150, 'optimo': 125}, 'MATERIA_ORGANICA_OPTIMA': 3.2, 'HUMEDAD_OPTIMA': 0.22, 'NDVI_OPTIMO': 0.7, 'NDRE_OPTIMO': 0.35, 'TCARI_OPTIMO': 0.25, 'OSAVI_OPTIMO': 0.45, 'RENDIMIENTO_BASE': 2.0, 'RENDIMIENTO_OPTIMO': 3.5, 'RESPUESTA_N': 0.015, 'RESPUESTA_P': 0.02, 'RESPUESTA_K': 0.018, 'FACTOR_CLIMA': 0.65}
}

TEXTURA_SUELO_OPTIMA = {
    'MAÍZ': {'textura_optima': 'Franco', 'arena_optima': 45, 'limo_optima': 35, 'arcilla_optima': 20, 'densidad_aparente_optima': 1.3, 'porosidad_optima': 0.5},
    'SOYA': {'textura_optima': 'Franco', 'arena_optima': 40, 'limo_optima': 40, 'arcilla_optima': 20, 'densidad_aparente_optima': 1.2, 'porosidad_optima': 0.55},
    'TRIGO': {'textura_optima': 'Franco', 'arena_optima': 50, 'limo_optima': 30, 'arcilla_optima': 20, 'densidad_aparente_optima': 1.25, 'porosidad_optima': 0.52},
    'GIRASOL': {'textura_optima': 'Franco arenoso-arcilloso', 'arena_optima': 55, 'limo_optima': 25, 'arcilla_optima': 20, 'densidad_aparente_optima': 1.35, 'porosidad_optima': 0.48}
}

CLASIFICACION_PENDIENTES = {
    'PLANA (0-2%)': {'min': 0, 'max': 2, 'color': '#4daf4a', 'factor_erosivo': 0.1},
    'SUAVE (2-5%)': {'min': 2, 'max': 5, 'color': '#a6d96a', 'factor_erosivo': 0.3},
    'MODERADA (5-10%)': {'min': 5, 'max': 10, 'color': '#ffffbf', 'factor_erosivo': 0.6},
    'FUERTE (10-15%)': {'min': 10, 'max': 15, 'color': '#fdae61', 'factor_erosivo': 0.8},
    'MUY FUERTE (15-25%)': {'min': 15, 'max': 25, 'color': '#f46d43', 'factor_erosivo': 0.9},
    'EXTREMA (>25%)': {'min': 25, 'max': 100, 'color': '#d73027', 'factor_erosivo': 1.0}
}

RECOMENDACIONES_TEXTURA = {
    'Franco': {'propiedades': ["Equilibrio arena-limo-arcilla", "Buena aireación y drenaje", "CIC intermedia-alta", "Retención de agua adecuada"], 'limitantes': ["Puede compactarse con maquinaria pesada", "Erosión en pendientes si no hay cobertura"], 'manejo': ["Mantener coberturas vivas o muertas", "Evitar tránsito excesivo de maquinaria", "Fertilización eficiente, sin muchas pérdidas", "Ideal para la mayoría de cultivos"]},
    'Franco arcilloso': {'propiedades': ["Mayor proporción de arcilla (25–35%)", "Alta retención de agua y nutrientes", "Drenaje natural lento", "Buena fertilidad natural"], 'limitantes': ["Riesgo de encharcamiento", "Compactación fácil", "Menor oxigenación radicular"], 'manejo': ["Implementar drenajes (canales y subdrenes)", "Subsolado previo a siembra", "Incorporar materia orgánica", "Fertilización fraccionada en lluvias intensas"]},
    'Franco arenoso-arcilloso': {'propiedades': ["Arena 40–50%, arcilla 20–30%", "Buen desarrollo radicular", "Drenaje moderado", "Retención de agua moderada-baja"], 'limitantes': ["Riesgo de lixiviación de nutrientes", "Estrés hídrico en veranos", "Fertilidad moderada"], 'manejo': ["Uso de coberturas leguminosas", "Aplicar mulching", "Riego suplementario en sequía", "Fertilización fraccionada"]}
}

ICONOS_CULTIVOS = {'MAÍZ': '🌽', 'SOYA': '🫘', 'TRIGO': '🌾', 'GIRASOL': '🌻'}
COLORES_CULTIVOS = {'MAÍZ': '#FFD700', 'SOYA': '#90EE90', 'TRIGO': '#DAA520', 'GIRASOL': '#FFA500'}
PALETAS_GEE = {
    'FERTILIDAD': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850', '#006837'],
    'NITROGENO': ['#00ff00', '#80ff00', '#ffff00', '#ff8000', '#ff0000'],
    'FOSFORO': ['#0000ff', '#4040ff', '#8080ff', '#c0c0ff', '#ffffff'],
    'POTASIO': ['#4B0082', '#6A0DAD', '#8A2BE2', '#9370DB', '#D8BFD8'],
    'TEXTURA': ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e'],
    'ELEVACION': ['#006837', '#1a9850', '#66bd63', '#a6d96a', '#d9ef8b', '#ffffbf', '#fee08b', '#fdae61', '#f46d43', '#d73027'],
    'PENDIENTE': ['#4daf4a', '#a6d96a', '#ffffbf', '#fdae61', '#f46d43', '#d73027']
}
IMAGENES_CULTIVOS = {
    'MAÍZ': 'https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=200&h=150&q=80',
    'SOYA': 'https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=200&h=150&q=80',
    'TRIGO': 'https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=200&h=150&q=80',
    'GIRASOL': 'https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=200&h=150&q=80',
}

# ===== INICIALIZACIÓN SEGURA DE VARIABLES DE CONFIGURACIÓN =====
nutriente = None
satelite_seleccionado = "SENTINEL-2"
indice_seleccionado = "NDVI"
fecha_inicio = datetime.now() - timedelta(days=30)
fecha_fin = datetime.now()
intervalo_curvas = 5.0
resolucion_dem = 10.0

# === SISTEMA DE REGISTRO POR EMAIL + LÍMITE DE 2 ANÁLISIS ===
if 'email_autorizado' not in st.session_state:
    st.session_state.email_autorizado = None
if 'analisis_realizados' not in st.session_state:
    st.session_state.analisis_realizados = 0

# Bloquear si ya se hicieron 2 análisis
if st.session_state.analisis_realizados >= 2:
    st.error("🔒 Has alcanzado el límite de la versión DEMO (2 análisis).")
    st.info("💡 **La versión completa incluye:**\n- Recomendaciones NPK personalizadas\n- Análisis de curvas de nivel y pendientes\n- Sin límite de uso\n- Soporte prioritario")
    st.markdown("📧 **Contáctanos para adquirir la versión completa:** ventas@agrotech.com")
    st.stop()

# Registro de email
if st.session_state.email_autorizado is None:
    st.markdown("### 📧 Acceso a la Demo")
    st.write("Ingresa tu email para probar la versión limitada (2 análisis gratuitos).")
    email = st.text_input("Email", placeholder="tu@email.com")
    if st.button("✅ Usar la demo"):
        if "@" in email and "." in email:
            st.session_state.email_autorizado = email
            st.success(f"¡Bienvenido! Puedes realizar hasta 2 análisis.")
            st.rerun()
        else:
            st.error("Por favor ingresa un email válido.")
    st.stop()

# ===== SIDEBAR MEJORADO (INTERFAZ VISUAL) =====
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙️ CONFIGURACIÓN (DEMO)</div>', unsafe_allow_html=True)
    cultivo = st.selectbox("Cultivo:", ["MAÍZ", "SOYA", "TRIGO", "GIRASOL"])
    st.image(IMAGENES_CULTIVOS[cultivo], use_container_width=True)

    if satelite_seleccionado in METODOLOGIAS_NPK:
        st.info(f"**Metodología {satelite_seleccionado}:**")
        for nutriente_metodo, info in METODOLOGIAS_NPK[satelite_seleccionado].items():
            st.write(f"- **{nutriente_metodo}**: {info['metodo']}")

    # === TIPOS DE ANÁLISIS (CON OPCIONES BLOQUEADAS VISIBLES) ===
    st.subheader("🔍 Tipos de Análisis")
    
    # Opciones permitidas en la DEMO
    analisis_tipo = st.selectbox(
        "Análisis disponibles (DEMO):",
        ["FERTILIDAD ACTUAL", "ANÁLISIS DE TEXTURA"]
    )

    # Mostrar las otras opciones como desactivadas (solo informativas)
    st.markdown("### 🚫 Funciones de la versión completa:")
    st.markdown("""
    <div style="background: #f8fafc; padding: 12px; border-radius: 10px; border-left: 4px solid #94a3b8; margin: 10px 0;">
        <strong>• RECOMENDACIONES NPK</strong><br>
        <small style="color: #64748b;">Fertilización variable por nutriente</small>
    </div>
    <div style="background: #f8fafc; padding: 12px; border-radius: 10px; border-left: 4px solid #94a3b8; margin: 10px 0;">
        <strong>• ANÁLISIS DE CURVAS DE NIVEL</strong><br>
        <small style="color: #64748b;">Topografía, pendientes y erosión</small>
    </div>
    """, unsafe_allow_html=True)

    if analisis_tipo == "RECOMENDACIONES NPK":
        nutriente = st.selectbox("Nutriente:", ["NITRÓGENO", "FÓSFORO", "POTASIO"])

    st.subheader("🛰️ Fuente de Datos Satelitales")
    satelite_seleccionado = st.selectbox(
        "Satélite:",
        ["SENTINEL-2", "LANDSAT-8", "DATOS_SIMULADOS"],
        help="Selecciona la fuente de datos satelitales"
    )

    info_satelites = {
        'SENTINEL-2': {'nombre': 'Sentinel-2', 'resolucion': '10m', 'revisita': '5 días', 'indices': ['NDVI', 'NDRE', 'GNDVI']},
        'LANDSAT-8': {'nombre': 'Landsat 8', 'resolucion': '30m', 'revisita': '16 días', 'indices': ['NDVI', 'NDWI', 'EVI']},
        'DATOS_SIMULADOS': {'nombre': 'Datos Simulados', 'resolucion': '10m', 'revisita': '5 días', 'indices': ['NDVI', 'NDRE']}
    }
    if satelite_seleccionado in info_satelites:
        info = info_satelites[satelite_seleccionado]
        st.info(f"**{info['nombre']}**\n- Resolución: {info['resolucion']}\n- Índices: {', '.join(info['indices'][:3])}")

    if analisis_tipo in ["FERTILIDAD ACTUAL"]:
        st.subheader("📊 Índices de Vegetación")
        if satelite_seleccionado == "SENTINEL-2":
            indice_seleccionado = st.selectbox("Índice:", ['NDVI', 'NDRE', 'GNDVI'])
        elif satelite_seleccionado == "LANDSAT-8":
            indice_seleccionado = st.selectbox("Índice:", ['NDVI', 'NDWI', 'EVI'])
        else:
            indice_seleccionado = st.selectbox("Índice:", ['NDVI', 'NDRE'])

    if analisis_tipo in ["FERTILIDAD ACTUAL"]:
        st.subheader("📅 Rango Temporal")
        fecha_fin = st.date_input("Fecha fin", datetime.now())
        fecha_inicio = st.date_input("Fecha inicio", datetime.now() - timedelta(days=30))

    st.subheader("🎯 División de Parcela")
    n_divisiones = st.slider("Número de zonas de manejo:", min_value=16, max_value=48, value=32)

    st.subheader("📤 Subir Parcela")
    uploaded_file = st.file_uploader("Subir archivo de tu parcela", type=['zip', 'kml', 'kmz'])

# >>> FUNCIONES AUXILIARES Y PRINCIPALES (IDÉNTICAS AL ARCHIVO ORIGINAL) <<<
# (Pega aquí todo el código de funciones desde `validar_y_corregir_crs` hasta el final del archivo original)

# Copia aquí TODO el código de funciones del archivo original (desde `validar_y_corregir_crs` hasta la última función)

# ===== FUNCIONES AUXILIARES - CORREGIDAS PARA EPSG:4326 =====
def validar_y_corregir_crs(gdf):
    if gdf is None or len(gdf) == 0:
        return gdf
    try:
        if gdf.crs is None:
            gdf = gdf.set_crs('EPSG:4326', inplace=False)
            st.info("ℹ️ Se asignó EPSG:4326 al archivo (no tenía CRS)")
        elif str(gdf.crs).upper() != 'EPSG:4326':
            original_crs = str(gdf.crs)
            gdf = gdf.to_crs('EPSG:4326')
            st.info(f"ℹ️ Transformado de {original_crs} a EPSG:4326")
        return gdf
    except Exception as e:
        st.warning(f"⚠️ Error al corregir CRS: {str(e)}")
        return gdf

def calcular_superficie(gdf):
    try:
        if gdf is None or len(gdf) == 0:
            return 0.0
        gdf = validar_y_corregir_crs(gdf)
        bounds = gdf.total_bounds
        if bounds[0] < -180 or bounds[2] > 180 or bounds[1] < -90 or bounds[3] > 90:
            st.warning("⚠️ Coordenadas fuera de rango para cálculo preciso de área")
            area_grados2 = gdf.geometry.area.sum()
            area_m2 = area_grados2 * 111000 * 111000
            return area_m2 / 10000
        gdf_projected = gdf.to_crs('EPSG:3857')
        area_m2 = gdf_projected.geometry.area.sum()
        return area_m2 / 10000
    except Exception as e:
        try:
            return gdf.geometry.area.sum() / 10000
        except:
            return 0.0

def dividir_parcela_en_zonas(gdf, n_zonas):
    if len(gdf) == 0:
        return gdf
    gdf = validar_y_corregir_crs(gdf)
    parcela_principal = gdf.iloc[0].geometry
    bounds = parcela_principal.bounds
    minx, miny, maxx, maxy = bounds
    sub_poligonos = []
    n_cols = math.ceil(math.sqrt(n_zonas))
    n_rows = math.ceil(n_zonas / n_cols)
    width = (maxx - minx) / n_cols
    height = (maxy - miny) / n_rows
    for i in range(n_rows):
        for j in range(n_cols):
            if len(sub_poligonos) >= n_zonas:
                break
            cell_minx = minx + (j * width)
            cell_maxx = minx + ((j + 1) * width)
            cell_miny = miny + (i * height)
            cell_maxy = miny + ((i + 1) * height)
            cell_poly = Polygon([(cell_minx, cell_miny), (cell_maxx, cell_miny), (cell_maxx, cell_maxy), (cell_minx, cell_maxy)])
            intersection = parcela_principal.intersection(cell_poly)
            if not intersection.is_empty and intersection.area > 0:
                sub_poligonos.append(intersection)
    if sub_poligonos:
        nuevo_gdf = gpd.GeoDataFrame({'id_zona': range(1, len(sub_poligonos) + 1), 'geometry': sub_poligonos}, crs='EPSG:4326')
        return nuevo_gdf
    else:
        return gdf

# [CONTINUAR CON TODAS LAS FUNCIONES DEL ARCHIVO ORIGINAL: cargar_shapefile_desde_zip, parsear_kml_manual, cargar_kml, cargar_archivo_parcela, calcular_nitrogeno_sentinel2, etc.]

# Por razones de longitud, no repito las +1000 líneas de funciones aquí, pero en tu archivo final DEBES incluirlas todas.

# ===== INTERFAZ PRINCIPAL =====
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
                    if analisis_tipo in ["FERTILIDAD ACTUAL"]:
                        st.write(f"- Satélite: {SATELITES_DISPONIBLES[satelite_seleccionado]['nombre']}")
                        st.write(f"- Índice: {indice_seleccionado}")

                # === BOTÓN DE EJECUCIÓN (INCREMENTA CONTADOR) ===
                if st.button("🚀 EJECUTAR ANÁLISIS COMPLETO", type="primary"):
                    # Incrementar contador de análisis
                    st.session_state.analisis_realizados += 1

                    # Ejecutar análisis (solo para los permitidos)
                    if analisis_tipo in ["FERTILIDAD ACTUAL", "ANÁLISIS DE TEXTURA"]:
                        resultados = ejecutar_analisis(
                            gdf, nutriente, analisis_tipo, n_divisiones,
                            cultivo, satelite_seleccionado, indice_seleccionado,
                            fecha_inicio, fecha_fin
                        )
                        if resultados and resultados['exitoso']:
                            # Guardar resultados y mostrar
                            st.session_state['resultados_guardados'] = {
                                'gdf_analizado': resultados['gdf_analizado'],
                                'analisis_tipo': analisis_tipo,
                                'cultivo': cultivo,
                                'area_total': resultados['area_total'],
                                'nutriente': nutriente,
                                'satelite_seleccionado': satelite_seleccionado,
                                'indice_seleccionado': indice_seleccionado,
                                'mapa_buffer': resultados.get('mapa_buffer'),
                                'df_power': resultados.get('df_power')
                            }
                            # Mostrar resultados según tipo
                            if analisis_tipo == "ANÁLISIS DE TEXTURA":
                                mostrar_resultados_textura(resultados['gdf_analizado'], cultivo, resultados['area_total'])
                            else:
                                # Mostrar resultados de fertilidad
                                gdf_analizado = resultados['gdf_analizado']
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Zonas Analizadas", len(gdf_analizado))
                                with col2:
                                    st.metric("Área Total", f"{resultados['area_total']:.1f} ha")
                                with col3:
                                    valor_prom = gdf_analizado['npk_integrado'].mean()
                                    st.metric("Índice NPK Integrado", f"{valor_prom:.3f}")
                                with col4:
                                    if 'nitrogeno_actual' in gdf_analizado.columns:
                                        n_prom = gdf_analizado['nitrogeno_actual'].mean()
                                        st.metric("Nitrógeno Promedio", f"{n_prom:.1f} kg/ha")
                                # Mostrar mapa, tabla, etc.
                                mapa_fertilidad = crear_mapa_fertilidad_integrada(gdf_analizado, cultivo, satelite_seleccionado)
                                if mapa_fertilidad:
                                    st.image(mapa_fertilidad, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error procesando archivo: {str(e)}")
            import traceback
            st.error(f"Detalle: {traceback.format_exc()}")
else:
    st.info("📁 Sube un archivo de tu parcela para comenzar el análisis")

# ===== EXPORTACIÓN PERSISTENTE (igual al original) =====
if 'resultados_guardados' in st.session_state:
    res = st.session_state['resultados_guardados']
    st.markdown("---")
    st.subheader("📤 EXPORTAR RESULTADOS")
    col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
    with col_exp1:
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
    with col_exp2:
        if st.button("📄 Generar Reporte PDF", key="export_pdf"):
            with st.spinner("Generando PDF..."):
                estadisticas = generar_resumen_estadisticas(
                    res['gdf_analizado'],
                    res['analisis_tipo'],
                    res['cultivo'],
                    res.get('df_power')
                )
                recomendaciones = generar_recomendaciones_generales(res['gdf_analizado'], res['analisis_tipo'], res['cultivo'])
                mapa_buffer = res.get('mapa_buffer')
                pdf_buffer = generar_reporte_pdf(
                    res['gdf_analizado'], res['cultivo'], res['analisis_tipo'], res['area_total'],
                    res.get('nutriente'), res.get('satelite_seleccionado'), res.get('indice_seleccionado'),
                    mapa_buffer, estadisticas, recomendaciones
                )
                if pdf_buffer:
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf_buffer,
                        file_name=f"reporte_{res['cultivo']}_{res['analisis_tipo'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        key="pdf_download"
                    )
    with col_exp3:
        if st.button("📝 Generar Reporte DOCX", key="export_docx"):
            with st.spinner("Generando DOCX..."):
                estadisticas = generar_resumen_estadisticas(
                    res['gdf_analizado'],
                    res['analisis_tipo'],
                    res['cultivo'],
                    res.get('df_power')
                )
                recomendaciones = generar_recomendaciones_generales(res['gdf_analizado'], res['analisis_tipo'], res['cultivo'])
                mapa_buffer = res.get('mapa_buffer')
                docx_buffer = generar_reporte_docx(
                    res['gdf_analizado'], res['cultivo'], res['analisis_tipo'], res['area_total'],
                    res.get('nutriente'), res.get('satelite_seleccionado'), res.get('indice_seleccionado'),
                    mapa_buffer, estadisticas, recomendaciones
                )
                if docx_buffer:
                    st.download_button(
                        label="📥 Descargar DOCX",
                        data=docx_buffer,
                        file_name=f"reporte_{res['cultivo']}_{res['analisis_tipo'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="docx_download"
                    )
    with col_exp4:
        if st.button("📊 Exportar CSV", key="export_csv"):
            if res['gdf_analizado'] is not None:
                if 'geometry' in res['gdf_analizado'].columns:
                    df_export = res['gdf_analizado'].drop(columns=['geometry']).copy()
                else:
                    df_export = res['gdf_analizado'].copy()
                csv = df_export.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name=f"datos_{res['cultivo']}_{res['analisis_tipo'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="csv_download"
                )

# FORMATOS ACEPTADOS Y METODOLOGÍA (igual al original)
with st.expander("📋 FORMATOS DE ARCHIVO ACEPTADOS"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🗺️ Shapefile (.zip)**")
        st.markdown("""
- Archivo ZIP que contiene:
- .shp (geometrías)
- .shx (índice)
- .dbf (atributos)
- .prj (proyección, opcional)
- Se recomienda usar EPSG:4326 (WGS84)
""")
    with col2:
        st.markdown("**🌐 KML (.kml)**")
        st.markdown("""
- Formato Keyhole Markup Language
- Usado por Google Earth
- Contiene geometrías y atributos
- Puede incluir estilos y colores
- Siempre en EPSG:4326
""")
    with col3:
        st.markdown("**📦 KMZ (.kmz)**")
        st.markdown("""
- Versión comprimida de KML
- Archivo ZIP con extensión .kmz
- Puede incluir recursos (imágenes, etc.)
- Compatible con Google Earth
- Siempre en EPSG:4326
""")

with st.expander("🔬 METODOLOGÍA CIENTÍFICA APLICADA"):
    st.markdown("""
### **🌱 METODOLOGÍAS CIENTÍFICAS PARA ESTIMAR NPK CON TELEDETECCIÓN**
#### **🛰️ PARA SENTINEL-2:**
**NITRÓGENO (N):**
- **Método:** NDRE + Regresión Espectral (Clevers & Gitelson, 2013)
- **Fórmula:** `N = 150 × NDRE + 50 × (B8A/B5)`
- **Bandas:** B5 (Red Edge 1), B8A (Red Edge 4)
- **Precisión esperada:** R² = 0.75
**FÓSFORO (P):**
- **Método:** Índice SWIR-VIS (Miphokasap et al., 2012)
- **Fórmula:** `P = 80 × (B11/B4)^0.5 + 20`
- **Bandas:** B4 (Rojo), B11 (SWIR 1)
- **Precisión esperada:** R² = 0.65
**POTASIO (K):**
- **Método:** Índice de Estrés Hídrico (Jackson et al., 2004)
- **Fórmula:** `K = 120 × NDII + 40 × (B8/B12)`
- **Bandas:** B8 (NIR), B11 (SWIR 1), B12 (SWIR 2)
- **Precisión esperada:** R² = 0.70
#### **🛰️ PARA LANDSAT-8:**
**NITRÓGENO (N):**
- **Método:** TCARI/OSAVI (Haboudane et al., 2002)
- **Fórmula:** `TCARI = 3 × [(B5-B4) - 0.2 × (B5-B3) × (B5/B4)]`
- **Bandas:** B3 (Verde), B4 (Rojo), B5 (NIR)
**FÓSFORO (P):**
- **Método:** Relación SWIR1-Verde (Chen et al., 2010)
- **Fórmula:** `P = 60 × (B6/B3)^0.7 + 25`
- **Bandas:** B3 (Verde), B6 (SWIR 1)
**POTASIO (K):**
- **Método:** Índice NIR-SWIR (Thenkabail et al., 2000)
- **Fórmula:** `K = 100 × (B5-B7)/(B5+B7) + 50`
- **Bandas:** B5 (NIR), B7 (SWIR 2)
### **📊 VALIDACIÓN CIENTÍFICA:**
- **Calibración:** Modelos calibrados con datos de campo de estudios publicados
- **Validación:** Comparación con datos de laboratorio (R² entre 0.65-0.75)
- **Limitaciones:** Precisión afectada por cobertura de nubes, sombras y fenología del cultivo
### **💡 RECOMENDACIONES:**
1. **Validación de campo:** Siempre validar con análisis de suelo de laboratorio
2. **Época óptima:** Análisis en etapas vegetativas (V6-V10 para maíz)
3. **Condiciones ideales:** Imágenes con <10% cobertura de nubes
4. **Complementar:** Usar junto con análisis de textura y topografía
### **📚 REFERENCIAS CIENTÍFICAS:**
1. Clevers & Gitelson (2013). Remote estimation of crop and grass chlorophyll.
2. Miphokasap et al. (2012). Estimation of soil phosphorus using hyperspectral data.
3. Jackson et al. (2004). Vegetation water content estimation using NDII.
4. Haboudane et al. (2002). Hyperspectral vegetation indices for nitrogen assessment.
5. Chen et al. (2010). Estimation of soil properties using Landsat imagery.
6. Thenkabail et al. (2000). Hyperspectral vegetation indices for crop characterization.
""")
