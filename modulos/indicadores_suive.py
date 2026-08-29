import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Evaluación Epidemiológica - SUIVE",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS para la interfaz y para la vista de exportación/impresión oficial
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #111827; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    .info-box { background-color: #F8FAFC; border-left: 4px solid #374151; padding: 12px; margin-bottom: 20px; border-radius: 4px; }
    
    /* Estilos para el Encabezado Institucional Oficial del Reporte */
    .report-container {
        background-color: white;
        padding: 30px;
        color: #1E293B;
        font-family: Arial, sans-serif;
    }
    .institutional-header {
        text-align: center;
        border-bottom: 2px solid #374151;
        padding-bottom: 15px;
        margin-bottom: 20px;
    }
    .institutional-header h4 { font-size: 0.9rem; font-weight: bold; margin: 2px 0; color: #334155; }
    .institutional-header h5 { font-size: 0.8rem; font-weight: normal; margin: 2px 0; color: #475569; }
    .institutional-header h3 { font-size: 1rem; font-weight: bold; margin: 8px 0; color: #0F172A; }

    .acotacion-table { width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 20px; font-size: 0.9rem; }
    .acotacion-table th, .acotacion-table td { border: 1px solid #CBD5E1; padding: 8px 12px; text-align: center; }
    .acotacion-table th { background-color: #374151; color: white; font-weight: bold; }
    .bg-excelente { background-color: #10B981; color: white; font-weight: bold; }
    .bg-bueno { background-color: #FFFFFF; color: black; font-weight: bold; border: 1px solid #CBD5E1; }
    .bg-regular { background-color: #FEF08A; color: black; font-weight: bold; }
    .bg-malo { background-color: #EF4444; color: white; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def render_institutional_header(titulo_extra=""):
    st.markdown(f"""
    <div class="institutional-header">
        <h4>REPRESENTACIÓN REGIONAL SUR</h4>
        <h4>SUBDELEGACIÓN MÉDICA</h4>
        <h4>DEPARTAMENTO DE ATENCIÓN MÉDICA</h4>
        <h4>COORDINACIÓN DE EPIDEMIOLOGÍA Y MEDICINA PREVENTIVA</h4>
        <h3>INDICADORES PARA EL SISTEMA ÚNICO AUTOMATIZADO DE VIGILANCIA EPIDEMIOLÓGICA (SUAVE)</h3>
        {f"<h5>{titulo_extra}</h5>" if titulo_extra else ""}
        <h5>AÑO: 2024</h5>
    </div>
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
                if num_oportunas is None:
                    t_vals_a[unidad] = np.nan
                else:
                    t_vals_a[unidad] = round((num_oportunas / 13.0) * 100, 2)
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
                    prom = np.mean(arr_vals)
                    med = np.median(arr_vals)
                    val_max_ref = max(prom, med)
                    
                    if val_max_ref > 0:
                        lim_inf = 0.75 * val_max_ref
                        lim_sup = 1.25 * val_max_ref
                        semanas_consistentes = sum(1 for v in semanas_valores if lim_inf <= v <= lim_sup)
                        val_ind = (semanas_consistentes / total_sem_trim) * 100 if total_sem_trim > 0 else 0.0
                        
                        t_vals_c[unidad] = {
                            "sem_cons": int(semanas_consistentes),
                            "tot_sem": int(total_sem_trim),
                            "porc": round(val_ind, 2)
                        }
                    else:
                        t_vals_c[unidad] = {
                            "sem_cons": int(len(semanas_valores)) if sum(semanas_valores) == 0 else 0,
                            "tot_sem": int(total_sem_trim),
                            "porc": 100.0 if sum(semanas_valores) == 0 else 0.0
                        }
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
                            if float(row_c[col_idx]) > 0:
                                suma_col_unidades += 1
                        except ValueError:
                            pass
                cob_semanas.append((suma_col_unidades / 15.0) * 100.0)
            global_cob = np.mean(cob_semanas) if len(cob_semanas) > 0 else 0.0
            
            vals_c_trim = [trim_results_c_data[t_name].get(u, {}).get("porc", np.nan) for u in TARGET_UNITS]
            valid_c_trim = [v for v in vals_c_trim if pd.notna(v)]
            delegational_c = max(valid_c_trim) if valid_c_trim else 0.0
            
            global_cal = (global_cob + delegational_c) / 2.0
            
            global_trim_results_f[t_name] = {
                "cobertura": round(global_cob, 2),
                "consistencia": round(delegational_c, 2),
                "calidad": round(global_cal, 2)
            }

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
                            if float(row_c[col_idx]) > 0:
                                suma_col_unidades += 1
                        except ValueError:
                            pass
                cob_semanas.append((suma_col_unidades / 15.0) * 100.0)
            delegational_b_trim[t_name] = round(np.mean(cob_semanas), 2) if len(cob_semanas) > 0 else 0.0

        # ==========================================
        # BOTÓN DE DESCARGA / VISTA DE REPORTE OFICIAL
        # ==========================================
        st.markdown("---")
        st.subheader("📥 Exportar Reporte Oficial")
        
        if st.button("🖨️ Generar Vista Oficial para Impresión / PDF"):
            st.markdown("""
            <div style="background-color: #FEF08A; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: center; font-weight: bold;">
                💡 Tip de impresión: Presiona <code>Ctrl + P</code> (o <code>Cmd + P</code> en Mac) y selecciona "Guardar como PDF" para obtener tu documento oficial con el membrete y formato institucional.
            </div>
            """, unsafe_allow_html=True)

            # Contenedor con formato de impresión oficial idéntico al PDF de referencia
            st.markdown('<div class="report-container">', unsafe_allow_html=True)
            render_institutional_header("REPORTE CONSOLIDADO DE INDICADORES SUAVE")
            
            # Tabla general integrada en el reporte
            general_table_data = []
            for unidad in TARGET_UNITS:
                fila = {("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE"): unidad}
                for t_name, _, _ in bloques_semanas:
                    val_a = trim_results_ind_a.get(t_name, {}).get(unidad, np.nan)
                    val_c = trim_results_c_data.get(t_name, {}).get(unidad, {}).get("porc", np.nan)
                    
                    fila[(t_name, "CUMPLIMIENTO U OPORTUNIDAD")] = val_a
                    fila[(t_name, "COBERTURA OPORTUNA")] = "NO APLICA"
                    fila[(t_name, "CONSISTENCIA")] = val_c
                    fila[(t_name, "CALIDAD")] = "NO APLICA"
                general_table_data.append(fila)

            df_gen_multi = pd.DataFrame(general_table_data)
            gen_tuples = [("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE")]
            for t_name, _, _ in bloques_semanas:
                gen_tuples.append((t_name, "CUMPLIMIENTO U OPORTUNIDAD"))
                gen_tuples.append((t_name, "COBERTURA OPORTUNA"))
                gen_tuples.append((t_name, "CONSISTENCIA"))
                gen_tuples.append((t_name, "CALIDAD"))

            df_gen_multi.columns = pd.MultiIndex.from_tuples(gen_tuples)
            
            def style_multi_table(row_data, is_delegacional=False):
                styles = [''] * len(row_data)
                for i, col_name in enumerate(row_data.index):
                    if isinstance(col_name, tuple) and col_name[0] != "UNIDAD MÉDICA / TRIMESTRE":
                        subcol = col_name[1]
                        val = row_data.iloc[i]
                        if pd.notna(val) and val != "NO APLICA":
                            if subcol == "CUMPLIMIENTO U OPORTUNIDAD":
                                styles[i] = get_bg_color(val, "a")
                            elif subcol == "COBERTURA OPORTUNA" and is_delegacional:
                                styles[i] = get_bg_color(val, "b")
                            elif subcol == "CONSISTENCIA":
                                styles[i] = get_bg_color(val, "c")
                            elif subcol == "CALIDAD" and is_delegacional:
                                styles[i] = get_bg_color(val, "f")
                return styles

            styled_gen_main = df_gen_multi.style.format(
                formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and pd.notna(x) else str(x),
                subset=[col for col in df_gen_multi.columns if col[0] != "UNIDAD MÉDICA / TRIMESTRE"]
            ).apply(style_multi_table, axis=1, is_delegacional=False)

            st.dataframe(styled_gen_main, use_container_width=True, hide_index=True)

            # Fila Delegacional
            fila_del = {("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE"): "DELEGACIONAL"}
            for t_name, _, _ in bloques_semanas:
                vals_a = [trim_results_ind_a.get(t_name, {}).get(u, np.nan) for u in TARGET_UNITS]
                min_a = min([v for v in vals_a if pd.notna(v)], default=np.nan)
                avg_b = delegational_b_trim.get(t_name, np.nan)
                vals_c = [trim_results_c_data.get(t_name, {}).get(u, {}).get("porc", np.nan) for u in TARGET_UNITS]
                max_c = max([v for v in vals_c if pd.notna(v)], default=np.nan)
                global_cal = global_trim_results_f.get(t_name, {}).get("calidad", np.nan)
                
                fila_del[(t_name, "CUMPLIMIENTO U OPORTUNIDAD")] = min_a
                fila_del[(t_name, "COBERTURA OPORTUNA")] = avg_b
                fila_del[(t_name, "CONSISTENCIA")] = max_c
                fila_del[(t_name, "CALIDAD")] = global_cal

            df_del_gen = pd.DataFrame([fila_del])
            df_del_gen.columns = pd.MultiIndex.from_tuples(gen_tuples)
            styled_del_gen = df_del_gen.style.format(
                formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and pd.notna(x) else str(x),
                subset=[col for col in df_del_gen.columns if col[0] != "UNIDAD MÉDICA / TRIMESTRE"]
            ).apply(style_multi_table, axis=1, is_delegacional=True)

            st.dataframe(styled_del_gen, use_container_width=True, hide_index=True)
            st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado el 14 de octubre de 2024.</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ==========================================
        # 1. APARTADO GENERAL EN INTERFAZ
        # ==========================================
        st.markdown("---")
        st.subheader("📊 Tabla Comparativa General (Panorama por Trimestres)")
        general_table_data = []
        for unidad in TARGET_UNITS:
            fila = {("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE"): unidad}
            for t_name, _, _ in bloques_semanas:
                val_a = trim_results_ind_a.get(t_name, {}).get(unidad, np.nan)
                val_c = trim_results_c_data.get(t_name, {}).get(unidad, {}).get("porc", np.nan)
                
                fila[(t_name, "CUMPLIMIENTO U OPORTUNIDAD")] = val_a
                fila[(t_name, "COBERTURA OPORTUNA")] = "NO APLICA"
                fila[(t_name, "CONSISTENCIA")] = val_c
                fila[(t_name, "CALIDAD")] = "NO APLICA"
            general_table_data.append(fila)

        df_gen_multi = pd.DataFrame(general_table_data)
        gen_tuples = [("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE")]
        for t_name, _, _ in bloques_semanas:
            gen_tuples.append((t_name, "CUMPLIMIENTO U OPORTUNIDAD"))
            gen_tuples.append((t_name, "COBERTURA OPORTUNA"))
            gen_tuples.append((t_name, "CONSISTENCIA"))
            gen_tuples.append((t_name, "CALIDAD"))

        df_gen_multi.columns = pd.MultiIndex.from_tuples(gen_tuples)
        styled_gen_main = df_gen_multi.style.format(
            formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and pd.notna(x) else str(x),
            subset=[col for col in df_gen_multi.columns if col[0] != "UNIDAD MÉDICA / TRIMESTRE"]
        ).apply(style_multi_table, axis=1, is_delegacional=False)

        st.dataframe(styled_gen_main, use_container_width=True, hide_index=True)

        fila_del = {("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE"): "DELEGACIONAL"}
        for t_name, _, _ in bloques_semanas:
            vals_a = [trim_results_ind_a.get(t_name, {}).get(u, np.nan) for u in TARGET_UNITS]
            min_a = min([v for v in vals_a if pd.notna(v)], default=np.nan)
            avg_b = delegational_b_trim.get(t_name, np.nan)
            vals_c = [trim_results_c_data.get(t_name, {}).get(u, {}).get("porc", np.nan) for u in TARGET_UNITS]
            max_c = max([v for v in vals_c if pd.notna(v)], default=np.nan)
            global_cal = global_trim_results_f.get(t_name, {}).get("calidad", np.nan)
            
            fila_del[(t_name, "CUMPLIMIENTO U OPORTUNIDAD")] = min_a
            fila_del[(t_name, "COBERTURA OPORTUNA")] = avg_b
            fila_del[(t_name, "CONSISTENCIA")] = max_c
            fila_del[(t_name, "CALIDAD")] = global_cal

        df_del_gen = pd.DataFrame([fila_del])
        df_del_gen.columns = pd.MultiIndex.from_tuples(gen_tuples)
        styled_del_gen = df_del_gen.style.format(
            formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and pd.notna(x) else str(x),
            subset=[col for col in df_del_gen.columns if col[0] != "UNIDAD MÉDICA / TRIMESTRE"]
        ).apply(style_multi_table, axis=1, is_delegacional=True)

        st.dataframe(styled_del_gen, use_container_width=True, hide_index=True)
        st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado el 14 de octubre de 2024.</p>", unsafe_allow_html=True)

        # ==========================================
        # 2. APARTADO DE ANÁLISIS DESGLOSADO POR INDICADOR
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
                ind_label = "Calidad (Descriptivo)"

            if ind_key == "b":
                render_institutional_header("INDICADOR EVALUADO: Cobertura Oportuna")
                st.markdown(f"""
                <div style="background-color: #374151; color: white; padding: 6px 12px; border-radius: 4px; margin-bottom: 15px; width: 310px; font-weight: bold; text-align: center;">
                    UNIDADES HABILITADAS POR SEMANA: 15
                </div>
                """, unsafe_allow_html=True)

                for t_name, start_col, end_col in bloques_semanas:
                    st.markdown(f"#### 📅 {t_name}")
                    semanas_bloque = [s for s in semanas_info if start_col <= s[0] <= end_col]
                    if not semanas_bloque: continue

                    fila_unidades = {"MÉTRICA / DÍA": "UNIDADES CON NOTIFICACIÓN OPORTUNA"}
                    fila_indicador = {"MÉTRICA / DÍA": "INDICADOR DIARIO (%)"}

                    for col_idx, sem_num in semanas_bloque:
                        suma_vertical_unidad = 0
                        for unidad in TARGET_UNITS:
                            m_rows = unit_rows_map.get(unidad, {})
                            row_casos = m_rows.get("Unidades con casos oportunos", None)
                            if row_casos is not None and col_idx < len(row_casos) and pd.notna(row_casos[col_idx]):
                                try:
                                    if float(row_casos[col_idx]) > 0: suma_vertical_unidad += 1
                                except ValueError: pass
                        
                        dia_key = f"Día {sem_num}"
                        fila_unidades[dia_key] = suma_vertical_unidad
                        fila_indicador[dia_key] = round((suma_vertical_unidad / 15.0) * 100, 2)

                    df_semanal = pd.DataFrame([fila_unidades, fila_indicador])
                    def style_semanal(row_data):
                        styles = [''] * len(row_data)
                        if row_data.name == 1:
                            for i, col_name in enumerate(row_data.index):
                                if i > 0 and pd.notna(row_data.iloc[i]):
                                    styles[i] = get_bg_color(row_data.iloc[i], ind_key)
                        return styles

                    styled_sem = df_semanal.style.format(
                        formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x <= 100 else (f"{x:.0f}" if isinstance(x, (int, float)) else str(x)),
                        subset=df_semanal.columns[1:]
                    ).apply(style_semanal, axis=1)

                    st.dataframe(styled_sem, use_container_width=True, hide_index=True)
                    st.markdown("---")

                st.markdown("##### Resultado Delegacional (Promedio por Trimestre)")
                fila_del_b = {"MÉTRICA / DÍA": "DELEGACIONAL"}
                for t_name, start_col, end_col in bloques_semanas:
                    avg_b = delegational_b_trim.get(t_name, np.nan)
                    for _, sem_num in [s for s in semanas_info if start_col <= s[0] <= end_col]:
                        fila_del_b[f"Día {sem_num}"] = avg_b

                df_del_b = pd.DataFrame([fila_del_b])
                styled_del_b = df_del_b.style.format(
                    formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x <= 100 else str(x),
                    subset=df_del_b.columns[1:]
                )
                st.dataframe(styled_del_b, use_container_width=True, hide_index=True)
                st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado el 14 de octubre de 2024.</p>", unsafe_allow_html=True)

            elif ind_key == "c":
                render_institutional_header("INDICADOR EVALUADO: Consistencia")
                tabla_c_data = []
                for unidad in TARGET_UNITS:
                    fila = {"UNIDAD MÉDICA": unidad}
                    for t_name, _, _ in bloques_semanas:
                        dat = trim_results_c_data[t_name].get(unidad, {"sem_cons": 0, "tot_sem": 13, "porc": np.nan})
                        fila[(t_name, "SEMANAS CONSISTENTES")] = dat["sem_cons"]
                        fila[(t_name, "TOTAL SEMANAS")] = dat["tot_sem"]
                        fila[(t_name, "%CONSISTENCIA")] = dat["porc"]
                    tabla_c_data.append(fila)

                df_c = pd.DataFrame(tabla_c_data)
                c_tuples = [("UNIDAD MÉDICA", "UNIDAD MÉDICA")]
                for t_name, _, _ in bloques_semanas:
                    c_tuples.append((t_name, "SEMANAS CONSISTENTES"))
                    c_tuples.append((t_name, "TOTAL SEMANAS"))
                    c_tuples.append((t_name, "%CONSISTENCIA"))

                df_c.columns = pd.MultiIndex.from_tuples(c_tuples)
                
                def style_c_table(row_data):
                    styles = [''] * len(row_data)
                    for i, col_name in enumerate(row_data.index):
                        if isinstance(col_name, tuple) and col_name[1] == "%CONSISTENCIA":
                            val = row_data.iloc[i]
                            if pd.notna(val): styles[i] = get_bg_color(val, "c")
                    return styles

                styled_c = df_c.style.format(
                    formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x <= 100 else (f"{x:.0f}" if isinstance(x, (int, float)) else "-"),
                    subset=[col for col in df_c.columns if col[1] == "%CONSISTENCIA"]
                ).apply(style_c_table, axis=1)

                st.markdown("### 📋 Reporte de Consistencia por Unidad y Trimestre")
                st.dataframe(styled_c, use_container_width=True, hide_index=True)

                fila_delegacional = {"UNIDAD MÉDICA": "DELEGACIONAL"}
                for t_name, _, _ in bloques_semanas:
                    col_sc, col_ts, col_pc = (t_name, "SEMANAS CONSISTENTES"), (t_name, "TOTAL SEMANAS"), (t_name, "%CONSISTENCIA")
                    max_pc = df_c[col_pc].max()
                    match_row = df_c[col_pc][df_c[col_pc] == max_pc].index
                    r_idx = match_row[0] if len(match_row) > 0 else 0
                    
                    fila_delegacional[col_sc] = df_c.loc[r_idx, col_sc]
                    fila_delegacional[col_ts] = df_c.loc[r_idx, col_ts]
                    fila_delegacional[col_pc] = max_pc

                df_del_c = pd.DataFrame([fila_delegacional])
                df_del_c.columns = pd.MultiIndex.from_tuples(c_tuples)
                styled_del_c = df_del_c.style.format(
                    formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x <= 100 else (f"{x:.0f}" if isinstance(x, (int, float)) else "-"),
                    subset=[col for col in df_del_c.columns if col[1] == "%CONSISTENCIA"]
                ).apply(style_c_table, axis=1)

                st.dataframe(styled_del_c, use_container_width=True, hide_index=True)
                st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado al {ultima_semana} día.</p>", unsafe_allow_html=True)

            elif ind_key == "f":
                render_institutional_header("INDICADOR EVALUADO: Calidad (Descriptivo)")
                tabla_f_data = []
                for t_name, _, _ in bloques_semanas:
                    res_global = global_trim_results_f[t_name]
                    tabla_f_data.append({
                        "TRIMESTRE": t_name,
                        "PORCENTAJE DE COBERTURA": res_global["cobertura"],
                        "PORCENTAJE DE CONSISTENCIA": res_global["consistencia"],
                        "INDICADOR DE CALIDAD": res_global["calidad"]
                    })

                df_f = pd.DataFrame(tabla_f_data)
                def style_calidad_table(row_data):
                    styles = [''] * len(row_data)
                    for i, col_name in enumerate(row_data.index):
                        if col_name == "INDICADOR DE CALIDAD" and pd.notna(row_data[col_name]):
                            styles[i] = get_bg_color(row_data[col_name], "f")
                    return styles

                styled_f = df_f.style.format(
                    formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else str(x),
                    subset=["PORCENTAJE DE COBERTURA", "PORCENTAJE DE CONSISTENCIA", "INDICADOR DE CALIDAD"]
                ).apply(style_calidad_table, axis=1)

                st.markdown("### 📋 Reporte Global de Calidad (Delegacional)")
                st.dataframe(styled_f, use_container_width=True, hide_index=True)
                st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado al {ultima_semana} día.</p>", unsafe_allow_html=True)

            else:
                render_institutional_header("INDICADOR EVALUADO: Cumplimiento u Oportunidad")
                trim_results_ind, trim_results_abs = {}, {}
                
                for t_name, start_col, end_col in bloques_semanas:
                    t_vals_ind, t_vals_abs = {}, {}
                    for unidad in TARGET_UNITS:
                        m_rows = unit_rows_map.get(unidad, {})
                        row_casos_oportunos = m_rows.get("Unidades con casos oportunos", None)
                        suma_bloque = 0.0
                        if row_casos_oportunos is not None:
                            for c_idx in range(start_col, end_col + 1):
                                if c_idx < len(row_casos_oportunos) and pd.notna(row_casos_oportunos[c_idx]):
                                    try: suma_bloque += float(row_casos_oportunos[c_idx])
                                    except ValueError: pass
                        t_vals_abs[unidad] = suma_bloque
                        t_vals_ind[unidad] = round((suma_bloque / 13.0) * 100, 2)
                        
                    trim_results_abs[t_name] = t_vals_abs
                    trim_results_ind[t_name] = t_vals_ind

                tabla_sep_data = []
                for unidad in TARGET_UNITS:
                    fila = {"UNIDAD MÉDICA": unidad}
                    for t_name, _, _ in bloques_semanas:
                        fila[(t_name, "DIAS NOTIFICADOS OPORTUNAMENTE")] = trim_results_abs[t_name].get(unidad, np.nan)
                        fila[(t_name, "INDICADOR")] = trim_results_ind[t_name].get(unidad, np.nan)
                    tabla_sep_data.append(fila)

                df_sep = pd.DataFrame(tabla_sep_data)
                sep_tuples = [("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE")]
                for t_name, _, _ in bloques_semanas:
                    sep_tuples.append((t_name, "DIAS NOTIFICADOS OPORTUNAMENTE"))
                    sep_tuples.append((t_name, "INDICADOR"))

                df_sep.columns = pd.MultiIndex.from_tuples(sep_tuples)

                def style_sep_table(row_data):
                    styles = [''] * len(row_data)
                    for i, col_name in enumerate(row_data.index):
                        if isinstance(col_name, tuple) and col_name[1] == "INDICADOR" and pd.notna(row_data.iloc[i]):
                            styles[i] = get_bg_color(row_data.iloc[i], ind_key)
                    return styles

                styled_sep = df_sep.style.format(
                    formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x > 10 else (f"{x:.0f}" if isinstance(x, (int, float)) else "-"), 
                    subset=[col for col in df_sep.columns if col[1] == "INDICADOR"]
                ).apply(style_sep_table, axis=1)

                st.dataframe(styled_sep, use_container_width=True, hide_index=True)

                fila_delegacional_a = {"UNIDAD MÉDICA": "DELEGACIONAL"}
                for t_name, _, _ in bloques_semanas:
                    col_abs, col_ind = (t_name, "DIAS NOTIFICADOS OPORTUNAMENTE"), (t_name, "INDICADOR")
                    min_ind = df_sep[col_ind].min()
                    match_row = df_sep[col_ind][df_sep[col_ind] == min_ind].index
                    r_idx = match_row[0] if len(match_row) > 0 else 0
                    
                    fila_delegacional_a[col_abs] = df_sep.loc[r_idx, col_abs]
                    fila_delegacional_a[col_ind] = min_ind

                df_del_a = pd.DataFrame([fila_delegacional_a])
                df_del_a.columns = pd.MultiIndex.from_tuples(sep_tuples)
                styled_del_a = df_del_a.style.format(
                    formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x > 10 else (f"{x:.0f}" if isinstance(x, (int, float)) else "-"), 
                    subset=[col for col in df_del_a.columns if col[1] == "INDICADOR"]
                ).apply(style_sep_table, axis=1)

                st.dataframe(styled_del_a, use_container_width=True, hide_index=True)
                st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado al {ultima_semana} día.</p>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo Excel: {e}")
else:
    st.info("👈 Por favor, carga tu archivo Excel en la parte superior para comenzar el análisis.")
