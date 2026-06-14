import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

# Configuración de estilo en español
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'

def obtener_reporte_profesional(df, var):
    freqs = df[var].value_counts(normalize=True)
    count = df[var].value_counts()
    
    # Análisis clínico-estadístico
    categoria_top = freqs.idxmax()
    prop_top = freqs.max() * 100
    
    texto = f"**Análisis de {var}:**\n\n"
    texto += f"El {prop_top:.1f}% de la muestra ({count[categoria_top]} sujetos) reporta '{categoria_top}'. "
    texto += "Este hallazgo evidencia una tendencia conductual que impacta directamente en la barrera de seguridad biológica. "
    texto += "Desde una perspectiva epidemiológica, esta prevalencia sugiere que las estrategias actuales de capacitación están logrando una penetración efectiva, "
    texto += "aunque se debe considerar el impacto de aquellos que se encuentran en los extremos de la distribución para evitar brechas en la seguridad del paciente."
    return texto

def generar_grafica_espanol(df, var, var_y=None):
    fig, ax = plt.subplots(figsize=(8, 5))
    if var_y is None:
        sns.countplot(data=df, x=var, palette="viridis", ax=ax)
        ax.set_title(f"Distribución de {var}", fontsize=14)
        ax.set_xlabel("Categorías", fontsize=12)
        ax.set_ylabel("Frecuencia (n)", fontsize=12)
    else:
        pd.crosstab(df[var], df[var_y]).plot(kind='bar', stacked=True, ax=ax)
        ax.set_title(f"Relación: {var} vs {var_y}", fontsize=14)
        ax.set_xlabel("Nivel de Conocimiento", fontsize=12)
        ax.set_ylabel("Frecuencia", fontsize=12)
        ax.legend(title="Cumplimiento", labels=["Nunca", "A veces", "Frecuentemente", "Siempre"])
    return fig

# --- INTERFAZ ---
st.title("🩺 EpidemioManager: Análisis Clínico Profesional")
uploaded_file = st.file_uploader("Carga tu CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    opcion = st.sidebar.radio("Sección:", ["Análisis Descriptivo", "Prueba de Hipótesis"])
    
    if opcion == "Análisis Descriptivo":
        var = st.selectbox("Variable:", df.columns)
        if st.button("Generar Reporte Profesional"):
            st.pyplot(generar_grafica_espanol(df, var))
            st.markdown(obtener_reporte_profesional(df, var))
            
    elif opcion == "Prueba de Hipótesis":
        st.subheader("Validación de Hipótesis: NOM-010 vs. Aplicación")
        v1, v2 = "Conocimiento_NOM", "Frecuencia_EPP"
        if st.button("Ejecutar Prueba Chi-Cuadrado"):
            st.pyplot(generar_grafica_espanol(df, v1, v2))
            
            # Cálculo Estadístico
            tabla = pd.crosstab(df[v1], df[v2])
            chi2, p, dof, _ = chi2_contingency(tabla)
            
            st.write(f"### Resultados Estadísticos")
            st.metric("Valor de Chi-Cuadrado (χ²)", f"{chi2:.3f}")
            st.metric("Grados de Libertad (gl)", dof)
            st.metric("Valor p", f"{p:.4f}")
            
            # Interpretación Clínica
            if p < 0.05:
                st.success("Interpretación: Se rechaza la Hipótesis Nula (p < 0.05). Existe evidencia estadísticamente significativa de que el nivel de conocimiento sobre la NOM-010-SSA-2023 condiciona la aplicación técnica de los protocolos.")
            else:
                st.warning("Interpretación: No hay significancia estadística (p > 0.05). La aplicación de bioseguridad parece ser independiente del conocimiento teórico, sugiriendo la influencia de factores externos como la infraestructura o la carga asistencial.")
