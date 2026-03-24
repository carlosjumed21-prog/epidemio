import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONEXIÓN (Mismo código) ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        ss_origen = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        ss_salida = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        
        h_datos_limpios = ss_origen.get_worksheet(1) 
        h_plantilla = ss_salida.get_worksheet(0)     
        h_historial = ss_salida.get_worksheet(1)     
            
        return ss_salida, h_plantilla, h_datos_limpios, h_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None

# --- 2. FUNCIÓN DE ACTUALIZACIÓN (Mismo código) ---
def actualizar_bloque_paciente(h_hi, fila_base, fila_datos, col_x):
    try:
        lista_celdas = [
            gspread.Cell(row=fila_base, col=2, value=str(fila_datos.iloc[1])),     
            gspread.Cell(row=fila_base + 1, col=2, value=str(fila_datos.iloc[2])), 
            gspread.Cell(row=fila_base + 2, col=1, value=str(fila_datos.iloc[4])), 
            gspread.Cell(row=fila_base + 4, col=2, value=str(fila_datos.iloc[6])), 
            gspread.Cell(row=fila_base + 5, col=2, value=str(fila_datos.iloc[3])), 
            gspread.Cell(row=fila_base + 6, col=2, value=str(fila_datos.iloc[8])), 
            gspread.Cell(row=fila_base + 1, col=col_x, value="X")                  
        ]
        h_hi.update_cells(lista_celdas, value_input_option='USER_ENTERED')
    except Exception as e:
        if "429" in str(e):
            time.sleep(10)
        else:
            st.warning(f"Error en bloque: {e}")

# --- 3. INTERFAZ CON SELECCIÓN ---
st.title("🏥 Vigilancia Epidemiológica - Selección Manual")

if st.button("🔄 1. CARGAR/REFRESCAR CENSO", use_container_width=True):
    res = conectar_google_sheets()
    if res[0]:
        _, _, h_dat, _ = res
        df = pd.DataFrame(h_dat.get_all_records())
        # Insertar columna de selección al inicio
        df.insert(0, "Seleccionar", False)
        st.session_state['df_vig_check'] = df
        st.success(f"✅ {len(df)} pacientes listos para selección.")

if 'df_vig_check' in st.session_state:
    # Vista previa con casillas
    st.subheader("Seleccione los pacientes a procesar:")
    df_con_checks = st.data_editor(
        st.session_state['df_vig_check'],
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("¿Procesar?", default=False)
        },
        disabled=[col for col in st.session_state['df_vig_check'].columns if col != "Seleccionar"],
        hide_index=True,
        use_container_width=True
    )
    
    # Filtrar solo los elegidos para el proceso
    df_seleccionados = df_con_checks[df_con_checks["Seleccionar"] == True].drop(columns=["Seleccionar"])

    c1, c2 = st.columns(2)

    with c1:
        if st.button("🚩 INICIO (RECREAR ELEGIDOS)", use_container_width=True):
            if df_seleccionados.empty:
                st.warning("Selecciona al menos un paciente.")
            else:
                res = conectar_google_sheets()
                if res[0]:
                    ss_sal, h_pla, h_dat, h_his = res
                    h_his.clear() # Cuidado: esto borra toda la hoja de historial
                    f_nueva = 1
                    prog = st.progress(0)
                    for i, (idx, row) in enumerate(df_seleccionados.iterrows()):
                        ss_sal.batch_update({"requests": [{"copyPaste": {
                            "source": {"sheetId": h_pla.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                            "destination": {"sheetId": h_his.id, "startRowIndex": f_nueva - 1, "endRowIndex": f_nueva + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                            "pasteType": "PASTE_NORMAL"
                        }}]})
                        try:
                            dia = int(str(row.iloc[0]).split('/')[0])
                            actualizar_bloque_paciente(h_his, f_nueva, row, dia + 3)
                        except: pass
                        f_nueva += 8
                        prog.progress((i+1)/len(df_seleccionados))
                        time.sleep(2.5) 
                    st.success("✅ Historial recreado con seleccionados.")

    with c2:
        if st.button("🔄 ACTUALIZAR DIARIA (ELEGIDOS)", type="primary", use_container_width=True):
            if df_seleccionados.empty:
                st.warning("Selecciona al menos un paciente.")
            else:
                res = conectar_google_sheets()
                if res[0]:
                    ss_sal, h_pla, h_dat, h_his = res
                    status = st.empty()
                    col_b = h_his.col_values(2) 
                    reg_map = {}
                    
                    # Mapeo de lo que ya existe en el historial
                    for i in range(5, len(col_b), 8):
                        val = str(col_b[i]).strip()
                        if val and val not in ["", "Registro"]:
                            reg_map[val] = (i + 1) - 5

                    f_disp = len(col_b) + 1
                    for i, (idx, row) in enumerate(df_seleccionados.iterrows()):
                        reg_id = str(row.iloc[3]).strip()
                        try:
                            dia = int(str(row.iloc[0]).split('/')[0])
                            col_tachado = dia + 3
                        except: col_tachado = 4
                        
                        status.text(f"Procesando: {row.iloc[4]}")

                        if reg_id in reg_map:
                            actualizar_bloque_paciente(h_his, reg_map[reg_id], row, col_tachado)
                        else:
                            ss_sal.batch_update({"requests": [{"copyPaste": {
                                "source": {"sheetId": h_pla.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                                "destination": {"sheetId": h_his.id, "startRowIndex": f_disp - 1, "endRowIndex": f_disp + 7, "startColumnIndex": 0, "endColumnIndex": 35},
                                "pasteType": "PASTE_NORMAL"
                            }}]})
                            actualizar_bloque_paciente(h_his, f_disp, row, col_tachado)
                            f_disp += 8
                        time.sleep(2.5) 
                    st.success("✅ Sincronización terminada.")
