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
        
        # Origen: Datos Limpios
        ss_origen = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        # Salida: Vigilancia Activa de Piso
        ss_salida = client.open_by_key("1GWFWY1PyfUERC9S0QYvOsugpvrIPQiRS7vyCval9ZTc")
        
        h_datos_limpios = ss_origen.get_worksheet(1) # Hoja 2 del origen
        h_plantilla = ss_salida.get_worksheet(0)     # Hoja 1 (Plantilla Maestra)
            
        return ss_salida, h_plantilla, h_datos_limpios
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None

# --- 2. FUNCIÓN DE MAPEO Y FORMATO ---
def actualizar_hoja_paciente(h_nueva, fila_datos):
    try:
        # Extraer día para la "X"
        fecha_str = str(fila_datos.iloc[0])
        dia = int(fecha_str.split('/')[0])
        col_dia = dia + 2  # Día 1 en Col C(3)

        # Mapeo de celdas según tu esquema
        # Nota: fila_base aquí es 1 porque es una hoja nueva
        lista_celdas = [
            gspread.Cell(row=3, col=2, value=str(fila_datos.iloc[4])),  # B3: Nombre
            gspread.Cell(row=3, col=15, value=str(fila_datos.iloc[3])), # O3: Expediente
            gspread.Cell(row=3, col=29, value=str(fila_datos.iloc[2])), # AC3: Edad
            gspread.Cell(row=4, col=3, value=str(fila_datos.iloc[6])),  # C4: Servicio
            gspread.Cell(row=5, col=27, value=str(fila_datos.iloc[1])), # AA5: Sexo
            gspread.Cell(row=6, col=2, value=str(fila_datos.iloc[8])),  # B6: Dx
            gspread.Cell(row=9, col=col_dia, value="X")                 # C9-AG9: Marca
        ]
        
        # Actualizar valores
        h_nueva.update_cells(lista_celdas, value_input_option='USER_ENTERED')
        
        # Aplicar alineación a la izquierda en las celdas de datos
        # Rangos: B3, O3, AC3, C4, AA5, B6
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
st.title("🛡️ Vigilancia Activa: Multi-Hoja")

if st.button("🔍 Cargar lista de pacientes del Censo"):
    res = conectar_piso_activo()
    if res[0]:
        _, _, h_dat = res
        df_full = pd.DataFrame(h_dat.get_all_records())
        st.session_state['df_piso_disponible'] = df_full
        st.success("Lista cargada.")

if 'df_piso_disponible' in st.session_state:
    df = st.session_state['df_piso_disponible']
    df['display_name'] = df.apply(lambda x: f"{x.iloc[4]} | {x.iloc[3]}", axis=1)
    
    seleccionados = st.multiselect("Selecciona pacientes:", options=df['display_name'].tolist())

    if st.button("🚀 Crear Hojas Individuales", type="primary"):
        if not seleccionados:
            st.warning("Selecciona al menos uno.")
        else:
            res = conectar_piso_activo()
            if res[0]:
                ss_sal, h_pla, h_dat = res
                df_procesar = df[df['display_name'].isin(seleccionados)]
                
                prog = st.progress(0)
                status = st.empty()

                for idx, (i, row) in enumerate(df_procesar.iterrows()):
                    nombre_paciente = str(row.iloc[4])[:20] # Truncar nombre para la pestaña
                    status.text(f"Creando pestaña para: {nombre_paciente}")
                    
                    # 1. Crear nueva hoja duplicando la plantilla
                    try:
                        # Duplicamos la hoja 1 (plantilla) con el nombre del paciente
                        nueva_hoja = ss_sal.duplicate_sheet(
                            source_sheet_id=h_pla.id,
                            new_sheet_name=f"Paciente_{nombre_paciente}_{idx}",
                            insert_sheet_index=idx + 1
                        )
                        
                        # 2. Llenar Datos y dar formato
                        actualizar_hoja_paciente(nueva_hoja, row)
                        
                    except Exception as e:
                        st.error(f"No se pudo crear la hoja para {nombre_paciente}: {e}")
                    
                    prog.progress((idx + 1) / len(df_procesar))
                    time.sleep(3) # Pausa obligatoria (duplicar hojas es pesado para la API)
                
                st.success("✅ Todas las pestañas han sido creadas.")
