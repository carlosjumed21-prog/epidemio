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
        
        h_datos_limpios = ss_origen.get_worksheet(1) # Hoja 2 del origen
        h_plantilla = ss_salida.get_worksheet(0)     # Hoja 1 (Plantilla Maestra)
            
        return ss_salida, h_plantilla, h_datos_limpios
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None

# --- 2. FUNCIÓN DE MAPEO, SEXO Y FORMATO ---
def actualizar_hoja_paciente(h_nueva, fila_datos):
    try:
        # Fecha y Día (Columna A = iloc[0])
        fecha_str = str(fila_datos.iloc[0])
        dia = int(fecha_str.split('/')[0])
        col_dia = dia + 2  

        # --- LÓGICA DE SEXO (Columna 6 / F / iloc[5]) ---
        sexo_val = str(fila_datos.iloc[5]).strip().upper()
        col_sexo = None
        if sexo_val == 'M':
            col_sexo = 23  # Celda W
        elif sexo_val == 'F':
            col_sexo = 25  # Celda Y

        # Preparar lista de celdas
        lista_celdas = [
            gspread.Cell(row=3, col=2, value=str(fila_datos.iloc[4])),  # B3: Nombre
            gspread.Cell(row=3, col=15, value=str(fila_datos.iloc[3])), # O3: Expediente
            gspread.Cell(row=3, col=29, value=str(fila_datos.iloc[2])), # AC3: Edad
            gspread.Cell(row=4, col=3, value=str(fila_datos.iloc[6])),  # C4: Servicio
            gspread.Cell(row=5, col=27, value=str(fila_datos.iloc[1])), # AA5: Sexo (Texto)
            gspread.Cell(row=6, col=2, value=str(fila_datos.iloc[8])),  # B6: Dx
            gspread.Cell(row=9, col=col_dia, value="X")                 # Calendario
        ]

        # Agregar la X de sexo si se identificó M o F
        if col_sexo:
            lista_celdas.append(gspread.Cell(row=5, col=col_sexo, value="X"))

        # Actualización masiva de valores
        h_nueva.update_cells(lista_celdas, value_input_option='USER_ENTERED')
        
        # Formato: Alineación a la IZQUIERDA
        fmt_left = {"horizontalAlignment": "LEFT"}
        h_nueva.batch_format([
            {"range": "B3", "format": fmt_left},
            {"range": "O3", "format": fmt_left},
            {"range": "AC3", "format": fmt_left},
            {"range": "C4", "format": fmt_left},
            {"range": "AA5", "format": fmt_left},
            {"range": "B6", "format": fmt_left}
        ])

    except Exception as e:
        st.error(f"Error en el mapeo: {e}")

# --- 3. INTERFAZ ---
st.title("🛡️ Vigilancia Activa: Selección por Tabla")

if st.button("🔍 Cargar pacientes del Censo"):
    res = conectar_piso_activo()
    if res[0]:
        _, _, h_dat = res
        df_full = pd.DataFrame(h_dat.get_all_records())
        df_full.insert(0, "Seleccionar", False)
        st.session_state['df_piso_tabla'] = df_full
        st.success("Censo cargado.")

if 'df_piso_tabla' in st.session_state:
    st.subheader("Selecciona los pacientes a procesar")
    
    df_visual = st.session_state['df_piso_tabla']
    df_seleccion = st.data_editor(
        df_visual,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("¿Crear?", default=False)
        },
        disabled=[col for col in df_visual.columns if col != "Seleccionar"],
        hide_index=True,
        use_container_width=True
    )

    if st.button("🚀 Generar Hojas Individuales", type="primary"):
        pacientes_elegidos = df_seleccion[df_seleccion["Seleccionar"] == True]
        
        if pacientes_elegidos.empty:
            st.warning("⚠️ No has seleccionado ningún paciente.")
        else:
            res = conectar_piso_activo()
            if res[0]:
                ss_sal, h_pla, _ = res
                prog = st.progress(0)
                status = st.empty()

                for idx, (original_idx, row) in enumerate(pacientes_elegidos.iterrows()):
                    datos_paciente = row.drop("Seleccionar")
                    nombre = str(datos_paciente.iloc[4])[:20].strip()
                    
                    status.text(f"Creando pestaña {idx+1}/{len(pacientes_elegidos)}: {nombre}")
                    
                    try:
                        # Duplicamos la plantilla en una hoja nueva
                        nueva_hoja = ss_sal.duplicate_sheet(
                            source_sheet_id=h_pla.id,
                            new_sheet_name=f"Vig_{nombre}_{int(time.time()) % 1000}",
                            insert_sheet_index=idx + 1
                        )
                        actualizar_hoja_paciente(nueva_hoja, datos_paciente)
                    except Exception as e:
                        st.error(f"Error con {nombre}: {e}")
                    
                    prog.progress((idx + 1) / len(pacientes_elegidos))
                    time.sleep(3.5) # Pausa para no saturar la API
                
                st.success("✅ Proceso terminado.")
