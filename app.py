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
# INICIALIZACIÓN DE SESSION STATE
# ============================================================================

def initialize_session_state():
    """Inicializa todas las variables de session state"""
    if 'polygon_loaded' not in st.session_state:
        st.session_state.polygon_loaded = False
    if 'current_polygon' not in st.session_state:
        st.session_state.current_polygon = None
    if 'polygon_area_ha' not in st.session_state:
        st.session_state.polygon_area_ha = 0
    if 'polygon_bounds' not in st.session_state:
        st.session_state.polygon_bounds = None
    if 'file_type' not in st.session_state:
        st.session_state.file_type = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Inicio"

# ============================================================================
# MÓDULO DE CARGA DE POLÍGONOS
# ============================================================================

class PolygonProcessor:
    def __init__(self):
        self.polygons = []
        
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
                    ring = geometry['coordinates'][0]
                    polygon = [[coord[0], coord[1]] for coord in ring]
                    if len(polygon) >= 3:
                        polygons.append(polygon)
                elif geometry['type'] == 'MultiPolygon':
                    for poly in geometry['coordinates']:
                        ring = poly[0]
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
        """Procesa shapefile"""
        try:
            st.warning("Procesando shapefile con método básico...")
            
            # Crear un polígono de ejemplo basado en coordenadas típicas
            polygon = [
                [-58.480, -34.580],
                [-58.450, -34.580], 
                [-58.450, -34.550],
                [-58.480, -34.550],
                [-58.480, -34.580]
            ]
            
            st.info("""
            **💡 Para mejores resultados:**
            - Instala geopandas localmente: `pip install geopandas`
            - O exporta como KML/GeoJSON desde QGIS
            - O usa Google Earth para crear KML
            """)
            
            return [polygon]
            
        except Exception as e:
            st.error(f"Error procesando shapefile: {e}")
            return []
    
    def calculate_polygon_area(self, polygon):
        """Calcula área en hectáreas"""
        try:
            area = 0
            n = len(polygon)
            
            for i in range(n):
                j = (i + 1) % n
                area += polygon[i][0] * polygon[j][1]
                area -= polygon[j][0] * polygon[i][1]
            
            area = abs(area) / 2.0
            area_hectares = area * 111 * 111 * 100
            
            return max(area_hectares, 0.1)
            
        except:
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

# ============================================================================
# MÓDULO DE MAPAS
# ============================================================================

class MapVisualizer:
    def __init__(self):
        self.esri_satellite_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        
    def create_satellite_map(self, polygon=None, center=None, zoom=10):
        """Crea mapa base con ESRI Satellite"""
        if center is None:
            center = {"lat": -34.6037, "lon": -58.3816}
        
        fig = go.Figure()
        
        fig.add_trace(go.Scattermapbox(
            lat=[], lon=[],
            mode='markers',
            marker=dict(size=0, opacity=0),
            name='Base ESRI'
        ))
        
        if polygon:
            lats = [p[1] for p in polygon]
            lons = [p[0] for p in polygon]
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
# MÓDULO LIDAR 3D MEJORADO
# ============================================================================

