import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN DE REDACCIÓN CRÍTICA ---
def generar_analisis_clinico(df, col, is_multi):
    # Cálculo de frecuencias y porcentajes
    if is_multi:
        freqs = df[col].str.split(', ', expand=True).stack().value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
    
    # Datos para el análisis
    top_cat = freqs.index[0]
    top_prop = freqs.iloc[0]
    
    # Análisis de contraste (identificar si hay una minoría significativa o una dispersión alta)
    analysis_text = f"• Se observa una tendencia predominante hacia '{top_cat}'. "
    
    # Lógica crítica: Comparar la mayoría vs el resto
    if len(freqs) > 1:
        segunda_cat = freqs.index[1]
        segunda_prop = freqs.iloc[1]
        
        # Si la segunda categoría tiene peso significativo (más del 20%)
        if segunda_prop > 0.20:
            analysis_text += f"No obstante, es relevante señalar que '{segunda_cat}' representa una proporción considerable. "
            analysis_text += "Esta divergencia en la práctica sugiere que, aunque el proceso está estandarizado, existe una variabilidad operativa que podría comprometer la uniformidad de los resultados clínicos. "
        else:
            analysis_text += "Este nivel de concentración indica una práctica asistencial consolidada en torno a este criterio, mostrando una baja variabilidad entre el personal evaluado. "
    
    # Contextualización clínica
    col_lower = col.lower()
    if any(x in col_lower for x in ['conocimiento', 'capacitacion', 'epp', 'lavado', 'barreras']):
        analysis_text += "Desde una perspectiva de gestión de riesgos, cualquier desviación respecto al estándar operativo principal debe ser monitorizada, ya que la inconsistencia en la aplicación de protocolos es, frecuentemente, el origen de eventos adversos."
    else:
        analysis_text += "La distribución observada es consistente con las características estructurales de la muestra y permite definir el perfil de operación actual en la unidad."
        
    return analysis_text

# --- INTERFAZ ---
st.title("🩺 Motor de Tesis: Análisis Clínico")
uploaded_file = st.file_uploader("Carga tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Fecha' in df.columns: df = df.drop(columns=['Fecha'])
    
    st.subheader("4.1 PRESENTACIÓN DE LA INFORMACIÓN")
    st.write("### Tabla 1: Resumen General de Variables")
    st.dataframe(df.describe(include='all').transpose())
    
    st.divider()
    
    st.subheader("4.2 ANÁLISIS DE LOS RESULTADOS")
    for col in df.columns:
        st.write(f"### Variable: {col}")
        is_multi = df[col].astype(str).str.contains(',').any()
        
        # Calcular proporciones
        if is_multi:
            porcentajes = (df[col].str.split(', ', expand=True).stack().value_counts(normalize=True) * 100).reset_index()
            porcentajes.columns = ['Categoría', 'Porcentaje']
        else:
            porcentajes = (df[col].value_counts(normalize=True) * 100).reset_index()
            porcentajes.columns = ['Categoría', 'Porcentaje']
        
        # Gráfica
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=porcentajes, x='Porcentaje', y='Categoría', palette="viridis", ax=ax)
        ax.bar_label(ax.containers[0], fmt='%.1f%%', padding=3)
        ax.set_ylabel("")
        ax.set_xlabel("Frecuencia (%)")
        st.pyplot(fig)
        
        # Redacción inteligente, analítica y crítica
        st.markdown(generar_analisis_clinico(df, col, is_multi))
        st.write("---")

    # 4.3 DISCUSIÓN
    st.subheader("4.3 DISCUSIÓN DE LOS RESULTADOS")
    v_indep, v_dep = "Conocimiento_NOM", "Frecuencia_EPP"
    if v_indep in df.columns and v_dep in df.columns:
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        _, p, _, _ = chi2_contingency(tabla)
        
        if p < 0.05:
            st.write("**Discusión:** Los hallazgos estadísticos confirman una correlación significativa (p < 0.05), lo que implica que el nivel de conocimiento técnico influye directamente en la adherencia operativa. Este resultado es un llamado a la estandarización de las competencias en el personal.")
        else:
            st.write("**Discusión:** La ausencia de una correlación estadísticamente significativa (p > 0.05) entre el nivel de conocimiento y la práctica clínica, pone en evidencia una desconexión crítica entre la teoría y la praxis hospitalaria, señalando fallas estructurales más que una falta de competencias individuales.")
