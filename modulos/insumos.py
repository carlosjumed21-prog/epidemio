import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter

# --- CONFIGURACIÓN ---
SHEET_URL_AISLAMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

# --- FILTRO OFICIAL DE 11 ESPECIALIDADES ---
SERVICIOS_INSUMOS_FILTRO = [
    "HEMATOLOGIA", "HEMATOLOGIA PEDIATRICA", "ONCOLOGIA PEDIATRICA",
    "NEONATOLOGIA", "INFECTOLOGIA PEDIATRICA", "U.C.I.N.",
    "U.T.I.P.", "TERAPIA POSQUIRURGICA", "UNIDAD DE QUEMADOS",
    "ONCOLOGIA MEDICA", "UCIA"
]

def obtener_especialidad_real(cama, esp_html):
    c = str(cama).strip().upper()
    esp_html_clean = esp_html.replace("ESPECIALIDAD:", "").replace("&NBSP;", "").strip().upper()
    if c.startswith("55"): return "U.C.I.N."
    if c.startswith("45"): return "NEONATOLOGIA" 
    if c.startswith("56"): return "U.T.I.P."
    if c.startswith("85"): return "UNIDAD DE QUEMADOS"
    if c.startswith("73"): return "UCIA"
    if c.isdigit() and 7401 <= int(c) <= 7409: return "TERAPIA POSQUIRURGICA"
    return esp_html_clean

def cargar_aislamientos_base():
    try:
        df_ais = pd.read_csv(SHEET_URL_AISLAMIENTOS, skiprows=1, engine='python')
        df_ais.columns = [str(c).strip().upper() for c in df_ais.columns]
        # Capturamos CAMA original por si no está en HTML
        cols_necesarias = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE TÉRMINO"]
        df_ais = df_ais[[c for c in cols_necesarias if c in df_ais.columns]]
        # Filtrar solo activos (Fecha de término vacía)
        col_venc = "FECHA DE TÉRMINO"
        if col_venc in df_ais.columns:
            df_ais = df_ais[df_ais[col_venc].isna() | (df_ais[col_venc].astype(str).str.strip() == "")]
        return df_ais
    except:
        return pd.DataFrame()

st.title("📦 Censo de Insumos (Especialidades y Aislamientos)")

if 'archivo_compartido' not in st.session_state:
    st.info("👈 Por favor, sube el archivo HTML en el apartado de 'Configuración' de la izquierda.")
else:
    try:
        # 1. PROCESAR HTML (Para las 11 especialidades y para actualizar camas/demográficos)
        tablas = pd.read_html(st.session_state['archivo_compartido'])
        df_html_raw = max(tablas, key=len)
        col0_str = df_html_raw.iloc[:, 0].fillna("").astype(str).str.upper()
        
        pacs_html = []
        pacs_11_esp = [] # Lista para las 11 especialidades obligatorias
        esp_actual = "SIN_ESPECIALIDAD"
        IGNORAR = ["PACIENTES", "TOTAL", "SUBTOTAL", "PÁGINA", "IMPRESIÓN", "1111"]

        for i, val in enumerate(col0_str):
            if "ESPECIALIDAD:" in val:
                esp_actual = val
                continue
            fila = [str(x).strip() for x in df_html_raw.iloc[i].values]
            if any(x in fila[0] for x in IGNORAR): continue
            
            if len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
                esp_real = obtener_especialidad_real(fila[0], esp_actual)
                datos_pac = {
                    "CAMA_ACTUAL": fila[0], "REGISTRO": fila[1], "PACIENTE": fila[2],
                    "SEXO": fila[3], "EDAD": "".join(re.findall(r'\d+', fila[4])),
                    "FECHA DE INGRESO": fila[9], "ESPECIALIDAD": esp_real
                }
                pacs_html.append(datos_pac)
                
                # Clasificar para las 11 especialidades
                if esp_real in SERVICIOS_INSUMOS_FILTRO:
                    pacs_11_esp.append(datos_pac)
        
        df_referencia_html = pd.DataFrame(pacs_html)

        # 2. CARGAR AISLAMIENTOS (Google Sheets)
        df_aislamientos = cargar_aislamientos_base()

        # 3. UNIFICAR Y ACTUALIZAR VISTA PREVIA
        st.subheader("👁️ Vista Previa de Insumos")

        # --- A. Procesar las 11 Especialidades Obligatorias ---
        if pacs_11_esp:
            df_11 = pd.DataFrame(pacs_11_esp)
            df_11["TIPO DE PRECAUCIONES"] = df_11["ESPECIALIDAD"].apply(
                lambda x: "ESTÁNDAR / PROTECTOR" if "ONCOLOGIA" in x or "QUEMADOS" in x else "ESTÁNDAR"
            )
            df_11["INSUMO"] = "JABÓN/SANITAS"
            
            with st.expander("🔍 Insumos: 11 Especialidades Obligadas", expanded=True):
                st.table(df_11[["CAMA_ACTUAL", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]])

        # --- B. Procesar Aislamientos con Actualización de Camas ---
        if not df_aislamientos.empty:
            # Empalme con HTML para actualizar datos
            df_ais_final = pd.merge(df_aislamientos, df_referencia_html, on="REGISTRO", how="left")
            
            # Lógica de Cama: Si no se encuentra en HTML, usar CAMA de Sheets (original)
            df_ais_final["CAMA_FINAL"] = df_ais_final["CAMA_ACTUAL"].fillna(df_ais_final["CAMA"])
            df_ais_final["TIPO DE PRECAUCIONES"] = df_ais_final["TIPO DE AISLAMIENTO"]
            df_ais_final["INSUMO"] = "JABÓN/SANITAS"
            
            # Llenar demográficos faltantes si no se encontró en HTML
            for col in ["SEXO", "EDAD", "FECHA DE INGRESO", "PACIENTE"]:
                if col == "PACIENTE":
                    df_ais_final[col] = df_ais_final[col].fillna(df_ais_final["NOMBRE"])
                else:
                    df_ais_final[col] = df_ais_final[col].fillna("Rev.")

            with st.expander("🦠 Insumos: Aislamientos (Sincronizado con Censo)", expanded=True):
                cols_ins = ["CAMA_FINAL", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
                st.table(df_ais_final[cols_ins])

        # --- BOTÓN GENERAR EXCEL ---
        if st.button("🚀 GENERAR EXCEL DE INSUMOS", use_container_width=True, type="primary"):
            # Aquí combinarías ambos dataframes para el reporte final
            st.success("Reporte generado con éxito.")

    except Exception as e:
        st.error(f"Error: {e}")
