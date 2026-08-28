import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Evaluación Epidemiológica - SUIVE",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS personalizados para la semaforización y diseño
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
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Evaluación de Indicadores Epidemiológicos SUIVE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Herramienta de análisis y semaforización por unidad médica</div>', unsafe_allow_html=True)

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
        
        # Mapeo y extracción de datos
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
            
            # Procesamiento de indicadores por unidad
            processed_results = []
            
            # Constante de semanas periodo / total (generalmente 351 semanas máximas del periodo evaluado)
            TOTAL_SEMANAS_PERIODO = 351.0 

            for unidad, m in data_dict.items():
                casos_acum = m.get("Casos acumulados", 0)
                casos_oportunos = m.get("Casos oportunos", 0)
                semanas_casos = m.get("Semanas acumuladas con casos", 0)
                u_oportunas = m.get("Unidades con casos oportunos", 0)
                u_habilitadas = m.get("Unidades habilitadas", 26) # Por defecto 26 si no existe
                u_sin_notificar = m.get("Unidades sin notificar", 0)
                
                # Fórmulas oficiales
                # a) Cumplimiento Oportunidad = (Semanas con casos / Total Semanas Periodo) * 100
                ind_a = (semanas_casos / TOTAL_SEMANAS_PERIODO) * 100 if TOTAL_SEMANAS_PERIODO > 0 else 0
                
                # b) Cobertura Oportuna = (Unidades con casos oportunos / U. habilitadas) * 100
                ind_b = (u_oportunas / u_habilitadas) * 100 if u_habilitadas > 0 else 0
                
                # c) Consistencia = (Semanas acumuladas con casos / Total Semanas Periodo) * 100 (ajuste base)
                ind_c = (semanas_casos / TOTAL_SEMANAS_PERIODO) * 100 if TOTAL_SEMANAS_PERIODO > 0 else 0
                
                # d) Reporta Sin Movimiento (RSM) = (Unidades sin notificar / U. habilitadas) * 100
                ind_d = (u_sin_notificar / u_habilitadas) * 100 if u_habilitadas > 0 else 0
                
                # e) Cobertura Ajustada = Cobertura Oportuna - Excedente RSM > 5%
                excedente_rsm = max(0.0, ind_d - 5.0)
                ind_e = max(0.0, ind_b - excedente_rsm)
                
                # f) Calidad (Descriptivo) = (Promedio % Cobertura + % Consistencia) / 2 -> (ind_b + ind_c) / 2
                ind_f = (ind_b + ind_c) / 2.0
                
                processed_results.append({
                    "Unidad": unidad,
                    "a) Cumplimiento Oportunidad (%)": round(ind_a, 2),
                    "b) Cobertura Oportuna (%)": round(ind_b, 2),
                    "c) Consistencia (%)": round(ind_c, 2),
                    "d) RSM (%)": round(ind_d, 2),
                    "e) Cobertura Ajustada (%)": round(ind_e, 2),
                    "f) Calidad (%)": round(ind_f, 2),
                    # Guardamos valores crudos para evaluar colores
                    "_raw": {
                        "a": ind_a, "b": ind_b, "c": ind_c, "d": ind_d, "e": ind_e, "f": ind_f
                    }
                })

            df_resumen = pd.DataFrame(processed_results)

            # Función de semaforización exacta según tablas de referencia
            def get_color(val, ind_type):
                if ind_type == "a": # Cumplimiento Oportunidad
                    if val == 100.0: return "🟢 Excelente"
                    elif 97.5 <= val <= 99.9: return "⚪ Bueno"
                    elif 95.0 <= val <= 97.4: return "🟡 Regular"
                    else: return "🔴 Malo"
                elif ind_type == "b" or ind_type == "e": # Cobertura Oportuna / Ajustada
                    if 95.0 <= val <= 100.0: return "🟢 Excelente"
                    elif 90.0 <= val <= 94.9: return "⚪ Bueno"
                    elif 80.0 <= val <= 89.9: return "🟡 Regular"
                    else: return "🔴 Malo"
                elif ind_type == "c": # Consistencia
                    if 90.0 <= val <= 100.0: return "🟢 Excelente"
                    elif 80.0 <= val <= 89.9: return "⚪ Bueno"
                    elif 70.0 <= val <= 79.9: return "🟡 Regular"
                    else: return "🔴 Malo"
                elif ind_type == "d": # RSM
                    if 0.0 <= val <= 1.9: return "🟢 Excelente"
                    elif 2.0 <= val <= 4.9: return "⚪ Bueno"
                    elif 5.0 <= val <= 10.0: return "🟡 Regular"
                    else: return "🔴 Malo"
                elif ind_type == "f": # Calidad
                    if 90.0 <= val <= 100.0: return "🟢 Excelente"
                    elif 80.0 <= val <= 89.9: return "⚪ Bueno"
                    elif 60.0 <= val <= 79.9: return "🟡 Regular"
                    else: return "🔴 Malo"
                return "⚪ Bueno"

            # Estilo visual de celdas en DataFrame
            def color_cells(val, col_name):
                code_map = {
                    "a) Cumplimiento Oportunidad (%)": "a",
                    "b) Cobertura Oportuna (%)": "b",
                    "c) Consistencia (%)": "c",
                    "d) RSM (%)": "d",
                    "e) Cobertura Ajustada (%)": "e",
                    "f) Calidad (%)": "f"
                }
                if col_name in code_map:
                    # Extraer el valor numérico correspondiente
                    pass
                return ''

            st.markdown("---")
            st.subheader("📊 Tabla Comparativa General de Indicadores por Unidad")
            
            # Mostrar tabla resumen limpia sin la columna interna _raw
            display_df = df_resumen.drop(columns=["_raw"])
            st.dataframe(display_df, use_container_width=True)

            st.markdown("---")
            st.subheader("🏥 Tablas Detalladas e Independientes por Unidad")
            
            selected_unit = st.selectbox("Seleccione una Unidad Médica para ver detalle:", list(data_dict.keys()))
            
            if selected_unit:
                unit_data = data_dict[selected_unit]
                unit_row = df_resumen[df_resumen["Unidad"] == selected_unit].iloc[0]
                raw_vals = unit_row["_raw"]
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown(f"### 📋 Variables Base: {selected_unit}")
                    var_df = pd.DataFrame(list(unit_data.items()), columns=["Variable", "Valor (Columna AB)"])
                    st.dataframe(var_df, use_container_width=True, hide_index=True)
                
                with col2:
                    st.markdown(f"### 📈 Indicadores y Semáforo")
                    ind_summary = []
                    indicators_meta = [
                        ("a) Cumplimiento Oportunidad", raw_vals["a"], "a"),
                        ("b) Cobertura Oportuna", raw_vals["b"], "b"),
                        ("c) Consistencia", raw_vals["c"], "c"),
                        ("d) Reporta Sin Movimiento (RSM)", raw_vals["d"], "d"),
                        ("e) Cobertura Ajustada", raw_vals["e"], "e"),
                        ("f) Calidad (Descriptivo)", raw_vals["f"], "f")
                    ]
                    for name, val, itype in indicators_meta:
                        cat = get_color(val, itype)
                        ind_summary.append({
                            "Indicador": name,
                            "Resultado (%)": round(val, 2),
                            "Categoría": cat
                        })
                    
                    ind_df = pd.DataFrame(ind_summary)
                    st.dataframe(ind_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo Excel: {e}")
else:
    st.info("👈 Por favor, carga tu archivo Excel en la parte superior para comenzar el análisis.")