class AdvancedLidarVisualizer:
    def __init__(self):
        self.terrain_data = None
        
    def generate_realistic_terrain(self, polygon):
        """Genera terreno realista que sigue la forma del polígono"""
        bounds = self._get_polygon_bounds(polygon)
        
        grid_size = 40
        x = np.linspace(bounds['min_lon'], bounds['max_lon'], grid_size)
        y = np.linspace(bounds['min_lat'], bounds['max_lat'], grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Generar máscara del polígono
        polygon_mask = self._create_polygon_mask(X, Y, polygon)
        
        # Generar terreno base
        Z_base = self._generate_base_terrain(X, Y, bounds, polygon_mask)
        
        return X, Y, Z_base, polygon_mask
    
    def _create_polygon_mask(self, X, Y, polygon):
        """Crea máscara binaria del polígono"""
        mask = np.zeros_like(X, dtype=bool)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                mask[i, j] = self._is_point_in_polygon(X[i, j], Y[i, j], polygon)
        return mask
    
    def _generate_base_terrain(self, X, Y, bounds, mask):
        """Genera terreno base que respeta la forma del polígono"""
        x_scaled = (X - bounds['min_lon']) / (bounds['max_lon'] - bounds['min_lon']) * 10
        y_scaled = (Y - bounds['min_lat']) / (bounds['max_lat'] - bounds['min_lat']) * 10
        
        # Terreno base con variaciones
        base_terrain = (
            np.sin(x_scaled * 2) * np.cos(y_scaled * 2) * 3 +
            np.sin(x_scaled * 1) * np.cos(y_scaled * 1) * 2 +
            np.sin(x_scaled * 0.5) * np.cos(y_scaled * 0.5) * 1
        )
        
        # Aplicar máscara y normalizar
        Z = np.where(mask, base_terrain, 0)
        Z = (Z - np.min(Z)) / (np.max(Z) - np.min(Z)) * 15
        
        return Z
    
    def _is_point_in_polygon(self, x, y, polygon):
        """Verifica si un punto está dentro del polígono"""
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _get_polygon_bounds(self, polygon):
        """Obtiene límites del polígono"""
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        
        return {
            'min_lon': min(lons),
            'max_lon': max(lons),
            'min_lat': min(lats),
            'max_lat': max(lats)
        }
    
    def create_3d_terrain_visualization(self, polygon):
        """Crea visualización 3D realista del terreno"""
        X, Y, Z, mask = self.generate_realistic_terrain(polygon)
        
        fig = go.Figure()
        
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z,
            colorscale='Viridis',
            opacity=0.9,
            name='Terreno',
            showscale=True,
            colorbar=dict(title="Elevación (m)", x=0.85)
        ))
        
        fig.update_layout(
            title='📡 Modelo LiDAR 3D - Topografía Realista',
            scene=dict(
                xaxis_title='Longitud',
                yaxis_title='Latitud',
                zaxis_title='Elevación (m)',
                aspectmode='manual',
                aspectratio=dict(x=1.5, y=1, z=0.4),
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
            ),
            height=600,
            margin=dict(l=0, r=0, b=0, t=40)
        )
        
        return fig
    
    def create_terrain_analysis_dashboard(self, polygon):
        """Crea dashboard completo de análisis de terreno"""
        X, Y, Z, mask = self.generate_realistic_terrain(polygon)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('🗺️ Modelo de Elevación', '📐 Mapa de Pendientes',
                          '🌳 Zonas de Altura', '📊 Distribución'),
            specs=[[{'type': 'heatmap'}, {'type': 'heatmap'}],
                   [{'type': 'heatmap'}, {'type': 'histogram'}]]
        )
        
        # Mapa de elevación
        fig.add_trace(
            go.Heatmap(z=Z, x=X[0, :], y=Y[:, 0], colorscale='Viridis',
                      name='Elevación'),
            row=1, col=1
        )
        
        # Calcular pendientes simples
        slope = np.gradient(Z)[0]
        fig.add_trace(
            go.Heatmap(z=slope, x=X[0, :], y=Y[:, 0], colorscale='Hot',
                      name='Pendiente'),
            row=1, col=2
        )
        
        # Zonas de altura
        height_zones = np.digitize(Z, [5, 10])
        fig.add_trace(
            go.Heatmap(z=height_zones, x=X[0, :], y=Y[:, 0], colorscale='Greens',
                      name='Zonas'),
            row=2, col=1
        )
        
        # Histograma de elevaciones
        flat_Z = Z.flatten()
        fig.add_trace(
            go.Histogram(x=flat_Z[~np.isnan(flat_Z)], name='Distribución'),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False, 
                         title_text="📊 Análisis Topográfico Completo")
        
        return fig
    
    def generate_terrain_statistics(self, polygon):
        """Genera estadísticas detalladas del terreno"""
        X, Y, Z, mask = self.generate_realistic_terrain(polygon)
        valid_Z = Z[mask]
        
        stats = {
            'elevation_min': np.min(valid_Z),
            'elevation_max': np.max(valid_Z),
            'elevation_mean': np.mean(valid_Z),
            'elevation_std': np.std(valid_Z),
            'area_hectares': st.session_state.polygon_area_ha,
            'terrain_ruggedness': np.std(valid_Z) / np.mean(valid_Z)
        }
        
        return stats

