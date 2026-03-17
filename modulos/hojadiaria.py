import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# --- FUNCIÓN PARA GENERAR PDF ---
def generar_pdf_vigilancia(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Configuraciones de diseño
    margin_x = 50
    margin_y = 50
    card_width = (width - (margin_x * 2)) 
    card_height = (height - (margin_y * 2)) / 4  # 4 plantillas por hoja
    
    y_position = height - margin_y
    count = 0

    for idx, row in df.iterrows():
        if count > 0 and count % 4 == 0:
            c.showPage() # Nueva página cada 4 pacientes
            y_position = height - margin_y
        
        # Dibujar recuadro de la plantilla
        c.setStrokeColor(colors.black)
        c.rect(margin_x, y_position - card_height + 10, card_width, card_height - 10)
        
        # Escribir Datos (Ajustado a tu mapeo de columnas)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin_x + 10, y_position - 25, f"PACIENTE: {str(row.iloc[4])}")
        
        c.setFont("Helvetica", 10)
        c.drawString(margin_x + 10, y_position - 45, f"REGISTRO: {str(row.iloc[3])}")
        c.drawString(margin_x + 200, y_position - 45, f"CAMA: {str(row.iloc[2])}")
        
        c.drawString(margin_x + 10, y_position - 65, f"ESPECIALIDAD: {str(row.iloc[1])}")
        c.drawString(margin_x + 200, y_position - 65, f"EDAD: {str(row.iloc[6])}")
        
        c.drawString(margin_x + 10, y_position - 85, f"FECHA INGRESO: {str(row.iloc[8])}")
        
        # Línea divisoria para notas o tachado visual
        c.setDash(1, 2)
        c.line(margin_x + 10, y_position - 100, margin_x + card_width - 10, y_position - 100)
        c.setDash()
        
        y_position -= card_height
        count += 1
        
    c.save()
    buffer.seek(0)
    return buffer

# --- AGREGAR A TU INTERFAZ EXISTENTE ---
# (Debajo de los botones de Inicio y Vigilancia Diaria)

if 'df_vig' in st.session_state:
    st.divider()
    st.subheader("🖨️ Exportar para Entrega de Guardia")
    
    df_pdf = st.session_state['df_vig']
    
    if not df_pdf.empty:
        pdf_file = generar_pdf_vigilancia(df_pdf)
        
        st.download_button(
            label="📄 Descargar PDF (4 plantillas por hoja)",
            data=pdf_file,
            file_name="vigilancia_diaria.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.warning("No hay datos cargados para generar el PDF.")
