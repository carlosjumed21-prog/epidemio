import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# --- 1. CONEXIÓN ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # ORIGEN: Sabana
        ss_origen = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        # SALIDA: Vigilancia
        ss_salida = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        
        h_datos_limpios = ss_origen.get_worksheet(1) # Hoja 2
        h_plantilla = ss_salida.get_worksheet(0)     # Hoja 1
        h_historial = ss_salida.get_worksheet(1)     # Hoja 2
            
        return ss_salida, h_plantilla, h_datos_limpios, h_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None

# --- 2. FUNCIÓN DE ACTUALIZACIÓN ---
def actualizar_bloque_paciente(h_hi, fila_base, fila_datos, col_x):
    try:
        lista_celdas = [
            gspread.Cell(row=fila_base, col=2, value=str(fila_datos.iloc[1])),     
            gspread.Cell(row=fila_base + 1, col=2, value=str(fila_datos.iloc[2])), 
            gspread.Cell(row=fila_base + 2, col=1, value=str(fila_datos.iloc[4])), 
            gspread.Cell(row=fila_base + 4, col=2, value=str(fila_datos.iloc[6])), 
            gspread.Cell(row=fila_base + 5, col=2, value=str(fila_datos.iloc[3])), 
            gspread.Cell(row=fila_base + 6, col=2, value=str(fila_datos.iloc[8])), 
            gspread.Cell(row=fila_base + 1, col=col_x, value="X")                  
        ]
        h_hi.update_cells(lista_celdas, value_input_option='USER_ENTERED')
    except Exception as e:
        time.sleep(10) # En caso de error de cuota

# --- 3. LÓGICA DE DIBUJO PDF (ESTILO HOSPITAL) ---
def generar_pdf_estilo_hospital(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin_left = 30
    y = height - 40
    
    for idx, row in df.iterrows():
        if y < 180:
            c.showPage()
            y = height - 40

        # Dibujar Cuadrícula y Textos (Basado en tu imagen)
        c.setLineWidth(0.6)
        c.setFont("Helvetica-Bold", 8)
        
        # Cabecera del bloque
        c.rect(margin_left, y, 550, 15) 
        c.drawString(margin_left + 5, y + 4, f"Servicio: {str(row.iloc[1])[:20]} | Cama: {str(row.iloc[2])}")
        
        # Dibujar cuadrícula de días 1-31
        for i in range(1, 33):
            x_pos = margin_left + 155 + (i * 12)
            c.line(x_pos, y, x_pos, y - 90) # Líneas verticales
            if i <= 31:
                c.setFont("Helvetica-Bold", 6)
                c.drawCentredString(x_pos + 6, y + 4, str(i))
        
        y -= 15
        # Filas de dispositivos
        labels = ["Seguimiento", "CVP", "CVC", "SU", "VMA", "PICC"]
        for label in labels:
            c.rect(margin_left, y, 550, 15)
            c.setFont("Helvetica", 7)
            c.drawString(margin_left + 105, y + 4, label)
            y -= 15
        
        # Datos del paciente (lado izquierdo del bloque)
        y_txt = y + 85
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margin_left + 5, y_txt, str(row.iloc[4])[:30])
        c.setFont("Helvetica", 7)
        c.drawString(margin_left + 5, y_txt - 15, f"Exp: {row.iloc[3]}")
        c.drawString(margin_left + 5, y_txt - 25, f"Edad: {row.iloc[6]}")
        c.drawString(margin_left + 5, y_txt - 35, f"Ingreso: {row.iloc[8]}")

        y -= 10 # Espacio entre bloques

    c.save()
    buffer.seek(0)
    return buffer

# --- 4. INTERFAZ STREAMLIT ---
st.title("🏥 Vigilancia Epidemiológica")

# BOTÓN REFRESH
if st.button("🔄 1. REFRESH: Cargar Censo", use_container_width=True):
    res = conectar_google_sheets()
    if res[0]:
        df = pd.DataFrame(res[2].get_all_records())
        st.session_state['df_vig'] = df
        st.success(f"✅ {len(df)} pacientes cargados de Hoja 2.")

if 'df_vig' in st.session_state:
    df_actual = st.session_state['df_vig']
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚩 INICIO (RECREAR)", use_container_width=True):
            res = conectar_google_sheets()
            if res[0]:
                ss, h_ma, h_dat, h_his = res
                h_his.clear()
                f = 1
                for i, row in df_actual.iterrows():
                    ss.batch_update({"requests": [{"copyPaste": {
                        "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": h_his.id, "startRowIndex": f-1, "endRowIndex": f+7, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }}]})
                    try:
                        d = int(str(row.iloc[0]).split('/')[0])
                        actualizar_bloque_paciente(h_his, f, row, d + 3)
                    except: pass
                    f += 8
                    time.sleep(2.5)
                st.success("Historial recreado.")

    with c2:
        if st.button("🔄 VIGILANCIA DIARIA", type="primary", use_container_width=True):
            res = conectar_google_sheets()
            if res[0]:
                ss, h_ma, h_dat, h_his = res
                col_b = h_his.col_values(2)
                reg_map = {str(col_b[i]).strip(): (i+1)-5 for i in range(5, len(col_b), 8) if str(col_b[i]).strip()}
                f_disp = len(col_b) + 1
                for idx, row in df_actual.iterrows():
                    r_id = str(row.iloc[3]).strip()
                    d = int(str(row.iloc[0]).split('/')[0])
                    if r_id in reg_map:
                        actualizar_bloque_paciente(h_his, reg_map[r_id], row, d + 3)
                    else:
                        ss.batch_update({"requests": [{"copyPaste": {
                            "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                            "destination": {"sheetId": h_his.id, "startRowIndex": f_disp-1, "endRowIndex": f_disp+7, "startColumnIndex": 0, "endColumnIndex": 35},
                            "pasteType": "PASTE_NORMAL"
                        }}]})
                        actualizar_bloque_paciente(h_his, f_disp, row, d + 3)
                        f_disp += 8
                    time.sleep(2.5)
                st.success("Vigilancia actualizada.")

    # --- BOTÓN DE PDF (AÑADIDO SIN ALTERAR LO DEMÁS) ---
    st.divider()
    if st.button("📄 Generar PDF para Imprimir (4 por hoja)", use_container_width=True):
        pdf_file = generar_pdf_estilo_hospital(df_actual)
        st.download_button(
            label="⬇️ Descargar Reporte PDF",
            data=pdf_file,
            file_name="Vigilancia_Epidemiologica.pdf",
            mime="application/pdf",
            use_container_width=True
        )
