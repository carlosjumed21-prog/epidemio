import streamlit as st
import pandas as pd
import io

# --- 1. CONFIGURACIÓN Y MAPEO DE MESES ---
MESES_MAP = {
    'ene': 'enero', 'feb': 'febrero', 'mar': 'marzo', 'abr': 'abril',
    'may': 'mayo', 'jun': 'junio', 'jul': 'julio', 'ago': 'agosto',
    'sep': 'septiembre', 'oct': 'octubre', 'nov': 'noviembre', 'dic': 'diciembre'
}

def color_negativo_rojo(val):
    """Aplica color rojo si el valor es negativo (error de captura en fechas)"""
    color = 'red' if isinstance(val, (int, float)) and val < 0 else 'black'
    return f'color: {color}'

st.title("📊 Estadísticas IAAS - CMN 20 de Noviembre")
st.markdown("""
Este módulo procesa los tiempos de respuesta epidemiológica utilizando la fórmula: 
$$Diferencia = (Fecha_{A} - Fecha_{B}) + 1$$
""")

# --- 2. CARGA DE ARCHIVO ---
archivo_iaas = st.file_uploader("Subir base de datos IAAS (Excel .xlsx)", type=["xlsx"])

if archivo_iaas:
    # Leemos el archivo original
    df_original = pd.read_excel(archivo_iaas)
    
    # Botón principal para ejecutar los cálculos
    if st.button("🚀 Generar estadísticas"):
        try:
            df = df_original.copy()
            
            # Convertir a datetime las columnas involucradas (Mapeo por posición)
            # A=0, B=1, D=3, E=4, G=6
            indices_fechas = [0, 1, 3, 4, 6]
            for idx in indices_fechas:
                df.iloc[:, idx] = pd.to_datetime(df.iloc[:, idx], errors='coerce')

            # Realizar cálculos solicitados (Fila posterior - Fila anterior + 1)
            # Col I (8) = A - B + 1
            df["Tiempo promedio de detección en días"] = (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1
            
            # Col J (9) = B - D + 1
            df["Tiempo promedio de toma de cultivo en días"] = (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1
            
            # Col K (10) = D - E + 1
            df["Tiempo promedio de entrega en días"] = (df.iloc[:, 3] - df.iloc[:, 4]).dt.days + 1
            
            # Col L (11) = E - G + 1
            df["Tiempo promedio de captura en días"] = (df.iloc[:, 4] - df.iloc[:, 6]).dt.days + 1

            # Procesar Meses (Columna H = index 7)
            def normalizar_mes(valor):
                v = str(valor).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            
            df['Mes_Filtro'] = df.iloc[:, 7].apply(normalizar_mes)
            
            # Guardar en el estado de la sesión para que no se pierda al interactuar
            st.session_state['df_procesado'] = df
            st.success("✅ Cálculos realizados con éxito.")

        except Exception as e:
            st.error(f"Error al procesar columnas: {e}. Verifica que las columnas A, B, D, E y G sean fechas válidas.")

    # --- 3. INTERFAZ DE RESULTADOS (Si ya se procesaron los datos) ---
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        
        st.divider()

        # Botón de Descarga
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_p.to_excel(writer, index=False, sheet_name='Estadisticas')
        
        st.download_button(
            label="📥 Descargar Reporte con Cálculos (.xlsx)",
            data=output.getvalue(),
            file_name="Estadisticas_IAAS_Procesadas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Vista Previa con corrección de .map()
        with st.expander("👀 Vista previa de datos (Negativos en rojo)"):
            columnas_iaas = [
                "Tiempo promedio de detección en días", 
                "Tiempo promedio de toma de cultivo en días", 
                "Tiempo promedio de entrega en días", 
                "Tiempo promedio de captura en días"
            ]
            # USAMOS .map() EN LUGAR DE .applymap() PARA PANDAS MODERNO
            st.dataframe(df_p.style.map(color_negativo_rojo, subset=columnas_iaas), use_container_width=True)

        # --- 4. FILTROS DINÁMICOS ---
        st.subheader("🔍 Filtros de Visualización")
        c1, c2 = st.columns(2)
        
        with c1:
            # Columna F (index 5) son los sujetos
            lista_sujetos = sorted(df_p.iloc[:, 5].unique())
            sujeto_sel = st.selectbox("Seleccionar Persona / Sujeto", lista_sujetos)
            
        with c2:
            opciones_mes = ["Anual"] + list(MESES_MAP.values())
            mes_sel = st.selectbox("Seleccionar Mes", opciones_mes)

        # Aplicar filtros
        mask = (df_p.iloc[:, 5] == sujeto_sel)
        if mes_sel != "Anual":
            mask = mask & (df_p['Mes_Filtro'] == mes_sel)
        
        df_filtrado = df_p[mask]

        # --- 5. BOTONES DE MÉTRICAS ---
        st.divider()
        st.subheader(f"📊 Resultados: Sujeto {sujeto_sel} | Periodo: {mes_sel}")
        
        met1, met2, met3, met4 = st.columns(4)
        
        def calcular_y_mostrar(col_name, container):
            if not df_filtrado.empty:
                promedio = df_filtrado[col_name].mean()
                container.metric(label="Promedio (Días)", value=f"{promedio:.2f}")
            else:
                container.warning("No hay datos")

        if met1.button("Promedio de detección"):
            calcular_y_mostrar("Tiempo promedio de detección en días", met1)

        if met2.button("Promedio de cultivo"):
            calcular_y_mostrar("Tiempo promedio de toma de cultivo en días", met2)

        if met3.button("Promedio de entrega"):
            calcular_y_mostrar("Tiempo promedio de entrega en días", met3)

        if met4.button("Promedio de captura"):
            calcular_y_mostrar("Tiempo promedio de captura en días", met4)

else:
    st.info("👋 Por favor, carga el archivo de Excel para habilitar el análisis.")
