import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN DE REDACCIÓN ---
def generar_analisis_clinico(df, col, is_multi):
    # Calcular frecuencias para el análisis
    if is_multi:
        freqs = df[col].str.split(', ', expand=True).stack().value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
    
    top_cat = freqs.index[0]
    
    # Análisis crítico específico
    col_lower = col.lower()
    if 'anios' in col_lower:
        analisis = f"La distribución del personal muestra una concentración principal en el rango '{top_cat}'. Este dato es clave para valorar la madurez operativa de la unidad, donde una mayor antigüedad sugiere una estabilidad técnica que favorece la seguridad del paciente."
    elif any(x in col_lower for x in ['conocimiento', 'capacitacion']):
        analisis = f"El resultado predominante hacia '{top_cat}' evidencia el nivel de competencia teórica actual. Es crítico considerar si esta posición es suficiente para mitigar los riesgos identificados o si existen brechas que el personal aún no ha logrado solventar."
    elif any(x in col_lower for x in ['epp', 'lavado', 'barreras']):
        analisis = f"La tendencia observada en '{top_cat}' marca el estándar de práctica actual. Sin embargo, la dispersión en las categorías restantes indica que no existe una estandarización total, lo que representa un riesgo potencial en la continuidad de la seguridad asistencial."
    else:
        analisis = f"La muestra se inclina predominantemente hacia '{top_cat}'. Esta distribución caracteriza el perfil operativo actual y sirve como línea base para identificar desviaciones en el desempeño clínico."
    
    return f"• {analisis} Se observa una variabilidad que requiere atención en la supervisión de los procesos."

# --- INTERFAZ ---
st.title("🩺 Motor de Tesis: Análisis Clínico")
uploaded_file = st.file_uploader("Carga tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Fecha' in df.columns: df = df.drop(columns=['Fecha'])
    
    # 4.1 RESUMEN GENERAL (TABLA 1)
    st.subheader("4.1 PRESENTACIÓN DE LA INFORMACIÓN")
    st.write("### Tabla 1: Resumen General de Variables")
    st.dataframe(df.describe(include='all').transpose())
    
    st.divider()
    
    # 4.2 ANÁLISIS DE RESULTADOS
    st.subheader("4.2 ANÁLISIS DE LOS RESULTADOS")
    for col in df.columns:
        st.write(f"### Variable: {col}")
        is_multi = df[col].astype(str).str.contains(',').any()
        
        # 1. Tabla de fundamento (Evidencia de datos)
        if is_multi:
            freqs = df[col].str.split(', ', expand=True).stack().value_counts()
            porcentajes = (freqs / len(df) * 100).round(1)
        else:
            freqs = df[col].value_counts()
            porcentajes = (freqs / len(df) * 100).round(1)
            
        # Lógica de agrupación para Años de Servicio (Binning)
        if col == 'Anios_Servicio':
            df_plot = pd.DataFrame({'Categoría': porcentajes.index.astype(str), 'Porcentaje': porcentajes.values})
        else:
            df_plot = pd.DataFrame({'Categoría': porcentajes.index, 'Porcentaje': porcentajes.values})
            
        st.table(pd.DataFrame({'Frecuencia (n)': freqs, 'Porcentaje (%)': porcentajes}))
        
        # 2. Gráfica Horizontal Profesional
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.barplot(data=df_plot, x='Porcentaje', y='Categoría', palette="viridis", ax=ax)
        
        # Etiquetas exactas en todas las barras
        ax.bar_label(ax.containers[0], fmt='%.1f%%', padding=5)
        ax.set_ylabel("")
        ax.set_xlabel("Porcentaje de participantes (%)")
        st.pyplot(fig)
        
        # 3. Redacción Analítica y Crítica
        st.markdown(generar_analisis_clinico(df, col, is_multi))
        st.write("---")
