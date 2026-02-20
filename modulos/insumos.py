import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Border, Side, Font

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="EpidemioManager", layout="wide")

# --- REGLAS DE NEGOCIO Y CATÁLOGOS ---
ORDEN_TERAPIAS_EXCEL = ["UNIDAD CORONARIA", "UCIA", "TERAPIA POSQUIRURGICA", "U.C.I.N.", "U.T.I.P.", "UNIDAD DE QUEMADOS"]

# Las 11 especialidades que mencionas para insumos
ESPECIALIDADES_INSUMOS = [
    "UNIDAD CORONARIA", "UCIA", "TERAPIA POSQUIRURGICA", "U.C.I.N.", "U.T.I.P.", 
    "UNIDAD DE QUEMADOS", "MEDICINA INTERNA", "CIRUGIA GENERAL", "NEUROCIRUGIA", 
    "HEMATO-ONCOLOGIA", "NEFROLOGIA"
]

CATALOGO = {
    "COORD_PEDIATRIA": ["MEDICINA INTERNA PEDIATRICA", "PEDIATRI", "PEDIATRICA", "NEONATO", "NEONATOLOGIA", "CUNERO", "UTIP", "UCIN"],
    "COORD_MODULARES": ["NEUROLOGIA", "ANGIOLOGIA", "VASCULAR", "CARDIOLOGIA", "CARDIOVASCULAR", "TORAX", "NEUMO", "HEMATO", "NEUROCIRUGIA", "ONCOLOGIA", "CORONARIA", "PSIQ", "PSIQUIATRIA"],
    "COORD_MEDICINA": ["DERMATO", "ENDOCRINO", "GERIAT", "INMUNO", "MEDICINA INTERNA", "REUMA", "UCIA", "TERAPIA INTERMEDIA", "CLINICA DEL DOLOR", "TPQX"],
    "COORD_CIRUGIA": ["CIRUGIA GENERAL", "CIR. GENERAL", "MAXILO", "RECONSTRUCTIVA", "PLASTICA", "GASTRO", "NEFROLOGIA", "OFTALMO", "ORTOPEDIA", "OTORRINO", "UROLOGIA", "TRASPLANTES", "QUEMADOS"],
    "COORD_GINECOLOGIA": ["GINECO", "OBSTETRICIA", "MATERNO", "REPRODUCCION"]
}

# --- FUNCIONES DE APOYO ---
def obtener_especialidad_real(cama, esp_html):
    c = str(cama).strip().upper()
    esp_html_clean = esp_html.replace("ESPECIALIDAD:", "").replace("&NBSP;", "").strip().upper()
    if c.startswith("64"): return "UNIDAD CORONARIA"
    if c.startswith("55"): return "U.C.I.N."
    if c.startswith("45"): return "NEONATOLOGIA" 
    if c.startswith("56"): return "U.T.I.P."
    if c.startswith("85"): return "UNIDAD DE QUEMADOS"
    if c.startswith("73"): return "UCIA"
    if c.isdigit() and 7401 <= int(c) <= 7409: return "TERAPIA POSQUIRURGICA"
    return esp_html_clean

# --- INTERFAZ PRINCIPAL ---
st.title("🏥 Sistema Epidemiológico - CMN 20 de Noviembre")

# Crear las pestañas
tab_censo, tab_insumos = st.tabs(["📋 CENSO DIARIO", "📦 GESTIÓN DE INSUMOS"])

with tab_censo:
    if 'archivo_compartido' not in st.session_state:
        st.info("👈 Por favor, sube el archivo HTML en la barra lateral para comenzar.")
    else:
        try:
            tablas = pd.read_html(st.session_state['archivo_compartido'])
            df_completo = max(tablas, key=len)
            col0_str = df_completo.iloc[:, 0].fillna("").astype(str).str.upper()
            
            pacs_detectados = []
            esp_actual_temp = "SIN_ESPECIALIDAD"
            for i, val in enumerate(col0_str):
                if "ESPECIALIDAD:" in val: esp_actual_temp = val; continue
                fila = [str(x).strip() for x in df_completo.iloc[i].values]
                if len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
                    esp_real = obtener_especialidad_real(fila[0], esp_actual_temp)
                    pacs_detectados.append({"CAMA": fila[0], "REG": fila[1], "PAC": fila[2], "esp_real": esp_real})

            st.subheader(f"📊 Pacientes Detectados: {len(pacs_detectados)}")
            st.write("Aquí iría el resto de tu lógica de Censo...")
        except Exception as e:
            st.error(f"Error: {e}")

with tab_insumos:
    st.subheader("🛠️ Control de Insumos por Especialidad")
    
    # 1. RECUADRO DE SELECCIÓN (Las 11 especialidades)
    with st.container(border=True):
        st.markdown("**Seleccione las especialidades para reporte de insumos:**")
        seleccionadas = st.multiselect(
            "Especialidades activas hoy:",
            options=ESPECIALIDADES_INSUMOS,
            default=None,
            placeholder="Haga clic para elegir..."
        )

    st.write("") # Espaciador

    # 2. RECUADRO DE PREVISUALIZACIÓN (Amigable a la vista)
    if seleccionadas:
        st.markdown("### 👁️ Previsualización de Carga")
        
        # Grid para mostrar "Cards" de previsualización
        cols_ins = st.columns(len(seleccionadas) if len(seleccionadas) <= 4 else 4)
        
        for idx, esp in enumerate(seleccionadas):
            with cols_ins[idx % 4]:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f0f2f6;
                        padding: 15px;
                        border-radius: 10px;
                        border-left: 5px solid #1B4F72;
                        margin-bottom: 10px;
                        min-height: 100px;
                    ">
                        <p style="margin:0; font-size: 0.8em; color: #555;">ESPECIALIDAD</p>
                        <p style="margin:0; font-weight: bold; color: #1B4F72;">{esp}</p>
                        <p style="margin:0; font-size: 0.7em; color: #28a745;">● Lista para insumos</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        
        # Tabla detallada abajo de las cards si se requiere más info
        with st.expander("Ver detalle de insumos calculados"):
            # Aquí puedes simular datos de insumos basados en los pacientes
            df_insumos_preview = pd.DataFrame({
                "Especialidad": seleccionadas,
                "Catéteres": [5] * len(seleccionadas),
                "Sondas": [3] * len(seleccionadas),
                "Antisépticos": ["OK"] * len(seleccionadas)
            })
            st.dataframe(df_insumos_preview, use_container_width=True)
            
        if st.button("📤 Procesar Insumos Seleccionados", type="primary"):
            st.toast(f"Procesando {len(seleccionadas)} especialidades...")
            
    else:
        st.warning("Seleccione al menos una especialidad arriba para previsualizar los insumos.")
