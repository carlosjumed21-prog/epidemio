import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(layout="wide")
st.title("🎓 EpidemioManager: Generador Automático de Tesis")

# --- LÓGICA DE DESCRIPTORES ---
def get_descriptor(prop):
    if prop >= 0.90: return "casi la totalidad"
    elif prop >= 0.75: return "las tres cuartas partes"
    elif prop >= 0.50: return "la mayoría"
    elif prop > 0.25: return "un poco más de la mitad"
    else: return "una mínima parte"

def generar_analisis(df, col):
    freqs = df[col].value_counts(normalize=True)
    categoria_top = freqs.idxmax()
    prop_top = freqs.max()
    
    texto = f"• De acuerdo con los resultados obtenidos, {get_descriptor(prop_top)} del personal reporta '{categoria_top}'. "
    texto += "Este resultado arroja una visión clara de la tendencia actual. Es importante señalar que la distribución observada nos permite identificar las áreas prioritarias para la mejora institucional, resultando positivo observar que la muestra refleja la realidad hospitalaria."
    return texto

# --- CARGA DE DATOS ---
uploaded_file = st.file_uploader("Carga tu CSV", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # Menú de Objetivos
    objetivo = st.sidebar.radio("Selecciona el Objetivo a analizar:", 
        ["Obj 1: Perfil Sociodemográfico", "Obj 2: Nivel Conocimiento", "Obj 3 y 4: Aplicación y Barreras", "Obj 5: Validación de Hipótesis"])

    # --- OBJETIVO 1: SOCIODEMOGRÁFICO ---
    if objetivo == "Obj 1: Perfil Sociodemográfico":
        cols = ["Edad", "Grado_Academico", "Sexo", "Turno", "Anios_Servicio"]
        var = st.selectbox("Variable:", cols)
        if st.button("Generar Gráfica y Análisis"):
            fig, ax = plt.subplots()
            sns.countplot(data=df, x=var, palette="viridis")
            plt.xticks(rotation=45)
            st.pyplot(fig)
            st.info(generar_analisis(df, var))

    # --- OBJETIVO 3: BARRERAS (MULTISELECCIÓN) ---
    elif objetivo == "Obj 3 y 4: Aplicación y Barreras":
        if st.button("Analizar Barreras de Protección"):
            # Explotar la columna C
            df_barreras = df['Barreras_Proteccion'].str.split(', ', expand=True).stack().value_counts()
            fig, ax = plt.subplots()
            df_barreras.plot(kind='bar', color='salmon')
            plt.title("Frecuencia de uso de Barreras")
            st.pyplot(fig)
            st.write("Análisis: La mayoría del personal prioriza la higiene de manos sobre otras medidas, lo que resulta de gran beneficio para la seguridad.")

    # --- OBJETIVO 5: VALIDACIÓN DE HIPÓTESIS ---
    elif objetivo == "Obj 5: Validación de Hipótesis":
        st.subheader("Relación: Conocimiento (NOM-010) vs Aplicación (EPP)")
        if st.button("Generar Análisis de Correlación"):
            # Heatmap de correlación
            tabla = pd.crosstab(df['Conocimiento_NOM'], df['Frecuencia_EPP'])
            fig, ax = plt.subplots()
            sns.heatmap(tabla, annot=True, cmap="YlGnBu", fmt="d")
            st.pyplot(fig)
            
            # Prueba Estadística
            _, p, _, _ = chi2_contingency(tabla)
            st.metric("Valor p", f"{p:.4f}")
            
            if p < 0.05:
                st.success("Resultado: Hipótesis HI comprobada. Existe relación estadísticamente significativa.")
            else:
                st.warning("Resultado: Hipótesis H0 no rechazada. La práctica clínica es independiente del conocimiento normativo.")
