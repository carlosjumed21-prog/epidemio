import streamlit as st
import pandas as pd
import io

# --- 1. MAPEO DE MESES ---
MESES_MAP = {
    'ene': 'enero', 'feb': 'febrero', 'mar': 'marzo', 'abr': 'abril',
    'may': 'mayo', 'jun': 'junio', 'jul': 'julio', 'ago': 'agosto',
    'sep': 'septiembre', 'oct': 'octubre', 'nov': 'noviembre', 'dic': 'diciembre'
}

def color_negativo_rojo(val):
    """Estilo para la vista previa en la web"""
    color = 'red' if isinstance(val, (int, float)) and val < 0 else 'black'
    return f'color: {color}'

st.title("📊 Estadísticas IAAS - Reporte Final")
st.info("Cálculos en I-L | Mes en M | Formato dd/mm/aaaa")

archivo_iaas = st.file_uploader("Subir base de datos IAAS", type=["xlsx"])

if archivo_iaas:
    df_original = pd.read_excel(archivo_iaas)
    
    if st.button("🚀 Generar estadísticas"):
        try:
            # Mantener solo columnas A hasta H (índices 0 a 7)
            df = df_original.iloc[:, :8].copy()
            
            # Convertir a datetime (dd/mm/aaaa) para cálculos
            idx_f = [0, 1, 3, 4, 6]
            for i in idx_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], format='%d/%m/%Y', errors='coerce')

            # --- CÁLCULOS SEGÚN COMANDOS ---
            # I (8) = A - B + 1 | J (9) = B - D + 1 | K (10) = E - A + 1 | L (11) = G - E + 1
            val_i = (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1
            val_j = (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1
            val_k = (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1
            val_l = (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1

            # Insertar resultados en I, J, K, L
            df.insert(8, "Tiempo promedio de detección en días", val_i)
            df.insert(9, "Tiempo promedio de toma de cultivo en días", val_j)
            df.insert(10, "Tiempo promedio de entrega en días", val_k)
            df.insert(11, "Tiempo promedio de captura en días", val_l)

            # --- NUEVA COLUMNA M (Índice 12) ---
            # Detecta el mes de la Columna H (index 7) y pone el nombre completo
            def obtener_nombre_mes(valor):
                v = str(valor).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            
            df.insert(12, "Mes", df.iloc[:, 7].apply(obtener_nombre_mes))
            
            st.session_state['df_procesado'] = df
            st.success("✅ Estadísticas generadas. Columna M añadida.")

        except Exception as e:
            st.error(f"Error en procesamiento: {e}")

    # --- EXPORTACIÓN Y VISTA ---
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']

        # Generar Excel con Formato Condicional
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            # Exportamos de la A a la M (0 al 12)
            df_export = df_p.iloc[:, :13]
            df_export.to_excel(writer, index=False, sheet_name='Reporte_IAAS')
            
            workbook  = writer.book
            worksheet = writer.sheets['Reporte_IAAS']
            format_rojo = workbook.add_format({'font_color': 'red'})
            
            # Aplicar rojo a I, J, K, L (8 a 11) si son menores a 0
            worksheet.conditional_format(1, 8, 2000, 11, {
                'type':     'cell',
                'criteria': '<',
                'value':    0,
                'format':   format_rojo
            })
            
            worksheet.set_column(0, 7, 15)   # Originales
            worksheet.set_column(8, 11, 25)  # Cálculos
            worksheet.set_column(12, 12, 15) # Columna M (Mes)

        st.download_button(
            label="📥 Descargar Excel con Tiempos y Mes (A-M)",
            data=output.getvalue(),
            file_name="Reporte_Estadisticas_IAAS.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        with st.expander("👀 Vista previa (Columnas I a M)"):
            # Mostramos desde la I en adelante para validar
            st.dataframe(df_p.style.map(color_negativo_rojo, subset=df_p.columns[8:12]))

        # --- FILTROS DE BOTONES ---
        st.subheader("🔍 Filtros de Análisis")
        c1, c2 = st.columns(2)
        with c1:
            sujeto = st.selectbox("Persona (Col F)", sorted(df_p.iloc[:, 5].unique()))
        with c2:
            # Usamos los valores de la nueva Columna M para el filtro
            opciones_mes = ["Anual"] + list(MESES_MAP.values())
            mes_sel = st.selectbox("Periodo", opciones_mes)

        # Filtrar por Sujeto y por la nueva Columna M
        mask = (df_p.iloc[:, 5] == sujeto)
        if mes_sel != "Anual":
            mask = mask & (df_p['Mes'] == mes_sel)
        
        df_f = df_p[mask]

        # --- BOTONES DE MÉTRICAS ---
        st.divider()
        st.write(f"### Promedios: {sujeto} ({mes_sel})")
        col1, col2, col3, col4 = st.columns(4)

        def metric_btn(container, label, col_idx):
            col_name = df_p.columns[col_idx]
            if container.button(label):
                if not df_f.empty:
                    val = df_f[col_name].mean()
                    container.metric("Días", f"{val:.2f}")
                else:
                    container.warning("N/A")

        metric_btn(col1, "Detección", 8)
        metric_btn(col2, "Cultivo", 9)
        metric_btn(col3, "Entrega", 10)
        metric_btn(col4, "Captura", 11)
