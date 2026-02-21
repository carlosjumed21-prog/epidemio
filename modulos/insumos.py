import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from fpdf import FPDF # Asegúrate de tener: pip install fpdf2

# --- CONFIGURACIÓN ---
SHEET_URL_AISLAMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

SERVICIOS_INSUMOS_FILTRO = [
    "HEMATOLOGIA", "HEMATOLOGIA PEDIATRICA", "ONCOLOGIA PEDIATRICA",
    "NEONATOLOGIA", "INFECTOLOGIA PEDIATRICA", "U.C.I.N.",
    "U.T.I.P.", "TERAPIA POSQUIRURGICA", "UNIDAD DE QUEMADOS",
    "ONCOLOGIA MEDICA", "UCIA"
]

# --- LÓGICA DE PDF ---
class PDFInsumos(FPDF):
    def header_oficial(self, servicio_nombre):
        hoy = datetime.now()
        venc = hoy + timedelta(days=7)
        self.set_font('Arial', 'B', 10)
        titulo = f"{servicio_nombre} DEL {hoy.strftime('%d/%m/%Y')} AL {venc.strftime('%d/%m/%Y')}\n(PARA LOS 3 TURNOS Y FINES DE SEMANA)"
        self.multi_cell(0, 5, titulo, border=0, align='C')
        self.ln(5)

    def tabla_insumos(self, df):
        self.set_font('Arial', 'B', 8)
        self.set_fill_color(31, 78, 120) # Azul oficial
        self.set_text_color(255, 255, 255)
        
        # Anchos de columna proporcionales
        widths = [15, 30, 45, 12, 12, 20, 35, 25]
        cols = ["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "INGRESO", "PRECAUCION", "INSUMO"]
        
        for i, col in enumerate(cols):
            self.cell(widths[i], 8, col, border=1, align='C', fill=True)
        self.ln()
        
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', '', 7)
        for _, row in df.iterrows():
            # Control de salto de página manual si la tabla es larga
            if self.get_y() > 250:
                self.add_page()
            
            self.cell(widths[0], 7, str(row[0]), 1, 0, 'C')
            self.cell(widths[1], 7, str(row[1]), 1, 0, 'C')
            self.cell(widths[2], 7, str(row[2])[:25], 1, 0, 'L')
            self.cell(widths[3], 7, str(row[3]), 1, 0, 'C')
            self.cell(widths[4], 7, str(row[4]), 1, 0, 'C')
            self.cell(widths[5], 7, str(row[5]), 1, 0, 'C')
            self.cell(widths[6], 7, str(row[6]), 1, 0, 'C')
            self.cell(widths[7], 7, str(row[7]), 1, 1, 'C')

    def footer_oficial(self):
        self.ln(5)
        self.set_font('Arial', 'I', 7)
        leyenda = "Comentario: de acuerdo con la Norma Oficial Mexicana NOM-045-SSA2-2005, Para la vigilancia epidemiológica, prevención y control de las infecciones nosocomiales. NINGUN RECIPIENTE QUE CONTENGA EL INSUMO DEBERÁ SER RELLENADO O REUTILIZADO."
        self.multi_cell(0, 4, leyenda, border=0, align='C')
        self.ln(5)
        self.set_font('Arial', 'B', 9)
        self.cell(0, 5, "AUTORIZÓ: DRA. BRENDA CASTILLO MATUS", border=0, align='C')

# --- FUNCIONES DE FORMATO EXCEL (Tu lógica original) ---
def aplicar_formato_oficial(writer, sheet_name, df, servicio_nombre):
    ws = writer.sheets[sheet_name]
    hoy = datetime.now()
    vencimiento = hoy + timedelta(days=7)
    f_hoy, f_venc = hoy.strftime("%d/%m/%Y"), vencimiento.strftime("%d/%m/%Y")
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=8)
    cell_h = ws.cell(row=1, column=1, value=f"{servicio_nombre} DEL {f_hoy} AL {f_venc} (PARA LOS 3 TURNOS Y FINES DE SEMANA)")
    cell_h.alignment, cell_h.font = center_align, Font(bold=True, size=11)

    for col_num, value in enumerate(df.columns, 1):
        cell = ws.cell(row=2, column=col_num, value=value)
        cell.fill, cell.font, cell.alignment, cell.border = header_fill, header_font, center_align, border

    for row in ws.iter_rows(min_row=3, max_row=len(df)+2, min_col=1, max_col=8):
        for cell in row: cell.border, cell.alignment = border, center_align
    for i in range(1, 9): ws.column_dimensions[get_column_letter(i)].width = 20

    lr = ws.max_row
    ws.merge_cells(start_row=lr + 1, start_column=1, end_row=lr + 1, end_column=8)
    cell_nom = ws.cell(row=lr + 1, column=1, value="Comentario: de acuerdo con la Norma Oficial Mexicana NOM-045-SSA2-2005...")
    cell_nom.alignment, cell_nom.font = center_align, Font(size=9, italic=True)
    ws.row_dimensions[lr + 1].height = 40

    ws.merge_cells(start_row=lr + 2, start_column=1, end_row=lr + 2, end_column=8)
    cell_auth = ws.cell(row=lr + 2, column=1, value="AUTORIZÓ: DRA. BRENDA CASTILLO MATUS")
    cell_auth.alignment, cell_auth.font = center_align, Font(bold=True)

