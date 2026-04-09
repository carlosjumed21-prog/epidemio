import streamlit as st
import pandas as pd
import io
import plotly.express as px

# --- 1. CONFIGURACIÓN DE MESES ---
MESES_MAP = {
    'ene': 'enero', 'feb': 'febrero', 'mar': 'marzo', 'abr': 'abril',
    'may': 'mayo', 'jun': 'junio', 'jul': 'julio', 'ago': 'agosto',
    'sep': 'septiembre', 'oct': 'octubre', 'nov': 'noviembre', 'dic': 'diciembre'
}

def color_negativo_rojo(val):
    if isinstance(val, (int, float)) and val < 0:
        return 'color: red; font-weight: bold'
    return 'color: black'

st.title("📊 Sistema de Vigilancia IAAS - Análisis de Tiempos")
st.markdown("---")

archivo_iaas = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    if 'df_base' not in st.session_state:
        df_raw = pd.read_excel(archivo_iaas)
        df_limpio = df_raw.dropna(how='all', subset=df_raw.columns[:8]).reset_index(drop=True)
        st.session_state['df_base'] = df_limpio

    if st.button("🚀 Procesar y Graficar"):
        try:
            df = st.session_state['df_base'].iloc[:, :8].copy()
            idx_f = [0, 1, 3, 4, 6]
            for i in idx_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # --- CÁLCULOS I, J, K, L ---
            df.insert(8, "Detección", (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1)
            df.insert(9, "Cultivo", (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1)
            df.insert(10, "Entrega", (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1)
            df.insert(11, "Captura", (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1)

            def get_mes(v):
                v = str(v).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df['Mes_Invisible'] = df.iloc[:, 7].apply(get_mes)

            st.session_state['df_procesado'] = df
            st.success("✅ Datos listos para visualización.")
            
        except Exception as e:
            st.error(f"❌ Error: {e}")

    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        cols_tiempos = ["Detección", "Cultivo", "Entrega", "Captura"]

        # --- FILTROS ---
        st.subheader("🔍 Filtros Dinámicos")
        c1, c2 = st.columns(2)
        with c1:
            # Agregamos la opción "Todos" al inicio de la lista de sujetos
            lista_sujetos = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            opciones_sujeto = ["Todos"] + [str(s) for s in lista_sujetos]
            s_sel = st.selectbox("Sujeto (Col F)", opciones_sujeto)
        with c2:
            m_sel = st.selectbox("Periodo", ["Anual"] + list(MESES_MAP.values()))

        # Aplicar Filtros a la máscara
        mask = pd.Series([True] * len(df_p))
        if s_sel != "Todos":
            mask = mask & (df_p.iloc[:, 5].astype(str) == s_sel)
        if m_sel != "Anual":
            mask = mask & (df_p['Mes_Invisible'] == m_sel)
        
        df_f = df_p[mask]

        # --- SECCIÓN DE GRÁFICAS ---
        st.divider()
        st.subheader(f"📈 Visualización del Proceso: {s_sel}")

        if not df_f.empty:
            # Preparar datos para la gráfica (Solo valores >= 0)
            df_plot = df_f.copy()
            for c in cols_tiempos:
                df_plot[c] = df_plot[c].apply(lambda x: x if x >= 0 else 0)

            if s_sel == "Todos":
                # Gráfica comparativa entre sujetos
                # Agrupamos por sujeto (Columna F = index 5)
                comp_df = df_plot.groupby(df_plot.columns[5])[cols_tiempos].mean().reset_index()
                fig = px.bar(comp_df, x=df_plot.columns[5], y=cols_tiempos, 
                             title="Promedio de Días por Sujeto y Etapa",
                             labels={'value': 'Días', 'variable': 'Etapa del Proceso'},
                             barmode='group', color_discrete_sequence=px.colors.qualitative.Pastel)
            else:
                # Gráfica individual (Promedio del sujeto seleccionado)
                ind_df = df_plot[cols_tiempos].mean().reset_index()
                ind_df.columns = ['Etapa', 'Días']
                fig = px.bar(ind_df, x='Etapa', y='Días', 
                             title=f"Distribución de Tiempos - Sujeto {s_sel}",
                             color='Etapa', text_auto='.2f')

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay datos disponibles para los filtros seleccionados.")

        # --- BOTONES DE MÉTRICAS Y ALERTAS ---
        tiene_rojos = (df_f[cols_tiempos] < 0).any().any()
        if tiene_rojos:
            st.warning("⚠️ **Nota:** Los días promedios son aproximados por fechas distantes.")

        st.write("### Indicadores Rápidos (Promedio)")
        m1, m2, m3, m4 = st.columns(4)
        def render_m(cont, label, col_name):
            if cont.button(label):
                if not df_f.empty:
                    val = df_f[col_name][df_f[col_name] >= 0].mean()
                    cont.metric("Promedio", f"{val:.2f} d")
                else: cont.warning("N/A")

        render_m(m1, "Detección", "Detección")
        render_m(m2, "Cultivo", "Cultivo")
        render_m(m3, "Entrega", "Entrega")
        render_m(m4, "Captura", "Captura")

        # --- DESCARGA Y VISTA PREVIA ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p.iloc[:, :12].copy()
            df_export.to_excel(writer, index=False, sheet_name='Reporte')
            workbook, worksheet = writer.book, writer.sheets['Reporte']
            
            # Tabla de Excel con fila de totales
            max_r, max_c = df_export.shape
            worksheet.add_table(0, 0, max_r, max_c - 1, {
                'columns': [{'header': c} for c in df_export.columns],
                'style': 'Table Style Medium 9',
                'total_row': True
            })
            
            # Fórmulas de promedio en el Excel (ignorando negativos)
            fmt_v = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'num_format': '0.00'})
            for i, col_let in zip(range(8, 12), ['I', 'J', 'K', 'L']):
                formula = f"=AVERAGEIF([{df_export.columns[i]}], \">=0\")"
                worksheet.write_formula(max_r + 1, i, formula, fmt_v)
            
            worksheet.set_column(0, 11, 20)

        st.download_button("📥 Descargar Reporte Completo", output.getvalue(), "Reporte_IAAS.xlsx")

        with st.expander("👀 Ver Tabla de Datos Completa"):
            df_vis = df_p.iloc[:, :12].copy()
            for i in [0, 1, 3, 4, 6]:
                df_vis.iloc[:, i] = df_vis.iloc[:, i].dt.strftime('%d/%m/%Y').astype(str).replace('nan', '-')
            st.dataframe(df_vis.style.map(color_negativo_rojo, subset=df_vis.columns[8:12]), use_container_width=True)

else:
    st.info("👋 Sube tu archivo Excel para generar las gráficas y estadísticas.")
