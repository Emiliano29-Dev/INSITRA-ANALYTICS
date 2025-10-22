import streamlit as st
import requests

API = st.secrets.get("CEIBA_BASE_URL")
# ---------------------------------------------------------------------
# AUTENTICACIÓN
# ---------------------------------------------------------------------

#Valida que el usuario y la contraseña sean correctos
def validarUsuario(usuario: str, clave: str):
    try:
        resp = requests.get(
            f"{API}/basic/key",
            params={"username": usuario, "password": clave},
            timeout=20,
        )
    except requests.RequestException as e:
        return False, None, f"Error de red: {e}"

    try:
        data = resp.json()
    except ValueError:
        return False, None, "Respuesta no es JSON."

    err = data.get("errorcode")
    if err == 200:
        key = (data.get("data") or {}).get("key")
        if key:
            return True, key, None
        return False, None, "Respuesta inesperada: falta 'data.key'."
    elif err == 206:
        return False, None, "Credenciales incorrectas."
    else:
        return False, None, f"Error de aplicación (errorcode={err})."

#Guarda la sesión obtenida en "sesion_state, api_key y usuario"
def _guardar_sesion(usuario: str, api_key: str):
    st.session_state["usuario"] = usuario
    st.session_state["api_key"] = api_key

#Cierra sesión
def cerrar_sesion():
    st.session_state.clear()
    st.rerun()
#Usamos para hacer get (Iniciar sesion)
def api_get(endpoint: str, params: dict):

    if "api_key" not in st.session_state:
        return False, None, "No autenticado (falta api_key)."

    p = dict(params or {})
    p["key"] = st.session_state["api_key"]

    try:
        r = requests.get(f"{API}/{endpoint.lstrip('/')}", params=p, timeout=10)
    except requests.RequestException as e:
        return False, None, f"Error de red: {e}"

    try:
        data = r.json()
    except ValueError:
        return False, None, "Respuesta no es JSON."

    return True, data, None

#Lo utilizamos para hacer peticiones (de datos)
def api_post(endpoint: str, json: dict):

    if "api_key" not in st.session_state:
        return False, None, "No autenticado (falta api_key)."

    #p = dict(params or {})
    key = st.session_state["api_key"]
    json["key"] = key

    try:
        r = requests.post(
            f"{API}/{endpoint.lstrip('/')}",
            json=json,  
            timeout=20,
        )
    except requests.RequestException as e:
        return False, None, f"Error de red: {e}"

    # Algunas APIs devuelven siempre 200; igual parseamos JSON
    try:
        payload = r.json()
    except ValueError:
        return False, None, f"Respuesta no es JSON. HTTP {r.status_code}: {r.text[:200]}"

    return True, payload, None


### Juanito
@st.cache_data(ttl=300)
def listar_grupos():
    ok, payload, err = api_get("basic/groups", params={'key': st.session_state.get("api_key")})
    if not ok:
        return [], err
    grupos = payload.get("data", []) or []
    # Normaliza llaves esperadas
    out = []
    for g in grupos:
        item = {
            "groupid": g.get("groupid"),
            "groupname": g.get("groupname"),
        }
        out.append(item)

    return out, None


###Juanito
@st.cache_data(ttl=300)
def listar_dispositivos_simplificado(groupid: str | None = None):
    """
    Devuelve la lista de dispositivos del usuario en un formato normalizado:
      { "groupid": str, "carlicence": str, "terid": str }
    Si se especifica groupid, filtra por ese grupo.
    Es robusta a variaciones de llaves del backend.
    """
    # Pedimos todos los dispositivos del usuario
    ok, payload, err = api_get("basic/devices", params={'key': st.session_state.get("api_key")})
    if not ok:
        return [], err

    raw = payload.get("data", []) or []
    out = []

    for d in raw:
        # Normalización de llaves
        gid = d.get("groupid") or d.get("groupId") or d.get("group_id")
        placa = d.get("carlicence") or d.get("carLicense") or d.get("car_licence")
        ter = d.get("terid") or d.get("terminalId") or d.get("terminal_id")

        # Filtrado por groupid si se pidió
        if groupid is not None and str(gid) != str(groupid):
            continue

        item = {
            "groupid": gid,
            "carlicence": placa,
            "terid": ter,
        }
        out.append(item)

    return out, None

#Modificaciones Emiliano