# --- CARGA Y PROCESAMIENTO ---
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
        df_ais = pd.read_csv(SHEET_URL_AISLAMIENTOS, skiprows=1, engine='python', encoding='latin-1')
        df_ais.columns = [str(c).strip().upper() for c in df_ais.columns]
        cols = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE TÉRMINO"]
        df_ais = df_ais[[c for c in cols if c in df_ais.columns]]
        df_ais = df_ais.replace(['nan', 'None', 'none', 'NAN', ' '], pd.NA)
        df_ais = df_ais[df_ais["FECHA DE TÉRMINO"].isna()]
        ruido = ["1111", "PACIENTES", "TOTAL", "SUBTOTAL"]
        df_ais = df_ais[~df_ais["REGISTRO"].astype(str).str.contains('|'.join(ruido), na=False)]
        df_ais["CAMA"], df_ais["NOMBRE"] = df_ais["CAMA"].ffill(), df_ais["NOMBRE"].ffill()
        df_ais["TIPO DE AISLAMIENTO"] = df_ais.groupby(["CAMA", "NOMBRE"])["TIPO DE AISLAMIENTO"].transform(lambda x: " / ".join(x.dropna().astype(str).unique()))
        return df_ais.drop_duplicates(["CAMA", "NOMBRE"]).dropna(subset=["REGISTRO"])
    except: return pd.DataFrame()

# --- INTERFAZ ---
st.title("📦 Censo de Insumos")

if 'archivo_compartido' not in st.session_state:
    st.info("👈 Sube el archivo HTML en 'Configuración' para iniciar.")
