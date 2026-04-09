import streamlit as st
import pandas as pd
import io

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

st.title("📊 Análisis IAAS - Reporte de Tiempos y Procesos")
st.markdown("---")

archivo_iaas = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    if 'df_base' not in st.session_state:
        df_raw = pd.read_excel(archivo_iaas)
        # Delimitar a las 121 filas reales (A-H)
        st.session_state['df_base'] = df_raw.dropna(how='all', subset=df_raw.columns[:8]).reset_index(drop=True)

    if st.button("🚀 Procesar Datos"):
        try:
            df = st.session_state['df_base'].iloc[:, :8].copy()
            # Convertir fechas (A=0, B=1, D=3, E=4, G=6)
            idx_f = [0, 1, 3, 4, 6]
            for i in idx_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # --- CÁLCULOS (Columnas I, J, K, L) ---
            df["Detección"] = (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1
            df["Cultivo"] = (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1
            df["Entrega"] = (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1
            df["Captura"] = (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1
            
            # --- NUEVA COLUMNA M (PROCESO: E - B + 1) ---
            df["PROCESO"] = (df.iloc[:, 4] - df.iloc[:, 1]).dt.days + 1

            # Mes invisible para filtros internos
            def get_mes(v):
                v = str(v).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df['Mes_Nombre'] = df.iloc[:, 7].apply(get_mes)

            st.session_state['df_procesado'] = df
            st.success("✅ Datos procesados con éxito.")
        except Exception as e:
            st.error(f"❌ Error al procesar: {e}")

    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']
        # Lista de columnas de tiempos (ahora son 5)
        cols_tiempos = ["Detección", "Cultivo", "Entrega", "Captura", "PROCESO"]

        # --- FILTROS (SUJETOS Y MESES) ---
        st.subheader("🔍 Filtros de Visualización")
        c1, c2 = st.columns([1, 2])
        
        with c1:
            sujetos_reales = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            opciones_sujeto = ["Todos"] + [str(int(s)) if isinstance(s, float) else str(s) for s in sujetos_reales]
            s_sel = st.selectbox("Seleccionar Sujeto (Col F)", opciones_sujeto)
        
        with c2:
            st.write("Seleccionar Meses:")
            check_todos = st.checkbox("Seleccionar todo el año", value=True)
            if check_todos:
                meses_sel = st.multiselect("Meses", MESES_ORDEN, default=MESES_ORDEN, disabled=True)
            else:
                meses_sel = st.multiselect("Meses", MESES_ORDEN, default=[])

        # Filtrado dinámico
        mask = pd.Series([True] * len(df_p))
        if s_sel != "Todos": mask = mask & (df_p.iloc[:, 5].astype(str) == s_sel)
        if meses_sel: mask = mask & (df_p['Mes_Nombre'].isin(meses_sel))
        else: mask = pd.Series([False] * len(df_p))
        
        df_f = df_p[mask]

        # --- INDICADORES (Métricas) ---
        if not df_f.empty:
            # Leyenda de Advertencia
            if (df_f[cols_tiempos] < 0).any().any():
                st.error("⚠️ **Nota:** Los días promedios son aproximados por fechas distantes (registros en rojo detectados).")

            st.write(f"### Indicadores Sujeto: {s_sel}")
            m1, m2, m3, m4, m5 = st.columns(5)
            def render(cont, label, col):
                val = df_f[col][df_f[col] >= 0].mean()
                cont.metric(label, f"{val:.2f} d" if pd.notna(val) else "N/A")
            
            render(m1, "Detección", "Detección")
            render(m2, "Cultivo", "Cultivo")
            render(m3, "Entrega", "Entrega")
            render(m4, "Captura", "Captura")
            render(m5, "PROCESO", "PROCESO")

        # --- EXCEL DINÁMICO (A-M + Columnas Auxiliares N-R) ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            # Exportamos hasta la columna M (0 al 12)
            df_export = df_p.iloc[:, :13].copy()
            df_export.to_excel(writer, index=False, sheet_name='Reporte')
            
            workbook, worksheet = writer.book, writer.sheets['Reporte']
            max_r = len(df_export)

            # Crear Tabla de Excel
            worksheet.add_table(0, 0, max_r, 12, {
                'columns': [{'header': c} for c in df_export.columns], 
                'style': 'Table Style Medium 9'
            })
            
            fmt_v = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'num_format': '0.00', 'border': 1})
            fmt_rojo = workbook.add_format({'font_color': 'red', 'bold': True})

            # TRUCO: Columnas auxiliares ocultas (N, O, P, Q, R) para ignorar negativos en SUBTOTALES
            # Empiezan en el índice 13
            letras_calculo = ['I', 'J', 'K', 'L', 'M']
            for r_idx in range(1, max_r + 1):
                for i, col_let in enumerate(letras_calculo):
                    # Fórmula: SI(Celda>=0, Celda, "")
                    formula = f"=IF({col_let}{r_idx+1}>=0, {col_let}{r_idx+1}, \"\")"
                    worksheet.write_formula(r_idx, 13 + i, formula)

            # Ocultar las columnas auxiliares
            worksheet.set_column(13, 17, None, None, {'hidden': True})

            # FILA DE TOTALES DINÁMICA (SUBTOTAL 101 ignora filas filtradas)
            worksheet.write(max_r + 1, 7, "PROMEDIO FILTRADO", fmt_v)
            letras_aux = ['N', 'O', 'P', 'Q', 'R']
            for i, col_aux in enumerate(letras_aux):
                formula = f"=SUBTOTAL(101, {col_aux}2:{col_aux}{max_r + 1})"
                worksheet.write_formula(max_r + 1, 8 + i, formula, fmt_v)

            # Formato condicional rojo para negativos en I, J, K, L, M
            worksheet.conditional_format(1, 8, max_r, 12, {
                'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_rojo
            })
            worksheet.set_column(0, 12, 20)

        st.download_button("📥 Descargar Reporte Final (A-M)", output.getvalue(), "Reporte_IAAS_Proceso.xlsx")

        with st.expander("👀 Ver Tabla de Datos"):
            df_vis = df_p.iloc[:, :13].copy()
            for i in [0, 1, 3, 4, 6]:
                df_vis.iloc[:, i] = df_vis.iloc[:, i].dt.strftime('%d/%m/%Y').astype(str).replace('nan', '-')
            st.dataframe(df_vis.style.map(color_negativo_rojo, subset=df_vis.columns[8:13]), use_container_width=True)

else:
    st.info("👋 Por favor, sube el archivo Excel para iniciar.")
