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

st.title("📊 Análisis IAAS - Reporte Dinámico")
st.markdown("---")

archivo_iaas = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    if 'df_base' not in st.session_state:
        df_raw = pd.read_excel(archivo_iaas)
        # Delimitar estrictamente a las 121 filas reales
        st.session_state['df_base'] = df_raw.dropna(how='all', subset=df_raw.columns[:8]).reset_index(drop=True)

    if st.button("🚀 Procesar Datos"):
        try:
            df = st.session_state['df_base'].iloc[:, :8].copy()
            idx_f = [0, 1, 3, 4, 6]
            for i in idx_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # --- CÁLCULOS I, J, K, L ---
            df["Detección"] = (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1
            df["Cultivo"] = (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1
            df["Entrega"] = (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1
            df["Captura"] = (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1

            def get_mes(v):
                v = str(v).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df['Mes_Nombre'] = df.iloc[:, 7].apply(get_mes)

            st.session_state['df_procesado'] = df
            st.success("✅ Datos procesados. Panel de control activado.")
        except Exception as e:
            st.error(f"❌ Error: {e}")

    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        cols_tiempos = ["Detección", "Cultivo", "Entrega", "Captura"]

        # --- FILTROS (SUJETOS Y MESES CON CASILLAS) ---
        st.subheader("🔍 Filtros de Visualización")
        c1, c2 = st.columns([1, 2])
        
        with c1:
            sujetos_reales = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            opciones_sujeto = ["Todos"] + [str(int(s)) if isinstance(s, float) else str(s) for s in sujetos_reales]
            s_sel = st.selectbox("Seleccionar Sujeto (Col F)", opciones_sujeto)
        
        with c2:
            st.write("Meses (Marcar casillas):")
            check_todos = st.checkbox("Seleccionar todo el año", value=True)
            if check_todos:
                meses_sel = st.multiselect("Meses", MESES_ORDEN, default=MESES_ORDEN, disabled=True)
            else:
                meses_sel = st.multiselect("Meses", MESES_ORDEN, default=[])

        # Filtrado dinámico para la App
        mask = pd.Series([True] * len(df_p))
        if s_sel != "Todos": mask = mask & (df_p.iloc[:, 5].astype(str) == s_sel)
        if meses_sel: mask = mask & (df_p['Mes_Nombre'].isin(meses_sel))
        else: mask = pd.Series([False] * len(df_p))
        
        df_f = df_p[mask]

        # --- GRÁFICAS ---
        if not df_f.empty:
            df_plot = df_f.copy()
            for c in cols_tiempos: df_plot[c] = df_plot[c].apply(lambda x: x if x >= 0 else 0)

            if s_sel == "Todos":
                comp_df = df_plot.groupby(df_p.columns[5])[cols_tiempos].mean().reset_index()
                fig = px.bar(comp_df, x=df_p.columns[5], y=cols_tiempos, barmode='group', title="Comparativa Global por Sujeto", text_auto='.1f')
            elif len(meses_sel) > 1:
                evol_df = df_plot.groupby('Mes_Nombre')[cols_tiempos].mean().reindex(MESES_ORDEN).dropna(how='all').reset_index()
                fig = px.bar(evol_df, x='Mes_Nombre', y=cols_tiempos, barmode='group', title=f"Evolución Mensual - Sujeto {s_sel}", text_auto='.1f')
            else:
                res_df = df_plot[cols_tiempos].mean().reset_index()
                res_df.columns = ['Etapa', 'Días']; fig = px.bar(res_df, x='Etapa', y='Días', color='Etapa', text_auto='.2f')
            st.plotly_chart(fig, use_container_width=True)

            # LEYENDA DE ADVERTENCIA
            if (df_f[cols_tiempos] < 0).any().any():
                st.error("⚠️ **Nota:** Los días promedios son aproximados por fechas distantes.")

            # INDICADORES (4 BOTONES/MÉTRICAS)
            st.write("### Indicadores de Tiempo (Promedio)")
            m1, m2, m3, m4 = st.columns(4)
            def render(cont, label, col):
                val = df_f[col][df_f[col] >= 0].mean()
                cont.metric(label, f"{val:.2f} d" if pd.notna(val) else "N/A")
            render(m1, "Detección", "Detección"); render(m2, "Cultivo", "Cultivo")
            render(m3, "Entrega", "Entrega"); render(m4, "Captura", "Captura")

        # --- EXCEL DINÁMICO (AQUÍ ESTÁ LA MAGIA) ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p.iloc[:, :12].copy()
            df_export.to_excel(writer, index=False, sheet_name='Reporte')
            workbook, worksheet = writer.book, writer.sheets['Reporte']
            max_r = len(df_export)

            # Crear Tabla de Excel
            worksheet.add_table(0, 0, max_r, 11, {'columns': [{'header': c} for c in df_export.columns], 'style': 'Table Style Medium 9'})
            
            # Formatos
            fmt_v = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'num_format': '0.00', 'border': 1})
            fmt_rojo = workbook.add_format({'font_color': 'red', 'bold': True})

            # TRUCO: Columnas auxiliares ocultas (M, N, O, P) para ignorar negativos en SUBTOTALES
            # M (12), N (13), O (14), P (15)
            for r_idx in range(1, max_r + 1):
                # Para cada fila, escribimos la lógica: SI(I2>=0; I2; "")
                for i, col_let in enumerate(['I', 'J', 'K', 'L']):
                    formula = f"=IF({col_let}{r_idx+1}>=0, {col_let}{r_idx+1}, \"\")"
                    worksheet.write_formula(r_idx, 12 + i, formula)

            # Ocultar las columnas auxiliares M, N, O, P
            worksheet.set_column(12, 15, None, None, {'hidden': True})

            # FILA DE TOTALES DINÁMICA
            worksheet.write(max_r + 1, 7, "PROMEDIO FILTRADO", fmt_v)
            for i, col_aux in zip(range(8, 12), ['M', 'N', 'O', 'P']):
                # SUBTOTALES(101, ...) calcula el promedio de solo lo VISIBLE
                formula = f"=SUBTOTAL(101, {col_aux}2:{col_aux}{max_r + 1})"
                worksheet.write_formula(max_r + 1, i, formula, fmt_v)

            # Formato condicional para negativos
            worksheet.conditional_format(1, 8, max_r, 11, {'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_rojo})
            worksheet.set_column(0, 11, 20)

        st.download_button("📥 Descargar Reporte Dinámico", output.getvalue(), "Reporte_IAAS_Dinámico.xlsx")
