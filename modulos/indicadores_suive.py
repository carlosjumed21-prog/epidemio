import io

def generar_excel_reporte():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 1. Hoja de Tabla General Comparativa
        df_gen_export = df_gen_multi.copy()
        # Aplanar nombres de columnas multiindex para Excel
        df_gen_export.columns = [
            f"{col[0]} - {col[1]}" if col[0] != "UNIDAD MÉDICA / TRIMESTRE" else "UNIDAD MÉDICA" 
            for col in df_gen_export.columns
        ]
        df_gen_export.to_excel(writer, sheet_name='General Comparativo', index=False)
        
        # Agregar fila delegacional a la hoja general
        # (Aquí puedes volcar también tu dataframe delegacional general)
        
        # 2. Hoja por cada Indicador desglosado
        # Indicador A
        # Indicador B
        # Indicador C
        # Indicador F
        
    output.seek(0)
    return output

# Botón de descarga en la interfaz de Streamlit
st.markdown("---")
st.subheader("📥 Exportar Resultados Completos")

if uploaded_file is not None:
    excel_data = generar_excel_reporte()
    st.download_button(
        label="📥 Descargar Reporte Completo en Excel (con formato y colores)",
        data=excel_data,
        file_name=f"Reporte_SUIVE_{anio}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
