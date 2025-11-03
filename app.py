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
# MÓDULOS DE ANÁLISIS COMPLETOS
# ============================================================================

class LiDARAnalyzer:
    """Analizador LiDAR para modelos 3D"""
    
    def __init__(self):
        self.colors = {
            'ground': '#8B4513',
            'vegetation_low': '#90EE90',
            'vegetation_medium': '#32CD32', 
            'vegetation_high': '#006400'
        }
    
    def generate_lidar_data(self, polygon, num_points=5000):
        """Genera datos LiDAR realistas para el polígono"""
        bounds = self._get_polygon_bounds(polygon)
        
        points = []
        for _ in range(num_points):
            lon = np.random.uniform(bounds['min_lon'], bounds['max_lon'])
            lat = np.random.uniform(bounds['min_lat'], bounds['max_lat'])
            
            if self._point_in_polygon(lon, lat, polygon):
                # Simular topografía realista
                base_height = self._simulate_terrain(lon, lat, bounds)
                
                # 70% probabilidad de ser terreno, 30% vegetación
                if np.random.random() > 0.7:
                    # Vegetación - altura variable
                    height = base_height + np.random.uniform(0.5, 3.0)
                    point_type = 'vegetation'
                else:
                    # Terreno
                    height = base_height + np.random.uniform(0, 0.3)
                    point_type = 'ground'
                
                points.append([lon, lat, height, point_type])
        
        return np.array(points)
    
    def _simulate_terrain(self, lon, lat, bounds):
        """Simula topografía realista con colinas suaves"""
        # Centro relativo para crear patrones
        center_x = (lon - bounds['min_lon']) / (bounds['max_lon'] - bounds['min_lon'])
        center_y = (lat - bounds['min_lat']) / (bounds['max_lat'] - bounds['min_lat'])
        
        # Crear patrones de terreno con funciones periódicas
        terrain = (
            0.1 * np.sin(center_x * 4 * np.pi) *
            np.cos(center_y * 3 * np.pi) +
            0.05 * np.sin(center_x * 8 * np.pi) *
            np.cos(center_y * 6 * np.pi)
        )
        
        return max(terrain, 0)  # No permitir alturas negativas
    
    def analyze_lidar_metrics(self, points):
        """Analiza métricas del modelo LiDAR"""
        if len(points) == 0:
            return {}
        
        heights = points[:, 2]
        point_types = points[:, 3]
        
        # Separar vegetación y terreno
        vegetation_mask = point_types == 'vegetation'
        ground_points = points[~vegetation_mask]
        vegetation_points = points[vegetation_mask]
        
        # Métricas básicas
        metrics = {
            'total_points': len(points),
            'vegetation_points': len(vegetation_points),
            'ground_points': len(ground_points),
            'max_height': float(np.max(heights)),
            'min_height': float(np.min(heights)),
            'mean_height': float(np.mean(heights)),
            'vegetation_coverage': len(vegetation_points) / len(points) * 100
        }
        
        # Métricas de vegetación
        if len(vegetation_points) > 0:
            veg_heights = vegetation_points[:, 2]
            metrics.update({
                'max_vegetation_height': float(np.max(veg_heights)),
                'mean_vegetation_height': float(np.mean(veg_heights)),
                'vegetation_density': len(vegetation_points) / metrics['vegetation_coverage'] if metrics['vegetation_coverage'] > 0 else 0
            })
        
        # Clasificación de cobertura vegetal
        coverage = metrics['vegetation_coverage']
        if coverage > 70:
            metrics['coverage_class'] = 'Alta'
        elif coverage > 40:
            metrics['coverage_class'] = 'Media'
        else:
            metrics['coverage_class'] = 'Baja'
        
        return metrics
    
    def create_3d_visualization(self, points, title="Modelo LiDAR 3D"):
        """Crea visualización 3D interactiva"""
        if len(points) == 0:
            return None
        
        fig = go.Figure()
        
        # Separar por tipo para colorear
        ground_points = points[points[:, 3] == 'ground']
        vegetation_points = points[points[:, 3] == 'vegetation']
        
        # Terreno
        if len(ground_points) > 0:
            fig.add_trace(go.Scatter3d(
                x=ground_points[:, 0],
                y=ground_points[:, 1],
                z=ground_points[:, 2],
                mode='markers',
                marker=dict(
                    size=2,
                    color=self.colors['ground'],
                    opacity=0.7
                ),
                name='Terreno'
            ))
        
        # Vegetación
        if len(vegetation_points) > 0:
            # Colorear vegetación por altura
            veg_heights = vegetation_points[:, 2]
            
            fig.add_trace(go.Scatter3d(
                x=vegetation_points[:, 0],
                y=vegetation_points[:, 1],
                z=vegetation_points[:, 2],
                mode='markers',
                marker=dict(
                    size=3,
                    color=veg_heights,
                    colorscale='Viridis',
                    opacity=0.8,
                    colorbar=dict(title="Altura (m)")
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
        
        return fig
    
    def _get_polygon_bounds(self, polygon):
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        return {
            'min_lon': min(lons), 'max_lon': max(lons),
            'min_lat': min(lats), 'max_lat': max(lats)
        }
    
    def _point_in_polygon(self, x, y, poly):
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
# INTERFAZ DE ANÁLISIS COMPLETOS
# ============================================================================

def render_soil_analysis():
    """Análisis completo de suelo"""
    st.header("🌱 Análisis de Fertilidad del Suelo")
    
    with st.form("soil_analysis_detailed"):
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
        
        st.subheader("Configuración del Cultivo")
        col3, col4 = st.columns(2)
        with col3:
            crop_type = st.selectbox("Cultivo Principal", 
                                   ["maiz", "soja", "trigo", "girasol", "algodón"])
        with col4:
            area_ha = st.session_state.get('polygon_area_ha', 10)
            st.metric("Área del Lote", f"{area_ha:.2f} ha")
        
        if st.form_submit_button("🔬 Ejecutar Análisis Completo", type="primary"):
            with st.spinner("Analizando suelo..."):
                # Ejecutar análisis
                soil_analyzer = SoilAnalysisEngine()
                soil_params = {
                    'ph': ph,
                    'organic_matter': organic_matter,
                    'nitrogen': nitrogen,
                    'phosphorus': phosphorus,
                    'potassium': potassium,
                    'texture': texture
                }
                
                analysis = soil_analyzer.analyze_soil_health(soil_params, area_ha, crop_type)
                st.session_state.soil_analysis = analysis
                st.session_state.soil_params = soil_params
            
    # Mostrar resultados si existen
    if 'soil_analysis' in st.session_state:
        analysis = st.session_state.soil_analysis
        
        st.subheader("📊 Resultados del Análisis")
        
        # Puntaje general
        overall_score = analysis['overall_score']
        st.metric("Puntaje General de Fertilidad", f"{overall_score:.0f}/100")
        
        # Barra de progreso
        color = "red" if overall_score < 50 else "orange" if overall_score < 70 else "green"
        st.markdown(f"""
        <div style="background: #f0f0f0; border-radius: 10px; padding: 3px; margin: 10px 0;">
            <div style="background: {color}; width: {overall_score}%; height: 30px; 
                        border-radius: 8px; text-align: center; color: white; 
                        line-height: 30px; font-weight: bold;">
                {overall_score:.0f}% - {'Excelente' if overall_score >= 80 else 'Bueno' if overall_score >= 60 else 'Necesita Mejora'}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Métricas detalladas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Componentes del Suelo")
            components = {
                'pH': analysis['ph_analysis'],
                'Materia Orgánica': analysis['om_analysis'],
                'Nitrógeno': analysis['n_analysis'],
                'Fósforo': analysis['p_analysis'],
                'Potasio': analysis['k_analysis']
            }
            
            for name, data in components.items():
                st.metric(f"{name}", f"{data['score']:.0f}%", data['status'])
                st.caption(data['interpretation'])
        
        with col2:
            st.subheader("🌾 Productividad Estimada")
            productivity = analysis['productivity']
            st.metric("Rendimiento Esperado", f"{productivity['estimado_ha']:.0f} {productivity['unidad']}")
            st.metric("Producción Total", f"{productivity['estimado_total']:.0f} kg")
            st.metric("Potencial", productivity['potencial'])
        
        # Recomendaciones
        st.subheader("🎯 Plan de Recomendaciones")
        
        if analysis['recommendations']:
            for i, rec in enumerate(analysis['recommendations'], 1):
                st.write(f"""
                **{i}. {rec['tipo']}** - *{rec['prioridad']}*
                - **Producto**: {rec['producto']}
                - **Dosis**: {rec['dosis']}
                - **Costo estimado**: {rec['costo_estimado']}
                """)
        else:
            st.success("✅ No se requieren correcciones inmediatas. Mantener prácticas actuales.")

def render_satellite_analysis():
    """Análisis satelital completo"""
    st.header("🛰️ Análisis Satelital Multiespectral")
    
    if not st.session_state.get('polygon_loaded'):
        st.warning("Primero carga tu polígono en la página de Inicio")
        return
    
    polygon = st.session_state.current_polygon
    
    if st.button("🌿 Ejecutar Análisis Satelital Completo", type="primary"):
        with st.spinner("Calculando índices de vegetación..."):
            analyzer = AdvancedSatelliteAnalyzer()
            indices_data = analyzer.generate_multispectral_data(polygon)
            health_analysis = analyzer.analyze_vegetation_health(indices_data)
            
            st.session_state.satellite_indices = indices_data
            st.session_state.vegetation_health = health_analysis
            
            st.success("✅ Análisis multiespectral completado!")
    
    if 'satellite_indices' in st.session_state:
        indices_data = st.session_state.satellite_indices
        health_analysis = st.session_state.vegetation_health
        
        # Mostrar métricas principales
        st.subheader("📊 Salud Vegetal del Lote")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("NDVI - Salud General", 
                     f"{np.mean(indices_data['ndvi']):.3f}",
                     health_analysis['ndvi_status'])
            st.caption(health_analysis['ndvi_interpretation'])
        with col2:
            st.metric("NDWI - Agua", 
                     f"{np.mean(indices_data['ndwi']):.3f}",
                     health_analysis['water_status'])
            st.caption(health_analysis['water_interpretation'])
        with col3:
            st.metric("EVI - Vegetación Densa", 
                     f"{np.mean(indices_data['evi']):.3f}")
            st.caption(health_analysis['evi_interpretation'])
        with col4:
            st.metric("NDRE - Nutrientes", 
                     f"{np.mean(indices_data['ndre']):.3f}",
                     health_analysis['nutrient_status'])
            st.caption(health_analysis['nutrient_interpretation'])
        
        # Puntaje general
        overall_score = health_analysis['overall_score']
        st.metric("Puntaje General de Salud Vegetal", f"{overall_score:.0f}/100")
        
        # Mapas de índices
        st.subheader("🗺️ Mapas de Índices de Vegetación")
        
        # Selector de índice
        index_to_show = st.selectbox(
            "Selecciona el índice a visualizar:",
            ["NDVI - Salud Vegetal", "NDWI - Estrés Hídrico", "EVI - Vegetación Densa", 
             "SAVI - Ajustado por Suelo", "NDRE - Nutrientes"]
        )
        
        index_map = {
            "NDVI - Salud Vegetal": ('ndvi', 'Viridis', 'NDVI'),
            "NDWI - Estrés Hídrico": ('ndwi', 'Blues', 'NDWI'),
            "EVI - Vegetación Densa": ('evi', 'Greens', 'EVI'),
            "SAVI - Ajustado por Suelo": ('savi', 'YlOrBr', 'SAVI'),
            "NDRE - Nutrientes": ('ndre', 'RdYlGn', 'NDRE')
        }
        
        index_key, colorscale, title = index_map[index_to_show]
        
        fig = go.Figure(data=go.Heatmap(
            x=indices_data['coordinates'][0][0],
            y=indices_data['coordinates'][1][:, 0],
            z=indices_data[index_key],
            colorscale=colorscale,
            colorbar=dict(title=title)
        ))
        
        fig.update_layout(
            title=f"Mapa de {title} - Tu Lote",
            xaxis_title='Longitud',
            yaxis_title='Latitud',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recomendaciones basadas en análisis
        st.subheader("🎯 Recomendaciones de Manejo")
        
        if overall_score >= 80:
            st.success("""
            **✅ CONDICIONES ÓPTIMAS**
            - La vegetación se encuentra en excelente estado
            - Mantener prácticas actuales de manejo
            - Continuar monitoreo preventivo cada 15 días
            """)
        elif overall_score >= 60:
            st.warning("""
            **🟡 ATENCIÓN RECOMENDADA**
            - Salud vegetal moderada, requiere atención
            - Considerar riego suplementario si NDWI es bajo
            - Evaluar programa de fertilización balanceada
            - Monitorear evolución semanalmente
            """)
        else:
            st.error("""
            **🔴 INTERVENCIÓN REQUERIDA**
            - Salud vegetal comprometida
            - Revisar sistema de riego urgentemente
            - Implementar fertilización específica
            - Evaluar presencia de plagas y enfermedades
            - Consultar con especialista agronómico
            """)

def render_lidar_analysis():
    """Análisis LiDAR completo"""
    st.header("📡 Modelo LiDAR 3D del Terreno")
    
    if not st.session_state.get('polygon_loaded'):
        st.warning("Primero carga tu polígono en la página de Inicio")
        return
    
    polygon = st.session_state.current_polygon
    area_ha = st.session_state.get('polygon_area_ha', 10)
    
    if st.button("🔄 Generar Modelo LiDAR 3D", type="primary"):
        with st.spinner("Generando modelo 3D del terreno..."):
            lidar_analyzer = LiDARAnalyzer()
            points = lidar_analyzer.generate_lidar_data(polygon, 3000)
            metrics = lidar_analyzer.analyze_lidar_metrics(points)
            
            st.session_state.lidar_points = points
            st.session_state.lidar_metrics = metrics
            
            st.success(f"✅ Modelo 3D generado con {len(points):,} puntos")
    
    if 'lidar_points' in st.session_state:
        points = st.session_state.lidar_points
        metrics = st.session_state.lidar_metrics
        
        # Mostrar métricas
        st.subheader("📊 Métricas del Terreno")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Puntos Totales", f"{metrics['total_points']:,}")
            st.metric("Altura Máxima", f"{metrics['max_height']:.1f} m")
        with col2:
            st.metric("Cobertura Vegetal", f"{metrics['vegetation_coverage']:.1f}%")
            st.metric("Clase Cobertura", metrics['coverage_class'])
        with col3:
            st.metric("Puntos Vegetación", f"{metrics['vegetation_points']:,}")
            st.metric("Altura Media Veg.", f"{metrics.get('mean_vegetation_height', 0):.1f} m")
        with col4:
            st.metric("Puntos Terreno", f"{metrics['ground_points']:,}")
            st.metric("Altura Media", f"{metrics['mean_height']:.1f} m")
        
        # Visualización 3D
        st.subheader("🌋 Visualización 3D Interactiva")
        lidar_analyzer = LiDARAnalyzer()
        fig_3d = lidar_analyzer.create_3d_visualization(points, "Modelo 3D de tu Terreno")
        if fig_3d:
            st.plotly_chart(fig_3d, use_container_width=True)
        
        # Análisis de recomendaciones
        st.subheader("🎯 Recomendaciones Topográficas")
        
        coverage = metrics['vegetation_coverage']
        if coverage > 70:
            st.success("""
            **✅ COBERTURA VEGETAL ALTA**
            - Excelente desarrollo de vegetación
            - Considerar manejo de densidad si es necesario
            - Monitorear competencia por recursos
            """)
        elif coverage > 40:
            st.info("""
            **🔵 COBERTURA VEGETAL MEDIA**
            - Desarrollo vegetal adecuado
            - Optimizar distribución si hay zonas desparejas
            - Mantener prácticas actuales
            """)
        else:
            st.warning("""
            **🟡 COBERTURA VEGETAL BAJA**
            - Evaluar causas de baja cobertura
            - Considerar resiembra en zonas críticas
            - Mejorar manejo de suelo y nutrientes
            """)

def render_integrated_dashboard():
    """Dashboard integrado con todos los análisis"""
    st.header("📊 Dashboard Integrado")
    
    if not st.session_state.get('polygon_loaded'):
        st.warning("Primero carga tu polígono en la página de Inicio")
        return
    
    # Verificar qué análisis están disponibles
    has_soil = 'soil_analysis' in st.session_state
    has_satellite = 'vegetation_health' in st.session_state
    has_lidar = 'lidar_metrics' in st.session_state
    
    if not any([has_soil, has_satellite, has_lidar]):
        st.info("Ejecuta al menos un análisis para ver el dashboard integrado")
        return
    
    # Resumen ejecutivo
    st.subheader("📈 Resumen Ejecutivo del Lote")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if has_soil:
            soil_score = st.session_state.soil_analysis['overall_score']
            st.metric("Fertilidad Suelo", f"{soil_score:.0f}%")
        else:
            st.metric("Fertilidad Suelo", "No analizado")
    
    with col2:
        if has_satellite:
            veg_score = st.session_state.vegetation_health['overall_score']
            st.metric("Salud Vegetal", f"{veg_score:.0f}%")
        else:
            st.metric("Salud Vegetal", "No analizado")
    
    with col3:
        if has_lidar:
            coverage = st.session_state.lidar_metrics['vegetation_coverage']
            st.metric("Cobertura Vegetal", f"{coverage:.1f}%")
        else:
            st.metric("Cobertura Vegetal", "No analizado")
    
    with col4:
        area_ha = st.session_state.get('polygon_area_ha', 0)
        st.metric("Área Total", f"{area_ha:.2f} ha")
    
    # Recomendaciones consolidadas
    st.subheader("🎯 Recomendaciones Integradas")
    
    recommendations = []
    
    # Recomendaciones de suelo
    if has_soil:
        soil_recs = st.session_state.soil_analysis.get('recommendations', [])
        for rec in soil_recs:
            if rec['prioridad'] == 'Alta':
                recommendations.append(f"🔴 {rec['tipo']}: {rec['producto']} - {rec['dosis']}")
    
    # Recomendaciones de vegetación
    if has_satellite:
        veg_health = st.session_state.vegetation_health
        if veg_health['overall_score'] < 60:
            recommendations.append("🟡 Revisar salud vegetal: posible necesidad de riego o fertilización")
        if veg_health['water_status'] == 'Estrés severo':
            recommendations.append("🔴 Urgente: deficit hídrico detectado")
    
    # Recomendaciones de cobertura
    if has_lidar:
        coverage = st.session_state.lidar_metrics['vegetation_coverage']
        if coverage < 40:
            recommendations.append("🟡 Baja cobertura vegetal: evaluar causas y soluciones")
    
    if recommendations:
        for rec in recommendations:
            st.write(rec)
    else:
        st.success("✅ No se detectaron problemas críticos. Mantener prácticas actuales.")
    
    # Gráfico comparativo si hay múltiples análisis
    if has_soil and has_satellite:
        st.subheader("📊 Comparación Suelo vs Vegetación")
        
        soil_score = st.session_state.soil_analysis['overall_score']
        veg_score = st.session_state.vegetation_health['overall_score']
        
        fig = go.Figure(data=[
            go.Bar(name='Suelo', x=['Fertilidad'], y=[soil_score], marker_color='#4CAF50'),
            go.Bar(name='Vegetación', x=['Salud'], y=[veg_score], marker_color='#2196F3')
        ])
        
        fig.update_layout(
            title='Comparación de Salud del Suelo vs Vegetación',
            yaxis_title='Puntaje (%)',
            yaxis=dict(range=[0, 100]),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Análisis de correlación
        if soil_score < 60 and veg_score < 60:
            st.error("""
            **🔴 CORRELACIÓN CRÍTICA DETECTADA**
            - Tanto el suelo como la vegetación presentan problemas
            - Se requiere intervención integral
            - Priorizar corrección de suelo para mejorar vegetación
            """)
        elif soil_score >= 70 and veg_score >= 70:
            st.success("""
            **✅ SISTEMA EN EQUILIBRIO**
            - Suelo y vegetación en condiciones óptimas
            - Mantener prácticas de manejo actuales
            - Continuar monitoreo preventivo
            """)

# ============================================================================
# FLUJO PRINCIPAL ACTUALIZADO
# ============================================================================

def main():
    """Función principal con todos los análisis implementados"""
    
    # Inicializar session state
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
    
    # Estado actual
    if st.session_state.get('polygon_loaded'):
        area_ha = st.session_state.get('polygon_area_ha', 0)
        st.sidebar.success(f"✅ Lote cargado\n{area_ha:.1f} ha")
        
        if st.sidebar.button("🔄 Cambiar Lote"):
            for key in ['polygon_loaded', 'current_polygon', 'polygon_area_ha', 'polygon_bounds', 
                       'soil_analysis', 'satellite_indices', 'vegetation_health', 'lidar_points', 'lidar_metrics']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    else:
        st.sidebar.warning("⚠️ Sin lote cargado")
    
    # Navegación a páginas específicas
    if page == "🏠 Inicio":
        # (Usar la función render_home existente)
        st.title("🏠 Inicio - Plataforma Agrícola Integral")
        st.info("Carga tu polígono para comenzar con los análisis")
        
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
            render_lidar_analysis()
        else:
            st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
            
    elif page == "📊 Dashboard":
        if st.session_state.get('polygon_loaded'):
            render_integrated_dashboard()
        else:
            st.warning("⚠️ Primero carga tu polígono en la página de Inicio")

if __name__ == "__main__":
    main()
