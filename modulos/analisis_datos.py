import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN DE REDACCIÓN ---
def generar_analisis_clinico(df, col, is_multi):
    if is_multi:
        freqs = df[col].str.split(', ', expand=True).stack().value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
    
    top_cat = freqs.index[0]
    
    col_lower = col.lower()
    # Análisis clínico directo y objetivo
    if 'anios' in col_lower:
        analisis = f"La concentración de personal en '{top_cat}' refleja la experiencia acumulada en el servicio. Este segmento constituye el soporte técnico para la transferencia de conocimientos."
    elif any(x in col_lower for x in ['conocimiento', 'capacitacion']):
        analisis = f"El resultado hacia '{top_cat}' marca el nivel de competencia teórica actual. Es necesario contrastar si esta base teórica se traduce efectivamente en la aplicación técnica durante la atención."
    elif any(x in col_lower for x in ['epp', 'lavado', 'barreras']):
        analisis = f"La tendencia observada en '{top_cat}' establece el estándar de práctica actual. La dispersión en las otras categorías debe ser vigilada para evitar variabilidad en los procesos de seguridad."
    else:
        analisis = f"Los resultados muestran una inclinación hacia '{top_cat}', caracterizando la distribución operativa actual en la unidad."
    
    return f"• {analisis} Se requiere supervisión continua para asegurar la estandarización de los procesos."

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
        
        # 1. Tabla de fundamento
        if is_multi:
            frecuencias = df[col].str.split(', ', expand=True).stack().value_counts()
            porcentajes = (frecuencias / len(df) * 100).round(1)
        else:
            frecuencias = df[col].value_counts()
            porcentajes = (frecuencias / len(df) * 100).round(1)
            
        tabla_datos = pd.DataFrame({'Frecuencia (n)': frecuencias, 'Porcentaje (%)': porcentajes})
        st.table(tabla_datos)
        
        # 2. Gráfica Vertical con etiquetas en todas las barras
        plot_data = pd.DataFrame({'Categoría': porcentajes.index, 'Porcentaje': porcentajes.values})
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=plot_data, x='Categoría', y='Porcentaje', palette="viridis", ax=ax)
        
        # Rotación para que no se encimen y etiquetas en cada barra
        plt.xticks(rotation=45, ha='right')
        ax.bar_label(ax.containers[0], fmt='%.1f%%', padding=3)
        ax.set_ylabel("Frecuencia (%)")
        ax.set_xlabel("")
        st.pyplot(fig)
        
        # 3. Redacción profesional
        st.markdown(generar_analisis_clinico(df, col, is_multi))
        st.write("---")

    # 4.3 DISCUSIÓN
    st.subheader("4.3 DISCUSIÓN DE LOS RESULTADOS")
    v_indep, v_dep = "Conocimiento_NOM", "Frecuencia_EPP"
    if v_indep in df.columns and v_dep in df.columns:
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        _, p, _, _ = chi2_contingency(tabla)
        
        if p < 0.05:
            st.write("**Discusión:** La relación estadísticamente significativa (p < 0.05) valida que el conocimiento normativo es un factor predictivo del cumplimiento técnico.")
        else:
            st.write("**Discusión:** La independencia estadística (p > 0.05) sugiere que el conocimiento no se traduce automáticamente en praxis asistencial, indicando fallas estructurales.")
