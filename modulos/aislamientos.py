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
SHEET_URL_ORIGEN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"
SHEET_URL_EDITABLE = "https://docs.google.com/spreadsheets/d/1LfQTTfto_I5bpLIyiWblfypD3gu99MoWldmW9bmuJ4A/edit"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIONES DE FORMATO (EXCEL Y PDF) ---
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
    cell_h = ws.cell(row=1, column=1, value=f"{titulo_reporte} DEL {hoy.strftime('%d/%m/%Y')} AL {vencimiento.strftime('%d/%m/%Y')}")
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
    estilo_titulo = ParagraphStyle('T', parent=styles['Heading2'], alignment=1, fontSize=11)
    estilo_celda = ParagraphStyle('C', parent=styles['Normal'], fontSize=7, alignment=1)
    
    elements = [Paragraph("CENSO DE AISLAMIENTOS VIGENTES", estilo_titulo), Spacer(1, 10)]
    data = [df.columns.tolist()] + df.values.tolist()
    
    t = RLTable(data, colWidths=[50, 70, 200, 150, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F4E78")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
    ]))
    elements.append(t)
    doc.build(elements)
    return output.getvalue()

# --- LÓGICA DE DATOS CORREGIDA ---

@st.cache_data(ttl=5)
def cargar_datos_aislamiento():
    try:
        # 1. Cargar datos ignorando filas vacías iniciales
        url_final = f"{SHEET_URL_ORIGEN}&cachebust={time.time()}"
        df = pd.read_csv(url_final, skiprows=1, engine='python')
        
        # 2. Seleccionar solo las columnas de interés (evitar columnas fantasmas a la derecha)
        df = df.iloc[:, 1:10]
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # 3. Limpieza de datos: Rellenar ffill solo si hay datos reales
        df["CAMA"] = df["CAMA"].astype(str).replace(['nan', 'None', ''], np.nan).ffill()
        df["NOMBRE"] = df["NOMBRE"].astype(str).replace(['nan', 'None', ''], np.nan).ffill()
        
        # 4. ELIMINAR FILAS TOTALMENTE VACÍAS (Esto previene el error de los 75 registros)
        # Solo procesamos si el nombre no es nulo/vacío
        df = df[df["NOMBRE"].notna() & (df["NOMBRE"] != "nan")].copy()

        # 5. FILTRADO POR VIGENCIA (Fecha de Término)
        if "FECHA DE TÉRMINO" in df.columns:
            # Convertir a string y limpiar
            df["FECHA DE TÉRMINO"] = df["FECHA DE TÉRMINO"].astype(str).str.strip().replace(['nan', 'None', 'NaT', ''], np.nan)
            # Nos quedamos SOLO con los que NO tienen fecha de término
            df = df[df["FECHA DE TÉRMINO"].isna()].copy()

        # 6. CONSOLIDACIÓN (Si un paciente tiene varias filas de aislamiento)
        def consolidar(group):
            res = group.iloc[0].copy()
            if "TIPO DE AISLAMIENTO" in group.columns:
                tipos = [str(t) for t in group["TIPO DE AISLAMIENTO"].dropna().unique() if str(t).strip().lower() not in ['nan', 'none', '']]
                res["TIPO DE AISLAMIENTO"] = " / ".join(tipos) if tipos else "PTE"
            return res

        if not df.empty:
            df = df.groupby(["CAMA", "NOMBRE"], as_index=False, sort=False).apply(consolidar).reset_index(drop=True)
            
            # Columnas finales
            cols_orden = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE INICIO"]
            df = df[[c for c in cols_orden if c in df.columns]].copy()
            df["INSUMO"] = "JABÓN/SANITAS"
            
            # Último filtro de seguridad: eliminar registros residuales
            df = df[df["NOMBRE"].str.len() > 3] 
            return df.reset_index(drop=True)
        
        return pd.DataFrame()

    except Exception as e:
        st.error(f"Error técnico: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🦠 Control de Vigilancia Epidemiológica")

tab1, tab2 = st.tabs(["🔍 Monitor", "📦 Insumos"])

with tab1:
    df_actual = cargar_datos_aislamiento()
    
    # Métricas
    c1, c2 = st.columns(2)
    c1.metric("Pacientes Aislados (Vigentes)", len(df_actual))
    
    if not df_actual.empty:
        st.dataframe(df_actual, use_container_width=True, hide_index=True)
        
        if st.button("🔄 Forzar Actualización desde Google Sheets"):
            st.cache_data.clear()
            st.rerun()
    else:
        st.info("No se encontraron aislamientos vigentes. Revisa si las fechas de término están llenas en el Excel.")

with tab2:
    if not df_actual.empty:
        st.subheader("Generar Reportes Oficiales")
        col_ex, col_pdf = st.columns(2)
        
        with col_ex:
            output_ex = BytesIO()
            with pd.ExcelWriter(output_ex, engine='openpyxl') as writer:
                df_actual.to_excel(writer, index=False, sheet_name="AISLAMIENTOS", startrow=1)
                aplicar_formato_excel_oficial(writer, "AISLAMIENTOS", df_actual, "AISLAMIENTOS")
            st.download_button("💾 Descargar Excel", output_ex.getvalue(), "Censo_Insumos.xlsx", "application/vnd.ms-excel", use_container_width=True)
            
        with col_pdf:
            pdf_data = generar_pdf_oficial(df_actual)
            st.download_button("📄 Descargar PDF", pdf_data, "Censo_Insumos.pdf", "application/pdf", use_container_width=True)
