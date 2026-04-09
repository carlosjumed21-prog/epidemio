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
    """Color rojo para valores negativos en la web"""
    if isinstance(val, (int, float)) and val < 0:
        return 'color: red; font-weight: bold'
    return 'color: black'

st.title("📊 Estadísticas IAAS - Reporte Final")
st.markdown("---")

archivo_iaas = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    # --- CARGA Y LIMPIEZA ESTRICTA ---
    if 'df_base' not in st.session_state:
        # Cargamos el archivo completo
        df_raw = pd.read_excel(archivo_iaas)
        
        # DELIMITAR FILAS: Eliminamos filas que estén completamente vacías 
        # en el rango de datos originales (A-H)
        df_limpio = df_raw.dropna(how='all', subset=df_raw.columns[:8]).reset_index(drop=True)
        
        st.session_state['df_base'] = df_limpio

    # BOTÓN DE PROCESAMIENTO
    if st.button("🚀 Generar Estadísticas"):
        try:
            # Trabajamos sobre las 121 filas detectadas (A-H)
            df = st.session_state['df_base'].iloc[:, :8].copy()
            
            # Convertir fechas (A, B, D, E, G)
            idx_f = [0, 1, 3, 4, 6]
            for i in idx_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # --- CÁLCULOS (Columnas I, J, K, L) ---
            # I=8 (A-B+1), J=9 (B-D+1), K=10 (E-A+1), L=11 (G-E+1)
            df.insert(8, "Tiempo promedio de detección en días", (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1)
            df.insert(9, "Tiempo promedio de toma de cultivo en días", (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1)
            df.insert(10, "Tiempo promedio de entrega en días", (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1)
            df.insert(11, "Tiempo promedio de captura en días", (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1)

            # Mes invisible para los filtros de la app
            def get_mes(v):
                v = str(v).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df['Mes_Invisible'] = df.iloc[:, 7].apply(get_mes)

            st.session_state['df_procesado'] = df
            st.success(f"✅ Se han procesado exactamente {len(df)} filas.")
            
        except Exception as e:
            st.error(f"❌ Error técnico: {e}")

    # --- RESULTADOS Y DESCARGA ---
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']

        # 1. GENERAR EXCEL COMO "TABLA"
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            # Exportamos solo de A a L (12 columnas)
            df_export = df_p.iloc[:, :12]
            df_export.to_excel(writer, index=False, sheet_name='Reporte_IAAS')
            
            workbook  = writer.book
            worksheet = writer.sheets['Reporte_IAAS']
            
            # Convertir el rango de celdas en una Tabla de Excel oficial
            (max_row, max_col) = df_export.shape
            worksheet.add_table(0, 0, max_row, max_col - 1, {
                'columns': [{'header': c} for c in df_export.columns],
                'style': 'Table Style Medium 9'
            })
            
            # Formato rojo para negativos
            fmt_rojo = workbook.add_format({'font_color': 'red', 'bold': True})
            worksheet.conditional_format(1, 8, max_row, 11, {
                'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_rojo
            })
            
            worksheet.set_column(0, 11, 20)

        st.download_button(
            label="📥 Descargar Tabla de Excel (121 filas)",
            data=output.getvalue(),
            file_name="Reporte_IAAS_Final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 2. VISTA PREVIA DELIMITADA (Solo 121 filas, sin horas)
        st.subheader(f"👀 Vista Previa del Reporte ({len(df_p)} registros)")
        
        # Limpieza visual para Streamlit
        df_visual = df_p.iloc[:, :12].copy()
        idx_fechas = [0, 1, 3, 4, 6]
        for i in idx_fechas:
            col_name = df_visual.columns[i]
            # Convertimos a texto dd/mm/aaaa para quitar la hora 00:00:00
            df_visual[col_name] = df_visual[col_name].dt.strftime('%d/%m/%Y').fillna("-")

        st.dataframe(
            df_visual.style.map(color_negativo_rojo, subset=df_visual.columns[8:12]), 
            use_container_width=True
        )

        # 3. FILTROS Y MÉTRICAS
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            sujetos = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            s_sel = st.selectbox("Sujeto (Col F)", sujetos)
        with c2:
            m_sel = st.selectbox("Periodo", ["Anual"] + list(MESES_MAP.values()))

        # Aplicar filtros
        mask = (df_p.iloc[:, 5] == s_sel)
        if m_sel != "Anual":
            mask = mask & (df_p['Mes_Invisible'] == m_sel)
        
        df_f = df_p[mask]

        st.write(f"### Promedios: Sujeto {s_sel} ({m_sel})")
        m1, m2, m3, m4 = st.columns(4)
        
        def render_btn(cont, label, col_idx):
            if cont.button(label):
                if not df_f.empty:
                    val = df_f.iloc[:, col_idx].mean()
                    cont.metric("Días", f"{val:.2f}")
                else: cont.warning("N/A")

        render_btn(m1, "Detección", 8)
        render_btn(m2, "Cultivo", 9)
        render_btn(m3, "Entrega", 10)
        render_btn(m4, "Captura", 11)

else:
    st.warning("👋 Sube tu archivo para limpiar las filas fantasma y generar la tabla.")
