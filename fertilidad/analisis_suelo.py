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
            rendimiento_esperado = st.number_input("Rendimiento Esperado (kg/ha)", 
                                                 min_value=1000, max_value=15000, value=5000)
        
        # Submit button
        submitted = st.form_submit_button("🔬 Analizar Suelo")
    
    if submitted:
        # Procesar análisis
        analizar_suelo(ph, materia_organica, textura, nitrogeno, fosforo, potasio,
                      capacidad_campo, conductividad, cultivo, rendimiento_esperado)

def analizar_suelo(ph, materia_organica, textura, nitrogeno, fosforo, potasio,
                  capacidad_campo, conductividad, cultivo, rendimiento_esperado):
    """Realiza el análisis completo del suelo"""
    
    # Calcular puntajes individuales
    puntaje_ph = calcular_puntaje_ph(ph, cultivo)
    puntaje_mo = calcular_puntaje_materia_organica(materia_organica, textura)
    puntaje_n = calcular_puntaje_nitrogeno(nitrogeno, cultivo)
    puntaje_p = calcular_puntaje_fosforo(fosforo, cultivo)
    puntaje_k = calcular_puntaje_potasio(potasio, cultivo)
    puntaje_textura = calcular_puntaje_textura(textura)
    puntaje_ce = calcular_puntaje_conductividad(conductividad)
    
    # Puntaje general ponderado
    puntaje_general = (
        puntaje_ph * 0.15 +
        puntaje_mo * 0.20 +
        puntaje_n * 0.25 +
        puntaje_p * 0.20 +
        puntaje_k * 0.15 +
        puntaje_textura * 0.03 +
        puntaje_ce * 0.02
    )
    
    # Guardar en session state para el dashboard
    st.session_state['soil_data'] = {
        'ph': ph,
        'organic_matter': materia_organica,
        'texture': textura,
        'nitrogen': nitrogeno,
        'phosphorus': fosforo,
        'potassium': potasio,
        'field_capacity': capacidad_campo,
        'conductivity': conductividad,
        'crop': cultivo,
        'expected_yield': rendimiento_esperado,
        'fertility_score': puntaje_general
    }
    
    # Mostrar resultados
    mostrar_resultados({
        'ph': {'valor': ph, 'puntaje': puntaje_ph, 'categoria': categorizar_ph(ph)},
        'materia_organica': {'valor': materia_organica, 'puntaje': puntaje_mo, 'categoria': categorizar_mo(materia_organica)},
        'nitrogeno': {'valor': nitrogeno, 'puntaje': puntaje_n, 'categoria': categorizar_nitrogeno(nitrogeno)},
        'fosforo': {'valor': fosforo, 'puntaje': puntaje_p, 'categoria': categorizar_fosforo(fosforo)},
        'potasio': {'valor': potasio, 'puntaje': puntaje_k, 'categoria': categorizar_potasio(potasio)},
        'puntaje_general': puntaje_general
    }, cultivo)

def calcular_puntaje_ph(ph, cultivo):
    """Calcula puntaje de pH según cultivo"""
    rangos_optimos = {
        "Maíz": (5.8, 7.0),
        "Soja": (6.0, 7.0),
        "Trigo": (6.0, 7.5),
        "Girasol": (6.0, 7.5),
        "Algodón": (5.5, 7.0)
    }
    
    optimo = rangos_optimos.get(cultivo, (6.0, 7.0))
    if optimo[0] <= ph <= optimo[1]:
        return 100
    elif ph < optimo[0] - 1 or ph > optimo[1] + 1:
        return 30
    else:
        return 70

def calcular_puntaje_materia_organica(mo, textura):
    """Calcula puntaje de materia orgánica"""
    rangos_optimos = {
        "Arenoso": (2.0, 4.0),
        "Franco": (3.0, 5.0),
        "Arcilloso": (4.0, 6.0)
    }
    
    optimo = rangos_optimos.get(textura, (3.0, 5.0))
    if optimo[0] <= mo <= optimo[1]:
        return 100
    elif mo < optimo[0] - 1:
        return 40
    else:
        return 80

def calcular_puntaje_nitrogeno(nitrogeno, cultivo):
    """Calcula puntaje de nitrógeno"""
    rangos = {
        "Maíz": (40, 80),
        "Soja": (30, 60),
        "Trigo": (35, 70),
        "Girasol": (25, 50),
        "Algodón": (40, 75)
    }
    
    optimo = rangos.get(cultivo, (40, 70))
    if optimo[0] <= nitrogeno <= optimo[1]:
        return 100
    elif nitrogeno < optimo[0] - 20:
        return 30
    elif nitrogeno < optimo[0]:
        return 70
    else:
        return 80

