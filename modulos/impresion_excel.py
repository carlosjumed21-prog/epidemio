import streamlit as st
import pandas as pd

def generar_html_impresion(dfs_dict, orientacion, tipo_hoja):
    """
    Genera un contenedor HTML estilizado con reglas de CSS @media print
    para forzar el autoajuste de las tablas al tamaño de hoja al imprimir.
    """
    # Configuración de dimensiones según la elección del usuario
    ancho_hoja = "215.9mm"
    alto_hoja = "279.4mm" if tipo_hoja == "Carta" else "355.6mm"
    
    if orientacion == "Horizontal":
        ancho_hoja, alto_hoja = alto_hoja, ancho_hoja

    html_content = f"""
    <style>
        /* Estilos en pantalla normal (Vista Previa) */
        .preview-container {{
            background-color: #ffffff;
            padding: 15px;
            margin-bottom: 30px;
            border: 1px solid #e6e9ef;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .preview-title {{
            color: #003366;
            font-size: 14px;
            font-weight: bold;
            border-bottom: 2px solid #003366;
            padding-bottom: 5px;
            margin-bottom: 10px;
        }}
        .print-table {{
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed; /* Fuerza el autoajuste de columnas */
            font-size: 11px;
        }}
        .print-table th {{
            background-color: #f4f6f9;
            color: #1e293b;
            border: 1px solid #cbd5e1;
            padding: 6px;
            text-align: center;
        }}
        .print-table td {{
            border: 1px solid #cbd5e1;
            padding: 5px;
            word-wrap: break-word;
        }}
        
        /* 🚨 MAGIA DE IMPRESIÓN RESTRINGIDA AL CONTENEDOR 🚨 */
        @media print {{
            body * {{
                visibility: hidden; /* Oculta toda la app de Streamlit (barras, botones) */
            }}
            .seccion-imprimible, .seccion-imprimible * {{
                visibility: visible; /* Muestra SOLO lo que está en este contenedor */
            }}
            .seccion-imprimible {{
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
            }}
            @page {{
                size: {ancho_hoja} {alto_hoja};
                margin: 10mm;
            }}
            .preview-container {{
                border: none !important;
                box-shadow: none !important;
                page-break-after: always; /* Cada pestaña va a una hoja nueva */
                page-break-inside: avoid;
            }}
            .preview-container:last-child {{
                page-break-after: avoid;
            }}
        }}
    </style>
    <div class="seccion-imprimible">
    """
    
    for sheet_name, df in dfs_dict.items():
        df_clean = df.fillna("")
        html_content += f"""
        <div class="preview-container">
            <div class="preview-title">CMN "20 de Noviembre" - Monitoreo IAAS: {sheet_name}</div>
            <table class="print-table">
                <thead>
                    <tr>
        """
        for col in df_clean.columns:
            html_content += f"<th>{col}</th>"
        html_content += "</tr></thead><tbody>"
        
        for _, row in df_clean.iterrows():
            html_content += "<tr>"
            for val in row:
                html_content += f"<td>{val}</td>"
            html_content += "</tr>"
            
        html_content += "</tbody></table></div>"
        
    html_content += "</div>"
    return html_content

# --- INTERFAZ ---
st.title("🖨️ Gestor de Impresión Nativo")
st.subheader("Autoajuste de reportes de Excel a PDF vía Navegador")

col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    tipo_hoja = st.selectbox("📄 Tamaño de Hoja:", ["Carta", "Oficio"])
with col2:
    orientacion = st.selectbox("📐 Orientación:", ["Horizontal", "Vertical"], index=0)
with col3:
    excel_subido = st.file_uploader("📂 Cargar reporte Excel", type=["xlsx", "xls"])

st.divider()

if excel_subido:
    try:
        excel_file = pd.ExcelFile(excel_subido)
        pestanas = excel_file.sheet_names
        
        dict_dataframes = {p: pd.read_excel(excel_subido, sheet_name=p) for p in pestanas}
        
        # Generamos el componente HTML estilizado
        html_impresion = generar_html_impresion(dict_dataframes, orientacion, tipo_hoja)
        
        # Instrucciones claras para el usuario clínico
        st.info(
            "💡 **Instrucciones para Imprimir / Guardar en PDF:**\n"
            "1. Haz clic en el botón **'Abrir Gestor de Impresión'** abajo.\n"
            "2. En el panel del navegador, cambia el Destino a **'Guardar como PDF'** o selecciona tu impresora física.\n"
            "3. Asegúrate de activar la casilla **'Gráficos de fondo'** si quieres conservar los colores de las tablas."
        )
        
        # Botón truco para lanzar la impresión nativa del sistema
        st.markdown(
            '<button onclick="window.print()" style="width:100%; padding:12px; background-color:#003366; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer; margin-bottom:20px;">🖨️ Abrir Gestor de Impresión (o CTRL + P)</button>', 
            unsafe_allow_html=True
        )
        
        st.markdown("### 👀 Vista Previa del Documento Ajustado")
        # Inyectamos el HTML en la aplicación para previsualizarlo y dejarlo listo para el motor de impresión
        st.markdown(html_impresion, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Error al mapear el archivo: {e}")
else:
    st.info("👋 Por favor sube un archivo Excel con pestañas para activar la vista previa de impresión.")
