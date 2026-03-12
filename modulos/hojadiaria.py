import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria - Actualización Inteligente")

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
        
        hoja_maestra = ss.get_worksheet(0)
        gid_maestra = hoja_maestra.id
        nombre_maestra = hoja_maestra.title
        
        try:
            hoja_historial = ss.worksheet("Historial")
        except:
            hoja_historial = ss.add_worksheet(title="Historial", rows="3000", cols="35")
        
        gid_historial = hoja_historial.id
            
        return ss, hoja_maestra, nombre_maestra, gid_maestra, hoja_historial, gid_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return [None]*6

# --- 2. LECTURA DEL CENSO ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

df_pacientes = cargar_censo()

# --- 3. FUNCIÓN DE ACTUALIZACIÓN O CREACIÓN ---
def procesar_inteligente(ss, h_ma, n_ma, gid_ma, h_hi, gid_hi, fila_datos, registro_map):
    try:
        # Datos origen
        registro_actual = str(fila_datos.iloc[3]) # Col D
        dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        columna_x = dt.day + 3 

        # ¿El paciente ya existe en el Historial?
        if registro_actual in registro_map:
            # ACTUALIZACIÓN: Solo actualizamos datos en su bloque existente
            fila_inicio_dest = registro_map[registro_actual]
            tipo_accion = "Actualizado"
        else:
            # CREACIÓN: Nuevo bloque al final
            total_filas_actuales = len(h_hi.get_all_values())
            # Si la hoja está vacía, empezamos en 1, si no, en la siguiente después del último bloque
            fila_inicio_dest = total_filas_actuales + 1 if total_filas_actuales > 0 else 1
            tipo_accion = "Nuevo"

            # Si es nuevo, primero clonamos el formato de la Hoja 1
            body_clonar = {
                "requests": [{
                    "copyPaste": {
                        "source": {"sheetId": gid_ma, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": gid_hi, "startRowIndex": fila_inicio_dest - 1, "endRowIndex": fila_inicio_dest + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }
                }]
            }
            ss.batch_update(body_clonar)

        # En ambos casos (nuevo o existente), actualizamos los datos del bloque
        batch = [
            {'range': f'Historial!B{fila_inicio_dest + 0}', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad (B3)
            {'range': f'Historial!B{fila_inicio_dest + 1}', 'values': [[str(fila_datos.iloc[2])]]}, # Cama (B4)
            {'range': f'Historial!A{fila_inicio_dest + 2}', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente (A5)
            {'range': f'Historial!B{fila_inicio_dest + 4}', 'values': [[str(fila_datos.iloc[6])]]}, # Edad (B7)
            {'range': f'Historial!B{fila_inicio_dest + 5}', 'values': [[str(fila_datos.iloc[3])]]}, # Registro (B8)
            {'range': f'Historial!B{fila_dest_inicio + 6}', 'values': [[str(fila_datos.iloc[8])]]}  # Ingreso (B9)
        ]
        # Nota: Ajusté los índices de fila_inicio_dest para que coincidan con B3, B4, A5, B7, B8, B9
        # B3 es +0, B4 es +1, A5 es +2, B7 es +4, B8 es +5, B9 es +6 relative al inicio del bloque.
        
        # Mandamos los datos
        ss.batch_update({'valueInputOption': 'USER_ENTERED', 'data': batch})
        # Marcamos la X
        h_hi.update_cell(fila_inicio_dest + 1, columna_x, "X")
        
        return tipo_accion
    except Exception as e:
        return f"Error: {e}"

# --- 4. INTERFAZ ---
if df_pacientes is not None:
    st.metric("📊 Pacientes en Censo Actual", len(df_pacientes))
    
    if st.button("📥 SINCRONIZAR HISTORIAL (Sin duplicados)", type="primary"):
        ss, h_ma, n_ma, gid_ma, h_hi, gid_hi = conectar_google_sheets()
        
        if h_ma and h_hi:
            status = st.empty()
            status.info("Leyendo historial existente para detectar duplicados...")
            
            # --- MAPEAR REGISTROS EXISTENTES ---
            # Buscamos en la columna B de Historial (donde cae el Registro B8)
            # El Registro B8 está en la fila 6 de cada bloque de 8 filas.
            todas_las_celdas = h_hi.get_all_values()
            registro_map = {}
            for i in range(5, len(todas_las_celdas), 8): # Empezamos en fila 6 (indice 5), saltamos de 8 en 8
                val_registro = todas_las_celdas[i][1] # Columna B (indice 1)
                if val_registro:
                    registro_map[val_registro] = i - 5 + 1 # Guardamos la fila de inicio del bloque

            progreso = st.progress(0)
            total = len(df_pacientes)
            nuevos = 0
            actualizados = 0

            for i, row in df_pacientes.iterrows():
                nombre = row.iloc[4]
                status.text(f"Procesando {i+1}/{total}: {nombre}")
                
                resultado = procesar_inteligente(ss, h_ma, n_ma, gid_ma, h_hi, gid_hi, row, registro_map)
                
                if resultado == "Nuevo": nuevos += 1
                elif resultado == "Actualizado": actualizados += 1
                
                progreso.progress((i + 1) / total)
                time.sleep(5) # Pausa de seguridad
            
            status.success(f"✅ Sincronización completa: {nuevos} nuevos, {actualizados} actualizados.")
            st.balloons()
