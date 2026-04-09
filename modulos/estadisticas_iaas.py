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
        # Delimitar a 121 filas reales (basado en A-H)
        st.session_state['df_base'] = df_raw.dropna(how='all', subset=df_raw.columns[:8]).reset_index(drop=True)

    if st.button("🚀 Generar Estadísticas y Gráficas"):
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

            # Crear columna de Mes
            def get_mes(v):
                v = str(v).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df['Mes_Nombre'] = df.iloc[:, 7].apply(get_mes)

            st.session_state['df_procesado'] = df
            st.success("✅ Datos procesados correctamente.")
            
        except Exception as e:
            st.error(f"❌ Error en cálculos: {e}")

    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        cols_tiempos = ["Detección", "Cultivo", "Entrega", "Captura"]

        # --- FILTROS (Casillas y Sujetos) ---
        st.subheader("🔍 Filtros de Análisis")
        c1, c2 = st.columns([1, 2])
        
        with c1:
            sujetos_reales = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            opciones_sujeto = ["Todos"] + [str(int(s)) if isinstance(s, float) else str(s) for s in sujetos_reales]
            s_sel = st.selectbox("Sujeto (Col F)", opciones_sujeto)
        
        with c2:
            st.write("Seleccionar Meses:")
            todos_meses = st.checkbox("Seleccionar todos los meses", value=True)
            if todos_meses:
                meses_sel = st.multiselect("Meses", MESES_ORDEN, default=MESES_ORDEN, disabled=True)
            else:
                meses_sel = st.multiselect("Meses", MESES_ORDEN)

        # Aplicar Filtro
        mask = pd.Series([True] * len(df_p))
        if s_sel != "Todos":
            mask = mask & (df_p.iloc[:, 5].astype(str) == s_sel)
        if meses_sel:
            mask = mask & (df_p['Mes_Nombre'].isin(meses_sel))
        else:
            mask = pd.Series([False] * len(df_p))
        
        df_f = df_p[mask]

        # --- SECCIÓN DE GRÁFICAS ---
        st.divider()
        if not df_f.empty:
            df_plot = df_f.copy()
            for c in cols_tiempos:
                df_plot[c] = df_plot[c].apply(lambda x: x if x >= 0 else 0)

            # CASO 1: FILTRO "TODOS" LOS SUJETOS
            if s_sel == "Todos":
                st.subheader("📈 Comparativa: Días por Sujeto")
                # Agrupamos por Sujeto (Eje X) y Tiempos (Barras)
                comp_df = df_plot.groupby(df_p.columns[5])[cols_tiempos].mean().reset_index()
                comp_df[df_p.columns[5]] = comp_df[df_p.columns[5]].astype(str)
                
                fig = px.bar(comp_df, x=df_p.columns[5], y=cols_tiempos, 
                             barmode='group', text_auto='.1f',
                             labels={df_p.columns[5]: 'Sujetos', 'value': 'Días', 'variable': 'Etapa'},
                             title="Desempeño Global por Sujeto",
                             color_discrete_sequence=px.colors.qualitative.Vivid)
                fig.update_xaxes(type='category', categoryorder='array', categoryarray=opciones_sujeto[1:])

            # CASO 2: UN SUJETO / ANUAL (O VARIOS MESES SELECCIONADOS)
            elif s_sel != "Todos" and len(meses_sel) > 1:
                st.subheader(f"📈 Evolución Mensual: Sujeto {s_sel}")
                # Agrupamos por Mes (Eje X) y Tiempos (Barras)
                evol_df = df_plot.groupby('Mes_Nombre')[cols_tiempos].mean().reindex(MESES_ORDEN).dropna(how='all').reset_index()
                
                fig = px.bar(evol_df, x='Mes_Nombre', y=cols_tiempos, 
                             barmode='group', text_auto='.1f',
                             labels={'Mes_Nombre': 'Meses', 'value': 'Días', 'variable': 'Etapa'},
                             title=f"Evolución de Tiempos - Sujeto {s_sel}",
                             color_discrete_sequence=px.colors.qualitative.Safe)
            
            # CASO 3: UN SUJETO / UN SOLO MES
            else:
                st.subheader(f"📊 Resumen: Sujeto {s_sel}")
                res_df = df_plot[cols_tiempos].mean().reset_index()
                res_df.columns = ['Etapa', 'Días']
                fig = px.bar(res_df, x='Etapa', y='Días', color='Etapa', text_auto='.2f')

            st.plotly_chart(fig, use_container_width=True)
            
            # Alerta de inconsistencias
            if (df_f[cols_tiempos] < 0).any().any():
                st.warning("⚠️ **Nota:** Los días promedios son aproximados por fechas distantes.")

        # --- EXCEL DE SALIDA (AQUÍ CORREGIMOS EL ERROR DE ARCHIVO) ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p.iloc[:, :12].copy()
            df_export.to_excel(writer, index=False, sheet_name='Reporte')
            
            workbook = writer.book
            worksheet = writer.sheets['Reporte']
            
            # max_data_row es el índice de la última fila de datos (sin contar el promedio)
            max_data_row = len(df_export) 
            
            # Crear la Tabla de Excel (Rango exacto A1:L[max_data_row+1])
            worksheet.add_table(0, 0, max_data_row, 11, {
                'columns': [{'header': c} for c in df_export.columns],
                'style': 'Table Style Medium 9'
            })
            
            # Escribir la fila de promedios JUSTO DEBAJO de la tabla
            fmt_v = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'num_format': '0.00', 'border': 1})
            worksheet.write(max_data_row + 1, 7, "PROMEDIO TOTAL", fmt_v)
            
            for i, col_let in zip(range(8, 12), ['I', 'J', 'K', 'L']):
                # Rango de datos: Fila 2 (index 1) hasta la última fila de datos
                formula = f"=AVERAGEIF({col_let}2:{col_let}{max_data_row + 1}, \">=0\")"
                worksheet.write_formula(max_data_row + 1, i, formula, fmt_v)
            
            worksheet.set_column(0, 11, 20)

        st.download_button("📥 Descargar Reporte Final (A-L)", output.getvalue(), "Reporte_IAAS_Final.xlsx")

        # Vista Previa
        with st.expander("👀 Ver Tabla de Datos"):
            df_vis = df_p.iloc[:, :12].copy()
            for i in [0, 1, 3, 4, 6]:
                df_vis.iloc[:, i] = df_vis.iloc[:, i].dt.strftime('%d/%m/%Y').astype(str).replace('nan', '-')
            st.dataframe(df_vis.style.map(color_negativo_rojo, subset=df_vis.columns[8:12]), use_container_width=True)
