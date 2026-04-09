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

st.title("📊 Análisis de Tiempos IAAS - CMN 20 de Noviembre")

archivo_iaas = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    if 'df_base' not in st.session_state:
        df_raw = pd.read_excel(archivo_iaas)
        df_limpio = df_raw.dropna(how='all', subset=df_raw.columns[:8]).reset_index(drop=True)
        st.session_state['df_base'] = df_limpio

    if st.button("🚀 Generar Estadísticas y Gráficas"):
        try:
            df = st.session_state['df_base'].iloc[:, :8].copy()
            idx_f = [0, 1, 3, 4, 6]
            for i in idx_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # --- CÁLCULOS ---
            df.insert(8, "Detección", (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1)
            df.insert(9, "Cultivo", (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1)
            df.insert(10, "Entrega", (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1)
            df.insert(11, "Captura", (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1)

            def get_mes(v):
                v = str(v).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df['Mes_Nombre'] = df.iloc[:, 7].apply(get_mes)

            st.session_state['df_procesado'] = df
            st.success("✅ Datos procesados con éxito.")
            
        except Exception as e:
            st.error(f"❌ Error: {e}")

    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        cols_tiempos = ["Detección", "Cultivo", "Entrega", "Captura"]

        # --- FILTROS ---
        st.subheader("🔍 Filtros de Visualización")
        c1, c2 = st.columns(2)
        with c1:
            sujetos_reales = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            opciones_sujeto = ["Todos"] + [str(int(s)) if isinstance(s, float) else str(s) for s in sujetos_reales]
            s_sel = st.selectbox("Sujeto (Col F)", opciones_sujeto)
        with c2:
            mes_sel = st.selectbox("Periodo", ["Anual"] + MESES_ORDEN)

        # Aplicar Máscara de Datos
        mask = pd.Series([True] * len(df_p))
        if s_sel != "Todos":
            mask = mask & (df_p.iloc[:, 5].astype(str) == s_sel)
        if mes_sel != "Anual":
            mask = mask & (df_p['Mes_Nombre'] == mes_sel)
        
        df_f = df_p[mask]

        # --- LÓGICA DE GRÁFICAS ---
        st.divider()
        if not df_f.empty:
            # Limpiar negativos para la gráfica
            df_plot = df_f.copy()
            for c in cols_tiempos:
                df_plot[c] = df_plot[c].apply(lambda x: x if x >= 0 else 0)

            # CASO A: TODOS LOS SUJETOS
            if s_sel == "Todos":
                st.subheader("📈 Comparativa: Días por Sujeto")
                df_plot[df_p.columns[5]] = df_plot[df_p.columns[5]].astype(str)
                comp_df = df_plot.groupby(df_p.columns[5])[cols_tiempos].mean().reset_index()
                
                fig = px.bar(comp_df, x=df_p.columns[5], y=cols_tiempos, 
                             barmode='group', text_auto='.1f',
                             labels={df_p.columns[5]: 'Sujetos', 'value': 'Días', 'variable': 'Etapa'},
                             title="Desempeño Global por Sujeto",
                             color_discrete_sequence=px.colors.qualitative.Vivid)
                fig.update_xaxes(type='category', categoryorder='array', categoryarray=opciones_sujeto[1:])

            # CASO B: UN SUJETO / ANUAL (Evolución por Meses)
            elif s_sel != "Todos" and mes_sel == "Anual":
                st.subheader(f"📈 Evolución Mensual: Sujeto {s_sel}")
                # Agrupar por mes
                evol_df = df_plot.groupby('Mes_Nombre')[cols_tiempos].mean().reindex(MESES_ORDEN).reset_index()
                
                fig = px.bar(evol_df, x='Mes_Nombre', y=cols_tiempos, 
                             barmode='group', text_auto='.1f',
                             labels={'Mes_Nombre': 'Meses del Año', 'value': 'Días', 'variable': 'Etapa'},
                             title=f"Tiempos Promedio de {s_sel} a lo largo del año",
                             color_discrete_sequence=px.colors.qualitative.Safe)

            # CASO C: UN SUJETO / MES ESPECÍFICO
            else:
                st.subheader(f"📊 Resumen: Sujeto {s_sel} - {mes_sel}")
                res_df = df_plot[cols_tiempos].mean().reset_index()
                res_df.columns = ['Etapa', 'Días']
                fig = px.bar(res_df, x='Etapa', y='Días', color='Etapa', text_auto='.2f',
                             title=f"Promedio de Tiempos en {mes_sel}")

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("No hay datos para mostrar con los filtros seleccionados.")

        # --- ALERTAS Y BOTONES ---
        if (df_f[cols_tiempos] < 0).any().any():
            st.warning("⚠️ **Nota:** Existen fechas distantes; promedios calculados solo con valores válidos.")

        st.write("### Indicadores Rápidos")
        m1, m2, m3, m4 = st.columns(4)
        def r_m(cont, label, col_n):
            if cont.button(label):
                if not df_f.empty:
                    val = df_f[col_n][df_f[col_n] >= 0].mean()
                    cont.metric("Días", f"{val:.2f}")
                else: cont.write("N/A")
        
        r_m(m1, "Detección", "Detección"); r_m(m2, "Cultivo", "Cultivo")
        r_m(m3, "Entrega", "Entrega"); r_m(m4, "Captura", "Captura")

        # --- EXCEL Y VISTA PREVIA ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p.iloc[:, :12].copy()
            df_export.to_excel(writer, index=False, sheet_name='Reporte')
            workbook, worksheet = writer.book, writer.sheets['Reporte']
            max_r, max_c = df_export.shape
            worksheet.add_table(0, 0, max_r, max_c - 1, {'style': 'Table Style Medium 9', 'total_row': True})
            fmt_v = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'num_format': '0.00', 'border': 1})
            for i, col_let in zip(range(8, 12), ['I', 'J', 'K', 'L']):
                formula = f"=AVERAGEIF({col_let}2:{col_let}{max_r + 1}, \">=0\")"
                worksheet.write_formula(max_r + 1, i, formula, fmt_v)
            worksheet.set_column(0, 11, 20)
        
        st.download_button("📥 Descargar Reporte Final", output.getvalue(), "Reporte_IAAS_Final.xlsx")

        with st.expander("👀 Ver Tabla de Datos"):
            df_vis = df_p.iloc[:, :12].copy()
            for i in [0, 1, 3, 4, 6]:
                df_vis.iloc[:, i] = df_vis.iloc[:, i].dt.strftime('%d/%m/%Y').astype(str).replace('nan', '-')
            st.dataframe(df_vis.style.map(color_negativo_rojo, subset=df_vis.columns[8:12]), use_container_width=True)
