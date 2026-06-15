import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN DE REDACCIÓN ---
def generar_analisis_clinico(df, col, is_multi):
    # Cálculo de frecuencias
    if is_multi:
        freqs = df[col].str.split(', ', expand=True).stack().value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
    
    top_cat = freqs.idxmax()
    analysis_text = f"• Se observa una tendencia hacia la categoría '{top_cat}'. "
    
    # Análisis crítico contextual
    col_lower = col.lower()
    if 'anios' in col_lower:
        analysis_text += "La categorización por antigüedad permite identificar la madurez operativa del equipo. Una mayor concentración en rangos de servicio avanzados sugiere la presencia de personal con experiencia, cuya retención es vital para la transferencia de conocimiento y la seguridad del paciente."
    elif any(x in col_lower for x in ['conocimiento', 'capacitacion', 'epp']):
        analysis_text += "Esta distribución evidencia la adherencia a los estándares institucionales. Cualquier dispersión detectada señala una oportunidad para fortalecer los procesos de supervisión y capacitación continua."
    else:
        analysis_text += "Este resultado caracteriza la estructura operativa de la muestra, proporcionando una base clara para la interpretación del entorno hospitalario actual."
    
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
        
        # Lógica de agrupamiento para Anios_Servicio
        if col == 'Anios_Servicio':
            bins = [0, 5, 10, 15, 20, 25, 30, 100]
            labels = ['1-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31+']
            df['Anios_Grupo'] = pd.cut(df[col], bins=bins, labels=labels)
            plot_df = (df['Anios_Grupo'].value_counts(normalize=True, sort=False) * 100).reset_index()
            plot_df.columns = ['Categoría', 'Porcentaje']
        elif is_multi:
            porcentajes = (df[col].str.split(', ', expand=True).stack().value_counts(normalize=True) * 100).reset_index()
            porcentajes.columns = ['Categoría', 'Porcentaje']
            plot_df = porcentajes
        else:
            porcentajes = (df[col].value_counts(normalize=True) * 100).reset_index()
            porcentajes.columns = ['Categoría', 'Porcentaje']
            plot_df = porcentajes
        
        # Gráfica Profesional
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=plot_df, x='Categoría', y='Porcentaje', palette="viridis", ax=ax)
        
        # Etiquetas en todas las barras
        ax.bar_label(ax.containers[0], fmt='%.1f%%', padding=3)
        ax.set_ylabel("Frecuencia (%)")
        ax.set_xlabel("")
        st.pyplot(fig)
        
        # Redacción inteligente
        st.markdown(generar_analisis_clinico(df, col, is_multi))
        st.write("---")

    # 4.3 DISCUSIÓN
    st.subheader("4.3 DISCUSIÓN DE LOS RESULTADOS")
    v_indep, v_dep = "Conocimiento_NOM", "Frecuencia_EPP"
    if v_indep in df.columns and v_dep in df.columns:
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        _, p, _, _ = chi2_contingency(tabla)
        
        if p < 0.05:
            st.write("**Discusión:** Existe una relación estadísticamente significativa (p < 0.05). Esto valida que el conocimiento normativo es un factor predictivo del cumplimiento técnico, reforzando la importancia de la educación continua.")
        else:
            st.write("**Discusión:** La aplicación técnica es independiente del nivel de conocimiento (p > 0.05), sugiriendo la presencia de barreras estructurales o una insuficiente integración de la teoría en la praxis asistencial cotidiana.")
