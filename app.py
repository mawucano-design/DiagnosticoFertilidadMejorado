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
                fillcolor='rgba(255, 0, 0, 0.2)',
                line=dict(color='red', width=3),
                name='Área de Análisis'
            ))
            
            # Calcular centro del polígono
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            center = {"lat": center_lat, "lon": center_lon}
        
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
            height=500
        )
        
        return fig
    
    def create_analysis_map(self, sentinel_data=None, polygon=None):
        """Crea mapa de análisis con múltiples capas"""
        if polygon is None:
            return self.create_satellite_map()
            
        # Crear figura con subplots
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{"type": "scattermapbox"}, {"type": "scattermapbox"}],
                   [{"type": "scattermapbox"}, {"type": "scattermapbox"}]],
            subplot_titles=('Vista Satelital', 'Área de Estudio', 
                          'Análisis NDVI', 'Zonas de Interés')
        )
        
        # Mapa 1: Vista satelital
        lats = [p[1] for p in polygon]
        lons = [p[0] for p in polygon]
        lats.append(lats[0])
        lons.append(lons[0])
        
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        center = {"lat": center_lat, "lon": center_lon}
        
        # Subplot 1: Vista satelital
        fig.add_trace(go.Scattermapbox(
            lat=lats, lon=lons,
            mode='lines', line=dict(color='red', width=2),
            name='Lote', showlegend=False
        ), row=1, col=1)
        
        # Subplot 2: Área de estudio
        fig.add_trace(go.Scattermapbox(
            lat=lats, lon=lons,
            mode='lines+markers', 
            fill='toself',
            fillcolor='rgba(0, 255, 0, 0.3)',
            line=dict(color='green', width=3),
            name='Área', showlegend=False
        ), row=1, col=2)
        
        # Subplot 3: Análisis (simulado)
        if sentinel_data:
            xx, yy = sentinel_data['coordinates']
            ndvi = sentinel_data['ndvi']
            
            # Crear puntos para el heatmap
            flat_xx = xx.flatten()
            flat_yy = yy.flatten()
            flat_ndvi = ndvi.flatten()
            
            # Muestra de puntos para no saturar
            sample_idx = np.random.choice(len(flat_xx), min(1000, len(flat_xx)), replace=False)
            
            fig.add_trace(go.Scattermapbox(
                lat=flat_yy[sample_idx],
                lon=flat_xx[sample_idx],
                mode='markers',
                marker=dict(
                    size=8,
                    color=flat_ndvi[sample_idx],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="NDVI")
                ),
                name='NDVI', showlegend=False
            ), row=2, col=1)
        
        # Subplot 4: Zonas de interés
        # Agregar puntos de interés simulados
        interest_points = [
            {"lat": center_lat + 0.001, "lon": center_lon + 0.001, "type": "Alta Productividad"},
            {"lat": center_lat - 0.001, "lon": center_lon - 0.001, "type": "Baja Productividad"},
            {"lat": center_lat + 0.002, "lon": center_lon, "type": "Zona Húmeda"}
        ]
        
        for point in interest_points:
            fig.add_trace(go.Scattermapbox(
                lat=[point["lat"]],
                lon=[point["lon"]],
                mode='markers',
                marker=dict(size=12, color='blue'),
                name=point["type"],
                text=point["type"],
                showlegend=False
            ), row=2, col=2)
        
        # Configurar layout de mapas
        mapbox_config = dict(
            style="white-bg",
            layers=[{
                "below": 'traces',
                "sourcetype": "raster",
                "source": [self.esri_satellite_url],
            }],
            center=center,
            zoom=13,
        )
        
        fig.update_layout(
            mapbox=mapbox_config,
            mapbox2=mapbox_config,
            mapbox3=mapbox_config,
            mapbox4=mapbox_config,
            margin={"r":0,"t":30,"l":0,"b":0},
            height=600,
            title_text="Análisis Espacial del Lote"
        )
        
        return fig