###Emiliano
@st.cache_data(ttl=300)
def grupo_por_defecto():
    """
    Devuelve (groupid, groupname, err) del primer grupo disponible para el usuario.
    """
    grupos, err = listar_grupos()
    if err:
        return None, None, err
    if not grupos:
        return None, None, "Sin grupos disponibles."
    g0 = grupos[0]
    return g0.get("groupid"), g0.get("groupname"), None

###Opciones de grupos
@st.cache_data(ttl=300)
def opciones_de_grupos():
    """
    Regresa (groupnames, map_name_to_id, err) para poblar el sidebar.
    """
    grupos, err = listar_grupos()
    if err:
        return [], {}, err

    groupnames = [g.get("groupname") for g in grupos if g.get("groupname")]
    map_name_to_id = {
        g.get("groupname"): g.get("groupid")
        for g in grupos
        if g.get("groupname") and g.get("groupid")
    }
    return groupnames, map_name_to_id, None

###Emiliano
@st.cache_data(ttl=300)
def listar_dispositivos_por_grupo(groupid: str):
    """
    Filtra los dispositivos del usuario por un groupid dado.
    Retorna (lista_de_dispositivos, err). Dispositivo = {groupid, carlicence, terid}.
    """
    if not groupid:
        return [], "groupid no proporcionado."

    dispositivos, err = listar_dispositivos_simplificado()
    if err:
        return [], err

    filtrados = [d for d in dispositivos if d.get("groupid") == groupid]
    return filtrados, None

###Emiliano
@st.cache_data(ttl=300)
def placas_y_mapas_por_grupo(groupid: str):
    """
    Para un groupid dado:
      - Lista de placas (carlicence)
      - map_placa_to_terid
      - map_terid_to_placa
    Retorna (placas, map_placa_to_terid, map_terid_to_placa, err)
    """
    dispositivos, err = listar_dispositivos_por_grupo(groupid)
    if err:
        return [], {}, {}, err

    placas = []
    map_placa_to_terid = {}
    map_terid_to_placa = {}

    for d in dispositivos:
        placa = d.get("carlicence")
        terid = d.get("terid")
        if placa and terid:
            placas.append(placa)
            map_placa_to_terid[placa] = terid
            map_terid_to_placa[terid] = placa

    return placas, map_placa_to_terid, map_terid_to_placa, None

####Emiliano
@st.cache_data(ttl=300)
def terids_por_grupo(groupid: str):
    """
    Devuelve solo la lista de terids del groupid.
    Retorna (terids, err)
    """
    dispositivos, err = listar_dispositivos_por_grupo(groupid)
    if err:
        return [], err
    return [d.get("terid") for d in dispositivos if d.get("terid")], None



#Modificaciones Emiliano

def generarMenu(usuario):
     
    with st.sidebar:
        
        st.write(f"Hola **:blue-background[{usuario}]** ¿Que vamos a hacer hoy? ")
        
        c1,c2,c3 = st.columns([1,1,1])
        with c2:
            if st.button('Salir'):
                cerrar_sesion()

        

def login():
    if "usuario" in st.session_state and "api_key" in st.session_state:
        generarMenu(st.session_state["usuario"])
    else:
        # Contenedor centrado por columnas
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            # Título "centrado" al ponerlo en la columna central
            st.markdown(
                "<h1 style='text-align:center;'> Iniciar Sesión </h1>",
                unsafe_allow_html=True
            )

            with st.form("frmLogin"):
                # Labels grandes (ocultamos el label nativo del input)
                st.subheader("Usuario")
                parUsuario = st.text_input("", placeholder="Ingresa tu usuario",
                                           label_visibility="collapsed")

                st.subheader("Contraseña")
                parPassword = st.text_input("", type="password", placeholder="Ingresa tu contraseña",
                                            label_visibility="collapsed")

                # Botón centrado en la columna media
                b1, b2, b3 = st.columns([1, 2, 1])
                with b2:
                    btnLogin = st.form_submit_button("Acceder", type="primary",
                                                     use_container_width=True)
                
                st.echo('Recuerda acceder con el mismo usuario y contraseña de CEIBA II ')
                    
                

        if btnLogin:
            with st.spinner("Validando..."):
                ok, key, err = validarUsuario(parUsuario, parPassword)
            if ok and key:
                _guardar_sesion(parUsuario, key)
                st.rerun()
            else:
                st.error(err or "Usuario o clave inválidos", icon=":material/gpp_maybe:")
                



def require_login():
    """
    Úsalo al inicio de cada página interna para forzar que haya sesión.
    """
    if "usuario" not in st.session_state or "api_key" not in st.session_state:
        st.stop()

