import streamlit as st
import pandas as pd
import numpy as np
from gemelos_digitales import lidar_processor, model_generator, visualizacion_3d
from fertilidad import analisis_suelo, recomendaciones
import os

# Configuración de la página
st.set_page_config(
    page_title="Plataforma Agrícola Integral",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    # Métricas rápidas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Precisión Análisis", "95%", "2%")
    with col2:
        st.metric Cultivos Analizados", "15", "3")
    with col3:
        st.metric("Eficiencia Mejorada", "30%", "5%")

def show_digital_twins():
    st.title("🔄 Gemelos Digitales con LiDAR")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Subir LiDAR", "⚙️ Procesamiento", "📊 Métricas", "🌐 Visualización 3D"])
    
    with tab1:
        st.header("Carga de Datos LiDAR")
        
        uploaded_file = st.file_uploader(
            "Subir archivo LiDAR (.las .laz)", 
            type=['las', 'laz'],
            help="Formatos soportados: LAS, LAZ"
        )
        
        if uploaded_file:
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
                    
    with tab2:
        st.header("Procesamiento y Segmentación")
        
        if 'point_cloud' in st.session_state:
            processor = lidar_processor.LiDARProcessor()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Filtrado de Datos")
                remove_outliers = st.checkbox("Remover outliers", value=True)
                voxel_size = st.slider("Tamaño de voxel", 0.01, 0.5, 0.05)
                
                if st.button("Aplicar Procesamiento"):
                    with st.spinner("Procesando..."):
                        processed_cloud = processor.apply_advanced_processing(
                            st.session_state['point_cloud'],
                            remove_outliers=remove_outliers,
                            voxel_size=voxel_size
                        )
                        st.session_state['processed_cloud'] = processed_cloud
                        st.success("Procesamiento completado")
            
            with col2:
                st.subheader("Segmentación")
                if st.button("Segmentar Vegetación"):
                    with st.spinner("Segmentando..."):
                        vegetation = processor.segment_vegetation()
                        if vegetation:
                            st.session_state['vegetation_cloud'] = vegetation
                            points_veg = np.asarray(vegetation.points)
                            st.success(f"Vegetación segmentada: {len(points_veg):,} puntos")
        else:
            st.warning("⏳ Primero sube un archivo LiDAR en la pestaña 'Subir LiDAR'")
    
    with tab3:
        st.header("Métricas y Análisis")
        
        if 'vegetation_cloud' in st.session_state:
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
            
            # Análisis detallado
            st.subheader("Análisis Detallado")
            st.json(metrics)
            
        else:
            st.info("👆 Realiza la segmentación de vegetación primero para ver las métricas")
    
    with tab4:
        st.header("Visualización 3D Interactiva")
        
        if 'point_cloud' in st.session_state:
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
        else:
            st.warning("⏳ Sube un archivo LiDAR para ver la visualización 3D")

def show_fertility_diagnosis():
    st.title("🔍 Diagnóstico de Fertilidad del Suelo")
    analisis_suelo.main()

def show_integrated_dashboard():
    st.title("📊 Dashboard Agrícola Integrado")
    
    # Verificar si tenemos datos de ambos módulos
    has_fertility_data = 'soil_data' in st.session_state
    has_lidar_data = 'vegetation_cloud' in st.session_state
    
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
            metrics = model_generator.extract_plant_metrics(st.session_state['vegetation_cloud'])
            st.metric("Salud del Dosel", f"{metrics.get('health_score', 0):.1f}%")
            st.metric("Crecimiento", f"{metrics.get('plant_height', 0):.2f} m")
            st.metric("Densidad", f"{metrics.get('plant_density', 0):,} pts")
        else:
            st.warning("Procesa datos LiDAR primero")
    
    # Recomendaciones integradas
    if has_fertility_data and has_lidar_data:
        st.subheader("🎯 Recomendaciones Integradas")
        
        soil_data = st.session_state['soil_data']
        lidar_metrics = model_generator.extract_plant_metrics(st.session_state['vegetation_cloud'])
        
        # Lógica de recomendación integrada
        health_score = lidar_metrics.get('health_score', 0)
        fertility_score = soil_data.get('fertility_score', 0)
        
        if health_score < 70 and fertility_score < 60:
            st.error("**Acción Requerida:** Tanto la salud del cultivo como la fertilidad del suelo son bajas. Considera:")
            st.write("- Aplicación de fertilizantes balanceados")
            st.write("- Riego adecuado")
            st.write("- Análisis de plagas y enfermedades")
        elif health_score < 70:
            st.warning("**Atención:** Salud del cultivo baja a pesar de buena fertilidad. Verifica:")
            st.write("- Riego y drenaje")
            st.write("- Presencia de plagas")
            st.write("- Condiciones climáticas")
        elif fertility_score < 60:
            st.warning("**Atención:** Fertilidad del suelo baja. Considera enmiendas:")
            st.write("- Aplicación de materia orgánica")
            st.write("- Corrección de pH si es necesario")
            st.write("- Fertilización específica")
        else:
            st.success("**✅ Estado Óptimo:** Cultivo y suelo en condiciones excelentes. Mantén las prácticas actuales.")

def main():
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
    
    # Navegación
    if app_mode == "🏠 Inicio":
        show_home()
    elif app_mode == "🔍 Diagnóstico Fertilidad":
        show_fertility_diagnosis()
    elif app_mode == "🔄 Gemelos Digitales":
        show_digital_twins()
    elif app_mode == "📊 Dashboard Integrado":
        show_integrated_dashboard()

if __name__ == "__main__":
    main()
