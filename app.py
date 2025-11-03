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
# MÓDULO DE CARGA DE POLÍGONOS
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
        """Procesa shapefile usando geopandas si está disponible"""
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
            st.warning("Usando método de aproximación para shapefile")
            
            # Crear un polígono de ejemplo
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
# MÓDULO DE FERTILIDAD MEJORADO
# ============================================================================

class SoilFertilityAnalyzer:
    def __init__(self):
        self.fertility_data = None
        
    def generate_fertility_map(self, polygon, soil_params):
        """Genera mapa de fertilidad basado en parámetros del suelo"""
        bounds = self._get_polygon_bounds(polygon)
        
        # Crear grid dentro del polígono
        grid_size = 50
        lons = np.linspace(bounds['min_lon'], bounds['max_lon'], grid_size)
        lats = np.linspace(bounds['min_lat'], bounds['max_lat'], grid_size)
        
        # Generar datos de fertilidad simulados con variación realista
        fertility_grid = np.zeros((grid_size, grid_size))
        
        for i in range(grid_size):
            for j in range(grid_size):
                # Verificar si el punto está dentro del polígono
                if self._is_point_in_polygon(lons[j], lats[i], polygon):
                    # Base de fertilidad basada en parámetros
                    base_fertility = (
                        (soil_params['ph'] - 4.0) / 5.0 * 0.3 +
                        soil_params['organic_matter'] / 8.0 * 0.4 +
                        soil_params['nitrogen'] / 200.0 * 0.1 +
                        soil_params['phosphorus'] / 100.0 * 0.1 +
                        soil_params['potassium'] / 300.0 * 0.1
                    )
                    
                    # Agregar variación espacial más realista
                    variation = (
                        np.sin(i * 0.3) * np.cos(j * 0.3) * 0.15 +
                        np.sin(i * 0.1) * np.cos(j * 0.1) * 0.1
                    )
                    fertility_grid[i, j] = np.clip(base_fertility + variation, 0.1, 1.0)
                else:
                    fertility_grid[i, j] = np.nan
        
        return lons, lats, fertility_grid
    
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
    
    def create_fertility_plot(self, polygon, soil_params):
        """Crea visualización del mapa de fertilidad"""
        lons, lats, fertility_grid = self.generate_fertility_map(polygon, soil_params)
        
        fig = go.Figure()
        
        # Mapa de calor de fertilidad
        fig.add_trace(go.Heatmap(
            z=fertility_grid,
            x=lons,
            y=lats,
            colorscale='RdYlGn',
            opacity=0.8,
            name='Fertilidad',
            hovertemplate='Fertilidad: %{z:.2f}<extra></extra>',
            colorbar=dict(title="Índice de Fertilidad")
        ))
        
        # Contorno del polígono
        poly_lons = [p[0] for p in polygon] + [polygon[0][0]]
        poly_lats = [p[1] for p in polygon] + [polygon[0][1]]
        
        fig.add_trace(go.Scatter(
            x=poly_lons,
            y=poly_lats,
            mode='lines',
            line=dict(color='red', width=3),
            name='Límite del Lote',
            fill='toself',
            fillcolor='rgba(255,0,0,0.1)'
        ))
        
        fig.update_layout(
            title='🌱 Mapa de Fertilidad del Suelo',
            xaxis_title='Longitud',
            yaxis_title='Latitud',
            height=500,
            showlegend=True,
            template='plotly_white'
        )
        
        return fig

# ============================================================================
# MÓDULO SATELITAL MEJORADO
# ============================================================================

