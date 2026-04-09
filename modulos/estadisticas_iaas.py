import streamlit as st
import pandas as pd
import io

# --- MAPEO DE MESES ---
MESES_MAP = {
    'ene': 'enero', 'feb': 'febrero', 'mar': 'marzo', 'abr': 'abril',
    'may': 'mayo', 'jun': 'junio', 'jul': 'julio', 'ago': 'agosto',
    'sep': 'septiembre', 'oct': 'octubre', 'nov': 'noviembre', 'dic': 'diciembre'
}

def color_negativo_rojo(val):
    """Función para dar estilo rojo a números negativos"""
    color = 'red' if isinstance(val, (int, float)) and val < 0 else 'black'
    return f'color: {color}'

st.title("📊 Estadísticas IAAS - Procesamiento Automático")
st.info("Carga tu archivo Excel para generar los indicadores de tiempos promedio.")

archivo_iaas = st.file_uploader("Subir Excel (.xlsx)", type=["xlsx"])

if archivo_iaas:
    # Leer el archivo - Usamos header=0 para que la Fila 1 sean los nombres
    df = pd.read_excel(archivo_iaas)
    
    # --- BOTÓN GENERAR ESTADÍSTICAS ---
    if st.button("🚀 Generar estadísticas"):
        try:
            # 1. Convertir columnas de fecha a datetime (Basado en posiciones)
            # A=0, B=1, D=3, E=4, G=6
            cols_fecha = [0, 1, 3, 4, 6]
            for col in cols_fecha:
                df.iloc[:, col] = pd.to_datetime(df.iloc[:, col], errors='coerce')

            # 2. Cálculos (Fecha_Posterior - Fecha_Anterior + 1)
            # Col I (index 8) = Col A - Col B + 1
            df["Tiempo promedio de detección en días"] = (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1
            
            # Col J (index 9) = Col B - Col D + 1
            df["Tiempo promedio de toma de cultivo en días"] = (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1
            
            # Col K (index 10) = Col D - Col E + 1
            df["Tiempo promedio de entrega en días"] = (df.iloc[:, 3] - df.iloc[:, 4]).dt.days + 1
            
            # Col L (index 11) = Col E - Col G + 1
            df["Tiempo promedio de captura en días"] = (df.iloc[:, 4] - df.iloc[:, 6]).dt.days + 1

            # 3. Procesamiento de Meses (Columna H = index 7)
            # Extrae el mes del formato "ene-26" y lo convierte a "enero"
            def limpiar_mes(valor):
                valor_str = str(valor).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in valor_str:
                        return nombre
                return "Otro"
            
            df['Mes_Filtro'] = df.iloc[:, 7].apply(limpiar_mes)

            # Guardar en session_state para que persista tras los filtros
            st.session_state['df_procesado'] = df
            st.success("✅ Datos procesados con éxito.")

        except Exception as e:
            st.error(f"Error en el mapeo de columnas: {e}. Revisa que las columnas A, B, D, E, G contengan fechas.")

    # --- SECCIÓN DE FILTROS Y VISUALIZACIÓN ---
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']

        st.divider()
        
        # --- OPCIONES DE DESCARGA Y VISTA PREVIA ---
        col_down1, col_down2 = st.columns([1, 1])
        
        # Generar Excel en memoria para descarga
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_p.to_excel(writer, index=False, sheet_name='Reporte_IAAS')
        
        col_down1.download_button(
            label="📥 Descargar Reporte Excel",
            data=output.getvalue(),
            file_name="Reporte_Estadisticas_IAAS.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        with st.expander("👀 Vista previa del archivo (Negativos en rojo)"):
            # Aplicar estilo rojo a las nuevas columnas I, J, K, L
            columnas_stats = [
                "Tiempo promedio de detección en días", 
                "Tiempo promedio de toma de cultivo en días", 
                "Tiempo promedio de entrega en días", 
                "Tiempo promedio de captura en días"
            ]
            st.dataframe(df_p.style.applymap(color_negativo_rojo, subset=columnas_stats), use_container_width=True)

        # --- FILTROS PARA BOTONES ---
        st.subheader("🔍 Filtros de Análisis")
        c1, c2 = st.columns(2)
        
        with c1:
            # Columna F (index 5) son los sujetos 1-12
            lista_sujetos = sorted(df_p.iloc[:, 5].unique())
            sujeto_sel = st.selectbox("Seleccionar Persona", lista_sujetos)
            
        with c2:
            opciones_mes = ["Anual"] + list(MESES_MAP.values())
            mes_sel = st.selectbox("Seleccionar Periodo", opciones_mes)

        # Filtrado de los datos para las métricas
        mask = (df_p.iloc[:, 5] == sujeto_sel)
        if mes_sel != "Anual":
            mask = mask & (df_p['Mes_Filtro'] == mes_sel)
        
        df_filtrado = df_p[mask]

        # --- BOTONES DE ESTADÍSTICAS ---
        st.divider()
        st.write(f"### Resultados para Sujeto {sujeto_sel} ({mes_sel})")
        
        b1, b2, b3, b4 = st.columns(4)
        
        def mostrar_metrica(titulo, columna):
            if not df_filtrado.empty:
                valor = df_filtrado[columna].mean()
                st.metric(label=titulo, value=f"{valor:.2f} días")
            else:
                st.metric(label=titulo, value="Sin datos")

        if b1.button("Promedio de detección"):
            mostrar_metrica("Detección", "Tiempo promedio de detección en días")
            
        if b2.button("Promedio de cultivo"):
            mostrar_metrica("Cultivo", "Tiempo promedio de toma de cultivo en días")
            
        if b3.button("Promedio de entrega"):
            mostrar_metrica("Entrega", "Tiempo promedio de entrega en días")
            
        if b4.button("Promedio de captura"):
            mostrar_metrica("Captura", "Tiempo promedio de captura en días")

        if df_filtrado.empty:
            st.warning("No hay registros que coincidan con el sujeto y mes seleccionado.")
