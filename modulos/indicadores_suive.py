import streamlit as st
import pandas as pd
import numpy as np
import io

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Evaluación Epidemiológica - SUIVE",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS personalizados para la interfaz web y la tabla de acotaciones inferior
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    .info-box { background-color: #F8FAFC; border-left: 4px solid #1E3A8A; padding: 12px; margin-bottom: 20px; border-radius: 4px; }
    
    /* Estilos para la tabla de acotaciones inferior */
    .acotacion-table { width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 20px; font-size: 0.9rem; }
    .acotacion-table th, .acotacion-table td { border: 1px solid #CBD5E1; padding: 8px 12px; text-align: center; }
    .acotacion-table th { background-color: #1E3A8A; color: white; font-weight: bold; }
    .bg-excelente { background-color: #10B981; color: white; font-weight: bold; }
    .bg-bueno { background-color: #FFFFFF; color: black; font-weight: bold; border: 1px solid #CBD5E1; }
    .bg-regular { background-color: #FEF08A; color: black; font-weight: bold; }
    .bg-malo { background-color: #EF4444; color: white; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Evaluación de Indicadores Epidemiológicos SUAVE / SUIVE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Herramienta de análisis epidemiológico por periodo, unidades, desglose por indicador y reporte oficial PDF</div>', unsafe_allow_html=True)

# Lista completa de unidades operativas oficiales (excluyendo CMN 20 DE NOVIEMBRE)
TARGET_UNITS = [
    "CHURUBUSCO", "CLIDDA", "COYOACAN", "DEL VALLE", 
    "DIVISION DEL NORTE", "DR. DARIO FERNANDEZ FIERRO", "DR. IGNACIO CHAVEZ", "ERMITA",
    "FUENTES BROTANTES", "HG DRA. MATILDE PETRA MONTOYA LAFRAGUA",
    "MILPA ALTA", "NARVARTE", "TLALPAN", "VILLA ALVARO OBREGON", "XOCHIMILCO"
]

# Subir archivo Excel
uploaded_file = st.file_uploader("📂 Sube tu archivo Excel de reportes SUIVE", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0, header=None)
        
        delegacion = df.iloc[0, 1] if df.shape[0] > 0 and df.shape[1] > 1 else "REPRESENTACIÓN REGIONAL SUR"
        anio = int(df.iloc[1, 1]) if df.shape[0] > 1 and df.shape[1] > 1 and str(df.iloc[1, 1]).isdigit() else 2024
        
        # Mapeo estricto de columnas y números de semanas desde la fila 5 (índice 4)
        semanas_info = [] # Lista de tuplas: (índice_columna, número_de_semana)
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
        periodo_str = f"Semana {semanas_info[0][1]} a Semana {ultima_semana} (Total: {total_semanas_reportadas} semanas)" if semanas_info else "No determinado"

        st.markdown(f"""
        <div class="info-box">
            <h4>📋 Información General del Reporte</h4>
            <ul>
                <li><b>Delegación:</b> {delegacion}</li>
                <li><b>Año:</b> {anio}</li>
                <li><b>Periodo Registrado en Excel:</b> {periodo_str}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Extracción de filas por unidad del Excel (omitiendo CMN 20 DE NOVIEMBRE)
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
                    metric_name = v_str
                    unit_rows_map[active_unit][metric_name] = row

        # Conversor de letras de columnas a índices numéricos (A=0, B=1, etc.)
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

        # Validar cuáles trimestres tienen datos reales según las semanas detectadas en el archivo
        bloques_semanas = []
        max_col_excel = df.shape[1] - 1
        for t_name, start_col, end_col in todos_bloques:
            columnas_validas_en_bloque = [c for c in range(start_col, end_col + 1) if c <= max_col_excel and any(c == s[0] for s in semanas_info)]
            if len(columnas_validas_en_bloque) > 0:
                bloques_semanas.append((t_name, start_col, end_col))

        # Cálculo base unificado: Semanas Notificadas Oportunamente (Valores Absolutos) solo para trimestres con datos
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

        def get_bg_color(val, ind_type):
            if val is None or pd.isna(val):
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
                elif 80.0 <= val <= 89.9: return 'background-color: #FFFFFF; color: black; font-weight: bold;'
                elif 70.0 <= val <= 79.9: return 'background-color: #FEF08A; color: black; font-weight: bold;'
                else: return 'background-color: #EF4444; color: white; font-weight: bold;'
            elif ind_type == "d":
                if 0.0 <= val <= 1.9: return 'background-color: #10B981; color: white; font-weight: bold;'
                elif 2.0 <= val <= 4.9: return 'background-color: #FFFFFF; color: black; font-weight: bold;'
                elif 5.0 <= val <= 10.0: return 'background-color: #FEF08A; color: black; font-weight: bold;'
                else: return 'background-color: #EF4444; color: white; font-weight: bold;'
            elif ind_type == "f":
                if 90.0 <= val <= 100.0: return 'background-color: #10B981; color: white; font-weight: bold;'
                elif 80.0 <= val <= 89.9: return 'background-color: #FFFFFF; color: black; font-weight: bold;'
                elif 60.0 <= val <= 79.9: return 'background-color: #FEF08A; color: black; font-weight: bold;'
                else: return 'background-color: #EF4444; color: white; font-weight: bold;'
            return ''

        # ==========================================
        # 1. APARTADO GENERAL (PANORAMA COMPARATIVO - 6 INDICADORES)
        # ==========================================
        st.markdown("---")
        st.subheader("🗓️ Selección de Periodo / Trimestre (Panorama General)")
        
        trimestre_opcion_gen = st.selectbox(
            "Seleccione el periodo general a analizar:",
            [
                "",
                "Total",
                "1er Trimestre (Semanas 1 a 13)",
                "2º Trimestre (Semanas 13 a 26)",
                "3er Trimestre (Semanas 26 a 39)",
                "4º Trimestre (Semanas 39 a 52)"
            ],
            index=0,
            key="sel_gen"
        )
        
        if trimestre_opcion_gen:
            def get_indices_semanas(opcion_periodo):
                if not opcion_periodo:
                    return [], ""
                if "1er Trimestre" in opcion_periodo or "Primer" in opcion_periodo:
                    indices = [item[0] for item in semanas_info if 1 <= item[1] <= 13]
                    etiqueta = "1er Trimestre (Sem. 1-13)"
                elif "2º Trimestre" in opcion_periodo or "Segundo" in opcion_periodo:
                    indices = [item[0] for item in semanas_info if 13 < item[1] <= 26]
                    etiqueta = "2º Trimestre (Sem. 14-26)"
                elif "3er Trimestre" in opcion_periodo or "Tercer" in opcion_periodo:
                    indices = [item[0] for item in semanas_info if 26 < item[1] <= 39]
                    etiqueta = "3er Trimestre (Sem. 27-39)"
                elif "4º Trimestre" in opcion_periodo or "Cuarto" in opcion_periodo:
                    indices = [item[0] for item in semanas_info if 39 < item[1] <= 52]
                    etiqueta = "4º Trimestre (Sem. 40-52)"
                else:
                    indices = [item[0] for item in semanas_info]
                    etiqueta = "Total"
                return indices, etiqueta

            indices_gen, etiqueta_gen = get_indices_semanas(trimestre_opcion_gen)

            def calcular_resultados_periodo_gen(cols_indices, total_sem_bloque):
                results = []
                for unidad in TARGET_UNITS:
                    m_rows = unit_rows_map.get(unidad, {})
                    row_casos_oportunos = m_rows.get("Unidades con casos oportunos", None)
                    suma_casos_oportunos = 0.0
                    tiene_datos = False
                    if row_casos_oportunos is not None and len(cols_indices) > 0:
                        for c in cols_indices:
                            if pd.notna(row_casos_oportunos[c]):
                                try:
                                    val_c = float(row_casos_oportunos[c])
                                    suma_casos_oportunos += val_c
                                    if val_c > 0:
                                        tiene_datos = True
                                except ValueError:
                                    pass

                    if not tiene_datos and trimestre_opcion_gen != "Total":
                        results.append({
                            "Unidad": unidad, "a": None, "b": None, "c": None, "d": None, "e": None, "f": None
                        })
                        continue

                    def get_ab_val(metric_key):
                        r = m_rows.get(metric_key, None)
                        if r is not None:
                            for col_idx in range(len(r) - 1, 0, -1):
                                val_celda = r[col_idx]
                                try:
                                    if pd.notna(val_celda) and str(val_celda).strip() != "":
                                        return float(val_celda)
                                except ValueError:
                                    continue
                        return 0.0

                    u_oportunas = get_ab_val("Unidades con casos oportunos")
                    u_habilitadas = get_ab_val("Unidades habilitadas")
                    if u_habilitadas == 0: u_habilitadas = float(len(TARGET_UNITS))
                    u_sin_notificar = get_ab_val("Unidades sin notificar")

                    base_hab = u_habilitadas if u_habilitadas > 0 else float(len(TARGET_UNITS))
                    divisor_calc = total_sem_bloque if total_sem_bloque > 0 else 13.0

                    ind_a = (suma_casos_oportunos / divisor_calc) * 100
                    ind_b = (u_oportunas / base_hab) * 100
                    ind_c = (suma_casos_oportunos / divisor_calc) * 100
                    ind_d = (u_sin_notificar / base_hab) * 100
                    excedente_rsm = max(0.0, ind_d - 5.0)
                    ind_e = max(0.0, ind_b - excedente_rsm)
                    ind_f = (ind_b + ind_c) / 2.0

                    results.append({
                        "Unidad": unidad,
                        "a": round(ind_a, 2),
                        "b": round(ind_b, 2),
                        "c": round(ind_c, 2),
                        "d": round(ind_d, 2),
                        "e": round(ind_e, 2),
                        "f": round(ind_f, 2)
                    })
                return results

            raw_gen_res = calcular_resultados_periodo_gen(indices_gen, 13.0)
            
            processed_gen = []
            for item in raw_gen_res:
                processed_gen.append({
                    "Unidad": item["Unidad"],
                    "a) Cumplimiento u Oportunidad (%)": item["a"],
                    "b) Cobertura Oportuna (%)": item["b"],
                    "c) Consistencia (%)": item["c"],
                    "d) Reporta Sin Movimiento (RSM) (%)": item["d"],
                    "e) Cobertura Ajustada (%)": item["e"],
                    "f) Calidad (Descriptivo) (%)": item["f"],
                    "_raw": {"a": item["a"], "b": item["b"], "c": item["c"], "d": item["d"], "e": item["e"], "f": item["f"]}
                })
            df_gen = pd.DataFrame(processed_gen)

            def style_dataframe(row_data):
                styles = [''] * len(row_data)
                col_mapping = {
                    "a) Cumplimiento u Oportunidad (%)": "a",
                    "b) Cobertura Oportuna (%)": "b",
                    "c) Consistencia (%)": "c",
                    "d) Reporta Sin Movimiento (RSM) (%)": "d",
                    "e) Cobertura Ajustada (%)": "e",
                    "f) Calidad (Descriptivo) (%)": "f"
                }
                idx = row_data.name
                raw_dict = df_gen.loc[idx, "_raw"]
                for i, col_name in enumerate(row_data.index):
                    actual_col = col_name[1] if isinstance(col_name, tuple) else col_name
                    if actual_col in col_mapping:
                        itype = col_mapping[actual_col]
                        val = raw_dict[itype]
                        styles[i] = get_bg_color(val, itype)
                return styles

            st.subheader(f"📊 Tabla Comparativa General (6 Indicadores) — {etiqueta_gen}")
            display_df = df_gen.drop(columns=["_raw"])
            multi_columns = pd.MultiIndex.from_tuples([
                ("Unidades Operativas", "Unidad"),
                (etiqueta_gen, "a) Cumplimiento u Oportunidad (%)"),
                (etiqueta_gen, "b) Cobertura Oportuna (%)"),
                (etiqueta_gen, "c) Consistencia (%)"),
                (etiqueta_gen, "d) Reporta Sin Movimiento (RSM) (%)"),
                (etiqueta_gen, "e) Cobertura Ajustada (%)"),
                (etiqueta_gen, "f) Calidad (Descriptivo) (%)")
            ])
            display_df.columns = multi_columns
            styled_general = display_df.style.format(formatter=lambda x: f"{x:.2f}" if pd.notna(x) else "-", subset=pd.IndexSlice[:, display_df.columns[1:]]).apply(style_dataframe, axis=1)
            
            st.dataframe(styled_general, use_container_width=True, height=580)

        # ==========================================
        # 2. APARTADO DE ANÁLISIS DESGLOSADO POR INDICADOR (FUSIÓN: SEMANAS + INDICADOR POR TRIMESTRE)
        # ==========================================
        st.markdown("---")
        st.subheader("📈 Análisis Desglosado por Indicador")
        
        indicador_seleccionado = st.selectbox(
            "Habilite el indicador a analizar:",
            [
                "",
                "CUMPLIMIENTO U OPORTUNIDAD (a)",
                "COBERTURA OPORTUNA (b)",
                "CONSISTENCIA (c)",
                "CALIDAD (f)"
            ],
            index=0,
            key="sel_indicador"
        )
        
        if indicador_seleccionado and indicador_seleccionado != "":
            if "CUMPLIMIENTO" in indicador_seleccionado:
                ind_key = "a"
                ind_label = "Cumplimiento u Oportunidad"
            elif "COBERTURA" in indicador_seleccionado:
                ind_key = "b"
                ind_label = "Cobertura Oportuna"
            elif "CONSISTENCIA" in indicador_seleccionado:
                ind_key = "c"
                ind_label = "Consistencia"
            else:
                ind_key = "f"
                ind_label = "Calidad"

            trim_results_ind = {}
            trim_results_abs = {}
            
            for t_name, start_col, end_col in bloques_semanas:
                t_vals_ind = {}
                t_vals_abs = {}
                for unidad in TARGET_UNITS:
                    m_rows = unit_rows_map.get(unidad, {})
                    
                    def get_ab_val(metric_key):
                        r = m_rows.get(metric_key, None)
                        if r is not None:
                            for col_idx in range(len(r) - 1, 0, -1):
                                val_celda = r[col_idx]
                                try:
                                    if pd.notna(val_celda) and str(val_celda).strip() != "":
                                        return float(val_celda)
                                except ValueError:
                                    continue
                        return 0.0

                    u_oportunas = get_ab_val("Unidades con casos oportunos")
                    u_habilitadas = get_ab_val("Unidades habilitadas")
                    if u_habilitadas == 0: u_habilitadas = float(len(TARGET_UNITS))
                    base_hab = u_habilitadas if u_habilitadas > 0 else float(len(TARGET_UNITS))

                    num_oportunas = abs_results[t_name].get(unidad, None)
                    if num_oportunas is None:
                        t_vals_abs[unidad] = np.nan
                        t_vals_ind[unidad] = np.nan
                        continue

                    t_vals_abs[unidad] = num_oportunas

                    if ind_key == "a":
                        val_ind = (num_oportunas / 13.0) * 100
                    elif ind_key == "b":
                        val_ind = (u_oportunas / base_hab) * 100
                    elif ind_key == "c":
                        val_ind = (num_oportunas / 13.0) * 100
                    else: # Calidad (f)
                        ind_a_temp = (num_oportunas / 13.0) * 100
                        ind_b_temp = (u_oportunas / base_hab) * 100
                        val_ind = (ind_b_temp + ind_a_temp) / 2.0

                    t_vals_ind[unidad] = round(val_ind, 2)
                    
                trim_results_abs[t_name] = t_vals_abs
                trim_results_ind[t_name] = t_vals_ind

            # Construcción de la tabla fusionada por trimestres en parejas (Semanas Notificadas + Indicador)
            tabla_fusión_data = []
            for unidad in TARGET_UNITS:
                fila = {"UNIDAD MÉDICA": unidad}
                for t_name, _, _ in bloques_semanas:
                    fila[(t_name, "Semanas Notificadas Oportunamente")] = trim_results_abs[t_name].get(unidad, np.nan)
                    fila[(t_name, "Indicador")] = trim_results_ind[t_name].get(unidad, np.nan)
                tabla_fusión_data.append(fila)

            df_fusion = pd.DataFrame(tabla_fusión_data)

            st.markdown(f"**INDICADOR EVALUADO:** {ind_label}")
            st.markdown(f"**AÑO:** {anio}")
            st.markdown(f"**FECHA DE CORTE:** Semana {ultima_semana}")

            st.markdown("""
            <div style="background-color: #1E3A8A; color: white; padding: 6px 12px; border-radius: 4px; margin-bottom: 15px; width: 220px; font-weight: bold; text-align: center;">
                SEMANAS POR TRIMESTRE: 13
            </div>
            """, unsafe_allow_html=True)

            fusion_tuples = [("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE")]
            for t_name, _, _ in bloques_semanas:
                fusion_tuples.append((t_name, "SEMANAS NOTIFICADAS\nOPORTUNAMENTE"))
                fusion_tuples.append((t_name, "INDICADOR"))

            df_fusion.columns = pd.MultiIndex.from_tuples(fusion_tuples)

            def style_fusion_table(row_data):
                styles = [''] * len(row_data)
                for i, col_name in enumerate(row_data.index):
                    if isinstance(col_name, tuple) and col_name[1] == "INDICADOR":
                        val = row_data.iloc[i]
                        if pd.notna(val):
                            # Mapeo de color exacto según valor y umbrales del indicador
                            if ind_key == "a":
                                if val == 100.0: styles[i] = 'background-color: #10B981; color: white; font-weight: bold;'
                                elif 97.5 <= val <= 99.9: styles[i] = 'background-color: #FFFFFF; color: black; font-weight: bold;'
                                elif 95.0 <= val <= 97.4: styles[i] = 'background-color: #FEF08A; color: black; font-weight: bold;'
                                else: styles[i] = 'background-color: #EF4444; color: white; font-weight: bold;'
                            else:
                                styles[i] = get_bg_color(val, ind_key)
                return styles

            styled_fusion = df_fusion.style.format(
                formatter=lambda x: f"{x:.2f}" if pd.notna(x) else "-", 
                subset=[col for col in df_fusion.columns if col[0] != "UNIDAD MÉDICA / TRIMESTRE"]
            ).apply(style_fusion_table, axis=1)

            st.dataframe(styled_fusion, use_container_width=True, hide_index=True, height=580)

            # Mini tabla delegacional inferior (Mínimos registrados por trimestre)
            min_row_ind = {}
            min_row_abs = {}
            for t_name, _, _ in bloques_semanas:
                vals_ind = [trim_results_ind[t_name][u] for u in TARGET_UNITS if pd.notna(trim_results_ind[t_name][u])]
                vals_abs = [trim_results_abs[t_name][u] for u in TARGET_UNITS if pd.notna(trim_results_abs[t_name][u])]
                
                if vals_ind:
                    min_row_ind[t_name] = f"{min(vals_ind):.2f}"
                    min_row_abs[t_name] = f"{min(vals_abs):.0f}"
                else:
                    min_row_ind[t_name] = "-"
                    min_row_abs[t_name] = "-"

            delegacional_dict = {("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE"): "DELEGACIONAL"}
            for t_name, _, _ in bloques_semanas:
                delegacional_dict[(t_name, "SEMANAS NOTIFICADAS\nOPORTUNAMENTE")] = min_row_abs[t_name]
                delegacional_dict[(t_name, "INDICADOR")] = min_row_ind[t_name]

            df_del = pd.DataFrame([delegacional_dict])
            df_del.columns = pd.MultiIndex.from_tuples(fusion_tuples)
            
            def style_delegational(row_data):
                styles = [''] * len(row_data)
                for i, col_name in enumerate(row_data.index):
                    if isinstance(col_name, tuple) and col_name[1] == "INDICADOR":
                        raw_str = row_data[col_name]
                        if raw_str != "-":
                            try:
                                clean_val = float(raw_str)
                                styles[i] = get_bg_color(clean_val, ind_key)
                            except ValueError:
                                pass
                return styles

            styled_del = df_del.style.apply(style_delegational, axis=1)
            st.dataframe(styled_del, use_container_width=True, hide_index=True)

            # Pie de fuente requerido
            st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado al {ultima_semana} semana.</p>", unsafe_allow_html=True)

            # Acotación de evaluación idéntica a la imagen oficial
            st.markdown("""
            <div style="display: flex; justify-content: flex-end; margin-top: 30px;">
                <table style="border-collapse: collapse; font-size: 0.85rem; width: 320px;">
                    <tr>
                        <td rowspan="4" style="vertical-align: middle; font-weight: bold; text-align: right; padding-right: 15px;">EVALUACIÓN:</td>
                        <td style="background-color: #10B981; color: white; text-align: center; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1;">100 %</td>
                        <td style="text-align: center; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1;">=</td>
                        <td style="background-color: #10B981; color: white; text-align: center; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1;">Excelente</td>
                    </tr>
                    <tr>
                        <td style="background-color: #FFFFFF; color: black; text-align: center; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1;">97.5 - 99.9</td>
                        <td style="text-align: center; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1;">=</td>
                        <td style="background-color: #FFFFFF; color: black; text-align: center; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1;">Bueno</td>
                    </tr>
                    <tr>
                        <td style="background-color: #FEF08A; color: black; text-align: center; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1;">95.0 - 97.4</td>
                        <td style="text-align: center; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1;">=</td>
                        <td style="background-color: #FEF08A; color: black; text-align: center; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1;">Regular</td>
                    </tr>
                    <tr>
                        <td style="background-color: #EF4444; color: white; text-align: center; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1;">94.9 ó menos</td>
                        <td style="text-align: center; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1;">=</td>
                        <td style="background-color: #EF4444; color: white; text-align: center; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1;">Malo</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

            # ==========================================
            # BOTÓN DE GENERACIÓN DE REPORTE OFICIAL EN PDF (REPORTLAB)
            # ==========================================
            st.markdown("---")
            st.subheader("📑 Generación de Reporte Oficial en PDF")
            st.info("Haz clic en el botón para descargar el reporte institucional en formato PDF.")

            def generar_pdf_reportlab():
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=landscape(letter),
                    rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20
                )
                elements = []
                styles = getSampleStyleSheet()

                # Estilos personalizados
                title_style = ParagraphStyle(
                    'HeaderTitle',
                    parent=styles['Normal'],
                    fontName='Helvetica-Bold',
                    fontSize=8,
                    leading=10,
                    alignment=1,
                    textColor=colors.HexColor('#1E3A8A')
                )
                sub_title_style = ParagraphStyle(
                    'SubHeaderTitle',
                    parent=styles['Normal'],
                    fontName='Helvetica-Bold',
                    fontSize=9,
                    leading=12,
                    alignment=1,
                    textColor=colors.black
                )
                meta_style = ParagraphStyle(
                    'MetaText',
                    parent=styles['Normal'],
                    fontName='Helvetica-Bold',
                    fontSize=8,
                    leading=11
                )

                # Encabezado institucional
                elements.append(Paragraph("REPRESENTACIÓN REGIONAL SUR", title_style))
                elements.append(Paragraph("SUBDELEGACIÓN MÉDICA", title_style))
                elements.append(Paragraph("DEPARTAMENTO DE ATENCIÓN MÉDICA", title_style))
                elements.append(Paragraph("COORDINACIÓN DE EPIDEMIOLOGÍA Y MEDICINA PREVENTIVA", title_style))
                elements.append(Spacer(1, 10))
                
                elements.append(Paragraph("INDICADORES PARA EL SISTEMA ÚNICO AUTOMATIZADO DE VIGILANCIA EPIDEMIOLÓGICA (SUAVE)", sub_title_style))
                elements.append(Spacer(1, 10))

                # Metadatos y recuadro de semanas
                meta_data = [
                    [Paragraph(f"<b>INDICADOR EVALUADO:</b> {ind_label}", meta_style), Paragraph("<b>SEMANAS POR TRIMESTRE</b>", ParagraphStyle('BoxH', parent=title_style, textColor=colors.white))],
                    [Paragraph(f"<b>AÑO:</b> {anio}", meta_style), Paragraph("<b>13</b>", ParagraphStyle('BoxV', parent=sub_title_style, fontSize=14, textColor=colors.white, alignment=1))],
                    [Paragraph(f"<b>FECHA DE CORTE:</b> Semana {ultima_semana}", meta_style), ""]
                ]
                meta_table = Table(meta_data, colWidths=[400, 150])
                meta_table.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BACKGROUND', (1,0), (1,0), colors.HexColor('#1E3A8A')),
                    ('BACKGROUND', (1,1), (1,1), colors.HexColor('#1E3A8A')),
                    ('BOX', (1,0), (1,1), 1, colors.black),
                ]))
                elements.append(meta_table)
                elements.append(Spacer(1, 15))

                # Construcción de la tabla de datos principal
                table_headers_1 = ["UNIDAD MÉDICA / TRIMESTRE"]
                table_headers_2 = [""]
                for t_name, _, _ in bloques_semanas:
                    table_headers_1.extend([t_name, ""])
                    table_headers_2.extend(["SEMANAS NOTIFICADAS OPORTUNAMENTE", "INDICADOR"])

                table_data = [table_headers_1, table_headers_2]

                for unidad in TARGET_UNITS:
                    row = [unidad]
                    for t_name, _, _ in bloques_semanas:
                        val_abs = trim_results_abs[t_name].get(unidad, np.nan)
                        val_ind = trim_results_ind[t_name].get(unidad, np.nan)
                        abs_str = f"{val_abs:.0f}" if pd.notna(val_abs) else "-"
                        ind_str = f"{val_ind:.2f}" if pd.notna(val_ind) else "-"
                        row.extend([abs_str, ind_str])
                    table_data.append(row)

                # Fila Delegacional
                del_row = ["DELEGACIONAL"]
                for t_name, _, _ in bloques_semanas:
                    min_abs = min_row_abs[t_name]
                    min_ind = min_row_ind[t_name]
                    del_row.extend([min_abs, min_ind])
                table_data.append(del_row)

                # Estilos de tabla PDF
                t_style = [
                    ('BACKGROUND', (0,0), (-1,1), colors.HexColor('#1E3A8A')),
                    ('TEXTCOLOR', (0,0), (-1,1), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 7.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#444444')),
                    ('BACKGROUND', (0,2), (0,-2), colors.HexColor('#1E3A8A')),
                    ('TEXTCOLOR', (0,2), (0,-2), colors.white),
                    ('FONTNAME', (0,2), (0,-2), 'Helvetica-Bold'),
                    ('ALIGN', (0,2), (0,-2), 'LEFT'),
                    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#1E3A8A')),
                    ('TEXTCOLOR', (0,-1), (-1,-1), colors.white),
                    ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ]

                # Aplicar colores de semáforo dinámicos en las celdas de indicador del PDF
                col_idx_eval = 2
                for t_idx, (_, _, _) in enumerate(bloques_semanas):
                    c_ind = col_idx_eval + (t_idx * 2)
                    for row_idx in range(2, len(table_data)):
                        val_str = table_data[row_idx][c_ind]
                        if val_str != "-":
                            try:
                                v_float = float(val_str)
                                hex_c = get_hex_color(v_float, ind_key)
                                txt_c = colors.white if hex_c in ["#10B981", "#EF4444"] else colors.black
                                t_style.append(('BACKGROUND', (c_ind, row_idx), (c_ind, row_idx), colors.HexColor(hex_c)))
                                t_style.append(('TEXTCOLOR', (c_ind, row_idx), (c_ind, row_idx), txt_c))
                            except ValueError:
                                pass

                col_widths = [150] + [90, 70] * len(bloques_semanas)
                main_table = Table(table_data, colWidths=col_widths, repeatRows=2)
                main_table.setStyle(TableStyle(t_style))
                elements.append(main_table)
                elements.append(Spacer(1, 10))

                # Fuente y tabla de evaluación
                elements.append(Paragraph(f"Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado al {ultima_semana} semana.", ParagraphStyle('FText', fontName='Helvetica-Oblique', fontSize=7, textColor=colors.HexColor('#555555'))))
                
                doc.build(elements)
                buffer.seek(0)
                return buffer

            pdf_buffer = generar_pdf_reportlab()
            st.download_button(
                label="📥 Descargar Reporte Oficial en PDF",
                data=pdf_buffer,
                file_name=f"Reporte_SUAVE_{ind_label.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo Excel: {e}")
else:
    st.info("👈 Por favor, carga tu archivo Excel en la parte superior para comenzar el análisis y habilitar los reportes.")
