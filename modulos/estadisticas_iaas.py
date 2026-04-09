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

st.title("📊 Estadísticas IAAS - Reporte Avanzado")
st.markdown("---")

archivo_iaas = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    if 'df_base' not in st.session_state:
        df_raw = pd.read_excel(archivo_iaas)
        # Delimitar a las 121 filas reales (basado en contenido en A-H)
        df_limpio = df_raw.dropna(how='all', subset=df_raw.columns[:8]).reset_index(drop=True)
        st.session_state['df_base'] = df_limpio

    if st.button("🚀 Generar Reporte con Totales"):
        try:
            df = st.session_state['df_base'].iloc[:, :8].copy()
            
            # Convertir fechas
            idx_f = [0, 1, 3, 4, 6]
            for i in idx_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # --- CÁLCULOS (I, J, K, L) ---
            df.insert(8, "Tiempo promedio de detección en días", (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1)
            df.insert(9, "Tiempo promedio de toma de cultivo en días", (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1)
            df.insert(10, "Tiempo promedio de entrega en días", (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1)
            df.insert(11, "Tiempo promedio de captura en días", (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1)

            # Mes invisible para filtros
            def get_mes(v):
                v = str(v).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df['Mes_Invisible'] = df.iloc[:, 7].apply(get_mes)

            st.session_state['df_procesado'] = df
            st.success(f"✅ Análisis completado para {len(df)} registros.")
            
        except Exception as e:
            st.error(f"❌ Error: {e}")

    # --- RESULTADOS Y DESCARGA ---
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']

        # 1. GENERAR EXCEL CON FILA DE TOTALES Y FÓRMULAS
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p.iloc[:, :12]
            df_export.to_excel(writer, index=False, sheet_name='Reporte_IAAS')
            
            workbook  = writer.book
            worksheet = writer.sheets['Reporte_IAAS']
            
            # Definir dimensiones
            (max_row, max_col) = df_export.shape # max_row será 121 datos + 1 encabezado = 122
            
            # Formatos
            fmt_rojo = workbook.add_format({'font_color': 'red', 'bold': True})
            fmt_totales_label = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D9EAD3', 'border': 1})
            fmt_totales_val = workbook.add_format({'bold': True, 'num_format': '0.00', 'bg_color': '#D9EAD3', 'border': 1})

            # Crear Tabla de Excel
            worksheet.add_table(0, 0, max_row - 1, max_col - 1, {
                'columns': [{'header': c} for c in df_export.columns],
                'style': 'Table Style Medium 9'
            })

            # --- AGREGAR FILA DE TOTALES (Fila 123 en Excel) ---
            fila_total = max_row 
            # Agrupar A-H (Merge)
            worksheet.merge_range(fila_total, 0, fila_total, 7, "PROMEDIO TOTAL (Excluye negativos)", fmt_totales_label)
            
            # Aplicar AVERAGEIF en I, J, K, L
            # Letras de columnas en Excel: I=I, J=J, K=K, L=L
            for col_idx, col_letter in zip(range(8, 12), ['I', 'J', 'K', 'L']):
                # Rango de datos va desde fila 2 hasta fila 122 (en Excel es 1-indexed)
                rango = f"{col_letter}2:{col_letter}{max_row}"
                formula = f"=AVERAGEIF({rango}, \">=0\")"
                worksheet.write_formula(fila_total, col_idx, formula, fmt_totales_val)

            # Formato condicional rojo para negativos en el cuerpo
            worksheet.conditional_format(1, 8, max_row - 1, 11, {
                'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_rojo
            })
            
            worksheet.set_column(0, 11, 22)

        st.download_button(
            label="📥 Descargar Excel con Totales y Fórmulas",
            data=output.getvalue(),
            file_name="Reporte_IAAS_Final_Con_Totales.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 2. VISTA PREVIA
        st.subheader("👀 Vista Previa")
        df_visual = df_p.iloc[:, :12].copy()
        idx_fechas = [0, 1, 3, 4, 6]
        for i in idx_fechas:
            df_visual.iloc[:, i] = df_visual.iloc[:, i].dt.strftime('%d/%m/%Y').fillna("-")

        st.dataframe(
            df_visual.style.map(color_negativo_rojo, subset=df_visual.columns[8:12]), 
            use_container_width=True
        )

        # 3. FILTROS Y MÉTRICAS CON NOTACIÓN DE ADVERTENCIA
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            sujetos = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            s_sel = st.selectbox("Seleccionar Sujeto (Col F)", sujetos)
        with c2:
            m_sel = st.selectbox("Seleccionar Mes", ["Anual"] + list(MESES_MAP.values()))

        mask = (df_p.iloc[:, 5] == s_sel)
        if m_sel != "Anual":
            mask = mask & (df_p['Mes_Invisible'] == m_sel)
        
        df_f = df_p[mask]

        # --- LÓGICA DE ADVERTENCIA ---
        # Verificamos si hay algún valor negativo en las columnas I, J, K o L para este sujeto
        hay_negativos = (df_f.iloc[:, 8:12] < 0).any().any()
        
        st.write(f"### Resultados: Sujeto {s_sel}")
        
        if hay_negativos:
            st.warning("⚠️ **Nota:** Los días promedios son aproximados por fechas distantes (se detectaron registros inconsistentes).")

        m1, m2, m3, m4 = st.columns(4)
        def render_btn(cont, label, col_idx):
            if cont.button(label):
                if not df_f.empty:
                    # Al igual que en Excel, aquí en la app también excluimos negativos para el promedio
                    datos_validos = df_f.iloc[:, col_idx][df_f.iloc[:, col_idx] >= 0]
                    if not datos_validos.empty:
                        val = datos_validos.mean()
                        cont.metric(label, f"{val:.2f} d")
                    else:
                        cont.error("Datos inválidos")
                else: cont.warning("N/A")

        render_btn(m1, "Detección", 8)
        render_btn(m2, "Cultivo", 9)
        render_btn(m3, "Entrega", 10)
        render_btn(m4, "Captura", 11)

else:
    st.warning("👋 Sube tu archivo para generar el reporte con indicadores y totales.")
