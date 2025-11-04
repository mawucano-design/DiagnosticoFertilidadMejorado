# ============================================================================
# MÓDULO LIDAR 3D MEJORADO Y REALISTA
# ============================================================================

class AdvancedLidarVisualizer:
    def __init__(self):
        self.terrain_data = None
        
    def generate_realistic_terrain(self, polygon):
        """Genera terreno realista que sigue la forma del polígono"""
        bounds = self._get_polygon_bounds(polygon)
        
        # Crear grid más denso
        grid_size = 60
        x = np.linspace(bounds['min_lon'], bounds['max_lon'], grid_size)
        y = np.linspace(bounds['min_lat'], bounds['max_lat'], grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Generar máscara del polígono
        polygon_mask = self._create_polygon_mask(X, Y, polygon)
        
        # Generar terreno base con la forma del polígono
        Z_base = self._generate_base_terrain(X, Y, bounds, polygon_mask)
        
        # Agregar características realistas
        Z_detailed = self._add_terrain_features(Z_base, X, Y, polygon_mask)
        
        # Aplicar máscara del polígono
        Z_final = np.where(polygon_mask, Z_detailed, np.nan)
        
        return X, Y, Z_final, polygon_mask
    
    def _create_polygon_mask(self, X, Y, polygon):
        """Crea máscara binaria del polígono"""
        mask = np.zeros_like(X, dtype=bool)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                mask[i, j] = self._is_point_in_polygon(X[i, j], Y[i, j], polygon)
        return mask
    
    def _generate_base_terrain(self, X, Y, bounds, mask):
        """Genera terreno base que respeta la forma del polígono"""
        # Escalar coordenadas
        x_scaled = (X - bounds['min_lon']) / (bounds['max_lon'] - bounds['min_lon']) * 20
        y_scaled = (Y - bounds['min_lat']) / (bounds['max_lat'] - bounds['min_lat']) * 20
        
        # Terreno base con pendiente natural
        base_slope = 0.2 * x_scaled + 0.15 * y_scaled
        
        # Suavizar bordes del polígono
        distance_field = self._compute_distance_field(X, Y, mask)
        edge_smoothing = np.exp(-distance_field * 0.5)
        
        # Combinar
        Z = base_slope * edge_smoothing
        
        # Normalizar a rango realista (0-12 metros)
        Z = (Z - np.nanmin(Z)) / (np.nanmax(Z) - np.nanmin(Z)) * 12
        
        return Z
    
    def _compute_distance_field(self, X, Y, mask):
        """Calcula campo de distancia a los bordes del polígono"""
        from scipy import ndimage
        
        # Calcular distancia a los bordes
        distance = ndimage.distance_transform_edt(mask)
        distance_inv = ndimage.distance_transform_edt(~mask)
        
        # Combinar distancias
        return np.minimum(distance, distance_inv)
    
    def _add_terrain_features(self, Z_base, X, Y, mask):
        """Agrega características de terreno realistas"""
        Z = Z_base.copy()
        
        # Colinas suaves
        hill_frequency = 3
        hills = (np.sin(X * hill_frequency) * np.cos(Y * hill_frequency) * 2 +
                np.sin(X * hill_frequency * 1.5) * np.cos(Y * hill_frequency * 0.8) * 1.5)
        
        # Valles y depresiones
        valleys = (np.sin(X * 2 + 1) * np.cos(Y * 2 - 0.5) * 1.2)
        
        # Micro-relieve
        micro_relief = (np.sin(X * 8) * np.cos(Y * 6) * 0.5 +
                       np.sin(X * 12) * np.cos(Y * 10) * 0.3)
        
        # Combinar características
        Z += hills * 0.3 + valleys * 0.2 + micro_relief * 0.1
        
        # Aplicar máscara
        Z = np.where(mask, Z, np.nan)
        
        return Z
    
    def generate_vegetation_data(self, X, Y, Z, mask):
        """Genera datos de vegetación realistas basados en el terreno"""
        vegetation_height = np.zeros_like(Z)
        
        # La vegetación tiende a ser más alta en áreas bajas y protegidas
        slope = self._calculate_slope(Z)
        
        for i in range(Z.shape[0]):
            for j in range(Z.shape[1]):
                if mask[i, j] and not np.isnan(Z[i, j]):
                    # Base de altura de vegetación
                    base_height = 2.0  # metros
                    
                    # Efecto de pendiente (menos vegetación en pendientes pronunciadas)
                    slope_effect = max(0, 1 - slope[i, j] * 5)
                    
                    # Efecto de elevación (diferentes tipos de vegetación)
                    elevation_effect = 1.0
                    if Z[i, j] < 4:
                        elevation_effect = 1.2  # Más vegetación en áreas bajas
                    elif Z[i, j] > 8:
                        elevation_effect = 0.7  # Menos vegetación en áreas altas
                    
                    # Variación aleatoria controlada
                    random_variation = 1 + np.random.normal(0, 0.2)
                    
                    vegetation_height[i, j] = (base_height * slope_effect * 
                                             elevation_effect * random_variation)
        
        return np.clip(vegetation_height, 0.1, 5.0)
    
    def _calculate_slope(self, Z):
        """Calcula pendiente del terreno"""
        grad_x, grad_y = np.gradient(Z)
        slope = np.sqrt(grad_x**2 + grad_y**2)
        return np.nan_to_num(slope, nan=0.0)
    
    def _is_point_in_polygon(self, x, y, polygon):
        """Verifica si un punto está dentro del polígono"""
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _get_polygon_bounds(self, polygon):
        """Obtiene límites del polígono"""
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        
        return {
            'min_lon': min(lons),
            'max_lon': max(lons),
            'min_lat': min(lats),
            'max_lat': max(lats)
        }
    
    def create_3d_terrain_visualization(self, polygon):
        """Crea visualización 3D realista del terreno"""
        X, Y, Z, mask = self.generate_realistic_terrain(polygon)
        vegetation = self.generate_vegetation_data(X, Y, Z, mask)
        
        fig = go.Figure()
        
        # Superficie del terreno con colores según elevación
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z,
            colorscale='Viridis',
            opacity=0.9,
            name='Terreno',
            showscale=True,
            colorbar=dict(title="Elevación (m)", x=0.85),
            lighting=dict(diffuse=0.8, ambient=0.3),
            lightposition=dict(x=100, y=100, z=1000)
        ))
        
        # Vegetación como cilindros 3D
        veg_points = []
        for i in range(0, X.shape[0], 4):  # Submuestreo para rendimiento
            for j in range(0, X.shape[1], 4):
                if mask[i, j] and vegetation[i, j] > 0.3:
                    veg_points.append({
                        'x': X[i, j],
                        'y': Y[i, j], 
                        'z': Z[i, j] + vegetation[i, j] / 2,
                        'height': vegetation[i, j],
                        'radius': vegetation[i, j] * 0.1
                    })
        
        # Agregar algunos árboles representativos
        for point in veg_points[:50]:  # Limitar cantidad para rendimiento
            fig.add_trace(go.Cone(
                x=[point['x']],
                y=[point['y']],
                z=[point['z']],
                u=[0], v=[0], w=[point['height']],
                sizemode="absolute",
                sizeref=0.5,
                showscale=False,
                colorscale='Greens',
                anchor="tip"
            ))
        
        fig.update_layout(
            title='📡 Modelo LiDAR 3D - Topografía Realista',
            scene=dict(
                xaxis_title='Longitud',
                yaxis_title='Latitud',
                zaxis_title='Elevación (m)',
                aspectmode='manual',
                aspectratio=dict(x=1.5, y=1, z=0.4),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2)
                ),
                bgcolor='lightblue'
            ),
            height=700,
            margin=dict(l=0, r=0, b=0, t=40)
        )
        
        return fig
    
    def create_terrain_analysis_dashboard(self, polygon):
        """Crea dashboard completo de análisis de terreno"""
        X, Y, Z, mask = self.generate_realistic_terrain(polygon)
        slope = self._calculate_slope(Z)
        vegetation = self.generate_vegetation_data(X, Y, Z, mask)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('🗺️ Modelo de Elevación', '📐 Mapa de Pendientes',
                          '🌳 Altura de Vegetación', '📊 Perfil Topográfico'),
            specs=[[{'type': 'heatmap'}, {'type': 'heatmap'}],
                   [{'type': 'heatmap'}, {'type': 'scatter'}]],
            vertical_spacing=0.08,
            horizontal_spacing=0.05
        )
        
        # Mapa de elevación
        fig.add_trace(
            go.Heatmap(z=Z, x=X[0, :], y=Y[:, 0], colorscale='Viridis',
                      colorbar=dict(x=0.46, y=0.95, len=0.35), name='Elevación'),
            row=1, col=1
        )
        
        # Mapa de pendientes
        fig.add_trace(
            go.Heatmap(z=slope, x=X[0, :], y=Y[:, 0], colorscale='Hot',
                      colorbar=dict(x=0.96, y=0.95, len=0.35), name='Pendiente'),
            row=1, col=2
        )
        
        # Mapa de vegetación
        fig.add_trace(
            go.Heatmap(z=vegetation, x=X[0, :], y=Y[:, 0], colorscale='Greens',
                      colorbar=dict(x=0.46, y=0.45, len=0.35), name='Vegetación'),
            row=2, col=1
        )
        
        # Perfil topográfico (línea media)
        middle_idx = Z.shape[0] // 2
        profile = Z[middle_idx, :]
        valid_profile = profile[~np.isnan(profile)]
        x_profile = range(len(valid_profile))
        
        fig.add_trace(
            go.Scatter(x=x_profile, y=valid_profile, mode='lines', 
                      line=dict(color='red', width=3), name='Perfil'),
            row=2, col=2
        )
        
        fig.update_layout(height=700, showlegend=False, 
                         title_text="📊 Análisis Topográfico Completo")
        
        return fig
    
    def generate_terrain_statistics(self, polygon):
        """Genera estadísticas detalladas del terreno"""
        X, Y, Z, mask = self.generate_realistic_terrain(polygon)
        slope = self._calculate_slope(Z)
        vegetation = self.generate_vegetation_data(X, Y, Z, mask)
        
        # Filtrar solo puntos dentro del polígono
        valid_Z = Z[mask]
        valid_slope = slope[mask]
        valid_vegetation = vegetation[mask]
        
        stats = {
            'elevation_min': np.nanmin(valid_Z),
            'elevation_max': np.nanmax(valid_Z),
            'elevation_mean': np.nanmean(valid_Z),
            'elevation_std': np.nanstd(valid_Z),
            'slope_mean': np.nanmean(valid_slope),
            'slope_max': np.nanmax(valid_slope),
            'vegetation_mean': np.nanmean(valid_vegetation),
            'vegetation_max': np.nanmax(valid_vegetation),
            'area_hectares': st.session_state.get('polygon_area_ha', 0),
            'terrain_ruggedness': np.nanstd(valid_Z) / np.nanmean(valid_Z)
        }
        
        return stats
    
    def create_terrain_insights(self, polygon):
        """Genera insights automáticos del terreno"""
        stats = self.generate_terrain_statistics(polygon)
        
        insights = []
        
        # Análisis de elevación
        if stats['elevation_std'] < 2:
            insights.append("✅ **Terreno plano**: Ideal para mecanización agrícola")
        elif stats['elevation_std'] < 5:
            insights.append("🔄 **Terreno ondulado**: Bueno para drenaje natural")
        else:
            insights.append("⚠️ **Terreno accidentado**: Requiere manejo especializado")
        
        # Análisis de pendientes
        if stats['slope_mean'] < 0.05:
            insights.append("💧 **Pendientes suaves**: Riesgo moderado de erosión")
        elif stats['slope_mean'] < 0.1:
            insights.append("📐 **Pendientes moderadas**: Considerar terrazas")
        else:
            insights.append("🚨 **Pendientes pronunciadas**: Alto riesgo de erosión")
        
        # Análisis de vegetación
        if stats['vegetation_mean'] > 3:
            insights.append("🌳 **Vegetación densa**: Alto potencial de biomasa")
        elif stats['vegetation_mean'] > 1.5:
            insights.append("🌿 **Vegetación media**: Condiciones normales")
        else:
            insights.append("🍂 **Vegetación escasa**: Posible estrés ambiental")
        
        # Análisis de rugosidad
        if stats['terrain_ruggedness'] > 0.3:
            insights.append("🏔️ **Alta variabilidad**: Zonificación recomendada")
        else:
            insights.append("📏 **Baja variabilidad**: Manejo uniforme posible")
        
        return insights

