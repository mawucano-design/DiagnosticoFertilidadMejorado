import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# Añadir el path para importar módulos
sys.path.append(os.path.dirname(__file__))

# Configuración de la página ANTES de cualquier otra cosa
st.set_page_config(
    page_title="Plataforma Agrícola Integral",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Limpiar caché problemático
try:
    st.cache_data.clear()
except:
    pass

def safe_import(module_name, class_name=None):
    """Importación segura de módulos"""
    try:
        if class_name:
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        else:
            return __import__(module_name)
    except Exception as e:
        st.warning(f"⚠️ Módulo {module_name} no disponible: {str(e)}")
        return None

# Importaciones seguras
try:
    from gemelos_digitales import lidar_processor, model_generator, visualizacion_3d
    from fertilidad import analisis_suelo, recomendaciones
    MODULES_AVAILABLE = True
except Exception as e:
    st.error(f"❌ Error cargando módulos: {e}")
    MODULES_AVAILABLE = False

def initialize_session_state():
    """Inicializa el estado de la sesión de forma segura"""
    default_state = {
        'point_cloud': None,
        'vegetation_cloud': None,
        'processed_cloud': None,
        'soil_data': None,
        'lidar_processed': False,
        'app_initialized': True
    }
    
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_home():
    st.title("🌱 Plataforma de Agricultura de Precisión")
    
    st.markdown("""
    ## Bienvenido a la Plataforma Agrícola Integral
    
    Esta plataforma combina **diagnóstico de fertilidad** del suelo con **gemelos digitales** 
    basados en LiDAR para una agricultura de precisión completa.
    
    ### 🚀 Módulos Disponibles:
    
    **🔍 Diagnóstico de Fertilidad**
    - Análisis completo de suelo
    - Recomendaciones de fertilización
    - Historial de cultivos
    
    **🔄 Gemelos Digitales**
    - Procesamiento de datos LiDAR
    - Modelos 3D de cultivos
    - Métricas de crecimiento y salud
    
    **📊 Dashboard Integrado**
    - Vista unificada de todos los datos
    - Correlación suelo-crecimiento
    - Reportes automáticos
    """)

def show_digital_twins():
    st.title("🔄 Gemelos Digitales con LiDAR")
    
    if not MODULES_AVAILABLE:
        st.error("❌ Módulo de gemelos digitales no disponible")
        return
    
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Subir LiDAR", "⚙️ Procesamiento", "📊 Métricas", "🌐 Visualización 3D"])
    
    with tab1:
        st.header("Carga de Datos LiDAR")
        
        uploaded_file = st.file_uploader(
            "Subir archivo LiDAR (.las .laz)", 
            type=['las', 'laz'],
            help="Formatos soportados: LAS, LAZ"
        )
        
        if uploaded_file:
            try:
                # Guardar archivo temporalmente
                with open("temp_upload.las", "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                st.success(f"✅ Archivo {uploaded_file.name} subido correctamente")
                
                # Procesar LiDAR
                with st.spinner("Procesando datos LiDAR..."):
                    processor = lidar_processor.LiDARProcessor()
                    point_cloud = processor.load_lidar("temp_upload.las")
                    
                    if point_cloud:
                        st.session_state['point_cloud'] = point_cloud
                        st.session_state['lidar_processed'] = True
                        
                        # Mostrar info básica
                        points = np.asarray(point_cloud.points)
                        st.info(f"**Puntos procesados:** {len(points):,}")
                        
            except Exception as e:
                st.error(f"❌ Error procesando archivo: {str(e)}")
    
    with tab2:
        st.header("Procesamiento y Segmentación")
        
        if 'point_cloud' in st.session_state and st.session_state['point_cloud']:
            processor = lidar_processor.LiDARProcessor()
            processor.point_cloud = st.session_state['point_cloud']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Filtrado de Datos")
                remove_outliers = st.checkbox("Remover outliers", value=True)
                voxel_size = st.slider("Tamaño de voxel", 0.01, 0.5, 0.05)
                
                if st.button("Aplicar Procesamiento"):
                    try:
                        with st.spinner("Procesando..."):
                            processed_cloud = processor.apply_advanced_processing(
                                st.session_state['point_cloud'],
                                remove_outliers=remove_outliers,
                                voxel_size=voxel_size
                            )
                            st.session_state['processed_cloud'] = processed_cloud
                            st.success("Procesamiento completado")
                    except Exception as e:
                        st.error(f"Error en procesamiento: {str(e)}")
            
            with col2:
                st.subheader("Segmentación")
                if st.button("Segmentar Vegetación"):
                    try:
                        with st.spinner("Segmentando..."):
                            vegetation = processor.segment_vegetation()
                            if vegetation:
                                st.session_state['vegetation_cloud'] = vegetation
                                points_veg = np.asarray(vegetation.points)
                                st.success(f"Vegetación segmentada: {len(points_veg):,} puntos")
                    except Exception as e:
                        st.error(f"Error en segmentación: {str(e)}")
        else:
            st.warning("⏳ Primero sube un archivo LiDAR en la pestaña 'Subir LiDAR'")
    
    with tab3:
        st.header("Métricas y Análisis")
        
        if 'vegetation_cloud' in st.session_state and st.session_state['vegetation_cloud']:
            try:
                metrics = model_generator.extract_plant_metrics(st.session_state['vegetation_cloud'])
                
                # Mostrar métricas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Altura de Planta", f"{metrics.get('plant_height', 0):.2f} m")
                    st.metric("Densidad de Puntos", f"{metrics.get('plant_density', 0):,}")
                    
                with col2:
                    st.metric("Volumen de Dosel", f"{metrics.get('canopy_volume', 0):.2f} m³")
                    st.metric("Área de Dosel", f"{metrics.get('canopy_area', 0):.2f} m²")
                    
                with col3:
                    health_score = metrics.get('health_score', 0)
                    st.metric("Puntaje de Salud", f"{health_score:.1f}%")
                    st.metric("Etapa de Crecimiento", metrics.get('growth_stage', 'N/A'))
                
            except Exception as e:
                st.error(f"Error calculando métricas: {str(e)}")
        else:
            st.info("👆 Realiza la segmentación de vegetación primero para ver las métricas")
    
    with tab4:
        st.header("Visualización 3D Interactiva")
        
        if 'point_cloud' in st.session_state and st.session_state['point_cloud']:
            try:
                # Selector de nube de puntos a visualizar
                cloud_options = {
                    "Original": st.session_state['point_cloud'],
                    "Procesada": st.session_state.get('processed_cloud', st.session_state['point_cloud']),
                    "Vegetación": st.session_state.get('vegetation_cloud', st.session_state['point_cloud'])
                }
                
                selected_cloud = st.selectbox(
                    "Seleccionar nube de puntos para visualizar:",
                    list(cloud_options.keys())
                )
                
                visualizacion_3d.create_interactive_plot(cloud_options[selected_cloud])
            except Exception as e:
                st.error(f"Error en visualización: {str(e)}")
        else:
            st.warning("⏳ Sube un archivo LiDAR para ver la visualización 3D")

def show_fertility_diagnosis():
    st.title("🔍 Diagnóstico de Fertilidad del Suelo")
    if MODULES_AVAILABLE:
        analisis_suelo.main()
    else:
        st.error("❌ Módulo de fertilidad no disponible")

def show_integrated_dashboard():
    st.title("📊 Dashboard Agrícola Integrado")
    
    # Verificar si tenemos datos de ambos módulos
    has_fertility_data = 'soil_data' in st.session_state and st.session_state['soil_data']
    has_lidar_data = 'vegetation_cloud' in st.session_state and st.session_state['vegetation_cloud']
    
    if not has_fertility_data and not has_lidar_data:
        st.info("💡 Usa los módulos de Fertilidad y Gemelos Digitales para ver datos integrados aquí")
        return
    
    # Layout del dashboard
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏭 Diagnóstico de Suelo")
        if has_fertility_data:
            soil_data = st.session_state['soil_data']
            st.metric("Fertilidad General", f"{soil_data.get('fertility_score', 0)}%")
            st.metric("pH del Suelo", f"{soil_data.get('ph', 0)}")
            st.metric("Materia Orgánica", f"{soil_data.get('organic_matter', 0):.1f}%")
        else:
            st.warning("Ejecuta el diagnóstico de fertilidad primero")
    
    with col2:
        st.subheader("🌿 Estado del Cultivo (LiDAR)")
        if has_lidar_data:
            try:
                metrics = model_generator.extract_plant_metrics(st.session_state['vegetation_cloud'])
                st.metric("Salud del Dosel", f"{metrics.get('health_score', 0):.1f}%")
                st.metric("Crecimiento", f"{metrics.get('plant_height', 0):.2f} m")
                st.metric("Densidad", f"{metrics.get('plant_density', 0):,} pts")
            except Exception as e:
                st.error(f"Error obteniendo métricas LiDAR: {e}")
        else:
            st.warning("Procesa datos LiDAR primero")

def main():
    try:
        # Inicializar estado de sesión
        initialize_session_state()
        
        st.sidebar.title("🌱 Plataforma Agrícola Integral")
        st.sidebar.markdown("---")
        
        # Navegación unificada
        app_mode = st.sidebar.selectbox(
            "Seleccionar Módulo",
            ["🏠 Inicio", "🔍 Diagnóstico Fertilidad", "🔄 Gemelos Digitales", "📊 Dashboard Integrado"]
        )
        
        st.sidebar.markdown("---")
        st.sidebar.info(
            "Plataforma desarrollada para agricultura de precisión. "
            "Combina análisis tradicional con tecnología LiDAR."
        )
        
        # Botón para limpiar caché
        if st.sidebar.button("🔄 Limpiar Caché"):
            try:
                st.cache_data.clear()
                for key in list(st.session_state.keys()):
                    if key != 'app_initialized':
                        del st.session_state[key]
                st.rerun()
            except:
                st.sidebar.warning("Error limpiando caché")
        
        # Navegación
        if app_mode == "🏠 Inicio":
            show_home()
        elif app_mode == "🔍 Diagnóstico Fertilidad":
            show_fertility_diagnosis()
        elif app_mode == "🔄 Gemelos Digitales":
            show_digital_twins()
        elif app_mode == "📊 Dashboard Integrado":
            show_integrated_dashboard()
            
    except Exception as e:
        st.error(f"❌ Error crítico en la aplicación: {str(e)}")
        st.info("💡 Intenta recargar la página o limpiar el caché del navegador")

if __name__ == "__main__":
    main()