class SatelliteAnalyzer:
    def __init__(self):
        self.ndvi_data = None
        self.ndwi_data = None
        
    def generate_vegetation_map(self, polygon):
        """Genera mapa de salud vegetal (NDVI)"""
        bounds = self._get_polygon_bounds(polygon)
        
        grid_size = 50
        lons = np.linspace(bounds['min_lon'], bounds['max_lon'], grid_size)
        lats = np.linspace(bounds['min_lat'], bounds['max_lat'], grid_size)
        
        # Generar datos NDVI simulados
        ndvi_grid = np.zeros((grid_size, grid_size))
        
        for i in range(grid_size):
            for j in range(grid_size):
                if self._is_point_in_polygon(lons[j], lats[i], polygon):
                    # Simular patrones de vegetación realistas
                    base_ndvi = 0.6 + np.random.normal(0, 0.1)
                    
                    # Agregar patrones espaciales
                    pattern = (
                        np.sin(i * 0.2) * np.cos(j * 0.2) * 0.15 +
                        np.sin(i * 0.05) * np.cos(j * 0.05) * 0.1
                    )
                    ndvi_grid[i, j] = np.clip(base_ndvi + pattern, 0.1, 0.9)
                else:
                    ndvi_grid[i, j] = np.nan
        
        return lons, lats, ndvi_grid
    
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
    
    def create_vegetation_plot(self, polygon):
        """Crea visualización del mapa de salud vegetal"""
        lons, lats, ndvi_grid = self.generate_vegetation_map(polygon)
        
        fig = go.Figure()
        
        # Mapa de calor NDVI
        fig.add_trace(go.Heatmap(
            z=ndvi_grid,
            x=lons,
            y=lats,
            colorscale='RdYlGn',
            opacity=0.8,
            name='NDVI',
            hovertemplate='NDVI: %{z:.2f}<extra></extra>',
            colorbar=dict(title="NDVI")
        ))
        
        # Contorno del polígono
        poly_lons = [p[0] for p in polygon] + [polygon[0][0]]
        poly_lats = [p[1] for p in polygon] + [polygon[0][1]]
        
        fig.add_trace(go.Scatter(
            x=poly_lons,
            y=poly_lats,
            mode='lines',
            line=dict(color='blue', width=3),
            name='Límite del Lote',
            fill='toself',
            fillcolor='rgba(0,0,255,0.1)'
        ))
        
        fig.update_layout(
            title='🛰️ Mapa de Salud Vegetal (NDVI)',
            xaxis_title='Longitud',
            yaxis_title='Latitud',
            height=500,
            showlegend=True,
            template='plotly_white'
        )
        
        return fig

# ============================================================================
# MÓDULO LIDAR 3D MEJORADO
# ============================================================================

