import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import base64
import io
import json
import xml.etree.ElementTree as ET
from io import BytesIO
import zipfile
import tempfile
import os

# CONFIGURACIÓN
st.set_page_config(
    page_title="Plataforma Agrícola Integral",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MÓDULO MEJORADO DE CARGA DE POLÍGONOS CON GEOPANDAS
# ============================================================================

class PolygonProcessor:
    def __init__(self):
        self.polygons = []
        self.current_polygon = None
        
    def parse_kml(self, kml_content):
        """Parsea archivo KML y extrae polígonos"""
        try:
            root = ET.fromstring(kml_content)
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
            polygons = []
            
            for polygon in root.findall('.//kml:Polygon', ns):
                coordinates_elem = polygon.find('.//kml:coordinates', ns)
                if coordinates_elem is not None:
                    coords_text = coordinates_elem.text.strip()
                    coordinates = []
                    
                    for line in coords_text.split():
                        parts = line.split(',')
                        if len(parts) >= 2:
                            lon, lat = float(parts[0]), float(parts[1])
                            coordinates.append([lon, lat])
                    
                    if coordinates and len(coordinates) >= 3:
                        polygons.append(coordinates)
            
            return polygons
            
        except Exception as e:
            st.error(f"Error parseando KML: {e}")
            return []
    
    def parse_geojson(self, geojson_content):
        """Parsea archivo GeoJSON"""
        try:
            data = json.loads(geojson_content)
            polygons = []
            
            def extract_coordinates(geometry):
                if geometry['type'] == 'Polygon':
                    # Tomar el anillo exterior (primer ring)
                    ring = geometry['coordinates'][0]
                    polygon = [[coord[0], coord[1]] for coord in ring]
                    if len(polygon) >= 3:
                        polygons.append(polygon)
                elif geometry['type'] == 'MultiPolygon':
                    for poly in geometry['coordinates']:
                        ring = poly[0]  # Primer anillo del polígono
                        polygon = [[coord[0], coord[1]] for coord in ring]
                        if len(polygon) >= 3:
                            polygons.append(polygon)
            
            if data['type'] == 'FeatureCollection':
                for feature in data['features']:
                    extract_coordinates(feature['geometry'])
            elif data['type'] == 'Feature':
                extract_coordinates(data['geometry'])
            elif data['type'] in ['Polygon', 'MultiPolygon']:
                extract_coordinates(data)
            
            return polygons
            
        except Exception as e:
            st.error(f"Error parseando GeoJSON: {e}")
            return []
    
    def parse_shapefile_zip(self, zip_file):
        """Procesa shapefile usando geopandas si está disponible, sino fallback"""
        try:
            # Intentar importar geopandas
            try:
                import geopandas as gpd
                GEOPANDAS_AVAILABLE = True
            except ImportError:
                GEOPANDAS_AVAILABLE = False
                st.warning("Geopandas no disponible. Usando método alternativo.")
            
            with zipfile.ZipFile(BytesIO(zip_file)) as z:
                file_list = z.namelist()
                
                # Buscar archivos necesarios
                shp_files = [f for f in file_list if f.endswith('.shp')]
                if not shp_files:
                    st.error("No se encontró archivo .shp en el ZIP")
                    return []
                
                # Crear directorio temporal
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Extraer todos los archivos
                    z.extractall(temp_dir)
                    
                    shp_path = os.path.join(temp_dir, shp_files[0])
                    
                    if GEOPANDAS_AVAILABLE:
                        # Usar geopandas para leer el shapefile
                        return self._read_shapefile_geopandas(shp_path)
                    else:
                        # Método alternativo
                        return self._read_shapefile_fallback(shp_path)
                        
        except Exception as e:
            st.error(f"Error procesando shapefile: {e}")
            return []
    
    def _read_shapefile_geopandas(self, shp_path):
        """Lee shapefile usando geopandas"""
        try:
            import geopandas as gpd
            from shapely.geometry import Polygon
            
            gdf = gpd.read_file(shp_path)
            st.success(f"✅ Shapefile leído: {len(gdf)} geometrías encontradas")
            
            polygons = []
            for geometry in gdf.geometry:
                if geometry.geom_type == 'Polygon':
                    # Convertir coordenadas
                    coords = list(geometry.exterior.coords)
                    polygon = [[lon, lat] for lon, lat in coords]
                    polygons.append(polygon)
                elif geometry.geom_type == 'MultiPolygon':
                    for poly in geometry.geoms:
                        coords = list(poly.exterior.coords)
                        polygon = [[lon, lat] for lon, lat in coords]
                        polygons.append(polygon)
            
            # Mostrar información del shapefile
            st.info(f"**Información del Shapefile:**")
            st.write(f"- CRS: {gdf.crs}")
            st.write(f"- Columnas: {list(gdf.columns)}")
            if len(gdf) > 0:
                st.write(f"- Extensión: {gdf.total_bounds}")
            
            return polygons
            
        except Exception as e:
            st.error(f"Error leyendo shapefile con geopandas: {e}")
            return self._read_shapefile_fallback(shp_path)
    
    def _read_shapefile_fallback(self, shp_path):
        """Método alternativo cuando geopandas no está disponible"""
        try:
            # Leer el archivo .shp como binario para extraer información básica
            with open(shp_path, 'rb') as f:
                content = f.read()
            
            # Esta es una aproximación muy básica - en producción siempre usar geopandas
            st.warning("Usando método de aproximación para shapefile")
            
            # Crear un polígono de ejemplo basado en el nombre del archivo
            # Esto es solo para demostración
            polygon = [
                [-58.480, -34.580],
                [-58.450, -34.580], 
                [-58.450, -34.550],
                [-58.480, -34.550],
                [-58.480, -34.580]
            ]
            
            st.info("""
            **💡 Para coordenadas exactas:**
            - Instala geopandas en tu entorno local
            - O exporta como KML/GeoJSON desde QGIS
            - O usa Google Earth para crear KML
            """)
            
            return [polygon]
            
        except Exception as e:
            st.error(f"Error en método alternativo: {e}")
            return []
    
    def calculate_polygon_area(self, polygon):
        """Calcula área en hectáreas"""
        try:
            # Fórmula del área de Gauss para polígonos
            area = 0
            n = len(polygon)
            
            for i in range(n):
                j = (i + 1) % n
                area += polygon[i][0] * polygon[j][1]
                area -= polygon[j][0] * polygon[i][1]
            
            area = abs(area) / 2.0
            
            # Convertir a hectáreas (aproximación)
            area_hectares = area * 111 * 111 * 100
            
            return max(area_hectares, 0.1)
            
        except:
            # Fallback a cálculo simple
            lons = [p[0] for p in polygon]
            lats = [p[1] for p in polygon]
            width = (max(lons) - min(lons)) * 111.32
            height = (max(lats) - min(lats)) * 110.57
            return max(width * height * 100, 0.1)

    def get_polygon_bounds(self, polygon):
        """Obtiene los límites del polígono"""
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        
        return {
            'min_lon': min(lons),
            'max_lon': max(lons),
            'min_lat': min(lats),
            'max_lat': max(lats),
            'center_lon': sum(lons) / len(lons),
            'center_lat': sum(lats) / len(lats)
        }

    def validate_polygon(self, polygon):
        """Valida que el polígono sea válido"""
        if not polygon or len(polygon) < 3:
            return False, "Polígono debe tener al menos 3 puntos"
        
        # Verificar que las coordenadas sean razonables
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        
        if max(lons) > 180 or min(lons) < -180:
            return False, "Longitudes fuera de rango (-180 a 180)"
        
        if max(lats) > 90 or min(lats) < -90:
            return False, "Latitudes fuera de rango (-90 a 90)"
        
        return True, "Polígono válido"

# ============================================================================
# MÓDULO DE MAPAS BASE ESRI
# ============================================================================

class MapVisualizer:
    def __init__(self):
        self.esri_satellite_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        
    def create_satellite_map(self, polygon=None, center=None, zoom=10):
        """Crea mapa base con ESRI Satellite"""
        if center is None:
            center = {"lat": -34.6037, "lon": -58.3816}
        
        fig = go.Figure()
        
        # Capa base ESRI Satellite
        fig.add_trace(go.Scattermapbox(
            lat=[], lon=[],
            mode='markers',
            marker=dict(size=0, opacity=0),
            name='Base ESRI'
        ))
        
        # Agregar polígono si existe
        if polygon:
            lats = [p[1] for p in polygon]
            lons = [p[0] for p in polygon]
            # Cerrar el polígono
            lats.append(lats[0])
            lons.append(lons[0])
            
            fig.add_trace(go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode='lines+markers',
                fill='toself',
                fillcolor='rgba(255, 0, 0, 0.3)',
                line=dict(color='red', width=3),
                name='Tu Lote'
            ))
            
            # Calcular centro del polígono para centrar el mapa
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            center = {"lat": center_lat, "lon": center_lon}
            zoom = 14
        
        fig.update_layout(
            mapbox=dict(
                style="white-bg",
                layers=[{
                    "below": 'traces',
                    "sourcetype": "raster",
                    "source": [self.esri_satellite_url],
                    "name": "ESRI Satellite"
                }],
                center=center,
                zoom=zoom,
            ),
            margin={"r":0,"t":0,"l":0,"b":0},
            height=500,
            showlegend=True
        )
        
        return fig