else:
    try:
        tablas = pd.read_html(st.session_state['archivo_compartido'], flavor='lxml')
        df_html_raw = max(tablas, key=len)
        col0_str = df_html_raw.iloc[:, 0].fillna("").astype(str).str.upper()
        
        datos_html, pacs_11_esp = [], []
        esp_actual = ""
        IGNORAR = ["PACIENTES", "TOTAL", "SUBTOTAL", "PÁGINA", "IMPRESIÓN", "1111"]

        for i, val in enumerate(col0_str):
            if "ESPECIALIDAD:" in val: esp_actual = val; continue
            fila = [str(x).strip() for x in df_html_raw.iloc[i].values]
            if any(x in fila[0] or x in fila[1] for x in IGNORAR): continue
            if len(fila) > 1 and len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
                esp_real = obtener_especialidad_real(fila[0], esp_actual)
                pac_data = {"CAMA": fila[0], "REGISTRO": fila[1], "PACIENTE": fila[2], "SEXO": fila[3], "EDAD": "".join(re.findall(r'\d+', fila[4])), "FECHA DE INGRESO": fila[9], "ESP_REAL": esp_real}
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
                    df_v["TIPO DE PRECAUCIONES"], df_v["INSUMO"] = "ESTÁNDAR", "JABÓN/SANITAS"
                    st.table(df_v[["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]])

        st.markdown("<br><hr><br>", unsafe_allow_html=True)
        st.header("🦠 INSUMOS: AISLAMIENTOS")
        
        if 'df_ais_mapeado' not in st.session_state:
            df_base = cargar_aislamientos_limpios()
            if not df_base.empty:
                df_f = pd.merge(df_base, df_ref_html, on="REGISTRO", how="left")
                df_f["CAMA"] = df_f["CAMA_HTML"].fillna(df_f["CAMA"]) if "CAMA_HTML" in df_f else df_f["CAMA"]
                df_f["PACIENTE"], df_f["TIPO DE PRECAUCIONES"], df_f["INSUMO"] = df_f["PACIENTE"].fillna(df_f["NOMBRE"]), df_f["TIPO DE AISLAMIENTO"], "JABÓN/SANITAS"
                for c in ["SEXO", "EDAD", "FECHA DE INGRESO"]: df_f[c] = df_f[c].fillna("Pendiente")
                st.session_state.df_ais_mapeado = df_f[["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]]
            else: st.session_state.df_ais_mapeado = pd.DataFrame()

        if not st.session_state.df_ais_mapeado.empty:
            mask_pend = st.session_state.df_ais_mapeado.astype(str).apply(lambda x: x.str.contains('Pendiente')).any(axis=1)
            df_pend = st.session_state.df_ais_mapeado[mask_pend].copy()

            if not df_pend.empty:
                st.subheader("⚠️ Pacientes por completar (Edición)")
                edit_pend = st.data_editor(df_pend.style.apply(lambda x: ['background-color: #FFF9C4' for _ in x], axis=1), use_container_width=True, hide_index=True, key="ed_pend")
                if not edit_pend.equals(df_pend):
                    st.session_state.df_ais_mapeado.update(edit_pend)
                    st.rerun()

            st.subheader("📋 Tabla Oficial (Aislamientos)")
            st.table(st.session_state.df_ais_mapeado)

            col_ex, col_pdf = st.columns(2)
            
            with col_ex:
                if st.button("🚀 GENERAR EXCEL TOTAL", use_container_width=True, type="primary"):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_ais_final = st.session_state.df_ais_mapeado
                        df_ais_final.to_excel(writer, index=False, sheet_name="AISLAMIENTOS", startrow=1)
                        aplicar_formato_oficial(writer, "AISLAMIENTOS", df_ais_final, "INSUMOS AISLAMIENTOS")
                        if pacs_11_esp:
                            for serv in sorted(df_11["ESP_REAL"].unique()):
                                df_s = df_11[df_11["ESP_REAL"] == serv].copy()
                                df_s["INSUMO"], df_s["TIPO DE PRECAUCIONES"] = "JABÓN/SANITAS", "ESTÁNDAR"
                                df_s = df_s[["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]]
                                nombre_hoja = serv[:30].replace("/", "-")
                                df_s.to_excel(writer, index=False, sheet_name=nombre_hoja, startrow=1)
                                aplicar_formato_oficial(writer, nombre_hoja, df_s, f"INSUMOS {serv}")
                    st.download_button("💾 DESCARGAR EXCEL", output.getvalue(), f"Insumos_Epidemio_{datetime.now().strftime('%d%m%Y')}.xlsx", use_container_width=True)

            with col_pdf:
                if st.button("🖨️ GENERAR REPORTE PDF", use_container_width=True):
                    pdf = PDFInsumos(orientation='L', unit='mm', format='A4')
                    
                    # 1. Página de Aislamientos
                    pdf.add_page()
                    pdf.header_oficial("INSUMOS AISLAMIENTOS")
                    pdf.tabla_insumos(st.session_state.df_ais_mapeado)
                    pdf.footer_oficial()
                    
                    # 2. Páginas por Especialidad
                    if pacs_11_esp:
                        for serv in sorted(df_11["ESP_REAL"].unique()):
                            pdf.add_page()
                            pdf.header_oficial(f"INSUMOS {serv}")
                            df_pdf = df_11[df_11["ESP_REAL"] == serv].copy()
                            df_pdf["INSUMO"], df_pdf["TIPO DE PRECAUCIONES"] = "JABÓN/SANITAS", "ESTÁNDAR"
                            pdf.tabla_insumos(df_pdf[["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]])
                            pdf.footer_oficial()
                    
                    pdf_output = BytesIO()
                    pdf_data = pdf.output(dest='S')
                    st.download_button("💾 DESCARGAR PDF", data=pdf_data, file_name=f"Reporte_Insumos_{datetime.now().strftime('%d%m%Y')}.pdf", mime="application/pdf", use_container_width=True)

    except Exception as e: st.error(f"Error: {e}")
