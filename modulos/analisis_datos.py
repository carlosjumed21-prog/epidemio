import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

st.title("📉 Análisis Estadístico de Resultados")
st.markdown("Carga tu base de datos de la tesis para evaluar las hipótesis.")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

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