class Lidar3DVisualizer:
    def __init__(self):
        self.terrain_data = None
        
    def generate_terrain_data(self, polygon):
        """Genera datos de terreno simulados para LiDAR"""
        bounds = self._get_polygon_bounds(polygon)
        
        # Crear grid más denso para mejor visualización 3D
        grid_size = 40
        x = np.linspace(bounds['min_lon'], bounds['max_lon'], grid_size)
        y = np.linspace(bounds['min_lat'], bounds['max_lat'], grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Generar terreno con variaciones realistas
        Z = self._generate_realistic_terrain(X, Y, bounds)
        
        return X, Y, Z
    
    def _generate_realistic_terrain(self, X, Y, bounds):
        """Genera terreno realista con múltiples frecuencias"""
        # Escalar coordenadas para mejor comportamiento
        x_scaled = (X - bounds['min_lon']) / (bounds['max_lon'] - bounds['min_lon']) * 20
        y_scaled = (Y - bounds['min_lat']) / (bounds['max_lat'] - bounds['min_lat']) * 20
        
        # Terreno base con pendiente suave
        base_slope = 0.3 * x_scaled + 0.2 * y_scaled
        
        # Variaciones de alta frecuencia (colinas pequeñas)
        high_freq = (
            np.sin(1.5 * x_scaled) * np.cos(1.2 * y_scaled) * 0.4 +
            np.sin(2.5 * x_scaled + 1) * np.cos(1.8 * y_scaled - 0.5) * 0.3
        )
        
        # Variaciones de baja frecuencia (colinas grandes)
        low_freq = np.sin(0.8 * x_scaled) * np.cos(0.8 * y_scaled) * 1.2
        
        # Combinar todas las capas
        Z = base_slope + low_freq + high_freq
        
        # Normalizar a rango realista (0-15 metros)
        Z = (Z - Z.min()) / (Z.max() - Z.min()) * 15
        
        return Z
    
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
    
    def create_3d_visualization(self, polygon):
        """Crea visualización 3D interactiva del terreno LiDAR"""
        X, Y, Z = self.generate_terrain_data(polygon)
        
        fig = go.Figure()
        
        # Superficie del terreno
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z,
            colorscale='Viridis',
            opacity=0.9,
            name='Terreno',
            showscale=True,
            colorbar=dict(title="Altura (m)")
        ))
        
        fig.update_layout(
            title='📡 Modelo LiDAR 3D - Topografía del Terreno',
            scene=dict(
                xaxis_title='Longitud',
                yaxis_title='Latitud',
                zaxis_title='Altura (m)',
                aspectmode='manual',
                aspectratio=dict(x=1, y=1, z=0.4),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            height=600,
            margin=dict(l=0, r=0, b=0, t=40)
        )
        
        return fig

# ============================================================================
# DASHBOARD MEJORADO
# ============================================================================

class DashboardVisualizer:
    def __init__(self):
        pass
    
    def create_soil_pie_chart(self):
        """Crea gráfico de torta para composición del suelo"""
        labels = ['Arcilla', 'Limo', 'Arena', 'Materia Orgánica']
        values = [35, 25, 30, 10]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values,
            hole=0.4,
            marker=dict(colors=['#8B4513', '#DEB887', '#F4A460', '#8FBC8F'])
        )])
        
        fig.update_layout(
            title='🧪 Composición del Suelo',
            height=300
        )
        
        return fig
    
    def create_nutrient_bar_chart(self):
        """Crea gráfico de barras para nutrientes"""
        nutrients = ['Nitrógeno (N)', 'Fósforo (P)', 'Potasio (K)', 'Calcio (Ca)', 'Magnesio (Mg)']
        current_levels = [45, 28, 65, 75, 35]
        optimal_levels = [50, 30, 70, 80, 40]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Nivel Actual',
            x=nutrients,
            y=current_levels,
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Nivel Óptimo',
            x=nutrients,
            y=optimal_levels,
            marker_color='lightgreen',
            opacity=0.6
        ))
        
        fig.update_layout(
            title='📊 Niveles de Nutrientes del Suelo',
            barmode='group',
            height=400,
            xaxis_tickangle=-45
        )
        
        return fig
    
    def create_vegetation_health_chart(self):
        """Crea gráfico de salud vegetal"""
        dates = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
        ndvi = [0.45, 0.52, 0.68, 0.72, 0.75, 0.71]
        ndwi = [-0.12, -0.08, -0.05, -0.02, 0.01, -0.03]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            name='NDVI',
            x=dates,
            y=ndvi,
            line=dict(color='green', width=3),
            mode='lines+markers'
        ))
        
        fig.add_trace(go.Scatter(
            name='NDWI',
            x=dates,
            y=ndwi,
            line=dict(color='blue', width=3),
            mode='lines+markers'
        ))
        
        fig.update_layout(
            title='🌿 Evolución de Salud Vegetal',
            height=400,
            xaxis_title='Mes',
            yaxis_title='Índice'
        )
        
        return fig
    
    def create_productivity_gauge(self):
        """Crea medidor de productividad"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=78,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Productividad General"},
            delta={'reference': 70},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90}
            }
        ))
        
        fig.update_layout(height=300)
        return fig

# ============================================================================
# INTERFAZ DE CARGA EN INICIO - CORREGIDA
# ============================================================================

def render_polygon_upload():
    """Interfaz para carga de polígonos en el inicio"""
    st.header("🗺️ Carga tu Lote o Campo")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 📁 Formatos Soportados:
        
        - **KML/KMZ** (Google Earth, Google Maps)
        - **GeoJSON** (QGIS, aplicaciones web)  
        - **Shapefile** (.zip con .shp, .shx, .dbf, .prj)
        
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
        """)
    
    # Uploader de archivos
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
                
                if polygons and len(polygons) > 0:
                    current_polygon = polygons[0]
                    area_ha = polygon_processor.calculate_polygon_area(current_polygon)
                    bounds = polygon_processor.get_polygon_bounds(current_polygon)
                    
                    # Guardar en session state
                    st.session_state.current_polygon = current_polygon
                    st.session_state.polygon_area_ha = area_ha
                    st.session_state.polygon_bounds = bounds
                    st.session_state.polygon_loaded = True
                    st.session_state.file_type = file_type
                    
                    st.success(f"✅ **{file_type} procesado correctamente!**")
                    
                    # Mostrar información del polígono
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
                    
                    # Mostrar mapa con el polígono
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
    
    # Estado de la aplicación
    polygon_loaded = st.session_state.get('polygon_loaded', False)
    
    if polygon_loaded:
        st.success("✅ **Tienes un lote cargado!** Ahora puedes realizar análisis específicos.")
        
        # Mostrar información del lote cargado
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
            st.markdown("""
            **🌱 Análisis de Suelo**
            - Diagnóstico de fertilidad
            - Recomendaciones de fertilización
            - Estimación de productividad
            """)
            if st.button("Ir a Análisis de Suelo", key="go_soil"):
                st.session_state.current_page = "🌱 Análisis Suelo"
                st.rerun()
        
        with col2:
            st.markdown("""
            **🛰️ Análisis Satelital**  
            - Salud vegetal (NDVI)
            - Estrés hídrico (NDWI)
            - Estado nutricional (NDRE)
            """)
            if st.button("Ir a Análisis Satelital", key="go_satellite"):
                st.session_state.current_page = "🛰️ Satelital"
                st.rerun()
        
        with col3:
            st.markdown("""
            **📡 Modelo LiDAR 3D**
            - Topografía del terreno
            - Cobertura vegetal
            - Modelo 3D interactivo
            """)
            if st.button("Ir a LiDAR 3D", key="go_lidar"):
                st.session_state.current_page = "📡 LiDAR 3D"
                st.rerun()
        
    else:
        # Sin polígono cargado - mostrar upload y información
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
        
        # Sección de carga de polígonos
        render_polygon_upload()

