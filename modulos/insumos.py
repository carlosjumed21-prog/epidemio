import streamlit as st
import pandas as pd
import re
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

# --- CONFIGURACIÓN ---
SHEET_URL_AISLAMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

SERVICIOS_INSUMOS_FILTRO = [
    "HEMATOLOGIA", "HEMATOLOGIA PEDIATRICA", "ONCOLOGIA PEDIATRICA",
    "NEONATOLOGIA", "INFECTOLOGIA PEDIATRICA", "U.C.I.N.",
    "U.T.I.P.", "TERAPIA POSQUIRURGICA", "UNIDAD DE QUEMADOS",
    "ONCOLOGIA MEDICA", "UCIA"
]

# --- FUNCIONES DE FORMATO Y LÓGICA (EXCEL) ---

def aplicar_formato_oficial(writer, sheet_name, df, servicio_nombre):
    """Aplica encabezados azules, vigencia de 7 días, bordes, NOM-045 y Firma en Excel."""
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
    leyenda = "Comentario: de acuerdo con la Norma Oficial Mexicana NOM-045-SSA2-2005, Para la vigilancia epidemiológica, prevención y control de las infecciones nosocomiales. NINGUN RECIPIENTE QUE CONTENGA EL INSUMO DEBERÁ SER RELLENADO O REUTILIZADO."
    cell_nom = ws.cell(row=lr + 1, column=1, value=leyenda)
    cell_nom.alignment = center_align
    cell_nom.font = Font(size=9, italic=True)
    ws.row_dimensions[lr + 1].height = 50

    ws.merge_cells(start_row=lr + 2, start_column=1, end_row=lr + 2, end_column=8)
    cell_auth = ws.cell(row=lr + 2, column=1, value="AUTORIZÓ: DRA. BRENDA CASTILLO MATUS")
    cell_auth.alignment = center_align
    cell_auth.font = Font(bold=True)

# --- FUNCIÓN GENERAR PDF (REPORTLAB) ---

def generar_pdf_insumos(df_ais, dict_especialidades):
    """Genera un PDF con formato oficial, una página por servicio."""
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
        # Título de la página
        elements.append(Paragraph(f"INSUMOS {nombre_tit} {f_rango}<br/>(PARA LOS 3 TURNOS Y FINES DE SEMANA)", title_style))
        elements.append(Spacer(1, 10))
        
        # Tabla
        data = [df.columns.tolist()] + df.values.tolist()
        # Ajuste de anchos de columna para landscape (aprox 700 pts totales)
        col_widths = [45, 60, 180, 45, 40, 70, 110, 110]
        
        t = RLTable(data, repeatRows=1, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 15))
        
        # Pie de página
        leyenda = "Comentario: de acuerdo con la Norma Oficial Mexicana NOM-045-SSA2-2005, Para la vigilancia epidemiológica, prevención y control de las infecciones nosocomiales. NINGUN RECIPIENTE QUE CONTENGA EL INSUMO DEBERÁ SER RELLENADO O REUTILIZADO."
        elements.append(Paragraph(leyenda, footer_style))
        elements.append(Paragraph("<b>AUTORIZÓ: DRA. BRENDA CASTILLO MATUS</b>", auth_style))
        elements.append(PageBreak())

    if not df_ais.empty:
        crear_hoja_pdf(df_ais, "AISLAMIENTOS")
    
    for serv, df_s in dict_especialidades.items():
        crear_hoja_pdf(df_s, serv)

    doc.build(elements)
    return output.getvalue()