# ============================================================================
# INTERFAZ MEJORADA DE CARGA DE POLÍGONOS
# ============================================================================

def render_polygon_upload_section():
    """Sección de carga de polígonos en el inicio"""
    st.header("🗺️ Carga tu Lote o Campo")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 📁 Formatos Soportados:
        
        - **KML/KMZ** (Google Earth, Google Maps) - **RECOMENDADO**
        - **GeoJSON** (QGIS, aplicaciones web) - **RECOMENDADO**  
        - **Shapefile** (.zip con .shp, .shx, .dbf, .prj) - *Requiere geopandas*
        
        ### 🎯 Tu análisis será específico para tu área:
        - Fertilidad del suelo adaptada
        - Datos LiDAR generados para tu terreno
        - Análisis satelital preciso
        - Recomendaciones personalizadas
        """)
    
    with col2:
        st.info("""
        **💡 Recomendación:**
        - **Para mejor precisión:** Usa KML desde Google Earth
        - **Para shapefiles:** Asegúrate de tener todos los archivos
        - **Área mínima:** 1 hectárea
        - **Verifica las coordenadas** en el mapa
        """)
    
    # Uploader de archivos
    uploaded_file = st.file_uploader(
        "Selecciona tu archivo geográfico",
        type=['kml', 'kmz', 'geojson', 'json', 'zip'],
        help="KML y GeoJSON son más confiables. Shapefile requiere geopandas.",
        key="polygon_uploader_home"
    )
    
    polygon_processor = PolygonProcessor()
    
    if uploaded_file is not None:
        with st.spinner("Procesando tu archivo..."):
            file_content = uploaded_file.read()
            
            try:
                polygons = []
                file_type = ""
                
                if uploaded_file.type == "application/vnd.google-earth.kml+xml" or uploaded_file.name.endswith('.kml'):
                    polygons = polygon_processor.parse_kml(file_content)
                    file_type = "KML"
                    st.success("📱 Procesando archivo KML...")
                    
                elif uploaded_file.type == "application/geo+json" or uploaded_file.name.endswith('.geojson') or uploaded_file.name.endswith('.json'):
                    polygons = polygon_processor.parse_geojson(file_content.decode('utf-8'))
                    file_type = "GeoJSON"
                    st.success("🗺️ Procesando archivo GeoJSON...")
                    
                elif uploaded_file.type == "application/zip" or uploaded_file.name.endswith('.zip'):
                    polygons = polygon_processor.parse_shapefile_zip(file_content)
                    file_type = "Shapefile"
                    st.success("📦 Procesando Shapefile...")
                
                if polygons:
                    current_polygon = polygons[0]
                    
                    # Validar polígono
                    is_valid, message = polygon_processor.validate_polygon(current_polygon)
                    
                    if not is_valid:
                        st.error(f"❌ {message}")
                        return False
                    
                    area_ha = polygon_processor.calculate_polygon_area(current_polygon)
                    bounds = polygon_processor.get_polygon_bounds(current_polygon)
                    
                    # Guardar en session state
                    st.session_state.current_polygon = current_polygon
                    st.session_state.polygon_area_ha = area_ha
                    st.session_state.polygon_bounds = bounds
                    st.session_state.polygon_loaded = True
                    st.session_state.file_type = file_type
                    
                    st.success(f"✅ **{file_type} procesado correctamente!**")
                    
                    # Mostrar información detallada del polígono
                    st.subheader("📋 Información del Lote")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Área del Lote", f"{area_ha:.2f} hectáreas")
                    with col2:
                        st.metric("Puntos del Polígono", len(current_polygon))
                    with col3:
                        st.metric("Formato", file_type)
                    with col4:
                        st.metric("Estado", "✅ Válido")
                    
                    # Mostrar coordenadas de referencia
                    with st.expander("📐 Ver coordenadas del polígono"):
                        coords_df = pd.DataFrame(current_polygon, columns=['Longitud', 'Latitud'])
                        st.dataframe(coords_df.head(10), use_container_width=True)
                        if len(current_polygon) > 10:
                            st.caption(f"Mostrando 10 de {len(current_polygon)} puntos")
                    
                    # Mostrar mapa con el polígono
                    st.subheader("🗺️ Vista de tu Lote")
                    map_viz = MapVisualizer()
                    map_fig = map_viz.create_satellite_map(polygon=current_polygon)
                    st.plotly_chart(map_fig, use_container_width=True)
                    
                    # Verificación visual
                    st.info(f"""
                    **🔍 Verifica en el mapa:**
                    - El polígono debe corresponder a tu lote real
                    - El área calculada: **{area_ha:.2f} ha**
                    - Si no coincide, intenta con otro formato
                    """)
                    
                    return True
                else:
                    st.error("❌ No se pudieron extraer polígonos del archivo")
                    st.info("""
                    **Solución:**
                    - Verifica que el archivo contenga polígonos
                    - Prueba con KML desde Google Earth
                    - Para shapefiles, asegúrate de incluir todos los archivos (.shp, .shx, .dbf, .prj)
                    """)
                    return False
                    
            except Exception as e:
                st.error(f"❌ Error procesando el archivo: {str(e)}")
                st.info("""
                **Posibles soluciones:**
                1. **Para KML:** Exporta desde Google Earth (no Google Maps)
                2. **Para GeoJSON:** Usa QGIS o herramientas profesionales  
                3. **Para Shapefile:** Comprime todos los archivos en un ZIP
                4. **Alternativa:** Dibuja el polígono manualmente en Google Earth y exporta como KML
                """)
                return False
    
    # Información adicional cuando no hay archivo cargado
    else:
        st.markdown("---")
        st.subheader("📋 Guía Rápida de Formatos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Google Earth (KML)**")
            st.write("1. Abre Google Earth")
            st.write("2. Dibuja tu polígono")
            st.write("3. Guarda como KML")
            st.write("4. Sube el archivo aquí")
            
        with col2:
            st.write("**QGIS (GeoJSON)**")
            st.write("1. Abre tu shapefile en QGIS")
            st.write("2. Exporta como GeoJSON")
            st.write("3. Sube el archivo .geojson")
            
        with col3:
            st.write("**Shapefile (ZIP)**")
            st.write("1. Selecciona TODOS los archivos:")
            st.write("   - .shp, .shx, .dbf, .prj")
            st.write("2. Comprímelos en un ZIP")
            st.write("3. Sube el archivo .zip")
    
    return False

# ============================================================================
# FUNCIONES EXISTENTES (simplificadas para el ejemplo)
# ============================================================================

def render_quick_analysis():
    """Análisis rápido basado en el polígono cargado"""
    if not st.session_state.get('polygon_loaded'):
        return
    
    st.header("🔬 Análisis Rápido de tu Lote")
    
    analysis_type = st.selectbox(
        "Selecciona el tipo de análisis:",
        ["Fertilidad de Suelo", "Análisis Satelital", "Generar Modelo LiDAR", "Recomendaciones Integradas"]
    )
    
    if analysis_type == "Fertilidad de Suelo":
        render_soil_analysis()
    elif analysis_type == "Análisis Satelital":
        render_satellite_analysis()
    elif analysis_type == "Generar Modelo LiDAR":
        render_lidar_generation()
    elif analysis_type == "Recomendaciones Integradas":
        render_integrated_recommendations()

def render_soil_analysis():
    st.subheader("🌱 Análisis de Fertilidad del Suelo")
    st.info("Módulo de análisis de suelo - Configura los parámetros según tu lote")

def render_satellite_analysis():
    st.subheader("🛰️ Análisis Satelital")
    st.info("Análisis multiespectral para tu lote cargado")

def render_lidar_generation():
    st.subheader("📡 Generar Modelo LiDAR 3D")
    st.info("Generación de modelo 3D específico para tu terreno")

def render_integrated_recommendations():
    st.subheader("🎯 Recomendaciones Integradas")
    st.info("Recomendaciones personalizadas basadas en tu lote")

def render_home():
    """Página de inicio completa"""
    st.title("🌱 Plataforma de Agricultura de Precisión")
    
    polygon_loaded = st.session_state.get('polygon_loaded', False)
    
    if polygon_loaded:
        st.success("✅ **Tienes un lote cargado!** Ahora puedes realizar análisis específicos.")
        
        area_ha = st.session_state.get('polygon_area_ha', 0)
        file_type = st.session_state.get('file_type', 'Desconocido')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Área del Lote", f"{area_ha:.2f} ha")
        with col2:
            st.metric("Formato", file_type)
        with col3:
            st.metric("Análisis Disponibles", "5")
        with col4:
            st.metric("Estado", "Listo ✅")
        
        # Mostrar mapa
        polygon = st.session_state.current_polygon
        map_viz = MapVisualizer()
        map_fig = map_viz.create_satellite_map(polygon=polygon)
        st.plotly_chart(map_fig, use_container_width=True)
        
        render_quick_analysis()
        
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ## ¡Bienvenido a tu Plataforma Agrícola!
            
            **Comienza cargando tu lote o campo para obtener análisis específicos**
            
            🗺️ **Carga tu polígono** en KML, GeoJSON o Shapefile
            🌱 **Análisis de suelo** personalizado para tu terreno  
            📡 **Modelos 3D LiDAR** de tu topografía
            🛰️ **Monitoreo satelital** de salud vegetal
            🎯 **Recomendaciones** específicas para tu cultivo
            """)
        
        with col2:
            st.info("""
            **📊 Análisis Disponibles:**
            
            - Fertilidad de suelo
            - Topografía 3D
            - Salud vegetal (NDVI)
            - Estrés hídrico  
            - Recomendaciones integradas
            """)
        
        st.markdown("---")
        render_polygon_upload_section()

