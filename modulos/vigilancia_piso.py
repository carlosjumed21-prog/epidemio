import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
def conectar_piso_activo():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Origen: Archivo con los datos limpios (Censo)
        ss_origen = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        # Salida: Archivo de Vigilancia Activa de Piso
        ss_salida = client.open_by_key("1GWFWY1PyfUERC9S0QYvOsugpvrIPQiRS7vyCval9ZTc")
        
        h_datos_limpios = ss_origen.get_worksheet(1) # Hoja 2 del origen
        h_plantilla = ss_salida.get_worksheet(0)     # Hoja 1 (Plantilla Maestra)
            
        return ss_salida, h_plantilla, h_datos_limpios
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None

# --- 2. FUNCIÓN DE MAPEO, SEXO Y FORMATO ---
def actualizar_hoja_paciente(h_nueva, fila_datos):
    """
    Mapeo de datos:
    B3: Nombre (E), O3: Expediente (D), AC3: Edad (C)
    C4: Servicio/Cama (G), AA5: Sexo Texto (B), B6: Dx (I)
    Sexo: M -> W5 (col 23), F -> Y5 (col 25)
    Día: C9-AG9 (según fecha en A)
    """
    try:
        # Extraer día para la "X" en el calendario
        fecha_str = str(fila_datos.iloc[0])
        dia = int(fecha_str.split('/')[0])
        col_dia = dia + 2  # Día 1 cae en Columna C (3)

        # Lógica de Sexo (Columna F en origen es iloc[5])
        sexo_val = str(fila_datos.iloc[5]).strip().upper()
        col_sexo = 23 if sexo_val == 'M' else (25 if sexo_val == 'F' else None)

        # Preparar lista de celdas para actualización masiva
        lista_celdas = [
            gspread.Cell(row=3, col=2, value=str(fila_datos.iloc[4])),  # B3
            gspread.Cell(row=3, col=15, value=str(fila_datos.iloc[3])), # O3
            gspread.Cell(row=3, col=29, value=str(fila_datos.iloc[2])), # AC3
            gspread.Cell(row=4, col=3, value=str(fila_datos.iloc[6])),  # C4
            gspread.Cell(row=5, col=27, value=str(fila_datos.iloc[1])), # AA5
            gspread.Cell(row=6, col=2, value=str(fila_datos.iloc[8])),  # B6
            gspread.Cell(row=9, col=col_dia, value="X")                 # Marca Día
        ]

        # Agregar marca de sexo si aplica
        if col_sexo:
            lista_celdas.append(gspread.Cell(row=5, col=col_sexo, value="X"))

        # Escribir en la hoja
        h_nueva.update_cells(lista_celdas, value_input_option='USER_ENTERED')
        
        # Aplicar alineación a la IZQUIERDA en celdas clave
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
        st.error(f"Error procesando datos del paciente: {e}")

# --- 3. INTERFAZ DE USUARIO (STREAMLIT) ---
st.title("🛡️ Vigilancia Activa: Generador de Pestañas")
st.markdown("Selecciona los pacientes del censo para generar sus hojas individuales de seguimiento.")

# Botón de Carga
if st.button("🔍 Obtener Pacientes del Censo", use_container_width=True):
    res = conectar_piso_activo()
    if res[0]:
        _, _, h_dat = res
        df_full = pd.DataFrame(h_dat.get_all_records())
        # Insertar columna de selección al inicio
        df_full.insert(0, "Seleccionar", False)
        st.session_state['df_piso_activo'] = df_full
        st.success("Censo cargado.")

# Vista Previa y Selección
if 'df_piso_activo' in st.session_state:
    st.subheader("Paso 1: Marcar Pacientes")
    
    # Editor de tabla interactiva
    df_visual = st.session_state['df_piso_activo']
    df_seleccion = st.data_editor(
        df_visual,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("¿Crear?", default=False)
        },
        disabled=[col for col in df_visual.columns if col != "Seleccionar"],
        hide_index=True,
        use_container_width=True
    )

    st.subheader("Paso 2: Ejecutar")
    if st.button("🚀 Generar Hojas en Google Sheets", type="primary", use_container_width=True):
        pacientes_a_procesar = df_seleccion[df_seleccion["Seleccionar"] == True]
        
        if pacientes_a_procesar.empty:
            st.warning("⚠️ No has seleccionado ningún paciente de la lista.")
        else:
            res = conectar_piso_activo()
            if res[0]:
                ss_sal, h_pla, _ = res
                
                prog = st.progress(0)
                status = st.empty()

                for idx, (original_idx, row) in enumerate(pacientes_a_procesar.iterrows()):
                    # Limpiar datos para el mapeo (quitar columna Seleccionar)
                    datos_paciente = row.drop("Seleccionar")
                    nombre_corto = str(datos_paciente.iloc[4])[:20].strip()
                    
                    status.text(f"Generando pestaña {idx+1}/{len(pacientes_a_procesar)}: {nombre_corto}")
                    
                    try:
                        # Duplicar la plantilla (Hoja 1) como una nueva pestaña
                        # El nombre incluye un ID único (timestamp) para evitar duplicados
                        nueva_hoja = ss_sal.duplicate_sheet(
                            source_sheet_id=h_pla.id,
                            new_sheet_name=f"Vig_{nombre_corto}_{int(time.time()) % 1000}",
                            insert_sheet_index=idx + 1
                        )
                        
                        # Inyectar datos y aplicar formato
                        actualizar_hoja_paciente(nueva_hoja, datos_paciente)
                        
                    except Exception as e:
                        st.error(f"Error al crear hoja para {nombre_corto}: {e}")
                    
                    # Progreso y pausa de seguridad para la API
                    prog.progress((idx + 1) / len(pacientes_a_procesar))
                    time.sleep(3.5) 
                
                st.success(f"✅ Proceso terminado. Se crearon {len(pacientes_a_procesar)} pestañas.")
