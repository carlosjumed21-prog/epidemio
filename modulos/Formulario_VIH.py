import streamlit as st
import pandas as pd
import numpy as np
import datetime
import random
from io import BytesIO

# --- 1. CONFIGURACIÓN ---
st.set_page_config(layout="wide")

if 'db_vih' not in st.session_state:
    columnas = [
        "Fecha", "Frecuencia_EPP", "Barreras_Proteccion", 
        "Accion_Lavado", "Accion_Notificacion", "Accion_Registro", "Accion_PPE",
        "Lavado_Manos_OMS", "Proteccion_Identidad", "Conocimiento_NOM",
        "Edad", "Grado_Academico", "Sexo", "Turno", "Anios_Servicio", "Capacitacion_VIH"
    ]
    st.session_state.db_vih = pd.DataFrame(columns=columnas)

st.title("📋 EpidemioManager: Registro de Vigilancia VIH")

# --- 2. SIMULADOR DE DATOS CON VARIABILIDAD ---
st.subheader("⚙️ Simulador de Muestra")
n_sim = st.number_input("Cantidad de registros a simular:", min_value=1, max_value=1000, value=50)

if st.button(f"🚀 Generar {n_sim} registros con variabilidad"):
    data = []
    opt_slider = ["Nunca", "Rara Vez", "A veces", "Casi Siempre", "Siempre"]
    opciones_barreras = ["Higiene de Manos", "Uso de EPP", "Manejo de Punzocortantes", "Limpieza/Desinfección"]
    
    for _ in range(n_sim):
        # Lógica de probabilidad sesgada para que los datos parezcan reales
        cap = np.random.choice(["Si", "No"], p=[0.7, 0.3])
        grado = np.random.choice(["Técnico", "Licenciatura", "Especialidad", "Maestría"], p=[0.15, 0.50, 0.30, 0.05])
        
        # Generación de fila con variabilidad
        row = {
            "Fecha": (datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
            "Frecuencia_EPP": np.random.choice(["Nunca", "A veces", "Frecuentemente", "Siempre"], p=[0.05, 0.15, 0.30, 0.50]),
            "Barreras_Proteccion": ", ".join(random.sample(opciones_barreras, k=random.randint(1, 4))),
            "Accion_Lavado": random.choice(opt_slider),
            "Accion_Notificacion": random.choice(opt_slider),
            "Accion_Registro": random.choice(opt_slider),
            "Accion_PPE": random.choice(opt_slider),
            "Lavado_Manos_OMS": random.choice(["Si", "No"]),
            "Proteccion_Identidad": "Si",
            "Conocimiento_NOM": np.random.choice(["Bajo (0-5.9)", "Medio (6-8.9)", "Alto (9-10)"], p=[0.1, 0.3, 0.6]),
            "Edad": random.choice(["21-30", "31-40", "41-50", "51-60", "Más de 60"]),
            "Grado_Academico": grado,
            "Sexo": np.random.choice(["Femenino", "Masculino"], p=[0.85, 0.15]), 
            "Turno": random.choice(["Matutino", "Vespertino", "Nocturno", "Jornada Acumulada"]),
            "Anios_Servicio": random.randint(1, 35), # Aquí está la variabilidad real
            "Capacitacion_VIH": cap
        }
        data.append(row)
    
    st.session_state.db_vih = pd.concat([st.session_state.db_vih, pd.DataFrame(data)], ignore_index=True)
    st.success(f"✅ {n_sim} registros con datos variables generados.")

# --- 3. FORMULARIO EN BLANCO ---
with st.form("form_vih"):
    q1 = st.radio("¿Con qué frecuencia utiliza el EPP completo al realizar procedimientos en pacientes con VIH?", 
                  ["Nunca", "A veces", "Frecuentemente", "Siempre"], index=None)
    
    q2 = st.multiselect("¿Cuáles barreras de protección ha aplicado?", 
                        ["Higiene de Manos", "Uso de EPP", "Manejo de Punzocortantes", "Limpieza/Desinfección"])
    
    st.subheader("Frecuencia de Acciones ante Exposición")
    opt_slider = ["-- Seleccione --", "Nunca", "Rara Vez", "A veces", "Casi Siempre", "Siempre"]
    r1 = st.select_slider("Lavado inmediato zona", options=opt_slider)
    r2 = st.select_slider("Notificación inmediata", options=opt_slider)
    r3 = st.select_slider("Registro del accidente", options=opt_slider)
    r4 = st.select_slider("Valoración para PPE", options=opt_slider)
    
    q4 = st.radio("¿Usa técnica de lavado de manos (5 momentos OMS)?", ["Si", "No"], index=None)
    q5 = st.radio("¿Aplica protección de identidad del paciente?", ["Si", "No"], index=None)
    
    q6 = st.select_slider("Nivel de conocimiento NOM-010-SSA-2023", 
                          options=["-- Seleccione --", "Bajo (0-5.9)", "Medio (6-8.9)", "Alto (9-10)"])
    
    col1, col2 = st.columns(2)
    with col1:
        q7 = st.selectbox("Edad", ["21-30", "31-40", "41-50", "51-60", "Más de 60"], index=None, placeholder="Seleccione...")
        q_grado = st.selectbox("Grado Académico", ["Técnico", "Licenciatura", "Especialidad", "Maestría"], index=None, placeholder="Seleccione...")
    with col2:
        q8 = st.radio("Sexo", ["Femenino", "Masculino"], index=None)
        q9 = st.selectbox("Turno", ["Matutino", "Vespertino", "Nocturno", "Jornada Acumulada"], index=None, placeholder="Seleccione...")
    
    q10 = st.number_input("Años laborando en el hospital", min_value=0, step=1, value=None, placeholder="0")
    q11 = st.radio("¿Ha recibido capacitación sobre VIH en los últimos 12 meses?", ["Si", "No"], index=None)
    
    submit = st.form_submit_button("Guardar Respuesta")

if submit:
    # Validación simple
    if q1 is None or q8 is None:
        st.error("⚠️ Por favor asegúrate de seleccionar todas las opciones requeridas.")
    else:
        nueva_fila = {
            "Fecha": datetime.datetime.now().strftime("%Y-%m-%d"),
            "Frecuencia_EPP": q1, "Barreras_Proteccion": ", ".join(q2),
            "Accion_Lavado": r1, "Accion_Notificacion": r2, "Accion_Registro": r3, "Accion_PPE": r4,
            "Lavado_Manos_OMS": q4, "Proteccion_Identidad": q5, "Conocimiento_NOM": q6,
            "Edad": q7, "Grado_Academico": q_grado, "Sexo": q8, "Turno": q9, 
            "Anios_Servicio": q10, "Capacitacion_VIH": q11
        }
        st.session_state.db_vih = pd.concat([st.session_state.db_vih, pd.DataFrame([nueva_fila])], ignore_index=True)
        st.success("✅ Respuesta guardada.")

# --- 4. EXPORTACIÓN ---
if not st.session_state.db_vih.empty:
    st.divider()
    col_x, col_y = st.columns(2)
    output_xlsx = BytesIO()
    with pd.ExcelWriter(output_xlsx, engine='xlsxwriter') as writer:
        st.session_state.db_vih.to_excel(writer, index=False, sheet_name='Datos_VIH')
    col_x.download_button("📥 Descargar Excel (.xlsx)", data=output_xlsx.getvalue(), file_name="Resultados_Tesis_VIH_2026.xlsx")
    csv_data = st.session_state.db_vih.to_csv(index=False).encode('utf-8')
    col_y.download_button("📥 Descargar CSV (.csv)", data=csv_data, file_name="Resultados_Tesis_VIH_2026.csv", mime="text/csv")
