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

# --- 2. FUNCIÓN DE MAPEO CORREGIDA ---
def actualizar_hoja_paciente(h_nueva, fila_datos):
    try:
        # 1. Lógica de Fecha (Columna 0 del Censo)
        fecha_str = str(fila_datos.iloc[0])
        dia = int(fecha_str.split('/')[0])
        col_dia = dia + 2  # C9...

        # 2. Lógica de Sexo (Búsqueda robusta)
        # Intentamos obtener el valor por nombre de columna 'SEXO'
        # Si falla, usamos el índice 5 (Columna F)
        try:
            sexo_raw = str(fila_datos['SEXO']).strip().upper()
        except:
            sexo_raw = str(fila_datos.iloc[5]).strip().upper()

        col_sexo = None
        if sexo_raw == 'M':
            col_sexo = 23  # Columna W
        elif sexo_raw == 'F':
            col_sexo = 25  # Columna Y

        # 3. Lista de celdas a actualizar
        lista_celdas = [
            gspread.Cell(row=3, col=2, value=str(fila_datos.iloc[4])),  # B3: Nombre
            gspread.Cell(row=3, col=15, value=str(fila_datos.iloc[3])), # O3: Expediente
            gspread.Cell(row=3, col=29, value=str(fila_datos.iloc[2])), # AC3: Edad
            gspread.Cell(row=4, col=3, value=str(fila_datos.iloc[6])),  # C4: Servicio
            gspread.Cell(row=5, col=27, value=str(fila_datos.iloc[1])), # AA5: Sexo Texto
            gspread.Cell(row=6, col=2, value=str(fila_datos.iloc[8])),  # B6: Dx
            gspread.Cell(row=9, col=col_dia, value="X")                 # Día del mes
        ]

        # 4. Insertar la X de sexo solo si se detectó M o F
        if col_sexo:
            lista_celdas.append(gspread.Cell(row=5, col=col_sexo, value="X"))
        else:
            # Mensaje de depuración en caso de que falle
            st.warning(f"⚠️ No se reconoció el sexo para {fila_datos.iloc[4]}. Valor leído: '{sexo_raw}'")

        # 5. Envío de datos a Google
        h_nueva.update_cells(lista_celdas, value_input_option='USER_ENTERED')
        
        # 6. Formato: Alineación a la izquierda
        fmt = {"horizontalAlignment": "LEFT"}
        h_nueva.batch_format([
            {"range": "B3:B6", "format": fmt},
            {"range": "O3", "format": fmt},
            {"range": "AC3", "format": fmt},
            {"range": "C4", "format": fmt},
            {"range": "AA5", "format": fmt}
        ])

    except Exception as e:
        st.error(f"Error en el proceso de datos: {e}")

# --- 3. INTERFAZ ---
st.title("🛡️ Vigilancia Activa de Piso")

if st.button("🔍 Cargar Pacientes del Censo"):
    res = conectar_piso_activo()
    if res[0]:
        _, _, h_dat = res
        # Obtenemos registros y limpiamos nombres de columnas (quitar espacios y poner en MAYUS)
        df_raw = pd.DataFrame(h_dat.get_all_records())
        df_raw.columns = [str(col).strip().upper() for col in df_raw.columns]
        
        df_raw.insert(0, "SELECCIONAR", False)
        st.session_state['df_piso_activo'] = df_raw
        st.success("Censo cargado.")

if 'df_piso_activo' in st.session_state:
    df_visual = st.session_state['df_piso_activo']
    
    # Editor de tabla para selección
    df_seleccion = st.data_editor(
        df_visual,
        column_config={
            "SELECCIONAR": st.column_config.CheckboxColumn("¿Procesar?", default=False)
        },
        disabled=[col for col in df_visual.columns if col != "SELECCIONAR"],
        hide_index=True,
        use_container_width=True
    )

    if st.button("🚀 Generar Hojas Individuales", type="primary"):
        elegidos = df_seleccion[df_seleccion["SELECCIONAR"] == True]
        
        if elegidos.empty:
            st.warning("Selecciona al menos un paciente.")
        else:
            res = conectar_piso_activo()
            if res[0]:
                ss_sal, h_pla, _ = res
                prog = st.progress(0)
                status = st.empty()

                for idx, (i, row) in enumerate(elegidos.iterrows()):
                    # Quitamos la columna de control para no mover los índices
                    datos = row.drop("SELECCIONAR")
                    nombre = str(datos.iloc[4])[:20].strip()
                    
                    status.text(f"Creando pestaña: {nombre}")
                    
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
                    time.sleep(3.5) # Pausa obligatoria para evitar bloqueo de Google
                
                st.success("✅ Proceso completado.")
