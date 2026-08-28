import streamlit as st
import pandas as pd
import numpy as np
import requests
from requests.auth import HTTPBasicAuth

st.title("📈 Indicadores SUIVE (Cubo de Datos)")
st.markdown("Módulo para conexión en vivo y análisis multidimensional de datos del SINAVE.")

# --- SECCIÓN 1: PRUEBA DE CONEXIÓN AL SERVIDOR ---
st.header("1. Conexión al Servidor SINAVE")
st.info("Utiliza las credenciales extraídas del archivo de Excel para verificar si el servidor permite consultas remotas.")

if st.button("Probar Conexión con SINAVE", type="primary"):
    with st.spinner("Enviando petición SOAP al cubo OLAP..."):
        url = "http://cubo.sinave.gob.mx/msmdpump.dll" 
        
        # Petición XMLA (XML for Analysis) para descubrir bases de datos
        body = """<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                    <Body>
                        <Discover xmlns="urn:schemas-microsoft-com:xml-analysis">
                            <RequestType>DBSCHEMA_CATALOGS</RequestType>
                            <Restrictions/>
                            <Properties/>
                        </Discover>
                    </Body>
                  </Envelope>"""
        
        # Cabeceras actualizadas simulando ser Microsoft Excel
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
                st.success("✅ ¡Conexión exitosa! El servidor respondió correctamente.")
                with st.expander("Ver respuesta del servidor (XML)"):
                    st.code(respuesta.text[:1500], language='xml')
            elif respuesta.status_code == 401:
                st.error("❌ Error 401: Autenticación fallida. Las credenciales son incorrectas o no tienen acceso remoto.")
            elif respuesta.status_code == 404:
                st.error("❌ Error 404: Endpoint no encontrado. Es probable que la ruta pública msmdpump.dll esté bloqueada.")
            else:
                st.warning(f"⚠️ El servidor respondió con un código inesperado: {respuesta.status_code}")
                with st.expander("Ver detalles del error"):
                    st.code(respuesta.text[:500])
                    
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error de red al intentar conectar: {e}")

st.divider()

# --- SECCIÓN 2: ESTRUCTURA DE LA TABLA DINÁMICA ---
st.header("2. Tablero Dinámico (Estructura)")
st.markdown("Visualización de prueba con la estructura de filtros y agrupación que se alimentará de los datos en vivo.")

# Datos simulados basados en variables típicas de vigilancia
df_simulado = pd.DataFrame({
    'Jurisdicción': ['Puebla', 'Tehuacán', 'Tehuacán', 'Puebla', 'Cholula', 'Cholula'],
    'Semana_Epi': [1, 1, 2, 2, 1, 2],
    'Grupo_Edad': ['Adultos', 'Adultos', 'Menores de 5', 'Adultos', 'Menores de 5', 'Menores de 5'],
    'Casos_Notificados': [15, 40, 12, 18, 5, 8]
})

# Filtros (Área de Filtros en Excel)
col1, col2 = st.columns(2)
with col1:
    filtro_jurisdiccion = st.multiselect("Filtrar Jurisdicción", df_simulado['Jurisdicción'].unique(), df_simulado['Jurisdicción'].unique())
with col2:
    filtro_edad = st.multiselect("Filtrar Grupo de Edad", df_simulado['Grupo_Edad'].unique(), df_simulado['Grupo_Edad'].unique())

# Aplicar filtros
df_filtrado = df_simulado[
    (df_simulado['Jurisdicción'].isin(filtro_jurisdiccion)) & 
    (df_simulado['Grupo_Edad'].isin(filtro_edad))
]

# Crear y mostrar tabla dinámica
if not df_filtrado.empty:
    tabla_dinamica = pd.pivot_table(
        data=df_filtrado,
        index=['Jurisdicción', 'Grupo_Edad'],  # Área de Filas
        columns=['Semana_Epi'],                # Área de Columnas
        values='Casos_Notificados',            # Área de Valores
        aggfunc=np.sum,                        # Operación
        fill_value=0                 
    )
    st.dataframe(tabla_dinamica, use_container_width=True)
else:
    st.warning("No hay casos que coincidan con los filtros seleccionados.")
