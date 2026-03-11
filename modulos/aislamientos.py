import streamlit as st
import pandas as pd
import numpy as np
import time
from io import BytesIO
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# Librerías para Excel Profesional
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

# Librerías para PDF Profesional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table as RLTable, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠", layout="wide")

# URLs
# Origen: CSV Público con todos los datos
SHEET_URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
# Destino: Hoja de edición para el equipo
SHEET_URL_EDITABLE = "https://docs.google.com/spreadsheets/d/1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A/edit"

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIONES DE FORMATO ---

def aplicar_formato_excel_oficial(writer, sheet_name, df, titulo_reporte):
    ws = writer.sheets[sheet_name]
    hoy = datetime.now()
    vencimiento = hoy + timedelta(days=7)
    
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    num_cols = len(df.columns)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=num_cols)
    titulo_texto = f"{titulo_reporte} DEL {hoy.strftime('%d/%m/%Y')} AL {vencimiento.strftime('%d/%m/%Y')} (PARA LOS 3 TURNOS Y FINES DE SEMANA)"
    
    cell_h = ws.cell(row=1, column=1, value=titulo_texto)
    cell_h.alignment = center_align
    cell_h.font = Font(bold=True, size=11)

    for col_num, value in enumerate(df.columns, 1):
        cell = ws.cell(row=2, column=col_num, value=value)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border

    for row in ws.iter_rows(min_row=3, max_row=len(df)+2, min_col=1, max_col=num_cols):
        for cell in row:
            cell.border = border
            cell.alignment = center_align

def generar_pdf_oficial(df):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter), topMargin=20, bottomMargin=20, leftMargin=30, rightMargin=30)
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('T', parent=styles['Heading2'], alignment=1, fontSize=11, spaceAfter=2)
    estilo_celda = ParagraphStyle('cell', parent=styles['Normal'], fontSize=7, alignment=1)
    
    elements = [Paragraph("CENSO DE AISLAMIENTOS VIGENTES", estilo_titulo), Spacer(1, 10)]
    data = [df.columns.tolist()] + df.values.tolist()
    
    t = RLTable(data, colWidths=[50, 70, 200, 150, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
    ]))
    elements.append(t)
    doc.build(elements)
    return output.getvalue()

# --- LÓGICA DE DATOS ---

@st.cache_data(ttl=2)
def cargar_datos_origen():
    # Cargar desde Origen
    url_final = f"{SHEET_URL_ORIGEN}&cachebust={time.time()}"
    df = pd.read_csv(url_final, skiprows=1, engine='python')
    
    # Selección y limpieza de columnas
    df = df.iloc[:, 1:10]
    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
    
    # Rellenar datos
    df["CAMA"] = df["CAMA"].ffill()
    df["NOMBRE"] = df["NOMBRE"].ffill()
    
    # --- FILTRADO REFORZADO ---
    # 1. Eliminar filas donde el nombre sea nulo o basura del CSV
    df = df.dropna(subset=["CAMA", "NOMBRE"])
    df = df[df["NOMBRE"].astype(str).str.strip() != ""]
    
    # 2. Condicionante: Solo si FECHA DE TÉRMINO está vacía
    if "FECHA DE TÉRMINO" in df.columns:
        # Normalizamos la columna de término para detectar vacíos reales
        df["FECHA DE TÉRMINO"] = df["FECHA DE TÉRMINO"].astype(str).replace(['nan', 'None', ' ', '', 'NaT'], np.nan)
        df = df[df["FECHA DE TÉRMINO"].isna()].copy()
    
    # Consolidar tipos de aislamiento
    def consolidar(group):
        res = group.iloc[0].copy()
        tipos = group["TIPO DE AISLAMIENTO"].dropna().unique()
        res["TIPO DE AISLAMIENTO"] = " / ".join(map(str, tipos)) if len(tipos) > 0 else "N/A"
        return res

    if not df.empty:
        df = df.groupby(["CAMA", "NOMBRE"], as_index=False, sort=False).apply(consolidar).reset_index(drop=True)
    
    cols_orden = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE INICIO"]
    df = df[[c for c in cols_orden if c in df.columns]].copy()
    df["INSUMO"] = "JABÓN/SANITAS"
    
    return df.reset_index(drop=True)

# --- INTERFAZ ---
st.title("🦠 Control de Aislamientos - Epidemiología")

tab1, tab2 = st.tabs(["🔍 Monitor y Edición", "📝 Reportes"])

with tab1:
    df_vigentes = cargar_datos_origen()
    
    # Métricas reales
    total_vigentes = len(df_vigentes)
    st.metric("Aislamientos Vigentes Detectados", total_vigentes)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔄 Actualizar desde Origen", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with c2:
        if st.button("🚀 Sincronizar a Hoja Editable", use_container_width=True):
            conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_vigentes)
            st.success("Hoja de vaciado actualizada")
    with c3:
        st.link_button("📂 Abrir Hoja de Vaciado", SHEET_URL_EDITABLE, use_container_width=True)

    st.divider()
    
    st.subheader("📋 Editor de Trabajo (Vaciado)")
    # Leemos la hoja donde se vacían los datos
    try:
        df_vaciado = conn.read(spreadsheet=SHEET_URL_EDITABLE, ttl=0)
        if not df_vaciado.empty:
            df_ed = st.data_editor(df_vaciado, use_container_width=True, num_rows="dynamic", hide_index=True)
            if st.button("💾 Guardar Cambios Manuales", use_container_width=True):
                conn.update(spreadsheet=SHEET_URL_EDITABLE, data=df_ed.reset_index(drop=True))
                st.toast("Datos guardados", icon="✅")
        else:
            st.info("La hoja de vaciado está vacía. Presiona 'Sincronizar' para traer los datos vigentes.")
    except:
        st.error("No se pudo conectar con la hoja de vaciado.")

with tab2:
    st.header("Generación de Reportes")
    if not df_vigentes.empty:
        col_ex, col_pdf = st.columns(2)
        with col_ex:
            output_ex = BytesIO()
            with pd.ExcelWriter(output_ex, engine='openpyxl') as writer:
                df_vigentes.to_excel(writer, index=False, sheet_name="INSUMOS", startrow=1)
                aplicar_formato_excel_oficial(writer, "INSUMOS", df_vigentes, "INSUMOS")
            st.download_button("💾 Excel de Insumos", output_ex.getvalue(), "Insumos.xlsx", use_container_width=True)
            
        with col_pdf:
            pdf_data = generar_pdf_oficial(df_vigentes)
            st.download_button("📄 PDF de Insumos", pdf_data, "Insumos.pdf", use_container_width=True)
