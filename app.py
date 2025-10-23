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
    page_icon='Recursos_visuales/insitra_logo.png',
    layout='wide'
)

#Requerimos el inicio de sesión.
cbc.login()
cbc.require_login()

#Agregamos selección de grupos (Sólo grupos en este caso: Es un Análisis de totales.)
gid, gname, terids_del_grupo, err_sidebar = util.sidebar_grupos(key_prefix="tot")
if err_sidebar:
    st.warning(err_sidebar)
    st.stop()


#Agregamos el sidebar de navegacion.
util.navegacion()

#Vista de la página.
st.title('INSITRA ANALYTICS: Totales 📊')

#KPI'S generales

#Seleccion de fechas para los KPIS

#Tomamos automáticamente 6 dias
date_presetg = date.today() - timedelta(days=6)

#Inicio y final
iniciog = date_presetg
finalg = date.today()

#Inicio y final en tupla
rango_fechas_g = (iniciog,finalg)

#Peticion de datos.


st.header('Cifras del dia')

#JSON pasajeros
conteo_pasajerosg = {
        "terid": terids_del_grupo,
        "starttime": f"{iniciog} 00:00:00",
        "endtime": f"{finalg} 23:59:59"
        }

#JSON kilometraje
kilometrajeg = {
        "terid": terids_del_grupo,
        "starttime": f"{iniciog} 00:00:00",
        "endtime": f"{finalg} 23:59:59"
        }

#Iniciamos la peticion P A S A J E R O S
ok, payload, err = cbc.api_post('basic/passenger-count/detail',json=conteo_pasajerosg)

#Construimos el dataset
if ok:
    conteog = pd.DataFrame(payload.get('data'))
    kpigp = pcd.construir_padp(conteog,30)

##Iniciamos la peticion K I L O M E T R O S
ok, payload, err = cbc.api_post('basic/mileage/count',json=kilometrajeg)

#Construimos el dataset
if ok:
    kilometrajeg = pd.DataFrame(payload.get('data'))
    kpigk = pcd.construir_kipd(kilometrajeg,30)

#Dataset's muestra

st.dataframe(kpigp,use_container_width=True)

# C O N S T R U C C I O N    D E L    K P I

#KPI'S
#Pasajeros actuales
pasg_actuales = kpigp.iloc[-1,-3]
#Pasajeros promedio por unidad actuales
pasgp_actuales = kpigp.iloc[-1,-1]
#kilometros actuales
ktg = kpigk.iloc[-1,-3]
#kilometros promedio por unidad
kpg = kpigk.iloc[-1,-1]

#KPI'S PROMEDIO COMPARATIVO
#pasg_actuales_prom = kpigp[]


row = st.container(horizontal=True)
#Empiezan las divisiones.
with row:
    st.metric('Ascensos del dia'  , f'{pasg_actuales} Personas', border = True)
    st.metric('Ascensos promedio' , f'{pasgp_actuales}', border=True)
    st.metric('Kilometros del día', f'{ktg} Km ', border=True)
    st.metric('Kilometros promedio', f'{kpg}', border=True)
# Aqui va a ir la barra de indicadores generales SOLO DEL DIA



#Barra de indicadroes
# C O N T E O   D E   P A S A J E R O S

#Titulo de la sección
st.header('Conteo de pasajeros')

#INICIO SELECCION DE FECHA.
#Delay de fehcas
date_presetp = date.today() - timedelta(days=6)

c1,c2 = st.columns(2)
with c1:
    iniciop = st.date_input('Inicio', date_presetp, key='iniciop')
with c2:
    finalp = st.date_input('Final', key='finalp')

if iniciop > finalp:
    st.error('La fecha final debe ser más reciente que la fecha de inicio')

#FINAL SELECCION DE FECHA.

#JSON PASAJEROS
conteo_pasajeros = {
        "terid": terids_del_grupo,
        "starttime": f"{iniciop} 00:00:00",
        "endtime": f"{finalp} 23:59:59"
        }

#Realizamos la petición de PDAP: Pasajeros unidad dia promedio
ok, payload, err = cbc.api_post('basic/passenger-count/detail',json=conteo_pasajeros)

#Construimos el dataset
if ok:
    conteo = pd.DataFrame(payload.get('data'))
    pdap = pcd.construir_padp(conteo,30)

#Graficamos pdapfig1 = Total de ascensos por dia
pdapfig1 = graph.pasajeros_por_unidad_dia_promedio(
    df = pdap,
    valor = 'Total de ascensos',
)

#Graficamos pdapfig2 = Promedio de ascensos por unidad.
pdapfig2 = graph.pasajeros_por_unidad_dia_promedio(
    df = pdap,
    valor = 'Promedio por unidad',
)

#Si no hay datos de la unidad "Warning"
if pdapfig1 is None or pdap.empty:
    st.warning('No hay datos en las fechas seleccionadas')  

#Ploteamos las graficas 
else:
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(pdapfig1, use_container_width=True)
    with c2:
        st.plotly_chart(pdapfig2, use_container_width=True)
    #Se dá al usuario el archivo de datos graficados
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
    iniciok = st.date_input('Inicio',date_presetk, key='iniciok')
with c2:
    finalk = st.date_input('Final', key='finalk')

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
    

#Graficamos: pdapfig1 = Total de kilometros por dia
kipdfig1 = graph.pasajeros_por_unidad_dia_promedio(
    df = kipd,
    valor = 'Kilometraje',
)

#Graficamos: kidpfig2 = Promedio de kilometros por dia (Consideramos 30km de tolerancia)
kipdfig2 = graph.pasajeros_por_unidad_dia_promedio(
    df = kipd,
    valor = 'Promedio por unidad',
)

#Casos
#A) Si no hay datos en el plot: Mostramos la leyenda
if kipdfig1 is None or pdap.empty:
    st.warning('No hay datos en las fechas seleccionadas')
    #B) si hay datos: Mostramos los plots y permitimos la descarga del dataset.  
else:
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(kipdfig1, use_container_width=True)
    with c2:
        st.plotly_chart(kipdfig2, use_container_width=True)
    with st.expander('Ver los datos mostrados en la gráfica'):
        st.dataframe(kipd)