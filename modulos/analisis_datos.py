import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN ESTÉTICA PARA TESIS ---
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'

def generar_grafica(df, var_x, var_y=None):
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # CASO 1: Análisis Descriptivo (Una sola variable)
    if var_y is None:
        if df[var_x].nunique() <= 10:
            # Gráfica de barras ordenada
            order = df[var_x].value_counts().index
            sns.countplot(data=df, x=var_x, order=order, palette="Blues_d", ax=ax)
            ax.set_title(f"Distribución de {var_x}")
        else:
            # Histograma para variables numéricas o con muchos datos
            sns.histplot(data=df, x=var_x, kde=True, color="skyblue", ax=ax)
            ax.set_title(f"Distribución de {var_x}")
    
    # CASO 2: Análisis de Hipótesis (Dos variables)
    else:
        # Barras apiladas al 100% (La mejor para ver relación proporcional)
        tabla = pd.crosstab(df[var_x], df[var_y], normalize='index') * 100
        tabla.plot(kind='bar', stacked=True, ax=ax, colormap="viridis")
        ax.set_title(f"Relación: {var_x} vs {var_y}")
        ax.set_ylabel("Porcentaje (%)")
        plt.legend(title=var_y, bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    return fig

# --- INTERFAZ DE AUTOMATIZACIÓN ---
st.title("📊 Generador Visual de Tesis")
uploaded_file = st.file_uploader("Carga tu CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    opcion = st.sidebar.radio("Sección:", ["Descriptiva", "Hipótesis"])
    
    if opcion == "Descriptiva":
        var = st.selectbox("Selecciona variable:", df.columns)
        if st.button("Generar Gráfica"):
            st.pyplot(generar_grafica(df, var))
            
    elif opcion == "Hipótesis":
        st.write("Cruce de variables para validación:")
        v1 = st.selectbox("Variable Independiente (Conocimiento):", df.columns)
        v2 = st.selectbox("Variable Dependiente (Aplicación):", df.columns)
        if st.button("Generar Gráfica de Correlación"):
            st.pyplot(generar_grafica(df, v1, v2))
