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
# INTERFAZ DE CARGA EN INICIO
# ============================================================================

def render_polygon_upload():
    """Interfaz para carga de polígonos en el inicio"""
    st.header("🗺️ Carga tu Lote o Campo
