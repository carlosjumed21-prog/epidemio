import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

# [La función generar_analisis_clinico se mantiene igual que antes...]

st.title("🩺 Motor de Tesis: Análisis Estadístico")
uploaded_file = st.file_uploader("Carga tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Fecha' in df.columns: df = df.drop(columns=['Fecha'])
    
    # Categorizar años para correlación
    bins = [0, 5, 10, 15, 20, 25, 30, 100]
    labels = ['1-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31+']
    df['Anios_Grupo'] = pd.cut(df['Anios_Servicio'], bins=bins, labels=labels)

    # 4.3 DISCUSIÓN Y CORRELACIÓN (CHI-CUADRADA)
    st.subheader("4.3 DISCUSIÓN: ANÁLISIS DE CORRELACIÓN (CHI-CUADRADA)")
    
    # Listas segmentadas
    indep_vars = ['Conocimiento_NOM', 'Capacitacion_VIH', 'Grado_Academico', 'Anios_Grupo', 'Edad', 'Sexo']
    dep_vars = ['Frecuencia_EPP', 'Accion_Lavado', 'Accion_Notificacion', 'Accion_Registro', 'Accion_PPE', 'Lavado_Manos_OMS', 'Proteccion_Identidad']
    
    v_indep = st.selectbox("Seleccione Variable Independiente (Teórica):", indep_vars)
    v_dep = st.selectbox("Seleccione Variable Dependiente (Práctica):", dep_vars)
    
    if st.button("Ejecutar Estadística"):
        # Tabla de contingencia
        tabla = pd.crosstab(df[v_indep], df[v_dep])
        
        # Mostrar Tabla de Observados (La base del cálculo)
        st.write("#### Tabla de Contingencia (Frecuencias Observadas)")
        st.table(tabla)
        
        chi2, p, dof, expected = chi2_contingency(tabla)
        
        # Mostrar Valor P y conclusión
        st.metric("Valor p", f"{p:.4f}")
        
        # Visualización: Barras Apiladas al 100%
        tabla_norm = pd.crosstab(df[v_indep], df[v_dep], normalize='index') * 100
        ax = tabla_norm.plot(kind='bar', stacked=True, figsize=(8, 5), colormap='viridis')
        plt.ylabel("Proporción (%)")
        plt.legend(title=v_dep, bbox_to_anchor=(1.05, 1), loc='upper left')
        st.pyplot(ax.figure)
        
        if p < 0.05:
            st.success(f"**Conclusión Estadística:** Existe una relación estadísticamente significativa (p < 0.05). Esto valida la hipótesis de que {v_indep} influye en {v_dep}.")
        else:
            st.warning(f"**Conclusión Estadística:** No existe relación estadísticamente significativa (p > 0.05). La práctica ({v_dep}) es independiente del nivel de conocimiento ({v_indep}).")
