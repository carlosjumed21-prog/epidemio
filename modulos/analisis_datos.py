import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from scipy.stats import chi2_contingency

# --- CONFIGURACIÓN DE REDACCIÓN ---
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
            analisis += "Esta variabilidad sugiere que el cumplimiento operativo no es uniforme. "
        else:
            analisis += "Al contrastar con las otras categorías, se identifica una tendencia consolidada en la muestra. "
            
    if any(x in col_lower for x in ['sexo', 'edad', 'anios']):
        analisis += "Este hallazgo refleja la estructura demográfica actual del personal."
    else:
        analisis += "Este comportamiento denota la dinámica asistencial vigente, permitiendo visualizar áreas donde la estandarización operativa debe ser fortalecida."
    return analisis

# --- INTERFAZ ---
st.set_page_config(layout="wide")
st.title("🩺 Motor de Tesis: Análisis Clínico")

uploaded_file = st.file_uploader("Carga tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Fecha' in df.columns: df = df.drop(columns=['Fecha'])
    
    # 4.1 y 4.2 PRESENTACIÓN Y ANÁLISIS
    st.subheader("4.1 PRESENTACIÓN DE LA INFORMACIÓN")
    st.dataframe(df.describe(include='all').transpose())
    st.divider()
    
    st.subheader("4.2 ANÁLISIS DE LOS RESULTADOS")
    for col in df.columns:
        st.write(f"### Variable: {col}")
        
        # Procesamiento
        if col == 'Anios_Servicio':
            bins = [0, 5, 10, 15, 20, 25, 30, 100]
            labels = ['1-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31+']
            df['Anios_Grupo'] = pd.cut(df[col], bins=bins, labels=labels)
            counts = df['Anios_Grupo'].value_counts(sort=False)
        elif df[col].astype(str).str.contains(',').any():
            counts = df[col].str.split(', ', expand=True).stack().value_counts()
        else:
            counts = df[col].value_counts()
        
        percents = (counts / len(df) * 100).round(1)
        plot_df = pd.DataFrame({'Categoría': counts.index.astype(str), 'Porcentaje': percents.values})
        
        st.table(pd.DataFrame({'Frecuencia (n)': counts, 'Porcentaje (%)': percents}))
        
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=plot_df, x='Categoría', y='Porcentaje', palette="viridis", ax=ax)
        for container in ax.containers: ax.bar_label(container, fmt='%.1f%%', padding=3)
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig)
        st.markdown(generar_analisis_clinico(plot_df, col))
        st.write("---")

    # 4.3 DISCUSIÓN Y CORRELACIÓN (BARRAS APILADAS AL 100%)
    st.subheader("4.3 DISCUSIÓN: ANÁLISIS DE CORRELACIÓN")
    cols_corr = [c for c in df.columns if c not in ['Anios_Grupo', 'Fecha', 'Anios_Servicio']]
    v_indep = st.selectbox("Variable Teórica (Independiente):", cols_corr, index=9) # Índice de Conocimiento_NOM
    v_dep = st.selectbox("Variable de Práctica (Dependiente):", cols_corr, index=1) # Índice de Frecuencia_EPP
    
    if st.button("Ejecutar Estadística (Chi-cuadrada + Gráfico Apilado)"):
        # Tabla de contingencia
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        chi2, p, dof, expected = chi2_contingency(tabla)
        
        st.write(f"### Valor p: {p:.4f}")
        
        # Barras Apiladas Normalizadas al 100%
        tabla_norm = pd.crosstab(df[v_indep], df[v_dep], normalize='index') * 100
        ax = tabla_norm.plot(kind='bar', stacked=True, figsize=(8, 5), colormap='viridis')
        plt.ylabel("Proporción (%)")
        plt.legend(title=v_dep, bbox_to_anchor=(1.05, 1), loc='upper left')
        st.pyplot(ax.figure)
        
        if p < 0.05:
            st.success("**Discusión:** Existe relación estadística significativa (p < 0.05). Esto valida la hipótesis de investigación: el conocimiento es un predictor fundamental del cumplimiento técnico.")
        else:
            st.warning("**Discusión:** No existe relación estadística significativa (p > 0.05). Esto sugiere que la aplicación técnica es independiente del nivel de conocimiento, indicando la presencia de barreras estructurales en el hospital.")
