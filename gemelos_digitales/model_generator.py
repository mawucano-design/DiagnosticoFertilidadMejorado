import numpy as np
import open3d as o3d
from scipy.spatial import ConvexHull, Delaunay
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pandas as pd

class DigitalTwinGenerator:
    def __init__(self):
        self.plant_models = {}
        self.health_model = None
        
    def train_health_model(self, X, y):
        """Entrena modelo de salud de plantas (placeholder para datos reales)"""
        try:
            self.health_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.health_model.fit(X, y)
            return True
        except Exception as e:
            st.warning(f"Modelo de salud no entrenado: {e}")
            return False

def extract_plant_metrics(vegetation_cloud):
    """Extrae métricas clave de la vegetación a partir de la nube de puntos"""
    if vegetation_cloud is None:
        return {}
        
    try:
        points = np.asarray(vegetation_cloud.points)
        
        if len(points) < 10:
            return {
                'plant_height': 0,
                'canopy_volume': 0,
                'plant_density': 0,
                'canopy_area': 0,
                'health_score': 0,
                'growth_stage': 'Insuficientes datos',
                'canopy_roughness': 0
            }
        
        # Métricas básicas
        min_z = np.min(points[:, 2])
        max_z = np.max(points[:, 2])
        plant_height = max_z - min_z
        
        # Densidad de puntos
        plant_density = len(points)
        
        # Volumen y área del dosel
        canopy_volume = calculate_canopy_volume(points)
        canopy_area = calculate_canopy_area(points)
        
        # Rugosidad del dosel (desviación estándar de alturas)
        canopy_roughness = np.std(points[:, 2])
        
        # Puntaje de salud (heurístico basado en métricas)
        health_score = calculate_health_score(plant_height, canopy_volume, plant_density, canopy_roughness)
        
        # Etapa de crecimiento estimada
        growth_stage = estimate_growth_stage(plant_height, canopy_volume)
        
        return {
            'plant_height': float(plant_height),
            'canopy_volume': float(canopy_volume),
            'plant_density': int(plant_density),
            'canopy_area': float(canopy_area),
            'health_score': float(health_score),
            'growth_stage': growth_stage,
            'canopy_roughness': float(canopy_roughness),
            'max_height': float(max_z),
            'min_height': float(min_z),
            'mean_height': float(np.mean(points[:, 2]))
        }
        
    except Exception as e:
        st.error(f"Error calculando métricas: {e}")
        return {}

def calculate_canopy_volume(points):
    """Calcula volumen del dosel usando convex hull 3D"""
    try:
        if len(points) < 4:
            return 0.0
            
        # Usar convex hull para volumen 3D
        hull = ConvexHull(points)
        return hull.volume
    except:
        # Fallback: volumen aproximado usando bounding box
        if len(points) > 0:
            x_range = np.max(points[:, 0]) - np.min(points[:, 0])
            y_range = np.max(points[:, 1]) - np.min(points[:, 1])
            z_range = np.max(points[:, 2]) - np.min(points[:, 2])
            return x_range * y_range * z_range * 0.5  # Factor de corrección
        return 0.0

def calculate_canopy_area(points):
    """Calcula área de proyección del dosel"""
    try:
        if len(points) < 3:
            return 0.0
            
        # Proyección en plano XY
        xy_points = points[:, :2]
        hull_2d = ConvexHull(xy_points)
        return hull_2d.volume  # En 2D, volume es el área
    except:
        # Fallback: área de bounding box
        if len(points) > 0:
            x_range = np.max(points[:, 0]) - np.min(points[:, 0])
            y_range = np.max(points[:, 1]) - np.min(points[:, 1])
            return x_range * y_range
        return 0.0

def calculate_health_score(height, volume, density, roughness):
    """Calcula puntaje de salud heurístico"""
    try:
        # Factores normalizados (valores típicos para cultivos)
        height_score = min(height / 3.0, 1.0) * 0.3  # Máximo 3m = 100%
        volume_score = min(volume / 50.0, 1.0) * 0.3  # Máximo 50m³ = 100%
        density_score = min(density / 10000.0, 1.0) * 0.3  # Máximo 10,000 puntos = 100%
        
        # Rugosidad (menos rugosidad = mejor)
        roughness_score = max(0, 1 - (roughness / 0.5)) * 0.1  # Máximo 0.5m rugosidad
        
        total_score = (height_score + volume_score + density_score + roughness_score) * 100
        return min(max(total_score, 0), 100)
    except:
        return 50.0  # Score por defecto

def estimate_growth_stage(height, volume):
    """Estima etapa de crecimiento basado en métricas"""
    if height < 0.5 or volume < 1.0:
        return "Plántula"
    elif height < 1.0 or volume < 5.0:
        return "Crecimiento Vegetativo"
    elif height < 2.0 or volume < 20.0:
        return "Floración"
    else:
        return "Maduración"

def create_digital_twin_model(metrics, plant_type="maize"):
    """Crea un modelo de gemelo digital basado en métricas"""
    model = {
        'type': plant_type,
        'metrics': metrics,
        'timestamp': pd.Timestamp.now().isoformat(),
        'recommendations': generate_recommendations(metrics)
    }
    return model

def generate_recommendations(metrics):
    """Genera recomendaciones basadas en las métricas"""
    health = metrics.get('health_score', 0)
    height = metrics.get('plant_height', 0)
    
    recommendations = []
    
    if health < 50:
        recommendations.append("🔴 Revisar nutrientes y condiciones de suelo")
    elif health < 70:
        recommendations.append("🟡 Monitorear crecimiento y considerar fertilización suplementaria")
    else:
        recommendations.append("🟢 Condiciones óptimas, mantener prácticas actuales")
    
    if height < 0.5:
        recommendations.append("🌱 Etapa temprana, asegurar riego adecuado")
    elif height > 2.5:
        recommendations.append("🌾 Etapa de maduración, preparar para cosecha")
    
    return recommendations
