import streamlit as st
import pandas as pd
import numpy as np
import io

from reportlab.lib.pagesizes import letter, portrait
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# Estilos CSS personalizados para la interfaz web y la tabla de acotaciones
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #111827; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    .info-box { background-color: #F8FAFC; border-left: 4px solid #374151; padding: 12px; margin-bottom: 20px; border-radius: 4px; }
    
    .acotacion-table { width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 20px; font-size: 0.9rem; }
    .acotacion-table th, .acotacion-table td { border: 1px solid #CBD5E1; padding: 8px 12px; text-align: center; }
    .acotacion-table th { background-color: #374151; color: white; font-weight: bold; }
    .bg-excelente { background-color: #10B981; color: white; font-weight: bold; }
    .bg-bueno { background-color: #FFFFFF; color: black; font-weight: bold; border: 1px solid #CBD5E1; }
    .bg-regular { background-color: #FEF08A; color: black; font-weight: bold; }
    .bg-malo { background-color: #EF4444; color: white; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Evaluación de Indicadores Epidemiológicos SUAVE / SUIVE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Herramienta de análisis epidemiológico por periodo, unidades y desglose por indicador</div>', unsafe_allow_html=True)

TARGET_UNITS = [
    "CHURUBUSCO", "CLIDDA", "COYOACAN", "DEL VALLE", 
    "DIVISION DEL NORTE", "DR. DARIO FERNANDEZ FIERRO", "DR. IGNACIO CHAVEZ", "ERMITA",
    "FUENTES BROTANTES", "HG DRA. MATILDE PETRA MONTOYA LAFRAGUA",
    "MILPA ALTA", "NARVARTE", "TLALPAN", "VILLA ALVARO OBREGON", "XOCHIMILCO"
]

def get_bg_color(val, ind_type):
    if val is None or pd.isna(val) or val == "NO APLICA":
        return ''
    if ind_type == "a":
        if val == 100.0: return 'background-color: #10B981; color: white; font-weight: bold;'
        elif 97.5 <= val <= 99.9: return 'background-color: #FFFFFF; color: black; font-weight: bold;'
        elif 95.0 <= val <= 97.4: return 'background-color: #FEF08A; color: black; font-weight: bold;'
        else: return 'background-color: #EF4444; color: white; font-weight: bold;'
    elif ind_type in ["b", "e"]:
        if 95.0 <= val <= 100.0: return 'background-color: #10B981; color: white; font-weight: bold;'
        elif 90.0 <= val <= 94.9: return 'background-color: #FFFFFF; color: black; font-weight: bold;'
        elif 80.0 <= val <= 89.9: return 'background-color: #FEF08A; color: black; font-weight: bold;'
        else: return 'background-color: #EF4444; color: white; font-weight: bold;'
    elif ind_type == "c":
        if 90.0 <= val <= 100.0: return 'background-color: #10B981; color: white; font-weight: bold;'
        elif 80.0 <= val <= 89.9: return 'background-color: #FFFFFF; color: black; font-weight: bold; border: 1px solid #CBD5E1;'
        elif 70.0 <= val <= 79.9: return 'background-color: #FEF08A; color: black; font-weight: bold;'
        else: return 'background-color: #EF4444; color: white; font-weight: bold;'
    elif ind_type == "f":
        if 90.0 <= val <= 100.0: return 'background-color: #10B981; color: white; font-weight: bold;'
        elif 80.0 <= val <= 89.9: return 'background-color: #FFFFFF; color: black; font-weight: bold; border: 1px solid #CBD5E1;'
        elif 60.0 <= val <= 79.9: return 'background-color: #FEF08A; color: black; font-weight: bold;'
        else: return 'background-color: #EF4444; color: white; font-weight: bold;'
    return ''

def get_hex_color(val, ind_type):
    if val is None or pd.isna(val) or val == "NO APLICA":
        return colors.white, colors.black
    bg_hex, text_color = colors.white, colors.black
    if ind_type == "a":
        if val == 100.0: bg_hex, text_color = colors.HexColor('#10B981'), colors.white
        elif 97.5 <= val <= 99.9: bg_hex, text_color = colors.white, colors.black
        elif 95.0 <= val <= 97.4: bg_hex, text_color = colors.HexColor('#FEF08A'), colors.black
        else: bg_hex, text_color = colors.HexColor('#EF4444'), colors.white
    elif ind_type in ["b", "e"]:
        if 95.0 <= val <= 100.0: bg_hex, text_color = colors.HexColor('#10B981'), colors.white
        elif 90.0 <= val <= 94.9: bg_hex, text_color = colors.white, colors.black
        elif 80.0 <= val <= 89.9: bg_hex, text_color = colors.HexColor('#FEF08A'), colors.black
        else: bg_hex, text_color = colors.HexColor('#EF4444'), colors.white
    elif ind_type == "c":
        if 90.0 <= val <= 100.0: bg_hex, text_color = colors.HexColor('#10B981'), colors.white
        elif 80.0 <= val <= 89.9: bg_hex, text_color = colors.white, colors.black
        elif 70.0 <= val <= 79.9: bg_hex, text_color = colors.HexColor('#FEF08A'), colors.black
        else: bg_hex, text_color = colors.HexColor('#EF4444'), colors.white
    elif ind_type == "f":
        if 90.0 <= val <= 100.0: bg_hex, text_color = colors.HexColor('#10B981'), colors.white
        elif 80.0 <= val <= 89.9: bg_hex, text_color = colors.white, colors.black
        elif 60.0 <= val <= 79.9: bg_hex, text_color = colors.HexColor('#FEF08A'), colors.black
        else: bg_hex, text_color = colors.HexColor('#EF4444'), colors.white
    return bg_hex, text_color

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_header_footer()
            super().showPage()
        super().save()

    def draw_header_footer(self):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor('#1F2937'))
        y = 755
        lines = [
            "REPRESENTACIÓN REGIONAL SUR",
            "SUBDELEGACIÓN MÉDICA",
            "DEPARTAMENTO DE ATENCIÓN MÉDICA",
            "COORDINACIÓN DE EPIDEMIOLOGÍA Y MEDICINA PREVENTIVA",
            "INDICADORES PARA EL SISTEMA ÚNICO AUTOMATIZADO DE VIGILANCIA EPIDEMIOLÓGICA (SUAVE)"
        ]
        for line in lines:
            self.drawCentredString(612 / 2.0, y, line)
            y -= 9
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.75)
        self.line(30, 705, 612 - 30, 705)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#6B7280'))
        self.drawRightString(612 - 30, 20, f"Página {self._pageNumber}")
        self.restoreState()

def generar_pdf_reporte(delegacion, anio, periodo_str, ultima_semana, trim_results_ind_a, trim_results_c_data, global_trim_results_f, delegational_b_trim, unit_rows_map, bloques_semanas, semanas_info):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=portrait(letter), rightMargin=25, leftMargin=25, topMargin=75, bottomMargin=35)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=13, textColor=colors.HexColor('#111827'), spaceAfter=3)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#4B5563'], spaceAfter=8)
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=10, textColor=colors.HexColor('#1F2937'], spaceBefore=8, spaceAfter=3)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=7.5, textColor=colors.HexColor('#374151'))
    
    story.append(Paragraph("Evaluación de Indicadores Epidemiológicos SUAVE / SUIVE", title_style))
    story.append(Paragraph(f"<b>Delegación:</b> {delegacion} | <b>Año:</b> {anio} | <b>Periodo:</b> {periodo_str}", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>INDICADOR EVALUADO:</b> Panorama General Comparativo (Trimestral)", normal_style))
    story.append(Paragraph(f"<b>AÑO:</b> {anio}", normal_style))
    story.append(Paragraph(f"<b>FECHA DE CORTE:</b> Día {ultima_semana}", normal_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Tabla Comparativa General (Panorama por Trimestres)", h2_style))
    
    gen_headers = ["Unidad Médica"]
    for t_name, _, _ in bloques_semanas:
        gen_headers.extend([f"{t_name[:3]}\nOport.", f"{t_name[:3]}\nCob.Op", f"{t_name[:3]}\nConsist.", f"{t_name[:3]}\nCalid."])
    
    table_data = [gen_headers]
    style_commands = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#374151')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 6.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
    ]
    
    row_idx = 1
    for unidad in TARGET_UNITS:
        row = [unidad]
        col_c = 1
        for t_name, _, _ in bloques_semanas:
            val_a = trim_results_ind_a.get(t_name, {}).get(unidad, np.nan)
            val_c = trim_results_c_data.get(t_name, {}).get(unidad, {}).get("porc", np.nan)
            
            row.append(f"{val_a:.1f}%" if pd.notna(val_a) else "-")
            bg_a, tc_a = get_hex_color(val_a, "a")
            if pd.notna(val_a):
                style_commands.append(('BACKGROUND', (col_c, row_idx), (col_c, row_idx), bg_a))
                style_commands.append(('TEXTCOLOR', (col_c, row_idx), (col_c, row_idx), tc_a))
            col_c += 1
            
            row.append("N/A")
            col_c += 1
            
            row.append(f"{val_c:.1f}%" if pd.notna(val_c) else "-")
            bg_c, tc_c = get_hex_color(val_c, "c")
            if pd.notna(val_c):
                style_commands.append(('BACKGROUND', (col_c, row_idx), (col_c, row_idx), bg_c))
                style_commands.append(('TEXTCOLOR', (col_c, row_idx), (col_c, row_idx), tc_c))
            col_c += 1
            
            row.append("N/A")
            col_c += 1
            
        table_data.append(row)
        row_idx += 1
        
    row_del = ["DELEGACIONAL"]
    col_c = 1
    for t_name, _, _ in bloques_semanas:
        vals_a = [trim_results_ind_a.get(t_name, {}).get(u, np.nan) for u in TARGET_UNITS]
        min_a = min([v for v in vals_a if pd.notna(v)], default=np.nan)
        avg_b = delegational_b_trim.get(t_name, np.nan)
        vals_c = [trim_results_c_data.get(t_name, {}).get(u, {}).get("porc", np.nan) for u in TARGET_UNITS]
        max_c = max([v for v in vals_c if pd.notna(v)], default=np.nan)
        global_cal = global_trim_results_f.get(t_name, {}).get("calidad", np.nan)
        
        row_del.append(f"{min_a:.1f}%" if pd.notna(min_a) else "-")
        bg_a, tc_a = get_hex_color(min_a, "a")
        if pd.notna(min_a):
            style_commands.append(('BACKGROUND', (col_c, row_idx), (col_c, row_idx), bg_a))
            style_commands.append(('TEXTCOLOR', (col_c, row_idx), (col_c, row_idx), tc_a))
        col_c += 1
        
        row_del.append(f"{avg_b:.1f}%" if pd.notna(avg_b) else "-")
        bg_b, tc_b = get_hex_color(avg_b, "b")
        if pd.notna(avg_b):
            style_commands.append(('BACKGROUND', (col_c, row_idx), (col_c, row_idx), bg_b))
            style_commands.append(('TEXTCOLOR', (col_c, row_idx), (col_c, row_idx), tc_b))
        col_c += 1
        
        row_del.append(f"{max_c:.1f}%" if pd.notna(max_c) else "-")
        bg_c, tc_c = get_hex_color(max_c, "c")
        if pd.notna(max_c):
            style_commands.append(('BACKGROUND', (col_c, row_idx), (col_c, row_idx), bg_c))
            style_commands.append(('TEXTCOLOR', (col_c, row_idx), (col_c, row_idx), tc_c))
        col_c += 1
        
        row_del.append(f"{global_cal:.1f}%" if pd.notna(global_cal) else "-")
        bg_f, tc_f = get_hex_color(global_cal, "f")
        if pd.notna(global_cal):
            style_commands.append(('BACKGROUND', (col_c, row_idx), (col_c, row_idx), bg_f))
            style_commands.append(('TEXTCOLOR', (col_c, row_idx), (col_c, row_idx), tc_f))
        col_c += 1
        
    table_data.append(row_del)
    style_commands.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#E2E8F0')))
    style_commands.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
    
    col_w = [110] + [45]*len(bloques_semanas)*4
    t_gen = Table(table_data, colWidths=col_w)
    t_gen.setStyle(TableStyle(style_commands))
    story.append(t_gen)
    story.append(Spacer(1, 10))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()

uploaded_file = st.file_uploader("📂 Sube tu archivo Excel de reportes SUIVE", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0, header=None)
        delegacion = df.iloc[0, 1] if df.shape[0] > 0 and df.shape[1] > 1 else "REPRESENTACIÓN REGIONAL SUR"
        anio = int(df.iloc[1, 1]) if df.shape[0] > 1 and df.shape[1] > 1 and str(df.iloc[1, 1]).isdigit() else 2024
        
        semanas_info = [] 
        if df.shape[0] > 4:
            for col_idx in range(1, df.shape[1] - 1):
                val_sem = df.iloc[4, col_idx]
                if pd.notna(val_sem):
                    try:
                        sem_num = int(float(str(val_sem).strip()))
                        semanas_info.append((col_idx, sem_num))
                    except ValueError:
                        continue
        
        total_semanas_reportadas = len(semanas_info)
        ultima_semana = semanas_info[-1][1] if semanas_info else 0
        periodo_str = f"Día {semanas_info[0][1]} a Día {ultima_semana} (Total: {total_semanas_reportadas} días)" if semanas_info else "No determinado"

        unit_rows_map = {}
        active_unit = None
        for idx, row in df.iterrows():
            v = row[0]
            if pd.notna(v):
                v_str = str(v).strip()
                if v_str in TARGET_UNITS:
                    active_unit = v_str
                    unit_rows_map[active_unit] = {}
                elif v_str == "CMN 20 DE NOVIEMBRE":
                    active_unit = None
                elif active_unit and pd.notna(v):
                    unit_rows_map[active_unit][str(v).strip()] = row

        def col_to_idx(col_str):
            col_str = col_str.upper()
            idx = 0
            for char in col_str:
                idx = idx * 26 + (ord(char) - ord('A') + 1)
            return idx - 1

        todos_bloques = [
            ("PRIMER TRIMESTRE", col_to_idx("B"), col_to_idx("N")),
            ("SEGUNDO TRIMESTRE", col_to_idx("O"), col_to_idx("AA")),
            ("TERCER TRIMESTRE", col_to_idx("AB"), col_to_idx("AN")),
            ("CUARTO TRIMESTRE", col_to_idx("AO"), col_to_idx("BA"))
        ]

        bloques_semanas = []
        max_col_excel = df.shape[1] - 1
        for t_name, start_col, end_col in todos_bloques:
            columnas_validas_en_bloque = [c for c in range(start_col, end_col + 1) if c <= max_col_excel and any(c == s[0] for s in semanas_info)]
            if len(columnas_validas_en_bloque) > 0:
                bloques_semanas.append((t_name, start_col, end_col))

        abs_results = {}
        for t_name, start_col, end_col in bloques_semanas:
            t_vals = {}
            for unidad in TARGET_UNITS:
                m_rows = unit_rows_map.get(unidad, {})
                row_casos_oportunos = m_rows.get("Unidades con casos oportunos", None)
                suma_bloque = 0.0
                tiene_datos_bloque = False
                if row_casos_oportunos is not None:
                    for c_idx in range(start_col, end_col + 1):
                        if c_idx < len(row_casos_oportunos) and pd.notna(row_casos_oportunos[c_idx]):
                            try:
                                val_c = float(row_casos_oportunos[c_idx])
                                suma_bloque += val_c
                                if val_c > 0:
                                    tiene_datos_bloque = True
                            except ValueError:
                                pass
                t_vals[unidad] = suma_bloque if tiene_datos_bloque else None
            abs_results[t_name] = t_vals

        trim_results_ind_a = {}
        for t_name, start_col, end_col in bloques_semanas:
            t_vals_a = {}
            for unidad in TARGET_UNITS:
                num_oportunas = abs_results[t_name].get(unidad, None)
                t_vals_a[unidad] = round((num_oportunas / 13.0) * 100, 2) if num_oportunas is not None else np.nan
            trim_results_ind_a[t_name] = t_vals_a

        trim_results_c_data = {}
        for t_name, start_col, end_col in bloques_semanas:
            t_vals_c = {}
            semanas_en_bloque = [s for s in semanas_info if start_col <= s[0] <= end_col]
            total_sem_trim = len(semanas_en_bloque) if len(semanas_en_bloque) > 0 else 13
            for unidad in TARGET_UNITS:
                m_rows = unit_rows_map.get(unidad, {})
                row_casos = m_rows.get("Casos oportunos", None)
                semanas_valores = []
                if row_casos is not None:
                    for c_idx in range(start_col, end_col + 1):
                        if c_idx < len(row_casos) and pd.notna(row_casos[c_idx]):
                            try:
                                semanas_valores.append(float(row_casos[c_idx]))
                            except ValueError:
                                pass
                if len(semanas_valores) > 0:
                    arr_vals = np.array(semanas_valores)
                    val_max_ref = max(np.mean(arr_vals), np.median(arr_vals))
                    if val_max_ref > 0:
                        lim_inf, lim_sup = 0.75 * val_max_ref, 1.25 * val_max_ref
                        semanas_consistentes = sum(1 for v in semanas_valores if lim_inf <= v <= lim_sup)
                        val_ind = (semanas_consistentes / total_sem_trim) * 100
                        t_vals_c[unidad] = {"sem_cons": int(semanas_consistentes), "tot_sem": int(total_sem_trim), "porc": round(val_ind, 2)}
                    else:
                        t_vals_c[unidad] = {"sem_cons": int(len(semanas_valores)) if sum(semanas_valores) == 0 else 0, "tot_sem": int(total_sem_trim), "porc": 100.0 if sum(semanas_valores) == 0 else 0.0}
                else:
                    t_vals_c[unidad] = {"sem_cons": 0, "tot_sem": int(total_sem_trim), "porc": np.nan}
            trim_results_c_data[t_name] = t_vals_c

        global_trim_results_f = {}
        for t_name, start_col, end_col in bloques_semanas:
            semanas_bloque_f = [s for s in semanas_info if start_col <= s[0] <= end_col]
            cob_semanas = []
            for col_idx, _ in semanas_bloque_f:
                suma_col_unidades = 0
                for u_check in TARGET_UNITS:
                    m_r = unit_rows_map.get(u_check, {})
                    row_c = m_r.get("Unidades con casos oportunos", None)
                    if row_c is not None and col_idx < len(row_c) and pd.notna(row_c[col_idx]):
                        try:
                            if float(row_c[col_idx]) > 0: suma_col_unidades += 1
                        except ValueError:
                            pass
                cob_semanas.append((suma_col_unidades / 15.0) * 100.0)
            global_cob = np.mean(cob_semanas) if len(cob_semanas) > 0 else 0.0
            vals_c_trim = [trim_results_c_data[t_name].get(u, {}).get("porc", np.nan) for u in TARGET_UNITS]
            delegational_c = max([v for v in vals_c_trim if pd.notna(v)], default=0.0)
            global_trim_results_f[t_name] = {"cobertura": round(global_cob, 2), "consistencia": round(delegational_c, 2), "calidad": round((global_cob + delegational_c) / 2.0, 2)}

        delegational_b_trim = {}
        for t_name, start_col, end_col in bloques_semanas:
            semanas_bloque_f = [s for s in semanas_info if start_col <= s[0] <= end_col]
            cob_semanas = []
            for col_idx, _ in semanas_bloque_f:
                suma_col_unidades = 0
                for u_check in TARGET_UNITS:
                    m_r = unit_rows_map.get(u_check, {})
                    row_c = m_r.get("Unidades con casos oportunos", None)
                    if row_c is not None and col_idx < len(row_c) and pd.notna(row_c[col_idx]):
                        try:
                            if float(row_c[col_idx]) > 0: suma_col_unidades += 1
                        except ValueError:
                            pass
                cob_semanas.append((suma_col_unidades / 15.0) * 100.0)
            delegational_b_trim[t_name] = round(np.mean(cob_semanas), 2) if len(cob_semanas) > 0 else 0.0

        st.markdown("---")
        pdf_bytes = generar_pdf_reporte(
            delegacion, anio, periodo_str, ultima_semana, 
            trim_results_ind_a, trim_results_c_data, 
            global_trim_results_f, delegational_b_trim, unit_rows_map, 
            bloques_semanas, semanas_info
        )
        st.download_button(
            label="📥 Descargar Reporte Completo en PDF",
            data=pdf_bytes,
            file_name=f"Reporte_SUIVE_{anio}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo Excel: {e}")
else:
    st.info("👈 Por favor, carga tu archivo Excel en la parte superior para comenzar el análisis.")
