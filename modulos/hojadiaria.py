import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape # Importamos horizontal
from reportlab.lib import colors

# --- 1. CONEXIÓN (Sin cambios) ---
def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        ss_origen = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        ss_salida = client.open_by_key("116OTUoft_0Vf6Pf_jdTwDeLUP341i6bBqqfzfRl2zHc")
        h_datos_limpios = ss_origen.get_worksheet(1) 
        h_plantilla = ss_salida.get_worksheet(0)     
        h_historial = ss_salida.get_worksheet(1)     
        return ss_salida, h_plantilla, h_datos_limpios, h_historial
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None, None, None, None

# --- 2. FUNCIÓN DE ACTUALIZACIÓN (Sin cambios) ---
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
    except Exception:
        time.sleep(10)

# --- 3. LÓGICA PDF HORIZONTAL (LITERAL AL SHEETS) ---
def generar_pdf_horizontal(df):
    buffer = BytesIO()
    # Configuramos la hoja en tamaño carta pero HORIZONTAL
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Dimensiones para que quepan 4 por hoja en horizontal (2 arriba, 2 abajo)
    card_w = (width / 2) - 30
    card_h = (height / 2) - 40
    
    x_positions = [20, (width / 2) + 10]
    y_positions = [height - 20, (height / 2) - 10]
    
    count = 0
    for idx, row in df.iterrows():
        if count > 0 and count % 4 == 0:
            c.showPage()
        
        # Determinar posición en la cuadrícula 2x2
        pos_x = x_positions[count % 2]
        pos_y = y_positions[(count // 2) % 2]
        
        # Dibujar Cuadro Principal
        c.setLineWidth(0.8)
        c.rect(pos_x, pos_y - card_h, card_w, card_h)
        
        # Encabezado: Servicio y Cama
        c.setFont("Helvetica-Bold", 8)
        c.line(pos_x, pos_y - 15, pos_x + card_w, pos_y - 15)
        c.drawString(pos_x + 5, pos_y - 10, f"Servicio: {str(row.iloc[1])[:15]} | Cama: {str(row.iloc[2])}")
        
        # Cuadrícula de 1 a 31
        c.setFont("Helvetica-Bold", 6)
        col_w = (card_w - 100) / 32
        for i in range(1, 33):
            lx = pos_x + 100 + (i * col_w)
            c.line(lx, pos_y, lx, pos_y - 90)
            if i <= 31:
                c.drawCentredString(lx - (col_w/2), pos_y - 10, str(i))
        
        # Filas de Dispositivos (Mismo orden que el Sheet)
        labels = ["Seguimiento", "CVP", "CVC", "SU", "VMA", "PICC"]
        curr_y = pos_y - 15
        for label in labels:
            c.line(pos_x + 100, curr_y, pos_x + card_w, curr_y)
            c.setFont("Helvetica", 7)
            c.drawString(pos_x + 105, curr_y - 10, label)
            
            # Si es el día actual, tachar con X
            try:
                dia = int(str(row.iloc[0]).split('/')[0])
                if label == "Seguimiento":
                    mx = pos_x + 100 + (dia * col_w) - (col_w/2)
                    c.setFont("Helvetica-Bold", 8)
                    c.drawCentredString(mx, curr_y - 10, "X")
            except: pass
            curr_y -= 15

        # Datos del Paciente (Izquierda)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(pos_x + 5, pos_y - 35, str(row.iloc[4])[:20])
        c.setFont("Helvetica", 7)
        c.drawString(pos_x + 5, pos_y - 50, f"Exp: {row.iloc[3]}")
        c.drawString(pos_x + 5, pos_y - 65, f"Edad: {row.iloc[6]}")
        c.drawString(pos_x + 5, pos_y - 80, f"Ingreso: {row.iloc[8]}")
        
        count += 1

    c.save()
    buffer.seek(0)
    return buffer

# --- 4. INTERFAZ (Tus 3 botones + Botón PDF) ---
st.title("🏥 Vigilancia Epidemiológica")

if st.button("🔄 1. REFRESH", use_container_width=True):
    res = conectar_google_sheets()
    if res[0]:
        st.session_state['df_vig'] = pd.DataFrame(res[2].get_all_records())
        st.success("Censo cargado.")

if 'df_vig' in st.session_state:
    df = st.session_state['df_vig']
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚩 INICIO (RECREAR)", use_container_width=True):
            res = conectar_google_sheets()
            if res[0]:
                ss, h_ma, h_dat, h_his = res
                h_his.clear()
                f = 1
                for i, r in df.iterrows():
                    ss.batch_update({"requests": [{"copyPaste": {
                        "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                        "destination": {"sheetId": h_his.id, "startRowIndex": f-1, "endRowIndex": f+7, "startColumnIndex": 0, "endColumnIndex": 35},
                        "pasteType": "PASTE_NORMAL"
                    }}]})
                    try: d = int(str(r.iloc[0]).split('/')[0]); actualizar_bloque_paciente(h_his, f, r, d + 3)
                    except: pass
                    f += 8; time.sleep(2.5)
                st.success("Hecho.")

    with c2:
        if st.button("🔄 VIGILANCIA DIARIA", type="primary", use_container_width=True):
            res = conectar_google_sheets()
            if res[0]:
                ss, h_ma, h_dat, h_his = res
                col_b = h_his.col_values(2)
                reg_map = {str(col_b[i]).strip(): (i+1)-5 for i in range(5, len(col_b), 8) if str(col_b[i]).strip()}
                f_disp = len(col_b) + 1
                for idx, r in df.iterrows():
                    r_id = str(r.iloc[3]).strip()
                    d = int(str(r.iloc[0]).split('/')[0])
                    if r_id in reg_map: actualizar_bloque_paciente(h_his, reg_map[r_id], r, d + 3)
                    else:
                        ss.batch_update({"requests": [{"copyPaste": {
                            "source": {"sheetId": h_ma.id, "startRowIndex": 2, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 35},
                            "destination": {"sheetId": h_his.id, "startRowIndex": f_disp-1, "endRowIndex": f_disp+7, "startColumnIndex": 0, "endColumnIndex": 35},
                            "pasteType": "PASTE_NORMAL"
                        }}]})
                        actualizar_bloque_paciente(h_his, f_disp, r, d + 3); f_disp += 8
                    time.sleep(2.5)
                st.success("Actualizado.")

    st.divider()
    if st.button("📄 GENERAR PDF (HORIZONTAL - 4 POR HOJA)", use_container_width=True):
        pdf_file = generar_pdf_horizontal(df)
        st.download_button(label="⬇️ Descargar PDF", data=pdf_file, file_name="Vigilancia.pdf", mime="application/pdf", use_container_width=True)