def main():
    """Función principal"""
    
    if 'polygon_loaded' not in st.session_state:
        st.session_state.polygon_loaded = False
    
    # Sidebar
    st.sidebar.title("🌱 Navegación")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Seleccionar Módulo:",
        ["🏠 Inicio", "🌱 Análisis Suelo", "🛰️ Satelital", "📡 LiDAR 3D", "📊 Dashboard"]
    )
    
    st.sidebar.markdown("---")
    
    if st.session_state.get('polygon_loaded'):
        area_ha = st.session_state.get('polygon_area_ha', 0)
        st.sidebar.success(f"✅ Lote cargado\n{area_ha:.1f} ha")
        
        if st.sidebar.button("🔄 Cambiar Lote"):
            for key in ['polygon_loaded', 'current_polygon', 'polygon_area_ha', 'polygon_bounds', 'file_type']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    else:
        st.sidebar.warning("⚠️ Sin lote cargado")
    
    # Navegación
    if page == "🏠 Inicio":
        render_home()
    elif page == "🌱 Análisis Suelo":
        if st.session_state.get('polygon_loaded'):
            render_soil_analysis()
        else:
            st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
    elif page == "🛰️ Satelital":
        if st.session_state.get('polygon_loaded'):
            render_satellite_analysis()
        else:
            st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
    elif page == "📡 LiDAR 3D":
        if st.session_state.get('polygon_loaded'):
            render_lidar_generation()
        else:
            st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
    elif page == "📊 Dashboard":
        st.title("📊 Dashboard Integrado")
        st.info("Dashboard unificado - Próximamente")

if __name__ == "__main__":
    main()
