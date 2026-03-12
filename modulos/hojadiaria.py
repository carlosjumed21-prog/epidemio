import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria - Procesamiento con Corte a Historial")

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
        
        hoja_principal = ss.get_worksheet(0) # Hoja 1 (Plantilla)
        try:
            hoja_historial = ss.worksheet("Historial") # Intentar buscar Hoja 2
        except:
            hoja_historial = ss.add_worksheet(title="Historial", rows="2000", cols="35")
            
        return ss, hoja_principal, hoja_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None

# --- 2. LECTURA DEL CENSO ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

df_pacientes = cargar_censo()

# --- 3. LÓGICA DE PROCESAMIENTO: LLENAR -> COPIAR -> MOVER ---
def procesar_y_mover_a_historial(ss, h_orig, h_dest, fila_datos, index_paciente):
    try:
        dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        columna_x = dt.day + 3
        
        # 1. LLENAR LOS DATOS EN LA PLANTILLA ORIGINAL (A3:AI10)
        batch = [
            {'range': 'B3', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad
            {'range': 'B4', 'values': [[str(fila_datos.iloc[2])]]}, # Cama
            {'range': 'A5', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente
            {'range': 'B8', 'values': [[str(fila_datos.iloc[6])]]}, # Edad
            {'range': 'B9', 'values': [[str(fila_datos.iloc[3])]]}, # Registro
            {'range': 'B10', 'values': [[str(fila_datos.iloc[8])]]},# Ingreso
            {'range': 'D4:AH4', 'values': [[''] * 31]}             # Limpiar X previas
        ]
        h_orig.batch_update(batch)
        h_orig.update_cell(4, columna_x, "X") # Poner la X del día

        # 2. CALCULAR DESTINO EN HOJA 2 (HISTORIAL)
        # Cada bloque mide 8 filas. 
        fila_inicio_dest = (index_paciente * 8) + 1
        rango_dest = f"A{fila_inicio_dest}:AI{fila_inicio_dest + 7}"

        # 3. COPIAR DE HOJA 1 A HOJA 2 (Mantiene formato porque usamos copy_range entre hojas)
        h_dest.copy_range(f"'{h_orig.title}'!A3:AI10", rango_dest)
        
        return True
    except Exception as e:
        if "429" in str(e):
            st.warning("⏳ Límite excedido. Esperando 15s...")
            time.sleep(15)
            return False
        st.error(f"Error con {fila_datos.iloc[4]}: {e}")
        return False

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    st.link_button("📂 Abrir Hoja de Salida", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    st.metric("Pacientes detectados", len(df_pacientes))
    
    st.divider()
    
    limpiar_historial = st.checkbox("Limpiar pestaña de Historial antes de empezar", value=True)

    if st.button("📥 INICIAR PROCESAMIENTO MASIVO", type="primary"):
        ss, h_orig, h_dest = conectar_google_sheets()
        
        if h_orig and h_dest:
            if limpiar_historial:
                h_dest.clear()
                st.info("Historial limpiado.")

            progreso = st.progress(0)
            status = st.empty()
            total = len(df_pacientes)
            
            for i, row in df_pacientes.iterrows():
                nombre = row.iloc[4]
                status.text(f"Procesando ({i+1}/{total}): {nombre}")
                
                # Ejecutamos la lógica de Llenar y Copiar a Hoja 2
                if not procesar_y_mover_a_historial(ss, h_orig, h_dest, row, i):
                    time.sleep(5)
                    procesar_y_mover_a_historial(ss, h_orig, h_dest, row, i)
                
                progreso.progress((i + 1) / total)
                # Pausa de seguridad para no saturar la API con formatos
                time.sleep(7) 
            
            # 4. LIMPIEZA FINAL DE LA PLANTILLA MAESTRA
            # Dejamos la Hoja 1 lista para el siguiente uso (opcional)
            limpieza_maestra = [
                {'range': 'B3:B4', 'values': [[''], ['']]},
                {'range': 'A5', 'values': [['']]},
                {'range': 'B8:B10', 'values': [[''], [''], ['']]},
                {'range': 'D4:AH4', 'values': [[''] * 31]}
            ]
            h_orig.batch_update(limpieza_maestra)
            
            status.success("✅ ¡Censo completado! Todos los formatos están en la pestaña 'Historial'.")
            st.balloons()
else:
    st.error("No se pudo cargar el censo.")
