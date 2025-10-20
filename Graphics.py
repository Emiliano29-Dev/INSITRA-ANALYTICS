import plotly.express as px
import pandas as pd


#Importamos datasets prcesados para la construcción del gráfico


# P A S A J E R O S    P O R   U N I D A D    Y   D I A.

#Graficamos PUD (Pasajeros por unidad y día) en Histograma
def pasajeros_unidad_dia(   #Argumentos
        df: pd.DataFrame, 
        unidades: list[str],
        rango_fechas: tuple,
        valor: str 
):

    #Agregamos filtros para mostrar datos

    #Fecha
    mascara_fecha = ((df['Apertura de puerta'] >= rango_fechas[0]) &
                    (df['Apertura de puerta'] <= rango_fechas[1])
                    )
    
    #Unidad (Si el usuario no elige nada, se muestran todas las unidades)
    mascara_unidad = df['Unidad'].isin(unidades) if unidades else True

    #Dataset preseleccionado
    df_filtrado = df.loc[mascara_fecha & mascara_unidad, ['Apertura de puerta', 'Unidad', valor]].copy()
    
    #Revisa si el dataset esta vacío
    if df_filtrado.empty:
        return None, pd.Dataframe()

    #Ordenamos los datos
    df_filtrado = df_filtrado.sort_values(['Apertura de puerta','Unidad'])

    #Grafico de lineas por unidad.
    fig = px.line(
        df_filtrado,
        x='Apertura de puerta',
        y = valor,
        color = 'Unidad',
        markers = True,
        title = f"{valor} por unidad y día.",
    )

    fig.update_layout(
        #Tamaño del titulo de la gráfica.
        title=dict(
            x=0.5,
            xanchor='center',
            font=dict(size=28),
        ),
        xaxis_title = 'Dia',
        yaxis_title = valor,
        hovermode = 'x unified',
        legend_title = 'Unidad',  
    )

    return fig, df_filtrado


# K I L O M E T R A J E    P O R    U N I D A D    Y    D I A.

def kilometros_unidad_dia(
        df: pd.DataFrame,
        unidades: list[str],
        rango_fechas: tuple,
        valor: str,

):
    #Agregamos filtros para mostrar datos

    #Fecha
    mascara_fecha = ((df['Dia inicio'] >= rango_fechas[0]) &
                    (df['Dia inicio'] <= rango_fechas[1])
                    )
    
    #Unidad (Si el usuario no elige nada, se muestran todas las unidades)
    mascara_unidad = df['Unidad'].isin(unidades) if unidades else True

    #Dataset preseleccionado
    df_filtrado = df.loc[mascara_fecha & mascara_unidad, ['Dia inicio', 'Unidad', valor]].copy()
    
    #Revisa si el dataset esta vacío
    if df_filtrado.empty:
        return None, pd.Dataframe()

    #Ordenamos los datos
    df_filtrado = df_filtrado.sort_values(['Dia inicio','Unidad'])

    fig = px.bar(
        df_filtrado,
        x = valor,
        y = 'Dia inicio',
        color = 'Unidad',
        barmode = 'group',
        height = 800,

        title = f"{valor} por unidad y día.",
    )

    fig.update_layout(
        #Tamaño del titulo de la gráfica.
        title=dict(
            x=0.5,
            xanchor='center',
            font=dict(size=28),
        ),
        xaxis_title = valor,
        yaxis_title = 'Dia',
        hovermode = 'x unified',
        legend_title = 'Unidad',  
    )

    return fig, df_filtrado

# P A S A J E R O S  P O R   U N I D A D   D I A   P R O M E D I O

def pasajeros_por_unidad_dia_promedio(
        df: pd.DataFrame,
        valor: str,
):
    #Df organizado:
    df = df.sort_values(['Dia'])

    #Configuración de la gráfica
    fig = px.line(
        df,
        x = 'Dia',
        y = valor,
        markers=True,
        title = f"{valor} por día.",
    )

    fig.update_layout(
        #Tamaño del titulo de la gráfica.
        title=dict(
            x=0.5,
            xanchor='center',
            font=dict(size=28),
        ),
        xaxis_title = 'Dia',
        yaxis_title = valor,
        hovermode = 'x unified',
        legend_title = 'Unidad',  
    )

    fig.update_yaxes(
        range = [0,None], #Empieza en 0 y hasta donde llegue
        rangemode = 'tozero',
        zeroline = True,
    )

    return fig

