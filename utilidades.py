import streamlit as st
import ceiba_client as cbc

def navegacion():
    with st.sidebar:
        st.title('Paneles')
        st.page_link('app.py',label=' Totales',icon='📊')
        st.page_link('pages/Unidades.py',label=' Unidades',icon='🚍')
        st.page_link('pages/Ruta.py',label=' Ruta',icon='🚦')

#Grupos por defecto

def sidebar_grupos(key_prefix: str = "grp"):
    """
    Dibuja el sidebar con el select de grupos (selección única).
    - Default = primer grupo que tenga al menos 1 unidad.
    - Guarda en session_state: selected_groupid, selected_groupname
    - Retorna: (selected_groupid, selected_groupname, terids_del_grupo, err)
    """
    with st.sidebar:
        st.title("Grupo")

        grupos, err_g = cbc.listar_grupos()
        if err_g:
            return None, None, [], f"Error al obtener grupos: {err_g}"
        if not grupos:
            return None, None, [], "No hay grupos disponibles para tu usuario."

        # Opciones visibles y mapa nombre->id
        groupnames = [g.get("groupname") for g in grupos if g.get("groupname")]
        name2id = {g.get("groupname"): g.get("groupid") for g in grupos if g.get("groupname") and g.get("groupid")}

        # Cargamos todos los dispositivos una sola vez y contamos por groupid
        dispositivos_all, err_d = cbc.listar_dispositivos_simplificado()
        if err_d:
            return None, None, [], f"Error al obtener dispositivos: {err_d}"

        conteo_por_gid = {}
        for d in dispositivos_all:
            gid = d.get("groupid")
            if gid is None:
                continue
            conteo_por_gid[gid] = conteo_por_gid.get(gid, 0) + 1

        # Default = primer grupo con al menos una unidad
        default_index = 0
        for idx, g in enumerate(grupos):
            gid = g.get("groupid")
            if conteo_por_gid.get(gid, 0) > 0:
                default_index = idx
                break

        selected_groupname = st.selectbox(
            "Selecciona un grupo",
            options=groupnames,
            index=default_index,
            key=f"{key_prefix}_sb_grupo"
        )
        selected_groupid = name2id.get(selected_groupname)

    # Guardar en sesión para otras vistas
    st.session_state["selected_groupname"] = selected_groupname
    st.session_state["selected_groupid"] = selected_groupid

    # Terids del grupo seleccionado (filtrando del listado ya cargado)
    terids_del_grupo = [
        d.get("terid") for d in dispositivos_all
        if str(d.get("groupid")) == str(selected_groupid) and d.get("terid")
    ]

    if not terids_del_grupo:
        return selected_groupid, selected_groupname, [], "Este grupo no tiene unidades. Cambia de grupo para ver datos."

    return selected_groupid, selected_groupname, terids_del_grupo, None


#Unidades
from typing import Callable, Dict, List, Optional, Tuple

def multiselect_unidades_por_grupo(
    groupid: str | int,
    listar_dispositivos_fn: Callable[[], Tuple[List[Dict], Optional[str]]],
    *,
    key_prefix: str = "unidades",
    label: str = "Selecciona las unidades (placa)",
    default_all: bool = True,
) -> Tuple[List[str], List[str | int], Dict[str, str | int]]:
    """
    Muestra un multiselect con las placas (unidades) pertenecientes a `groupid`.
    Persiste y devuelve la selección.

    Parámetros
    ----------
    groupid : str|int
        ID del grupo previamente seleccionado.
    listar_dispositivos_fn : función que devuelve (dispositivos, err)
        dispositivos: lista de dicts con al menos {"groupid","carlicence","terid"}.
    key_prefix : str
        Prefijo para las keys de Streamlit (evita colisiones).
    label : str
        Etiqueta del multiselect.
    default_all : bool
        Si True y no hay selección previa, preselecciona todas las placas del grupo.

    Retorna
    -------
    (placas_sel, terids_sel, map_placa_terid)
    """
    if groupid is None:
        st.warning("No se ha proporcionado un groupid.")
        return [], [], {}

    dispositivos, err = listar_dispositivos_fn()
    if err:
        st.error(err)
        return [], [], {}

    # Filtra dispositivos por grupo
    dispo_grupo = [d for d in dispositivos if d.get("groupid") == groupid]
    if not dispo_grupo:
        st.info("Este grupo no tiene unidades disponibles.")
        return [], [], {}

    # Construye opciones y mapeo placa->terid
    placas_opciones = sorted({d.get("carlicence") for d in dispo_grupo if d.get("carlicence")})
    map_placa_terid = {
        d["carlicence"]: d["terid"]
        for d in dispo_grupo
        if d.get("carlicence") and d.get("terid") is not None
    }

    # Default: última selección persistida o todas (si default_all=True)
    prev_key = f"{key_prefix}_placas_sel"
    default_placas = [p for p in st.session_state.get(prev_key, []) if p in placas_opciones]
    if not default_placas and default_all:
        default_placas = placas_opciones

    placas_sel = st.multiselect(
        label,
        options=placas_opciones,
        default=default_placas,
        key=f"{key_prefix}_placas_multiselect",
    )

    terids_sel = [map_placa_terid[p] for p in placas_sel if p in map_placa_terid]

    # Persistir selección
    st.session_state[f"{key_prefix}_grupo_id"] = groupid
    st.session_state[prev_key] = placas_sel
    st.session_state[f"{key_prefix}_terids_sel"] = terids_sel

    return placas_sel, terids_sel, map_placa_terid
