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
        
        # Archivos de Google Sheets
        ss_origen = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        ss_salida = client.open_by_key("1GWFWY1PyfUERC9S0QYvOsugpvrIPQiRS7vyCval9ZTc")
        
        h_datos_limpios = ss_origen.get_worksheet(1) # Hoja 2 Origen
        h_plantilla = ss_salida.get_worksheet(0)     # Hoja 1 Plantilla
            
        return ss_salida, h_plantilla, h_datos_limpios
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None

# --- 2. FUNCIÓN DE MAPEO CORREGIDA (SEXO EN FILA 3) ---
def actualizar_hoja_paciente(h_nueva, fila_datos):
    try:
        # A. Día para el calendario (Columna A del censo)
        fecha_str = str(fila_datos.iloc[0])
        dia = int(fecha_str.split('/')[0])
        col_dia = dia + 2  # Inicia en Col C (3)

        # B. Lógica de Sexo (Columna 6 del censo -> Etiqueta 'SEXO')
        # Buscamos 'M' para marcar W3 (Col 23) o 'F' para Y3 (Col 25)
        try:
            sexo_raw = str(fila_datos['SEXO']).strip().upper()
        except:
            sexo_raw = str(fila_datos.iloc[5]).strip().upper()

        col_sexo = None
        if sexo_raw == 'M':
            col_sexo = 23  # Celda W3
        elif sexo_raw == 'F':
            col_sexo = 25  # Celda Y3

        # C. Construcción del bloque de celdas
        lista_celdas = [
            gspread.Cell(row=3, col=2, value=str(fila_datos.iloc[4])),  # B3: Nombre
            gspread.Cell(row=3, col=15, value=str(fila_datos.iloc[3])), # O3: Expediente
            gspread.Cell(row=3, col=29, value=str(fila_datos.iloc[2])), # AC3: Edad
            gspread.Cell(row=4, col=3, value=str(fila_datos.iloc[6])),  # C4: Servicio
            gspread.Cell(row=5, col=27, value=str(fila_datos.iloc[1])), # AA5: Sexo Texto
            gspread.Cell(row=6, col=2, value=str(fila_datos.iloc[8])),  # B6: Dx
            gspread.Cell(row=9, col=col_dia, value="X")                 # Calendario
        ]

        # D. Marca de Sexo en FILA 3 (W3 o Y3)
        if col_sexo:
            lista_celdas.append(gspread.Cell(row=3, col=col_sexo, value="X"))
        else:
            st.warning(f"⚠️ Sexo no identificado para {fila_datos.iloc[4]}. Valor: '{sexo_raw}'")

        # E. Envío masivo a Google
        h_nueva.update_cells(lista_celdas, value_input_option='USER_ENTERED')
        
        # F. Formato: Alineación IZQUIERDA en las áreas de datos
        fmt_left = {"horizontalAlignment": "LEFT"}
        h_nueva.batch_format([
            {"range": "B3:AC6", "format": fmt_left}, # Cubre todo el bloque superior
            {"range": "C4", "format": fmt_left},
            {"range": "B6", "format": fmt_left}
        ])

    except Exception as e:
        st.error(f"Error procesando celdas: {e}")

# --- 3. INTERFAZ STREAMLIT ---
st.title("🛡️ Vigilancia Activa: Generador de Hojas")

if st.button("🔍 Cargar Censo de Origen"):
    res = conectar_piso_activo()
    if res[0]:
        _, _, h_dat = res
        df = pd.DataFrame(h_dat.get_all_records())
        # Normalizar nombres de columnas
        df.columns = [str(c).strip().upper() for c in df.columns]
        df.insert(0, "SELECCIONAR", False)
        st.session_state['df_vig_activa'] = df
        st.success("Censo cargado correctamente.")

if 'df_vig_activa' in st.session_state:
    df_visual = st.session_state['df_vig_activa']
    
    st.info("Marca los pacientes que requieren hoja de seguimiento hoy:")
    
    df_sel = st.data_editor(
        df_visual,
        column_config={"SELECCIONAR": st.column_config.CheckboxColumn("¿Crear?", default=False)},
        disabled=[c for c in df_visual.columns if c != "SELECCIONAR"],
        hide_index=True,
        use_container_width=True
    )

    if st.button("🚀 Crear Pestañas en Google Sheets", type="primary"):
        elegidos = df_sel[df_sel["SELECCIONAR"] == True]
        
        if elegidos.empty:
            st.warning("No hay pacientes seleccionados.")
        else:
            res = conectar_piso_activo()
            if res[0]:
                ss_sal, h_pla, _ = res
                prog = st.progress(0)
                status = st.empty()

                for idx, (i, row) in enumerate(elegidos.iterrows()):
                    paciente = row.drop("SELECCIONAR")
                    nombre_tab = str(paciente.iloc[4])[:20].strip()
                    
                    status.text(f"Trabajando en: {nombre_tab}")
                    
                    try:
                        # Duplicar Hoja 1 como nueva pestaña
                        nueva = ss_sal.duplicate_sheet(
                            source_sheet_id=h_pla.id,
                            new_sheet_name=f"Vig_{nombre_tab}_{idx+1}",
                            insert_sheet_index=idx + 1
                        )
                        actualizar_hoja_paciente(nueva, paciente)
                    except Exception as e:
                        st.error(f"Error en {nombre_tab}: {e}")
                    
                    prog.progress((idx + 1) / len(elegidos))
                    time.sleep(3.5) # Pausa anti-bloqueo
                
                st.success("✅ Proceso de generación finalizado.")
