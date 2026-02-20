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
    try:
        df_ais = pd.read_csv(SHEET_URL_AISLAMIENTOS, skiprows=1, engine='python')
        df_ais.columns = [str(c).strip().upper() for c in df_ais.columns]
        # B(CAMA), C(REG), D(NOMBRE), E(TIPO), H(TÉRMINO)
        cols = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE TÉRMINO"]
        df_ais = df_ais[[c for c in cols if c in df_ais.columns]]
        df_ais = df_ais.replace(['nan', 'None', 'none', 'NAN', ' '], pd.NA)
        # Filtro: Solo activos (Fecha de término vacía)
        df_ais = df_ais[df_ais["FECHA DE TÉRMINO"].isna()]
        # Consolidación filas dobles
        df_ais["CAMA"] = df_ais["CAMA"].ffill()
        df_ais["NOMBRE"] = df_ais["NOMBRE"].ffill()
        df_ais["TIPO DE AISLAMIENTO"] = df_ais.groupby(["CAMA", "NOMBRE"])["TIPO DE AISLAMIENTO"].transform(
            lambda x: " / ".join(x.dropna().astype(str).unique())
        )
        return df_ais.drop_duplicates(["CAMA", "NOMBRE"]).dropna(subset=["REGISTRO"])
    except:
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("📦 Censo de Insumos")

if 'archivo_compartido' not in st.session_state:
    st.info("👈 Sube el archivo HTML en 'Configuración' para iniciar.")
else:
    try:
        # 1. ESCANEO DE HTML (Base para todo)
        tablas = pd.read_html(st.session_state['archivo_compartido'])
        df_html_raw = max(tablas, key=len)
        col0_str = df_html_raw.iloc[:, 0].fillna("").astype(str).str.upper()
        
        datos_html = []
        pacs_11_esp = []
        esp_actual = ""
        IGNORAR = ["PACIENTES", "TOTAL", "SUBTOTAL", "PÁGINA", "IMPRESIÓN", "1111"]

        for i, val in enumerate(col0_str):
            if "ESPECIALIDAD:" in val:
                esp_actual = val; continue
            fila = [str(x).strip() for x in df_html_raw.iloc[i].values]
            if len(fila) > 1 and len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
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

        # --- SECCIÓN A: 11 ESPECIALIDADES OBLIGATORIAS ---
        st.header("📋 INSUMOS: ESPECIALIDADES")
        if pacs_11_esp:
            df_11 = pd.DataFrame(pacs_11_esp)
            for serv in sorted(df_11["ESP_REAL"].unique()):
                with st.expander(f"🔍 Vista Previa: {serv}"):
                    df_v = df_11[df_11["ESP_REAL"] == serv].copy()
                    df_v["TIPO DE PRECAUCIONES"] = df_v["ESP_REAL"].apply(
                        lambda x: "ESTÁNDAR / PROTECTOR" if "ONCOLOGIA" in x or "QUEMADOS" in x else "ESTÁNDAR"
                    )
                    df_v["INSUMO"] = "JABÓN/SANITAS"
                    st.table(df_v[["CAMA_HTML", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]])
        else:
            st.warning("No se detectaron pacientes en las 11 especialidades.")

        st.markdown("---") # Espacio visual entre secciones

        # --- SECCIÓN B: AISLAMIENTOS (CON EDICIÓN MANUAL) ---
        st.header("🦠 INSUMOS: AISLAMIENTOS")
        df_ais_base = cargar_aislamientos_limpios()
        
        if not df_ais_base.empty:
            # Empalme con HTML
            df_ais_final = pd.merge(df_ais_base, df_mapeo_html, on="REGISTRO", how="left")
            
            # Actualizar camas y completar datos
            df_ais_final["CAMA"] = df_ais_final["CAMA_HTML"].fillna(df_ais_final["CAMA"])
            df_ais_final["PACIENTE"] = df_ais_final["PACIENTE"].fillna(df_ais_final["NOMBRE"])
            df_ais_final["TIPO DE PRECAUCIONES"] = df_ais_final["TIPO DE AISLAMIENTO"]
            df_ais_final["INSUMO"] = "JABÓN/SANITAS"
            
            for c in ["SEXO", "EDAD", "FECHA DE INGRESO"]:
                df_ais_final[c] = df_ais_final[c].fillna("Pendiente")

            cols_ais = ["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
            df_editor_ais = df_ais_final[cols_ais]

            # Estilo para celdas Pendiente
            def resaltar_pendientes(val):
                return 'background-color: #fff9c4' if val == "Pendiente" else ''

            st.info("📝 Edita los campos 'Pendiente' si es necesario antes de generar el reporte.")
            
            df_editado_final = st.data_editor(
                df_editor_ais.style.applymap(resaltar_pendientes, subset=["SEXO", "EDAD", "FECHA DE INGRESO"]),
                use_container_width=True,
                hide_index=True,
                key="editor_ais"
            )

            # --- GENERAR EXCEL TOTAL ---
            if st.button("🚀 GENERAR EXCEL TOTAL", use_container_width=True, type="primary"):
                hoy = datetime.now()
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Hoja Aislamientos (con cambios manuales)
                    df_editado_final.to_excel(writer, index=False, sheet_name="AISLAMIENTOS", startrow=1)
                    # Hojas Especialidades
                    if pacs_11_esp:
                        for serv in sorted(df_11["ESP_REAL"].unique()):
                            df_s = df_11[df_11["ESP_REAL"] == serv].copy()
                            df_s["TIPO DE PRECAUCIONES"] = "ESTÁNDAR"
                            df_s["INSUMO"] = "JABÓN/SANITAS"
                            df_s[["CAMA_HTML", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]].to_excel(
                                writer, index=False, sheet_name=serv[:30].replace("/", "-"), startrow=1
                            )
                
                st.success("✅ Reporte consolidado generado.")
                st.download_button("💾 DESCARGAR EXCEL", output.getvalue(), f"Insumos_Total_{hoy.strftime('%d%m%Y')}.xlsx", use_container_width=True)
        else:
            st.info("No hay aislamientos activos registrados.")

    except Exception as e:
        st.error(f"Error en el proceso: {e}")
