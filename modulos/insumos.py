import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter

# --- CONFIGURACIÓN ---
SHEET_URL_AISLAMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

SERVICIOS_INSUMOS_FILTRO = [
    "HEMATOLOGIA", "HEMATOLOGIA PEDIATRICA", "ONCOLOGIA PEDIATRICA",
    "NEONATOLOGIA", "INFECTOLOGIA PEDIATRICA", "U.C.I.N.",
    "U.T.I.P.", "TERAPIA POSQUIRURGICA", "UNIDAD DE QUEMADOS",
    "ONCOLOGIA MEDICA", "UCIA"
]

# --- FUNCIONES DE PROCESAMIENTO ---

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

def cargar_aislamientos_limpios():
    """Lógica de escaneo y consolidación de la tabla de Google Sheets"""
    try:
        df_ais = pd.read_csv(SHEET_URL_AISLAMIENTOS, skiprows=1, engine='python')
        df_ais.columns = [str(c).strip().upper() for c in df_ais.columns]
        
        # Columnas necesarias: B(CAMA), C(REGISTRO), D(NOMBRE), E(TIPO AISLAMIENTO), H(FECHA TÉRMINO)
        cols = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE TÉRMINO"]
        df_ais = df_ais[[c for c in cols if c in df_ais.columns]]
        
        # Limpiar vacíos y filtrar por Fecha de Término (Solo Activos)
        df_ais = df_ais.replace(['nan', 'None', 'none', 'NAN', ' '], pd.NA)
        df_ais = df_ais[df_ais["FECHA DE TÉRMINO"].isna()]
        
        # Consolidar filas dobles: Rellenar Camas/Nombres y unir Tipos de Aislamiento
        df_ais["CAMA"] = df_ais["CAMA"].ffill()
        df_ais["NOMBRE"] = df_ais["NOMBRE"].ffill()
        df_ais["TIPO DE AISLAMIENTO"] = df_ais.groupby(["CAMA", "NOMBRE"])["TIPO DE AISLAMIENTO"].transform(
            lambda x: " / ".join(x.dropna().astype(str).unique())
        )
        
        # Eliminar duplicados quedándonos con la fila que tenga más datos
        df_ais['data_count'] = df_ais.notna().sum(axis=1)
        df_ais = df_ais.sort_values('data_count', ascending=False).drop_duplicates(["CAMA", "NOMBRE"]).drop(columns=['data_count'])
        
        return df_ais.dropna(subset=["REGISTRO"])
    except:
        return pd.DataFrame()

# --- INTERFAZ PRINCIPAL ---
st.title("📦 Censo de Insumos (Mapeo y Empalme)")

if 'archivo_compartido' not in st.session_state:
    st.info("👈 Sube el archivo HTML en 'Configuración' para iniciar el mapeo.")
else:
    try:
        # 1. ESCANEAR HTML PARA MAPEO DEMOGRÁFICO
        tablas = pd.read_html(st.session_state['archivo_compartido'])
        df_html_raw = max(tablas, key=len)
        col0_str = df_html_raw.iloc[:, 0].fillna("").astype(str).str.upper()
        
        datos_html = []
        pacs_11_esp = []
        esp_actual = ""
        IGNORAR = ["PACIENTES", "TOTAL", "SUBTOTAL", "PÁGINA", "IMPRESIÓN", "1111"]

        for i, val in enumerate(col0_str):
            if "ESPECIALIDAD:" in val:
                esp_actual = val
                continue
            fila = [str(x).strip() for x in df_html_raw.iloc[i].values]
            if any(x in fila[0] for x in IGNORAR): continue
            
            if len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
                esp_real = obtener_especialidad_real(fila[0], esp_actual)
                pac_data = {
                    "CAMA_HTML": fila[0], "REGISTRO": fila[1], "PACIENTE": fila[2],
                    "SEXO": fila[3], "EDAD": "".join(re.findall(r'\d+', fila[4])),
                    "FECHA DE INGRESO": fila[9], "ESP_REAL": esp_real
                }
                datos_html.append(pac_data)
                if esp_real in SERVICIOS_INSUMOS_FILTRO:
                    pacs_11_esp.append(pac_data)

        df_mapeo_html = pd.DataFrame(datos_html)

        # 2. EMPALME DE ESPECIALIDADES OBLIGATORIAS
        st.subheader("📋 Insumos: Especialidades Obligadas")
        if pacs_11_esp:
            df_11 = pd.DataFrame(pacs_11_esp)
            for serv in sorted(df_11["ESP_REAL"].unique()):
                with st.expander(f"🔍 {serv}"):
                    df_v = df_11[df_11["ESP_REAL"] == serv].copy()
                    df_v["TIPO DE PRECAUCIONES"] = "ESTÁNDAR"
                    df_v["INSUMO"] = "JABÓN/SANITAS"
                    st.table(df_v[["CAMA_HTML", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]])

        # 3. EMPALME DE AISLAMIENTOS (Mapeo Inteligente)
        st.subheader("🦠 Insumos: Aislamientos")
        df_ais_base = cargar_aislamientos_limpios()
        
        if not df_ais_base.empty:
            # Empalmamos la tabla de aislamientos con el mapeo del HTML usando el REGISTRO
            df_ais_final = pd.merge(df_ais_base, df_mapeo_html, on="REGISTRO", how="left")
            
            # Si el paciente no está en el HTML, preservamos los datos originales del Sheets
            df_ais_final["CAMA_INSUMO"] = df_ais_final["CAMA_HTML"].fillna(df_ais_final["CAMA"])
            df_ais_final["PACIENTE_FINAL"] = df_ais_final["PACIENTE"].fillna(df_ais_final["NOMBRE"])
            df_ais_final["TIPO DE PRECAUCIONES"] = df_ais_final["TIPO DE AISLAMIENTO"]
            df_ais_final["INSUMO"] = "JABÓN/SANITAS"
            
            # Limpiar textos de celdas no encontradas
            for c in ["SEXO", "EDAD", "FECHA DE INGRESO"]:
                df_ais_final[c] = df_ais_final[c].fillna("Pendiente")

            cols_final = ["CAMA_INSUMO", "REGISTRO", "PACIENTE_FINAL", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
            
            with st.expander("👁️ Ver Aislamientos Empalmados", expanded=True):
                st.table(df_ais_final[cols_final])

            # --- GENERAR EXCEL ---
            if st.button("🚀 GENERAR EXCEL TOTAL", use_container_width=True, type="primary"):
                hoy = datetime.now()
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Hoja de Aislamientos
                    df_excel_ais = df_ais_final[cols_final].copy()
                    df_excel_ais.columns = ["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
                    df_excel_ais.to_excel(writer, index=False, sheet_name="AISLAMIENTOS", startrow=1)
                    
                    # Hojas de Especialidades
                    for serv in sorted(df_11["ESP_REAL"].unique()):
                        df_s = df_11[df_11["ESP_REAL"] == serv][["CAMA_HTML", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "ESP_REAL"]]
                        df_s.columns = ["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES"]
                        df_s["INSUMO"] = "JABÓN/SANITAS"
                        df_s.to_excel(writer, index=False, sheet_name=serv[:30].replace("/", "-"), startrow=1)

                st.success("✅ Reporte consolidado con éxito.")
                st.download_button("💾 DESCARGAR", output.getvalue(), f"Reporte_Insumos_{hoy.strftime('%d%m%Y')}.xlsx", use_container_width=True)

    except Exception as e:
        st.error(f"Error en el proceso de empalme: {e}")
