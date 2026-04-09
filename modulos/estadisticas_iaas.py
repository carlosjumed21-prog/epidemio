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
st.markdown("---")

archivo_iaas = st.file_uploader("📂 Sube tu archivo Excel (121 registros)", type=["xlsx"])

if archivo_iaas:
    # Carga inicial y limpieza de filas fantasma
    if 'df_base' not in st.session_state:
        df_raw = pd.read_excel(archivo_iaas)
        # Tomamos solo las filas que tengan datos en las primeras columnas (A-H)
        st.session_state['df_base'] = df_raw.dropna(how='all', subset=df_raw.columns[:8]).reset_index(drop=True)

    # BOTÓN DE PROCESAMIENTO
    if st.button("🚀 Procesar Datos y Generar Reporte"):
        try:
            df = st.session_state['df_base'].iloc[:, :8].copy()
            
            # Convertir fechas (A, B, D, E, G)
            idx_f = [0, 1, 3, 4, 6]
            for i in idx_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # --- CÁLCULOS (Columnas I, J, K, L) ---
            df["Detección"] = (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1
            df["Cultivo"] = (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1
            df["Entrega"] = (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1
            df["Captura"] = (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1

            # Crear columna de Mes para los filtros
            def get_mes(v):
                v = str(v).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df['Mes_Nombre'] = df.iloc[:, 7].apply(get_mes)

            # GUARDAR EN SESSION STATE PARA PERSISTENCIA
            st.session_state['df_procesado'] = df
            st.success(f"✅ ¡Procesamiento listo! {len(df)} registros detectados.")
        except Exception as e:
            st.error(f"❌ Error al procesar: {e}")

    # --- MOSTRAR RESULTADOS (Fuera del botón para que no desaparezcan) ---
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        cols_tiempos = ["Detección", "Cultivo", "Entrega", "Captura"]

        st.divider()
        st.subheader("🔍 Filtros de Visualización")
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            sujetos_reales = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            opciones_sujeto = ["Todos"] + [str(int(s)) if isinstance(s, float) else str(s) for s in sujetos_reales]
            s_sel = st.selectbox("Seleccionar Persona (Sujetos)", opciones_sujeto)
        
        with c2:
            st.write("Seleccionar Meses:")
            check_todos = st.checkbox("Seleccionar todo el año", value=True)
            if check_todos:
                meses_sel = st.multiselect("Meses", MESES_ORDEN, default=MESES_ORDEN, disabled=True)
            else:
                meses_sel = st.multiselect("Meses", MESES_ORDEN, default=[])

        # FILTRADO DINÁMICO
        mask = pd.Series([True] * len(df_p))
        if s_sel != "Todos":
            mask = mask & (df_p.iloc[:, 5].astype(str) == s_sel)
        if meses_sel:
            mask = mask & (df_p['Mes_Nombre'].isin(meses_sel))
        else:
            mask = pd.Series([False] * len(df_p))
        
        df_f = df_p[mask]

        # --- SECCIÓN DE GRÁFICAS ---
        st.subheader("📈 Gráfica de Tiempos")
        if not df_f.empty:
            # Limpiamos negativos solo para que la gráfica no se rompa (se muestran como 0)
            df_plot = df_f.copy()
            for c in cols_tiempos:
                df_plot[c] = df_plot[c].apply(lambda x: x if x >= 0 else 0)

            if s_sel == "Todos":
                # Eje X: Sujetos | Barras: Tiempos
                df_plot[df_p.columns[5]] = df_plot[df_p.columns[5]].astype(str)
                comp_df = df_plot.groupby(df_p.columns[5])[cols_tiempos].mean().reset_index()
                fig = px.bar(comp_df, x=df_p.columns[5], y=cols_tiempos, barmode='group',
                             title="Promedio de Días por Sujeto", text_auto='.1f')
                fig.update_xaxes(type='category', categoryorder='array', categoryarray=opciones_sujeto[1:])
            elif len(meses_sel) > 1:
                # Eje X: Meses | Barras: Tiempos
                evol_df = df_plot.groupby('Mes_Nombre')[cols_tiempos].mean().reindex(MESES_ORDEN).dropna(how='all').reset_index()
                fig = px.bar(evol_df, x='Mes_Nombre', y=cols_tiempos, barmode='group',
                             title=f"Evolución Mensual - Sujeto {s_sel}", text_auto='.1f')
            else:
                # Resumen de un solo mes
                res_df = df_plot[cols_tiempos].mean().reset_index()
                res_df.columns = ['Etapa', 'Días']
                fig = px.bar(res_df, x='Etapa', y='Días', color='Etapa', text_auto='.2f')

            st.plotly_chart(fig, use_container_width=True)

            # LEYENDA DE ADVERTENCIA
            hay_negativos = (df_f[cols_tiempos] < 0).any().any()
            if hay_negativos:
                st.error("⚠️ **Nota:** Los días promedios son aproximados por fechas distantes (registros en rojo).")

            # INDICADORES NUMÉRICOS (Botonera)
            st.write("### Indicadores de Tiempo (Días Promedio)")
            m1, m2, m3, m4 = st.columns(4)
            
            def mostrar_metrica(cont, label, col_n):
                # Calculamos el promedio ignorando negativos (>=0)
                datos_validos = df_f[col_n][df_f[col_n] >= 0]
                val = datos_validos.mean()
                cont.metric(label, f"{val:.2f} d" if pd.notna(val) else "N/A")

            mostrar_metrica(m1, "Detección", "Detección")
            mostrar_metrica(m2, "Cultivo", "Cultivo")
            mostrar_metrica(m3, "Entrega", "Entrega")
            mostrar_metrica(m4, "Captura", "Captura")
            
        else:
            st.warning("⚠️ No hay datos para mostrar. Selecciona al menos un mes.")

        # --- DESCARGA EXCEL ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p.iloc[:, :12].copy()
            df_export.to_excel(writer, index=False, sheet_name='Reporte')
            workbook, worksheet = writer.book, writer.sheets['Reporte']
            max_r = len(df_export)
            
            # Tabla oficial de Excel
            worksheet.add_table(0, 0, max_r, 11, {
                'columns': [{'header': c} for c in df_export.columns],
                'style': 'Table Style Medium 9'
            })
            
            # Fila de Totales
            fmt_v = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'num_format': '0.00', 'border': 1})
            worksheet.write(max_r + 1, 7, "PROMEDIO TOTAL", fmt_v)
            for i, col_let in zip(range(8, 12), ['I', 'J', 'K', 'L']):
                formula = f"=AVERAGEIF({col_let}2:{col_let}{max_r + 1}, \">=0\")"
                worksheet.write_formula(max_r + 1, i, formula, fmt_v)
            
            worksheet.set_column(0, 11, 20)

        st.download_button("📥 Descargar Reporte Final (A-L)", output.getvalue(), "Reporte_IAAS.xlsx")

        with st.expander("👀 Ver Tabla de Datos"):
            df_vis = df_p.iloc[:, :12].copy()
            for i in [0, 1, 3, 4, 6]:
                df_vis.iloc[:, i] = df_vis.iloc[:, i].dt.strftime('%d/%m/%Y').astype(str).replace('nan', '-')
            st.dataframe(df_vis.style.map(color_negativo_rojo, subset=df_vis.columns[8:12]), use_container_width=True)

else:
    st.info("👋 Por favor, sube el archivo Excel para activar el panel de estadísticas.")
