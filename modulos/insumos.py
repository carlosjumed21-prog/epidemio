import streamlit as st
import pandas as pd
import numpy as np
import re
import time
from io import BytesIO
from datetime import datetime, timedelta

# Librerías para el Excel
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

# Librerías para el PDF (ReportLab)
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table as RLTable, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- NUEVO ENLACE ACTUALIZADO ---
SHEET_URL_AISLAMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"

SERVICIOS_INSUMOS_FILTRO = [
    "HEMATOLOGIA", "HEMATOLOGIA PEDIATRICA", "ONCOLOGIA PEDIATRICA",
    "NEONATOLOGIA", "INFECTOLOGIA PEDIATRICA", "U.C.I.N.",
    "U.T.I.P.", "TERAPIA POSQUIRURGICA", "UNIDAD DE QUEMADOS",
    "ONCOLOGIA MEDICA", "UCIA"
]

# --- FUNCIONES DE FORMATO (EXCEL Y PDF SE MANTIENEN IGUAL) ---
def aplicar_formato_oficial(writer, sheet_name, df, servicio_nombre):
    ws = writer.sheets[sheet_name]
    hoy = datetime.now()
    vencimiento = hoy + timedelta(days=7)
    f_hoy = hoy.strftime("%d/%m/%Y")
    f_venc = vencimiento.strftime("%d/%m/%Y")
    
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=8)
    titulo = f"{servicio_nombre} DEL {f_hoy} AL {f_venc} (PARA LOS 3 TURNOS Y FINES DE SEMANA)"
    cell_h = ws.cell(row=1, column=1, value=titulo)
    cell_h.alignment = center_align
    cell_h.font = Font(bold=True, size=11)

    for col_num, value in enumerate(df.columns, 1):
        cell = ws.cell(row=2, column=col_num, value=value)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border

    for row in ws.iter_rows(min_row=3, max_row=len(df)+2, min_col=1, max_col=8):
        for cell in row:
            cell.border = border
            cell.alignment = center_align
    
    for i in range(1, 9):
        ws.column_dimensions[get_column_letter(i)].width = 20

    lr = ws.max_row
    ws.merge_cells(start_row=lr + 1, start_column=1, end_row=lr + 1, end_column=8)
    leyenda = "Comentario: de acuerdo con la Norma Oficial Mexicana NOM-045-SSA2-2005..."
    cell_nom = ws.cell(row=lr + 1, column=1, value=leyenda)
    cell_nom.alignment = center_align
    cell_nom.font = Font(size=9, italic=True)
    ws.row_dimensions[lr + 1].height = 50

    ws.merge_cells(start_row=lr + 2, start_column=1, end_row=lr + 2, end_column=8)
    ws.cell(row=lr + 2, column=1, value="AUTORIZÓ: DRA. BRENDA CASTILLO MATUS").alignment = center_align

