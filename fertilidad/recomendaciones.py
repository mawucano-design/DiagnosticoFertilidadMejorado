import streamlit as st

def generar_recomendaciones(resultados, cultivo):
    """Genera recomendaciones basadas en los resultados del análisis"""
    
    recomendaciones = []
    
    # Recomendaciones de pH
    ph_valor = resultados['ph']['valor']
    if ph_valor < 5.5:
        recomendaciones.append("""
        **🔴 Corrección de Acidez:**
        - Aplicar cal agrícola: 2-4 ton/ha según análisis
        - Preferir calcáreo dolomítico si hay deficiencia de Mg
        - Incorporar 3 meses antes de la siembra
        """)
    elif ph_valor > 7.5:
        recomendaciones.append("""
        **🟡 Corrección de Alcalinidad:**
        - Aplicar azufre elemental: 500-1000 kg/ha
        - Considerar uso de yeso agrícola
        - Incorporar materia orgánica acidificante
        """)
    
    # Recomendaciones de Materia Orgánica
    mo_valor = resultados['materia_organica']['valor']
    if mo_valor < 2.0:
        recomendaciones.append("""
        **🔴 Mejora de Materia Orgánica:**
        - Aplicar 10-20 ton/ha de estiércol compostado
        - Implementar abonos verdes (vicia, avena)
        - Considerar siembra directa con cobertura
        - Aplicar compost: 5-10 ton/ha
        """)
    
    # Recomendaciones de Nitrógeno
    n_valor = resultados['nitrogeno']['valor']
    n_categoria = resultados['nitrogeno']['categoria']
    
    if n_categoria in ["Muy Bajo", "Bajo"]:
        dosis_n = calcular_dosis_nitrogeno(cultivo, n_valor)
        recomendaciones.append(f"""
        **🔴 Fertilización Nitrogenada:**
        - Dosis recomendada: {dosis_n} kg N/ha
        - Fuentes recomendadas: Urea (46% N), Nitrato de amonio (34% N)
        - Aplicar 50% en siembra y 50% en encañado (para cereales)
        """)
    
    # Recomendaciones de Fósforo
    p_valor = resultados['fosforo']['valor']
    p_categoria = resultados['fosforo']['categoria']
    
    if p_categoria in ["Muy Bajo", "Bajo"]:
        dosis_p = calcular_dosis_fosforo(cultivo, p_valor)
        recomendaciones.append(f"""
        **🟡 Fertilización Fosfatada:**
        - Dosis recomendada: {dosis_p} kg P₂O₅/ha
        - Fuentes recomendadas: Superfosfato triple (46% P₂O₅)
        - Aplicar total en siembra, incorporar superficialmente
        """)
    
    # Recomendaciones de Potasio
    k_valor = resultados['potasio']['valor']
    k_categoria = resultados['potasio']['categoria']
    
    if k_categoria in ["Muy Bajo", "Bajo"]:
        dosis_k = calcular_dosis_potasio(cultivo, k_valor)
        recomendaciones.append(f"""
        **🟡 Fertilización Potásica:**
        - Dosis recomendada: {dosis_k} kg K₂O/ha
        - Fuentes recomendadas: Cloruro de potasio (60% K₂O)
        - Aplicar total en siembra
        """)
    
    # Recomendaciones generales según puntaje
    puntaje = resultados['puntaje_general']
    
    if puntaje >= 80:
        recomendaciones.append("""
        **🟢 Mantenimiento:**
        - Suelo en condiciones óptimas
        - Mantener prácticas de manejo actuales
        - Monitorear nutrientes anualmente
        - Continuar con rotación de cultivos
        """)
    elif puntaje >= 60:
        recomendaciones.append("""
        **🟡 Mejora Continua:**
        - Mantener programa de fertilización balanceada
        - Incrementar materia orgánica gradualmente
        - Monitorear pH cada 2 años
        - Considerar análisis foliares complementarios
        """)
    else:
        recomendaciones.append("""
        **🔴 Plan de Mejora Integral:**
        - Realizar análisis de suelo cada 6 meses
        - Implementar plan de enmiendas correctivas
        - Considerar asesoramiento técnico especializado
        - Evaluar sistema de riego y drenaje
        """)
    
    # Mostrar todas las recomendaciones
    for i, rec in enumerate(recomendaciones, 1):
        st.markdown(rec)
        
    # Plan de acción resumido
    st.subheader("📋 Plan de Acción Resumido")
    
    acciones_prioritarias = []
    if any(cat in resultados['ph']['categoria'] for cat in ["Muy Ácido", "Muy Alcalino"]):
        acciones_prioritarias.append("✅ Corrección de pH (prioridad alta)")
    if resultados['materia_organica']['categoria'] in ["Muy Baja", "Baja"]:
        acciones_prioritarias.append("✅ Mejora de materia orgánica (prioridad media-alta)")
    if any(cat in resultados['nitrogeno']['categoria'] for cat in ["Muy Bajo", "Bajo"]):
        acciones_prioritarias.append("✅ Fertilización nitrogenada (prioridad alta)")
    if any(cat in resultados['fosforo']['categoria'] for cat in ["Muy Bajo", "Bajo"]):
        acciones_prioritarias.append("✅ Fertilización fosfatada (prioridad media)")
    if any(cat in resultados['potasio']['categoria'] for cat in ["Muy Bajo", "Bajo"]):
        acciones_prioritarias.append("✅ Fertilización potásica (prioridad media)")
    
    for accion in acciones_prioritarias:
        st.write(accion)

def calcular_dosis_nitrogeno(cultivo, nivel_n):
    """Calcula dosis de nitrógeno según cultivo y nivel actual"""
    dosis_base = {
        "Maíz": 120,
        "Soja": 0,  # Soja fija su propio N
        "Trigo": 80,
        "Girasol": 60,
        "Algodón": 90
    }
    
    dosis = dosis_base.get(cultivo, 80)
    
    # Ajustar según nivel actual
    if nivel_n < 20:
        return dosis + 40
    elif nivel_n < 40:
        return dosis + 20
    elif nivel_n > 100:
        return max(dosis - 30, 30)
    else:
        return dosis

def calcular_dosis_fosforo(cultivo, nivel_p):
    """Calcula dosis de fósforo según cultivo y nivel actual"""
    dosis_base = {
        "Maíz": 60,
        "Soja": 40,
        "Trigo": 50,
        "Girasol": 35,
        "Algodón": 55
    }
    
    dosis = dosis_base.get(cultivo, 45)
    
    # Ajustar según nivel actual
    if nivel_p < 10:
        return dosis + 30
    elif nivel_p < 20:
        return dosis + 15
    elif nivel_p > 60:
        return max(dosis - 20, 20)
    else:
        return dosis

def calcular_dosis_potasio(cultivo, nivel_k):
    """Calcula dosis de potasio según cultivo y nivel actual"""
    dosis_base = {
        "Maíz": 80,
        "Soja": 60,
        "Trigo": 70,
        "Girasol": 50,
        "Algodón": 75
    }
    
    dosis = dosis_base.get(cultivo, 65)
    
    # Ajustar según nivel actual
    if nivel_k < 50:
        return dosis + 40
    elif nivel_k < 100:
        return dosis + 20
    elif nivel_k > 250:
        return max(dosis - 30, 30)
    else:
        return dosis
