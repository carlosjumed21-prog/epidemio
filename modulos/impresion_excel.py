import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO

class PDFReporte(FPDF):
    def __init__(self, orientacion, tamano):
        # Convertir orientación a formato fpdf ('P' o 'L')
        ori = 'P' if orientacion == 'Vertical' else 'L'
        super().__init__(orientation=ori, unit='mm', format=tamano)
        self.set_auto_page_break(auto=True, margin=10)

    def header(self):
        # Encabezado institucional del CMN 20 de Noviembre
        self.set_font('Arial', 'B', 11)
        self.set_text_color(0, 51, 102) # Azul Institucional
        self.cell(0, 6, 'CENTRO MÉDICO NACIONAL "20 DE NOVIEMBRE" - ISSSTE', ln=True, align='C')
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Coordinación de Vigilancia Epidemiológica - Gestión de IAAS', ln=True, align='C')
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Página {self.page_no()} - Documento generado de forma automática por EpidemioManager', align='C')

def generar_pdf_autoajustado(df, nombre_pestana, orientacion, tipo_hoja):
    # Inicializar PDF con las dimensiones seleccionadas
    # fpdf usa 'letter' o 'legal' (Oficio americano)
    formato_hoja = 'letter' if tipo_hoja == 'Carta' else 'legal'
    pdf = PDFReporte(orientacion, formato_hoja)
    pdf.add_page()
    
    # Título de la sección/pestaña
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 6, f"Reporte: {nombre_pestana}", ln=True, align='L')
    pdf.ln(2)

    # Limpiar nulos del DataFrame para evitar impresiones de "nan"
    df_clean = df.fillna("")
    
    # ---- LÓGICA DE AUTOAJUSTE CRÍTICA ----
    # Obtener el ancho disponible de la página actual (ancho total - márgenes izquierdo y derecho)
    ancho_disponible = pdf.epw 
    num_columnas = len(df_clean.columns)
    
    if num_columnas == 0:
        pdf.cell(0, 10, "La pestaña seleccionada no contiene datos.", ln=True)
        return pdf.output()

    # Dividir de forma exacta el ancho de la hoja entre las columnas para garantizar que quepa en 1 plana a lo ancho
    ancho_columna = ancho_disponible / num_columnas

    # --- RENDERIZAR ENCABEZADOS ---
    pdf.set_font('Arial', 'B', 7)
    pdf.set_fill_color(240, 244, 248) # Gris azulado claro
    pdf.set_text_color(0, 51, 102)
    
    for col in df_clean.columns:
        # Guardamos la posición actual para controlar el ajuste de texto en celdas fijas
        x, y = pdf.get_x(), pdf.get_y()
        # MultiCell permite que el texto largo se rompa en renglones dentro de la celda ajustada
        pdf.multi_cell(ancho_columna, 6, str(col), border=1, align='C', fill=True)
        # Regresar a la posición horizontal derecha para la siguiente celda
        pdf.set_xy(x + ancho_columna, y)
    
    pdf.ln(6) # Salto de línea después del encabezado

    # --- RENDERIZAR FILAS DE DATOS ---
    pdf.set_font('Arial', '', 6.5)
    pdf.set_text_color(30, 30, 30)
    
    # Variable para alternar color de filas (facilita la lectura en hojas densas)
    alternar_color = False

    for _, fila in df_clean.iterrows():
        # Calcular la altura máxima que requerirá la fila actual midiendo la cantidad de texto
        alturas = []
        for celda in fila:
            # Estimar cuántas líneas ocupará el texto en el ancho asignado
            lineas = pdf.get_string_width(str(celda)) / ancho_columna
            alturas.append(max(1, int(lineas) + 1) * 4) # 4mm por línea aproximadamente
        altura_fila = max(alturas)

        # Evitar que una fila se corte a la mitad de camino al final de la página
        if pdf.get_y() + altura_fila > pdf.page_break_trigger:
            pdf.add_page()
            
        # Aplicar fondo alterno para el censo
        if alternar_color:
            pdf.set_fill_color(250, 250, 250)
        else:
            pdf.set_fill_color(255, 255, 255)
            
        x_inicio = pdf.get_x()
        y_inicio = pdf.get_y()

        for celda in fila:
            x, y = pdf.get_x(), pdf.get_y()
            pdf.multi_cell(ancho_columna, altura_fila / (altura_fila / 4), str(celda), border=1, align='L', fill=True)
            pdf.set_xy(x + ancho_columna, y_inicio)
            
        pdf.ln(altura_fila)
        alternar_color = not alternar_color

    # Retornar los bytes del PDF generado
    return pdf.output()

# --- INTERFAZ EN STREAMLIT ---
st.title("🖨️ Gestor de Impresión Directa a PDF")
st.subheader("Configuración de dimensiones y selección de pestañas para censos IAAS")

# Bloque superior de configuración
with st.container():
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        tipo_hoja = st.selectbox("📄 Tamaño del PDF:", ["Carta", "Oficio"])
    with c2:
        orientacion = st.selectbox("📐 Orientación de la Hoja:", ["Horizontal", "Vertical"], index=0)
    with c3:
        excel_subido = st.file_uploader("📂 Cargar archivo Excel de Origen", type=["xlsx", "xls"])

st.divider()

if excel_subido:
    try:
        # Leer la estructura del Excel cargado
        excel_file = pd.ExcelFile(excel_subido)
        pestanas_disponibles = excel_file.sheet_names
        
        # 🌟 NUEVA PESTAÑA DESPLEGABLE REQUERIDA 🌟
        pestana_seleccionada = st.selectbox(
            "📋 Selecciona la pestaña específica que deseas exportar a PDF:",
            options=pestanas_disponibles,
            help="El gestor leerá esta hoja y la autoajustará de manera exacta al ancho de una página."
        )
        
        st.write("") # Espaciador
        
        # Procesar la pestaña seleccionada únicamente
        with st.spinner(f"Procesando y aplicando autoajuste a la pestaña '{pestana_seleccionada}'..."):
            df_pestana = pd.read_excel(excel_subido, sheet_name=pestana_seleccionada)
            
            # Generar el binario del PDF usando FPDF2
            pdf_bytes = generar_pdf_autoajustado(df_pestana, pestana_seleccionada, orientacion, tipo_hoja)
        
        # Panel de acciones de descarga
        st.success(f"✅ Conversión finalizada con éxito para la pestaña: **{pestana_seleccionada}**")
        
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            st.info(
                f"**Resumen de Salida:**\n"
                f"- Pestaña procesada: `{pestana_seleccionada}`\n"
                f"- Formato: `{tipo_hoja} ({orientacion})` \n"
                f"- Las columnas fueron recalculadas (`pdf.epw / columnas`) para forzar un escalado perfecto."
            )
        with col_btn:
            st.write("") # Alineación visual
            st.download_button(
                label="📥 Exportar PDF",
                data=bytes(pdf_bytes),
                file_name=f"IAAS_{pestana_seleccionada}_{tipo_hoja}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
    except Exception as e:
        st.error(f"❌ Error al mapear o procesar la pestaña del Excel: {e}")
else:
    st.info("👋 Por favor, arrastra o sube el reporte de Excel para activar el selector de pestañas e iniciar la generación.")
