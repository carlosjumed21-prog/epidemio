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

# --- 2. FUNCIÓN DE MAPEO Y FORMATO ---
def actualizar_hoja_paciente(h_nueva, fila_datos):
    try:
        fecha_str = str(fila_datos.iloc[0])
        dia = int(fecha_str.split('/')[0])
        col_dia = dia + 2  

        lista_celdas = [
            gspread.Cell(row=3, col=2, value=str(fila_datos.iloc[4])),  # B3: Nombre
            gspread.Cell(row=3, col=15, value=str(fila_datos.iloc[3])), # O3: Expediente
            gspread.Cell(row=3, col=29, value=str(fila_datos.iloc[2])), # AC3: Edad
            gspread.Cell(row=4, col=3, value=str(fila_datos.iloc[6])),  # C4: Servicio
            gspread.Cell(row=5, col=27, value=str(fila_datos.iloc[1])), # AA5: Sexo
            gspread.Cell(row=6, col=2, value=str(fila_datos.iloc[8])),  # B6: Dx
            gspread.Cell(row=9, col=col_dia, value="X")                 
        ]
        
        h_nueva.update_cells(lista_celdas, value_input_option='USER_ENTERED')
        
        # Formato: Alineación a la izquierda
        fmt = {"horizontalAlignment": "LEFT"}
        h_nueva.batch_format([
            {"range": "B3", "format": fmt},
            {"range": "O3", "format": fmt},
            {"range": "AC3", "format": fmt},
            {"range": "C4", "format": fmt},
            {"range": "AA5", "format": fmt},
            {"range": "B6", "format": fmt}
        ])
    except Exception as e:
        st.error(f"Error en mapeo/formato: {e}")

# --- 3. INTERFAZ ---
st.title("🛡️ Vigilancia Activa: Selección por Tabla")

if st.button("🔍 Cargar pacientes del Censo"):
    res = conectar_piso_activo()
    if res[0]:
        _, _, h_dat = res
        data = h_dat.get_all_records()
        df_full = pd.DataFrame(data)
        # Añadimos columna de selección al inicio
        df_full.insert(0, "Seleccionar", False)
        st.session_state['df_piso_tabla'] = df_full
        st.success("Censo cargado correctamente.")

if 'df_piso_tabla' in st.session_state:
    st.subheader("Lista de Pacientes Detectados")
    st.write("Marca la casilla de los pacientes que deseas procesar:")

    # Editor de datos para selección por casilla
    # Mostramos solo columnas relevantes para que no se vea amontonado
    df_visual = st.session_state['df_piso_tabla']
    
    # Configuramos el editor para que solo la columna "Seleccionar" sea editable
    df_seleccion = st.data_editor(
        df_visual,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn(
                "¿Procesar?",
                help="Marca para generar su hoja de vigilancia",
                default=False,
            )
        },
        disabled=[col for col in df_visual.columns if col != "Seleccionar"],
        hide_index=True,
        use_container_width=True
    )

    if st.button("🚀 Generar Hojas para Seleccionados", type="primary"):
        # Filtramos los que el usuario marcó con True
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
                    # Quitamos la columna 'Seleccionar' para no confundir al mapeo iloc original
                    datos_paciente = row.drop("Seleccionar")
                    nombre = str(datos_paciente.iloc[4])[:25]
                    
                    status.text(f"Creando pestaña {idx+1}/{len(pacientes_elegidos)}: {nombre}")
                    
                    try:
                        nueva_hoja = ss_sal.duplicate_sheet(
                            source_sheet_id=h_pla.id,
                            new_sheet_name=f"Vig_{nombre}_{int(time.time()) % 1000}",
                            insert_sheet_index=idx + 1
                        )
                        actualizar_hoja_paciente(nueva_hoja, datos_paciente)
                    except Exception as e:
                        st.error(f"Error con {nombre}: {e}")
                    
                    prog.progress((idx + 1) / len(pacientes_elegidos))
                    time.sleep(3) 
                
                st.success(f"✅ Se generaron {len(pacientes_elegidos)} pestañas nuevas.")