# --- LÓGICA DE PROCESAMIENTO ---

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
        cols = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE TÉRMINO"]
        df_ais = df_ais[[c for c in cols if c in df_ais.columns]]
        df_ais = df_ais.replace(['nan', 'None', 'none', 'NAN', ' '], pd.NA)
        df_ais = df_ais[df_ais["FECHA DE TÉRMINO"].isna()]
        
        ruido = ["1111", "PACIENTES", "TOTAL", "SUBTOTAL"]
        df_ais = df_ais[~df_ais["REGISTRO"].astype(str).str.contains('|'.join(ruido), na=False)]
        
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

            if len(fila) > 1 and len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
                esp_real = obtener_especialidad_real(fila[0], esp_actual)
                pac_data = {"CAMA_HTML": fila[0], "REGISTRO": fila[1], "PACIENTE": fila[2], "SEXO": fila[3], "EDAD": "".join(re.findall(r'\d+', fila[4])), "FECHA DE INGRESO": fila[9], "ESP_REAL": esp_real}
                datos_html.append(pac_data)
                if esp_real in SERVICIOS_INSUMOS_FILTRO: pacs_11_esp.append(pac_data)

        df_ref_html = pd.DataFrame(datos_html)

        # SECCIÓN A: ESPECIALIDADES
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

        # SECCIÓN B: AISLAMIENTOS
        st.header("🦠 INSUMOS: AISLAMIENTOS")
        if 'df_ais_mapeado' not in st.session_state:
            df_base = cargar_aislamientos_limpios()
            if not df_base.empty:
                df_f = pd.merge(df_base, df_ref_html, on="REGISTRO", how="left")
                df_f["CAMA"] = df_f["CAMA_HTML"].fillna(df_f["CAMA"])
                df_f["PACIENTE"] = df_f["PACIENTE"].fillna(df_f["NOMBRE"])
                df_f["TIPO DE PRECAUCIONES"] = df_f["TIPO DE AISLAMIENTO"]
                df_f["INSUMO"] = "JABÓN/SANITAS"
                for c in ["SEXO", "EDAD", "FECHA DE INGRESO"]: df_f[c] = df_f[c].fillna("Pendiente")
                st.session_state.df_ais_mapeado = df_f[["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]]
            else:
                st.session_state.df_ais_mapeado = pd.DataFrame()

        if not st.session_state.df_ais_mapeado.empty:
            df_actual = st.session_state.df_ais_mapeado
            mask_pend = df_actual.astype(str).apply(lambda x: x.str.contains('Pendiente')).any(axis=1)
            df_pend = df_actual[mask_pend].copy()

            if not df_pend.empty:
                st.subheader("⚠️ Pacientes por completar (Edición)")
                edit_pend = st.data_editor(df_pend.style.apply(lambda x: ['background-color: #FFF9C4' for _ in x], axis=1), use_container_width=True, hide_index=True, key="ed_pend")
                if not edit_pend.equals(df_pend):
                    st.session_state.df_ais_mapeado.update(edit_pend)
                    st.rerun()

            st.subheader("📋 Tabla Oficial (Aislamientos)")
            st.table(st.session_state.df_ais_mapeado)

            # --- GENERACIÓN DE REPORTES ---
            st.divider()
            col_ex, col_pdf = st.columns(2)

            # Diccionario de servicios para reportes
            dict_especialidades_final = {}
            if pacs_11_esp:
                for serv in sorted(df_11["ESP_REAL"].unique()):
                    df_s = df_11[df_11["ESP_REAL"] == serv].copy()
                    df_s["INSUMO"] = "JABÓN/SANITAS"
                    df_s["TIPO DE PRECAUCIONES"] = "ESTÁNDAR"
                    df_s = df_s[["CAMA_HTML", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]]
                    df_s.columns = ["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
                    dict_especialidades_final[serv] = df_s

            with col_ex:
                if st.button("🚀 GENERAR EXCEL TOTAL", use_container_width=True, type="primary"):
                    output_ex = BytesIO()
                    with pd.ExcelWriter(output_ex, engine='openpyxl') as writer:
                        df_ais_final = st.session_state.df_ais_mapeado
                        df_ais_final.to_excel(writer, index=False, sheet_name="AISLAMIENTOS", startrow=1)
                        aplicar_formato_oficial(writer, "AISLAMIENTOS", df_ais_final, "INSUMOS AISLAMIENTOS")
                        
                        for serv, df_s in dict_especialidades_final.items():
                            nombre_hoja = serv[:30].replace("/", "-")
                            df_s.to_excel(writer, index=False, sheet_name=nombre_hoja, startrow=1)
                            aplicar_formato_oficial(writer, nombre_hoja, df_s, f"INSUMOS {serv}")
                    
                    st.download_button("💾 DESCARGAR EXCEL", output_ex.getvalue(), f"Insumos_Epidemio_{datetime.now().strftime('%d%m%Y')}.xlsx", use_container_width=True)

            with col_pdf:
                if st.button("📄 GENERAR PDF IMPRESIÓN", use_container_width=True):
                    pdf_bytes = generar_pdf_insumos(st.session_state.df_ais_mapeado, dict_especialidades_final)
                    st.download_button("📥 DESCARGAR PDF", pdf_bytes, f"Insumos_Epidemio_{datetime.now().strftime('%d%m%Y')}.pdf", "application/pdf", use_container_width=True)

        else:
            st.info("No hay aislamientos activos registrados.")

    except Exception as e:
        st.error(f"Error: {e}")
