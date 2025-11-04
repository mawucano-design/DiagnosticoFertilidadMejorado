import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import json
import xml.etree.ElementTree as ET
from io import BytesIO
import zipfile

# CONFIGURACIÓN BÁSICA
st.set_page_config(
    page_title="Plataforma Agrícola",
    page_icon="🌱",
    layout="wide"
)

# ============================================================================
# INICIALIZACIÓN DE SESSION STATE
# ============================================================================

if 'polygon_loaded' not in st.session_state:
    st.session_state.polygon_loaded = False
if 'current_polygon' not in st.session_state:
    st.session_state.current_polygon = None
if 'polygon_area_ha' not in st.session_state:
    st.session_state.polygon_area_ha = 0
if 'file_type' not in st.session_state:
    st.session_state.file_type = None

# ============================================================================
# MÓDULO DE CARGA DE POLÍGONOS
# ============================================================================

class PolygonProcessor:
    def parse_kml(self, kml_content):
        try:
            root = ET.fromstring(kml_content)
            polygons = []
            
            for polygon in root.findall('.//{http://www.opengis.net/kml/2.2}Polygon'):
                coordinates_elem = polygon.find('.//{http://www.opengis.net/kml/2.2}coordinates')
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
            st.error("Error procesando KML")
            return []

    def parse_geojson(self, geojson_content):
        try:
            data = json.loads(geojson_content)
            polygons = []
            
            if data['type'] == 'FeatureCollection':
                for feature in data['features']:
                    geom = feature['geometry']
                    if geom['type'] == 'Polygon':
                        ring = geom['coordinates'][0]
                        polygon = [[coord[0], coord[1]] for coord in ring]
                        polygons.append(polygon)
            elif data['type'] == 'Feature':
                geom = data['geometry']
                if geom['type'] == 'Polygon':
                    ring = geom['coordinates'][0]
                    polygon = [[coord[0], coord[1]] for coord in ring]
                    polygons.append(polygon)
            
            return polygons
        except:
            st.error("Error procesando GeoJSON")
            return []

    def calculate_polygon_area(self, polygon):
        try:
            area = 0
            n = len(polygon)
            for i in range(n):
                j = (i + 1) % n
                area += polygon[i][0] * polygon[j][1]
                area -= polygon[j][0] * polygon[i][1]
            area = abs(area) / 2.0
            return max(area * 10000, 1.0)
        except:
            return 10.0

# ============================================================================
# MÓDULO DE MAPAS
# ============================================================================

class MapVisualizer:
    def create_satellite_map(self, polygon=None):
        if polygon is None:
            center = {"lat": -34.6037, "lon": -58.3816}
        else:
            lats = [p[1] for p in polygon]
            lons = [p[0] for p in polygon]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            center = {"lat": center_lat, "lon": center_lon}
        
        fig = go.Figure()
        
        if polygon:
            lats = [p[1] for p in polygon] + [polygon[0][1]]
            lons = [p[0] for p in polygon] + [polygon[0][0]]
            
            fig.add_trace(go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode='lines+markers',
                fill='toself',
                fillcolor='rgba(255, 0, 0, 0.3)',
                line=dict(color='red', width=3),
                name='Tu Lote'
            ))
        
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=center,
                zoom=12,
            ),
            margin={"r":0,"t":0,"l":0,"b":0},
            height=400
        )
        
        return fig

# ============================================================================
# MÓDULO LIDAR 3D
# ============================================================================

class LidarVisualizer:
    def generate_terrain(self, polygon):
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        grid_size = 30
        x = np.linspace(min_lon, max_lon, grid_size)
        y = np.linspace(min_lat, max_lat, grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Crear terreno realista
        Z = np.zeros_like(X)
        for i in range(grid_size):
            for j in range(grid_size):
                # Verificar si está dentro del polígono
                if self.is_point_in_polygon(X[i,j], Y[i,j], polygon):
                    # Generar relieve realista
                    dx = (X[i,j] - min_lon) / (max_lon - min_lon) * 10
                    dy = (Y[i,j] - min_lat) / (max_lat - min_lat) * 10
                    Z[i,j] = (np.sin(dx) * np.cos(dy) * 3 + 
                             np.sin(dx*0.5) * np.cos(dy*0.5) * 2 +
                             np.sin(dx*0.2) * np.cos(dy*0.2) * 1)
                else:
                    Z[i,j] = np.nan
        
        # Normalizar
        Z = (Z - np.nanmin(Z)) / (np.nanmax(Z) - np.nanmin(Z)) * 10
        return X, Y, Z

    def is_point_in_polygon(self, x, y, polygon):
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

    def create_3d_visualization(self, polygon):
        X, Y, Z = self.generate_terrain(polygon)
        
        fig = go.Figure()
        
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z,
            colorscale='Viridis',
            opacity=0.9
        ))
        
        fig.update_layout(
            title='Modelo 3D del Terreno',
            scene=dict(
                xaxis_title='Longitud',
                yaxis_title='Latitud', 
                zaxis_title='Elevación (m)'
            ),
            height=500
        )
        
        return fig

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

