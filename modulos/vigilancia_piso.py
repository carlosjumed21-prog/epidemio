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

# --- 2. FUNCIÓN DE MAPEO POR NOMBRE DE COLUMNA ---
def actualizar_hoja_paciente(h_nueva, fila_datos):
    """
    Usa los nombres de las columnas del Censo para evitar errores de índice.
    """
    try:
        # 1. Identificar Día (Columna 'FECHA' o posición 0)
        # Asumimos que la fecha está en la primera columna disponible
        fecha_val = str(fila_datos.iloc[0])
        dia = int(fecha_val.split('/')[0])
        col_dia = dia + 2  

        # 2. Lógica de Sexo (Buscamos la etiqueta 'SEXO')
        # Si no encuentra 'SEXO', intentamos con el índice 5 (Col F)
        try:
            sexo_val = str(fila_datos['SEXO']).strip().upper()
        except:
            sexo_val = str(fila_datos.iloc[5]).strip().upper()

        col_sexo = None
        if sexo_val == 'M':
            col_sexo = 23  # W
        elif sexo_val == 'F':
            col_sexo = 25  # Y

        # 3. Preparar celdas (Mapeo basado en tus requerimientos)
        # Ajustamos los índices basándonos en tu descripción previa
        lista_celdas = [
            gspread.Cell(row=3, col=2, value=str(fila_datos.iloc[4])),  # B3: NOMBRE
            gspread.Cell(row=3, col=15, value=str(fila_datos.iloc[3])), # O3: EXPEDIENTE
            gspread.Cell(row=3, col=29, value=str(fila_datos.iloc[2])), # AC3: EDAD
            gspread.Cell(row=4, col=3, value=str(fila_datos.iloc[6])),  # C4: SERVICIO/CAMA
            gspread.Cell(row=5, col=27, value=str(fila_datos.iloc[1])), # AA5: SEXO TEXTO
            gspread.Cell(row=6, col=2, value=str(fila_datos.iloc[8])),  # B6: DX
            gspread.Cell(row=9, col=col_dia, value="X")                 # CALENDARIO
        ]

        # 4. Agregar la marca de sexo con "X"
        if col_sexo:
            lista_celdas.append(gspread.Cell(row=5, col=col_sexo, value="X"))
        else:
            # Mensaje de ayuda si sigue fallando la detección
            st.warning(f"⚠️ Valor de sexo no reconocido: '{sexo_val}'")

        # 5. Escribir y dar formato
        h_nueva.update_cells(lista_celdas, value_input_option='USER_ENTERED')
        
        fmt_left = {"horizontalAlignment": "LEFT"}
        h_nueva.batch_format([
            {"range": "B3:B6", "format": fmt_left},
            {"range": "O3", "format": fmt_left},
            {"range": "AC3", "format": fmt_left},
            {"range": "C4", "format": fmt_left},
            {"range": "AA5", "format": fmt_left}
        ])

    except Exception as e:
        st.error(f"❌ Error en el mapeo: {e}")

# --- 3. INTERFAZ ---
st.title("🏥 Vigilancia Activa")

if st.button("🔍 1. CARGAR CENSO"):
    res = conectar_piso_activo()
    if res[0]:
        _, _, h_dat = res
        df = pd.DataFrame(h_dat.get_all_records())
        # Limpieza de nombres de columnas para evitar espacios invisibles
        df.columns = [str(c).strip().upper() for c in df.columns]
        df.insert(0, "SELECCIONAR", False)
        st.session_state['df_piso'] = df
        st.success("Censo cargado.")

if 'df_piso' in st.session_state:
    df_visual = st.session_state['df_piso']
    
    st.info("Selecciona los pacientes y presiona el botón inferior.")
    
    df_sel = st.data_editor(
        df_visual,
        column_config={"SELECCIONAR": st.column_config.CheckboxColumn("¿CREAR?", default=False)},
        disabled=[c for c in df_visual.columns if c != "SELECCIONAR"],
        hide_index=True,
        use_container_width=True
    )

    if st.button("🚀 2. GENERAR PESTAÑAS", type="primary"):
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
                    # Limpiar fila
                    paciente = row.drop("SELECCIONAR")
                    nombre = str(paciente.iloc[4])[:20]
                    
                    status.text(f"Procesando: {nombre}")
                    
                    try:
                        nueva = ss_sal.duplicate_sheet(
                            source_sheet_id=h_pla.id,
                            new_sheet_name=f"VIG_{nombre}_{idx+1}",
                            insert_sheet_index=idx + 1
                        )
                        actualizar_hoja_paciente(nueva, paciente)
                    except Exception as e:
                        st.error(f"Fallo en {nombre}: {e}")
                    
                    prog.progress((idx + 1) / len(elegidos))
                    time.sleep(3.5) # Pausa crítica para la API
                
                st.success("✅ ¡Hecho!")
