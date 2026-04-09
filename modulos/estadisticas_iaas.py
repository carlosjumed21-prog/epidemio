import streamlit as st
import pandas as pd
import io
import plotly.express as px

# --- 1. CONFIGURACIÓN DE MESES ---
MESES_ORDEN = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
               'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

# Mapeo numérico para fechas de la Columna H
MES_NUM_MAP = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

def color_negativo_rojo(val):
    if isinstance(val, (int, float)) and val < 0:
        return 'color: red; font-weight: bold'
    return 'color: black'

st.title("🏥 Epidemiología CMN 20 de Noviembre")
st.markdown("---")

archivo_iaas = st.file_uploader("📂 1. Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    if 'df_base' not in st.session_state:
        df_raw = pd.read_excel(archivo_iaas)
        # Delimitar a 121 filas (A-H)
        st.session_state['df_base'] = df_raw.dropna(how='all', subset=df_raw.columns[:8]).reset_index(drop=True)

    # 2. PROCESAMIENTO
    if st.button("🚀 2. Procesar Datos Base"):
        try:
            df = st.session_state['df_base'].iloc[:, :8].copy()
            
            # Convertir fechas (A, B, D, E, G y H)
            # Ahora incluimos la columna H (índice 7) para extraer el mes
            for i in [0, 1, 3, 4, 6, 7]:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # Cálculos I, J, K, L, M
            df["Detección"] = (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1
            df["Cultivo"] = (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1
            df["Entrega"] = (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1
            df["Captura"] = (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1
            df["PROCESO"] = (df.iloc[:, 4] - df.iloc[:, 1]).dt.days + 1

            # Extraer Mes de la Columna H (index 7) usando el número del mes
            df['Mes_Nombre'] = df.iloc[:, 7].dt.month.map(MES_NUM_MAP)
            
            st.session_state['df_procesado'] = df
            st.success("✅ Datos listos. La Columna H se detectó como fecha correctamente.")
        except Exception as e:
            st.error(f"❌ Error al procesar: {e}")

    # 3. FILTROS Y GRÁFICAS
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        cols_estudio = ["Detección", "Cultivo", "Entrega", "Captura"]

        st.divider()
        st.subheader("🔍 3. Configuración de Filtros")
        
        c1, c2 = st.columns([1, 2])
        with c1:
            # Limpiar columna F (Sujetos) para que sean etiquetas consistentes
            sujetos = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            opciones_s = ["Todos"] + [str(int(s)) if isinstance(s, (float, int)) else str(s) for s in sujetos]
            s_sel = st.selectbox("Sujeto (Col F)", opciones_s)
        
        with c2:
            st.write("Seleccionar Meses (de Columna H):")
            check_t = st.checkbox("Seleccionar todo el año", value=True)
            if check_t:
                meses_sel = st.multiselect("Meses", MESES_ORDEN, default=MESES_ORDEN, disabled=True)
            else:
                meses_sel = st.multiselect("Meses", MESES_ORDEN, default=[])

        if st.button("📊 Generar / Actualizar Gráfica"):
            # Filtrado por Sujeto (Col F)
            mask = pd.Series([True] * len(df_p))
            if s_sel != "Todos":
                mask = mask & (df_p.iloc[:, 5].astype(str).str.contains(f"^{s_sel}$", regex=True) | 
                               df_p.iloc[:, 5].astype(float, errors='ignore').astype(str).str.contains(f"^{s_sel}$", regex=True))
            
            # Filtrado por Meses (Col H transformada)
            if meses_sel:
                mask = mask & (df_p['Mes_Nombre'].isin(meses_sel))
            
            df_f = df_p[mask]

            if not df_f.empty:
                # --- GRÁFICA ---
                df_plot = df_f.copy()
                for c in cols_estudio:
                    df_plot[c] = df_plot[c].apply(lambda x: x if x >= 0 else 0)

                if s_sel == "Todos":
                    # EJE X: SUJETOS (1-12) | EJE Y: DÍAS | BARRAS: LAS 4 ETAPAS
                    df_plot[df_p.columns[5]] = df_plot[df_p.columns[5]].astype(str)
                    comp_df = df_plot.groupby(df_p.columns[5])[cols_estudio].mean().reset_index()
                    fig = px.bar(comp_df, x=df_p.columns[5], y=cols_estudio, barmode='group',
                                 title="Anual: Comparativa entre Sujetos (Eje X: Sujetos)",
                                 labels={df_p.columns[5]: 'Sujetos (Col F)', 'value': 'Días'},
                                 text_auto='.1f', color_discrete_sequence=px.colors.qualitative.Bold)
                    # Forzar orden del 1 al 12
                    fig.update_xaxes(type='category', categoryorder='array', categoryarray=opciones_s[1:])
                else:
                    # EJE X: MESES | EJE Y: DÍAS
                    evol_df = df_plot.groupby('Mes_Nombre')[cols_estudio].mean().reindex(MESES_ORDEN).dropna(how='all').reset_index()
                    fig = px.bar(evol_df, x='Mes_Nombre', y=cols_estudio, barmode='group',
                                 title=f"Evolución Mensual: Sujeto {s_sel} (Eje X: Meses)",
                                 labels={'Mes_Nombre': 'Meses', 'value': 'Días'},
                                 text_auto='.1f', color_discrete_sequence=px.colors.qualitative.Pastel)

                st.plotly_chart(fig, use_container_width=True)

                # --- INDICADORES ---
                if (df_f[cols_estudio] < 0).any().any():
                    st.error("⚠️ **Nota:** Existen datos inconsistentes (fechas en rojo).")

                st.write(f"### Promedios: {s_sel}")
                m1, m2, m3, m4, m5 = st.columns(5)
                def render_m(cont, label, col):
                    val = df_f[col][df_f[col] >= 0].mean()
                    cont.metric(label, f"{val:.2f} d" if pd.notna(val) else "N/A")
                
                render_m(m1, "Detección", "Detección"); render_m(m2, "Cultivo", "Cultivo")
                render_m(m3, "Entrega", "Entrega"); render_m(m4, "Captura", "Captura")
                render_m(m5, "PROCESO", "PROCESO")
            else:
                st.warning("No se encontraron datos. Verifica que la Columna H tenga formato de fecha (ej. 01/01/2026).")

        # --- EXCEL DINÁMICO ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p.iloc[:, :13].copy()
            # Convertimos la columna H de nuevo a formato fecha para el Excel de salida
            df_export.iloc[:, 7] = pd.to_datetime(df_export.iloc[:, 7])
            
            df_export.to_excel(writer, index=False, sheet_name='Reporte')
            workbook, worksheet = writer.book, writer.sheets['Reporte']
            max_r = len(df_export)

            worksheet.add_table(0, 0, max_r, 12, {'style': 'Table Style Medium 9'})
            fmt_v = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'num_format': '0.00', 'border': 1})
            fmt_r = workbook.add_format({'font_color': 'red', 'bold': True})

            # Auxiliares ocultas (N-R)
            for r_idx in range(1, max_r + 1):
                for i, col_let in enumerate(['I', 'J', 'K', 'L', 'M']):
                    worksheet.write_formula(r_idx, 13 + i, f"=IF({col_let}{r_idx+1}>=0, {col_let}{r_idx+1}, \"\")")

            worksheet.set_column(13, 17, None, None, {'hidden': True})
            worksheet.write(max_r + 1, 7, "PROM. FILTRADO", fmt_v)
            for i, col_aux in zip(range(8, 13), ['N', 'O', 'P', 'Q', 'R']):
                worksheet.write_formula(max_r + 1, i, f"=SUBTOTAL(101, {col_aux}2:{col_aux}{max_r + 1})", fmt_v)

            worksheet.conditional_format(1, 8, max_r, 12, {'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_r})
            worksheet.set_column(0, 12, 18)

        st.download_button("📥 Descargar Reporte Final (A-M)", output.getvalue(), "Reporte_IAAS_Final.xlsx")

        with st.expander("👀 Ver Tabla de Datos"):
            df_vis = df_p.iloc[:, :13].copy()
            for i in [0, 1, 3, 4, 6, 7]:
                df_vis.iloc[:, i] = df_vis.iloc[:, i].dt.strftime('%d/%m/%Y').astype(str).replace('nan', '-')
            st.dataframe(df_vis.style.map(color_negativo_rojo, subset=df_vis.columns[8:13]), use_container_width=True)
