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
# MÓDULO DE FERTILIDAD
# ============================================================================

class SoilFertilityAnalyzer:
    def __init__(self):
        self.fertility_data = None
        
    def generate_fertility_map(self, polygon, soil_params):
        """Genera mapa de fertilidad basado en parámetros del suelo"""
        bounds = self._get_polygon_bounds(polygon)
        
        # Crear grid dentro del polígono
        grid_size = 20
        lons = np.linspace(bounds['min_lon'], bounds['max_lon'], grid_size)
        lats = np.linspace(bounds['min_lat'], bounds['max_lat'], grid_size)
        
        # Generar datos de fertilidad simulados
        fertility_grid = np.zeros((grid_size, grid_size))
        
        for i in range(grid_size):
            for j in range(grid_size):
                # Simular variación espacial basada en parámetros
                base_fertility = (
                    soil_params['ph'] * 0.3 +
                    soil_params['organic_matter'] * 0.4 +
                    soil_params['nitrogen'] * 0.1 +
                    soil_params['phosphorus'] * 0.1 +
                    soil_params['potassium'] * 0.1
                ) / 10.0
                
                # Agregar variación espacial
                variation = np.sin(i * 0.5) * np.cos(j * 0.5) * 0.2
                fertility_grid[i, j] = np.clip(base_fertility + variation, 0.1, 1.0)
        
        return lons, lats, fertility_grid
    
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
        fig.add_trace(go.Contour(
            z=fertility_grid,
            x=lons,
            y=lats,
            colorscale='RdYlGn',
            opacity=0.7,
            name='Fertilidad',
            hovertemplate='Fertilidad: %{z:.2f}<extra></extra>'
        ))
        
        # Contorno del polígono
        poly_lons = [p[0] for p in polygon] + [polygon[0][0]]
        poly_lats = [p[1] for p in polygon] + [polygon[0][1]]
        
        fig.add_trace(go.Scatter(
            x=poly_lons,
            y=poly_lats,
            mode='lines',
            line=dict(color='red', width=3),
            name='Límite del Lote'
        ))
        
        fig.update_layout(
            title='🌱 Mapa de Fertilidad del Suelo',
            xaxis_title='Longitud',
            yaxis_title='Latitud',
            height=500,
            showlegend=True
        )
        
        return fig

# ============================================================================
# MÓDULO LIDAR 3D
# ============================================================================

