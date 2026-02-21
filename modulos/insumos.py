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

# --- FUNCIONES DE FORMATO ---

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
    leyenda = "Comentario: de acuerdo con la Norma Oficial Mexicana NOM-045-SSA2-2005... NINGUN RECIPIENTE DEBERÁ SER RELLENADO."
    cell_nom = ws.cell(row=lr + 1, column=1, value=leyenda)
    cell_nom.alignment = center_align
    cell_nom.font = Font(size=9, italic=True)
    ws.row_dimensions[lr + 1].height = 50

    ws.merge_cells(start_row=lr + 2, start_column=1, end_row=lr + 2, end_column=8)
    cell_auth = ws.cell(row=lr + 2, column=1, value="AUTORIZÓ: DRA. BRENDA CASTILLO MATUS")
    cell_auth.alignment = center_align
    cell_auth.font = Font(bold=True)

def generar_pdf_insumos(df_ais, dict_especialidades):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter), topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []
    
    hoy = datetime.now()
    vencimiento = hoy + timedelta(days=7)
    f_rango = f"DEL {hoy.strftime('%d/%m/%Y')} AL {vencimiento.strftime('%d/%m/%Y')}"
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading2'], alignment=1, fontSize=12, spaceAfter=10)
    footer_style = ParagraphStyle('FooterStyle', parent=styles['Normal'], fontSize=8, alignment=1)

    def crear_hoja_pdf(df, nombre_tit):
        elements.append(Paragraph(f"INSUMOS {nombre_tit} {f_rango}", title_style))
        data = [df.columns.tolist()] + df.values.tolist()
        col_widths = [45, 60, 180, 45, 40, 70, 110, 110]
        t = RLTable(data, repeatRows=1, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("AUTORIZÓ: DRA. BRENDA CASTILLO MATUS", title_style))
        elements.append(PageBreak())

    if not df_ais.empty: crear_hoja_pdf(df_ais, "AISLAMIENTOS")
    for serv, df_s in dict_especialidades.items(): crear_hoja_pdf(df_s, serv)
    doc.build(elements)
    return output.getvalue()