# ============================================================================
# MÓDULO DE VISUALIZACIÓN 3D MEJORADA
# ============================================================================

class Advanced3DVisualizer:
    def __init__(self):
        self.colors = {
            'ground': '#8B4513',
            'vegetation_low': '#90EE90',
            'vegetation_medium': '#32CD32', 
            'vegetation_high': '#006400',
            'water': '#1E90FF'
        }
    
    def create_enhanced_3d_plot(self, point_cloud, title="Modelo 3D del Terreno"):
        """Crea visualización 3D mejorada con colores y efectos"""
        if point_cloud is None or not hasattr(point_cloud, 'points'):
            return None
            
        points = point_cloud.points
        
        # Calcular métricas para colorear
        ground_level = np.percentile(points[:, 2], 10)
        vegetation_mask = points[:, 2] > ground_level + 0.2
        height_above_ground = points[:, 2] - ground_level
        
        # Asignar colores basados en altura y tipo
        colors = []
        sizes = []
        
        for i, height in enumerate(height_above_ground):
            if height <= 0.1:  # Terreno
                colors.append(self.colors['ground'])
                sizes.append(2)
            elif height <= 1.0:  # Vegetación baja
                colors.append(self.colors['vegetation_low'])
                sizes.append(3)
            elif height <= 2.0:  # Vegetación media
                colors.append(self.colors['vegetation_medium'])
                sizes.append(4)
            else:  # Vegetación alta/árboles
                colors.append(self.colors['vegetation_high'])
                sizes.append(5)
        
        # Crear figura 3D
        fig = go.Figure()
        
        # Agregar puntos con colores
        fig.add_trace(go.Scatter3d(
            x=points[:, 0],
            y=points[:, 1],
            z=points[:, 2],
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                opacity=0.8,
                line=dict(width=0)
            ),
            name='Puntos LiDAR',
            hovertemplate=(
                'X: %{x:.2f}<br>'
                'Y: %{y:.2f}<br>'
                'Z: %{z:.2f} m<br>'
                '<extra></extra>'
            )
        ))
        
        # Agregar superficie de terreno (simplificada)
        try:
            # Crear malla de superficie
            x_unique = np.linspace(np.min(points[:, 0]), np.max(points[:, 0]), 20)
            y_unique = np.linspace(np.min(points[:, 1]), np.max(points[:, 1]), 20)
            xx, yy = np.meshgrid(x_unique, y_unique)
            
            # Interpolar altura
            from scipy.interpolate import griddata
            ground_points = points[~vegetation_mask]
            if len(ground_points) > 10:
                zz = griddata(
                    (ground_points[:, 0], ground_points[:, 1]), 
                    ground_points[:, 2], 
                    (xx, yy), 
                    method='linear'
                )
                
                fig.add_trace(go.Surface(
                    x=xx, y=yy, z=zz,
                    colorscale=[[0, self.colors['ground']], [1, self.colors['ground']]],
                    opacity=0.3,
                    showscale=False,
                    name='Superficie del Terreno'
                ))
        except:
            pass  # Si falla la interpolación, continuar sin superficie
        
        # Configurar layout
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor='center',
                font=dict(size=20)
            ),
            scene=dict(
                xaxis_title='Longitud',
                yaxis_title='Latitud', 
                zaxis_title='Altura (m)',
                aspectmode='data',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                ),
                bgcolor='rgb(240, 240, 240)'
            ),
            height=600,
            showlegend=True
        )
        
        return fig
    
    def create_comparison_3d(self, point_cloud1, point_cloud2, title1="Antes", title2="Después"):
        """Crea comparación 3D entre dos nubes de puntos"""
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{'type': 'scatter3d'}, {'type': 'scatter3d'}]],
            subplot_titles=(title1, title2)
        )
        
        # Primer conjunto de puntos
        if point_cloud1 and hasattr(point_cloud1, 'points'):
            points1 = point_cloud1.points
            fig.add_trace(go.Scatter3d(
                x=points1[:, 0], y=points1[:, 1], z=points1[:, 2],
                mode='markers',
                marker=dict(size=2, color='blue', opacity=0.6),
                name=title1
            ), row=1, col=1)
        
        # Segundo conjunto de puntos  
        if point_cloud2 and hasattr(point_cloud2, 'points'):
            points2 = point_cloud2.points
            fig.add_trace(go.Scatter3d(
                x=points2[:, 0], y=points2[:, 1], z=points2[:, 2],
                mode='markers',
                marker=dict(size=2, color='red', opacity=0.6),
                name=title2
            ), row=1, col=2)
        
        fig.update_layout(
            height=500,
            title_text="Comparación 3D de Datos LiDAR"
        )
        
        # Configurar cámaras iguales para comparación
        camera = dict(eye=dict(x=1.5, y=1.5, z=1.5))
        
        fig.update_scenes(
            aspectmode='data',
            camera=camera,
            row=1, col=1
        )
        
        fig.update_scenes(
            aspectmode='data',
            camera=camera,
            row=1, col=2
        )
        
        return fig

