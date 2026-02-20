import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill

# --- CONFIGURACIÓN ---
SHEET_URL_AISLAMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

SERVICIOS_INSUMOS_FILTRO = [
    "HEMATOLOGIA", "HEMATOLOGIA PEDIATRICA", "ONCOLOGIA PEDIATRICA",
    "NEONATOLOGIA", "INFECTOLOGIA PEDIATRICA", "U.C.I.N.",
    "U.T.I.P.", "TERAPIA POSQUIRURGICA", "UNIDAD DE QUEMADOS",
    "ONCOLOGIA MEDICA", "UCIA"
]

# --- FUNCIONES DE FORMATO EXCEL ---
def aplicar_formato_profesional(writer, sheet_name, df):
    worksheet = writer.sheets[sheet_name]
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    alignment = Alignment(horizontal="center", vertical="center")

    for col_num, value in enumerate(df.columns, 1):
        cell = worksheet.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = alignment
        cell.border = border
        
    for row in worksheet.iter_rows(min_row=2, max_row=len(df)+1, min_col=1, max_col=len(df.columns)):
        for cell in row:
            cell.alignment = alignment
            cell.border = border

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

# --- INTERFAZ ---
st.title("📦 Censo de Insumos")

if 'archivo_compartido' not in st.session_state:
    st.info("👈 Sube el archivo HTML en 'Configuración' para iniciar.")
else:
    try:
        tablas = pd.read_html(st.session_state['archivo_compartido'])
        df_html_raw = max(tablas, key=len)
        col0_str = df_html_raw.iloc[:, 0].fillna("").astype(str).str.upper()
        
        datos_html = []
        pacs_11_esp = []
        esp_actual = ""

        for i, val in enumerate(col0_str):
            if "ESPECIALIDAD:" in val:
                esp_actual = val; continue
            fila = [str(x).strip() for x in df_html_raw.iloc[i].values]
            if len(fila) > 1 and len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
                esp_real = obtener_especialidad_real(fila[0], esp_actual)
                pac_data = {
                    "CAMA": fila[0], "REGISTRO": fila[1], "PACIENTE": fila[2],
                    "SEXO": fila[3], "EDAD": "".join(re.findall(r'\d+', fila[4])),
                    "FECHA DE INGRESO": fila[9], "ESP_REAL": esp_real
                }
                datos_html.append(pac_data)
                if esp_real in SERVICIOS_INSUMOS_FILTRO:
                    pacs_11_esp.append(pac_data)

        df_ref_html = pd.DataFrame(datos_html)

        # --- SECCIÓN A: ESPECIALIDADES ---
        st.header("📋 INSUMOS: ESPECIALIDADES")
        if pacs_11_esp:
            df_11 = pd.DataFrame(pacs_11_esp)
            for serv in sorted(df_11["ESP_REAL"].unique()):
                with st.expander(f"🔍 Vista Previa: {serv}"):
                    df_v = df_11[df_11["ESP_REAL"] == serv].copy()
                    df_v["TIPO DE PRECAUCIONES"] = "ESTÁNDAR"
                    df_v["INSUMO"] = "JABÓN/SANITAS"
                    st.table(df_v[["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]])

        st.markdown("<br><hr><br>", unsafe_allow_html=True)

        # --- SECCIÓN B: AISLAMIENTOS (EDICIÓN Y ACTUALIZACIÓN) ---
        st.header("🦠 INSUMOS: AISLAMIENTOS")
        
        if 'df_maestro_ais' not in st.session_state:
            df_ais_raw = pd.read_csv(SHEET_URL_AISLAMIENTOS, skiprows=1).replace(['nan', ' '], pd.NA)
            df_ais_raw.columns = [str(c).strip().upper() for c in df_ais_raw.columns]
            df_ais_f = pd.merge(df_ais_raw, df_ref_html, on="REGISTRO", how="left", suffixes=('_SHEET', '_HTML'))
            
            df_ais_f["CAMA"] = df_ais_f["CAMA_HTML"].fillna(df_ais_f["CAMA_SHEET"])
            df_ais_f["PACIENTE"] = df_ais_f["PACIENTE"].fillna(df_ais_f["NOMBRE"])
            df_ais_f["TIPO DE PRECAUCIONES"] = df_ais_f["TIPO DE AISLAMIENTO"]
            df_ais_f["INSUMO"] = "JABÓN/SANITAS"
            
            for c in ["SEXO", "EDAD", "FECHA DE INGRESO"]:
                df_ais_f[c] = df_ais_f[c].fillna("Pendiente")
            
            st.session_state.df_maestro_ais = df_ais_f[["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]].dropna(subset=["REGISTRO"])

        # Editor de Pendientes
        mask = st.session_state.df_maestro_ais.astype(str).apply(lambda x: x.str.contains('Pendiente')).any(axis=1)
        df_pendientes = st.session_state.df_maestro_ais[mask]

        if not df_pendientes.empty:
            st.subheader("⚠️ Edición de Datos Faltantes")
            editados = st.data_editor(
                df_pendientes.style.apply(lambda x: ['background-color: #FFF9C4' for _ in x], axis=1),
                use_container_width=True, hide_index=True, key="ed_pend"
            )
            if not editados.equals(df_pendientes):
                st.session_state.df_maestro_ais.update(editados)
                st.rerun()

        st.subheader("📋 Tabla Oficial (Solo Lectura)")
        st.table(st.session_state.df_maestro_ais)

        # --- GENERACIÓN DE EXCEL TOTAL ---
        if st.button("🚀 GENERAR EXCEL TOTAL", use_container_width=True, type="primary"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # 1. Hoja Aislamientos
                df_ais_final = st.session_state.df_maestro_ais
                df_ais_final.to_excel(writer, index=False, sheet_name="AISLAMIENTOS")
                aplicar_formato_profesional(writer, "AISLAMIENTOS", df_ais_final)
                
                # 2. Hojas Especialidades
                if not df_11.empty:
                    for serv in sorted(df_11["ESP_REAL"].unique()):
                        df_s = df_11[df_11["ESP_REAL"] == serv].copy()
                        df_s["TIPO DE PRECAUCIONES"] = "ESTÁNDAR"
                        df_s["INSUMO"] = "JABÓN/SANITAS"
                        nombre_hoja = serv[:30].replace("/", "-")
                        df_s = df_s[["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]]
                        df_s.to_excel(writer, index=False, sheet_name=nombre_hoja)
                        aplicar_formato_profesional(writer, nombre_hoja, df_s)
            
            st.success("✅ Excel generado con todos los detalles y formato profesional.")
            st.download_button("💾 DESCARGAR REPORTE", output.getvalue(), f"Insumos_{datetime.now().strftime('%d%m%Y')}.xlsx", use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