def generar_pdf_insumos(df_ais, dict_especialidades):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter), topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []
    
    hoy = datetime.now()
    vencimiento = hoy + timedelta(days=7)
    f_rango = f"DEL {hoy.strftime('%d/%m/%Y')} AL {vencimiento.strftime('%d/%m/%Y')}"

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading2'], alignment=1, fontSize=12, spaceAfter=10)
    footer_style = ParagraphStyle('FooterStyle', parent=styles['Normal'], fontSize=8, leading=10, italic=True, alignment=1)
    auth_style = ParagraphStyle('AuthStyle', parent=styles['Normal'], fontSize=10, bold=True, alignment=1, spaceBefore=10)

    def crear_hoja_pdf(df, nombre_tit):
        elements.append(Paragraph(f"INSUMOS {nombre_tit} {f_rango}<br/>(PARA LOS 3 TURNOS Y FINES DE SEMANA)", title_style))
        data = [df.columns.tolist()] + df.values.tolist()
        col_widths = [45, 60, 180, 45, 40, 70, 110, 110]
        t = RLTable(data, repeatRows=1, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Comentario: NOM-045-SSA2-2005...", footer_style))
        elements.append(Paragraph("<b>AUTORIZÓ: DRA. BRENDA CASTILLO MATUS</b>", auth_style))
        elements.append(PageBreak())

    if not df_ais.empty: crear_hoja_pdf(df_ais, "AISLAMIENTOS")
    for serv, df_s in dict_especialidades.items(): crear_hoja_pdf(df_s, serv)

    doc.build(elements)
    return output.getvalue()

# --- LÓGICA DE PROCESAMIENTO (REFORZADA) ---

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

@st.cache_data(ttl=10) # Para que se actualice rápido el link de Google
def cargar_aislamientos_limpios():
    try:
        # Forzar lectura fresca con timestamp
        url_fresca = f"{SHEET_URL_AISLAMIENTOS}&t={time.time()}"
        df = pd.read_csv(url_fresca, skiprows=1, engine='python')
        
        # Limpiar nombres de columnas y datos
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.apply(lambda x: x.astype(str).str.strip())
        df = df.replace(['nan', 'None', 'none', 'NAN', 'NULL', ''], np.nan)

        # 1. Rellenar hacia abajo antes de filtrar para no perder el contexto del paciente
        if "CAMA" in df.columns: df["CAMA"] = df["CAMA"].ffill()
        if "NOMBRE" in df.columns: df["NOMBRE"] = df["NOMBRE"].ffill()
        if "REGISTRO" in df.columns: df["REGISTRO"] = df["REGISTRO"].ffill()

        # 2. Filtro de activos (Fecha de término vacía)
        col_termino = "FECHA DE TÉRMINO"
        if col_termino in df.columns:
            df = df[df[col_termino].isna()]

        # 3. Consolidar Tipos de Aislamiento (por Registro para ser únicos)
        col_tipo = "TIPO DE AISLAMIENTO"
        if col_tipo in df.columns:
            df[col_tipo] = df.groupby("REGISTRO")[col_tipo].transform(
                lambda x: " / ".join(x.dropna().unique())
            )
        
        df = df.drop_duplicates(subset=["REGISTRO"])
        return df[["CAMA", "REGISTRO", "NOMBRE", col_tipo]]
    except Exception as e:
        st.error(f"Error al cargar Sheets: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("📦 Censo de Insumos (Epidemiología)")

if 'archivo_compartido' not in st.session_state:
    st.info("👈 Sube el archivo HTML en la barra lateral para iniciar.")
else:
    try:
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
            if any(x in fila[0] or x in fila[1] for x in IGNORAR): continue

            # Detectar fila de paciente válida (Registro de 5+ dígitos)
            if len(fila) > 1 and len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
                esp_real = obtener_especialidad_real(fila[0], esp_actual)
                pac_data = {
                    "CAMA_HTML": fila[0], 
                    "REGISTRO": fila[1], 
                    "PACIENTE": fila[2], 
                    "SEXO": fila[3], 
                    "EDAD": "".join(re.findall(r'\d+', fila[4])), 
                    "FECHA DE INGRESO": fila[9], 
                    "ESP_REAL": esp_real
                }
                datos_html.append(pac_data)
                if esp_real in SERVICIOS_INSUMOS_FILTRO: pacs_11_esp.append(pac_data)

        df_ref_html = pd.DataFrame(datos_html)

        # SECCIÓN AISLAMIENTOS (REFORZADA)
        st.header("🦠 INSUMOS: AISLAMIENTOS")
        df_base = cargar_aislamientos_limpios()
        
        if not df_base.empty:
            # EL CRUCE CLAVE: Usamos el Registro como llave
            df_f = pd.merge(df_base, df_ref_html, on="REGISTRO", how="left")
            
            # Si el cruce falló (nan), mantenemos el dato del Sheets original
            df_f["CAMA"] = df_f["CAMA_HTML"].fillna(df_f["CAMA"])
            df_f["PACIENTE"] = df_f["PACIENTE"].fillna(df_f["NOMBRE"])
            df_f["TIPO DE PRECAUCIONES"] = df_f["TIPO DE AISLAMIENTO"]
            df_f["INSUMO"] = "JABÓN/SANITAS"
            
            # Detectar los que quedaron incompletos
            for col in ["SEXO", "EDAD", "FECHA DE INGRESO"]:
                df_f[col] = df_f[col].fillna("Pendiente")

            final_cols = ["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
            df_ais_final = df_f[final_cols]

            # Editor para corregir "Pendientes"
            mask_pend = df_ais_final.astype(str).apply(lambda x: x.str.contains('Pendiente')).any(axis=1)
            if mask_pend.any():
                st.warning("⚠️ Hay datos que no se encontraron en el HTML. Favor de completarlos abajo:")
                df_ais_final = st.data_editor(df_ais_final, use_container_width=True, hide_index=True)
            else:
                st.table(df_ais_final)
            
            st.session_state.df_ais_mapeado = df_ais_final

            # --- BOTONES DE DESCARGA ---
            st.divider()
            col_ex, col_pdf = st.columns(2)
            
            dict_especialidades_final = {}
            if pacs_11_esp:
                df_11 = pd.DataFrame(pacs_11_esp)
                for serv in sorted(df_11["ESP_REAL"].unique()):
                    df_s = df_11[df_11["ESP_REAL"] == serv].copy()
                    df_s["INSUMO"] = "JABÓN/SANITAS"
                    df_s["TIPO DE PRECAUCIONES"] = "ESTÁNDAR"
                    df_s = df_s[["CAMA_HTML", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]]
                    df_s.columns = final_cols
                    dict_especialidades_final[serv] = df_s

            with col_ex:
                if st.button("🚀 GENERAR EXCEL TOTAL", use_container_width=True, type="primary"):
                    output_ex = BytesIO()
                    with pd.ExcelWriter(output_ex, engine='openpyxl') as writer:
                        st.session_state.df_ais_mapeado.to_excel(writer, index=False, sheet_name="AISLAMIENTOS", startrow=1)
                        aplicar_formato_oficial(writer, "AISLAMIENTOS", st.session_state.df_ais_mapeado, "INSUMOS AISLAMIENTOS")
                        for s, d in dict_especialidades_final.items():
                            n = s[:30].replace("/", "-")
                            d.to_excel(writer, index=False, sheet_name=n, startrow=1)
                            aplicar_formato_oficial(writer, n, d, f"INSUMOS {s}")
                    st.download_button("💾 DESCARGAR EXCEL", output_ex.getvalue(), "Insumos.xlsx")

            with col_pdf:
                if st.button("📄 GENERAR PDF IMPRESIÓN", use_container_width=True):
                    pdf = generar_pdf_insumos(st.session_state.df_ais_mapeado, dict_especialidades_final)
                    st.download_button("📥 DESCARGAR PDF", pdf, "Insumos.pdf", "application/pdf")
        else:
            st.info("No se detectaron aislamientos activos en el Sheets.")

    except Exception as e:
        st.error(f"Error procesando datos: {e}")
