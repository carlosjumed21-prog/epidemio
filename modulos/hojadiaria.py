import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria - Generador de Kardex")

# --- 1. CONEXIÓN SEGURA Y DETECCIÓN DE NOMBRES ---
def conectar_google_sheets():
    try:
        # Extraemos credenciales desde secrets
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
        nombre_maestra = hoja_maestra.title # Esto resuelve el error 'Hoja 1'!A3
        
        # Buscamos o creamos la pestaña de Historial
        try:
            hoja_historial = ss.worksheet("Historial")
        except:
            hoja_historial = ss.add_worksheet(title="Historial", rows="2000", cols="35")
            
        return ss, hoja_maestra, nombre_maestra, hoja_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None

# --- 2. LECTURA DEL CENSO DE ORIGEN ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        # Cargamos el CSV publicado
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

df_pacientes = cargar_censo()

# --- 3. LÓGICA DE PROCESAMIENTO (LLENAR -> CLONAR FORMATO) ---
def procesar_paciente(ss, h_orig, nombre_orig, h_dest, fila_datos, index_paciente):
    try:
        # Procesar fecha y calcular columna de la X
        fecha_val = str(fila_datos.iloc[0])
        dt = datetime.strptime(fecha_val, "%d/%m/%Y")
        columna_x = dt.day + 3 # Día 1 = Columna D (4)
        
        # 1. Llenar los datos directamente en la plantilla de la Hoja 1
        # Esto asegura que el bloque que vamos a copiar ya tenga la info y el formato
        batch = [
            {'range': 'B3', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad
            {'range': 'B4', 'values': [[str(fila_datos.iloc[2])]]}, # Cama
            {'range': 'A5', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente
            {'range': 'B8', 'values': [[str(fila_datos.iloc[6])]]}, # Edad
            {'range': 'B9', 'values': [[str(fila_datos.iloc[3])]]}, # Registro
            {'range': 'B10', 'values': [[str(fila_datos.iloc[8])]]},# Ingreso
            {'range': 'D4:AH4', 'values': [[''] * 31]}             # Limpiar X anteriores
        ]
        h_orig.batch_update(batch)
        h_orig.update_cell(4, columna_x, "X") # Poner X nueva

        # 2. Copiar el bloque completo (datos + formato) al Historial
        # Cada bloque mide 8 filas (A3:AI10)
        fila_dest = (index_paciente * 8) + 1
        rango_orig_completo = f"'{nombre_orig}'!A3:AI10"
        rango_dest_completo = f"A{fila_dest}:AI{fila_dest + 7}"
        
        # Clonamos el rango de Hoja 1 a Hoja Historial
        h_dest.copy_range(rango_orig_completo, rango_dest_completo)
        
        return True
    except Exception as e:
        if "429" in str(e):
            st.warning(f"⏳ Pausa por cuota de Google. Esperando 15s...")
            time.sleep(15)
            return False
        st.error(f"Error con {fila_datos.iloc[4]}: {e}")
        return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    st.link_button("📂 Abrir Archivo en Google Sheets", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    
    st.metric("Pacientes detectados", len(df_pacientes))
    
    st.divider()
    limpiar = st.checkbox("Limpiar historial antes de iniciar el vaciado masivo", value=True)

    if st.button("📥 INICIAR PROCESAMIENTO MASIVO", type="primary"):
        ss, h_maestra, n_maestra, h_historial = conectar_google_sheets()
        
        if h_maestra and h_historial:
            if limpiar:
                h_historial.clear()
                st.info(f"Historial reseteado. Usando plantilla de: {n_maestra}")

            progreso = st.progress(0)
            status = st.empty()
            total_p = len(df_pacientes)
            
            for i, row in df_pacientes.iterrows():
                nombre_p = row.iloc[4]
                status.text(f"Procesando ({i+1}/{total_p}): {nombre_p}")
                
                # Ejecutar proceso. Si falla por cuota, reintenta tras pausa.
                if not procesar_paciente(ss, h_maestra, n_maestra, h_historial, row, i):
                    time.sleep(10)
                    procesar_paciente(ss, h_maestra, n_maestra, h_historial, row, i)
                
                progreso.progress((i + 1) / total_p)
                # Pausa necesaria de 8 segundos para no saturar la API de Google con formatos
                time.sleep(8) 
            
            # Limpiar la plantilla maestra al terminar para dejarla lista
            h_maestra.batch_update([{'range': 'A3:AI10', 'values': [[''] * 35] * 8}])
            
            status.success("✅ ¡Proceso completado! Todos los Kardex con formato están en 'Historial'.")
            st.balloons()
else:
    st.error("No se pudo cargar el censo de origen.")
