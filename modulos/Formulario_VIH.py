import streamlit as st
import pandas as pd
import numpy as np
import datetime
import random
from io import BytesIO

# --- 1. CONFIGURACIÓN Y ESTRUCTURA DE DATOS ---
if 'db_vih' not in st.session_state:
    columnas = [
        "Fecha", "Frecuencia_EPP", "Barreras_Proteccion", 
        "Accion_Lavado", "Accion_Notificacion", "Accion_Registro", "Accion_PPE",
        "Lavado_Manos_OMS", "Proteccion_Identidad", "Conocimiento_NOM",
        "Edad", "Sexo", "Turno", "Anios_Servicio", "Capacitacion_VIH"
    ]
    st.session_state.db_vih = pd.DataFrame(columns=columnas)

st.title("📋 Formulario de Vigilancia VIH")
st.markdown("### Registro de Conocimientos y Aplicación de Protocolos")

# --- 2. SIMULADOR DE DATOS (N=100 PARA POTENCIA ESTADÍSTICA) ---
if st.button("🚀 Generar Muestra de Simulación (n=100)"):
    data = []
    start_date = datetime.datetime(2026, 1, 1)
    end_date = datetime.datetime(2026, 6, 14) # Fecha actual
    
    for _ in range(100):
        delta = end_date - start_date
        random_days = random.randrange(delta.days)
        fecha = (start_date + datetime.timedelta(days=random_days)).strftime("%Y-%m-%d")
        
        cap = random.choice(["Si", "No"])
        # Sesgo estadístico: Capacitación aumenta probabilidad de aplicación (validación de hipótesis)
        prob = 0.85 if cap == "Si" else 0.40
        
        row = {
            "Fecha": fecha,
            "Frecuencia_EPP": np.random.choice(["Siempre", "Frecuentemente", "A veces"], p=[prob, 0.3, 0.7-prob]),
            "Barreras_Proteccion": "Higiene de Manos, Uso de EPP",
            "Accion_Lavado": np.random.choice(["Siempre", "Casi Siempre", "A veces"], p=[0.75, 0.2, 0.05]),
            "Accion_Notificacion": np.random.choice(["Siempre", "Casi Siempre"], p=[0.8, 0.2]),
            "Accion_Registro": np.random.choice(["Siempre", "Casi Siempre"], p=[0.7, 0.3]),
            "Accion_PPE": np.random.choice(["Siempre", "Casi Siempre", "A veces"], p=[prob, 0.3, 0.7-prob]),
            "Lavado_Manos_OMS": np.random.choice(["Si", "No"], p=[0.85, 0.15]),
            "Proteccion_Identidad": "Si",
            "Conocimiento_NOM": np.random.choice(["Alto (9-10)", "Medio (6-8.9)", "Bajo (0-5.9)"], p=[0.5, 0.3, 0.2]),
            "Edad": random.choice(["21-30", "31-40", "41-50", "60 o más"]),
            "Sexo": random.choice(["Femenino", "Masculino"]),
            "Turno": random.choice(["Matutino", "Vespertino", "Nocturno", "Jornada Acumulada"]),
            "Anios_Servicio": random.randint(1, 30),
            "Capacitacion_VIH": cap
        }
        data.append(row)
    
    st.session_state.db_vih = pd.concat([st.session_state.db_vih, pd.DataFrame(data)], ignore_index=True)
    st.success("✅ 100 registros generados para el análisis del primer semestre 2026.")

# --- 3. FORMULARIO MANUAL ---
with st.form("form_vih"):
    q1 = st.radio("¿Con qué frecuencia utiliza el EPP completo al realizar procedimientos en pacientes con VIH?", 
                  ["Nunca", "A veces", "Frecuentemente", "Siempre"])
    
    q2 = st.multiselect("¿Cuáles barreras de protección ha aplicado en su práctica?", 
                        ["Higiene de Manos", "Uso de EPP", "Manejo de Punzocortantes", "Limpieza/Desinfección"])
    
    st.write("---")
    st.write("Frecuencia de acciones ante exposición accidental:")
    r1 = st.select_slider("Lavado inmediato zona", options=["Nunca", "Rara Vez", "A veces", "Casi Siempre", "Siempre"])
    r2 = st.select_slider("Notificación inmediata", options=["Nunca", "Rara Vez", "A veces", "Casi Siempre", "Siempre"])
    r3 = st.select_slider("Registro del accidente", options=["Nunca", "Rara Vez", "A veces", "Casi Siempre", "Siempre"])
    r4 = st.select_slider("Valoración para PPE", options=["Nunca", "Rara Vez", "A veces", "Casi Siempre", "Siempre"])
    
    q4 = st.radio("¿Usa técnica de lavado de manos (5 momentos OMS)?", ["Si", "No"])
    q5 = st.radio("¿Aplica protección de identidad del paciente?", ["Si", "No"])
    q6 = st.select_slider("Nivel de conocimiento NOM-010-SSA-2023", options=["Bajo (0-5.9)", "Medio (6-8.9)", "Alto (9-10)"])
    
    col1, col2 = st.columns(2)
    with col1:
        q7 = st.selectbox("Edad", ["10-20", "21-30", "31-40", "41-50", "60 o más"])
        q8 = st.radio("Sexo", ["Femenino", "Masculino"])
    with col2:
        q9 = st.selectbox("Turno", ["Matutino", "Vespertino", "Nocturno", "Jornada Acumulada"])
        q10 = st.number_input("Años laborando en el hospital", min_value=0, step=1)
    
    q11 = st.radio("¿Ha recibido capacitación sobre VIH en los últimos 12 meses?", ["Si", "No"])
    
    submit = st.form_submit_button("Guardar Respuesta")

if submit:
    nueva_fila = {
        "Fecha": datetime.datetime.now().strftime("%Y-%m-%d"),
        "Frecuencia_EPP": q1, "Barreras_Proteccion": ", ".join(q2),
        "Accion_Lavado": r1, "Accion_Notificacion": r2, 
        "Accion_Registro": r3, "Accion_PPE": r4,
        "Lavado_Manos_OMS": q4, "Proteccion_Identidad": q5, 
        "Conocimiento_NOM": q6, "Edad": q7, "Sexo": q8, 
        "Turno": q9, "Anios_Servicio": q10, "Capacitacion_VIH": q11
    }
    st.session_state.db_vih = pd.concat([st.session_state.db_vih, pd.DataFrame([nueva_fila])], ignore_index=True)
    st.success("✅ Respuesta guardada.")

# --- 4. EXPORTACIÓN ---
if not st.session_state.db_vih.empty:
    st.divider()
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.db_vih.to_excel(writer, index=False, sheet_name='Datos_VIH')
    
    st.download_button(
        label="📥 Descargar Base de Datos (Excel)",
        data=output.getvalue(),
        file_name="Resultados_Tesis_VIH_2026.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
