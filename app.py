import streamlit as st
import json
import tempfile
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw

# Configuración de la página
st.set_page_config(
    page_title="Analizador de Fertilidad",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🌱 Analizador de Fertilidad")
st.markdown("---")

# Inicializar session state
if 'drawn_polygons' not in st.session_state:
    st.session_state.drawn_polygons = []
if 'current_polygon' not in st.session_state:
    st.session_state.current_polygon = None

# Sidebar para controles
with st.sidebar:
    st.header("Configuración")
    
    # Selección de cultivo
    crop = st.selectbox(
        "Selecciona el cultivo:",
        ["Trigo", "Maíz", "Soja", "Sorgo", "Girasol"]
    )
    
    # Selección de mapa base
    base_map = st.selectbox(
        "Mapa Base:",
        ["ESRI Satélite", "ESRI Topográfico", "OpenStreetMap"]
    )
    
    st.markdown("---")
    st.header("Acciones")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Limpiar Mapa", use_container_width=True):
            st.session_state.drawn_polygons = []
            st.session_state.current_polygon = None
            st.rerun()
    
    with col2:
        analyze_disabled = st.session_state.current_polygon is None
        if st.button("📊 Analizar", use_container_width=True, disabled=analyze_disabled):
            st.session_state.analyze_clicked = True

# Función para crear el mapa
def create_map(base_map_choice):
    # Coordenadas iniciales (Argentina)
    m = folium.Map(
        location=[-34.6037, -58.3816],
        zoom_start=13,
        control_scale=True
    )
    
    # Capas base
    if base_map_choice == "ESRI Satélite":
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='ESRI Satélite',
            overlay=False,
            control=True
        ).add_to(m)
    elif base_map_choice == "ESRI Topográfico":
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='ESRI Topográfico',
            overlay=False,
            control=True
        ).add_to(m)
    else:  # OpenStreetMap
        folium.TileLayer(
            tiles='OpenStreetMap',
            attr='OpenStreetMap',
            name='OpenStreetMap',
            overlay=False,
            control=True
        ).add_to(m)
    
    # Plugin de dibujo
    draw_options = {
        'position': 'topleft',
        'draw': {
            'polygon': {
                'allowIntersection': False,
                'showArea': True,
                'shapeOptions': {
                    'color': '#4CAF50',
                    'fillColor': '#4CAF50',
                    'fillOpacity': 0.2,
                    'weight': 3
                }
            },
            'polyline': False,
            'rectangle': False,
            'circle': False,
            'marker': False,
            'circlemarker': False
        },
        'edit': False
    }
    
    draw = Draw(export=False, **draw_options)
    draw.add_to(m)
    
    return m

# Función para simular análisis
def simulate_fertility_analysis(crop):
    import random
    
    crop_requirements = {
        'Trigo': {'n': 'alto', 'p': 'medio', 'k': 'medio', 'ph_optimo': 6.0},
        'Maíz': {'n': 'muy_alto', 'p': 'alto', 'k': 'alto', 'ph_optimo': 6.5},
        'Soja': {'n': 'medio', 'p': 'alto', 'k': 'medio', 'ph_optimo': 6.8},
        'Sorgo': {'n': 'medio', 'p': 'medio', 'k': 'alto', 'ph_optimo': 6.2},
        'Girasol': {'n': 'bajo', 'p': 'medio', 'k': 'medio', 'ph_optimo': 6.5}
    }
    
    # Calcular área aproximada
    area_hectares = round(random.uniform(5, 50), 2)
    
    requirements = crop_requirements.get(crop, crop_requirements['Trigo'])
    
    return {
        'cultivo': crop,
        'area_hectareas': area_hectares,
        'parametros': {
            'nitrogeno': random.choice(['bajo', 'medio', 'alto']),
            'fosforo': random.choice(['bajo', 'medio', 'alto']),
            'potasio': random.choice(['bajo', 'medio', 'alto']),
            'ph': round(random.uniform(5.0, 7.5), 1),
            'materia_organica': round(random.uniform(1.0, 4.0), 1)
        },
        'requerimientos': requirements,
        'recomendaciones': generar_recomendaciones(crop)
    }

def generar_recomendaciones(crop):
    recomendaciones = {
        'Trigo': [
            "Aplicar fertilizante nitrogenado en pre-siembra",
            "Mantener pH alrededor de 6.0",
            "Controlar niveles de fósforo"
        ],
        'Maíz': [
            "Alta demanda de nitrógeno - fertilizar adecuadamente",
            "Asegurar buen drenaje del suelo",
            "Mantener niveles altos de potasio"
        ],
        'Soja': [
            "Inocular con rhizobium para fijación de nitrógeno",
            "Mantener niveles adecuados de fósforo",
            "Controlar pH para optimizar nodulación"
        ],
        'Sorgo': [
            "Moderada demanda de nutrientes",
            "Tolerante a suelos más secos",
            "Mantener niveles de potasio"
        ],
        'Girasol': [
            "Baja demanda de nitrógeno",
            "Sensible a excesos de agua",
            "Mantener pH neutro"
        ]
    }
    return recomendaciones.get(crop, [])