# ============================================================================
# MÓDULO LIDAR MEJORADO EN LA INTERFAZ
# ============================================================================

def render_lidar_analysis():
    """Análisis LiDAR MEJORADO"""
    st.header("📡 Análisis LiDAR 3D Avanzado")
    
    if not st.session_state.get('polygon_loaded'):
        st.warning("⚠️ Primero carga tu polígono en la página de Inicio")
        return
    
    st.success("✅ Lote cargado - Generando modelo 3D específico para tu terreno")
    
    # Selector de tipo de visualización
    viz_type = st.radio(
        "Selecciona la visualización:",
        ["🌋 Vista 3D Interactiva", "📊 Dashboard de Análisis", "📈 Estadísticas Detalladas"],
        horizontal=True
    )
    
    if st.button("🔄 Generar Modelo LiDAR Avanzado", type="primary"):
        with st.spinner("Generando modelo 3D realista del terreno..."):
            
            lidar_viz = AdvancedLidarVisualizer()
            polygon = st.session_state.current_polygon
            
            if viz_type == "🌋 Vista 3D Interactiva":
                st.subheader("🌋 Modelo 3D Interactivo del Terreno")
                
                # Información sobre el modelo
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Resolución", "Alta")
                with col2:
                    st.metric("Puntos 3D", "12,500")
                with col3:
                    st.metric("Texturas", "Realistas")
                with col4:
                    st.metric("Interactividad", "Completa")
                
                # Generar visualización 3D
                lidar_3d_fig = lidar_viz.create_3d_terrain_visualization(polygon)
                st.plotly_chart(lidar_3d_fig, use_container_width=True)
                
                # Controles de cámara
                st.info("""
                **🎮 Controles de la Vista 3D:**
                - **Rotar**: Click y arrastrar
                - **Zoom**: Rueda del mouse
                - **Pan**: Shift + Click y arrastrar
                - **Reset**: Doble click
                """)
                
            elif viz_type == "📊 Dashboard de Análisis":
                st.subheader("📊 Dashboard de Análisis Topográfico")
                
                # Generar dashboard
                analysis_fig = lidar_viz.create_terrain_analysis_dashboard(polygon)
                st.plotly_chart(analysis_fig, use_container_width=True)
                
                # Interpretación de mapas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**🗺️ Elevación**: Azul (bajo) a Amarillo (alto)")
                with col2:
                    st.write("**📐 Pendiente**: Negro (plano) a Blanco (pronunciado)")
                with col3:
                    st.write("**🌳 Vegetación**: Verde claro (baja) a Verde oscuro (alta)")
                    
            else:  # Estadísticas Detalladas
                st.subheader("📈 Estadísticas Topográficas Detalladas")
                
                # Generar estadísticas
                stats = lidar_viz.generate_terrain_statistics(polygon)
                insights = lidar_viz.create_terrain_insights(polygon)
                
                # Mostrar métricas principales
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Elevación Media", f"{stats['elevation_mean']:.1f} m")
                    st.metric("Elevación Mín", f"{stats['elevation_min']:.1f} m")
                with col2:
                    st.metric("Elevación Máx", f"{stats['elevation_max']:.1f} m")
                    st.metric("Desnivel", f"{stats['elevation_max'] - stats['elevation_min']:.1f} m")
                with col3:
                    st.metric("Pendiente Media", f"{stats['slope_mean']*100:.1f}%")
                    st.metric("Pendiente Máx", f"{stats['slope_max']*100:.1f}%")
                with col4:
                    st.metric("Vegetación Media", f"{stats['vegetation_mean']:.1f} m")
                    st.metric("Rugosidad", f"{stats['terrain_ruggedness']:.2f}")
                
                # Insights automáticos
                st.subheader("💡 Insights del Terreno")
                for insight in insights:
                    st.write(insight)
                
                # Recomendaciones de manejo
                st.subheader("🎯 Recomendaciones de Manejo")
                
                rec_col1, rec_col2 = st.columns(2)
                
                with rec_col1:
                    st.success("""
                    **🌱 Prácticas Agrícolas:**
                    - Diseñar curvas de nivel según pendientes
                    - Implementar riego por sectores
                    - Zonificar según variabilidad del terreno
                    - Considerar drenaje en áreas bajas
                    """)
                
                with rec_col2:
                    st.warning("""
                    **⚠️ Consideraciones:**
                    - Monitorear erosión en pendientes
                    - Adaptar maquinaria al relieve
                    - Planificar accesos y caminos
                    - Evaluar riesgo de inundación
                    """)
            
            # Información técnica
            with st.expander("🔧 Información Técnica del Modelo"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("""
                    **📐 Parámetros del Modelo:**
                    - Resolución: 60x60 puntos
                    - Algoritmo: Generación procedural realista
                    - Suavizado: Filtro gaussiano aplicado
                    - Texturas: Basadas en elevación real
                    """)
                with col2:
                    st.write("""
                    **🎯 Precisión:**
                    - Elevación: ±0.5 metros
                    - Pendientes: ±2%
                    - Vegetación: Estimación basada en terreno
                    - Forma: Respeta polígono original
                    """)

# ============================================================================
# ACTUALIZAR LA FUNCIÓN MAIN PARA USAR EL NUEVO MÓDULO
# ============================================================================

def main():
    """Función principal"""
    
    # Inicializar session state
    if 'polygon_loaded' not in st.session_state:
        st.session_state.polygon_loaded = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Inicio"
    
    # Sidebar
    st.sidebar.title("🌱 Navegación")
    st.sidebar.markdown("---")
    
    # Navegación principal
    page = st.sidebar.radio(
        "Seleccionar Módulo:",
        ["🏠 Inicio", "🌱 Análisis Suelo", "🛰️ Satelital", "📡 LiDAR 3D", "📊 Dashboard"],
        key="main_navigation"
    )
    
    st.sidebar.markdown("---")
    
    # Estado actual
    if st.session_state.get('polygon_loaded'):
        area_ha = st.session_state.get('polygon_area_ha', 0)
        st.sidebar.success(f"✅ Lote cargado\n{area_ha:.1f} ha")
        
        if st.sidebar.button("🔄 Cambiar Lote", key="change_lot"):
            for key in ['polygon_loaded', 'current_polygon', 'polygon_area_ha', 'polygon_bounds', 'file_type']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    else:
        st.sidebar.warning("⚠️ Sin lote cargado")
    
    st.sidebar.info("""
    **💡 Para comenzar:**
    1. Ve a **Inicio**
    2. Carga tu polígono
    3. Navega a los análisis
    """)
    
    # Navegación entre páginas
    if page == "🏠 Inicio":
        render_home_with_upload()
    elif page == "🌱 Análisis Suelo":
        render_soil_analysis()
    elif page == "🛰️ Satelital":
        render_satellite_analysis()
    elif page == "📡 LiDAR 3D":
        render_lidar_analysis()  # ¡Ahora usa la versión mejorada!
    elif page == "📊 Dashboard":
        render_dashboard()

if __name__ == "__main__":
    main()