# --- LÓGICA DE DATOS ---

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
        pacs_11_esp_raw = []
        esp_actual = ""
        IGNORAR = ["PACIENTES", "TOTAL", "SUBTOTAL", "PÁGINA", "IMPRESIÓN", "1111"]

        for i, val in enumerate(col0_str):
            if "ESPECIALIDAD:" in val: esp_actual = val; continue
            fila = [str(x).strip() for x in df_html_raw.iloc[i].values]
            if any(x in fila[0] or x in fila[1] for x in IGNORAR): continue
            if len(fila) > 1 and len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
                esp_real = obtener_especialidad_real(fila[0], esp_actual)
                pac_data = {"CAMA": fila[0], "REGISTRO": fila[1], "PACIENTE": fila[2], "SEXO": fila[3], "EDAD": "".join(re.findall(r'\d+', fila[4])), "FECHA DE INGRESO": fila[9], "ESP_REAL": esp_real, "TIPO DE PRECAUCIONES": "ESTÁNDAR", "INSUMO": "JABÓN/SANITAS"}
                datos_html.append(pac_data)
                if esp_real in SERVICIOS_INSUMOS_FILTRO: pacs_11_esp_raw.append(pac_data)

        df_total_html = pd.DataFrame(datos_html)
        df_ais_base = cargar_aislamientos_limpios()
        
        # --- LÓGICA DE CRUCE Y NO DUPLICIDAD ---
        # Identificamos qué registros de aislamientos están en las 11 especialidades
        registros_en_11 = [str(p["REGISTRO"]) for p in pacs_11_esp_raw]
        
        # 1. Actualizar Precauciones en las 11 Especialidades
        pacs_11_procesados = []
        for p in pacs_11_esp_raw:
            ais_match = df_ais_base[df_ais_base["REGISTRO"].astype(str) == str(p["REGISTRO"])]
            if not ais_match.empty:
                # Si existe en aislamiento, combinamos precauciones y marcamos para resaltar
                tipo_ais = ais_match.iloc[0]["TIPO DE AISLAMIENTO"]
                p["TIPO DE PRECAUCIONES"] = f"ESTÁNDAR / {tipo_ais}"
                p["RESALTAR"] = True
            else:
                p["RESALTAR"] = False
            pacs_11_procesados.append(p)
        
        df_11_final = pd.DataFrame(pacs_11_procesados)

        # 2. Filtrar la tabla de Aislamientos General (Sección B)
        # Solo dejamos los que NO están en las 11 especialidades
        df_ais_solo = df_ais_base[~df_ais_base["REGISTRO"].astype(str).isin(registros_en_11)].copy()
        
        # Mapeo final para la tabla de Aislamientos Pura
        if not df_ais_solo.empty:
            df_ais_solo = pd.merge(df_ais_solo, df_total_html, on="REGISTRO", how="left", suffixes=('', '_h'))
            df_ais_solo["CAMA"] = df_ais_solo["CAMA"].fillna(df_ais_solo["CAMA_h"])
            df_ais_solo["PACIENTE"] = df_ais_solo["NOMBRE"].fillna(df_ais_solo["PACIENTE"])
            df_ais_solo["TIPO DE PRECAUCIONES"] = df_ais_solo["TIPO DE AISLAMIENTO"]
            df_ais_solo["INSUMO"] = "JABÓN/SANITAS"
            df_ais_final_seccion_b = df_ais_solo[["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]].fillna("Pendiente")
        else:
            df_ais_final_seccion_b = pd.DataFrame()

        # --- VISTA PREVIA ESPECIALIDADES ---
        st.header("📋 INSUMOS: ESPECIALIDADES")
        if not df_11_final.empty:
            for serv in sorted(df_11_final["ESP_REAL"].unique()):
                with st.expander(f"🔍 {serv}"):
                    df_v = df_11_final[df_11_final["ESP_REAL"] == serv].copy()
                    
                    # Función para resaltar filas que vienen de aislamientos
                    def highlight_ais(row):
                        return ['background-color: #D4E6F1' if row.RESALTAR else '' for _ in row]
                    
                    st.table(df_v[["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]].style.apply(highlight_ais, axis=1))

        # --- VISTA PREVIA AISLAMIENTOS (RESTO) ---
        st.header("🦠 INSUMOS: AISLAMIENTOS (OTROS SERVICIOS)")
        if not df_ais_final_seccion_b.empty:
            st.table(df_ais_final_seccion_b)
        else:
            st.info("Todos los pacientes en aislamiento pertenecen a las especialidades críticas.")

        # --- BOTONES DE DESCARGA ---
        st.divider()
        col1, col2 = st.columns(2)
        
        # Preparar diccionario para reportes
        dict_reporte = {}
        for serv in sorted(df_11_final["ESP_REAL"].unique()):
            dict_reporte[serv] = df_11_final[df_11_final["ESP_REAL"] == serv][["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]]

        with col1:
            if st.button("🚀 GENERAR EXCEL", use_container_width=True, type="primary"):
                out = BytesIO()
                with pd.ExcelWriter(out, engine='openpyxl') as writer:
                    if not df_ais_final_seccion_b.empty:
                        df_ais_final_seccion_b.to_excel(writer, index=False, sheet_name="AISLAMIENTOS", startrow=1)
                        aplicar_formato_oficial(writer, "AISLAMIENTOS", df_ais_final_seccion_b, "INSUMOS AISLAMIENTOS")
                    for s, df_s in dict_reporte.items():
                        df_s.to_excel(writer, index=False, sheet_name=s[:30], startrow=1)
                        aplicar_formato_oficial(writer, s[:30], df_s, f"INSUMOS {s}")
                st.download_button("💾 DESCARGAR EXCEL", out.getvalue(), "Insumos.xlsx", use_container_width=True)

        with col2:
            if st.button("📄 GENERAR PDF", use_container_width=True):
                pdf = generar_pdf_insumos(df_ais_final_seccion_b, dict_reporte)
                st.download_button("📥 DESCARGAR PDF", pdf, "Insumos.pdf", "application/pdf", use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
