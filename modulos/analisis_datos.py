import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE REDACCIÓN ESPECÍFICA ---
def generar_analisis_clinico(df, col, is_multi):
    if is_multi:
        freqs = df[col].str.split(', ', expand=True).stack().value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
    
    top_cat = freqs.idxmax()
    col_lower = col.lower()
    
    # Análisis clínico segmentado
    if 'sexo' in col_lower:
        analisis = f"La prevalencia del sexo '{top_cat}' es un resultado esperado, ya que refleja la composición demográfica tradicional y predominante en el personal de enfermería en el entorno hospitalario."
    elif 'edad' in col_lower:
        analisis = f"La concentración del personal en el rango '{top_cat}' indica una fuerza laboral con experiencia, lo cual es un factor determinante para la estabilidad operativa de la unidad."
    elif 'anios' in col_lower:
        analisis = f"La distribución en el rango '{top_cat}' de años de servicio refleja una curva de aprendizaje consolidada, clave para la transferencia de conocimientos y la cultura de seguridad."
    elif any(x in col_lower for x in ['conocimiento', 'capacitacion', 'epp', 'lavado', 'barreras', 'accion']):
        analisis = f"La tendencia hacia '{top_cat}' evidencia la práctica actual. Sin embargo, la dispersión observada señala brechas operativas que requieren supervisión directa. Es necesario evaluar si estas variaciones en la aplicación de los protocolos son resultado de barreras estructurales o de falta de estandarización en la praxis asistencial."
    else:
        analisis = f"Se observa una tendencia hacia '{top_cat}'. Este resultado caracteriza la distribución operativa actual, proporcionando una base sólida para la toma de decisiones."
        
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
        
        # 1. CÁLCULO Y TABLA DE FUNDAMENTO (RESTAURADA)
        if col == 'Anios_Servicio':
            bins = [0, 5, 10, 15, 20, 25, 30, 100]
            labels = ['1-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31+']
            df['Anios_Grupo'] = pd.cut(df[col], bins=bins, labels=labels)
            counts = df['Anios_Grupo'].value_counts(sort=False)
            percents = (df['Anios_Grupo'].value_counts(normalize=True, sort=False) * 100).round(1)
            plot_df = pd.DataFrame({'Categoría': labels, 'Porcentaje': percents.values})
        elif is_multi:
            counts = df[col].str.split(', ', expand=True).stack().value_counts()
            percents = (counts / len(df) * 100).round(1)
            plot_df = pd.DataFrame({'Categoría': counts.index, 'Porcentaje': percents.values})
        else:
            counts = df[col].value_counts()
            percents = (counts / len(df) * 100).round(1)
            plot_df = pd.DataFrame({'Categoría': counts.index, 'Porcentaje': percents.values})
            
        # Mostrar Tabla de Fundamento
        tabla_fundamento = pd.DataFrame({'Frecuencia (n)': counts, 'Porcentaje (%)': percents})
        st.table(tabla_fundamento)
        
        # 2. GRÁFICA CON PORCENTAJES EN TODAS LAS BARRAS
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=plot_df, x='Categoría', y='Porcentaje', palette="viridis", ax=ax)
        
        # Forzar etiquetas en TODAS las barras
        for container in ax.containers:
            ax.bar_label(container, fmt='%.1f%%', padding=3)
            
        plt.xticks(rotation=45, ha='right')
        ax.set_ylabel("Frecuencia (%)")
        ax.set_xlabel("")
        st.pyplot(fig)
        
        # 3. REDACCIÓN ANALÍTICA
        st.markdown(generar_analisis_clinico(df, col, is_multi))
        st.write("---")
        
