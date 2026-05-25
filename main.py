import streamlit as st
import pandas as pd

def generar_interfaz_y_script(df, nombre_pestana, orientacion, tipo_hoja):
    """
    Genera la tabla mapeada en HTML junto con el botón de descarga y el script 
    de html2pdf agrupados para evitar bloqueos de seguridad del navegador.
    """
    df_clean = df.fillna("")
    
    # Mapeo exacto de dimensiones para la maquetación del PDF
    format_js = "letter" if tipo_hoja == "Carta" else "legal"
    orientation_js = "landscape" if orientacion == "Horizontal" else "portrait"
    
    # Construcción de la tabla con CSS estructurado para forzar el autoajuste
    html_table = "<table style='width:100%; border-collapse:collapse; font-family:Arial, sans-serif; font-size:10px; table-layout:fixed;'>"
    html_table += "<thead><tr style='background-color:#003366; color:white;'>"
    for col in df_clean.columns:
        html_table += f"<th style='border:1px solid #cbd5e1; padding:6px; text-align:center; font-size:9px;'>{col}</th>"
    html_table += "</tr></thead><tbody>"
    
    # Inyección de filas
    for _, row in df_clean.iterrows():
        html_table += "<tr>"
        for val in row:
            html_table += f"<td style='border:1px solid #cbd5e1; padding:5px; word-wrap:break-word;'>{val}</td>"
        html_table += "</tr>"
    html_table += "</tbody></table>"

    # Documento completo estructurado para el renderizado
    html_final = f"""
    <div style="font-family:Arial, sans-serif; margin-bottom:15px;">
        <button onclick="descargarPDF()" 
            style="width:100%; padding:12px; background-color:#003366; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer; font-size:15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            📥 Generar y Descargar PDF (`{nombre_pestana}`)
        </button>
    </div>

    <div id="area-impresion" style="padding:15px; background:white; color:#333;">
        <div style="border-bottom:2px solid #003366; padding-bottom:5px; margin-bottom:15px;">
            <h2 style="color:#003366; margin:0; font-size:16px;">CENTRO MÉDICO NACIONAL "20 DE NOVIEMBRE" - ISSSTE</h2>
            <p style="margin:3px 0 0 0; font-size:11px; color:#555;">Vigilancia Epidemiológica | Reporte de Pestaña: <b>{nombre_pestana}</b></p>
        </div>
        {html_table}
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    
    <script>
        function descargarPDF() {{
            var element = document.getElementById('area-impresion');
            var opt = {{
                margin:       10,
                filename:     'IAAS_{nombre_pestana}_{tipo_hoja}.pdf',
                image:        {{ type: 'jpeg', quality: 0.98 }},
                html2canvas:  {{ scale: 2, useCORS: true }},
                jsPDF:        {{ unit: 'mm', format: '{format_js}', orientation: '{orientation_js}' }}
            }};
            // Ejecuta la compilación y descarga directa en la máquina del usuario
            html2pdf().set(opt).from(element).save();
        }}
    </script>
    """
    return html_final

# --- INTERFAZ EN STREAMLIT ---
st.title("🖨️ Gestor de Impresión Directa a PDF")
st.subheader("Filtro por pestañas con autoajuste de celdas para censos hospitalarios")

# Contenedor superior de configuraciones formales
with st.container():
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        tipo_hoja = st.selectbox("📄 Tamaño del PDF destino:", ["Carta", "Oficio"])
    with c2:
        orientacion = st.selectbox("📐 Orientación del diseño:", ["Horizontal", "Vertical"], index=0)
    with c3:
        excel_subido = st.file_uploader("📂 Selecciona el reporte de Excel de origen", type=["xlsx", "xls"])

st.divider()

if excel_subido:
    try:
        # Extraer nombres de pestañas sin procesar todo el archivo para ahorrar memoria
        excel_file = pd.ExcelFile(excel_subido)
        pestanas_disponibles = excel_file.sheet_names
        
        # Desplegable dinámico solicitado
        pestana_seleccionada = st.selectbox(
            "📋 Selecciona la pestaña específica que deseas exportar:",
            options=pestanas_disponibles,
            help="El gestor adaptará el número de columnas al ancho del papel de manera automatizada."
        )
        
        # Cargar únicamente la pestaña seleccionada por el usuario
        with st.spinner(f"Estructurando datos de '{pestana_seleccionada}'..."):
            df_pestana = pd.read_excel(excel_subido, sheet_name=pestana_seleccionada)
            
            # Generar el bloque unificado de HTML, Estilos, Botón y Script JS
            componente_html = generar_interfaz_y_script(df_pestana,
