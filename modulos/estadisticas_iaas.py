import streamlit as st
import pandas as pd
import io
import plotly.express as px

# --- 1. CONFIGURACIÓN ---
MESES_ORDEN = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
               'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

MES_NUM_MAP = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

ETIQUETAS_FINALES = [
    "Fecha de deteccion", "Fecha de Inicio", "Fecha de Termino", 
    "Fecha de toma del cultivo", "FECHA DE ENTREGA", "MODIFICACION", 
    "Fecha de captura en RHOVE", "MES 1", "Detección", 
    "Cultivo", "Entrega", "Captura", "Proceso"
]

def color_negativo_rojo(val):
    if isinstance(val, (int, float)) and val < 0:
        return 'color: red; font-weight: bold'
    return 'color: black'

st.set_page_config(page_title="Vigilancia IAAS CMN 20", layout="wide")
st.title("🏥 Vigilancia IAAS - CMN 20 de Noviembre")
st.markdown("---")

archivo_iaas = st.file_uploader("📂 1. Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    if 'df_base' not in st.session_state:
        df_raw = pd.read_excel(archivo_iaas)
        df_base = df_raw.iloc[:, :8].copy()
        df_base.columns = ETIQUETAS_FINALES[:8]
        df_base["MODIFICACION"] = pd.to_numeric(df_base["MODIFICACION"], errors='coerce')
        st.session_state['df_base'] = df_base.dropna(how='all', subset=["Fecha de deteccion"]).reset_index(drop=True)

    if st.button("🚀 Procesar Datos Base"):
        try:
            df = st.session_state['df_base'].copy()
            cols_f = ["Fecha de deteccion", "Fecha de Inicio", "Fecha de toma del cultivo", 
                      "FECHA DE ENTREGA", "Fecha de captura en RHOVE", "MES 1"]
            for col in cols_f:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

            # --- CÁLCULOS I-M ---
            df["Detección"] = (df["Fecha de deteccion"] - df["Fecha de Inicio"]).dt.days + 1
            df["Cultivo"] = (df["Fecha de Inicio"] - df["Fecha de toma del cultivo"]).dt.days + 1
            df["Entrega"] = (df["FECHA DE ENTREGA"] - df["Fecha de deteccion"]).dt.days + 1
            df["Captura"] = (df["Fecha de captura en RHOVE"] - df["FECHA DE ENTREGA"]).dt.days + 1
            df["Proceso"] = (df["FECHA DE ENTREGA"] - df["Fecha de Inicio"]).dt.days + 1

            df['Mes_Nombre'] = df["MES 1"].dt.month.map(MES_NUM_MAP)
            st.session_state['df_procesado'] = df
            st.success("✅ Datos procesados con éxito.")
        except Exception as e:
            st.error(f"❌ Error: {e}")

    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        # Definimos las 5 etiquetas para las gráficas (incluyendo Proceso)
        etiquetas_grafica = ["Detección", "Cultivo", "Entrega", "Captura", "Proceso"]

        st.subheader("🔍 Filtros Dinámicos")
        c1, c2 = st.columns([1, 2])
        
        with c1:
            sujetos_lista = sorted([int(s) for s in df_p["MODIFICACION"].unique() if pd.notna(s)])
            opciones_s = ["Todos"] + [str(s) for s in sujetos_lista]
            s_sel = st.selectbox("Sujeto (MODIFICACION)", opciones_s)
        
        with c2:
            st.write("Seleccionar Meses:")
            check_t = st.checkbox("Seleccionar todo el año", value=True)
            if check_t:
                meses_sel = MESES_ORDEN
                st.multiselect("Meses", MESES_ORDEN, default=MESES_ORDEN, disabled=True, key="ms_dis")
            else:
                meses_sel = st.multiselect("Meses", MESES_ORDEN, default=[], key="ms_en")

        # Filtrado Dinámico
        mask = pd.Series([True] * len(df_p))
        if s_sel != "Todos":
            mask = mask & (df_p["MODIFICACION"].fillna(-1).astype(int).astype(str) == s_sel)
        if meses_sel:
            mask = mask & (df_p['Mes_Nombre'].isin(meses_sel))
        
        df_f = df_p[mask].copy()

        if not df_f.empty:
            st.divider()
            
            df_plot = df_f.copy()
            for c in etiquetas_grafica:
                df_plot[c] = df_plot[c].apply(lambda x: x if x >= 0 else 0)

            if s_sel == "Todos":
                # GRÁFICA COMPARATIVA GLOBAL (Incluye Proceso)
                comp_df = df_plot.groupby("MODIFICACION")[etiquetas_grafica].mean().reset_index()
                comp_df = comp_df.sort_values(by="MODIFICACION")
                comp_df["MODIFICACION"] = comp_df["MODIFICACION"].astype(int).astype(str)
                
                fig = px.bar(comp_df, x="MODIFICACION", y=etiquetas_grafica, barmode='group',
                             title="📊 Comparativa Anual por Sujeto (Incluye Proceso Total)",
                             labels={'MODIFICACION': 'ID Sujeto', 'value': 'Días', 'variable': 'Etapa'},
                             text_auto='.1f', color_discrete_sequence=px.colors.qualitative.Bold)
                fig.update_xaxes(type='category', categoryorder='array', categoryarray=opciones_s[1:])
            else:
                # GRÁFICA EVOLUCIÓN INDIVIDUAL (Incluye Proceso)
                evol_df = df_plot.groupby('Mes_Nombre')[etiquetas_grafica].mean().reindex(MESES_ORDEN).dropna(how='all').reset_index()
                fig = px.bar(evol_df, x='Mes_Nombre', y=etiquetas_grafica, barmode='group',
                             title=f"📈 Evolución Mensual: Sujeto {s_sel} (Incluye Proceso Total)",
                             labels={'Mes_Nombre': 'Meses', 'value': 'Días', 'variable': 'Etapa'},
                             text_auto='.1f', color_discrete_sequence=px.colors.qualitative.Safe)

            st.plotly_chart(fig, use_container_width=True)

            if (df_f[ETIQUETAS_FINALES[8:]] < 0).any().any():
                st.error("⚠️ Nota: Se detectaron registros inconsistentes (rojos).")

            st.write(f"### Promedios: {s_sel}")
            metrics_cols = st.columns(5)
            for i, etiqueta in enumerate(ETIQUETAS_FINALES[8:]):
                val = df_f[etiqueta][df_f[etiqueta] >= 0].mean()
                metrics_cols[i].metric(etiqueta, f"{val:.2f} d" if pd.notna(val) else "N/A")
        else:
            st.warning("⚠️ No hay datos para los filtros seleccionados.")

        # --- EXCEL DE SALIDA (A-M) ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p[ETIQUETAS_FINALES].copy()
            df_export.to_excel(writer, index=False, sheet_name='Reporte')
            workbook, worksheet = writer.book, writer.sheets['Reporte']
            max_r = len(df_export)
            
            column_settings = [{'header': col} for col in ETIQUETAS_FINALES]
            worksheet.add_table(0, 0, max_r, 12, {'columns': column_settings, 'style': 'Table Style Medium 9'})
            
            fmt_v = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'num_format': '0.00', 'border': 1})
            fmt_r = workbook.add_format({'font_color': 'red', 'bold': True})

            for r_idx in range(1, max_r + 1):
                for i, col_let in enumerate(['I', 'J', 'K', 'L', 'M']):
                    worksheet.write_formula(r_idx, 13 + i, f"=IF({col_let}{r_idx+1}>=0, {col_let}{r_idx+1}, \"\")")

            worksheet.set_column(13, 17, None, None, {'hidden': True})
            worksheet.write(max_r + 1, 7, "PROM. FILTRADO", fmt_v)
            for i, col_aux in zip(range(8, 13), ['N', 'O', 'P', 'Q', 'R']):
                worksheet.write_formula(max_r + 1, i, f"=SUBTOTAL(101, {col_aux}2:{col_aux}{max_r + 1})", fmt_v)

            worksheet.conditional_format(1, 8, max_r, 12, {'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_r})
            worksheet.set_column(0, 12, 22)

        st.download_button("📥 Descargar Reporte Final (A-M)", output.getvalue(), "Reporte_IAAS_Final.xlsx")

        with st.expander("👀 Ver Tabla de Datos"):
            df_vis = df_p[ETIQUETAS_FINALES].copy()
            for col in ETIQUETAS_FINALES[:8]:
                if "Fecha" in col or "FECHA" in col or "MES" in col:
                    df_vis[col] = df_vis[col].dt.strftime('%d/%m/%Y').astype(str).replace('nan', '-')
            st.dataframe(df_vis.style.map(color_negativo_rojo, subset=ETIQUETAS_FINALES[8:]), use_container_width=True)
