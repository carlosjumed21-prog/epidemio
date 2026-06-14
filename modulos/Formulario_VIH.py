import streamlit as st
import pandas as pd
import datetime

# Inicializar base de datos en memoria si no existe
if 'db_vih' not in st.session_state:
    columnas = [
        "Fecha", "Frecuencia_EPP", "Barreras_Proteccion", 
        "Accion_Lavado", "Accion_Notificacion", "Accion_Registro", "Accion_PPE",
        "Lavado_Manos_OMS", "Proteccion_Identidad", "Conocimiento_NOM",
        "Edad", "Sexo", "Turno", "Anios_Servicio", "Capacitacion_VIH"
    ]
    st.session_state.db_vih = pd.DataFrame(columns=columnas)

st.title("📋 Formulario de Vigilancia VIH")

with st.form("form_vih"):
    q1 = st.radio("¿Con qué frecuencia utiliza el EPP completo al realizar procedimientos en pacientes con VIH?", 
                  ["Nunca", "A veces", "Frecuentemente", "Siempre"])
    
    q2 = st.multiselect("¿Cuáles barreras de protección ha aplicado en su práctica?", 
                        ["Higiene de Manos", "Uso de EPP", "Manejo de Punzocortantes", 
                         "Limpieza/Desinfección", "Consideración ante exposición"])
    
    st.subheader("Acciones ante exposición accidental")
    st.write("Frecuencia de realización:")
    cols_act = st.columns(5)
    frecuencias = ["Nunca", "Rara Vez", "A veces", "Casi Siempre", "Siempre"]
    
    r1 = st.select_slider("Lavado inmediato zona", options=frecuencias)
    r2 = st.select_slider("Notificación inmediata", options=frecuencias)
    r3 = st.select_slider("Registro del accidente", options=frecuencias)
    r4 = st.select_slider("Valoración para PPE", options=frecuencias)
    
    q4 = st.radio("¿Usa la técnica de lavado de manos correcta (5 momentos OMS)?", ["Si", "No"])
    q5 = st.radio("¿Aplica medidas para proteger identidad/diagnóstico del paciente?", ["Si", "No"])
    q6 = st.select_slider("¿Identifica fluidos de alto riesgo y protocolo NOM-010-SSA-2023?", 
                          options=["Bajo (0-5.9)", "Medio (6-8.9)", "Alto (9-10)"])
    
    q7 = st.selectbox("¿Cual es su edad?", ["10-20", "21-30", "31-40", "41-50", "60 o más"])
    q8 = st.radio("Sexo", ["Femenino", "Masculino"])
    q9 = st.selectbox("Turno", ["Matutino", "Vespertino", "Nocturno", "Jornada Acumulada"])
    q10 = st.number_input("Años laborando en el hospital", min_value=0, step=1)
    q11 = st.radio("¿Ha recibido capacitación sobre VIH en los últimos 12 meses?", ["Si", "No"])
    
    submit = st.form_submit_button("Guardar Respuesta")

if submit:
    nueva_fila = {
        "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Frecuencia_EPP": q1, "Barreras_Proteccion": ", ".join(q2),
        "Accion_Lavado": r1, "Accion_Notificacion": r2, 
        "Accion_Registro": r3, "Accion_PPE": r4,
        "Lavado_Manos_OMS": q4, "Proteccion_Identidad": q5, 
        "Conocimiento_NOM": q6, "Edad": q7, "Sexo": q8, 
        "Turno": q9, "Anios_Servicio": q10, "Capacitacion_VIH": q11
    }
    st.session_state.db_vih = pd.concat([st.session_state.db_vih, pd.DataFrame([nueva_fila])], ignore_index=True)
    st.success("✅ Respuesta guardada correctamente.")

# Botón de descarga
if not st.session_state.db_vih.empty:
    csv = st.session_state.db_vih.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Base de Datos (CSV)", data=csv, file_name="respuestas_VIH.csv", mime="text/csv")
