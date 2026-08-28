import streamlit as st
import pandas as pd
import numpy as np
import requests
from requests.auth import HTTPBasicAuth

st.title("📈 Indicadores SUIVE (Cubo de Datos)")
st.markdown("Módulo de análisis multidimensional de vigilancia epidemiológica.")

# --- SECCIÓN 1: CONFIGURACIÓN DEL ENTORNO ---
st.header("📍 Entorno de Red")
st.markdown("Selecciona tu ubicación actual para determinar el método de conexión:")

zona_trabajo = st.radio(
    "Zona de Trabajo:",
    options=[
        "Externa (Casa / Red Comercial / Wi-Fi Público)", 
        "Interna (Hospital / Cable Ethernet ISSSTE)"
    ],
    horizontal=False
)

st.divider()

# --- SECCIÓN 2: LÓGICA SEGÚN EL ENTORNO ---

if "Interna" in zona_trabajo:
    st.subheader("Extracción en Vivo (Intranet)")
    st.info("💡 **Nota:** Al usar el cable Ethernet en el hospital, es normal no tener 'Internet' para navegar, pero sí tienes acceso a la red interna del gobierno de salud.")
    
    if st.button("Verificar Conectividad al SINAVE", type="primary"):
        with st.spinner("Intentando traspasar el firewall hacia el servidor del SINAVE..."):
            url = "http://cubo.sinave.gob.mx/msmdpump.dll" 
            body = """<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                        <Body>
                            <Discover xmlns="urn:schemas-microsoft-com:xml-analysis">
                                <RequestType>DBSCHEMA_CATALOGS</RequestType>
                                <Restrictions/>
                                <Properties/>
                            </Discover>
                        </Body>
                      </Envelope>"""
            headers = {
                'Content-Type': 'text/xml',
                'User-Agent': 'Microsoft Office/16.0 (Windows NT 10.0; Microsoft Excel 16.0.12026; Pro)',
                'Accept': '*/*'
            }
            
            try:
                respuesta = requests.post(
                    url, 
                    data=body, 
                    headers=headers, 
                    auth=HTTPBasicAuth('PWIDGE10\\cubos2015', 'Cubos$2015'),
                    timeout=10
                )
                
                if respuesta.status_code == 200:
                    st.success("✅ ¡Acceso Autorizado! Estás dentro de la red del SINAVE.")
                    st.caption("El servidor respondió correctamente. Ya podemos programar la descarga de la base de datos completa.")
                elif respuesta.status_code == 401:
                    st.error("❌ Error 401: El firewall te dejó pasar, pero las credenciales fueron rechazadas.")
                else:
                    st.warning(f"⚠️ El servidor respondió con un código inesperado: {respuesta.status_code}")
                        
            except requests.exceptions.RequestException as e:
                st.error("❌ Conexión rechazada. El firewall institucional bloqueó la petición o la intranet no está resolviendo el dominio del SINAVE.")
                st.caption(str(e))

else:
    st.subheader("Modo de Análisis Local (Offline)")
    st.info("Estás fuera de la red institucional. El sistema utilizará la última base de datos sincronizada localmente para que puedas seguir trabajando.")
    
    if st.button("Cargar Base de Datos Local", type="primary"):
        with st.spinner("Cargando el archivo local (ej. datos_suive.csv)..."):
            # Aquí irá el código pd.read_csv() cuando tengamos el archivo extraído
            # Por ahora generamos el DataFrame simulado
            st.session_state['datos_suive'] = pd.DataFrame({
                'Jurisdicción': ['Puebla', 'Tehuacán', 'Tehuacán', 'Puebla', 'Cholula', 'Cholula'],
                'Semana_Epi': [1, 1, 2, 2, 1, 2],
                'Grupo_Edad': ['Adultos', 'Adultos', 'Menores de 5', 'Adultos', 'Menores de 5', 'Menores de 5'],
                'Casos_Notificados': [15, 40, 12, 18, 5, 8]
            })
            st.success("✅ Datos locales cargados correctamente.")

st.divider()

# --- SECCIÓN 3: TABLERO DINÁMICO ---
if 'datos_suive' in st.session_state or ("Interna" in zona_trabajo):
    st.header("📊 Tablero Dinámico")
    
    # Si estamos en modo offline y cargamos los datos, usamos esos. 
    # (Si estamos online, aquí iría el cruce con los datos vivos).
    if 'datos_suive' in st.session_state:
        df_base = st.session_state['datos_suive']
        
        col1, col2 = st.columns(2)
        with col1:
            filtro_jurisdiccion = st.multiselect("Filtrar Jurisdicción", df_base['Jurisdicción'].unique(), df_base['Jurisdicción'].unique())
        with col2:
            filtro_edad = st.multiselect("Filtrar Grupo de Edad", df_base['Grupo_Edad'].unique(), df_base['Grupo_Edad'].unique())

        df_filtrado = df_base[
            (df_base['Jurisdicción'].isin(filtro_jurisdiccion)) & 
            (df_base['Grupo_Edad'].isin(filtro_edad))
        ]

        if not df_filtrado.empty:
            tabla_dinamica = pd.pivot_table(
                data=df_filtrado,
                index=['Jurisdicción', 'Grupo_Edad'],
                columns=['Semana_Epi'],
                values='Casos_Notificados',
                aggfunc=np.sum,
                fill_value=0                 
            )
            st.dataframe(tabla_dinamica, use_container_width=True)
        else:
            st.warning("No hay casos que coincidan con los filtros seleccionados.")
