import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from scipy.stats import chi2_contingency

# --- LÓGICA DE ANÁLISIS ESPECÍFICO ---
def generar_analisis_clinico(df, col, is_multi):
    # Calcular datos principales
    if is_multi:
        freqs = df[col].str.split(', ', expand=True).stack().value_counts(normalize=True)
    else:
        freqs = df[col].value_counts(normalize=True)
    
    cat_top = freqs.idxmax()
    
    # Base de conocimientos por variable (Lo que le da lógica y coherencia)
    analisis = {
        'Sexo': f"La distribución de la muestra con predominio de '{cat_top}' refleja la composición demográfica habitual en el área de enfermería. Este dato es estructural y establece la base sobre la cual se analizan el resto de las variables de desempeño.",
        'Edad': f"La concentración del personal en el grupo '{cat_top}' indica una fuerza laboral con madurez profesional. Esta distribución sugiere que la mayor parte del equipo cuenta con experiencia acumulada, lo cual es un factor determinante para la adherencia a procesos complejos.",
        'Grado_Academico': f"La prevalencia del nivel '{cat_top}' en la formación académica del personal representa el estándar de competencia teórica actual. Este nivel de preparación debe traducirse directamente en la toma de decisiones clínicas y en la aplicación de los protocolos de seguridad.",
        'Turno': f"La distribución del personal en el turno '{cat_top}' impacta directamente en la carga asistencial. Es vital considerar si las variaciones en los procesos de atención identificadas coinciden con los momentos de mayor saturación operativa en este horario.",
        'Anios_Servicio': f"La presencia de personal con '{cat_top}' años de servicio sugiere una curva de aprendizaje consolidada. Este segmento de la población es clave para el mantenimiento de la cultura de seguridad, actuando como referencia para el personal de reciente ingreso.",
        'Frecuencia_EPP': f"El reporte predominante de '{cat_top}' en el uso de EPP indica una cultura de autocuidado establecida. Sin embargo, la brecha hacia el cumplimiento absoluto señala que aún existen situaciones donde el personal prioriza la agilidad sobre la barrera de protección física.",
        'Conocimiento_NOM': f"Identificar un nivel '{cat_top}' de conocimiento sobre la normativa vigente es un hallazgo crítico. Esto demuestra que la base teórica es sólida, pero plantea la duda de por qué este conocimiento no siempre se refleja en una aplicación técnica perfecta en la práctica asistencial.",
        'Capacitacion_VIH': f"El hecho de que la mayoría reporte '{cat_top}' en capacitación reciente es un indicador de la vigilancia institucional. La continuidad de este indicador es el motor necesario para evitar la obsolescencia técnica en el manejo de riesgos por VIH.",
        'Barreras_Proteccion': f"La elección de '{cat_top}' como barrera principal destaca la percepción de riesgo del personal. La variabilidad observada en el resto de las barreras sugiere que el personal adapta su protección según el procedimiento, lo que requiere supervisión para evitar omisiones por exceso de confianza."
    }

    # Retorno: Análisis específico si existe en el diccionario, o genérico profesional
    if col in analisis:
        return f"• {analisis[col]}"
    else:
        return f"• Los resultados muestran una tendencia hacia '{cat_top}'. Este comportamiento requiere un análisis detallado sobre cómo la variabilidad observada impacta directamente en la seguridad del paciente y en la eficacia de los procesos hospitalarios, siendo necesario evaluar si existen barreras estructurales que impiden un desempeño estandarizado."

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
        
        # Calcular proporciones
        if is_multi:
            porcentajes = (df[col].str.split(', ', expand=True).stack().value_counts(normalize=True) * 100).reset_index()
            porcentajes.columns = ['Categoría', 'Porcentaje']
        else:
            porcentajes = (df[col].value_counts(normalize=True) * 100).reset_index()
            porcentajes.columns = ['Categoría', 'Porcentaje']
        
        # Gráfica
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=porcentajes, x='Porcentaje', y='Categoría', palette="viridis", ax=ax)
        ax.bar_label(ax.containers[0], fmt='%.1f%%', padding=3)
        ax.set_ylabel("")
        ax.set_xlabel("Frecuencia (%)")
        st.pyplot(fig)
        
        # Redacción inteligente y crítica
        st.markdown(generar_analisis_clinico(df, col, is_multi))
        st.write("---")

    # 4.3 DISCUSIÓN
    st.subheader("4.3 DISCUSIÓN DE LOS RESULTADOS")
    v_indep, v_dep = "Conocimiento_NOM", "Frecuencia_EPP"
    if v_indep in df.columns and v_dep in df.columns:
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        _, p, _, _ = chi2_contingency(tabla)
        
        if p < 0.05:
            st.write("**Discusión:** Existe una relación estadísticamente significativa (p < 0.05). Esto valida que el conocimiento normativo (NOM-010-SSA-2023) es un factor predictivo del cumplimiento técnico. Se recomienda estandarizar la supervisión.")
        else:
            st.write("**Discusión:** La aplicación técnica es independiente del nivel de conocimiento (p > 0.05), lo cual sugiere la existencia de barreras estructurales o una insuficiente integración de la teoría en la praxis asistencial cotidiana, lo que requiere medidas correctivas de gestión.")
