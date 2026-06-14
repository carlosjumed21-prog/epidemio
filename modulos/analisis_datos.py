import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN DE REDACCIÓN ---
frases_inicio = [
    "De acuerdo con los resultados obtenidos se observa que",
    "Este resultado arroja que",
    "Podemos observar que la mayoría",
    "Es trascendente saber que",
    "Con los datos obtenidos se observa que",
    "Observando los resultados obtenidos se identifica que",
    "Resulta positivo observar que la mayoría de la población"
]

def get_descriptor(prop):
    if prop >= 0.90: return "casi la totalidad"
    elif prop >= 0.75: return "las tres cuartas partes"
    elif prop >= 0.50: return "la mayoría"
    elif prop > 0.25: return "un poco más de la mitad"
    else: return "una mínima parte"

def generar_redaccion_tesis(df, col, is_multi):
    # Cálculo de frecuencias
    if is_multi:
        freqs = df[col].str.split(', ', expand=True).stack().value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
    
    categoria_top = freqs.idxmax()
    prop_top = freqs.max()
    inicio = random.choice(frases_inicio)
    
    # Análisis de dispersión: (si la categoría top < 50%, hay alta dispersión, lo cual es un hallazgo crítico)
    dispersión = "alta" if prop_top < 0.50 else "concentrada"
    
    redaccion = f"• {inicio} {get_descriptor(prop_top)} del personal reporta '{categoria_top}'. "
    
    # Análisis crítico
    if dispersión == "alta":
        redaccion += f"El hecho de que los resultados se encuentren distribuidos sin una tendencia dominante en {col}, sugiere una falta de estandarización en la práctica clínica actual. "
        redaccion += "Esta variabilidad en la respuesta es un indicador crítico de heterogeneidad operativa, lo cual aumenta el riesgo de inconsistencias en el cumplimiento de los protocolos establecidos. "
        redaccion += "Resulta imperativo analizar los factores causales que impiden que esta variable converja hacia un criterio único y seguro."
    else:
        redaccion += f"Al analizar la distribución de {col}, se identifica una tendencia consolidada en la muestra. "
        redaccion += "Este comportamiento demuestra un nivel de uniformidad que, si bien es favorable para la estandarización, debe ser contrastado con la normativa vigente para asegurar que la práctica actual sea realmente efectiva. "
        redaccion += "Es importante señalar que la distribución observada facilita la identificación de áreas donde la institución ha logrado una madurez operativa, permitiendo enfocar los recursos de mejora en los segmentos disidentes."
    
    return redaccion

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
        
        # 2. Gráfica Proporcional
        plot_data = pd.DataFrame({'Categoría': porcentajes.index, 'Porcentaje': porcentajes.values})
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(data=plot_data, x='Porcentaje', y='Categoría', palette="viridis", ax=ax)
        
        # Etiquetas en todas las barras
        for container in ax.containers:
            ax.bar_label(container, fmt='%.1f%%', padding=3)
        
        ax.set_ylabel("")
        ax.set_xlabel("Frecuencia (%)")
        st.pyplot(fig)
        
        # 3. Redacción Analítica y Crítica
        st.markdown(generar_redaccion_tesis(df, col, is_multi))
        st.write("---")

    # 4.3 DISCUSIÓN DE HIPÓTESIS
    st.subheader("4.3 DISCUSIÓN DE LOS RESULTADOS")
    v_indep, v_dep = "Conocimiento_NOM", "Frecuencia_EPP"
    if v_indep in df.columns and v_dep in df.columns:
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        _, p, _, _ = chi2_contingency(tabla)
        
        if p < 0.05:
            st.write("**Discusión:** La hipótesis es verdadera. Existe una relación estadísticamente significativa (p < 0.05), validando que el conocimiento normativo (NOM-010-SSA-2023) es un factor predictivo del cumplimiento técnico. La coherencia entre el saber y el hacer es el eje central de este hallazgo.")
        else:
            st.write("**Discusión:** La hipótesis nula no se rechaza (p > 0.05). La aplicación técnica es independiente del nivel de conocimiento, lo cual es un hallazgo crítico que sugiere la existencia de barreras estructurales o una insuficiente integración de la teoría en la praxis asistencial cotidiana.")
