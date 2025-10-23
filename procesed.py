     # U T I L I I D A D E S
import pandas as pd

# U N I D A D E S 


#Construimos pud: pasajeros por unidad y día. (espera parámetros de unidad)
def construir_pud(
        ps: pd.DataFrame,
):  
#Renombra la columnas del dataset
    ps  = ps.rename(columns={
        'terid': 'Unidad',
        'on': 'Ascensos',
        'off': 'Descensos',
        'opentime': 'Apertura de puerta',
        'closetime': 'Cierre de puerta',
        'lat': 'Latitud',
        'lng': 'Longitud',
    })
    
    #transforma a datetimes
    ps['Apertura de puerta'] = pd.to_datetime(ps['Apertura de puerta'], format="%Y-%m-%d %H:%M:%S")
    ps['Cierre de puerta'] = pd.to_datetime(ps['Cierre de puerta'], format="%Y-%m-%d %H:%M:%S")

    #Construimos el dataset.
    return (ps.groupby([ps['Apertura de puerta'].dt.date, 'Unidad'])[['Ascensos','Descensos']]
        .sum() #Sumamos los valores 
        .reset_index()) #Volvemos a convertir a un dataset


#Construimos kud: kilometros unidad y dia (Espera parámetros)
def construir_kud(
        km: pd.DataFrame,
):
    # Renombra la columnas del dataset
    km = km.rename(columns={
        'terid': 'Unidad',
        'mileage': 'Kilometraje',
        'starttime': 'Dia inicio',
        'endtime': 'Tiempo final',
    })

    # Asegura tipos correctos y tolera formatos inesperados
    km['Dia inicio']   = pd.to_datetime(km['Dia inicio'], errors='coerce')               
    km['Tiempo final'] = pd.to_datetime(km['Tiempo final'], errors='coerce')             
    km['Kilometraje']  = pd.to_numeric(km.get('Kilometraje'), errors='coerce')           

    # Limpia las fechas con la columna inválida
    km = km.dropna(subset=['Dia inicio'])

    # Deja 'Dia inicio' como date puro (para que compare bien con el input en el front end)
    km = km.assign(**{'Dia inicio': km['Dia inicio'].dt.date})

    # Construimos el dataset agrupado
    return (
        km.groupby(['Dia inicio', 'Unidad'], as_index=False)['Kilometraje']
          .sum() #Sumamos los valores
          .sort_values(['Dia inicio', 'Unidad']) #Lo convertimos a dataset ordenandolo por dia de inicio y luego unidad (Fecha y número de unidad)
    )
    
# Contruimos padp: pasajeros unidad dia promedio. (No espera unidades)

