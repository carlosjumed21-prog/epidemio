import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Evaluación Epidemiológica - SUIVE",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS para la interfaz y la vista de impresión oficial (PDF) con soporte de saltos de página
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #111827; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    .info-box { background-color: #F8FAFC; border-left: 4px solid #374151; padding: 12px; margin-bottom: 20px; border-radius: 4px; }
    
    .report-page {
        background-color: white;
        padding: 40px;
        color: #1E293B;
        font-family: Arial, sans-serif;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        margin-top: 30px;
        margin-bottom: 30px;
        page-break-after: always;
        break-after: page;
    }
    .institutional-header {
        text-align: center;
        border-bottom: 2px solid #374151;
        padding-bottom: 15px;
        margin-bottom: 25px;
    }
    .institutional-header h4 { font-size: 0.9rem; font-weight: bold; margin: 2px 0; color: #334155; }
    .institutional-header h5 { font-size: 0.8rem; font-weight: normal; margin: 2px 0; color: #475569; }
    .institutional-header h3 { font-size: 1rem; font-weight: bold; margin: 8px 0; color: #0F172A; }

    .acotacion-table { width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 20px; font-size: 0.9rem; font-family: Arial, sans-serif; }
    .acotacion-table th, .acotacion-table td { border: 1px solid #CBD5E1; padding: 8px 12px; text-align: center; }
    .acotacion-table th { background-color: #374151; color: white; font-weight: bold; }
    .bg-excelente { background-color: #10B981; color: white; font-weight: bold; }
    .bg-bueno { background-color: #FFFFFF; color: black; font-weight: bold; border: 1px solid #CBD5E1; }
    .bg-regular { background-color: #FEF08A; color: black; font-weight: bold; }
    .bg-malo { background-color: #EF4444; color: white; font-weight: bold; }

    @media print {
        body { background-color: white; }
        header, .stSidebar, .stFileUploader, .stButton, .main-header, .sub-header, .info-box, hr, stSelectbox {
            display: none !important;
        }
        .report-page {
            border: none;
            box-shadow: none;
            padding: 0;
            margin: 0;
            page-break-after: always;
            break-after: page;
        }
    }
</style>
""", unsafe_allow_html=True)

def render_institutional_header(titulo_extra=""):
    st.markdown(f"""
    <div class="institutional-header">
        <h4>REPRESENTACIÓN REGIONAL SUR[cite: 2]</h4>
        <h4>SUBDELEGACIÓN MÉDICA[cite: 2]</h4>
        <h4>DEPARTAMENTO DE ATENCIÓN MÉDICA[cite: 2]</h4>
        <h4>COORDINACIÓN DE EPIDEMIOLOGÍA Y MEDICINA PREVENTIVA[cite: 2]</h4>
        <h3>INDICADORES PARA EL SISTEMA ÚNICO AUTOMATIZADO DE VIGILANCIA EPIDEMIOLÓGICA (SUAVE)[cite: 2]</h3>
        {f"<h5>{titulo_extra}</h5>" if titulo_extra else ""}
        <h5>AÑO: 2024[cite: 2]</h5>
    </div>
    """, unsafe_allow_html=True)

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

def style_multi_table(row_data, is_delegacional=False):
    styles = [''] * len(row_data)
    for i, col_name in enumerate(row_data.index):
        if isinstance(col_name, tuple) and col_name[0] != "UNIDAD MÉDICA / TRIMESTRE":
            subcol = col_name[1]
            val = row_data.iloc[i]
            if pd.notna(val) and val != "NO APLICA":
                if subcol == "CUMPLIMIENTO U OPORTUNIDAD": styles[i] = get_bg_color(val, "a")
                elif subcol == "COBERTURA OPORTUNA" and is_delegacional: styles[i] = get_bg_color(val, "b")
                elif subcol == "CONSISTENCIA": styles[i] = get_bg_color(val, "c")
                elif subcol == "CALIDAD" and is_delegacional: styles[i] = get_bg_color(val, "f")
    return styles

st.markdown('<div class="main-header">Evaluación de Indicadores Epidemiológicos SUAVE / SUIVE[cite: 2]</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Herramienta de análisis epidemiológico por periodo, unidades y desglose por indicador</div>', unsafe_allow_html=True)

TARGET_UNITS = [
    "CHURUBUSCO", "CLIDDA", "COYOACAN", "DEL VALLE", 
    "DIVISION DEL NORTE", "DR. DARIO FERNANDEZ FIERRO", "DR. IGNACIO CHAVEZ", "ERMITA",
    "FUENTES BROTANTES", "HG DRA. MATILDE PETRA MONTOYA LAFRAGUA",
    "MILPA ALTA", "NARVARTE", "TLALPAN", "VILLA ALVARO OBREGON", "XOCHIMILCO"
]

uploaded_file = st.file_uploader("📂 Sube tu archivo Excel de reportes SUIVE", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0, header=None)
        
        delegacion = df.iloc[0, 1] if df.shape[0] > 0 and df.shape[1] > 1 else "REPRESENTACIÓN REGIONAL SUR"[cite: 2]
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
                    unit_rows_map[active_unit][v_str] = row

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
            if any(c <= max_col_excel and any(c == s[0] for s in semanas_info) for c in range(start_col, end_col + 1)):
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
                            except ValueError: pass
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
            total_sem_trim = len([s for s in semanas_info if start_col <= s[0] <= end_col]) or 13
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
                        t_vals_c[unidad] = {"sem_cons": semanas_consistentes, "tot_sem": total_sem_trim, "porc": round((semanas_consistentes / total_sem_trim) * 100, 2)}
                    else:
                        t_vals_c[unidad] = {"sem_cons": len(semanas_valores) if sum(semanas_valores) == 0 else 0, "tot_sem": total_sem_trim, "porc": 100.0 if sum(semanas_valores) == 0 else 0.0}
                else:
                    t_vals_c[unidad] = {"sem_cons": 0, "tot_sem": total_sem_trim, "porc": np.nan}
            trim_results_c_data[t_name] = t_vals_c

        global_trim_results_f = {}
        for t_name, start_col, end_col in bloques_semanas:
            semanas_bloque_f = [s for s in semanas_info if start_col <= s[0] <= end_col]
            cob_semanas = []
            for col_idx, _ in semanas_bloque_f:
                suma_col_unidades = sum(1 for u_check in TARGET_UNITS if unit_rows_map.get(u_check, {}).get("Unidades con casos oportunos", [None])[col_idx] is not None and pd.notna(unit_rows_map[u_check].get("Unidades con casos oportunos")[col_idx]) and float(unit_rows_map[u_check].get("Unidades con casos oportunos")[col_idx]) > 0)
                cob_semanas.append((suma_col_unidades / 15.0) * 100.0)
            global_cob = np.mean(cob_semanas) if len(cob_semanas) > 0 else 0.0
            delegational_c = max([trim_results_c_data[t_name].get(u, {}).get("porc", np.nan) for u in TARGET_UNITS if pd.notna(trim_results_c_data[t_name].get(u, {}).get("porc", np.nan))], default=0.0)
            global_trim_results_f[t_name] = {"cobertura": round(global_cob, 2), "consistencia": round(delegational_c, 2), "calidad": round((global_cob + delegational_c) / 2.0, 2)}

        delegational_b_trim = {}
        for t_name, start_col, end_col in bloques_semanas:
            semanas_bloque_f = [s for s in semanas_info if start_col <= s[0] <= end_col]
            cob_semanas = []
            for col_idx, _ in semanas_bloque_f:
                suma_col_unidades = sum(1 for u_check in TARGET_UNITS if unit_rows_map.get(u_check, {}).get("Unidades con casos oportunos", [None])[col_idx] is not None and pd.notna(unit_rows_map[u_check].get("Unidades con casos oportunos")[col_idx]) and float(unit_rows_map[u_check].get("Unidades con casos oportunos")[col_idx]) > 0)
                cob_semanas.append((suma_col_unidades / 15.0) * 100.0)
            delegational_b_trim[t_name] = round(np.mean(cob_semanas), 2) if len(cob_semanas) > 0 else 0.0

        # Tablas Generales
        general_table_data = []
        for unidad in TARGET_UNITS:
            fila = {("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE"): unidad}
            for t_name, _, _ in bloques_semanas:
                fila[(t_name, "CUMPLIMIENTO U OPORTUNIDAD")] = trim_results_ind_a.get(t_name, {}).get(unidad, np.nan)
                fila[(t_name, "COBERTURA OPORTUNA")] = "NO APLICA"
                fila[(t_name, "CONSISTENCIA")] = trim_results_c_data.get(t_name, {}).get(unidad, {}).get("porc", np.nan)
                fila[(t_name, "CALIDAD")] = "NO APLICA"
            general_table_data.append(fila)

        df_gen_multi = pd.DataFrame(general_table_data)
        gen_tuples = [("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE")]
        for t_name, _, _ in bloques_semanas:
            gen_tuples.extend([(t_name, "CUMPLIMIENTO U OPORTUNIDAD"), (t_name, "COBERTURA OPORTUNA"), (t_name, "CONSISTENCIA"), (t_name, "CALIDAD")])
        df_gen_multi.columns = pd.MultiIndex.from_tuples(gen_tuples)

        styled_gen_main = df_gen_multi.style.format(formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and pd.notna(x) else str(x), subset=[col for col in df_gen_multi.columns if col[0] != "UNIDAD MÉDICA / TRIMESTRE"]).apply(style_multi_table, axis=1, is_delegacional=False)

        fila_del = {("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE"): "DELEGACIONAL"}
        for t_name, _, _ in bloques_semanas:
            vals_a = [trim_results_ind_a.get(t_name, {}).get(u, np.nan) for u in TARGET_UNITS]
            min_a = min([v for v in vals_a if pd.notna(v)], default=np.nan)
            vals_c = [trim_results_c_data.get(t_name, {}).get(u, {}).get("porc", np.nan) for u in TARGET_UNITS]
            max_c = max([v for v in vals_c if pd.notna(v)], default=np.nan)
            
            fila_del[(t_name, "CUMPLIMIENTO U OPORTUNIDAD")] = min_a
            fila_del[(t_name, "COBERTURA OPORTUNA")] = delegational_b_trim.get(t_name, np.nan)
            fila_del[(t_name, "CONSISTENCIA")] = max_c
            fila_del[(t_name, "CALIDAD")] = global_trim_results_f.get(t_name, {}).get("calidad", np.nan)

        df_del_gen = pd.DataFrame([fila_del])
        df_del_gen.columns = pd.MultiIndex.from_tuples(gen_tuples)
        styled_del_gen = df_del_gen.style.format(formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and pd.notna(x) else str(x), subset=[col for col in df_del_gen.columns if col[0] != "UNIDAD MÉDICA / TRIMESTRE"]).apply(style_multi_table, axis=1, is_delegacional=True)

        # Interfaz Interactiva Principal
        st.markdown("---")
        st.subheader("📊 Tabla Comparativa General (Panorama por Trimestres)")
        st.dataframe(styled_gen_main, use_container_width=True, hide_index=True)
        st.dataframe(styled_del_gen, use_container_width=True, hide_index=True)
        st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado el 14 de octubre de 2024[cite: 2].</p>", unsafe_allow_html=True)

        # ==========================================
        # BOTÓN DE DESCARGA ÚNICO / DOCUMENTO PDF CONSOLIDADO AL FINAL
        # ==========================================
        st.markdown("---")
        st.markdown("### 📄 Documento PDF Consolidado (Listo para Imprimir / Descargar)")
        st.markdown("""
        <div style="background-color: #FEF08A; padding: 12px; border-radius: 5px; margin-bottom: 20px; text-align: center; font-weight: bold; color: #1E293B;">
            🖨️ Haz clic en tu navegador en <b>Ctrl + P</b> (o <b>Cmd + P</b> en Mac) y selecciona <b>"Guardar como PDF"</b> para descargar el reporte oficial completo con todas las páginas ordenadas y sus respectivas acotaciones institucionales.
        </div>
        """, unsafe_allow_html=True)

        # --- PÁGINA 1: GENERAL + ACOTACIONES GENERALES ---
        st.markdown('<div class="report-page">', unsafe_allow_html=True)
        render_institutional_header("PANORAMA GENERAL DE INDICADORES SUAVE")
        st.dataframe(styled_gen_main, use_container_width=True, hide_index=True)
        st.dataframe(styled_del_gen, use_container_width=True, hide_index=True)
        st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado el 14 de octubre de 2024[cite: 2].</p>", unsafe_allow_html=True)
        
        # Acotación General (Combinada)
        st.markdown("""
        <table class="acotacion-table">
            <tr>
                <th>Indicador / Categoría</th>
                <th>Excelente</th>
                <th>Bueno</th>
                <th>Regular</th>
                <th>Malo</th>
            </tr>
            <tr>
                <td><b>Cumplimiento u Oportunidad (a)</b></td>
                <td class="bg-excelente">100.0%[cite: 2]</td>
                <td class="bg-bueno">97.5 - 99.9%[cite: 2]</td>
                <td class="bg-regular">95.0 - 97.4%[cite: 2]</td>
                <td class="bg-malo">≤ 94.9%[cite: 2]</td>
            </tr>
            <tr>
                <td><b>Cobertura Oportuna (b) / Ajustada (e)</b></td>
                <td class="bg-excelente">95.0 - 100%[cite: 2]</td>
                <td class="bg-bueno">90.0 - 94.9%[cite: 2]</td>
                <td class="bg-regular">80.0 - 89.9%[cite: 2]</td>
                <td class="bg-malo">≤ 79.9%[cite: 2]</td>
            </tr>
            <tr>
                <td><b>Consistencia (c) / Calidad (f)</b></td>
                <td class="bg-excelente">90.0 - 100%[cite: 2]</td>
                <td class="bg-bueno">80.0 - 89.9%[cite: 2]</td>
                <td class="bg-regular">70.0 - 79.9% (f: 60-79.9)[cite: 2]</td>
                <td class="bg-malo">≤ 69.9% (f: ≤59.9)[cite: 2]</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- PÁGINA 2: INDICADOR A ---
        st.markdown('<div class="report-page">', unsafe_allow_html=True)
        render_institutional_header("INDICADOR EVALUADO: Cumplimiento u Oportunidad (a)")
        
        tabla_sep_data = []
        for unidad in TARGET_UNITS:
            fila = {"UNIDAD MÉDICA": unidad}
            for t_name, _, _ in bloques_semanas:
                fila[(t_name, "DIAS NOTIFICADOS OPORTUNAMENTE")] = abs_results[t_name].get(unidad, np.nan)
                fila[(t_name, "INDICADOR")] = trim_results_ind_a[t_name].get(unidad, np.nan)
            tabla_sep_data.append(fila)

        df_sep = pd.DataFrame(tabla_sep_data)
        sep_tuples = [("UNIDAD MÉDICA / TRIMESTRE", "UNIDAD MÉDICA / TRIMESTRE")]
        for t_name, _, _ in bloques_semanas:
            sep_tuples.extend([(t_name, "DIAS NOTIFICADOS OPORTUNAMENTE"), (t_name, "INDICADOR")])
        df_sep.columns = pd.MultiIndex.from_tuples(sep_tuples)

        def style_sep_table(row_data):
            styles = [''] * len(row_data)
            for i, col_name in enumerate(row_data.index):
                if isinstance(col_name, tuple) and col_name[1] == "INDICADOR" and pd.notna(row_data.iloc[i]):
                    styles[i] = get_bg_color(row_data.iloc[i], "a")
            return styles

        styled_sep = df_sep.style.format(formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x > 10 else (f"{x:.0f}" if isinstance(x, (int, float)) else "-"), subset=[col for col in df_sep.columns if col[1] == "INDICADOR"]).apply(style_sep_table, axis=1)
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
        styled_del_a = df_del_a.style.format(formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x > 10 else (f"{x:.0f}" if isinstance(x, (int, float)) else "-"), subset=[col for col in df_del_a.columns if col[1] == "INDICADOR"]).apply(style_sep_table, axis=1)
        st.dataframe(styled_del_a, use_container_width=True, hide_index=True)
        st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado el 14 de octubre de 2024[cite: 2].</p>", unsafe_allow_html=True)
        
        # Acotación A
        st.markdown("""
        <table class="acotacion-table">
            <tr>
                <th>Indicador</th>
                <th>Excelente</th>
                <th>Bueno</th>
                <th>Regular</th>
                <th>Malo</th>
            </tr>
            <tr>
                <td><b>Cumplimiento u Oportunidad (a)</b></td>
                <td class="bg-excelente">100.0%[cite: 2]</td>
                <td class="bg-bueno">97.5 - 99.9%[cite: 2]</td>
                <td class="bg-regular">95.0 - 97.4%[cite: 2]</td>
                <td class="bg-malo">≤ 94.9%[cite: 2]</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- PÁGINA 3: INDICADOR B ---
        st.markdown('<div class="report-page">', unsafe_allow_html=True)
        render_institutional_header("INDICADOR EVALUADO: Cobertura Oportuna (b)")
        st.markdown("UNIDADES HABILITADAS POR SEMANA: 15[cite: 2]")
        
        for t_name, start_col, end_col in bloques_semanas:
            st.markdown(f"#### 📅 {t_name}")
            semanas_bloque = [s for s in semanas_info if start_col <= s[0] <= end_col]
            if not semanas_bloque: continue

            fila_unidades, fila_indicador = {"MÉTRICA / DÍA": "UNIDADES CON NOTIFICACIÓN OPORTUNA"}, {"MÉTRICA / DÍA": "INDICADOR DIARIO (%)"}
            for col_idx, sem_num in semanas_bloque:
                suma_vertical_unidad = sum(1 for u in TARGET_UNITS if unit_rows_map.get(u, {}).get("Unidades con casos oportunos", [None])[col_idx] is not None and pd.notna(unit_rows_map[u].get("Unidades con casos oportunos")[col_idx]) and float(unit_rows_map[u].get("Unidades con casos oportunos")[col_idx]) > 0)
                fila_unidades[f"Día {sem_num}"] = suma_vertical_unidad
                fila_indicador[f"Día {sem_num}"] = round((suma_vertical_unidad / 15.0) * 100, 2)

            df_semanal = pd.DataFrame([fila_unidades, fila_indicador])
            styled_sem = df_semanal.style.format(formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x <= 100 else (f"{x:.0f}" if isinstance(x, (int, float)) else str(x)), subset=df_semanal.columns[1:])
            st.dataframe(styled_sem, use_container_width=True, hide_index=True)

        fila_del_b = {"MÉTRICA / DÍA": "DELEGACIONAL"}
        for t_name, start_col, end_col in bloques_semanas:
            avg_b = delegational_b_trim.get(t_name, np.nan)
            for _, sem_num in [s for s in semanas_info if start_col <= s[0] <= end_col]:
                fila_del_b[f"Día {sem_num}"] = avg_b

        df_del_b = pd.DataFrame([fila_del_b])
        styled_del_b = df_del_b.style.format(formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x <= 100 else str(x), subset=df_del_b.columns[1:])
        st.dataframe(styled_del_b, use_container_width=True, hide_index=True)
        st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado el 14 de octubre de 2024[cite: 2].</p>", unsafe_allow_html=True)
        
        # Acotación B
        st.markdown("""
        <table class="acotacion-table">
            <tr>
                <th>Indicador</th>
                <th>Excelente</th>
                <th>Bueno</th>
                <th>Regular</th>
                <th>Malo</th>
            </tr>
            <tr>
                <td><b>Cobertura Oportuna (b)</b></td>
                <td class="bg-excelente">95.0 - 100%[cite: 2]</td>
                <td class="bg-bueno">90.0 - 94.9%[cite: 2]</td>
                <td class="bg-regular">80.0 - 89.9%[cite: 2]</td>
                <td class="bg-malo">≤ 79.9%[cite: 2]</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- PÁGINA 4: INDICADOR C ---
        st.markdown('<div class="report-page">', unsafe_allow_html=True)
        render_institutional_header("INDICADOR EVALUADO: Consistencia (c)")
        
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
            c_tuples.extend([(t_name, "SEMANAS CONSISTENTES"), (t_name, "TOTAL SEMANAS"), (t_name, "%CONSISTENCIA")])
        df_c.columns = pd.MultiIndex.from_tuples(c_tuples)

        def style_c_table(row_data):
            styles = [''] * len(row_data)
            for i, col_name in enumerate(row_data.index):
                if isinstance(col_name, tuple) and col_name[1] == "%CONSISTENCIA" and pd.notna(row_data.iloc[i]):
                    styles[i] = get_bg_color(row_data.iloc[i], "c")
            return styles

        styled_c = df_c.style.format(formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x <= 100 else (f"{x:.0f}" if isinstance(x, (int, float)) else "-"), subset=[col for col in df_c.columns if col[1] == "%CONSISTENCIA"]).apply(style_c_table, axis=1)
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
        styled_del_c = df_del_c.style.format(formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x <= 100 else (f"{x:.0f}" if isinstance(x, (int, float)) else "-"), subset=[col for col in df_del_c.columns if col[1] == "%CONSISTENCIA"]).apply(style_c_table, axis=1)
        st.dataframe(styled_del_c, use_container_width=True, hide_index=True)
        st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado al 14 de octubre de 2024[cite: 2].</p>", unsafe_allow_html=True)
        
        # Acotación C
        st.markdown("""
        <table class="acotacion-table">
            <tr>
                <th>Indicador</th>
                <th>Excelente</th>
                <th>Bueno</th>
                <th>Regular</th>
                <th>Malo</th>
            </tr>
            <tr>
                <td><b>Consistencia (c)</b></td>
                <td class="bg-excelente">90.0 - 100%[cite: 2]</td>
                <td class="bg-bueno">80.0 - 89.9%[cite: 2]</td>
                <td class="bg-regular">70.0 - 79.9%[cite: 2]</td>
                <td class="bg-malo">≤ 69.9%[cite: 2]</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- PÁGINA 5: INDICADOR F ---
        st.markdown('<div class="report-page">', unsafe_allow_html=True)
        render_institutional_header("INDICADOR EVALUADO: Calidad (Descriptivo) (f)")
        
        tabla_f_data = [{"TRIMESTRE": t, "PORCENTAJE DE COBERTURA": global_trim_results_f[t]["cobertura"], "PORCENTAJE DE CONSISTENCIA": global_trim_results_f[t]["consistencia"], "INDICADOR DE CALIDAD": global_trim_results_f[t]["calidad"]} for t, _, _ in bloques_semanas]
        df_f = pd.DataFrame(tabla_f_data)
        
        def style_calidad_table(row_data):
            styles = [''] * len(row_data)
            for i, col_name in enumerate(row_data.index):
                if col_name == "INDICADOR DE CALIDAD" and pd.notna(row_data[col_name]):
                    styles[i] = get_bg_color(row_data[col_name], "f")
            return styles

        styled_f = df_f.style.format(formatter=lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else str(x), subset=["PORCENTAJE DE COBERTURA", "PORCENTAJE DE CONSISTENCIA", "INDICADOR DE CALIDAD"]).apply(style_calidad_table, axis=1)
        st.dataframe(styled_f, use_container_width=True, hide_index=True)
        st.markdown(f"<p style='font-size:0.8rem; color:#64748B; font-style:italic;'>Fuente: SINAVE-SUAVE. Cubo de indicadores, descargado al 14 de octubre de 2024[cite: 2].</p>", unsafe_allow_html=True)
        
        # Acotación F
        st.markdown("""
        <table class="acotacion-table">
            <tr>
                <th>Indicador</th>
                <th>Excelente</th>
                <th>Bueno</th>
                <th>Regular</th>
                <th>Malo</th>
            </tr>
            <tr>
                <td><b>Calidad (Descriptivo) (f)</b></td>
                <td class="bg-excelente">90.0 - 100%[cite: 2]</td>
                <td class="bg-bueno">80.0 - 89.9%[cite: 2]</td>
                <td class="bg-regular">60.0 - 79.9%[cite: 2]</td>
                <td class="bg-malo">≤ 59.9%[cite: 2]</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo Excel: {e}")
else:
    st.info("👈 Por favor, carga tu archivo Excel en la parte superior para comenzar el análisis.")
