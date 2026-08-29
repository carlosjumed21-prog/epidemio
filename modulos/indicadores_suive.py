import streamlit as st
import pandas as pd
import numpy as np
import io

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Evaluación Epidemiológica - SUIVE",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS personalizados para la interfaz web y la tabla de acotaciones
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #111827; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    .info-box { background-color: #F8FAFC; border-left: 4px solid #374151; padding: 12px; margin-bottom: 20px; border-radius: 4px; }
    
    /* Estilos para la tabla de acotaciones */
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

# Lista completa de unidades operativas oficiales (excluyendo CMN 20 DE NOVIEMBRE)
TARGET_UNITS = [
    "CHURUBUSCO", "CLIDDA", "COYOACAN", "DEL VALLE", 
    "DIVISION DEL NORTE", "DR. DARIO FERNANDEZ FIERRO", "DR. IGNACIO CHAVEZ", "ERMITA",
    "FUENTES BROTANTES", "HG DRA. MATILDE PETRA MONTOYA LAFRAGUA",
    "MILPA ALTA", "NARVARTE", "TLALPAN", "VILLA ALVARO OBREGON", "XOCHIMILCO"
]

def get_bg_color(val, ind_type):
    if val is None or pd.isna(val):
        return ''
    
    if ind_type == "a":
        if val == 100.0: return 'background-color: #10B981; color: white; font-weight: bold;'
        elif 97.5 <= val <= 99.9: return 'background-color: #FFFFFF; color: black; font-weight: bold;'
        elif 95.0 <= val <= 97.4: return 'background-color: #FEF08A; color: black; font-weight: bold;'
        else: return 'background-color: #EF4444; color: white; font-weight: bold;'
    elif ind_type in ["b", "e"]:
        # Umbrales específicos para Cobertura Oportuna (b)
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

