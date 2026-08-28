import streamlit as st
import pandas as pd
import numpy as np
import io
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Evaluación Epidemiológica - SUIVE",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    .info-box { background-color: #F8FAFC; border-left: 4px solid #1E3A8A; padding: 12px; margin-bottom: 20px; border-radius: 4px; }
    .legend-container { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
    .legend-item { padding: 8px 15px; border-radius: 6px; font-weight: bold; font-size: 0.9rem; text-align: center; }
    .legend-excelente { background-color: #10B981; color: white; }
    .legend-bueno { background-color: #FFFFFF; color: black; border: 1px solid #CBD5E1; }
    .legend-regular { background-color: #FEF08A; color: black; }
    .legend-malo { background-color: #EF4444; color: white; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Evaluación de Indicadores Epidemiológicos SUIVE - Trimestral</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Generador de Reportes Institucionales en Formato Word (.docx)</div>', unsafe_allow_html=True)

TARGET_UNITS = [
    "CHURUBUSCO", "CLIDDA", "CMN 20 DE NOVIEMBRE", "COYOACAN", "DEL VALLE", 
    "DIVISION DEL NORTE", "DR. DARIO FERNANDEZ FIERRO", "DR. IGNACIO CHAVEZ", "ERMITA",
    "FUENTES BROTANTES", "HG DRA. MATILDE PETRA MONTOYA LAFRAGUA",
    "MILPA ALTA", "NARVARTE", "TLALPAN", "VILLA ALVARO OBREGON", "XOCHIMILCO"
]

uploaded_file = st.file_uploader("📂 Sube tu archivo Excel de reportes SUIVE", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0, header=None)
        
        delegacion = df.iloc[0, 1] if df.shape[0] > 0 and df.shape[1] > 1 else "ISSSTE SUR"
        anio = int(df.iloc[1, 1]) if df.shape[0] > 1 and df.shape[1] > 1 and str(df.iloc[1, 1]).isdigit() else 2024
        
        # Validación de semanas del año (Bisiesto = 53, Normal = 52 -> Semestre/Trimestres dinámicos)
        es_bisiesto = (anio % 4 == 0 and anio % 100 != 0) or (anio % 400 == 0)
        total_semanas_anio = 53 if es_bisiesto else 52
        semanas_por_trimestre = total_semanas_anio / 4.0 # 4 trimestres o adaptado a 3 periodos según se requiera

        semanas_list = []
        if df.shape[0] > 4:
            for col_idx in range(1, 27):
                val_sem = df.iloc[4, col_idx]
                if pd.notna(val_sem):
                    semanas_list.append(str(val_sem).strip())
        
        total_semanas_reportadas = len(semanas_list)
        periodo_str = f"Semana {semanas_list[0]} a Semana {semanas_list[-1]} (Total analizado: {total_semanas_reportadas} semanas)" if semanas_list else "No determinado"

        st.markdown(f"""
        <div class="info-box">
            <h4>📋 Información del Periodo Analizado</h4>
            <ul>
                <li><b>Delegación:</b> {delegacion}</li>
                <li><b>Año:</b> {anio} {('(Bisiesto - 53 semanas)' if es_bisiesto else '(Normal - 52 semanas)')}</li>
                <li><b>Estructura de Semanas:</b> {periodo_str}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Mapeo de datos
        data_dict = {}
        current_unit = None
        metrics = {}
        
        for i, row in df.iterrows():
            val = row[0]
            ab_val = row[27] if len(row) > 27 else np.nan
            if pd.notna(val):
                val_str = str(val).strip()
                if val_str in TARGET_UNITS:
                    if current_unit:
                        data_dict[current_unit] = metrics
                    current_unit = val_str
                    metrics = {}
                elif current_unit:
                    if val_str in [
                        "Casos acumulados", "Casos oportunos", "Semanas acumuladas con casos",
                        "Unidades con casos oportunos", "Unidades habilitadas", "Unidades sin notificar"
                    ]:
                        metrics[val_str] = float(ab_val) if pd.notna(ab_val) else 0.0

        if current_unit:
            data_dict[current_unit] = metrics

        # Procesamiento para vista previa
        processed_results = []
        unidades_operativas = [u for u in TARGET_UNITS if u != "CMN 20 DE NOVIEMBRE"]
        TOTAL_SEMANAS_PERIODO = float(total_semanas_reportadas) if total_semanas_reportadas > 0 else 26.0

        for unidad in unidades_operativas:
            m = data_dict.get(unidad, {})
            semanas_casos = m.get("Semanas acumuladas con casos", 0.0)
            u_oportunas = m.get("Unidades con casos oportunos", 0.0)
            u_habilitadas = m.get("Unidades habilitadas", 16.0)
            u_sin_notificar = m.get("Unidades sin notificar", 0.0)
            
            base_hab = u_habilitadas if u_habilitadas > 0 else 16.0
            promedio_semanas_unidad = (semanas_casos / base_hab) if base_hab > 0 else 0.0
            
            ind_a = (promedio_semanas_unidad / TOTAL_SEMANAS_PERIODO) * 100
            ind_b = (u_oportunas / base_hab) * 100
            ind_c = (promedio_semanas_unidad / TOTAL_SEMANAS_PERIODO) * 100
            ind_d = (u_sin_notificar / base_hab) * 100
            excedente_rsm = max(0.0, ind_d - 5.0)
            ind_e = max(0.0, ind_b - excedente_rsm)
            ind_f = (ind_b + ind_c) / 2.0
            
            processed_results.append({
                "Unidad": unidad,
                "a) Cumplimiento u Oportunidad (%)": round(ind_a, 2),
                "b) Cobertura Oportuna (%)": round(ind_b, 2),
                "c) Consistencia (%)": round(ind_c, 2),
                "d) Reporta Sin Movimiento (RSM) (%)": round(ind_d, 2),
                "e) Cobertura Ajustada (%)": round(ind_e, 2),
                "f) Calidad (Descriptivo) (%)": round(ind_f, 2),
                "_raw": {"a": ind_a, "b": ind_b, "c": ind_c, "d": ind_d, "e": ind_e, "f": ind_f}
            })

        df_resumen = pd.DataFrame(processed_results)

        st.subheader("📊 Vista Previa de Indicadores Oficiales")
        display_df = df_resumen.drop(columns=["_raw"])
        st.dataframe(display_df, use_container_width=True)

        # -------------------------------------------------------------
        # FUNCIÓN DE GENERACIÓN DE WORD (.DOCX) CON DISEÑO INSTITUCIONAL
        # -------------------------------------------------------------
        def generar_documento_word():
            doc = Document()
            
            # Márgenes de página
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(1)
                section.bottom_margin = Inches(1)
                section.left_margin = Inches(1)
                section.right_margin = Inches(1)
            
            # Encabezado Institucional
            p_header = doc.add_paragraph()
            p_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_h1 = p_header.add_run("REPRESENTACIÓN REGIONAL SUR\nSUBDELEGACIÓN MÉDICA\nDEPARTAMENTO DE ATENCIÓN MÉDICA\nCOORDINACIÓN DE EPIDEMIOLOGÍA Y MEDICINA PREVENTIVA\n")
            run_h1.bold = True
            run_h1.font.size = Pt(9)
            run_h1.font.color.rgb = RGBColor(30, 58, 138)
            
            run_h2 = p_header.add_run("INDICADORES PARA EL SISTEMA ÚNICO AUTOMATIZADO DE VIGILANCIA EPIDEMIOLÓGICA (SUAVE)\n")
            run_h2.bold = True
            run_h2.font.size = Pt(10)
            
            run_anio = p_header.add_run(f"AÑO: {anio}\n")
            run_anio.bold = True
            run_anio.font.size = Pt(10)

            doc.add_paragraph().paragraph_format.space_after = Pt(6)

            # Título de la Tabla Principal
            p_title = doc.add_paragraph()
            p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r_title = p_title.add_run("RESUMEN GENERAL DE INDICADORES POR UNIDAD MÉDICA")
            r_title.bold = True
            r_title.font.size = Pt(11)

            # Creación de Tabla en Word
            table = doc.add_table(rows=1, cols=7)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False

            headers = [
                "Unidad Médica", 
                "Cumplimiento u Oportunidad", 
                "Cobertura Oportuna", 
                "Consistencia", 
                "RSM", 
                "Cobertura Ajustada", 
                "Calidad"
            ]
            
            hdr_cells = table.rows[0].cells
            for i, header_text in enumerate(headers):
                hdr_cells[i].text = header_text
                p = hdr_cells[i].paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.bold = True
                    run.font.size = Pt(8.5)
                    run.font.color.rgb = RGBColor(255, 255, 255)
                # Fondo azul institucional para cabecera
                shading = OxmlElement('w:shd')
                shading.set(qn('w:val'), 'clear')
                shading.set(qn('w:color'), 'auto')
                shading.set(qn('w:fill'), '1E3A8A')
                hdr_cells[i]._tc.get_or_add_tcPr().append(shading)

            # Llenado de filas con datos
            for idx, row in df_resumen.iterrows():
                row_cells = table.add_row().cells
                row_cells[0].text = str(row["Unidad"])
                row_cells[1].text = f"{row['a) Cumplimiento u Oportunidad (%)']:.2f}%"
                row_cells[2].text = f"{row['b) Cobertura Oportuna (%)']:.2f}%"
                row_cells[3].text = f"{row['c) Consistencia (%)']:.2f}%"
                row_cells[4].text = f"{row['d) Reporta Sin Movimiento (RSM) (%)']:.2f}%"
                row_cells[5].text = f"{row['e) Cobertura Ajustada (%)']:.2f}%"
                row_cells[6].text = f"{row['f) Calidad (Descriptivo) (%)']:.2f}%"
                
                for i, cell in enumerate(row_cells):
                    p = cell.paragraphs[0]
                    if i > 0:
                        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    else:
                        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    for run in p.runs:
                        run.font.size = Pt(8.5)

            doc.add_paragraph().paragraph_format.space_after = Pt(12)

            # Pie de página / Fuente oficial
            p_footer = doc.add_paragraph()
            r_footer = p_footer.add_run("Fuente: SINAVE-SUAVE. Cubo de indicadores, sistema institucional de vigilancia epidemiológica.")
            r_footer.italic = True
            r_footer.font.size = Pt(8)
            r_footer.font.color.rgb = RGBColor(100, 100, 100)

            # Guardar en memoria BytesIO
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            return bio

        # Botón de Descarga en Streamlit
        st.markdown("---")
        word_file = generar_documento_word()
        st.download_button(
            label="📥 Descargar Reporte Institucional en Word (.docx)",
            data=word_file,
            file_name=f"Reporte_SUAVE_{anio}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo para Word: {e}")
else:
    st.info("👈 Sube tu archivo Excel en la parte superior para habilitar la generación del reporte en Word.")