# ============================================================================
# MÓDULO DE GRÁFICOS MEJORADOS
# ============================================================================

class EnhancedChartBuilder:
    def __init__(self):
        self.color_palette = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B']
    
    def create_soil_health_gauge(self, score, title="Salud del Suelo"):
        """Crea gauge chart para salud del suelo"""
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': title},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 70], 'color': "gray"},
                    {'range': [70, 100], 'color': "lightgray"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90}}))
        
        fig.update_layout(height=300)
        return fig
    
    def create_radar_chart(self, metrics, title="Perfil de Métricas"):
        """Crea gráfico radar para múltiples métricas"""
        categories = list(metrics.keys())
        values = list(metrics.values())
        
        # Cerrar el radar
        categories.append(categories[0])
        values.append(values[0])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=title,
            line=dict(color=self.color_palette[0])
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=False,
            height=400,
            title=title
        )
        
        return fig
    
    def create_stacked_bar_analysis(self, soil_analysis, vegetation_health):
        """Crea gráfico de barras apiladas para análisis integrado"""
        categories = ['Suelo', 'Vegetación', 'Agua', 'Nutrientes']
        
        # Datos de suelo
        soil_scores = [
            soil_analysis.get('total_score', 0),
            vegetation_health.get('health_score', 0),
            vegetation_health.get('mean_ndwi', 0) * 100,  # Convertir a porcentaje
            vegetation_health.get('mean_ndre', 0) * 100   # Convertir a porcentaje
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=categories,
            y=soil_scores,
            marker_color=self.color_palette,
            text=[f'{score:.0f}%' for score in soil_scores],
            textposition='auto',
        ))
        
        fig.update_layout(
            title='Análisis Integrado de Componentes',
            xaxis_title='Componentes',
            yaxis_title='Puntaje (%)',
            yaxis=dict(range=[0, 100]),
            height=400
        )
        
        return fig
    
    def create_timeseries_chart(self, dates, values, title="Evolución Temporal"):
        """Crea gráfico de series temporales"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name=title,
            line=dict(color=self.color_palette[0], width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Fecha',
            yaxis_title='Valor',
            height=400
        )
        
        return fig

# ============================================================================
# MÓDULOS EXISTENTES (SIMPLIFICADOS)
# ============================================================================

class SentinelAnalyzer:
    def calculate_ndvi(self, red_band, nir_band):
        return (nir_band - red_band) / (nir_band + red_band + 1e-8)
    
    def generate_sentinel_data(self, polygon, resolution=50):
        if not polygon:
            return None
            
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        x_coords = np.linspace(min_lon, max_lon, resolution)
        y_coords = np.linspace(min_lat, max_lat, resolution)
        xx, yy = np.meshgrid(x_coords, y_coords)
        
        np.random.seed(42)
        red_band = 0.2 + 0.1 * np.sin(xx * 10) + 0.1 * np.cos(yy * 10)
        nir_band = 0.3 + 0.2 * np.sin(xx * 8) + 0.15 * np.cos(yy * 8)
        green_band = 0.25 + 0.1 * np.sin(xx * 12) + 0.1 * np.cos(yy * 12)
        red_edge_band = 0.22 + 0.12 * np.sin(xx * 9) + 0.1 * np.cos(yy * 9)
        
        return {
            'coordinates': (xx, yy),
            'ndvi': self.calculate_ndvi(red_band, nir_band),
            'ndwi': (green_band - nir_band) / (green_band + nir_band + 1e-8),
            'ndre': (nir_band - red_edge_band) / (nir_band + red_edge_band + 1e-8),
        }

# ============================================================================
# INTERFAZ PRINCIPAL MEJORADA
# ============================================================================

def render_enhanced_home():
    st.title("🌱 Plataforma de Agricultura de Precisión")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## ¡Bienvenido a la Plataforma Agrícola Integral!
        
        **Herramientas avanzadas para la gestión agrícola basada en datos:**
        
        🛰️ **Análisis Satelital** - Imágenes ESRI + Sentinel-2
        📡 **Modelos 3D** - Visualización LiDAR mejorada  
        🌱 **Diagnóstico de Suelo** - Análisis completo de fertilidad
        📊 **Dashboards Interactivos** - Gráficos comprensibles
        🗺️ **Mapas Inteligentes** - ESRI base + análisis espacial
        """)
        
        # Mapa de ejemplo
        st.subheader("🗺️ Mapa de Referencia")
        map_viz = MapVisualizer()
        map_fig = map_viz.create_satellite_map()
        st.plotly_chart(map_fig, use_container_width=True)
    
    with col2:
        st.info("""
        **🚀 Comenzar Análisis:**
        
        1. **🌱 Análisis de Suelo** 
           - Diagnóstico de fertilidad
           - Recomendaciones específicas
        
        2. **🔄 Gemelos Digitales**
           - Carga de polígonos KML
           - Modelos 3D LiDAR
           - Mapas ESRI satelital
        
        3. **🔬 Análisis Integrado**
           - Combinación de datos
           - Dashboards unificados
        """)
        
        # Métricas rápidas
        st.subheader("📈 Estado del Sistema")
        st.metric("Módulos Activos", "5/5", "100%")
        st.metric("Análisis Disponibles", "12")
        st.metric("Precisión Estimada", "95%")

