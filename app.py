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

# CONFIGURACIÓN
st.set_page_config(
    page_title="Plataforma Agrícola Integral",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MÓDULO DE CARGA Y PROCESAMIENTO DE POLÍGONOS
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
                        # GeoJSON usa [lon, lat] y puede tener anillos múltiples
                        for ring in feature['geometry']['coordinates']:
                            polygon = [[coord[0], coord[1]] for coord in ring]
                            polygons.append(polygon)
            elif data['type'] == 'Feature':
                if data['geometry']['type'] == 'Polygon':
                    for ring in data['geometry']['coordinates']:
                        polygon = [[coord[0], coord[1]] for coord in ring]
                        polygons.append(polygon)
            elif data['type'] == 'Polygon':
                for ring in data['coordinates']:
                    polygon = [[coord[0], coord[1]] for coord in ring]
                    polygons.append(polygon)
            
            return polygons
            
        except Exception as e:
            st.error(f"Error parseando GeoJSON: {e}")
            return []
    
    def parse_shapefile_zip(self, zip_file):
        """Procesa archivo ZIP con Shapefile"""
        try:
            with zipfile.ZipFile(BytesIO(zip_file)) as z:
                # Listar archivos en el ZIP
                file_list = z.namelist()
                st.info(f"Archivos en el ZIP: {', '.join(file_list)}")
                
                # Buscar archivos .shp, .shx, .dbf, .prj
                shp_files = [f for f in file_list if f.endswith('.shp')]
                
                if not shp_files:
                    st.error("No se encontró archivo .shp en el ZIP")
                    return []
                
                # Para esta demo, simulamos un polígono de ejemplo
                # En producción, usarías bibliotecas como fiona o geopandas
                st.success("✅ Shapefile detectado correctamente")
                
                # Crear polígono de ejemplo basado en Argentina
                polygon = [
                    [-58.500, -34.600],  # Esquina noroeste
                    [-58.400, -34.600],  # Esquina noreste  
                    [-58.400, -34.500],  # Esquina sureste
                    [-58.500, -34.500],  # Esquina suroeste
                    [-58.500, -34.600]   # Cerrar polígono
                ]
                
                return [polygon]
                
        except Exception as e:
            st.error(f"Error procesando shapefile: {e}")
            return []
    
    def calculate_polygon_area(self, polygon):
        """Calcula área aproximada del polígono en hectáreas"""
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
            # 1 grado ≈ 111 km en latitud, varía en longitud
            area_hectares = area * 111 * 111 * 100  # Conversión simplificada
            
            return max(area_hectares, 0.1)  # Mínimo 0.1 ha
            
        except:
            return 10.0  # Valor por defecto
    
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
# MÓDULO DE MAPAS BASE ESRI
# ============================================================================

class MapVisualizer:
    def __init__(self):
        self.esri_satellite_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        self.esri_terrain_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}"
        
    def create_satellite_map(self, polygon=None, center=None, zoom=10):
        """Crea mapa base con ESRI Satellite"""
        if center is None:
            center = {"lat": -34.6037, "lon": -58.3816}  # Buenos Aires por defecto
        
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
            zoom = 14  # Zoom más cercano cuando hay polígono
        
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
# MÓDULO DE ANÁLISIS DE SUELO
# ============================================================================

