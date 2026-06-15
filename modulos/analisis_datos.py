import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN DE REDACCIÓN ---
def generar_analisis_clinico(df, col, is_multi):
    if is_multi:
        freqs = df[col].str.split(', ', expand=True).stack().value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
    
    top_cat = freqs.idxmax()
    
    # Redacción con conexión teórica (Aquí es donde fundamentas tu tesis)
    analisis = f"La tendencia predominante hacia '{top_cat}' refleja la dinámica operativa actual. "
    
    # Conexión con teoría (Fundamentación)
    col_lower = col.lower()
    if any(x in col_lower for x in ['conocimiento', 'capacitacion']):
        analisis += "Este hallazgo se alinea con la teoría de la conducta organizacional, donde la competencia técnica es el pilar de la seguridad asistencial. La brecha observada cuestiona si el modelo de capacitación actual es suficiente para garantizar la adherencia a la NOM-010."
    elif any(x in col_lower for x in ['epp', 'lavado', 'barreras']):
        analisis += "Este resultado es consistente con los modelos de seguridad del paciente que señalan el error humano como un factor multicausal. La variabilidad detectada indica que el cumplimiento no depende solo de la voluntad individual, sino de la estandarización del proceso asistencial."
    else:
        analisis += "Estos datos permiten caracterizar la estructura de la muestra, sirviendo como fundamento empírico para contrastar la realidad institucional con los estándares de calidad vigentes."
        
    return f"• {analisis} Se requiere una revisión de las estrategias actuales de gestión para asegurar que la práctica clínica converja con los estándares teóricos."

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
        
        # Cálculo de datos
        if is_multi:
            frecuencias = df[col].str.split(', ', expand=True).stack().value_counts()
            porcentajes = (frecuencias / len(df) * 100).round(1)
        else:
            frecuencias = df[col].value_counts()
            porcentajes = (frecuencias / len(df) * 100).round(1)
            
        # Gráfica Profesional
        plot_data = pd.DataFrame({'Categoría': porcentajes.index, 'Porcentaje': porcentajes.values})
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=plot_data, x='Categoría', y='Porcentaje', palette="viridis", ax=ax)
        
        # CORRECCIÓN: Etiquetado robusto para todas las barras
        for p in ax.patches:
            ax.annotate(f'{p.get_height():.1f}%', 
                        (p.get_x() + p.get_width() / 2., p.get_height()), 
                        ha = 'center', va = 'center', 
                        xytext = (0, 9), 
                        textcoords = 'offset points')
        
        plt.xticks(rotation=45, ha='right')
        ax.set_ylabel("Frecuencia (%)")
        ax.set_xlabel("")
        st.pyplot(fig)
        
        # Análisis con fundamento teórico
        st.markdown(generar_analisis_clinico(df, col, is_multi))
        st.write("---")

    # 4.3 DISCUSIÓN
    st.subheader("4.3 DISCUSIÓN DE LOS RESULTADOS")
    v_indep, v_dep = "Conocimiento_NOM", "Frecuencia_EPP"
    if v_indep in df.columns and v_dep in df.columns:
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        _, p, _, _ = chi2_contingency(tabla)
        
        # Conclusión teórica de la discusión
        conclusion_teorica = "Esto sugiere una desconexión entre la norma técnica y la práctica asistencial, validando la hipótesis de barreras estructurales." if p > 0.05 else "Esto valida que el conocimiento normativo es un pilar fundamental para la práctica segura."
        
        st.write(f"**Discusión:** {conclusion_teorica} Este hallazgo refuerza la necesidad de integrar la normativa vigente con la supervisión operativa diaria, superando el enfoque tradicional de capacitación aislada.")
