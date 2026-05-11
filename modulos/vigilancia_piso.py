import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONEXIÓN ---
def conectar_piso_activo():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        ss_origen = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        ss_salida = client.open_by_key("1GWFWY1PyfUERC9S0QYvOsugpvrIPQiRS7vyCval9ZTc")
        
        h_datos_limpios = ss_origen.get_worksheet(1) 
        h_plantilla = ss_salida.get_worksheet(0)     
            
        return ss_salida, h_plantilla, h_datos_limpios
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None

# --- 2. FUNCIÓN DE LIMPIEZA ---
def limpiar_hojas_salida(ss_salida):
    try:
        todas_las_hojas = ss_salida.worksheets()
        # Borramos desde la segunda hoja (índice 1) en adelante
        for i in range(1, len(todas_las_hojas)):
            ss_salida.del_worksheet(todas_las_hojas[1]) # Siempre borramos la que queda en pos 1
        return True
    except Exception as e:
        st.error(f"Error al limpiar: {e}")
        return False

# --- 3. FUNCIÓN DE MAPEO ---
def actualizar_hoja_paciente(h_nueva, fila_datos):
    try:
        fecha_str = str(fila_datos.iloc[0])
        dia = int(fecha_str.split('/')[0])
        col_dia = dia + 2  

        sexo_raw = str(fila_datos.iloc[5]).strip().upper()
        col_sexo = 23 if sexo_raw == 'M' else (25 if sexo_raw == 'F' else None)

        lista_celdas = [
            gspread.Cell(row=3, col=2, value=str(fila_datos.iloc[4])),  # B3: Nombre
            gspread.Cell(row=3, col=15, value=str(fila_datos.iloc[3])), # O3: Expediente
            gspread.Cell(row=3, col=29, value=str(fila_datos.iloc[2])), # AC3: Edad
            gspread.Cell(row=4, col=3, value=str(fila_datos.iloc[6])),  # C4: Servicio
            gspread.Cell(row=5, col=27, value=str(fila_datos.iloc[1])), # AA5: Sexo
            gspread.Cell(row=6, col=2, value=str(fila_datos.iloc[8])),  # B6: Dx
            gspread.Cell(row=6, col=19, value=str(fila_datos.iloc[7])), # S6: Columna H
            gspread.Cell(row=9, col=col_dia, value="X")                  
        ]

        if col_sexo:
            lista_celdas.append(gspread.Cell(row=3, col=col_sexo, value="X"))

        h_nueva.update_cells(lista_celdas, value_input_option='USER_ENTERED')
        
        # Formatos básicos
        h_nueva.batch_format([
            {"range": "B3:AC6", "format": {"horizontalAlignment": "LEFT"}},
            {"range": "W3:Y3", "format": {"horizontalAlignment": "CENTER", "textFormat": {"bold": True}}},
            {"range": "C9:AG9", "format": {"horizontalAlignment": "CENTER", "textFormat": {"bold": True}}}
        ])
    except Exception as e:
        st.error(f"Error en el mapeo de datos: {e}")

# --- 4. INTERFAZ ---
st.set_page_config(page_title="Vigilancia Epidemiológica", layout="wide")
st.title("🛡️ Vigilancia Activa de Piso")

# CARGA DE DATOS
if st.button("🔍 Cargar Censo"):
    res = conectar_piso_activo()
    if res[0]:
        _, _, h_dat = res
        df = pd.DataFrame(h_dat.get_all_records())
        df.columns = [str(c).strip().upper() for c in df.columns]
        df.insert(0, "SELECCIONAR", False)
        st.session_state['df_piso_final'] = df

if 'df_piso_final' in st.session_state:
    # --- Casilla Seleccionar Todos ---
    sel_all = st.checkbox("Seleccionar todos los pacientes")
    if sel_all:
        st.session_state['df_piso_final']["SELECCIONAR"] = True
    
    df_sel = st.data_editor(
        st.session_state['df_piso_final'],
        column_config={"SELECCIONAR": st.column_config.CheckboxColumn("¿Crear?", default=False)},
        disabled=[c for c in st.session_state['df_piso_final'].columns if c != "SELECCIONAR"],
        hide_index=True,
        use_container_width=True,
        key="editor_censo"
    )

    if st.button("🚀 Generar Hojas Individuales", type="primary"):
        elegidos = df_sel[df_sel["SELECCIONAR"] == True]
        if not elegidos.empty:
            ss_sal, h_pla, _ = conectar_piso_activo()
            if ss_sal and h_pla:
                prog = st.progress(0)
                for idx, (i, row) in enumerate(elegidos.iterrows()):
                    datos = row.drop("SELECCIONAR")
                    nombre_pac = str(datos.iloc[4])[:15].strip()
                    try:
                        # FIX: Forzamos int() en h_pla.id para evitar el TypeError
                        nueva = ss_sal.duplicate_sheet(
                            source_sheet_id=int(h_pla.id), 
                            new_sheet_name=f"Vig_{nombre_pac}_{idx+1}", 
                            insert_sheet_index=idx + 1
                        )
                        actualizar_hoja_paciente(nueva, datos)
                    except Exception as e:
                        st.error(f"No se pudo crear la hoja de {nombre_pac}: {e}")
                    
                    prog.progress((idx + 1) / len(elegidos))
                    time.sleep(2) # Pausa mínima para no saturar la API
                st.success("✅ Proceso finalizado.")

# --- SECCIÓN DE LIMPIEZA SIMPLE ---
st.divider()
st.subheader("🧹 Mantenimiento")

if 'modo_limpieza' not in st.session_state:
    st.session_state['modo_limpieza'] = False

if not st.session_state['modo_limpieza']:
    if st.button("Limpiar Hojas"):
        st.session_state['modo_limpieza'] = True
        st.rerun()
else:
    st.warning("⚠️ ¿Confirmas que deseas borrar todas las pestañas de pacientes?")
    c1, c2, _ = st.columns([1, 1, 8])
    if c1.button("SÍ"):
        ss_sal, _, _ = conectar_piso_activo()
        if ss_sal and limpiar_hojas_salida(ss_sal):
            st.success("Hojas eliminadas.")
            st.session_state['modo_limpieza'] = False
            time.sleep(1)
            st.rerun()
    if c2.button("NO"):
        st.session_state['modo_limpieza'] = False
        st.rerun()
