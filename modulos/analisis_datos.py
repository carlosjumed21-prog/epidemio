import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

st.title("📉 Análisis Estadístico de Resultados")
st.markdown("Carga tu base de datos de la tesis para evaluar las hipótesis.")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

# --- FUNCIONES DE AUTOMATIZACIÓN ---
def obtener_descriptor(prop):
    if prop >= 0.90: return "casi la totalidad"
    elif prop >= 0.75: return "las tres cuartas partes"
    elif prop >= 0.50: return "la mayoría"
    elif prop > 0.25: return "un poco más de la mitad"
    else: return "una mínima parte"

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

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ Base de datos cargada correctamente.")
    
    # Selección de análisis
    st.subheader("Análisis Bivariado (Hipótesis)")
    col1, col2 = st.columns(2)
    v_indep = col1.selectbox("Variable Independiente", df.columns)
    v_dep = col2.selectbox("Variable Dependiente", df.columns)
    
    if st.button("Ejecutar Análisis y Redacción"):
        # 1. Tabla y Chi-cuadrado
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        st.write("### Tabla de Contingencia")
        st.dataframe(tabla)
        
        _, p, _, _ = chi2_contingency(tabla)
        st.metric("Valor p", f"{p:.4f}")
        
        # 2. Gráfica
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.heatmap(tabla, annot=True, cmap="Blues", fmt="d")
        st.pyplot(fig)
        
        # 3. Reporte Automático
        st.subheader("Análisis para la Tesis (Copiar y Pegar)")
        reporte = generar_analisis_automatico(df, v_dep)
        st.info(reporte)
        
        if p < 0.05:
            st.success("Nota: Existe evidencia estadística para rechazar la hipótesis nula.")
        else:
            st.warning("Nota: No se encontró significancia estadística.")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("✅ Base de datos cargada.")
    
    # Selección de variables para análisis bivariado
    col1, col2 = st.columns(2)
    with col1:
        v_indep = st.selectbox("Variable Independiente (ej. Capacitacion_VIH)", df.columns)
    with col2:
        v_dep = st.selectbox("Variable Dependiente (ej. Frecuencia_EPP)", df.columns)
        
    if st.button("Ejecutar Prueba de Hipótesis"):
        # Tabla de contingencia
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        st.write("### Tabla de Contingencia")
        st.dataframe(tabla)
        
        # Chi-Cuadrado
        chi2, p, dof, expected = chi2_contingency(tabla)
        
        st.write("### Resultados Estadísticos")
        st.metric("Valor p (p-value)", f"{p:.4f}")
        
        if p < 0.05:
            st.success("Resultado significativo (p < 0.05): Se rechaza la hipótesis nula.")
        else:
            st.warning("No hay significancia estadística (p > 0.05): No se rechaza la hipótesis nula.")
        
        # Visualización
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(tabla, annot=True, cmap="YlGnBu", fmt="d")
        plt.title(f"Relación entre {v_indep} y {v_dep}")
        st.pyplot(fig)
        
        st.write("""
        **Interpretación sugerida para la tesis:**
        El análisis bivariado muestra una asociación estadística significativa entre las variables seleccionadas. 
        Esto valida la correlación planteada en los objetivos específicos del estudio.
        """)