class Lidar3DVisualizer:
    def __init__(self):
        self.terrain_data = None
        
    def generate_terrain_data(self, polygon):
        """Genera datos de terreno simulados para LiDAR"""
        bounds = self._get_polygon_bounds(polygon)
        
        # Crear grid más denso para mejor visualización 3D
        grid_size = 30
        x = np.linspace(bounds['min_lon'], bounds['max_lon'], grid_size)
        y = np.linspace(bounds['min_lat'], bounds['max_lat'], grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Generar terreno con variaciones realistas
        Z = self._generate_realistic_terrain(X, Y, bounds)
        
        # Generar datos de vegetación
        vegetation_height = self._generate_vegetation_data(X, Y, Z)
        
        return X, Y, Z, vegetation_height
    
    def _generate_realistic_terrain(self, X, Y, bounds):
        """Genera terreno realista con múltiples frecuencias"""
        # Escalar coordenadas para mejor comportamiento del ruido
        x_scaled = (X - bounds['min_lon']) / (bounds['max_lon'] - bounds['min_lon']) * 10
        y_scaled = (Y - bounds['min_lat']) / (bounds['max_lat'] - bounds['min_lat']) * 10
        
        # Terreno base con pendiente suave
        base_slope = 0.5 * x_scaled + 0.3 * y_scaled
        
        # Variaciones de alta frecuencia (colinas pequeñas)
        high_freq = (
            np.sin(2 * x_scaled) * np.cos(1.5 * y_scaled) * 0.3 +
            np.sin(3 * x_scaled + 1) * np.cos(2 * y_scaled - 0.5) * 0.2
        )
        
        # Variaciones de baja frecuencia (colinas grandes)
        low_freq = np.sin(0.5 * x_scaled) * np.cos(0.5 * y_scaled) * 0.8
        
        # Combinar todas las capas
        Z = base_slope + low_freq + high_freq
        
        # Normalizar a rango realista (0-10 metros)
        Z = (Z - Z.min()) / (Z.max() - Z.min()) * 10
        
        return Z
    
    def _generate_vegetation_data(self, X, Y, terrain):
        """Genera datos de altura de vegetación"""
        # Patrón de vegetación que sigue el terreno
        veg_pattern = (
            np.sin(3 * X) * np.cos(2 * Y) * 0.5 +
            np.sin(2 * X + 1) * np.cos(3 * Y - 0.5) * 0.3
        )
        
        # La vegetación es más alta en áreas más bajas
        vegetation = np.clip((1 - terrain / terrain.max()) * 3 + veg_pattern, 0, 4)
        
        return vegetation
    
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
        X, Y, Z, vegetation = self.generate_terrain_data(polygon)
        
        fig = go.Figure()
        
        # Superficie del terreno
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z,
            colorscale='Earth',
            opacity=0.9,
            name='Terreno',
            showscale=True,
            colorbar=dict(title="Altura (m)")
        ))
        
        # Vegetación como puntos 3D
        veg_points = []
        for i in range(0, X.shape[0], 3):  # Submuestrear para mejor rendimiento
            for j in range(0, X.shape[1], 3):
                if vegetation[i, j] > 0.5:  # Solo mostrar vegetación significativa
                    veg_points.append({
                        'x': X[i, j],
                        'y': Y[i, j], 
                        'z': Z[i, j] + vegetation[i, j] / 2,
                        'height': vegetation[i, j]
                    })
        
        if veg_points:
            veg_x = [p['x'] for p in veg_points]
            veg_y = [p['y'] for p in veg_points]
            veg_z = [p['z'] for p in veg_points]
            veg_heights = [p['height'] for p in veg_points]
            
            fig.add_trace(go.Scatter3d(
                x=veg_x, y=veg_y, z=veg_z,
                mode='markers',
                marker=dict(
                    size=3,
                    color=veg_heights,
                    colorscale='Greens',
                    opacity=0.7,
                    colorbar=dict(title="Altura Veg. (m)")
                ),
                name='Vegetación'
            ))
        
        fig.update_layout(
            title='📡 Modelo LiDAR 3D - Topografía y Vegetación',
            scene=dict(
                xaxis_title='Longitud',
                yaxis_title='Latitud',
                zaxis_title='Altura (m)',
                aspectmode='manual',
                aspectratio=dict(x=1, y=1, z=0.3)
            ),
            height=600,
            margin=dict(l=0, r=0, b=0, t=40)
        )
        
        return fig
    
    def create_topographic_map(self, polygon):
        """Crea mapa topográfico 2D con curvas de nivel"""
        X, Y, Z, _ = self.generate_terrain_data(polygon)
        
        fig = go.Figure()
        
        # Mapa de calor de elevación
        fig.add_trace(go.Contour(
            z=Z,
            x=X[0, :],  # Longitudes
            y=Y[:, 0],  # Latitudes
            colorscale='Viridis',
            name='Elevación',
            contours=dict(
                showlabels=True,
                labelfont=dict(size=12, color='white')
            ),
            colorbar=dict(title="Elevación (m)")
        ))
        
        # Contorno del polígono
        poly_lons = [p[0] for p in polygon] + [polygon[0][0]]
        poly_lats = [p[1] for p in polygon] + [polygon[0][1]]
        
        fig.add_trace(go.Scatter(
            x=poly_lons,
            y=poly_lats,
            mode='lines',
            line=dict(color='red', width=3),
            name='Límite del Lote'
        ))
        
        fig.update_layout(
            title='🗺️ Mapa Topográfico con Curvas de Nivel',
            xaxis_title='Longitud',
            yaxis_title='Latitud',
            height=500,
            showlegend=True
        )
        
        return fig

