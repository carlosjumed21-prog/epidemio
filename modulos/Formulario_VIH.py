import streamlit as st
import pandas as pd
import numpy as np
import datetime
import random
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency
from io import BytesIO

# --- 1. CONFIGURACIÓN Y ESTRUCTURA ---
if 'db_vih' not in st.session_state:
    st.session_state.db_vih = pd.DataFrame()

st.title("📋 Gestión y Análisis: Vigilancia VIH")
tab1, tab2, tab3 = st.tabs(["📝 Formulario", "🚀 Simulación", "📉 Análisis Estadístico"])

# --- 2. PESTAÑA: FORMULARIO ---
with tab1:
    with st.form("form_vih"):
        q1 = st.radio("¿Frecuencia de uso de EPP completo?", ["Nunca", "A veces", "Frecuentemente", "Siempre"])
        q2 = st.multiselect("Barreras aplicadas", ["Higiene de Manos", "Uso de EPP", "Manejo de Punzocortantes", "Limpieza/Desinfección"])
        r1 = st.select_slider("Lavado inmediato zona", options=["Nunca", "Rara Vez", "A veces", "Casi Siempre", "Siempre"])
        q_grado = st.selectbox("Grado Académico", ["Técnico", "Licenciatura", "Especialidad", "Maestría"])
        q11 = st.radio("¿Capacitación en los últimos 12 meses?", ["Si", "No"])
        submit = st.form_submit_button("Guardar Respuesta")

    if submit:
        nueva_fila = {"Fecha": datetime.datetime.now().strftime("%Y-%m-%d"), "Frecuencia_EPP": q1, 
                      "Grado_Academico": q_grado, "Capacitacion_VIH": q11}
        st.session_state.db_vih = pd.concat([st.session_state.db_vih, pd.DataFrame([nueva_fila])], ignore_index=True)
        st.success("✅ Respuesta guardada.")

# --- 3. PESTAÑA: SIMULADOR ---
with tab2:
    if st.button("🚀 Generar 100 registros para Tesis"):
        data = []
        for _ in range(100):
            cap = random.choice(["Si", "No"])
            grado = np.random.choice(["Técnico", "Licenciatura", "Especialidad", "Maestría"], p=[0.1, 0.5, 0.35, 0.05])
            p_epp = 0.85 if cap == "Si" else 0.45
            data.append({
                "Fecha": "2026-01-01", "Capacitacion_VIH": cap, "Grado_Academico": grado,
                "Frecuencia_EPP": np.random.choice(["Siempre", "Frecuentemente", "A veces"], p=[p_epp, 0.3, 0.7-p_epp])
            })
        st.session_state.db_vih = pd.DataFrame(data)
        st.success("✅ Datos simulados generados.")

# --- 4. PESTAÑA: ANÁLISIS ESTADÍSTICO ---
with tab3:
    if not st.session_state.db_vih.empty:
        df = st.session_state.db_vih
        var_indep = st.selectbox("Variable Independiente", df.columns)
        var_dep = st.selectbox("Variable Dependiente", df.columns)
        
        if st.button("Ejecutar Análisis Chi-Cuadrado"):
            tabla = pd.crosstab(df[var_indep], df[var_dep])
            chi2, p, dof, expected = chi2_contingency(tabla)
            
            st.write(f"### Valor p (p-value): {p:.4f}")
            if p < 0.05:
                st.success("Resultado estadísticamente significativo (p < 0.05). Existe relación entre variables.")
            else:
                st.warning("No hay significancia estadística (p > 0.05).")
            
            fig, ax = plt.subplots()
            sns.heatmap(tabla, annot=True, cmap="YlGnBu", fmt="d")
            st.pyplot(fig)
    else:
        st.info("Genera datos o carga una base para analizar.")

# --- 5. DESCARGA ---
if not st.session_state.db_vih.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.db_vih.to_excel(writer, index=False)
    st.download_button("📥 Descargar Excel", data=output.getvalue(), file_name="Resultados_Tesis.xlsx")
