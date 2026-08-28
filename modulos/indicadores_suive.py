import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Evaluación Epidemiológica - SUIVE",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .info-box {
        background-color: #F8FAFC;
        border-left: 4px solid #1E3A8A;
        padding: 12px;
        margin-bottom: 20px;
        border-radius: 4px;
    }
    .legend-container {
        display: flex;
        gap: 15px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .legend-item {
        padding: 8px 15px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.9rem;
        text-align: center;
    }
    .legend-excelente { background-color: #10B981; color: white; }
    .legend-bueno { background-color: #FFFFFF; color: black; border: 1px solid #CBD5E1; }
    .legend-regular { background-color: #FEF08A; color: black; }
    .legend-malo { background-color: #EF4444; color: white; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Evaluación de Indicadores Epidemiológicos SUIVE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Herramienta de análisis, metadatos y semaforización por unidad médica</div>', unsafe_allow_html=True)

# Lista exacta de unidades requeridas
TARGET_UNITS = [
    "CHURUBUSCO", "CLIDDA", "COYOACAN", "DEL VALLE", "DIVISION DEL NORTE",
    "DR. DARIO FERNANDEZ FIERRO", "DR. IGNACIO CHAVEZ", "ERMITA",
    "FUENTES BROTANTES", "HG DRA. MATILDE PETRA MONTOYA LAFRAGUA",
    "MILPA ALTA", "NARVARTE", "TLALPAN", "VILLA ALVARO OBREGON", "XOCHIMILCO"
]

# Subir archivo Excel
uploaded_file = st.file_uploader("📂 Sube tu archivo Excel de reportes SUIVE", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Leer el archivo Excel sin importar el nombre
        df = pd.read_excel(uploaded_file, sheet_name=0, header=None)
        
        # Extracción de Metadatos de Cabecera
        delegacion = df.iloc[0, 1] if df.shape[0] > 0 and df.shape[1] > 1 else "No especificado"
        anio = df.iloc[1, 1] if df.shape[0] > 1 and df.shape[1] > 1 else "No especificado"
        
        # Periodo registrado: conteo de semanas en fila 5 (índice 4), desde columna B (índice 1) hasta AA (índice 26) = 26 semanas
        semanas_list = []
        if df.shape[0] > 4:
            for col_idx in range(1, 27): # Columnas B a AA
                val_sem = df.iloc[4, col_idx]
                if pd.notna(val_sem):
                    semanas_list.append(str(val_sem).strip())
        
        total_semanas_reportadas = len(semanas_list)
        periodo_str = f"Semana {semanas_list[0]} a Semana {semanas_list[-1]} (Total: {total_semanas_reportadas} semanas)" if semanas_list else "No determinado"

        # Mostrar Panel de Metadatos Generales
        st.markdown(f"""
        <div class="info-box">
            <h4>📋 Información General del Reporte</h4>
            <ul>
                <li><b>Delegación:</b> {delegacion}</li>
                <li><b>Año:</b> {anio}</li>
                <li><b>Periodo Registrado:</b> {periodo_str}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Mapeo y extracción de datos por unidad
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
                elif current_unit and val_str in [
                    "Casos acumulados", "Casos oportunos", "Semanas acumuladas con casos",
                    "Unidades con casos oportunos", "Unidades habilitadas", "Unidades sin notificar"
                ]:
                    metrics[val_str] = float(ab_val) if pd.notna(ab_val) else 0.0

        if current_unit:
            data_dict[current_unit] = metrics

        if not data_dict:
            st.error("No se encontraron unidades válidas en la Columna A con los nombres esperados.")
        else:
            st.success(f"¡Archivo procesado con éxito! Se mapearon {len(data_dict)} unidades.")
            
            # Procesamiento de indicadores por unidad con las etiquetas originales exactas
            processed_results = []
            TOTAL_SEMANAS_PERIODO = float(total_semanas_reportadas) if total_semanas_reportadas > 0 else 26.0

            for unidad, m in data_dict.items():
                casos_acum = m.get("Casos acumulados", 0)
                casos_oportunos = m.get("Casos oportunos", 0)
                semanas_casos = m.get("Semanas acumuladas con casos", 0)
                u_oportunas = m.get("Unidades con casos oportunos", 0)
                u_habilitadas = m.get("Unidades habilitadas", 26)
                u_sin_notificar = m.get("Unidades sin notificar", 0)
                
                # Fórmulas oficiales exactas
                promedio_semanas_unidad = (semanas_casos / u_habilitadas) if u_habilitadas > 0 else 0
                ind_a = (promedio_semanas_unidad / TOTAL_SEMANAS_PERIODO) * 100
                ind_b = (u_oportunas / u_habilitadas) * 100 if u_habilitadas > 0 else 0.0
                ind_c = (promedio_semanas_unidad / TOTAL_SEMANAS_PERIODO) * 100
                ind_d = (u_sin_notificar / u_habilitadas) * 100 if u_habilitadas > 0 else 0.0
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
                    }
                })

            df_resumen = pd.DataFrame(processed_results)

            # Función para determinar color de fondo según rangos y tipo de indicador
            def get_bg_color(val, ind_type):
                if ind_type == "a": # Cumplimiento u Oportunidad
                    if val == 100.0: return 'background-color: #10B981; color: white; font-weight: bold;'
                    elif 97.5 <= val <= 99.9: return 'background-color: #FFFFFF; color: black; font-weight: bold;' # Bueno
                    elif 95.0 <= val <= 97.4: return 'background-color: #FEF08A; color: black; font-weight: bold;'
                    else: return 'background-color: #EF4444; color: white; font-weight: bold;'
                elif ind_type in ["b", "e"]: # Cobertura Oportuna / Cobertura Ajustada
                    if 95.0 <= val <= 100.0: return 'background-color: #10B981; color: white; font-weight: bold;'
                    elif 90.0 <= val <= 94.9: return 'background-color: #FFFFFF; color: black; font-weight: bold;' # Bueno
                    elif 80.0 <= val <= 89.9: return 'background-color: #FEF08A; color: black; font-weight: bold;'
                    else: return 'background-color: #EF4444; color: white; font-weight: bold;'
                elif ind_type == "c": # Consistencia
                    if 90.0 <= val <= 100.0: return 'background-color: #10B981; color: white; font-weight: bold;'
                    elif 80.0 <= val <= 89.9: return 'background-color: #FFFFFF; color: black; font-weight: bold;' # Bueno
                    elif 70.0 <= val <= 79.9: return 'background-color: #FEF08A; color: black; font-weight: bold;'
                    else: return 'background-color: #EF4444; color: white; font-weight: bold;'
                elif ind_type == "d": # Reporta Sin Movimiento (RSM)
                    if 0.0 <= val <= 1.9: return 'background-color: #10B981; color: white; font-weight: bold;'
                    elif 2.0 <= val <= 4.9: return 'background-color: #FFFFFF; color: black; font-weight: bold;' # Bueno
                    elif 5.0 <= val <= 10.0: return 'background-color: #FEF08A; color: black; font-weight: bold;'
                    else: return 'background-color: #EF4444; color: white; font-weight: bold;'
                elif ind_type == "f": # Calidad (Descriptivo)
                    if 90.0 <= val <= 100.0: return 'background-color: #10B981; color: white; font-weight: bold;'
                    elif 80.0 <= val <= 89.9: return 'background-color: #FFFFFF; color: black; font-weight: bold;' # Bueno
                    elif 60.0 <= val <= 79.9: return 'background-color: #FEF08A; color: black; font-weight: bold;'
                    else: return 'background-color: #EF4444; color: white; font-weight: bold;'
                return ''

            # Función para aplicar estilos a la tabla general
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
                    if col_name in col_mapping:
                        itype = col_mapping[col_name]
                        val = raw_dict[itype]
                        styles[i] = get_bg_color(val,itype)
                return styles

            st.markdown("---")
            st.subheader("📊 Tabla Comparativa General de Indicadores (Con Semaforización)")
            
            display_df = df_resumen.drop(columns=["_raw"])
            styled_general = display_df.style.format(formatter="{:.2f}", subset=pd.IndexSlice[:, display_df.columns[1:]]).apply(style_dataframe, axis=1)
            st.dataframe(styled_general, use_container_width=True)

            st.markdown("---")
            st.subheader("🏥 Tablas Detalladas e Independientes por Unidad")
            
            st.markdown("##### 🚦 Leyenda de Acotaciones y Semaforización")
            st.markdown("""
            <div class="legend-container">
                <div class="legend-item legend-excelente">🟢 Excelente</div>
                <div class="legend-item legend-bueno">⚪ Bueno</div>
                <div class="legend-item legend-regular">🟡 Regular</div>
                <div class="legend-item legend-malo">🔴 Malo</div>
            </div>
            """, unsafe_allow_html=True)
            
            unit_options = ["TODAS"] + list(data_dict.keys())
            selected_unit = st.selectbox("Seleccione una Unidad Médica (o elija 'TODAS' para ver el desglose completo):", unit_options)
            
            def render_unit_details(unit_name):
                unit_data = data_dict[unit_name]
                unit_row = df_resumen[df_resumen["Unidad"] == unit_name].iloc[0]
                raw_vals = unit_row["_raw"]
                
                st.markdown(f"### 📍 Unidad: **{unit_name}**")
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("##### Variables Base")
                    var_df = pd.DataFrame(list(unit_data.items()), columns=["Variable", "Valor (Columna AB)"])
                    st.dataframe(var_df, use_container_width=True, hide_index=True)
                
                with col2:
                    st.markdown("##### Indicadores y Semáforo")
                    ind_summary = []
                    indicators_meta = [
                        ("a) Cumplimiento u Oportunidad", raw_vals["a"], "a"),
                        ("b) Cobertura Oportuna", raw_vals["b"], "b"),
                        ("c) Consistencia", raw_vals["c"], "c"),
                        ("d) Reporta Sin Movimiento (RSM)", raw_vals["d"], "d"),
                        ("e) Cobertura Ajustada", raw_vals["e"], "e"),
                        ("f) Calidad (Descriptivo)", raw_vals["f"], "f")
                    ]
                    for name, val, itype in indicators_meta:
                        ind_summary.append({
                            "Indicador": name,
                            "Resultado (%)": round(val, 2)
                        })
                    
                    ind_df = pd.DataFrame(ind_summary)
                    
                    def style_ind_table(row_ind):
                        styles = [''] * len(row_ind)
                        itypes = ["a", "b", "c", "d", "e", "f"]
                        idx = row_ind.name
                        itype = itypes[idx] if idx < len(itypes) else "a"
                        for i, col_name in enumerate(row_ind.index):
                            if col_name == "Resultado (%)":
                                val = raw_vals[itype]
                                styles[i] = get_bg_color(val, itype)
                        return styles

                    styled_ind = ind_df.style.format(formatter="{:.2f}", subset=["Resultado (%)"]).apply(style_ind_table, axis=1)
                    st.dataframe(styled_ind, use_container_width=True, hide_index=True)
                st.markdown("---")

            if selected_unit == "TODAS":
                for u in data_dict.keys():
                    render_unit_details(u)
            else:
                render_unit_details(selected_unit)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo Excel: {e}")
else:
    st.info("👈 Por favor, carga tu archivo Excel en la parte superior para comenzar el análisis.")
