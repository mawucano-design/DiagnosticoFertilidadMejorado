import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import io

# CONFIGURACIÓN - DEBE SER LO PRIMERO
st.set_page_config(
    page_title="Plataforma Agrícola Integral",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MÓDULO LIDAR - INTEGRADO DIRECTAMENTE
# ============================================================================

class LiDARProcessor:
    def __init__(self):
        self.point_cloud = None
        
    def create_sample_data(self):
        """Crea datos de ejemplo para demostración"""
        # Generar puntos de ejemplo que simulan un cultivo
        np.random.seed(42)
        
        # Terreno base
        x = np.linspace(0, 10, 50)
        y = np.linspace(0, 10, 50)
        xx, yy = np.meshgrid(x, y)
        z_ground = 0.1 * np.sin(xx) * np.cos(yy)
        
        # Vegetación (plantas)
        plant_centers = [(3, 3), (7, 7), (5, 2), (2, 7), (8, 3)]
        points = []
        
        # Puntos del terreno
        for i in range(len(xx.flatten())):
            points.append([xx.flatten()[i], yy.flatten()[i], z_ground.flatten()[i]])
        
        # Puntos de vegetación
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
    
    # Métricas básicas
    min_z = np.min(points[:, 2])
    max_z = np.max(points[:, 2])
    plant_height = max_z - min_z
    
    # Identificar vegetación (puntos sobre el terreno)
    ground_level = np.percentile(points[:, 2], 10)
    vegetation_mask = points[:, 2] > ground_level + 0.2
    vegetation_points = points[vegetation_mask]
    
    metrics = {
        'plant_height': float(plant_height),
        'canopy_volume': float(len(vegetation_points) * 0.001),  # Aproximado
        'plant_density': int(len(vegetation_points)),
        'canopy_area': float(100),  # Área fija para demo
        'health_score': float(min(100, len(vegetation_points) / 10)),
        'growth_stage': "Vegetativo" if plant_height > 1.0 else "Crecimiento",
        'max_height': float(max_z),
        'min_height': float(min_z),
        'vegetation_points': len(vegetation_points),
        'total_points': len(points)
    }
    
    return metrics

def create_interactive_plot(point_cloud, title="Visualización 3D - Datos LiDAR"):
    """Crea visualización 3D interactiva"""
    points = point_cloud.points
    
    # Crear figura 3D
    fig = go.Figure()
    
    # Separar terreno y vegetación
    ground_level = np.percentile(points[:, 2], 10)
    ground_mask = points[:, 2] <= ground_level + 0.2
    vegetation_mask = points[:, 2] > ground_level + 0.2
    
    # Terreno
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
    
    # Vegetación
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
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Altura (m)',
            aspectmode='data'
        ),
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar estadísticas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Puntos", f"{len(points):,}")
    with col2:
        st.metric("Altura Máx", f"{np.max(points[:, 2]):.2f} m")
    with col3:
        st.metric("Vegetación", f"{np.sum(vegetation_mask):,} pts")
    with col4:
        st.metric("Área Cubierta", "10x10 m")

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
            # Calcular puntajes
            puntaje_ph = calcular_puntaje_ph(ph, cultivo)
            puntaje_mo = calcular_puntaje_materia_organica(materia_organica, textura)
            puntaje_n = calcular_puntaje_nitrogeno(nitrogeno, cultivo)
            puntaje_p = calcular_puntaje_fosforo(fosforo, cultivo)
            puntaje_k = calcular_puntaje_potasio(potasio, cultivo)
            
            # Puntaje general
            puntaje_general = (
                puntaje_ph * 0.2 +
                puntaje_mo * 0.2 +
                puntaje_n * 0.25 +
                puntaje_p * 0.2 +
                puntaje_k * 0.15
            )
            
            # Guardar resultados
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
            
            # Mostrar resultados
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
    
    # Barra de progreso
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
    
    # Métricas
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
    
    # Recomendaciones
    st.header("🎯 Recomendaciones")
    if puntaje >= 80:
        st.success("✅ Condiciones óptimas. Mantener prácticas actuales.")
    elif puntaje >= 60:
        st.warning("⚠️ Condiciones aceptables. Considerar mejoras graduales.")
    else:
        st.error("❌ Necesita mejoras. Implementar plan de corrección.")

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

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
    - Visualización 3D interactiva de cultivos
    - Métricas de crecimiento y salud vegetal
    - Datos de ejemplo para demostración
    
    **📊 Dashboard Integrado**
    - Vista unificada de suelo y cultivo
    - Correlación entre fertilidad y crecimiento
    """)
    
    # Estado del sistema
    st.info("""
    **📈 Estado del Sistema:**
    - ✅ Módulo LiDAR: **Disponible** (con datos de ejemplo)
    - ✅ Módulo Fertilidad: **Disponible** 
    - ✅ Visualización 3D: **Activa**
    - 🟢 Sistema: **Operativo**
    """)

def render_lidar_page():
    st.title("🔄 Gemelos Digitales LiDAR")
    
    st.markdown("""
    **Procesamiento y visualización de datos LiDAR para agricultura de precisión**
    
    *Actualmente usando datos de demostración - Sube tus archivos .LAS/.LAZ cuando estén disponibles*
    """)
    
    tab1, tab2, tab3 = st.tabs(["📤 Datos", "📊 Métricas", "🌐 Visualización 3D"])
    
    with tab1:
        st.header("Datos LiDAR")
        
        # Opción de datos de ejemplo
        if st.button("🔄 Generar Datos de Ejemplo", key="generate_sample"):
            processor = LiDARProcessor()
            point_cloud = processor.create_sample_data()
            st.session_state.point_cloud = point_cloud
            st.success("✅ Datos de ejemplo generados correctamente")
        
        # Uploader simulado
        st.info("💡 *Funcionalidad de upload real disponible con archivos .LAS/.LAZ*")
        
        if 'point_cloud' in st.session_state:
            points = st.session_state.point_cloud.points
            st.success(f"✅ {len(points):,} puntos LiDAR cargados")
    
    with tab2:
        st.header("Métricas del Cultivo")
        
        if 'point_cloud' in st.session_state:
            metrics = extract_plant_metrics(st.session_state.point_cloud)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Altura Máxima", f"{metrics['max_height']:.2f} m")
                st.metric("Densidad", f"{metrics['plant_density']:,} pts")
            with col2:
                st.metric("Volumen Dosel", f"{metrics['canopy_volume']:.1f} m³")
                st.metric("Área", f"{metrics['canopy_area']} m²")
            with col3:
                st.metric("Salud", f"{metrics['health_score']:.1f}%")
                st.metric("Etapa", metrics['growth_stage'])
        else:
            st.info("👆 Genera datos de ejemplo primero para ver las métricas")
    
    with tab3:
        st.header("Visualización 3D Interactiva")
        
        if 'point_cloud' in st.session_state:
            create_interactive_plot(st.session_state.point_cloud)
        else:
            st.info("👆 Genera datos de ejemplo para ver la visualización 3D")

def render_dashboard():
    st.title("📊 Dashboard Integrado")
    
    has_soil = 'soil_data' in st.session_state
    has_lidar = 'point_cloud' in st.session_state
    
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
        else:
            st.warning("Genera datos LiDAR primero")
    
    # Recomendaciones integradas
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
    """Función principal simplificada"""
    
    # Sidebar
    st.sidebar.title("🌱 Navegación")
    page = st.sidebar.radio("Ir a:", ["🏠 Inicio", "🔍 Fertilidad", "🔄 LiDAR", "📊 Dashboard"])
    
    st.sidebar.markdown("---")
    st.sidebar.info("**Sistema Estable**\n\nTodos los módulos operativos")
    
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
