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
    "Resulta positivo observar que la mayoría de la población"
]

def get_descriptor(prop):
    if prop >= 0.90: return "casi la totalidad"
    elif prop >= 0.75: return "las tres cuartas partes"
    elif prop >= 0.50: return "la mayoría"
    elif prop > 0.25: return "un poco más de la mitad"
    else: return "una mínima parte"

def generar_redaccion_tesis(plot_data, col):
    # Ordenar datos para obtener el top y el segundo lugar
    datos = plot_data.sort_values('Porcentaje', ascending=False)
    top_cat = datos.iloc[0]['Categoría']
    top_prop = datos.iloc[0]['Porcentaje'] / 100
    inicio = random.choice(frases_inicio)
    
    # Análisis comparativo (Contraste crítico)
    redaccion = f"• {inicio} {get_descriptor(top_prop)} del personal reporta '{top_cat}'. "
    
    if len(datos) > 1:
        segunda_cat = datos.iloc[1]['Categoría']
        segunda_prop = datos.iloc[1]['Porcentaje']
        
        if segunda_prop > 15: # Solo comentar si la segunda categoría es relevante
            redaccion += f"Al contrastar este hallazgo, se identifica que un segmento significativo ({segunda_prop}%) opta por '{segunda_cat}', lo cual sugiere una variabilidad en los procesos de atención. "
            redaccion += "Esta heterogeneidad en la práctica clínica evidencia la necesidad de fortalecer la supervisión y la estandarización operativa para mitigar riesgos en la seguridad del paciente. "
            redaccion += "La persistencia de estas discrepancias técnicas subraya la importancia de reevaluar los protocolos actuales para garantizar una praxis asistencial uniforme y efectiva."
        else:
            redaccion += f"Al analizar la distribución de la variable {col}, se identifica una tendencia consolidada en la muestra. "
            redaccion += "Este comportamiento demuestra un nivel de uniformidad que, si bien es favorable para la estandarización, debe ser contrastado continuamente con la normativa para asegurar la efectividad técnica. "
            redaccion += "Es importante señalar que la distribución observada facilita la identificación de áreas donde la institución ha logrado una madurez operativa, permitiendo enfocar los recursos de mejora de manera precisa."
    
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
        
        # Lógica de cálculo (Binning para Anios_Servicio)
        if col == 'Anios_Servicio':
            bins = [0, 5, 10, 15, 20, 25, 30, 100]
            labels = ['1-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31+']
            df['Anios_Grupo'] = pd.cut(df[col], bins=bins, labels=labels)
            plot_df = (df['Anios_Grupo'].value_counts(normalize=True, sort=False) * 100).reset_index()
            plot_df.columns = ['Categoría', 'Porcentaje']
        elif is_multi:
            frecuencias = df[col].str.split(', ', expand=True).stack().value_counts()
            plot_df = pd.DataFrame({'Categoría': frecuencias.index, 'Porcentaje': (frecuencias / len(df) * 100).round(1)})
        else:
            porcentajes = (df[col].value_counts(normalize=True) * 100).reset_index()
            porcentajes.columns = ['Categoría', 'Porcentaje']
            plot_df = porcentajes
        
        # Gráfica Profesional
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=plot_df, x='Categoría', y='Porcentaje', palette="viridis", ax=ax)
        
        # Etiquetas en TODAS las barras
        ax.bar_label(ax.containers[0], fmt='%.1f%%', padding=3)
        ax.set_ylabel("Frecuencia (%)")
        ax.set_xlabel("")
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig)
        
        # Redacción Analítica
        st.markdown(generar_redaccion_tesis(plot_df, col))
        st.write("---")

    # 4.3 DISCUSIÓN
    st.subheader("4.3 DISCUSIÓN DE LOS RESULTADOS")
    v_indep, v_dep = "Conocimiento_NOM", "Frecuencia_EPP"
    if v_indep in df.columns and v_dep in df.columns:
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        _, p, _, _ = chi2_contingency(tabla)
        
        if p < 0.05:
            st.write("**Discusión:** Existe una relación estadísticamente significativa (p < 0.05). Esto valida que el conocimiento normativo es un factor predictivo del cumplimiento técnico, reforzando la importancia de la educación continua como pilar de la calidad asistencial.")
        else:
            st.write("**Discusión:** La aplicación técnica es independiente del nivel de conocimiento (p > 0.05), sugiriendo la presencia de barreras estructurales o una insuficiente integración de la teoría en la praxis asistencial cotidiana, lo que requiere medidas de gestión correctivas.")
