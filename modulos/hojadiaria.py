import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

st.header("🏥 Hoja Diaria - Historial con Formato")

# --- 1. CONEXIÓN SEGURA Y DINÁMICA ---
def conectar_google_sheets():
    try:
        # Extraemos las credenciales desde los secrets de Streamlit
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # ID de tu Google Sheet de salida
        ss = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        
        # Obtenemos la primera pestaña (donde está tu plantilla original)
        hoja_plantilla = ss.get_worksheet(0)
        nombre_p_origen = hoja_plantilla.title # Detecta si es 'Hoja 1', 'Sheet1', etc.
        
        # Intentamos obtener la pestaña de Historial, si no existe, la creamos
        try:
            hoja_historial = ss.worksheet("Historial")
        except:
            hoja_historial = ss.add_worksheet(title="Historial", rows="2000", cols="35")
            
        return ss, nombre_p_origen, hoja_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None

# --- 2. LECTURA DEL CENSO DE ORIGEN ---
URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

def cargar_datos_censo():
    try:
        # Cargamos el CSV publicado del censo
        return pd.read_csv(URL_ORIGEN)
    except Exception as e:
        return None

df_pacientes = cargar_datos_censo()

# --- 3. FUNCIÓN DE PROCESAMIENTO (MAPEO Y CLONACIÓN) ---
def procesar_paciente_al_historial(ss, nombre_plantilla, h_historial, fila_datos, index):
    try:
        # Procesamiento de la fecha para la columna de la "X"
        fecha_str = str(fila_datos.iloc[0])
        dt = datetime.strptime(fecha_str, "%d/%m/%Y")
        columna_x = dt.day + 3 # Día 1 = Columna D (4)
        
        # Cálculo de posición: bloques de 8 filas (A3:AI10)
        # Paciente 1 inicia en fila 1, Paciente 2 en fila 9...
        fila_dest = (index * 8) + 1
        rango_dest = f"A{fila_dest}:AI{fila_dest + 7}"
        
        # PASO A: Copiar Plantilla con Formato desde Hoja 1 a Historial
        rango_orig = f"'{nombre_plantilla}'!A3:AI10"
        h_historial.copy_range(rango_orig, rango_dest)

        # PASO B: Llenado de datos usando Batch Update (Una sola petición por paciente)
        # Mapeo según tus instrucciones: B3, B4, A5, B8, B9, B10 del bloque
        batch_data = [
            {'range': f'Historial!B{fila_dest + 0}', 'values': [[str(fila_datos.iloc[1])]]}, # Especialidad
            {'range': f'Historial!B{fila_dest + 1}', 'values': [[str(fila_datos.iloc[2])]]}, # Cama
            {'range': f'Historial!A{fila_dest + 2}', 'values': [[str(fila_datos.iloc[4])]]}, # Paciente
            {'range': f'Historial!B{fila_dest + 5}', 'values': [[str(fila_datos.iloc[6])]]}, # Edad
            {'range': f'Historial!B{fila_dest + 6}', 'values': [[str(fila_datos.iloc[3])]]}, # Registro
            {'range': f'Historial!B{fila_dest + 7}', 'values': [[str(fila_datos.iloc[8])]]}  # F. Ingreso
        ]
        ss.batch_update({'valueInputOption': 'USER_ENTERED', 'data': batch_data})

        # PASO C: Nueva "X" en la fila del día (Fila 4 original -> fila_dest + 1)
        h_historial.update_cell(fila_dest + 1, columna_x, "X")
        
        return True
    except Exception as e:
        if "429" in str(e):
            st.warning(f"⏳ Google limitó la velocidad. Esperando para reintentar con {fila_datos.iloc[4]}...")
            time.sleep(20) # Pausa larga si se agota la cuota
            return False
        st.error(f"Error procesando a {fila_datos.iloc[4]}: {e}")
        return False

# --- 4. INTERFAZ DE USUARIO ---
if df_pacientes is not None:
    # Botón directo para supervisar cambios
    st.link_button("📂 Abrir Hoja de Salida (Kardex)", "https://docs.google.com/spreadsheets/d/116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc/edit")
    
    st.metric("Total de Pacientes en Censo", len(df_pacientes))
    
    with st.expander("🔍 Ver listado de pacientes detectados"):
        st.dataframe(df_pacientes, use_container_width=True, hide_index=True)

    st.divider()

    # Opción de limpieza
    limpiar = st.checkbox("Limpiar pestaña de Historial antes de iniciar vaciado", value=True)

    if st.button("📥 INICIAR VACIADO MASIVO A HISTORIAL", type="primary"):
        ss_obj, nombre_p, h_hist = conectar_google_sheets()
        
        if ss_obj and h_hist:
            if limpiar:
                h_hist.clear()
                st.info(f"Hoja de historial preparada. Usando molde de: {nombre_p}")

            bar_progreso = st.progress(0)
            status_txt = st.empty()
            total_p = len(df_pacientes)
            
            for i, row in df_pacientes.iterrows():
                nombre_actual = row.iloc[4]
                status_txt.text(f"Procesando ({i+1}/{total_p}): {nombre_actual}")
                
                # Intentamos procesar. Si falla por cuota, el bucle espera.
                exito = procesar_paciente_al_historial(ss_obj, nombre_p, h_hist, row, i)
                
                if not exito:
                    # Reintento único tras pausa
                    procesar_paciente_al_historial(ss_obj, nombre_p, h_hist, row, i)
                
                bar_progreso.progress((i + 1) / total_p)
                # Pausa de seguridad vital (8 seg) para copiar formatos sin error 429
                time.sleep(8) 
            
            status_txt.success("✅ ¡Censo procesado exitosamente en la pestaña Historial!")
            st.balloons()
else:
    st.error("No se pudo cargar la vista previa del censo. Revisa la URL pública.")