# Función para exportar GeoJSON
def export_geojson(polygon_data, crop):
    geojson = polygon_data.copy()
    geojson['properties'] = {
        'export_date': datetime.now().isoformat(),
        'crop': crop,
        'analyzed_by': 'Analizador de Fertilidad Streamlit'
    }
    return geojson

# Crear y mostrar el mapa
st.subheader("Mapa Interactivo")
st.markdown("Dibuja un polígono en el mapa usando la herramienta de dibujo (ícono de polígono en la esquina superior izquierda)")

# Crear el mapa
m = create_map(base_map)

# Mostrar el mapa y capturar interacciones
map_data = st_folium(
    m,
    width=1200,
    height=600,
    returned_objects=["last_active_drawing"]
)

# Procesar polígono dibujado
if map_data and map_data.get("last_active_drawing"):
    polygon_data = map_data["last_active_drawing"]
    st.session_state.current_polygon = polygon_data
    
    # Añadir a la lista si no existe
    if polygon_data not in st.session_state.drawn_polygons:
        st.session_state.drawn_polygons.append(polygon_data)
        
    # Mostrar información del área
    st.sidebar.success("✅ Polígono dibujado correctamente")
    
    # Calcular área aproximada (simulada)
    import random
    area_hectareas = round(random.uniform(5, 50), 2)
    st.sidebar.info(f"**Área aproximada:** {area_hectareas} hectáreas")

# Análisis de fertilidad
if (st.session_state.current_polygon is not None and 
    hasattr(st.session_state, 'analyze_clicked') and 
    st.session_state.analyze_clicked):
    
    with st.spinner("Analizando fertilidad..."):
        # Simular análisis
        analysis_result = simulate_fertility_analysis(crop)
    
    # Mostrar resultados
    st.markdown("---")
    st.subheader("📊 Resultados del Análisis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Información General**")
        st.info(f"**Cultivo:** {analysis_result['cultivo']}")
        st.info(f"**Área:** {analysis_result['area_hectareas']} hectáreas")
        
        st.markdown("**Parámetros del Suelo**")
        parametros = analysis_result['parametros']
        
        # Mostrar parámetros con indicadores de color
        for param, valor in parametros.items():
            if param in ['nitrogeno', 'fosforo', 'potasio']:
                if valor == 'bajo':
                    st.error(f"**{param.title()}:** {valor} ❌")
                elif valor == 'medio':
                    st.warning(f"**{param.title()}:** {valor} ⚠️")
                else:
                    st.success(f"**{param.title()}:** {valor} ✅")
            else:
                st.info(f"**{param.title()}:** {valor}")
    
    with col2:
        st.markdown("**Recomendaciones**")
        for i, recomendacion in enumerate(analysis_result['recomendaciones'], 1):
            st.write(f"{i}. {recomendacion}")
    
    # Botón de exportación
    st.markdown("---")
    st.subheader("💾 Exportar Datos")
    
    if st.button("📥 Exportar GeoJSON", key="export_btn"):
        geojson_data = export_geojson(st.session_state.current_polygon, crop)
        geojson_str = json.dumps(geojson_data, indent=2)
        
        st.download_button(
            label="Descargar Archivo GeoJSON",
            data=geojson_str,
            file_name=f"fertilidad_{crop}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson",
            mime="application/json",
            use_container_width=True
        )
    
    # Resetear el flag de análisis
    st.session_state.analyze_clicked = False

# Mensaje si no hay polígono
elif st.session_state.current_polygon is None:
    st.info("ℹ️ Dibuja un polígono en el mapa para comenzar el análisis")

# Información adicional
with st.expander("ℹ️ Instrucciones de uso"):
    st.markdown("""
    ### Cómo usar la aplicación:
    
    1. **Selecciona un cultivo** en el panel lateral
    2. **Dibuja un polígono** en el mapa usando la herramienta de dibujo (ícono de polígono en la esquina superior izquierda)
    3. **Haz clic en 'Analizar'** para obtener los resultados de fertilidad
    4. **Exporta los datos** en formato GeoJSON si lo necesitas
    
    ### Características:
    - Múltiples mapas base (ESRI Satélite, ESRI Topográfico, OpenStreetMap)
    - Análisis de fertilidad por cultivo específico
    - Exportación en formato GeoJSON estándar
    - Interfaz responsive y fácil de usar
    - Compatible con dispositivos móviles
    
    ### Cultivos soportados:
    - 🌾 Trigo
    - 🌽 Maíz  
    - 🫘 Soja
    - 🌾 Sorgo
    - 🌻 Girasol
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Analizador de Fertilidad - Desarrollado con Streamlit 🌱"
    "</div>",
    unsafe_allow_html=True
)