# Subir archivo Excel
uploaded_file = st.file_uploader("📂 Sube tu archivo Excel de reportes SUIVE", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0, header=None)
        
        delegacion = df.iloc[0, 1] if df.shape[0] > 0 and df.shape[1] > 1 else "REPRESENTACIÓN REGIONAL SUR"
        anio = int(df.iloc[1, 1]) if df.shape[0] > 1 and df.shape[1] > 1 and str(df.iloc[1, 1]).isdigit() else 2024
        
        # Mapeo estricto de columnas y números de periodos/días desde la fila 5 (índice 4)
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

        # Validar cuáles trimestres tienen datos reales
        bloques_semanas = []
        max_col_excel = df.shape[1] - 1
        for t_name, start_col, end_col in todos_bloques:
            columnas_validas_en_bloque = [c for c in range(start_col, end_col + 1) if c <= max_col_excel and any(c == s[0] for s in semanas_info)]
            if len(columnas_validas_en_bloque) > 0:
                bloques_semanas.append((t_name, start_col, end_col))

        # Cálculo base unificado: Semanas/Días Notificadas Oportunamente (Valores Absolutos)
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

        # Pre-cálculo de Indicador A para todos los trimestres disponibles
        trim_results_ind_a = {}
        for t_name, start_col, end_col in bloques_semanas:
            t_vals_a = {}
            for unidad in TARGET_UNITS:
                num_oportunas = abs_results[t_name].get(unidad, None)
                if num_oportunas is None:
                    t_vals_a[unidad] = np.nan
                else:
                    t_vals_a[unidad] = round((num_oportunas / 13.0) * 100, 2)
            trim_results_ind_a[t_name] = t_vals_a

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
                "1er Trimestre (Días 1 a 13)",
                "2º Trimestre (Días 13 a 26)",
                "3er Trimestre (Días 26 a 39)",
                "4º Trimestre (Días 39 a 52)"
            ],
            index=0,
            key="sel_gen"
        )
        
        if trimestre_opcion_gen:
            def get_indices_semanas(opcion_periodo):
                if not opcion_periodo:
                    return [], ""
                if "1er Trimestre" in opcion_periodo or "Primer" in opcion_periodo:
                    return [item[0] for item in semanas_info if 1 <= item[1] <= 13], "1er Trimestre (Días 1-13)", "PRIMER TRIMESTRE"
                elif "2º Trimestre" in opcion_periodo or "Segundo" in opcion_periodo:
                    return [item[0] for item in semanas_info if 13 < item[1] <= 26], "2º Trimestre (Días 14-26)", "SEGUNDO TRIMESTRE"
                elif "3er Trimestre" in opcion_periodo or "Tercer" in opcion_periodo:
                    return [item[0] for item in semanas_info if 26 < item[1] <= 39], "3er Trimestre (Días 27-39)", "TERCER TRIMESTRE"
                elif "4º Trimestre" in opcion_periodo or "Cuarto" in opcion_periodo:
                    return [item[0] for item in semanas_info if 39 < item[1] <= 52], "4º Trimestre (Días 40-52)", "CUARTO TRIMESTRE"
                else:
                    return [item[0] for item in semanas_info], "Total", None

            indices_gen, etiqueta_gen, nombre_trimestre_match = get_indices_semanas(trimestre_opcion_gen)

            def calcular_resultados_periodo_gen(cols_indices, total_sem_bloque, trim_match):
                results = []
                for unidad in TARGET_UNITS:
                    m_rows = unit_rows_map.get(unidad, {})
                    
                    val_a_estatico = np.nan
                    if trim_match and trim_match in trim_results_ind_a:
                        val_a_estatico = trim_results_ind_a[trim_match].get(unidad, np.nan)
                    elif not trim_match and len(bloques_semanas) > 0:
                        vals_trim = [trim_results_ind_a[t[0]].get(unidad, np.nan) for t in bloques_semanas if pd.notna(trim_results_ind_a[t[0]].get(unidad, np.nan))]
                        if vals_trim:
                            val_a_estatico = round(sum(vals_trim) / len(vals_trim), 2)

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

                    row_casos_oportunos = m_rows.get("Unidades con casos oportunos", None)
                    suma_casos_oportunos = 0.0
                    if row_casos_oportunos is not None and len(cols_indices) > 0:
                        for c in cols_indices:
                            if pd.notna(row_casos_oportunos[c]):
                                try:
                                    suma_casos_oportunos += float(row_casos_oportunos[c])
                                except ValueError:
                                    pass

                    u_oportunas = get_ab_val("Unidades con casos oportunos")
                    u_habilitadas = get_ab_val("Unidades habilitadas")
                    if u_habilitadas == 0: u_habilitadas = float(len(TARGET_UNITS))
                    u_sin_notificar = get_ab_val("Unidades sin notificar")

                    base_hab = u_habilitadas if u_habilitadas > 0 else float(len(TARGET_UNITS))
                    divisor_calc = total_sem_bloque if total_sem_bloque > 0 else 13.0

                    ind_a = val_a_estatico if pd.notna(val_a_estatico) else round((suma_casos_oportunos / divisor_calc) * 100, 2)
                    ind_b = round((u_oportunas / base_hab) * 100, 2)
                    ind_c = ind_a
                    ind_d = round((u_sin_notificar / base_hab) * 100, 2)
                    excedente_rsm = max(0.0, ind_d - 5.0)
                    ind_e = round(max(0.0, ind_b - excedente_rsm), 2)
                    ind_f = round((ind_b + ind_c) / 2.0, 2)

                    results.append({
                        "Unidad": unidad,
                        "a": ind_a if pd.notna(ind_a) else None,
                        "b": ind_b,
                        "c": ind_c,
                        "d": ind_d,
                        "e": ind_e,
                        "f": ind_f
                    })
                return results

            raw_gen_res = calcular_resultados_periodo_gen(indices_gen, 13.0, nombre_trimestre_match)
            
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
        # 2. APARTADO DE ANÁLISIS DESGLOSADO POR INDICADOR (ESTRUCTURA SEPARADA)
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
                ind_label = "Indicador de Cobertura oportuna"
            elif "CONSISTENCIA" in indicador_seleccionado:
                ind_key = "c"
                ind_label = "Consistencia"
            else:
                ind_key = "f"
                ind_label = "Calidad"

            # CASO ESPECIAL PARA EL INDICADOR B: Sumatoria vertical por columna/día (denominador fijo 15)
            if ind_key == "b":
                st.markdown(f"**INDICADOR EVALUADO:** {ind_label} (Sumatoria Vertical Diaria / 15 Unidades)")
                st.markdown(f"**AÑO:** {anio}")
                st.markdown(f"**FECHA DE CORTE:** Día {ultima_semana}")

                st.markdown("""
                <div style="background-color: #374151; color: white; padding: 6px 12px; border-radius: 4px; margin-bottom: 15px; width: 310px; font-weight: bold; text-align: center;">
                    UNIDADES HABILITADAS POR SEMANA: 15
                </div>
                """, unsafe_allow_html=True)

                for t_name, start_col, end_col in bloques_semanas:
                    st.markdown(f"#### 📅 {t_name}")
                    
                    semanas_bloque = [s for s in semanas_info if start_col <= s[0] <= end_col]
                    if not semanas_bloque:
                        st.info(f"No hay registros activos para el {t_name}.")
                        continue

                    fila_unidades = {"MÉTRICA / DÍA": "UNIDADES CON NOTIFICACIÓN OPORTUNA"}
                    fila_indicador = {"MÉTRICA / DÍA": "INDICADOR DIARIO (%)"}

                    for col_idx, sem_num in semanas_bloque:
                        suma_vertical_unidad = 0
                        for unidad in TARGET_UNITS:
                            m_rows = unit_rows_map.get(unidad, {})
                            row_casos = m_rows.get("Unidades con casos oportunos", None)
                            if row_casos is not None and col_idx < len(row_casos) and pd.notna(row_casos[col_idx]):
                                try:
                                    val_c = float(row_casos[col_idx])
                                    if val_c > 0:
                                        suma_vertical_unidad += 1
                                except ValueError:
                                    pass
                        
                        dia_key = f"Día {sem_num}"
                        fila_unidades[dia_key] = suma_vertical_unidad
                        ind_val = round((suma_vertical_unidad / 15.0) * 100, 2)
                        fila_indicador[dia_key] = ind_val

                    df_semanal = pd.DataFrame([fila_unidades, fila_indicador])
                    
                    def style_semanal(row_data):
                        styles = [''] * len(row_data)
                        if row_data.name == 1:  # Fila de indicador
                            for i, col_name in enumerate(row_data.index):
                                if i > 0:
                                    val = row_data.iloc[i]
                                    if pd.notna(val):
                                        styles[i] = get_bg_color(val, ind_key)
                        return styles

                    styled_sem = df_semanal.style.format(
                        formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x <= 100 else (f"{x:.0f}" if isinstance(x, (int, float)) else str(x)),
                        subset=df_semanal.columns[1:]
                    ).apply(style_semanal, axis=1)

                    st.dataframe(styled_sem, use_container_width=True, hide_index=True)
                    st.markdown("---")

                # Acotación específica para el Indicador b (Cobertura Oportuna)
                st.markdown(f"""
                <table class="acotacion-table">
                    <tr>
                        <th>Indicador</th>
                        <th>Excelente</th>
                        <th>Bueno</th>
                        <th>Regular</th>
                        <th>Malo</th>
                    </tr>
                    <tr>
                        <td><b>{ind_label}</b></td>
                        <td class="bg-excelente">95.0 - 100%</td>
                        <td class="bg-bueno">90.0 - 94.9%</td>
                        <td class="bg-regular">80.0 - 89.9%</td>
                        <td class="bg-malo">≤ 79.9%</td>
                    </tr>
                </table>
                """, unsafe_allow_html=True)

            else:
                # ESTRUCTURA ESTÁNDAR PARA LOS DEMÁS INDICADORES (a, c, f)
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
                        elif ind_key == "c":
                            val_ind = (num_oportunas / 13.0) * 100
                        else: # Calidad (f)
                            ind_a_temp = (num_oportunas / 13.0) * 100
                            ind_b_temp = (u_oportunas / base_hab) * 100
                            val_ind = (ind_b_temp + ind_a_temp) / 2.0

                        t_vals_ind[unidad] = round(val_ind, 2)
                        
                    trim_results_abs[t_name] = t_vals_abs
                    trim_results_ind[t_name] = t_vals_ind

                tabla_sep_data = []
                for unidad in TARGET_UNITS:
                    fila = {"UNIDAD MÉDICA": unidad}
                    for t_name, _, _ in bloques_semanas:
                        fila[("DIAS NOTIFICADOS OPORTUNAMENTE", t_name)] = trim_results_abs[t_name].get(unidad, np.nan)
                    for t_name, _, _ in bloques_semanas:
                        fila[("INDICADOR", t_name)] = trim_results_ind[t_name].get(unidad, np.nan)
                    tabla_sep_data.append(fila)

                df_sep = pd.DataFrame(tabla_sep_data)

                st.markdown(f"**INDICADOR EVALUADO:** {ind_label}")
                st.markdown(f"**AÑO:** {anio}")
                st.markdown(f"**FECHA DE CORTE:** Día {ultima_semana}")

                st.markdown("""
                <div style="background-color: #374151; color: white; padding: 6px 12px; border-radius: 4px; margin-bottom: 15px; width: 220px; font-weight: bold; text-align: center;">
                    DÍAS POR TRIMESTRE: 13
                </div>
                """, unsafe_allow_html=True)

                sep_tuples = [("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE")]
                for t_name, _, _ in bloques_semanas:
                    sep_tuples.append(("DIAS NOTIFICADOS OPORTUNAMENTE", t_name))
                for t_name, _, _ in bloques_semanas:
                    sep_tuples.append(("INDICADOR", t_name))

                df_sep.columns = pd.MultiIndex.from_tuples(sep_tuples)

                def style_sep_table(row_data):
                    styles = [''] * len(row_data)
                    for i, col_name in enumerate(row_data.index):
                        if isinstance(col_name, tuple) and col_name[0] == "INDICADOR":
                            val = row_data.iloc[i]
                            if pd.notna(val):
                                styles[i] = get_bg_color(val, ind_key)
                    return styles

                styled_sep = df_sep.style.format(
                    formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x > 10 else (f"{x:.0f}" if isinstance(x, (int, float)) else "-"), 
                    subset=[col for col in df_sep.columns if col[0] != "UNIDAD MÉDICA / TRIMESTRE"]
                ).apply(style_sep_table, axis=1)

                st.dataframe(styled_sep, use_container_width=True, hide_index=True, height=580)

                # Mini tabla delegacional inferior
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
                    delegacional_dict[("DIAS NOTIFICADOS OPORTUNAMENTE", t_name)] = min_row_abs[t_name]
                for t_name, _, _ in bloques_semanas:
                    delegacional_dict[("INDICADOR", t_name)] = min_row_ind[t_name]

                df_del = pd.DataFrame([delegacional_dict])
                df_del.columns = pd.MultiIndex.from_tuples(sep_tuples)
                
                def style_delegational(row_data):
                    styles = [''] * len(row_data)
                    for i, col_name in enumerate(row_data.index):
                        if isinstance(col_name, tuple) and col_name[0] == "INDICADOR":
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

                st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado al {ultima_semana} día.</p>", unsafe_allow_html=True)

                st.markdown(f"""
                <table class="acotacion-table">
                    <tr>
                        <th>Indicador</th>
                        <th>Excelente</th>
                        <th>Bueno</th>
                        <th>Regular</th>
                        <th>Malo</th>
                    </tr>
                    <tr>
                        <td><b>{ind_label}</b></td>
                        <td class="bg-excelente">100%</td>
                        <td class="bg-bueno">97.5 - 99.9%</td>
                        <td class="bg-regular">95.0 - 97.4%</td>
                        <td class="bg-malo">≤ 94.9%</td>
                    </tr>
                </table>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo Excel: {e}")
else:
    st.info("👈 Por favor, carga tu archivo Excel en la parte superior para comenzar el análisis.")
