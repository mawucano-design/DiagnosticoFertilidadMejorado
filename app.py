from flask import Flask, render_template, request, jsonify, send_file
import json
import os
from datetime import datetime
import tempfile

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_fertility():
    """Analizar fertilidad del polígono"""
    try:
        data = request.json
        geojson = data.get('geojson')
        crop = data.get('crop', 'trigo')
        
        # Análisis de fertilidad simplificado
        analysis_result = simulate_fertility_analysis(geojson, crop)
        
        return jsonify({
            'success': True,
            'result': analysis_result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/export', methods=['POST'])
def export_geojson():
    """Exportar GeoJSON como archivo descargable"""
    try:
        data = request.json
        geojson = data.get('geojson')
        crop = data.get('crop', 'trigo')
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
            # Añadir metadatos
            geojson['properties'] = {
                'export_date': datetime.now().isoformat(),
                'crop': crop,
                'analyzed_by': 'Analizador de Fertilidad'
            }
            json.dump(geojson, f, indent=2)
            temp_path = f.name
        
        # Enviar archivo
        filename = f"fertilidad_{crop}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson"
        return send_file(temp_path, as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def simulate_fertility_analysis(geojson, crop):
    """Simular análisis de fertilidad basado en el polígono y cultivo"""
    import random
    
    crop_requirements = {
        'trigo': {'n': 'alto', 'p': 'medio', 'k': 'medio', 'ph_optimo': 6.0},
        'maiz': {'n': 'muy_alto', 'p': 'alto', 'k': 'alto', 'ph_optimo': 6.5},
        'soja': {'n': 'medio', 'p': 'alto', 'k': 'medio', 'ph_optimo': 6.8},
        'sorgo': {'n': 'medio', 'p': 'medio', 'k': 'alto', 'ph_optimo': 6.2},
        'girasol': {'n': 'bajo', 'p': 'medio', 'k': 'medio', 'ph_optimo': 6.5}
    }
    
    # Calcular área aproximada (sin shapely)
    area_hectares = calculate_area_approximate(geojson)
    
    requirements = crop_requirements.get(crop, crop_requirements['trigo'])
    
    return {
        'crop': crop,
        'area_hectareas': area_hectares,
        'parametros': {
            'nitrogeno': random.choice(['bajo', 'medio', 'alto']),
            'fosforo': random.choice(['bajo', 'medio', 'alto']),
            'potasio': random.choice(['bajo', 'medio', 'alto']),
            'ph': round(random.uniform(5.0, 7.5), 1),
            'materia_organica': round(random.uniform(1.0, 4.0), 1)
        },
        'requerimientos': requirements,
        'recomendaciones': generar_recomendaciones(crop)
    }

def calculate_area_approximate(geojson):
    """Calcular área aproximada sin shapely"""
    import random
    # En una implementación real, aquí calcularías el área basado en las coordenadas
    # Por ahora retornamos un valor aleatorio razonable
    return round(random.uniform(5, 50), 2)

def generar_recomendaciones(crop):
    """Generar recomendaciones basadas en el cultivo"""
    recomendaciones = {
        'trigo': [
            "Aplicar fertilizante nitrogenado en pre-siembra",
            "Mantener pH alrededor de 6.0",
            "Controlar niveles de fósforo"
        ],
        'maiz': [
            "Alta demanda de nitrógeno - fertilizar adecuadamente",
            "Asegurar buen drenaje del suelo",
            "Mantener niveles altos de potasio"
        ],
        'soja': [
            "Inocular con rhizobium para fijación de nitrógeno",
            "Mantener niveles adecuados de fósforo",
            "Controlar pH para optimizar nodulación"
        ],
        'sorgo': [
            "Moderada demanda de nutrientes",
            "Tolerante a suelos más secos",
            "Mantener niveles de potasio"
        ],
        'girasol': [
            "Baja demanda de nitrógeno",
            "Sensible a excesos de agua",
            "Mantener pH neutro"
        ]
    }
    return recomendaciones.get(crop, [])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
