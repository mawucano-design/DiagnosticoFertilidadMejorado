import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# CONFIGURACIÓN CRÍTICA - debe ser lo PRIMERO
st.set_page_config(
    page_title="Plataforma Agrícola Integral",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# EVITAR CACHÉ PROBLEMÁTICO
@st.cache_resource(show_spinner=False)
def get_session_id():
    return str(hash(st.session_state.get('_runtime', {})))

# IMPORTACIONES SEGURAS CON FALLBACK
def safe_import_module(module_path, class_name=None):
    """Importación segura con manejo de errores robusto"""
    try:
        module = __import__(module_path, fromlist=[class_name] if class_name else [])
        return getattr(module, class_name) if class_name else module
    except ImportError as e:
        st.warning(f"⚠️ Módulo {module_path} no disponible: {e}")
        return None
    except Exception as e:
        st.warning(f"⚠️ Error cargando {module_path}: {e}")
        return None

# Intentar cargar módulos
try:
    from gemelos_digitales.lidar_processor import LiDARProcessor
    from gemelos_digitales.model_generator import extract_plant_metrics
    from gemelos_digitales.visualizacion_3d import create_interactive_plot
    LIDAR_AVAILABLE = True
except:
    LIDAR_AVAILABLE = False
    st.warning("🔧 Módulo LiDAR no disponible")

try:
    from fertilidad.analisis_suelo import main as analisis_suelo_main
    FERTILIDAD_AVAILABLE = True
except:
    FERTILIDAD_AVAILABLE = False
    st.warning("🔧 Módulo Fertilidad no disponible")

# INICIALIZACIÓN SEGURA DEL ESTADO
def initialize_session_state():
    """Inicialización robusta del estado de sesión"""
    defaults = {
        'app_initialized': True,
        'current_page': 'home',
        'point_cloud': None,
        'vegetation_cloud': None,
        'soil_data': None,
        'session_id': get_session_id()
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# COMPONENTES DE UI SEGUROS
def create_safe_button(label, key_suffix):
    """Crea botones de forma segura con keys únicos"""
    return st.button(label, key=f"btn_{key_suffix}_{st.session_state.session_id}")

def create_safe_selectbox(label, options, key_suffix, index=0):
    """Crea selectbox de forma segura"""
    return st.selectbox(
        label, 
        options, 
        index=index,
        key=f"select_{key_suffix}_{st.session_state.session_id}"
    )

# PÁGINAS PRINCIPALES
def render_home():
    """Página de inicio - mínima interacción"""
    st.title("🌱 Plataforma de Agricultura de Precisión")
    
    st.markdown("""
    ## Bienvenido a la Plataforma Agrícola Integral
    
    **Módulos disponibles:**
    - 🔍 **Diagnóstico de Fertilidad**: Análisis completo de suelo
    - 🔄 **Gemelos Digitales**: Procesamiento LiDAR y modelos 3D
    - 📊 **Dashboard Integrado**: Vista unificada de datos
    
    ### Instrucciones rápidas:
    1. Navega entre módulos usando el menú lateral
    2. Los datos se mantienen durante tu sesión
    3. Usa 'Limpiar Sesión' si encuentras problemas
    """)
    
    # Métricas simples sin estado complejo
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Sesión Activa", "✅")
    with col2:
        st.metric("Módulos Cargados", f"{2 if LIDAR_AVAILABLE and FERTILIDAD_AVAILABLE else 1}/2")
    with col3:
        st.metric("Estado", "Estable")

def render_fertility():
    """Página de fertilidad - simplificada"""
    st.title("🔍 Diagnóstico de Fertilidad del Suelo")
    
    if FERTILIDAD_AVAILABLE:
        try:
            analisis_suelo_main()
        except Exception as e:
            st.error(f"❌ Error en módulo fertilidad: {e}")
            show_fallback_fertility()
    else:
        show_fallback_fertility()

def show_fallback_fertility():
    """Versión de respaldo del módulo fertilidad"""
    st.warning("Usando versión simplificada del análisis de suelo")
    
    with st.form("simple_soil_analysis"):
        ph = st.slider("pH del suelo", 3.0, 9.0, 6.5, 0.1)
        nitrogeno = st.slider("Nitrógeno (ppm)", 0, 200, 50)
        
        if st.form_submit_button("Analizar"):
            # Análisis simple
            score = min(100, max(0, (ph - 4) * 20 + nitrogeno / 2))
            st.session_state.soil_data = {
                'ph': ph,
                'nitrogen': nitrogeno,
                'fertility_score': score
            }
            st.success(f"Puntaje de fertilidad: {score:.0f}/100")

def render_lidar():
    """Página LiDAR - simplificada y estable"""
    st.title("🔄 Gemelos Digitales con LiDAR")
    
    if not LIDAR_AVAILABLE:
        st.error("❌ Módulo LiDAR no disponible en esta sesión")
        st.info("💡 Recarga la aplicación para intentar cargar los módulos")
        return
    
    # Pestañas simplificadas
    tab1, tab2 = st.tabs(["📤 Carga de Datos", "📊 Visualización"])
    
    with tab1:
        handle_lidar_upload()
    
    with tab2:
        handle_lidar_visualization()

def handle_lidar_upload():
    """Manejo seguro de carga LiDAR"""
    st.header("Carga de Datos LiDAR")
    
    uploaded_file = st.file_uploader(
        "Subir archivo LiDAR (.las .laz)", 
        type=['las', 'laz'],
        key=f"file_uploader_{st.session_state.session_id}"
    )
    
    if uploaded_file is not None:
        try:
            with st.spinner("Procesando archivo LiDAR..."):
                # Simulación de procesamiento para evitar errores
                st.success(f"✅ Archivo {uploaded_file.name} recibido")
                st.info("🔧 Procesamiento LiDAR en desarrollo...")
                
                # Datos de ejemplo para demostración
                points = np.random.rand(1000, 3) * 10
                st.session_state.point_cloud = type('PointCloud', (), {'points': points})()
                st.session_state.lidar_processed = True
                
        except Exception as e:
            st.error(f"❌ Error procesando LiDAR: {e}")

def handle_lidar_visualization():
    """Visualización LiDAR segura"""
    if hasattr(st.session_state, 'point_cloud') and st.session_state.point_cloud:
        st.header("Visualización de Datos LiDAR")
        
        try:
            # Visualización simple con Plotly
            points = st.session_state.point_cloud.points
            
            import plotly.graph_objects as go
            
            fig = go.Figure(data=[go.Scatter3d(
                x=points[:, 0],
                y=points[:, 1], 
                z=points[:, 2],
                mode='markers',
                marker=dict(size=2, color=points[:, 2], colorscale='Viridis')
            )])
            
            fig.update_layout(title="Visualización 3D - Datos de Ejemplo")
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error en visualización: {e}")
    else:
        st.info("📁 Sube un archivo LiDAR para ver la visualización")

def render_dashboard():
    """Dashboard simplificado"""
    st.title("📊 Dashboard Integrado")
    
    has_soil = hasattr(st.session_state, 'soil_data') and st.session_state.soil_data
    has_lidar = hasattr(st.session_state, 'point_cloud') and st.session_state.point_cloud
    
    if not has_soil and not has_lidar:
        st.info("💡 Usa los otros módulos para ver datos integrados aquí")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏭 Estado del Suelo")
        if has_soil:
            soil = st.session_state.soil_data
            st.metric("Fertilidad", f"{soil.get('fertility_score', 0)}%")
            st.metric("pH", f"{soil.get('ph', 0)}")
        else:
            st.warning("Sin datos de suelo")
    
    with col2:
        st.subheader("🌿 Estado del Cultivo")
        if has_lidar:
            st.metric("Puntos LiDAR", f"{len(st.session_state.point_cloud.points):,}")
            st.metric("Procesado", "✅")
        else:
            st.warning("Sin datos LiDAR")

# SIDEBAR SEGURO
def render_sidebar():
    """Sidebar simplificado y estable"""
    st.sidebar.title("🌱 Navegación")
    
    # Navegación simple sin estado complejo
    page_options = ["🏠 Inicio", "🔍 Fertilidad", "🔄 LiDAR", "📊 Dashboard"]
    selected_page = st.sidebar.radio(
        "Ir a:",
        page_options,
        key=f"nav_radio_{st.session_state.session_id}"
    )
    
    st.sidebar.markdown("---")
    
    # Botón de reset seguro
    if st.sidebar.button("🔄 Limpiar Sesión", key="reset_btn"):
        clear_session_safe()
    
    st.sidebar.info("Sesión: " + st.session_state.session_id[:8])
    
    return selected_page

def clear_session_safe():
    """Limpieza segura de sesión"""
    try:
        # Mantener solo lo esencial
        keep_keys = ['app_initialized', 'session_id']
        new_state = {k: st.session_state[k] for k in keep_keys if k in st.session_state}
        
        # Limpiar todo
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Restaurar esenciales
        for key, value in new_state.items():
            st.session_state[key] = value
            
        st.success("✅ Sesión limpiada correctamente")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error limpiando sesión: {e}")

# APLICACIÓN PRINCIPAL
def main():
    """Función principal con manejo robusto de errores"""
    try:
        # Inicialización
        initialize_session_state()
        
        # Sidebar
        selected_page = render_sidebar()
        
        # Navegación
        page_map = {
            "🏠 Inicio": render_home,
            "🔍 Fertilidad": render_fertility, 
            "🔄 LiDAR": render_lidar,
            "📊 Dashboard": render_dashboard
        }
        
        # Renderizar página seleccionada
        if selected_page in page_map:
            page_map[selected_page]()
        else:
            render_home()
            
    except Exception as e:
        # ERROR CRÍTICO - Mostrar pantalla de error amigable
        st.error("""
        🚨 **Error crítico en la aplicación**
        
        Por favor:
        1. Recarga la página (F5 o Ctrl+R)
        2. Usa el botón 'Limpiar Sesión' en el sidebar
        3. Si persiste, contacta al administrador
        """)
        
        # Debug info (opcional)
        if st.checkbox("Mostrar detalles técnicos"):
            st.code(f"Error: {str(e)}")

# PUNTO DE ENTRADA SEGURO
if __name__ == "__main__":
    main()
