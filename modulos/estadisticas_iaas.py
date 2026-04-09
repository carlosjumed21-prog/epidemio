import streamlit as st
import pandas as pd
import io

# --- 1. CONFIGURACIÓN DE MESES ---
MESES_MAP = {
    'ene': 'enero', 'feb': 'febrero', 'mar': 'marzo', 'abr': 'abril',
    'may': 'mayo', 'jun': 'junio', 'jul': 'julio', 'ago': 'agosto',
    'sep': 'septiembre', 'oct': 'octubre', 'nov': 'noviembre', 'dic': 'diciembre'
}

def color_negativo_rojo(val):
    """Pinta de rojo los valores negativos en la web"""
    if isinstance(val, (int, float)) and val < 0:
        return 'color: red; font-weight: bold'
    return 'color: black'

st.title("📊 Estadísticas IAAS - CMN 20 de Noviembre")
st.markdown("---")

archivo_iaas = st.file_uploader("📂 1. Sube tu archivo Excel (dd/mm/aaaa)", type=["xlsx"])

if archivo_iaas:
    # Carga inicial del archivo
    if 'df_base' not in st.session_state:
        st.session_state['df_base'] = pd.read_excel(archivo_iaas)

    # BOTÓN DE PROCESAMIENTO
    if st.button("🚀 2. Generar Estadísticas y Columnas I-M"):
        try:
            # Trabajamos sobre una copia de las primeras 8 columnas (A-H)
            # Esto ELIMINA cualquier columna basura de la M en adelante
            df = st.session_state['df_base'].iloc[:, :8].copy()
            
            # Convertir fechas (A, B, D, E, G)
            indices_f = [0, 1, 3, 4, 6]
            for i in indices_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], format='%d/%m/%Y', errors='coerce')

            # --- CÁLCULOS EXACTOS ---
            # Col I (8): A - B + 1
            df.insert(8, "Tiempo promedio de detección en días", (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1)
            # Col J (9): B - D + 1
            df.insert(9, "Tiempo promedio de toma de cultivo en días", (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1)
            # Col K (10): E - A + 1
            df.insert(10, "Tiempo promedio de entrega en días", (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1)
            # Col L (11): G - E + 1
            df.insert(11, "Tiempo promedio de captura en días", (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1)

            # --- COLUMNA M (12): NOMBRE DEL MES ---
            def normalizar_mes(valor):
                v = str(valor).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df.insert(12, "Mes_Nombre", df.iloc[:, 7].apply(normalizar_mes))

            # Guardar resultado final en session_state
            st.session_state['df_procesado'] = df
            st.success("✅ ¡Columnas I, J, K, L y M generadas con éxito!")
            
        except Exception as e:
            st.error(f"❌ Error al procesar: {e}. Revisa el formato de fecha en tu Excel.")

    # --- MOSTRAR RESULTADOS SI EXISTEN ---
    if 'df_procesado' in st.session_state:
        df_final = st.session_state['df_procesado']

        # 1. BOTÓN DE DESCARGA
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            # Exportar de la A a la M (0 al 12)
            df_final.iloc[:, :13].to_excel(writer, index=False, sheet_name='Resultados')
            
            workbook = writer.book
            worksheet = writer.sheets['Resultados']
            fmt_rojo = workbook.add_format({'font_color': 'red'})
            
            # Formato condicional en Excel (Columnas I a L / 8 a 11)
            worksheet.conditional_format(1, 8, 2000, 11, {
                'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_rojo
            })
            worksheet.set_column(0, 12, 18)

        st.download_button(
            label="📥 Descargar Excel con Tiempos y Mes (A-M)",
            data=output.getvalue(),
            file_name="Estadisticas_IAAS_Procesadas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 2. VISTA PREVIA CON COLOR
        st.subheader("👀 Vista Previa de Datos Procesados")
        # Aplicamos el color rojo solo a las columnas de cálculo
        columnas_stats = df_final.columns[8:12]
        st.dataframe(df_final.style.map(color_negativo_rojo, subset=columnas_stats), use_container_width=True)

        # 3. FILTROS Y MÉTRICAS
        st.divider()
        st.subheader("🔍 Análisis por Sujeto")
        c1, c2 = st.columns(2)
        with c1:
            sujeto_sel = st.selectbox("Selecciona Sujeto (Col F)", sorted(df_final.iloc[:, 5].unique()))
        with c2:
            mes_sel = st.selectbox("Selecciona Mes", ["Anual"] + list(MESES_MAP.values()))

        # Filtrado
        mask = (df_final.iloc[:, 5] == sujeto_sel)
        if mes_sel != "Anual":
            mask = mask & (df_final['Mes_Nombre'] == mes_sel)
        
        df_filtrado = df_final[mask]

        # Botones de métricas
        m1, m2, m3, m4 = st.columns(4)
        def mostrar_m(cont, label, col_idx):
            if cont.button(label):
                if not df_filtrado.empty:
                    val = df_filtrado.iloc[:, col_idx].mean()
                    cont.metric("Promedio", f"{val:.2f} d")
                else:
                    cont.warning("No hay datos")

        mostrar_m(m1, "Detección", 8)
        mostrar_m(m2, "Cultivo", 9)
        mostrar_m(m3, "Entrega", 10)
        mostrar_m(m4, "Captura", 11)

    else:
        # Si no se ha procesado, mostrar la tabla original para que el usuario sepa que se cargó
        st.warning("⚠️ Los cambios se verán después de hacer clic en 'Generar Estadísticas'.")
        st.write("Vista previa del archivo original:")
        st.dataframe(st.session_state['df_base'].head(10))