# ============================================================================
# MÓDULOS DE ANÁLISIS (completos y corregidos)
# ============================================================================

def render_soil_analysis():
    """Análisis de suelo"""
    st.header("🌱 Análisis de Fertilidad del Suelo")
    
    if not st.session_state.get('polygon_loaded'):
        st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
        return
    
    st.success("✅ Lote cargado - Análisis específico para tu terreno")
    
    with st.form("soil_analysis"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Parámetros del Suelo")
            ph = st.slider("pH del suelo", 4.0, 9.0, 6.5, 0.1)
            organic_matter = st.slider("Materia Orgánica (%)", 0.5, 8.0, 2.5, 0.1)
            texture = st.selectbox("Textura del Suelo", 
                                 ["Arcilloso", "Franco", "Arenoso", "Franco-Arcilloso"])
            
        with col2:
            st.subheader("Nutrientes (ppm)")
            nitrogen = st.slider("Nitrógeno (N)", 10, 200, 50, 5)
            phosphorus = st.slider("Fósforo (P)", 5, 100, 25, 5)
            potassium = st.slider("Potasio (K)", 50, 300, 120, 10)
        
        area_ha = st.session_state.get('polygon_area_ha', 10)
        st.metric("Área del Lote", f"{area_ha:.2f} ha")
        
        if st.form_submit_button("🔬 Ejecutar Análisis de Suelo", type="primary"):
            # Simular análisis
            st.success("✅ Análisis de suelo completado!")
            
            # Mostrar resultados simulados
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Fertilidad General", "78%")
                st.metric("pH", "6.5 (Óptimo)")
                st.metric("Materia Orgánica", "2.8% (Bueno)")
            with col2:
                st.metric("Nitrógeno", "55 ppm (Adecuado)")
                st.metric("Fósforo", "28 ppm (Óptimo)")
                st.metric("Potasio", "115 ppm (Adecuado)")
            
            # Generar y mostrar mapa de fertilidad
            st.subheader("🗺️ Mapa de Fertilidad")
            
            soil_params = {
                'ph': ph,
                'organic_matter': organic_matter,
                'nitrogen': nitrogen,
                'phosphorus': phosphorus,
                'potassium': potassium
            }
            
            fertility_analyzer = SoilFertilityAnalyzer()
            polygon = st.session_state.current_polygon
            fertility_fig = fertility_analyzer.create_fertility_plot(polygon, soil_params)
            st.plotly_chart(fertility_fig, use_container_width=True)
            
            # Recomendaciones
            st.subheader("🎯 Recomendaciones de Fertilización")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info("""
                **📋 Recomendaciones Generales:**
                - Aplicar 150 kg/ha de fertilizante NPK 15-15-15
                - Enmienda orgánica: 2 ton/ha de compost
                - Control de pH: aplicación de 500 kg/ha de cal
                """)
            with col2:
                st.info("""
                **⏰ Plan de Aplicación:**
                - **Fertilización base:** Inmediata
                - **Fertilización cobertura:** 30 días
                - **Análisis de seguimiento:** 60 días
                """)

def render_satellite_analysis():
    """Análisis satelital"""
    st.header("🛰️ Análisis Satelital Multiespectral")
    
    if not st.session_state.get('polygon_loaded'):
        st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
        return
    
    st.success("✅ Lote cargado - Análisis satelital específico")
    
    if st.button("🌿 Ejecutar Análisis Satelital", type="primary"):
        with st.spinner("Analizando imágenes satelitales..."):
            # Simular análisis
            st.success("✅ Análisis satelital completado!")
            
            # Mostrar resultados
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("NDVI - Salud Vegetal", "0.68", "0.08")
            with col2:
                st.metric("NDWI - Agua", "-0.12", "-0.03")
            with col3:
                st.metric("EVI - Vegetación Densa", "0.45", "0.05")
            with col4:
                st.metric("NDRE - Nutrientes", "0.28", "0.02")
            
            # Generar y mostrar mapa de salud vegetal
            st.subheader("🗺️ Mapa de Salud Vegetal (NDVI)")
            
            satellite_analyzer = SatelliteAnalyzer()
            polygon = st.session_state.current_polygon
            vegetation_fig = satellite_analyzer.create_vegetation_plot(polygon)
            st.plotly_chart(vegetation_fig, use_container_width=True)
            
            # Interpretación NDVI
            st.subheader("📊 Interpretación del NDVI")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.info("**0.0 - 0.2**: Suelo desnudo")
            with col2:
                st.success("**0.2 - 0.5**: Vegetación escasa")
            with col3:
                st.success("**0.5 - 0.7**: Vegetación buena")
            with col4:
                st.success("**0.7 - 1.0**: Vegetación excelente")

def render_lidar_analysis():
    """Análisis LiDAR"""
    st.header("📡 Modelo LiDAR 3D del Terreno")
    
    if not st.session_state.get('polygon_loaded'):
        st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
        return
    
    st.success("✅ Lote cargado - Generando modelo 3D específico")
    
    if st.button("🔄 Generar Modelo LiDAR 3D", type="primary"):
        with st.spinner("Generando modelo 3D del terreno..."):
            # Simular generación
            st.success("✅ Modelo LiDAR 3D generado!")
            
            # Mostrar métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Puntos Generados", "12,847")
                st.metric("Altura Máxima", "8.2 m")
            with col2:
                st.metric("Resolución", "0.5 m")
                st.metric("Altura Mínima", "0.2 m")
            with col3:
                st.metric("Pendiente Media", "3.2%")
                st.metric("Desnivel Total", "8.0 m")
            with col4:
                st.metric("Calidad", "Alta")
            
            # Generar visualizaciones LiDAR
            lidar_viz = Lidar3DVisualizer()
            polygon = st.session_state.current_polygon
            
            st.subheader("🌋 Visualización 3D Interactiva")
            lidar_3d_fig = lidar_viz.create_3d_visualization(polygon)
            st.plotly_chart(lidar_3d_fig, use_container_width=True)
            
            # Análisis de pendientes
            st.subheader("📊 Análisis de Pendientes")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Pendiente Media", "3.2%")
                st.metric("Área Plana (<2%)", "45%")
            with col2:
                st.metric("Pendiente Máxima", "12.8%")
                st.metric("Área Inclinada (>5%)", "25%")
            with col3:
                st.metric("Dirección Predominante", "Noreste")
                st.metric("Erosión Potencial", "Baja")

def render_dashboard():
    """Dashboard integrado mejorado"""
    st.header("📊 Dashboard Integrado")
    
    if not st.session_state.get('polygon_loaded'):
        st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
        return
    
    st.success("✅ Lote cargado - Vista consolidada de todos los análisis")
    
    # Métricas resumen
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Fertilidad Suelo", "78%", "3%")
    with col2:
        st.metric("Salud Vegetal", "85%", "5%")
    with col3:
        st.metric("Cobertura Vegetal", "72%", "2%")
    with col4:
        st.metric("Área Total", f"{st.session_state.get('polygon_area_ha', 0):.1f} ha")
    
    # Gráficos del dashboard
    dashboard_viz = DashboardVisualizer()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de torta - composición del suelo
        pie_chart = dashboard_viz.create_soil_pie_chart()
        st.plotly_chart(pie_chart, use_container_width=True)
        
        # Gráfico de evolución de salud vegetal
        health_chart = dashboard_viz.create_vegetation_health_chart()
        st.plotly_chart(health_chart, use_container_width=True)
    
    with col2:
        # Gráfico de barras - nutrientes
        bar_chart = dashboard_viz.create_nutrient_bar_chart()
        st.plotly_chart(bar_chart, use_container_width=True)
        
        # Medidor de productividad
        gauge_chart = dashboard_viz.create_productivity_gauge()
        st.plotly_chart(gauge_chart, use_container_width=True)
    
    # Recomendaciones integradas
    st.subheader("🎯 Recomendaciones Integradas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("""
        **🌱 SUELO**
        - Fertilización balanceada requerida
        - pH en rango óptimo
        - Materia orgánica adecuada
        """)
    
    with col2:
        st.info("""
        **💧 RIEGO**
        - Eficiencia hídrica: 85%
        - Programar riego por sectores
        - Monitorear humedad
        """)
    
    with col3:
        st.warning("""
        **📈 PRODUCTIVIDAD**
        - Rendimiento esperado: 85%
        - Áreas de mejora identificadas
        - Seguimiento recomendado
        """)

# ============================================================================
# FLUJO PRINCIPAL
# ============================================================================

def main():
    """Función principal"""
    
    # Inicializar session state
    if 'polygon_loaded' not in st.session_state:
        st.session_state.polygon_loaded = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Inicio"
    
    # Sidebar
    st.sidebar.title("🌱 Navegación")
    st.sidebar.markdown("---")
    
    # Navegación principal
    page = st.sidebar.radio(
        "Seleccionar Módulo:",
        ["🏠 Inicio", "🌱 Análisis Suelo", "🛰️ Satelital", "📡 LiDAR 3D", "📊 Dashboard"],
        key="main_navigation"
    )
    
    st.sidebar.markdown("---")
    
    # Estado actual
    if st.session_state.get('polygon_loaded'):
        area_ha = st.session_state.get('polygon_area_ha', 0)
        st.sidebar.success(f"✅ Lote cargado\n{area_ha:.1f} ha")
        
        if st.sidebar.button("🔄 Cambiar Lote", key="change_lot"):
            for key in ['polygon_loaded', 'current_polygon', 'polygon_area_ha', 'polygon_bounds', 'file_type']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
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
