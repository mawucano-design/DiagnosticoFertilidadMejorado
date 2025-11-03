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

# CONFIGURACIÓN
st.set_page_config(
    page_title="Plataforma Agrícola Integral",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MÓDULO SENTINEL-2 Y ANÁLISIS MULTIESPECTRAL
# ============================================================================

class SentinelAnalyzer:
    def __init__(self):
        self.ndvi_data = None
        self.ndwi_data = None
        self.ndre_data = None
        
    def calculate_ndvi(self, red_band, nir_band):
        """Calcula NDVI (Normalized Difference Vegetation Index)"""
        return (nir_band - red_band) / (nir_band + red_band + 1e-8)
    
    def calculate_ndwi(self, green_band, nir_band):
        """Calcula NDWI (Normalized Difference Water Index)"""
        return (green_band - nir_band) / (green_band + nir_band + 1e-8)
    
    def calculate_ndre(self, nir_band, red_edge_band):
        """Calcula NDRE (Normalized Difference Red Edge)"""
        return (nir_band - red_edge_band) / (nir_band + red_edge_band + 1e-8)
    
    def generate_sentinel_data(self, polygon, resolution=100):
        """Genera datos simulados de Sentinel-2 para un polígono"""
        if not polygon:
            return None
            
        # Crear grid dentro del polígono
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        # Generar datos multiespectrales simulados
        x_coords = np.linspace(min_lon, max_lon, resolution)
        y_coords = np.linspace(min_lat, max_lat, resolution)
        xx, yy = np.meshgrid(x_coords, y_coords)
        
        # Simular bandas espectrales
        np.random.seed(42)
        
        # Banda Roja (B4)
        red_band = 0.2 + 0.1 * np.sin(xx * 10) + 0.1 * np.cos(yy * 10)
        
        # Banda Infrarrojo Cercano (B8)
        nir_band = 0.3 + 0.2 * np.sin(xx * 8) + 0.15 * np.cos(yy * 8)
        
        # Banda Verde (B3)
        green_band = 0.25 + 0.1 * np.sin(xx * 12) + 0.1 * np.cos(yy * 12)
        
        # Banda Red Edge (B5)
        red_edge_band = 0.22 + 0.12 * np.sin(xx * 9) + 0.1 * np.cos(yy * 9)
        
        # Calcular índices
        ndvi = self.calculate_ndvi(red_band, nir_band)
        ndwi = self.calculate_ndwi(green_band, nir_band)
        ndre = self.calculate_ndre(nir_band, red_edge_band)
        
        return {
            'coordinates': (xx, yy),
            'ndvi': ndvi,
            'ndwi': ndwi,
            'ndre': ndre,
            'red_band': red_band,
            'nir_band': nir_band,
            'green_band': green_band,
            'red_edge_band': red_edge_band
        }
    
    def analyze_vegetation_health(self, sentinel_data):
        """Analiza salud de la vegetación basado en índices espectrales"""
        if sentinel_data is None:
            return {}
            
        ndvi = sentinel_data['ndvi']
        ndre = sentinel_data['ndre']
        ndwi = sentinel_data['ndwi']
        
        # Análisis de salud
        mean_ndvi = np.mean(ndvi)
        mean_ndre = np.mean(ndre)
        mean_ndwi = np.mean(ndwi)
        
        # Clasificar salud basado en NDVI
        if mean_ndvi > 0.6:
            health_status = "Excelente"
            health_score = 90
        elif mean_ndvi > 0.4:
            health_status = "Buena"
            health_score = 75
        elif mean_ndvi > 0.2:
            health_status = "Moderada"
            health_score = 60
        else:
            health_status = "Pobre"
            health_score = 40
            
        # Detectar estrés hídrico
        water_stress = "Bajo" if mean_ndwi > -0.1 else "Moderado" if mean_ndwi > -0.3 else "Alto"
        
        # Nutrientes (basado en NDRE)
        nutrient_status = "Óptimo" if mean_ndre > 0.3 else "Adecuado" if mean_ndre > 0.2 else "Deficiente"
        
        return {
            'health_score': health_score,
            'health_status': health_status,
            'mean_ndvi': float(mean_ndvi),
            'mean_ndre': float(mean_ndre),
            'mean_ndwi': float(mean_ndwi),
            'water_stress': water_stress,
            'nutrient_status': nutrient_status,
            'biomass_estimate': float(mean_ndvi * 1000)  # kg/ha estimado
        }

# ============================================================================
# MÓDULO DE ANÁLISIS DE FERTILIDAD INTEGRADO
# ============================================================================

class AdvancedSoilAnalyzer:
    def __init__(self):
        self.soil_data = None
        
    def comprehensive_soil_analysis(self, soil_params, polygon_area=None):
        """Análisis completo de fertilidad del suelo"""
        # Parámetros básicos
        ph = soil_params.get('ph', 6.5)
        organic_matter = soil_params.get('organic_matter', 2.5)
        nitrogen = soil_params.get('nitrogen', 50)
        phosphorus = soil_params.get('phosphorus', 30)
        potassium = soil_params.get('potassium', 100)
        texture = soil_params.get('texture', 'Franco')
        crop = soil_params.get('crop', 'Maíz')
        
        # Cálculo de puntajes individuales
        ph_score = self._calculate_ph_score(ph, crop)
        om_score = self._calculate_organic_matter_score(organic_matter, texture)
        n_score = self._calculate_nitrogen_score(nitrogen, crop)
        p_score = self._calculate_phosphorus_score(phosphorus, crop)
        k_score = self._calculate_potassium_score(potassium, crop)
        
        # Puntaje integrado con pesos
        total_score = (
            ph_score * 0.15 +
            om_score * 0.20 +
            n_score * 0.25 +
            p_score * 0.20 +
            k_score * 0.20
        )
        
        # Recomendaciones de fertilización
        recommendations = self._generate_fertilization_recommendations(
            ph_score, om_score, n_score, p_score, k_score, crop, polygon_area
        )
        
        # Análisis de productividad potencial
        productivity = self._estimate_productivity(total_score, crop, polygon_area)
        
        return {
            'total_score': total_score,
            'component_scores': {
                'ph': ph_score,
                'organic_matter': om_score,
                'nitrogen': n_score,
                'phosphorus': p_score,
                'potassium': k_score
            },
            'recommendations': recommendations,
            'productivity_estimate': productivity,
            'soil_health_category': self._categorize_soil_health(total_score)
        }
    
    def _calculate_ph_score(self, ph, crop):
        rangos_optimos = {
            "Maíz": (5.8, 7.0), "Soja": (6.0, 7.0), "Trigo": (6.0, 7.5),
            "Girasol": (6.0, 7.5), "Algodón": (5.5, 7.0)
        }
        optimo = rangos_optimos.get(crop, (6.0, 7.0))
        
        if optimo[0] <= ph <= optimo[1]:
            return 100
        elif ph < 4.5 or ph > 8.5:
            return 20
        else:
            # Puntaje decreciente hacia los extremos
            distance = min(abs(ph - optimo[0]), abs(ph - optimo[1]))
            return max(40, 100 - distance * 20)
    
    def _calculate_organic_matter_score(self, om, texture):
        objetivos = {"Arenoso": 3.0, "Franco": 4.0, "Arcilloso": 5.0}
        objetivo = objetivos.get(texture, 3.5)
        
        if om >= objetivo:
            return 100
        elif om >= objetivo * 0.7:
            return 80
        elif om >= objetivo * 0.5:
            return 60
        else:
            return 40
    
    def _calculate_nitrogen_score(self, nitrogen, crop):
        rangos = {"Maíz": 60, "Soja": 40, "Trigo": 50, "Girasol": 35, "Algodón": 55}
        objetivo = rangos.get(crop, 50)
        
        return min(100, nitrogen / objetivo * 100)
    
    def _calculate_phosphorus_score(self, phosphorus, crop):
        rangos = {"Maíz": 25, "Soja": 20, "Trigo": 22, "Girasol": 18, "Algodón": 24}
        objetivo = rangos.get(crop, 22)
        
        return min(100, phosphorus / objetivo * 100)
    
    def _calculate_potassium_score(self, potassium, crop):
        rangos = {"Maíz": 120, "Soja": 100, "Trigo": 110, "Girasol": 90, "Algodón": 115}
        objetivo = rangos.get(crop, 105)
        
        return min(100, potassium / objetivo * 100)
    
    def _generate_fertilization_recommendations(self, ph_score, om_score, n_score, p_score, k_score, crop, area_ha):
        recommendations = []
        
        if ph_score < 70:
            recommendations.append({
                'type': 'Corrección',
                'producto': 'Cal agrícola' if ph_score < 50 else 'Enmienda correctiva',
                'dosis': f"{2-4 if ph_score < 50 else 1-2} ton/ha",
                'prioridad': 'Alta'
            })
        
        if n_score < 70:
            dosis_base = {"Maíz": 120, "Soja": 0, "Trigo": 80, "Girasol": 60, "Algodón": 90}
            dosis = max(0, dosis_base.get(crop, 80) * (1 - n_score/100))
            if dosis > 0:
                recommendations.append({
                    'type': 'Nitrógeno',
                    'producto': 'Urea o Nitrato de amonio',
                    'dosis': f"{dosis:.0f} kg N/ha",
                    'prioridad': 'Alta' if n_score < 50 else 'Media'
                })
        
        if p_score < 70:
            dosis_base = {"Maíz": 60, "Soja": 40, "Trigo": 50, "Girasol": 35, "Algodón": 55}
            dosis = dosis_base.get(crop, 45) * (1 - p_score/100)
            recommendations.append({
                'type': 'Fósforo',
                'producto': 'Superfosfato triple',
                'dosis': f"{dosis:.0f} kg P₂O₅/ha",
                'prioridad': 'Media'
            })
        
        if k_score < 70:
            dosis_base = {"Maíz": 80, "Soja": 60, "Trigo": 70, "Girasol": 50, "Algodón": 75}
            dosis = dosis_base.get(crop, 65) * (1 - k_score/100)
            recommendations.append({
                'type': 'Potasio',
                'producto': 'Cloruro de potasio',
                'dosis': f"{dosis:.0f} kg K₂O/ha",
                'prioridad': 'Media'
            })
        
        if om_score < 70:
            recommendations.append({
                'type': 'Materia Orgánica',
                'producto': 'Compost o abonos verdes',
                'dosis': '5-10 ton/ha',
                'prioridad': 'Media-Alta'
            })
        
        # Calcular costos estimados si hay área
        if area_ha:
            total_cost = self._estimate_fertilization_cost(recommendations, area_ha)
            for rec in recommendations:
                rec['costo_estimado'] = f"${total_cost/len(recommendations):.0f}/ha"
        
        return recommendations
    
    def _estimate_fertilization_cost(self, recommendations, area_ha):
        # Costos aproximados por tipo de producto
        costos = {
            'Corrección': 50, 'Nitrógeno': 300, 'Fósforo': 400, 
            'Potasio': 350, 'Materia Orgánica': 150
        }
        total = 0
        for rec in recommendations:
            total += costos.get(rec['type'], 200) * area_ha
        return total
    
    def _estimate_productivity(self, soil_score, crop, area_ha):
        # Rendimientos potenciales base (kg/ha)
        rendimientos_base = {
            "Maíz": 8000, "Soja": 3000, "Trigo": 4000, 
            "Girasol": 2000, "Algodón": 1500
        }
        
        base = rendimientos_base.get(crop, 3000)
        factor_suelo = soil_score / 100
        
        # Ajustar por calidad de suelo
        rendimiento_estimado = base * factor_suelo
        
        if area_ha:
            return {
                'rendimiento_ha': rendimiento_estimado,
                'rendimiento_total': rendimiento_estimado * area_ha,
                'unidad': 'kg/ha'
            }
        else:
            return {'rendimiento_ha': rendimiento_estimado, 'unidad': 'kg/ha'}
    
    def _categorize_soil_health(self, score):
        if score >= 80: return "Excelente"
        elif score >= 70: return "Buena"
        elif score >= 60: return "Moderada"
        elif score >= 50: return "Regular"
        else: return "Pobre"

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

# ============================================================================
# MÓDULO LIDAR
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
            points = self._generate_points_in_polygon(polygon, 5000)
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
                z = 0.1 * np.sin(center_x) * np.cos(center_y) + height
                points.append([center_x + dx, center_y + dy, z])
        
        points = np.array(points)
        self.point_cloud = type('PointCloud', (), {})()
        self.point_cloud.points = points
        return self.point_cloud
    
    def _generate_points_in_polygon(self, polygon, num_points):
        """Genera puntos dentro de un polígono"""
        if not polygon:
            return None
            
        # Calcular bounding box
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        points = []
        while len(points) < num_points:
            lon = np.random.uniform(min_lon, max_lon)
            lat = np.random.uniform(min_lat, max_lat)
            
            # Verificación simple de punto en polígono
            if self._point_in_polygon(lon, lat, polygon):
                # Altura base + variación
                base_height = np.random.uniform(0, 0.3)
                # Algunos puntos son vegetación
                if np.random.random() > 0.7:
                    height = base_height + np.random.uniform(0.5, 2.5)
                else:
                    height = base_height
                points.append([lon, lat, height])
        
        return np.array(points)
    
    def _point_in_polygon(self, x, y, poly):
        """Verifica si un punto está dentro de un polígono"""
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
    
    # Calcular área aproximada
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
            marker=dict(size=2, color='brown', opacity=0.6),
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
                size=3, 
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
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

def render_home():
    st.title("🌱 Plataforma de Agricultura de Precisión")
    
    st.markdown("""
    ## ¡Bienvenido a la Plataforma Agrícola Integral!
    
    **Combina diagnóstico de fertilidad con gemelos digitales LiDAR y análisis satelital**
    
    ### 🚀 Módulos Disponibles:
    
    **🌱 Análisis de Suelo Avanzado**
    - Diagnóstico completo de fertilidad
    - Recomendaciones de fertilización con costos
    - Estimación de rendimientos
    - Plan de manejo integrado
    
    **🔄 Gemelos Digitales LiDAR**  
    - Carga de polígonos KML/GeoJSON/Shapefile
    - Generación de datos LiDAR 3D
    - Análisis topográfico y de vegetación
    - Métricas espaciales precisas
    
    **🔬 Análisis Integrado**
    - Combinación LiDAR + Sentinel-2
    - Mapas de NDVI, NDWI, NDRE
    - Salud vegetal y estrés hídrico
    - Dashboard unificado
    
    **📊 Dashboard de Gestión**
    - Vista consolidada de todos los datos
    - Tendencias y correlaciones
    - Decisiones basadas en datos
    """)
    
    st.info("""
    **📈 Estado del Sistema:**
    - ✅ Módulo Suelo: **Disponible** 
    - ✅ Módulo LiDAR: **Disponible** 
    - ✅ Análisis Satelital: **Disponible**
    - ✅ Carga de polígonos: **Activa**
    - 🟢 Sistema: **Operativo**
    """)

def render_polygon_upload():
    """Interfaz para carga de polígonos"""
    st.header("🗺️ Cargar Polígono de Análisis")
    
    uploaded_file = st.file_uploader(
        "Seleccionar archivo geográfico (KML, GeoJSON, ZIP)",
        type=['kml', 'kmz', 'geojson', 'json', 'zip'],
        key="polygon_uploader"
    )
    
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
                current_polygon = polygons[0]
                area_ha = polygon_processor.calculate_polygon_area(current_polygon)
                
                st.info(f"**📐 Área del polígono:** {area_ha:.2f} hectáreas")
                
                # Mostrar preview del polígono
                st.subheader("📊 Vista previa del Polígono")
                poly_df = pd.DataFrame(current_polygon, columns=['Longitud', 'Latitud'])
                poly_df = pd.concat([poly_df, poly_df.iloc[[0]]])
                
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
                
                st.session_state.current_polygon = current_polygon
                st.session_state.polygon_area_ha = area_ha
                
        except Exception as e:
            st.error(f"❌ Error procesando archivo: {e}")
    
    return current_polygon

def render_lidar_page():
    st.title("🔄 Gemelos Digitales LiDAR")
    
    tab1, tab2, tab3 = st.tabs(["🗺️ Polígono", "📤 Datos LiDAR", "📊 Métricas"])
    
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
        st.header("Visualización y Métricas")
        
        if 'point_cloud' in st.session_state:
            # Visualización
            title = "Visualización LiDAR - Área Personalizada" if 'current_polygon' in st.session_state else "Visualización LiDAR - Datos de Ejemplo"
            create_interactive_plot(st.session_state.point_cloud, title)
            
            # Métricas
            metrics = extract_plant_metrics(st.session_state.point_cloud)
            
            st.subheader("📈 Métricas del Cultivo")
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
        else:
            st.info("👆 Genera datos LiDAR primero para ver la visualización y métricas")

def render_soil_analysis_main():
    """Módulo principal de análisis de suelo"""
    st.title("🌱 Análisis de Fertilidad del Suelo")
    
    st.markdown("""
    **Diagnóstico completo de fertilidad con recomendaciones específicas por lote**
    """)
    
    with st.form("advanced_soil_analysis"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Parámetros Básicos del Suelo")
            ph = st.slider("pH del suelo", 3.0, 9.0, 6.5, 0.1)
            materia_organica = st.slider("Materia Orgánica (%)", 0.1, 10.0, 2.5, 0.1)
            textura = st.selectbox("Textura del Suelo", ["Arcilloso", "Franco", "Arenoso"])
            
        with col2:
            st.subheader("Nutrientes Principales (ppm)")
            nitrogeno = st.slider("Nitrógeno (N)", 0, 200, 50, key="n_slider")
            fosforo = st.slider("Fósforo (P)", 0, 150, 30, key="p_slider")
            potasio = st.slider("Potasio (K)", 0, 300, 100, key="k_slider")
        
        st.subheader("Configuración del Análisis")
        col3, col4 = st.columns(2)
        with col3:
            cultivo = st.selectbox("Cultivo Principal", 
                                 ["Maíz", "Soja", "Trigo", "Girasol", "Algodón", "Otro"])
        with col4:
            area_ha = st.number_input("Área del lote (hectáreas)", 
                                    min_value=1.0, max_value=1000.0, value=50.0, step=1.0)
        
        if st.form_submit_button("🔬 Realizar Análisis Completo"):
            # Realizar análisis avanzado
            soil_analyzer = AdvancedSoilAnalyzer()
            soil_params = {
                'ph': ph, 'organic_matter': materia_organica, 'texture': textura,
                'nitrogen': nitrogeno, 'phosphorus': fosforo, 'potassium': potasio,
                'crop': cultivo
            }
            
            analysis_result = soil_analyzer.comprehensive_soil_analysis(soil_params, area_ha)
            
            # Guardar resultados
            st.session_state.soil_analysis = analysis_result
            st.session_state.soil_recommendations = analysis_result['recommendations']
            st.session_state.soil_params = soil_params
            
            # Mostrar resultados
            show_advanced_soil_results(analysis_result, area_ha)

def show_advanced_soil_results(analysis, area_ha):
    """Muestra resultados detallados del análisis de suelo"""
    
    st.header("📊 Resultados del Análisis de Fertilidad")
    
    # Puntaje general
    total_score = analysis['total_score']
    st.subheader(f"Puntaje General de Fertilidad: {total_score:.0f}/100")
    
    # Barra de progreso mejorada
    color = "red" if total_score < 50 else "orange" if total_score < 70 else "green"
    st.markdown(f"""
    <div style="background: #f0f0f0; border-radius: 10px; padding: 3px; margin: 10px 0;">
        <div style="background: {color}; width: {total_score}%; height: 30px; 
                    border-radius: 8px; text-align: center; color: white; 
                    line-height: 30px; font-weight: bold; font-size: 16px;">
            {total_score:.0f}% - {analysis['soil_health_category']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas detalladas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Puntajes por Componente")
        for component, score in analysis['component_scores'].items():
            component_name = {
                'ph': 'pH', 'organic_matter': 'Materia Orgánica',
                'nitrogen': 'Nitrógeno', 'phosphorus': 'Fósforo', 'potassium': 'Potasio'
            }.get(component, component)
            
            st.metric(component_name, f"{score:.0f}%")
    
    with col2:
        st.subheader("🌾 Estimación de Productividad")
        productivity = analysis['productivity_estimate']
        st.metric("Rendimiento Esperado", f"{productivity['rendimiento_ha']:.0f} {productivity['unidad']}")
        if 'rendimiento_total' in productivity:
            st.metric("Producción Total Estimada", f"{productivity['rendimiento_total']:.0f} kg")
        st.metric("Categoría de Salud", analysis['soil_health_category'])
    
    # Recomendaciones detalladas
    st.header("🎯 Plan de Fertilización Recomendado")
    
    if analysis['recommendations']:
        for i, rec in enumerate(analysis['recommendations'], 1):
            priority_color = {
                'Alta': '🔴', 'Media-Alta': '🟠', 'Media': '🟡', 'Baja': '🟢'
            }.get(rec['prioridad'], '⚪')
            
            st.write(f"""
            {priority_color} **{i}. {rec['type']}** - *{rec['prioridad']}*
            - **Producto**: {rec['producto']}
            - **Dosis**: {rec['dosis']}
            - **Costo estimado**: {rec.get('costo_estimado', 'No calculado')}
            """)
    else:
        st.success("✅ No se requieren correcciones inmediatas. Mantener prácticas actuales.")

def render_advanced_analysis():
    """Análisis integrado LiDAR + Sentinel-2 + Suelo"""
    st.title("🔬 Análisis Integrado Avanzado")
    
    st.markdown("""
    **Análisis completo que combina:** 
    - 🛰️ **Imágenes Sentinel-2** para salud vegetal
    - 📡 **Datos LiDAR** para topografía 3D  
    - 🌱 **Análisis de suelo** para fertilidad
    - 💧 **Monitoreo hídrico** y nutricional
    """)
    
    # Verificar datos disponibles
    has_polygon = 'current_polygon' in st.session_state
    has_lidar = 'point_cloud' in st.session_state
    has_soil = 'soil_analysis' in st.session_state
    
    if not has_polygon:
        st.warning("⚠️ Primero carga un polígono en el módulo LiDAR para realizar análisis avanzado")
        return
    
    # Generar datos Sentinel-2
    if st.button("🛰️ Generar Análisis Satelital", key="generate_sentinel"):
        with st.spinner("Generando análisis multiespectral..."):
            sentinel_analyzer = SentinelAnalyzer()
            sentinel_data = sentinel_analyzer.generate_sentinel_data(
                st.session_state.current_polygon
            )
            vegetation_health = sentinel_analyzer.analyze_vegetation_health(sentinel_data)
            
            st.session_state.sentinel_data = sentinel_data
            st.session_state.vegetation_health = vegetation_health
            st.success("✅ Análisis satelital completado")
    
    # Mostrar resultados integrados
    if 'sentinel_data' in st.session_state and 'vegetation_health' in st.session_state:
        sentinel_data = st.session_state.sentinel_data
        vegetation_health = st.session_state.vegetation_health
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Salud Vegetal", vegetation_health['health_status'])
        with col2:
            st.metric("NDVI Promedio", f"{vegetation_health['mean_ndvi']:.3f}")
        with col3:
            st.metric("Estrés Hídrico", vegetation_health['water_stress'])
        with col4:
            st.metric("Estado Nutricional", vegetation_health['nutrient_status'])
        
        # Mapas de índices
        st.subheader("🗺️ Mapas de Índices Espectrales")
        
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=('NDVI - Salud Vegetal', 'NDWI - Estrés Hídrico', 'NDRE - Estado Nutricional'),
            specs=[[{'type': 'heatmap'}, {'type': 'heatmap'}, {'type': 'heatmap'}]]
        )
        
        xx, yy = sentinel_data['coordinates']
        
        # NDVI
        fig.add_trace(
            go.Heatmap(
                x=xx[0], y=yy[:, 0], z=sentinel_data['ndvi'],
                colorscale='Viridis', name='NDVI',
                colorbar=dict(title='NDVI', x=0.3)
            ), row=1, col=1
        )
        
        # NDWI
        fig.add_trace(
            go.Heatmap(
                x=xx[0], y=yy[:, 0], z=sentinel_data['ndwi'],
                colorscale='Blues', name='NDWI',
                colorbar=dict(title='NDWI', x=0.63)
            ), row=1, col=2
        )
        
        # NDRE
        fig.add_trace(
            go.Heatmap(
                x=xx[0], y=yy[:, 0], z=sentinel_data['ndre'],
                colorscale='Greens', name='NDRE',
                colorbar=dict(title='NDRE', x=1.0)
            ), row=1, col=3
        )
        
        fig.update_layout(height=400, title_text="Análisis Multiespectral del Área")
        st.plotly_chart(fig, use_container_width=True)
        
        # Recomendaciones integradas
        st.subheader("🎯 Recomendaciones de Manejo Integrado")
        
        soil_recs = st.session_state.get('soil_recommendations', [])
        veg_health = vegetation_health['health_score']
        
        if veg_health < 60 and soil_recs:
            st.error("""
            **🔴 Atención Crítica Requerida:**
            - Salud vegetal y suelo necesitan mejoras inmediatas
            - Implementar las recomendaciones de fertilización
            - Revisar sistema de riego y drenaje
            - Considerar análisis de plagas y enfermedades
            """)
        elif veg_health < 70:
            st.warning("""
            **🟡 Monitoreo Intensivo Recomendado:**
            - Salud vegetal moderada, requiere atención
            - Implementar fertilización balanceada
            - Monitorear evolución semanalmente
            """)
        else:
            st.success("""
            **✅ Condiciones Óptimas:**
            - Salud vegetal y suelo en buen estado
            - Mantener prácticas actuales de manejo
            - Continuar monitoreo preventivo
            """)
        
        # Plan de acción detallado
        if soil_recs:
            st.subheader("📋 Plan de Acción Detallado")
            for i, rec in enumerate(soil_recs, 1):
                st.write(f"{i}. **{rec['type']}**: {rec['producto']} - {rec['dosis']} ({rec['prioridad']})")

def render_dashboard():
    st.title("📊 Dashboard de Gestión")
    
    has_soil = 'soil_analysis' in st.session_state
    has_lidar = 'point_cloud' in st.session_state
    has_sentinel = 'vegetation_health' in st.session_state
    
    if not has_soil and not has_lidar and not has_sentinel:
        st.info("💡 Usa los otros módulos para ver datos integrados aquí")
        return
    
    # Resumen ejecutivo
    st.header("📈 Resumen Ejecutivo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if has_soil:
            soil_score = st.session_state.soil_analysis['total_score']
            st.metric("Fertilidad Suelo", f"{soil_score:.0f}%")
        else:
            st.metric("Fertilidad Suelo", "N/D")
    
    with col2:
        if has_sentinel:
            veg_health = st.session_state.vegetation_health['health_score']
            st.metric("Salud Vegetal", f"{veg_health:.0f}%")
        else:
            st.metric("Salud Vegetal", "N/D")
    
    with col3:
        if has_lidar:
            metrics = extract_plant_metrics(st.session_state.point_cloud)
            st.metric("Cobertura Vegetal", f"{metrics['vegetation_percentage']:.1f}%")
        else:
            st.metric("Cobertura Vegetal", "N/D")
    
    with col4:
        if has_sentinel:
            water_stress = st.session_state.vegetation_health['water_stress']
            st.metric("Estrés Hídrico", water_stress)
        else:
            st.metric("Estrés Hídrico", "N/D")
    
    # Recomendaciones consolidadas
    st.header("🎯 Recomendaciones Consolidadas")
    
    if has_soil and has_sentinel:
        soil_score = st.session_state.soil_analysis['total_score']
        veg_health = st.session_state.vegetation_health['health_score']
        
        if soil_score < 60 and veg_health < 60:
            st.error("""
            **🔴 INTERVENCIÓN INMEDIATA REQUERIDA**
            - Suelo y cultivo en condiciones críticas
            - Implementar plan de fertilización completo
            - Evaluar sistema de riego y drenaje
            - Considerar rotación de cultivos
            """)
        elif soil_score >= 70 and veg_health >= 70:
            st.success("""
            **✅ CONDICIONES ÓPTIMAS**
            - Mantener prácticas actuales
            - Continuar monitoreo preventivo
            - Optimizar rentabilidad
            """)
        else:
            st.warning("""
            **🟡 MANEJO PRECISIO REQUERIDO**
            - Algunos parámetros necesitan atención
            - Aplicar fertilización específica
            - Monitorear evolución
            """)

def main():
    """Función principal"""
    
    # Sidebar
    st.sidebar.title("🌱 Plataforma Agrícola Integral")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio("Navegación Principal", [
        "🏠 Inicio", 
        "🌱 Análisis de Suelo", 
        "🔄 Gemelos Digitales", 
        "🔬 Análisis Integrado",
        "📊 Dashboard"
    ])
    
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Nuevas Funcionalidades:**
    - 🛰️ Análisis Sentinel-2
    - 🔬 Análisis integrado
    - 💰 Recomendaciones con costos
    - 📈 Estimación de rendimientos
    """)
    
    # Navegación
    if page == "🏠 Inicio":
        render_home()
    elif page == "🌱 Análisis de Suelo":
        render_soil_analysis_main()
    elif page == "🔄 Gemelos Digitales":
        render_lidar_page()
    elif page == "🔬 Análisis Integrado":
        render_advanced_analysis()
    elif page == "📊 Dashboard":
        render_dashboard()

if __name__ == "__main__":
    main()