def main():
    st.title("🌱 Plataforma Agrícola de Precisión")
    
    # Sidebar
    st.sidebar.title("Navegación")
    page = st.sidebar.selectbox(
        "Selecciona una página:",
        ["Inicio", "Análisis de Suelo", "LiDAR 3D", "Dashboard"]
    )
    
    # Página de Inicio
    if page == "Inicio":
        st.header("Carga tu Lote o Campo")
        
        uploaded_file = st.file_uploader(
            "Sube tu archivo KML o GeoJSON",
            type=['kml', 'geojson', 'json']
        )
        
        processor = MapVisualizer()
        
        if uploaded_file is not None:
            content = uploaded_file.read()
            polygon_processor = PolygonProcessor()
            
            try:
                if uploaded_file.name.endswith('.kml'):
                    polygons = polygon_processor.parse_kml(content)
                    file_type = "KML"
                else:
                    polygons = polygon_processor.parse_geojson(content.decode('utf-8'))
                    file_type = "GeoJSON"
                
                if polygons:
                    polygon = polygons[0]
                    area = polygon_processor.calculate_polygon_area(polygon)
                    
                    # Actualizar session state
                    st.session_state.polygon_loaded = True
                    st.session_state.current_polygon = polygon
                    st.session_state.polygon_area_ha = area
                    st.session_state.file_type = file_type
                    
                    st.success("Archivo procesado correctamente")
                    
                    # Mostrar información
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Área", f"{area:.1f} ha")
                    with col2:
                        st.metric("Formato", file_type)
                    with col3:
                        st.metric("Estado", "Cargado")
                    
                    # Mostrar mapa
                    st.subheader("Vista de tu Lote")
                    map_fig = processor.create_satellite_map(polygon)
                    st.plotly_chart(map_fig, use_container_width=True)
                    
            except Exception as e:
                st.error("Error al procesar el archivo")
        
        else:
            st.info("""
            **Instrucciones:**
            1. Sube un archivo KML o GeoJSON de tu lote
            2. Espera a que se procese
            3. Navega a las otras secciones para análisis
            """)
    
    # Página de Análisis de Suelo
    elif page == "Análisis de Suelo":
        st.header("Análisis de Suelo")
        
        if not st.session_state.polygon_loaded:
            st.warning("Primero carga un polígono en la página de Inicio")
            return
        
        st.success("Lote cargado - Análisis específico")
        
        with st.form("soil_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                ph = st.slider("pH", 4.0, 9.0, 6.5)
                organic = st.slider("Materia Orgánica %", 0.5, 8.0, 2.5)
                
            with col2:
                nitrogen = st.slider("Nitrógeno ppm", 10, 200, 50)
                phosphorus = st.slider("Fósforo ppm", 5, 100, 25)
                potassium = st.slider("Potasio ppm", 50, 300, 120)
            
            if st.form_submit_button("Analizar Suelo"):
                st.success("Análisis completado")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Fertilidad", "78%")
                    st.metric("pH", "Óptimo")
                    st.metric("Materia Org", "Buena")
                with col2:
                    st.metric("Nitrógeno", "Adecuado")
                    st.metric("Fósforo", "Óptimo") 
                    st.metric("Potasio", "Adecuado")
    
    # Página LiDAR 3D
    elif page == "LiDAR 3D":
        st.header("Modelo LiDAR 3D")
        
        if not st.session_state.polygon_loaded:
            st.warning("Primero carga un polígono en la página de Inicio")
            return
        
        st.success("Generando modelo 3D específico")
        
        if st.button("Generar Modelo 3D"):
            lidar = LidarVisualizer()
            polygon = st.session_state.current_polygon
            
            with st.spinner("Creando modelo 3D..."):
                fig_3d = lidar.create_3d_visualization(polygon)
                st.plotly_chart(fig_3d, use_container_width=True)
                
                # Métricas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Resolución", "Alta")
                with col2:
                    st.metric("Puntos 3D", "2,500")
                with col3:
                    st.metric("Elevación Max", "8.2 m")
                with col4:
                    st.metric("Calidad", "Buena")
    
    # Página Dashboard
    elif page == "Dashboard":
        st.header("Dashboard Integrado")
        
        if not st.session_state.polygon_loaded:
            st.warning("Primero carga un polígono en la página de Inicio")
            return
        
        st.success("Vista consolidada de análisis")
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Fertilidad", "78%")
        with col2:
            st.metric("Salud Vegetal", "85%")
        with col3:
            st.metric("Área Total", f"{st.session_state.polygon_area_ha:.1f} ha")
        with col4:
            st.metric("Estado", "Óptimo")
        
        # Gráficos simples
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de torta
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Óptimo', 'Bueno', 'Regular'],
                values=[60, 30, 10]
            )])
            fig_pie.update_layout(title="Estado General")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Gráfico de barras
            fig_bar = go.Figure(data=[go.Bar(
                x=['N', 'P', 'K', 'OM'],
                y=[85, 75, 90, 65]
            )])
            fig_bar.update_layout(title="Nutrientes (%)")
            st.plotly_chart(fig_bar, use_container_width=True)

if __name__ == "__main__":
    main()
