import streamlit as st
import pandas as pd
import numpy as np
from .recomendaciones import generar_recomendaciones

def main():
    st.title("🔍 Análisis de Fertilidad del Suelo")
    
    st.markdown("""
    Complete los parámetros del suelo para obtener un diagnóstico detallado 
    y recomendaciones de fertilización específicas.
    """)
    
    # Formulario de entrada de datos
    with st.form("soil_analysis_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Parámetros Básicos")
            ph = st.slider("pH del suelo", 3.0, 9.0, 6.5, 0.1)
            materia_organica = st.slider("Materia Orgánica (%)", 0.1, 10.0, 2.5, 0.1)
            textura = st.selectbox("Textura del Suelo", 
                                 ["Arcilloso", "Franco", "Arenoso"])
            
        with col2:
            st.subheader("Nutrientes Principales")
            nitrogeno = st.slider("Nitrógeno (ppm)", 0, 200, 50)
            fosforo = st.slider("Fósforo (ppm)", 0, 150, 30)
            potasio = st.slider("Potasio (ppm)", 0, 300, 100)
        
        st.subheader("Parámetros Adicionales")
        col3, col4 = st.columns(2)
        
        with col3:
            capacidad_campo = st.slider("Capacidad de Campo (%)", 10, 50, 25)
            conductividad = st.slider("Conductividad Eléctrica (dS/m)", 0.0, 8.0, 1.5, 0.1)
        
        with col4:
            cultivo = st.selectbox("Cultivo Principal", 
                                 ["Maíz", "Soja", "Trigo", "Girasol", "Algodón", "Otro"])
            rendimiento_esperado = st
