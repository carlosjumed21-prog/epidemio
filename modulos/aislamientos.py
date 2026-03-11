import streamlit as st
import pandas as pd
import numpy as np
import time
from io import BytesIO
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# Librerías para Excel y PDF (se mantienen igual)
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table as RLTable, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠", layout="wide")

SHEET_URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
SHEET_URL_EDITABLE = "https://docs.google.com/spreadsheets/d/1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A/edit"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIONES DE FORMATO (Omitidas por brevedad, se mantienen igual que tu original) ---
def aplicar_formato_excel_oficial(writer, sheet_name, df, titulo_reporte):
    ws = writer.sheets[sheet_name]
    # ... (Tu código de formato original)
    pass

def generar_pdf_oficial(df):
    # ... (Tu código de PDF original)
    pass

# --- LÓGICA DE DATOS CORREGIDA PARA CELDAS COMBINADAS ---

@st.cache_data(ttl=2)
def cargar_y_filtrar_datos():
    try:
        url_final = f"{SHEET_URL_ORIGEN}&cachebust={time.time()}"
        df = pd.read_csv(url_final, skiprows=1, engine='python')
        
        # 1. Limpieza inicial de columnas
        df = df.iloc[:, 1:12] # Tomamos un rango amplio para no perder columnas
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # 2. TRATAMIENTO DE CELDAS COMBINADAS (IMPORTANTE)
        # Reemplazamos vacíos de texto por NaN real para que ffill funcione
        df = df.replace(['nan', 'None', '', ' '], np.nan)
        
        # Rellenamos hacia abajo las columnas que suelen estar combinadas
        columnas_a_rellenar = ["CAMA", "REGISTRO", "NOMBRE", "FECHA DE TÉRMINO", "FECHA DE INICIO"]
        for col in columnas_a_rellenar:
            if col in df.columns:
                df[col] = df[col].ffill()

        # 3. FILTRADO DE AISLAMIENTOS VIGENTES
        # Ahora que ffill ya puso la fecha de término en todas las filas del paciente...
        # Filtramos: Solo si la FECHA DE TÉRMINO sigue siendo NaN (Vigente)
        if "FECHA DE TÉRMINO" in df.columns:
            # Eliminamos filas que tengan CUALQUIER dato en fecha de término
            df = df[df["FECHA DE TÉRMINO"].isna()].copy()

        # 4. LIMPIEZA DE FILAS VACÍAS (Basura del Sheets)
        df = df.dropna(subset=["NOMBRE"])

        # 5. CONSOLIDACIÓN DE FILAS (Si un paciente tiene varios tipos de aislamiento)
        def consolidar(group):
            res = group.iloc[0].copy()
            if "TIPO DE AISLAMIENTO" in group.columns:
                tipos = group["TIPO DE AISLAMIENTO"].dropna().unique()
                res["TIPO DE AISLAMIENTO"] = " / ".join(map(str, tipos)) if len(tipos) > 0 else "N/A"
            return res

        if not df.empty:
            df = df.groupby(["CAMA", "NOMBRE"], as_index=False, sort=False).apply(consolidar).reset_index(drop=True)
            
            # Seleccionamos columnas finales
            cols_ok = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE INICIO"]
            df = df[[c for c in cols_ok if c in df.columns]].copy()
            df["INSUMO"] = "JABÓN/SANITAS"
            
            return df
        return pd.DataFrame()

    except Exception as e:
        st.error(f"Error procesando datos: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🦠 Control Epidemiológico de Aislamientos")

df_vigentes = cargar_y_filtrar_datos()

tab1, tab2 = st.tabs(["🔍 Monitor y Sincronización", "📝 Reportes"])

with tab1:
    st.metric("Total Aislamientos Vigentes", len(df_vigentes))
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 1. Actualizar desde Origen", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_btn2:
        if st.button("🚀 2. Sincronizar hacia Hoja de Trabajo", use_container_width=True):
            if not df_vigentes.empty:
                conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_vigentes)
                st.success("¡Datos filtrados enviados correctamente!")
            else:
                st.warning("No hay datos para enviar.")

    st.divider()
    st.subheader("📋 Vista Previa de Aislamientos Vigentes")
    st.dataframe(df_vigentes, use_container_width=True, hide_index=True)

with tab2:
    # (Aquí iría tu código de generación de Excel/PDF usando df_vigentes)
    if not df_vigentes.empty:
        st.success("Datos listos para descargar.")
        # Aquí puedes pegar tus botones de descarga de Excel y PDF
    else:
        st.error("No hay datos vigentes.")
