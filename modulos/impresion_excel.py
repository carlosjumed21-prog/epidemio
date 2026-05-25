import streamlit as st
import pandas as pd
from io import BytesIO
from xhtml2pdf import pisa

# --- CONFIGURACIÓN DE TAMAÑOS DE HOJA (En mm para precisión) ---
MEDIDAS_HOJA = {
    "Carta (Vertical)": {"size": "letter", "orientation": "portrait"},
    "Carta (Horizontal)": {"size": "letter", "orientation": "landscape"},
    "Oficio (Vertical)": {"size": "8.5in 14in", "orientation": "portrait"},
    "Oficio (Horizontal)": {"size": "14in 8.5in", "orientation": "landscape"},
}

def generar_html_para_pdf(dfs_dict, tamano_config, titulo_documento="Reporte IAAS"):
    """
    Genera un string HTML con estilos CSS para forzar que las tablas
    se autoajusten al ancho de la página seleccionada.
    """
    size_css = tamano_config["size"]
    orientation_css = tamano_config["orientation"]
    
    html_content = f"""
    <html>
    <head>
        <style>
            @page {{
                size: {size_css} {orientation_css};
                margin: 1cm;
            }}
            body {{
                font-family: 'Helvetica', 'Arial', sans-serif;
                color: #333333;
                font-size: 8pt;
            }}
            .page-break {{
                page-break-after: always;
            }}
            .page-break:last-child {{
                page-break-after: avoid;
            }}
            .header {{
                text-align: center;
                margin-bottom: 15px;
                border-bottom: 2px solid #003366;
                padding-bottom: 5px;
            }}
            .hospital-title {{
                font-size: 14pt;
                font-weight: bold;
                color: #003366;
            }}
            .sheet-title {{
                font-size: 11pt;
                font-weight: bold;
                margin-top: 5px;
                color: #555555;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                table-layout: fixed; /* Fuerza el autoajuste de columnas dentro del ancho */
            }}
            th {{
                background-color: #f2f2f2;
                color: #003366;
                font-weight: bold;
                border: 1px solid #dddddd;
                padding: 4px;
                text-align: center;
                font-size: 7.5pt;
            }}
            td {{
                border: 1px solid #dddddd;
                padding: 4px;
                text-align: left;
                word-wrap: break-word; /* Evita que textos largos rompan la celda */
                font-size: 7pt;
            }}
            tr:nth-child(even) {{
                background-color: #fafafa;
            }}
        </style>
    </head>
    <body>
    """
    
    # Iterar por cada pestaña del Excel
    for sheet_name, df in dfs_dict.items():
        # Reemplazar valores nulos por vacío para una impresión limpia
        df_clean = df.fillna("")
        
        html_content += f"""
        <div class="page-break">
            <div class="header">
                <div class="hospital-title">CMN "20 de Noviembre" - ISSSTE</div>
                <div class="sheet-title">Monitoreo Epidemiológico: {sheet_name}</div>
            </div>
            <table>
                <thead>
                    <tr>
        """
        # Renderizar Encabezados
        for col in df_clean.columns:
            html_content += f"<th>{col}</th>"
            
        html_content += """
                    </tr>
                </thead>
                <tbody>
        """
        # Renderizar Filas
        for _, row in df_clean.iterrows():
            html_content += "<tr>"
            for val in row:
                html_content += f"<td>{val}</td>"
            html_content += "</tr>"
            
        html_content += """
                </tbody>
            </table>
        </div>
        """
        
    html_content += "</body></html>"
    return html_content

def convertir_html_a_pdf(html_string):
    """Convierte el HTML autogenerado en un archivo binario PDF."""
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html_string.encode("utf-8")), dest=pdf_buffer)
    if pisa_status.err:
        return None
    pdf_buffer.seek(0)
    return pdf_buffer


# --- INTERFAZ DE STREAMLIT ---

st.title("🖨️ Gestor de Impresión y Formateo IAAS")
st.subheader("Autoajuste de reportes de Excel a PDF de una sola hoja por pestaña")

# Contenedor de configuración de página
col1, col2 = st.columns([2, 2])

with col1:
    tipo_hoja = st.selectbox(
        "📄 Selecciona el tamaño y orientación de impresión:",
        options=list(MEDIDAS_HOJA.keys()),
        index=1 # Por defecto Carta Horizontal, suele ser mejor para censos
    )

with col2:
    excel_subido = st.file_uploader(
        "📂 Arrastra o selecciona el archivo Excel de origen",
        type=["xlsx", "xls"],
        help="Sube aquí cualquier reporte con múltiples pestañas para forzar su ajuste."
    )

st.divider()

if excel_subido:
    try:
        # 1. Leer todas las pestañas del Excel de manera automática
        excel_file = pd.ExcelFile(excel_subido)
        pestanas = excel_file.sheet_names
        
        st.success(f"📊 Archivo cargado correctamente. Se detectaron **{len(pestanas)}** pestañas.")
        
        # Guardar los DataFrames en un diccionario
        dict_dataframes = {}
        for biente in pestanas:
            # Seteamos header=0 para los títulos de columnas
            dict_dataframes[biente] = pd.read_excel(excel_subido, sheet_name=biente)
        
        # 2. PESTAÑAS DE VISTA PREVIA EN STREAMLIT
        st.markdown("### 👀 Vista Previa de Datos Origen")
        tabs_visualizacion = st.tabs(pestanas)
        
        for idx, nombre_pestana in enumerate(pestanas):
            with tabs_visualizacion[idx]:
                st.dataframe(
                    dict_dataframes[nombre_pestana], 
                    use_container_width=True,
                    column_config={"_index": None}
                )
        
        st.divider()
        
        # 3. GENERACIÓN DE DOCUMENTO DE IMPRESIÓN
        with st.spinner("⚙️ Mapeando y autoajustando dimensiones para PDF..."):
            # Generar HTML con la configuración elegida
            html_final = generar_html_para_pdf(dict_dataframes, MEDIDAS_HOJA[tipo_hoja])
            pdf_listo = convertir_html_a_pdf(html_final)
            
        if pdf_listo:
            st.markdown("### 🖨️ Centro de Descarga e Impresión")
            
            info_col, btn_col = st.columns([3, 1])
            with info_col:
                st.info(
                    f"✨ El documento ha sido formateado en tamaño **{tipo_hoja}**. \n"
                    f"Las columnas han sido forzadas mediante CSS (`table-layout: fixed`) "
                    f"para compactarse automáticamente al ancho de una página por pestaña."
                )
            with btn_col:
                st.write("") # Espaciador
                st.download_button(
                    label="📥 Descargar PDF listo para Imprimir",
                    data=pdf_listo,
                    file_name="Reporte_IAAS_Impresion.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.error("❌ Hubo un error al compilar el PDF. Revisa que el Excel no contenga caracteres extraños.")
            
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo Excel: {e}")

else:
    st.info("👋 Sube un archivo de Excel en la barra superior para generar la maquetación de impresión.")
