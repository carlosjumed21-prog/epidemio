import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria - Generador de Kardex")

# --- 1. CONEXIÓN SEGURA Y DINÁMICA ---
def conectar_google_sheets():
    try:
        # Extraemos credenciales desde secrets de Streamlit
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Abrir el archivo por su ID
        ss = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        
        # Detectamos la hoja maestra (índice 0) dinámicamente
        hoja_maestra = ss.get_worksheet(0)
        nombre_maestra = hoja_maestra.title # Resuelve el error de 'Hoja 1'
        
        # Buscamos o creamos la pestaña de Historial
        try:
            hoja_historial = ss.worksheet("Historial")
        except:
            # Si no existe, crea una hoja con espacio suficiente
            hoja_historial = ss.add_worksheet(title="Historial", rows="3000", cols="35")
            
        return ss, hoja_maestra, nombre_maestra, hoja_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None

# --- 2. LECTURA DEL CENSO (ORIGEN) ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

df_pacientes = cargar_censo()

# --- 3. LÓGICA DE PROCESAMIENTO: LLENAR -> CLONAR FORMATO ---
def procesar_paciente(ss, h_orig, nombre_orig, h_dest, fila_datos, index_paciente):
    try:
        # Procesar fecha y columna X
        fecha_str = str(fila_datos.iloc[0])
        dt = datetime.strptime(fecha_str, "%d/%m/%Y")
        columna_x = dt.day + 3 # Día 1 = Columna D (4)
        
        # 1. Llenar los datos primero en la Hoja 1 (donde está el formato)
        batch = [
            {'range': 'B3', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad
            {'range': 'B4', 'values': [[str(fila_datos.iloc[2])]]}, # Cama
            {'range': 'A5', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente
            {'range': 'B8', 'values': [[str(fila_datos.iloc[6])]]}, # Edad
            {'range': 'B9', 'values': [[str(fila_datos.iloc[3])]]}, # Registro
            {'range': 'B10', 'values': [[str(fila_datos.iloc[8])]]},# Ingreso
            {'range': 'D4:AH4', 'values': [[''] * 31]}             # Limpieza X previa
        ]
        h_orig.batch_update(batch)
        h_orig.update_cell(4, columna_x, "X") # Marcar día actual

        # 2. Copiar bloque completo (datos + formato) a la pestaña Historial
        # Bloques de 8 filas (A3:AI10)
        fila_dest = (index_paciente * 8) + 1
        
        # Sintaxis de rango cruzado: 'Nombre de Hoja'!A1:B2
        rango_orig_completo = f"'{nombre_orig}'!A3:AI10"
        rango_dest_completo = f"A{fila_dest}:AI{fila_dest + 7}"
        
        # Comando para duplicar el rango de una pestaña a otra
        h_dest.copy_range(rango_orig_completo, rango_dest_completo)
        
        return True
    except Exception as e:
        if "429" in str(e):
            st.warning("⏳ Pausa por límite de Google. Esperando 15s...")
            time.sleep(15)
            return False
        st.error(f"Error con {fila_datos.iloc[4]}: {e}")
        return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    st.link_button("📂 Abrir Kardex en Google Sheets", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    
    st.metric("Total de Pacientes en Censo", len(df_pacientes))
    
    with st.expander("🔍 Ver listado de pacientes"):
        st.dataframe(df_pacientes, use_container_width=True, hide_index=True)

    st.divider()
    
    limpiar_h = st.checkbox("Limpiar historial antes de iniciar el procesamiento", value=True)

    if st.button("📥 INICIAR VACIADO MASIVO A HISTORIAL", type="primary"):
        ss, h_maestra, n_maestra, h_historial = conectar_google_sheets()
        
        if h_maestra and h_historial:
            if limpiar_h:
                h_historial.clear()
                st.info(f"Historial vaciado. Usando plantilla de: {n_maestra}")

            progreso = st.progress(0)
            status = st.empty()
            total_p = len(df_pacientes)
            
            for i, row in df_pacientes.iterrows():
                nombre_p = row.iloc[4]
                status.text(f"Procesando ({i+1}/{total_p}): {nombre_p}")
                
                # Ejecutar proceso
                if not procesar_paciente(ss, h_maestra, n_maestra, h_historial, row, i):
                    time.sleep(10)
                    procesar_paciente(ss, h_maestra, n_maestra, h_historial, row, i)
                
                progreso.progress((i + 1) / total_p)
                # Pausa necesaria para evitar error 429 de Google al copiar formatos
                time.sleep(8) 
            
            # Limpieza final de la hoja maestra (Opcional, borra los datos del último paciente)
            h_maestra.batch_update([{'range': 'A3:AI10', 'values': [[''] * 35] * 8}])
            
            status.success("✅ ¡Censo completado! Revisa la pestaña 'Historial' para ver todos los formatos.")
            st.balloons()
else:
    st.error("No se pudo cargar el censo de origen.")
