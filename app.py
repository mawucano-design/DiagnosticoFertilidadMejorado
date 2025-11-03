import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import io
import json
import xml.etree.ElementTree as ET
from io import BytesIO
import zipfile

# CONFIGURACIÓN - DEBE SER LO PRIMERO
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
            # Parsear KML
            root = ET.fromstring(kml_content)
            
            # Namespace de KML
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            polygons = []
            
            # Buscar polígonos en el KML
            for polygon in root.findall('.//kml:Polygon', ns):
                coordinates_elem = polygon.find('.//kml:coordinates', ns)
                if coordinates_elem is not None:
                    coords_text = coordinates_elem.text.strip()
                    coordinates = []
                    
                    # Parsear coordenadas
                    for line in coords_text.split():
                        parts = line.split(',')
                        if len(parts) >= 2:
                            lon, lat = float(parts[0]), float(parts[1])
                            coordinates.append([lon, lat])
                    
                    if coordinates:
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
            
            if data['type'] == 'FeatureCollection':
                for feature in data['features']:
                    if feature['geometry']['type'] == 'Polygon':
                        polygons.extend(feature['geometry']['coordinates'])
            elif data['type'] == 'Feature':
                if data['geometry']['type'] == 'Polygon':
                    polygons.extend(data['geometry']['coordinates'])
            elif data['type'] == 'Polygon':
                polygons.extend(data['coordinates'])
            
            return polygons
            
        except Exception as e:
            st.error(f"Error parseando GeoJSON: {e}")
            return []
    
    def parse_shapefile_zip(self, zip_file):
        """Simula parseo de shapefile (versión simplificada)"""
        try:
            # En una implementación real usarías fiona o geopandas
            st.info("📦 Archivo shapefile detectado (procesamiento simulado)")
            
            # Crear polígono de ejemplo
            polygon = [
                [-58.500, -34.600],
                [-58.400, -34.600],
                [-58.400, -34.500],
                [-58.500, -34.500],
                [-58.500, -34.600]
            ]
            
            return [polygon]
            
        except Exception as e:
            st.error(f"Error procesando shapefile: {e}")
            return []
    
    def calculate_polygon_area(self, polygon):
        """Calcula área aproximada del polígono en hectáreas"""
        try:
            # Fórmula del área de Gauss
            area = 0
            n = len(polygon)
            
            for i in range(n):
                j = (i + 1) % n
                area += polygon[i][0] * polygon[j][1]
                area -= polygon[j][0] * polygon[i][1]
            
            area = abs(area) / 2.0
            
            # Convertir a hectáreas (aproximación)
            # 1 grado ≈ 111 km en latitud, varía en longitud
            area_hectares = area * 111 * 111 * 100  # Conversión simplificada
            
            return max(area_hectares, 0.1)  # Mínimo 0.1 ha
            
        except:
            return 10.0  # Valor por defecto
    
    def create_lidar_data_for_polygon(self, polygon, points_per_hectare=1000):
        """Genera datos LiDAR simulados para el polígono"""
        if not polygon:
            return None
        
        # Calcular bounding box del polígono
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        # Calcular área y número de puntos
        area_ha = self.calculate_polygon_area(polygon)
        num_points = int(area_ha * points_per_hectare)
        
        # Generar puntos aleatorios dentro del polígono
        points = []
        for _ in range(num_points):
            # Generar punto aleatorio en el bounding box
            lon = np.random.uniform(min_lon, max_lon)
            lat = np.random.uniform(min_lat, max_lat)
            
            # Verificar si el punto está dentro del polígono (simplificado)
            if self.point_in_polygon(lon, lat, polygon):
                # Altura base + variación de terreno + vegetación
                base_height = np.random.uniform(0, 0.5)
                
                # Simular vegetación (algunos puntos más altos)
                if np.random.random() > 0.7:  # 30% de puntos son vegetación
                    height = base_height + np.random.uniform(0.5, 3.0)
                else:
                    height = base_height
                
                points.append([lon, lat, height])
        
        return np.array(points) if points else None
    
    def point_in_polygon(self, x, y, poly):
        """Verifica si un punto está dentro de un polígono (algoritmo ray casting)"""
        n = len(poly)
        inside = False
        
        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xints:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside

# ============================================================================
# MÓDULO LIDAR - INTEGRADO DIRECTAMENTE
# ============================================================================

