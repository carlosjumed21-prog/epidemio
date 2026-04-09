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

st.title("📊 Sistema de Vigilancia IAAS - CMN 20 de Noviembre")
st.markdown("---")

archivo_iaas = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    if 'df_base' not in st.session_state:
        df_raw = pd.read_excel(archivo_iaas)
        # Delimitar a 121 filas reales (basado en A-H)
        df_limpio = df_raw.dropna(how='all', subset=df_raw.columns[:8]).reset_index(drop=True)
        st.session_state['df_base'] = df_limpio

    if st.button("🚀 Generar Estadísticas y Gráficas"):
        try:
            df = st.session_state['df_base'].iloc[:, :8].copy()
            idx_f = [0, 1, 3, 4, 6]
            for i in idx_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # --- CÁLCULOS I, J, K, L (Ajustados a tus comandos) ---
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
            st.success("✅ Datos procesados correctamente.")
            
        except Exception as e:
            st.error(f"❌ Error en cálculos: {e}")

    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        cols_tiempos = ["Detección", "Cultivo", "Entrega", "Captura"]

        # --- FILTROS ---
        st.subheader("🔍 Filtros de Análisis")
        c1, c2 = st.columns(2)
        with c1:
            # Obtenemos lista de sujetos únicos y los convertimos a String para la gráfica
            sujetos_reales = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            opciones_sujeto = ["Todos"] + [str(int(s)) if isinstance(s, float) else str(s) for s in sujetos_reales]
            s_sel = st.selectbox("Seleccionar Sujeto (Col F)", opciones_sujeto)
        with c2:
            mes_sel = st.selectbox("Periodo", ["Anual"] + list(MESES_MAP.values()))

        # Aplicar Filtros
        mask = pd.Series([True] * len(df_p))
        if s_sel != "Todos":
            mask = mask & (df_p.iloc[:, 5].astype(str) == s_sel)
        if mes_sel != "Anual":
            mask = mask & (df_p['Mes_Invisible'] == mes_sel)
        
        df_f = df_p[mask]

        # --- SECCIÓN DE GRÁFICAS ---
        st.divider()
        st.subheader(f"📈 Comparativa de Tiempos: {s_sel}")

        if not df_f.empty:
            # Limpieza para gráfica (tratar negativos como 0 para no romper el eje Y)
            df_plot = df_f.copy()
            for c in cols_tiempos:
                df_plot[c] = df_plot[c].apply(lambda x: x if x >= 0 else 0)

            if s_sel == "Todos":
                # Agrupamos por Sujeto y sacamos el promedio
                # Forzamos que el Sujeto sea string para que Plotly no salte números
                df_plot[df_plot.columns[5]] = df_plot[df_plot.columns[5]].astype(str)
                comp_df = df_plot.groupby(df_plot.columns[5])[cols_tiempos].mean().reset_index()
                
                # Crear la gráfica de barras agrupadas
                fig = px.bar(comp_df, 
                             x=df_plot.columns[5], 
                             y=cols_tiempos, 
                             title="Promedio de Días por Sujeto (Comparativo)",
                             labels={df_plot.columns[5]: 'Sujeto ID', 'value': 'Días', 'variable': 'Etapa'},
                             barmode='group',
                             text_auto='.1f',
                             color_discrete_sequence=px.colors.qualitative.Safe)
                
                # Ajuste para que el eje X muestre TODOS los números en orden
                fig.update_xaxes(type='category', categoryorder='array', categoryarray=opciones_sujeto[1:])
            else:
                # Gráfica individual
                ind_df = df_plot[cols_tiempos].mean().reset_index()
                ind_df.columns = ['Etapa', 'Promedio Días']
                fig = px.bar(ind_df, x='Etapa', y='Promedio Días', 
                             title=f"Tiempos Promedio - Sujeto {s_sel}",
                             color='Etapa', text_auto='.2f',
                             color_discrete_sequence=px.colors.qualitative.Pastel)

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay registros para este filtro.")

        # --- BOTONES Y ALERTAS ---
        tiene_rojos = (df_f[cols_tiempos] < 0).any().any()
        if tiene_rojos:
            st.warning("⚠️ **Nota:** Los días promedios son aproximados por fechas distantes.")

        st.write("### Indicadores Rápidos")
        m1, m2, m3, m4 = st.columns(4)
        def render_m(cont, label, col_name):
            if cont.button(label):
                if not df_f.empty:
                    val = df_f[col_name][df_f[col_name] >= 0].mean()
                    cont.metric("Días", f"{val:.2f}")
                else: cont.warning("N/A")

        render_m(m1, "Detección", "Detección")
        render_m(m2, "Cultivo", "Cultivo")
        render_m(m3, "Entrega", "Entrega")
        render_m(m4, "Captura", "Captura")

        # --- EXPORTACIÓN Y VISTA PREVIA ---
        st.divider()
        # Generar Excel con Tabla y Totales (Se mantiene lógica anterior)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p.iloc[:, :12].copy()
            df_export.to_excel(writer, index=False, sheet_name='Reporte')
            workbook, worksheet = writer.book, writer.sheets['Reporte']
            
            max_r, max_c = df_export.shape
            worksheet.add_table(0, 0, max_r - 1, max_c - 1, {
                'columns': [{'header': c} for c in df_export.columns],
                'style': 'Table Style Medium 9'
            })
            
            # Fila de Totales PROMEDIO (Fila max_r + 1)
            fmt_v = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'num_format': '0.00', 'border': 1})
            worksheet.write(max_r, 7, "PROMEDIO TOTAL", fmt_v)
            for i, col_let in zip(range(8, 12), ['I', 'J', 'K', 'L']):
                worksheet.write_formula(max_r, i, f"=AVERAGEIF({col_let}2:{col_let}{max_row}, \">=0\")", fmt_v)
            
            worksheet.set_column(0, 11, 20)

        st.download_button("📥 Descargar Reporte Final (A-L)", output.getvalue(), "Reporte_IAAS_Final.xlsx")

        with st.expander("👀 Ver Tabla de Datos (121 registros)"):
            df_vis = df_p.iloc[:, :12].copy()
            for i in [0, 1, 3, 4, 6]:
                df_vis.iloc[:, i] = df_vis.iloc[:, i].dt.strftime('%d/%m/%Y').astype(str).replace('nan', '-')
            st.dataframe(df_vis.style.map(color_negativo_rojo, subset=df_vis.columns[8:12]), use_container_width=True)
