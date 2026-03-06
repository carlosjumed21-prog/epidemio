import streamlit as st
import pandas as pd
import numpy as np
import time
from io import BytesIO
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# Librerías para Excel
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

# Librerías para PDF con ajuste de texto
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table as RLTable, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠", layout="wide")

SHEET_URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
SHEET_URL_EDITABLE = "https://docs.google.com/spreadsheets/d/1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A/edit"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIONES DE REPORTES (EXCEL Y PDF) ---

def aplicar_formato_excel_oficial(writer, sheet_name, df, titulo_reporte):
    ws = writer.sheets[sheet_name]
    hoy = datetime.now()
    vencimiento = hoy + timedelta(days=7)
    
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(df.columns))
    titulo_texto = f"{titulo_reporte} DEL {hoy.strftime('%d/%m/%Y')} AL {vencimiento.strftime('%d/%m/%Y')}"
    cell_h = ws.cell(row=1, column=1, value=titulo_texto)
    cell_h.alignment = center_align
    cell_h.font = Font(bold=True, size=11)

    for col_num, value in enumerate(df.columns, 1):
        cell = ws.cell(row=2, column=col_num, value=value)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border

    for row in ws.iter_rows(min_row=3, max_row=len(df)+2, min_col=1, max_col=len(df.columns)):
        for cell in row:
            cell.border = border
            cell.alignment = center_align
            cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    
    for i in range(1, len(df.columns) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 25

def generar_pdf_mejorado(df):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter), topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    
    # Estilo para que el texto dentro de la tabla haga wrap
    cell_style = ParagraphStyle('cell', parent=styles['Normal'], fontSize=7, alignment=1, leading=8)
    header_style = ParagraphStyle('header', parent=styles['Normal'], fontSize=8, textColor=colors.whitesmoke, alignment=1, fontName='Helvetica-Bold')
    
    elements = []
    hoy = datetime.now()
    vencimiento = hoy + timedelta(days=7)
    
    # Título
    elements.append(Paragraph(f"<b>CENSO DE AISLAMIENTOS OFICIAL</b><br/>DEL {hoy.strftime('%d/%m/%Y')} AL {vencimiento.strftime('%d/%m/%Y')}", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    # Procesar datos: Convertir cada celda en un Paragraph para que el texto se ajuste
    data = [[Paragraph(col, header_style) for col in df.columns]]
    for row in df.values:
        data.append([Paragraph(str(item), cell_style) for item in row])
    
    # Anchos de columna fijos (en puntos) para paisaje (landscape)
    col_widths = [50, 65, 180, 130, 130, 80]
    
    t = RLTable(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 15))
    
    leyenda = "Comentario: de acuerdo con la NOM-045-SSA2-2005. NINGUN RECIPIENTE DEBERÁ SER RELLENADO."
    elements.append(Paragraph(leyenda, styles['Italic']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>AUTORIZÓ: DRA. BRENDA CASTILLO MATUS</b>", styles['Normal']))

    doc.build(elements)
    return output.getvalue()

# --- LÓGICA DE DATOS ---

@st.cache_data(ttl=2)
def cargar_datos():
    url_final = f"{SHEET_URL_ORIGEN}&cachebust={time.time()}"
    df = pd.read_csv(url_final, skiprows=1, engine='python')
    df = df.iloc[:, 1:10]
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    df["CAMA"] = df["CAMA"].ffill()
    df["NOMBRE"] = df["NOMBRE"].ffill()
    
    def consolidar(group):
        res = group.iloc[0].copy()
        tipos = group["TIPO DE AISLAMIENTO"].dropna().unique()
        res["TIPO DE AISLAMIENTO"] = " / ".join(tipos) if len(tipos) > 0 else np.nan
        return res

    df = df.groupby(["CAMA", "NOMBRE"], as_index=False, sort=False).apply(consolidar)
    if "FECHA DE TÉRMINO" in df.columns:
        df = df[df["FECHA DE TÉRMINO"].isna()]
    
    cols = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "MOTIVO DE SEGUIMIENTO", "FECHA DE INICIO"]
    df = df[[c for c in cols if c in df.columns]]
    return df.dropna(subset=["CAMA", "NOMBRE"]).reset_index(drop=True)

# --- INTERFAZ ---
st.title("🦠 Gestión de Aislamientos")

tab1, tab2 = st.tabs(["🔍 Monitor y Edición", "📦 Insumos Aislamientos"])

with tab1:
    df_final = cargar_datos()
    st.metric("Pacientes Activos", len(df_final))
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with c2:
        if st.button("🚀 Enviar a Drive", use_container_width=True):
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_final)
            st.success("Sincronizado")
    with c3:
        st.link_button("📂 Ver Google Sheets", SHEET_URL_EDITABLE, use_container_width=True)

    st.divider()
    
    df_drive = conn.read(spreadsheet=SHEET_URL_EDITABLE, ttl=0)
    if not df_drive.empty:
        df_drive.index = range(1, len(df_drive) + 1)
        df_ed = st.data_editor(df_drive, use_container_width=True, num_rows="dynamic", hide_index=True)
        if st.button("💾 Guardar Cambios"):
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_ed.reset_index(drop=True))
            st.toast("Guardado")

with tab2:
    st.header("Generación de Reportes Oficiales")
    st.info("Descarga los archivos con el formato oficial de la Dra. Brenda Castillo (NOM-045).")
    
    # Usamos los datos actuales para los reportes
    df_reporte = cargar_datos()
    
    col_ex, col_pdf = st.columns(2)
    
    with col_ex:
        output_ex = BytesIO()
        with pd.ExcelWriter(output_ex, engine='openpyxl') as writer:
            df_reporte.to_excel(writer, index=False, sheet_name="INSUMOS", startrow=1)
            aplicar_formato_excel_oficial(writer, "INSUMOS", df_reporte, "INSUMOS AISLAMIENTOS")
        
        st.download_button(
            "💾 DESCARGAR EXCEL (FORMATO AZUL)",
            output_ex.getvalue(),
            f"Insumos_Aislamientos_{datetime.now().strftime('%d%m%Y')}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, type="primary"
        )
        
    with col_pdf:
        # Generamos el PDF usando Paragraphs para que el texto NO se corte
        pdf_data = generar_pdf_mejorado(df_reporte)
        st.download_button(
            "📄 DESCARGAR PDF (AJUSTE DE TEXTO)",
            pdf_data,
            f"Insumos_Aislamientos_{datetime.now().strftime('%d%m%Y')}.pdf",
            "application/pdf",
            use_container_width=True
        )
