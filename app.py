#Importamos utilidades del sistema
import streamlit as st
import pandas as pd
from datetime import date, timedelta


#Improtamos utilidades propias de la aplicación
import ceiba_client as cbc
import procesed as pcd
import graphics as graph
import utilidades as util

#Configuracion básica de la página
st.set_page_config(
    page_title='Insitra Analytics: Totales',
    page_icon='Recursos_visuales/insitra imagotipo.png'
    
)

#Requerimos el inicio de sesión.
cbc.login()
cbc.require_login()

#Agregamos selección de grupos
gid, gname, terids_del_grupo, err_sidebar = util.sidebar_grupos(key_prefix="tot")
if err_sidebar:
    st.warning(err_sidebar)
    st.stop()


#Agregamos el sidebar de navegacion.
util.navegacion()

#Vista de la página.
st.title('INSITRA ANALYTICS: Totales 📊')

st.set_page_config(
    layout='wide'
)

#
# Aqui va a ir la barra de indicadores generales SOLO DEL DIA

# C O N T E O   D E   P A S A J E R O S

#Titulo de la sección
st.header('Conteo de pasajeros')
#Barra de selección de fecha.
#Delay de fehcas
date_presetp = date.today() - timedelta(days=6)

c1,c2 = st.columns(2)
with c1:
    iniciop = st.date_input('Inicio',date_presetp,key='iniciop')
with c2:
    finalp = st.date_input('Final',key='finalp')

if iniciop > finalp:
    st.error('La fecha final debe ser más reciente que la fecha de inicio')

#Final de la declaración de fechas.

#Declaramos el json
conteo_pasajeros = {
        "terid": terids_del_grupo,
        "starttime": f"{iniciop} 00:00:00",
        "endtime": f"{finalp} 23:59:59"
        }

#Realizamos la petición de PDAP: 
#Pasajeros unidad dia promedio
ok, payload, err = cbc.api_post('basic/passenger-count/detail',json=conteo_pasajeros)
#Verificamos que la respuesta haya sido exitosa
if ok:
    conteo = pd.DataFrame(payload.get('data'))
    pdap = pcd.construir_padp(conteo,30)

#Graficamos pdapfig1 = Total de ascensos por dia
pdapfig1 = graph.pasajeros_por_unidad_dia_promedio(
    df = pdap,
    valor = 'Total de ascensos',
)

pdapfig2 = graph.pasajeros_por_unidad_dia_promedio(
    df = pdap,
    valor = 'Promedio por unidad',
)

if pdapfig1 is None or pdap.empty:
    st.warning('No hay datos en las fechas seleccionadas')  
else:
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(pdapfig1, use_container_width=True)
    with c2:
        st.plotly_chart(pdapfig2, use_container_width=True)
    with st.expander('Ver los datos mostrados en la gráfica'):
        st.dataframe(pdap)

#      K I L O M E T R A J E

#Título de la sección
st.header('Kilometraje')

#Barra de selección de fecha.

#Delay de fehcas
date_presetk = date.today() - timedelta(days=6)

c1,c2 = st.columns(2)
with c1:
    iniciok = st.date_input('Inicio',date_presetk,key='iniciok')
with c2:
    finalk = st.date_input('Final',key='finalk')

if iniciok > finalk:
    st.error('La fecha final debe ser más reciente que la fecha de inicio')

#Declaramos el json
kilometraje = {
        "terid": terids_del_grupo,
        "starttime": f"{iniciok} 00:00:00",
        "endtime": f"{finalk} 23:59:59"
        }


#Pasajeros unidad dia promedio
ok, payload, err = cbc.api_post('basic/mileage/count',json=kilometraje)
#Verificamos que la respuesta haya sido exitosa
if ok:
    conteo = pd.DataFrame(payload.get('data'))
    kipd = pcd.construir_kipd(conteo,30)
    

#Graficamos pdapfig1 = Total de ascensos por dia
kipdfig1 = graph.pasajeros_por_unidad_dia_promedio(
    df = kipd,
    valor = 'Kilometraje',
)

kipdfig2 = graph.pasajeros_por_unidad_dia_promedio(
    df = kipd,
    valor = 'Promedio por unidad',
)

if kipdfig1 is None or pdap.empty:
    st.warning('No hay datos en las fechas seleccionadas')  
else:
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(kipdfig1, use_container_width=True)
    with c2:
        st.plotly_chart(kipdfig2, use_container_width=True)
    with st.expander('Ver los datos mostrados en la gráfica'):
        st.dataframe(kipd)