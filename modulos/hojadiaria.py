import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

def generar_pdf_estilo_hospital(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Márgenes y dimensiones
    margin_left = 30
    card_height = 180  # Altura de cada bloque de paciente
    y = height - 40     # Posición inicial
    
    for idx, row in df.iterrows():
        # Verificar si necesitamos una nueva página (máximo 4 por hoja)
        if y < 200:
            c.showPage()
            y = height - 40

        # --- DIBUJAR ESTRUCTURA DE LA TABLA (CELDAS) ---
        c.setLineWidth(0.5)
        c.setFont("Helvetica-Bold", 8)
        
        # Fila 1: Servicio y Días del mes (1-31)
        c.rect(margin_left, y, 550, 15) 
        c.drawString(margin_left + 5, y + 4, f"Servicio: {str(row.iloc[1])[:25]}")
        
        # Dibujar números 1 al 31 y el Total
        for i in range(1, 33): # 31 días + columna Total
            x_pos = margin_left + 150 + (i * 12)
            c.line(x_pos, y, x_pos, y - 105) # Líneas verticales de la cuadrícula
            if i <= 31:
                c.setFont("Helvetica-Bold", 6)
                c.drawCentredString(x_pos + 6, y + 4, str(i))
        c.drawString(margin_left + 150 + (32 * 12) + 2, y + 4, "Total")

        # Fila 2: Cama y días de seguimiento
        y -= 15
        c.rect(margin_left, y, 550, 15)
        c.drawString(margin_left + 5, y + 4, f"Cama: {str(row.iloc[2])}")
        c.drawString(margin_left + 100, y + 4, "Dias de seguimiento:")

        # Filas de Dispositivos (CVP, CVC, SU, VMA, PICC)
        dispositivos = ["CVP", "CVC", "SU", "VMA", "PICC"]
        y_temp = y
        for disp in dispositivos:
            y_temp -= 15
            c.rect(margin_left, y_temp, 550, 15)
            c.setFont("Helvetica", 7)
            c.drawString(margin_left + 105, y_temp + 4, disp)

        # Recuadro de Datos Personales (Izquierda)
        y_datos = y - 15
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(margin_left + 50, y_datos - 10, str(row.iloc[4])[:30]) # Nombre
        
        c.setFont("Helvetica", 7)
        c.drawString(margin_left + 5, y_datos - 30, f"Edad: {row.iloc[6]}")
        c.drawString(margin_left + 5, y_datos - 45, f"Expediente: {row.iloc[3]}")
        c.drawString(margin_left + 5, y_datos - 60, f"Ingreso: {row.iloc[8]}")

        # --- MARCAR LA 'X' SEGÚN EL DÍA ACTUAL ---
        try:
            dia_actual = int(str(row.iloc[0]).split('/')[0])
            if 1 <= dia_actual <= 31:
                x_marca = margin_left + 150 + (dia_actual * 12) + 3
                c.setFont("Helvetica-Bold", 10)
                c.drawString(x_marca, y + 4, "X") # Pone la X en la fila de Seguimiento
        except: pass

        # Espaciado para el siguiente paciente
        y -= 110 

    c.save()
    buffer.seek(0)
    return buffer

# --- INTEGRACIÓN EN TU INTERFAZ ---
if 'df_vig' in st.session_state:
    st.divider()
    st.subheader("🖨️ Generar Reporte PDF")
    if st.button("🛠️ Preparar PDF de Vigilancia"):
        pdf_data = generar_pdf_estilo_hospital(st.session_state['df_vig'])
        st.download_button(
            label="⬇️ Descargar PDF para Impresión (4 por hoja)",
            data=pdf_data,
            file_name="Vigilancia_Epidemiologica.pdf",
            mime="application/pdf",
            use_container_width=True
        )
