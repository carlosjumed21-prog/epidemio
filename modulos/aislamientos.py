import streamlit as st
import pandas as pd
import numpy as np
import time
import re
from io import BytesIO
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# Librerías para Excel Profesional
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

# Librerías para PDF Profesional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table as RLTable, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠", layout="wide")

# URLs
SHEET_URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
SHEET_URL_EDITABLE = "https://docs.google.com/spreadsheets/d/1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A/edit"

# --- FUNCIONES DE FORMATO (EXCEL Y PDF) ---

def aplicar_formato_excel_oficial(writer, sheet_name, df, titulo_reporte):
    ws = writer.sheets[sheet_name]
    hoy = datetime.now()
    vencimiento = hoy + timedelta(days=7)
    
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # 1. Título y Vigencia
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(df.columns))
    titulo_texto = f"{titulo_reporte} DEL {hoy.strftime('%d/%m/%Y')} AL {vencimiento.strftime('%d/%m/%Y')}"
    cell_h = ws.cell(row=1, column=1, value=titulo_texto)
    cell_h.alignment = center_align
    cell_h.font = Font(bold=True, size=11)

    # 2. Encabezados
    for col_num, value in enumerate(df.columns, 1):
        cell = ws.cell(row=2, column=col_num, value=value)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border

    # 3. Cuerpo y Autoajuste
    for row in ws.iter_rows(min_row=3, max_row=len(df)+2, min_col=1, max_col=len(df.columns)):
        for cell in row:
            cell.border = border
            cell.alignment = center_align
    
    for i in range(1, len(df.columns) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 22

    # 4. Pie de Página (NOM-045 y Firma)
    lr = ws.max_row
    ws.merge_cells(start_row=lr + 1, start_column=1, end_row=lr + 1, end_column=len(df.columns))
    leyenda = "Comentario: de acuerdo con la Norma Oficial Mexicana NOM-045-SSA2-2005, Para la vigilancia epidemiológica, prevención y control de las infecciones nosocomiales."
    cell_nom = ws.cell(row=lr + 1, column=1, value=leyenda)
    cell_nom.alignment = center_align
    cell_nom.font = Font(size=9, italic=True)
    
    ws.merge_cells(start_row=lr + 2, start_column=1, end_row=lr + 2, end_column=len(df.columns))
    cell_auth = ws.cell(row=lr + 2, column=1, value="AUTORIZÓ: DRA. BRENDA CASTILLO MATUS")
    cell_auth.alignment = center_align
    cell_auth.font = Font(bold=True)

def generar_pdf_aislamientos(df):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter), topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []
    
    hoy = datetime.now()
    vencimiento = hoy + timedelta(days=7)
    f_rango = f"DEL {hoy.strftime('%d/%m/%Y')} AL {vencimiento.strftime('%d/%m/%Y')}"

    title_style = ParagraphStyle('T', parent=styles['Heading2'], alignment=1, fontSize=11, spaceAfter=10)
    footer_style = ParagraphStyle('F', parent=styles['Normal'], fontSize=8, italic=True, alignment=1)
    
    # Título
    elements.append(Paragraph(f"CENSO DE AISLAMIENTOS ACTIVOS {f_rango}", title_style))
    
    # Tabla
    data = [df.columns.tolist()] + df.values.tolist()
    # Ajuste proporcional de anchos para 6 columnas
    col_widths = [50, 70, 180, 120, 120, 80] 
    t = RLTable(data, repeatRows=1, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))
    
    # Leyendas
    leyenda = "Comentario: de acuerdo con la Norma Oficial Mexicana NOM-045-SSA2-2005..."
    elements.append(Paragraph(leyenda, footer_style))
    elements.append(Paragraph("<br/><b>AUTORIZÓ: DRA. BRENDA CASTILLO MATUS</b>", title_style))

    doc.build(elements)
    return output.getvalue()

# --- LÓGICA DE DATOS ---

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def cargar_censo_total():
    url_final = f"{SHEET_URL_ORIGEN}&cachebust={time.time()}"
    df = pd.read_csv(url_final, skiprows=1, engine='python', encoding='utf-8')
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
    df = df.replace(['nan', 'None', '', ' '], np.nan).dropna(subset=["CAMA", "NOMBRE"])
    return df.reset_index(drop=True)

# --- INTERFAZ ---
st.title("🦠 Gestión y Reportes de Aislamiento")

try:
    df_final = cargar_censo_total()
    st.metric("Pacientes Activos", len(df_final))

    # FILA DE BOTONES PRINCIPALES
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔄 Refrescar Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with c2:
        if st.button("🚀 Sincronizar con Drive", use_container_width=True):
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_final)
            st.success("Drive Actualizado")
    with c3:
        st.link_button("📂 Abrir Sheet de Carlos", SHEET_URL_EDITABLE, use_container_width=True)

    st.divider()

    # --- NUEVA SECCIÓN: DESCARGA DE REPORTES OFICIALES ---
    st.subheader("📥 Descargar Reportes con Formato Oficial")
    col_ex, col_pdf = st.columns(2)

    with col_ex:
        # Generar Excel con Formato
        output_ex = BytesIO()
        with pd.ExcelWriter(output_ex, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name="AISLAMIENTOS", startrow=1)
            aplicar_formato_excel_oficial(writer, "AISLAMIENTOS", df_final, "CENSO DE AISLAMIENTOS")
        
        st.download_button(
            label="💾 DESCARGAR EXCEL OFICIAL",
            data=output_ex.getvalue(),
            file_name=f"Censo_Aislamientos_{datetime.now().strftime('%d%m%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )

    with col_pdf:
        # Generar PDF con Formato
        pdf_bytes = generar_pdf_aislamientos(df_final)
        st.download_button(
            label="📄 DESCARGAR PDF OFICIAL",
            data=pdf_bytes,
            file_name=f"Censo_Aislamientos_{datetime.now().strftime('%d%m%Y')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.divider()

    # --- VISTA PREVIA EDITABLE ---
    df_censo = conn.read(spreadsheet=SHEET_URL_EDITABLE, ttl=0)
    if not df_censo.empty:
        df_censo.index = range(1, len(df_censo) + 1)
        df_editado = st.data_editor(df_censo, use_container_width=True, num_rows="dynamic", hide_index=True)
        
        if st.button("💾 Guardar Cambios Manuales en el Censo", use_container_width=True):
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_editado.reset_index(drop=True))
            st.toast("Censo guardado", icon="✅")

except Exception as e:
    st.error(f"Error: {e}")