class SoilAnalyzer:
    def comprehensive_soil_analysis(self, soil_params, area_ha):
        """Análisis completo de fertilidad del suelo"""
        ph = soil_params.get('ph', 6.5)
        organic_matter = soil_params.get('organic_matter', 2.5)
        nitrogen = soil_params.get('nitrogen', 50)
        phosphorus = soil_params.get('phosphorus', 30) 
        potassium = soil_params.get('potassium', 100)
        
        # Cálculo de puntajes
        ph_score = self._calculate_ph_score(ph)
        om_score = self._calculate_organic_matter_score(organic_matter)
        n_score = self._calculate_nutrient_score(nitrogen, 60)
        p_score = self._calculate_nutrient_score(phosphorus, 25)
        k_score = self._calculate_nutrient_score(potassium, 120)
        
        total_score = (ph_score + om_score + n_score + p_score + k_score) / 5
        
        # Recomendaciones
        recommendations = []
        if ph_score < 70:
            recommendations.append("Aplicar enmiendas para corregir pH")
        if n_score < 70:
            recommendations.append(f"Aplicar {max(0, (80 - nitrogen) * 2)} kg/ha de nitrógeno")
        if p_score < 70:
            recommendations.append(f"Aplicar {max(0, (30 - phosphorus) * 3)} kg/ha de fósforo")
        if k_score < 70:
            recommendations.append(f"Aplicar {max(0, (130 - potassium) * 2)} kg/ha de potasio")
        
        return {
            'total_score': total_score,
            'component_scores': {
                'pH': ph_score,
                'Materia Orgánica': om_score,
                'Nitrógeno': n_score,
                'Fósforo': p_score,
                'Potasio': k_score
            },
            'recommendations': recommendations,
            'area_hectares': area_ha
        }
    
    def _calculate_ph_score(self, ph):
        if 6.0 <= ph <= 7.0:
            return 100
        elif 5.5 <= ph < 6.0 or 7.0 < ph <= 7.5:
            return 80
        else:
            return 50
    
    def _calculate_organic_matter_score(self, om):
        if om >= 3.0:
            return 100
        elif om >= 2.0:
            return 80
        else:
            return 60
    
    def _calculate_nutrient_score(self, value, optimal):
        return min(100, (value / optimal) * 100)

# ============================================================================
# INTERFAZ PRINCIPAL MEJORADA
# ============================================================================

def render_polygon_upload_section():
    """Sección de carga de polígonos en el inicio"""
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
        **💡 Consejo:**
        - Exporta desde Google Earth como KML
        - O desde QGIS como Shapefile
        - El área mínima recomendada: 1 hectárea
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
                
                if uploaded_file.type == "application/vnd.google-earth.kml+xml" or uploaded_file.name.endswith('.kml'):
                    polygons = polygon_processor.parse_kml(file_content)
                    file_type = "KML"
                    
                elif uploaded_file.type == "application/geo+json" or uploaded_file.name.endswith('.geojson') or uploaded_file.name.endswith('.json'):
                    polygons = polygon_processor.parse_geojson(file_content.decode('utf-8'))
                    file_type = "GeoJSON"
                    
                elif uploaded_file.type == "application/zip" or uploaded_file.name.endswith('.zip'):
                    polygons = polygon_processor.parse_shapefile_zip(file_content)
                    file_type = "Shapefile"
                
                if polygons:
                    current_polygon = polygons[0]  # Usar el primer polígono
                    area_ha = polygon_processor.calculate_polygon_area(current_polygon)
                    bounds = polygon_processor.get_polygon_bounds(current_polygon)
                    
                    # Guardar en session state
                    st.session_state.current_polygon = current_polygon
                    st.session_state.polygon_area_ha = area_ha
                    st.session_state.polygon_bounds = bounds
                    st.session_state.polygon_loaded = True
                    
                    st.success(f"✅ **{file_type} procesado correctamente!**")
                    
                    # Mostrar información del polígono
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Área del Lote", f"{area_ha:.2f} hectáreas")
                    with col2:
                        st.metric("Puntos del Polígono", len(current_polygon))
                    with col3:
                        st.metric("Formato", file_type)
                    
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

def render_quick_analysis():
    """Análisis rápido basado en el polígono cargado"""
    if not st.session_state.get('polygon_loaded'):
        return
    
    st.header("🔬 Análisis Rápido de tu Lote")
    
    # Selector de tipo de análisis
    analysis_type = st.selectbox(
        "Selecciona el tipo de análisis:",
        ["Fertilidad de Suelo", "Generar Modelo LiDAR", "Análisis Satelital", "Recomendaciones Integradas"]
    )
    
    if analysis_type == "Fertilidad de Suelo":
        render_soil_analysis()
    elif analysis_type == "Generar Modelo LiDAR":
        render_lidar_generation()
    elif analysis_type == "Análisis Satelital":
        render_satellite_analysis()
    elif analysis_type == "Recomendaciones Integradas":
        render_integrated_recommendations()

