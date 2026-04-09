import streamlit as st
import pandas as pd
import io
import plotly.express as px

# --- 1. CONFIGURACIÓN DE MESES ---
MESES_ORDEN = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
               'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

MESES_MAP = {
    'ene': 'enero', 'feb': 'febrero', 'mar': 'marzo', 'abr': 'abril',
    'may': 'mayo', 'jun': 'junio', 'jul': 'julio', 'ago': 'agosto',
    'sep': 'septiembre', 'oct': 'octubre', 'nov': 'noviembre', 'dic': 'diciembre'
}

def color_negativo_rojo(val):
    if isinstance(val, (int, float)) and val < 0:
        return 'color: red; font-weight: bold'
    return 'color: black'

st.title("🏥 Epidemiología CMN 20 de Noviembre")
st.markdown("### Control de Tiempos y Procesos IAAS")

archivo_iaas = st.file_uploader("📂 1. Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    # Carga y limpieza inicial
    if 'df_base' not in st.session_state:
        df_raw = pd.read_excel(archivo_iaas)
        # Delimitar a 121 filas reales (A-H)
        st.session_state['df_base'] = df_raw.dropna(how='all', subset=df_raw.columns[:8]).reset_index(drop=True)

    if st.button("🚀 2. Procesar Datos y Generar Panel"):
        try:
            df = st.session_state['df_base'].iloc[:, :8].copy()
            idx_f = [0, 1, 3, 4, 6]
            for i in idx_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # --- CÁLCULOS (I, J, K, L, M) ---
            df["Detección"] = (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1
            df["Cultivo"] = (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1
            df["Entrega"] = (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1
            df["Captura"] = (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1
            df["PROCESO"] = (df.iloc[:, 4] - df.iloc[:, 1]).dt.days + 1

            # Mes para filtros
            def get_mes(v):
                v = str(v).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df['Mes_Nombre'] = df.iloc[:, 7].apply(get_mes)

            st.session_state['df_procesado'] = df
            st.success("✅ Datos listos. Ajusta los filtros abajo para ver las gráficas.")
        except Exception as e:
            st.error(f"❌ Error al procesar: {e}")

    # --- PANEL DE CONTROL REACTIVO ---
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        cols_grafica = ["Detección", "Cultivo", "Entrega", "Captura"]

        st.divider()
        st.subheader("🔍 3. Filtros de Análisis")
        
        c1, c2 = st.columns([1, 2])
        with c1:
            sujetos = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            opciones_s = ["Todos"] + [str(int(s)) if isinstance(s, float) else str(s) for s in sujetos]
            s_sel = st.selectbox("Persona (Sujeto)", opciones_s)
        
        with c2:
            st.write("Seleccionar Meses:")
            check_t = st.checkbox("Seleccionar todo el año", value=True)
            if check_t:
                meses_sel = st.multiselect("Meses", MESES_ORDEN, default=MESES_ORDEN, disabled=True)
            else:
                meses_sel = st.multiselect("Meses", MESES_ORDEN, default=[])

        # Filtrado Dinámico
        mask = pd.Series([True] * len(df_p))
        if s_sel != "Todos":
            mask = mask & (df_p.iloc[:, 5].astype(str) == s_sel)
        if meses_sel:
            mask = mask & (df_p['Mes_Nombre'].isin(meses_sel))
        else:
            mask = pd.Series([False] * len(df_p))
        
        df_f = df_p[mask]

        # --- SECCIÓN DE GRÁFICAS ---
        st.subheader("📈 Visualización de Tiempos")
        if not df_f.empty:
            df_plot = df_f.copy()
            # Limpiar negativos para la gráfica (ponerlos en 0 para no romper el eje Y)
            for c in cols_grafica:
                df_plot[c] = df_plot[c].apply(lambda x: x if x >= 0 else 0)

            # GRÁFICA A: TODOS / ANUAL (O MESES SELEC)
            if s_sel == "Todos":
                df_plot[df_p.columns[5]] = df_plot[df_p.columns[5]].astype(str)
                comp_df = df_plot.groupby(df_p.columns[5])[cols_grafica].mean().reset_index()
                
                fig = px.bar(comp_df, x=df_p.columns[5], y=cols_grafica, 
                             barmode='group', text_auto='.1f',
                             labels={df_p.columns[5]: 'Sujetos', 'value': 'Días'},
                             title="Comparativa Global por Sujeto",
                             color_discrete_sequence=px.colors.qualitative.Prism)
                fig.update_xaxes(type='category', categoryorder='array', categoryarray=opciones_s[1:])

            # GRÁFICA B: INDIVIDUO / MESES SELEC
            else:
                evol_df = df_plot.groupby('Mes_Nombre')[cols_grafica].mean().reindex(MESES_ORDEN).dropna(how='all').reset_index()
                
                fig = px.bar(evol_df, x='Mes_Nombre', y=cols_grafica, 
                             barmode='group', text_auto='.1f',
                             labels={'Mes_Nombre': 'Meses', 'value': 'Días'},
                             title=f"Evolución Mensual: Sujeto {s_sel}",
                             color_discrete_sequence=px.colors.qualitative.Pastel)

            st.plotly_chart(fig, use_container_width=True)

            # LEYENDA Y MÉTRICAS
            if (df_f[cols_grafica] < 0).any().any():
                st.error("⚠️ **Nota:** Los días promedios son aproximados por fechas distantes (registros en rojo).")

            st.write("### Indicadores Promedio (Filtro Actual)")
            m1, m2, m3, m4, m5 = st.columns(5)
            def r_m(cont, label, col):
                val = df_f[col][df_f[col] >= 0].mean()
                cont.metric(label, f"{val:.2f} d" if pd.notna(val) else "N/A")
            
            r_m(m1, "Detección", "Detección"); r_m(m2, "Cultivo", "Cultivo")
            r_m(m3, "Entrega", "Entrega"); r_m(m4, "Captura", "Captura")
            r_m(m5, "PROCESO", "PROCESO")

        else:
            st.warning("⚠️ No hay datos para mostrar. Por favor selecciona al menos un mes en las casillas.")

        # --- EXCEL DINÁMICO ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p.iloc[:, :13].copy()
            df_export.to_excel(writer, index=False, sheet_name='Reporte')
            workbook, worksheet = writer.book, writer.sheets['Reporte']
            max_r = len(df_export)

            worksheet.add_table(0, 0, max_r, 12, {'style': 'Table Style Medium 9'})
            fmt_v = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'num_format': '0.00', 'border': 1})
            fmt_r = workbook.add_format({'font_color': 'red', 'bold': True})

            # Auxiliares ocultas (N-R) para SUBTOTAL dinámico
            letras_calc = ['I', 'J', 'K', 'L', 'M']
            for r_idx in range(1, max_r + 1):
                for i, col_let in enumerate(letras_calc):
                    worksheet.write_formula(r_idx, 13 + i, f"=IF({col_let}{r_idx+1}>=0, {col_let}{r_idx+1}, \"\")")

            worksheet.set_column(13, 17, None, None, {'hidden': True})
            worksheet.write(max_r + 1, 7, "PROM. FILTRADO", fmt_v)
            letras_aux = ['N', 'O', 'P', 'Q', 'R']
            for i, col_aux in zip(range(8, 13), letras_aux):
                worksheet.write_formula(max_r + 1, i, f"=SUBTOTAL(101, {col_aux}2:{col_aux}{max_r + 1})", fmt_v)

            worksheet.conditional_format(1, 8, max_r, 12, {'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_r})
            worksheet.set_column(0, 12, 18)

        st.download_button("📥 Descargar Reporte Final (A-M)", output.getvalue(), "Reporte_IAAS_Final.xlsx")

        with st.expander("👀 Ver Tabla de Datos"):
            df_vis = df_p.iloc[:, :13].copy()
            for i in [0, 1, 3, 4, 6]:
                df_vis.iloc[:, i] = df_vis.iloc[:, i].dt.strftime('%d/%m/%Y').astype(str).replace('nan', '-')
            st.dataframe(df_vis.style.map(color_negativo_rojo, subset=df_vis.columns[8:13]), use_container_width=True)