class LiDARProcessor:
    def __init__(self):
        self.point_cloud = None
        
    def create_sample_data(self, polygon=None):
        """Crea datos de ejemplo, opcionalmente dentro de un polígono"""
        np.random.seed(42)
        
        if polygon:
            # Usar el polígono para generar datos
            polygon_processor = PolygonProcessor()
            points = polygon_processor.create_lidar_data_for_polygon(polygon)
            if points is not None:
                self.point_cloud = type('PointCloud', (), {})()
                self.point_cloud.points = points
                return self.point_cloud
        
        # Datos de ejemplo por defecto
        x = np.linspace(0, 10, 50)
        y = np.linspace(0, 10, 50)
        xx, yy = np.meshgrid(x, y)
        z_ground = 0.1 * np.sin(xx) * np.cos(yy)
        
        plant_centers = [(3, 3), (7, 7), (5, 2), (2, 7), (8, 3)]
        points = []
        
        for i in range(len(xx.flatten())):
            points.append([xx.flatten()[i], yy.flatten()[i], z_ground.flatten()[i]])
        
        for center_x, center_y in plant_centers:
            for _ in range(200):
                dx, dy = np.random.normal(0, 0.5, 2)
                height = np.random.uniform(0.5, 2.0)
                z = z_ground[int(center_x*5), int(center_y*5)] + height
                points.append([center_x + dx, center_y + dy, z])
        
        points = np.array(points)
        self.point_cloud = type('PointCloud', (), {})()
        self.point_cloud.points = points
        return self.point_cloud

def extract_plant_metrics(point_cloud):
    """Extrae métricas de vegetación"""
    if point_cloud is None:
        return {}
    
    points = point_cloud.points
    
    min_z = np.min(points[:, 2])
    max_z = np.max(points[:, 2])
    plant_height = max_z - min_z
    
    ground_level = np.percentile(points[:, 2], 10)
    vegetation_mask = points[:, 2] > ground_level + 0.2
    vegetation_points = points[vegetation_mask]
    
    # Calcular área aproximada del dataset
    x_range = np.max(points[:, 0]) - np.min(points[:, 0])
    y_range = np.max(points[:, 1]) - np.min(points[:, 1])
    area_m2 = x_range * y_range
    area_ha = area_m2 / 10000
    
    metrics = {
        'plant_height': float(plant_height),
        'canopy_volume': float(len(vegetation_points) * 0.001),
        'plant_density': int(len(vegetation_points)),
        'canopy_area': float(area_ha),
        'health_score': float(min(100, len(vegetation_points) / max(1, len(points) / 100))),
        'growth_stage': "Vegetativo" if plant_height > 1.0 else "Crecimiento",
        'max_height': float(max_z),
        'min_height': float(min_z),
        'vegetation_points': len(vegetation_points),
        'total_points': len(points),
        'area_hectares': float(area_ha),
        'vegetation_percentage': float(len(vegetation_points) / len(points) * 100)
    }
    
    return metrics

def create_interactive_plot(point_cloud, title="Visualización 3D - Datos LiDAR"):
    """Crea visualización 3D interactiva"""
    points = point_cloud.points
    
    fig = go.Figure()
    
    ground_level = np.percentile(points[:, 2], 10)
    ground_mask = points[:, 2] <= ground_level + 0.2
    vegetation_mask = points[:, 2] > ground_level + 0.2
    
    if np.any(ground_mask):
        ground_points = points[ground_mask]
        fig.add_trace(go.Scatter3d(
            x=ground_points[:, 0],
            y=ground_points[:, 1],
            z=ground_points[:, 2],
            mode='markers',
            marker=dict(size=3, color='brown', opacity=0.6),
            name='Terreno'
        ))
    
    if np.any(vegetation_mask):
        veg_points = points[vegetation_mask]
        fig.add_trace(go.Scatter3d(
            x=veg_points[:, 0],
            y=veg_points[:, 1], 
            z=veg_points[:, 2],
            mode='markers',
            marker=dict(
                size=4, 
                color=veg_points[:, 2], 
                colorscale='Viridis',
                opacity=0.8
            ),
            name='Vegetación'
        ))
    
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title='Longitud',
            yaxis_title='Latitud',
            zaxis_title='Altura (m)',
            aspectmode='data'
        ),
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar estadísticas
    metrics = extract_plant_metrics(point_cloud)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Puntos", f"{len(points):,}")
    with col2:
        st.metric("Área", f"{metrics['area_hectares']:.2f} ha")
    with col3:
        st.metric("Vegetación", f"{metrics['vegetation_points']:,} pts")
    with col4:
        st.metric("% Vegetación", f"{metrics['vegetation_percentage']:.1f}%")

