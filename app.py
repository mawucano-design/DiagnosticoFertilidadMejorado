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
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

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
# MÓDULO DE VISUALIZACIÓN MEJORADO
# ============================================================================

def create_advanced_visualization(lidar_data, sentinel_data, soil_analysis):
    """Crea visualizaciones integradas LiDAR + Sentinel-2"""
    
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{'type': 'scatter3d'}, {'type': 'xy'}],
               [{'type': 'xy'}, {'type': 'xy'}]],
        subplot_titles=(
            'Modelo 3D LiDAR - Topografía y Vegetación',
            'Análisis NDVI - Salud Vegetal',
            'Análisis NDWI - Estrés Hídrico',
            'Perfil de Fertilidad del Suelo'
        )
    )
    
    # 1. Visualización 3D LiDAR
    if lidar_data and hasattr(lidar_data, 'points'):
        points = lidar_data.points
        ground_level = np.percentile(points[:, 2], 10)
        vegetation_mask = points[:, 2] > ground_level + 0.2
        
        # Terreno
        ground_points = points[~vegetation_mask]
        fig.add_trace(
            go.Scatter3d(
                x=ground_points[:, 0], y=ground_points[:, 1], z=ground_points[:, 2],
                mode='markers', marker=dict(size=2, color='brown', opacity=0.6),
                name='Terreno'
            ), row=1, col=1
        )
        
        # Vegetación
        veg_points = points[vegetation_mask]
        fig.add_trace(
            go.Scatter3d(
                x=veg_points[:, 0], y=veg_points[:, 1], z=veg_points[:, 2],
                mode='markers', marker=dict(size=3, color='green', opacity=0.7),
                name='Vegetación'
            ), row=1, col=1
        )
    
    # 2. Mapa de NDVI
    if sentinel_data:
        xx, yy = sentinel_data['coordinates']
        ndvi = sentinel_data['ndvi']
        
        fig.add_trace(
            go.Heatmap(
                x=xx[0], y=yy[:, 0], z=ndvi,
                colorscale='Viridis', name='NDVI',
                colorbar=dict(title='NDVI')
            ), row=1, col=2
        )
    
    # 3. Mapa de NDWI
    if sentinel_data:
        ndwi = sentinel_data['ndwi']
        fig.add_trace(
            go.Heatmap(
                x=xx[0], y=yy[:, 0], z=ndwi,
                colorscale='Blues', name='NDWI',
                colorbar=dict(title='NDWI')
            ), row=2, col=1
        )
    
    # 4. Perfil de fertilidad
    if soil_analysis:
        componentes = list(soil_analysis['component_scores'].keys())
        puntajes = list(soil_analysis['component_scores'].values())
        
        fig.add_trace(
            go.Bar(
                x=componentes, y=puntajes,
                marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
                name='Puntajes'
            ), row=2, col=2
        )
    
    fig.update_layout(height=800, title_text="Dashboard Integrado de Análisis Agrícola")
    return fig

# ============================================================================
# INTERFAZ PRINCIPAL MEJORADA
# ============================================================================

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
        
        # Visualización integrada
        st.subheader("📊 Dashboard de Análisis Integrado")
        soil_analysis = st.session_state.get('soil_analysis', None)
        lidar_data = st.session_state.get('point_cloud', None)
        
        fig = create_advanced_visualization(lidar_data, sentinel_data, soil_analysis)
        st.plotly_chart(fig, use_container_width=True)
        
        # Recomendaciones integradas
        st.subheader("🎯 Recomendaciones de Manejo Integrado")
        
        # Combinar recomendaciones de suelo y vegetación
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

# ============================================================================
# INTERFAZ PRINCIPAL ACTUALIZADA
# ============================================================================

def main():
    """Función principal con nueva estructura"""
    
    # Sidebar con nueva organización
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

# (Los demás módulos como render_home, render_lidar_page, etc. se mantienen similares pero actualizados)

if __name__ == "__main__":
    main()
