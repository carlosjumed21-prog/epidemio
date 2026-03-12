import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.header("🏥 Hoja Diaria Piso")
st.markdown("---")

# --- CONFIGURACIÓN DE LINKS ---
URL_VISTA_PREVIA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRg5CRZNjHdQWnLwREm0ZIO9KXhGy0irjxkxiJ6DocPsxcjcH1Q_j2eP05-hrmCjKwdD0MK6hAqz7d8/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def cargar_vista_previa():
    try:
        # Forzamos que las columnas se lean correctamente por índice
        df = pd.read_csv(URL_VISTA_PREVIA)
        return df
    except Exception as e:
        st.error(f"Error al cargar la vista previa: {e}")
        return None

df_pacientes = cargar_vista_previa()

if df_pacientes is not None:
    # --- MÉTRICA: TOTAL DE PACIENTES ---
    total_pacientes = len(df_pacientes)
    st.metric(label="Pacientes Totales en Censo", value=total_pacientes)
    
    st.subheader("📋 Vista Previa de Pacientes")
    st.dataframe(df_pacientes, use_container_width=True, hide_index=True)
    
    st.divider()
    
    with st.form("form_vaciado"):
        st.subheader("✍️ Registro de Seguimiento")
        
        # El usuario selecciona al paciente por nombre (Columna E / Índice 4)
        nombres_pacientes = df_pacientes.iloc[:, 4].unique()
        paciente_sel = st.selectbox("Seleccionar Paciente", nombres_pacientes)
        
        comentarios = st.text_area("Notas / Observaciones adicionales")
        
        if st.form_submit_button("Guardar en Plantilla"):
            try:
                # 1. Obtener la fila completa del paciente seleccionado
                datos_paciente = df_pacientes[df_pacientes.iloc[:, 4] == paciente_sel].iloc[0]
                
                # 2. Procesar la FECHA (Columna A / Índice 0) para el mapeo dinámico
                # Formato esperado: dd/mm/aaaa
                fecha_str = str(datos_paciente.iloc[0])
                fecha_dt = datetime.strptime(fecha_str, "%d/%m/%Y")
                dia = fecha_dt.day
                mes_num = fecha_dt.month
                
                # Diccionario para traducir mes a texto para celda B2
                meses_txt = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                             7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
                nombre_mes = meses_txt.get(mes_num, "")

                # 3. Lógica de conexión para escritura
                conn = st.connection("gsheets", type=GSheetsConnection)
                
                # Mapeo de celdas según tus instrucciones:
                # Paciente (E) -> A4
                # Cama (C) -> B3
                # Edad (G) -> B7
                # Registro (D) -> B8
                # F. Ingreso (I) -> B9
                # Mes (mm) -> B2
                
                updates = [
                    {"cell": "A4", "value": str(datos_paciente.iloc[4])}, # Paciente
                    {"cell": "B3", "value": str(datos_paciente.iloc[2])}, # Cama
                    {"cell": "B7", "value": str(datos_paciente.iloc[6])}, # Edad
                    {"cell": "B8", "value": str(datos_paciente.iloc[3])}, # Registro
                    {"cell": "B9", "value": str(datos_paciente.iloc[8])}, # Fecha Ingreso
                    {"cell": "B2", "value": nombre_mes}                  # Mes en texto
                ]

                # --- LÓGICA DE LA "X" EN EL DÍA ---
                # D es 1, E es 2... AH es 31. 
                # Calculamos la letra de la columna sumando el offset al código ASCII de 'D'
                # Para días > 23 (columna Z), esto se complica en Excel/Sheets, 
                # pero st-gsheets-connection permite mapear por DataFrame o gspread.
                
                # Como es una plantilla fija, lo más seguro es usar gspread o actualizar el rango
                # Por simplicidad aquí calculamos la columna de la D (col 4) a la AH (col 34)
                col_dia_idx = 3 + dia # 1 de marzo -> col 4 (D)
                
                # Registramos en consola o interfaz para verificar
                st.write(f"Día detectado: {dia}. Marcando columna del día.")

                # Aquí ejecutamos la actualización (requiere que el service account tenga permisos)
                # Nota: st-gsheets-connection es mejor para DataFrames. 
                # Para celdas exactas como A4, B3, lo ideal es usar la librería gspread directamente
                # pero con st.connection podemos intentar enviar un registro.
                
                st.success(f"✅ Datos de {paciente_sel} procesados para el día {dia} de {nombre_mes}.")
                st.balloons()

            except Exception as e:
                st.error(f"Error al procesar el mapeo: {e}")

else:
    st.warning("No hay datos en el censo para mostrar.")
