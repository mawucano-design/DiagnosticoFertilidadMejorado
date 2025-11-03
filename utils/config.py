# Configuración de la aplicación

# Parámetros LiDAR
LIDAR_CONFIG = {
    'voxel_size_default': 0.05,
    'outlier_std_ratio': 2.0,
    'outlier_nb_neighbors': 20,
    'vegetation_height_threshold': 0.3,  # metros
    'max_file_size_mb': 100
}

# Parámetros de análisis de suelo
SOIL_CONFIG = {
    'optimal_ph_range': (6.0, 7.0),
    'optimal_organic_matter': (3.0, 5.0),
    'default_crop': 'Maíz'
}

# Configuración de visualización
VIZ_CONFIG = {
    'point_size': 2,
    'opacity': 0.8,
    'colorscale': 'Viridis',
    'plot_height': 600
}

# Configuración de la aplicación
APP_CONFIG = {
    'name': 'Plataforma Agrícola Integral',
    'version': '1.0.0',
    'description': 'Sistema integrado de diagnóstico de fertilidad y gemelos digitales'
}