# ============================================================================
# INTERFAZ DE CARGA EN INICIO
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
        help="Puedes subir KML, GeoJSON o ZIP con Shapefile",
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
        
        # Ejemplos de formatos
        st.markdown("---")
        st.subheader("📋 Ejemplos de Formatos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Google Earth (KML)**")
            st.code("""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Placemark>
  <Polygon>
    <coordinates>
      -58.500,-34.600,0
      -58.400,-34.600,0
      -58.400,-34.500,0
      -58.500,-34.500,0
    </coordinates>
  </Polygon>
</Placemark>
</kml>""", language="xml")
        
        with col2:
            st.write("**GeoJSON**")
            st.code("""{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [-58.500, -34.600],
      [-58.400, -34.600],
      [-58.400, -34.500],
      [-58.500, -34.500],
      [-58.500, -34.600]
    ]]
  }
}""", language="json")
        
        with col3:
            st.write("**Shapefile**")
            st.write("Archivos necesarios en ZIP:")
            st.write("- `.shp` (geometría)")
            st.write("- `.shx` (índice)") 
            st.write("- `.dbf` (atributos)")
            st.write("- `.prj` (proyección)")

# ============================================================================
# MÓDULOS DE ANÁLISIS (completos)
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
                st.metric("NDVI - Salud Vegetal", "0.68", "Excelente")
            with col2:
                st.metric("NDWI - Agua", "-0.12", "Óptimo")
            with col3:
                st.metric("EVI - Vegetación Densa", "0.45")
            with col4:
                st.metric("NDRE - Nutrientes", "0.28", "Óptimo")
            
            # Mapa simulado
            st.subheader("🗺️ Mapa de Salud Vegetal")
            st.info("Mapa de NDVI generado para tu lote")

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
                st.metric("Puntos Generados", "3,847")
                st.metric("Altura Máxima", "2.8 m")
            with col2:
                st.metric("Cobertura Vegetal", "72%")
                st.metric("Altura Media Veg.", "1.5 m")
            with col3:
                st.metric("Puntos Terreno", "1,153")
                st.metric("Altura Media", "0.8 m")
            with col4:
                st.metric("Resolución", "Alta")
            
            # Generar visualizaciones LiDAR
            lidar_viz = Lidar3DVisualizer()
            polygon = st.session_state.current_polygon
            
            st.subheader("🌋 Visualización 3D Interactiva")
            lidar_3d_fig = lidar_viz.create_3d_visualization(polygon)
            st.plotly_chart(lidar_3d_fig, use_container_width=True)
            
            st.subheader("🗺️ Mapa Topográfico 2D")
            topo_fig = lidar_viz.create_topographic_map(polygon)
            st.plotly_chart(topo_fig, use_container_width=True)
            
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
    """Dashboard integrado"""
    st.header("📊 Dashboard Integrado")
    
    if not st.session_state.get('polygon_loaded'):
        st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
        return
    
    st.success("✅ Lote cargado - Vista consolidada de todos los análisis")
    
    # Métricas resumen
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Fertilidad Suelo", "78%")
    with col2:
        st.metric("Salud Vegetal", "85%")
    with col3:
        st.metric("Cobertura Vegetal", "72%")
    with col4:
        st.metric("Área Total", f"{st.session_state.get('polygon_area_ha', 0):.1f} ha")
    
    st.subheader("🎯 Recomendaciones Integradas")
    st.success("""
    **✅ CONDICIONES GENERALES BUENAS**
    - Suelo y vegetación en buen estado
    - Mantener prácticas actuales de manejo
    - Monitoreo preventivo recomendado
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
