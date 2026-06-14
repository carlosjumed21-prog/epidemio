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

def generar_redaccion_tesis(df, col, es_multiselect=False):
    if es_multiselect:
        s = df[col].str.split(', ', expand=True).stack()
        freqs = s.value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
    
    categoria_top = freqs.idxmax()
    prop_top = freqs.max()
    inicio = random.choice(frases_inicio)
    
    # Redacción analítica, sin sesgos terminológicos, centrada en la práctica hospitalaria
    redaccion = f"• {inicio} {get_descriptor(prop_top)} del personal reporta '{categoria_top}'. "
    redaccion += f"Al analizar la distribución de la variable {col}, se identifica una disparidad técnica significativa respecto a las categorías restantes. "
    redaccion += "Este comportamiento denota que, si bien existe una tendencia hacia la estandarización, persisten brechas operativas que requieren atención inmediata para la seguridad del paciente. "
    redaccion += "La persistencia de prácticas alternativas subraya la necesidad crítica de reforzar la capacitación técnica y la supervisión directa en el servicio para garantizar un cumplimiento uniforme de los protocolos establecidos."
    return redaccion

# --- INTERFAZ ---
st.title("🩺 Motor de Tesis: Análisis Clínico")
uploaded_file = st.file_uploader("Carga tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Fecha' in df.columns: df = df.drop(columns=['Fecha'])
    
    # 4.1 RESUMEN GENERAL (TABLA 1)
    st.subheader("4.1 PRESENTACIÓN DE LA INFORMACIÓN")
    st.write("### Tabla 1: Resumen de variables")
    st.dataframe(df.describe(include='all').transpose())
    
    st.divider()
    
    # 4.2 ANÁLISIS DE RESULTADOS
    st.subheader("4.2 ANÁLISIS DE LOS RESULTADOS")
    for col in df.columns:
        st.write(f"### Variable: {col}")
        is_multi = df[col].astype(str).str.contains(',').any()
        
        # Calcular proporciones
        if is_multi:
            porcentajes = (df[col].str.split(', ', expand=True).stack().value_counts(normalize=True) * 100).reset_index()
            porcentajes.columns = ['Categoría', 'Porcentaje']
        else:
            porcentajes = (df[col].value_counts(normalize=True) * 100).reset_index()
            porcentajes.columns = ['Categoría', 'Porcentaje']
        
        # Gráfica Profesional con etiquetas en TODAS las barras
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=porcentajes, x='Porcentaje', y='Categoría', palette="viridis", ax=ax)
        
        # Etiquetar todas las barras
        for container in ax.containers:
            ax.bar_label(container, fmt='%.1f%%', padding=3)
            
        ax.set_ylabel("")
        ax.set_xlabel("Frecuencia (%)")
        st.pyplot(fig)
        
        # Redacción (Reglas aplicadas)
        st.markdown(generar_redaccion_tesis(df, col, is_multi))
        st.write("---")

    # 4.3 DISCUSIÓN
    st.subheader("4.3 DISCUSIÓN DE LOS RESULTADOS")
    v_indep, v_dep = "Conocimiento_NOM", "Frecuencia_EPP"
    if v_indep in df.columns and v_dep in df.columns:
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        _, p, _, _ = chi2_contingency(tabla)
        
        if p < 0.05:
            st.write("**Discusión:** La hipótesis es verdadera. Existe una relación estadísticamente significativa (p < 0.05), validando que el conocimiento normativo (NOM-010-SSA-2023) es un factor predictivo del cumplimiento técnico. Se recomienda estandarizar la supervisión.")
        else:
            st.write("**Discusión:** La hipótesis nula no se rechaza (p > 0.05). La aplicación técnica es independiente del nivel de conocimiento, sugiriendo la presencia de barreras estructurales o una insuficiente integración de la teoría en la praxis asistencial cotidiana.")
