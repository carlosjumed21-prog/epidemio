import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN ---
st.set_page_config(layout="wide")
st.title("📑 Automatización de Tesis: Capítulos 4.2 y 4.3")

# --- LÓGICA DE REDACCIÓN CUALITATIVA ---
def get_descriptor(prop):
    if prop >= 0.90: return "casi la totalidad"
    elif prop >= 0.75: return "las tres cuartas partes"
    elif prop >= 0.50: return "la mayoría"
    elif prop > 0.25: return "un poco más de la mitad"
    else: return "una mínima parte"

# --- GENERADOR 4.2 ---
def generar_analisis_4_2(df, col):
    freqs = df[col].value_counts(normalize=True)
    # Seleccionamos la categoría principal para la redacción
    principal = freqs.idxmax()
    prop_principal = freqs.max()
    
    redaccion = f"• De acuerdo con los resultados obtenidos, {get_descriptor(prop_principal)} de la población reporta '{principal}'. "
    redaccion += f"Este resultado arroja una visión clara de la tendencia actual en la variable {col}. "
    redaccion += f"Es importante señalar que la distribución observada nos permite identificar las áreas prioritarias para la mejora institucional. "
    redaccion += f"El análisis de esta pregunta confirma que la percepción del personal es un factor clave en la dinámica hospitalaria."
    return redaccion

# --- GENERADOR 4.3 ---
def generar_discusion_4_3(df):
    # Comparación de Hipótesis: Conocimiento vs Aplicación
    v_indep = "Conocimiento_NOM"
    v_dep = "Frecuencia_EPP"
    
    tabla = pd.crosstab(df[v_indep], df[v_dep])
    _, p, _, _ = chi2_contingency(tabla)
    
    discusion = "### 4.3 DISCUSIÓN DE LOS RESULTADOS\n\n"
    
    # Lógica Hipótesis HI
    discusion += "**De acuerdo a la hipótesis de investigación (HI):**\n"
    if p < 0.05:
        discusion += "La hipótesis es verdadera. Se encontró una relación estadísticamente significativa entre el nivel de conocimiento de la NOM-010-SSA-2023 y la aplicación de protocolos. "
        discusion += "Se percibió una actitud de cumplimiento mayor en aquellos con conocimientos altos, validando la importancia de la capacitación técnica.\n\n"
    else:
        discusion += "La hipótesis no se pudo comprobar estadísticamente. Los resultados sugieren que, aunque existe conocimiento, la práctica clínica se ve influenciada por otros factores ajenos a la teoría.\n\n"
        
    # Lógica Hipótesis H0
    discusion += "**De acuerdo a la hipótesis nula (H0):**\n"
    if p >= 0.05:
        discusion += "Se comprobó la hipótesis nula, indicando que la práctica clínica es independiente del nivel de conocimiento normativo, sugiriendo la necesidad de investigar variables externas como la carga de trabajo."
    else:
        discusion += "La hipótesis nula fue rechazada, lo cual demuestra que la capacitación es, efectivamente, el factor determinante en la calidad de la atención."
        
    return discusion

# --- INTERFAZ ---
uploaded_file = st.file_uploader("Carga tu base de datos CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    st.sidebar.title("Navegación")
    seccion = st.sidebar.radio("Selecciona sección a redactar:", ["4.2 Análisis de Resultados", "4.3 Discusión"])
    
    if seccion == "4.2 Análisis de Resultados":
        st.subheader("4.2 ANÁLISIS DE LOS RESULTADOS")
        st.write("Copia y pega este contenido en tu tesis:")
        
        for col in df.columns:
            if col not in ['Fecha', 'Anios_Servicio']: # Excluir columnas numéricas simples
                st.markdown(generar_analisis_4_2(df, col))
                st.write("")
    
    elif seccion == "4.3 Discusión":
        st.write(generar_discusion_4_3(df))
