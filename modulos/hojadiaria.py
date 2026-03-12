import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Sistema de Vigilancia Epidemiológica")

# --- 1. CONEXIÓN SEGURA Y OBTENCIÓN DE IDS ---
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

# --- 2. LECTURA DEL CENSO (URL NUBE) ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_censo():
    try:
        return pd.read_csv(URL_ORIGEN)
    except:
        return None

# --- 3. FUNCIÓN MAESTRA: PROCESAR VIGILANCIA ---
def motor_vigilancia(ss, h_orig, n_orig, gid_orig, h_dest, gid_dest, fila_datos, reg_map, index_p):
    try:
        # Mapeo origen: A=0, B=1, C=2, D=3, E=4, G=6, I=8
        registro = str(fila_datos.iloc[3]).strip()
        fecha_dt = datetime.strptime(str(fila_datos.iloc[0]), "%d/%m/%Y")
        columna_x = fecha_dt.day + 3 
        
        # DECISIÓN: ¿Existe el paciente?
        if registro in reg_map:
            fila_inicio_dest = reg_map[registro]
            accion = "Actualizado"
        else:
            # Si es nuevo, se coloca al final (basado en index_p o filas existentes)
            # Para esta lógica de "Vigilancia Diaria", buscamos la última fila con datos
            vals = h_dest.get_all_values()
            fila_inicio_dest = len(vals) + 1
            
            # Clonamos la plantilla (A3:AI10)
            body = {
                "requests": [{
                    "copyPaste": {
                        "source": {"sheetId": gid_orig, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": gid_dest, "startRowIndex": fila_inicio_dest - 1, "endRowIndex": fila_inicio_dest + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }
                }]
            }
            ss.batch_update(body)
            accion = "Nuevo"

        # Llenamos/Actualizamos datos en el bloque
        # Celdas: B3(+0), B4(+1), A5(+2), B7(+4), B8(+5), B9(+6)
        batch = [
            {'range': f'Historial!B{fila_inicio_dest + 0}', 'values': [[str(fila_datos.iloc[1])]]}, # ESPECIALIDAD
            {'range': f'Historial!B{fila_inicio_dest + 1}', 'values': [[str(fila_datos.iloc[2])]]}, # CAMA
            {'range': f'Historial!A{fila_inicio_dest + 2}', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente
            {'range': f'Historial!B{fila_inicio_dest + 4}', 'values': [[str(fila_datos.iloc[6])]]}, # EDAD
            {'range': f'Historial!B{fila_inicio_dest + 5}', 'values': [[str(fila_datos.iloc[3])]]}, # REGISTRO
            {'range': f'Historial!B{fila_inicio_dest + 6}', 'values': [[str(fila_datos.iloc[8])]]}  # F. INGRESO
        ]
        ss.batch_update({'valueInputOption': 'USER_ENTERED', 'data': batch})
        
        # Marcamos la "X" (Fila 4 original -> fila_inicio_dest + 1)
        h_dest.update_cell(fila_inicio_dest + 1, columna_x, "X")
        
        return accion
    except Exception as e:
        if "429" in str(e):
            time.sleep(15)
            return False
        return f"Error: {e}"

# --- 4. INTERFAZ ---
# Botón de Refresh para cargar censo
if st.button("🔄 ACTUALIZAR CENSO (Refresh)", use_container_width=True):
    df = cargar_censo()
    if df is not None:
        st.session_state['df_vigilancia'] = df
        st.success(f"Censo cargado: {len(df)} pacientes detectados.")

if 'df_vigilancia' in st.session_state:
    df_pacientes = st.session_state['df_vigilancia']
    
    st.metric("📊 Pacientes en Censo", len(df_pacientes))
    
    with st.expander("🔍 Ver listado de pacientes detectados"):
        st.dataframe(df_pacientes.iloc[:, [3,4,2,1]], use_container_width=True, hide_index=True)

    st.divider()

    # BOTONES DE DECISIÓN
    st.subheader("🛠️ Acciones de Vigilancia")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚩 INICIO DE VIGILANCIA", help="Borra historial y genera plantillas nuevas para todos"):
            ss, h_ma, n_ma, gid_ma, h_hi, gid_hi = conectar_google_sheets()
            if ss:
                h_hi.clear()
                st.warning("Historial reseteado. Generando cuadros...")
                prog = st.progress(0)
                for i, row in df_pacientes.iterrows():
                    motor_vigilancia(ss, h_ma, n_ma, gid_ma, h_hi, gid_hi, row, {}, i)
                    prog.progress((i+1)/len(df_pacientes))
                    time.sleep(5)
                st.success("¡Vigilancia inicial completa!")

    with col2:
        if st.button("🔄 VIGILANCIA DIARIA", type="primary", help="Sincroniza: actualiza existentes y añade nuevos"):
            ss, h_ma, n_ma, gid_ma, h_hi, gid_hi = conectar_google_sheets()
            if ss:
                msg = st.empty()
                msg.info("Analizando historial para evitar duplicados...")
                
                # Mapeo de registros en B8 (fila 6 de cada bloque)
                data_h = h_hi.get_all_values()
                reg_map = {}
                for r in range(5, len(data_h), 8):
                    reg_val = str(data_h[r][1]).strip()
                    if reg_val: reg_map[reg_val] = r - 5 + 1
                
                prog = st.progress(0)
                for i, row in df_pacientes.iterrows():
                    msg.text(f"Sincronizando: {row.iloc[4]}")
                    motor_vigilancia(ss, h_ma, n_ma, gid_ma, h_hi, gid_hi, row, reg_map, i)
                    prog.progress((i+1)/len(df_pacientes))
                    time.sleep(5)
                msg.success("¡Vigilancia diaria actualizada!")