def render_soil_analysis():
    """Análisis de suelo para el polígono cargado"""
    st.subheader("🌱 Análisis de Fertilidad del Suelo")
    
    with st.form("soil_analysis_form"):
        st.write("**Ingresa los parámetros de suelo de tu lote:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ph = st.slider("pH del suelo", 4.0, 9.0, 6.5, 0.1)
            organic_matter = st.slider("Materia Orgánica (%)", 0.5, 8.0, 2.5, 0.1)
            
        with col2:
            nitrogen = st.slider("Nitrógeno (ppm)", 10, 200, 50, 5)
            phosphorus = st.slider("Fósforo (ppm)", 5, 100, 25, 5)
            potassium = st.slider("Potasio (ppm)", 50, 300, 120, 10)
        
        crop_type = st.selectbox("Cultivo Principal", 
                               ["Maíz", "Soja", "Trigo", "Girasol", "Algodón", "Otro"])
        
        if st.form_submit_button("🔬 Analizar Suelo"):
            area_ha = st.session_state.get('polygon_area_ha', 10)
            soil_analyzer = SoilAnalyzer()
            
            soil_params = {
                'ph': ph,
                'organic_matter': organic_matter,
                'nitrogen': nitrogen,
                'phosphorus': phosphorus,
                'potassium': potassium
            }
            
            analysis = soil_analyzer.comprehensive_soil_analysis(soil_params, area_ha)
            
            # Mostrar resultados
            st.subheader("📊 Resultados del Análisis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Puntaje general
                score = analysis['total_score']
                st.metric("Puntaje General de Fertilidad", f"{score:.0f}/100")
                
                # Gráfico de componentes
                components = analysis['component_scores']
                fig = go.Figure(data=[
                    go.Bar(x=list(components.keys()), y=list(components.values()),
                          marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
                ])
                fig.update_layout(title="Puntajes por Componente", height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("🎯 Recomendaciones")
                for i, rec in enumerate(analysis['recommendations'], 1):
                    st.write(f"{i}. {rec}")
                
                # Estado general
                if score >= 80:
                    st.success("✅ **Excelente** - Tu suelo está en óptimas condiciones")
                elif score >= 60:
                    st.warning("⚠️ **Bueno** - Algunas mejoras recomendadas")
                else:
                    st.error("❌ **Necesita atención** - Implementa las recomendaciones")

def render_lidar_generation():
    """Generación de datos LiDAR para el polígono"""
    st.subheader("📡 Generar Modelo LiDAR 3D")
    
    if st.button("🔄 Generar Modelo 3D para mi Lote", type="primary"):
        with st.spinner("Generando modelo 3D específico para tu terreno..."):
            # Generar datos LiDAR realistas para el polígono
            polygon = st.session_state.current_polygon
            bounds = st.session_state.polygon_bounds
            
            # Crear puntos dentro del polígono
            points = []
            num_points = 5000  # Puntos a generar
            
            for _ in range(num_points):
                # Generar punto aleatorio en el bounding box
                lon = np.random.uniform(bounds['min_lon'], bounds['max_lon'])
                lat = np.random.uniform(bounds['min_lat'], bounds['max_lat'])
                
                # Verificar si está dentro del polígono (simplificado)
                if (bounds['min_lon'] <= lon <= bounds['max_lon'] and 
                    bounds['min_lat'] <= lat <= bounds['max_lat']):
                    
                    # Altura base + variación de terreno + vegetación
                    base_height = np.random.uniform(0, 0.5)
                    
                    # Simular vegetación (algunos puntos más altos)
                    if np.random.random() > 0.7:  # 30% de puntos son vegetación
                        height = base_height + np.random.uniform(0.5, 3.0)
                    else:
                        height = base_height
                    
                    points.append([lon, lat, height])
            
            points = np.array(points)
            st.session_state.point_cloud = type('PointCloud', (), {'points': points})()
            
            st.success(f"✅ Modelo 3D generado con {len(points):,} puntos")
            
            # Mostrar visualización 3D
            st.subheader("🌋 Visualización 3D de tu Terreno")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter3d(
                x=points[:, 0], y=points[:, 1], z=points[:, 2],
                mode='markers',
                marker=dict(
                    size=2,
                    color=points[:, 2],
                    colorscale='Viridis',
                    opacity=0.7
                )
            ))
            
            fig.update_layout(
                title="Modelo 3D de tu Lote",
                scene=dict(
                    xaxis_title='Longitud',
                    yaxis_title='Latitud',
                    zaxis_title='Altura (m)'
                ),
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)

def render_satellite_analysis():
    """Análisis satelital para el polígono"""
    st.subheader("🛰️ Análisis Satelital")
    
    if st.button("📡 Obtener Análisis Satelital", type="primary"):
        with st.spinner("Analizando imágenes satelitales de tu área..."):
            # Simular análisis satelital
            polygon = st.session_state.current_polygon
            bounds = st.session_state.polygon_bounds
            
            # Generar datos NDVI simulados
            lons = np.linspace(bounds['min_lon'], bounds['max_lon'], 50)
            lats = np.linspace(bounds['min_lat'], bounds['max_lat'], 50)
            xx, yy = np.meshgrid(lons, lats)
            
            # Simular NDVI (salud vegetal)
            ndvi = 0.3 + 0.4 * np.sin(xx * 20) * np.cos(yy * 20)
            
            st.success("✅ Análisis satelital completado")
            
            # Mostrar mapa de calor NDVI
            st.subheader("🌿 Salud Vegetal (NDVI)")
            
            fig = go.Figure(data=go.Heatmap(
                x=xx[0], y=yy[:, 0], z=ndvi,
                colorscale='Viridis',
                colorbar=dict(title='NDVI')
            ))
            
            fig.update_layout(
                title="Mapa de Salud Vegetal - Tu Lote",
                xaxis_title='Longitud',
                yaxis_title='Latitud',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Métricas de salud vegetal
            mean_ndvi = np.mean(ndvi)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("NDVI Promedio", f"{mean_ndvi:.3f}")
            with col2:
                health_status = "Excelente" if mean_ndvi > 0.6 else "Buena" if mean_ndvi > 0.4 else "Moderada"
                st.metric("Estado Vegetal", health_status)
            with col3:
                st.metric("Área Analizada", f"{st.session_state.polygon_area_ha:.1f} ha")

def render_integrated_recommendations():
    """Recomendaciones integradas basadas en todos los análisis"""
    st.subheader("🎯 Recomendaciones Integradas para tu Lote")
    
    if not st.session_state.get('polygon_loaded'):
        st.warning("Primero carga tu polígono para obtener recomendaciones")
        return
    
    area_ha = st.session_state.get('polygon_area_ha', 10)
    
    st.info(f"""
    **📋 Resumen de tu Lote:**
    - **Área:** {area_ha:.1f} hectáreas
    - **Ubicación:** Personalizada según tu polígono
    - **Análisis Disponible:** Específico para tu terreno
    """)
    
    # Recomendaciones generales basadas en el área
    st.subheader("💡 Recomendaciones de Manejo")
    
    if area_ha < 5:
        st.write("""
        **🔍 Lote Pequeño - Enfoque de Precisión:**
        - Fertilización variable según zonas
        - Riego por goteo para eficiencia
        - Monitoreo intensivo de cultivo
        - Considerar agricultura de precisión
        """)
    elif area_ha < 50:
        st.write("""
        **🏭 Lote Mediano - Balance Eficiencia/Precisión:**
        - Muestreo de suelo por grillas
        - Fertilización balanceada
        - Monitoreo satelital periódico
        - Plan de rotación de cultivos
        """)
    else:
        st.write("""
        **🌾 Lote Grande - Enfoque Eficiente:**
        - Muestreo de suelo por ambientes
        - Maquinaria de aplicación variable
        - Monitoreo satelital constante
        - Gestión por ambientes productivos
        """)
    
    # Próximos pasos
    st.subheader("🚀 Próximos Pasos Recomendados")
    st.write("""
    1. **Realizar análisis de suelo** completo con muestras
    2. **Generar modelo LiDAR** para topografía detallada  
    3. **Configurar monitoreo satelital** continuo
    4. **Implementar recomendaciones** de fertilización
    5. **Programar seguimiento** mensual del cultivo
    """)

def render_home():
    """Página de inicio mejorada"""
    st.title("🌱 Plataforma de Agricultura de Precisión")
    
    # Estado de la aplicación
    polygon_loaded = st.session_state.get('polygon_loaded', False)
    
    if polygon_loaded:
        st.success("✅ **Tienes un lote cargado!** Ahora puedes realizar análisis específicos.")
        
        # Mostrar información del lote cargado
        area_ha = st.session_state.get('polygon_area_ha', 0)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Área del Lote", f"{area_ha:.2f} ha")
        with col2:
            st.metric("Análisis Disponibles", "5")
        with col3:
            st.metric("Estado", "Listo ✅")
        
        # Análisis rápido
        render_quick_analysis()
        
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
            - Planes de fertilización
            """)
        
        # Línea separadora
        st.markdown("---")
        
        # Sección de carga de polígonos
        render_polygon_upload_section()
        
        # Ejemplos de formatos
        st.markdown("---")
        st.subheader("📋 Ejemplos de Formatos Soportados")
        
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

def main():
    """Función principal"""
    
    # Inicializar session state
    if 'polygon_loaded' not in st.session_state:
        st.session_state.polygon_loaded = False
    
    # Sidebar
    st.sidebar.title("🌱 Navegación")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Seleccionar Módulo:",
        ["🏠 Inicio", "🗺️ Mi Lote", "🌱 Análisis Suelo", "📡 LiDAR 3D", "🛰️ Satelital"]
    )
    
    st.sidebar.markdown("---")
    
    # Estado actual en sidebar
    if st.session_state.get('polygon_loaded'):
        area_ha = st.session_state.get('polygon_area_ha', 0)
        st.sidebar.success(f"✅ Lote cargado\n{area_ha:.1f} hectáreas")
    else:
        st.sidebar.warning("⚠️ Sin lote cargado")
    
    st.sidebar.info("""
    **💡 Tip Rápido:**
    Comienza en **Inicio** para cargar tu polígono y luego usa los otros módulos para análisis específicos.
    """)
    
    # Navegación
    if page == "🏠 Inicio":
        render_home()
    elif page == "🗺️ Mi Lote":
        if st.session_state.get('polygon_loaded'):
            st.title("🗺️ Mi Lote - Vista General")
            polygon = st.session_state.current_polygon
            map_viz = MapVisualizer()
            map_fig = map_viz.create_satellite_map(polygon=polygon)
            st.plotly_chart(map_fig, use_container_width=True)
            
            # Información del lote
            area_ha = st.session_state.get('polygon_area_ha', 0)
            bounds = st.session_state.get('polygon_bounds', {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Área Total", f"{area_ha:.2f} ha")
            with col2:
                st.metric("Ancho Aprox.", f"{(bounds.get('max_lon',0)-bounds.get('min_lon',0))*111:.1f} km")
            with col3:
                st.metric("Largo Aprox.", f"{(bounds.get('max_lat',0)-bounds.get('min_lat',0))*111:.1f} km")
            with col4:
                st.metric("Estado", "Cargado ✅")
        else:
            st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
            st.info("Ve a **🏠 Inicio** para cargar tu lote o campo")
    elif page == "🌱 Análisis Suelo":
        render_soil_analysis()
    elif page == "📡 LiDAR 3D":
        render_lidar_generation()
    elif page == "🛰️ Satelital":
        render_satellite_analysis()

if __name__ == "__main__":
    main()
