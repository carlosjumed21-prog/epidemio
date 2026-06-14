import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN Y FUNCIONES ---
def generar_resumen_general(df):
    """Genera una tabla resumen para la 'Tabla 1' de la tesis."""
    # Tabla para variables categóricas (Sex, Turno, Grado)
    cat_cols = ['Sexo', 'Turno', 'Grado_Academico', 'Capacitacion_VIH']
    cat_summary = []
    for col in cat_cols:
        if col in df.columns:
            counts = df[col].value_counts()
            percs = df[col].value_counts(normalize=True) * 100
            for val in counts.index:
                cat_summary.append({"Variable": col, "Categoría": val, "n": counts[val], "%": round(percs[val], 1)})
    
    # Tabla para variables numéricas (Edad, Años)
    num_cols = ['Anios_Servicio']
    num_summary = []
    for col in num_cols:
        if col in df.columns:
            num_summary.append({"Variable": col, "Media": round(df[col].mean(), 1), "Mediana": df[col].median(), "Moda": df[col].mode()[0]})
            
    return pd.DataFrame(cat_summary), pd.DataFrame(num_summary)

# --- INTERFAZ ---
st.title("🩺 Motor de Tesis: Análisis Epidemiológico")
uploaded_file = st.file_uploader("Carga tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Fecha' in df.columns: df = df.drop(columns=['Fecha'])
    
    # 1. RESUMEN GENERAL (TABLA 1)
    st.subheader("4.1 PRESENTACIÓN DE LA INFORMACIÓN")
    st.write("### Tabla 1: Características Sociodemográficas")
    cat_table, num_table = generar_resumen_general(df)
    st.table(cat_table)
    st.write("### Estadísticos de Tendencia Central")
    st.table(num_table)
    
    st.divider()
    
    # 2. ANÁLISIS DETALLADO (4.2)
    st.subheader("4.2 ANÁLISIS DE LOS RESULTADOS")
    for col in df.columns:
        if col in ['Sexo', 'Turno', 'Grado_Academico', 'Capacitacion_VIH', 'Anios_Servicio']:
            continue # Ya se cubrieron en la Tabla 1
            
        st.write(f"### Variable: {col}")
        
        # Gráfica
        is_multi = df[col].astype(str).str.contains(',').any()
        fig, ax = plt.subplots(figsize=(6, 3))
        if is_multi:
            data_plot = (df[col].str.split(', ', expand=True).stack().value_counts(normalize=True) * 100).reset_index()
            sns.barplot(data=data_plot, x='proportion', y='index', palette="viridis", ax=ax)
        else:
            sns.countplot(data=df, x=col, palette="viridis", ax=ax)
            plt.xticks(rotation=45)
        ax.set_ylabel("Frecuencia (%)")
        st.pyplot(fig)
        
        # Redacción (siguiendo reglas)
        # (Aquí va la lógica de redacción que ya teníamos)
        st.write("---")