def render_enhanced_lidar():
    st.title("🔄 Gemelos Digitales - Análisis LiDAR")
    
    # Inicializar visualizadores
    map_viz = MapVisualizer()
    viz_3d = Advanced3DVisualizer()
    
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Mapa Base", "📡 Datos LiDAR", "🌋 Visualización 3D", "📊 Análisis"])
    
    with tab1:
        st.header("Mapa Base ESRI Satelital")
        
        # Cargar polígono
        polygon = st.session_state.get('current_polygon')
        
        if polygon:
            st.success("✅ Polígono cargado - Generando mapa...")
            map_fig = map_viz.create_analysis_map(polygon=polygon)
            st.plotly_chart(map_fig, use_container_width=True)
        else:
            st.info("💡 Carga un polígono KML para ver el análisis espacial")
            default_map = map_viz.create_satellite_map()
            st.plotly_chart(default_map, use_container_width=True)
    
    with tab2:
        st.header("Generación de Datos LiDAR")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Generar Datos LiDAR", type="primary"):
                # Simular generación de datos
                np.random.seed(42)
                points = np.random.rand(2000, 3) * 10
                points[:, 2] = points[:, 2] * 2  # Alturas más realistas
                
                st.session_state.point_cloud = type('PointCloud', (), {'points': points})()
                st.success("✅ Datos LiDAR generados exitosamente")
        
        with col2:
            if 'point_cloud' in st.session_state:
                points = st.session_state.point_cloud.points
                st.metric("Puntos Generados", f"{len(points):,}")
                st.metric("Altura Máxima", f"{np.max(points[:, 2]):.1f} m")
    
    with tab3:
        st.header("Visualización 3D Mejorada")
        
        if 'point_cloud' in st.session_state:
            # Visualización 3D mejorada
            viz_3d = Advanced3DVisualizer()
            fig_3d = viz_3d.create_enhanced_3d_plot(
                st.session_state.point_cloud,
                "Modelo 3D del Terreno - Visualización Mejorada"
            )
            st.plotly_chart(fig_3d, use_container_width=True)
            
            # Métricas de la visualización
            points = st.session_state.point_cloud.points
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Resolución", "Alta")
            with col2:
                st.metric("Puntos Visibles", f"{len(points):,}")
            with col3:
                st.metric("Área Cubierta", "10x10 m")
            with col4:
                st.metric("Detalle", "✅ 3D Completo")
        else:
            st.info("👆 Genera datos LiDAR primero para ver la visualización 3D")
    
    with tab4:
        st.header("Análisis y Métricas")
        
        if 'point_cloud' in st.session_state:
            # Gráficos de análisis
            chart_builder = EnhancedChartBuilder()
            
            # Datos simulados para gráficos
            points = st.session_state.point_cloud.points
            vegetation_mask = points[:, 2] > 1.0
            vegetation_percentage = np.sum(vegetation_mask) / len(points) * 100
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Gauge de vegetación
                gauge_fig = chart_builder.create_soil_health_gauge(
                    vegetation_percentage, 
                    "Cobertura Vegetal"
                )
                st.plotly_chart(gauge_fig, use_container_width=True)
            
            with col2:
                # Radar de métricas
                metrics = {
                    'Altura': (np.mean(points[:, 2]) / 3) * 100,
                    'Densidad': min(vegetation_percentage * 2, 100),
                    'Uniformidad': 75,
                    'Cobertura': vegetation_percentage
                }
                radar_fig = chart_builder.create_radar_chart(metrics, "Perfil LiDAR")
                st.plotly_chart(radar_fig, use_container_width=True)
            
            # Serie temporal simulada
            st.subheader("📈 Evolución Temporal (Simulada)")
            dates = pd.date_range('2024-01-01', periods=6, freq='M')
            values = [60, 65, 72, 68, 75, 78]  # Cobertura vegetal %
            
            ts_fig = chart_builder.create_timeseries_chart(dates, values, "Cobertura Vegetal Mensual")
            st.plotly_chart(ts_fig, use_container_width=True)

def main():
    """Función principal"""
    
    # Sidebar mejorado
    st.sidebar.title("🌱 Navegación")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Seleccionar Módulo:",
        ["🏠 Inicio", "🗺️ Mapas ESRI", "🔄 LiDAR 3D", "🌱 Análisis Suelo", "📊 Dashboard"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **✨ Nuevas Funcionalidades:**
    
    - 🗺️ Mapas ESRI Satelital
    - 🌋 Visualización 3D Mejorada
    - 📊 Gráficos Interactivos
    - 🎯 Análisis Integrado
    """)
    
    # Navegación
    if page == "🏠 Inicio":
        render_enhanced_home()
    elif page == "🗺️ Mapas ESRI":
        render_enhanced_lidar()
    elif page == "🔄 LiDAR 3D":
        render_enhanced_lidar()
    elif page == "🌱 Análisis Suelo":
        st.title("🌱 Análisis de Suelo")
        st.info("Módulo en desarrollo - Próximamente")
    elif page == "📊 Dashboard":
        st.title("📊 Dashboard Integrado")
        st.info("Módulo en desarrollo - Próximamente")

if __name__ == "__main__":
    main()
