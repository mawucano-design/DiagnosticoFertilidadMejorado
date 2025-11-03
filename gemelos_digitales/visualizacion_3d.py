import plotly.graph_objects as go
import numpy as np
import streamlit as st
from plotly.subplots import make_subplots

def create_interactive_plot(point_cloud, title="Visualización 3D - Nube de Puntos"):
    """Crea visualización 3D interactiva de la nube de puntos"""
    try:
        points = np.asarray(point_cloud.points)
        
        if len(points) == 0:
            st.warning("No hay puntos para visualizar")
            return
            
        # Determinar colores
        if point_cloud.has_colors():
            colors = np.asarray(point_cloud.colors)
            marker_color = [f'rgb({int(r*255)},{int(g*255)},{int(b*255)})' for r, g, b in colors]
        else:
            # Color por altura
            z = points[:, 2]
            z_normalized = (z - np.min(z)) / (np.max(z) - np.min(z))
            marker_color = z_normalized
        
        # Crear figura 3D
        fig = go.Figure(data=[go.Scatter3d(
            x=points[:, 0],
            y=points[:, 1],
            z=points[:, 2],
            mode='markers',
            marker=dict(
                size=2,
                color=marker_color,
                opacity=0.8,
                colorscale='Viridis' if not point_cloud.has_colors() else None,
                colorbar=dict(title='Altura (m)') if not point_cloud.has_colors() else None
            ),
            name='Puntos LiDAR',
            hovertemplate=
            '<b>X:</b> %{x:.2f}m<br>' +
            '<b>Y:</b> %{y:.2f}m<br>' +
            '<b>Z:</b> %{z:.2f}m<br>' +
            '<extra></extra>'
        )])
        
        # Actualizar layout
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor='center'
            ),
            scene=dict(
                xaxis_title='X (m)',
                yaxis_title='Y (m)',
                zaxis_title='Altura (m)',
                aspectmode='data',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            height=600,
            margin=dict(l=0, r=0, b=0, t=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar estadísticas
        show_point_cloud_stats(points)
        
    except Exception as e:
        st.error(f"Error creando visualización: {e}")

def create_comparison_plot(cloud1, cloud2, title1="Antes", title2="Después"):
    """Crea visualización comparativa de dos nubes de puntos"""
    try:
        points1 = np.asarray(cloud1.points)
        points2 = np.asarray(cloud2.points)
        
        if len(points1) == 0 or len(points2) == 0:
            st.warning("No hay suficientes puntos para comparación")
            return
            
        # Crear subplots
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{'type': 'scatter3d'}, {'type': 'scatter3d'}]],
            subplot_titles=[title1, title2]
        )
        
        # Nube 1
        fig.add_trace(
            go.Scatter3d(
                x=points1[:, 0], y=points1[:, 1], z=points1[:, 2],
                mode='markers',
                marker=dict(size=2, color='blue', opacity=0.6),
                name=title1
            ),
            row=1, col=1
        )
        
        # Nube 2
        fig.add_trace(
            go.Scatter3d(
                x=points2[:, 0], y=points2[:, 1], z=points2[:, 2],
                mode='markers',
                marker=dict(size=2, color='red', opacity=0.6),
                name=title2
            ),
            row=1, col=2
        )
        
        # Actualizar layouts
        camera = dict(eye=dict(x=1.5, y=1.5, z=1.5))
        
        fig.update_layout(
            height=500,
            title_text="Comparación de Nubes de Puntos"
        )
        
        fig.update_scenes(
            aspectmode='data',
            camera=camera,
            row=1, col=1
        )
        
        fig.update_scenes(
            aspectmode='data',
            camera=camera,
            row=1, col=2
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creando comparación: {e}")

def show_point_cloud_stats(points):
    """Muestra estadísticas de la nube de puntos"""
    if len(points) == 0:
        return
        
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Puntos", f"{len(points):,}")
    
    with col2:
        st.metric("Altura Máx", f"{np.max(points[:, 2]):.2f} m")
    
    with col3:
        st.metric("Altura Mín", f"{np.min(points[:, 2]):.2f} m")
    
    with col4:
        st.metric("Altura Prom", f"{np.mean(points[:, 2]):.2f} m")
    
    # Área cubierta
    x_range = np.max(points[:, 0]) - np.min(points[:, 0])
    y_range = np.max(points[:, 1]) - np.min(points[:, 1])
    
    st.info(f"**Área cubierta:** {x_range:.1f} × {y_range:.1f} m = {x_range * y_range:.1f} m²")

def create_height_profile_plot(point_cloud):
    """Crea perfil de alturas 2D"""
    try:
        points = np.asarray(point_cloud.points)
        
        if len(points) == 0:
            return
            
        # Crear histograma de alturas
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=points[:, 2],
            nbinsx=50,
            name='Distribución de Alturas',
            marker_color='lightblue',
            opacity=0.7
        ))
        
        fig.update_layout(
            title="Distribución de Alturas",
            xaxis_title="Altura (m)",
            yaxis_title="Número de Puntos",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creando perfil de alturas: {e}")
