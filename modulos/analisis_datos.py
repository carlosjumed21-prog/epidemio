import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN Y FUNCIONES ---
def get_stats_summary(df, col):
    """Calcula estadísticos descriptivos automáticamente."""
    if pd.api.types.is_numeric_dtype(df[col]) or df[col].nunique() > 10:
        # Para variables numéricas (Edad/Años de Servicio)
        return pd.DataFrame({
            "Estadístico": ["Media", "Mediana", "Moda"],
            "Valor": [df[col].mean(), df[col].median(), df[col].mode()[0]]
        })
    else:
        # Para variables categóricas (Sexo/Turno)
        freqs = df[col].value_counts()
        percs = df[col].value_counts(normalize=True) * 100
        return pd.DataFrame({"Frecuencia (n)": freqs, "Porcentaje (%)": percs.round(2)})

def generar_redaccion_tesis(df, col, es_multiselect=False):
    # Lógica de redacción (sin incluir porcentajes numéricos)
    if es_multiselect:
        s = df[col].str.split(', ', expand=True).stack()
        freqs = s.value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
        
    categoria_top = freqs.idxmax()
    prop_top = freqs.max()
    
    # Lista de frases de inicio
    frases = [
        "De acuerdo con los resultados obtenidos se observa que",
        "Con los datos obtenidos se identifica que",
        "Resulta positivo observar que la mayoría de la población"
    ]
    inicio = random.choice(frases)
    
    # Regla: Sin porcentajes, usando descriptores cualitativos
    descriptor = "casi la totalidad" if prop_top >= 0.90 else "las tres cuartas partes" if prop_top >= 0.75 else "la mayoría" if prop_top >= 0.50 else "un poco más de la mitad"
    
    redaccion = f"• {inicio} {descriptor} del personal reporta '{categoria_top}'. "
    redaccion += f"Este hallazgo es fundamental para comprender la variable {col} en el contexto de nuestra investigación. "
    redaccion += "Es importante señalar que la distribución observada nos permite identificar las áreas prioritarias para la mejora institucional, "
    redaccion += "confirmando que la percepción del personal es un factor clave en la dinámica de bioseguridad del hospital."
    return redaccion

# --- INTERFAZ ---
st.title("🩺 Motor de Tesis: Análisis Estadístico")
uploaded_file = st.file_uploader("Carga tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Fecha' in df.columns: df = df.drop(columns=['Fecha'])
    
    st.subheader("4.1 PRESENTACIÓN DE LA INFORMACIÓN")
    for col in df.columns:
        st.write(f"### Análisis de la variable: {col}")
        
        # 1. Tabla Estadística (Aquí sí van los números y porcentajes)
        st.table(get_stats_summary(df, col))
        
        # 2. Gráfica
        is_multi = df[col].astype(str).str.contains(',').any()
        fig, ax = plt.subplots(figsize=(6, 3))
        
        if is_multi:
            data_plot = (df[col].str.split(', ', expand=True).stack().value_counts(normalize=True) * 100).reset_index()
            sns.barplot(data=data_plot, x='proportion', y='index', palette="viridis", ax=ax)
        else:
            sns.countplot(data=df, x=col, palette="viridis", ax=ax)
            plt.xticks(rotation=45)
            
        ax.set_ylabel("Frecuencia")
        st.pyplot(fig)
        
        # 3. Análisis Cualitativo (Sin porcentajes, con viñetas)
        st.markdown(generar_redaccion_tesis(df, col, is_multi))
        st.write("---")
