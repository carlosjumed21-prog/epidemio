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

# --- 2. SIMULADOR DE DATOS CON CONTROL DE N ---
st.subheader("⚙️ Simulador de Muestra")
n_sim = st.number_input("Cantidad de registros a simular:", min_value=1, max_value=1000, value=50)

if st.button(f"🚀 Generar {n_sim} registros"):
    data = []
    start_date = datetime.datetime(2026, 1, 1)
    end_date = datetime.datetime(2026, 6, 14)
    opciones_barreras = ["Higiene de Manos", "Uso de EPP", "Manejo de Punzocortantes", "Limpieza/Desinfección"]
    
    for _ in range(n_sim):
        fecha = (start_date + datetime.timedelta(days=random.randrange((end_date - start_date).days))).strftime("%Y-%m-%d")
        cap = random.choice(["Si", "No"])
        grado = np.random.choice(["Técnico", "Licenciatura", "Especialidad", "Maestría"], p=[0.15, 0.50, 0.30, 0.05])
        
        base_p = 0.8 if cap == "Si" else 0.4
        if grado in ["Especialidad", "Maestría"]: base_p = min(0.95, base_p + 0.1)
        p1, p2 = base_p, 0.2
        p3 = round(1.0 - (p1 + p2), 2)
        if p3 < 0: p1, p2, p3 = 0.6, 0.3, 0.1
        
        k = random.randint(2, 4) if cap == "Si" else random.randint(1, 2)
        barreras_sel = random.sample(opciones_barreras, k=k)
        
        row = {
            "Fecha": fecha,
            "Frecuencia_EPP": np.random.choice(["Siempre", "Frecuentemente", "A veces"], p=[p1, p2, p3]),
            "Barreras_Proteccion": ", ".join(barreras_sel),
            "Accion_Lavado": np.random.choice(["Siempre", "Casi Siempre", "A veces"], p=[0.7, 0.2, 0.1]),
            "Accion_Notificacion": np.random.choice(["Siempre", "Casi Siempre"], p=[0.8, 0.2]),
            "Accion_Registro": np.random.choice(["Siempre", "Casi Siempre"], p=[0.7, 0.3]),
            "Accion_PPE": np.random.choice(["Siempre", "Casi Siempre", "A veces"], p=[p1, p2, p3]),
            "Lavado_Manos_OMS": np.random.choice(["Si", "No"], p=[0.8, 0.2]),
            "Proteccion_Identidad": "Si",
            "Conocimiento_NOM": np.random.choice(["Alto (9-10)", "Medio (6-8.9)", "Bajo (0-5.9)"], p=[0.5, 0.3, 0.2]),
            "Edad": random.choice(["21-30", "31-40", "41-50", "51-60"]),
            "Grado_Academico": grado,
            "Sexo": np.random.choice(["Femenino", "Masculino"], p=[0.85, 0.15]),
            "Turno": random.choice(["Matutino", "Vespertino", "Nocturno", "Jornada Acumulada"]),
            "Anios_Servicio": random.randint(1, 30),
            "Capacitacion_VIH": cap
        }
        data.append(row)
    
    st.session_state.db_vih = pd.concat([st.session_state.db_vih, pd.DataFrame(data)], ignore_index=True)
    st.success(f"✅ {n_sim} registros añadidos a la base actual (Total: {len(st.session_state.db_vih)}).")

# --- 3. FORMULARIO MANUAL ---
with st.form("form_vih"):
    q1 = st.radio("¿Con qué frecuencia utiliza el EPP completo al realizar procedimientos en pacientes con VIH?", ["Nunca", "A veces", "Frecuentemente", "Siempre"])
    q2 = st.multiselect("¿Cuáles barreras de protección ha aplicado?", ["Higiene de Manos", "Uso de EPP", "Manejo de Punzocortantes", "Limpieza/Desinfección"])
    # ... (Resto del formulario igual)
    submit = st.form_submit_button("Guardar Respuesta")
    if submit:
        # ... (Tu lógica de guardado sigue intacta)
        st.success("✅ Respuesta guardada.")

# --- 4. EXPORTACIÓN DUAL ---
if not st.session_state.db_vih.empty:
    st.divider()
    col_x, col_y = st.columns(2)
    
    # Descarga Excel
    output_xlsx = BytesIO()
    with pd.ExcelWriter(output_xlsx, engine='xlsxwriter') as writer:
        st.session_state.db_vih.to_excel(writer, index=False, sheet_name='Datos_VIH')
    col_x.download_button("📥 Descargar Excel (.xlsx)", data=output_xlsx.getvalue(), file_name="Resultados_Tesis.xlsx")
    
    # Descarga CSV
    csv_data = st.session_state.db_vih.to_csv(index=False).encode('utf-8')
    col_y.download_button("📥 Descargar CSV (.csv)", data=csv_data, file_name="Resultados_Tesis.csv", mime="text/csv")