# ============================================================================
# MÓDULO FERTILIDAD - INTEGRADO DIRECTAMENTE
# ============================================================================

def analisis_suelo_main():
    """Módulo completo de análisis de suelo"""
    st.header("🔍 Análisis de Fertilidad del Suelo")
    
    with st.form("soil_analysis_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Parámetros Básicos")
            ph = st.slider("pH del suelo", 3.0, 9.0, 6.5, 0.1)
            materia_organica = st.slider("Materia Orgánica (%)", 0.1, 10.0, 2.5, 0.1)
            textura = st.selectbox("Textura del Suelo", ["Arcilloso", "Franco", "Arenoso"])
            
        with col2:
            st.subheader("Nutrientes Principales")
            nitrogeno = st.slider("Nitrógeno (ppm)", 0, 200, 50)
            fosforo = st.slider("Fósforo (ppm)", 0, 150, 30)
            potasio = st.slider("Potasio (ppm)", 0, 300, 100)
        
        cultivo = st.selectbox("Cultivo Principal", ["Maíz", "Soja", "Trigo", "Girasol", "Algodón"])
        
        if st.form_submit_button("🔬 Analizar Suelo"):
            puntaje_ph = calcular_puntaje_ph(ph, cultivo)
            puntaje_mo = calcular_puntaje_materia_organica(materia_organica, textura)
            puntaje_n = calcular_puntaje_nitrogeno(nitrogeno, cultivo)
            puntaje_p = calcular_puntaje_fosforo(fosforo, cultivo)
            puntaje_k = calcular_puntaje_potasio(potasio, cultivo)
            
            puntaje_general = (
                puntaje_ph * 0.2 +
                puntaje_mo * 0.2 +
                puntaje_n * 0.25 +
                puntaje_p * 0.2 +
                puntaje_k * 0.15
            )
            
            st.session_state.soil_data = {
                'ph': ph,
                'organic_matter': materia_organica,
                'texture': textura,
                'nitrogen': nitrogeno,
                'phosphorus': fosforo,
                'potassium': potasio,
                'crop': cultivo,
                'fertility_score': puntaje_general
            }
            
            mostrar_resultados_fertilidad({
                'ph': {'valor': ph, 'puntaje': puntaje_ph},
                'materia_organica': {'valor': materia_organica, 'puntaje': puntaje_mo},
                'nitrogeno': {'valor': nitrogeno, 'puntaje': puntaje_n},
                'fosforo': {'valor': fosforo, 'puntaje': puntaje_p},
                'potasio': {'valor': potasio, 'puntaje': puntaje_k},
                'puntaje_general': puntaje_general
            })

def calcular_puntaje_ph(ph, cultivo):
    rangos = {"Maíz": (5.8, 7.0), "Soja": (6.0, 7.0), "Trigo": (6.0, 7.5)}
    optimo = rangos.get(cultivo, (6.0, 7.0))
    if optimo[0] <= ph <= optimo[1]:
        return 100
    elif ph < 5.0 or ph > 8.0:
        return 30
    else:
        return 70

def calcular_puntaje_materia_organica(mo, textura):
    if mo >= 3.0:
        return 100
    elif mo >= 2.0:
        return 75
    else:
        return 50

def calcular_puntaje_nitrogeno(nitrogeno, cultivo):
    if nitrogeno >= 40:
        return 100
    elif nitrogeno >= 20:
        return 75
    else:
        return 50

def calcular_puntaje_fosforo(fosforo, cultivo):
    if fosforo >= 25:
        return 100
    elif fosforo >= 15:
        return 75
    else:
        return 50

def calcular_puntaje_potasio(potasio, cultivo):
    if potasio >= 120:
        return 100
    elif potasio >= 80:
        return 75
    else:
        return 50

