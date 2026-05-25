import streamlit as st
import pandas as pd

def generar_impresion_con_escalado(df, nombre_pestana, orientacion, tipo_hoja):
    """
    Genera el documento respetando las celdas del Excel original,
    aplicando un escalado dinámico en CSS para ajustar el bloque completo
    al ancho de la hoja seleccionada (Carta u Oficio).
    """
    df_clean = df.fillna("")
    
    # Configuración de dimensiones para la maquetación física en el PDF
    format_js = "letter" if tipo_hoja == "Carta" else "legal"
    orientation_js = "landscape" if orientacion == "Horizontal" else "portrait"
    
    # 1. Construcción de la tabla estándar simulando la cuadrícula de Excel
    html_table = """
    <table style="
        border-collapse: collapse; 
        font-family: Calibri, Arial, sans-serif; 
        font-size: 11pt; 
        width: auto; 
        white-space: nowrap; /* Mantiene el formato original de las celdas sin romper renglón */
    ">
    """
    
    # Encabezados originales
    html_table += "<thead style='background-color: #f2f2f2; font-weight: bold;'>"
    html_table += "<tr>"
    for col in df_clean.columns:
        html_table += f"<th style='border: 1px solid #777777; padding: 6px; text-align: center;'>{col}</th>"
    html_table += "</tr></thead><tbody>"
    
    # Filas de datos tal cual vienen del Excel
    for _, row in df_clean.iterrows():
        html_table += "<tr>"
        for val in row:
            html_table += f"<td style='border: 1px solid #bbbbbb; padding: 5px; text-align: left;'>{val}</td>"
        html_table += "</tr>"
    html_table += "</tbody></table>"

    # 2. Inyección de estilos y el script JS encargado de extender/encoger la selección
    html_final = f"""
    <div style="font-family: Arial, sans-serif; margin-bottom: 15px;">
        <button onclick="exportarReporte()" 
            style="width: 100%; padding: 12px; background-color: #003366; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 15px;">
            📥 Generar e Imprimir PDF (Pestaña: {nombre_pestana})
        </button>
    </div>

    <div id="contenedor-impresion" style="background: white; padding: 10px; box-sizing: border-box;">
        <div id="bloque-escalado" style="transform-origin: top left; display: inline-block;">
            <div style="margin-bottom: 15px; font-family: Arial, sans-serif;">
                <h3 style="color: #003366; margin: 0; font-size: 16px;">CENTRO MÉDICO NACIONAL "20 DE NOVIEMBRE" - ISSSTE</h3>
                <p style="margin: 3px 0; font-size: 12px; color: #555;">Reporte de Vigilancia Epidemiológica | Pestaña: <b>{nombre_pestana}</b></p>
            </div>
            {html_table}
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    
    <script>
        function exportarReporte() {{
            var contenedor = document.getElementById('contenedor-impresion');
            var bloque = document.getElementById('bloque-escalado');
            
            // Definir ancho objetivo aproximado en pixeles según el tipo de hoja seleccionado
            var anchoHojaMm = ({format_js} === 'letter') ? 215.9 : 215.9;
            if ('{orientation_js}' === 'landscape') {{
                anchoHojaMm = ({format_js} === 'letter') ? 279.4 : 355.6;
            }}
            
            // Convertir mm disponibles a pixeles (descontando márgenes estándar)
            var margenMm = 20; 
            var anchoObjetivoPx = (anchoHojaMm - margenMm) * 3.7795275591;
            
            // Calcular el factor de extensión o reducción real del Excel original
            var anchoTablaOriginal = bloque.offsetWidth;
            var factorEscalado = anchoObjetivoPx / anchoTablaOriginal;
            
            // Aplicar el factor de escala de forma idéntica a la selección de Excel
            bloque.style.transform = 'scale(' + factorEscalado + ')';
            
            var opt = {{
                margin:       10,
                filename:     'IAAS_{nombre_pestana}_{tipo_hoja}.pdf',
                image:        {{ type: 'jpeg', quality: 0.98 }},
                html2canvas:  {{ scale: 2, useCORS: true }},
                jsPDF:        {{ unit: 'mm', format: '{format_js}', orientation: '{orientation_js}' }}
            }};
            
            // Compilar el PDF y regresar la escala a la normalidad en pantalla al terminar
            html2pdf().set(opt).from(contenedor).save().then(function() {{
                bloque.style.transform = 'none';
            }});
        }}
    </script>
    """
    return html_final

# --- INTERFAZ EN STREAMLIT ---
st.title("🖨️ Gestor de Impresión Directa a PDF")
st.subheader("Configuración de escala y tamaño de impresión por pestaña")

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
        excel_file = pd.ExcelFile(excel_subido)
        pestanas_disponibles = excel_file.sheet_names
        
        pestana_seleccionada = st.selectbox(
            "📋 Selecciona la pestaña específica que deseas exportar:",
            options=pestanas_disponibles
        )
        
        with st.spinner(f"Mapeando celdas originales de '{pestana_seleccionada}'..."):
            df_pestana = pd.read_excel(excel_subido, sheet_name=pestana_seleccionada)
            componente_html = generar_impresion_con_escalado(df_pestana, pestana_seleccionada, orientacion, tipo_hoja)
        
        st.write("") 
        st.success(f"✅ Estructura original de la pestaña **'{pestana_seleccionada}'** lista para escalado.")
        
        # Renderizar la interfaz interactiva para el usuario clínico
        st.components.v1.html(componente_html, height=550, scrolling=True)
            
    except Exception as e:
        st.error(f"❌ Ocurrió un error al procesar el Excel original: {e}")
else:
    st.info("👋 Por favor, arrastra tu archivo Excel en la sección superior para habilitar el selector de pestañas.")