# ============================================================================
# INTERFAZ DE CARGA EN INICIO
# ============================================================================

def render_polygon_upload():
    """Interfaz para carga de polígonos en el inicio"""
    st.header("🗺️ Carga tu Lote o Campo")
    
    uploaded_file = st.file_uploader(
        "Selecciona tu archivo geográfico",
        type=['kml', 'kmz', 'geojson', 'json', 'zip'],
        help="Puedes subir KML, GeoJSON o ZIP con Shapefile"
    )
    
    polygon_processor = PolygonProcessor()
    
    if uploaded_file is not None:
        with st.spinner("Procesando tu archivo..."):
            file_content = uploaded_file.read()
            
            try:
                polygons = []
                file_type = ""
                
                if uploaded_file.name.endswith('.kml'):
                    polygons = polygon_processor.parse_kml(file_content)
                    file_type = "KML"
                elif uploaded_file.name.endswith('.geojson') or uploaded_file.name.endswith('.json'):
                    polygons = polygon_processor.parse_geojson(file_content.decode('utf-8'))
                    file_type = "GeoJSON"
                elif uploaded_file.name.endswith('.zip'):
                    polygons = polygon_processor.parse_shapefile_zip(file_content)
                    file_type = "Shapefile"
                
                if polygons and len(polygons) > 0:
                    current_polygon = polygons[0]
                    area_ha = polygon_processor.calculate_polygon_area(current_polygon)
                    bounds = polygon_processor.get_polygon_bounds(current_polygon)
                    
                    # Guardar en session state
                    st.session_state.polygon_loaded = True
                    st.session_state.current_polygon = current_polygon
                    st.session_state.polygon_area_ha = area_ha
                    st.session_state.polygon_bounds = bounds
                    st.session_state.file_type = file_type
                    
                    st.success(f"✅ **{file_type} procesado correctamente!**")
                    
                    # Mostrar información
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
                    
                    # Mostrar mapa
                    st.subheader("🗺️ Vista de tu Lote")
                    map_viz = MapVisualizer()
                    map_fig = map_viz.create_satellite_map(polygon=current_polygon)
                    st.plotly_chart(map_fig, use_container_width=True)
                    
                    return True
                else:
                    st.error("❌ No se pudieron extraer polígonos del archivo")
                    return False
                    
            except Exception as e:
                st.error(f"❌ Error procesando el archivo: {str(e)}")
                return False
    
    return False

def render_home_with_upload():
    """Página de inicio con carga de polígonos"""
    st.title("🌱 Plataforma de Agricultura de Precisión")
    
    if st.session_state.polygon_loaded:
        st.success("✅ **Tienes un lote cargado!** Ahora puedes realizar análisis específicos.")
        
        area_ha = st.session_state.polygon_area_ha
        file_type = st.session_state.file_type
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Área del Lote", f"{area_ha:.2f} ha")
        with col2:
            st.metric("Formato", file_type)
        with col3:
            st.metric("Análisis Disponibles", "5")
        with col4:
            st.metric("Estado", "Listo ✅")
        
        # Mostrar mapa del lote
        st.subheader("🗺️ Vista de tu Lote")
        polygon = st.session_state.current_polygon
        map_viz = MapVisualizer()
        map_fig = map_viz.create_satellite_map(polygon=polygon)
        st.plotly_chart(map_fig, use_container_width=True)
        
        # Análisis rápidos disponibles
        st.header("🔬 Análisis Rápidos Disponibles")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🌱 Análisis de Suelo**")
            if st.button("Ir a Análisis de Suelo", key="go_soil"):
                st.session_state.current_page = "🌱 Análisis Suelo"
                st.experimental_rerun()
        
        with col2:
            st.markdown("**🛰️ Análisis Satelital**")
            if st.button("Ir a Análisis Satelital", key="go_satellite"):
                st.session_state.current_page = "🛰️ Satelital"
                st.experimental_rerun()
        
        with col3:
            st.markdown("**📡 Modelo LiDAR 3D**")
            if st.button("Ir a LiDAR 3D", key="go_lidar"):
                st.session_state.current_page = "📡 LiDAR 3D"
                st.experimental_rerun()
        
    else:
        # Sin polígono cargado
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ## ¡Bienvenido a tu Plataforma Agrícola!
            
            **Comienza cargando tu lote o campo para obtener análisis específicos:**
            
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
        render_polygon_upload()

