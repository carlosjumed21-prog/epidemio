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

# --- FUNCIONES DE APOYO ---
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
        # Cargamos saltando la primera fila de título
        df_ais = pd.read_csv(SHEET_URL_AISLAMIENTOS, skiprows=1, engine='python')
        df_ais.columns = [str(c).strip().upper() for c in df_ais.columns]
        cols_necesarias = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE TÉRMINO"]
        df_ais = df_ais[[c for c in cols_necesarias if c in df_ais.columns]]
        
        # Filtro de activos (Fecha de término vacía)
        df_ais = df_ais.replace(['nan', 'None', 'none', 'NAN', ' '], pd.NA)
        df_ais = df_ais[df_ais["FECHA DE TÉRMINO"].isna()]
        
        # Consolidación de filas dobles
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
    st.info("👈 Por favor, sube el archivo HTML en el apartado de 'Configuración' de la izquierda.")
else:
    try:
        # 1. PROCESAR HTML
        tablas = pd.read_html(st.session_state['archivo_compartido'])
        df_html_raw = max(tablas, key=len)
        col0_str = df_html_raw.iloc[:, 0].fillna("").astype(str).str.upper()
        
        pacs_html = []
        pacs_11_esp = []
        esp_actual = "SIN_ESPECIALIDAD"
        IGNORAR = ["PACIENTES", "TOTAL", "SUBTOTAL", "PÁGINA", "IMPRESIÓN", "1111"]

        for i, val in enumerate(col0_str):
            if "ESPECIALIDAD:" in val:
                esp_actual = val; continue
            fila = [str(x).strip() for x in df_html_raw.iloc[i].values]
            if len(fila) > 1 and len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
                esp_real = obtener_especialidad_real(fila[0], esp_actual)
                datos_pac = {
                    "CAMA_HTML": fila[0], "REGISTRO": fila[1], "PACIENTE": fila[2],
                    "SEXO": fila[3], "EDAD": "".join(re.findall(r'\d+', fila[4])),
                    "FECHA DE INGRESO": fila[9], "ESP_REAL": esp_real
                }
                pacs_html.append(datos_pac)
                if esp_real in SERVICIOS_INSUMOS_FILTRO:
                    pacs_11_esp.append(datos_pac)
        
        df_ref_html = pd.DataFrame(pacs_html)

        # --- SECCIÓN A: 11 ESPECIALIDADES ---
        st.header("📋 INSUMOS: ESPECIALIDADES")
        if pacs_11_esp:
            df_11 = pd.DataFrame(pacs_11_esp)
            for serv in sorted(df_11["ESP_REAL"].unique()):
                with st.expander(f"🔍 Vista Previa: {serv}"):
                    df_v = df_11[df_11["ESP_REAL"] == serv].copy()
                    df_v["TIPO DE PRECAUCIONES"] = "ESTÁNDAR"
                    df_v["INSUMO"] = "JABÓN/SANITAS"
                    st.table(df_v[["CAMA_HTML", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]])
        
        st.markdown("<br><hr><br>", unsafe_allow_html=True)

        # --- SECCIÓN B: AISLAMIENTOS ---
        st.header("🦠 INSUMOS: AISLAMIENTOS")
        df_ais_base = cargar_aislamientos_base()
        
        if not df_ais_base.empty:
            # Empalme con HTML
            df_ais_f = pd.merge(df_ais_base, df_ref_html, on="REGISTRO", how="left")
            
            # Cama inteligente: HTML > Sheets
            df_ais_f["CAMA"] = df_ais_f["CAMA_HTML"].fillna(df_ais_f["CAMA"])
            df_ais_f["PACIENTE"] = df_ais_f["PACIENTE"].fillna(df_ais_f["NOMBRE"])
            df_ais_f["TIPO DE PRECAUCIONES"] = df_ais_f["TIPO DE AISLAMIENTO"]
            df_ais_f["INSUMO"] = "JABÓN/SANITAS"
            
            # Aseguramos que los "Pendientes" sean visibles
            for c in ["SEXO", "EDAD", "FECHA DE INGRESO"]:
                df_ais_f[c] = df_ais_f[c].fillna("Pendiente")

            cols_final = ["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
            df_edit = df_ais_f[cols_final].copy()

            # LÓGICA DE RESALTADO FORZADA
            def highlight_row(row):
                # Si 'Pendiente' existe en la fila, se pinta de amarillo
                is_pending = row.astype(str).str.contains('Pendiente').any()
                return ['background-color: #FFF9C4' if is_pending else '' for _ in row]

            st.warning("⚠️ Completa los datos en las filas amarillas. El color se quitará al ingresar el dato real.")
            
            # Uso de data_editor con Stylus
            df_ais_editado = st.data_editor(
                df_edit.style.apply(highlight_row, axis=1),
                use_container_width=True,
                hide_index=True,
                key="editor_insumos_aislamientos"
            )

            # --- BOTÓN GENERAR EXCEL ---
            if st.button("🚀 GENERAR EXCEL TOTAL", use_container_width=True, type="primary"):
                hoy = datetime.now()
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Hoja Aislamientos (Usa el DF editado)
                    df_ais_editado.to_excel(writer, index=False, sheet_name="AISLAMIENTOS", startrow=1)
                    
                    # Hojas Especialidades
                    if pacs_11_esp:
                        for serv in sorted(df_11["ESP_REAL"].unique()):
                            df_s = df_11[df_11["ESP_REAL"] == serv].copy()
                            df_s["INSUMO"] = "JABÓN/SANITAS"
                            df_s[["CAMA_HTML", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "ESP_REAL", "INSUMO"]].to_excel(
                                writer, index=False, sheet_name=serv[:30].replace("/", "-"), startrow=1
                            )
                
                st.success("✅ Reporte Consolidado generado correctamente.")
                st.download_button("💾 DESCARGAR EXCEL", output.getvalue(), f"Insumos_Epidemio_{hoy.strftime('%d%m%Y')}.xlsx", use_container_width=True)
        else:
            st.info("No se detectaron aislamientos activos en Google Sheets.")

    except Exception as e:
        st.error(f"Error en el procesamiento: {e}")