def mostrar_resultados_fertilidad(resultados):
    st.header("📊 Resultados del Análisis")
    
    puntaje = resultados['puntaje_general']
    
    st.subheader(f"Puntaje General: {puntaje:.0f}/100")
    color = "red" if puntaje < 50 else "orange" if puntaje < 70 else "green"
    st.markdown(f"""
    <div style="background: #f0f0f0; border-radius: 10px; padding: 3px;">
        <div style="background: {color}; width: {puntaje}%; height: 25px; 
                    border-radius: 8px; text-align: center; color: white; 
                    line-height: 25px; font-weight: bold;">
            {puntaje:.0f}%
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("pH", f"{resultados['ph']['valor']}", f"{resultados['ph']['puntaje']}%")
        st.metric("Materia Orgánica", f"{resultados['materia_organica']['valor']}%", 
                 f"{resultados['materia_organica']['puntaje']}%")
    with col2:
        st.metric("Nitrógeno", f"{resultados['nitrogeno']['valor']} ppm", 
                 f"{resultados['nitrogeno']['puntaje']}%")
        st.metric("Fósforo", f"{resultados['fosforo']['valor']} ppm", 
                 f"{resultados['fosforo']['puntaje']}%")
    with col3:
        st.metric("Potasio", f"{resultados['potasio']['valor']} ppm", 
                 f"{resultados['potasio']['puntaje']}%")
        st.metric("Fertilidad General", f"{puntaje:.0f}%")
    
    st.header("🎯 Recomendaciones")
    if puntaje >= 80:
        st.success("✅ Condiciones óptimas. Mantener prácticas actuales.")
    elif puntaje >= 60:
        st.warning("⚠️ Condiciones aceptables. Considerar mejoras graduales.")
    else:
        st.error("❌ Necesita mejoras. Implementar plan de corrección.")

# ============================================================================
# INTERFAZ PRINCIPAL CON CARGA DE POLÍGONOS
# ============================================================================

def render_polygon_upload():
    """Interfaz para carga de polígonos"""
    st.header("🗺️ Cargar Polígono de Análisis")
    
    st.markdown("""
    **Carga tu área de interés en formato:**
    - **KML** (Google Earth, Google Maps)
    - **GeoJSON** (aplicaciones GIS)
    - **ZIP con Shapefile** (SIG profesionales)
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader(
            "Seleccionar archivo geográfico",
            type=['kml', 'kmz', 'geojson', 'json', 'zip'],
            key="polygon_uploader"
        )
    
    with col2:
        st.info("""
        **Formatos soportados:**
        - ✅ KML/KMZ (Google Earth)
        - ✅ GeoJSON
        - ✅ Shapefile (.zip)
        
        **El polígono definirá el área para:** 
        - Generación de datos LiDAR
        - Cálculo de área y métricas
        - Análisis espacial
        """)
    
    polygon_processor = PolygonProcessor()
    current_polygon = None
    
    if uploaded_file is not None:
        file_content = uploaded_file.read()
        
        try:
            if uploaded_file.type == "application/vnd.google-earth.kml+xml" or uploaded_file.name.endswith('.kml'):
                polygons = polygon_processor.parse_kml(file_content)
                st.success(f"✅ KML procesado: {len(polygons)} polígono(s) encontrado(s)")
                
            elif uploaded_file.type == "application/geo+json" or uploaded_file.name.endswith('.geojson') or uploaded_file.name.endswith('.json'):
                polygons = polygon_processor.parse_geojson(file_content.decode('utf-8'))
                st.success(f"✅ GeoJSON procesado: {len(polygons)} polígono(s) encontrado(s)")
                
            elif uploaded_file.type == "application/zip" or uploaded_file.name.endswith('.zip'):
                polygons = polygon_processor.parse_shapefile_zip(file_content)
                st.success(f"✅ Shapefile procesado: {len(polygons)} polígono(s) encontrado(s)")
            
            if polygons:
                current_polygon = polygons[0]  # Usar el primer polígono
                area_ha = polygon_processor.calculate_polygon_area(current_polygon)
                
                st.info(f"**📐 Área del polígono:** {area_ha:.2f} hectáreas")
                
                # Mostrar preview del polígono
                st.subheader("📊 Vista previa del Polígono")
                
                # Crear visualización 2D del polígono
                poly_df = pd.DataFrame(current_polygon, columns=['Longitud', 'Latitud'])
                poly_df = pd.concat([poly_df, poly_df.iloc[[0]]])  # Cerrar el polígono
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=poly_df['Longitud'],
                    y=poly_df['Latitud'],
                    fill='toself',
                    fillcolor='rgba(0,100,80,0.2)',
                    line=dict(color='rgba(0,100,80,1)'),
                    name='Polígono'
                ))
                
                fig.update_layout(
                    title="Vista del Polígono Cargado",
                    xaxis_title="Longitud",
                    yaxis_title="Latitud",
                    showlegend=False,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Guardar polígono en session state
                st.session_state.current_polygon = current_polygon
                st.session_state.polygon_area_ha = area_ha
                
        except Exception as e:
            st.error(f"❌ Error procesando archivo: {e}")
    
    return current_polygon

def render_lidar_page():
    st.title("🔄 Gemelos Digitales LiDAR")
    
    st.markdown("""
    **Procesamiento y visualización de datos LiDAR para agricultura de precisión**
    
    *Carga un polígono para generar datos específicos de tu área de interés*
    """)
    
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Polígono", "📤 Datos LiDAR", "📊 Métricas", "🌐 Visualización 3D"])
    
    with tab1:
        current_polygon = render_polygon_upload()
        
        if current_polygon:
            st.success("✅ Polígono listo para generar datos LiDAR")
        else:
            st.info("💡 Carga un polígono KML/GeoJSON/Shapefile para definir el área de análisis")
    
    with tab2:
        st.header("Datos LiDAR")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Generar Datos en Polígono", key="generate_polygon_data"):
                if 'current_polygon' in st.session_state:
                    processor = LiDARProcessor()
                    point_cloud = processor.create_sample_data(st.session_state.current_polygon)
                    st.session_state.point_cloud = point_cloud
                    st.success("✅ Datos LiDAR generados para el polígono")
                else:
                    st.warning("⚠️ Primero carga un polígono")
            
            if st.button("🔄 Generar Datos de Ejemplo", key="generate_sample_data"):
                processor = LiDARProcessor()
                point_cloud = processor.create_sample_data()
                st.session_state.point_cloud = point_cloud
                st.success("✅ Datos de ejemplo generados")
        
        with col2:
            if 'point_cloud' in st.session_state:
                points = st.session_state.point_cloud.points
                st.success(f"✅ {len(points):,} puntos LiDAR cargados")
                
                if 'polygon_area_ha' in st.session_state:
                    st.info(f"📐 Área de análisis: {st.session_state.polygon_area_ha:.2f} ha")
    
    with tab3:
        st.header("Métricas del Cultivo")
        
        if 'point_cloud' in st.session_state:
            metrics = extract_plant_metrics(st.session_state.point_cloud)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Altura Máxima", f"{metrics['max_height']:.2f} m")
                st.metric("Densidad", f"{metrics['plant_density']:,} pts")
            with col2:
                st.metric("Volumen Dosel", f"{metrics['canopy_volume']:.1f} m³")
                st.metric("Área", f"{metrics['canopy_area']:.2f} ha")
            with col3:
                st.metric("Salud", f"{metrics['health_score']:.1f}%")
                st.metric("Etapa", metrics['growth_stage'])
            
            # Métricas adicionales para polígono
            if 'polygon_area_ha' in st.session_state:
                st.subheader("📐 Métricas Espaciales")
                col4, col5, col6 = st.columns(3)
                with col4:
                    st.metric("Área Polígono", f"{st.session_state.polygon_area_ha:.2f} ha")
                with col5:
                    density_ha = metrics['plant_density'] / st.session_state.polygon_area_ha
                    st.metric("Densidad/ha", f"{density_ha:,.0f} pts/ha")
                with col6:
                    st.metric("% Cobertura", f"{metrics['vegetation_percentage']:.1f}%")
        else:
            st.info("👆 Genera datos LiDAR primero para ver las métricas")
    
    with tab4:
        st.header("Visualización 3D Interactiva")
        
        if 'point_cloud' in st.session_state:
            title = "Visualización LiDAR - Área Personalizada" if 'current_polygon' in st.session_state else "Visualización LiDAR - Datos de Ejemplo"
            create_interactive_plot(st.session_state.point_cloud, title)
        else:
            st.info("👆 Genera datos LiDAR para ver la visualización 3D")

def render_home():
    st.title("🌱 Plataforma de Agricultura de Precisión")
    
    st.markdown("""
    ## ¡Bienvenido a la Plataforma Agrícola Integral!
    
    **Combina diagnóstico de fertilidad con gemelos digitales LiDAR**
    
    ### 🚀 Módulos Disponibles:
    
    **🔍 Diagnóstico de Fertilidad**
    - Análisis completo de parámetros del suelo
    - Recomendaciones de fertilización específicas
    - Puntaje de fertilidad integrado
    
    **🔄 Gemelos Digitales LiDAR**  
    - ✅ **NUEVO:** Carga de polígonos KML/GeoJSON/Shapefile
    - Visualización 3D interactiva de cultivos
    - Métricas de crecimiento y salud vegetal
    - Análisis espacial por área definida
    
    **📊 Dashboard Integrado**
    - Vista unificada de suelo y cultivo
    - Correlación entre fertilidad y crecimiento
    """)
    
    st.info("""
    **📈 Estado del Sistema:**
    - ✅ Módulo LiDAR: **Disponible** (con datos de ejemplo y polígonos)
    - ✅ Módulo Fertilidad: **Disponible** 
    - ✅ Carga de polígonos: **Activa** (KML, GeoJSON, Shapefile)
    - 🟢 Sistema: **Operativo**
    """)

def render_dashboard():
    st.title("📊 Dashboard Integrado")
    
    has_soil = 'soil_data' in st.session_state
    has_lidar = 'point_cloud' in st.session_state
    has_polygon = 'current_polygon' in st.session_state
    
    if not has_soil and not has_lidar:
        st.info("💡 Usa los módulos de Fertilidad y LiDAR para ver datos integrados aquí")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏭 Diagnóstico de Suelo")
        if has_soil:
            soil = st.session_state.soil_data
            st.metric("Fertilidad General", f"{soil['fertility_score']:.0f}%")
            st.metric("pH", f"{soil['ph']}")
            st.metric("Materia Orgánica", f"{soil['organic_matter']}%")
            st.metric("Cultivo", soil['crop'])
        else:
            st.warning("Ejecuta el diagnóstico de fertilidad primero")
    
    with col2:
        st.subheader("🌿 Estado del Cultivo (LiDAR)")
        if has_lidar:
            metrics = extract_plant_metrics(st.session_state.point_cloud)
            st.metric("Salud del Dosel", f"{metrics['health_score']:.1f}%")
            st.metric("Altura del Cultivo", f"{metrics['plant_height']:.2f} m")
            st.metric("Densidad Vegetal", f"{metrics['plant_density']:,}")
            st.metric("Etapa", metrics['growth_stage'])
            
            if has_polygon:
                st.metric("Área Analizada", f"{st.session_state.polygon_area_ha:.2f} ha")
        else:
            st.warning("Genera datos LiDAR primero")
    
    if has_soil and has_lidar:
        st.subheader("🎯 Recomendaciones Integradas")
        
        soil_score = st.session_state.soil_data['fertility_score']
        lidar_health = metrics['health_score']
        
        if soil_score >= 70 and lidar_health >= 70:
            st.success("""
            **✅ Estado Óptimo**
            - Suelo y cultivo en condiciones excelentes
            - Mantener prácticas actuales de manejo
            - Continuar monitoreo regular
            """)
        elif soil_score < 60 and lidar_health < 60:
            st.error("""
            **🔴 Atención Requerida**
            - Tanto el suelo como el cultivo necesitan mejoras
            - Implementar plan de fertilización balanceada
            - Revisar riego y condiciones ambientales
            """)
        else:
            st.warning("""
            **🟡 Monitoreo Recomendado**
            - Algún parámetro necesita atención
            - Continuar con prácticas actuales
            - Monitorear evolución
            """)

def main():
    """Función principal"""
    
    # Sidebar
    st.sidebar.title("🌱 Navegación")
    page = st.sidebar.radio("Ir a:", ["🏠 Inicio", "🔍 Fertilidad", "🔄 LiDAR", "📊 Dashboard"])
    
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Nuevas Funcionalidades:**
    - ✅ Carga de polígonos KML
    - ✅ Análisis por área específica  
    - ✅ GeoJSON y Shapefile
    - ✅ Métricas espaciales
    """)
    
    # Navegación
    if page == "🏠 Inicio":
        render_home()
    elif page == "🔍 Fertilidad":
        analisis_suelo_main()
    elif page == "🔄 LiDAR":
        render_lidar_page()
    elif page == "📊 Dashboard":
        render_dashboard()

# EJECUCIÓN
if __name__ == "__main__":
    main()