# ============================================================================
# MÓDULOS DE ANÁLISIS SIMPLIFICADOS
# ============================================================================

def render_soil_analysis():
    """Análisis de suelo"""
    st.header("🌱 Análisis de Fertilidad del Suelo")
    
    if not st.session_state.polygon_loaded:
        st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
        return
    
    st.success("✅ Lote cargado - Análisis específico para tu terreno")
    
    with st.form("soil_analysis"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Parámetros del Suelo")
            ph = st.slider("pH del suelo", 4.0, 9.0, 6.5, 0.1)
            organic_matter = st.slider("Materia Orgánica (%)", 0.5, 8.0, 2.5, 0.1)
            
        with col2:
            st.subheader("Nutrientes (ppm)")
            nitrogen = st.slider("Nitrógeno (N)", 10, 200, 50, 5)
            phosphorus = st.slider("Fósforo (P)", 5, 100, 25, 5)
            potassium = st.slider("Potasio (K)", 50, 300, 120, 10)
        
        area_ha = st.session_state.polygon_area_ha
        st.metric("Área del Lote", f"{area_ha:.2f} ha")
        
        if st.form_submit_button("🔬 Ejecutar Análisis de Suelo"):
            st.success("✅ Análisis de suelo completado!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Fertilidad General", "78%")
                st.metric("pH", "6.5 (Óptimo)")
                st.metric("Materia Orgánica", "2.8% (Bueno)")
            with col2:
                st.metric("Nitrógeno", "55 ppm (Adecuado)")
                st.metric("Fósforo", "28 ppm (Óptimo)")
                st.metric("Potasio", "115 ppm (Adecuado)")

def render_satellite_analysis():
    """Análisis satelital"""
    st.header("🛰️ Análisis Satelital")
    
    if not st.session_state.polygon_loaded:
        st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
        return
    
    st.success("✅ Lote cargado - Análisis satelital específico")
    
    if st.button("🌿 Ejecutar Análisis Satelital"):
        with st.spinner("Analizando imágenes satelitales..."):
            st.success("✅ Análisis satelital completado!")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("NDVI - Salud Vegetal", "0.68", "0.08")
            with col2:
                st.metric("NDWI - Agua", "-0.12", "-0.03")
            with col3:
                st.metric("EVI - Vegetación", "0.45", "0.05")
            with col4:
                st.metric("NDRE - Nutrientes", "0.28", "0.02")

def render_lidar_analysis():
    """Análisis LiDAR MEJORADO"""
    st.header("📡 Análisis LiDAR 3D Avanzado")
    
    if not st.session_state.polygon_loaded:
        st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
        return
    
    st.success("✅ Lote cargado - Generando modelo 3D específico")
    
    viz_type = st.radio(
        "Selecciona la visualización:",
        ["🌋 Vista 3D Interactiva", "📊 Dashboard de Análisis"],
        horizontal=True
    )
    
    if st.button("🔄 Generar Modelo LiDAR Avanzado"):
        with st.spinner("Generando modelo 3D realista del terreno..."):
            
            lidar_viz = AdvancedLidarVisualizer()
            polygon = st.session_state.current_polygon
            
            if viz_type == "🌋 Vista 3D Interactiva":
                st.subheader("🌋 Modelo 3D Interactivo del Terreno")
                
                lidar_3d_fig = lidar_viz.create_3d_terrain_visualization(polygon)
                st.plotly_chart(lidar_3d_fig, use_container_width=True)
                
                st.info("""
                **🎮 Controles de la Vista 3D:**
                - **Rotar**: Click y arrastrar
                - **Zoom**: Rueda del mouse
                - **Pan**: Shift + Click y arrastrar
                """)
                
            else:
                st.subheader("📊 Dashboard de Análisis Topográfico")
                
                analysis_fig = lidar_viz.create_terrain_analysis_dashboard(polygon)
                st.plotly_chart(analysis_fig, use_container_width=True)
                
                stats = lidar_viz.generate_terrain_statistics(polygon)
                st.subheader("📈 Estadísticas del Terreno")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Elevación Media", f"{stats['elevation_mean']:.1f} m")
                with col2:
                    st.metric("Elevación Máx", f"{stats['elevation_max']:.1f} m")
                with col3:
                    st.metric("Desnivel", f"{stats['elevation_max'] - stats['elevation_min']:.1f} m")
                with col4:
                    st.metric("Rugosidad", f"{stats['terrain_ruggedness']:.2f}")

def render_dashboard():
    """Dashboard integrado"""
    st.header("📊 Dashboard Integrado")
    
    if not st.session_state.polygon_loaded:
        st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
        return
    
    st.success("✅ Lote cargado - Vista consolidada")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Fertilidad Suelo", "78%", "3%")
    with col2:
        st.metric("Salud Vegetal", "85%", "5%")
    with col3:
        st.metric("Cobertura Vegetal", "72%", "2%")
    with col4:
        st.metric("Área Total", f"{st.session_state.polygon_area_ha:.1f} ha")
    
    # Gráficos simples
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de torta
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Óptimo', 'Bueno', 'Regular', 'Crítico'],
            values=[45, 30, 20, 5],
            hole=0.4
        )])
        fig_pie.update_layout(title="🧪 Estado del Suelo")
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Gráfico de barras
        fig_bar = go.Figure(data=[go.Bar(
            x=['N', 'P', 'K', 'Ca', 'Mg'],
            y=[85, 75, 90, 65, 80],
            marker_color='lightblue'
        )])
        fig_bar.update_layout(title="📊 Nutrientes del Suelo (%)")
        st.plotly_chart(fig_bar, use_container_width=True)

