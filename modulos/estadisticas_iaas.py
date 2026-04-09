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
    """Resaltar errores de lógica de fechas"""
    color = 'red' if isinstance(val, (int, float)) and val < 0 else 'black'
    return f'color: {color}'

st.title("📊 Estadísticas IAAS - Precisión de Tiempos")
st.info("Cálculo exacto basado en fechas dd/mm/aaaa (Respetando días calendario)")

archivo_iaas = st.file_uploader("Subir base de datos IAAS", type=["xlsx"])

if archivo_iaas:
    # Leemos el archivo original
    df_original = pd.read_excel(archivo_iaas)
    
    if st.button("🚀 Generar estadísticas"):
        try:
            df = df_original.copy()
            
            # 1. Convertir a datetime respetando el formato día/mes/año
            # Posiciones: A=0, B=1, D=3, E=4, G=6
            indices_fechas = [0, 1, 3, 4, 6]
            for idx in indices_fechas:
                df.iloc[:, idx] = pd.to_datetime(df.iloc[:, idx], format='%d/%m/%Y', errors='coerce')

            # 2. Cálculos e Inserción en Columnas I, J, K, L (Índices 8, 9, 10, 11)
            # Calculamos los valores primero
            val_i = (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1
            val_j = (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1
            val_k = (df.iloc[:, 3] - df.iloc[:, 4]).dt.days + 1
            val_l = (df.iloc[:, 4] - df.iloc[:, 6]).dt.days + 1

            # Insertamos en las posiciones exactas (I=8, J=9, K=10, L=11)
            # Si las columnas ya existen por una corrida previa, las eliminamos para no duplicar
            cols_nuevas = [
                "Tiempo promedio de detección en días",
                "Tiempo promedio de toma de cultivo en días",
                "Tiempo promedio de entrega en días",
                "Tiempo promedio de captura en días"
            ]
            for c in cols_nuevas:
                if c in df.columns: df.drop(columns=[c], inplace=True)

            df.insert(8, cols_nuevas[0], val_i)
            df.insert(9, cols_nuevas[1], val_j)
            df.insert(10, cols_nuevas[2], val_k)
            df.insert(11, cols_nuevas[3], val_l)

            # 3. Procesar Meses para filtros (Columna H = index 7)
            def normalizar_mes(valor):
                v = str(valor).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            
            df['Mes_Filtro'] = df.iloc[:, 7].apply(normalizar_mes)
            
            st.session_state['df_procesado'] = df
            st.success("✅ Datos procesados. Las columnas se han insertado en las posiciones I, J, K y L.")

        except Exception as e:
            st.error(f"Error: {e}. Revisa que las fechas tengan el formato dd/mm/aaaa")

    # --- RESULTADOS Y DESCARGA ---
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        
        # 4. Configurar descarga con formato de fecha para Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_p.to_excel(writer, index=False, sheet_name='Estadisticas')
            # Ajustar ancho de columnas automáticamente para que se vea bien
            worksheet = writer.sheets['Estadisticas']
            for i, col in enumerate(df_p.columns):
                worksheet.set_column(i, i, 20)

        st.download_button(
            label="📥 Descargar Excel Corregido (Columnas I-L)",
            data=output.getvalue(),
            file_name="Estadisticas_IAAS_Final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        with st.expander("👀 Vista Previa (Validar posiciones I, J, K, L)"):
            columnas_stats = [
                "Tiempo promedio de detección en días", 
                "Tiempo promedio de toma de cultivo en días", 
                "Tiempo promedio de entrega en días", 
                "Tiempo promedio de captura en días"
            ]
            st.dataframe(df_p.style.map(color_negativo_rojo, subset=columnas_stats))

        # --- FILTROS ---
        st.subheader("🔍 Generar Reporte por Sujeto")
        c1, c2 = st.columns(2)
        with c1:
            sujeto_sel = st.selectbox("Persona (Columna F)", sorted(df_p.iloc[:, 5].unique()))
        with c2:
            mes_sel = st.selectbox("Mes de Análisis", ["Anual"] + list(MESES_MAP.values()))

        mask = (df_p.iloc[:, 5] == sujeto_sel)
        if mes_sel != "Anual":
            mask = mask & (df_p['Mes_Filtro'] == mes_sel)
        
        df_filtrado = df_p[mask]

        # --- BOTONES DE ESTADÍSTICAS ---
        st.divider()
        st.write(f"### Análisis de Tiempos: Sujeto {sujeto_sel}")
        
        b1, b2, b3, b4 = st.columns(4)
        
        def mostrar(col, container, titulo):
            if not df_filtrado.empty:
                avg = df_filtrado[col].mean()
                container.metric(titulo, f"{avg:.2f} d")
            else:
                container.write("N/A")

        if b1.button("Detección"):
            mostrar("Tiempo promedio de detección en días", b1, "Detección")
        if b2.button("Cultivo"):
            mostrar("Tiempo promedio de toma de cultivo en días", b2, "Cultivo")
        if b3.button("Entrega"):
            mostrar("Tiempo promedio de entrega en días", b3, "Entrega")
        if b4.button("Captura"):
            mostrar("Tiempo promedio de captura en días", b4, "Captura")
