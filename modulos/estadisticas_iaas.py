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

# TUS 13 ETIQUETAS OFICIALES
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

st.title("🏥 Vigilancia IAAS - CMN 20 de Noviembre")
st.markdown("---")

archivo_iaas = st.file_uploader("📂 1. Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    if 'df_base' not in st.session_state:
        # Cargamos ignorando los encabezados que traiga el archivo para evitar basura
        df_raw = pd.read_excel(archivo_iaas)
        # Tomamos las primeras 8 columnas (A-H)
        df_base = df_raw.iloc[:, :8].copy()
        # Forzamos los nombres de las primeras 8
        df_base.columns = ETIQUETAS_FINALES[:8]
        st.session_state['df_base'] = df_base.dropna(how='all').reset_index(drop=True)

    # 2. PROCESAMIENTO
    if st.button("🚀 2. Procesar Datos y Aplicar Etiquetas"):
        try:
            df = st.session_state['df_base'].copy()
            
            # Convertir fechas para cálculos
            # A (0), B (1), D (3), E (4), G (6), H (7)
            cols_f = ["Fecha de deteccion", "Fecha de Inicio", "Fecha de toma del cultivo", 
                      "FECHA DE ENTREGA", "Fecha de captura en RHOVE", "MES 1"]
            
            for col in cols_f:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

            # --- CÁLCULOS (I, J, K, L, M) ---
            df["Detección"] = (df["Fecha de deteccion"] - df["Fecha de Inicio"]).dt.days + 1
            df["Cultivo"] = (df["Fecha de Inicio"] - df["Fecha de toma del cultivo"]).dt.days + 1
            df["Entrega"] = (df["FECHA DE ENTREGA"] - df["Fecha de deteccion"]).dt.days + 1
            df["Captura"] = (df["Fecha de captura en RHOVE"] - df["FECHA DE ENTREGA"]).dt.days + 1
            df["Proceso"] = (df["FECHA DE ENTREGA"] - df["Fecha de Inicio"]).dt.days + 1

            # Extraer Mes para filtros
            df['Mes_Nombre'] = df["MES 1"].dt.month.map(MES_NUM_MAP)
            
            st.session_state['df_procesado'] = df
            st.success("✅ Datos procesados con las 13 etiquetas oficiales.")
        except Exception as e:
            st.error(f"❌ Error al procesar: {e}")

    # 3. FILTROS Y GRÁFICAS
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        etiquetas_stats = ["Detección", "Cultivo", "Entrega", "Captura"]

        st.divider()
        st.subheader("🔍 3. Filtros y Gráficas")
        
        c1, c2 = st.columns([1, 2])
        with c1:
            sujetos = sorted([s for s in df_p["MODIFICACION"].unique() if pd.notna(s)])
            opciones_s = ["Todos"] + [str(int(s)) if isinstance(s, (float, int)) else str(s) for s in sujetos]
            s_sel = st.selectbox("Sujeto (MODIFICACION)", opciones_s)
        
        with c2:
            st.write("Seleccionar Meses (MES 1):")
            check_t = st.checkbox("Seleccionar todo el año", value=True)
            meses_sel = MESES_ORDEN if check_t else st.multiselect("Meses", MESES_ORDEN, default=[])

        if st.button("📊 Generar / Actualizar Gráfica"):
            mask = pd.Series([True] * len(df_p))
            if s_sel != "Todos":
                mask = mask & (df_p["MODIFICACION"].astype(str).str.contains(f"^{s_sel}$"))
            if meses_sel:
                mask = mask & (df_p['Mes_Nombre'].isin(meses_sel))
            
            df_f = df_p[mask]

            if not df_f.empty:
                df_plot = df_f.copy()
                for c in etiquetas_stats:
                    df_plot[c] = df_plot[c].apply(lambda x: x if x >= 0 else 0)

                if s_sel == "Todos":
                    df_plot["MODIFICACION"] = df_plot["MODIFICACION"].astype(str)
                    comp_df = df_plot.groupby("MODIFICACION")[etiquetas_stats].mean().reset_index()
                    fig = px.bar(comp_df, x="MODIFICACION", y=etiquetas_stats, barmode='group',
                                 title="Comparativa Global por Sujeto",
                                 labels={'value': 'Días', 'variable': 'Etapa'},
                                 text_auto='.1f', color_discrete_sequence=px.colors.qualitative.Safe)
                    fig.update_xaxes(type='category', categoryorder='array', categoryarray=opciones_s[1:])
                else:
                    evol_df = df_plot.groupby('Mes_Nombre')[etiquetas_stats].mean().reindex(MESES_ORDEN).dropna(how='all').reset_index()
                    fig = px.bar(evol_df, x='Mes_Nombre', y=etiquetas_stats, barmode='group',
                                 title=f"Evolución Mensual: Sujeto {s_sel}",
                                 labels={'Mes_Nombre': 'Meses', 'value': 'Días'},
                                 text_auto='.1f', color_discrete_sequence=px.colors.qualitative.Pastel)

                st.plotly_chart(fig, use_container_width=True)

                if (df_f[ETIQUETAS_FINALES[8:]] < 0).any().any():
                    st.error("⚠️ Nota: Se detectaron registros inconsistentes (rojos).")

                st.write(f"### Promedios: {s_sel}")
                metrics_cols = st.columns(5)
                for i, etiqueta in enumerate(ETIQUETAS_FINALES[8:]):
                    val = df_f[etiqueta][df_f[etiqueta] >= 0].mean()
                    metrics_cols[i].metric(etiqueta, f"{val:.2f} d" if pd.notna(val) else "N/A")
            else:
                st.warning("No hay datos para esta selección.")

        # --- EXCEL DE SALIDA (AQUÍ CORREGIMOS LAS ETIQUETAS) ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            # Aseguramos que el DF de exportación tenga las 13 columnas en orden
            df_export = df_p[ETIQUETAS_FINALES].copy()
            # Devolvemos MES 1 a formato fecha para el Excel
            df_export["MES 1"] = pd.to_datetime(df_export["MES 1"])
            
            df_export.to_excel(writer, index=False, sheet_name='Reporte')
            
            workbook, worksheet = writer.book, writer.sheets['Reporte']
            max_r = len(df_export)

            # FORZAMOS LAS ETIQUETAS EN LA TABLA DE EXCEL
            column_settings = [{'header': col} for col in ETIQUETAS_FINALES]
            
            worksheet.add_table(0, 0, max_r, 12, {
                'columns': column_settings,
                'style': 'Table Style Medium 9'
            })
            
            fmt_v = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'num_format': '0.00', 'border': 1})
            fmt_r = workbook.add_format({'font_color': 'red', 'bold': True})

            # Auxiliares ocultas para promedios dinámicos (N-R)
            letras_calc = ['I', 'J', 'K', 'L', 'M']
            for r_idx in range(1, max_r + 1):
                for i, col_let in enumerate(letras_calc):
                    worksheet.write_formula(r_idx, 13 + i, f"=IF({col_let}{r_idx+1}>=0, {col_let}{r_idx+1}, \"\")")

            worksheet.set_column(13, 17, None, None, {'hidden': True})
            worksheet.write(max_r + 1, 7, "PROM. FILTRADO", fmt_v)
            for i, col_aux in zip(range(8, 13), ['N', 'O', 'P', 'Q', 'R']):
                worksheet.write_formula(max_r + 1, i, f"=SUBTOTAL(101, {col_aux}2:{col_aux}{max_r + 1})", fmt_v)

            worksheet.conditional_format(1, 8, max_r, 12, {'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_r})
            worksheet.set_column(0, 12, 22)

        st.download_button("📥 Descargar Reporte Final (A-M)", output.getvalue(), "Reporte_IAAS_Final.xlsx")

        with st.expander("👀 Ver Tabla de Datos"):
            # Mostramos la tabla tal cual se exportará
            df_vis = df_p[ETIQUETAS_FINALES].copy()
            for col in ETIQUETAS_FINALES[:8]:
                if "Fecha" in col or "FECHA" in col or "MES" in col:
                    df_vis[col] = df_vis[col].dt.strftime('%d/%m/%Y').astype(str).replace('nan', '-')
            st.dataframe(df_vis.style.map(color_negativo_rojo, subset=ETIQUETAS_FINALES[8:]), use_container_width=True)
