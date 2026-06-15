import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
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

uploaded_file = st.file_uploader("Carga tu archivo CSV (Resultados_Tesis_VIH_2026 OFICIAL.csv)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Fecha' in df.columns: df = df.drop(columns=['Fecha'])
    
    # 4.1 y 4.2 PRESENTACIÓN Y ANÁLISIS
    if st.button("🚀 Generar Informe Estadístico y Análisis"):
        st.session_state.show_report = True

    if st.session_state.get('show_report', False):
        st.subheader("4.1 PRESENTACIÓN DE LA INFORMACIÓN")
        st.dataframe(df.describe(include='all').transpose())
        st.divider()
        
        st.subheader("4.2 ANÁLISIS DE LOS RESULTADOS")
        for col in df.columns:
            st.write(f"### Variable: {col}")
            
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

        # 4.3 DISCUSIÓN Y CORRELACIÓN
        st.subheader("4.3 DISCUSIÓN: ANÁLISIS DE CORRELACIÓN")
        
        # Filtrar solo columnas categóricas relevantes
        cols_indep = ['Conocimiento_NOM', 'Capacitacion_VIH', 'Grado_Academico', 'Edad', 'Sexo', 'Turno']
        cols_dep = ['Frecuencia_EPP', 'Accion_Lavado', 'Accion_Notificacion', 'Accion_Registro', 'Accion_PPE', 'Lavado_Manos_OMS']
        
        v_indep = st.selectbox("Variable Independiente (Teórica/Control):", cols_indep)
        v_dep = st.selectbox("Variable Dependiente (Práctica):", cols_dep)
        
        if st.button("Ejecutar Estadística (Chi-cuadrada)"):
            tabla_obs = pd.crosstab(df[v_indep], df[v_dep])
            chi2, p, dof, expected = chi2_contingency(tabla_obs)
            tabla_esp = pd.DataFrame(expected, index=tabla_obs.index, columns=tabla_obs.columns).round(2)
            
            # Mostrar Tablas
            col1, col2 = st.columns(2)
            with col1:
                st.write("#### Frecuencias Observadas (O)")
                st.table(tabla_obs)
            with col2:
                st.write("#### Frecuencias Esperadas (E)")
                st.table(tabla_esp)
            
            st.metric("Valor p", f"{p:.4f}")
            
            # Gráfico de barras apiladas
            tabla_norm = pd.crosstab(df[v_indep], df[v_dep], normalize='index') * 100
            ax = tabla_norm.plot(kind='bar', stacked=True, figsize=(8, 5), colormap='viridis')
            plt.ylabel("Proporción (%)")
            plt.legend(title=v_dep, bbox_to_anchor=(1.05, 1), loc='upper left')
            st.pyplot(ax.figure)
            
            # Bloque para copiar
            st.success("### 📋 BLOQUE PARA COPIAR Y PEGAR EN TESIS")
            reporte = f"""
Para evaluar la asociación entre {v_indep} y {v_dep}, se aplicó la prueba de independencia de Chi-cuadrada ($\chi^2$).
Resultados estadísticos:
- Valor de $\chi^2$: {chi2:.4f}
- Grados de libertad (gl): {dof}
- Valor de significancia (p): {p:.4f}

Interpretación: {'Existe una asociación estadísticamente significativa (p < 0.05), lo que valida que el nivel de conocimiento es un predictor fundamental del cumplimiento técnico.' if p < 0.05 else 'No existe asociación estadísticamente significativa (p > 0.05). La aplicación técnica resultó ser independiente del nivel de conocimiento, sugiriendo la presencia de barreras estructurales en el entorno hospitalario.'}
            """
            st.text_area("Copia el texto siguiente:", value=reporte, height=200)
