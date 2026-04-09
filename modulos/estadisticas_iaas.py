import streamlit as st
import pandas as pd
import io

# --- 1. CONFIGURACIÓN DE MESES ---
MESES_MAP = {
    'ene': 'enero', 'feb': 'febrero', 'mar': 'marzo', 'abr': 'abril',
    'may': 'mayo', 'jun': 'junio', 'jul': 'julio', 'ago': 'agosto',
    'sep': 'septiembre', 'oct': 'octubre', 'nov': 'noviembre', 'dic': 'diciembre'
}

def color_negativo_rojo(val):
    """Estilo para la vista previa web"""
    if isinstance(val, (int, float)) and val < 0:
        return 'color: red; font-weight: bold'
    return 'color: black'

st.title("📊 Estadísticas IAAS - CMN 20 de Noviembre")
st.markdown("---")

archivo_iaas = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    if 'df_base' not in st.session_state:
        df_raw = pd.read_excel(archivo_iaas)
        # Delimitar estrictamente a filas con datos en A-H (las 121 reales)
        df_limpio = df_raw.dropna(how='all', subset=df_raw.columns[:8]).reset_index(drop=True)
        st.session_state['df_base'] = df_limpio

    if st.button("🚀 Generar Reporte"):
        try:
            df = st.session_state['df_base'].iloc[:, :8].copy()
            
            # Convertir fechas (A, B, D, E, G)
            idx_f = [0, 1, 3, 4, 6]
            for i in idx_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # --- CÁLCULOS (Columnas I, J, K, L) ---
            df.insert(8, "Tiempo promedio de detección en días", (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1)
            df.insert(9, "Tiempo promedio de toma de cultivo en días", (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1)
            df.insert(10, "Tiempo promedio de entrega en días", (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1)
            df.insert(11, "Tiempo promedio de captura en días", (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1)

            # Mes invisible para filtros internos
            def get_mes(v):
                v = str(v).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df['Mes_Invisible'] = df.iloc[:, 7].apply(get_mes)

            st.session_state['df_procesado'] = df
            st.success(f"✅ Procesado: {len(df)} registros detectados.")
            
        except Exception as e:
            st.error(f"❌ Error en cálculos: {e}")

    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']

        # --- 1. EXCEL DE SALIDA (A-L + Totales) ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p.iloc[:, :12].copy()
            df_export.to_excel(writer, index=False, sheet_name='Reporte_IAAS')
            
            workbook  = writer.book
            worksheet = writer.sheets['Reporte_IAAS']
            (max_row, max_col) = df_export.shape
            
            # Formatos Excel
            fmt_rojo = workbook.add_format({'font_color': 'red', 'bold': True})
            fmt_total_lbl = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'border': 1, 'align': 'center'})
            fmt_total_val = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'border': 1, 'num_format': '0.00'})

            # Crear Tabla de Excel
            worksheet.add_table(0, 0, max_row - 1, max_col - 1, {
                'columns': [{'header': c} for c in df_export.columns],
                'style': 'Table Style Medium 9'
            })

            # Fila de Totales (Promedio que ignora negativos)
            worksheet.merge_range(max_row, 0, max_row, 7, "PROMEDIO TOTAL (Excluye inconsistencias)", fmt_total_lbl)
            for i, col_let in zip(range(8, 12), ['I', 'J', 'K', 'L']):
                rango = f"{col_let}2:{col_let}{max_row}"
                # AVERAGEIF en Excel ignora los menores a 0
                worksheet.write_formula(max_row, i, f"=AVERAGEIF({rango}, \">=0\")", fmt_total_val)

            # Formato condicional Rojo para negativos
            worksheet.conditional_format(1, 8, max_row-1, 11, {
                'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_rojo
            })
            worksheet.set_column(0, 11, 20)

        st.download_button("📥 Descargar Reporte Final (A-L)", output.getvalue(), "Reporte_IAAS_Totales.xlsx")

        # --- 2. VISTA PREVIA (Aquí es donde ocurría el TypeError) ---
        st.subheader(f"👀 Vista Previa ({len(df_p)} filas)")
        
        # Solución al TypeError: Convertimos a string ANTES de usar .dt.strftime
        df_visual = df_p.iloc[:, :12].copy()
        idx_fechas = [0, 1, 3, 4, 6]
        
        for i in idx_fechas:
            col_name = df_visual.columns[i]
            # Convertimos la columna a tipo "objeto/texto" para que acepte el formato
            df_visual[col_name] = df_visual[col_name].dt.strftime('%d/%m/%Y').astype(str).replace('nan', '-')

        st.dataframe(
            df_visual.style.map(color_negativo_rojo, subset=df_visual.columns[8:12]), 
            use_container_width=True
        )

        # --- 3. FILTROS Y NOTACIÓN DE ADVERTENCIA ---
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            sujetos = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            s_sel = st.selectbox("Persona (Col F)", sujetos)
        with c2:
            m_sel = st.selectbox("Mes", ["Anual"] + list(MESES_MAP.values()))

        mask = (df_p.iloc[:, 5] == s_sel)
        if m_sel != "Anual":
            mask = mask & (df_p['Mes_Invisible'] == m_sel)
        df_f = df_p[mask]

        # Alerta si el sujeto tiene datos negativos (rojos)
        tiene_rojos = (df_f.iloc[:, 8:12] < 0).any().any()
        
        st.write(f"### Análisis: Sujeto {s_sel}")
        if tiene_rojos:
            st.warning("⚠️ **Nota:** Los días promedios son aproximados por fechas distantes.")

        m1, m2, m3, m4 = st.columns(4)
        def metric_btn(cont, label, col_idx):
            if cont.button(label):
                if not df_f.empty:
                    # Promedio real ignorando negativos para no sesgar
                    validos = df_f.iloc[:, col_idx][df_f.iloc[:, col_idx] >= 0]
                    val = validos.mean() if not validos.empty else 0
                    cont.metric("Días", f"{val:.2f}")
                else: cont.warning("N/A")

        metric_btn(m1, "Detección", 8); metric_btn(m2, "Cultivo", 9)
        metric_btn(m3, "Entrega", 10); metric_btn(m4, "Captura", 11)

else:
    st.warning("👋 Sube el archivo para iniciar.")
