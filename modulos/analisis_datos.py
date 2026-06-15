import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN DE REDACCIÓN (REGLAS DE ORO) ---
frases_inicio = [
    "De acuerdo con los resultados obtenidos se observa que",
    "Con los datos obtenidos se observa que",
    "Podemos observar que la mayoría",
    "Observando los resultados obtenidos se identifica que",
    "Resulta positivo observar que la mayoría de la población",
    "En la población entrevistada podemos observar que",
    "En relación a las variables observadas nos damos cuenta que"
]

def obtener_expresion(p):
    if p >= 90: return "casi la totalidad"
    elif p >= 75: return "las tres cuartas partes"
    elif p >= 50: return "la mayoría"
    elif p >= 25: return "un poco más de la mitad"
    else: return "una mínima parte"

def generar_analisis_clinico(plot_df, col):
    df_sorted = plot_df.sort_values('Porcentaje', ascending=False)
    top_cat = df_sorted.iloc[0]['Categoría']
    top_p = df_sorted.iloc[0]['Porcentaje']
    
    inicio = random.choice(frases_inicio)
    expresion = obtener_expresion(top_p)
    col_lower = col.lower()
    
    analisis = f"• {inicio} {expresion} de la población seleccionó '{top_cat}'. "
    
    if len(df_sorted) > 1:
        segunda_cat = df_sorted.iloc[1]['Categoría']
        segunda_p = df_sorted.iloc[1]['Porcentaje']
        if segunda_p > 15:
            analisis += f"Al realizar el contraste, se identifica que un segmento significativo también refiere '{segunda_cat}'. "
            analisis += "Esta variabilidad sugiere que el cumplimiento operativo no es uniforme, lo cual representa un riesgo de inconsistencia en la seguridad asistencial. "
        else:
            analisis += "Al contrastar con las otras categorías, se identifica una tendencia consolidada en la muestra. "
            analisis += "Este comportamiento demuestra un nivel de uniformidad que, aunque favorable para la estandarización, requiere supervisión para asegurar la efectividad técnica. "
            
    if any(x in col_lower for x in ['sexo', 'edad', 'anios']):
        analisis += "Este hallazgo refleja la estructura demográfica y operativa actual del hospital, proporcionando una base clara para la comprensión del perfil del personal que labora en la unidad."
    else:
        analisis += "Este comportamiento denota la dinámica asistencial vigente, permitiendo visualizar áreas donde la estandarización operativa debe ser fortalecida para garantizar la calidad en la atención."
    return analisis

# --- INTERFAZ ---
st.title("🩺 Motor de Tesis: Análisis Clínico")
uploaded_file = st.file_uploader("Carga tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Fecha' in df.columns: df = df.drop(columns=['Fecha'])
    
    # MANTENER ESTADO DEL REPORTE
    if 'show_report' not in st.session_state: st.session_state.show_report = False
    
    if st.button("🚀 Generar Informe Estadístico y Análisis"):
        st.session_state.show_report = True

    if st.session_state.show_report:
        st.subheader("4.1 PRESENTACIÓN DE LA INFORMACIÓN")
        st.dataframe(df.describe(include='all').transpose())
        st.divider()
        
        st.subheader("4.2 ANÁLISIS DE LOS RESULTADOS")
        for col in df.columns:
            st.write(f"### Variable: {col}")
            is_multi = df[col].astype(str).str.contains(',').any()
            
            # Procesamiento
            if col == 'Anios_Servicio':
                bins = [0, 5, 10, 15, 20, 25, 30, 100]
                labels = ['1-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31+']
                df['Anios_Grupo'] = pd.cut(df[col], bins=bins, labels=labels)
                counts = df['Anios_Grupo'].value_counts(sort=False)
                percents = (counts / len(df) * 100).round(1)
            elif is_multi:
                counts = df[col].str.split(', ', expand=True).stack().value_counts()
                percents = (counts / len(df) * 100).round(1)
            else:
                counts = df[col].value_counts()
                percents = (counts / len(df) * 100).round(1)
            
            plot_df = pd.DataFrame({'Categoría': counts.index.astype(str), 'Porcentaje': percents.values})
            
            # 1. Tabla de Fundamento
            st.table(pd.DataFrame({'Frecuencia (n)': counts, 'Porcentaje (%)': percents}))
            
            # 2. Gráfica Profesional
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(data=plot_df, x='Categoría', y='Porcentaje', palette="viridis", ax=ax)
            for container in ax.containers:
                ax.bar_label(container, fmt='%.1f%%', padding=3)
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig)
            
            # 3. Análisis
            st.markdown(generar_analisis_clinico(plot_df, col))
            st.write("---")

        # 4.3 DISCUSIÓN Y CORRELACIÓN (CHI-CUADRADA)
        st.subheader("4.3 DISCUSIÓN: ANÁLISIS DE CORRELACIÓN")
        cols = [c for c in df.columns if c not in ['Anios_Grupo', 'Fecha']]
        v_indep = st.selectbox("Seleccione Variable Independiente:", cols, key="v1")
        v_dep = st.selectbox("Seleccione Variable Dependiente:", cols, key="v2")
        
        if st.button("Ejecutar Estadística (Chi-cuadrada)"):
            tabla = pd.crosstab(df[v_indep], df[v_dep])
            chi2, p, dof, expected = chi2_contingency(tabla)
            st.write(f"**Valor p:** {p:.4f}")
            
            fig_corr, ax_corr = plt.subplots(figsize=(6, 4))
            sns.heatmap(tabla, annot=True, fmt='d', cmap='Blues', ax=ax_corr)
            st.pyplot(fig_corr)
            
            if p < 0.05:
                st.write("**Discusión:** Existe una relación estadísticamente significativa (p < 0.05). Esto valida que la variable independiente es un factor predictor de la dependiente.")
            else:
                st.write("**Discusión:** La aplicación técnica es independiente (p > 0.05). Sugiere barreras estructurales o una insuficiente integración de la teoría en la praxis.")
