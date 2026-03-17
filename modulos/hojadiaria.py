import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONEXIÓN (Mantenemos tu lógica de gspread) ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        # Tu ID de Sheet
        ss = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        
        h_maestra = ss.get_worksheet(0) # Plantilla
        try:
            h_hoja2 = ss.worksheet("Hoja 2")     # Fuente de datos limpios
            h_historial = ss.worksheet("Historial") # Destino de plantillas
        except Exception as e:
            st.error(f"Error al encontrar pestañas: {e}")
            return None, None, None, None
            
        return ss, h_maestra, h_hoja2, h_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None

def actualizar_bloque_paciente(h_hi, fila_base, fila_datos, col_x):
    """Mantiene tu lógica original de mapeo de celdas"""
    lista_celdas = [
        gspread.Cell(row=fila_base, col=2, value=str(fila_datos.iloc[1])),     # Especialidad
        gspread.Cell(row=fila_base + 1, col=2, value=str(fila_datos.iloc[2])), # Cama
        gspread.Cell(row=fila_base + 2, col=1, value=str(fila_datos.iloc[4])), # Paciente
        gspread.Cell(row=fila_base + 4, col=2, value=str(fila_datos.iloc[6])), # Edad
        gspread.Cell(row=fila_base + 5, col=2, value=str(fila_datos.iloc[3])), # Registro
        gspread.Cell(row=fila_base + 6, col=2, value=str(fila_datos.iloc[8])), # F. Ingreso
        gspread.Cell(row=fila_base + 1, col=col_x, value="X")                  # Marcado X
    ]
    h_hi.update_cells(lista_celdas, value_input_option='USER_ENTERED')

# --- INTERFAZ ---
st.title("🏥 Generador de Plantillas (Desde Hoja 2)")

if st.button("🔄 VIGILANCIA DIARIA (Desde Hoja 2)", type="primary", use_container_width=True):
    ss, h_ma, h_h2, h_hi = conectar_google_sheets()
    
    if ss:
        status = st.empty()
        status.info("📥 Leyendo datos filtrados de la Hoja 2...")
        
        # Leer los datos de la Hoja 2 para procesarlos
        datos_h2 = h_h2.get_all_records()
        df_h2 = pd.DataFrame(datos_h2)
        
        if df_h2.empty:
            st.error("La Hoja 2 está vacía. Primero usa la pestaña de Filtrado.")
            st.stop()

        status.info("🔍 Mapeando Historial para evitar duplicados...")
        col_b = h_hi.col_values(2) 
        reg_map = {}
        
        # Mapear bloques de 8 filas en el historial
        for i in range(5, len(col_b), 8):
            val = str(col_b[i]).strip()
            if val and val != "" and val != "Registro":
                reg_map[val] = (i + 1) - 5

        ingresos = 0
        seguimientos = 0
        f_disponible = len(col_b) + 1
        prog = st.progress(0)
        
        for idx, row in df_h2.iterrows():
            # El Registro está en la Columna D (index 3)
            reg_id = str(row.iloc[3]).strip()
            # La Fecha está en la Columna A (index 0)
            dia = int(str(row.iloc[0]).split('/')[0])
            
            status.text(f"Procesando: {row.iloc[4]}")

            if reg_id in reg_map:
                # PACIENTE EXISTE: Actualizar su bloque
                actualizar_bloque_paciente(h_hi, reg_map[reg_id], row, dia + 3)
                seguimientos += 1
            else:
                # PACIENTE NUEVO: Copiar bloque de plantilla (8 filas)
                ss.batch_update({"requests": [{"copyPaste": {
                    "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                    "destination": {"sheetId": h_hi.id, "startRowIndex": f_disponible - 1, "endRowIndex": f_disponible + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                    "pasteType": "PASTE_NORMAL"
                }}]})
                actualizar_bloque_paciente(h_hi, f_disponible, row, dia + 3)
                reg_map[reg_id] = f_disponible
                f_disponible += 8
                ingresos += 1
            
            prog.progress((idx+1)/len(df_h2))
            time.sleep(2) # Para no saturar la API de Google

        status.empty()
        st.subheader("📋 Resumen de Generación")
        c1, c2 = st.columns(2)
        c1.metric("🆕 Plantillas Nuevas", ingresos)
        c2.metric("📋 Seguimientos Actualizados", seguimientos)
        st.success("✅ Historial sincronizado con Hoja 2.")
