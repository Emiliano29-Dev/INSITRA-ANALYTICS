# ------------------ Configuración y imports ------------------
from datetime import date, timedelta
import streamlit as st
import pandas as pd

import ceiba_client as cbc
import utilidades as util
import procesed as pcd
import graphics as graph
# import graphics as graph  # si lo necesitas después

st.set_page_config(
    page_title='Insitra Analytics: Unidades',
    page_icon='Recursos_visuales/insitra imagotipo.png',
    layout='wide',
)

# ------------------ Autenticación y sidebar ------------------
cbc.login()
cbc.require_login()

# 1) Sidebar de navegación (tu menú)
util.navegacion()

# 2) Sidebar de grupos (con prefijo propio para no chocar con otras páginas)
gid, gname, terids_del_grupo, err_sidebar = util.sidebar_grupos(key_prefix="uni")
if err_sidebar:
    st.warning(err_sidebar)
    st.stop()

# ------------------ Vista principal ------------------
st.title('INSITRA ANALYTICS: Unidades 🚍')
st.header('Conteo de pasajeros')

# ---------- Selección por unidades ----------
# Obtenemos dispositivos del usuario y filtramos por el grupo activo
dispositivos, err = cbc.listar_dispositivos_simplificado()
if err:
    st.error(err)
    st.stop()

dispositivos = [d for d in dispositivos if str(d.get("groupid")) == str(gid)]

placas = [d.get("carlicence") for d in dispositivos if d.get("carlicence")]
map_placa_to_terid = {
    d.get("carlicence"): d.get("terid")
    for d in dispositivos
    if d.get("carlicence") and d.get("terid")
}

#Mapeamos de regreso
map_terid_to_placa = {
    str(d.get("terid")): d.get("carlicence")
    for d in dispositivos
    if d.get("carlicence") and d.get("terid")
}

sel_placas = st.multiselect("Unidades", options=placas, key="uni_ms_unidades")

# Si no se elige nada, tomamos TODAS las del grupo
if sel_placas:
    sel_terids = [map_placa_to_terid[p] for p in sel_placas]
else:
    sel_terids = [map_placa_to_terid[p] for p in placas]

# ---------- Rango de fechas ----------
date_presetp = date.today() - timedelta(days=6)

c1, c2 = st.columns(2)
with c1:
    iniciop = st.date_input('Inicio', date_presetp, key='uni_inicio')
with c2:
    finalp = st.date_input('Final', key='uni_final')

if iniciop > finalp:
    st.error('La fecha final debe ser más reciente que la fecha de inicio')
    st.stop()

# ---------- Llamada a la API ----------
conteo_pasajeros = {
    "terid": sel_terids,
    "starttime": f"{iniciop} 00:00:00",
    "endtime": f"{finalp} 23:59:59",
}

rango_fechas = (iniciop,finalp)

ok, payload, err = cbc.api_post("basic/passenger-count/detail", json=conteo_pasajeros)
if not ok:
    st.error(err or "Error consultando CEIBA")
    st.stop()

# ---------- Procesamiento y vista ----------
conteo = pd.DataFrame(payload.get('data') or [])
if conteo.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

pud = pcd.construir_pud(conteo)  # tu función de procesado por unidad/día

if "Unidad" in pud.columns:
    pud["Unidad"] = pud["Unidad"].astype(str).map(map_terid_to_placa).fillna(pud["Unidad"])
elif "terid" in pud.columns:
    pud["terid"] = pud["terid"].astype(str).map(map_terid_to_placa).fillna(pud["terid"])
    # (opcional) si prefieres que la columna final se llame 'Unidad':
    pud = pud.rename(columns={"terid": "Unidad"})

#G R A F I C A M O S
pfig, pud_plot = graph.pasajeros_unidad_dia(
    df = pud,
    unidades = sel_placas,
    rango_fechas = rango_fechas,
    valor = 'Ascensos'
)

#Excepsiones
if pfig is None or pud_plot.empty:
    st.warning('No hay datos de las fechas seleccionadas')
else:
    st.plotly_chart(pfig,use_container_width=True)
    with st.expander('Ver los datos mostrados en la gráfica'):
        st.dataframe(pud,use_container_width=True)