def calcular_puntaje_fosforo(fosforo, cultivo):
    """Calcula puntaje de fósforo"""
    rangos = {
        "Maíz": (25, 50),
        "Soja": (20, 40),
        "Trigo": (20, 45),
        "Girasol": (15, 35),
        "Algodón": (25, 50)
    }
    
    optimo = rangos.get(cultivo, (20, 45))
    if optimo[0] <= fosforo <= optimo[1]:
        return 100
    elif fosforo < optimo[0] - 10:
        return 35
    elif fosforo < optimo[0]:
        return 75
    else:
        return 85

def calcular_puntaje_potasio(potasio, cultivo):
    """Calcula puntaje de potasio"""
    rangos = {
        "Maíz": (120, 200),
        "Soja": (100, 180),
        "Trigo": (100, 170),
        "Girasol": (80, 150),
        "Algodón": (120, 200)
    }
    
    optimo = rangos.get(cultivo, (100, 180))
    if optimo[0] <= potasio <= optimo[1]:
        return 100
    elif potasio < optimo[0] - 50:
        return 30
    elif potasio < optimo[0]:
        return 70
    else:
        return 85

def calcular_puntaje_textura(textura):
    """Calcula puntaje de textura"""
    puntajes = {"Franco": 100, "Arcilloso": 80, "Arenoso": 60}
    return puntajes.get(textura, 70)

def calcular_puntaje_conductividad(ce):
    """Calcula puntaje de conductividad eléctrica"""
    if ce < 2.0:
        return 100
    elif ce < 4.0:
        return 80
    elif ce < 6.0:
        return 50
    else:
        return 20

def categorizar_ph(ph):
    if ph < 5.5: return "Muy Ácido"
    elif ph < 6.5: return "Ligeramente Ácido"
    elif ph < 7.5: return "Neutro"
    elif ph < 8.5: return "Alcalino"
    else: return "Muy Alcalino"

def categorizar_mo(mo):
    if mo < 1.0: return "Muy Baja"
    elif mo < 2.0: return "Baja"
    elif mo < 4.0: return "Media"
    elif mo < 6.0: return "Alta"
    else: return "Muy Alta"

def categorizar_nitrogeno(n):
    if n < 20: return "Muy Bajo"
    elif n < 40: return "Bajo"
    elif n < 80: return "Óptimo"
    elif n < 120: return "Alto"
    else: return "Muy Alto"

def categorizar_fosforo(p):
    if p < 10: return "Muy Bajo"
    elif p < 20: return "Bajo"
    elif p < 50: return "Óptimo"
    elif p < 80: return "Alto"
    else: return "Muy Alto"

def categorizar_potasio(k):
    if k < 50: return "Muy Bajo"
    elif k < 100: return "Bajo"
    elif k < 200: return "Óptimo"
    elif k < 300: return "Alto"
    else: return "Muy Alto"

def mostrar_resultados(resultados, cultivo):
    """Muestra los resultados del análisis"""
    st.header("📊 Resultados del Análisis")
    
    # Puntaje general
    puntaje = resultados['puntaje_general']
    st.subheader(f"Puntaje General de Fertilidad: {puntaje:.0f}/100")
    
    # Barra de progreso
    progress_color = "red" if puntaje < 50 else "orange" if puntaje < 70 else "green"
    st.markdown(f"""
    <div style="background-color: #f0f0f0; border-radius: 10px; padding: 5px;">
        <div style="background-color: {progress_color}; width: {puntaje}%; 
                    height: 20px; border-radius: 8px; text-align: center; color: white;">
            {puntaje:.0f}%
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas detalladas
    st.subheader("📈 Métricas Detalladas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("pH", f"{resultados['ph']['valor']}", resultados['ph']['categoria'])
        st.metric("Materia Orgánica", f"{resultados['materia_organica']['valor']}%", 
                 resultados['materia_organica']['categoria'])
    
    with col2:
        st.metric("Nitrógeno", f"{resultados['nitrogeno']['valor']} ppm", 
                 resultados['nitrogeno']['categoria'])
        st.metric("Fósforo", f"{resultados['fosforo']['valor']} ppm", 
                 resultados['fosforo']['categoria'])
    
    with col3:
        st.metric("Potasio", f"{resultados['potasio']['valor']} ppm", 
                 resultados['potasio']['categoria'])
        st.metric("Fertilidad General", f"{puntaje:.0f}%", 
                 "Excelente" if puntaje >= 80 else "Buena" if puntaje >= 60 else "Regular" if puntaje >= 40 else "Mala")
    
    # Recomendaciones
    st.header("🎯 Recomendaciones")
    generar_recomendaciones(resultados, cultivo)
