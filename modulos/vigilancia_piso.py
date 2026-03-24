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

# --- 2. FUNCIÓN DE MAPEO Y FORMATO DETALLADO ---
def actualizar_hoja_paciente(h_nueva, fila_datos):
    try:
        # A. Día para el calendario
        fecha_str = str(fila_datos.iloc[0])
        dia = int(fecha_str.split('/')[0])
        col_dia = dia + 2  

        # B. Lógica de Sexo (M -> W3 / F -> Y3)
        try:
            sexo_raw = str(fila_datos['SEXO']).strip().upper()
        except:
            sexo_raw = str(fila_datos.iloc[5]).strip().upper()

        col_sexo = 23 if sexo_raw == 'M' else (25 if sexo_raw == 'F' else None)

        # C. Lista de celdas (La X va en Mayúscula)
        lista_celdas = [
            gspread.Cell(row=3, col=2, value=str(fila_datos.iloc[4])),  # B3: Nombre
            gspread.Cell(row=3, col=15, value=str(fila_datos.iloc[3])), # O3: Expediente
            gspread.Cell(row=3, col=29, value=str(fila_datos.iloc[2])), # AC3: Edad
            gspread.Cell(row=4, col=3, value=str(fila_datos.iloc[6])),  # C4: Servicio
            gspread.Cell(row=5, col=27, value=str(fila_datos.iloc[1])), # AA5: Sexo Texto
            gspread.Cell(row=6, col=2, value=str(fila_datos.iloc[8])),  # B6: Dx
            gspread.Cell(row=9, col=col_dia, value="X")                 # Calendario
        ]

        if col_sexo:
            lista_celdas.append(gspread.Cell(row=3, col=col_sexo, value="X"))

        # D. Ejecutar actualización de valores
        h_nueva.update_cells(lista_celdas, value_input_option='USER_ENTERED')
        
        # E. APLICAR FORMATOS ESPECÍFICOS (Negrita, Centrado, Mayúscula)
        fmt_datos = {"horizontalAlignment": "LEFT"}
        fmt_marca_x = {
            "horizontalAlignment": "CENTER",
            "textFormat": {"bold": True}
        }

        # Formateo por lotes (Batch Format)
        formateos = [
            {"range": "B3:AC6", "format": fmt_datos},    # Datos generales a la izquierda
            {"range": "W3", "format": fmt_marca_x},      # X de Masculino (Si existe)
            {"range": "Y3", "format": fmt_marca_x},      # X de Femenino (Si existe)
            {"range": "C9:AG9", "format": fmt_marca_x}   # X del calendario
        ]
        
        h_nueva.batch_format(formateos)

    except Exception as e:
        st.error(f"Error en el mapeo: {e}")

# --- 3. INTERFAZ ---
st.title("🛡️ Vigilancia Activa de Piso")

if st.button("🔍 Cargar Censo"):
    res = conectar_piso_activo()
    if res[0]:
        _, _, h_dat = res
        df = pd.DataFrame(h_dat.get_all_records())
        df.columns = [str(c).strip().upper() for c in df.columns]
        df.insert(0, "SELECCIONAR", False)
        st.session_state['df_piso_final'] = df
        st.success("Censo cargado.")

if 'df_piso_final' in st.session_state:
    df_visual = st.session_state['df_piso_final']
    
    df_sel = st.data_editor(
        df_visual,
        column_config={"SELECCIONAR": st.column_config.CheckboxColumn("¿Crear?", default=False)},
        disabled=[c for c in df_visual.columns if c != "SELECCIONAR"],
        hide_index=True,
        use_container_width=True
    )

    if st.button("🚀 Generar Hojas Individuales", type="primary"):
        elegidos = df_sel[df_sel["SELECCIONAR"] == True]
        
        if not elegidos.empty:
            res = conectar_piso_activo()
            if res[0]:
                ss_sal, h_pla, _ = res
                prog = st.progress(0)
                status = st.empty()

                for idx, (i, row) in enumerate(elegidos.iterrows()):
                    datos = row.drop("SELECCIONAR")
                    nombre = str(datos.iloc[4])[:20].strip()
                    status.text(f"Creando pestaña para: {nombre}")
                    
                    try:
                        nueva = ss_sal.duplicate_sheet(
                            source_sheet_id=h_pla.id,
                            new_sheet_name=f"Vig_{nombre}_{idx+1}",
                            insert_sheet_index=idx + 1
                        )
                        actualizar_hoja_paciente(nueva, datos)
                    except Exception as e:
                        st.error(f"Error en {nombre}: {e}")
                    
                    prog.progress((idx + 1) / len(elegidos))
                    time.sleep(3.5)
                
                st.success("✅ Proceso finalizado.")
