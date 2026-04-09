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
    """Estilo para resaltar errores de captura en la web"""
    if isinstance(val, (int, float)) and val < 0:
        return 'color: red; font-weight: bold'
    return 'color: black'

st.title("📊 Estadísticas IAAS - Reporte Final")
st.info("Cálculos exactos multianual (Cruza de 2025 a 2026) | Sin Columna M")

archivo_iaas = st.file_uploader("📂 Sube tu archivo Excel (Formato dd/mm/aaaa)", type=["xlsx"])

if archivo_iaas:
    # Carga inicial del dataframe
    if 'df_base' not in st.session_state:
        st.session_state['df_base'] = pd.read_excel(archivo_iaas)

    # BOTÓN DE PROCESAMIENTO
    if st.button("🚀 Generar Estadísticas"):
        try:
            # 1. Tomar solo A-H y limpiar basura a la derecha
            df = st.session_state['df_base'].iloc[:, :8].copy()
            
            # 2. Convertir fechas (A, B, D, E, G) con formato día primero
            # Esto maneja automáticamente los saltos de año (Dic 2025 -> Ene 2026)
            indices_f = [0, 1, 3, 4, 6]
            for i in indices_f:
                df.iloc[:, i] = pd.to_datetime(df.iloc[:, i], dayfirst=True, errors='coerce')

            # --- 3. CÁLCULOS SEGÚN TUS COMANDOS (I, J, K, L) ---
            # I (8) = A - B + 1
            df.insert(8, "Tiempo promedio de detección en días", (df.iloc[:, 0] - df.iloc[:, 1]).dt.days + 1)
            # J (9) = B - D + 1
            df.insert(9, "Tiempo promedio de toma de cultivo en días", (df.iloc[:, 1] - df.iloc[:, 3]).dt.days + 1)
            # K (10) = E - A + 1
            df.insert(10, "Tiempo promedio de entrega en días", (df.iloc[:, 4] - df.iloc[:, 0]).dt.days + 1)
            # L (11) = G - E + 1
            df.insert(11, "Tiempo promedio de captura en días", (df.iloc[:, 6] - df.iloc[:, 4]).dt.days + 1)

            # --- 4. LÓGICA DE MES (Oculta, para filtros) ---
            def normalizar_mes(valor):
                v = str(valor).lower()
                for abr, nombre in MESES_MAP.items():
                    if abr in v: return nombre
                return "Otro"
            df['Mes_Invisible'] = df.iloc[:, 7].apply(normalizar_mes)

            st.session_state['df_procesado'] = df
            st.success("✅ Procesamiento terminado. El cálculo considera el salto de año correctamente.")
            
        except Exception as e:
            st.error(f"❌ Error durante el cálculo: {e}")

    # --- 5. VISUALIZACIÓN Y DESCARGA ---
    if 'df_procesado' in st.session_state:
        df_p = st.session_state['df_procesado']

        # EXCEL DE SALIDA (Llega hasta la columna L)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            # Solo exportamos de la columna 0 (A) a la 11 (L)
            df_export = df_p.iloc[:, :12]
            df_export.to_excel(writer, index=False, sheet_name='Reporte_Epidemio')
            
            workbook = writer.book
            worksheet = writer.sheets['Reporte_Epidemio']
            fmt_rojo = workbook.add_format({'font_color': 'red'})
            
            # Formato condicional para negativos en el archivo Excel
            worksheet.conditional_format(1, 8, 2000, 11, {
                'type': 'cell', 'criteria': '<', 'value': 0, 'format': fmt_rojo
            })
            worksheet.set_column(0, 11, 20)

        st.download_button(
            label="📥 Descargar Reporte Final (A a L)",
            data=output.getvalue(),
            file_name="Analisis_IAAS_CMN20Nov.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # VISTA PREVIA (Sin horas, solo fechas limpias)
        st.subheader("👀 Vista Previa de Resultados")
        
        df_visual = df_p.iloc[:, :12].copy()
        # Formatear columnas de fecha para que no muestren la hora en la web
        idx_fechas_nombres = df_visual.columns[[0, 1, 3, 4, 6]]
        for col in idx_fechas_nombres:
            df_visual[col] = df_visual[col].dt.strftime('%d/%m/%Y')

        # Aplicar el color rojo a las columnas I, J, K, L
        cols_stats = df_visual.columns[8:12]
        st.dataframe(df_visual.style.map(color_negativo_rojo, subset=cols_stats), use_container_width=True)

        # --- 6. FILTROS Y MÉTRICAS ---
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            sujeto_sel = st.selectbox("Sujeto (Col F)", sorted(df_p.iloc[:, 5].unique()))
        with c2:
            mes_sel = st.selectbox("Mes de Análisis", ["Anual"] + list(MESES_MAP.values()))

        mask = (df_p.iloc[:, 5] == sujeto_sel)
        if mes_sel != "Anual":
            mask = mask & (df_p['Mes_Invisible'] == mes_sel)
        
        df_f = df_p[mask]

        st.write(f"### Promedios: Sujeto {sujeto_sel} ({mes_sel})")
        met1, met2, met3, met4 = st.columns(4)
        
        def render_metric(cont, label, col_idx):
            if cont.button(label):
                if not df_f.empty:
                    val = df_f.iloc[:, col_idx].mean()
                    cont.metric("Promedio", f"{val:.2f} días")
                else:
                    cont.warning("N/A")

        render_metric(met1, "Detección", 8)
        render_metric(met2, "Cultivo", 9)
        render_metric(met3, "Entrega", 10)
        render_metric(met4, "Captura", 11)

else:
    st.warning("👋 Por favor, sube el archivo Excel para iniciar el análisis.")