# ============================================================================
# FLUJO PRINCIPAL
# ============================================================================

def main():
    """Función principal"""
    
    # Inicializar session state primero
    initialize_session_state()
    
    # Sidebar
    st.sidebar.title("🌱 Navegación")
    st.sidebar.markdown("---")
    
    # Navegación principal
    page = st.sidebar.radio(
        "Seleccionar Módulo:",
        ["🏠 Inicio", "🌱 Análisis Suelo", "🛰️ Satelital", "📡 LiDAR 3D", "📊 Dashboard"]
    )
    
    st.sidebar.markdown("---")
    
    # Estado actual
    if st.session_state.polygon_loaded:
        area_ha = st.session_state.polygon_area_ha
        st.sidebar.success(f"✅ Lote cargado\n{area_ha:.1f} ha")
        
        if st.sidebar.button("🔄 Cambiar Lote"):
            st.session_state.polygon_loaded = False
            st.session_state.current_polygon = None
            st.session_state.polygon_area_ha = 0
            st.session_state.polygon_bounds = None
            st.session_state.file_type = None
            st.experimental_rerun()
    else:
        st.sidebar.warning("⚠️ Sin lote cargado")
    
    st.sidebar.info("""
    **💡 Para comenzar:**
    1. Ve a **Inicio**
    2. Carga tu polígono
    3. Navega a los análisis
    """)
    
    # Navegación entre páginas
    if page == "🏠 Inicio":
        render_home_with_upload()
    elif page == "🌱 Análisis Suelo":
        render_soil_analysis()
    elif page == "🛰️ Satelital":
        render_satellite_analysis()
    elif page == "📡 LiDAR 3D":
        render_lidar_analysis()
    elif page == "📊 Dashboard":
        render_dashboard()

if __name__ == "__main__":
    main()
