# ------------------ Configuración y imports ------------------
from datetime import date, timedelta
import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, Draw
from streamlit_folium import st_folium
from shapely.geometry import Point, shape
from shapely.ops import unary_union

#Importamos utilidades nativas
import ceiba_client as cbc
import utilidades as util
import procesed as pcd
import graphics as graph
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
# import graphics as graph  # si lo necesitas después

st.set_page_config(
    page_title='Insitra Analytics: Unidades',
    page_icon='Recursos_visuales/insitra_logo.png',
    layout='wide',
)

# ------------------ Autenticación y sidebar ------------------
cbc.login()
cbc.require_login()

# 2) Sidebar de grupos (con prefijo propio para no chocar con otras páginas)
gid, gname, terids_del_grupo, err_sidebar = util.sidebar_grupos(key_prefix="uni")
if err_sidebar:
    st.warning(err_sidebar)
    st.stop()

# 1) Sidebar de navegación (tu menú)
util.navegacion()

# ------------------ Vista principal ------------------
st.title('INSITRA ANALYTICS: Ruta 🚦')
st.header('Mapa de calor')

# ---------- Rango de fechas ----------
date_presetk = date.today()

c1, c2 = st.columns(2)
with c1:
    iniciop = st.date_input('Inicio', date_presetk, key='uni_inicio_p')
with c2:
    finalp = st.date_input('Final', key='uni_final_p')

if iniciop > finalp:
    st.error('La fecha final debe ser más reciente que la fecha de inicio')
    st.stop()

rango_fechas = (iniciop,finalp)


# ---------- Llamada a la API ----------
conteo_pasajeros = {
    "terid": terids_del_grupo,
    "starttime": f"{iniciop} 00:00:00",
    "endtime": f"{finalp} 23:59:59",
}

ok, payload, err = cbc.api_post("basic/passenger-count/detail", json=conteo_pasajeros)
if not ok:
    st.error(err or "Error consultando CEIBA")
    st.stop()

# ---------- Procesamiento y vista ----------
conteo = pd.DataFrame(payload.get('data') or [])
if conteo.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

#Ajuste y normalización de datos

conteo = conteo.rename(columns={
    'lat': 'lat', 
    'lng': 'lon',
    'on':'on',
})

# ---- KPIs ARRIBA (placeholders) ----
st.subheader("Resultados en la zona dibujada")
kpi = st.container()
with kpi:
    c1, c2, c3 = st.columns(3)
    m_on  = c1.empty()  # placeholder métrica Ascensos
    m_off = c2.empty()  # placeholder métrica Descensos
    m_pts = c3.empty()  # placeholder métrica Puntos

# Valores iniciales (mientras no haya polígono dibujado)
#Modificamos el tamaño de letra
st.markdown("""
    <style>
    [data-testid = "stMetricLabel"] p{
            font-size: 1.5rem;
            }
            <style>
             """,unsafe_allow_html=True)

m_on.metric("Ascensos", "—", border=True)
m_off.metric("Descensos", "—", border=True)
m_pts.metric("Eventos dentro del área", "—", border=True)

# ----------------- TU PROCESAMIENTO -----------------
# Asegura nombres y tipos
conteo = pd.DataFrame(payload.get("data") or [])
conteo = conteo.rename(columns={"lng": "lon"})  # por si viene 'lng'
conteo["lat"] = pd.to_numeric(conteo["lat"], errors="coerce")
conteo["lon"] = pd.to_numeric(conteo["lon"], errors="coerce")
conteo["on"]  = pd.to_numeric(conteo.get("on"),  errors="coerce").fillna(0)
conteo["off"] = pd.to_numeric(conteo.get("off"), errors="coerce").fillna(0)
conteo = conteo.dropna(subset=["lat","lon"])

if conteo.empty:
    st.warning("No hay coordenadas válidas para el mapa.")
    st.stop()

# Mapa base
centro = [float(conteo["lat"].mean()), float(conteo["lon"].mean())]
m = folium.Map(location=centro, zoom_start=12, tiles="OpenStreetMap", control_scale=True)

# Heatmap
heat_data = conteo[["lat","lon"]].assign(peso=conteo["on"]).values.tolist()
HeatMap(heat_data, radius=25, blur=18, max_zoom=12).add_to(m)

# Herramienta de dibujo
Draw(
    export=False,
    position="topleft",
    draw_options={
        "polyline": False,
        "polygon": True,
        "rectangle": True,
        "circle": False,
        "circlemarker": False,
        "marker": False,
    },
    edit_options={"edit": True, "remove": True},
).add_to(m)

# Render y captura
state = st_folium(
    m,
    height=600,
    key="mapa_ruta_draw",
    returned_objects=["all_drawings", "last_active_drawing"],
    width=None
)

# ---- Procesar polígonos dibujados ----
features = []
if state is not None:
    drawings = state.get("all_drawings")
    last_one = state.get("last_active_drawing")

    if drawings:
        if isinstance(drawings, dict) and "features" in drawings:  # FeatureCollection
            features = drawings["features"]
        elif isinstance(drawings, list):                           # lista de features
            features = drawings

    if not features and isinstance(last_one, dict):
        features = [last_one]

if not features:
    st.info("Dibuja un polígono o rectángulo en el mapa para ver los totales dentro de la zona.")
    st.stop()

# Geometrías shapely
geoms = []
for feat in features:
    try:
        geom = shape(feat["geometry"])   # GeoJSON es [lon, lat]
        geoms.append(geom)
    except Exception:
        continue

if not geoms:
    st.warning("No se pudo interpretar la geometría dibujada.")
    st.stop()

zona = unary_union(geoms)

# Métricas en la zona (incluye borde si prefieres .covers)
pts  = [Point(xy) for xy in zip(conteo["lon"].to_numpy(), conteo["lat"].to_numpy())]
mask = [zona.contains(p) for p in pts]  # o zona.covers(p) para incluir borde
en_zona = conteo.loc[mask]

total_on  = int(en_zona["on"].sum()) if not en_zona.empty else 0
total_off = int(en_zona["off"].sum()) if not en_zona.empty else 0
n_puntos  = len(en_zona)

# ---- ACTUALIZAR KPIs (arriba) ----
m_on.metric("Ascensos", f"{total_on:,}", border=True)
m_off.metric("Descensos", f"{total_off:,}", border=True)
m_pts.metric("Eventos dentro del área", f"{n_puntos:,}", border=True)

# (Opcional) tabla
with st.expander("Ver puntos dentro de la zona"):
    st.dataframe(en_zona, use_container_width=True)

