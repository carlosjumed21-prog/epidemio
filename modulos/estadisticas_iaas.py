import streamlit as st
import pandas as pd
import io
import plotly.express as px

# --- 1. CONFIGURACIÓN Y CONSTANTES ---
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

METRICAS_LISTA = ["Detección", "Cultivo", "Entrega", "Captura", "Proceso"]

def color_negativo_rojo(val):
    if isinstance(val, (int, float)) and val < 0:
        return 'color: red; font-weight: bold'
    return 'color: black'

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Vigilancia IAAS CMN 20", layout="wide")
st.title("🏥 Vigilancia IAAS - CMN 20 de Noviembre")
st.markdown("---")

# --- 3. CARGA DE ARCHIVO ---
archivo_iaas = st.file_uploader("📂 1. Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    if 'df_base' not in st.session_state:
        # Lectura inicial
        df_raw = pd.read_excel(archivo_iaas)
        
        # Selección de columnas base (A-H)
        df_base = df_raw.iloc[:, :8].copy()
        df_base.columns = ETIQUETAS_FINALES[:8]
        
        # --- CORRECCIÓN DE FILAS VACÍAS (ELIMINA LAS 150 FILAS FANTASMA) ---
        # Borramos filas donde la fecha de detección o el Sujeto (MODIFICACION) sean nulos
        df_base = df_base.dropna(subset=["Fecha de deteccion", "MODIFICACION"], how='any')
        
        # Limpieza de la columna MODIFICACION para asegurar que sean números limpios
        df_base["MODIFICACION"] = pd.to_numeric(df_base["MODIFICACION"], errors='coerce')
        df_base = df_base.dropna(subset=["MODIFICACION"])
        
        st.session_state['df_base'] = df_base.reset_index(drop=True)

    if st.button("🚀 Procesar y Limpiar Datos"):
        try:
            df = st.session_state['df_base'].copy()
            cols_f = ["Fecha de deteccion", "Fecha de Inicio", "Fecha de toma del cultivo", 
                      "FECHA DE ENTREGA", "Fecha de captura en RHOVE", "MES 1"]
            
            for col in cols_f:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

            # --- CÁLCULOS DE ETAPAS ---
            df["Detección"] = (df["Fecha de deteccion"] - df["Fecha de Inicio"]).dt.days + 1
            df["Cultivo"] = (df["Fecha de toma del cultivo"] - df["Fecha de Inicio"]).dt.days
            df["Entrega"] = (df["FECHA DE ENTREGA"] - df["Fecha de deteccion"]).dt.days + 1
            df["Captura"] = (df["Fecha de captura en RHOVE"] - df["FECHA DE ENTREGA"]).dt.days + 1
            df["Proceso"] = (df["FECHA DE ENTREGA"] - df["Fecha de Inicio"]).dt.days + 1

            df['Mes_Nombre'] = df["MES 1"].dt.month.map(MES_NUM_MAP)
            st.session_state['df_procesado'] = df
            st.success(f"✅ ¡Listo! Se procesaron {len(df)} registros reales.")
        except Exception as e:
            st.error(f"❌ Error en el procesamiento: {e}")

    # --- 4. DASHBOARD INTERACTIVO ---
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']

        st.subheader("🔍 Filtros Personalizados")
        c1, c2, c3 = st.columns([1, 1, 2])
        
        with c1:
            sujetos_lista = sorted([int(s) for s in df_p["MODIFICACION"].unique() if pd.notna(s)])
            opciones_s = ["Todos"] + [str(s) for s in sujetos_lista]
            s_sel = st.selectbox("Sujeto (MODIFICACION)", opciones_s)
        
        with c2:
            st.write("Seleccionar Meses:")
            check_t = st.checkbox("Todo el año", value=True)
            meses_sel = MESES_ORDEN if check_t else st.multiselect("Meses", MESES_ORDEN, default=[])

        with c3:
            # --- NUEVA FUNCIONALIDAD: SELECTOR DE MÉTRICAS ---
            metricas_visibles = st.multiselect(
                "Métricas a visualizar:",
                options=METRICAS_LISTA,
                default=METRICAS_LISTA
            )

        # Aplicar filtros a los datos
        mask = pd.Series([True] * len(df_p))
        if s_sel != "Todos":
            mask = mask & (df_p["MODIFICACION"].astype(int).astype(str) == s_sel)
        if meses_sel:
            mask = mask & (df_p['Mes_Nombre'].isin(meses_sel))
        
        df_f = df_p[mask].copy()

        if not df_f.empty and metricas_visibles:
            st.divider()
            
            # Preparar datos para gráfica (limpiar negativos solo para visualización)
            df_plot = df_f.copy()
            for c in metricas_visibles:
                df_plot[c] = df_plot[c].apply(lambda x: x if x >= 0 else 0)

            # Gráfica Dinámica
            if s_sel == "Todos":
                comp_df = df_plot.groupby("MODIFICACION")[metricas_visibles].mean().reset_index()
                comp_df["MODIFICACION"] = comp_df["MODIFICACION"].astype(int).astype(str)
                fig = px.bar(comp_df, x="MODIFICACION", y=metricas_visibles, barmode='group',
                             title="📊 Comparativa por Sujeto",
                             labels={'MODIFICACION': 'ID Sujeto', 'value': 'Días', 'variable': 'Etapa'},
                             text_auto='.1f', color_discrete_sequence=px.colors.qualitative.Bold)
            else:
                evol_df = df_plot.groupby('Mes_Nombre')[metricas_visibles].mean().reindex(MESES_ORDEN).dropna(how='all').reset_index()
                fig = px.bar(evol_df, x='Mes_Nombre', y=metricas_visibles, barmode='group',
                             title=f"📈 Evolución Mensual: Sujeto {s_sel}",
                             labels={'Mes_Nombre': 'Meses', 'value': 'Días', 'variable': 'Etapa'},
                             text_auto='.1f', color_discrete_sequence=px.colors.qualitative.Safe)

            st.plotly_chart(fig, use_container_width=True)

            # Indicadores (Métricas) Dinámicos
            st.write("### Promedios Seleccionados")
            m_cols = st.columns(len(metricas_visibles))
            for i, met in enumerate(metricas_visibles):
                val_met = df_f[met][df_f[met] >= 0].mean()
                m_cols[i].metric(met, f"{val_met:.2f} d" if pd.notna(val_met) else "N/A")
        
        elif not metricas_visibles:
            st.warning("Selecciona al menos una métrica para mostrar la gráfica.")
        else:
            st.warning("⚠️ No hay datos para los filtros seleccionados.")

        # --- 5. EXCEL DE SALIDA CORREGIDO ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p[ETIQUETAS_FINALES].copy()
            df_export.to_excel(writer, index=False, sheet_name='Reporte')
            
            workbook, worksheet = writer.book, writer.sheets['Reporte']
            max_r = len(df_export) # Aquí ya solo contará los 90 datos reales
            
            # Tabla de Excel
            column_settings = [{'header': col} for col in ETIQUETAS_FINALES]
            worksheet.add_table(0, 0, max_r, 12, {'columns': column_settings, 'style': 'Table Style Medium 9'})
            
            # Formatos
            fmt_v = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'num_format': '0.00', 'border': 1})
            fmt_r = workbook.add_format({'font_color': 'red', 'bold': True})

            # Columnas auxiliares para promedios filtrados (SI valor >= 0)
            letras_base = ['I', 'J', 'K', 'L', 'M']
            for r_idx in range(1, max_r + 1):
                for i, col_let in enumerate(letras_base):
                    formula = f"=IF({col_let}{r_idx+1}>=0, {col_let}{r_idx+1}, \"\")"
                    worksheet.write_formula(r_idx, 13 + i, formula)

            worksheet.set_column(13, 17, None, None, {'hidden': True})
            
            # Fila de Promedio Final
            fila_promedio = max_r + 1
            worksheet.write(fila_promedio, 7, "PROM. FILTRADO", fmt_v)
            
            letras_aux = ['N', 'O', 'P', 'Q', 'R']
            for i, col_aux in zip(range(8, 13), letras_aux):
                formula_sub = f"=SUBTOTAL(101, {col_aux}2:{col_aux}{max_r + 1})"
                worksheet.write_formula(fila_promedio, i, formula_sub, fmt_v)

            # Formato condicional para errores (negativos)
            worksheet.conditional_format(1, 8, max_r, 12, {'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_r})
            worksheet.set_column(0, 12, 20)

        st.download_button("📥 Descargar Reporte Limpio (Excel)", output.getvalue(), "Reporte_IAAS_Final.xlsx")

        # --- 6. VISTA PREVIA ---
        with st.expander("👀 Ver Tabla de Datos Procesados"):
            df_vis = df_p[ETIQUETAS_FINALES].copy()
            for col in ETIQUETAS_FINALES[:8]:
                if "Fecha" in col or "FECHA" in col or "MES" in col:
                    df_vis[col] = df_vis[col].dt.strftime('%d/%m/%Y').replace('nan', '-')
            
            st.dataframe(
                df_vis.style.map(color_negativo_rojo, subset=METRICAS_LISTA)
                .format(precision=0, subset=METRICAS_LISTA), 
                use_container_width=True
            )
