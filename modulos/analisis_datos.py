import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="EpidemioManager - Análisis", layout="wide")

# --- FUNCIONES DE AUTOMATIZACIÓN ---
def obtener_descriptor(prop):
    if prop >= 0.90: 
        return "casi la totalidad"
    elif prop >= 0.75: 
        return "las tres cuartas partes"
    elif prop >= 0.50: 
        return "la mayoría"
    elif prop > 0.25: 
        return "un poco más de la mitad"
    else: 
        return "una mínima parte"

def generar_analisis_automatico(df, variable):
    freqs = df[variable].value_counts(normalize=True)
    frases = []
    for valor, prop in freqs.items():
        frases.append(f"{obtener_descriptor(prop)} de la población reporta '{valor}'")
    
    texto = f"De acuerdo con los resultados obtenidos en la variable **{variable}**, se observa que " + ", ".join(frases) + ". "
    texto += "Resulta positivo observar que esta distribución aporta información valiosa para comprender la práctica clínica actual."
    return texto

# --- INTERFAZ ---
st.title("📉 EpidemioManager: Generador de Resultados")
uploaded_file = st.file_uploader("Carga tu base de datos (CSV)", type=["csv"])

if uploaded_file is not None:
    # Cargar datos
    df = pd.read_csv(uploaded_file)
    st.success("✅ Base de datos cargada correctamente.")
    
    # Selección de análisis
    st.subheader("Análisis Bivariado (Hipótesis)")
    col1, col2 = st.columns(2)
    
    # Lista de columnas
    cols = df.columns.tolist()
    
    v_indep = col1.selectbox("Variable Independiente", cols)
    v_dep = col2.selectbox("Variable Dependiente", cols)
    
    if st.button("Ejecutar Análisis y Redacción"):
        # 1. Tabla
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        st.write("### Tabla de Contingencia")
        st.dataframe(tabla)
        
        # 2. Chi-cuadrado
        _, p, _, _ = chi2_contingency(tabla)
        st.metric("Valor p", f"{p:.4f}")
        
        # 3. Gráfica
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.heatmap(tabla, annot=True, cmap="Blues", fmt="d")
        st.pyplot(fig)
        
        # 4. Reporte Automático
        st.subheader("Análisis para la Tesis (Copiar y Pegar)")
        reporte = generar_analisis_automatico(df, v_dep)
        st.info(reporte)
        
        if p < 0.05:
            st.success("Nota: Existe evidencia estadística para rechazar la hipótesis nula (p < 0.05).")
        else:
            st.warning("Nota: No se encontró significancia estadística (p > 0.05).")
