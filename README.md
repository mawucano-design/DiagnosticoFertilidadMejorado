# 🌱 Analizador Multi-Cultivo 

> 🌴🍫🍌☕ Sistema de análisis satelital y geoespacial para **trigo, maiz, soja y girasol**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url)

Este sistema permite a técnicos agrícolas, ingenieros y productores realizar un **diagnóstico integral de sus parcelas** utilizando **imágenes satelitales** (Sentinel-2, Landsat-8) y **análisis geoespacial avanzado**.

---

## 🚀 Funcionalidades

### 🌿 Análisis de Fertilidad y Nutrición
- Evaluación del estado actual de **Nitrógeno (N), Fósforo (P) y Potasio (K)** mediante índices satelitales
- Recomendaciones de fertilización **específicas por cultivo y zona de manejo**

### 🏗️ Análisis de Textura del Suelo
- Clasificación geoespacial de la textura (arena, limo, arcilla)
- Recomendaciones de manejo según tipo de suelo

### 🗻 Análisis Topográfico (Curvas de Nivel)
- Generación de **mapas de calor de pendientes**
- Evaluación de **riesgo de erosión** en función de la pendiente
- Visualización 3D del terreno

### 📊 Exportación de Resultados
- **PDF y DOCX**: Reportes técnicos detallados con mapas, estadísticas y recomendaciones
- **GeoJSON**: Exportación de zonas de manejo para SIG
- **CSV**: Datos tabulados para análisis adicional

---

## 🌍 Cultivos Soportados

| Cultivo | Icono | Características |
|--------|-------|-----------------|
| **Palma aceitera** | 🌴 | Alto requerimiento de K, sensible a encharcamientos |
| **Cacao** | 🍫 | Requiere sombra y alta materia orgánica, sistema radicular superficial |
| **Banano** | 🍌 | Alta demanda de N y K, sensible a anegamiento |
| **Café** | ☕ | Cultivo de montaña, requiere pendientes manejables y pH ácido |

---

## 📥 Formatos de Entrada

- **Shapefile** (`.zip`): Archivo comprimido con `.shp`, `.shx`, `.dbf`
- **KML** (`.kml`): Formato de Google Earth
- **KMZ** (`.kmz`): Versión comprimida de KML

> **Recomendación**: Usar coordenadas **EPSG:4326 (WGS84)** para mejores resultados

---

## 🛠️ Requisitos

```bash
pip install streamlit geopandas pandas numpy matplotlib fpdf python-docx geojson
