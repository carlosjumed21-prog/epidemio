import streamlit as st
import pandas as pd
import numpy as np
import io

# Importaciones para generación de Word con python-docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Configuración de la página
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

# Función auxiliar para pintar celdas en Word de manera limpia
def set_cell_background(cell, fill_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_color)
    tcPr.append(shd)

def generar_word_reporte(delegacion, anio, periodo_str, ultima_semana, trim_results_ind_a, trim_results_c_data, global_trim_results_f, delegational_b_trim, unit_rows_map, bloques_semanas, semanas_info):
    doc = Document()
    
    # Configurar márgenes de página (Vertical)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
        # Encabezado institucional en cada página de Word
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        hp.text = (
            "REPRESENTACIÓN REGIONAL SUR\n"
            "SUBDELEGACIÓN MÉDICA\n"
            "DEPARTAMENTO DE ATENCIÓN MÉDICA\n"
            "COORDINACIÓN DE EPIDEMIOLOGÍA Y MEDICINA PREVENTIVA\n"
            "INDICADORES PARA EL SISTEMA ÚNICO AUTOMATIZADO DE VIGILANCIA EPIDEMIOLÓGICA (SUAVE)"
        )
        for run in hp.runs:
            run.font.name = 'Helvetica'
            run.font.size = Pt(7.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(31, 41, 55)

    # Título principal del documento
    doc.add_heading("Evaluación de Indicadores Epidemiológicos SUAVE / SUIVE", level=1)
    p_info = doc.add_paragraph(f"Delegación: {delegacion} | Año: {anio} | Periodo: {periodo_str}")
    p_info.runs[0].font.size = Pt(9)
    
    # Metadatos obligatorios
    doc.add_paragraph("INDICADOR EVALUADO: Panorama General Comparativo (Trimestral)", style='Normal').bold = True
    doc.add_paragraph(f"AÑO: {anio}", style='Normal')
    doc.add_paragraph(f"FECHA DE CORTE: Día {ultima_semana}", style='Normal')
    doc.add_paragraph("", style='Normal')

    # Tabla General en Word
    doc.add_heading("Tabla Comparativa General (Panorama por Trimestres)", level=2)
    
    headers = ["Unidad Médica"]
    for t_name, _, _ in bloques_semanas:
        headers.extend([f"{t_name[:3]} Oport.", f"{t_name[:3]} Cob.Op", f"{t_name[:3]} Consist.", f"{t_name[:3]} Calid."])
        
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], '374151')
        for run in hdr_cells[i].paragraphs[0].runs:
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.bold = True
            run.font.size = Pt(7.5)

    # Rellenar filas de unidades
    for unidad in TARGET_UNITS:
        row_cells = table.add_row().cells
        row_cells[0].text = unidad
        col_c = 1
        for t_name, _, _ in bloques_semanas:
            val_a = trim_results_ind_a.get(t_name, {}).get(unidad, np.nan)
            val_c = trim_results_c_data.get(t_name, {}).get(unidad, {}).get("porc", np.nan)
            
            row_cells[col_c].text = f"{val_a:.1f}%" if pd.notna(val_a) else "-"
            col_c += 1
            row_cells[col_c].text = "N/A"
            col_c += 1
            row_cells[col_c].text = f"{val_c:.1f}%" if pd.notna(val_c) else "-"
            col_c += 1
            row_cells[col_c].text = "N/A"
            col_c += 1

    # Fila Delegacional
    row_del_cells = table.add_row().cells
    row_del_cells[0].text = "DELEGACIONAL"
    col_c = 1
    for t_name, _, _ in bloques_semanas:
        vals_a = [trim_results_ind_a.get(t_name, {}).get(u, np.nan) for u in TARGET_UNITS]
        min_a = min([v for v in vals_a if pd.notna(v)], default=np.nan)
        avg_b = delegational_b_trim.get(t_name, np.nan)
        vals_c = [trim_results_c_data.get(t_name, {}).get(u, {}).get("porc", np.nan) for u in TARGET_UNITS]
        max_c = max([v for v in vals_c if pd.notna(v)], default=np.nan)
        global_cal = global_trim_results_f.get(t_name, {}).get("calidad", np.nan)
        
        row_del_cells[col_c].text = f"{min_a:.1f}%" if pd.notna(min_a) else "-"
        col_c += 1
        row_del_cells[col_c].text = f"{avg_b:.1f}%" if pd.notna(avg_b) else "-"
        col_c += 1
        row_del_cells[col_c].text = f"{max_c:.1f}%" if pd.notna(max_c) else "-"
        col_c += 1
        row_del_cells[col_c].text = f"{global_cal:.1f}%" if pd.notna(global_cal) else "-"
        col_c += 1

    for cell in row_del_cells:
        set_cell_background(cell, 'E2E8F0')
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.size = Pt(7.5)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# Subir archivo Excel en Streamlit
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
                                if val_c > 0: tiene_datos_bloque = True
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
                            try: semanas_valores.append(float(row_casos[c_idx]))
                            except ValueError: pass
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
                        except ValueError: pass
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
                        except ValueError: pass
                cob_semanas.append((suma_col_unidades / 15.0) * 100.0)
            delegational_b_trim[t_name] = round(np.mean(cob_semanas), 2) if len(cob_semanas) > 0 else 0.0

        st.markdown("---")
        word_bytes = generar_word_reporte(
            delegacion, anio, periodo_str, ultima_semana, 
            trim_results_ind_a, trim_results_c_data, 
            global_trim_results_f, delegational_b_trim, unit_rows_map, 
            bloques_semanas, semanas_info
        )
        st.download_button(
            label="📥 Descargar Reporte Completo en Word (.docx)",
            data=word_bytes,
            file_name=f"Reporte_SUIVE_{anio}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo Excel: {e}")
else:
    st.info("👈 Por favor, carga tu archivo Excel en la parte superior para comenzar el análisis.")
