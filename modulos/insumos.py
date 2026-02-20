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

# --- LÓGICA DE APOYO ---
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
        # B=CAMA, C=REGISTRO, D=NOMBRE, E=TIPO DE AISLAMIENTO, H=FECHA DE TÉRMINO
        cols_necesarias = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE TÉRMINO"]
        df_ais = df_ais[[c for c in cols_necesarias if c in df_ais.columns]]
        # Filtrar solo los activos (Fecha de término vacía)
        col_venc = "FECHA DE TÉRMINO"
        if col_venc in df_ais.columns:
            df_ais = df_ais[df_ais[col_venc].isna() | (df_ais[col_venc].astype(str).str.strip() == "")]
        return df_ais
    except:
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("📦 Censo de Insumos (Especialidades y Aislamientos)")

if 'archivo_compartido' not in st.session_state:
    st.info("👈 Por favor, sube el archivo HTML en el apartado de 'Configuración' de la izquierda.")
else:
    try:
        # 1. Procesar HTML para Especialidades y Referencia Demográfica
        tablas = pd.read_html(st.session_state['archivo_compartido'])
        df_html_raw = max(tablas, key=len)
        col0_str = df_html_raw.iloc[:, 0].fillna("").astype(str).str.upper()
        
        lista_demograficos_html = []
        pacs_11_esp = []
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
                    "CAMA_HTML": fila[0], 
                    "REGISTRO": fila[1], 
                    "PACIENTE": fila[2], 
                    "SEXO": fila[3], 
                    "EDAD": "".join(re.findall(r'\d+', fila[4])), 
                    "FECHA DE INGRESO": fila[9],
                    "ESP_REAL": esp_real
                }
                
                # Guardamos para el match de aislamientos
                lista_demograficos_html.append(datos_pac)
                
                # Clasificamos para las 11 especialidades
                if esp_real in SERVICIOS_INSUMOS_FILTRO:
                    pacs_11_esp.append(datos_pac)
        
        df_referencia_html = pd.DataFrame(lista_demograficos_html)

        # --- SECCIÓN 1: LAS 11 ESPECIALIDADES (VISTAS INDIVIDUALES) ---
        st.subheader("📋 Insumos por Especialidades Obligadas")
        if not pacs_11_esp:
            st.warning("No se encontraron pacientes para las 11 especialidades en el HTML.")
        else:
            df_11 = pd.DataFrame(pacs_11_esp)
            servicios_encontrados = sorted(df_11["ESP_REAL"].unique())
            
            for serv in servicios_encontrados:
                with st.expander(f"🔍 Vista Previa: {serv}"):
                    df_v = df_11[df_11["ESP_REAL"] == serv].copy()
                    df_v["TIPO DE PRECAUCIONES"] = df_v["ESP_REAL"].apply(
                        lambda x: "ESTÁNDAR / PROTECTOR" if "ONCOLOGIA" in x or "QUEMADOS" in x else "ESTÁNDAR"
                    )
                    df_v["INSUMO"] = "JABÓN/SANITAS"
                    st.table(df_v[["CAMA_HTML", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]])

        # --- SECCIÓN 2: AISLAMIENTOS (CON CAMA ACTUALIZADA O DE ORIGEN) ---
        st.subheader("🦠 Insumos por Aislamientos")
        df_ais_base = cargar_aislamientos_base()
        
        if df_ais_base.empty:
            st.info("No hay pacientes activos en la lista de Aislamientos.")
        else:
            # Empalme (Merge) con los datos del HTML
            df_ais_final = pd.merge(df_ais_base, df_referencia_html, on="REGISTRO", how="left")
            
            # LÓGICA DE CAMA: Si no está en HTML (NaN), se queda con la CAMA de Google Sheets
            df_ais_final["CAMA_FINAL"] = df_ais_final["CAMA_HTML"].fillna(df_ais_final["CAMA"])
            
            # Llenar datos faltantes (Sexo, Edad, etc.) para los que no están en HTML
            df_ais_final["PACIENTE"] = df_ais_final["PACIENTE"].fillna(df_ais_final["NOMBRE"])
            df_ais_final["SEXO"] = df_ais_final["SEXO"].fillna("S/D")
            df_ais_final["EDAD"] = df_ais_final["EDAD"].fillna("S/D")
            df_ais_final["FECHA DE INGRESO"] = df_ais_final["FECHA DE INGRESO"].fillna("S/D")
            df_ais_final["TIPO DE PRECAUCIONES"] = df_ais_final["TIPO DE AISLAMIENTO"]
            df_ais_final["INSUMO"] = "JABÓN/SANITAS"

            with st.expander("👁️ Vista Previa: Pacientes en Aislamiento", expanded=True):
                cols_ais = ["CAMA_FINAL", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
                st.table(df_ais_final[cols_ais])

        # --- BOTÓN GENERAR EXCEL ---
        if st.button("🚀 GENERAR EXCEL DE INSUMOS TOTAL", use_container_width=True, type="primary"):
            hoy = datetime.now()
            venc = hoy + timedelta(days=7)
            output = BytesIO()
            thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # 1. Pestañas de Especialidades
                if not df_11.empty:
                    for serv in servicios_encontrados:
                        df_s = df_11[df_11["ESP_REAL"] == serv].copy()
                        df_s["TIPO DE PRECAUCIONES"] = df_s["ESP_REAL"].apply(lambda x: "ESTÁNDAR / PROTECTOR" if "ONCOLOGIA" in x or "QUEMADOS" in x else "ESTÁNDAR")
                        df_s["INSUMO"] = "JABÓN/SANITAS"
                        
                        df_excel = df_s[["CAMA_HTML", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]]
                        df_excel.columns = ["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
                        
                        sn = serv[:30].replace("/", "-")
                        df_excel.to_excel(writer, index=False, sheet_name=sn, startrow=1)
                        ws = writer.sheets[sn]
                        
                        # Encabezado y Estilos
                        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=8)
                        cell = ws.cell(row=1, column=1, value=f"{serv} DEL {hoy.strftime('%d/%m/%Y')} AL {venc.strftime('%d/%m/%Y')}")
                        cell.alignment = Alignment(horizontal="center"); cell.font = Font(bold=True)
                        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=8):
                            for c in row: c.border = thin_border; c.alignment = Alignment(horizontal="center")

                # 2. Pestaña de Aislamientos
                if not df_ais_final.empty:
                    df_ais_ex = df_ais_final[["CAMA_FINAL", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]]
                    df_ais_ex.columns = ["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
                    df_ais_ex.to_excel(writer, index=False, sheet_name="AISLAMIENTOS", startrow=1)
                    ws_a = writer.sheets["AISLAMIENTOS"]
                    ws_a.merge_cells(start_row=1, start_column=1, end_row=1, end_column=8)
                    cell_a = ws_a.cell(row=1, column=1, value=f"INSUMOS AISLAMIENTOS DEL {hoy.strftime('%d/%m/%Y')} AL {venc.strftime('%d/%m/%Y')}")
                    cell_a.alignment = Alignment(horizontal="center"); cell_a.font = Font(bold=True)

            st.success("✅ Reporte de insumos (Especialidades + Aislamientos) generado.")
            st.download_button(label="💾 DESCARGAR REPORTE", data=output.getvalue(), file_name=f"Insumos_Epidemio_{hoy.strftime('%d%m%Y')}.xlsx", use_container_width=True)

    except Exception as e:
        st.error(f"Error crítico: {e}")
