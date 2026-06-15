import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE REDACCIÓN ESPECÍFICA ---
def generar_analisis_clinico(df, col, is_multi):
    # Cálculo de frecuencias
    if is_multi:
        freqs = df[col].str.split(', ', expand=True).stack().value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
    
    top_cat = freqs.idxmax()
    
    # Análisis específico por variable
    col_lower = col.lower()
    
    # 1. Variables Demográficas (Descripción objetiva)
    if 'sexo' in col_lower:
        analisis = f"La prevalencia del sexo '{top_cat}' es un resultado esperado, ya que refleja la composición demográfica tradicional y predominante en el personal de enfermería en el entorno hospitalario."
    elif 'edad' in col_lower:
        analisis = f"La concentración del personal en el rango '{top_cat}' indica una fuerza laboral con experiencia, lo cual es fundamental para la estabilidad operativa de la unidad."
    elif 'anios' in col_lower:
        analisis = f"La distribución en el rango '{top_cat}' de años de servicio refleja una curva de aprendizaje consolidada, la cual es clave para el mantenimiento de la cultura de seguridad en el hospital."
    
    # 2. Variables de Desempeño y Conocimiento (Análisis Crítico)
    elif any(x in col_lower for x in ['conocimiento', 'capacitacion', 'epp', 'lavado', 'barreras', 'accion']):
        analisis = f"La tendencia predominante hacia '{top_cat}' evidencia la práctica actual. Sin embargo, al observar la dispersión en las otras categorías, se identifican brechas operativas que requieren una supervisión directa. Es necesario analizar si estas variaciones en la aplicación de los protocolos son resultado de barreras estructurales o de falta de estandarización en la praxis asistencial."
    
    else:
        analisis = f"Se observa una tendencia hacia '{top_cat}'. Este resultado caracteriza la distribución operativa actual, permitiendo establecer una base para la toma de decisiones."
        
    return f"• {analisis}"

# --- INTERFAZ ---
st.title("🩺 Motor de Tesis: Análisis Clínico")
uploaded_file = st.file_uploader("Carga tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Fecha' in df.columns: df = df.drop(columns=['Fecha'])
    
    st.subheader("4.1 PRESENTACIÓN DE LA INFORMACIÓN")
    st.dataframe(df.describe(include='all').transpose())
    
    st.divider()
    
    st.subheader("4.2 ANÁLISIS DE LOS RESULTADOS")
    for col in df.columns:
        st.write(f"### Variable: {col}")
        is_multi = df[col].astype(str).str.contains(',').any()
        
        # Lógica de cálculo
        if col == 'Anios_Servicio':
            bins = [0, 5, 10, 15, 20, 25, 30, 100]
            labels = ['1-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31+']
            df['Anios_Grupo'] = pd.cut(df[col], bins=bins, labels=labels)
            plot_df = (df['Anios_Grupo'].value_counts(normalize=True, sort=False) * 100).reset_index()
            plot_df.columns = ['Categoría', 'Porcentaje']
        elif is_multi:
            frecuencias = df[col].str.split(', ', expand=True).stack().value_counts()
            porcentajes = (frecuencias / len(df) * 100).round(1)
            plot_df = pd.DataFrame({'Categoría': porcentajes.index, 'Porcentaje': porcentajes.values})
        else:
            porcentajes = (df[col].value_counts(normalize=True) * 100).reset_index()
            porcentajes.columns = ['Categoría', 'Porcentaje']
            plot_df = porcentajes
        
        # Gráfica Profesional
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=plot_df, x='Categoría', y='Porcentaje', palette="viridis", ax=ax)
        
        # Forzar etiquetas en todas las barras
        for container in ax.containers:
            ax.bar_label(container, fmt='%.1f%%', padding=3)
            
        plt.xticks(rotation=45, ha='right')
        ax.set_ylabel("Frecuencia (%)")
        ax.set_xlabel("")
        st.pyplot(fig)
        
        # Redacción específica
        st.markdown(generar_analisis_clinico(df, col, is_multi))
        st.write("---")
