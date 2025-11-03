import laspy
import numpy as np
import open3d as o3d
import streamlit as st
from scipy import spatial
from sklearn.cluster import DBSCAN
import tempfile
import os

class LiDARProcessor:
    def __init__(self):
        self.point_cloud = None
        self.vegetation_cloud = None
        
    def load_lidar(self, file_path):
        """Carga y procesa archivos LiDAR LAS/LAZ"""
        try:
            # Leer archivo LAS
            las = laspy.read(file_path)
            
            # Extraer coordenadas
            x = las.x
            y = las.y
            z = las.z
            
            # Crear array de puntos
            points = np.vstack((x, y, z)).transpose()
            
            # Crear nube de puntos Open3D
            self.point_cloud = o3d.geometry.PointCloud()
            self.point_cloud.points = o3d.utility.Vector3dVector(points)
            
            # Extraer intensidad si está disponible
            if hasattr(las, 'intensity'):
                intensity = np.array(las.intensity)
                # Normalizar intensidad para visualización
                if len(intensity) > 0:
                    intensity_normalized = (intensity - np.min(intensity)) / (np.max(intensity) - np.min(intensity))
                    colors = np.zeros((points.shape[0], 3))
                    colors[:, 0] = intensity_normalized  # Rojo basado en intensidad
                    self.point_cloud.colors = o3d.utility.Vector3dVector(colors)
            
            st.success(f"✅ LiDAR cargado: {len(points):,} puntos")
            return self.point_cloud
            
        except Exception as e:
            st.error(f"❌ Error cargando LiDAR: {str(e)}")
            return None
    
    def apply_advanced_processing(self, point_cloud, remove_outliers=True, voxel_size=0.05):
        """Aplica procesamiento avanzado a la nube de puntos"""
        try:
            processed_cloud = point_cloud
            
            # 1. Downsampling con voxel grid
            if voxel_size > 0:
                processed_cloud = processed_cloud.voxel_down_sample(voxel_size=voxel_size)
                st.info(f"Downsampling aplicado: {len(processed_cloud.points):,} puntos después de voxel grid")
            
            # 2. Remover outliers estadísticos
            if remove_outliers and len(processed_cloud.points) > 100:
                cl, ind = processed_cloud.remove_statistical_outlier(
                    nb_neighbors=50, 
                    std_ratio=1.5
                )
                processed_cloud = processed_cloud.select_by_index(ind)
                st.info(f"Outliers removidos: {len(processed_cloud.points):,} puntos restantes")
            
            # 3. Estimación de normales
            if len(processed_cloud.points) > 100:
                processed_cloud.estimate_normals(
                    search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
                )
            
            return processed_cloud
            
        except Exception as e:
            st.error(f"Error en procesamiento: {str(e)}")
            return point_cloud
    
    def segment_vegetation(self):
        """Segmenta vegetación del terreno usando múltiples métodos"""
        if self.point_cloud is None:
            st.error("No hay nube de puntos cargada")
            return None
            
        try:
            points = np.asarray(self.point_cloud.points)
            
            if len(points) < 100:
                st.warning("Muy pocos puntos para segmentación")
                return None
            
            # Método 1: Segmentación por altura (Simple)
            ground_height = np.percentile(points[:, 2], 2)  # Usar percentil 2 para terreno
            vegetation_mask = points[:, 2] > ground_height + 0.3  # 30 cm sobre terreno
            
            # Método 2: Clusterización para separar objetos
            if np.sum(vegetation_mask) > 50:
                vegetation_points = points[vegetation_mask]
                
                # Aplicar DBSCAN para separar clusters de vegetación
                clustering = DBSCAN(eps=0.5, min_samples=10).fit(vegetation_points)
                labels = clustering.labels_
                
                # Mantener solo el cluster más grande (asumiendo que es la vegetación principal)
                if len(np.unique(labels)) > 1:
                    unique, counts = np.unique(labels[labels >= 0], return_counts=True)
                    if len(unique) > 0:
                        main_cluster = unique[np.argmax(counts)]
                        vegetation_mask_refined = labels == main_cluster
                        vegetation_points = vegetation_points[vegetation_mask_refined]
            
            # Crear nube de puntos de vegetación
            self.vegetation_cloud = o3d.geometry.PointCloud()
            self.vegetation_cloud.points = o3d.utility.Vector3dVector(vegetation_points)
            
            # Copiar colores si existen
            if self.point_cloud.has_colors():
                colors = np.asarray(self.point_cloud.colors)
                vegetation_colors = colors[vegetation_mask]
                if len(vegetation_colors) == len(vegetation_points):
                    self.vegetation_cloud.colors = o3d.utility.Vector3dVector(vegetation_colors)
            
            st.success(f"✅ Vegetación segmentada: {len(vegetation_points):,} puntos")
            return self.vegetation_cloud
            
        except Exception as e:
            st.error(f"❌ Error en segmentación: {str(e)}")
            return None
    
    def calculate_ground_profile(self):
        """Calcula el perfil del terreno"""
        if self.point_cloud is None:
            return None
            
        points = np.asarray(self.point_cloud.points)
        ground_height = np.percentile(points[:, 2], 5)
        
        return {
            'min_elevation': np.min(points[:, 2]),
            'max_elevation': np.max(points[:, 2]),
            'mean_elevation': np.mean(points[:, 2]),
            'ground_height': ground_height,
            'roughness': np.std(points[:, 2])
        }
