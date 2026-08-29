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

# Estilos CSS personalizados para la interfaz web
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

st.markdown('<div class="main-header">Evaluación de Indicadores Epidemiológicos SUAVE / SUIVE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Herramienta de análisis epidemiológico por periodo y unidades operativas</div>', unsafe_allow_html=True)

# Lista completa de las 16 unidades operativas oficiales
TARGET_UNITS = [
    "CHURUBUSCO", "CLIDDA", "CMN 20 DE NOVIEMBRE", "COYOACAN", "DEL VALLE", 
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
        periodo_str = f"Semana {semanas_info[0][1]} a Semana {semanas_info[-1][1]} (Total: {total_semanas_reportadas} semanas)" if semanas_info else "No determinado"

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

        # Extracción de filas por unidad del Excel
        unit_rows_map = {}
        active_unit = None
        for idx, row in df.iterrows():
            v = row[0]
            if pd.notna(v) and str(v).strip() in TARGET_UNITS:
                active_unit = str(v).strip()
                unit_rows_map[active_unit] = {}
            elif active_unit and pd.notna(v):
                metric_name = str(v).strip()
                unit_rows_map[active_unit][metric_name] = row

        # Selector de Periodo con la opción "Total"
        st.markdown("---")
        st.subheader("🗓️ Selección de Periodo / Trimestre")
        
        trimestre_opcion = st.selectbox(
            "Seleccione el periodo a analizar:",
            [
                "Total",
                "1er Trimestre (Semanas 1 a 13)",
                "2º Trimestre (Semanas 13 a 26)",
                "3er Trimestre (Semanas 26 a 39)",
                "4º Trimestre (Semanas 39 a 52)"
            ]
        )
        
        # Filtrado estricto de columnas según las semanas del Excel
        if "1er Trimestre" in trimestre_opcion:
            cols_trimestre_indices = [item[0] for item in semanas_info if 1 <= item[1] <= 13]
            rango_etiqueta = "1er Trimestre (Sem. 1-13)"
        elif "2º Trimestre" in trimestre_opcion:
            cols_trimestre_indices = [item[0] for item in semanas_info if 13 < item[1] <= 26]
            rango_etiqueta = "2º Trimestre (Sem. 14-26)"
        elif "3er Trimestre" in trimestre_opcion:
            cols_trimestre_indices = [item[0] for item in semanas_info if 26 < item[1] <= 39]
            rango_etiqueta = "3er Trimestre (Sem. 27-39)"
        elif "4º Trimestre" in trimestre_opcion:
            cols_trimestre_indices = [item[0] for item in semanas_info if 39 < item[1] <= 52]
            rango_etiqueta = "4º Trimestre (Sem. 40-52)"
        else:
            cols_trimestre_indices = [item[0] for item in semanas_info]
            rango_etiqueta = "Total"

        # Validación estricta sin simulación
        if trimestre_opcion != "Total" and len(cols_trimestre_indices) == 0:
            st.warning(f"⚠️ El archivo cargado no contiene datos registrados en la fila 5 para el bloque del {rango_etiqueta}. No se simularán datos.")
            stop_processing = True
        else:
            stop_processing = False

        if not stop_processing:
            TOTAL_SEMANAS_BLOQUE = float(len(cols_trimestre_indices)) if len(cols_trimestre_indices) > 0 else 26.0

            processed_results = []

            for unidad in TARGET_UNITS:
                m_rows = unit_rows_map.get(unidad, {})
                
                row_semanas_casos = m_rows.get("Semanas acumuladas con casos", None)
                if row_semanas_casos is not None and len(cols_trimestre_indices) > 0:
                    semanas_casos_bloque = sum([float(row_semanas_casos[c]) for c in cols_trimestre_indices if pd.notna(row_semanas_casos[c])])
                else:
                    semanas_casos_bloque = 0.0

                def get_ab_val(metric_key):
                    r = m_rows.get(metric_key, None)
                    if r is not None and len(r) > 27 and pd.notna(r[27]):
                        return float(r[27])
                    return 0.0

                u_oportunas = get_ab_val("Unidades con casos oportunos")
                u_habilitadas = get_ab_val("Unidades habilitadas")
                if u_habilitadas == 0: u_habilitadas = 16.0
                u_sin_notificar = get_ab_val("Unidades sin notificar")

                base_hab = u_habilitadas if u_habilitadas > 0 else 16.0
                promedio_semanas_unidad = (semanas_casos_bloque / base_hab) if base_hab > 0 else 0.0
                divisor_calc = TOTAL_SEMANAS_BLOQUE if TOTAL_SEMANAS_BLOQUE > 0 else 1.0

                ind_a = (promedio_semanas_unidad / divisor_calc) * 100
                ind_b = (u_oportunas / base_hab) * 100
                ind_c = (promedio_semanas_unidad / divisor_calc) * 100
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
                    "_raw": {
                        "a": ind_a, "b": ind_b, "c": ind_c, "d": ind_d, "e": ind_e, "f": ind_f
                    },
                    "_metrics": {
                        "Semanas con casos en el periodo": semanas_casos_bloque,
                        "Unidades con casos oportunos": u_oportunas,
                        "Unidades habilitadas": u_habilitadas,
                        "Unidades sin notificar": u_sin_notificar
                    }
                })

            df_resumen = pd.DataFrame(processed_results)

            def get_bg_color(val, ind_type):
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
                raw_dict = df_resumen.loc[idx, "_raw"]
                for i, col_name in enumerate(row_data.index):
                    actual_col = col_name[1] if isinstance(col_name, tuple) else col_name
                    if actual_col in col_mapping:
                        itype = col_mapping[actual_col]
                        val = raw_dict[itype]
                        styles[i] = get_bg_color(val, itype)
                return styles

            st.markdown("---")
            st.subheader(f"📊 Tabla Comparativa General — {rango_etiqueta}")
            
            display_df = df_resumen.drop(columns=["_raw", "_metrics"])
            
            multi_columns = pd.MultiIndex.from_tuples([
                ("Unidades Operativas", "Unidad"),
                (rango_etiqueta, "a) Cumplimiento u Oportunidad (%)"),
                (rango_etiqueta, "b) Cobertura Oportuna (%)"),
                (rango_etiqueta, "c) Consistencia (%)"),
                (rango_etiqueta, "d) Reporta Sin Movimiento (RSM) (%)"),
                (rango_etiqueta, "e) Cobertura Ajustada (%)"),
                (rango_etiqueta, "f) Calidad (Descriptivo) (%)")
            ])
            
            display_df.columns = multi_columns
            styled_general = display_df.style.format(formatter="{:.2f}", subset=pd.IndexSlice[:, display_df.columns[1:]]).apply(style_dataframe, axis=1)
            st.dataframe(styled_general, use_container_width=True)

            st.markdown("---")
            st.subheader("🏥 Datos del Periodo por Unidad Médica")
            
            unit_options = ["TODAS"] + TARGET_UNITS
            selected_unit = st.selectbox("Seleccione una Unidad Médica (o elija 'TODAS' para ver el desglose completo de datos):", unit_options)
            
            def render_unit_details(unit_name):
                unit_row = df_resumen[df_resumen["Unidad"] == unit_name].iloc[0]
                unit_metrics = unit_row["_metrics"]
                
                st.markdown(f"### 📍 Unidad: **{unit_name}**")
                st.markdown(f"##### Datos del Periodo ({rango_etiqueta})")
                
                var_df = pd.DataFrame(list(unit_metrics.items()), columns=["Métrica", "Valor en el Periodo"])
                st.dataframe(var_df, use_container_width=True, hide_index=True)
                st.markdown("---")

            if selected_unit == "TODAS":
                for u in TARGET_UNITS:
                    render_unit_details(u)
            else:
                render_unit_details(selected_unit)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo Excel: {e}")
else:
    st.info("👈 Por favor, carga tu archivo Excel en la parte superior para comenzar el análisis y habilitar la exportación.")