def construir_padp(pad: pd.DataFrame, umbral_ascensos_unidad: int):

    #Renombramos las columnas
    pad  = pad.rename(columns={
        'terid': 'Plate No.',
        'on': 'On person',
        'off': 'Off person',
        'opentime': 'Open door time',
        'closetime': 'Close door time',
        'lat': 'Latitud',
        'lng': 'Longitud',
    })

    # Tipado robusto (Forzamos el datetime)
    pad['Open door time']  = pd.to_datetime(pad['Open door time'],  errors='coerce')
    #También ponemos Close door time (En caso de que utilicemos DVR's viejos)
    pad['Close door time'] = pd.to_datetime(pad['Close door time'], errors='coerce')
    # Tipado robusto, en caso de que no llegara a ser un número y si es un None, lo rellena con 0
    pad['On person'] = pd.to_numeric(pad['On person'], errors='coerce').fillna(0)

    #Liampiamos los datos en caso de no tenerlos.
    pad = pad.dropna(subset=['Open door time']) #No lo considera si no tiene es valor, si arroja un None o no es un datetime

    # Utilizamos dia, por practicidad y lo volvemos a poner como datetime.
    pad['Dia'] = pad['Open door time'].dt.date

    
    # Agrupamos ascensos por unidad y dia (Tabla pivote)
    por_unidad = (
        pad.groupby(['Dia', 'Plate No.'], as_index=False)['On person']
           .sum()
           .rename(columns={'On person': 'Ascensos'})
    )

    # Reagrupamos pero ahora sin unidad, solo los totales
    totales_dia = (
        por_unidad.groupby('Dia', as_index=False)['Ascensos']
                  .sum()
                  .rename(columns={'Ascensos': 'Total de ascensos'})
    )

    # Establecemos un umbral de ascensos por unidad
    
    #CASO A, considera el umbral
    if umbral_ascensos_unidad > 0:
        activas = (
            por_unidad[por_unidad['Ascensos'] >= umbral_ascensos_unidad]
            .groupby('Dia', as_index=False)['Plate No.']
            .nunique()
            .rename(columns={'Plate No.': 'unidades_activas'})
        )
    #CASO B, no considera el umbral
    else:
        activas = (
            por_unidad.groupby('Dia', as_index=False)['Plate No.']
                      .nunique()
                      .rename(columns={'Plate No.': 'unidades_activas'})
        )

    #Creamos padp = pasajeros dia promedio
    padp = totales_dia.merge(activas, on='Dia', how='left')
    padp['unidades_activas'] = padp['unidades_activas'].fillna(0).astype(int)
    
    #Nos aseguramos que de haber 0's no nos afecten
    denom = padp['unidades_activas'].where(padp['unidades_activas'] != 0, 1)
    
    #Calculamos el promedio y nos volvemos a asegurar de que no haya errores en caso de que alguna día
    #ninguna unidad haya salido a trabajar y no se cuenten con unidades disponibles
    padp['Promedio por unidad'] = (padp['Total de ascensos'] / denom).where(padp['unidades_activas'] != 0, 0)
    #Redondeamos
    padp['Promedio por unidad'] = padp['Promedio por unidad'].round(0)

    #Ordenamos de nuevo
    padp = padp.sort_values('Dia', kind='stable')

    return padp

def construir_kipd(
        kipd: pd.DataFrame,
        umbral_kilometros: int,
):
    kipd = kipd.rename(columns={
        'terid': 'Unidad',
        'mileage': 'Kilometraje',
        'starttime': 'Dia inicio',
        'endtime': 'Tiempo final',
    })

    # Tipos
    kipd['Dia inicio']   = pd.to_datetime(kipd['Dia inicio'], errors='coerce')
    kipd['Kilometraje']  = pd.to_numeric(kipd['Kilometraje'], errors='coerce').fillna(0)

    # Limpieza
    kipd = kipd.dropna(subset=['Dia inicio'])
    kipd['Dia'] = kipd['Dia inicio'].dt.date

    # Totales por día (suma de km)
    totales_unidad_dia = kipd[['Unidad', 'Dia', 'Kilometraje']].copy()
    totales_dia = (
        kipd.groupby(['Dia'], as_index=False)['Kilometraje']
            .sum()
    )

    # Unidades activas (contar unidades únicas por día según umbral)
    if umbral_kilometros > 0:
        activas = (
            totales_unidad_dia[totales_unidad_dia['Kilometraje'] >= umbral_kilometros]
            .groupby('Dia', as_index=False)['Unidad']
            .nunique()
            .rename(columns={'Unidad': 'Unidades Activas'})
        )
    else:
        activas = (
            totales_unidad_dia
            .groupby('Dia', as_index=False)['Unidad']
            .nunique()
            .rename(columns={'Unidad': 'Unidades Activas'})
        )

    # Mezcla y métricas
    kipd = totales_dia.merge(activas, on='Dia', how='left')
    kipd['Unidades Activas'] = kipd['Unidades Activas'].fillna(0).astype(int)

    # Evitar división entre cero
    denom = kipd['Unidades Activas'].where(kipd['Unidades Activas'] != 0, 1)
    kipd['Promedio por unidad'] = (kipd['Kilometraje'] / denom).where(kipd['Unidades Activas'] != 0, 0)
    kipd['Promedio por unidad'] = kipd['Promedio por unidad'].round(0)
    kipd['Kilometraje'] = kipd['Kilometraje'].round(0)

    # Orden
    kipd = kipd.sort_values('Dia', kind='stable')
    return kipd



     
    
    

