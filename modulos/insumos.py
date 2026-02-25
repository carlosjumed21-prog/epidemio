import streamlit as st
import pandas as pd
import numpy as np
import re
import time
from io import BytesIO
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
# Link actualizado según tu última indicación
SHEET_URL_AISLAMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"

# Tus 11 especialidades intocables
SERVICIOS_INSUMOS_FILTRO = [
    "HEMATOLOGIA", "HEMATOLOGIA PEDIATRICA", "ONCOLOGIA PEDIATRICA",
    "NEONATOLOGIA", "INFECTOLOGIA PEDIATRICA", "U.C.I.N.",
    "U.T.I.P.", "TERAPIA POSQUIRURGICA", "UNIDAD DE QUEMADOS",
    "ONCOLOGIA MEDICA", "UCIA"
]

# --- FUNCIONES DE CARGA (REFORZADAS) ---

@st.cache_data(ttl=5)
def cargar_aislamientos_limpios():
    try:
        # Forzamos descarga fresca
        url_fresca = f"{SHEET_URL_AISLAMIENTOS}&cachebust={time.time()}"
        df = pd.read_csv(url_fresca, skiprows=1, engine='python')
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # 1. Limpieza inicial de nulos
        df = df.replace(['nan', 'None', 'none', 'NAN', 'NULL', ''], np.nan)

        # 2. RELLENO CRÍTICO: Rellenamos Cama, Registro y Nombre ANTES de filtrar
        # Esto evita que los pacientes "sin nombre" en la fila del aislamiento se pierdan
        cols_paciente = ["CAMA", "REGISTRO", "NOMBRE"]
        for col in cols_paciente:
            if col in df.columns:
                df[col] = df[col].ffill()

        # 3. FILTRO DE ACTIVOS: Solo filas donde FECHA DE TÉRMINO sea NaN
        if "FECHA DE TÉRMINO" in df.columns:
            df = df[df["FECHA DE TÉRMINO"].isna()]

        # 4. CONSOLIDAR AISLAMIENTOS: Si un paciente tiene varias filas (varios bichos)
        if "TIPO DE AISLAMIENTO" in df.columns:
            df["TIPO DE AISLAMIENTO"] = df.groupby("REGISTRO")["TIPO DE AISLAMIENTO"].transform(
                lambda x: " / ".join(x.dropna().astype(str).unique())
            )
        
        # 5. Quitamos duplicados para tener un renglón por paciente
        df = df.drop_duplicates(subset=["REGISTRO"])
        
        # Aseguramos que las columnas necesarias existan
        for c in ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO"]:
            if c not in df.columns: df[c] = "N/A"
            
        return df[["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO"]]
    except Exception as e:
        st.error(f"Error cargando Sheets: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("📦 Censo de Insumos")

if 'archivo_compartido' not in st.session_state:
    st.info("👈 Sube el archivo HTML en la barra lateral para iniciar.")
else:
    try:
        # Procesamiento del HTML
        tablas = pd.read_html(st.session_state['archivo_compartido'])
        df_html_raw = max(tablas, key=len)
        
        datos_html = []
        pacs_especialidades = [] # Aquí irán tus 11 servicios
        
        esp_actual = ""
        for i in range(len(df_html_raw)):
            val_col0 = str(df_html_raw.iloc[i, 0]).upper()
            
            if "ESPECIALIDAD:" in val_col0:
                esp_actual = val_col0.replace("ESPECIALIDAD:", "").replace("&NBSP;", "").strip()
                continue
            
            fila = [str(x).strip() for x in df_html_raw.iloc[i].values]
            
            # Validar que sea una fila de paciente (Registro con números y longitud >= 5)
            if len(fila) > 1 and len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
                # Ajuste de especialidad por número de cama
                cama = fila[0]
                esp_real = esp_actual
                if cama.startswith("55"): esp_real = "U.C.I.N."
                elif cama.startswith("45"): esp_real = "NEONATOLOGIA"
                elif cama.startswith("56"): esp_real = "U.T.I.P."
                elif cama.startswith("85"): esp_real = "UNIDAD DE QUEMADOS"
                elif cama.startswith("73"): esp_real = "UCIA"
                elif cama.isdigit() and 7401 <= int(cama) <= 7409: esp_real = "TERAPIA POSQUIRURGICA"

                pac_data = {
                    "CAMA": cama, "REGISTRO": fila[1], "PACIENTE": fila[2],
                    "SEXO": fila[3], "EDAD": "".join(re.findall(r'\d+', fila[4])),
                    "FECHA DE INGRESO": fila[9], "ESP_REAL": esp_real
                }
                datos_html.append(pac_data)
                
                if esp_real in SERVICIOS_INSUMOS_FILTRO:
                    pacs_especialidades.append(pac_data)

        df_ref_html = pd.DataFrame(datos_html)

        # --- SECCIÓN A: LAS 11 ESPECIALIDADES ---
        st.header("📋 INSUMOS: ESPECIALIDADES")
        if pacs_especialidades:
            df_servicios = pd.DataFrame(pacs_especialidades)
            for serv in sorted(df_servicios["ESP_REAL"].unique()):
                with st.expander(f"🔍 Vista Previa: {serv}"):
                    df_v = df_servicios[df_servicios["ESP_REAL"] == serv].copy()
                    df_v["TIPO DE PRECAUCIONES"] = "ESTÁNDAR"
                    df_v["INSUMO"] = "JABÓN/SANITAS"
                    st.table(df_v[["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]])

        # --- SECCIÓN B: AISLAMIENTOS (CRUCE MEJORADO) ---
        st.header("🦠 INSUMOS: AISLAMIENTOS")
        df_ais_base = cargar_aislamientos_limpios()
        
        if not df_ais_base.empty:
            # Aseguramos que 'REGISTRO' sea string para el cruce
            df_ais_base["REGISTRO"] = df_ais_base["REGISTRO"].astype(str)
            df_ref_html["REGISTRO"] = df_ref_html["REGISTRO"].astype(str)

            # CRUCE: Traemos los datos del HTML a la base de Aislamientos
            df_final_ais = pd.merge(df_ais_base, df_ref_html, on="REGISTRO", how="left", suffixes=('', '_H'))
            
            # REPARACIÓN DE DATOS: Si no cruzó con el HTML, usamos lo que tenemos en el Sheets
            df_final_ais["PACIENTE"] = df_final_ais["PACIENTE"].fillna(df_final_ais["NOMBRE"])
            df_final_ais["CAMA"] = df_final_ais["CAMA"].fillna(df_final_ais["CAMA_H"])
            df_final_ais["TIPO DE PRECAUCIONES"] = df_final_ais["TIPO DE AISLAMIENTO"]
            df_final_ais["INSUMO"] = "JABÓN/SANITAS"
            
            # Rellenar faltantes con "Pendiente" para edición manual
            for col in ["SEXO", "EDAD", "FECHA DE INGRESO"]:
                df_final_ais[col] = df_final_ais[col].fillna("Pendiente")

            cols_mostrar = ["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
            df_ready = df_final_ais[cols_mostrar]

            # Si hay pendientes, mostramos el editor
            if (df_ready == "Pendiente").any().any():
                st.warning("⚠️ Algunos pacientes no están en el HTML. Completa los datos amarillos:")
                df_ready = st.data_editor(df_ready.style.applymap(lambda x: 'background-color: #FFF9C4' if x == "Pendiente" else ''), use_container_width=True, hide_index=True)
            else:
                st.table(df_ready)

            st.session_state.df_ais_mapeado = df_ready

            # Botones de descarga (se omiten funciones de Excel/PDF por brevedad, usa las de tu código original)
            st.success("✅ Cruce de datos completado.")

    except Exception as e:
        st.error(f"Error general: {e}")
