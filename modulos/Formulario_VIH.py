import streamlit as st
import pandas as pd
import numpy as np
import datetime
import random
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency
from io import BytesIO

# --- 1. CONFIGURACIÓN ---
if 'db_vih' not in st.session_state:
    columnas = [
        "Fecha", "Frecuencia_EPP", "Barreras_Proteccion", "Lavado_Accidente", 
        "Notificacion_Accidente", "Registro_Accidente", "PPE_Accidente",
        "Lavado_Manos_OMS", "Proteccion_Identidad", "Conocimiento_NOM",
        "Edad", "Grado_Academico", "Sexo", "Turno", "Anios_Servicio", "Capacitacion_VIH"
    ]
    st.session_state.db_vih = pd.DataFrame(columns=columnas)

st.title("📋 Vigilancia VIH: Formulario y Análisis")
tab1, tab2, tab3 = st.tabs(["📝 Formulario", "🚀 Simulación", "📉 Análisis"])

# --- 2. FORMULARIO ---
with tab1:
    with st.form("form_vih"):
        q1 = st.radio("¿Frecuencia de uso de EPP completo?", ["Nunca", "A veces", "Frecuentemente", "Siempre"])
        q2 = st.multiselect("Barreras de protección aplicadas", ["Higiene de Manos", "Uso de EPP", "Manejo de Punzocortantes", "Limpieza, Desinfección y Manejo de Ropa", "Consideración ante una exposición accidental"])
        
        st.write("### Frecuencia ante exposición accidental")
        r1 = st.select_slider("Lavado inmediato de zona", options=["Nunca", "Rara Vez", "A veces", "Casi Siempre", "Siempre"])
        r2 = st.select_slider("Notificación inmediata", options=["Nunca", "Rara Vez", "A veces", "Casi Siempre", "Siempre"])
        r3 = st.select_slider("Registro del accidente", options=["Nunca", "Rara Vez", "A veces", "Casi Siempre", "Siempre"])
        r4 = st.select_slider("Valoración para Profilaxis (PPE)", options=["Nunca", "Rara Vez", "A veces", "Casi Siempre", "Siempre"])
        
        q4 = st.radio("¿Usa técnica de lavado de manos 5 momentos OMS?", ["Si", "No"])
        q5 = st.radio("¿Protege identidad/diagnóstico del paciente?", ["Si", "No"])
        q6 = st.select_slider("Nivel de conocimiento NOM-010-SSA-2023", options=["Bajo (0-5.9)", "Medio (6-8.9)", "Alto (9-10)"])
        
        c1, c2 = st.columns(2)
        with c1:
            q7 = st.selectbox("Edad", ["10-20", "21-30", "31-40", "41-50", "60 o más"])
            q_grado = st.selectbox("Grado Académico", ["Técnico", "Licenciatura", "Especialidad", "Maestría"])
            q8 = st.radio("Sexo", ["Femenino", "Masculino"])
        with c2:
            q9 = st.selectbox("Turno", ["Matutino", "Vespertino", "Nocturno", "Jornada Acumulada"])
            q10 = st.number_input("Años laborando", min_value=0)
            q11 = st.radio("¿Capacitación en últimos 12 meses?", ["Si", "No"])
            
        submit = st.form_submit_button("Guardar Respuesta")

    if submit:
        nueva = {"Fecha": datetime.datetime.now().strftime("%Y-%m-%d"), "Frecuencia_EPP": q1, "Barreras_Proteccion": ", ".join(q2),
                 "Lavado_Accidente": r1, "Notificacion_Accidente": r2, "Registro_Accidente": r3, "PPE_Accidente": r4,
                 "Lavado_Manos_OMS": q4, "Proteccion_Identidad": q5, "Conocimiento_NOM": q6, "Edad": q7, 
                 "Grado_Academico": q_grado, "Sexo": q8, "Turno": q9, "Anios_Servicio": q10, "Capacitacion_VIH": q11}
        st.session_state.db_vih = pd.concat([st.session_state.db_vih, pd.DataFrame([nueva])], ignore_index=True)
        st.success("Respuesta guardada.")

# --- 3. SIMULACIÓN ---
with tab2:
    if st.button("🚀 Generar 100 registros para Tesis"):
        data = []
        for _ in range(100):
            cap = random.choice(["Si", "No"])
            p1 = 0.85 if cap == "Si" else 0.45
            data.append({
                "Fecha": "2026-03-01", 
                "Frecuencia_EPP": np.random.choice(["Siempre", "Frecuentemente", "A veces"], p=[p1, 0.10, 0.05 if cap == "Si" else 0.45]),
                "Capacitacion_VIH": cap, 
                "Grado_Academico": np.random.choice(["Técnico", "Licenciatura", "Especialidad", "Maestría"], p=[0.1, 0.5, 0.35, 0.05]),
                "Conocimiento_NOM": "Alto (9-10)" if cap == "Si" else "Bajo (0-5.9)"
            })
        st.session_state.db_vih = pd.DataFrame(data)
        st.success("✅ Datos simulados generados.")

# --- 4. ANÁLISIS ---
with tab3:
    if not st.session_state.db_vih.empty:
        df = st.session_state.db_vih
        v1 = st.selectbox("Independiente (ej. Capacitacion_VIH)", df.columns)
        v2 = st.selectbox("Dependiente (ej. Frecuencia_EPP)", df.columns)
        if st.button("Ejecutar Análisis Chi-Cuadrado"):
            tabla = pd.crosstab(df[v1], df[v2])
            chi2, p, _, _ = chi2_contingency(tabla)
            st.metric("Valor p", f"{p:.4f}")
            if p < 0.05: st.success("Resultado significativo (p < 0.05).")
            else: st.warning("No hay significancia estadística.")
            fig, ax = plt.subplots()
            sns.heatmap(tabla, annot=True, cmap="Blues", fmt="d")
            st.pyplot(fig)
            st.write("El análisis estadístico permite observar la correlación entre variables para sustentar los objetivos de la tesis.")
            
    
    if not st.session_state.db_vih.empty:
        output = BytesIO()
        with pd.ExcelWriter(output) as w: st.session_state.db_vih.to_excel(w, index=False)
        st.download_button("📥 Descargar Excel", data=output.getvalue(), file_name="Resultados_Tesis.xlsx")
