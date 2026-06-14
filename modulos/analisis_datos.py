import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN DE REDACCIÓN (REGLAS DE ORO) ---
frases_inicio = [
    "De acuerdo con los resultados obtenidos se observa que",
    "Este resultado arroja que",
    "Podemos observar que la mayoría",
    "Es trascendente saber que",
    "Con los datos obtenidos se observa que",
    "Observando los resultados obtenidos se identifica que",
    "Las tres cuartas partes de la población están conscientes de",
    "Con los datos obtenidos se puede comprobar que",
    "Es importante señalar que un poco más de la mitad de la población menciona",
    "Resulta positivo observar que la mayoría de la población"
]

def get_descriptor(prop):
    if prop >= 0.90: return "casi la totalidad"
    elif prop >= 0.75: return "las tres cuartas partes"
    elif prop >= 0.50: return "la mayoría"
    elif prop > 0.25: return "un poco más de la mitad"
    else: return "una mínima parte"

def generar_redaccion_tesis(df, col, es_multiselect=False):
    # Lógica para contar frecuencias
    if es_multiselect:
        s = df[col].str.split(', ', expand=True).stack()
        freqs = s.value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
        
    categoria_top = freqs.idxmax()
    prop_top = freqs.max()
    inicio = random.choice(frases_inicio)
    
    # Redacción ajustada a 4-5 renglones, sin porcentajes numéricos
    redaccion = f"• {inicio} {get_descriptor(prop_top)} del personal reporta '{categoria_top}'. "
    redaccion += f"Este hallazgo es fundamental para comprender la variable {col} en el contexto de nuestra investigación. "
    redaccion += "Es importante señalar que la distribución observada nos permite identificar las áreas prioritarias para la mejora institucional. "
    redaccion += "El análisis de esta pregunta confirma que la percepción del personal es un factor clave en la dinámica de bioseguridad y, por lo tanto, valida la necesidad de estrategias de capacitación continua."
    return redaccion

# --- INTERFAZ ---
st.title("🩺 Motor de Tesis: Análisis Epidemiológico")
uploaded_file = st.file_uploader("Carga tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Fecha' in df.columns: df = df.drop(columns=['Fecha'])
    
    # 4.1 RESUMEN GENERAL (TABLA 1)
    st.subheader("4.1 PRESENTACIÓN DE LA INFORMACIÓN")
    st.write("### Tabla 1: Características Sociodemográficas")
    
    # Generar tabla general rápida
    tabla_resumen = df.describe(include='all').transpose()
    st.dataframe(tabla_resumen)
    
    st.divider()
    
    # 4.2 ANÁLISIS DETALLADO
    st.subheader("4.2 ANÁLISIS DE LOS RESULTADOS")
    
    for col in df.columns:
        st.write(f"#### Análisis de: {col}")
        is_multi = df[col].astype(str).str.contains(',').any()
        
        # 1. Tabla de frecuencias (Números y porcentajes para la evidencia)
        if is_multi:
            frecuencias = df[col].str.split(', ', expand=True).stack().value_counts()
            porcentajes = df[col].str.split(', ', expand=True).stack().value_counts(normalize=True) * 100
        else:
            frecuencias = df[col].value_counts()
            porcentajes = df[col].value_counts(normalize=True) * 100
        
        st.table(pd.DataFrame({'Frecuencia': frecuencias, 'Porcentaje (%)': porcentajes.round(2)}))
        
        # 2. Gráfica Proporcional
        fig, ax = plt.subplots(figsize=(6, 3))
        if is_multi:
            data_plot = (porcentajes).reset_index()
            sns.barplot(data=data_plot, x='proportion', y='index', palette="viridis", ax=ax)
        else:
            sns.countplot(data=df, x=col, palette="viridis", ax=ax)
            plt.xticks(rotation=45)
        
        ax.set_xlabel("Frecuencia (%)")
        st.pyplot(fig)
        
        # 3. Redacción profesional (Reglas de estilo)
        st.markdown(generar_redaccion_tesis(df, col, is_multi))
        st.write("---")

    # 4.3 DISCUSIÓN DE HIPÓTESIS
    st.subheader("4.3 DISCUSIÓN DE LOS RESULTADOS")
    v_indep, v_dep = "Conocimiento_NOM", "Frecuencia_EPP"
    tabla = pd.crosstab(df[v_indep], df[v_dep])
    _, p, _, _ = chi2_contingency(tabla)
    
    if p < 0.05:
        st.write("**Discusión:** La hipótesis es verdadera. Existe una relación estadísticamente significativa (p < 0.05), validando que el conocimiento normativo (NOM-010-SSA-2023) es el factor predictivo del cumplimiento técnico.")
    else:
        st.write("**Discusión:** La hipótesis nula no se rechaza (p > 0.05). La aplicación técnica es independiente del nivel de conocimiento, sugiriendo barreras estructurales (falta de insumos o carga laboral) más que una deficiencia cognitiva.")
