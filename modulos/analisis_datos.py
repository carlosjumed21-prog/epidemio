import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from scipy.stats import chi2_contingency

# --- REGLAS DE REDACCIÓN ---
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

def generar_observacion_tabla(col, categoria_top):
    return f"**Observación:** La tabla describe la distribución de frecuencias para {col}, donde la categoría predominante '{categoria_top}' concentra la mayor parte de la muestra, reflejando una tendencia clara en el comportamiento del personal ante esta variable."

def generar_redaccion_tesis(df, col, es_multiselect=False):
    if es_multiselect:
        s = df[col].str.split(', ', expand=True).stack()
        freqs = s.value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
        
    categoria_top = freqs.idxmax()
    prop_top = freqs.max()
    inicio = random.choice(frases_inicio)
    
    redaccion = f"• {inicio} {get_descriptor(prop_top)} del personal reporta '{categoria_top}'. "
    redaccion += f"Este hallazgo es fundamental para comprender la variable {col} en el contexto de nuestra investigación epidemiológica. "
    redaccion += "Es importante señalar que la distribución observada nos permite identificar las áreas prioritarias para la mejora institucional y la mitigación de riesgos biológicos. "
    redaccion += "El análisis de esta pregunta confirma que la percepción del personal es un factor clave en la dinámica de bioseguridad, validando la imperante necesidad de estrategias de capacitación continua alineadas a la normativa vigente."
    return redaccion

# --- INTERFAZ ---
st.title("🩺 Motor de Tesis: Análisis Profesional")
uploaded_file = st.file_uploader("Carga tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Fecha' in df.columns: df = df.drop(columns=['Fecha'])
    
    st.subheader("4.1 y 4.2 Análisis de Resultados")
    
    for col in df.columns:
        st.write(f"### Variable: {col}")
        is_multi = df[col].astype(str).str.contains(',').any()
        
        # 1. Tabla de evidencia
        if is_multi:
            frecuencias = df[col].str.split(', ', expand=True).stack().value_counts()
            porcentajes = df[col].str.split(', ', expand=True).stack().value_counts(normalize=True) * 100
        else:
            frecuencias = df[col].value_counts()
            porcentajes = df[col].value_counts(normalize=True) * 100
        
        tabla_datos = pd.DataFrame({'Frecuencia (n)': frecuencias, 'Porcentaje (%)': porcentajes.round(1)})
        st.table(tabla_datos)
        st.write(generar_observacion_tabla(col, porcentajes.idxmax()))
        
        # 2. Gráfica Proporcional con Etiquetas
        fig, ax = plt.subplots(figsize=(7, 4))
        if is_multi:
            plot_df = porcentajes.reset_index()
            sns.barplot(data=plot_df, x='proportion', y='index', palette="viridis", ax=ax)
            ax.set_xlabel("Frecuencia (%)")
            # Etiquetas en barras
            ax.bar_label(ax.containers[0], fmt='%.1f%%', padding=3)
        else:
            sns.countplot(data=df, x=col, palette="viridis", ax=ax)
            plt.xticks(rotation=45)
            ax.set_ylabel("Frecuencia (n)")
            # Etiquetas en barras
            ax.bar_label(ax.containers[0], fmt='%d (%.0f%%)')
            
        st.pyplot(fig)
        
        # 3. Redacción profesional (Reglas de estilo)
        st.markdown(generar_redaccion_tesis(df, col, is_multi))
        st.write("---")
