import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria - Procesamiento Masivo")

# --- 1. CONEXIÓN ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        ss = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        
        # Intentamos obtener o crear la Hoja 2
        try:
            hoja_historial = ss.worksheet("Historial")
        except:
            hoja_historial = ss.add_worksheet(title="Historial", rows="1000", cols="35")
            
        return ss.get_worksheet(0), hoja_historial # Retorna (Plantilla, Historial)
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None

# --- 2. LECTURA DEL CENSO ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

df_pacientes = cargar_censo()

# --- 3. LÓGICA DE PROCESAMIENTO A HOJA 2 ---
def procesar_a_historial(h_plantilla, h_historial, fila_datos, index_paciente):
    try:
        dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        dia_num = dt.day
        columna_x = dia_num + 3
        
        # Calculamos dónde pegar en la Hoja 2 (cada bloque mide 8 filas)
        # El primer paciente en la fila 1, el segundo en la 9, etc.
        fila_destino = (index_paciente * 8) + 1
        rango_destino = f"A{fila_destino}:AI{fila_destino + 7}"

        # PASO 1: Copiar formato y estructura de Hoja 1 a Hoja 2
        h_historial.copy_range("A3:AI10", rango_destino)

        # PASO 2: Llenar datos en el bloque recién copiado en Hoja 2
        # Ajustamos las coordenadas sumando el desplazamiento de fila_destino
        batch = [
            {'range': f'B{fila_destino + 0}', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad (original B3)
            {'range': f'B{fila_destino + 1}', 'values': [[str(fila_datos.iloc[2])]]}, # Cama (original B4)
            {'range': f'A{fila_destino + 2}', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente (original A5)
            {'range': f'B{fila_destino + 5}', 'values': [[str(fila_datos.iloc[6])]]}, # Edad (original B8)
            {'range': f'B{fila_destino + 6}', 'values': [[str(fila_datos.iloc[3])]]}, # Registro (original B9)
            {'range': f'B{fila_destino + 7}', 'values': [[str(fila_datos.iloc[8])]]}  # Ingreso (original B10)
        ]
        h_historial.batch_update(batch)

        # PASO 3: Poner la "X" en la fila correspondiente al día (original fila 4 -> destino + 1)
        h_historial.update_cell(fila_destino + 1, columna_x, "X")
        
        return True
    except Exception as e:
        if "429" in str(e):
            time.sleep(15)
            return False
        st.error(f"Error: {e}")
        return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    st.link_button("📂 Abrir Google Sheets", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    
    st.metric("Pacientes en Censo", len(df_pacientes))
    
    with st.expander("🔍 Ver listado"):
        st.dataframe(df_pacientes, use_container_width=True, hide_index=True)

    st.divider()

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Vaciado Masivo a Hoja 2", type="primary"):
            h_plant, h_hist = conectar_google_sheets()
            if h_plant and h_hist:
                # Opcional: Limpiar Hoja 2 antes de empezar
                if st.confirm("¿Deseas limpiar la Hoja 2 antes de iniciar?"):
                    h_hist.clear()
                
                progreso = st.progress(0)
                status = st.empty()
                
                for i, row in df_pacientes.iterrows():
                    nombre = row.iloc[4]
                    status.text(f"Copiando a Historial ({i+1}/{len(df_pacientes)}): {nombre}")
                    
                    if procesar_a_historial(h_plant, h_hist, row, i):
                        progreso.progress((i + 1) / len(df_pacientes))
                        time.sleep(5) # Pausa para estabilidad
                    else:
                        st.warning(f"Reintentando {nombre}...")
                        time.sleep(10)
                        procesar_a_historial(h_plant, h_hist, row, i)
                
                status.success("✅ ¡Todo el censo ha sido movido a la Hoja 2!")
                st.balloons()
    
    with col2:
        if st.button("🧹 Limpiar Hoja 2 (Historial)"):
            _, h_hist = conectar_google_sheets()
            if h_hist:
                h_hist.clear()
                st.success("Hoja de historial vaciada.")

else:
    st.error("No se pudo cargar el censo.")
