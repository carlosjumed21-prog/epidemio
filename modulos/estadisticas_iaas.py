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

st.title("📊 Estadísticas IAAS - Reporte Final")
st.info("Formato de Tabla de Excel activado. Se respetan las 121 filas originales.")

archivo_iaas = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if archivo_iaas:
    # Carga inicial sin limpieza agresiva para no perder filas
    if 'df_base' not in st.session_state:
        df_temp = pd.read_excel(archivo_iaas)
        # Solo eliminamos filas si están COMPLETAMENTE vacías
        st.session_state['df_base'] = df_temp.dropna(how='all').reset_index(drop=True)

    if st.button("🚀 Generar Estadísticas"):
        try:
            # Tomamos de la A a la H
            df = st.session_state['df_base'].iloc[:, :8].copy()
            
            # Convertir fechas (A, B, D, E, G)
            indices_f = [0, 1, 3, 4, 6]
            for i in indices_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # --- CÁLCULOS I, J, K, L ---
            # I (8) = A - B + 1 | J (9) = B - D + 1 | K (10) = E - A + 1 | L (11) = G - E + 1
            df.insert(8, "Tiempo promedio de detección en días", (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1)
            df.insert(9, "Tiempo promedio de toma de cultivo en días", (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1)
            df.insert(10, "Tiempo promedio de entrega en días", (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1)
            df.insert(11, "Tiempo promedio de captura en días", (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1)

            # Mes invisible para filtros
            def normalizar_mes(valor):
                v = str(valor).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df['Mes_Invisible'] = df.iloc[:, 7].apply(normalizar_mes)

            st.session_state['df_procesado'] = df
            st.success(f"✅ Procesado: {len(df)} filas detectadas.")
            
        except Exception as e:
            st.error(f"❌ Error: {e}")

    # --- RESULTADOS ---
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']

        # --- EXPORTACIÓN COMO TABLA DE EXCEL ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            df_export = df_p.iloc[:, :12]
            df_export.to_excel(writer, index=False, sheet_name='Reporte_IAAS')
            
            workbook  = writer.book
            worksheet = writer.sheets['Reporte_IAAS']
            
            # Definir dimensiones para la Tabla de Excel
            (max_row, max_col) = df_export.shape
            column_settings = [{'header': column} for column in df_export.columns]
            
            # Añadir el objeto "Tabla" (permite filtros automáticos y estilo)
            worksheet.add_table(0, 0, max_row, max_col - 1, {
                'columns': column_settings,
                'style': 'Table Style Medium 9'
            })
            
            # Formato rojo para negativos en I, J, K, L
            fmt_rojo = workbook.add_format({'font_color': 'red', 'bold': True})
            worksheet.conditional_format(1, 8, max_row, 11, {
                'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_rojo
            })
            
            worksheet.set_column(0, 11, 20)

        st.download_button("📥 Descargar Tabla de Excel Final", output.getvalue(), "Reporte_IAAS_Final.xlsx")

        # --- VISTA PREVIA CORREGIDA ---
        st.subheader(f"👀 Vista Previa ({len(df_p)} filas)")
        
        # Formateo visual para la web (sin horas)
        df_visual = df_p.iloc[:, :12].copy()
        idx_f = [0, 1, 3, 4, 6]
        for i in idx_f:
            col_name = df_visual.columns[i]
            df_visual[col_name] = df_visual[col_name].dt.strftime('%d/%m/%Y').fillna("S/D")

        st.dataframe(df_visual.style.map(color_negativo_rojo, subset=df_visual.columns[8:12]), use_container_width=True)

        # --- FILTROS Y BOTONES ---
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            sujetos = sorted([s for s in df_p.iloc[:, 5].unique() if pd.notna(s)])
            sujeto_sel = st.selectbox("Sujeto (Col F)", sujetos)
        with c2:
            mes_sel = st.selectbox("Filtrar por Mes", ["Anual"] + list(MESES_MAP.values()))

        mask = (df_p.iloc[:, 5] == sujeto_sel)
        if mes_sel != "Anual":
            mask = mask & (df_p['Mes_Invisible'] == mes_sel)
        df_f = df_p[mask]

        st.write(f"### Promedios: {sujeto_sel} ({mes_sel})")
        m1, m2, m3, m4 = st.columns(4)
        
        def mostrar(cont, label, col_idx):
            if cont.button(label):
                if not df_f.empty:
                    val = df_f.iloc[:, col_idx].mean()
                    cont.metric("Promedio", f"{val:.2f}")
                else: cont.warning("N/A")

        mostrar(m1, "Detección", 8); mostrar(m2, "Cultivo", 9)
        mostrar(m3, "Entrega", 10); mostrar(m4, "Captura", 11)

else:
    st.warning("👋 Sube el archivo para comenzar el análisis.")
